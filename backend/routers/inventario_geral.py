# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\inventario_geral.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-24 11:15 -03
# ATUALIZADO EM: 2026-11-08 13:00 -03
# VERSAO: 1.6.0
# v1.6.0: Sessao 123 (2026-11-13 19:50 -03) - AUDITORIA ETAPA 6 (leitura a fundo): animal com Sexo vazio/invalido passa a ser ERRO GRAVE (antes contava no total e sumia do quadro Sexo x Faixa). REVERSAO: .bak_antes_etapa6d.
# v1.5.0: Sessao 118 (2026-11-08 13:00 -03) - Animais na BND: cada animal ganha a faixa de ERAS (calculada Hoje - Nascimento, a mesma conta do quadro-resumo). Cada tupla de animais passa a ter 5 itens (o 5o e a faixa). So o Animais na BND usa a lista. REVERSAO: .bak_antes_s118_eras.
#
# DESCRICAO:
#     Modulo Inventario Geral (Sessao 079) - 1o card do Hub de
#     Inventario (hubs.py v1.32.0, slug 'inventario'). Reproduz a
#     tela "Relatorio do Inventario Geral da Propriedade" do
#     legado GERAS. Navegacao real (Regra de Ouro #7): menu
#     lateral "Inventario" -> Hub de Inventario -> card
#     "Inventario Geral".
#
#     FLUXO (4 rotas):
#       1. /produtor/inventario-geral/iniciar - Padrao
#          Reutilizavel N.1 (Propriedade/Produtor). 1 unico par:
#          pula direto para a tela.
#       2. /produtor/inventario-geral/tela - Propriedade travada
#          (so exibicao) + 2 botoes, cada um gera um PDF:
#       3. /produtor/inventario-geral/animais-bnd - PDF "DIA's
#          DISPONIVEIS" (lista de animais + quadro por Especie).
#       4. /produtor/inventario-geral/saldo (v1.1.0) - PDF
#          "INVENTARIO DE ANIMAIS" (so os quadros por Especie +
#          assinaturas, 1 pagina).
#       Desenho dos 2 PDFs: backend/utils/pdf_inventario_geral.py.
#
#     CONTAGEM COMPARTILHADA (v1.1.0): as 2 rotas de PDF usam a
#     MESMA preparacao (_preparar_inventario) e a MESMA montagem
#     de blocos (_montar_blocos) - os numeros do Saldo e do
#     Animais na BND nunca podem divergir.
#
#     REGRAS DE NEGOCIO (fechadas com Benedito, Sessao 079):
#       - Animais considerados = VIVOS no rebanho da Propriedade
#         (tb_2001 - estoque = presenca na tb_2001).
#       - Um bloco por Especie (ordem alfabetica da descricao) -
#         SO as Especies que tem animal (sem Bubalinos, nao sai
#         quadro de Bubalinos). Animais em ordem de SISBOV
#         crescente, Indice CONTINUO entre as especies.
#       - SISBOV impresso com os 15 digitos corridos, SEM hifen
#         (v1.0.1 - nao existe mais digito verificador separado).
#       - Idade ATUAL (nunca gravada - Regras.txt secao 13):
#         calculada do Nascimento ate HOJE, em dias, e
#         enquadrada nas faixas da tb_4006 (dias_min/dias_max). As
#         2 primeiras faixas oficiais (ordem codigo_geras) sao
#         somadas numa so coluna "Zero a 12 Meses" - quadro com 4
#         colunas, igual ao legado.
#       - ERRO GRAVE: animal sem Nascimento (ou com Nascimento no
#         futuro, que nao cai em nenhuma faixa) BLOQUEIA os 2 PDFs
#         - a tela mostra os SISBOVs com problema (decisao de
#         Benedito: inventario e documento de conferencia, numero
#         errado e pior do que nao sair).
#       - NIRF: coluna real nirf_incra de public.propriedades
#         (confirmada via information_schema por Benedito) - lida
#         por SQL direto, pois o model Propriedade nao a mapeia
#         (Regra de Ouro #1 - nada presumido, model intocado).
#       - Estabelecimento Rural (Saldo) = propriedades.codigo_mapa
#         (confirmado por Benedito).
#       - Certificadora Responsavel (Saldo): ainda nao existem
#         Certificadoras cadastradas - linha sai em branco, so com
#         o rotulo, para preenchimento manual.
#
#     SEGURANCA: tela e PDFs conferem se o id_propriedade da URL
#     pertence mesmo aos pares Propriedade/Produtor do usuario
#     logado (nunca confiar so na URL).
#
#     v1.0.0: Criacao do modulo (Sessao 079, 24/09/2026, 11:15 -03).
#     v1.0.1: Sessao 079 (24/09/2026, 11:30 -03) - Correcao
#             apontada por Benedito no 1o teste real: o SISBOV
#             NAO tem mais digito verificador separado - o hifen
#             antes do ultimo digito (copiado do legado) foi
#             removido. Funcao de formatacao do SISBOV eliminada;
#             o numero vai direto para o PDF e para a lista de
#             ERRO GRAVE. Nenhuma outra mudanca.
#     v1.1.0: Sessao 079 (24/09/2026, 11:34 -03) - Botao "Saldo"
#             construido (modelo real do legado trazido por
#             Benedito). Mudancas:
#               - NOVA rota saldo() - PDF "INVENTARIO DE ANIMAIS".
#               - Preparacao comum extraida de animais_bnd() para
#                 NOVAS funcoes _preparar_inventario() (permissao,
#                 dados, catalogos, rebanho, ERRO GRAVE) e
#                 _montar_blocos() (agrupamento por Especie e
#                 contagem Sexo x Faixa) - usadas pelas 2 rotas.
#               - _buscar_dados_propriedade() passa a trazer
#                 tambem codigo_mapa (Estabelecimento Rural).
#             Comportamento do Animais na BND inalterado.
#     v1.2.0: Sessao 091 (08/10/2026, 20:00 -03) - FAZENDA EM USO (Regra de Ouro #13):
#         Com fazenda em uso a tela "Selecionar Propriedade" e pulada (iniciar()
#         abre direto a tela da fazenda). Voltar vai ao Hub de Inventario, sem passar
#         pela selecao. TRAVA: Propriedade da URL diferente da fazenda em uso e negada
#         (tela e os 2 PDFs) e volta ao iniciar(). Contagem e PDFs intactos.
#         REVERSAO: devolver a versao anterior.
#     v1.4.0: Sessao 116 (06/11/2026, 15:35 -03) - PRODUTOR LOGADO. A Propriedade passou a ter 2+ Produtores
#         (Alteracao de Posse) e a tela/PDFs pegavam o PRIMEIRO vinculo da Propriedade (mostrava a Maria
#         Angelica para o Sebastiao). Agora o Produtor e o da sessao (o mesmo cujo schema e lido).
#         _buscar_dados_propriedade() devolve tambem produtor_nome, cpf, cnpj, inscricao_estadual,
#         codigo_eras e cep, usados no cabecalho dos 2 PDFs (bloco igual ao dos Comunicados de Saida).
#         Contagem e regras do inventario intactas.
#         REVERSAO: .bak_antes_s116_produtor.
# =========================================================

