# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_log_operacoes_itens.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-03 15:30 -03
# ATUALIZADO EM: 2026-09-03 15:30 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_log_operacoes_itens - o "detalhe" de
#     cada mudanca dentro de uma operacao registrada em
#     tb_log_operacoes (ver esse model para o contexto geral do
#     mecanismo "Desfazer por Operacao", Sessao 045).
#
#     Vive dentro do schema do Produtor, mesma logica das demais
#     tabelas de movimento.
#
#     Cada linha aqui representa 1 mudanca em 1 linha de 1
#     tabela: tabela (nome), id_registro (qual linha), tipo_mudanca
#     ('INSERT' ou 'UPDATE'), dados_antes/dados_depois (JSONB,
#     so os campos que realmente mudaram - nao a linha inteira).
#
#     Para tipo_mudanca='INSERT': dados_antes fica NULO (a linha
#     nao existia antes) - desfazer = DELETE dessa linha.
#     Para tipo_mudanca='UPDATE': dados_antes tem os valores de
#     antes dos campos mudados - desfazer = UPDATE devolvendo
#     esses valores, SE o valor atual ainda bater com
#     dados_depois (senao, bloqueia - algo mexeu depois).
#
#     A leitura/gravacao generica dessas colunas (via reflexao de
#     tabela do SQLAlchemy, nao Models especificos) e o que torna
#     o mecanismo reaproveitavel por qualquer modulo, sem cada um
#     precisar escrever sua propria logica de desfazer - ver
#     backend/utils/log_operacoes.py.
#
#     v1.0.0: Criacao do modulo (Sessao 045, 03/09/2026, 15:30 -03).
# =========================================================

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from .certificadora import Base


# -------------------------------------------------------
# Model LogOperacaoItem
# Espelha a tabela tb_log_operacoes_itens no PostgreSQL
# -------------------------------------------------------
class LogOperacaoItem(Base):
    __tablename__ = 'tb_log_operacoes_itens'

    id             = Column(Integer, primary_key=True)

    # FK para o "recibo" (tb_log_operacoes) - forca o nome da
    # tabela explicitamente pois este model nao usa schema.SCHEMA
    # fixo (vive dentro do schema do Produtor, resolvido em tempo
    # de execucao pelo get_db_produtor).
    id_operacao    = Column(Integer, ForeignKey('tb_log_operacoes.id'), nullable=False)

    # Nome real da tabela mexida (ex.: 'tb_7017_entrada_brincos_rfid')
    tabela         = Column(String(60), nullable=False)

    # PK da linha mexida naquela tabela
    id_registro    = Column(Integer, nullable=False)

    # 'INSERT' ou 'UPDATE' - define a estrategia de desfazer
    tipo_mudanca   = Column(String(10), nullable=False)

    # So os campos que mudaram, nao a linha inteira. NULO em
    # dados_antes quando tipo_mudanca='INSERT' (nao existia antes).
    dados_antes    = Column(JSONB)
    dados_depois   = Column(JSONB)

    def __repr__(self):
        return f'<LogOperacaoItem {self.tabela}#{self.id_registro} ({self.tipo_mudanca})>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_log_operacoes_itens.py
# =========================================================