# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_log_alteracao_gta.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-08-21 17:28 -03
# ATUALIZADO EM: 2026-08-21 17:28 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_log_alteracao_gta.
#     Log detalhado de alteracoes feitas numa GTA ja gravada
#     (Sessao 037/038) - uma linha por CAMPO alterado, nao uma
#     linha por edicao inteira. Cobre tanto campos do documento
#     (Emissao, Validade, Meio de Transporte, etc.) quanto
#     categorias de Animais (cada categoria adicionada, removida
#     ou com quantidade alterada vira uma linha propria, com
#     campo_alterado descrevendo a categoria, ex.: "Animal:
#     BOVINO MACHO Zero a 04 Meses").
#
#     Mesmo espirito de tb_log_conferencia_parceiro, ja existente
#     no projeto: nada e sobrescrito silenciosamente, toda
#     alteracao fica registrada para auditoria.
#
#     Mora dentro do schema de cada Produtor (produtor_NNNNN),
#     igual a tb_4001_gta - ver script real
#     Tabelas/criar_tb_log_alteracao_gta.sql.
#
#     v1.0.0: Criacao do modulo (Sessao 037/038), a partir da
#             estrutura definida em
#             Tabelas/criar_tb_log_alteracao_gta.sql (6 colunas
#             + id).
# =========================================================

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model LogAlteracaoGta
# Espelha a tabela tb_log_alteracao_gta no PostgreSQL
# -------------------------------------------------------
class LogAlteracaoGta(Base):
    __tablename__ = 'tb_log_alteracao_gta'

    # Identificacao
    id                  = Column(Integer, primary_key=True)

    # Vinculo obrigatorio com a GTA alterada. Isolamento entre
    # Produtores diferentes e garantido pelo schema
    # (Schema-por-Produtor) - nao precisa de coluna id_produtor
    # aqui, mesmo padrao das demais tabelas de movimento.
    id_gta              = Column(Integer, ForeignKey('tb_4001_gta.id'), nullable=False)
    gta                 = relationship('Gta', foreign_keys=[id_gta], backref='logs_alteracao')

    # Quem alterou. id_usuario aponta para public.usuarios (fora
    # do schema do Produtor); usuario_nome guarda um "retrato"
    # do nome no momento da alteracao, para o historico continuar
    # legivel mesmo se o Usuario for renomeado/desativado depois.
    id_usuario          = Column(Integer, ForeignKey('public.usuarios.id'), nullable=False)
    usuario_nome         = Column(String(150), nullable=False)

    # O que mudou. campo_alterado identifica o campo do
    # documento (ex.: "Data de Validade", "Meio de Transporte")
    # ou a categoria de Animal afetada (ex.: "Animal: BOVINO
    # MACHO Zero a 04 Meses"). valor_anterior/valor_novo em TEXT
    # (nao tipado) para caber qualquer campo, inclusive datas
    # formatadas e marcadores como "REMOVIDA"/"ADICIONADA".
    campo_alterado       = Column(String(60), nullable=False)
    valor_anterior        = Column(Text)
    valor_novo             = Column(Text)

    # Controle de data
    alterado_em          = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<LogAlteracaoGta gta={self.id_gta} campo={self.campo_alterado}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_log_alteracao_gta.py
# =========================================================