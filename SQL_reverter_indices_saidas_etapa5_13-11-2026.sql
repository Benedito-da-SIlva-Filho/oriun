-- SQL_reverter_indices_saidas_etapa5_13-11-2026.sql  (versao 1.0.0)
-- Desfaz o SQL_criar_indices_saidas_etapa5_13-11-2026.sql (apaga so os 3 indices; nenhum dado e tocado).
DO $$
DECLARE s text;
BEGIN
  FOR s IN SELECT nspname FROM pg_namespace WHERE nspname ~ '^produtor_[0-9]+$' ORDER BY nspname LOOP
    EXECUTE format('DROP INDEX IF EXISTS %I.uq_tb_2002_animal_valido', s);
    EXECUTE format('DROP INDEX IF EXISTS %I.uq_tb_2002_embarque_valido', s);
    EXECUTE format('DROP INDEX IF EXISTS %I.uq_tb_3008_sisbov', s);
  END LOOP;
END $$;
