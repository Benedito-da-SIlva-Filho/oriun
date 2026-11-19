# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_4008_linkagem_inconformes.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-11-10 18:20 -03
# ATUALIZADO EM: 2026-11-10 18:20 -03
# VERSAO:       1.0.0
#
# DESCRICAO:
#     Model da tabela tb_4008_linkagem_inconformes - tudo que deu errado na Linkagem RFID e Brinco
#     (RFID ja em uso, SISBOV fora do estoque da fazenda, SISBOV que ja tem RFID...). Uma linha por
#     tentativa recusada. Tabela POR-PRODUTOR (Schema-por-Produtor): sem schema fixo no Model -
#     resolvido em tempo de execucao por get_db_produtor(). Guarda o que foi LIDO/DIGITADO (em texto),
#     por isso nao ha FK para o animal. Molde: tb_4007_pesagem_inconformes.
#
#     Script de criacao: Tabelas\criar_linkagem_s120.sql.
#
#     v1.0.0: Criacao (Sessao 120, 10/11/2026, 18:20 -03).
# =========================================================

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from .certificadora import Base


class LinkagemInconforme(Base):
    __tablename__ = 'tb_4008_linkagem_inconformes'

    id             = Column(Integer, primary_key=True)
    id_propriedade = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    id_usuario     = Column(Integer)
    rfid           = Column(String(40))            # como foi lido/digitado
    sisbov         = Column(String(40))            # como foi lido/digitado (vazio quando o erro foi no RFID)
    motivo         = Column(String(200), nullable=False)
    criado_em      = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<LinkagemInconforme {self.rfid} {self.sisbov} {self.motivo[:30]}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_4008_linkagem_inconformes.py
# =========================================================
