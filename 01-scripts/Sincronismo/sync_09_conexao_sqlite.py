# sync_09_conexao_sqlite.py
# ╔════════════════════════════════════════════════════════════════════╗
# ║         SCRIPTUM HONORIS — CONEXÃO COM BANCO SQLITE ORIUN         ║
# ║                                                                  ║
# ║  Estabelece conexão com o banco SQLite                           ║
# ║  Retorna cursor e conexão                                        ║
# ║  Registra logs com prefixo [SYNC_09]                             ║
# ║                                                                  ║
# ║  “NÓS SÓ INCLUÍMOS E ATUALIZAMOS. NÃO MUDAMOS E NEM APAGAMOS.”   ║
# ╚════════════════════════════════════════════════════════════════════╝

import sqlite3
import os
from sync_07_logs import log_execucao, registrar_erro

def conectar_sqlite(caminho_db=None):
    try:
        # Caminho padrão se nenhum for informado
        if caminho_db is None:
            caminho_db = "C:/Oriun/03-banco/oriun_local.db"

        # Verifica se o arquivo existe antes de tentar conectar
        if not os.path.isfile(caminho_db):
            registrar_erro(f"[SYNC_09] ✖ Arquivo SQLite não encontrado: {caminho_db}")
            return None, None

        conexao = sqlite3.connect(caminho_db)
        conexao.row_factory = sqlite3.Row  # 🔧 Retorna registros como dict
        cursor = conexao.cursor()

        log_execucao(f"[SYNC_09] ✔ Conexão SQLite estabelecida com {caminho_db}")
        return cursor, conexao

    except Exception as e:
        registrar_erro(f"[SYNC_09] ✖ Erro ao conectar ao SQLite: {e}")
        return None, None
