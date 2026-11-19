# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\posse_leitura.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-05 13:30 -03
# ATUALIZADO EM: 2026-11-10 14:05 -03
# VERSAO: 1.8.0
# v1.8.0: Sessao 120 (2026-11-10 14:05 -03) - Animal vinculado a OUTRA GTA nao aparece mais na lista "lidos nesta data" nem no contador GRAVADOS da Leitura (Regra de Ouro #67; decisao do Benedito). REVERSAO: .bak_antes_s120_oculta_vinc.
# v1.7.0: Sessao 120 (2026-11-10 13:40 -03) - Regra de Ouro #67: animal VINCULADO a uma GTA nunca aparece como livre. Selecao separa livres x vinculados (com o numero da GTA); Leitura mostra a etiqueta da GTA no animal vinculado. REVERSAO: .bak_antes_s120_livres_posse.
# v1.6.1: Sessao 115 (2026-11-05 19:00 -03) - Mensagem de DTA atendida manda "Vincule a DTA" (serve para Leitor, Bastao e Lista). REVERSAO: .bak_antes_s115_aviso_vincular.
# v1.6.0: Sessao 115 (2026-11-05 18:55 -03) - Posse: andamento, trava de categoria e botao Vincular contam as leituras em aberto de qualquer data dentro da validade da DTA. REVERSAO: .bak_antes_s115_validade.
# v1.5.0: Sessao 115 (2026-11-05 18:35 -03) - Lista: botao Vincular a DTA (habilita quando os lidos atendem a DTA) e rota vincular-estado. REVERSAO: .bak_antes_s115_btn_vincular.
#
# DESCRICAO:
#     Leitor da Alteracao de Posse e Leitor da Alteracao de Posse com Bastao (Sessao 115, pacote 2).
#     Leitura no brete dos animais que ficam na MESMA Propriedade (mesmo OESA) e passam para OUTRO Produtor.
#     Navegacao: Home -> card "Saidas" -> Hub de Saidas (hub_entrada_agrupado.py, slug 'saida')
#     -> card "Leitor da Alteracao de Posse" (leitor) ou "... com Bastao" (bastao).
#
#     FLUXO (3 telas, o mesmo para as duas vias; a via vai na propria rota):
#       1. /produtor/posse/<via>/iniciar - resolve Propriedade (Padrao Reutilizavel N.1).
#       2. /produtor/posse/<via>/selecao - Data Leitura (vale como Data de Saida) e leituras em aberto.
#       3. /produtor/posse/<via>/leitura - cursor no SISBOV (leitor) ou no RFID (bastao).
#
#     MOLDE: copia da transferencia_leitura.py v1.6.1 (Regra de Ouro n.47: clonar e varrer).
#     REUSO (peca unica): conferencia do animal vem do saida_leitor.py (_buscar_animal) e do saida_bastao.py
#     (_buscar_animal_por_rfid), mais a trava de entrada (utils\entrada_comunicada.py). O Abate e a Transferencia
#     NAO sao alterados por aqui.
#
#     REGRAS (decisoes do Benedito, 05/11/2026):
#       - SEM peso, sexo, peso minimo, liberacao de abate nem ERAS: os animais nao saem da propriedade.
#       - Elemento (Botton/Brinco) continua, como controle interno. SEM Lote de Saida (no destino nao tem sentido).
#       - A LEITURA NAO DA BAIXA: grava so em tb_2020_embarque (tipo_saida = POSSE, sts = False). O destino
#         vem da DTA (pacote 3) e a baixa/entrada no destino acontece no Gerar Comunicado (pacote 4).
#       - Brinco com leitura em aberto (de qualquer tipo): mesma pergunta do Abate (excluir a antiga e usar
#         a nova, ou manter a antiga).
#       - Data Leitura = Data de Saida; a Entrada no destino usa a mesma data.
#
#     PACOTE 3 (DTA): o trecho "GTA na leitura" (escolher a DTA na Selecao, andamento por categoria, Concluir e vincular)
#     ja esta aqui, igual ao da Transferencia, e fica sem efeito (lista vazia) ate o Vincular GTA aceitar o tipo POSSE.
#     Quando o pacote 3 ensinar o saida_vincular.py, ele passa a funcionar; o texto do destino (_dados_destino_transfer)
#     sera ajustado la.
#
#     v1.4.0: Sessao 115 (2026-11-05 18:00 -03) - DTA de Posse: a caixa 'DTAs aguardando animais' mostra o destino (Estabelecimento - Produtor) e o check-list do destino usa a regra da Posse. REVERSAO: .bak_antes_s115_dta3a.
#     v1.3.0: Sessao 115 (2026-11-05 17:20 -03) - Lista: desmarcar animal ja gravado (rota lista/desfazer; so sem DTA vinculada). REVERSAO: .bak_antes_s115_desfazer.
#     v1.2.0: Sessao 115 (2026-11-05 16:55 -03) - Lista: animais ja gravados (Posse em aberto) continuam na tabela, travados e no topo, com 'Lido em'. REVERSAO: .bak_antes_s115_gravados.
#     v1.1.0: Sessao 115 (2026-11-05 14:15 -03) - Sem Lote de Saida; nova via 'lista' (Lista da Alteracao de Posse: marcar animais por Sexo/ERAS, marcar todos) e rota lista/gravar; Embarque montado por _novo_embarque. REVERSAO: .bak_antes_s115_lista.
#     v1.0.1: Sessao 115 (2026-11-05 13:55 -03) - Caixa 'DTAs aguardando animais' passa a listar so DTA de Posse (antes caia em GTA de Abate). REVERSAO: .bak_antes_s115_dta.
#     v1.0.0: Criacao (Sessao 115, pacote 2).
# =========================================================

