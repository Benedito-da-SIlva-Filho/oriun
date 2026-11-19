# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\parceiros_fornecedores.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-08-18 19:37 -03
# ATUALIZADO EM: 2026-11-12 19:00 -03
# VERSAO: 1.7.0
# v1.7.0: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras no CNPJ aceitas e conferidas; CNPJ antigo continua valendo. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Rotas de consulta e impressao de Parceiros/Fornecedores
#     (tb_parceiros + tb_parceiros_propriedades), do lado
#     Produtor. Fecha a lacuna registrada como P-047: ate esta
#     sessao, o resolver_parceiro() (backend/servicos/
#     resolver_parceiro.py) ja criava/atualizava esses registros
#     durante a leitura de GTA, mas nao existia NENHUMA tela para
#     o Produtor consultar o que foi gravado.
#
#     - /produtor/parceiros                    -> lista, com busca
#     - /produtor/parceiros/<id>                -> detalhe (ficha +
#                                                  Propriedades
#                                                  vinculadas)
#     - /produtor/parceiros/relatorio/<id>       -> PDF da ficha de
#                                                  1 Parceiro
#     - /produtor/parceiros/relatorio            -> PDF da lista
#                                                  completa
#
#     ISOLAMENTO POR SCHEMA: tb_parceiros e tb_parceiros_
#     propriedades vivem DENTRO do schema de cada Produtor
#     (Schema-por-Produtor), nao no schema public - toda rota
#     aqui usa get_db_produtor(session['id_produtor']) (backend/
#     utils/multitenant.py), nunca Session(engine) puro. Mesma
#     correcao ja aplicada em gta_compra.py v2.6.0 (ver changelog
#     la para o erro real - UndefinedTable - que revelou isso).
#
#     ESCOPO (decisao de Benedito, Sessao 034 cont. 9): esta tela
#     mostra TODOS os Parceiros do Produtor logado, sem filtro por
#     Propriedade - o isolamento por Propriedade nao existe aqui
#     de proposito (regra ja fechada com Benedito: um Parceiro,
#     uma vez cadastrado no schema do Produtor, vale para
#     qualquer uma das Propriedades dele, sem restricao).
#
#     BUSCA: cobre todos os campos de identificacao que aparecem
#     numa GTA - Nome/Razao Social e CPF/CNPJ (tb_parceiros) +
#     Estabelecimento e Municipio (tb_parceiros_propriedades) -
#     decisao de Benedito: "as informacoes tanto da consulta como
#     da impressao sao todos os dados que constam na GTA".
#
#     v1.0.0: Criacao do modulo (Sessao 034 continuacao 9,
#         18/08/2026).
#     v1.2.0: Sessao 035 (19/08/2026) - Reestruturacao da Lista e
#         dos dois PDFs, a pedido de Benedito: a coluna "Propriedades"
#         (contagem) foi substituida pela lista detalhada de
#         Propriedades por Parceiro (1 bloco por Parceiro, 1 linha
#         por Propriedade), tanto na tela quanto nos dois relatorios
#         em PDF. A rota detalhe() passou a aceitar o parametro
#         opcional ?propriedade=<id> na querystring, usado para
#         destacar/rolar ate uma Propriedade especifica quando o
#         acesso vem de um clique na lista (padrao novo "Lista
#         Clicavel" do Orion). Corrigido tambem o rodape do arquivo,
#         que ainda citava o nome antigo "parceiros.py" (residuo da
#         renomeacao feita na Sessao 034 cont. 10, ver Referencia do
#         Sistema Secao 19).
#     v1.3.0: Sessao 089 (07/10/2026, 09:45 -03) - Parceiros ganha lugar
#         no menu lateral (grupo CADASTRO). As telas Lista e Detalhe
#         passam menu_ativo='parceiros' (antes None) para o item do
#         menu ficar destacado. Nenhuma outra mudanca neste arquivo.
#     v1.4.0: Sessao 095 (13/10/2026, 19:10 -03) - NOVO PARCEIRO: rotas novo() e novo_salvar()
#         (botao "+ Novo Parceiro" na lista; cadastro avulso, sem GTA). Municipio escolhido na
#         tb_1023_municipios (grava codigo + nome + UF oficiais). Codigo do municipio passa a
#         seguir para as telas/impressoes (municipio_codigo nos dados). REVERSAO:
#         .bak_antes_novo_parceiro_s095.
#     v1.5.0: Sessao 095 (13/10/2026, 19:30 -03) - Regioes do municipio (Regiao do Brasil, Mesorregiao, Microrregiao - IBGE) vindas da tb_1023 por codigo; vao para tela de detalhe e PDFs. REVERSAO: bak_antes_regioes_s095.
#     v1.6.0: Sessao 095 (13/10/2026, 19:40 -03) - Mesorregiao travada (vale a do IBGE; so livre se o municipio nao tem). REVERSAO: .bak_antes_meso_travada_s095.
# =========================================================

