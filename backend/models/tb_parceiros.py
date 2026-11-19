# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_parceiros.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-15 10:28 -03
# ATUALIZADO EM: 2026-07-17 16:20 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_parceiros.
#     Cadastro de Parceiro externo (pessoa fisica ou juridica
#     que compra ou vende animais para o Produtor, incluindo
#     o caso do proprio Produtor sendo seu parceiro numa
#     Transferencia). Sem correspondente no legado GERAS,
#     criado na Sessao 16 a partir dos dados ricos de
#     Procedencia/Destino de uma e-GTA real (IAGRO/MS).
#
#     Um Parceiro pode ter varias Propriedades vinculadas
#     (1:N, cada uma com seu Codigo MAPA), via tabela
#     tb_parceiros_propriedades.
#
#     O campo id_produtor (FK nullable) so e preenchido
#     quando o usuario confirma manualmente, na tela de
#     conferencia humana, que esse Parceiro corresponde a um
#     Produtor ja cadastrado no Orion (caso de Transferencia).
#     Nunca e preenchido automaticamente (ver regra de
#     conferencia humana obrigatoria, Secao 5 do Diario 016).
#
#     v1.0.0: Criacao do modulo (Sessao 17), a partir da
#             estrutura real de tb_parceiros conferida no
#             pgAdmin (7 colunas).
#
#     v1.1.0: Sessao 019 - Corrigida FK id_produtor para
#             'public.produtores.id' (com prefixo de schema
#             explicito). Motivo: apos produtor.py v2.2.0 marcar
#             __table_args__ = {'schema': 'public'}, referencias
#             sem o prefixo 'public.' deixaram de encontrar a
#             tabela produtores - esta foi a causa raiz do erro
#             original (UndefinedTable) na rotina de Onboarding.
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model Parceiro
# Espelha a tabela tb_parceiros no PostgreSQL
# -------------------------------------------------------
class Parceiro(Base):
    __tablename__ = 'tb_parceiros'

    # Identificacao
    id              = Column(Integer, primary_key=True)
    cpf_cnpj        = Column(String(18), nullable=False)
    nome            = Column(String(150), nullable=False)

    # Vinculo opcional: preenchido apenas quando o usuario
    # confirma manualmente, na tela de conferencia, que este
    # Parceiro corresponde a um Produtor ja cadastrado no
    # Orion. Nunca preenchido de forma automatica.
    id_produtor     = Column(Integer, ForeignKey('public.produtores.id'))
    produtor        = relationship('Produtor', foreign_keys=[id_produtor], backref='parceiros')

    # Controle de status
    ativo           = Column(Boolean, nullable=False, default=True)

    # Controle de datas
    criado_em       = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em   = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Parceiro {self.nome}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_parceiros.py
# =========================================================