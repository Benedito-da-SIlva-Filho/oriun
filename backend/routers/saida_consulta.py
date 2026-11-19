# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\saida_consulta.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-17 17:15 -03
# ATUALIZADO EM: 2026-11-08 13:30 -03
# VERSAO: 1.7.1
# v1.7.1: Sessao 118 (2026-11-08 13:30 -03) - Machos/Femeas por linha na Consulta Embarque. REVERSAO: .bak_antes_s118_pedido
#
# DESCRICAO:
#     Consulta Embarque (Sessao 099) - grupo "Consultas e correcoes" do Hub
#     de Saidas, no molde da tela do GERAS: uma linha por Data de Embarque
#     (animais lidos no brete e ainda sem Comunicado), com a quantidade, a
#     Saida (ABATE) e os botoes:
#       Correcao      - lista dos animais da data; Data Embarque e Peso Saida
#                       sao editaveis por animal (desmembrar um embarque =
#                       mudar a data so de alguns animais).
#       Impressao     - abre o Relatorio de Embarque da data (saida_relatorio).
#       Abate         - gera o arquivo ABATE.TXT (Em breve).
#       Data Embarque - troca a data de TODOS os animais da data por uma nova;
#                       se a nova data ja existe, as leituras se juntam
#                       (caso real: 200 animais a tarde + 200 na manha seguinte
#                       = um embarque so).
#
#     ERAS (faixa de idade): NAO e gravada - e calculada na hora, pela idade
#     do animal NA Data Embarque. Mudou a data, a faixa e recalculada. Antes de
#     confirmar a troca de data, a tela avisa quantos animais mudam de faixa
#     (evita pedir a GTA com categoria errada e desclassificacao no frigorifico).
#
#     Data Embarque = data de saida do animal: pode ser ate 30 dias a frente
#     (o caminhao pode sair depois da leitura) e nao pode ser muito antiga.
#     Peso: maior ou igual ao Peso Minimo padrao (100 kg) e ate 2000 kg.
#     So mexe em leituras com sts = False (Comunicado ainda nao gerado).
#     Nao mexe em eras_dias (copia informativa da leitura).
#
#     ROTAS (/produtor/saida-consulta/):
#       iniciar, lista, data-embarque, data-embarque/previa (JSON),
#       data-embarque/salvar (POST), correcao, correcao/salvar (POST).
#
#     v1.0.0: Criacao (Sessao 099).
#     v1.1.0: Sessao 100 (19/10/2026, 18:20 -03) - Animal LIGADO a GTA nao pode ter Data Embarque nem Peso mexidos (decisao de Benedito: o usuario
#             desvincula a GTA antes). Troca de Data Embarque e Correcao gravam Log (modulos saida_data_embarque e
#             saida_correcao, so historico). Correcao mostra os ligados travados, com o numero da GTA.
#             REVERSAO: devolver .bak_antes_log_saidas_s100.
#     v1.2.0: Sessao 107 (28/10/2026) - Aceita TRANSFERENCIA: uma linha por Data + tipo + destino (id da Propriedade destino). As rotas
#             recebem tipo e dest (sem tipo = ABATE, compativel). Transferencia nao tem Peso Saida (Correcao sem coluna de peso) e
#             a Impressao do embarque (Pedido de GTA do Abate) fica so no Abate. REVERSAO: devolver .bak_antes_s107c.
#     v1.2.1: Sessao 107 - Abate tambem mostra o destino (Frigorifico da GTA vinculada; 'sem GTA' enquanto nao ha vinculo), padrao com a Transferencia.
#     v1.3.0: Sessao 107 - Transferencia tambem lida SEM destino (igual ao Abate): uma linha por Data + tipo; o destino exibido
#             e o da GTA de Transferencia vinculada. REVERSAO: devolver .bak_antes_s107d.
#     v1.4.1: Sessao 107 (28/10/2026, 19:45) - Correcao da Transferencia tambem mostra e grava o Peso Saida (opcional: em branco mantem o peso; sem Peso Minimo; ate 2000 kg).  REVERSAO: .bak_antes_s107za.
#     v1.3.1: Sessao 107 - o destino da Transferencia na lista vem da GTA de Transferencia vinculada (ou 'sem GTA vinculada'). REVERSAO: .bak_antes_s107i.
#     REVERSAO: remover este arquivo e os templates saida_consulta_*.html;
#     devolver os .bak_antes_consulta_embarque_s099.
#     v1.5.1: Sessao 114 (04/11/2026, 10:37 -03) - Correcao do Abate: mensagem de peso abaixo do minimo vira "peso incorreto, verifique." (mantem o SISBOV na frente).  REVERSAO: .bak_antes_s114_peso.
#     v1.7.0: Sessao 118 (2026-11-08 13:00 -03) - A lista aceita o parametro tipo (ABATE, TRANSFER, VENDA ou POSSE) e mostra so aquele tipo; sem tipo continua mostrando todos (Consultas e correcoes). iniciar leva o tipo adiante. Motivo: o card Consulta Embarque entrou como passo de cada aba do Hub. REVERSAO: .bak_antes_s118_filtro.
#     v1.6.0: Sessao 115 (2026-11-05 17:05 -03) - Alteracao de Posse (tipo POSSE) entra na lista, na Correcao (so a data, sem peso e sem lote) e no Data Embarque.  REVERSAO: .bak_antes_s115_consulta.
# =========================================================

