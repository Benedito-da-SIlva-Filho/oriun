-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\Tabelas
-- MODULO: Tabelas\criar_tb_2020_2002_2011_s098.sql
-- AUTOR: Benedito Silva Filho
-- CRIADO EM: 2026-10-16 14:16 -03
-- ATUALIZADO EM: 2026-10-16 14:16 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--   Sessao 098 - SAIDAS (Abate). Cria em TODOS os schemas produtor_NNNNN:
--     tb_2020_embarque       leituras de saida no brete (molde: tb_5001)
--     tb_2002_saida_animais  o animal depois da saida (Abate/Venda/Morte/Transf.)
--     tb_2011_com_saidas     Comunicado de Saida (molde: tb_2012)
--   Tambem cria: CHECKs (tipo_saida, tipo_morte, destino_morte), o indice
--   unico parcial uq_tb_2020_sisbov_aberto (o mesmo animal nao fica em duas
--   leituras abertas) e os indices de consulta. Sobe a versao do banco
--   (tb_versao_schema) para 3, junto com VERSAO_SCHEMA_ATUAL = 3 do
--   backup_helper.py v1.5.0.
--   Pode rodar mais de uma vez sem estragar nada (IF NOT EXISTS; a versao so
--   sobe). Schema sem tb_4001_gta, tb_4005_racas ou tb_versao_schema e PULADO
--   com aviso (WARNING). Nenhuma tabela existente e alterada.
--   RODAR ANTES de instalar os arquivos .py.
--
--   v1.0.0: Criacao (Sessao 098).
-- =========================================================

DO $blk$
DECLARE
    esquema text;
