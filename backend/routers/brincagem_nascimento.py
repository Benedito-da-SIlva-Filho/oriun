# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\brincagem_nascimento.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-28 20:55 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 2.10.0
# v2.10.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (7 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v2.9.0: Sessao 123 (2026-11-13 19:40 -03) - AUDITORIA ETAPA 4 (2a passada, decisao de Benedito 'C'): Nascimento = Data de Brincagem menos N meses de CALENDARIO; faixa de idade e Cota Hilton mantidas; PIA grava os meses digitados. REVERSAO: .bak_antes_etapa4c.
#
# DESCRICAO:
#     Brincagem de Nascimento/Desmame no ESCRITORIO (sequencial).
#     Desenho fechado com Benedito na Sessao 081, espelhando a tela
#     "Entrada de Animais" do GERAS com Negociacao = NASCTO/DESMAME.
#
#     NAVEGACAO (Regra de Ouro #7) - DOIS caminhos (v1.1.0):
#       (a) Hub de Entrada -> Brincagem Sequencial -> Lista ->
#           botao "Nascimento / Desmame" (origem 'lista');
#       (b) Hub de Entrada -> card Nascimento / Desmame -> sub-hub ->
#           card "Brincagem Sequencial" (mesma arte, decisao de
#           Benedito - o usuario reconhece a finalidade) -> rota
#           iniciar (Padrao Reutilizavel No1, origem 'hub').
#     O botao Voltar respeita o caminho real (Regra de Ouro #9):
#     quem veio do sub-hub volta para o sub-hub (ou para a selecao
#     de Produtor, se houver mais de um); quem veio da Lista volta
#     para a Lista. A origem fica na sessao (nascimento_origem). Arquivo proprio para NAO mexer no
#     brincagem_sequencial.py ja validado; so reaproveita (importa)
#     2 funcoes dele: _parse_data_br e _decrementar_saldo_lotes
#     (baixa saldo E qtde_saida juntos, regra da Sessao 080).
#
#     ROTAS (prefixo /produtor/brincagem-sequencial/nascimento):
#       - GET  /iniciar  -> Padrao No1: selecao de PAR Propriedade |
#                           Produtor (1 par segue direto) - v1.2.0.
#       - GET  ''        -> formulario (campos "grudentos": o
#                           ultimo valor fica ate o usuario trocar).
#       - GET  /previa   -> JSON: saldo, 1o brinco, faixas de
#                           SISBOV, qtde de series (so leitura).
#       - POST /incluir  -> grava tudo numa transacao unica e
#                           gera a Notificacao (NAS + 7 digitos).
#
#     REGRAS DE NEGOCIO (Benedito, Sessao 081):
#       - Sem GTA. Cada "Incluir" gera UMA Notificacao, gravada na
#         propria tb_4001_gta: serie 'NAS', numero_gta_sequencial
#         de 7 digitos, numero_gta_completo 'NAS0000015' (10
#         posicoes, o mesmo espaco da GTA), tipo_movimento
#         'NASCTO-DESMAME', sentido 'ENTRADA', emissao = validade
#         = entrega = Data da Brincagem, meio_transporte 'NAO SE
#         APLICA', sem Parceiro e sem Frigorifico, e
#         status_brincagem 'BRINCADO' ja na criacao (nunca aparece
#         em lista de pendentes). Sem Comunicado de Entrada
#         (comunicado_entrada.py v1.4.0 e gta_consulta.py v1.12.0
#         ignoram NASCTO-DESMAME).
#       - Numeracao POR PRODUTOR (cada schema tem a sua): maior
#         numero NAS do schema + 1, com trava de 2 partes
#         (NAMESPACE + id_produtor) - a forma de 2 partes do
#         Postgres nunca colide com as travas de 1 parte da PIA e
#         do Comunicado.
#       - Nascimento = Data da Brincagem - Nro Meses x 30 dias
#         (regras_sisbov.DIAS_POR_MES - decisao da Sessao 081),
#         editavel pelo usuario.
#       - Cota Hilton pela regra central regras_sisbov.
#         eh_cota_hilton(eras_dias) - ate 306 dias. Acima disso NAO
#         bloqueia: grava CTH=False e a tela avisa antes.
#       - Brincos escolhidos NA HORA DE GRAVAR (nao ha GTA para
#         amarrar reserva), com trava por Propriedade. Disponivel =
#         saida_data, saida_gta, saida_origem e numero_comunicado
#         vazios + sem reserva ativa de GTA de Compra + NAO lido no
#         brete aguardando Vincular (tb_5001 sts=False). Ordem:
#         lote mais antigo primeiro, SISBOV crescente (mesma da
#         Sequencial). SISBOV com 2 copias disponiveis = duplicado
#         no estoque (bloqueia - avise a Consiste).
#       - Cadeia gravada: tb_4001_gta + tb_4001_gta_animais (1
#         linha, especie = CODIGO do catalogo ("BOV") e faixa pela descricao
#         da tb_4006 - mesmo formato das GTAs de Compra), tb_7017
#         (ENTRADA, saida_gta = NAS), tb_3008 (origem NASCTO-
#         DESMAME), tb_2001, tb_2017 (origem e destino = a propria
#         fazenda/Produtor), tb_7002 (motivo NASCIMENTO, numero_pia
#         = numero da Notificacao) e tb_3007 (saldo e qtde_saida).
#       - Log de Operacoes, igual a Sequencial. v1.1.0: entra no
#         DESFAZER (decisao de Benedito) - SO A ULTIMA Notificacao
#         do Produtor pode ser desfeita (log_operacoes.py v1.3.0),
#         para nao deixar buraco na numeracao oficial. Por isso a
#         Notificacao E a linha de animais dela (tb_4001_gta_animais)
#         vao no Log, na ordem certa.
#       - TRAVA DE PERMISSAO: a Propriedade tem que ser de um par
#         do usuario logado E do Produtor da sessao.
#
#     v1.0.0: Criacao do modulo (Sessao 081).
#     v1.1.0: Sessao 082 (29/09/2026, 17:05 -03) - Pacote 2:
#         - NOVA rota iniciar() (Padrao Reutilizavel No1) para o
#           card do sub-hub de Nascimento; com 1 Produtor so, segue
#           direto ao formulario; com mais de um, mostra a selecao
#           (titulo "Brincagem de Nascimento — Selecionar
#           Propriedade", voltar = sub-hub).
#         - Voltar pelo caminho real: origem gravada na sessao
#           (lista ou hub) - NOVA funcao _url_voltar().
#         - DESFAZER: a linha da tb_4001_gta_animais passa a ser
#           registrada no Log (antes so a Notificacao ia - o Desfazer
#           tentaria apagar a Notificacao com a linha de animais
#           ainda apontando para ela e o banco recusaria).
#         - ESPECIE gravada como CODIGO ("BOV") em
#           tb_4001_gta_animais (regra de Benedito: banco com codigo,
#           tela com a palavra - antes gravava a descricao em
#           maiusculas).
#         - Faixa verde: a sessao guarda no maximo 8 faixas de SISBOV
#           (MAX_FAIXAS_SESSAO) e o total omitido - o cookie da
#           sessao do Flask tem cerca de 4 KB e um lote com muitos
#           brincos salteados poderia estourar e derrubar o login.
#         - Endurecimento sem mudanca de regra: a exclusao dos brincos
#           lidos no brete usa select() explicito dentro do in_().
#     v1.2.0: Sessao 082 (29/09/2026, 17:35 -03) - PROPRIEDADE FIXA
#         (Benedito: "precisamos selecionar a Propriedade E o
#         Produtor - regra conhecida nossa; so nao ha selecao quando
#         existe um par so"). O v1.1.0 copiou da Brincagem Sequencial
#         o agrupamento por Produtor e deixou a Propriedade num
#         dropdown do formulario (que ainda vinha "lembrada" pelo
#         navegador) - a tela nem mostrava o Produtor. Corrigido:
#           - iniciar(): selecao por PAR Propriedade | Produtor (1 par
#             segue direto; 2 ou mais mostram a tela de selecao),
#             igual ao Gerar Comunicado e a GTA Manual. Aceita
#             ?origem=lista (botao da Lista) para o Voltar.
#           - formulario(): a Propriedade escolhida e CONFERIDA (trava
#             de permissao), guardada na sessao (nascimento_propriedade)
#             e a URL recarrega limpa. O dropdown SAIU - a tela mostra
#             Propriedade e Produtor fixos, so leitura, e um campo
#             oculto com o id.
#           - incluir(): a Propriedade vem da SESSAO e e reconferida;
#             o campo oculto so serve para detectar outra aba/janela
#             (se difere da sessao, recusa com aviso).
#           - NOVAS _propriedade_permitida() (agora exige par do
#             usuario E Produtor da sessao e devolve tambem o nome do
#             Produtor), _propriedade_atual(), _url_origem(); o
#             _url_voltar() agora volta do formulario para a selecao
#             quando ha mais de um par. _propriedades_permitidas()
#             (lista) REMOVIDA.
#         Nenhuma mudanca de regra de gravacao.
#     v2.0.0: Sessao 083 (30/09/2026, 13:48 -03) - PACOTE 3D: TELA
#         EM LINHAS (modelo da GTA Manual, pedido de Benedito). Um
#         Gravar = UMA Notificacao com VARIAS linhas de animais.
#         Regras fechadas com Benedito na Sessao 083:
#           - CABECALHO (vale para todos): Propriedade (fixa), Especie,
#             Data da Brincagem e QUANTIDADE TOTAL de nascimentos.
#           - CADA LINHA: Sexo, Nro Meses (o usuario digita o que
#             quiser), Raca, Lote e Quantidade. Nascimento, Faixa de
#             idade e CTH/Livre sao CALCULADOS (Data - Meses x 30) e
#             so aparecem na tela - o usuario nao edita (antes o
#             Nascimento era editavel).
#           - Contador "Falta incluir N": a soma das linhas tem de
#             bater com o total (conferido de novo aqui).
#           - Linhas repetidas (mesmo Sexo e Faixa) sao aceitas: a
#             tb_4001_gta_animais SOMA por Especie + Sexo + Faixa; os
#             animais continuam gravados um a um.
#           - Brincos em sequencia, na ORDEM DAS LINHAS (a 1a linha
#             pega os primeiros).
#           - Confirmacao com RESUMO na tela (janela
#             modal_confirmacao.html) - o campo confirmo_nascimento
#             continua sendo exigido aqui.
#           - Sempre abre NAS novo (nao junta com o Controle do brete).
#         Mudancas:
#           - _valores_do_form(): cabecalho + lista 'linhas' (campos
#             em lista do formulario: sexo[], nro_meses[], raca[],
#             lote[], quantidade[]).
#           - _contexto(): envia tambem as faixas de idade (tb_4006)
#             para a tela calcular Faixa e CTH de cada linha.
#           - previa(): devolve tambem o primeiro e o ultimo SISBOV que
#             serao usados (resumo da confirmacao).
#           - incluir(): validacao por linha, cadeia por linha (mesma
#             gravacao da v1.2.0, tabela por tabela), tb_4001_gta_
#             animais agrupada, resposta com CTH e Livres.
#           - Campos "grudentos": so Especie e Data da Brincagem (as
#             linhas e o total recomecam a cada Notificacao).
#           - NOVA constante MAX_LINHAS (50 linhas por Gravar).
#         Nenhuma mudanca em iniciar(), formulario(), travas, numero
#         NAS, escolha e ordem dos brincos, Log e Desfazer.
#     v2.0.2: Sessao 084 (01/10/2026, 18:30 -03) - o animal gravado em
#         tb_2001 passa a nascer com conferido_brete=False: o brete
#         (Brincagem com Leitor, Tipo Nascimento) enxerga o lancamento
#         do escritorio e confere cada brinco. Unica mudanca.
#     v2.1.0: Sessao 084 (02/10/2026, 12:10 -03) - LANCAMENTO DO ESCRITORIO
#         ENTRA NO NAS JA EXISTENTE (decisao de Benedito: se o brete ja
#         leu, o escritorio nao abre um 2o NAS na mesma data). Substitui a
#         regra da v2.0.0 "sempre abre NAS novo". Regras fechadas:
#           - Existe NAS BRINCADO da mesma Propriedade + Data de Brincagem,
#             com animais e AINDA NAO impresso (mesma busca do brete:
#             buscar_notificacao_para_integracao): o lancamento entra nele
#             - mesma cadeia por animal; tb_4001_gta_animais soma na
#             categoria (ou cria); a qtde da Notificacao e o
#             gta_entrada_animais da tb_2017 passam ao total novo; usa o
#             numero e a PIA dele.
#           - NAS PENDENTE com leituras do brete (Gerar Notificacao ainda
#             nao feito): BLOQUEIA com aviso para gerar a Notificacao do
#             brete primeiro. Nada e gravado.
#           - NAS PENDENTE ZERADO (0 leituras), NAS ja IMPRESSO ou nenhum
#             NAS na data: abre NAS novo, como antes.
#           - Log/Desfazer: o lancamento que entra em NAS existente
#             registra UPDATE (nao INSERT) da Notificacao, da linha de
#             animais e das linhas antigas da tb_2017, para o Desfazer
#             restaurar so o que ele mexeu (log_operacoes.py v1.7.0).
#         Nenhuma mudanca em iniciar(), formulario(), previa(),
#         validacoes, escolha/ordem dos brincos e travas.
#     v2.2.0: Sessao 084 (02/10/2026, 19:20 -03) - DUAS DECISOES DE BENEDITO:
#         (a) DATA DA BRINCAGEM COM MAIS DE 30 DIAS E BLOQUEADA (a data
#             digitada errada passava e a Notificacao nascia vencida):
#             incluir() recusa com a mensagem unica de regras_sisbov.py
#             v1.3.0 (data_brincagem_vencida). A tela recebe o prazo em
#             'prazo_envio_dias' e avisa na hora de digitar.
#         (b) ESPECIE E DATA NAO FICAM MAIS "LEMBRADAS" (a v2.0.0 mantinha
#             as duas para lancamentos seguidos, o que repetia o erro de
#             digitacao): ao ENTRAR ou VOLTAR para a tela - inclusive depois
#             do Gravar - vem tudo em branco, e a Especie volta para
#             "-- Selecione --". Com erro de validacao os campos digitados
#             continuam na tela (so nao viajam entre telas).
#         Nenhuma outra mudanca.
#     v2.3.0: Sessao 089 (07/10/2026, 17:00 -03) - MODULO PILOTO DA FAZENDA EM
#         USO (escolhida no Home novo, faixa em todas as telas). Tres pontos:
#           - iniciar(): com fazenda em uso valida (auth.
#             resolver_fazenda_em_uso), PULA a tela "Selecionar Propriedade"
#             e abre o formulario direto nela. Sem fazenda em uso, ou com
#             uma fazenda so, tudo igual a antes.
#           - _url_voltar(): com fazenda em uso a selecao nao existe mais, por
#             isso o Voltar do formulario vai para a ORIGEM (Lista ou
#             sub-hub), nunca para o iniciar() (que reabriria o formulario:
#             laco). Sem fazenda em uso, igual a antes (Regra de Ouro #9).
#           - _propriedade_atual() (a trava do modulo): se a fazenda em uso for
#             DIFERENTE da Propriedade fixa do formulario (ex.: trocada em
#             outra aba), devolve None - formulario() e incluir() mandam para o
#             iniciar(), que abre o formulario na fazenda em uso. Nada e
#             gravado numa fazenda enquanto a faixa mostra outra.
#         Nenhuma mudanca em previa(), validacoes, gravacao, brincos, Log e
#         Desfazer.
#     v2.4.0: Sessao 092 (09/10/2026, 19:40 -03) - BLOCKCHAIN: cada animal
#         nascido lancado (brincagem de nascimento) gera um evento NASCIMENTO
#         na fila do blockchain (backend/utils/blockchain.py v1.1.0), logo
#         depois da gravacao na tb_2001 e antes do commit. A ficha leva o
#         numero do NAS (documento de controle do nascimento, gravado na
#         tb_4001_gta) onde a compra leva a GTA. O peso do nascimento nao
#         sai aqui - ele chega na conferencia do brete (Leitor/Bastao) e vira
#         o evento PESAGEM (pesagem.py v1.1.0). So age se o Produtor tem
#         provedor ligado; uma falha no blockchain nunca derruba o lancamento.
#         O Desfazer ja existente cancela/estorna os eventos.
#         Nenhuma outra mudanca - previa, validacoes, brincos e Log iguais.
#     v2.5.0: Sessao 094 (12/10/2026, 19:30 -03) - NAS POR PROPRIEDADE (decisao de Benedito):
#         a numeracao da Notificacao de Nascimento (NAS) passa a ser da PROPRIEDADE (dentro do
#         schema do Produtor), nao mais do Produtor inteiro: a primeira NAS de cada fazenda e a
#         NAS0000001. O lancamento do escritorio calcula o proximo numero so entre as NAS da propriedade.
#         REVERSAO: devolver .bak_antes_nas_propriedade.
#     v2.6.0: Sessao 094 (12/10/2026, 20:40 -03) - AUDITORIA DO NASCIMENTO: o manejo do animal vem do estoque ou da regra do modelo (antes: 6 ultimos digitos, errado
#             no 105), via gravacao_nascimento.manejo_do_brinco(). REVERSAO: devolver .bak_antes_auditoria_nasc.
#     v2.7.0: Sessao 101 (20/10/2026, 10:10 -03) - tb_2017 passa a ser copia fiel da tb_2001: a linha de Entrada grava tambem lote, data_brincagem, conferido_brete, conferido_em, id_origem e id_gta_entrada (model tb_2017 v1.2.0). Nenhuma outra mudanca. REVERSAO: devolver .bak_antes_2017_copia_s101.
#     v2.8.0: Sessao 104 (23/10/2026, 08:50 -03) - CAIXA DE SUCESSO (Padrao No7): depois do Gravar o usuario ve a tela de conclusao
#             (Notificacao, animais, Cota Hilton/Livres, faixas de SISBOV, aviso de series) em vez da faixa verde no formulario. O resumo continua montado
#             ANTES do commit e guardado na sessao; nova rota GET .../nascimento/concluida o mostra uma vez so (F5 nao regrava).
#             O formulario deixa de receber 'sucesso'. Nenhuma mudanca na gravacao. Precisa do caixa_sucesso.py 1.1.0 e do brincagem_nascimento_formulario.html 2.4.0.
#             REVERSAO: .bak_antes_s104 (router e formulario).
# =========================================================