from datetime import datetime, date, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, Produtor
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4001_gta import Gta
from backend.models.tb_frigorificos import Frigorifico
from backend.utils.destino_transferencia import nomes_destinos_transfer
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.saida_leitor import PESO_MINIMO_PADRAO, _ler_decimal, _formatar_kg
from backend.utils.multitenant import get_db_produtor
from backend.utils.log_operacoes import registrar_operacao, registrar_item

saida_consulta = Blueprint('saida_consulta', __name__)

TIPO_SAIDA_ABATE = 'ABATE'
TIPO_SAIDA_TRANSFER = 'TRANSFER'
TIPO_SAIDA_VENDA = 'VENDA'                  # s111 - Venda: lida sem destino, igual a Transferencia (comprador vem da GTA)
TIPO_SAIDA_POSSE = 'POSSE'                  # s115 - Alteracao de Posse (sem peso e sem lote; destino vem da DTA)
TIPOS_COM_DESTINO = (TIPO_SAIDA_TRANSFER, TIPO_SAIDA_VENDA, TIPO_SAIDA_POSSE)
ROTULO_SAIDA_TXT = {TIPO_SAIDA_TRANSFER: 'Transferência', TIPO_SAIDA_VENDA: 'Venda', TIPO_SAIDA_POSSE: 'Alteração de Posse'}
ROTULO_SAIDA = {TIPO_SAIDA_ABATE: 'ABATE', TIPO_SAIDA_TRANSFER: 'TRANSFERÊNCIA', TIPO_SAIDA_VENDA: 'VENDA', TIPO_SAIDA_POSSE: 'ALTERAÇÃO DE POSSE'}
URL_HUB     = '/produtor/hub-novo/saida'
URL_INICIAR = '/produtor/saida-consulta/iniciar'
URL_LISTA   = '/produtor/saida-consulta/lista'
DIAS_A_FRENTE_MAX = 30
PESO_MAXIMO = Decimal('2000')
DATA_MINIMA = date(2020, 1, 1)
MSG_LIGADOS = ('Esta data tem {n} animal(is) ligado(s) a uma GTA. Desvincule a GTA '
               '(Vincular GTA / Embarque) antes de trocar a data.')


def _ligados_na_data(db, id_propriedade, data, tipo=TIPO_SAIDA_ABATE, dest=None):
    """Quantos animais abertos da data ja estao ligados a uma GTA."""
    return db.query(func.count(Embarque.id)).filter(
        *_filtro_abertas(id_propriedade, tipo, dest), Embarque.data_embarque == data,
        Embarque.id_gta.isnot(None)).scalar()


def _ler_tipo_dest(fonte):
    """Le 'tipo' e 'dest' (id da Propriedade destino) da URL ou do JSON. Sem tipo = ABATE.
    Devolve (tipo, id_destino, ok); ok False = Transferencia sem destino valido."""
    bruto = str(fonte.get('tipo') or '').strip().upper()
    if bruto not in TIPOS_COM_DESTINO:
        return TIPO_SAIDA_ABATE, None, True
    return bruto, None, True   # o destino vem da GTA, nao da leitura


