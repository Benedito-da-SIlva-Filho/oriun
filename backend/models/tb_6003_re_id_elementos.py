# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_6003_re_id_elementos.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-25 11:16 -03
# ATUALIZADO EM: 2026-07-25 11:16 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_6003_re_id_elementos.
#     Cabecalho do pedido de Reidentificacao por Elementos
#     (GR6003 do GERAS, pasta 6-Formularios) - reposicao fisica
#     de Brinco ou Botton danificado, mantendo o mesmo SISBOV
#     (identidade preservada, sem Antigo/Novo).
#
#     Vive no SCHEMA DO PRODUTOR (Schema-por-Produtor), nao no
#     schema publico - mesmo raciocinio ja validado em
#     tb_5001_brincagem: id_propriedade diferencia, dentro do
#     mesmo schema, para qual Propriedade daquele Produtor
#     pertence cada pedido.
#
#     Campo qtde_animais: informado pelo usuario, funciona como
#     trava de conferencia manual (nao e um status automatico) -
#     o usuario compara mentalmente/na tela contra a contagem de
#     itens ja lancados em tb_6004_re_id_elementos_itens, evitando
#     "esquecer" de lancar um brinco. Nao existe coluna de status
#     ABERTO/ENCERRADO - decisao consciente de Benedito.
#
#     Campo data_solicitacao: informada pelo usuario, pode ser
#     retroativa (diferente de criado_em, que e o timestamp real
#     de gravacao no banco). A data de impressao do documento NAO
#     e gravada em lugar nenhum - calculada em tempo real (NOW())
#     toda vez que o PDF e gerado, mesmo padrao ja usado nos
#     demais relatorios do sistema.
#
#     Campo elementos usa o ENUM elementos_reidentificacao_enum
#     (schema publico, script SQL proprio) - 3 valores estaveis
#     (Brinco/Botton/Brinco+Botton), decisao por ENUM em vez de
#     tabela catalogo por nao dependerem de ato normativo do MAPA.
#
#     "Codigo Reimpressao" do legado = o proprio id (SERIAL) desta
#     tabela, sem coluna duplicada - confirmado por Benedito.
#
#     v1.0.0: Criacao do modulo.
# =========================================================

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# ENUM nativo do Postgres, ja criado no banco via SQL
# (create_type=False - nao deixar o SQLAlchemy tentar criar
# de novo no boot).
elementos_reidentificacao_enum = PgEnum(
    'BRINCO', 'BOTTON', 'BRINCO_BOTTON',
    name='elementos_reidentificacao_enum',
    schema='public',
    create_type=False
)


# -------------------------------------------------------
# Model ReIdElementos
# Espelha a tabela tb_6003_re_id_elementos no PostgreSQL
# -------------------------------------------------------
class ReIdElementos(Base):
    __tablename__ = 'tb_6003_re_id_elementos'

    # Identificacao - tambem cumpre o papel de "Codigo Reimpressao"
    id                  = Column(Integer, primary_key=True)

    # Lado interno (Propriedade dona do pedido). Isolamento entre
    # Produtores diferentes e garantido pelo schema
    # (Schema-por-Produtor) - id_propriedade diferencia entre as
    # varias Propriedades que um mesmo Produtor pode ter.
    id_propriedade      = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    propriedade         = relationship('Propriedade', foreign_keys=[id_propriedade])

    # Qual elemento fisico esta sendo reposto
    elementos           = Column(elementos_reidentificacao_enum, nullable=False)

    # Trava de conferencia manual do usuario (nao e status automatico)
    qtde_animais        = Column(Integer, nullable=False)

    # Texto livre, informado pelo usuario (ex.: "PERDEU")
    motivo              = Column(String(200), nullable=False)

    # Informada pelo usuario, pode ser retroativa
    data_solicitacao    = Column(Date, nullable=False)

    # Controle de datas (gravacao real no banco)
    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em       = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<ReIdElementos {self.id} elementos={self.elementos}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_6003_re_id_elementos.py
# =========================================================