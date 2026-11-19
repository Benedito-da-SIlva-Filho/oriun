# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\pdf_linkagem.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-10 21:20 -03
# ATUALIZADO EM: 2026-11-17 11:30 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     PDF "Relatorio da Linkagem RFID e Brinco do dia", NO VISUAL DO MAGIC/GERAS (A4 retrato), igual ao dos Conferidos dos Pesos
#     (mesmas pecas: _it, _Desenho, escala S, DADOS DA ORIGEM DOS ANIMAIS). So desenha: nao acessa o banco. Recebe um dict de
#     contexto montado por backend/routers/linkagem_consulta.py e devolve um BytesIO para send_file().
#
#     Layout: titulo em duas linhas, "Impressao", barra DADOS DA ORIGEM DOS ANIMAIS (Produtor, CPF/CNPJ, Inscr. Estadual, Produtor Rural,
#     Propriedade, Municipio/UF/CEP), caixa Linkagem + Qtde Animais, tabela Indice | Codigo SISBOV | RFID | Manejo | Sexo | Raca | Lote |
#     Peso, e no fim o quadro Femeas / Machos / Total / Peso Total / Media Kg. Peso so aparece nos animais que foram pesados na Linkagem.
#
#     Chaves do contexto: data (dd/mm/aaaa), gerado_em_completo, produtor, cpf, cnpj, inscricao_estadual, codigo_eras, propriedade,
#     municipio, uf, cep, animais [{sisbov, rfid, manejo, sexo, raca, lote, peso}], femeas, machos, total, peso_total, peso_medio (None se ninguem foi pesado), sem_peso.
#
#     v1.0.0: Criacao (Sessao 120, 10/11/2026, 21:20 -03). Molde: pdf_pesos_conferidos.py. REVERSAO: remover este arquivo.
#     v1.1.0: Sessao 129 (2026-11-17 11:30 -03) - pedido da Certificadora: quadro final ganha PESO TOTAL e MEDIA (Kg) so dos animais com peso, e o aviso "N animais sem peso" quando houver. REVERSAO: .bak_antes_s129_peso_total.
# =========================================================

from io import BytesIO

from reportlab.lib import colors
from reportlab.platypus import KeepTogether, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.utils import pdf_reportlab as _rl
from backend.utils.pdf_anexo_saida import MARGEM_V_ANEXO, _Desenho, formatar_sisbov
from backend.utils.pdf_anexo_xix import CINZA as CINZA_MAGIC, S, _documentos_linha, _it, _y

# Colunas (pt da amostra, escaladas por S): Indice, SISBOV, RFID, Manejo, Sexo, Raca, Lote, Peso
LARGURAS = [32.3, 118.0, 118.0, 39.2, 39.2, 30.5, 70.0, 39.7]
ROTULOS = ['Indice', 'Código SISBOV', 'RFID', 'Manejo', 'Sexo', 'Raça', 'Lote', 'Peso']
ALTURA_CABECALHO = 14.4
ALTURA_LINHA = 17.9


def _num(valor, casas=2):
    if valor is None or valor == '':
        return ''
    texto = f'{float(valor):,.{casas}f}'
    return texto.replace(',', '#').replace('.', ',').replace('#', '.')


# -------------------------------------------------------
# Topo: titulo, impressao, DADOS DA ORIGEM e caixa Linkagem / Qtde Animais (y = distancia do topo, em pt da amostra)
# -------------------------------------------------------
def _topo(ctx):
    itens = [
        _it(0, 553.6, 4.0, 16.0, 'RELATÓRIO DA LINKAGEM RFID E BRINCO', 'Times-Bold', 15, borda=False),
        _it(0, 553.6, 22.0, 16.0, f"DO DIA {ctx.get('data', '')}", 'Times-Bold', 15, borda=False),
        _it(392.4, 553.3, 42.5, 7.9, f"Impressão: {ctx.get('gerado_em_completo', '')}", 'Helvetica-Bold', 7, alinha='r', borda=False),
        _it(1.8, 551.8, 53.7, 13.6, 'DADOS DA ORIGEM DOS ANIMAIS', 'Times-Bold', 11, fundo=True),
    ]

    def rotulo(y, texto, x0=56.5, x1=129.8):
        itens.append(_it(x0, x1, y, 10.7, texto, alinha='r'))

    def valor(y, x0, x1, texto, alinha='c'):
        itens.append(_it(x0, x1, y, 10.7, texto or '', alinha=alinha))

    passo = 12.3
    y = 68.8
    rotulo(y, 'Produtor:')
    valor(y, 132.1, 433.0, ctx.get('produtor'), 'l')

    y += passo
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
    rotulo(y, 'CEP:', 345.0, 375.0)
    valor(y, 377.0, 433.0, ctx.get('cep'))

    y += passo + 2.0   # caixa Linkagem | data | Qtde Animais | n
    itens += [
        _it(121.0, 204.6, y, 13.6, 'Linkagem', 'Times-Bold', 11, fundo=True),
        _it(206.0, 289.0, y, 13.6, str(ctx.get('data', '')), 'Times-Bold', 11),
        _it(322.0, 396.0, y, 13.6, 'Qtde Animais', 'Times-Bold', 11, fundo=True),
        _it(398.0, 434.0, y, 13.6, str(ctx.get('total', 0)), 'Times-Bold', 11),
    ]
    return _Desenho(itens, _y(y + 14.0))


