import psycopg2

try:
    conn = psycopg2.connect(
        dbname="oriun_dados",
        application_name="debug_utf8",
        options='-c client_encoding=UTF8'
    )
    print("✅ Conexão estabelecida.")
    conn.close()
except Exception as e:
    print("❌ Erro na conexão:")
    print(repr(e))  # Mostra o erro bruto, incluindo bytes problemáticos
