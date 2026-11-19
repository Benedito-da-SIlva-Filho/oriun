# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\pesos_consulta.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-04 18:40 -03
# ATUALIZADO EM: 2026-11-16 11:20 -03
# VERSAO: 1.2.0
#
# DESCRICAO:
#     Pesos pacote 3 (Sessao 114): CONSULTA (tela) e CONFERIDOS (PDF no visual do Magic). Telas de CONSULTA: nao gravam nada.
#
#     Regras decididas pelo Benedito (04/11/2026):
#       - So importa a DATA DA PESAGEM (dd/mm/aaaa). Sem periodo, sem filtro de lote.
#       - Entram as pesagens da data de TODAS as origens (Leitor, Bastao e brete da Brincagem), mas SO de animais que
#         ainda estao no rebanho (tb_2001) - quem ja saiu (venda, abate, morte, transferencia) nao entra.
#       - Consulta: Seq (ordem de leitura), SISBOV, Manejo, Sexo, Idade em Meses, Raca, Liberacao, Lote, Peso, Ganho, Dias,
#         GMD, Perdeu Elemento. SEM botao Ex (corrigir/excluir so no brete). Resumo final por ERAS (faixa de idade):
#         quantidade, peso medio e GMD medio.
#       - Conferidos: PDF igual a amostra do Magic (Relatorio de Conferencias do dia), quantidade REAL, resumo Femeas/Machos
#         por faixa de idade com Total, Media e Geral. Sem Ganho/GMD.
#
#     ROTAS:
#       /produtor/pesos-consulta/iniciar    - resolve a Propriedade.
#       /produtor/pesos-consulta/lista      - data + tabela + resumo por ERAS (tela).
#       /produtor/pesos-conferidos/iniciar  - resolve a Propriedade.
#       /produtor/pesos-conferidos/selecao  - data + ultimas datas (cada uma abre o PDF).
#       /produtor/pesos-conferidos/pdf      - PDF do dia.
#
#     v1.0.0: Criacao (Sessao 114, 04/11/2026, 18:40 -03).
#     v1.1.0: Sessao 114 (04/11/2026, 18:45 -03) - A data agora e escolhida num COMBO com todas as datas que tem pesagem, da mais recente para a mais antiga (pedido do Benedito). REVERSAO: .bak_antes_s114_combo.
#     REVERSAO: remover este arquivo, pesos_consulta.html, utils\pdf_pesos_conferidos.py, o registro em app.py, os 2 cards do
#     Hub 'pesos' e as 2 linhas de permissoes.py.
#     v1.2.0: Sessao 128 (2026-11-16 11:20 -03) - AUDITORIA ETAPA 7e: erro ao listar as datas vai para o log do servidor; texto de data errada volta codificado (quote) na URL do PDF. REVERSAO: .bak_antes_etapa7e.
# =========================================================

from datetime import datetime
import logging
from urllib.parse import quote

from flask import Blueprint, render_template, request, redirect, session, send_file
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, Produtor, PropriedadeProdutor
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.gta_manual import municipio_sem_uf
from backend.routers.pesos_leitor import _iniciar_generico, ELEMENTOS
from backend.routers.saida_leitor import _propriedade_do_usuario, _data_br, _ler_data_br
from backend.utils.documentos_produtor import documentos_do_produtor
from backend.utils.multitenant import get_db_produtor
from backend.utils.pdf_pesos_conferidos import gerar_pdf_pesos_conferidos

pesos_consulta = Blueprint('pesos_consulta', __name__)
logger = logging.getLogger(__name__)


@pesos_consulta.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


URL_HUB                = '/produtor/hub-novo/pesos'
URL_CONSULTA_INICIAR   = '/produtor/pesos-consulta/iniciar'
URL_CONSULTA_LISTA     = '/produtor/pesos-consulta/lista'
URL_CONFERIDOS_INICIAR = '/produtor/pesos-conferidos/iniciar'
URL_CONFERIDOS_SELECAO = '/produtor/pesos-conferidos/selecao'
URL_CONFERIDOS_PDF     = '/produtor/pesos-conferidos/pdf'

