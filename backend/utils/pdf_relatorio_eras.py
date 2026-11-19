# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\pdf_relatorio_eras.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-09-17 10:20 -03
# ATUALIZADO EM: 2026-10-21 12:05 -03
# VERSAO:       2.0.1
#
# DESCRICAO:
#     Geracao do PDF do Relatorio de ERAS, ReportLab puro. Chamado por backend/routers/relatorio_eras.py::gerar().
#
#     v2.0.0: Sessao 102 (21/10/2026, 11:50 -03) - VISUAL DO MAGIC/GERAS (decisao de Benedito: PDFs no visual do Magic).
#             Medidas tiradas do PDF vetorial "Geras Relatorio de ERas" (A4 retrato): titulo "Relatorio de ERAS" + faixa em todas as
#             paginas (Times-Bold 18); tabela Indice | Sisbov | Manejo | RFID | Sexo | Raca | Liberacao Abate | Inclusao | LOTE com
#             cabecalho repetido e colunas de linha dupla; fecha com "Total de Animais:" em quadro. Bloco de dados da origem (Produtor,
#             CPF/CNPJ por fazenda, Insc. Estadual, Cod. ERAS, Propriedade, Municipio/UF, NIRF) so na 1a pagina - acrescimo do Orion
#             (o Magic nao tem), mantido por decisao da Sessao 054. SAIRAM: Nascimento, Idade Atual, CTH e o quadro Sexo x Cota Hilton
#             (o Magic nao tem). Raca vai em codigo (NE, XX...), como no Magic. Assinatura ganhou o parametro "contexto" (opcional).
#             REVERSAO: devolver .bak_antes_visual_magic_s102 (1.9.0) e o relatorio_eras.py 1.1.0.
#     v2.0.1: Sessao 102 (21/10/2026, 12:05 -03) - CABECALHO NO PADRAO DO ORION (igual ao Nascimentos por Periodo): barra cinza + Produtor,
#             CPF/CNPJ, Insc. Estadual, Produtor Rural, Propriedade, Municipio/UF, NIRF em caixas. Tabela e total iguais a 2.0.0.
#     v1.0.0 a v1.9.0: layout antigo (padrao Orion, retrato, com resumo Sexo x Cota Hilton).
# =========================================================

from datetime import datetime
from io import BytesIO

from flask import send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.utils.pdf_anexo_saida import LARGURA_UTIL as _LARGURA_DESENHO, _Desenho, formatar_sisbov
from backend.utils.pdf_anexo_xix import _documentos_linha, _it, _y

PAGINA = A4
MARGEM_H = 14
LARGURA_UTIL = PAGINA[0] - 2 * MARGEM_H
S = LARGURA_UTIL / 570.2                 # a tabela do Magic mede 570,2 pt
CINZA = colors.Color(0.941176, 0.941176, 0.941176)
ALTURA_LINHA = 15.84 * S
TOPO_TABELA = 66.0
MARGEM_INFERIOR = 22

GAP = 2.2   # espaco entre as colunas (a linha dupla do Magic)
# (rotulo, largura, negrito no corpo)
COLUNAS = [('Indice', 33.8, False), ('Sisbov', 92.9, True), ('Manejo', 44.7, True), ('RFID', 77.1, False),
           ('Sexo', 38.9, False), ('Raça', 33.8, False), ('Liberação Abate', 69.8, False),
           ('Inclusão', 69.8, False), ('LOTE', 90.7, False)]


def _texto(valor):
    return '' if valor in (None, '-') else str(valor)


def _data(d):
    return d.strftime('%d/%m/%Y') if d else ''


def _pagina_factory(faixa, gerado_em):
    def desenhar(canvas, doc):
        largura, altura = PAGINA
        canvas.saveState()
        canvas.setFillColor(colors.black)
        canvas.setFont('Times-Bold', 18)
        canvas.drawCentredString(largura / 2, altura - 31, 'Relatório de ERAS')
        canvas.drawCentredString(largura / 2, altura - 56, faixa.descricao)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(MARGEM_H, 9, f'Relatório de ERAS — gerado pela plataforma Orion SISBOV em {gerado_em}')
        canvas.drawRightString(largura - MARGEM_H, 9, f'Página {doc.page}')
        canvas.restoreState()
    return desenhar


def _bloco_origem(c):
    """Cabecalho padrao do Orion (mesmo do Nascimentos por Periodo): barra DADOS DO DESTINO + Produtor, CPF/CNPJ,
    Insc. Estadual, Produtor Rural, Propriedade, Municipio/UF e NIRF."""
    base = 3.7
    itens = [_it(1.8, 551.8, base, 13.6, 'DADOS DO PRODUTOR E DA PROPRIEDADE', 'Times-Bold', 11, fundo=True)]

    def rotulo(y, texto, x0=56.5, x1=129.8):
        itens.append(_it(x0, x1, y, 10.7, texto, alinha='r'))

    def valor(y, x0, x1, texto, alinha='c'):
        itens.append(_it(x0, x1, y, 10.7, texto or '', alinha=alinha))

    passo = 12.3
    y = base + 15.1
    rotulo(y, 'Produtor:')
    valor(y, 132.1, 433.0, c.get('produtor'), 'l')
    y += passo
    r1, v1, r2, v2 = _documentos_linha({'cpf': c.get('cpf'), 'cnpj': c.get('cnpj')})
    rotulo(y, r1)
    valor(y, 132.1, 253.0, v1)
    if r2:
        rotulo(y, r2, 280.0, 311.6)
        valor(y, 313.9, 433.0, v2)
    y += passo
    rotulo(y, 'Inscr. Estadual:')
    valor(y, 132.1, 210.5, c.get('inscricao_estadual'))
    rotulo(y, 'Produtor Rural:', 320.0, 388.3)
    valor(y, 390.6, 433.0, str(c.get('codigo_eras') or ''))
    y += passo
    rotulo(y, 'Propriedade:')
    valor(y, 132.1, 433.0, c.get('propriedade'), 'l')
    y += passo
    rotulo(y, 'Municipio:')
    valor(y, 132.1, 312.7, c.get('municipio'))
    valor(y, 320.0, 340.8, c.get('uf'))
    y += passo
    rotulo(y, 'NIRF')
    valor(y, 132.1, 210.5, c.get('nirf'))

    desenho = _Desenho(itens, _y(y + 12.0))
    envelope = Table([[desenho]], colWidths=[_LARGURA_DESENHO], hAlign='CENTER')
    envelope.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                                  ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
    return envelope


