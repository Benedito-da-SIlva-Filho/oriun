-- =============================================================
-- ORION SISBOV
-- Sessão 009 — Implementação do Banco de Dados (Módulo GERAS)
-- Arquivo: 06_numeracoes.sql
-- Tabela 6 de 10: numeracoes
-- Data: 01/07/2026
-- Responsável: Benedito Silva Filho
-- Companheiro de Viagem: Clau (Claude Sonnet 5)
--
-- Histórico de versão:
--   v1.0 - 01/07/2026 - Criação inicial - Clau
--
-- Descrição:
--   Cria a tabela "numeracoes" — a FAIXA de brincos recebida pelo
--   Produtor junto ao fabricante. Escopo desta tabela é só a faixa
--   em si (bloco recebido); controle individual por brinco (RFID),
--   reidentificação, cancelamento e vínculo com dados do animal
--   ficam para sessão futura dedicada ao módulo Animais — já
--   referenciada com base na estrutura provada do sistema Maker
--   (tabelas GR2001 "Entrada Animais" e GR7017 "Entrada Brincos
--   RFID"), que não será reinventada, só devidamente planejada em
--   sessão própria.
--
--   DECISÕES DESTA SESSÃO:
--   1. Tabela nova (não existia no banco).
--   2. Padrão de nomenclatura: prefixo "id_" para chaves
--      estrangeiras, consistente com o restante do banco.
--   3. SEM Dígito Verificador (DV) — novo modelo de brincos não
--      usa mais esse campo (diferente do Maker/GR3007).
--   4. "id_solicitacao" é OPCIONAL — cobre o cenário de cliente
--      migrando para o Orion já com numeração ativa no SISBOV,
--      sem solicitação formal registrada no sistema.
--   5. "faixa_final" é calculada pela aplicação (faixa_inicial +
--      quantidade), mas GRAVADA no banco — redundante, porém
--      facilita muito consultas futuras por faixa.
--   6. "quantidade_usada" — controle agregado de quantos brincos
--      da faixa já foram aplicados em animais (contagem simples;
--      o detalhe individual por brinco fica para o módulo Animais).
-- =============================================================

-- Bloco 1: Criação da tabela numeracoes
CREATE TABLE numeracoes (
    id                  SERIAL PRIMARY KEY,

    -- Vínculos
    id_solicitacao      INTEGER         REFERENCES solicitacoes_numeracao(id),  -- nulo = cadastro avulso/migração
    id_produtor         INTEGER         NOT NULL REFERENCES produtores(id),
    id_propriedade      INTEGER         NOT NULL REFERENCES propriedades(id),
    id_fabricante       INTEGER         NOT NULL REFERENCES fabricantes_brincos(id),

    -- Documento fiscal
    numero_nf           VARCHAR(20),

    -- Faixa recebida
    faixa_inicial       VARCHAR(15)     NOT NULL,   -- número SISBOV (15 dígitos), sem DV
    faixa_final         VARCHAR(15)     NOT NULL,   -- calculado na aplicação, gravado aqui
    quantidade          INTEGER         NOT NULL,
    quantidade_usada    INTEGER         NOT NULL DEFAULT 0,

    status              VARCHAR(30)     NOT NULL,
    data_entrada         DATE            NOT NULL,

    -- Controle de datas
    criado_em           TIMESTAMP       NOT NULL DEFAULT NOW(),
    atualizado_em        TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Bloco 2: Comentários de documentação
COMMENT ON TABLE numeracoes IS
    'Faixa de brincos recebida pelo Produtor junto ao fabricante. Controle individual por brinco (RFID) e vínculo com animal ficam para sessão futura do módulo Animais.';
COMMENT ON COLUMN numeracoes.id_solicitacao IS
    'Nulo = cadastro avulso ou migração de cliente que já vem com numeração ativa no SISBOV, sem solicitação formal no Orion.';
COMMENT ON COLUMN numeracoes.faixa_inicial IS
    'Número SISBOV inicial da faixa (15 dígitos: 076 + sequencial). Sem dígito verificador (DV) — não usado no novo modelo de brincos.';
COMMENT ON COLUMN numeracoes.faixa_final IS
    'Calculado na aplicação (faixa_inicial + quantidade - 1), mas gravado no banco para facilitar buscas por faixa.';
COMMENT ON COLUMN numeracoes.quantidade_usada IS
    'Contagem agregada de brincos já aplicados em animais. Controle individual por brinco fica no módulo Animais (sessão futura).';

-- Bloco 3: Índices de busca
CREATE INDEX idx_numeracoes_id_produtor ON numeracoes (id_produtor);
CREATE INDEX idx_numeracoes_id_propriedade ON numeracoes (id_propriedade);
CREATE INDEX idx_numeracoes_faixa_inicial ON numeracoes (faixa_inicial);
CREATE INDEX idx_numeracoes_faixa_final ON numeracoes (faixa_final);

-- Bloco 4: Trigger para manter "atualizado_em" sempre corrente
CREATE OR REPLACE FUNCTION trg_numeracoes_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_atualizado_em_numeracoes
    BEFORE UPDATE ON numeracoes
    FOR EACH ROW
    EXECUTE FUNCTION trg_numeracoes_atualizado_em();