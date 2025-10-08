import psycopg2
import locale
import os

# Força o locale para ignorar erros de decodificação
locale.setlocale(locale.LC_ALL, 'C')
os.environ['PYTHONIOENCODING'] = 'utf-8:ignore'

try:
    conn = psycopg2.connect(
        dbname="oriun_dados",
        application_name="teste_ignore",
        options='-c client_encoding=UTF8'
    )
    print("✅ Conexão estabelecida com workaround de encoding.")
    conn.close()
except Exception as e:
    print("❌ Erro na conexão:", e)
