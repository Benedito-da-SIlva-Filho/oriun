# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\Orion\backend\routers
# MODULO: backend\routers\bnd_fazenda_consiste.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-18 20:00 -03
# ATUALIZADO EM: 2026-11-18 20:00 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Tela CONSISTE > BND/Fazenda: CORRECAO da base a partir do Extrato de Animais Vivos do MAPA (so o perfil CONSISTE).
#     A comparacao com relatorios e do Produtor (ver bnd_fazenda.py); aqui a Consiste so corrige.
#
#     O Extrato da Propriedade pode trazer varios Produtores (uma parte por Produtor, com o CPF/CNPJ). A Correcao vale
#     para TODOS os Produtores do arquivo. Produtor ou Propriedade que nao existe no Orion: e pulado e a tela avisa
#     (os demais seguem). Cada Produtor e gravado numa transacao propria.
#
#     O QUE CORRIGE (o que vale e a BND): sexo, nascimento e raca dos animais que estao nos dois lados com dado diferente,
#     e a DATA DE INCLUSAO automaticamente. Tabelas: tb_2001, tb_2017 e tb_7017 (regra em backend\utils\bnd_fazenda.py).
#     Sem Desfazer. Grava no Log so quem corrigiu, quando e quantos animais por Produtor.
#
#     ROTAS
#       GET  /consiste/bnd-fazenda            - envio do PDF
#       POST /consiste/bnd-fazenda/analisar   - le o PDF e mostra o que seria corrigido, por Produtor (nao grava)
#       POST /consiste/bnd-fazenda/corrigir   - le o PDF guardado DE NOVO e GRAVA a correcao (Regra #73: nada vem pronto do navegador)
#
#   v1.0.0: Criacao (BND/Fazenda, Sessao 132, 18/11/2026).
# =========================================================

import os
import re
import secrets
import time
import traceback

from flask import Blueprint, render_template, request, session
from sqlalchemy.orm import Session

from backend.database import engine
from backend.leitores import leitor_mapa_extrato_vivos as leitor
from backend.routers.auth import redirecionar_home
from backend.utils import bnd_fazenda as bf
from backend.utils import carga_animais as ca
from backend.utils.multitenant import get_db_produtor

bnd_fazenda_consiste = Blueprint('bnd_fazenda_consiste', __name__)

PASTA_TEMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'storage', 'bnd_corrige_tmp')
PADRAO_TOKEN = re.compile(r'^[0-9a-f]{32}$')
TEMPLATE = 'consiste/consiste_bnd_fazenda.html'


def _acesso_negado():
    if 'usuario_id' not in session or session.get('usuario_perfil') != 'CONSISTE':
        return redirecionar_home(session.get('usuario_perfil'))
    return None


def _contexto(**extra):
    base = dict(
        usuario_nome=session.get('usuario_nome'), usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'), nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='bnd_fazenda', mensagem=None, mensagem_tipo=None, itens=None, token=None, nome_arquivo=None, aplicado=False,
    )
    base.update(extra)
    return base


def _caminho_token(token):
    if not token or not PADRAO_TOKEN.match(token):
        return None
    return os.path.normpath(os.path.join(PASTA_TEMP, token + '.pdf'))


def _limpar_antigos():
    try:
        for nome in os.listdir(PASTA_TEMP):
            c = os.path.join(PASTA_TEMP, nome)
            if nome.endswith('.pdf') and time.time() - os.path.getmtime(c) > 86400:
                os.remove(c)
    except OSError:
        pass


def _apagar(caminho):
    try:
        if caminho and os.path.exists(caminho):
            os.remove(caminho)
    except OSError:
        pass