import re
from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, redirect, request, session, jsonify
from sqlalchemy import text, func, or_, select
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, Produtor
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4001_gta_animais import GtaAnimal
from backend.models.tb_4002_especie import Especie
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.models.tb_3007_brincos_entrada import BrincoEntrada
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.models.tb_3008_brincos_saida import BrincoSaida
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_5001_brincagem import Brincagem
from backend.models.tb_7002_pia import Pia
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.brincagem_sequencial import _parse_data_br, _decrementar_saldo_lotes
from backend.utils.multitenant import get_db_produtor
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.caixa_sucesso import render_caixa_sucesso   # v2.8.0 - Padrao No7
from backend.utils.blockchain import registrar_evento_animal, TIPO_NASCIMENTO   # v2.4.0 - blockchain
from backend.utils.gravacao_nascimento import (
    buscar_controle_aberto, contar_leituras_do_controle, buscar_notificacao_para_integracao,
    manejo_do_brinco,   # v2.6.0
)
from backend.utils.regras_sisbov import (
    eh_cota_hilton, DIAS_POR_MES, DIAS_MAX_COTA_HILTON, data_nascimento_por_meses,
    PRAZO_ENVIO_NOTIFICACAO_DIAS, MENSAGEM_DATA_BRINCAGEM_VENCIDA, data_brincagem_vencida,
)


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
brincagem_nascimento = Blueprint('brincagem_nascimento', __name__)


