# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\parceiro_cadastro_manual.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-08-21 10:29 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.10.0
# v1.10.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (4 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.9.0: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras no CNPJ aceitas e conferidas; CNPJ antigo continua valendo. REVERSAO: .bak_antes_s122_etapa2.
# v1.8.0: Sessao 122 (2026-11-12 17:40 -03) - Auditoria Etapa 2 (itens 7 e 9): confere se o CPF/CNPJ ja existe e reaproveita o Parceiro (so acrescenta o estabelecimento novo; Parceiro inativo avisa a Consiste); Municipio/UF conferidos pelo catalogo tb_1023. REVERSAO: .bak_antes_s122_etapa2.
# v1.7.0: Sessao 115 (2026-11-05 17:40 -03) - origem 'posse' (volta para a DTA de Posse). REVERSAO: .bak_antes_s115_dta3a.
#
# DESCRICAO:
#     Tela de resolucao de Parceiro para a GTA Manual (Sessao
#     036). Passo 2 do fluxo (ver gta_manual.py v1.0.0 para o
#     desenho completo) - o usuario digita o CPF/CNPJ da
#     Procedencia:
#       - Encontrado (via /api/busca-parceiro): se tiver 1 so
#         Propriedade, segue direto; se tiver mais de uma, o
#         usuario escolhe qual (tudo resolvido em JavaScript,
#         sem nova chamada ao servidor).
#       - Nao encontrado: abre formulario de cadastro novo
#         (Parceiro + 1 Propriedade), tambem em JavaScript, na
#         mesma tela - sem navegar para outra pagina.
#     Ao final (achado ou cadastrado), redireciona para a GTA
#     Manual (backend/routers/gta_manual.py) levando id_parceiro,
#     id_propriedade (do Parceiro, externa) E
#     id_propriedade_interna (do Produtor logado, ja resolvida
#     por gta_manual.iniciar() ANTES desta tela) na querystring.
#     A URL final usa string fixa (nao url_for) porque a rota
#     gta_manual.nova ainda nao existe no momento desta entrega -
#     PENDENCIA IMEDIATA: trocar para url_for() assim que
#     gta_manual.py ganhar a rota nova().
#
#     Grava em tb_parceiros + tb_parceiros_propriedades (schema
#     do Produtor logado, via get_db_produtor).
#
#     Campo Municipio usa autocomplete via /api/busca-municipio
#     (piloto de integracao de tb_1023_municipios) -
#     municipio_codigo viaja escondido no formulario, preenchido
#     pelo JavaScript ao escolher um resultado da busca.
#
#     v1.0.0: Criacao do modulo (Sessao 036).
#     v1.1.0: Sessao 036 - CORRECAO DE BUG real, identificado em
#             teste: ao dar erro de validacao no salvar(), a
#             tela recarregava em branco, perdendo TODOS os
#             dados ja digitados pelo usuario (violava o padrao
#             do projeto de sempre preservar dados no
#             re-render). Corrigido: em caso de erro, os dados
#             submetidos sao devolvidos ao template via
#             SimpleNamespace, e o formulario de cadastro ja e
#             reaberto automaticamente (mostrar_cadastro=True),
#             sem o usuario precisar buscar o CPF de novo.
#     v1.2.0: Sessao 036/037 - CORRECAO DE BUG real, identificado
#             em teste: id_propriedade_interna (resolvida por
#             gta_manual.iniciar(), passo anterior do fluxo) era
#             recebida na querystring de nova() mas NUNCA
#             repassada adiante - se perdia no caminho, tanto no
#             fluxo "achou Parceiro" (JS) quanto no fluxo
#             "cadastrou Parceiro novo" (POST salvar()). Corrigido
#             nos tres pontos: (1) nova() le id_propriedade_interna
#             da querystring e injeta num campo hidden no
#             template; (2) a funcao JS irParaGtaManual() passa a
#             receber e incluir esse valor na URL final; (3)
#             salvar() le o campo hidden do formulario e inclui
#             na URL de redirect ao final da gravacao.
#     v1.2.1: Sessao 080 (25/09/2026, 18:00 -03) - VARREDURA do
#             vicio "ler do banco depois do commit()" (Sessoes
#             078/079/080): salvar() lia parceiro.id e
#             propriedade.id DEPOIS do db.commit() - os objetos
#             expiram e a releitura acontece sem o schema do
#             Produtor ("nao existe a relacao"), estourando erro
#             APOS gravar (o usuario tentaria de novo e duplicaria
#             o Parceiro). Os 2 ids agora sao guardados ANTES do
#             commit. Nenhuma outra mudanca.
#     v1.3.0: Sessao 087 (05/10/2026, 10:50 -03) - VOLTAR PELO CAMINHO
#             INVERSO (Regra de Ouro #4, pedido de Benedito): (1) nova()
#             passa a ler o parametro documento (CPF/CNPJ) da URL e o
#             entrega ao template, para o campo chegar preenchido quando
#             o usuario volta do formulario da GTA - so preenche, nao
#             busca sozinho (senao o usuario seria jogado de novo para
#             a GTA); (2) novo helper _url_origem(): o Voltar e o
#             Cancelar desta tela vao para a Selecao de Propriedade
#             quando o usuario tem 2+ pares Propriedade/Produtor, e para
#             o card GTA Preenchimento Manual (/produtor/entrada/compra/
#             nova) quando tem 1 so - com 1 par, iniciar() redireciona
#             direto para esta tela e o Voltar ficava preso num laco.
#     v1.4.0: Sessao 090 (08/10/2026, 08:10 -03) - FAZENDA EM USO (Lote 3):
#             FAZENDA EM USO (Regra de Ouro #13): a tela "Selecionar Propriedade" deixa
#             de aparecer quando ha fazenda em uso (auth.resolver_fazenda_em_uso).
#               - _url_origem(): com fazenda em uso o Voltar/Cancelar vai direto
#                 ao card GTA Preenchimento Manual (voltar ao iniciar() de
#                 gta_manual reabriria esta tela: laco).
#               - nova(): trava - Propriedade diferente da fazenda em uso
#                 (trocada em outra aba) manda para gta_manual.iniciar().
#             Nenhuma outra mudanca.
#     v1.5.0: Sessao 095 (13/10/2026, 19:45 -03) - nome do municipio gravado sem " / UF" (a UF tem coluna propria; saia repetida nas impressoes).
# =========================================================

