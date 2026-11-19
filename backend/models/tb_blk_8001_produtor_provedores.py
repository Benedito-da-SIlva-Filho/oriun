# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_blk_8001_produtor_provedores.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-09 17:35 -03
# ATUALIZADO EM: 2026-10-10 14:30 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Model da tabela tb_blk_8001_produtor_provedores (BLOCKCHAIN, Sessao
#     092): quais provedores estao LIGADOS para este Produtor. Sem linha
#     ativa aqui, o Produtor nao gera nenhum evento de blockchain (nenhum
#     peso extra). ambiente = TESTE ou PRODUCAO; envia_dono = se o bloco do
#     dono tambem vai para o provedor (padrao NAO). Tabela POR-PRODUTOR
#     (Schema-por-Produtor): sem schema fixo - resolvido por
#     get_db_produtor().
#
#     Script de criacao: Tabelas\12_create_tb_blk_8001_8003_produtor.sql.
#
#     v1.0.0: Criacao (Sessao 092, 09/10/2026, 17:35 -03).
#     v1.1.0: Sessao 093 (10/10/2026, 14:30 -03) - O model passa a ter as
#             mesmas travas e valores padrao do script 12 (trava de
#             ambiente TESTE/PRODUCAO e valores padrao no banco). POR QUE:
#             o onboarding de Produtor novo cria a tabela a partir deste
#             model; sem isso a tabela nasceria mais fraca que a criada
#             pelo script. Nenhuma coluna nova, nenhuma mudanca de
#             comportamento no codigo.
# =========================================================

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey,
    CheckConstraint, text,
)

from .certificadora import Base


class ProdutorProvedorBlk(Base):
    __tablename__ = 'tb_blk_8001_produtor_provedores'
    # Trava de ambiente (igual ao script 12): so TESTE ou PRODUCAO.
    __table_args__ = (
        CheckConstraint("ambiente IN ('TESTE', 'PRODUCAO')", name='chk_tb_blk_8001_ambiente'),
    )

    id            = Column(Integer, primary_key=True)
    id_provedor   = Column(Integer, ForeignKey('public.tb_blk_8000_provedores.id'), nullable=False, unique=True)
    ativo         = Column(Boolean, nullable=False, default=True, server_default=text('true'))
    ambiente      = Column(String(10), nullable=False, default='TESTE', server_default=text("'TESTE'"))
    envia_dono    = Column(Boolean, nullable=False, default=False, server_default=text('false'))
    criado_em     = Column(DateTime, nullable=False, default=datetime.now, server_default=text('now()'))
    atualizado_em = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, server_default=text('now()'))

    def __repr__(self):
        return f'<ProdutorProvedorBlk provedor={self.id_provedor} {self.ambiente}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_blk_8001_produtor_provedores.py
# =========================================================
