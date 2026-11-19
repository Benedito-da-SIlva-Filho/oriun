-- =========================================================
-- PROJETO:      Orion
-- PASTA:        C:\orion\Tabelas
-- MODULO:       Tabelas\criar_linkagem_s120_b.sql
-- AUTOR:        Benedito Silva Filho
-- CRIADO EM:    2026-11-10 21:10 -03
-- VERSAO:       1.0.0
--
-- DESCRICAO:
--     Linkagem RFID e Brinco, pacote 2 - Sessao 120. Para TODOS os schemas produtor_NNNNN:
--       1) tb_4009_linkagem (os pares RFID + SISBOV ligados: base da Consulta e do PDF) + indices
--       2) tb_versao_schema = 10
--     Rodar DEPOIS do criar_linkagem_s120.sql (tb_4008). Pode rodar mais de uma vez (IF NOT EXISTS).
--
-- REVERSAO (so se precisar; rodar por schema):
--     DROP TABLE IF EXISTS produtor_NNNNN.tb_4009_linkagem;
--     UPDATE produtor_NNNNN.tb_versao_schema SET versao = 9 WHERE versao = 10;
-- =========================================================

DO $blk$
DECLARE
    s text;
BEGIN
    FOR s IN
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'produtor\_%'
        ORDER BY schema_name
    LOOP
        IF NOT (EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = s AND table_name = 'tb_2001')
            AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = s AND table_name = 'tb_versao_schema')) THEN
            RAISE WARNING '% -> PULADO (falta tb_2001 ou tb_versao_schema)', s;
            CONTINUE;
        END IF;

        -- 1) pares ligados
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I.tb_4009_linkagem ('
                       'id SERIAL PRIMARY KEY, '
                       'id_propriedade INTEGER NOT NULL REFERENCES public.propriedades(id), '
                       'id_usuario INTEGER, '
                       'sisbov VARCHAR(15) NOT NULL, '
                       'rfid VARCHAR(15) NOT NULL, '
                       'data_linkagem DATE NOT NULL, '
                       'hora_linkagem TIME, '
                       'lote VARCHAR(30), '
                       'peso NUMERIC(6,2), '
                       'criado_em TIMESTAMP NOT NULL DEFAULT now())', s);
        EXECUTE format('CREATE INDEX IF NOT EXISTS ix_tb_4009_prop_data '
                       'ON %I.tb_4009_linkagem (id_propriedade, data_linkagem)', s);
        EXECUTE format('CREATE INDEX IF NOT EXISTS ix_tb_4009_sisbov '
                       'ON %I.tb_4009_linkagem (sisbov)', s);

        -- 2) versao do schema
        EXECUTE format('UPDATE %I.tb_versao_schema SET versao = 10 WHERE versao < 10', s);
        EXECUTE format('INSERT INTO %I.tb_versao_schema (versao) SELECT 10 '
                       'WHERE NOT EXISTS (SELECT 1 FROM %I.tb_versao_schema)', s, s);
    END LOOP;
END
$blk$;