NOMES_ELEMENTO = dict(ELEMENTOS)   # {'BOTTON': 'Botton', 'BRINCO': 'Brinco'}
SEXO_TELA = {'FEMEA': 'Fêmea', 'MACHO': 'Macho'}


def _negado(url_iniciar):
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect(url_iniciar)
    return redirecionar_home()


def _br(valor, casas=2):
    if valor is None:
        return ''
    texto = f'{float(valor):,.{casas}f}'
    return texto.replace(',', '#').replace('.', ',').replace('#', '.')


def _url_voltar(url_iniciar):
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    return url_iniciar if (len(pares) > 1 and resolver_fazenda_em_uso(pares) is None) else URL_HUB


# -------------------------------------------------------
# Pesagens da data (todas as origens) de animais que AINDA estao no rebanho.
# Devolve a lista de dicts e o resumo por faixa de idade (ERAS).
# -------------------------------------------------------
def _montar(db, id_propriedade, data_pesagem):
    ip = int(id_propriedade)
    linhas = (
        db.query(Peso, Entrada)
        .join(Entrada, Entrada.sisbov == Peso.sisbov)
        .filter(Peso.id_propriedade == ip, Peso.data_pesagem == data_pesagem, Entrada.id_propriedade == ip)
        .order_by(Peso.id.asc())
        .all()
    )
    faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
    racas = {r.id: r.codigo for r in db.query(Raca).all()}
    sisbovs = [p.sisbov for p, _ in linhas]
    datas_anteriores = {}
    if sisbovs:
        for s, seq, d in db.query(Peso.sisbov, Peso.sequencia, Peso.data_pesagem).filter(
                Peso.id_propriedade == ip, Peso.sisbov.in_(sisbovs)).all():
            datas_anteriores[(s, seq)] = d

    animais = []
    for ordem, (p, e) in enumerate(linhas, start=1):
        if e.nascimento:
            dias_idade = (data_pesagem - e.nascimento).days
        else:
            dias_idade = p.eras_dias
        faixa = ''
        if dias_idade is not None:
            for f in faixas:
                if f.dias_min <= dias_idade <= f.dias_max:
                    faixa = f.descricao
                    break
        anterior = datas_anteriores.get((p.sisbov, (p.sequencia or 0) - 1))
        dias = (data_pesagem - anterior).days if anterior else None
        ganho = float(p.ganho_peso) if p.ganho_peso is not None else None
        gmd = (ganho / dias) if (ganho is not None and dias and dias > 0) else None
        sexo = str(e.sexo.value if hasattr(e.sexo, 'value') else (e.sexo or ''))
        animais.append({
            'seq': ordem,
            'sisbov': p.sisbov,
            'manejo': e.manejo or '',
            'sexo': sexo,
            'nascimento': e.nascimento,
            'faixa': faixa,
            'raca': racas.get(e.id_raca, ''),
            'liberacao': e.liberacao_abate,
            'lote': p.lote or e.lote or '',
            'peso': float(p.peso),
            'ganho': ganho,
            'dias': dias,
            'gmd': gmd,
            'elemento': NOMES_ELEMENTO.get(p.elemento_perdido or '', ''),
        })

    # Resumo por ERAS (faixa de idade): quantidade, peso medio e GMD medio.
    por_faixa = {}
    for a in animais:
        item = por_faixa.setdefault(a['faixa'] or 'Sem faixa', {'qtd': 0, 'peso': 0.0, 'gmds': []})
        item['qtd'] += 1
        item['peso'] += a['peso']
        if a['gmd'] is not None:
            item['gmds'].append(a['gmd'])
    ordem_faixas = [f.descricao for f in faixas] + ['Sem faixa']
    resumo_eras = []
    for nome in ordem_faixas:
        item = por_faixa.get(nome)
        if not item:
            continue
        resumo_eras.append({
            'faixa': nome, 'qtd': item['qtd'], 'peso_medio': item['peso'] / item['qtd'],
            'gmd_medio': (sum(item['gmds']) / len(item['gmds'])) if item['gmds'] else None,
        })
    total = len(animais)
    peso_total = sum(a['peso'] for a in animais)
    todos_gmd = [a['gmd'] for a in animais if a['gmd'] is not None]
    return {
        'animais': animais,
        'faixas': [f.descricao for f in faixas],
        'resumo_eras': resumo_eras,
        'total': total,
        'peso_total': peso_total,
        'peso_medio': (peso_total / total) if total else None,
        'gmd_medio': (sum(todos_gmd) / len(todos_gmd)) if todos_gmd else None,
    }


