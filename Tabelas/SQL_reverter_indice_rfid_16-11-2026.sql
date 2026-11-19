-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\Orion\Tabelas
-- MODULO: SQL_reverter_indice_rfid_16-11-2026.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-11-16 11:10 -03
-- VERSAO: 1.0.0
-- DESCRICAO: Desfaz o SQL_criar_indice_rfid_16-11-2026.sql (apaga so o indice uq_tb_2001_rfid; nenhum dado e tocado).
-- =========================================================

DO $$
DECLARE s text;
BEGIN
  FOR s IN SELECT nspname FROM pg_namespace WHERE nspname ~ '^produtor_[0-9]+$' ORDER BY nspname LOOP
    EXECUTE format('DROP INDEX IF EXISTS %I.uq_tb_2001_rfid', s);
  END LOOP;
END $$;

-- FIM DE ARQUIVO
