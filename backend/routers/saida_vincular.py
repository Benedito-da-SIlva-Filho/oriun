# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\saida_vincular.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-19 16:50 -03
# ATUALIZADO EM: 2026-11-10 12:43 -03
# VERSAO: 1.10.0
# v1.10.0: Sessao 120 (2026-11-10 12:43 -03) - Depois de vincular, o botao principal da Caixa de Sucesso e GERAR COMUNICADO (vai direto); "Vincular outra GTA" so aparece se ainda houver leitura sem GTA (Regra de Ouro #64). REVERSAO: .bak_antes_s120_vincular_fluxo.
# v1.9.1: Sessao 119 (2026-11-09 19:35 -03) - "Ver GTAs ja vinculadas": UMA linha por GTA (antes: uma por GTA e Data de Embarque, e a DTA da Posse com leituras de duas datas aparecia em 2 linhas). Datas juntas e animais somados; so a tela, o Desvincular ja solta a GTA inteira. REVERSAO: .bak_antes_s119_vinculadas.
# v1.8.1: Sessao 118 (2026-11-08 14:40 -03) - Vincular filtrado pelo tipo da aba. REVERSAO: .bak_antes_s118_raca
# v1.9.0: Sessao 115 (2026-11-05 18:55 -03) - Posse: a DTA e atendida por leituras em aberto de qualquer data dentro da validade dela (idade pela data de leitura de cada animal; Data de Saida >= ultima leitura). REVERSAO: .bak_antes_s115_validade.
# v1.8.0: Sessao 115 (2026-11-05 18:20 -03) - Vincular aceita DTA de ALTERACAO DE POSSE (tipo POSSE: datas pendentes, GTAs, conferencia por sexo/idade, vincular, desvincular). REVERSAO: .bak_antes_s115_vincular_posse.
#
# DESCRICAO:
#     Vincular GTA / Embarque (Sessao 100) - liga uma GTA de SAIDA (Abate)
#     aos animais lidos no brete (tb_2020_embarque), como o Vincular GTA da
#     Entrada faz com a Brincagem. Abre pelo botao "Vincular GTA" da linha da
#     Data Embarque, na Consulta Embarque (saida_consulta).
#
#     REGRAS FECHADAS COM O BENEDITO (19/10/2026):
#       - O Salvar so LIGA o animal a GTA (id_gta). NAO da baixa: o animal so
#         sai da tb_2001 quando o Comunicado de Saida for gerado.
#       - Uma Data Embarque pode ter mais animais do que a GTA pede (varios
#         caminhoes): a tela MARCA SOZINHA a quantidade de cada categoria
#         (sexo x faixa de idade) da GTA, pelos MENORES SISBOVs; os que sobram
#         ficam livres para a proxima GTA. O usuario troca pela caixinha.
#       - FALTANDO animal em alguma categoria: NAO deixa vincular. A tela
#         informa quantos animais e de quais faixas (ERAS) faltam. Por isso
#         nao existe GTA "meio vinculada": ou vincula completa, ou nao vincula.
#       - A faixa de idade e calculada pela DATA EMBARQUE (mesma conta da
#         Consulta Embarque), nunca pela Data de Saida.
#       - DATA DE SAIDA: OBRIGATORIA, digitada nesta tela (pode ser depois da
#         Data Embarque). Nao pode ser anterior a Data Embarque e precisa
#         estar entre a emissao e a validade da GTA. Fica gravada na GTA, no
#         coluna propria data_saida da tb_4001_gta (v1.1.0; na v1.0.0 usava
#         data_entrega). Exige o script Tabelas\alter_tb_4001_gta_data_saida_s100.sql.
#       - DESVINCULAR: desfaz o vinculo enquanto o Comunicado nao foi gerado
#         (animais voltam a ficar livres e a Data de Saida da GTA e apagada).
#       - Ao vincular, o id_frigorifico do animal recebe o da GTA.
#
#     ROTAS (todas em /produtor/saida-vincular/):
#       iniciar      - escolhe a Propriedade (se precisar) e abre embarques.
#       embarques    - datas de embarque pendentes de GTA.
#       vinculadas   - GTAs ja vinculadas (sem Comunicado), com o botao Desvincular.
#       gtas         - GTAs de saida disponiveis + as ja vinculadas a esta data.
#       conferencia  - GTA escolhida: Data de Saida e animais marcados por categoria.
#       salvar       - POST JSON: valida tudo de novo no servidor e vincula.
#       desvincular  - POST JSON: desfaz o vinculo da GTA.
#
#     ASSUMIDO (Benedito ainda nao confirmou): vincular e desvincular NAO gravam
#     Log de Operacoes por enquanto.
#
#     v1.0.0: Criacao (Sessao 100).
#     v1.1.0: Sessao 100 (19/10/2026, 17:05 -03) - Data de Saida passa a ser gravada na coluna propria data_saida
#             (antes: data_entrega).
#     v1.2.0: Sessao 100 (19/10/2026, 17:40 -03) - Entrada propria do Hub: rotas iniciar (escolhe a Propriedade)
#             e embarques (so datas com animais SEM GTA; se houver uma so, abre direto a lista de GTAs).
#             Voltar da lista de GTAs vai para embarques (ou para o Hub se so houver uma data).
#     v1.3.0: Sessao 100 (19/10/2026, 18:20 -03) - Log de Operacoes no Vincular e no Desvincular (modulo saida_vincular, so historico) e nova tela
#             "GTAs ja vinculadas" (rota vinculadas): datas com GTA vinculada e sem Comunicado, com o botao Desvincular.
#             Botao "Ver GTAs ja vinculadas" no topo das telas embarques e gtas.
#     v1.4.0: Sessao 103 (22/10/2026, 16:40 -03) - Caixa de Sucesso (utils/caixa_sucesso.py) no Vincular e no Desvincular: depois de gravar o usuario
#             ve 'GTA vinculada com sucesso!' (GTA, animais por categoria, Data de Saida, frigorifico) ou 'GTA desvinculada.' em vez do banner.
#             Novas rotas GET /produtor/saida-vincular/concluida e /desvinculada. Regras do vinculo nao mudaram.  REVERSAO: .bak_antes_caixa_pacoteB_s103.
#     REVERSAO: remover este arquivo e os templates saida_vincular_*.html; devolver
#     os .bak_antes_vincular_s100 de app.py, permissoes.py e saida_consulta_lista.html.
# =========================================================