from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, Produtor
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_4001_gta import Gta
from backend.utils.leituras_vinculo import resumo_abertas, numeros_gta, marcar_gtas_atendidas   # s120 - Regra de Ouro #67
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.models.tb_parceiros import Parceiro
from backend.models.tb_4001_gta_animais import GtaAnimal
from backend.routers.saida_vincular import _gtas_disponiveis, _necessidades, _classificar_livres, _codigos_de_especie, _faixa_em, _chave, _livres_da_gta_posse
from backend.utils.destino_transferencia import nomes_destinos_transfer
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.entrada_comunicada import motivo_entrada_pendente
from backend.routers.saida_leitor import (
    MENSAGEM_JA_CONFERIDO, MENSAGEM_MANEJO_PEDE_DV, URL_HUB,
    _propriedade_do_usuario, _data_br, _ler_data_br, _buscar_animal, _faixa_idade,
)
from backend.routers.saida_bastao import _buscar_animal_por_rfid, ELEMENTOS_POR_VIA


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
posse = Blueprint('posse', __name__)


@posse.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


# -------------------------------------------------------
# Constantes
# -------------------------------------------------------
TIPO_SAIDA_POSSE = 'POSSE'
URL_BASE = '/produtor/posse'

# via -> titulo e tela de leitura (a Selecao e uma so)
VIAS = {
    'leitor': {'titulo': 'Leitor da Alteração de Posse',
               'template': 'produtor/posse_leitor_leitura.html'},
    'bastao': {'titulo': 'Leitor da Alteração de Posse com Bastão',
               'template': 'produtor/posse_bastao_leitura.html'},
    'lista':  {'titulo': 'Lista da Alteração de Posse',
               'template': 'produtor/posse_lista.html'},
}

MENSAGENS_ERRO_SELECAO = {
    'data':    'Data Leitura incorreta. Digite no formato dd/mm/aaaa.',
    'gta':     'A GTA escolhida não está mais disponível (já tem Comunicado ou animais ligados). Escolha outra ou leia sem GTA.',
    'validade': 'A Data Leitura passa da Validade da GTA escolhida. Corrija a data.',   # v1.6.0
}
MENSAGEM_PROPRIEDADE_NEGADA = ('Propriedade não pertence ao seu usuário ou a fazenda em uso mudou. '
                               'Volte ao Hub de Saídas e abra de novo.')


def _url(via, etapa):
    return f'{URL_BASE}/{via}/{etapa}'


# -------------------------------------------------------
# Redirecionamento quando a Propriedade nao e do usuario.
# -------------------------------------------------------
def _negado(via):
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect(_url(via, 'iniciar'))
    return redirecionar_home()


# -------------------------------------------------------
# Leituras da Posse, por data (so POSSE, so em aberto). O destino vem da GTA, nao da leitura.
# -------------------------------------------------------
def _filtro_aberto(id_propriedade, data_leitura):
    return (
        Embarque.id_propriedade == int(id_propriedade),
        Embarque.tipo_saida == TIPO_SAIDA_POSSE,
        Embarque.data_embarque == data_leitura,
        Embarque.sts == False,   # noqa: E712
    )


def _contar_gravados(db, id_propriedade, data_leitura):
    return db.query(func.count(Embarque.id)).filter(*_filtro_aberto(id_propriedade, data_leitura), Embarque.id_gta.is_(None)).scalar() or 0   # s120 - so os livres


def _lidos_da_data(db, id_propriedade, data_leitura):
    linhas = (
        db.query(Embarque)
        .filter(*_filtro_aberto(id_propriedade, data_leitura), Embarque.id_gta.is_(None))   # s120 - vinculado a outra GTA nao aparece
        .order_by(Embarque.id.desc())
        .all()
    )
    _nums_gta = numeros_gta(db, [l.id_gta for l in linhas])   # s120 - numero da GTA do animal vinculado
    return [{
        'sisbov': l.sisbov,
        'manejo': l.manejo or '',
        'sexo': l.sexo or '',
        'hora': l.hora_embarque.strftime('%H:%M') if l.hora_embarque else '',
        'vinculado': l.id_gta is not None,
        'gta': _nums_gta.get(l.id_gta, ''),   # s120
    } for l in linhas]


# -------------------------------------------------------
# v1.3.0 - GTA NA LEITURA
# A DTA (GTA de Posse) da Propriedade, ainda sem Comunicado e sem animais ligados; ou None.
# -------------------------------------------------------
def _gta_posse_da_propriedade(db, id_propriedade, id_gta):
    try:
        id_int = int(id_gta)
    except (TypeError, ValueError):
        return None
    gta = (
        db.query(Gta)
        .filter(Gta.id == id_int,
                Gta.id_propriedade == int(id_propriedade),
                Gta.sentido == 'SAIDA',
                Gta.tipo_movimento == 'POSSE',
                Gta.numero_comunicado.is_(None))
        .first()
    )
    if gta is None:
        return None
    ja_ligada = db.query(func.count(Embarque.id)).filter(Embarque.id_gta == gta.id).scalar()
    return None if ja_ligada else gta


