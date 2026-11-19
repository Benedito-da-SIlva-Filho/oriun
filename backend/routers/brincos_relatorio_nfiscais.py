# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\brincos_relatorio_nfiscais.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-02 10:00 -03
# ATUALIZADO EM: 2026-10-08 18:30 -03
# VERSAO: 1.3.0
# v1.3.0: Sessao 123 (2026-11-13 20:10 -03) - AUDITORIA ETAPA 6 (leitura a fundo): lista e PDF conferem a Propriedade (numero + e do usuario + a do lote); mensagens com norte (antes: erro 500 / cabecalho de outra Propriedade / lote de outra Propriedade abria). REVERSAO: .bak_antes_etapa6e.
#
# DESCRICAO:
#     Modulo "Relatorio N.Fiscais" do Hub de Brincos (Sessao 044),
#     ultimo dos 7 cards do Hub, seguindo a ordem ja combinada
#     com Benedito (Fornecedor -> Entrada -> Relatorio Resumo ->
#     este). Mesmo padrao arquitetural ja fechado em
#     brincos_entrada.py e brincos_relatorio_resumo.py:
#
#       1. /produtor/brincos-relatorio-nfiscais/iniciar - resolve
#          Propriedade E Produtor, reaproveitando
#          auth.buscar_pares_propriedade_produtor() (PADRAO
#          REUTILIZAVEL No1, sem duplicacao de logica).
#       2. /produtor/brincos-relatorio-nfiscais/listar?id_propriedade=X
#          - grid com 1 linha por lote de tb_3007_brincos_entrada
#          da Propriedade escolhida, ordenada por id (ordem de
#          entrada - decisao de Benedito). Colunas: Codigo Inicial,
#          Codigo Final, N.Fiscal, Emissao (data_nf), Solicitacao
#          (solicitacao_nro, exibido com zero a esquerda),
#          Data (solicitacao_data), Entrada (qtde_entrada), Saida
#          (qtde_saida), Saldo (saldo) - estes 3 ultimos ja vem
#          prontos da propria tb_3007, sem necessidade de juncao
#          com tb_3008/tb_7017 (confirmado por Benedito). Cada
#          linha tem botao "Imprimir" que abre o PDF individual
#          daquele lote em nova aba.
#       3. /produtor/brincos-relatorio-nfiscais/pdf/<id_lote_entrada>
#          - gera e devolve o PDF (PADRAO REUTILIZAVEL No2:
#          xhtml2pdf, download forcado) com a relacao individual
#          dos brincos DISPONIVEIS daquele lote, lendo
#          tb_7017_entrada_brincos_rfid filtrada por
#          id_lote_entrada = lote.id AND saida_gta IS NULL AND
#          saida_origem IS NULL (livre para uso). Fornecedor via
#          consulta separada em schema public na tb_1021 (sem
#          relationship confirmado BrincoEntrada->Fabricante,
#          mesma regra ja aplicada no Relatorio Resumo).
#          Responsavel via relationship ja existente
#          BrincoEntrada.responsavel (Usuario.nome).
#
#     REGRAS DE NEGOCIO (fechadas com Benedito, Sessao 044):
#       - SISBOV exibido PURO, 15 digitos, SEM digito verificador
#         e SEM hifen (bases antigas do GERAS usavam digito
#         verificador separado - o Orion NAO usa mais, decisao ja
#         fechada anteriormente e reconfirmada nesta sessao).
#       - Solicitacao (solicitacao_nro) e so formatacao de
#         exibicao com zero a esquerda (6 digitos) - campo
#         continua integer no banco, sem mudanca de tipo.
#       - "Data" da grid = solicitacao_data (nao data_entrada).
#       - Grid nao tem filtro de periodo (diferente do Relatorio
#         Resumo) - lista TODOS os lotes da Propriedade escolhida.
#
#     v1.1.0: Sessao 044 (02/09/2026, 16:00 -03) - Cadeia de
#         navegacao "Voltar" corrigida (Benedito, teste real,
#         mesma correcao aplicada em todos os modulos do Hub de
#         Brincos): (1) chamadas a selecionar_propriedade_produtor.
#         html agora passam voltar='/produtor/hub/brincos'; (2)
#         nova funcao _url_voltar_listagem() calcula dinamicamente
#         o destino do Voltar da grid: volta para
#         /produtor/brincos-relatorio-nfiscais/iniciar (re-exibe a
#         Selecao de Propriedade) se o usuario tem 2+ pares, ou
#         direto para o Hub se tem so 1 par.
#     v1.2.0: Sessao 091 (08/10/2026, 18:30 -03) - FAZENDA EM USO (Regra de Ouro #13):
#         Com fazenda em uso a tela "Selecionar Propriedade" e pulada: o iniciar()
#         abre direto a tela do modulo. O Voltar vai ao Hub de Brincos (sem passar pela
#         selecao). TRAVA: Propriedade da URL diferente da fazenda em uso e negada
#         (nunca le nem grava). Sem fazenda em uso o comportamento anterior permanece.
#         Leitura e gravacao dos dados intactas. REVERSAO: devolver a versao anterior.
# =========================================================