from sqlalchemy import func
from sqlalchemy.orm import Session
from flask import Blueprint, render_template, request, redirect, session, jsonify

from backend.database import engine
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4001_gta_animais import GtaAnimal
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.models.tb_frigorificos import Frigorifico
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.saida_leitor import _formatar_kg
from backend.routers.saida_consulta import (
    _contexto_base, _propriedade_do_usuario, _negado, _data_br, _ler_iso, _ler_br,
    _faixa_em, _filtro_abertas, _nomes, URL_HUB,
)
from backend.utils.multitenant import get_db_produtor
from backend.utils.destino_transferencia import nomes_destinos_transfer
from backend.utils.especies import carregar_especies
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.caixa_sucesso import render_caixa_sucesso

saida_vincular = Blueprint('saida_vincular', __name__)

SENTIDO_SAIDA = 'SAIDA'
TIPO_MOVIMENTO_ABATE = 'ABATE'
TIPO_MOVIMENTO_TRANSFER = 'TRANSFERENCIA'   # v107 - GTA de Transferencia
TIPO_MOVIMENTO_VENDA = 'VENDA'             # s111 - GTA de Venda (destino = Parceiro, como na Transferencia)
TIPO_MOVIMENTO_POSSE = 'POSSE'             # s115 - DTA de Alteracao de Posse (destino = outro Produtor da mesma Propriedade)
TIPOS_GTA = (TIPO_MOVIMENTO_ABATE, TIPO_MOVIMENTO_TRANSFER, TIPO_MOVIMENTO_VENDA, TIPO_MOVIMENTO_POSSE)
TIPOS_COM_DESTINO = ('TRANSFER', 'VENDA', 'POSSE')   # tipos (tipo_saida) cujo destino vem da GTA (Parceiro + Propriedade)
MOVIMENTO_DO_TIPO = {'ABATE': TIPO_MOVIMENTO_ABATE, 'TRANSFER': TIPO_MOVIMENTO_TRANSFER, 'VENDA': TIPO_MOVIMENTO_VENDA, 'POSSE': TIPO_MOVIMENTO_POSSE}
ROTULO_DO_TIPO = {'ABATE': 'Abate', 'TRANSFER': 'Transferência', 'VENDA': 'Venda', 'POSSE': 'Alteração de Posse'}
ROTULO_DESTINO_DO_TIPO = {'ABATE': 'Frigorífico', 'TRANSFER': 'Destino', 'VENDA': 'Comprador', 'POSSE': 'Novo Produtor'}
ROTULO_DESTINO_LONGO = {'ABATE': 'Frigorífico', 'TRANSFER': 'Destino (Transferência)', 'VENDA': 'Comprador (Venda)', 'POSSE': 'Novo Produtor (Alteração de Posse)'}


def _tipo_saida_da_gta(tipo_movimento):
    """tipo_saida das leituras (tb_2020) que esta GTA pode receber: a GTA define o tipo (Abate, Transferencia ou Venda)."""
    if tipo_movimento == TIPO_MOVIMENTO_TRANSFER:
        return 'TRANSFER'
    if tipo_movimento == TIPO_MOVIMENTO_POSSE:
        return 'POSSE'
    return 'VENDA' if tipo_movimento == TIPO_MOVIMENTO_VENDA else 'ABATE'


def _tipo_da_url(texto):
    t = str(texto or '').strip().upper()
    return t if t in TIPOS_COM_DESTINO else 'ABATE'


def _tipo_filtro(texto):   # s118 - vazio = todos
    t = str(texto or '').strip().upper()
    return t if t in ('ABATE', 'TRANSFER', 'VENDA', 'POSSE') else ''


def _qs_filtro():
    f = _tipo_filtro(request.args.get('tipo'))
    return f'&tipo={f}' if f else ''


def _qs_tipo(tipo):
    return f'&tipo={tipo}' if tipo in TIPOS_COM_DESTINO else ''
URL_GTAS = '/produtor/saida-vincular/gtas'
URL_INICIAR = '/produtor/saida-vincular/iniciar'
URL_EMBARQUES = '/produtor/saida-vincular/embarques'
URL_VINCULADAS = '/produtor/saida-vincular/vinculadas'
URL_CONFERENCIA = '/produtor/saida-vincular/conferencia'
URL_CONCLUIDA = '/produtor/saida-vincular/concluida'
URL_GERAR_COMUNICADO = '/produtor/saida-comunicado/conferencia'   # s120 - destino direto depois de vincular
URL_DESVINCULADA = '/produtor/saida-vincular/desvinculada'

ROTULO_SEXO = {'MACHO': 'Macho', 'FEMEA': 'Fêmea'}


# =========================================================
# BLOCO 1 - Funcoes PURAS (sem banco, sem Flask): categorias, marcacao
# automatica e validacao da Data de Saida.
# =========================================================

def _norm_faixa(texto):
    """'Zero a 04 Meses' e 'ZERO A 04 MESES' viram a mesma chave."""
    return ''.join((texto or '').upper().split())


def _chave(especie, sexo, faixa):
    """Chave de categoria: (especie, sexo, faixa normalizada)."""
    return ((especie or '').upper(), (sexo or '').upper(), _norm_faixa(faixa))


def _rotulo_categoria(sexo, faixa):
    """Texto para a tela: 'Macho · 13 a 24 Meses'."""
    return f"{ROTULO_SEXO.get((sexo or '').upper(), sexo or '-')} · {faixa}"


