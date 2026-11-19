# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_log_conferencia_parceiro.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-15 11:30 -03
# ATUALIZADO EM: 2026-07-17 16:20 -03
# VERSAO: 1.3.0 changelog:
#
# DESCRICAO:
#     Model da tabela tb_log_conferencia_parceiro.
#     Log de auditoria imutavel de toda decisao humana durante
#     a leitura da GTA (PDF/OCR), quando o CPF/CNPJ da Origem
#     e cruzado com o cadastro de Parceiros. Regra de
#     automacao restritiva (Secao 5 do Diario 016): nenhuma
#     criacao ou vinculo de Parceiro/Propriedade e automatica,
#     sempre passa por conferencia humana registrada aqui.
#
#     Tres situacoes possiveis (tipo_situacao):
#       1) Match perfeito - CPF/CNPJ ja cadastrado, segue o
#          fluxo com o Parceiro existente.
#       2) Sem match - CPF/CNPJ novo, sistema cadastra o
#          Parceiro e segue o fluxo.
#       3) Divergencia parcial - CPF/CNPJ bate mas outro dado
#          diverge (ex.: Insc. Estadual, Endereco - campos de
#          tb_parceiros_propriedades), usuario decide se
#          ajusta o cadastro ou segue mesmo assim.
#
#     Nao referencia tb_4001_gta (Sessao 17): a conferencia do
#     Parceiro acontece ANTES da GTA ser salva no banco, entao
#     nao existe id_gta disponivel no momento do log. A tabela
#     nasceu com id_gta NOT NULL por engano na Sessao 16 -
#     coluna removida nesta sessao (tabela ainda estava vazia).
#
#     v1.0.0: Criacao do modulo (Sessao 17), a partir da
#             estrutura real de tb_log_conferencia_parceiro
#             conferida no pgAdmin apos o ajuste (8 colunas).
#     v1.1.0: Sessao 17 (continuacao) - Decisao arquitetural:
#             banco unico + RLS por produtor (schema-por-produtor
#             descartado). Adicionada coluna id_produtor direta.
#     v1.2.0: Sessao 018 - Decisao arquitetural revertida: RLS
#             descartado, Schema-por-Produtor confirmado como
#             modelo definitivo. Coluna id_produtor removida -
#             era suporte tecnico exclusivo do RLS. No modelo de
#             Schema-por-Produtor o isolamento ja e fisico (o
#             log inteiro mora dentro do schema do Produtor cujo
#             usuario tomou a decisao) - manter a coluna seria
#             redundante e um risco de dessincronia.
#
#     v1.3.0: Sessao 019 - Corrigida FK id_usuario para
#             'public.usuarios.id' (com prefixo de schema
#             explicito). Motivo: apos usuario.py v1.3.0 marcar
#             __table_args__ = {'schema': 'public'}, referencias
#             sem o prefixo 'public.' deixaram de encontrar a
#             tabela usuarios, na rotina de Onboarding.
# =========================================================

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model LogConferenciaParceiro
# Espelha a tabela tb_log_conferencia_parceiro no PostgreSQL
# -------------------------------------------------------
class LogConferenciaParceiro(Base):
    __tablename__ = 'tb_log_conferencia_parceiro'

    # Identificacao
    id                          = Column(Integer, primary_key=True)

    # Usuario responsavel pela decisao (sempre obrigatorio -
    # nunca "o software decidiu", sempre "o usuario X confirmou").
    # Isolamento entre Produtores diferentes e garantido pelo
    # schema (Schema-por-Produtor) - nao precisa de coluna
    # id_produtor aqui, ver changelog v1.2.0.
    id_usuario                  = Column(Integer, ForeignKey('public.usuarios.id'), nullable=False)
    usuario                     = relationship('Usuario', foreign_keys=[id_usuario])

    # Parceiro envolvido na conferencia (sempre resolvido no
    # momento do log - match existente ou recem-cadastrado)
    id_parceiro                 = Column(Integer, ForeignKey('tb_parceiros.id'), nullable=False)
    parceiro                    = relationship('Parceiro', foreign_keys=[id_parceiro], backref='logs_conferencia')

    # Propriedade do Parceiro envolvida (opcional - nem toda
    # conferencia resolve uma propriedade especifica)
    id_parceiro_propriedade     = Column(Integer, ForeignKey('tb_parceiros_propriedades.id'))
    parceiro_propriedade        = relationship('ParceiroPropriedades', foreign_keys=[id_parceiro_propriedade], backref='logs_conferencia')

    # Dados da decisao
    tipo_situacao                = Column(String(20), nullable=False)   # MATCH_PERFEITO / SEM_MATCH / DIVERGENCIA
    divergencias_encontradas     = Column(Text)                         # detalhe da divergencia, quando houver
    decisao_tomada                = Column(String(30), nullable=False)   # o que o usuario decidiu fazer

    # Controle de data (log imutavel - sem atualizado_em, o
    # registro nunca e editado depois de criado)
    data_hora                    = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<LogConferenciaParceiro {self.tipo_situacao} - Parceiro {self.id_parceiro}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_log_conferencia_parceiro.py
# =========================================================