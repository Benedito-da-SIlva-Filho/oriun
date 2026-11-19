# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\Orion\Manual
# MODULO: gerar_manual_cadastro.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 17/11/2026 22:11 -03
# ATUALIZADO EM: 17/11/2026 22:11 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Gera o PDF "Manual do Cadastro: Propriedade, Proprietario, Produtor e
#     Ativacao do Ambiente" para o usuario CONSISTE sem conhecimento previo.
#     Saidas (na mesma pasta):
#         Manual_Cadastro_Propriedade_Produtor_Ambiente.pdf
#         paginas.json   (pagina de cada capitulo; usado pelos botoes
#                         "Manual" das telas Propriedades, Proprietarios e
#                         Produtores para abrir o PDF no capitulo certo)
#     Para gerar de novo (quando uma tela mudar), rodar na pasta C:\Orion:
#         python Manual\gerar_manual_cadastro.py
#     As telas do manual sao DESENHOS esquematicos (nao fotos): nenhum dado de
#     cliente real aparece. Nomes e numeros dos exemplos sao inventados.
#     Reportlab puro. Cor padrao Orion: #D4370A (Regra #14).
#     v1.0.0: Criacao (17/11/2026).
# =========================================================

import json
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, KeepTogether, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA_PDF = os.path.join(AQUI, 'Manual_Cadastro_Propriedade_Produtor_Ambiente.pdf')
SAIDA_JSON = os.path.join(AQUI, 'paginas.json')

LARANJA = colors.HexColor('#D4370A')
LARANJA_CLARO = colors.HexColor('#FBE9E4')
CINZA_CLARO = colors.HexColor('#F2F2F2')
BORDA = colors.HexColor('#CCCCCC')
AZUL_CLARO = colors.HexColor('#E3F0FB')
AZUL = colors.HexColor('#1F4E79')
AMARELO_CLARO = colors.HexColor('#FFF6DD')
AMARELO = colors.HexColor('#B26A00')
VERDE_CLARO = colors.HexColor('#E8F3E8')
VERDE = colors.HexColor('#2E7D32')
VERMELHO_CLARO = colors.HexColor('#FDE7E7')
VERMELHO = colors.HexColor('#C62828')

LARGURA, ALTURA = A4
MARGEM = 20 * mm
LARGURA_UTIL = LARGURA - 2 * MARGEM

corpo = ParagraphStyle('corpo', fontName='Helvetica', fontSize=10.5, leading=15, spaceAfter=6, alignment=TA_LEFT)
h1 = ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=LARANJA, spaceAfter=10)
h2 = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=colors.HexColor('#333333'), spaceBefore=12, spaceAfter=6)
h3 = ParagraphStyle('h3', fontName='Helvetica-Bold', fontSize=11.5, leading=15, textColor=LARANJA, spaceBefore=8, spaceAfter=4)
capa_titulo = ParagraphStyle('capa_titulo', fontName='Helvetica-Bold', fontSize=30, leading=36, textColor=colors.white, alignment=TA_CENTER)
capa_sub = ParagraphStyle('capa_sub', fontName='Helvetica', fontSize=14, leading=19, textColor=colors.white, alignment=TA_CENTER)
celula = ParagraphStyle('celula', fontName='Helvetica', fontSize=9, leading=12)
celula_b = ParagraphStyle('celula_b', parent=celula, fontName='Helvetica-Bold')
celula_h = ParagraphStyle('celula_h', parent=celula, fontName='Helvetica-Bold', textColor=colors.white)
legenda = ParagraphStyle('legenda', parent=corpo, fontSize=9.5, leading=13, spaceAfter=3)


def P(texto, estilo=corpo):
    return Paragraph(texto, estilo)


class Capitulo(Paragraph):
    """Titulo de capitulo: registra a pagina em que cai (sumario e botoes das telas)."""
    def __init__(self, chave, texto):
        super().__init__(texto, h1)
        self.chave = chave


def caixa(tipo, titulo, texto):
    cores = {'dica': (AZUL_CLARO, AZUL), 'atencao': (AMARELO_CLARO, AMARELO),
             'importante': (VERMELHO_CLARO, VERMELHO), 'ok': (VERDE_CLARO, VERDE)}
    fundo, borda = cores[tipo]
    est_t = ParagraphStyle('ct', parent=celula_b, fontSize=10, leading=13, textColor=borda)
    est_x = ParagraphStyle('cx', parent=celula, fontSize=10, leading=14)
    t = Table([[Paragraph(titulo, est_t)], [Paragraph(texto, est_x)]], colWidths=[LARGURA_UTIL])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), fundo), ('LINEBEFORE', (0, 0), (0, -1), 3, borda),
        ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 6), ('BOTTOMPADDING', (0, -1), (-1, -1), 7),
        ('TOPPADDING', (0, 1), (-1, 1), 0), ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
    ]))
    return KeepTogether([t, Spacer(1, 8)])


def passo(numero, titulo, texto):
    bola = Table([[str(numero)]], colWidths=[9 * mm], rowHeights=[9 * mm])
    bola.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), LARANJA), ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                              ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 12),
                              ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    miolo = [Paragraph(f'<b>{titulo}</b>', ParagraphStyle('pt', parent=corpo, spaceAfter=2, fontSize=11)), Paragraph(texto, corpo)]
    t = Table([[bola, miolo]], colWidths=[13 * mm, LARGURA_UTIL - 13 * mm])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
    return KeepTogether([t, Spacer(1, 4)])


def tabela(cabecalho, linhas, larguras):
    dados = [[Paragraph(c, celula_h) for c in cabecalho]]
    for l in linhas:
        dados.append([Paragraph(str(c), celula_b if i == 0 else celula) for i, c in enumerate(l)])
    t = Table(dados, colWidths=larguras, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), LARANJA), ('GRID', (0, 0), (-1, -1), 0.5, BORDA),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t


def lista(itens):
    return [Paragraph(f'&bull;&nbsp;&nbsp;{i}', ParagraphStyle('li', parent=corpo, leftIndent=14, firstLineIndent=-10, spaceAfter=3)) for i in itens]


def legendas(itens):
    saida = [Paragraph(f'<font color="#D4370A"><b>{n}</b></font> &nbsp;&#8212;&nbsp; {t}', legenda) for n, t in itens]
    saida.append(Spacer(1, 8))
    return saida


def _cortar(texto, fonte, tam, largura):
    if stringWidth(texto, fonte, tam) <= largura:
        return texto
    while texto and stringWidth(texto + '...', fonte, tam) > largura:
        texto = texto[:-1]
    return texto + '...'


