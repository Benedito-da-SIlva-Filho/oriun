-- =========================================================
-- PROJETO:      Orion
-- PASTA:        C:\orion\Tabelas
-- MODULO:       Tabelas\criar_linkagem_s120.sql
-- AUTOR:        Benedito Silva Filho
-- CRIADO EM:    2026-11-10 18:20 -03
-- VERSAO:       1.0.0
--
-- DESCRICAO:
--     Linkagem RFID e Brinco, pacote 1 - Sessao 120. Para TODOS os schemas produtor_NNNNN:
--       1) tb_4008_linkagem_inconformes (tentativas recusadas da Linkagem) + indice
--       2) tb_versao_schema = 9
--     Pode rodar mais de uma vez (IF NOT EXISTS).
--
-- REVERSAO (so se precisar; rodar por schema):
--     DROP TABLE IF EXISTS produtor_NNNNN.tb_4008_linkagem_inconformes;
--     UPDATE produtor_NNNNN.tb_versao_schema SET versao = 8 WHERE versao = 9;
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

        -- 1) inconformidades da Linkagem
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I.tb_4008_linkagem_inconformes ('
                       'id SERIAL PRIMARY KEY, '
                       'id_propriedade INTEGER NOT NULL REFERENCES public.propriedades(id), '
                       'id_usuario INTEGER, '
                       'rfid VARCHAR(40), '
                       'sisbov VARCHAR(40), '
                       'motivo VARCHAR(200) NOT NULL, '
                       'criado_em TIMESTAMP NOT NULL DEFAULT now())', s);
        EXECUTE format('CREATE INDEX IF NOT EXISTS ix_tb_4008_prop_criado '
                       'ON %I.tb_4008_linkagem_inconformes (id_propriedade, criado_em)', s);

        -- 2) versao do schema
        EXECUTE format('UPDATE %I.tb_versao_schema SET versao = 9 WHERE versao < 9', s);
        EXECUTE format('INSERT INTO %I.tb_versao_schema (versao) SELECT 9 '
                       'WHERE NOT EXISTS (SELECT 1 FROM %I.tb_versao_schema)', s, s);
    END LOOP;
END
$blk$;
