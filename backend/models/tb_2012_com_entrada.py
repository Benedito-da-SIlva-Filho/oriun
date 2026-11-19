# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_2012_com_entrada.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-09-14 17:10 -03
# ATUALIZADO EM: 2026-11-17 18:32 -03
# VERSAO:       1.4.0
#
# DESCRICAO:
#     Model da tabela tb_2012_com_entrada - Comunicado de Entrada
#     (Anexo XIX, documento oficial que segue para a Certificadora
#     e o MAPA). Tabela POR-PRODUTOR (Schema-por-Produtor) - o
#     numero_comunicado e sequencial por Propriedade DENTRO do
#     proprio schema do Produtor.
#
#     1 LINHA POR GTA dentro de um Comunicado - um Comunicado pode
#     reunir ate 6 GTAs da MESMA procedencia para o MESMO destino
#     (Benedito, Sessao 052); quando ha mais de 6 GTAs elegiveis,
#     forma-se mais de um Comunicado (lotes de 6, respeitando
#     gta_data_emissao ASC). Todas as linhas de um mesmo Comunicado
#     compartilham o mesmo numero_comunicado.
#
#     Gatilho: GTA com tb_4001_gta.status_brincagem='BRINCADO' e
#     ainda sem numero_comunicado. Ao gerar, o MESMO numero_
#     comunicado e gravado tambem em tb_2001.numero_comunicado e
#     tb_7017_entrada_brincos_rfid.numero_comunicado (nivel do
#     animal/brinco individual) e em tb_4001_gta.numero_comunicado
#     (nivel da GTA) - alem de tb_7002_pia.numero_pia receber
#     UPDATE com este mesmo valor (o numero da PIA "vira" o numero
#     oficial do Comunicado, Benedito Sessao 052 - nao existe
#     numeracao PIA separada de verdade, era so um valor provisorio
#     de teste).
#
#     Campos de origem/destino sao DENORMALIZADOS por decisao do
#     legado (dicionario de dados real "2012 Com Entrada" mostrado
#     por Benedito, Sessao 052) - o Comunicado e um documento
#     oficial e nao deve mudar retroativamente se o cadastro do
#     Parceiro/Propriedade for corrigido depois.
#
#     id_gta (CAMPO NOVO, fora da lista original de 16 campos do
#     legado, sugerido pelo Claude e PENDENTE DE CONFIRMACAO por
#     Benedito): FK real para tb_4001_gta.id, MESMO SCHEMA - o
#     legado so guardava gta_numero em texto, sem link garantido.
#     Se Benedito preferir remover, e so tirar esta coluna e usar
#     gta_numero para localizar a GTA por busca de texto.
#
#     data_liberacao_abate: COPIADA de tb_2001.liberacao_abate
#     (data_brincagem + 90 dias, calculo que ja existe e ja roda em
#     producao desde a Brincagem Sequencial) - nunca recalculada
#     aqui, para nao duplicar regra de negocio em dois lugares.
#
#     data_envio: gravada com o MESMO valor da data de impressao
#     (Benedito, Sessao 052: "para nos a data de envio e a data de
#     impressao") - por isso so existe 1 coluna, nao duas.
#
#     status: nasce 'ABERTO'; passa a 'IMPRESSO' (+ data_envio
#     preenchida) no momento da Impressao. Reimpressao e livre, nao
#     muda o status nem a data_envio de novo.
#
#     SEM indice unico em (id_propriedade_destino, numero_comunicado)
#     (v1.1.0): como a tabela guarda 1 LINHA POR GTA e um Comunicado
#     tem de 1 ate 6 GTAs (MAXIMO_GTAS_POR_COMUNICADO em
#     comunicado_entrada.py), o MESMO numero se repete em ate 6 linhas
#     da mesma Propriedade - um indice unico nesse par recusaria a 2a
#     GTA de qualquer Comunicado. A numeracao continua protegida pelo
#     pg_advisory_xact_lock + MAX + 1 usados no momento da geracao
#     (mesmo mecanismo ja usado para tb_7002_pia.numero_pia, ver
#     brincagem_sequencial.py, _obter_proximo_numero_pia()). Quem
#     garante que a MESMA GTA nao entra duas vezes e a validacao na
#     entrada da GTA (tb_4001_gta), nao esta tabela.
#
#     v1.0.0: Criacao do modulo (Sessao 052), a partir do dicionario
#             de dados real do legado ("2012 Com Entrada") e do
#             alinhamento de campos fechado com Benedito.
#     v1.1.0: Sessao 085 (04/10/2026, 16:05 -03) - BUG REAL achado antes
#             de acontecer em producao: o banco tinha o indice unico
#             uq_tb_2012_propriedade_numero (Propriedade + numero do
#             Comunicado), criado na v1.0.0 como "segunda camada de
#             defesa", achando que 1 linha = 1 Comunicado. Contraria a
#             regra de 1 a 6 GTAs por Comunicado - o Gerar Comunicado
#             falharia na 2a GTA (exemplo real do legado: Comunicado
#             000008 com 4 GTAs). REMOVIDO o UniqueConstraint (e o
#             __table_args__ que so existia por ele) deste model; o
#             indice some do banco pelo script Tabelas\drop_uq_tb_2012_
#             propriedade_numero_s085.sql (todos os schemas produtor_
#             NNNNN). Nenhuma outra mudanca de coluna/tipo/FK.
#     v1.2.0: Sessao 091 (08/10/2026, 20:45 -03) - 2 colunas novas para provar QUEM e
#             QUANDO imprimiu: impresso_em (data E hora da 1a impressao) e
#             id_usuario_impressao. Ambas aceitam vazio (comunicados antigos).
#             SQL: Tabelas\alter_tb_2012_impressao_s091.sql (todos os schemas).
#     v1.3.0: Sessao 115 (2026-11-05 11:36 -03) - ALTERACAO DE POSSE: o ENUM tipo_entrada_enum ganha o valor POSSE (animal que chega ao destino por Alteracao de Posse).
#         O valor novo entra no banco por Tabelas\alterar_posse_s115_b.sql. Nenhuma coluna nova.  REVERSAO: .bak_antes_s115_posse_b.
#     v1.4.0: Sessao 130 (2026-11-17 18:32 -03) - CARGA (animais de Produtor novo, Extrato do MAPA): o ENUM tipo_entrada_enum ganha o valor CARGA.
#         O valor novo entra no banco por Tabelas\SQL_carga_passo1_enums_17-11-2026.sql. Nenhuma coluna nova.  REVERSAO: bak_antes_s130_carga.
# =========================================================

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# ENUM ja existente no banco (create_type=False) - MESMO
# reaproveitado de tb_2001_entradas.py. So os valores COMPRA e
# TRANSFERENCIA sao usados de fato neste Comunicado (Benedito,
# Sessao 052), mas nao ha necessidade de um ENUM novo so para
# restringir ainda mais.
# -------------------------------------------------------
tipo_entrada_enum = PgEnum(
    'COMPRA', 'NASCTO-DESMAME', 'REIDENTIFICACAO', 'TRANSFERENCIA', 'POSSE', 'CARGA',
    name='tipo_entrada_enum', schema='public', create_type=False
)