# -------------------------------------------------------
# v1.3.0 - Andamento da leitura contra a GTA: o que ela pede por categoria x o que ja foi lido
# (leituras em aberto da data, sem GTA ligada). Mesma classificacao do Vincular.
# -------------------------------------------------------
def _progresso_gta(db, id_propriedade, data_leitura, gta):
    faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
    nec = _necessidades(db.query(GtaAnimal).filter(GtaAnimal.id_gta == gta.id).all())
    livres = _livres_da_gta_posse(db, id_propriedade, gta)   # s115 - qualquer data dentro da validade da DTA
    por_chave, _sem_categoria = _classificar_livres(livres, faixas, None, _codigos_de_especie())
    linhas = []
    total_pede = 0
    dentro = 0
    for k, n in nec.items():
        lidos = len(por_chave.get(k, []))
        total_pede += n['qtd']
        dentro += min(lidos, n['qtd'])
        linhas.append({'rotulo': n['rotulo'], 'pede': n['qtd'], 'lidos': lidos})
    total_lidos = len(livres)
    sobra = total_lidos - dentro
    return {
        'numero': gta.numero_gta_completo,
        'linhas': linhas,
        'total_pede': total_pede,
        'total_lidos': total_lidos,
        'sobra': sobra,
        'completo': bool(linhas) and sobra == 0 and all(l['lidos'] == l['pede'] for l in linhas),
    }


# -------------------------------------------------------
# Conferencia de UM animal para a Alteracao de Posse. Usada pelo checar() e, de novo, pelo gravar().
# Devolve {'bloqueio': texto}  ou  {'repetido': {...}}  ou  {'animal': Entrada, 'ficha': {...}}
# Sem sexo, peso, liberacao nem ERAS (decisao do Benedito).
# -------------------------------------------------------
def _conferir_categoria_gta(db, id_propriedade, data_leitura, animal, id_gta):
    """
    v1.5.0 - Com GTA escolhida, so entra animal que a GTA pede (sexo + faixa de idade na Data Leitura)
    e enquanto a categoria ainda nao estiver completa. Devolve o texto do bloqueio, ou None se pode.
    Sem GTA escolhida (ou GTA que nao vale mais): None (le livre e vincula depois).
    """
    if not id_gta:
        return None
    gta = _gta_posse_da_propriedade(db, id_propriedade, id_gta)
    if gta is None:
        return None
    progresso = _progresso_gta(db, id_propriedade, data_leitura, gta)
    if progresso['completo']:   # v1.5.1 - GTA ja atendida: nao le mais, orienta a vincular
        return (f"GTA {gta.numero_gta_completo} atendida: os {progresso['total_pede']} animais pedidos já foram lidos. "
                f"Vincule a DTA para seguir.")
    faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
    nec = _necessidades(db.query(GtaAnimal).filter(GtaAnimal.id_gta == gta.id).all())
    pedido = ' / '.join(f"{n['qtd']} {n['rotulo']}" for n in nec.values())
    faixa = _faixa_em(faixas, animal.nascimento, data_leitura)
    especie = _codigos_de_especie().get(animal.id_especie)
    sexo_txt = {'MACHO': 'Macho', 'FEMEA': 'Fêmea'}.get(animal.sexo, animal.sexo or '-')
    chave = _chave(especie, animal.sexo, faixa)
    if faixa == '-' or not animal.sexo or not especie or chave not in nec:
        return (f'Este animal ({sexo_txt}, {faixa if faixa != "-" else "idade fora das faixas"}) não é da GTA '
                f'{gta.numero_gta_completo}. A GTA pede: {pedido}.')
    livres = _livres_da_gta_posse(db, id_propriedade, gta)   # s115 - qualquer data dentro da validade da DTA
    por_chave, _sem = _classificar_livres(livres, faixas, None, _codigos_de_especie())
    if len(por_chave.get(chave, [])) >= nec[chave]['qtd']:
        return (f"A GTA {gta.numero_gta_completo} já tem todos os animais de {nec[chave]['rotulo']} "
                f"({nec[chave]['qtd']}). A GTA pede: {pedido}.")
    return None


def _validar_posse(db, id_propriedade, data_leitura, sisbov, manejo, dv, id_gta=None):
    animal, bloqueio = _buscar_animal(db, id_propriedade, sisbov, manejo, dv)
    if bloqueio:
        if bloqueio == MENSAGEM_MANEJO_PEDE_DV:
            return {'bloqueio': bloqueio, 'pede_dv': True}
        return {'bloqueio': bloqueio}

    motivo_entrada = motivo_entrada_pendente(db, animal)   # animal com entrada ainda nao comunicada nao sai
    if motivo_entrada:
        return {'bloqueio': motivo_entrada}

    aberta = (
        db.query(Embarque)
        .filter(Embarque.sisbov == animal.sisbov, Embarque.sts == False)   # noqa: E712
        .order_by(Embarque.id.desc())
        .first()
    )
    if aberta is not None:
        return {'repetido': {
            'sisbov': animal.sisbov,
            'data': _data_br(aberta.data_embarque),
            'hora': aberta.hora_embarque.strftime('%H:%M') if aberta.hora_embarque else '',
        }}

    bloqueio_gta = _conferir_categoria_gta(db, id_propriedade, data_leitura, animal, id_gta)   # v1.5.0
    if bloqueio_gta:
        return {'bloqueio': bloqueio_gta}

    faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
    dias_idade = (data_leitura - animal.nascimento).days if animal.nascimento else None
    raca = db.get(Raca, animal.id_raca) if animal.id_raca else None
    ficha = {
        'sisbov': animal.sisbov,
        'manejo': animal.manejo or '',
        'rfid': animal.rfid or '',
        'sexo': animal.sexo or '',
        'raca': raca.codigo if raca else '',
        'nascimento': _data_br(animal.nascimento),
        'idade_meses': _faixa_idade(faixas, dias_idade),
        'lote_entrada': animal.lote or '',
    }
    return {'animal': animal, 'ficha': ficha}


