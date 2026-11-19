# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_6012_cancelamento_brinco.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-25 13:42 -03
# ATUALIZADO EM: 2026-07-25 13:42 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_6012_cancelamento_brinco.
#     Cabecalho do pedido de Cancelamento de Brinco (origem
#     GR6012 do GERAS, pasta 6-Formularios, tela "Cadastrar
#     Cancelamento" do menu Formularios).
#
#     Usado quando o Peao vai brincar o animal e o brinco quebra
#     ou fica danificado ANTES de ser utilizado - confirmado por
#     Benedito (Sessao 022). Diferente das demais tabelas da
#     familia de Reidentificacao (tb_6003/6005/6007), que tratam
#     de brincos ja aplicados/associados a um animal - aqui o
#     brinco nunca chegou a ser usado, por isso nao ha RFID
#     associado (ver tb_6013_cancelamento_brinco_itens).
#
#     Vive no SCHEMA DO PRODUTOR (Schema-por-Produtor), mesmo
#     raciocinio ja validado nas demais tabelas desta familia.
#
#     Campo qtde_animais (na tela, "Qtde Briscos a Cancelar"):
#     mesma logica das demais tabelas da familia - trava de
#     conferencia manual do usuario, nao um status automatico.
#
#     Campo motivo (texto livre, VARCHAR(200)): mesmo padrao ja
#     usado em tb_6003_re_id_elementos.
#
#     "Codigo Cancelamento" do legado = o proprio id (SERIAL)
#     desta tabela, sem coluna duplicada.
#
#     v1.0.0: Criacao do modulo.
# =========================================================

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model CancelamentoBrinco
# Espelha a tabela tb_6012_cancelamento_brinco no PostgreSQL
# -------------------------------------------------------
class CancelamentoBrinco(Base):
    __tablename__ = 'tb_6012_cancelamento_brinco'

    # Identificacao - tambem cumpre o papel de "Codigo Cancelamento"
    id                  = Column(Integer, primary_key=True)

    # Lado interno (Propriedade dona do pedido). Isolamento entre
    # Produtores diferentes e garantido pelo schema
    # (Schema-por-Produtor) - id_propriedade diferencia entre as
    # varias Propriedades que um mesmo Produtor pode ter.
    id_propriedade      = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    propriedade         = relationship('Propriedade', foreign_keys=[id_propriedade])

    # Trava de conferencia manual do usuario (nao e status automatico)
    qtde_animais        = Column(Integer, nullable=False)

    # Texto livre, informado pelo usuario
    motivo              = Column(String(200), nullable=False)

    # Informada pelo usuario, pode ser retroativa
    data_solicitacao    = Column(Date, nullable=False)

    # Controle de datas (gravacao real no banco)
    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em       = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<CancelamentoBrinco {self.id}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_6012_cancelamento_brinco.py
# =========================================================