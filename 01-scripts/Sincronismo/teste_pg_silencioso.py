import psycopg2

try:
    conn = psycopg2.connect(
        dbname="oriun_dados",
        application_name="teste_silencioso",
        options='-c client_encoding=UTF8'
    )
    print("✅ Conexão silenciosa estabelecida com sucesso.")
    conn.close()
except Exception as e:
    print("❌ Erro na conexão:", e)
