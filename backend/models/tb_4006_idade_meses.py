# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_4006_idade_meses.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-07 19:50 -03
# ATUALIZADO EM: 2026-09-07 20:20 -03
# VERSAO: 1.2.0
#
# DESCRICAO:
#     Model da tabela tb_4006_idade_meses (nome corrigido - v1.0.0
#     deste model usava o nome errado tb_4006_idade_em_meses,
#     causando ERROR: relation does not exist; nome real confirmado
#     via pg_tables) - catalogo PUBLICO (compartilhado entre todos
#     os Produtores, __table_args__ com schema='public') das 5
#     faixas etarias oficiais usadas na GTA, com o intervalo de
#     dias correspondente (fonte: GR4006.TXT, export real do GERAS)
#     e o ponto medio ja calculado (dias_medio, coluna NOVA desta
#     sessao) - usado por tb_2001.eras_dias.
#
#     JA EXISTIA populada desde 25/07/2026 (7 colunas reais: id,
#     sequencia, descricao, dias_min, dias_max, criado_em,
#     atualizado_em) - so a coluna dias_medio precisou ser
#     adicionada via ALTER TABLE (ver Tabelas\alterar_tb_4006_
#     dias_medio.sql).
#
#     dias_medio da ultima faixa (+36 Meses, sem teto real - dias_max
#     e um valor simbolico de "sem limite", 9999) NAO e a media
#     aritmetica do intervalo - e um valor fixo de 1200 dias (= 40
#     meses x 30 dias), decisao de Benedito (Sessao 047): "acima de
#     36 meses vamos estimar 40 meses fixo".
#
#     `descricao` grava o texto OFICIAL da fonte (GR4006.TXT), com
#     eventuais espacos duplos do export original NORMALIZADOS para
#     espaco simples (ex.: "04 a 12 Meses", nao "04  a 12 Meses") -
#     mas qualquer comparacao/busca por este campo em outros
#     modulos deve normalizar espacos multiplos antes de comparar,
#     ja que a GTA ou outras telas podem gravar variacoes de
#     formatacao (ex.: "+36 Meses" sem espaco vs "+ 36 Meses" com
#     espaco) - combinado com Benedito, Sessao 047.
#
#     v1.0.0: Criacao do modulo (Sessao 047) - nome de tabela ERRADO
#             (tb_4006_idade_em_meses).
#     v1.1.0: Sessao 047 (07/09/2026, 20:10 -03) - CORRECAO: nome
#             real confirmado via pg_tables = tb_4006_idade_meses.
#             Nome de coluna ainda ERRADO (sequencia).
#     v1.2.0: Sessao 047 (07/09/2026, 20:20 -03) - CORRECAO: coluna
#             real (via information_schema.columns) = codigo_geras,
#             nao "sequencia".
# =========================================================

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model IdadeMeses
# Espelha a tabela tb_4006_idade_meses no PostgreSQL (schema public)
# -------------------------------------------------------
class IdadeMeses(Base):
    __tablename__ = 'tb_4006_idade_meses'
    __table_args__ = {'schema': 'public'}

    id              = Column(Integer, primary_key=True)
    codigo_geras    = Column(Integer, nullable=False, unique=True)  # ordem oficial (1 a 5, mesma numeração do GERAS)
    descricao       = Column(String(20), nullable=False)  # ex: "04 a 12 Meses"
    dias_min        = Column(Integer, nullable=False)
    dias_max        = Column(Integer, nullable=False)
    dias_medio      = Column(Integer, nullable=False)  # ponto medio - ver DESCRICAO sobre a ultima faixa
    criado_em       = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em   = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<IdadeMeses {self.descricao} ({self.dias_min}-{self.dias_max}d)>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_4006_idade_meses.py
# =========================================================