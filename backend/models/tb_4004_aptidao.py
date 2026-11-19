# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_4004_aptidao.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-25 09:05 -03
# ATUALIZADO EM: 2026-07-25 09:05 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_4004_aptidao.
#     Catalogo de Aptidao do animal (GR4004 do GERAS) -
#     Corte, Leite, Misto, Outro, Precoce, Super Precoce,
#     Vitelo. Registro "AA" do legado (sem descricao)
#     intencionalmente fora do seed - lixo residual.
#     Schema publico (catalogo compartilhado por todos os
#     Produtores - nao entra nas tabelas do Schema-por-Produtor).
#
#     v1.0.0: Criacao do modulo.
# =========================================================

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model Aptidao
# Espelha a tabela tb_4004_aptidao no PostgreSQL
# -------------------------------------------------------
class Aptidao(Base):
    __tablename__ = 'tb_4004_aptidao'
    __table_args__ = {'schema': 'public'}

    id              = Column(Integer, primary_key=True)

    # Codigo GERAS (CR, LT, MS, OT, PC, SP, VT)
    codigo          = Column(String(2), nullable=False, unique=True)

    # Label para exibicao na tela (dropdown)
    descricao       = Column(String(60), nullable=False)

    # Controle de datas
    criado_em       = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em   = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Aptidao {self.codigo}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_4004_aptidao.py
# =========================================================