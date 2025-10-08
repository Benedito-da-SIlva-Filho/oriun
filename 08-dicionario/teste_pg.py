import psycopg2
import sys

def testar_conexao():
    try:
        print("🔄 Tentando conectar ao PostgreSQL...")
        conn = psycopg2.connect(
            dbname="oriun_dados",
            options='-c client_encoding=UTF8'
        )
        print("✅ Conexão estabelecida com sucesso.")
        conn.close()
    except psycopg2.Error as e:
        print("❌ Erro específico do psycopg2:")
        print(f"→ {e.pgerror or str(e)}")
    except UnicodeDecodeError as ue:
        print("❌ Erro de codificação (UnicodeDecodeError):")
        print(f"→ {ue}")
    except Exception as ex:
        print("❌ Erro inesperado:")
        print(f"→ {ex}")
    finally:
        print("🔚 Teste de conexão finalizado.")

if __name__ == "__main__":
    testar_conexao()
