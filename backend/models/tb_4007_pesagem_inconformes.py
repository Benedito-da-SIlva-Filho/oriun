# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_4007_pesagem_inconformes.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-11-04 11:10 -03
# ATUALIZADO EM: 2026-11-04 11:10 -03
# VERSAO:       1.0.0
#
# DESCRICAO:
#     Model da tabela tb_4007_pesagem_inconformes - tudo que deu errado no Leitor de Peso
#     (brinco com digitos faltando, DV errado, animal morto/vendido/abatido, brinco do estoque,
#     peso incorreto, pesagem repetida na data...). Uma linha por tentativa recusada. A lista
#     "Inconformes" do Hub de Pesos le esta tabela (decisao do Benedito, Sessao 114: "qualquer
#     erro que der fica gravado"). Tabela POR-PRODUTOR (Schema-por-Produtor): sem schema fixo
#     no Model - resolvido em tempo de execucao por get_db_produtor().
#     Guarda o que foi LIDO/DIGITADO (sisbov/manejo/peso em texto), por isso nao ha FK para o animal.
#
#     Script de criacao: Tabelas\criar_pesos_s114.sql.
#
#     v1.0.0: Criacao (Sessao 114, 04/11/2026, 11:10 -03).
# =========================================================

from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey

from .certificadora import Base


class PesagemInconforme(Base):
    __tablename__ = 'tb_4007_pesagem_inconformes'

    id             = Column(Integer, primary_key=True)
    id_propriedade = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    id_usuario     = Column(Integer)
    sisbov         = Column(String(40))            # como foi lido/digitado (pode ter digitos faltando)
    manejo         = Column(String(10))
    data_pesagem   = Column(Date)                  # Data da Pesagem da Selecao
    peso_digitado  = Column(String(20))            # texto digitado (so quando o erro foi no peso)
    motivo         = Column(String(200), nullable=False)
    criado_em      = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<PesagemInconforme {self.sisbov} {self.motivo[:30]}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_4007_pesagem_inconformes.py
# =========================================================
