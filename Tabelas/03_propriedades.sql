-- =============================================================
-- ORION SISBOV
-- Sessão 009 — Implementação do Banco de Dados (Módulo GERAS)
-- Arquivo: 03_propriedades.sql
-- Tabela 3 de 10: propriedades
-- Data: 01/07/2026
-- Hora de início: 12:26
-- Responsável: Benedito Silva Filho
-- Companheiro de Viagem: Clau (Claude Sonnet 5)
--
-- Histórico de versão:
--   v1.0 - 01/07/2026 12:26 - Criação inicial - Clau
--
-- Descrição:
--   Recria a tabela "propriedades" (o ERAS — Estabelecimento Rural
--   Aprovado no SISBOV), fundindo o modelo SISBOV 2.0 com os campos
--   já existentes no banco e com o modelo de negócio da Consiste.
--
--   IMPORTANTE — decisões desta sessão:
--   1. Tabela estava ZERADA — seguro fazer DROP + CREATE.
--   2. "codigo_sisbov" (nome antigo) = "codigo_eras" — apenas
--      renomeado, mesmo conceito (código da fazenda no MAPA).
--   3. "inscricao_est" foi mantido AQUI TAMBÉM como
--      "inscricao_estadual" — a propriedade tem a sua própria
--      inscrição estadual, além da que o Produtor tem em
--      "propriedade_produtor" (dados distintos, não duplicidade).
--   4. Endereço migrado do formato genérico (endereco/cidade) para
--      o formato detalhado (logradouro/numero/complemento/bairro/
--      municipio/uf), conforme padrão SISBOV 2.0.
--   5. "nirf" e "incra" foram FUNDIDOS em um único campo
--      "nirf_incra" — a propriedade preenche um ou outro, nunca
--      os dois (na prática, quase nunca é preenchido).
--   6. "razao_social" NÃO entra — o formulário oficial do MAPA não
--      pede esse campo para propriedades.
--   7. "oesa" é campo NOVO — Código no Órgão Executor de Sanidade
--      Agropecuária (IDAF, IMA, INDEA, etc.), essencial para
--      emissão de GTA. Opcional no banco (obrigatório só quando a
--      propriedade participa do SISBOV — validação na aplicação).
--   8. "codigo_eras" é OPCIONAL — sua presença/ausência é o próprio
--      indicador de participação no SISBOV. Esta tela (plataforma
--      Consiste) cadastra apenas propriedades NÃO-ERAS; quando a
--      propriedade se torna ERAS, é a Certificadora quem cadastra
--      esse vínculo em outro fluxo (fora do escopo desta sessão).
--   9. "status_atividade" é campo NOVO (Ativo/Suspenso/Cancelado) —
--      status operacional amplo do SISBOV, distinto dos booleanos
--      habilitada/certificada/suspensa. Opcional — só é preenchido
--      quando a propriedade entra em vistoria/auditoria do SISBOV
--      (ou seja, quando tem codigo_eras).
--   10. "visibilidade" foi DESCARTADO de propriedades (mantido só
--       em proprietarios e produtores).
--   11. "telefone2" é opcional (nem todo mundo tem 2 telefones).
--   12. "certificadora_id" continua OPCIONAL (RN-006) — nesta tela
--       nasce sempre nulo, junto com codigo_eras.
-- =============================================================

-- Bloco 1: Remove a tabela antiga (confirmado zerada, sem risco)
DROP TABLE IF EXISTS propriedades;

