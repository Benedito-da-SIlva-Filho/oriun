# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\leitores
# MODULO: backend\leitores\leitor_ms_iagro.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-08-01 11:15 -03
# ATUALIZADO EM: 2026-08-10 16:40 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Leitor automatico de e-GTA emitida pelo IAGRO/MS (PDF
#     nativo, gerado por Microsoft Reporting Services - texto
#     100% extraivel, sem necessidade de OCR). Desenhado e
#     TESTADO contra um documento real: GTA_Compra_MS.pdf,
#     Serie Q, Numero 515308 (Procedencia: Roselene Carvalho de
#     Oliveira / Fazenda Tres Barras; Destino: Maria Angelica
#     Maia Cintra / Fazenda Olho D'Agua).
#
#     TECNICA DE LEITURA - por que coordenadas X/Y e nao so
#     "procurar o texto":
#       O e-GTA do IAGRO imprime Procedencia e Destino LADO A
#       LADO, na MESMA linha visual do papel (duas colunas). Se
#       o leitor so procurasse pelo texto "CPF/CNPJ:", ele
#       acharia DOIS resultados na mesma linha e nao saberia
#       qual e qual. Por isso este leitor usa a biblioteca
#       pdfplumber, que devolve cada palavra do PDF com sua
#       posicao exata (x0 = inicio, x1 = fim, top = linha) -
#       nao so o texto corrido.
#
#       Com a posicao em maos, o leitor calcula uma "regua de
#       corte" (a coordenada X onde a coluna Destino comeca) e
#       classifica cada palavra da metade Procedencia/Destino
#       como ESQUERDA ou DIREITA dessa regua, linha por linha.
#       Testado e confirmado: a coluna Destino sempre comeca na
#       mesma posicao X do papel (a mesma usada pelo cabecalho
#       "DESTINO"), entao a regua = (posicao X do cabecalho
#       DESTINO) menos uma margem de seguranca - ver
#       MARGEM_CORTE_COLUNA abaixo.
#
#     TOLERANCIA DE FORMATACAO - o proprio IAGRO nao e
#       consistente na propria formatacao (confirmado no
#       documento real):
#         "Insc.Estadual:" (Procedencia, sem espaco) vs
#         "Insc. Estadual:" (Destino, com espaco);
#         "Código MAPA:500002064440001" (Procedencia, colado) vs
#         "Código MAPA: 500000680640005" (Destino, com espaco).
#       Por isso todo regex de rotulo usa \s* (zero ou mais
#       espacos) nos pontos de variacao, nunca espaco fixo.
#
#     CAMPOS QUE ESTE LEITOR NAO PREENCHE (por decisao de
#       projeto, nao por limitacao tecnica):
#         - data_entrega: e a UNICA decisao real do usuario
#           nesta tela (quando os animais chegaram de fato) -
#           nunca deve vir pre-preenchida por leitura automatica.
#         - codigo_barras_iagro: decisao de Benedito (Sessao
#           029) - o Codigo de Autenticidade sozinho ja e
#           suficiente como resguardo documental, nao precisamos
#           do Codigo de Barras tambem.
#
#     CONTRATO DA FUNCAO PUBLICA ler(caminho_pdf):
#       Devolve um dict com as chaves abaixo, usando EXATAMENTE
#       os mesmos nomes de campo que backend/routers/gta_compra.py
#       ja usa em request.form.get(...) - assim o router so
#       precisa espalhar o dict direto nos campos, sem tradução:
#         uf_gta, serie_gta, numero_gta_sequencial,
#         data_emissao, data_validade, meio_transporte,
#         codigo_autenticidade,
#         procedencia_documento, procedencia_regiao,
#         procedencia_nome, procedencia_propriedade,
#         procedencia_codigo_mapa, procedencia_insc_estadual,
#         procedencia_municipio, procedencia_municipio_codigo,
#         procedencia_uf,
#         destino_documento, destino_regiao,
#         destino_produtor, destino_propriedade,
#         destino_codigo_mapa, destino_insc_estadual,
#         destino_municipio, destino_municipio_codigo, destino_uf,
#         animais (lista de dicts: especie, sexo, idade_meses,
#         quantidade - mesmo formato que
#         _ler_animais_do_formulario() ja usa em gta_compra.py).
#
#       Levanta ValueError (mensagem endereçada ao usuario,
#       "Sr. Usuário(a)...") se algum campo OBRIGATORIO nao for
#       localizado no documento - nunca devolve a tela pela
#       metade preenchida. O router captura essa excecao e
#       reexibe o dropzone de upload com o aviso.
#
#     v1.0.0: Criacao do modulo (Sessao 029). Desenhado E
#         TESTADO campo a campo contra o documento real
#         GTA_Compra_MS.pdf (Serie Q/515308) antes da entrega -
#         todos os 21 campos conferidos manualmente contra o
#         PDF fisico.
#     v1.1.0: Sessao 034 (continuacao 4, 10/08/2026) - Passa a
#         capturar tambem o CODIGO do Municipio (ex.: "5006408"
#         em "Municipio: 5006408 - PEDRO GOMES"), que ja vinha
#         no documento mas era descartado ate agora - so o nome
#         era extraido. Motivo: a futura funcao resolver_parceiro()
#         (backend/servicos/) precisa do codigo oficial para a
#         cascata de busca em tb_parceiros_propriedades (campo
#         municipio_codigo, ja existente no model desde a Sessao
#         17 - nao precisou de ALTER TABLE, so faltava capturar o
#         dado). NAO MUDA NADA VISIVEL NA TELA - os dois campos
#         novos (procedencia_municipio_codigo, destino_municipio_
#         codigo) sao carregados apenas em campos hidden do
#         formulario (ver gta_compra_cadastro.html v2.8.0),
#         decisao de Benedito para nao mexer em nada ja validado
#         em producao. O campo procedencia_municipio /
#         destino_municipio (nome) continua identico, sem
#         nenhuma mudanca de comportamento.
# =========================================================

