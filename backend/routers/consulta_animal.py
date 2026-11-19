# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\routers
# MODULO:       backend\routers\consulta_animal.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-21 11:45 -03
# ATUALIZADO EM: 2026-11-19 12:30 -03
# VERSAO:       1.0.4
#
# DESCRICAO:
#     "Consulta de Animal e Brinco" (Sessao 102) - item do menu lateral, grupo OPERACAO, aberto a todos os cargos so em modo
#     CONSULTA. O usuario digita o Manejo (6 numeros) ou o SISBOV / RFID (15 numeros) e a tela responde DUAS coisas, sempre
#     dentro da Propriedade em USO (decisao de Benedito: o brinco tem de pertencer a Propriedade em uso):
#
#       1. ANIMAL: esta na Propriedade (tb_2001: resumo + link para a ficha da Consulta por Manejo) ou SAIU (tb_2002: tipo,
#          data, destino, GTA, Comunicado e peso). Se o mesmo Manejo existir em mais de um animal (um que saiu e outro que
#          entrou depois), mostra TODOS, do mais recente para o mais antigo - nao bloqueia.
#       2. BRINCO: situacao atual + linha do tempo (ordem de data): Disponivel no estoque, Em uso, Reidentificado, Cancelado,
#          Perdido ou Saiu com o animal. Brinco no estoque mostra so "Disponivel" (decisao de Benedito, sem lote).
#
#     Fontes (todas SO LEITURA): tb_2001 e tb_2002 (animal), tb_2017 (entradas e saidas), tb_7017 (ficha do brinco: status vazio =
#     disponivel, ENTRADA = aplicado, REIDENTI, CANCELADO), tb_3008 (saida do estoque de brincos), tb_6005/6006 (reidentificacao
#     com baixa, SISBOV antigo -> novo), tb_6003/6004 (troca de elemento, mesmo SISBOV), tb_6007/6008 (perda), tb_6012/6013
#     (cancelamento). Morte, Venda e Transferencia aparecem sozinhas quando esses modulos gravarem em tb_2002/tb_2017.
#     Animal lido para saida que NAO embarcou (substituido=True) nao conta como "saiu": entra na linha do tempo do brinco.
#
#     Permissao: usa o modulo 'consulta_manejo' (Consulta); o endereco /produtor/consulta-animal esta no mapa do porteiro
#     (permissoes.py 1.6.0). NAO grava nada.
#
#     ROTAS: /produtor/consulta-animal/iniciar (resolve a fazenda em uso) e /produtor/consulta-animal (a consulta).
#
#     v1.0.4: Sessao 133 (19/11/2026, 12:30 -03) - ROTULO_ENTRADA ganha 'CARGA' (animal que entrou pela Carga). REVERSAO: .bak_antes_s133_carga.
#     v1.0.3: Sessao 121 (11/11/2026, 14:00 -03) - ROTULO_SAIDA ganha 'REIDENTI' (Reidentificacao). REVERSAO: .bak_antes_s121_reidentificacao.
#     v1.0.2: Sessao 102 (21/10/2026, 12:40 -03) - situacao do brinco que saiu com o animal passa a ser so "ABATE - 19/10/2026" (pedido de Benedito).
#     v1.0.1: Sessao 102 (21/10/2026, 12:20 -03) - quadro BRINCO ao lado do quadro ANIMAL (pedido de Benedito): a tela recebe 'grupos' (animal(is) +
#             o brinco do mesmo SISBOV na mesma linha). Nada de consulta mudou.
#     v1.0.0: Criacao (Sessao 102, 21/10/2026, 11:45 -03). REVERSAO: remover este arquivo, consulta_animal.html, devolver
#             app.py, permissoes.py e produtor_menu.html pelos .bak_antes_consulta_animal_s102.
#     v1.0.4: Sessao 121 (2026-11-11 19:00 -03) - Reidentificacao: a data vem do proprio animal (data_reidentificacao), pois animal pendente ainda nao tem pedido. REVERSAO: .bak_antes_s121_pendentes.
# =========================================================

from datetime import date

from flask import Blueprint, redirect, render_template, request, session
from sqlalchemy import or_

