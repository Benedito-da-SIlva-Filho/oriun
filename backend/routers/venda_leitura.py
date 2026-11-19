# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\venda_leitura.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-01 12:30 -03
# ATUALIZADO EM: 2026-11-10 14:05 -03
# VERSAO: 1.2.0
# v1.2.0: Sessao 120 (2026-11-10 14:05 -03) - Animal vinculado a OUTRA GTA nao aparece mais na lista "lidos nesta data" nem no contador GRAVADOS da Leitura (Regra de Ouro #67; decisao do Benedito). REVERSAO: .bak_antes_s120_oculta_vinc.
# v1.1.0: Sessao 120 (2026-11-10 13:40 -03) - Regra de Ouro #67: animal VINCULADO a uma GTA nunca aparece como livre. Selecao separa livres x vinculados (com o numero da GTA); Leitura mostra a etiqueta da GTA no animal vinculado. REVERSAO: .bak_antes_s120_livres_venda.
#
# DESCRICAO:
#     Leitor da Venda e Leitor da Venda com Bastao. Leitura no brete dos animais que sao vendidos para OUTRO Produtor.
#     Mesma regra da Transferencia: o animal e lido SEM destino; o destino (comprador) vem da GTA de Venda no Vincular GTA.
#     Sem sexo, peso minimo, liberacao nem ERAS. A leitura NAO da baixa: grava so em tb_2020_embarque (tipo_saida = VENDA, sts = False).
#     Rotas: /produtor/venda/<via>/iniciar|selecao|leitura e /produtor/venda/checar|gravar|excluir-leitura.
#     v1.0.0: Sessao 111 (01/11/2026) - Criacao: copia da Transferencia (transferencia_*) com tipo_saida = VENDA e GTA de Venda.
#     v1.0.1: Sessao 113 (03/11/2026, 13:10 -03) - Mensagem de peso simplificada: "Peso incorreto, verifique."  REVERSAO: .bak_antes_s113_peso.
#             REVERSAO: apagar este arquivo e os venda_*.html e desfazer o registro em app.py e no Hub.
# =========================================================

from datetime import datetime, date
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, Produtor
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4001_gta import Gta
from backend.utils.leituras_vinculo import resumo_abertas, numeros_gta, marcar_gtas_atendidas   # s120 - Regra de Ouro #67
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.models.tb_parceiros import Parceiro
from backend.models.tb_4001_gta_animais import GtaAnimal
from backend.routers.saida_vincular import _gtas_disponiveis, _necessidades, _classificar_livres, _codigos_de_especie, _faixa_em, _chave
from backend.utils.destino_transferencia import nomes_destinos_transfer
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.entrada_comunicada import motivo_entrada_pendente
from backend.routers.saida_leitor import (
    MENSAGEM_JA_CONFERIDO, MENSAGEM_MANEJO_PEDE_DV, URL_HUB,
    _propriedade_do_usuario, _data_br, _ler_data_br, _buscar_animal, _faixa_idade, _ler_decimal, _formatar_kg,
)
from backend.routers.saida_bastao import _buscar_animal_por_rfid, ELEMENTOS_POR_VIA


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
venda = Blueprint('venda', __name__)


@venda.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


# -------------------------------------------------------
# Constantes
# -------------------------------------------------------
TIPO_SAIDA_VENDA = 'VENDA'
URL_BASE = '/produtor/venda'

# via -> titulo e tela de leitura (a Selecao e uma so)
VIAS = {
    'leitor': {'titulo': 'Leitor da Venda',
               'template': 'produtor/venda_leitor_leitura.html'},
    'bastao': {'titulo': 'Leitor da Venda com Bastão',
               'template': 'produtor/venda_bastao_leitura.html'},
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
# Leituras da Venda, por data (so VENDA, so em aberto). O destino vem da GTA, nao da leitura.
# -------------------------------------------------------
def _filtro_aberto(id_propriedade, data_leitura):
    return (
        Embarque.id_propriedade == int(id_propriedade),
        Embarque.tipo_saida == TIPO_SAIDA_VENDA,
        Embarque.data_embarque == data_leitura,
        Embarque.sts == False,   # noqa: E712
    )


PESO_MAXIMO = Decimal('3000')


def _ultimo_peso(db, sisbov):
    """Ultima pesagem do animal (tb_4003_pesos) ou None."""
    return (db.query(Peso).filter(Peso.sisbov == sisbov).order_by(Peso.sequencia.desc()).first())


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
        'peso': _formatar_kg(l.peso_saida) if l.peso_saida is not None else '',
        'vinculado': l.id_gta is not None,
        'gta': _nums_gta.get(l.id_gta, ''),   # s120
    } for l in linhas]


