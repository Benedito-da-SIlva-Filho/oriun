# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\gta_manual.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-08-21 14:41 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.17.0
# v1.17.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (4 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.16.0: Sessao 122 (2026-11-12 19:00 -03) - Auditoria Etapa 4 (Entradas): Procedencia conferida (numero, existe, do Parceiro); Sucesso respeita a fazenda em uso. REVERSAO: .bak_antes_s122_etapa2.
# v1.15.0: Sessao 120 (2026-11-10 12:43 -03) - Rota nova gta-checar (JSON): confere NA HORA se a GTA de Entrada digitada ja existe, para a tela mostrar a tarja vermelha e travar o preenchimento. O Salvar continua conferindo no servidor. REVERSAO: .bak_antes_s120_gta_dup.
# v1.14.0: Sessao 118 (2026-11-08 15:00 -03) - Preenchimento Manual abre direto o formulario; a Procedencia (CPF/CNPJ + Buscar) fica dentro dele, como no destino da Venda. REVERSAO: .bak_antes_s118_compra
#
# DESCRICAO:
#     Fluxo completo da GTA Manual (Sessao 036/037). PRIMEIRA
#     GRAVACAO REAL de GTA no projeto (tb_4001_gta +
#     tb_4001_gta_animais) - o fluxo automatico via upload de
#     PDF (gta_compra.py) ainda nao grava, so testa o
#     resolver_parceiro().
#
#     ORDEM DO FLUXO (ver v1.0.0 para o historico completo):
#       1. /produtor/gta-manual/iniciar - resolve Propriedade
#          E Produtor (Destino). v1.4.0: passou a usar
#          auth.buscar_pares_propriedade_produtor() (P-036).
#       2. /produtor/parceiro-manual - resolve/cadastra a
#          Procedencia (Parceiro externo). Ja construido.
#       3. /produtor/gta-manual/nova - formulario completo da
#          GTA, com Procedencia e Destino ja resolvidos e
#          exibidos so para conferencia (nao editaveis - vieram
#          de cadastro, nao de transcricao de documento).
#       4. /produtor/gta-manual/salvar - grava em tb_4001_gta +
#          tb_4001_gta_animais, dentro do schema do Produtor
#          logado (get_db_produtor).
#
#     ESCOPO DESTA VERSAO: SEM checagem de estoque/Brincagem
#     (decisao de Benedito, Sessao 036 - a Brincagem acontece em
#     momento separado, a juncao dos dois arquivos so ocorre no
#     futuro Gerar Comunicado). Idade por categoria usa as 5
#     faixas fixas normatizadas. Especie (v1.6.0) vem do catalogo
#     tb_4002_especie via backend\utils\especies.py: o dropdown
#     MOSTRA a descricao ("Bovino") e GRAVA o codigo ("BOV") -
#     regra de Benedito, Sessao 082. Sexo usa dropdown fixo
#     (MACHO/FEMEA, sem acento - decisao de Benedito, Sessao 037,
#     mesmo padrao ja usado na leitura automatica). Campo Qtde de
#     Animais na GTA e declarado no topo e conferido contra a soma
#     das categorias incluidas antes de permitir salvar (mesmo
#     espirito do GERAS real, telas mostradas por Benedito nesta
#     sessao).
#
#     tipo_movimento e sentido fixos, mesmo padrao do fluxo
#     automatico (gta_compra.py): COMPRA / ENTRADA.
#
#     id_propriedade (interno/Destino) e id_parceiro_propriedade
#     (externo/Procedencia) sao os dois lados que tb_4001_gta ja
#     precisa - nenhum dado de Procedencia/Destino e duplicado
#     em texto livre na tabela (diferente do que dados_lidos
#     fazia no fluxo automatico) - a tela so exibe, buscando ao
#     vivo em Parceiro/ParceiroPropriedades/Propriedade.
#
#     REGRA DE NEGOCIO (mesma logica de gta_compra.py) - Data de
#     Entrega: janela Emissao <= Entrega <= Validade, com
#     tolerancia de +30 dias quando Meio de Transporte for
#     exatamente "COMITIVA". v1.6.1: a Entrega tambem NUNCA pode
#     ser futura (depois de hoje) - e o dia em que os animais
#     chegaram de fato.
#
#     STATUS DA BRINCAGEM (v1.6.1): toda GTA de Compra gravada aqui
#     nasce com status_brincagem = 'PENDENTE' - e o que a faz
#     aparecer na Brincagem Sequencial e no Vincular GTA.
#
#     v1.0.0: Criacao do modulo (Sessao 036/037) - so o passo 1
#             (iniciar + selecionar_propriedade).
#     v1.1.0: Sessao 036/037 (15:10) - Adicionadas as rotas
#             nova() e salvar() - formulario completo e gravacao
#             real da GTA. Primeira gravacao de verdade em
#             tb_4001_gta/tb_4001_gta_animais no projeto. Sexo
#             validado como MACHO/FEMEA (sem acento).
#     v1.2.0: Sessao 037 (15:36) - _buscar_dados_exibicao()
#             passou a trazer, para os dois lados (Procedencia e
#             Destino), os MESMOS campos da e-GTA fisica - Nome,
#             CPF/CNPJ, Regiao, Codigo MAPA, Insc. Estadual,
#             Municipio/UF (nome/CPF do Produtor do Destino via
#             PropriedadeProdutor + Produtor, vinculo ativo).
#     v1.3.0: Sessao 037 (16:00) - Serie = exatamente 1 letra;
#             Numero = exatamente 6 digitos (zfill); Meio de
#             Transporte validado contra lista fixa
#             (MEIOS_TRANSPORTE_VALIDOS), mantendo "COMITIVA".
#     v1.4.0: Sessao (26/08/2026, 15:23 -03) - Resolve P-036:
#             iniciar() passa a usar
#             auth.buscar_pares_propriedade_produtor() (resolve
#             Propriedade E Produtor juntos) e o template
#             compartilhado selecionar_propriedade_produtor.html.
#     v1.5.0: Sessao 056 (18/09/2026, 11:40 -03) - BUG REAL: os 2
#             render_template() de iniciar() nao passavam
#             'voltar' (Voltar ia para /produtor/home). Agora
#             voltar='/produtor/entrada/compra/nova' e titulo
#             'GTA Manual — Selecionar Propriedade'.
#     v1.5.1: Sessao 080 (25/09/2026, 18:00 -03) - VARREDURA do
#             vicio "ler do banco depois do commit()" (Sessoes
#             078/079/080): salvar() lia gta.id DEPOIS do
#             db.commit() - o objeto expira e a releitura acontece
#             sem o schema do Produtor, estourando erro APOS gravar
#             (o usuario tentaria de novo e DUPLICARIA a GTA). O id
#             agora e guardado ANTES do commit. Nenhuma outra
#             mudanca.
#     v1.6.0: Sessao 082 (29/09/2026, 06:55 -03) - BUG REAL que
#             travava TODA Brincagem Sequencial de Compra: a lista
#             fixa ESPECIES_VALIDAS = ['BOVINO', 'BUBALINO'] fazia a
#             GTA Manual gravar a especie POR EXTENSO em
#             tb_4001_gta_animais, e a Sequencial procura o CODIGO
#             do catalogo ("BOV"). Regra de Benedito: banco com
#             codigo, tela com a palavra. Mudancas:
#               - ESPECIES_VALIDAS REMOVIDA (era importada tambem
#                 por gta_consulta.py - atualizado junto, v1.13.0).
#               - nova()/salvar() passam ao template a lista do
#                 catalogo (carregar_especies() - dicts com codigo
#                 e descricao); o dropdown mostra "Bovino" e envia
#                 "BOV" (gta_manual_cadastro.html v1.8.0).
#               - _ler_animais_do_formulario() converte a especie
#                 recebida para o codigo (codigo_da_especie()) -
#                 aceita "BOV" ou "BOVINO".
#               - Validacao no servidor contra codigos_validos().
#             Dados antigos convertidos por SQL (Tabelas\
#             converter_especie_codigo_s082.sql). Nenhuma outra
#             mudanca.
#     v1.6.1: Sessao 082 (29/09/2026, 11:30 -03) - 2 correcoes
#             achadas em teste real de Benedito (GTA MGQ258741
#             cadastrada e "invisivel" no Vincular GTA):
#               - BUG REAL: salvar() nunca definia status_brincagem
#                 - a GTA nascia com o padrao da coluna,
#                 'NAO_APLICA', e NAO aparecia na Brincagem
#                 Sequencial nem no Vincular GTA (os dois so listam
#                 'PENDENTE'). Defeito existente desde a criacao da
#                 coluna (Sessao 048); as GTAs anteriores tinham
#                 sido acertadas pelo script daquela sessao. Agora
#                 toda GTA de Compra nasce 'PENDENTE'
#                 (STATUS_BRINCAGEM_INICIAL). GTAs ja gravadas
#                 acertadas por Tabelas\
#                 acertar_status_brincagem_gta_manual_s082.sql
#                 (executado: 1 GTA no Zopone).
#               - NOVA TRAVA (decisao de Benedito): Data de Entrega
#                 nao pode ser futura. Caso real: ano digitado 2029
#                 em vez de 2026 - a GTA passava (Entrega dentro de
#                 Emissao/Validade, todas em 2029) e o problema so
#                 aparecia no Vincular, como pendencia em todos os
#                 animais. Mesma trava no Alterar (gta_consulta.py
#                 v1.13.1). Emissao e Validade NAO travadas (GTA
#                 pode ter validade futura legitima).
#             Nenhuma outra mudanca.
#     v1.7.0: Sessao 085 (04/10/2026, 17:50 -03) - GTA DUPLICADA (regra
#             de Benedito: jamais duas GTAs iguais - UF + Serie + Numero
#             + sentido, dentro do mesmo Produtor; ver backend/utils/
#             gta_duplicada.py). salvar() agora confere ANTES de gravar:
#             logo apos validar UF/Serie/Numero (o usuario ve o problema
#             primeiro, sem corrigir os outros campos a toa) e avisa com
#             a mensagem padrao, sem gravar nada. Se duas pessoas salvarem
#             a mesma GTA ao mesmo tempo, a trava do banco (constraint
#             uq_tb_4001_gta_uf_serie_numero_sentido) recusa a segunda -
#             o IntegrityError e tratado (rollback) e vira a mesma
#             mensagem. Nenhuma outra mudanca.
#     v1.8.0: Sessao 085 (04/10/2026, 18:20 -03) - SERIE DA GTA POR UF
#             (regra de Benedito: Goias com 2 letras, demais UFs com 1 -
#             regras_sisbov.py v1.4.0). salvar() valida o tamanho da Serie
#             conforme a UF escolhida (antes: sempre 1 letra) e a mensagem
#             diz quantas letras. Numero continua com 6 digitos.
#             gta_manual_cadastro.html v1.10.0 ajusta o campo na tela.
#             Nenhuma outra mudanca.
#     v1.9.0: Sessao 087 (05/10/2026, 11:05 -03) - VOLTAR PELO CAMINHO
#             INVERSO (Regra de Ouro #4, pedido de Benedito): a tela de
#             sucesso mandava "Lancar Outra GTA Manual" para o inicio do
#             fluxo (Selecao de Propriedade). sucesso() agora monta
#             url_proxima = Cadastro do Parceiro com a Propriedade e o
#             CPF/CNPJ da Procedencia da GTA gravada ja preenchidos (le
#             id_propriedade e id_parceiro_propriedade da propria GTA),
#             para o usuario seguir lancando GTAs do mesmo Parceiro.
#             Sem esses dados, cai em /produtor/gta-manual/iniciar.
#             gta_manual_sucesso.html v1.1.0 usa url_proxima. Nenhuma
#             outra mudanca.
#     v1.10.0: Sessao 090 (08/10/2026, 08:10 -03) - FAZENDA EM USO (Lote 3):
#             FAZENDA EM USO (Regra de Ouro #13): a tela "Selecionar Propriedade" deixa
#             de aparecer quando ha fazenda em uso (auth.resolver_fazenda_em_uso).
#               - iniciar(): com fazenda em uso, PULA a selecao e abre o
#                 Cadastro do Parceiro direto na fazenda em uso. Sem fazenda
#                 em uso, ou com 1 par so, tudo igual a antes.
#               - TRAVA (_fora_da_fazenda_em_uso): nova() e salvar() recusam
#                 Propriedade diferente da fazenda em uso (trocada em outra
#                 aba) e mandam para o iniciar(). Nada e gravado.
#             Nenhuma mudanca em regras de negocio, validacoes e gravacao.
#     v1.11.0: Sessao 094 (12/10/2026, 20:30 -03) - AUDITORIA DE COMPRAS: _fora_da_fazenda_em_uso() tambem recusa Propriedade destino vazia, nao numerica ou que
#             nao pertence ao usuario (antes passava e podia dar erro 500). Nenhuma outra mudanca.
#             REVERSAO: devolver .bak_antes_auditoria_compras.
#     v1.12.0: Sessao 102 (21/10/2026, 09:20 -03) - UF DUPLICADA: novo helper municipio_sem_uf() tira o " / UF"
#             que o nome do municipio ja traz (ex.: "MANAUS / AM"). _buscar_dados_exibicao() passa a devolver
#             municipio_nome limpo (Procedencia e Destino); as telas e PDFs ja somam a UF uma vez so.
#             Nenhuma outra mudanca. REVERSAO: devolver .bak_antes_uf_s102.
#     v1.13.0: Sessao 104 (23/10/2026, 12:40 -03) - TRILHA DE AUDITORIA: salvar() registra no Log de Operacoes (quem lancou a GTA e quando),
#             modulo 'gta_manual', so-historico (sem Desfazer). REVERSAO: .bak_antes_s104i.
#     v1.13.1: Sessao 117 (2026-11-06 18:05 -03) - Destino da GTA mostra o Produtor LOGADO, nao o primeiro vinculo da Propriedade (defeito com 2+ Produtores). CPF/CNPJ nao mexido. REVERSAO: .bak_antes_s117_produtor.
# =========================================================

