# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\routers
# MODULO:       backend\routers\brincagem_sequencial.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-09-09 11:45 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO:       1.26.0
# v1.26.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (3 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Modulo "Brincagem Sequencial" do Hub de Entrada (4o card).
#     Alinhamento de negocio fechado nas Sessoes 047/048/049.
#
#     BLOCO C - REGRAS DE NEGOCIO (ver historico completo nos
#     cabecalhos anteriores v1.5.0 a v1.9.0).
#
#     v1.9.0: Sessao 049 (10/09/2026, 16:00 -03) - pacote de
#         correcoes apos teste ao vivo (Saldo tb_3007, Raca em
#         tb_2001, Liberacao de Abate, Lote uppercase, id_
#         propriedade em tb_2001, botao Voltar da Lista).
#     v1.9.1: Sessao 049 (10/09/2026, 17:30 -03) - BUG REAL
#         corrigido: 'racas' convertida para lista de dicts simples
#         ANTES de qualquer commit().
#     v1.10.0: Sessao 049 (10/09/2026, 18:34 -03) - pacote de
#         ajustes: Lista ordenada por Propriedade Destino (nome)
#         ASC + data_entrega ASC; BUG REAL corrigido - Cota Hilton
#         em tb_2001 estava sempre False, agora calculada;
#         tb_2017.destino_propriedade/destino_cpf_cnpj passam a
#         ser preenchidos na Entrada.
#     v1.10.1: Sessao 049 (10/09/2026, 18:45 -03) - CONFIRMADO:
#         tb_2017_movimentacoes ganhou a coluna cota_hilton.
#     v1.11.0: Sessao 050 (12/09/2026, 13:05 -03) - BUG REAL
#         encontrado por Benedito ao planejar o Relatorio por GTA:
#         tb_2001.id_especie e tb_2017.id_especie vinham gravando
#         SEMPRE None desde a Sessao 049. Corrigido: NOVA Validacao
#         5, id_especie resolvido contra o catalogo tb_4002_especie.
#     v1.12.0: Sessao 052 (14/09/2026, 17:10 -03) - BUG REAL
#         encontrado por Benedito ao desenhar o modulo Gerar
#         Comunicado: tb_2001 nunca gravava a propria data_brincagem
#         (coluna nao existia ate esta sessao - ver Tabelas\
#         5_alter_tb_2001_data_brincagem.sql), e liberacao_abate
#         vinha sendo calculada ERRADA a partir de gta.data_entrega
#         em vez de data_brincagem + 90 dias (regra real confirmada
#         por Benedito: "o correto e data de Brincagem + 90 dias,
#         onde estiver diferente tem que corrigir"). Corrigido nos
#         2 pontos: (1) liberacao_abate agora calculada a partir de
#         data_brincagem (mesma variavel ja validada no Bloco C,
#         unica por GTA); (2) Entrada() (tb_2001) passa a receber
#         data_brincagem=data_brincagem explicitamente. Correcao dos
#         animais JA GRAVADOS desde a Sessao 049 (com data_brincagem
#         nula e liberacao_abate errada): ver Tabelas\
#         6_backfill_tb_2001_data_brincagem_liberacao_abate.sql
#         (busca a data real em tb_7017 por SISBOV e recalcula).
#         Nenhuma outra mudanca de logica nesta versao.
#     v1.12.1: Sessao 080 (25/09/2026, 18:00 -03) - 2 BUGS REAIS
#         achados na varredura do vicio "ler depois do commit()" e
#         na conferencia dos saldos da tb_3007:
#           - salvar(): numero_gta_confirmada era lido DEPOIS do
#             db.commit() - o objeto GTA expira e a releitura
#             acontece sem o schema do Produtor, estourando erro
#             APOS gravar (mesmo vicio corrigido no Vincular GTA
#             v1.5.1). Agora e lido ANTES do commit.
#           - _decrementar_saldo_lotes(): baixava o SALDO mas NUNCA
#             somava a QTDE_SAIDA do lote - a conta
#             "entrada - saida - saldo" nao fechava (lote 1 da
#             Campo Grande: diferenca de 45 = os 45 animais da
#             MSA111114; lote 3 da Campo Verde IV: diferenca de
#             50). Agora soma qtde_saida junto (mesma regra do
#             Vincular GTA e do Cancelamento de Brincos). Os lotes
#             ja gravados foram corrigidos por SQL a partir da
#             contagem real da tb_3008 (Sessao 080). O Log de
#             Operacoes registra qtde_saida antes/depois tambem.
#     v1.13.0: Sessao 081 (28/09/2026, 20:05 -03) - REGRA DA COTA
#         HILTON centralizada (decisao de Benedito): a constante
#         local IDADE_MESES_COTA_HILTON (= 10, regra "Nro Meses <
#         10") foi REMOVIDA. O CTH passa a vir de backend\utils\
#         regras_sisbov.py::eh_cota_hilton(eras_dias) - elegivel
#         com idade ATE 306 dias na data da brincagem. Usa o
#         eras_dias que o salvar() ja calculava por categoria (e
#         que respeita o Nascimento editado pelo usuario). A conta
#         de 1 mes = 30 dias NAO mudou (decisao de Benedito,
#         Sessao 081). Nenhuma outra mudanca de logica.
#     v1.14.0: Sessao 082 (29/09/2026, 06:55 -03) - ESPECIE NA
#         TELA pela palavra (regra de Benedito: banco com "BOV",
#         tela com "Bovino"). O Formulario mostrava o texto
#         gravado na GTA; agora _montar_contexto_formulario()
#         traduz o codigo para a descricao do catalogo
#         (backend\utils\especies.py). A Validacao 5 NAO mudou -
#         ja procurava pelo CODIGO, que era o certo; o que travava
#         era a GTA Manual gravar "BOVINO" por extenso (corrigido
#         em gta_manual.py v1.6.0 + SQL de conversao dos dados
#         antigos). Nenhuma outra mudanca.
#     v1.15.0: Sessao 087 (05/10/2026, 13:10 -03) - TRAVAS DA DATA BRINCAGEM
#         E PESO BALANCAO (pedidos de Benedito, testes do Pacote 087).
#         (1) Data Brincagem: o salvar() so conferia se a data existia - uma
#         data futura (ex.: 2029) gravava e estragava Nascimento,
#         Liberacao para Abate e a saida dos brincos. Agora recusa data
#         FUTURA e data alem de 30 dias depois da Data de VALIDADE da GTA
#         (transporte COMITIVA: 60 dias, os 30 mais a mesma tolerancia da
#         GTA Manual). Sem trava para data anterior - o campo e livre.
#         (2) Peso Balancao (campo peso_balancao): ate aqui o Salvar NAO
#         lia esse campo e o valor digitado se perdia. Agora, se vier
#         preenchido (inteiro, ponto de milhar aceito, ex.: 14.410): calcula
#         a MEDIA (peso / total de animais da GTA, arredondada para
#         inteiro) e grava (a) a 1a pesagem (sequencia 1) de CADA animal
#         na tb_4003_pesos, na Data Brincagem, via backend/utils/pesagem.py
#         (origem BALANCAO_COMPRA), (b) na GTA: pesagem_balancao (total),
#         pesagem_data e peso_medio_entrada - a tb_2017 passa a receber a
#         media em peso_medio - tudo na MESMA transacao e no Log de
#         Operacoes (o Desfazer apaga junto). Vazio = nada e gravado.
#         Recusa peso zero e media acima de 1.000 kg por animal.
#         O Selo de Prazo NAO mudou (continua contando da Data de Entrega).
#         brincagem_formulario.html v1.9.0 devolve os campos digitados apos
#         um erro. Nenhuma outra mudanca.
#     v1.16.0: Sessao 087 (05/10/2026, 16:00 -03) - OS ANIMAIS DA SEQUENCIAL
#         NASCEM "A CONFERIR NO BRETE" (processo descrito por Benedito: o
#         escritorio lanca a GTA e relaciona os brincos em sequencia; o peao
#         depois le os brincos no brete - Brincagem com Leitor/Bastao - e a
#         GTA encerra sozinha no ultimo). A tb_2001 nascia com conferido_brete
#         = TRUE (padrao do model), entao o brete nunca enxergaria a GTA. Agora
#         o Entrada(...) grava conferido_brete = FALSE (conferido_em vazio).
#         A conferencia e feita por brincagem_leitor.py v1.14.0 e
#         brincagem_bastao.py v1.10.0 (backend/utils/conferencia_compra.py).
#         GTAs ja lancadas antes desta versao precisam do UPDATE do script
#         Tabelas\alterar_tb_2001_conferido_brete_sequencial_s087.sql.
#         Nenhuma outra mudanca.
#     v1.17.0: Sessao 087 (05/10/2026, 19:00 -03) - O BRETE PREVALECE (acordo com
#         Benedito apos o caso dos brincos 047-052: abrir o formulario da GTA reservou
#         os brincos por 30 min e o Leitor/Bastao passou a barrar o brete - "imagine
#         ficar 30 minutos no Brete esperando"). A Sequencial passa a SE ADAPTAR:
#           (1) _brincos_disponiveis_lote() PULA os brincos ja lidos no brete e ainda
#               pendentes (tb_5001 sts=False) - antes a Sequencial os entregava a outra
#               GTA e o erro so aparecia no Vincular GTA;
#           (2) a SEQUENCIA fica VISIVEL no formulario: total, primeiro e ultimo
#               brinco e, se pulou algum, quais (usados no brete);
#           (3) o Salvar CONFERE DE NOVO os brincos reservados (_garantir_reserva): se
#               o brete levou algum, ou a reserva expirou e os numeros mudariam, a
#               sequencia e RECALCULADA, o formulario volta com os dados digitados e o
#               aviso "O brinco 053 foi usado no brete. Sequencia ajustada: 054 a 058"
#               e NAO grava - o escritorio confere os numeros novos e confirma de novo
#               (o checkbox de confirmacao volta desmarcado). Se nada mudou, grava no
#               1o Salvar, sem clique extra. Antes o Salvar so contava os reservados e
#               NAO conferia se continuavam livres.
#         brincagem_leitor.py v1.15.0 / brincagem_bastao.py v1.11.0: a reserva da
#         Sequencial nunca mais bloqueia o brete. brincagem_formulario.html v1.10.0
#         mostra a sequencia e o aviso. Nenhuma outra mudanca.
#     v1.18.0: Sessao 090 (08/10/2026, 08:10 -03) - FAZENDA EM USO (Lote 3):
#             FAZENDA EM USO (Regra de Ouro #13): a tela "Selecionar Propriedade" deixa
#             de aparecer quando ha fazenda em uso (auth.resolver_fazenda_em_uso).
#               - iniciar(): com fazenda em uso, abre a Lista direto.
#               - lista(): com fazenda em uso mostra SO as GTAs pendentes da
#                 fazenda escolhida (antes: todas as fazendas do Produtor).
#               - VOLTAR (Regra #9): da Lista vai ao Hub de Entrada novo; so
#                 volta para a selecao quem tem 2+ Produtores e nenhuma fazenda
#                 em uso.
#               - TRAVA: formulario() e salvar() recusam GTA de OUTRA fazenda
#                 quando ha fazenda em uso (trocada em outra aba) e mandam para
#                 a Lista. Nada e gravado.
#             Nenhuma mudanca na logica de brincos, peso, reserva e Salvar.
#     v1.19.0: Sessao 092 (09/10/2026, 19:40 -03) - BLOCKCHAIN: cada animal
#             brincado (compra) gera um evento ENTRADA na fila do blockchain
#             (backend/utils/blockchain.py v1.1.0), logo depois da gravacao na
#             tb_2001 e antes do commit - se o Salvar falhar, o evento tambem
#             nao existe. A ficha leva o numero da GTA como origem. A pesagem
#             (Peso Balancao) passa o id_operacao ao registrar_pesagem(), que
#             gera o evento PESAGEM (pesagem.py v1.1.0). So age se o Produtor
#             tem provedor ligado; uma falha no blockchain nunca derruba o
#             Salvar. O Desfazer ja existente cancela/estorna os eventos.
#             Nenhuma outra mudanca - brincos, peso, reserva e gravacao iguais.
#     v1.20.0: Sessao 094 (12/10/2026, 20:15 -03) - AUDITORIA: o agrupamento de faixas
#             (_formatar_faixas_brincos) passa a reconhecer brincos consecutivos do modelo
#             antigo (105) pela BASE de 14 digitos (o DV muda a cada numero e quebrava a faixa
#             em todo brinco). Modelo novo igual a antes. Nenhuma outra mudanca.
#             REVERSAO: devolver .bak_antes_faixas_dv.
#     v1.21.0: Sessao 096 (14/10/2026, 10:05 -03) - NASCIMENTO DEPOIS DA BRINCAGEM: o Salvar recusa a
#             categoria cuja Data de Nascimento (editavel) seja posterior a Data Brincagem
#             (regras_sisbov.py v1.6.0). O formulario recebe dias_max_cota_hilton para o aviso
#             da Cota Hilton. Nenhuma outra mudanca.
#             REVERSAO: devolver .bak_antes_nasc_cth_s096.
#     v1.22.0: Sessao 101 (20/10/2026, 10:10 -03) - tb_2017 passa a ser copia fiel da tb_2001: a linha de Entrada grava tambem lote, data_brincagem, conferido_brete, conferido_em, id_origem e id_gta_entrada (model tb_2017 v1.2.0). Nenhuma outra mudanca. REVERSAO: devolver .bak_antes_2017_copia_s101.
#     v1.23.0: Sessao 102 (21/10/2026, 09:20 -03) - UF DUPLICADA: a Procedencia da ficha usa municipio_sem_uf()
#             (gta_manual.py v1.12.0) antes de somar a UF. Nenhuma outra mudanca. REVERSAO: devolver .bak_antes_uf_s102.
#     v1.24.0: Sessao 104 (23/10/2026, 08:50 -03) - CAIXA DE SUCESSO (Padrao No7): depois do Salvar o usuario ve a tela de conclusao (GTA, animais,
#             Data Brincagem, Raca, Liberacao p/ abate, Peso medio, faixas de SISBOV) em vez do banner verde na Lista. O resumo e montado ANTES do commit,
#             guardado na sessao e mostrado pela nova rota GET /produtor/brincagem-sequencial/concluida (F5 nao regrava). A Lista deixa de ler ?sucesso=.
#             Nenhuma mudanca na gravacao. Precisa do caixa_sucesso.py 1.1.0 e do brincagem_lista.html 1.6.0.  REVERSAO: .bak_antes_s104 (router e lista).
#     v1.25.0: Sessao 106 (26/10/2026, 14:10 -03) - PONTA SOLTA (auditoria): GTA com leitura RESERVADA no brete (Leitor/Bastao, tb_5001.id_gta_reservada)
#             aparece na Lista DESABILITADA com 'Em leitura no brete: N de M', e formulario()/salvar() recusam a GTA - o Sequencial nao brinca por cima
#             de uma leitura em andamento. Nenhuma outra mudanca. REVERSAO: .bak_antes_s106s.
# =========================================================