class TelaMock(Flowable):
    """Desenho esquematico de uma tela do Orion, com bolinhas numeradas (legendas logo abaixo)."""
    LARG = LARGURA_UTIL

    def __init__(self, titulo, menu_ativo=None, aviso=None, campos=(), botoes=(), linhas_tabela=None, cabecalho_tabela=None, busca=None):
        super().__init__()
        self.titulo, self.menu_ativo, self.aviso = titulo, menu_ativo, aviso
        self.campos, self.botoes = list(campos), list(botoes)
        self.linhas_tabela, self.cabecalho_tabela, self.busca = linhas_tabela, cabecalho_tabela, busca
        self._linhas_campos = self._agrupar()

    def _agrupar(self):
        linhas, atual = [], []
        for c in self.campos:
            if c.get('cheio'):
                if atual:
                    linhas.append(atual)
                    atual = []
                linhas.append([c])
            else:
                atual.append(c)
                if len(atual) == 2:
                    linhas.append(atual)
                    atual = []
        if atual:
            linhas.append(atual)
        return linhas

    def _altura(self):
        h = 24 + 34
        if self.busca:
            h += 30
        if self.aviso:
            h += 30
        if self.linhas_tabela is not None:
            h += 26 + 18 * len(self.linhas_tabela)
        h += 34 * len(self._linhas_campos)
        if self.botoes:
            h += 38
        return max(h + 12, 150)

    def wrap(self, aw, ah):
        self.h = self._altura()
        return self.LARG, self.h

    def _bolinha(self, x, y, n):
        c = self.canv
        c.setFillColor(LARANJA)
        c.setStrokeColor(colors.white)
        c.circle(x, y, 7, fill=1, stroke=1)
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 8.5)
        c.drawCentredString(x, y - 3, str(n))

    def draw(self):
        c, w, h = self.canv, self.LARG, self.h
        c.setStrokeColor(colors.HexColor('#999999'))
        c.setFillColor(colors.white)
        c.setLineWidth(1)
        c.roundRect(0, 0, w, h, 4, fill=1, stroke=1)
        c.setFillColor(LARANJA)
        c.rect(0, h - 24, w, 24, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 10)
        c.drawString(10, h - 16, 'Orion SISBOV')
        c.setFont('Helvetica', 7.5)
        c.drawRightString(w - 10, h - 15, 'Administrador Consiste   CONSISTE   Sair')
        mw = 92
        c.setFillColor(colors.HexColor('#FAFAFA'))
        c.rect(0, 0, mw, h - 24, fill=1, stroke=0)
        c.setStrokeColor(colors.HexColor('#E0E0E0'))
        c.line(mw, 0, mw, h - 24)
        itens = [('Home', 'home'), ('CADASTROS', None), ('Propriedades', 'propriedades'), ('Proprietários', 'proprietarios'), ('Produtores', 'produtores')]
        y = h - 24 - 18
        for nome, chave in itens:
            if chave is None:
                c.setFillColor(colors.HexColor('#999999'))
                c.setFont('Helvetica', 6.5)
                c.drawString(8, y + 2, nome)
            else:
                if chave == self.menu_ativo:
                    c.setFillColor(LARANJA_CLARO)
                    c.rect(0, y - 5, mw, 16, fill=1, stroke=0)
                    c.setFillColor(LARANJA)
                    c.setFont('Helvetica-Bold', 8)
                else:
                    c.setFillColor(colors.HexColor('#444444'))
                    c.setFont('Helvetica', 8)
                c.drawString(10, y, nome)
            y -= 18
        x0, larg = mw + 14, w - mw - 28
        y = h - 24 - 22
        c.setFillColor(colors.HexColor('#222222'))
        c.setFont('Helvetica-Bold', 11)
        c.drawString(x0, y, self.titulo)
        y -= 10
        if self.busca:
            c.setStrokeColor(BORDA)
            c.setFillColor(colors.white)
            c.roundRect(x0, y - 22, larg * 0.55, 18, 3, fill=1, stroke=1)
            c.setFillColor(colors.HexColor('#999999'))
            c.setFont('Helvetica', 7.5)
            c.drawString(x0 + 6, y - 16, self.busca['texto'])
            if self.busca.get('num'):
                self._bolinha(x0 + larg * 0.55 - 2, y - 4, self.busca['num'])
            bx = x0 + larg * 0.55 + 10
            c.setStrokeColor(LARANJA)
            c.setFillColor(LARANJA)
            c.roundRect(bx, y - 22, 40, 18, 3, fill=0, stroke=1)
            c.drawCentredString(bx + 20, y - 16, 'Buscar')
            y -= 30
        if self.aviso:
            fundo, borda = {'verde': (VERDE_CLARO, VERDE), 'amarelo': (AMARELO_CLARO, AMARELO), 'azul': (AZUL_CLARO, AZUL), 'vermelho': (VERMELHO_CLARO, VERMELHO)}[self.aviso.get('cor', 'azul')]
            c.setFillColor(fundo)
            c.setStrokeColor(borda)
            c.roundRect(x0, y - 22, larg, 22, 3, fill=1, stroke=1)
            c.setFillColor(borda)
            c.setFont('Helvetica-Bold', 7.5)
            c.drawString(x0 + 8, y - 14, self.aviso['texto'][:105])
            if self.aviso.get('num'):
                self._bolinha(x0 + larg - 6, y - 2, self.aviso['num'])
            y -= 30
        if self.linhas_tabela is not None:
            larg_util_tab = larg - 24   # sobra a direita para a bolinha
            ideais = []
            for i, h in enumerate(self.cabecalho_tabela):
                w = stringWidth(h.upper(), 'Helvetica-Bold', 7)
                for l in self.linhas_tabela:
                    w = max(w, stringWidth(l['celulas'][i], 'Helvetica-Bold', 7.5))
                ideais.append(w + 10)
            fator = min(1.0, larg_util_tab / sum(ideais))
            larguras_col = [w * fator for w in ideais]
            if fator >= 1.0:   # sobrou espaco: reparte igualmente
                extra = (larg_util_tab - sum(ideais)) / len(ideais)
                larguras_col = [w + extra for w in ideais]
            xs = [x0 + sum(larguras_col[:i]) for i in range(len(larguras_col))]
            c.setFillColor(colors.HexColor('#F5F5F5'))
            c.rect(x0, y - 16, larg, 16, fill=1, stroke=0)
            c.setFillColor(colors.HexColor('#666666'))
            c.setFont('Helvetica-Bold', 6.5)
            for i, t in enumerate(self.cabecalho_tabela):
                c.drawString(xs[i] + 4, y - 11, _cortar(t.upper(), 'Helvetica-Bold', 7, larguras_col[i] - 6))
            y -= 16
            for linha in self.linhas_tabela:
                c.setStrokeColor(colors.HexColor('#EEEEEE'))
                c.line(x0, y - 18, x0 + larg, y - 18)
                for i, t in enumerate(linha['celulas']):
                    destaque = t in ('Editar', 'Imprimir')
                    c.setFont('Helvetica-Bold' if destaque else 'Helvetica', 7.5)
                    c.setFillColor(LARANJA if destaque else colors.HexColor('#333333'))
                    c.drawString(xs[i] + 4, y - 12, _cortar(t, 'Helvetica-Bold' if destaque else 'Helvetica', 7.5, larguras_col[i] - 6))
                if linha.get('num'):
                    self._bolinha(x0 + larg - 6, y - 9, linha['num'])
                y -= 18
            y -= 10
        for linha in self._linhas_campos:
            cheio = len(linha) == 1 and linha[0].get('cheio')
            cw = larg if cheio else (larg - 12) / 2
            for i, f in enumerate(linha):
                fx = x0 + i * (cw + 12)
                c.setFillColor(colors.HexColor('#555555'))
                c.setFont('Helvetica-Bold', 7)
                c.drawString(fx, y - 4, f['label'] + (' *' if f.get('obrig') else ''))
                c.setStrokeColor(LARANJA if f.get('destaque') else BORDA)
                c.setLineWidth(1.4 if f.get('destaque') else 0.8)
                c.setFillColor(colors.HexColor('#F0F0F0') if f.get('travado') else colors.white)
                c.roundRect(fx, y - 24, cw, 16, 3, fill=1, stroke=1)
                c.setLineWidth(1)
                c.setFillColor(colors.HexColor('#333333'))
                c.setFont('Helvetica', 7.5)
                c.drawString(fx + 5, y - 19, _cortar(f.get('valor', ''), 'Helvetica', 7.5, cw - 22))
                if f.get('num'):
                    self._bolinha(fx + cw - 2, y - 8, f['num'])
            y -= 34
        if self.botoes:
            bx = x0
            for b in self.botoes:
                bw = max(60, 6.2 * len(b['texto']) + 18)
                cinza = b.get('cor') == 'cinza'
                cor = {'laranja': LARANJA, 'verde': VERDE, 'azul': AZUL, 'cinza': colors.HexColor('#888888')}[b.get('cor', 'laranja')]
                c.setFillColor(colors.white if cinza else cor)
                c.setStrokeColor(cor)
                c.roundRect(bx, y - 20, bw, 20, 4, fill=1, stroke=1)
                c.setFillColor(cor if cinza else colors.white)
                c.setFont('Helvetica-Bold', 8)
                c.drawCentredString(bx + bw / 2, y - 13.5, b['texto'])
                if b.get('num'):
                    self._bolinha(bx + bw - 2, y - 2, b['num'])
                bx += bw + 10


TITULO_RODAPE = 'Manual do Cadastro: Propriedade, Proprietário, Produtor e Ambiente'
PAGINAS = {}
PAGINAS_ANT = {}


class Doc(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Capitulo):
            PAGINAS[flowable.chave] = self.page


