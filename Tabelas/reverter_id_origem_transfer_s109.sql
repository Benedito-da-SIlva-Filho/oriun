-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\reverter_id_origem_transfer_s109.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-10-30 18:55 -03
-- ATUALIZADO EM: 2026-10-30 18:55 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Desfaz ajuste_id_origem_transfer_s109.sql: devolve o id_origem original (vazio) na tb_2001 e na tb_2017_movimentacoes e apaga SO o
--     Parceiro e a Propriedade que o ajuste criou (registrados em bkp_s109_criados). Um bloco so: ou desfaz tudo ou nada.
--     As tabelas bkp_s109_* ficam; apague-as depois, se quiser, com os comandos comentados no fim.
--
-- v1.0.0: Sessao 109 (30/10/2026, 18:55 -03) - Criacao.
-- =========================================================

DO $$
BEGIN
    UPDATE produtor_00001.tb_2001 t SET id_origem = b.id_origem
      FROM produtor_00001.bkp_s109_tb_2001 b WHERE t.id = b.id;
    UPDATE produtor_00001.tb_2017_movimentacoes t SET id_origem = b.id_origem
      FROM produtor_00001.bkp_s109_tb_2017 b WHERE t.id = b.id;
    DELETE FROM produtor_00001.tb_parceiros_propriedades
     WHERE id IN (SELECT id FROM produtor_00001.bkp_s109_criados WHERE tipo = 'PROPRIEDADE');
    DELETE FROM produtor_00001.tb_parceiros
     WHERE id IN (SELECT id FROM produtor_00001.bkp_s109_criados WHERE tipo = 'PARCEIRO');
    RAISE NOTICE 'Ajuste desfeito.';
END $$;

-- Para apagar as copias de seguranca depois (opcional):
-- DROP TABLE produtor_00001.bkp_s109_tb_2001;
-- DROP TABLE produtor_00001.bkp_s109_tb_2017;
-- DROP TABLE produtor_00001.bkp_s109_criados;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\reverter_id_origem_transfer_s109.sql
-- =========================================================