import re
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import quote

from flask import Blueprint, render_template, redirect, request, session
from sqlalchemy import text, or_, func   # v1.25.0 - func

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
from backend.models.tb_7002_pia import Pia
from backend.models.tb_5001_brincagem import Brincagem   # v1.17.0 - brincos lidos no brete (pendentes)
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.gta_manual import MEIO_TRANSPORTE_COMITIVA, TOLERANCIA_COMITIVA_DIAS, municipio_sem_uf   # v1.23.0
from backend.utils.pesagem import registrar_pesagem
from backend.utils.blockchain import registrar_evento_animal, TIPO_ENTRADA   # v1.19.0 - blockchain
from backend.utils.multitenant import get_db_produtor
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.caixa_sucesso import render_caixa_sucesso   # v1.24.0 - Padrao No7
from backend.utils.regras_sisbov import (
    eh_cota_hilton, modelo_do_sisbov, completar_sisbov_antigo, MODELO_SISBOV_ANTIGO,   # v1.20.0
    TAMANHO_BASE_SISBOV_ANTIGO,
    DIAS_MAX_COTA_HILTON, nascimento_depois_da_brincagem, MENSAGEM_NASCIMENTO_DEPOIS_BRINCAGEM,   # v1.21.0
)
from backend.utils.especies import descricao_da_especie, carregar_especies


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
brincagem_sequencial = Blueprint('brincagem_sequencial', __name__)


# -------------------------------------------------------
# Constantes do modulo.
# v1.13.0: IDADE_MESES_COTA_HILTON removida - a regra da Cota
# Hilton mora em backend\utils\regras_sisbov.py.
# -------------------------------------------------------
PRAZO_DIAS_TOTAL         = 30  # Selo de Prazo - a partir da Data de Entrega da GTA
PRAZO_DIAS_URGENTE       = 7   # corte para virar "urgente" (cor chamativa)
PRAZO_RESERVA_MINUTOS    = 30  # validade da reserva temporaria de brincos
TAMANHO_MAXIMO_GTA_3008  = 10  # limite real de tb_3008.gta (String(10))
DIAS_LIBERACAO_ABATE     = 90  # tb_2001.liberacao_abate = data_brincagem + N dias (v1.12.0)
PRAZO_DIAS_APOS_VALIDADE = 30  # v1.15.0 - limite da Data Brincagem: Validade da GTA + N dias (COMITIVA: + tolerancia)
PESO_MAXIMO_POR_ANIMAL_KG = 1000  # v1.15.0 - media do Peso Balancao nunca passa disso (mesma trava do Leitor)
ORIGEM_PESAGEM_BALANCAO  = 'BALANCAO_COMPRA'  # v1.15.0 - origem gravada na tb_4003_pesos
URL_LISTA                = '/produtor/brincagem-sequencial/lista'       # v1.24.0
URL_CONCLUIDA            = '/produtor/brincagem-sequencial/concluida'   # v1.24.0 - Caixa de Sucesso
CHAVE_SUCESSO_SESSAO     = 'brincagem_seq_sucesso'                      # v1.24.0 - resumo (1 vez)
MAX_FAIXAS_SUCESSO       = 8                                            # v1.24.0 - cookie da sessao ~4 KB


# -------------------------------------------------------
# Funcao auxiliar: calcula o selo de Prazo de uma GTA.
# -------------------------------------------------------
def _calcular_prazo(data_entrega):
    prazo_final     = data_entrega + timedelta(days=PRAZO_DIAS_TOTAL)
    dias_restantes  = (prazo_final - date.today()).days

    if dias_restantes > PRAZO_DIAS_URGENTE:
        return {'classe': 'ok', 'texto': f'{dias_restantes} dias restantes'}

    if dias_restantes >= 1:
        return {
            'classe': 'urgente',
            'texto':  f'⚠ {dias_restantes} dia{"s" if dias_restantes != 1 else ""} restante{"s" if dias_restantes != 1 else ""}',
        }

    dias_vencido = abs(dias_restantes)
    return {
        'classe': 'vencido',
        'texto':  f'✖ Vencido há {dias_vencido} dia{"s" if dias_vencido != 1 else ""}' if dias_vencido > 0 else '✖ Vence hoje',
    }


