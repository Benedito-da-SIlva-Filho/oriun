-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\backend\sql
-- MODULO: alter_propriedades_codigo_mapa.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-07-27 12:04 -03
-- ATUALIZADO EM: 2026-07-27 12:04 -03
-- VERSAO: 1.0.0, changelog:
--
-- DESCRICAO:
--     ALTER em propriedades para acrescentar o campo
--     codigo_mapa (chave de registro do estabelecimento rural
--     junto ao MAPA na Base Nacional de Dados, formato UF+
--     Municipio+sequencial, ex: 500001428140003). Descoberto
--     a partir de e-GTA real (bloco Procedencia), Sessao 024.
--
--     Distinto de codigo_eras (indicador de participacao no
--     SISBOV, formato curto - ex: 18834) e de oesa/nirf_incra/
--     car/inscricao_estadual, ja existentes e conferidos
--     como nao correspondentes a este codigo.
--
--     v1.0.0: Criacao (Sessao 024).
-- =========================================================

ALTER TABLE public.propriedades
    ADD COLUMN codigo_mapa VARCHAR(15);

COMMENT ON COLUMN public.propriedades.codigo_mapa IS
    'Chave de registro do estabelecimento rural junto ao MAPA (Base Nacional de Dados), formato UF+Municipio+sequencial (ex: 500001428140003). Distinto de codigo_eras. VARCHAR(15) por margem de seguranca (Sessao 024).';

-- =========================================================
-- FIM DE ARQUIVO: alter_propriedades_codigo_mapa.sql
-- =========================================================