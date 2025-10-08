# +--------------------------------------------------------------------+
# ¦         SCRIPTUM HONORIS — LOGS DE SINCRONISMO ORIUN               ¦
# ¦                                                                    ¦
# ¦         sync_07_logs.py                                            ¦
# ¦                                                                    ¦
# ¦  Este módulo registra eventos de execução, erros, alterações e     ¦
# ¦  conflitos durante o sincronismo entre bancos.                     ¦
# ¦                                                                    ¦
# ¦  Características:                                                  ¦
# ¦  - Cria logs separados por tipo: execução, erro, PostgreSQL, etc.  ¦
# ¦  - Adiciona timestamp em cada linha                                ¦
# ¦  - Integra com o dicionário para registrar descrições de campos    ¦
# ¦                                                                    ¦
# ¦  Registra eventos, erros, alterações e conflitos entre bancos      ¦
# ¦  “LOGAR É HONRAR O QUE FOI FEITO, COM CLAREZA E VERDADE.”          ¦
# +--------------------------------------------------------------------+

from datetime import datetime
import os

# ?? Caminhos centralizados
LOG_EXECUCAO = r"C:\Oriun\06-logs\execucao.log"
LOG_ERROS = r"C:\Oriun\06-logs\erros.log"
LOG_PG = r"C:\Oriun\06-logs\log_pg.txt"
LOG_SQLITE = r"C:\Oriun\06-logs\log_sqlite.txt"

def log_execucao(mensagem):
    _registrar_log(mensagem, LOG_EXECUCAO, nivel="INFO")

def registrar_erro(mensagem):
    _registrar_log(mensagem, LOG_ERROS, nivel="ERRO")

def log_postgres(mensagem):
    _registrar_log(mensagem, LOG_PG, nivel="INFO")

def log_sqlite(mensagem):
    _registrar_log(mensagem, LOG_SQLITE, nivel="INFO")

def _registrar_log(mensagem, caminho, nivel="INFO"):
    try:
        pasta = os.path.dirname(caminho)
        if not os.path.exists(pasta):
            os.makedirs(pasta)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(caminho, "a", encoding="utf-8") as log:
            log.write(f"[{timestamp}] [{nivel}] {mensagem}\n")

    except Exception as e:
        print(f"Erro ao registrar log em {caminho}: {e}")

# ?? Funções refinadas

def log_alteracao_campo(id_registro, campo, valor_antigo, valor_novo, origem="desconhecida"):
    mensagem = (f"[ALTERAÇÃO] ID {id_registro} — campo '{campo}' alterado "
                f"de '{valor_antigo}' para '{valor_novo}' por origem '{origem}'")
    log_execucao(mensagem)

def log_conflito(id_registro, campo, valor_1, origem_1, valor_2, origem_2):
    mensagem = (f"[CONFLITO] ID {id_registro} — campo '{campo}' recebeu valores simultâneos: "
                f"'{valor_1}' ({origem_1}) vs '{valor_2}' ({origem_2}) — revisão necessária")
    registrar_erro(mensagem)

def registrar_log(tabela, campo, chave, metadado):
    descricao = metadado["campos"].get(campo, {}).get("descricao", "sem descrição")
    mensagem = (f"[SYNC] Tabela '{tabela}' — campo '{campo}' ({descricao}) "
                f"sincronizado para registro {chave}")
    log_execucao(mensagem)
