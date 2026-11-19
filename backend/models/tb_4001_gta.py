# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_4001_gta.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-15 11:40 -03
# ATUALIZADO EM: 2026-11-17 18:32 -03
# VERSAO: 1.11.0
#
# DESCRICAO:
#     Model da tabela tb_4001_gta.
#     Cabecalho da GTA (Guia de Transito Animal), cobre tanto
#     Entrada quanto Saida via campo sentido (ENUM
#     sentido_gta_enum: ENTRADA/SAIDA).
#
#     Numero da GTA guardado em tres campos separados
#     (uf_gta, serie_gta, numero_gta_sequencial) mais um
#     campo calculado (numero_gta_completo) para busca/
#     exibicao.
#
#     Lado externo aponta para tb_parceiros_propriedades OU
#     tb_frigorificos, nunca os dois ao mesmo tempo - garantido
#     por CHECK constraint no banco
#     (chk_tb_4001_gta_lado_externo).
#
#     tipo_movimento (ENUM tipo_movimento_gta_enum, fechado na
#     Sessao 17): COMPRA, NASCTO-DESMAME, VENDA, ABATE, MORTE,
#     TRANSFERENCIA.
#
#     numero_comunicado (RENOMEADA v1.6.0, Sessao 052, 14/09/2026,
#     17:10 -03) - ver DESCRICAO completa no changelog v1.6.0 mais
#     abaixo. Ate a v1.5.0 este campo se chamava id_comunicado e
#     nunca tinha sido usado por nenhum codigo (a tabela tb_2012_
#     com_entrada nao existia ainda). Renomeado para bater com o
#     MESMO NOME usado em tb_2001 e tb_7017_entrada_brincos_rfid.
#
#     id_propriedade (obrigatorio) e quem diferencia, dentro do
#     mesmo schema de Produtor, para qual Propriedade dele cada
#     GTA esta indo/saindo.
#
#     meio_transporte (Sessao 027): transcricao livre e fiel do
#     campo "MEIO DE TRANSPORTE" impresso na GTA fisica.
#
#     arquivo_pdf_caminho / arquivo_pdf_hash (Sessao 029):
#     resguardo documental do PDF lido automaticamente.
#
#     status_brincagem (Sessao 048): identifica se uma GTA de
#     COMPRA ja foi brincada ou nao.
#
#     v1.0.0: Criacao do modulo (Sessao 17).
#     v1.1.0: Sessao 018 - Decisao arquitetural revertida: RLS
#             descartado, Schema-por-Produtor confirmado.
#     v1.2.0: Sessao 019 - Tres correcoes de schema/PgEnum.
#     v1.3.0: Sessao 027 - Adicionada coluna meio_transporte.
#     v1.4.0: Sessao 029 - Adicionadas arquivo_pdf_caminho e
#             arquivo_pdf_hash.
#     v1.5.0: Sessao 048 (09/09/2026, 11:45 -03) - Adicionada
#             coluna status_brincagem.
#     v1.6.0: Sessao 052 (14/09/2026, 17:10 -03) - Coluna
#             id_comunicado RENOMEADA para numero_comunicado (SQL:
#             Tabelas\1_rename_tb_4001_gta_numero_comunicado.sql,
#             aplicado em todos os schemas produtor_NNNNN). Motivo:
#             padronizar o MESMO nome de campo nas 3 tabelas que
#             participam do modulo Gerar Comunicado de Entrada
#             (tb_2001, tb_4001_gta, tb_7017_entrada_brincos_rfid) -
#             decisao explicita de Benedito, Sessao 052. Nenhuma
#             outra mudanca de coluna/tipo/FK nesta versao. Antes de
#             aplicar o SQL, confirmado que nenhum outro arquivo do
#             projeto referenciava "id_comunicado" (a coluna nunca
#             tinha sido usada em codigo ate esta sessao).
#     v1.7.0: Sessao 085 (04/10/2026, 17:50 -03) - TRAVA DE GTA UNICA no
#             model: UniqueConstraint (uf_gta, serie_gta,
#             numero_gta_sequencial, sentido) com o nome uq_tb_4001_gta_
#             uf_serie_numero_sentido (regra de Benedito: jamais duas GTAs
#             iguais - UF + Serie + Numero + sentido; o sentido entra
#             porque a mesma GTA pode existir 1x como ENTRADA e 1x como
#             SAIDA numa Transferencia entre Propriedades do mesmo
#             Produtor). A tb_4001_gta e criada pelo onboarding a partir
#             deste model (nao ha script CREATE em Tabelas), entao todo
#             Produtor NOVO ja nasce com a trava. Os schemas JA existentes
#             recebem a mesma constraint pelo script Tabelas\alter_tb_4001_
#             gta_unica_uf_serie_numero_sentido_s085.sql. A checagem com
#             mensagem clara (antes de gravar) fica em backend/utils/
#             gta_duplicada.py. Nenhuma outra mudanca de coluna/tipo/FK.
#     v1.8.0: Sessao 094 (12/10/2026, 19:30 -03) - NAS POR PROPRIEDADE (decisao de Benedito):
#         a numeracao da Notificacao de Nascimento (NAS) passa a ser da PROPRIEDADE (dentro do
#         schema do Produtor), nao mais do Produtor inteiro: a primeira NAS de cada fazenda e a
#         NAS0000001. UniqueConstraint trocada por 2 indices unicos parciais (GTA: serie<>NAS; NAS: propriedade+numero).
#         REVERSAO: devolver .bak_antes_nas_propriedade.
#         Script: Tabelas\alter_tb_4001_gta_nas_por_propriedade_s094.sql
#     v1.9.0: Sessao 100 (19/10/2026, 17:05 -03) - NOVA COLUNA data_saida (Date, opcional): Data de Saida da GTA de
#         Saida, digitada na tela Vincular GTA / Embarque (decisao de Benedito: a GTA e um caminhao, sai numa data so).
#         Antes ficava em data_entrega; agora tem coluna propria. Novos Produtores recebem a coluna pelo Onboarding
#         (create_all); Produtores existentes pelo script SQL.
#         REVERSAO: devolver .bak_antes_data_saida_s100.
#         Script: Tabelas\alter_tb_4001_gta_data_saida_s100.sql
#     v1.10.0: Sessao 115 (2026-11-05 11:13 -03) - ALTERACAO DE POSSE (pacote 1): o ENUM tipo_movimento_gta_enum ganha o valor POSSE
#         (DTA - Documento de Transferencia Animal da Alteracao de Posse: mesmo Estabelecimento, Produtor diferente).
#         O valor novo entra no banco pelo script Tabelas\alterar_posse_s115.sql (ALTER TYPE ... ADD VALUE).
#         Nenhuma coluna nova. REVERSAO: .bak_antes_s115_posse (o valor do ENUM, uma vez criado, fica no banco sem uso).
#     v1.11.0: Sessao 130 (2026-11-17 18:32 -03) - CARGA (animais de Produtor novo, Extrato do MAPA): (1) o ENUM tipo_movimento_gta_enum ganha o valor CARGA;
#         (2) a GTA da Carga usa a serie propria 'CAR' (numero_gta_completo = 'CARGA'), no molde da 'NAS': o indice geral uq_tb_4001_gta_uf_serie_numero_sentido
#         passa a valer so para serie diferente de NAS e CAR; (3) NOVO indice unico parcial uq_tb_4001_gta_carga_propriedade (id_propriedade) onde serie = 'CAR':
#         UMA Carga por Propriedade (o Desfazer apaga a GTA CAR e libera outra). Nenhuma coluna nova.
#         Scripts: Tabelas\SQL_carga_passo1_enums_17-11-2026.sql e SQL_carga_passo2_indices_17-11-2026.sql (reverter: SQL_carga_reverter_17-11-2026.sql). REVERSAO: bak_antes_s130_carga.
# =========================================================

