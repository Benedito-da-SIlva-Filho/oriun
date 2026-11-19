# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\brincos_saidas.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-03 11:32 -03
# ATUALIZADO EM: 2026-10-08 18:30 -03
# VERSAO: 1.4.0
# v1.4.0: Sessao 123 (2026-11-13 20:10 -03) - AUDITORIA ETAPA 6 (leitura a fundo): Propriedade conferida (numero + e do usuario) e mensagens com norte em tela do Orion (antes: erro 500 / cabecalho de outra Propriedade / texto solto). REVERSAO: .bak_antes_etapa6e.
#
# DESCRICAO:
#     Modulo "Brincos Saídas" do Hub de Brincos - 7o e ultimo card,
#     fecha o Hub. Alinhamento de negocio fechado na Sessao 045, a
#     partir do relatorio real de referencia trazido por Benedito
#     (relatorio_de_saidas.pdf, telas do GERAS "Brincos Saídas").
#
#     Base de dados: tb_3008_brincos_saida (todo brinco que ja
#     saiu do estoque - seja por uso em animal via futura
#     Brincagem/GTA, seja por Cancelamento). Cadeia de
#     rastreabilidade ate o lote de origem via
#     id_lote_entrada -> tb_3007_brincos_entrada (usado so para
#     montar o cabecalho de cada secao do PDF - Sequencia,
#     Solicitacao, Nota Fiscal, Qtde Entrada, Data Entrada, Sisbov
#     Inicial/Final do LOTE INTEIRO, nao so dos itens filtrados).
#
#     Fluxo de 3 rotas (PADRAO REUTILIZAVEL No1 + No2, mesma
#     familia de brincos_disponiveis.py - PDF continuo, sem grid
#     intermediaria, sem quebra de pagina forcada entre lotes):
#       1. /produtor/brincos-saidas/iniciar - resolve Propriedade
#          E Produtor.
#       2. /produtor/brincos-saidas/filtro?id_propriedade=X - tela
#          com 3 opcoes de Tipo de Relatorio (radio) + campos de
#          Data De/Ate (aparecem so quando "Por Periodo" e
#          escolhido, via JS) + botao Imprimir.
#       3. /produtor/brincos-saidas/pdf?id_propriedade=X&tipo=...
#          - gera o PDF, 1 secao por Lote de origem que teve pelo
#          menos 1 brinco saido dentro do filtro escolhido.
#
#     3 MODOS DE RELATORIO (fechados com Benedito, Sessao 045):
#       - 'sequencial' (default) - TODOS os brincos que ja sairam
#         do lote, sem filtro de motivo/data. Layout: grid simples
#         de 5 colunas, so o numero do SISBOV (replica exata do
#         relatorio_de_saidas.pdf trazido por Benedito) - o motivo
#         individual nao importa tanto aqui, e um raio-x do lote
#         inteiro.
#       - 'cancelados' - filtra so os 4 motivos de cancelamento
#         (DANIFICADO/EXTRAVIADO/INATIVADO/VENDIDO, mesma lista
#         MOTIVOS_CANCELAMENTO de brincos_cancelamento.py -
#         reaproveitada daqui, evita duplicar a lista em 2 lugares).
#         Layout: TABELA com 3 colunas (SISBOV | Motivo | Data
#         Saida) - aqui o motivo de cada brinco E a informacao
#         principal (proposito de auditoria), por isso a grid
#         simples nao serve.
#       - 'periodo' - filtra por data_saida dentro do intervalo
#         De/Ate escolhido pelo Usuario (sem filtro de motivo -
#         pega uso em animal E cancelamento juntos). Layout: grid
#         simples de 5 colunas, IGUAL ao modo 'sequencial' -
#         CORRIGIDO NA v1.1.0, ver changelog abaixo (o filtro de
#         data ja restringe o resultado; nao precisa da tabela de
#         Motivo/Data para isso).
#
#     Em TODOS os 3 modos, o agrupamento por Lote/Solicitacao e
#     mantido (decisao explicita de Benedito, Sessao 045: "sempre
#     agrupado por lote, independente do filtro").
#
#     v1.0.0: Criacao do modulo (Sessao 045, 03/09/2026, 11:32 -03),
#         a partir do alinhamento de negocio fechado em conversa e
#         do relatorio real de referencia (relatorio_de_saidas.pdf)
#         trazido por Benedito.
#     v1.1.0: Sessao 045 (03/09/2026, 11:55 -03) - Ajuste pedido por
#         Benedito, em teste real: o modo 'periodo' deixa de usar o
#         layout de tabela (SISBOV | Motivo | Data Saida) e passa a
#         usar o MESMO layout de grid simples do modo 'sequencial'
#         (so o SISBOV, 5 colunas). Motivo: o filtro de data ja
#         restringe o resultado ao intervalo escolhido, entao a
#         apresentacao pode ficar simples igual ao Sequencial - a
#         tabela com Motivo/Data continua exclusiva do modo
#         'cancelados', onde o motivo individual de cada brinco
#         ainda e a informacao principal (proposito de auditoria).
#     v1.2.0: Sessao 045 (03/09/2026, 12:15 -03) - BUG REAL
#         reportado por Benedito em teste (PDF gerado sem mostrar
#         qual periodo havia sido filtrado - so aparecia "Por
#         Período" solto no subtitulo). Corrigido: no modo
#         'periodo', o subtitulo do PDF agora inclui o intervalo de
#         datas escolhido pelo Usuario, formatado em pt-BR (ex.:
#         "Por Período (01/09/2026 a 02/09/2026)") - montado na
#         propria rota /pdf, a partir dos parametros data_inicio/
#         data_fim recebidos na querystring.
#     v1.3.0: Sessao 091 (08/10/2026, 18:30 -03) - FAZENDA EM USO (Regra de Ouro #13):
#         Com fazenda em uso a tela "Selecionar Propriedade" e pulada: o iniciar()
#         abre direto a tela do modulo. O Voltar vai ao Hub de Brincos (sem passar pela
#         selecao). TRAVA: Propriedade da URL diferente da fazenda em uso e negada
#         (nunca le nem grava). Sem fazenda em uso o comportamento anterior permanece.
#         Leitura e gravacao dos dados intactas. REVERSAO: devolver a versao anterior.
# =========================================================

