# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\pdf_nascimentos_periodo.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-02 17:00 -03
# ATUALIZADO EM: 2026-10-21 11:10 -03
# VERSAO: 2.3.0
#
# DESCRICAO:
#     Monta o PDF do relatorio "Nascimentos por Periodo" (A4 RETRATO, em pe)
#     a partir de um dict de contexto (montado por backend/routers/
#     nascimentos_periodo.py). SO desenha - nao acessa o banco. Devolve
#     um BytesIO pronto para send_file().
#
#     Conteudo: cabecalho (Produtor, Propriedade, periodo), quadro-
#     resumo (total, machos, femeas, CTH), tabela RESUMO POR
#     NOTIFICACAO e tabela dos ANIMAIS (cabecalho repetido a cada
#     pagina; rodape "Pagina X de Y"). SEXO e RACA da tabela de animais
#     chegam ja em MAIUSCULAS e SEM ACENTO (regra de Benedito, Sessao
#     084) - funcao maiusculo_sem_acento() exportada para o router.
#
#     Chaves do contexto: produtor, cpf_cnpj, propriedade, municipio_uf,
#     codigo_eras, periodo, gerado_em, totais {qtde, machos, femeas,
#     cth, notificacoes}, notificacoes [{notificacao, data_brincagem,
#     qtde, machos, femeas, cth, situacao}], animais [{notificacao,
#     data_brincagem, sisbov, manejo, sexo, raca, nascimento, meses,
#     lote, cth}].
#
#     v1.0.0: Criacao do modulo (Sessao 084, 02/10/2026, 17:00 -03).
#     v1.1.0: Sessao 084 (02/10/2026, 17:30 -03) - pedido de Benedito: o
#             relatorio e RETRATO (A4 em pe), nao paisagem - cabe no
#             formulario padrao. Larguras das colunas e fontes refeitas
#             para a pagina em pe. Conteudo igual ao da v1.0.0.
#     v1.2.0: Sessao 084 (02/10/2026, 18:00 -03) - o MESMO PDF serve ao
#             relatorio Nascimento por Numero de Controle: o contexto aceita
#             as chaves opcionais 'titulo', 'titulo_rodape' e
#             'rotulo_periodo' (sem elas, sai igual ao de Nascimentos por
#             Periodo). Nenhuma outra mudanca.
#     v1.3.0: Sessao 095 (13/10/2026, 11:23 -03) - COR DA CONSISTE: o relatorio usava o vinho
#             (#7a1f04) como cor de barra e fundo de faixa proprio. Agora usa a cor padrao
#             (COR_PRIMARIA e COR_FUNDO_TOTAL de pdf_reportlab.py), igual aos demais
#             documentos. Nenhuma outra mudanca. REVERSAO: devolver .bak_antes_cor_padrao.
#     v2.0.0: Sessao 102 (21/10/2026, 10:10 -03) - NASCIMENTOS POR PERIODO NO VISUAL DO MAGIC/GERAS ("ENTRADA DE ANIMAIS -
#             Nascimento e Desmame"): medidas tiradas do PDF vetorial do Magic. Quando o contexto traz a chave 'grupos'
#             (lista de {numero, data_entrada, animais}) sai o layout novo; chaves novas do contexto: cpf, cnpj,
#             inscricao_estadual, uf, nirf, periodo_inicial, periodo_final, gerado_em_completo. SEM 'grupos' (Nascimento
#             por Numero de Controle) o layout antigo continua igual (funcao _gerar_pdf_legado). Categoria = faixa de
#             idade pelos meses completos na brincagem (como a Notificacao). REVERSAO: .bak_antes_visual_magic_s102.
#     v2.1.0: Sessao 102 (21/10/2026, 10:40 -03) - NASCIMENTO POR NUMERO DE CONTROLE no modelo do Magic/GERAS (Comunicado de
#             Insercao BND/SISBOV, sem Termo e sem assinaturas, grade sem Brincagem): novo modo ctx['tipo'] == 'controle'.
#             O layout antigo (_gerar_pdf_legado) fica no arquivo, sem uso na tela. Rodape usa 'titulo_rodape' do contexto.
#             REVERSAO: .bak_antes_controle_s102.
#     v2.2.0: Sessao 102 (21/10/2026, 10:55 -03) - AJUSTES (Benedito): (1) quadro RESUMO por Codigo Interno sem as colunas em
#             branco: blocos lado a lado, ate 3 por linha, cabecalho so na 1a linha (como as GTAs do Anexo XIX); (2) a coluna
#             APTIDAO saiu das duas grades (sua largura foi para a Categoria). REVERSAO: .bak_antes_aptidao_s102.
#     v2.3.0: Sessao 102 (21/10/2026, 11:10 -03) - LIMPEZA (Benedito): saem o quadro RESUMO por Codigo Interno e a linha "Total Geral de
#             Animais" do topo - ja aparecem em cada bloco (Codigo/Entrada/Qtde) e no quadro Sexo/Geral do fim. Os blocos comecam
#             logo depois dos dados do destino. REVERSAO: .bak_antes_limpeza_s102.
# =========================================================

