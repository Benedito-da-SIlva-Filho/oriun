-- =========================================================
-- PROJETO: Orion   SESSAO 104 (23/10/2026)   SQL 20 v2
-- Auditoria de consistencia - SO LEITURA, UM UNICO COMANDO (nao cria nada).
-- Varre todos os schemas produtor_NNNNN. Resultado VAZIO = tudo consistente.
-- Selecione TUDO (Ctrl+A) e rode (F5).
-- =========================================================
WITH esquemas AS (
  SELECT schema_name::text AS sn
    FROM information_schema.schemata
   WHERE schema_name ~ '^produtor_[0-9]{5}$'
),
verificacoes(nome, modelo) AS (
  VALUES
  ('A) animal ativo (tb_2001) e baixado (tb_2002) ao mesmo tempo, sem troca',
   'SELECT count(*) AS c FROM %1$I.tb_2001 a JOIN %1$I.tb_2002_saida_animais b ON b.sisbov = a.sisbov WHERE b.sisbov_substituto IS NULL'),
  ('B) embarque: sts e numero_comunicado nao combinam',
   'SELECT count(*) AS c FROM %1$I.tb_2020_embarque WHERE (sts IS TRUE AND numero_comunicado IS NULL) OR (sts IS NOT TRUE AND numero_comunicado IS NOT NULL)'),
  ('C) embarque aberto de animal que nao esta no rebanho',
   'SELECT count(*) AS c FROM %1$I.tb_2020_embarque e WHERE e.sts IS NOT TRUE AND NOT EXISTS (SELECT 1 FROM %1$I.tb_2001 a WHERE a.sisbov = e.sisbov)'),
  ('D) saida baixada sem numero de Comunicado',
   'SELECT count(*) AS c FROM %1$I.tb_2002_saida_animais WHERE numero_comunicado IS NULL'),
  ('E) animal sem Propriedade',
   'SELECT count(*) AS c FROM %1$I.tb_2001 WHERE id_propriedade IS NULL'),
  ('F) mesmo animal em 2 embarques abertos',
   'SELECT count(*) AS c FROM (SELECT sisbov FROM %1$I.tb_2020_embarque WHERE sts IS NOT TRUE GROUP BY sisbov HAVING count(*) > 1) x')
),
resultado AS (
  SELECT e.sn AS schema_nome, v.nome AS verificacao,
         (xpath('/row/c/text()', query_to_xml(format(v.modelo, e.sn), false, true, '')))[1]::text::bigint AS qtde
    FROM esquemas e CROSS JOIN verificacoes v
)
SELECT schema_nome, verificacao, qtde FROM resultado WHERE qtde > 0
ORDER BY 1, 2;
