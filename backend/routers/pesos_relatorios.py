# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\pesos_relatorios.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-17 11:30 -03
# ATUALIZADO EM: 2026-11-17 14:30 -03
# VERSAO: 1.0.7
#
# DESCRICAO:
#     Relatorios de Pesagem em PDF (Sessao 129) - UMA tela so ("Relatorios de Pesagem"): o usuario escolhe o relatorio e so aparecem os
#     filtros dele. Equivale aos relatorios da coluna Impressao do menu Pesos do GERAS (modelos de 13/11/2026). Telas de CONSULTA: nao gravam.
#
#     RELATORIOS (tipo): 01 Pesagem por Periodo | 02 Ultimo Peso do Lote | 03 Primeiras 03 Pesagens | 04 Todas as Pesagens do Lote |
#       05 Resumo dos Lotes | 06 Resumo por Data | 07 Ultima Pesagem do Lote no Periodo | 08 Primeira e Ultima Pesagem do Lote |
#       09 Resumo por Faixa de Peso (de 50 em 50 kg) | 10 Pesagem por Selecao (peso acima de N kg).
#
#     REGRAS (propostas do Claude, a confirmar pelo Benedito):
#       - So entram animais que AINDA estao no rebanho (tb_2001). Fazenda e Produtor vem da Propriedade em uso (sem escolher na tela).
#       - Media (Kg, @, GMD, dias) so conta os animais que TEM o dado; quem nao foi pesado nao puxa a media para baixo.
#       - Media em @ = Kg / 30 (igual ao legado). Ganho = peso atual - peso anterior; GMD = ganho / dias; sem pesagem anterior = em branco.
#       - Faixas do 09: "-300" = abaixo de 300 kg; "+300" = de 300 a 349,9; ... "+700" = 700 kg ou mais; coluna extra "Sem peso".
#       - 02 usa todo o historico do lote; 08 so as pesagens do periodo. 04 mostra uma linha por pesagem.
#
#     ROTAS:
#       /produtor/pesos-relatorios/iniciar - resolve a Propriedade.
#       /produtor/pesos-relatorios/selecao - tela unica (escolhe relatorio + filtros).
#       /produtor/pesos-relatorios/pdf     - gera o PDF.
#
#     v1.0.7: Sessao 129 (2026-11-17 14:30 -03) - Relatorios 01 e 06: o Ind (numero do animal) tambem aparece so na 1a linha de cada animal, igual ao 04 (decisao do Benedito: mesmo padrao em todos). REVERSAO: .bak_antes_s129_ind_01_06.
#     v1.0.6: Sessao 129 (2026-11-17 14:25 -03) - Relatorio 04: o Ind (numero do animal) aparece so na 1a linha de cada animal e a numeracao conta so os animais que tem pesagem no periodo. Sugestao do Benedito. REVERSAO: .bak_antes_s129_ind_04.
#     v1.0.5: Sessao 129 (2026-11-17 13:10 -03) - Relatorio 06: a pesagem ANTERIOR passa a ser so de data anterior ao dia do relatorio (antes comparava com outra pesagem do mesmo dia: Dias 0 e ganho negativo sem sentido); Ind = numero do animal e coluna Nº (em branco quando o animal tem uma so), como no 01. REVERSAO: .bak_antes_s129_rel06.
#     v1.0.4: Sessao 129 (2026-11-17 13:00 -03) - Nome do arquivo PDF descritivo (ex.: Pesagem_04_Todas_as_Pesagens_BOX_13_2026-11-17.pdf) em vez de so o numero. Pedido do Benedito. REVERSAO: .bak_antes_s129_nome_arquivo.
#     v1.0.3: Sessao 129 (2026-11-17 12:50 -03) - Media Dias (relatorios 02, 03, 06 e 08) conta so os animais com intervalo maior que 0 dia, igual a Media GMD (pesagens no mesmo dia davam 0 e puxavam a media para baixo). Pedido do Benedito. REVERSAO: .bak_antes_s129_media_dias.
#     v1.0.2: Sessao 129 (2026-11-17 12:10 -03) - Relatorio 01: coluna Nº fica em BRANCO para o animal que tem uma unica pesagem no relatorio (so aparece nos que se repetem). Pedido do Benedito. REVERSAO: .bak_antes_s129_n_branco.
#     v1.0.1: Sessao 129 (2026-11-17 12:05 -03) - Relatorio 01: Ind passa a ser o numero do ANIMAL (repete nas pesagens dele) e entra a coluna Nº (ordem da pesagem do animal), para o ultimo Ind bater com o total de Animais (pedido do Benedito). REVERSAO: .bak_antes_s129_ind_animal.
#     v1.0.0: Criacao (Sessao 129, 17/11/2026, 11:30 -03). REVERSAO: remover este arquivo, pesos_relatorios.html, utils\pdf_pesagem_relatorios.py,
#     o registro em app.py, o card no hub_entrada_agrupado.py e a linha de permissoes.py.
# =========================================================

