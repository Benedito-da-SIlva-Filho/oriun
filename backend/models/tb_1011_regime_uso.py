# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_1011_regime_uso.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-23 12:13 -03
# ATUALIZADO EM: 2026-07-23 12:13 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_1011_regime_uso.
#     Catalogo de Regime de Uso (GR1011 do GERAS) - descreve
#     a forma de vinculo do Produtor com a Propriedade
#     (Proprietario Unico, Arrendatario, Posseiro, etc.).
#     Schema publico (catalogo compartilhado por todos os
#     Produtores - nao entra nas tabelas do Schema-por-Produtor).
#
#     Substitui o campo livre propriedade_produtor.tipo_vinculo
#     (String(30) sem validacao) por uma FK de verdade,
#     decidido na Sessao de Parelhamento Orion x GERAS
#     (pasta 1-Cadastros).
#
#     v1.0.0: Criacao do modulo. Campo definicao (Text,
#             nullable) guarda o texto explicativo do GERAS,
#             usado como tooltip/ajuda na tela do Orion.
# =========================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model RegimeUso
# Espelha a tabela tb_1011_regime_uso no PostgreSQL
# -------------------------------------------------------
class RegimeUso(Base):
    __tablename__ = 'tb_1011_regime_uso'
    __table_args__ = {'schema': 'public'}

    id              = Column(Integer, primary_key=True)

    # Codigo interno (usado em regras de negocio, se necessario)
    codigo          = Column(String(30), nullable=False, unique=True)

    # Label curto para exibicao na tela (dropdown)
    descricao       = Column(String(100), nullable=False)

    # Texto explicativo do GERAS, usado como tooltip/ajuda
    # na tela do Orion. Nulo para itens sem definicao no
    # export original (Condomino, Comodatario).
    definicao       = Column(Text)

    # Permite desativar um regime sem apagar historico
    ativo           = Column(Boolean, nullable=False, default=True)

    # Controle de datas
    criado_em       = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em   = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<RegimeUso {self.codigo}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_1011_regime_uso.py
# =========================================================