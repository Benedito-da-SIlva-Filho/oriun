# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\vitrine_visitante.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-08-11 20:30 -03
# ATUALIZADO EM: 2026-08-13 13:20 -03
# VERSAO:       1.1.0
#
# DESCRICAO:
#     Model da tabela vitrine_visitantes (schema public).
#     Registro de cada visitante que preencheu a Etapa 1 do
#     Convite Publico (/convite) e foi direcionado a Tela Vitrine,
#     em vez de seguir direto para a criacao de conta real (Etapa
#     2, pausada - ver convite.py v2.2.0).
#
#     v1.0.0: Criacao do modulo (Sessao 034, continuacao 6).
#             Decisao de Benedito: em vez de criar conta real (com
#             senha provisoria) direto na Etapa 1, o visitante ve
#             uma vitrine publica travada do sistema primeiro; a
#             conta real so nasce depois que a Consiste conversa
#             com ele e ele "compra a ideia".
#     v1.1.0: Sessao 034 (continuacao 9, 13/08/2026, 13:20 -03) -
#             Cenario 2 (reconexao da Etapa 2): duas colunas novas
#             para rastrear a conversao do visitante em cliente
#             real, feita pela nova tela "Visitantes da Vitrine"
#             (backend/routers/vitrine_visitantes.py):
#               id_produtor_criado - FK nullable para
#               produtores.id, preenchida so no momento da
#               conversao (manual ou por auto-deteccao).
#               convertido_em - TIMESTAMP nullable, marca o
#               momento da conversao. NULL = ainda aparece na
#               lista de visitantes pendentes; preenchido = ja e
#               cliente, some da lista (decisao de Benedito).
#             Ver Tabelas\alterar_vitrine_visitantes_conversao.sql.
# =========================================================

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model VitrineVisitante
# Espelha a tabela vitrine_visitantes no PostgreSQL
# -------------------------------------------------------
class VitrineVisitante(Base):
    __tablename__ = 'vitrine_visitantes'
    __table_args__ = {'schema': 'public'}

    id          = Column(Integer, primary_key=True)
    cpf_cnpj    = Column(String(18), nullable=False)
    nome        = Column(String(150), nullable=False)
    email       = Column(String(150), nullable=False)
    telefone    = Column(String(20), nullable=False)
    visitado_em = Column(DateTime, nullable=False, default=datetime.now)

    # v1.1.0: rastreamento de conversao em cliente real (Cenario 2).
    # Ambos nullable - so preenchidos no momento da conversao.
    id_produtor_criado = Column(Integer, ForeignKey('public.produtores.id'), nullable=True)
    convertido_em       = Column(DateTime, nullable=True)

    def __repr__(self):
        return f'<VitrineVisitante {self.nome} - {self.cpf_cnpj}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\vitrine_visitante.py
# =========================================================