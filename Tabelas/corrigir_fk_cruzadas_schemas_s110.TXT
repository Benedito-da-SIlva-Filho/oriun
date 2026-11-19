-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\corrigir_fk_cruzadas_schemas_s110.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-10-31 13:21 -03
-- ATUALIZADO EM: 2026-10-31 13:21 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Corrige FOREIGN KEYS que, num schema de Produtor (produtor_NNNNN), apontam para a tabela de OUTRO schema de Produtor
--     (defeito de clonagem). Achado na Sessao 110: produtor_00001 e produtor_00010 tinham tb_2012_com_entrada_id_gta_fkey
--     apontando para produtor_00004.tb_4001_gta; o Gerar Comunicado da Transferencia entre Produtores deu erro 500 (id 2 da
--     copia da GTA nao existia na base do Claudenor).
--
--     PASSO 1 (so leitura): lista todas as FKs cruzadas. PASSO 2: refaz cada uma apontando para a tabela do PROPRIO schema,
--     com o mesmo nome e as mesmas regras (ON DELETE etc). Cada FK e refeita isoladamente: se alguma nao puder ser refeita
--     (dado orfao), ela volta como estava e o aviso diz qual. PASSO 3 (so leitura): conferencia, deve vir vazio.
--     O pgAdmin roda so o que estiver MARCADO: rode um passo por vez. No PASSO 2, abra a aba Messages e guarde o texto
--     (traz a definicao ANTES de cada FK, para reverter se for preciso).
--
--     v1.0.0: Sessao 110 (31/10/2026, 13:21 -03) - Criacao.
-- =========================================================

-- ---------- PASSO 1 (so leitura): FKs cruzadas entre schemas de Produtor ----------
SELECT n1.nspname AS schema_da_tabela, c1.relname AS tabela, k.conname AS fk,
       n2.nspname AS aponta_para_schema, c2.relname AS aponta_para_tabela
FROM pg_constraint k
JOIN pg_class c1 ON c1.oid = k.conrelid  JOIN pg_namespace n1 ON n1.oid = c1.relnamespace
JOIN pg_class c2 ON c2.oid = k.confrelid JOIN pg_namespace n2 ON n2.oid = c2.relnamespace
WHERE k.contype = 'f' AND n1.nspname LIKE 'produtor\_%' AND n2.nspname LIKE 'produtor\_%' AND n1.nspname <> n2.nspname
ORDER BY 1, 2, 3;

-- ---------- PASSO 2 (corrige): refaz as FKs apontando para o proprio schema ----------
DO $$
DECLARE
    r record;
    novo text;
BEGIN
    FOR r IN
        SELECT k.conname, n1.nspname AS esquema, c1.relname AS tabela, n2.nspname AS esquema_ref, c2.relname AS tabela_ref,
               pg_get_constraintdef(k.oid) AS def
        FROM pg_constraint k
        JOIN pg_class c1 ON c1.oid = k.conrelid  JOIN pg_namespace n1 ON n1.oid = c1.relnamespace
        JOIN pg_class c2 ON c2.oid = k.confrelid JOIN pg_namespace n2 ON n2.oid = c2.relnamespace
        WHERE k.contype = 'f' AND n1.nspname LIKE 'produtor\_%' AND n2.nspname LIKE 'produtor\_%' AND n1.nspname <> n2.nspname
        ORDER BY 1, 2, 3
    LOOP
        BEGIN
            novo := replace(r.def, r.esquema_ref || '.' || r.tabela_ref, r.esquema || '.' || r.tabela_ref);
            IF novo = r.def THEN
                RAISE EXCEPTION 'definicao nao reconhecida';
            END IF;
            EXECUTE format('ALTER TABLE %I.%I DROP CONSTRAINT %I', r.esquema, r.tabela, r.conname);
            EXECUTE format('ALTER TABLE %I.%I ADD CONSTRAINT %I %s', r.esquema, r.tabela, r.conname, novo);
            RAISE NOTICE 'CORRIGIDA: %.% (%) | antes: % | depois: %', r.esquema, r.tabela, r.conname, r.def, novo;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'NAO CORRIGIDA (ficou como estava): %.% (%): %', r.esquema, r.tabela, r.conname, SQLERRM;
        END;
    END LOOP;
END
$$;

-- ---------- PASSO 3 (so leitura): conferencia, deve voltar VAZIO ----------
SELECT n1.nspname AS schema_da_tabela, c1.relname AS tabela, k.conname AS fk, n2.nspname AS aponta_para_schema
FROM pg_constraint k
JOIN pg_class c1 ON c1.oid = k.conrelid  JOIN pg_namespace n1 ON n1.oid = c1.relnamespace
JOIN pg_class c2 ON c2.oid = k.confrelid JOIN pg_namespace n2 ON n2.oid = c2.relnamespace
WHERE k.contype = 'f' AND n1.nspname LIKE 'produtor\_%' AND n2.nspname LIKE 'produtor\_%' AND n1.nspname <> n2.nspname;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\corrigir_fk_cruzadas_schemas_s110.sql
-- =========================================================
