# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\morte_notificacao.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-01 18:30 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.1.0
# v1.1.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (4 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     NOTIFICACAO DE MORTE (Anexo XXII) - Gerar, Impressao e Reimpressao (pacote 5). Documento oficial, como a Notificacao de Nascimento.
#     Regras do Benedito (01/11/2026):
#       - O escritorio vai juntando as mortes (cada lancamento = um Controle MRT) e faz a Notificacao de todas de uma vez: o GERAR pega
#         TODAS as mortes da Propriedade que ainda nao tem numero de Notificacao (nao ha escolha por periodo);
#       - numeracao PROPRIA, por Propriedade, a partir de 000001 (tb_2021_notificacao_morte); o numero vai no MRT (tb_2013), em cada animal
#         (tb_2002, tipo_saida = MORTE) e na tb_2017 (6 digitos);
#       - fluxo Gerar -> Impressao (1a impressao: ABERTO vira IMPRESSO) -> Reimpressao (nunca grava); 2 vias; sem codigo de barras e sem PIA;
#       - depois de gerada a Notificacao, o Desfazer da morte deixa de valer (log_operacoes.py v1.20.0); a Notificacao em si e so historico.
#     Tudo ou nada, com trava por Propriedade (o primeiro que clicar leva o numero).
#
#     ROTAS (/produtor/morte/notificacao/): gerar/iniciar, gerar (GET confere / POST grava), impressao|reimpressao/iniciar, /listar, /pdf/<n>.
#
#     v1.0.0: Sessao 111 (01/11/2026) - Criacao. REVERSAO: apagar este arquivo e o morte_notificacao_*.html; desfazer o registro em app.py e no Hub;
#     v1.0.1: Sessao 113 (03/11/2026, 15:40 -03) - Lista do Gerar mostra a data (ou o periodo) da morte de CADA animal do MRT, nao so a do primeiro.  REVERSAO: .bak_antes_s113_ordem_data.
#             log_operacoes.py volta ao .bak_antes_s111_notificacao.
#     v1.0.2: Sessao 117 (06/11/2026, 20:45 -03) - Aviso da tela de sucesso em duas linhas (icone maior). REVERSAO: .bak_antes_s117_aviso2l.
# =========================================================
from datetime import date, datetime

from flask import Blueprint, redirect, render_template, request, send_file, session
from sqlalchemy import func, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Produtor, Usuario
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_2013_com_morte import ControleMorte
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_2021_notificacao_morte import NotificacaoMorte
from backend.routers.auth import buscar_pares_propriedade_produtor, redirecionar_home, resolver_fazenda_em_uso
from backend.routers.saida_consulta import _contexto_base, _negado, _nomes, _propriedade_do_usuario, URL_HUB
from backend.routers.morte_lancamento import _texto_controle
from backend.utils.caixa_sucesso import render_caixa_sucesso
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.multitenant import get_db_produtor
from backend.utils.notificacao_morte_display import listar_notificacoes, montar_contexto_anexo_xxii
from backend.utils.pdf_anexo_xxii import gerar_pdf_anexo_xxii

morte_notificacao = Blueprint('morte_notificacao', __name__)

BASE = '/produtor/morte/notificacao'
CLASSE_TRAVA_NOTIFICACAO = 2021
MODULO_LOG = 'morte_notificacao'
CONFIG = {
    'impressao': {'base': f'{BASE}/impressao', 'titulo': 'Impressão da Notificação de Morte',
                  'subtitulo': 'Notificações de Morte aguardando impressão', 'status': 'ABERTO',
                  'vazio': 'Não existe Notificação de Morte aguardando impressão para esta Propriedade.'},
    'reimpressao': {'base': f'{BASE}/reimpressao', 'titulo': 'Reimpressão da Notificação de Morte',
                    'subtitulo': 'Notificações de Morte já impressas', 'status': 'IMPRESSO',
                    'vazio': 'Não existe Notificação de Morte já impressa para esta Propriedade.'},
}


def _mapa_usuarios(ids):
    if not ids:
        return {}
    with Session(engine) as dbp:
        return {u.id: u.nome for u in dbp.query(Usuario).filter(Usuario.id.in_(ids)).all()}


