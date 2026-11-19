# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\usuario.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-06-21 09:41 -03
# ATUALIZADO EM: 2026-08-13 11:17 -03
# VERSAO: 1.4.0
#
# DESCRICAO:
#     Model da tabela usuarios.
#     Controle de acesso e login do sistema.
#     Perfis: ADMIN, CERTIFICADORA, PRODUTOR, CONSISTE
#     v1.0.0: Criacao do modulo.
#     v1.1.0: Adicionado campo senha_provisoria.
#     v1.2.0: Sessao 010 - Corrigido nome das colunas de FK
#             para o padrao id_ (certificadora_id -> 
#             id_certificadora), produtor_id -> id_produtor),
#             acompanhando o RENAME COLUMN feito no banco na
#             Sessao 009. Nenhum outro campo foi alterado.
#	 v1.3.0: Sessao 019 - Adicionado __table_args__ com schema
#	             'public' explicito. Mesmo motivo de produtor.py v2.2.0 -
#	             Usuario e referenciada por FK a partir de
#	             tb_3007_brincos_entrada.id_responsavel.
#     v1.4.0: Sessao 034 (continuacao 9, 13/08/2026, 11:17 -03) -
#             Adicionado campo login_provisorio (Boolean, default
#             True), espelhando o padrao ja existente de
#             senha_provisoria. Motivado pela decisao de Benedito
#             de que, no primeiro acesso, o usuario devera poder
#             escolher seu proprio login (nao so a senha) - feature
#             ainda NAO implementada (tela de escolha fica como
#             pendencia formal, precisa dos arquivos de usuarios.py/
#             troca de senha para ser desenhada com seguranca). Esta
#             coluna e criada agora para que os Usuarios ja criados
#             hoje (Cenario 1 - botao "Criar Acesso" em
#             produtores.py v1.9.0) nasçam compativeis com essa
#             feature futura, sem exigir migracao/retrabalho depois.
#             Ver Tabelas\alterar_usuarios_login_provisorio.sql.
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base

# -------------------------------------------------------
# Model Usuario
# Espelha a tabela usuarios no PostgreSQL
# -------------------------------------------------------
class Usuario(Base):
    __tablename__ = 'usuarios'
    __table_args__ = {'schema': 'public'}

    # Identificacao
    id               = Column(Integer, primary_key=True)
    id_certificadora = Column(Integer, ForeignKey('certificadoras.id'))
    id_produtor      = Column(Integer, ForeignKey('public.produtores.id'))
    login            = Column(String(50), nullable=False, unique=True)
    senha            = Column(String(200), nullable=False)  # sempre criptografada!
    perfil           = Column(String(20), nullable=False)   # ADMIN, CERTIFICADORA, PRODUTOR, CONSISTE
    nome             = Column(String(100))
    email            = Column(String(100))
    cargo            = Column(String(50))   # Master, Suporte, Estagiario, etc.

    # Relacionamentos
    certificadora    = relationship('Certificadora', backref='usuarios')

    # Controle
    ativo             = Column(Boolean, default=True)
    senha_provisoria  = Column(Boolean, default=True)  # TRUE=senha definitiva | FALSE=deve trocar no proximo login
    # v1.4.0: mesmo padrao de senha_provisoria, agora para o LOGIN.
    # TRUE  = login ainda e o provisorio (CPF/CNPJ) - usuario ainda
    #         nao escolheu um login proprio (feature futura, sem
    #         tela ainda).
    # FALSE = usuario ja escolheu seu proprio login.
    login_provisorio  = Column(Boolean, nullable=False, default=True)
    ultimo_acesso    = Column(DateTime)
    criado_em        = Column(DateTime, default=datetime.now)
    atualizado_em    = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Usuario {self.login} — {self.perfil}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\usuario.py
# =========================================================