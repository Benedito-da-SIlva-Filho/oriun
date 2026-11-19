-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\backend\sql
-- MODULO: alter_tb_frigorificos_codigo_mapa.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-07-27 11:20 -03
-- ATUALIZADO EM: 2026-07-27 11:20 -03
-- VERSAO: 1.0.0, changelog:
--
-- DESCRICAO:
--     ALTER em tb_frigorificos para acrescentar o campo
--     codigo_mapa (chave de registro do estabelecimento
--     industrial junto ao MAPA, distinta dos codigos de
--     inspecao sanitaria SIF/SIE/SIM). Campo descoberto a
--     partir de e-GTA real de Abate (Sessao 024) - nao
--     existia no cadastro legado GERAS (GR1119) nem na
--     estrutura original de tb_frigorificos (Sessao 17).
--
--     v1.0.0: Criacao (Sessao 024).
-- =========================================================

ALTER TABLE public.tb_frigorificos
    ADD COLUMN codigo_mapa VARCHAR(15);

COMMENT ON COLUMN public.tb_frigorificos.codigo_mapa IS
    'Chave de registro do estabelecimento industrial junto ao MAPA (ex: 5000024228), distinta dos codigos de inspecao sanitaria SIF/SIE/SIM. Formato/tamanho ainda em observacao - VARCHAR(15) por margem de seguranca (Sessao 024).';

-- =========================================================
-- FIM DE ARQUIVO: alter_tb_frigorificos_codigo_mapa.sql
-- =========================================================