from types import SimpleNamespace
from flask import Blueprint, render_template, request, redirect, session
from backend.models.tb_parceiros import Parceiro
from backend.models.tb_parceiros_propriedades import ParceiroPropriedades
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.busca_municipio import buscar_municipio_por_codigo
from backend.utils.multitenant import get_db_produtor
from backend.utils.validadores import validar_cpf, validar_cnpj, limpar_documento


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
parceiro_cadastro_manual = Blueprint('parceiro_cadastro_manual', __name__)


# -------------------------------------------------------
# v1.3.0 - destino do Voltar/Cancelar desta tela (caminho inverso).
# 2+ pares Propriedade/Produtor: a tela de Selecao de Propriedade
# (gta_manual.iniciar). 1 par: iniciar() pularia a selecao e
# redirecionaria de volta para ca (laco) - entao volta direto para
# o card GTA Preenchimento Manual.
# -------------------------------------------------------
_TIPO_DA_ORIGEM = {'transfer': 'TRANSFER', 'venda': 'VENDA', 'posse': 'POSSE'}   # s115 - origem da tela -> tipo da GTA de Saida


def _url_transfer(id_propriedade_interna, documento='', tipo='TRANSFER'):
    """v1.5.0 - volta para a GTA de Transferencia (Saida) da Propriedade de origem. v1.6.0 (s111): tipo VENDA tambem."""
    url = f'/produtor/gta-saida/nova?id_propriedade={id_propriedade_interna}&tipo={tipo}'
    if documento:
        url += f'&documento={documento}'
    return url


