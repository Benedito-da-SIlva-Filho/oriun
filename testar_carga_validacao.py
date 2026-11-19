# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\Orion\
# MODULO: testar_carga_validacao.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-17 18:38 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Teste da parte PURA da Carga (backend\utils\carga_animais.py: validar_animais e montar_previa), sem banco e sem Flask.
#     Usa o EXTRATO DE VIVOS.pdf real (lido pelo leitor) e casos montados a mao. Rodar na pasta C:\Orion:
#         python testar_carga_validacao.py
#     Saida esperada: "TUDO OK" no final (codigo de saida 0).
#   v1.0.0: Criacao (Carga, 17/11/2026).
# =========================================================

import copy
import os
import sys
from datetime import date

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from backend.leitores import leitor_mapa_extrato_vivos as leitor
from backend.utils import carga_animais as ca

HOJE = date(2026, 11, 17)
RACAS = {'NELORE': (1, 'NE'), 'COMPOSTO': (2, 'XX'), 'ABERDEEN ANGUS': (3, 'AN')}

falhas, total = [], 0


def conferir(nome, obtido, esperado):
    global total
    total += 1
    if obtido != esperado:
        falhas.append(f'{nome}: obtido {obtido!r}, esperado {esperado!r}')


def codigos(itens):
    return sorted({i['codigo'] for i in itens})


extrato = leitor.ler(os.path.join(AQUI, 'EXTRATO DE VIVOS.pdf'))
cab, base = extrato['cabecalho'], extrato['animais']

# 1) arquivo real: sem erro nenhum
erros, alertas = ca.validar_animais(base, cab, RACAS, HOJE)
conferir('arquivo real sem erros', erros, [])
previa = ca.montar_previa(extrato, RACAS, HOJE)
conferir('previa pode gravar', previa['pode_gravar'], True)
conferir('previa lidos', (previa['lidos'], previa['femeas'], previa['machos']), (1244, 31, 1213))
print(f'Arquivo real: {previa["qtd_alertas"]} alerta(s): {[(g["titulo"], g["qtd"]) for g in previa["alertas"]]}')


def com(alteracoes, indice=0):
    """Copia da lista com uma alteracao no animal de posicao indice."""
    lista = copy.deepcopy(base)
    lista[indice].update(alteracoes)
    return lista


# 2) cada erro sozinho
cab_sem_total = dict(cab, total_femea=None, total_macho=None)
e, _ = ca.validar_animais(com({'sisbov': base[1]['sisbov']}), cab_sem_total, RACAS, HOJE)
conferir('SISBOV repetido no arquivo', codigos(e), ['SISBOV_REPETIDO_ARQUIVO'])
e, _ = ca.validar_animais(com({'sisbov': '105500191288652'}), cab_sem_total, RACAS, HOJE)
conferir('DV invalido', codigos(e), ['DV_INVALIDO'])
e, _ = ca.validar_animais(com({'raca_nome': 'Raca Inventada'}), cab_sem_total, RACAS, HOJE)
conferir('raca desconhecida', codigos(e), ['RACA_DESCONHECIDA'])
e, _ = ca.validar_animais(com({'raca_nome': 'nelore'}), cab_sem_total, RACAS, HOJE)
conferir('raca com outra caixa e aceita', e, [])
e, _ = ca.validar_animais(com({'nascimento': date(2027, 1, 1)}), cab_sem_total, RACAS, HOJE)
conferir('nascimento no futuro', codigos(e), ['NASC_FUTURO'])
e, _ = ca.validar_animais(com({'nascimento': date(1900, 1, 1), 'nascimento_texto': '01/01/1900'}), cab_sem_total, RACAS, HOJE)
conferir('data impossivel 1900', codigos(e), ['DATA_IMPOSSIVEL'])
e, _ = ca.validar_animais(com({'nascimento': None, 'nascimento_texto': '31/02/2020'}), cab_sem_total, RACAS, HOJE)
conferir('data impossivel 31/02', codigos(e), ['DATA_IMPOSSIVEL'])
e, _ = ca.validar_animais(com({'data_inclusao': date(2004, 1, 1)}), cab_sem_total, RACAS, HOJE)
conferir('nascimento depois da inclusao', codigos(e), ['NASC_DEPOIS_INCLUSAO'])
e, _ = ca.validar_animais(com({'sexo': None, 'sexo_texto': 'X'}), cab_sem_total, RACAS, HOJE)
conferir('sexo invalido', codigos(e), ['SEXO_INVALIDO'])
e, _ = ca.validar_animais(base[:-1], cab, RACAS, HOJE)
conferir('total do cabecalho diverge', codigos(e), ['TOTAL_DIVERGE'])
e, _ = ca.validar_animais([], cab, RACAS, HOJE)
conferir('arquivo vazio', codigos(e), ['ARQUIVO_VAZIO'])

# 3) alertas (nao barram)
e, al = ca.validar_animais(com({'sexo': 'MACHO', 'nascimento': date(1998, 5, 1), 'data_inclusao': date(2006, 1, 1)}), cab_sem_total, RACAS, HOJE)
conferir('macho antigo: sem erro', e, [])
conferir('macho antigo: alerta', [a['codigo'] for a in al if a['linha'] == 1], ['MACHO_ANTIGO'])
e, al = ca.validar_animais(com({'sexo': 'FEMEA', 'nascimento': date(1995, 5, 1), 'data_inclusao': date(2006, 1, 1)}), cab_sem_total, RACAS, HOJE)
conferir('femea velha: sem erro', e, [])
conferir('femea velha: alerta', [a['codigo'] for a in al if a['linha'] == 1], ['FEMEA_VELHA'])
e, al = ca.validar_animais(com({'sexo': 'FEMEA', 'nascimento': date(1996, 12, 1), 'data_inclusao': date(2006, 1, 1)}), cab_sem_total, RACAS, HOJE)
conferir('femea 29 anos: sem alerta de idade', [a['codigo'] for a in al if a['linha'] == 1 and a['codigo'] == 'FEMEA_VELHA'], [])

# 4) previa: erro do banco entra primeiro e barra
p = ca.montar_previa(extrato, RACAS, HOJE, erros_extra=[{'codigo': 'CARGA_JA_FEITA', 'linha': None, 'sisbov': '', 'mensagem': 'x'}])
conferir('previa barrada por erro do banco', (p['pode_gravar'], p['erros'][0]['codigo']), (False, 'CARGA_JA_FEITA'))
p = ca.montar_previa(dict(extrato, linhas_nao_lidas=[{'pagina': 3, 'texto': '123456789012345 xx'}]), RACAS, HOJE)
conferir('linha nao lida barra', (p['pode_gravar'], 'LINHA_NAO_LIDA' in [g['codigo'] for g in p['erros']]), (False, True))

if falhas:
    print('FALHAS:')
    for f in falhas:
        print('  -', f)
    sys.exit(1)
print(f'{total} conferencias. TUDO OK')

# =========================================================
# FIM DE ARQUIVO: testar_carga_validacao.py
# =========================================================
