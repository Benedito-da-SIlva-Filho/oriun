# sync_04_transformacao_dados.py
# O que esse módulo faz
# Recebe os dados brutos do SQLite (lista de tuplas)
# Aplica transformações simples: limpeza de texto, conversão de booleanos, tratamento de datas
# Retorna uma lista de dicionários prontos para inserção no PostgreSQL
# Registra logs com prefixo [SYNC_04] para rastreamento claro
#  Em caso de erro, retorna lista vazia e registra no log de erro

from sync_07_logs import log_execucao, registrar_erro

def transformar_dados(dados_brutos):
    try:
        dados_tratados = []

        for registro in dados_brutos:
            # Exemplo: supondo que o registro seja uma tupla (id, nome, ativo, data_criacao)
            id_, nome, ativo, data_criacao = registro

            # Normalização de nome
            nome = nome.strip().title() if nome else "Desconhecido"

            # Conversão de campo booleano
            ativo = True if ativo == 1 else False

            # Formatação de data (se necessário)
            data_formatada = data_criacao if data_criacao else "1900-01-01"

            dados_tratados.append({
                "id": id_,
                "nome": nome,
                "ativo": ativo,
                "data_criacao": data_formatada
            })

        log_execucao(f"[SYNC_04] ✔ Transformação concluída: {len(dados_tratados)} registros tratados")
        return dados_tratados

    except Exception as e:
        registrar_erro(f"[SYNC_04] Erro ao transformar dados: {e}")
        return []
