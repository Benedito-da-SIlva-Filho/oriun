-- =============================================================
-- ORION SISBOV
-- Sessão 009 — Implementação do Banco de Dados (Módulo GERAS)
-- Arquivo: 04_fabricantes_brincos.sql
-- Tabela 4 de 10: fabricantes_brincos
-- Data: 01/07/2026
-- Hora de início: 15:25
-- Responsável: Benedito Silva Filho
-- Companheiro de Viagem: Clau (Claude Sonnet 5)
--
-- Histórico de versão:
--   v1.0 - 01/07/2026 15:25 - Criação inicial - Clau
--
-- Descrição:
--   Cria a tabela "fabricantes_brincos" — fornecedores de brincos
--   SISBOV. Tabela nova (não existia no banco), modelo enxuto:
--
--   DECISÕES DESTA SESSÃO:
--   1. Fabricante não tem código próprio no MAPA — a numeração de
--      brinco segue a sequência do Produtor na solicitação, não do
--      fabricante.
--   2. Contato (telefone/email) NÃO entra nesta tabela — essa
--      informação já vem na Nota Fiscal de cada pedido.
--   3. CNPJ é único por fabricante — trava UNIQUE no banco.
--   4. logo_path é obrigatório — logo do fabricante é usado na
--      impressão do documento DIA (armazenado fisicamente em
--      static/logos/fornecedores/).
-- =============================================================

-- Bloco 1: Criação da tabela fabricantes_brincos
CREATE TABLE fabricantes_brincos (
    id              SERIAL PRIMARY KEY,

    nome            VARCHAR(150)    NOT NULL,
    cnpj            VARCHAR(18)     NOT NULL UNIQUE,
    logo_path       VARCHAR(255)    NOT NULL,   -- caminho em static/logos/fornecedores/

    ativo           BOOLEAN         NOT NULL DEFAULT TRUE,

    criado_em       TIMESTAMP       NOT NULL DEFAULT NOW(),
    atualizado_em   TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Bloco 2: Comentários de documentação
COMMENT ON TABLE fabricantes_brincos IS
    'Fornecedores de brincos SISBOV. Numeração segue sequência do Produtor na solicitação, não do fabricante.';
COMMENT ON COLUMN fabricantes_brincos.logo_path IS
    'Caminho do logo em static/logos/fornecedores/. Obrigatório para impressão do documento DIA.';
COMMENT ON COLUMN fabricantes_brincos.cnpj IS
    'CNPJ único por fabricante (trava UNIQUE).';

-- Bloco 3: Índice de busca (CNPJ já tem índice implícito pela UNIQUE)
CREATE INDEX idx_fabricantes_brincos_nome ON fabricantes_brincos (nome);

-- Bloco 4: Trigger para manter "atualizado_em" sempre corrente
CREATE OR REPLACE FUNCTION trg_fabricantes_brincos_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_atualizado_em_fabricantes_brincos
    BEFORE UPDATE ON fabricantes_brincos
    FOR EACH ROW
    EXECUTE FUNCTION trg_fabricantes_brincos_atualizado_em();