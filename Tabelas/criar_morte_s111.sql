-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\criar_morte_s111.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-11-01 16:30 -03
-- ATUALIZADO EM: 2026-11-01 16:30 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--   Sessao 111 - SAIDAS / MORTE (pacote 1: preparacao). Em TODOS os schemas produtor_NNNNN:
--     1) tb_2002_saida_animais: coluna controle_morte VARCHAR(12) (Controle Interno MRT000118) + indice (id_propriedade, controle_morte);
--     2) tb_2021_notificacao_morte (nova): Notificacao de Morte (Anexo XXII), 1 linha por Notificacao; unica por (propriedade, numero);
--     3) tb_2022_morte_fotos (nova): ate 2 fotos por animal morto; FK para tb_2002 com ON DELETE CASCADE (o Desfazer apaga junto);
--     4) tb_versao_schema = 6 (junto com VERSAO_SCHEMA_ATUAL = 6 do backup_helper.py v1.9.0).
--   Pode rodar mais de uma vez (IF NOT EXISTS; a versao so sobe). Schema sem tb_2002 ou tb_versao_schema e PULADO com aviso.
--   RODAR ANTES de instalar os arquivos .py. Nenhum dado existente e alterado.
--
--   v1.0.0: Criacao (Sessao 111).
--   REVERSAO: DROP TABLE produtor_NNNNN.tb_2022_morte_fotos; DROP TABLE produtor_NNNNN.tb_2021_notificacao_morte;
--             DROP INDEX produtor_NNNNN.idx_tb_2002_controle_morte; ALTER TABLE produtor_NNNNN.tb_2002_saida_animais DROP COLUMN controle_morte;
--             e voltar tb_versao_schema para 5.
-- =========================================================

DO $blk$
DECLARE
    esquema text;
BEGIN
    FOR esquema IN
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'produtor\_%'
        ORDER BY schema_name
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = esquema AND table_name = 'tb_2002_saida_animais')
           AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = esquema AND table_name = 'tb_versao_schema') THEN

            EXECUTE format('ALTER TABLE %I.tb_2002_saida_animais ADD COLUMN IF NOT EXISTS controle_morte VARCHAR(12)', esquema);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_tb_2002_controle_morte ON %I.tb_2002_saida_animais (id_propriedade, controle_morte)', esquema);

            EXECUTE format($t$
                CREATE TABLE IF NOT EXISTS %1$I.tb_2021_notificacao_morte (
                    id                   SERIAL PRIMARY KEY,
                    id_propriedade       INTEGER NOT NULL REFERENCES public.propriedades(id),
                    numero_comunicado    INTEGER NOT NULL,
                    qtd_animais          INTEGER NOT NULL DEFAULT 0,
                    status               VARCHAR(20) NOT NULL DEFAULT 'ABERTO',
                    data_envio           DATE,
                    impresso_em          TIMESTAMP,
                    id_usuario_impressao INTEGER,
                    id_usuario_geracao   INTEGER,
                    criado_em            TIMESTAMP NOT NULL DEFAULT now(),
                    atualizado_em        TIMESTAMP NOT NULL DEFAULT now(),
                    CONSTRAINT uq_tb_2021_propriedade_numero UNIQUE (id_propriedade, numero_comunicado)
                )$t$, esquema);

            EXECUTE format($t$
                CREATE TABLE IF NOT EXISTS %1$I.tb_2022_morte_fotos (
                    id               SERIAL PRIMARY KEY,
                    id_saida_animal  INTEGER NOT NULL REFERENCES %1$I.tb_2002_saida_animais(id) ON DELETE CASCADE,
                    ordem            INTEGER NOT NULL,
                    arquivo_nome     VARCHAR(120) NOT NULL,
                    nome_original    VARCHAR(200),
                    tamanho_bytes    INTEGER,
                    hash_sha256      VARCHAR(64),
                    id_usuario       INTEGER,
                    criado_em        TIMESTAMP NOT NULL DEFAULT now(),
                    CONSTRAINT uq_tb_2022_animal_ordem UNIQUE (id_saida_animal, ordem)
                )$t$, esquema);

            -- versao do banco = 6
            EXECUTE format('UPDATE %I.tb_versao_schema SET versao = 6 WHERE versao < 6', esquema);
            EXECUTE format('INSERT INTO %I.tb_versao_schema (versao) SELECT 6 WHERE NOT EXISTS (SELECT 1 FROM %I.tb_versao_schema)', esquema, esquema);

            RAISE NOTICE '% -> Morte OK (coluna, 2 tabelas) e versao 6 OK', esquema;
        ELSE
            RAISE WARNING '% -> PULADO (falta tb_2002_saida_animais ou tb_versao_schema)', esquema;
        END IF;
    END LOOP;
END $blk$;

-- =========================================================
-- CONFERENCIA (rodar uma de cada vez; o pgAdmin mostra so o ultimo comando)
-- =========================================================
-- 1) Esperado: uma linha por schema, com 'sim' nas 3 colunas e versao 6.
-- SELECT s.schema_name,
--        EXISTS (SELECT 1 FROM information_schema.columns c WHERE c.table_schema = s.schema_name AND c.table_name = 'tb_2002_saida_animais' AND c.column_name = 'controle_morte') AS coluna_controle,
--        EXISTS (SELECT 1 FROM information_schema.tables t WHERE t.table_schema = s.schema_name AND t.table_name = 'tb_2021_notificacao_morte') AS tabela_notificacao,
--        EXISTS (SELECT 1 FROM information_schema.tables t WHERE t.table_schema = s.schema_name AND t.table_name = 'tb_2022_morte_fotos') AS tabela_fotos,
--        (xpath('/row/v/text()', query_to_xml(format('SELECT max(versao) AS v FROM %I.tb_versao_schema', s.schema_name), false, true, '')))[1]::text AS versao
--   FROM information_schema.schemata s WHERE s.schema_name LIKE 'produtor\_%' ORDER BY s.schema_name;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\criar_morte_s111.sql
-- =========================================================