from datetime import datetime, date, timedelta
from types import SimpleNamespace
from flask import Blueprint, render_template, request, redirect, session, jsonify

from backend.database import engine
from backend.models import Propriedade, PropriedadeProdutor, Produtor
from backend.models.tb_parceiros import Parceiro
from backend.models.tb_parceiros_propriedades import ParceiroPropriedades
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4001_gta_animais import GtaAnimal
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.log_operacoes import registrar_operacao, registrar_item   # v1.13.0 - trilha de auditoria
from backend.utils.regras_sisbov import tamanho_serie_gta, mensagem_serie_gta
from backend.utils.especies import carregar_especies, codigo_da_especie, codigos_validos
from backend.utils.gta_duplicada import buscar_gta_duplicada, mensagem_gta_duplicada, eh_violacao_unicidade_gta
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
gta_manual = Blueprint('gta_manual', __name__)

# -------------------------------------------------------
# Fixos desta tela (nunca escolhidos pelo usuario) - mesmo
# padrao do fluxo automatico (gta_compra.py).
# -------------------------------------------------------
SENTIDO_FIXO         = 'ENTRADA'
TIPO_MOVIMENTO_FIXO  = 'COMPRA'

# v1.6.1 - toda GTA de Compra nasce pendente de Brincagem (e o que
# a faz aparecer na Brincagem Sequencial e no Vincular GTA).
STATUS_BRINCAGEM_INICIAL = 'PENDENTE'

