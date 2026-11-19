-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: criar_tb_log_alteracao_gta.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-08-21 17:28 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Cria a tabela tb_log_alteracao_gta - log detalhado de
--     alteracoes feitas numa GTA ja gravada (Sessao 037/038).
--     Uma linha por CAMPO alterado (nao uma linha por edicao
--     inteira) - mesmo espirito de tb_log_conferencia_parceiro,
--     ja existente no projeto. Cobre tanto campos do documento
--     (Emissao, Validade, Meio de Transporte, etc.) quanto
--     categorias de Animais (cada categoria adicionada, removida
--     ou com quantidade alterada vira uma linha propria).
--
--     Mora dentro do schema de cada Produtor (produtor_NNNNN),
--     igual a tb_4001_gta e as demais tabelas de movimento -
--     precisa ser criada em CADA schema de Produtor existente,
--     e no template de Onboarding (backend/utils/onboarding.py)
--     para os Produtores futuros.
--
--     EXECUTAR ESTE SCRIPT trocando produtor_NNNNN pelo schema
--     real de cada Produtor (ex.: produtor_00005).
-- =========================================================

CREATE TABLE produtor_NNNNN.tb_log_alteracao_gta (
    id                  SERIAL PRIMARY KEY,
    id_gta              INTEGER NOT NULL REFERENCES produtor_NNNNN.tb_4001_gta(id),
    id_usuario          INTEGER NOT NULL REFERENCES public.usuarios(id),
    usuario_nome        VARCHAR(150) NOT NULL,
    campo_alterado      VARCHAR(60) NOT NULL,
    valor_anterior      TEXT,
    valor_novo          TEXT,
    alterado_em         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE produtor_00001.tb_log_alteracao_gta IS
    'Log detalhado de alteracoes em GTAs ja gravadas - 1 linha por campo alterado (documento ou categoria de Animais).';

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\criar_tb_log_alteracao_gta.sql
-- =========================================================