from backend.models import Produtor, Propriedade
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_3008_brincos_saida import BrincoSaida
from backend.models.tb_4005_racas import Raca
from backend.models.tb_6003_re_id_elementos import ReIdElementos
from backend.models.tb_6004_re_id_elementos_itens import ReIdElementosItem
from backend.models.tb_6005_reidentificacao_com_baixa import ReidentificacaoComBaixa
from backend.models.tb_6006_reidentificacao_com_baixa_itens import ReidentificacaoComBaixaItem
from backend.models.tb_6007_perda_saida_estoque import PerdaSaidaEstoque
from backend.models.tb_6008_perda_saida_estoque_itens import PerdaSaidaEstoqueItem
from backend.models.tb_6012_cancelamento_brinco import CancelamentoBrinco
from backend.models.tb_6013_cancelamento_brinco_itens import CancelamentoBrincoItem
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.routers.auth import buscar_pares_propriedade_produtor, redirecionar_home, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor

consulta_animal = Blueprint('consulta_animal', __name__)

URL_INICIAR = '/produtor/consulta-animal/iniciar'
URL_CONSULTA = '/produtor/consulta-animal'
URL_HOME = '/produtor/home'
URL_FICHA = '/produtor/consulta-manejo'
TITULO = 'Consulta de Animal e Brinco'
TAMANHO_MANEJO = 6
TAMANHO_SISBOV = 15
MENSAGEM_FORMATO = f'Digite o Manejo ({TAMANHO_MANEJO} números) ou o SISBOV / RFID ({TAMANHO_SISBOV} números).'

ROTULO_ENTRADA = {
    'COMPRA': 'Compra', 'NASCTO-DESMAME': 'Nascimento / Desmame', 'CARGA': 'Carga',
    'REIDENTIFICACAO': 'Reidentificação', 'TRANSFERENCIA': 'Transferência',
}
ROTULO_SAIDA = {'ABATE': 'Abate', 'VENDA': 'Venda', 'MORTE': 'Morte', 'TRANSFER': 'Transferência', 'REIDENTI': 'Reidentificação'}


@consulta_animal.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


# -------------------------------------------------------
# Auxiliares
# -------------------------------------------------------
def _data_br(d):
    return d.strftime('%d/%m/%Y') if d else ''


def _so_digitos(texto):
    return ''.join(c for c in (texto or '') if c in '0123456789')


def _propriedade_do_usuario(id_propriedade):
    try:
        id_int = int(id_propriedade)
    except (TypeError, ValueError):
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and par_em_uso.id_propriedade != id_int:
        return False
    return any(p.id_propriedade == id_int and p.id_produtor == session.get('id_produtor') for p in pares)


def _url_voltar(pares):
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return URL_INICIAR
    return URL_HOME


def _contexto_base():
    return dict(
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='consulta_animal',
    )


