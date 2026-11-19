# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\brincos_disponiveis.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-02 14:35 -03
# ATUALIZADO EM: 2026-10-08 18:30 -03
# VERSAO: 1.5.0
# v1.5.0: Sessao 123 (2026-11-13 20:10 -03) - AUDITORIA ETAPA 6 (leitura a fundo): Propriedade conferida (numero + e do usuario) e mensagens com norte em tela do Orion (antes: erro 500 / cabecalho de outra Propriedade / texto solto). REVERSAO: .bak_antes_etapa6e.
#
# DESCRICAO:
#     Modulo "Brincos Disponiveis" do Hub de Brincos (Sessao 044),
#     5o dos 7 cards. Mesmo padrao arquitetural ja fechado em
#     brincos_relatorio_nfiscais.py, mas SEM tela de grid
#     intermediaria - so uma tela de CONFIRMACAO com botao
#     "Imprimir" explicito (ver v1.1.0 abaixo).
#
#       1. /produtor/brincos-disponiveis/iniciar - resolve
#          Propriedade E Produtor (PADRAO REUTILIZAVEL No1). SEMPRE
#          renderiza a tela de confirmacao (brincos_disponiveis_
#          confirmar.html), mesmo com 1 par so - v1.0.0 pulava
#          direto para o PDF quando havia 1 par, e o Usuario nao
#          tinha nenhum aviso visual de que a impressao estava
#          rodando ou tinha terminado (bug real reportado por
#          Benedito, corrigido nesta v1.1.0). Com 2+ pares, usuario
#          escolhe em selecionar_propriedade_produtor.html e o
#          "proximo" e a rota de confirmacao (nao mais a de PDF
#          direto).
#       2. /produtor/brincos-disponiveis/confirmar?id_propriedade=X
#          - tela com Propriedade/Produtor em bloco readonly +
#          botao "Imprimir" (abre o PDF em nova aba via JS, com
#          aviso "Gerando..."/"PDF gerado" no proprio botao).
#       3. /produtor/brincos-disponiveis/pdf?id_propriedade=X -
#          gera e devolve o PDF (PADRAO REUTILIZAVEL No2) com UMA
#          SECAO POR LOTE com saldo > 0 (tb_3007_brincos_entrada),
#          ordenados por id, cada secao no MESMO formato do PDF
#          individual do Relatorio N.Fiscais (mini-cabecalho +
#          tabela Ind/Codigo dos disponiveis + subtotal), em
#          fluxo CONTINUO (sem quebra de pagina forcada entre
#          lotes) e SEM total geral consolidado no fim - decisao
#          de Benedito, confirmada pelo relatorio real do GERAS
#          (Sessao 044).
#
#     REGRAS DE NEGOCIO (fechadas com Benedito, Sessao 044):
#       - So entram lotes com saldo > 0 (tem brinco disponivel).
#       - Disponivel = tb_7017_entrada_brincos_rfid com
#         saida_gta/saida_origem em branco (mesmo filtro do
#         Relatorio N.Fiscais).
#       - SISBOV sempre puro, 15 digitos, SEM digito
#         verificador/hifen.
#       - Uso de auditoria (Benedito): brinco antigo ainda
#         disponivel precisa ter motivo rastreavel (cancelamento
#         ou reidentificacao, ambos com justificativa) - nao afeta
#         a query desta tela, so o contexto de por que ela existe.
#
#     Fornecedor buscado em lote via consulta separada em schema
#     public (tb_1021), evitando N+1 (1 query so, dict por id).
#
#     v1.0.0: Criacao (Sessao 044, 02/09/2026, 14:35 -03).
#     v1.1.0: Sessao 044 (02/09/2026, 14:53 -03) - Bug real (UX)
#         reportado por Benedito: com 1 par so, o fluxo ia direto
#         para o download do PDF, sem NENHUM aviso visual de que a
#         impressao estava rodando/tinha terminado. Corrigido:
#         nova rota /confirmar sempre exibida antes do PDF (mesmo
#         com 1 par), com botao "Imprimir" explicito + aviso de
#         status. Rota /pdf mantida igual (so passa a ser chamada
#         a partir da tela de confirmacao, nunca mais direto do
#         /iniciar).
#     v1.2.0: Sessao 044 (02/09/2026, 15:11 -03) - Cadeia de
#         navegacao "Voltar" corrigida (Benedito, teste real):
#         Confirmar -> Voltar -> Selecionar Propriedade (quando
#         houve mais de 1 par) -> Voltar -> Hub de Brincos. Rota
#         /confirmar passa a calcular url_voltar dinamicamente
#         (reconsulta buscar_pares_propriedade_produtor: 2+ pares
#         -> volta para /iniciar; 1 par so -> volta direto pro Hub,
#         ja que neste caso nenhuma tela de selecao foi mostrada).
#     v1.3.0: Sessao 044 (02/09/2026, 16:00 -03) - Ultima perna da
#         cadeia corrigida: as chamadas a
#         selecionar_propriedade_produtor.html agora passam
#         voltar='/produtor/hub/brincos' - o template compartilhado
#         corrigido (v1.1.0) precisa dessa variavel para nao cair
#         no default '/produtor/home'. Mesma correcao aplicada em
#         todos os routers do Hub de Brincos nesta sessao.
#     v1.4.0: Sessao 091 (08/10/2026, 18:30 -03) - FAZENDA EM USO (Regra de Ouro #13):
#         Com fazenda em uso a tela "Selecionar Propriedade" e pulada: o iniciar()
#         abre direto a tela do modulo. O Voltar vai ao Hub de Brincos (sem passar pela
#         selecao). TRAVA: Propriedade da URL diferente da fazenda em uso e negada
#         (nunca le nem grava). Sem fazenda em uso o comportamento anterior permanece.
#         Leitura e gravacao dos dados intactas. REVERSAO: devolver a versao anterior.
# =========================================================

