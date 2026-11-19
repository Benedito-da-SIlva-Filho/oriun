-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\teste_voltar_120_dias_s099.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-10-17 11:05 -03
-- ATUALIZADO EM: 2026-10-17 11:05 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--   Sessao 099 - DADO DE TESTE (Regra de Ouro #19). Prepara 10 animais da
--   Fazenda Campo Grande (id_propriedade = 6, schema produtor_00004) para
--   testar o Leitor do Abate com animais ja liberados (mais de 90 dias).
--   Em tb_2001, SO nestes 10 SISBOVs:
--     data_inclusao   = data_inclusao  - 120 dias
--     data_brincagem  = data_brincagem - 120 dias (vazio continua vazio)
--     liberacao_abate = nova data_inclusao + 90 dias
--   Animais: 123456789010003, 007, 012, 019, 021, 022, 029, 030, 059, 069
--   (os finais acima, todos com prefixo 123456789010).
--   NAO mexe em pesagens, ERAS (eras_dias) nem em outras tabelas.
--   COPIA DE SEGURANCA: tabela produtor_00004.tb_2001_bkp_teste_s099 (valores
--   ORIGINAIS). Se ela ja existir, o script PARA sem alterar nada (evita
--   guardar valores ja alterados por cima dos originais).
--   Tudo ou nada: se nao achar exatamente 10 animais, nada e gravado.
--   PARA DESFAZER: rodar teste_reverter_120_dias_s099.sql.
--
--   v1.0.0: Criacao (Sessao 099).
-- =========================================================

DO $blk$
DECLARE
    sisbovs text[] := ARRAY[
        '123456789010003','123456789010007','123456789010012','123456789010019',
        '123456789010021','123456789010022','123456789010029','123456789010030',
        '123456789010059','123456789010069'];
    achados integer;
    alterados integer;
BEGIN
    -- trava 1: copia de seguranca ja existe -> para
    IF to_regclass('produtor_00004.tb_2001_bkp_teste_s099') IS NOT NULL THEN
        RAISE EXCEPTION 'Copia de seguranca tb_2001_bkp_teste_s099 ja existe. Rode antes o reverter ou apague a copia (so se tiver certeza). Nada foi alterado.';
    END IF;

    -- trava 2: tem que achar exatamente os 10 animais da propriedade 6
    SELECT count(*) INTO achados
      FROM produtor_00004.tb_2001
     WHERE id_propriedade = 6 AND sisbov = ANY (sisbovs);
    IF achados <> 10 THEN
        RAISE EXCEPTION 'Esperava 10 animais da propriedade 6 e achei %. Nada foi alterado.', achados;
    END IF;

    -- copia de seguranca (valores originais)
    CREATE TABLE produtor_00004.tb_2001_bkp_teste_s099 AS
        SELECT id, sisbov, data_inclusao, data_brincagem, liberacao_abate,
               now() AS salvo_em
          FROM produtor_00004.tb_2001
         WHERE id_propriedade = 6 AND sisbov = ANY (sisbovs);

    -- alteracao (a ordem dos SETs nao importa: o lado direito usa o valor antigo)
    UPDATE produtor_00004.tb_2001
       SET data_inclusao   = data_inclusao - 120,
           data_brincagem  = data_brincagem - 120,
           liberacao_abate = (data_inclusao - 120) + 90
     WHERE id_propriedade = 6 AND sisbov = ANY (sisbovs);
    GET DIAGNOSTICS alterados = ROW_COUNT;

    RAISE NOTICE 'Copia salva e % animais alterados (esperado 10).', alterados;
END $blk$;

-- =========================================================
-- CONFERENCIA (rodar depois)
-- =========================================================

-- 1) Copia de seguranca. Esperado: 10
SELECT count(*) AS animais_na_copia FROM produtor_00004.tb_2001_bkp_teste_s099;

-- 2) Os 15 do teste. Esperado:
--    - 10 alterados (003,007,012,019,021,022,029,030,059,069): dias_na_propriedade 135 a 139,
--      liberacao_abate entre 2026-08-29 e 2026-09-02, aptos = SIM
--    - 014, 015, 017: dias 258, aptos = SIM (nao foram mexidos)
--    - 018 e 065: dias 15 e 16, liberacao 2026-12-31, aptos = NAO (fora da Liberacao de proposito)
SELECT sisbov, rfid, sexo, nascimento, data_inclusao, data_brincagem, liberacao_abate,
       (CURRENT_DATE - data_inclusao) AS dias_na_propriedade,
       CASE WHEN liberacao_abate <= CURRENT_DATE THEN 'SIM' ELSE 'NAO' END AS apto
  FROM produtor_00004.tb_2001
 WHERE id_propriedade = 6
   AND sisbov IN ('123456789010014','123456789010015','123456789010021','123456789010022',
                  '123456789010029','123456789010030','123456789010003','123456789010065',
                  '123456789010017','123456789010059','123456789010069','123456789010007',
                  '123456789010012','123456789010019','123456789010018')
 ORDER BY (rfid IS NOT NULL), sisbov;

-- 3) Nenhum outro animal mexido: dos 91 da fazenda, so 13 ficam aptos hoje.
SELECT count(*) FILTER (WHERE liberacao_abate <= CURRENT_DATE) AS aptos_hoje,
       count(*) FILTER (WHERE liberacao_abate >  CURRENT_DATE) AS fora_da_liberacao
  FROM produtor_00004.tb_2001 WHERE id_propriedade = 6;
-- Esperado: aptos_hoje = 13 (10 alterados + 014, 015, 017), fora_da_liberacao = 78

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\teste_voltar_120_dias_s099.sql
-- =========================================================
