# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\troca_rfid.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-09 16:10 -03
# ATUALIZADO EM: 2026-11-16 10:55 -03
# VERSAO: 1.5.0
# v1.5.0: Sessao 128 (2026-11-16 10:55 -03) - AUDITORIA ETAPA 7c (Regras #71 e #74): trava do Produtor na gravacao (RFID novo nao pode ir para 2 animais ao mesmo tempo) e erro de gravacao agora fica no log do servidor. REVERSAO: .bak_antes_etapa7c.
# v1.4.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (2 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Tela "Troca de RFID" (a "Linkagem" do GERAS) - Sessao 092, pedido de
#     Benedito: o animal JA tem o brinco SISBOV mas perdeu o RFID (o elemento
#     amarelo da orelha esquerda). Troca-se SO o RFID; o SISBOV, o manejo e
#     todo o resto do animal ficam como estao. O RFID antigo deixa de existir
#     no banco e o novo passa a ser o do brinco SISBOV.
#
#     FLUXO (uma tela simples, igual para Leitor e Bastao):
#       1. digita o SISBOV completo (15 digitos);
#       2. o sistema mostra o animal: manejo, sexo, raca, idade em meses
#          (atualizada), liberacao de abate, ultimo peso e o RFID atual;
#       3. le o RFID NOVO (15 digitos) - o sistema confere na hora;
#       4. grava (com confirmacao) e avisa "RFID substituido".
#
#     ONDE O RFID MORA (decisao de Benedito: "em todos eles"), trocado na
#     MESMA transacao:
#       tb_2001 (o animal), tb_2017_movimentacoes (por id_animal),
#       tb_7017_entrada_brincos_rfid, tb_3008_brincos_saida, tb_4003_pesos e
#       tb_5001_brincagem (todas as linhas daquele SISBOV, para o RFID antigo
#       realmente deixar de existir). tb_5003, tb_6004 e tb_6006 NAO sao
#       tocadas.
#
#     ANIMAL ENCONTRADO EM: tb_2001 (rebanho da fazenda) ou, se ainda nao
#     esta la, na leitura pendente do brete (tb_5001 sts=False, sem
#     Comunicado).
#
#     REGRAS DO RFID NOVO (mesma regra do Bastao + as da troca):
#       - exatamente 15 digitos;
#       - diferente do SISBOV (RFID igual ao SISBOV e bloqueado);
#       - diferente do RFID que o animal ja tem;
#       - livre: nao pode estar em nenhum animal da tb_2001 nem em leitura
#         pendente da tb_5001 (sts=False). A tb_7017 NAO e consultada (o chip
#         e reaproveitavel);
#       - confusao de digitacao: se o numero digitado como SISBOV for na
#         verdade um RFID de animal, ou o RFID novo for na verdade um SISBOV,
#         a tela avisa (Benedito: "o usuario pode ter invertido").
#
#     LOG / DESFAZER: uma operacao (modulo 'troca_rfid') com uma linha de Log
#     por registro alterado (guarda o RFID antigo); o Desfazer generico do
#     log_operacoes.py (janela de 24h) devolve o RFID antigo.
#
#     FAZENDA EM USO (Regra de Ouro #13): a selecao de Propriedade e pulada;
#     Propriedade diferente da fazenda em uso = negado (403 no AJAX). Voltar
#     vai para o Hub novo de Brincagem.
#
#     v1.0.0: Criacao (Sessao 092, 09/10/2026, 16:10 -03).
#     v1.1.0: Sessao 092 (09/10/2026, 17:35 -03) - BLOCKCHAIN (piloto): depois de trocar o
#             RFID de animal do REBANHO (tb_2001), registra o evento TROCA_RFID na fila
#             (backend/utils/blockchain.py), na MESMA transacao, antes do commit - com o
#             RFID antigo e o novo na ficha. So gera evento se o Produtor tem provedor
#             ligado; falha do blockchain nunca derruba a troca. Leitura pendente do brete
#             (ainda sem Comunicado) nao gera evento. Nenhuma outra mudanca.
#     v1.3.0: Sessao 114 (2026-11-04 15:00 -03) - Buscar aceita o MANEJO (6 numeros, +DV nos brincos 105) no lugar do SISBOV; mesmas mensagens e regras das outras telas (Manejo repetido pede o DV). REVERSAO: .bak_antes_s114_manejo.
#     v1.3.1: Sessao 117 (2026-11-06 18:05 -03) - Cabecalho mostra o Produtor LOGADO, nao o primeiro vinculo da Propriedade (defeito com 2+ Produtores). Nenhuma outra mudanca. REVERSAO: .bak_antes_s117_produtor.
# =========================================================