from types import SimpleNamespace

from flask import Blueprint, render_template, request, redirect, session, send_file
from sqlalchemy.orm import Session
from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime

from backend.database import engine
from backend.models import Propriedade, Produtor
from backend.models.tb_1021_fabricantes_brincos import Fabricante
from backend.models.tb_3007_brincos_entrada import BrincoEntrada
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.brincos_propriedade import propriedade_do_usuario_brincos, tela_erro_brincos
from backend.utils.pdf_helper import link_callback_pdf


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
brincos_disponiveis = Blueprint('brincos_disponiveis', __name__)


# -------------------------------------------------------
# v1.4.0 - TRAVA DA FAZENDA EM USO (Regra de Ouro #13): a Propriedade da URL
# difere da fazenda em uso (trocada em outra aba)? Sem fazenda em uso, ou
# valor que nao e numero, devolve False (as validacoes de cada tela
# continuam valendo).
# -------------------------------------------------------
def _fora_da_fazenda_em_uso(id_propriedade):
    try:
        id_int = int(id_propriedade)
    except (TypeError, ValueError):
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares)
    return par_em_uso is not None and int(par_em_uso.id_propriedade) != id_int


# -------------------------------------------------------
# Rota: GET /produtor/brincos-disponiveis/iniciar - ponto de
# partida, MESMO padrao ja usado em brincos_relatorio_nfiscais.
# -------------------------------------------------------
@brincos_disponiveis.route('/produtor/brincos-disponiveis/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            titulo='Selecionar Propriedade',
            proximo='/produtor/brincos-disponiveis/confirmar',
            campo_propriedade='id_propriedade',
            voltar='/produtor/hub/brincos',
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='brincos',
        )

    # v1.4.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/brincos-disponiveis/confirmar?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/brincos-disponiveis/confirmar?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        titulo='Selecionar Propriedade',
        proximo='/produtor/brincos-disponiveis/confirmar',
        campo_propriedade='id_propriedade',
        voltar='/produtor/hub/brincos',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )


# -------------------------------------------------------
# Funcao auxiliar: busca os dados de cabecalho (Propriedade +
# Produtor vinculado) - copia curta local (PADRAO REUTILIZAVEL
# No1), mesma usada em brincos_relatorio_nfiscais.py.
# -------------------------------------------------------
def _buscar_dados_cabecalho(id_produtor, id_propriedade):
    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade)) if id_propriedade else None
        produtor    = db.get(Produtor, int(id_produtor)) if id_produtor else None

        if not propriedade or not produtor:
            return None

        return SimpleNamespace(
            propriedade_nome = propriedade.nome,
            municipio        = propriedade.municipio,
            uf               = propriedade.uf,
            produtor_nome    = produtor.nome,
        )


