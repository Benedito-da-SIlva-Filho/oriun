# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\scripts
# MODULO: backend\scripts\popular_racas.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-07 12:30 -03
# ATUALIZADO EM: 2026-09-07 12:30 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Script avulso (roda manualmente, nao faz parte do app.py) -
#     cria a tabela tb_4005_racas (se nao existir) em TODO schema
#     'produtor_%' e popula com a lista real de Racas extraida do
#     GERAS (GR4005.TXT, Sessao 047), corrigindo os caracteres
#     acentuados que vieram corrompidos no arquivo de origem
#     (encoding perdido no export do GERAS).
#
#     IDEMPOTENTE: usa `ON CONFLICT (codigo) DO NOTHING`, entao
#     pode ser reexecutado sem duplicar dados - inclusive serve
#     pra popular um Produtor NOVO no futuro (schema criado depois
#     desta sessao), ja que nao ha nenhum gatilho automatico que
#     faca isso sozinho ainda no provisionamento de schema novo.
#
#     Uso: python -m backend.scripts.popular_racas
#
#     Codigo 'AA' sem nome no arquivo de origem e PROPOSITAL -
#     representa "Nao Informado" (confirmado com Benedito).
#     Codigos 'NE' (Nelore) e 'XX' (Composto) vem com `comum=True`
#     de fabrica - mesmo padrao que o Produtor de referencia ja
#     usava no GERAS; qualquer outro ajuste fica pra tela de
#     selecao do Produtor (sessao futura).
#
#     v1.0.0: Criacao do modulo (Sessao 047).
# =========================================================

from sqlalchemy import text
from backend.database import engine


# -------------------------------------------------------
# Lista de Racas (codigo, nome, comum) - extraida de
# GR4005.TXT (export do GERAS), com acentuacao corrigida
# manualmente (o arquivo original veio com encoding perdido).
# -------------------------------------------------------
RACAS = [
    ('AA', 'Não Informado',                          False),
    ('AF', 'Africander',                             False),
    ('AN', 'Aberdeen Angus',                         False),
    ('AR', 'Red Angus',                              False),
    ('AU', 'Aubrac',                                 False),
    ('AY', 'Ayrshire',                               False),
    ('BA', 'Barzona',                                False),
    ('BB', 'Belgian Blue',                           False),
    ('BD', "Blonde D'Aquitaine",                     False),
    ('BE', 'Beefalo',                                False),
    ('BH', 'Brahmental',                             False),
    ('BL', 'Braler',                                 False),
    ('BM', 'Beefmaster',                             False),
    ('BN', 'Brangus',                                False),
    ('BO', 'Braford',                                False),
    ('BR', 'Brahman',                                False),
    ('BS', 'Pardo Suíço Leite Brown Swuiss',          False),
    ('BT', 'Belmont Red',                            False),
    ('CA', 'Chianina',                               False),
    ('CB', 'Charbray',                               False),
    ('CC', 'Canchim',                                False),
    ('CG', 'Kangaian',                               False),
    ('CH', 'Charolês',                               False),
    ('CL', 'Curraleiro',                             False),
    ('CN', 'Canadiense',                             False),
    ('CO', 'Carabao',                                False),
    ('CP', 'Campino Red Pied',                       False),
    ('CR', 'Caracu',                                 False),
    ('CZ', 'Guzerá',                                 False),
    ('DB', 'Danish Black & White',                   False),
    ('DE', 'Devon',                                  False),
    ('DR', 'Dexter',                                 False),
    ('DS', 'South Devon',                            False),
    ('ER', 'Eringer',                                False),
    ('FA', 'Flamenga',                               False),
    ('FP', 'East Fleming Red Pied',                  False),
    ('FR', 'Fribourg',                               False),
    ('GA', 'Galloway',                               False),
    ('GD', 'Guzolando',                              False),
    ('GH', 'Gir Leiteiro Mocho',                     False),
    ('GI', 'Grauvieh',                               False),
    ('GL', 'Gir Leiteiro',                           False),
    ('GM', 'Gir Mocho',                              False),
    ('GO', 'Gyrolando',                              False),
    ('GR', 'Gronninger',                             False),
    ('GS', 'Gascone',                                False),
    ('GT', 'Guzerá Leiteiro',                        False),
    ('GU', 'Guernsev',                               False),
    ('GV', 'Gelbvieh',                               False),
    ('GY', 'Gir',                                    False),
    ('HC', 'Hays Converter',                         False),
    ('HH', 'Hereford',                               False),
    ('HI', 'Highland',                               False),
    ('HO', 'Holandês',                               False),
    ('HP', 'Hereford Mocho',                         False),
    ('IB', 'Indubrasil',                             False),
    ('JA', 'Jafarabadi',                             False),
    ('JE', 'Jersey',                                 False),
    ('KB', 'Kobe (Wagyu)',                           False),
    ('LA', 'Lavinia',                                False),
    ('LM', 'Limousin',                               False),
    ('LR', 'Lincoln Red',                            False),
    ('LU', 'Luing',                                  False),
    ('MA', 'Maine-Anjou',                            False),
    ('MD', 'Mediterrâneo',                           False),
    ('ME', 'Maremmana',                              False),
    ('MG', 'Murray Gray',                            False),
    ('MI', 'Mueserhineissel',                        False),
    ('MR', 'Marchigiana',                            False),
    ('NE', 'Nelore',                                 True),
    ('NM', 'Nelore Mocho',                           False),
    ('NO', 'Normando',                               False),
    ('NR', 'Norwegian Red',                          False),
    ('NS', 'Bonsmara',                               False),
    ('PA', 'Pathenais',                              False),
    ('PI', 'Piemontês',                              False),
    ('PN', 'Pantaneiro',                             False),
    ('PR', 'Pirenaico',                              False),
    ('PT', 'Pitangueiras',                           False),
    ('PZ', 'Pinzgauer',                              False),
    ('RA', 'Ranger',                                 False),
    ('RB', 'Red Brangus',                            False),
    ('RD', 'Red Dane',                               False),
    ('RG', 'Rubia Galega',                           False),
    ('RN', 'Romagnola',                              False),
    ('RW', 'Dinamarquês Vermelho',                   False),
    ('SB', 'Pardo Suíço (Brown Swiss Beef)',          False),
    ('SD', 'Sindi',                                  False),
    ('SE', 'Senepol',                                False),
    ('SG', 'Santa Gertrudis',                        False),
    ('SI', 'Simbrasil',                              False),
    ('SL', 'Salers',                                 False),
    ('SM', 'Simental',                               False),
    ('SN', 'Senangus',                               False),
    ('SO', 'Siboney',                                False),
    ('SS', 'Shorton (Beef)',                         False),
    ('SW', 'Sahiwal',                                False),
    ('SX', 'Sussex',                                 False),
    ('TA', 'Tarentaise',                             False),
    ('TB', 'Tabapuã',                                False),
    ('TG', 'Tasmanian Grey',                         False),
    ('TI', 'Tuli',                                   False),
    ('TX', 'Texas Longhorn',                         False),
    ('UM', 'Murrah',                                 False),
    ('WB', 'Welsh Black',                            False),
    ('WF', 'West Flemish Rer',                       False),
    ('WW', 'Holandes Vermelho',                      False),
    ('XX', 'Composto',                               True),
]