import re

import pdfplumber


# -------------------------------------------------------
# Margem de seguranca (em pontos PDF) subtraida da posicao X do
# cabecalho "DESTINO" para formar a regua de corte de coluna.
# Por que nao usar a posicao X exata do cabecalho: o CONTEUDO de
# cada linha (ex.: "Insc.Estadual: 286941600") pode ser mais
# largo que a palavra "DESTINO" do titulo, entao a regua precisa
# de uma folga para nao cortar o final de um valor da
# Procedencia jogando ele pro lado do Destino. Valor calibrado
# e testado contra o documento real - a coluna Destino sempre
# comeca exatamente na mesma posicao X que o cabecalho "DESTINO"
# no e-GTA MS/IAGRO, entao 12 pontos de folga e suficiente.
# -------------------------------------------------------
MARGEM_CORTE_COLUNA = 12

# Tolerancia (em pontos PDF) para agrupar palavras na mesma
# "linha visual" do documento, mesmo que o PDF as tenha gerado
# com um ou dois pontos de diferenca vertical (comum quando duas
# colunas independentes sao renderizadas lado a lado).
TOLERANCIA_LINHA = 1.5


# =========================================================
# BLOCO 1 - Leitura bruta do PDF: palavras com coordenadas,
# agrupadas em linhas visuais.
# =========================================================

def _extrair_palavras(caminho_pdf):
    """Abre o PDF e devolve a lista de palavras da 1a pagina,
    cada uma com texto + posicao (x0, x1, top). e-GTA sempre
    cabe em 1 pagina - confirmado em todos os documentos reais
    analisados na Sessao 028."""
    with pdfplumber.open(caminho_pdf) as pdf:
        primeira_pagina = pdf.pages[0]
        return primeira_pagina.extract_words(
            use_text_flow=False, keep_blank_chars=False
        )


def _agrupar_em_linhas(palavras, tolerancia=TOLERANCIA_LINHA):
    """Agrupa palavras soltas em linhas visuais, com base na
    coordenada 'top' (posicao vertical). Palavras cuja diferenca
    de 'top' for menor ou igual a tolerancia entram na mesma
    linha. Cada linha devolvida ja vem ordenada da esquerda pra
    direita (por x0) - essencial para depois separar
    Procedencia (esquerda) de Destino (direita)."""
    palavras_ordenadas = sorted(palavras, key=lambda p: (p['top'], p['x0']))

    linhas = []
    linha_atual = []
    top_referencia = None

    for palavra in palavras_ordenadas:
        if top_referencia is None or abs(palavra['top'] - top_referencia) <= tolerancia:
            linha_atual.append(palavra)
            if top_referencia is None:
                top_referencia = palavra['top']
        else:
            linhas.append(sorted(linha_atual, key=lambda p: p['x0']))
            linha_atual = [palavra]
            top_referencia = palavra['top']

    if linha_atual:
        linhas.append(sorted(linha_atual, key=lambda p: p['x0']))

    return linhas


