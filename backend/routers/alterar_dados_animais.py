# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\alterar_dados_animais.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-05 20:35 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.5.0
# v1.5.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (3 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Tela "Alterar Dados dos Animais" (Sessao 087, pedido de Benedito):
#     corrigir Lote, Peso, Sexo e Raca dos animais do brete SEM precisar
#     abrir um por um. Caso real: no modo automatico do Leitor/Bastao os
#     valores se repetem de um animal para o outro - o peao errou varios
#     lotes, e um peso digitado 81 em vez de 381.
#
#     ORIGENS (de onde vem a lista de animais):
#       - leituras: animais lidos no brete e ainda NAO vinculados a uma GTA
#         (tb_5001 sts=False, sem GTA e sem Comunicado), por Data Brincagem.
#         A Consulta Brincagem -> Alterar ja corrige um por um; aqui e em
#         lote. Corrigir aqui, antes do Vincular GTA, faz o Vincular levar
#         os valores certos.
#       - compra: animais de uma GTA de COMPRA ja em tb_2001 (conferidos no
#         brete apos a Brincagem Sequencial, ou vinculados pelo Vincular GTA).
#         Trava POR ANIMAL: Comunicado de Entrada gerado (numero_comunicado).
#       - nas: animais de uma Notificacao de Nascimento (NAS) em tb_2001.
#         Trava: Notificacao ja IMPRESSA (tb_7020).
#
#     O QUE SE CORRIGE (decisoes de Benedito, 05/10/2026):
#       - Lote (obrigatorio, ate 30 caracteres) - em varios de uma vez (marca
#         os animais e aplica) ou um por um;
#       - Peso (superior a 100 kg e no maximo 1.000) - corrige a pesagem DO
#         BRETE na tb_4003 (origem BRETE_COMPRA / BRETE_NASCIMENTO) e
#         recalcula o ganho dela e o da pesagem seguinte. A media do Peso
#         Balancao (BALANCAO_COMPRA) NAO e tocada aqui;
#       - Sexo e Raca - o animal ja gravado tem sexo/raca copiados em 5
#         lugares, e TODOS sao corrigidos na mesma transacao: tb_2001, tb_2017
#         (movimentacao), tb_7002_pia (sexo e codigo da raca), tb_7017 (o
#         brinco no estoque) e a leitura original da tb_5001, se existir.
#     Trocar o SEXO de animal de GTA muda a composicao real em relacao ao que
#     a GTA declarou (ex.: 8 machos viram 7 + 1 femea): a tela AVISA antes
#     de gravar e a composicao vai no Log; a GTA NAO e alterada.
#
#     Tudo vai para o Log de Operacoes (backend/utils/log_operacoes.py): so os
#     campos que de fato mudaram entram em dados_antes/dados_depois, uma
#     linha de Log por registro alterado, todas na MESMA operacao e na MESMA
#     transacao (ou grava tudo ou nada).
#
#     Cartao nos DOIS Hubs (hubs.py v1.42.0): 'brincagem' (campo, logo apos
#     Consulta Brincagem) e 'entrada' (escritorio, antes de Vincular GTA).
#
#     v1.0.0: Criacao (Sessao 087, 05/10/2026, 20:35 -03).
#     v1.0.1: Sessao 087 (2026-10-05 20:51 -03) - DESFAZER (conferido com o log_operacoes.py v1.7.0):
#             o Desfazer compara o valor ATUAL do banco com dados_depois COMO TEXTO
#             (verificar_conflitos). O Log gravava o peso como "350" e o Numeric do
#             banco devolve "350.00" - falso conflito, o Desfazer das alteracoes de
#             peso ficaria sempre bloqueado. Agora _atualizar_registro() relê o
#             registro depois do flush e grava em dados_depois o valor COMO O BANCO
#             o devolve. A descricao da operacao tambem ficou curta (ate 120
#             caracteres - a coluna nunca foi vista). Nenhuma outra mudanca.
#     v1.1.0: Sessao 090 (08/10/2026, 08:35 -03) - FAZENDA EM USO (Lote 4):
#             FAZENDA EM USO (Regra de Ouro #13): a tela "Selecionar Propriedade" deixa
#             de aparecer quando ha fazenda em uso (auth.resolver_fazenda_em_uso).
#               - iniciar(): com fazenda em uso, abre "O que alterar" direto.
#               - VOLTAR (Regra #9): vai para os Hubs NOVOS (entrada ou
#                 brincagem, conforme a origem); so volta para a selecao quem
#                 tem 2+ pares e nenhuma fazenda em uso.
#               - TRAVA em _propriedade_do_usuario(): Propriedade diferente da
#                 fazenda em uso (outra aba) = negado. As telas mandam para o
#                 iniciar() (_negado); o Salvar (AJAX) responde 403 e nao grava.
#             Nenhuma outra mudanca. Gravacao, Log e regras intactos.
#     v1.2.0: Sessao 094 (12/10/2026, 20:30 -03) - AUDITORIA DE COMPRAS: O nome do Produtor da tela vem do vinculo do Produtor LOGADO (antes, .first() da
#             Propriedade: com 2+ Produtores na fazenda aparecia o nome errado).
#             REVERSAO: devolver .bak_antes_auditoria_compras.
#     v1.3.0: Sessao 094 (12/10/2026, 20:45 -03) - AUDITORIA DE CONSULTAS/CORRECOES: _linhas_editaveis() trava as linhas (FOR UPDATE): Comunicado ou Vincular GTA no meio nao deixam
#             corrigir animal recem-travado. REVERSAO: devolver .bak_antes_auditoria_consulta.
#     v1.4.0: Sessao 106 (26/10/2026, 16:20 -03) - PONTA SOLTA (auditoria): leitura RESERVADA a GTA no brete (tb_5001.id_gta_reservada) sai das 3
#             consultas (contagem por data, linhas da data, linhas travadas do Salvar) - nao se corrige animal no meio da leitura da GTA. REVERSAO: .bak_antes_s106s.
# =========================================================

