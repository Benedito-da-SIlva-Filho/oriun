# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\pdf_notificacao_nascimento.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-02 09:00 -03
# ATUALIZADO EM: 2026-10-20 20:00 -03
# VERSAO:       2.0.0
#
# DESCRICAO:
#     Monta o PDF da NOTIFICACAO DE NASCIMENTO ("Comunicado de Insercao BND/SISBOV - Animais Nascidos no
#     ERAS") a partir de um dict de contexto (montado por backend/routers/notificacao_nascimento.py).
#     SO desenha: nao acessa banco. Devolve um BytesIO pronto para send_file().
#
#     v2.0.0 - REFEITO no modelo do Magic/GERAS (Sessao 101): as medidas vieram do PDF real
#     (Geras_Nasscto.pdf, Comunicado de Insercao NAS0000008, Fazenda Nova Esperanca). Usa as mesmas pecas dos
#     Anexos XIX e XX (caixinhas rotulo/valor, barras cinza #F0F0F0). Mudancas sobre a "carta" antiga:
#       - SAIU: destinatario Certificadora, prazo de 30 dias, local/data, assinatura da Certificadora.
#       - UM FORMULARIO POR FABRICANTE de brinco (criterio da PIA), cada um com a LOGO do fabricante no canto
#         superior esquerdo; sem logo (ou sem fabricante) o formulario sai sem logo, nunca quebra.
#       - TERMO DE DECLARACAO E RESPONSABILIDADE DO PRODUTOR (acrescentado ao modelo do GERAS), logo depois dos
#         dados da origem e antes do Controle Interno / Qtde, com a quantidade de animais do formulario.
#       - Coluna "Idade em Meses" = meses COMPLETOS entre o nascimento e a brincagem (calculado no router).
#       - Quadro-resumo Femeas/Machos por faixa: Zero a 03, 04 a 07 e 08 a 10 meses + Total + Geral. Animal com
#         mais de 10 meses entra so no Total (e o PDF avisa).
#       - CPF/CNPJ do Produtor: so CPF, so CNPJ ou os dois (mesma regra do Anexo XIX).
#
#     contexto (dict):
#         numero (str, ex.: NAS0000008), produtor, cpf, cnpj, inscricao_estadual, codigo_eras,
#         propriedade, municipio, uf, nirf, gerado_em (str)
#         grupos: lista de {logo (caminho do arquivo ou None),
#                  animais: [{sisbov, manejo, especie, sexo ('MACHO'/'FEMEA'), raca, nascimento, brincagem,
#                             meses (int ou None)}]}
#
#     v1.0.0 a v1.2.0: carta a Certificadora (Sessoes 084 e 095).
#     v2.0.0: Sessao 101 (20/10/2026, 20:00 -03) - modelo GERAS + Termo + um formulario por fabricante. REVERSAO: .bak_antes_geras_s101
# =========================================================

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    Flowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from backend.utils.pdf_reportlab import LARGURA_UTIL, MARGEM_H, PAGE_SIZE
from backend.utils.pdf_anexo_saida import MARGEM_V_ANEXO, _Desenho, formatar_sisbov
from backend.utils.pdf_anexo_xix import CINZA, S, _documentos_linha, _it, _y

TEXTO_TERMO = (
    'Declaro, sob as penas da lei, que os ({qtde}) animais listados nesta notificação nasceram '
    'na propriedade rural acima qualificada e foram identificados com os dispositivos do SISBOV '
    'dentro da idade máxima permitida pelas regras vigentes.'
)

FAIXAS = [(0, 3), (4, 7), (8, 10)]   # meses completos na brincagem

# Colunas da grade (largura em pt da amostra): Ind | SISBOV | Manejo | Especie | Sexo | Nascimento | Idade | Brincagem | Raca
LARGURAS_GRADE = [22.3, 86.4, 43.2, 46.8, 43.2, 57.6, 68.4, 57.6, 30.2]
ROTULOS_GRADE = ['Ind', 'SISBOV', 'Manejo', 'Espécie', 'Sexo', 'Nascimento', 'Idade em Meses', 'Brincagem', 'Raça']
ALTURA_LINHA_GRADE = 15.1
LOGO_L, LOGO_A = 108.0, 50.4


