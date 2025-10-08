# sync_01_backup_sqlite.py
# O que esse módulo faz
# Cria um backup do banco oriun_local.db com timestamp
# Salva na pasta C:\Oriun\07-bkp\sqlite\
# Garante que a pasta existe antes de salvar
# Registra logs com prefixo [SYNC_01] para facilitar rastreamento
from datetime import datetime
import os
from sync_07_logs import log_execucao, registrar_erro

def executar_backup_sqlite():
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        origem = r"C:\Oriun\03-banco\oriun_local.db"
        destino = fr"C:\Oriun\07-bkp\sqlite\oriun_local_bkp_{timestamp}.db"
        pasta_destino = os.path.dirname(destino)

        # Garante que a pasta de destino existe
        os.makedirs(pasta_destino, exist_ok=True)

        # Verifica se o arquivo de origem existe
        if not os.path.exists(origem):
            registrar_erro(f"[SYNC_01] ✖ Arquivo de origem não encontrado: {origem}")
            return

        # Executa a cópia binária
        with open(origem, "rb") as src, open(destino, "wb") as dst:
            dst.write(src.read())

        log_execucao(f"[SYNC_01] ✔ Backup SQLite realizado com sucesso: {destino}")

    except Exception as e:
        registrar_erro(f"[SYNC_01] ✖ Erro ao executar backup SQLite: {e}")