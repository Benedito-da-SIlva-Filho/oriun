# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_blk_8003_envios.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-09 17:35 -03
# ATUALIZADO EM: 2026-10-10 14:30 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Model da tabela tb_blk_8003_envios (BLOCKCHAIN, Sessao 092): uma
#     linha por EVENTO x PROVEDOR. Status: PENDENTE, ENVIANDO (o "carteiro"
#     pegou), CONFIRMADO, ERRO (tenta de novo ate o limite) e CANCELADO (a
#     operacao foi desfeita antes de sair). codigo_retorno = o codigo que o
#     provedor devolveu (hash da transacao, DFID...); url_verificacao = o
#     link de verificacao, quando houver. Tabela POR-PRODUTOR.
#
#     Scripts: Tabelas\12_create_tb_blk_8001_8003_produtor.sql (v1.1.0) e
#     Tabelas\13_alter_tb_blk_8003_status_cancelado.sql.
#
#     v1.0.0: Criacao (Sessao 092, 09/10/2026, 17:35 -03).
#     v1.1.0: Sessao 093 (10/10/2026, 14:30 -03) - O model passa a ter as
#             mesmas travas, indice e valores padrao do script 12 (um envio
#             por evento e provedor; trava de status e de ambiente; indice
#             da fila). POR QUE: o onboarding de Produtor novo cria a tabela
#             a partir deste model; sem isso nasceria mais fraca que a
#             criada pelo script. Nenhuma coluna nova, nenhuma mudanca de
#             comportamento no codigo.
# =========================================================

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    UniqueConstraint, CheckConstraint, Index, text,
)

from .certificadora import Base

STATUS_ENVIO = ('PENDENTE', 'ENVIANDO', 'CONFIRMADO', 'ERRO', 'CANCELADO')


class EnvioBlk(Base):
    __tablename__ = 'tb_blk_8003_envios'
    # Travas e indice (iguais aos do script 12 v1.1.0 + script 13).
    __table_args__ = (
        UniqueConstraint('id_evento', 'id_provedor', name='uq_tb_blk_8003_evento_provedor'),
        CheckConstraint(
            "status IN ('PENDENTE', 'ENVIANDO', 'CONFIRMADO', 'ERRO', 'CANCELADO')",
            name='chk_tb_blk_8003_status',
        ),
        CheckConstraint("ambiente IN ('TESTE', 'PRODUCAO')", name='chk_tb_blk_8003_ambiente'),
        Index('ix_tb_blk_8003_fila', 'status', 'proximo_envio'),
    )

    id              = Column(Integer, primary_key=True)
    id_evento       = Column(Integer, ForeignKey('tb_blk_8002_eventos.id'), nullable=False)
    id_provedor     = Column(Integer, ForeignKey('public.tb_blk_8000_provedores.id'), nullable=False)
    ambiente        = Column(String(10), nullable=False, default='TESTE', server_default=text("'TESTE'"))
    status          = Column(String(12), nullable=False, default='PENDENTE', server_default=text("'PENDENTE'"))
    tentativas      = Column(Integer, nullable=False, default=0, server_default=text('0'))
    proximo_envio   = Column(DateTime, nullable=False, default=datetime.now, server_default=text('now()'))
    codigo_retorno  = Column(String(200))
    url_verificacao = Column(String(500))
    erro            = Column(Text)
    enviado_em      = Column(DateTime)
    confirmado_em   = Column(DateTime)
    criado_em       = Column(DateTime, nullable=False, default=datetime.now, server_default=text('now()'))
    atualizado_em   = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, server_default=text('now()'))

    def __repr__(self):
        return f'<EnvioBlk evento={self.id_evento} provedor={self.id_provedor} {self.status}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_blk_8003_envios.py
# =========================================================