def _novo_embarque(db, id_propriedade, animal, data_leitura, elemento, agora):
    """Leitura de Posse (tb_2020, tipo POSSE, em aberto) de UM animal. Usada pelo Leitor/Bastao e pela Lista."""
    gta = db.get(Gta, animal.id_gta_entrada) if animal.id_gta_entrada else None
    origem = db.get(Parceiro, animal.id_origem) if animal.id_origem else None

    return Embarque(
        id_propriedade=int(id_propriedade),
        id_animal=animal.id,
        sisbov=animal.sisbov,
        manejo=animal.manejo,
        rfid=animal.rfid,
        id_especie=animal.id_especie,
        sexo=animal.sexo,
        nascimento=animal.nascimento,
        eras_dias=animal.eras_dias,
        id_aptidao=animal.id_aptidao,
        id_raca=animal.id_raca,
        cota_hilton=bool(animal.cota_hilton),
        liberacao_abate=animal.liberacao_abate,
        gta_entrada=((gta.numero_gta_completo or '')[:10] or None) if gta else None,
        gta_entrada_emissao=gta.data_emissao if gta else None,
        gta_entrada_validade=gta.data_validade if gta else None,
        gta_entrada_animais=gta.qtde_animais if gta else None,
        data_inclusao=animal.data_inclusao,
        lote_entrada=animal.lote,
        origem_propriedade=(origem.nome or '')[:150] if origem else None,
        origem_cpf_cnpj=origem.cpf_cnpj if origem else None,
        tipo_saida=TIPO_SAIDA_POSSE,
        data_embarque=data_leitura,
        hora_embarque=agora.time().replace(microsecond=0),
        elemento=elemento or None,
        sts=False,
    )


