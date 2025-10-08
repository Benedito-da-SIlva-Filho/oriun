# sync_04_transformacao_dados.py
# ╔════════════════════════════════════════════════════════════════════╗
# ║        SCRIPTUM HONORIS — TRANSFORMAÇÃO DE DADOS ORIUN           ║
# ║                                                                  ║
# ║  Este módulo aplica transformações nos dados vindos da origem    ║
# ║  (SQLite ou PostgreSQL), preparando-os para sincronismo.         ║
# ║                                                                  ║
# ║  Características:                                                ║
# ║  - Limpeza de texto, normalização de booleanos e datas           ║
# ║  - Baseado em metadados do dicionário de dados                   ║
# ║  - Validação semântica por campo obrigatório                     ║
# ║  - Registra logs com prefixo [SYNC_04]                           ║
# ║                                                                  ║
# ║  “NÓS SÓ INCLUÍMOS E ATUALIZAMOS. NÃO MUDAMOS E NEM APAGAMOS.”   ║
# ╚════════════════════════════════════════════════════════════════════╝

from sync_07_logs import log_execucao, registrar_erro
from importador import importar_modulo

# Carregamento dinâmico do validador semântico
mod_validacao = importar_modulo(
    "validar_registro",
    "C:/Oriun/08-dicionario/02-validar_registro_por_metadado.py"
)

validar_registro = mod_validacao.validar_registro

def transformar_dados(dados_brutos, metadado):
    """
    Transforma dados vindos do SQLite (lista de tuplas, dicts ou sqlite3.Row)
    Prepara para inserção no PostgreSQL com base no dicionário
    """
    try:
        dados_tratados = []

        # Diagnóstico do tipo recebido
        if dados_brutos:
            tipo = type(dados_brutos[0])
            log_execucao(f"[SYNC_04] 🧪 Tipo do primeiro registro recebido: {tipo}")

        # Conversão segura se os dados vierem como tupla
        if dados_brutos and isinstance(dados_brutos[0], tuple):
            colunas = list(metadado["campos"].keys())
            dados_brutos = [dict(zip(colunas, linha)) for linha in dados_brutos]
            log_execucao(f"[SYNC_04] ⚠ Dados convertidos de tupla para dict com base no metadado")

        for registro in dados_brutos:
            registro_dict = {}

            for campo, props in metadado["campos"].items():
                valor = registro[campo] if campo in registro else None

                # Normalização por tipo
                if props["tipo_postgres"] == "TEXT" and isinstance(valor, str):
                    valor = valor.strip().title()
                elif props["tipo_postgres"] == "BOOLEAN":
                    valor = bool(valor)
                elif props["tipo_postgres"] == "DATE" and not valor:
                    valor = "1900-01-01"

                registro_dict[campo] = valor

            # Validação semântica
            valido, mensagem = validar_registro(registro_dict, metadado)
            if not valido:
                registrar_erro(f"[SYNC_04] ✖ Registro inválido: {mensagem}")
                continue

            dados_tratados.append(registro_dict)

        log_execucao(f"[SYNC_04] ✔ Transformação direta concluída: {len(dados_tratados)} registros tratados")
        return dados_tratados

    except Exception as e:
        registrar_erro(f"[SYNC_04] ✖ Erro na transformação direta: {e}")
        return []

def transformar_dados_postgres(dados_brutos, metadado):
    """
    Transforma dados vindos do PostgreSQL (lista de dicts ou RealDictCursor)
    Prepara para inserção no SQLite com base no dicionário
    """
    try:
        dados_tratados = []

        for registro in dados_brutos:
            registro_dict = {}

            for campo, props in metadado["campos"].items():
                valor = registro[campo] if campo in registro else None

                # Normalização por tipo
                if props["tipo_sqlite"] == "TEXT" and isinstance(valor, str):
                    valor = valor.strip().title()
                elif props["tipo_sqlite"] == "INTEGER":
                    valor = int(valor) if valor is not None else 0
                elif props["tipo_sqlite"] == "DATE" and not valor:
                    valor = "1900-01-01"

                registro_dict[campo] = valor

            # Validação semântica
            valido, mensagem = validar_registro(registro_dict, metadado)
            if not valido:
                registrar_erro(f"[SYNC_04] ✖ Registro inválido: {mensagem}")
                continue

            dados_tratados.append(registro_dict)

        log_execucao(f"[SYNC_04] ✔ Transformação inversa concluída: {len(dados_tratados)} registros tratados")
        return dados_tratados

    except Exception as e:
        registrar_erro(f"[SYNC_04] ✖ Erro na transformação inversa: {e}")
        return []
