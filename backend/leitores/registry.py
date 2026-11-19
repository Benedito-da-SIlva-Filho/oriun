# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\leitores
# MODULO: backend\leitores\registry.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-08-01 11:15 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Arquitetura plugavel por Estado/orgao emissor de e-GTA
#     (desenhada nas Sessoes 028/029). Este modulo NAO le o PDF
#     campo a campo - ele so decide QUAL leitor especializado
#     deve ler o documento, por auto-deteccao de uma
#     "assinatura" (um texto que so aquele orgao usa - hoje,
#     o dominio do site que aparece no rodape do documento).
#
#     Por que auto-deteccao e nao um dropdown pro usuario
#     escolher o Estado (decisao de Benedito, Sessao 029): se o
#     Produtor escolhe a opcao errada num dropdown, ele nao
#     hesita em dizer pro Produtor/Responsavel que "o Software
#     errou" - e o problema cai na conta da Consiste mesmo assim.
#     Auto-deteccao elimina esse erro de origem: o Produtor so
#     sobe o PDF, sem nenhuma decisao pra errar.
#
#     COMO ADICIONAR UM LEITOR NOVO (ex.: MT/INDEA, P-032):
#       1. Criar backend/leitores/leitor_mt_indea.py com uma
#          funcao publica ler(caminho_pdf) -> dict, devolvendo
#          as mesmas chaves que leitor_ms_iagro.ler() devolve
#          hoje (mesmo "contrato").
#       2. Importar o modulo novo aqui embaixo (import).
#       3. Adicionar uma linha no dicionario ASSINATURAS: chave
#          = nome interno do leitor, valor = tupla com (texto de
#          assinatura unico daquele orgao, funcao ler do leitor).
#     Nenhum outro arquivo do projeto (nem o router gta_compra.py)
#     precisa saber que um leitor novo existe - esse isolamento e
#     o proposito da arquitetura plugavel.
#
#     v1.0.0: Criacao do modulo (Sessao 029). Um unico leitor
#         registrado por enquanto: MS/IAGRO, assinatura
#         "iagro.ms.gov.br" (dominio que aparece no e-mail/rodape
#         de todo e-GTA emitido por aquele orgao - confirmado
#         contra documento real, GTA_Compra_MS.pdf, Serie
#         Q/515308).
# =========================================================

import pdfplumber

from backend.leitores import leitor_ms_iagro


# -------------------------------------------------------
# Cada entrada: nome interno do leitor -> (texto de assinatura
# unico daquele orgao, funcao ler(caminho_pdf) daquele leitor).
# A busca da assinatura e sempre em minusculas (case-insensitive)
# contra o texto integral extraido da 1a pagina do PDF.
# -------------------------------------------------------
ASSINATURAS = {
    'MS_IAGRO': ('iagro.ms.gov.br', leitor_ms_iagro.ler),
}


def _extrair_texto_primeira_pagina(caminho_pdf):
    """Abre o PDF e devolve o texto integral da 1a pagina.
    Usado SO para a auto-deteccao de assinatura (deteccao
    grosseira, so precisa achar uma palavra) - cada leitor
    especializado faz sua propria extracao detalhada, com
    coordenadas X/Y, para os campos de verdade."""
    with pdfplumber.open(caminho_pdf) as pdf:
        primeira_pagina = pdf.pages[0]
        return primeira_pagina.extract_text() or ''


def identificar_leitor(caminho_pdf):
    """Auto-detecta qual leitor especializado deve processar o
    PDF recebido, procurando a assinatura de cada orgao
    cadastrado em ASSINATURAS, no texto da 1a pagina. Devolve
    uma tupla (nome_leitor, funcao_ler) do primeiro leitor cuja
    assinatura for encontrada, ou (None, None) se nenhum orgao
    conhecido for reconhecido no documento."""
    texto = _extrair_texto_primeira_pagina(caminho_pdf).lower()

    for nome_leitor, (assinatura, funcao_ler) in ASSINATURAS.items():
        if assinatura.lower() in texto:
            return nome_leitor, funcao_ler

    return None, None


def ler_gta(caminho_pdf):
    """Ponto de entrada UNICO usado pelo router (gta_compra.py).
    Identifica automaticamente o leitor certo e ja devolve o
    dicionario de campos lidos, pronto para preencher a tela.

    Levanta ValueError com mensagem amigavel (endereçada ao
    usuario, "Sr. Usuário(a)...") em dois cenarios distintos,
    ambos tratados do mesmo jeito pelo router (reexibe o
    dropzone de upload com a mensagem):
      - nenhum orgao conhecido foi reconhecido no documento
        (levantado aqui mesmo, no registry);
      - o orgao FOI reconhecido, mas o leitor especializado nao
        conseguiu localizar algum campo obrigatorio dentro do
        documento (levantado dentro do proprio leitor, ex.:
        leitor_ms_iagro.ler() - o erro so "atravessa" este
        ponto de entrada sem ser interceptado)."""
    nome_leitor, funcao_ler = identificar_leitor(caminho_pdf)

    if funcao_ler is None:
        raise ValueError(
            'Sr. Usuário(a), não foi possível reconhecer este documento '
            'como uma e-GTA de um órgão emissor conhecido pelo Orion. '
            'Verifique se o arquivo enviado é o PDF correto da GTA.'
        )

    dados = funcao_ler(caminho_pdf)
    dados['orgao_emissor_identificado'] = nome_leitor
    return dados

# =========================================================
# FIM DE ARQUIVO: backend\leitores\registry.py
# =========================================================