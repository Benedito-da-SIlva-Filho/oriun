# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\brincos_relatorio_resumo.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-01 11:50 -03
# ATUALIZADO EM: 2026-10-08 18:30 -03
# VERSAO: 1.3.0
# v1.3.0: Sessao 123 (2026-11-13 20:10 -03) - AUDITORIA ETAPA 6 (leitura a fundo): Propriedade conferida (numero + e do usuario) no filtro e no gerar; totais tratam valor vazio como 0 (antes: erro 500 / cabecalho de outra Propriedade). REVERSAO: .bak_antes_etapa6e.
#
# DESCRICAO:
#     Relatorio Resumo de Entrada de Brincos (Hub de Brincos),
#     sintese de tb_3007_brincos_entrada num periodo escolhido -
#     mesmo processo trazido por Benedito nas imagens do GERAS
#     (tela "Registro de Entrada de Brincos" com filtro de
#     Fazenda/Produtor/Periodo, gerando um PDF com 1 linha por
#     lote/Nota Fiscal e totais no rodape).
#
#     Fluxo de telas, MESMO padrao ja fechado em brincos_entrada.py:
#       1. /produtor/brincos-relatorio-resumo/iniciar - resolve
#          Propriedade E Produtor via
#          auth.buscar_pares_propriedade_produtor() (0 pares ->
#          erro; 1 par -> segue direto; 2+ -> tela de selecao).
#       2. /produtor/brincos-relatorio-resumo/filtro?id_propriedade=X
#          - formulario com Propriedade/Produtor SO PARA
#          CONFERENCIA (ja resolvidos no passo 1 - decisao de
#          Benedito, Sessao 043: NAO repetir os dropdowns livres
#          de Fazenda/Produtor do GERAS) e 2 campos editaveis:
#          Data Inicio / Data Fim.
#       3. /produtor/brincos-relatorio-resumo/gerar - POST, valida
#          Data Inicio <= Data Fim, busca os lotes de tb_3007 no
#          periodo (schema do Produtor logado), gera o PDF
#          (xhtml2pdf, MESMO padrao ja usado em
#          produtores.py/relatorio_pdf()) e devolve como DOWNLOAD
#          FORCADO (decisao de Benedito, Sessao 043 - mesmo padrao
#          do Relatorio de Produtor).
#
#     REGRAS DE NEGOCIO (fechadas com Benedito, Sessao 043):
#       - Filtro por tb_3007.data_entrada, entre Data Inicio e
#         Data Fim, AMBAS INCLUSIVE.
#       - Data Inicio DEVE ser <= Data Fim (validado no servidor).
#       - Datas nascem VAZIAS na tela (usuario preenche sempre,
#         sem default de periodo).
#       - 1 linha por lote (cada linha de tb_3007), ordenado por
#         data_entrada, depois sequencia.
#       - Coluna Fornecedor: nome do Fabricante (tb_1021), buscado
#         por id_fabricante - schema PUBLIC, MESMA logica de
#         consulta separada ja usada em
#         brincos_entrada._listar_fabricantes_ativos() (nao ha
#         relationship confirmado de BrincoEntrada->Fabricante,
#         entao a busca e feita a parte, por id, para nao assumir
#         estrutura nao confirmada - Regra de Ouro).
#       - Coluna Responsavel: nome do Usuario que fez o
#         lancamento, via relationship ja existente
#         BrincoEntrada.responsavel (id_responsavel) - confirmado
#         em tb_3007_brincos_entrada.py.
#       - Demonstrativo de totais no rodape do PDF: Total Entrada
#         (soma de qtde_entrada), Total Saidas (soma de
#         qtde_saida), Total Disponivel (soma de saldo) - dos
#         lotes filtrados no periodo (decisao de Benedito, Sessao
#         043 - NAO e "Brincos adquiridos"/"disponiveis" like
#         GERAS, e um demonstrativo com os 3 numeros).
#       - PDF: A4 PAISAGEM (9 colunas, codigos de 15 digitos nao
#         cabem em retrato) - unica diferenca de orientacao em
#         relacao ao padrao ja usado em
#         consiste/produtor_relatorio_pdf.html (que e A4 retrato).
#         Mesmo padrao de layout (colgroup com largura FIXA em cm,
#         zebra striping #FBE9E4, titulo #D4370A) - decisao de
#         manter a identidade visual, so mudando a orientacao pela
#         quantidade de colunas.
#
#     v1.0.0: Criacao do modulo (Sessao 043, 01/09/2026, 11:50 -03).
#     v1.0.1: Sessao 043 (01/09/2026, 13:45 -03) - Correcao de
#         processo: o timestamp ATUALIZADO EM da v1.0.0 estava
#         incorreto (Claude codou sem pedir a hora real antes,
#         quebrando o ritual combinado) - corrigido para o horario
#         real de entrega. Nenhuma mudanca de codigo/logica.
#     v1.1.0: Sessao 044 (02/09/2026, 16:00 -03) - Cadeia de
#         navegacao "Voltar" corrigida (Benedito, teste real,
#         mesma correcao aplicada em todos os modulos do Hub de
#         Brincos): (1) chamadas a selecionar_propriedade_produtor.
#         html agora passam voltar='/produtor/hub/brincos' (antes
#         o template compartilhado ia sempre para /produtor/home);
#         (2) nova funcao _url_voltar_filtro() calcula
#         dinamicamente o destino do Voltar da tela de filtro:
#         volta para /produtor/brincos-relatorio-resumo/iniciar
#         (re-exibe a Selecao de Propriedade) se o usuario tem 2+
#         pares, ou direto para o Hub se tem so 1 par. Variavel
#         url_voltar passada para o template filtro.html - AINDA
#         PENDENTE aplicar no HTML em si (Claude nao tem o arquivo
#         brincos_relatorio_resumo_filtro.html real - pedir a
#         Benedito na proxima sessao).
#     v1.2.0: Sessao 091 (08/10/2026, 18:30 -03) - FAZENDA EM USO (Regra de Ouro #13):
#         Com fazenda em uso a tela "Selecionar Propriedade" e pulada: o iniciar()
#         abre direto a tela do modulo. O Voltar vai ao Hub de Brincos (sem passar pela
#         selecao). TRAVA: Propriedade da URL diferente da fazenda em uso e negada
#         (nunca le nem grava). Sem fazenda em uso o comportamento anterior permanece.
#         Leitura e gravacao dos dados intactas. REVERSAO: devolver a versao anterior.
# =========================================================