import unicodedata
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle

from backend.utils.pdf_reportlab import COR_PRIMARIA, COR_FUNDO_TOTAL   # v1.3.0 - cor padrao
from reportlab.platypus import CondPageBreak, KeepTogether, PageBreak, SimpleDocTemplate   # v2.0.0
from backend.utils import pdf_reportlab as _rl   # v2.0.0 - margens e pagina do Orion
from backend.utils.pdf_anexo_saida import MARGEM_V_ANEXO, _Desenho, formatar_sisbov   # v2.0.0
from backend.utils.pdf_anexo_xix import CINZA as CINZA_MAGIC, S, _documentos_linha, _it, _y   # v2.0.0
from backend.utils.pdf_notificacao_nascimento import _resumo as _resumo_sexo_faixa, _aviso_acima   # v2.0.0
COR_FAIXA = COR_FUNDO_TOTAL
COR_LINHA = colors.HexColor('#bdbdbd')
COR_ZEBRA = colors.HexColor('#f7f7f7')

LARGURA, ALTURA = A4
MARGEM = 12 * mm
LARGURA_UTIL = LARGURA - 2 * MARGEM

_base = ParagraphStyle('base', fontName='Helvetica', fontSize=9, leading=11)
_celula = ParagraphStyle('celula', parent=_base, fontSize=7.5, leading=9)
_centro = ParagraphStyle('centro', parent=_celula, alignment=TA_CENTER)
_th = ParagraphStyle('th', parent=_centro, fontName='Helvetica-Bold', fontSize=7, leading=8.5, textColor=colors.white)
_rotulo = ParagraphStyle('rotulo', parent=_base, fontName='Helvetica-Bold', fontSize=7, textColor=colors.HexColor('#777777'), leading=8.5)
_valor = ParagraphStyle('valor', parent=_base, fontName='Helvetica-Bold', fontSize=10, leading=12)
_secao = ParagraphStyle('secao', parent=_base, fontName='Helvetica-Bold', fontSize=10, textColor=colors.white, leading=12)


def maiusculo_sem_acento(texto):
    """SEXO e RACA da tabela: maiusculas, sem acento."""
    if not texto:
        return texto or ''
    sem_acento = unicodedata.normalize('NFKD', str(texto)).encode('ascii', 'ignore').decode('ascii')
    return sem_acento.upper()


