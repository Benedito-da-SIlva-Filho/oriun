# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils\
# MODULO: backend\utils\regras_sisbov.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-28 20:05 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.8.0
# v1.8.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (4 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.7.0: Sessao 123 (2026-11-13 19:40 -03) - AUDITORIA ETAPA 4 (2a passada, decisao de Benedito 'C'): nova data_nascimento_por_meses() (nascimento por meses de calendario). REVERSAO: .bak_antes_etapa4c.
#
# DESCRICAO:
#     Regras de negocio do SISBOV num lugar so. Todo modulo que
#     precisar destas regras IMPORTA daqui - nunca repete o numero
#     numa constante local (origem: Sessao 081, a regra da Cota
#     Hilton estava copiada em brincagem_sequencial.py e
#     vincular_gta.py, cada um com a sua versao).
#
#     COTA HILTON (decisao de Benedito, Sessao 081):
#       - Animal inserido na base do MAPA com ATE 10 meses entra
#         na Lista da Cota Hilton (bonus financeiro ao Produtor).
#       - "Ate 10 meses" = idade em DIAS na data da brincagem
#         (eras_dias = data_brincagem - nascimento) MENOR OU IGUAL
#         a 306 dias. Vale para Compra e para Nascimento/Desmame.
#       - Substitui a regra antiga "Nro Meses < 10" (que deixava
#         de fora animais de 10 meses e, no Vincular GTA, animais
#         de ~285 dias arredondados para "10").
#       - O CTH e gravado UMA VEZ, no evento de entrada - nunca
#         recalculado depois (mesmo padrao da idade no evento).
#
#     MES = 30 DIAS (decisao de Benedito, Sessao 081):
#       - O Orion inteiro usa 1 mes = 30 dias para estimar o
#         Nascimento a partir do Nro Meses (Leitor, Bastao,
#         Consulta/Alterar, Sequencial, Vincular). O GERAS usava
#         365/12 (30,4167). A diferenca (poucos dias) foi aceita
#         para nao mexer em 10 arquivos ja validados; a data de
#         Nascimento continua editavel pelo usuario.
#       - DIAS_POR_MES fica aqui para os modulos NOVOS (ex.:
#         Brincagem de Nascimento). Os modulos antigos mantem a
#         propria constante local de 30 - mesmo valor.
#
#     TIPO DE ENTRADA (v1.1.0, decisao de Benedito, Sessao 082):
#       - Lista FIXA (nao e catalogo no banco - Regra de Ouro #8
#         perguntada e respondida): COMPRA ou NASCIMENTO.
#       - Usada por todas as telas que perguntam o tipo (Leitor,
#         Bastao e, depois, Brincagem Sequencial). No banco grava
#         o CODIGO (COMPRA/NASCIMENTO); na tela mostra o texto.
#       - Protegida por CHECK no banco (tb_5001_brincagem.
#         tipo_entrada).
#
#   v1.0.0: Criacao (Sessao 081).
#   v1.1.0: Sessao 082 (29/09/2026, 20:05 -03) - Lista fixa do
#       Tipo de Entrada (TIPO_ENTRADA_COMPRA, TIPO_ENTRADA_
#       NASCIMENTO, TIPOS_ENTRADA) + funcao descricao_tipo_entrada().
#       Nenhuma mudanca na Cota Hilton nem no DIAS_POR_MES.
#   v1.2.0: Sessao 084 (02/10/2026, 21:00 -03) - PRAZO DA NOTIFICACAO DE
#       NASCIMENTO centralizado (decisao de Benedito: regra num lugar so):
#       PRAZO_ENVIO_NOTIFICACAO_DIAS (30 dias, contados da Data de
#       Brincagem) e DIAS_ALERTA_PRAZO_NOTIFICACAO (alerta quando restam
#       ate 5 dias ou ja venceu). Antes estavam copiados em notificacao_
#       nascimento.py e alerta_prazo_notificacao.py. NAO muda o prazo da
#       Brincagem da GTA de Compra (brincagem_sequencial.py - outra regra).
#   v1.3.0: Sessao 084 (02/10/2026, 19:20 -03) - DATA DA BRINCAGEM DO
#       NASCIMENTO NAO PODE TER MAIS DE 30 DIAS (decisao de Benedito: o
#       prazo de envio da Notificacao ja nasceria vencido e a data
#       errada de digitacao passava sem aviso). NOVA data_brincagem_
#       vencida() (hoje - data MAIOR que PRAZO_ENVIO_NOTIFICACAO_DIAS;
#       no dia 30 ainda vale - mesmo criterio do prazo restante da lista
#       de Notificacoes) e a mensagem unica MENSAGEM_DATA_BRINCAGEM_
#       VENCIDA. Usadas pelo escritorio (brincagem_nascimento.py), pelo
#       Leitor e pelo Bastao. Nenhuma outra mudanca.
#   v1.4.0: Sessao 085 (04/10/2026, 18:20 -03) - SERIE DA GTA POR UF (decisao
#       de Benedito: Goias tem Serie com 2 letras; as demais UFs, 1 letra).
#       Regra num lugar so: SERIE_GTA_TAMANHO_POR_UF (hoje so GO; outro
#       Estado que adotar 2 letras entra nesta lista) + tamanho_serie_gta()
#       e mensagem_serie_gta(). Usadas por gta_manual.py e gta_consulta.py
#       (e pelos 2 formularios, que ajustam o limite do campo Serie ao
#       escolher a UF). A coluna tb_4001_gta.serie_gta ja comporta 5
#       posicoes - sem mudanca de banco. O Numero continua com 6 digitos.
#   v1.5.0: Sessao 094 (12/10/2026, 15:25 -03) - BRINCO SISBOV EM DOIS MODELOS
#       (demanda do MAPA, decisao de Benedito). ANTIGO: comeca com 105, 14
#       digitos digitados + DV calculado (pesos 2 a 9 da direita para a
#       esquerda, voltando para 2; DV = 11 - resto da soma por 11; 10 ou 11
#       vira 0) = 15 digitos gravados; a faixa soma na BASE de 14 digitos e
#       recalcula o DV de cada brinco; manejo = 6 digitos antes do DV. NOVO:
#       qualquer outro inicio, 15 digitos sequenciais, sem DV; manejo = 6
#       ultimos. NOVAS: modelo_do_sisbov, calcular_dv_sisbov, completar_
#       sisbov_antigo, sisbov_confere, manejo_do_sisbov, extremos_faixa_sisbov,
#       gerar_faixa_sisbov.
#       So acrescentou; nada do que existia foi alterado. Os 8 modulos que
#       calculam o manejo com os 6 ultimos digitos NAO foram trocados.
#   v1.6.0: Sessao 096 (14/10/2026, 10:05 -03) - NASCIMENTO DEPOIS DA BRINCAGEM
#       (decisao de Benedito: caso impossivel, BLOQUEIA em Compra e Nascimento).
#       NOVAS: nascimento_depois_da_brincagem() e MENSAGEM_NASCIMENTO_DEPOIS_
#       BRINCAGEM. So acrescentou; nada do que existia foi alterado.
#       REVERSAO: devolver .bak_antes_nasc_cth_s096.
# =========================================================

