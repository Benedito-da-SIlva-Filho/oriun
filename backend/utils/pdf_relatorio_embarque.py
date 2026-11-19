# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\pdf_relatorio_embarque.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-21 11:40 -03
# ATUALIZADO EM: 2026-11-01 17:40 -03
# VERSAO: 1.3.0
# v1.3.0: Sessao 111 (01/11/2026) - Venda e Morte (ver Diario de Bordo da Sessao 111). REVERSAO: arquivos .bak_antes_s111* ao lado.
#
# DESCRICAO:
#     Monta o PDF do "Relatorio de Embarque - ABATE" no visual do Magic/GERAS (A4 PAISAGEM). Medidas tiradas do PDF
#     vetorial do Magic (Geras_Relatorio_de_Embarque.pdf, embarque de 08/10/2026). SO desenha - nao acessa o banco.
#     Chamado por backend\routers\saida_relatorio.py (rota pdf).
#
#     Titulo e "Referente a Embarque do dia" em todas as paginas; bloco de dados da origem (acrescimo do Orion, pedido de
#     Benedito) so na 1a pagina; tabela de 15 colunas (Ind, Sisbov, RFID, Sexo, Idade em Meses, 1a Pesagem, 1o Peso, Saida,
#     Kgs, Dias, GPD, @ Vivo, @ Abate, Lote Entrada, Lote Saida) com cabecalho repetido; quadro final Sexo x faixas de idade
#     + Geral + Peso (total e media) + @ Vivo + @ Abate + GMP + Diarias. Numeros no formato brasileiro (virgula decimal).
#
#     contexto (dict):
#         produtor, cpf, cnpj, inscricao_estadual, codigo_eras, propriedade, municipio, uf, nirf,
#         data_embarque (dd/mm/aaaa), gerado_em_completo (dd/mm/aaaa hh:mm:ss)
#         animais: lista de {indice, sisbov, rfid, sexo, faixa, data_pesagem1, peso1, kgs, dias, gpd,
#                            arroba_vivo, arroba_abate, lote_entrada, lote_saida}  (numeros float/int ou None)
#         colunas (faixas de idade), resumo_femeas, resumo_machos (listas), total_femeas, total_machos, total,
#         pesos: {peso_total, peso_medio, arroba_vivo, arroba_abate, gmp, diarias}
#         fora_liberacao (int): animais fora da Liberacao para Abate (vira uma nota no fim)
#
#     v1.0.0: Criacao (Sessao 102, 21/10/2026, 11:40 -03).
#     v1.1.0: Sessao 103 (22/10/2026, 08:25 -03) - decisoes de Benedito: (1) CABECALHO PADRAO DO ORION (barra cinza + caixas, igual ao ERAS);
#             (2) SAIU a coluna Lote Entrada: fica so o Lote Saida (o router repete o de entrada quando nao ha de saida); (3) colunas novas
#             CTH (SIM/NAO por animal) e BC (Blockchain; sai vazia ate existir o selo) e CTH no quadro final (femeas/machos);
#             (4) SISBOV sem hifen (via formatar_sisbov). Saida e Kgs continuam duplicadas (ganho de peso = peso de saida - peso de entrada).
#             contexto novo: animais[].cth (bool), animais[].bc (bool), cth_femeas, cth_machos.  REVERSAO: .bak_antes_cth_bc_cabecalho_s103.
#     v1.2.0: Sessao 107 (28/10/2026) - contexto novo 'tipo' (TRANSFER troca o titulo para TRANSFERENCIA; sem tipo = ABATE).  REVERSAO: .bak_antes_s107y.
# =========================================================

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.utils.pdf_anexo_saida import LARGURA_UTIL as _LARGURA_DESENHO, _Desenho, formatar_sisbov
from backend.utils.pdf_anexo_xix import _documentos_linha, _it, _y

PAGINA = landscape(A4)
MARGEM_H = 40
LARGURA_UTIL = PAGINA[0] - 2 * MARGEM_H

CINZA = colors.Color(0.941176, 0.941176, 0.941176)   # #F0F0F0, o cinza do Magic

# A amostra do Magic mede 726,3 pt de largura na tabela; tudo e escalado para a largura util do Orion.
S = LARGURA_UTIL / 726.3
DESLOC = 14                    # pt abaixo da posicao do Magic (impressoras com margem)
TOPO_TABELA = 58.0 + DESLOC    # o titulo ocupa o alto da pagina; a tabela comeca abaixo
MARGEM_INFERIOR = 34

# Colunas da tabela principal (largura em pt da amostra) e rotulos (rotulo, tamanho da fonte)
LARGURAS = [24.45, 75.6, 68.4, 40.35, 97.2, 48.95, 32.4, 32.4, 32.4, 27.35, 28.8, 33.1, 33.85, 30.0, 26.0, 95.05]   # v1.1.0: sem Lote Entrada; com CTH e BC
ROTULOS = [('Ind', 8), ('Sisbov', 8), ('RFID', 8), ('Sexo', 8), ('Idade em Meses', 8), ('1ª Pesagem', 7),
           ('1º Peso', 7), ('Saída', 7), ('Kgs', 7), ('Dias', 7), ('GPD', 7), ('@ Vivo', 7), ('@ Abate', 7),
           ('CTH', 7), ('BC', 7), ('Lote Saida', 8)]
