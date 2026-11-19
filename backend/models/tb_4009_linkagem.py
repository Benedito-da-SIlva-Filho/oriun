# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_4009_linkagem.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-11-10 21:10 -03
# ATUALIZADO EM: 2026-11-10 21:10 -03
# VERSAO:       1.0.0
#
# DESCRICAO:
#     Model da tabela tb_4009_linkagem - um registro por par RFID + SISBOV ligado na Linkagem RFID e Brinco.
#     Base da Consulta e do PDF da Linkagem (por data). Cada linha entra no Log como INSERT, entao o Desfazer
#     da operacao apaga a linha. Tabela POR-PRODUTOR (Schema-por-Produtor): sem schema fixo no Model.
#     Guarda tambem o lote e o peso informados na hora (opcionais).
#
#     Script de criacao: Tabelas\criar_linkagem_s120_b.sql.
#
#     v1.0.0: Criacao (Sessao 120, 10/11/2026, 21:10 -03).
# =========================================================

from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, Time, DateTime, Numeric, ForeignKey

from .certificadora import Base


class Linkagem(Base):
    __tablename__ = 'tb_4009_linkagem'

    id             = Column(Integer, primary_key=True)
    id_propriedade = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    id_usuario     = Column(Integer)
    sisbov         = Column(String(15), nullable=False)
    rfid           = Column(String(15), nullable=False)
    data_linkagem  = Column(Date, nullable=False)
    hora_linkagem  = Column(Time)
    lote           = Column(String(30))
    peso           = Column(Numeric(6, 2))
    criado_em      = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<Linkagem {self.sisbov} {self.rfid}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_4009_linkagem.py
# =========================================================
