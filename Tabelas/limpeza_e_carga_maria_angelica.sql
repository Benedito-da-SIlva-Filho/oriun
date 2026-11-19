-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\limpeza_e_carga_maria_angelica.sql
-- AUTOR: Benedito Silva Filho.
-- CRIADO EM: 2026-07-31 16:17 -03
-- ATUALIZADO EM: 2026-07-31 16:17 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Script transacional de duas partes:
--
--     PARTE 1 - LIMPEZA: remove o Produtor de teste fictício
--         "AGRO MODELO" (id=1) e tudo que está ligado a ele
--         (usuário de teste, vínculos de Propriedade/Produtor/
--         Proprietário, e o schema produtor_00001 inteiro via
--         DROP SCHEMA CASCADE). Motivado por decisão de
--         Benedito: dados fictícios não servem mais de teste
--         porque as e-GTAs reais trazem CPF/CNPJ de pessoas de
--         verdade, que nunca vão bater contra Propriedades
--         inventadas.
--
--     PARTE 2 - CARGA: cadastra os dados REAIS extraídos da
--         e-GTA MS/Q/515308 (arquivo GTA_Compra_MS.pdf) para o
--         lado Destino - Maria Angélica Maia Cintra, cliente
--         real de Benedito, com SISBOV confirmado. Ela entra
--         como Proprietário (dona da terra) E Produtor (opera a
--         Fazenda), decisão confirmada com Benedito nesta
--         sessão - mesma pessoa em dois cadastros distintos por
--         principio de negocio ja estabelecido (Proprietario x
--         Produtor sao sempre entidades distintas no Orion,
--         mesmo quando e a mesma pessoa fisica).
--
--         Vinculada a Certificadora Teste (id=1, ja existente
--         no banco). codigo_eras da Propriedade fica NULL por
--         enquanto - Benedito vai preencher depois, nao e dado
--         disponivel na propria GTA.
--
--         id_proprietario em produtores aponta para o proprio
--         registro de Maria Angelica em proprietarios (ela e
--         proprietaria E produtora) - confirmado com Benedito.
--
--         Dados usados, direto da e-GTA real (Destino):
--           Nome: MARIA ANGELICA MAIA CINTRA
--           CPF: 20317217801
--           Estabelecimento: FAZENDA OLHO D'AGUA
--           Codigo MAPA: 500000680640005
--           Insc. Estadual: 287094561
--           Municipio: 5003306 - COXIM / MS
--
--     NAO faz parte deste script (fica para depois, script
--     separado): cadastro da Roselene Carvalho de Oliveira como
--     Parceiro (Procedencia da mesma GTA) - essa tabela
--     (tb_parceiros_propriedades) mora DENTRO do schema
--     produtor_00001, que so existe depois de rodar o
--     onboarding.py pela tela de edicao do Produtor. Ordem
--     correta: 1) este script, 2) onboarding via tela, 3)
--     proximo script cadastrando a Roselene no schema novo.
--
--     v1.0.0: Criacao do script (Sessao de hoje).
-- =========================================================

BEGIN;

-- ---------------------------------------------------------
-- PARTE 1 - LIMPEZA DO PRODUTOR DE TESTE FICTICIO (AGRO MODELO)
-- ---------------------------------------------------------

-- Usuario de login de teste (teste.agromodelo), se existir
DELETE FROM usuarios
WHERE login = 'teste.agromodelo';

-- Vinculo Propriedade x Produtor do AGRO MODELO (id_produtor = 1)
DELETE FROM propriedade_produtor
WHERE id_produtor = 1;

-- Vinculo Propriedade x Proprietario, para qualquer Propriedade
-- que tenha "AGRO MODELO" no nome
DELETE FROM propriedade_proprietario
WHERE id_propriedade IN (
    SELECT id FROM propriedades WHERE nome ILIKE '%AGRO MODELO%'
);

-- A(s) Propriedade(s) fictícia(s) em si
DELETE FROM propriedades
WHERE nome ILIKE '%AGRO MODELO%';

-- Proprietario vinculado ao Produtor AGRO MODELO (capturado
-- ANTES de apagar o produtor, senao a referencia se perde)
DELETE FROM proprietarios
WHERE id = (SELECT id_proprietario FROM produtores WHERE id = 1);

-- O Produtor de teste fictício em si
DELETE FROM produtores
WHERE id = 1;

-- O schema fisico inteiro (as 9 tabelas do onboarding antigo)
DROP SCHEMA IF EXISTS produtor_00001 CASCADE;


