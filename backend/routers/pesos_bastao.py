# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\pesos_bastao.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-04 14:45 -03
# ATUALIZADO EM: 2026-11-16 11:20 -03
# VERSAO: 1.2.0
# v1.2.0: Sessao 128 (2026-11-16 11:20 -03) - AUDITORIA ETAPA 7e: erro ao listar as pesagens recentes agora vai para o log do servidor (antes sumia em silencio). REVERSAO: .bak_antes_etapa7e.
# v1.1.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     PESOS - Leitor de Peso com BASTAO (Sessao 114, pacote 1). Tela PROPRIA; o Leitor de Peso (pesos_leitor.py)
#     fica como esta. Navegacao: Home -> card Pesagens -> Hub de Pesos (slug 'pesos') -> card "Leitor de Peso com Bastao".
#
#     REUSO (peca unica): toda a conferencia do animal (_validar: DV, animal que ja saiu/morto, brinco do estoque, pesagem
#     repetida na data, data anterior a ultima pesagem), o Inconforme (tb_4007), a Selecao e as rotas GRAVAR e EXCLUIR PESAGEM
#     vem de pesos_leitor.py (a tela do Bastao chama as mesmas rotas). Aqui entra so o que o Bastao tem de novo:
#     achar o animal pelo RFID.
#
#     FLUXO (igual ao Leitor de Peso): iniciar -> selecao (Data da Pesagem) -> leitura. Cursor sempre no RFID: o bastao le o
#     RFID (15 digitos); se o animal tem esse RFID cadastrado nesta Propriedade, o Orion acha o animal sozinho (SISBOV e Manejo
#     vem preenchidos) e segue o fluxo normal (Peso, Perdeu Elemento, Observacoes, Gravar). RFID que nao existe: mensagem
#     vermelha, e o brete pode seguir pelo SISBOV ou pelo Manejo na mesma tela.
#
#     Todo RFID recusado (nao encontrado, duplicado, animal morto/ja saiu, brinco do estoque...) fica gravado em
#     tb_4007_pesagem_inconformes, como no Leitor de Peso (o RFID vai no campo sisbov, escrito "RFID <numero>").
#
#     v1.0.0: Criacao (Sessao 114, 04/11/2026, 14:45 -03). Molde: saida_bastao.py.
#     REVERSAO: remover este arquivo, os 2 templates pesos_bastao_*.html, o registro em app.py, o card do Hub e as linhas de permissoes.py.
# =========================================================

from datetime import date
import logging

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, PropriedadeProdutor, Produtor
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.pesos_leitor import (
    _iniciar_generico, _negado, _registrar_inconforme, _validar, _mensagem_sem_animal,
    _contar_gravados_na_data, _lidos_da_data,
    URL_HUB, ORIGEM_PESO, ELEMENTOS, GMD_AVISO, QUEDA_AVISO_PCT, MENSAGENS_ERRO_SELECAO,
)
from backend.routers.saida_leitor import (
    _propriedade_do_usuario, _data_br, _ler_data_br,
    MENSAGEM_BRINCO_NO_ESTOQUE, MENSAGEM_BRINCO_CANCELADO,
)
from backend.routers.saida_bastao import (
    TAMANHO_RFID, MENSAGEM_RFID_TAMANHO, MENSAGEM_RFID_NAO_ENCONTRADO, MENSAGEM_RFID_DUPLICADO,
)
from backend.utils.multitenant import get_db_produtor


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
pesos_bastao = Blueprint('pesos_bastao', __name__)
logger = logging.getLogger(__name__)


@pesos_bastao.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


URL_INICIAR = '/produtor/pesos-bastao/iniciar'
URL_SELECAO = '/produtor/pesos-bastao/selecao'