# -------------------------------------------------------
# Funcao auxiliar: dict {id_fabricante: nome}, 1 query so (evita
# N+1 ao montar N lotes na mesma pagina).
# -------------------------------------------------------
def _mapa_fabricantes():
    with Session(engine) as db:
        fabricantes = db.query(Fabricante).all()
        return {f.id: f.nome for f in fabricantes}


# -------------------------------------------------------
# Rota: GET /produtor/brincos-disponiveis/confirmar?id_propriedade=X
# - tela de confirmacao (Propriedade/Produtor readonly + botao
# Imprimir), sempre exibida antes do PDF (mesmo com 1 par so - ver
# changelog v1.1.0).
# -------------------------------------------------------
@brincos_disponiveis.route('/produtor/brincos-disponiveis/confirmar')
def confirmar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if _fora_da_fazenda_em_uso(id_propriedade):
        return redirect('/produtor/brincos-disponiveis/iniciar')
    if not id_propriedade or not propriedade_do_usuario_brincos(id_propriedade):
        return tela_erro_brincos()

    cabecalho = _buscar_dados_cabecalho(session['id_produtor'], id_propriedade)
    if cabecalho is None:
        return tela_erro_brincos()

    # "Voltar" desta tela depende de quantos pares Propriedade/Produtor
    # o usuario tem: se so 1 (nenhuma tela de selecao foi mostrada),
    # volta direto pro Hub; se 2+ (tela de selecao FOI mostrada antes
    # desta), volta para ela via /iniciar (mesma logica de resolucao
    # roda de novo e re-renderiza a lista) - cadeia correta confirmada
    # por Benedito, Sessao 044: Confirmar -> Selecionar Propriedade ->
    # Hub de Brincos.
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        url_voltar = '/produtor/brincos-disponiveis/iniciar'
    else:
        url_voltar = '/produtor/hub/brincos'

    return render_template(
        'produtor/brincos_disponiveis_confirmar.html',
        cabecalho=cabecalho,
        url_pdf=f'/produtor/brincos-disponiveis/pdf?id_propriedade={id_propriedade}',
        url_voltar=url_voltar,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )


# -------------------------------------------------------
# Rota: GET /produtor/brincos-disponiveis/pdf?id_propriedade=X -
# gera o PDF com 1 secao por lote com saldo > 0.
# -------------------------------------------------------
@brincos_disponiveis.route('/produtor/brincos-disponiveis/pdf')
def pdf():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if _fora_da_fazenda_em_uso(id_propriedade):
        return redirect('/produtor/brincos-disponiveis/iniciar')
    if not id_propriedade or not propriedade_do_usuario_brincos(id_propriedade):
        return tela_erro_brincos()

    cabecalho = _buscar_dados_cabecalho(session['id_produtor'], id_propriedade)
    if cabecalho is None:
        return tela_erro_brincos()

    mapa_fabricantes = _mapa_fabricantes()

    with get_db_produtor(session['id_produtor']) as db:
        lotes_db = (
            db.query(BrincoEntrada)
            .filter_by(id_propriedade=int(id_propriedade))
            .filter(BrincoEntrada.saldo > 0)
            .order_by(BrincoEntrada.id)
            .all()
        )

        secoes = []
        for lote in lotes_db:
            disponiveis_db = (
                db.query(EntradaBrincoRfid)
                .filter_by(id_lote_entrada=lote.id)
                .filter(EntradaBrincoRfid.saida_gta.is_(None))
                .filter(EntradaBrincoRfid.saida_origem.is_(None))
                .order_by(EntradaBrincoRfid.sisbov)
                .all()
            )
            sisbovs = [item.sisbov for item in disponiveis_db]

            linhas = []
            for i in range(0, len(sisbovs), 4):
                grupo = sisbovs[i:i + 4]
                linhas.append([(i + off + 1, s) for off, s in enumerate(grupo)])

            secoes.append(SimpleNamespace(
                nota_fiscal      = lote.nota_fiscal,
                qtde_entrada     = lote.qtde_entrada,
                fornecedor_nome  = mapa_fabricantes.get(lote.id_fabricante, '-'),
                responsavel_nome = lote.responsavel.nome if lote.responsavel else '-',
                linhas           = linhas,
                total_disponivel = len(sisbovs),
            ))

    html = render_template(
        'produtor/brincos_disponiveis_pdf.html',
        cabecalho=cabecalho,
        secoes=secoes,
        data_impressao=datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
    )

    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer, link_callback=link_callback_pdf)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='brincos_disponiveis.pdf',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\brincos_disponiveis.py
# =========================================================