from datetime import date
import calendar


# -------------------------------------------------------
# Constantes oficiais
# -------------------------------------------------------
DIAS_MAX_COTA_HILTON = 306   # idade em dias na brincagem: ate este valor = CTH
DIAS_POR_MES         = 30    # 1 mes = 30 dias (ver DESCRICAO)

# v1.4.0 - Serie da GTA: quantas LETRAS por UF. Padrao 1; Goias 2.
SERIE_GTA_TAMANHO_PADRAO = 1
SERIE_GTA_TAMANHO_POR_UF = {'GO': 2}

# v1.2.0 - prazo de envio da Notificacao de Nascimento a Certificadora,
# contado da Data de Brincagem, e a antecedencia do alerta (Home e lista).
PRAZO_ENVIO_NOTIFICACAO_DIAS      = 30
DIAS_ALERTA_PRAZO_NOTIFICACAO     = 5

# v1.3.0 - mensagem unica do bloqueio da Data da Brincagem do Nascimento
# com mais de PRAZO_ENVIO_NOTIFICACAO_DIAS dias.
MENSAGEM_DATA_BRINCAGEM_VENCIDA = (
    'Data da Brincagem com mais de {dias} dias (prazo de envio da Notificação vencido). '
    'Confira a data digitada.'
).format(dias=PRAZO_ENVIO_NOTIFICACAO_DIAS)

