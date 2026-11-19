# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\blockchain
# MODULO: backend\blockchain\base.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-09 17:35 -03
# ATUALIZADO EM: 2026-10-09 17:35 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     O molde dos conectores de blockchain (Sessao 092).
#
#     Conector.enviar(evento, ambiente) recebe o evento como dicionario e
#     devolve um ResultadoEnvio (codigo + link de verificacao) ou levanta
#     ErroEnvio. O "evento" traz SEMPRE: tipo_evento, sisbov_hash,
#     versao_chave, hash_animal, hash_dono, hash_evento, ocorrido_em e
#     id_evento_anterior. Quando o conector declara aceita_ficha = True, traz
#     tambem ficha_animal (e ficha_dono se o Produtor liberou "envia_dono").
#     Redes PUBLICAS devem ficar com aceita_ficha = False: so os hashes sobem.
#
#     v1.0.0: Criacao (Sessao 092, 09/10/2026, 17:35 -03).
# =========================================================

from dataclasses import dataclass
from typing import Optional


@dataclass
class ResultadoEnvio:
    codigo: str                          # hash da transacao, DFID etc.
    url_verificacao: Optional[str] = None


class ErroEnvio(Exception):
    """Falha no envio. definitivo=True nao adianta tentar de novo."""
    def __init__(self, mensagem, definitivo=False):
        super().__init__(mensagem)
        self.definitivo = definitivo


class Conector:
    codigo = ''                 # codigo do provedor (tb_blk_8000_provedores.codigo)
    aceita_ficha = False        # True so para destino fechado/de teste

    def enviar(self, evento, ambiente):
        raise NotImplementedError

# =========================================================
# FIM DE ARQUIVO: backend\blockchain\base.py
# =========================================================
