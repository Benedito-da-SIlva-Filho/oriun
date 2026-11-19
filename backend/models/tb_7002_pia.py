# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_7002_pia.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-09-07 19:05 -03
# ATUALIZADO EM: 2026-09-07 19:05 -03
# VERSAO:       1.0.0
#
# DESCRICAO:
#     Model da tabela tb_7002_pia - Planilha de Identificacao
#     Individual de Animais (Anexo XXIII, documento oficial que
#     segue para a Certificadora e o MAPA). Tabela POR-PRODUTOR
#     (Schema-por-Produtor), SEM __table_args__ de schema.
#
#     1 LINHA POR ANIMAL POR PIA GERADA - nasce automaticamente ao
#     concluir a Brincagem Sequencial de uma GTA (1 PIA por GTA
#     brincada, decisao de Benedito, Sessao 047). numero_pia e
#     sequencial POR PROPRIEDADE (reinicia a cada fazenda) -
#     calculado como MAX(numero_pia) + 1 daquela Propriedade no
#     momento da geracao.
#
#     Dados congelados no momento da geracao (documento oficial -
#     nao deve mudar retroativamente mesmo se o cadastro do animal
#     for corrigido depois). raca_codigo guarda o CODIGO de 2
#     letras (ex.: "NE"), igual aparece impresso no documento real -
#     nao o nome completo da raca.
#
#     id_gta e id_animal NAO sao Foreign Keys de banco de verdade -
#     mesmo motivo/padrao ja aplicado em tb_2017_movimentacoes.py
#     (tb_2001 faz DELETE fisico do animal no evento de saida;
#     manter referencia solta evita travar esse DELETE).
#
#     Demais dados do documento (Fabricante, Produtor, CNPJ,
#     Propriedade, Endereco, Cod. ERAS) NAO viram coluna aqui -
#     sao buscados nos cadastros ja existentes na hora de montar o
#     PDF, mesmo padrao ja usado nos demais documentos (Cancelamento
#     de Brincos, etc.).
#
#     v1.0.0: Criacao do modulo (Sessao 047), a partir do documento
#             real (Relatorio_PIA.pdf, Anexo XXIII) e do alinhamento
#             de campos fechado com Benedito.
# =========================================================

from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# ENUM ja existente no banco (create_type=False: apenas
# referencia, nunca tenta recriar) - MESMO de tb_2001_entradas.py.
# -------------------------------------------------------
sexo_enum = PgEnum('MACHO', 'FEMEA', name='sexo_enum', schema='public', create_type=False)


# -------------------------------------------------------
# Model Pia
# Espelha a tabela tb_7002_pia (schema do Produtor)
# -------------------------------------------------------
class Pia(Base):
    __tablename__ = 'tb_7002_pia'

    id                  = Column(Integer, primary_key=True)
    id_propriedade      = Column(Integer, nullable=False)
    numero_pia          = Column(Integer, nullable=False)  # sequencial por Propriedade

    id_gta              = Column(Integer)  # SEM ForeignKey - ver DESCRICAO

    sisbov              = Column(String(15), nullable=False)
    manejo              = Column(String(6))
    nascimento          = Column(Date)
    idade_meses         = Column(Integer)  # calculada na Data de Identificacao
    sexo                = Column(sexo_enum)
    raca_codigo         = Column(String(2))  # codigo de 2 letras, ex: "NE"
    motivo              = Column(String(20), nullable=False)  # ex: "ENTRADA"
    data_identificacao  = Column(Date, nullable=False)  # = data da Brincagem

    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em       = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Pia {self.numero_pia} - {self.sisbov}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_7002_pia.py
# =========================================================