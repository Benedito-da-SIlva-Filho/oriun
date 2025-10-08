"""
Script: validar_registro_por_metadado.py
Autor: Benedito & Equipe Oriun
Data de criação: 2025-09-13
Finalidade:
    Valida se um registro está completo com base nos campos obrigatórios definidos 
    no dicionário de dados. Retorna status booleano e mensagem de erro (se houver).

Uso:
    valido, mensagem = validar_registro(registro, metadado)

Parâmetros:
    registro (dict): Registro a ser validado (ex: vindo do SQLite)
    metadado (dict): Metadados da tabela, obtidos via carregar_metadados_pg

Retorno:
    tuple (bool, str): 
        - True se o registro está válido
        - False e mensagem explicativa se algum campo obrigatório estiver ausente

Observações:
    - Não valida tipos nem formatos, apenas presença de campos obrigatórios
    - Pode ser usado antes de sincronizar ou inserir registros
"""

def validar_registro(registro, metadado):
    for campo, props in metadado["campos"].items():
        if props["obrigatorio"] and not registro.get(campo):
            return False, f"Campo obrigatório '{campo}' ausente"
    return True, ""
