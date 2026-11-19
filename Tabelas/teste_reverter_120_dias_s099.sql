-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\teste_reverter_120_dias_s099.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-10-17 11:05 -03
-- ATUALIZADO EM: 2026-10-17 11:05 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--   Sessao 099 - DESFAZ o teste_voltar_120_dias_s099.sql (Regra de Ouro #19).
--   Devolve a tb_2001 (produtor_00004) os valores ORIGINAIS guardados em
--   tb_2001_bkp_teste_s099: data_inclusao, data_brincagem e liberacao_abate
--   dos 10 animais. So mexe nesses 10 (casa pelo id).
--   Se a copia nao existir ou nao tiver 10 linhas, PARA sem alterar nada.
--   A tabela de copia NAO e apagada (para voce conferir). Depois de conferir,
--   se quiser limpar, rode a linha DROP TABLE comentada no fim.
--   ATENCAO: leituras de teste ja gravadas em tb_2020 guardam a Liberacao
--   usada na hora; limpe/trate essas leituras antes ou depois de reverter.
--
--   v1.0.0: Criacao (Sessao 099).
-- =========================================================

DO $blk$
DECLARE
    na_copia integer;
    devolvidos integer;
BEGIN
    IF to_regclass('produtor_00004.tb_2001_bkp_teste_s099') IS NULL THEN
        RAISE EXCEPTION 'Copia tb_2001_bkp_teste_s099 nao existe. Nada foi alterado.';
    END IF;

    SELECT count(*) INTO na_copia FROM produtor_00004.tb_2001_bkp_teste_s099;
    IF na_copia <> 10 THEN
        RAISE EXCEPTION 'A copia tem % linhas (esperado 10). Nada foi alterado.', na_copia;
    END IF;

    UPDATE produtor_00004.tb_2001 a
       SET data_inclusao   = b.data_inclusao,
           data_brincagem  = b.data_brincagem,
           liberacao_abate = b.liberacao_abate
      FROM produtor_00004.tb_2001_bkp_teste_s099 b
     WHERE a.id = b.id;
    GET DIAGNOSTICS devolvidos = ROW_COUNT;

    RAISE NOTICE '% animais devolvidos aos valores originais (esperado 10).', devolvidos;
END $blk$;

-- =========================================================
-- CONFERENCIA (rodar depois)
-- =========================================================

-- 1) Nenhuma diferenca entre a tb_2001 e a copia. Esperado: 0
SELECT count(*) AS diferentes
  FROM produtor_00004.tb_2001 a
  JOIN produtor_00004.tb_2001_bkp_teste_s099 b ON b.id = a.id
 WHERE a.data_inclusao   IS DISTINCT FROM b.data_inclusao
    OR a.data_brincagem  IS DISTINCT FROM b.data_brincagem
    OR a.liberacao_abate IS DISTINCT FROM b.liberacao_abate;

-- 2) Aptos hoje. Esperado: 3 (014, 015, 017) e fora_da_liberacao = 88
SELECT count(*) FILTER (WHERE liberacao_abate <= CURRENT_DATE) AS aptos_hoje,
       count(*) FILTER (WHERE liberacao_abate >  CURRENT_DATE) AS fora_da_liberacao
  FROM produtor_00004.tb_2001 WHERE id_propriedade = 6;

-- (OPCIONAL, so depois de conferir) apagar a copia:
-- DROP TABLE produtor_00004.tb_2001_bkp_teste_s099;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\teste_reverter_120_dias_s099.sql
-- =========================================================
