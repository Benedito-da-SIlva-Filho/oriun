# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_5003_rejeicoes_brincagem.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-20 10:15 -03
# ATUALIZADO EM: 2026-09-20 10:15 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Model da tabela tb_5003_rejeicoes_brincagem (NOVA, Sessao
#     057) - registra toda tentativa de leitura de brinco
#     BLOQUEADA por duplicidade na tela de Leitura (modulo
#     Brincagem com Leitor, backend/routers/brincagem_leitor.py).
#
#     Gravada quando o SISBOV lido ja existe em QUALQUER uma das
#     3 tabelas consultadas na validacao de duplicidade:
#     tb_2001_entradas, tb_5001_brincagem (sts=False) ou
#     tb_7002_pia. Ver Especificacao_Brincagem_Leitor.docx secao
#     3.2 e 5.2.
#
#     rfid: hoje SEMPRE gravado vazio ('') - nao existe leitor
#     RFID ainda, campo reservado para quando existir.
#
#     ATENCAO (Regra de Ouro #1 - anti-suposicao): a FK
#     id_usuario abaixo (ForeignKey('public.usuarios.id')) NAO
#     foi conferida contra o model real de usuarios.py - este
#     arquivo nunca foi visto por mim (Claude). O nome da coluna/
#     tabela ('usuarios.id') veio literal da Especificacao
#     fechada (secao 5.2), e o prefixo 'public.' foi aplicado por
#     ser o mesmo padrao usado em id_propriedade logo abaixo
#     (schema publico, catalogo/cadastro compartilhado entre
#     Produtores). CONFERIR contra o model real de usuarios antes
#     de rodar em producao - se o nome/schema real for diferente,
#     e um ajuste de 1 linha aqui.
#
#     v1.0.0: Criacao do modulo (Sessao 057, 20/09/2026, 10:15
#             -03), a partir da especificacao fechada na Sessao
#             056 (Especificacao_Brincagem_Leitor.docx secao
#             5.2). Aplicada ao banco via script SQL
#             Tabelas\N_recriar_tb_5001_brincagem_criar_tb_5003.sql.
# =========================================================

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model RejeicaoBrincagem
# Espelha a tabela tb_5003_rejeicoes_brincagem (schema do Produtor)
# -------------------------------------------------------
class RejeicaoBrincagem(Base):
    __tablename__ = 'tb_5003_rejeicoes_brincagem'

    id                  = Column(Integer, primary_key=True)

    id_propriedade      = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)

    # Quem tentou a leitura. Ver ATENCAO no cabecalho do arquivo -
    # FK nao conferida contra o model real de usuarios.py.
    id_usuario          = Column(Integer, ForeignKey('public.usuarios.id'), nullable=False)

    sisbov              = Column(String(15), nullable=False)   # com digito verificador, ex: "10522220100024-0"
    rfid                = Column(String(15))                    # hoje sempre '' (sem leitor RFID ainda)
    motivo              = Column(String(150), nullable=False)  # ex: "Sisbov do Animal ja Inserido"
    data_tentativa      = Column(Date, nullable=False)

    criado_em           = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<RejeicaoBrincagem sisbov={self.sisbov} motivo={self.motivo}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_5003_rejeicoes_brincagem.py
# =========================================================