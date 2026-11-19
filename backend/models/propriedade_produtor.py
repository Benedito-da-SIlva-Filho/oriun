# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\propriedade_produtor.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-02 13:43 -03
# ATUALIZADO EM: 2026-10-20 18:10 -03
# VERSAO: 1.4.0 changelog:
#
# DESCRICAO:
#     Model da tabela propriedade_produtor.
#     Tabela de vinculo N:N entre Propriedade e Produtor -
#     quem opera o rebanho naquela terra (com inscricao
#     estadual, codigo de exploracao pecuaria, tipo de
#     vinculo e campo "principal" para quando ha mais de
#     um Produtor na mesma Propriedade).
#     Diferente de propriedade_proprietario, que trata
#     apenas da titularidade legal da terra.
#
#     v1.0.0: Criacao do modulo (Sessao 010), com base no
#             esquema real da tabela (existente desde antes
#             da Sessao 009, com 8 colunas adicionadas
#             naquela sessao), conferido direto no banco.
#
#     v1.1.0: Sessao 019 - Corrigidas FKs id_propriedade e
#             id_produtor para incluir prefixo 'public.'
#             explicito. Motivo: apos propriedade.py v2.2.0 e
#             produtor.py v2.2.0 marcarem __table_args__ =
#             {'schema': 'public'}, referencias sem o prefixo
#             deixaram de encontrar as tabelas - erro so
#             apareceu ao SQLAlchemy configurar TODOS os mappers
#             do sistema (nao so os 9 do Onboarding), no boot do
#             servidor Flask.
#
#     v1.2.0: Sessao de Parelhamento Orion x GERAS (1-Cadastros) -
#             Adicionado id_regime_uso (FK para o novo catalogo
#             public.tb_1011_regime_uso, correspondente a GR1011
#             do GERAS). Substitui o uso pretendido do antigo
#             tipo_vinculo (String(30) livre, sem validacao).
#             tipo_vinculo NAO foi removida nesta versao - fica
#             como coluna morta ate confirmarmos que nada mais
#             le/escreve nela (pendencia separada de limpeza).
#
#     v1.3.0: Sessao de definicao do modelo de acesso do Produtor/
#             Equipe - Adicionado __table_args__ com schema
#             'public' explicito (mesmo padrao ja aplicado em
#             produtor.py v2.2.0 e usuario.py v1.3.0, Sessao 019 -
#             esta tabela tinha ficado de fora daquela rodada).
#             Motivo: o novo model UsuarioVinculo (usuario_vinculo)
#             referencia propriedade_produtor via FK com prefixo
#             'public.' explicito - sem esta marcacao aqui, o
#             SQLAlchemy nao conseguia determinar o join
#             (InvalidRequestError: "there are no foreign keys
#             linking these tables"), erro que so aparece no boot
#             do Flask, ao configurar TODOS os mappers do sistema
#             (por isso bloqueava ate o login de perfis que nao
#             usam UsuarioVinculo, como CONSISTE).
#     v1.4.0: Sessao 101 (20/10/2026, 18:10 -03) - Coluna nova documento_secundario (CNPJ do Produtor Fisico / CPF do Juridico, por fazenda). SQL: Tabelas\18_alter_propriedade_produtor_documento_secundario.sql
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model PropriedadeProdutor
# Espelha a tabela propriedade_produtor no PostgreSQL
# -------------------------------------------------------
class PropriedadeProdutor(Base):
    __tablename__ = 'propriedade_produtor'
    __table_args__ = {'schema': 'public'}

    # Identificacao e vinculo
    id                       = Column(Integer, primary_key=True)
    id_propriedade           = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    id_produtor              = Column(Integer, ForeignKey('public.produtores.id'), nullable=False)

    # true = este e o Produtor principal daquela Propriedade
    # (uso quando ha mais de um Produtor vinculado)
    principal                = Column(Boolean, default=False)

    # Dados operacionais do vinculo (podem diferir do
    # cadastro geral do Produtor, pois sao especificos
    # desta Propriedade)
    inscricao_estadual       = Column(String(30))
    uf_inscricao              = Column(String(2))
    codigo_exploracao        = Column(String(30))   # codigo de exploracao pecuaria

    # Sessao 101: documento SECUNDARIO do Produtor NESTA Propriedade (so digitos, opcional): CNPJ do Produtor
    # Fisica ou CPF do Juridico. O principal (cpf_cnpj + tipo_pessoa) fica no Produtor. Ver documentos_produtor.py.
    documento_secundario     = Column(String(14))

    # DEPRECIADO (v1.2.0): campo livre, sem validacao.
    # Mantido temporariamente ate confirmarmos que nada mais
    # le/escreve nele. Usar id_regime_uso a partir de agora.
    tipo_vinculo             = Column(String(30))    # ex: PROPRIETARIO, ARRENDATARIO

    # Regime de Uso (GR1011 do GERAS) - FK para o catalogo
    # public.tb_1011_regime_uso. Substitui tipo_vinculo.
    id_regime_uso            = Column(Integer, ForeignKey('public.tb_1011_regime_uso.id'))
    regime_uso               = relationship('RegimeUso', foreign_keys=[id_regime_uso])

    responsavel_informacoes  = Column(String(150))

    # Vigencia do vinculo
    data_inicio              = Column(Date)
    data_fim                 = Column(Date)   # nulo = vinculo ativo

    # Relacionamentos
    propriedade              = relationship('Propriedade', backref='vinculos_produtor')
    produtor                 = relationship('Produtor', backref='vinculos_propriedade')

    # Controle de datas
    # OBS: no banco, criado_em esta como NULLABLE com default
    # CURRENT_TIMESTAMP (diferente do padrao NOT NULL usado
    # nas demais tabelas) - mantido igual ao banco real.
    criado_em                = Column(DateTime, default=datetime.now)
    atualizado_em            = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<PropriedadeProdutor propriedade={self.id_propriedade} produtor={self.id_produtor}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\propriedade_produtor.py
# =========================================================