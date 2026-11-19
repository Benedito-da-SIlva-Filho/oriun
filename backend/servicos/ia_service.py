# -*- coding: utf-8 -*-
# ===================================================================
# PROJETO: Orion SISBOV
# PASTA: C:\orion\services\
# MODULO: servicos\ia_service.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 28/08/2026
# ATUALIZADO EM: 28/08/2026
# VERSAO: 1.0.0
# DESCRICAO:
#   - v1.0.0: Criacao do servico centralizado de IA. Concentra toda
#     comunicacao com a Anthropic em um unico ponto, para que rotas
#     Flask/FastAPI nunca falem diretamente com o provedor de IA.
#     Preparado para futura migracao de provedor (ex.: OpenRouter)
#     sem exigir alteracao nos controllers que o utilizam.
# ===================================================================

"""
Servico de IA do Orion.

Regra de ouro deste arquivo: NENHUM outro modulo do sistema deve importar
a biblioteca "anthropic" diretamente. Toda rota, todo router, todo script
que precisar de IA passa por AQUI. Se um dia trocarmos de provedor, o
unico arquivo que muda e este.
"""

import os
import base64
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from anthropic import Anthropic, APIError, APIConnectionError

# -------------------------------------------------------------------
# Carregamento de credenciais (.env)
# -------------------------------------------------------------------
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
# Modelo default configuravel via .env, para trocar de versao sem mexer
# em codigo. claude-sonnet-4-6 e o modelo de producao recomendado hoje
# para tarefas de texto e visao (custo/qualidade equilibrados).
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

if not ANTHROPIC_API_KEY:
    raise RuntimeError(
        "ANTHROPIC_API_KEY nao encontrada. Verifique se o arquivo .env "
        "existe na raiz do projeto e contem essa variavel."
    )

# Cliente unico, reaproveitado por todas as funcoes deste arquivo.
_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Mapa simples de extensao de arquivo -> media_type aceito pela API.
_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


# -------------------------------------------------------------------
# Funcao 1: texto simples
# -------------------------------------------------------------------
def processar_texto(prompt: str, contexto: Optional[str] = None) -> str:
    """
    Envia uma instrucao de texto simples para a IA e devolve a resposta
    como string pronta para uso.

    Parametros:
        prompt (str): a pergunta ou instrucao principal.
        contexto (str, opcional): texto de apoio (ex.: dados de uma GTA
            ja extraidos, um trecho de regra de negocio, etc.) que ajuda
            a IA a responder com mais precisao.

    Retorno:
        str: texto de resposta da IA.

    Exemplo:
        resposta = processar_texto(
            prompt="Resuma esse texto em uma frase.",
            contexto="A GTA numero 123456 foi emitida em Uberlandia..."
        )
    """
    mensagem_usuario = prompt if not contexto else f"{contexto}\n\n{prompt}"

    try:
        resposta = _client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": mensagem_usuario}
            ],
        )
    except APIConnectionError as erro:
        raise RuntimeError(
            "Nao foi possivel conectar a API da Anthropic. Verifique sua "
            "conexao com a internet."
        ) from erro
    except APIError as erro:
        raise RuntimeError(f"Erro retornado pela API da Anthropic: {erro}") from erro

    # A resposta vem em blocos (content). Para texto simples, juntamos
    # todos os blocos do tipo "text".
    partes_texto = [bloco.text for bloco in resposta.content if bloco.type == "text"]
    return "\n".join(partes_texto).strip()


# -------------------------------------------------------------------
# Funcao 2: extracao multimodal (imagem de GTA)
# -------------------------------------------------------------------
def extrair_dados_gta_imagem(caminho_imagem: str) -> dict:
    """
    Le uma imagem de GTA (foto, print ou pagina de PDF convertida em
    imagem), envia para a IA e pede a extracao estruturada dos dados
    em formato JSON.

    Parametros:
        caminho_imagem (str): caminho local do arquivo de imagem
            (.png, .jpg, .jpeg ou .webp).

    Retorno:
        dict: dados extraidos da GTA. Estrutura pensada como ponto de
        partida - deve ser ajustada junto com Benedito quando o modulo
        de leitura de GTA for desenhado de verdade (ainda nao definido
        no projeto Orion).

    Observacao importante:
        Esta funcao pede que a IA responda SOMENTE em JSON. Ainda assim,
        IA pode errar ou a imagem pode estar ilegivel - por isso o
        retorno inclui sempre a chave "sucesso" para o controller decidir
        o que fazer (pedir nova foto, cair para digitacao manual, etc.).
    """
    caminho = Path(caminho_imagem)

    if not caminho.exists():
        raise FileNotFoundError(f"Imagem nao encontrada: {caminho_imagem}")

    extensao = caminho.suffix.lower()
    media_type = _MEDIA_TYPES.get(extensao)
    if not media_type:
        raise ValueError(
            f"Extensao '{extensao}' nao suportada. Use: "
            f"{', '.join(_MEDIA_TYPES.keys())}"
        )

    imagem_base64 = base64.standard_b64encode(caminho.read_bytes()).decode("utf-8")

    instrucao = """
Voce esta vendo a imagem de uma GTA (Guia de Transito Animal) brasileira.
Extraia os dados visiveis e responda APENAS com um JSON valido, sem texto
antes ou depois, seguindo exatamente este formato:

{
  "sucesso": true ou false,
  "numero_gta": "string ou null",
  "uf_gta": "string (sigla) ou null",
  "serie_gta": "string (1 letra) ou null",
  "data_emissao": "DD/MM/AAAA ou null",
  "propriedade_origem": "string ou null",
  "propriedade_destino": "string ou null",
  "quantidade_animais": numero inteiro ou null,
  "observacoes": "qualquer coisa relevante que nao se encaixe acima, ou null"
}

Se algum campo nao estiver legivel ou nao existir na imagem, use null nesse
campo especifico - nao invente valores. Se a imagem nao parecer ser uma GTA,
responda com "sucesso": false e explique o motivo em "observacoes".
""".strip()

    try:
        resposta = _client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": imagem_base64,
                            },
                        },
                        {"type": "text", "text": instrucao},
                    ],
                }
            ],
        )
    except APIConnectionError as erro:
        raise RuntimeError(
            "Nao foi possivel conectar a API da Anthropic. Verifique sua "
            "conexao com a internet."
        ) from erro
    except APIError as erro:
        raise RuntimeError(f"Erro retornado pela API da Anthropic: {erro}") from erro

    texto_resposta = "\n".join(
        bloco.text for bloco in resposta.content if bloco.type == "text"
    ).strip()

    import json

    try:
        dados = json.loads(texto_resposta)
    except json.JSONDecodeError:
        # A IA nao respeitou o formato JSON. Devolvemos um retorno
        # padronizado de falha, em vez de deixar o controller quebrar.
        return {
            "sucesso": False,
            "numero_gta": None,
            "uf_gta": None,
            "serie_gta": None,
            "data_emissao": None,
            "propriedade_origem": None,
            "propriedade_destino": None,
            "quantidade_animais": None,
            "observacoes": "A IA nao retornou um JSON valido. Resposta bruta: "
            + texto_resposta[:300],
        }

    return dados


# ===================================================================
# FIM DE ARQUIVO: servicos\ia_service.py
# ===================================================================