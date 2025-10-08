"""
Script: log_por_metadado.py
Autor: Benedito & Equipe Oriun
Data de criação: 2025-09-13
Finalidade:
    Gera logs refinados de sincronismo com base nas descrições dos campos 
    definidos no dicionário de dados. Facilita auditoria e rastreabilidade.

Uso:
    registrar_log("a001_propriedades", "a001_car", "123", metadado)

Parâmetros:
    tabela (str): Nome da tabela
    campo (str): Nome do campo sincronizado
    chave (str/int): Valor do campo-chave do registro
    metadado (dict): Metadados da tabela

Retorno:
    None (imprime log no console ou envia para sistema de log externo)

Observações:
    - Pode ser adaptado para salvar em arquivo ou banco de logs
    - Usa a descrição do campo para tornar o log mais legível
"""

def registrar_log(tabela, campo, chave, metadado):
    descricao = metadado["campos"][campo]["descricao"]
    print(f"[SYNC] Campo '{campo}' ({descricao}) sincronizado para registro {chave} na tabela {tabela}")
