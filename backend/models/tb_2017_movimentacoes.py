# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_2017_movimentacoes.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-09-07 19:05 -03
# ATUALIZADO EM: 2026-11-17 18:32 -03
# VERSAO:       1.4.0
#
# DESCRICAO:
#     Model da tabela tb_2017_movimentacoes - "copia"/kardex do
#     animal, ja salvou o Produtor inumeras vezes no GERAS.
#     Tabela POR-PRODUTOR (Schema-por-Produtor), SEM
#     __table_args__ de schema.
#
#     1 LINHA NOVA POR EVENTO (Entrada, e futuramente Saida/Venda/
#     Abate/Morte/Transferencia geram OUTRA linha separada - nunca
#     atualiza uma linha existente). Cada linha e um "retrato"
#     completo do animal naquele momento - campos do lado oposto ao
#     evento (ex.: campos de Saida numa linha de Entrada) ficam em
#     branco.
#
#     cota_hilton (NOVA v1.1.0, Sessao 049, 10/09/2026, 18:45 -03):
#     espelha tb_2001.cota_hilton (mesmo tipo/default - Boolean,
#     NOT NULL, default False) - decisao de Benedito: o
#     espelhamento de tb_2001 que esta tabela ja documentava desde
#     a v1.0.0 deve incluir tambem esta informacao, calculada pelo
#     Bloco C da Brincagem Sequencial (elegivel se tipo_entrada =
#     NASCTO-DESMAME OU entrou com idade < 10 meses - mesma regra
#     de tb_2001, ver brincagem_sequencial.py v1.10.0). Script:
#     Tabelas\alter_tb_2017_cota_hilton.sql, ja executado por
#     Benedito em todos os schemas produtor_NNNNN.
#
#     id_animal NAO e uma ForeignKey de banco de verdade (decisao
#     de Benedito, Sessao 047): tb_2001 faz DELETE FISICO no evento
#     de saida do animal (ver tb_2001_entradas.py) - se id_animal
#     fosse FK real, o banco IMPEDIRIA esse DELETE enquanto existir
#     uma linha aqui referenciando o animal, quebrando o
#     comportamento que tb_2001 precisa ter. Aqui fica so um
#     Integer solto (referencia historica, sem constraint).
#
#     Reaproveita os MESMOS enums que tb_2001 ja usa (sexo_enum,
#     tipo_entrada_enum, interno_externo_enum), sem criar nada
#     paralelo - decisao de Benedito, Sessao 047. Campo
#     `negociacao` (COMPRA/VENDA/TRANSFERENCIA, igual ao tipo de
#     movimento da GTA) e `tipo_saida` (reservado para o futuro
#     modulo de Saidas) ainda NAO tem enum equivalente conhecido -
#     ficam VARCHAR por ora; podem virar enum de verdade quando o
#     modulo de Saidas for desenhado.
#
#     v1.0.0: Criacao do modulo (Sessao 047), a partir do
#             alinhamento de campos do GERAS (tela "2017-...") e do
#             model real de tb_2001_entradas.py (Regra de Ouro).
#     v1.1.0: Sessao 049 (10/09/2026, 18:45 -03) - Adicionada
#             coluna cota_hilton (Boolean, NOT NULL, default
#             False), ja aplicada via ALTER TABLE (bloco DO $$ em
#             loop) em todos os schemas produtor_NNNNN. Ver
#             DESCRICAO acima.
#     v1.2.0: Sessao 101 (20/10/2026, 10:10 -03) - Copia fiel da tb_2001: novas colunas lote, data_brincagem, conferido_brete, conferido_em, id_origem e id_gta_entrada (SQL Tabelas\alter_tb_2017_copia_fiel_s101.sql). Decisao do Benedito: a tb_2017 e a copia exata da tb_2001, para devolver o animal na substituicao depois do Comunicado.
#     v1.3.0: Sessao 115 (2026-11-05 11:36 -03) - ALTERACAO DE POSSE: o ENUM tipo_entrada_enum ganha o valor POSSE (animal que chega ao destino por Alteracao de Posse).
#         O valor novo entra no banco por Tabelas\alterar_posse_s115_b.sql. Nenhuma coluna nova.  REVERSAO: .bak_antes_s115_posse_b.
#     v1.4.0: Sessao 130 (2026-11-17 18:32 -03) - CARGA (animais de Produtor novo, Extrato do MAPA): o ENUM tipo_entrada_enum ganha o valor CARGA.
#         O valor novo entra no banco por Tabelas\SQL_carga_passo1_enums_17-11-2026.sql. Nenhuma coluna nova.  REVERSAO: bak_antes_s130_carga.
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Numeric
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# ENUMs ja existentes no banco (create_type=False: apenas
# referencia, nunca tenta recriar) - MESMOS de tb_2001_entradas.py,
# reaproveitados aqui sem duplicar/criar nada paralelo.
# -------------------------------------------------------
sexo_enum = PgEnum('MACHO', 'FEMEA', name='sexo_enum', schema='public', create_type=False)
tipo_entrada_enum = PgEnum(
    'COMPRA', 'NASCTO-DESMAME', 'REIDENTIFICACAO', 'TRANSFERENCIA', 'POSSE', 'CARGA',
    name='tipo_entrada_enum', schema='public', create_type=False
)
interno_externo_enum = PgEnum(
    'INTERNO', 'EXTERNO', name='interno_externo_enum', schema='public', create_type=False
)


