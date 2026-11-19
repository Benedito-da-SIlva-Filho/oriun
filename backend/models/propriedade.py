# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\propriedade.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-06-21 09:41 -03
# ATUALIZADO EM: 2026-08-04 15:09 -03
# VERSAO: 2.5.0
#
# DESCRICAO:
#     Model da tabela propriedades.
#     Representa as fazendas/estabelecimentos rurais.
#     Cadastro feito exclusivamente pela Consiste (equipe
#     interna); o Produtor logado tem apenas consulta
#     (Page-Up/Page-Down) das propriedades vinculadas a
#     ele. O vinculo com Produtor(es) e Proprietario(s) e
#     feito via tabelas propriedade_produtor e
#     propriedade_proprietario (relacionamento N:N, nao
#     ha FK direta aqui para produtor/proprietario).
#
#     v1.0.0: Criacao do modulo (pre-Sessao 009).
#     v2.0.0: Sessao 010 - Reescrita completa para bater
#             com o esquema real do banco pos Sessao 009
#             (27 colunas, conferidas direto no banco).
#     v2.1.0: Sessao 010 - Ajustes de tela de cadastro:
#             - Removida coluna complemento (DROP COLUMN -
#               "fazenda nao tem complemento", conceito de
#               endereco urbano nao se aplica)
#             - Adicionada coluna distancia_sede_cidade
#               (texto livre, ex: "15km asfalto + 3km terra")
#     v2.2.0: Sessao 019 - Adicionado __table_args__ com schema
#             'public' explicito. Mesmo motivo de produtor.py v2.2.0 -
#             protege contra "sequestro" pelo schema_translate_map da
#             rotina de Onboarding, ja que Propriedade e referenciada
#             por FK a partir de varias tabelas do schema do Produtor
#             (Gta, BrincoEntrada, BrincoSaida, EntradaBrincoRfid).
#     v2.3.0: Sessao 024 - Adicionado codigo_mapa (chave de
#             registro do estabelecimento rural junto ao MAPA,
#             Base Nacional de Dados - distinto de codigo_eras).
#             Motivado por e-GTA real de Abate, bloco Procedencia.
#             VARCHAR(15).
#     v2.4.0: Sessao 025 - Adicionados municipio_codigo (codigo
#             oficial IBGE, ex.: 5001102) e regiao (classificacao
#             regional, ex.: PANTANAL/PLANALTO, vista em toda
#             e-GTA). Fecha assimetria com tb_parceiros_propriedades,
#             que ja tinha os dois campos. Ambos NULLABLE - nao
#             afeta cadastros existentes. Habilita a busca de
#             matching por codigo (nao mais so nome de municipio
#             em texto livre) no fluxo de leitura de GTA, e
#             viabiliza a geracao automatica da GTA de Entrada
#             espelhada quando a Transferencia e entre duas
#             Propriedades do mesmo Produtor.
#     v2.5.0: Sessao 032 - Adicionado cadastro_completo (Boolean,
#             NOT NULL, default True). Pendencia P-040: o
#             pre-cadastro criado pelo fluxo de Convite Publico
#             (/convite) nasce com campos obrigatorios em
#             placeholder (tipo/roteiro_acesso/area_hectares) -
#             esta coluna marca isso, para redirecionar o
#             Produtor a completar o cadastro no primeiro acesso
#             em vez de cair direto na Home (logica em
#             auth.py/produtor_home()). Nasce False apenas quando
#             criada pelo Convite Publico (definido explicitamente
#             em convite.py, nao pelo default da coluna) - toda
#             Propriedade cadastrada pela Consiste (fluxo normal,
#             dados reais) e True desde a criacao. Coluna ja
#             adicionada ao banco via script SQL proprio
#             (Tabelas/adicionar_cadastro_completo_propriedades.sql).
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model Propriedade
# Espelha a tabela propriedades no PostgreSQL
# -------------------------------------------------------
class Propriedade(Base):
    __tablename__ = 'propriedades'
    __table_args__ = {'schema': 'public'}

    # Identificacao
    id                  = Column(Integer, primary_key=True)
    id_certificadora    = Column(Integer, ForeignKey('certificadoras.id'))
    nome                = Column(String(150), nullable=False)
    tipo                = Column(String(30), nullable=False)   # MISTA, CORTE, LEITE

    # Dados SISBOV / regulatorios
    # codigo_eras: presenca/ausencia = unico indicador de
    # participacao no SISBOV (sem flag booleana separada).
    # Nasce sempre nulo no cadastro pela Consiste; e
    # preenchido pela Certificadora em fluxo proprio (P-013).
    codigo_eras         = Column(String(20))
    # codigo_mapa: chave de registro do estabelecimento rural
    # junto ao MAPA (Base Nacional de Dados), formato UF+
    # Municipio+sequencial (ex: 500001428140003). DISTINTO de
    # codigo_eras - nao e indicador de SISBOV, e identificacao
    # federal do estabelecimento em si. Visto em toda e-GTA,
    # bloco Procedencia (Sessao 024).
    codigo_mapa         = Column(String(15))
    nirf_incra          = Column(String(30))
    car                 = Column(String(50))
    oesa                = Column(String(11))   # codigo no orgao estadual de sanidade (GTA)
    inscricao_estadual  = Column(String(30))
    status_atividade    = Column(String(20))   # Ativo / Suspenso / Cancelado

    # Endereco detalhado
    # OBS: sem "complemento" - conceito de endereco urbano
    # (apto, sala, bloco) nao se aplica a estabelecimento rural.
    logradouro          = Column(String(200))
    numero              = Column(String(10))
    bairro                 = Column(String(100))
    cep                 = Column(String(9))
    municipio           = Column(String(100), nullable=False)
    # municipio_codigo: codigo oficial IBGE do municipio (ex.:
    # 5001102), separado do campo municipio acima (texto livre).
    # Adicionado v2.4.0 (Sessao 025) - paridade com
    # tb_parceiros_propriedades e suporte a matching por codigo
    # no fluxo de leitura de GTA.
    municipio_codigo    = Column(String(10))
    uf                  = Column(String(2), nullable=False)
    # regiao: classificacao regional vista no bloco
    # Procedencia/Destino de toda e-GTA (ex.: PANTANAL,
    # PLANALTO). Adicionado v2.4.0 (Sessao 025) - nao obrigatorio,
    # preenchimento gradual conforme leitura de GTAs reais.
    regiao              = Column(String(50))
    roteiro_acesso      = Column(Text, nullable=False)
    distancia_sede_cidade = Column(String(200))   # texto livre, ex: "15km asfalto + 3km terra"

    # Contato
    email               = Column(String(150), nullable=False)
    telefone            = Column(String(20), nullable=False)
    telefone2           = Column(String(20))

    # Area e localizacao geografica
    area_hectares       = Column(Numeric(10, 2), nullable=False)
    latitude            = Column(Numeric(10, 7))
    longitude           = Column(Numeric(10, 7))

    # Relacionamentos
    certificadora       = relationship('Certificadora', backref='propriedades')

    # Controle
    ativo               = Column(Boolean, nullable=False, default=True)
    # cadastro_completo: False apenas quando nasce pelo Convite
    # Publico, com campos obrigatorios em placeholder (P-040,
    # Sessao 032). True em qualquer outro caso (cadastro pela
    # Consiste, com dados reais, ja nasce completo).
    cadastro_completo   = Column(Boolean, nullable=False, default=True)
    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em       = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Propriedade {self.nome}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\propriedade.py
# =========================================================