def _esc(valor):
    return (str(valor) if valor not in (None, '') else '—').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class _CanvasNumerado(rl_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        self._contexto = kwargs.pop('contexto')
        super().__init__(*args, **kwargs)
        self._paginas = []

    def showPage(self):
        self._paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._paginas)
        for estado in self._paginas:
            self.__dict__.update(estado)
            self.setStrokeColor(COR_LINHA)
            self.setLineWidth(0.5)
            self.line(MARGEM, 11 * mm, LARGURA - MARGEM, 11 * mm)
            self.setFont('Helvetica', 7.5)
            self.setFillColor(colors.HexColor('#666666'))
            self.drawString(MARGEM, 7 * mm, f"{self._contexto.get('titulo_rodape') or 'Nascimentos por Período'} — {self._contexto.get('periodo', '')} — gerado pela plataforma Orion SISBOV em {self._contexto.get('gerado_em', '')}")
            self.drawRightString(LARGURA - MARGEM, 7 * mm, f'Página {self._pageNumber} de {total}')
            super().showPage()
        super().save()


def _faixa(titulo):
    t = Table([[Paragraph(titulo, _secao)]], colWidths=[LARGURA_UTIL])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), COR_PRIMARIA), ('LEFTPADDING', (0, 0), (-1, -1), 8),
                           ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
    return t


def _cabecalho(ctx):
    titulo = ParagraphStyle('t', parent=_base, fontName='Helvetica-Bold', fontSize=15, leading=18, textColor=COR_PRIMARIA)
    campos = [
        ('Produtor', ctx.get('produtor')), ('CPF / CNPJ', ctx.get('cpf_cnpj')),
        ('Propriedade', ctx.get('propriedade')), ('Código ERAS', ctx.get('codigo_eras')),
        ('Município / UF', ctx.get('municipio_uf')), (ctx.get('rotulo_periodo') or 'Período (Data de Brincagem)', ctx.get('periodo')),
    ]
    celulas = [[Paragraph(r.upper(), _rotulo), Paragraph(_esc(v), _valor)] for r, v in campos]
    larg = LARGURA_UTIL / 2
    grade = Table([celulas[0:2], celulas[2:4], celulas[4:6]], colWidths=[larg] * 2)
    grade.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.6, COR_LINHA), ('INNERGRID', (0, 0), (-1, -1), 0.3, COR_LINHA),
                               ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 7),
                               ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    return [Paragraph(ctx.get('titulo') or 'NASCIMENTOS POR PERÍODO', titulo), Spacer(1, 2),
            Paragraph('Animais nascidos e identificados na propriedade (Nascimento / Desmame) — SISBOV', _base),
            Spacer(1, 6), grade]


def _quadro_resumo(ctx):
    t = ctx.get('totais') or {}
    caixas = [('Notificações', t.get('notificacoes', 0)), ('Total de animais', t.get('qtde', 0)),
              ('Machos', t.get('machos', 0)), ('Fêmeas', t.get('femeas', 0)), ('Cota Hilton', t.get('cth', 0))]
    valor_grande = ParagraphStyle('vg', parent=_valor, fontSize=14, leading=16, textColor=COR_PRIMARIA)
    celulas = [[[Paragraph(r.upper(), _rotulo), Paragraph(str(v), valor_grande)] for r, v in caixas]]
    tabela = Table(celulas, colWidths=[LARGURA_UTIL / len(caixas)] * len(caixas))
    tabela.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.8, COR_PRIMARIA), ('INNERGRID', (0, 0), (-1, -1), 0.3, COR_LINHA),
                                ('BACKGROUND', (0, 0), (-1, -1), COR_FAIXA), ('LEFTPADDING', (0, 0), (-1, -1), 8),
                                ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    return tabela