from datetime import datetime
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, PropriedadeProdutor, Produtor
from backend.models.tb_5001_brincagem import Brincagem
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4001_gta_animais import GtaAnimal
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_7002_pia import Pia
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.models.tb_7020_notificacao_impressao import NotificacaoImpressao
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.conferencia_compra import ler_peso_brete, ler_lote_brete


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
alterar_dados_animais = Blueprint('alterar_dados_animais', __name__)


# -------------------------------------------------------
# Mesma protecao de cache dos modulos irmaos (Sessao 064): a lista e o
# catalogo de Racas mudam de Produtor para Produtor.
# -------------------------------------------------------
@alterar_dados_animais.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


NOME_MODULO_LOG = 'alterar_dados_animais'
SESSAO_ORIGEM   = 'alterar_dados_animais_origem'

SEXOS_VALIDOS = ('MACHO', 'FEMEA')

TIPO_BANCO_COMPRA     = 'COMPRA'
TIPO_BANCO_NASCIMENTO = 'NASCTO-DESMAME'
SERIE_NOTIFICACAO     = 'NAS'

ORIGENS_PESAGEM_BRETE = ('BRETE_COMPRA', 'BRETE_NASCIMENTO')
ORIGENS_DADOS         = ('leituras', 'compra', 'nas')
DESCRICAO_TIPO        = {'COMPRA': 'Compra', 'NASCIMENTO': 'Nascimento / Desmame', TIPO_BANCO_NASCIMENTO: 'Nascimento / Desmame'}

LIMITE_ANIMAIS_POR_SALVAR = 500


# -------------------------------------------------------
# Funcoes auxiliares
# -------------------------------------------------------
def _propriedade_do_usuario(id_propriedade):
    # Trava de seguranca (mesma da Consulta Brincagem v2.11.1): a Propriedade
    # tem de ser de um par do usuario logado E do Produtor da sessao.
    try:
        id_int = int(id_propriedade)
    except (TypeError, ValueError):
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    # v1.1.0 - TRAVA DA FAZENDA EM USO: Propriedade diferente da fazenda em
    # uso (trocada em outra aba) = negado.
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and par_em_uso.id_propriedade != id_int:
        return False
    return any(
        par.id_propriedade == id_int and par.id_produtor == session.get('id_produtor')
        for par in pares
    )


# -------------------------------------------------------
# Negado (v1.1.0): com fazenda em uso, a Propriedade errada manda para o
# iniciar() (que abre a fazenda em uso); sem fazenda em uso, Home como antes.
# -------------------------------------------------------
def _negado():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect(f'/produtor/alterar-dados-animais/iniciar?origem={_origem_hub()}')
    return redirecionar_home()


def _origem_hub():
    origem = session.get(SESSAO_ORIGEM, 'brincagem')
    return origem if origem in ('entrada', 'brincagem') else 'brincagem'


def _voltar_hub(origem):
    # v1.1.0 - Hubs novos (agrupados).
    return '/produtor/hub-novo/entrada' if origem == 'entrada' else '/produtor/hub-novo/brincagem'


def _url_voltar_origem(origem):
    # Caminho real percorrido (Regra de Ouro #4): com 2+ pares passou pela
    # Selecao de Propriedade; com 1 so, o Voltar vai direto para o Hub.
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    # v1.1.0 - com fazenda em uso a selecao e pulada: volta direto ao Hub.
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return f'/produtor/alterar-dados-animais/iniciar?origem={origem}'
    return _voltar_hub(origem)


def _data_br(data):
    return data.strftime('%d/%m/%Y') if data else ''


def _parse_data_br(texto):
    try:
        return datetime.strptime((texto or '').strip(), '%d/%m/%Y').date()
    except ValueError:
        return None


