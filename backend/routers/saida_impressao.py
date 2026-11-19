# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\routers
# MODULO:       backend\routers\saida_impressao.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-20 12:15 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.6.0
# v1.6.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (2 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.5.0: Sessao 120 (2026-11-10 14:05 -03) - Titulo da tela (e da selecao de Propriedade) mostra o tipo: Impressao/Reimpressao Comunicado de Saida - Venda/Abate/Transferencia/Posse. Subtitulo volta ao texto normal. REVERSAO: .bak_antes_s120_imp_tipo.
# v1.4.0: Sessao 120 (2026-11-10 12:43 -03) - Reimpressao (e Impressao, se receber tipo) filtrada pelo tipo da aba do Hub: Venda so Venda, Abate so Abate, Transferencia so Transferencia, Posse so Posse. Sem tipo na URL lista todos, como antes. REVERSAO: .bak_antes_s120_reimp_tipo.
# v1.3.0: Sessao 115 (05/11/2026) - Posse na Impressao/Reimpressao com PDF proprio (Comunicado de Alteracao de Posse). REVERSAO: .bak_antes_s115_posse_pdf.
# v1.2.0: Sessao 111 (01/11/2026) - Venda e Morte (ver Diario de Bordo da Sessao 111). REVERSAO: arquivos .bak_antes_s111* ao lado.
#
# DESCRICAO:
#     Impressao e Reimpressao do Comunicado de Saida (Abate) - Hub de Saidas, grupo "Comunicados a Certificadora".
#     Molde: impressao_comunicado.py / reimpressao_comunicado.py da Entrada, num arquivo so (as duas telas
#     sao quase iguais; o que muda e quem grava).
#
#     IMPRESSAO  (/produtor/saida-impressao/...)   lista so os Comunicados ABERTOS. Na PRIMEIRA vez que o usuario
#                baixa o PDF (de qualquer um dos tres modelos) o Comunicado vira IMPRESSO e grava data_envio,
#                impresso_em e id_usuario_impressao em todas as linhas (GTAs) dele. O PDF e montado ANTES de
#                gravar: se o PDF falhar, o status nao muda. Se ja estiver IMPRESSO, so devolve o PDF.
#     REIMPRESSAO (/produtor/saida-reimpressao/...) lista so os IMPRESSOS, do mais recente para o mais antigo,
#                com "Impresso em" e "Por". NUNCA grava nada.
#
#     MODELOS (o usuario escolhe, um PDF por escolha - parametro "modelo" da rota pdf):
#         xx  = Anexo XX (grade Ind | SISBOV)
#         xxi = Anexo XXI com codigo de barras
#         qr  = Anexo XXI com QR Code (modelo Orion, em teste)
#     PDFs: backend/utils/pdf_anexo_saida.py; dados: backend/utils/comunicado_saida_display.py.
#
#     Seguranca: toda rota com id_propriedade confere se a Propriedade e do usuario logado e a fazenda em uso
#     (_propriedade_do_usuario); a Reimpressao confere de novo no servidor que o Comunicado esta IMPRESSO.
#     Download como anexo (pasta Downloads), com o aviso padrao (aviso_download).
#
#     v1.0.0: Criacao (Sessao 101, Pacote 2).
#     v1.1.0: Sessao 107 (28/10/2026) - Transferencia na Impressao/Reimpressao (parametro tipo=TRANSFER nas rotas pdf; o numero repete entre tipos).  REVERSAO: .bak_antes_s107zg
# =========================================================

from datetime import date, datetime

from flask import Blueprint, redirect, render_template, request, send_file, session
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Produtor, Propriedade, Usuario
from backend.models.tb_2011_com_saidas import ComunicadoSaida
from backend.routers.auth import buscar_pares_propriedade_produtor, redirecionar_home, resolver_fazenda_em_uso
from backend.routers.saida_consulta import _contexto_base, _negado, _nomes, _propriedade_do_usuario, URL_HUB
from backend.utils.comunicado_saida_display import agrupar_comunicados_saida, montar_contexto_anexo_saida, montar_contexto_posse
from backend.utils.multitenant import get_db_produtor
from backend.utils.pdf_anexo_saida import MODELOS
from backend.utils.pdf_comunicado_posse import MODELOS_POSSE

saida_impressao = Blueprint('saida_impressao', __name__)

BASE_IMPRESSAO = '/produtor/saida-impressao'
BASE_REIMPRESSAO = '/produtor/saida-reimpressao'
URL_HUB_COMUNICADOS = URL_HUB