def _datas_recentes(db, id_propriedade):
    linhas = (
        db.query(Peso.data_pesagem, func.count(Peso.id))
        .filter(Peso.id_propriedade == int(id_propriedade))
        .group_by(Peso.data_pesagem)
        .order_by(Peso.data_pesagem.desc())
        .all()   # v1.1.0 - todas as datas, mais recentes primeiro (vai para o combo)
    )
    return [{'data': _data_br(d), 'quantidade': int(q)} for d, q in linhas]


def _tela(modo, id_propriedade, url_iniciar, **extra):
    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
    try:
        with get_db_produtor(session['id_produtor']) as db_prod:
            recentes = _datas_recentes(db_prod, id_propriedade)
    except Exception:
        logger.exception('Pesos Consulta: falha ao listar as datas com pesagem')
        recentes = []
    return render_template(
        'produtor/pesos_consulta.html',
        modo=modo, propriedade=propriedade, id_propriedade=id_propriedade, recentes=recentes,
        url_voltar=_url_voltar(url_iniciar),
        usuario_nome=session.get('usuario_nome'), usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A', nome_sistema='Orion SISBOV', menu_ativo='pesagens',
        **extra,
    )


# -------------------------------------------------------
# CONSULTA (tela)
# -------------------------------------------------------
@pesos_consulta.route('/produtor/pesos-consulta/iniciar')
def consulta_iniciar():
    return _iniciar_generico('Consulta de Peso — Selecionar Propriedade', URL_CONSULTA_LISTA)


@pesos_consulta.route('/produtor/pesos-consulta/lista')
def consulta_lista():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado(URL_CONSULTA_INICIAR)

    texto = (request.args.get('data', '') or '').strip()
    data = _ler_data_br(texto) if texto else None
    erro = 'Data incorreta. Digite no formato dd/mm/aaaa.' if (texto and data is None) else None
    rel = None
    if data is not None:
        with get_db_produtor(session['id_produtor']) as db:
            rel = _montar(db, id_propriedade, data)
        rel['peso_total_txt'] = _br(rel['peso_total'])
        rel['peso_medio_txt'] = _br(rel['peso_medio'])
        rel['gmd_medio_txt'] = _br(rel['gmd_medio'], 3)
        for a in rel['animais']:
            a['sexo_txt'] = SEXO_TELA.get(a['sexo'], a['sexo'])
            a['liberacao_txt'] = _data_br(a['liberacao']) if a['liberacao'] else ''
            a['peso_txt'] = _br(a['peso'])
            a['ganho_txt'] = _br(a['ganho'])
            a['gmd_txt'] = _br(a['gmd'], 3)
            a['dias_txt'] = '' if a['dias'] is None else str(a['dias'])
        for r in rel['resumo_eras']:
            r['peso_medio_txt'] = _br(r['peso_medio'])
            r['gmd_medio_txt'] = _br(r['gmd_medio'], 3)
    return _tela('consulta', id_propriedade, URL_CONSULTA_INICIAR, erro=erro, filtro=texto, rel=rel)


# -------------------------------------------------------
# CONFERIDOS (PDF)
# -------------------------------------------------------
@pesos_consulta.route('/produtor/pesos-conferidos/iniciar')
def conferidos_iniciar():
    return _iniciar_generico('Conferidos dos Pesos — Selecionar Propriedade', URL_CONFERIDOS_SELECAO)


