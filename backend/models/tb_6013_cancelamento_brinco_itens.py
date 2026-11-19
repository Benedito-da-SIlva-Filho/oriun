# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_6013_cancelamento_brinco_itens.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-25 13:42 -03
# ATUALIZADO EM: 2026-07-25 13:42 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_6013_cancelamento_brinco_itens.
#     Detalhe do pedido de Cancelamento de Brinco (origem GR6013
#     do GERAS) - uma linha por brinco cancelado.
#
#     Vive no SCHEMA DO PRODUTOR, mesmo schema fisico da tabela
#     cabecalho (tb_6012) - a FK id_pedido nao leva prefixo de
#     schema.
#
#     SEM RFID - confirmado por Benedito: o brinco quebrou/
#     danificou ANTES de ser aplicado no animal, entao nunca
#     chegou a ter um RFID associado. Mesma ausencia de campo ja
#     aplicada em tb_6008_perda_saida_estoque_itens, mas por
#     motivo de negocio diferente (la o animal nunca teve
#     identificacao; aqui o brinco nunca foi usado).
#
#     codigo_sisbov (VARCHAR(15)): SISBOV + digito verificador
#     numa unica coluna de 15 digitos - mesma regra ja fechada em
#     todo o sistema, mesmo o legado guardando em colunas
#     separadas (SISBOV + Dv).
#
#     v1.0.0: Criacao do modulo.
# =========================================================

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model CancelamentoBrincoItem
# Espelha a tabela tb_6013_cancelamento_brinco_itens no PostgreSQL
# -------------------------------------------------------
class CancelamentoBrincoItem(Base):
    __tablename__ = 'tb_6013_cancelamento_brinco_itens'

    id                  = Column(Integer, primary_key=True)

    # Vinculo obrigatorio com o cabecalho do pedido. Sem prefixo
    # de schema - tb_6012 mora no mesmo schema do Produtor.
    id_pedido           = Column(Integer, ForeignKey('tb_6012_cancelamento_brinco.id'), nullable=False)
    pedido              = relationship('CancelamentoBrinco', foreign_keys=[id_pedido], backref='itens')

    # SISBOV + DV numa unica coluna (15 digitos). Sem RFID - o
    # brinco nunca chegou a ser aplicado no animal.
    codigo_sisbov       = Column(String(15), nullable=False)

    # Controle de datas
    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em       = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<CancelamentoBrincoItem sisbov={self.codigo_sisbov}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_6013_cancelamento_brinco_itens.py
# =========================================================