import logging
import re
from datetime import date, timedelta

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, PropriedadeProdutor, Produtor
from backend.models.tb_5001_brincagem import Brincagem
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_3008_brincos_saida import BrincoSaida
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.animal_saiu import mensagem_animal_saiu   # v1.2.0 - onde o animal esta
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.blockchain import registrar_evento, ficha_do_animal, ficha_do_dono, TIPO_TROCA_RFID
from backend.utils.regras_sisbov import DIAS_POR_MES, MODELO_SISBOV_ANTIGO, modelo_do_sisbov
from backend.routers.saida_leitor import (   # v1.3.0 - Manejo: mesmas mensagens das outras telas
    TAMANHO_MANEJO, MENSAGEM_MANEJO_INCORRETO, MENSAGEM_DV_MANEJO_INCORRETO, MENSAGEM_MANEJO_PEDE_DV, MENSAGEM_MANEJO_DUPLICADO,
)


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
troca_rfid = Blueprint('troca_rfid', __name__)


@troca_rfid.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


NOME_MODULO_LOG = 'troca_rfid'
URL_HUB_BRINCAGEM = '/produtor/hub-novo/brincagem'
DIAS_LIBERACAO_ABATE = 90          # Liberacao de Abate = Data de Brincagem + 90 dias
TAMANHO = 15
SO_DIGITOS = re.compile(r'^\d{15}$')


# -------------------------------------------------------
# Funcoes auxiliares
# -------------------------------------------------------
# v1.5.0 (Etapa 7c) - trava por Produtor: o RFID e unico em todo o schema do Produtor (todas as Propriedades dele).
TRAVA_RFID_PRODUTOR = 81003        # + id_produtor
logger = logging.getLogger(__name__)


def _propriedade_do_usuario(id_propriedade):
    try:
        id_int = int(id_propriedade)
    except (TypeError, ValueError):
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and par_em_uso.id_propriedade != id_int:
        return False
    return any(
        par.id_propriedade == id_int and par.id_produtor == session.get('id_produtor')
        for par in pares
    )


def _negado():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect('/produtor/troca-rfid/iniciar')
    return redirecionar_home()


def _url_voltar():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return '/produtor/troca-rfid/iniciar'
    return URL_HUB_BRINCAGEM


def _buscar_propriedade_produtor(id_propriedade):
    with Session(engine) as db:
        propriedade = db.get(Propriedade, id_propriedade)
        produtor = None
        if propriedade:
            vinculo = db.query(PropriedadeProdutor).filter_by(
                id_propriedade=propriedade.id, id_produtor=session['id_produtor'], data_fim=None   # v1.3.1: Produtor LOGADO
            ).first()
            if vinculo:
                produtor = db.get(Produtor, vinculo.id_produtor)
        nome_propriedade = propriedade.nome if propriedade else '-'
        nome_produtor = produtor.nome if produtor else '-'
    return nome_propriedade, nome_produtor


def _contexto_tela():
    return {
        'usuario_nome':   session.get('usuario_nome'),
        'usuario_perfil': session.get('usuario_perfil'),
        'cor_primaria':   session.get('cor_primaria', '#D4370A'),
        'nome_sistema':   session.get('nome_sistema', 'Orion SISBOV'),
        'menu_ativo':     'brincagem',
    }


def _data_br(data):
    return data.strftime('%d/%m/%Y') if data else ''


def _numero(valor):
    # Somente digitos, sem espacos (o leitor as vezes manda espaco/quebra no fim).
    return re.sub(r'\s+', '', str(valor or ''))