# -------------------------------------------------------
# PURA (sem banco): situacao atual do brinco + linha do tempo, a partir das linhas ja lidas.
# dados: dict com as listas  animal_prop (tb_2001), saidas (tb_2002 que embarcaram), nao_embarcou (tb_2002 substituido),
#   ficha (tb_7017 ou None), estoque_saida (tb_3008), movs (tb_2017), reid_antigo, reid_novo, troca_elemento, perda, cancelado
#   (cada uma: lista de dicts simples com 'data' = date ou None e os textos usados abaixo).
# Devolve (situacao_texto, situacao_classe, eventos[{data, titulo, detalhe}] em ordem de data).
# -------------------------------------------------------
def montar_situacao_e_eventos(d):
    eventos = []

    def add(data, titulo, detalhe=''):
        eventos.append({'data': data, 'titulo': titulo, 'detalhe': detalhe})

    for e in d.get('estoque_saida', []):
        partes = [ROTULO_ENTRADA.get(e.get('origem'), e.get('origem') or '')]
        if e.get('gta'):
            partes.append(f"GTA {e['gta']}")
        add(e.get('data'), 'Saiu do estoque de brincos', ' · '.join(p for p in partes if p))
    for m in d.get('movs', []):
        if m.get('tipo_saida'):
            partes = [m.get('destino') or '']
            if m.get('gta_saida'):
                partes.append(f"GTA {m['gta_saida']}")
            if m.get('comunicado'):
                partes.append(f"Comunicado {m['comunicado']}")
            add(m.get('data'), f"Saída — {ROTULO_SAIDA.get(m['tipo_saida'], m['tipo_saida'])}",
                ' · '.join(p for p in partes if p))
        else:
            partes = []
            if m.get('gta_entrada'):
                partes.append(f"GTA {m['gta_entrada']}")
            if m.get('lote'):
                partes.append(f"Lote {m['lote']}")
            if m.get('comunicado'):
                partes.append(f"Comunicado {m['comunicado']}")
            add(m.get('data'), f"Entrada — {ROTULO_ENTRADA.get(m.get('tipo_entrada'), m.get('tipo_entrada') or '')}",
                ' · '.join(partes))
    for r in d.get('reid_antigo', []):
        add(r.get('data'), 'Reidentificado', f"Substituído pelo SISBOV {r.get('outro')}")
    for r in d.get('reid_novo', []):
        add(r.get('data'), 'Reidentificação', f"Este brinco substituiu o SISBOV {r.get('outro')}")
    for r in d.get('troca_elemento', []):
        add(r.get('data'), f"Troca de elemento ({r.get('elementos') or ''})".replace(' ()', ''), r.get('motivo') or '')
    for r in d.get('perda', []):
        add(r.get('data'), 'Perda / saída de estoque', 'Código atribuído a animal sem identificação')
    for r in d.get('cancelado', []):
        add(r.get('data'), 'Brinco cancelado', r.get('motivo') or '')
    for r in d.get('nao_embarcou', []):
        add(r.get('data'), 'Lido para saída, não embarcou', r.get('detalhe') or '')

    eventos.sort(key=lambda e: (e['data'] is None, e['data'] or date.min))

    # ---- situacao atual (a mais forte primeiro) ----
    saidas = d.get('saidas', [])
    ficha = d.get('ficha')
    status = (ficha or {}).get('status') or ''
    if d.get('animal_prop'):
        sit = ('Em uso — no animal que está na Propriedade', 'uso')
    elif saidas:
        s = saidas[0]
        tipo = ROTULO_SAIDA.get(s.get('tipo'), s.get('tipo') or '').upper()
        sit = (f"{tipo} - {_data_br(s.get('data'))}" if s.get('data') else tipo, 'saiu')
    elif d.get('cancelado') or status == 'CANCELADO':
        sit = ('Cancelado', 'cancelado')
    elif d.get('perda'):
        sit = ('Perda / saída de estoque', 'cancelado')
    elif d.get('reid_antigo') or status == 'REIDENTI':
        sit = ('Reidentificado', 'reid')
    elif ficha is not None and not status:
        sit = ('Disponível', 'disponivel')
    elif ficha is not None and status == 'ENTRADA':
        sit = ('Em uso — aplicado em animal', 'uso')
    elif eventos:
        sit = ('Sem situação definida — veja a linha do tempo', 'reid')
    else:
        sit = ('Não consta nesta Propriedade', 'nao')
    return sit[0], sit[1], eventos


