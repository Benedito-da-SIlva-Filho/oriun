# sincronismo.py
# Módulo Principal de Sincronismo — Oriun
# 
# O que este módulo faz:
# - Orquestra a execução sequencial dos módulos de sincronismo (sync_01 a sync_07)
# - Realiza:
#     1. Backup do banco SQLite
#     2. Backup do banco PostgreSQL
#     3. Leitura dos dados no SQLite
#     4. Transformação dos dados conforme regras de negócio
#     5. Conexão com o banco PostgreSQL
#     6. Inserção/atualização dos dados tratados
#     7. Registro de logs de execução e falhas
#
#  Características:
#  - Usa try/except para capturar falhas inesperadas sem interromper o processo
#  - Registra logs em arquivos específicos para rastreabilidade
#  - Imprime mensagens no console para acompanhamento visual
#  - Garante modularidade e clareza na execução do sincronismo
#
#  Local recomendado:
#  C:\Oriun\01-scripts\sincronismo\sincronismo.py
#
#  Requisitos:
#  - Python 3.10+
#  - Módulos sync_01 a sync_07 corretamente implementados
#  - Estrutura de pastas conforme documentação do projeto

from sync_01_backup_sqlite import executar_backup_sqlite
from sync_02_backup_postgres import executar_backup_postgres
from sync_03_leitura_sqlite import ler_dados_sqlite
from sync_04_transformacao_dados import transformar_dados
from sync_05_conexao_postgres import conectar_postgres
from sync_06_sincronismo_tabelas import sincronizar_tabela_propriedades
from sync_07_logs import log_execucao, registrar_erro

def main():
    print("=== Iniciando sincronismo ===")
    log_execucao("[SINCRONISMO] 🔄 Início do processo de sincronismo")

    try:
        executar_backup_sqlite()
        executar_backup_postgres()

        dados_brutos = ler_dados_sqlite()
        dados_tratados = transformar_dados(dados_brutos)

        conn, cursor = conectar_postgres()
        if conn and cursor:
            sincronizar_tabela_propriedades(dados_tratados, cursor, conn)
            log_execucao("[SINCRONISMO] ✔ Sincronismo concluído com sucesso")
        else:
            registrar_erro("[SINCRONISMO] ✖ Falha ao conectar ao PostgreSQL. Processo interrompido.")

    except Exception as e:
        registrar_erro(f"[SINCRONISMO] ✖ Erro inesperado no processo: {e}")

    print("=== Sincronismo concluído ===")

if __name__ == "__main__":
    main()