from datetime import date, datetime
from io import BytesIO
from types import SimpleNamespace
from flask import Blueprint, render_template, request, redirect, session, send_file

from sqlalchemy.orm import Session
from xhtml2pdf import pisa

from backend.database import engine
from backend.models import Propriedade, Produtor
from backend.models.tb_1021_fabricantes_brincos import Fabricante
from backend.models.tb_3007_brincos_entrada import BrincoEntrada
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.brincos_propriedade import propriedade_do_usuario_brincos, tela_erro_brincos
from backend.utils.pdf_helper import link_callback_pdf


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
brincos_relatorio_resumo = Blueprint('brincos_relatorio_resumo', __name__)


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
# Rota: GET /produtor/brincos-relatorio-resumo/iniciar — ponto de
# partida do fluxo, MESMO padrao ja usado em
# brincos_entrada.iniciar().
# -------------------------------------------------------
@brincos_relatorio_resumo.route('/produtor/brincos-relatorio-resumo/iniciar')
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
            proximo='/produtor/brincos-relatorio-resumo/filtro',
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
        return redirect(f'/produtor/brincos-relatorio-resumo/filtro?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/brincos-relatorio-resumo/filtro?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        titulo='Selecionar Propriedade',
        proximo='/produtor/brincos-relatorio-resumo/filtro',
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
# Produtor vinculado) para exibicao/conferencia na tela. MESMA
# logica ja usada em brincos_entrada._buscar_dados_cabecalho() -
# cada router mantem sua propria copia (mesmo padrao ja
# documentado ali), por ser uma consulta pequena e autocontida.
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
        )


