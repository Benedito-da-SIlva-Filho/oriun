-- SQL_conferir_indices_saidas_etapa5_13-11-2026.sql  (versao 1.0.0)
-- Etapa 5 da Auditoria: so LEITURA (SELECT). Nao altera nada.
-- Pergunta: tb_2002 (saida de animais) e tb_3008 (brincos de saida) tem indice UNICO
-- que impede o mesmo animal/brinco de ser gravado 2 vezes? (tb_2011 incluida de brinde: numero do Comunicado)
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('tb_2002_saida_animais','tb_3008_brincos_saida','tb_2011_com_saidas')
  AND schemaname NOT IN ('pg_catalog','information_schema')
ORDER BY tablename, schemaname, indexname;
