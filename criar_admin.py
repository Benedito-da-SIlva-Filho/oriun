# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion
# MODULO: criar_admin.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-06-21 11:30 -03
# ATUALIZADO EM: 2026-07-02 14:46 -03
# VERSAO: 1.3.0
#
# DESCRICAO:
#     Script para criar o usuario Master da Consiste.
#     Execute apenas uma vez!
#     As credenciais vem do arquivo .env
#     v1.0.0: Criacao do modulo.
#     v1.1.0: Credenciais lidas do .env
#     v1.2.0: Adicionado campo cargo.
#     v1.3.0: Sessao 010 - Corrigidos nomes de campo renomeados
#             no model (certificadora_id -> id_certificadora,
#             produtor_id -> id_produtor).
#
# COMO RECRIAR O USUARIO MASTER:
#     $env:PATH += ";C:\Program Files\PostgreSQL\16\bin"
#     psql -U postgres -p 5433 -d orion
#     DELETE FROM usuarios WHERE login = 'consiste';
#     SELECT id, login FROM usuarios; <- deve retornar (0 rows)
#     \q
#     python criar_admin.py
# =========================================================

from werkzeug.security import generate_password_hash
from backend.database import engine
from backend.models import Usuario
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

# Carrega as variaveis do arquivo .env
load_dotenv()

# -------------------------------------------------------
# Dados do usuario Master — vem do .env
# -------------------------------------------------------
MASTER_LOGIN = os.getenv('MASTER_LOGIN', 'consiste')
MASTER_SENHA = os.getenv('MASTER_SENHA', '')
MASTER_NOME  = os.getenv('MASTER_NOME', 'Benedito Silva Filho')
MASTER_CARGO = os.getenv('MASTER_CARGO', 'Master')

# -------------------------------------------------------
# Cria o usuario Master
# -------------------------------------------------------
def criar_master():

    # Verifica se a senha foi configurada
    if not MASTER_SENHA:
        print('ERRO: MASTER_SENHA nao configurada no .env!')
        return

    with Session(engine) as db:

        # Verifica se ja existe
        existente = db.query(Usuario).filter_by(login=MASTER_LOGIN).first()
        if existente:
            print(f'Usuario {MASTER_LOGIN} ja existe!')
            return

        # Cria o usuario Master
        master = Usuario(
            login             = MASTER_LOGIN,
            senha             = generate_password_hash(MASTER_SENHA),
            perfil            = 'CONSISTE',
            nome              = MASTER_NOME,
            cargo             = MASTER_CARGO,
            id_certificadora  = None,
            id_produtor       = None,
            ativo             = True
        )

        db.add(master)
        db.commit()
        print('=' * 50)
        print('Usuario Master criado com sucesso!')
        print(f'Login  : {MASTER_LOGIN}')
        print(f'Nome   : {MASTER_NOME}')
        print(f'Perfil : CONSISTE')
        print(f'Cargo  : {MASTER_CARGO}')
        print('=' * 50)

# -------------------------------------------------------
# Execucao
# -------------------------------------------------------
if __name__ == '__main__':
    criar_master()

# =========================================================
# FIM DE ARQUIVO: criar_admin.py
# =========================================================