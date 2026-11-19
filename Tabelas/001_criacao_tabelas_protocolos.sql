-- ============================================================
-- Projeto: Orion SISBOV
-- Arquivo: 001_criacao_tabelas_protocolos.sql
-- Módulo: GERAS - Protocolos de Certificação (ABPO, PEFB, CSCB, Cota Hilton, etc.)
-- Sessão: 011
-- Data: 03/07/2026
-- Horário: 14:41
-- Responsável: Benedito Silva Filho
-- Companheiro de Viagem: Clau (Claude Sonnet 5)
-- ============================================================
-- Histórico de Versões:
-- v1.0.0 - 03/07/2026 14:41 - Criação inicial das tabelas protocolos
--                             e propriedade_protocolo, com triggers
--                             de auditoria dedicados.
-- ============================================================
-- Contexto (alinhado em conversa antes de codar):
-- Protocolos são selos/certificações de valor agregado que uma
-- Propriedade pode aderir voluntariamente (ex: ABPO, PEFB, CSCB,
-- Cota Hilton). O catálogo é administrável (não fixo), pois novos
-- protocolos podem surgir ou mudar de sigla no futuro.
-- A Propriedade ativa o protocolo por autodeclaração; a partir da
-- data de ativação, o histórico do protocolo passa a ser contado.
-- Desativação pode ser voluntária (decisão do Produtor) ou
-- compulsória (irregularidade constatada por entidade externa).
-- ============================================================


-- ============================================================
-- BLOCO 1: Tabela protocolos (catálogo administrável)
-- ============================================================
-- Guarda os protocolos existentes (ABPO, PEFB, CSCB, Cota Hilton...).
-- Terá tela própria de administração (Configurações > Protocolos)
-- para criar/editar/inativar qualquer protocolo, atual ou futuro.

CREATE TABLE protocolos (
    id                  SERIAL PRIMARY KEY,
    codigo              VARCHAR(20)     NOT NULL,
    nome                VARCHAR(150)    NOT NULL,
    resumo              VARCHAR(200)    NOT NULL,
    descricao           TEXT,
    tipo_vinculo        VARCHAR(20)     NOT NULL,
    ativo               BOOLEAN         NOT NULL DEFAULT TRUE,
    criado_em           TIMESTAMP       NOT NULL DEFAULT NOW(),
    atualizado_em       TIMESTAMP       NOT NULL DEFAULT NOW(),

    CONSTRAINT protocolos_codigo_unique UNIQUE (codigo),
    CONSTRAINT protocolos_tipo_vinculo_check
        CHECK (tipo_vinculo IN ('propriedade', 'planta_industrial'))
);

COMMENT ON TABLE protocolos IS 'Catálogo administrável de protocolos/selos de certificação (ex: ABPO, PEFB, CSCB, Cota Hilton)';
COMMENT ON COLUMN protocolos.codigo IS 'Sigla curta do protocolo, ex: PEFB';
COMMENT ON COLUMN protocolos.resumo IS 'Texto curto (1-2 linhas) exibido na listagem e no card da Propriedade';
COMMENT ON COLUMN protocolos.descricao IS 'Explicação completa do protocolo, exibida ao detalhar';
COMMENT ON COLUMN protocolos.tipo_vinculo IS 'Define onde o protocolo se ancora: propriedade ou planta_industrial (ex: CSCB/curtume)';


-- Trigger dedicado de atualizado_em (padrão do projeto: uma função
-- por tabela, sem função genérica compartilhada)

CREATE OR REPLACE FUNCTION trg_protocolos_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_protocolos_atualizado_em
    BEFORE UPDATE ON protocolos
    FOR EACH ROW
    EXECUTE FUNCTION trg_protocolos_atualizado_em();


-- ============================================================
-- BLOCO 2: Tabela propriedade_protocolo (vínculo)
-- ============================================================
-- Registra quais protocolos cada Propriedade ativou, quando, e o
-- desfecho caso tenha sido desativado (voluntário ou compulsório).
-- Um mesmo par Propriedade+Protocolo pode ter várias linhas ao
-- longo do tempo (histórico de adesão/saída), mas só pode haver
-- UM vínculo com status 'ativo' por vez (garantido pelo índice
-- único parcial abaixo).

