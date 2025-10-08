# sync_07_logs.py
# O que esse módulo faz
# Cria dois arquivos de log:
# 	- execucao.log para registros normais
# 	- erros.log para falhas e exceções
#   - log_pg.txt → para eventos específicos do PostgreSQL
#   - log_sqlite.txt → para eventos específicos do SQLite
# Adiciona timestamp em cada linha
# Garante que os logs fiquem organizados na pasta logs dentro de sincronismo
# Em caso de falha no próprio log, imprime no console (sem travar o sistema)
# 
# Dica
# - Antes de rodar o sincronismo, certifique-se de que a pasta C:\Oriun\06-logs

# Funções originais mantidas — funcionamento preservado
from datetime import datetime
import os

def log_execucao(mensagem):
    _registrar_log(mensagem, r"C:\Oriun\06-logs\execucao.log")

def registrar_erro(mensagem):
    _registrar_log(mensagem, r"C:\Oriun\06-logs\erros.log")

def log_postgres(mensagem):
    _registrar_log(mensagem, r"C:\Oriun\06-logs\log_pg.txt")

def log_sqlite(mensagem):
    _registrar_log(mensagem, r"C:\Oriun\06-logs\log_sqlite.txt")

def _registrar_log(mensagem, caminho):
    try:
        pasta = os.path.dirname(caminho)
        if not os.path.exists(pasta):
            os.makedirs(pasta)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(caminho, "a", encoding="utf-8") as log:
            log.write(f"[{timestamp}] {mensagem}\n")

    except Exception as e:
        print(f"Erro ao registrar log em {caminho}: {e}")

# 🔄 Funções novas — para alterações por campo e conflitos

def log_alteracao_campo(id_registro, campo, valor_antigo, valor_novo, origem="desconhecida"):
    mensagem = (f"[ALTERAÇÃO] ID {id_registro} — campo '{campo}' alterado "
                f"de '{valor_antigo}' para '{valor_novo}' por origem '{origem}'")
    log_execucao(mensagem)

def log_conflito(id_registro, campo, valor_1, origem_1, valor_2, origem_2):
    mensagem = (f"[CONFLITO] ID {id_registro} — campo '{campo}' recebeu valores simultâneos: "
                f"'{valor_1}' ({origem_1}) vs '{valor_2}' ({origem_2}) — revisão necessária")
    registrar_erro(mensagem)