def _tabela_notificacoes(ctx):
    cab = ['Notificação', 'Data da Brincagem', 'Animais', 'Machos', 'Fêmeas', 'Cota Hilton', 'Situação']
    dados = [[Paragraph(c, _th) for c in cab]]
    for n in ctx.get('notificacoes') or []:
        dados.append([Paragraph(_esc(n.get('notificacao')), _centro), Paragraph(_esc(n.get('data_brincagem')), _centro),
                      Paragraph(str(n.get('qtde', 0)), _centro), Paragraph(str(n.get('machos', 0)), _centro),
                      Paragraph(str(n.get('femeas', 0)), _centro), Paragraph(str(n.get('cth', 0)), _centro),
                      Paragraph(_esc(n.get('situacao')), _celula)])
    larg = [28 * mm, 28 * mm, 16 * mm, 16 * mm, 16 * mm, 20 * mm]
    larg.append(LARGURA_UTIL - sum(larg))
    t = Table(dados, colWidths=larg, repeatRows=1)
    estilo = [('BACKGROUND', (0, 0), (-1, 0), COR_PRIMARIA), ('BOX', (0, 0), (-1, -1), 0.6, COR_LINHA),
              ('INNERGRID', (0, 0), (-1, -1), 0.3, COR_LINHA), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
              ('TOPPADDING', (0, 0), (-1, -1), 2.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5)]
    for i in range(2, len(dados), 2):
        estilo.append(('BACKGROUND', (0, i), (-1, i), COR_ZEBRA))
    t.setStyle(TableStyle(estilo))
    return t


def _tabela_animais(ctx):
    cab = ['Nº', 'Notificação', 'Data Brincagem', 'SISBOV', 'Manejo', 'Sexo', 'Raça', 'Nascimento', 'Meses', 'Lote', 'CTH']
    dados = [[Paragraph(c, _th) for c in cab]]
    for i, a in enumerate(ctx.get('animais') or [], start=1):
        dados.append([Paragraph(str(i), _centro), Paragraph(_esc(a.get('notificacao')), _centro),
                      Paragraph(_esc(a.get('data_brincagem')), _centro), Paragraph(_esc(a.get('sisbov')), _centro),
                      Paragraph(_esc(a.get('manejo')), _centro), Paragraph(_esc(a.get('sexo')), _centro),
                      Paragraph(_esc(a.get('raca')), _centro), Paragraph(_esc(a.get('nascimento')), _centro),
                      Paragraph(_esc(a.get('meses')), _centro), Paragraph(_esc(a.get('lote')), _celula),
                      Paragraph(_esc(a.get('cth')), _centro)])
    larg = [9 * mm, 22 * mm, 20 * mm, 29 * mm, 14 * mm, 16 * mm, 12 * mm, 19 * mm, 13 * mm, 0, 11 * mm]
    larg[9] = LARGURA_UTIL - sum(larg)
    t = Table(dados, colWidths=larg, repeatRows=1)
    estilo = [('BACKGROUND', (0, 0), (-1, 0), COR_PRIMARIA), ('BOX', (0, 0), (-1, -1), 0.6, COR_LINHA),
              ('INNERGRID', (0, 0), (-1, -1), 0.3, COR_LINHA), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
              ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]
    for i in range(2, len(dados), 2):
        estilo.append(('BACKGROUND', (0, i), (-1, i), COR_ZEBRA))
    t.setStyle(TableStyle(estilo))
    return t


def _gerar_pdf_legado(ctx):   # v2.0.0 - antes: gerar_pdf_nascimentos_periodo (usado so pelo Nascimento por Numero de Controle)
    buffer = BytesIO()

    def fabrica(*args, **kwargs):
        return _CanvasNumerado(*args, contexto=ctx, **kwargs)

    doc = BaseDocTemplate(buffer, pagesize=A4, leftMargin=MARGEM, rightMargin=MARGEM,
                          topMargin=MARGEM, bottomMargin=15 * mm,
                          title=(ctx.get('titulo_rodape') or 'Nascimentos por Período'), author='Orion SISBOV')
    quadro = Frame(MARGEM, 15 * mm, LARGURA_UTIL, ALTURA - MARGEM - 15 * mm,
                   leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id='pagina', frames=[quadro])])

    historia = _cabecalho(ctx) + [Spacer(1, 8), _quadro_resumo(ctx), Spacer(1, 8)]
    if ctx.get('animais'):
        historia += [_faixa('RESUMO POR NOTIFICAÇÃO'), _tabela_notificacoes(ctx), Spacer(1, 8),
                     _faixa('ANIMAIS NASCIDOS'), _tabela_animais(ctx)]
    else:
        historia += [Paragraph('Nenhum nascimento encontrado no período informado.', _base)]
    doc.build(historia, canvasmaker=fabrica)
    buffer.seek(0)
    return buffer