# -------------------------------------------------------
# Tabela dos animais (cabecalho repetido a cada pagina)
# -------------------------------------------------------
def _tabela_animais(animais):
    dados = [ROTULOS]
    for i, a in enumerate(animais, start=1):
        dados.append([
            f'{i:04d}', formatar_sisbov(a.get('sisbov')), a.get('rfid') or '', a.get('manejo') or '',
            a.get('sexo') or '', a.get('raca') or '', a.get('lote') or '', _num(a.get('peso')),
        ])
    alturas = [ALTURA_CABECALHO * S] + [ALTURA_LINHA * S] * (len(dados) - 1)
    tabela = Table(dados, colWidths=[w * S for w in LARGURAS], rowHeights=alturas, repeatRows=1, hAlign='CENTER')
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), CINZA_MAGIC),
        ('BOX', (0, 0), (-1, -1), 0.72, colors.black),
        ('LINEAFTER', (0, 0), (-2, -1), 0.72, colors.black),
        ('LINEBELOW', (0, 0), (-1, -2), 0.72, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 1), ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, 0), 8 * S),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (-1, -1), 8 * S),
        ('FONTNAME', (1, 1), (2, -1), 'Times-Bold'), ('FONTSIZE', (1, 1), (2, -1), 9.5 * S),
        ('FONTNAME', (4, 1), (4, -1), 'Helvetica-Bold'), ('FONTSIZE', (4, 1), (4, -1), 6.5 * S),
    ]))
    return tabela


# -------------------------------------------------------
# Quadro final: Femeas / Machos / Total
# -------------------------------------------------------
def _quadro_final(ctx):
    # v1.1.0: Femeas | Machos | Total | Peso Total | Media Kg (peso e media so dos animais pesados) + aviso de animais sem peso.
    peso_total = ctx.get('peso_total')
    peso_medio = ctx.get('peso_medio')
    if peso_total is None or peso_medio is None:
        txt_total = txt_media = '-'
    else:
        txt_total = _num(peso_total, 0 if float(peso_total).is_integer() else 2)
        txt_media = _num(peso_medio, 2)
    itens = []
    x = 0.0
    for rotulo, valor in (('Fêmeas', ctx.get('femeas', 0)), ('Machos', ctx.get('machos', 0)), ('Total', ctx.get('total', 0)),
                          ('Peso Total', txt_total), ('Média Kg', txt_media)):
        itens.append(_it(x, x + 70.0, 0.0, 14.0, rotulo, 'Times-Bold', 12))
        itens.append(_it(x, x + 70.0, 15.6, 20.0, str(valor), 'Times-Bold', 11))
        x += 71.3
    sem_peso = int(ctx.get('sem_peso') or 0)
    if sem_peso:
        itens.append(_it(0.0, 356.0, 38.0, 10.0,
                         f"Peso Total e Média consideram só os animais pesados ({sem_peso} sem peso).",
                         'Helvetica', 7, alinha='l', borda=False))
        return _Desenho(itens, _y(50.0))
    return _Desenho(itens, _y(36.0))


def _rodape_factory(ctx):
    def desenhar(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(_rl.MARGEM_H, 18, f"Relatório da Linkagem RFID e Brinco — {ctx.get('data', '')} — gerado pela plataforma Orion SISBOV em {ctx.get('gerado_em_completo', '')}")
        canvas.drawRightString(_rl.PAGE_SIZE[0] - _rl.MARGEM_H, 18, f'Página {doc.page}')
        canvas.restoreState()
    return desenhar


def gerar_pdf_linkagem(ctx):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=_rl.PAGE_SIZE,
        leftMargin=_rl.MARGEM_H, rightMargin=_rl.MARGEM_H, topMargin=MARGEM_V_ANEXO, bottomMargin=34,
        title='Relatório da Linkagem RFID e Brinco', author='Orion SISBOV',
    )
    historia = [_topo(ctx), Spacer(1, _y(6)), _tabela_animais(ctx.get('animais') or []), Spacer(1, _y(8)),
                KeepTogether([_quadro_final(ctx)])]
    rodape = _rodape_factory(ctx)
    doc.build(historia, onFirstPage=rodape, onLaterPages=rodape)
    buffer.seek(0)
    return buffer

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_linkagem.py
# =========================================================
