# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_parceiros_propriedades.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-15 10:44 -03
# ATUALIZADO EM: 2026-07-28 19:22 -03
# VERSAO: 1.3.0
#
# DESCRICAO:
#     Model da tabela tb_parceiros_propriedades.
#     Tabela filha de tb_parceiros (1:N) - cada Parceiro
#     (mesmo CPF/CNPJ) pode ter varias propriedades, cada
#     uma com seu proprio Codigo MAPA. Sem correspondente no
#     legado GERAS, criada na Sessao 16 a partir dos dados
#     ricos de Procedencia/Destino de uma e-GTA real
#     (IAGRO/MS).
#
#     Usada tanto na leitura de GTA (identificar de qual
#     propriedade do Parceiro vieram/foram os animais) quanto
#     na tela de conferencia humana obrigatoria (Secao 5 do
#     Diario 016) - nenhum vinculo Parceiro/Propriedade e
#     criado automaticamente pelo sistema.
#
#     v1.0.0: Criacao do modulo (Sessao 17), a partir da
#             estrutura real de tb_parceiros_propriedades
#             conferida no pgAdmin (12 colunas).
#     v1.1.0: Sessao 17 (continuacao) - Decisao arquitetural:
#             banco unico + RLS por produtor (schema-por-produtor
#             descartado). Adicionada coluna id_produtor direta.
#     v1.2.0: Sessao 018 - Decisao arquitetural revertida: RLS
#             descartado, Schema-por-Produtor confirmado como
#             modelo definitivo. Coluna id_produtor removida -
#             era suporte tecnico exclusivo do RLS (filtro de
#             linha dentro de uma tabela unica). No modelo de
#             Schema-por-Produtor o isolamento ja e fisico (a
#             tabela inteira mora dentro do schema do Produtor
#             dono) - manter a coluna seria redundante e um
#             risco de dessincronia (linha migrada de schema sem
#             atualizar o id_produtor).
#     v1.3.0: Sessao 025 - codigo_mapa alterado de NOT NULL para
#             NULLABLE. Motivo: Sessao 024 confirmou que Codigo
#             MAPA so existe em propriedades ERAS/SISBOV -
#             propriedades comuns/mercado interno nunca tiveram
#             esse codigo. Com a coluna obrigatoria, era
#             impossivel cadastrar um Parceiro comum (sem
#             SISBOV) na tela de leitura de GTA. Agora com o
#             mesmo tratamento de insc_estadual (ja nullable).
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model ParceiroPropriedades
# Espelha a tabela tb_parceiros_propriedades no PostgreSQL
# -------------------------------------------------------
class ParceiroPropriedades(Base):
    __tablename__ = 'tb_parceiros_propriedades'

    # Identificacao
    id                  = Column(Integer, primary_key=True)

    # Vinculo obrigatorio com o Parceiro dono desta propriedade.
    # Isolamento entre Produtores diferentes e garantido pelo
    # schema (Schema-por-Produtor) - nao precisa de coluna
    # id_produtor aqui, ver changelog v1.2.0.
    id_parceiro         = Column(Integer, ForeignKey('tb_parceiros.id'), nullable=False)
    parceiro            = relationship('Parceiro', foreign_keys=[id_parceiro], backref='propriedades')

    # Dados da propriedade externa (Procedencia/Destino da e-GTA)
    estabelecimento     = Column(String(150), nullable=False)
    # codigo_mapa: NULLABLE desde a v1.3.0 (Sessao 025) - nem
    # toda propriedade externa tem esse codigo (so ERAS/SISBOV).
    codigo_mapa         = Column(String(20))
    insc_estadual       = Column(String(20))

    # Localizacao
    municipio_codigo    = Column(String(10))
    municipio_nome      = Column(String(100))
    uf                  = Column(String(2))
    regiao              = Column(String(50))

    # Controle de status
    ativo               = Column(Boolean, nullable=False, default=True)

    # Controle de datas
    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em       = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<ParceiroPropriedades {self.estabelecimento} ({self.codigo_mapa})>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_parceiros_propriedades.py
# =========================================================