# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_1021_fabricantes_brincos.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-17 09:55 -03
# ATUALIZADO EM: 2026-07-17 09:55 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_1021_fabricantes_brincos.
#     Catalogo de Fabricantes de Brincos (fornecedores dos
#     brincos/lacres oficiais). Corresponde ao "1021 - Fornecedor
#     de Brincos" no GERAS.
#
#     Vive no schema publico (compartilhado entre todos os
#     Produtores), conforme classificacao fechada na Sessao 018 -
#     nao faz parte do schema-por-produtor, pois um mesmo
#     Fabricante pode fornecer brincos para varios Produtores
#     diferentes.
#
#     E referenciado por tb_3007_brincos_entrada.id_fabricante
#     (cada lote de brincos comprado indica de qual Fabricante
#     veio).
#
#     Campo uf (VARCHAR(2)): quando a tela de cadastro deste
#     Model for construida, pelo Padrao de Validacao ja fechado
#     (Sessao 010), este campo devera ser dropdown fechado com
#     as 27 UFs - nunca texto livre.
#
#     v1.0.0: Criacao do modulo (Sessao 019), a partir da
#             estrutura real de tb_1021_fabricantes_brincos
#             conferida no pgAdmin (12 colunas).
#     v1.1.0: Sessao 019 - Adicionado __table_args__ com schema
#             'public' explicito. Mesmo motivo de produtor.py v2.2.0 -
#             Fabricante e referenciada por FK a partir de
#             tb_3007_brincos_entrada.id_fabricante.
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model Fabricante
# Espelha a tabela tb_1021_fabricantes_brincos no PostgreSQL
# -------------------------------------------------------
class Fabricante(Base):
    __tablename__ = 'tb_1021_fabricantes_brincos'
    __table_args__ = {'schema': 'public'}

    # Identificacao
    id                  = Column(Integer, primary_key=True)
    nome                = Column(String(50), nullable=False)
    logo                = Column(String(100))

    # Endereco
    endereco            = Column(String(50))
    complemento         = Column(String(50))
    bairro              = Column(String(40))
    cidade              = Column(String(40))
    # NOTA: dropdown fechado (27 UFs) na tela - nunca texto livre
    uf                  = Column(String(2))
    cep                 = Column(String(8))

    # Situacao
    ativo               = Column(Boolean, nullable=False, default=True)

    # Controle de datas
    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em        = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Fabricante {self.nome}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_1021_fabricantes_brincos.py
# =========================================================