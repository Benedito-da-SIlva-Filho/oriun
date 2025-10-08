# sync_05_conexao_postgres.py
# ╔════════════════════════════════════════════════════════════════════╗
# ║     CONEXÃO COM POSTGRESQL — AMBIENTE DEV                         ║
# ║                                                                  ║
# ║  Conecta ao banco oriun_dev usando autenticação local/trust      ║
# ║  Retorna conexão e cursor com DictCursor                         ║
# ║  Registra sucesso com [SYNC_05] ou erro com detalhes             ║
# ╚════════════════════════════════════════════════════════════════════╝

import psycopg2
from psycopg2.extras import DictCursor
from sync_07_logs import log_execucao, registrar_erro

def conectar_postgres():
    try:
        conexao = psycopg2.connect(
            dbname="oriun_dev",
            user="postgres",
            host="localhost",
            port="5432"
            # Sem senha — ambiente DEV usa trust/local
        )
        cursor = conexao.cursor(cursor_factory=DictCursor)
        log_execucao("[SYNC_05] ✔ Conexão com PostgreSQL estabelecida com sucesso")
        return conexao, cursor

    except Exception as e:
        registrar_erro(f"[SYNC_05] ✖ Erro ao conectar ao PostgreSQL: {e}")
        return None, None
