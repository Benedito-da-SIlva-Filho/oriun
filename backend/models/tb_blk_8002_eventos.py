# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_blk_8002_eventos.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-09 17:35 -03
# ATUALIZADO EM: 2026-10-10 14:30 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Model da tabela tb_blk_8002_eventos (BLOCKCHAIN, Sessao 092): a FILA.
#     Cada linha e um fato do animal (tipo_evento), com o SISBOV so como
#     hash (HMAC com a chave da Consiste, versao em versao_chave), a COPIA
#     CONGELADA da ficha (animal e dono, em JSON) e os hashes de cada bloco
#     e do evento. Correcao/Desfazer = evento NOVO apontando para o anterior
#     (id_evento_anterior). id_operacao liga ao Log de Operacoes, SEM
#     ForeignKey de proposito (mesmo padrao de numero_comunicado). Tabela
#     POR-PRODUTOR (Schema-por-Produtor).
#
#     Script de criacao: Tabelas\12_create_tb_blk_8001_8003_produtor.sql.
#
#     v1.0.0: Criacao (Sessao 092, 09/10/2026, 17:35 -03).
#     v1.1.0: Sessao 093 (10/10/2026, 14:30 -03) - (1) Coluna NOVA
#             conferido_em (marca de "ja conferido pelo validador"; vazio =
#             ainda nao conferido; o uso entra na Entrega 2 do validador).
#             Script: Tabelas\14_alter_blk_conferido_versao2.sql. (2) O
#             model passa a ter os mesmos indices e valores padrao do
#             script 12. POR QUE: o onboarding de Produtor novo cria a
#             tabela a partir deste model; sem isso nasceria mais fraca
#             que a criada pelo script.
# =========================================================

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import JSONB

from .certificadora import Base


class EventoBlk(Base):
    __tablename__ = 'tb_blk_8002_eventos'
    # Indices de consulta (iguais aos do script 12).
    __table_args__ = (
        Index('ix_tb_blk_8002_sisbov_hash', 'sisbov_hash', 'ocorrido_em'),
        Index('ix_tb_blk_8002_propriedade', 'id_propriedade', 'ocorrido_em'),
    )

    id                 = Column(Integer, primary_key=True)
    id_propriedade     = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    tipo_evento        = Column(String(30), nullable=False)
    sisbov_hash        = Column(String(64), nullable=False)
    versao_chave       = Column(Integer, nullable=False, default=1, server_default=text('1'))
    ficha_animal       = Column(JSONB, nullable=False)
    ficha_dono         = Column(JSONB)
    hash_animal        = Column(String(64), nullable=False)
    hash_dono          = Column(String(64))
    hash_evento        = Column(String(64), nullable=False)
    id_evento_anterior = Column(Integer, ForeignKey('tb_blk_8002_eventos.id'))
    id_operacao        = Column(Integer)          # SEM ForeignKey de proposito
    id_usuario         = Column(Integer, ForeignKey('public.usuarios.id'))
    ocorrido_em        = Column(DateTime, nullable=False)
    criado_em          = Column(DateTime, nullable=False, default=datetime.now, server_default=text('now()'))
    # NOVO v1.1.0: quando o validador conferiu este evento (vazio = ainda nao).
    conferido_em       = Column(DateTime)

    def __repr__(self):
        return f'<EventoBlk {self.id} {self.tipo_evento}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_blk_8002_eventos.py
# =========================================================
