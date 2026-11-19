# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_6004_re_id_elementos_itens.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-25 11:16 -03
# ATUALIZADO EM: 2026-07-25 11:16 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_6004_re_id_elementos_itens.
#     Detalhe do pedido de Reidentificacao por Elementos (GR6004
#     do GERAS, pasta 6-Formularios) - uma linha por animal/SISBOV
#     dentro de um pedido (tb_6003_re_id_elementos).
#
#     Vive no SCHEMA DO PRODUTOR (Schema-por-Produtor), mesmo
#     schema fisico da tabela cabecalho (tb_6003) - a FK
#     id_pedido nao leva prefixo de schema, pois ambas as
#     tabelas moram juntas dentro do schema do Produtor.
#
#     codigo_sisbov (VARCHAR(15)): SISBOV + digito verificador
#     numa unica coluna de 15 digitos - mesma regra ja fechada
#     em todo o sistema (nunca coluna separada de DV), mesmo
#     quando o legado guardava em duas colunas (Codigo SISBOV +
#     Dv), como confirmado por Benedito a partir do print real.
#
#     rfid (VARCHAR(15)): confirmado por Benedito.
#
#     v1.0.0: Criacao do modulo.
# =========================================================

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model ReIdElementosItem
# Espelha a tabela tb_6004_re_id_elementos_itens no PostgreSQL
# -------------------------------------------------------
class ReIdElementosItem(Base):
    __tablename__ = 'tb_6004_re_id_elementos_itens'

    id                  = Column(Integer, primary_key=True)

    # Vinculo obrigatorio com o cabecalho do pedido. Sem prefixo
    # de schema - tb_6003 mora no mesmo schema do Produtor.
    id_pedido           = Column(Integer, ForeignKey('tb_6003_re_id_elementos.id'), nullable=False)
    pedido              = relationship('ReIdElementos', foreign_keys=[id_pedido], backref='itens')

    # SISBOV + DV numa unica coluna (15 digitos) - padrao do
    # sistema, sem coluna separada de digito verificador.
    codigo_sisbov       = Column(String(15), nullable=False)

    rfid                = Column(String(15))

    # Controle de datas
    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em       = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<ReIdElementosItem sisbov={self.codigo_sisbov}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_6004_re_id_elementos_itens.py
# =========================================================