def _buscar_propriedade_produtor(id_propriedade):
    with Session(engine) as db:
        propriedade = db.get(Propriedade, id_propriedade)
        produtor = None
        if propriedade:
            vinculo = db.query(PropriedadeProdutor).filter_by(
                id_propriedade=propriedade.id, id_produtor=session['id_produtor'], data_fim=None   # Sessao 094
            ).first()
            if vinculo:
                produtor = db.get(Produtor, vinculo.id_produtor)
        nome_propriedade = propriedade.nome if propriedade else '-'
        nome_produtor = produtor.nome if produtor else '-'
    return nome_propriedade, nome_produtor


def _txt(valor):
    # Texto comparavel para o Log: numero sem zeros a toa (310 == 310.00).
    if valor is None:
        return None
    if isinstance(valor, (Decimal, float, int)) and not isinstance(valor, bool):
        return format(Decimal(str(valor)).normalize(), 'f')
    return str(valor)


def _texto_do_banco(valor):
    # v1.0.1 - texto do valor lido do banco (None continua None).
    return None if valor is None else str(valor)


def _contexto_tela(origem):
    return {
        'usuario_nome':   session.get('usuario_nome'),
        'usuario_perfil': session.get('usuario_perfil'),
        'cor_primaria':   session.get('cor_primaria', '#D4370A'),
        'nome_sistema':   session.get('nome_sistema', 'Orion SISBOV'),
        'menu_ativo':     'brincagem' if origem == 'brincagem' else 'entrada',
    }


# -------------------------------------------------------
# Rota: GET /produtor/alterar-dados-animais/iniciar - ponto de partida
# (card dos Hubs). Guarda 'origem' na sessao e resolve Propriedade/
# Produtor (Padrao Reutilizavel N.1). Com 1 unico par, pula a selecao.
# -------------------------------------------------------
@alterar_dados_animais.route('/produtor/alterar-dados-animais/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    origem = request.args.get('origem', 'brincagem')
    if origem not in ('entrada', 'brincagem'):
        origem = 'brincagem'
    session[SESSAO_ORIGEM] = origem
    voltar = _voltar_hub(origem)

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    # v1.1.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/alterar-dados-animais/origem?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/alterar-dados-animais/origem?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None if pares else 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
        titulo='Alterar Dados dos Animais — Selecionar Propriedade',
        proximo='/produtor/alterar-dados-animais/origem',
        campo_propriedade='id_propriedade',
        voltar=voltar,
        **_contexto_tela(origem),
    )


# -------------------------------------------------------
# Funcoes auxiliares da tela "O que alterar" - o que existe para corrigir.
# -------------------------------------------------------
def _listar_leituras_pendentes(db, id_propriedade):
    linhas = (
        db.query(Brincagem.data_brincagem, func.count(Brincagem.id))
        .filter(
            Brincagem.id_propriedade == id_propriedade,
            Brincagem.sts == False,   # noqa: E712
            Brincagem.id_gta.is_(None),
            Brincagem.id_gta_reservada.is_(None),   # v1.4.0
            Brincagem.numero_comunicado.is_(None),
            Brincagem.data_brincagem.isnot(None),
        )
        .group_by(Brincagem.data_brincagem)
        .order_by(Brincagem.data_brincagem.desc())
        .all()
    )
    return [{'data': _data_br(data), 'qtde': qtde} for data, qtde in linhas]


def _listar_gtas(db, id_propriedade, tipo_banco):
    agregados = (
        db.query(
            Entrada.id_gta_entrada,
            func.count(Entrada.id),
            func.sum(case((Entrada.numero_comunicado.is_(None), 1), else_=0)),
            func.sum(case((Entrada.conferido_brete.is_(True), 1), else_=0)),
        )
        .filter(
            Entrada.id_propriedade == id_propriedade,
            Entrada.tipo_entrada == tipo_banco,
            Entrada.id_gta_entrada.isnot(None),
        )
        .group_by(Entrada.id_gta_entrada)
        .all()
    )
    ids = [linha[0] for linha in agregados]
    if not ids:
        return []

    gtas = {g.id: g for g in db.query(Gta).filter(Gta.id.in_(ids)).all()}
    impressas = {
        linha[0] for linha in
        db.query(NotificacaoImpressao.id_gta).filter(NotificacaoImpressao.id_gta.in_(ids)).all()
    }

    itens = []
    for id_gta, total, livres, conferidos in agregados:
        gta = gtas.get(id_gta)
        if gta is None:
            continue
        if tipo_banco == TIPO_BANCO_NASCIMENTO:
            if gta.serie_gta != SERIE_NOTIFICACAO or id_gta in impressas:
                continue   # so NAS ainda NAO impressa
        elif not livres:
            continue       # Comunicado ja gerado para todos os animais
        itens.append({
            'id': id_gta,
            'numero': gta.numero_gta_completo,
            'data': _data_br(gta.data_emissao),
            'ordem': (gta.data_emissao or datetime.min.date(), id_gta),
            'total': total,
            'conferidos': int(conferidos or 0),
            'livres': int(livres or 0),
        })
    itens.sort(key=lambda item: item['ordem'], reverse=True)
    return itens


