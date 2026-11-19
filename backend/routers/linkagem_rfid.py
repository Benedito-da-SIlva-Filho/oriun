# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\linkagem_rfid.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-10 18:20 -03
# ATUALIZADO EM: 2026-11-16 10:55 -03
# VERSAO: 1.3.0
# v1.3.0: Sessao 128 (2026-11-16 10:55 -03) - AUDITORIA ETAPA 7c (Regras #71 e #74): trava do Produtor na gravacao (mesmo RFID nao vai para 2 animais ao mesmo tempo, igual a Troca de RFID) e erro de gravacao agora fica no log do servidor. REVERSAO: .bak_antes_etapa7c.
#
# DESCRICAO:
#     LINKAGEM RFID e BRINCO (Sessao 120, pacote 1) - a "Linkagem Chip+Brinco" do GERAS: liga o RFID (chip) ao brinco SISBOV
#     de animal que JA esta em estoque e AINDA NAO tem RFID. Desenho: Linkagem_Desenho_10-11-2026.md (Projeto).
#     Navegacao: Home -> Hub de Entrada -> grupo "Consultas e correcoes" -> card "Linkagem RFID e Brinco".
#
#     FLUXO (uma tela, serve para Leitor e Bastao): cursor sempre no RFID PRIMEIRO (o bastao le o RFID); o Orion confere o RFID na
#     hora; depois le-se o brinco SISBOV (Leitor ou digitado, 15 digitos): a tela mostra o animal; Lote Novo e Peso sao opcionais;
#     GRAVAR (ou Enter) liga o par. Volta o cursor ao RFID.
#
#     REUSO (peca unica, nada copiado): troca_rfid.py fornece a busca do animal (_localizar_animal: rebanho tb_2001 ou leitura pendente
#     do brete tb_5001), a conferencia do RFID (_erro_rfid_novo: 15 digitos, diferente do SISBOV, nao e SISBOV de animal, nao esta em
#     outro animal nem em leitura pendente) e a troca nas tabelas (_trocar_no_registro). O RFID e gravado nas MESMAS tabelas da Troca
#     de RFID, na MESMA transacao, com Log e Desfazer (modulo 'linkagem_rfid'; o Desfazer generico devolve o RFID a vazio).
#
#     INCONFORMIDADES (bloqueiam e ficam gravadas em tb_4008_linkagem_inconformes): RFID invalido ou ja em uso; SISBOV fora do estoque
#     da fazenda (ou que ja saiu); SISBOV que ja tem RFID (a mensagem manda usar a Troca de RFID).
#
#     BLOCKCHAIN (decisao do Benedito, 10/11/2026): gera evento, igual a Troca de RFID - reaproveita o tipo TROCA_RFID, com
#     rfid_anterior vazio e rfid_novo preenchido. So animal do rebanho; sem provedor ligado nao faz nada; falha do blockchain nunca
#     derruba a gravacao.
#
#     FORA deste pacote (pacote 2): Consulta dos pares por data, Impressao (PDF Magic) e lista de Inconformidades. Linkagem Enviar/Receber
#     (arquivo do Bastao antigo) ficam fora por decisao do Benedito.
#
#     v1.0.0: Criacao (Sessao 120, 10/11/2026, 18:20 -03). SQL: Tabelas\criar_linkagem_s120.sql (tb_4008 + tb_versao_schema = 9).
#     v1.1.0: Sessao 120 (10/11/2026, 19:10 -03) - Tela como a Leitura da Brincagem com Bastao (pedido do Benedito): ao ler o brinco a tela
#         mostra os dados do animal (nova rota /buscar) para o usuario ter certeza que e o animal certo; LOTE NOVO (opcional, muda o lote do
#         animal como o Alterar Dados dos Animais) e PESO (opcional, vira uma pesagem no historico, data de hoje, origem BRETE_PESO e as mesmas
#         regras do Leitor de Peso: maior que 100 kg e ate 1000 kg); a gravacao passa a ser no botao GRAVAR (ou Enter), nao mais ao completar os 15
#         digitos; lista dos animais ligados ao lado. SO animal do rebanho (tb_2001): brinco ainda em leitura do brete (sem Comunicado) e recusado.
#         Tudo (RFID, lote, pesagem) numa operacao so, com Log e Desfazer; a pesagem entra no Log como INSERT. RFID do estoque de brincos
#         (tb_7017) nao e consultado: nao ha estoque de RFID, o chip e do Produtor. REVERSAO: .bak_antes_s120_peso_lote.
#     v1.2.0: Sessao 120 (10/11/2026, 21:15 -03) - Pacote 2: cada par ligado tambem grava uma linha em tb_4009_linkagem (base da Consulta e do PDF da
#         Linkagem, em linkagem_consulta.py), com INSERT no Log (o Desfazer apaga a linha). SQL: Tabelas\criar_linkagem_s120_b.sql (versao do schema = 10).
#         REVERSAO: .bak_antes_s120_pacote2.
#     REVERSAO: remover este arquivo, o model tb_4008, o template linkagem_rfid.html, o registro em app.py, o card do Hub e a linha de permissoes.py.
# =========================================================

