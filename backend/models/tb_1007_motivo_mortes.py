# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_1007_motivo_mortes.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-23 12:13 -03
# ATUALIZADO EM: 2026-07-23 12:13 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_1007_motivo_mortes.
#     Catalogo de Motivos de Morte (GR1007 do GERAS), com
#     categoria fixa (ABATE/NATURAL/SACRIFICIO) via ENUM
#     nativo do Postgres. Schema publico (catalogo
#     compartilhado por todos os Produtores).
#
#     Usado apenas na tela de tipo_movimento MORTE (Saida).
#     Abate para Frigorifico e um fluxo separado (GTA com
#     Frigorifico vinculado) e nao usa este catalogo, mesmo
#     quando a categoria do motivo e ABATE - confirmado com
#     o Navigator na Sessao de Parelhamento Orion x GERAS.
#
#     Motivo em tabela (nao enum), diferente da categoria:
#     o MAPA pode incluir novos motivos ou inativar
#     existentes ao longo do tempo.
#
#     v1.0.0: Criacao do modulo.
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from datetime import datetime
from .certificadora import Base


# ENUM nativo do Postgres, ja criado no banco via SQL
# (create_type=False - nao deixar o SQLAlchemy tentar criar
# de novo no boot).
categoria_motivo_morte_enum = PgEnum(
    'ABATE', 'NATURAL', 'SACRIFICIO',
    name='categoria_motivo_morte_enum',
    schema='public',
    create_type=False
)


# -------------------------------------------------------
# Model MotivoMorte
# Espelha a tabela tb_1007_motivo_mortes no PostgreSQL
# -------------------------------------------------------
class MotivoMorte(Base):
    __tablename__ = 'tb_1007_motivo_mortes'
    __table_args__ = {'schema': 'public'}

    id              = Column(Integer, primary_key=True)

    # Codigo original do GERAS (001-044), preservado para
    # rastreio/auditoria com o legado.
    codigo_geras    = Column(String(3), nullable=False, unique=True)

    descricao       = Column(String(150), nullable=False)

    # ABATE / NATURAL / SACRIFICIO - informativo, sem regra
    # de negocio amarrada (o fluxo de Abate para Frigorifico
    # e independente deste catalogo).
    categoria       = Column(categoria_motivo_morte_enum, nullable=False)

    # Permite inativar um motivo (MAPA pode descontinuar)
    # sem apagar historico
    ativo           = Column(Boolean, nullable=False, default=True)

    # Controle de datas
    criado_em       = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em   = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<MotivoMorte {self.codigo_geras} - {self.descricao}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_1007_motivo_mortes.py
# =========================================================