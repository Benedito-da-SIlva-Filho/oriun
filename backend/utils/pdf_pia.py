# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\pdf_pia.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-25 10:55 -03
# ATUALIZADO EM: 2026-11-16 13:35 -03
# VERSAO: 2.0.1
# v2.0.1: Sessao 128 (2026-11-16 13:35 -03) - PIA de Nascimento (modelo 'IX') passa a imprimir ANEXO XXIII, numero oficial da PIA no Manual SISBOV v1.2 (o IX do manual e outro formulario). Modelo interno 'IX' mantido. REVERSAO: .bak_antes_s128_anexos.
#
# DESCRICAO:
#     Desenho do PDF da PIA - Anexo XXIII, "Formulario para
#     Planilha de Identificacao Individual de Animais" (documento
#     oficial que segue para a Certificadora/MAPA). Chamado por
#     backend/routers/pia_impressao.py nas 3 abas (Periodo, Manejo,
#     Comunicado) - o PDF e o mesmo, so muda o filtro.
#
#     CADA PAGINA E UMA PLANILHA COMPLETA (v1.3.0 - igual ao
#     legado, conferido por Benedito: a Certificadora recebe folhas
#     soltas, cada uma tem que valer sozinha):
#       - Cabecalho: LOGO do Fabricante (quando houver) | ANEXO
#         XXIII + subtitulo em UMA linha | caixa com o NUMERO da
#         PIA/Comunicado (so na aba Por Comunicado).
#       - Bloco "RAZAO SOCIAL DO FABRICANTE" e bloco "DADOS DA
#         IDENTIFICACAO DO PRODUTOR".
#       - Tabela com no maximo 25 ANIMAIS POR PAGINA: Numero
#         SISBOV | Manejo | Nascimento Mes/Ano | Idade Meses | Sexo
#         | Raca* | Motivo | Data de Identificacao. SISBOV com os
#         15 digitos corridos, SEM hifen (nao existe mais digito
#         verificador separado).
#       - Rodape do documento, SEMPRE na mesma posicao no pe da
#         folha: "* Consultar relacao de Racas" | "1a via
#         Encaminhar para Certificadora / 2a via Arquivo Eras da
#         Propriedade" + linha de assinatura + "A certificadora
#         devera indicar a comprovacao...".
#       - Linha final: "Impressao: dd/mm/aaaa hh:mm:ss" e
#         "Pag. X de Y - N de TOTAL animais" (N = acumulado ate a
#         pagina, TOTAL = todos os animais do arquivo).
#
#     UMA PIA POR FABRICANTE (decisao de Benedito, Sessao 080): o
#     documento e "do fabricante" - cada grupo recebido comeca em
#     PAGINA NOVA com o seu proprio cabecalho. Tudo num unico
#     arquivo.
#
#     LOGO (v1.3.0 - busca tolerante): o caminho gravado em
#     tb_1021.logo e procurado dentro de /static/ e de
#     /static/img/, com as extensoes .jpg, .jpeg e .png (o cadastro
#     real tinha 2 formatos de caminho e uma extensao trocada).
#     Nao achou: o PDF sai sem logo (nunca quebra) e o TERMINAL
#     avisa quais caminhos foram tentados.
#
#     v1.0.0: Criacao do modulo (Sessao 080, 25/09/2026, 10:55 -03).
#     v1.1.0: Sessao 080 (25/09/2026, 15:50 -03) - Caixa com o
#         NUMERO da PIA/Comunicado no canto superior direito (so na
#         aba Por Comunicado). Parametro opcional numero_pia.
#     v1.2.0: Sessao 080 (25/09/2026, 16:40 -03) - Rodape do legado
#         no fim de cada planilha + contagem "Pag. X de Y - N de
#         TOTAL animais" (classe TabelaPia + DocPia com
#         afterFlowable). Nota "Total de animais nesta planilha"
#         removida.
#     v1.3.0: Sessao 080 (25/09/2026, 17:15 -03) - Conferencia com
#         o PDF do legado (Benedito):
#           - 25 ANIMAIS POR PAGINA, fixos, e CABECALHO COMPLETO em
#             toda pagina (logo, titulo, numero, Fabricante e
#             Produtor) - cada folha e uma planilha completa.
#           - Rodape com ASSINATURA em TODAS as paginas, desenhado
#             no pe da folha pelo canvas (antes so no fim de cada
#             planilha) - funcao _desenhar_rodape_documento();
#             margem inferior aumentada para reservar o espaco.
#           - Fonte da tabela um pouco menor (7.2) e subtitulo em
#             UMA linha (fonte 7.4).
#           - Logo: busca tolerante (_caminho_logo - pasta, extensao
#             e maiusculas/minusculas) + aviso no terminal quando nao
#             encontra.
#     v1.4.0: Sessao 080 (25/09/2026, 17:30 -03) - BUG REAL no 1o
#         teste da v1.3.0 (Benedito): no projeto real os blocos de
#         Fabricante/Produtor (criar_bloco_dados) sao mais altos que
#         na simulacao - so cabiam 24 animais e o 25o "vazava" para
#         uma pagina nova com 1 animal so. Correcao que GARANTE as
#         25 linhas:
#           - ALTURA AUTOMATICA DAS LINHAS: antes de montar cada
#             pagina, o cabecalho e MEDIDO (wrap) e o espaco que
#             sobra ate o rodape e dividido por 25 - a tabela
#             sempre fecha a folha, sem vazar, mesmo que o
#             cabecalho cresca (NOVA funcao _altura_linha()). Linha
#             limitada entre 9 e 15 pt.
#           - Margem superior menor (cabecalho sobe) e logo menor.
#           - Fonte da tabela 7 (cabecalho 6.8), sem padding
#             vertical (a altura vem do calculo).
#     v1.5.0: Sessao 080 (25/09/2026, 17:37 -03) - BLOCOS COMPACTOS
#         (pedido de Benedito): os blocos "Razao Social do
#         Fabricante" e "Dados da Identificacao do Produtor" deixam
#         de usar criar_bloco_dados() (funcao COMPARTILHADA do
#         pdf_reportlab.py - Inventario, Comunicado etc. continuam
#         usando, SEM mudanca) e passam a usar a NOVA funcao local
#         _bloco_compacto(): mesmo visual (faixa laranja com o
#         titulo, rotulo cinza, valor em negrito, CEP/Cod. ERAS a
#         direita, borda), com linhas de 13 pt e fonte 8. O espaco
#         ganho vai para as linhas da tabela (calculo automatico da
#         v1.4.0, ate 15 pt) e para o respiro antes do rodape.
#         criar_bloco_dados deixa de ser importado aqui.
#     v1.5.1: Sessao 095 (13/10/2026, 11:23 -03) - o laranja da faixa deixa de ser escrito
#             direto aqui e passa a vir de COR_PRIMARIA (pdf_reportlab.py). A cor e a mesma;
#             so passa a acompanhar o padrao. REVERSAO: devolver .bak_antes_cor_padrao.
#     v2.0.0: Sessao 101 (20/10/2026, 20:30 -03) - REFEITO NO VISUAL DO MAGIC/GERAS (medidas tiradas dos PDFs
#         reais Geras_PIA.pdf = Anexo XXIII e Geras_Pia_Nascto.pdf = Anexo IX). Agora cada folha e desenhada
#         direto no canvas, com posicoes fixas (barras cinza #F0F0F0, caixinhas rotulo/valor, divisorias duplas).
#           - DOIS MODELOS: 'XXIII' (PIA de Entrada: Nascimento Mes/Ano, caixa com o numero do Comunicado) e
#             'IX' (PIA de Nascimento: titulo ANEXO IX, Nascimento com a data completa, sem caixa de numero).
#           - 28 ANIMAIS POR FOLHA (como no Magic; eram 25).
#           - SISBOV com hifen antes do digito final (como o Magic e os Anexos XIX/XX).
#           - CPF/CNPJ do Produtor: so CPF, so CNPJ ou os dois (chaves cpf/cnpj do dict produtor).
#           - Logo do fabricante no canto; sem logo (ou arquivo ilegivel) a folha sai sem logo.
#           - Mantidos: uma PIA por fabricante, cabecalho completo em toda folha, rodape fixo com assinatura,
#             "Impressao" e "Pag. X de Y - N de TOTAL animais" (linha pequena no fim da folha).
#           - gerar_pdf_pia(grupos, produtor, sufixo, numero_pia=None, modelo='XXIII'); _caminho_logo() continua
#             disponivel (usada tambem pela Notificacao de Nascimento).
#         REVERSAO: .bak_antes_geras_s101
# =========================================================

