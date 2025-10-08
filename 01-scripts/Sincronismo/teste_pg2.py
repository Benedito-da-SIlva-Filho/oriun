import psycopg2

try:
    conn = psycopg2.connect(
        dbname="oriun_dados",
        options='-c client_encoding=LATIN1'
    )
    print("✅ Conexão com PostgreSQL estabelecida usando LATIN1")
    conn.close()
except Exception as e:
    print("❌ Erro na conexão:", e)
