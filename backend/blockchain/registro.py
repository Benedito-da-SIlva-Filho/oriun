# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\blockchain
# MODULO: backend\blockchain\registro.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-09 17:35 -03
# ATUALIZADO EM: 2026-10-09 17:35 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Registro dos conectores disponiveis (Sessao 092): codigo do provedor
#     (tb_blk_8000_provedores.codigo) -> conector. Provedor SEM conector
#     aqui (hoje: STELLAR_TESTE, POLYGON_TESTE e DEFARM) fica com o envio
#     PENDENTE - o carteiro avisa no log e nao gasta tentativa.
#
#     v1.0.0: Criacao (Sessao 092, 09/10/2026, 17:35 -03). So o SIMULADO.
# =========================================================

from .simulado import ConectorSimulado

CONECTORES = {
    'SIMULADO': ConectorSimulado(),
}

# =========================================================
# FIM DE ARQUIVO: backend\blockchain\registro.py
# =========================================================
