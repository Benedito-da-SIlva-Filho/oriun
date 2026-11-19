# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_4005_racas.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-07 12:30 -03
# ATUALIZADO EM: 2026-09-07 12:30 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_4005_racas - cadastro de Racas de
#     animais, usado no dropdown de Raca da Brincagem Sequencial
#     (id_raca em tb_2001) e no codigo de 2 caracteres gravado em
#     tb_7017.raca.
#
#     Vive DENTRO do schema de cada Produtor (Schema-por-Produtor,
#     sem __table_args__ de schema - resolvido via search_path,
#     mesmo padrao de tb_parceiros.py), e NAO numa tabela
#     compartilhada em 'public': cada Produtor tem sua PROPRIA
#     copia completa da lista de racas, com o campo `comum`
#     controlando quais aparecem pra ELE no dropdown da Entrada
#     (decisao de Benedito, Sessao 047 - evita telas com ~100
#     opcoes quando o Produtor so trabalha com 2 ou 3 racas).
#
#     Populada via script avulso (backend/scripts/popular_racas.py),
#     que roda em todo schema 'produtor_%' existente - e deve ser
#     reexecutado sempre que um Produtor novo for criado, ja que
#     nao ha (ainda) nenhum gatilho automatico de provisionamento
#     de schema novo que rode isso sozinho.
#
#     Tela de selecao do Produtor (marcar/desmarcar quais racas
#     sao `comum` a ele) fica para uma sessao futura - por ora
#     todas as racas ja chegam com o valor inicial vindo do
#     arquivo de origem do GERAS (GR4005.TXT).
#
#     v1.0.0: Criacao do modulo (Sessao 047).
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model Raca
# Espelha a tabela tb_4005_racas no PostgreSQL (schema do
# Produtor logado, via search_path)
# -------------------------------------------------------
class Raca(Base):
    __tablename__ = 'tb_4005_racas'

    # Identificacao
    id              = Column(Integer, primary_key=True)
    codigo          = Column(String(2), nullable=False, unique=True)
    nome            = Column(String(60), nullable=False)

    # Selecao do Produtor: quais racas aparecem pra ele no
    # dropdown da Entrada (evita lista cheia de ~100 opcoes)
    comum           = Column(Boolean, nullable=False, default=False)

    # Controle de status (soft-delete, mesmo padrao do projeto)
    ativo           = Column(Boolean, nullable=False, default=True)

    # Controle de datas
    criado_em       = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em   = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Raca {self.codigo} - {self.nome}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_4005_racas.py
# =========================================================