def _necessidades(linhas_gta):
    """
    Categorias que a GTA pede. Recebe objetos com especie, sexo, idade_meses e
    quantidade. Linhas repetidas da mesma categoria se somam.
    Devolve dict chave -> {'sexo','faixa','qtd','rotulo'}, na ordem da GTA.
    """
    nec = {}
    for l in linhas_gta:
        k = _chave(l.especie, l.sexo, l.idade_meses)
        if k in nec:
            nec[k]['qtd'] += int(l.quantidade or 0)
        else:
            nec[k] = {
                'sexo': (l.sexo or '').upper(),
                'faixa': l.idade_meses,
                'qtd': int(l.quantidade or 0),
                'rotulo': _rotulo_categoria(l.sexo, l.idade_meses),
            }
    return nec


def _classificar_livres(leituras, faixas, data_embarque, codigo_por_id_especie):
    """
    Separa os animais LIVRES (sem GTA) por categoria, usando a idade NA Data
    Embarque. Animal sem nascimento / sem sexo / sem especie / com idade fora
    das faixas nao entra em categoria nenhuma (vai para 'sem_categoria').
    Devolve (por_chave, sem_categoria); cada lista ja vem por SISBOV crescente.
    """
    por_chave = {}
    sem_categoria = []
    for l in sorted(leituras, key=lambda x: x.sisbov or ''):
        faixa = _faixa_em(faixas, l.nascimento, data_embarque if data_embarque is not None else l.data_embarque)   # None = idade na data de leitura de cada animal (Posse)
        especie = codigo_por_id_especie.get(l.id_especie)
        animal = {
            'id': l.id,
            'sisbov': l.sisbov,
            'manejo': l.manejo or '',
            'sexo': ROTULO_SEXO.get(l.sexo, l.sexo or '-'),
            'nascimento': _data_br(l.nascimento),
            'faixa': faixa,
            'peso': _formatar_kg(l.peso_saida) if l.peso_saida is not None else '',
        }
        if faixa == '-' or not l.sexo or not especie:
            sem_categoria.append(animal)
            continue
        por_chave.setdefault(_chave(especie, l.sexo, faixa), []).append(animal)
    return por_chave, sem_categoria


def _marcar_automatico(nec, por_chave):
    """
    Marca, em cada categoria da GTA, a quantidade pedida pelos MENORES SISBOVs.
    Devolve (ids_marcados, faltas); 'faltas' lista cada categoria com animais
    insuficientes: pede, livres e quantos faltam.
    """
    marcados = set()
    faltas = []
    for k, n in nec.items():
        livres = por_chave.get(k, [])
        for a in livres[:n['qtd']]:
            marcados.add(a['id'])
        if len(livres) < n['qtd']:
            faltas.append({
                'rotulo': n['rotulo'],
                'pede': n['qtd'],
                'livres': len(livres),
                'faltam': n['qtd'] - len(livres),
            })
    return marcados, faltas


def _validar_data_saida(texto, data_embarque, emissao, validade):
    """Devolve (data, None) ou (None, mensagem). Obrigatoria."""
    if not (texto or '').strip():
        return None, 'Informe a Data de Saída (obrigatória).'
    d = _ler_br(texto)
    if d is None:
        return None, 'Data de Saída incorreta! Use o formato dd/mm/aaaa.'
    if d < data_embarque:
        return None, f'A Data de Saída não pode ser anterior à Data de Embarque ({_data_br(data_embarque)}).'
    if d < emissao or d > validade:
        return None, (f'A Data de Saída precisa estar dentro da validade da GTA '
                      f'({_data_br(emissao)} a {_data_br(validade)}).')
    return d, None


def _texto_faltas(faltas):
    """Mensagem unica com tudo que falta (para o servidor e para a tela)."""
    total = sum(f['faltam'] for f in faltas)
    partes = [f"{f['rotulo']}: a GTA pede {f['pede']}, há {f['livres']} livre(s) — faltam {f['faltam']}"
              for f in faltas]
    return f'Animais insuficientes para esta GTA: faltam {total} animal(is). ' + '; '.join(partes) + '.'


# =========================================================
# BLOCO 2 - Acesso ao banco (usado pelas rotas)
# =========================================================

def _gta_da_propriedade(db, id_propriedade, id_gta):
    """A GTA de saida (Abate ou Transferencia), da Propriedade, ainda sem Comunicado; ou None."""
    try:
        id_int = int(id_gta)
    except (TypeError, ValueError):
        return None
    return (
        db.query(Gta)
        .filter(
            Gta.id == id_int,
            Gta.id_propriedade == int(id_propriedade),
            Gta.sentido == SENTIDO_SAIDA,
            Gta.tipo_movimento.in_(TIPOS_GTA),
            Gta.numero_comunicado.is_(None),
        )
        .first()
    )


def _livres_da_data(db, id_propriedade, data_embarque, tipo='ABATE'):
    """Leituras abertas (sem Comunicado) da data, do tipo da GTA, que ainda nao tem GTA."""
    return (
        db.query(Embarque)
        .filter(*_filtro_abertas(id_propriedade, tipo),
                Embarque.data_embarque == data_embarque,
                Embarque.id_gta.is_(None))
        .order_by(Embarque.sisbov.asc())
        .all()
    )


def _livres_da_gta_posse(db, id_propriedade, gta):
    """s115 - ALTERACAO DE POSSE: leituras de Posse abertas, sem DTA, de QUALQUER data dentro da validade da DTA (emissao a validade)."""
    q = db.query(Embarque).filter(*_filtro_abertas(id_propriedade, 'POSSE'), Embarque.id_gta.is_(None))
    if gta.data_emissao:
        q = q.filter(Embarque.data_embarque >= gta.data_emissao)
    if gta.data_validade:
        q = q.filter(Embarque.data_embarque <= gta.data_validade)
    return q.order_by(Embarque.sisbov.asc()).all()


def _codigos_de_especie():
    return {e['id']: e['codigo'] for e in carregar_especies()}


def _nomes_frigorificos(ids):
    nomes = {}
    ids = {i for i in ids if i}
    if ids:
        with Session(engine) as dbp:
            for f in dbp.query(Frigorifico).filter(Frigorifico.id.in_(ids)).all():
                nomes[f.id] = f.nome
    return nomes


# =========================================================
# BLOCO 3 - Rotas
# =========================================================