# -------------------------------------------------------
# Acha o animal pelo RFID. Devolve (animal, mensagem_de_bloqueio).
# (A mensagem de animal morto/que ja saiu vem de pesos_leitor._mensagem_sem_animal: nao grava em tb_5003.)
# -------------------------------------------------------
def _buscar_animal_por_rfid(db, id_propriedade, rfid):
    if len(rfid) != TAMANHO_RFID or not (rfid.isascii() and rfid.isdecimal()):
        return None, MENSAGEM_RFID_TAMANHO
    candidatos = (
        db.query(Entrada)
        .filter(Entrada.id_propriedade == int(id_propriedade), Entrada.rfid == rfid)
        .all()
    )
    if len(candidatos) == 1:
        return candidatos[0], None
    if len(candidatos) > 1:
        return None, MENSAGEM_RFID_DUPLICADO
    # nao esta mais em tb_2001: se saiu ou morreu, usa a mesma mensagem do Leitor de Peso
    saida = (
        db.query(SaidaAnimal)
        .filter(SaidaAnimal.rfid == rfid)
        .order_by(SaidaAnimal.data_saida.desc(), SaidaAnimal.id.desc())
        .first()
    )
    if saida is not None and saida.sisbov:
        return None, _mensagem_sem_animal(db, id_propriedade, saida.sisbov)
    # nao saiu: ve se o RFID e de um brinco do estoque (tb_7017, status vazio) ou cancelado
    brinco = (
        db.query(EntradaBrincoRfid)
        .filter(EntradaBrincoRfid.rfid == rfid, EntradaBrincoRfid.id_propriedade == int(id_propriedade))
        .first()
    )
    if brinco is not None:
        status = (brinco.status or '').strip().upper()
        if status == '':
            return None, MENSAGEM_BRINCO_NO_ESTOQUE
        if status == 'CANCELADO':
            return None, MENSAGEM_BRINCO_CANCELADO
    return None, MENSAGEM_RFID_NAO_ENCONTRADO


# -------------------------------------------------------
# Rota: GET /produtor/pesos-bastao/iniciar - ponto de partida (escolhe a Propriedade).
# -------------------------------------------------------
@pesos_bastao.route('/produtor/pesos-bastao/iniciar')
def iniciar():
    return _iniciar_generico('Leitor de Peso com Bastão — Selecionar Propriedade', URL_SELECAO)


# -------------------------------------------------------
# Rota: GET /produtor/pesos-bastao/selecao - Selecao (so a Data da Pesagem).
# -------------------------------------------------------
@pesos_bastao.route('/produtor/pesos-bastao/selecao')
def selecao():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado_bastao()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    url_voltar = URL_INICIAR if (len(pares) > 1 and resolver_fazenda_em_uso(pares) is None) else URL_HUB

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
        nome_produtor = None
        if propriedade:
            vinculo = db.query(PropriedadeProdutor).filter_by(
                id_propriedade=propriedade.id, id_produtor=session['id_produtor'], data_fim=None
            ).first()
            if vinculo:
                produtor = db.get(Produtor, vinculo.id_produtor)
                if produtor:
                    nome_produtor = produtor.nome

    try:
        with get_db_produtor(session['id_produtor']) as db_prod:
            linhas = (
                db_prod.query(Peso.data_pesagem, func.count(Peso.id))
                .filter(Peso.id_propriedade == int(id_propriedade), Peso.origem == ORIGEM_PESO)
                .group_by(Peso.data_pesagem)
                .order_by(Peso.data_pesagem.desc())
                .limit(8)
                .all()
            )
            recentes = [{'data': _data_br(d), 'quantidade': int(q)} for d, q in linhas]
    except Exception:
        logger.exception('Pesos Bastao: falha ao listar as pesagens recentes')
        recentes = []

    return render_template(
        'produtor/pesos_bastao_selecao.html',
        erro=MENSAGENS_ERRO_SELECAO.get(request.args.get('erro', '')),
        propriedade=propriedade,
        nome_produtor=nome_produtor,
        id_propriedade=id_propriedade,
        url_voltar=url_voltar,
        recentes=recentes,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='pesagens',
    )


