# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\pdf_relatorio_brincagem.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-09-20 15:30 -03
# ATUALIZADO EM: 2026-09-20 20:30 -03
# VERSAO:       1.3.0
#
# DESCRICAO:
#     Geracao do PDF do Relatorio de Brincagem por Lote (Sessao
#     068/069), via ReportLab puro (Padrao Reutilizavel numero 2 -
#     ver receita completa em Regras.txt secao 10.2). Chamado por
#     backend/routers/brincagem_consulta.py::imprimir().
#
#     Cabecalho de Propriedade/Produtor: MESMO PADRAO SIMPLIFICADO
#     do Relatorio de ERAS (Produtor+CPF, Propriedade+Cod.MAPA,
#     Municipio/UF) - NAO reproduz Insc. Estadual/"Produtor Rural"/
#     CEP do mockup legado (atributos nunca confirmados nos models
#     reais, Regra de Ouro #1).
#
#     Tabela de animais (v1.1.0): construida MANUALMENTE com
#     Table/TableStyle (nao mais via criar_tabela_padrao) - pedido
#     de Benedito (Sessao 069) de reduzir a fonte (agora que o RFID
#     precisa caber 15 posicoes) exigia controle fino que a funcao
#     generica nao expõe. Colunas Manejo e Lote REMOVIDAS da
#     tabela (Lote ja aparece no cabecalho de campos; Manejo nunca
#     e coletado pela Brincagem com Leitor, sempre vazio). Peso SEM
#     casas decimais (3 posicoes inteiras, pedido de Benedito).
#
#     Quadro de totais (v1.1.0): SOMENTE Sexo x Idade x Total - SEM
#     a faixa "Zero a 04 Meses" (removida de proposito por
#     Benedito - Brincagem nao se aplica a bezerros tao novos) e
#     SEM as colunas Peso/Media por sexo nem o bloco lateral
#     Geral/Media/Peso (que causava o estouro na borda direita da
#     pagina, Sessao 068) - esses totais gerais agora vivem no
#     cabecalho de campos (Peso Geral/Peso Medio), junto com Lote/
#     Data Brincagem/Qtde Animais. Quadro sozinho e bem mais
#     estreito agora, centralizado na LARGURA_UTIL inteira sem
#     risco de estourar a pagina.
#
#     ATENCAO: a faixa "Zero a 04 Meses" e assumida como a 1a da
#     lista faixas_idade recebida (ordenada por id, ver chamador) -
#     se por acaso algum animal cair nela mesmo assim, ele ainda
#     conta no Total da linha do sexo, so nao aparece numa coluna
#     propria (nao existe mais coluna pra ela).
#
#     v1.0.0: Criacao do modulo (Sessao 068, 20/09/2026, 15:30 -03).
#     v1.1.0: Sessao 069 (20/09/2026, 09:00 -03) - Ajustes pedidos
#             por Benedito apos teste real (ver DESCRICAO acima):
#             titulo sem data, sem subtitulo de Lote (ja repetia
#             informacao), colunas Manejo/Lote removidas da
#             tabela, fonte da tabela reduzida (tabela reconstruida
#             manualmente pra isso), Peso sem decimais, quadro de
#             totais simplificado (4 faixas, sem Peso/Media/Geral)
#             e Peso Geral/Peso Medio movidos pro cabecalho de
#             campos.
#     v1.2.0: Sessao 070 (20/09/2026, 09:15 -03) - Dois ajustes
#             pedidos por Benedito apos novo teste: (1) espaco
#             adicionado entre o titulo e o bloco de dados da
#             Propriedade, que estavam colados; (2) colunas Idade
#             em Meses e Peso reduzidas, espaco redistribuido pro
#             SISBOV, que tambem ganhou fonte maior (9pt, contra
#             7pt do resto da tabela).
#     v1.3.0: Sessao 071 (20/09/2026, 20:00 -03) - Mais espaco
#             tirado de Peso e dado ao RFID; fonte do SISBOV
#             aumentada de 9 para 11pt (pedido de Benedito).
#     v1.4.0: Sessao 072 (20/09/2026, 20:00 -03) - Dois ajustes
#             pedidos por Benedito: (1) altura das celulas do
#             quadro de totais (Sexo x Idade) reduzida - menos
#             preenchimento vertical, cabem mais linhas impressas
#             se o quadro crescer; (2) Peso Geral (cabecalho de
#             campos) passa a usar ponto de milhar (ex.: "1,007.00"
#             em vez de "1007.00").
#     v1.5.0: Sessao 073 (20/09/2026, horario a confirmar) - BUG
#             REAL corrigido: a v1.4.0 usou formato AMERICANO de
#             numero ("1,007.00" - ponto de milhar, virgula
#             decimal e o oposto do padrao BR), Benedito corrigiu
#             na hora. Nova funcao _numero_br() formata certo
#             ("1.007,00" - ponto de milhar, virgula decimal),
#             aplicada em Peso Geral E Peso Medio (este ultimo
#             tambem estava errado, mesma causa - corrigido por
#             consistencia, nao foi pedido explicito).
#     v1.6.0: Sessao 074 (20/09/2026, horario a confirmar) - Fonte
#             de SISBOV aumentada de 11 para 13pt, e RFID (antes
#             no tamanho padrao de 7pt) passa a 12pt e negrito,
#             mesmo destaque do SISBOV - pedido de Benedito.
#     v1.7.0: Sessao 075 (20/09/2026, horario a confirmar) - BUG
#             REAL corrigido: as regras de FONTSIZE do SISBOV/RFID
#             vinham ANTES da regra geral de FONTSIZE 7 na lista da
#             TableStyle - no ReportLab, quando 2 regras se
#             sobrepoem na mesma celula, a ULTIMA da lista vence.
#             Por isso nenhum tamanho de fonte configurado pro
#             SISBOV/RFID (9, 11, 13, nem o 15 que Benedito tentou)
#             aparecia de verdade - a regra geral de 7pt, vindo
#             depois, sempre sobrescrevia de volta. Corrigido
#             reordenando: regra geral primeiro, destaques de
#             SISBOV (15pt)/RFID (12pt) por ultimo.
# =========================================================

