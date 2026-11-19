# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\pdf_anexo_saida.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-20 12:15 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 2.4.0
# v2.4.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v2.3.0: Sessao 123 (2026-11-13 19:10 -03) - AUDITORIA ETAPA 6 (Regra #72): mascara de CPF/CNPJ passa pela funcao central (agora tambem mascara quando o texto tem espacos). REVERSAO: .bak_antes_etapa6c.
# v2.2.1: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras do CNPJ mantidas na limpeza e na formatacao. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Monta os PDFs do Comunicado de Saida (Abate) - TRES modelos, o usuario escolhe:
#         - gerar_pdf_anexo_xx(contexto):         Anexo XX, grade Ind | SISBOV (5 pares por linha).
#         - gerar_pdf_anexo_xxi_barras(contexto): Anexo XXI oficial, 2 animais por linha, CODIGO DE BARRAS
#                                                 (Interleaved 2 of 5, 16 digitos = zero + SISBOV; lido pelo celular),
#                                                 com os 16 digitos espacados embaixo das barras.
#         - gerar_pdf_anexo_xxi_qrcode(contexto): modelo ORION, igual ao XXI, mas com QR CODE no lugar das barras.
#                                                 O QR guarda SO o numero SISBOV (15 digitos), sem endereco de site;
#                                                 o SISBOV tambem vai escrito ao lado. Modelo em teste (o QR ainda
#                                                 nao esta em vigor no SISBOV).
#     A Impressao (grava IMPRESSO na primeira vez) e a Reimpressao (nunca grava) chamam as MESMAS funcoes.
#
#     VISUAL (v2.0.0): copia dos formularios do sistema anterior (Magic Print Preview, amostras do Benedito):
#     titulos em fonte com serifa, barras de secao cinza, cada rotulo e cada valor numa caixinha propria,
#     blocos de campos recuados e centralizados, CPF/CNPJ formatados, sem rodape. Tudo desenhado direto no
#     PDF (Flowable com caixas), em coordenadas medidas nas amostras (pixels da amostra * K).
#
#     contexto (dict) - montado por comunicado_saida_display.montar_contexto_anexo_saida:
#         numero_comunicado (int)
#         origem:  produtor_nome, cpf, cnpj, inscricao_estadual, codigo_eras, propriedade_nome, municipio, cep
#         destino: frigorifico_nome, estabelecimento, cnpj, inscricao_estadual, municipio, sif
#         gtas: lista de {numero, qtde_animais, data_emissao (texto)}
#         total_animais (int), data_saida (texto dd/mm/aaaa)
#         sisbov: lista de strings com 15 digitos, ja na ordem final de numeracao
#
#     ASSUNCOES: codigo de barras Interleaved 2 of 5, 16 digitos (zero + SISBOV), como na amostra; se o celular
#     nao ler igual, trocar o padrao em _BarraTexto. Campo sem dado sai em branco (como no sistema anterior).
#
#     v1.0.0: Criacao (Sessao 101, Pacote 2 - Impressao/Reimpressao do Comunicado de Saida).
#     v1.0.1: Sessao 101 (20/10/2026, 13:15 -03) - Pares na mesma linha (CPF+CNPJ, IE+ERAS, Municipio+CEP; CNPJ+IE, Municipio+SIF).
#     v2.0.0: Sessao 101 (20/10/2026, 13:30 -03) - REFEITO no visual das amostras do Magic (Anexo XX e XXI): caixinhas, fontes
#             com serifa, titulos oficiais, grade do XXI com barras e digitos espacados, sem rodape. Nao usa mais
#             pdf_anexo_xix.py. QR Code copia o desenho do XXI.
#     v2.0.1: Sessao 101 (20/10/2026, 18:25 -03) - Anexo XX: numeros dos Brincos centralizados na altura da celula (estavam colados na linha de cima; medido a 600 dpi: folga topo = folga base).  REVERSAO: .bak_antes_centro_sisbov_s101
#     v2.0.2: Sessao 101 (20/10/2026, 18:50 -03) - Pecas compartilhadas com o Anexo XIX: _Desenho aceita cor de fundo por item ('cor') e _grade_sisbov aceita fundo_cabecalho (padrao None = igual a antes).  REVERSAO: .bak_antes_xix_s101
#     v2.0.3: Sessao 101 (20/10/2026, 19:10 -03) - Grade de GTAs: cabecalho GTA | Animais | Emissao so na 1a linha de blocos (igual ao Anexo XIX).  REVERSAO: .bak_antes_cabecalho_gta_s101
#     v2.1.0: Sessao 103 (22/10/2026, 08:25 -03) - SISBOV SEM HIFEN: formatar_sisbov passa a devolver os 15 digitos corridos (decisao de Benedito:
#             regra unica para todos os relatorios e formularios). Como todos os PDFs usam esta rotina, a mudanca vale para o Comunicado
#             (Anexo XX e texto ao lado do QR), PIA, Notificacao, Nascimentos, ERAS e Embarque.  REVERSAO: .bak_antes_sem_hifen_s103.
#     v2.2.0: Sessao 113 (03/11/2026, 13:05 -03) - Comunicado de Venda e de Transferencia SEM o campo S.I.F. (SIF e de frigorifico): Municipio fica sozinho na linha.  REVERSAO: .bak_antes_s113_sif.
# =========================================================