def _indice_primeira_linha_contendo(linhas, *textos_procurados, a_partir_de=0):
    """Devolve o indice da primeira linha (a partir do indice
    informado) que contem TODAS as palavras exatas passadas em
    textos_procurados. Devolve None se nao encontrar - quem
    chama decide se isso e erro fatal ou nao."""
    for indice in range(a_partir_de, len(linhas)):
        textos_da_linha = [palavra['text'] for palavra in linhas[indice]]
        if all(texto in textos_da_linha for texto in textos_procurados):
            return indice
    return None


# =========================================================
# BLOCO 2 - Regua de corte Procedencia/Destino e divisao de
# linhas em duas metades.
# =========================================================

def _calcular_x_corte(linhas):
    """Localiza a linha de cabecalho 'PROCEDÊNCIA ... DESTINO' e
    calcula a coordenada X que separa as duas colunas, usando a
    posicao X onde a palavra 'DESTINO' comeca, menos a margem de
    seguranca (ver MARGEM_CORTE_COLUNA acima)."""
    indice_cabecalho = _indice_primeira_linha_contendo(linhas, 'DESTINO')

    if indice_cabecalho is None:
        raise ValueError(
            'Sr. Usuário(a), não foi possível localizar o cabeçalho '
            '"DESTINO" neste documento. Verifique se o PDF enviado é '
            'uma e-GTA do MS/IAGRO completa e sem cortes de página.'
        )

    palavra_destino = next(
        p for p in linhas[indice_cabecalho] if p['text'] == 'DESTINO'
    )
    return palavra_destino['x0'] - MARGEM_CORTE_COLUNA, indice_cabecalho


def _dividir_linha_por_corte(linha, x_corte):
    """Separa as palavras de uma linha em duas metades (esquerda
    = Procedencia, direita = Destino), de acordo com a regua de
    corte, e devolve o texto de cada metade ja remontado com
    espaco simples entre as palavras."""
    texto_esquerda = ' '.join(p['text'] for p in linha if p['x0'] < x_corte)
    texto_direita = ' '.join(p['text'] for p in linha if p['x0'] >= x_corte)
    return texto_esquerda, texto_direita


def _montar_blocos_procedencia_destino(linhas):
    """Percorre as linhas do quadro Procedencia/Destino (do
    cabecalho ate a linha 'FINALIDADE:', que fecha o quadro) e
    devolve dois textos multi-linha ja separados: um so com o
    conteudo de Procedencia, outro so com o de Destino. Cada um
    desses textos depois passa pelos regex de campo do BLOCO 3."""
    x_corte, indice_cabecalho = _calcular_x_corte(linhas)

    indice_fim = _indice_primeira_linha_contendo(
        linhas, a_partir_de=indice_cabecalho + 1,
        *['FINALIDADE:']
    )
    if indice_fim is None:
        # Fallback defensivo: se o rotulo FINALIDADE nao aparecer
        # por algum motivo, usa 8 linhas fixas (tamanho real do
        # quadro no documento testado) para nao ler o PDF inteiro
        # por engano.
        indice_fim = indice_cabecalho + 8

    linhas_esquerda = []
    linhas_direita = []
    for linha in linhas[indice_cabecalho + 1:indice_fim]:
        esquerda, direita = _dividir_linha_por_corte(linha, x_corte)
        linhas_esquerda.append(esquerda)
        linhas_direita.append(direita)

    return '\n'.join(linhas_esquerda), '\n'.join(linhas_direita)


# =========================================================
# BLOCO 3 - Extracao de campos por regex, tolerante a variacao
# de espacamento (o proprio IAGRO nao e consistente - ver
# DESCRICAO no topo do arquivo).
# =========================================================

def _extrair_campo(padrao, texto, obrigatorio, nome_campo_amigavel):
    """Busca um padrao regex (1 grupo de captura) no texto e
    devolve o valor encontrado, ja sem espacos nas pontas. Se
    obrigatorio=True e o padrao nao for encontrado, levanta
    ValueError com mensagem endereçada ao usuario, citando o
    nome amigavel do campo - nunca devolve a tela pela metade."""
    resultado = re.search(padrao, texto)

    if resultado:
        return resultado.group(1).strip()

    if obrigatorio:
        raise ValueError(
            f'Sr. Usuário(a), não foi possível localizar o campo '
            f'"{nome_campo_amigavel}" neste documento. Verifique se o '
            f'PDF enviado é a e-GTA correta e está completo.'
        )

    return ''