ALTURA_LINHA = 14.4


# -------------------------------------------------------
# Formatacao brasileira
# -------------------------------------------------------
def _num(valor, casas, milhar=False):
    if valor is None:
        return ''
    texto = f'{float(valor):,.{casas}f}' if milhar else f'{float(valor):.{casas}f}'
    return texto.replace(',', '#').replace('.', ',').replace('#', '.')


def _texto(valor):
    return '' if valor in (None, '-') else str(valor)


# -------------------------------------------------------
# Titulo em todas as paginas + rodape pequeno (acrescimo do Orion: identificacao e pagina)
# -------------------------------------------------------
def _pagina_factory(ctx):
    def desenhar(canvas, doc):
        largura, altura = PAGINA
        canvas.saveState()
        canvas.setFillColor(colors.black)
        canvas.setFont('Times-Bold', 16)
        canvas.drawCentredString(largura / 2, altura - (24.7 + DESLOC), {'TRANSFER': 'Relatório de Embarque TRANSFERÊNCIA', 'VENDA': 'Relatório de Embarque VENDA'}.get(ctx.get('tipo'), 'Relatório de Embarque ABATE'))
        canvas.drawCentredString(largura / 2, altura - (49.9 + DESLOC),
                                 f"Referente a Embarque do dia {ctx.get('data_embarque', '')}")
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(MARGEM_H, 18, f"Relatório de Embarque — gerado pela plataforma Orion SISBOV em {ctx.get('gerado_em_completo', '')}")
        canvas.drawRightString(largura - MARGEM_H, 18, f'Página {doc.page}')
        canvas.restoreState()
    return desenhar


# -------------------------------------------------------
# Cabecalho padrao do Orion (v1.1.0 - igual ao ERAS e ao Nascimentos por Periodo): barra cinza + Produtor, CPF/CNPJ,
# Insc. Estadual, Produtor Rural, Propriedade, Municipio/UF e NIRF em caixas. So na 1a pagina.
# -------------------------------------------------------
def _bloco_origem(c):
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


# -------------------------------------------------------
# Tabela dos animais (cabecalho repetido a cada pagina)
# -------------------------------------------------------
def _tabela_animais(animais):
    dados = [[r for r, _ in ROTULOS]]
    for a in animais:
        dados.append([
            str(a.get('indice', '')), formatar_sisbov(a.get('sisbov')), _texto(a.get('rfid')),
            {'MACHO': 'MACHO', 'FEMEA': 'FEMEA'}.get(a.get('sexo'), _texto(a.get('sexo'))), _texto(a.get('faixa')),
            _texto(a.get('data_pesagem1')), _num(a.get('peso1'), 1), _num(a.get('kgs'), 1), _num(a.get('kgs'), 1),
            '' if a.get('dias') is None else str(a['dias']), _num(a.get('gpd'), 3), _num(a.get('arroba_vivo'), 2),
            _num(a.get('arroba_abate'), 2), 'SIM' if a.get('cth') else 'NÃO', 'SIM' if a.get('bc') else '',
            _texto(a.get('lote_saida')),   # v1.1.0: o router ja repete o Lote Entrada quando nao ha Lote Saida
        ])
    tabela = Table(dados, colWidths=[w * S for w in LARGURAS], rowHeights=[ALTURA_LINHA * S] * len(dados),
                   repeatRows=1, hAlign='CENTER')
    estilo = [
        ('BACKGROUND', (0, 0), (-1, 0), CINZA),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.72, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 1), ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'), ('FONTSIZE', (0, 1), (-1, -1), 7 * S),
    ]
    for coluna, (_, tam) in enumerate(ROTULOS):
        estilo.append(('FONTSIZE', (coluna, 0), (coluna, 0), tam * S))
    tabela.setStyle(TableStyle(estilo))
    return tabela


