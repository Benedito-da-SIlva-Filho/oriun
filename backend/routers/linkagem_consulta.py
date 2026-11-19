# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\linkagem_consulta.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-10 21:35 -03
# ATUALIZADO EM: 2026-11-17 11:30 -03
# VERSAO: 1.2.0
#
# DESCRICAO:
#     Linkagem RFID e Brinco - pacote 2 (Sessao 120): CONSULTA dos pares por data, RELATORIO (PDF no visual do Magic) e lista de
#     INCONFORMIDADES. Telas de CONSULTA: nao gravam nada.
#
#     ROTAS:
#       /produtor/linkagem-consulta/iniciar    - resolve a Propriedade.
#       /produtor/linkagem-consulta/lista      - combo com as datas que tem linkagem + tabela dos pares da data + botao PDF.
#       /produtor/linkagem-consulta/pdf        - PDF "Relatorio da Linkagem RFID e Brinco do dia".
#       /produtor/linkagem-inconformes/iniciar - resolve a Propriedade.
#       /produtor/linkagem-inconformes/lista   - tentativas recusadas (tb_4008), da mais nova para a mais antiga, filtro opcional por dia.
#
#     Base: tb_4009_linkagem (um par por linha). Manejo, Sexo, Raca vem do animal em tb_2001; quem ja saiu do rebanho aparece so com
#     SISBOV/RFID/Lote/Peso gravados na hora. Permissao: segmentos 'linkagem-consulta' e 'linkagem-inconformes' = modulo 'entrada'
#     (fora de TELAS_DE_LANCAMENTO, quem so consulta nao e bloqueado).
#
#     v1.0.0: Criacao (Sessao 120, 10/11/2026, 21:35 -03). REVERSAO: remover este arquivo, pdf_linkagem.py, os 2 templates, o registro em
#     app.py, os 2 cards do Hub de Entrada e as 2 linhas de permissoes.py.
#     v1.1.0: Sessao 128 (2026-11-16 11:20 -03) - AUDITORIA ETAPA 7e: erros de consulta vao para o log do servidor; mensagem de erro com norte para o usuario (sem falar em script do banco); texto de data errada volta codificado (quote) na URL do PDF. REVERSAO: .bak_antes_etapa7e.
#     v1.2.0: Sessao 129 (2026-11-17 11:30 -03) - _montar calcula Peso Total, Media (so animais com peso) e quantos ficaram sem peso; o PDF imprime no quadro final. REVERSAO: .bak_antes_s129_peso_total.
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
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4008_linkagem_inconformes import LinkagemInconforme
from backend.models.tb_4009_linkagem import Linkagem
from backend.models.usuario import Usuario
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.gta_manual import municipio_sem_uf
from backend.routers.saida_leitor import _propriedade_do_usuario, _data_br, _ler_data_br
from backend.utils.documentos_produtor import documentos_do_produtor
from backend.utils.multitenant import get_db_produtor
from backend.utils.pdf_linkagem import gerar_pdf_linkagem

linkagem_consulta = Blueprint('linkagem_consulta', __name__)
logger = logging.getLogger(__name__)


@linkagem_consulta.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


URL_HUB                 = '/produtor/hub-novo/entrada'
URL_CONSULTA_INICIAR    = '/produtor/linkagem-consulta/iniciar'
URL_CONSULTA_LISTA      = '/produtor/linkagem-consulta/lista'
URL_INCONF_INICIAR      = '/produtor/linkagem-inconformes/iniciar'
URL_INCONF_LISTA        = '/produtor/linkagem-inconformes/lista'
LIMITE_INCONFORMES = 300
SEXO_TELA = {'FEMEA': 'Fêmea', 'MACHO': 'Macho'}


def _contexto_tela():
    return {
        'usuario_nome':   session.get('usuario_nome'),
        'usuario_perfil': session.get('usuario_perfil'),
        'cor_primaria':   session.get('cor_primaria', '#D4370A'),
        'nome_sistema':   session.get('nome_sistema', 'Orion SISBOV'),
        'menu_ativo':     'entrada',
    }


def _negado(url_iniciar):
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect(url_iniciar)
    return redirecionar_home()


def _url_voltar(url_iniciar):
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    return url_iniciar if (len(pares) > 1 and resolver_fazenda_em_uso(pares) is None) else URL_HUB