# -------------------------------------------------------
# Funcao auxiliar - Voltar dinamico da Lista (conta Produtores
# DISTINTOS).
# -------------------------------------------------------
def _url_voltar_pos_selecao():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    produtores_distintos = {par.id_produtor for par in pares}
    # v1.18.0 - com fazenda em uso a selecao e pulada: volta direto ao Hub.
    if len(produtores_distintos) > 1 and resolver_fazenda_em_uso(pares) is None:
        return '/produtor/brincagem-sequencial/iniciar'
    return '/produtor/hub-novo/entrada'


# -------------------------------------------------------
# TRAVA DA FAZENDA EM USO (v1.18.0): True quando ha fazenda em uso e a GTA
# e de OUTRA Propriedade (a fazenda foi trocada em outra aba).
# -------------------------------------------------------
def _gta_fora_da_fazenda_em_uso(gta):
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is None or gta.id_propriedade is None:
        return False
    return int(gta.id_propriedade) != int(par_em_uso.id_propriedade)


# -------------------------------------------------------
# Funcao auxiliar - normaliza texto removendo TODOS os espacos.
# -------------------------------------------------------
def _normalizar(texto):
    return re.sub(r'\s+', '', texto.strip()).lower()


# -------------------------------------------------------
# Funcao auxiliar - parseia data "dd/mm/aaaa" para date().
# -------------------------------------------------------
def _parse_data_br(texto):
    texto = (texto or '').strip()
    m = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', texto)
    if not m:
        return None
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return date(ano, mes, dia)
    except ValueError:
        return None


# -------------------------------------------------------
# v1.15.0 - Trava da Data Brincagem (servidor). Devolve a mensagem de
# erro, ou None se a data esta correta. Regras (Benedito, 05/10/2026):
# nunca futura; no maximo 30 dias depois da Data de VALIDADE da GTA
# (transporte COMITIVA: 30 + a tolerancia da GTA Manual = 60 dias).
# Nao ha trava para data anterior - o campo e de digitacao livre.
# -------------------------------------------------------
def _validar_data_brincagem(data_brincagem, gta):
    hoje = date.today()
    if data_brincagem > hoje:
        return f'Data Brincagem não pode ser futura (hoje é {hoje.strftime("%d/%m/%Y")}).'

    eh_comitiva = (gta.meio_transporte or '').strip().upper() == MEIO_TRANSPORTE_COMITIVA
    prazo_dias  = PRAZO_DIAS_APOS_VALIDADE + (TOLERANCIA_COMITIVA_DIAS if eh_comitiva else 0)
    limite      = gta.data_validade + timedelta(days=prazo_dias)

    if data_brincagem > limite:
        limite_br = limite.strftime('%d/%m/%Y')
        if eh_comitiva:
            return (
                f'Data Brincagem passa do limite de {prazo_dias} dias da Validade da GTA '
                f'(transporte COMITIVA, até {limite_br}).'
            )
        return (
            f'Data Brincagem passa do limite de {PRAZO_DIAS_APOS_VALIDADE} dias da Validade da GTA '
            f'(até {limite_br}). Só GTA com transporte COMITIVA tem prazo maior '
            f'({PRAZO_DIAS_APOS_VALIDADE + TOLERANCIA_COMITIVA_DIAS} dias).'
        )
    return None


# -------------------------------------------------------
# v1.15.0 - Le o Peso Balancao digitado (inteiro, com ou sem ponto de
# milhar: 14410 ou 14.410). Devolve (valor_inteiro_ou_None, erro_ou_None).
# Vazio = (None, None) - o campo nao e obrigatorio.
# -------------------------------------------------------
def _ler_peso_balancao(texto):
    texto = (texto or '').strip()
    if not texto:
        return None, None
    if not re.match(r'^\d{1,3}(\.\d{3})+$|^\d+$', texto):
        return None, 'Peso Balanção incorreto. Digite só números inteiros, sem vírgula (ex.: 14.410).'
    valor = int(texto.replace('.', ''))
    if valor <= 0:
        return None, 'Peso Balanção deve ser maior que zero (ou deixe o campo em branco).'
    return valor, None


# -------------------------------------------------------
# Funcao auxiliar - lotes com saldo > 0 de uma Propriedade.
# -------------------------------------------------------
def _lotes_disponiveis(db, id_propriedade):
    return (
        db.query(BrincoEntrada)
        .filter(
            BrincoEntrada.id_propriedade == id_propriedade,
            BrincoEntrada.saldo > 0,
        )
        .order_by(BrincoEntrada.data_entrada.asc(), BrincoEntrada.id.asc())
        .all()
    )


# -------------------------------------------------------
# Funcao auxiliar - brincos disponiveis (tb_7017) de UM lote,
# considerando reserva.
# -------------------------------------------------------
def _brincos_disponiveis_lote(db, id_propriedade, id_lote, limit=None, id_gta=None, ignorar_lidos_brete=True):
    condicao_reserva = or_(
        EntradaBrincoRfid.reservado_ate.is_(None),
        EntradaBrincoRfid.reservado_ate < datetime.now(),
        EntradaBrincoRfid.reservado_id_gta == id_gta,
    )
    query = (
        db.query(EntradaBrincoRfid)
        .filter(
            EntradaBrincoRfid.id_propriedade == id_propriedade,
            EntradaBrincoRfid.id_lote_entrada == id_lote,
            EntradaBrincoRfid.saida_gta.is_(None),
            EntradaBrincoRfid.saida_origem.is_(None),
            condicao_reserva,
        )
    )
    # v1.17.0 - O BRETE PREVALECE: brinco ja lido no brete e ainda pendente (tb_5001
    # sts=False, aguardando o Vincular GTA) esta na orelha de um animal vivo - a
    # Sequencial nao pode entrega-lo a outra GTA. ignorar_lidos_brete=False so e usado
    # para descobrir quais brincos foram PULADOS (aviso na tela).
    if ignorar_lidos_brete:
        lidos_brete = (
            db.query(Brincagem.sisbov)
            .filter(Brincagem.id_propriedade == id_propriedade, Brincagem.sts == False)   # noqa: E712
            .scalar_subquery()
        )
        query = query.filter(~EntradaBrincoRfid.sisbov.in_(lidos_brete))
    query = query.order_by(EntradaBrincoRfid.sisbov.asc())
    if limit is not None:
        query = query.limit(limit)
    return query.all()


# -------------------------------------------------------
# Funcao auxiliar - simula a distribuicao sequencial de brincos.
# -------------------------------------------------------
def _montar_fila_brincos(db, id_propriedade, lotes, necessario_total, id_gta, ignorar_lidos_brete=True):
    fila     = []
    restante = necessario_total
    for lote in lotes:
        if restante <= 0:
            break
        brincos_lote = _brincos_disponiveis_lote(
            db, id_propriedade, lote.id, limit=restante, id_gta=id_gta,
            ignorar_lidos_brete=ignorar_lidos_brete,
        )
        fila.extend(brincos_lote)
        restante -= len(brincos_lote)
    return fila


def _simular_consumo_brincos(db, id_propriedade, quantidades, id_gta=None):
    lotes            = _lotes_disponiveis(db, id_propriedade)
    lidos_brete      = _lidos_no_brete_livres(db, id_propriedade)   # v1.17.0
    saldo_total      = sum(lote.saldo for lote in lotes) - len(lidos_brete)
    necessario_total = sum(quantidades)

    resultado = {
        'saldo_disponivel':  saldo_total,
        'necessario_total':  necessario_total,
        'suficiente':        saldo_total >= necessario_total,
        'primeiro_brinco':   None,
        'ultimo_brinco':     None,   # v1.17.0
        'pulados':           [],     # v1.17.0 - SISBOVs pulados por ja terem sido lidos no brete
        'categorias':        [],
    }

    if not resultado['suficiente']:
        return resultado

    fila = _montar_fila_brincos(db, id_propriedade, lotes, necessario_total, id_gta)
    if len(fila) < necessario_total:
        resultado['suficiente'] = False
        return resultado

    if fila:
        resultado['primeiro_brinco'] = fila[0].sisbov
        resultado['ultimo_brinco']   = fila[-1].sisbov

    # v1.17.0 - quais brincos a Sequencial PULOU: tudo que a fila pegaria sem a regra do brete,
    # ate o ULTIMO brinco que ela pegou de verdade, e que ficou de fora (os lidos no brete).
    if lidos_brete:
        fila_ingenua = _montar_fila_brincos(
            db, id_propriedade, lotes, necessario_total + len(lidos_brete), id_gta, ignorar_lidos_brete=False
        )
        reais = {brinco.sisbov for brinco in fila}
        posicao_ultimo = max(
            (indice for indice, brinco in enumerate(fila_ingenua) if brinco.sisbov == resultado['ultimo_brinco']),
            default=len(fila_ingenua) - 1,
        )
        resultado['pulados'] = [
            brinco.sisbov for brinco in fila_ingenua[:posicao_ultimo + 1] if brinco.sisbov not in reais
        ]

    ponteiro = 0
    for qtd in quantidades:
        chunk = fila[ponteiro:ponteiro + qtd]
        resultado['categorias'].append(chunk)
        ponteiro += qtd

    return resultado