# -------------------------------------------------------
# Datas de embarque pendentes (animais abertos, sem GTA)
# -------------------------------------------------------
def _datas_pendentes(db, id_propriedade):
    """Lista [(data, tipo, livres, total)], da mais recente para a mais antiga; so datas com livres > 0. Abate e Transferencia separados."""
    saida = []
    for tipo in ('ABATE', 'TRANSFER', 'VENDA', 'POSSE'):
        totais = dict(
            db.query(Embarque.data_embarque, func.count(Embarque.id))
            .filter(*_filtro_abertas(id_propriedade, tipo))
            .group_by(Embarque.data_embarque).all()
        )
        livres = (
            db.query(Embarque.data_embarque, func.count(Embarque.id))
            .filter(*_filtro_abertas(id_propriedade, tipo), Embarque.id_gta.is_(None))
            .group_by(Embarque.data_embarque).all()
        )
        saida += [(d, tipo, q, totais.get(d, q)) for d, q in livres]
    return sorted(saida, key=lambda x: x[0], reverse=True)


# -------------------------------------------------------
# GET /produtor/saida-vincular/iniciar
# -------------------------------------------------------
@saida_vincular.route('/produtor/saida-vincular/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista,
            erro=erro,
            titulo='Vincular GTA / Embarque — Selecionar Propriedade',
            proximo=URL_EMBARQUES + (f'?tipo={_tipo_filtro(request.args.get("tipo"))}' if _tipo_filtro(request.args.get('tipo')) else ''),
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
        return redirect(f'{URL_EMBARQUES}?id_propriedade={par_em_uso.id_propriedade}{_qs_filtro()}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_EMBARQUES}?id_propriedade={par.id_propriedade}{_qs_filtro()}')

    return _tela_selecionar(pares, None)


# -------------------------------------------------------
# GET /produtor/saida-vincular/embarques - so os pendentes de GTA.
# -------------------------------------------------------
# -------------------------------------------------------
# v1.6.0 - GTAs de Saida ainda NAO vinculadas (sem Comunicado), por tipo, mais recentes primeiro.
# Devolve {tipo: [{id, numero, destino}]}.
# -------------------------------------------------------
def _gtas_disponiveis(db, id_propriedade, tipos):
    resultado = {}
    for tipo in tipos:
        todas = (
            db.query(Gta)
            .filter(Gta.id_propriedade == int(id_propriedade),
                    Gta.sentido == SENTIDO_SAIDA,
                    Gta.tipo_movimento == MOVIMENTO_DO_TIPO.get(tipo, TIPO_MOVIMENTO_ABATE),
                    Gta.numero_comunicado.is_(None))
            .order_by(Gta.data_emissao.desc(), Gta.numero_gta_completo.desc())
            .all()
        )
        ids = [g.id for g in todas]
        ja_vinculadas = set()
        if ids:
            ja_vinculadas = {r[0] for r in db.query(Embarque.id_gta).filter(Embarque.id_gta.in_(ids)).distinct().all()}
        livres = [g for g in todas if g.id not in ja_vinculadas]
        if tipo in TIPOS_COM_DESTINO:
            nomes = nomes_destinos_transfer(db, [g.id_parceiro_propriedade for g in livres])
            destino = {g.id: nomes.get(g.id_parceiro_propriedade, '-') for g in livres}
        else:
            nomes = _nomes_frigorificos(g.id_frigorifico for g in livres)
            destino = {g.id: nomes.get(g.id_frigorifico, '-') for g in livres}
        resultado[tipo] = [{'id': g.id, 'numero': g.numero_gta_completo, 'destino': destino[g.id]} for g in livres]
    return resultado


@saida_vincular.route('/produtor/saida-vincular/embarques')
def embarques():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']

    with get_db_produtor(id_produtor) as db:
        pendentes = _datas_pendentes(db, id_propriedade)
        if _tipo_filtro(request.args.get('tipo')):   # s118 - cada aba so ve o seu tipo
            pendentes = [x for x in pendentes if x[1] == _tipo_filtro(request.args.get('tipo'))]
        gtas_por_tipo = _gtas_disponiveis(db, id_propriedade, {t for _d, t, _l, _t in pendentes})

    # v1.6.0 - uma linha por GTA ainda nao vinculada, do mesmo tipo do embarque (Vincular vai direto a conferencia)
    linhas = [{
        'iso': d.strftime('%Y-%m-%d'),
        'data': _data_br(d),
        'tipo': tipo,
        'tipo_rotulo': ROTULO_DO_TIPO.get(tipo, 'Abate'),
        'qs': _qs_tipo(tipo),
        'livres': livres,
        'total': total,
        'gtas': gtas_por_tipo.get(tipo, []),
        'url_cadastrar': f'/produtor/gta-saida/nova?id_propriedade={int(id_propriedade)}' + _qs_tipo(tipo),
    } for d, tipo, livres, total in pendentes]

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_vincular_embarques.html',
        embarques=linhas,
        id_propriedade=int(id_propriedade),
        url_vinculadas=f'{URL_VINCULADAS}?id_propriedade={int(id_propriedade)}',
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        url_hub=URL_HUB,
        **_contexto_base(),
    )