import os
from datetime import datetime
from io import BytesIO

from flask import current_app, send_file
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas as canvas_reportlab

from backend.utils.pdf_reportlab import LARGURA_UTIL, MARGEM_H, PAGE_SIZE
from backend.utils.pdf_anexo_saida import formatar_documento, formatar_sisbov


# -------------------------------------------------------
# Medidas do Magic (v2.0.0). Tudo em pontos da AMOSTRA (largura 568,7 entre as pontas das barras, a partir
# de x = 3,2; y = distancia do topo da folha) e convertido por S para a largura util do Orion.
# -------------------------------------------------------
ANIMAIS_POR_PAGINA = 28            # a planilha do Magic traz 28 linhas por folha
EXTENSOES_LOGO = ('.jpg', '.jpeg', '.png')

S = LARGURA_UTIL / 568.7
X0_AMOSTRA = 3.2
TOPO_FOLHA = 24                    # margem de cima (pt reais)
CINZA = colors.Color(0.941176, 0.941176, 0.941176)

ALT_CAIXA = 12.1
LOGO_L, LOGO_A = 136.8, 50.4
Y_LINHA_TABELA = 286.6             # fim do cabecalho cinza da tabela
ALT_CABECALHO = 33.9
ALT_LINHA = 15.07

# Colunas da tabela (largura em pt da amostra) e rotulos, por modelo
MODELOS = {
    'XXIII': {
        'titulo': 'ANEXO XXIII',
        'larguras': [88.95, 43.2, 57.6, 36.0, 46.8, 36.0, 79.2, 71.65],
        'cabecalho': [['Número SISBOV'], ['Manejo'], ['Nascimento', 'Mês/Ano'], ['Idade', 'Meses'],
                      ['Sexo'], ['Raça*'], ['Motivo'], ['Data', 'de Identificação']],
        'x_racas': 69.8, 'x_vias': 360.0,
    },
    'IX': {
        'titulo': 'ANEXO XXIII',
        'larguras': [103.7, 46.8, 72.0, 36.0, 43.2, 36.0, 68.4, 79.1],
        'cabecalho': [['Número SISBOV'], ['Manejo'], ['Nascimento'], ['Idade', 'Meses'],
                      ['Sexo'], ['Raça*'], ['Motivo'], ['Data', 'de Identificação']],
        'x_racas': 56.0, 'x_vias': 408.2,
    },
}
SUBTITULO = 'FORMULÁRIO PARA PLANILHA DE IDENTIFICAÇÃO INDIVIDUAL DE ANIMAIS'