import logging
from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import text

from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_4008_linkagem_inconformes import LinkagemInconforme
from backend.models.tb_4009_linkagem import Linkagem
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_3008_brincos_saida import BrincoSaida
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_5001_brincagem import Brincagem
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.troca_rfid import (
    _propriedade_do_usuario, _buscar_propriedade_produtor, _numero,
    _localizar_animal, _ficha_animal, _erro_rfid_novo, _trocar_no_registro, SO_DIGITOS, TAMANHO,
    TRAVA_RFID_PRODUTOR,   # v1.3.0 (Etapa 7c) - mesma trava da Troca de RFID
)
from backend.routers.alterar_dados_animais import _atualizar_registro   # lote: mesmo UPDATE com Log do Alterar Dados dos Animais
from backend.routers.pesos_leitor import ORIGEM_PESO, GMD_AVISO, QUEDA_AVISO_PCT
from backend.utils.conferencia_compra import ler_peso_brete, ler_lote_brete
from backend.utils.pesagem import registrar_pesagem
from backend.utils.animal_saiu import mensagem_animal_saiu
from backend.utils.blockchain import registrar_evento, ficha_do_animal, ficha_do_dono, TIPO_TROCA_RFID
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.multitenant import get_db_produtor


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
linkagem_rfid = Blueprint('linkagem_rfid', __name__)


@linkagem_rfid.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


NOME_MODULO_LOG = 'linkagem_rfid'
logger = logging.getLogger(__name__)   # v1.3.0
URL_HUB_ENTRADA = '/produtor/hub-novo/entrada'
URL_INICIAR = '/produtor/linkagem-rfid/iniciar'

MENSAGEM_SISBOV_FORA_DO_ESTOQUE = 'Este SISBOV não está no estoque desta fazenda.'
MENSAGEM_SISBOV_JA_TEM_RFID = 'Este SISBOV já tem RFID ({rfid}). Para trocar o RFID, use a Troca de RFID.'
MENSAGEM_SISBOV_SEM_COMUNICADO = 'Este brinco ainda está na leitura do brete, sem Comunicado: não está no estoque da fazenda.'


# -------------------------------------------------------
# Funcoes auxiliares
# -------------------------------------------------------
def _negado():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect(URL_INICIAR)
    return redirecionar_home()


def _url_voltar():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return URL_INICIAR
    return URL_HUB_ENTRADA


def _contexto_tela():
    return {
        'usuario_nome':   session.get('usuario_nome'),
        'usuario_perfil': session.get('usuario_perfil'),
        'cor_primaria':   session.get('cor_primaria', '#D4370A'),
        'nome_sistema':   session.get('nome_sistema', 'Orion SISBOV'),
        'menu_ativo':     'entrada',
    }


# -------------------------------------------------------
# Grava a tentativa recusada (tb_4008). Nunca derruba a resposta: se nao der para gravar, segue.
# Commit proprio (solta tambem o bloqueio da linha, se houver).
# -------------------------------------------------------
def _registrar_inconforme(db, id_propriedade, rfid, sisbov, motivo):
    try:
        db.rollback()
        db.add(LinkagemInconforme(
            id_propriedade=id_propriedade,
            id_usuario=session.get('usuario_id'),
            rfid=(rfid or '')[:40] or None,
            sisbov=(sisbov or '')[:40] or None,
            motivo=(motivo or '')[:200],
        ))
        db.commit()
    except Exception:
        db.rollback()


# -------------------------------------------------------
# Rota: GET /produtor/linkagem-rfid/iniciar - ponto de partida (card do Hub)
# -------------------------------------------------------
@linkagem_rfid.route('/produtor/linkagem-rfid/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/linkagem-rfid/tela?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/linkagem-rfid/tela?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None if pares else 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
        titulo='Linkagem RFID e Brinco — Selecionar Propriedade',
        proximo='/produtor/linkagem-rfid/tela',
        campo_propriedade='id_propriedade',
        voltar=URL_HUB_ENTRADA,
        **_contexto_tela(),
    )


