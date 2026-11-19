# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\protocolo.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-03 15:53 -03
# ATUALIZADO EM: 2026-07-03 15:53 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela protocolos.
#     Catalogo administravel de protocolos/selos de
#     certificacao (ex: ABPO, PEFB, CSCB, Cota Hilton).
#     Novos protocolos entram por tela de administracao
#     (Configuracoes > Protocolos), sem necessidade de
#     alterar SQL ou codigo manualmente.
#
#     v1.0.0: Criacao do modulo (Sessao 011), com base no
#             esquema criado no script
#             001_criacao_tabelas_protocolos.sql.
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model Protocolo
# Espelha a tabela protocolos no PostgreSQL
# -------------------------------------------------------
class Protocolo(Base):
    __tablename__ = 'protocolos'

    # Identificacao e dados principais
    id            = Column(Integer, primary_key=True)
    codigo        = Column(String(20), nullable=False, unique=True)   # ex: PEFB
    nome          = Column(String(150), nullable=False)
    resumo        = Column(String(200), nullable=False)   # 1-2 linhas, para listagem/card
    descricao     = Column(Text)   # texto completo, exibido ao detalhar

    # tipo_vinculo: 'propriedade' (ex: ABPO, PEFB, Cota Hilton) ou
    # 'planta_industrial' (ex: CSCB / curtume)
    tipo_vinculo  = Column(String(20), nullable=False)
    ativo         = Column(Boolean, nullable=False, default=True)

    # Controle de datas
    criado_em     = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Protocolo {self.codigo} - {self.nome}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\protocolo.py
# =========================================================