def _px(pt):
    return MARGEM_H + (pt - X0_AMOSTRA) * S


def _py(topo_pt):
    """y do canvas (a partir do pe) de um ponto a 'topo_pt' do topo da folha da amostra."""
    return PAGE_SIZE[1] - TOPO_FOLHA - topo_pt * S


# -------------------------------------------------------
# Logo do Fabricante - busca tolerante (v1.3.0). Devolve o caminho
# do arquivo ou None (avisando no terminal o que foi tentado).
# -------------------------------------------------------
def _caminho_logo(caminho_gravado):
    if not caminho_gravado:
        return None

    relativo = caminho_gravado.replace('\\', '/').lstrip('/')
    if relativo.lower().startswith('static/'):
        relativo = relativo[len('static/'):]
    base_sem_ext, _ = os.path.splitext(relativo)

    pasta_static = current_app.static_folder
    tentativas = []
    for prefixo in ('', 'img/'):
        if prefixo and relativo.lower().startswith(prefixo):
            continue
        tentativas.append(os.path.join(pasta_static, prefixo + relativo))
        for extensao in EXTENSOES_LOGO:
            tentativas.append(os.path.join(pasta_static, prefixo + base_sem_ext + extensao))

    for caminho in tentativas:
        if os.path.isfile(caminho):
            return caminho
        # Mesmo nome ignorando maiusculas/minusculas (ex.: cadastro
        # "allflex" x arquivo "Allflex.jpg") - servidor que diferencia.
        pasta, nome = os.path.split(caminho)
        if os.path.isdir(pasta):
            for arquivo in os.listdir(pasta):
                if arquivo.lower() == nome.lower():
                    return os.path.join(pasta, arquivo)

    print(f'[PIA] Logo do fabricante NAO encontrada para "{caminho_gravado}". Tentado: {tentativas}')
    return None


