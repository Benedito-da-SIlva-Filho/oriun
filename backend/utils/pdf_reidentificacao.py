# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\pdf_reidentificacao.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-11 12:40 -03
# ATUALIZADO EM: 2026-11-16 13:35 -03
# VERSAO: 1.2.1
# v1.2.1: Sessao 128 (2026-11-16 13:35 -03) - titulo passa a trazer ANEXO XXIV (numero oficial no Manual SISBOV v1.2). REVERSAO: .bak_antes_s128_anexos.
#
# DESCRICAO:
#     PDF "REIDENTIFICACAO DE ANIMAIS" (Notificacao a Certificadora), no modelo do formulario do Magic ("Reidentificacao Notificacao.pdf"):
#     titulo, Data Solicitacao + Nro do Pedido, texto da declaracao (IN 17, cap. III, art. 7o, par. V), DADOS DE IDENTIFICACAO DO PRODUTOR,
#     DADOS DE IDENTIFICACAO DA PROPRIEDADE, "Relacao dos Codigos para serem Baixados" (Cod. SISBOV - Saida / Cod. SISBOV - Entrada, um
#     animal por linha, com a data de cada um) e linhas de assinatura. So desenha: nao acessa o banco. Recebe um dict de contexto montado por
#     backend/routers/reidentificacao_consulta.py e devolve um BytesIO para send_file().
#
#     Chaves do contexto: data_solicitacao (dd/mm/aaaa), nro_pedido (6 digitos), gerado_em_completo, produtor, cpf, cnpj, endereco,
#     complemento, bairro, municipio, uf, cep, email, fone, celular, propriedade, codigo_eras, inscricao_estadual, contato_propriedade,
#     email_propriedade, local_data (ex.: "Aracatuba, 11/11/2026"), itens [{sisbov_antigo, sisbov_novo}].
#
#     v1.2.0: Sessao 121 (2026-11-11 20:10 -03) - Cabecalho PADRAO do Orion (o mesmo do Anexo XIX): titulo + Nro + barra 'DADOS DO ESTABELECIMENTO RURAL' (Produtor, CPF/CNPJ, Cod. ERAS, Propriedade, Municipio). Saem do corpo os quadros de endereco/contato do formulario antigo. Reaproveita _it/_linhas_estabelecimento do pdf_anexo_xix.py. REVERSAO: .bak_antes_s121_cabecalho.
#     v1.1.0: Sessao 121 (2026-11-11 18:40 -03) - Um animal por linha com a coluna 'Data da Reidentificação' (cada animal tem a sua data; a Notificacao junta lancamentos de dias diferentes). itens ganha 'data' (dd/mm/aaaa). REVERSAO: .bak_antes_s121_pendentes.
#     v1.0.0: Criacao (Sessao 121, 11/11/2026, 12:40 -03). REVERSAO: remover este arquivo.
# =========================================================

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.utils import pdf_reportlab as _rl
from backend.utils.pdf_anexo_saida import MARGEM_V_ANEXO, _Desenho, formatar_sisbov
from backend.utils.pdf_anexo_xix import _it, _linhas_estabelecimento, _y

_UNID = ['', 'UM', 'DOIS', 'TRÊS', 'QUATRO', 'CINCO', 'SEIS', 'SETE', 'OITO', 'NOVE', 'DEZ', 'ONZE', 'DOZE', 'TREZE', 'CATORZE',
         'QUINZE', 'DEZESSEIS', 'DEZESSETE', 'DEZOITO', 'DEZENOVE']
_DEZ = ['', '', 'VINTE', 'TRINTA', 'QUARENTA', 'CINQUENTA', 'SESSENTA', 'SETENTA', 'OITENTA', 'NOVENTA']
_CEM = ['', 'CENTO', 'DUZENTOS', 'TREZENTOS', 'QUATROCENTOS', 'QUINHENTOS', 'SEISCENTOS', 'SETECENTOS', 'OITOCENTOS', 'NOVECENTOS']


def _extenso(n):
    """Numero por extenso (1 a 999), em maiusculas. Acima disso devolve so os algarismos."""
    n = int(n)
    if n <= 0 or n > 999:
        return str(n)
    if n == 100:
        return 'CEM'
    partes = []
    c, resto = divmod(n, 100)
    if c:
        partes.append(_CEM[c])
    if resto:
        if resto < 20:
            partes.append(_UNID[resto])
        else:
            d, u = divmod(resto, 10)
            partes.append(_DEZ[d] + (' E ' + _UNID[u] if u else ''))
    return ' E '.join(partes)


def _fmt_doc(cpf, cnpj):
    if cnpj:
        return f'CNPJ.: {cnpj}'
    if cpf:
        return f'CPF.: {cpf}'
    return 'CPF.:'