from datetime import datetime, date
import logging
from urllib.parse import urlencode

from flask import Blueprint, render_template, request, redirect, session, send_file
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, Produtor
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.pesos_leitor import _iniciar_generico
from backend.routers.saida_leitor import _propriedade_do_usuario, _data_br, _ler_data_br
from backend.utils.multitenant import get_db_produtor
from backend.utils.pdf_pesagem_relatorios import gerar_pdf_pesagem_relatorio

pesos_relatorios = Blueprint('pesos_relatorios', __name__)
logger = logging.getLogger(__name__)


@pesos_relatorios.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


URL_HUB      = '/produtor/hub-novo/pesos'
URL_INICIAR  = '/produtor/pesos-relatorios/iniciar'
URL_SELECAO  = '/produtor/pesos-relatorios/selecao'

# tipo -> (nome, precisa de periodo, precisa de lote)
RELATORIOS = {
    '01': ('01 - Pesagem por Período', True, False),
    '02': ('02 - Último Peso do Lote', False, True),
    '03': ('03 - Primeiras 03 Pesagens do Lote', True, True),
    '04': ('04 - Todas as Pesagens do Lote', True, True),
    '05': ('05 - Resumo dos Pesos dos Lotes', False, False),
    '06': ('06 - Resumo por Data', False, False),
    '07': ('07 - Última Pesagem do Lote no Período', True, True),
    '08': ('08 - Primeira e Última Pesagem do Lote', True, True),
    '09': ('09 - Resumo por Faixa de Peso', False, False),
    '10': ('10 - Pesagem por Seleção (peso acima de)', False, False),
}
ARROBA_KG = 30.0
FAIXAS_PESO = [300, 350, 400, 450, 500, 550, 600, 650, 700]   # limites inferiores; abaixo de 300 = "-300"

# Nome curto de cada relatorio para o arquivo baixado (sem acento nem espaco)
NOMES_ARQUIVO = {
    '01': 'Pesagem_por_Periodo', '02': 'Ultimo_Peso_do_Lote', '03': 'Primeiras_3_Pesagens', '04': 'Todas_as_Pesagens',
    '05': 'Resumo_dos_Lotes', '06': 'Resumo_por_Data', '07': 'Ultima_Pesagem_do_Lote', '08': 'Primeira_e_Ultima_Pesagem',
    '09': 'Resumo_por_Faixa_de_Peso', '10': 'Pesagem_por_Selecao',
}

MENSAGENS = {
    'tipo':    'Escolha o relatório que deseja imprimir.',
    'data':    'Data incorreta. Digite no formato dd/mm/aaaa.',
    'periodo': 'A data inicial é maior que a final. Corrija as datas.',
    'lote':    'Escolha o lote deste relatório.',
    'peso':    'Digite o peso (em kg) maior que zero e menor que 5.000.',
    'vazio':   'Nenhuma pesagem encontrada com esses filtros (só entram animais que ainda estão na Propriedade). Confira as datas e o lote.',
}


# -------------------------------------------------------
# Formatacao (padrao brasileiro)
# -------------------------------------------------------
def _br(valor, casas=2):
    if valor is None:
        return ''
    texto = f'{float(valor):,.{casas}f}'
    return texto.replace(',', '#').replace('.', ',').replace('#', '.')


def _total_txt(valor):
    """Soma de pesos: sem casas quando for inteira, senao 2 casas."""
    v = float(valor)
    return _br(v, 0 if abs(v - round(v)) < 0.005 else 2)


def _peso(valor):
    """Peso do animal: inteiro quando nao tem fracao (418), senao ate 2 casas (418,5)."""
    if valor is None:
        return ''
    v = float(valor)
    if abs(v - round(v)) < 0.005:
        return _br(round(v), 0)
    return _br(v, 2).rstrip('0').rstrip(',')


def _media(valores):
    return (sum(valores) / len(valores)) if valores else None


def _arroba(media):
    return (media / ARROBA_KG) if media is not None else None


def _sexo(e):
    s = str(e.sexo.value if hasattr(e.sexo, 'value') else (e.sexo or ''))
    return {'FEMEA': 'Fêmea', 'MACHO': 'Macho'}.get(s, s)


def _faixa_idade(faixas, e, data, eras_dias=None):
    dias = (data - e.nascimento).days if (e.nascimento and data) else eras_dias
    if dias is None:
        return ''
    for f in faixas:
        if f.dias_min <= dias <= f.dias_max:
            return f.descricao
    return ''


