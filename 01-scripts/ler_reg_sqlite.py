import sqlite3

conn = sqlite3.connect(r"C:\Oriun\03-banco\oriun_local.db")
cursor = conn.cursor()

cursor.execute("SELECT a001_cod_propriedade FROM a001_propriedades;")
registros = cursor.fetchall()

print("📋 PKs encontrados na tabela:")
for r in registros:
    print(f"🔎 PK = {r[0]}")

conn.close()
