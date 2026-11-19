# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_2020_embarque.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-16 14:16 -03
# ATUALIZADO EM: 2026-11-13 17:40 -03
# VERSAO:       1.3.0
# v1.3.0: Sessao 123 (2026-11-13 17:40 -03) - AUDITORIA ETAPA 5: model passa a declarar o indice unico parcial uq_tb_2020_sisbov_aberto (sisbov onde sts = false), que ja existe no banco e no onboarding; so documenta (sem mudar comportamento). REVERSAO: .bak_antes_etapa5.
#
# DESCRICAO:
#     Model da tabela tb_2020_embarque - leituras de SAIDA no brete
#     (Abate Leitor/Bastao/Arquivo Texto). Staging de pre-Comunicado de
#     Saida, molde: tb_5001_brincagem. Tabela POR-PRODUTOR.
#
#     A leitura NAO da baixa: o animal so sai de tb_2001 quando o
#     Comunicado de Saida e gerado (sts passa a True). A GTA de saida e
#     lancada no escritorio, por isso id_gta nasce vazio.
#
#     Aceites (decisao de Benedito, Sessao 098): o aviso A (fora da
#     Liberacao para Abate) e o aviso B (ERAS 0 a 12 meses) NAO bloqueiam,
#     mas o "Estou ciente" fica GRAVADO no registro do animal (quem e
#     quando). O texto do aviso e calculado na hora, nao e guardado.
#
#     FKs para o schema public levam o prefixo "public." na string;
#     FKs para tabelas do MESMO schema do Produtor ficam sem prefixo.
#     SEM __table_args__ com schema fixo (schema_translate_map de
#     get_db_produtor). CHECKs e indices vem do script SQL e do
#     onboarding.py, nao deste Model.
#
#     v1.0.0: Criacao (Sessao 098, desenho do Abate fechado com Benedito).
#             SQL: Tabelas\criar_tb_2020_2002_2011_s098.sql
#     v1.1.0: Sessao 098 (16/10/2026, 19:55 -03) - Coluna elemento (BOTTON / BRINCO / vazio).
#             SQL: Tabelas\alterar_tb_2020_2002_elemento_s098.sql
#     v1.2.0: Sessao 107 (28/10/2026, 09:10 -03) - TRANSFERENCIA (pacote 1): nova coluna id_propriedade_destino
#             (Integer, opcional, FK public.propriedades). Guarda a fazenda de destino escolhida na leitura do brete
#             quando tipo_saida = TRANSFER; vazia em Abate, Venda e Morte. Produtor novo recebe a coluna pelo Onboarding
#             (create_all); os existentes pelo SQL. REVERSAO: .bak_antes_s107.
#             SQL: Tabelas\alterar_tb_2020_2011_destino_transfer_s107.sql
# =========================================================

from datetime import datetime
from sqlalchemy import text
from sqlalchemy import Column, Integer, String, Date, Boolean, Time, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from .certificadora import Base


# ENUM ja existente no banco (create_type=False: so referencia).
sexo_enum = PgEnum('MACHO', 'FEMEA', name='sexo_enum', schema='public', create_type=False)


# -------------------------------------------------------
# Model Embarque - espelha a tabela tb_2020_embarque (schema do Produtor)
# -------------------------------------------------------
class Embarque(Base):
    __tablename__ = 'tb_2020_embarque'
    # v1.3.0 - mesmo indice do banco: o mesmo SISBOV nao tem 2 leituras em aberto (sem schema fixo: vale em cada schema de Produtor)
    __table_args__ = (
        Index('uq_tb_2020_sisbov_aberto', 'sisbov', unique=True, postgresql_where=text('sts = false')),
    )

    id                         = Column(Integer, primary_key=True)
    id_propriedade             = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    id_animal                  = Column(Integer)  # id do animal em tb_2001 - SEM ForeignKey (tb_2001 apaga a linha na saida)
    sisbov                     = Column(String(15), nullable=False)
    manejo                     = Column(String(6))
    rfid                       = Column(String(15))
    id_especie                 = Column(Integer, ForeignKey('public.tb_4002_especie.id'))
    sexo                       = Column(sexo_enum)
    nascimento                 = Column(Date)
    eras_dias                  = Column(Integer)
    id_aptidao                 = Column(Integer, ForeignKey('public.tb_4004_aptidao.id'))
    id_raca                    = Column(Integer, ForeignKey('tb_4005_racas.id'))
    cota_hilton                = Column(Boolean, nullable=False, default=False)
    liberacao_abate            = Column(Date)
    gta_entrada                = Column(String(10))
    gta_entrada_emissao        = Column(Date)
    gta_entrada_validade       = Column(Date)
    gta_entrada_animais        = Column(Integer)
    data_inclusao              = Column(Date)
    lote_entrada               = Column(String(30))
    origem_propriedade         = Column(String(150))
    origem_cpf_cnpj            = Column(String(18))
    tipo_saida                 = Column(String(20), nullable=False, default='ABATE')  # ABATE / VENDA / MORTE / TRANSFER (CHECK no banco)
    data_embarque              = Column(Date, nullable=False)  # dia da leitura no brete
    hora_embarque              = Column(Time)
    id_frigorifico             = Column(Integer, ForeignKey('public.tb_frigorificos.id'))
    id_propriedade_destino     = Column(Integer, ForeignKey('public.propriedades.id'))  # so na TRANSFERENCIA: fazenda de destino (mesmo Produtor)
    id_gta                     = Column(Integer, ForeignKey('tb_4001_gta.id'))  # GTA de saida: vazia na leitura, preenchida na Consulta Embarque
    lote_saida                 = Column(String(30))  # em branco quando nao houver lote de saida
    peso_saida                 = Column(Numeric(10, 2))
    elemento                   = Column(String(10))  # BOTTON / BRINCO, so quando o brete escolhe; vazio = tem os dois (CHECK no banco)
    aceite_fora_liberacao      = Column(Boolean, nullable=False, default=False)  # Aviso A: "Estou ciente e assumo" (animal fora da Liberacao para Abate)
    aceite_fora_liberacao_por  = Column(Integer)  # id do usuario que aceitou
    aceite_fora_liberacao_em   = Column(DateTime)
    aceite_era_0_12            = Column(Boolean, nullable=False, default=False)  # Aviso B: "Estou ciente" (animal na ERAS 0 a 12 meses)
    aceite_era_0_12_por        = Column(Integer)  # id do usuario que aceitou
    aceite_era_0_12_em         = Column(DateTime)
    sts                        = Column(Boolean, nullable=False, default=False)  # False = lido, Comunicado ainda nao gerado; True = Comunicado gerado
    numero_comunicado          = Column(Integer)  # SEM ForeignKey, mesmo padrao de tb_5001
    criado_em                  = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em              = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Embarque {self.sisbov}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_2020_embarque.py
# =========================================================