from datetime import date
from io import BytesIO

from flask import Blueprint, render_template, request, redirect, url_for, session, send_file
from sqlalchemy.orm import joinedload
from xhtml2pdf import pisa

from backend.models.tb_parceiros import Parceiro
from backend.models.tb_parceiros_propriedades import ParceiroPropriedades
from sqlalchemy.orm import Session
from backend.database import engine
from backend.models.tb_1023_municipios import Municipio
from backend.routers.auth import redirecionar_home
from backend.routers.busca_municipio import buscar_municipio_por_codigo
from backend.utils.validadores import validar_cpf, validar_cnpj, limpar_documento
from backend.utils.multitenant import get_db_produtor
from backend.utils.pdf_helper import link_callback_pdf

# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
parceiros_fornecedores = Blueprint('parceiros_fornecedores', __name__)


# -------------------------------------------------------
# Funcao auxiliar: confere perfil (PRODUTOR/FAZENDA) e presenca
# de id_produtor na sessao (necessario para abrir o schema
# correto). Devolve None se tudo certo, ou uma resposta de
# redirecionamento pronta se algo estiver faltando.
# -------------------------------------------------------
def _checar_acesso():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    perfil = session.get('usuario_perfil')
    if perfil not in ('PRODUTOR', 'FAZENDA'):
        return redirecionar_home(perfil)

    if not session.get('id_produtor'):
        return redirecionar_home(perfil)

    return None


# -------------------------------------------------------
# v1.5.0 - Regioes do IBGE por codigo de municipio (tb_1023).
# Anexa regiao_brasil / microrregiao / mesorregiao_ibge aos itens
# (dict ou objeto) - 1 consulta so para todos.
# -------------------------------------------------------
def _anexar_regioes(itens):
    def ler(i, c):
        return i.get(c) if isinstance(i, dict) else getattr(i, c, None)
    def gravar(i, c, v):
        if isinstance(i, dict):
            i[c] = v
        else:
            setattr(i, c, v)
    codigos = {ler(i, 'municipio_codigo') for i in itens if ler(i, 'municipio_codigo')}
    mapa = {}
    if codigos:
        with Session(engine) as dbp:
            for cod, rb, me, mi in dbp.query(Municipio.codigo_ibge, Municipio.regiao_brasil,
                                             Municipio.mesorregiao, Municipio.microrregiao
                                             ).filter(Municipio.codigo_ibge.in_(codigos)).all():
                mapa[cod] = (rb, me, mi)
    for i in itens:
        rb, me, mi = mapa.get(ler(i, 'municipio_codigo'), (None, None, None))
        gravar(i, 'regiao_brasil', rb)
        gravar(i, 'mesorregiao_ibge', me)
        gravar(i, 'microrregiao', mi)


# -------------------------------------------------------
# Funcao auxiliar: busca Parceiros no schema ja aberto (db),
# filtrando pelo termo em Nome/CPF-CNPJ (tb_parceiros) ou
# Estabelecimento/Municipio (tb_parceiros_propriedades) - ver
# DESCRICAO no topo do arquivo. Sem termo, devolve todos.
# joinedload evita N+1 query ao acessar parceiro.propriedades
# na tela (usada para montar o bloco de Propriedades por
# Parceiro, ver _montar_parceiro_view() abaixo).
# -------------------------------------------------------
def _buscar_parceiros(db, termo):
    query = db.query(Parceiro).options(joinedload(Parceiro.propriedades))

    if termo:
        query = query.outerjoin(
            ParceiroPropriedades, ParceiroPropriedades.id_parceiro == Parceiro.id
        ).filter(
            (Parceiro.nome.ilike(f'%{termo}%')) |
            (Parceiro.cpf_cnpj.ilike(f'%{termo}%')) |
            (ParceiroPropriedades.estabelecimento.ilike(f'%{termo}%')) |
            (ParceiroPropriedades.municipio_nome.ilike(f'%{termo}%'))
        ).distinct()

    return query.order_by(Parceiro.nome).all()


