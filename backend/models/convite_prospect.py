# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\convite_prospect.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-08-11 19:33 -03
# ATUALIZADO EM: 2026-08-12 10:30 -03
# VERSAO:       1.1.0
#
# DESCRICAO:
#     Model da tabela convite_prospects (schema public).
#     Registro de cada convite comercial enviado pela Consiste
#     a um Produtor prospect, usando o link fixo /convite
#     (Convite Publico, ja existente - backend/routers/convite.py).
#
#     NAO tem FK nem relacionamento com Produtor/Propriedade -
#     o prospect pode nunca vir a se cadastrar, e mesmo se
#     cadastrar, o /convite nao carrega nenhum identificador
#     que ligue de volta a este registro (link generico, sem
#     token - decisao da Sessao 032). Esta tabela e so o
#     historico de "quem a Consiste convidou".
#
#     v1.0.0: Criacao do modulo (Sessao 034, continuacao 6).
#             Decisao de Benedito: Consiste precisa de um meio
#             de convidar prospects a conhecer o produto,
#             reaproveitando o link ja existente do Convite
#             Publico. Fase 1 = e-mail; WhatsApp fica para
#             fase futura (nao afeta esta tabela).
#     v1.1.0: Adicionados telefone (opcional, so digitos, usado
#             para montar o link wa.me) e canal (obrigatorio,
#             default 'EMAIL', valores 'EMAIL'/'WHATSAPP').
#             Permite registros duplicados por prospect -
#             historico completo por canal (Sessao 034,
#             continuacao 8).
# =========================================================

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model ConviteProspect
# Espelha a tabela convite_prospects no PostgreSQL
# -------------------------------------------------------
class ConviteProspect(Base):
    __tablename__ = 'convite_prospects'
    __table_args__ = {'schema': 'public'}

    id                  = Column(Integer, primary_key=True)
    nome                = Column(String(150), nullable=False)
    email               = Column(String(150), nullable=False)
    telefone            = Column(String(11), nullable=True)
    canal               = Column(String(10), nullable=False, default='EMAIL')
    id_usuario_consiste = Column(Integer, ForeignKey('public.usuarios.id'), nullable=False)
    enviado_em          = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<ConviteProspect {self.nome} - {self.email} - {self.canal}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\convite_prospect.py
# =========================================================