# -------------------------------------------------------
# Funcao auxiliar - libera reserva anterior desta GTA.
# -------------------------------------------------------
def _liberar_reserva_antiga(db, id_gta):
    db.query(EntradaBrincoRfid).filter_by(reservado_id_gta=id_gta).update(
        {'reservado_id_gta': None, 'reservado_ate': None}
    )
    db.flush()


# -------------------------------------------------------
# Funcao auxiliar - reserva os brincos escolhidos pela simulacao.
# -------------------------------------------------------
def _reservar_brincos(db, id_gta, categorias_brincos):
    ate = datetime.now() + timedelta(minutes=PRAZO_RESERVA_MINUTOS)
    for lista_categoria in categorias_brincos:
        for brinco in lista_categoria:
            brinco.reservado_id_gta = id_gta
            brinco.reservado_ate    = ate
    db.flush()


# -------------------------------------------------------
# Funcao auxiliar - busca os brincos JA RESERVADOS para uma GTA.
# -------------------------------------------------------
def _brincos_reservados_gta(db, id_gta):
    return (
        db.query(EntradaBrincoRfid)
        .join(BrincoEntrada, EntradaBrincoRfid.id_lote_entrada == BrincoEntrada.id)
        .filter(
            EntradaBrincoRfid.reservado_id_gta == id_gta,
            EntradaBrincoRfid.reservado_ate.isnot(None),
            EntradaBrincoRfid.reservado_ate >= datetime.now(),
        )
        .order_by(BrincoEntrada.data_entrada.asc(), BrincoEntrada.id.asc(), EntradaBrincoRfid.sisbov.asc())
        .all()
    )


# -------------------------------------------------------
# v1.17.0 - SISBOVs lidos no brete e ainda PENDENTES (tb_5001 sts=False), e quais
# deles ainda estao no estoque (sem saida) - sao os que a Sequencial nao pode usar.
# -------------------------------------------------------
def _lidos_no_brete_livres(db, id_propriedade):
    lidos = [
        linha[0] for linha in
        db.query(Brincagem.sisbov)
        .filter(Brincagem.id_propriedade == id_propriedade, Brincagem.sts == False)   # noqa: E712
        .all()
    ]
    if not lidos:
        return []
    return [
        linha[0] for linha in
        db.query(EntradaBrincoRfid.sisbov)
        .filter(
            EntradaBrincoRfid.id_propriedade == id_propriedade,
            EntradaBrincoRfid.saida_gta.is_(None),
            EntradaBrincoRfid.saida_origem.is_(None),
            EntradaBrincoRfid.sisbov.in_(lidos),
        )
        .all()
    ]


# -------------------------------------------------------
# v1.17.0 - os brincos que o formulario MOSTROU (e reservou) para a GTA: todas as linhas
# com reservado_id_gta = GTA, venceu a reserva ou nao. Mesma ordem de _brincos_reservados_gta.
# -------------------------------------------------------
def _brincos_vistos_gta(db, id_gta):
    return (
        db.query(EntradaBrincoRfid)
        .join(BrincoEntrada, EntradaBrincoRfid.id_lote_entrada == BrincoEntrada.id)
        .filter(EntradaBrincoRfid.reservado_id_gta == id_gta)
        .order_by(BrincoEntrada.data_entrada.asc(), BrincoEntrada.id.asc(), EntradaBrincoRfid.sisbov.asc())
        .all()
    )


# -------------------------------------------------------
# v1.17.0 - SISBOVs (entre os informados) que ja estao OCUPADOS: no rebanho (tb_2001),
# na PIA (tb_7002) ou lidos no brete e pendentes (tb_5001 sts=False).
# -------------------------------------------------------
def _sisbovs_ocupados(db, sisbovs):
    ocupados = set()
    if not sisbovs:
        return ocupados
    for modelo in (Entrada, Pia):
        ocupados.update(linha[0] for linha in db.query(modelo.sisbov).filter(modelo.sisbov.in_(sisbovs)).all())
    ocupados.update(
        linha[0] for linha in
        db.query(Brincagem.sisbov).filter(Brincagem.sisbov.in_(sisbovs), Brincagem.sts == False).all()   # noqa: E712
    )
    return ocupados


def _brinco_livre(brinco, ocupados):
    return (
        brinco.saida_data is None
        and brinco.saida_gta is None
        and brinco.saida_origem is None
        and brinco.numero_comunicado is None
        and brinco.sisbov not in ocupados
    )


# -------------------------------------------------------
# v1.17.0 - O Salvar CONFERE DE NOVO os brincos reservados. Devolve
# (brincos_reservados, aviso_ajuste, erro):
#   - tudo como o formulario mostrou (mesma quantidade, reservas validas, brincos livres):
#     (brincos, None, None) - grava normalmente;
#   - o brete levou algum brinco, ou a reserva expirou: libera a reserva, SIMULA de novo
#     (pulando os lidos no brete) e reserva a sequencia nova. Se por acaso a sequencia
#     nova for IGUAL a que o usuario viu (so expirou), segue gravando; se MUDOU, devolve
#     o aviso e quem chama NAO grava - o escritorio confere os numeros novos e confirma.
# -------------------------------------------------------
def _garantir_reserva(db, gta, quantidades):
    total  = sum(quantidades)
    vistos = _brincos_vistos_gta(db, gta.id)
    agora  = datetime.now()

    ocupados = _sisbovs_ocupados(db, [brinco.sisbov for brinco in vistos])
    usados   = [brinco.sisbov for brinco in vistos if not _brinco_livre(brinco, ocupados)]
    validos  = [
        brinco for brinco in vistos
        if brinco.sisbov not in usados and brinco.reservado_ate is not None and brinco.reservado_ate >= agora
    ]

    if len(vistos) == total and len(validos) == total:
        return validos, None, None

    sisbovs_vistos = [brinco.sisbov for brinco in vistos]

    _liberar_reserva_antiga(db, gta.id)
    simulacao = _simular_consumo_brincos(db, gta.id_propriedade, quantidades, id_gta=gta.id)
    if not simulacao['suficiente']:
        return [], None, (
            f'Estoque de brincos insuficiente para esta GTA: precisa de {total}, '
            f'só há {simulacao["saldo_disponivel"]} disponíveis. Nenhum dado foi gravado.'
        )

    _reservar_brincos(db, gta.id, simulacao['categorias'])
    novos = _brincos_reservados_gta(db, gta.id)
    sisbovs_novos = [brinco.sisbov for brinco in novos]
    if len(novos) != total:
        return [], None, 'Não foi possível reservar os brincos desta GTA. Tente de novo.'

    if sisbovs_novos == sisbovs_vistos:
        return novos, None, None   # so expirou: os numeros sao os mesmos que o usuario viu

    if usados:
        faixas = ', '.join(faixa['texto'] for faixa in _formatar_faixas_brincos(sorted(usados)))
        plural = len(usados) > 1
        motivo = f"{'Os brincos' if plural else 'O brinco'} {faixas} {'foram usados' if plural else 'foi usado'} no brete. "
    elif not vistos:
        motivo = 'Os brincos desta GTA ainda não estavam reservados. '
    else:
        motivo = 'A reserva dos brincos expirou. '

    novas = ', '.join(faixa['texto'] for faixa in _formatar_faixas_brincos(sisbovs_novos))
    return novos, f'{motivo}Sequência ajustada: {novas}. Confira os números e confirme a Brincagem de novo.', None



# -------------------------------------------------------
# Funcao auxiliar - baixa o lote (tb_3007), uma vez por LOTE.
# v1.12.1: soma a qtde_saida JUNTO com a baixa do saldo (antes so
# o saldo baixava e a conta "entrada - saida - saldo" nao fechava).
# -------------------------------------------------------
def _decrementar_saldo_lotes(db, id_operacao, todos_brincos_consumidos):
    consumo_por_lote = {}
    for brinco in todos_brincos_consumidos:
        consumo_por_lote[brinco.id_lote_entrada] = consumo_por_lote.get(brinco.id_lote_entrada, 0) + 1

    for id_lote, quantidade_consumida in consumo_por_lote.items():
        lote = db.get(BrincoEntrada, id_lote)
        saldo_antes      = lote.saldo
        qtde_saida_antes = lote.qtde_saida or 0
        lote.saldo       = saldo_antes - quantidade_consumida
        lote.qtde_saida  = qtde_saida_antes + quantidade_consumida
        db.flush()

        registrar_item(
            db, id_operacao, tabela='tb_3007_brincos_entrada',
            id_registro=lote.id, tipo_mudanca='UPDATE',
            dados_antes={'saldo': saldo_antes, 'qtde_saida': qtde_saida_antes},
            dados_depois={'saldo': lote.saldo, 'qtde_saida': lote.qtde_saida},
        )


# -------------------------------------------------------
# Funcao auxiliar - agrupa SISBOVs consecutivos em faixas legiveis.
# -------------------------------------------------------
# v1.20.0 - "atual" e o brinco logo depois de "anterior"? Modelo novo: numero + 1.
# Modelo antigo (105): o DV muda a cada numero, entao compara a BASE de 14 digitos
# (base + 1, com o DV recalculado) - antes a faixa quebrava em todo brinco.
def _eh_proximo_brinco(anterior, atual):
    try:
        if (modelo_do_sisbov(anterior) == MODELO_SISBOV_ANTIGO
                and modelo_do_sisbov(atual) == MODELO_SISBOV_ANTIGO):
            base = int(anterior[:TAMANHO_BASE_SISBOV_ANTIGO]) + 1
            esperado = completar_sisbov_antigo(str(base).zfill(TAMANHO_BASE_SISBOV_ANTIGO))
            return esperado == atual
        return int(atual) == int(anterior) + 1
    except ValueError:
        return False


