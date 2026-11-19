-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\Orion\Tabelas
-- MODULO: alter_tb_2017_copia_fiel_s101.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-10-20 10:10 -03
-- ATUALIZADO EM: 2026-10-20 10:10 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Torna a tb_2017_movimentacoes COPIA FIEL da tb_2001 (decisao do Benedito,
--     20/10/2026): acrescenta, em TODOS os schemas produtor_NNNNN, as 6 colunas
--     que a tb_2001 tem e a tb_2017 nao tinha, e preenche o passado.
--
--     Colunas novas (todas opcionais, sem ForeignKey de proposito):
--         lote (varchar 30), data_brincagem (date), conferido_brete (boolean),
--         conferido_em (timestamp), id_origem (integer), id_gta_entrada (integer).
--
--     IMPORTANTE - ORDEM DE INSTALACAO: rodar este script ANTES de reiniciar o
--     Orion com os arquivos novos (a Entrada passa a gravar essas colunas).
--     Produtores NOVOS recebem as colunas pelo Onboarding (model tb_2017 v1.2.0).
--
--     PASSO 1 - cria as colunas (pode rodar mais de uma vez, nao estraga nada).
--     PASSO 2 - preenche a linha de Entrada de cada animal que ainda esta na tb_2001
--               (so linhas de Entrada, mesmo animal e mesmo SISBOV; so o que esta vazio).
--     PASSO 3 - conferencia (rodar uma de cada vez).
--
--     v1.0.0: Criacao (Sessao 101).
--     REVERSAO: ALTER TABLE produtor_NNNNN.tb_2017_movimentacoes DROP COLUMN lote,
--               DROP COLUMN data_brincagem, DROP COLUMN conferido_brete,
--               DROP COLUMN conferido_em, DROP COLUMN id_origem, DROP COLUMN id_gta_entrada;
--               (e devolver os .bak_antes_2017_copia_s101 dos arquivos .py).
-- =========================================================

-- ---------------------------------------------------------
-- PASSO 1 - CRIAR AS COLUNAS EM TODOS OS SCHEMAS
-- ---------------------------------------------------------
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT table_schema AS esquema
          FROM information_schema.tables
         WHERE table_schema LIKE 'produtor\_%'
           AND table_name = 'tb_2017_movimentacoes'
         ORDER BY table_schema
    LOOP
        EXECUTE format('ALTER TABLE %I.tb_2017_movimentacoes
                            ADD COLUMN IF NOT EXISTS lote VARCHAR(30),
                            ADD COLUMN IF NOT EXISTS data_brincagem DATE,
                            ADD COLUMN IF NOT EXISTS conferido_brete BOOLEAN,
                            ADD COLUMN IF NOT EXISTS conferido_em TIMESTAMP,
                            ADD COLUMN IF NOT EXISTS id_origem INTEGER,
                            ADD COLUMN IF NOT EXISTS id_gta_entrada INTEGER', r.esquema);
        RAISE NOTICE '% - colunas da copia fiel garantidas', r.esquema;
    END LOOP;
END $$;

-- ---------------------------------------------------------
-- PASSO 2 - PREENCHER O PASSADO a partir da tb_2001
-- So a linha de Entrada (tipo_saida vazio) do mesmo animal e do mesmo SISBOV,
-- e so onde a linha ainda nao foi preenchida (conferido_brete vazio).
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
           AND table_name = 'tb_2017_movimentacoes'
         ORDER BY table_schema
    LOOP
        EXECUTE format(
            'UPDATE %1$I.tb_2017_movimentacoes m
                SET lote = e.lote,
                    data_brincagem = e.data_brincagem,
                    conferido_brete = e.conferido_brete,
                    conferido_em = e.conferido_em,
                    id_origem = e.id_origem,
                    id_gta_entrada = e.id_gta_entrada
               FROM %1$I.tb_2001 e
              WHERE m.id_animal = e.id
                AND m.sisbov = e.sisbov
                AND m.tipo_saida IS NULL
                AND m.conferido_brete IS NULL',
            r.esquema);
        GET DIAGNOSTICS qtde = ROW_COUNT;
        RAISE NOTICE '% - linhas de Entrada preenchidas: %', r.esquema, qtde;
    END LOOP;
END $$;

-- ---------------------------------------------------------
-- PASSO 3 - CONFERENCIA (rodar UMA de cada vez)
-- ---------------------------------------------------------

-- 3a) As 6 colunas existem em todos os schemas? (esperado: 6 por schema)
SELECT table_schema, COUNT(*) AS colunas_novas
  FROM information_schema.columns
 WHERE table_schema LIKE 'produtor\_%'
   AND table_name = 'tb_2017_movimentacoes'
   AND column_name IN ('lote','data_brincagem','conferido_brete','conferido_em','id_origem','id_gta_entrada')
 GROUP BY table_schema
 ORDER BY table_schema;

-- 3b) Por schema: animais na tb_2001 que ficaram SEM linha de Entrada preenchida na tb_2017
--     (esperado: 0; se vier numero, me mande o resultado).
DO $$
DECLARE
    r RECORD;
    qtde INTEGER;
BEGIN
    FOR r IN
        SELECT table_schema AS esquema
          FROM information_schema.tables
         WHERE table_schema LIKE 'produtor\_%'
           AND table_name = 'tb_2017_movimentacoes'
         ORDER BY table_schema
    LOOP
        EXECUTE format(
            'SELECT COUNT(*) FROM %1$I.tb_2001 e
              WHERE NOT EXISTS (SELECT 1 FROM %1$I.tb_2017_movimentacoes m
                                 WHERE m.id_animal = e.id AND m.sisbov = e.sisbov
                                   AND m.tipo_saida IS NULL AND m.conferido_brete IS NOT NULL)',
            r.esquema) INTO qtde;
        RAISE NOTICE '% - animais sem Entrada preenchida na tb_2017: %', r.esquema, qtde;
    END LOOP;
END $$;
-- =========================================================
-- FIM DE ARQUIVO: alter_tb_2017_copia_fiel_s101.sql
-- =========================================================