from datetime import date

from flask import Blueprint, render_template, request, redirect, session
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, PropriedadeProdutor, Produtor
from backend.models.tb_2001_entradas import Entrada
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.documentos_produtor import documentos_do_produtor
from backend.utils.pdf_inventario_geral import gerar_pdf_inventario_geral, gerar_pdf_saldo


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
inventario_geral = Blueprint('inventario_geral', __name__)


# -------------------------------------------------------
# Mesma protecao de cache dos demais modulos por Produtor
# (Sessao 064) - evita tela antiga de outro Produtor no cache.
# -------------------------------------------------------
@inventario_geral.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


# -------------------------------------------------------
# Destinos do Voltar (Regra de Ouro #9 - caminho real):
#   - Hub de Inventario: origem real do fluxo (Regra #7).
#   - Tela de Selecionar Propriedade: so existe no caminho com
#     2+ pares Propriedade/Produtor.
# -------------------------------------------------------
VOLTAR_HUB = '/produtor/hub/inventario'
VOLTAR_SELECAO = '/produtor/inventario-geral/iniciar'

MENU_ATIVO = 'inventario'

# Titulo da 1a coluna do quadro-resumo (soma das 2 primeiras
# faixas oficiais da tb_4006 - igual ao legado).
TITULO_PRIMEIRA_FAIXA = 'Zero a 12 Meses'

# Quantos SISBOVs com problema aparecem na tela de erro (o resto
# vira "e mais N").
LIMITE_SISBOVS_ERRO = 30

SEXOS = ('FEMEA', 'MACHO')


