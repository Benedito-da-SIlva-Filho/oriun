# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\permissoes.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-15 09:41 -03
# ATUALIZADO EM: 2026-11-16 11:45 -03
# VERSAO: 1.3.0
#
# DESCRICAO:
#     PORTEIRO UNICO das permissoes por cargo (Etapa 1). Roda antes de
#     toda requisicao e olha so os enderecos /produtor/... de quem e
#     PRODUTOR. Consiste, Certificadora e paginas publicas ficam de fora.
#
#     Regra: cargo (session['usuario_cargo']) + modulo do endereco +
#     metodo -> libera ou barra. Barrou: volta para a Home com o aviso
#     ?aviso=permissao (ou responde 403 em JSON se for chamada AJAX).
#
#     Os ajustes do Titular vem de public.permissao_cargo (por
#     propriedade). Se a tabela ainda nao existe ou o banco falha, valem
#     os padroes de backend\utils\permissoes.py (nunca derruba o sistema).
#
#     Tambem oferece aos templates o ajudante pode_ver('modulo') e aos
#     Hubs a funcao caminho_permitido(caminho).
#
# HISTORICO DE VERSOES:
#     v1.0.0: Sessao 097 (15/10/2026, 09:41 -03) - Criacao.
#     v1.1.0: Sessao 097 (15/10/2026, 11:20 -03) - AUDITORIA: o porteiro tambem barra, para PRODUTOR sem acesso, os enderecos
#             fora de /produtor/ que o utils/permissoes.py v1.1.0 mapeia (/propriedades,
#             /proprietarios, /produtores e /api/busca-cpf-cnpj).
#     v1.2.0: Sessao 097 (15/10/2026, 11:20 -03) - CARGO RECONFERIDO: a cada 5 minutos o cargo da sessao e relido no banco
#             (vinculo do usuario com o produtor em uso). Cargo alterado vale em ate 5 min;
#             vinculo encerrado deixa so o Painel. Erro de banco nao mexe na sessao.
#     v1.3.0: Sessao 128 (2026-11-16 11:45 -03) - AUDITORIA ETAPA 8a: usuario com 2 ou mais fazendas e nenhuma em uso valia o PADRAO do cargo (ignorava os ajustes do Titular). Agora vale o MAIS RESTRITIVO entre os ajustes das fazendas dele. REVERSAO: .bak_antes_etapa8a.
# =========================================================

import time

from flask import Blueprint, request, session, g, jsonify, redirect, url_for
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import UsuarioVinculo
from backend.utils.permissoes import (
    CONSULTA, NIVEIS, autorizado, nivel_efetivo, modulo_do_caminho, nivel_padrao,
)

permissoes = Blueprint('permissoes', __name__)

_AVISOU_TABELA = False

# v1.2.0: de quanto em quanto tempo o cargo da sessao e conferido de novo no banco
# (se o Titular mudar o cargo ou encerrar o vinculo, vale em ate 5 minutos).
_REVALIDA_SEGUNDOS = 300


def _id_propriedade_em_uso():
    """Propriedade a que os ajustes se referem: a fazenda em uso ou a unica
    propriedade do usuario. None se nao da para saber (valem os padroes)."""
    fazenda = session.get('fazenda_ativa')
    if fazenda:
        try:
            return int(fazenda['id_propriedade'])
        except (KeyError, TypeError, ValueError):
            pass

    id_usuario = session.get('usuario_id')
    cache = session.get('perm_prop')
    if cache and len(cache) == 2 and cache[0] == id_usuario:
        return cache[1]

    try:
        from backend.routers.auth import buscar_pares_propriedade_produtor
        ids = {int(p.id_propriedade) for p in buscar_pares_propriedade_produtor(id_usuario)}
    except Exception:
        return None
    if len(ids) == 1:
        unica = ids.pop()
        session['perm_prop'] = [id_usuario, unica]
        return unica
    if len(ids) > 1:
        g._perm_ids_multi = sorted(ids)   # v1.3.0: 2+ fazendas e nenhuma em uso
    return None


