import sqlite3
import psycopg2

# Caminho do banco SQLite
CAMINHO_SQLITE = r"C:\Oriun\03-banco\oriun_local.db"

# Nome da tabela que será sincronizada
TABELA = 'a001_propriedades'
CAMPO_CHAVE = 'a001_cod_propriedade'

def conectar_sqlite():
    return sqlite3.connect(CAMINHO_SQLITE)

def conectar_postgres():
    return psycopg2.connect(dbname="oriun_dados")  # Ajuste se necessário

def carregar_campos_sincronizaveis(cursor_sqlite, tabela):
    cursor_sqlite.execute("""
        SELECT nome_campo FROM oriun_dicionario_de_dados
        WHERE nome_tabela = ? AND sincronizar = 1
    """, (tabela,))
    return [row[0] for row in cursor_sqlite.fetchall()]

def buscar_registros_sqlite(cursor_sqlite, tabela, campo_chave):
    cursor_sqlite.execute(f"SELECT {campo_chave} FROM {tabela}")
    return [row[0] for row in cursor_sqlite.fetchall()]

def buscar_registro(cursor, tabela, campo_chave, valor_chave, campos, banco):
    if banco == 'sqlite':
        cursor.execute(f"SELECT {', '.join(campos)} FROM {tabela} WHERE {campo_chave} = ?", (valor_chave,))
    else:
        cursor.execute(f'SELECT {", ".join(campos)} FROM "01-Cadastros".{tabela} WHERE {campo_chave} = %s', (valor_chave,))
    row = cursor.fetchone()
    return dict(zip(campos, row)) if row else None

def sincronizar_registro_sqlite_para_postgres(reg_sqlite, reg_pg, campos, cursor_pg, conn_pg, tabela, campo_chave, valor_chave):
    atualizacoes = {campo: reg_sqlite[campo] for campo in campos if str(reg_sqlite[campo]) != str(reg_pg.get(campo))}
    if atualizacoes:
        set_clause = ", ".join([f"{campo} = %s" for campo in atualizacoes])
        valores = list(atualizacoes.values()) + [valor_chave]
        cursor_pg.execute(f'UPDATE "01-Cadastros".{tabela} SET {set_clause} WHERE {campo_chave} = %s', valores)
        conn_pg.commit()
        print(f"✅ Atualizado PK {valor_chave}: {atualizacoes}")
    else:
        print(f"🟡 Sem mudanças para PK {valor_chave}")

def sincronizar_tabela():
    conn_sqlite = conectar_sqlite()
    conn_pg = conectar_postgres()
    cur_sqlite = conn_sqlite.cursor()
    cur_pg = conn_pg.cursor()

    campos = carregar_campos_sincronizaveis(cur_sqlite, TABELA)
    chaves = buscar_registros_sqlite(cur_sqlite, TABELA, CAMPO_CHAVE)

    for valor_chave in chaves:
        reg_sqlite = buscar_registro(cur_sqlite, TABELA, CAMPO_CHAVE, valor_chave, campos, 'sqlite')
        reg_pg = buscar_registro(cur_pg, TABELA, CAMPO_CHAVE, valor_chave, campos, 'postgres')
        if reg_sqlite and reg_pg:
            sincronizar_registro_sqlite_para_postgres(reg_sqlite, reg_pg, campos, cur_pg, conn_pg, TABELA, CAMPO_CHAVE, valor_chave)
        else:
            print(f"❌ Registro PK {valor_chave} não encontrado em um dos bancos")

    conn_sqlite.close()
    conn_pg.close()

if __name__ == "__main__":
    sincronizar_tabela()