def _gmd(ganho, dias):
    return (ganho / dias) if (ganho is not None and dias and dias > 0) else None


def _volta_hub():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    return URL_INICIAR if (len(pares) > 1 and resolver_fazenda_em_uso(pares) is None) else URL_HUB


def _periodo_txt(p):
    return f"Período: {_data_br(p['ini'])} até {_data_br(p['fim'])}"


def _no_periodo(lista, p):
    return [x for x in lista if p['ini'] <= x.data_pesagem <= p['fim']]


def _do_lote(ativos, lote):
    return sorted([e for e in ativos.values() if (e.lote or '') == lote], key=lambda e: e.sisbov)


def _ultimo(hist, sisbov):
    lista = hist.get(sisbov) or []
    return lista[-1] if lista else None


# -------------------------------------------------------
# CONSTRUTORES (funcoes puras: recebem os dados ja carregados e devolvem o contexto do PDF).
#   ativos: {sisbov: Entrada}   hist: {sisbov: [Peso ordenado por data/sequencia]}
# -------------------------------------------------------
def _rel_01(ativos, hist, faixas, racas, p):
    itens = []
    for sisbov, lista in hist.items():
        for x in _no_periodo(lista, p):
            itens.append((x.data_pesagem, sisbov, x))
    itens.sort(key=lambda t: (t[1], t[0]))
    linhas, pesos, animais = [], [], {}
    por_animal = {}
    for (_, sisbov, _x) in itens:
        por_animal[sisbov] = por_animal.get(sisbov, 0) + 1   # quantas linhas cada animal tem no relatorio
    for (_, sisbov, x) in itens:
        e = ativos[sisbov]
        primeira_linha = sisbov not in animais
        i = animais.setdefault(sisbov, len(animais) + 1)   # Ind = numero do animal, so na 1a linha dele
        if float(x.peso) > 0:
            pesos.append(float(x.peso))
        linhas.append([f'{i}' if primeira_linha else '', sisbov, f'{x.sequencia}' if por_animal[sisbov] > 1 else '', _sexo(e), racas.get(e.id_raca, ''), 'SIM' if e.cota_hilton else '', x.lote or e.lote or '',
                       _faixa_idade(faixas, e, x.data_pesagem, x.eras_dias), _data_br(x.data_pesagem), _peso(x.peso),
                       _data_br(e.liberacao_abate)])
    media = _media(pesos)
    return {
        'titulo': 'REGISTRO DE PESAGENS POR PERÍODO', 'subtitulos': [_periodo_txt(p)],
        'colunas': [('Ind', 5, 'c'), ('Sisbov', 15, 'c'), ('Nº', 4, 'c'), ('Sexo', 7, 'c'), ('Raça', 5, 'c'), ('CTH', 5, 'c'), ('Lote', 15, 'l'),
                    ('Idade em Meses', 11, 'c'), ('Pesagem', 10, 'c'), ('Peso', 7, 'r'), ('Liberação', 10, 'c')],
        'negrito': [1], 'linhas': linhas, 'paisagem': False,
        'totais': [('Total Pesagens', f'{len(linhas)}'), ('Animais', f'{len(animais)}'), ('Peso Total', _total_txt(sum(pesos))),
                   ('Média Kgs', _br(media)), ('Média @', _br(_arroba(media)))],
        'nota': 'Ind = número do animal (só na 1ª linha dele); Nº = ordem da pesagem do animal (em branco quando o animal tem uma só). Média só das pesagens com peso. Média @ = Kg ÷ 30.',
        'vazio': not linhas,
    }


