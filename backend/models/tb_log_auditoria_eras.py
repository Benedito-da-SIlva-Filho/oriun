# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_log_auditoria_eras.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-07 12:05 -03
# ATUALIZADO EM: 2026-10-07 12:05 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_log_auditoria_eras (schema public).
#     Log das CORRECOES feitas numa vistoria ja registrada: uma
#     linha por campo alterado (valor anterior e novo em texto),
#     com quem alterou e quando. Mesmo espirito de
#     tb_log_alteracao_gta: nada e sobrescrito em silencio.
#
#     confirmou_alerta_60: True quando a vistoria corrigida tinha
#     60 dias ou mais e a pessoa confirmou o alerta "alterar pode
#     comprometer a propriedade" antes de salvar.
#
#     v1.0.0: Criacao do modulo (Sessao 089, 07/10/2026, 12:05 -03).
# =========================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model LogAuditoriaEras
# Espelha a tabela tb_log_auditoria_eras no PostgreSQL
# -------------------------------------------------------
class LogAuditoriaEras(Base):
    __tablename__ = 'tb_log_auditoria_eras'
    __table_args__ = {'schema': 'public'}

    id                   = Column(Integer, primary_key=True)
    id_auditoria         = Column(Integer, ForeignKey('public.tb_auditoria_eras.id'), nullable=False)
    id_usuario           = Column(Integer, ForeignKey('public.usuarios.id'), nullable=False)
    usuario_nome         = Column(String(150), nullable=False)
    campo_alterado       = Column(String(60), nullable=False)
    valor_anterior       = Column(Text)
    valor_novo           = Column(Text)
    confirmou_alerta_60  = Column(Boolean, nullable=False, default=False)
    alterado_em          = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<LogAuditoriaEras auditoria={self.id_auditoria} campo={self.campo_alterado}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_log_auditoria_eras.py
# =========================================================
