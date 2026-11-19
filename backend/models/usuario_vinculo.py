# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\usuario_vinculo.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-08-03 16:55 -03
# ATUALIZADO EM: 2026-08-03 16:55 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela usuario_vinculo.
#     Representa o vinculo de acesso de um Usuario (perfil
#     PRODUTOR) a um Produtor especifico - define ONDE ele
#     atua e QUAL Cargo (nivel de acesso) ele tem naquele
#     vinculo.
#
#     Um Usuario pode ter mais de um vinculo simultaneo (ex.:
#     um colaborador que atende varios Produtores/Propriedades
#     ao mesmo tempo). O vinculo padrao e por id_produtor (vale
#     para todas as Propriedades daquele Produtor); o campo
#     id_propriedade_produtor e opcional e serve so para a
#     excecao pontual em que o Cargo do colaborador precisa
#     variar entre Propriedades do mesmo Produtor - quando
#     preenchido, esse vinculo especifico prevalece sobre o
#     vinculo geral do Produtor para aquela Propriedade.
#
#     Perfis CONSISTE e CERTIFICADORA NAO usam esta tabela -
#     sao usuarios da propria plataforma, sem vinculo com
#     Produtor/Propriedade.
#
#     Cargo e um ENUM fechado (CHECK constraint), fixado pela
#     Consiste - Produtor nao cria cargo novo (evitaria cargos
#     "vazando" entre Produtores diferentes, ja que o catalogo
#     de cargos e compartilhado/publico):
#         TITULAR                  - dono/familia, acesso total
#         ADMINISTRADOR             - gerente contratado de confianca,
#                                     acesso total
#         ADMINISTRATIVO            - escritorio, acesso total exceto
#                                     Financeiro
#         CAMPEIRO                  - consultas + brincagem (leitura
#                                     de brincos/RFID, manejo)
#         GERENTE_CAPATAZ           - sem acesso definido ainda
#         VETERINARIO_ZOOTECNISTA   - sem acesso definido ainda
#         AUXILIAR                  - sem acesso definido ainda
#
#     Vigencia do vinculo por data_inicio/data_fim (mesmo padrao
#     ja usado em propriedade_produtor e propriedade_proprietario) -
#     data_fim nulo = vinculo ativo.
#
#     v1.0.0: Criacao do modulo. Sessao de definicao do modelo
#             de acesso do Produtor/Equipe (substitui os campos
#             fixos usuarios.cargo e usuarios.id_produtor, que
#             nao suportavam um mesmo colaborador atendendo mais
#             de um Produtor, nem Cargo variando por Propriedade).
# =========================================================

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Cargos validos (ENUM fechado, aplicado via CHECK constraint
# no banco). Mantido aqui tambem como lista Python, para uso
# em validacao no backend (dropdown do formulario, etc.).
# -------------------------------------------------------
CARGOS_VALIDOS = [
    'TITULAR',
    'ADMINISTRADOR',
    'ADMINISTRATIVO',
    'CAMPEIRO',
    'GERENTE_CAPATAZ',
    'VETERINARIO_ZOOTECNISTA',
    'AUXILIAR',
]


# -------------------------------------------------------
# Model UsuarioVinculo
# Espelha a tabela usuario_vinculo no PostgreSQL
# -------------------------------------------------------
class UsuarioVinculo(Base):
    __tablename__ = 'usuario_vinculo'
    __table_args__ = (
        CheckConstraint(
            "cargo IN ('TITULAR','ADMINISTRADOR','ADMINISTRATIVO','CAMPEIRO',"
            "'GERENTE_CAPATAZ','VETERINARIO_ZOOTECNISTA','AUXILIAR')",
            name='ck_usuario_vinculo_cargo'
        ),
        {'schema': 'public'},
    )

    # Identificacao e vinculo
    id                       = Column(Integer, primary_key=True)
    id_usuario               = Column(Integer, ForeignKey('public.usuarios.id'), nullable=False)
    id_produtor              = Column(Integer, ForeignKey('public.produtores.id'), nullable=False)

    # Opcional - so preenchido na excecao pontual em que o Cargo
    # varia por Propriedade dentro do mesmo Produtor (ver
    # docstring do modulo). Quando presente, este vinculo
    # especifico prevalece sobre o vinculo geral do Produtor
    # para aquela Propriedade.
    id_propriedade_produtor  = Column(Integer, ForeignKey('public.propriedade_produtor.id'), nullable=True)

    # Nivel de acesso deste vinculo (ver CARGOS_VALIDOS acima)
    cargo                    = Column(String(30), nullable=False)

    # Vigencia do vinculo - data_fim nulo = vinculo ativo
    data_inicio              = Column(Date, nullable=False)
    data_fim                 = Column(Date, nullable=True)

    # Relacionamentos
    usuario                  = relationship('Usuario', foreign_keys=[id_usuario], backref='vinculos')
    produtor                 = relationship('Produtor', foreign_keys=[id_produtor], backref='vinculos_usuario')
    propriedade_produtor     = relationship('PropriedadeProdutor', foreign_keys=[id_propriedade_produtor])

    # Controle de datas
    criado_em                = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em             = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<UsuarioVinculo usuario={self.id_usuario} produtor={self.id_produtor} cargo={self.cargo}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\usuario_vinculo.py
# =========================================================