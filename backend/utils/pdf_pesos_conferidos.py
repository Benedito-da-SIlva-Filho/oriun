# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\pdf_pesos_conferidos.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-04 18:30 -03
# ATUALIZADO EM: 2026-11-04 18:30 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     PDF "Relatorio de Conferencias do dia" dos Pesos, NO VISUAL DO MAGIC/GERAS (A4 retrato). So desenha: nao acessa o
#     banco. Recebe um dict de contexto montado por backend/routers/pesos_consulta.py e devolve um BytesIO para send_file().
#
#     Layout (amostra do Magic, 04/11/2026): titulo em duas linhas, "Impressao", barra DADOS DA ORIGEM DOS ANIMAIS
#     (Produtor, CPF/CNPJ, Inscr. Estadual, Produtor Rural, Propriedade, Municipio/UF/CEP), caixa Conferencia + Qtde
#     Animais (REAL), tabela Indice | Codigo SISBOV | Manejo | Sexo | Nascimento | Idade em Meses | Raca | Elementos |
#     Peso, e no fim o quadro Sexo x faixas de idade (quantidade) + Total + Peso por sexo, com as caixas Total (peso),
#     Media e Geral (quantidade). Sem Ganho/GMD (decisao do Benedito, 04/11/2026). Numeros no formato brasileiro.
#
#     Chaves do contexto: data (dd/mm/aaaa), gerado_em_completo, produtor, cpf, cnpj, inscricao_estadual, codigo_eras,
#     propriedade, municipio, uf, cep, animais [{sisbov, manejo, sexo, nascimento, faixa, raca, elemento, peso}],
#     faixas [descricoes, na ordem], resumo {FEMEA/MACHO: {'qtd': [por faixa], 'total': n, 'peso': kg}}, peso_total,
#     peso_medio, total.
#
#     v1.0.0: Criacao (Sessao 114, 04/11/2026, 18:30 -03). Pecas reaproveitadas do Nascimentos por Periodo (_it, _Desenho,
#             escala S). REVERSAO: remover este arquivo.
# =========================================================

from io import BytesIO

from reportlab.lib import colors
from reportlab.platypus import KeepTogether, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.utils import pdf_reportlab as _rl
from backend.utils.pdf_anexo_saida import MARGEM_V_ANEXO, _Desenho, formatar_sisbov
from backend.utils.pdf_anexo_xix import CINZA as CINZA_MAGIC, S, _documentos_linha, _it, _y

# Colunas da tabela (pt da amostra, escaladas por S): Indice, SISBOV, Manejo, Sexo, Nascimento, Idade, Raca, Elementos, Peso
LARGURAS = [32.3, 131.9, 39.2, 39.2, 58.8, 85.8, 30.5, 59.3, 39.7]
ROTULOS = ['Indice', 'Código SISBOV', 'Manejo', 'Sexo', 'Nascimento', 'Idade em Meses', 'Raça', 'Elementos', 'Peso']
ALTURA_CABECALHO = 14.4
ALTURA_LINHA = 17.9


def _num(valor, casas=2):
    if valor is None:
        return ''
    texto = f'{float(valor):,.{casas}f}'
    return texto.replace(',', '#').replace('.', ',').replace('#', '.')


# -------------------------------------------------------
# Topo: titulo, impressao, DADOS DA ORIGEM e caixa Conferencia / Qtde Animais (y = distancia do topo, em pt da amostra)
# -------------------------------------------------------
def _topo(ctx):
    itens = [
        _it(0, 553.6, 4.0, 16.0, 'RELATÓRIO DE CONFERÊNCIAS', 'Times-Bold', 15, borda=False),
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

    y += passo + 2.0   # caixa Conferencia | data | Qtde Animais | n
    itens += [
        _it(121.0, 204.6, y, 13.6, 'Conferência', 'Times-Bold', 11, fundo=True),
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
            f'{i:04d}', formatar_sisbov(a.get('sisbov')), a.get('manejo') or '', a.get('sexo') or '',
            a.get('nascimento') or '', a.get('faixa') or '', a.get('raca') or '', a.get('elemento') or '',
            _num(a.get('peso')),
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
        ('FONTNAME', (1, 1), (1, -1), 'Times-Bold'), ('FONTSIZE', (1, 1), (1, -1), 9.5 * S),
        ('FONTNAME', (3, 1), (3, -1), 'Helvetica-Bold'), ('FONTSIZE', (3, 1), (3, -1), 6.5 * S),
        ('FONTNAME', (4, 1), (5, -1), 'Helvetica-Bold'), ('FONTSIZE', (4, 1), (5, -1), 6.5 * S),
    ]))
    return tabela