from io import BytesIO

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.common import I2of5
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.utils.pdf_reportlab import LARGURA_UTIL, MARGEM_H, PAGE_SIZE
from backend.utils.validadores import formatar_documento as _formatar_documento_central

# Margem vertical propria (mesma dos anexos da Entrada)
MARGEM_V_ANEXO = 28

# Escala: as amostras foram medidas em pixels (barra de secao = 955 px); K converte para pontos.
K = LARGURA_UTIL / 955.0

ALT_BARRA = 13.5     # barra cinza de secao
ALT_CAIXA = 11.5     # caixinha de rotulo/valor
PASSO = 12.8         # distancia entre linhas de campos
FUNDO_CINZA = colors.HexColor('#e6e6e6')

FONTE_ROTULO = 'Times-Bold'
FONTE_VALOR = 'Helvetica-Bold'


def _x(px):
    return px * K


# -------------------------------------------------------
# Formatacao de documento: 11 digitos = CPF, 14 = CNPJ; outro tamanho vai como esta.
# -------------------------------------------------------
def formatar_documento(valor):
    return _formatar_documento_central(valor)   # central (validadores.py)


# SISBOV escrito: 15 digitos corridos, SEM hifen (decisao de Benedito, Sessao 103: vale para todos os relatorios e formularios)
def formatar_sisbov(sisbov):
    texto = str(sisbov or '').strip()
    return texto.replace('-', '').replace(' ', '') if texto.replace('-', '').replace(' ', '').isdecimal() else texto


# -------------------------------------------------------
# Desenho por caixas: lista de itens, cada um um dict
#   x0, x1 (px da amostra, relativos a borda esquerda da barra de secao), y (pt a partir do topo), h (pt),
#   texto, fonte, tam, alinha ('c', 'r', 'l'), fundo (bool), borda (bool)
# -------------------------------------------------------
class _Desenho(Flowable):
    def __init__(self, itens, altura):
        super().__init__()
        self.itens = itens
        self.altura = altura

    def wrap(self, largura, altura):
        return LARGURA_UTIL, self.altura

    def draw(self):
        c = self.canv
        for it in self.itens:
            x0 = _x(it['x0'])
            largura = _x(it['x1']) - x0
            base = self.altura - it['y'] - it['h']
            if it.get('borda', True) or it.get('fundo'):
                c.setLineWidth(0.7)
                c.setStrokeColor(colors.black)
                if it.get('fundo'):
                    c.setFillColor(it.get('cor', FUNDO_CINZA))
                c.rect(x0, base, largura, it['h'], stroke=1 if it.get('borda', True) else 0, fill=1 if it.get('fundo') else 0)
            texto = it.get('texto') or ''
            if not texto:
                continue
            fonte = it.get('fonte', FONTE_VALOR)
            tam = it.get('tam', 8)
            while tam > 5 and stringWidth(texto, fonte, tam) > largura - 4:
                tam -= 0.25
            c.setFillColor(colors.black)
            c.setFont(fonte, tam)
            y_texto = base + (it['h'] - tam * 0.72) / 2
            alinha = it.get('alinha', 'c')
            if alinha == 'c':
                c.drawCentredString(x0 + largura / 2, y_texto, texto)
            elif alinha == 'r':
                c.drawRightString(x0 + largura - 3, y_texto, texto)
            else:
                c.drawString(x0 + 3, y_texto, texto)


