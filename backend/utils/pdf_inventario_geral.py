# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\pdf_inventario_geral.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-09-24 11:15 -03
# ATUALIZADO EM: 2026-11-16 13:35 -03
# VERSAO:       1.4.1
# v1.4.1: Sessao 128 (2026-11-16 13:35 -03) - PDF Saldo passa a trazer ANEXO XVIII no titulo (numero oficial no Manual SISBOV v1.2). REVERSAO: .bak_antes_s128_anexos.
#     v1.4.0: Sessao 118 (2026-11-08 13:00 -03) - Animais na BND: coluna ERAS em cada animal (5o item da tupla; tupla antiga de 4 itens ainda funciona). Larguras: ERAS ganha COL_ERAS e a coluna RFID fica com o que sobra. REVERSAO: .bak_antes_s118_eras.
#
# DESCRICAO:
#     Geracao dos 2 PDFs do Inventario Geral da Propriedade:
#       - "DIA's DISPONIVEIS" (botao "Animais na BND") -
#         gerar_pdf_inventario_geral();
#       - "INVENTARIO DE ANIMAIS" (botao "Saldo", v1.1.0) -
#         gerar_pdf_saldo() - ver bloco SALDO no fim do arquivo.
#     Ambos via ReportLab puro
#     (Padrao Reutilizavel N.2 - Regras.txt secao 10.2). Chamado
#     por backend/routers/inventario_geral.py::animais_bnd().
#     Layout reproduz o PDF real do legado GERAS trazido por
#     Benedito (Sessao 079):
#
#       - Um BLOCO por Especie, cada um comecando em pagina nova:
#         titulo + Dados da Propriedade (Nome, Municipio/UF,
#         NIRF) + faixa "N DIAs Bovinos." + tabela + quadro.
#       - Tabela com 2 animais por linha (Indice | Codigo SISBOV |
#         RFid, repetido 2x), cabecalho repetido a cada pagina.
#       - Quadro-resumo no fim do bloco: Femeas/Machos x 4 faixas
#         de idade + Total por sexo + Geral (celula unica com o
#         total da especie).
#
#     DIFERENCA CONSCIENTE DO LEGADO: a data/hora de impressao sai
#     no RODAPE de TODAS as paginas, alinhada a direita (regra
#     permanente do Orion, Regras.txt secao 10) - no legado ela
#     ficava no topo. Desenhada direto no canvas (funcao
#     _desenhar_rodape), pois o relatorio tem muitas paginas.
#
#     Este arquivo NAO consulta banco: recebe tudo pronto do
#     router (lista de blocos ja agrupada, ordenada e com Indice
#     continuo entre especies). Assim a regra de negocio fica no
#     router e aqui so o desenho.
#
#     v1.0.0: Criacao do modulo (Sessao 079, 24/09/2026, 11:15 -03).
#     v1.3.0: Sessao 116 (06/11/2026, 15:35 -03) - CABECALHO PADRAO DOS COMUNICADOS DE SAIDA nos 2 PDFs
#             (Animais na BND e Saldo): bloco "DADOS DO PRODUTOR" (Produtor, CPF, CNPJ, Inscr. Estadual,
#             Cod. ERAS, Propriedade, Municipio, CEP + NIRF e Estab. Rural, que ja existiam) no lugar da
#             caixa "Dados da Propriedade". Nova funcao _cabecalho_produtor(); reaproveita _bloco_secao()
#             do pdf_anexo_saida. Lista, quadros e assinaturas intactos.
#             REVERSAO: .bak_antes_s116_produtor.
#     v1.2.0: Sessao 108 (29/10/2026, 15:40 -03) - NOVA coluna Sexo (M/F)
#             na lista de animais do "Animais na BND" (pedido do
#             Benedito). A tupla do animal ganhou o 4o item (sexo).
#             REVERSAO: .bak_antes_s108_inventario_sexo.
#     v1.1.0: Sessao 079 (24/09/2026, 11:34 -03) - NOVO PDF do
#             botao "Saldo" ("INVENTARIO DE ANIMAIS"), a partir
#             do modelo real do legado trazido por Benedito: bloco
#             Propriedade (Nome, Municipio/UF, NIRF, Estabelecimento
#             Rural = codigo_mapa), um quadro por Especie (so as
#             que tem animal - reaproveita _quadro_resumo() sem
#             mudanca) e bloco de assinaturas (Data/Local/Produtor
#             e Certificadora/Supervisor - nome da Certificadora
#             em branco, ainda nao ha cadastro). NOVAS funcoes:
#             _titulo_especie_espacado(), _bloco_assinaturas(),
#             montar_pdf_saldo(), gerar_pdf_saldo(). O PDF "DIA's
#             DISPONIVEIS" nao mudou.
# =========================================================

