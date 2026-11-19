# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\pdf_anexo_xxii.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-01 17:50 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.2.0
# v1.2.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.1.0: Sessao 123 (2026-11-13 19:10 -03) - AUDITORIA ETAPA 6 (Regra #72): mascara de CPF/CNPJ passa pela funcao central. REVERSAO: .bak_antes_etapa6c.
# v1.0.1: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras do CNPJ mantidas na limpeza e na formatacao. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     PDF do ANEXO XXII - Comunicado de Sacrificio, Morte Natural ou Acidental de Animais (Notificacao de Morte), no visual do Magic/GERAS
#     (medidas tiradas do PDF "Gers Morte.pdf": A4, desenhado direto no canvas, em pontos a partir do topo da folha).
#     Cabecalho em todas as folhas: titulo + numero da Notificacao (caixa), barra "DADOS DA ORIGEM DOS ANIMAIS", Produtor, CPF/CNPJ e Cod ERAS,
#     Propriedade, Municipio e CEP, e a linha de titulos da tabela (No SISBOV | Morte | Causa | Data | Observacao). 42 animais por folha.
#     Observacao = sexo + idade em meses NA DATA DA MORTE (ex.: "F 153 meses"). Depois da ultima linha: "Referente ao Comunicado Nro ...",
#     as duas vias (1a Certificadora, 2a Arquivo Eras da Propriedade), as duas observacoes oficiais, a linha de assinatura e a nota da
#     certificadora; se nao couber na folha, vai para uma folha nova (com o cabecalho). SISBOV com 15 digitos corridos, sem hifen.
#
#     contexto = {
#       'numero_comunicado': int,
#       'origem': {'produtor_nome', 'cpf', 'cnpj', 'codigo_eras', 'propriedade_nome', 'municipio' (ja com a UF: 'CIDADE/MT'), 'cep'},
#       'animais': [{'sisbov', 'tipo', 'causa', 'data' (dd/mm/aaaa), 'obs'}, ...]   # na ordem em que devem sair
#     }
#
#     v1.0.0: Sessao 111 (01/11/2026) - Criacao. REVERSAO: apagar este arquivo.
# =========================================================
from io import BytesIO

from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from backend.utils.validadores import formatar_documento

LARGURA_PAGINA = 595.32
ALTURA_PAGINA = 841.92
FUNDO = colors.Color(0.941176, 0.941176, 0.941176)
FONTE_TITULO = 'Helvetica-Bold'   # no Magic os rotulos e o titulo sao Arial Negrito (conferido pela largura das palavras)
FONTE_ROTULO = 'Helvetica-Bold'
FONTE_VALOR = 'Helvetica-Bold'
FONTE_LINHA = 'Helvetica'

LINHAS_POR_FOLHA = 42
TOPO_PRIMEIRA_LINHA = 165.6     # topo do "passo" da linha 1 (a caixa fica 1,8 pt abaixo)
PASSO_LINHA = 15.85
ALT_CAIXA_LINHA = 13.6
ALTURA_RODAPE = 118             # espaco que o bloco final (vias, observacoes, assinatura) ocupa a partir do topo da proxima linha

X_COLUNAS = {   # (x0, x1) das caixas de cada coluna da tabela
    'ind': (4.7, 19.0), 'sisbov': (21.2, 88.8), 'morte': (91.1, 133.4), 'causa': (135.0, 317.8),
    'data': (320.0, 373.2), 'obs': (375.5, 561.8),
}
X_CABECALHO = {   # caixas cinzas do titulo da tabela
    'sisbov': (20.5, 88.1), 'morte': (90.4, 132.7), 'causa': (135.0, 317.8), 'data': (320.0, 373.2), 'obs': (375.5, 561.8),
}


def formatar_sisbov(sisbov):
    texto = str(sisbov or '').strip()
    limpo = texto.replace('-', '').replace(' ', '')
    return limpo if limpo.isdecimal() else texto


def _formatar_documento(valor):
    return formatar_documento(valor)   # central (validadores.py)


def _y(topo):
    """Coordenada do reportlab (de baixo para cima) a partir do topo da folha."""
    return ALTURA_PAGINA - topo


