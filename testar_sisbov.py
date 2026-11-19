# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\
# MODULO: testar_sisbov.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-12 15:30 -03
# ATUALIZADO EM: 2026-10-12 15:30 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Teste das regras do brinco SISBOV (backend\utils\regras_sisbov.py
#     v1.5.0): DV do modelo antigo, modelo, manejo e geracao de faixa.
#     Nao usa banco nem Flask. Rodar na pasta C:\Orion:
#         python testar_sisbov.py
#     Saida esperada: "TUDO OK" no final (codigo de saida 0).
#     Numeros reais de 3 clientes enviados por Benedito (Sessao 094).
#   v1.0.0: Criacao (Sessao 094).
# =========================================================

import importlib.util
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    'regras_sisbov', os.path.join(AQUI, 'backend', 'utils', 'regras_sisbov.py'))
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)

# --- Cliente 1 (44 numeros de 15 digitos, base + DV juntos)
CLIENTE_1 = """
105500472721057 105500472721065 105500472721073 105500472721081 105500472721090
105500472721103 105500472721111 105500472721120 105500472721138 105500472721146
105500472721154 105500472721413 105500472721421 105500472721430 105500472721448
105500472721456 105500472721464 105500472721472 105500472721480 105500472721499
105500472721502 105500472721510 105500472721529 105500472721537 105500472721545
105500472721553 105500472721561 105500472721570 105500472721588 105500472721596
105500472721600 105500472721618 105500472721626 105500472721634 105500472721642
105500472721650 105500472721669 105500472721677 105500472721685 105500472721693
105500472721707 105500472721715 105500472721723 105500472721731
""".split()

# --- Cliente 2 (13 numeros de teste, base de 14 + DV separado; so provam o DV)
CLIENTE_2 = [
    ('10050032140338', 5), ('10050032140339', 3), ('10050032140340', 7),
    ('10050032140341', 5), ('10050032140342', 3), ('10050032140343', 1),
    ('10050032140344', 0), ('10050032140345', 8), ('10050032140346', 6),
    ('10050032140347', 4), ('10050032140348', 2), ('10050032140349', 0),
    ('10050032140350', 4),
]

# --- Cliente 3 (13 numeros, formato base-DV)
CLIENTE_3 = """
10550050129796-3 10550050129797-1 10550050129798-0 10550050129799-8
10550050129800-5 10550050129801-3 10550050129803-0 10550050129805-6
10550050129806-4 10550050129807-2 10550050129809-9 10550050129810-2
10550050129811-0
""".split()

falhas = []
total = 0


def conferir(nome, obtido, esperado):
    global total
    total += 1
    if obtido != esperado:
        falhas.append(f'{nome}: obtido {obtido!r}, esperado {esperado!r}')


def deve_falhar(nome, funcao, *args):
    global total
    total += 1
    try:
        funcao(*args)
    except ValueError:
        return
    falhas.append(f'{nome}: era para dar erro e nao deu')


# 1. DV dos 70 numeros reais
for n in CLIENTE_1:
    conferir(f'DV cliente 1 {n}', rs.calcular_dv_sisbov(n[:14]), int(n[14]))
    conferir(f'confere cliente 1 {n}', rs.sisbov_confere(n), True)
for base, dv in CLIENTE_2:
    conferir(f'DV cliente 2 {base}', rs.calcular_dv_sisbov(base), dv)
for item in CLIENTE_3:
    base, dv = item.split('-')
    conferir(f'DV cliente 3 {base}', rs.calcular_dv_sisbov(base), int(dv))
    conferir(f'confere cliente 3 {item}', rs.sisbov_confere(base + dv), True)

# 2. DV errado nao passa
conferir('DV errado', rs.sisbov_confere('105500472721058'), False)
conferir('tamanho errado', rs.sisbov_confere('10550047272105'), False)

# 3. Modelo pelo inicio do numero
conferir('modelo 105', rs.modelo_do_sisbov('10550047272105'), 'ANTIGO')
conferir('modelo outro', rs.modelo_do_sisbov('200000000000001'), 'NOVO')
conferir('modelo vazio', rs.modelo_do_sisbov(''), None)