# -------------------------------------------------------
# GET /produtor/saida-vincular/vinculadas - GTAs ja vinculadas (sem Comunicado),
# uma linha por GTA e Data de Embarque, com o botao Desvincular.
# -------------------------------------------------------
@saida_vincular.route('/produtor/saida-vincular/vinculadas')
def vinculadas():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']

    with get_db_produtor(id_produtor) as db:
        grupos = (
            db.query(Embarque.id_gta, Embarque.data_embarque, func.count(Embarque.id))
            .filter(Embarque.id_propriedade == int(id_propriedade), Embarque.tipo_saida.in_(['ABATE', 'TRANSFER', 'VENDA', 'POSSE']),
                    Embarque.sts == False, Embarque.id_gta.isnot(None))   # noqa: E712
            .group_by(Embarque.id_gta, Embarque.data_embarque)
            .order_by(Embarque.data_embarque.desc()).all()
        )
        ids = {g[0] for g in grupos}
        gtas_por_id = {}
        if ids:
            gtas_por_id = {g.id: g for g in db.query(Gta).filter(
                Gta.id.in_(ids), Gta.id_propriedade == int(id_propriedade),
                Gta.sentido == SENTIDO_SAIDA, Gta.tipo_movimento.in_(TIPOS_GTA),
                Gta.numero_comunicado.is_(None)).all()}
        destinos_transfer = nomes_destinos_transfer(db, [g.id_parceiro_propriedade for g in gtas_por_id.values()])
        brutas = []
        for id_gta, d, qtd in grupos:
            g = gtas_por_id.get(id_gta)
            if g is None:
                continue
            brutas.append({
                'id': g.id,
                'numero': g.numero_gta_completo,
                'id_frigorifico': g.id_frigorifico,
                'transfer': g.tipo_movimento in (TIPO_MOVIMENTO_TRANSFER, TIPO_MOVIMENTO_VENDA, TIPO_MOVIMENTO_POSSE),
                'destino_transfer': destinos_transfer.get(g.id_parceiro_propriedade, '-'),
                'data_saida': _data_br(g.data_saida) if g.data_saida else '-',
                'iso': d.strftime('%Y-%m-%d'),
                'data': _data_br(d),
                'animais': qtd,
            })

    # ---- v1.9.1 - UMA linha por GTA: junta as Datas de Embarque (ex.: "05/11/2026 e 06/11/2026") e soma os animais. So a tela; o Desvincular solta a GTA inteira ----
    unidas = {}
    for b in brutas:
        u = unidas.get(b['id'])
        if u is None:
            b['_datas'] = [(b['iso'], b['data'])]
            unidas[b['id']] = b
        else:
            u['_datas'].append((b['iso'], b['data']))
            u['animais'] += b['animais']
    brutas = list(unidas.values())
    for b in brutas:
        datas = sorted(b.pop('_datas'))
        textos = [d for _iso, d in datas]
        b['data'] = ' e '.join(textos) if len(textos) == 2 else ', '.join(textos)
        b['iso'] = datas[0][0]

    nomes = _nomes_frigorificos(b['id_frigorifico'] for b in brutas)
    for b in brutas:
        b['frigorifico'] = b['destino_transfer'] if b['transfer'] else nomes.get(b['id_frigorifico'], '-')

    mensagem = 'GTA desvinculada. Os animais voltaram a ficar livres.' if request.args.get('des') else None
    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_vincular_vinculadas.html',
        vinculadas=brutas,
        mensagem=mensagem,
        id_propriedade=int(id_propriedade),
        url_embarques=f'{URL_EMBARQUES}?id_propriedade={int(id_propriedade)}',
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        url_hub=URL_HUB,
        **_contexto_base(),
    )


# -------------------------------------------------------
# GET /produtor/saida-vincular/gtas - GTAs de saida para escolher.
# -------------------------------------------------------
@saida_vincular.route('/produtor/saida-vincular/gtas')
def gtas():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    data = _ler_iso(request.args.get('data', ''))
    tipo = _tipo_da_url(request.args.get('tipo'))
    url_embarques = f'{URL_EMBARQUES}?id_propriedade={int(id_propriedade)}'
    if not data:
        return redirect(url_embarques)
    id_produtor = session['id_produtor']
    voltar = url_embarques

    with get_db_produtor(id_produtor) as db:
        total_data = db.query(func.count(Embarque.id)).filter(
            *_filtro_abertas(id_propriedade, tipo), Embarque.data_embarque == data).scalar()
        if not total_data:
            return redirect(url_embarques)
        livres = db.query(func.count(Embarque.id)).filter(
            *_filtro_abertas(id_propriedade, tipo), Embarque.data_embarque == data,
            Embarque.id_gta.is_(None)).scalar()

        todas = (
            db.query(Gta)
            .filter(Gta.id_propriedade == int(id_propriedade),
                    Gta.sentido == SENTIDO_SAIDA,
                    Gta.tipo_movimento == MOVIMENTO_DO_TIPO.get(tipo, TIPO_MOVIMENTO_ABATE),
                    Gta.numero_comunicado.is_(None))
            .order_by(Gta.data_emissao.desc(), Gta.numero_gta_completo.desc())
            .all()
        )
        ids = [g.id for g in todas]
        vinculos = {}   # id_gta -> {data_embarque: qtd}
        categorias = {}  # id_gta -> texto das categorias
        if ids:
            for id_gta, d, qtd in (
                db.query(Embarque.id_gta, Embarque.data_embarque, func.count(Embarque.id))
                .filter(Embarque.id_gta.in_(ids))
                .group_by(Embarque.id_gta, Embarque.data_embarque).all()
            ):
                vinculos.setdefault(id_gta, {})[d] = qtd
            linhas = db.query(GtaAnimal).filter(GtaAnimal.id_gta.in_(ids)).all()
            for id_gta in ids:
                nec = _necessidades([l for l in linhas if l.id_gta == id_gta])
                categorias[id_gta] = '; '.join(f"{n['qtd']} {n['rotulo']}" for n in nec.values())

        destinos_transfer = nomes_destinos_transfer(db, [g.id_parceiro_propriedade for g in todas])
        brutas = [{
            'id': g.id,
            'numero': g.numero_gta_completo,
            'emissao': _data_br(g.data_emissao),
            'validade': _data_br(g.data_validade),
            'qtde': g.qtde_animais,
            'id_frigorifico': g.id_frigorifico,
            'destino_transfer': destinos_transfer.get(g.id_parceiro_propriedade, '-'),
            'data_saida': _data_br(g.data_saida) if g.data_saida else '-',
            'categorias': categorias.get(g.id, ''),
            'vinculos': vinculos.get(g.id, {}),
        } for g in todas]

    nomes = _nomes_frigorificos(b['id_frigorifico'] for b in brutas)
    disponiveis = []
    vinculadas = []
    for b in brutas:
        b['frigorifico'] = b['destino_transfer'] if tipo in TIPOS_COM_DESTINO else nomes.get(b['id_frigorifico'], '-')
        if not b['vinculos']:
            disponiveis.append(b)
        elif data in b['vinculos']:
            b['animais'] = b['vinculos'][data]
            vinculadas.append(b)

    # Mensagens de retorno (vem so o ID da GTA; o texto e montado aqui)
    mensagem = None
    try:
        id_ok = int(request.args.get('ok', '0'))
        id_des = int(request.args.get('des', '0'))
    except ValueError:
        id_ok, id_des = 0, 0
    for b in vinculadas:
        if b['id'] == id_ok:
            mensagem = (f"GTA {b['numero']} vinculada a {b['animais']} animal(is). "
                        f"Data de Saída: {b['data_saida']}.")
    for b in disponiveis:
        if b['id'] == id_des:
            mensagem = f"GTA {b['numero']} desvinculada. Os animais voltaram a ficar livres."

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_vincular_gtas.html',
        id_propriedade=int(id_propriedade),
        tipo_rotulo=ROTULO_DO_TIPO.get(tipo, 'Abate'),
        destino_rotulo=ROTULO_DESTINO_DO_TIPO.get(tipo, 'Frigorífico'),
        iso=data.strftime('%Y-%m-%d'),
        data_embarque=_data_br(data),
        total_data=total_data,
        livres=livres,
        disponiveis=disponiveis,
        vinculadas=vinculadas,
        mensagem=mensagem,
        url_vinculadas=f'{URL_VINCULADAS}?id_propriedade={int(id_propriedade)}',
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        url_voltar=voltar,
        **_contexto_base(),
    )


