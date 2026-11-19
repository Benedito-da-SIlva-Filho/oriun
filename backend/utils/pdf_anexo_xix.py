# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\pdf_anexo_xix.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-09-16 10:25 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO:       2.1.0
# v2.1.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Monta o PDF do "Anexo XIX - Formulario para Comunicado de Entrada" (vai para a Certificadora e o
#     Arquivo ERAS). Modulo PURO quanto a dados: recebe o dict "contexto" (montado por
#     backend/utils/comunicado_display.py::montar_contexto_anexo_xix) e devolve o PDF em memoria.
#     Chamado igual pela Impressao e pela Reimpressao.
#
#     v2.0.0 - REFEITO no visual do Magic (Sessao 101): todas as medidas (caixas, barras, grade, rodape) foram
#     tiradas do PDF real do Magic (Geras_Com_Entrada.pdf, vetorial: Comunicado 000011, Fazenda Nova Esperanca),
#     e as pecas sao as mesmas do Anexo de Saida (pdf_anexo_saida.py): caixinhas rotulo/valor, barras e
#     cabecalhos cinza (#F0F0F0), grade Ind | SISBOV em 5 pares, GTAs em ate 3 blocos por linha.
#
#     CPF e CNPJ do Produtor DESTINO: imprime so o que existe (so CPF, so CNPJ ou os dois), documento
#     principal do Produtor + o secundario da fazenda (documentos_produtor.py). A ORIGEM e um Parceiro, que
#     tem um documento so: 11 digitos = CPF, 14 = CNPJ.
#
#     Rodape fixo no pe da pagina, como no Magic: "Referente ao Comunicado Nro", "1a via Certificadora",
#     "2a via Arquivo ERAS", linha de assinatura e a nota da certificadora.
#
#     contexto (dict):
#         numero_comunicado (int)
#         destino: produtor_nome, cpf, cnpj, codigo_eras, propriedade_nome, municipio
#         origem:  produtor_nome, cpf, cnpj, propriedade_nome, municipio
#         gtas: lista de {numero, qtde_animais, data_emissao (str)}
#         total_animais (int), data_entrada (str dd/mm/aaaa), sisbov (lista, ja na ordem final)
#
#     v1.0.0/v1.1.0: Criacao e grade de GTAs em blocos (Sessao 054).
#     v2.0.0: Sessao 101 (20/10/2026, 18:50 -03) - visual do Magic + CPF/CNPJ + rodape fixo. REVERSAO: .bak_antes_visual_magic_s101
#     v2.0.1: Sessao 101 (20/10/2026, 19:00 -03) - Grade de GTAs: o cabecalho GTA | Animais | Emissao aparece so na 1a linha de blocos (a 2a linha, com GTAs 4 a 6, leva so os valores).  REVERSAO: .bak_antes_cabecalho_gta_s101
# =========================================================

from io import BytesIO

from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Spacer

from backend.utils.pdf_reportlab import LARGURA_UTIL, MARGEM_H, PAGE_SIZE
from backend.utils.pdf_anexo_saida import (
    MARGEM_V_ANEXO, _Desenho, _caixa, _grade_sisbov, formatar_documento,
)

CINZA = colors.Color(0.941176, 0.941176, 0.941176)   # #F0F0F0, o cinza das barras no Magic

# A amostra do Magic mede 550 pt entre as pontas da barra (x de 1,8 a 551,8). Tudo e escalado para a
# largura util do Orion: S em pt, e as colunas em "unidades" de 955 (a unidade do _Desenho).
S = LARGURA_UTIL / 550.0
U = 955.0 / 550.0


def _x(pt):
    return (pt - 1.8) * U


def _y(pt):
    return pt * S


def _it(x0, x1, y, h, texto='', fonte='Helvetica-Bold', tam=8, alinha='c', fundo=False, borda=True):
    item = {'x0': _x(x0), 'x1': _x(x1), 'y': _y(y), 'h': _y(h), 'texto': texto,
            'fonte': fonte, 'tam': tam * S, 'alinha': alinha, 'borda': borda}
    if fundo:
        item['fundo'] = True
        item['cor'] = CINZA
    return item


