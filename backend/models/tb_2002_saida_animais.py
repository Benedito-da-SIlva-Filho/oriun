# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_2002_saida_animais.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-16 14:16 -03
# ATUALIZADO EM: 2026-11-13 17:55 -03
# VERSAO: 1.3.0
#
# DESCRICAO:
#     Model da tabela tb_2002_saida_animais - o animal DEPOIS da saida
#     (Abate, Venda, Morte ou Transferencia). Tabela POR-PRODUTOR.
#
#     Gravada quando o Comunicado de Saida e gerado; ao mesmo tempo o
#     animal sai de tb_2001 e entra uma linha nova em tb_2017.
#
#     SUBSTITUICAO apos o Comunicado (decisao de Benedito, Sessao 098):
#     NADA e apagado. O animal lido que nao embarcou fica marcado
#     (substituido = True) e volta ao rebanho por uma linha NOVA em
#     tb_2001; o que embarcou entra como nova saida. O historico fica
#     todo aqui, para o blockchain apontar sempre para o evento original.
#
#     Campos de Morte (tipo_morte, id_motivo_morte, destino_morte) so sao
#     preenchidos quando tipo_saida = MORTE (pacote da Morte, depois do
#     Abate). Listas fixas e catalogo seguem o padrao do MAPA.
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
#     v1.3.0: Sessao 123 (2026-11-13 17:55 -03) - AUDITORIA ETAPA 5: model declara os 2 indices unicos parciais que ja existem no banco (uq_tb_2002_animal_valido e uq_tb_2002_embarque_valido, so onde substituido = false). So documenta. REVERSAO: .bak_antes_etapa5.
# =========================================================

from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, Boolean, Numeric, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from .certificadora import Base


# ENUM ja existente no banco (create_type=False: so referencia).
sexo_enum = PgEnum('MACHO', 'FEMEA', name='sexo_enum', schema='public', create_type=False)


# -------------------------------------------------------
# Model SaidaAnimal - espelha a tabela tb_2002_saida_animais (schema do Produtor)
# -------------------------------------------------------
class SaidaAnimal(Base):
    __tablename__ = 'tb_2002_saida_animais'
    # v1.3.0 - uma entrada = uma saida valida (Troca de Comunicado deixa a linha 'substituido' de historico: nao conta). Sem schema fixo.
    __table_args__ = (
        Index('uq_tb_2002_animal_valido', 'id_animal', unique=True, postgresql_where=text('id_animal IS NOT NULL AND substituido = false')),
        Index('uq_tb_2002_embarque_valido', 'id_embarque', unique=True, postgresql_where=text('id_embarque IS NOT NULL AND substituido = false')),
    )

    id                         = Column(Integer, primary_key=True)
    id_propriedade             = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    id_animal                  = Column(Integer)  # id que o animal tinha em tb_2001 - SEM ForeignKey
    id_embarque                = Column(Integer, ForeignKey('tb_2020_embarque.id'))  # leitura de origem (vazio na Morte)
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
    tipo_saida                 = Column(String(20), nullable=False)  # ABATE / VENDA / MORTE / TRANSFER (CHECK no banco)
    gta_saida                  = Column(String(10))
    gta_saida_emissao          = Column(Date)
    gta_saida_validade         = Column(Date)
    gta_saida_animais          = Column(Integer)
    id_gta                     = Column(Integer, ForeignKey('tb_4001_gta.id'))
    id_frigorifico             = Column(Integer, ForeignKey('public.tb_frigorificos.id'))
    destino_propriedade        = Column(String(150))
    destino_cpf_cnpj           = Column(String(18))
    data_embarque              = Column(Date)  # dia da leitura no brete
    data_saida                 = Column(Date, nullable=False)  # dia em que o animal saiu da propriedade (informada no escritorio)
    numero_comunicado          = Column(Integer)
    lote_saida                 = Column(String(30))
    peso_saida                 = Column(Numeric(10, 2))
    elemento                   = Column(String(10))  # BOTTON / BRINCO, so quando o brete escolhe; vazio = tem os dois (CHECK no banco)
    tipo_morte                 = Column(String(15))  # ACIDENTAL / DESLIGADO / NATURAL / SACRIFICIO (padrao MAPA, CHECK no banco)
    id_motivo_morte            = Column(Integer, ForeignKey('public.tb_1007_motivo_mortes.id'))  # Causa Mortis (catalogo MAPA)
    destino_morte              = Column(String(15))  # CREMACAO / ENTERRAMENTO / OUTROS (padrao MAPA, CHECK no banco)
    id_com_morte               = Column(Integer, ForeignKey('tb_2013_com_morte.id'))  # s111 - Controle Interno (MRT) do lancamento da Morte; vazio nas outras saidas
    aceite_fora_liberacao      = Column(Boolean, nullable=False, default=False)  # Aviso A: "Estou ciente e assumo" (animal fora da Liberacao para Abate)
    aceite_fora_liberacao_por  = Column(Integer)  # id do usuario que aceitou
    aceite_fora_liberacao_em   = Column(DateTime)
    aceite_era_0_12            = Column(Boolean, nullable=False, default=False)  # Aviso B: "Estou ciente" (animal na ERAS 0 a 12 meses)
    aceite_era_0_12_por        = Column(Integer)  # id do usuario que aceitou
    aceite_era_0_12_em         = Column(DateTime)
    substituido                = Column(Boolean, nullable=False, default=False)  # True = animal lido que NAO embarcou; fica no historico (nunca e apagado)
    substituido_em             = Column(DateTime)
    id_usuario_substituicao    = Column(Integer)
    sisbov_substituto          = Column(String(15))  # numero do animal que embarcou no lugar
    criado_em                  = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em              = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<SaidaAnimal {self.sisbov}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_2002_saida_animais.py
# =========================================================
