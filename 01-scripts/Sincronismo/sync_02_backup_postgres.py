# sync_02_backup_postgres.py
# ╔════════════════════════════════════════════════════════════════════╗
# ║     SCRIPTUM HONORIS — BACKUP DO POSTGRES ORIUN_DEV              ║
# ║                                                                  ║
# ║  Este módulo gera um backup do banco oriun_dev usando pg_dump    ║
# ║  Salva o arquivo com timestamp na pasta C:\Oriun\07-bkp\postgres ║
# ║  Cria a pasta se ela não existir                                 ║
# ║  Registra logs de sucesso ou erro com prefixo [SYNC_02]          ║
# ║                                                                  ║
# ║  “BACKUP É O ATO DE HONRAR O PASSADO PARA PROTEGER O FUTURO.”    ║
# ╚════════════════════════════════════════════════════════════════════╝

from datetime import datetime
import os
from sync_07_logs import log_execucao, registrar_erro

def executar_backup_postgres():
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pasta_destino = r"C:\Oriun\07-bkp\postgres"
        bkp_path = os.path.join(pasta_destino, f"oriun_dev_bkp_{timestamp}.backup")

        # Garante que a pasta existe
        os.makedirs(pasta_destino, exist_ok=True)

        # Comando pg_dump
        comando = f'pg_dump -U postgres -h localhost -p 5432 -F c -b -v -f "{bkp_path}" oriun_dev'
        resultado = os.system(comando)

        if resultado == 0:
            log_execucao(f"[SYNC_02] ✔ Backup PostgreSQL realizado com sucesso: {bkp_path}")
        else:
            registrar_erro(f"[SYNC_02] ✖ Falha ao executar backup PostgreSQL. Código de saída: {resultado}")

    except Exception as e:
        registrar_erro(f"[SYNC_02] ✖ Erro ao executar backup PostgreSQL: {e}")
