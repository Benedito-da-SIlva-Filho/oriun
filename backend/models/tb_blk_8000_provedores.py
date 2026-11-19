# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_blk_8000_provedores.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-09 17:35 -03
# ATUALIZADO EM: 2026-10-09 17:35 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_blk_8000_provedores (BLOCKCHAIN, Sessao 092): o
#     catalogo dos provedores para onde o Orion pode enviar os eventos dos
#     animais (SIMULADO, STELLAR_TESTE, POLYGON_TESTE, DEFARM...). Vive no
#     schema PUBLIC (igual para todos os Produtores).
#
#     Script de criacao: Tabelas\11_create_tb_blk_8000_provedores.sql.
#
#     v1.0.0: Criacao (Sessao 092, 09/10/2026, 17:35 -03).
# =========================================================

from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime

from .certificadora import Base


class ProvedorBlk(Base):
    __tablename__ = 'tb_blk_8000_provedores'
    __table_args__ = {'schema': 'public'}

    id        = Column(Integer, primary_key=True)
    codigo    = Column(String(30), nullable=False, unique=True)
    nome      = Column(String(80), nullable=False)
    ativo     = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<ProvedorBlk {self.codigo}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_blk_8000_provedores.py
# =========================================================