# -------------------------------------------------------
# Desenho com logo no canto superior esquerdo
# -------------------------------------------------------
class _DesenhoComLogo(_Desenho):
    def __init__(self, itens, altura, logo=None):
        super().__init__(itens, altura)
        self.logo = logo

    def draw(self):
        super().draw()
        if not self.logo:
            return
        try:
            self.canv.drawImage(self.logo, 0, self.altura - LOGO_A * S, width=LOGO_L * S, height=LOGO_A * S,
                                preserveAspectRatio=True, anchor='nw', mask='auto')
        except Exception as erro:   # logo ilegivel nunca derruba o formulario
            print(f'[NASCIMENTO] Logo ilegivel ({self.logo}): {erro}')


def _sem_acento_maiusculo(texto):
    import unicodedata
    if not texto:
        return ''
    return unicodedata.normalize('NFKD', str(texto)).encode('ascii', 'ignore').decode('ascii').upper()


# -------------------------------------------------------
# Topo: titulo + DADOS DA ORIGEM (posicoes da amostra; y = distancia do topo da pagina)
# -------------------------------------------------------
def _topo(ctx, logo):
    itens = [
        _it(120, 468, 12, 19, 'Comunicado de Inserção BND/SISBOV', 'Times-Bold', 16, borda=False),
        _it(120, 468, 33, 19, 'Animais Nascidos no ERAS', 'Times-Bold', 16, borda=False),
        _it(1.8, 551.8, 52.2, 13.6, 'DADOS DA ORIGEM DOS ANIMAIS', 'Times-Bold', 11, fundo=True),
    ]

    def linha(y, rotulo, valor, x1_valor=464.6):
        itens.append(_it(88.2, 161.5, y, 10.7, rotulo, alinha='r'))
        itens.append(_it(163.8, x1_valor, y, 10.7, valor))

    linha(67.3, 'Produtor:', ctx.get('produtor') or '')

    r1, v1, r2, v2 = _documentos_linha(ctx)
    itens.append(_it(88.2, 161.5, 80.3, 10.7, r1, alinha='r'))
    itens.append(_it(163.8, 284.6, 80.3, 10.7, v1))
    if r2:
        itens.append(_it(318.6, 350.2, 80.3, 10.7, r2, alinha='r'))
        itens.append(_it(353.2, 463.9, 80.3, 10.7, v2))

    linha(93.2, 'Inscr. Estadual:', ctx.get('inscricao_estadual') or '', 284.6)
    itens.append(_it(352.4, 420.7, 93.2, 10.7, 'Produtor Rural:', alinha='r'))
    itens.append(_it(422.3, 464.6, 93.2, 10.7, str(ctx.get('codigo_eras') or '')))

    linha(106.2, 'Propriedade:', ctx.get('propriedade') or '')
    linha(119.2, 'Municipio:', ctx.get('municipio') or '', 344.4)
    itens.append(_it(352.4, 373.2, 119.2, 10.7, ctx.get('uf') or ''))
    linha(132.1, 'NIRF', ctx.get('nirf') or '', 284.6)

    return _DesenhoComLogo(itens, _y(143.5), logo)


# -------------------------------------------------------
# Termo de Declaracao e Responsabilidade do Produtor
# -------------------------------------------------------
def _termo(qtde):
    barra = _Desenho([_it(1.8, 551.8, 0, 13.6, 'TERMO DE DECLARAÇÃO E RESPONSABILIDADE DO PRODUTOR',
                          'Times-Bold', 11, fundo=True)], _y(13.6))
    estilo = ParagraphStyle('termo', fontName='Helvetica', fontSize=8 * S, leading=10.5 * S, alignment=TA_JUSTIFY)
    texto = Table([[Paragraph(TEXTO_TERMO.format(qtde=qtde), estilo)]], colWidths=[455.7 * S], hAlign='CENTER')
    texto.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                               ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
    return [Spacer(1, _y(3)), barra, Spacer(1, _y(5)), texto, Spacer(1, _y(4))]


