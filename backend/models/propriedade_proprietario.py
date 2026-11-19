# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\propriedade_proprietario.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-02 13:43 -03
# ATUALIZADO EM: 2026-07-17 17:46
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela propriedade_proprietario.
#     Tabela de vinculo N:N entre Propriedade e
#     Proprietario - trata apenas da titularidade legal
#     da terra, sem dados de operacao/rastreabilidade
#     (isso fica em propriedade_produtor). Sem campo
#     "principal": essa distincao nao se aplica ao
#     Proprietario, que nao gerencia animais nem possui
#     inventario proprio.
#
#     v1.0.0: Criacao do modulo (Sessao 010), com base no
#             esquema real da tabela (nova, criada na
#             Sessao 009), conferido direto no banco.
#     vX.X.0: Sessao 019 - Corrigida FK id_propriedade para
#            'public.propriedades.id' (com prefixo de schema
#            explicito). Motivo: apos propriedade.py v2.2.0
#
#            marcar __table_args__ = {'schema': 'public'},
#            referencias sem o prefixo deixaram de encontrar a
#            tabela propriedades, ao SQLAlchemy configurar todos
#            os mappers do sistema no boot do servidor Flask.
#
# =========================================================

from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model PropriedadeProprietario
# Espelha a tabela propriedade_proprietario no PostgreSQL
# -------------------------------------------------------
class PropriedadeProprietario(Base):
    __tablename__ = 'propriedade_proprietario'

    # Identificacao e vinculo
    id              = Column(Integer, primary_key=True)
    id_propriedade  = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    id_proprietario = Column(Integer, ForeignKey('public.proprietarios.id'), nullable=False)

    # Vigencia da titularidade
    data_inicio     = Column(Date, nullable=False)
    data_fim        = Column(Date)   # nulo = titularidade ativa

    # Relacionamentos
    propriedade     = relationship('Propriedade', backref='vinculos_proprietario')
    proprietario     = relationship('Proprietario', backref='vinculos_propriedade')

    # Controle de datas
    criado_em       = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em   = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<PropriedadeProprietario propriedade={self.id_propriedade} proprietario={self.id_proprietario}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\propriedade_proprietario.py
# =========================================================