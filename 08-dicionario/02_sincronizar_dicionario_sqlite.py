# 02_sincronizar_dicionario_sqlite.py
# ╔════════════════════════════════════════════════════════════════════╗
# ║     SINCRONISMO SEMÂNTICO — DICIONÁRIO DE DADOS PG → SQLITE       ║
# ║                                                                  ║
# ║  Este script extrai os metadados do PostgreSQL e insere no       ║
# ║  SQLite, garantindo que ambos bancos compartilhem a mesma        ║
# ║  estrutura semântica para validação e auditoria.                 ║
# ╚════════════════════════════════════════════════════════════════════╝

import sqlite3
import importlib.util
import sys

# Caminhos dos módulos
CAMINHO_CONEXAO = r"C:\Oriun\08-Dicionario\06_conectar_postgres.py"
CAMINHO_METADADOS = r"C:\Oriun\08-Dicionario\01_carregar_metadados_pg.py"
CAMINHO_LISTAR_TABELAS = r"C:\Oriun\08-Dicionario\02_listar_tabelas_pg.py"
CAMINHO_SQLITE = r"C:\Oriun\01-bases\oriun_local.db"

# 🔧 Carregar módulo de conexão PostgreSQL
spec_conexao = importlib.util.spec_from_file_location("conectar_postgres", CAMINHO_CONEXAO)
mod_conexao = importlib.util.module_from_spec(spec_conexao)
sys.modules["conectar_postgres"] = mod_conexao
spec_conexao.loader.exec_module(mod_conexao)

# 🔧 Carregar módulo de metadados
spec_metadados = importlib.util.spec_from_file_location("carregar_metadados_pg", CAMINHO_METADADOS)
mod_metadados = importlib.util.module_from_spec(spec_metadados)
sys.modules["carregar_metadados_pg"] = mod_metadados
spec_metadados.loader.exec_module(mod_metadados)

# 🔧 Carregar módulo de listagem de tabelas
spec_listar = importlib.util.spec_from_file_location("listar_tabelas_pg", CAMINHO_LISTAR_TABELAS)
mod_listar = importlib.util.module_from_spec(spec_listar)
sys.modules["listar_tabelas_pg"] = mod_listar
spec_listar.loader.exec_module(mod_listar)

def conectar_sqlite():
    try:
        conn = sqlite3.connect(CAMINHO_SQLITE)
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print(f"Erro ao conectar ao SQLite: {e}")
        return None, None

def limpar_dicionario_sqlite(cursor_sqlite):
    try:
        cursor_sqlite.execute("DELETE FROM oriun_dicionario_de_dados")
        print("🧹 Dicionário no SQLite limpo com sucesso.")
    except Exception as e:
        print(f"Erro ao limpar dicionário no SQLite: {e}")

def inserir_metadados_sqlite(cursor_sqlite, metadado):
    for campo, props in metadado["campos"].items():
        try:
            cursor_sqlite.execute("""
                INSERT INTO oriun_dicionario_de_dados (
                    tabela, campo, tipo_sqlite, tipo_postgres,
                    descricao, obrigatorio, sincronizar, fonte
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadado["tabela"],
                campo,
                props.get("tipo_sqlite", ""),
                props.get("tipo_postgres", ""),
                props.get("descricao", ""),
                props.get("obrigatorio", False),
                props.get("sincronizar", False),
                props.get("fonte", "")
            ))
        except Exception as e:
            print(f"Erro ao inserir campo '{campo}' da tabela '{metadado['tabela']}': {e}")

def sincronizar_dicionario():
    conn_pg, cursor_pg = mod_conexao.conectar_postgres()
    conn_sqlite, cursor_sqlite = conectar_sqlite()

    if not cursor_pg or not cursor_sqlite:
        print("Erro nas conexões. Abortando sincronismo.")
        return

    limpar_dicionario_sqlite(cursor_sqlite)

    tabelas = mod_listar.listar_tabelas_pg(cursor_pg)
    for tabela in tabelas:
        try:
            metadado = mod_metadados.carregar_metadados_pg(cursor_pg, tabela)
            inserir_metadados_sqlite(cursor_sqlite, metadado)
            print(f"✅ Tabela '{tabela}' sincronizada com sucesso.")
        except Exception as e:
            print(f"⚠ Erro ao processar tabela '{tabela}': {e}")

    conn_sqlite.commit()
    conn_sqlite.close()
    conn_pg.close()
    print("\n📘 Sincronismo do dicionário concluído com sucesso.")

if __name__ == "__main__":
    sincronizar_dicionario()
