-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion
-- MODULO: criar_tabelas.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-06-21 09:32 -03
-- ATUALIZADO EM: 2026-06-21 09:32 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Cria as tabelas do banco de dados do Orion.
--     Arquitetura inicial: schema publico (Opcao 1).
--     FUTURO: migrar para schema por certificadora (Opcao 3).
--     v1.0.0: Criacao das tabelas base.
-- =========================================================

-- -------------------------------------------------------
-- TABELA 1 — certificadoras
-- Cadastro das certificadoras credenciadas pelo MAPA.
-- Tambem armazena configuracoes do White Label.
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS certificadoras (
    id               SERIAL PRIMARY KEY,
    nome             VARCHAR(100) NOT NULL,
    cnpj             VARCHAR(18)  NOT NULL UNIQUE,
    inscricao_est    VARCHAR(20),
    endereco         VARCHAR(200),
    cidade           VARCHAR(100),
    uf               CHAR(2),
    cep              VARCHAR(9),
    telefone         VARCHAR(20),
    email            VARCHAR(100),
    -- White Label
    logo             VARCHAR(200),
    cor_primaria     VARCHAR(7)   DEFAULT '#1F4E79',
    cor_secundaria   VARCHAR(7)   DEFAULT '#2E75B6',
    dominio          VARCHAR(100),
    -- Controle
    ativo            BOOLEAN      DEFAULT TRUE,
    criado_em        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    atualizado_em    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------
-- TABELA 2 — propriedades
-- Cadastro das fazendas/estabelecimentos rurais.
-- Feito pela Certificadora ou pela Consiste.
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS propriedades (
    id               SERIAL PRIMARY KEY,
    certificadora_id INTEGER      REFERENCES certificadoras(id),
    nome             VARCHAR(100) NOT NULL,
    codigo_sisbov    VARCHAR(20)  UNIQUE,
    inscricao_est    VARCHAR(20),
    tipo             VARCHAR(20),  -- MISTA, CORTE, LEITE
    endereco         VARCHAR(200),
    cidade           VARCHAR(100),
    uf               CHAR(2),
    cep              VARCHAR(9),
    area_hectares    NUMERIC(10,2),
    latitude         NUMERIC(10,6),
    longitude        NUMERIC(10,6),
    nirf             VARCHAR(20),
    car              VARCHAR(50),
    -- Controle
    ativo            BOOLEAN      DEFAULT TRUE,
    criado_em        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    atualizado_em    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------
-- TABELA 3 — produtores
-- Cadastro dos produtores rurais.
-- Um produtor pode ter varias propriedades.
-- Uma propriedade pode ter varios produtores.
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS produtores (
    id               SERIAL PRIMARY KEY,
    tipo_pessoa      CHAR(1)      NOT NULL, -- F=Fisica J=Juridica
    cpf              VARCHAR(14),
    cnpj             VARCHAR(18),
    nome             VARCHAR(100) NOT NULL,
    inscricao_est    VARCHAR(20),
    regime_uso       VARCHAR(30),  -- PROPRIETARIO UNICO, ARRENDATARIO
    endereco         VARCHAR(200),
    cidade           VARCHAR(100),
    uf               CHAR(2),
    cep              VARCHAR(9),
    telefone         VARCHAR(20),
    celular          VARCHAR(20),
    email            VARCHAR(100),
    marca_criador    VARCHAR(200), -- caminho da imagem
    -- Controle
    ativo            BOOLEAN      DEFAULT TRUE,
    criado_em        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    atualizado_em    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------
-- TABELA 4 — propriedade_produtor
-- Relacionamento muitos-para-muitos entre
-- propriedades e produtores.
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS propriedade_produtor (
    id               SERIAL PRIMARY KEY,
    propriedade_id   INTEGER      NOT NULL REFERENCES propriedades(id),
    produtor_id      INTEGER      NOT NULL REFERENCES produtores(id),
    principal        BOOLEAN      DEFAULT FALSE, -- produtor principal
    criado_em        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(propriedade_id, produtor_id)
);

-- -------------------------------------------------------
-- TABELA 5 — usuarios
-- Login e controle de acesso ao sistema.
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id               SERIAL PRIMARY KEY,
    certificadora_id INTEGER      REFERENCES certificadoras(id),
    produtor_id      INTEGER      REFERENCES produtores(id),
    login            VARCHAR(50)  NOT NULL UNIQUE,
    senha            VARCHAR(200) NOT NULL, -- sempre criptografada!
    perfil           VARCHAR(20)  NOT NULL, -- ADMIN, CERTIFICADORA, PRODUTOR, CONSISTE
    nome             VARCHAR(100),
    email            VARCHAR(100),
    -- Controle
    ativo            BOOLEAN      DEFAULT TRUE,
    ultimo_acesso    TIMESTAMP,
    criado_em        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    atualizado_em    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- FIM DE ARQUIVO: criar_tabelas.sql
-- =========================================================