def _negado_bastao():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect(URL_INICIAR)
    return redirecionar_home()


# -------------------------------------------------------
# Rota: GET /produtor/pesos-bastao/leitura - Tela de Leitura.
# -------------------------------------------------------
@pesos_bastao.route('/produtor/pesos-bastao/leitura')
def leitura():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado_bastao()

    base = f'{URL_SELECAO}?id_propriedade={id_propriedade}'
    data_pesagem = _ler_data_br(request.args.get('data_pesagem', ''))
    if data_pesagem is None:
        return redirect(f'{base}&erro=data')
    if data_pesagem > date.today():
        return redirect(f'{base}&erro=futura')

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))

    with get_db_produtor(session['id_produtor']) as db:
        total_gravados = _contar_gravados_na_data(db, id_propriedade, data_pesagem)
        lidos = _lidos_da_data(db, id_propriedade, data_pesagem)

    return render_template(
        'produtor/pesos_bastao_leitura.html',
        propriedade=propriedade,
        id_propriedade=id_propriedade,
        data_pesagem=_data_br(data_pesagem),
        total_gravados=total_gravados,
        lidos=lidos,
        elementos=ELEMENTOS,
        gmd_aviso=GMD_AVISO,
        queda_pct=QUEDA_AVISO_PCT,
        url_selecao=base,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='pesagens',
    )


# -------------------------------------------------------
# Rota: POST /produtor/pesos-bastao/checar (AJAX) - confere o animal assim que o RFID e lido
# (ou o SISBOV / Manejo, quando o chip nao serve). Bloqueio vira Inconforme (menos o pedido de DV).
# GRAVAR e EXCLUIR PESAGEM: a tela chama as rotas do pesos_leitor.
# -------------------------------------------------------
@pesos_bastao.route('/produtor/pesos-bastao/checar', methods=['POST'])
def checar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    rfid   = (dados.get('rfid') or '').strip()
    sisbov = (dados.get('sisbov') or '').strip()
    manejo = (dados.get('manejo') or '').strip()
    dv     = (dados.get('dv') or '').strip()
    data_pesagem = _ler_data_br(dados.get('data_pesagem'))

    if not id_propriedade or (not rfid and not sisbov and not manejo) or data_pesagem is None:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou. Volte ao Hub de Pesos e abra de novo.'}), 403

    with get_db_produtor(session['id_produtor']) as db:
        if rfid:
            animal, bloqueio = _buscar_animal_por_rfid(db, id_propriedade, rfid)
            if bloqueio:
                _registrar_inconforme(db, id_propriedade, data_pesagem, f'RFID {rfid}', None, None, bloqueio)
                return jsonify({'bloqueio': True, 'mensagem': bloqueio, 'pede_dv': False})
            # achou o animal pelo chip: a conferencia daqui em diante e a do Leitor, pelo SISBOV dele
            resultado = _validar(db, id_propriedade, data_pesagem, animal.sisbov, '', '')
            identificado = f'RFID {rfid}'
        else:
            resultado = _validar(db, id_propriedade, data_pesagem, sisbov, manejo, dv)
            identificado = sisbov

        if 'bloqueio' in resultado:
            mensagem = resultado['bloqueio']
            pede_dv = bool(resultado.get('pede_dv'))
            if not pede_dv:
                _registrar_inconforme(db, id_propriedade, data_pesagem, identificado, manejo, None, mensagem)
            return jsonify({'bloqueio': True, 'mensagem': mensagem, 'pede_dv': pede_dv})
        ficha = resultado['ficha']

    return jsonify({'ok': True, 'animal': ficha, 'gmd_aviso': GMD_AVISO, 'queda_pct': QUEDA_AVISO_PCT})

# =========================================================
# FIM DE ARQUIVO: backend\routers\pesos_bastao.py
# =========================================================
