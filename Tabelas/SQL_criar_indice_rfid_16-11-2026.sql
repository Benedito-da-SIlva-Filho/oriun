-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\Orion\Tabelas
-- MODULO: SQL_criar_indice_rfid_16-11-2026.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-11-16 11:10 -03
-- VERSAO: 1.0.0
-- DESCRICAO: Etapa 7d da Auditoria - ALTERA O BANCO (1 indice por schema de Produtor). Reverter: SQL_reverter_indice_rfid_16-11-2026.sql
--   Indice unico parcial uq_tb_2001_rfid: o mesmo RFID so em UM animal do Produtor (Regra #74). RFID vazio/nulo nao conta.
--   ANTES de rodar: BACKUP do banco (Regra #24). Rodar UMA vez, no banco orion. Conferido em 16/11/2026: 0 RFID repetido.
--   Se algum schema tiver RFID repetido, o script PARA com aviso e nao cria nada.
-- =========================================================

DO $$
DECLARE s text; n bigint;
BEGIN
  FOR s IN SELECT nspname FROM pg_namespace WHERE nspname ~ '^produtor_[0-9]+$' ORDER BY nspname LOOP
    EXECUTE format('SELECT count(*) FROM (SELECT rfid FROM %I.tb_2001 WHERE rfid IS NOT NULL AND rfid <> '''' GROUP BY rfid HAVING count(*) > 1) x', s) INTO n;
    IF n > 0 THEN
      RAISE EXCEPTION 'Schema % tem % RFID repetido - rode o SQL_conferir_rfid_duplicado e corrija antes', s, n;
    END IF;
  END LOOP;
  FOR s IN SELECT nspname FROM pg_namespace WHERE nspname ~ '^produtor_[0-9]+$' ORDER BY nspname LOOP
    EXECUTE format('CREATE UNIQUE INDEX IF NOT EXISTS uq_tb_2001_rfid ON %I.tb_2001 (rfid) WHERE rfid IS NOT NULL AND rfid <> ''''', s);
    RAISE NOTICE 'indice criado em %', s;
  END LOOP;
END $$;

SELECT schemaname, indexname FROM pg_indexes WHERE indexname = 'uq_tb_2001_rfid' ORDER BY schemaname;

-- FIM DE ARQUIVO