# -------------------------------------------------------
# Funcao auxiliar: confere se o id_propriedade da URL pertence
# aos pares do usuario logado. Devolve a lista de pares (usada
# tambem para calcular o Voltar) ou None se nao pertencer.
# -------------------------------------------------------
def _pares_se_permitido(id_propriedade):
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    ids_permitidos = {str(par.id_propriedade) for par in pares}
    if str(id_propriedade) not in ids_permitidos:
        return None
    # v1.2.0 - TRAVA DA FAZENDA EM USO: Propriedade diferente da fazenda em uso = negado.
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and str(par_em_uso.id_propriedade) != str(id_propriedade):
        return None
    return pares


# -------------------------------------------------------
# v1.2.0 - Acesso negado: com fazenda em uso volta ao iniciar() (que abre a
# fazenda em uso); sem fazenda em uso, Home como antes. Nunca vai ao Home com
# fazenda em uso (o Home sem parametros apaga a fazenda em uso).
# -------------------------------------------------------
def _negado():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect('/produtor/inventario-geral/iniciar')
    return redirecionar_home()


# -------------------------------------------------------
# Funcao auxiliar: dados de exibicao da Propriedade (tela e
# PDFs), ja convertidos em dict dentro da sessao do banco.
# NIRF via SQL direto (coluna nirf_incra, fora do model).
# v1.1.0: + codigo_mapa (Estabelecimento Rural do Saldo).
# -------------------------------------------------------
def _buscar_dados_propriedade(id_propriedade):
    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
        if not propriedade:
            return None

        # v1.4.0: Produtor = o LOGADO (o mesmo cujo schema e lido no rebanho), nao o
        # primeiro vinculo da Propriedade. CPF/CNPJ pela rotina padrao dos Comunicados.
        nome_produtor = None
        cpf_produtor, cnpj_produtor = '', ''
        id_produtor_logado = int(session['id_produtor'])
        vinculo = db.query(PropriedadeProdutor).filter_by(
            id_propriedade=propriedade.id, id_produtor=id_produtor_logado, data_fim=None
        ).first()
        if vinculo:
            produtor = db.get(Produtor, id_produtor_logado)
            if produtor:
                nome_produtor = produtor.nome
                cpf_produtor, cnpj_produtor = documentos_do_produtor(produtor, vinculo)

        dados = {
            'nome': propriedade.nome,
            'municipio': propriedade.municipio,
            'uf': propriedade.uf,
            'codigo_mapa': propriedade.codigo_mapa,
            'nome_produtor': nome_produtor,
            'produtor_nome': nome_produtor,
            'cpf': cpf_produtor,
            'cnpj': cnpj_produtor,
            'inscricao_estadual': propriedade.inscricao_estadual,
            'codigo_eras': propriedade.codigo_eras,
            'cep': propriedade.cep,
        }

    with engine.connect() as conn:
        nirf = conn.execute(
            text('SELECT nirf_incra FROM public.propriedades WHERE id = :id'),
            {'id': int(id_propriedade)},
        ).scalar()
    dados['nirf'] = nirf

    return dados


# -------------------------------------------------------
# Funcao auxiliar: rotulo da Especie no plural (ex.: "BOVINO" ->
# "Bovinos").
# -------------------------------------------------------
def _rotulo_especie(descricao):
    if not descricao:
        return 'Sem Espécie'
    return descricao.strip().capitalize() + 's'


# -------------------------------------------------------
# Funcao auxiliar: posicao (0..3) da coluna do quadro-resumo
# para um animal com 'dias' de idade. As faixas vem em ordem
# oficial (codigo_geras); as 2 primeiras caem na coluna 0.
# Fora de todas as faixas: None (vira ERRO GRAVE no chamador).
# -------------------------------------------------------
def _coluna_da_idade(dias, faixas):
    for posicao, faixa in enumerate(faixas):
        if faixa['dias_min'] <= dias <= faixa['dias_max']:
            return max(posicao - 1, 0)
    return None


