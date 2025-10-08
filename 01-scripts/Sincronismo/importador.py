"""
importador.py

Este módulo fornece uma função utilitária para importar dinamicamente arquivos Python
cujo nome ou caminho não seguem a convenção padrão de importação do Python — como
pastas ou arquivos que começam com números ou contêm caracteres especiais.

Função principal:
- importar_modulo(nome_alias, caminho_absoluto)

Parâmetros:
- nome_alias: Nome interno que será atribuído ao módulo importado.
- caminho_absoluto: Caminho completo do arquivo .py que será carregado.

Retorno:
- Um objeto de módulo carregado dinamicamente, permitindo acesso às suas funções e variáveis.

Uso típico:
Permite que projetos com estrutura legada (ex: '08-dicionario/01_carregar_metadados_pg.py')
sejam integrados ao Python sem necessidade de renomeação ou reestruturação.

Exemplo:
    modulo = importar_modulo("carregar_metadados_pg", "C:/Oriun/08-dicionario/01_carregar_metadados_pg.py")
    modulo.carregar_metadados_pg()

Ideal para projetos que precisam preservar nomenclaturas existentes por compatibilidade com
scripts, banco de dados, triggers ou documentação já consolidada.
"""



import importlib.util
import os

def importar_modulo(nome_alias, caminho_absoluto):
    spec = importlib.util.spec_from_file_location(nome_alias, caminho_absoluto)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
