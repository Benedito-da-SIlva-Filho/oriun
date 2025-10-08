import sqlite3
import psycopg2
from datetime import datetime
import pytz
import traceback
import os

# 🌎 Fuso horário de Brasília
brasilia = pytz.timezone("America/Sao_Paulo")

# 📊 Relatório final por tabela
relatorio_final = {}

# 🛡️ Registro de erros
def registrar_erro(e):
    try:
        erro_str = str(e).encode('latin1').decode('utf-8')
    except Exception:
        erro_str = repr(e)

    log_path = os.path.join(os.path.dirname(__file__), "log_pg.txt")
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[{datetime.now(brasilia)}] ERRO: {erro_str}\n")

# 📝 Registro de leitura de dados
def registrar_leitura(nome_tabela, linha):
    try:
        log_path = r"C:\Oriun\01-scripts\log_pg.txt"
        pasta = os.path.dirname(log_path)
        if not os.path.exists(pasta):
            print(f"❌ Diretório não encontrado: {pasta}")
            return

        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"[{datetime.now(brasilia)}] Tabela '{nome_tabela}' - Registro lido: {linha}\n")
        print(f"✅ Registro gravado no log: {linha}")
    except Exception as e:
        print(f"❌ Erro ao registrar leitura no log_pg.txt: {e}")
        registrar_erro(f"Erro ao registrar leitura: {e}")

# 📋 Listar todas as tabelas do SQLite
def listar_tabelas_sqlite(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row[0] for row in cursor.fetchall()]

# 📋 Listar colunas de uma tabela
def listar_colunas_sqlite(conn, nome_tabela):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({nome_tabela});")
    return [row[1] for row in cursor.fetchall()]

# 🌾 Extrair dados de uma tabela com log reforçado
def extrair_dados_tabela(conn, nome_tabela):
    print(f"🧪 Entrando na função extrair_dados_tabela para '{nome_tabela}'")
    colunas = listar_colunas_sqlite(conn, nome_tabela)
    colunas_sql = ', '.join([f'"{col}"' for col in colunas])
    cursor = conn.cursor()
    cursor.execute(f"SELECT {colunas_sql} FROM {nome_tabela};")
    dados = cursor.fetchall()

    print(f"[{datetime.now(brasilia)}] 📥 {len(dados)} registro(s) lido(s) da tabela '{nome_tabela}'")
    relatorio_final[nome_tabela] = {"lidos": len(dados), "sincronizados": 0}

    for i, linha in enumerate(dados, start=1):
        print(f"🔎 Registro {i}: {linha}")
        print(f"🧪 Chamando registrar_leitura para registro {i}")
        registrar_leitura(nome_tabela, linha)

    print(f"🧪 Finalizando leitura da tabela '{nome_tabela}'\n")
    return dados, colunas

# 🔄 Mapeamento de nomes entre SQLite e PostgreSQL
def mapear_nome_tabela_sqlite_para_postgres(nome_sqlite):
    if nome_sqlite == "a001_propriedades":
        return "a001_propriedades"
    return nome_sqlite

# 🔁 Conversão de campos booleanos
def converter_booleanos(linha, colunas_booleanas, colunas):
    linha_convertida = list(linha)
    for i, col in enumerate(colunas):
        if col in colunas_booleanas:
            valor = linha[i]
            if isinstance(valor, int):
                linha_convertida[i] = bool(valor)
            elif isinstance(valor, str):
                if valor.lower() in ['true', '1']:
                    linha_convertida[i] = True
                elif valor.lower() in ['false', '0']:
                    linha_convertida[i] = False
    return tuple(linha_convertida)