BEGIN
    FOR esquema IN
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'produtor\_%'
        ORDER BY schema_name
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = esquema AND table_name = 'tb_4001_gta')
           AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = esquema AND table_name = 'tb_4005_racas')
           AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = esquema AND table_name = 'tb_versao_schema') THEN

            -- ---------- tb_2020_embarque ----------
            EXECUTE format($sql$
                CREATE TABLE IF NOT EXISTS %1$I.tb_2020_embarque (
                    id                         SERIAL PRIMARY KEY,
                    id_propriedade             INTEGER NOT NULL REFERENCES public.propriedades(id),
                    id_animal                  INTEGER,  -- id do animal em tb_2001 - SEM ForeignKey (tb_2001 apaga a linha na saida)
                    sisbov                     VARCHAR(15) NOT NULL,
                    manejo                     VARCHAR(6),
                    rfid                       VARCHAR(15),
                    id_especie                 INTEGER REFERENCES public.tb_4002_especie(id),
                    sexo                       public.sexo_enum,
                    nascimento                 DATE,
                    eras_dias                  INTEGER,
                    id_aptidao                 INTEGER REFERENCES public.tb_4004_aptidao(id),
                    id_raca                    INTEGER REFERENCES %1$I.tb_4005_racas(id),
                    cota_hilton                BOOLEAN NOT NULL DEFAULT FALSE,
                    liberacao_abate            DATE,
                    gta_entrada                VARCHAR(10),
                    gta_entrada_emissao        DATE,
                    gta_entrada_validade       DATE,
                    gta_entrada_animais        INTEGER,
                    data_inclusao              DATE,
                    lote_entrada               VARCHAR(30),
                    origem_propriedade         VARCHAR(150),
                    origem_cpf_cnpj            VARCHAR(18),
                    tipo_saida                 VARCHAR(20) NOT NULL DEFAULT 'ABATE',  -- ABATE / VENDA / MORTE / TRANSFER (CHECK no banco)
                    data_embarque              DATE NOT NULL,  -- dia da leitura no brete
                    hora_embarque              TIME,
                    id_frigorifico             INTEGER REFERENCES public.tb_frigorificos(id),
                    id_gta                     INTEGER REFERENCES %1$I.tb_4001_gta(id),  -- GTA de saida: vazia na leitura, preenchida na Consulta Embarque
                    lote_saida                 VARCHAR(30),  -- em branco quando nao houver lote de saida
                    peso_saida                 NUMERIC(10,2),
                    aceite_fora_liberacao      BOOLEAN NOT NULL DEFAULT FALSE,  -- Aviso A: "Estou ciente e assumo" (animal fora da Liberacao para Abate)
                    aceite_fora_liberacao_por  INTEGER,  -- id do usuario que aceitou
                    aceite_fora_liberacao_em   TIMESTAMP,
                    aceite_era_0_12            BOOLEAN NOT NULL DEFAULT FALSE,  -- Aviso B: "Estou ciente" (animal na ERAS 0 a 12 meses)
                    aceite_era_0_12_por        INTEGER,  -- id do usuario que aceitou
                    aceite_era_0_12_em         TIMESTAMP,
                    sts                        BOOLEAN NOT NULL DEFAULT FALSE,  -- False = lido, Comunicado ainda nao gerado; True = Comunicado gerado
                    numero_comunicado          INTEGER,  -- SEM ForeignKey, mesmo padrao de tb_5001
                    criado_em                  TIMESTAMP NOT NULL DEFAULT now(),
                    atualizado_em              TIMESTAMP NOT NULL DEFAULT now()
                )
            $sql$, esquema);

            -- ---------- tb_2002_saida_animais ----------
            EXECUTE format($sql$
                CREATE TABLE IF NOT EXISTS %1$I.tb_2002_saida_animais (
                    id                         SERIAL PRIMARY KEY,
                    id_propriedade             INTEGER NOT NULL REFERENCES public.propriedades(id),
                    id_animal                  INTEGER,  -- id que o animal tinha em tb_2001 - SEM ForeignKey
                    id_embarque                INTEGER REFERENCES %1$I.tb_2020_embarque(id),  -- leitura de origem (vazio na Morte)
                    sisbov                     VARCHAR(15) NOT NULL,
                    manejo                     VARCHAR(6),
                    rfid                       VARCHAR(15),
                    id_especie                 INTEGER REFERENCES public.tb_4002_especie(id),
                    sexo                       public.sexo_enum,
                    nascimento                 DATE,
                    eras_dias                  INTEGER,
                    id_aptidao                 INTEGER REFERENCES public.tb_4004_aptidao(id),
                    id_raca                    INTEGER REFERENCES %1$I.tb_4005_racas(id),
                    cota_hilton                BOOLEAN NOT NULL DEFAULT FALSE,
                    liberacao_abate            DATE,
                    gta_entrada                VARCHAR(10),
                    gta_entrada_emissao        DATE,
                    gta_entrada_validade       DATE,
                    gta_entrada_animais        INTEGER,
                    data_inclusao              DATE,
                    lote_entrada               VARCHAR(30),
                    origem_propriedade         VARCHAR(150),
                    origem_cpf_cnpj            VARCHAR(18),
                    tipo_saida                 VARCHAR(20) NOT NULL,  -- ABATE / VENDA / MORTE / TRANSFER (CHECK no banco)
                    gta_saida                  VARCHAR(10),
                    gta_saida_emissao          DATE,
                    gta_saida_validade         DATE,
                    gta_saida_animais          INTEGER,
                    id_gta                     INTEGER REFERENCES %1$I.tb_4001_gta(id),
                    id_frigorifico             INTEGER REFERENCES public.tb_frigorificos(id),
                    destino_propriedade        VARCHAR(150),
                    destino_cpf_cnpj           VARCHAR(18),
                    data_embarque              DATE,  -- dia da leitura no brete
                    data_saida                 DATE NOT NULL,  -- dia em que o animal saiu da propriedade (informada no escritorio)
                    numero_comunicado          INTEGER,
                    lote_saida                 VARCHAR(30),
                    peso_saida                 NUMERIC(10,2),
                    tipo_morte                 VARCHAR(15),  -- ACIDENTAL / DESLIGADO / NATURAL / SACRIFICIO (padrao MAPA, CHECK no banco)
                    id_motivo_morte            INTEGER REFERENCES public.tb_1007_motivo_mortes(id),  -- Causa Mortis (catalogo MAPA)
                    destino_morte              VARCHAR(15),  -- CREMACAO / ENTERRAMENTO / OUTROS (padrao MAPA, CHECK no banco)
                    aceite_fora_liberacao      BOOLEAN NOT NULL DEFAULT FALSE,  -- Aviso A: "Estou ciente e assumo" (animal fora da Liberacao para Abate)
                    aceite_fora_liberacao_por  INTEGER,  -- id do usuario que aceitou
                    aceite_fora_liberacao_em   TIMESTAMP,
                    aceite_era_0_12            BOOLEAN NOT NULL DEFAULT FALSE,  -- Aviso B: "Estou ciente" (animal na ERAS 0 a 12 meses)
                    aceite_era_0_12_por        INTEGER,  -- id do usuario que aceitou
                    aceite_era_0_12_em         TIMESTAMP,
                    substituido                BOOLEAN NOT NULL DEFAULT FALSE,  -- True = animal lido que NAO embarcou; fica no historico (nunca e apagado)
                    substituido_em             TIMESTAMP,
                    id_usuario_substituicao    INTEGER,
                    sisbov_substituto          VARCHAR(15),  -- numero do animal que embarcou no lugar
                    criado_em                  TIMESTAMP NOT NULL DEFAULT now(),
                    atualizado_em              TIMESTAMP NOT NULL DEFAULT now()
                )
            $sql$, esquema);

            -- ---------- tb_2011_com_saidas ----------
            EXECUTE format($sql$
                CREATE TABLE IF NOT EXISTS %1$I.tb_2011_com_saidas (
                    id                         SERIAL PRIMARY KEY,
                    id_propriedade_origem      INTEGER NOT NULL REFERENCES public.propriedades(id),
                    cpf_cnpj_produtor_origem   VARCHAR(18),
                    numero_comunicado          INTEGER NOT NULL,
                    tipo_saida                 VARCHAR(20) NOT NULL,  -- ABATE / VENDA / MORTE / TRANSFER (CHECK no banco)
                    id_gta                     INTEGER REFERENCES %1$I.tb_4001_gta(id),
                    gta_numero                 VARCHAR(10) NOT NULL,
                    gta_data_emissao           DATE,
                    gta_data_validade          DATE,
                    data_saida                 DATE,  -- dia em que os animais saem da propriedade
                    qtd_animais                INTEGER,
                    data_inclusao              DATE NOT NULL DEFAULT CURRENT_DATE,
                    id_frigorifico             INTEGER REFERENCES public.tb_frigorificos(id),
                    cpf_cnpj_destino           VARCHAR(18),
                    status                     VARCHAR(20) NOT NULL DEFAULT 'ABERTO',  -- ABERTO -> IMPRESSO
                    data_envio                 DATE,
                    impresso_em                TIMESTAMP,
                    id_usuario_impressao       INTEGER,
                    criado_em                  TIMESTAMP NOT NULL DEFAULT now(),
                    atualizado_em              TIMESTAMP NOT NULL DEFAULT now()
                )
            $sql$, esquema);

            -- ---------- CHECKs (nomes iguais aos do onboarding.py) ----------
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_tb_2020_tipo_saida' AND conrelid = format('%I.tb_2020_embarque', esquema)::regclass) THEN
                EXECUTE format('ALTER TABLE %I.tb_2020_embarque ADD CONSTRAINT chk_tb_2020_tipo_saida CHECK (tipo_saida IN (''ABATE'', ''VENDA'', ''MORTE'', ''TRANSFER''))', esquema);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_tb_2002_tipo_saida' AND conrelid = format('%I.tb_2002_saida_animais', esquema)::regclass) THEN
                EXECUTE format('ALTER TABLE %I.tb_2002_saida_animais ADD CONSTRAINT chk_tb_2002_tipo_saida CHECK (tipo_saida IN (''ABATE'', ''VENDA'', ''MORTE'', ''TRANSFER''))', esquema);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_tb_2002_tipo_morte' AND conrelid = format('%I.tb_2002_saida_animais', esquema)::regclass) THEN
                EXECUTE format('ALTER TABLE %I.tb_2002_saida_animais ADD CONSTRAINT chk_tb_2002_tipo_morte CHECK (tipo_morte IS NULL OR tipo_morte IN (''ACIDENTAL'', ''DESLIGADO'', ''NATURAL'', ''SACRIFICIO''))', esquema);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_tb_2002_destino_morte' AND conrelid = format('%I.tb_2002_saida_animais', esquema)::regclass) THEN
                EXECUTE format('ALTER TABLE %I.tb_2002_saida_animais ADD CONSTRAINT chk_tb_2002_destino_morte CHECK (destino_morte IS NULL OR destino_morte IN (''CREMACAO'', ''ENTERRAMENTO'', ''OUTROS''))', esquema);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_tb_2011_tipo_saida' AND conrelid = format('%I.tb_2011_com_saidas', esquema)::regclass) THEN
                EXECUTE format('ALTER TABLE %I.tb_2011_com_saidas ADD CONSTRAINT chk_tb_2011_tipo_saida CHECK (tipo_saida IN (''ABATE'', ''VENDA'', ''MORTE'', ''TRANSFER''))', esquema);
            END IF;

            -- ---------- indices ----------
            EXECUTE format('CREATE UNIQUE INDEX IF NOT EXISTS uq_tb_2020_sisbov_aberto ON %I.tb_2020_embarque (sisbov) WHERE sts = FALSE', esquema);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_tb_2020_embarque_data ON %I.tb_2020_embarque (id_propriedade, data_embarque)', esquema);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_tb_2002_sisbov ON %I.tb_2002_saida_animais (sisbov)', esquema);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_tb_2002_comunicado ON %I.tb_2002_saida_animais (id_propriedade, numero_comunicado)', esquema);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_tb_2011_comunicado ON %I.tb_2011_com_saidas (id_propriedade_origem, numero_comunicado)', esquema);

            -- ---------- versao do banco = 3 ----------
            EXECUTE format('UPDATE %I.tb_versao_schema SET versao = 3 WHERE versao < 3', esquema);
            EXECUTE format('INSERT INTO %I.tb_versao_schema (versao) SELECT 3 WHERE NOT EXISTS (SELECT 1 FROM %I.tb_versao_schema)', esquema, esquema);

            RAISE NOTICE '% -> 3 tabelas OK e versao 3 OK', esquema;
        ELSE
            RAISE WARNING '% -> PULADO (falta tb_4001_gta, tb_4005_racas ou tb_versao_schema)', esquema;
        END IF;
    END LOOP;