from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# ENUMs ja existentes no banco (create_type=False - o
# SQLAlchemy nao tenta recriar o tipo, so referencia o que
# ja foi criado via CREATE TYPE no pgAdmin).
# -------------------------------------------------------
sentido_gta_enum = PgEnum(
    'ENTRADA', 'SAIDA',
    name='sentido_gta_enum',
    schema='public',
    create_type=False
)

tipo_movimento_gta_enum = PgEnum(
    'COMPRA', 'NASCTO-DESMAME', 'VENDA', 'ABATE', 'MORTE', 'TRANSFERENCIA', 'POSSE', 'CARGA',
    name='tipo_movimento_gta_enum',
    schema='public',
    create_type=False
)


# -------------------------------------------------------
# Model Gta
# Espelha a tabela tb_4001_gta no PostgreSQL
# -------------------------------------------------------
class Gta(Base):
    __tablename__ = 'tb_4001_gta'
    # v1.7.0 - mesma GTA (UF + Serie + Numero + sentido) nunca 2x no Produtor.
    # v1.8.0 - a trava vale para GTA de verdade (serie diferente de NAS); a NAS (Notificacao de
    # Nascimento, numeracao interna) tem fila por PROPRIEDADE: trava propria (propriedade + numero).
    __table_args__ = (
        Index(
            'uq_tb_4001_gta_uf_serie_numero_sentido',
            'uf_gta', 'serie_gta', 'numero_gta_sequencial', 'sentido',
            unique=True, postgresql_where=text("serie_gta NOT IN ('NAS', 'CAR')"),
        ),
        Index(
            'uq_tb_4001_gta_nas_propriedade_numero',
            'id_propriedade', 'numero_gta_sequencial',
            unique=True, postgresql_where=text("serie_gta = 'NAS'"),
        ),
        Index(
            'uq_tb_4001_gta_carga_propriedade',
            'id_propriedade',
            unique=True, postgresql_where=text("serie_gta = 'CAR'"),
        ),
    )

    # Identificacao
    id                          = Column(Integer, primary_key=True)

    # Lado interno (dono da GTA - sempre uma Propriedade do Orion).
    id_propriedade              = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    propriedade                 = relationship('Propriedade', foreign_keys=[id_propriedade])

    # Numero da GTA (UF + Serie + Numero separados, mais o calculado)
    uf_gta                      = Column(String(2), nullable=False)
    serie_gta                   = Column(String(5), nullable=False)
    numero_gta_sequencial       = Column(String(15), nullable=False)
    numero_gta_completo         = Column(String(30), nullable=False)

    # Dados do movimento
    qtde_animais                = Column(Integer, nullable=False)
    tipo_movimento               = Column(tipo_movimento_gta_enum, nullable=False)
    sentido                      = Column(sentido_gta_enum, nullable=False)

    # Datas do documento
    data_emissao                = Column(Date, nullable=False)
    data_validade                = Column(Date, nullable=False)
    data_entrega                 = Column(Date)
    data_saida                   = Column(Date)  # Data de Saida (GTA de Saida) - Sessao 100

    # Meio de Transporte (Sessao 027)
    meio_transporte              = Column(String(30), nullable=False)

    # Lado externo - mutuamente exclusivo (Parceiro OU Frigorifico)
    id_parceiro_propriedade     = Column(Integer, ForeignKey('tb_parceiros_propriedades.id'))
    parceiro_propriedade        = relationship('ParceiroPropriedades', foreign_keys=[id_parceiro_propriedade])

    id_frigorifico               = Column(Integer, ForeignKey('public.tb_frigorificos.id'))
    frigorifico                  = relationship('Frigorifico', foreign_keys=[id_frigorifico])

    # Numero oficial do Comunicado de Entrada (RENOMEADO v1.6.0 -
    # ver DESCRICAO/changelog acima). Preenchido ao Gerar Comunicado.
    # SEM ForeignKey de proposito - mesmo padrao das outras 2 tabelas.
    numero_comunicado             = Column(Integer)

    # Dados internos do processo administrativo
    nf_numero                    = Column(Integer)
    pesagem_balancao             = Column(Numeric)
    pesagem_data                  = Column(Date)
    peso_medio_entrada           = Column(Numeric)

    # Campos de auditoria
    codigo_autenticidade         = Column(String(100))
    emitente_nome                = Column(String(150))
    emitente_cargo                = Column(String(80))
    observacoes                   = Column(Text)

    # Arquivo fisico do documento (Sessao 029)
    arquivo_pdf_caminho          = Column(String(255))
    arquivo_pdf_hash             = Column(String(64))

    # Status da Brincagem (Sessao 048)
    status_brincagem             = Column(String(20), default='NAO_APLICA')

    # Controle de datas
    criado_em                    = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em                = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Gta {self.numero_gta_completo} ({self.sentido}/{self.tipo_movimento})>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_4001_gta.py
# =========================================================