# -------------------------------------------------------
# Funcao auxiliar (NOVA v1.2.0): "achata" 1 Parceiro + suas
# Propriedades para um dict pronto para o template/PDF, com o
# nivel de detalhe indicado por completo=True/False.
#   completo=False -> so os campos usados na Lista/PDF resumido
#                      (Estabelecimento, Municipio/UF, Status).
#   completo=True  -> todos os campos de tb_parceiros_
#                      propriedades (usado no PDF da lista
#                      completa, a pedido de Benedito: "todas as
#                      informacoes do cadastro").
# -------------------------------------------------------
def _montar_parceiro_view(p, completo=False):
    propriedades_view = []
    for prop in sorted(p.propriedades, key=lambda x: x.estabelecimento):
        item = {
            'id':              prop.id,
            'estabelecimento': prop.estabelecimento,
            'municipio_codigo': prop.municipio_codigo,
            'municipio_nome':  prop.municipio_nome,
            'uf':              prop.uf,
            'ativo':           prop.ativo,
        }
        if completo:
            item['codigo_mapa']   = prop.codigo_mapa
            item['insc_estadual'] = prop.insc_estadual
            item['regiao']        = prop.regiao
        propriedades_view.append(item)
    _anexar_regioes(propriedades_view)

    return {
        'id':           p.id,
        'nome':         p.nome,
        'cpf_cnpj':     p.cpf_cnpj,
        'ativo':        p.ativo,
        'propriedades': propriedades_view,
    }


# -------------------------------------------------------
# Rota: /produtor/parceiros — lista, com busca
# -------------------------------------------------------
@parceiros_fornecedores.route('/produtor/parceiros')
def lista():
    resposta_bloqueio = _checar_acesso()
    if resposta_bloqueio:
        return resposta_bloqueio

    termo_busca = request.args.get('busca', '').strip()

    with get_db_produtor(session['id_produtor']) as db:
        lista_parceiros = _buscar_parceiros(db, termo_busca)

        # Monta os dados ja "achatados" para o template, evitando
        # acessar objetos SQLAlchemy fora da sessao (a sessao
        # fecha ao sair do "with"). v1.2.0: cada Parceiro traz sua
        # lista de Propriedades (nao mais so a contagem).
        parceiros_view = [_montar_parceiro_view(p) for p in lista_parceiros]

    return render_template('produtor/parceiro_lista.html',
        parceiros      = parceiros_view,
        termo_busca    = termo_busca,
        mensagem_ok    = ('Parceiro cadastrado com sucesso!' if request.args.get('salvo') == '1' else ''),
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'parceiros'
    )


# -------------------------------------------------------
# Rota: /produtor/parceiros/<id> — detalhe (ficha + Propriedades
# vinculadas a este Parceiro).
# v1.2.0: aceita o parametro opcional ?propriedade=<id> na
# querystring - usado para destacar/rolar ate uma Propriedade
# especifica quando o acesso vem de um clique na Lista (padrao
# "Lista Clicavel" do Orion).
# -------------------------------------------------------
@parceiros_fornecedores.route('/produtor/parceiros/<int:id>')
def detalhe(id):
    resposta_bloqueio = _checar_acesso()
    if resposta_bloqueio:
        return resposta_bloqueio

    propriedade_destaque = request.args.get('propriedade', type=int)

    with get_db_produtor(session['id_produtor']) as db:
        parceiro = db.get(Parceiro, id)
        if not parceiro:
            return redirect(url_for('parceiros_fornecedores.lista'))

        propriedades = db.query(ParceiroPropriedades).filter(
            ParceiroPropriedades.id_parceiro == id
        ).order_by(ParceiroPropriedades.estabelecimento).all()

        parceiro_view = {
            'id':           parceiro.id,
            'nome':         parceiro.nome,
            'cpf_cnpj':     parceiro.cpf_cnpj,
            'ativo':        parceiro.ativo,
            'criado_em':    parceiro.criado_em,
        }
        propriedades_view = [{
            'id':               prop.id,
            'estabelecimento':  prop.estabelecimento,
            'codigo_mapa':      prop.codigo_mapa,
            'insc_estadual':    prop.insc_estadual,
            'municipio_codigo': prop.municipio_codigo,
            'municipio_nome':   prop.municipio_nome,
            'uf':               prop.uf,
            'regiao':           prop.regiao,
            'ativo':            prop.ativo,
        } for prop in propriedades]
        _anexar_regioes(propriedades_view)

    return render_template('produtor/parceiro_detalhe.html',
        parceiro              = parceiro_view,
        propriedades          = propriedades_view,
        propriedade_destaque  = propriedade_destaque,
        usuario_nome          = session.get('usuario_nome'),
        usuario_perfil        = session.get('usuario_perfil'),
        cor_primaria          = session.get('cor_primaria', '#D4370A'),
        nome_sistema          = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo            = 'parceiros'
    )