# v1.6.0 - mensagem unica do bloqueio de Nascimento posterior a Data da
# Brincagem (Compra e Nascimento/Desmame).
MENSAGEM_NASCIMENTO_DEPOIS_BRINCAGEM = (
    'Data de Nascimento posterior à Data da Brincagem. Confira as datas digitadas.'
)

# v1.1.0 - Tipo de Entrada (lista fixa - ver DESCRICAO). Ordem =
# ordem do dropdown. (codigo gravado no banco, texto da tela)
TIPO_ENTRADA_COMPRA     = 'COMPRA'
TIPO_ENTRADA_NASCIMENTO = 'NASCIMENTO'
TIPOS_ENTRADA = (
    (TIPO_ENTRADA_COMPRA,     'Compra'),
    (TIPO_ENTRADA_NASCIMENTO, 'Nascimento / Desmame'),
)


# -------------------------------------------------------
# Funcao: o animal e elegivel a Cota Hilton?
# eras_dias = (data_brincagem - nascimento).days.
# Sem idade ou idade negativa (Nascimento depois da Brincagem,
# dado incoerente) -> False: na duvida, nao marca CTH.
# -------------------------------------------------------
def eh_cota_hilton(eras_dias):
    if eras_dias is None:
        return False
    return 0 <= eras_dias <= DIAS_MAX_COTA_HILTON

# -------------------------------------------------------
# Funcao: data_nascimento_por_meses (Etapa 4, 2a passada - decisao de Benedito 'C')
# Nascimento do animal LANCADO POR NASCIMENTO (digita-se o Nro de Meses): a Data de Brincagem
# menos N MESES DE CALENDARIO (mesmo dia, N meses atras; dia que nao existe no mes vira o ultimo
# dia dele). Assim os 'meses completos' da Notificacao de Nascimento e dos Nascimentos por periodo
# batem SEMPRE com o numero digitado (com 30 dias por mes o PDF mostrava 1 mes a menos).
# A faixa de idade (tb_4006) segue pela conta antiga (meses x DIAS_POR_MES); a Cota Hilton segue
# pela idade REAL em dias (ate 306; 10 meses de calendario no maximo = 306: mesmo resultado de antes).
# -------------------------------------------------------
def data_nascimento_por_meses(data_brincagem, nro_meses):
    total = data_brincagem.year * 12 + (data_brincagem.month - 1) - int(nro_meses)
    ano, mes0 = divmod(total, 12)
    mes = mes0 + 1
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(data_brincagem.day, ultimo_dia))



# -------------------------------------------------------
# Funcao (v1.6.0): o Nascimento e POSTERIOR a Data da Brincagem?
# Caso impossivel (o animal nao pode ser brincado antes de nascer).
# Vale para Compra e para Nascimento/Desmame. Falta de qualquer das
# duas datas -> False (quem chama valida a obrigatoriedade).
# -------------------------------------------------------
def nascimento_depois_da_brincagem(nascimento, data_brincagem):
    if nascimento is None or data_brincagem is None:
        return False
    return nascimento > data_brincagem


# -------------------------------------------------------
# Funcao (v1.3.0): a Data da Brincagem de um NASCIMENTO ja passou do
# prazo de envio da Notificacao? (hoje - data) > PRAZO_ENVIO_NOTIFICACAO_
# DIAS. No dia 30 ainda vale. Sem data -> False (quem chama valida
# obrigatoriedade). Data futura -> False (outra regra, outro aviso).
# 'hoje' so existe para teste; em producao e date.today().
# -------------------------------------------------------
def data_brincagem_vencida(data_brincagem, hoje=None):
    if data_brincagem is None:
        return False
    hoje = hoje or date.today()
    return (hoje - data_brincagem).days > PRAZO_ENVIO_NOTIFICACAO_DIAS


