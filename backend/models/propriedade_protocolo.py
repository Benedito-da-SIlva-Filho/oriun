# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\propriedade_protocolo.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-03 15:53 -03
# ATUALIZADO EM: 2026-07-17 17:51
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela propriedade_protocolo.
#     Vinculo entre Propriedade e Protocolo, com historico
#     de ativacao/desativacao. Uma Propriedade pode ter
#     varios protocolos ativos ao mesmo tempo (ex: ABPO +
#     PEFB + Cota Hilton simultaneamente) - a unica regra e
#     nao poder ter dois vinculos ATIVOS do mesmo protocolo
#     para a mesma Propriedade (garantido por indice unico
#     parcial no banco, WHERE status = 'ativo').
#
#     Ativacao e por autodeclaracao do Produtor, direto no
#     cadastro da Propriedade. data_ativacao e o marco
#     temporal: historico do protocolo so conta a partir
#     dali. Desativacao pode ser voluntaria (Produtor
#     desistiu) ou compulsoria (irregularidade constatada
#     por entidade externa).
#
#     v1.0.0: Criacao do modulo (Sessao 011), com base no
#             esquema criado no script
#             001_criacao_tabelas_protocolos.sql.
#
#		 vX.X.0: Sessao 019 - Corrigida FK id_propriedade para
#					 'public.propriedades.id' (com prefixo de schema
#					 explicito). Motivo: apos propriedade.py v2.2.0
#					 marcar __table_args__ = {'schema': 'public'},
#					 referencias sem o prefixo deixaram de encontrar a
#					 tabela propriedades, ao SQLAlchemy configurar todos
#					 os mappers do sistema no boot do servidor Flask.
#
#
# =========================================================

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base

# -------------------------------------------------------
# Model PropriedadeProtocolo
# Espelha a tabela propriedade_protocolo no PostgreSQL
# -------------------------------------------------------
class PropriedadeProtocolo(Base):
    __tablename__ = 'propriedade_protocolo'

    # Identificacao e vinculo
    id                     = Column(Integer, primary_key=True)
    id_propriedade         = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    id_protocolo           = Column(Integer, ForeignKey('protocolos.id'), nullable=False)

    # Ativacao (marco temporal do historico)
    data_ativacao          = Column(Date, nullable=False, default=datetime.now)
    status                 = Column(String(10), nullable=False, default='ativo')

    # Desativacao (preenchidos so quando status = inativo)
    # motivo_inativacao: 'voluntaria' ou 'compulsoria'
    motivo_inativacao      = Column(String(15))
    observacao_inativacao  = Column(Text)
    data_desativacao       = Column(Date)

    # Relacionamentos
    propriedade            = relationship('Propriedade', backref='protocolos_vinculados')
    protocolo               = relationship('Protocolo', backref='vinculos_propriedade')

    # Controle de datas
    criado_em              = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em          = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<PropriedadeProtocolo propriedade={self.id_propriedade} protocolo={self.id_protocolo} status={self.status}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\propriedade_protocolo.py
# =========================================================