# -------------------------------------------------------
# Pecas de desenho
# -------------------------------------------------------
def _texto_ou_traco(valor):
    return valor if valor else '-'


def _caixa(c, x0, x1, y, texto='', fonte='Helvetica-Bold', tam=8, alinha='c', h=ALT_CAIXA, fundo=False, borda=True):
    """Caixa (coordenadas da amostra) com texto centrado na vertical; texto encolhe se nao couber."""
    x = _px(x0)
    largura = (x1 - x0) * S
    altura = h * S
    base = _py(y + h)
    if borda or fundo:
        c.setLineWidth(0.72)
        c.setStrokeColor(colors.black)
        c.setFillColor(CINZA if fundo else colors.white)
        c.rect(x, base, largura, altura, stroke=1 if borda else 0, fill=1 if fundo else 0)
    texto = str(texto or '')
    if not texto:
        return
    tamanho = tam * S
    while tamanho > 5 and stringWidth(texto, fonte, tamanho) > largura - 4:
        tamanho -= 0.25
    c.setFillColor(colors.black)
    c.setFont(fonte, tamanho)
    y_texto = base + (altura - tamanho * 0.72) / 2
    if alinha == 'c':
        c.drawCentredString(x + largura / 2, y_texto, texto)
    elif alinha == 'r':
        c.drawRightString(x + largura - 3, y_texto, texto)
    else:
        c.drawString(x + 3, y_texto, texto)


def _documentos_produtor(produtor):
    """(rotulo, valor, tem_dois): so CPF, so CNPJ ou os dois (v2.0.0). Sem as chaves cpf/cnpj, cai no
    campo antigo cpf_cnpj."""
    if 'cpf' in produtor or 'cnpj' in produtor:
        cpf = formatar_documento(produtor.get('cpf'))
        cnpj = formatar_documento(produtor.get('cnpj'))
        if cpf and cnpj:
            return 'CPF/CNPJ:', f'{cpf}   /   {cnpj}', True
        if cnpj:
            return 'CNPJ:', cnpj, False
        return 'CPF:', cpf, False
    return 'CNPJ/CPF:', formatar_documento(produtor.get('cpf_cnpj')), False


def _cabecalho(c, modelo, fab, produtor, numero_pia):
    cfg = MODELOS[modelo]

    # logo (canto superior esquerdo) - sem logo o formulario sai sem logo
    caminho = _caminho_logo(fab.get('logo'))
    if caminho:
        try:
            c.drawImage(caminho, _px(X0_AMOSTRA), _py(LOGO_A), width=LOGO_L * S, height=LOGO_A * S,
                        preserveAspectRatio=True, anchor='nw', mask='auto')
        except Exception as erro:
            print(f'[PIA] Logo do fabricante ilegivel ({caminho}): {erro}')

    # titulo e numero
    _caixa(c, 3.2, 571.9, 7.5, cfg['titulo'], 'Times-Bold', 14, borda=False, h=18)
    _caixa(c, 3.2, 571.9, 30.5, SUBTITULO, 'Helvetica-Bold', 8, borda=False, h=11)
    if numero_pia is not None and modelo == 'XXIII':
        _caixa(c, 501.5, 569.8, 16.2, f'{int(numero_pia):06d}', 'Helvetica-BoldOblique', 22, h=25.1)

    # ---- fabricante ----
    _caixa(c, 3.2, 571.9, 58.0, 'RAZÃO SOCIAL DO FABRICANTE', 'Times-Bold', 12, fundo=True, h=17.1)
    cidade_fab = f'{_texto_ou_traco(fab.get("cidade"))} / {_texto_ou_traco(fab.get("uf"))}'
    linhas = [
        (77.4, 'Fabricante:', _texto_ou_traco(fab.get('nome')), 482.6),
        (92.5, 'Endereço:', _texto_ou_traco(fab.get('endereco')), 482.6),
        (107.6, 'Compl.:', _texto_ou_traco(fab.get('complemento')), 482.6),
        (122.8, 'Bairro:', _texto_ou_traco(fab.get('bairro')), 415.0),
        (137.9, 'Cidade:', cidade_fab, 415.0),
    ]
    for y, rotulo, valor, x1 in linhas:
        _caixa(c, 108.4, 179.5, y, rotulo, alinha='r')
        _caixa(c, 181.8, x1, y, valor)
    _caixa(c, 422.3, 482.6, 137.9, str(fab.get('cep') or '-'))

    # ---- produtor ----
    _caixa(c, 4.7, 573.4, 156.6, 'DADOS DA IDENTIFICAÇÃO DO PRODUTOR', 'Times-Bold', 12, fundo=True, h=17.2)
    _caixa(c, 108.4, 179.5, 176.0, 'Produtor:', alinha='r')
    _caixa(c, 181.8, 482.6, 176.0, _texto_ou_traco(produtor.get('nome')))
    rotulo_doc, valor_doc, dois = _documentos_produtor(produtor)
    _caixa(c, 108.4, 179.5, 190.4, rotulo_doc, alinha='r')
    _caixa(c, 181.8, 361.0 if dois else 302.6, 190.4, valor_doc or '-')
    _caixa(c, 364.7, 421.4, 190.4, 'Cód. ERAS', alinha='r')
    _caixa(c, 425.9, 482.6, 190.4, str(produtor.get('codigo_eras') or '-'))
    _caixa(c, 108.4, 179.5, 204.8, 'Propriedade:', alinha='r')
    _caixa(c, 181.8, 482.6, 204.8, _texto_ou_traco(produtor.get('propriedade')))
    _caixa(c, 108.4, 179.5, 219.2, 'Endereço:', alinha='r')
    _caixa(c, 181.8, 482.6, 219.2, _texto_ou_traco(produtor.get('endereco')))
    _caixa(c, 108.4, 179.5, 233.6, 'Cidade:', alinha='r')
    _caixa(c, 181.8, 397.0, 233.6, _texto_ou_traco(produtor.get('cidade')))
    _caixa(c, 425.9, 482.6, 233.6, str(produtor.get('cep') or '-'))


