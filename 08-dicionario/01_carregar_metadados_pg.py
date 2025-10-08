"""
Script: carregar_metadados_pg.py
Autor: Benedito & Equipe Oriun
Data de criação: 2025-09-13
Finalidade: 
    Consulta o dicionário de dados armazenado no PostgreSQL e retorna os metadados 
    da tabela informada em formato estruturado (dict), contendo campo-chave, tipos, 
    obrigatoriedade, sincronismo e descrição.

Uso:
    metadado = carregar_metadados_pg(cursor_pg, "a001_propriedades")

Parâmetros:
    cursor_pg (psycopg2 cursor): Cursor ativo da conexão PostgreSQL
    nome_tabela (str): Nome da tabela cujos metadados devem ser carregados

Retorno:
    dict com estrutura:
    {
        "campo_chave": "nome_do_campo",
        "campos": {
            "campo1": {
                "tipo_postgres": "TEXT",
                "tipo_sqlite": "TEXT",
                "descricao": "...",
                "obrigatorio": True,
                "sincronizar": True,
                "fonte": "manual"
            },
            ...
        }
    }

Observações:
    - Requer que a tabela oriun_dicionario_de_dados esteja criada no schema "01-Cadastros"
    - Utiliza DictCursor para facilitar acesso por nome de campo
"""

from sync_07_logs import log_execucao, registrar_erro

def carregar_metadados_pg(cursor, nome_tabela):
    try:
        cursor.execute("""
            SELECT nome_campo, tipo_postgres, tipo_sqlite, descricao,
                   obrigatorio, campo_chave, sincronizar, fonte
            FROM "01-Cadastros".oriun_dicionario_de_dados
            WHERE nome_tabela = %s;
        """, (nome_tabela,))
        
        resultados = cursor.fetchall()
        if not resultados:
            registrar_erro(f"[METADADO] ✖ Nenhum metadado encontrado para a tabela {nome_tabela}")
            return {"campo_chave": None, "campos": {}}

        metadados = {"campo_chave": None, "campos": {}}

        for row in resultados:
            campo = row["nome_campo"]
            if row["campo_chave"]:
                metadados["campo_chave"] = campo
            metadados["campos"][campo] = {
                "tipo_postgres": row["tipo_postgres"],
                "tipo_sqlite": row["tipo_sqlite"],
                "descricao": row["descricao"],
                "obrigatorio": row["obrigatorio"],
                "sincronizar": row["sincronizar"],
                "fonte": row["fonte"]
            }

        log_execucao(f"[METADADO] 📘 Metadado carregado para {nome_tabela} com {len(metadados['campos'])} campos.")
        return metadados

    except Exception as e:
        registrar_erro(f"[METADADO] ✖ Erro ao carregar metadado da tabela {nome_tabela}: {e}")
        return {"campo_chave": None, "campos": {}}

def listar_tabelas_pg(cursor):
    """
    Retorna uma lista única de todas as tabelas mapeadas no dicionário de dados.
    """
    try:
        cursor.execute("""
            SELECT DISTINCT nome_tabela
            FROM "01-Cadastros".oriun_dicionario_de_dados
            ORDER BY nome_tabela;
        """)
        resultados = cursor.fetchall()
        tabelas = [row["nome_tabela"] for row in resultados]
        log_execucao(f"[METADADO] 📋 Tabelas disponíveis para sincronismo: {tabelas}")
        return tabelas
    except Exception as e:
        registrar_erro(f"[METADADO] ✖ Erro ao listar tabelas do dicionário: {e}")
        return []
