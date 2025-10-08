# +------------------------------------------------------------------+
# ¦     TESTE DE SINCRONISMO BIDIRECIONAL — PROJETO ORIUN           ¦
# ¦                                                                  ¦
# ¦  Valida se os registros 6 e 7 foram atualizados corretamente     ¦
# ¦  após execução do sincronismo.py                                 ¦
# ¦                                                                  ¦
# ¦  “TESTAR É HONRAR A CONFIANÇA NO QUE FOI CONSTRUÍDO.”            ¦
# +------------------------------------------------------------------+

import os
import sqlite3
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime

LOG_PATH = r"C:\Oriun\06-logs\teste_sincronismo.log"

def registrar_log(texto):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8", errors="replace") as f:
        f.write(texto + "\n")

def conectar_sqlite():
    print("🔧 Conectando ao SQLite...")
    registrar_log("🔧 Conectando ao SQLite...")
    caminho_db = r"C:\Oriun\03-banco\oriun_local.db"
    conn = sqlite3.connect(caminho_db)
    conn.row_factory = sqlite3.Row
    return conn.cursor()

def conectar_postgres():
    print("🔧 Conectando ao PostgreSQL...")
    registrar_log("🔧 Conectando ao PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            port="5432",
            dbname="oriun_dev",  # ← nome corrigido conforme ambiente real
            user="postgres",
            password="postgres"
        )
        return conn.cursor(cursor_factory=DictCursor)
    except Exception as e:
        erro_str = repr(e)
        msg = f"[ERRO] Falha ao conectar ao PostgreSQL: {erro_str}"
        print(msg)
        registrar_log(msg)
        return None

def verificar_registros():
    print("🚀 Iniciando verificação de registros...")
    registrar_log("🚀 Iniciando verificação de registros...")

    registros = [6, 7]
    campos = ["a001_cod_propriedade", "a001_nome_propriedade", "a001_data_de_movimentacao"]

    cursor_sqlite = conectar_sqlite()
    cursor_pg = conectar_postgres()
    if not cursor_pg:
        print("⚠ Encerrando: conexão com PostgreSQL falhou.")
        registrar_log("⚠ Encerrando: conexão com PostgreSQL falhou.")
        return

    cabecalho = f"\n📋 RELATÓRIO DE TESTE DE SINCRONISMO BIDIRECIONAL — {datetime.now()}\n"
    cabecalho += "=" * 70
    print(cabecalho)
    registrar_log(cabecalho)

    for cod in registros:
        print(f"\n🔍 Verificando propriedade {cod}...")
        registrar_log(f"\n🔍 Verificando propriedade {cod}...")

        # SQLite
        cursor_sqlite.execute(f"""
            SELECT {', '.join(campos)}
            FROM a001_propriedades
            WHERE a001_cod_propriedade = ?;
        """, (cod,))
        dados_sqlite = cursor_sqlite.fetchone()

        # PostgreSQL
        cursor_pg.execute(f"""
            SELECT {', '.join(campos)}
            FROM "01-Cadastros".a001_propriedades
            WHERE a001_cod_propriedade = %s;
        """, (cod,))
        dados_pg = cursor_pg.fetchone()

        if not dados_sqlite or not dados_pg:
            msg = f"❌ Registro {cod} não encontrado em um dos bancos."
            print(msg)
            registrar_log(msg)
            continue

        nome_sqlite = dados_sqlite["a001_nome_propriedade"]
        nome_pg = dados_pg["a001_nome_propriedade"]

        data_sqlite = dados_sqlite["a001_data_de_movimentacao"]
        data_pg = dados_pg["a001_data_de_movimentacao"]

        linha_sqlite = f"SQLite → Nome: {nome_sqlite} | Data: {data_sqlite}"
        linha_pg = f"PostgreSQL → Nome: {nome_pg} | Data: {data_pg}"

        print(linha_sqlite)
        print(linha_pg)
        registrar_log(linha_sqlite)
        registrar_log(linha_pg)

        if nome_sqlite == nome_pg:
            status = "✅ Nome sincronizado corretamente."
        else:
            status = "⚠ Nome divergente entre os bancos."

        print(status)
        registrar_log(status)
        registrar_log("-" * 60)

    print("\n✅ Verificação concluída.")
    registrar_log("✅ Verificação concluída.")

if __name__ == "__main__":
    print("🧪 Executando script principal...")
    registrar_log("🧪 Executando script principal...")
    verificar_registros()

print("🔚 Fim do script.")
registrar_log("🔚 Fim do script.")
