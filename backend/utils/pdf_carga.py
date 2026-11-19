# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\pdf_carga.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-11-17 18:42 -03
# ATUALIZADO EM: 2026-11-17 18:42 -03
# VERSAO:       1.0.0
#
# DESCRICAO:
#     PDF "RELATORIO DA CARGA": o que o Produtor recebe para conhecer a Carga
#     inicial de animais. Cabecalho padrao (DADOS DO PRODUTOR + Data da Carga),
#     lista de 1 animal por linha (Indice, SISBOV, Nascimento, Raca, Sexo,
#     Data Inclusao, ERAS na data da Carga) com cabecalho repetido a cada
#     pagina, e ao FIM (so na ultima pagina) o quadro Sexo x faixas de ERAS com
#     Total e Geral. Rodape padrao com a hora da impressao.
#     NAO consulta banco: recebe tudo pronto do router carga_relatorio.py.
#     Reaproveita cabecalho, rodape e quadro de pdf_inventario_geral.py.
#     v1.0.0: Criacao (Carga, 17/11/2026).
# =========================================================

from datetime import datetime
from io import BytesIO

from flask import send_file
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.utils.pdf_inventario_geral import _cabecalho_produtor, _criar_rodape, _quadro_resumo
from backend.utils.pdf_reportlab import (
    COR_BORDA, COR_FUNDO_CABECALHO, LARGURA_UTIL, MARGEM_H, MARGEM_V, PAGE_SIZE, estilo_titulo,
)

COL_INDICE, COL_SISBOV, COL_NASC, COL_RACA, COL_SEXO, COL_INCL = 50, 115, 95, 60, 50, 95
COL_ERAS = LARGURA_UTIL - (COL_INDICE + COL_SISBOV + COL_NASC + COL_RACA + COL_SEXO + COL_INCL)

estilo_data_carga = ParagraphStyle('DataCarga', fontName='Helvetica-Bold', fontSize=10, alignment=TA_CENTER)


def _tabela_animais(animais):
    linhas = [['Índice', 'Código SISBOV', 'Nascimento', 'Raça', 'Sexo', 'Data Inclusão', 'ERAS']]
    for a in animais:
        linhas.append([str(a[0]), a[1], a[2], a[3], a[4], a[5], a[6]])
    tabela = Table(linhas, colWidths=[COL_INDICE, COL_SISBOV, COL_NASC, COL_RACA, COL_SEXO, COL_INCL, COL_ERAS], repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COR_FUNDO_CABECALHO),
        ('GRID', (0, 0), (-1, -1), 0.5, COR_BORDA),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),   # depois da regra geral (a ultima vence)
    ]))
    return tabela


def montar_pdf_carga(dados, data_carga, animais, colunas_faixas, resumo):
    """animais: lista de tuplas (indice, sisbov, nascimento 'dd/mm/aaaa', raca (codigo de 2 letras), sexo 'M'/'F',
    data inclusao 'dd/mm/aaaa', texto da faixa de ERAS). resumo: {'FEMEA': [4 ints], 'MACHO': [4 ints]}."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PAGE_SIZE, leftMargin=MARGEM_H, rightMargin=MARGEM_H,
                            topMargin=MARGEM_V, bottomMargin=MARGEM_V, title='Relatório da Carga')
    rodape = _criar_rodape(f'Impressão: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')

    story = [Paragraph('RELATÓRIO DA CARGA', estilo_titulo), Spacer(1, 10)]
    story += _cabecalho_produtor(dados)
    story.append(Paragraph(f'Data da Carga: {data_carga.strftime("%d/%m/%Y")} &nbsp;&nbsp;&#8212;&nbsp;&nbsp; {len(animais)} animais', estilo_data_carga))
    story.append(Spacer(1, 8))
    story.append(_tabela_animais(animais))
    story.append(Spacer(1, 10))
    story.append(KeepTogether([_quadro_resumo(colunas_faixas, resumo, len(animais))]))   # so no fim: ultima pagina

    doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
    buffer.seek(0)
    return buffer


def gerar_pdf_carga(dados, data_carga, animais, colunas_faixas, resumo):
    buffer = montar_pdf_carga(dados, data_carga, animais, colunas_faixas, resumo)
    nome = (dados.get('nome') or 'Propriedade').replace(' ', '_')
    arquivo = f'Relatorio_da_Carga_{nome}_{data_carga.strftime("%d-%m-%Y")}.pdf'
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=arquivo)

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_carga.py
# =========================================================
