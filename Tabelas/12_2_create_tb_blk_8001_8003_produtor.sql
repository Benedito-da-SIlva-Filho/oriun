-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\12_2_create_tb_blk_8001_8003_produtor.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-10-09 17:20 -03
-- ATUALIZADO EM: 2026-10-09 17:35 -03
-- VERSAO: 1.1.0
--
-- DESCRICAO:
--   Sessao 092 - BLOCKCHAIN (preparacao). Cria, em TODOS os schemas
--   produtor_NNNNN, as 3 tabelas da fila de eventos. Pode rodar mais de
--   uma vez sem estragar nada. Rodar DEPOIS do script 11_.
--
--   tb_blk_8001_produtor_provedores - quais provedores estao ligados para
--       este Produtor (ambiente TESTE/PRODUCAO; envia_dono = se o bloco do
--       dono tambem vai para o provedor, padrao NAO).
--   tb_blk_8002_eventos - a FILA: um fato do animal (tipo_evento), com o
--       SISBOV so como hash (HMAC), a COPIA CONGELADA da ficha (animal e
--       dono, em JSON) e os hashes. Correcao = evento novo apontando para o
--       anterior (id_evento_anterior). id_operacao liga ao Log de
--       Operacoes, SEM ForeignKey de proposito (mesmo padrao de
--       numero_comunicado) - o Log pode ser limpo sem apagar o evento.
--   tb_blk_8003_envios - uma linha por EVENTO x PROVEDOR: status, tentativas,
--       proximo reenvio, codigo devolvido e link de verificacao.
--       Status: PENDENTE, ENVIANDO (o "carteiro" pegou), CONFIRMADO, ERRO e
--       CANCELADO (a operacao foi desfeita antes do envio - v1.1.0).
--
--   v1.1.0: status CANCELADO incluido (Desfazer). Quem ja rodou a v1.0.0
--           roda tambem o script 13_.
--
--   O Orion NUNCA grava o SISBOV em claro na rede: sisbov_hash e um HMAC
--   com a chave da Consiste; versao_chave diz qual chave foi usada.
-- =========================================================

DO $blk$
DECLARE
    esquema text;
BEGIN
    FOR esquema IN
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'produtor\_%'
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema = esquema AND table_name = 'tb_4001_gta') THEN

            -- ---------- 8001: provedores ligados ----------
            EXECUTE format($sql$
                CREATE TABLE IF NOT EXISTS %I.tb_blk_8001_produtor_provedores (
                    id            SERIAL PRIMARY KEY,
                    id_provedor   INTEGER     NOT NULL UNIQUE REFERENCES public.tb_blk_8000_provedores(id),
                    ativo         BOOLEAN     NOT NULL DEFAULT TRUE,
                    ambiente      VARCHAR(10) NOT NULL DEFAULT 'TESTE',
                    envia_dono    BOOLEAN     NOT NULL DEFAULT FALSE,
                    criado_em     TIMESTAMP   NOT NULL DEFAULT now(),
                    atualizado_em TIMESTAMP   NOT NULL DEFAULT now(),
                    CONSTRAINT chk_tb_blk_8001_ambiente CHECK (ambiente IN ('TESTE', 'PRODUCAO'))
                )
            $sql$, esquema);

            -- ---------- 8002: eventos (a fila) ----------
            EXECUTE format($sql$
                CREATE TABLE IF NOT EXISTS %I.tb_blk_8002_eventos (
                    id                 SERIAL PRIMARY KEY,
                    id_propriedade     INTEGER      NOT NULL REFERENCES public.propriedades(id),
                    tipo_evento        VARCHAR(30)  NOT NULL,
                    sisbov_hash        VARCHAR(64)  NOT NULL,
                    versao_chave       INTEGER      NOT NULL DEFAULT 1,
                    ficha_animal       JSONB        NOT NULL,
                    ficha_dono         JSONB,
                    hash_animal        VARCHAR(64)  NOT NULL,
                    hash_dono          VARCHAR(64),
                    hash_evento        VARCHAR(64)  NOT NULL,
                    id_evento_anterior INTEGER      REFERENCES %I.tb_blk_8002_eventos(id),
                    id_operacao        INTEGER,
                    id_usuario         INTEGER      REFERENCES public.usuarios(id),
                    ocorrido_em        TIMESTAMP    NOT NULL,
                    criado_em          TIMESTAMP    NOT NULL DEFAULT now()
                )
            $sql$, esquema, esquema);

            EXECUTE format('CREATE INDEX IF NOT EXISTS ix_tb_blk_8002_sisbov_hash ON %I.tb_blk_8002_eventos (sisbov_hash, ocorrido_em)', esquema);
            EXECUTE format('CREATE INDEX IF NOT EXISTS ix_tb_blk_8002_propriedade ON %I.tb_blk_8002_eventos (id_propriedade, ocorrido_em)', esquema);

            -- ---------- 8003: envios (evento x provedor) ----------
            EXECUTE format($sql$
                CREATE TABLE IF NOT EXISTS %I.tb_blk_8003_envios (
                    id               SERIAL PRIMARY KEY,
                    id_evento        INTEGER      NOT NULL REFERENCES %I.tb_blk_8002_eventos(id),
                    id_provedor      INTEGER      NOT NULL REFERENCES public.tb_blk_8000_provedores(id),
                    ambiente         VARCHAR(10)  NOT NULL DEFAULT 'TESTE',
                    status           VARCHAR(12)  NOT NULL DEFAULT 'PENDENTE',
                    tentativas       INTEGER      NOT NULL DEFAULT 0,
                    proximo_envio    TIMESTAMP    NOT NULL DEFAULT now(),
                    codigo_retorno   VARCHAR(200),
                    url_verificacao  VARCHAR(500),
                    erro             TEXT,
                    enviado_em       TIMESTAMP,
                    confirmado_em    TIMESTAMP,
                    criado_em        TIMESTAMP    NOT NULL DEFAULT now(),
                    atualizado_em    TIMESTAMP    NOT NULL DEFAULT now(),
                    CONSTRAINT uq_tb_blk_8003_evento_provedor UNIQUE (id_evento, id_provedor),
                    CONSTRAINT chk_tb_blk_8003_status CHECK (status IN ('PENDENTE', 'ENVIANDO', 'CONFIRMADO', 'ERRO', 'CANCELADO')),
                    CONSTRAINT chk_tb_blk_8003_ambiente CHECK (ambiente IN ('TESTE', 'PRODUCAO'))
                )
            $sql$, esquema, esquema);

            EXECUTE format('CREATE INDEX IF NOT EXISTS ix_tb_blk_8003_fila ON %I.tb_blk_8003_envios (status, proximo_envio)', esquema);

            RAISE NOTICE '% -> tb_blk_8001, 8002 e 8003 OK', esquema;
        END IF;
    END LOOP;
END $blk$;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\12_create_tb_blk_8001_8003_produtor.sql
-- =========================================================