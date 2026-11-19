-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\Orion\Tabelas
-- MODULO: SQL_carga_passo1_enums_17-11-2026.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-11-17 18:02 -03
-- ATUALIZADO EM: 2026-11-17 18:02 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--   CARGA (animais de Produtor novo, a partir do Extrato do MAPA) - PASSO 1 de 2.
--   Novo valor CARGA nos dois ENUMs (ficam no schema public, UM comando serve para todos os Produtores):
--     a) public.tipo_entrada_enum          (tipo de entrada do animal: tb_2001, tb_2012, tb_2017, tb_3008)
--     b) public.tipo_movimento_gta_enum    (tipo de movimento da GTA: tb_4001_gta)
--   Nao altera tabelas nem dados. Pode rodar mais de uma vez (IF NOT EXISTS).
--   COMO RODAR: selecione UMA linha de cada vez e execute (ADD VALUE nao roda junto com outros comandos).
--   RODAR ANTES do passo 2 e ANTES de instalar os arquivos .py.
--   ANTES de rodar: BACKUP do banco (Regra #24).
--
--   v1.0.0: Criacao.
--   REVERSAO: o valor de um ENUM nao se remove; fica sem uso. (Reverter o passo 2 basta.)
-- =========================================================

-- a) tipo de entrada do animal
ALTER TYPE public.tipo_entrada_enum ADD VALUE IF NOT EXISTS 'CARGA';

-- b) tipo de movimento da GTA
ALTER TYPE public.tipo_movimento_gta_enum ADD VALUE IF NOT EXISTS 'CARGA';

-- =========================================================
-- CONFERENCIA (rodar uma de cada vez)
-- =========================================================

-- 1) Esperado: a lista termina com POSSE e CARGA (COMPRA, NASCTO-DESMAME, REIDENTIFICACAO, TRANSFERENCIA, POSSE, CARGA)
SELECT unnest(enum_range(NULL::public.tipo_entrada_enum)) AS valor;

-- 2) Esperado: COMPRA, NASCTO-DESMAME, VENDA, ABATE, MORTE, TRANSFERENCIA, POSSE, CARGA
SELECT unnest(enum_range(NULL::public.tipo_movimento_gta_enum)) AS valor;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\SQL_carga_passo1_enums_17-11-2026.sql
-- =========================================================