MEIO_TRANSPORTE_COMITIVA  = 'COMITIVA'
TOLERANCIA_COMITIVA_DIAS  = 30

# -------------------------------------------------------
# Meios de Transporte validos (Sessao 037) - combo fixo,
# substituindo o texto livre anterior. O valor interno da
# opcao "A Pe (Comitiva/Tocada)" continua sendo exatamente
# "COMITIVA", para nao quebrar a regra de tolerancia de 30
# dias na Data de Entrega, ja validada e em uso.
# -------------------------------------------------------
MEIOS_TRANSPORTE_VALIDOS = ['RODOVIARIO', 'COMITIVA', 'FLUVIAL_MARITIMO', 'FERROVIARIO', 'AEREO']

# -------------------------------------------------------
# Faixas de Idade normatizadas (Sessao 037) - a data real
# informada em campo (marca/fogo, ou idade em meses) e
# classificada pelo usuario dentro de uma destas faixas na PIA,
# nao fica solta como texto livre.
# -------------------------------------------------------
FAIXAS_IDADE = ['Zero a 04 Meses', '04 a 12 Meses', '13 a 24 Meses', '25 a 36 Meses', '+36 Meses']

# v1.6.0: ESPECIES_VALIDAS (lista fixa por extenso) REMOVIDA - a
# Especie vem do catalogo tb_4002 (backend\utils\especies.py).

