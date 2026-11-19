-- SQL_criar_indices_saidas_etapa5_13-11-2026.sql  (versao 1.0.0)
-- Etapa 5 da Auditoria. ALTERA O BANCO (cria 3 indices por schema de Produtor). Reverter: SQL_reverter_indices_saidas_etapa5_13-11-2026.sql
-- ANTES de rodar: fazer BACKUP do banco (Regra #24/#19). Rodar UMA vez, no banco orion.
-- Regra do Benedito: uma entrada = uma saida; brinco baixado so uma vez.
--  1) tb_2002: o mesmo animal (id_animal) so tem UMA saida valida. Linha 'substituido' (Troca de Comunicado: animal lido que
--     NAO embarcou e volta ao rebanho) fica de historico e nao conta - por isso o indice e PARCIAL (substituido = false).
--  2) tb_2002: a mesma leitura (id_embarque) so vira UMA saida valida (mesma excecao do substituido).
--  3) tb_3008: o mesmo brinco (sisbov) so e baixado UMA vez.
-- Conferido em 13/11/2026: sem duplicidade nos 5 schemas (00001, 00002, 00003, 00004, 00010).
DO $$
DECLARE s text;
BEGIN
  FOR s IN SELECT nspname FROM pg_namespace WHERE nspname ~ '^produtor_[0-9]+$' ORDER BY nspname LOOP
    EXECUTE format('CREATE UNIQUE INDEX IF NOT EXISTS uq_tb_2002_animal_valido ON %I.tb_2002_saida_animais (id_animal) WHERE id_animal IS NOT NULL AND substituido = false', s);
    EXECUTE format('CREATE UNIQUE INDEX IF NOT EXISTS uq_tb_2002_embarque_valido ON %I.tb_2002_saida_animais (id_embarque) WHERE id_embarque IS NOT NULL AND substituido = false', s);
    EXECUTE format('CREATE UNIQUE INDEX IF NOT EXISTS uq_tb_3008_sisbov ON %I.tb_3008_brincos_saida (sisbov)', s);
    RAISE NOTICE 'indices criados em %', s;
  END LOOP;
END $$;

-- Conferir:
SELECT schemaname, tablename, indexname FROM pg_indexes
WHERE indexname IN ('uq_tb_2002_animal_valido','uq_tb_2002_embarque_valido','uq_tb_3008_sisbov')
ORDER BY schemaname, indexname;
