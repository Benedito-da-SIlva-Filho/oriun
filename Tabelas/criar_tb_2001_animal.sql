-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\backend\sql
-- MODULO: criar_tb_2001_animal.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-07-27 12:27 -03
-- ATUALIZADO EM: 2026-07-27 12:27 -03
-- VERSAO: 1.0.0, changelog:
--
-- DESCRICAO:
--     Criacao fisica de tb_2001 (Estado Atual do Animal),
--     desenho fechado na Sessao 023 (Secao 9.6.1 da
--     Referencia) e materializado na Sessao 024.
--
--     tb_2001 e tabela POR-PRODUTOR (Schema-por-Produtor,
--     decisao da Sessao 17/18) - guarda SOMENTE o rebanho
--     vivo. No evento de saida (Venda/Abate/Morte/
--     Transferencia/Reidentificacao), o registro e removido
--     fisicamente daqui (DELETE real, ja decidido na Sessao
--     021) - por isso NAO tem coluna "ativo".
--
--     Rodar este script com o search_path apontando para o
--     schema do Produtor desejado (troque 'produtor_00001'
--     pelo schema correto antes de rodar em outro Produtor).
--     Os dois ENUMs novos (tipo_saida_enum, interno_externo_
--     enum) e o sexo_enum ficam no schema public (compartilhado
--     entre todos os Produtores), criados de forma idempotente
--     (nao falha se ja existirem).
--
--     v1.0.0: Criacao (Sessao 024).
-- =========================================================

-- ---------------------------------------------------------
-- PARTE 1 - ENUMs no schema public (rodar uma unica vez,
-- independente de qual Produtor - nao repetir por schema)
-- ---------------------------------------------------------

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sexo_enum') THEN
        CREATE TYPE public.sexo_enum AS ENUM ('MACHO', 'FEMEA');
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_saida_enum') THEN
        CREATE TYPE public.tipo_saida_enum AS ENUM
            ('VENDA', 'ABATE', 'MORTE', 'TRANSFERENCIA', 'REIDENTIFICACAO');
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'interno_externo_enum') THEN
        CREATE TYPE public.interno_externo_enum AS ENUM ('INTERNO', 'EXTERNO');
    END IF;
END$$;

-- ---------------------------------------------------------
-- PARTE 2 - tb_2001, dentro do schema do Produtor.
-- IMPORTANTE: definir o schema ativo antes de rodar a PARTE 2
-- (troque 'produtor_00001' pelo schema correto quando for
-- rodar em outro Produtor).
-- ---------------------------------------------------------

SET search_path TO produtor_00001, public;

CREATE TABLE tb_2001 (
    id                  SERIAL PRIMARY KEY,

    -- Bloco Identificacao
    sisbov              VARCHAR(15) NOT NULL,   -- Sisbov + DV fundidos
    manejo              VARCHAR(6),
    rfid                VARCHAR(15),
    id_especie          INTEGER REFERENCES public.tb_4002_especie(id),
    sexo                public.sexo_enum,
    nascimento          DATE,
    -- eras_dias: ponto medio da faixa etaria declarada na GTA
    -- (tb_4006_idade_meses.dias_min/dias_max). Travado no
    -- momento da Entrada/Brincagem, nunca recalculado depois.
    eras_dias           INTEGER,
    id_raca             INTEGER REFERENCES public.tb_4005_racas(id),

    -- Bloco Elegibilidade
    id_aptidao          INTEGER REFERENCES public.tb_4004_aptidao(id),
    -- cota_hilton: calculado automaticamente - elegivel se
    -- tipo_entrada = NASCTO-DESMAME OU entrou com idade < 10
    -- meses. Nunca marcado manualmente pelo usuario.
    cota_hilton         BOOLEAN NOT NULL DEFAULT false,
    -- liberacao_abate: calculado como data_inclusao + 90 dias.
    -- Pode ser sobrescrito manualmente via UPDATE direto quando
    -- a conferencia BND x Fazenda (P-026) encontrar divergencia
    -- - a BND sempre prevalece sobre o calculo local.
    liberacao_abate     DATE,

    -- Bloco Entrada
    tipo_entrada        tipo_entrada_enum NOT NULL,
    brincos             public.interno_externo_enum,
    id_gta_entrada       INTEGER REFERENCES tb_4001_gta(id),
    data_inclusao       DATE NOT NULL,
    lote                VARCHAR(30),   -- piquete/pasto, texto livre
    id_origem           INTEGER REFERENCES tb_parceiros(id),

    -- Controle de datas
    criado_em           TIMESTAMP NOT NULL DEFAULT now(),
    atualizado_em       TIMESTAMP NOT NULL DEFAULT now(),

    CONSTRAINT uq_tb_2001_sisbov UNIQUE (sisbov)
);

COMMENT ON TABLE tb_2001 IS
    'Estado Atual do Animal - guarda somente o rebanho vivo. DELETE fisico no evento de saida (Secao 9.6.1, Sessao 023/024).';

CREATE INDEX idx_tb_2001_manejo ON tb_2001 (manejo);
CREATE INDEX idx_tb_2001_rfid ON tb_2001 (rfid);
CREATE INDEX idx_tb_2001_id_gta_entrada ON tb_2001 (id_gta_entrada);
CREATE INDEX idx_tb_2001_id_origem ON tb_2001 (id_origem);

-- Trigger dedicada de atualizado_em (padrao do projeto - uma
-- funcao por tabela, nunca trigger generica compartilhada)
CREATE OR REPLACE FUNCTION tb_2001_atualizado_em()
RETURNS TRIGGER AS $trg$
BEGIN
    NEW.atualizado_em = now();
    RETURN NEW;
END;
$trg$ LANGUAGE plpgsql;

CREATE TRIGGER trg_tb_2001_atualizado_em
    BEFORE UPDATE ON tb_2001
    FOR EACH ROW
    EXECUTE FUNCTION tb_2001_atualizado_em();

-- =========================================================
-- FIM DE ARQUIVO: criar_tb_2001_animal.sql
-- =========================================================