# Sem acento - decisao de Benedito (Sessao 037), mesmo padrao ja
# usado na leitura automatica de e-GTA.
SEXOS_VALIDOS = ['MACHO', 'FEMEA']

# -------------------------------------------------------
# Destino do botao "Voltar" da tela compartilhada de Selecionar
# Propriedade (Regra de Ouro, Sessao 051 - ver
# selecionar_propriedade_produtor.html): SEMPRE a tela
# imediatamente anterior deste fluxo especifico - o card
# "GTA Preenchimento Manual" fica em
# /produtor/entrada/compra/nova (Sessao 056, v2.14.0 do
# template gta_compra_cadastro.html).
# -------------------------------------------------------
VOLTAR_SELECIONAR_PROPRIEDADE = '/produtor/entrada/compra/nova'


# -------------------------------------------------------
# TRAVA DA FAZENDA EM USO (v1.10.0 / Sessao 090 - Lote 3).
# True quando ha fazenda em uso e a Propriedade informada e DIFERENTE dela
# (ex.: a fazenda foi trocada em outra aba). Nesse caso a rota nao le e nao
# grava nada e manda para o iniciar(), que abre a fazenda em uso.
# -------------------------------------------------------
def _fora_da_fazenda_em_uso(id_propriedade_interna):
    # v1.11.0 - tambem recusa Propriedade vazia/nao numerica ou que nao e do usuario.
    if not str(id_propriedade_interna).isdecimal():
        return True
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if int(id_propriedade_interna) not in {int(par.id_propriedade) for par in pares}:
        return True
    par_em_uso = resolver_fazenda_em_uso(pares)
    return par_em_uso is not None and int(par_em_uso.id_propriedade) != int(id_propriedade_interna)