# -------------------------------------------------------
# Topo: titulo + DESTINO + ORIGEM (posicoes fixas, medidas na amostra; y = distancia do topo da pagina)
# -------------------------------------------------------
def _digitos(valor):
    return ''.join(c for c in str(valor or '') if c.isdecimal())


def _documentos_linha(dados):
    """(rotulo1, valor1, rotulo2, valor2): so CPF, so CNPJ ou os dois (CPF na 1a posicao)."""
    cpf = formatar_documento(dados.get('cpf'))
    cnpj = formatar_documento(dados.get('cnpj'))
    if cpf and cnpj:
        return 'CPF:', cpf, 'CNPJ:', cnpj
    if cnpj:
        return 'CNPJ:', cnpj, '', ''
    return 'CPF:', cpf, '', ''


def _linhas_estabelecimento(itens, y0, dados, com_eras):
    # linhas com 1 campo: rotulo 88,2-161,5 e valor 163,8-464,6; passo 17,3
    def linha1(y, rotulo, valor):
        itens.append(_it(88.2, 161.5, y, 15, rotulo, alinha='r'))
        itens.append(_it(163.8, 464.6, y, 15, valor))

    linha1(y0, 'Produtor:', dados.get('produtor_nome') or '')

    y = y0 + 17.3
    r1, v1, r2, v2 = _documentos_linha(dados)
    itens.append(_it(88.2, 161.5, y, 15, r1, alinha='r'))
    itens.append(_it(163.8, 274.6, y, 15, v1))
    if r2:
        itens.append(_it(318.6, 350.2, y, 15, r2, alinha='r'))
        itens.append(_it(353.2, 463.9, y, 15, v2))

    if com_eras:
        y += 17.3
        itens.append(_it(88.2, 161.5, y, 15, 'Cód. ERAS:', alinha='r'))
        itens.append(_it(163.8, 217.0, y, 15, str(dados.get('codigo_eras') or '')))

    y += 17.3
    linha1(y, 'Propriedade:', dados.get('propriedade_nome') or '')
    y += 17.3
    linha1(y, 'Municipio:', dados.get('municipio') or '')


def _topo(contexto):
    numero = f"{contexto['numero_comunicado']:06d}"
    itens = [
        _it(0, 553.6, 7.5, 19, 'ANEXO XIX', 'Times-Bold', 16, borda=False),
        _it(0, 553.6, 29, 14, 'FORMULÁRIO PARA COMUNICADO DE ENTRADA', 'Times-Bold', 12, borda=False),
        _it(430, 490.5, 16.9, 17.2, 'Nro:', 'Times-Bold', 14, alinha='r', borda=False),
        _it(493.6, 542.4, 16.9, 17.2, numero, 'Times-Bold', 16),
        _it(1.8, 551.8, 54.4, 17.2, 'DADOS DO ESTABELECIMENTO RURAL DESTINO', 'Times-Bold', 14, fundo=True),
    ]
    _linhas_estabelecimento(itens, 73.8, contexto['destino'], com_eras=True)
    itens.append(_it(1.8, 551.8, 166.0, 17.2, 'DADOS DO ESTABELECIMENTO ORIGEM', 'Times-Bold', 14, fundo=True))
    _linhas_estabelecimento(itens, 185.4, contexto['origem'], com_eras=False)
    return _Desenho(itens, _y(253.5))


# -------------------------------------------------------
# GTAs: ate 3 blocos GTA | Animais | Emissao por linha
# -------------------------------------------------------
def _grade_gtas(gtas):
    # Cabecalho GTA | Animais | Emissao so na 1a linha de blocos; as demais linhas levam so os valores.
    itens = []
    colunas = [(14.0, 80.9), (83.2, 125.5), (127.8, 188.2)]
    passo = 15.1
    for linha_bloco, inicio in enumerate(range(0, len(gtas), 3)):
        y = passo * (linha_bloco + 1)
        for indice, gta in enumerate(gtas[inicio:inicio + 3]):
            deslocamento = indice * 308 / U
            if linha_bloco == 0:
                for (x0, x1), texto in zip(colunas, ['GTA', 'Animais', 'Emissão']):
                    itens.append(_it(x0 + deslocamento, x1 + deslocamento, 0, 13.6, texto, fundo=True))
            valores = [(str(gta['numero']), 'Helvetica-Bold'), (str(gta['qtde_animais']), 'Helvetica-Bold'),
                       (str(gta['data_emissao']), 'Helvetica')]
            for (x0, x1), (texto, fonte) in zip(colunas, valores):
                itens.append(_it(x0 + deslocamento, x1 + deslocamento, y, 13.6, texto, fonte=fonte))
    linhas_de_blocos = (len(gtas) + 2) // 3
    return _Desenho(itens, _y(passo * linhas_de_blocos + 13.6))


