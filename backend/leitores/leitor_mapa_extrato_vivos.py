# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\Orion\backend\leitores
# MODULO: backend\leitores\leitor_mapa_extrato_vivos.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-17 18:09 -03
# ATUALIZADO EM: 2026-11-18 20:00 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     CARGA de animais - leitor do PDF "Extrato de Animais Vivos" do MAPA (SISBOV).
#     FUNCAO PURA: so le o arquivo e devolve a lista padrao. NAO usa banco, NAO usa Flask e NAO
#     valida regra de negocio (DV, raca, datas, duplicados: isso e da etapa de Validacao/Previa).
#     Texto 100% extraivel (sem OCR). Repete cabecalho e rodape a cada pagina; o leitor ignora o que
#     nao for linha de animal.
#
#     LISTA PADRAO (o "contrato" que TODOS os leitores da Carga devolvem: Excel, TXT, curral etc.):
#       ler(caminho_pdf) -> dict com as chaves:
#         'formato'         texto fixo do leitor ('MAPA_EXTRATO_VIVOS')
#         'cabecalho'       dict: certificadora, propriedade_nome, nirf, cod_propriedade, municipio, uf,
#                           produtor_nome, produtor_documento (so digitos), total_femea, total_macho,
#                           emitido_em, paginas (todos podem vir None se nao achados)
#         'animais'         lista de dict, na ordem do arquivo: linha, pagina, sisbov (texto), nascimento (date
#                           ou None), nascimento_texto, raca_nome, sexo ('MACHO'/'FEMEA' ou None), sexo_texto,
#                           data_inclusao (date ou None), data_inclusao_texto
#         'linhas_nao_lidas' lista de dict (pagina, texto): linha que parece animal (comeca com numero grande)
#                           mas nao bateu no formato. NUNCA e descartada em silencio: vai para a Previa.
#     "Invent." (S/N) e lido e ignorado, por decisao do Benedito (17/11/2026).
#     Data impossivel (ex.: 31/02/2020) vira None, com o texto original guardado; a Validacao barra.
#
#   v1.1.0: BND/Fazenda (18/11/2026): NOVA funcao ler_partes(caminho) - o Extrato da Propriedade pode trazer varios Produtores, cada um
#           numa parte (a parte comeca na linha "Nome: ... CPF/CNPJ: ..."). Devolve uma lista de partes, cada uma no mesmo formato
#           de ler() (cabecalho, animais, linhas_nao_lidas). ler() NAO mudou (a Carga continua igual).
#   v1.0.0: Criacao (Carga, 17/11/2026). Testado com EXTRATO DE VIVOS.pdf (1.244 animais, 31 F, 1.213 M).
# =========================================================

import re
from datetime import date

import pdfplumber

FORMATO = 'MAPA_EXTRATO_VIVOS'

# Linha de animal: SISBOV(15) Nascimento Raca(1+ palavras) Sexo Inclusao [Invent S/N, opcional e ignorado].
_RE_ANIMAL = re.compile(
    r'^(?P<sisbov>\d{15})\s+(?P<nasc>\d{2}/\d{2}/\d{4})\s+(?P<raca>.+?)\s+'
    r'(?P<sexo>Macho|F[eê]mea)\s+(?P<incl>\d{2}/\d{2}/\d{4})(?:\s+[SN])?\s*$',
    re.IGNORECASE,
)
# Parece linha de animal (comeca com numero grande) - para nao perder em silencio o que nao bateu.
_RE_PARECE_ANIMAL = re.compile(r'^\d{10,}\b')

