-- =========================================================
-- PROJETO:      Orion
-- PASTA:        C:\orion\Tabelas
-- MODULO:       Tabelas\criar_pesos_s114.sql
-- AUTOR:        Benedito Silva Filho
-- CRIADO EM:    2026-11-04 11:10 -03
-- VERSAO:       1.0.0
--
-- DESCRICAO:
--     Pesos pacote 1 (Leitor de Peso) - Sessao 114. Para TODOS os schemas produtor_NNNNN:
--       1) tb_4003_pesos.elemento_perdido  VARCHAR(10)  (BOTTON / BRINCO / NULL) + CHECK
--       2) tb_2001.elemento_perdido        VARCHAR(10)  (idem) + CHECK
--       3) tb_4007_pesagem_inconformes (tentativas recusadas do Leitor de Peso) + indice
--       4) tb_versao_schema = 7
--     Pode rodar mais de uma vez (IF NOT EXISTS / checagem de constraint).
--
-- REVERSAO (so se precisar; rodar por schema):
--     ALTER TABLE produtor_NNNNN.tb_4003_pesos DROP CONSTRAINT IF EXISTS chk_tb_4003_elemento_perdido;
--     ALTER TABLE produtor_NNNNN.tb_4003_pesos DROP COLUMN IF EXISTS elemento_perdido;
--     ALTER TABLE produtor_NNNNN.tb_2001 DROP CONSTRAINT IF EXISTS chk_tb_2001_elemento_perdido;
--     ALTER TABLE produtor_NNNNN.tb_2001 DROP COLUMN IF EXISTS elemento_perdido;
--     DROP TABLE IF EXISTS produtor_NNNNN.tb_4007_pesagem_inconformes;
--     UPDATE produtor_NNNNN.tb_versao_schema SET versao = 6 WHERE versao = 7;
-- =========================================================

DO $blk$
DECLARE
    s text;
BEGIN
    FOR s IN
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'produtor\_%'
        ORDER BY schema_name
    LOOP
        IF NOT (EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = s AND table_name = 'tb_4003_pesos')
            AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = s AND table_name = 'tb_2001')
            AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = s AND table_name = 'tb_versao_schema')) THEN
            RAISE WARNING '% -> PULADO (falta tb_4003_pesos, tb_2001 ou tb_versao_schema)', s;
            CONTINUE;
        END IF;

        -- 1) pesagem: elemento perdido
        EXECUTE format('ALTER TABLE %I.tb_4003_pesos ADD COLUMN IF NOT EXISTS elemento_perdido VARCHAR(10)', s);
        IF NOT EXISTS (SELECT 1 FROM pg_constraint
                       WHERE conname = 'chk_tb_4003_elemento_perdido'
                         AND conrelid = format('%I.tb_4003_pesos', s)::regclass) THEN
            EXECUTE format('ALTER TABLE %I.tb_4003_pesos ADD CONSTRAINT chk_tb_4003_elemento_perdido '
                           'CHECK (elemento_perdido IS NULL OR elemento_perdido IN (''BOTTON'', ''BRINCO''))', s);
        END IF;

        -- 2) animal: elemento perdido
        EXECUTE format('ALTER TABLE %I.tb_2001 ADD COLUMN IF NOT EXISTS elemento_perdido VARCHAR(10)', s);
        IF NOT EXISTS (SELECT 1 FROM pg_constraint
                       WHERE conname = 'chk_tb_2001_elemento_perdido'
                         AND conrelid = format('%I.tb_2001', s)::regclass) THEN
            EXECUTE format('ALTER TABLE %I.tb_2001 ADD CONSTRAINT chk_tb_2001_elemento_perdido '
                           'CHECK (elemento_perdido IS NULL OR elemento_perdido IN (''BOTTON'', ''BRINCO''))', s);
        END IF;

        -- 3) inconformes
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I.tb_4007_pesagem_inconformes ('
                       'id SERIAL PRIMARY KEY, '
                       'id_propriedade INTEGER NOT NULL REFERENCES public.propriedades(id), '
                       'id_usuario INTEGER, '
                       'sisbov VARCHAR(40), '
                       'manejo VARCHAR(10), '
                       'data_pesagem DATE, '
                       'peso_digitado VARCHAR(20), '
                       'motivo VARCHAR(200) NOT NULL, '
                       'criado_em TIMESTAMP NOT NULL DEFAULT now())', s);
        EXECUTE format('CREATE INDEX IF NOT EXISTS ix_tb_4007_prop_criado '
                       'ON %I.tb_4007_pesagem_inconformes (id_propriedade, criado_em)', s);

        -- 4) versao do schema
        EXECUTE format('UPDATE %I.tb_versao_schema SET versao = 7 WHERE versao < 7', s);
        EXECUTE format('INSERT INTO %I.tb_versao_schema (versao) SELECT 7 '
                       'WHERE NOT EXISTS (SELECT 1 FROM %I.tb_versao_schema)', s, s);
    END LOOP;
END
$blk$;

-- =========================================================
-- CONFERENCIA (rodar depois; esperado: todas as linhas com 1 coluna de cada e versao 7)
-- =========================================================
-- SELECT t.table_schema,
--        SUM((t.table_name = 'tb_4003_pesos'  AND c.column_name = 'elemento_perdido')::int) AS pesos_ok,
--        SUM((t.table_name = 'tb_2001'        AND c.column_name = 'elemento_perdido')::int) AS animal_ok
--   FROM information_schema.tables t
--   JOIN information_schema.columns c USING (table_schema, table_name)
--  WHERE t.table_schema LIKE 'produtor\_%' AND c.column_name = 'elemento_perdido'
--  GROUP BY t.table_schema ORDER BY 1;
-- SELECT table_schema FROM information_schema.tables
--  WHERE table_name = 'tb_4007_pesagem_inconformes' ORDER BY 1;
-- SELECT s.schema_name,
--        (xpath('/row/v/text()', query_to_xml(format('SELECT max(versao) AS v FROM %I.tb_versao_schema', s.schema_name), false, true, '')))[1]::text AS versao
--   FROM information_schema.schemata s WHERE s.schema_name LIKE 'produtor\_%' ORDER BY 1;   -- esperado: 7

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\criar_pesos_s114.sql
-- =========================================================