# -------------------------------------------------------
# Model Movimentacao
# Espelha a tabela tb_2017_movimentacoes (schema do Produtor)
# -------------------------------------------------------
class Movimentacao(Base):
    __tablename__ = 'tb_2017_movimentacoes'

    # Identificacao / vinculo historico
    id                   = Column(Integer, primary_key=True)
    id_animal            = Column(Integer)  # SEM ForeignKey - ver DESCRICAO
    id_propriedade       = Column(Integer, nullable=False)
    sisbov               = Column(String(15), nullable=False)  # copia
    manejo               = Column(String(6))
    rfid                 = Column(String(15))

    # Bloco Classificacao (copia de tb_2001, no momento do evento)
    negociacao           = Column(String(20))  # COMPRA/VENDA/TRANSFERENCIA - sem enum proprio ainda
    brincos              = Column(interno_externo_enum)
    id_especie           = Column(Integer)
    sexo                 = Column(sexo_enum)
    nascimento           = Column(Date)
    dias                 = Column(Integer)  # eras_dias, travado no momento do evento
    cota_hilton          = Column(Boolean, nullable=False, default=False)
    id_aptidao           = Column(Integer)
    id_raca              = Column(Integer)
    liberacao_abate      = Column(Date)

    # Bloco Entrada
    tipo_entrada         = Column(tipo_entrada_enum)
    gta_entrada          = Column(String(10))
    gta_entrada_emissao  = Column(Date)
    gta_entrada_validade = Column(Date)
    gta_entrada_animais  = Column(Integer)
    data_inclusao        = Column(Date)   # quando foi lancado no sistema
    entrada              = Column(Date)   # Data de Entrega da GTA (fisica)
    origem_propriedade   = Column(String(150))
    origem_cpf_cnpj      = Column(String(18))

    # Copia fiel de tb_2001 (v1.2.0, Sessao 101): o que a Entrada tem e nao existia aqui.
    # Servem para DEVOLVER o animal identico a tb_2001 (substituicao depois do Comunicado de Saida).
    # Sem ForeignKey de proposito (mesmo motivo de id_animal).
    lote                 = Column(String(30))
    data_brincagem       = Column(Date)
    conferido_brete      = Column(Boolean)
    conferido_em         = Column(DateTime)
    id_origem            = Column(Integer)   # tb_parceiros.id, sem ForeignKey
    id_gta_entrada       = Column(Integer)   # tb_4001_gta.id, sem ForeignKey

    # Bloco Saida - ficam em branco numa linha de Entrada; usados
    # pelo futuro modulo de Saidas (Venda/Abate/Morte/Transferencia)
    tipo_saida           = Column(String(20))  # sem enum proprio ainda (ver DESCRICAO)
    gta_saida            = Column(String(10))
    gta_saida_emissao    = Column(Date)
    gta_saida_validade   = Column(Date)
    gta_saida_animais    = Column(Integer)
    destino_propriedade  = Column(String(150))
    destino_cpf_cnpj     = Column(String(18))

    # Bloco Movimentacao / Documentos
    data_movimentacao    = Column(Date, nullable=False)  # data do evento (= Entrada, nesse caso)
    numero_comunicado    = Column(String(6))   # nro sequencial de 6 digitos do Comunicado gerado
    peso_medio           = Column(Numeric(6, 2))  # Balancao / qtde de animais da GTA

    # Controle de datas
    criado_em            = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em        = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Movimentacao {self.sisbov} - {self.data_movimentacao}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_2017_movimentacoes.py
# =========================================================