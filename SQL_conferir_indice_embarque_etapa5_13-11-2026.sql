-- SQL_conferir_indice_embarque_etapa5_13-11-2026.sql  (versao 1.0.0)
-- Etapa 5 da Auditoria: so LEITURA (SELECT). Nao altera nada.
-- Pergunta: existe indice UNICO que impede o mesmo animal ter 2 leituras de saida em aberto?
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename = 'tb_2020_embarque'
  AND schemaname NOT IN ('pg_catalog','information_schema')
ORDER BY schemaname, indexname;
-- Se, em cada schema de Produtor, nao aparecer nenhum indice com UNIQUE envolvendo id_animal,
-- me traga o resultado: eu desenho a trava (#71) e o indice, com backup e script de reverter.
