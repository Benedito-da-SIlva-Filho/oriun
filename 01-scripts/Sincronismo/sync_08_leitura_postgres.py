# sync_08_leitura_postgres.py
# ╔════════════════════════════════════════════════════════════════════╗
# ║      SCRIPTUM HONORIS — LEITURA UNIVERSAL POSTGRES AJUSTADA      ║
# ║                                                                  ║
# ║  Este módulo varre todos os schemas válidos no PostgreSQL        ║
# ║  e retorna os dados organizados por tabela.                      ║
# ║                                                                  ║
# ║  Retorno:                                                        ║
# ║  { "nome_tabela": [ {coluna: valor, ...}, ... ] }                ║
# ║                                                                  ║
# ║  “NÓS SÓ INCLUÍMOS E ATUALIZAMOS. NÃO MUDAMOS E NEM APAGAMOS.”   ║
# ╚════════════════════════════════════════════════════════════════════╝

from sync_07_logs import log_execucao, registrar_erro

def listar_schemas_validos(cursor):
    try:
        cursor.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
        """)
        schemas = [linha[0] for linha in cursor.fetchall() if linha and len(linha) > 0]
        log_execucao(f"[SYNC_08] ✔ {len(schemas)} schemas válidos encontrados")
        return schemas
    except Exception as e:
        registrar_erro(f"[SYNC_08] ✖ Erro ao listar schemas: {e}")
        return []

def listar_tabelas_por_schema(cursor, schema):
    try:
        cursor.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_name NOT LIKE 'pg_%'
              AND table_name NOT LIKE 'sql_%';
        """)
        resultados = cursor.fetchall()

        log_execucao(f"[DEBUG] Resultado bruto geral: {resultados}")

        tabelas = []
        for i, linha in enumerate(resultados):
            try:
                log_execucao(f"[DEBUG] Linha {i}: {linha}")
                if (
                    isinstance(linha, tuple)
                    and len(linha) == 2
                    and linha[0] == schema
                    and linha[1]
                ):
                    tabelas.append(str(linha[1]))
            except Exception as linha_erro:
                registrar_erro(f"[SYNC_08] ✖ Erro ao processar linha {i} do schema {schema}: {linha_erro}")

        log_execucao(f"[DEBUG] Schema {schema} — Tabelas encontradas: {tabelas}")
        return tabelas
    except Exception as e:
        registrar_erro(f"[SYNC_08] ✖ Erro ao listar tabelas do schema {schema}: {e}")
        return []

def ler_todas_tabelas_postgres(cursor):
    dados_por_tabela = {}
    schemas = listar_schemas_validos(cursor)

    for schema in schemas:
        tabelas = listar_tabelas_por_schema(cursor, schema)
        for tabela in tabelas:
            try:
                cursor.execute(f'SELECT * FROM "{schema}"."{tabela}"')
                registros = cursor.fetchall()

                # Verifica se há descrição válida
                if not cursor.description:
                    registrar_erro(f"[SYNC_08] ✖ cursor.description ausente para {schema}.{tabela}")
                    continue

                colunas = [desc[0] for desc in cursor.description]
                dados = [dict(zip(colunas, linha)) for linha in registros]

                dados_por_tabela[tabela] = dados

                log_execucao(f"[DEBUG] Tabela processada: {tabela}")
                log_execucao(f"[SYNC_08] ✔ {len(dados)} registros lidos da tabela {tabela}")
            except Exception as e:
                registrar_erro(f"[SYNC_08] ✖ Erro ao ler tabela {schema}.{tabela}: {e}")

    return dados_por_tabela