def _extrair_municipio(texto_bloco, nome_campo_documento_amigavel):
    """Extrai CODIGO e NOME do Municipio juntos (ex.: 'Municipio:
    5006408 - PEDRO GOMES  UF: MS' -> codigo '5006408', nome
    'PEDRO GOMES'). Sessao 034 cont. 4: antes so o nome era
    capturado (o codigo, apesar de estar no documento, era
    descartado) - agora os dois grupos sao extraidos na mesma
    busca, sem custo extra de regex."""
    resultado = re.search(
        r'Municipio:\s*(\d+)\s*-\s*(.+?)\s+UF:', texto_bloco
    )

    if resultado:
        return resultado.group(1).strip(), resultado.group(2).strip()

    raise ValueError(
        f'Sr. Usuário(a), não foi possível localizar o campo '
        f'"Município da {nome_campo_documento_amigavel}" neste documento. '
        f'Verifique se o PDF enviado é a e-GTA correta e está completo.'
    )


def _extrair_bloco_parceiro(prefixo, texto_bloco, nome_campo_documento_amigavel, chave_nome):
    """Extrai os campos de um lado (Procedencia OU Destino) a
    partir do texto ja separado por _montar_blocos_procedencia_destino().
    O NOME da chave do campo 'nome/razao social' muda conforme o
    lado (procedencia_nome vs destino_produtor - mesma assimetria
    ja usada na tela real, gta_compra_cadastro.html) - por isso e
    recebido como parametro (chave_nome), em vez de fixo."""
    municipio_codigo, municipio_nome = _extrair_municipio(
        texto_bloco, nome_campo_documento_amigavel)

    return {
        f'{prefixo}documento': _extrair_campo(
            r'CPF/CNPJ:\s*(\d+)', texto_bloco, True,
            f'CPF/CNPJ da {nome_campo_documento_amigavel}'),
        f'{prefixo}regiao': _extrair_campo(
            r'Regi[ãa]o:\s*([A-ZÀ-Ú ]+?)(?:\n|$)', texto_bloco, False,
            f'Região da {nome_campo_documento_amigavel}'),
        f'{prefixo}{chave_nome}': _extrair_campo(
            r'Nome:\s*(.+?)(?:\n|$)', texto_bloco, True,
            f'Nome da {nome_campo_documento_amigavel}'),
        f'{prefixo}propriedade': _extrair_campo(
            r'Estabelecimento:\s*(.+?)(?:\n|$)', texto_bloco, True,
            f'Estabelecimento da {nome_campo_documento_amigavel}'),
        f'{prefixo}codigo_mapa': _extrair_campo(
            r'C[óo]digo MAPA:\s*(\d+)', texto_bloco, False,
            f'Código MAPA da {nome_campo_documento_amigavel}'),
        f'{prefixo}insc_estadual': _extrair_campo(
            r'Insc\.?\s*Estadual:\s*(\d+)', texto_bloco, False,
            f'Inscrição Estadual da {nome_campo_documento_amigavel}'),
        f'{prefixo}municipio': municipio_nome,
        f'{prefixo}municipio_codigo': municipio_codigo,
        f'{prefixo}uf': _extrair_campo(
            r'UF:\s*([A-Z]{2})', texto_bloco, True,
            f'UF da {nome_campo_documento_amigavel}'),
    }


# =========================================================
# BLOCO 4 - Dados do cabecalho (UF/Serie/Numero da propria GTA,
# distinto do UF de Procedencia/Destino) e Animais.
# =========================================================

def _extrair_uf_serie_numero(linhas):
    """O cabecalho da GTA imprime os ROTULOS 'UF Série Número'
    numa linha, e os VALORES ('MS Q 515308') na(s) linha(s)
    seguinte(s) - casamento por ORDEM (1o rotulo = 1o valor),
    ja que sempre sao exatamente 3 rotulos e 3 valores nesta
    posicao. Procura nas 3 linhas seguintes ao rotulo porque o
    subtitulo "(Válida em todo o Território Nacional)" pode
    entrar como uma linha extra no meio, dependendo do PDF."""
    indice_rotulo = _indice_primeira_linha_contendo(
        linhas, 'UF', 'Série', 'Número')

    if indice_rotulo is None:
        raise ValueError(
            'Sr. Usuário(a), não foi possível localizar o cabeçalho '
            '"UF / Série / Número" neste documento.'
        )

    for linha in linhas[indice_rotulo + 1: indice_rotulo + 4]:
        # So considera palavras a direita do subtitulo (que fica
        # sempre mais a esquerda, x0 < 260 no documento testado).
        candidatos = [p['text'] for p in linha if p['x0'] > 260]
        if len(candidatos) == 3 and re.fullmatch(r'[A-Z]{2}', candidatos[0]):
            return candidatos[0], candidatos[1], candidatos[2]

    raise ValueError(
        'Sr. Usuário(a), não foi possível localizar os valores de '
        '"UF / Série / Número" logo abaixo do cabeçalho deste documento.'
    )


