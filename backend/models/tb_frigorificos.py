# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_frigorificos.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-15 11:10 -03
# ATUALIZADO EM: 2026-07-27 11:20 -03
# VERSAO: 1.2.0, changelog:
#
# DESCRICAO:
#     Model da tabela tb_frigorificos.
#     Cadastro de plantas de abate (Frigorificos). Diferente
#     do Parceiro, cada CNPJ e uma planta distinta, sem
#     tabela filha - Frigorifico nao compra nem vende, ele
#     abate. Sem correspondente direto no legado GERAS via
#     e-GTA, mas equivalente ao cadastro legado "Frigorificos"
#     (11-Insumos, tabela 1119, 14 colunas).
#
#     Estrutura ajustada na Sessao 17 para ficar fiel ao
#     legado GERAS: adicionados endereco detalhado
#     (logradouro/numero/bairro/cep) e os tres codigos de
#     inspecao sanitaria (SIF/SIE/SIM), removidos os campos
#     estabelecimento/codigo_mapa/regiao que tinham vindo por
#     engano do padrao de tb_parceiros_propriedades (tabela
#     ainda estava vazia, sem risco de perda de dado).
#
#     v1.0.0: Criacao do modulo (Sessao 17), a partir da
#             estrutura real de tb_frigorificos conferida no
#             pgAdmin apos o ajuste (17 colunas).
#
#     v1.1.0: Sessao 019 - Adicionado __table_args__ com schema
#             'public' explicito. Mesmo motivo de produtor.py v2.2.0 -
#             Frigorifico e referenciada por FK a partir de
#             tb_4001_gta.id_frigorifico.
#
#     v1.2.0: Sessao 024 - Reaberta a decisao da Sessao 17:
#             codigo_mapa volta ao model, mas agora como campo
#             distinto do SIF/SIE/SIM (nao e selo sanitario, e
#             a chave de registro do estabelecimento industrial
#             junto ao MAPA). Motivado por e-GTA real de Abate,
#             que traz esse codigo no bloco Destino. VARCHAR(15).
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model Frigorifico
# Espelha a tabela tb_frigorificos no PostgreSQL
# -------------------------------------------------------
class Frigorifico(Base):
    __tablename__ = 'tb_frigorificos'
    __table_args__ = {'schema': 'public'}

    # Identificacao
    id                  = Column(Integer, primary_key=True)
    cpf_cnpj            = Column(String(18), nullable=False)
    nome                = Column(String(150), nullable=False)
    insc_estadual       = Column(String(20))

    # Registro federal (distinto dos codigos de inspecao sanitaria abaixo)
    codigo_mapa         = Column(String(15))

    # Endereco detalhado (equivalente a Endereco/Numero/Bairro/CEP do GERAS)
    logradouro          = Column(String(60))
    numero              = Column(String(10))
    bairro              = Column(String(30))
    cep                 = Column(String(9))

    # Localizacao
    municipio_codigo    = Column(String(10))
    municipio_nome      = Column(String(100))
    uf                  = Column(String(2))

    # Codigos de inspecao sanitaria (equivalente a Cod. SIF/SIE/SIM do GERAS)
    cod_sif             = Column(String(7))
    cod_sie             = Column(String(10))
    cod_sim             = Column(String(10))

    # Controle de status
    ativo               = Column(Boolean, nullable=False, default=True)

    # Controle de datas
    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em       = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Frigorifico {self.nome}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_frigorificos.py
# =========================================================