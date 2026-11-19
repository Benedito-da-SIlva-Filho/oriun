-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\Orion\Tabelas
-- MODULO: SQL_carga_passo2_indices_17-11-2026.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-11-17 18:02 -03
-- ATUALIZADO EM: 2026-11-17 18:02 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--   CARGA - PASSO 2 de 2 (rodar DEPOIS do passo 1). ALTERA O BANCO: 2 indices por schema de Produtor.
--   A GTA da Carga usa a serie propria 'CAR' (numero_gta_completo = 'CARGA'), no mesmo molde da serie 'NAS'.
--   O que faz, em TODOS os schemas produtor_NNNNN (transacao unica):
--     1) uq_tb_4001_gta_uf_serie_numero_sentido (mesmo nome, e o gta_duplicada.py reconhece)
--        passa a valer so para GTA de verdade: serie diferente de NAS E de CAR.
--        (Sem isso, a GTA CAR de duas Propriedades da mesma UF bateria uma na outra.)
--     2) NOVO uq_tb_4001_gta_carga_propriedade em (id_propriedade) WHERE serie_gta = 'CAR':
--        UMA unica Carga por Propriedade (regra do Benedito, 17/11/2026). O Desfazer apaga a GTA CAR
--        e a Propriedade volta a poder receber uma nova Carga. O banco tambem diz "uma Carga so" (Regra #74).
--   Nao cria coluna nova: o lote da Carga e a propria GTA CAR (id_gta_entrada de cada animal, tipo_entrada = CARGA).
--   Nao apaga nem altera dados. Nao muda a versao do banco (so indices, como o uq_tb_2001_rfid).
--   SEGURANCA: se algum schema ja tiver GTA com serie 'CAR', o script PARA e nao altera nada.
--   ANTES de rodar: BACKUP do banco (Regra #24). Rodar UMA vez, no banco orion.
--   Reverter: SQL_carga_reverter_17-11-2026.sql
--
--   v1.0.0: Criacao.
-- =========================================================

DO $$
DECLARE s text; n bigint;
BEGIN
  FOR s IN SELECT nspname FROM pg_namespace WHERE nspname ~ '^produtor_[0-9]+$' ORDER BY nspname LOOP
    IF to_regclass(format('%I.tb_4001_gta', s)) IS NULL THEN CONTINUE; END IF;
    EXECUTE format('SELECT count(*) FROM %I.tb_4001_gta WHERE serie_gta = ''CAR''', s) INTO n;
    IF n > 0 THEN
      RAISE EXCEPTION 'Schema % ja tem % GTA com serie CAR - NADA foi alterado em nenhum schema. Conferir antes.', s, n;
    END IF;
  END LOOP;

  FOR s IN SELECT nspname FROM pg_namespace WHERE nspname ~ '^produtor_[0-9]+$' ORDER BY nspname LOOP
    IF to_regclass(format('%I.tb_4001_gta', s)) IS NULL THEN CONTINUE; END IF;
    -- 1) indice geral: GTA de verdade (serie diferente de NAS e de CAR)
    EXECUTE format('DROP INDEX IF EXISTS %I.uq_tb_4001_gta_uf_serie_numero_sentido', s);
    EXECUTE format('CREATE UNIQUE INDEX uq_tb_4001_gta_uf_serie_numero_sentido ON %I.tb_4001_gta (uf_gta, serie_gta, numero_gta_sequencial, sentido) WHERE serie_gta NOT IN (''NAS'', ''CAR'')', s);
    -- 2) Carga: uma por Propriedade
    EXECUTE format('CREATE UNIQUE INDEX IF NOT EXISTS uq_tb_4001_gta_carga_propriedade ON %I.tb_4001_gta (id_propriedade) WHERE serie_gta = ''CAR''', s);
    RAISE NOTICE 'indices da Carga OK em %', s;
  END LOOP;
END $$;

-- =========================================================
-- CONFERENCIA (rodar uma de cada vez)
-- =========================================================

-- 1) Esperado: 3 indices por schema (geral, nas_propriedade_numero e carga_propriedade)
SELECT schemaname, indexname FROM pg_indexes
 WHERE tablename = 'tb_4001_gta' AND indexname LIKE 'uq\_tb\_4001\_gta%'
 ORDER BY schemaname, indexname;

-- 2) Esperado: o indice geral com WHERE (serie_gta NOT IN ('NAS','CAR')) e o da Carga com WHERE (serie_gta = 'CAR')
SELECT schemaname, indexname, indexdef FROM pg_indexes
 WHERE tablename = 'tb_4001_gta' AND indexname IN ('uq_tb_4001_gta_uf_serie_numero_sentido', 'uq_tb_4001_gta_carga_propriedade')
 ORDER BY schemaname, indexname;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\SQL_carga_passo2_indices_17-11-2026.sql
-- =========================================================