def _tipo_filtro_da_url():
    """s118 - tipo pedido na URL para filtrar a lista (ABATE, TRANSFER, VENDA ou POSSE). Vazio = todos."""
    bruto = str(request.args.get('tipo') or '').strip().upper()
    return bruto if bruto in (TIPO_SAIDA_ABATE,) + TIPOS_COM_DESTINO else ''


def _qs_tipo(tipo, dest):
    """Trecho de URL que leva o tipo/destino junto (vazio no Abate)."""
    return f'&tipo={tipo}' if tipo in TIPOS_COM_DESTINO else ''


def _destinos_transfer_por_data(id_produtor, id_propriedade, tipo=TIPO_SAIDA_TRANSFER):
    """{data: texto} com o destino das GTAs de Transferencia vinculadas as leituras abertas da data ('sem GTA vinculada' enquanto nao ha vinculo)."""
    resultado = {}
    with get_db_produtor(id_produtor) as db:
        pares = db.query(Embarque.data_embarque, Embarque.id_gta, func.count(Embarque.id)).filter(
            *_filtro_abertas(id_propriedade, tipo)).group_by(Embarque.data_embarque, Embarque.id_gta).all()
        ids_gta = {i for _d, i, _q in pares if i}
        pp_por_gta = {}
        if ids_gta:
            pp_por_gta = {g.id: g.id_parceiro_propriedade for g in db.query(Gta).filter(Gta.id.in_(ids_gta)).all()}
        nomes = nomes_destinos_transfer(db, list(pp_por_gta.values()))
    por_data = {}
    for d, id_gta, q in pares:
        item = por_data.setdefault(d, {'nomes': [], 'sem': 0})
        if id_gta:
            n = nomes.get(pp_por_gta.get(id_gta), '-')
            if n not in item['nomes']:
                item['nomes'].append(n)
        else:
            item['sem'] += q
    for d, item in por_data.items():
        partes = list(item['nomes'])
        if item['sem']:
            partes.append('sem GTA vinculada' if not partes else f"{item['sem']} sem GTA")
        resultado[d] = ' / '.join(partes)
    return resultado


def _nome_propriedade(id_propriedade):
    with Session(engine) as db:
        p = db.get(Propriedade, int(id_propriedade))
        return p.nome if p else '-'


def _contexto_base():
    return dict(
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='saidas',
    )


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
        return redirect(URL_INICIAR)
    return redirecionar_home()


def _data_br(d):
    return d.strftime('%d/%m/%Y') if d else '-'


