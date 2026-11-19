-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\alterar_posse_s115.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-11-05 11:13 -03
-- ATUALIZADO EM: 2026-11-05 11:13 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--   Sessao 115 - SAIDAS / ALTERACAO DE POSSE (pacote 1: preparacao do banco).
--   Mesma Propriedade (mesmo OESA), muda o Produtor. Documento: DTA.
--   O que faz:
--     PASSO 1 (rodar SOZINHO, antes do passo 2):
--       novo valor POSSE no ENUM public.tipo_movimento_gta_enum (tipo de movimento da GTA/DTA).
--     PASSO 2 (todos os schemas produtor_NNNNN, bloco DO $$):
--       a) tb_2011_com_saidas: colunas motivo_posse (VARCHAR 10) e justificativa_posse (TEXT), opcionais;
--       b) CHECK tipo_saida passa a aceitar POSSE em tb_2020_embarque, tb_2002_saida_animais e tb_2011_com_saidas;
--       c) nova trava chk_tb_2011_motivo_posse (VENDA / HERANCA ou vazio);
--       d) sobe a versao do banco (tb_versao_schema) para 8, junto com VERSAO_SCHEMA_ATUAL = 8 do backup_helper.py v1.11.0.
--   Nenhuma tabela nova e nenhum dado alterado. Pode rodar mais de uma vez sem estragar nada.
--   Schema sem as tabelas e PULADO com aviso (WARNING).
--   RODAR ANTES de instalar os arquivos .py.
--
--   v1.0.0: Criacao (Sessao 115).
--   REVERSAO (passo 2): ALTER TABLE produtor_NNNNN.tb_2011_com_saidas DROP COLUMN motivo_posse, DROP COLUMN justificativa_posse;
--             voltar os 3 CHECKs de tipo_saida para ('ABATE','VENDA','MORTE','TRANSFER'); DROP CONSTRAINT chk_tb_2011_motivo_posse;
--             tb_versao_schema volta para 7. (O valor POSSE do ENUM nao se remove; fica sem uso.)
-- =========================================================

-- =========================================================
-- PASSO 1 - rodar SOZINHO (selecione so esta linha e execute)
-- =========================================================
ALTER TYPE public.tipo_movimento_gta_enum ADD VALUE IF NOT EXISTS 'POSSE';

-- =========================================================
-- PASSO 2 - rodar depois (selecione o bloco DO inteiro e execute)
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
           AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = esquema AND table_name = 'tb_2011_com_saidas')
           AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = esquema AND table_name = 'tb_versao_schema') THEN

            -- a) colunas novas do Comunicado de Saida
            EXECUTE format('ALTER TABLE %I.tb_2011_com_saidas ADD COLUMN IF NOT EXISTS motivo_posse VARCHAR(10)', esquema);
            EXECUTE format('ALTER TABLE %I.tb_2011_com_saidas ADD COLUMN IF NOT EXISTS justificativa_posse TEXT', esquema);

            -- b) CHECK de tipo_saida aceita POSSE (apaga o antigo e recria; as linhas existentes continuam validas)
            EXECUTE format('ALTER TABLE %I.tb_2020_embarque DROP CONSTRAINT IF EXISTS chk_tb_2020_tipo_saida', esquema);
            EXECUTE format('ALTER TABLE %I.tb_2020_embarque ADD CONSTRAINT chk_tb_2020_tipo_saida CHECK (tipo_saida IN (''ABATE'', ''VENDA'', ''MORTE'', ''TRANSFER'', ''POSSE''))', esquema);
            EXECUTE format('ALTER TABLE %I.tb_2002_saida_animais DROP CONSTRAINT IF EXISTS chk_tb_2002_tipo_saida', esquema);
            EXECUTE format('ALTER TABLE %I.tb_2002_saida_animais ADD CONSTRAINT chk_tb_2002_tipo_saida CHECK (tipo_saida IN (''ABATE'', ''VENDA'', ''MORTE'', ''TRANSFER'', ''POSSE''))', esquema);
            EXECUTE format('ALTER TABLE %I.tb_2011_com_saidas DROP CONSTRAINT IF EXISTS chk_tb_2011_tipo_saida', esquema);
            EXECUTE format('ALTER TABLE %I.tb_2011_com_saidas ADD CONSTRAINT chk_tb_2011_tipo_saida CHECK (tipo_saida IN (''ABATE'', ''VENDA'', ''MORTE'', ''TRANSFER'', ''POSSE''))', esquema);

            -- c) trava do motivo
            EXECUTE format('ALTER TABLE %I.tb_2011_com_saidas DROP CONSTRAINT IF EXISTS chk_tb_2011_motivo_posse', esquema);
            EXECUTE format('ALTER TABLE %I.tb_2011_com_saidas ADD CONSTRAINT chk_tb_2011_motivo_posse CHECK (motivo_posse IS NULL OR motivo_posse IN (''VENDA'', ''HERANCA''))', esquema);

            -- d) versao do banco = 8
            EXECUTE format('UPDATE %I.tb_versao_schema SET versao = 8 WHERE versao < 8', esquema);
            EXECUTE format('INSERT INTO %I.tb_versao_schema (versao) SELECT 8 WHERE NOT EXISTS (SELECT 1 FROM %I.tb_versao_schema)', esquema, esquema);

            RAISE NOTICE '% -> Posse OK e versao 8 OK', esquema;
        ELSE
            RAISE WARNING '% -> PULADO (falta tb_2020_embarque, tb_2002_saida_animais, tb_2011_com_saidas ou tb_versao_schema)', esquema;
        END IF;
    END LOOP;
END $blk$;

-- =========================================================
-- CONFERENCIA (rodar uma de cada vez; o pgAdmin mostra so o ultimo comando)
-- =========================================================

-- 1) Valor novo no ENUM. Esperado: aparece POSSE no fim da lista
SELECT unnest(enum_range(NULL::public.tipo_movimento_gta_enum)) AS valor;

-- 2) Colunas novas. Esperado: 2 linhas por schema (motivo_posse e justificativa_posse)
SELECT table_schema, column_name, data_type, character_maximum_length
  FROM information_schema.columns
 WHERE table_name = 'tb_2011_com_saidas'
   AND column_name IN ('motivo_posse', 'justificativa_posse')
   AND table_schema LIKE 'produtor\_%'
 ORDER BY table_schema, column_name;

-- 3) Travas. Esperado: 4 linhas por schema; os 3 tipo_saida com POSSE e o motivo_posse com VENDA/HERANCA
SELECT n.nspname AS schema, c.conrelid::regclass AS tabela, c.conname, pg_get_constraintdef(c.oid) AS regra
  FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace
 WHERE c.conname IN ('chk_tb_2020_tipo_saida', 'chk_tb_2002_tipo_saida', 'chk_tb_2011_tipo_saida', 'chk_tb_2011_motivo_posse')
   AND n.nspname LIKE 'produtor\_%'
 ORDER BY n.nspname, c.conname;

-- 4) Versao do banco em cada schema. Esperado: 8
SELECT table_schema,
       (xpath('/row/versao/text()', query_to_xml(format('SELECT versao FROM %I.tb_versao_schema', table_schema), false, true, '')))[1]::text AS versao
  FROM information_schema.tables
 WHERE table_name = 'tb_versao_schema' AND table_schema LIKE 'produtor\_%'
 ORDER BY table_schema;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\alterar_posse_s115.sql
-- =========================================================