def _tabela(c, modelo, animais):
    cfg = MODELOS[modelo]
    larguras = cfg['larguras']
    largura_total = sum(larguras)
    x_ini = 288.0 - largura_total / 2          # centrada na folha da amostra
    y_topo = 252.4
    y_fim = Y_LINHA_TABELA + ALT_LINHA * len(animais)
    x_fim = x_ini + largura_total

    # faixa cinza do cabecalho + moldura
    c.setLineWidth(0.72)
    c.setStrokeColor(colors.black)
    c.setFillColor(CINZA)
    c.rect(_px(x_ini), _py(Y_LINHA_TABELA), largura_total * S, (Y_LINHA_TABELA - y_topo) * S, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.rect(_px(x_ini), _py(y_fim), largura_total * S, (y_fim - Y_LINHA_TABELA) * S, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.rect(_px(x_ini), _py(y_fim), largura_total * S, (y_fim - y_topo) * S, stroke=1, fill=0)
    c.line(_px(x_ini), _py(Y_LINHA_TABELA), _px(x_fim), _py(Y_LINHA_TABELA))

    # divisorias verticais duplas (como no Magic)
    x = x_ini
    limites = []
    for largura in larguras:
        limites.append((x, x + largura))
        x += largura
    for x_div in [lim[1] for lim in limites[:-1]]:
        for deslocamento in (-1.05, 1.05):
            c.line(_px(x_div + deslocamento), _py(y_topo), _px(x_div + deslocamento), _py(y_fim))

    # cabecalho
    c.setFillColor(colors.black)
    for (xa, xb), linhas in zip(limites, cfg['cabecalho']):
        centro = _px((xa + xb) / 2)
        c.setFont('Helvetica-Bold', 8 * S)
        if len(linhas) == 1:
            c.drawCentredString(centro, _py(269.65) - 8 * S * 0.36, linhas[0])
        else:
            c.drawCentredString(centro, _py(258.1) - 8 * S * 0.36, linhas[0])
            c.drawCentredString(centro, _py(267.7) - 8 * S * 0.36, linhas[1])

    # linhas
    campo_nasc = 'nascimento_mes_ano' if modelo == 'XXIII' else 'nascimento_data'
    for i, a in enumerate(animais):
        y_meio = Y_LINHA_TABELA + ALT_LINHA * (i + 0.5)
        valores = [
            (formatar_sisbov(a.get('sisbov')), 8), (a.get('manejo') or '', 8), (a.get(campo_nasc) or '', 8),
            (a.get('idade_meses') or '', 8), (a.get('sexo') or '', 8), (a.get('raca_codigo') or '', 8),
            (a.get('motivo') or '', 7), (a.get('data_identificacao') or '', 8),
        ]
        for (xa, xb), (texto, tam) in zip(limites, valores):
            if not texto:
                continue
            tamanho = tam * S
            while tamanho > 5 and stringWidth(texto, 'Helvetica-Bold', tamanho) > (xb - xa) * S - 4:
                tamanho -= 0.25
            c.setFont('Helvetica-Bold', tamanho)
            c.drawCentredString(_px((xa + xb) / 2), _py(y_meio) - tamanho * 0.36, texto)


def _rodape(c, modelo, texto_impressao, pagina, total_paginas, acumulado, total_animais):
    cfg = MODELOS[modelo]
    c.setFillColor(colors.black)
    c.setStrokeColor(colors.black)
    c.setFont('Helvetica-Bold', 7 * S)
    c.drawString(_px(cfg['x_racas']), _py(721.8 + 6), '* Consultar relação de Raças')
    c.setFont('Helvetica-Bold', 8 * S)
    c.drawString(_px(cfg['x_vias']), _py(720.7 + 7), '1º via Encaminhar para Certificadora')
    c.drawString(_px(cfg['x_vias']), _py(735.1 + 7), '2ª via Arquivo Eras da Propriedade')
    c.setLineWidth(0.72)
    c.line(_px(166.3), _py(812.2), _px(399.6), _py(812.2))
    c.setFont('Helvetica-Bold', 7 * S)
    centro = _px(288.0)
    c.drawCentredString(centro, _py(817.3 + 6), 'Data e assinatura do produtor rural ou responsável pela informação')
    c.drawCentredString(centro, _py(828.4 + 6), 'A certificadora deverá indicar a comprovação, com data, do recebimento deste documento.')

    # linha pequena no fim da folha: impressao e contagem (igual a v1.2.0)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#666666'))
    c.drawString(MARGEM_H, 16, texto_impressao)
    c.setFont('Helvetica-Bold', 8)
    texto = f'Pág. {pagina} de {total_paginas}'
    if total_animais:
        texto += f'  —  {acumulado} de {total_animais} animais'
    c.drawRightString(PAGE_SIZE[0] - MARGEM_H, 16, texto)


# -------------------------------------------------------
# Monta o PDF. grupos = lista de {'fabricante': {...}, 'animais': [...]} (1 grupo por Fabricante).
# produtor = dict do bloco "Dados da Identificacao do Produtor". numero_pia = so na aba Comunicado.
# modelo = 'XXIII' (Entrada) ou 'IX' (Nascimento). Cada pagina: cabecalho completo + ate 28 animais.
# -------------------------------------------------------
def montar_pdf_pia(grupos, produtor, numero_pia=None, modelo='XXIII'):
    if modelo not in MODELOS:
        modelo = 'XXIII'
    paginas = []
    for grupo in grupos:
        animais = grupo['animais']
        for i in range(0, len(animais), ANIMAIS_POR_PAGINA):
            paginas.append((grupo['fabricante'], animais[i:i + ANIMAIS_POR_PAGINA]))
    total_animais = sum(len(g['animais']) for g in grupos)
    texto_impressao = f'Impressão: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'

    buffer = BytesIO()
    c = canvas_reportlab.Canvas(buffer, pagesize=PAGE_SIZE)
    c.setTitle(f'PIA - Anexo {modelo}')
    acumulado = 0
    for numero, (fab, animais) in enumerate(paginas, start=1):
        acumulado += len(animais)
        _cabecalho(c, modelo, fab, produtor, numero_pia)
        _tabela(c, modelo, animais)
        _rodape(c, modelo, texto_impressao, numero, len(paginas), acumulado, total_animais)
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def gerar_pdf_pia(grupos, produtor, sufixo_nome, numero_pia=None, modelo='XXIII'):
    buffer = montar_pdf_pia(grupos, produtor, numero_pia, modelo)
    nome_propriedade = (produtor.get('propriedade') or 'Propriedade').replace(' ', '_')
    nome_arquivo = f'PIA_{nome_propriedade}_{sufixo_nome}.pdf'
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_pia.py
# =========================================================
