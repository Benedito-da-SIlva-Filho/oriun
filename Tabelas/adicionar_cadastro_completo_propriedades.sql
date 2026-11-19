-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\adicionar_cadastro_completo_propriedades.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-08-04 15:09 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Adiciona a coluna cadastro_completo em propriedades.
--     Motivo: pendencia P-040 - o pre-cadastro criado pelo
--     fluxo de Convite Publico (/convite) nasce com campos
--     obrigatorios preenchidos com placeholder (tipo='MISTA',
--     roteiro_acesso='A COMPLETAR', area_hectares=0). Esta
--     coluna marca quando isso ainda esta pendente, para o
--     Produtor ser direcionado a completar o cadastro no
--     primeiro acesso, em vez de cair direto na Home.
--
--     DEFAULT TRUE: toda Propriedade ja existente no banco
--     (cadastrada pela Consiste, com dados reais) e
--     considerada completa automaticamente - nao exige nenhuma
--     acao retroativa. Só nasce FALSE quando criada pelo
--     Convite Publico (definido explicitamente no codigo,
--     nao pelo default da coluna).
-- =========================================================

ALTER TABLE propriedades
ADD COLUMN cadastro_completo BOOLEAN NOT NULL DEFAULT TRUE;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\adicionar_cadastro_completo_propriedades.sql
-- =========================================================