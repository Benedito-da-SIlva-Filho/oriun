# +------------------------------------------------------------------+
# ¦     SCRIPTUM HONORIS — LEITURA DE DADOS DO SQLITE ORIUN          ¦
# ¦                                                                  ¦
# ¦  Conecta ao banco oriun_local.db                                 ¦
# ¦  Executa SELECT na tabela informada                              ¦
# ¦  Retorna os dados como lista de dicionários                      ¦
# ¦  Registra logs com prefixo [SYNC_03]                             ¦
# ¦                                                                  ¦
# ¦  “LER É HONRAR A VERDADE QUE JÁ EXISTE.”                         ¦
# +------------------------------------------------------------------+

import sqlite3
from sync_07_logs import log_execucao, registrar_erro

def ler_dados_sqlite(nome_tabela):
    """
    Executa SELECT * na tabela informada e retorna os dados como lista de dicionários.
    """
    conexao = None
    try:
        caminho_db = r"C:\Oriun\03-banco\oriun_local.db"
        conexao = sqlite3.connect(caminho_db)
        conexao.row_factory = sqlite3.Row  # garante retorno como dict
        cursor = conexao.cursor()

        log_execucao(f"[SYNC_03] ?? Iniciando leitura da tabela {nome_tabela}")

        # Verifica se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (nome_tabela,))
        if not cursor.fetchone():
            registrar_erro(f"[SYNC_03] ? Tabela {nome_tabela} não existe no SQLite")
            return []

        cursor.execute(f"SELECT * FROM {nome_tabela}")
        dados = [dict(row) for row in cursor.fetchall()]

        if dados:
            colunas = list(dados[0].keys())
            log_execucao(f"[SYNC_03] ?? Colunas detectadas na tabela {nome_tabela}: {colunas}")
            log_execucao(f"[SYNC_03] ? Leitura concluída: {len(dados)} registros convertidos da tabela {nome_tabela}")
        else:
            log_execucao(f"[SYNC_03] ? Tabela {nome_tabela} está vazia")

        return dados

    except Exception as e:
        registrar_erro(f"[SYNC_03] ? Erro ao ler dados da tabela {nome_tabela}: {e}")
        return []

    finally:
        if conexao:
            conexao.close()

def obter_colunas_sqlite(nome_tabela):
    """
    Retorna a lista de nomes de colunas reais da tabela no SQLite.
    Útil para validar se o metadado está alinhado com a estrutura.
    """
    conexao = None
    try:
        caminho_db = r"C:\Oriun\03-banco\oriun_local.db"
        conexao = sqlite3.connect(caminho_db)
        cursor = conexao.cursor()

        cursor.execute(f"PRAGMA table_info({nome_tabela})")
        estrutura = cursor.fetchall()
        colunas = [linha[1] for linha in estrutura]

        log_execucao(f"[SYNC_03] ?? Estrutura real da tabela {nome_tabela}: {colunas}")
        return colunas

    except Exception as e:
        registrar_erro(f"[SYNC_03] ? Erro ao obter colunas da tabela {nome_tabela}: {e}")
        return []

    finally:
        if conexao:
            conexao.close()
