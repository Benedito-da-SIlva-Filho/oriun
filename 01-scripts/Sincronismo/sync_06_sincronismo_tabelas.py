# sync_06_sincronismo_tabelas.py
# ╔════════════════════════════════════════════════════════════════════╗
# ║     SCRIPTUM HONORIS — SINCRONISMO DE TABELAS ORIUN              ║
# ║                                                                  ║
# ║  Suporte bidirecional: PostgreSQL ↔ SQLite                       ║
# ║  Atualiza apenas campos modificados                              ║
# ║  Usa metadados para chave e campos sincronizáveis                ║
# ║  Registra logs refinados por campo e descrição                   ║
# ╚════════════════════════════════════════════════════════════════════╝

from sync_07_logs import log_execucao, registrar_erro
from importador import importar_modulo

mod_log = importar_modulo(
    "log_por_metadado",
    "C:/Oriun/08-dicionario/04_log_por_metadado.py"
)

registrar_log = mod_log.registrar_log

def formatar_nome_tabela(tabela, banco_destino):
    return f'"01-Cadastros".{tabela}' if banco_destino == "postgres" else tabela

def buscar_registro(cursor, tabela, campo_chave, valor_chave, banco_destino):
    nome_tabela = formatar_nome_tabela(tabela, banco_destino)
    cursor.execute(f"""
        SELECT * FROM {nome_tabela}
        WHERE {campo_chave} = ?
    """ if banco_destino == "sqlite" else f"""
        SELECT * FROM {nome_tabela}
        WHERE {campo_chave} = %s
    """, (valor_chave,))
    resultado = cursor.fetchone()
    if resultado:
        colunas = [desc[0] for desc in cursor.description]
        return dict(zip(colunas, resultado))
    return None

def detectar_alteracoes(registro_novo, registro_antigo, metadado):
    alteracoes = {}
    for campo, props in metadado["campos"].items():
        if props.get("sincronizar", False):
            novo = registro_novo.get(campo)
            antigo = registro_antigo.get(campo)
            if novo != antigo:
                alteracoes[campo] = {
                    "valor_antigo": antigo,
                    "valor_novo": novo
                }
    return alteracoes

def sincronizar_tabela(dados, cursor, conexao, metadado, nome_tabela, banco_destino):
    try:
        campo_chave = metadado["campo_chave"]
        nome_tabela_formatado = formatar_nome_tabela(nome_tabela, banco_destino)
        total = 0

        if dados and isinstance(dados[0], tuple):
            colunas = list(metadado["campos"].keys())
            dados = [dict(zip(colunas, r)) for r in dados]

        for registro in dados:
            valor_chave = registro.get(campo_chave)
            if not valor_chave:
                registrar_erro(f"[SYNC_06] ✖ Registro sem campo-chave '{campo_chave}'")
                continue

            registro_antigo = buscar_registro(cursor, nome_tabela, campo_chave, valor_chave, banco_destino)

            if registro_antigo:
                alteracoes = detectar_alteracoes(registro, registro_antigo, metadado)
                if alteracoes:
                    campos_update = ", ".join([
                        f"{campo} = ?" if banco_destino == "sqlite" else f"{campo} = %s"
                        for campo in alteracoes
                    ])
                    valores_update = [registro[campo] for campo in alteracoes]
                    valores_update.append(valor_chave)

                    cursor.execute(f"""
                        UPDATE {nome_tabela_formatado}
                        SET {campos_update}
                        WHERE {campo_chave} = ?
                    """ if banco_destino == "sqlite" else f"""
                        UPDATE {nome_tabela_formatado}
                        SET {campos_update}
                        WHERE {campo_chave} = %s
                    """, valores_update)

                    for campo in alteracoes:
                        registrar_log(nome_tabela, campo, valor_chave, metadado)
                else:
                    log_execucao(f"[SYNC_06] ⏸ Registro {valor_chave} já está atualizado.")
            else:
                campos_insert = []
                valores_insert = []
                placeholders = []

                for campo, props in metadado["campos"].items():
                    if campo in registro and registro[campo] is not None:
                        campos_insert.append(campo)
                        valores_insert.append(registro[campo])
                        placeholders.append("?" if banco_destino == "sqlite" else "%s")

                cursor.execute(f"""
                    INSERT INTO {nome_tabela_formatado}
                    ({', '.join(campos_insert)})
                    VALUES ({', '.join(placeholders)})
                """, valores_insert)

                log_execucao(f"[SYNC_06] ➕ Registro novo inserido: {valor_chave}")

            total += 1

        conexao.commit()
        log_execucao(f"[SYNC_06] ✔ Sincronismo concluído: {total} registros processados na tabela {nome_tabela}")

    except Exception as e:
        registrar_erro(f"[SYNC_06] ✖ Erro ao sincronizar tabela {nome_tabela}: {e}")
        conexao.rollback()
