import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        dbname="veri",
        user="postgres"
    )
    conn.close()
    print("[✔] Conexão com PostgreSQL estabelecida.")
except Exception as e:
    try:
        msg = str(e)
    except Exception:
        msg = repr(e)
    print("[✖] Erro ao conectar com PostgreSQL:")
    print(msg)