def _ajustes_da_requisicao():
    """Ajustes {(cargo, modulo): nivel} da propriedade em uso, 1 consulta por requisicao."""
    global _AVISOU_TABELA
    if hasattr(g, '_perm_ajustes'):
        return g._perm_ajustes

    ajustes = {}
    id_propriedade = _id_propriedade_em_uso()
    if id_propriedade:
        try:
            with Session(engine) as db:
                linhas = db.execute(
                    text("SELECT cargo, modulo, nivel FROM public.permissao_cargo "
                         "WHERE id_propriedade = :p"),
                    {'p': id_propriedade}
                ).fetchall()
            for cargo, modulo, nivel in linhas:
                if nivel in NIVEIS:
                    ajustes[(cargo, modulo)] = NIVEIS[nivel]
        except Exception:
            if not _AVISOU_TABELA:
                print('PERMISSOES: tabela public.permissao_cargo indisponivel - usando os padroes.')
                _AVISOU_TABELA = True
            ajustes = {}
    elif getattr(g, '_perm_ids_multi', None):
        # v1.3.0: sem fazenda em uso, vale o MAIS RESTRITIVO entre as fazendas do usuario
        # (fazenda sem ajuste conta com o padrao do cargo).
        try:
            with Session(engine) as db:
                linhas = db.execute(
                    text("SELECT id_propriedade, cargo, modulo, nivel FROM public.permissao_cargo "
                         "WHERE id_propriedade = ANY(:ps)"),
                    {'ps': list(g._perm_ids_multi)}
                ).fetchall()
            por_propriedade = {}
            for id_prop, cargo, modulo, nivel in linhas:
                if nivel in NIVEIS:
                    por_propriedade.setdefault(id_prop, {})[(cargo, modulo)] = NIVEIS[nivel]
            chaves = {chave for d in por_propriedade.values() for chave in d}
            for chave in chaves:
                ajustes[chave] = min(
                    por_propriedade.get(p, {}).get(chave, nivel_padrao(chave[0], chave[1]))
                    for p in g._perm_ids_multi
                )
        except Exception:
            if not _AVISOU_TABELA:
                print('PERMISSOES: tabela public.permissao_cargo indisponivel - usando os padroes.')
                _AVISOU_TABELA = True
            ajustes = {}

    g._perm_ajustes = ajustes
    return ajustes


def _revalidar_cargo():
    """Reconfere no banco o cargo do usuario no produtor em uso, no maximo a cada
    _REVALIDA_SEGUNDOS. Vinculo encerrado = sem cargo (so o Painel). Qualquer erro
    de banco NAO mexe na sessao."""
    id_usuario = session.get('usuario_id')
    id_produtor = session.get('id_produtor')
    if not id_usuario or not id_produtor:
        return

    agora = time.time()
    marca = session.get('perm_marca')
    if (marca and len(marca) == 3 and marca[0] == id_usuario
            and marca[1] == id_produtor and agora - marca[2] < _REVALIDA_SEGUNDOS):
        return

    try:
        with Session(engine) as db:
            vinculo = db.query(UsuarioVinculo).filter_by(
                id_usuario=id_usuario, id_produtor=id_produtor, data_fim=None
            ).first()
            cargo = vinculo.cargo if vinculo else None
    except Exception:
        return

    session['usuario_cargo'] = cargo
    session['perm_marca'] = [id_usuario, id_produtor, agora]


def _eh_produtor():
    return 'usuario_id' in session and session.get('usuario_perfil') == 'PRODUTOR'


def nivel_atual(modulo):
    """Nivel do usuario logado num modulo (para os templates)."""
    cargo = session.get('usuario_cargo')
    return nivel_efetivo(cargo, modulo, _ajustes_da_requisicao())


def pode_ver(modulo):
    """True se o usuario logado enxerga o modulo. Nunca lanca excecao: em
    caso de duvida mostra (o porteiro barra o acesso de qualquer jeito)."""
    try:
        if not _eh_produtor():
            return True
        return nivel_atual(modulo) >= CONSULTA
    except Exception:
        return True


def caminho_permitido(caminho, metodo='GET'):
    """True se o usuario logado pode abrir esse caminho (usado nos cards dos Hubs)."""
    try:
        if not _eh_produtor():
            return True
        liberado, _ = autorizado(session.get('usuario_cargo'), metodo, caminho, _ajustes_da_requisicao())
        return liberado
    except Exception:
        return True


def _quer_json():
    return (request.is_json
            or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or request.accept_mimetypes.best == 'application/json')


@permissoes.before_app_request
def _porteiro_permissoes():
    caminho = request.path
    # v1.1.0: alem de /produtor/, cobre as telas do Produtor que ficam fora dele
    if not caminho.startswith('/produtor/') and modulo_do_caminho(caminho) is None:
        return None
    if not _eh_produtor():
        return None

    _revalidar_cargo()
    cargo = session.get('usuario_cargo')
    liberado, modulo = autorizado(cargo, request.method, caminho, _ajustes_da_requisicao())
    if liberado:
        return None

    if modulo is None:
        print(f'PERMISSOES: endereco sem modulo registrado barrado: {request.method} {caminho}')

    if _quer_json():
        return jsonify({'ok': False, 'erro': 'permissao',
                        'mensagem': 'Seu cargo nao tem acesso a esta funcao.'}), 403
    return redirect(url_for('auth.produtor_home', aviso='permissao'))


@permissoes.app_context_processor
def _ajudantes_de_template():
    return {'pode_ver': pode_ver}

# =========================================================
# FIM DE ARQUIVO: backend\routers\permissoes.py
# =========================================================