CREATE TABLE propriedade_protocolo (
    id                      SERIAL PRIMARY KEY,
    id_propriedade          INTEGER         NOT NULL,
    id_protocolo            INTEGER         NOT NULL,
    data_ativacao           DATE            NOT NULL DEFAULT CURRENT_DATE,
    status                  VARCHAR(10)     NOT NULL DEFAULT 'ativo',
    motivo_inativacao       VARCHAR(15),
    observacao_inativacao   TEXT,
    data_desativacao        DATE,
    criado_em               TIMESTAMP       NOT NULL DEFAULT NOW(),
    atualizado_em           TIMESTAMP       NOT NULL DEFAULT NOW(),

    CONSTRAINT propriedade_protocolo_id_propriedade_fkey
        FOREIGN KEY (id_propriedade) REFERENCES propriedades(id),
    CONSTRAINT propriedade_protocolo_id_protocolo_fkey
        FOREIGN KEY (id_protocolo) REFERENCES protocolos(id),
    CONSTRAINT propriedade_protocolo_status_check
        CHECK (status IN ('ativo', 'inativo')),
    CONSTRAINT propriedade_protocolo_motivo_check
        CHECK (motivo_inativacao IS NULL OR motivo_inativacao IN ('voluntaria', 'compulsoria'))
);

COMMENT ON TABLE propriedade_protocolo IS 'Vínculo entre Propriedade e Protocolo, com histórico de ativação/desativação';
COMMENT ON COLUMN propriedade_protocolo.data_ativacao IS 'Marco temporal: histórico do protocolo só conta a partir desta data';
COMMENT ON COLUMN propriedade_protocolo.motivo_inativacao IS 'voluntaria (Produtor desistiu) ou compulsoria (irregularidade constatada por entidade externa)';

-- Garante no máximo um vínculo ATIVO por Propriedade+Protocolo
-- (permite reativação futura, criando nova linha, sem apagar histórico)
CREATE UNIQUE INDEX propriedade_protocolo_ativo_unique
    ON propriedade_protocolo (id_propriedade, id_protocolo)
    WHERE status = 'ativo';


-- Trigger dedicado de atualizado_em

CREATE OR REPLACE FUNCTION trg_propriedade_protocolo_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_propriedade_protocolo_atualizado_em
    BEFORE UPDATE ON propriedade_protocolo
    FOR EACH ROW
    EXECUTE FUNCTION trg_propriedade_protocolo_atualizado_em();


-- ============================================================
-- BLOCO 3: Carga inicial dos protocolos conhecidos
-- ============================================================
-- Popula o catálogo com os 4 protocolos já mapeados nesta sessão.
-- Novos protocolos futuros entram pela tela de administração,
-- não é mais necessário alterar SQL manualmente.

INSERT INTO protocolos (codigo, nome, resumo, descricao, tipo_vinculo) VALUES
(
    'ABPO',
    'Associação Brasileira de Produtores Orgânicos',
    'Carne Orgânica e Sustentável do Pantanal, sem transgênicos, hormônios ou antibióticos preventivos.',
    'Protocolo voltado à produção da Carne Orgânica e Sustentável do Pantanal. Exige regras rígidas baseadas na Lei dos Orgânicos: proíbe uso de grãos transgênicos, ureia, hormônios, antibióticos preventivos e ionóforos. Foco em sustentabilidade ambiental, bem-estar animal e responsabilidade social. Produtor recebe prêmio financeiro por arroba, mas passa por auditorias severas.',
    'propriedade'
),
(
    'PEFB',
    'Protocolo de Exportação de Fêmeas Bovinas',
    'Garante que fêmeas exportadas para a Europa nunca receberam estradiol e estão no SISBOV.',
    'Protocolo setorial homologado pelo MAPA, criado para garantir exportações de carne bovina brasileira à União Europeia. Garante que as fêmeas nunca receberam estradiol em nenhuma fase da vida. Propriedade precisa ser SISBOV/ERAS e as fêmeas devem entrar na fazenda certificada com idade igual ou inferior a 12 meses.',
    'propriedade'
),
(
    'CSCB',
    'Certificação de Sustentabilidade do Couro Brasileiro',
    'Avalia curtumes em pilares econômico, ambiental, social e de gestão, com medalhas Bronze a Diamante.',
    'Certificação com respaldo do Inmetro, aplicada à Planta Industrial (curtume). Avalia origem legal e livre de desmatamento do gado, eficiência no uso de água e energia, eliminação correta de resíduos químicos (como o cromo) e garantia de trabalho seguro. Curtumes recebem medalhas: Bronze, Prata, Ouro ou Diamante. A rastreabilidade da pele, porém, depende da Propriedade de origem.',
    'planta_industrial'
),
(
    'HILTON',
    'Cota Hilton',
    'Cota de exportação de cortes bovinos de alta qualidade para a União Europeia, com redução de até 20% na taxa.',
    'Acordo comercial criado em 1979 que permite exportação limitada de cortes bovinos de alta qualidade para a União Europeia. Exige propriedade cadastrada no SISBOV/ERAS, animais identificados antes dos 10 meses de idade, permanência mínima de 90 dias (noventena) na fazenda de terminação antes do abate, e frigorífico habilitado. Reduz em até 20% a taxa cobrada pela UE e gera bonificação por arroba.',
    'propriedade'
);