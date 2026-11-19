# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_2013_com_morte.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-11-01 16:40 -03
# ATUALIZADO EM: 2026-11-01 16:40 -03
# VERSAO:       1.0.0
#
# DESCRICAO:
#     Model da tabela tb_2013_com_morte - Controle Interno da Morte (MRT000118). Tabela POR-PRODUTOR. Espelho da tb_2013 "Com. Morte" do GERAS:
#     1 linha por LANCAMENTO (individual = 1 animal; por arquivo = N animais com a mesma Data, Tipo, Causa e Destino).
#       controle           = numero do Controle Interno, por Propriedade, comecando em 1 (documento mostra MRT + 6 digitos)
#       numero_comunicado  = Nº da Notificacao de Morte (Anexo XXII) que incluiu este lancamento; vazio ate a Notificacao ser gerada
#       data_morte         = data real da morte (nunca futura nem anterior a entrada do animal)
#       criado_em          = Data e Hora de Emissao (insercao)
#     Os animais do lancamento ficam na tb_2002_saida_animais (tipo_saida = MORTE), ligados por id_com_morte.
#
#     v1.0.0: Sessao 111 (01/11/2026) - Criacao. REVERSAO: Tabelas\criar_morte_s111_b.sql (secao REVERSAO).
# =========================================================
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from .certificadora import Base


class ControleMorte(Base):
    __tablename__ = 'tb_2013_com_morte'
    __table_args__ = (UniqueConstraint('id_propriedade', 'controle', name='uq_tb_2013_propriedade_controle'),)

    id                = Column(Integer, primary_key=True)
    id_propriedade    = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    controle          = Column(Integer, nullable=False)          # Nº do Controle Interno (MRT)
    numero_comunicado = Column(Integer)                           # Nº da Notificacao (vazio = ainda sem Notificacao)
    data_morte        = Column(Date, nullable=False)
    qtd_animais       = Column(Integer, nullable=False, default=0)
    origem            = Column(String(12), nullable=False, default='INDIVIDUAL')   # INDIVIDUAL / ARQUIVO
    id_usuario        = Column(Integer)
    criado_em         = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em     = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<ControleMorte MRT{self.controle:06d}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_2013_com_morte.py
# =========================================================
