# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\pdf_pedido_gta.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-08 13:30 -03
# ATUALIZADO EM: 2026-11-13 18:35 -03
# VERSAO: 1.2.0
# v1.2.0: Sessao 123 (2026-11-13 18:35 -03) - AUDITORIA ETAPA 6 (Regra #14): o laranja vem de pdf_reportlab.COR_PRIMARIA (mesmo valor #D4370A; so limpeza). REVERSAO: .bak_antes_etapa6.
# v1.1.0: Sessao 118 (2026-11-08 14:40 -03) - Tabela Raca x faixa x sexo. REVERSAO: .bak_antes_s118_raca
# v1.0.0: Sessao 118 - Criacao. PDF de 1 pagina "Pedido de GTA" (substitui o botao Copiar pedido de GTA).
#
# DESCRICAO:
#     Monta o PDF "Pedido de GTA" (A4 retrato): Produtor, Propriedade, tipo da saida, data do embarque e a tabela
#     Sexo x faixa de idade (ERAS) com os animais lidos, para o escritorio pedir a GTA ao orgao do Estado com as MESMAS
#     categorias. SO desenha - nao acessa o banco. Chamado por backend\routers\saida_relatorio.py (rota pedido_pdf).
#
#     contexto (dict): tipo (ABATE/TRANSFER/VENDA/POSSE), produtor, propriedade, data_embarque (dd/mm/aaaa),
#         gerado_em_completo, colunas (faixas), resumo_machos, resumo_femeas (listas), sem_faixa_machos, sem_faixa_femeas,
#         total_machos, total_femeas, total
# =========================================================

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.utils.pdf_reportlab import COR_PRIMARIA

ROTULO = {'ABATE': 'ABATE', 'TRANSFER': 'TRANSFERÊNCIA', 'VENDA': 'VENDA', 'POSSE': 'ALTERAÇÃO DE POSSE'}
CINZA = colors.Color(0.941176, 0.941176, 0.941176)
LARANJA = COR_PRIMARIA   # v1.2.0 (Regra #14): a cor da marca vem de pdf_reportlab.py, nunca escrita de novo aqui


def gerar_pdf_pedido_gta(ctx):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
                            title='Pedido de GTA', author='Orion SISBOV')
    titulo = ParagraphStyle('t', fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=LARANJA)
    normal = ParagraphStyle('n', fontName='Helvetica', fontSize=10.5, leading=15)
    aviso = ParagraphStyle('a', fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=colors.HexColor('#8e0000'))
    pequeno = ParagraphStyle('p', fontName='Helvetica', fontSize=8, leading=10, textColor=colors.grey)
    cel = ParagraphStyle('c', fontName='Helvetica', fontSize=10, leading=12)

    tipo = ctx.get('tipo', 'ABATE')
    el = [Paragraph(f'PEDIDO DE GTA — {ROTULO.get(tipo, tipo)}', titulo), Spacer(1, 4 * mm)]
    el.append(Paragraph(f'<b>Produtor:</b> {ctx.get("produtor", "")}', normal))
    el.append(Paragraph(f'<b>Propriedade:</b> {ctx.get("propriedade", "")}', normal))
    el.append(Paragraph(f'<b>Embarque (leitura no brete) de:</b> {ctx.get("data_embarque", "")}', normal))
    el.append(Paragraph(f'<b>Total:</b> {ctx.get("total", 0)} animal(is)', normal))
    el.append(Spacer(1, 6 * mm))

    if ctx.get('linhas_raca'):   # s118 - Raca x faixa x sexo
        linhas = [['Raça', 'Faixa de idade (ERAS)', 'Machos', 'Fêmeas', 'Total']]
        for r, f, m, fe in ctx['linhas_raca']:
            linhas.append([Paragraph(str(r), cel), Paragraph(str(f), cel), m or '-', fe or '-', m + fe])
        linhas.append(['TOTAL', '', ctx.get('total_machos', 0), ctx.get('total_femeas', 0), ctx.get('total', 0)])
        t = Table(linhas, colWidths=[46 * mm, 54 * mm, 24 * mm, 24 * mm, 22 * mm], repeatRows=1)
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10), ('BACKGROUND', (0, 0), (-1, 0), CINZA), ('BACKGROUND', (0, -1), (-1, -1), CINZA),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.6, 0.6, 0.6)),
            ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        sm = sf = 0
        for r_, f_, m_, fe_ in ctx['linhas_raca']:
            if f_.startswith('SEM FAIXA'):
                sm += m_; sf += fe_
        el += [t, Spacer(1, 8 * mm)]
        if sm or sf:
            el.append(Paragraph('Atenção: há animais sem data de nascimento — confira antes de pedir a GTA.', aviso))
            el.append(Spacer(1, 3 * mm))
        el.append(Paragraph('Peça a GTA com estas categorias (raça, sexo e idade). Se a GTA vier diferente, o Orion não deixa vincular.', aviso))
        el.append(Spacer(1, 10 * mm))
        el.append(Paragraph(f'Gerado pelo Orion SISBOV em {ctx.get("gerado_em_completo", "")}', pequeno))
        doc.build(el)
        buf.seek(0)
        return buf

    linhas = [['Faixa de idade (ERAS)', 'Machos', 'Fêmeas', 'Total']]
    colunas = ctx.get('colunas') or []
    rm, rf = ctx.get('resumo_machos') or [], ctx.get('resumo_femeas') or []
    for i, faixa in enumerate(colunas):
        m = rm[i] if i < len(rm) else 0
        f = rf[i] if i < len(rf) else 0
        if m or f:
            linhas.append([Paragraph(str(faixa), cel), m or '-', f or '-', m + f])
    sm, sf = ctx.get('sem_faixa_machos', 0), ctx.get('sem_faixa_femeas', 0)
    if sm or sf:
        linhas.append([Paragraph('SEM FAIXA (sem data de nascimento)', cel), sm or '-', sf or '-', sm + sf])
    linhas.append(['TOTAL', ctx.get('total_machos', 0), ctx.get('total_femeas', 0), ctx.get('total', 0)])
    t = Table(linhas, colWidths=[80 * mm, 30 * mm, 30 * mm, 30 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10), ('BACKGROUND', (0, 0), (-1, 0), CINZA), ('BACKGROUND', (0, -1), (-1, -1), CINZA),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.6, 0.6, 0.6)),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    el += [t, Spacer(1, 8 * mm)]
    if sm or sf:
        el.append(Paragraph('Atenção: há animais sem data de nascimento — confira antes de pedir a GTA.', aviso))
        el.append(Spacer(1, 3 * mm))
    el.append(Paragraph('Peça a GTA com estas categorias (sexo e idade). Se a GTA vier diferente, o Orion não deixa vincular.', aviso))
    el.append(Spacer(1, 10 * mm))
    el.append(Paragraph(f'Gerado pelo Orion SISBOV em {ctx.get("gerado_em_completo", "")}', pequeno))
    doc.build(el)
    buf.seek(0)
    return buf
