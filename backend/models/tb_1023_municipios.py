# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_1023_municipios.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-23 12:13 -03
# ATUALIZADO EM: 2026-10-13 19:45 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Model da tabela tb_1023_municipios.
#     Catalogo de Municipios (GR1023 do GERAS) - codigos
#     oficiais IBGE/MAPA. Schema publico (catalogo
#     compartilhado por todos os Produtores).
#
#     Usado nos cadastros de Produtor e Propriedade (campos
#     municipio/uf), substituindo texto livre por referencia
#     a codigo oficial.
#
#     v1.0.0: Criacao do modulo. Seed com 5.566 municipios,
#             fonte GR1023.TXT (export do GERAS).
#     v1.1.0: Sessao 095 (13/10/2026, 19:45 -03) - novas colunas regiao_brasil, mesorregiao e microrregiao (carregadas por importar_regioes_tb_1023.sql).
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model Municipio
# Espelha a tabela tb_1023_municipios no PostgreSQL
# -------------------------------------------------------
class Municipio(Base):
    __tablename__ = 'tb_1023_municipios'
    __table_args__ = {'schema': 'public'}

    id              = Column(Integer, primary_key=True)

    # Codigo oficial IBGE/MAPA (7 digitos)
    codigo_ibge     = Column(String(7), nullable=False, unique=True)

    nome            = Column(String(50), nullable=False)
    uf              = Column(String(2), nullable=False)

    # v-s095 - regioes oficiais do IBGE (carregadas por importar_regioes_tb_1023.sql)
    regiao_brasil   = Column(String(20))
    mesorregiao     = Column(String(100))
    microrregiao    = Column(String(100))

    # Municipio pode ser criado/desmembrado com o tempo -
    # permite inativar sem apagar historico
    ativo           = Column(Boolean, nullable=False, default=True)

    # Controle de datas
    criado_em       = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em   = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Municipio {self.nome}/{self.uf}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_1023_municipios.py
# =========================================================