# -------------------------------------------------------
# Rota: /produtor/parceiros/relatorio/<id> — PDF da ficha de
# 1 Parceiro (dados + todas as Propriedades vinculadas)
# -------------------------------------------------------
@parceiros_fornecedores.route('/produtor/parceiros/relatorio/<int:id>')
def relatorio_pdf(id):
    resposta_bloqueio = _checar_acesso()
    if resposta_bloqueio:
        return resposta_bloqueio

    with get_db_produtor(session['id_produtor']) as db:
        parceiro = db.get(Parceiro, id)
        if not parceiro:
            return redirect(url_for('parceiros_fornecedores.lista'))

        propriedades = db.query(ParceiroPropriedades).filter(
            ParceiroPropriedades.id_parceiro == id
        ).order_by(ParceiroPropriedades.estabelecimento).all()

        _anexar_regioes(list(propriedades))
        html_renderizado = render_template('produtor/parceiro_relatorio_pdf.html',
            parceiro      = parceiro,
            propriedades  = propriedades,
            data_emissao  = date.today().strftime('%d/%m/%Y')
        )

    buffer_pdf = BytesIO()
    pisa.CreatePDF(html_renderizado, dest=buffer_pdf, link_callback=link_callback_pdf)
    buffer_pdf.seek(0)

    return send_file(
        buffer_pdf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'parceiro_{id}_ficha.pdf'
    )


# -------------------------------------------------------
# Rota: /produtor/parceiros/relatorio — PDF da lista completa de
# Parceiros. v1.2.0: deixou de ser a visao resumida (1 linha por
# Parceiro com contagem de Propriedades) e passou a trazer todas
# as informacoes do cadastro de cada Propriedade, a pedido de
# Benedito ("todas as informacoes do cadastro").
# -------------------------------------------------------
@parceiros_fornecedores.route('/produtor/parceiros/relatorio')
def relatorio_lista_pdf():
    resposta_bloqueio = _checar_acesso()
    if resposta_bloqueio:
        return resposta_bloqueio

    with get_db_produtor(session['id_produtor']) as db:
        lista_parceiros = _buscar_parceiros(db, '')

        parceiros_view = [_montar_parceiro_view(p, completo=True) for p in lista_parceiros]

        html_renderizado = render_template('produtor/parceiros_lista_relatorio_pdf.html',
            parceiros     = parceiros_view,
            data_emissao  = date.today().strftime('%d/%m/%Y')
        )

    buffer_pdf = BytesIO()
    pisa.CreatePDF(html_renderizado, dest=buffer_pdf, link_callback=link_callback_pdf)
    buffer_pdf.seek(0)

    return send_file(
        buffer_pdf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='parceiros_lista.pdf'
    )

# -------------------------------------------------------
# v1.4.0 - NOVO PARCEIRO (cadastro avulso, sem passar pela GTA).
# Produtor e Administrativo dele (perfil PRODUTOR). Cria 1 Parceiro +
# 1 Propriedade na mesma transacao. O Municipio vem da tb_1023
# (codigo, nome e UF oficiais - nunca "NOME / UF" dentro do nome).
# -------------------------------------------------------
def _contexto_novo(erro, dados):
    return dict(
        erro           = erro,
        dados          = dados,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'parceiros'
    )


