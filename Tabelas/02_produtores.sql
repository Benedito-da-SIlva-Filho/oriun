-- =============================================================
-- ORION SISBOV
-- Sessão 009 — Implementação do Banco de Dados (Módulo GERAS)
-- Arquivo: 02_produtores.sql
-- Tabela 2 de 10: produtores
-- Data: 01/07/2026
-- Hora de início: 10:32
-- Responsável: Benedito Silva Filho
-- Companheiro de Viagem: Clau (Claude Sonnet 5)
--
-- Histórico de versão:
--   v1.0 - 01/07/2026 10:32 - Criação inicial - Clau
--
-- Descrição:
--   Recria a tabela "produtores", fundindo o modelo SISBOV 2.0
--   (alinhado na Sessão 008) com o campo "marca_criador" já
--   existente no banco (diferencial de personalização — Consiste).
--
--   IMPORTANTE — decisões desta sessão:
--   1. Tabela estava ZERADA (confirmado por Benedito) — seguro
--      fazer DROP + CREATE sem risco de perda de dados.
--   2. Campo "regime_uso" (versão antiga) foi DESCARTADO por ser
--      duplicidade de "propriedade_produtor.tipo_vinculo" — o
--      regime de uso é característica do VÍNCULO produtor-fazenda,
--      não do produtor em si (um produtor pode ser arrendatário
--      numa fazenda e comodatário em outra).
--   3. Campo "marca_criador" foi PRESERVADO — usado como trunfo
--      para personalização quando exigido pelo cliente.
-- =============================================================

-- Bloco 1: Remove a tabela antiga (confirmado zerada, sem risco)
DROP TABLE IF EXISTS produtores;

-- Bloco 2: Criação da tabela produtores (modelo fundido)
CREATE TABLE produtores (
    id              SERIAL PRIMARY KEY,

    -- Identificação (SISBOV 2.0)
    nome            VARCHAR(150)    NOT NULL,
    razao_social    VARCHAR(150)    NOT NULL,
    cpf_cnpj        VARCHAR(18)     NOT NULL,   -- dado cadastral, NÃO é login
    tipo_pessoa     VARCHAR(10)     NOT NULL,   -- 'Fisica' ou 'Juridica'
    visibilidade    VARCHAR(10)     NOT NULL,   -- 'Privado' ou 'Publico' (regra de negócio pendente)

    -- Contato (SISBOV 2.0)
    email           VARCHAR(150)    NOT NULL,   -- não é login
    telefone        VARCHAR(20)     NOT NULL,
    telefone2       VARCHAR(20),

    -- Endereço (SISBOV 2.0) — fixo por produtor
    logradouro      VARCHAR(200),
    numero          VARCHAR(10),
    complemento     VARCHAR(100),
    bairro          VARCHAR(100),
    cep             VARCHAR(9),
    municipio       VARCHAR(100)    NOT NULL,
    uf              CHAR(2)         NOT NULL,
    latitude        NUMERIC(10,7),              -- preenchimento automático
    longitude       NUMERIC(10,7),              -- preenchimento automático

    -- Vínculo (SISBOV 2.0 / Orion)
    proprietario_id INTEGER REFERENCES proprietarios(id),  -- nulo se arrendatário

    -- Diferencial Consiste (preservado do banco atual)
    marca_criador   VARCHAR(200),               -- personalização / marca própria de criador

    -- Controle interno (Orion)
    ativo           BOOLEAN         NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMP       NOT NULL DEFAULT NOW(),
    atualizado_em   TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Bloco 3: Comentários de documentação
COMMENT ON TABLE produtores IS
    'Quem opera a propriedade (SISBOV 2.0). Pode ser arrendatário (maioria) ou proprietário. Modelo fundido: SISBOV 2.0 + marca_criador (Consiste).';
COMMENT ON COLUMN produtores.cpf_cnpj IS
    'CPF ou CNPJ — dado cadastral, NÃO é usado como login (RN-001).';
COMMENT ON COLUMN produtores.visibilidade IS
    'Valores esperados: Privado, Publico. Regra de negócio de exibição pública ainda PENDENTE de confirmação.';
COMMENT ON COLUMN produtores.marca_criador IS
    'Marca própria do criador/produtor, usada em personalizações quando exigido pelo cliente.';
COMMENT ON COLUMN produtores.proprietario_id IS
    'Nulo se o produtor for arrendatário sem vínculo de propriedade da terra.';

-- Bloco 4: Índices de busca
CREATE INDEX idx_produtores_cpf_cnpj ON produtores (cpf_cnpj);
CREATE INDEX idx_produtores_proprietario_id ON produtores (proprietario_id);

-- Bloco 5: Trigger para manter "atualizado_em" sempre corrente
-- (Reaproveita o padrão de atualização automática já usado no restante do sistema)
CREATE OR REPLACE FUNCTION trg_produtores_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_atualizado_em_produtores
    BEFORE UPDATE ON produtores
    FOR EACH ROW
    EXECUTE FUNCTION trg_produtores_atualizado_em();