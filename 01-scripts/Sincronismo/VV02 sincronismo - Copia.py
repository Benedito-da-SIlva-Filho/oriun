# ╔════════════════════════════════════════════════════════════════════╗
# ║               SCRIPTUM HONORIS — SINCRONISMO.py ORIUN              ║
# ║                                                                    ║
# ║  Sincronismo bidirecional entre SQLite e PostgreSQL               ║
# ║  Fluxo inverso agora sincroniza todas as tabelas dinamicamente    ║
# ║                                                                   ║
# ║  “NÓS SÓ INCLUÍMOS E ATUALIZAMOS. NÃO MUDAMOS E NEM APAGAMOS.”    ║
# ╚════════════════════════════════════════════════════════════════════╝

# Módulos para fluxo normal (SQLite → PostgreSQL)
from sync_01_backup_sqlite import executar_backup_sqlite
from sync_02_backup_postgres import executar_backup_postgres
from sync_03_leitura_sqlite import ler_dados_sqlite
from sync_04_transformacao_dados import transformar_dados
from sync_05_conexao_postgres import conectar_postgres
from sync_06_sincronismo_tabelas import sincronizar_tabela_propriedades

# Módulos para fluxo inverso (PostgreSQL → SQLite)
from sync_08_leitura_postgres import ler_todas_tabelas_postgres
from sync_04_transformacao_dados import transformar_dados_postgres
from sync_09_conexao_sqlite import conectar_sqlite
from sync_10_sincronismo_sqlite import sincronizar_sqlite_tabela

# Logs
from sync_07_logs import log_execucao, registrar_erro

def main(direcao="normal"):
    print("=== Iniciando sincronismo ===")
    log_execucao(f"[SINCRONISMO] 🔄 Início do processo de sincronismo ({direcao.upper()})")

    try:
        executar_backup_sqlite()
        executar_backup_postgres()

        if direcao == "normal":
            # Fluxo SQLite → PostgreSQL
            dados_brutos = ler_dados_sqlite()
            dados_tratados = transformar_dados(dados_brutos)

            conn, cursor = conectar_postgres()
            if conn and cursor:
                sincronizar_tabela_propriedades(dados_tratados, cursor, conn)
                log_execucao("[SINCRONISMO] ✔ Sincronismo concluído com sucesso (SQLite → PostgreSQL)")
            else:
                registrar_erro("[SINCRONISMO] ✖ Falha ao conectar ao PostgreSQL. Processo interrompido.")

        elif direcao == "inverso":
            # Fluxo PostgreSQL → SQLite
            conn_pg, cursor_pg = conectar_postgres()
            if conn_pg and cursor_pg:
                dados_por_tabela = ler_todas_tabelas_postgres(cursor_pg)

                cursor_sqlite, conn_sqlite = conectar_sqlite(r"C:\Oriun\03-banco\oriun_local.db")
                if cursor_sqlite and conn_sqlite:
                    for tabela, registros in dados_por_tabela.items():
                        try:
                            dados_tratados = transformar_dados_postgres(registros)

                            # 🔍 Verificação específica para a001_propriedades
                            if tabela == "a001_propriedades":
                                log_execucao(f"[DEBUG] Registros recebidos para {tabela}: {len(dados_tratados)}")
                                if dados_tratados:
                                    exemplo = dados_tratados[0]
                                    log_execucao(f"[DEBUG] Exemplo de registro: {exemplo}")
                                    if "a001_cod_propriedade" not in exemplo:
                                        log_execucao(f"[DEBUG] ⚠ Campo 'a001_cod_propriedade' ausente no registro")
                                else:
                                    log_execucao(f"[DEBUG] ⚠ Nenhum registro tratado para {tabela}")

                            sincronizar_sqlite_tabela(tabela, dados_tratados, cursor_sqlite, conn_sqlite)
                        except Exception as e:
                            registrar_erro(f"[SINCRONISMO] ✖ Erro ao sincronizar tabela {tabela}: {e}")
                    log_execucao("[SINCRONISMO] ✔ Sincronismo inverso concluído com sucesso (PostgreSQL → SQLite)")
                else:
                    registrar_erro("[SINCRONISMO] ✖ Falha ao conectar ao SQLite. Processo interrompido.")
            else:
                registrar_erro("[SINCRONISMO] ✖ Falha ao conectar ao PostgreSQL. Processo interrompido.")

        else:
            registrar_erro(f"[SINCRONISMO] ✖ Direção inválida: {direcao}")

    except Exception as e:
        registrar_erro(f"[SINCRONISMO] ✖ Erro inesperado no processo: {e}")

    print("=== Sincronismo concluído ===")

if __name__ == "__main__":
    # Altere para "inverso" se quiser executar PostgreSQL → SQLite
    main(direcao="inverso")