# -------------------------------------------------------
# Rota: GET /produtor/alterar-dados-animais/origem?id_propriedade=X
# Tela "O que alterar": leituras pendentes por Data, GTAs de Compra e
# Notificacoes NAS que ainda aceitam correcao.
# -------------------------------------------------------
@alterar_dados_animais.route('/produtor/alterar-dados-animais/origem')
def escolher_origem():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_prop = int(id_propriedade)
    origem = _origem_hub()

    nome_propriedade, nome_produtor = _buscar_propriedade_produtor(id_prop)

    with get_db_produtor(session['id_produtor']) as db:
        leituras    = _listar_leituras_pendentes(db, id_prop)
        gtas_compra = _listar_gtas(db, id_prop, TIPO_BANCO_COMPRA)
        gtas_nas    = _listar_gtas(db, id_prop, TIPO_BANCO_NASCIMENTO)

    return render_template(
        'produtor/alterar_dados_animais_origem.html',
        id_propriedade=id_propriedade,
        propriedade_nome=nome_propriedade,
        produtor_nome=nome_produtor,
        leituras=leituras,
        gtas_compra=gtas_compra,
        gtas_nas=gtas_nas,
        url_voltar=_url_voltar_origem(origem),
        **_contexto_tela(origem),
    )


# -------------------------------------------------------
# Carrega a lista de animais de uma origem. Devolve dict com titulo,
# animais (dicts simples, montados ANTES de qualquer commit), declarado
# (composicao que a GTA declarou, ou None) e bloqueio_geral (texto, ou
# None). Devolve None se a origem/valor nao existir.
# -------------------------------------------------------
def _carregar_escopo(db, id_propriedade, origem_dados, valor):
    if origem_dados == 'leituras':
        data = _parse_data_br(valor)
        if not data:
            return None
        linhas = (
            db.query(Brincagem)
            .filter(
                Brincagem.id_propriedade == id_propriedade,
                Brincagem.data_brincagem == data,
                Brincagem.sts == False,   # noqa: E712
                Brincagem.id_gta.is_(None),
                Brincagem.id_gta_reservada.is_(None),   # v1.4.0
                Brincagem.numero_comunicado.is_(None),
            )
            .order_by(Brincagem.sexo.asc(), Brincagem.sisbov.asc())
            .all()
        )
        if not linhas:
            return None
        animais = [{
            'id': linha.id, 'sisbov': linha.sisbov, 'sexo': linha.sexo, 'id_raca': linha.id_raca,
            'peso': float(linha.peso) if linha.peso is not None else None,
            'lote': linha.lote or '',
            'situacao': 'Lido no brete — ' + DESCRICAO_TIPO.get(linha.tipo_entrada, linha.tipo_entrada or ''),
            'bloqueado': False, 'motivo': '', 'peso_editavel': True,
        } for linha in linhas]
        return {
            'titulo': f'Leituras do brete — {valor}',
            'subtitulo': 'Animais lidos no brete e ainda NÃO vinculados a uma GTA. Corrija antes do Vincular GTA.',
            'animais': animais, 'declarado': None, 'bloqueio_geral': None,
        }

    if not str(valor).isdecimal():
        return None
    gta = db.get(Gta, int(valor))
    tipo_banco = TIPO_BANCO_COMPRA if origem_dados == 'compra' else TIPO_BANCO_NASCIMENTO
    if not gta or gta.id_propriedade != id_propriedade or gta.tipo_movimento != (
        'COMPRA' if origem_dados == 'compra' else TIPO_BANCO_NASCIMENTO
    ):
        return None

    bloqueio_geral = None
    if origem_dados == 'nas':
        if gta.serie_gta != SERIE_NOTIFICACAO:
            return None
        if db.query(NotificacaoImpressao.id).filter_by(id_gta=gta.id).first() is not None:
            bloqueio_geral = 'A Notificação desta NAS já foi impressa — os dados não podem mais ser alterados.'

    linhas = (
        db.query(Entrada)
        .filter(
            Entrada.id_gta_entrada == gta.id,
            Entrada.id_propriedade == id_propriedade,
            Entrada.tipo_entrada == tipo_banco,
        )
        .order_by(Entrada.sexo.asc(), Entrada.sisbov.asc())
        .all()
    )
    if not linhas:
        return None

    sisbovs = [linha.sisbov for linha in linhas]
    pesagens_brete = {}
    for pesagem in (
        db.query(Peso)
        .filter(Peso.id_propriedade == id_propriedade, Peso.sisbov.in_(sisbovs), Peso.origem.in_(ORIGENS_PESAGEM_BRETE))
        .order_by(Peso.sequencia.asc())
        .all()
    ):
        pesagens_brete[pesagem.sisbov] = pesagem   # fica a ULTIMA pesagem do brete

    animais = []
    for linha in linhas:
        pesagem = pesagens_brete.get(linha.sisbov)
        bloqueado, motivo = False, ''
        if bloqueio_geral:
            bloqueado, motivo = True, 'Notificação impressa'
        elif origem_dados == 'compra' and linha.numero_comunicado is not None:
            bloqueado, motivo = True, f'Comunicado {linha.numero_comunicado}'
        animais.append({
            'id': linha.id, 'sisbov': linha.sisbov, 'sexo': linha.sexo, 'id_raca': linha.id_raca,
            'peso': float(pesagem.peso) if pesagem is not None else None,
            'lote': linha.lote or '',
            'situacao': 'Conferido no brete' if linha.conferido_brete else 'A conferir no brete',
            'bloqueado': bloqueado, 'motivo': motivo, 'peso_editavel': pesagem is not None,
        })

    declarado = None
    categorias = db.query(GtaAnimal).filter(GtaAnimal.id_gta == gta.id).all() if origem_dados == 'compra' else []
    if categorias:
        declarado = {'MACHO': 0, 'FEMEA': 0}
        for categoria in categorias:
            if categoria.sexo in declarado:
                declarado[categoria.sexo] += categoria.quantidade

    rotulo = 'GTA' if origem_dados == 'compra' else 'Notificação'
    return {
        'titulo': f'{rotulo} {gta.numero_gta_completo}',
        'subtitulo': (
            'Animais da GTA de Compra. Cada animal trava quando o Comunicado de Entrada é gerado.'
            if origem_dados == 'compra' else
            'Animais da Notificação de Nascimento. Trava quando a Notificação é impressa.'
        ),
        'animais': animais, 'declarado': declarado, 'bloqueio_geral': bloqueio_geral,
    }