# -------------------------------------------------------
# GET /produtor/saida-vincular/conferencia - animais por categoria da GTA.
# -------------------------------------------------------
@saida_vincular.route('/produtor/saida-vincular/conferencia')
def conferencia():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    data = _ler_iso(request.args.get('data', ''))
    voltar_consulta = f'{URL_EMBARQUES}?id_propriedade={int(id_propriedade)}'
    if not data:
        return redirect(voltar_consulta)
    iso = data.strftime('%Y-%m-%d')
    voltar = voltar_consulta   # v1.6.1 - Escolher outra GTA / Cancelar voltam para a lista de embarques
    id_produtor = session['id_produtor']
    codigos = _codigos_de_especie()

    with get_db_produtor(id_produtor) as db:
        gta = _gta_da_propriedade(db, id_propriedade, request.args.get('id_gta', ''))
        if gta is None:
            return redirect(voltar)
        tipo_leitura = _tipo_saida_da_gta(gta.tipo_movimento)
        ja_vinculada = db.query(func.count(Embarque.id)).filter(Embarque.id_gta == gta.id).scalar()
        if ja_vinculada:
            return redirect(voltar)

        faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
        nec = _necessidades(db.query(GtaAnimal).filter(GtaAnimal.id_gta == gta.id).all())
        if tipo_leitura == 'POSSE':   # s115 - todas as leituras dentro da validade da DTA; idade na data de leitura de cada animal
            por_chave, sem_categoria = _classificar_livres(_livres_da_gta_posse(db, id_propriedade, gta), faixas, None, codigos)
        else:
            por_chave, sem_categoria = _classificar_livres(
                _livres_da_data(db, id_propriedade, data, tipo_leitura), faixas, data, codigos)
        marcados, faltas = _marcar_automatico(nec, por_chave)

        dados_gta = {
            'id': gta.id,
            'numero': gta.numero_gta_completo,
            'emissao': _data_br(gta.data_emissao),
            'validade': _data_br(gta.data_validade),
            'qtde': gta.qtde_animais,
            'id_frigorifico': gta.id_frigorifico,
            'transfer': tipo_leitura in TIPOS_COM_DESTINO,
            'destino_transfer': nomes_destinos_transfer(db, [gta.id_parceiro_propriedade]).get(gta.id_parceiro_propriedade, '-'),
        }

    dados_gta['frigorifico'] = (dados_gta['destino_transfer'] if dados_gta['transfer']
                                else _nomes_frigorificos([dados_gta['id_frigorifico']]).get(dados_gta['id_frigorifico'], '-'))
    dados_gta['destino_rotulo'] = ROTULO_DESTINO_LONGO.get(tipo_leitura, 'Frigorífico')

    categorias = []
    for indice, (k, n) in enumerate(nec.items()):
        livres_cat = por_chave.get(k, [])
        categorias.append({
            'indice': indice,
            'rotulo': n['rotulo'],
            'pede': n['qtd'],
            'livres': len(livres_cat),
            'animais': [dict(a, marcado=(a['id'] in marcados)) for a in livres_cat],
        })
    nas_categorias = {k for k in nec}
    fora_da_gta = sum(len(v) for k, v in por_chave.items() if k not in nas_categorias)

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_vincular_conferencia.html',
        id_propriedade=int(id_propriedade),
        iso=iso,
        data_embarque=_data_br(data),
        gta=dados_gta,
        categorias=categorias,
        faltas=faltas,
        texto_faltas=_texto_faltas(faltas) if faltas else '',
        sem_categoria=len(sem_categoria),
        fora_da_gta=fora_da_gta,
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        url_voltar=voltar,
        **_contexto_base(),
    )


