-- =========================================================
-- PROJETO: Orion
-- PASTA: C:\orion\database (ajustar conforme sua pasta de migrations)
-- MODULO: sql_criacao_tb_1007_motivo_mortes.sql
-- AUTOR: Benedito Silva Filho.
-- CRIADO EM: 2026-07-23 12:13 -03
-- ATUALIZADO EM: 2026-07-23 12:13 -03
-- VERSAO: 1.0.0
--
-- DESCRICAO:
--     Cria o ENUM categoria_motivo_morte_enum e a tabela
--     tb_1007_motivo_mortes (schema publico), correspondente
--     a GR1007 do GERAS ("Motivos Morte"). Catalogo em
--     tabela (nao enum) porque o MAPA pode incluir novos
--     motivos ou inativar existentes ao longo do tempo -
--     decisao da Sessao de Parelhamento Orion x GERAS
--     (pasta 1-Cadastros). A categoria (ABATE/NATURAL/
--     SACRIFICIO) e fixa (3 valores, dificilmente muda) e
--     por isso ficou como ENUM, nao tabela separada.
--
--     Uso: motivo aplicavel apenas na tela de tipo_movimento
--     MORTE (Saida). Abate para Frigorifico e um fluxo
--     separado (GTA com Frigorifico vinculado), nao usa
--     este catalogo mesmo quando a categoria do motivo e
--     ABATE - confirmado com o Navigator.
--
--     v1.0.0: Criacao do modulo.
--             - ENUM categoria_motivo_morte_enum.
--             - Tabela tb_1007_motivo_mortes com id,
--               codigo_geras, descricao, categoria, ativo,
--               criado_em, atualizado_em.
--             - Trigger dedicada trg_tb_1007_motivo_mortes_atualizado_em.
--             - Seed com os 44 motivos oficiais do GERAS
--               (fonte: GR1007.TXT). Todos ativos (True),
--               conforme confirmado pelo Navigator.
-- =========================================================

-- ---------------------------------------------------------
-- 1. ENUM de categoria
-- ---------------------------------------------------------
CREATE TYPE public.categoria_motivo_morte_enum AS ENUM (
    'ABATE',
    'NATURAL',
    'SACRIFICIO'
);

-- ---------------------------------------------------------
-- 2. Tabela de catalogo
-- ---------------------------------------------------------
CREATE TABLE public.tb_1007_motivo_mortes (
    id              SERIAL PRIMARY KEY,
    codigo_geras    VARCHAR(3)   NOT NULL UNIQUE,
    descricao       VARCHAR(150) NOT NULL,
    categoria       public.categoria_motivo_morte_enum NOT NULL,
    ativo           BOOLEAN      NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.tb_1007_motivo_mortes IS 'Catalogo de Motivos de Morte (GR1007 do GERAS) - usado no tipo_movimento MORTE (Saida).';

-- ---------------------------------------------------------
-- 3. Trigger dedicada
-- ---------------------------------------------------------
CREATE OR REPLACE FUNCTION public.trg_fn_tb_1007_motivo_mortes_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_tb_1007_motivo_mortes_atualizado_em
    BEFORE UPDATE ON public.tb_1007_motivo_mortes
    FOR EACH ROW
    EXECUTE FUNCTION public.trg_fn_tb_1007_motivo_mortes_atualizado_em();

-- ---------------------------------------------------------
-- 4. Seed - 44 motivos oficiais (fonte: GR1007.TXT)
-- ---------------------------------------------------------
INSERT INTO public.tb_1007_motivo_mortes (codigo_geras, descricao, categoria) VALUES
('001', 'Abate',                                                      'SACRIFICIO'),
('002', 'Abate em Frigorífico SIM, SIE e SIF não exportador',         'ABATE'),
('003', 'Abate no Frigorífico SIF exportação',                        'NATURAL'),
('004', 'Abate para consumo na propriedade',                          'ABATE'),
('005', 'Abate para fechamento da propriedade',                       'NATURAL'),
('006', 'Abate sanitário',                                            'SACRIFICIO'),
('007', 'Abigeato ou desaparecimento',                                'NATURAL'),
('008', 'Acidente ofídico',                                           'NATURAL'),
('009', 'Afogamento/atolamento',                                      'NATURAL'),
('010', 'Anaplasmose/babesiose/piroplasmose',                         'NATURAL'),
('011', 'Ataque por predadores',                                      'NATURAL'),
('012', 'Botulismo',                                                  'NATURAL'),
('013', 'Brucelose',                                                  'NATURAL'),
('014', 'Complicações pós parto/parto distócico',                     'NATURAL'),
('015', 'Debilidade por idade avançada',                              'NATURAL'),
('016', 'Deficiência nutricional',                                    'NATURAL'),
('017', 'Descarga elétrica',                                          'NATURAL'),
('018', 'Descarte',                                                   'NATURAL'),
('019', 'Distúrbios metabólicos',                                     'NATURAL'),
('020', 'Doença parasitária',                                         'NATURAL'),
('021', 'Doenças bacterianas',                                        'NATURAL'),
('022', 'Hipotermia',                                                 'NATURAL'),
('023', 'Informação indisponível',                                    'NATURAL'),
('024', 'Ingestão de corpo estranho',                                 'NATURAL'),
('025', 'Insuficiência cardíaca',                                     'NATURAL'),
('026', 'Intoxicação',                                                'NATURAL'),
('027', 'Leucose',                                                    'NATURAL'),
('028', 'Mastite crônica',                                            'NATURAL'),
('029', 'Mastite septicêmica/gangrenosa',                             'NATURAL'),
('030', 'Metrite',                                                    'NATURAL'),
('031', 'Morte durante o transporte',                                 'NATURAL'),
('032', 'Morte natural por idade avançada',                           'NATURAL'),
('033', 'Neoplasia',                                                  'NATURAL'),
('034', 'Pleuropneumonia',                                            'NATURAL'),
('035', 'Pododermatite',                                              'NATURAL'),
('036', 'Problemas reprodutivos',                                     'NATURAL'),
('037', 'Raiva',                                                      'NATURAL'),
('038', 'Raiva (por diagnóstico laboratorial)',                       'NATURAL'),
('039', 'Septicemia',                                                 'NATURAL'),
('040', 'Timpanismo',                                                 'NATURAL'),
('041', 'Torção do abomaso',                                          'NATURAL'),
('042', 'Traumatismo/fratura',                                        'NATURAL'),
('043', 'Tuberculose',                                                'NATURAL'),
('044', 'Causa desconhecida',                                         'NATURAL');

-- =========================================================
-- FIM DE ARQUIVO: sql_criacao_tb_1007_motivo_mortes.sql
-- =========================================================