def _caixa(x0, x1, y, texto, rotulo=False, h=ALT_CAIXA, tam=None, alinha=None, fonte=None):
    return {
        'x0': x0, 'x1': x1, 'y': y, 'h': h, 'texto': texto,
        'fonte': fonte or (FONTE_ROTULO if rotulo else FONTE_VALOR),
        'tam': tam or 8,
        'alinha': alinha or ('r' if rotulo else 'c'),
    }


# -------------------------------------------------------
# Titulo com o numero do Comunicado
# -------------------------------------------------------
def _titulo(numero_comunicado, modelo_xx):
    numero = f'{numero_comunicado:06d}'
    itens = []
    if modelo_xx:
        itens.append({'x0': 0, 'x1': 955, 'y': 2, 'h': 22, 'texto': 'ANEXO XX', 'fonte': 'Times-Bold', 'tam': 20, 'alinha': 'c', 'borda': False})
        itens.append({'x0': 0, 'x1': 955, 'y': 28, 'h': 13, 'texto': 'FORMULÁRIO PARA COMUNICADO DE', 'fonte': 'Times-Bold', 'tam': 11.5, 'alinha': 'c', 'borda': False})
        itens.append({'x0': 0, 'x1': 955, 'y': 41, 'h': 13, 'texto': 'SAÍDA (OFÍCIO CIRCULAR Nº 07/2018)', 'fonte': 'Times-Bold', 'tam': 11.5, 'alinha': 'c', 'borda': False})
        itens.append({'x0': 740, 'x1': 809, 'y': 8, 'h': 16, 'texto': 'Nro:', 'fonte': 'Times-Bold', 'tam': 12, 'alinha': 'r', 'borda': False})
        itens.append({'x0': 816, 'x1': 895, 'y': 8, 'h': 16, 'texto': numero, 'fonte': 'Times-Bold', 'tam': 12.5, 'alinha': 'c'})
        altura = 62
    else:
        itens.append({'x0': 0, 'x1': 955, 'y': 4, 'h': 14, 'texto': 'FORMULÁRIO PARA COMUNICADO DE SAÍDA', 'fonte': 'Times-Bold', 'tam': 12, 'alinha': 'c', 'borda': False})
        itens.append({'x0': 0, 'x1': 955, 'y': 18, 'h': 14, 'texto': '(ANEXO XXI DO OFÍCIO CIRCULAR Nº 07/2018)', 'fonte': 'Times-Bold', 'tam': 12, 'alinha': 'c', 'borda': False})
        itens.append({'x0': 856, 'x1': 937, 'y': 4, 'h': 17, 'texto': numero, 'fonte': 'Times-Bold', 'tam': 13, 'alinha': 'c'})
        altura = 44
    return _Desenho(itens, altura)


# -------------------------------------------------------
# Bloco de secao (Origem / Destino): barra cinza + linhas de campos, medidas nas amostras.
# linha = ('1', rotulo, chave)  ou  ('2', rotulo1, chave1, fim_valor1, rotulo2, chave2, ini_rotulo2, fim_rotulo2, ini_valor2)
# -------------------------------------------------------
_L0, _L1, _V0, _V1 = 146, 278, 282, 805   # rotulo (x0, x1) e valor (x0, x1) das linhas de 1 campo


def _bloco_secao(titulo, dados, linhas):
    itens = [{'x0': 0, 'x1': 955, 'y': 0, 'h': ALT_BARRA, 'texto': titulo, 'fonte': 'Times-Bold', 'tam': 10.5, 'alinha': 'c', 'fundo': True}]
    y = ALT_BARRA + 1.5
    for linha in linhas:
        if linha[0] == '1':
            _, rotulo, chave = linha
            itens.append(_caixa(_L0, _L1, y, rotulo, rotulo=True))
            itens.append(_caixa(_V0, _V1, y, dados.get(chave) or ''))
        else:
            _, rotulo1, chave1, fim_v1, rotulo2, chave2, ini_l2, fim_l2, ini_v2 = linha
            itens.append(_caixa(_L0, _L1, y, rotulo1, rotulo=True))
            itens.append(_caixa(_V0, fim_v1, y, dados.get(chave1) or ''))
            itens.append(_caixa(ini_l2, fim_l2, y, rotulo2, rotulo=True))
            itens.append(_caixa(ini_v2, _V1, y, dados.get(chave2) or ''))
        y += PASSO
    return _Desenho(itens, y)


