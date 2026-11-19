# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\blockchain
# MODULO: backend\blockchain\simulado.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-09 17:35 -03
# ATUALIZADO EM: 2026-10-09 17:35 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Conector SIMULADO (Sessao 092): nao sai do Orion. Recebe o evento,
#     devolve um codigo de transacao INVENTADO (SIM- + parte do hash do
#     evento) e confirma. Serve para testar a fila, o carteiro, o reenvio e
#     as telas sem rede, sem carteira e sem custo.
#
#     Para testar falhas, defina no .env a variavel BLK_SIMULADO_FALHA com
#     um numero de 0 a 1 (ex.: 0.5 = metade dos envios falha). Sem a
#     variavel, nunca falha. O codigo devolvido e sempre marcado como
#     "SIM-", para ninguem confundir com um registro de verdade.
#
#     v1.0.0: Criacao (Sessao 092, 09/10/2026, 17:35 -03).
# =========================================================

import os
import random

from .base import Conector, ResultadoEnvio, ErroEnvio


class ConectorSimulado(Conector):
    codigo = 'SIMULADO'
    aceita_ficha = True

    def enviar(self, evento, ambiente):
        try:
            taxa = float(os.getenv('BLK_SIMULADO_FALHA', '0') or 0)
        except ValueError:
            taxa = 0.0
        if taxa > 0 and random.random() < taxa:
            raise ErroEnvio('Falha simulada (BLK_SIMULADO_FALHA).')
        return ResultadoEnvio(codigo='SIM-' + evento['hash_evento'][:32], url_verificacao=None)

# =========================================================
# FIM DE ARQUIVO: backend\blockchain\simulado.py
# =========================================================
