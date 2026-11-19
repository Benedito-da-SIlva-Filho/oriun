# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\certificadora.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-06-21 09:41 -03
# ATUALIZADO EM: 2026-06-23 15:10 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Model da tabela certificadoras.
#     Representa as certificadoras credenciadas pelo MAPA.
#     Tambem armazena configuracoes do White Label.
#     v1.0.0: Criacao do modulo.
#     v1.1.0: Campo nome renomeado para razao_social.
#             Campo nome_fantasia adicionado.
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Certificadora(Base):
    __tablename__ = 'certificadoras'

    # Identificacao
    id             = Column(Integer, primary_key=True)
    razao_social   = Column(String(100), nullable=False)
    nome_fantasia  = Column(String(100))
    cnpj           = Column(String(18), nullable=False, unique=True)
    inscricao_est  = Column(String(20))

    # Endereco
    endereco       = Column(String(200))
    cidade         = Column(String(100))
    uf             = Column(String(2))
    cep            = Column(String(9))
    telefone       = Column(String(20))
    email          = Column(String(100))

    # White Label
    logo           = Column(String(200))
    cor_primaria   = Column(String(7), default='#1F4E79')
    cor_secundaria = Column(String(7), default='#2E75B6')
    dominio        = Column(String(100))

    # Controle
    ativo          = Column(Boolean, default=True)
    criado_em      = Column(DateTime, default=datetime.now)
    atualizado_em  = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Certificadora {self.razao_social}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\certificadora.py
# =========================================================