_RE_CERTIFICADORA = re.compile(r'Entidade Certificadora:[ \t]*([^\n]+)')
_RE_PROPRIEDADE   = re.compile(r'Propriedade:\s*(.+?)\s+Nirf\s*/\s*Incra:\s*(\S+)\s+C[oó]d\.\s*Propriedade:\s*(\S+)', re.IGNORECASE)
_RE_MUNICIPIO     = re.compile(r'Munic[ií]pio:\s*(.+?)\s+UF:\s*([A-Za-z]{2})')
_RE_PRODUTOR      = re.compile(r'Nome:\s*(.+?)\s+CPF\s*/\s*CNPJ:\s*(\S+)', re.IGNORECASE)
_RE_TOTAIS        = re.compile(r'Total F[eê]mea:\s*(\d+)\s+Total Macho:\s*(\d+)', re.IGNORECASE)
_RE_RODAPE        = re.compile(r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})\s+P[aá]gina\s+(\d+)\s+de\s+(\d+)')


def _data(texto):
    """dd/mm/aaaa -> date, ou None se a data for impossivel (ex.: 31/02/2020)."""
    try:
        d, m, a = texto.split('/')
        return date(int(a), int(m), int(d))
    except (ValueError, AttributeError):
        return None


def _sexo(texto):
    t = (texto or '').strip().lower()
    if t == 'macho':
        return 'MACHO'
    if t in ('fêmea', 'femea'):
        return 'FEMEA'
    return None


def _ler_cabecalho(texto_pagina1):
    cab = {
        'certificadora': None, 'propriedade_nome': None, 'nirf': None, 'cod_propriedade': None,
        'municipio': None, 'uf': None, 'produtor_nome': None, 'produtor_documento': None,
        'total_femea': None, 'total_macho': None, 'emitido_em': None, 'paginas': None,
    }
    m = _RE_CERTIFICADORA.search(texto_pagina1)
    if m:
        cab['certificadora'] = m.group(1).strip()
    m = _RE_PROPRIEDADE.search(texto_pagina1)
    if m:
        cab['propriedade_nome'], cab['nirf'], cab['cod_propriedade'] = m.group(1), m.group(2), m.group(3)
    m = _RE_MUNICIPIO.search(texto_pagina1)
    if m:
        cab['municipio'], cab['uf'] = m.group(1), m.group(2).upper()
    m = _RE_PRODUTOR.search(texto_pagina1)
    if m:
        cab['produtor_nome'] = m.group(1)
        cab['produtor_documento'] = re.sub(r'\D', '', m.group(2))
    m = _RE_TOTAIS.search(texto_pagina1)
    if m:
        cab['total_femea'], cab['total_macho'] = int(m.group(1)), int(m.group(2))
    m = _RE_RODAPE.search(texto_pagina1)
    if m:
        cab['emitido_em'], cab['paginas'] = m.group(1), int(m.group(3))
    return cab


def ler(caminho_pdf):
    """Le o Extrato de Animais Vivos do MAPA e devolve a lista padrao (ver DESCRICAO)."""
    animais = []
    nao_lidas = []
    cabecalho = None
    with pdfplumber.open(caminho_pdf) as pdf:
        for numero_pagina, pagina in enumerate(pdf.pages, start=1):
            texto = pagina.extract_text() or ''
            if numero_pagina == 1:
                cabecalho = _ler_cabecalho(texto)
            for linha in texto.splitlines():
                linha = linha.strip()
                m = _RE_ANIMAL.match(linha)
                if m:
                    animais.append({
                        'linha': len(animais) + 1,
                        'pagina': numero_pagina,
                        'sisbov': m.group('sisbov'),
                        'nascimento': _data(m.group('nasc')),
                        'nascimento_texto': m.group('nasc'),
                        'raca_nome': m.group('raca').strip(),
                        'sexo': _sexo(m.group('sexo')),
                        'sexo_texto': m.group('sexo'),
                        'data_inclusao': _data(m.group('incl')),
                        'data_inclusao_texto': m.group('incl'),
                    })
                elif _RE_PARECE_ANIMAL.match(linha):
                    nao_lidas.append({'pagina': numero_pagina, 'texto': linha})
    return {
        'formato': FORMATO,
        'cabecalho': cabecalho or _ler_cabecalho(''),
        'animais': animais,
        'linhas_nao_lidas': nao_lidas,
    }


def _cabecalho_vazio():
    return _ler_cabecalho('')