def _caixa(c, x0, x1, topo, altura, texto='', fonte=FONTE_VALOR, tam=8, alinha='c', fundo=None, borda=True, recuo=0.0, dy=0.0):
    c.setLineWidth(0.5)
    c.setStrokeColor(colors.black)
    if fundo is not None:
        c.setFillColor(fundo)
        c.rect(x0, _y(topo + altura), x1 - x0, altura, stroke=1 if borda else 0, fill=1)
    elif borda:
        c.rect(x0, _y(topo + altura), x1 - x0, altura, stroke=1, fill=0)
    texto = str(texto or '')
    if not texto:
        return
    largura = x1 - x0
    while tam > 5 and stringWidth(texto, fonte, tam) > largura - 3:
        tam -= 0.25
    c.setFillColor(colors.black)
    c.setFont(fonte, tam)
    base = _y(topo + (altura + tam * 0.72) / 2 + dy)
    if alinha == 'c':
        c.drawCentredString((x0 + x1) / 2, base, texto)
    elif alinha == 'r':
        c.drawRightString(x1 - 0.4 - recuo, base, texto)
    else:
        c.drawString(x0 + 0.4 + recuo, base, texto)


def _cabecalho(c, ctx, numero_6):
    c.setFillColor(colors.black)
    c.setFont(FONTE_TITULO, 18)
    c.drawString(229.0, _y(9.0 + 14.5), 'ANEXO XXII')
    c.setLineWidth(0.5)
    c.rect(498.6, _y(36.2), 54.6, 20.0, stroke=1, fill=0)
    c.setFont(FONTE_TITULO, 18)
    c.drawCentredString(525.9, _y(18.4 + 14.5), numero_6)
    c.setFont(FONTE_ROTULO, 8)
    c.drawString(195.8, _y(33.5 + 6.5), 'COMUNICADO DE SACRIFÍCIO, MORTE')
    c.drawString(195.8, _y(43.1 + 6.5), 'NATURAL OU ACIDENTAL DE ANIMAIS.')

    # barra de secao
    c.setLineWidth(0.5)
    c.setFillColor(FUNDO)
    c.rect(9.7, _y(78.7), 550.0, 17.1, stroke=1, fill=1)
    c.setFillColor(colors.black)
    c.setFont(FONTE_TITULO, 11)
    c.drawCentredString(284.7, _y(61.6 + 12.4), 'DADOS DA ORIGEM DOS ANIMAIS')

    o = ctx['origem']
    cpf, cnpj = o.get('cpf') or '', o.get('cnpj') or ''
    if cpf and cnpj:
        rotulo_doc, valor_doc = 'CPF/CNPJ:', f'{_formatar_documento(cpf)} / {_formatar_documento(cnpj)}'
    elif cnpj:
        rotulo_doc, valor_doc = 'CNPJ:', _formatar_documento(cnpj)
    else:
        rotulo_doc, valor_doc = 'CPF:', _formatar_documento(cpf)
    h = 13.6
    _caixa(c, 96.8, 170.2, 81.0, h, 'Produtor:', FONTE_ROTULO, 8, 'r', fundo=colors.white)
    _caixa(c, 172.4, 473.3, 81.0, h, o.get('produtor_nome', ''), FONTE_VALOR, 8, 'c', fundo=colors.white)
    _caixa(c, 96.8, 170.2, 98.3, h, rotulo_doc, FONTE_ROTULO, 8, 'r', fundo=colors.white)
    _caixa(c, 172.4, 293.3, 98.3, h, valor_doc, FONTE_VALOR, 8, 'c', fundo=colors.white)
    _caixa(c, 329.4, 386.2, 98.3, h, 'Cód ERAS:', FONTE_ROTULO, 8, 'r', fundo=colors.white, recuo=2.3)
    _caixa(c, 388.4, 473.3, 98.3, h, o.get('codigo_eras', ''), FONTE_VALOR, 8, 'c', fundo=colors.white)
    _caixa(c, 96.8, 170.2, 115.6, h, 'Propriedade:', FONTE_ROTULO, 8, 'r', fundo=colors.white)
    _caixa(c, 172.4, 473.3, 115.6, h, o.get('propriedade_nome', ''), FONTE_VALOR, 8, 'c', fundo=colors.white)
    _caixa(c, 96.8, 170.2, 132.8, h, 'Municipio:', FONTE_ROTULO, 8, 'r', fundo=colors.white, recuo=2.3)
    _caixa(c, 172.4, 383.3, 132.8, h, o.get('municipio', ''), FONTE_VALOR, 8, 'c', fundo=colors.white)
    _caixa(c, 416.5, 473.3, 132.8, h, o.get('cep', ''), FONTE_VALOR, 8, 'c', fundo=colors.white)

    # titulos da tabela
    for chave, rotulo in (('sisbov', 'Nº SISBOV'), ('morte', 'Morte'), ('causa', 'Causa'), ('data', 'Data'), ('obs', 'Observação')):
        x0, x1 = X_CABECALHO[chave]
        _caixa(c, x0, x1, 151.6, 13.5, rotulo, FONTE_ROTULO, 8, 'c', fundo=FUNDO)