# =========================================================
# v2.0.0 - LAYOUT DO MAGIC/GERAS "ENTRADA DE ANIMAIS - Nascimento e Desmame"
# Medidas tiradas do PDF vetorial do Magic (Geras_Nascto_por_periodo.pdf, A4 retrato, Fazenda Nova Esperanca).
# Pecas reaproveitadas da Notificacao de Nascimento / Anexo XIX (mesma escala S).
# Usado quando o contexto traz a chave 'grupos' (Nascimentos por Periodo). Sem 'grupos' (Nascimento por
# Numero de Controle) continua saindo o layout antigo (_gerar_pdf_legado), sem nenhuma mudanca.
# =========================================================

# Categoria pela idade (meses completos na brincagem) - mesma regra da Notificacao de Nascimento.
FAIXAS_CATEGORIA = [(0, 3, 'Zero a 03 Meses'), (4, 7, '04 a 07 Meses'), (8, 10, '08 a 10 Meses')]

LARG_GRADE_M = [25.9, 28.8, 82.8, 38.2, 36.0, 43.2, 54.0, 54.0, 126.0, 30.2]   # v2.2.0 - sem Aptidao
ROT_GRADE_M = ['Ind', 'Qtde', 'Código SISBOV', 'Manejo', 'Espécie', 'Sexo', 'Nascimento', 'Brincagem',
               'Categoria', 'Raça']


def _categoria_por_meses(meses):
    """Rotulo da faixa de idade; vazio acima de 10 meses (so entra no Total, como na Notificacao)."""
    if meses is None:
        return ''
    for ini, fim, nome in FAIXAS_CATEGORIA:
        if ini <= meses <= fim:
            return nome
    return ''


# -------------------------------------------------------
# Topo: titulo, periodo, data de impressao e DADOS DO DESTINO (y = distancia do topo, na amostra)
# -------------------------------------------------------
def _topo_magic(ctx):
    itens = [
        _it(0, 553.6, 16.5, 14, 'ENTRADA DE ANIMAIS - Nascimento e Desmame', 'Times-Bold', 14, borda=False),
        _it(148.0, 361.4, 40.3, 10.1,
            f"Período: {ctx.get('periodo_inicial', '')} até {ctx.get('periodo_final', '')}",
            'Helvetica-Bold', 8, alinha='l', borda=False),
        _it(392.4, 553.3, 42.5, 7.9, f"Impressão: {ctx.get('gerado_em_completo', '')}",
            'Helvetica-Bold', 7, alinha='r', borda=False),
        _it(1.8, 551.8, 63.7, 13.6, 'DADOS DO DESTINO DOS ANIMAIS', 'Times-Bold', 11, fundo=True),
    ]

    def rotulo(y, texto, x0=56.5, x1=129.8):
        itens.append(_it(x0, x1, y, 10.7, texto, alinha='r'))

    def valor(y, x0, x1, texto, alinha='c'):
        itens.append(_it(x0, x1, y, 10.7, texto or '', alinha=alinha))

    passo = 12.3
    y = 78.8
    rotulo(y, 'Produtor:')
    valor(y, 132.1, 433.0, ctx.get('produtor'), 'l')

    y += passo   # CPF / CNPJ: so o que existe (regra por fazenda)
    r1, v1, r2, v2 = _documentos_linha({'cpf': ctx.get('cpf'), 'cnpj': ctx.get('cnpj')})
    rotulo(y, r1)
    valor(y, 132.1, 253.0, v1)
    if r2:
        rotulo(y, r2, 280.0, 311.6)
        valor(y, 313.9, 433.0, v2)

    y += passo
    rotulo(y, 'Inscr. Estadual:')
    valor(y, 132.1, 210.5, ctx.get('inscricao_estadual'))
    rotulo(y, 'Produtor Rural:', 320.0, 388.3)
    valor(y, 390.6, 433.0, str(ctx.get('codigo_eras') or ''))

    y += passo
    rotulo(y, 'Propriedade:')
    valor(y, 132.1, 433.0, ctx.get('propriedade'), 'l')

    y += passo
    rotulo(y, 'Municipio:')
    valor(y, 132.1, 312.7, ctx.get('municipio'))
    valor(y, 320.0, 340.8, ctx.get('uf'))

    y += passo
    rotulo(y, 'NIRF')
    valor(y, 132.1, 210.5, ctx.get('nirf'))

    return _Desenho(itens, _y(151.9))


