# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_6008_perda_saida_estoque_itens.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-25 13:19 -03
# ATUALIZADO EM: 2026-07-25 13:19 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_6008_perda_saida_estoque_itens.
#     Detalhe do pedido de Perda Saida Estoque (origem GR6008 do
#     GERAS) - uma linha por animal, com o codigo SISBOV
#     atribuido pela primeira vez.
#
#     Vive no SCHEMA DO PRODUTOR, mesmo schema fisico da tabela
#     cabecalho (tb_6007) - a FK id_pedido nao leva prefixo de
#     schema.
#
#     Diferente de tb_6006_reidentificacao_com_baixa_itens (que
#     guarda um PAR Antigo->Novo, pois o animal ja tinha
#     identificacao), aqui existe SO O CODIGO NOVO
#     (sisbov_atribuido) - confirmado por Benedito a partir dos
#     dados reais do legado, onde os campos "Saida SISBOV" e
#     "Saida RFID" apareciam sempre zerados (o animal nunca teve
#     identificacao antes). Sem coluna de "saida" que ficaria
#     sempre vazia.
#
#     SEM RFID - confirmado por Benedito, decisao consciente de
#     nao incluir este campo nesta tabela (diferente das demais
#     tabelas da familia de Reidentificacao, que tem rfid).
#
#     sisbov_atribuido (VARCHAR(15)): SISBOV + digito verificador
#     numa unica coluna de 15 digitos - mesma regra ja fechada em
#     todo o sistema.
#
#     v1.0.0: Criacao do modulo.
# =========================================================

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model PerdaSaidaEstoqueItem
# Espelha a tabela tb_6008_perda_saida_estoque_itens no PostgreSQL
# -------------------------------------------------------
class PerdaSaidaEstoqueItem(Base):
    __tablename__ = 'tb_6008_perda_saida_estoque_itens'

    id                  = Column(Integer, primary_key=True)

    # Vinculo obrigatorio com o cabecalho do pedido. Sem prefixo
    # de schema - tb_6007 mora no mesmo schema do Produtor.
    id_pedido           = Column(Integer, ForeignKey('tb_6007_perda_saida_estoque.id'), nullable=False)
    pedido              = relationship('PerdaSaidaEstoque', foreign_keys=[id_pedido], backref='itens')

    # SISBOV + DV numa unica coluna (15 digitos) - codigo
    # atribuido pela primeira vez (animal nao tinha identificacao
    # antes). Sem RFID (decisao consciente de Benedito).
    sisbov_atribuido    = Column(String(15), nullable=False)

    # Controle de datas
    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em       = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<PerdaSaidaEstoqueItem sisbov={self.sisbov_atribuido}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_6008_perda_saida_estoque_itens.py
# =========================================================