-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\ajuste_id_origem_transfer_s109.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-10-30 18:55 -03
-- ATUALIZADO EM: 2026-10-30 18:55 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Ajuste dos animais de teste que entraram por Transferencia ENTRE PRODUTORES na Sessao 108 (produtor_00001, Maria Angelica):
--     cria (ou reaproveita) o Parceiro que representa o Produtor de origem e a Propriedade de origem dele, e grava o id do Parceiro
--     em id_origem na tb_2001 e na tb_2017_movimentacoes. O Parceiro nasce SEM id_produtor (vinculo so por confirmacao manual).
--     Regra de Ouro #19: PASSO 1 faz a copia de seguranca; para desfazer rode reverter_id_origem_transfer_s109.sql.
--     Pode rodar de novo: so mexe em linha com id_origem vazio e nao refaz a copia de seguranca se ela ja existe.
--     No pgAdmin rode UM passo por vez (marque so o bloco do passo).
--
-- v1.0.0: Sessao 109 (30/10/2026, 18:55 -03) - Criacao.
-- =========================================================

-- PASSO 0 - Conferencia de colunas (rode sozinho). Esperado: so cpf_cnpj, nome, ativo, criado_em, atualizado_em (tb_parceiros) e
-- id_parceiro, estabelecimento, ativo, criado_em, atualizado_em (tb_parceiros_propriedades). Se aparecer outra coluna, PARE e avise.
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'produtor_00001' AND table_name IN ('tb_parceiros', 'tb_parceiros_propriedades')
  AND is_nullable = 'NO' AND column_default IS NULL
ORDER BY table_name, ordinal_position;

-- PASSO 1 - Copia de seguranca (so cria se ainda nao existir)
CREATE TABLE IF NOT EXISTS produtor_00001.bkp_s109_tb_2001 AS
SELECT id, id_origem FROM produtor_00001.tb_2001
WHERE tipo_entrada::text = 'TRANSFERENCIA' AND id_origem IS NULL AND id_gta_entrada IS NOT NULL;

CREATE TABLE IF NOT EXISTS produtor_00001.bkp_s109_tb_2017 AS
SELECT id, id_origem FROM produtor_00001.tb_2017_movimentacoes
WHERE tipo_saida IS NULL AND id_origem IS NULL
  AND id_animal IN (SELECT id FROM produtor_00001.bkp_s109_tb_2001);

CREATE TABLE IF NOT EXISTS produtor_00001.bkp_s109_criados (tipo text, id integer);

-- PASSO 2 - O ajuste (um bloco so: ou faz tudo ou nao faz nada)
DO $$
DECLARE
    v_qtd_origens   integer;
    v_id_prop       integer;
    v_cpf           text;
    v_nome          text;
    v_id_parceiro   integer;
    v_oesa          text;
    v_id_pp         integer;
    p               record;
