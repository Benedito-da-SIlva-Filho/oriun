# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_auditoria_eras.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-07 12:05 -03
# ATUALIZADO EM: 2026-10-07 12:05 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_auditoria_eras (schema public).
#     Uma linha por VISTORIA/AUDITORIA feita numa Propriedade que
#     tem codigo ERAS. O historico e da Propriedade (nao de um
#     Produtor): dois Produtores da mesma fazenda veem o mesmo
#     historico. Nunca se apaga uma vistoria; correcoes ficam
#     registradas em tb_log_auditoria_eras.
#
#     Campos obrigatorios: data da vistoria, veredito da
#     Certificadora (CONFORME ou NAO_CONFORME), nome do
#     vistoriador/auditor e proxima data (o vistoriador precisa
#     saber quando volta, e o aviso do Home depende dela).
#     Observacao do auditor e opcional.
#
#     id_usuario / usuario_nome: quem registrou. O nome e um
#     "retrato" do momento (mesmo padrao de tb_log_alteracao_gta).
#
#     v1.0.0: Criacao do modulo (Sessao 089, 07/10/2026, 12:05 -03),
#             a partir de Tabelas/criar_tb_auditoria_eras.sql.
# =========================================================

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model AuditoriaEras
# Espelha a tabela tb_auditoria_eras no PostgreSQL
# -------------------------------------------------------
class AuditoriaEras(Base):
    __tablename__ = 'tb_auditoria_eras'
    __table_args__ = {'schema': 'public'}

    id              = Column(Integer, primary_key=True)
    id_propriedade  = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)

    data_vistoria   = Column(Date, nullable=False)
    veredito        = Column(String(12), nullable=False)    # CONFORME ou NAO_CONFORME
    vistoriador     = Column(String(100), nullable=False)
    proxima_data    = Column(Date, nullable=False)
    observacao      = Column(Text)

    id_usuario      = Column(Integer, ForeignKey('public.usuarios.id'), nullable=False)
    usuario_nome    = Column(String(150), nullable=False)
    criado_em       = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em   = Column(DateTime)                      # vazio ate a 1a correcao

    def __repr__(self):
        return f'<AuditoriaEras propriedade={self.id_propriedade} data={self.data_vistoria}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_auditoria_eras.py
# =========================================================