# -------------------------------------------------------
# Quadro final: Sexo x faixas + Geral + Peso + @ Vivo + @ Abate + GMP + Diarias (medidas da amostra)
# -------------------------------------------------------
class _QuadroTotais(Flowable):
    ALTURA = 46.6

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    def wrap(self, largura, altura):
        return LARGURA_UTIL, self.ALTURA * S

    def draw(self):
        c = self.canv
        ctx = self.ctx
        pesos = ctx.get('pesos') or {}
        faixas = list(ctx.get('colunas') or [])
        femeas, machos = list(ctx.get('resumo_femeas') or []), list(ctx.get('resumo_machos') or [])
        largura_faixa = 72.6 if len(faixas) <= 3 else 56.0   # v1.1.0: faixas mais estreitas para caber a coluna CTH
        colunas = [('Sexo', 42.4, 10)] + [(f, largura_faixa, 10) for f in faixas] + [
            ('Total', 52.0, 10), ('Geral', 52.0, 14), ('Peso', 62.0, 14), ('@ Vivo', 44.0, 11),
            ('@ Abate', 44.0, 11), ('CTH', 44.0, 10), ('GMP', 40.0, 12), ('Diárias', 40.0, 12)]
        folga = 1.5
        topo = self.ALTURA * S

        def caixa(x0, x1, y0, y1, texto='', fonte='Times-Bold', tam=10):
            c.setLineWidth(0.72)
            c.setStrokeColor(colors.black)
            c.rect(x0 * S, topo - y1 * S, (x1 - x0) * S, (y1 - y0) * S, stroke=1, fill=0)
            if texto == '':
                return
            tam_ok = tam * S
            while tam_ok > 5 and stringWidth(texto, fonte, tam_ok) > (x1 - x0) * S - 3:
                tam_ok -= 0.25
            c.setFillColor(colors.black)
            c.setFont(fonte, tam_ok)
            c.drawCentredString((x0 + x1) / 2 * S, topo - ((y0 + y1) / 2) * S - tam_ok * 0.33, texto)

        linhas = {'cab': (0.0, 13.5), 'fem': (15.1, 30.1), 'mac': (31.6, 46.6)}
        x = 0.0
        for indice, (rotulo, largura, tam) in enumerate(colunas):
            x0, x1 = x, x + largura
            x = x1 + folga
            caixa(x0, x1, *linhas['cab'], rotulo, tam=tam)
            e_faixa = 1 <= indice <= len(faixas)
            if rotulo == 'Sexo':
                caixa(x0, x1, *linhas['fem'], 'Fêmeas')
                caixa(x0, x1, *linhas['mac'], 'Machos')
            elif e_faixa:
                caixa(x0, x1, *linhas['fem'], str(femeas[indice - 1] if indice - 1 < len(femeas) else 0))
                caixa(x0, x1, *linhas['mac'], str(machos[indice - 1] if indice - 1 < len(machos) else 0))
            elif rotulo == 'Total':
                caixa(x0, x1, *linhas['fem'], str(ctx.get('total_femeas', 0)))
                caixa(x0, x1, *linhas['mac'], str(ctx.get('total_machos', 0)))
            elif rotulo == 'Geral':
                caixa(x0, x1, linhas['fem'][0], linhas['mac'][1], str(ctx.get('total', 0)), tam=12)
            elif rotulo == 'Peso':
                caixa(x0, x1, *linhas['fem'], _num(pesos.get('peso_total'), 2, milhar=True))
                caixa(x0, x1, *linhas['mac'], _num(pesos.get('peso_medio'), 2, milhar=True))
            elif rotulo == '@ Vivo':
                caixa(x0, x1, *linhas['fem'], _num(pesos.get('arroba_vivo'), 1, milhar=True), tam=12)
            elif rotulo == '@ Abate':
                caixa(x0, x1, *linhas['fem'], _num(pesos.get('arroba_abate'), 1, milhar=True), tam=12)
            elif rotulo == 'CTH':   # v1.1.0: Cota Hilton - fêmeas e machos com CTH
                caixa(x0, x1, *linhas['fem'], str(ctx.get('cth_femeas', 0)))
                caixa(x0, x1, *linhas['mac'], str(ctx.get('cth_machos', 0)))
            elif rotulo == 'GMP':
                caixa(x0, x1, *linhas['fem'], _num(pesos.get('gmp'), 3), tam=12)
            elif rotulo == 'Diárias':
                caixa(x0, x1, *linhas['fem'], '' if pesos.get('diarias') is None else str(pesos['diarias']), tam=12)


def gerar_pdf_relatorio_embarque(ctx):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=PAGINA, leftMargin=MARGEM_H, rightMargin=MARGEM_H,
        topMargin=TOPO_TABELA, bottomMargin=MARGEM_INFERIOR,
        title='Relatório de Embarque', author='Orion SISBOV',
    )
    historia = [_bloco_origem(ctx), Spacer(1, 6 * S), _tabela_animais(ctx.get('animais') or []), Spacer(1, 4 * S),
                _QuadroTotais(ctx)]
    if ctx.get('fora_liberacao'):
        nota = ParagraphStyle('nota', fontName='Helvetica-Bold', fontSize=7.5, leading=9, textColor=colors.HexColor('#B00020'))
        historia += [Spacer(1, 4), Paragraph(
            f"ATENÇÃO: {ctx['fora_liberacao']} animal(is) fora da Liberação para Abate na data da leitura.", nota)]
    pagina = _pagina_factory(ctx)
    doc.build(historia, onFirstPage=pagina, onLaterPages=pagina)
    buffer.seek(0)
    return buffer

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_relatorio_embarque.py
# =========================================================