def _br(valor, casas=2):
    if valor is None:
        return ''
    texto = f'{float(valor):,.{casas}f}'
    return texto.replace(',', '#').replace('.', ',').replace('#', '.')


def _iniciar(titulo, proximo, url_iniciar):
    if 'id_produtor' not in session:
        return redirecionar_home()
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{proximo}?id_propriedade={par_em_uso.id_propriedade}')
    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{proximo}?id_propriedade={par.id_propriedade}')
    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None if pares else 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
        titulo=titulo, proximo=proximo, campo_propriedade='id_propriedade', voltar=URL_HUB,
        **_contexto_tela(),
    )


# -------------------------------------------------------
# Pares ligados na data, na ordem em que foram gravados
# -------------------------------------------------------
def _montar(db, id_propriedade, data):
    ip = int(id_propriedade)
    linhas = (
        db.query(Linkagem)
        .filter(Linkagem.id_propriedade == ip, Linkagem.data_linkagem == data)
        .order_by(Linkagem.id.asc())
        .all()
    )
    sisbovs = [l.sisbov for l in linhas]
    animais = {}
    if sisbovs:
        for e in db.query(Entrada).filter(Entrada.id_propriedade == ip, Entrada.sisbov.in_(sisbovs)).all():
            animais[e.sisbov] = e
    racas = {r.id: r.codigo for r in db.query(Raca).all()}

    itens = []
    femeas = machos = 0
    for ordem, l in enumerate(linhas, start=1):
        e = animais.get(l.sisbov)
        sexo = ''
        if e is not None:
            sexo = str(e.sexo.value if hasattr(e.sexo, 'value') else (e.sexo or ''))
        if sexo == 'FEMEA':
            femeas += 1
        elif sexo == 'MACHO':
            machos += 1
        itens.append({
            'seq': ordem, 'sisbov': l.sisbov, 'rfid': l.rfid,
            'manejo': (e.manejo or '') if e is not None else '',
            'sexo': sexo, 'raca': racas.get(e.id_raca, '') if e is not None else '',
            'lote': l.lote or ((e.lote or '') if e is not None else ''),
            'peso': float(l.peso) if l.peso is not None else None,
            'hora': l.hora_linkagem.strftime('%H:%M') if l.hora_linkagem else '',
        })
    # v1.2.0: Peso Total e Media so dos animais que foram pesados na Linkagem
    pesos = [i['peso'] for i in itens if i['peso'] is not None]
    peso_total = sum(pesos) if pesos else None
    peso_medio = (peso_total / len(pesos)) if pesos else None
    return {'animais': itens, 'total': len(itens), 'femeas': femeas, 'machos': machos,
            'peso_total': peso_total, 'peso_medio': peso_medio, 'sem_peso': len(itens) - len(pesos)}


def _datas(db, id_propriedade):
    linhas = (
        db.query(Linkagem.data_linkagem, func.count(Linkagem.id))
        .filter(Linkagem.id_propriedade == int(id_propriedade))
        .group_by(Linkagem.data_linkagem)
        .order_by(Linkagem.data_linkagem.desc())
        .all()
    )
    return [{'data': _data_br(d), 'quantidade': int(q)} for d, q in linhas]


# -------------------------------------------------------
# CONSULTA (tela)
# -------------------------------------------------------
@linkagem_consulta.route('/produtor/linkagem-consulta/iniciar')
def consulta_iniciar():
    return _iniciar('Consulta da Linkagem — Selecionar Propriedade', URL_CONSULTA_LISTA, URL_CONSULTA_INICIAR)


@linkagem_consulta.route('/produtor/linkagem-consulta/lista')
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
    erro = {'data': 'Data incorreta. Digite no formato dd/mm/aaaa.',
            'vazio': 'Nenhuma linkagem nesta data.'}.get(request.args.get('erro', ''))
    if texto and data is None:
        erro = 'Data incorreta. Digite no formato dd/mm/aaaa.'

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
    rel = None
    try:
        with get_db_produtor(session['id_produtor']) as db:
            recentes = _datas(db, id_propriedade)
            if data is not None:
                rel = _montar(db, id_propriedade, data)
                for a in rel['animais']:
                    a['sexo_txt'] = SEXO_TELA.get(a['sexo'], a['sexo'])
                    a['peso_txt'] = _br(a['peso'])
    except Exception:
        logger.exception('Linkagem Consulta: falha ao consultar os pares')
        recentes = []
        erro = erro or 'Não foi possível consultar a Linkagem agora. Tente de novo; se repetir, avise a Consiste.'

    return render_template(
        'produtor/linkagem_consulta.html',
        erro=erro, propriedade=propriedade, id_propriedade=id_propriedade, recentes=recentes,
        filtro=texto, rel=rel, url_voltar=_url_voltar(URL_CONSULTA_INICIAR), **_contexto_tela(),
    )