from datetime import datetime
from io import BytesIO

from flask import send_file
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from backend.utils.pdf_anexo_saida import _bloco_secao, formatar_documento
from backend.utils.pdf_reportlab import (
    COR_BORDA, COR_FUNDO_CABECALHO, COR_FUNDO_TOTAL, COR_RODAPE,
    LARGURA_UTIL, MARGEM_H, MARGEM_V, PAGE_SIZE,
    criar_bloco_dados, estilo_titulo,
)


# -------------------------------------------------------
# Larguras ABSOLUTAS (pontos) da tabela de animais - nunca
# percentual de container encolhido (bug real Sessao 055). Cada
# metade da linha (1 animal) = Indice + SISBOV + RFID; a coluna
# RFID fica com o que sobra, para a soma fechar na LARGURA_UTIL.
# -------------------------------------------------------
COL_INDICE = 32   # s118 - era 40 (sobra espaco: o SISBOV de 15 digitos cabe em bem menos que 112)
COL_SISBOV = 84   # s118 - era 112
COL_SEXO   = 24   # s118 - era 26
COL_ERAS   = 44   # s118 - faixa de ERAS de cada animal
COL_RFID   = (LARGURA_UTIL / 2) - COL_INDICE - COL_SISBOV - COL_SEXO - COL_ERAS

# Quadro-resumo (larguras absolutas, centralizado na pagina).
COL_RESUMO_SEXO  = 52
COL_RESUMO_FAIXA = 72
COL_RESUMO_TOTAL = 50
COL_RESUMO_GERAL = 58


# -------------------------------------------------------
# Estilos exclusivos deste relatorio.
# -------------------------------------------------------
estilo_eras_celula = ParagraphStyle('ErasCelula', fontName='Helvetica', fontSize=6.5, leading=7.5, alignment=TA_CENTER)   # s118

estilo_faixa_especie = ParagraphStyle(
    'FaixaEspecie', fontName='Helvetica-Bold', fontSize=14,
    alignment=TA_CENTER,
)

# v1.1.0 (Saldo): titulo espacado da Especie ("B O V I N O S").
estilo_titulo_especie_saldo = ParagraphStyle(
    'TituloEspecieSaldo', fontName='Helvetica-Bold', fontSize=15,
    alignment=TA_CENTER, spaceAfter=4,
)


# -------------------------------------------------------
# Funcao: _desenhar_rodape() - chamada pelo ReportLab em TODA
# pagina. Escreve "Impressao: dd/mm/aaaa HH:MM:SS" no rodape, a
# direita (regra permanente). O texto e fixado UMA vez (mesma
# hora em todas as paginas do mesmo PDF).
# -------------------------------------------------------
def _criar_rodape(texto_impressao):
    def _desenhar_rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(COR_RODAPE)
        canvas.drawRightString(PAGE_SIZE[0] - MARGEM_H, MARGEM_V / 2, texto_impressao)
        canvas.restoreState()
    return _desenhar_rodape


# -------------------------------------------------------
# Funcao (NOVA, v1.3.0): _cabecalho_produtor() - bloco "DADOS DO
# PRODUTOR" no mesmo desenho dos Comunicados de Saida (Anexo XX),
# usado nos 2 PDFs. 'dados' vem pronto do router (Produtor LOGADO).
# NIRF e Estabelecimento Rural (codigo_mapa) ja existiam nos PDFs
# e foram mantidos numa linha propria.
# -------------------------------------------------------
def _cabecalho_produtor(dados):
    municipio_uf = f'{dados["municipio"]} / {dados["uf"]}' if dados.get('municipio') else '-'
    campos = {
        'produtor_nome': dados.get('produtor_nome') or '-',
        'cpf': formatar_documento(dados.get('cpf')),
        'cnpj': formatar_documento(dados.get('cnpj')),
        'inscricao_estadual': dados.get('inscricao_estadual') or '',
        'codigo_eras': dados.get('codigo_eras') or '',
        'propriedade_nome': dados.get('nome') or '-',
        'municipio': municipio_uf,
        'cep': dados.get('cep') or '',
        'nirf': dados.get('nirf') or '-',
        'codigo_mapa': dados.get('codigo_mapa') or '-',
    }
    bloco = _bloco_secao('DADOS DO PRODUTOR', campos, [
        ('1', 'Produtor:', 'produtor_nome'),
        ('2', 'CPF:', 'cpf', 492, 'CNPJ:', 'cnpj', 535, 590, 594),
        ('2', 'Inscr. Estadual:', 'inscricao_estadual', 492, 'Cód. ERAS:', 'codigo_eras', 617, 709, 712),
        ('1', 'Propriedade:', 'propriedade_nome'),
        ('2', 'Município:', 'municipio', 649, 'CEP:', 'cep', 667, 709, 712),
        ('2', 'NIRF:', 'nirf', 492, 'Estab. Rural:', 'codigo_mapa', 595, 709, 712),
    ])
    bloco.hAlign = 'CENTER'   # alinha a barra com as demais tabelas (sem o desvio de 6pt do quadro)
    return [bloco, Spacer(1, 6)]