# -------------------------------------------------------
# v1.3.0 - GTA NA LEITURA
# A GTA de Venda da Propriedade, ainda sem Comunicado e sem animais ligados; ou None.
# -------------------------------------------------------
def _gta_venda_da_propriedade(db, id_propriedade, id_gta):
    try:
        id_int = int(id_gta)
    except (TypeError, ValueError):
        return None
    gta = (
        db.query(Gta)
        .filter(Gta.id == id_int,
                Gta.id_propriedade == int(id_propriedade),
                Gta.sentido == 'SAIDA',
                Gta.tipo_movimento == 'VENDA',
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
    livres = (
        db.query(Embarque)
        .filter(*_filtro_aberto(id_propriedade, data_leitura), Embarque.id_gta.is_(None))
        .all()
    )
    por_chave, _sem_categoria = _classificar_livres(livres, faixas, data_leitura, _codigos_de_especie())
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
# Conferencia de UM animal para a Venda. Usada pelo checar() e, de novo, pelo gravar().
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
    gta = _gta_venda_da_propriedade(db, id_propriedade, id_gta)
    if gta is None:
        return None
    progresso = _progresso_gta(db, id_propriedade, data_leitura, gta)
    if progresso['completo']:   # v1.5.1 - GTA ja atendida: nao le mais, orienta a vincular
        return (f"GTA {gta.numero_gta_completo} atendida: os {progresso['total_pede']} animais pedidos já foram lidos. "
                f"Clique em \u201cConcluir e vincular esta GTA\u201d para seguir.")
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
    livres = (
        db.query(Embarque)
        .filter(*_filtro_aberto(id_propriedade, data_leitura), Embarque.id_gta.is_(None))
        .all()
    )
    por_chave, _sem = _classificar_livres(livres, faixas, data_leitura, _codigos_de_especie())
    if len(por_chave.get(chave, [])) >= nec[chave]['qtd']:
        return (f"A GTA {gta.numero_gta_completo} já tem todos os animais de {nec[chave]['rotulo']} "
                f"({nec[chave]['qtd']}). A GTA pede: {pedido}.")
    return None


def _validar_venda(db, id_propriedade, data_leitura, sisbov, manejo, dv, id_gta=None):
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
            'peso': '',
            'hora': aberta.hora_embarque.strftime('%H:%M') if aberta.hora_embarque else '',
        }}

    bloqueio_gta = _conferir_categoria_gta(db, id_propriedade, data_leitura, animal, id_gta)   # v1.5.0
    if bloqueio_gta:
        return {'bloqueio': bloqueio_gta}

    faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
    dias_idade = (data_leitura - animal.nascimento).days if animal.nascimento else None
    raca = db.get(Raca, animal.id_raca) if animal.id_raca else None
    ultimo = _ultimo_peso(db, animal.sisbov)
    ficha = {
        'sisbov': animal.sisbov,
        'manejo': animal.manejo or '',
        'rfid': animal.rfid or '',
        'sexo': animal.sexo or '',
        'raca': raca.codigo if raca else '',
        'nascimento': _data_br(animal.nascimento),
        'idade_meses': _faixa_idade(faixas, dias_idade),
        'lote_entrada': animal.lote or '',
        'peso_anterior': _formatar_kg(ultimo.peso) if ultimo is not None else '',
        'data_peso': _data_br(ultimo.data_pesagem) if ultimo is not None else '',
    }
    return {'animal': animal, 'ficha': ficha}


