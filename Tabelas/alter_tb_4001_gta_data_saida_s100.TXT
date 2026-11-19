-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\Orion\Tabelas
-- MODULO: alter_tb_4001_gta_data_saida_s100.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-10-19 17:05 -03
-- ATUALIZADO EM: 2026-10-19 17:05 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Cria a coluna data_saida (DATE, opcional) na tb_4001_gta de TODOS os
--     schemas produtor_NNNNN. Guarda a Data de Saida da GTA de Saida, digitada
--     na tela Vincular GTA / Embarque.
--     Produtores NOVOS recebem a coluna pelo Onboarding (model tb_4001_gta.py
--     v1.9.0), por isso este script e so para os que ja existem.
--
--     PASSO 1 - cria a coluna (pode rodar mais de uma vez, nao estraga nada).
--     PASSO 2 - (OPCIONAL) so se voce ja testou o Vincular GTA v1.0.0: move a
--               data que ficou em data_entrega das GTAs de SAIDA para data_saida.
--     PASSO 3 - conferencia (rodar uma de cada vez).
--
--     v1.0.0: Criacao (Sessao 100).
--     REVERSAO: ALTER TABLE produtor_NNNNN.tb_4001_gta DROP COLUMN data_saida;
-- =========================================================

-- ---------------------------------------------------------
-- PASSO 1 - CRIAR A COLUNA EM TODOS OS SCHEMAS
-- ---------------------------------------------------------
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT table_schema AS esquema
          FROM information_schema.tables
         WHERE table_schema LIKE 'produtor\_%'
           AND table_name = 'tb_4001_gta'
         ORDER BY table_schema
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_schema = r.esquema
                      AND table_name = 'tb_4001_gta'
                      AND column_name = 'data_saida') THEN
            RAISE NOTICE '% - ja tinha data_saida (nada feito)', r.esquema;
        ELSE
            EXECUTE format('ALTER TABLE %I.tb_4001_gta ADD COLUMN IF NOT EXISTS data_saida DATE', r.esquema);
            RAISE NOTICE '% - coluna data_saida CRIADA', r.esquema;
        END IF;
    END LOOP;
END $$;

-- ---------------------------------------------------------
-- PASSO 2 - OPCIONAL: mover data_entrega -> data_saida (somente GTAs de SAIDA)
-- So rode se voce ja vinculou GTA com o Vincular v1.0.0 (que gravava em data_entrega).
-- ---------------------------------------------------------
DO $$
DECLARE
    r RECORD;
    qtde INTEGER;
BEGIN
    FOR r IN
        SELECT table_schema AS esquema
          FROM information_schema.tables
         WHERE table_schema LIKE 'produtor\_%'
           AND table_name = 'tb_4001_gta'
         ORDER BY table_schema
    LOOP
        EXECUTE format(
            'UPDATE %I.tb_4001_gta
                SET data_saida = data_entrega, data_entrega = NULL
              WHERE sentido = ''SAIDA'' AND data_entrega IS NOT NULL AND data_saida IS NULL',
            r.esquema);
        GET DIAGNOSTICS qtde = ROW_COUNT;
        RAISE NOTICE '% - GTAs de saida movidas: %', r.esquema, qtde;
    END LOOP;
END $$;

-- ---------------------------------------------------------
-- PASSO 3 - CONFERENCIA (rodar UMA de cada vez)
-- ---------------------------------------------------------

-- 3.1 Todo schema com tb_4001_gta deve mostrar "sim":
SELECT t.table_schema AS esquema,
       CASE WHEN c.column_name IS NULL THEN 'NAO' ELSE 'sim' END AS tem_data_saida,
       c.data_type AS tipo
  FROM information_schema.tables t
  LEFT JOIN information_schema.columns c
         ON c.table_schema = t.table_schema AND c.table_name = t.table_name
        AND c.column_name = 'data_saida'
 WHERE t.table_schema LIKE 'produtor\_%' AND t.table_name = 'tb_4001_gta'
 ORDER BY t.table_schema;

-- 3.2 Ninguem deve ter GTA de SAIDA com data_entrega preenchida (deve voltar 0 linhas),
--     troque produtor_00004 pelo schema que quiser conferir:
SELECT id, numero_gta_completo, data_entrega, data_saida
  FROM produtor_00004.tb_4001_gta
 WHERE sentido = 'SAIDA' AND data_entrega IS NOT NULL;

-- 3.3 GTAs de saida e suas datas de saida (produtor_00004):
SELECT id, numero_gta_completo, data_emissao, data_validade, data_saida, numero_comunicado
  FROM produtor_00004.tb_4001_gta
 WHERE sentido = 'SAIDA'
 ORDER BY id;

-- =========================================================
-- FIM DE ARQUIVO
-- =========================================================