def _topo(ctx):
    """Cabecalho padrao do Orion (igual ao Anexo XIX): titulo, Nro e a barra do estabelecimento rural."""
    municipio = ' / '.join(t for t in (ctx.get('municipio') or '', ctx.get('uf') or '') if t)
    dados = {'produtor_nome': ctx.get('produtor') or '', 'cpf': ctx.get('cpf'), 'cnpj': ctx.get('cnpj'),
             'codigo_eras': ctx.get('codigo_eras'), 'propriedade_nome': ctx.get('propriedade') or '', 'municipio': municipio}
    itens = [
        _it(0, 553.6, 7.5, 19, 'ANEXO XXIV - REIDENTIFICAÇÃO DE ANIMAIS', 'Times-Bold', 16, borda=False),
        _it(0, 553.6, 29, 14, f"Data da Solicitação: {ctx.get('data_solicitacao', '')}", 'Times-Bold', 12, borda=False),
        _it(430, 490.5, 16.9, 17.2, 'Nro:', 'Times-Bold', 14, alinha='r', borda=False),
        _it(493.6, 542.4, 16.9, 17.2, str(ctx.get('nro_pedido', '')), 'Times-Bold', 16),
        _it(1.8, 551.8, 54.4, 17.2, 'DADOS DO ESTABELECIMENTO RURAL', 'Times-Bold', 14, fundo=True),
    ]
    _linhas_estabelecimento(itens, 73.8, dados, com_eras=True)
    return _Desenho(itens, _y(158.0))


def _tabela_codigos(itens):
    """Um animal por linha: Cod.SISBOV - Saida | Cod. SISBOV - Entrada | Data da Reidentificacao."""
    dados = [['Cód.SISBOV - Saída', 'Cód. SISBOV - Entrada', 'Data da Reidentificação']]
    for it in itens:
        dados.append([formatar_sisbov(it.get('sisbov_antigo')), formatar_sisbov(it.get('sisbov_novo')), it.get('data') or ''])
    tabela = Table(dados, colWidths=[170, 170, 130], repeatRows=1, hAlign='CENTER')
    tabela.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Bold'), ('FONTSIZE', (0, 1), (-1, -1), 9.5),
        ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#B71C1C')),
        ('TEXTCOLOR', (1, 1), (1, -1), colors.HexColor('#0D47A1')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, 0), 0.72, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return tabela


def _assinatura(ctx):
    dados = [[ctx.get('local_data') or '', ''], ['Local e Data', 'Assinatura do Responsável']]
    tabela = Table(dados, colWidths=[230, 270], hAlign='CENTER', rowHeights=[22, 14])
    tabela.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'), ('FONTSIZE', (0, 1), (-1, 1), 8.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, 0), 'BOTTOM'),
        ('LINEBELOW', (0, 0), (0, 0), 0.72, colors.black), ('LINEBELOW', (1, 0), (1, 0), 0.72, colors.black),
    ]))
    return KeepTogether([Spacer(1, 40), tabela])


def _rodape_factory(ctx):
    def desenhar(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(_rl.MARGEM_H, 18, f"Reidentificação de Animais — Notificação {ctx.get('nro_pedido', '')} — gerado pela plataforma Orion SISBOV em {ctx.get('gerado_em_completo', '')}")
        canvas.drawRightString(_rl.PAGE_SIZE[0] - _rl.MARGEM_H, 18, f'Página {doc.page}')
        canvas.restoreState()
    return desenhar


def gerar_pdf_reidentificacao(ctx):
    itens = ctx.get('itens') or []
    qtde = len(itens)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=_rl.PAGE_SIZE,
        leftMargin=_rl.MARGEM_H, rightMargin=_rl.MARGEM_H, topMargin=MARGEM_V_ANEXO, bottomMargin=34,
        title='Reidentificação de Animais', author='Orion SISBOV',
    )

    texto = ParagraphStyle('texto', fontName='Helvetica', fontSize=9.5, leading=14, alignment=TA_JUSTIFY, spaceAfter=10)
    sub = ParagraphStyle('sub', fontName='Times-Bold', fontSize=11, alignment=1, spaceBefore=6, spaceAfter=6)

    animais_txt = 'Animal' if qtde == 1 else 'Animais'
    declaracao = (
        f"Eu <b>{ctx.get('produtor') or ''}</b> portador do {_fmt_doc(ctx.get('cpf'), ctx.get('cnpj'))} Venho por meio desta, "
        f"informar que <b>{qtde} ( {_extenso(qtde)} {animais_txt} )</b> os quais estavam rastreados de acordo com as regras do SISBOV, "
        f"perderam os seus elementos Identificadores, e de acordo com a instrução Normativa 17, capítulo III, artigo 7º, parágrafo V, "
        f"todo animal que perder o seu Elemento de Identificação deverá receber uma nova identificação, cumprindo todos os procedimentos "
        f"constantes desta normativa. Solicito que a numeração perdida seja baixada para que assim possam ser substituída por uma nova "
        f"identificação."
    )

    historia = [
        _topo(ctx), Spacer(1, 14),
        Paragraph(declaracao, texto),
        Spacer(1, 4),
        Paragraph('Relação dos Códigos para serem Baixados:', sub),
        _tabela_codigos(itens),
        _assinatura(ctx),
    ]
    rodape = _rodape_factory(ctx)
    doc.build(historia, onFirstPage=rodape, onLaterPages=rodape)
    buffer.seek(0)
    return buffer

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_reidentificacao.py
# =========================================================