# -------------------------------------------------------
# Constantes do modulo
# -------------------------------------------------------
URL_FORMULARIO = '/produtor/brincagem-sequencial/nascimento'
URL_LISTA      = '/produtor/brincagem-sequencial/lista'

TIPO_NASCIMENTO        = 'NASCTO-DESMAME'
SERIE_NOTIFICACAO      = 'NAS'
DIGITOS_NOTIFICACAO    = 7            # NAS + 7 = 10 posicoes (espaco da GTA)
MEIO_TRANSPORTE        = 'NAO SE APLICA'
MOTIVO_PIA             = 'NASCIMENTO'
DIAS_LIBERACAO_ABATE   = 90           # mesma regra da Sequencial/Vincular
NRO_MESES_MAXIMO       = 99           # mesmo limite do Vincular (2 digitos)
QTDE_MAXIMA            = 1000         # teto de seguranca por Incluir
TAMANHO_LOTE           = 30           # tb_2001.lote = String(30)
TAMANHO_MANEJO         = 6
SEXOS_VALIDOS          = ('MACHO', 'FEMEA')

# Travas de 2 partes (namespace, id) - nunca colidem com as
# travas de 1 parte ja usadas pela PIA e pelo Comunicado.
TRAVA_NUMERO_NAS       = 81001        # + id_produtor
TRAVA_BRINCOS_NASC     = 81002        # + id_propriedade

CHAVE_VALORES_SESSAO   = 'nascimento_valores'    # campos "grudentos"
CHAVE_SUCESSO_SESSAO   = 'nascimento_sucesso'    # resumo da Caixa de Sucesso (1 vez)
URL_CONCLUIDA          = URL_FORMULARIO + '/concluida'   # v2.8.0 - Caixa de Sucesso
CHAVE_ORIGEM_SESSAO    = 'nascimento_origem'     # 'lista' ou 'hub' (v1.1.0)
CHAVE_PROPRIEDADE_SESSAO = 'nascimento_propriedade'  # Propriedade FIXA (v1.2.0)

# v1.1.0 - caminhos e limites
URL_INICIAR            = URL_FORMULARIO + '/iniciar'
URL_SUBHUB             = '/produtor/hub/entrada-nascimento'
TITULO_SELECAO         = 'Brincagem de Nascimento — Selecionar Propriedade'
MAX_FAIXAS_SESSAO      = 8            # cookie da sessao ~4 KB (ver changelog)
MAX_LINHAS             = 50           # v2.0.0 - linhas por Gravar (seguranca)


# -------------------------------------------------------
# Funcao auxiliar (v1.2.0): a Propriedade e permitida? Ela precisa
# ser de um par Propriedade/Produtor do usuario logado E do Produtor
# que esta na sessao (gravado pela tela de selecao). Devolve um dict
# com os dados para a tela (nome, municipio/UF, UF e nome do
# Produtor) ou None. E a TRAVA DE PERMISSAO deste modulo - conferida
# na tela, na previa e no Incluir.
# -------------------------------------------------------
def _propriedade_permitida(id_propriedade):
    if not str(id_propriedade).isdecimal() or 'id_produtor' not in session:
        return None

    id_propriedade = int(id_propriedade)
    id_produtor    = int(session['id_produtor'])

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if not any(
        int(par.id_propriedade) == id_propriedade and int(par.id_produtor) == id_produtor
        for par in pares
    ):
        return None

    with Session(engine) as db:
        propriedade = db.get(Propriedade, id_propriedade)
        produtor    = db.get(Produtor, id_produtor)
        if not propriedade:
            return None
        return {
            'id':            propriedade.id,
            'nome':          propriedade.nome,
            'municipio_uf':  f'{propriedade.municipio} / {propriedade.uf}',
            'uf':            propriedade.uf,
            'produtor_nome': produtor.nome if produtor else '-',
        }