# 4. Manejo: antigo = 6 antes do DV; novo = 6 ultimos
conferir('manejo antigo', rs.manejo_do_sisbov('105500472721057'), '272105')
conferir('manejo antigo 2', rs.manejo_do_sisbov('105500501392001'), '139200')
conferir('manejo novo', rs.manejo_do_sisbov('200000000140338'), '140338')

# 5. Faixa antiga: tela do Maker (inicial ...200 DV 1, final ...299 DV 0, qtde 100)
faixa = rs.gerar_faixa_sisbov('10550050139200', 100)
conferir('faixa antiga qtde', len(faixa), 100)
conferir('faixa antiga primeiro', faixa[0], '105500501392001')
conferir('faixa antiga ultimo', faixa[-1], '105500501392990')
conferir('faixa antiga todos conferem', all(rs.sisbov_confere(x) for x in faixa), True)
conferir('faixa antiga sem repetidos', len(set(faixa)), 100)
# sequencia dos clientes: base ...05 a ...15 do cliente 1
conferir('faixa antiga cliente 1',
         rs.gerar_faixa_sisbov('10550047272105', 11),
         [n for n in CLIENTE_1[:11]])

# 5b. extremos_faixa_sisbov (leve) igual ao primeiro/ultimo da faixa completa
conferir('extremos antigo', rs.extremos_faixa_sisbov('10550050139200', 100),
         ('ANTIGO', '105500501392001', '105500501392990'))
conferir('extremos novo', rs.extremos_faixa_sisbov('200000000000008', 5),
         ('NOVO', '200000000000008', '200000000000012'))
conferir('extremos grande', rs.extremos_faixa_sisbov('10550050139200', 999999)[0], 'ANTIGO')
deve_falhar('extremos erro', rs.extremos_faixa_sisbov, '1055005013920', 5)

# 6. Faixa nova: 15 digitos seguidos, sem DV
faixa = rs.gerar_faixa_sisbov('200000000000008', 5)
conferir('faixa nova', faixa, ['200000000000008', '200000000000009', '200000000000010',
                               '200000000000011', '200000000000012'])

# 7. Erros esperados
deve_falhar('antigo com 15 digitos', rs.gerar_faixa_sisbov, '105500472721057', 10)
deve_falhar('antigo com 13 digitos', rs.gerar_faixa_sisbov, '1055004727210', 10)
deve_falhar('novo com 14 digitos', rs.gerar_faixa_sisbov, '20000000000001', 10)
deve_falhar('letras', rs.gerar_faixa_sisbov, '1055004727210A', 10)
deve_falhar('qtde zero', rs.gerar_faixa_sisbov, '10550047272105', 0)
deve_falhar('qtde texto', rs.gerar_faixa_sisbov, '10550047272105', 'x')
deve_falhar('antigo passa de 14', rs.gerar_faixa_sisbov, '10599999999999', 2)
deve_falhar('novo passa de 15', rs.gerar_faixa_sisbov, '999999999999999', 2)
deve_falhar('novo entra no 105', rs.gerar_faixa_sisbov, '104999999999999', 2)
deve_falhar('base com 13 digitos no DV', rs.calcular_dv_sisbov, '1055004727210')
deve_falhar('manejo com 14 digitos', rs.manejo_do_sisbov, '10550047272105')

# 8. Regras antigas do arquivo continuam intactas
conferir('cota hilton 306', rs.eh_cota_hilton(306), True)
conferir('cota hilton 307', rs.eh_cota_hilton(307), False)
conferir('serie GO', rs.tamanho_serie_gta('GO'), 2)
conferir('serie MG', rs.tamanho_serie_gta('MG'), 1)

print(f'{total} conferencias.')
if falhas:
    print(f'FALHAS: {len(falhas)}')
    for f in falhas:
        print('  -', f)
    sys.exit(1)
print('TUDO OK')

# =========================================================
# FIM DE ARQUIVO: testar_sisbov.py
# =========================================================
