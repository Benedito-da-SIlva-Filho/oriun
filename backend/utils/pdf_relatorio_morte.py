# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\pdf_relatorio_morte.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-01 19:00 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.2.0
# v1.2.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (2 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.1.0: Sessao 123 (2026-11-13 19:10 -03) - AUDITORIA ETAPA 6 (Regra #72): mascara de CPF/CNPJ passa pela funcao central. REVERSAO: .bak_antes_etapa6c.
# v1.0.4: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras do CNPJ mantidas na limpeza e na formatacao. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Os dois relatorios da Morte no visual do Magic/GERAS (medidas tiradas de "Geras Morte  Controle.pdf" e "Geras Morte Periodo.pdf";
#     A4, desenhado direto no canvas, posicoes em pontos a partir do topo da folha):
#       1) gerar_pdf_morte_controle(ctx)  - CONTROLE INTERNO: "SAIDA DE ANIMAIS / MORTE", numero do MRT na caixa, "Impressao: data hora";
#       2) gerar_pdf_morte_periodo(ctx)   - MORTES NO PERIODO: "Formulario para Comunicar Mortes ocorridas no Periodo", com o periodo.
#     Os dois: barra "DADOS DA ORIGEM DOS ANIMAIS", dados da origem, tabela (Ind | Codigo SISBOV | Tipo Morte | [Morte] | Causa Mortis |
#     Destino | Sexo | Eras) com divisorias verticais duplas, e, no fim, o resumo Sexo x faixa de idade (Zero a 12, +12 a 24, +24 a 36,
#     +36 meses) com Total e Geral. SISBOV com 15 digitos corridos (sem hifen). A faixa Eras e calculada NA DATA DA MORTE (decisao do Benedito).
#
#     ctx = {'origem': {'produtor_nome','cpf','cnpj','nirf','inscricao_estadual','codigo_eras','produtor_rural','propriedade_nome','municipio','cep'},
#            'animais': [{'sisbov','tipo','data','causa','destino','sexo' ('MACHO'|'FEMEA'),'eras'}],   # 'eras' = texto da faixa
#            'controle_texto': 'MRT000021' (so Controle), 'impresso_em': 'dd/mm/aaaa hh:mm:ss' (so Controle), 'periodo': ('dd/mm/aaaa','dd/mm/aaaa') (so Periodo)}
#
#     v1.0.0: Sessao 111 (01/11/2026) - Criacao. REVERSAO: apagar este arquivo.
#     v1.0.1: Sessao 111 (01/11/2026, 17:30) - Controle Interno: NIRF com 14 digitos (zeros a esquerda) e Produtor Rural EM BRANCO quando sem codigo (decisao do Benedito; o Magic imprime 00000000).
#     v1.0.2: Sessao 113 (03/11/2026, 15:05 -03) - NIRF com 14 digitos tambem no relatorio de Periodo; titulos do quadro-resumo (Zero a 12 Meses, + 12 a 24 Meses...) encolhem para caber na celula.  REVERSAO: .bak_antes_s113_pdf_morte.
#     v1.0.3: Sessao 113 (03/11/2026, 15:55 -03) - PDF do Controle ganha a coluna Morte (Data da Morte de cada animal), como no Periodo; a ordem segue por SISBOV.  REVERSAO: .bak_antes_s113_pdf_controle_data.
#             REVERSAO: .bak_antes_s111_nirf.
# =========================================================
from io import BytesIO

from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from backend.utils.validadores import formatar_documento

LARGURA = 595.32
ALTURA = 841.92
CINZA = colors.Color(0.941176, 0.941176, 0.941176)
NEGRITO = 'Helvetica-Bold'
NORMAL = 'Helvetica'
ASC = 0.76     # distancia entre o topo medido do texto e a linha de base, em fracao do tamanho (calibrado contra o Magic)

FAIXAS = ('Zero a 12 Meses', '+12 a 24 Meses', '+24 a 36 Meses', '+ 36 Meses')
FAIXAS_RESUMO = ('Zero a 12 Meses', '+ 12 a 24 Meses', '+ 24 a 36 Meses', '+ 36 Meses')


