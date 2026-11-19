-- SQL_duplicidades_saidas_etapa5_13-11-2026.sql  (versao 1.0.0)
-- Etapa 5 da Auditoria: so LEITURA (SELECT). Nao altera nada.
-- Roda em CADA schema de Produtor: troque produtor_00001 pelo schema (00002, 00003, 00004, 00010).
-- Pergunta: ja existe duplicidade que impediria um indice unico?
SET search_path TO produtor_00001, public;

-- A) tb_2002: mesma saida gravada 2x para o mesmo animal (id que ele tinha na tb_2001)
SELECT 'A tb_2002 id_animal repetido' AS teste, id_animal, count(*) AS vezes, string_agg(tipo_saida || ' ' || data_saida::text, ' | ') AS saidas
FROM tb_2002_saida_animais WHERE id_animal IS NOT NULL
GROUP BY id_animal HAVING count(*) > 1;

-- B) tb_2002: mesma leitura (embarque) virando 2 saidas
SELECT 'B tb_2002 id_embarque repetido' AS teste, id_embarque, count(*) AS vezes
FROM tb_2002_saida_animais WHERE id_embarque IS NOT NULL
GROUP BY id_embarque HAVING count(*) > 1;

-- C) tb_2002: mesmo SISBOV com varias saidas (so para eu ver: pode ser legitimo se voltou por Transferencia)
SELECT 'C tb_2002 sisbov com 2+ saidas' AS teste, sisbov, count(*) AS vezes, string_agg(tipo_saida || ' ' || data_saida::text, ' | ' ORDER BY data_saida) AS saidas
FROM tb_2002_saida_animais GROUP BY sisbov HAVING count(*) > 1;

-- D) tb_3008: mesmo brinco baixado 2x
SELECT 'D tb_3008 sisbov repetido' AS teste, sisbov, count(*) AS vezes, string_agg(origem::text || ' ' || coalesce(data_saida::text,'-'), ' | ' ORDER BY id) AS motivos
FROM tb_3008_brincos_saida GROUP BY sisbov HAVING count(*) > 1;