def _ler_iso(texto):
    try:
        return datetime.strptime((texto or '').strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def _ler_br(texto):
    try:
        return datetime.strptime((texto or '').strip(), '%d/%m/%Y').date()
    except ValueError:
        return None


def _validar_data_embarque(texto):
    """Devolve (data, None) ou (None, mensagem)."""
    d = _ler_br(texto)
    if d is None:
        return None, 'Data incorreta! Use o formato dd/mm/aaaa.'
    if d < DATA_MINIMA:
        return None, 'Data de Embarque muito antiga. Confira o ano digitado.'
    limite = date.today() + timedelta(days=DIAS_A_FRENTE_MAX)
    if d > limite:
        return None, (f'Data de Embarque muito distante: no máximo {DIAS_A_FRENTE_MAX} dias à frente '
                      f'({_data_br(limite)}). Confira o ano digitado.')
    return d, None


def _faixa_em(faixas, nascimento, data_ref):
    if not nascimento:
        return '-'
    dias = (data_ref - nascimento).days
    for f in faixas:
        if f.dias_min <= dias <= f.dias_max:
            return f.descricao
    return '-'


def _filtro_abertas(id_propriedade, tipo=TIPO_SAIDA_ABATE, dest=None):
    filtros = [
        Embarque.id_propriedade == int(id_propriedade),
        Embarque.tipo_saida == tipo,
        Embarque.sts == False,   # noqa: E712
    ]
    return tuple(filtros)


def _nomes(id_propriedade, id_produtor):
    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
        produtor = db.get(Produtor, id_produtor)
        return (
            produtor.nome if produtor else '-',
            propriedade.nome if propriedade else '-',
            f'{propriedade.municipio or ""} / {propriedade.uf or ""}' if propriedade else '',
        )


# -------------------------------------------------------
# GET /produtor/saida-consulta/iniciar
# -------------------------------------------------------
@saida_consulta.route('/produtor/saida-consulta/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista,
            erro=erro,
            titulo='Consulta Embarque — Selecionar Propriedade',
            proximo=URL_LISTA,
            campo_propriedade='id_propriedade',
            voltar=URL_HUB,
            **_contexto_base(),
        )

    if len(pares) == 0:
        return _tela_selecionar([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')

    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{URL_LISTA}?id_propriedade={par_em_uso.id_propriedade}' + (f'&tipo={_tipo_filtro_da_url()}' if _tipo_filtro_da_url() else ''))

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_LISTA}?id_propriedade={par.id_propriedade}' + (f'&tipo={_tipo_filtro_da_url()}' if _tipo_filtro_da_url() else ''))

    return _tela_selecionar(pares, None)


# -------------------------------------------------------
# GET /produtor/saida-consulta/lista - uma linha por Data de Embarque.
# -------------------------------------------------------
@saida_consulta.route('/produtor/saida-consulta/lista')
def lista():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']
    tipo_filtro = _tipo_filtro_da_url()   # s118 - vazio = todos os tipos
    tipos_da_lista = [tipo_filtro] if tipo_filtro else [TIPO_SAIDA_ABATE, TIPO_SAIDA_TRANSFER, TIPO_SAIDA_VENDA, TIPO_SAIDA_POSSE]

    with get_db_produtor(id_produtor) as db:
        linhas = (
            db.query(Embarque.data_embarque, Embarque.tipo_saida, func.count(Embarque.id))
            .filter(
                Embarque.id_propriedade == int(id_propriedade),
                Embarque.tipo_saida.in_(tipos_da_lista),
                Embarque.sts == False,   # noqa: E712
            )
            .group_by(Embarque.data_embarque, Embarque.tipo_saida)
            .order_by(Embarque.data_embarque.desc(), Embarque.tipo_saida.asc())
            .all()
        )
        # s118 - Machos / Femeas de cada linha (data + tipo)
        sexos = {}
        for d_, tp_, sx_, q_ in (
            db.query(Embarque.data_embarque, Embarque.tipo_saida, Embarque.sexo, func.count(Embarque.id))
            .filter(Embarque.id_propriedade == int(id_propriedade), Embarque.tipo_saida.in_(tipos_da_lista),
                    Embarque.sts == False)   # noqa: E712
            .group_by(Embarque.data_embarque, Embarque.tipo_saida, Embarque.sexo).all()
        ):
            sexos.setdefault((d_, tp_), {})[sx_] = q_

    # Destino do Abate = Frigorifico da GTA vinculada (so exibicao; a linha do Abate continua sendo por data).
    with get_db_produtor(id_produtor) as dbf:
        pares_frigo = dbf.query(Embarque.data_embarque, Embarque.id_frigorifico, func.count(Embarque.id)).filter(
            *_filtro_abertas(id_propriedade)).group_by(Embarque.data_embarque, Embarque.id_frigorifico).all()
    nomes_frigo = {}
    ids_frigo = {i for _d, i, _q in pares_frigo if i}
    if ids_frigo:
        with Session(engine) as dbp:
            nomes_frigo = {f.id: f.nome for f in dbp.query(Frigorifico).filter(Frigorifico.id.in_(ids_frigo)).all()}
    destino_abate = {}
    for d_, i_, q_ in pares_frigo:
        item = destino_abate.setdefault(d_, {'nomes': [], 'sem': 0})
        if i_:
            n_ = nomes_frigo.get(i_, '-')
            if n_ not in item['nomes']:
                item['nomes'].append(n_)
        else:
            item['sem'] += q_

    destino_por_tipo = {t_: _destinos_transfer_por_data(id_produtor, id_propriedade, t_) for t_ in TIPOS_COM_DESTINO}

    def _destino_abate(d_):
        item = destino_abate.get(d_)
        if not item:
            return ''
        partes = list(item['nomes'])
        if item['sem']:
            partes.append('sem GTA vinculada' if not partes else f"{item['sem']} sem GTA")
        return ' / '.join(partes)

    def _destino_transfer(d_, t_):
        return destino_por_tipo.get(t_, {}).get(d_, '')

    embarques = [{
        'iso': d.strftime('%Y-%m-%d'),
        'data': _data_br(d),
        'qtde': qtd,
        'machos': sexos.get((d, tp), {}).get('MACHO', 0),
        'femeas': sexos.get((d, tp), {}).get('FEMEA', 0),
        'saida': ROTULO_SAIDA.get(tp, TIPO_SAIDA_ABATE),
        'destino': _destino_transfer(d, tp) if tp in TIPOS_COM_DESTINO else _destino_abate(d),
        'transfer': tp in TIPOS_COM_DESTINO,
        'tipo': tp,
        'qs': _qs_tipo(tp, None),
    } for d, tp, qtd in linhas]

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_consulta_lista.html',
        embarques=embarques,
        id_propriedade=int(id_propriedade),
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        url_hub=URL_HUB,
        tipo_filtro=tipo_filtro,
        rotulo_filtro=ROTULO_SAIDA.get(tipo_filtro, '') if tipo_filtro else '',
        **_contexto_base(),
    )


# -------------------------------------------------------
# GET /produtor/saida-consulta/data-embarque - tela de troca de data.
# -------------------------------------------------------
@saida_consulta.route('/produtor/saida-consulta/data-embarque')
def data_embarque():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    atual = _ler_iso(request.args.get('data', ''))
    voltar = f'{URL_LISTA}?id_propriedade={int(id_propriedade)}'
    tipo, dest, ok_tipo = _ler_tipo_dest(request.args)
    if not atual or not ok_tipo:
        return redirect(voltar)
    id_produtor = session['id_produtor']

    with get_db_produtor(id_produtor) as db:
        qtde = db.query(func.count(Embarque.id)).filter(
            *_filtro_abertas(id_propriedade, tipo, dest), Embarque.data_embarque == atual).scalar()
        ligados = _ligados_na_data(db, id_propriedade, atual, tipo, dest)
    if not qtde:
        return redirect(voltar)

    produtor_nome, propriedade_nome, _ = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_consulta_data.html',
        id_propriedade=int(id_propriedade),
        iso=atual.strftime('%Y-%m-%d'),
        data_atual=_data_br(atual),
        qtde=qtde,
        ligados=ligados,
        msg_ligados=MSG_LIGADOS.format(n=ligados),
        tipo=tipo,
        dest=dest,
        qs=_qs_tipo(tipo, dest),
        destino_nome='',
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        url_lista=voltar,
        **_contexto_base(),
    )