_CAMPOS_NOVO = ('cpf_cnpj', 'nome', 'estabelecimento', 'codigo_mapa', 'insc_estadual',
                'regiao', 'municipio_codigo', 'municipio_nome', 'uf')


@parceiros_fornecedores.route('/produtor/parceiros/novo', methods=['GET'])
def novo():
    resposta_bloqueio = _checar_acesso()
    if resposta_bloqueio:
        return resposta_bloqueio
    return render_template('produtor/parceiro_novo.html',
        **_contexto_novo(None, {c: '' for c in _CAMPOS_NOVO}))


@parceiros_fornecedores.route('/produtor/parceiros/novo/salvar', methods=['POST'])
def novo_salvar():
    resposta_bloqueio = _checar_acesso()
    if resposta_bloqueio:
        return resposta_bloqueio

    dados = {c: (request.form.get(c) or '').strip() for c in _CAMPOS_NOVO}
    for c in ('nome', 'estabelecimento', 'insc_estadual', 'regiao', 'municipio_nome', 'uf'):
        dados[c] = dados[c].upper()

    doc = limpar_documento(dados['cpf_cnpj'])
    dados['cpf_cnpj'] = doc

    erro = None
    municipio = buscar_municipio_por_codigo(dados['municipio_codigo'])

    if not doc:
        erro = 'Informe o CPF/CNPJ do Parceiro.'
    elif len(doc) not in (11, 14):
        erro = 'CPF/CNPJ com quantidade de caracteres incorreta.'
    elif len(doc) == 11 and not validar_cpf(doc):
        erro = 'CPF incorreto.'
    elif len(doc) == 14 and not validar_cnpj(doc):
        erro = 'CNPJ incorreto.'
    elif not dados['nome'] or len(dados['nome']) > 150:
        erro = 'Informe o Nome / Razão Social do Parceiro.'
    elif not dados['estabelecimento'] or len(dados['estabelecimento']) > 150:
        erro = 'Informe o Estabelecimento (nome da Fazenda).'
    elif len(dados['codigo_mapa']) > 20:
        erro = 'Código MAPA excede o tamanho permitido.'
    elif len(dados['insc_estadual']) > 20:
        erro = 'Inscrição Estadual excede o tamanho permitido.'
    elif len(dados['regiao']) > 50:
        erro = 'Região excede o tamanho permitido.'
    elif not municipio:
        erro = 'Escolha o Município na lista (ou digite um código de município válido).'

    if not erro:
        dados['municipio_nome'] = municipio['nome'].upper()
        dados['uf'] = municipio['uf'].upper()
        # v1.6.0 - Mesorregiao travada: se o IBGE tem, vale a do IBGE; so e livre quando o municipio veio sem.
        if municipio.get('mesorregiao'):
            dados['regiao'] = municipio['mesorregiao'].upper()
        with get_db_produtor(session['id_produtor']) as db:
            existente = db.query(Parceiro).filter_by(cpf_cnpj=doc).first()
            if existente:
                erro = 'Já existe um Parceiro com este CPF/CNPJ: %s.' % existente.nome
            else:
                parceiro = Parceiro(cpf_cnpj=doc, nome=dados['nome'], ativo=True)
                db.add(parceiro)
                db.flush()
                db.add(ParceiroPropriedades(
                    id_parceiro      = parceiro.id,
                    estabelecimento  = dados['estabelecimento'],
                    codigo_mapa      = dados['codigo_mapa'] or None,
                    insc_estadual    = dados['insc_estadual'] or None,
                    municipio_codigo = municipio['codigo_ibge'],
                    municipio_nome   = dados['municipio_nome'],
                    uf               = dados['uf'],
                    regiao           = dados['regiao'] or None,
                    ativo            = True,
                ))
                db.commit()

    if erro:
        dados['regiao_livre'] = '1' if (municipio and not municipio.get('mesorregiao')) else ''
        return render_template('produtor/parceiro_novo.html', **_contexto_novo(erro, dados))

    return redirect(url_for('parceiros_fornecedores.lista', salvo='1'))


# =========================================================
# FIM DE ARQUIVO: backend\routers\parceiros_fornecedores.py
# =========================================================