# s120 - tipo vindo da aba do Hub (?tipo=VENDA etc.). Vazio = todos.
TIPOS_VALIDOS = ('ABATE', 'TRANSFER', 'VENDA', 'POSSE')
TITULO_TIPO = {'ABATE': 'Abate', 'TRANSFER': 'Transferência', 'VENDA': 'Venda', 'POSSE': 'Posse'}   # s120 - sufixo do titulo
ROTULO_TIPO = {'ABATE': 'Abate', 'TRANSFER': 'Transferência', 'VENDA': 'Venda', 'POSSE': 'Alteração de Posse'}


def _tipo_filtro():
    t = (request.args.get('tipo') or '').strip().upper()
    return t if t in TIPOS_VALIDOS else ''


CONFIG = {
    'impressao': {
        'base': BASE_IMPRESSAO,
        'titulo': 'Impressão Comunicado de Saída',
        'subtitulo': 'Comunicados de Saída aguardando impressão',
        'status': 'ABERTO',
        'vazio': 'Não existe Comunicado de Saída aguardando impressão para esta Propriedade.',
    },
    'reimpressao': {
        'base': BASE_REIMPRESSAO,
        'titulo': 'Reimpressão Comunicado de Saída',
        'subtitulo': 'Comunicados de Saída já impressos',
        'status': 'IMPRESSO',
        'vazio': 'Não existe Comunicado de Saída já impresso para esta Propriedade.',
    },
}


def _mapa_usuarios(ids_usuario):
    if not ids_usuario:
        return {}
    with Session(engine) as dbp:
        return {u.id: u.nome for u in dbp.query(Usuario).filter(Usuario.id.in_(ids_usuario)).all()}


