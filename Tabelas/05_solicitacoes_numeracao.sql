-- =============================================================
-- ORION SISBOV
-- Sessão 009 — Implementação do Banco de Dados (Módulo GERAS)
-- Arquivo: 05_solicitacoes_numeracao.sql
-- Tabela 5 de 10: solicitacoes_numeracao
-- Data: 01/07/2026
-- Hora de início: 17:11
-- Responsável: Benedito Silva Filho
-- Companheiro de Viagem: Clau (Claude Sonnet 5)
--
-- Histórico de versão:
--   v1.0 - 01/07/2026 17:11 - Criação inicial - Clau
--
-- Descrição:
--   Cria a tabela "solicitacoes_numeracao" — pedidos de numeração
--   de brincos feitos pelo Produtor. Tabela ÚNICA que atende aos
--   dois fluxos de negócio (decisão desta sessão: "uma tabela,
--   duas telas"):
--
--   1. Fluxo SISBOV: propriedade com codigo_eras — a Certificadora
--      intermedia o processo (id_certificadora preenchido).
--   2. Fluxo não-SISBOV: Produtor pede direto ao fabricante
--      (id_certificadora nulo).
--
--   DECISÕES DESTA SESSÃO:
--   1. Tabela nova (não existia no banco).
--   2. PADRÃO DE NOMENCLATURA NOVO A PARTIR DESTA TABELA: chaves
--      estrangeiras usam prefixo "id_" (id_produtor, id_propriedade,
--      etc.), não mais sufixo "_id". As 4 tabelas anteriores já
--      foram renomeadas para manter consistência em todo o banco.
--   3. "tipo_identificador" — lista fechada do manual oficial do
--      MAPA (Bottom, Brinco, etc.), relevante só no fluxo SISBOV.
--      Opcional no banco; obrigatoriedade condicional na aplicação.
--   4. "faixa_numeracao" NÃO entra aqui — hipótese é que pertence
--      à tabela "numeracoes" (6/10), como confirmação de
--      recebimento após o pedido. PENDÊNCIA a revisitar na
--      próxima tabela.
--   5. "solicitante" não vira campo — no fluxo do Produtor, é
--      sempre o próprio id_produtor (não há usuário terceiro
--      solicitando em nome dele).
--   6. "numero_referencia" — campo livre e opcional, preenchido
--      pelo Produtor com o nº da solicitação junto ao fabricante
--      ou o nº da Nota Fiscal, quando existir. NÃO é a nossa PK.
-- =============================================================

-- Bloco 1: Criação da tabela solicitacoes_numeracao
CREATE TABLE solicitacoes_numeracao (
    id                  SERIAL PRIMARY KEY,

    -- Vínculos (padrão novo: prefixo id_)
    id_produtor         INTEGER         NOT NULL REFERENCES produtores(id),
    id_propriedade      INTEGER         NOT NULL REFERENCES propriedades(id),
    id_fabricante       INTEGER         NOT NULL REFERENCES fabricantes_brincos(id),
    id_certificadora    INTEGER         REFERENCES certificadoras(id),  -- nulo = pedido direto (não-SISBOV)

    -- Dados da solicitação
    tipo_identificador  VARCHAR(60),                -- relevante só no fluxo SISBOV
    quantidade          INTEGER         NOT NULL,
    status              VARCHAR(30)     NOT NULL,
    numero_referencia   VARCHAR(50),                -- nº solicitação externa ou nº da NF
    observacao          TEXT,

    -- Controle de datas
    data_solicitacao    TIMESTAMP       NOT NULL DEFAULT NOW(),
    criado_em           TIMESTAMP       NOT NULL DEFAULT NOW(),
    atualizado_em       TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Bloco 2: Comentários de documentação
COMMENT ON TABLE solicitacoes_numeracao IS
    'Pedidos de numeração de brincos. Tabela única para os dois fluxos: SISBOV (id_certificadora preenchido) e não-SISBOV (id_certificadora nulo, pedido direto ao fabricante).';
COMMENT ON COLUMN solicitacoes_numeracao.id_certificadora IS
    'Nulo = pedido direto ao fabricante (não-SISBOV). Preenchido = fluxo SISBOV, intermediado pela Certificadora.';
COMMENT ON COLUMN solicitacoes_numeracao.tipo_identificador IS
    'Tipo de identificador conforme manual SISBOV: Bottom/Bottom e Marca Fogo/Brinco/Migração RASTREA/Registrado em Associação/etc. Relevante só no fluxo SISBOV.';
COMMENT ON COLUMN solicitacoes_numeracao.numero_referencia IS
    'Número de referência livre, informado pelo Produtor: nº da solicitação junto ao fabricante ou nº da Nota Fiscal. NÃO é a chave primária da tabela.';
COMMENT ON COLUMN solicitacoes_numeracao.status IS
    'Situação da solicitação (ex: Pendente, Aprovado, Recusado, Em processamento) — valores exatos a definir na aplicação.';

-- Bloco 3: Índices de busca
CREATE INDEX idx_solicitacoes_numeracao_id_produtor ON solicitacoes_numeracao (id_produtor);
CREATE INDEX idx_solicitacoes_numeracao_id_propriedade ON solicitacoes_numeracao (id_propriedade);
CREATE INDEX idx_solicitacoes_numeracao_status ON solicitacoes_numeracao (status);

-- Bloco 4: Trigger para manter "atualizado_em" sempre corrente
CREATE OR REPLACE FUNCTION trg_solicitacoes_numeracao_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_atualizado_em_solicitacoes_numeracao
    BEFORE UPDATE ON solicitacoes_numeracao
    FOR EACH ROW
    EXECUTE FUNCTION trg_solicitacoes_numeracao_atualizado_em();