from types import SimpleNamespace
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, session, send_file
from sqlalchemy.orm import Session
from xhtml2pdf import pisa
from io import BytesIO

from backend.database import engine
from backend.models import Propriedade, Produtor
from backend.models.tb_3007_brincos_entrada import BrincoEntrada
from backend.models.tb_3008_brincos_saida import BrincoSaida
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.brincos_cancelamento import MOTIVOS_CANCELAMENTO
from backend.utils.multitenant import get_db_produtor
from backend.utils.brincos_propriedade import propriedade_do_usuario_brincos, tela_erro_brincos
from backend.utils.pdf_helper import link_callback_pdf


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
brincos_saidas = Blueprint('brincos_saidas', __name__)


# -------------------------------------------------------
# v1.3.0 - TRAVA DA FAZENDA EM USO (Regra de Ouro #13): a Propriedade da URL
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
# Rotulos amigaveis por tipo de relatorio - usados no titulo do
# PDF e como validacao dos valores aceitos na querystring.
# -------------------------------------------------------
TIPOS_RELATORIO = {
    'sequencial': 'Sequencial por Solicitação (Todos)',
    'cancelados': 'Só Cancelados',
    'periodo':    'Por Período',
}


# -------------------------------------------------------
# Funcao auxiliar: busca os dados de cabecalho (Propriedade +
# Produtor vinculado) - copia curta local (PADRAO REUTILIZAVEL
# No1), mesma usada nos demais modulos do Hub de Brincos.
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
# Funcao auxiliar: calcula a URL de "Voltar" para a tela de filtro,
# dependendo de quantos pares Propriedade/Produtor o usuario tem
# (Regra de Ouro No4 - nunca hardcoded). Mesma logica ja fechada em
# brincos_disponiveis.py / brincos_cancelamento.py.
# -------------------------------------------------------
def _url_voltar_pos_selecao():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return '/produtor/brincos-saidas/iniciar'
    return '/produtor/hub/brincos'