def _rel_02_08(ativos, hist, faixas, racas, p, so_periodo):
    lote = p['lote']
    linhas, atuais, dias_l, gmds = [], [], [], []
    selecionados = _do_lote(ativos, lote)
    for i, e in enumerate(selecionados, start=1):
        lista = hist.get(e.sisbov, [])
        if so_periodo:
            lista = _no_periodo(lista, p)
        cth = 'SIM' if e.cota_hilton else ''
        if lista:
            primeira, ultima = lista[0], lista[-1]
            dias = (ultima.data_pesagem - primeira.data_pesagem).days if len(lista) > 1 else None
            ganho = (float(ultima.peso) - float(primeira.peso)) if len(lista) > 1 else None
            gmd = _gmd(ganho, dias)
            atuais.append(float(ultima.peso))
            if dias:   # so intervalo maior que 0 dia entra na Media Dias
                dias_l.append(dias)
            if gmd is not None:
                gmds.append(gmd)
            linhas.append([f'{i:04d}', e.sisbov, e.rfid or '', _data_br(e.data_inclusao), _peso(primeira.peso), f'{len(lista)}',
                           _data_br(ultima.data_pesagem), _peso(ultima.peso), '' if dias is None else f'{dias}',
                           _peso(ganho) if ganho is not None else '', _br(gmd, 3), cth])
        else:
            linhas.append([f'{i:04d}', e.sisbov, e.rfid or '', _data_br(e.data_inclusao), '', '0', '', '', '', '', '', cth])
    subs = [f'Lote: {lote} - {len(selecionados)} Animais.']
    if so_periodo:
        subs.insert(0, _periodo_txt(p))
    return {
        'titulo': 'PRIMEIRA E ÚLTIMA PESAGEM POR LOTE' if so_periodo else 'REGISTRO DA ÚLTIMA PESAGEM DO LOTE', 'subtitulos': subs,
        'colunas': [('Ind', 5, 'c'), ('Sisbov', 14, 'c'), ('RFID', 14, 'c'), ('Data Entrada', 9, 'c'), ('Peso Inicial', 7, 'r'), ('Qtde de Pesagens', 7, 'c'),
                    ('Última Pesagem', 9, 'c'), ('Peso Atual', 7, 'r'), ('Dias', 5, 'c'), ('Ganho Total', 7, 'r'), ('Média Diária', 7, 'r'), ('CTH', 5, 'c')],
        'negrito': [1], 'linhas': linhas, 'paisagem': True,
        'totais': [('Total Animais', f'{len(selecionados)}'), ('Peso Lote', _total_txt(sum(atuais))),
                   ('Média Kgs', _br(_media(atuais))), ('Média Dias', _br(_media(dias_l), 0)), ('Média GMD', _br(_media(gmds), 3))],
        'nota': 'Peso Lote e médias só dos animais com peso. Dias, Ganho e Média Diária só aparecem com 2 ou mais pesagens. Média Dias e Média GMD só contam animais com intervalo maior que 0 dia.',
        'vazio': not selecionados or not atuais,
    }


def _rel_03(ativos, hist, faixas, racas, p):
    lote = p['lote']
    linhas, finais, dias_f, gmds = [], [], [], []
    selecionados = _do_lote(ativos, lote)
    for i, e in enumerate(selecionados, start=1):
        lista = _no_periodo(hist.get(e.sisbov, []), p)[:3]
        linha = [f'{i:04d}', e.sisbov, e.lote or '']
        for n in range(3):
            if n < len(lista):
                x = lista[n]
                linha += [_data_br(x.data_pesagem), _peso(x.peso)]
                if n > 0:
                    anterior = lista[n - 1]
                    ganho = float(x.peso) - float(anterior.peso)
                    dias = (x.data_pesagem - anterior.data_pesagem).days
                    linha += [_peso(ganho), f'{dias}', _br(_gmd(ganho, dias), 3)]
            else:
                linha += ['', ''] + ([] if n == 0 else ['', '', ''])
        if len(lista) >= 2:
            ganho_f = float(lista[-1].peso) - float(lista[0].peso)
            dias_fin = (lista[-1].data_pesagem - lista[0].data_pesagem).days
            gmd_f = _gmd(ganho_f, dias_fin)
            linha += [_peso(ganho_f), f'{dias_fin}', _br(gmd_f, 3)]
            if dias_fin > 0:   # so intervalo maior que 0 dia entra na Media Dias
                dias_f.append(dias_fin)
            if gmd_f is not None:
                gmds.append(gmd_f)
        else:
            linha += ['', '', '']
        if lista:
            finais.append(float(lista[-1].peso))
        linhas.append(linha)
    colunas = [('Ind', 4, 'c'), ('Sisbov', 11, 'c'), ('Lote', 8, 'l'),
               ('1ª Data', 6, 'c'), ('1ª Peso', 4, 'r'),
               ('2ª Data', 6, 'c'), ('2ª Peso', 4, 'r'), ('2ª Ganho', 4, 'r'), ('2ª Dias', 3, 'c'), ('2ª Média', 4, 'r'),
               ('3ª Data', 6, 'c'), ('3ª Peso', 4, 'r'), ('3ª Ganho', 4, 'r'), ('3ª Dias', 3, 'c'), ('3ª Média', 4, 'r'),
               ('Ganho Final', 5, 'r'), ('Dias Final', 4, 'c'), ('Média Final', 5, 'r')]
    return {
        'titulo': 'REGISTRO DAS 03 PESAGENS DO LOTE', 'subtitulos': [_periodo_txt(p), f'Lote: {lote} - {len(selecionados)} Animais.'],
        'colunas': colunas, 'negrito': [1], 'linhas': linhas, 'paisagem': True,
        'totais': [('Total Animais', f'{len(selecionados)}'), ('Peso Lote', _total_txt(sum(finais))),
                   ('Média Kgs Lote', _br(_media(finais))), ('Média Dias', _br(_media(dias_f), 0)), ('Média GMD', _br(_media(gmds), 3))],
        'nota': 'Peso Lote e Média Kgs: último peso das 3 primeiras pesagens do período, só dos animais com peso. "Média" = ganho médio por dia (GMD).',
        'vazio': not selecionados or not finais,
    }