def _blocos_origem_destino(contexto):
    origem = dict(contexto['origem'])
    origem['cpf'] = formatar_documento(origem.get('cpf'))
    origem['cnpj'] = formatar_documento(origem.get('cnpj'))
    destino = dict(contexto['destino'])
    destino['cnpj'] = formatar_documento(destino.get('cnpj'))

    bloco_origem = _bloco_secao('DADOS DA ORIGEM DOS ANIMAIS', origem, [
        ('1', 'Produtor:', 'produtor_nome'),
        ('2', 'CPF:', 'cpf', 492, 'CNPJ:', 'cnpj', 535, 590, 594),
        ('2', 'Inscr. Estadual:', 'inscricao_estadual', 492, 'Cód. ERAS:', 'codigo_eras', 617, 709, 712),
        ('1', 'Propriedade:', 'propriedade_nome'),
        ('2', 'Município:', 'municipio', 649, 'CEP:', 'cep', 667, 709, 712),
    ])
    linha_municipio = ('2', 'Município:', 'municipio', 649, 'S.I.F.:', 'sif', 669, 725, 729)
    if contexto.get('tipo_saida') in ('TRANSFER', 'VENDA'):   # v2.2.0: S.I.F. e de frigorifico (so Abate)
        linha_municipio = ('1', 'Município:', 'municipio')
    bloco_destino = _bloco_secao('DADOS DO DESTINO DOS ANIMAIS', destino, [
        ('1', 'Nome:', 'frigorifico_nome'),
        ('1', 'Estabelecimento:', 'estabelecimento'),
        ('2', 'CNPJ:', 'cnpj', 472, 'Inscr. Estadual:', 'inscricao_estadual', 535, 662, 666),
        linha_municipio,
    ])
    return [bloco_origem, Spacer(1, 1.5), bloco_destino, Spacer(1, 3)]


# -------------------------------------------------------
# Grade de GTAs: ate 3 blocos GTA | Animais | Emissao por linha (cada bloco = cabecalho + valores)
# -------------------------------------------------------
def _grade_gtas(gtas):
    # Cabecalho GTA | Animais | Emissao so na 1a linha de blocos; as demais levam so os valores.
    itens = []
    passo = ALT_CAIXA + 1.5
    for linha_bloco, inicio in enumerate(range(0, len(gtas), 3)):
        y = passo * (linha_bloco + 1)
        for indice, gta in enumerate(gtas[inicio:inicio + 3]):
            base = 17 + indice * 308
            colunas = [(base, base + 119), (base + 122, base + 197), (base + 200, base + 304)]
            if linha_bloco == 0:
                for (x0, x1), texto in zip(colunas, ['GTA', 'Animais', 'Emissão']):
                    itens.append(_caixa(x0, x1, 0, texto, fonte='Helvetica-Bold', tam=8, alinha='c'))
            valores = [(str(gta['numero']), 'Helvetica-Bold', 'c'), (str(gta['qtde_animais']), 'Helvetica', 'r'), (str(gta['data_emissao']), 'Helvetica', 'c')]
            for (x0, x1), (texto, fonte, alinha) in zip(colunas, valores):
                itens.append(_caixa(x0, x1, y, texto, fonte=fonte, tam=8, alinha=alinha))
    linhas_de_blocos = (len(gtas) + 2) // 3
    return _Desenho(itens, passo * linhas_de_blocos + ALT_CAIXA + 3)


# -------------------------------------------------------
# Linha de totais: "Total Geral de Animais: [n]      Saida: [dd/mm/aaaa]"
# -------------------------------------------------------
def _linha_totais(total_animais, data_saida, rotulo_data):
    largura_rotulo_data = 105 if rotulo_data.startswith('Data') else 71
    itens = [
        _caixa(152, 366, 0, 'Total Geral de Animais:', rotulo=True, h=12.5, tam=9.5, alinha='c'),
        _caixa(370, 433, 0, str(total_animais), h=12.5, tam=9, fonte='Helvetica-Bold'),
        _caixa(623, 623 + largura_rotulo_data, 0, rotulo_data, rotulo=True, h=12.5, tam=9.5, alinha='c'),
        _caixa(629 + largura_rotulo_data, 760 + largura_rotulo_data, 0, str(data_saida), h=12.5, tam=9.5, fonte='Times-Bold'),
    ]
    return _Desenho(itens, 12.5)