# -------------------------------------------------------
# Rota: GET /produtor/posse/<via>/iniciar - ponto de partida.
# -------------------------------------------------------
@posse.route('/produtor/posse/<via>/iniciar')
def iniciar(via):
    if via not in VIAS:
        return redirect(URL_HUB)
    if 'id_produtor' not in session:
        return redirecionar_home()

    url_selecao = _url(via, 'selecao')
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista,
            erro=erro,
            titulo=f'{VIAS[via]["titulo"]} — Selecionar Propriedade',
            proximo=url_selecao,
            campo_propriedade='id_propriedade',
            voltar=URL_HUB,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='saidas',
        )

    if len(pares) == 0:
        return _tela_selecionar([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')

    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{url_selecao}?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{url_selecao}?id_propriedade={par.id_propriedade}')

    return _tela_selecionar(pares, None)


# -------------------------------------------------------
# Rota: GET /produtor/posse/<via>/selecao - so a Data Leitura (o destino vem da GTA).
# -------------------------------------------------------
@posse.route('/produtor/posse/<via>/selecao')
def selecao(via):
    if via not in VIAS:
        return redirect(URL_HUB)
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado(via)

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        url_voltar = _url(via, 'iniciar')
    else:
        url_voltar = URL_HUB

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
        produtor = db.get(Produtor, session['id_produtor'])
        nome_produtor = produtor.nome if produtor else None

    # Leituras de Posse em aberto (sem Comunicado), uma linha por data.
    abertas = []
    resumo = []   # s120 - leituras em aberto por data (livres x vinculadas); tambem usado para marcar as GTAs atendidas
    try:
        with get_db_produtor(session['id_produtor']) as db_prod:
            resumo = resumo_abertas(db_prod, id_propriedade, TIPO_SAIDA_POSSE)
        abertas = [{'data': _data_br(r['data']), 'quantidade': r['livres'] + r['vinculados'], 'livres': r['livres'], 'vinculados': r['vinculados'], 'gtas': r['gtas_txt']} for r in resumo]
    except Exception:
        abertas = []

    # v1.3.0 - DTAs de Posse ainda sem animais (para escolher antes de ler; opcional)
    gtas_posse = []
    try:
        with get_db_produtor(session['id_produtor']) as db_gta:
            # v1.0.1 - so DTA de Posse (tipo_movimento POSSE), ainda sem Comunicado e sem animais; nunca GTA de Abate
            todas = (db_gta.query(Gta)
                     .filter(Gta.id_propriedade == int(id_propriedade), Gta.sentido == 'SAIDA',
                             Gta.tipo_movimento == 'POSSE', Gta.numero_comunicado.is_(None))
                     .order_by(Gta.data_emissao.desc(), Gta.numero_gta_completo.desc()).all())
            ids_todas = [g.id for g in todas]
            usadas = set()
            if ids_todas:
                usadas = {r[0] for r in db_gta.query(Embarque.id_gta).filter(Embarque.id_gta.in_(ids_todas)).distinct().all()}
            nomes_dest = nomes_destinos_transfer(db_gta, [g.id_parceiro_propriedade for g in todas])
            gtas_posse = [{'id': g.id, 'numero': g.numero_gta_completo, 'destino': nomes_dest.get(g.id_parceiro_propriedade, '-')}
                          for g in todas if g.id not in usadas]
            # v1.6.0 - Validade de cada GTA (a tela avisa na hora se a Data Leitura passar dela)
            validades = {}
            ids_gta = [g['id'] for g in gtas_posse]
            if ids_gta:
                validades = {i: v for i, v in db_gta.query(Gta.id, Gta.data_validade).filter(Gta.id.in_(ids_gta)).all()}
            for g in gtas_posse:
                v = validades.get(g['id'])
                g['validade_iso'] = v.strftime('%Y-%m-%d') if v else ''
                g['validade_br'] = _data_br(v) if v else ''
            marcar_gtas_atendidas(db_gta, id_propriedade, gtas_posse, resumo, _progresso_gta)   # s120 - marca a GTA que os animais livres ja atendem
    except Exception:
        gtas_posse = []

    return render_template(
        'produtor/posse_selecao.html',
        erro=MENSAGENS_ERRO_SELECAO.get(request.args.get('erro', '')),
        via=via,
        titulo_tela=VIAS[via]['titulo'],
        propriedade=propriedade,
        nome_produtor=nome_produtor,
        id_propriedade=id_propriedade,
        url_voltar=url_voltar,
        url_leitura=_url(via, 'leitura'),
        data_hoje=_data_br(date.today()),
        abertas=abertas,
        gtas_posse=gtas_posse,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='saidas',
    )


# -------------------------------------------------------
# Rota: GET /produtor/posse/<via>/leitura - Tela de Leitura.
# -------------------------------------------------------
@posse.route('/produtor/posse/<via>/leitura')
def leitura(via):
    if via not in VIAS:
        return redirect(URL_HUB)
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado(via)

    base = f'{_url(via, "selecao")}?id_propriedade={id_propriedade}'
    data_leitura = _ler_data_br(request.args.get('data_leitura', ''))
    if data_leitura is None:
        return redirect(f'{base}&erro=data')

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))

    id_gta_txt = (request.args.get('id_gta', '') or '').strip()
    if via == 'lista':
        return _tela_lista(via, propriedade, id_propriedade, data_leitura, id_gta_txt, base)
    gta_info = None
    with get_db_produtor(session['id_produtor']) as db:
        total_gravados = _contar_gravados(db, id_propriedade, data_leitura)
        lidos = _lidos_da_data(db, id_propriedade, data_leitura)
        if id_gta_txt:
            gta = _gta_posse_da_propriedade(db, id_propriedade, id_gta_txt)
            if gta is None:
                return redirect(f'{base}&erro=gta')
            # v1.6.0 - Data Leitura nao pode passar da Validade da GTA (a tela ja avisa; o servidor confere de novo)
            if gta.data_validade and data_leitura > gta.data_validade:
                return redirect(f'{base}&erro=validade')
            id_pp = gta.id_parceiro_propriedade
            gta_info = {
                'id': gta.id,
                'numero': gta.numero_gta_completo,
                'destino_nome': nomes_destinos_transfer(db, [id_pp]).get(id_pp, '-'),
                'progresso': _progresso_gta(db, id_propriedade, data_leitura, gta),
                'url_vincular': (f'/produtor/saida-vincular/conferencia?id_propriedade={int(id_propriedade)}'
                                 f'&data={data_leitura.strftime("%Y-%m-%d")}&id_gta={gta.id}'),
                'destino_texto': '',
            }
            id_pp_destino = id_pp

    # resultado do check-list do destino (nossa base), como na GTA
    if gta_info is not None:
        from backend.routers.gta_saida import _dados_destino_transfer   # import tardio: evita ciclo entre routers
        destino = _dados_destino_transfer(id_pp_destino, id_propriedade, 'POSSE')
        if destino:
            conf = destino['conferencia']
            gta_info['destino_texto'] = (conf['itens'][-1]['texto'] if conf['nivel'] != 'bloqueio' else conf['titulo'])
            if conf.get('status') == 'NA_BASE':   # v1.4.1 - destino na base: sem frase (Benedito, 29/10)
                gta_info['destino_texto'] = ''

    return render_template(
        VIAS[via]['template'],
        id_gta=id_gta_txt if gta_info else '',
        gta_info=gta_info,
        propriedade=propriedade,
        id_propriedade=id_propriedade,
        data_leitura=_data_br(data_leitura),
        total_gravados=total_gravados,
        lidos=lidos,
        url_selecao=base,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='saidas',
    )