def _rel_04(ativos, hist, faixas, racas, p):
    lote = p['lote']
    selecionados = _do_lote(ativos, lote)
    linhas, n_pesagens, n_animais = [], 0, 0
    for e in selecionados:
        lista = hist.get(e.sisbov, [])
        primeira_linha = True
        for k, x in enumerate(lista):
            if not (p['ini'] <= x.data_pesagem <= p['fim']):
                continue
            if primeira_linha:
                n_animais += 1
            ganho = dias = None
            if k > 0:
                ganho = float(x.peso) - float(lista[k - 1].peso)
                dias = (x.data_pesagem - lista[k - 1].data_pesagem).days
            n_pesagens += 1
            ind = f'{n_animais:04d}' if primeira_linha else ''   # Ind so na 1a linha do animal
            primeira_linha = False
            linhas.append([ind, e.sisbov, f'{x.sequencia}', _data_br(x.data_pesagem), _peso(x.peso),
                           _peso(ganho) if ganho is not None else '', '' if dias is None else f'{dias}', _br(_gmd(ganho, dias), 3),
                           x.lote or e.lote or ''])
    return {
        'titulo': 'REGISTRO DE TODAS AS PESAGENS DO LOTE', 'subtitulos': [_periodo_txt(p), f'Lote: {lote} - {len(selecionados)} Animais.'],
        'colunas': [('Ind', 6, 'c'), ('Sisbov', 16, 'c'), ('Pesagem nº', 8, 'c'), ('Data', 11, 'c'), ('Peso', 8, 'r'), ('Ganho', 8, 'r'),
                    ('Dias', 6, 'c'), ('Média Diária', 10, 'r'), ('Lote', 16, 'l')],
        'negrito': [1], 'linhas': linhas, 'paisagem': False,
        'totais': [('Total Animais', f'{len(selecionados)}'), ('Total Pesagens', f'{n_pesagens}')],
        'nota': 'Ganho e Dias contam a partir da pesagem anterior do animal (mesmo que ela seja anterior ao período).',
        'vazio': n_pesagens == 0,
    }


def _rel_05(ativos, hist, faixas, racas, p):
    grupos = {}
    for e in ativos.values():
        g = grupos.setdefault(e.lote or '(sem lote)', {'animais': 0, 'sem': 0, 'pesos': []})
        g['animais'] += 1
        u = _ultimo(hist, e.sisbov)
        if u is None or float(u.peso) <= 0:
            g['sem'] += 1
        else:
            g['pesos'].append(float(u.peso))
    linhas, tot_a, tot_s, tot_p = [], 0, 0, []
    for i, nome in enumerate(sorted(grupos, key=lambda s: s.upper()), start=1):
        g = grupos[nome]
        m = _media(g['pesos'])
        linhas.append([f'{i}', nome, f"{g['animais']}", f"{g['sem']}", _br(sum(g['pesos']), 1), _br(m), _br(_arroba(m))])
        tot_a += g['animais']
        tot_s += g['sem']
        tot_p += g['pesos']
    m = _media(tot_p)
    linhas.append(['', 'Totais', f'{tot_a}', f'{tot_s}', _br(sum(tot_p), 1), _br(m), _br(_arroba(m))])
    return {
        'titulo': 'REGISTRO DE PESAGENS DOS LOTES', 'subtitulos': ['RESUMO (último peso de cada animal)'],
        'colunas': [('Ind', 6, 'c'), ('Lote', 26, 'l'), ('Animais', 10, 'c'), ('Sem peso', 10, 'c'), ('Peso', 14, 'r'), ('Média Kgs', 12, 'r'), ('Média @', 12, 'r')],
        'negrito': [1], 'linhas': linhas, 'total_ultima_linha': True, 'paisagem': False,
        'nota': 'Peso, Média Kg e Média @ só dos animais com peso. Média @ = Kg ÷ 30.',
        'vazio': not ativos,
    }


