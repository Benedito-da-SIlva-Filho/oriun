# +--------------------------------------------------------------------+
# ¦         SCRIPTUM HONORIS — CONEXOES.PY ORIUN                       ¦
# ¦                                                                    ¦
# ¦  Módulo de conexão com bancos SQLite e PostgreSQL                  ¦
# ¦  Retorna cursor e conexão prontos para uso                         ¦
# ¦                                                                    ¦
# ¦  “CONECTAR É ESTABELECER CONFIANÇA ENTRE FONTES DE VERDADE.”       ¦
# +--------------------------------------------------------------------+

import sqlite3
import psycopg2
from sync_07_logs import registrar_erro, log_execucao

def conectar_sqlite(caminho_db=r"C:/Oriun/03-banco/oriun_local.db"):
    try:
        conexao = sqlite3.connect(caminho_db)
        cursor = conexao.cursor()
        log_execucao(f"[CONEXÃO] ? SQLite conectado com sucesso: {caminho_db}")
        return cursor, conexao
    except Exception as e:
        registrar_erro(f"[CONEXÃO] ? Erro ao conectar ao SQLite: {e}")
        return None, None

def conectar_postgres():
    try:
        conexao = psycopg2.connect(
            dbname="oriun",
            user="postgres",
            host="localhost",
            port="5432"
            # Sem senha, usando trust no pg_hba.conf
        )
        cursor = conexao.cursor()
        log_execucao("[CONEXÃO] ? PostgreSQL conectado com sucesso.")
        return conexao, cursor
    except Exception as e:
        registrar_erro(f"[CONEXÃO] ? Erro ao conectar ao PostgreSQL: {e}")
        return None, None
