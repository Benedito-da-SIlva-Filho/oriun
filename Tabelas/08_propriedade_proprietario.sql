-- =============================================================
-- ORION SISBOV
-- Sessão 009 — Implementação do Banco de Dados (Módulo GERAS)
-- Arquivo: 08_propriedade_proprietario.sql
-- Tabela 8 de 9 (última tabela da sessão): propriedade_proprietario
-- Data: 01/07/2026
-- Hora de início: 18:39
-- Responsável: Benedito Silva Filho
-- Companheiro de Viagem: Clau (Claude Sonnet 5)
--
-- Histórico de versão:
--   v1.0 - 01/07/2026 18:39 - Criação inicial - Clau
--
-- Descrição:
--   Cria a tabela "propriedade_proprietario" — vínculo entre a
--   Propriedade (a terra) e o Proprietário (dono legal/titular).
--
--   DECISÕES DESTA SESSÃO:
--   1. Tabela nova (não existia no banco).
--   2. Guarda EXCLUSIVAMENTE a titularidade da terra — nenhuma
--      informação de operação de animal, rastreabilidade ou
--      inventário (isso é responsabilidade de
--      "propriedade_produtor"). Proprietário nem sempre é Produtor.
--   3. SEM campo "principal" — diferente de propriedade_produtor,
--      não há necessidade de eleger um "proprietário principal",
--      já que o Proprietário não gerencia animais nem tem
--      inventário próprio (essa distinção só faz sentido para
--      quem opera o rebanho).
--   4. data_inicio/data_fim cobrem mudança de titularidade ao
--      longo do tempo (venda, herança, sociedade).
-- =============================================================

-- Bloco 1: Criação da tabela propriedade_proprietario
CREATE TABLE propriedade_proprietario (
    id                  SERIAL PRIMARY KEY,

    id_propriedade      INTEGER         NOT NULL REFERENCES propriedades(id),
    id_proprietario     INTEGER         NOT NULL REFERENCES proprietarios(id),

    data_inicio         DATE            NOT NULL,
    data_fim             DATE,                       -- nulo = titularidade ainda ativa

    criado_em           TIMESTAMP       NOT NULL DEFAULT NOW(),
    atualizado_em        TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Bloco 2: Comentários de documentação
COMMENT ON TABLE propriedade_proprietario IS
    'Vínculo de titularidade: quem é o dono legal da terra e desde quando. Não guarda dados de operação/rastreabilidade de animal (ver propriedade_produtor).';
COMMENT ON COLUMN propriedade_proprietario.data_fim IS
    'Nulo = titularidade ainda ativa. Preenchido = venda, herança ou outra mudança de titularidade.';

-- Bloco 3: Índices de busca
CREATE INDEX idx_propriedade_proprietario_id_propriedade ON propriedade_proprietario (id_propriedade);
CREATE INDEX idx_propriedade_proprietario_id_proprietario ON propriedade_proprietario (id_proprietario);

-- Bloco 4: Trigger para manter "atualizado_em" sempre corrente
CREATE OR REPLACE FUNCTION trg_propriedade_proprietario_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_atualizado_em_propriedade_proprietario
    BEFORE UPDATE ON propriedade_proprietario
    FOR EACH ROW
    EXECUTE FUNCTION trg_propriedade_proprietario_atualizado_em();