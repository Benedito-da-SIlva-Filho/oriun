# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\produtor.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-06-21 09:41 -03
# ATUALIZADO EM: 2026-07-16 16:20 -03
# VERSAO: 2.1.0
#
# DESCRICAO:
#     Model da tabela produtores.
#     Representa o Produtor rural (quem opera o rebanho).
#     Um Produtor pode ter varias Propriedades (proprias,
#     arrendadas ou alugadas) via tabela de vinculo
#     propriedade_produtor. Pode tambem ser, ao mesmo
#     tempo, o Proprietario de uma ou mais dessas terras
#     (id_proprietario aponta para esse caso; fica nulo
#     quando o Produtor e apenas arrendatario).
#
#     v1.0.0: Criacao do modulo (pre-Sessao 009).
#     v2.0.0: Sessao 010 - Reescrita completa para bater
#             com o esquema real do banco pos Sessao 009
#             (25 colunas, conferidas direto no banco).
#             - Campos cpf/cnpj separados substituidos por
#               cpf_cnpj unico + tipo_pessoa
#             - Campo regime_uso removido (duplicava
#               propriedade_produtor.tipo_vinculo)
#             - Adicionados: razao_social, visibilidade,
#               telefone2, endereco detalhado (logradouro/
#               numero/complemento/bairro/cep/municipio/uf),
#               latitude, longitude, id_proprietario,
#               ativo_alterado_em, id_usuario_alteracao_status
#     v2.1.0: Sessao 018 - Adicionado schema_nome (mecanismo
#             Schema-por-Produtor, multi-tenant). Guarda o
#             nome do schema Postgres exclusivo deste Produtor
#             (ex.: produtor_00042), gerado a partir da PK.
#             Fica NULL ate o Produtor passar pela rotina de
#             onboarding. Coluna ja existe no banco (SQL
#             executado em 16/07/2026); esta versao so
#             mapeia ela aqui no Model.
#
#	 v2.2.0: Sessao 019 - Adicionado __table_args__ com schema
#	             'public' explicito. Motivo: sem essa marcacao, a
#	             rotina de Onboarding (schema_translate_map) "sequestrava"
#	             esta tabela para dentro do schema do Produtor sendo
#	             criado, ao montar a FK de tb_parceiros.id_produtor -
#	             causava erro real (UndefinedTable) na primeira execucao
#	             de producao (teste com Produtor id=1).
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model Produtor
# Espelha a tabela produtores no PostgreSQL
# -------------------------------------------------------
class Produtor(Base):
    __tablename__ = 'produtores'
    __table_args__ = {'schema': 'public'}

    # Identificacao
    id              = Column(Integer, primary_key=True)
    nome            = Column(String(150), nullable=False)
    razao_social    = Column(String(150), nullable=False)
    cpf_cnpj        = Column(String(18), nullable=False)
    tipo_pessoa     = Column(String(10), nullable=False)   # FISICA / JURIDICA
    visibilidade    = Column(String(10), nullable=False)   # controle de exibicao (P-011)

    # Contato
    email           = Column(String(150), nullable=False)
    telefone        = Column(String(20), nullable=False)
    telefone2       = Column(String(20))

    # Endereco detalhado
    logradouro      = Column(String(200))
    numero          = Column(String(10))
    complemento     = Column(String(100))
    bairro          = Column(String(100))
    cep             = Column(String(9))
    municipio       = Column(String(100), nullable=False)
    uf              = Column(String(2), nullable=False)

    # Localizacao geografica
    latitude        = Column(Numeric(10, 7))
    longitude       = Column(Numeric(10, 7))

    # Vinculo opcional: preenchido quando o proprio Produtor
    # tambem e o Proprietario de (pelo menos) uma das terras.
    # Fica nulo no caso comum de arrendatario.
    id_proprietario = Column(Integer, ForeignKey('public.proprietarios.id'))
    proprietario    = relationship('Proprietario', foreign_keys=[id_proprietario])

    # Diferencial de personalizacao Consiste (preservado do
    # banco anterior a Sessao 009)
    marca_criador   = Column(String(200))   # caminho da imagem

    # Mecanismo Schema-por-Produtor (multi-tenant, Sessao 018).
    # Nome do schema Postgres exclusivo deste Produtor
    # (padrao: produtor_ + id com zero-padding, ex.: produtor_00042).
    # NULL enquanto o Produtor nao passou pela rotina de onboarding.
    # Nunca preenchido manualmente - so pela rotina de onboarding.
    schema_nome     = Column(String(20), unique=True, nullable=True)

    # Controle de status (self-service pelo Produtor)
    ativo                          = Column(Boolean, nullable=False, default=True)
    ativo_alterado_em              = Column(DateTime)
    id_usuario_alteracao_status    = Column(Integer, ForeignKey('public.usuarios.id'))
    usuario_alteracao_status       = relationship('Usuario', foreign_keys=[id_usuario_alteracao_status])

    # Controle de datas
    criado_em       = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em   = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Produtor {self.nome}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\produtor.py
# =========================================================