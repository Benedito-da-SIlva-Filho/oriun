-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: criar_tb_log_conferencia_propriedade.sql
-- AUTOR: Benedito Silva Filho.
-- CRIADO EM: 2026-07-29 10:04 -03
-- ATUALIZADO EM: 2026-07-29 10:04 -03
-- VERSAO: 1.0.0
--
-- CHANGELOG:
-- v1.0.0 - Criacao do modulo (Sessao 026). Fecha o P-029 do
--          Diario 025: log de auditoria imutavel para o lado
--          interno (Destino/Propriedade) da leitura de GTA,
--          espelhando tb_log_conferencia_parceiro (lado
--          externo). So existe uma situacao possivel aqui:
--          mais de uma Propriedade do proprio Produtor bate
--          com os criterios de busca do Destino, e o usuario
--          escolhe manualmente qual e a correta. Diferente do
--          lado Parceiro, aqui nao ha divergencia de sistema
--          para registrar - o campo central e a justificativa
--          escrita pelo proprio usuario, que ratifica e
--          responsabiliza a decisao (Regra de automacao,
--          Secao 5 do Diario 016: "o usuario nunca erra, e
--          sempre o software" - o sistema nunca decide sozinho
--          entre candidatas ambiguas).
--
--          Roda dentro do schema de cada Produtor (Schema-por-
--          Produtor, Sessao 018) - mesma factory de tabelas de
--          Movimentacao que tb_log_conferencia_parceiro. FKs
--          para tabelas public (usuarios, propriedades) usam
--          prefixo explicito 'public.' (licao da Sessao 019).
--
--          Log imutavel: sem atualizado_em, sem trigger.
-- =========================================================

CREATE TABLE IF NOT EXISTS tb_log_conferencia_propriedade (
    id                      SERIAL PRIMARY KEY,

    id_usuario              INTEGER NOT NULL
                                REFERENCES public.usuarios(id),

    id_propriedade          INTEGER NOT NULL
                                REFERENCES public.propriedades(id),

    tipo_situacao           VARCHAR(20) NOT NULL
                                DEFAULT 'AMBIGUIDADE_PROPRIEDADE',

    justificativa_usuario   TEXT NOT NULL,

    decisao_tomada          VARCHAR(30) NOT NULL
                                DEFAULT 'CONFIRMOU_PROPRIEDADE',

    data_hora               TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indices sobre as FKs, seguindo o padrao do projeto
CREATE INDEX IF NOT EXISTS idx_log_conf_propriedade_id_usuario
    ON tb_log_conferencia_propriedade (id_usuario);

CREATE INDEX IF NOT EXISTS idx_log_conf_propriedade_id_propriedade
    ON tb_log_conferencia_propriedade (id_propriedade);

-- =========================================================
-- FIM DE ARQUIVO: criar_tb_log_conferencia_propriedade.sql
-- =========================================================