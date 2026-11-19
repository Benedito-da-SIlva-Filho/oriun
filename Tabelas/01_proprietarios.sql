-- =============================================================
-- ORION SISBOV
-- Sessão 009 — Implementação do Banco de Dados (Módulo GERAS)
-- Arquivo: 01_proprietarios.sql
-- Tabela 1 de 10: proprietarios
-- Data: 01/07/2026
-- Hora de início: 09:56
-- Responsável: Benedito Silva Filho
-- Companheiro de Viagem: Clau (Claude Sonnet 5)
--
-- Histórico de versão:
--   v1.0 - 01/07/2026 09:56 - Criação inicial - Clau
--
-- Descrição:
--   Cria a tabela "proprietarios" — dono legal da terra, separado do
--   Produtor conforme SISBOV 2.0 (IN 51/2018 Anexo III). A maioria
--   dos clientes da Consiste é arrendatária, então o Proprietário é
--   uma entidade que existe de forma independente do Produtor.
-- =============================================================

-- Bloco 1: Criação da tabela proprietarios
CREATE TABLE proprietarios (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(150)    NOT NULL,
    razao_social    VARCHAR(150)    NOT NULL,
    cpf_cnpj        VARCHAR(18)     NOT NULL,
    tipo_pessoa     VARCHAR(10)     NOT NULL,   -- 'Fisica' ou 'Juridica'
    visibilidade    VARCHAR(10)     NOT NULL,   -- 'Privado' ou 'Publico'
    email           VARCHAR(150)    NOT NULL,
    telefone        VARCHAR(20)     NOT NULL,
    telefone2       VARCHAR(20),
    logradouro      VARCHAR(200),
    numero          VARCHAR(10),
    complemento     VARCHAR(100),
    bairro          VARCHAR(100),
    cep             VARCHAR(9),
    municipio       VARCHAR(100)    NOT NULL,
    uf              CHAR(2)         NOT NULL,
    latitude        NUMERIC(10,7),              -- preenchimento automático
    longitude       NUMERIC(10,7),              -- preenchimento automático
    ativo           BOOLEAN         NOT NULL DEFAULT TRUE
);

-- Bloco 2: Comentários de documentação (facilita manutenção futura)
COMMENT ON TABLE proprietarios IS
    'Dono legal da terra. Entidade separada do Produtor conforme SISBOV 2.0 (RN-007).';
COMMENT ON COLUMN proprietarios.tipo_pessoa IS
    'Valores esperados: Fisica, Juridica';
COMMENT ON COLUMN proprietarios.visibilidade IS
    'Valores esperados: Privado, Publico';
COMMENT ON COLUMN proprietarios.cpf_cnpj IS
    'CPF (11 dig.) ou CNPJ (14 dig.), armazenado formatado como texto.';

-- Bloco 3: Índice para busca rápida por CPF/CNPJ (evita duplicidade em consultas)
CREATE INDEX idx_proprietarios_cpf_cnpj ON proprietarios (cpf_cnpj);