BEGIN
    -- Origem: tem que ser UMA so Propriedade e UM so CPF/CNPJ (senao PARA e avisa)
    SELECT COUNT(DISTINCT g.id_propriedade), MIN(g.id_propriedade)
      INTO v_qtd_origens, v_id_prop
      FROM produtor_00001.tb_2001 e
      JOIN produtor_00001.tb_4001_gta g ON g.id = e.id_gta_entrada
     WHERE e.id IN (SELECT id FROM produtor_00001.bkp_s109_tb_2001);
    IF v_qtd_origens <> 1 THEN
        RAISE EXCEPTION 'Esperava 1 Propriedade de origem e achei %. Nada foi alterado.', v_qtd_origens;
    END IF;

    SELECT COUNT(DISTINCT regexp_replace(origem_cpf_cnpj, '[^0-9]', '', 'g')), MIN(regexp_replace(origem_cpf_cnpj, '[^0-9]', '', 'g'))
      INTO v_qtd_origens, v_cpf
      FROM produtor_00001.tb_2017_movimentacoes
     WHERE id IN (SELECT id FROM produtor_00001.bkp_s109_tb_2017);
    IF v_qtd_origens <> 1 OR v_cpf IS NULL OR v_cpf = '' THEN
        RAISE EXCEPTION 'Esperava 1 CPF/CNPJ de origem e achei %. Nada foi alterado.', v_qtd_origens;
    END IF;

    SELECT nome INTO v_nome FROM public.produtores
     WHERE regexp_replace(cpf_cnpj, '[^0-9]', '', 'g') = v_cpf ORDER BY id LIMIT 1;
    IF v_nome IS NULL THEN
        RAISE EXCEPTION 'Produtor com CPF/CNPJ % nao encontrado em public.produtores. Nada foi alterado.', v_cpf;
    END IF;

    -- Parceiro: reaproveita pelo CPF/CNPJ ou cria (SEM id_produtor)
    SELECT id INTO v_id_parceiro FROM produtor_00001.tb_parceiros
     WHERE regexp_replace(cpf_cnpj, '[^0-9]', '', 'g') = v_cpf ORDER BY id LIMIT 1;
    IF v_id_parceiro IS NULL THEN
        INSERT INTO produtor_00001.tb_parceiros (cpf_cnpj, nome, ativo, criado_em, atualizado_em)
        VALUES (v_cpf, left(v_nome, 150), true, now(), now())
        RETURNING id INTO v_id_parceiro;
        INSERT INTO produtor_00001.bkp_s109_criados (tipo, id) VALUES ('PARCEIRO', v_id_parceiro);
    END IF;

    -- Propriedade de origem do Parceiro: chave = OESA (11 primeiros digitos); sem OESA, o nome
    SELECT * INTO p FROM public.propriedades WHERE id = v_id_prop;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Propriedade % nao encontrada em public.propriedades. Nada foi alterado.', v_id_prop;
    END IF;
    v_oesa := COALESCE(NULLIF(left(regexp_replace(COALESCE(p.oesa, ''), '[^0-9]', '', 'g'), 11), ''),
                       NULLIF(left(regexp_replace(COALESCE(p.codigo_mapa, ''), '[^0-9]', '', 'g'), 11), ''));
    SELECT id INTO v_id_pp FROM produtor_00001.tb_parceiros_propriedades
     WHERE id_parceiro = v_id_parceiro
       AND ((v_oesa IS NOT NULL AND left(regexp_replace(COALESCE(codigo_mapa, ''), '[^0-9]', '', 'g'), 11) = v_oesa)
         OR (v_oesa IS NULL AND upper(trim(estabelecimento)) = upper(trim(p.nome))))
     ORDER BY id LIMIT 1;
    IF v_id_pp IS NULL THEN
        INSERT INTO produtor_00001.tb_parceiros_propriedades
               (id_parceiro, estabelecimento, codigo_mapa, insc_estadual, municipio_codigo, municipio_nome, uf, regiao, ativo, criado_em, atualizado_em)
        VALUES (v_id_parceiro, left(trim(p.nome), 150), v_oesa, left(p.inscricao_estadual, 20), left(p.municipio_codigo, 10),
                left(p.municipio, 100), p.uf, p.regiao, true, now(), now())
        RETURNING id INTO v_id_pp;
        INSERT INTO produtor_00001.bkp_s109_criados (tipo, id) VALUES ('PROPRIEDADE', v_id_pp);
    END IF;

    -- id_origem nos animais e nas movimentacoes de entrada
    UPDATE produtor_00001.tb_2001 SET id_origem = v_id_parceiro
     WHERE id IN (SELECT id FROM produtor_00001.bkp_s109_tb_2001) AND id_origem IS NULL;
    UPDATE produtor_00001.tb_2017_movimentacoes SET id_origem = v_id_parceiro
     WHERE id IN (SELECT id FROM produtor_00001.bkp_s109_tb_2017) AND id_origem IS NULL;

    RAISE NOTICE 'OK: Parceiro % (%), Propriedade do Parceiro %, id_origem gravado.', v_id_parceiro, v_nome, v_id_pp;
END $$;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\ajuste_id_origem_transfer_s109.sql
-- =========================================================