# -------------------------------------------------------
# Leitura do banco: tudo que existe de UM brinco (SISBOV) na Propriedade -> dict para montar_situacao_e_eventos
# -------------------------------------------------------
def _ler_brinco(db, id_propriedade, sisbov):
    d = {'sisbov': sisbov}
    d['animal_prop'] = [1 for _ in db.query(Entrada.id).filter(
        Entrada.id_propriedade == id_propriedade, Entrada.sisbov == sisbov).all()]

    saidas, nao_embarcou = [], []
    for s in db.query(SaidaAnimal).filter(SaidaAnimal.id_propriedade == id_propriedade,
                                          SaidaAnimal.sisbov == sisbov).order_by(SaidaAnimal.data_saida.desc()).all():
        if s.substituido:
            nao_embarcou.append({'data': s.data_embarque or s.data_saida,
                                 'detalhe': f'Substituído pelo SISBOV {s.sisbov_substituto}' if s.sisbov_substituto else ''})
        else:
            saidas.append({'tipo': s.tipo_saida, 'data': s.data_saida})
    d['saidas'], d['nao_embarcou'] = saidas, nao_embarcou

    f = db.query(EntradaBrincoRfid).filter(EntradaBrincoRfid.id_propriedade == id_propriedade,
                                           EntradaBrincoRfid.sisbov == sisbov).first()
    d['ficha'] = {'status': (f.status or '').strip().upper()} if f is not None else None

    d['estoque_saida'] = [
        {'data': b.data_saida, 'gta': b.gta, 'origem': b.origem}
        for b in db.query(BrincoSaida).filter(BrincoSaida.id_propriedade == id_propriedade,
                                              BrincoSaida.sisbov == sisbov).all()]

    d['movs'] = [
        {'data': m.data_movimentacao, 'tipo_entrada': m.tipo_entrada, 'tipo_saida': m.tipo_saida,
         'gta_entrada': m.gta_entrada, 'gta_saida': m.gta_saida, 'lote': m.lote, 'destino': m.destino_propriedade,
         'comunicado': m.numero_comunicado}
        for m in db.query(Movimentacao).filter(Movimentacao.id_propriedade == id_propriedade,
                                               Movimentacao.sisbov == sisbov)
        .order_by(Movimentacao.data_movimentacao.asc(), Movimentacao.id.asc()).all()]

    d['reid_antigo'] = [
        {'data': i.data_reidentificacao, 'outro': i.sisbov_novo}
        for i in db.query(ReidentificacaoComBaixaItem)
        .filter(ReidentificacaoComBaixaItem.id_propriedade == id_propriedade,
                ReidentificacaoComBaixaItem.sisbov_antigo == sisbov).all()]
    d['reid_novo'] = [
        {'data': i.data_reidentificacao, 'outro': i.sisbov_antigo}
        for i in db.query(ReidentificacaoComBaixaItem)
        .filter(ReidentificacaoComBaixaItem.id_propriedade == id_propriedade,
                ReidentificacaoComBaixaItem.sisbov_novo == sisbov).all()]
    d['troca_elemento'] = [
        {'data': p.data_solicitacao, 'elementos': str(p.elementos or ''), 'motivo': p.motivo}
        for i, p in db.query(ReIdElementosItem, ReIdElementos)
        .join(ReIdElementos, ReIdElementosItem.id_pedido == ReIdElementos.id)
        .filter(ReIdElementos.id_propriedade == id_propriedade, ReIdElementosItem.codigo_sisbov == sisbov).all()]
    d['perda'] = [
        {'data': p.data_solicitacao}
        for i, p in db.query(PerdaSaidaEstoqueItem, PerdaSaidaEstoque)
        .join(PerdaSaidaEstoque, PerdaSaidaEstoqueItem.id_pedido == PerdaSaidaEstoque.id)
        .filter(PerdaSaidaEstoque.id_propriedade == id_propriedade, PerdaSaidaEstoqueItem.sisbov_atribuido == sisbov).all()]
    d['cancelado'] = [
        {'data': p.data_solicitacao, 'motivo': p.motivo}
        for i, p in db.query(CancelamentoBrincoItem, CancelamentoBrinco)
        .join(CancelamentoBrinco, CancelamentoBrincoItem.id_pedido == CancelamentoBrinco.id)
        .filter(CancelamentoBrinco.id_propriedade == id_propriedade, CancelamentoBrincoItem.codigo_sisbov == sisbov).all()]
    return d


def _resumo_animal(db, a, id_propriedade, na_propriedade, racas):
    """Dicionario de TEXTO do animal (nada de objeto do banco vai para o template)."""
    base = {
        'na_propriedade': na_propriedade,
        'sisbov': a.sisbov or '', 'manejo': a.manejo or '', 'rfid': a.rfid or '',
        'sexo': a.sexo or '', 'raca': racas.get(a.id_raca, ''), 'nascimento': _data_br(a.nascimento),
    }
    if na_propriedade:
        base.update({
            'data_ordem': a.data_inclusao or a.data_brincagem,
            'origem': ROTULO_ENTRADA.get(a.tipo_entrada, a.tipo_entrada or ''),
            'lote': a.lote or '', 'entrada': _data_br(a.data_brincagem),
            'inclusao_bnd': _data_br(a.data_inclusao),
            'comunicado': '' if a.numero_comunicado is None else a.numero_comunicado,
            'liberacao_abate': _data_br(a.liberacao_abate),
            'link_ficha': f'{URL_FICHA}?id_propriedade={id_propriedade}&manejo={a.manejo}' if a.manejo else '',
        })
    else:
        base.update({
            'data_ordem': a.data_saida,
            'tipo_saida': ROTULO_SAIDA.get(a.tipo_saida, a.tipo_saida or ''),
            'data_saida': _data_br(a.data_saida), 'destino': a.destino_propriedade or '',
            'gta_saida': a.gta_saida or '',
            'comunicado': '' if a.numero_comunicado is None else a.numero_comunicado,
            'peso': '' if a.peso_saida is None else f'{float(a.peso_saida):.2f}'.replace('.', ','),
        })
    return base


