# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_2011_com_saidas.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-16 14:16 -03
# ATUALIZADO EM: 2026-11-05 11:13 -03
# VERSAO:       1.2.0
#
# DESCRICAO:
#     Model da tabela tb_2011_com_saidas - Comunicado de Saida
#     (Anexo XX / XXI). Tabela POR-PRODUTOR. Molde: tb_2012_com_entrada.
#
#     1 LINHA POR GTA dentro de um Comunicado. Numeracao propria
#     (sequencial por Propriedade de origem), igual ao Comunicado de
#     Entrada: o mesmo numero se repete nas linhas das GTAs do mesmo
#     Comunicado, por isso NAO ha indice unico em (propriedade, numero).
#
#     Status nasce ABERTO e passa a IMPRESSO na primeira impressao
#     (impresso_em e id_usuario_impressao provam quem e quando).
#     Liberacao para Abate NAO fica aqui: ja esta no registro do animal.
#
#     FKs para o schema public levam o prefixo "public." na string;
#     FKs para tabelas do MESMO schema do Produtor ficam sem prefixo.
#     SEM __table_args__ com schema fixo (schema_translate_map de
#     get_db_produtor). CHECKs e indices vem do script SQL e do
#     onboarding.py, nao deste Model.
#
#     v1.0.0: Criacao (Sessao 098, desenho do Abate fechado com Benedito).
#             SQL: Tabelas\criar_tb_2020_2002_2011_s098.sql
#     v1.1.0: Sessao 107 (28/10/2026, 09:10 -03) - TRANSFERENCIA (pacote 1): nova coluna id_propriedade_destino
#             (Integer, opcional, FK public.propriedades) = "Destino Propriedade" do GERAS. Preenchida so quando
#             tipo_saida = TRANSFER (o CPF/CNPJ do destino segue em cpf_cnpj_destino). REVERSAO: .bak_antes_s107.
#             SQL: Tabelas\alterar_tb_2020_2011_destino_transfer_s107.sql
#     v1.2.0: Sessao 115 (2026-11-05 11:13 -03) - ALTERACAO DE POSSE (pacote 1): duas colunas novas, so usadas quando
#             tipo_saida = POSSE: motivo_posse (VENDA / HERANCA, CHECK no banco) e justificativa_posse (texto digitado
#             no Gerar Comunicado e impresso no documento). Vazias nos demais tipos. Produtor novo recebe as colunas pelo
#             Onboarding (create_all); os existentes pelo SQL. REVERSAO: .bak_antes_s115_posse.
#             SQL: Tabelas\alterar_posse_s115.sql
# =========================================================

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey
from .certificadora import Base


# -------------------------------------------------------
# Model ComunicadoSaida - espelha a tabela tb_2011_com_saidas (schema do Produtor)
# -------------------------------------------------------
class ComunicadoSaida(Base):
    __tablename__ = 'tb_2011_com_saidas'

    id                         = Column(Integer, primary_key=True)
    id_propriedade_origem      = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    cpf_cnpj_produtor_origem   = Column(String(18))
    numero_comunicado          = Column(Integer, nullable=False)
    tipo_saida                 = Column(String(20), nullable=False)  # ABATE / VENDA / MORTE / TRANSFER / POSSE (CHECK no banco)
    id_gta                     = Column(Integer, ForeignKey('tb_4001_gta.id'))
    gta_numero                 = Column(String(10), nullable=False)
    gta_data_emissao           = Column(Date)
    gta_data_validade          = Column(Date)
    data_saida                 = Column(Date)  # dia em que os animais saem da propriedade
    qtd_animais                = Column(Integer)
    data_inclusao              = Column(Date, nullable=False, default=date.today)
    id_frigorifico             = Column(Integer, ForeignKey('public.tb_frigorificos.id'))
    cpf_cnpj_destino           = Column(String(18))
    id_propriedade_destino     = Column(Integer, ForeignKey('public.propriedades.id'))  # so na TRANSFERENCIA: fazenda de destino (Destino Propriedade do GERAS)
    motivo_posse               = Column(String(10))  # so na POSSE: VENDA / HERANCA (CHECK no banco) - s115
    justificativa_posse        = Column(Text)  # so na POSSE: texto digitado no Gerar Comunicado - s115
    status                     = Column(String(20), nullable=False, default='ABERTO')  # ABERTO -> IMPRESSO
    data_envio                 = Column(Date)
    impresso_em                = Column(DateTime)
    id_usuario_impressao       = Column(Integer)
    criado_em                  = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em              = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<ComunicadoSaida {self.numero_comunicado}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_2011_com_saidas.py
# =========================================================