# -------------------------------------------------------
# iniciar: sem fazenda em uso e com 2+ pares mostra a selecao; senao abre a lista direto.
# -------------------------------------------------------
def _iniciar(modo):
    cfg = CONFIG[modo]
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    tipo_filtro = _tipo_filtro()   # s120 - leva o tipo da aba ate a lista
    url_listar = f"{cfg['base']}/listar" + (f'?tipo={tipo_filtro}' if tipo_filtro else '')
    sep = '&' if '?' in url_listar else '?'

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista,
            erro=erro,
            titulo=f"{cfg['titulo']}{(' – ' + TITULO_TIPO[tipo_filtro]) if tipo_filtro else ''} — Selecionar Propriedade",
            proximo=url_listar,
            campo_propriedade='id_propriedade',
            voltar=URL_HUB_COMUNICADOS,
            **_contexto_base(),
        )

    if len(pares) == 0:
        return _tela_selecionar([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')

    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{url_listar}{sep}id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{url_listar}{sep}id_propriedade={par.id_propriedade}')

    return _tela_selecionar(pares, None)


def _listar(modo):
    cfg = CONFIG[modo]
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade.isdecimal() or not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_propriedade = int(id_propriedade)

    with get_db_produtor(session['id_produtor']) as db:
        propriedade = db.get(Propriedade, id_propriedade)
        if not propriedade:
            return _negado()

        linhas = (
            db.query(ComunicadoSaida)
            .filter(
                ComunicadoSaida.id_propriedade_origem == id_propriedade,
                ComunicadoSaida.status == cfg['status'],
                ComunicadoSaida.tipo_saida.in_((_tipo_filtro(),) if _tipo_filtro() else TIPOS_VALIDOS),   # s120 - so o tipo da aba
            )
            .order_by(ComunicadoSaida.numero_comunicado.desc(), ComunicadoSaida.gta_data_emissao.asc())
            .all()
        )
        comunicados = agrupar_comunicados_saida(db, linhas, decrescente=True)

        nomes = _mapa_usuarios([c['id_usuario_impressao'] for c in comunicados if c['id_usuario_impressao']])
        for c in comunicados:
            if c['impresso_em']:
                c['impresso_texto'] = c['impresso_em'].strftime('%d/%m/%Y %H:%M')
            elif c['data_envio']:
                c['impresso_texto'] = c['data_envio'].strftime('%d/%m/%Y')
            else:
                c['impresso_texto'] = '-'
            c['impresso_por'] = nomes.get(c['id_usuario_impressao'], '-') if c['id_usuario_impressao'] else '-'

        produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, session['id_produtor'])

        tipo_filtro = _tipo_filtro()   # s120 - tipo da aba (vazio = todos)
        return render_template(
            'produtor/saida_impressao_listar.html',
            modo=modo,
            titulo_tela=cfg['titulo'] + (f' – {TITULO_TIPO[tipo_filtro]}' if tipo_filtro else ''),   # s120 - titulo com o tipo
            subtitulo_tela=cfg['subtitulo'],
            texto_vazio=(cfg['vazio'].replace('Comunicado de Saída', f'Comunicado de Saída de {ROTULO_TIPO[tipo_filtro]}') if tipo_filtro else cfg['vazio']),   # s120
            url_base=cfg['base'],
            produtor_nome=produtor_nome,
            propriedade_nome=propriedade_nome,
            propriedade_local=propriedade_local,
            id_propriedade=id_propriedade,
            comunicados=comunicados,
            url_voltar=URL_HUB_COMUNICADOS,
            **_contexto_base(),
        )


# -------------------------------------------------------
# pdf: monta o PDF primeiro; so depois (e so na Impressao, so se ainda ABERTO) grava IMPRESSO.
# -------------------------------------------------------
def _pdf(modo, numero_comunicado):
    cfg = CONFIG[modo]
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade.isdecimal() or not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_propriedade = int(id_propriedade)

    url_lista = f"{cfg['base']}/listar?id_propriedade={id_propriedade}"
    tipo = request.args.get('tipo') if request.args.get('tipo') in ('TRANSFER', 'VENDA', 'POSSE') else 'ABATE'

    modelo = request.args.get('modelo', '')
    modelos_do_tipo = MODELOS_POSSE if tipo == 'POSSE' else MODELOS   # s115: a Posse tem PDF proprio
    if modelo not in modelos_do_tipo:
        return redirect(url_lista)
    funcao_pdf, sufixo = modelos_do_tipo[modelo]

    with get_db_produtor(session['id_produtor']) as db:
        linhas = (
            db.query(ComunicadoSaida)
            .filter(
                ComunicadoSaida.id_propriedade_origem == id_propriedade,
                ComunicadoSaida.numero_comunicado == numero_comunicado,
                ComunicadoSaida.tipo_saida == tipo,
            )
            .order_by(ComunicadoSaida.gta_data_emissao.asc(), ComunicadoSaida.id.asc())
            .all()
        )
        if not linhas:
            return redirect(url_lista)

        # Reimpressao so serve Comunicado JA impresso (conferido no servidor, nao so na lista).
        if modo == 'reimpressao' and linhas[0].status != 'IMPRESSO':
            return redirect(url_lista)

        produtor = db.get(Produtor, session['id_produtor'])
        if tipo == 'POSSE':
            if session.get('usuario_cargo') not in ('TITULAR', 'ADMINISTRADOR'):
                return _negado()
            contexto = montar_contexto_posse(db, linhas, produtor, id_propriedade)
            if not contexto['animais']:
                return redirect(url_lista)
        else:
            contexto = montar_contexto_anexo_saida(db, linhas, produtor, id_propriedade)
            if not contexto['sisbov']:
                return redirect(url_lista)
        buffer = funcao_pdf(contexto)

        # So agora grava (primeira impressao, so na Impressao).
        if modo == 'impressao' and linhas[0].status == 'ABERTO':
            agora = datetime.now()
            for linha in linhas:
                linha.status = 'IMPRESSO'
                linha.data_envio = date.today()
                linha.impresso_em = agora
                linha.id_usuario_impressao = session['usuario_id']
            db.commit()

    prefixo = {'TRANSFER': 'comunicado_saida_transfer', 'VENDA': 'comunicado_saida_venda', 'POSSE': 'comunicado_saida_posse'}.get(tipo, 'comunicado_saida')
    nome_arquivo = f'{prefixo}_{numero_comunicado:06d}_{sufixo}.pdf'
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)


# -------------------------------------------------------
# Rotas - Impressao
# -------------------------------------------------------
@saida_impressao.route(f'{BASE_IMPRESSAO}/iniciar')
def impressao_iniciar():
    return _iniciar('impressao')


@saida_impressao.route(f'{BASE_IMPRESSAO}/listar')
def impressao_listar():
    return _listar('impressao')


@saida_impressao.route(f'{BASE_IMPRESSAO}/pdf/<int:numero_comunicado>')
def impressao_pdf(numero_comunicado):
    return _pdf('impressao', numero_comunicado)


# -------------------------------------------------------
# Rotas - Reimpressao (nunca grava)
# -------------------------------------------------------
@saida_impressao.route(f'{BASE_REIMPRESSAO}/iniciar')
def reimpressao_iniciar():
    return _iniciar('reimpressao')


@saida_impressao.route(f'{BASE_REIMPRESSAO}/listar')
def reimpressao_listar():
    return _listar('reimpressao')


@saida_impressao.route(f'{BASE_REIMPRESSAO}/pdf/<int:numero_comunicado>')
def reimpressao_pdf(numero_comunicado):
    return _pdf('reimpressao', numero_comunicado)

# =========================================================
# FIM DE ARQUIVO: backend\routers\saida_impressao.py
# =========================================================
