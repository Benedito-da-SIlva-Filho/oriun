# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\pdf_reportlab.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-09-12 16:10 -03
# ATUALIZADO EM: 2026-09-12 19:30 -03
# VERSAO:       1.2.0
#
# DESCRICAO:
#     Padrao Reutilizavel Nº2 do Orion (NOVA VERSAO, Sessao 050) -
#     geracao de PDF via ReportLab puro (Platypus: SimpleDocTemplate
#     + Table/TableStyle/Paragraph), substituindo o antigo padrao
#     xhtml2pdf/pisa PARA RELATORIOS NOVOS a partir desta sessao.
#
#     MOTIVACAO (decisao de Benedito, Sessao 050): o motor xhtml2pdf
#     so suporta CSS 2.1 (sem flex/grid, table-layout comportando-se
#     de forma imprevisivel) - ajustar largura/alinhamento de coluna
#     virou uma bricabraque de tentativa e erro no "Relatorio por
#     GTA". ReportLab desenha o PDF diretamente em Python, com
#     larguras de coluna em PONTOS - controle pixel-a-pixel de
#     verdade.
#
#     ESCOPO: relatorios ANTIGOS (Relatorio Resumo de Brincos,
#     Relatorio N.Fiscais, etc.) continuam em xhtml2pdf, intocados.
#     Este modulo e o novo padrao para relatorios NOVOS dali para
#     frente.
#
#     Este arquivo guarda so o que e GENERICO/REUTILIZAVEL. A
#     montagem do PDF especifico de cada relatorio (quais dados,
#     quais colunas) fica no router de cada modulo.
#
#     v1.0.0: Criacao do modulo (Sessao 050), extraido do primeiro
#             uso real - a migracao do "Relatorio por GTA".
#     v1.1.0: Sessao 050 (12/09/2026, 19:05 -03) - BUG REAL
#             encontrado em teste ao vivo (PDF real da GTA
#             MSA111114): rotulos quebravam NO MEIO DA PALAVRA
#             ("Produt/or:", "Insc. E/stadua/l:", "CPF/C/NPJ:") -
#             as colunas de rotulo de criar_bloco_dados() eram
#             estreitas demais (9%/9%) para o texto que carregavam.
#             Corrigido: proporcoes internas ajustadas - rotulo
#             9% -> 13%, rotulo_curto 9% -> 16%, valor 52% -> 44%.
#     v1.2.0: Sessao 050 (12/09/2026, 19:30 -03) - pacote de
#             ajustes apos nova rodada de teste visual:
#             (1) BUG REAL: rotulo "Propriedade:" AINDA quebrava
#             mesmo com 13% (linha "Propriedad/e:") - alargado
#             para 15%, testado contra a fonte real (Helvetica
#             9.5px) para garantir folga.
#             (2) MUDANCA DE DESIGN (pedido de Benedito): CPF/CNPJ
#             e Insc. Estadual deixam de ter rotulo e valor em
#             colunas SEPARADAS (deixava espaco morto/desalinhado
#             entre eles) - agora sao um UNICO Paragraph combinado
#             ("CPF/CNPJ: 80257631887"), alinhado a direita, sempre
#             grudados. Libera espaco extra para o Nome do Produtor/
#             Propriedade (valor: 44% -> 50%).
#             MUDANCA DE ASSINATURA (BREAKING): criar_bloco_dados()
#             passa a receber linhas de 3 elementos (rotulo, valor,
#             texto_direita) em vez de 4 (rotulo, valor, rotulo_
#             curto, valor_curto). texto_direita ja vem PRONTO do
#             chamador como "Rótulo: valor" - None para linha de
#             largura total (ex: Municipio). Qualquer chamador
#             existente desta funcao precisa ser atualizado junto
#             (ver gta_consulta.py v1.11.0).
# =========================================================

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer


# -------------------------------------------------------
# Pagina e margens - RETRATO (A4), mesmas margens usadas em
# SimpleDocTemplate() no router. Qualquer relatorio que use este
# modulo deve construir o SimpleDocTemplate com estas MESMAS
# margens, para que LARGURA_UTIL bata com a largura real
# disponivel na pagina.
# -------------------------------------------------------
PAGE_SIZE  = A4
MARGEM_H   = 40
MARGEM_V   = 40
LARGURA_UTIL = PAGE_SIZE[0] - (2 * MARGEM_H)


# -------------------------------------------------------
# Paleta de cores do Orion.
# -------------------------------------------------------
COR_PRIMARIA        = colors.HexColor('#D4370A')
COR_ROTULO          = colors.HexColor('#666666')
COR_BORDA           = colors.HexColor('#999999')
COR_GRADE           = colors.HexColor('#cccccc')
COR_FUNDO_CABECALHO = colors.HexColor('#f0f0f0')
COR_FUNDO_TOTAL     = colors.HexColor('#FBE9E4')
COR_RODAPE          = colors.HexColor('#888888')


