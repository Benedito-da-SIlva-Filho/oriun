-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas\
-- MODULO: Tabelas\converter_especie_codigo_s082.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-09-29 06:55 -03
-- ATUALIZADO EM: 2026-09-29 06:55 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--   Regra de Benedito (Sessao 082): no banco a Especie e SEMPRE
--   o CODIGO do catalogo public.tb_4002_especie ("BOV", "BUB");
--   na tela, a descricao ("Bovino", "Bubalino").
--
--   A GTA Manual gravava a especie POR EXTENSO ("BOVINO") em
--   tb_4001_gta_animais - e a Brincagem Sequencial procura o
--   codigo, travando toda Brincagem de Compra. Este script
--   converte os registros ja gravados, em TODOS os schemas de
--   Produtor, comparando o texto gravado com a DESCRICAO do
--   catalogo (sem diferenca de maiusculas/espacos). Registro que
--   ja esta com o codigo nao e tocado.
--
--   NAO converte tb_log_alteracao_gta: e historico (registra o
--   que estava gravado na epoca da alteracao).
--
--   ORDEM: rodar logo DEPOIS de copiar os arquivos do Pacote 1 e
--   ANTES de testar.
--     PASSO 1 - previa (so conta, nao altera nada).
--     PASSO 2 - conversao (bloco DO, atomico; resultado na aba
--               Messages).
--     PASSO 3 - conferencia (selecionar e F5).
--
--   v1.0.0: Criacao (Sessao 082).
-- =========================================================


-- =========================================================
-- PASSO 1 - Previa no Zopone: o que esta gravado hoje
-- =========================================================
SELECT especie, COUNT(*) AS linhas
FROM produtor_00004.tb_4001_gta_animais
GROUP BY especie
ORDER BY especie;


-- =========================================================
-- PASSO 2 - Conversao em todos os schemas de Produtor
-- =========================================================
DO $$
DECLARE
    r       RECORD;
    v_qtde  INTEGER;
BEGIN
    FOR r IN
        SELECT t.table_schema AS esquema
        FROM information_schema.tables t
        WHERE t.table_schema LIKE 'produtor\_%'
          AND t.table_name = 'tb_4001_gta_animais'
        ORDER BY t.table_schema
    LOOP
        EXECUTE format($sql$
            UPDATE %1$I.tb_4001_gta_animais a
               SET especie = e.codigo
              FROM public.tb_4002_especie e
             WHERE upper(trim(a.especie)) = upper(trim(e.descricao))
               AND a.especie <> e.codigo
        $sql$, r.esquema);
        GET DIAGNOSTICS v_qtde = ROW_COUNT;

        RAISE NOTICE '% : % linha(s) convertida(s) para o codigo', r.esquema, v_qtde;
    END LOOP;
END $$;


-- =========================================================
-- PASSO 3 - Conferencia: especies que NAO sao codigo do
-- catalogo, em qualquer schema (esperado: nenhuma linha)
-- =========================================================
DO $$
DECLARE
    r       RECORD;
    v_qtde  INTEGER;
BEGIN
    FOR r IN
        SELECT t.table_schema AS esquema
        FROM information_schema.tables t
        WHERE t.table_schema LIKE 'produtor\_%'
          AND t.table_name = 'tb_4001_gta_animais'
        ORDER BY t.table_schema
    LOOP
        EXECUTE format($sql$
            SELECT COUNT(*) FROM %1$I.tb_4001_gta_animais a
             WHERE a.especie NOT IN (SELECT codigo FROM public.tb_4002_especie)
        $sql$, r.esquema) INTO v_qtde;

        RAISE NOTICE '% : % linha(s) FORA do catalogo (esperado 0)', r.esquema, v_qtde;
    END LOOP;
END $$;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\converter_especie_codigo_s082.sql
-- =========================================================
