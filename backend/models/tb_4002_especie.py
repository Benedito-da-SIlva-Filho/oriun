# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_4002_especie.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-25 09:05 -03
# ATUALIZADO EM: 2026-07-25 09:05 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_4002_especie.
#     Catalogo de Especie (GR4002 do GERAS) - BOV Bovino,
#     BUB Bubalino. Atributo do proprio animal.
#     Schema publico (catalogo compartilhado por todos os
#     Produtores - nao entra nas tabelas do Schema-por-Produtor).
#
#     v1.0.0: Criacao do modulo.
# =========================================================

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model Especie
# Espelha a tabela tb_4002_especie no PostgreSQL
# -------------------------------------------------------
class Especie(Base):
    __tablename__ = 'tb_4002_especie'
    __table_args__ = {'schema': 'public'}

    id              = Column(Integer, primary_key=True)

    # Codigo GERAS (BOV, BUB)
    codigo          = Column(String(3), nullable=False, unique=True)

    # Label para exibicao na tela (dropdown)
    descricao       = Column(String(60), nullable=False)

    # Controle de datas
    criado_em       = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em   = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Especie {self.codigo}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_4002_especie.py
# =========================================================