# -------------------------------------------------------
# Estilos base (titulo/subtitulo/rodape) - usados diretamente
# pelo router, fora dos blocos/tabelas montados aqui.
# -------------------------------------------------------
estilo_titulo = ParagraphStyle(
    'TituloRelatorio', fontName='Helvetica-Bold', fontSize=16,
    alignment=TA_CENTER, spaceAfter=4,
)

estilo_subtitulo = ParagraphStyle(
    'SubtituloRelatorio', fontName='Helvetica-Bold', fontSize=15,
    textColor=COR_PRIMARIA, alignment=TA_CENTER, spaceAfter=14,
)

estilo_rodape = ParagraphStyle(
    'RodapeRelatorio', fontName='Helvetica', fontSize=8,
    textColor=COR_RODAPE, alignment=TA_RIGHT,
)


# -------------------------------------------------------
# Bloco de dados tipo "Origem/Destino" - barra de titulo em
# vermelho + linhas em 3 colunas: rotulo (esquerda), valor (largo,
# esquerda) e um bloco combinado rotulo+valor (direita, sempre
# grudados - v1.2.0, ver changelog). Reutilizavel em qualquer
# relatorio futuro que precise desse tipo de caixa.
#
# linhas: lista de tuplas (rotulo, valor, texto_direita).
#     texto_direita ja vem PRONTO do chamador, ex: "CPF/CNPJ:
#     80257631887" - None quando a linha usa 'valor' com SPAN sobre
#     as 2 colunas restantes (ex: Municipio, que ocupa a linha
#     inteira).
# -------------------------------------------------------
def criar_bloco_dados(titulo, linhas, largura=LARGURA_UTIL):
    estilo_titulo_bloco = ParagraphStyle(
        'TituloBloco', fontName='Helvetica-Bold', fontSize=10.5,
        textColor=colors.white,
    )
    estilo_rotulo = ParagraphStyle(
        'RotuloBloco', fontName='Helvetica', fontSize=9.5, textColor=COR_ROTULO,
    )
    estilo_valor = ParagraphStyle(
        'ValorBloco', fontName='Helvetica-Bold', fontSize=9.5,
    )
    estilo_direita = ParagraphStyle(
        'DireitaBloco', fontName='Helvetica-Bold', fontSize=9.5,
        alignment=TA_RIGHT,
    )

    # Proporcao v1.2.0: rotulo (15% - cabe "Propriedade:" com
    # folga) + valor largo (50%) + bloco direita combinado
    # rotulo+valor (resto, calculado por subtracao - garante que a
    # soma bate exatamente com 'largura').
    col_rotulo   = largura * 0.15
    col_valor    = largura * 0.50
    col_direita  = largura - col_rotulo - col_valor

    tabela_titulo = Table([[Paragraph(titulo, estilo_titulo_bloco)]], colWidths=[largura])
    tabela_titulo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COR_PRIMARIA),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    dados = []
    estilo_tabela = [
        ('BOX', (0, 0), (-1, -1), 0.5, COR_BORDA),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]

    for indice, (rotulo, valor, texto_direita) in enumerate(linhas):
        p_rotulo = Paragraph(rotulo, estilo_rotulo)
        p_valor  = Paragraph(valor or '-', estilo_valor)

        if texto_direita is None:
            dados.append([p_rotulo, p_valor, ''])
            estilo_tabela.append(('SPAN', (1, indice), (2, indice)))
        else:
            p_direita = Paragraph(texto_direita, estilo_direita)
            dados.append([p_rotulo, p_valor, p_direita])

    tabela_dados = Table(dados, colWidths=[col_rotulo, col_valor, col_direita])
    tabela_dados.setStyle(TableStyle(estilo_tabela))

    return [tabela_titulo, tabela_dados, Spacer(1, 8)]


# -------------------------------------------------------
# Cabecalho tipo "GTA" - N campos de largura igual, cada um com
# rotulo pequeno em cima e valor em destaque embaixo. Reutilizavel
# para qualquer cabecalho de documento (nao so GTA).
#
# campos: lista de tuplas (rotulo, valor).
# -------------------------------------------------------
def criar_cabecalho_campos(campos, largura=LARGURA_UTIL):
    estilo_rotulo = ParagraphStyle(
        'RotuloCampo', fontName='Helvetica', fontSize=8,
        textColor=COR_ROTULO, alignment=TA_CENTER,
    )
    estilo_valor = ParagraphStyle(
        'ValorCampo', fontName='Helvetica-Bold', fontSize=10,
        alignment=TA_CENTER,
    )

    n = len(campos)
    col = largura / n

    linha_rotulos = [Paragraph(rotulo, estilo_rotulo) for rotulo, _ in campos]
    linha_valores = [Paragraph(valor, estilo_valor) for _, valor in campos]

    tabela = Table([linha_rotulos, linha_valores], colWidths=[col] * n)
    tabela.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, COR_BORDA),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COR_BORDA),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return tabela


