-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\database (ajustar conforme sua pasta de migrations)
-- MODULO: sql_criacao_tb_1011_regime_uso.sql
-- AUTOR: Benedito Silva Filho.
-- CRIADO EM: 2026-07-23 12:13 -03
-- ATUALIZADO EM: 2026-07-23 12:13 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Cria a tabela de catalogo tb_1011_regime_uso (schema
--     publico), correspondente a GR1011 do GERAS ("Regime
--     Uso"). Substitui o campo livre
--     propriedade_produtor.tipo_vinculo (String(30), sem
--     validacao) por um catalogo real com FK, seguindo
--     decisao da Sessao de Parelhamento Orion x GERAS
--     (pasta 1-Cadastros).
--
--     v1.0.0: Criacao do modulo.
--             - Tabela tb_1011_regime_uso com id, codigo,
--               descricao, definicao (tooltip/ajuda),
--               ativo, criado_em, atualizado_em.
--             - Trigger dedicada trg_tb_1011_regime_uso_atualizado_em.
--             - Seed com os 9 valores oficiais do GERAS
--               (fonte: GR1011.TXT). Definicao nula para
--               Condomino e Comodatario - o export do GERAS
--               nao trouxe texto explicativo para esses dois.
--             - Coluna propriedade_produtor.id_regime_uso
--               (FK) adicionada; tipo_vinculo antigo mantido
--               por ora (nao removida nesta versao - ver
--               observacao no rodape).
-- =========================================================

-- ---------------------------------------------------------
-- 1. Tabela de catalogo
-- ---------------------------------------------------------
CREATE TABLE public.tb_1011_regime_uso (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(30)  NOT NULL UNIQUE,
    descricao       VARCHAR(100) NOT NULL,
    definicao       TEXT,
    ativo           BOOLEAN      NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.tb_1011_regime_uso IS 'Catalogo de Regime de Uso (GR1011 do GERAS) - forma de vinculo do Produtor com a Propriedade.';

-- ---------------------------------------------------------
-- 2. Trigger dedicada (padrao: uma por tabela, nao generica)
-- ---------------------------------------------------------
CREATE OR REPLACE FUNCTION public.trg_fn_tb_1011_regime_uso_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_tb_1011_regime_uso_atualizado_em
    BEFORE UPDATE ON public.tb_1011_regime_uso
    FOR EACH ROW
    EXECUTE FUNCTION public.trg_fn_tb_1011_regime_uso_atualizado_em();

-- ---------------------------------------------------------
-- 3. Seed - 9 valores oficiais (fonte: GR1011.TXT)
--    Definicao nula em Condomino (7) e Comodatario (8):
--    o export do GERAS nao trouxe texto para esses dois.
-- ---------------------------------------------------------
INSERT INTO public.tb_1011_regime_uso (codigo, descricao, definicao) VALUES
('PROPRIETARIO_UNICO',    'Proprietário Único',        'Dono com escritura.'),
('ARRENDATARIO',          'Arrendatário',               'Quem arrenda por indivíduo, pessoa física ou jurídica, que toma alguma coisa em arrendamento; inquilino, rendeiro.'),
('ESPOLIO',               'Espólio',                    'Conjunto de bens que forma o patrimônio do morto, a ser partilhado no inventário entre os herdeiros ou legatários; herança.'),
('ALUGUEL_PASTO',         'Aluguel de Pasto',           'Cedência ou aquisição do uso e gozo de qualquer coisa móvel ou imóvel, ou prestação de serviços, por tempo e preço determinados, mediante contrato; arrendamento, locação.'),
('CONFINAMENTO_BOITEL',   'Confinamento (Boitel)',      'Ato ou efeito de isolar em determinado lugar.'),
('POSSEIRO',              'Posseiro',                   'Estado de quem possui uma coisa, que a detém como sua ou tem o gozo dela.'),
('CONDOMINO',             'Condômino',                  NULL),
('COMODATARIO',           'Comodatário',                NULL),
('OUTROS',                'Outros',                     'Qualquer outra atividade não citada anteriormente.');

-- ---------------------------------------------------------
-- 4. Nova FK em propriedade_produtor
--    OBS: tipo_vinculo (String(30) antigo) NAO foi removida
--    nesta versao - fica como coluna morta ate confirmarmos
--    que nada mais le/escreve nela, para nao quebrar nada
--    silenciosamente. Remocao entra como pendencia separada.
-- ---------------------------------------------------------
ALTER TABLE public.propriedade_produtor
    ADD COLUMN id_regime_uso INTEGER REFERENCES public.tb_1011_regime_uso(id);

CREATE INDEX ix_propriedade_produtor_id_regime_uso
    ON public.propriedade_produtor (id_regime_uso);

-- =========================================================
-- FIM DE ARQUIVO: sql_criacao_tb_1011_regime_uso.sql
-- =========================================================