-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\alter_propriedades_municipio_codigo_regiao.sql
-- AUTOR: Benedito Silva Filho.
-- CRIADO EM: 2026-07-28 19:22 -03
-- ATUALIZADO EM: 2026-07-28 19:22 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Adiciona municipio_codigo e regiao em propriedades
--     (schema public), para paridade com
--     tb_parceiros_propriedades - fecha a assimetria
--     encontrada na Sessao 025.
--
--     municipio_codigo: codigo oficial do municipio (padrao
--     IBGE, ex.: 5001102), separado do campo municipio ja
--     existente (texto livre, ex.: "AQUIDAUANA"). Necessario
--     para a busca de matching por codigo em vez de texto,
--     igual ja acontece em tb_parceiros_propriedades.
--
--     regiao: classificacao regional que aparece no bloco
--     Procedencia/Destino de toda e-GTA (ex.: PANTANAL,
--     PLANALTO). Propriedades nao tinha esse campo ate agora
--     porque o cadastro e feito pela Consiste sem essa
--     informacao - passa a existir para permitir capturar o
--     dado quando disponivel (preenchimento nao obrigatorio
--     por enquanto).
--
--     Ambos NULLABLE - nao quebra nenhum cadastro existente,
--     e propriedades ja cadastradas continuam validas sem
--     esses dados ate serem complementados.
--
--     v1.0.0: Criacao do script (Sessao 025).
-- =========================================================

ALTER TABLE public.propriedades
    ADD COLUMN municipio_codigo VARCHAR(10),
    ADD COLUMN regiao VARCHAR(50);

-- Confirmacao: deve mostrar as duas colunas novas, nullable
SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'propriedades'
  AND column_name IN ('municipio_codigo', 'regiao');

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\alter_propriedades_municipio_codigo_regiao.sql
-- =========================================================