def _rel_06(ativos, hist, faixas, racas, p):
    data = p['data']
    itens = []
    for sisbov, lista in hist.items():
        do_dia = [x for x in lista if x.data_pesagem == data]
        if not do_dia:
            continue
        anteriores = [x for x in lista if x.data_pesagem < data]
        ant = anteriores[-1] if anteriores else None   # so pesagem de data ANTERIOR ao dia do relatorio
        for x in do_dia:
            itens.append((sisbov, x, ant))
    itens.sort(key=lambda t: (t[0], t[1].sequencia))
    por_animal = {}
    for (sisbov, _x, _a) in itens:
        por_animal[sisbov] = por_animal.get(sisbov, 0) + 1
    numeros = {}
    linhas, pesos, gmds, dias_l = [], [], [], []
    for (sisbov, x, ant) in itens:
        e = ativos[sisbov]
        primeira_linha = sisbov not in numeros
        i = numeros.setdefault(sisbov, len(numeros) + 1)   # Ind = numero do animal, so na 1a linha dele
        ganho = dias = gmd = None
        if ant is not None:
            ganho = float(x.peso) - float(ant.peso)
            dias = (x.data_pesagem - ant.data_pesagem).days
            gmd = _gmd(ganho, dias)
            if dias > 0:   # so intervalo maior que 0 dia entra na Media Dias
                dias_l.append(dias)
            if gmd is not None:
                gmds.append(gmd)
        pesos.append(float(x.peso))
        linhas.append([f'{i}' if primeira_linha else '', sisbov, f'{x.sequencia}' if por_animal[sisbov] > 1 else '',
                       _data_br(ant.data_pesagem) if ant else '', _peso(ant.peso) if ant else '', _data_br(x.data_pesagem), _peso(x.peso),
                       '' if dias is None else f'{dias}', _br(gmd, 3), _peso(ganho) if ganho is not None else '', x.lote or e.lote or ''])
    return {
        'titulo': 'REGISTRO DE PESAGENS', 'subtitulos': [f'Pesagem: {_data_br(data)}'],
        'colunas': [('Ind', 5, 'c'), ('Sisbov', 15, 'c'), ('Nº', 4, 'c'), ('Pesagem Anterior', 11, 'c'), ('Peso Anterior', 8, 'r'), ('Pesagem', 11, 'c'), ('Peso', 8, 'r'),
                    ('Dias', 6, 'c'), ('Média Diária', 9, 'r'), ('Ganho Final', 8, 'r'), ('Lote', 16, 'l')],
        'negrito': [1], 'linhas': linhas, 'paisagem': False,
        'totais': [('Total Animais', f'{len(numeros)}'), ('Total Pesagens', f'{len(linhas)}'), ('Total Peso', _total_txt(sum(pesos))),
                   ('Média Kgs', _br(_media(pesos))), ('Média GMD', _br(_media(gmds), 3)), ('Média Dias', _br(_media(dias_l), 0))],
        'nota': 'Ind = número do animal (só na 1ª linha dele); Nº = número da pesagem do animal (aparece só quando ele tem mais de uma no dia). A pesagem anterior é sempre de uma data anterior; Dias, Média Diária e Ganho Final só aparecem quando existe.',
        'vazio': not linhas,
    }


def _rel_07(ativos, hist, faixas, racas, p):
    lote = p['lote']
    selecionados = _do_lote(ativos, lote)
    linhas, pesos = [], []
    for e in selecionados:
        lista = _no_periodo(hist.get(e.sisbov, []), p)
        if not lista:
            continue
        u = lista[-1]
        pesos.append(float(u.peso))
        linhas.append([f'{len(linhas) + 1}', e.sisbov, e.rfid or '', _data_br(u.data_pesagem), _peso(u.peso), 'SIM' if e.cota_hilton else ''])
    return {
        'titulo': 'REGISTRO DA ÚLTIMA PESAGEM DO LOTE', 'subtitulos': [_periodo_txt(p), f'Lote: {lote} - {len(selecionados)} Animais.'],
        'colunas': [('Ind', 6, 'c'), ('Sisbov', 20, 'c'), ('RFID', 20, 'c'), ('Última Pesagem', 14, 'c'), ('Peso Atual', 10, 'r'), ('Cota Hilton', 10, 'c')],
        'negrito': [1], 'linhas': linhas, 'paisagem': False,
        'totais': [('Animais Pesados', f'{len(linhas)}'), ('Peso Total', _total_txt(sum(pesos))), ('Média Kgs', _br(_media(pesos)))],
        'vazio': not linhas,
    }


def _rotulo_faixa(i):
    return '-300' if i == 0 else f'+{FAIXAS_PESO[i - 1]}'


def _indice_faixa(valor):
    n = 0
    for lim in FAIXAS_PESO:
        if valor >= lim:
            n += 1
    return n