# -------------------------------------------------------
# Model ComunicadoEntrada
# Espelha a tabela tb_2012_com_entrada (schema do Produtor)
# -------------------------------------------------------
class ComunicadoEntrada(Base):
    __tablename__ = 'tb_2012_com_entrada'

    id                          = Column(Integer, primary_key=True)

    # Destino (Propriedade/Produtor do proprio schema)
    id_propriedade_destino      = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    propriedade_destino         = relationship('Propriedade', foreign_keys=[id_propriedade_destino])
    cpf_cnpj_produtor_destino   = Column(String(18))

    # Numeracao oficial (sequencial por Propriedade destino, com
    # pg_advisory_xact_lock no momento da geracao)
    numero_comunicado           = Column(Integer, nullable=False)

    # GTA incluida neste Comunicado (1 linha por GTA) - id_gta e
    # campo novo sugerido, ver DESCRICAO acima (PENDENTE DE
    # CONFIRMACAO).
    id_gta                       = Column(Integer, ForeignKey('tb_4001_gta.id'))
    gta                           = relationship('Gta', foreign_keys=[id_gta])
    gta_numero                    = Column(String(30), nullable=False)
    gta_data_emissao               = Column(Date)
    gta_data_validade               = Column(Date)
    data_brincagem                   = Column(Date)
    gta_data_entrega                  = Column(Date)
    qtd_animais                        = Column(Integer)

    # Liberacao para Abate - COPIADA de tb_2001.liberacao_abate,
    # nunca recalculada aqui.
    data_liberacao_abate                 = Column(Date)

    # Auditoria de geracao - protege a Plataforma (Benedito,
    # Sessao 052).
    data_inclusao                          = Column(Date, nullable=False, default=datetime.now)

    # Origem (Parceiro/Propriedade externa - mesmo schema do
    # Produtor, sem prefixo public., mesmo padrao de
    # tb_4001_gta.id_parceiro_propriedade)
    id_parceiro_propriedade                  = Column(Integer, ForeignKey('tb_parceiros_propriedades.id'))
    parceiro_propriedade                       = relationship('ParceiroPropriedades', foreign_keys=[id_parceiro_propriedade])
    cpf_cnpj_produtor_origem                     = Column(String(18))

    tipo_entrada                                   = Column(tipo_entrada_enum, nullable=False)

    # Status/Impressao - nasce ABERTO; IMPRESSO grava data_envio
    # (= data da impressao, Reimpressao nao muda mais nenhum dos
    # dois).
    status                                           = Column(String(20), nullable=False, default='ABERTO')
    data_envio                                         = Column(Date)
    impresso_em                                         = Column(DateTime)      # v1.2.0 - data E hora da 1a impressao
    id_usuario_impressao                                 = Column(Integer)       # v1.2.0 - quem imprimiu

    criado_em                                            = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em                                          = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<ComunicadoEntrada {self.numero_comunicado} - GTA {self.gta_numero}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_2012_com_entrada.py
# =========================================================