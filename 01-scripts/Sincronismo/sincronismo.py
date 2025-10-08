# +--------------------------------------------------------------------+
# ¦               SCRIPTUM HONORIS — SINCRONISMO.py ORIUN              ¦
# ¦                                                                    ¦
# ¦  Sincronismo bidirecional entre SQLite e PostgreSQL                ¦
# ¦  Fluxo inteligente compara datas e atualiza o lado mais antigo     ¦
# ¦  Baseado em metadados do dicionário de dados                       ¦
# ¦                                                                    ¦
# ¦  “NÓS SÓ INCLUÍMOS E ATUALIZAMOS. NÃO MUDAMOS E NEM APAGAMOS.”     ¦
# +--------------------------------------------------------------------+

from sync_01_backup_sqlite import executar_backup_sqlite
from sync_02_backup_postgres import executar_backup_postgres
from sync_03_leitura_sqlite import ler_dados_sqlite, obter_colunas_sqlite
from sync_04_transformacao_dados import transformar_dados, transformar_dados_postgres
from sync_05_conexao_postgres import conectar_postgres
from sync_06_sincronismo_tabelas import sincronizar_tabela
from sync_08_leitura_postgres import ler_todas_tabelas_postgres
from sync_09_conexao_sqlite import conectar_sqlite
from sync_10_sincronismo_sqlite import sincronizar_sqlite_tabela
from sync_07_logs import log_execucao, registrar_erro
from importador import importar_modulo

mod_dicionario = importar_modulo(
    "carregar_metadados_pg",
    "C:/Oriun/08-dicionario/01_carregar_metadados_pg.py"
)

def validar_estrutura(tabela, metadado):
    colunas_reais = obter_colunas_sqlite(tabela)
    campos_metadado = list(metadado["campos"].keys())

    log_execucao(f"[VALIDAÇÃO] 📘 Metadado define campos: {campos_metadado}")
    log_execucao(f"[VALIDAÇÃO] 📗 SQLite possui colunas: {colunas_reais}")

    faltando = [campo for campo in campos_metadado if campo not in colunas_reais]
    extras = [col for col in colunas_reais if col not in campos_metadado]

    if faltando:
        registrar_erro(f"[VALIDAÇÃO] ⚠ Campos no metadado ausentes na tabela {tabela}: {faltando}")
        return False
    if extras:
        log_execucao(f"[VALIDAÇÃO] ℹ Colunas no SQLite não mapeadas no metadado: {extras}")
    return True

def converter_tuplas_para_dicts(dados, metadado):
    colunas = list(metadado["campos"].keys())
    return [dict(zip(colunas, linha)) for linha in dados]

def sincronismo_bidirecional():
    conn_pg, cursor_pg = conectar_postgres()
    if not (conn_pg and cursor_pg):
        registrar_erro("[SINCRONISMO] ✖ Falha ao conectar ao PostgreSQL. Processo interrompido.")
        return

    cursor_sqlite, conn_sqlite = conectar_sqlite(r"C:/Oriun/03-banco/oriun_local.db")
    if not (cursor_sqlite and conn_sqlite):
        registrar_erro("[SINCRONISMO] ✖ Falha ao conectar ao SQLite. Processo interrompido.")
        return

    tabelas = mod_dicionario.listar_tabelas_pg(cursor_pg)

    for tabela in tabelas:
        try:
            metadado = mod_dicionario.carregar_metadados_pg(cursor_pg, tabela)
            if not validar_estrutura(tabela, metadado):
                continue

            campos = list(metadado["campos"].keys())
            pk = metadado["chave_primaria"]
            campo_data = "a001_data_de_movimentacao"

            # Leitura dos dados
            cursor_sqlite.execute(f"SELECT {', '.join(campos)} FROM {tabela}")
            dados_sqlite = {row[pk]: dict(row) for row in cursor_sqlite.fetchall()}

            cursor_pg.execute(f'SELECT {", ".join(campos)} FROM "01-Cadastros".{tabela}')
            dados_pg = {row[pk]: dict(row) for row in cursor_pg.fetchall()}

            # Sincronismo por data
            for chave in set(dados_sqlite.keys()) & set(dados_pg.keys()):
                registro_sqlite = dados_sqlite[chave]
                registro_pg = dados_pg[chave]

                data_sqlite = registro_sqlite.get(campo_data)
                data_pg = registro_pg.get(campo_data)

                if not data_sqlite or not data_pg:
                    log_execucao(f"[SINCRONISMO] ⚠ PK {chave} sem campo de data. Ignorado.")
                    continue

                if data_sqlite > data_pg:
                    sincronizar_tabela([registro_sqlite], cursor_pg, conn_pg, metadado, tabela, banco_destino="postgres")
                    log_execucao(f"[SINCRONISMO] 🔁 PK {chave} atualizado no PostgreSQL com dados do SQLite")
                elif data_pg > data_sqlite:
                    sincronizar_sqlite_tabela(tabela, [registro_pg], cursor_sqlite, conn_sqlite, metadado)
                    log_execucao(f"[SINCRONISMO] 🔁 PK {chave} atualizado no SQLite com dados do PostgreSQL")
                else:
                    log_execucao(f"[SINCRONISMO] ⏸ PK {chave} já está sincronizado")

        except Exception as e:
            registrar_erro(f"[SINCRONISMO] ✖ Erro ao sincronizar tabela {tabela}: {e}")