# -------------------------------------------------------
# Rota: GET /produtor/linkagem-rfid/tela?id_propriedade=X
# -------------------------------------------------------
@linkagem_rfid.route('/produtor/linkagem-rfid/tela')
def tela():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()

    nome_propriedade, nome_produtor = _buscar_propriedade_produtor(int(id_propriedade))

    return render_template(
        'produtor/linkagem_rfid.html',
        id_propriedade=id_propriedade,
        propriedade_nome=nome_propriedade,
        produtor_nome=nome_produtor,
        url_voltar=_url_voltar(),
        **_contexto_tela(),
    )


# -------------------------------------------------------
# Rota: POST /produtor/linkagem-rfid/checar-rfid (AJAX)
# Corpo: {id_propriedade, rfid}. Confere o RFID (1o passo, sem gravar).
# -------------------------------------------------------
@linkagem_rfid.route('/produtor/linkagem-rfid/checar-rfid', methods=['POST'])
def checar_rfid():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    rfid = _numero(dados.get('rfid'))

    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário.'}), 403
    id_prop = int(id_propriedade)

    with get_db_produtor(session['id_produtor']) as db:
        erro = _erro_rfid_novo(db, id_prop, '', '', rfid)
        if erro:
            _registrar_inconforme(db, id_prop, rfid, '', erro)
            return jsonify({'erro': erro}), 409

    return jsonify({'sucesso': True})


# -------------------------------------------------------
# Rota: POST /produtor/linkagem-rfid/buscar (AJAX)
# Corpo: {id_propriedade, sisbov}. 2o passo: acha o animal (so do rebanho) e devolve a ficha para o usuario conferir.
# Recusa (e grava a Inconformidade): SISBOV fora do estoque / que ja saiu, em leitura de brete sem Comunicado, ou que ja tem RFID.
# -------------------------------------------------------
@linkagem_rfid.route('/produtor/linkagem-rfid/buscar', methods=['POST'])
def buscar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = _numero(dados.get('sisbov'))
    rfid = _numero(dados.get('rfid'))

    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário.'}), 403
    id_prop = int(id_propriedade)

    with get_db_produtor(session['id_produtor']) as db:
        erro, status = None, 404
        tipo, registro = (None, None)
        if not SO_DIGITOS.match(sisbov):
            erro, status = f'SISBOV inválido: são {TAMANHO} dígitos (somente números).', 400
        else:
            tipo, registro = _localizar_animal(db, id_prop, sisbov)
            if registro is None:
                dono = db.query(Entrada.sisbov).filter(Entrada.rfid == sisbov, Entrada.id_propriedade == id_prop).first()
                if dono is not None and dono[0]:
                    erro = f'Este número é um RFID (do animal SISBOV {dono[0]}), não um SISBOV. Leia o brinco SISBOV.'
                else:
                    erro = mensagem_animal_saiu(db, id_prop, sisbov=sisbov) or MENSAGEM_SISBOV_FORA_DO_ESTOQUE
            elif tipo != 'rebanho':
                erro = MENSAGEM_SISBOV_SEM_COMUNICADO
            elif registro.rfid:
                erro, status = MENSAGEM_SISBOV_JA_TEM_RFID.format(rfid=registro.rfid), 409
        if erro:
            _registrar_inconforme(db, id_prop, rfid, sisbov, erro)
            return jsonify({'erro': erro}), status

        ficha = _ficha_animal(db, id_prop, tipo, registro)
        ultimo = db.query(Peso).filter(Peso.sisbov == sisbov).order_by(Peso.sequencia.desc()).first()
        ficha['peso_anterior'] = float(ultimo.peso) if ultimo is not None else None
        ficha['dias_peso_anterior'] = (date.today() - ultimo.data_pesagem).days if ultimo is not None else None

    return jsonify({'sucesso': True, 'animal': ficha, 'gmd_aviso': GMD_AVISO, 'queda_aviso_pct': QUEDA_AVISO_PCT})


