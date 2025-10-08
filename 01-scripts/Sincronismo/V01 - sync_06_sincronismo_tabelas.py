# sync_06_sincronismo_tabelas.py
# O que esse módulo faz
# Recebe os dados transformados (lista de dicionários)
# Aplica INSERT ... ON CONFLICT para evitar duplicidade
# Atualiza registros existentes com os novos dados
# Usa commit() e rollback() para garantir integridade
# Registra logs com prefixo [SYNC_06] para rastreamento claro
# 
# Observações
# A chave de conflito usada é id - ajuste conforme a estrutura da sua tabela
# O nome da tabela pode ser alterado via parâmetro tabela_destino
# Se quiser sincronizar outras tabelas, podemos duplicar essa função com ajustes específicos

def sincronizar_tabela_propriedades(dados, cursor, conexao, tabela_destino="a001_propriedades"):
    try:
        total = 0
        for registro in dados:
            cursor.execute(f"""
                INSERT INTO {tabela_destino} (id, nome, ativo, data_criacao)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    nome = EXCLUDED.nome,
                    ativo = EXCLUDED.ativo,
                    data_criacao = EXCLUDED.data_criacao
            """, (
                registro["id"],
                registro["nome"],
                registro["ativo"],
                registro["data_criacao"]
            ))
            total += 1

        conexao.commit()
        from sync_07_logs import log_execucao
        log_execucao(f"[SYNC_06] ✔ Sincronismo concluído: {total} registros aplicados na tabela {tabela_destino}")

    except Exception as e:
        from sync_07_logs import registrar_erro
        registrar_erro(f"[SYNC_06] Erro ao sincronizar tabela {tabela_destino}: {e}")
        conexao.rollback()