def _escolher_propriedade(url_destino, titulo):
    """Sem fazenda em uso e com 2+ pares mostra a selecao; senao vai direto."""
    if 'id_produtor' not in session:
        return redirecionar_home()
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela(pares_lista, erro):
        return render_template('produtor/selecionar_propriedade_produtor.html', pares=pares_lista, erro=erro,
                               titulo=f'{titulo} — Selecionar Propriedade', proximo=url_destino,
                               campo_propriedade='id_propriedade', voltar=URL_HUB, **_contexto_base())

    if len(pares) == 0:
        return _tela([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor'] = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{url_destino}?id_propriedade={par_em_uso.id_propriedade}')
    if len(pares) == 1:
        par = pares[0]
        session['id_produtor'] = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{url_destino}?id_propriedade={par.id_propriedade}')
    return _tela(pares, None)


# =========================================================
# GERAR
# =========================================================

def _periodo_datas(db, ids_controle):
    """s113 - {id_controle: 'dd/mm/aaaa' ou 'dd/mm/aaaa a dd/mm/aaaa'} pela Data da Morte de CADA animal (o mesmo MRT pode ter datas diferentes)."""
    if not ids_controle:
        return {}
    linhas = (db.query(SaidaAnimal.id_com_morte, func.min(SaidaAnimal.data_saida), func.max(SaidaAnimal.data_saida))
              .filter(SaidaAnimal.id_com_morte.in_(ids_controle), SaidaAnimal.tipo_saida == 'MORTE')
              .group_by(SaidaAnimal.id_com_morte).all())
    saida = {}
    for idc, menor, maior in linhas:
        if menor is None:
            continue
        saida[idc] = menor.strftime('%d/%m/%Y') if menor == maior else f"{menor.strftime('%d/%m/%Y')} a {maior.strftime('%d/%m/%Y')}"
    return saida


def _pendentes(db, id_propriedade, travar=False):
    consulta = (db.query(ControleMorte).filter(ControleMorte.id_propriedade == int(id_propriedade),
                                               ControleMorte.numero_comunicado.is_(None))
                .order_by(ControleMorte.controle.asc()))
    if travar:
        consulta = consulta.with_for_update()
    return consulta.all()


@morte_notificacao.route(f'{BASE}/gerar/iniciar')
def gerar_iniciar():
    return _escolher_propriedade(f'{BASE}/gerar', 'Gerar Notificação de Morte')


@morte_notificacao.route(f'{BASE}/gerar')
def gerar_conferencia():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade.isdecimal() or not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_propriedade = int(id_propriedade)
    with get_db_produtor(session['id_produtor']) as db:
        controles = _pendentes(db, id_propriedade)
        proximo = (db.query(func.max(NotificacaoMorte.numero_comunicado))
                   .filter(NotificacaoMorte.id_propriedade == id_propriedade).scalar() or 0) + 1
        periodos = _periodo_datas(db, [c.id for c in controles])
        itens = [{'texto': _texto_controle(c.controle), 'data_morte': periodos.get(c.id, c.data_morte.strftime('%d/%m/%Y')), 'qtd': c.qtd_animais,
                  'origem': 'Arquivo' if c.origem == 'ARQUIVO' else 'Individual'} for c in controles]
        total = sum(c.qtd_animais for c in controles)
    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, session['id_produtor'])
    return render_template(
        'produtor/morte_notificacao_gerar.html', itens=itens, total_animais=total, numero_texto=f'{proximo:06d}',
        id_propriedade=id_propriedade, url_gerar=f'{BASE}/gerar', url_voltar=URL_HUB,
        produtor_nome=produtor_nome, propriedade_nome=propriedade_nome, propriedade_local=propriedade_local,
        **_contexto_base())


