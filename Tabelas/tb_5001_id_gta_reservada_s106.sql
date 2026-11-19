-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\tb_5001_id_gta_reservada_s106.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-10-26 14:30 -03
-- ATUALIZADO EM: 2026-10-26 14:30 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Sessao 106 - Brincagem com Leitor, caso 1 (GTA de Compra PENDENTE escolhida na selecao).
--     Nova coluna tb_5001_brincagem.id_gta_reservada (INTEGER, NULL, FK tb_4001_gta) em TODOS os
--     schemas produtor_NNNNN: guarda a leitura do brete reservada a uma GTA ainda nao brincada.
--     Pode rodar mais de uma vez sem erro (IF NOT EXISTS). NAO apaga nem altera dados.
--
--   v1.0.0: Criacao (Sessao 106). REVERSAO: ALTER TABLE ... DROP COLUMN id_gta_reservada (so se ninguem usou).
-- =========================================================

DO $$
DECLARE
    schema_rec RECORD;
BEGIN
    FOR schema_rec IN
        SELECT schema_name
          FROM information_schema.schemata
         WHERE schema_name LIKE 'produtor_%'
         ORDER BY schema_name
    LOOP
        IF EXISTS (
            SELECT 1 FROM information_schema.tables
             WHERE table_schema = schema_rec.schema_name AND table_name = 'tb_5001_brincagem'
        ) AND EXISTS (
            SELECT 1 FROM information_schema.tables
             WHERE table_schema = schema_rec.schema_name AND table_name = 'tb_4001_gta'
        ) THEN
            EXECUTE format(
                'ALTER TABLE %I.tb_5001_brincagem '
                'ADD COLUMN IF NOT EXISTS id_gta_reservada INTEGER REFERENCES %I.tb_4001_gta(id)',
                schema_rec.schema_name, schema_rec.schema_name
            );
        END IF;
    END LOOP;
END $$;

-- Conferencia (deve listar uma linha por produtor):
SELECT table_schema, column_name, data_type
  FROM information_schema.columns
 WHERE table_name = 'tb_5001_brincagem' AND column_name = 'id_gta_reservada'
 ORDER BY table_schema;