def _formatar_faixas_brincos(sisbovs):
    if not sisbovs:
        return []

    faixas   = []
    inicio   = sisbovs[0]
    anterior = sisbovs[0]

    for atual in sisbovs[1:]:
        if _eh_proximo_brinco(anterior, atual):
            anterior = atual
            continue
        faixas.append((inicio, anterior))
        inicio   = atual
        anterior = atual

    faixas.append((inicio, anterior))

    return [
        {'texto': inicio if inicio == fim else f'{inicio} a {fim}'}
        for inicio, fim in faixas
    ]


# -------------------------------------------------------
# Funcao auxiliar - texto do aviso de prazo no Formulario.
# -------------------------------------------------------
def _texto_aviso_prazo(data_entrega):
    prazo_final    = data_entrega + timedelta(days=PRAZO_DIAS_TOTAL)
    dias_restantes = (prazo_final - date.today()).days
    data_entrega_br = data_entrega.strftime('%d/%m/%Y')

    if dias_restantes >= 0:
        return (
            f'Esta GTA foi entregue em {data_entrega_br} — faltam '
            f'{dias_restantes} dia{"s" if dias_restantes != 1 else ""} '
            f'para o limite de {PRAZO_DIAS_TOTAL} dias pra brincagem.'
        )

    dias_vencido = abs(dias_restantes)
    return (
        f'Esta GTA foi entregue em {data_entrega_br} — o limite de '
        f'{PRAZO_DIAS_TOTAL} dias venceu há {dias_vencido} '
        f'dia{"s" if dias_vencido != 1 else ""}.'
    )


# -------------------------------------------------------
# Funcao auxiliar - monta o contexto completo do template
# brincagem_formulario.html.
# -------------------------------------------------------
def _montar_contexto_formulario(db, gta, dados_repostos=None, erro=None, reservar=False, aviso_sequencia=None):
    categorias_db = (
        db.query(GtaAnimal)
        .filter_by(id_gta=gta.id)
        .order_by(GtaAnimal.id.asc())
        .all()
    )

    idades_db  = db.query(IdadeMeses).all()
    idades_map = {_normalizar(idade.descricao): idade for idade in idades_db}

    # Dicts simples, montados ANTES de qualquer commit() - evita
    # objetos ORM expirando apos commit() e quebrando na hora do
    # Jinja renderizar.
    racas_db = (
        db.query(Raca)
        .filter_by(comum=True, ativo=True)
        .order_by(Raca.nome.asc())
        .all()
    )
    racas = [{'codigo': raca.codigo, 'nome': raca.nome} for raca in racas_db]

    quantidades = [categoria.quantidade for categoria in categorias_db]
    simulacao   = _simular_consumo_brincos(db, gta.id_propriedade, quantidades, id_gta=gta.id)

    if reservar and simulacao['suficiente']:
        _reservar_brincos(db, gta.id, simulacao['categorias'])

    # v1.17.0 - SEQUENCIA VISIVEL: total, primeiro e ultimo brinco e os pulados (lidos no brete).
    todos_brincos = [brinco for brincos_cat in simulacao['categorias'] for brinco in brincos_cat]
    sequencia = None
    if todos_brincos:
        sequencia = {
            'total':   len(todos_brincos),
            'primeiro': todos_brincos[0].sisbov,
            'ultimo':   todos_brincos[-1].sisbov,
            'pulados':  _formatar_faixas_brincos(simulacao['pulados']),
        }

    # v1.14.0 - catalogo carregado 1 vez (tela mostra "Bovino").
    especies_catalogo = carregar_especies()

    categorias = []
    for categoria, brincos_categoria in zip(
        categorias_db, simulacao['categorias'] or [[] for _ in categorias_db]
    ):
        idade = idades_map.get(_normalizar(categoria.idade_meses))
        sisbovs_categoria = [brinco.sisbov for brinco in brincos_categoria]
        categorias.append({
            'especie':          descricao_da_especie(categoria.especie, especies_catalogo),
            'sexo':             categoria.sexo,
            'idade_meses':      categoria.idade_meses,
            'quantidade':       categoria.quantidade,
            'meses_estimado':   round(idade.dias_medio / 30) if idade else None,
            'faixas_brincos':   _formatar_faixas_brincos(sisbovs_categoria),
        })

    cabecalho_documento = {
        'numero_gta_completo': gta.numero_gta_completo,
        'data_emissao_br':     gta.data_emissao.strftime('%d/%m/%Y'),
        'data_validade_br':    gta.data_validade.strftime('%d/%m/%Y'),
        'data_entrega_br':     gta.data_entrega.strftime('%d/%m/%Y'),
        'tipo_movimento':      gta.tipo_movimento,
        'meio_transporte':     gta.meio_transporte,
        'qtde_animais':        gta.qtde_animais,
        'sentido':             gta.sentido,
    }

    parceiro_propriedade = gta.parceiro_propriedade
    parceiro             = parceiro_propriedade.parceiro if parceiro_propriedade else None
    procedencia = {
        'nome':            parceiro.nome if parceiro else '-',
        'cpf_cnpj':        parceiro.cpf_cnpj if parceiro else '-',
        'estabelecimento': parceiro_propriedade.estabelecimento if parceiro_propriedade else '-',
        'regiao':          parceiro_propriedade.regiao if parceiro_propriedade else '-',
        'municipio_uf':    (
            f'{municipio_sem_uf(parceiro_propriedade.municipio_nome, parceiro_propriedade.uf)} / {parceiro_propriedade.uf}'   # v1.23.0
            if parceiro_propriedade and parceiro_propriedade.municipio_nome else '-'
        ),
    }

    propriedade_destino = gta.propriedade
    produtor             = db.get(Produtor, session['id_produtor'])
    destino = {
        'produtor_nome':    produtor.nome if produtor else '-',
        'propriedade_nome': propriedade_destino.nome if propriedade_destino else '-',
        'municipio_uf':     (
            f'{propriedade_destino.municipio} / {propriedade_destino.uf}'
            if propriedade_destino else '-'
        ),
    }

    total_femea = sum(c.quantidade for c in categorias_db if c.sexo == 'FEMEA')
    total_macho = sum(c.quantidade for c in categorias_db if c.sexo == 'MACHO')

    return {
        'gta_id':              gta.id,
        'cabecalho_documento': cabecalho_documento,
        'procedencia':         procedencia,
        'destino':             destino,
        'categorias':          categorias,
        'racas':               racas,
        'saldo_disponivel':    simulacao['saldo_disponivel'],
        'primeiro_brinco':     simulacao['primeiro_brinco'],
        'estoque_suficiente':  simulacao['suficiente'],
        'total_femea':         total_femea,
        'total_macho':         total_macho,
        'total_geral':         total_femea + total_macho,
        'aviso_prazo':         _texto_aviso_prazo(gta.data_entrega) if gta.data_entrega else None,
        'erro':                erro,
        'sequencia':           sequencia,         # v1.17.0
        'aviso_sequencia':     aviso_sequencia,   # v1.17.0
        'dias_max_cota_hilton': DIAS_MAX_COTA_HILTON,   # v1.21.0 - aviso da Cota Hilton na tela
        'dados_repostos':      dados_repostos or {},
        'url_voltar':          '/produtor/brincagem-sequencial/lista',
        'usuario_nome':        session.get('usuario_nome'),
        'usuario_perfil':      session.get('usuario_perfil'),
        'cor_primaria':        session.get('cor_primaria', '#D4370A'),
        'nome_sistema':        session.get('nome_sistema', 'Orion SISBOV'),
        'menu_ativo':          'entrada',
    }


# -------------------------------------------------------
# Funcao auxiliar - numero_pia sequencial POR PROPRIEDADE, com
# trava via pg_advisory_xact_lock.
# -------------------------------------------------------
def _obter_proximo_numero_pia(db, id_propriedade):
    db.execute(text('SELECT pg_advisory_xact_lock(:id_propriedade)'), {'id_propriedade': id_propriedade})

    maximo_atual = (
        db.query(Pia.numero_pia)
        .filter(Pia.id_propriedade == id_propriedade)
        .order_by(Pia.numero_pia.desc())
        .limit(1)
        .scalar()
    )
    return (maximo_atual or 0) + 1


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-sequencial/iniciar
# -------------------------------------------------------
@brincagem_sequencial.route('/produtor/brincagem-sequencial/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            titulo='Selecionar Propriedade — Brincagem Sequencial',
            proximo='/produtor/brincagem-sequencial/lista',
            campo_propriedade='id_propriedade',
            voltar='/produtor/hub-novo/entrada',
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='entrada',
        )

    # v1.18.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect('/produtor/brincagem-sequencial/lista')

    produtores_distintos = {par.id_produtor for par in pares}

    if len(produtores_distintos) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect('/produtor/brincagem-sequencial/lista')

    pares_por_produtor = []
    vistos = set()
    for par in pares:
        if par.id_produtor not in vistos:
            pares_por_produtor.append(par)
            vistos.add(par.id_produtor)

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares_por_produtor,
        erro=None,
        titulo='Selecionar Propriedade — Brincagem Sequencial',
        proximo='/produtor/brincagem-sequencial/lista',
        campo_propriedade='id_propriedade',
        voltar='/produtor/hub-novo/entrada',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-sequencial/lista