def _topo(contexto, modelo_xx, rotulo_data):
    elementos = [_titulo(contexto['numero_comunicado'], modelo_xx), Spacer(1, 3)]
    elementos += _blocos_origem_destino(contexto)
    if contexto['gtas']:
        elementos.append(_grade_gtas(contexto['gtas']))
    elementos.append(Spacer(1, 12))
    elementos.append(_linha_totais(contexto['total_animais'], contexto['data_saida'], rotulo_data))
    elementos.append(Spacer(1, 2))
    return elementos


def _construir(elementos):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=PAGE_SIZE,
        leftMargin=MARGEM_H, rightMargin=MARGEM_H,
        topMargin=MARGEM_V_ANEXO, bottomMargin=MARGEM_V_ANEXO,
    )
    doc.build(elementos)
    buffer.seek(0)
    return buffer


# -------------------------------------------------------
# MODELO 1 - Anexo XX: grade Ind | SISBOV, 5 pares por linha (como a amostra)
# -------------------------------------------------------
def _grade_sisbov(lista_sisbov, fundo_cabecalho=None):
    larguras = [_x(46), _x(126)] * 5
    cabecalho = ['Ind', 'SISBOV'] * 5
    dados = [cabecalho]
    for inicio in range(0, len(lista_sisbov), 5):
        linha = []
        for deslocamento in range(5):
            posicao = inicio + deslocamento
            if posicao < len(lista_sisbov):
                linha += [str(posicao + 1), formatar_sisbov(lista_sisbov[posicao])]
            else:
                linha += ['', '']
        dados.append(linha)

    alturas = [14] + [12.5] * (len(dados) - 1)
    tabela = Table(dados, colWidths=larguras, rowHeights=alturas, repeatRows=1, hAlign='CENTER')
    estilo = [
        ('GRID', (0, 0), (-1, -1), 0.8, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 6.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        # v2.0.1: numeros dos Brincos estavam colados na linha de cima; desce o texto das linhas de dados
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 0),
    ]
    for par in range(5):
        estilo.append(('ALIGN', (par * 2, 1), (par * 2, -1), 'RIGHT'))
        estilo.append(('ALIGN', (par * 2 + 1, 1), (par * 2 + 1, -1), 'CENTER'))
    if fundo_cabecalho is not None:   # v2.0.2: Anexo XIX tem o cabecalho Ind | SISBOV cinza
        estilo.append(('BACKGROUND', (0, 0), (-1, 0), fundo_cabecalho))
    tabela.setStyle(TableStyle(estilo))
    return tabela


def gerar_pdf_anexo_xx(contexto):
    elementos = _topo(contexto, True, 'Data Saída:')
    elementos.append(_grade_sisbov(contexto['sisbov']))
    return _construir(elementos)


# -------------------------------------------------------
# Celulas da grade do XXI: codigo de barras (com os 16 digitos espacados embaixo) e QR Code
# -------------------------------------------------------
class _BarraTexto(Flowable):
    """Interleaved 2 of 5, 16 digitos (zero + SISBOV), com os digitos espacados embaixo (como na amostra)."""
    ALTURA = 34

    def __init__(self, sisbov, largura):
        super().__init__()
        self.valor = '0' + str(sisbov)
        self.largura = largura

    def wrap(self, largura, altura):
        return self.largura, self.ALTURA

    def _barras(self):
        largura_barra = 0.95
        barras = I2of5(self.valor, barWidth=largura_barra, barHeight=22, ratio=2.2, checksum=0, bearers=0, quiet=0)
        while barras.width > self.largura - 14 and largura_barra > 0.6:
            largura_barra -= 0.05
            barras = I2of5(self.valor, barWidth=largura_barra, barHeight=22, ratio=2.2, checksum=0, bearers=0, quiet=0)
        return barras

    def draw(self):
        barras = self._barras()
        x = (self.largura - barras.width) / 2
        barras.drawOn(self.canv, x, 10)
        texto = self.valor
        espaco = 3.2
        tam = 6.5
        largura_texto = stringWidth(texto, 'Helvetica', tam) + espaco * (len(texto) - 1)
        obj = self.canv.beginText()
        obj.setFont('Helvetica', tam)
        obj.setCharSpace(espaco)
        obj.setTextOrigin((self.largura - largura_texto) / 2, 2)
        obj.textOut(texto)
        self.canv.drawText(obj)