# -------------------------------------------------------
# Rota: GET /produtor/brincos-saidas/iniciar - ponto de partida,
# MESMO padrao ja usado nos demais modulos do Hub de Brincos
# (PADRAO REUTILIZAVEL No1).
# -------------------------------------------------------
@brincos_saidas.route('/produtor/brincos-saidas/iniciar')
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
            proximo='/produtor/brincos-saidas/filtro',
            campo_propriedade='id_propriedade',
            voltar='/produtor/hub/brincos',
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='brincos',
        )

    # v1.3.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/brincos-saidas/filtro?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/brincos-saidas/filtro?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        titulo='Selecionar Propriedade',
        proximo='/produtor/brincos-saidas/filtro',
        campo_propriedade='id_propriedade',
        voltar='/produtor/hub/brincos',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )


# -------------------------------------------------------
# Rota: GET /produtor/brincos-saidas/filtro?id_propriedade=X - tela
# de filtro (Tipo de Relatorio + Data De/Ate condicional).
# -------------------------------------------------------
@brincos_saidas.route('/produtor/brincos-saidas/filtro')
def filtro():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if _fora_da_fazenda_em_uso(id_propriedade):
        return redirect('/produtor/brincos-saidas/iniciar')
    if not id_propriedade or not propriedade_do_usuario_brincos(id_propriedade):
        return tela_erro_brincos()

    cabecalho = _buscar_dados_cabecalho(session['id_produtor'], id_propriedade)
    if cabecalho is None:
        return tela_erro_brincos()

    return render_template(
        'produtor/brincos_saidas_filtro.html',
        cabecalho=cabecalho,
        id_propriedade=id_propriedade,
        url_voltar=_url_voltar_pos_selecao(),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )


