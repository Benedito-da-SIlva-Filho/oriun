import sqlite3
import csv
import os

# Caminho atualizado do banco SQLite
CAMINHO_BANCO = r"C:\Oriun\03-banco\oriun_local.db"
CAMINHO_CSV = r"C:\Oriun\03-banco\backup_a001.csv"

def exportar_dados():
    if not os.path.exists(CAMINHO_BANCO):
        print(f"❌ Banco de dados não encontrado: {CAMINHO_BANCO}")
        return

    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM a001_propriedades")
        rows = cursor.fetchall()

        with open(CAMINHO_CSV, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([desc[0] for desc in cursor.description])  # cabeçalhos
            writer.writerows(rows)

        print(f"✅ Dados exportados com sucesso para: {CAMINHO_CSV}")

    except Exception as e:
        print(f"❌ Erro ao exportar dados: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    exportar_dados()
