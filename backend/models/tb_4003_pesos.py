# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_4003_pesos.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-02 22:00 -03
# ATUALIZADO EM: 2026-11-04 11:20 -03
# VERSAO:       1.1.0
#
# DESCRICAO:
#     Model da tabela tb_4003_pesos - historico de PESAGENS do animal
#     (equivalente enxuto da tabela 4003 "Peso Animal" do GERAS). Uma
#     linha por pesagem; o animal e identificado pelo SISBOV (a tb_2001
#     apaga o animal na saida, o historico de peso fica). A pesagem de
#     SEQUENCIA 1 e a do brete, no dia da Brincagem (Nascimento/
#     Desmame: o peso so e validado no brete - decisao de Benedito,
#     Sessao 084). Tabela POR-PRODUTOR (Schema-por-Produtor): sem schema
#     fixo no Model - resolvido em tempo de execucao por
#     get_db_produtor().
#
#     Fora desta versao (decisao de Benedito): GTA, sigla, contrato,
#     elemento e envio do GERAS. Acrescentados: origem e id_usuario.
#
#     Script de criacao: Tabelas\10_create_tb_4003_pesos.sql.
#
#     v1.0.0: Criacao (Sessao 084, 02/10/2026, 22:00 -03).
#     v1.1.0: Sessao 114 (2026-11-04 11:20 -03) - Coluna elemento_perdido (perda de Botton/Brinco registrada na pesagem) e origem BRETE_PESO (Leitor de Peso). SQL: Tabelas\criar_pesos_s114.sql.  REVERSAO: .bak_antes_s114_pesos.
# =========================================================

from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, Time, DateTime, Numeric, Text, ForeignKey, UniqueConstraint

from .certificadora import Base


class Peso(Base):
    __tablename__ = 'tb_4003_pesos'
    __table_args__ = (UniqueConstraint('sisbov', 'sequencia', name='uq_tb_4003_sisbov_sequencia'),)

    id             = Column(Integer, primary_key=True)
    id_propriedade = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    sisbov         = Column(String(15), nullable=False)
    rfid           = Column(String(15))
    sequencia      = Column(Integer, nullable=False)          # 1, 2, 3... por animal
    data_pesagem   = Column(Date, nullable=False)
    hora_pesagem   = Column(Time)
    peso           = Column(Numeric(6, 2), nullable=False)     # kg
    ganho_peso     = Column(Numeric(6, 2))                     # peso - pesagem anterior (vazio na 1a)
    eras_dias      = Column(Integer)                           # idade em dias na pesagem
    lote           = Column(String(30))
    origem         = Column(String(30), nullable=False)        # BRETE_NASCIMENTO / BRETE_COMPRA / BRETE_PESO / MANUAL
    observacao     = Column(Text)
    elemento_perdido = Column(String(10))                      # BOTTON / BRINCO / vazio (v1.1.0 - Sessao 114)
    id_usuario     = Column(Integer)
    criado_em      = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<Peso {self.sisbov} #{self.sequencia} {self.peso}kg>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_4003_pesos.py
# =========================================================