# -------------------------------------------------------
# Funcao auxiliar (v1.2.0): a Propriedade FIXA da sessao (gravada
# quando o usuario a escolhe na selecao), reconferida a cada uso.
# None = nao ha escolha valida - o chamador manda para o iniciar().
# -------------------------------------------------------
def _propriedade_atual():
    propriedade = _propriedade_permitida(session.get(CHAVE_PROPRIEDADE_SESSAO))
    if not propriedade:
        return None

    # v2.3.0 - FAZENDA EM USO: se ha uma e ela e DIFERENTE da fixa do
    # formulario (trocada em outra aba, por exemplo), nao ha escolha valida:
    # o chamador manda para o iniciar(), que abre a fazenda em uso.
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and int(par_em_uso.id_propriedade) != int(propriedade['id']):
        return None

    return propriedade


# -------------------------------------------------------
# Funcao auxiliar (v1.2.0): ponto de ORIGEM do caminho - a Lista da
# Brincagem Sequencial (botao "Nascimento / Desmame") ou o sub-hub
# de Nascimento (card do Hub).
# -------------------------------------------------------
def _url_origem():
    return URL_LISTA if session.get(CHAVE_ORIGEM_SESSAO) == 'lista' else URL_SUBHUB


# -------------------------------------------------------
# Funcao (v1.2.0, substitui a de mesmo nome da v1.1.0): destino do
# botao Voltar pelo CAMINHO REAL (Regra de Ouro #9). Do formulario,
# volta para a SELECAO quando o usuario tem mais de um par
# Propriedade/Produtor (mesma logica dos demais modulos); com um
# par so, nao houve selecao e volta direto para a origem.
# -------------------------------------------------------
def _url_voltar():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    # v2.3.0 - com fazenda em uso a selecao e pulada: o Voltar vai para a
    # origem (voltar ao iniciar() reabriria o formulario - laco).
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return f'{URL_INICIAR}?origem={session.get(CHAVE_ORIGEM_SESSAO) or "hub"}'
    return _url_origem()


# -------------------------------------------------------
# Funcao auxiliar: brincos disponiveis para o Nascimento, na
# ordem de consumo (lote mais antigo, SISBOV crescente).
# limite=None traz todos (usado so para contar).
# -------------------------------------------------------
def _consulta_brincos_disponiveis(db, id_propriedade):
    # v1.1.0 - select() explicito (forma oficial para usar dentro do in_()).
    sisbovs_pendentes_brete = select(Brincagem.sisbov).where(
        Brincagem.id_propriedade == int(id_propriedade),
        Brincagem.sts == False,  # noqa: E712
    )
    return (
        db.query(EntradaBrincoRfid)
        .join(BrincoEntrada, EntradaBrincoRfid.id_lote_entrada == BrincoEntrada.id)
        .filter(
            EntradaBrincoRfid.id_propriedade == int(id_propriedade),
            BrincoEntrada.saldo > 0,
            EntradaBrincoRfid.saida_data.is_(None),
            EntradaBrincoRfid.saida_gta.is_(None),
            EntradaBrincoRfid.saida_origem.is_(None),
            EntradaBrincoRfid.numero_comunicado.is_(None),
            or_(
                EntradaBrincoRfid.reservado_id_gta.is_(None),
                EntradaBrincoRfid.reservado_ate.is_(None),
                EntradaBrincoRfid.reservado_ate < datetime.now(),
            ),
            ~EntradaBrincoRfid.sisbov.in_(sisbovs_pendentes_brete),
        )
        .order_by(BrincoEntrada.data_entrada.asc(), BrincoEntrada.id.asc(), EntradaBrincoRfid.sisbov.asc())
    )


def _saldo_propriedade(db, id_propriedade):
    total = (
        db.query(func.coalesce(func.sum(BrincoEntrada.saldo), 0))
        .filter(BrincoEntrada.id_propriedade == int(id_propriedade), BrincoEntrada.saldo > 0)
        .scalar()
    )
    return int(total or 0)


# -------------------------------------------------------
# Funcao auxiliar: faixas legiveis de SISBOV (consecutivos
# viram "X a Y") + quantidade de series (9 primeiros digitos).
# -------------------------------------------------------
def _faixas_e_series(sisbovs):
    if not sisbovs:
        return [], 0

    faixas = []
    inicio = anterior = sisbovs[0]
    for atual in sisbovs[1:]:
        if int(atual) == int(anterior) + 1:
            anterior = atual
            continue
        faixas.append(inicio if inicio == anterior else f'{inicio} a {anterior}')
        inicio = anterior = atual
    faixas.append(inicio if inicio == anterior else f'{inicio} a {anterior}')

    series = {s[:9] for s in sisbovs}
    return faixas, len(series)


# -------------------------------------------------------
# Funcao auxiliar: monta o contexto da tela (formulario).
# -------------------------------------------------------
def _contexto(valores, erro=None):
    propriedade = _propriedade_atual()   # v1.2.0 - Propriedade fixa da sessao

    with get_db_produtor(session['id_produtor']) as db:
        especies = [
            {'id': e.id, 'codigo': e.codigo, 'descricao': e.descricao}
            for e in db.query(Especie).order_by(Especie.id.asc()).all()
        ]
        racas = [
            {'codigo': r.codigo, 'nome': r.nome}
            for r in db.query(Raca).filter_by(comum=True, ativo=True).order_by(Raca.nome.asc()).all()
        ]
        # v2.0.0 - faixas oficiais (tb_4006) para a tela mostrar a
        # Faixa de cada linha
        faixas_idade = [
            {'descricao': f.descricao, 'dias_min': f.dias_min, 'dias_max': f.dias_max}
            for f in db.query(IdadeMeses).order_by(IdadeMeses.dias_min.asc()).all()
        ]

    return {
        'propriedade':           propriedade,
        'especies':              especies,
        'racas':                 racas,
        'faixas_idade':          faixas_idade,   # v2.0.0
        'sexos':                 SEXOS_VALIDOS,
        'valores':               valores,
        'erro':                  erro,
        'dias_por_mes':          DIAS_POR_MES,
        'dias_max_cota_hilton':  DIAS_MAX_COTA_HILTON,
        'qtde_maxima':           QTDE_MAXIMA,
        'prazo_envio_dias':      PRAZO_ENVIO_NOTIFICACAO_DIAS,   # v2.2.0
        'tamanho_lote':          TAMANHO_LOTE,
        'max_linhas':            MAX_LINHAS,     # v2.0.0
        'nro_meses_maximo':      NRO_MESES_MAXIMO,   # v2.0.0
        'url_voltar':            _url_voltar(),   # v1.1.0 - caminho real
        'usuario_nome':          session.get('usuario_nome'),
        'usuario_perfil':        session.get('usuario_perfil'),
        'cor_primaria':          session.get('cor_primaria', '#D4370A'),
        'nome_sistema':          session.get('nome_sistema', 'Orion SISBOV'),
        'menu_ativo':            'entrada',
    }


