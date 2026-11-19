# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_2021_notificacao_morte.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-11-01 16:30 -03
# ATUALIZADO EM: 2026-11-01 16:30 -03
# VERSAO:       1.0.0
#
# DESCRICAO:
#     Model da tabela tb_2021_notificacao_morte - Notificacao de Morte (Anexo XXII), 1 linha por Notificacao. Tabela POR-PRODUTOR.
#     A Morte NAO tem GTA: por isso nao usa a tb_2011 (1 linha por GTA). O numero da Notificacao vai tambem em
#     tb_2002_saida_animais.numero_comunicado (tipo_saida = MORTE) de cada animal incluido. Numeracao propria, por Propriedade,
#     comecando em 000001. A Notificacao junta TODAS as mortes da Propriedade ainda sem numero (decisao do Benedito, 01/11/2026).
#     status: ABERTO (gerada) -> IMPRESSO (1a impressao; a Reimpressao nunca grava).
#
#     v1.0.0: Sessao 111 (01/11/2026) - Criacao. REVERSAO: DROP TABLE produtor_NNNNN.tb_2021_notificacao_morte (todos os schemas)
#             e voltar tb_versao_schema para 5.
# =========================================================
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from .certificadora import Base


class NotificacaoMorte(Base):
    __tablename__ = 'tb_2021_notificacao_morte'
    __table_args__ = (UniqueConstraint('id_propriedade', 'numero_comunicado', name='uq_tb_2021_propriedade_numero'),)

    id                   = Column(Integer, primary_key=True)
    id_propriedade       = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    numero_comunicado    = Column(Integer, nullable=False)       # Nº da Notificacao (ex.: 001267 no Anexo XXII)
    qtd_animais          = Column(Integer, nullable=False, default=0)
    status               = Column(String(20), nullable=False, default='ABERTO')   # ABERTO -> IMPRESSO
    data_envio           = Column(Date)
    impresso_em          = Column(DateTime)
    id_usuario_impressao = Column(Integer)
    id_usuario_geracao   = Column(Integer)
    criado_em            = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em        = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<NotificacaoMorte {self.numero_comunicado}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_2021_notificacao_morte.py
# =========================================================
