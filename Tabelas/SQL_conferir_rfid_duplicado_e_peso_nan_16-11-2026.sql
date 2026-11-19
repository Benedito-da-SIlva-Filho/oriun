-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\Orion\XX Orion
-- MODULO: SQL_conferir_rfid_duplicado_e_peso_nan_16-11-2026.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-11-16 10:55 -03
-- VERSAO: 1.0.0
-- DESCRICAO: Etapa 7c da Auditoria - SO CONFERE (nao altera nada).
--   1) RFID repetido em animais (tb_2001) em TODOS os schemas produtor_NNNNN.
--      Resultado vazio = pode criar o indice unico no banco (Regra #74).
--   2) Pesos gravados como NaN (tb_4003_pesos) em TODOS os schemas - bug do "nan" corrigido na Etapa 7c.
-- COMO USAR: rodar o script inteiro no pgAdmin (mesma janela); o resultado sai nas duas ultimas consultas.
-- =========================================================

DROP TABLE IF EXISTS tmp_conf_rfid;
DROP TABLE IF EXISTS tmp_conf_nan;
CREATE TEMP TABLE tmp_conf_rfid (schema_nome text, rfid text, qtde bigint, sisbovs text);
CREATE TEMP TABLE tmp_conf_nan  (schema_nome text, id_peso bigint, sisbov text, data_pesagem date);

DO $$
DECLARE s record;
BEGIN
  FOR s IN SELECT schema_name FROM information_schema.schemata WHERE schema_name ~ '^produtor_[0-9]+$' ORDER BY 1 LOOP
    EXECUTE format(
      'INSERT INTO tmp_conf_rfid SELECT %L, rfid, count(*), string_agg(sisbov, '', '') FROM %I.tb_2001 '
      'WHERE rfid IS NOT NULL AND rfid <> '''' GROUP BY rfid HAVING count(*) > 1', s.schema_name, s.schema_name);
    EXECUTE format(
      'INSERT INTO tmp_conf_nan SELECT %L, id, sisbov, data_pesagem FROM %I.tb_4003_pesos WHERE peso = ''NaN''::numeric',
      s.schema_name, s.schema_name);
  END LOOP;
END $$;

-- 1) RFID repetido (esperado: 0 linhas)
SELECT * FROM tmp_conf_rfid ORDER BY schema_nome, rfid;

-- 2) Pesos NaN (esperado: 0 linhas)
SELECT * FROM tmp_conf_nan ORDER BY schema_nome, id_peso;

-- FIM DE ARQUIVO
