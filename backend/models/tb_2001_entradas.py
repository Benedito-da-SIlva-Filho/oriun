# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_2001_entradas.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-07-27 12:27 -03
# ATUALIZADO EM: 2026-11-17 18:32 -03
# VERSAO:       1.9.0
#
# DESCRICAO:
#     Model da tabela tb_2001 (Entradas - rebanho vivo por
#     evento de Entrada). Tabela POR-PRODUTOR (Schema-por-
#     Produtor) - guarda somente o rebanho vivo. DELETE fisico
#     no evento de saida (Venda/Abate/Morte/Transferencia/
#     Reidentificacao) - por isso NAO tem coluna ativo.
#
#     SEM __table_args__ com schema fixo - o schema real e
#     resolvido em tempo de execucao pelo schema_translate_map de
#     get_db_produtor() (backend/utils/multitenant.py).
#
#     id_propriedade (Sessao 049, 10/09/2026, 16:00 -03): identifica
#     a QUAL Propriedade do Produtor pertence este animal - ver
#     changelog v1.2.0 abaixo.
#
#     numero_comunicado (v1.3.0, Sessao 052, 14/09/2026, 17:10
#     -03): gravado quando o Comunicado de Entrada (tb_2012_com_
#     entrada) e gerado para a GTA deste animal.
#
#     data_brincagem (NOVA v1.4.0, Sessao 052, 14/09/2026, 17:10
#     -03) - BUG REAL corrigido: esta tabela nunca teve essa data
#     propria (so tb_7017.data_brincagem existia) e liberacao_abate
#     vinha sendo calculada ERRADA, a partir de gta.data_entrega em
#     vez de data_brincagem + 90 dias (regra real confirmada por
#     Benedito, Sessao 052). Ver brincagem_sequencial.py v1.12.0
#     (correcao do Bloco C para toda gravacao NOVA) e
#     Tabelas\6_backfill_tb_2001_data_brincagem_liberacao_abate.sql
#     (correcao de todo animal ja gravado desde a Sessao 049).
#
#     FKs para catalogos do schema public levam o prefixo
#     'public.' explicito na string (id_especie, id_raca,
#     id_aptidao, e id_propriedade) - mesma correcao da
#     Sessao 019. FKs para tabelas do MESMO schema do Produtor
#     (id_gta_entrada -> tb_4001_gta, id_origem -> tb_parceiros)
#     ficam sem prefixo.
#
#     ENUMs referenciados com create_type=False (ja criados
#     via script SQL, este Model nao tenta recria-los):
#     sexo_enum, tipo_entrada_enum, interno_externo_enum.
#
#     v1.0.0: Criacao (Sessao 024).
#     v1.1.0: Sessao 034 - RENOMEACAO de Animal/tb_2001_animal.py
#             para Entrada/tb_2001_entradas.py, sem mudanca de
#             coluna/tipo/FK/ENUM.
#     v1.2.0: Sessao 049 (10/09/2026, 16:00 -03) - Adicionada
#             coluna id_propriedade (Integer, FK para
#             public.propriedades.id, NULLABLE), ja aplicada via
#             ALTER TABLE (bloco DO $$ em loop) em todos os
#             schemas produtor_NNNNN.
#     v1.3.0: Sessao 052 (14/09/2026, 17:10 -03) - Adicionada
#             coluna numero_comunicado (Integer, NULLABLE, SEM
#             ForeignKey), ja aplicada via ALTER TABLE (bloco DO $$
#             em loop) em todos os schemas produtor_NNNNN. Parte do
#             modulo Gerar Comunicado de Entrada (tb_2012_com_
#             entrada, nova nesta sessao).
#     v1.4.0: Sessao 052 (14/09/2026, 17:10 -03) - Adicionada
#             coluna data_brincagem (Date, NULLABLE) - ver
#             DESCRICAO/BUG REAL acima. Script:
#             Tabelas\5_alter_tb_2001_data_brincagem.sql.
#     v1.5.0: Sessao 084 (01/10/2026, 18:30 -03) - Adicionadas as
#             colunas conferido_brete (Boolean, NOT NULL, padrao
#             TRUE) e conferido_em (DateTime, NULLABLE). O Nascimento
#             lancado pelo escritorio grava conferido_brete=False e o
#             Brincagem com Leitor marca TRUE quando o peao le o
#             brinco no brete. Todo o resto (Compra, Vincular GTA,
#             etc.) continua nascendo TRUE. Script:
#             Tabelas\7_alter_tb_2001_conferido_brete.sql.
#     v1.6.0: Sessao 114 (2026-11-04 11:20 -03) - Coluna elemento_perdido (BOTTON/BRINCO), marcada no Leitor de Peso (Pesos pacote 1). SQL: Tabelas\criar_pesos_s114.sql.  REVERSAO: .bak_antes_s114_pesos.
#     v1.7.0: Sessao 115 (2026-11-05 11:36 -03) - ALTERACAO DE POSSE: o ENUM tipo_entrada_enum ganha o valor POSSE (animal que chega ao destino por Alteracao de Posse).
#         O valor novo entra no banco por Tabelas\alterar_posse_s115_b.sql. Nenhuma coluna nova.  REVERSAO: .bak_antes_s115_posse_b.
#     v1.8.0: Sessao 128 (2026-11-16 11:10 -03) - AUDITORIA ETAPA 7d: model declara o indice unico parcial uq_tb_2001_rfid (RFID nao repete no Produtor; vazio/nulo nao conta), mesmo nome e regra do script Tabelas\SQL_criar_indice_rfid_16-11-2026.sql. REVERSAO: .bak_antes_etapa7d.
#     v1.9.0: Sessao 130 (2026-11-17 18:32 -03) - CARGA (animais de Produtor novo, Extrato do MAPA): o ENUM tipo_entrada_enum ganha o valor CARGA.
#         O valor novo entra no banco por Tabelas\SQL_carga_passo1_enums_17-11-2026.sql. Nenhuma coluna nova.  REVERSAO: bak_antes_s130_carga.
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# ENUMs ja existentes no banco (create_type=False: apenas
# referencia, nunca tenta recriar)
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
# Model Entrada
# Espelha a tabela tb_2001 (schema do Produtor)
# -------------------------------------------------------
class Entrada(Base):
    __tablename__ = 'tb_2001'
    # v1.8.0 - o mesmo RFID so em UM animal do Produtor (RFID vazio/nulo nao conta). Sem schema fixo.
    __table_args__ = (Index('uq_tb_2001_rfid', 'rfid', unique=True, postgresql_where=text("rfid IS NOT NULL AND rfid <> ''")),)

    # Bloco Identificacao
    id                  = Column(Integer, primary_key=True)
    sisbov              = Column(String(15), nullable=False, unique=True)
    manejo              = Column(String(6))
    rfid                = Column(String(15))
    id_especie          = Column(Integer, ForeignKey('public.tb_4002_especie.id'))
    sexo                = Column(sexo_enum)
    nascimento          = Column(Date)
    eras_dias           = Column(Integer)
    id_raca             = Column(Integer, ForeignKey('tb_4005_racas.id'))

    # Bloco Elegibilidade
    id_aptidao          = Column(Integer, ForeignKey('public.tb_4004_aptidao.id'))
    cota_hilton         = Column(Boolean, nullable=False, default=False)
    liberacao_abate     = Column(Date)

    # Bloco Entrada
    tipo_entrada        = Column(tipo_entrada_enum, nullable=False)
    brincos             = Column(interno_externo_enum)
    id_gta_entrada       = Column(Integer, ForeignKey('tb_4001_gta.id'))
    data_inclusao       = Column(Date, nullable=False)
    lote                = Column(String(30))
    id_origem           = Column(Integer, ForeignKey('tb_parceiros.id'))

    # Propriedade (v1.2.0)
    id_propriedade      = Column(Integer, ForeignKey('public.propriedades.id'))
    propriedade         = relationship('Propriedade', foreign_keys=[id_propriedade])

    # Comunicado de Entrada (v1.3.0) - ver DESCRICAO acima.
    # SEM ForeignKey de proposito.
    numero_comunicado   = Column(Integer)

    # Data da Brincagem (NOVO v1.4.0) - ver DESCRICAO/BUG REAL
    # acima. Fonte de verdade para liberacao_abate.
    data_brincagem      = Column(Date)

    # Conferencia no brete (NOVO v1.5.0) - ver changelog.
    conferido_brete     = Column(Boolean, nullable=False, default=True)
    conferido_em        = Column(DateTime)

    # Elemento perdido (NOVO v1.6.0, Sessao 114): BOTTON / BRINCO / vazio. Marcado no Leitor de Peso; o Abate confere de novo.
    elemento_perdido    = Column(String(10))

    # Controle de datas
    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em       = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Entrada {self.sisbov}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_2001_entradas.py
# =========================================================