# -------------------------------------------------------
# Rota: POST /produtor/linkagem-rfid/gravar (AJAX)
# Corpo: {id_propriedade, rfid, sisbov, lote?, peso?}. Confere tudo de novo no servidor ANTES de gravar qualquer coisa e, numa
# transacao so: liga o RFID (mesmas tabelas da Troca de RFID), troca o lote (se veio) e grava a pesagem (se veio) + Log + blockchain.
# -------------------------------------------------------
@linkagem_rfid.route('/produtor/linkagem-rfid/gravar', methods=['POST'])
def gravar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = _numero(dados.get('sisbov'))
    rfid = _numero(dados.get('rfid'))
    peso_txt = str(dados.get('peso') or '').strip()
    lote_txt = dados.get('lote')

    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário.'}), 403
    id_prop = int(id_propriedade)

    with get_db_produtor(session['id_produtor']) as db:
        # v1.3.0 - trava ANTES, confere DENTRO (Regra #71): dois bretes nao gravam o mesmo RFID ao mesmo tempo.
        db.execute(text('SELECT pg_advisory_xact_lock(:ns, :id)'), {'ns': TRAVA_RFID_PRODUTOR, 'id': int(session['id_produtor'])})
        if not SO_DIGITOS.match(sisbov):
            erro = f'SISBOV inválido: são {TAMANHO} dígitos (somente números).'
            _registrar_inconforme(db, id_prop, rfid, sisbov, erro)
            return jsonify({'erro': erro}), 400

        tipo, registro = _localizar_animal(db, id_prop, sisbov, travar=True)
        if registro is None:
            dono = db.query(Entrada.sisbov).filter(Entrada.rfid == sisbov, Entrada.id_propriedade == id_prop).first()
            if dono is not None and dono[0]:
                erro = f'Este número é um RFID (do animal SISBOV {dono[0]}), não um SISBOV. Leia o brinco SISBOV.'
            else:
                erro = mensagem_animal_saiu(db, id_prop, sisbov=sisbov) or MENSAGEM_SISBOV_FORA_DO_ESTOQUE
            _registrar_inconforme(db, id_prop, rfid, sisbov, erro)
            return jsonify({'erro': erro}), 404
        if tipo != 'rebanho':
            _registrar_inconforme(db, id_prop, rfid, sisbov, MENSAGEM_SISBOV_SEM_COMUNICADO)
            return jsonify({'erro': MENSAGEM_SISBOV_SEM_COMUNICADO}), 409

        if registro.rfid:
            erro = MENSAGEM_SISBOV_JA_TEM_RFID.format(rfid=registro.rfid)
            _registrar_inconforme(db, id_prop, rfid, sisbov, erro)
            return jsonify({'erro': erro}), 409

        erro = _erro_rfid_novo(db, id_prop, sisbov, '', rfid)
        if erro:
            _registrar_inconforme(db, id_prop, rfid, sisbov, erro)
            return jsonify({'erro': erro}), 409

        # ---- Lote Novo (opcional) e Peso (opcional): conferidos ANTES de gravar qualquer coisa ----
        lote_novo, erro_lote = ler_lote_brete(lote_txt)
        if erro_lote:
            _registrar_inconforme(db, id_prop, rfid, sisbov, f'Lote recusado: {erro_lote}')
            return jsonify({'erro': erro_lote}), 400

        hoje = date.today()
        peso = None
        if peso_txt:
            peso_valor, erro_peso = ler_peso_brete(peso_txt)
            if erro_peso:
                _registrar_inconforme(db, id_prop, rfid, sisbov, f'Peso recusado: {erro_peso}')
                return jsonify({'erro': erro_peso}), 400
            peso = Decimal(str(peso_valor)).quantize(Decimal('0.01'))
            ultimo = db.query(Peso).filter(Peso.sisbov == sisbov).order_by(Peso.sequencia.desc()).first()
            if ultimo is not None and ultimo.data_pesagem >= hoje:
                erro = f'Este animal já tem pesagem em {ultimo.data_pesagem.strftime("%d/%m/%Y")}. Deixe o Peso em branco.'
                _registrar_inconforme(db, id_prop, rfid, sisbov, erro)
                return jsonify({'erro': erro}), 409

        manejo = registro.manejo or ''
        sexo = {'MACHO': 'Macho', 'FEMEA': 'Fêmea'}.get(str(registro.sexo), str(registro.sexo or ''))
        descricao = f'Linkagem RFID e Brinco — SISBOV {sisbov} — RFID {rfid}'[:120]

        try:
            id_operacao = registrar_operacao(
                db,
                id_usuario=session['usuario_id'],
                id_propriedade=id_prop,
                modulo=NOME_MODULO_LOG,
                descricao=descricao,
            )
            ligados = 0

            # tb_2001 (o animal) e tb_2017 (movimentacoes, por id_animal)
            ligados += _trocar_no_registro(db, id_operacao, 'tb_2001', registro, rfid)
            for movimentacao in db.query(Movimentacao).filter(Movimentacao.id_animal == registro.id).all():
                ligados += _trocar_no_registro(db, id_operacao, 'tb_2017_movimentacoes', movimentacao, rfid)

            # tb_7017, tb_3008, tb_4003 e tb_5001: todas as linhas daquele SISBOV nesta fazenda (mesmas tabelas da Troca de RFID)
            for modelo, tabela in (
                (EntradaBrincoRfid, 'tb_7017_entrada_brincos_rfid'),
                (BrincoSaida,       'tb_3008_brincos_saida'),
                (Peso,              'tb_4003_pesos'),
                (Brincagem,         'tb_5001_brincagem'),
            ):
                for linha in db.query(modelo).filter(modelo.id_propriedade == id_prop, modelo.sisbov == sisbov).all():
                    ligados += _trocar_no_registro(db, id_operacao, tabela, linha, rfid)

            # BLOCKCHAIN: evento na fila (sem provedor ligado nao faz nada). Igual a Troca de RFID.
            registrar_evento(
                db, id_prop, TIPO_TROCA_RFID, registro.sisbov,
                ficha_do_animal(db, registro, extras={'rfid_anterior': None, 'rfid_novo': rfid}),
                ficha_dono=ficha_do_dono(db, id_prop),
                id_usuario=session['usuario_id'], id_operacao=id_operacao,
            )

            # Lote Novo: mesmo UPDATE com Log do Alterar Dados dos Animais (tb_2001 e a leitura original tb_5001)
            lote_mudou = False
            if lote_novo is not None and lote_novo != (registro.lote or None):
                lote_mudou = _atualizar_registro(db, id_operacao, 'tb_2001', registro, {'lote': lote_novo})
                for leitura in db.query(Brincagem).filter(Brincagem.id_propriedade == id_prop, Brincagem.sisbov == sisbov).all():
                    _atualizar_registro(db, id_operacao, 'tb_5001_brincagem', leitura, {'lote': lote_novo})

            # Peso: pesagem no historico (sequencia, ganho e evento PESAGEM do blockchain na funcao compartilhada) + INSERT no Log
            pesagem = None
            if peso is not None:
                pesagem = registrar_pesagem(
                    db, id_prop, registro.sisbov, rfid, hoje, peso,
                    ((hoje - registro.nascimento).days if registro.nascimento else None),
                    registro.lote, ORIGEM_PESO, session.get('usuario_id'), id_operacao=id_operacao,
                )
                if pesagem is not None:
                    registrar_item(
                        db, id_operacao, tabela='tb_4003_pesos', id_registro=pesagem.id,
                        tipo_mudanca='INSERT', dados_antes=None,
                        dados_depois={'sisbov': registro.sisbov, 'data_pesagem': hoje.isoformat(), 'peso': str(peso)},
                    )

            # Pacote 2: o par ligado (base da Consulta e do PDF por data); entra no Log como INSERT (o Desfazer apaga a linha)
            par = Linkagem(
                id_propriedade=id_prop, id_usuario=session.get('usuario_id'), sisbov=registro.sisbov, rfid=rfid,
                data_linkagem=hoje, hora_linkagem=datetime.now().time().replace(microsecond=0),
                lote=registro.lote, peso=(peso if pesagem is not None else None),
            )
            db.add(par)
            db.flush()
            registrar_item(
                db, id_operacao, tabela='tb_4009_linkagem', id_registro=par.id,
                tipo_mudanca='INSERT', dados_antes=None,
                dados_depois={'sisbov': registro.sisbov, 'rfid': rfid, 'data_linkagem': hoje.isoformat()},
            )

            lote_final = registro.lote or ''
            peso_fmt = f'{peso:.2f}'.replace('.', ',') if pesagem is not None else ''
            db.commit()
        except Exception:
            db.rollback()
            logger.exception('Linkagem RFID: falha ao gravar (SISBOV %s, Propriedade %s)', sisbov, id_prop)   # v1.3.0 - o motivo fica no log
            return jsonify({'erro': 'Não foi possível gravar. Nada foi alterado.'}), 500

    return jsonify({
        'sucesso': True,
        'mensagem': 'RFID ligado ao brinco.',
        'sisbov': sisbov,
        'rfid': rfid,
        'manejo': manejo,
        'sexo': sexo,
        'lote': lote_final,
        'lote_mudou': bool(lote_mudou),
        'peso': peso_fmt,
        'hora': datetime.now().strftime('%H:%M'),
        'registros': int(ligados),
    })

# =========================================================
# FIM DE ARQUIVO: backend\routers\linkagem_rfid.py
# =========================================================