def faixa_eras(meses):
    """Faixa de idade em MESES COMPLETOS (None = sem nascimento)."""
    if meses is None:
        return ''
    if meses <= 12:
        return FAIXAS[0]
    if meses <= 24:
        return FAIXAS[1]
    if meses <= 36:
        return FAIXAS[2]
    return FAIXAS[3]


def _y(topo):
    return ALTURA - topo


def _fmt_doc(valor):
    return formatar_documento(valor)   # central (validadores.py)


def _sisbov(valor):
    t = str(valor or '').strip().replace('-', '').replace(' ', '')
    return t if t.isdecimal() else str(valor or '')


def _txt(c, x, topo, texto, fonte=NEGRITO, tam=8, alinha='l', largura_max=None):
    """Texto com o TOPO medido (como no Magic); alinha: l = x e a esquerda, c = x e o centro, r = x e a direita."""
    texto = str(texto or '')
    if not texto:
        return
    if largura_max:
        while tam > 4.5 and stringWidth(texto, fonte, tam) > largura_max:
            tam -= 0.25
    c.setFont(fonte, tam)
    c.setFillColor(colors.black)
    base = _y(topo + ASC * tam)
    if alinha == 'c':
        c.drawCentredString(x, base, texto)
    elif alinha == 'r':
        c.drawRightString(x, base, texto)
    else:
        c.drawString(x, base, texto)


def _caixa(c, x0, x1, topo, h, fundo=colors.white, borda=True):
    c.setLineWidth(0.5)
    c.setStrokeColor(colors.black)
    c.setFillColor(fundo)
    c.rect(x0, _y(topo + h), x1 - x0, h, stroke=1 if borda else 0, fill=1)


def _campo(c, x0, x1, topo, h, texto, rotulo=False, recuo=0.4):
    _caixa(c, x0, x1, topo, h)
    if rotulo:
        _txt(c, x1 - recuo, topo + (h - 8 * 0.76 * 1.0) / 2 - 0.9, texto, NEGRITO, 8, 'r')
    else:
        _txt(c, (x0 + x1) / 2, topo + (h - 8 * 0.76 * 1.0) / 2 - 0.9, texto, NEGRITO, 8, 'c', largura_max=(x1 - x0) - 3)


# -------------------------------------------------------
# Cabecalho de origem: dois layouts (alturas e posicoes medidas)
# -------------------------------------------------------
def _documento(o):
    cpf, cnpj = o.get('cpf') or '', o.get('cnpj') or ''
    if cpf and cnpj:
        return 'CPF/CNPJ:', f'{_fmt_doc(cpf)} / {_fmt_doc(cnpj)}'
    if cnpj:
        return 'CNPJ:', _fmt_doc(cnpj)
    return 'CPF:', _fmt_doc(cpf)


def _nirf_14(valor):
    d = ''.join(ch for ch in str(valor or '') if ch.isdecimal())
    return d.zfill(14) if d else ''


def _origem_controle(c, o):
    h = 12.1
    rot, doc = _documento(o)
    _campo(c, 88.9, 162.2, 77.4, h, 'Produtor:', True, 0.3)
    _campo(c, 163.8, 464.6, 77.4, h, o.get('produtor_nome', ''))
    _campo(c, 88.9, 162.2, 92.5, h, rot, True, 0.3)
    _campo(c, 163.8, 284.6, 92.5, h, doc)
    _campo(c, 310.0, 383.3, 92.5, h, 'NIRF', True, 0.2)
    _campo(c, 386.3, 464.6, 92.5, h, _nirf_14(o.get('nirf', '')))   # no Controle o Magic completa o NIRF com zeros (14 digitos)
    _campo(c, 88.9, 162.2, 107.6, h, 'Inscr. Estadual:', True, 0.2)
    _campo(c, 163.8, 284.6, 107.6, h, o.get('inscricao_estadual', ''))
    _campo(c, 310.0, 383.3, 107.6, h, 'Produtor Rural:', True, 0.4)
    _campo(c, 386.3, 464.6, 107.6, h, o.get('produtor_rural', ''))   # Benedito (01/11/2026): sem codigo fica EM BRANCO (o Magic imprime 00000000)
    _campo(c, 88.9, 162.2, 122.8, h, 'Propriedade:', True, 0.3)
    _campo(c, 163.8, 464.6, 122.8, h, o.get('propriedade_nome', ''))
    _campo(c, 88.9, 162.2, 137.9, h, 'Municipio:', True, 2.3)
    _campo(c, 163.8, 374.6, 137.9, h, o.get('municipio', ''))
    _campo(c, 396.4, 420.7, 137.9, h, 'CEP:', True, 2.4)
    _campo(c, 422.3, 464.6, 137.9, h, o.get('cep', ''))