# -------------------------------------------------------
# Rota: POST /produtor/posse/checar (AJAX) - confere o animal assim que o SISBOV (ou o
# RFID, ou o Manejo) e lido. Serve ao Leitor e ao Bastao.
# -------------------------------------------------------
@posse.route('/produtor/posse/checar', methods=['POST'])
def checar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    rfid   = (dados.get('rfid') or '').strip()
    sisbov = (dados.get('sisbov') or '').strip()
    manejo = (dados.get('manejo') or '').strip()
    dv     = (dados.get('dv') or '').strip()
    data_leitura = _ler_data_br(dados.get('data_leitura'))
    id_gta_tela = dados.get('id_gta')   # v1.5.0 - GTA escolhida: so entra animal que ela pede

    if not id_propriedade or (not rfid and not sisbov and not manejo) or data_leitura is None:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': MENSAGEM_PROPRIEDADE_NEGADA}), 403

    with get_db_produtor(session['id_produtor']) as db:
        if rfid:
            animal, bloqueio = _buscar_animal_por_rfid(db, id_propriedade, rfid)
            if bloqueio:
                return jsonify({'bloqueio': True, 'mensagem': bloqueio, 'pede_dv': False})
            # achou o animal pelo chip: a conferencia daqui em diante e pelo SISBOV dele
            resultado = _validar_posse(db, id_propriedade, data_leitura, animal.sisbov, '', '', id_gta_tela)
        else:
            resultado = _validar_posse(db, id_propriedade, data_leitura, sisbov, manejo, dv, id_gta_tela)

    if 'bloqueio' in resultado:
        return jsonify({'bloqueio': True, 'mensagem': resultado['bloqueio'], 'pede_dv': bool(resultado.get('pede_dv'))})
    if 'repetido' in resultado:
        return jsonify({'repetido': True, 'leitura_antiga': resultado['repetido']})
    return jsonify({'ok': True, 'animal': resultado['ficha']})


# -------------------------------------------------------
# Rota: POST /produtor/posse/gravar (AJAX) - grava a leitura em tb_2020_embarque
# (tipo POSSE, sem destino: ele vem da GTA no Vincular). Confere TUDO de novo no servidor.
# -------------------------------------------------------
@posse.route('/produtor/posse/gravar', methods=['POST'])
def gravar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = (dados.get('sisbov') or '').strip()
    via    = (dados.get('via') or '').strip().upper()
    elemento = (dados.get('elemento') or '').strip().upper()
    data_leitura = _ler_data_br(dados.get('data_leitura'))
    id_gta_tela = dados.get('id_gta')   # v1.3.0 - GTA escolhida na Selecao (so para mostrar o andamento)

    if not id_propriedade or not sisbov or data_leitura is None or via not in ELEMENTOS_POR_VIA:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': MENSAGEM_PROPRIEDADE_NEGADA}), 403
    if elemento and elemento not in ELEMENTOS_POR_VIA[via]:
        return jsonify({'erro': 'Elemento incorreto para esta forma de leitura.'}), 400

    with get_db_produtor(session['id_produtor']) as db:
        resultado = _validar_posse(db, id_propriedade, data_leitura, sisbov, '', '', id_gta_tela)
        if 'bloqueio' in resultado:
            return jsonify({'bloqueio': True, 'mensagem': resultado['bloqueio'], 'erro': resultado['bloqueio']}), 409
        if 'repetido' in resultado:
            # a tela deveria ter perguntado antes; se chegou aqui, o servidor nao grava por cima
            return jsonify({'bloqueio': True, 'mensagem': MENSAGEM_JA_CONFERIDO, 'erro': MENSAGEM_JA_CONFERIDO}), 409

        animal = resultado['animal']
        agora = datetime.now()
        embarque = _novo_embarque(db, id_propriedade, animal, data_leitura, elemento, agora)
        db.add(embarque)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            return jsonify({'bloqueio': True, 'erro': MENSAGEM_JA_CONFERIDO,
                            'mensagem': MENSAGEM_JA_CONFERIDO}), 409

        total_gravados = _contar_gravados(db, id_propriedade, data_leitura)
        progresso_gta = None
        if id_gta_tela:
            gta_tela = _gta_posse_da_propriedade(db, id_propriedade, id_gta_tela)
            if gta_tela is not None:
                progresso_gta = _progresso_gta(db, id_propriedade, data_leitura, gta_tela)
        hora_txt = embarque.hora_embarque.strftime('%H:%M')
        manejo_txt = animal.manejo or ''
        sexo_txt = animal.sexo or ''
        db.commit()

    return jsonify({
        'sucesso': True,
        'mensagem': 'Gravação Efetuada com Sucesso',
        'sisbov': sisbov,
        'manejo': manejo_txt,
        'sexo': sexo_txt,
        'hora': hora_txt,
        'total_gravados': total_gravados,
        'gta_progresso': progresso_gta,
    })


# -------------------------------------------------------
# v1.1.0 - LISTA DA ALTERACAO DE POSSE (Pacote 2B)
# Em vez de ler no brete, o usuario ve os animais em estoque (SISBOV, Manejo, Sexo, ERAS, Raca), filtra por Sexo e
# ERAS e marca (ou "marca todos" do filtro). Cada animal passa pela MESMA validacao da leitura (_validar_posse).
# Grava em tb_2020_embarque (tipo POSSE, sts = False), igual ao Leitor/Bastao. A leitura nao da baixa.
# -------------------------------------------------------
LIMITE_LISTA = 5000


