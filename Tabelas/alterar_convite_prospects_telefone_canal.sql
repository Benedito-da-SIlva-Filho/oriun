-- =========================================================
-- PROJETO:      Orion
-- PASTA:        C:\orion\Tabelas
-- MODULO:       Tabelas\alterar_convite_prospects_telefone_canal.sql
-- AUTOR:        Benedito Silva Filho
-- CRIADO EM:    2026-08-12 10:30 -03
-- ATUALIZADO EM: 2026-08-12 10:30 -03
-- VERSAO:       1.0.0
--
-- DESCRICAO:
--     Adiciona suporte ao canal WhatsApp no Convite de Prospects
--     (backend/routers/prospects.py). Ate esta versao, a tabela
--     convite_prospects so registrava convites enviados por
--     e-mail (Sessao 034, continuacao 6). A partir de agora,
--     a Consiste tambem pode convidar um prospect via link
--     wa.me (sem custo, sem API paga, envio final manual).
--
--     - telefone: opcional, so digitos (DDD + numero, 11
--       caracteres), usado para montar o link wa.me. Fica
--       nulo quando o convite foi enviado so por e-mail.
--     - canal: obrigatorio, default 'EMAIL' (preenche as
--       linhas ja existentes automaticamente). Alimenta a
--       coluna "Canal" na lista de convidados.
--
--     Decisao de Benedito (11/08/2026, planejamento) e
--     confirmada em conversa (12/08/2026): permite registros
--     duplicados por prospect (historico completo por canal),
--     nao ha unicidade por email/nome.
--
--     v1.0.0: Criacao do script (Sessao 034, continuacao 8).
-- =========================================================

ALTER TABLE public.convite_prospects
    ADD COLUMN telefone VARCHAR(11),
    ADD COLUMN canal VARCHAR(10) NOT NULL DEFAULT 'EMAIL';

ALTER TABLE public.convite_prospects
    ADD CONSTRAINT ck_convite_prospects_canal CHECK (canal IN ('EMAIL', 'WHATSAPP'));

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\alterar_convite_prospects_telefone_canal.sql
-- =========================================================