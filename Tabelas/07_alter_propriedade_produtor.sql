-- =============================================================
-- ORION SISBOV
-- Sessão 009 — Implementação do Banco de Dados (Módulo GERAS)
-- Arquivo: 07_alter_propriedade_produtor.sql
-- Tabela 7 de 9: propriedade_produtor (ALTER TABLE)
-- Data: 01/07/2026
-- Hora de início: 18:28
-- Responsável: Benedito Silva Filho
-- Companheiro de Viagem: Clau (Claude Sonnet 5)
--
-- Histórico de versão:
--   v1.0 - 01/07/2026 18:28 - Criação inicial - Clau
--
-- Descrição:
--   Adiciona à tabela "propriedade_produtor" (já existente, com
--   apenas id/id_propriedade/id_produtor/principal/criado_em) os
--   campos definidos na Sessão 008 para o vínculo completo entre
--   Propriedade e Produtor:
--
--   - inscricao_estadual / uf_inscricao — inscrição estadual do
--     Produtor NAQUELA propriedade específica (distinta da
--     inscrição da própria propriedade, em propriedades.
--     inscricao_estadual).
--   - codigo_exploracao — Código de Exploração Pecuária, confirmado
--     pelo manual oficial do SISBOV (tela "Produtores" da
--     Propriedade).
--   - data_inicio / data_fim — vigência do vínculo (permite
--     histórico de arrendamentos ao longo do tempo).
--   - tipo_vinculo — Arrendatário/Comodatário/Proprietário/Outro.
--     Campo que evitou duplicidade com "regime_uso" (descartado de
--     produtores nesta sessão).
--   - responsavel_informacoes — nome de quem responde pelas
--     informações desse vínculo perante o SISBOV.
--   - atualizado_em — tabela não tinha controle de atualização;
--     adicionado junto com trigger, padrão das demais tabelas.
-- =============================================================

-- Bloco 1: Adiciona as colunas que faltavam
ALTER TABLE propriedade_produtor
    ADD COLUMN inscricao_estadual      VARCHAR(30),
    ADD COLUMN uf_inscricao            CHAR(2),
    ADD COLUMN codigo_exploracao       VARCHAR(30),
    ADD COLUMN data_inicio             DATE,
    ADD COLUMN data_fim                DATE,
    ADD COLUMN tipo_vinculo            VARCHAR(30),
    ADD COLUMN responsavel_informacoes VARCHAR(150),
    ADD COLUMN atualizado_em           TIMESTAMP NOT NULL DEFAULT NOW();

-- Bloco 2: Comentários de documentação
COMMENT ON COLUMN propriedade_produtor.inscricao_estadual IS
    'Inscrição estadual do Produtor NESTA propriedade específica (distinta da inscrição da propriedade em si).';
COMMENT ON COLUMN propriedade_produtor.tipo_vinculo IS
    'Arrendatário / Comodatário / Proprietário / Outro. Substitui o antigo "regime_uso" (descartado de produtores por duplicidade).';
COMMENT ON COLUMN propriedade_produtor.codigo_exploracao IS
    'Código de Exploração Pecuária, conforme manual oficial SISBOV.';
COMMENT ON COLUMN propriedade_produtor.data_inicio IS
    'Início da vigência do vínculo Produtor-Propriedade. Permite histórico de arrendamentos ao longo do tempo.';
COMMENT ON COLUMN propriedade_produtor.data_fim IS
    'Fim da vigência do vínculo. Nulo = vínculo ainda ativo.';

-- Bloco 3: Índices de busca
CREATE INDEX idx_propriedade_produtor_tipo_vinculo ON propriedade_produtor (tipo_vinculo);

-- Bloco 4: Trigger para manter "atualizado_em" sempre corrente
CREATE OR REPLACE FUNCTION trg_propriedade_produtor_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_atualizado_em_propriedade_produtor
    BEFORE UPDATE ON propriedade_produtor
    FOR EACH ROW
    EXECUTE FUNCTION trg_propriedade_produtor_atualizado_em();