# -------------------------------------------------------
# Rota: GET /produtor/alterar-dados-animais/lista?id_propriedade=X&
# origem_dados=leituras|compra|nas&valor=<data dd/mm/aaaa | id da GTA>
# -------------------------------------------------------
@alterar_dados_animais.route('/produtor/alterar-dados-animais/lista')
def lista():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    origem_dados   = (request.args.get('origem_dados') or '').strip().lower()
    valor          = (request.args.get('valor') or '').strip()
    if not _propriedade_do_usuario(id_propriedade) or origem_dados not in ORIGENS_DADOS:
        return _negado()
    id_prop = int(id_propriedade)
    origem = _origem_hub()

    nome_propriedade, nome_produtor = _buscar_propriedade_produtor(id_prop)

    with get_db_produtor(session['id_produtor']) as db:
        escopo = _carregar_escopo(db, id_prop, origem_dados, valor)
        if escopo is None:
            return redirect(f'/produtor/alterar-dados-animais/origem?id_propriedade={id_propriedade}')
        racas = [
            {'id': raca.id, 'nome': raca.nome}
            for raca in db.query(Raca).filter_by(ativo=True, comum=True).order_by(Raca.nome.asc()).all()
        ]

    ok = request.args.get('ok', '')
    return render_template(
        'produtor/alterar_dados_animais_lista.html',
        id_propriedade=id_propriedade,
        origem_dados=origem_dados,
        valor=valor,
        propriedade_nome=nome_propriedade,
        produtor_nome=nome_produtor,
        titulo_origem=escopo['titulo'],
        subtitulo=escopo['subtitulo'],
        animais=escopo['animais'],
        declarado=escopo['declarado'],
        bloqueio_geral=escopo['bloqueio_geral'],
        racas=racas,
        ok=int(ok) if ok.isdecimal() else None,
        url_voltar=f'/produtor/alterar-dados-animais/origem?id_propriedade={id_propriedade}',
        **_contexto_tela(origem),
    )


# -------------------------------------------------------
# Atualiza um registro e grava no Log SO o que mudou (antes/depois).
# Devolve True se algo mudou.
# -------------------------------------------------------
def _atualizar_registro(db, id_operacao, tabela, registro, novos):
    antes, mudaram = {}, []
    for campo, novo in novos.items():
        atual = getattr(registro, campo)
        if _txt(atual) != _txt(novo):
            antes[campo] = _txt(atual)
            mudaram.append(campo)
            setattr(registro, campo, novo)
    if not antes:
        return False
    # v1.0.1 - dados_depois = o valor COMO O BANCO guardou (350 vira 350.00): o Desfazer compara
    # o valor atual com dados_depois como texto (log_operacoes.verificar_conflitos).
    db.flush()
    db.refresh(registro)
    depois = {campo: _texto_do_banco(getattr(registro, campo)) for campo in mudaram}
    registrar_item(
        db, id_operacao=id_operacao, tabela=tabela, id_registro=registro.id,
        tipo_mudanca='UPDATE', dados_antes=antes, dados_depois=depois,
    )
    return True