@consulta_animal.route('/produtor/consulta-animal/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def tela(lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html', pares=lista, erro=erro,
            titulo=f'{TITULO} — Selecionar Propriedade', proximo=URL_CONSULTA, campo_propriedade='id_propriedade',
            voltar=URL_HOME, **_contexto_base())

    if len(pares) == 0:
        return tela([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')
    par_em_uso = resolver_fazenda_em_uso(pares)
    par = par_em_uso if par_em_uso is not None else (pares[0] if len(pares) == 1 else None)
    if par is not None:
        session['id_produtor'] = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_CONSULTA}?id_propriedade={par.id_propriedade}')
    return tela(pares, None)


@consulta_animal.route('/produtor/consulta-animal')
def consultar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return redirect(URL_INICIAR)
    id_propriedade = int(id_propriedade)

    busca = request.args.get('busca', '').strip()
    digitos = _so_digitos(busca)
    erro = None
    aviso = None
    animais, brincos = [], []

    with get_db_produtor(session['id_produtor']) as db:
        propriedade = db.get(Propriedade, id_propriedade)
        if not propriedade:
            return redirect(URL_INICIAR)
        produtor = db.get(Produtor, session['id_produtor'])
        propriedade_nome = propriedade.nome or ''
        produtor_nome = produtor.nome if produtor else ''

        if busca:
            if len(digitos) == TAMANHO_MANEJO:
                filtro_e = Entrada.manejo == digitos
                filtro_s = SaidaAnimal.manejo == digitos
                filtro_b = EntradaBrincoRfid.manejo == digitos
            elif len(digitos) == TAMANHO_SISBOV:
                filtro_e = or_(Entrada.sisbov == digitos, Entrada.rfid == digitos)
                filtro_s = or_(SaidaAnimal.sisbov == digitos, SaidaAnimal.rfid == digitos)
                filtro_b = or_(EntradaBrincoRfid.sisbov == digitos, EntradaBrincoRfid.rfid == digitos)
            else:
                filtro_e = None
                erro = MENSAGEM_FORMATO

            if filtro_e is not None:
                racas = {r.id: r.codigo for r in db.query(Raca).all()}
                na_prop = db.query(Entrada).filter(Entrada.id_propriedade == id_propriedade, filtro_e).all()
                saiu = (db.query(SaidaAnimal)
                        .filter(SaidaAnimal.id_propriedade == id_propriedade, filtro_s, SaidaAnimal.substituido == False)  # noqa: E712
                        .all())
                animais = [_resumo_animal(db, a, id_propriedade, True, racas) for a in na_prop]
                animais += [_resumo_animal(db, a, id_propriedade, False, racas) for a in saiu]
                animais.sort(key=lambda a: (a['data_ordem'] is None, -(a['data_ordem'].toordinal() if a['data_ordem'] else 0)))

                lista_sisbov = []
                for a in animais:
                    if a['sisbov'] and a['sisbov'] not in lista_sisbov:
                        lista_sisbov.append(a['sisbov'])
                for f in db.query(EntradaBrincoRfid).filter(EntradaBrincoRfid.id_propriedade == id_propriedade, filtro_b).all():
                    if f.sisbov not in lista_sisbov:
                        lista_sisbov.append(f.sisbov)
                if len(digitos) == TAMANHO_SISBOV and not lista_sisbov:
                    lista_sisbov.append(digitos)   # nada achado: ainda assim consulta as tabelas de brinco

                for s in lista_sisbov:
                    texto, classe, eventos = montar_situacao_e_eventos(_ler_brinco(db, id_propriedade, s))
                    brincos.append({
                        'sisbov': s, 'situacao': texto, 'classe': classe,
                        'eventos': [{'data': _data_br(e['data']) or '—', 'titulo': e['titulo'], 'detalhe': e['detalhe']}
                                    for e in eventos],
                    })
                if not animais and not any(b['classe'] != 'nao' for b in brincos):
                    aviso = 'Nada encontrado nesta Propriedade (nem animal, nem brinco).'
                    brincos = []

    # v1.0.1 - uma linha por brinco: o(s) animal(is) desse SISBOV a esquerda e o brinco a direita
    grupos = []
    vistos = set()
    for b in brincos:
        do_brinco = [a for a in animais if a['sisbov'] == b['sisbov']]
        vistos.update(id(a) for a in do_brinco)
        grupos.append({'animais': do_brinco, 'brinco': b})
    for a in animais:
        if id(a) not in vistos:
            grupos.append({'animais': [a], 'brinco': None})

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    return render_template(
        'produtor/consulta_animal.html',
        id_propriedade=id_propriedade, propriedade_nome=propriedade_nome, produtor_nome=produtor_nome,
        busca=busca, erro=erro, aviso=aviso, animais=animais, brincos=brincos, grupos=grupos,
        url_voltar=_url_voltar(pares), **_contexto_base())

# =========================================================
# FIM DE ARQUIVO: backend\routers\consulta_animal.py
# =========================================================