def _rel_09(ativos, hist, faixas, racas, p):
    contagem = [0] * (len(FAIXAS_PESO) + 1)
    sem = 0
    for e in ativos.values():
        u = _ultimo(hist, e.sisbov)
        if u is None or float(u.peso) <= 0:
            sem += 1
        else:
            contagem[_indice_faixa(float(u.peso))] += 1
    total = sum(contagem) + sem
    colunas = [('', 16, 'l')] + [(_rotulo_faixa(i), 6, 'c') for i in range(len(contagem))] + [('Sem peso', 7, 'c'), ('Total', 7, 'c')]
    linha = [p.get('produtor', '')] + [str(c) for c in contagem] + [str(sem), str(total)]
    linha_tot = ['Totais'] + [str(c) for c in contagem] + [str(sem), str(total)]
    return {
        'titulo': 'RESUMO DE PESAGEM POR FAIXA', 'subtitulos': ['Animais na Propriedade pelo último peso (faixas de 50 kg)'],
        'colunas': colunas, 'negrito': [0], 'linhas': [linha, linha_tot], 'total_ultima_linha': True, 'paisagem': True,
        'nota': '"-300" = abaixo de 300 kg; "+300" = de 300 a 349,9 kg; e assim por diante; "+700" = 700 kg ou mais.',
        'vazio': not ativos,
    }


def _rel_10(ativos, hist, faixas, racas, p):
    minimo = p['peso_min']
    itens = []
    for e in ativos.values():
        u = _ultimo(hist, e.sisbov)
        if u is not None and float(u.peso) > minimo:
            itens.append((float(u.peso), e, u))
    itens.sort(key=lambda t: (t[0], t[1].sisbov))
    linhas, pesos = [], []
    for i, (v, e, u) in enumerate(itens, start=1):
        pesos.append(v)
        linhas.append([f'{i}', e.sisbov, e.rfid or '', _data_br(u.data_pesagem), racas.get(e.id_raca, ''), u.lote or e.lote or '',
                       _data_br(e.liberacao_abate), _peso(v)])
    return {
        'titulo': 'PESAGEM POR SELEÇÃO', 'subtitulos': [f'Peso Superior a {_total_txt(minimo)} Kgs.'],
        'colunas': [('Ind', 6, 'c'), ('Sisbov', 16, 'c'), ('RFID', 16, 'c'), ('Pesagem', 11, 'c'), ('Raça', 6, 'c'), ('Lote', 18, 'l'),
                    ('Liberação', 11, 'c'), ('Peso', 8, 'r')],
        'negrito': [1], 'linhas': linhas, 'paisagem': False,
        'totais': [('Total Animais', f'{len(linhas)}'), ('Peso Total', _total_txt(sum(pesos))), ('Média Kgs', _br(_media(pesos)))],
        'vazio': not linhas,
    }


def montar_relatorio(tipo, ativos, hist, faixas, racas, p):
    """Escolhe o construtor do relatorio (funcao pura - facil de testar)."""
    if tipo == '01':
        return _rel_01(ativos, hist, faixas, racas, p)
    if tipo == '02':
        return _rel_02_08(ativos, hist, faixas, racas, p, so_periodo=False)
    if tipo == '03':
        return _rel_03(ativos, hist, faixas, racas, p)
    if tipo == '04':
        return _rel_04(ativos, hist, faixas, racas, p)
    if tipo == '05':
        return _rel_05(ativos, hist, faixas, racas, p)
    if tipo == '06':
        return _rel_06(ativos, hist, faixas, racas, p)
    if tipo == '07':
        return _rel_07(ativos, hist, faixas, racas, p)
    if tipo == '08':
        return _rel_02_08(ativos, hist, faixas, racas, p, so_periodo=True)
    if tipo == '09':
        return _rel_09(ativos, hist, faixas, racas, p)
    return _rel_10(ativos, hist, faixas, racas, p)


# -------------------------------------------------------
# Carga dos dados (banco do Produtor)
# -------------------------------------------------------
def _carregar(db, id_propriedade):
    ip = int(id_propriedade)
    ativos = {e.sisbov: e for e in db.query(Entrada).filter(Entrada.id_propriedade == ip).all()}
    hist = {}
    linhas = (db.query(Peso).join(Entrada, Entrada.sisbov == Peso.sisbov)
              .filter(Peso.id_propriedade == ip, Entrada.id_propriedade == ip)
              .order_by(Peso.sisbov.asc(), Peso.data_pesagem.asc(), Peso.sequencia.asc()).all())
    for x in linhas:
        hist.setdefault(x.sisbov, []).append(x)
    faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
    racas = {r.id: r.codigo for r in db.query(Raca).all()}
    return ativos, hist, faixas, racas


