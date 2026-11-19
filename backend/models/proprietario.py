# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\proprietario.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-02 13:43 -03
# ATUALIZADO EM: 2026-07-17 17:58
# VERSAO: 1.0.0 changelog:
#
# DESCRICAO:
#     Model da tabela proprietarios.
#     Representa o dono legal da terra (proprietario do
#     imovel), sempre uma entidade separada do Produtor
#     (quem opera o rebanho). Um Proprietario pode se
#     repetir em varias Propriedades (via tabela de
#     vinculo propriedade_proprietario). Pode tambem ser,
#     ao mesmo tempo, um Produtor (mesma pessoa/CPF-CNPJ
#     em dois papeis diferentes no sistema).
#
#     v1.0.0: Criacao do modulo (Sessao 010), com base no
#             esquema real da tabela criada na Sessao 009
#             (21 colunas, conferidas direto no banco).
#     v1.1.0: Sessao 019 - Adicionado __table_args__ com schema
#             'public' explicito. Motivo: propriedade_proprietario.py
#             referencia esta tabela via ForeignKey('public.proprietarios.id')
#             - sem essa marcacao aqui, o SQLAlchemy registra a
#             tabela internamente so como 'proprietarios' (sem
#             prefixo), e nao consegue casar a FK, mesmo apontando
#             fisicamente para o lugar certo.
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model Proprietario
# Espelha a tabela proprietarios no PostgreSQL
# -------------------------------------------------------
class Proprietario(Base):
    __tablename__ = 'proprietarios'
    __table_args__ = {'schema': 'public'}

    # Identificacao
    id             = Column(Integer, primary_key=True)
    nome           = Column(String(150), nullable=False)
    razao_social   = Column(String(150), nullable=False)
    cpf_cnpj       = Column(String(18), nullable=False)
    tipo_pessoa    = Column(String(10), nullable=False)   # FISICA / JURIDICA
    visibilidade   = Column(String(10), nullable=False)   # controle de exibicao (P-011)

    # Contato
    email          = Column(String(150), nullable=False)
    telefone       = Column(String(20), nullable=False)
    telefone2      = Column(String(20))

    # Endereco detalhado
    logradouro     = Column(String(200))
    numero         = Column(String(10))
    complemento    = Column(String(100))
    bairro         = Column(String(100))
    cep            = Column(String(9))
    municipio      = Column(String(100), nullable=False)
    uf             = Column(String(2), nullable=False)

    # Localizacao geografica
    latitude       = Column(Numeric(10, 7))
    longitude      = Column(Numeric(10, 7))

    # Controle
    ativo          = Column(Boolean, nullable=False, default=True)
    criado_em      = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em  = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Proprietario {self.nome}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\proprietario.py
# =========================================================