# -------------------------------------------------------
# POST /produtor/saida-vincular/salvar - valida de novo e vincula.
# Tudo ou nada. NAO da baixa (isso e do Comunicado).
# -------------------------------------------------------
@saida_vincular.route('/produtor/saida-vincular/salvar', methods=['POST'])
def salvar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    data = _ler_iso(dados.get('data', ''))
    if not data:
        return jsonify({'erro': 'Data de Embarque inválida.'}), 400
    try:
        ids_marcados = {int(i) for i in (dados.get('ids') or [])}
    except (TypeError, ValueError):
        return jsonify({'erro': 'Lista de animais inválida.'}), 400
    if not ids_marcados:
        return jsonify({'erro': 'Nenhum animal marcado.'}), 400
    codigos = _codigos_de_especie()

    with get_db_produtor(session['id_produtor']) as db:
        gta = _gta_da_propriedade(db, id_propriedade, dados.get('id_gta', ''))
        if gta is None:
            return jsonify({'erro': 'GTA não encontrada ou já com Comunicado. Recarregue a tela.'}), 400
        if db.query(func.count(Embarque.id)).filter(Embarque.id_gta == gta.id).scalar():
            return jsonify({'erro': 'Esta GTA já está vinculada a animais. Recarregue a tela.'}), 400

        posse = (_tipo_saida_da_gta(gta.tipo_movimento) == 'POSSE')
        livres_posse = _livres_da_gta_posse(db, id_propriedade, gta) if posse else None
        data_ref = data
        if posse:   # s115 - a Data de Saida nao pode ser anterior a ULTIMA leitura usada
            data_ref = max([l.data_embarque for l in livres_posse if l.id in ids_marcados] or [data])
        data_saida, erro = _validar_data_saida(
            dados.get('data_saida', ''), data_ref, gta.data_emissao, gta.data_validade)
        if erro:
            return jsonify({'erro': erro}), 400

        faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
        nec = _necessidades(db.query(GtaAnimal).filter(GtaAnimal.id_gta == gta.id).all())
        tipo_leitura = _tipo_saida_da_gta(gta.tipo_movimento)
        livres = livres_posse if posse else _livres_da_data(db, id_propriedade, data, tipo_leitura)
        por_chave, _sem = _classificar_livres(livres, faixas, None if posse else data, codigos)

        # Cada animal marcado precisa estar livre, na data, e ter categoria.
        chave_por_id = {a['id']: k for k, lista in por_chave.items() for a in lista}
        for i in ids_marcados:
            if i not in chave_por_id:
                return jsonify({'erro': 'Algum animal marcado não está mais livre ou não tem categoria. Recarregue a tela.'}), 400

        # Contagem marcada por categoria x o que a GTA pede (exato).
        contagem = {}
        for i in ids_marcados:
            k = chave_por_id[i]
            contagem[k] = contagem.get(k, 0) + 1
        for k, n in nec.items():
            marcados_cat = contagem.get(k, 0)
            if marcados_cat != n['qtd']:
                return jsonify({'erro': (f"{n['rotulo']}: a GTA pede {n['qtd']} animal(is) e você marcou "
                                         f"{marcados_cat}. Marque exatamente {n['qtd']}.")}), 400
        for k in contagem:
            if k not in nec:
                return jsonify({'erro': 'Há animal marcado de uma categoria que não está na GTA.'}), 400

        linhas = [l for l in livres if l.id in ids_marcados]
        if len(linhas) != len(ids_marcados):
            return jsonify({'erro': 'Algum animal marcado não está mais livre. Recarregue a tela.'}), 400

        total = len(linhas)
        id_operacao = registrar_operacao(
            db, id_usuario=session['usuario_id'], id_propriedade=int(id_propriedade),
            modulo='saida_vincular',
            descricao=(f'Vínculo da GTA {gta.numero_gta_completo} a {total} animal(is) do embarque '
                       f'de {_data_br(data)} — Data de Saída {_data_br(data_saida)}'))
        for l in linhas:
            antes = {'id_gta': l.id_gta, 'id_frigorifico': l.id_frigorifico}
            l.id_gta = gta.id
            l.id_frigorifico = gta.id_frigorifico
            registrar_item(db, id_operacao, 'tb_2020_embarque', l.id, 'UPDATE', antes,
                           {'id_gta': gta.id, 'id_frigorifico': gta.id_frigorifico})
        antes_gta = {'data_saida': gta.data_saida.isoformat() if gta.data_saida else None}
        gta.data_saida = data_saida
        registrar_item(db, id_operacao, 'tb_4001_gta', gta.id, 'UPDATE', antes_gta,
                       {'data_saida': data_saida.isoformat()})
        id_gta_ok = gta.id
        resumo_caixa = {
            'numero': gta.numero_gta_completo, 'total': total, 'data_embarque': _data_br(data), 'data_saida': _data_br(data_saida),
            'id_frigorifico': gta.id_frigorifico,
            'categorias': [f"{n['qtd']} {n['rotulo']}" for n in nec.values()],
            'transfer': tipo_leitura in TIPOS_COM_DESTINO,
            'destino_transfer': nomes_destinos_transfer(db, [gta.id_parceiro_propriedade]).get(gta.id_parceiro_propriedade, '-'),
        }
        db.commit()

    if resumo_caixa['transfer']:
        resumo_caixa['frigorifico'] = resumo_caixa['destino_transfer']
        resumo_caixa['destino_rotulo'] = ROTULO_DESTINO_LONGO.get(tipo_leitura, 'Destino (Transferência)')
    else:
        resumo_caixa['frigorifico'] = _nomes_frigorificos([resumo_caixa['id_frigorifico']]).get(resumo_caixa['id_frigorifico'], '-')
        resumo_caixa['destino_rotulo'] = 'Frigorífico'
    session['caixa_vincular'] = resumo_caixa
    return jsonify({
        'ok': True,
        'total': total,
        'url': f'{URL_CONCLUIDA}?id_propriedade={int(id_propriedade)}&data={data.strftime("%Y-%m-%d")}{_qs_tipo(tipo_leitura)}',
    })