-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\parte2_carga_maria_angelica_fragmentado.sql
-- AUTOR: Benedito Silva Filho.
-- CRIADO EM: 2026-07-31 16:17 -03
-- ATUALIZADO EM: 2026-07-31 16:38 -03
-- VERSAO: 1.2.0
--
-- DESCRICAO:
--     Parte 2 (carga de Maria Angelica Maia Cintra / Fazenda
--     Olho D'Agua) fragmentada em 5 blocos INDEPENDENTES, cada
--     um com seu proprio BEGIN/COMMIT. Motivado por duas
--     tentativas anteriores que falharam por colunas NOT NULL
--     desconhecidas (tipo, email) - em vez de descobrir campo a
--     campo com a transacao inteira sendo desfeita a cada erro,
--     Benedito optou por rodar fragmento por fragmento: sucesso
--     -> segue pro proximo; erro -> para so naquele fragmento
--     (os anteriores ja commitados continuam validos).
--
--     Cada fragmento usa subquery por CPF/nome (chave natural)
--     em vez de encadear ids via CTE - assim nenhum fragmento
--     depende de um id retornado manualmente do fragmento
--     anterior.
--
--     ATENCAO - PLACEHOLDER: o campo email (obrigatorio, erro
--     desta rodada) recebeu um valor temporario
--     'pendente@fazendaolhodagua.com.br' - Benedito deve
--     substituir pelo email real quando tiver, ou apagar/editar
--     depois pela tela de cadastro.
--
--     v1.0.0 / v1.1.0: tentativas anteriores (nao fragmentadas).
--     v1.2.0: Sessao de hoje - fragmentado em 5 blocos
--             independentes; campo email adicionado com
--             placeholder.
-- =========================================================


-- =========================================================
-- FRAGMENTO 1 de 5 - Proprietario (Maria Angelica, dona da terra)
-- =========================================================
BEGIN;

INSERT INTO proprietarios (
    nome, razao_social, cpf_cnpj, tipo_pessoa, visibilidade, email,
    telefone, logradouro, numero, bairro, cep, municipio, uf, ativo,
    criado_em, atualizado_em
) VALUES (
    'MARIA ANGELICA MAIA CINTRA', 'MARIA ANGELICA MAIA CINTRA', '20317217801', 'FISICA', 'PUBLICO',
    'pendente@fazendaolhodagua.com.br', '(00) 00000-0000', 'PENDENTE', 'S/N', 'ZONA RURAL', '00000-000',
    'COXIM', 'MS', true, NOW(), NOW()
);

SELECT id, nome, cpf_cnpj FROM proprietarios WHERE cpf_cnpj = '20317217801';

-- Se certo: COMMIT;
-- Se errado: ROLLBACK;

-- =========================================================
-- FRAGMENTO 2 de 5 - Produtor (Maria Angelica, opera a Fazenda)
-- So rode depois do Fragmento 1 estar com COMMIT feito.
-- =========================================================
ROLLBACK;
BEGIN;

INSERT INTO produtores (
    nome, razao_social, cpf_cnpj, tipo_pessoa, visibilidade, email,
    telefone, logradouro, numero, bairro, cep, municipio, uf,
    id_proprietario, ativo, schema_nome, criado_em, atualizado_em
)
SELECT
    'MARIA ANGELICA MAIA CINTRA', 'MARIA ANGELICA MAIA CINTRA', '20317217801', 'FISICA', 'PUBLICO',
    'pendente@fazendaolhodagua.com.br', '(00) 00000-0000', 'PENDENTE', 'S/N', 'ZONA RURAL', '00000-000',
    'COXIM', 'MS', id, true, 'produtor_00001', NOW(), NOW()
FROM proprietarios
WHERE cpf_cnpj = '20317217801';

SELECT id, nome, cpf_cnpj, id_proprietario, schema_nome FROM produtores WHERE cpf_cnpj = '20317217801';

COMMIT;
-- Se errado: ROLLBACK;

-- =========================================================
-- FRAGMENTO 3 de 5 - Propriedade (Fazenda Olho D'Agua)
-- =========================================================

BEGIN;

INSERT INTO propriedades (
    id_certificadora, codigo_mapa, inscricao_estadual, nome, tipo,
    status_atividade, email, telefone, telefone2, logradouro, numero,
    bairro, cep, municipio, municipio_codigo, uf, regiao,
    area_hectares, latitude, longitude, roteiro_acesso,
    distancia_sede_cidade, ativo, criado_em, atualizado_em
) VALUES (
    1, '500000680640005', '287094561', 'FAZENDA OLHO D''AGUA', 'MISTA',
    'ATIVA', 'pendente@fazendaolhodagua.com.br', '(00) 00000-0000', '(00) 00000-0000',
    'PENDENTE', 'S/N', 'ZONA RURAL', '00000-000', 'COXIM', '5003306', 'MS', 'PENDENTE',
    0, 0, 0, 'PENDENTE', 'PENDENTE', true, NOW(), NOW()
);

COMMIT;

SELECT id, nome, codigo_mapa, id_certificadora FROM propriedades WHERE codigo_mapa = '500000680640005';

-- Se certo: COMMIT;
-- Se errado: ROLLBACK;
-- =========================================================
-- FRAGMENTO 4 de 5 - Vinculo Propriedade x Produtor
-- So rode depois dos Fragmentos 2 e 3 estarem com COMMIT feito.
-- =========================================================
BEGIN;

INSERT INTO propriedade_produtor (
    id_propriedade, id_produtor, principal, criado_em
)
SELECT
    (SELECT id FROM propriedades WHERE codigo_mapa = '500000680640005'),
    (SELECT id FROM produtores WHERE cpf_cnpj = '20317217801'),
    true, NOW();

COMMIT;

SELECT * FROM propriedade_produtor
WHERE id_produtor = (SELECT id FROM produtores WHERE cpf_cnpj = '20317217801');

-- =========================================================
-- FRAGMENTO 5 de 5 - Vinculo Propriedade x Proprietario
-- So rode depois dos Fragmentos 1 e 3 estarem com COMMIT feito.
-- =========================================================


-- =========================================================
-- CONFERENCIA FINAL - so roda depois dos 5 fragmentos com COMMIT
-- =========================================================
SELECT
    pr.id            AS id_produtor,
    pr.nome          AS produtor_nome,
    pr.schema_nome,
    pt.id            AS id_proprietario,
    ppd.principal,
    pp.id            AS id_propriedade,
    pp.nome          AS propriedade_nome,
    pp.tipo,
    pp.codigo_mapa,
    pp.id_certificadora
FROM produtores pr
JOIN proprietarios pt ON pt.id = pr.id_proprietario
JOIN propriedade_produtor ppd ON ppd.id_produtor = pr.id
JOIN propriedades pp ON pp.id = ppd.id_propriedade
WHERE pr.cpf_cnpj = '20317217801';

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\parte2_carga_maria_angelica_fragmentado.sql
-- =========================================================