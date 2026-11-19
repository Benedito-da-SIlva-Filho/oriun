# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\pdf_comunicado_posse.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-11-05 20:20 -03
# ATUALIZADO EM: 2026-11-05 20:20 -03
# VERSAO: 1.0.3
# v1.0.3: Sessao 115 - Campos em grade unica de 4 colunas: tracos verticais alinhados em todas as linhas. REVERSAO: .bak_antes_s115_ajuste3.
# v1.0.2: Sessao 115 - CPF (ou CNPJ) do Produtor de origem abaixo do nome, na assinatura. REVERSAO: .bak_antes_s115_ajuste2.
# v1.0.1: Sessao 115 - DTA numa coluna so (sem Serie/Numero separados) e nome da assinatura afastado do traco. REVERSAO: .bak_antes_s115_ajuste1.
# v1.0.0: Sessao 115 (05/11/2026) - Pacote 5: PDF "Comunicado de Alteracao de Posse" (modelo ORION proprio).
#
# DESCRICAO:
#     Documento unico (origem e destino juntos, sem marcacao Entrada/Saida), em 2 VIAS (a 2a via e uma copia completa
#     em paginas novas), com assinatura SO do Produtor de origem. Mesmo visual dos anexos de Saida (pdf_anexo_saida.py):
#     barras de secao cinza, rotulos em Times-Bold, valores em Helvetica-Bold, caixinhas com borda.
#
#     Campos: numero do Comunicado, cidade e data, "A" = Certificadora, Produtor de origem, Propriedade, Produtor de
#     destino, motivo (Venda / Heranca com X), DTA(s), Total / Machos / Femeas, justificativa, relacao dos animais
#     (SISBOV, Nascimento, Raca, Sexo, Data de Identificacao).
#
#     contexto (dict) - montado por comunicado_saida_display.montar_contexto_posse:
#         numero_comunicado, cidade, data (texto), certificadora,
#         origem:  produtor_nome, cpf, cnpj, inscricao_estadual, propriedade_nome, codigo_mapa, nirf_incra, municipio, uf
#         destino: produtor_nome, cpf_cnpj, propriedade_nome, codigo_mapa
#         motivo ('VENDA' / 'HERANCA'), justificativa
#         dtas: lista de {serie, numero, emissao, validade, animais}
#         total, machos, femeas
#         animais: lista de {sisbov, nascimento, raca, sexo, identificacao}
# =========================================================

from io import BytesIO

from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle

from backend.utils.pdf_anexo_saida import FUNDO_CINZA, formatar_documento, formatar_sisbov
from backend.utils.pdf_reportlab import LARGURA_UTIL, MARGEM_H, PAGE_SIZE

MARGEM_V = 28

_ROTULO = ParagraphStyle('rotulo', fontName='Times-Bold', fontSize=8.5, leading=10, alignment=2)
_VALOR = ParagraphStyle('valor', fontName='Helvetica-Bold', fontSize=8, leading=9.5)
_TEXTO = ParagraphStyle('texto', fontName='Helvetica', fontSize=8.5, leading=11)


def _esc(valor):
    texto = str(valor if valor is not None else '').strip()
    return texto.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _barra(titulo):
    t = Table([[titulo]], colWidths=[LARGURA_UTIL], rowHeights=[14])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), FUNDO_CINZA), ('BOX', (0, 0), (-1, -1), 0.7, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 10.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
    return t


def _campos(linhas):
    """linhas: lista de listas de (rotulo, valor, _). Grade unica de 4 colunas (rotulo | valor | rotulo | valor) para TODAS as linhas,
    assim os tracos verticais ficam alinhados; linha de 1 campo junta as 3 ultimas colunas."""
    larg_rot1, larg_rot2 = 80, 70
    resto = LARGURA_UTIL - larg_rot1 - larg_rot2
    cols = [larg_rot1, resto * 0.55, larg_rot2, resto * 0.45]
    tabelas = []
    for pares in linhas:
        if len(pares) == 1:
            rotulo, valor, _ = pares[0]
            linha = [Paragraph(_esc(rotulo), _ROTULO), Paragraph(_esc(valor), _VALOR), '', '']
            extra = [('SPAN', (1, 0), (3, 0))]
        else:
            (r1, v1, _), (r2, v2, _) = pares[0], pares[1]
            linha = [Paragraph(_esc(r1), _ROTULO), Paragraph(_esc(v1), _VALOR), Paragraph(_esc(r2), _ROTULO), Paragraph(_esc(v2), _VALOR)]
            extra = []
        t = Table([linha], colWidths=cols, rowHeights=[14])
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.7, colors.black), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 3), ('RIGHTPADDING', (0, 0), (-1, -1), 3)] + extra))
        tabelas.append(t)
        tabelas.append(Spacer(1, 1.2))
    return tabelas