def _origem_periodo(c, o):
    h = 13.6
    rot, doc = _documento(o)
    _campo(c, 88.9, 162.2, 78.1, h, 'Produtor:', True, 0.3)
    _campo(c, 163.8, 464.6, 78.1, h, o.get('produtor_nome', ''))
    _campo(c, 88.9, 162.2, 94.7, h, rot, True, 0.3)
    _campo(c, 163.8, 284.6, 94.7, h, doc)
    _campo(c, 310.0, 383.3, 94.7, h, 'NIRF', True, 27.0)
    _campo(c, 386.3, 464.6, 94.7, h, _nirf_14(o.get('nirf', '')))   # v1.0.2: NIRF com 14 digitos tambem no Periodo
    _campo(c, 88.9, 162.2, 111.2, h, 'Inscr. Estadual:', True, 0.2)
    _campo(c, 163.8, 284.6, 111.2, h, o.get('inscricao_estadual', ''))
    _campo(c, 310.0, 383.3, 111.2, h, 'Cód. ERAS', True, 15.6)
    _campo(c, 386.3, 464.6, 111.2, h, o.get('codigo_eras', ''))
    _campo(c, 88.9, 162.2, 127.8, h, 'Propriedade:', True, 0.3)
    _campo(c, 163.8, 464.6, 127.8, h, o.get('propriedade_nome', ''))
    _campo(c, 88.9, 162.2, 144.4, h, 'Municipio:', True, 2.3)
    _campo(c, 163.8, 374.6, 144.4, h, o.get('municipio', ''))
    _campo(c, 407.9, 464.6, 144.4, h, o.get('cep', ''))


# -------------------------------------------------------
# Tabela
# -------------------------------------------------------
def _grade(c, colunas, topo, base, texto_cab, cab_topo_texto, cab_altura, x_direita):
    """Moldura da tabela: caixa externa, faixa cinza do titulo, divisorias verticais duplas e rotulos."""
    x_esq = colunas[0][0]
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.72)
    c.rect(x_esq - 0.4, _y(base), (x_direita + 0.2) - (x_esq - 0.4), base - topo, stroke=1, fill=0)
    c.setFillColor(CINZA)
    c.rect(x_esq, _y(topo + 0.3 + cab_altura), x_direita - x_esq, cab_altura, stroke=0, fill=1)
    c.rect(x_direita - 1.4, _y(base - 0.2), 1.4, base - topo - 0.4, stroke=0, fill=1)
    c.setLineWidth(0.72)
    c.setStrokeColor(colors.black)
    for (x0, x1) in colunas[1:]:
        for dx in (-2.9, -0.7):
            c.line(x0 + dx, _y(topo + 0.3), x0 + dx, _y(base - 0.2))
    for (x0, x1), rotulo in zip(colunas, texto_cab):
        _txt(c, (x0 + x1) / 2, cab_topo_texto, rotulo, NORMAL, 8, 'c')