from datetime import datetime
from io import BytesIO
from types import SimpleNamespace

from flask import Blueprint, render_template, request, redirect, session, send_file
from sqlalchemy.orm import Session
from xhtml2pdf import pisa

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
brincos_relatorio_nfiscais = Blueprint('brincos_relatorio_nfiscais', __name__)


# -------------------------------------------------------
# v1.2.0 - TRAVA DA FAZENDA EM USO (Regra de Ouro #13): a Propriedade da URL
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
# Tamanho fixo do numero SISBOV (mesmo padrao de
# brincos_entrada.py - 15 digitos, sem digito verificador).
# -------------------------------------------------------
TAMANHO_SISBOV = 15


# -------------------------------------------------------
# Rota: GET /produtor/brincos-relatorio-nfiscais/iniciar - ponto
# de partida do fluxo, MESMO padrao ja usado em
# brincos_entrada.iniciar().
# -------------------------------------------------------
@brincos_relatorio_nfiscais.route('/produtor/brincos-relatorio-nfiscais/iniciar')
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
            proximo='/produtor/brincos-relatorio-nfiscais/listar',
            campo_propriedade='id_propriedade',
            voltar='/produtor/hub/brincos',
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='brincos',
        )

    # v1.2.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/brincos-relatorio-nfiscais/listar?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/brincos-relatorio-nfiscais/listar?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        titulo='Selecionar Propriedade',
        proximo='/produtor/brincos-relatorio-nfiscais/listar',
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
# Produtor vinculado) para exibicao/conferencia na tela - copia
# curta local, mesmo padrao repetido em brincos_entrada.py e
# brincos_relatorio_resumo.py (PADRAO REUTILIZAVEL No1).
# -------------------------------------------------------
def _buscar_dados_cabecalho(id_produtor, id_propriedade):
    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade)) if id_propriedade else None
        produtor    = db.get(Produtor, int(id_produtor)) if id_produtor else None

        if not propriedade or not produtor:
            return None

        return SimpleNamespace(
            id_propriedade   = propriedade.id,
            propriedade_nome = propriedade.nome,
            municipio        = propriedade.municipio,
            uf               = propriedade.uf,
            id_produtor      = produtor.id,
            produtor_nome    = produtor.nome,
            cpf_produtor     = produtor.cpf_cnpj,
        )


# -------------------------------------------------------
# Funcao auxiliar: nome do Fabricante a partir do id_fabricante -
# consulta separada em schema public, SEM assumir relationship
# (Regra de Ouro - mesma decisao ja fechada no Relatorio Resumo).
# -------------------------------------------------------
def _buscar_nome_fabricante(id_fabricante):
    if not id_fabricante:
        return '-'
    with Session(engine) as db:
        fabricante = db.get(Fabricante, int(id_fabricante))
        return fabricante.nome if fabricante else '-'


# -------------------------------------------------------
# Rota: GET /produtor/brincos-relatorio-nfiscais/listar?id_propriedade=X
# - grid com todos os lotes (Notas Fiscais) da Propriedade,
# ordenados por id (ordem de entrada).
# -------------------------------------------------------
# -------------------------------------------------------
# Funcao auxiliar: URL de "Voltar" da tela de listagem - volta
# para a tela de Selecionar Propriedade se o usuario tem 2+ pares
# Propriedade/Produtor (ela foi mostrada antes), ou direto para o
# Hub de Brincos se so tem 1 par - mesma logica ja aplicada em
# brincos_entrada.py e brincos_disponiveis.py (Sessao 044).
# -------------------------------------------------------
def _url_voltar_listagem():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return '/produtor/brincos-relatorio-nfiscais/iniciar'
    return '/produtor/hub/brincos'