# -------------------------------------------------------
# Rota: GET /produtor/brincos-saidas/pdf?id_propriedade=X&tipo=...
# &data_inicio=AAAA-MM-DD&data_fim=AAAA-MM-DD - gera o PDF, 1
# secao por Lote que teve pelo menos 1 brinco saido dentro do
# filtro escolhido.
# -------------------------------------------------------
@brincos_saidas.route('/produtor/brincos-saidas/pdf')
def pdf():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if _fora_da_fazenda_em_uso(id_propriedade):
        return redirect('/produtor/brincos-saidas/iniciar')
    if not id_propriedade or not propriedade_do_usuario_brincos(id_propriedade):
        return tela_erro_brincos()

    cabecalho = _buscar_dados_cabecalho(session['id_produtor'], id_propriedade)
    if cabecalho is None:
        return tela_erro_brincos()

    tipo        = request.args.get('tipo', 'sequencial')
    data_inicio = request.args.get('data_inicio', '')
    data_fim    = request.args.get('data_fim', '')

    if tipo not in TIPOS_RELATORIO:
        tipo = 'sequencial'

    with get_db_produtor(session['id_produtor']) as db:
        query = db.query(BrincoSaida).filter_by(id_propriedade=int(id_propriedade))

        if tipo == 'cancelados':
            query = query.filter(BrincoSaida.origem.in_(MOTIVOS_CANCELAMENTO))
        elif tipo == 'periodo':
            if data_inicio:
                query = query.filter(BrincoSaida.data_saida >= data_inicio)
            if data_fim:
                query = query.filter(BrincoSaida.data_saida <= data_fim)

        saidas = query.order_by(BrincoSaida.id_lote_entrada, BrincoSaida.sisbov).all()

        # Monta o rotulo do subtitulo do PDF - no modo 'periodo',
        # inclui o intervalo de datas escolhido pelo Usuario (sem
        # isso, o PDF nao mostrava QUAL periodo foi filtrado - bug
        # real reportado por Benedito em teste).
        titulo_relatorio = TIPOS_RELATORIO[tipo]
        if tipo == 'periodo':
            def _formatar_data_br(data_iso):
                try:
                    return datetime.strptime(data_iso, '%Y-%m-%d').strftime('%d/%m/%Y')
                except (ValueError, TypeError):
                    return data_iso or '?'

            titulo_relatorio = (
                f'{titulo_relatorio} '
                f'({_formatar_data_br(data_inicio)} a {_formatar_data_br(data_fim)})'
            )

        # Agrupa os resultados por Lote de origem (id_lote_entrada)
        itens_por_lote = {}
        for saida in saidas:
            itens_por_lote.setdefault(saida.id_lote_entrada, []).append(saida)

        # Busca os dados de cabecalho de cada Lote afetado, ordenados
        # por id (ordem de entrada - mesma convencao ja usada no
        # Relatorio N.Fiscais).
        ids_lote = list(itens_por_lote.keys())
        lotes_db = (
            db.query(BrincoEntrada)
            .filter(BrincoEntrada.id.in_(ids_lote))
            .order_by(BrincoEntrada.id)
            .all()
            if ids_lote else []
        )

        secoes      = []
        total_geral = 0

        for lote in lotes_db:
            itens = itens_por_lote.get(lote.id, [])

            secao_base = dict(
                sequencia       = lote.sequencia,
                solicitacao_nro = lote.solicitacao_nro,
                nota_fiscal     = lote.nota_fiscal,
                qtde_entrada    = lote.qtde_entrada,
                data_entrada    = lote.data_entrada.strftime('%d/%m/%Y') if lote.data_entrada else '-',
                codigo_inicial  = lote.codigo_inicial,
                codigo_final    = lote.codigo_final,
                total_secao     = len(itens),
            )

            if tipo == 'cancelados':
                # Layout de tabela: SISBOV | Motivo | Data Saida -
                # so aqui o motivo individual de cada brinco e a
                # informacao principal (Benedito, Sessao 045).
                linhas_tabela = sorted(
                    (SimpleNamespace(
                        sisbov=item.sisbov,
                        motivo=item.origem,
                        data_saida=item.data_saida.strftime('%d/%m/%Y') if item.data_saida else '-',
                    ) for item in itens),
                    key=lambda x: x.sisbov,
                )
                secao_base['modo_tabela']    = True
                secao_base['linhas_tabela']  = linhas_tabela
            else:
                # Layout simples: grid de 5 colunas, so o SISBOV -
                # usado em 'sequencial' e, a pedido de Benedito
                # (Sessao 045, ajuste pos-entrega), tambem em
                # 'periodo': o filtro de data ja restringe o
                # resultado, entao a apresentacao pode ficar igual
                # ao modo Sequencial (mesma listagem simples).
                sisbovs = sorted(item.sisbov for item in itens)
                linhas  = [sisbovs[i:i + 5] for i in range(0, len(sisbovs), 5)]
                secao_base['modo_tabela'] = False
                secao_base['linhas']      = linhas

            secoes.append(SimpleNamespace(**secao_base))
            total_geral += len(itens)

    html = render_template(
        'produtor/brincos_saidas_pdf.html',
        cabecalho=cabecalho,
        secoes=secoes,
        total_geral=total_geral,
        titulo_relatorio=titulo_relatorio,
        modo_tabela=(tipo == 'cancelados'),
        data_impressao=datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
    )

    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer, link_callback=link_callback_pdf)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='brincos_saidas.pdf',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\brincos_saidas.py
# =========================================================