# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_3007_brincos_entrada.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-17 10:01 -03
# ATUALIZADO EM: 2026-10-10 16:40 -03
# VERSAO: 1.2.0
#
# DESCRICAO:
#     Model da tabela tb_3007_brincos_entrada.
#     Lote de entrada de brincos (compra junto ao Fabricante,
#     identificado por Nota Fiscal), com faixa de codigos
#     (codigo_inicial a codigo_final) e controle de saldo
#     (qtde_entrada - qtde_saida = saldo).
#
#     Vive dentro do schema do Produtor (Schema-por-Produtor,
#     conforme classificacao fechada na Sessao 018) - cada
#     Produtor controla seu proprio estoque de brincos.
#
#     E o primeiro elo da cadeia de rastreabilidade:
#     1021 (Fabricantes) -> 3007 (este) -> gera -> 7017
#     -> atualizado por -> 5001 (Brincagem) -> 2012 (Com. Entrada)
#     -> carrega definitivamente em -> 2001 (Animal).
#
#     id_fabricante: FK para tb_1021_fabricantes_brincos (schema
#     publico) - de qual Fabricante veio este lote de brincos.
#
#     id_responsavel: FK para usuarios - o usuario logado que fez
#     o input desta entrada de brincos no sistema (nao e o
#     responsavel pelo recebimento fisico do lote, e sim quem
#     lancou o registro). Confirmado com Benedito em 2026-07-17.
#
#     id_propriedade (obrigatorio): mesma logica ja usada em
#     Gta - diferencia, dentro do schema do Produtor, para qual
#     das Propriedades dele este lote de brincos pertence.
#
#     cpf_produtor (NOVO v1.1.0): CPF/CNPJ do Produtor que fez a
#     solicitacao deste lote de brincos, selecionado na tela de
#     Entrada de Brincos. Necessario porque id_propriedade sozinho
#     NAO basta para identificar o Produtor responsavel - uma
#     mesma Propriedade pode ter mais de um Produtor/proprietario
#     vinculado (caso real visto no GERAS: Fazenda Olho D'Agua com
#     Maria Angelica Maia Cintra e Oswaldo Valente Cintra, ambos
#     na mesma Propriedade). Este mesmo cpf_produtor e replicado
#     em cada linha gerada em tb_7017_entrada_brincos_rfid na hora
#     da gravacao simultanea (ver DESCRICAO de tb_7017), garantindo
#     que os dois fiquem sincronizados desde a origem, sem precisar
#     de JOIN complexo para descobrir de qual Produtor e o lote/o
#     brinco individual. Decisao fechada com Benedito, 31/08/2026.
#
#     Nao possui coluna id_produtor - isolamento garantido pelo
#     proprio schema do Produtor (Schema-por-Produtor, Sessao 018).
#     Nao possui campo de "lote de origem" - esta tabela E o lote
#     de entrada, a referencia so existe de fora para dentro
#     (ver tb_3008_brincos_saida.id_lote_entrada e
#     tb_7017_entrada_brincos_rfid.id_lote_entrada).
#
#     v1.0.0: Criacao do modulo (Sessao 019), a partir da
#             estrutura real de tb_3007_brincos_entrada
#             conferida no pgAdmin (17 colunas), ja sem coluna
#             id_produtor (removida na Sessao 018).
#     v1.1.0: Sessao 042 (31/08/2026, 18:32 -03) - Fechamento do
#             desenho de dados da tela de Entrada de Brincos, com
#             Benedito. Adicionadas 3 colunas novas, ja aplicadas
#             via ALTER TABLE (bloco DO $$ em loop) nos 4 schemas
#             de Produtor existentes (produtor_00001, 00004, 00005,
#             00010):
#               (1) data_nf (Date) - Data da Nota Fiscal. Regra de
#                   negocio: deve ser maior ou igual a
#                   solicitacao_data.
#               (2) impressao_pia (Date) - Data de Impressao da
#                   PIA (Planilha Individual de Animais). Regra de
#                   negocio: deve ser maior ou igual a
#                   data_fabricacao.
#               (3) cpf_produtor (String(18)) - ver DESCRICAO acima.
#             Datas de referencia ja existentes na tabela mantidas
#             sem alteracao: solicitacao_data, data_fabricacao.
#             Regra de negocio confirmada por Benedito: data_fabricacao
#             deve ser ESTRITAMENTE maior que solicitacao_data (nao
#             pode ser igual).
#     v1.2.0: Sessao 093 (10/10/2026, 16:40 -03) - CORRECAO: nota_fiscal de
#             String(6) para String(10). O banco dos 4 produtores existentes
#             ja estava com 10 (ajustado a mao, o Model ficou para tras); o
#             produtor novo (teste id 11) nasceu com 6 pelo Model. Nada
#             a fazer nos schemas existentes - so o Model e o produtor novo.
# =========================================================

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model BrincoEntrada
# Espelha a tabela tb_3007_brincos_entrada no PostgreSQL
# -------------------------------------------------------
class BrincoEntrada(Base):
    __tablename__ = 'tb_3007_brincos_entrada'

    # Identificacao
    id                   = Column(Integer, primary_key=True)

    # Propriedade do Produtor (dentro do schema) a que este lote
    # pertence - mesma logica de Gta.id_propriedade
    id_propriedade       = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    propriedade          = relationship('Propriedade', foreign_keys=[id_propriedade])

    # CPF/CNPJ do Produtor que solicitou este lote (ver DESCRICAO
    # v1.1.0 acima) - replicado em cada linha de tb_7017 gerada
    # a partir deste lote.
    cpf_produtor         = Column(String(18))

    # Fabricante (schema publico) de quem veio o lote
    id_fabricante        = Column(Integer, ForeignKey('public.tb_1021_fabricantes_brincos.id'), nullable=False)
    fabricante           = relationship('Fabricante', foreign_keys=[id_fabricante])

    # Usuario logado que fez o input desta entrada (nao e o
    # responsavel pelo recebimento fisico)
    id_responsavel        = Column(Integer, ForeignKey('public.usuarios.id'))
    responsavel           = relationship('Usuario', foreign_keys=[id_responsavel])

    # Faixa de codigos dos brincos deste lote
    sequencia             = Column(Integer)
    codigo_inicial         = Column(String(15), nullable=False)
    codigo_final           = Column(String(15), nullable=False)

    # Documento de compra
    nota_fiscal            = Column(String(10))
    # Data da Nota Fiscal (NOVO v1.1.0) - regra: >= solicitacao_data
    data_nf                 = Column(Date)

    # Controle de estoque (saldo = qtde_entrada - qtde_saida)
    qtde_entrada           = Column(Integer, nullable=False)
    data_entrada            = Column(Date)
    qtde_saida              = Column(Integer, nullable=False, default=0)
    saldo                   = Column(Integer, nullable=False, default=0)

    # Dados da solicitacao junto ao Fabricante
    solicitacao_nro          = Column(Integer)
    solicitacao_data          = Column(Date)
    data_fabricacao            = Column(Date)
    # Data de Impressao da PIA (NOVO v1.1.0) - regra: >= data_fabricacao
    impressao_pia               = Column(Date)
    total_caixas                = Column(Integer)

    # Controle de datas
    criado_em                    = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em                 = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<BrincoEntrada {self.codigo_inicial}-{self.codigo_final} (NF {self.nota_fiscal})>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_3007_brincos_entrada.py
# =========================================================