def _aplicar_leitura(db, id_operacao, linha, campos):
    novos = {}
    if 'peso' in campos:
        novos['peso'] = campos['peso']
    if 'lote' in campos:
        novos['lote'] = campos['lote']
    if 'sexo' in campos:
        novos['sexo'] = campos['sexo']
    if 'id_raca' in campos:
        novos['id_raca'] = campos['id_raca']
    return _atualizar_registro(db, id_operacao, 'tb_5001_brincagem', linha, novos)


def _aplicar_animal(db, id_operacao, id_propriedade, linha, campos, pesagens_brete, racas_validas):
    mudou = False
    sisbov = linha.sisbov

    # ---- tb_2001 (o animal): lote, sexo, raca ----
    novos_2001 = {}
    for campo in ('lote', 'sexo', 'id_raca'):
        if campo in campos:
            novos_2001[campo] = campos[campo]
    mudou |= _atualizar_registro(db, id_operacao, 'tb_2001', linha, novos_2001)

    # ---- tb_4003_pesos (pesagem do BRETE): peso, ganho, lote ----
    pesagem = pesagens_brete.get(sisbov)
    if pesagem is not None and ('peso' in campos or 'lote' in campos):
        novos_pesagem = {}
        if 'lote' in campos:
            novos_pesagem['lote'] = campos['lote']
        if 'peso' in campos:
            novo_peso = Decimal(str(campos['peso']))
            anterior = (
                db.query(Peso)
                .filter(Peso.id_propriedade == id_propriedade, Peso.sisbov == sisbov, Peso.sequencia == pesagem.sequencia - 1)
                .first()
            )
            novos_pesagem['peso'] = novo_peso
            novos_pesagem['ganho_peso'] = (novo_peso - Decimal(str(anterior.peso))) if anterior is not None else None
            seguinte = (
                db.query(Peso)
                .filter(Peso.id_propriedade == id_propriedade, Peso.sisbov == sisbov, Peso.sequencia == pesagem.sequencia + 1)
                .first()
            )
            if seguinte is not None:
                mudou |= _atualizar_registro(db, id_operacao, 'tb_4003_pesos', seguinte,
                                             {'ganho_peso': Decimal(str(seguinte.peso)) - novo_peso})
        mudou |= _atualizar_registro(db, id_operacao, 'tb_4003_pesos', pesagem, novos_pesagem)

    # ---- sexo e raca: copiados em tb_2017, tb_7002_pia, tb_7017 e na leitura original (tb_5001) ----
    if 'sexo' in campos or 'id_raca' in campos:
        codigo_raca = racas_validas.get(campos['id_raca']) if 'id_raca' in campos else None

        novos = {}
        if 'sexo' in campos:
            novos['sexo'] = campos['sexo']
        if 'id_raca' in campos:
            novos['id_raca'] = campos['id_raca']
        for movimentacao in db.query(Movimentacao).filter(Movimentacao.id_animal == linha.id).all():
            mudou |= _atualizar_registro(db, id_operacao, 'tb_2017_movimentacoes', movimentacao, dict(novos))

        novos_pia = {}
        if 'sexo' in campos:
            novos_pia['sexo'] = campos['sexo']
        if 'id_raca' in campos:
            novos_pia['raca_codigo'] = codigo_raca
        for pia in db.query(Pia).filter(Pia.id_propriedade == id_propriedade, Pia.sisbov == sisbov).all():
            mudou |= _atualizar_registro(db, id_operacao, 'tb_7002_pia', pia, dict(novos_pia))

        novos_estoque = {}
        if 'sexo' in campos:
            novos_estoque['sexo'] = campos['sexo']
        if 'id_raca' in campos:
            novos_estoque['raca'] = codigo_raca
        for brinco in db.query(EntradaBrincoRfid).filter(
            EntradaBrincoRfid.id_propriedade == id_propriedade, EntradaBrincoRfid.sisbov == sisbov
        ).all():
            mudou |= _atualizar_registro(db, id_operacao, 'tb_7017_entrada_brincos_rfid', brinco, dict(novos_estoque))

    # ---- a leitura original (tb_5001, se o animal veio do Leitor/Bastao): mantem a Consulta Brincagem igual ----
    novos_leitura = {campo: campos[campo] for campo in ('peso', 'lote', 'sexo', 'id_raca') if campo in campos}
    if novos_leitura:
        for leitura in db.query(Brincagem).filter(Brincagem.id_propriedade == id_propriedade, Brincagem.sisbov == sisbov).all():
            mudou |= _atualizar_registro(db, id_operacao, 'tb_5001_brincagem', leitura, dict(novos_leitura))
    return mudou


