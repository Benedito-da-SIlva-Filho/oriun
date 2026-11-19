-- =========================================================
-- PROJETO:      Orion
-- PASTA:        C:\orion\Tabelas
-- MODULO:       Tabelas\18_alter_propriedade_produtor_documento_secundario.sql
-- AUTOR:        Benedito Silva Filho
-- CRIADO EM:    2026-10-20 18:10 -03
-- VERSAO:       1.0.0
--
-- DESCRICAO:
--     CNPJ/CPF do Produtor POR FAZENDA (Sessao 101). Coluna nova no vinculo Produtor+Propriedade:
--         documento_secundario VARCHAR(14) - so digitos, opcional:
--             CNPJ do Produtor Fisico  /  CPF do Produtor Juridico, daquela fazenda.
--     O documento PRINCIPAL continua em public.produtores (tipo_pessoa + cpf_cnpj).
--     As colunas cpf e cnpj criadas em public.produtores pelo script 17 deixam de ser usadas (ficam la, sem dano).
--     Pode rodar mais de uma vez.
--     ORDEM: rodar ESTE script ANTES de subir os .py (o model do vinculo passa a ler a coluna).
-- =========================================================

BEGIN;

ALTER TABLE public.propriedade_produtor ADD COLUMN IF NOT EXISTS documento_secundario VARCHAR(14);

COMMENT ON COLUMN public.propriedade_produtor.documento_secundario IS
    'Documento secundario do Produtor NESTA Propriedade (so digitos): CNPJ do Produtor Fisico ou CPF do Juridico. Opcional.';

-- Tatiane (Juridica, 00000179765108 em produtores.cnpj): NAO migrado, aguardando confirmacao do Benedito.

COMMIT;

-- CONFERENCIA (deve listar 1 linha):
SELECT column_name, data_type, character_maximum_length
  FROM information_schema.columns
 WHERE table_schema = 'public' AND table_name = 'propriedade_produtor' AND column_name = 'documento_secundario';

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\18_alter_propriedade_produtor_documento_secundario.sql
-- =========================================================
