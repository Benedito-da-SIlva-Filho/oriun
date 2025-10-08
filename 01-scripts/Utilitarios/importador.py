
# +--------------------------------------------------------------------+
# ¦         SCRIPTUM HONORIS — IMPORTADOR.PY ORIUN                     ¦
# ¦                                                                    ¦
# ¦  Módulo utilitário para importar scripts e metadados externos      ¦
# ¦  Permite carregamento dinâmico de módulos por caminho absoluto     ¦
# ¦                                                                    ¦
# ¦  “IMPORTAR É TRAZER CONHECIMENTO PARA DENTRO, COM PROPÓSITO.”      ¦
# +--------------------------------------------------------------------+

import importlib.util
import os

def importar_modulo(nome_modulo, caminho_arquivo):
    """
    Importa dinamicamente um módulo Python a partir de um caminho absoluto.

    Parâmetros:
    - nome_modulo: nome simbólico para o módulo
    - caminho_arquivo: caminho completo do arquivo .py

    Retorna:
    - módulo importado, pronto para uso
    """
    try:
        if not os.path.exists(caminho_arquivo):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

        spec = importlib.util.spec_from_file_location(nome_modulo, caminho_arquivo)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo

    except Exception as e:
        print(f"? Erro ao importar módulo '{nome_modulo}': {e}")
        return None