# -------------------------------------------------------
# Linhas que a tela pode alterar AGORA (travas aplicadas). Devolve
# (linhas {id: registro}, gta, erro_geral).
# -------------------------------------------------------
def _linhas_editaveis(db, id_propriedade, origem_dados, valor, ids):
    if origem_dados == 'leituras':
        data = _parse_data_br(valor)
        if not data:
            return {}, None, 'Data de Brincagem inválida.'
        linhas = (
            db.query(Brincagem)
            .filter(
                Brincagem.id.in_(ids),
                Brincagem.id_propriedade == id_propriedade,
                Brincagem.data_brincagem == data,
                Brincagem.sts == False,   # noqa: E712
                Brincagem.id_gta.is_(None),
                Brincagem.id_gta_reservada.is_(None),   # v1.4.0
                Brincagem.numero_comunicado.is_(None),
            )
            .with_for_update()   # v1.3.0
            .all()
        )
        return {linha.id: linha for linha in linhas}, None, None

    if not str(valor).isdecimal():
        return {}, None, 'GTA inválida.'
    gta = db.get(Gta, int(valor))
    tipo_banco = TIPO_BANCO_COMPRA if origem_dados == 'compra' else TIPO_BANCO_NASCIMENTO
    tipo_gta = 'COMPRA' if origem_dados == 'compra' else TIPO_BANCO_NASCIMENTO
    if not gta or gta.id_propriedade != id_propriedade or gta.tipo_movimento != tipo_gta:
        return {}, None, 'GTA não encontrada nesta Propriedade.'
    if origem_dados == 'nas':
        if gta.serie_gta != SERIE_NOTIFICACAO:
            return {}, None, 'Notificação não encontrada.'
        if db.query(NotificacaoImpressao.id).filter_by(id_gta=gta.id).first() is not None:
            return {}, gta, 'A Notificação desta NAS já foi impressa — os dados não podem mais ser alterados.'

    linhas = (
        db.query(Entrada)
        .filter(
            Entrada.id.in_(ids),
            Entrada.id_gta_entrada == gta.id,
            Entrada.id_propriedade == id_propriedade,
            Entrada.tipo_entrada == tipo_banco,
        )
        .with_for_update()   # v1.3.0
        .all()
    )
    if origem_dados == 'compra':
        linhas = [linha for linha in linhas if linha.numero_comunicado is None]
    return {linha.id: linha for linha in linhas}, gta, None


