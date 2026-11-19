-- =========================================================
-- PROJETO:   Orion
-- PASTA:     C:\orion\Tabelas
-- MODULO:    Tabelas\criar_convite_prospects.sql
-- AUTOR:     Benedito Silva Filho
-- CRIADO EM: 2026-08-11 19:33 -03
-- VERSAO:    1.0.0
--
-- DESCRICAO:
--     Cria a tabela convite_prospects (schema public) - registro
--     de cada convite comercial enviado pela Consiste a um
--     Produtor prospect, usando o link fixo /convite (Convite
--     Publico, ja existente). Guarda quem foi convidado, quando,
--     e qual usuario da Consiste enviou.
--
--     NAO tem relacao com o fluxo de Convite Publico em si -
--     esta tabela so registra o disparo do e-mail comercial, o
--     cadastro real (se o prospect aceitar) continua acontecendo
--     via /convite normalmente, sem nenhum vinculo direto com
--     esta tabela.
-- =========================================================

CREATE TABLE public.convite_prospects (
    id                   SERIAL PRIMARY KEY,
    nome                 VARCHAR(150) NOT NULL,
    email                VARCHAR(150) NOT NULL,
    id_usuario_consiste  INTEGER NOT NULL REFERENCES public.usuarios(id),
    enviado_em           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\criar_convite_prospects.sql
-- =========================================================