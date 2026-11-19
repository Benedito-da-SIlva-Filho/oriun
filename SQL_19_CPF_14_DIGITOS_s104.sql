-- =========================================================
-- PROJETO: Orion   SESSAO 104 (23/10/2026)
-- SQL 19 - CPF legado com 14 digitos ('000' + 11) passa a ser gravado com 11 digitos
-- Rodar no banco do Orion (pgAdmin), na ORDEM: 1) conferir  2) corrigir  3) conferir de novo
-- =========================================================

-- 1) CONFERIR: quais Produtores estao assim (esperado: ver a lista; depois da correcao: vazio)
SELECT p.id, p.nome, p.tipo_pessoa, p.cpf_cnpj,
       right(p.cpf_cnpj, 11) AS cpf_novo,
       (SELECT count(*) FROM public.produtores o
         WHERE o.id <> p.id AND o.cpf_cnpj = right(p.cpf_cnpj, 11)) AS ja_existe_igual
  FROM public.produtores p
 WHERE length(p.cpf_cnpj) = 14 AND p.cpf_cnpj LIKE '000%'
 ORDER BY p.id;
-- ATENCAO: se "ja_existe_igual" > 0 em alguma linha, NAO rode a correcao: me avise.

-- 2) CORRIGIR (CPF no Produtor e no login do Usuario)
BEGIN;
UPDATE public.usuarios u
   SET login = right(u.login, 11)
 WHERE length(u.login) = 14 AND u.login LIKE '000%'
   AND u.login IN (SELECT cpf_cnpj FROM public.produtores WHERE length(cpf_cnpj) = 14 AND cpf_cnpj LIKE '000%');

UPDATE public.produtores
   SET cpf_cnpj = right(cpf_cnpj, 11),
       tipo_pessoa = 'FISICA'
 WHERE length(cpf_cnpj) = 14 AND cpf_cnpj LIKE '000%';
COMMIT;

-- 3) CONFERIR DE NOVO (esperado: vazio)
SELECT id, nome, tipo_pessoa, cpf_cnpj FROM public.produtores WHERE length(cpf_cnpj) = 14 AND cpf_cnpj LIKE '000%';
SELECT id, login FROM public.usuarios WHERE length(login) = 14 AND login LIKE '000%';
