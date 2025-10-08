import psycopg2
import sqlite3

# Conexões
conn_sqlite = sqlite3.connect(r"C:\Oriun\03-banco\oriun_local.db")
cursor_sqlite = conn_sqlite.cursor()

conn_pg = psycopg2.connect(
    dbname="oriun_dev",
    user="postgres",
    password="sua_senha",
    host="localhost",
    port="5432"
)
cursor_pg = conn_pg.cursor()

# Dados de teste
cursor_sqlite.execute("SELECT * FROM a001_propriedades")
dados = cursor_sqlite.fetchall()

# Colunas
colunas = [desc[0] for desc in cursor_sqlite.description]
colunas_sql = ', '.join(f'"{c}"' for c in colunas)
valores_sql = ', '.join(['%s'] * len(colunas))
pk = "a001_Cod_Propriedade"
update_sql = ', '.join(f'"{c}" = EXCLUDED."{c}"' for c in colunas if c != pk)

# Inserção
for linha in dados:
    cursor_pg.execute(f"""
        INSERT INTO "01-Cadastros"."a001_propriedades" ({colunas_sql})
        VALUES ({valores_sql})
        ON CONFLICT ("{pk}")
        DO UPDATE SET {update_sql};
    """, linha)

conn_pg.commit()
conn_pg.close()
conn_sqlite.close()