# -------------------------------------------------------
# v1.5.0 - Botao "Vincular a DTA" da Lista: habilita quando os animais LIDOS da data atendem a DTA (contagem exata por categoria).
# -------------------------------------------------------
def _estado_vincular(db, id_propriedade, data_leitura, id_gta_txt):
    if not id_gta_txt:
        return None
    gta = _gta_posse_da_propriedade(db, id_propriedade, id_gta_txt)
    if gta is None:
        return None
    prog = _progresso_gta(db, id_propriedade, data_leitura, gta)
    dica = ''
    if not prog['completo']:
        partes = [f"faltam {l['pede'] - l['lidos']} {l['rotulo']}" for l in prog['linhas'] if l['lidos'] < l['pede']]
        if prog['sobra'] > 0:
            partes.append(f"{prog['sobra']} animal(is) lido(s) a mais do que a DTA pede")
        dica = '; '.join(partes) or 'Leia/grave os animais que a DTA pede.'
    return {
        'numero': prog['numero'],
        'habilita': bool(prog['completo']),
        'dica': dica,
        'url': (f'/produtor/saida-vincular/conferencia?id_propriedade={int(id_propriedade)}'
                f'&data={data_leitura.strftime("%Y-%m-%d")}&id_gta={gta.id}'),
    }


@posse.route('/produtor/posse/lista/vincular-estado')
def lista_vincular_estado():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    data_leitura = _ler_data_br(request.args.get('data_leitura', ''))
    if not data_leitura:
        return jsonify({'erro': 'Data inválida.'}), 400
    with get_db_produtor(session['id_produtor']) as db:
        estado = _estado_vincular(db, id_propriedade, data_leitura, request.args.get('id_gta', ''))
    return jsonify({'ok': True, 'estado': estado})


def _tela_lista(via, propriedade, id_propriedade, data_leitura, id_gta_txt, base):
    with get_db_produtor(session['id_produtor']) as db:
        if id_gta_txt and _gta_posse_da_propriedade(db, id_propriedade, id_gta_txt) is None:
            return redirect(f'{base}&erro=gta')
        faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
        racas = {r.id: r.codigo for r in db.query(Raca).all()}
        com_leitura = select(Embarque.sisbov).where(Embarque.sts == False)   # noqa: E712
        animais = (
            db.query(Entrada)
            .filter(Entrada.id_propriedade == int(id_propriedade), ~Entrada.sisbov.in_(com_leitura))
            .order_by(Entrada.manejo.asc(), Entrada.sisbov.asc())
            .limit(LIMITE_LISTA + 1)
            .all()
        )
        cortado = len(animais) > LIMITE_LISTA
        animais = animais[:LIMITE_LISTA]
        # v1.2.0 - os ja gravados (leitura de Posse em aberto) continuam na lista, travados, no topo
        gravados = (
            db.query(Embarque)
            .filter(Embarque.id_propriedade == int(id_propriedade),
                    Embarque.tipo_saida == TIPO_SAIDA_POSSE, Embarque.sts == False)   # noqa: E712
            .order_by(Embarque.data_embarque.desc(), Embarque.manejo.asc(), Embarque.sisbov.asc())
            .all()
        )
        linhas = []
        for g in gravados:
            dias = (g.data_embarque - g.nascimento).days if g.nascimento else None
            linhas.append({
                'sisbov': g.sisbov, 'manejo': g.manejo or '', 'sexo': g.sexo or '',
                'eras': _faixa_idade(faixas, dias), 'raca': racas.get(g.id_raca, ''),
                'gravado': True, 'lido_em': _data_br(g.data_embarque), 'vinculado': g.id_gta is not None,
            })
        qtde_gravados = len(linhas)
        estado_vincular = _estado_vincular(db, id_propriedade, data_leitura, id_gta_txt)
        for a in animais:
            dias = (data_leitura - a.nascimento).days if a.nascimento else None
            linhas.append({
                'sisbov': a.sisbov,
                'manejo': a.manejo or '',
                'sexo': a.sexo or '',
                'eras': _faixa_idade(faixas, dias),
                'raca': racas.get(a.id_raca, ''),
                'gravado': False, 'lido_em': '', 'vinculado': False,
            })
    return render_template(
        VIAS[via]['template'],
        titulo_tela=VIAS[via]['titulo'],
        propriedade=propriedade,
        id_propriedade=id_propriedade,
        data_leitura=_data_br(data_leitura),
        id_gta=id_gta_txt,
        animais=linhas,
        qtde_gravados=qtde_gravados,
        estado_vincular=estado_vincular,
        url_vincular_estado=f'{URL_BASE}/lista/vincular-estado',
        eras_opcoes=[f.descricao for f in faixas],
        cortado=cortado,
        limite=LIMITE_LISTA,
        url_selecao=base,
        url_gravar=f'{URL_BASE}/lista/gravar',
        url_desfazer=f'{URL_BASE}/lista/desfazer',
        url_hub=URL_HUB,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='saidas',
    )