def _lotes_com_quantidade(db, id_propriedade):
    linhas = (db.query(Entrada.lote, func.count(Entrada.id))
              .filter(Entrada.id_propriedade == int(id_propriedade), Entrada.lote.isnot(None), Entrada.lote != '')
              .group_by(Entrada.lote).order_by(Entrada.lote.asc()).all())
    return [{'lote': l, 'qtd': int(q)} for l, q in linhas]


def _negado():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect(URL_INICIAR)
    return redirecionar_home()


def _ler_peso(texto):
    """Peso em kg digitado (aceita virgula). So vale entre 0 e 5.000."""
    try:
        v = float(str(texto).strip().replace(',', '.'))
    except (TypeError, ValueError):
        return None
    return v if 0 < v < 5000 else None


# -------------------------------------------------------
# TELA UNICA
# -------------------------------------------------------
@pesos_relatorios.route('/produtor/pesos-relatorios/iniciar')
def iniciar():
    return _iniciar_generico('Relatórios de Pesagem — Selecionar Propriedade', URL_SELECAO)


@pesos_relatorios.route('/produtor/pesos-relatorios/selecao')
def selecao():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
    try:
        with get_db_produtor(session['id_produtor']) as db_prod:
            lotes = _lotes_com_quantidade(db_prod, id_propriedade)
    except Exception:
        logger.exception('Relatorios de Pesagem: falha ao listar os lotes')
        lotes = []
    hoje = date.today()
    valores = {
        'tipo': request.args.get('tipo', ''),
        'ini': request.args.get('ini') or f'01/01/{hoje.year}',
        'fim': request.args.get('fim') or _data_br(hoje),
        'data': request.args.get('data') or _data_br(hoje),
        'lote': request.args.get('lote', ''),
        'peso_min': request.args.get('peso_min') or '300',
    }
    return render_template(
        'produtor/pesos_relatorios.html',
        propriedade=propriedade, id_propriedade=id_propriedade, lotes=lotes, relatorios=RELATORIOS, v=valores,
        erro=MENSAGENS.get(request.args.get('erro', '')), url_voltar=_volta_hub(),
        usuario_nome=session.get('usuario_nome'), usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A', nome_sistema='Orion SISBOV', menu_ativo='pesagens',
    )


@pesos_relatorios.route('/produtor/pesos-relatorios/pdf')
def pdf():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()

    tipo = (request.args.get('tipo', '') or '').strip()
    filtros = {k: (request.args.get(k, '') or '').strip() for k in ('ini', 'fim', 'data', 'lote', 'peso_min')}

    def volta(erro):
        return redirect(f'{URL_SELECAO}?' + urlencode({'id_propriedade': int(id_propriedade), 'tipo': tipo, 'erro': erro, **filtros}))

    if tipo not in RELATORIOS:
        return volta('tipo')
    _, quer_periodo, quer_lote = RELATORIOS[tipo]
    p = {'lote': filtros['lote']}
    if quer_periodo:
        p['ini'], p['fim'] = _ler_data_br(filtros['ini']), _ler_data_br(filtros['fim'])
        if p['ini'] is None or p['fim'] is None:
            return volta('data')
        if p['ini'] > p['fim']:
            return volta('periodo')
    if quer_lote and not p['lote']:
        return volta('lote')
    if tipo == '06':
        p['data'] = _ler_data_br(filtros['data'])
        if p['data'] is None:
            return volta('data')
    if tipo == '10':
        p['peso_min'] = _ler_peso(filtros['peso_min'])
        if p['peso_min'] is None:
            return volta('peso')

    id_produtor = session['id_produtor']
    try:
        with get_db_produtor(id_produtor) as db:
            ativos, hist, faixas, racas = _carregar(db, id_propriedade)
    except Exception:
        logger.exception('Relatorios de Pesagem: falha ao carregar os dados')
        return volta('vazio')

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
        produtor = db.get(Produtor, id_produtor)
    p['produtor'] = produtor.nome if produtor else ''

    ctx = montar_relatorio(tipo, ativos, hist, faixas, racas, p)
    if ctx.get('vazio'):
        return volta('vazio')
    ctx.update({
        'produtor': p['produtor'], 'propriedade': propriedade.nome if propriedade else '',
        'gerado_em_completo': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
    })
    buffer = gerar_pdf_pesagem_relatorio(ctx)
    lote_txt = ''.join(c if c.isalnum() else '_' for c in p['lote']).strip('_') if (quer_lote and p['lote']) else ''
    partes = [f'Pesagem_{tipo}', NOMES_ARQUIVO[tipo], lote_txt, datetime.now().strftime('%Y-%m-%d')]
    nome = '_'.join(x for x in partes if x) + '.pdf'
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome)

# =========================================================
# FIM DE ARQUIVO: backend\routers\pesos_relatorios.py
# =========================================================