def _rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#888888'))
    canvas.drawString(MARGEM, 12 * mm, 'Orion SISBOV  |  ' + TITULO_RODAPE)
    canvas.drawRightString(LARGURA - MARGEM, 12 * mm, f'Página {doc.page}')
    canvas.setStrokeColor(LARANJA)
    canvas.setLineWidth(1.2)
    canvas.line(MARGEM, 16 * mm, LARGURA - MARGEM, 16 * mm)
    canvas.restoreState()


def _capa(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(LARANJA)
    canvas.rect(0, 0, LARGURA, ALTURA, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#B82F08'))
    canvas.rect(0, 0, LARGURA, 60 * mm, fill=1, stroke=0)
    canvas.restoreState()


# =========================================================
# CONTEUDO - capa, sumario, capitulos 1 e 2
# =========================================================
def parte_inicio():
    s = []
    s += [Spacer(1, 55 * mm), P('MANUAL DO CADASTRO', capa_titulo), Spacer(1, 6),
          P('Propriedade, Proprietário, Produtor<br/>e Ativação do Ambiente', capa_sub), Spacer(1, 18 * mm),
          P('Passo a passo para quem nunca usou o sistema', capa_sub), Spacer(1, 40 * mm),
          P('Orion SISBOV &#8212; Plataforma Consiste<br/>Rastreabilidade bovina', capa_sub), Spacer(1, 8),
          P('Versão 1.0.0 &#8212; 17/11/2026', capa_sub), PageBreak()]

    def pg(k):
        return str(PAGINAS_ANT.get(k, '?'))
    s += [P('Sumário', h1)]
    linhas = [('1', 'Antes de começar: o que é cada coisa e o que reunir', 'antes'),
              ('2', 'Como entrar no sistema e achar o Cadastro', 'entrar'),
              ('3', 'Propriedades: cadastrar a fazenda', 'propriedades'),
              ('4', 'Proprietários: cadastrar o dono da terra', 'proprietarios'),
              ('5', 'Produtores: cadastrar quem cria o gado', 'produtores'),
              ('6', 'Ativar o Ambiente do Produtor', 'ambiente'),
              ('7', 'Criar o Acesso (login e senha) do Produtor', 'acesso'),
              ('8', 'Conferência final, problemas comuns e glossário', 'final')]
    dados = [[P(f'<b>{n}</b>'), P(t), P(f'<b>{pg(k)}</b>')] for n, t, k in linhas]
    t = Table(dados, colWidths=[12 * mm, LARGURA_UTIL - 32 * mm, 20 * mm])
    t.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDA), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                           ('ALIGN', (2, 0), (2, -1), 'RIGHT'), ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    s += [t, Spacer(1, 14)]
    s.append(caixa('dica', 'Como usar este manual',
                   'Siga os capítulos <b>na ordem</b>: 3, 4, 5, 6 e 7. Cada capítulo explica uma etapa do cadastro de um cliente novo. '
                   'Os desenhos mostram as telas de forma simplificada; as <b>bolinhas laranja numeradas</b> apontam o que você deve fazer, '
                   'e a legenda logo abaixo do desenho explica cada número. Os nomes e números usados nos exemplos são <b>inventados</b>.'))
    s.append(caixa('atencao', 'Quem usa este manual',
                   'Este manual é para o usuário da <b>Consiste</b> (perfil CONSISTE), que cadastra os clientes novos. '
                   'Você não precisa saber programação nem ter usado o sistema antes.'))
    s.append(PageBreak())

    # ---------------- 1 ANTES DE COMECAR ----------------
    s += [Capitulo('antes', '1. Antes de começar'),
          P('Para cadastrar um cliente novo você vai criar <b>cinco coisas</b>, sempre nesta ordem. Entender o que cada uma é evita a maioria dos erros.'),
          tabela(['Etapa', 'O que é', 'Em palavras simples'], [
              ['1. Propriedade', 'O estabelecimento rural', 'A <b>fazenda</b> onde os animais ficam. Tudo no Orion começa por ela.'],
              ['2. Proprietário', 'O dono da terra', 'A pessoa (ou empresa) dona da fazenda. É cadastrado <b>dentro</b> da Propriedade.'],
              ['3. Produtor', 'Quem cria o gado', 'A pessoa (ou empresa) que movimenta os animais e usa o sistema no dia a dia. Pode ser a mesma pessoa do Proprietário.'],
              ['4. Ambiente', 'O espaço próprio do Produtor', 'Um espaço separado só dele, onde ficam os animais, as GTAs e os documentos. Precisa ser <b>ativado uma única vez</b>.'],
              ['5. Acesso', 'Login e senha', 'O que o Produtor usa para entrar no sistema. A Consiste cria e o sistema envia por e-mail.'],
          ], [28 * mm, 40 * mm, LARGURA_UTIL - 68 * mm]),
          Spacer(1, 10),
          P('<b>Vínculo</b> é a ligação entre a Propriedade e uma pessoa. Quando você cadastra um Proprietário ou um Produtor dentro de uma Propriedade, o sistema cria o vínculo '
            'automaticamente. O vínculo fica <b>Ativo</b> ou <b>Inativo</b> (explicado nos capítulos 4 e 5).'),
          P('Ordem do cadastro', h2),
          passo(1, 'Cadastrar a Propriedade', 'Capítulo 3. Sem a Propriedade salva, o sistema não libera as seções de Proprietário e Produtor.'),
          passo(2, 'Cadastrar o Proprietário dentro da Propriedade', 'Capítulo 4.'),
          passo(3, 'Cadastrar o Produtor dentro da Propriedade', 'Capítulo 5.'),
          passo(4, 'Ativar o Ambiente do Produtor', 'Capítulo 6. Sem isso o Produtor não consegue lançar animais.'),
          passo(5, 'Criar o Acesso do Produtor', 'Capítulo 7. É o último passo: o Produtor recebe o login e a senha.'),
          P('O que reunir antes de sentar para cadastrar', h2),
          P('Peça ao cliente (ou separe dos documentos dele) as informações abaixo. Com tudo em mãos o cadastro leva poucos minutos:')]
    s += lista([
        '<b>Da fazenda:</b> nome da fazenda; tipo (Mista, Corte ou Leite); área em hectares; município e estado (UF); código do estabelecimento no órgão estadual (OESA); '
        'roteiro de como chegar; e-mail e telefone. Se tiver: Inscrição Estadual, NIRF/INCRA, CAR, código SISBOV (ERAS), CEP, coordenadas.',
        '<b>Do Proprietário:</b> CPF ou CNPJ; nome completo (ou razão social); município e UF; e-mail e telefone.',
        '<b>Do Produtor:</b> CPF ou CNPJ; nome completo (ou razão social); município e UF; <b>e-mail válido</b> (é para ele que o login e a senha serão enviados); telefone; '
        'e, se quiser, a logomarca do criador em PNG ou JPG.',
    ])
    s += [Spacer(1, 6), caixa('importante', 'Confira o CPF/CNPJ com cuidado',
                              'O sistema confere o <b>dígito verificador</b> do CPF e do CNPJ. Se um número for digitado errado, o cadastro <b>não é salvo</b>. '
                              'O CPF/CNPJ do Produtor também vira o <b>login</b> dele; por isso, digite-o com atenção.'),
          P('Como o sistema se comporta (vale para todas as telas)', h2)]
    s += lista([
        '<b>Campos com asterisco (*)</b> são obrigatórios. Sem eles o sistema não salva e avisa qual está faltando.',
        '<b>Letras maiúsculas:</b> o sistema converte automaticamente o que você digita (menos o e-mail).',
        '<b>CPF/CNPJ:</b> digite só os números; o sistema coloca os pontos e traços sozinho.',
        '<b>Busca automática:</b> ao digitar o CPF/CNPJ de um Proprietário ou Produtor e sair do campo, o sistema procura se a pessoa já existe e, se existir, preenche os dados.',
        '<b>Aviso de alterações não salvas:</b> se você tentar sair de uma tela depois de digitar algo, o sistema pergunta se quer continuar editando ou sair sem salvar.',
        '<b>Tamanho dos campos:</b> cada campo aceita um número máximo de letras. Se passar, o sistema avisa quanto foi digitado.',
        '<b>Menu lateral:</b> o botão com três tracinhos (canto superior esquerdo) abre e fecha o menu.',
    ])
    s.append(PageBreak())

    # ---------------- 2 ENTRAR ----------------
    s += [Capitulo('entrar', '2. Como entrar no sistema e achar o Cadastro'),
          passo(1, 'Abra o sistema', 'No navegador (Chrome, por exemplo), digite o endereço do Orion que a Consiste informou e pressione Enter.'),
          passo(2, 'Entre com o seu login e senha de usuário Consiste', 'Você será levado ao <b>Painel Consiste</b> (a tela inicial). No canto superior direito aparecem o seu nome e a etiqueta <b>CONSISTE</b>.'),
          passo(3, 'Procure o grupo CADASTROS no menu da esquerda', 'Nele estão os três itens que você vai usar: <b>Propriedades</b>, <b>Proprietários</b> e <b>Produtores</b>.')]
    s.append(TelaMock('Painel Consiste', menu_ativo='home', campos=[
        {'label': 'Menu lateral: grupo CADASTROS', 'valor': 'Propriedades / Proprietários / Produtores', 'cheio': True, 'num': 1, 'destaque': True},
        {'label': 'Acesso Rápido', 'valor': '[ Nova Propriedade ]', 'cheio': True, 'num': 2},
    ]))
    s += legendas([(1, 'No menu lateral, o grupo <b>CADASTROS</b> tem os três itens de cadastro.'),
                   (2, 'No Painel, o botão <b>Nova Propriedade</b> (em "Acesso Rápido") leva direto ao cadastro de uma Propriedade nova.')])
    s += [caixa('dica', 'O que cada item do menu faz',
                '<b>Propriedades:</b> lista as fazendas e é onde se cadastra uma nova. <b>Proprietários</b> e <b>Produtores:</b> listam as pessoas já cadastradas, '
                'para consultar e corrigir dados. <b>Atenção:</b> Proprietário e Produtor <b>novos</b> são criados sempre de dentro de uma Propriedade (capítulos 4 e 5).'),
          caixa('ok', 'Manual sempre à mão',
                'Nas telas Propriedades, Proprietários e Produtores existe o botão <b>Manual (PDF)</b>, que abre este manual já no capítulo daquela tela. '
                'No Painel Consiste ele também está em "Acesso Rápido".'),
          PageBreak()]
    return s


# =========================================================
# CONTEUDO - capitulo 3 (Propriedades)
# =========================================================
def parte_propriedades():
    s = [Capitulo('propriedades', '3. Propriedades: cadastrar a fazenda'),
         P('Esta é a <b>primeira etapa</b>. Você cadastra a fazenda e, em seguida, abre-a para ligar o Proprietário e o Produtor.'),
         P('3.1 A lista de Propriedades', h2),
         passo(1, 'Clique em Propriedades', 'No menu lateral, dentro de CADASTROS. Abre a lista de todas as fazendas cadastradas.')]
    s.append(TelaMock('Propriedades', menu_ativo='propriedades', busca={'texto': 'Buscar por nome...', 'num': 1},
                      cabecalho_tabela=['Nome', 'Município / UF', 'Tipo', 'Área (ha)', 'Status', 'Ações'],
                      linhas_tabela=[{'celulas': ['FAZENDA BOA ESPERANÇA', 'UBERABA / MG', 'MISTA', '150,5', 'Ativo', 'Editar'], 'num': 2},
                                     {'celulas': ['SITIO SANTA CLARA', 'ARAGUARI / MG', 'CORTE', '48,0', 'Ativo', 'Editar']}],
                      botoes=[{'texto': '+ Nova Propriedade', 'num': 3}]))
    s += legendas([(1, '<b>Busca:</b> digite parte do nome e clique em Buscar. Faça sempre a busca <b>antes de cadastrar</b>, para não duplicar uma fazenda que já existe.'),
                   (2, '<b>Editar:</b> abre a Propriedade para corrigir dados e para ligar Proprietário, Produtor e Protocolos. Ao lado de Editar há também <b>Inativar/Ativar</b>.'),
                   (3, '<b>+ Nova Propriedade:</b> abre o formulário em branco (fica no canto superior direito da lista).')])
    s += [caixa('atencao', 'Inativar não apaga',
                'Inativar uma Propriedade só muda o status dela para Inativo. Nada é apagado, e é possível Ativar de novo. '
                'Use apenas quando a Consiste decidir encerrar o atendimento daquela fazenda.'),
          P('3.2 Preencher o formulário', h2),
          passo(1, 'Clique em + Nova Propriedade', 'O formulário abre em branco, com os blocos <b>Dados da Propriedade</b>, <b>Endereço</b>, <b>Contato</b> e <b>Localização Geográfica</b>.'),
          passo(2, 'Preencha os campos', 'Use a tabela mais abaixo. Os campos com asterisco (*) são obrigatórios.')]
    s.append(TelaMock('Nova Propriedade', menu_ativo='propriedades', campos=[
        {'label': 'Nome', 'valor': 'FAZENDA BOA ESPERANÇA', 'obrig': True, 'cheio': True, 'num': 1},
        {'label': 'Tipo', 'valor': 'MISTA', 'obrig': True, 'num': 2},
        {'label': 'Área (hectares)', 'valor': '150,5', 'obrig': True, 'num': 3},
        {'label': 'Código do Estabelecimento (OESA)', 'valor': '31012345', 'obrig': True, 'num': 4},
        {'label': 'Município', 'valor': 'UBERABA', 'obrig': True, 'num': 5},
    ], botoes=[{'texto': 'Cadastrar', 'num': 6}, {'texto': 'Cancelar', 'cor': 'cinza'}]))
    s += legendas([(1, 'Nome da fazenda como o cliente a conhece.'), (2, 'Escolha na lista: Mista, Corte ou Leite.'),
                   (3, 'Tamanho da propriedade em hectares. Pode usar vírgula (ex.: 150,5).'),
                   (4, 'Código da fazenda no órgão estadual (o mesmo da GTA). Até 11 caracteres.'),
                   (5, 'Município e UF (a UF é escolhida numa lista).'), (6, 'Ao terminar, clique em <b>Cadastrar</b>.')])
    s += [P('Campo por campo', h3),
          tabela(['Campo', 'Obrig.', 'O que escrever'], [
              ['Nome', 'Sim', 'Nome da fazenda (até 150 letras). Ex.: FAZENDA BOA ESPERANÇA.'],
              ['Tipo', 'Sim', 'Escolha <b>Mista</b>, <b>Corte</b> ou <b>Leite</b>, conforme a atividade principal.'],
              ['Inscrição Estadual', 'Não', 'Número da inscrição estadual do produtor rural, se houver (até 30 caracteres).'],
              ['NIRF / INCRA', 'Não', 'Número do imóvel rural na Receita Federal / INCRA, se houver (até 30 caracteres).'],
              ['CAR', 'Não', 'Número do Cadastro Ambiental Rural, se houver (até 50 caracteres).'],
              ['Código SISBOV (ERAS)', 'Não', 'Código do estabelecimento no SISBOV, <b>se o cliente já tiver</b>. Produtor que não é SISBOV deixa em branco. '
                                              '<b>Não pode repetir:</b> se o código já existir em outra Propriedade, o sistema avisa qual.'],
              ['Código do Estabelecimento (OESA)', 'Sim', 'Código da fazenda no órgão estadual de defesa agropecuária (aparece na GTA). Até 11 caracteres.'],
              ['Área (hectares)', 'Sim', 'Número maior que zero. Pode usar vírgula. Ex.: 150,5.'],
              ['Logradouro, Número, Bairro, CEP', 'Não', 'Endereço da sede (rodovia, estrada, número). CEP no formato 00000-000.'],
              ['UF', 'Sim', 'Estado, escolhido na lista.'],
              ['Município', 'Sim', 'Cidade onde fica a fazenda.'],
              ['Roteiro de Acesso', 'Sim', 'Texto explicando como chegar à fazenda a partir do centro da cidade ou de uma referência próxima.'],
              ['Distância da Sede à Cidade Próxima', 'Não', 'Ex.: 15KM ASFALTO + 3KM TERRA.'],
              ['E-mail', 'Sim', 'E-mail de contato da fazenda (até 150 caracteres).'],
              ['Telefone', 'Sim', 'Com DDD: (00) 00000-0000.'],
              ['Telefone 2', 'Não', 'Telefone alternativo.'],
              ['Latitude / Longitude', 'Não', 'Coordenadas. Aceita decimal (ex.: -19.3232123), graus-minutos-segundos ou o par copiado do Google Maps. '
                                              'A latitude vai de -90 a 90 e a longitude de -180 a 180.'],
          ], [44 * mm, 14 * mm, LARGURA_UTIL - 58 * mm]),
          Spacer(1, 8),
          passo(3, 'Clique em Cadastrar', 'Se estiver tudo certo, o sistema volta para a <b>lista de Propriedades</b> e a fazenda nova já aparece nela. '
                'Se algo estiver errado, a tela mostra uma <b>mensagem em vermelho</b> no topo e <b>mantém tudo o que você digitou</b>: corrija e clique de novo.'),
          caixa('importante', 'A fazenda ainda não está pronta',
                'Depois de cadastrar, as seções de Proprietário, Produtor e Protocolos <b>ainda estão bloqueadas</b>. O sistema mostra o aviso '
                '"Salve a Propriedade primeiro". Para liberá-las, faça o passo 4.'),
          passo(4, 'Abra a Propriedade de novo', 'Na lista, procure a fazenda (use a Busca) e clique em <b>Editar</b>. Agora aparecem as seções '
                '<b>Proprietário(s)</b>, <b>Produtor(es)</b> e <b>Protocolos de Certificação</b>. Você está pronto para o capítulo 4.'),
          P('3.3 Protocolos de Certificação (opcional)', h2),
          P('No fim da tela de edição existe a seção <b>Protocolos de Certificação</b>. Ela só funciona depois de a Propriedade estar salva. '
            'Marque os protocolos em que a fazenda está inscrita. Para <b>desativar</b> um protocolo, o sistema pede o <b>motivo</b> '
            '(<i>Voluntária</i>: o produtor optou por sair; ou <i>Compulsória</i>: irregularidade constatada por entidade externa) e uma observação. '
            'Se você não tem certeza de quais protocolos marcar, deixe como está e consulte a coordenação da Consiste.'),
          P('3.4 Mensagens de erro mais comuns', h2),
          tabela(['O que o sistema diz', 'O que fazer'], [
              ['Preencha o campo "..." e salve de novo.', 'Falta um campo obrigatório (Nome, Tipo, UF, Município, Roteiro de acesso, E-mail ou Telefone). Preencha o que foi citado.'],
              ['Área (hectares) incorreta!', 'Digite um número maior que zero, como 150,5. Não use letras.'],
              ['Campo "..." excede o limite de N caracteres.', 'O texto está grande demais. Encurte (o OESA, por exemplo, aceita só 11 caracteres).'],
              ['O Código ERAS ... já está cadastrado na Propriedade ...', 'Confira o número digitado. Se estiver certo, é uma fazenda repetida: avise a coordenação da Consiste antes de continuar.'],
              ['Latitude/Longitude incorreta!', 'Use só números e ponto decimal, ou o formato de graus. Latitude de -90 a 90; longitude de -180 a 180.'],
              ['Escolha a UF na lista.', 'Selecione o estado na lista (não digite).'],
          ], [62 * mm, LARGURA_UTIL - 62 * mm]),
          PageBreak()]
    return s


# =========================================================
# CONTEUDO - capitulos 4 e 5 (Proprietarios e Produtores)
# =========================================================
def parte_pessoas():
    s = [Capitulo('proprietarios', '4. Proprietários: cadastrar o dono da terra'),
         P('O Proprietário é cadastrado <b>de dentro da Propriedade</b>. Por isso a Propriedade precisa estar salva (capítulo 3).'),
         P('4.1 Chegar na tela certa', h2),
         passo(1, 'Abra a Propriedade', 'Menu <b>Propriedades</b>, procure a fazenda e clique em <b>Editar</b>.'),
         passo(2, 'Localize a seção Proprietário(s)', 'Se ainda não há ninguém, aparece "Nenhum Proprietário vinculado no momento".'),
         passo(3, 'Clique em + Adicionar Proprietário', 'Abre o formulário do Proprietário. No alto aparece o nome da fazenda: '
               '"Vinculando este Proprietário à Propriedade: ...". Isso confirma que você está no lugar certo.')]
    s.append(TelaMock('Propriedade: FAZENDA BOA ESPERANÇA', menu_ativo='propriedades', campos=[
        {'label': 'Proprietário(s)', 'valor': 'Nenhum Proprietário vinculado no momento.', 'cheio': True},
    ], botoes=[{'texto': '+ Adicionar Proprietário', 'num': 1}]))
    s += legendas([(1, 'Clique aqui para abrir o formulário do Proprietário.')])
    s += [P('4.2 Primeiro o CPF/CNPJ: a busca automática', h2),
          P('O formulário começa pelo <b>Tipo de Pessoa</b>. O campo CPF/CNPJ só é liberado depois que você escolhe esse tipo. '
            'Quando você digita o número e sai do campo, o sistema <b>procura sozinho</b> se essa pessoa já foi cadastrada antes. Há dois resultados possíveis:')]
    s.append(TelaMock('Novo Proprietário', menu_ativo='proprietarios',
                      aviso={'texto': 'CPF/CNPJ já cadastrado: dados carregados abaixo. Os campos foram travados.', 'cor': 'verde', 'num': 3}, campos=[
        {'label': 'Tipo de Pessoa', 'valor': 'Física', 'obrig': True, 'num': 1},
        {'label': 'CPF/CNPJ', 'valor': '123.456.789-09', 'obrig': True, 'num': 2, 'destaque': True},
        {'label': 'Razão Social', 'valor': 'JOÃO DA SILVA', 'obrig': True, 'cheio': True, 'travado': True},
    ], botoes=[{'texto': 'Vincular', 'num': 4}, {'texto': 'Cancelar', 'cor': 'cinza'}]))
    s += legendas([(1, 'Escolha primeiro o <b>Tipo de Pessoa</b>: Física (CPF) ou Jurídica (CNPJ).'),
                   (2, 'Digite o CPF ou CNPJ e <b>saia do campo</b> (clique em outro lugar ou aperte Tab).'),
                   (3, '<b>Se a pessoa já existe:</b> aparece este aviso verde, os dados vêm preenchidos e os campos ficam <b>travados</b> (cinza), para ninguém alterar o cadastro existente sem querer.'),
                   (4, 'Nesse caso o botão vira <b>Vincular</b>: ele só liga a pessoa já cadastrada a esta fazenda. Clique nele e pronto.')])
    s += [caixa('dica', 'Se a pessoa NÃO existe',
                'Nenhum aviso aparece, os campos ficam <b>livres</b> e o botão fica <b>Cadastrar</b>. Preencha todos os dados (tabela abaixo) e clique em Cadastrar: '
                'o sistema cria a pessoa <b>e</b> já a vincula à fazenda.'),
          P('4.3 Campos do Proprietário', h2),
          tabela(['Campo', 'Obrig.', 'O que escrever'], [
              ['Tipo de Pessoa', 'Sim', '<b>Física</b> (pessoa, CPF) ou <b>Jurídica</b> (empresa, CNPJ). Escolha primeiro.'],
              ['Visibilidade', 'Sim', 'Escolha <b>Público</b> ou <b>Privado</b>. É um controle de exibição dos dados da pessoa. Siga a orientação combinada com o cliente.'],
              ['CPF/CNPJ', 'Sim', 'Só números. O sistema confere o dígito verificador: se estiver errado, avisa "CPF incorreto! O dígito verificador não confere".'],
              ['Razão Social', 'Sim', 'Nome completo da pessoa ou razão social da empresa.'],
              ['Nome Fantasia', 'Não', 'O sistema copia a Razão Social sozinho. Só altere se o nome usado no dia a dia for diferente.'],
              ['Logradouro, Número, Complemento, Bairro, CEP', 'Não', 'Endereço da pessoa.'],
              ['UF', 'Sim', 'Estado, escolhido na lista.'],
              ['Município', 'Sim', 'Cidade da pessoa.'],
              ['E-mail', 'Sim', 'E-mail de contato.'],
              ['Telefone', 'Sim', 'Com DDD. Ex.: (34) 99999-0000.'],
              ['Telefone 2', 'Não', 'Telefone alternativo.'],
          ], [44 * mm, 14 * mm, LARGURA_UTIL - 58 * mm]),
          Spacer(1, 8),
          passo(4, 'Clique em Cadastrar (ou Vincular)', 'O sistema volta para a tela da Propriedade, e o Proprietário aparece na seção <b>Proprietário(s)</b>, '
                'com o texto "Vinculado desde (data)" e o status <b>Ativo</b>.'),
          P('4.4 Corrigir os dados ou encerrar o vínculo', h2)]
    s += lista([
        '<b>Corrigir:</b> na seção Proprietário(s) da Propriedade, clique em <b>Editar</b> ao lado do nome. Altere e clique em <b>Salvar Alterações</b>.',
        '<b>Vínculo Ativo/Inativo:</b> dentro da tela de edição há o quadro "Vínculo com esta Propriedade". O botão <b>Inativar</b> encerra o vínculo '
        '(passa a aparecer "Encerrado em (data)"); o botão <b>Ativar</b> religa. Isso <b>não apaga</b> a pessoa.',
        '<b>Menu Proprietários:</b> mostra a lista geral (com busca por nome ou razão social e a coluna Status). Serve para consultar e corrigir. '
        'Lembre: um Proprietário <b>novo</b> é sempre criado de dentro da Propriedade.',
    ])
    s.append(PageBreak())

    # ---------------- 5 PRODUTORES ----------------
    s += [Capitulo('produtores', '5. Produtores: cadastrar quem cria o gado'),
          P('O Produtor é a pessoa (ou empresa) que vai <b>usar o sistema</b>. O cadastro é parecido com o do Proprietário, com alguns itens a mais: '
            'documento secundário, logomarca e o quadro do <b>Ambiente</b>.'),
          P('5.1 Chegar na tela certa', h2),
          passo(1, 'Abra a Propriedade', 'Menu <b>Propriedades</b>, procure a fazenda e clique em <b>Editar</b>.'),
          passo(2, 'Na seção Produtor(es), clique em + Adicionar Produtor', 'Abre o formulário, com o aviso "Vinculando este Produtor à Propriedade: (nome da fazenda)".'),
          P('5.2 CPF/CNPJ e a busca automática (três resultados)', h2),
          P('Igual ao Proprietário: escolha o <b>Tipo de Pessoa</b>, digite o <b>CPF/CNPJ</b> e saia do campo. O sistema procura e pode responder de <b>três</b> formas:')]
    s.append(TelaMock('Novo Produtor', menu_ativo='produtores',
                      aviso={'texto': 'Esta pessoa já é Proprietário cadastrado: dados pré-preenchidos. Revise antes de salvar.', 'cor': 'azul', 'num': 2}, campos=[
        {'label': 'Tipo de Pessoa', 'valor': 'Física', 'obrig': True},
        {'label': 'CPF/CNPJ', 'valor': '123.456.789-09', 'obrig': True, 'num': 1, 'destaque': True},
        {'label': 'CNPJ (opcional)', 'valor': '', 'num': 3},
        {'label': 'Marca/Criador (logo)', 'valor': 'Escolher arquivo PNG ou JPG', 'num': 4},
    ], botoes=[{'texto': 'Cadastrar', 'num': 5}, {'texto': 'Cancelar', 'cor': 'cinza'}]))
    s += legendas([(1, 'Digite o CPF/CNPJ e saia do campo.'),
                   (2, '<b>Resultado A: a pessoa já é Proprietário.</b> Aviso azul: os dados vêm pré-preenchidos do cadastro de Proprietário. Revise, complete o que faltar e clique em Cadastrar.'),
                   (3, '<b>Documento secundário (opcional):</b> numa pessoa Física, aceita um CNPJ; numa Jurídica, aceita um CPF. Deixe em branco se não houver.'),
                   (4, '<b>Marca/Criador (logo):</b> imagem PNG ou JPG, até 10 MB. Use o botão Atualizar para ver a prévia antes de salvar. Deixe em branco se não houver.'),
                   (5, 'Clique em <b>Cadastrar</b>.')])
    s += [caixa('ok', 'Resultado B: a pessoa já é Produtor em outra fazenda',
                'Aviso verde "CPF/CNPJ já cadastrado como Produtor". Os campos ficam travados e o botão vira <b>Vincular</b>. Clique nele: o Produtor passa a atender também esta fazenda. '
                '(Um mesmo Produtor pode ter várias Propriedades.)'),
          caixa('dica', 'Resultado C: a pessoa não existe',
                'Nenhum aviso. Os campos ficam livres e o botão é <b>Cadastrar</b>. Preencha tudo e clique. Se o Produtor for a <b>mesma pessoa do Proprietário</b>, '
                'você cai no Resultado A e economiza digitação.'),
          caixa('importante', 'Trocou o CPF/CNPJ depois da busca?',
                'Se você digitar outro CPF/CNPJ depois de um cadastro ter sido encontrado, o sistema <b>limpa</b> os campos que foram preenchidos pela busca '
                '(nome, e-mail, telefones, endereço, CEP, município), para você não gravar os dados de uma pessoa em outro número.'),
          P('5.3 Campos do Produtor', h2),
          tabela(['Campo', 'Obrig.', 'O que escrever'], [
              ['Tipo de Pessoa', 'Sim', 'Física ou Jurídica.'],
              ['Visibilidade', 'Sim', 'Público ou Privado (controle de exibição). Siga a orientação combinada com o cliente.'],
              ['CPF/CNPJ', 'Sim', 'Só números; dígito verificador conferido. <b>Este número será o login do Produtor.</b>'],
              ['CNPJ (opcional) / CPF (opcional)', 'Não', 'Documento secundário: Física pode ter um CNPJ; Jurídica pode ter um CPF.'],
              ['Razão Social', 'Sim', 'Nome completo ou razão social.'],
              ['Nome Fantasia', 'Não', 'O sistema copia a Razão Social; só altere se for diferente.'],
              ['Marca/Criador (logo)', 'Não', 'PNG ou JPG, até 10 MB.'],
              ['Logradouro, Número, Complemento, Bairro, CEP', 'Não', 'Endereço do Produtor.'],
              ['UF', 'Sim', 'Estado, escolhido na lista.'],
              ['Município', 'Sim', 'Cidade do Produtor.'],
              ['E-mail', 'Sim', '<b>Muito importante:</b> é para este e-mail que o login e a senha provisória serão enviados (capítulo 7). Confira com o cliente.'],
              ['Telefone', 'Sim', 'Com DDD. É usado também para o envio opcional por WhatsApp.'],
              ['Telefone 2', 'Não', 'Telefone alternativo.'],
          ], [44 * mm, 14 * mm, LARGURA_UTIL - 58 * mm]),
          Spacer(1, 8),
          passo(3, 'Clique em Cadastrar (ou Vincular)', 'O sistema volta à Propriedade e o Produtor aparece na seção <b>Produtor(es)</b>, com "Vinculado desde (data)" e status <b>Ativo</b>.'),
          P('5.4 Corrigir, imprimir e encerrar o vínculo', h2)]
    s += lista([
        '<b>Corrigir:</b> na Propriedade, seção Produtor(es), clique em <b>Editar</b>. Altere e clique em <b>Salvar Alterações</b>.',
        '<b>Vínculo Ativo/Inativo:</b> quadro "Vínculo com esta Propriedade", botão <b>Inativar</b>/<b>Ativar</b>. <b>Só a Consiste faz isso</b>. Não apaga o Produtor.',
        '<b>Menu Produtores:</b> lista geral (busca por nome ou razão social). Em cada linha: <b>Editar</b>, <b>Imprimir</b> (gera o relatório do Produtor em PDF) e <b>Inativar/Ativar</b>.',
    ])
    s.append(TelaMock('Produtores', menu_ativo='produtores', busca={'texto': 'Buscar por nome ou razão social...'},
                      cabecalho_tabela=['Nome', 'Tipo', 'CPF/CNPJ', 'Município / UF', 'Status', 'Ações'],
                      linhas_tabela=[{'celulas': ['JOÃO DA SILVA', 'Física', '123.456.789-09', 'UBERABA / MG', 'Ativo', 'Editar'], 'num': 1}]))
    s += legendas([(1, 'Clique em <b>Editar</b> para abrir o Produtor. É nesta tela que ficam o quadro do <b>Ambiente</b> (capítulo 6) e o aviso do <b>Acesso</b> (capítulo 7).')])
    s.append(PageBreak())
    return s


# =========================================================
# CONTEUDO - capitulos 6, 7 e 8 + montagem
# =========================================================
def parte_ambiente():
    s = [Capitulo('ambiente', '6. Ativar o Ambiente do Produtor'),
         P('O <b>Ambiente</b> é o espaço privado do Produtor dentro do Orion: é onde ficam os animais, pesagens, GTAs e documentos dele, separados dos dados de todos os outros Produtores. '
           'Enquanto o Ambiente não for ativado, o Produtor está apenas "cadastrado": ele existe na lista, mas <b>não consegue trabalhar</b>.'),
         caixa('importante', 'Atenção: isto é feito UMA vez e não tem volta',
               'Ativar o Ambiente é irreversível. Antes de clicar, confira: nome, CPF/CNPJ e e-mail do Produtor. Só a equipe da <b>Consiste</b> vê este botão.'),
         P('6.1 Passo a passo', h2),
         passo(1, 'Abra o Produtor', 'Menu <b>Produtores</b> &gt; clique em <b>Editar</b> na linha do Produtor (ou, dentro da Propriedade, <b>Editar</b> ao lado do nome do Produtor).'),
         passo(2, 'Localize o quadro do Ambiente', 'Na tela de edição, o quadro do Ambiente mostra o status: <b>Ambiente ainda não ativado</b>.'),
         passo(3, 'Clique em Ativar Ambiente', 'Abre uma janela de confirmação perguntando se você tem certeza.'),
         passo(4, 'Confirme', 'Clique no botão de confirmação. Aguarde alguns segundos, <b>sem fechar a página nem clicar de novo</b>.')]
    s.append(TelaMock('Editar Produtor: JOÃO DA SILVA', menu_ativo='produtores', campos=[
        {'label': 'Ambiente', 'valor': 'Ambiente ainda não ativado', 'cheio': True},
    ], botoes=[{'texto': 'Ativar Ambiente', 'num': 1}, {'texto': 'Salvar Alterações', 'cor': 'cinza'}]))
    s += legendas([(1, 'Este é o botão. Ele só aparece para a Consiste e só enquanto o Ambiente não foi ativado.')])
    s += [P('6.2 O que acontece quando você confirma', h2),
          P('O sistema cria, sozinho, tudo o que o Produtor precisa para trabalhar. Quando termina, mostra uma mensagem de sucesso e o quadro passa a indicar <b>Ambiente ativo</b>.'),
          caixa('ok', 'Se der erro, não há sujeira',
                'A criação é "tudo ou nada". Se algo falhar no meio do caminho, o sistema <b>desfaz tudo</b> e avisa na tela. O Produtor continua como antes e você pode tentar de novo. '
                'Se o erro se repetir, anote a mensagem e chame o suporte.'),
          P('6.3 Como saber se deu certo', h2)]
    s += lista(['O quadro do Ambiente mostra <b>Ambiente ativo</b>.',
                'O botão <b>Ativar Ambiente</b> desapareceu.',
                'Agora aparece a opção de <b>Criar Acesso</b> (capítulo 7).'])
    s.append(PageBreak())
    return s


def parte_acesso():
    s = [Capitulo('acesso', '7. Criar o Acesso (login e senha) do Produtor'),
         P('Com o Ambiente ativo, falta dar ao Produtor a <b>chave de entrada</b>: o login e a senha. Isso se chama <b>Criar Acesso</b>.'),
         tabela(['Item', 'Como funciona'], [
             ['Login', 'É o <b>CPF ou CNPJ</b> do Produtor, só os números (sem pontos, traço ou barra).'],
             ['Senha', 'O sistema gera uma senha <b>provisória</b> e envia por <b>e-mail</b>. O Produtor troca a senha no primeiro acesso.'],
             ['Cargo', 'O primeiro acesso nasce com o cargo <b>TITULAR</b> (dono do ambiente, com todas as permissões).'],
             ['E-mail', '<b>Obrigatório.</b> Sem e-mail cadastrado no Produtor, o acesso não pode ser criado.'],
         ], [30 * mm, LARGURA_UTIL - 30 * mm]),
         Spacer(1, 8),
         P('7.1 Passo a passo', h2),
         passo(1, 'Confira o e-mail do Produtor', 'Na tela de edição do Produtor, veja se o campo <b>E-mail</b> está correto. Se não estiver, corrija e clique em Salvar Alterações.'),
         passo(2, 'Clique em Criar Acesso', 'O botão aparece quando o Ambiente já está ativo e o Produtor ainda não tem acesso.'),
         passo(3, 'Aguarde a mensagem', 'O sistema avisa que o acesso foi criado e para qual e-mail a senha provisória foi enviada.'),
         passo(4, 'Opcional: enviar por WhatsApp', 'Se o cliente preferir, use o link de WhatsApp que aparece na tela: ele abre o aplicativo com a mensagem pronta, com login e senha provisória. Basta apertar enviar.')]
    s.append(TelaMock('Editar Produtor: JOÃO DA SILVA', menu_ativo='produtores',
                      aviso={'texto': 'Ambiente ativo. Este Produtor ainda não tem acesso ao sistema.', 'cor': 'amarelo', 'num': 1}, campos=[
        {'label': 'E-mail', 'valor': 'joao@fazenda.com.br', 'obrig': True, 'num': 2},
    ], botoes=[{'texto': 'Criar Acesso', 'num': 3}]))
    s += legendas([(1, 'Aviso: o ambiente existe, mas ainda não há login.'),
                   (2, 'Confira se o e-mail está certo: é para ele que a senha vai.'),
                   (3, 'Clique para criar o login e enviar a senha provisória.')])
    s += [P('7.2 Se o e-mail não chegar', h2)]
    s += lista(['O acesso <b>já foi criado</b> mesmo assim. O sistema avisa na tela que o e-mail falhou.',
                'Peça ao Produtor para olhar a caixa de <b>spam/lixo eletrônico</b>.',
                'Use o <b>link de WhatsApp</b> para entregar a senha provisória.',
                'Confira se o e-mail do Produtor está escrito corretamente; se estava errado, corrija e peça uma nova senha pela tela de login do Orion ("Esqueci minha senha").'])
    s.append(PageBreak())
    return s


def parte_final():
    s = [Capitulo('final', '8. Conferência final, problemas comuns e glossário'),
         P('8.1 Lista de conferência: está tudo pronto?', h2),
         tabela(['Conferir', 'Onde ver', 'OK?'], [
             ['Propriedade cadastrada, com Nirf e código SISBOV', 'Menu Propriedades', '[  ]'],
             ['Proprietário aparece na Propriedade, vínculo Ativo', 'Propriedades &gt; Editar &gt; Proprietário(s)', '[  ]'],
             ['Produtor aparece na Propriedade, vínculo Ativo', 'Propriedades &gt; Editar &gt; Produtor(es)', '[  ]'],
             ['E-mail e telefone do Produtor corretos', 'Produtores &gt; Editar', '[  ]'],
             ['Ambiente ativo', 'Produtores &gt; Editar (quadro do Ambiente)', '[  ]'],
             ['Acesso criado e senha provisória enviada', 'Mensagem na tela / e-mail do Produtor', '[  ]'],
             ['Produtor consegue entrar com CPF/CNPJ e a senha', 'Teste de login (peça ao cliente)', '[  ]'],
         ], [78 * mm, 76 * mm, 16 * mm]),
         Spacer(1, 8),
         P('8.2 Problemas comuns', h2),
         tabela(['O que apareceu', 'O que fazer'], [
             ['"CPF incorreto! O dígito verificador não confere"', 'Digitou algum número errado. Confira o documento do cliente e digite de novo.'],
             ['Campos travados (cinza) ao digitar o CPF/CNPJ', 'Normal: a pessoa já existe. Use o botão <b>Vincular</b>.'],
             ['Não encontro o botão + Adicionar Proprietário/Produtor', 'Salve a Propriedade e clique em <b>Editar</b>: as seções só abrem depois de salva.'],
             ['Não aparece o botão Ativar Ambiente', 'Só a Consiste vê. Ou o Ambiente já está ativo. Confira o quadro do Ambiente.'],
             ['Não aparece o botão Criar Acesso', 'O Ambiente ainda não foi ativado, ou o Produtor já tem acesso.'],
             ['Criar Acesso recusado por falta de e-mail', 'Preencha o E-mail do Produtor, salve e tente de novo.'],
             ['Erro ao ativar o Ambiente', 'O sistema desfez tudo. Tente de novo; se repetir, chame o suporte com a mensagem exibida.'],
             ['Logo não carrega', 'Use imagem PNG ou JPG com até 10 MB.'],
         ], [70 * mm, LARGURA_UTIL - 70 * mm]),
         Spacer(1, 8),
         P('8.3 Glossário: palavras que você vai ver', h2),
         tabela(['Palavra', 'Significado'], [
             ['SISBOV', 'Serviço de Rastreabilidade da Cadeia Produtiva de Bovinos e Bubalinos, do Ministério da Agricultura (MAPA).'],
             ['ERAS', 'Estabelecimento Rural Aprovado no SISBOV: a fazenda que está habilitada a produzir animais rastreados.'],
             ['OESA', 'Organismo que atua na estrutura oficial do SISBOV, a quem os dados são comunicados.'],
             ['GTA', 'Guia de Trânsito Animal: documento que acompanha os animais quando eles se movimentam.'],
             ['NIRF', 'Número do imóvel rural na Receita Federal.'],
             ['CAR', 'Cadastro Ambiental Rural do imóvel.'],
             ['Propriedade', 'A fazenda (o lugar).'],
             ['Proprietário', 'O dono da terra.'],
             ['Produtor', 'Quem cria o gado e usa o Orion.'],
             ['Vínculo', 'A ligação entre uma pessoa e uma Propriedade. Pode ser Ativo ou Inativo.'],
             ['Ambiente', 'Espaço privado do Produtor dentro do Orion (capítulo 6).'],
             ['Titular', 'Cargo do primeiro acesso do Produtor, com todas as permissões.'],
             ['Protocolo', 'Programa de certificação ao qual a Propriedade é vinculada (ex.: União Europeia).'],
         ], [30 * mm, LARGURA_UTIL - 30 * mm]),
         Spacer(1, 10),
         caixa('dica', 'Precisa de ajuda?', 'Em qualquer tela de cadastro do Consiste existe o botão <b>Manual (PDF)</b>, que abre este manual já no capítulo daquela tela.')]
    return s


def construir(caminho):
    doc = Doc(caminho, pagesize=A4, leftMargin=MARGEM, rightMargin=MARGEM, topMargin=18 * mm, bottomMargin=22 * mm,
              title='Manual do Cadastro: Propriedade, Proprietário, Produtor e Ambiente', author='Consiste Informática')
    quadro = Frame(MARGEM, 22 * mm, LARGURA_UTIL, ALTURA - 40 * mm, id='q', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id='capa', frames=[quadro], onPage=_capa, autoNextPageTemplate='corpo'),
                          PageTemplate(id='corpo', frames=[quadro], onPage=_rodape)])
    story = parte_inicio() + parte_propriedades() + parte_pessoas() + parte_ambiente() + parte_acesso() + parte_final()
    doc.build(story)