# -------------------------------------------------------
# Controle Interno | Qtde
# -------------------------------------------------------
def _linha_controle(numero, qtde):
    itens = [
        _it(88.2, 181.0, 0, 13.6, 'Controle Interno', 'Times-Bold', 11, fundo=True),
        _it(182.5, 258.0, 0, 13.6, str(numero or ''), 'Times-Bold', 11, fundo=True),
        _it(394.9, 426.5, 0, 13.6, 'Qtde', 'Times-Bold', 11, fundo=True),
        _it(428.0, 464.6, 0, 13.6, str(qtde), 'Times-Bold', 11, fundo=True),
    ]
    return _Desenho(itens, _y(13.6))


# -------------------------------------------------------
# Grade dos animais (cabecalho repetido em cada pagina)
# -------------------------------------------------------
def _grade(animais):
    estilo_cab = ParagraphStyle('cab', fontName='Helvetica', fontSize=8 * S)
    dados = [ROTULOS_GRADE]
    for i, a in enumerate(animais, start=1):
        meses = a.get('meses')
        dados.append([
            str(i), formatar_sisbov(a.get('sisbov')), a.get('manejo') or '', a.get('especie') or '',
            _sem_acento_maiusculo(a.get('sexo')), a.get('nascimento') or '',
            '' if meses is None else str(meses), a.get('brincagem') or '', a.get('raca') or '',
        ])
    larguras = [w * S for w in LARGURAS_GRADE]
    tabela = Table(dados, colWidths=larguras, rowHeights=[14.4 * S] + [ALTURA_LINHA_GRADE * S] * (len(dados) - 1),
                   repeatRows=1, hAlign='CENTER')
    estilo = [
        ('BACKGROUND', (0, 0), (-1, 0), CINZA),
        ('BOX', (0, 0), (-1, -1), 0.72, colors.black),
        ('LINEAFTER', (0, 0), (-2, -1), 0.72, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 0.72, colors.black),
        ('LINEBELOW', (0, 1), (-1, -2), 0.72, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 1), ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, 0), 8 * S),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (0, -1), 8 * S),
        ('FONTNAME', (1, 1), (7, -1), 'Helvetica-Bold'), ('FONTSIZE', (1, 1), (7, -1), 7 * S),
        ('FONTNAME', (8, 1), (8, -1), 'Helvetica'), ('FONTSIZE', (8, 1), (8, -1), 8 * S),
    ]
    tabela.setStyle(TableStyle(estilo))
    return tabela


# -------------------------------------------------------
# Quadro-resumo por sexo e faixa de idade
# -------------------------------------------------------
def _contagens(animais):
    """{'FEMEA': [f1, f2, f3, total], 'MACHO': [...]}; acima de 10 meses so entra no total. Devolve tambem
    quantos tem mais de 10 meses."""
    quadro = {'FEMEA': [0, 0, 0, 0], 'MACHO': [0, 0, 0, 0]}
    acima = 0
    for a in animais:
        sexo = _sem_acento_maiusculo(a.get('sexo'))
        if sexo not in quadro:
            continue
        quadro[sexo][3] += 1
        meses = a.get('meses')
        achou = False
        if meses is not None:
            for i, (ini, fim) in enumerate(FAIXAS):
                if ini <= meses <= fim:
                    quadro[sexo][i] += 1
                    achou = True
                    break
        if not achou and meses is not None and meses > 10:
            acima += 1
    return quadro, acima


def _resumo(animais):
    quadro, acima = _contagens(animais)
    geral = quadro['FEMEA'][3] + quadro['MACHO'][3]
    base = 213.5
    cab = [(70.9, 113.3, 'Sexo'), (114.8, 187.4, 'Zero a 03 Meses'), (189.7, 262.3, '04 a 07 Meses'),
           (263.9, 336.5, '08 a 10 Meses'), (338.0, 410.6, 'Total')]
    itens = [_it(x0, x1, 0, 12.1, t, 'Times-Bold', 10) for x0, x1, t in cab]
    itens.append(_it(412.2, 481.2, 0, 17.1, 'Geral', 'Times-Bold', 14))
    for y, nome, chave in ((227.2 - base, 'Fêmeas', 'FEMEA'), (241.6 - base, 'Machos', 'MACHO')):
        itens.append(_it(70.9, 113.3, y, 12.1, nome, 'Times-Bold', 10))
        for (x0, x1, _), valor in zip(cab[1:], quadro[chave]):
            itens.append(_it(x0, x1, y, 12.1, str(valor), 'Times-Bold', 10))
    itens.append(_it(412.2, 481.2, 232.9 - base, 20.8, str(geral), 'Times-Bold', 12))
    return _Desenho(itens, _y(253.7 - base)), acima