# -------------------------------------------------------
# Funcao: _tabela_animais() - monta a grade de 2 animais por
# linha. 'animais' = lista de tuplas (indice, sisbov_formatado,
# rfid) JA ordenada. Numero impar: a ultima linha fica com a
# metade direita vazia (igual ao legado).
# -------------------------------------------------------
# s118 - texto da faixa de ERAS do animal (5o item da tupla); vazio se a tupla for antiga (4 itens).
def _eras_curta(animal):
    if len(animal) <= 4 or not animal[4]:
        return ''
    texto = str(animal[4]).replace('Meses', '').replace('Zero', '0').strip()   # '04 a 12 Meses' -> '04 a 12'
    return Paragraph(texto, estilo_eras_celula)


def _tabela_animais(animais):
    cabecalho = ['Indice', 'Código SISBOV', 'RFid', 'Sexo', 'ERAS', 'Indice', 'Código SISBOV', 'RFid', 'Sexo', 'ERAS']
    linhas = [cabecalho]

    for i in range(0, len(animais), 2):
        esquerda = animais[i]
        direita = animais[i + 1] if i + 1 < len(animais) else ('', '', '', '', '')
        linhas.append([
            str(esquerda[0]), esquerda[1], esquerda[2] or '', esquerda[3] or '', _eras_curta(esquerda),
            str(direita[0]), direita[1], direita[2] or '', direita[3] or '', _eras_curta(direita),
        ])

    larguras = [COL_INDICE, COL_SISBOV, COL_RFID, COL_SEXO, COL_ERAS] * 2

    tabela = Table(linhas, colWidths=larguras, repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COR_FUNDO_CABECALHO),
        ('GRID', (0, 0), (-1, -1), 0.5, COR_BORDA),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        # Destaque do SISBOV - vem DEPOIS da regra geral de fonte
        # (no ReportLab a ULTIMA regra que cobre a celula vence -
        # bug real da Sessao 075).
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (6, 1), (6, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (4, 1), (4, -1), 6.5),   # s118 - ERAS: fonte menor para caber o texto da faixa
        ('FONTSIZE', (9, 1), (9, -1), 6.5),
        # Linha grossa separando os 2 animais da mesma linha.
        ('LINEAFTER', (4, 0), (4, -1), 1.2, colors.black),
    ]))
    return tabela


# -------------------------------------------------------
# Funcao: _quadro_resumo() - Femeas/Machos x faixas + Total +
# Geral (celula unica, mesclada nas 2 linhas, com o total da
# especie), centralizado na LARGURA_UTIL inteira (receita 10.3).
# -------------------------------------------------------
def _quadro_resumo(colunas_faixas, resumo, total_especie):
    femeas = resumo['FEMEA']
    machos = resumo['MACHO']
    total_femeas = sum(femeas)
    total_machos = sum(machos)

    dados = [
        ['Sexo'] + list(colunas_faixas) + ['Total', 'Geral'],
        ['Fêmeas'] + [str(v) for v in femeas] + [str(total_femeas), str(total_especie)],
        ['Machos'] + [str(v) for v in machos] + [str(total_machos), ''],
    ]

    larguras = (
        [COL_RESUMO_SEXO]
        + [COL_RESUMO_FAIXA] * len(colunas_faixas)
        + [COL_RESUMO_TOTAL, COL_RESUMO_GERAL]
    )
    largura_quadro = sum(larguras)

    quadro = Table(dados, colWidths=larguras)
    quadro.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COR_FUNDO_CABECALHO),
        ('GRID', (0, 0), (-1, -1), 0.5, COR_BORDA),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        # Coluna Total por sexo destacada.
        ('BACKGROUND', (-2, 1), (-2, -1), COR_FUNDO_TOTAL),
        ('FONTNAME', (-2, 1), (-2, -1), 'Helvetica-Bold'),
        # Celula Geral: mesclada nas 2 linhas de sexo.
        ('SPAN', (-1, 1), (-1, 2)),
        ('BACKGROUND', (-1, 1), (-1, 2), COR_FUNDO_TOTAL),
        ('FONTNAME', (-1, 1), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (-1, 1), (-1, 2), 12),
    ]))

    margem = max((LARGURA_UTIL - largura_quadro) / 2, 0)
    linha = Table([['', quadro, '']], colWidths=[margem, largura_quadro, margem])
    linha.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return linha


