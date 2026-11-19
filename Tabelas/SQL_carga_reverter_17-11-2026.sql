-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\Orion\Tabelas
-- MODULO: SQL_carga_reverter_17-11-2026.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-11-17 18:02 -03
-- VERSAO: 1.0.0
-- DESCRICAO: Desfaz o SQL_carga_passo2_indices_17-11-2026.sql: apaga o indice da Carga e devolve o indice
--   geral ao molde anterior (serie diferente de NAS). Nenhum dado e tocado.
--   Se algum schema ja tiver GTA com serie 'CAR' (Carga feita), o script PARA: desfaca as Cargas antes.
--   (Os valores CARGA dos ENUMs nao se removem; ficam sem uso.)
-- =========================================================

DO $$
DECLARE s text; n bigint;
BEGIN
  FOR s IN SELECT nspname FROM pg_namespace WHERE nspname ~ '^produtor_[0-9]+$' ORDER BY nspname LOOP
    IF to_regclass(format('%I.tb_4001_gta', s)) IS NULL THEN CONTINUE; END IF;
    EXECUTE format('SELECT count(*) FROM %I.tb_4001_gta WHERE serie_gta = ''CAR''', s) INTO n;
    IF n > 0 THEN
      RAISE EXCEPTION 'Schema % tem % GTA com serie CAR - desfaca as Cargas antes de reverter. NADA foi alterado.', s, n;
    END IF;
  END LOOP;

  FOR s IN SELECT nspname FROM pg_namespace WHERE nspname ~ '^produtor_[0-9]+$' ORDER BY nspname LOOP
    IF to_regclass(format('%I.tb_4001_gta', s)) IS NULL THEN CONTINUE; END IF;
    EXECUTE format('DROP INDEX IF EXISTS %I.uq_tb_4001_gta_carga_propriedade', s);
    EXECUTE format('DROP INDEX IF EXISTS %I.uq_tb_4001_gta_uf_serie_numero_sentido', s);
    EXECUTE format('CREATE UNIQUE INDEX uq_tb_4001_gta_uf_serie_numero_sentido ON %I.tb_4001_gta (uf_gta, serie_gta, numero_gta_sequencial, sentido) WHERE serie_gta <> ''NAS''', s);
  END LOOP;
END $$;

-- Conferencia: esperado 2 indices por schema (geral e nas_propriedade_numero)
SELECT schemaname, indexname FROM pg_indexes
 WHERE tablename = 'tb_4001_gta' AND indexname LIKE 'uq\_tb\_4001\_gta%'
 ORDER BY schemaname, indexname;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\SQL_carga_reverter_17-11-2026.sql
-- =========================================================