# -------------------------------------------------------
# Funcao: cria a tabela (se nao existir) em 1 schema.
# Estrutura identica ao model backend/models/tb_4005_racas.py.
# -------------------------------------------------------
def criar_tabela(conexao, schema):
    conexao.execute(text(f'''
        CREATE TABLE IF NOT EXISTS "{schema}".tb_4005_racas (
            id             SERIAL PRIMARY KEY,
            codigo         VARCHAR(2) NOT NULL UNIQUE,
            nome           VARCHAR(60) NOT NULL,
            comum          BOOLEAN NOT NULL DEFAULT FALSE,
            ativo          BOOLEAN NOT NULL DEFAULT TRUE,
            criado_em      TIMESTAMP NOT NULL DEFAULT now(),
            atualizado_em  TIMESTAMP NOT NULL DEFAULT now()
        );
    '''))


# -------------------------------------------------------
# Funcao: insere a lista de Racas em 1 schema. Idempotente -
# ON CONFLICT (codigo) DO NOTHING permite reexecutar o script
# sem duplicar dados (ex: populando um Produtor novo).
# -------------------------------------------------------
def popular_tabela(conexao, schema):
    for codigo, nome, comum in RACAS:
        conexao.execute(
            text(f'''
                INSERT INTO "{schema}".tb_4005_racas (codigo, nome, comum)
                VALUES (:codigo, :nome, :comum)
                ON CONFLICT (codigo) DO NOTHING;
            '''),
            {'codigo': codigo, 'nome': nome, 'comum': comum}
        )


# -------------------------------------------------------
# Rotina principal: descobre todos os schemas 'produtor_%'
# existentes e aplica criar_tabela + popular_tabela em cada um.
# -------------------------------------------------------
def main():
    with engine.begin() as conexao:
        schemas = conexao.execute(text('''
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'produtor_%'
            ORDER BY schema_name;
        ''')).scalars().all()

        if not schemas:
            print('Nenhum schema "produtor_%" encontrado - nada a fazer.')
            return

        for schema in schemas:
            criar_tabela(conexao, schema)
            popular_tabela(conexao, schema)
            print(f'{schema}: tb_4005_racas OK ({len(RACAS)} raças verificadas).')

    print('Concluído.')


if __name__ == '__main__':
    main()

# =========================================================
# FIM DE ARQUIVO: backend\scripts\popular_racas.py
# =========================================================