# 06_conectar_postgres.py
# ╔════════════════════════════════════════════════════════════════════╗
# ║     CONEXÃO COM POSTGRESQL — MÓDULO LOCAL PARA O DICIONÁRIO       ║
# ║                                                                  ║
# ║  Este módulo estabelece conexão com o banco PostgreSQL,          ║
# ║  retornando cursor e conexão para uso nos scripts de sincronismo.║
# ╚════════════════════════════════════════════════════════════════════╝

import psycopg2

def conectar_postgres():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            dbname="oriun_dados",
            user="postgres",
            password="sua_senha_aqui"
        )
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print(f"Erro ao conectar ao PostgreSQL: {e}")
        return None, None