# -------------------------------------------------------
# Funcao auxiliar: URL de "Voltar" da tela de filtro - volta para
# a tela de Selecionar Propriedade se o usuario tem 2+ pares
# Propriedade/Produtor (ela foi mostrada antes), ou direto para o
# Hub de Brincos se so tem 1 par (ela nunca apareceu) - mesma
# logica ja aplicada em brincos_entrada.py v1.2.0 e
# brincos_disponiveis.py v1.2.0 (Sessao 044).
# -------------------------------------------------------
def _url_voltar_filtro():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return '/produtor/brincos-relatorio-resumo/iniciar'
    return '/produtor/hub/brincos'


# -------------------------------------------------------
# Rota: GET /produtor/brincos-relatorio-resumo/filtro?id_propriedade=X
# — formulario com Propriedade/Produtor so para conferencia e os
# 2 campos editaveis (Data Inicio / Data Fim).
# -------------------------------------------------------
@brincos_relatorio_resumo.route('/produtor/brincos-relatorio-resumo/filtro')
def filtro():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    url_voltar = _url_voltar_filtro()
    id_propriedade = request.args.get('id_propriedade', '')
    if _fora_da_fazenda_em_uso(id_propriedade):
        return redirect('/produtor/brincos-relatorio-resumo/iniciar')

    if not id_propriedade or not propriedade_do_usuario_brincos(id_propriedade):
        return render_template(
            'produtor/brincos_relatorio_resumo_filtro.html',
            erro='Propriedade não informada ou inválida. Reinicie o fluxo pelo Hub de Brincos.',
            cabecalho=None,
            filtro_tentativa=None,
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
            'produtor/brincos_relatorio_resumo_filtro.html',
            erro='Propriedade ou Produtor não encontrado(s). Reinicie o fluxo pelo Hub de Brincos.',
            cabecalho=None,
            filtro_tentativa=None,
            url_voltar=url_voltar,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='brincos',
        )

    return render_template(
        'produtor/brincos_relatorio_resumo_filtro.html',
        erro=None,
        cabecalho=cabecalho,
        filtro_tentativa=None,
        url_voltar=url_voltar,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )


# -------------------------------------------------------
# Rota: POST /produtor/brincos-relatorio-resumo/gerar — valida o
# periodo, busca os lotes de tb_3007 e devolve o PDF como
# DOWNLOAD FORCADO (mesmo padrao de produtores.relatorio_pdf()).
# -------------------------------------------------------
@brincos_relatorio_resumo.route('/produtor/brincos-relatorio-resumo/gerar', methods=['POST'])
def gerar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    url_voltar = _url_voltar_filtro()
    id_produtor    = session['id_produtor']
    id_propriedade = request.form.get('id_propriedade', '')
    if _fora_da_fazenda_em_uso(id_propriedade):
        return redirect('/produtor/brincos-relatorio-resumo/iniciar')

    cabecalho = _buscar_dados_cabecalho(id_produtor, id_propriedade) if propriedade_do_usuario_brincos(id_propriedade) else None

    data_inicio_str = request.form.get('data_inicio', '').strip()
    data_fim_str    = request.form.get('data_fim', '').strip()

    filtro_tentativa = SimpleNamespace(
        data_inicio = data_inicio_str,
        data_fim    = data_fim_str,
    )

    def _reexibir(mensagem_erro):
        return render_template(
            'produtor/brincos_relatorio_resumo_filtro.html',
            erro=mensagem_erro,
            cabecalho=cabecalho,
            filtro_tentativa=filtro_tentativa,
            url_voltar=url_voltar,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='brincos',
        )

    if cabecalho is None:
        return _reexibir('Propriedade ou Produtor não encontrado(s). Reinicie o fluxo pelo Hub de Brincos.')

    if not data_inicio_str:
        return _reexibir('Data Início é obrigatória!')
    try:
        data_inicio = datetime.strptime(data_inicio_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data Início incorreta! Use o formato dd/mm/aaaa.')

    if not data_fim_str:
        return _reexibir('Data Fim é obrigatória!')
    try:
        data_fim = datetime.strptime(data_fim_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data Fim incorreta! Use o formato dd/mm/aaaa.')

    if data_inicio > data_fim:
        return _reexibir('Data Início não pode ser posterior à Data Fim!')

    # -----------------------------------------------------
    # Busca os lotes no periodo, dentro do schema do Produtor
    # logado - MESMO padrao de acesso ja usado em
    # brincos_entrada.salvar() (get_db_produtor).
    # -----------------------------------------------------
    with get_db_produtor(id_produtor) as db:
        lotes_query = (
            db.query(BrincoEntrada)
            .filter(
                BrincoEntrada.id_propriedade == int(id_propriedade),
                BrincoEntrada.data_entrada >= data_inicio,
                BrincoEntrada.data_entrada <= data_fim,
            )
            .order_by(BrincoEntrada.data_entrada, BrincoEntrada.sequencia)
            .all()
        )

        # Desanexa os dados necessarios ANTES de fechar a sessao -
        # inclui o nome do Responsavel via relationship ja
        # existente (BrincoEntrada.responsavel), que so pode ser
        # acessado enquanto a sessao ainda esta aberta.
        ids_fabricante = {lote.id_fabricante for lote in lotes_query}

        lotes = [
            SimpleNamespace(
                nota_fiscal      = lote.nota_fiscal,
                data_entrada     = lote.data_entrada,
                id_fabricante    = lote.id_fabricante,
                qtde_entrada     = lote.qtde_entrada,
                qtde_saida       = lote.qtde_saida,
                saldo            = lote.saldo,
                codigo_inicial   = lote.codigo_inicial,
                codigo_final     = lote.codigo_final,
                responsavel_nome = lote.responsavel.nome if lote.responsavel else '-',
            )
            for lote in lotes_query
        ]

    # -----------------------------------------------------
    # Nomes dos Fabricantes (schema PUBLIC) - consulta separada,
    # MESMO padrao ja usado em
    # brincos_entrada._listar_fabricantes_ativos() (nao ha
    # relationship confirmado BrincoEntrada->Fabricante).
    # -----------------------------------------------------
    nomes_fabricante = {}
    if ids_fabricante:
        with Session(engine) as db:
            fabricantes = db.query(Fabricante).filter(Fabricante.id.in_(ids_fabricante)).all()
            nomes_fabricante = {f.id: f.nome for f in fabricantes}

    for lote in lotes:
        lote.fornecedor_nome = nomes_fabricante.get(lote.id_fabricante, '-')

    # -----------------------------------------------------
    # Totais do periodo (demonstrativo Entrada / Saidas /
    # Disponivel - decisao de Benedito, Sessao 043).
    # -----------------------------------------------------
    total_entrada    = sum((lote.qtde_entrada or 0) for lote in lotes)
    total_saida       = sum((lote.qtde_saida or 0) for lote in lotes)
    total_disponivel = sum((lote.saldo or 0) for lote in lotes)

    html_renderizado = render_template(
        'produtor/brincos_relatorio_resumo_pdf.html',
        cabecalho        = cabecalho,
        lotes            = lotes,
        data_inicio      = data_inicio.strftime('%d/%m/%Y'),
        data_fim         = data_fim.strftime('%d/%m/%Y'),
        data_emissao     = date.today().strftime('%d/%m/%Y'),
        total_entrada    = total_entrada,
        total_saida      = total_saida,
        total_disponivel = total_disponivel,
    )

    buffer_pdf = BytesIO()
    pisa.CreatePDF(html_renderizado, dest=buffer_pdf, link_callback=link_callback_pdf)
    buffer_pdf.seek(0)

    nome_arquivo = f'brincos_resumo_propriedade{id_propriedade}_{data_inicio.strftime("%Y%m%d")}_{data_fim.strftime("%Y%m%d")}.pdf'
    return send_file(
        buffer_pdf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=nome_arquivo
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\brincos_relatorio_resumo.py
# =========================================================