@morte_notificacao.route(f'{BASE}/gerar', methods=['POST'])
def gerar():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.form.get('id_propriedade', '')
    if not id_propriedade.isdecimal() or not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_propriedade = int(id_propriedade)
    url_conferencia = f'{BASE}/gerar?id_propriedade={id_propriedade}'
    if request.form.get('confirmo') != '1':
        return redirect(url_conferencia)
    id_produtor = session['id_produtor']
    id_usuario = session.get('usuario_id')

    try:
        with get_db_produtor(id_produtor) as db:
            db.execute(text('SELECT pg_advisory_xact_lock(:classe, :id_propriedade)'),
                       {'classe': CLASSE_TRAVA_NOTIFICACAO, 'id_propriedade': id_propriedade})
            controles = _pendentes(db, id_propriedade, travar=True)
            if not controles:
                return redirect(url_conferencia)
            ids_controle = [c.id for c in controles]
            animais = (db.query(SaidaAnimal).filter(SaidaAnimal.id_com_morte.in_(ids_controle), SaidaAnimal.tipo_saida == 'MORTE',
                                                    SaidaAnimal.id_propriedade == id_propriedade).with_for_update().all())
            numero = (db.query(func.max(NotificacaoMorte.numero_comunicado))
                      .filter(NotificacaoMorte.id_propriedade == id_propriedade).scalar() or 0) + 1
            numero_6 = f'{numero:06d}'
            total = len(animais)
            textos_mrt = [_texto_controle(c.controle) for c in controles]

            id_operacao = registrar_operacao(
                db, id_usuario=id_usuario, id_propriedade=id_propriedade, modulo=MODULO_LOG,
                descricao=(f'Notificação de Morte nº {numero_6} — {len(controles)} controle(s) ({textos_mrt[0]}'
                           + (f' a {textos_mrt[-1]}' if len(textos_mrt) > 1 else '') + f') — {total} animal(is)')[:255])
            notificacao = NotificacaoMorte(id_propriedade=id_propriedade, numero_comunicado=numero, qtd_animais=total,
                                           status='ABERTO', id_usuario_geracao=id_usuario)
            db.add(notificacao)
            db.flush()
            registrar_item(db, id_operacao, 'tb_2021_notificacao_morte', notificacao.id, 'INSERT', None,
                           {'numero_comunicado': numero, 'animais': total})
            for c in controles:
                registrar_item(db, id_operacao, 'tb_2013_com_morte', c.id, 'UPDATE', {'numero_comunicado': None}, {'numero_comunicado': numero})
                c.numero_comunicado = numero
            sisbovs = []
            for a in animais:
                a.numero_comunicado = numero
                sisbovs.append(a.sisbov)
            if sisbovs:   # tb_2017: a linha de saida da morte recebe o numero (texto de 6 digitos)
                db.query(Movimentacao).filter(
                    Movimentacao.id_propriedade == id_propriedade, Movimentacao.sisbov.in_(sisbovs),
                    Movimentacao.tipo_saida == 'MORTE', Movimentacao.numero_comunicado.is_(None),
                ).update({'numero_comunicado': numero_6}, synchronize_session=False)
            qtd_controles = len(controles)
            db.commit()
    except IntegrityError:
        return redirect(url_conferencia)

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_caixa_sucesso(
        _contexto_base(),
        titulo='Notificação de Morte gerada!',
        subtitulo=f'Nº {numero_6}',
        mudancas=[
            {'campo': 'Propriedade', 'antes': None, 'depois': f'{produtor_nome} — {propriedade_nome} — {propriedade_local}'},
            {'campo': 'Notificação nº', 'antes': None, 'depois': numero_6},
            {'campo': 'Controles incluídos', 'antes': None, 'depois': f'{qtd_controles} ({textos_mrt[0]}' + (f' a {textos_mrt[-1]}' if len(textos_mrt) > 1 else '') + ')'},
            {'campo': 'Animais', 'antes': None, 'depois': str(total)},
        ],
        avisos=[['Depois de gerada, a morte não pode mais ser desfeita.', 'Imprima o documento (2 vias: Certificadora e Arquivo ERAS).']],   # v1.0.2: aviso em duas linhas
        botoes=[{'texto': 'Imprimir agora', 'url': f'{BASE}/impressao/iniciar', 'primario': True},
                {'texto': 'Hub de Saídas', 'url': URL_HUB, 'primario': False}],
        url_voltar=URL_HUB, icone='&#9989;', titulo_pagina='Orion SISBOV — Notificação de Morte',
    )


