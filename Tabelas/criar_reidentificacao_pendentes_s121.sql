-- =========================================================
-- PROJETO:      Orion
-- PASTA:        C:\orion\Tabelas
-- MODULO:       Tabelas\criar_reidentificacao_pendentes_s121.sql
-- AUTOR:        Benedito Silva Filho
-- CRIADO EM:    2026-11-11 16:40 -03
-- VERSAO:       1.0.0
--
-- DESCRICAO:
--     REIDENTIFICACAO - NOVO MODELO (decisao do Benedito, 11/11/2026): o Produtor lanca os animais ao longo dos dias; eles ficam PENDENTES de
--     Notificacao (sem numero). Ao GERAR a Notificacao, todos os pendentes entram nela e ela recebe o numero (tb_6005 = a Notificacao).
--     Para TODOS os schemas produtor_NNNNN, em tb_6006_reidentificacao_com_baixa_itens:
--       1) id_pedido passa a aceitar vazio (animal pendente, ainda sem Notificacao)
--       2) colunas novas: id_propriedade, data_reidentificacao (cada animal tem a sua), id_usuario
--       3) animais ja gravados (se houver) recebem id_propriedade e data a partir do pedido
--       4) indice ix_tb_6006_prop (id_propriedade, id_pedido)
--       5) tb_versao_schema = 12
--     Pode rodar mais de uma vez. Rodar DEPOIS do criar_reidentificacao_s121.sql (versao 11).
--
-- REVERSAO (so se precisar; rodar por schema; so com a tabela vazia ou sem pendentes):
--     DROP INDEX IF EXISTS produtor_NNNNN.ix_tb_6006_prop;
--     ALTER TABLE produtor_NNNNN.tb_6006_reidentificacao_com_baixa_itens DROP COLUMN IF EXISTS id_propriedade,
--         DROP COLUMN IF EXISTS data_reidentificacao, DROP COLUMN IF EXISTS id_usuario;
--     ALTER TABLE produtor_NNNNN.tb_6006_reidentificacao_com_baixa_itens ALTER COLUMN id_pedido SET NOT NULL;
--     UPDATE produtor_NNNNN.tb_versao_schema SET versao = 11 WHERE versao = 12;
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
        IF NOT (EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = s AND table_name = 'tb_6005_reidentificacao_com_baixa')
            AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = s AND table_name = 'tb_6006_reidentificacao_com_baixa_itens')
            AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = s AND table_name = 'tb_versao_schema')) THEN
            RAISE WARNING '% -> PULADO (falta tabela base)', s;
            CONTINUE;
        END IF;

        -- 1) pendente = sem Notificacao
        EXECUTE format('ALTER TABLE %I.tb_6006_reidentificacao_com_baixa_itens ALTER COLUMN id_pedido DROP NOT NULL', s);

        -- 2) colunas novas
        EXECUTE format('ALTER TABLE %I.tb_6006_reidentificacao_com_baixa_itens '
                       'ADD COLUMN IF NOT EXISTS id_propriedade INTEGER REFERENCES public.propriedades(id), '
                       'ADD COLUMN IF NOT EXISTS data_reidentificacao DATE, '
                       'ADD COLUMN IF NOT EXISTS id_usuario INTEGER', s);

        -- 3) o que ja existia herda do pedido
        EXECUTE format('UPDATE %1$I.tb_6006_reidentificacao_com_baixa_itens i '
                       'SET id_propriedade = p.id_propriedade, data_reidentificacao = p.data_solicitacao, id_usuario = p.id_usuario '
                       'FROM %1$I.tb_6005_reidentificacao_com_baixa p '
                       'WHERE p.id = i.id_pedido AND (i.id_propriedade IS NULL OR i.data_reidentificacao IS NULL)', s);

        -- 4) indice
        EXECUTE format('CREATE INDEX IF NOT EXISTS ix_tb_6006_prop ON %I.tb_6006_reidentificacao_com_baixa_itens (id_propriedade, id_pedido)', s);

        -- 5) versao do schema
        EXECUTE format('UPDATE %I.tb_versao_schema SET versao = 12 WHERE versao < 12', s);
    END LOOP;
END
$blk$;

-- =========================================================
-- CONFERENCIA (rodar depois; trocar o schema se quiser ver outro)
-- =========================================================
-- 1) colunas novas (esperado: 3 linhas) e id_pedido aceitando vazio (esperado: is_nullable = YES)
-- SELECT column_name, data_type, is_nullable FROM information_schema.columns
--  WHERE table_schema = 'produtor_00004' AND table_name = 'tb_6006_reidentificacao_com_baixa_itens'
--    AND column_name IN ('id_pedido','id_propriedade','data_reidentificacao','id_usuario') ORDER BY column_name;
-- 2) indice (esperado: 1 linha)
-- SELECT indexname FROM pg_indexes WHERE schemaname = 'produtor_00004' AND indexname = 'ix_tb_6006_prop';
-- 3) versao do schema (esperado: 12)
-- SELECT versao FROM produtor_00004.tb_versao_schema;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\criar_reidentificacao_pendentes_s121.sql
-- =========================================================