# -------------------------------------------------------
# GET .../data-embarque/previa (JSON) - o que acontece se a data mudar:
# quantos animais mudam de faixa e se a nova data ja tem animais (juncao).
# -------------------------------------------------------
@saida_consulta.route('/produtor/saida-consulta/data-embarque/previa')
def data_embarque_previa():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    atual = _ler_iso(request.args.get('data', ''))
    if not atual:
        return jsonify({'erro': 'Data atual inválida.'}), 400
    tipo, dest, ok_tipo = _ler_tipo_dest(request.args)
    if not ok_tipo:
        return jsonify({'erro': 'Destino da Transferência inválido.'}), 400
    nova, erro = _validar_data_embarque(request.args.get('nova', ''))
    if erro:
        return jsonify({'ok': False, 'erro': erro})
    if nova == atual:
        return jsonify({'ok': False, 'erro': 'A nova data é igual à data atual.'})

    with get_db_produtor(session['id_produtor']) as db:
        faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
        animais = db.query(Embarque.nascimento).filter(
            *_filtro_abertas(id_propriedade, tipo, dest), Embarque.data_embarque == atual).all()
        ja_existem = db.query(func.count(Embarque.id)).filter(
            *_filtro_abertas(id_propriedade, tipo, dest), Embarque.data_embarque == nova).scalar()
        ligados = _ligados_na_data(db, id_propriedade, atual, tipo, dest)
    if ligados:
        return jsonify({'ok': False, 'erro': MSG_LIGADOS.format(n=ligados)})

    mudancas = {}
    sem_nascimento = 0
    for (nasc,) in ([] if tipo in TIPOS_COM_DESTINO else animais):   # faixa ERAS so importa no Abate (frigorifico)
        if not nasc:
            sem_nascimento += 1
            continue
        de = _faixa_em(faixas, nasc, atual)
        para = _faixa_em(faixas, nasc, nova)
        if de != para:
            mudancas[(de, para)] = mudancas.get((de, para), 0) + 1

    detalhes = [{'de': de, 'para': para, 'qtd': qtd} for (de, para), qtd in sorted(mudancas.items())]
    return jsonify({
        'ok': True,
        'total': len(animais),
        'mudam': sum(d['qtd'] for d in detalhes),
        'detalhes': detalhes,
        'ja_existem': ja_existem,
        'sem_nascimento': sem_nascimento,
    })


