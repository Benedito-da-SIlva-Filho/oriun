# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\pdf_pesagem_relatorios.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-17 11:30 -03
# ATUALIZADO EM: 2026-11-17 11:30 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Motor unico dos RELATORIOS DE PESAGEM em PDF (Sessao 129), no visual do Magic/GERAS: titulo em Times-Bold, linha(s) de periodo/lote,
#     barra Propriedade + Produtor, tabela com cabecalho cinza repetido a cada pagina e quadro de totais. So desenha: nao acessa o banco.
#     Quem monta os dados e escolhe as colunas de cada relatorio e backend/routers/pesos_relatorios.py.
#
#     Chaves do contexto (dict):
#       titulo, subtitulos [texto, ...], produtor, propriedade, gerado_em_completo,
#       colunas [(rotulo, peso_relativo_da_largura, alinha 'l'|'c'|'r')], linhas [[texto, ...]],
#       negrito [indices de coluna em negrito], total_ultima_linha (bool - ultima linha da tabela em negrito, ex.: "Totais"),
#       totais [(rotulo, valor), ...] (quadro final, 3 por linha), nota (texto pequeno opcional), paisagem (bool).
#
#     v1.0.0: Criacao (Sessao 129, 17/11/2026, 11:30 -03). REVERSAO: remover este arquivo, pesos_relatorios.py e pesos_relatorios.html e as 3 linhas de registro (app.py, permissoes.py, hub_entrada_agrupado.py).
# =========================================================

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, KeepTogether

CINZA = colors.Color(0.941176, 0.941176, 0.941176)   # #F0F0F0, o cinza das barras no Magic
MARGEM = 28
_ALINHA = {'l': TA_LEFT, 'c': TA_CENTER, 'r': TA_RIGHT}


def _p(texto, estilo):
    return Paragraph(escape(str(texto if texto is not None else '')), estilo)


def gerar_pdf_pesagem_relatorio(ctx):
    tamanho = landscape(A4) if ctx.get('paisagem') else A4
    largura = tamanho[0] - 2 * MARGEM
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=tamanho, leftMargin=MARGEM, rightMargin=MARGEM, topMargin=26, bottomMargin=34,
                            title=ctx.get('titulo', 'Relatório de Pesagem'), author='Orion SISBOV')

    est_titulo = ParagraphStyle('t', fontName='Times-Bold', fontSize=15, leading=18, alignment=TA_CENTER)
    est_sub = ParagraphStyle('s', fontName='Times-Bold', fontSize=11, leading=14, alignment=TA_CENTER)
    est_imp = ParagraphStyle('i', fontName='Helvetica-Bold', fontSize=7, leading=9, alignment=TA_RIGHT)
    est_barra = ParagraphStyle('b', fontName='Times-Bold', fontSize=11, leading=13, alignment=TA_CENTER)
    est_nota = ParagraphStyle('n', fontName='Helvetica', fontSize=7.5, leading=9, textColor=colors.HexColor('#444444'))

    historia = [_p(ctx.get('titulo', ''), est_titulo)]
    for sub in ctx.get('subtitulos') or []:
        historia.append(_p(sub, est_sub))
    historia.append(_p(f"Impressão: {ctx.get('gerado_em_completo', '')}", est_imp))
    historia.append(Spacer(1, 3))

    barra = Table([[_p(ctx.get('propriedade', ''), est_barra)], [_p(ctx.get('produtor', ''), est_barra)]], colWidths=[largura * 0.7], hAlign='CENTER')
    barra.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.7, colors.black), ('LINEBELOW', (0, 0), (-1, 0), 0.7, colors.black),
                               ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
    historia += [barra, Spacer(1, 6)]

    # ---- tabela ----
    colunas = ctx['colunas']
    soma = float(sum(c[1] for c in colunas)) or 1.0
    larguras = [largura * c[1] / soma for c in colunas]
    tam = 8 if not ctx.get('paisagem') else 7.5
    negrito = set(ctx.get('negrito') or [])
    est_cab = ParagraphStyle('c', fontName='Helvetica-Bold', fontSize=tam, leading=tam + 1.5, alignment=TA_CENTER)
    estilos = []
    for i, c in enumerate(colunas):
        estilos.append(ParagraphStyle(f'col{i}', fontName='Helvetica-Bold' if i in negrito else 'Helvetica', fontSize=tam,
                                      leading=tam + 1.5, alignment=_ALINHA.get(c[2], TA_CENTER)))
    estilos_total = [ParagraphStyle(f'tot{i}', parent=e, fontName='Helvetica-Bold') for i, e in enumerate(estilos)]

    dados = [[_p(c[0], est_cab) for c in colunas]]
    linhas = ctx.get('linhas') or []
    for n, linha in enumerate(linhas):
        ultima_total = ctx.get('total_ultima_linha') and n == len(linhas) - 1
        base = estilos_total if ultima_total else estilos
        dados.append([_p(v, base[i]) for i, v in enumerate(linha)])
    tabela = Table(dados, colWidths=larguras, repeatRows=1, hAlign='CENTER')
    estilo_tab = [
        ('BACKGROUND', (0, 0), (-1, 0), CINZA),
        ('GRID', (0, 0), (-1, -1), 0.6, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2), ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]
    if ctx.get('total_ultima_linha') and len(dados) > 1:
        estilo_tab.append(('BACKGROUND', (0, len(dados) - 1), (-1, len(dados) - 1), CINZA))
    tabela.setStyle(TableStyle(estilo_tab))
    historia.append(tabela)

    # ---- quadro de totais (3 pares por linha) ----
    totais = ctx.get('totais') or []
    if totais:
        historia.append(Spacer(1, 10))
        est_rot = ParagraphStyle('r', fontName='Times-Bold', fontSize=11, leading=13, alignment=TA_RIGHT)
        est_val = ParagraphStyle('v', fontName='Times-Bold', fontSize=11, leading=13, alignment=TA_CENTER)
        linhas_tot = []
        for i in range(0, len(totais), 3):
            grupo = totais[i:i + 3]
            linha = []
            for rot, val in grupo:
                linha += [_p(f'{rot}:', est_rot), _p(val, est_val)]
            while len(linha) < 6:
                linha += [_p('', est_rot)]
            linhas_tot.append(linha)
        un = largura / 3.0
        tab_tot = Table(linhas_tot, colWidths=[un * 0.58, un * 0.40] * 3, hAlign='CENTER')
        est_t = [('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]
        for r, linha in enumerate(linhas_tot):
            n_pares = min(3, len(totais) - r * 3)
            for k in range(n_pares):
                est_t.append(('BOX', (2 * k + 1, r), (2 * k + 1, r), 0.7, colors.black))
                est_t.append(('BACKGROUND', (2 * k + 1, r), (2 * k + 1, r), CINZA))
        tab_tot.setStyle(TableStyle(est_t))
        historia.append(KeepTogether([tab_tot]))
    if ctx.get('nota'):
        historia += [Spacer(1, 6), _p(ctx['nota'], est_nota)]

    def rodape(canvas, doc_):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(MARGEM, 16, f"{ctx.get('titulo', '')} — gerado pela plataforma Orion SISBOV em {ctx.get('gerado_em_completo', '')}")
        canvas.drawRightString(tamanho[0] - MARGEM, 16, f'Página {doc_.page}')
        canvas.restoreState()

    doc.build(historia, onFirstPage=rodape, onLaterPages=rodape)
    buffer.seek(0)
    return buffer

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_pesagem_relatorios.py
# =========================================================
