# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_4010_reidentificacao_inconformes.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-11-11 11:40 -03
# ATUALIZADO EM: 2026-11-11 11:40 -03
# VERSAO:       1.0.0
#
# DESCRICAO:
#     Model da tabela tb_4010_reidentificacao_inconformes - tudo que foi recusado na Reidentificacao (brinco perdido fora do rebanho,
#     brinco novo fora do estoque ou ja usado, animal em leitura de saida, brinco repetido...). Uma linha por tentativa recusada.
#     Tabela POR-PRODUTOR (Schema-por-Produtor): sem schema fixo no Model - resolvido em tempo de execucao por get_db_produtor().
#     Guarda o que foi LIDO/DIGITADO (em texto), por isso nao ha FK para o animal. Molde: tb_4008_linkagem_inconformes.
#
#     Script de criacao: Tabelas\criar_reidentificacao_s121.sql.
#
#     v1.0.0: Criacao (Sessao 121, 11/11/2026, 11:40 -03).
# =========================================================

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from .certificadora import Base


class ReidentificacaoInconforme(Base):
    __tablename__ = 'tb_4010_reidentificacao_inconformes'

    id             = Column(Integer, primary_key=True)
    id_propriedade = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    id_usuario     = Column(Integer)
    sisbov_antigo  = Column(String(40))   # brinco perdido, como foi lido/digitado
    sisbov_novo    = Column(String(40))   # brinco que substitui, como foi lido/digitado
    motivo         = Column(String(200), nullable=False)   # texto da recusa
    criado_em      = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<ReidentificacaoInconforme {self.sisbov_antigo} -> {self.sisbov_novo}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_4010_reidentificacao_inconformes.py
# =========================================================
