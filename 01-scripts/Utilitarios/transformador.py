# +--------------------------------------------------------------------+
# ¦         SCRIPTUM HONORIS — TRANSFORMADOR.PY ORIUN                  ¦
# ¦                                                                    ¦
# ¦  Módulo responsável por padronizar dados antes do sincronismo      ¦
# ¦  Aplica regras do metadado, remove campos nulos e limpa strings    ¦
# ¦                                                                    ¦
# ¦  “TRANSFORMAR É PREPARAR PARA SER INCLUÍDO COM HONRA.”             ¦
# +--------------------------------------------------------------------+

def transformar_dados(dados, metadado):
    """
    Aplica transformação nos dados vindos do SQLite antes de enviar ao PostgreSQL.
    Remove campos não sincronizáveis, limpa strings e ignora nulos.
    """
    campos_validos = [campo for campo, props in metadado["campos"].items() if props.get("sincronizar", False)]
    dados_tratados = []

    for registro in dados:
        novo = {}
        for campo in campos_validos:
            valor = registro.get(campo)
            if valor is not None:
                if isinstance(valor, str):
                    valor = valor.strip()
                novo[campo] = valor
        dados_tratados.append(novo)

    return dados_tratados

def transformar_dados_postgres(dados, metadado):
    """
    Aplica transformação nos dados vindos do PostgreSQL antes de enviar ao SQLite.
    Remove campos não sincronizáveis, limpa strings e ignora nulos.
    """
    campos_validos = [campo for campo, props in metadado["campos"].items() if props.get("sincronizar", True)]
    dados_tratados = []

    for registro in dados:
        novo = {}
        for campo in campos_validos:
            valor = registro.get(campo)
            if valor is not None:
                if isinstance(valor, str):
                    valor = valor.strip()
                novo[campo] = valor
        dados_tratados.append(novo)

    return dados_tratados
