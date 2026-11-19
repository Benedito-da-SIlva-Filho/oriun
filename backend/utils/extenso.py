# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\extenso.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-03 17:00 -03
# ATUALIZADO EM: 2026-09-03 17:00 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Utilitario GENERICO: converte um numero inteiro (0 a 999) para
#     sua forma por extenso em portugues, em maiusculas - usado no
#     Documento de Cancelamento ("1 (UM Brinco(s))"), mas escrito de
#     forma reaproveitavel para qualquer outro documento formal que
#     precise disso no futuro.
#
#     Faixa coberta: 0 a 999. Suficiente para o uso atual (MAX_FAIXA
#     de brincos_cancelamento.py e 500) - se um dia precisar de
#     numeros maiores (milhares), esta funcao precisa ser estendida
#     (levanta ValueError acima de 999, de proposito, para nunca
#     devolver um valor incorreto/truncado silenciosamente).
#
#     Sem dependencia externa (decisao de Benedito, Sessao 045: nao
#     usar biblioteca como num2words) - implementacao propria,
#     testada com bateria de 24 casos reais (unidades, dezenas,
#     "e" conector, casos especiais CEM/CENTO, todas as centenas)
#     antes desta entrega.
#
#     v1.0.0: Criacao do modulo (Sessao 045, 03/09/2026, 17:00 -03).
# =========================================================

UNIDADES = ['', 'UM', 'DOIS', 'TRÊS', 'QUATRO', 'CINCO', 'SEIS', 'SETE', 'OITO', 'NOVE']
DEZ_A_DEZENOVE = ['DEZ', 'ONZE', 'DOZE', 'TREZE', 'QUATORZE', 'QUINZE', 'DEZESSEIS', 'DEZESSETE', 'DEZOITO', 'DEZENOVE']
DEZENAS = ['', '', 'VINTE', 'TRINTA', 'QUARENTA', 'CINQUENTA', 'SESSENTA', 'SETENTA', 'OITENTA', 'NOVENTA']
CENTENAS = ['', 'CENTO', 'DUZENTOS', 'TREZENTOS', 'QUATROCENTOS', 'QUINHENTOS', 'SEISCENTOS', 'SETECENTOS', 'OITOCENTOS', 'NOVECENTOS']


# -------------------------------------------------------
# Funcao: numero_por_extenso() - converte um inteiro de 0 a 999 para
# sua forma por extenso em portugues, maiusculas, seguindo as regras
# gramaticais padrao (conector "E" entre centena/dezena/unidade,
# caso especial "CEM" para exatamente 100, dezenas de 10-19 com
# nomes proprios).
# -------------------------------------------------------
def numero_por_extenso(n):
    if n == 0:
        return 'ZERO'
    if n < 0 or n > 999:
        raise ValueError('numero_por_extenso() so cobre a faixa de 0 a 999.')

    partes = []

    centena = n // 100
    resto = n % 100

    if centena > 0:
        if n == 100:
            partes.append('CEM')
        else:
            partes.append(CENTENAS[centena])

    if resto > 0:
        if resto < 10:
            partes.append(UNIDADES[resto])
        elif resto < 20:
            partes.append(DEZ_A_DEZENOVE[resto - 10])
        else:
            dezena = resto // 10
            unidade = resto % 10
            if unidade == 0:
                partes.append(DEZENAS[dezena])
            else:
                partes.append(f'{DEZENAS[dezena]} E {UNIDADES[unidade]}')

    return ' E '.join(partes)

# =========================================================
# FIM DE ARQUIVO: backend\utils\extenso.py
# =========================================================