# -------------------------------------------------------
# POST /produtor/saida-vincular/desvincular - desfaz o vinculo da GTA.
# So enquanto nenhum animal teve Comunicado.
# -------------------------------------------------------
@saida_vincular.route('/produtor/saida-vincular/desvincular', methods=['POST'])
def desvincular():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    data = _ler_iso(dados.get('data', ''))
    if not data:
        return jsonify({'erro': 'Data de Embarque inválida.'}), 400

    with get_db_produtor(session['id_produtor']) as db:
        gta = _gta_da_propriedade(db, id_propriedade, dados.get('id_gta', ''))
        if gta is None:
            return jsonify({'erro': 'GTA não encontrada ou já com Comunicado.'}), 400
        linhas = db.query(Embarque).filter(Embarque.id_gta == gta.id).all()
        if not linhas:
            return jsonify({'erro': 'Esta GTA não está vinculada a nenhum animal.'}), 400
        if any(l.sts for l in linhas):
            return jsonify({'erro': 'Já existe Comunicado para estes animais: não dá mais para desvincular.'}), 400
        id_operacao = registrar_operacao(
            db, id_usuario=session['usuario_id'], id_propriedade=int(id_propriedade),
            modulo='saida_vincular',
            descricao=(f'Desvínculo da GTA {gta.numero_gta_completo} de {len(linhas)} animal(is) — '
                       f'Data de Saída apagada'))
        for l in linhas:
            antes = {'id_gta': l.id_gta, 'id_frigorifico': l.id_frigorifico}
            l.id_gta = None
            l.id_frigorifico = None
            registrar_item(db, id_operacao, 'tb_2020_embarque', l.id, 'UPDATE', antes,
                           {'id_gta': None, 'id_frigorifico': None})
        antes_gta = {'data_saida': gta.data_saida.isoformat() if gta.data_saida else None}
        resumo_caixa = {'numero': gta.numero_gta_completo, 'total': len(linhas), 'data_embarque': _data_br(data),
                        'data_saida': _data_br(gta.data_saida) if gta.data_saida else '-'}
        gta.data_saida = None
        registrar_item(db, id_operacao, 'tb_4001_gta', gta.id, 'UPDATE', antes_gta, {'data_saida': None})
        id_gta_ok = gta.id
        qs_tipo = _qs_tipo(_tipo_saida_da_gta(gta.tipo_movimento))
        db.commit()

    session['caixa_desvincular'] = resumo_caixa
    return jsonify({
        'ok': True,
        'url': f'{URL_DESVINCULADA}?id_propriedade={int(id_propriedade)}&data={data.strftime("%Y-%m-%d")}{qs_tipo}',
    })


# -------------------------------------------------------
# GET /produtor/saida-vincular/concluida e /desvinculada - Caixas de Sucesso (v1.4.0).
# Leem e apagam o resumo guardado na sessao; se nao houver (F5), voltam para a tela da data.
# -------------------------------------------------------
@saida_vincular.route('/produtor/saida-vincular/concluida')
def concluida():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    url_gtas = f'{URL_EMBARQUES}?id_propriedade={int(id_propriedade)}'   # v1.6.1 - o fluxo volta para a lista de embarques
    r = session.pop('caixa_vincular', None)
    if not r:
        return redirect(url_gtas)
    mudancas = [{'campo': 'Animais vinculados', 'antes': None, 'depois': f'{r["total"]} do embarque de {r["data_embarque"]}'}]
    if r['categorias']:
        mudancas.append({'campo': 'Categorias', 'antes': None, 'depois': ' · '.join(r['categorias'])})
    mudancas += [{'campo': 'Data de Saída', 'antes': None, 'depois': r['data_saida']},
                 {'campo': r.get('destino_rotulo', 'Frigorífico'), 'antes': None, 'depois': r['frigorifico']}]
    # s120 - ainda ha leitura SEM GTA (qualquer tipo) nesta Propriedade? So entao oferece "Vincular outra GTA".
    with get_db_produtor(session['id_produtor']) as db_pend:
        ha_pendente = any(
            (db_pend.query(func.count(Embarque.id)).filter(*_filtro_abertas(int(id_propriedade), t_pend), Embarque.id_gta.is_(None)).scalar() or 0) > 0
            for t_pend in ('ABATE', 'TRANSFER', 'VENDA', 'POSSE'))
    botoes = [{'texto': 'Gerar Comunicado de Saída', 'url': f'{URL_GERAR_COMUNICADO}?id_propriedade={int(id_propriedade)}', 'primario': True}]
    if ha_pendente:
        botoes.append({'texto': 'Vincular outra GTA', 'url': url_gtas, 'primario': False})
    botoes += [{'texto': 'Ver GTAs já vinculadas', 'url': f'{URL_VINCULADAS}?id_propriedade={int(id_propriedade)}', 'primario': False},
               {'texto': 'Voltar ao Hub de Saídas', 'url': URL_HUB, 'primario': False}]
    return render_caixa_sucesso(
        _contexto_base(), titulo='GTA vinculada com sucesso!', subtitulo=r['numero'], mudancas=mudancas,
        notas=['Próximo passo: gerar o Comunicado de Saída. Se precisar desfazer, use "Ver GTAs já vinculadas" antes do Comunicado.',
               'O vínculo ficou registrado no Log de Operações.'],
        botoes=botoes,
        url_voltar=url_gtas, titulo_pagina='Orion SISBOV — GTA vinculada',
    )


@saida_vincular.route('/produtor/saida-vincular/desvinculada')
def desvinculada():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    url_gtas = f'{URL_EMBARQUES}?id_propriedade={int(id_propriedade)}'   # v1.6.1 - o fluxo volta para a lista de embarques
    url_vinculadas = f'{URL_VINCULADAS}?id_propriedade={int(id_propriedade)}'
    r = session.pop('caixa_desvincular', None)
    if not r:
        return redirect(url_vinculadas)
    return render_caixa_sucesso(
        _contexto_base(), titulo='GTA desvinculada.', subtitulo=r['numero'], icone='&#8617;&#65039;',
        mudancas=[{'campo': 'Animais', 'antes': f'{r["total"]} vinculados', 'depois': 'voltaram a ficar livres'},
                  {'campo': 'Data de Saída', 'antes': r['data_saida'], 'depois': 'apagada'}],
        notas=[f'Os animais continuam no embarque de {r["data_embarque"]}. Para usar a GTA de novo, vincule outra vez.',
               'O desvínculo ficou registrado no Log de Operações.'],
        botoes=[{'texto': 'Vincular GTA', 'url': url_gtas, 'primario': True},
                {'texto': 'Ver GTAs já vinculadas', 'url': url_vinculadas, 'primario': False}],
        url_voltar=url_vinculadas, titulo_pagina='Orion SISBOV — GTA desvinculada',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\saida_vincular.py
# =========================================================