# 🔄 Sincronizar uma tabela com PostgreSQL
def sincronizar_tabela_postgres(nome_sqlite, dados, colunas):
    try:
        conn = psycopg2.connect(
            dbname="oriun_dev",
            user="postgres",
            password="",  # Ambiente de testes: sem senha
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        nome_pg = mapear_nome_tabela_sqlite_para_postgres(nome_sqlite)
        colunas_sql = ', '.join([f'"{col}"' for col in colunas])
        valores_sql = ', '.join(['%s'] * len(colunas))

        pk = colunas[0]
        campo_mod = next((c for c in colunas if "movimentacao" in c.lower()), None)

        colunas_booleanas = ["a001_status", "ativo", "visivel"]

        registros_sincronizados = 0

        for linha in dados:
            print(f"📌 Processando PK = {linha[0]}")
            print(f"🔎 Linha extraída: {linha}")
            linha_convertida = converter_booleanos(linha, colunas_booleanas, colunas)
            print("📤 Tentando inserir:", linha_convertida)

            try:
                if campo_mod:
                    update_sql = ', '.join([f'"{col}" = EXCLUDED."{col}"' for col in colunas if col != pk])
                    sql = f"""
                        INSERT INTO "01-Cadastros"."{nome_pg}" ({colunas_sql})
                        VALUES ({valores_sql})
                        ON CONFLICT ("{pk}")
                        DO UPDATE SET {update_sql}
                        WHERE EXCLUDED."{campo_mod}" > "01-Cadastros"."{nome_pg}"."{campo_mod}";
                    """
                else:
                    sql = f"""
                        INSERT INTO "01-Cadastros"."{nome_pg}" ({colunas_sql})
                        VALUES ({valores_sql})
                        ON CONFLICT ("{pk}") DO NOTHING;
                    """

                print("🧾 SQL:", sql.strip())
                cursor.execute(sql, linha_convertida)
                registros_sincronizados += 1
                relatorio_final[nome_sqlite]["sincronizados"] += 1

            except Exception as linha_erro:
                print("❌ Erro ao inserir:", linha_erro)
                registrar_erro(f"Erro em linha da tabela '{nome_sqlite}': {linha_erro}")

        conn.commit()
        conn.close()
        print(f"[{datetime.now(brasilia)}] ✅ Tabela '{nome_sqlite}' sincronizada com {registros_sincronizados} registro(s).")
    except Exception as e:
        print(f"[{datetime.now(brasilia)}] ❌ Erro ao sincronizar tabela '{nome_sqlite}'.")
        registrar_erro(e)

# 🚀 Fluxo principal
print(f"[{datetime.now(brasilia)}] 🚀 Iniciando sincronismo entre SQLite e PostgreSQL...\n")

caminho_sqlite = r"C:\Oriun\03-banco\oriun_local.db"

try:
    conn_sqlite = sqlite3.connect(caminho_sqlite)
    tabelas = listar_tabelas_sqlite(conn_sqlite)

    for tabela in tabelas:
        if tabela.startswith("sqlite_"):
            continue

        dados, colunas = extrair_dados_tabela(conn_sqlite, tabela)

        if dados:
            sincronizar_tabela_postgres(tabela, dados, colunas)
        else:
            print(f"[{datetime.now(brasilia)}] ⚠️ Tabela '{tabela}' está vazia ou não pôde ser lida.")
            registrar_erro(f"Tabela '{tabela}' está vazia ou não pôde ser lida.")

    conn_sqlite.close()
except Exception as e:
    print(f"[{datetime.now(brasilia)}] ❌ Erro geral no processo de sincronismo.")
    registrar_erro(e)

print(f"[{datetime.now(brasilia)}] ✅ Processo encerrado.\n")

# 📊 Relatório final
print("\n📊 RELATÓRIO FINAL DE SINCRONISMO")
for tabela, info in relatorio_final.items():
    print(f"🗂️ Tabela '{tabela}': {info['lidos']} lido(s), {info['sincronizados']} sincronizado(s)")


try:
    log_path = r"C:\Oriun\01-scripts\log_pg.txt"
    with open(log_path, "a", encoding="utf-8") as log:
        log.write("\n📊 RELATÓRIO FINAL DE SINCRONISMO\n")
        for tabela, info in relatorio_final.items():
            linha = f"🗂️ Tabela '{tabela}': {info['lidos']} lido(s), {info['sincronizados']} sincronizado(s)\n"
            log.write(linha)
    print("🧾 Relatório final gravado no log.")
except Exception as e:
    print(f"❌ Erro ao gravar relatório final no log: {e}")
    registrar_erro(f"Erro ao gravar relatório final: {e}")


print("🧪 Teste de escrita no log...")
registrar_leitura("diagnostico_teste", ("PK_TESTE", "registro de teste"))