# -------------------------------------------------------
# Funcao (v1.1.0): codigo do Tipo de Entrada -> texto da tela.
# Codigo desconhecido devolve o proprio codigo (nunca quebra a
# tela).
# -------------------------------------------------------
def descricao_tipo_entrada(codigo):
    for valor, texto in TIPOS_ENTRADA:
        if valor == codigo:
            return texto
    return codigo or ''


# -------------------------------------------------------
# Funcao (v1.4.0): quantas letras a Serie da GTA desta UF deve ter.
# UF desconhecida ou vazia = padrao (1 letra).
# -------------------------------------------------------
def tamanho_serie_gta(uf):
    return SERIE_GTA_TAMANHO_POR_UF.get((uf or '').strip().upper(), SERIE_GTA_TAMANHO_PADRAO)


# -------------------------------------------------------
# Funcao (v1.4.0): mensagem de erro da Serie para a UF informada.
# Para 1 letra mantem o texto de sempre.
# -------------------------------------------------------
def mensagem_serie_gta(uf):
    tamanho = tamanho_serie_gta(uf)
    if tamanho == 1:
        return 'Série da GTA é obrigatória e deve ter exatamente 1 letra!'
    return f'Série da GTA de {(uf or "").strip().upper()} é obrigatória e deve ter exatamente {tamanho} letras!'

# -------------------------------------------------------
# v1.5.0 - BRINCO SISBOV EM DOIS MODELOS (Sessao 094)
#   ANTIGO: comeca com 105. O usuario digita 14 digitos (a BASE) e o
#           Orion calcula o DV. Gravado com 15 (base + DV).
#   NOVO:   qualquer outro inicio. 15 digitos sequenciais, sem DV.
# O que se grava e sempre o numero de 15 digitos, numa coluna so.
# -------------------------------------------------------
PREFIXO_SISBOV_ANTIGO       = '105'
MODELO_SISBOV_ANTIGO        = 'ANTIGO'
MODELO_SISBOV_NOVO          = 'NOVO'
TAMANHO_SISBOV              = 15   # numero gravado (antigo: base + DV)
TAMANHO_BASE_SISBOV_ANTIGO  = 14   # o que o usuario digita no modelo antigo
TAMANHO_MANEJO_SISBOV       = 6
PESOS_DV_SISBOV             = (2, 3, 4, 5, 6, 7, 8, 9)


# Modelo do brinco pelo inicio do numero. Vazio -> None.
def modelo_do_sisbov(sisbov):
    texto = (sisbov or '').strip()
    if not texto:
        return None
    if texto.startswith(PREFIXO_SISBOV_ANTIGO):
        return MODELO_SISBOV_ANTIGO
    return MODELO_SISBOV_NOVO


# DV do modelo antigo: base de 14 digitos -> inteiro de 0 a 9.
# Pesos 2,3,...,9 da DIREITA para a ESQUERDA, voltando para 2.
# DV = 11 - (soma % 11); resultado 10 ou 11 vira 0.
# Conferido contra 70 numeros reais de 3 clientes (Sessao 094).
def calcular_dv_sisbov(base14):
    base = (base14 or '').strip()
    if len(base) != TAMANHO_BASE_SISBOV_ANTIGO or not base.isdecimal():
        raise ValueError('A base do brinco deve ter 14 dígitos numéricos.')
    soma = 0
    for posicao, digito in enumerate(reversed(base)):
        soma += int(digito) * PESOS_DV_SISBOV[posicao % len(PESOS_DV_SISBOV)]
    dv = 11 - (soma % 11)
    return 0 if dv >= 10 else dv


# Base de 14 digitos -> numero de 15 digitos (base + DV).
def completar_sisbov_antigo(base14):
    base = (base14 or '').strip()
    return base + str(calcular_dv_sisbov(base))


