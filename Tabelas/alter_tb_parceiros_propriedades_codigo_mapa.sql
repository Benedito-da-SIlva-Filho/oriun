-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\alter_tb_parceiros_propriedades_codigo_mapa.sql
-- AUTOR: Benedito Silva Filho.
-- CRIADO EM: 2026-07-28 19:22 -03
-- ATUALIZADO EM: 2026-07-28 19:22 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Corrige codigo_mapa em tb_parceiros_propriedades de
--     NOT NULL para NULLABLE.
--
--     Motivo (Sessao 025, achado durante o desenho da tela de
--     cadastro de novo Parceiro): a Sessao 024 confirmou que
--     Codigo MAPA so existe em propriedades ERAS/SISBOV -
--     propriedades comuns/mercado interno nunca tiveram esse
--     codigo, nao e campo esquecido de preencher. Com a coluna
--     NOT NULL, o cadastro de um Parceiro comum (sem SISBOV)
--     ficava impossivel de salvar. insc_estadual ja era
--     nullable - esta correcao deixa os dois campos com o
--     mesmo tratamento.
--
--     Tabela em produtor_00001 confirmada vazia (0 linhas)
--     antes desta alteracao - ALTER seguro, sem risco de dado
--     existente virar NULL indevidamente.
--
--     Roda dentro do schema de cada Produtor - ajustar o
--     "SET search_path" ou o schema explicito conforme o
--     Produtor sendo alterado (aqui, produtor_00001 de teste).
--
--     v1.0.0: Criacao do script (Sessao 025).
-- =========================================================

ALTER TABLE produtor_00001.tb_parceiros_propriedades
    ALTER COLUMN codigo_mapa DROP NOT NULL;

-- Confirmacao: deve mostrar is_nullable = YES
SELECT column_name, is_nullable
FROM information_schema.columns
WHERE table_schema = 'produtor_00001'
  AND table_name = 'tb_parceiros_propriedades'
  AND column_name IN ('codigo_mapa', 'insc_estadual');

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\alter_tb_parceiros_propriedades_codigo_mapa.sql
-- =========================================================