# -------------------------------------------------------
# Quadro final: Sexo x faixas + Total + Peso por sexo, e as caixas Total / Media / Geral
# -------------------------------------------------------
def _quadro_final(ctx):
    faixas = list(ctx.get('faixas') or [])
    resumo = ctx.get('resumo') or {}
    n = max(len(faixas), 1)
    folga = 1.3
    larg_sexo, larg_total, larg_peso, larg_caixa = 42.6, 52.5, 49.0, 54.2
    reservado = larg_sexo + larg_total + larg_peso + 3 * larg_caixa + (n + 6) * folga + 8.0
    larg_faixa = min(52.5, (550.0 - reservado) / n)

    topo_cab, alt_cab = 0.0, 13.8
    y_fem, y_mac, alt_lin = 15.6, 30.2, 13.2
    itens = []

    def caixa(x0, largura, y, h, texto, fonte='Times-Bold', tam=10, fundo=False):
        itens.append(_it(x0, x0 + largura, y, h, texto, fonte, tam, fundo=fundo))

    x = 0.0
    caixa(x, larg_sexo, topo_cab, alt_cab, 'Sexo', tam=10)
    caixa(x, larg_sexo, y_fem, alt_lin, 'Fêmeas')
    caixa(x, larg_sexo, y_mac, alt_lin, 'Machos')
    x += larg_sexo + folga
    for i, nome in enumerate(faixas):
        caixa(x, larg_faixa, topo_cab, alt_cab, nome, tam=10)
        for chave, y in (('FEMEA', y_fem), ('MACHO', y_mac)):
            qtd = (resumo.get(chave) or {}).get('qtd') or []
            caixa(x, larg_faixa, y, alt_lin, str(qtd[i] if i < len(qtd) else 0))
        x += larg_faixa + folga
    caixa(x, larg_total, topo_cab, alt_cab, 'Total', tam=10)
    caixa(x, larg_total, y_fem, alt_lin, str((resumo.get('FEMEA') or {}).get('total', 0)))
    caixa(x, larg_total, y_mac, alt_lin, str((resumo.get('MACHO') or {}).get('total', 0)))
    x += larg_total + folga
    caixa(x, larg_peso, topo_cab, alt_cab, 'Peso', tam=10)
    caixa(x, larg_peso, y_fem, alt_lin, _num((resumo.get('FEMEA') or {}).get('peso', 0)))
    caixa(x, larg_peso, y_mac, alt_lin, _num((resumo.get('MACHO') or {}).get('peso', 0)))
    x += larg_peso + 6.0
    for rotulo, valor in (('Total', _num(ctx.get('peso_total'))), ('Média', _num(ctx.get('peso_medio'))),
                          ('Geral', str(ctx.get('total', 0)))):
        caixa(x, larg_caixa, 0.0, 14.0, rotulo, tam=12)
        caixa(x, larg_caixa, 15.6, 27.8, valor, tam=11)
        x += larg_caixa + folga
    return _Desenho(itens, _y(43.6))


def _rodape_factory(ctx):
    def desenhar(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(_rl.MARGEM_H, 18, f"Relatório de Conferências — {ctx.get('data', '')} — gerado pela plataforma Orion SISBOV em {ctx.get('gerado_em_completo', '')}")
        canvas.drawRightString(_rl.PAGE_SIZE[0] - _rl.MARGEM_H, 18, f'Página {doc.page}')
        canvas.restoreState()
    return desenhar


def gerar_pdf_pesos_conferidos(ctx):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=_rl.PAGE_SIZE,
        leftMargin=_rl.MARGEM_H, rightMargin=_rl.MARGEM_H, topMargin=MARGEM_V_ANEXO, bottomMargin=34,
        title='Relatório de Conferências', author='Orion SISBOV',
    )
    historia = [_topo(ctx), Spacer(1, _y(6)), _tabela_animais(ctx.get('animais') or []), Spacer(1, _y(8)),
                KeepTogether([_quadro_final(ctx)])]
    rodape = _rodape_factory(ctx)
    doc.build(historia, onFirstPage=rodape, onLaterPages=rodape)
    buffer.seek(0)
    return buffer

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_pesos_conferidos.py
# =========================================================
