"""
Script: sincronizar_por_metadado.py
Autor: Benedito & Equipe Oriun
Data de criação: 2025-09-13
Finalidade:
    Realiza sincronismo entre registros do SQLite e PostgreSQL com base nos campos 
    definidos como sincronizáveis no dicionário de dados. Atualiza o PostgreSQL 
    apenas se houver divergência.

Uso:
    sucesso = sincronizar_registro(reg_sqlite, reg_pg, metadado, cursor_pg, conn_pg, "a001_propriedades")

Parâmetros:
    reg_sqlite (dict): Registro vindo do banco local SQLite
    reg_pg (dict): Registro atual no PostgreSQL
    metadado (dict): Metadados da tabela
    cursor_pg (psycopg2 cursor): Cursor ativo da conexão PostgreSQL
    conn_pg (psycopg2 connection): Conexão ativa para commit
    nome_tabela (str): Nome da tabela a ser sincronizada

Retorno:
    bool: True se houve atualização, False se os dados já estavam sincronizados

Observações:
    - Utiliza UPDATE dinâmico com base nos campos divergentes
    - Requer que campo-chave esteja definido no dicionário
"""

def sincronizar_registro(registro_sqlite, registro_pg, metadado, cursor_pg, conn_pg, nome_tabela):
    campo_chave = metadado["campo_chave"]
    chave = registro_sqlite.get(campo_chave)

    atualizacoes = []
    valores = []

    for campo, props in metadado["campos"].items():
        if props["sincronizar"]:
            valor_pg = registro_pg.get(campo)
            valor_sqlite = registro_sqlite.get(campo)
            if valor_pg != valor_sqlite:
                atualizacoes.append(f"{campo} = %s")
                valores.append(valor_sqlite)

    if atualizacoes:
        sql = f"""
            UPDATE "01-Cadastros".{nome_tabela}
            SET {', '.join(atualizacoes)}
            WHERE {campo_chave} = %s;
        """
        cursor_pg.execute(sql, valores + [chave])
        conn_pg.commit()
        return True
    return False
