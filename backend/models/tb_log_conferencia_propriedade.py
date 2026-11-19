# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_log_conferencia_propriedade.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-29 10:04 -03
# ATUALIZADO EM: 2026-07-29 10:04 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_log_conferencia_propriedade.
#     Log de auditoria imutavel do lado INTERNO (Destino/
#     Propriedade) da leitura de GTA - fecha o P-029 do
#     Diario 025. Espelha tb_log_conferencia_parceiro (lado
#     externo), mas cobre um cenario diferente: quando o
#     bloco Destino encontra MAIS DE UMA Propriedade do
#     proprio Produtor batendo com os criterios de busca
#     (via propriedade_produtor), o usuario escolhe manualmente
#     qual e a correta. Quando existe so uma correspondencia,
#     o sistema resolve sozinho e NAO gera log aqui (Diario
#     025, Secao 4.2) - esta tabela so recebe linha quando
#     houve intervencao humana de verdade.
#
#     Situacao unica (tipo_situacao):
#       AMBIGUIDADE_PROPRIEDADE - mais de uma Propriedade
#       propria encontrada, usuario escolheu entre as
#       candidatas.
#
#     Campo central: justificativa_usuario (obrigatorio) - o
#     proprio usuario escreve o motivo da escolha, ratificando
#     e assumindo a responsabilidade pela decisao. Mesma regra
#     de automacao restritiva do lado Parceiro (Secao 5 do
#     Diario 016): o sistema nunca decide sozinho em caso de
#     ambiguidade.
#
#     Vive dentro do schema de cada Produtor (Schema-por-
#     Produtor, Sessao 018), junto das demais tabelas de
#     Movimentacao. FKs para tabelas public (usuarios,
#     propriedades) usam prefixo explicito 'public.' - licao
#     da Sessao 019 sobre schema_translate_map "sequestrar"
#     tabelas public referenciadas por FK.
#
#     Log imutavel: sem atualizado_em, sem trigger.
#
#     v1.0.0: Criacao do modulo (Sessao 026), a partir do
#             desenho fechado com Benedito - espelho de
#             tb_log_conferencia_parceiro (v1.3.0) adaptado
#             para o lado interno.
# =========================================================

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model LogConferenciaPropriedade
# Espelha a tabela tb_log_conferencia_propriedade no PostgreSQL
# -------------------------------------------------------
class LogConferenciaPropriedade(Base):
    __tablename__ = 'tb_log_conferencia_propriedade'

    # Identificacao
    id                          = Column(Integer, primary_key=True)

    # Usuario responsavel pela decisao (sempre obrigatorio -
    # nunca "o software decidiu", sempre "o usuario X escolheu
    # e justificou"). Isolamento entre Produtores diferentes e
    # garantido pelo schema (Schema-por-Produtor).
    id_usuario                  = Column(Integer, ForeignKey('public.usuarios.id'), nullable=False)
    usuario                     = relationship('Usuario', foreign_keys=[id_usuario])

    # Propriedade escolhida pelo usuario entre as candidatas
    # ambiguas (sempre a propria Propriedade do Produtor, nunca
    # uma Propriedade de Parceiro externo - isso e o lado
    # Parceiro, tratado em tb_log_conferencia_parceiro)
    id_propriedade               = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    propriedade                  = relationship('Propriedade', foreign_keys=[id_propriedade], backref='logs_conferencia')

    # Dados da decisao
    tipo_situacao                = Column(String(20), nullable=False, default='AMBIGUIDADE_PROPRIEDADE')
    justificativa_usuario        = Column(Text, nullable=False)          # obrigatorio - motivo escrito pelo usuario
    decisao_tomada                = Column(String(30), nullable=False, default='CONFIRMOU_PROPRIEDADE')

    # Controle de data (log imutavel - sem atualizado_em, o
    # registro nunca e editado depois de criado)
    data_hora                    = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<LogConferenciaPropriedade Propriedade {self.id_propriedade}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_log_conferencia_propriedade.py
# =========================================================