@brincos_relatorio_nfiscais.route('/produtor/brincos-relatorio-nfiscais/listar')
def listar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    url_voltar = _url_voltar_listagem()
    id_propriedade = request.args.get('id_propriedade', '')
    if _fora_da_fazenda_em_uso(id_propriedade):
        return redirect('/produtor/brincos-relatorio-nfiscais/iniciar')

    if not id_propriedade or not propriedade_do_usuario_brincos(id_propriedade):
        return render_template(
            'produtor/brincos_relatorio_nfiscais_lista.html',
            erro='Propriedade não informada ou inválida. Reinicie o fluxo pelo Hub de Brincos.',
            cabecalho=None,
            lotes=[],
            url_voltar=url_voltar,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='brincos',
        )

    cabecalho = _buscar_dados_cabecalho(session['id_produtor'], id_propriedade)

    if cabecalho is None:
        return render_template(
            'produtor/brincos_relatorio_nfiscais_lista.html',
            erro='Propriedade ou Produtor não encontrado(s). Reinicie o fluxo pelo Hub de Brincos.',
            cabecalho=None,
            lotes=[],
            url_voltar=url_voltar,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='brincos',
        )

    with get_db_produtor(session['id_produtor']) as db:
        lotes_db = (
            db.query(BrincoEntrada)
            .filter_by(id_propriedade=int(id_propriedade))
            .order_by(BrincoEntrada.id)
            .all()
        )

        lotes = []
        for lote in lotes_db:
            lotes.append(SimpleNamespace(
                id                = lote.id,
                codigo_inicial    = lote.codigo_inicial,
                codigo_final      = lote.codigo_final,
                nota_fiscal       = lote.nota_fiscal,
                data_nf           = lote.data_nf,
                solicitacao_nro   = str(lote.solicitacao_nro).zfill(6) if lote.solicitacao_nro is not None else '-',
                solicitacao_data  = lote.solicitacao_data,
                qtde_entrada      = lote.qtde_entrada,
                qtde_saida        = lote.qtde_saida,
                saldo             = lote.saldo,
            ))

    return render_template(
        'produtor/brincos_relatorio_nfiscais_lista.html',
        erro=None,
        cabecalho=cabecalho,
        lotes=lotes,
        url_voltar=url_voltar,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )


# -------------------------------------------------------
# Rota: GET /produtor/brincos-relatorio-nfiscais/pdf/<id_lote_entrada>
# - gera o PDF individual do lote (relacao de brincos disponiveis),
# PADRAO REUTILIZAVEL No2 (xhtml2pdf, download forcado, testado
# internamente antes de qualquer entrega).
# -------------------------------------------------------
@brincos_relatorio_nfiscais.route('/produtor/brincos-relatorio-nfiscais/pdf/<int:id_lote_entrada>')
def pdf(id_lote_entrada):
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    with get_db_produtor(session['id_produtor']) as db:
        lote = db.get(BrincoEntrada, id_lote_entrada)

        if lote is None or not propriedade_do_usuario_brincos(lote.id_propriedade):
            return tela_erro_brincos('Não encontramos este Lote de Entrada de Brincos na sua conta. Volte à lista do Relatório de NFs e escolha o lote de novo; se repetir, avise a Consiste.')

        disponiveis_db = (
            db.query(EntradaBrincoRfid)
            .filter_by(id_lote_entrada=lote.id)
            .filter(EntradaBrincoRfid.saida_gta.is_(None))
            .filter(EntradaBrincoRfid.saida_origem.is_(None))
            .order_by(EntradaBrincoRfid.sisbov)
            .all()
        )

        sisbovs = [item.sisbov for item in disponiveis_db]
        responsavel_nome = lote.responsavel.nome if lote.responsavel else '-'

    cabecalho = _buscar_dados_cabecalho(session['id_produtor'], lote.id_propriedade)
    if cabecalho is None:
        return tela_erro_brincos()
    fornecedor_nome = _buscar_nome_fabricante(lote.id_fabricante)

    # Agrupa os SISBOVs em linhas de 4 colunas (Ind/Codigo x4),
    # mesmo layout do relatorio impresso do GERAS.
    linhas = []
    for i in range(0, len(sisbovs), 4):
        grupo = sisbovs[i:i + 4]
        linha = []
        for offset, sisbov in enumerate(grupo):
            linha.append((i + offset + 1, sisbov))
        linhas.append(linha)

    html = render_template(
        'produtor/brincos_relatorio_nfiscais_pdf.html',
        cabecalho=cabecalho,
        lote=lote,
        fornecedor_nome=fornecedor_nome,
        responsavel_nome=responsavel_nome,
        linhas=linhas,
        total_disponivel=len(sisbovs),
        data_impressao=datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
    )

    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer, link_callback=link_callback_pdf)
    buffer.seek(0)

    nome_arquivo = f'brincos_nf_{lote.nota_fiscal}.pdf'

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=nome_arquivo,
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\brincos_relatorio_nfiscais.py
# =========================================================