# -------------------------------------------------------
# Rota: GET /produtor/venda/<via>/iniciar - ponto de partida.
# -------------------------------------------------------
@venda.route('/produtor/venda/<via>/iniciar')
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
# Rota: GET /produtor/venda/<via>/selecao - so a Data Leitura (o destino vem da GTA).
# -------------------------------------------------------
@venda.route('/produtor/venda/<via>/selecao')
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

    # Leituras de Venda em aberto (sem Comunicado), uma linha por data.
    abertas = []
    resumo = []   # s120 - leituras em aberto por data (livres x vinculadas); tambem usado para marcar as GTAs atendidas
    try:
        with get_db_produtor(session['id_produtor']) as db_prod:
            resumo = resumo_abertas(db_prod, id_propriedade, TIPO_SAIDA_VENDA)
        abertas = [{'data': _data_br(r['data']), 'quantidade': r['livres'] + r['vinculados'], 'livres': r['livres'], 'vinculados': r['vinculados'], 'gtas': r['gtas_txt']} for r in resumo]
    except Exception:
        abertas = []

    # v1.3.0 - GTAs de Venda ainda sem animais (para escolher antes de ler; opcional)
    gtas_venda = []
    try:
        with get_db_produtor(session['id_produtor']) as db_gta:
            gtas_venda = _gtas_disponiveis(db_gta, id_propriedade, ['VENDA'])['VENDA']
            # v1.6.0 - Validade de cada GTA (a tela avisa na hora se a Data Leitura passar dela)
            validades = {}
            ids_gta = [g['id'] for g in gtas_venda]
            if ids_gta:
                validades = {i: v for i, v in db_gta.query(Gta.id, Gta.data_validade).filter(Gta.id.in_(ids_gta)).all()}
            for g in gtas_venda:
                v = validades.get(g['id'])
                g['validade_iso'] = v.strftime('%Y-%m-%d') if v else ''
                g['validade_br'] = _data_br(v) if v else ''
            marcar_gtas_atendidas(db_gta, id_propriedade, gtas_venda, resumo, _progresso_gta)   # s120 - marca a GTA que os animais livres ja atendem
    except Exception:
        gtas_venda = []

    return render_template(
        'produtor/venda_selecao.html',
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
        gtas_venda=gtas_venda,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='saidas',
    )


# -------------------------------------------------------
# Rota: GET /produtor/venda/<via>/leitura - Tela de Leitura.
# -------------------------------------------------------
@venda.route('/produtor/venda/<via>/leitura')
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
    gta_info = None
    with get_db_produtor(session['id_produtor']) as db:
        total_gravados = _contar_gravados(db, id_propriedade, data_leitura)
        lidos = _lidos_da_data(db, id_propriedade, data_leitura)
        if id_gta_txt:
            gta = _gta_venda_da_propriedade(db, id_propriedade, id_gta_txt)
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
        destino = _dados_destino_transfer(id_pp_destino, id_propriedade, 'VENDA')
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
# Rota: POST /produtor/venda/checar (AJAX) - confere o animal assim que o SISBOV (ou o
# RFID, ou o Manejo) e lido. Serve ao Leitor e ao Bastao.
# -------------------------------------------------------
@venda.route('/produtor/venda/checar', methods=['POST'])
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
            resultado = _validar_venda(db, id_propriedade, data_leitura, animal.sisbov, '', '', id_gta_tela)
        else:
            resultado = _validar_venda(db, id_propriedade, data_leitura, sisbov, manejo, dv, id_gta_tela)

    if 'bloqueio' in resultado:
        return jsonify({'bloqueio': True, 'mensagem': resultado['bloqueio'], 'pede_dv': bool(resultado.get('pede_dv'))})
    if 'repetido' in resultado:
        return jsonify({'repetido': True, 'leitura_antiga': resultado['repetido']})
    return jsonify({'ok': True, 'animal': resultado['ficha']})