# -------------------------------------------------------
# Rota: POST /produtor/alterar-dados-animais/salvar (AJAX)
# Corpo: {id_propriedade, origem_dados, valor, alteracoes: [{id, peso?,
# lote?, sexo?, id_raca?}]} - so os campos que MUDARAM. Valida tudo ANTES
# de gravar (um erro = nada e gravado) e grava na mesma transacao + Log.
# -------------------------------------------------------
@alterar_dados_animais.route('/produtor/alterar-dados-animais/salvar', methods=['POST'])
def salvar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    origem_dados   = (dados.get('origem_dados') or '').strip().lower()
    valor          = str(dados.get('valor') or '').strip()
    alteracoes     = dados.get('alteracoes')

    if origem_dados not in ORIGENS_DADOS or not isinstance(alteracoes, list) or not alteracoes:
        return jsonify({'erro': 'Nada para alterar.'}), 400
    if len(alteracoes) > LIMITE_ANIMAIS_POR_SALVAR:
        return jsonify({'erro': f'Altere no máximo {LIMITE_ANIMAIS_POR_SALVAR} animais por vez.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário.'}), 403
    id_prop = int(id_propriedade)

    ids = []
    for alteracao in alteracoes:
        try:
            ids.append(int(alteracao.get('id')))
        except (TypeError, ValueError, AttributeError):
            return jsonify({'erro': 'Registro inválido na lista de alterações.'}), 400

    with get_db_produtor(session['id_produtor']) as db:
        linhas, gta, erro_geral = _linhas_editaveis(db, id_prop, origem_dados, valor, ids)
        if erro_geral:
            return jsonify({'erro': erro_geral}), 409

        racas_validas = {
            raca.id: raca.codigo
            for raca in db.query(Raca).filter_by(ativo=True, comum=True).all()
        }

        pesagens_brete = {}
        if origem_dados != 'leituras':
            for pesagem in (
                db.query(Peso)
                .filter(
                    Peso.id_propriedade == id_prop,
                    Peso.sisbov.in_([linha.sisbov for linha in linhas.values()]),
                    Peso.origem.in_(ORIGENS_PESAGEM_BRETE),
                )
                .order_by(Peso.sequencia.asc())
                .all()
            ):
                pesagens_brete[pesagem.sisbov] = pesagem

        # ---------------- validacao (nada e gravado se houver erro) ----------------
        erros, mudancas = [], []
        for alteracao, id_linha in zip(alteracoes, ids):
            linha = linhas.get(id_linha)
            if linha is None:
                erros.append(f'Registro {id_linha}: não encontrado, ou já travado (Comunicado / Notificação / Vincular GTA).')
                continue
            rotulo = f'SISBOV {linha.sisbov}'
            campos = {}

            if 'peso' in alteracao:
                if origem_dados != 'leituras' and linha.sisbov not in pesagens_brete:
                    erros.append(f'{rotulo}: não há pesagem do brete para corrigir.')
                else:
                    peso, erro = ler_peso_brete(alteracao.get('peso'))
                    if erro:
                        erros.append(f'{rotulo}: {erro}')
                    else:
                        campos['peso'] = peso
            if 'lote' in alteracao:
                lote, erro = ler_lote_brete(alteracao.get('lote'), obrigatorio=True)
                if erro:
                    erros.append(f'{rotulo}: {erro}')
                else:
                    campos['lote'] = lote
            if 'sexo' in alteracao:
                sexo = str(alteracao.get('sexo') or '').strip().upper()
                if sexo not in SEXOS_VALIDOS:
                    erros.append(f'{rotulo}: Sexo incorreto.')
                else:
                    campos['sexo'] = sexo
            if 'id_raca' in alteracao:
                try:
                    id_raca = int(alteracao.get('id_raca'))
                except (TypeError, ValueError):
                    id_raca = None
                if id_raca not in racas_validas:
                    erros.append(f'{rotulo}: Raça inválida.')
                else:
                    campos['id_raca'] = id_raca
            if campos:
                mudancas.append((linha, campos))

        if erros:
            return jsonify({'erro': 'Corrija antes de salvar:', 'erros': erros[:20]}), 400
        if not mudancas:
            return jsonify({'erro': 'Nenhuma alteração para gravar.'}), 400

        # ---------------- composicao real x declarada (so GTA/NAS, so se o sexo mudou) ----------------
        composicao = None
        trocas_sexo = [(linha, campos['sexo']) for linha, campos in mudancas if 'sexo' in campos and campos['sexo'] != linha.sexo]
        if gta is not None and trocas_sexo:
            todas = db.query(Entrada).filter(Entrada.id_gta_entrada == gta.id).all()
            novo_sexo = {linha.id: sexo for linha, sexo in trocas_sexo}
            agora = {'MACHO': 0, 'FEMEA': 0}
            for animal in todas:
                sexo_final = novo_sexo.get(animal.id, animal.sexo)
                if sexo_final in agora:
                    agora[sexo_final] += 1
            declarado = None
            if origem_dados == 'compra':
                categorias = db.query(GtaAnimal).filter(GtaAnimal.id_gta == gta.id).all()
                if categorias:
                    declarado = {'MACHO': 0, 'FEMEA': 0}
                    for categoria in categorias:
                        if categoria.sexo in declarado:
                            declarado[categoria.sexo] += categoria.quantidade
            composicao = {'agora': agora, 'declarado': declarado}

        # ---------------- gravacao (mesma transacao + Log) ----------------
        descricao_origem = {
            'leituras': f'leituras de {valor}',
            'compra':   f'GTA {gta.numero_gta_completo}' if gta else 'GTA de Compra',
            'nas':      f'Notificação {gta.numero_gta_completo}' if gta else 'Notificação NAS',
        }[origem_dados]
        descricao = f'Alteração de dados de animais — {descricao_origem} — {len(mudancas)} animal(is)'
        if composicao:
            agora = composicao['agora']
            descricao += f' — sexo: {agora["MACHO"]}M/{agora["FEMEA"]}F'
            if composicao['declarado']:
                descricao += f' (GTA {composicao["declarado"]["MACHO"]}M/{composicao["declarado"]["FEMEA"]}F)'
        descricao = descricao[:120]   # v1.0.1 - a coluna nunca foi vista: descricao curta

        try:
            id_operacao = registrar_operacao(
                db,
                id_usuario=session['usuario_id'],
                id_propriedade=id_prop,
                modulo=NOME_MODULO_LOG,
                descricao=descricao,
            )
            alterados = 0
            for linha, campos in mudancas:
                if origem_dados == 'leituras':
                    houve = _aplicar_leitura(db, id_operacao, linha, campos)
                else:
                    houve = _aplicar_animal(db, id_operacao, id_prop, linha, campos, pesagens_brete, racas_validas)
                alterados += 1 if houve else 0
            db.commit()
        except Exception:
            db.rollback()
            return jsonify({'erro': 'Não foi possível gravar as alterações. Nada foi alterado.'}), 500

    return jsonify({
        'sucesso': True,
        'alterados': alterados,
        'mensagem': f'{alterados} animal(is) alterado(s) com sucesso.',
        'composicao': composicao,
    })

# =========================================================
# FIM DE ARQUIVO: backend\routers\alterar_dados_animais.py
# =========================================================