# -------------------------------------------------------
# Funcao: montar_pdf_inventario_geral() - monta o PDF inteiro e
# devolve o BytesIO (ja posicionado no inicio). Separada da
# resposta Flask para poder ser testada sozinha.
#
# blocos: lista (uma entrada por Especie, ja na ordem de
#     impressao) de dicts:
#       'rotulo'  - ex.: 'Bovinos'
#       'animais' - lista de (indice, sisbov_formatado, rfid, sexo M/F)
#       'resumo'  - {'FEMEA': [4 ints], 'MACHO': [4 ints]}
#       'total'   - total de animais da especie
# colunas_faixas: 4 titulos das faixas (ex.: 'Zero a 12 Meses').
# dados_propriedade: dict com nome, municipio, uf, nirf.
# -------------------------------------------------------
def montar_pdf_inventario_geral(blocos, colunas_faixas, dados_propriedade):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=PAGE_SIZE,
        leftMargin=MARGEM_H, rightMargin=MARGEM_H,
        topMargin=MARGEM_V, bottomMargin=MARGEM_V,
        title="DIA's Disponíveis",
    )

    texto_impressao = f'Impressão: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'
    rodape = _criar_rodape(texto_impressao)

    municipio_uf = (
        f'{dados_propriedade["municipio"]} / {dados_propriedade["uf"]}'
        if dados_propriedade.get('municipio') else '-'
    )
    texto_nirf = f'NIRF: {dados_propriedade["nirf"]}' if dados_propriedade.get('nirf') else 'NIRF: -'

    story = []
    for posicao, bloco in enumerate(blocos):
        if posicao > 0:
            story.append(PageBreak())

        story.append(Paragraph("DIA's DISPONÍVEIS", estilo_titulo))
        story.append(Spacer(1, 10))
        story += _cabecalho_produtor(dados_propriedade)
        story.append(Paragraph(f'{bloco["total"]} DIAs {bloco["rotulo"]}.', estilo_faixa_especie))
        story.append(Spacer(1, 8))
        story.append(_tabela_animais(bloco['animais']))
        story.append(Spacer(1, 10))
        # KeepTogether: o quadro nunca e partido entre 2 paginas.
        story.append(KeepTogether([_quadro_resumo(colunas_faixas, bloco['resumo'], bloco['total'])]))

    doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
    buffer.seek(0)
    return buffer


# -------------------------------------------------------
# Funcao principal (chamada pelo router): gera o PDF e devolve a
# Response pronta do Flask (download).
# -------------------------------------------------------
def gerar_pdf_inventario_geral(blocos, colunas_faixas, dados_propriedade):
    buffer = montar_pdf_inventario_geral(blocos, colunas_faixas, dados_propriedade)

    nome_propriedade = (dados_propriedade.get('nome') or 'Propriedade').replace(' ', '_')
    nome_arquivo = f'Inventario_DIAs_Disponiveis_{nome_propriedade}_{datetime.now().strftime("%d-%m-%Y")}.pdf'

    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)

# =========================================================
# BLOCO SALDO (v1.1.0) - PDF "INVENTARIO DE ANIMAIS"
# =========================================================

# Larguras (pontos) do bloco de assinaturas - fecham na
# LARGURA_UTIL (linha 1: Data | Local | Produtor; linha 2:
# Certificadora | espaco | Supervisor).
ASS_COL_DATA      = 125
ASS_COL_LOCAL     = 175
ASS_COL_PRODUTOR  = LARGURA_UTIL - ASS_COL_DATA - ASS_COL_LOCAL
ASS_COL_ESPACO    = 35
ASS_COL_METADE    = (LARGURA_UTIL - ASS_COL_ESPACO) / 2