# -------------------------------------------------------
# "1a via" + duas assinaturas (posicoes da amostra, relativas ao topo do bloco = 255)
# -------------------------------------------------------
class _Assinaturas(Flowable):
    def wrap(self, largura, altura):
        return LARGURA_UTIL, _y(115)

    def draw(self):
        c = self.canv
        topo = _y(115)
        origem = 255.0

        def base(y_topo, tam):
            return topo - _y(y_topo - origem + tam * 0.9)

        def px(pt):   # ponto da amostra -> pt a partir da borda esquerda da barra
            return (pt - 1.8) * S

        c.setFillColor(colors.black)
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.72)
        c.setFont('Helvetica-Bold', 8 * S)
        c.drawRightString(px(459.4), base(257, 8), '1ª via Órgão Executor da Sanidade Animal no Estado')
        for data_y, linha_y, linha_x0, linha_x1, rotulo_y, rotulo in (
            (285, 293.8, 279.4, 457.2, 298, 'Assinatura do Produtor ou Responsável Cadastrado'),
            (341, 349.2, 284.4, 462.2, 353, 'Assinatura do Responsável'),
        ):
            c.setFont('Helvetica-Bold', 8 * S)
            c.drawString(px(105.6), base(data_y, 8), 'Data: ____/____/______')
            y_linha = topo - _y(linha_y - origem)
            c.line(px(linha_x0), y_linha, px(linha_x1), y_linha)
            c.setFont('Helvetica-Bold', 7 * S)
            c.drawCentredString(px((linha_x0 + linha_x1) / 2), base(rotulo_y, 7), rotulo)


def _aviso_acima(acima):
    estilo = ParagraphStyle('aviso', fontName='Helvetica-Bold', fontSize=7.5 * S, leading=9 * S,
                            textColor=colors.HexColor('#B00020'), alignment=1)
    return Paragraph(f'ATENÇÃO: {acima} animal(is) com mais de 10 meses na brincagem — contado(s) apenas no Total.',
                     estilo)


# -------------------------------------------------------
# Rodape: identificacao e pagina (as listas longas passam de uma pagina)
# -------------------------------------------------------
def _rodape_factory(ctx):
    def desenhar(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.HexColor('#666666'))
        y = 18
        canvas.drawString(MARGEM_H, y, f"Notificação {ctx.get('numero', '')} — gerada pela plataforma Orion SISBOV em {ctx.get('gerado_em', '')}")
        canvas.drawRightString(PAGE_SIZE[0] - MARGEM_H, y, f'Página {doc.page}')
        canvas.restoreState()
    return desenhar


# -------------------------------------------------------
# Funcao publica
# -------------------------------------------------------
def gerar_pdf_notificacao_nascimento(ctx):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=PAGE_SIZE,
        leftMargin=MARGEM_H, rightMargin=MARGEM_H, topMargin=MARGEM_V_ANEXO, bottomMargin=34,
        title=f"Notificação de Nascimento {ctx.get('numero', '')}", author='Orion SISBOV',
    )

    historia = []
    grupos = [g for g in (ctx.get('grupos') or []) if g.get('animais')]
    for indice, grupo in enumerate(grupos):
        animais = grupo['animais']
        if indice:
            historia.append(PageBreak())
        historia.append(_topo(ctx, grupo.get('logo')))
        historia.extend(_termo(len(animais)))
        historia.append(_linha_controle(ctx.get('numero'), len(animais)))
        historia.append(Spacer(1, _y(3)))
        historia.append(_grade(animais))
        historia.append(Spacer(1, _y(8)))
        resumo, acima = _resumo(animais)
        fim = [resumo]
        if acima:
            fim += [Spacer(1, _y(3)), _aviso_acima(acima)]
        fim += [Spacer(1, _y(2)), _Assinaturas()]
        historia.append(KeepTogether(fim))

    rodape = _rodape_factory(ctx)
    doc.build(historia, onFirstPage=rodape, onLaterPages=rodape)
    buffer.seek(0)
    return buffer

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_notificacao_nascimento.py
# =========================================================