def _resumo(c, topo, animais):
    """Resumo Sexo x faixa de idade + Total + Geral, a partir de 'topo' (topo da caixa de titulos)."""
    cols = [(34.9, 77.3), (78.8, 151.4), (153.0, 225.6), (227.2, 299.8), (301.3, 373.9), (375.5, 448.1)]
    rotulos = ['Sexo'] + list(FAIXAS_RESUMO) + ['T o t a l']
    for (x0, x1), r in zip(cols, rotulos):
        _caixa(c, x0, x1, topo, 12.1)
        _txt(c, (x0 + x1) / 2, topo + 1.7, r, NEGRITO, 10, 'c', largura_max=(x1 - x0) - 4)   # v1.0.2: titulo cabe na celula (encolhe a letra se preciso)
    _caixa(c, 449.6, 518.6, topo, 17.1)
    _txt(c, 484.1, topo + 2.4, 'G e r a l', NEGRITO, 14, 'c')
    linhas = (('Fêmeas', 'FEMEA', topo + 13.7), ('Machos', 'MACHO', topo + 28.1))
    total_geral = len(animais)
    for nome, sexo, t in linhas:
        _caixa(c, *cols[0], t, 12.1)
        _txt(c, (cols[0][0] + cols[0][1]) / 2, t + 1.6, nome, NEGRITO, 10, 'c', largura_max=33)
        soma = 0
        for (x0, x1), faixa in zip(cols[1:5], FAIXAS):
            q = sum(1 for a in animais if a.get('sexo') == sexo and a.get('eras') == faixa)
            soma += q
            _caixa(c, x0, x1, t, 12.1)
            _txt(c, (x0 + x1) / 2, t + 1.6, str(q), NEGRITO, 10, 'c')
        qt = sum(1 for a in animais if a.get('sexo') == sexo)
        _caixa(c, *cols[5], t, 12.1)
        _txt(c, (cols[5][0] + cols[5][1]) / 2, t + 1.6, str(qt), NEGRITO, 10, 'c')
    _caixa(c, 449.6, 518.6, topo + 19.4, 20.8)
    _txt(c, 484.1, topo + 24.3, str(total_geral), NEGRITO, 12, 'c')


# -------------------------------------------------------
# Controle Interno (MRT)
# -------------------------------------------------------
COL_CONTROLE = [(2.9, 25.2), (25.2, 108.7), (108.7, 157.7), (157.7, 209.7), (209.7, 344.9), (344.9, 438.5), (438.5, 475.9), (475.9, 554.4)]
CAB_CONTROLE = ['Ind', 'Código SISBOV', 'Tipo Morte', 'Morte', 'Causa Mortis', 'Destino', 'Sexo', 'Eras']   # v1.0.3: coluna Morte (Data da Morte de cada animal)
LINHAS_CONTROLE = 41


def _pagina_controle(c, ctx, lote, inicio, ultima):
    _txt(c, 233.4, 9.3, 'SAIDA DE ANIMAIS', NEGRITO, 16, 'c')
    _txt(c, 235.4, 34.5, 'MORTE', NEGRITO, 16, 'c')
    _caixa(c, 453.2, 546.0, 9.0, 17.2, fundo=colors.white)
    _txt(c, 499.6, 11.4, ctx.get('controle_texto', ''), NEGRITO, 14, 'c')
    _txt(c, 447.5, 41.9, f"Impressão: {ctx.get('impresso_em', '')}", NEGRITO, 7, 'l')
    _caixa(c, 1.8, 555.4, 52.2, 20.8, fundo=CINZA)
    _txt(c, 280.4, 56.4, 'DADOS DA ORIGEM DOS ANIMAIS', NEGRITO, 14, 'c')
    _origem_controle(c, ctx['origem'])
    n = len(lote)
    base = 167.8 + 15.1 + max(n - 1, 0) * 15.85 + 0.6 if n else 183.5
    _grade(c, COL_CONTROLE, 153.4, base, CAB_CONTROLE, 156.7, 14.4, 554.4)
    c.setLineWidth(0.72)
    c.setStrokeColor(colors.black)
    for i, a in enumerate(lote):
        topo = 171.0 + i * 15.85
        if i < n - 1:
            y = 182.9 + i * 15.85
            c.line(2.9, _y(y), 554.4, _y(y))
        _txt(c, 11.85, topo, str(inicio + i + 1).zfill(3), NEGRITO, 7, 'c')
        _txt(c, 64.8, topo, _sisbov(a['sisbov']), NEGRITO, 7, 'c')
        _txt(c, 110.2, topo, a.get('tipo', ''), NEGRITO, 7, 'l')
        _txt(c, 183.7, topo, a.get('data', ''), NEGRITO, 7, 'c')
        _txt(c, 211.1, topo, a.get('causa', ''), NEGRITO, 7, 'l', largura_max=131)
        _txt(c, 346.3, topo, a.get('destino', ''), NEGRITO, 7, 'l')
        _txt(c, 455.8, topo, a.get('sexo_texto', ''), NEGRITO, 7, 'c')
        _txt(c, 514.0, topo, a.get('eras', ''), NEGRITO, 7, 'c')
    return base


