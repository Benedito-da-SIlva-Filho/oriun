# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_log_operacoes.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-03 15:30 -03
# ATUALIZADO EM: 2026-09-03 15:30 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_log_operacoes - o "recibo" de cada
#     operacao que grava dados no sistema, base do mecanismo
#     "Desfazer por Operacao" (Log de Operacoes, alinhado com
#     Benedito na Sessao 045). Generico e reaproveitavel por
#     qualquer modulo (piloto: Cancelamento de Brincos) - cada
#     modulo so precisa chamar backend/utils/log_operacoes.py
#     para registrar o que fez.
#
#     Vive dentro do schema do Produtor (Schema-por-Produtor,
#     mesma logica de tb_3007/tb_3008/tb_7017) - isolamento
#     garantido pelo proprio schema, sem coluna id_produtor.
#
#     1 operacao (esta tabela) pode ter N itens de mudanca
#     (tb_log_operacoes_itens) - ex.: um Cancelamento de 3
#     brincos gera 1 linha aqui + varias linhas em
#     tb_log_operacoes_itens (uma por tabela/linha mexida).
#
#     desfeito_em/desfeito_por ficam NULOS ate a operacao ser
#     desfeita - usados tanto para saber SE ja foi desfeita
#     (nao pode desfazer 2x) quanto para auditoria (quem
#     desfez, quando).
#
#     Regras de negocio (Sessao 045):
#       - Janela de 24h para desfazer, calculada a partir de
#         criado_em.
#       - Pode desfazer quem fez (id_usuario) OU quem tem Cargo
#         TITULAR, ADMINISTRADOR ou ADMINISTRATIVO.
#
#     v1.0.0: Criacao do modulo (Sessao 045, 03/09/2026, 15:30 -03).
# =========================================================

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model LogOperacao
# Espelha a tabela tb_log_operacoes no PostgreSQL
# -------------------------------------------------------
class LogOperacao(Base):
    __tablename__ = 'tb_log_operacoes'

    id               = Column(Integer, primary_key=True)

    # Quem fez a operacao original - usado tanto para exibir
    # "quem fez" quanto para a regra de permissao do Desfazer
    # ("quem fez pode desfazer").
    id_usuario       = Column(Integer, ForeignKey('public.usuarios.id'), nullable=False)

    id_propriedade   = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)

    # Nome curto do modulo que gerou a operacao (ex.:
    # 'cancelamento_brincos') - usado so para exibicao/filtro,
    # nao ha logica de codigo dependendo do valor exato.
    modulo           = Column(String(40), nullable=False)

    # Texto legivel para o Usuario ver na tela (ex.: "Cancelamento
    # de 3 brinco(s) - Motivo: VENDIDO").
    descricao        = Column(String(255), nullable=False)

    criado_em        = Column(DateTime, nullable=False, default=datetime.now)

    # Preenchidos so quando a operacao e desfeita - NULOS ate la.
    desfeito_em      = Column(DateTime)
    desfeito_por     = Column(Integer, ForeignKey('public.usuarios.id'))

    def __repr__(self):
        return f'<LogOperacao {self.id} ({self.modulo})>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_log_operacoes.py
# =========================================================