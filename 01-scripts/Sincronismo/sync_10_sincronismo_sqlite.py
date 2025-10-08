# sync_10_sincronismo_sqlite.py
# ╔════════════════════════════════════════════════════════════════════╗
# ║         SCRIPTUM HONORIS — SINCRONISMO UNIVERSAL SQLITE           ║
# ║                                                                  ║
# ║  Este módulo sincroniza dados transformados vindos do PostgreSQL ║
# ║  com o banco SQLite, aplicando INSERT ou UPDATE conforme o caso. ║
# ║                                                                  ║
# ║  Características:                                                ║
# ║  - Detecta alterações campo a campo                              ║
# ║  - Usa metadados do dicionário para campo-chave e campos ativos  ║
# ║  - Aplica INSERT OR UPDATE dinamicamente                         ║
# ║  - Registra logs refinados por campo e descrição                 ║
# ║                                                                  ║
# ║  “SINCRONIZAR É HONRAR O ESTADO MAIS RECENTE DA VERDADE.”        ║
# ╚════════════════════════════════════════════════════════════════════╝

from sync_07_logs import log_execucao, registrar_erro
from importador import importar_modulo

# Carregamento dinâmico do módulo de log por metadado
mod_log = importar_modulo(
    "log_por_metadado",
    "C:/Oriun/08-dicionario/04_log_por_metadado.py"
)

registrar_log = mod_log.registrar_log

def buscar_registro_sqlite(cursor, tabela, campo_chave, valor_chave):
    cursor.execute(f"SELECT * FROM {tabela} WHERE {campo_chave} = ?", (valor_chave,))
    resultado = cursor.fetchone()
    if resultado:
        colunas = [desc[0] for desc in cursor.description]
        return dict(zip(colunas, resultado))
    return None

def detectar_alteracoes(registro_novo, registro_antigo, metadado):
    alteracoes = {}
    for campo, props in metadado["campos"].items():
        if props["sincronizar"]:
            novo = registro_novo[campo] if campo in registro_novo else None
            antigo = registro_antigo[campo] if campo in registro_antigo else None
            if novo != antigo:
                alteracoes[campo] = {
                    "valor_antigo": antigo,
                    "valor_novo": novo
                }
    return alteracoes

def sincronizar_sqlite_tabela(tabela, registros, cursor, conexao, metadado):
    try:
        campo_chave = metadado["campo_chave"]
        total = 0

        # 🔒 Conversão segura: se os registros vierem como tuplas
        if registros and isinstance(registros[0], tuple):
            colunas = list(metadado["campos"].keys())
            registros = [dict(zip(colunas, r)) for r in registros]

        for registro in registros:
            valor_chave = registro[campo_chave] if campo_chave in registro else None
            if not valor_chave:
                log_execucao(f"[SYNC_10] ⚠ Registro ignorado: campo-chave '{campo_chave}' ausente ou nulo na tabela {tabela}")
                continue

            registro_antigo = buscar_registro_sqlite(cursor, tabela, campo_chave, valor_chave)

            if registro_antigo:
                alteracoes = detectar_alteracoes(registro, registro_antigo, metadado)
                if alteracoes:
                    campos_update = ", ".join([f"{campo} = ?" for campo in alteracoes])
                    valores_update = [registro[campo] if campo in registro else None for campo in alteracoes]
                    valores_update.append(valor_chave)

                    cursor.execute(f"""
                        UPDATE {tabela}
                        SET {campos_update}
                        WHERE {campo_chave} = ?
                    """, valores_update)

                    for campo in alteracoes:
                        registrar_log(tabela, campo, valor_chave, metadado)
                else:
                    log_execucao(f"[SYNC_10] ⏸ Registro {campo_chave} {valor_chave} já está atualizado na tabela {tabela}")
            else:
                campos_insert = []
                valores_insert = []
                placeholders = []

                for campo, props in metadado["campos"].items():
                    if campo in registro and registro[campo] is not None:
                        campos_insert.append(campo)
                        valores_insert.append(registro[campo])
                        placeholders.append("?")

                cursor.execute(f"""
                    INSERT INTO {tabela} ({', '.join(campos_insert)})
                    VALUES ({', '.join(placeholders)})
                """, valores_insert)

                log_execucao(f"[SYNC_10] ➕ Registro novo inserido: {campo_chave} {valor_chave} na tabela {tabela}")

            total += 1

        conexao.commit()
        log_execucao(f"[SYNC_10] ✔ Tabela {tabela} sincronizada com sucesso: {total} registros aplicados")

    except Exception as e:
        registrar_erro(f"[SYNC_10] ✖ Erro ao sincronizar tabela {tabela}: {e}")
        conexao.rollback()
