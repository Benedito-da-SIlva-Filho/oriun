# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_4013_tipos_identificacao.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-25 09:05 -03
# ATUALIZADO EM: 2026-07-25 09:05 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_4013_tipos_identificacao.
#     Catalogo de Tipos de Identificacao (GR4013 do GERAS) -
#     Simples/Dupla combinada com Botton/Tatuagem/Marca a
#     Fogo/Chip Eletronico. Atributo do proprio animal.
#     Schema publico (catalogo compartilhado por todos os
#     Produtores - nao entra nas tabelas do Schema-por-Produtor).
#
#     v1.0.0: Criacao do modulo.
# =========================================================

from sqlalchemy import Column, Integer, SmallInteger, String, DateTime
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model TipoIdentificacao
# Espelha a tabela tb_4013_tipos_identificacao no PostgreSQL
# -------------------------------------------------------
class TipoIdentificacao(Base):
    __tablename__ = 'tb_4013_tipos_identificacao'
    __table_args__ = {'schema': 'public'}

    id              = Column(Integer, primary_key=True)

    # Codigo sequencial do GERAS (1 a 5)
    codigo_geras    = Column(SmallInteger, nullable=False, unique=True)

    # Label para exibicao na tela (dropdown)
    descricao       = Column(String(100), nullable=False)

    # Controle de datas
    criado_em       = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em   = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<TipoIdentificacao {self.codigo_geras}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_4013_tipos_identificacao.py
# =========================================================