# -------------------------------------------------------
# Rota: GET /produtor/gta-manual/iniciar — ponto de partida do
# fluxo manual.
#
# v1.4.0 (P-036): resolve Propriedade E Produtor juntos, via
# auth.buscar_pares_propriedade_produtor() - cobre tanto o caso
# de 1 Produtor com varias Propriedades (Claudenor) quanto o de
# um usuario com vinculo ativo em mais de um Produtor ao mesmo
# tempo (Fazenda Olho D'Agua). Com 1 unico par, segue direto -
# mesmo comportamento de sempre.
#
# v1.5.0: os 2 render_template() abaixo (erro e pares) agora
# passam 'voltar' e o 'titulo' no formato correto - ver
# changelog v1.5.0 no topo do arquivo para a causa raiz do bug.
# -------------------------------------------------------
@gta_manual.route('/produtor/gta-manual/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            titulo='GTA Manual — Selecionar Propriedade',
            proximo='/produtor/gta-manual/nova',
            campo_propriedade='id_propriedade_interna',
            voltar=VOLTAR_SELECIONAR_PROPRIEDADE,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='entrada',
        )

    # v1.10.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade" e abre o
    # Cadastro do Parceiro direto na fazenda em uso.
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/gta-manual/nova?id_propriedade_interna={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/gta-manual/nova?id_propriedade_interna={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        titulo='GTA Manual — Selecionar Propriedade',
        proximo='/produtor/gta-manual/nova',
        campo_propriedade='id_propriedade_interna',
        voltar=VOLTAR_SELECIONAR_PROPRIEDADE,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Funcao auxiliar: busca os dados de exibicao de Procedencia
# (Parceiro + Propriedade externa) e Destino (Propriedade
# interna + Produtor vinculado), para mostrar na tela do
# formulario. So leitura, so para conferencia visual - nao
# grava nada.
#
# v1.2.0: os dois lados passaram a trazer os MESMOS campos que
# aparecem na e-GTA fisica (Nome, CPF/CNPJ, Regiao, Codigo MAPA,
# Insc. Estadual, Municipio/UF) - quanto mais informacao para
# conferencia, maior a chance do usuario detectar um erro antes
# de salvar (motivacao de Benedito, caso real da familia Jose
# Jr). O nome/CPF do Produtor do lado Destino vem de uma
# consulta extra em PropriedadeProdutor + Produtor (vinculo
# ativo, data_fim IS NULL).
# -------------------------------------------------------
# -------------------------------------------------------
# Helper (v1.12.0): tira do nome do municipio o sufixo " / UF" quando
# ele ja vem gravado junto (ex.: "MANAUS / AM" -> "MANAUS"). Evita
# "MANAUS / AM / AM" nas telas e PDFs que somam a UF depois. Repete
# enquanto houver sufixo. Sem UF ou sem sufixo: devolve igual.
# -------------------------------------------------------
def municipio_sem_uf(nome, uf):
    if not nome or not uf:
        return nome
    nome = str(nome).strip()
    sufixo = ' / ' + str(uf).strip().upper()
    while nome.upper().endswith(sufixo):
        nome = nome[:-len(sufixo)].rstrip()
    return nome


def _buscar_dados_exibicao(id_produtor, id_parceiro, id_propriedade_externa, id_propriedade_interna):
    procedencia = None
    destino = None

    with get_db_produtor(id_produtor) as db:
        parceiro = db.get(Parceiro, int(id_parceiro)) if id_parceiro else None
        propriedade_externa = db.get(ParceiroPropriedades, int(id_propriedade_externa)) if id_propriedade_externa else None

        if parceiro and propriedade_externa:
            procedencia = SimpleNamespace(
                nome=parceiro.nome,
                cpf_cnpj=parceiro.cpf_cnpj,
                estabelecimento=propriedade_externa.estabelecimento,
                regiao=propriedade_externa.regiao,
                codigo_mapa=propriedade_externa.codigo_mapa,
                insc_estadual=propriedade_externa.insc_estadual,
                municipio_nome=municipio_sem_uf(propriedade_externa.municipio_nome, propriedade_externa.uf),   # v1.12.0
                uf=propriedade_externa.uf,
            )

    with Session(engine) as db:
        propriedade_interna = db.get(Propriedade, int(id_propriedade_interna)) if id_propriedade_interna else None

        if propriedade_interna:
            nome_produtor = None
            cpf_cnpj_produtor = None

            vinculo = db.query(PropriedadeProdutor).filter_by(
                id_propriedade=propriedade_interna.id,
                id_produtor=id_produtor,   # v1.13.1: Produtor LOGADO
                data_fim=None
            ).first()

            if vinculo:
                produtor = db.get(Produtor, vinculo.id_produtor)
                if produtor:
                    nome_produtor = produtor.nome
                    cpf_cnpj_produtor = produtor.cpf_cnpj

            destino = SimpleNamespace(
                nome=propriedade_interna.nome,
                produtor_nome=nome_produtor,
                cpf_cnpj=cpf_cnpj_produtor,
                regiao=propriedade_interna.regiao,
                codigo_mapa=propriedade_interna.codigo_mapa,
                insc_estadual=propriedade_interna.inscricao_estadual,
                municipio_nome=municipio_sem_uf(propriedade_interna.municipio, propriedade_interna.uf),   # v1.12.0
                uf=propriedade_interna.uf,
            )

    return procedencia, destino


# -------------------------------------------------------
# Rota: GET /produtor/gta-manual/nova — formulario completo da
# GTA Manual. Recebe id_parceiro, id_propriedade (externa) e
# id_propriedade_interna na querystring, ja resolvidos pelos
# passos anteriores do fluxo.
# v1.6.0: especies vem do catalogo (dicts codigo/descricao).
# -------------------------------------------------------
@gta_manual.route('/produtor/gta-manual/nova')
def nova():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_parceiro             = request.args.get('id_parceiro', '')
    id_propriedade          = request.args.get('id_propriedade', '')
    id_propriedade_interna  = request.args.get('id_propriedade_interna', '')

    # v1.10.0 - trava da fazenda em uso.
    if _fora_da_fazenda_em_uso(id_propriedade_interna):
        return redirect('/produtor/gta-manual/iniciar')

    especies = carregar_especies()

    # s118 - sem Procedencia ainda: abre o formulario direto, com Buscar CPF/CNPJ na Procedencia (igual ao destino da Venda)
    if id_propriedade_interna and not (id_parceiro and id_propriedade):
        _p, destino = _buscar_dados_exibicao(session['id_produtor'], '', '', id_propriedade_interna)
        return render_template(
            'produtor/gta_manual_cadastro.html',
            erro=None,
            procedencia=None,
            destino=destino,
            gta=None,
            animais=[],
            ids=SimpleNamespace(id_parceiro='', id_propriedade='', id_propriedade_interna=id_propriedade_interna),
            escolher_procedencia=True,
            faixas_idade=FAIXAS_IDADE,
            especies=especies,
            sexos=SEXOS_VALIDOS,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='entrada',
        )

    if not (id_parceiro and id_propriedade and id_propriedade_interna):
        return render_template(
            'produtor/gta_manual_cadastro.html',
            erro='Dados de Procedência/Destino incompletos. Reinicie o fluxo pelo link de Preenchimento Manual.',
            procedencia=None,
            destino=None,
            gta=None,
            animais=[],
            ids=None,
            faixas_idade=FAIXAS_IDADE,
            especies=especies,
            sexos=SEXOS_VALIDOS,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='entrada',
        )

    procedencia, destino = _buscar_dados_exibicao(
        session['id_produtor'], id_parceiro, id_propriedade, id_propriedade_interna
    )

    ids = SimpleNamespace(
        id_parceiro=id_parceiro,
        id_propriedade=id_propriedade,
        id_propriedade_interna=id_propriedade_interna,
    )

    return render_template(
        'produtor/gta_manual_cadastro.html',
        erro=None,
        procedencia=procedencia,
        destino=destino,
        gta=None,
        animais=[],
        ids=ids,
        faixas_idade=FAIXAS_IDADE,
        especies=especies,
        sexos=SEXOS_VALIDOS,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Funcao auxiliar: le as linhas dinamicas da tabela de Animais
# vindas do formulario (arrays especie[]/sexo[]/idade_faixa[]/
# quantidade[]).
# v1.6.0: a especie e convertida para o CODIGO do catalogo
# ("BOV") - aceita "BOV" ou "BOVINO". Texto que nao existe no
# catalogo fica como veio (a validacao do salvar() recusa).
# -------------------------------------------------------
def _ler_animais_do_formulario(especies):
    especies_form = request.form.getlist('especie[]')
    sexos         = request.form.getlist('sexo[]')
    idades        = request.form.getlist('idade_faixa[]')
    quantidades   = request.form.getlist('quantidade[]')

    animais = []
    for especie, sexo, idade, quantidade in zip(especies_form, sexos, idades, quantidades):
        especie = (especie or '').strip().upper()
        sexo    = (sexo or '').strip().upper()
        idade   = (idade or '').strip()
        qtd_str = (quantidade or '').strip()

        if not especie and not sexo and not idade and not qtd_str:
            continue

        try:
            qtd = int(qtd_str)
        except ValueError:
            qtd = 0

        animais.append({
            'especie':     codigo_da_especie(especie, especies) or especie,
            'sexo':        sexo,
            'idade_meses': idade,
            'quantidade':  qtd,
        })

    return animais


# -------------------------------------------------------
# Rota: POST /produtor/gta-manual/salvar — valida e grava a GTA
# de verdade em tb_4001_gta + tb_4001_gta_animais (schema do
# Produtor logado).
# v1.6.0: especie validada contra os codigos do catalogo.
# -------------------------------------------------------
@gta_manual.route('/produtor/gta-manual/salvar', methods=['POST'])
def salvar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_produtor = session['id_produtor']

    id_parceiro             = request.form.get('id_parceiro', '')
    id_propriedade          = request.form.get('id_propriedade', '')
    id_propriedade_interna  = request.form.get('id_propriedade_interna', '')

    # v1.10.0 - trava da fazenda em uso: nada e lido nem gravado.
    if _fora_da_fazenda_em_uso(id_propriedade_interna):
        return redirect('/produtor/gta-manual/iniciar')

    # Etapa 4 (item 8): Procedencia com texto no lugar do numero (dado adulterado) voltava erro 500.
    if (id_parceiro and not id_parceiro.isdecimal()) or (id_propriedade and not id_propriedade.isdecimal()):
        return redirect('/produtor/gta-manual/iniciar')

    uf_gta                  = request.form.get('uf_gta', '').strip().upper()
    serie_gta                = request.form.get('serie_gta', '').strip().upper()
    numero_gta_sequencial    = ''.join(c for c in request.form.get('numero_gta_sequencial', '') if c.isdecimal())
    if numero_gta_sequencial:
        numero_gta_sequencial = numero_gta_sequencial.zfill(6)
    data_emissao_str         = request.form.get('data_emissao', '').strip()
    data_validade_str        = request.form.get('data_validade', '').strip()
    data_entrega_str         = request.form.get('data_entrega', '').strip()
    meio_transporte          = request.form.get('meio_transporte', '').strip().upper()
    qtde_animais_gta_str     = request.form.get('qtde_animais_gta', '').strip()
    confirma_dados           = request.form.get('confirma_dados') == 'on'

    especies = carregar_especies()
    codigos_especie = codigos_validos(especies)

    animais = _ler_animais_do_formulario(especies)
    numero_gta_completo = f'{uf_gta}{serie_gta}{numero_gta_sequencial}'
    soma_animais = sum(a['quantidade'] for a in animais)

    procedencia, destino = _buscar_dados_exibicao(
        id_produtor, id_parceiro, id_propriedade, id_propriedade_interna
    )

    ids = SimpleNamespace(
        id_parceiro=id_parceiro,
        id_propriedade=id_propriedade,
        id_propriedade_interna=id_propriedade_interna,
    )

    gta_tentativa = SimpleNamespace(
        uf_gta=uf_gta,
        serie_gta=serie_gta,
        numero_gta_sequencial=numero_gta_sequencial,
        data_emissao=data_emissao_str,
        data_validade=data_validade_str,
        data_entrega=data_entrega_str,
        meio_transporte=meio_transporte,
        qtde_animais_gta=qtde_animais_gta_str,
        confirma_dados=confirma_dados,
    )

    def _reexibir(mensagem_erro):
        return render_template(
            'produtor/gta_manual_cadastro.html',
            erro=mensagem_erro,
            procedencia=procedencia,
            destino=destino,
            gta=gta_tentativa,
            animais=animais,
            ids=ids,
            faixas_idade=FAIXAS_IDADE,
            especies=especies,
            sexos=SEXOS_VALIDOS,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='entrada',
        )

    if not (id_parceiro and id_propriedade and id_propriedade_interna):
        return _reexibir('Dados de Procedência/Destino incompletos. Reinicie o fluxo pelo link de Preenchimento Manual.')

    if not uf_gta or len(uf_gta) != 2:
        return _reexibir('UF da GTA é obrigatória!')
    if not serie_gta or len(serie_gta) != tamanho_serie_gta(uf_gta) or not serie_gta.isalpha():
        return _reexibir(mensagem_serie_gta(uf_gta))
    if not numero_gta_sequencial or len(numero_gta_sequencial) != 6:
        return _reexibir('Número da GTA é obrigatório e deve ter 6 dígitos!')

    # ---------------------------------------------------
    # v1.7.0 - GTA DUPLICADA: se ja existe uma GTA identica (UF + Serie
    # + Numero + sentido) neste Produtor, avisa e IMPEDE a entrada.
    # Conferida logo aqui, antes dos demais campos, para o usuario ver
    # o problema primeiro. A mensagem e montada com a sessao aberta.
    # ---------------------------------------------------
    with get_db_produtor(id_produtor) as db:
        gta_existente = buscar_gta_duplicada(db, uf_gta, serie_gta, numero_gta_sequencial, SENTIDO_FIXO)
        mensagem_duplicada = mensagem_gta_duplicada(gta_existente) if gta_existente else None
    if mensagem_duplicada:
        return _reexibir(mensagem_duplicada)

    if not meio_transporte or meio_transporte not in MEIOS_TRANSPORTE_VALIDOS:
        return _reexibir('Selecione o Meio de Transporte!')

    try:
        qtde_animais_gta = int(qtde_animais_gta_str)
        if qtde_animais_gta <= 0:
            raise ValueError()
    except ValueError:
        return _reexibir('Quantidade de Animais na GTA é obrigatória e deve ser maior que zero!')

    data_emissao = data_validade = data_entrega = None

    if not data_emissao_str:
        return _reexibir('Data de Emissão é obrigatória!')
    try:
        data_emissao = datetime.strptime(data_emissao_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data de Emissão incorreta! Use o formato dd/mm/aaaa.')

    if not data_validade_str:
        return _reexibir('Data de Validade é obrigatória!')
    try:
        data_validade = datetime.strptime(data_validade_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data de Validade incorreta! Use o formato dd/mm/aaaa.')

    if data_validade < data_emissao:
        return _reexibir('Data de Validade não pode ser anterior à Data de Emissão!')

    if not data_entrega_str:
        return _reexibir('Data de Entrega é obrigatória!')
    try:
        data_entrega = datetime.strptime(data_entrega_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data de Entrega incorreta! Use o formato dd/mm/aaaa.')

    # v1.6.1 - Entrega e o dia em que os animais chegaram: nunca futura.
    if data_entrega > date.today():
        return _reexibir(
            f'Data de Entrega não pode ser uma data futura (hoje é {date.today().strftime("%d/%m/%Y")})! '
            f'Confira o dia, o mês e o ano digitados.'
        )

    eh_comitiva = (meio_transporte == MEIO_TRANSPORTE_COMITIVA)
    limite_superior = data_validade + timedelta(days=TOLERANCIA_COMITIVA_DIAS) if eh_comitiva else data_validade

    if data_entrega < data_emissao:
        return _reexibir('Data de Entrega não pode ser anterior à Data de Emissão!')
    if data_entrega > limite_superior:
        if eh_comitiva:
            return _reexibir(
                f'Data de Entrega além do limite de tolerância para Comitiva '
                f'(até 30 dias após a Validade, {limite_superior.strftime("%d/%m/%Y")})!'
            )
        return _reexibir(
            f'Data de Entrega deve estar entre a Emissão ({data_emissao.strftime("%d/%m/%Y")}) '
            f'e a Validade ({data_validade.strftime("%d/%m/%Y")})!'
        )

    if not animais:
        return _reexibir('Informe ao menos uma categoria de Animais!')

    for animal in animais:
        if animal['especie'] not in codigos_especie:
            return _reexibir('Selecione a Espécie em todas as categorias de Animais.')
        if animal['sexo'] not in SEXOS_VALIDOS:
            return _reexibir('Selecione o Sexo em todas as categorias de Animais.')
        if animal['idade_meses'] not in FAIXAS_IDADE:
            return _reexibir('Selecione a Idade em todas as categorias de Animais.')
        if animal['quantidade'] <= 0:
            return _reexibir('Quantidade deve ser maior que zero em todas as categorias de Animais.')

    if soma_animais != qtde_animais_gta:
        if soma_animais < qtde_animais_gta:
            return _reexibir(f'Falta incluir {qtde_animais_gta - soma_animais} animal(is) para bater com a Quantidade declarada ({qtde_animais_gta}).')
        return _reexibir(f'A soma das categorias ({soma_animais}) excede a Quantidade declarada na GTA ({qtde_animais_gta}). Confira os valores.')

    if not confirma_dados:
        return _reexibir('Confirme que os dados foram conferidos antes de salvar!')

    # ---------------------------------------------------
    # Tudo validado - grava de verdade.
    # ---------------------------------------------------
    with get_db_produtor(id_produtor) as db:
        # Etapa 4 (item 8): a Procedencia precisa existir e ser deste Parceiro (antes: id inexistente = erro 500).
        procedencia_db = db.get(ParceiroPropriedades, int(id_propriedade))
        if procedencia_db is None or str(procedencia_db.id_parceiro) != str(int(id_parceiro)):
            return _reexibir('Procedência incorreta. Reinicie o fluxo pelo link de Preenchimento Manual.')
        try:
            gta = Gta(
                id_propriedade=int(id_propriedade_interna),
                uf_gta=uf_gta,
                serie_gta=serie_gta,
                numero_gta_sequencial=numero_gta_sequencial,
                numero_gta_completo=numero_gta_completo,
                qtde_animais=qtde_animais_gta,
                tipo_movimento=TIPO_MOVIMENTO_FIXO,
                sentido=SENTIDO_FIXO,
                data_emissao=data_emissao,
                data_validade=data_validade,
                data_entrega=data_entrega,
                meio_transporte=meio_transporte,
                id_parceiro_propriedade=int(id_propriedade),
                status_brincagem=STATUS_BRINCAGEM_INICIAL,   # v1.6.1
            )
            db.add(gta)
            db.flush()  # garante gta.id antes de criar as linhas de Animais

            for animal in animais:
                db.add(GtaAnimal(
                    id_gta=gta.id,
                    especie=animal['especie'],
                    sexo=animal['sexo'],
                    idade_meses=animal['idade_meses'],
                    quantidade=animal['quantidade'],
                ))

            # v1.13.0 - trilha: quem lancou a GTA e quando (sem Desfazer)
            id_operacao_log = registrar_operacao(
                db, id_usuario=session['usuario_id'], id_propriedade=int(id_propriedade_interna), modulo='gta_manual',
                descricao=f'GTA de Entrada {numero_gta_completo} lançada — {qtde_animais_gta} animal(is)'[:255])
            registrar_item(db, id_operacao_log, 'tb_4001_gta', gta.id, 'INSERT', None,
                           {'numero_gta_completo': numero_gta_completo, 'qtde_animais': qtde_animais_gta})

            # v1.5.1 - id guardado ANTES do commit (depois dele nao se le
            # mais nada dos objetos do banco - regra da Sessao 078).
            id_gta_gravada = gta.id

            db.commit()
        except IntegrityError as erro_banco:
            # v1.7.0 - outra pessoa/aba gravou a MESMA GTA no mesmo
            # instante: a trava do banco recusou a segunda. Nada foi
            # gravado (rollback) e o usuario recebe a mesma mensagem.
            db.rollback()
            if not eh_violacao_unicidade_gta(erro_banco):
                raise
            gta_existente = buscar_gta_duplicada(db, uf_gta, serie_gta, numero_gta_sequencial, SENTIDO_FIXO)
            if gta_existente:
                return _reexibir(mensagem_gta_duplicada(gta_existente))
            return _reexibir(
                'Esta GTA acabou de ser cadastrada por outra pessoa. '
                'Não é permitido cadastrar a mesma GTA duas vezes.'
            )

    return redirect(f'/produtor/gta-manual/sucesso/{id_gta_gravada}')


# -------------------------------------------------------
# Rota: GET /produtor/gta-manual/sucesso/<id> — confirmacao
# simples apos a gravacao. Tela minima por ora - pode evoluir
# para exibir os dados gravados/reimprimir, se fizer sentido no
# futuro.
# -------------------------------------------------------
# -------------------------------------------------------
# v1.15.0 - GET /produtor/gta-manual/gta-checar (JSON) - GTA duplicada avisada NA HORA (UF + Serie + Numero, sentido ENTRADA, neste Produtor).
# So leitura. Sem os 3 campos completos devolve mensagem vazia.
# -------------------------------------------------------
@gta_manual.route('/produtor/gta-manual/gta-checar')
def gta_checar():
    if 'id_produtor' not in session or 'usuario_id' not in session:
        return jsonify({'mensagem': ''})
    uf = (request.args.get('uf') or '').strip().upper()
    serie = (request.args.get('serie') or '').strip().upper()
    numero = (request.args.get('numero') or '').strip()
    if not uf or not serie or len(numero) != 6:
        return jsonify({'mensagem': ''})
    with get_db_produtor(session['id_produtor']) as db:
        existente = buscar_gta_duplicada(db, uf, serie, numero, SENTIDO_FIXO)
        mensagem = mensagem_gta_duplicada(existente) if existente else ''   # monta com a sessao aberta
    return jsonify({'mensagem': mensagem})


@gta_manual.route('/produtor/gta-manual/sucesso/<int:id_gta>')
def sucesso(id_gta):
    if 'id_produtor' not in session:
        return redirecionar_home()

    # v1.9.0 - destino do botao "Lancar Outra GTA Manual" (e do Voltar):
    # Cadastro do Parceiro, com Propriedade e CPF/CNPJ ja preenchidos.
    url_proxima = '/produtor/gta-manual/iniciar'

    with get_db_produtor(session['id_produtor']) as db:
        gta = db.get(Gta, id_gta)

        if gta and gta.id_propriedade and _fora_da_fazenda_em_uso(gta.id_propriedade):   # Etapa 4 (item 9)
            return redirect('/produtor/gta-manual/iniciar')

        if gta and gta.id_propriedade:
            url_proxima = f'/produtor/gta-manual/nova?id_propriedade_interna={gta.id_propriedade}'   # s118
            if gta.id_parceiro_propriedade:
                propriedade_externa = db.get(ParceiroPropriedades, gta.id_parceiro_propriedade)
                parceiro = db.get(Parceiro, propriedade_externa.id_parceiro) if propriedade_externa else None
                if parceiro and parceiro.cpf_cnpj:
                    url_proxima += f'&documento={parceiro.cpf_cnpj}'

    return render_template(
        'produtor/gta_manual_sucesso.html',
        gta=gta,
        url_proxima=url_proxima,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='entrada',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\gta_manual.py
# =========================================================