def _url_origem(origem='', id_propriedade_interna=''):
    # v1.5.0 - veio da GTA de Transferencia: o Voltar/Cancelar volta para ela
    if origem in ('transfer', 'venda', 'posse') and str(id_propriedade_interna).isdecimal():
        return _url_transfer(id_propriedade_interna, '', _TIPO_DA_ORIGEM.get(origem, 'TRANSFER'))
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    # v1.4.0 - com fazenda em uso a selecao e pulada (voltar para ela
    # reabriria esta tela: laco) - volta direto ao card GTA Manual.
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return '/produtor/gta-manual/iniciar'
    return '/produtor/entrada/compra/nova'


# -------------------------------------------------------
# TRAVA DA FAZENDA EM USO (v1.4.0): True quando ha fazenda em uso e a
# Propriedade da URL e DIFERENTE dela (trocada em outra aba).
# -------------------------------------------------------
def _fora_da_fazenda_em_uso(id_propriedade_interna):
    if not str(id_propriedade_interna).isdecimal():
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares)
    return par_em_uso is not None and int(par_em_uso.id_propriedade) != int(id_propriedade_interna)


# -------------------------------------------------------
# Rota: GET /produtor/parceiro-manual — tela inicial. Todo o
# fluxo de busca/escolha de Propriedade acontece em JavaScript
# (chamando /api/busca-parceiro); esta rota so entrega a
# pagina em branco, pronta para o usuario digitar o CPF/CNPJ.
#
# id_propriedade_interna (v1.2.0): recebida na querystring
# (vinda de gta_manual.iniciar()), repassada ao template para
# viajar num campo hidden ate o final do fluxo.
# -------------------------------------------------------
@parceiro_cadastro_manual.route('/produtor/parceiro-manual', methods=['GET'])
def nova():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade_interna = request.args.get('id_propriedade_interna', '')
    origem = request.args.get('origem', '') if request.args.get('origem', '') in ('transfer', 'venda', 'posse') else ''

    # v1.4.0 - trava da fazenda em uso.
    if _fora_da_fazenda_em_uso(id_propriedade_interna):
        return redirect('/produtor/gta-manual/iniciar')

    # v1.3.0 - CPF/CNPJ de volta do formulario da GTA: so digitos, max 14
    documento = limpar_documento(request.args.get('documento', ''))[:14]

    return render_template(
        'produtor/parceiro_cadastro_manual.html',
        erro=None,
        dados=None,
        mostrar_cadastro=False,
        id_propriedade_interna=id_propriedade_interna,
        documento=documento,
        origem=origem,
        url_origem=_url_origem(origem, id_propriedade_interna),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: POST /produtor/parceiro-manual/salvar — grava um
# Parceiro novo + 1 Propriedade, na mesma transacao. So
# acionada quando a busca por CPF/CNPJ nao encontrou nada
# (fluxo de cadastro).
# -------------------------------------------------------
@parceiro_cadastro_manual.route('/produtor/parceiro-manual/salvar', methods=['POST'])
def salvar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_produtor = session['id_produtor']

    cpf_cnpj          = (request.form.get('cpf_cnpj') or '').strip()
    nome              = (request.form.get('nome') or '').strip().upper()
    estabelecimento   = (request.form.get('estabelecimento') or '').strip().upper()
    codigo_mapa       = (request.form.get('codigo_mapa') or '').strip()
    insc_estadual     = (request.form.get('insc_estadual') or '').strip().upper()
    municipio_codigo  = (request.form.get('municipio_codigo') or '').strip()
    municipio_nome    = (request.form.get('municipio_nome') or '').strip().upper()
    uf                = (request.form.get('uf') or '').strip().upper()
    regiao            = (request.form.get('regiao') or '').strip().upper()
    # v-s095 - o nome do municipio nao leva " / UF" (a UF tem coluna propria; senao saia repetida nas impressoes)
    if uf and municipio_nome.endswith(' / ' + uf):
        municipio_nome = municipio_nome[:-len(' / ' + uf)]

    # v1.2.0 - viaja em campo hidden desde a nova(), precisa
    # sobreviver tanto ao reexibir por erro quanto ao redirect
    # final de sucesso.
    id_propriedade_interna = (request.form.get('id_propriedade_interna') or '').strip()
    origem = (request.form.get('origem') or '') if (request.form.get('origem') or '') in ('transfer', 'venda', 'posse') else ''

    # Preserva tudo que foi digitado - devolvido ao template em caso
    # de erro, para o formulario nao voltar em branco (v1.1.0).
    dados = SimpleNamespace(
        cpf_cnpj=cpf_cnpj,
        nome=nome,
        estabelecimento=estabelecimento,
        codigo_mapa=codigo_mapa,
        insc_estadual=insc_estadual,
        municipio_codigo=municipio_codigo,
        municipio_nome=municipio_nome,
        uf=uf,
        regiao=regiao,
    )

    erro = None

    # ---- Validacoes obrigatorias ----
    doc_limpo = limpar_documento(cpf_cnpj)
    if not doc_limpo:
        erro = 'Informe o CPF/CNPJ da Procedência.'
    elif len(doc_limpo) == 11 and not validar_cpf(doc_limpo):
        erro = 'CPF da Procedência incorreto.'
    elif len(doc_limpo) == 14 and not validar_cnpj(doc_limpo):
        erro = 'CNPJ da Procedência incorreto.'
    elif len(doc_limpo) not in (11, 14):
        erro = 'CPF/CNPJ da Procedência com quantidade de caracteres incorreta.'
    elif not nome or len(nome) > 150:
        erro = 'Informe o Nome/Razão Social da Procedência.'
    elif not estabelecimento or len(estabelecimento) > 150:
        erro = 'Informe o Estabelecimento (nome da Fazenda) da Procedência.'
    elif codigo_mapa and len(codigo_mapa) > 20:
        erro = 'Código MAPA excede o tamanho permitido.'
    elif insc_estadual and len(insc_estadual) > 20:
        erro = 'Inscrição Estadual excede o tamanho permitido.'
    elif not municipio_nome or len(municipio_nome) > 100:
        erro = 'Informe o Município da Procedência.'
    elif not uf or len(uf) != 2:
        erro = 'Informe a UF da Procedência.'
    elif regiao and len(regiao) > 50:
        erro = 'Região excede o tamanho permitido.'

    # Etapa 2 (item 9): Municipio/UF conferidos com o catalogo (tb_1023), como na tela Parceiros.
    # Vale o nome/UF oficiais do codigo informado; sem codigo valido nao grava.
    if not erro:
        municipio_cat = buscar_municipio_por_codigo(municipio_codigo)
        if not municipio_cat:
            erro = 'Município não encontrado. Digite um código de município válido (7 dígitos, ex: 5006408) e confira o nome que aparece ao lado.'
        else:
            municipio_codigo = municipio_cat['codigo_ibge']
            municipio_nome   = municipio_cat['nome'].upper()
            uf               = municipio_cat['uf'].upper()
            if municipio_cat.get('mesorregiao'):
                regiao = municipio_cat['mesorregiao'].upper()
            dados.municipio_codigo = municipio_codigo
            dados.municipio_nome   = municipio_nome
            dados.uf               = uf
            dados.regiao           = regiao

    if erro:
        return render_template(
            'produtor/parceiro_cadastro_manual.html',
            erro=erro,
            dados=dados,
            mostrar_cadastro=True,
            id_propriedade_interna=id_propriedade_interna,
            documento=doc_limpo,
            origem=origem,
            url_origem=_url_origem(origem, id_propriedade_interna),
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='entrada',
        )

    with get_db_produtor(id_produtor) as db:
        # Etapa 2 (item 7): o CPF/CNPJ pode ja existir (duplo clique, botao Voltar do
        # navegador, 2 abas). Nesse caso reaproveita o Parceiro; so acrescenta o
        # estabelecimento se ele ainda nao existir para esse Parceiro.
        parceiro = db.query(Parceiro).filter_by(cpf_cnpj=doc_limpo).first()
        if parceiro is not None and not parceiro.ativo:
            erro_inativo = (f'O CPF/CNPJ {doc_limpo} já está cadastrado como Parceiro, mas está inativo. '
                            f'Peça à Consiste para reativar o cadastro.')
            return render_template(
                'produtor/parceiro_cadastro_manual.html',
                erro=erro_inativo, dados=dados, mostrar_cadastro=True,
                id_propriedade_interna=id_propriedade_interna, documento=doc_limpo, origem=origem,
                url_origem=_url_origem(origem, id_propriedade_interna),
                usuario_nome=session.get('usuario_nome'), usuario_perfil=session.get('usuario_perfil'),
                cor_primaria='#D4370A', nome_sistema='Orion SISBOV', menu_ativo='entrada',
            )
        if parceiro is None:
            parceiro = Parceiro(
                cpf_cnpj=doc_limpo,
                nome=nome,
                ativo=True,
            )
            db.add(parceiro)
            db.flush()  # garante parceiro.id antes de criar a Propriedade

        propriedade_existente = db.query(ParceiroPropriedades).filter(
            ParceiroPropriedades.id_parceiro == parceiro.id,
            ParceiroPropriedades.estabelecimento == estabelecimento,
            ParceiroPropriedades.municipio_codigo == (municipio_codigo or None),
        ).first()
        if propriedade_existente is not None:
            id_parceiro_novo = parceiro.id
            id_propriedade_novo = propriedade_existente.id
            db.commit()
            if origem in ('transfer', 'venda', 'posse') and id_propriedade_interna.isdecimal():
                return redirect(_url_transfer(id_propriedade_interna, doc_limpo, _TIPO_DA_ORIGEM.get(origem, 'TRANSFER')))
            return redirect(
                f'/produtor/gta-manual/nova'
                f'?id_parceiro={id_parceiro_novo}'
                f'&id_propriedade={id_propriedade_novo}'
                f'&id_propriedade_interna={id_propriedade_interna}'
            )

        propriedade = ParceiroPropriedades(
            id_parceiro=parceiro.id,
            estabelecimento=estabelecimento,
            codigo_mapa=codigo_mapa or None,
            insc_estadual=insc_estadual or None,
            municipio_codigo=municipio_codigo or None,
            municipio_nome=municipio_nome,
            uf=uf,
            regiao=regiao or None,
            ativo=True,
        )
        db.add(propriedade)
        db.flush()  # v1.2.1 - garante propriedade.id antes do commit

        # v1.2.1 - ids guardados ANTES do commit (depois dele nao se
        # le mais nada dos objetos do banco - regra da Sessao 078).
        id_parceiro_novo = parceiro.id
        id_propriedade_novo = propriedade.id

        db.commit()

    # v1.5.0 - veio da GTA de Transferencia: volta para ela com o CPF/CNPJ ja preenchido
    if origem in ('transfer', 'venda', 'posse') and id_propriedade_interna.isdecimal():
        return redirect(_url_transfer(id_propriedade_interna, doc_limpo, _TIPO_DA_ORIGEM.get(origem, 'TRANSFER')))

    # PENDENCIA (ver cabecalho): trocar por url_for('gta_manual.nova', ...)
    # assim que gta_manual.py ganhar a rota nova().
    return redirect(
        f'/produtor/gta-manual/nova'
        f'?id_parceiro={id_parceiro_novo}'
        f'&id_propriedade={id_propriedade_novo}'
        f'&id_propriedade_interna={id_propriedade_interna}'
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\parceiro_cadastro_manual.py
# =========================================================