# -------------------------------------------------------
# Funcao auxiliar: renderiza a tela (com ou sem erro). O Voltar
# e calculado pelo numero real de pares (Regra de Ouro #9).
# -------------------------------------------------------
def _renderizar_tela(id_propriedade, pares, dados, erro=None, sisbovs_erro=None, qtde_extra_erro=0):
    url_voltar = VOLTAR_SELECAO if (len(pares) > 1 and resolver_fazenda_em_uso(pares) is None) else VOLTAR_HUB

    return render_template(
        'produtor/inventario_geral.html',
        id_propriedade=id_propriedade,
        dados=dados,
        erro=erro,
        sisbovs_erro=sisbovs_erro or [],
        qtde_extra_erro=qtde_extra_erro,
        url_voltar=url_voltar,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo=MENU_ATIVO,
    )


# -------------------------------------------------------
# Funcao (NOVA, v1.1.0): _preparar_inventario() - tudo o que os
# 2 PDFs precisam ANTES do desenho. Devolve (resposta, contexto):
#   - resposta != None -> a rota devolve ela direto (redirect por
#     permissao, ou a tela com erro/ERRO GRAVE);
#   - senao, contexto = dict com dados, especies, colunas_faixas
#     e animais (cada animal ja com a sua 'coluna' de idade).
# Etapas:
#   1. Permissao + dados da Propriedade.
#   2. Catalogos (Especie e faixas de idade).
#   3. Rebanho vivo (tb_2001) da Propriedade, por SISBOV.
#   4. Idade atual + conferencia de ERRO GRAVE.
# -------------------------------------------------------
def _preparar_inventario(id_propriedade):
    # ---- 1. Permissao + dados da Propriedade ----
    pares = _pares_se_permitido(id_propriedade) if id_propriedade else None
    if not pares:
        return _negado(), None

    dados = _buscar_dados_propriedade(id_propriedade)
    if not dados:
        return redirecionar_home(), None

    # ---- 2. Catalogos do schema public ----
    with engine.connect() as conn:
        especies = {
            row['id']: row['descricao']
            for row in conn.execute(text('SELECT id, descricao FROM public.tb_4002_especie')).mappings().all()
        }
        faixas = [
            dict(row) for row in conn.execute(text(
                'SELECT id, descricao, dias_min, dias_max '
                'FROM public.tb_4006_idade_meses ORDER BY codigo_geras'
            )).mappings().all()
        ]
    colunas_faixas = [TITULO_PRIMEIRA_FAIXA] + [f['descricao'] for f in faixas[2:]]

    # ---- 3. Rebanho vivo (valores copiados DENTRO da sessao) ----
    with get_db_produtor(session['id_produtor']) as db:
        registros = (
            db.query(Entrada)
            .filter_by(id_propriedade=int(id_propriedade))
            .order_by(Entrada.sisbov)
            .all()
        )
        animais = [{
            'sisbov': r.sisbov,
            'rfid': r.rfid,
            'id_especie': r.id_especie,
            'sexo': r.sexo,
            'nascimento': r.nascimento,
        } for r in registros]

    if not animais:
        return _renderizar_tela(
            id_propriedade, pares, dados,
            erro='Nenhum animal no rebanho desta Propriedade — não há inventário para imprimir.',
        ), None

    # ---- 4. Idade atual + ERRO GRAVE ----
    hoje = date.today()
    sisbovs_com_problema = []
    for animal in animais:
        coluna = None
        if animal['nascimento']:
            coluna = _coluna_da_idade((hoje - animal['nascimento']).days, faixas)
        animal['coluna'] = coluna
        if coluna is None or animal['sexo'] not in SEXOS:
            sisbovs_com_problema.append(animal['sisbov'] or '')

    if sisbovs_com_problema:
        return _renderizar_tela(
            id_propriedade, pares, dados,
            erro=(
                f'ERRO GRAVE — Inventário não gerado: {len(sisbovs_com_problema)} animal(is) '
                f'sem Data de Nascimento válida ou sem Sexo válido. Corrija antes de imprimir.'
            ),
            sisbovs_erro=sisbovs_com_problema[:LIMITE_SISBOVS_ERRO],
            qtde_extra_erro=max(len(sisbovs_com_problema) - LIMITE_SISBOVS_ERRO, 0),
        ), None

    return None, {
        'dados': dados,
        'especies': especies,
        'colunas_faixas': colunas_faixas,
        'animais': animais,
    }