# O numero de 15 digitos esta correto? Antigo: confere o DV.
# Novo: so confere o tamanho e que sao digitos (nao ha DV).
def sisbov_confere(sisbov):
    texto = (sisbov or '').strip()
    if len(texto) != TAMANHO_SISBOV or not texto.isdecimal():
        return False
    if modelo_do_sisbov(texto) == MODELO_SISBOV_ANTIGO:
        return completar_sisbov_antigo(texto[:TAMANHO_BASE_SISBOV_ANTIGO]) == texto
    return True


# Manejo = 6 digitos. Antigo: os 6 ANTES do DV. Novo: os 6 ultimos.
def manejo_do_sisbov(sisbov):
    texto = (sisbov or '').strip()
    if len(texto) != TAMANHO_SISBOV or not texto.isdecimal():
        raise ValueError('O brinco deve ter 15 dígitos numéricos.')
    if modelo_do_sisbov(texto) == MODELO_SISBOV_ANTIGO:
        return texto[TAMANHO_BASE_SISBOV_ANTIGO - TAMANHO_MANEJO_SISBOV:TAMANHO_BASE_SISBOV_ANTIGO]
    return texto[-TAMANHO_MANEJO_SISBOV:]


# Primeiro e ultimo numero da faixa, SEM gerar a lista inteira (leve:
# usado pela tela para mostrar Nro Final e DV ao vivo e pela gravacao).
# inicial_digitado: 14 digitos se comecar com 105 (modelo antigo, sem DV);
#                   15 digitos nos demais (modelo novo).
# Devolve (modelo, primeiro15, ultimo15). Levanta ValueError com a
# mensagem pronta para a tela.
def extremos_faixa_sisbov(inicial_digitado, qtde):
    texto = (inicial_digitado or '').strip()
    if not texto.isdecimal():
        raise ValueError('Nro Inicial deve ter apenas dígitos.')
    try:
        qtde = int(qtde)
    except (TypeError, ValueError):
        raise ValueError('Quantidade de brincos incorreta.')
    if qtde < 1:
        raise ValueError('Quantidade de brincos deve ser pelo menos 1.')

    modelo = modelo_do_sisbov(texto)
    if modelo == MODELO_SISBOV_ANTIGO:
        if len(texto) != TAMANHO_BASE_SISBOV_ANTIGO:
            raise ValueError('Brinco do modelo antigo (começa com 105) deve ter 14 dígitos, sem o DV.')
        tamanho = TAMANHO_BASE_SISBOV_ANTIGO
    else:
        if len(texto) != TAMANHO_SISBOV:
            raise ValueError('Brinco do modelo novo deve ter 15 dígitos.')
        tamanho = TAMANHO_SISBOV

    ultimo_int = int(texto) + qtde - 1
    if len(str(ultimo_int)) > tamanho:
        raise ValueError(f'Nro Final passa de {tamanho} dígitos.')
    texto_ultimo = str(ultimo_int).zfill(tamanho)
    if modelo_do_sisbov(texto_ultimo) != modelo:
        raise ValueError('A faixa de brincos muda de modelo no meio (prefixo 105). Reduza a quantidade.')

    if modelo == MODELO_SISBOV_ANTIGO:
        return modelo, completar_sisbov_antigo(texto), completar_sisbov_antigo(texto_ultimo)
    return modelo, texto, texto_ultimo


# Gera a faixa completa de brincos (lista de numeros de 15 digitos).
# Mesmas regras e mesmas mensagens de extremos_faixa_sisbov.
def gerar_faixa_sisbov(inicial_digitado, qtde):
    modelo, _primeiro, _ultimo = extremos_faixa_sisbov(inicial_digitado, qtde)
    texto = inicial_digitado.strip()
    primeiro_int = int(texto)
    ultimo_int = primeiro_int + int(qtde) - 1
    antigo = modelo == MODELO_SISBOV_ANTIGO
    tamanho = TAMANHO_BASE_SISBOV_ANTIGO if antigo else TAMANHO_SISBOV
    faixa = []
    for numero in range(primeiro_int, ultimo_int + 1):
        base = str(numero).zfill(tamanho)
        faixa.append(completar_sisbov_antigo(base) if antigo else base)
    return faixa

# =========================================================
# FIM DE ARQUIVO: backend\utils\regras_sisbov.py
# =========================================================