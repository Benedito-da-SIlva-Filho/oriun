-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\alterar_posse_s115_b.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-11-05 11:36 -03
-- ATUALIZADO EM: 2026-11-05 11:36 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--   Sessao 115 - SAIDAS / ALTERACAO DE POSSE (pacote 1, parte B).
--   Novo valor POSSE no ENUM public.tipo_entrada_enum (tipo de entrada do animal que chega ao
--   destino por Alteracao de Posse; decisao de Benedito, 05/11/2026).
--   O ENUM e unico (schema public), por isso UM comando serve para todos os Produtores.
--   Nao altera tabelas nem dados e nao muda a versao do banco (continua 8).
--   Pode rodar mais de uma vez (IF NOT EXISTS). RODAR ANTES de instalar os arquivos .py.
--
--   v1.0.0: Criacao (Sessao 115).
--   REVERSAO: o valor de um ENUM nao se remove; fica sem uso.
-- =========================================================

ALTER TYPE public.tipo_entrada_enum ADD VALUE IF NOT EXISTS 'POSSE';

-- =========================================================
-- CONFERENCIA
-- =========================================================

-- Esperado: a lista termina com POSSE (COMPRA, NASCTO-DESMAME, REIDENTIFICACAO, TRANSFERENCIA e outros ja existentes, mais POSSE)
SELECT unnest(enum_range(NULL::public.tipo_entrada_enum)) AS valor;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\alterar_posse_s115_b.sql
-- =========================================================