# -------------------------------------------------------
# v1.3.0 - Acha o SISBOV pelo MANEJO (+ DV nos brincos 105), no rebanho (tb_2001) e na leitura pendente do brete (tb_5001).
# Devolve (sisbov, mensagem_de_erro, pede_dv).
# -------------------------------------------------------
def _sisbov_do_manejo(db, id_propriedade, manejo, dv):
    if len(manejo) != TAMANHO_MANEJO or not (manejo.isascii() and manejo.isdecimal()):
        return None, MENSAGEM_MANEJO_INCORRETO, False
    if dv and not (len(dv) == 1 and dv.isascii() and dv.isdecimal()):
        return None, MENSAGEM_DV_MANEJO_INCORRETO, False
    sisbovs = {s for (s,) in db.query(Entrada.sisbov).filter(Entrada.id_propriedade == id_propriedade, Entrada.manejo == manejo).all() if s}
    sisbovs |= {
        s for (s,) in db.query(Brincagem.sisbov)
        .filter(Brincagem.id_propriedade == id_propriedade, Brincagem.manejo == manejo,
                Brincagem.sts == False, Brincagem.numero_comunicado.is_(None))   # noqa: E712
        .all() if s
    }
    if dv:
        sisbovs = {s for s in sisbovs if modelo_do_sisbov(s) != MODELO_SISBOV_ANTIGO or s[-1] == dv}
    if not sisbovs:
        return None, (mensagem_animal_saiu(db, id_propriedade, manejo=manejo) or 'Manejo não encontrado nesta fazenda.'), False
    if len(sisbovs) > 1:
        if any(modelo_do_sisbov(s) == MODELO_SISBOV_ANTIGO for s in sisbovs) and not dv:
            return None, MENSAGEM_MANEJO_PEDE_DV, True
        return None, MENSAGEM_MANEJO_DUPLICADO, False
    return sisbovs.pop(), None, False


def _texto_do_banco(valor):
    return None if valor is None else str(valor)


# -------------------------------------------------------
# Rota: GET /produtor/troca-rfid/iniciar - ponto de partida (card do Hub)
# -------------------------------------------------------
@troca_rfid.route('/produtor/troca-rfid/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/troca-rfid/tela?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/troca-rfid/tela?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None if pares else 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
        titulo='Troca de RFID — Selecionar Propriedade',
        proximo='/produtor/troca-rfid/tela',
        campo_propriedade='id_propriedade',
        voltar=URL_HUB_BRINCAGEM,
        **_contexto_tela(),
    )


# -------------------------------------------------------
# Rota: GET /produtor/troca-rfid/tela?id_propriedade=X
# -------------------------------------------------------
@troca_rfid.route('/produtor/troca-rfid/tela')
def tela():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()

    nome_propriedade, nome_produtor = _buscar_propriedade_produtor(int(id_propriedade))

    return render_template(
        'produtor/troca_rfid.html',
        id_propriedade=id_propriedade,
        propriedade_nome=nome_propriedade,
        produtor_nome=nome_produtor,
        url_voltar=_url_voltar(),
        **_contexto_tela(),
    )


# -------------------------------------------------------
# Localiza o animal pelo SISBOV: primeiro no rebanho (tb_2001), depois na
# leitura pendente do brete (tb_5001 sts=False, sem Comunicado).
# Devolve (tipo, registro) com tipo 'rebanho' | 'leitura', ou (None, None).
# -------------------------------------------------------
def _localizar_animal(db, id_propriedade, sisbov, travar=False):
    consulta = db.query(Entrada).filter(Entrada.sisbov == sisbov, Entrada.id_propriedade == id_propriedade)
    if travar:
        consulta = consulta.with_for_update()
    entrada = consulta.first()
    if entrada is not None:
        return 'rebanho', entrada

    consulta = (
        db.query(Brincagem)
        .filter(
            Brincagem.sisbov == sisbov,
            Brincagem.id_propriedade == id_propriedade,
            Brincagem.sts == False,   # noqa: E712
            Brincagem.numero_comunicado.is_(None),
        )
        .order_by(Brincagem.id.desc())
    )
    if travar:
        consulta = consulta.with_for_update()
    leitura = consulta.first()
    if leitura is not None:
        return 'leitura', leitura
    return None, None