def _topo(contexto, via):
    numero = f"{int(contexto['numero_comunicado']):06d}"
    t = Table([[Paragraph('<b>COMUNICADO DE ALTERAÇÃO DE POSSE</b>',
                          ParagraphStyle('t', fontName='Times-Bold', fontSize=15, leading=18, alignment=1)),
                Paragraph(f'<b>Nº {numero}</b><br/><font size="8">{via}</font>',
                          ParagraphStyle('n', fontName='Times-Bold', fontSize=12, leading=14, alignment=1))]],
              colWidths=[LARGURA_UTIL - 110, 110])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOX', (1, 0), (1, 0), 0.7, colors.black),
                           ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    return [t, Spacer(1, 4)]


def _via(contexto, via):
    c = contexto
    o, d = c['origem'], c['destino']
    el = _topo(c, via)
    el += _campos([[('Local e data:', f"{c.get('cidade') or ''}, {c.get('data') or ''}", None)],
                   [('À Certificadora:', c.get('certificadora') or '', None)]])
    el.append(Spacer(1, 3))

    el.append(_barra('PRODUTOR DE ORIGEM (QUEM TRANSFERE A POSSE)'))
    el.append(Spacer(1, 1.5))
    el += _campos([[('Produtor:', o.get('produtor_nome'), None)],
                   [('CPF:', formatar_documento(o.get('cpf')), None), ('CNPJ:', formatar_documento(o.get('cnpj')), None)],
                   [('Inscr. Estadual:', o.get('inscricao_estadual'), None)],
                   [('Propriedade:', o.get('propriedade_nome'), None)],
                   [('Cód. MAPA:', o.get('codigo_mapa'), None), ('NIRF/INCRA:', o.get('nirf_incra'), None)],
                   [('Município:', o.get('municipio'), None), ('UF:', o.get('uf'), None)]])
    el.append(Spacer(1, 3))

    el.append(_barra('PRODUTOR DE DESTINO (QUEM RECEBE A POSSE)'))
    el.append(Spacer(1, 1.5))
    el += _campos([[('Produtor:', d.get('produtor_nome'), None)],
                   [('CPF/CNPJ:', formatar_documento(d.get('cpf_cnpj')), None)],
                   [('Propriedade:', d.get('propriedade_nome'), None)],
                   [('Cód. MAPA:', d.get('codigo_mapa'), None)]])
    el.append(Spacer(1, 3))

    el.append(_barra('MOTIVO DA ALTERAÇÃO DE POSSE'))
    el.append(Spacer(1, 1.5))
    marca_v = 'X' if c.get('motivo') == 'VENDA' else ' '
    marca_h = 'X' if c.get('motivo') == 'HERANCA' else ' '
    m = Table([[Paragraph(f'( {marca_v} ) Venda', _VALOR), Paragraph(f'( {marca_h} ) Herança', _VALOR)]],
              colWidths=[LARGURA_UTIL / 2] * 2, rowHeights=[14])
    m.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.7, colors.black), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                           ('LEFTPADDING', (0, 0), (-1, -1), 8)]))
    el += [m, Spacer(1, 3)]

    el.append(_barra('DOCUMENTO DE TRANSFERÊNCIA ANIMAL (DTA)'))
    el.append(Spacer(1, 1.5))
    dados = [['DTA', 'Emissão', 'Validade', 'Animais']]
    for dta in c['dtas']:
        dados.append([dta['numero'], dta['emissao'], dta['validade'], str(dta['animais'])])
    t = Table(dados, colWidths=[LARGURA_UTIL * f for f in (0.31, 0.23, 0.23, 0.23)])
    t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.7, colors.black), ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f2f2f2')),
                           ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'), ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
                           ('FONTSIZE', (0, 0), (-1, -1), 8.5), ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                           ('TOPPADDING', (0, 0), (-1, -1), 1.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5)]))
    el += [t, Spacer(1, 3)]

    tot = Table([[Paragraph('Total de Animais:', _ROTULO), Paragraph(str(c['total']), _VALOR),
                  Paragraph('Machos:', _ROTULO), Paragraph(str(c['machos']), _VALOR),
                  Paragraph('Fêmeas:', _ROTULO), Paragraph(str(c['femeas']), _VALOR)]],
                colWidths=[110, 60, 70, 60, 70, 60], rowHeights=[14], hAlign='CENTER')
    tot.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.7, colors.black), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                             ('ALIGN', (1, 0), (1, 0), 'CENTER')]))
    el += [tot, Spacer(1, 4)]

    el.append(_barra('JUSTIFICATIVA'))
    el.append(Spacer(1, 1.5))
    j = Table([[Paragraph(_esc(c.get('justificativa')).replace('\n', '<br/>') or '&nbsp;', _TEXTO)]], colWidths=[LARGURA_UTIL])
    j.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.7, colors.black), ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 18)]))
    el += [j, Spacer(1, 4)]

    el.append(_barra('RELAÇÃO DOS ANIMAIS'))
    el.append(Spacer(1, 1.5))
    cab = ['Ind', 'SISBOV', 'Nascimento', 'Raça', 'Sexo', 'Data de Identificação']
    linhas = [cab] + [[str(i + 1), formatar_sisbov(a['sisbov']), a['nascimento'], a['raca'], a['sexo'], a['identificacao']]
                      for i, a in enumerate(c['animais'])]
    ta = Table(linhas, repeatRows=1,
               colWidths=[LARGURA_UTIL * f for f in (0.07, 0.19, 0.16, 0.22, 0.14, 0.22)])
    ta.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.7, colors.black), ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f2f2f2')),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'), ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 8.5), ('FONTSIZE', (0, 1), (-1, -1), 7.5),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
                            ('TOPPADDING', (0, 0), (-1, -1), 1.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5)]))
    el += [ta, Spacer(1, 40)]

    ass = Table([[''], [Paragraph(f"<b>{_esc(o.get('produtor_nome'))}</b>", ParagraphStyle('a', fontName='Helvetica', fontSize=8.5, alignment=1))],
                 [Paragraph('CPF/CNPJ: ' + _esc(formatar_documento(o.get('cpf') or o.get('cnpj'))), ParagraphStyle('a3', fontName='Helvetica', fontSize=8.5, alignment=1))],
                 [Paragraph('Produtor de origem', ParagraphStyle('a2', fontName='Times-Bold', fontSize=8.5, alignment=1))]],
                colWidths=[260], hAlign='CENTER', rowHeights=[16, 18, 12, 12])
    ass.setStyle(TableStyle([('LINEBELOW', (0, 0), (0, 0), 0.8, colors.black), ('VALIGN', (0, 1), (0, 1), 'BOTTOM'), ('TOPPADDING', (0, 1), (0, 1), 6)]))
    el.append(ass)
    return el


def gerar_pdf_posse(contexto):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PAGE_SIZE, leftMargin=MARGEM_H, rightMargin=MARGEM_H,
                            topMargin=MARGEM_V, bottomMargin=MARGEM_V)
    elementos = _via(contexto, '1ª via') + [PageBreak()] + _via(contexto, '2ª via')
    doc.build(elementos)
    buffer.seek(0)
    return buffer


# Chave da URL -> (funcao, sufixo do nome do arquivo) - mesmo formato de MODELOS em pdf_anexo_saida.py
MODELOS_POSSE = {'posse': (gerar_pdf_posse, 'comunicado_posse')}

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_comunicado_posse.py
# =========================================================
