-- =========================================================
-- PROJETO:   Orion
-- PASTA:     C:\orion\Tabelas
-- MODULO:    Tabelas\criar_vitrine_visitantes.sql
-- AUTOR:     Benedito Silva Filho
-- CRIADO EM: 2026-08-11 20:30 -03
-- VERSAO:    1.0.0
--
-- DESCRICAO:
--     Cria a tabela vitrine_visitantes (schema public) - registro
--     de cada visitante que preencheu a Etapa 1 do Convite
--     Publico (/convite) e foi direcionado a Tela Vitrine (Sessao
--     034 continuacao 6), em vez de seguir direto para a Etapa 2
--     (criacao de conta real). Serve de base de contato/feedback
--     para a Consiste ligar depois - NAO cria Produtor, Propriedade
--     nem Usuario. A conta real so nasce quando a Consiste decidir
--     reativar a Etapa 2 (ainda pendente, decisao futura), apos a
--     pessoa "comprar a ideia" na conversa.
-- =========================================================

CREATE TABLE public.vitrine_visitantes (
    id           SERIAL PRIMARY KEY,
    cpf_cnpj     VARCHAR(18) NOT NULL,
    nome         VARCHAR(150) NOT NULL,
    email        VARCHAR(150) NOT NULL,
    telefone     VARCHAR(20) NOT NULL,
    visitado_em  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\criar_vitrine_visitantes.sql
-- =========================================================