# -------------------------------------------------------
@brincagem_sequencial.route('/produtor/brincagem-sequencial/lista')
def lista():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    # v1.18.0 - FAZENDA EM USO: a Lista mostra SO as GTAs da fazenda escolhida
    # (Regra de Ouro #13). Sem fazenda em uso, tudo igual a antes.
    pares_usuario = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares_usuario)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo

    with get_db_produtor(session['id_produtor']) as db:
        consulta_gtas = (
            db.query(Gta)
            .join(Propriedade, Gta.id_propriedade == Propriedade.id)
            .filter(
                Gta.tipo_movimento == 'COMPRA',
                Gta.status_brincagem == 'PENDENTE',
                Gta.data_entrega.isnot(None),
            )
            .order_by(Propriedade.nome.asc(), Gta.data_entrega.asc())
        )
        if par_em_uso is not None:
            consulta_gtas = consulta_gtas.filter(Gta.id_propriedade == int(par_em_uso.id_propriedade))
        gtas_db = consulta_gtas.all()

        produtor = db.get(Produtor, session['id_produtor'])
        produtor_nome = produtor.nome if produtor else '-'

        gtas_lista = []
        for gta in gtas_db:
            parceiro_propriedade = gta.parceiro_propriedade
            propriedade_destino  = gta.propriedade
            lidos_brete = _lidos_reservados_gta(db, gta.id)   # v1.25.0

            gtas_lista.append({
                'numero_gta_completo':      gta.numero_gta_completo,
                'procedencia_fazenda':      parceiro_propriedade.estabelecimento if parceiro_propriedade else '-',
                'procedencia_proprietario': parceiro_propriedade.parceiro.nome if parceiro_propriedade and parceiro_propriedade.parceiro else '-',
                'destino_fazenda':          propriedade_destino.nome if propriedade_destino else '-',
                'destino_proprietario':     produtor_nome,
                'data_entrega_br':          gta.data_entrega.strftime('%d/%m/%Y'),
                'qtde_animais':             gta.qtde_animais,
                'prazo':                    _calcular_prazo(gta.data_entrega),
                'url_brincagem':            None if lidos_brete else f'/produtor/brincagem-sequencial/formulario?id_gta={gta.id}',
                'em_leitura':               f'{lidos_brete} de {gta.qtde_animais}' if lidos_brete else '',   # v1.25.0
            })

        return render_template(
            'produtor/brincagem_lista.html',
            gtas=gtas_lista,
            url_voltar=_url_voltar_pos_selecao(),
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='entrada',
        )


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-sequencial/formulario?id_gta=X
# BLOCO B - RESERVA os brincos mostrados (30 min).
# -------------------------------------------------------
@brincagem_sequencial.route('/produtor/brincagem-sequencial/formulario')
def formulario():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_gta = request.args.get('id_gta', '')
    if not id_gta.isdecimal():
        return 'GTA não informada ou inválida. Reinicie o fluxo pela Lista.', 400

    with get_db_produtor(session['id_produtor']) as db:
        gta = db.get(Gta, int(id_gta))

        if not gta or gta.tipo_movimento != 'COMPRA' or gta.status_brincagem != 'PENDENTE':
            return 'Esta GTA não está pendente de Brincagem (pode já ter sido brincada). Volte à Lista e atualize.', 400

        # v1.18.0 - trava da fazenda em uso: GTA de outra fazenda nao abre nem grava.
        if _gta_fora_da_fazenda_em_uso(gta):
            return redirect('/produtor/brincagem-sequencial/lista')

        # v1.25.0 - GTA em leitura no brete (Leitor/Bastao): nao abre aqui.
        if _lidos_reservados_gta(db, gta.id):
            return redirect('/produtor/brincagem-sequencial/lista')

        _liberar_reserva_antiga(db, gta.id)
        contexto = _montar_contexto_formulario(db, gta, reservar=True)

        db.commit()

        return render_template('produtor/brincagem_formulario.html', **contexto)


