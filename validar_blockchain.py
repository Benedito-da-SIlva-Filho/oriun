# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion
# MODULO: validar_blockchain.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-09 18:50 -03
# ATUALIZADO EM: 2026-10-10 18:00 -03
# VERSAO: 1.2.0
#
# DESCRICAO:
#     VALIDADOR do blockchain do Orion pelo TERMINAL (Sessao 092): confere a
#     fila de eventos e envios de cada Produtor e diz "tudo OK" ou aponta o
#     que esta errado. Nao envia nem cancela nada; a unica coisa que grava e
#     a marca "conferido" nos eventos que passaram em tudo (so confere o que
#     ainda nao foi conferido). Pode rodar a qualquer hora, com o Orion e o
#     carteiro ligados.
#
#     As conferencias em si moram em backend\utils\validador_blockchain.py
#     (a mesma "receita" usada pela tela Consiste > Blockchain). Este arquivo
#     so le os parametros, chama a receita e imprime.
#
#     COMO RODAR (na pasta C:\orion, mesmo ambiente do Orion):
#         python validar_blockchain.py                  - todos os Produtores
#         python validar_blockchain.py --produtor 4     - so o produtor_00004
#         python validar_blockchain.py --tipo TROCA_RFID - so um tipo de evento
#         python validar_blockchain.py --so-problemas   - mostra so ATENCAO/FALHA
#         python validar_blockchain.py --salvar         - grava o relatorio em
#                                                          .txt (comprovante)
#         python validar_blockchain.py --tudo           - reconfere TAMBEM os
#                                                          ja conferidos antes
#         python validar_blockchain.py --nao-marcar     - confere sem gravar a
#                                                          marca (so leitura)
#
#     RESULTADO: [OK], [ATENCAO] (olhar, mas pode ser normal) ou [FALHA]
#     (algo esta errado). Se houver qualquer FALHA, o script termina com
#     codigo 1 (tipo de evento invalido ou nenhum Produtor: codigo 2).
#
#     v1.0.0: Criacao (Sessao 092, 09/10/2026, 18:50 -03).
#     v1.1.0: Sessao 092 (09/10/2026, 18:58 -03) - As conferencias foram para
#         backend\utils\validador_blockchain.py (receita unica, usada tambem
#         pela tela Consiste > Blockchain). Este script ficou so com a linha
#         de comando. Mesmos parametros e mesmo resultado de antes.
#     v1.2.0: Sessao 093 (10/10/2026, 18:00 -03) - Entrega 2: por padrao so
#         confere os eventos ainda nao conferidos e marca os que passaram em
#         tudo. Novas opcoes --tudo (reconfere tudo) e --nao-marcar (so
#         leitura, como antes da v1.2.0).
# =========================================================

import argparse
import sys
from datetime import datetime

from backend.utils import blockchain as B
from backend.utils import validador_blockchain as V


def main():
    ap = argparse.ArgumentParser(description='Validador do blockchain do Orion (so le o banco).')
    ap.add_argument('--produtor', type=int, help='numero do Produtor (ex.: 4 = produtor_00004)')
    ap.add_argument('--tipo', help='so um tipo de evento (ex.: TROCA_RFID)')
    ap.add_argument('--so-problemas', action='store_true', help='mostra so ATENCAO e FALHA')
    ap.add_argument('--salvar', action='store_true', help='grava o relatorio em arquivo .txt')
    ap.add_argument('--tudo', action='store_true', help='reconfere tambem os eventos ja conferidos antes')
    ap.add_argument('--nao-marcar', action='store_true', help='confere sem gravar a marca de conferido')
    args = ap.parse_args()

    tipo = args.tipo.upper() if args.tipo else None
    if tipo and tipo not in B.TIPOS_EVENTO:
        print(f'Tipo "{tipo}" nao existe. Tipos validos: {", ".join(B.TIPOS_EVENTO)}')
        return 2

    inicio = datetime.now()
    marcar = not args.nao_marcar
    resultados = V.validar(id_produtor=args.produtor, tipo=tipo, tudo=args.tudo, marcar=marcar)
    if not resultados:
        print('Nenhum Produtor encontrado.')
        return 2

    texto = V.formatar_texto(resultados, tipo=tipo, so_problemas=args.so_problemas, quando=inicio,
                             tudo=args.tudo, marcar=marcar)
    print(texto)

    if args.salvar:
        nome = f'validacao_blockchain_{inicio:%Y%m%d_%H%M}.txt'
        with open(nome, 'w', encoding='utf-8', newline='\r\n') as arq:
            arq.write(texto + '\n')
        print(f'\nRelatorio salvo em {nome}')

    return 1 if V.somar(resultados)['FALHA'] else 0


if __name__ == '__main__':
    sys.exit(main())

# =========================================================
# FIM DE ARQUIVO: validar_blockchain.py
# =========================================================