# -------------------------------------------------------
# POST .../data-embarque/salvar - troca a data de todos os animais da data.
# -------------------------------------------------------
@saida_consulta.route('/produtor/saida-consulta/data-embarque/salvar', methods=['POST'])
def data_embarque_salvar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    atual = _ler_iso(dados.get('data', ''))
    if not atual:
        return jsonify({'erro': 'Data atual inválida.'}), 400
    tipo, dest, ok_tipo = _ler_tipo_dest(dados)
    if not ok_tipo:
        return jsonify({'erro': 'Destino da Transferência inválido.'}), 400
    nova, erro = _validar_data_embarque(dados.get('nova', ''))
    if erro:
        return jsonify({'erro': erro}), 400
    if nova == atual:
        return jsonify({'erro': 'A nova data é igual à data atual.'}), 400

    with get_db_produtor(session['id_produtor']) as db:
        linhas = db.query(Embarque).filter(
            *_filtro_abertas(id_propriedade, tipo, dest), Embarque.data_embarque == atual).all()
        if not linhas:
            return jsonify({'erro': 'Não há animais nesta data (talvez já tenham sido alterados).'}), 400
        ligados = sum(1 for l in linhas if l.id_gta is not None)
        if ligados:
            return jsonify({'erro': MSG_LIGADOS.format(n=ligados)}), 400
        total = len(linhas)
        id_operacao = registrar_operacao(
            db, id_usuario=session['usuario_id'], id_propriedade=int(id_propriedade),
            modulo='saida_data_embarque',
            descricao=f'Data Embarque: {_data_br(atual)} para {_data_br(nova)} ({total} animal(is))')
        for l in linhas:
            antes = l.data_embarque
            l.data_embarque = nova
            registrar_item(db, id_operacao, 'tb_2020_embarque', l.id, 'UPDATE',
                           {'data_embarque': antes.isoformat() if antes else None},
                           {'data_embarque': nova.isoformat()})
        db.commit()

    return jsonify({'ok': True, 'total': total, 'nova': _data_br(nova),
                    'url': f'{URL_LISTA}?id_propriedade={int(id_propriedade)}'})


# -------------------------------------------------------
# GET /produtor/saida-consulta/correcao - animais da data, com Data Embarque
# e Peso editaveis.
# -------------------------------------------------------
@saida_consulta.route('/produtor/saida-consulta/correcao')
def correcao():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    atual = _ler_iso(request.args.get('data', ''))
    voltar = f'{URL_LISTA}?id_propriedade={int(id_propriedade)}'
    tipo, dest, ok_tipo = _ler_tipo_dest(request.args)
    if not atual or not ok_tipo:
        return redirect(voltar)
    id_produtor = session['id_produtor']

    with get_db_produtor(id_produtor) as db:
        faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
        racas = {r.id: r.codigo for r in db.query(Raca).all()}
        leituras = (
            db.query(Embarque)
            .filter(*_filtro_abertas(id_propriedade, tipo, dest), Embarque.data_embarque == atual)
            .order_by(Embarque.sisbov.asc())
            .all()
        )
        ids_gta = {l.id_gta for l in leituras if l.id_gta is not None}
        numeros_gta = {g.id: g.numero_gta_completo for g in db.query(Gta).filter(Gta.id.in_(ids_gta)).all()} if ids_gta else {}
        animais = [{
            'id': l.id,
            'travado': l.id_gta is not None,
            'gta': numeros_gta.get(l.id_gta, '') if l.id_gta is not None else '',
            'sisbov': l.sisbov,
            'rfid': l.rfid or '',
            'sexo': {'FEMEA': 'Fêmea', 'MACHO': 'Macho'}.get(l.sexo, l.sexo or '-'),
            'faixa': _faixa_em(faixas, l.nascimento, atual),
            'raca': racas.get(l.id_raca, '-'),
            'data': _data_br(l.data_embarque),
            'lote_saida': l.lote_saida or '',
            'peso': _formatar_kg(l.peso_saida) if l.peso_saida is not None else '',
        } for l in leituras]

    if not animais:
        return redirect(voltar)

    produtor_nome, propriedade_nome, _ = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_consulta_correcao.html',
        animais=animais,
        id_propriedade=int(id_propriedade),
        iso=atual.strftime('%Y-%m-%d'),
        data_atual=_data_br(atual),
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        peso_minimo=_formatar_kg(PESO_MINIMO_PADRAO),
        tipo=tipo,
        dest=dest,
        sem_peso=(tipo == TIPO_SAIDA_POSSE),   # s115 - Posse nao tem peso nem lote
        destino_nome='',
        url_lista=voltar,
        **_contexto_base(),
    )


