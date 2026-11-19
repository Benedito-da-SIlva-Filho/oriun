# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\Orion\
# MODULO: testar_leitor_extrato.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-17 18:09 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Teste do leitor do Extrato de Animais Vivos do MAPA (backend\leitores\leitor_mapa_extrato_vivos.py)
#     contra o arquivo real "EXTRATO DE VIVOS.pdf". Nao usa banco nem Flask. Rodar na pasta C:\Orion:
#         python testar_leitor_extrato.py
#     Saida esperada: "TUDO OK" no final (codigo de saida 0).
#     Tambem mostra (so informativo, nao reprova) quantos SISBOV do arquivo passam na conferencia do DV.
#   v1.0.0: Criacao (Carga, 17/11/2026).
# =========================================================

import importlib.util
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))


def carregar(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, os.path.join(AQUI, *caminho))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


leitor = carregar('leitor_extrato', ('backend', 'leitores', 'leitor_mapa_extrato_vivos.py'))
rs = carregar('regras_sisbov', ('backend', 'utils', 'regras_sisbov.py'))

falhas = []
total = 0


def conferir(nome, obtido, esperado):
    global total
    total += 1
    if obtido != esperado:
        falhas.append(f'{nome}: obtido {obtido!r}, esperado {esperado!r}')


r = leitor.ler(os.path.join(AQUI, 'EXTRATO DE VIVOS.pdf'))
cab, animais = r['cabecalho'], r['animais']

conferir('formato', r['formato'], 'MAPA_EXTRATO_VIVOS')
conferir('total de animais lidos', len(animais), 1244)
conferir('femeas lidas', sum(1 for a in animais if a['sexo'] == 'FEMEA'), 31)
conferir('machos lidos', sum(1 for a in animais if a['sexo'] == 'MACHO'), 1213)
conferir('nenhuma linha nao lida', r['linhas_nao_lidas'], [])
conferir('totais do cabecalho', (cab['total_femea'], cab['total_macho']), (31, 1213))
conferir('totais batem com a lista', (cab['total_femea'] + cab['total_macho']), len(animais))
conferir('paginas', cab['paginas'], 30)
conferir('ultima pagina com animal', animais[-1]['pagina'], 30)
conferir('produtor', cab['produtor_nome'], 'JOSE LUIZ FRAGNAN')
conferir('documento so digitos', cab['produtor_documento'], '00453021972')
conferir('propriedade', cab['propriedade_nome'], 'FAZENDA SÃO JOSÉ')
conferir('nirf', cab['nirf'], '08806306')
conferir('cod propriedade', cab['cod_propriedade'], '32570')
conferir('municipio/uf', (cab['municipio'], cab['uf']), ('ITAQUIRAÍ', 'MS'))
conferir('certificadora', cab['certificadora'], 'QIMA RASTREABILIDADE E CERTIFICACOES LTDA')
conferir('sisbov todos com 15 digitos', all(len(a['sisbov']) == 15 and a['sisbov'].isdecimal() for a in animais), True)
conferir('sem SISBOV repetido no arquivo', len({a['sisbov'] for a in animais}), len(animais))
conferir('todas as datas validas', all(a['nascimento'] and a['data_inclusao'] for a in animais), True)
conferir('primeiro animal', (animais[0]['sisbov'], animais[0]['raca_nome'], animais[0]['sexo'], animais[0]['data_inclusao_texto']),
         ('105500191288651', 'Nelore', 'MACHO', '17/10/2006'))
conferir('raca composta lida', any(a['raca_nome'] == 'Composto' for a in animais), True)

racas = sorted({a['raca_nome'] for a in animais})
dv_ok = sum(1 for a in animais if rs.sisbov_confere(a['sisbov']))
print(f'Racas no arquivo: {racas}')
print(f'SISBOV com DV conferindo: {dv_ok} de {len(animais)}')

if falhas:
    print('FALHAS:')
    for f in falhas:
        print('  -', f)
    sys.exit(1)
print(f'{total} conferencias. TUDO OK')

# =========================================================
# FIM DE ARQUIVO: testar_leitor_extrato.py
# =========================================================