# -------------------------------------------------------
# Funcao: _titulo_especie_espacado() - "Bovinos" -> "B O V I N O S"
# (mesmo visual do legado).
# -------------------------------------------------------
def _titulo_especie_espacado(rotulo):
    return ' '.join(rotulo.upper())


# -------------------------------------------------------
# Funcao: _bloco_assinaturas() - 2 tabelas de linhas de
# assinatura. Linha de assinatura = LINEABOVE na celula do
# rotulo (o texto fica logo abaixo do traco).
#   Tabela 1: Data ___/___/___ | Local (Municipio/UF escrito em
#             cima do traco) | Assinatura do Produtor.
#   Tabela 2: Certificadora Responsavel (nome em branco - ainda
#             sem cadastro) | Assinatura e Carimbo do Supervisor.
# -------------------------------------------------------
def _bloco_assinaturas(texto_local):
    tabela_1 = Table(
        [
            ['Data ____/____/______', texto_local, ''],
            ['', 'Local', 'Assinatura do Produtor ou Responsável'],
        ],
        colWidths=[ASS_COL_DATA, ASS_COL_LOCAL, ASS_COL_PRODUTOR],
    )
    tabela_1.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ALIGN', (1, 0), (2, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING', (0, 0), (-1, 0), 24),
        ('LINEABOVE', (1, 1), (1, 1), 0.8, colors.black),
        ('LINEABOVE', (2, 1), (2, 1), 0.8, colors.black),
        ('LEFTPADDING', (1, 0), (2, -1), 8),
        ('RIGHTPADDING', (1, 0), (2, -1), 8),
    ]))

    tabela_2 = Table(
        [
            ['', '', ''],
            ['Certificadora Responsável', '', 'Assinatura e Carimbo do Supervisor da Certificadora'],
        ],
        colWidths=[ASS_COL_METADE, ASS_COL_ESPACO, ASS_COL_METADE],
    )
    tabela_2.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, 0), 30),
        ('LINEABOVE', (0, 1), (0, 1), 0.8, colors.black),
        ('LINEABOVE', (2, 1), (2, 1), 0.8, colors.black),
    ]))

    return [tabela_1, Spacer(1, 18), tabela_2]


# -------------------------------------------------------
# Funcao: montar_pdf_saldo() - monta o PDF "INVENTARIO DE
# ANIMAIS" e devolve o BytesIO. Recebe os MESMOS blocos do
# Animais na BND (a lista 'animais' de cada bloco e ignorada
# aqui - so resumo/total/rotulo).
# -------------------------------------------------------
def montar_pdf_saldo(blocos, colunas_faixas, dados_propriedade):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=PAGE_SIZE,
        leftMargin=MARGEM_H, rightMargin=MARGEM_H,
        topMargin=MARGEM_V, bottomMargin=MARGEM_V,
        title='Inventário de Animais',
    )

    texto_impressao = f'Impressão: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'
    rodape = _criar_rodape(texto_impressao)

    municipio_uf = (
        f'{dados_propriedade["municipio"]} / {dados_propriedade["uf"]}'
        if dados_propriedade.get('municipio') else '-'
    )
    texto_estab = f'Estabelecimento Rural: {dados_propriedade.get("codigo_mapa") or "-"}'

    story = [Paragraph('ANEXO XVIII - INVENTÁRIO DE ANIMAIS', estilo_titulo), Spacer(1, 10)]
    story += _cabecalho_produtor(dados_propriedade)

    for bloco in blocos:
        story.append(KeepTogether([
            Paragraph(_titulo_especie_espacado(bloco['rotulo']), estilo_titulo_especie_saldo),
            _quadro_resumo(colunas_faixas, bloco['resumo'], bloco['total']),
            Spacer(1, 14),
        ]))

    story.append(Spacer(1, 16))
    story.append(KeepTogether(_bloco_assinaturas(municipio_uf)))

    doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
    buffer.seek(0)
    return buffer


# -------------------------------------------------------
# Funcao principal do Saldo (chamada pelo router): gera o PDF e
# devolve a Response pronta do Flask (download).
# -------------------------------------------------------
def gerar_pdf_saldo(blocos, colunas_faixas, dados_propriedade):
    buffer = montar_pdf_saldo(blocos, colunas_faixas, dados_propriedade)

    nome_propriedade = (dados_propriedade.get('nome') or 'Propriedade').replace(' ', '_')
    nome_arquivo = f'Inventario_Saldo_{nome_propriedade}_{datetime.now().strftime("%d-%m-%Y")}.pdf'

    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_inventario_geral.py
# =========================================================