def sincronismo_normal():
    conn_pg, cursor_pg = conectar_postgres()
    if not (conn_pg and cursor_pg):
        registrar_erro("[SINCRONISMO] ✖ Falha ao conectar ao PostgreSQL. Processo interrompido.")
        return

    tabelas = mod_dicionario.listar_tabelas_pg(cursor_pg)

    for tabela in tabelas:
        try:
            dados_brutos = ler_dados_sqlite(tabela)
            metadado = mod_dicionario.carregar_metadados_pg(cursor_pg, tabela)

            if not validar_estrutura(tabela, metadado):
                continue

            if dados_brutos and isinstance(dados_brutos[0], tuple):
                dados_brutos = converter_tuplas_para_dicts(dados_brutos, metadado)
                log_execucao(f"[SINCRONISMO] ⚠ Conversão aplicada em {tabela}")

            dados_tratados = transformar_dados(dados_brutos, metadado)
            sincronizar_tabela(dados_tratados, cursor_pg, conn_pg, metadado, tabela, banco_destino="postgres")
            log_execucao(f"[SINCRONISMO] ✔ Tabela {tabela} sincronizada com sucesso (SQLite → PostgreSQL)")

        except Exception as e:
            registrar_erro(f"[SINCRONISMO] ✖ Erro ao sincronizar tabela {tabela}: {e}")

def sincronismo_inverso():
    conn_pg, cursor_pg = conectar_postgres()
    if not (conn_pg and cursor_pg):
        registrar_erro("[SINCRONISMO] ✖ Falha ao conectar ao PostgreSQL. Processo interrompido.")
        return

    dados_por_tabela = ler_todas_tabelas_postgres(cursor_pg)
    cursor_sqlite, conn_sqlite = conectar_sqlite(r"C:/Oriun/03-banco/oriun_local.db")

    if not (cursor_sqlite and conn_sqlite):
        registrar_erro("[SINCRONISMO] ✖ Falha ao conectar ao SQLite. Processo interrompido.")
        return

    for tabela, registros in dados_por_tabela.items():
        try:
            metadado = mod_dicionario.carregar_metadados_pg(cursor_pg, tabela)
            dados_tratados = transformar_dados_postgres(registros, metadado)
            sincronizar_sqlite_tabela(tabela, dados_tratados, cursor_sqlite, conn_sqlite, metadado)
            log_execucao(f"[SINCRONISMO] ✔ Tabela {tabela} sincronizada com sucesso (PostgreSQL → SQLite)")
        except Exception as e:
            registrar_erro(f"[SINCRONISMO] ✖ Erro ao sincronizar tabela {tabela}: {e}")

def main(direcao="inteligente"):
    print("=== Iniciando sincronismo ===")
    log_execucao(f"[SINCRONISMO] 🔄 Início do processo de sincronismo ({direcao.upper()})")

    try:
        executar_backup_sqlite()
        executar_backup_postgres()

        if direcao == "normal":
            sincronismo_normal()
        elif direcao == "inverso":
            sincronismo_inverso()
        elif direcao == "inteligente":
            sincronismo_bidirecional()
        else:
            registrar_erro(f"[SINCRONISMO] ✖ Direção inválida: {direcao}")

    except Exception as e:
        registrar_erro(f"[SINCRONISMO] ✖ Erro inesperado no processo: {e}")

    print("=== Sincronismo concluído ===")
    log_execucao("[SINCRONISMO] ✅ Processo concluído com sucesso.")