from datetime import datetime
from io import BytesIO

from flask import send_file
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.utils.pdf_reportlab import (
    COR_BORDA, COR_FUNDO_CABECALHO,
    LARGURA_UTIL, MARGEM_H, MARGEM_V, PAGE_SIZE,
    criar_bloco_dados, criar_cabecalho_campos,
    estilo_rodape, estilo_titulo,
)


def _numero_br(valor):
    """Formata um numero no padrao brasileiro: ponto pro milhar,
    virgula pro decimal (ex.: 1007.5 -> '1.007,50'). Corrige o
    erro da v1.4.0, que usava '{:,.2f}' puro (formato americano,
    "1,007.00") - pedido de Benedito, Sessao 073."""
    return '{:,.2f}'.format(valor).replace(',', 'X').replace('.', ',').replace('X', '.')


# -------------------------------------------------------
# Funcao principal: monta o PDF do Relatorio de Brincagem por Lote
# e devolve a Response ja pronta pro Flask (send_file).
#
# animais: lista de dicts, JA resolvidos pelo chamador
#     (brincagem_consulta.py::imprimir()) - chaves esperadas:
#     sisbov, manejo, rfid, sexo, nascimento (date), idade_faixa
#     (descricao ou None), raca_codigo, lote, peso (float ou None).
#     'manejo' e 'lote' continuam recebidos (podem servir a outro
#     uso futuro), mas NAO aparecem mais na tabela impressa.
# faixas_idade: lista de descricoes das 5 faixas (ordem real do
#     banco, tb_4006_idade_meses, por id) - a PRIMEIRA (Zero a 04
#     Meses) e descartada do quadro de totais (v1.1.0).
# lote: nome do Lote (string).
# data_brincagem: objeto date.
# propriedade / produtor: objetos Propriedade / Produtor (ou None).
# -------------------------------------------------------
def gerar_pdf_relatorio_brincagem(animais, faixas_idade, lote, data_brincagem, propriedade, produtor):
    faixas_exibidas = faixas_idade[1:] if len(faixas_idade) > 1 else faixas_idade

    linhas_tabela = []
    contagem = {}  # {(sexo, faixa_idade): {'qtde': N}}
    peso_total_geral = 0.0
    qtde_com_peso = 0

    for indice, animal in enumerate(animais, start=1):
        peso_val = animal['peso']

        linhas_tabela.append([
            indice,
            animal['sisbov'] or '-',
            animal['rfid'] or '-',
            animal['sexo'] or '-',
            animal['nascimento'].strftime('%d/%m/%Y') if animal['nascimento'] else '-',
            animal['idade_faixa'] or '-',
            animal['raca_codigo'] or '-',
            ('%d' % round(peso_val)) if peso_val is not None else '-',
        ])

        if peso_val is not None:
            peso_total_geral += peso_val
            qtde_com_peso += 1

        if animal['sexo'] in ('MACHO', 'FEMEA') and animal['idade_faixa']:
            chave = (animal['sexo'], animal['idade_faixa'])
            contagem.setdefault(chave, {'qtde': 0})
            contagem[chave]['qtde'] += 1

    peso_medio_geral = (peso_total_geral / qtde_com_peso) if qtde_com_peso else 0.0

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=PAGE_SIZE,
        leftMargin=MARGEM_H, rightMargin=MARGEM_H,
        topMargin=MARGEM_V, bottomMargin=MARGEM_V,
    )

    # v1.1.0: titulo sem data, sem linha de subtitulo com Lote
    # (ja aparece logo abaixo, no cabecalho de campos - evitava
    # repetir a mesma informacao duas vezes, pedido de Benedito).
    story = [Paragraph('RELATÓRIO DE BRINCAGEM', estilo_titulo)]
    # v1.2.0: espaco entre o titulo e o bloco de dados - sem isso
    # eles ficavam colados (Sessao 070, teste real de Benedito).
    story.append(Spacer(1, 12))

    texto_mapa = f'Cód. MAPA: {propriedade.codigo_mapa}' if propriedade and propriedade.codigo_mapa else ''

    story += criar_bloco_dados('DADOS DA ORIGEM DOS ANIMAIS', [
        ('Produtor:', produtor.nome if produtor else '-',
         f'CPF/CNPJ: {produtor.cpf_cnpj}' if produtor and produtor.cpf_cnpj else 'CPF/CNPJ: -'),
        ('Propriedade:', propriedade.nome if propriedade else '-', texto_mapa),
        ('Município:', f'{propriedade.municipio} / {propriedade.uf}' if propriedade and propriedade.municipio else '-', None),
    ])

    # v1.1.0: Peso Geral e Peso Medio entraram aqui (antes viviam
    # no bloco lateral do quadro de totais, que foi removido).
    story.append(criar_cabecalho_campos([
        ('Lote', lote),
        ('Data Brincagem', data_brincagem.strftime('%d/%m/%Y')),
        ('Qtde Animais', str(len(animais))),
        ('Peso Geral', _numero_br(peso_total_geral)),
        ('Peso Médio', _numero_br(peso_medio_geral)),
    ]))
    story.append(Spacer(1, 10))

    # ---------------------------------------------------
    # Tabela de animais - v1.1.0: construida manualmente (nao mais
    # criar_tabela_padrao) para reduzir a fonte e ajustar larguras
    # com precisao (RFID cabe 15 posicoes, Raca so 2, Peso sem
    # decimais). Colunas Manejo e Lote REMOVIDAS.
    # ---------------------------------------------------
    cabecalhos_animais = ['Ind.', 'SISBOV', 'RFID', 'Sexo', 'Nascimento', 'Idade em Meses', 'Raça', 'Peso']
    # v1.3.0: mais espaço tirado de Peso e dado ao RFID (pedido de
    # Benedito, Sessao 071); fonte do SISBOV aumentada de novo.
    pesos_col = (0.05, 0.27, 0.23, 0.08, 0.12, 0.12, 0.07, 0.06)
    larguras_animais = [w * LARGURA_UTIL for w in pesos_col]

    tabela_animais = Table(
        [cabecalhos_animais] + linhas_tabela,
        colWidths=larguras_animais,
        repeatRows=1,
    )
    tabela_animais.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COR_FUNDO_CABECALHO),
        ('GRID', (0, 0), (-1, -1), 0.5, COR_BORDA),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (6, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('ALIGN', (7, 0), (7, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        # BUG REAL corrigido (Sessao 075): as regras abaixo (SISBOV
        # e RFID) precisam vir DEPOIS da regra geral de FONTSIZE 7
        # acima - no ReportLab, quando 2 regras da TableStyle se
        # sobrepoem na mesma celula, a ULTIMA da lista vence. Elas
        # estavam ANTES da regra geral nas versoes anteriores, e
        # por isso o aumento de fonte nunca aparecia de verdade -
        # o tamanho 13/15 que Benedito configurava era sempre
        # sobrescrito de volta pra 7 por essa mesma regra geral.
        ('FONTNAME', (1, 1), (2, -1), 'Helvetica-Bold'),  # SISBOV e RFID em destaque
        ('FONTSIZE', (1, 1), (1, -1), 11),  # fonte do SISBOV
        ('FONTSIZE', (2, 1), (2, -1), 11),  # fonte do RFID
    ]))
    story.append(tabela_animais)
    story.append(Spacer(1, 10))

    # ---------------------------------------------------
    # Quadro de totais - v1.1.0: SOMENTE Sexo x Idade (4 faixas,
    # sem "Zero a 04 Meses") x Total. Sozinho na sua linha,
    # centralizado na LARGURA_UTIL inteira (mesma tecnica do
    # Relatorio de ERAS v1.9.0) - bem mais estreito agora, sem
    # risco de estourar a borda da pagina.
    # ---------------------------------------------------
    cabecalho_resumo = ['Sexo'] + faixas_exibidas + ['Total']

    def _linha_sexo(sexo_enum, rotulo):
        qtdes = []
        total_linha = 0
        for faixa in faixas_exibidas:
            qtde = contagem.get((sexo_enum, faixa), {'qtde': 0})['qtde']
            qtdes.append(str(qtde) if qtde else '')
            total_linha += qtde
        return [rotulo] + qtdes + [str(total_linha) if total_linha else '']

    resumo_dados = [cabecalho_resumo, _linha_sexo('FEMEA', 'Fêmeas'), _linha_sexo('MACHO', 'Machos')]

    col_sexo  = 55
    col_faixa = 68
    col_total = 50
    larguras_resumo = [col_sexo] + [col_faixa] * len(faixas_exibidas) + [col_total]
    largura_tabela_resumo = sum(larguras_resumo)

    tabela_resumo = Table(resumo_dados, colWidths=larguras_resumo)
    tabela_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COR_FUNDO_CABECALHO),
        ('GRID', (0, 0), (-1, -1), 0.5, COR_BORDA),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    margem_centralizacao = (LARGURA_UTIL - largura_tabela_resumo) / 2
    if margem_centralizacao < 0:
        margem_centralizacao = 0

    linha_resumo = Table(
        [['', tabela_resumo, '']],
        colWidths=[margem_centralizacao, largura_tabela_resumo, margem_centralizacao],
    )
    linha_resumo.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(linha_resumo)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        f'Impressão: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}',
        estilo_rodape,
    ))

    doc.build(story)
    buffer.seek(0)

    nome_propriedade = (propriedade.nome if propriedade else 'Propriedade').replace(' ', '_')
    nome_lote = lote.replace(' ', '_')
    nome_arquivo = f'Relatorio_Brincagem_{nome_propriedade}_{nome_lote}.pdf'

    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_relatorio_brincagem.py
# =========================================================