# -------------------------------------------------------
# RELATORIO (PDF)
# -------------------------------------------------------
@linkagem_consulta.route('/produtor/linkagem-consulta/pdf')
def consulta_pdf():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado(URL_CONSULTA_INICIAR)

    texto = (request.args.get('data', '') or '').strip()
    data = _ler_data_br(texto)
    volta = f'{URL_CONSULTA_LISTA}?id_propriedade={int(id_propriedade)}'
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

    ctx = dict(cabecalho)
    ctx.update({
        'data': _data_br(data),
        'gerado_em_completo': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'animais': rel['animais'], 'femeas': rel['femeas'], 'machos': rel['machos'], 'total': rel['total'],
        'peso_total': rel['peso_total'], 'peso_medio': rel['peso_medio'], 'sem_peso': rel['sem_peso'],
    })
    buffer = gerar_pdf_linkagem(ctx)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                     download_name=f'Linkagem_RFID_{data.strftime("%Y-%m-%d")}.pdf')


# -------------------------------------------------------
# INCONFORMIDADES (tela): tentativas recusadas, da mais nova para a mais antiga
# -------------------------------------------------------
@linkagem_consulta.route('/produtor/linkagem-inconformes/iniciar')
def inconformes_iniciar():
    return _iniciar('Inconformidades da Linkagem — Selecionar Propriedade', URL_INCONF_LISTA, URL_INCONF_INICIAR)


@linkagem_consulta.route('/produtor/linkagem-inconformes/lista')
def inconformes_lista():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado(URL_INCONF_INICIAR)

    filtro_txt = (request.args.get('data', '') or '').strip()
    filtro = _ler_data_br(filtro_txt) if filtro_txt else None
    erro = 'Data incorreta. Digite no formato dd/mm/aaaa.' if (filtro_txt and filtro is None) else None

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))

    itens_brutos = []
    total = 0
    try:
        with get_db_produtor(session['id_produtor']) as db:
            q = db.query(LinkagemInconforme).filter(LinkagemInconforme.id_propriedade == int(id_propriedade))
            if filtro is not None:
                q = q.filter(func.date(LinkagemInconforme.criado_em) == filtro)
            total = q.count()
            linhas = q.order_by(LinkagemInconforme.id.desc()).limit(LIMITE_INCONFORMES).all()
            itens_brutos = [{
                'quando': l.criado_em.strftime('%d/%m/%Y %H:%M') if l.criado_em else '',
                'rfid': l.rfid or '', 'sisbov': l.sisbov or '', 'motivo': l.motivo or '',
                'id_usuario': l.id_usuario,
            } for l in linhas]
    except Exception:
        logger.exception('Linkagem Inconformidades: falha ao consultar')
        erro = erro or 'Não foi possível consultar as Inconformidades agora. Tente de novo; se repetir, avise a Consiste.'

    ids = {i['id_usuario'] for i in itens_brutos if i['id_usuario']}
    nomes = {}
    if ids:
        with Session(engine) as db:
            nomes = {i: n for i, n in db.query(Usuario.id, Usuario.nome).filter(Usuario.id.in_(ids)).all()}
    for i in itens_brutos:
        i['usuario'] = nomes.get(i['id_usuario'], '')

    return render_template(
        'produtor/linkagem_inconformes_lista.html',
        erro=erro, propriedade=propriedade, id_propriedade=id_propriedade, filtro=filtro_txt,
        itens=itens_brutos, total=total, limite=LIMITE_INCONFORMES,
        url_voltar=_url_voltar(URL_INCONF_INICIAR), **_contexto_tela(),
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\linkagem_consulta.py
# =========================================================