# -------------------------------------------------------
# POST .../correcao/salvar - grava Data Embarque e Peso dos animais alterados.
# Tudo ou nada: se uma linha tem erro, nada e gravado.
# -------------------------------------------------------
@saida_consulta.route('/produtor/saida-consulta/correcao/salvar', methods=['POST'])
def correcao_salvar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    tipo, dest, ok_tipo = _ler_tipo_dest(dados)
    if not ok_tipo:
        return jsonify({'erro': 'Destino da Transferência inválido.'}), 400
    alteracoes = dados.get('alteracoes')
    if not isinstance(alteracoes, list) or not alteracoes:
        return jsonify({'erro': 'Nenhuma alteração para gravar.'}), 400

    with get_db_produtor(session['id_produtor']) as db:
        ids = []
        for a in alteracoes:
            try:
                ids.append(int(a.get('id')))
            except (TypeError, ValueError, AttributeError):
                return jsonify({'erro': 'Alteração inválida.'}), 400
        linhas = {l.id: l for l in db.query(Embarque).filter(
            *_filtro_abertas(id_propriedade, tipo, dest), Embarque.id.in_(ids)).all()}

        pendentes = []
        for a in alteracoes:
            l = linhas.get(int(a['id']))
            if l is None:
                return jsonify({'erro': 'Animal não encontrado ou já com Comunicado. Recarregue a tela.'}), 400
            if l.id_gta is not None:
                return jsonify({'erro': f'SISBOV {l.sisbov}: está ligado a uma GTA. Desvincule a GTA (Vincular GTA / Embarque) antes de corrigir.'}), 400
            nova_data, erro = _validar_data_embarque(a.get('data', ''))
            if erro:
                return jsonify({'erro': f'SISBOV {l.sisbov}: {erro}'}), 400
            if tipo == TIPO_SAIDA_POSSE:   # s115 - Posse: so a data (sem peso)
                pendentes.append((l, nova_data, None))
                continue
            if tipo in TIPOS_COM_DESTINO:   # Transferencia e Venda: peso opcional (em branco = mantem), sem Peso Minimo
                peso_txt = str(a.get('peso', '') or '').strip()
                if not peso_txt:
                    pendentes.append((l, nova_data, None))
                    continue
                peso = _ler_decimal(peso_txt)
                if peso is None or peso <= 0:
                    return jsonify({'erro': f'SISBOV {l.sisbov}: informe o peso em quilos.'}), 400
                if peso > PESO_MAXIMO:
                    return jsonify({'erro': f'SISBOV {l.sisbov}: peso acima de {_formatar_kg(PESO_MAXIMO)} kg. Confira o valor.'}), 400
                pendentes.append((l, nova_data, peso.quantize(Decimal('0.01'))))
                continue
            peso = _ler_decimal(a.get('peso', ''))
            if peso is None or peso <= 0:
                return jsonify({'erro': f'SISBOV {l.sisbov}: informe o peso em quilos.'}), 400
            if peso < PESO_MINIMO_PADRAO:
                return jsonify({'erro': f'SISBOV {l.sisbov}: peso incorreto, verifique.'}), 400
            if peso > PESO_MAXIMO:
                return jsonify({'erro': f'SISBOV {l.sisbov}: peso acima de {_formatar_kg(PESO_MAXIMO)} kg. Confira o valor.'}), 400
            pendentes.append((l, nova_data, peso.quantize(Decimal('0.01'))))

        total = len(pendentes)
        id_operacao = registrar_operacao(
            db, id_usuario=session['usuario_id'], id_propriedade=int(id_propriedade),
            modulo='saida_correcao',
            descricao=f'Correção do embarque: {total} animal(is)')
        for l, nova_data, peso in pendentes:
            antes, depois = {}, {}
            if l.data_embarque != nova_data:
                antes['data_embarque'] = l.data_embarque.isoformat() if l.data_embarque else None
                depois['data_embarque'] = nova_data.isoformat()
            if peso is not None and l.peso_saida != peso:
                antes['peso_saida'] = str(l.peso_saida) if l.peso_saida is not None else None
                depois['peso_saida'] = str(peso)
            l.data_embarque = nova_data
            if peso is not None:
                l.peso_saida = peso
            if depois:
                registrar_item(db, id_operacao, 'tb_2020_embarque', l.id, 'UPDATE', antes, depois)
        db.commit()

    return jsonify({'ok': True, 'total': total})

