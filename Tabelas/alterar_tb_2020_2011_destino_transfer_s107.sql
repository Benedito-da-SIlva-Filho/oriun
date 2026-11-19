-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\alterar_tb_2020_2011_destino_transfer_s107.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-10-28 09:10 -03
-- ATUALIZADO EM: 2026-10-28 09:10 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--   Sessao 107 - SAIDAS / TRANSFERENCIA (pacote 1). Cria a coluna
--   id_propriedade_destino (INTEGER, opcional, FK public.propriedades) em:
--     tb_2020_embarque    (leitura no brete: fazenda de destino escolhida)
--     tb_2011_com_saidas  (Comunicado de Saida: "Destino Propriedade" do GERAS)
--   em TODOS os schemas produtor_NNNNN. Fica vazia em Abate, Venda e Morte;
--   so a Transferencia preenche. O CPF/CNPJ do destino ja existe em
--   tb_2011.cpf_cnpj_destino. Nenhuma tabela nova, nenhum dado alterado.
--   Sobe a versao do banco (tb_versao_schema) para 5, junto com
--   VERSAO_SCHEMA_ATUAL = 5 do backup_helper.py v1.8.0.
--   Pode rodar mais de uma vez sem estragar nada (IF NOT EXISTS; a versao so
--   sobe). Schema sem as tabelas e PULADO com aviso (WARNING).
--   RODAR ANTES de instalar os arquivos .py.
--
--   v1.0.0: Criacao (Sessao 107).
--   REVERSAO: ALTER TABLE produtor_NNNNN.tb_2020_embarque DROP COLUMN id_propriedade_destino;
--             ALTER TABLE produtor_NNNNN.tb_2011_com_saidas DROP COLUMN id_propriedade_destino;
--             (e voltar tb_versao_schema para 4)
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
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = esquema AND table_name = 'tb_2020_embarque')
           AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = esquema AND table_name = 'tb_2011_com_saidas')
           AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = esquema AND table_name = 'tb_versao_schema') THEN

            EXECUTE format('ALTER TABLE %I.tb_2020_embarque ADD COLUMN IF NOT EXISTS id_propriedade_destino INTEGER REFERENCES public.propriedades(id)', esquema);
            EXECUTE format('ALTER TABLE %I.tb_2011_com_saidas ADD COLUMN IF NOT EXISTS id_propriedade_destino INTEGER REFERENCES public.propriedades(id)', esquema);

            -- versao do banco = 5
            EXECUTE format('UPDATE %I.tb_versao_schema SET versao = 5 WHERE versao < 5', esquema);
            EXECUTE format('INSERT INTO %I.tb_versao_schema (versao) SELECT 5 WHERE NOT EXISTS (SELECT 1 FROM %I.tb_versao_schema)', esquema, esquema);

            RAISE NOTICE '% -> coluna id_propriedade_destino OK e versao 5 OK', esquema;
        ELSE
            RAISE WARNING '% -> PULADO (falta tb_2020_embarque, tb_2011_com_saidas ou tb_versao_schema)', esquema;
        END IF;
    END LOOP;
END $blk$;

-- =========================================================
-- CONFERENCIA (rodar uma de cada vez; o pgAdmin mostra so o ultimo comando)
-- =========================================================

-- 1) Coluna nova por tabela. Esperado: 2 linhas por schema (tb_2020_embarque e tb_2011_com_saidas)
SELECT table_schema, table_name, column_name, data_type
  FROM information_schema.columns
 WHERE column_name = 'id_propriedade_destino'
   AND table_name IN ('tb_2020_embarque','tb_2011_com_saidas')
   AND table_schema LIKE 'produtor\_%'
 ORDER BY table_schema, table_name;

-- 2) Versao do banco em cada schema. Esperado: 5
SELECT table_schema,
       (xpath('/row/versao/text()', query_to_xml(format('SELECT versao FROM %I.tb_versao_schema', table_schema), false, true, '')))[1]::text AS versao
  FROM information_schema.tables
 WHERE table_name = 'tb_versao_schema' AND table_schema LIKE 'produtor\_%'
 ORDER BY table_schema;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\alterar_tb_2020_2011_destino_transfer_s107.sql
-- =========================================================