# -------------------------------------------------------
# Total Geral de Animais | Data Entrada
# -------------------------------------------------------
def _linha_totais(total_animais, data_entrada):
    itens = [
        _it(67.3, 191.0, 0, 13.6, 'Total Geral de Animais:', 'Times-Bold', 11, fundo=True),
        _it(193.3, 229.9, 0, 13.6, str(total_animais), 'Times-Bold', 11, fundo=True),
        _it(333.7, 407.8, 0, 13.6, 'Data Entrada:', 'Times-Bold', 11, fundo=True),
        _it(410.0, 485.5, 0, 13.6, str(data_entrada), 'Times-Bold', 11, fundo=True),
    ]
    return _Desenho(itens, _y(13.6))


# -------------------------------------------------------
# Rodape fixo no pe da pagina (posicoes da amostra, medidas a partir do fundo da pagina)
# -------------------------------------------------------
SUBIR_RODAPE = 10   # pt acima da posicao do Magic, para nao ser cortado por impressoras com margem


def _rodape_factory(numero_comunicado):
    numero = f'{numero_comunicado:06d}'
    altura_pagina = PAGE_SIZE[1]

    def px(pt):
        return MARGEM_H + (pt - 1.8) * S

    def base(topo_pt, tam):
        return altura_pagina - (topo_pt + tam * 0.9) + SUBIR_RODAPE

    def desenhar(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.black)
        canvas.setStrokeColor(colors.black)
        canvas.setFont('Helvetica-Bold', 8 * S)
        canvas.drawString(px(24.5), base(685, 8), 'Referente ao Comunicado Nro')
        canvas.drawString(px(161.9), base(685, 8), numero)
        canvas.drawString(px(396.0), base(684, 8), '1ª via Certificadora')
        canvas.drawString(px(396.0), base(699, 8), '2ª via Arquivo ERAS')
        canvas.setLineWidth(0.72)
        y_linha = altura_pagina - 802.1 + SUBIR_RODAPE
        canvas.line(px(154.1), y_linha, px(398.9), y_linha)
        canvas.setFont('Helvetica-Bold', 7 * S)
        centro = px(276.5)
        canvas.drawCentredString(centro, base(810, 7), 'Data e Assinatura do Produtor Rural ou Responsável pela informação')
        canvas.drawCentredString(centro, base(821, 7), 'A certificadora deverá indicar a comprovação, com data, do recebimento deste documento.')
        canvas.restoreState()

    return desenhar


# -------------------------------------------------------
# Funcao publica
# -------------------------------------------------------
def gerar_pdf_anexo_xix(contexto):
    buffer = BytesIO()
    # a area util termina acima do rodape fixo ("Referente..." em y = 685 do topo, no Magic)
    margem_inferior = PAGE_SIZE[1] - 678 + SUBIR_RODAPE
    doc = SimpleDocTemplate(
        buffer, pagesize=PAGE_SIZE,
        leftMargin=MARGEM_H, rightMargin=MARGEM_H,
        topMargin=MARGEM_V_ANEXO, bottomMargin=margem_inferior,
    )

    elementos = [_topo(contexto), Spacer(1, _y(3.8))]
    if contexto['gtas']:
        elementos.append(_grade_gtas(contexto['gtas']))
    elementos.append(Spacer(1, _y(17.4)))
    elementos.append(_linha_totais(contexto['total_animais'], contexto['data_entrada']))
    elementos.append(Spacer(1, _y(2.3)))
    elementos.append(_grade_sisbov(contexto['sisbov'], fundo_cabecalho=CINZA))

    rodape = _rodape_factory(contexto['numero_comunicado'])
    doc.build(elementos, onFirstPage=rodape, onLaterPages=rodape)
    buffer.seek(0)
    return buffer

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_anexo_xix.py
# =========================================================