@pesos_consulta.route('/produtor/pesos-conferidos/selecao')
def conferidos_selecao():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado(URL_CONFERIDOS_INICIAR)
    erro = {'data': 'Data incorreta. Digite no formato dd/mm/aaaa.',
            'vazio': 'Nenhum animal pesado nesta data (ou os pesados já saíram da Propriedade).'}.get(request.args.get('erro', ''))
    return _tela('conferidos', id_propriedade, URL_CONFERIDOS_INICIAR, erro=erro, filtro=request.args.get('data', ''), rel=None)


@pesos_consulta.route('/produtor/pesos-conferidos/pdf')
def conferidos_pdf():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado(URL_CONFERIDOS_INICIAR)

    texto = (request.args.get('data', '') or '').strip()
    data = _ler_data_br(texto)
    volta = f'{URL_CONFERIDOS_SELECAO}?id_propriedade={int(id_propriedade)}'
    if data is None:
        return redirect(f'{volta}&erro=data&data={quote(texto)}')

    id_produtor = session['id_produtor']
    with get_db_produtor(id_produtor) as db:
        rel = _montar(db, id_propriedade, data)
    if not rel['animais']:
        return redirect(f'{volta}&erro=vazio&data={quote(texto)}')

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
        produtor = db.get(Produtor, id_produtor)
        vinculo = None
        if produtor is not None:
            vinculo = (db.query(PropriedadeProdutor)
                       .filter_by(id_propriedade=int(id_propriedade), id_produtor=produtor.id, data_fim=None).first())
        cpf, cnpj = documentos_do_produtor(produtor, vinculo)
        inscricao = (getattr(vinculo, 'inscricao_estadual', None) or getattr(propriedade, 'inscricao_estadual', None)
                     or '') if propriedade is not None else ''
        cabecalho = {
            'produtor': produtor.nome if produtor else '',
            'cpf': cpf, 'cnpj': cnpj, 'inscricao_estadual': inscricao,
            'codigo_eras': propriedade.codigo_eras if propriedade else '',
            'propriedade': propriedade.nome if propriedade else '',
            'municipio': municipio_sem_uf(propriedade.municipio, propriedade.uf) if propriedade else '',
            'uf': propriedade.uf if propriedade else '',
            'cep': (getattr(propriedade, 'cep', None) or '') if propriedade else '',
        }

    # Conferidos: ordem do SISBOV (como na amostra); sem Ganho/GMD.
    animais_pdf = []
    resumo = {'FEMEA': {'qtd': [0] * len(rel['faixas']), 'total': 0, 'peso': 0.0},
              'MACHO': {'qtd': [0] * len(rel['faixas']), 'total': 0, 'peso': 0.0}}
    for a in sorted(rel['animais'], key=lambda x: x['sisbov']):
        animais_pdf.append({
            'sisbov': a['sisbov'], 'manejo': a['manejo'], 'sexo': a['sexo'],
            'nascimento': _data_br(a['nascimento']) if a['nascimento'] else '',
            'faixa': a['faixa'], 'raca': a['raca'], 'elemento': a['elemento'], 'peso': a['peso'],
        })
        if a['sexo'] in resumo:
            resumo[a['sexo']]['total'] += 1
            resumo[a['sexo']]['peso'] += a['peso']
            if a['faixa'] in rel['faixas']:
                resumo[a['sexo']]['qtd'][rel['faixas'].index(a['faixa'])] += 1

    ctx = dict(cabecalho)
    ctx.update({
        'data': _data_br(data),
        'gerado_em_completo': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'animais': animais_pdf, 'faixas': rel['faixas'], 'resumo': resumo,
        'peso_total': rel['peso_total'], 'peso_medio': rel['peso_medio'], 'total': rel['total'],
    })
    buffer = gerar_pdf_pesos_conferidos(ctx)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                     download_name=f'Conferencias_Pesos_{data.strftime("%Y-%m-%d")}.pdf')

# =========================================================
# FIM DE ARQUIVO: backend\routers\pesos_consulta.py
# =========================================================