# -------------------------------------------------------
# Funcao auxiliar (v2.0.0): le o formulario - cabecalho + a lista
# de linhas (campos em lista: sexo[], nro_meses[], raca[], lote[],
# quantidade[], todos na mesma ordem da tela).
# -------------------------------------------------------
def _valores_do_form(form):
    sexos      = form.getlist('sexo[]')
    meses      = form.getlist('nro_meses[]')
    racas      = form.getlist('raca[]')
    lotes      = form.getlist('lote[]')
    quantidades = form.getlist('quantidade[]')

    linhas = []
    for i in range(len(sexos)):
        linhas.append({
            'sexo':       (sexos[i] or '').strip().upper(),
            'nro_meses':  (meses[i] if i < len(meses) else '').strip(),
            'raca':       (racas[i] if i < len(racas) else '').strip(),
            'lote':       (lotes[i] if i < len(lotes) else '').strip().upper(),
            'quantidade': (quantidades[i] if i < len(quantidades) else '').strip(),
        })

    return {
        'id_propriedade':   (form.get('id_propriedade') or '').strip(),
        'id_especie':       (form.get('id_especie') or '').strip(),
        'data_brincagem':   (form.get('data_brincagem') or '').strip(),
        'quantidade_total': (form.get('quantidade_total') or '').strip(),
        'linhas':           linhas,
    }


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-sequencial/nascimento/iniciar -
# ponto de partida (Padrao Reutilizavel No1) do card do sub-hub e
# do botao da Lista. v1.2.0: PROPRIEDADE FIXA - a selecao e por PAR
# Propriedade | Produtor, como no Gerar Comunicado e na GTA Manual:
#   - nenhum par: mensagem de erro;
#   - 1 par so: nao ha o que escolher - grava o Produtor e a
#     Propriedade na sessao e abre o formulario direto;
#   - 2 ou mais pares: tela de selecao (Propriedade | Produtor); a
#     escolha grava o Produtor (auth.selecionar-vinculo) e abre o
#     formulario com a Propriedade escolhida.
# ?origem=lista (botao da Lista) ou nada/hub (card) define para
# onde o Voltar leva.
# v2.3.0: com FAZENDA EM USO (Home novo) a selecao e pulada.
# -------------------------------------------------------
@brincagem_nascimento.route(URL_INICIAR)
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    origem = request.args.get('origem')
    session[CHAVE_ORIGEM_SESSAO] = origem if origem in ('lista', 'hub') else 'hub'
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    contexto_selecao = dict(
        titulo=TITULO_SELECAO,
        proximo=URL_FORMULARIO,
        campo_propriedade='id_propriedade',
        voltar=_url_origem(),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            **contexto_selecao,
        )

    # v2.3.0 - FAZENDA EM USO: ja escolhida no Home novo (conferida contra os
    # pares do usuario) - pula a tela de selecao e abre o formulario direto.
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{URL_FORMULARIO}?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_FORMULARIO}?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        **contexto_selecao,
    )


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-sequencial/nascimento - formulario.
# v1.2.0: recebe ?id_propriedade=X da selecao, CONFERE a Propriedade
# (trava de permissao), guarda na sessao e recarrega a URL limpa.
# Sem escolha valida na sessao, volta para o iniciar().
# -------------------------------------------------------
@brincagem_nascimento.route(URL_FORMULARIO)
def formulario():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade_arg = request.args.get('id_propriedade', '').strip()
    if id_propriedade_arg:
        if not _propriedade_permitida(id_propriedade_arg):
            return redirect(URL_INICIAR)
        session[CHAVE_PROPRIEDADE_SESSAO] = int(id_propriedade_arg)
        return redirect(URL_FORMULARIO)

    if not _propriedade_atual():
        return redirect(URL_INICIAR)

    # v2.2.0 - Especie e Data NAO ficam lembradas: entrou ou voltou = em branco.
    session.pop(CHAVE_VALORES_SESSAO, None)
    valores = {}

    return render_template('produtor/brincagem_nascimento_formulario.html', **_contexto(valores))


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-sequencial/nascimento/previa -
# JSON so leitura: saldo, 1o brinco, faixas e series para a
# quantidade pedida. Os brincos definitivos sao escolhidos de novo
# no Incluir (o estoque pode mudar entre a previa e o clique).
# -------------------------------------------------------
@brincagem_nascimento.route(URL_FORMULARIO + '/previa')
def previa():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    id_propriedade = request.args.get('id_propriedade', '')
    qtde_str       = request.args.get('quantidade', '')

    if not _propriedade_permitida(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403

    qtde = int(qtde_str) if qtde_str.isdecimal() else 0
    qtde = min(qtde, QTDE_MAXIMA)

    with get_db_produtor(session['id_produtor']) as db:
        saldo = _saldo_propriedade(db, id_propriedade)
        consulta = _consulta_brincos_disponiveis(db, id_propriedade)
        primeiro = consulta.first()
        primeiro_brinco = primeiro.sisbov if primeiro else None

        sisbovs = []
        if qtde > 0:
            sisbovs = [b.sisbov for b in consulta.limit(qtde).all()]

    faixas, qtde_series = _faixas_e_series(sisbovs)

    return jsonify({
        'saldo':            saldo,
        'primeiro_brinco':  primeiro_brinco,
        'suficiente':       qtde > 0 and len(sisbovs) == qtde,
        'disponiveis':      len(sisbovs),
        'faixas':           faixas,
        'qtde_series':      qtde_series,
        # v2.0.0 - para o resumo da confirmacao
        'primeiro_escolhido': sisbovs[0] if sisbovs else None,
        'ultimo_escolhido':   sisbovs[-1] if sisbovs else None,
    })


# -------------------------------------------------------
# Rota: POST /produtor/brincagem-sequencial/nascimento/incluir -
# grava a Notificacao e a cadeia inteira, numa transacao unica.
# v2.0.0: VARIAS LINHAS por Notificacao. Blocos:
#   1. Validacoes do cabecalho e de cada linha (nada gravado ainda).
#   2. Catalogos + calculo de cada linha (Nascimento, idade, Faixa,
#      CTH) no servidor, nunca confiando na tela.
#   3. Travas + escolha definitiva dos brincos (total de uma vez).
#   4. Numero NAS + tb_4001_gta + tb_4001_gta_animais (agrupada por
#      Especie + Sexo + Faixa). v2.1.0: se ja existe NAS BRINCADO nao
#      impresso na Propriedade + Data, o lancamento ENTRA nele (sem
#      numero novo); NAS PENDENTE com leituras do brete bloqueia.
#   5. Log de Operacoes (Notificacao E linhas de animais).
#   6. Cadeia por animal, linha por linha, na ordem das linhas:
#      7017, 3008, 2001, 2017, 7002 (mesma gravacao da v1.2.0).
#   7. tb_3007 (saldo e qtde_saida).
#   8. Valores da resposta lidos ANTES do commit; commit.
# -------------------------------------------------------
@brincagem_nascimento.route(URL_FORMULARIO + '/incluir', methods=['POST'])
def incluir():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    valores  = _valores_do_form(request.form)
    confirmo = request.form.get('confirmo_nascimento') == 'on'

    def _reexibir(mensagem):
        return render_template(
            'produtor/brincagem_nascimento_formulario.html',
            **_contexto(valores, erro=mensagem),
        )

    # ---------------------------------------------------
    # 1. Validacoes - cabecalho
    # ---------------------------------------------------
    # Propriedade FIXA (v1.2.0): vem da SESSAO e e reconferida; o campo
    # oculto so detecta outra aba/janela que trocou a escolha.
    propriedade = _propriedade_atual()
    if not propriedade:
        return redirect(URL_INICIAR)
    if str(propriedade['id']) != valores['id_propriedade']:
        return _reexibir(
            'A Propriedade escolhida mudou em outra aba ou janela. '
            'Confira a Propriedade no topo da tela e lance de novo.'
        )

    if not valores['id_especie'].isdecimal():
        return _reexibir('Selecione a Espécie.')

    data_brincagem = _parse_data_br(valores['data_brincagem'])
    if not data_brincagem:
        return _reexibir('Data da Brincagem é obrigatória e deve estar no formato dd/mm/aaaa.')
    if data_brincagem > date.today():
        return _reexibir('Data da Brincagem não pode ser uma data futura.')
    # v2.2.0 - mais de 30 dias: prazo de envio da Notificacao ja vencido.
    if data_brincagem_vencida(data_brincagem):
        return _reexibir(MENSAGEM_DATA_BRINCAGEM_VENCIDA)

    if not valores['quantidade_total'].isdecimal() or int(valores['quantidade_total']) <= 0:
        return _reexibir('Informe a Quantidade Total de Nascimentos.')
    quantidade_total = int(valores['quantidade_total'])
    if quantidade_total > QTDE_MAXIMA:
        return _reexibir(f'Quantidade acima do limite de {QTDE_MAXIMA} animais por Notificação. Divida em lançamentos menores.')

    linhas = valores['linhas']
    if not linhas:
        return _reexibir('Inclua pelo menos uma linha de animais.')
    if len(linhas) > MAX_LINHAS:
        return _reexibir(f'No máximo {MAX_LINHAS} linhas por Notificação.')

    # ---------------------------------------------------
    # 1b. Validacoes - cada linha (a mensagem diz o numero da linha)
    # ---------------------------------------------------
    soma_linhas = 0
    for numero_linha, linha in enumerate(linhas, start=1):
        prefixo = f'Linha {numero_linha}: '
        if linha['sexo'] not in SEXOS_VALIDOS:
            return _reexibir(prefixo + 'selecione o Sexo.')
        if not linha['nro_meses'].isdecimal():
            return _reexibir(prefixo + 'Nro Meses é obrigatório.')
        if int(linha['nro_meses']) > NRO_MESES_MAXIMO:
            return _reexibir(prefixo + f'Nro Meses incorreto (máximo {NRO_MESES_MAXIMO}).')
        if not linha['raca']:
            return _reexibir(prefixo + 'selecione a Raça.')
        if len(linha['lote']) > TAMANHO_LOTE:
            return _reexibir(prefixo + f'Lote pode ter no máximo {TAMANHO_LOTE} caracteres.')
        if not linha['quantidade'].isdecimal() or int(linha['quantidade']) <= 0:
            return _reexibir(prefixo + 'a Quantidade deve ser maior que zero.')
        soma_linhas += int(linha['quantidade'])

    if soma_linhas != quantidade_total:
        return _reexibir(
            f'A soma das linhas ({soma_linhas}) não bate com a Quantidade Total ({quantidade_total}).'
        )

    if not confirmo:
        return _reexibir('É necessário confirmar a Brincagem de Nascimento no resumo antes de gravar.')

    id_propriedade  = int(propriedade['id'])
    id_produtor     = int(session['id_produtor'])
    liberacao_abate = data_brincagem + timedelta(days=DIAS_LIBERACAO_ABATE)

    with get_db_produtor(id_produtor) as db:

        # ---------------------------------------------------
        # 2. Catalogos + calculo de cada linha (no servidor)
        # ---------------------------------------------------
        especie = db.get(Especie, int(valores['id_especie']))
        if not especie:
            return _reexibir('Espécie não encontrada no catálogo.')

        racas_por_codigo = {
            r.codigo: r for r in db.query(Raca).filter_by(comum=True, ativo=True).all()
        }
        faixas = db.query(IdadeMeses).all()

        linhas_calc = []   # uma entrada por linha, na ordem da tela
        for numero_linha, linha in enumerate(linhas, start=1):
            raca_obj = racas_por_codigo.get(linha['raca'])
            if not raca_obj:
                return _reexibir(f'Linha {numero_linha}: Raça não encontrada no catálogo.')

            nro_meses  = int(linha['nro_meses'])
            nascimento = data_nascimento_por_meses(data_brincagem, nro_meses)   # meses de CALENDARIO (decisao C)
            eras_dias  = (data_brincagem - nascimento).days                       # idade REAL (Cota Hilton)
            dias_faixa = nro_meses * DIAS_POR_MES                                 # faixa pela conta antiga (tb_4006)
            faixa_idade = next(
                (f for f in faixas if f.dias_min <= dias_faixa <= f.dias_max), None
            )
            if not faixa_idade:
                return _reexibir(
                    f'Linha {numero_linha}: {nro_meses} meses não se encaixa em nenhuma faixa de idade.'
                )

            linhas_calc.append({
                'sexo':        linha['sexo'],
                'raca':        raca_obj,
                'lote':        linha['lote'] or None,
                'quantidade':  int(linha['quantidade']),
                'nascimento':  nascimento,
                'nro_meses':   nro_meses,
                'eras_dias':   eras_dias,
                'faixa':       faixa_idade.descricao,
                'cota_hilton': eh_cota_hilton(eras_dias),
            })

        # ---------------------------------------------------
        # 3. Travas + brincos definitivos (o total de uma vez; depois
        #    repartidos na ordem das linhas)
        # ---------------------------------------------------
        db.execute(text('SELECT pg_advisory_xact_lock(:ns, :id)'),
                   {'ns': TRAVA_BRINCOS_NASC, 'id': id_propriedade})

        brincos = _consulta_brincos_disponiveis(db, id_propriedade).limit(quantidade_total).all()
        if len(brincos) < quantidade_total:
            db.rollback()
            return _reexibir(
                f'Estoque insuficiente: esta Propriedade tem {len(brincos)} brinco(s) disponível(is) '
                f'e o lançamento pede {quantidade_total}. Nada foi gravado.'
            )

        sisbovs_escolhidos = [b.sisbov for b in brincos]
        if len(set(sisbovs_escolhidos)) != len(sisbovs_escolhidos):
            db.rollback()
            return _reexibir('Há SISBOV duplicado no estoque desta Propriedade. Nada foi gravado — avise a Consiste.')

        copias = (
            _consulta_brincos_disponiveis(db, id_propriedade)
            .filter(EntradaBrincoRfid.sisbov.in_(sisbovs_escolhidos))
            .count()
        )
        if copias != len(sisbovs_escolhidos):
            db.rollback()
            return _reexibir('Há SISBOV duplicado no estoque desta Propriedade. Nada foi gravado — avise a Consiste.')

        # ---------------------------------------------------
        # 4. Numero NAS + Notificacao (tb_4001_gta)
        # ---------------------------------------------------
        db.execute(text('SELECT pg_advisory_xact_lock(:ns, :id)'),
                   {'ns': TRAVA_NUMERO_NAS, 'id': id_produtor})

        # v2.1.0 - 4a. NAS PENDENTE com leituras do brete: o brete leu e
        # a Notificacao ainda nao foi gerada - bloqueia (nada gravado).
        # PENDENTE ZERADO (0 leituras) nao bloqueia: abre NAS novo.
        controle_pendente = buscar_controle_aberto(db, id_propriedade, data_brincagem)
        if controle_pendente and contar_leituras_do_controle(db, controle_pendente) > 0:
            numero_pendente = controle_pendente.numero_gta_completo
            db.rollback()
            return _reexibir(
                f'Existem animais lidos no brete aguardando a Notificação {numero_pendente} '
                f'(Brincagem de {data_brincagem.strftime("%d/%m/%Y")}). '
                'Gere a Notificação do brete primeiro e lance de novo. Nada foi gravado.'
            )

        # v2.1.0 - 4b. NAS BRINCADO, com animais e AINDA NAO impresso,
        # nesta Propriedade + Data: o lancamento entra nele.
        notificacao_existente = buscar_notificacao_para_integracao(db, id_propriedade, data_brincagem)

        movs_anteriores = []   # (id, gta_entrada_animais antes) - so quando entra em NAS existente

        if notificacao_existente:
            notificacao        = notificacao_existente
            numero_sequencial  = notificacao.numero_gta_sequencial
            numero_notificacao = notificacao.numero_gta_completo
            proximo            = int(numero_sequencial)

            qtde_notificacao_antes = notificacao.qtde_animais
            ja_gravados = db.query(func.count(Entrada.id)).filter(Entrada.id_gta_entrada == notificacao.id).scalar() or 0
            total_notificacao = int(ja_gravados) + quantidade_total

            notificacao.qtde_animais = total_notificacao
            db.flush()

            # animais ja gravados nesta Notificacao passam a mostrar o total novo (tb_2017)
            movs_anteriores = [
                (m.id, m.gta_entrada_animais)
                for m in db.query(Movimentacao.id, Movimentacao.gta_entrada_animais).filter(
                    Movimentacao.gta_entrada == numero_notificacao,
                    Movimentacao.id_propriedade == id_propriedade,
                ).all()
            ]
            (
                db.query(Movimentacao)
                .filter(Movimentacao.gta_entrada == numero_notificacao, Movimentacao.id_propriedade == id_propriedade)
                .update({Movimentacao.gta_entrada_animais: total_notificacao}, synchronize_session=False)
            )
        else:
            maior_atual = (
                db.query(func.max(Gta.numero_gta_sequencial))
                .filter(Gta.id_propriedade == id_propriedade, Gta.tipo_movimento == TIPO_NASCIMENTO, Gta.serie_gta == SERIE_NOTIFICACAO)   # v2.5.0 - fila da PROPRIEDADE
                .scalar()
            )
            proximo = int(maior_atual) + 1 if maior_atual and str(maior_atual).isdecimal() else 1
            numero_sequencial = str(proximo).zfill(DIGITOS_NOTIFICACAO)
            numero_notificacao = f'{SERIE_NOTIFICACAO}{numero_sequencial}'
            total_notificacao = quantidade_total

            notificacao = Gta(
                id_propriedade=id_propriedade,
                uf_gta=propriedade['uf'],
                serie_gta=SERIE_NOTIFICACAO,
                numero_gta_sequencial=numero_sequencial,
                numero_gta_completo=numero_notificacao,
                qtde_animais=quantidade_total,
                tipo_movimento=TIPO_NASCIMENTO,
                sentido='ENTRADA',
                data_emissao=data_brincagem,
                data_validade=data_brincagem,
                data_entrega=data_brincagem,
                meio_transporte=MEIO_TRANSPORTE,
                status_brincagem='BRINCADO',
            )
            db.add(notificacao)
            db.flush()

        # v2.0.0 - tb_4001_gta_animais SOMADA por Especie + Sexo + Faixa
        # (linhas repetidas na tela viram uma linha so aqui), na ordem
        # em que cada categoria aparece pela primeira vez.
        # v2.1.0 - em NAS existente, a categoria que ja existe so SOMA.
        categorias = {}
        for lc in linhas_calc:
            chave = (lc['sexo'], lc['faixa'])
            categorias[chave] = categorias.get(chave, 0) + lc['quantidade']

        linhas_gta_animais = []   # (linha, 'INSERT' ou 'UPDATE', quantidade antes)
        for (sexo, faixa), qtde in categorias.items():
            linha_existente = None
            if notificacao_existente:
                linha_existente = (
                    db.query(GtaAnimal)
                    .filter(
                        GtaAnimal.id_gta == notificacao.id,
                        GtaAnimal.especie == especie.codigo,
                        GtaAnimal.sexo == sexo,
                        GtaAnimal.idade_meses == faixa,
                    )
                    .first()
                )

            if linha_existente:
                qtde_antes_linha = linha_existente.quantidade or 0
                linha_existente.quantidade = qtde_antes_linha + qtde
                db.flush()
                linhas_gta_animais.append((linha_existente, 'UPDATE', qtde_antes_linha))
            else:
                animais_gta = GtaAnimal(
                    id_gta=notificacao.id,
                    especie=especie.codigo,
                    sexo=sexo,
                    idade_meses=faixa,
                    quantidade=qtde,
                )
                db.add(animais_gta)
                db.flush()
                linhas_gta_animais.append((animais_gta, 'INSERT', None))

        produtor = db.get(Produtor, id_produtor)
        cpf_produtor = produtor.cpf_cnpj if produtor else None

        # ---------------------------------------------------
        # 5. Log de Operacoes - Notificacao primeiro, depois as linhas
        #    de animais (o Desfazer percorre de tras para frente e
        #    apaga as linhas ANTES da Notificacao).
        #    v2.1.0 - em NAS existente: UPDATE (nao INSERT) da
        #    Notificacao, das linhas de animais somadas e da tb_2017.
        # ---------------------------------------------------
        if notificacao_existente:
            descricao_log = (
                f'Brincagem de Nascimento — {quantidade_total} animais incluídos na Notificação '
                f'{numero_notificacao} já existente (total {total_notificacao})'
            )
        else:
            descricao_log = f'Brincagem de Nascimento — Notificação {numero_notificacao} ({quantidade_total} animais)'

        id_operacao = registrar_operacao(
            db,
            id_usuario=session.get('usuario_id'),
            id_propriedade=id_propriedade,
            modulo='brincagem_nascimento',
            descricao=descricao_log,
        )

        if notificacao_existente:
            registrar_item(
                db, id_operacao, tabela='tb_4001_gta', id_registro=notificacao.id,
                tipo_mudanca='UPDATE',
                dados_antes={'qtde_animais': qtde_notificacao_antes},
                dados_depois={'qtde_animais': total_notificacao},
            )
        else:
            registrar_item(
                db, id_operacao, tabela='tb_4001_gta', id_registro=notificacao.id,
                tipo_mudanca='INSERT', dados_antes=None,
                dados_depois={'numero_gta_completo': numero_notificacao, 'tipo_movimento': TIPO_NASCIMENTO},
            )

        for animais_gta, tipo_linha, qtde_antes_linha in linhas_gta_animais:
            if tipo_linha == 'UPDATE':
                registrar_item(
                    db, id_operacao, tabela='tb_4001_gta_animais', id_registro=animais_gta.id,
                    tipo_mudanca='UPDATE',
                    dados_antes={'quantidade': qtde_antes_linha},
                    dados_depois={'quantidade': animais_gta.quantidade},
                )
            else:
                registrar_item(
                    db, id_operacao, tabela='tb_4001_gta_animais', id_registro=animais_gta.id,
                    tipo_mudanca='INSERT', dados_antes=None,
                    dados_depois={'id_gta': notificacao.id, 'especie': especie.codigo},
                )

        for id_mov, qtde_mov_antes in movs_anteriores:
            registrar_item(
                db, id_operacao, tabela='tb_2017_movimentacoes', id_registro=id_mov,
                tipo_mudanca='UPDATE',
                dados_antes={'gta_entrada_animais': qtde_mov_antes},
                dados_depois={'gta_entrada_animais': total_notificacao},
            )

        # ---------------------------------------------------
        # 6. Cadeia por animal - linha por linha, os brincos em
        #    sequencia (a 1a linha pega os primeiros).
        # ---------------------------------------------------
        posicao = 0
        qtde_cth = 0
        for lc in linhas_calc:
            brincos_da_linha = brincos[posicao:posicao + lc['quantidade']]
            posicao += lc['quantidade']
            if lc['cota_hilton']:
                qtde_cth += lc['quantidade']

            for brinco in brincos_da_linha:
                manejo = manejo_do_brinco(brinco)   # v2.6.0 - estoque -> regra do modelo

                # ---- 6.1 tb_7017 (UPDATE) ----
                dados_antes_7017 = {
                    'status': brinco.status, 'raca': brinco.raca, 'sexo': brinco.sexo,
                    'data_brincagem': str(brinco.data_brincagem) if brinco.data_brincagem else None,
                    'nascimento': str(brinco.nascimento) if brinco.nascimento else None,
                    'eras_dias': brinco.eras_dias,
                    'saida_data': str(brinco.saida_data) if brinco.saida_data else None,
                    'saida_gta': brinco.saida_gta,
                }
                brinco.status           = 'ENTRADA'
                brinco.raca             = lc['raca'].codigo
                brinco.sexo             = lc['sexo']
                brinco.data_brincagem   = data_brincagem
                brinco.nascimento       = lc['nascimento']
                brinco.eras_dias        = lc['eras_dias']
                brinco.saida_data       = data_brincagem
                brinco.saida_gta        = numero_notificacao
                brinco.reservado_id_gta = None
                brinco.reservado_ate    = None
                db.flush()
                registrar_item(
                    db, id_operacao, tabela='tb_7017_entrada_brincos_rfid',
                    id_registro=brinco.id, tipo_mudanca='UPDATE',
                    dados_antes=dados_antes_7017,
                    dados_depois={'status': 'ENTRADA', 'saida_gta': numero_notificacao},
                )

                # ---- 6.2 tb_3008 (CREATE) ----
                brinco_saida = BrincoSaida(
                    id_propriedade=id_propriedade,
                    id_lote_entrada=brinco.id_lote_entrada,
                    sisbov=brinco.sisbov,
                    rfid=brinco.rfid,
                    data_saida=data_brincagem,
                    gta=numero_notificacao,
                    origem=TIPO_NASCIMENTO,
                )
                db.add(brinco_saida)
                db.flush()
                registrar_item(
                    db, id_operacao, tabela='tb_3008_brincos_saida',
                    id_registro=brinco_saida.id, tipo_mudanca='INSERT',
                    dados_antes=None, dados_depois={'sisbov': brinco.sisbov},
                )

                # ---- 6.3 tb_2001 (CREATE) ----
                entrada = Entrada(
                    sisbov=brinco.sisbov,
                    manejo=manejo,
                    rfid=brinco.rfid,
                    id_especie=especie.id,
                    sexo=lc['sexo'],
                    nascimento=lc['nascimento'],
                    eras_dias=lc['eras_dias'],
                    id_raca=lc['raca'].id,
                    id_aptidao=None,
                    cota_hilton=lc['cota_hilton'],
                    data_brincagem=data_brincagem,
                    liberacao_abate=liberacao_abate,
                    tipo_entrada=TIPO_NASCIMENTO,
                    brincos='INTERNO',
                    conferido_brete=False,   # v2.0.2 - aguarda leitura no brete
                    id_gta_entrada=notificacao.id,
                    data_inclusao=data_brincagem,
                    lote=lc['lote'],
                    id_origem=None,
                    id_propriedade=id_propriedade,
                )
                db.add(entrada)
                db.flush()
                registrar_item(
                    db, id_operacao, tabela='tb_2001', id_registro=entrada.id,
                    tipo_mudanca='INSERT', dados_antes=None, dados_depois={'sisbov': entrada.sisbov},
                )

                # ---- 6.3a BLOCKCHAIN (v2.4.0) - evento NASCIMENTO do animal ----
                registrar_evento_animal(db, entrada, TIPO_NASCIMENTO,
                                        id_usuario=session.get('usuario_id'), id_operacao=id_operacao)

                # ---- 6.4 tb_2017 (CREATE) - origem e destino = a
                # propria fazenda (o bezerro nasceu ali) ----
                movimentacao = Movimentacao(
                    # v2.7.0 (Sessao 101) - copia fiel da tb_2001: campos novos da tb_2017
                    lote=entrada.lote, data_brincagem=entrada.data_brincagem,
                    conferido_brete=entrada.conferido_brete, conferido_em=entrada.conferido_em,
                    id_origem=entrada.id_origem, id_gta_entrada=entrada.id_gta_entrada,
                    id_animal=entrada.id,
                    id_propriedade=id_propriedade,
                    sisbov=brinco.sisbov,
                    manejo=manejo,
                    rfid=brinco.rfid,
                    negociacao=TIPO_NASCIMENTO,
                    brincos='INTERNO',
                    id_especie=especie.id,
                    sexo=lc['sexo'],
                    nascimento=lc['nascimento'],
                    dias=lc['eras_dias'],
                    cota_hilton=lc['cota_hilton'],
                    id_aptidao=None,
                    id_raca=lc['raca'].id,
                    tipo_entrada=TIPO_NASCIMENTO,
                    gta_entrada=numero_notificacao,
                    gta_entrada_emissao=data_brincagem,
                    gta_entrada_validade=data_brincagem,
                    gta_entrada_animais=total_notificacao,   # v2.1.0 - total da Notificacao
                    data_inclusao=data_brincagem,
                    entrada=data_brincagem,
                    origem_propriedade=propriedade['nome'],
                    origem_cpf_cnpj=cpf_produtor,
                    destino_propriedade=propriedade['nome'],
                    destino_cpf_cnpj=cpf_produtor,
                    data_movimentacao=data_brincagem,
                )
                db.add(movimentacao)
                db.flush()
                registrar_item(
                    db, id_operacao, tabela='tb_2017_movimentacoes',
                    id_registro=movimentacao.id, tipo_mudanca='INSERT',
                    dados_antes=None, dados_depois={'sisbov': movimentacao.sisbov},
                )

                # ---- 6.5 tb_7002 PIA (CREATE) - numero da PIA = numero
                # da Notificacao ----
                pia = Pia(
                    id_propriedade=id_propriedade,
                    numero_pia=proximo,
                    id_gta=notificacao.id,
                    sisbov=brinco.sisbov,
                    manejo=manejo,
                    nascimento=lc['nascimento'],
                    idade_meses=lc['nro_meses'],   # o numero digitado (antes round(dias/30))
                    sexo=lc['sexo'],
                    raca_codigo=lc['raca'].codigo,
                    motivo=MOTIVO_PIA,
                    data_identificacao=data_brincagem,
                )
                db.add(pia)
                db.flush()
                registrar_item(
                    db, id_operacao, tabela='tb_7002_pia', id_registro=pia.id,
                    tipo_mudanca='INSERT', dados_antes=None,
                    dados_depois={'numero_pia': proximo, 'sisbov': pia.sisbov},
                )

        # ---------------------------------------------------
        # 7. tb_3007 - saldo E qtde_saida juntos (funcao da
        # Sequencial v1.12.1, ja com Log)
        # ---------------------------------------------------
        _decrementar_saldo_lotes(db, id_operacao, brincos)

        # ---------------------------------------------------
        # 8. Resposta montada ANTES do commit (regra da Sessao 078)
        # ---------------------------------------------------
        faixas_sisbov, qtde_series = _faixas_e_series(sisbovs_escolhidos)
        sucesso = {
            'numero':          numero_notificacao,
            'quantidade':      quantidade_total,
            'propriedade':     propriedade['nome'],
            'faixas':          faixas_sisbov[:MAX_FAIXAS_SESSAO],                 # cookie
            'faixas_omitidas': max(len(faixas_sisbov) - MAX_FAIXAS_SESSAO, 0),
            'qtde_series':     qtde_series,
            'qtde_cth':        qtde_cth,                                         # v2.0.0
            'qtde_livres':     quantidade_total - qtde_cth,                      # v2.0.0
        }

        db.commit()

    # v2.2.0 - Especie e Data NAO ficam mais lembradas (v2.0.0 guardava as duas):
    # a tela volta toda em branco depois do Gravar.
    session.pop(CHAVE_VALORES_SESSAO, None)
    session[CHAVE_SUCESSO_SESSAO] = sucesso

    return redirect(URL_CONCLUIDA)


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-sequencial/nascimento/concluida  (v2.8.0)
# CAIXA DE SUCESSO (Padrao No7) depois do Gravar. Le e apaga o resumo guardado
# na sessao; sem resumo (F5, link antigo), volta para o formulario.
# -------------------------------------------------------
@brincagem_nascimento.route(URL_CONCLUIDA)
def concluida():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    resumo = session.pop(CHAVE_SUCESSO_SESSAO, None)
    if not resumo:
        return redirect(URL_FORMULARIO)

    mudancas = [
        {'campo': 'Notificação',  'antes': None, 'depois': resumo['numero']},
        {'campo': 'Propriedade',  'antes': None, 'depois': resumo['propriedade']},
        {'campo': 'Animais',      'antes': None, 'depois': str(resumo['quantidade'])},
        {'campo': 'Cota Hilton',  'antes': None, 'depois': str(resumo.get('qtde_cth') or 0)},
        {'campo': 'Livres',       'antes': None, 'depois': str(resumo.get('qtde_livres') or 0)},
    ]
    avisos = []
    if resumo.get('qtde_series', 0) > 1:
        avisos.append(f"Foram usadas {resumo['qtde_series']} séries diferentes.")

    notas = []
    if resumo['faixas']:
        texto = 'SISBOV utilizados: ' + ' | '.join(resumo['faixas'])
        if resumo['faixas_omitidas']:
            texto += f" | ... e mais {resumo['faixas_omitidas']} faixa(s) (consulte pelo Relatório de ERAS)"
        notas.append(texto)
    notas.append(f'Cota Hilton: limite de {DIAS_MAX_COTA_HILTON} dias na brincagem.')

    contexto = dict(
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )
    return render_caixa_sucesso(
        contexto, titulo='Notificação gerada com sucesso!', subtitulo=resumo['numero'],
        mudancas=mudancas, avisos=avisos, notas=notas,
        botoes=[{'texto': 'Lançar outra Notificação', 'url': URL_FORMULARIO, 'primario': True},
                {'texto': 'Voltar', 'url': _url_voltar(), 'primario': False}],
        url_voltar=URL_FORMULARIO, titulo_pagina='Orion SISBOV — Notificação gerada',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\brincagem_nascimento.py
# =========================================================
