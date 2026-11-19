-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\alterar_tb_2020_2002_elemento_s098.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-10-16 19:55 -03
-- ATUALIZADO EM: 2026-10-16 19:55 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--   Sessao 098 - SAIDAS (Leitor do Abate). Cria a coluna ELEMENTO nas duas
--   tabelas do embarque, em TODOS os schemas produtor_NNNNN:
--     tb_2020_embarque       (leitura no brete)
--     tb_2002_saida_animais  (animal depois da saida)
--   ELEMENTO = qual elemento de identificacao o animal NAO tem mais:
--   vazio (NULL) = tem os dois (brinco e botton), caso normal; 'BOTTON' ou
--   'BRINCO' so quando o brete escolhe (Leitor oferece Botton, Manejo oferece
--   Brinco). CHECK no banco aceita so NULL, BOTTON ou BRINCO.
--   Sobe a versao do banco (tb_versao_schema) para 4, junto com
--   VERSAO_SCHEMA_ATUAL = 4 do backup_helper.py v1.6.0.
--   Pode rodar mais de uma vez sem estragar nada (IF NOT EXISTS; a versao so
--   sobe). Schema sem tb_2020_embarque, tb_2002_saida_animais ou
--   tb_versao_schema e PULADO com aviso (WARNING): rode antes o script
--   criar_tb_2020_2002_2011_s098.sql. Nada existente e apagado.
--   RODAR ANTES de instalar os arquivos .py.
--
--   v1.0.0: Criacao (Sessao 098).
-- =========================================================

DO $blk$
DECLARE
    esquema text;
BEGIN
    FOR esquema IN
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'produtor\_%'
        ORDER BY schema_name
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = esquema AND table_name = 'tb_2020_embarque')
           AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = esquema AND table_name = 'tb_2002_saida_animais')
           AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = esquema AND table_name = 'tb_versao_schema') THEN

            EXECUTE format('ALTER TABLE %I.tb_2020_embarque ADD COLUMN IF NOT EXISTS elemento VARCHAR(10)', esquema);
            EXECUTE format('ALTER TABLE %I.tb_2002_saida_animais ADD COLUMN IF NOT EXISTS elemento VARCHAR(10)', esquema);

            -- CHECKs (nomes iguais aos do onboarding.py)
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_tb_2020_elemento' AND conrelid = format('%I.tb_2020_embarque', esquema)::regclass) THEN
                EXECUTE format('ALTER TABLE %I.tb_2020_embarque ADD CONSTRAINT chk_tb_2020_elemento CHECK (elemento IS NULL OR elemento IN (''BOTTON'', ''BRINCO''))', esquema);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_tb_2002_elemento' AND conrelid = format('%I.tb_2002_saida_animais', esquema)::regclass) THEN
                EXECUTE format('ALTER TABLE %I.tb_2002_saida_animais ADD CONSTRAINT chk_tb_2002_elemento CHECK (elemento IS NULL OR elemento IN (''BOTTON'', ''BRINCO''))', esquema);
            END IF;

            -- versao do banco = 4
            EXECUTE format('UPDATE %I.tb_versao_schema SET versao = 4 WHERE versao < 4', esquema);
            EXECUTE format('INSERT INTO %I.tb_versao_schema (versao) SELECT 4 WHERE NOT EXISTS (SELECT 1 FROM %I.tb_versao_schema)', esquema, esquema);

            RAISE NOTICE '% -> coluna elemento OK e versao 4 OK', esquema;
        ELSE
            RAISE WARNING '% -> PULADO (falta tb_2020_embarque, tb_2002_saida_animais ou tb_versao_schema)', esquema;
        END IF;
    END LOOP;
END $blk$;

-- =========================================================
-- CONFERENCIA (rodar depois; o resultado esperado esta em cada comentario)
-- =========================================================

-- 1) Colunas por tabela em cada schema. Esperado: tb_2020_embarque = 40, tb_2002_saida_animais = 53
SELECT table_schema, table_name, count(*) AS colunas
  FROM information_schema.columns
 WHERE table_name IN ('tb_2020_embarque','tb_2002_saida_animais')
   AND table_schema LIKE 'produtor\_%'
 GROUP BY table_schema, table_name ORDER BY table_schema, table_name;

-- 2) Versao do banco em cada schema. Esperado: 4
SELECT table_schema,
       (xpath('/row/versao/text()', query_to_xml(format('SELECT versao FROM %I.tb_versao_schema', table_schema), false, true, '')))[1]::text AS versao
  FROM information_schema.tables
 WHERE table_name = 'tb_versao_schema' AND table_schema LIKE 'produtor\_%'
 ORDER BY table_schema;

-- 3) Travas. Esperado: 2 CHECKs por schema
SELECT n.nspname AS schema, c.conname FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace
 WHERE c.conname IN ('chk_tb_2020_elemento','chk_tb_2002_elemento')
 ORDER BY 1, 2;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\alterar_tb_2020_2002_elemento_s098.sql
-- =========================================================