END $blk$;

-- =========================================================
-- CONFERENCIA (rodar depois; o resultado esperado esta em cada comentario)
-- =========================================================

-- 1) Colunas por tabela em cada schema. Esperado: tb_2020_embarque = 39, tb_2002_saida_animais = 52, tb_2011_com_saidas = 20
SELECT table_schema, table_name, count(*) AS colunas
  FROM information_schema.columns
 WHERE table_name IN ('tb_2020_embarque','tb_2002_saida_animais','tb_2011_com_saidas')
   AND table_schema LIKE 'produtor\_%'
 GROUP BY table_schema, table_name ORDER BY table_schema, table_name;

-- 2) Versao do banco em cada schema. Esperado: 3
SELECT table_schema,
       (xpath('/row/versao/text()', query_to_xml(format('SELECT versao FROM %I.tb_versao_schema', table_schema), false, true, '')))[1]::text AS versao
  FROM information_schema.tables
 WHERE table_name = 'tb_versao_schema' AND table_schema LIKE 'produtor\_%'
 ORDER BY table_schema;

-- 3) Travas e indices. Esperado: 5 CHECKs e 5 indices por schema
SELECT n.nspname AS schema, c.conname FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace
 WHERE c.conname IN ('chk_tb_2020_tipo_saida','chk_tb_2002_tipo_saida','chk_tb_2002_tipo_morte','chk_tb_2002_destino_morte','chk_tb_2011_tipo_saida')
 ORDER BY 1, 2;
SELECT schemaname, indexname FROM pg_indexes
 WHERE indexname IN ('uq_tb_2020_sisbov_aberto','idx_tb_2020_embarque_data','idx_tb_2002_sisbov','idx_tb_2002_comunicado','idx_tb_2011_comunicado')
 ORDER BY 1, 2;

-- =========================================================
-- FIM DE ARQUIVO: Tabelas\criar_tb_2020_2002_2011_s098.sql
-- =========================================================
