import psycopg2

try:
    conn = psycopg2.connect("dbname=oriun_dados options='-c client_encoding=UTF8'")
    print("✅ Conexão com PostgreSQL estabelecida")
    conn.close()
except Exception as e:
    print("❌ Erro na conexão:", e)