# -------------------------------------------------------
# Funcao (NOVA, v1.1.0): _montar_blocos() - agrupa por Especie
# (ordem alfabetica, so Especies com animal) e conta Sexo x
# Faixa. Mesma conta para os 2 PDFs. Cada bloco:
#   'rotulo'  - ex.: 'Bovinos'
#   'animais' - lista de (indice, sisbov, rfid, sexo M/F), Indice continuo
#               entre especies (usada so pelo Animais na BND)
#   'resumo'  - {'FEMEA': [4 ints], 'MACHO': [4 ints]}
#   'total'   - total de animais da especie
# -------------------------------------------------------
def _montar_blocos(contexto):
    especies = contexto['especies']
    qtde_colunas = len(contexto['colunas_faixas'])
    qtde_faixas_nomes = contexto['colunas_faixas']   # s118 - nome da faixa de cada coluna (ERAS por animal)

    por_especie = {}
    for animal in contexto['animais']:
        por_especie.setdefault(animal['id_especie'], []).append(animal)

    ids_ordenados = sorted(por_especie.keys(), key=lambda i: (especies.get(i) or '').upper())

    blocos = []
    indice = 0
    for id_especie in ids_ordenados:
        lista = por_especie[id_especie]
        resumo = {sexo: [0] * qtde_colunas for sexo in SEXOS}
        linhas = []
        for animal in lista:
            indice += 1
            # s118 - 5o item = faixa de ERAS do animal (mesma coluna usada no quadro-resumo)
            linhas.append((indice, animal['sisbov'] or '', animal['rfid'], {'MACHO': 'M', 'FEMEA': 'F'}.get(animal['sexo'], ''),
                           qtde_faixas_nomes[animal['coluna']]))
            if animal['sexo'] in SEXOS:
                resumo[animal['sexo']][animal['coluna']] += 1

        blocos.append({
            'rotulo': _rotulo_especie(especies.get(id_especie)),
            'animais': linhas,
            'resumo': resumo,
            'total': len(lista),
        })

    return blocos


# -------------------------------------------------------
# Rota: GET /produtor/inventario-geral/iniciar — ponto de
# partida (Padrao Reutilizavel N.1). Com 1 unico par, pula
# direto para a tela.
# -------------------------------------------------------
@inventario_geral.route('/produtor/inventario-geral/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    # v1.2.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/inventario-geral/tela?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/inventario-geral/tela?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None if pares else 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
        titulo='Inventário Geral — Selecionar Propriedade',
        proximo='/produtor/inventario-geral/tela',
        campo_propriedade='id_propriedade',
        voltar=VOLTAR_HUB,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo=MENU_ATIVO,
    )


# -------------------------------------------------------
# Rota: GET /produtor/inventario-geral/tela?id_propriedade=X —
# tela com a Propriedade travada e os 2 botoes.
# -------------------------------------------------------
@inventario_geral.route('/produtor/inventario-geral/tela')
def tela():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    pares = _pares_se_permitido(id_propriedade) if id_propriedade else None
    if not pares:
        return _negado()

    dados = _buscar_dados_propriedade(id_propriedade)
    if not dados:
        return redirecionar_home()

    return _renderizar_tela(id_propriedade, pares, dados)


# -------------------------------------------------------
# Rota: GET /produtor/inventario-geral/animais-bnd?id_propriedade=X
# — PDF "DIA's DISPONIVEIS" (lista + quadro por Especie).
# -------------------------------------------------------
@inventario_geral.route('/produtor/inventario-geral/animais-bnd')
def animais_bnd():
    if 'id_produtor' not in session:
        return redirecionar_home()

    resposta, contexto = _preparar_inventario(request.args.get('id_propriedade', ''))
    if resposta is not None:
        return resposta

    blocos = _montar_blocos(contexto)
    return gerar_pdf_inventario_geral(blocos, contexto['colunas_faixas'], contexto['dados'])


# -------------------------------------------------------
# Rota (NOVA, v1.1.0): GET /produtor/inventario-geral/saldo?
# id_propriedade=X — PDF "INVENTARIO DE ANIMAIS" (so quadros por
# Especie + assinaturas). Mesma preparacao e mesma contagem do
# Animais na BND.
# -------------------------------------------------------
@inventario_geral.route('/produtor/inventario-geral/saldo')
def saldo():
    if 'id_produtor' not in session:
        return redirecionar_home()

    resposta, contexto = _preparar_inventario(request.args.get('id_propriedade', ''))
    if resposta is not None:
        return resposta

    blocos = _montar_blocos(contexto)
    return gerar_pdf_saldo(blocos, contexto['colunas_faixas'], contexto['dados'])

# =========================================================
# FIM DE ARQUIVO: backend\routers\inventario_geral.py
# =========================================================