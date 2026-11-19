-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\criar_morte_s111_b.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-11-01 16:40 -03
-- ATUALIZADO EM: 2026-11-01 16:40 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--   Sessao 111 - SAIDAS / MORTE (pacote 1, ajuste). Roda DEPOIS de criar_morte_s111.sql. Em TODOS os schemas produtor_NNNNN:
--     1) cria tb_2013_com_morte (Controle Interno MRT, espelho da tb_2013 do GERAS), unica por (propriedade, controle);
--     2) tb_2002_saida_animais: coluna id_comunicado -> id_com_morte INTEGER REFERENCES tb_2013_com_morte(id) + indice;
--     3) tira a coluna controle_morte (e seu indice) criada no script anterior, SO se nenhuma linha a usa (senao PULA com aviso).
--   A versao do banco continua 6. Pode rodar mais de uma vez.
--
--   v1.0.0: Criacao (Sessao 111).
--   REVERSAO: ALTER TABLE produtor_NNNNN.tb_2002_saida_animais DROP COLUMN id_com_morte; DROP TABLE produtor_NNNNN.tb_2013_com_morte;
-- =========================================================

DO $blk$
DECLARE
    esquema text;
    em_uso  integer;
BEGIN
    FOR esquema IN
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'produtor\_%'
        ORDER BY schema_name
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = esquema AND table_name = 'tb_2002_saida_animais' AND column_name = 'controle_morte')
           OR EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = esquema AND table_name = 'tb_2002_saida_animais') THEN

            EXECUTE format($t$
                CREATE TABLE IF NOT EXISTS %1$I.tb_2013_com_morte (
                    id                SERIAL PRIMARY KEY,
                    id_propriedade    INTEGER NOT NULL REFERENCES public.propriedades(id),
                    controle          INTEGER NOT NULL,
                    numero_comunicado INTEGER,
                    data_morte        DATE NOT NULL,
                    qtd_animais       INTEGER NOT NULL DEFAULT 0,
                    origem            VARCHAR(12) NOT NULL DEFAULT 'INDIVIDUAL',
                    id_usuario        INTEGER,
                    criado_em         TIMESTAMP NOT NULL DEFAULT now(),
                    atualizado_em     TIMESTAMP NOT NULL DEFAULT now(),
                    CONSTRAINT uq_tb_2013_propriedade_controle UNIQUE (id_propriedade, controle)
                )$t$, esquema);

            EXECUTE format('ALTER TABLE %I.tb_2002_saida_animais ADD COLUMN IF NOT EXISTS id_com_morte INTEGER REFERENCES %I.tb_2013_com_morte(id)', esquema, esquema);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_tb_2002_com_morte ON %I.tb_2002_saida_animais (id_com_morte)', esquema);

            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = esquema AND table_name = 'tb_2002_saida_animais' AND column_name = 'controle_morte') THEN
                EXECUTE format('SELECT count(*) FROM %I.tb_2002_saida_animais WHERE controle_morte IS NOT NULL', esquema) INTO em_uso;
                IF em_uso = 0 THEN
                    EXECUTE format('DROP INDEX IF EXISTS %I.idx_tb_2002_controle_morte', esquema);
                    EXECUTE format('ALTER TABLE %I.tb_2002_saida_animais DROP COLUMN controle_morte', esquema);
                    RAISE NOTICE '% -> tb_2013_com_morte OK, id_com_morte OK, controle_morte removida', esquema;
                ELSE
                    RAISE WARNING '% -> controle_morte TEM % linha(s) em uso: NAO removida', esquema, em_uso;
                END IF;
            ELSE
                RAISE NOTICE '% -> tb_2013_com_morte OK, id_com_morte OK', esquema;
            END IF;
        ELSE
            RAISE WARNING '% -> PULADO (falta tb_2002_saida_animais)', esquema;
        END IF;
    END LOOP;
END $blk$;

-- =========================================================
-- CONFERENCIA (rodar uma de cada vez; o pgAdmin mostra so o ultimo comando)
-- Esperado: uma linha por schema, com true / true / false (controle_morte ja removida).
-- SELECT s.schema_name,
--        EXISTS (SELECT 1 FROM information_schema.tables t WHERE t.table_schema = s.schema_name AND t.table_name = 'tb_2013_com_morte') AS tabela_2013,
--        EXISTS (SELECT 1 FROM information_schema.columns c WHERE c.table_schema = s.schema_name AND c.table_name = 'tb_2002_saida_animais' AND c.column_name = 'id_com_morte') AS coluna_id_com_morte,
--        EXISTS (SELECT 1 FROM information_schema.columns c WHERE c.table_schema = s.schema_name AND c.table_name = 'tb_2002_saida_animais' AND c.column_name = 'controle_morte') AS coluna_antiga
--   FROM information_schema.schemata s WHERE s.schema_name LIKE 'produtor\_%' ORDER BY s.schema_name;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\criar_morte_s111_b.sql
-- =========================================================