# -------------------------------------------------------
# Um bloco por Codigo Interno: barra (Codigo | Entrada | Qtde) + grade dos animais
# -------------------------------------------------------
def _linha_codigo_magic(numero, data_entrada, qtde):
    return _Desenho([
        _it(58.0, 139.9, 0, 13.6, 'Código Interno', 'Times-Bold', 11, fundo=True),
        _it(141.5, 223.4, 0, 13.6, str(numero or ''), 'Times-Bold', 11),
        _it(246.6, 322.1, 0, 13.6, 'Entrada', 'Times-Bold', 11, fundo=True),
        _it(323.6, 399.1, 0, 13.6, str(data_entrada or ''), 'Times-Bold', 11),
        _it(424.4, 461.0, 0, 13.6, 'Qtde', 'Times-Bold', 11, fundo=True),
        _it(462.6, 499.2, 0, 13.6, str(qtde), 'Times-Bold', 11),
    ], _y(13.6))


def _grade_animais_magic(animais, ind_inicial):
    dados = [ROT_GRADE_M]
    for i, a in enumerate(animais):
        dados.append([
            str(ind_inicial + i), str(i + 1), formatar_sisbov(a.get('sisbov')), a.get('manejo') or '',
            a.get('especie') or '', maiusculo_sem_acento(a.get('sexo')), a.get('nascimento') or '',
            a.get('brincagem') or '', _categoria_por_meses(a.get('meses')),
            a.get('raca') or '',
        ])
    tabela = Table(dados, colWidths=[w * S for w in LARG_GRADE_M], rowHeights=[14.4 * S] * len(dados),
                   repeatRows=1, hAlign='CENTER')
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), CINZA_MAGIC),
        ('BOX', (0, 0), (-1, -1), 0.72, colors.black),
        ('LINEAFTER', (0, 0), (-2, -1), 0.72, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 0.72, colors.black),
        ('LINEBELOW', (0, 1), (-1, -2), 0.72, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 1), ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, 0), 8 * S),
        ('FONTNAME', (0, 1), (1, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (1, -1), 8 * S),
        ('FONTNAME', (2, 1), (-1, -1), 'Helvetica-Bold'), ('FONTSIZE', (2, 1), (-1, -1), 7 * S),
    ]))
    return tabela