def _tabela(animais, racas):
    cab = [r for r, _, _ in COLUNAS]
    dados_cols = [cab]
    for i, a in enumerate(animais, start=1):
        dados_cols.append([
            str(i), formatar_sisbov(a.sisbov), _texto(a.manejo), _texto(a.rfid), _texto(a.sexo),
            racas.get(a.id_raca, ''), _data(a.liberacao_abate), _data(a.data_inclusao), _texto(a.lote),
        ])
    # intercala colunas de espaco (linha dupla do Magic)
    dados, larguras = [], []
    for k, (_, larg, _) in enumerate(COLUNAS):
        if k:
            larguras.append(GAP * S)
        larguras.append(larg * S)
    for linha in dados_cols:
        nova = []
        for k, v in enumerate(linha):
            if k:
                nova.append('')
            nova.append(v)
        dados.append(nova)
    t = Table(dados, colWidths=larguras, rowHeights=[ALTURA_LINHA] * len(dados), repeatRows=1, hAlign='CENTER')
    est = [('GRID', (0, 0), (-1, -1), 0.5, colors.black), ('BACKGROUND', (0, 0), (-1, 0), CINZA),
           ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
           ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, -1), 8 * S),
           ('LEFTPADDING', (0, 0), (-1, -1), 1), ('RIGHTPADDING', (0, 0), (-1, -1), 1),
           ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]
    for k, (_, _, negrito) in enumerate(COLUNAS):
        if negrito:
            est.append(('FONTNAME', (k * 2, 1), (k * 2, -1), 'Helvetica-Bold'))
    t.setStyle(TableStyle(est))
    return t


class _Total(Flowable):
    def __init__(self, total):
        super().__init__()
        self.total = str(total)

    def wrap(self, largura, altura):
        return LARGURA_UTIL, 34

    def draw(self):
        c = self.canv
        c.setFillColor(colors.black)
        c.setFont('Times-Bold', 18)
        w1 = stringWidth('Total de Animais:', 'Times-Bold', 18)
        c.setFont('Times-Bold', 24)
        w2 = stringWidth(self.total, 'Times-Bold', 24) + 14
        x0 = (LARGURA_UTIL - (w1 + 4 + w2)) / 2
        c.setFont('Times-Bold', 18)
        c.drawString(x0, 10, 'Total de Animais:')
        c.setLineWidth(0.72)
        c.rect(x0 + w1 + 4, 3, w2, 27, stroke=1, fill=0)
        c.setFont('Times-Bold', 24)
        c.drawCentredString(x0 + w1 + 4 + w2 / 2, 9.5, self.total)


# -------------------------------------------------------
# animais: Entrada (tb_2001) ja filtrados pela faixa e ordenados por Manejo pelo chamador.
# contexto (dict, opcional): produtor, cpf, cnpj, inscricao_estadual, codigo_eras, propriedade, municipio, uf, nirf, racas {id: codigo}
# -------------------------------------------------------
def gerar_pdf_relatorio_eras(animais, faixa, propriedade, produtor, contexto=None):
    c = dict(contexto or {})
    if not c:
        c = {'produtor': produtor.nome if produtor else '', 'propriedade': propriedade.nome if propriedade else '',
             'municipio': propriedade.municipio if propriedade else '', 'uf': propriedade.uf if propriedade else '',
             'codigo_eras': propriedade.codigo_eras if propriedade else '', 'cnpj': '', 'cpf': ''}
    racas = c.get('racas') or {}
    gerado_em = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PAGINA, leftMargin=MARGEM_H, rightMargin=MARGEM_H,
                            topMargin=TOPO_TABELA, bottomMargin=MARGEM_INFERIOR,
                            title='Relatório de ERAS', author='Orion SISBOV')
    historia = [_bloco_origem(c), Spacer(1, 6), _tabela(animais, racas), Spacer(1, 2), _Total(len(animais))]
    pagina = _pagina_factory(faixa, gerado_em)
    doc.build(historia, onFirstPage=pagina, onLaterPages=pagina)
    buffer.seek(0)

    nome_propriedade = (propriedade.nome if propriedade else 'Propriedade').replace(' ', '_')
    nome_arquivo = f'Relatorio_ERAS_{nome_propriedade}_{faixa.descricao.replace(" ", "_")}.pdf'
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_relatorio_eras.py
# =========================================================