def _ficha_animal(db, id_propriedade, tipo, registro):
    # Dados para a conferencia na tela (tudo montado em tipos simples).
    nascimento = registro.nascimento
    hoje = date.today()
    idade_meses = None
    if nascimento is not None:
        idade_meses = max((hoje - nascimento).days // DIAS_POR_MES, 0)

    if tipo == 'rebanho':
        liberacao = registro.liberacao_abate
        if liberacao is None and registro.data_brincagem is not None:
            liberacao = registro.data_brincagem + timedelta(days=DIAS_LIBERACAO_ABATE)
        situacao = 'Animal do rebanho'
    else:
        liberacao = (registro.data_brincagem + timedelta(days=DIAS_LIBERACAO_ABATE)) if registro.data_brincagem else None
        situacao = 'Lido no brete, ainda sem Comunicado'

    raca = db.get(Raca, registro.id_raca) if registro.id_raca else None
    raca_texto = ''
    if raca is not None:
        raca_texto = f'{raca.codigo} - {raca.nome}' if getattr(raca, 'codigo', None) else raca.nome

    ultimo_peso = (
        db.query(Peso)
        .filter(Peso.id_propriedade == id_propriedade, Peso.sisbov == registro.sisbov)
        .order_by(Peso.sequencia.desc())
        .first()
    )
    peso, data_peso = None, None
    if ultimo_peso is not None:
        peso, data_peso = float(ultimo_peso.peso), ultimo_peso.data_pesagem
    elif tipo == 'leitura' and registro.peso is not None:
        peso, data_peso = float(registro.peso), registro.data_brincagem

    return {
        'sisbov': registro.sisbov,
        'manejo': registro.manejo or '',
        'sexo': {'MACHO': 'Macho', 'FEMEA': 'Fêmea'}.get(str(registro.sexo), str(registro.sexo or '')),
        'raca': raca_texto,
        'idade_meses': idade_meses,
        'nascimento': _data_br(nascimento),
        'liberacao_abate': _data_br(liberacao),
        'peso': peso,
        'data_peso': _data_br(data_peso),
        'lote': registro.lote or '',
        'rfid_atual': registro.rfid or '',
        'situacao': situacao,
    }


# -------------------------------------------------------
# Confere o RFID novo. Devolve texto de erro, ou None se estiver tudo certo.
# -------------------------------------------------------
def _erro_rfid_novo(db, id_propriedade, sisbov, rfid_atual, rfid_novo):
    if not SO_DIGITOS.match(rfid_novo):
        return f'O RFID precisa ter exatamente {TAMANHO} dígitos (somente números).'
    if rfid_novo == sisbov:
        return 'O RFID não pode ser igual ao número SISBOV.'
    if rfid_atual and rfid_novo == rfid_atual:
        return 'Este já é o RFID atual do animal. Leia o RFID novo.'

    # Digitou o SISBOV de algum animal no lugar do RFID?
    eh_sisbov = (
        db.query(Entrada.id).filter(Entrada.sisbov == rfid_novo).first() is not None
        or db.query(EntradaBrincoRfid.id).filter(EntradaBrincoRfid.sisbov == rfid_novo).first() is not None
    )
    if eh_sisbov:
        return 'Este número é um SISBOV, não um RFID. Leia o RFID do brinco novo (o elemento amarelo).'

    dono = db.query(Entrada.sisbov).filter(Entrada.rfid == rfid_novo).first()
    if dono is not None:
        return f'Este RFID já está em uso pelo animal SISBOV {dono[0]}.'
    pendente = (
        db.query(Brincagem.sisbov)
        .filter(Brincagem.rfid == rfid_novo, Brincagem.sts == False)   # noqa: E712
        .first()
    )
    if pendente is not None:
        return f'Este RFID já foi lido na brincagem do animal SISBOV {pendente[0] or "(sem SISBOV)"}, ainda sem Comunicado.'
    return None


# -------------------------------------------------------
# Rota: POST /produtor/troca-rfid/buscar (AJAX)
# Corpo: {id_propriedade, sisbov}. Devolve a ficha do animal.
# -------------------------------------------------------
@troca_rfid.route('/produtor/troca-rfid/buscar', methods=['POST'])
def buscar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = _numero(dados.get('sisbov'))
    manejo = _numero(dados.get('manejo'))   # v1.3.0 - pode achar o animal pelo Manejo (+ DV)
    dv     = _numero(dados.get('dv'))

    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário.'}), 403
    id_prop = int(id_propriedade)

    if not (manejo and not sisbov) and not SO_DIGITOS.match(sisbov):
        return jsonify({'erro': f'Digite o SISBOV completo: {TAMANHO} dígitos (somente números).'}), 400

    with get_db_produtor(session['id_produtor']) as db:
        if manejo and not sisbov:
            sisbov, erro_manejo, pede_dv = _sisbov_do_manejo(db, id_prop, manejo, dv)
            if erro_manejo:
                return jsonify({'erro': erro_manejo, 'pede_dv': pede_dv}), 404
        tipo, registro = _localizar_animal(db, id_prop, sisbov)
        if registro is None:
            # Digitou o RFID no lugar do SISBOV?
            dono = db.query(Entrada.sisbov).filter(Entrada.rfid == sisbov, Entrada.id_propriedade == id_prop).first()
            if dono is None:
                dono = (
                    db.query(Brincagem.sisbov)
                    .filter(Brincagem.rfid == sisbov, Brincagem.id_propriedade == id_prop, Brincagem.sts == False)   # noqa: E712
                    .first()
                )
            if dono is not None and dono[0]:
                return jsonify({'erro': f'Este número é um RFID (do animal SISBOV {dono[0]}), não um SISBOV. Digite o número do brinco SISBOV.'}), 404
            return jsonify({'erro': mensagem_animal_saiu(db, id_prop, sisbov=sisbov) or 'SISBOV não encontrado nesta fazenda.'}), 404   # v1.2.0
        ficha = _ficha_animal(db, id_prop, tipo, registro)

    return jsonify({'sucesso': True, 'animal': ficha})


# -------------------------------------------------------
# Rota: POST /produtor/troca-rfid/checar-rfid (AJAX)
# Corpo: {id_propriedade, sisbov, rfid}. Confere o RFID novo (sem gravar).
# -------------------------------------------------------
@troca_rfid.route('/produtor/troca-rfid/checar-rfid', methods=['POST'])
def checar_rfid():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = _numero(dados.get('sisbov'))
    rfid_novo = _numero(dados.get('rfid'))

    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário.'}), 403
    id_prop = int(id_propriedade)

    with get_db_produtor(session['id_produtor']) as db:
        tipo, registro = _localizar_animal(db, id_prop, sisbov)
        if registro is None:
            return jsonify({'erro': 'Animal não encontrado. Busque o SISBOV de novo.'}), 404
        erro = _erro_rfid_novo(db, id_prop, sisbov, registro.rfid or '', rfid_novo)

    if erro:
        return jsonify({'erro': erro}), 409
    return jsonify({'sucesso': True})


# -------------------------------------------------------
# Atualiza o RFID de um registro e grava no Log (antes/depois). O depois e
# o valor COMO O BANCO guarda (flush + refresh): o Desfazer compara como texto.
# -------------------------------------------------------
def _trocar_no_registro(db, id_operacao, tabela, registro, rfid_novo):
    if (registro.rfid or None) == rfid_novo:
        return False
    antes = {'rfid': _texto_do_banco(registro.rfid)}
    registro.rfid = rfid_novo
    db.flush()
    db.refresh(registro)
    registrar_item(
        db, id_operacao=id_operacao, tabela=tabela, id_registro=registro.id,
        tipo_mudanca='UPDATE', dados_antes=antes,
        dados_depois={'rfid': _texto_do_banco(registro.rfid)},
    )
    return True


# -------------------------------------------------------
# Rota: POST /produtor/troca-rfid/gravar (AJAX)
# Corpo: {id_propriedade, sisbov, rfid}. Confere tudo de novo no servidor e
# troca o RFID nas tabelas, na mesma transacao + Log.
# -------------------------------------------------------
@troca_rfid.route('/produtor/troca-rfid/gravar', methods=['POST'])
def gravar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = _numero(dados.get('sisbov'))
    rfid_novo = _numero(dados.get('rfid'))

    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário.'}), 403
    id_prop = int(id_propriedade)

    if not SO_DIGITOS.match(sisbov):
        return jsonify({'erro': f'SISBOV inválido: são {TAMANHO} dígitos.'}), 400

    with get_db_produtor(session['id_produtor']) as db:
        # v1.5.0 - trava ANTES, confere DENTRO (Regra #71): dois bretes nao gravam o mesmo RFID ao mesmo tempo.
        db.execute(text('SELECT pg_advisory_xact_lock(:ns, :id)'), {'ns': TRAVA_RFID_PRODUTOR, 'id': int(session['id_produtor'])})
        tipo, registro = _localizar_animal(db, id_prop, sisbov, travar=True)
        if registro is None:
            return jsonify({'erro': 'Animal não encontrado (pode ter saído). Nada foi alterado.'}), 404

        rfid_antigo = registro.rfid or ''
        erro = _erro_rfid_novo(db, id_prop, sisbov, rfid_antigo, rfid_novo)
        if erro:
            return jsonify({'erro': erro}), 409

        descricao = f'Troca de RFID — SISBOV {sisbov} — {rfid_antigo or "sem RFID"} para {rfid_novo}'[:120]

        try:
            id_operacao = registrar_operacao(
                db,
                id_usuario=session['usuario_id'],
                id_propriedade=id_prop,
                modulo=NOME_MODULO_LOG,
                descricao=descricao,
            )
            trocados = 0

            # tb_2001 (o animal) e tb_2017 (movimentacoes, por id_animal)
            if tipo == 'rebanho':
                trocados += _trocar_no_registro(db, id_operacao, 'tb_2001', registro, rfid_novo)
                for movimentacao in db.query(Movimentacao).filter(Movimentacao.id_animal == registro.id).all():
                    trocados += _trocar_no_registro(db, id_operacao, 'tb_2017_movimentacoes', movimentacao, rfid_novo)

            # tb_7017, tb_3008, tb_4003 e tb_5001: todas as linhas daquele SISBOV nesta fazenda
            for modelo, tabela in (
                (EntradaBrincoRfid, 'tb_7017_entrada_brincos_rfid'),
                (BrincoSaida,       'tb_3008_brincos_saida'),
                (Peso,              'tb_4003_pesos'),
                (Brincagem,         'tb_5001_brincagem'),
            ):
                for linha in db.query(modelo).filter(modelo.id_propriedade == id_prop, modelo.sisbov == sisbov).all():
                    trocados += _trocar_no_registro(db, id_operacao, tabela, linha, rfid_novo)

            # v1.1.0 - BLOCKCHAIN: evento na fila (so animal do rebanho; sem provedor ligado nao faz nada)
            if tipo == 'rebanho':
                registrar_evento(
                    db, id_prop, TIPO_TROCA_RFID, registro.sisbov,
                    ficha_do_animal(db, registro, extras={'rfid_anterior': rfid_antigo or None, 'rfid_novo': rfid_novo}),
                    ficha_dono=ficha_do_dono(db, id_prop),
                    id_usuario=session['usuario_id'], id_operacao=id_operacao,
                )

            db.commit()
        except Exception:
            db.rollback()
            logger.exception('Troca de RFID: falha ao gravar (SISBOV %s, Propriedade %s)', sisbov, id_prop)   # v1.5.0 - o motivo fica no log
            return jsonify({'erro': 'Não foi possível gravar. Nada foi alterado.'}), 500

    return jsonify({
        'sucesso': True,
        'mensagem': 'RFID substituído.',
        'rfid_antigo': rfid_antigo,
        'rfid_novo': rfid_novo,
        'registros': int(trocados),
    })

# =========================================================
# FIM DE ARQUIVO: backend\routers\troca_rfid.py
# =========================================================