def ler_partes(caminho_pdf):
    """BND/Fazenda: le o Extrato e devolve UMA PARTE POR PRODUTOR (o PDF vem particionado por Produtor).
    Cada parte = {'cabecalho': ..., 'animais': [...], 'linhas_nao_lidas': [...]} no mesmo formato de ler().
    A parte comeca na linha 'Nome: ... CPF/CNPJ: ...'; certificadora, propriedade e municipio valem ate a proxima
    vez que aparecerem. Linhas de animal que vierem antes de qualquer Produtor vao para uma parte sem Produtor."""
    partes = []
    contexto = _cabecalho_vazio()
    atual = None

    def nova_parte():
        cab = dict(contexto)
        cab['produtor_nome'] = None
        cab['produtor_documento'] = None
        cab['total_femea'] = None
        cab['total_macho'] = None
        return {'cabecalho': cab, 'animais': [], 'linhas_nao_lidas': []}

    with pdfplumber.open(caminho_pdf) as pdf:
        total_paginas = len(pdf.pages)
        for numero_pagina, pagina in enumerate(pdf.pages, start=1):
            texto = pagina.extract_text() or ''
            for linha in texto.splitlines():
                linha = linha.strip()
                m = _RE_CERTIFICADORA.match(linha)
                if m:
                    contexto['certificadora'] = m.group(1).strip()
                    continue
                m = _RE_PROPRIEDADE.match(linha)
                if m:
                    contexto['propriedade_nome'], contexto['nirf'], contexto['cod_propriedade'] = m.group(1), m.group(2), m.group(3)
                    continue
                m = _RE_MUNICIPIO.match(linha)
                if m:
                    contexto['municipio'], contexto['uf'] = m.group(1), m.group(2).upper()
                    continue
                m = _RE_PRODUTOR.match(linha)
                if m:
                    # O cabecalho (Propriedade, Produtor) se repete em TODAS as paginas: o mesmo Produtor na mesma
                    # Propriedade continua a mesma parte; so um Produtor/Propriedade diferente abre parte nova.
                    documento = re.sub(r'\D', '', m.group(2))
                    chave = (documento, contexto.get('cod_propriedade'))
                    atual = None
                    for existente in partes:
                        if (existente['cabecalho']['produtor_documento'], existente['cabecalho']['cod_propriedade']) == chave:
                            atual = existente
                            break
                    if atual is None:
                        atual = nova_parte()
                        atual['cabecalho']['produtor_nome'] = m.group(1)
                        atual['cabecalho']['produtor_documento'] = documento
                        partes.append(atual)
                    continue
                m = _RE_TOTAIS.match(linha)
                if m and atual is not None:
                    atual['cabecalho']['total_femea'], atual['cabecalho']['total_macho'] = int(m.group(1)), int(m.group(2))
                    continue
                m = _RE_ANIMAL.match(linha)
                if m:
                    if atual is None:
                        atual = nova_parte()
                        partes.append(atual)
                    atual['animais'].append({
                        'linha': len(atual['animais']) + 1,
                        'pagina': numero_pagina,
                        'sisbov': m.group('sisbov'),
                        'nascimento': _data(m.group('nasc')),
                        'nascimento_texto': m.group('nasc'),
                        'raca_nome': m.group('raca').strip(),
                        'sexo': _sexo(m.group('sexo')),
                        'sexo_texto': m.group('sexo'),
                        'data_inclusao': _data(m.group('incl')),
                        'data_inclusao_texto': m.group('incl'),
                    })
                elif _RE_PARECE_ANIMAL.match(linha):
                    if atual is None:
                        atual = nova_parte()
                        partes.append(atual)
                    atual['linhas_nao_lidas'].append({'pagina': numero_pagina, 'texto': linha})
    for p in partes:
        p['cabecalho']['paginas'] = total_paginas
    return partes

# =========================================================
# FIM DE ARQUIVO: backend\leitores\leitor_mapa_extrato_vivos.py
# =========================================================
