# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\pdf_bnd_fazenda.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-11-18 20:00 -03
# ATUALIZADO EM: 2026-11-18 20:00 -03
# VERSAO:       1.0.0
#
# DESCRICAO:
#     Os 4 PDFs do BND/Fazenda (4 relatorios distintos). Cabecalho objetivo (decisao do Benedito): titulo que explica o que e
#     o relatorio, Propriedade e Produtor de quem e. Rodape padrao com a hora da impressao (_criar_rodape).
#       01 FAZENDA igual BND   - codigos em 5 colunas + Total
#       02 Fazenda nao BND     - codigos em 5 colunas + Total
#       03 BND nao Fazenda     - codigo, evento no Orion (Abate/Venda/Transferencia/Morte, sem Posse) e data + totais
#       04 Inconformidades     - codigo, Fazenda (sexo, nascimento, raca), mensagem, BND (sexo, nascimento, raca) +
#                                "SALDO DISPONIVEL" (= total de divergencias)
#     NAO consulta banco: recebe tudo pronto de backend\routers\bnd_fazenda.py. Raca em codigo de 2 letras (Regra #11).
#
#   v1.0.0: Criacao (BND/Fazenda, Sessao 132, 18/11/2026).
# =========================================================

from datetime import datetime
from io import BytesIO

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.utils.bnd_fazenda import formatar_sisbov
from backend.utils.pdf_inventario_geral import _criar_rodape
from backend.utils.pdf_reportlab import (
    COR_BORDA, COR_FUNDO_CABECALHO, LARGURA_UTIL, MARGEM_H, MARGEM_V, PAGE_SIZE,
)

TITULOS = {
    1: 'CÓDIGOS DO SISBOV QUE CONSTAM NA BND (MAPA)<br/>E NA FAZENDA TAMBÉM',
    2: 'CÓDIGOS DO SISBOV QUE CONSTAM NA FAZENDA<br/>E NÃO CONSTAM NA BND (MAPA)',
    3: 'CÓDIGOS QUE CONSTAM NA BND (MAPA)<br/>E NÃO CONSTAM NA FAZENDA',
    4: 'INCONFORMIDADES<br/>RELAÇÃO DOS CÓDIGOS SISBOV SUJEITOS A AVERIGUAÇÃO',
}
NOMES_ARQUIVO = {1: 'Fazenda_igual_BND', 2: 'Fazenda_nao_BND', 3: 'BND_nao_Fazenda', 4: 'Inconformidades'}

_est_titulo = ParagraphStyle('BndTitulo', fontName='Helvetica-Bold', fontSize=13, alignment=TA_CENTER, leading=17, spaceAfter=6)
_est_linha = ParagraphStyle('BndLinha', fontName='Helvetica-Bold', fontSize=11, alignment=TA_CENTER, leading=14)
_est_total = ParagraphStyle('BndTotal', fontName='Helvetica-Bold', fontSize=10, alignment=TA_CENTER, leading=14)


def nome_arquivo(numero, dados):
    nome = (dados.get('prop_nome') or 'Propriedade').replace(' ', '_').replace("'", '')
    return f'BND_Fazenda_{numero:02d}_{NOMES_ARQUIVO[numero]}_{nome}_{datetime.now():%d-%m-%Y}.pdf'


def _data(d):
    return d.strftime('%d/%m/%Y') if d else ''