def gerar_pdf_morte_controle(ctx):
    animais = ctx.get('animais') or []
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(LARGURA, ALTURA))
    c.setTitle(f"Morte - Controle Interno {ctx.get('controle_texto', '')}")
    c.setAuthor('Orion SISBOV')
    paginas = max(1, (len(animais) + LINHAS_CONTROLE - 1) // LINHAS_CONTROLE)
    for p in range(paginas):
        lote = animais[p * LINHAS_CONTROLE:(p + 1) * LINHAS_CONTROLE]
        base = _pagina_controle(c, ctx, lote, p * LINHAS_CONTROLE, p == paginas - 1)
        if p == paginas - 1:
            if base + 50 < ALTURA - 14:
                _resumo(c, base + 2.3, animais)
            else:
                c.showPage()
                _resumo(c, 20.0, animais)
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# -------------------------------------------------------
# Mortes no Periodo
# -------------------------------------------------------
COL_PERIODO = [(2.9, 25.2), (25.2, 104.4), (104.4, 156.2), (156.2, 208.1), (208.1, 352.1), (352.1, 431.3), (431.3, 468.7), (468.7, 547.2)]
CAB_PERIODO = ['Ind', 'Código SISBOV', 'Tipo Morte', 'Morte', 'Causa Mortis', 'Destino', 'Sexo', 'Eras']
LINHAS_PERIODO = 41


def _pagina_periodo(c, ctx, lote, inicio):
    _txt(c, 344.75, 8.6, 'Formulário para Comunicar Mortes ocorridas no Período', NEGRITO, 16, 'c', largura_max=395.3)
    ini, fim = ctx.get('periodo', ('', ''))
    _txt(c, 318.95, 32.2, f'Período: {ini} até {fim}', NEGRITO, 12, 'c', largura_max=177.5)
    _caixa(c, 1.8, 555.4, 54.4, 20.7, fundo=CINZA)
    _txt(c, 280.4, 58.6, 'DADOS DA ORIGEM DOS ANIMAIS', NEGRITO, 14, 'c')
    _origem_periodo(c, ctx['origem'])
    n = len(lote)
    base = 177.1 + n * 15.85 + 0.4 if n else 178.0
    _grade(c, COL_PERIODO, 162.7, base, CAB_PERIODO, 166.1, 14.4, 547.2)
    c.setLineWidth(0.72)
    c.setStrokeColor(colors.black)
    for i, a in enumerate(lote):
        topo = 180.4 + i * 15.85
        if i < n - 1:
            y = 192.2 + i * 15.85
            c.line(2.9, _y(y), 547.2, _y(y))
        _txt(c, 11.85, topo, str(inicio + i + 1).zfill(3), NEGRITO, 7, 'c')
        _txt(c, 62.6, topo, _sisbov(a['sisbov']), NEGRITO, 7, 'c')
        _txt(c, 128.1, topo, a.get('tipo', ''), NEGRITO, 7, 'c')
        _txt(c, 180.0, topo, a.get('data', ''), NEGRITO, 7, 'c')
        _txt(c, 209.5, topo, a.get('causa', ''), NEGRITO, 7, 'l', largura_max=140)
        _txt(c, 389.5, topo, a.get('destino', ''), NEGRITO, 7, 'c')
        _txt(c, 448.6, topo, a.get('sexo_texto', ''), NEGRITO, 7, 'c')
        _txt(c, 506.9, topo, a.get('eras', ''), NEGRITO, 7, 'c')
    return base


def gerar_pdf_morte_periodo(ctx):
    animais = ctx.get('animais') or []
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(LARGURA, ALTURA))
    c.setTitle('Morte - Mortes no Periodo')
    c.setAuthor('Orion SISBOV')
    paginas = max(1, (len(animais) + LINHAS_PERIODO - 1) // LINHAS_PERIODO)
    for p in range(paginas):
        lote = animais[p * LINHAS_PERIODO:(p + 1) * LINHAS_PERIODO]
        base = _pagina_periodo(c, ctx, lote, p * LINHAS_PERIODO)
        if p == paginas - 1:
            if base + 50 < ALTURA - 14:
                _resumo(c, base + 5.1, animais)
            else:
                c.showPage()
                _resumo(c, 20.0, animais)
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_relatorio_morte.py
# =========================================================