# =========================================================
# IMPRESSAO / REIMPRESSAO
# =========================================================
def _iniciar(modo):
    cfg = CONFIG[modo]
    return _escolher_propriedade(f"{cfg['base']}/listar", cfg['titulo'])


def _listar(modo):
    cfg = CONFIG[modo]
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade.isdecimal() or not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_propriedade = int(id_propriedade)
    with get_db_produtor(session['id_produtor']) as db:
        notificacoes = listar_notificacoes(db, id_propriedade, cfg['status'])
    nomes = _mapa_usuarios([n['id_usuario_impressao'] for n in notificacoes if n['id_usuario_impressao']])
    for n in notificacoes:
        n['impresso_texto'] = n['impresso_em'].strftime('%d/%m/%Y %H:%M') if n['impresso_em'] else '-'
        n['impresso_por'] = nomes.get(n['id_usuario_impressao'], '-') if n['id_usuario_impressao'] else '-'
    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, session['id_produtor'])
    return render_template(
        'produtor/morte_notificacao_listar.html', modo=modo, titulo_tela=cfg['titulo'], subtitulo_tela=cfg['subtitulo'],
        texto_vazio=cfg['vazio'], url_base=cfg['base'], id_propriedade=id_propriedade, notificacoes=notificacoes,
        url_voltar=URL_HUB, produtor_nome=produtor_nome, propriedade_nome=propriedade_nome, propriedade_local=propriedade_local,
        **_contexto_base())


def _pdf(modo, numero):
    cfg = CONFIG[modo]
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade.isdecimal() or not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_propriedade = int(id_propriedade)
    url_lista = f"{cfg['base']}/listar?id_propriedade={id_propriedade}"
    with get_db_produtor(session['id_produtor']) as db:
        notificacao = (db.query(NotificacaoMorte).filter(NotificacaoMorte.id_propriedade == id_propriedade,
                                                         NotificacaoMorte.numero_comunicado == numero).first())
        if notificacao is None:
            return redirect(url_lista)
        if modo == 'reimpressao' and notificacao.status != 'IMPRESSO':   # a Reimpressao so serve Notificacao JA impressa
            return redirect(url_lista)
        produtor = db.get(Produtor, session['id_produtor'])
        contexto = montar_contexto_anexo_xxii(db, notificacao, produtor, id_propriedade)
        if not contexto['animais']:
            return redirect(url_lista)
        buffer = gerar_pdf_anexo_xxii(contexto)   # monta o PDF primeiro; so depois grava
        if modo == 'impressao' and notificacao.status == 'ABERTO':
            notificacao.status = 'IMPRESSO'
            notificacao.data_envio = date.today()
            notificacao.impresso_em = datetime.now()
            notificacao.id_usuario_impressao = session['usuario_id']
            db.commit()
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                     download_name=f'notificacao_morte_{numero:06d}_anexo_xxii.pdf')


@morte_notificacao.route(f'{BASE}/impressao/iniciar')
def impressao_iniciar():
    return _iniciar('impressao')


@morte_notificacao.route(f'{BASE}/impressao/listar')
def impressao_listar():
    return _listar('impressao')


@morte_notificacao.route(f'{BASE}/impressao/pdf/<int:numero>')
def impressao_pdf(numero):
    return _pdf('impressao', numero)


@morte_notificacao.route(f'{BASE}/reimpressao/iniciar')
def reimpressao_iniciar():
    return _iniciar('reimpressao')


@morte_notificacao.route(f'{BASE}/reimpressao/listar')
def reimpressao_listar():
    return _listar('reimpressao')


@morte_notificacao.route(f'{BASE}/reimpressao/pdf/<int:numero>')
def reimpressao_pdf(numero):
    return _pdf('reimpressao', numero)

# =========================================================
# FIM DE ARQUIVO: backend\routers\morte_notificacao.py
# =========================================================