def _linha(c, indice, topo_passo, a):
    topo = topo_passo + 1.8
    h = ALT_CAIXA_LINHA
    dy = -0.5   # o texto das linhas do Magic fica 0,5 pt mais alto
    _caixa(c, *X_COLUNAS['ind'], topo, h, str(indice), FONTE_LINHA, 8, 'c', fundo=colors.white, dy=dy)
    _caixa(c, *X_COLUNAS['sisbov'], topo, h, formatar_sisbov(a.get('sisbov')), FONTE_LINHA, 8, 'l', dy=dy, recuo=0.1)
    _caixa(c, *X_COLUNAS['morte'], topo, h, a.get('tipo', ''), FONTE_LINHA, 8, 'c', dy=dy)
    _caixa(c, *X_COLUNAS['causa'], topo, h, a.get('causa', ''), FONTE_LINHA, 8, 'l', dy=dy)
    _caixa(c, *X_COLUNAS['data'], topo, h, a.get('data', ''), FONTE_LINHA, 8, 'c', dy=dy)
    _caixa(c, *X_COLUNAS['obs'], topo, h, a.get('obs', ''), FONTE_LINHA, 8, 'l', recuo=2.2, dy=dy)


def _rodape(c, numero_6, topo):
    """Bloco final (vias, observacoes oficiais, assinatura). 'topo' = topo da proxima linha livre."""
    c.setFillColor(colors.black)
    c.setFont(FONTE_ROTULO, 8)
    c.drawString(24.0, _y(topo + 2.2 + 6.5), f'Referente ao Comunicado Nro {numero_6}')
    c.setFont(FONTE_ROTULO, 7)
    c.drawString(434.9, _y(topo + 0.9 + 5.7), '1ª via Certificadora')
    c.drawString(434.9, _y(topo + 13.8 + 5.7), '2ª via Arquivo Eras da Propriedade')
    c.drawString(28.8, _y(topo + 13.8 + 5.7), 'Obs: Animais mortos antes da identificação devem constar desde comunicado. Por não terem número, devem ser')
    c.drawString(28.8, _y(topo + 22.1 + 5.7), 'descritos pelo gênero e idade aproximada.')
    c.drawString(28.8, _y(topo + 33.3 + 5.7), 'Obs 2: Em caso de abigeato ou desaparecimento, fica dispensado o disposto no §2º Art. 68, Anexo III, IN 51/2018,')
    c.drawString(28.8, _y(topo + 41.5 + 5.7), 'sendo necessário, para estes casos, justificativa em campo de observação ou documento complementar.')
    c.setLineWidth(0.72)
    c.line(168.5, _y(topo + 97.2), 401.8, _y(topo + 97.2))
    c.drawCentredString(285.0, _y(topo + 101.7 + 5.7), 'Assinatura do produtor rural ou responsável pela informação')
    c.drawCentredString(280.2, _y(topo + 112.7 + 5.7), 'A certificadora deverá indicar a comprovação, com data, do recebimento deste documento.')


def gerar_pdf_anexo_xxii(contexto):
    animais = contexto.get('animais') or []
    numero_6 = f'{int(contexto["numero_comunicado"]):06d}'
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(LARGURA_PAGINA, ALTURA_PAGINA))
    c.setTitle(f'Anexo XXII - Notificacao de Morte {numero_6}')
    c.setAuthor('Orion SISBOV')

    total = len(animais)
    indice = 0
    folhas = max(1, (total + LINHAS_POR_FOLHA - 1) // LINHAS_POR_FOLHA)
    for folha in range(folhas):
        _cabecalho(c, contexto, numero_6)
        lote = animais[folha * LINHAS_POR_FOLHA:(folha + 1) * LINHAS_POR_FOLHA]
        for posicao, a in enumerate(lote):
            indice += 1
            _linha(c, indice, TOPO_PRIMEIRA_LINHA + posicao * PASSO_LINHA, a)
        usadas = len(lote)
        proximo_topo = TOPO_PRIMEIRA_LINHA + usadas * PASSO_LINHA
        ultima = (folha == folhas - 1)
        if ultima:
            if proximo_topo + ALTURA_RODAPE <= ALTURA_PAGINA - 14:
                _rodape(c, numero_6, proximo_topo)
                c.showPage()
            else:   # nao cabe: o bloco final vai para uma folha nova, com o cabecalho
                c.showPage()
                _cabecalho(c, contexto, numero_6)
                _rodape(c, numero_6, TOPO_PRIMEIRA_LINHA)
                c.showPage()
        else:
            c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_anexo_xxii.py
# =========================================================