# -------------------------------------------------------
# Rota: POST /produtor/brincagem-sequencial/salvar
# BLOCO C - v1.12.0. Gravacao real, 1 transacao unica, 7 lugares +
# Log de Operacoes. liberacao_abate CORRIGIDA (data_brincagem + 90
# dias, nao mais gta.data_entrega - ver changelog v1.12.0 no
# cabecalho). tb_2001 passa a gravar sua PROPRIA data_brincagem.
# v1.12.1: numero da GTA lido ANTES do commit.
# v1.13.0: Cota Hilton pela regra central (eh_cota_hilton).
# -------------------------------------------------------
@brincagem_sequencial.route('/produtor/brincagem-sequencial/salvar', methods=['POST'])
def salvar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_gta = request.form.get('id_gta', '')
    if not id_gta.isdecimal():
        return 'GTA não informada ou inválida. Reinicie o fluxo pela Lista.', 400

    with get_db_produtor(session['id_produtor']) as db:
        gta = db.get(Gta, int(id_gta))

        if not gta or gta.tipo_movimento != 'COMPRA' or gta.status_brincagem != 'PENDENTE':
            return 'Esta GTA não está pendente de Brincagem (pode já ter sido brincada). Volte à Lista e atualize.', 400

        # v1.18.0 - trava da fazenda em uso: GTA de outra fazenda nao abre nem grava.
        if _gta_fora_da_fazenda_em_uso(gta):
            return redirect('/produtor/brincagem-sequencial/lista')

        # v1.25.0 - GTA em leitura no brete (Leitor/Bastao): nao grava aqui.
        if _lidos_reservados_gta(db, gta.id):
            return 'Esta GTA está sendo lida no brete (Leitor/Bastão). Termine a leitura lá ou desfaça-a antes de usar a Brincagem Sequencial.', 400

        erro = None

        # ---------------------------------------------------
        # VALIDACAO 1 - tamanho do numero da GTA.
        # ---------------------------------------------------
        numero_gta_para_3008 = gta.numero_gta_completo
        if len(numero_gta_para_3008) > TAMANHO_MAXIMO_GTA_3008:
            erro = (
                f'Número da GTA "{numero_gta_para_3008}" tem {len(numero_gta_para_3008)} '
                f'caracteres - excede o limite de {TAMANHO_MAXIMO_GTA_3008} do sistema. '
                f'Nenhum dado foi gravado. Avise a Consiste antes de tentar novamente.'
            )

        # ---------------------------------------------------
        # VALIDACAO 2 - campos gerais do POST.
        # ---------------------------------------------------
        codigo_raca        = (request.form.get('raca') or '').strip()
        data_brincagem_str = (request.form.get('data_brincagem_geral') or '').strip()
        confirmo            = request.form.get('confirmo_brincagem') == 'on'

        raca_obj = None
        if not erro:
            if not codigo_raca:
                erro = 'Selecione a Raça antes de salvar.'
            else:
                raca_obj = (
                    db.query(Raca)
                    .filter_by(codigo=codigo_raca, comum=True, ativo=True)
                    .first()
                )
                if not raca_obj:
                    erro = 'Raça selecionada é inválida ou não pertence ao Produtor.'

        data_brincagem = None
        if not erro:
            data_brincagem = _parse_data_br(data_brincagem_str)
            if not data_brincagem:
                erro = 'Data Brincagem é obrigatória e deve estar no formato dd/mm/aaaa.'
            else:
                erro = _validar_data_brincagem(data_brincagem, gta)   # v1.15.0

        if not erro and not confirmo:
            erro = 'É necessário marcar "Revisei os dados e confirmo a Brincagem".'

        # ---------------------------------------------------
        # VALIDACAO 3 - categorias + brincos JA RESERVADOS.
        # ---------------------------------------------------
        categorias_db = (
            db.query(GtaAnimal)
            .filter_by(id_gta=gta.id)
            .order_by(GtaAnimal.id.asc())
            .all()
        )
        quantidades = [categoria.quantidade for categoria in categorias_db]

        # v1.17.0 - o brete prevalece: confere de novo se os brincos reservados continuam
        # livres; se mudou, a sequencia e ajustada e o escritorio confirma os numeros novos.
        brincos_reservados = []
        aviso_ajuste = None
        if not erro:
            brincos_reservados, aviso_ajuste, erro_reserva = _garantir_reserva(db, gta, quantidades)
            if erro_reserva:
                erro = erro_reserva

        categorias_brincos = []
        if not erro:
            ponteiro = 0
            for qtd in quantidades:
                categorias_brincos.append(brincos_reservados[ponteiro:ponteiro + qtd])
                ponteiro += qtd

        # ---------------------------------------------------
        # VALIDACAO 3b (v1.15.0) - Peso Balancao (opcional). Vazio = nada
        # e gravado. Preenchido: inteiro > 0, e a MEDIA por animal
        # (arredondada para inteiro) fica entre 1 e 1.000 kg.
        # ---------------------------------------------------
        peso_balancao_total = None
        media_peso          = None
        if not erro:
            peso_balancao_total, erro_peso = _ler_peso_balancao(request.form.get('peso_balancao'))
            if erro_peso:
                erro = erro_peso
            elif peso_balancao_total is not None:
                total_animais_gta = sum(quantidades)
                media_peso = (
                    Decimal(peso_balancao_total) / Decimal(total_animais_gta)
                ).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                if media_peso < 1:
                    erro = (
                        f'Peso Balanção incorreto: a média ficou abaixo de 1 kg por animal '
                        f'({total_animais_gta} animais).'
                    )
                elif media_peso > PESO_MAXIMO_POR_ANIMAL_KG:
                    erro = (
                        f'Peso Balanção incorreto: a média ficou em {media_peso} kg por animal '
                        f'({total_animais_gta} animais). O máximo é {PESO_MAXIMO_POR_ANIMAL_KG} kg.'
                    )

        # ---------------------------------------------------
        # VALIDACAO 4 - Nro Meses / Nascimento / Lote por
        # categoria. eras_dias (idade em dias na brincagem) e o
        # que decide a Cota Hilton mais abaixo (v1.13.0).
        # ---------------------------------------------------
        dados_categorias = []
        if not erro:
            for indice, categoria in enumerate(categorias_db):
                nro_meses_str   = (request.form.get(f'nro_meses_{indice}') or '').strip()
                nascimento_str  = (request.form.get(f'nascimento_{indice}') or '').strip()
                lote_categoria  = (request.form.get(f'lote_{indice}') or '').strip().upper() or None

                if not nro_meses_str.isdecimal():
                    erro = f'Nro Meses da categoria "{categoria.idade_meses}" é obrigatório.'
                    break
                nro_meses = int(nro_meses_str)

                nascimento = _parse_data_br(nascimento_str)
                if not nascimento:
                    nascimento = data_brincagem - timedelta(days=nro_meses * 30)

                # v1.21.0 - Nascimento DEPOIS da Data Brincagem e impossivel: nao grava.
                if nascimento_depois_da_brincagem(nascimento, data_brincagem):
                    erro = f'Categoria "{categoria.idade_meses}": {MENSAGEM_NASCIMENTO_DEPOIS_BRINCAGEM}'
                    break

                eras_dias = (data_brincagem - nascimento).days

                dados_categorias.append({
                    'categoria':  categoria,
                    'nascimento': nascimento,
                    'eras_dias':  eras_dias,
                    'lote':       lote_categoria,
                    'nro_meses':  nro_meses,
                })

        # ---------------------------------------------------
        # VALIDACAO 5 - resolve id_especie de cada categoria
        # contra o catalogo tb_4002_especie.
        # ---------------------------------------------------
        mapa_especie = {}
        if not erro:
            codigos_especie_distintos = list({categoria.especie for categoria in categorias_db})
            especies_db = (
                db.query(Especie)
                .filter(Especie.codigo.in_(codigos_especie_distintos))
                .all()
            )
            mapa_especie = {especie.codigo: especie.id for especie in especies_db}

            codigos_nao_encontrados = set(codigos_especie_distintos) - set(mapa_especie.keys())
            if codigos_nao_encontrados:
                erro = (
                    f'Espécie "{", ".join(codigos_nao_encontrados)}" não encontrada no catálogo '
                    f'(tb_4002_especie). Nenhum dado foi gravado. Avise a Consiste.'
                )

        # ---------------------------------------------------
        # Se qualquer validacao falhou: reexibe o Formulario.
        # ---------------------------------------------------
        if erro or aviso_ajuste:
            contexto = _montar_contexto_formulario(
                db, gta, dados_repostos=dict(request.form), erro=erro, reservar=False,
                aviso_sequencia=aviso_ajuste,
            )
            if aviso_ajuste:
                db.commit()   # v1.17.0 - a sequencia ajustada (nova reserva) fica gravada; NAO grava a Brincagem
            return render_template('produtor/brincagem_formulario.html', **contexto)

        # ---------------------------------------------------
        # 5. Dados auxiliares para as gravacoes.
        # ---------------------------------------------------
        parceiro_propriedade = gta.parceiro_propriedade
        parceiro              = parceiro_propriedade.parceiro if parceiro_propriedade else None
        id_origem             = parceiro.id if parceiro else None

        origem_propriedade = parceiro_propriedade.estabelecimento if parceiro_propriedade else None
        origem_cpf_cnpj      = parceiro.cpf_cnpj if parceiro else None

        id_usuario       = session.get('usuario_id')
        id_propriedade   = gta.id_propriedade

        propriedade_destino_obj = gta.propriedade
        produtor_destino         = db.get(Produtor, session['id_produtor'])
        destino_propriedade      = propriedade_destino_obj.nome if propriedade_destino_obj else None
        destino_cpf_cnpj          = produtor_destino.cpf_cnpj if produtor_destino else None

        # CORRIGIDO v1.12.0: liberacao_abate a partir de
        # data_brincagem (regra real), NAO mais gta.data_entrega.
        liberacao_abate = data_brincagem + timedelta(days=DIAS_LIBERACAO_ABATE)

        # ---------------------------------------------------
        # 5b (v1.15.0). Peso Balancao na GTA - ANTES do laco, porque a
        # tb_2017 le gta.peso_medio_entrada. Os valores de antes/depois
        # vao para o Log (Desfazer). Sem peso informado, o Log fica como
        # sempre foi (so o status_brincagem).
        # ---------------------------------------------------
        dados_antes_gta  = {'status_brincagem': gta.status_brincagem}
        dados_depois_gta = {'status_brincagem': 'BRINCADO'}
        observacao_pesagem = None

        if media_peso is not None:
            dados_antes_gta.update({
                'pesagem_balancao':   str(gta.pesagem_balancao) if gta.pesagem_balancao is not None else None,
                'pesagem_data':       str(gta.pesagem_data) if gta.pesagem_data is not None else None,
                'peso_medio_entrada': str(gta.peso_medio_entrada) if gta.peso_medio_entrada is not None else None,
            })
            gta.pesagem_balancao   = Decimal(peso_balancao_total)
            gta.pesagem_data       = data_brincagem
            gta.peso_medio_entrada = media_peso
            db.flush()
            dados_depois_gta.update({
                'pesagem_balancao':   str(gta.pesagem_balancao),
                'pesagem_data':       str(data_brincagem),
                'peso_medio_entrada': str(media_peso),
            })
            peso_total_br = f'{peso_balancao_total:,}'.replace(',', '.')
            observacao_pesagem = (
                f'Média do Peso Balanção: {peso_total_br} kg / {sum(quantidades)} animais'
            )

        # ---------------------------------------------------
        # 6. Registra o "recibo" da operacao no Log.
        # ---------------------------------------------------
        id_operacao = registrar_operacao(
            db,
            id_usuario=id_usuario,
            id_propriedade=id_propriedade,
            modulo='brincagem_sequencial',
            descricao=f'Brincagem Sequencial da GTA {gta.numero_gta_completo}',
        )

        # ---------------------------------------------------
        # 7. Gravacao real, categoria por categoria, brinco por
        #    brinco - usando os brincos JA RESERVADOS.
        # ---------------------------------------------------
        todos_brincos_consumidos = []

        for dados_cat, brincos_categoria in zip(dados_categorias, categorias_brincos):
            categoria  = dados_cat['categoria']
            nascimento = dados_cat['nascimento']
            eras_dias  = dados_cat['eras_dias']
            lote       = dados_cat['lote']

            # v1.13.0 - regra central: idade ATE 306 dias na brincagem.
            cota_hilton_categoria = eh_cota_hilton(eras_dias)
            id_especie_categoria = mapa_especie[categoria.especie]

            for brinco in brincos_categoria:
                todos_brincos_consumidos.append(brinco)

                # ---- 1. tb_7017 (UPDATE) ----
                dados_antes_7017 = {
                    'status':          brinco.status,
                    'raca':            brinco.raca,
                    'sexo':            brinco.sexo,
                    'data_brincagem':  brinco.data_brincagem,
                    'nascimento':      brinco.nascimento,
                    'eras_dias':       brinco.eras_dias,
                    'saida_data':      brinco.saida_data,
                    'saida_gta':       brinco.saida_gta,
                }
                brinco.status            = 'ENTRADA'
                brinco.raca               = codigo_raca
                brinco.sexo                = categoria.sexo
                brinco.data_brincagem       = data_brincagem
                brinco.nascimento            = nascimento
                brinco.eras_dias              = eras_dias
                brinco.saida_data              = data_brincagem
                brinco.saida_gta                = numero_gta_para_3008
                brinco.reservado_id_gta           = None
                brinco.reservado_ate                = None
                db.flush()

                registrar_item(
                    db, id_operacao, tabela='tb_7017_entrada_brincos_rfid',
                    id_registro=brinco.id, tipo_mudanca='UPDATE',
                    dados_antes=dados_antes_7017,
                    dados_depois={
                        'status': 'ENTRADA', 'raca': codigo_raca, 'sexo': categoria.sexo,
                        'data_brincagem': str(data_brincagem), 'nascimento': str(nascimento),
                        'eras_dias': eras_dias, 'saida_data': str(data_brincagem),
                        'saida_gta': numero_gta_para_3008,
                    },
                )

                # ---- 2. tb_3008 (CREATE) ----
                brinco_saida = BrincoSaida(
                    id_propriedade=id_propriedade,
                    id_lote_entrada=brinco.id_lote_entrada,
                    sisbov=brinco.sisbov,
                    rfid=brinco.rfid,
                    data_saida=data_brincagem,
                    gta=numero_gta_para_3008,
                    origem='COMPRA',
                )
                db.add(brinco_saida)
                db.flush()

                registrar_item(
                    db, id_operacao, tabela='tb_3008_brincos_saida',
                    id_registro=brinco_saida.id, tipo_mudanca='INSERT',
                    dados_antes=None, dados_depois={'sisbov': brinco.sisbov},
                )

                # ---- 3. tb_2001 (CREATE) - data_brincagem e
                # liberacao_abate CORRIGIDAS v1.12.0 ----
                entrada = Entrada(
                    sisbov=brinco.sisbov,
                    manejo=brinco.manejo,
                    rfid=brinco.rfid,
                    id_especie=id_especie_categoria,
                    sexo=categoria.sexo,
                    nascimento=nascimento,
                    eras_dias=eras_dias,
                    id_raca=raca_obj.id,
                    id_aptidao=None,
                    cota_hilton=cota_hilton_categoria,
                    data_brincagem=data_brincagem,
                    liberacao_abate=liberacao_abate,
                    conferido_brete=False,   # v1.16.0 - o brete confere os brincos depois
                    tipo_entrada='COMPRA',
                    brincos='INTERNO',
                    id_gta_entrada=gta.id,
                    data_inclusao=gta.data_entrega,
                    lote=lote,
                    id_origem=id_origem,
                    id_propriedade=id_propriedade,
                )
                db.add(entrada)
                db.flush()

                registrar_item(
                    db, id_operacao, tabela='tb_2001', id_registro=entrada.id,
                    tipo_mudanca='INSERT', dados_antes=None,
                    dados_depois={'sisbov': entrada.sisbov},
                )

                # ---- 3a. BLOCKCHAIN (v1.19.0) - evento ENTRADA (compra) do animal ----
                registrar_evento_animal(db, entrada, TIPO_ENTRADA, id_usuario=id_usuario, id_operacao=id_operacao)

                # ---- 3b. tb_4003_pesos (CREATE) - v1.15.0: 1a pesagem
                # (sequencia 1) = media do Peso Balancao, so se informado ----
                if media_peso is not None:
                    pesagem = registrar_pesagem(
                        db, id_propriedade, brinco.sisbov, brinco.rfid, data_brincagem,
                        media_peso, eras_dias, lote, ORIGEM_PESAGEM_BALANCAO, id_usuario,
                        observacao=observacao_pesagem, id_operacao=id_operacao,
                    )
                    if pesagem is not None:
                        registrar_item(
                            db, id_operacao, tabela='tb_4003_pesos', id_registro=pesagem.id,
                            tipo_mudanca='INSERT', dados_antes=None,
                            dados_depois={
                                'sisbov': brinco.sisbov, 'sequencia': pesagem.sequencia,
                                'peso': str(media_peso),
                            },
                        )

                # ---- 4. tb_2017 (CREATE) ----
                movimentacao = Movimentacao(
                    # v1.22.0 (Sessao 101) - copia fiel da tb_2001: campos novos da tb_2017
                    lote=entrada.lote, data_brincagem=entrada.data_brincagem,
                    conferido_brete=entrada.conferido_brete, conferido_em=entrada.conferido_em,
                    id_origem=entrada.id_origem, id_gta_entrada=entrada.id_gta_entrada,
                    id_animal=entrada.id,
                    id_propriedade=id_propriedade,
                    sisbov=brinco.sisbov,
                    manejo=brinco.manejo,
                    rfid=brinco.rfid,
                    negociacao='COMPRA',
                    brincos='INTERNO',
                    id_especie=id_especie_categoria,
                    sexo=categoria.sexo,
                    nascimento=nascimento,
                    dias=eras_dias,
                    cota_hilton=cota_hilton_categoria,
                    id_aptidao=None,
                    id_raca=raca_obj.id,
                    tipo_entrada='COMPRA',
                    gta_entrada=gta.numero_gta_completo,
                    gta_entrada_emissao=gta.data_emissao,
                    gta_entrada_validade=gta.data_validade,
                    gta_entrada_animais=gta.qtde_animais,
                    data_inclusao=gta.data_entrega,
                    entrada=gta.data_entrega,
                    origem_propriedade=origem_propriedade,
                    origem_cpf_cnpj=origem_cpf_cnpj,
                    destino_propriedade=destino_propriedade,
                    destino_cpf_cnpj=destino_cpf_cnpj,
                    data_movimentacao=gta.data_entrega,
                    peso_medio=gta.peso_medio_entrada,
                )
                db.add(movimentacao)
                db.flush()

                registrar_item(
                    db, id_operacao, tabela='tb_2017_movimentacoes',
                    id_registro=movimentacao.id, tipo_mudanca='INSERT',
                    dados_antes=None, dados_depois={'sisbov': movimentacao.sisbov},
                )

                # ---- 5. tb_7002 (CREATE) - numero_pia com lock ----
                numero_pia = _obter_proximo_numero_pia(db, id_propriedade)
                pia = Pia(
                    id_propriedade=id_propriedade,
                    numero_pia=numero_pia,
                    id_gta=gta.id,
                    sisbov=brinco.sisbov,
                    manejo=brinco.manejo,
                    nascimento=nascimento,
                    idade_meses=round(eras_dias / 30),
                    sexo=categoria.sexo,
                    raca_codigo=codigo_raca,
                    motivo='ENTRADA',
                    data_identificacao=data_brincagem,
                )
                db.add(pia)
                db.flush()

                registrar_item(
                    db, id_operacao, tabela='tb_7002_pia', id_registro=pia.id,
                    tipo_mudanca='INSERT',
                    dados_antes=None,
                    dados_depois={'numero_pia': numero_pia, 'sisbov': pia.sisbov},
                )

        # ---- 6. tb_3007 (UPDATE, por LOTE - saldo E qtde_saida, v1.12.1) ----
        _decrementar_saldo_lotes(db, id_operacao, todos_brincos_consumidos)

        # ---- 7. tb_4001_gta.status_brincagem (UPDATE) ----
        # v1.15.0 - dados_antes_gta / dados_depois_gta ja foram montados no
        # passo 5b (antes do laco), com o Peso Balancao quando informado.
        gta.status_brincagem = 'BRINCADO'
        db.flush()

        registrar_item(
            db, id_operacao, tabela='tb_4001_gta', id_registro=gta.id,
            tipo_mudanca='UPDATE',
            dados_antes=dados_antes_gta,
            dados_depois=dados_depois_gta,
        )

        # v1.12.1 - BUG REAL: o numero da GTA e lido ANTES do commit
        # (depois dele nao se le mais nada dos objetos do banco -
        # regra da Sessao 078).
        numero_gta_confirmada = gta.numero_gta_completo

        # ---- v1.24.0: resumo da CAIXA DE SUCESSO, montado ANTES do commit (nada e lido do banco depois dele) ----
        faixas_sucesso = [f['texto'] for f in _formatar_faixas_brincos([b.sisbov for b in todos_brincos_consumidos])]
        resumo_sucesso = {
            'numero_gta':      numero_gta_confirmada,
            'qtde':            len(todos_brincos_consumidos),
            'data_brincagem':  data_brincagem.strftime('%d/%m/%Y'),
            'raca':            raca_obj.nome,
            'liberacao_abate': liberacao_abate.strftime('%d/%m/%Y'),
            'peso_medio':      str(media_peso) if media_peso is not None else '',
            'faixas':          faixas_sucesso[:MAX_FAIXAS_SUCESSO],
            'faixas_omitidas': max(len(faixas_sucesso) - MAX_FAIXAS_SUCESSO, 0),
        }

        db.commit()

    session[CHAVE_SUCESSO_SESSAO] = resumo_sucesso
    return redirect(URL_CONCLUIDA)


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-sequencial/concluida  (v1.24.0)
# CAIXA DE SUCESSO (Padrao No7) depois do Salvar. Le e apaga o resumo
# guardado na sessao; sem resumo (F5, link antigo), volta para a Lista.
# -------------------------------------------------------
@brincagem_sequencial.route(URL_CONCLUIDA)
def concluida():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    resumo = session.pop(CHAVE_SUCESSO_SESSAO, None)
    if not resumo:
        return redirect(URL_LISTA)

    mudancas = [
        {'campo': 'GTA',                 'antes': None, 'depois': resumo['numero_gta']},
        {'campo': 'Animais brincados',   'antes': None, 'depois': str(resumo['qtde'])},
        {'campo': 'Data Brincagem',      'antes': None, 'depois': resumo['data_brincagem']},
        {'campo': 'Raça',                'antes': None, 'depois': resumo['raca']},
        {'campo': 'Liberação p/ abate',  'antes': None, 'depois': resumo['liberacao_abate']},
    ]
    if resumo['peso_medio']:
        mudancas.append({'campo': 'Peso médio', 'antes': None, 'depois': f"{resumo['peso_medio']} kg"})

    notas = []
    if resumo['faixas']:
        texto = 'SISBOV utilizados: ' + ' | '.join(resumo['faixas'])
        if resumo['faixas_omitidas']:
            texto += f" | ... e mais {resumo['faixas_omitidas']} faixa(s) (consulte pelo Relatório de ERAS)"
        notas.append(texto)

    contexto = dict(
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )
    return render_caixa_sucesso(
        contexto, titulo='Brincagem confirmada e gravada com sucesso!', subtitulo=f"GTA {resumo['numero_gta']}",
        mudancas=mudancas, notas=notas,
        botoes=[{'texto': 'Brincar outra GTA', 'url': URL_LISTA, 'primario': True},
                {'texto': 'Voltar ao Hub de Entrada', 'url': _url_voltar_pos_selecao(), 'primario': False}],
        url_voltar=URL_LISTA, titulo_pagina='Orion SISBOV — Brincagem confirmada',
    )

# -------------------------------------------------------
# v1.25.0 - quantos brincos estao RESERVADOS a esta GTA no brete (Leitor/Bastao).
# -------------------------------------------------------
def _lidos_reservados_gta(db, id_gta):
    return (
        db.query(func.count(Brincagem.id))
        .filter(
            Brincagem.id_gta_reservada == int(id_gta),
            Brincagem.sts == False,   # noqa: E712
            Brincagem.id_gta.is_(None),
        )
        .scalar()
    ) or 0


# =========================================================
# FIM DE ARQUIVO: backend\routers\brincagem_sequencial.py
# =========================================================
