# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils\
# MODULO: backend\utils\especies.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-29 06:55 -03
# ATUALIZADO EM: 2026-09-29 06:55 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Tradutor UNICO de Especie do Orion (Sessao 082).
#
#     REGRA DE BENEDITO (Sessao 082): "nos arquivos gravamos
#     apenas BOV ou BUB; visualmente, para o usuario, usamos a
#     palavra completa". Ou seja:
#       - BANCO: sempre o CODIGO do catalogo (tb_4002_especie.
#         codigo) - "BOV", "BUB".
#       - TELA: sempre a DESCRICAO do catalogo - "Bovino",
#         "Bubalino".
#
#     O catalogo public.tb_4002_especie e a UNICA fonte (Regra
#     de Ouro #8) - nenhuma lista de especies escrita a mao em
#     outro arquivo. Motivo real: a GTA Manual gravava "BOVINO"
#     por extenso (lista fixa no codigo) e a Brincagem
#     Sequencial procurava esse texto na coluna codigo ("BOV") -
#     toda Brincagem de Compra ficava travada (Sessao 082).
#
#     FUNCOES:
#       carregar_especies()        -> lista de dicts {id, codigo,
#                                     descricao}, na ordem do
#                                     catalogo (para dropdowns).
#       codigo_da_especie(texto)   -> aceita "BOV", "BOVINO",
#                                     "Bovino", "bovino" e devolve
#                                     o codigo ("BOV"); None se
#                                     nao existir no catalogo.
#                                     Usado ao GRAVAR e ao ler
#                                     texto vindo de PDF/tela.
#       descricao_da_especie(cod)  -> "BOV" -> "Bovino"; se nao
#                                     achar, devolve o proprio
#                                     texto (nunca quebra a tela).
#       mapa_codigo_descricao()    -> {"BOV": "Bovino", ...} para
#                                     os templates.
#       codigos_validos()          -> ["BOV", "BUB"] para
#                                     validacao no servidor.
#
#     Todas aceitam a lista ja carregada (parametro especies)
#     para nao consultar o catalogo varias vezes na mesma tela.
#
#   v1.0.0: Criacao (Sessao 082).
# =========================================================

import unicodedata

from sqlalchemy import text

from backend.database import engine


# -------------------------------------------------------
# Funcao auxiliar: MAIUSCULO, sem acento e sem espacos - para
# comparar "Bovino", "BOVINO" e " bovino " como iguais.
# -------------------------------------------------------
def _normalizar(texto):
    if not texto:
        return ''
    sem_acento = unicodedata.normalize('NFKD', str(texto))
    sem_acento = ''.join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.upper().replace(' ', '')


# -------------------------------------------------------
# Funcao: le o catalogo publico (schema public) - lista de
# dicts simples, na ordem do id.
# -------------------------------------------------------
def carregar_especies():
    with engine.connect() as conn:
        linhas = conn.execute(text(
            'SELECT id, codigo, descricao FROM public.tb_4002_especie ORDER BY id'
        )).mappings().all()
    return [
        {'id': linha['id'], 'codigo': linha['codigo'], 'descricao': linha['descricao']}
        for linha in linhas
    ]


# -------------------------------------------------------
# Funcao: qualquer forma de escrita -> codigo do catalogo.
# -------------------------------------------------------
def codigo_da_especie(texto, especies=None):
    alvo = _normalizar(texto)
    if not alvo:
        return None
    for especie in (especies if especies is not None else carregar_especies()):
        if alvo in (_normalizar(especie['codigo']), _normalizar(especie['descricao'])):
            return especie['codigo']
    return None


# -------------------------------------------------------
# Funcao: codigo -> descricao (para mostrar na tela).
# -------------------------------------------------------
def descricao_da_especie(codigo, especies=None):
    codigo_certo = codigo_da_especie(codigo, especies)
    for especie in (especies if especies is not None else carregar_especies()):
        if especie['codigo'] == codigo_certo:
            return especie['descricao']
    return codigo or ''


# -------------------------------------------------------
# Funcao: {"BOV": "Bovino", ...} para os templates.
# -------------------------------------------------------
def mapa_codigo_descricao(especies=None):
    return {
        especie['codigo']: especie['descricao']
        for especie in (especies if especies is not None else carregar_especies())
    }


# -------------------------------------------------------
# Funcao: lista de codigos aceitos (validacao no servidor).
# -------------------------------------------------------
def codigos_validos(especies=None):
    return [especie['codigo'] for especie in (especies if especies is not None else carregar_especies())]

# =========================================================
# FIM DE ARQUIVO: backend\utils\especies.py
# =========================================================