# -------------------------------------------------------
# POST .../correcao/liberar - Sessao 107: LIBERA animais do embarque (apaga a leitura em aberto).
# So animais sem GTA vinculada e sem Comunicado. Tudo ou nada. Grava Log (so historico, nao se desfaz:
# para voltar, le-se o animal de novo).
# -------------------------------------------------------
@saida_consulta.route('/produtor/saida-consulta/correcao/liberar', methods=['POST'])
def correcao_liberar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    atual = _ler_iso(dados.get('data', ''))
    if not atual:
        return jsonify({'erro': 'Data do embarque inválida.'}), 400
    tipo, dest, ok_tipo = _ler_tipo_dest(dados)
    if not ok_tipo:
        return jsonify({'erro': 'Destino da Transferência inválido.'}), 400
    try:
        ids = sorted({int(x) for x in (dados.get('ids') or [])})
    except (TypeError, ValueError):
        return jsonify({'erro': 'Seleção inválida.'}), 400
    if not ids:
        return jsonify({'erro': 'Marque pelo menos um animal.'}), 400

    voltar = f'{URL_LISTA}?id_propriedade={int(id_propriedade)}'
    with get_db_produtor(session['id_produtor']) as db:
        linhas = db.query(Embarque).filter(
            *_filtro_abertas(id_propriedade, tipo, dest), Embarque.data_embarque == atual,
            Embarque.id.in_(ids)).all()
        if len(linhas) != len(ids):
            return jsonify({'erro': 'Algum animal não está mais neste embarque (talvez já tenha Comunicado). Recarregue a tela.'}), 400
        ligado = next((l for l in linhas if l.id_gta is not None), None)
        if ligado is not None:
            return jsonify({'erro': f'SISBOV {ligado.sisbov}: está ligado a uma GTA. Desvincule a GTA (Vincular GTA / Embarque) antes de liberar.'}), 400

        total = len(linhas)
        id_operacao = registrar_operacao(
            db, id_usuario=session['usuario_id'], id_propriedade=int(id_propriedade),
            modulo='saida_liberar',
            descricao=f'Animais liberados do embarque de {_data_br(atual)} ({ROTULO_SAIDA_TXT.get(tipo, "Abate")}): {total} animal(is)')
        for l in linhas:
            sexo = getattr(l.sexo, 'value', l.sexo)
            registrar_item(db, id_operacao, 'tb_2020_embarque', l.id, 'DELETE', {
                'sisbov': l.sisbov, 'manejo': l.manejo, 'rfid': l.rfid,
                'sexo': str(sexo) if sexo is not None else None,
                'tipo_saida': l.tipo_saida,
                'data_embarque': l.data_embarque.isoformat() if l.data_embarque else None,
            }, None)
            db.delete(l)
        db.flush()
        restantes = db.query(func.count(Embarque.id)).filter(
            *_filtro_abertas(id_propriedade, tipo, dest), Embarque.data_embarque == atual).scalar()
        db.commit()

    url = voltar if not restantes else f'/produtor/saida-consulta/correcao?id_propriedade={int(id_propriedade)}&data={atual.strftime("%Y-%m-%d")}{_qs_tipo(tipo, dest)}'
    return jsonify({'ok': True, 'total': total, 'restantes': int(restantes), 'url': url})


# =========================================================
# FIM DE ARQUIVO: backend\routers\saida_consulta.py
# =========================================================