def _extrair_animais(linhas):
    """Le a(s) linha(s) de categoria de Animais, entre o
    cabecalho 'ANIMAIS QUANTIDADE' e a linha de resumo
    'Fêmea Macho Total ...'. Cada linha segue o padrao:
    ESPECIE SEXO <descrição livre da idade> QUANTIDADE - sem
    nenhum separador alem do espaco, entao a regra de fatiamento
    (decisao de Benedito, Sessao 029) e: 1a palavra = Especie,
    2a palavra = Sexo, ultima palavra = Quantidade, tudo que
    sobrar no meio = Idade em meses (aceita os 3 formatos
    oficiais: "0 A 12 MESES", "13 A 24 MESES", "ACIMA DE 36
    MESES")."""
    indice_inicio = _indice_primeira_linha_contendo(linhas, 'ANIMAIS', 'QUANTIDADE')
    indice_fim = _indice_primeira_linha_contendo(
        linhas, a_partir_de=(indice_inicio or 0) + 1, *['Fêmea', 'Macho'])

    if indice_inicio is None or indice_fim is None:
        raise ValueError(
            'Sr. Usuário(a), não foi possível localizar o quadro de '
            '"Animais" neste documento.'
        )

    animais = []
    for linha in linhas[indice_inicio + 1: indice_fim]:
        tokens = [p['text'] for p in linha]
        if not tokens:
            continue

        try:
            quantidade = int(tokens[-1])
        except ValueError:
            # Linha que nao termina em numero nao e uma linha de
            # categoria de animal (pode ser espaco em branco
            # residual entre o cabecalho e a 1a categoria) -
            # ignora, sem quebrar a leitura das demais.
            continue

        animais.append({
            'especie': tokens[0],
            'sexo': tokens[1],
            'idade_meses': ' '.join(tokens[2:-1]),
            'quantidade': quantidade,
        })

    if not animais:
        raise ValueError(
            'Sr. Usuário(a), não foi possível localizar nenhuma linha de '
            'categoria de Animais válida neste documento.'
        )

    return animais


# =========================================================
# FUNCAO PUBLICA - ver contrato completo na DESCRICAO do topo.
# =========================================================

def ler(caminho_pdf):
    palavras = _extrair_palavras(caminho_pdf)
    linhas = _agrupar_em_linhas(palavras)
    texto_completo = '\n'.join(
        ' '.join(p['text'] for p in linha) for linha in linhas
    )

    uf_gta, serie_gta, numero_gta_sequencial = _extrair_uf_serie_numero(linhas)

    texto_procedencia, texto_destino = _montar_blocos_procedencia_destino(linhas)

    dados = {
        'uf_gta': uf_gta,
        'serie_gta': serie_gta,
        'numero_gta_sequencial': numero_gta_sequencial,

        'data_emissao': _extrair_campo(
            r'Data:\s*(\d{2}/\d{2}/\d{4})', texto_completo, True, 'Data de Emissão'),
        'data_validade': _extrair_campo(
            r'Validade:\s*(\d{2}/\d{2}/\d{4})', texto_completo, True, 'Data de Validade'),
        'meio_transporte': _extrair_campo(
            r'MEIO DE TRANSPORTE:\s*([A-ZÀ-Ú]+)', texto_completo, True, 'Meio de Transporte'),
        'codigo_autenticidade': _extrair_campo(
            r'C[ÓO]DIGO DE AUTENTICIDADE:\s*(\d+)', texto_completo, True, 'Código de Autenticidade'),

        'animais': _extrair_animais(linhas),
    }

    dados.update(_extrair_bloco_parceiro(
        'procedencia_', texto_procedencia, 'Procedência', chave_nome='nome'))

    # Bloco Destino usa a mesma extracao generica do Procedencia,
    # mas o campo de nome/razao social troca de chave (destino_
    # produtor, nao destino_nome) para bater com o nome real do
    # campo ja usado em gta_compra.py / gta_compra_cadastro.html.
    dados.update(_extrair_bloco_parceiro(
        'destino_', texto_destino, 'Destino', chave_nome='produtor'))

    return dados

# =========================================================
# FIM DE ARQUIVO: backend\leitores\leitor_ms_iagro.py
# =========================================================