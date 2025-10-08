# ╔════════════════════════════════════════════════════════════════════╗
# ║     AUDITORIA DE ESTRUTURA — DICIONÁRIO vs SQLITE                ║
# ║                                                                  ║
# ║  Compara campos definidos no dicionário de dados PostgreSQL      ║
# ║  com colunas reais das tabelas no banco SQLite                   ║
# ║                                                                  ║
# ║  Gera relatório de divergência por tabela                        ║
# ╚════════════════════════════════════════════════════════════════════╝

import sys
import os
sys.path.append(os.path.abspath("C:/Oriun/01-scripts/Sincronismo"))  # Caminho correto para os módulos sync_XX

from sync_05_conexao_postgres import conectar_postgres
from sync_09_conexao_sqlite import conectar_sqlite
from sync_03_leitura_sqlite import obter_colunas_sqlite
from sync_07_logs import log_execucao, registrar_erro
from importador import importar_modulo

mod_dicionario = importar_modulo(
    "carregar_metadados_pg",
    "C:/Oriun/08-dicionario/01_carregar_metadados_pg.py"
)

def obter_tabelas_dicionario(cursor_pg):
    try:
        cursor_pg.execute("""
            SELECT DISTINCT nome_tabela
            FROM "01-Cadastros".oriun_dicionario_de_dados
            ORDER BY nome_tabela;
        """)
        resultados = cursor_pg.fetchall()
        return [row[0] for row in resultados]
    except Exception as e:
        registrar_erro(f"[AUDITORIA] ✖ Erro ao obter lista de tabelas do dicionário: {e}")
        return []

def comparar_estrutura(tabela, campos_metadado, colunas_sqlite):
    faltando = [campo for campo in campos_metadado if campo not in colunas_sqlite]
    extras = [col for col in colunas_sqlite if col not in campos_metadado]

    if not faltando and not extras:
        log_execucao(f"[AUDITORIA] ✅ Tabela {tabela} está alinhada")
    else:
        if faltando:
            registrar_erro(f"[AUDITORIA] ⚠ Campos ausentes no SQLite ({tabela}): {faltando}")
        if extras:
            log_execucao(f"[AUDITORIA] ℹ Colunas extras no SQLite ({tabela}): {extras}")

def auditar_estrutura():
    conn_pg, cursor_pg = conectar_postgres()
    if not (conn_pg and cursor_pg):
        registrar_erro("[AUDITORIA] ✖ Falha ao conectar ao PostgreSQL.")
        return

    cursor_sqlite, conn_sqlite = conectar_sqlite(r"C:/Oriun/03-banco/oriun_local.db")
    if not (cursor_sqlite and conn_sqlite):
        registrar_erro("[AUDITORIA] ✖ Falha ao conectar ao SQLite.")
        return

    tabelas = obter_tabelas_dicionario(cursor_pg)
    log_execucao(f"[AUDITORIA] 📋 Iniciando auditoria de {len(tabelas)} tabelas...")

    for tabela in tabelas:
        try:
            metadado = mod_dicionario.carregar_metadados_pg(cursor_pg, tabela)
            campos_metadado = list(metadado["campos"].keys())
            colunas_sqlite = obter_colunas_sqlite(tabela)

            if not campos_metadado:
                registrar_erro(f"[AUDITORIA] ✖ Metadado vazio para {tabela}")
                continue

            if not colunas_sqlite:
                registrar_erro(f"[AUDITORIA] ✖ Tabela {tabela} não encontrada no SQLite")
                continue

            comparar_estrutura(tabela, campos_metadado, colunas_sqlite)

        except Exception as e:
            registrar_erro(f"[AUDITORIA] ✖ Erro ao auditar tabela {tabela}: {e}")

    log_execucao("[AUDITORIA] ✔ Auditoria concluída")

if __name__ == "__main__":
    auditar_estrutura()
