# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_6006_reidentificacao_com_baixa_itens.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-25 12:45 -03
# ATUALIZADO EM: 2026-11-11 16:40 -03
# VERSAO: 1.2.0
#
# DESCRICAO:
#     Model da tabela tb_6006_reidentificacao_com_baixa_itens.
#     Detalhe do pedido de Reidentificacao COM Baixa (origem
#     GR6006 do GERAS) - uma linha por animal, com o par de
#     codigos SISBOV Antigo -> Novo.
#
#     Vive no SCHEMA DO PRODUTOR, mesmo schema fisico da tabela
#     cabecalho (tb_6005) - a FK id_pedido nao leva prefixo de
#     schema, pois ambas as tabelas moram juntas dentro do
#     schema do Produtor.
#
#     sisbov_antigo / sisbov_novo (VARCHAR(15) cada): SISBOV +
#     digito verificador numa unica coluna de 15 digitos por
#     codigo - mesma regra ja fechada em todo o sistema (nunca
#     coluna separada de DV), mesmo o legado guardando em colunas
#     separadas (Saida SISBOV + Saida Dv, Entrada SISBOV +
#     Entrada Dv).
#
#     rfid (VARCHAR(15), UNICO campo - nao duplicado em
#     antigo/novo): confirmado por Benedito - o chip RFID e um
#     elemento fisico separado do brinco impresso com o SISBOV;
#     na Reidentificacao com Baixa, o animal perde/troca o
#     BRINCO (por isso o SISBOV muda), mas o RFID permanece o
#     mesmo no animal durante todo o processo. Mesmo raciocinio
#     de negocio confirmado tambem para tb_6003/tb_6004_re_id_
#     elementos, que ja nasceram certas por acaso com este
#     desenho (campo rfid unico).
#
#     v1.0.0: Criacao do modulo.
#     v1.1.0: Sessao 121 (2026-11-11 11:40 -03) - REIDENTIFICACAO do Orion: colunas manejo_antigo / manejo_novo (Manejo de 6 digitos do
#         brinco que saiu e do que entrou) e motivo (PERDA / QUEBRA / DESGASTE / DEFEITO_LEITURA, lista fixa, individual por animal).
#         SQL: Tabelas\criar_reidentificacao_s121.sql. REVERSAO: .bak_antes_s121_reidentificacao.
#     v1.2.0: Sessao 121 (2026-11-11 16:40 -03) - NOVO MODELO (decisao do Benedito, 11/11/2026): o animal e lancado ao longo dos dias e fica PENDENTE de Notificacao
#         (id_pedido vazio). Ao gerar a Notificacao (tb_6005) os pendentes entram nela. Colunas novas: id_propriedade, data_reidentificacao (cada animal tem a
#         sua) e id_usuario. SQL: Tabelas\criar_reidentificacao_pendentes_s121.sql. REVERSAO: .bak_antes_s121_pendentes.
# =========================================================

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model ReidentificacaoComBaixaItem
# Espelha a tabela tb_6006_reidentificacao_com_baixa_itens no PostgreSQL
# -------------------------------------------------------
class ReidentificacaoComBaixaItem(Base):
    __tablename__ = 'tb_6006_reidentificacao_com_baixa_itens'

    id                  = Column(Integer, primary_key=True)

    # Vinculo obrigatorio com o cabecalho do pedido. Sem prefixo
    # de schema - tb_6005 mora no mesmo schema do Produtor.
    # v1.2.0 - vazio = animal PENDENTE (ainda sem Notificacao); preenchido = ja entrou na Notificacao
    id_pedido           = Column(Integer, ForeignKey('tb_6005_reidentificacao_com_baixa.id'), nullable=True)
    pedido              = relationship('ReidentificacaoComBaixa', foreign_keys=[id_pedido], backref='itens')

    # v1.2.0 - Propriedade, data da reidentificacao (cada animal tem a sua) e quem lancou
    id_propriedade      = Column(Integer, ForeignKey('public.propriedades.id'))
    data_reidentificacao = Column(Date)
    id_usuario          = Column(Integer)

    # SISBOV + DV numa unica coluna cada (15 digitos), sem coluna
    # separada de digito verificador - padrao do sistema.
    sisbov_antigo       = Column(String(15), nullable=False)
    sisbov_novo         = Column(String(15), nullable=False)

    # RFID e um elemento fisico separado do brinco - permanece o
    # mesmo no animal durante toda a Reidentificacao, por isso um
    # unico campo (nao antigo/novo).
    rfid                = Column(String(15))

    # v1.1.0 (s121) - Manejo de cada brinco e motivo da Reidentificacao (lista fixa; CHECK no banco)
    manejo_antigo       = Column(String(6))
    manejo_novo         = Column(String(6))
    motivo              = Column(String(20))

    # Controle de datas
    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em       = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<ReidentificacaoComBaixaItem {self.sisbov_antigo} -> {self.sisbov_novo}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_6006_reidentificacao_com_baixa_itens.py
# =========================================================