def _rodape_magic_factory(ctx):
    """Rodape pequeno (acrescimo do Orion): identificacao e pagina - a lista pode passar de uma folha."""
    def desenhar(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(_rl.MARGEM_H, 18, f"{ctx.get('titulo_rodape') or 'Nascimentos por Período'} — {ctx.get('periodo', '')} — gerado pela plataforma Orion SISBOV em {ctx.get('gerado_em', '')}")
        canvas.drawRightString(_rl.PAGE_SIZE[0] - _rl.MARGEM_H, 18, f'Página {doc.page}')
        canvas.restoreState()
    return desenhar


def _gerar_pdf_magic(ctx):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=_rl.PAGE_SIZE,
        leftMargin=_rl.MARGEM_H, rightMargin=_rl.MARGEM_H, topMargin=MARGEM_V_ANEXO, bottomMargin=34,
        title='Nascimentos por Período', author='Orion SISBOV',
    )
    grupos = [g for g in (ctx.get('grupos') or []) if g.get('animais')]
    todos = [a for g in grupos for a in g['animais']]

    historia = [_topo_magic(ctx)]
    if not grupos:
        historia += [Spacer(1, 10), Paragraph('Nenhum nascimento encontrado no período informado.', _base)]
    else:
        ind = 1
        for posicao, g in enumerate(grupos):
            historia += [CondPageBreak(60 * S), Spacer(1, _y(6.0 if posicao == 0 else 7.4)),
                         _linha_codigo_magic(g['numero'], g['data_entrada'], len(g['animais'])),
                         Spacer(1, _y(2.2)), _grade_animais_magic(g['animais'], ind)]
            ind += len(g['animais'])
        resumo, acima = _resumo_sexo_faixa(todos)
        fim = [resumo]
        if acima:
            fim += [Spacer(1, _y(3)), _aviso_acima(acima)]
        historia += [Spacer(1, _y(8)), KeepTogether(fim)]

    rodape = _rodape_magic_factory(ctx)
    doc.build(historia, onFirstPage=rodape, onLaterPages=rodape)
    buffer.seek(0)
    return buffer


# -------------------------------------------------------
# v2.1.0 - NASCIMENTO POR NUMERO DE CONTROLE no modelo do Magic/GERAS ("Comunicado de Inserção BND/SISBOV -
# Animais Nascidos no ERAS", Geras_Nascto_Nro_Controle.pdf): origem + Codigo Interno + grade (sem Brincagem) +
# quadro por sexo e faixa. Sem Termo e sem assinaturas (a amostra nao tem). Usado com ctx['tipo'] == 'controle'.
# -------------------------------------------------------
LARG_GRADE_C = [34.9, 100.8, 43.2, 43.2, 43.2, 64.8, 136.1, 32.0]   # v2.2.0 - sem Aptidao
ROT_GRADE_C = ['Indice', 'Código SISBOV', 'Manejo', 'Espécie', 'Sexo', 'Nascimento', 'Categoria', 'Raça']


def _topo_controle(ctx, grupo):
    itens = [
        _it(120, 468, 12, 19, 'Comunicado de Inserção BND/SISBOV', 'Times-Bold', 16, borda=False),
        _it(120, 468, 33, 19, 'Animais Nascidos no ERAS', 'Times-Bold', 16, borda=False),
        _it(392.4, 553.3, 41.9, 7.9, f"Impressão: {ctx.get('gerado_em_completo', '')}",
            'Helvetica-Bold', 7, alinha='r', borda=False),
        _it(1.8, 551.8, 52.2, 13.6, 'DADOS DA ORIGEM DOS ANIMAIS', 'Times-Bold', 11, fundo=True),
    ]

    def rotulo(y, texto, x0=88.2, x1=161.5):
        itens.append(_it(x0, x1, y, 10.7, texto, alinha='r'))

    def valor(y, x0, x1, texto, alinha='c'):
        itens.append(_it(x0, x1, y, 10.7, texto or '', alinha=alinha))

    rotulo(67.3, 'Produtor:')
    valor(67.3, 163.8, 464.6, ctx.get('produtor'), 'l')
    r1, v1, r2, v2 = _documentos_linha({'cpf': ctx.get('cpf'), 'cnpj': ctx.get('cnpj')})
    rotulo(80.3, r1)
    valor(80.3, 163.8, 284.6, v1)
    if r2:
        rotulo(80.3, r2, 318.6, 350.2)
        valor(80.3, 353.2, 464.6, v2)
    rotulo(93.2, 'Inscr. Estadual:')
    valor(93.2, 163.8, 237.8, ctx.get('inscricao_estadual'))
    rotulo(93.2, 'Produtor Rural:', 352.4, 420.7)
    valor(93.2, 422.3, 464.6, str(ctx.get('codigo_eras') or ''))
    rotulo(106.2, 'Propriedade:')
    valor(106.2, 163.8, 464.6, ctx.get('propriedade'), 'l')
    rotulo(119.2, 'Municipio:')
    valor(119.2, 163.8, 344.4, ctx.get('municipio'))
    valor(119.2, 352.4, 373.2, ctx.get('uf'))
    rotulo(132.1, 'NIRF')
    valor(132.1, 163.8, 237.8, ctx.get('nirf'))

    for x0, x1, texto in ((88.2, 170.2, 'Código Interno'), (172.4, 247.9, grupo.get('numero')),
                          (261.7, 307.0, 'Entrada'), (308.5, 384.0, grupo.get('data_entrada')),
                          (394.9, 426.5, 'Qtde'), (428.0, 464.6, len(grupo['animais']))):
        itens.append(_it(x0, x1, 145.8, 13.6, str(texto or ''), 'Times-Bold', 11, fundo=True))
    return _Desenho(itens, _y(159.4))