TAMANHO_QR = 44


class _QrTexto(Flowable):
    """QR Code do SISBOV (so o numero de 15 digitos) com o SISBOV escrito ao lado."""
    ALTURA = 50

    def __init__(self, sisbov, largura):
        super().__init__()
        self.sisbov = str(sisbov)
        self.largura = largura

    def wrap(self, largura, altura):
        return self.largura, self.ALTURA

    def draw(self):
        widget = QrCodeWidget(self.sisbov, barLevel='M')
        x0, y0, x1, y1 = widget.getBounds()
        desenho = Drawing(TAMANHO_QR, TAMANHO_QR, transform=[TAMANHO_QR / (x1 - x0), 0, 0, TAMANHO_QR / (y1 - y0), 0, 0])
        desenho.add(widget)
        x_qr = self.largura * 0.08
        renderPDF.draw(desenho, self.canv, x_qr, (self.ALTURA - TAMANHO_QR) / 2)
        texto = formatar_sisbov(self.sisbov)
        self.canv.setFont('Helvetica-Bold', 9)
        self.canv.setFillColor(colors.black)
        self.canv.drawString(x_qr + TAMANHO_QR + 8, self.ALTURA / 2 - 3, texto)


def _grade_dupla(lista_sisbov, titulo_coluna, classe_celula, altura_linha):
    """2 animais por linha: Ind | celula (barras ou QR), medidas da amostra do XXI."""
    larg_ind = _x(54)
    larg_cel_1 = _x(334)
    larg_cel_2 = _x(335)
    larg_ind_2 = _x(53)

    dados = [['Ind', titulo_coluna, 'Ind', titulo_coluna]]
    for inicio in range(0, len(lista_sisbov), 2):
        linha = []
        for deslocamento, larg_cel in ((0, larg_cel_1), (1, larg_cel_2)):
            posicao = inicio + deslocamento
            if posicao < len(lista_sisbov):
                linha += [str(posicao + 1), classe_celula(lista_sisbov[posicao], larg_cel)]
            else:
                linha += ['', '']
        dados.append(linha)

    alturas = [14] + [altura_linha] * (len(dados) - 1)
    tabela = Table(dados, colWidths=[larg_ind, larg_cel_1, larg_ind_2, larg_cel_2], rowHeights=alturas, repeatRows=1, hAlign='CENTER')
    tabela.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.8, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    return tabela


# -------------------------------------------------------
# MODELO 2 - Anexo XXI com codigo de barras
# -------------------------------------------------------
def gerar_pdf_anexo_xxi_barras(contexto):
    elementos = _topo(contexto, False, 'Saída:')
    elementos.append(_grade_dupla(contexto['sisbov'], 'Código Barras / Sisbov', _BarraTexto, 39))
    return _construir(elementos)


# -------------------------------------------------------
# MODELO 3 - Anexo XXI com QR Code (modelo Orion): mesmo desenho do XXI, QR no lugar das barras
# -------------------------------------------------------
def gerar_pdf_anexo_xxi_qrcode(contexto):
    elementos = _topo(contexto, False, 'Saída:')
    elementos.append(_grade_dupla(contexto['sisbov'], 'QR Code / Sisbov', _QrTexto, 52))
    return _construir(elementos)


# Modelos aceitos pelo router: chave da URL -> (funcao, sufixo do nome do arquivo)
MODELOS = {
    'xx':  (gerar_pdf_anexo_xx, 'anexo_xx'),
    'xxi': (gerar_pdf_anexo_xxi_barras, 'anexo_xxi_barras'),
    'qr':  (gerar_pdf_anexo_xxi_qrcode, 'anexo_xxi_qrcode'),
}

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_anexo_saida.py
# =========================================================