# -------------------------------------------------------
# Tabela detalhada generica (tipo "grade de animais") - cabecalho
# cinza repetido em toda pagina nova (equivalente ao repeat="1" do
# xhtml2pdf), com suporte a alinhamento por coluna e a colunas com
# fonte maior (destaque de legibilidade).
#
# cabecalhos: lista de textos do cabecalho.
# linhas: lista de listas de valores (na mesma ordem dos cabecalhos).
# larguras: lista de larguras em pontos, mesma ordem/quantidade dos
#     cabecalhos - a soma deve fechar com a largura util da pagina.
#     Responsabilidade do CHAMADOR garantir que cada largura acomoda
#     o texto do proprio cabecalho sem quebrar no meio da palavra.
# alinhamentos: lista opcional ('LEFT'/'CENTER'/'RIGHT') por coluna;
#     default 'LEFT'.
# colunas_destaque: lista opcional de INDICES de coluna que usam
#     fonte maior (ex: campos que precisam de mais legibilidade).
# -------------------------------------------------------
def criar_tabela_padrao(cabecalhos, linhas, larguras, alinhamentos=None, colunas_destaque=None):
    n = len(cabecalhos)
    alinhamentos = alinhamentos or ['LEFT'] * n
    colunas_destaque = colunas_destaque or []
    mapa_alinhamento = {'LEFT': TA_LEFT, 'CENTER': TA_CENTER, 'RIGHT': TA_RIGHT}

    def _estilo_cabecalho(indice):
        tamanho = 11 if indice in colunas_destaque else 8.5
        return ParagraphStyle(
            f'CabPadrao{indice}', fontName='Helvetica-Bold', fontSize=tamanho,
            alignment=mapa_alinhamento[alinhamentos[indice]],
        )

    def _estilo_celula(indice):
        tamanho = 10.5 if indice in colunas_destaque else 8.5
        return ParagraphStyle(
            f'CelPadrao{indice}', fontName='Helvetica', fontSize=tamanho,
            alignment=mapa_alinhamento[alinhamentos[indice]],
        )

    linha_cabecalho = [Paragraph(texto, _estilo_cabecalho(i)) for i, texto in enumerate(cabecalhos)]
    dados = [linha_cabecalho]
    for linha in linhas:
        dados.append([Paragraph(str(valor), _estilo_celula(i)) for i, valor in enumerate(linha)])

    tabela = Table(dados, colWidths=larguras, repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COR_FUNDO_CABECALHO),
        ('GRID', (0, 0), (-1, -1), 0.5, COR_GRADE),
        ('BOX', (0, 0), (-1, -1), 0.5, COR_BORDA),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return tabela


# -------------------------------------------------------
# Tabela de resumo "Sexo x Faixa Etaria" (padrao GERAS) - 2 linhas
# fixas (Femeas/Machos) + coluna Total destacada. Especifica o
# suficiente para nao valer a pena generalizar mais - se um segundo
# relatorio precisar de algo parecido, avaliar nesse momento se vale
# a pena abstrair de novo.
# -------------------------------------------------------
def criar_tabela_resumo(colunas_faixas, resumo_femeas, resumo_machos, total_femeas, total_machos, largura=None):
    largura = largura if largura is not None else LARGURA_UTIL * 0.75
    n_colunas = len(colunas_faixas) + 2  # Sexo + faixas + Total
    col = largura / n_colunas

    estilo_cabecalho = ParagraphStyle('CabResumo', fontName='Helvetica-Bold', fontSize=8.5, alignment=TA_CENTER)
    estilo_rotulo_linha = ParagraphStyle('RotuloResumo', fontName='Helvetica-Bold', fontSize=8.5, alignment=TA_LEFT)
    estilo_valor = ParagraphStyle('ValorResumo', fontName='Helvetica', fontSize=8.5, alignment=TA_CENTER)
    estilo_total = ParagraphStyle('TotalResumo', fontName='Helvetica-Bold', fontSize=8.5, alignment=TA_CENTER)

    cabecalho = (
        [Paragraph('Sexo', estilo_cabecalho)]
        + [Paragraph(faixa, estilo_cabecalho) for faixa in colunas_faixas]
        + [Paragraph('Total', estilo_cabecalho)]
    )
    linha_femeas = (
        [Paragraph('Fêmeas', estilo_rotulo_linha)]
        + [Paragraph(str(v), estilo_valor) for v in resumo_femeas]
        + [Paragraph(str(total_femeas), estilo_total)]
    )
    linha_machos = (
        [Paragraph('Machos', estilo_rotulo_linha)]
        + [Paragraph(str(v), estilo_valor) for v in resumo_machos]
        + [Paragraph(str(total_machos), estilo_total)]
    )

    tabela = Table([cabecalho, linha_femeas, linha_machos], colWidths=[col] * n_colunas)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COR_FUNDO_CABECALHO),
        ('BACKGROUND', (-1, 1), (-1, -1), COR_FUNDO_TOTAL),
        ('GRID', (0, 0), (-1, -1), 0.5, COR_BORDA),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return tabela

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_reportlab.py
# =========================================================