@posse.route('/produtor/posse/lista/gravar', methods=['POST'])
def lista_gravar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    data_leitura = _ler_data_br(dados.get('data_leitura'))
    id_gta_tela = dados.get('id_gta')
    sisbovs = dados.get('sisbovs')
    if not id_propriedade or data_leitura is None or not isinstance(sisbovs, list) or not sisbovs:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if len(sisbovs) > LIMITE_LISTA:
        return jsonify({'erro': f'Marque no máximo {LIMITE_LISTA} animais de uma vez.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': MENSAGEM_PROPRIEDADE_NEGADA}), 403

    gravados = 0
    falhas = []
    vistos = set()
    agora = datetime.now()
    with get_db_produtor(session['id_produtor']) as db:
        for bruto in sisbovs:
            sisbov = str(bruto or '').strip()
            if not sisbov or sisbov in vistos:
                continue
            vistos.add(sisbov)
            resultado = _validar_posse(db, id_propriedade, data_leitura, sisbov, '', '', id_gta_tela)
            if 'bloqueio' in resultado:
                falhas.append({'sisbov': sisbov, 'motivo': resultado['bloqueio']})
                continue
            if 'repetido' in resultado:
                falhas.append({'sisbov': sisbov, 'motivo': MENSAGEM_JA_CONFERIDO})
                continue
            try:
                with db.begin_nested():
                    db.add(_novo_embarque(db, id_propriedade, resultado['animal'], data_leitura, None, agora))
                    db.flush()
                gravados += 1
            except IntegrityError:
                falhas.append({'sisbov': sisbov, 'motivo': MENSAGEM_JA_CONFERIDO})
        total_gravados = _contar_gravados(db, id_propriedade, data_leitura)
        db.commit()
    return jsonify({'sucesso': True, 'gravados': gravados, 'falhas': falhas, 'total_gravados': total_gravados})


@posse.route('/produtor/posse/lista/desfazer', methods=['POST'])
def lista_desfazer():
    """v1.3.0 - Desmarcar na Lista um animal ja gravado: apaga SO a leitura de Posse em aberto (sem Comunicado) e
    ainda NAO vinculada a uma DTA. Vinculada = Desvincular primeiro. Mesma regra do excluir-leitura. Fica linha no log."""
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbovs = dados.get('sisbovs')
    if not id_propriedade or not isinstance(sisbovs, list) or not sisbovs:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': MENSAGEM_PROPRIEDADE_NEGADA}), 403

    desfeitos = 0
    falhas = []
    with get_db_produtor(session['id_produtor']) as db:
        for bruto in {str(s or '').strip() for s in sisbovs}:
            if not bruto:
                continue
            linha = (
                db.query(Embarque)
                .filter(Embarque.id_propriedade == int(id_propriedade), Embarque.tipo_saida == TIPO_SAIDA_POSSE,
                        Embarque.sts == False, Embarque.sisbov == bruto)   # noqa: E712
                .first()
            )
            if linha is None:
                falhas.append({'sisbov': bruto, 'motivo': 'Leitura não encontrada (já foi desfeita ou já tem Comunicado).'})
            elif linha.id_gta is not None:
                falhas.append({'sisbov': bruto, 'motivo': 'Já está vinculado a uma DTA. Use o Desvincular antes.'})
            else:
                db.delete(linha)
                desfeitos += 1
        db.commit()
    try:
        from flask import current_app
        current_app.logger.info('DESFAZER LEITURA Posse (lista): produtor=%s propriedade=%s qtde=%s',
                                session.get('id_produtor'), id_propriedade, desfeitos)
    except Exception:
        pass
    return jsonify({'sucesso': True, 'desfeitos': desfeitos, 'falhas': falhas})


# -------------------------------------------------------
# Rota: POST /produtor/posse/excluir-leitura (AJAX) - EXCLUIR UMA LEITURA da lista "Geral" (Sessao 108).
# Apaga SO a leitura em aberto (sem Comunicado) e AINDA NAO vinculada a uma GTA.
# Depois de vinculada, o caminho e o Desvincular. Fica uma linha no log do servidor (quem, qual brinco, quando).
# -------------------------------------------------------
@posse.route('/produtor/posse/excluir-leitura', methods=['POST'])
def excluir_leitura():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = (dados.get('sisbov') or '').strip()
    data_leitura = _ler_data_br(dados.get('data_leitura'))
    id_gta_tela = dados.get('id_gta')
    if not id_propriedade or not sisbov or data_leitura is None:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou.'}), 403

    with get_db_produtor(session['id_produtor']) as db:
        linha = (
            db.query(Embarque)
            .filter(*_filtro_aberto(id_propriedade, data_leitura), Embarque.sisbov == sisbov)
            .first()
        )
        if linha is None:
            return jsonify({'erro': 'Leitura não encontrada (já foi excluída ou o embarque já foi concluído).'}), 404
        if linha.id_gta is not None:
            return jsonify({'erro': 'Esta leitura já está vinculada a uma GTA. Use o Desvincular antes de excluir.'}), 409
        db.delete(linha)
        db.flush()
        total_gravados = _contar_gravados(db, id_propriedade, data_leitura)
        progresso_gta = None
        if id_gta_tela:
            gta_tela = _gta_posse_da_propriedade(db, id_propriedade, id_gta_tela)
            if gta_tela is not None:
                progresso_gta = _progresso_gta(db, id_propriedade, data_leitura, gta_tela)
        db.commit()

    try:
        from flask import current_app
        current_app.logger.info('EXCLUIR LEITURA Posse: produtor=%s propriedade=%s sisbov=%s data=%s',
                                session.get('id_produtor'), id_propriedade, sisbov, dados.get('data_leitura'))
    except Exception:
        pass
    return jsonify({'sucesso': True, 'total_gravados': total_gravados, 'gta_progresso': progresso_gta})

# =========================================================
# FIM DE ARQUIVO: backend\routers\posse_leitura.py
# =========================================================
