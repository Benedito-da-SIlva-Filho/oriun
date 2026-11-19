# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend
# MODULO: backend\database.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-06-21 08:17 -03
# ATUALIZADO EM: 2026-06-21 08:17 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Conexao com o banco de dados PostgreSQL.
#     Arquitetura multi-tenant por schema.
#     - get_engine()     -> cria a conexao com o banco
#     - testar_conexao() -> confirma que o banco esta acessivel
#     v1.0.0: Criacao do modulo.
#     v1.1.0: Variaveis separadas — evita problemas com
#             caracteres especiais na senha.
# =========================================================

from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

# Carrega as variaveis do arquivo .env
load_dotenv()

# -------------------------------------------------------
# Leitura das variaveis de ambiente
# -------------------------------------------------------
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5433')
DB_NAME = os.getenv('DB_NAME', 'orion')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', '')

# -------------------------------------------------------
# DIAGNOSTICO — remove apos confirmar a conexao
# -------------------------------------------------------
#print(f'DEBUG HOST: {DB_HOST}')
#print(f'DEBUG PORT: {DB_PORT}')
#print(f'DEBUG NAME: {DB_NAME}')
#print(f'DEBUG USER: {DB_USER}')
#print(f'DEBUG PASS: {DB_PASS}')

# -------------------------------------------------------
# Codifica a senha — escapa caracteres especiais (@, #)
# -------------------------------------------------------
DB_PASS_ENCODED = quote_plus(DB_PASS)
DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASS_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# -------------------------------------------------------
# Cria a conexao principal com o banco PostgreSQL
# -------------------------------------------------------
engine = create_engine(DATABASE_URL)

# -------------------------------------------------------
# Teste de conexao — confirma que o banco esta acessivel
# -------------------------------------------------------
def testar_conexao():
    try:
        with engine.connect() as conexao:
            conexao.execute(text('SELECT 1'))
            print('Conexao com o banco orion: OK!')
            return True
    except Exception as erro:
        print(f'Erro ao conectar no banco: {erro}')
        return False

# =========================================================
# FIM DE ARQUIVO: backend\database.py
# =========================================================