def _estilo_grade(cabecalhos=1):
    return [
        ('GRID', (0, 0), (-1, -1), 0.5, COR_BORDA),
        ('BACKGROUND', (0, 0), (-1, cabecalhos - 1), COR_FUNDO_CABECALHO),
        ('FONTNAME', (0, 0), (-1, cabecalhos - 1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]


def _documento(numero, dados, corpo):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PAGE_SIZE, leftMargin=MARGEM_H, rightMargin=MARGEM_H,
                            topMargin=MARGEM_V, bottomMargin=MARGEM_V + 6, title=f'BND/Fazenda {numero:02d}')
    rodape = _criar_rodape(f'Impressão: {datetime.now():%d/%m/%Y %H:%M:%S}')
    story = [Paragraph(TITULOS[numero], _est_titulo),
             Paragraph(f'PRODUTOR: {dados.get("prod_nome") or ""}', _est_linha),
             Paragraph(f'PROPRIEDADE: {dados.get("prop_nome") or ""}', _est_linha),
             Spacer(1, 10)]
    story += corpo
    doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
    buffer.seek(0)
    return buffer


def _grade_codigos(sisbovs, colunas=5):
    linhas = [['Código'] * colunas]
    atual = []
    for s in sisbovs:
        atual.append(formatar_sisbov(s))
        if len(atual) == colunas:
            linhas.append(atual)
            atual = []
    if atual:
        linhas.append(atual + [''] * (colunas - len(atual)))
    t = Table(linhas, colWidths=[LARGURA_UTIL / colunas] * colunas, repeatRows=1)
    t.setStyle(TableStyle(_estilo_grade(1)))
    return t


def montar_codigos(numero, dados, sisbovs):
    """Relatorios 01 e 02."""
    corpo = []
    if sisbovs:
        corpo.append(_grade_codigos(sisbovs))
    else:
        corpo.append(Paragraph('Nenhum código nesta relação.', _est_total))
    corpo += [Spacer(1, 10), Paragraph(f'Total : {len(sisbovs)}', _est_total)]
    return _documento(numero, dados, corpo)


def montar_bnd_nao_fazenda(dados, sisbovs, eventos):
    """Relatorio 03. eventos: {sisbov: (nome do evento, data)}; quem nao esta la = sem registro no Orion."""
    larg = [130, 200, LARGURA_UTIL - 330]
    linhas = [['Código', 'Registro no Orion', 'Data']]
    com_evento = 0
    for s in sisbovs:
        ev = eventos.get(s)
        if ev:
            com_evento += 1
            linhas.append([formatar_sisbov(s), ev[0], _data(ev[1])])
        else:
            linhas.append([formatar_sisbov(s), 'Sem registro de saída', ''])
    corpo = []
    if sisbovs:
        t = Table(linhas, colWidths=larg, repeatRows=1)
        t.setStyle(TableStyle(_estilo_grade(1)))
        corpo.append(t)
    else:
        corpo.append(Paragraph('Nenhum código nesta relação.', _est_total))
    corpo += [Spacer(1, 10), Paragraph(f'Total : {len(sisbovs)}', _est_total),
              Paragraph(f'Com saída registrada no Orion (Abate, Venda, Transferência ou Morte): {com_evento}', _est_total),
              Paragraph(f'Sem registro de saída (o Produtor precisa descobrir o que aconteceu): {len(sisbovs) - com_evento}', _est_total)]
    return _documento(3, dados, corpo)


def montar_inconformidades(dados, inconformidades):
    """Relatorio 04. inconformidades: lista de dict (ver bnd_fazenda.comparar)."""
    larg = [92, 36, 52, 28, 0, 36, 52, 28]
    larg[4] = LARGURA_UTIL - sum(larg)
    linhas = [['', 'Fazenda', '', '', 'Mensagem de ERRO', 'BND', '', ''],
              ['Código', 'Sexo', 'Nascto', 'Raça', '', 'Sexo', 'Nascto', 'Raça']]
    for x in inconformidades:
        linhas.append([formatar_sisbov(x['sisbov']), x['f_sexo'] or '', _data(x['f_nascimento']), x['f_raca'],
                       x['mensagem'], x['b_sexo'] or '', _data(x['b_nascimento']), x['b_raca']])
    corpo = []
    if inconformidades:
        t = Table(linhas, colWidths=larg, repeatRows=2)
        estilo = _estilo_grade(2) + [('SPAN', (1, 0), (3, 0)), ('SPAN', (5, 0), (7, 0)), ('SPAN', (4, 0), (4, 1)),
                                     ('FONTSIZE', (0, 2), (-1, -1), 7.5), ('ALIGN', (4, 2), (4, -1), 'LEFT')]
        t.setStyle(TableStyle(estilo))
        corpo.append(t)
    else:
        corpo.append(Paragraph('Nenhuma inconformidade: os dados dos animais conferem com a BND.', _est_total))
    corpo += [Spacer(1, 10), Paragraph(f'SALDO DISPONIVEL: {len(inconformidades)}', _est_total)]
    return _documento(4, dados, corpo)

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_bnd_fazenda.py
# =========================================================