# ---------------------------------------------------------
# Manuais SEPARADOS (um passo a passo so para cada tela)
# ---------------------------------------------------------
import re
from reportlab.platypus import Paragraph as _Par

_REF = re.compile(r'\s*\((?:explicado nos )?cap[ií]tulos? \d(?: e \d)?\)')
_NUM = re.compile(r'^\d+(?:\.\d+)?\.? (?=[A-ZÀ-Ú])')


def _limpar_texto(texto, estilo):
    texto = _REF.sub('', texto)
    texto = texto.replace('Você está pronto para o capítulo 4.', 'Em seguida, cadastre o Proprietário e o Produtor.')
    if getattr(estilo, 'name', '') in ('h1', 'h2'):
        texto = _NUM.sub('', texto)
    return texto


def construir_separado(caminho, titulo, subtitulo, partes, rodape):
    global TITULO_RODAPE
    TITULO_RODAPE = rodape
    original = _Par.__init__

    def patch(self, text, style=None, *a, **k):
        original(self, _limpar_texto(text, style), style, *a, **k)
    _Par.__init__ = patch
    try:
        capa = [Spacer(1, 55 * mm), P(titulo, capa_titulo), Spacer(1, 6), P(subtitulo, capa_sub), Spacer(1, 18 * mm),
                P('Passo a passo para quem nunca usou o sistema', capa_sub), Spacer(1, 60 * mm),
                P('Orion SISBOV &#8212; Plataforma Consiste<br/>Rastreabilidade bovina', capa_sub), Spacer(1, 8),
                P('Versão 1.0.0 &#8212; 17/11/2026', capa_sub), PageBreak()]
        story = capa
        for f in partes:
            story += f()
        while story and isinstance(story[-1], PageBreak):
            story.pop()
        doc = Doc(caminho, pagesize=A4, leftMargin=MARGEM, rightMargin=MARGEM, topMargin=18 * mm, bottomMargin=22 * mm,
                  title=titulo, author='Consiste Informática')
        quadro = Frame(MARGEM, 22 * mm, LARGURA_UTIL, ALTURA - 40 * mm, id='q', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        doc.addPageTemplates([PageTemplate(id='capa', frames=[quadro], onPage=_capa, autoNextPageTemplate='corpo'),
                              PageTemplate(id='corpo', frames=[quadro], onPage=_rodape)])
        doc.build(story)
    finally:
        _Par.__init__ = original


def _so(nome_cap):
    """Pega so uma parte dos capitulos 4/5 (parte_pessoas devolve os dois, separados por PageBreak)."""
    def f():
        todos = parte_pessoas()
        pos = [i for i, x in enumerate(todos) if isinstance(x, PageBreak)][0]
        return todos[:pos] if nome_cap == 'proprietarios' else todos[pos + 1:]
    return f


SEPARADOS = [
    ('Manual_Propriedade.pdf', 'COMO CADASTRAR<br/>A PROPRIEDADE', 'Cadastro da fazenda, passo a passo',
     [parte_propriedades], 'Manual: Cadastrar a Propriedade'),
    ('Manual_Proprietario.pdf', 'COMO CADASTRAR<br/>O PROPRIETÁRIO', 'Cadastro do dono da terra, passo a passo',
     [_so('proprietarios')], 'Manual: Cadastrar o Proprietário'),
    ('Manual_Produtor.pdf', 'COMO CADASTRAR<br/>O PRODUTOR', 'Cadastro, Ativação do Ambiente e Criação do Acesso',
     [_so('produtores'), parte_ambiente, parte_acesso], 'Manual: Cadastrar o Produtor, ativar o Ambiente e criar o Acesso'),
]


def gerar_separados():
    for arq, tit, sub, partes, rod in SEPARADOS:
        saida = os.path.join(AQUI, arq)
        construir_separado(saida, tit, sub, partes, rod)
        print('PDF gerado:', saida)


if __name__ == '__main__':
    construir(SAIDA_PDF)                 # 1a passada: descobre as paginas
    PAGINAS_ANT.update(PAGINAS)
    PAGINAS.clear()
    construir(SAIDA_PDF)                 # 2a passada: Sumario com as paginas certas
    with open(SAIDA_JSON, 'w', encoding='utf-8') as f:
        json.dump(PAGINAS, f, ensure_ascii=False, indent=2)
    print('PDF gerado:', SAIDA_PDF)
    print('Paginas dos capitulos:', PAGINAS)
    gerar_separados()

# FIM DE ARQUIVO: gerar_manual_cadastro.py
