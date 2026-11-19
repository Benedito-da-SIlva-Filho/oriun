# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_3008_brincos_saida.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-17 10:10 -03
# ATUALIZADO EM: 2026-11-17 18:32 -03
# VERSAO: 1.4.0
#
# DESCRICAO:
#     Model da tabela tb_3008_brincos_saida.
#     Registra a saida individual de cada brinco do estoque de
#     um lote (tb_3007_brincos_entrada) para aplicacao em um
#     animal - identificado pelo SISBOV/RFID - OU para registrar
#     o cancelamento de um brinco (ver v1.1.0 abaixo).
#
#     Vive dentro do schema do Produtor (Schema-per-Produtor,
#     conforme classificacao fechada na Sessao 018).
#
#     id_lote_entrada: FK para tb_3007_brincos_entrada - o lote
#     de origem deste brinco especifico, mantendo a cadeia de
#     rastreabilidade (1021 -> 3007 -> 3008/7017).
#
#     origem (ENUM tipo_entrada_enum, reaproveitado - mesmo tipo
#     compartilhado usado em outros pontos do sistema): COMPRA,
#     NASCTO-DESMAME, REIDENTIFICACAO, TRANSFERENCIA (motivos de
#     saida por aplicacao em animal) + DANIFICADO, EXTRAVIADO,
#     INATIVADO, VENDIDO (motivos de CANCELAMENTO, NOVO v1.1.0).
#     ATENCAO: TRANSFERENCIA e tecnicamente aceito pelo tipo do
#     Postgres, mas NAO deve ocorrer na pratica nesta tabela -
#     pela regra ja fechada ENTRADA vs BRINCAGEM (Transferencia
#     mantem os brincos de origem do animal, nao consome brinco
#     do estoque local; so consumiria brinco se o destino optasse
#     por SUBSTITUIR, e nesse caso deixa de ser Transferencia e
#     passa a ser Brincagem). Mantido no tipo por ser ENUM
#     compartilhado - nao pode ser removido sem afetar outros
#     usos. Comportamento real a confirmar em uso (Benedito,
#     Sessao 019: "vamos ver como funciona na pratica").
#
#     Nao possui coluna id_produtor - isolamento garantido pelo
#     proprio schema do Produtor (Schema-per-Produtor, Sessao 018).
#
#     v1.0.0: Criacao do modulo (Sessao 019), a partir da
#             estrutura real de tb_3008_brincos_saida conferida
#             no pgAdmin (9 colunas), ja sem coluna id_produtor
#             (removida na Sessao 018).
#     v1.1.0: Sessao 045 (03/09/2026, 09:40 -03) - Modulo
#             Cancelamento de Brincos (alinhamento fechado nas
#             Sessoes 044/045). Adicionados ao ENUM Python os 4
#             motivos de cancelamento do dropdown "Motivo" da tela
#             de Cancelamento: DANIFICADO, EXTRAVIADO, INATIVADO,
#             VENDIDO - espelhando o ALTER TYPE ja aplicado no
#             banco (script alter_tipo_entrada_enum_motivos_
#             cancelamento.sql, rodado por Benedito em 03/09/2026).
#             SEM esta atualizacao, o SQLAlchemy recusaria a
#             gravacao no lado Python (valida a lista de valores
#             aceitos ANTES de mandar pro banco), mesmo o banco ja
#             aceitando os 4 valores novos - encontrado durante o
#             levantamento de arquivos reais desta sessao (Regra
#             de Ouro), antes de qualquer codigo do router novo
#             ser escrito.
#     v1.2.0: Sessao 115 (2026-11-05 11:36 -03) - ALTERACAO DE POSSE: o ENUM tipo_entrada_enum ganha o valor POSSE (animal que chega ao destino por Alteracao de Posse).
#         O valor novo entra no banco por Tabelas\alterar_posse_s115_b.sql. Nenhuma coluna nova.  REVERSAO: .bak_antes_s115_posse_b.
#     v1.3.0: Sessao 123 (2026-11-13 17:55 -03) - AUDITORIA ETAPA 5: model declara o indice unico uq_tb_3008_sisbov (brinco baixado uma vez), que ja existe no banco. So documenta. REVERSAO: .bak_antes_etapa5.
#     v1.4.0: Sessao 130 (2026-11-17 18:32 -03) - CARGA (animais de Produtor novo, Extrato do MAPA): o ENUM tipo_entrada_enum ganha o valor CARGA.
#         O valor novo entra no banco por Tabelas\SQL_carga_passo1_enums_17-11-2026.sql. Nenhuma coluna nova.  REVERSAO: bak_antes_s130_carga.
# =========================================================

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# ENUM ja existente no banco (create_type=False - so
# referencia o tipo, nao tenta recriar). Lista de valores
# espelha exatamente o que existe hoje no Postgres apos o
# ALTER TYPE de 03/09/2026 (motivos de entrada + motivos de
# cancelamento, ver DESCRICAO v1.1.0 acima).
# -------------------------------------------------------
tipo_entrada_enum = PgEnum(
    'COMPRA', 'NASCTO-DESMAME', 'REIDENTIFICACAO', 'TRANSFERENCIA', 'POSSE', 'CARGA',
    'DANIFICADO', 'EXTRAVIADO', 'INATIVADO', 'VENDIDO',
    name='tipo_entrada_enum',
    schema='public',
    create_type=False
)


# -------------------------------------------------------
# Model BrincoSaida
# Espelha a tabela tb_3008_brincos_saida no PostgreSQL
# -------------------------------------------------------
class BrincoSaida(Base):
    __tablename__ = 'tb_3008_brincos_saida'
    __table_args__ = (Index('uq_tb_3008_sisbov', 'sisbov', unique=True),)   # v1.3.0 - brinco baixado uma vez

    # Identificacao
    id                = Column(Integer, primary_key=True)

    # Propriedade do Produtor (dentro do schema) a que este
    # brinco pertence - mesma logica de Gta.id_propriedade
    id_propriedade    = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    propriedade       = relationship('Propriedade', foreign_keys=[id_propriedade])

    # Lote de origem deste brinco (cadeia de rastreabilidade)
    id_lote_entrada   = Column(Integer, ForeignKey('tb_3007_brincos_entrada.id'), nullable=False)
    lote_entrada      = relationship('BrincoEntrada', foreign_keys=[id_lote_entrada])

    # Identificacao do animal que recebeu o brinco (ou do brinco
    # cancelado, quando origem for um dos 4 motivos de cancelamento)
    sisbov             = Column(String(15), nullable=False)
    rfid                = Column(String(15))

    # Dados da saida
    data_saida           = Column(Date)
    gta                   = Column(String(10))
    # Ver nota de ATENCAO no cabecalho sobre TRANSFERENCIA
    origem                = Column(tipo_entrada_enum)

    # Controle de datas
    criado_em              = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em            = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<BrincoSaida {self.sisbov} ({self.origem})>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_3008_brincos_saida.py
# =========================================================