# -------------------------------------------------------
# Rota: POST /produtor/venda/gravar (AJAX) - grava a leitura em tb_2020_embarque
# (tipo VENDA, sem destino: ele vem da GTA no Vincular). Confere TUDO de novo no servidor.
# -------------------------------------------------------
@venda.route('/produtor/venda/gravar', methods=['POST'])
def gravar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = (dados.get('sisbov') or '').strip()
    via    = (dados.get('via') or '').strip().upper()
    elemento = (dados.get('elemento') or '').strip().upper()
    lote_saida = (dados.get('lote_saida') or '').strip()
    data_leitura = _ler_data_br(dados.get('data_leitura'))
    peso_txt = str(dados.get('peso') or '').strip()
    peso = _ler_decimal(peso_txt) if peso_txt else None
    id_gta_tela = dados.get('id_gta')   # v1.3.0 - GTA escolhida na Selecao (so para mostrar o andamento)

    if not id_propriedade or not sisbov or data_leitura is None or via not in ELEMENTOS_POR_VIA:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': MENSAGEM_PROPRIEDADE_NEGADA}), 403
    if elemento and elemento not in ELEMENTOS_POR_VIA[via]:
        return jsonify({'erro': 'Elemento incorreto para esta forma de leitura.'}), 400
    if len(lote_saida) > 30:
        return jsonify({'erro': 'Lote de Saída com mais de 30 caracteres.'}), 400
    if peso_txt and (peso is None or peso <= 0 or peso > PESO_MAXIMO):
        return jsonify({'erro': 'Peso incorreto, verifique.'}), 400

    with get_db_produtor(session['id_produtor']) as db:
        resultado = _validar_venda(db, id_propriedade, data_leitura, sisbov, '', '', id_gta_tela)
        if 'bloqueio' in resultado:
            return jsonify({'bloqueio': True, 'mensagem': resultado['bloqueio'], 'erro': resultado['bloqueio']}), 409
        if 'repetido' in resultado:
            # a tela deveria ter perguntado antes; se chegou aqui, o servidor nao grava por cima
            return jsonify({'bloqueio': True, 'mensagem': MENSAGEM_JA_CONFERIDO, 'erro': MENSAGEM_JA_CONFERIDO}), 409

        animal = resultado['animal']
        if peso is None:   # nao digitou: vale o ultimo peso do animal (se houver)
            ultimo = _ultimo_peso(db, animal.sisbov)
            peso = Decimal(str(ultimo.peso)) if ultimo is not None else None
        gta = db.get(Gta, animal.id_gta_entrada) if animal.id_gta_entrada else None
        origem = db.get(Parceiro, animal.id_origem) if animal.id_origem else None
        agora = datetime.now()

        embarque = Embarque(
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
            tipo_saida=TIPO_SAIDA_VENDA,
            data_embarque=data_leitura,
            hora_embarque=agora.time().replace(microsecond=0),
            lote_saida=lote_saida or None,
            peso_saida=peso.quantize(Decimal('0.01')) if peso is not None else None,
            elemento=elemento or None,
            sts=False,
        )
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
            gta_tela = _gta_venda_da_propriedade(db, id_propriedade, id_gta_tela)
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
        'peso': _formatar_kg(peso) if peso is not None else '',
        'total_gravados': total_gravados,
        'gta_progresso': progresso_gta,
    })


# -------------------------------------------------------
# Rota: POST /produtor/venda/excluir-leitura (AJAX) - EXCLUIR UMA LEITURA da lista "Geral" (Sessao 108).
# Apaga SO a leitura em aberto (sem Comunicado) e AINDA NAO vinculada a uma GTA.
# Depois de vinculada, o caminho e o Desvincular. Fica uma linha no log do servidor (quem, qual brinco, quando).
# -------------------------------------------------------
@venda.route('/produtor/venda/excluir-leitura', methods=['POST'])
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
            gta_tela = _gta_venda_da_propriedade(db, id_propriedade, id_gta_tela)
            if gta_tela is not None:
                progresso_gta = _progresso_gta(db, id_propriedade, data_leitura, gta_tela)
        db.commit()

    try:
        from flask import current_app
        current_app.logger.info('EXCLUIR LEITURA Venda: produtor=%s propriedade=%s sisbov=%s data=%s',
                                session.get('id_produtor'), id_propriedade, sisbov, dados.get('data_leitura'))
    except Exception:
        pass
    return jsonify({'sucesso': True, 'total_gravados': total_gravados, 'gta_progresso': progresso_gta})

# =========================================================
# FIM DE ARQUIVO: backend\routers\venda_leitura.py
# =========================================================
