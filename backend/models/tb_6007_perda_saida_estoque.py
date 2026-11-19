# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_6007_perda_saida_estoque.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-25 13:19 -03
# ATUALIZADO EM: 2026-07-25 13:19 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_6007_perda_saida_estoque.
#     Cabecalho do pedido de Perda Saida Estoque (origem GR6007
#     do GERAS, pasta 6-Formularios, tela "Cadastrar Perda" do
#     menu Formularios, bloco "Reidentificacao sem Baixa").
#
#     Usado quando o animal NAO TEM NENHUM elemento de
#     identificacao (confirmado por Benedito, Sessao 022) - o
#     Produtor avisa o MAPA que vai utilizar elementos novos; na
#     proxima vacinacao, descobrem qual brinco estava faltando e
#     o ciclo se fecha. Diferente de tb_6003_re_id_elementos
#     (mesmo SISBOV, so troca a peca fisica) e de
#     tb_6005_reidentificacao_com_baixa (par Antigo->Novo, o
#     animal ja tinha identificacao antes).
#
#     Vive no SCHEMA DO PRODUTOR (Schema-por-Produtor), mesmo
#     raciocinio ja validado nas demais tabelas de Reidentificacao.
#
#     Campo qtde_animais: mesma logica das demais tabelas desta
#     familia - trava de conferencia manual do usuario, nao um
#     status automatico.
#
#     Campos biologicos da tela (Especie, Raca, Aptidao, Sexo,
#     Nro Meses, Nascimento, Lote) foram DELIBERADAMENTE
#     OMITIDOS - confirmado por Benedito que nao servem para
#     nada gravado (nem na 6007 nem na 6008 do legado).
#
#     Campo "Tipo Reidentificacao" do legado (valor fixo
#     truncado "REIDENTIFI...") tambem OMITIDO - redundante,
#     mesma decisao ja aplicada em tb_6005_reidentificacao_com_
#     baixa (tabela dedicada a um unico processo).
#
#     "Codigo Reidentificacao" do legado = o proprio id (SERIAL)
#     desta tabela, sem coluna duplicada.
#
#     v1.0.0: Criacao do modulo.
# =========================================================

from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model PerdaSaidaEstoque
# Espelha a tabela tb_6007_perda_saida_estoque no PostgreSQL
# -------------------------------------------------------
class PerdaSaidaEstoque(Base):
    __tablename__ = 'tb_6007_perda_saida_estoque'

    # Identificacao - tambem cumpre o papel de "Codigo Reidentificacao"
    id                  = Column(Integer, primary_key=True)

    # Lado interno (Propriedade dona do pedido). Isolamento entre
    # Produtores diferentes e garantido pelo schema
    # (Schema-por-Produtor) - id_propriedade diferencia entre as
    # varias Propriedades que um mesmo Produtor pode ter.
    id_propriedade      = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    propriedade         = relationship('Propriedade', foreign_keys=[id_propriedade])

    # Trava de conferencia manual do usuario (nao e status automatico)
    qtde_animais        = Column(Integer, nullable=False)

    # Informada pelo usuario, pode ser retroativa
    data_solicitacao    = Column(Date, nullable=False)

    # Controle de datas (gravacao real no banco)
    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em       = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<PerdaSaidaEstoque {self.id}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_6007_perda_saida_estoque.py
# =========================================================