def _processar(caminho, aplicar, id_usuario):
    """Le o Extrato e, para cada Produtor do arquivo, calcula (ou grava, se aplicar) a correcao. Devolve a lista de itens da tela."""
    partes = leitor.ler_partes(caminho)
    itens = []
    for parte in partes:
        cab, animais = parte['cabecalho'], parte['animais']
        item = {'produtor': cab.get('produtor_nome') or '(sem Produtor no arquivo)', 'documento': cab.get('produtor_documento') or '',
                'propriedade': cab.get('propriedade_nome') or '', 'qtd_extrato': len(animais), 'nao_lidas': len(parte['linhas_nao_lidas']),
                'status': 'pulado', 'mensagens': [], 'plano': None, 'na_fazenda': 0}
        with Session(engine) as pub:
            racas = ca.racas_do_cadastro(pub)
            produtor, propriedade, vinculo, erros = ca.resolver_destino(pub, cab)
            destino = None
            if produtor is not None and propriedade is not None and vinculo is not None:
                destino = {'id_produtor': produtor.id, 'id_propriedade': propriedade.id, 'produtor': produtor.nome, 'propriedade': propriedade.nome}
        if destino is None:
            item['mensagens'] = [e['mensagem'] for e in erros] or ['Produtor ou Propriedade não encontrados no Orion.']
            itens.append(item)
            continue
        item['produtor'], item['propriedade'] = destino['produtor'], destino['propriedade']
        if not animais:
            item['mensagens'] = ['Nenhum animal lido para este Produtor.']
            itens.append(item)
            continue
        try:
            with get_db_produtor(destino['id_produtor']) as db:
                fazenda = bf.ler_fazenda(db, destino['id_propriedade'])
                item['na_fazenda'] = len(fazenda)
                if aplicar:
                    try:
                        item['plano'] = bf.aplicar_correcao(db, destino['id_propriedade'], fazenda, animais, racas, id_usuario)
                        db.commit()
                        item['status'] = 'corrigido'
                    except Exception:
                        db.rollback()
                        raise
                else:
                    item['plano'] = bf.plano_correcao(fazenda, animais, racas)
                    item['status'] = 'pronto'
        except Exception as e:
            traceback.print_exc()
            item['status'] = 'erro'
            item['mensagens'] = [f'Não foi possível {"gravar" if aplicar else "analisar"} este Produtor; nada foi alterado nele ({type(e).__name__}).']
        itens.append(item)
    return itens


@bnd_fazenda_consiste.route('/consiste/bnd-fazenda')
def tela():
    negado = _acesso_negado()
    if negado:
        return negado
    return render_template(TEMPLATE, **_contexto())


@bnd_fazenda_consiste.route('/consiste/bnd-fazenda/analisar', methods=['POST'])
def analisar():
    negado = _acesso_negado()
    if negado:
        return negado
    arq = request.files.get('arquivo')
    if arq is None or not arq.filename:
        return render_template(TEMPLATE, **_contexto(mensagem='Escolha o arquivo PDF do Extrato de Animais Vivos.', mensagem_tipo='erro'))
    conteudo = arq.read()
    if not conteudo.startswith(b'%PDF'):
        return render_template(TEMPLATE, **_contexto(mensagem='O arquivo enviado não é um PDF. Envie o "Extrato de Animais Vivos" do MAPA.', mensagem_tipo='erro'))
    os.makedirs(PASTA_TEMP, exist_ok=True)
    _limpar_antigos()
    token = secrets.token_hex(16)
    caminho = _caminho_token(token)
    with open(caminho, 'wb') as f:
        f.write(conteudo)
    try:
        itens = _processar(caminho, False, session['usuario_id'])
    except Exception as e:
        traceback.print_exc()
        _apagar(caminho)
        return render_template(TEMPLATE, **_contexto(mensagem=f'Não consegui ler este PDF (nada foi alterado): {type(e).__name__}.', mensagem_tipo='erro'))
    if not itens:
        _apagar(caminho)
        return render_template(TEMPLATE, **_contexto(mensagem='Não encontrei animais neste PDF. Confira se é o "Extrato de Animais Vivos" do MAPA.', mensagem_tipo='erro'))
    pode = any(i['status'] == 'pronto' for i in itens)
    return render_template(TEMPLATE, **_contexto(itens=itens, token=token if pode else None, nome_arquivo=arq.filename[:120]))


@bnd_fazenda_consiste.route('/consiste/bnd-fazenda/corrigir', methods=['POST'])
def corrigir():
    negado = _acesso_negado()
    if negado:
        return negado
    caminho = _caminho_token(request.form.get('token', ''))
    if caminho is None or not os.path.exists(caminho):
        return render_template(TEMPLATE, **_contexto(mensagem='O arquivo enviado não está mais disponível. Envie o PDF de novo.', mensagem_tipo='erro'))
    try:
        itens = _processar(caminho, True, session['usuario_id'])
    except Exception as e:
        traceback.print_exc()
        return render_template(TEMPLATE, **_contexto(mensagem=f'Não foi possível corrigir (nada foi alterado): {type(e).__name__}.', mensagem_tipo='erro'))
    _apagar(caminho)
    ok = sum(1 for i in itens if i['status'] == 'corrigido')
    pulados = len(itens) - ok
    msg = f'Correção concluída em {ok} Produtor(es).' + (f' {pulados} não foram corrigidos: veja abaixo.' if pulados else '')
    return render_template(TEMPLATE, **_contexto(itens=itens, aplicado=True, mensagem=msg, mensagem_tipo='ok' if not pulados else 'erro'))

# =========================================================
# FIM DE ARQUIVO: backend\routers\bnd_fazenda_consiste.py
# =========================================================
