-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\tb_5001_tipo_entrada_s082.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-09-29 20:05 -03
-- ATUALIZADO EM: 2026-09-29 20:05 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Sessao 082 - Pacote 3A. Nova coluna tb_5001_brincagem.
--     tipo_entrada (COMPRA / NASCIMENTO) em TODOS os schemas
--     produtor_NNNNN (Regras.txt secao 3).
--       - VARCHAR(10) NOT NULL DEFAULT 'COMPRA': as linhas que ja
--         existem viram COMPRA automaticamente (decisao de
--         Benedito, Sessao 082).
--       - CHECK chk_tb_5001_brincagem_tipo_entrada: so aceita
--         COMPRA ou NASCIMENTO (mesma lista fixa de
--         backend\utils\regras_sisbov.py v1.1.0).
--     Pode rodar mais de uma vez sem erro (IF NOT EXISTS e
--     checagem da constraint antes de criar).
--
--   v1.0.0: Criacao (Sessao 082).
-- =========================================================

DO $$
DECLARE
    schema_rec RECORD;
BEGIN
    FOR schema_rec IN
        SELECT schema_name
          FROM information_schema.schemata
         WHERE schema_name LIKE 'produtor_%'
         ORDER BY schema_name
    LOOP
        -- So mexe onde a tabela existe (schema recem-criado sem
        -- tabelas nao quebra o script).
        IF EXISTS (
            SELECT 1 FROM information_schema.tables
             WHERE table_schema = schema_rec.schema_name
               AND table_name   = 'tb_5001_brincagem'
        ) THEN
            EXECUTE format(
                'ALTER TABLE %I.tb_5001_brincagem '
                'ADD COLUMN IF NOT EXISTS tipo_entrada VARCHAR(10) NOT NULL DEFAULT ''COMPRA''',
                schema_rec.schema_name
            );

            IF NOT EXISTS (
                SELECT 1
                  FROM pg_constraint c
                  JOIN pg_namespace n ON n.oid = c.connamespace
                 WHERE c.conname = 'chk_tb_5001_brincagem_tipo_entrada'
                   AND n.nspname = schema_rec.schema_name
            ) THEN
                EXECUTE format(
                    'ALTER TABLE %I.tb_5001_brincagem '
                    'ADD CONSTRAINT chk_tb_5001_brincagem_tipo_entrada '
                    'CHECK (tipo_entrada IN (''COMPRA'', ''NASCIMENTO''))',
                    schema_rec.schema_name
                );
            END IF;

            RAISE NOTICE 'OK: %.tb_5001_brincagem', schema_rec.schema_name;
        END IF;
    END LOOP;
END $$;

-- ---------------------------------------------------------
-- CONFERENCIA: deve listar 1 linha por schema, todas com a
-- coluna tipo_entrada, default 'COMPRA'::character varying.
-- ---------------------------------------------------------
SELECT table_schema, column_name, data_type, character_maximum_length, column_default, is_nullable
  FROM information_schema.columns
 WHERE table_name  = 'tb_5001_brincagem'
   AND column_name = 'tipo_entrada'
 ORDER BY table_schema;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\tb_5001_tipo_entrada_s082.sql
-- =========================================================