def _grade_controle(animais):
    dados = [ROT_GRADE_C]
    for i, a in enumerate(animais, start=1):
        dados.append([
            str(i), formatar_sisbov(a.get('sisbov')), a.get('manejo') or '', a.get('especie') or '',
            maiusculo_sem_acento(a.get('sexo')), a.get('nascimento') or '', _categoria_por_meses(a.get('meses')),
            a.get('raca') or '',
        ])
    tabela = Table(dados, colWidths=[w * S for w in LARG_GRADE_C],
                   rowHeights=[14.4 * S] + [15.1 * S] * (len(dados) - 1), repeatRows=1, hAlign='CENTER')
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), CINZA_MAGIC),
        ('BOX', (0, 0), (-1, -1), 0.72, colors.black),
        ('LINEAFTER', (0, 0), (-2, -1), 0.72, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 0.72, colors.black),
        ('LINEBELOW', (0, 1), (-1, -2), 0.72, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 1), ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, -1), 8 * S),
        ('FONTNAME', (4, 1), (4, -1), 'Helvetica-Bold'), ('FONTSIZE', (4, 1), (4, -1), 7 * S),
    ]))
    return tabela


def _gerar_pdf_controle_magic(ctx):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=_rl.PAGE_SIZE,
        leftMargin=_rl.MARGEM_H, rightMargin=_rl.MARGEM_H, topMargin=MARGEM_V_ANEXO, bottomMargin=34,
        title='Nascimento por Número de Controle', author='Orion SISBOV',
    )
    grupos = [g for g in (ctx.get('grupos') or []) if g.get('animais')]
    historia = []
    for indice, grupo in enumerate(grupos):
        if indice:
            historia.append(PageBreak())
        resumo, acima = _resumo_sexo_faixa(grupo['animais'])
        fim = [resumo]
        if acima:
            fim += [Spacer(1, _y(3)), _aviso_acima(acima)]
        historia += [_topo_controle(ctx, grupo), Spacer(1, _y(2.2)), _grade_controle(grupo['animais']),
                     Spacer(1, _y(6.6)), KeepTogether(fim)]
    if not grupos:
        historia = [Spacer(1, 10), Paragraph('Nenhum animal encontrado para este número de controle.', _base)]

    rodape = _rodape_magic_factory(ctx)
    doc.build(historia, onFirstPage=rodape, onLaterPages=rodape)
    buffer.seek(0)
    return buffer


# -------------------------------------------------------
# Funcao publica: 'grupos' + tipo 'controle' = Nascimento por Numero de Controle (Magic); so 'grupos' =
# Nascimentos por Periodo (Magic); sem 'grupos' = layout antigo (_gerar_pdf_legado, hoje sem uso na tela).
# -------------------------------------------------------
def gerar_pdf_nascimentos_periodo(ctx):
    if ctx.get('grupos') is not None:
        if ctx.get('tipo') == 'controle':
            return _gerar_pdf_controle_magic(ctx)
        return _gerar_pdf_magic(ctx)
    return _gerar_pdf_legado(ctx)

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_nascimentos_periodo.py
# =========================================================
