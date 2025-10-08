# +------------------------------------------------------------------+
# ¦  SCRIPTUM HONORIS — sync_bidirecional_tabelas.py                 ¦
# ¦                                                                  ¦
# ¦  Finalidade:                                                     ¦
# ¦  Este módulo realiza o sincronismo de registros entre bancos     ¦
# ¦  SQLite e PostgreSQL, com suporte bidirecional e controle        ¦
# ¦  refinado por metadado.                                          ¦
# ¦                                                                  ¦
# ¦  Características principais:                                     ¦
# ¦  • Sincronismo direto (SQLite ? PostgreSQL)                      ¦
# ¦  • Sincronismo inverso (PostgreSQL ? SQLite)                     ¦
# ¦  • Atualização seletiva campo a campo                            ¦
# ¦  • Inserção de novos registros quando não encontrados            ¦
# ¦  • Uso de metadado para definir chave primária e campos ativos   ¦
# ¦  • Compatível com múltiplas tabelas e estruturas                 ¦
# ¦  • Logs refinados por campo e operação                           ¦
# ¦                                                                  ¦
# ¦  Parâmetros esperados:                                           ¦
# ¦  • dados: lista de registros transformados                       ¦
# ¦  • cursor: conexão ativa com banco de destino                    ¦
# ¦  • conexao: objeto de transação para commit/rollback             ¦
# ¦  • metadado: dicionário com estrutura da tabela                  ¦
# ¦  • nome_tabela: nome da tabela alvo                              ¦
# ¦  • banco_destino: "postgres" ou "sqlite"                         ¦
# ¦                                                                  ¦
# ¦  Exemplo de uso:                                                 ¦
# ¦  sincronizar_tabela(dados, cursor, conexao, metadado,            ¦
# ¦                      nome_tabela="a001_propriedades",            ¦
# ¦                      banco_destino="sqlite")                     ¦
# ¦                                                                  ¦
# ¦  “SINCRONIZAR É HONRAR O ESTADO MAIS RECENTE DA VERDADE.”        ¦
# +------------------------------------------------------------------+

from sync_06_sincronismo_tabelas import sincronizar_tabela

# Simulação de dados vindos do PostgreSQL
dados_postgres = [{
    "a001_cod_propriedade": 6,
    "a001_car": "PG666666",
    "a001_data_de_movimentacao": "2025-09-13 23:55:00"
}]

# Metadado simulado
metadado = {
    "campo_chave": "a001_cod_propriedade",
    "campos": {
        "a001_cod_propriedade": {"sincronizar": False},
        "a001_car": {"sincronizar": True},
        "a001_data_de_movimentacao": {"sincronizar": True}
    }
}

# Conexão com SQLite
import sqlite3
conexao_sqlite = sqlite3.connect("banco_local.sqlite")
cursor_sqlite = conexao_sqlite.cursor()

# Execução do sincronismo inverso
sincronizar_tabela(
    dados=dados_postgres,
    cursor=cursor_sqlite,
    conexao=conexao_sqlite,
    metadado=metadado,
    nome_tabela="a001_propriedades",
    banco_destino="sqlite"
)