-- Bloco 2: Criação da tabela propriedades (modelo fundido)
CREATE TABLE propriedades (
    id                  SERIAL PRIMARY KEY,

    -- Vínculo SISBOV (nascem juntos nulos nesta tela — Consiste)
    certificadora_id    INTEGER REFERENCES certificadoras(id),
    codigo_eras         VARCHAR(20),                -- Código ERAS no MAPA/SISBOV

    -- Identificadores de órgãos (fiscal/ambiental/sanitário)
    nirf_incra          VARCHAR(30),                -- NIRF ou INCRA (um ou outro)
    car                 VARCHAR(50),                -- Cadastro Ambiental Rural
    oesa                VARCHAR(11),                -- Código no Órgão Estadual de Sanidade

    -- Controle interno
    ativo               BOOLEAN         NOT NULL DEFAULT TRUE,

    -- Status SISBOV (só populado quando participa do programa)
    status_atividade    VARCHAR(20),                -- Ativo / Suspenso / Cancelado

    -- Identificação
    nome                VARCHAR(150)    NOT NULL,   -- Nome da fazenda
    inscricao_estadual  VARCHAR(30),                -- Inscrição estadual da própria propriedade
    tipo                VARCHAR(30)     NOT NULL,   -- Confinamento / Criação / Misto

    -- Endereço detalhado (SISBOV 2.0)
    logradouro          VARCHAR(200),
    numero              VARCHAR(10),
    complemento         VARCHAR(100),
    bairro              VARCHAR(100),
    cep                 VARCHAR(9),
    municipio           VARCHAR(100)    NOT NULL,
    uf                  CHAR(2)         NOT NULL,

    -- Contato
    email               VARCHAR(150)    NOT NULL,
    telefone            VARCHAR(20)     NOT NULL,
    telefone2           VARCHAR(20),

    -- Dados operacionais
    area_hectares       NUMERIC(10,2)   NOT NULL,
    latitude            NUMERIC(10,7),              -- preenchimento automático ou manual
    longitude           NUMERIC(10,7),              -- preenchimento automático ou manual
    roteiro_acesso      TEXT            NOT NULL,   -- forma de acesso à propriedade

    -- Controle de datas
    criado_em           TIMESTAMP       NOT NULL DEFAULT NOW(),
    atualizado_em       TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Bloco 3: Comentários de documentação
COMMENT ON TABLE propriedades IS
    'O ERAS — Estabelecimento Rural Aprovado no SISBOV. Cadastro pode existir com ou sem codigo_eras: presença/ausência define participação no SISBOV.';
COMMENT ON COLUMN propriedades.codigo_eras IS
    'Código da fazenda no MAPA/SISBOV (antigo "codigo_sisbov"). Nulo = propriedade fora do SISBOV. Nesta tela (Consiste) nasce sempre nulo.';
COMMENT ON COLUMN propriedades.certificadora_id IS
    'Nulo até vincular Certificadora cliente da Consiste (RN-006). Nesta tela nasce sempre nulo, junto com codigo_eras.';
COMMENT ON COLUMN propriedades.nirf_incra IS
    'NIRF ou INCRA — um ou outro, nunca os dois. Raramente preenchido na prática.';
COMMENT ON COLUMN propriedades.oesa IS
    'Código no Órgão Executor de Sanidade Agropecuária (IDAF, IMA, INDEA, etc). Essencial para emissão de GTA. Obrigatório apenas quando participa do SISBOV (validação na aplicação).';
COMMENT ON COLUMN propriedades.status_atividade IS
    'Status operacional SISBOV: Ativo / Suspenso / Cancelado. Só populado quando a propriedade tem codigo_eras (entra em vistoria/auditoria).';
COMMENT ON COLUMN propriedades.inscricao_estadual IS
    'Inscrição estadual da própria propriedade (distinta da inscrição do Produtor, guardada em propriedade_produtor).';

-- Bloco 4: Índices de busca
CREATE INDEX idx_propriedades_codigo_eras ON propriedades (codigo_eras);
CREATE INDEX idx_propriedades_certificadora_id ON propriedades (certificadora_id);
CREATE INDEX idx_propriedades_municipio_uf ON propriedades (municipio, uf);

-- Bloco 5: Trigger para manter "atualizado_em" sempre corrente
CREATE OR REPLACE FUNCTION trg_propriedades_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_atualizado_em_propriedades
    BEFORE UPDATE ON propriedades
    FOR EACH ROW
    EXECUTE FUNCTION trg_propriedades_atualizado_em();