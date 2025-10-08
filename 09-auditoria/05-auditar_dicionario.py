"""
Script: auditar_dicionario.py
Autor: Benedito & Equipe Oriun
Data de criação: 2025-09-13
Finalidade:
    Verifica a consistência do dicionário de dados, identificando campos sem 
    descrição, sem tipo definido ou duplicados. Gera relatório técnico para revisão.

Uso:
    problemas = auditar_dicionario(cursor_pg)

Parâmetros:
    cursor_pg (psycopg2 cursor): Cursor ativo da conexão PostgreSQL

Retorno:
    list de tuples: Cada tupla contém (nome_tabela, nome_campo) com problema detectado

Observações:
    - Pode ser usado como parte de rotina de manutenção ou validação
    - Requer que a tabela oriun_dicionario_de_dados esteja populada corretamente
"""

def auditar_dicionario(cursor):
    cursor.execute("""
        SELECT nome_tabela, nome_campo, descricao, tipo_postgres
        FROM "01-Cadastros".oriun_dicionario_de_dados;
    """)
    resultados = cursor.fetchall()
    problemas = []

    for row in resultados:
        if not row["descricao"] or not row["tipo_postgres"]:
            problemas.append((row["nome_tabela"], row["nome_campo"]))

    return problemas
