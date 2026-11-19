-- =========================================================
-- PROJETO:      Orion
-- PASTA:        C:\orion\Tabelas
-- MODULO:       Tabelas\17_alter_produtores_cpf_cnpj.sql
-- AUTOR:        Benedito Silva Filho
-- CRIADO EM:    2026-10-20 17:18 -03
-- VERSAO:       1.0.0
--
-- DESCRICAO:
--     Produtor com CPF e CNPJ ao mesmo tempo (Sessao 101). Duas colunas novas em public.produtores
--     (a tabela existe SO no schema public - nao ha copia nos schemas produtor_NNNNN):
--         cpf  VARCHAR(14)  - CPF do Produtor (so digitos), opcional
--         cnpj VARCHAR(14)  - CNPJ do Produtor (so digitos), opcional
--     cpf_cnpj + tipo_pessoa continuam como o documento PRINCIPAL (login, busca, blockchain).
--
--     Os registros atuais sao copiados para a coluna certa pelo tipo de pessoa:
--         FISICA   -> cpf  (se vier com 14 digitos e comecar com 000, ex.: 00005407536889 do sistema
--                          antigo, apara para os 11 digitos finais)
--         JURIDICA -> cnpj
--     Pode rodar mais de uma vez: so preenche onde a coluna nova ainda esta vazia.
--
--     ORDEM: rodar ESTE script ANTES de subir os arquivos .py da Sessao 101 (o model passa a ler as colunas).
-- =========================================================

BEGIN;

ALTER TABLE public.produtores ADD COLUMN IF NOT EXISTS cpf  VARCHAR(14);
ALTER TABLE public.produtores ADD COLUMN IF NOT EXISTS cnpj VARCHAR(14);

COMMENT ON COLUMN public.produtores.cpf  IS 'CPF do Produtor (so digitos). Opcional. Sao Paulo exige CPF e CNPJ.';
COMMENT ON COLUMN public.produtores.cnpj IS 'CNPJ do Produtor (so digitos). Opcional. Sao Paulo exige CPF e CNPJ.';

-- Copia do documento principal para a coluna certa (so onde ainda esta vazia)
UPDATE public.produtores
   SET cpf = CASE
                 WHEN length(regexp_replace(cpf_cnpj, '\D', '', 'g')) = 14
                      AND regexp_replace(cpf_cnpj, '\D', '', 'g') LIKE '000%'
                     THEN right(regexp_replace(cpf_cnpj, '\D', '', 'g'), 11)
                 ELSE regexp_replace(cpf_cnpj, '\D', '', 'g')
             END
 WHERE upper(tipo_pessoa) = 'FISICA' AND cpf IS NULL;

UPDATE public.produtores
   SET cnpj = regexp_replace(cpf_cnpj, '\D', '', 'g')
 WHERE upper(tipo_pessoa) = 'JURIDICA' AND cnpj IS NULL;

COMMIT;

-- =========================================================
-- CONFERENCIA (rodar depois):
-- =========================================================
-- 1) Colunas criadas (deve listar 2 linhas):
SELECT column_name, data_type, character_maximum_length
  FROM information_schema.columns
 WHERE table_schema = 'public' AND table_name = 'produtores' AND column_name IN ('cpf', 'cnpj')
 ORDER BY column_name;

-- 2) Como ficaram os Produtores (um por linha):
SELECT id, nome, tipo_pessoa, cpf_cnpj, cpf, cnpj FROM public.produtores ORDER BY id;

-- 3) Produtor Fisico sem CPF ou Juridico sem CNPJ (deve voltar 0 linhas):
SELECT id, nome, tipo_pessoa, cpf_cnpj, cpf, cnpj FROM public.produtores
 WHERE (upper(tipo_pessoa) = 'FISICA' AND cpf IS NULL) OR (upper(tipo_pessoa) = 'JURIDICA' AND cnpj IS NULL);

-- 4) CPF com tamanho diferente de 11 (deve voltar 0 linhas):
SELECT id, nome, cpf FROM public.produtores WHERE cpf IS NOT NULL AND length(cpf) <> 11;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\17_alter_produtores_cpf_cnpj.sql
-- =========================================================
