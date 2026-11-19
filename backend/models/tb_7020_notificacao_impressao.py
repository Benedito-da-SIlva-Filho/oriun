# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_7020_notificacao_impressao.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-02 09:00 -03
# ATUALIZADO EM: 2026-10-02 09:00 -03
# VERSAO:       1.0.0
#
# DESCRICAO:
#     Model da tabela tb_7020_notificacao_impressao - registra que a
#     NOTIFICACAO DE NASCIMENTO (NAS, tb_4001_gta) ja foi IMPRESSA
#     (Certificadora avisada). Uma linha por Notificacao (id_gta
#     UNICO): a existencia da linha e o que TRAVA o Desfazer
#     (backend/utils/log_operacoes.py v1.5.0) e muda o botao da lista
#     de "Imprimir" para "Reimprimir" (backend/routers/
#     notificacao_nascimento.py). Tabela POR-PRODUTOR (Schema-por-
#     Produtor): sem schema fixo no Model - resolvido em tempo de
#     execucao por get_db_produtor().
#
#     Script de criacao: Tabelas\8_create_tb_7020_notificacao_
#     impressao.sql.
#
#     v1.0.0: Criacao (Sessao 084, 02/10/2026, 09:00 -03).
# =========================================================

from datetime import datetime

from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey

from .certificadora import Base


class NotificacaoImpressao(Base):
    __tablename__ = 'tb_7020_notificacao_impressao'

    id             = Column(Integer, primary_key=True)
    id_gta         = Column(Integer, ForeignKey('tb_4001_gta.id'), nullable=False, unique=True)
    data_impressao = Column(Date, nullable=False)
    id_usuario     = Column(Integer, nullable=False)
    impresso_em    = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<NotificacaoImpressao gta={self.id_gta} em {self.data_impressao}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_7020_notificacao_impressao.py
# =========================================================
