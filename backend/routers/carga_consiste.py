# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\Orion\backend\routers
# MODULO: backend\routers\carga_consiste.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-17 18:40 -03
# ATUALIZADO EM: 2026-11-17 18:40 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Tela CONSISTE > Carga de Animais: carga inicial de um Produtor novo a
#     partir do PDF "Extrato de Animais Vivos" do MAPA. So o perfil CONSISTE.
#
#     ROTAS
#       GET  /consiste/carga            - envio do PDF + lista das Cargas feitas
#       POST /consiste/carga/previa     - le o PDF, valida e mostra a Previa (nao grava)
#       POST /consiste/carga/confirmar  - le o PDF guardado de novo, valida e GRAVA tudo
#                                         numa transacao so
#       POST /consiste/carga/desfazer   - desfaz uma Carga (so se nenhum animal teve
#                                         movimento depois)
#
#     SEGURANCA (Regra #73): o navegador so devolve um codigo (token) do arquivo
#     guardado no servidor; na confirmacao o PDF e lido e validado DE NOVO.
#     Nada vem pronto do navegador. Sem Comunicado, PIA, Notificacao ou blockchain.
#     A regra das validacoes e da gravacao mora em backend\utils\carga_animais.py.
#
#     v1.0.0: Criacao (Carga, 17/11/2026).
#     v1.1.0: Arquivo de Conferencia (CSV) na Previa, sem compromisso de Carga (GET /consiste/carga/conferencia).
#     v1.0.1: Erro ao analisar o PDF aparece na tela (e no terminal) em vez de erro 500.
# =========================================================

import hashlib
import os
import re
import csv
import io
import secrets
import time
import traceback
from datetime import date

from flask import Blueprint, Response, render_template, request, session

from sqlalchemy.orm import Session

from backend.database import engine
from backend.leitores import leitor_mapa_extrato_vivos as leitor
from backend.models.produtor import Produtor
from backend.models.propriedade import Propriedade
from backend.routers.auth import redirecionar_home
from backend.utils import carga_animais as ca
from backend.utils.multitenant import get_db_produtor

carga_consiste = Blueprint('carga_consiste', __name__)

PASTA_TEMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'storage', 'carga_tmp')
PADRAO_TOKEN = re.compile(r'^[0-9a-f]{32}$')


def _acesso_negado():
    if 'usuario_id' not in session or session.get('usuario_perfil') != 'CONSISTE':
        return redirecionar_home(session.get('usuario_perfil'))
    return None


def _contexto(**extra):
    base = dict(
        usuario_nome=session.get('usuario_nome'), usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'), nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='carga', mensagem=None, mensagem_tipo=None, previa=None, destino=None, token=None,
        nome_arquivo=None, cargas=[],
    )
    base.update(extra)
    return base


def _caminho_token(token):
    if not token or not PADRAO_TOKEN.match(token):
        return None
    return os.path.normpath(os.path.join(PASTA_TEMP, token + '.pdf'))


def _limpar_antigos():
    """Apaga PDFs temporarios com mais de 1 dia (o arquivo fica guardado para o Confirmar e a Conferencia)."""
    try:
        for nome in os.listdir(PASTA_TEMP):
            c = os.path.join(PASTA_TEMP, nome)
            if nome.endswith('.pdf') and time.time() - os.path.getmtime(c) > 86400:
                os.remove(c)
    except OSError:
        pass


def _apagar_temp(caminho):
    try:
        if caminho and os.path.exists(caminho):
            os.remove(caminho)
    except OSError:
        pass


def _listar_todas_as_cargas():
    """Cargas de todos os Produtores ativos (mais nova primeiro)."""
    saida = []
    with Session(engine) as pub:
        produtores = pub.query(Produtor).filter(Produtor.ativo.is_(True), Produtor.schema_nome.isnot(None)).order_by(Produtor.nome).all()
        nomes_prop = {p.id: p.nome for p in pub.query(Propriedade).all()}
        lista = [(p.id, p.nome) for p in produtores]
    for id_produtor, nome in lista:
        try:
            with get_db_produtor(id_produtor) as db:
                for c in ca.listar_cargas(db):
                    saida.append(dict(c, id_produtor=id_produtor, produtor=nome, propriedade=nomes_prop.get(c['id_propriedade'], '')))
        except Exception:
            continue
    saida.sort(key=lambda c: c['criado_em'] or c['data'], reverse=True)
    return saida


def _analisar(caminho):
    """Le o PDF e valida TUDO (arquivo + banco). Devolve (extrato, previa, destino) ou (None, previa_de_erro, None)."""
    try:
        extrato = leitor.ler(caminho)
    except Exception:
        return None, None, None, None
    cab, animais = extrato['cabecalho'], extrato['animais']
    erros_extra = []
    destino = None
    with Session(engine) as pub:
        racas = ca.racas_do_cadastro(pub)
        produtor, propriedade, vinculo, erros_dest = ca.resolver_destino(pub, cab)
        erros_extra += erros_dest
        if produtor is not None and propriedade is not None and vinculo is not None:
            destino = {'id_produtor': produtor.id, 'produtor': produtor.nome, 'id_propriedade': propriedade.id,
                       'propriedade': propriedade.nome, 'uf': propriedade.uf}
    if len(animais) > ca.MAX_ANIMAIS_CARGA:
        erros_extra.append({'codigo': 'ARQUIVO_GRANDE', 'linha': None, 'sisbov': '',
                            'mensagem': f'O arquivo tem mais de {ca.MAX_ANIMAIS_CARGA} animais.'})
    if destino is not None and not erros_extra:
        with get_db_produtor(destino['id_produtor']) as db:
            erros_extra += ca.erros_do_banco(db, destino['id_propriedade'], animais)
    ca.TITULOS_ERRO.setdefault('ARQUIVO_GRANDE', 'Arquivo grande demais')
    previa = ca.montar_previa(extrato, racas, date.today(), erros_extra=erros_extra)
    erros_f, alertas_f = ca.validar_animais(animais, cab, racas, date.today())
    brutos = {'erros': list(erros_extra) + erros_f, 'alertas': alertas_f, 'racas': racas}
    return extrato, previa, destino, brutos


@carga_consiste.route('/consiste/carga')
def tela():
    negado = _acesso_negado()
    if negado:
        return negado
    return render_template('consiste/consiste_carga.html', **_contexto(cargas=_listar_todas_as_cargas()))


@carga_consiste.route('/consiste/carga/previa', methods=['POST'])
def previa():
    negado = _acesso_negado()
    if negado:
        return negado
    arq = request.files.get('arquivo')
    if arq is None or not arq.filename:
        return render_template('consiste/consiste_carga.html', **_contexto(
            mensagem='Escolha o arquivo PDF do Extrato de Animais Vivos para enviar.', mensagem_tipo='erro', cargas=_listar_todas_as_cargas()))
    conteudo = arq.read()
    if not conteudo.startswith(b'%PDF'):
        return render_template('consiste/consiste_carga.html', **_contexto(
            mensagem='O arquivo enviado não é um PDF. Envie o "Extrato de Animais Vivos" gerado no MAPA.', mensagem_tipo='erro', cargas=_listar_todas_as_cargas()))
    os.makedirs(PASTA_TEMP, exist_ok=True)
    _limpar_antigos()
    token = secrets.token_hex(16)
    caminho = _caminho_token(token)
    with open(caminho, 'wb') as f:
        f.write(conteudo)
    try:
        extrato, prev, destino, brutos = _analisar(caminho)
    except Exception as e:
        traceback.print_exc()
        _apagar_temp(caminho)
        return render_template('consiste/consiste_carga.html', **_contexto(
            mensagem=f'Erro ao analisar o arquivo (nada foi gravado): {type(e).__name__}: {str(e)[:300]}', mensagem_tipo='erro', cargas=[]))
    if extrato is None or prev is None:
        _apagar_temp(caminho)
        return render_template('consiste/consiste_carga.html', **_contexto(
            mensagem='Não consegui ler este PDF. Confira se é o "Extrato de Animais Vivos" do MAPA e tente de novo.', mensagem_tipo='erro', cargas=_listar_todas_as_cargas()))
    return render_template('consiste/consiste_carga.html', **_contexto(
        previa=prev, destino=destino, token=token if prev['pode_gravar'] else None, token_conf=token, cabecalho=extrato['cabecalho'],
        nome_arquivo=arq.filename[:120], cargas=_listar_todas_as_cargas()))


@carga_consiste.route('/consiste/carga/conferencia')
def conferencia():
    """Arquivo de Conferencia (CSV): cada animal lido do PDF com a situacao. Nao grava nada."""
    negado = _acesso_negado()
    if negado:
        return negado
    caminho = _caminho_token(request.args.get('token', ''))
    if caminho is None or not os.path.exists(caminho):
        return render_template('consiste/consiste_carga.html', **_contexto(
            mensagem='O arquivo enviado não está mais disponível. Envie o PDF de novo.', mensagem_tipo='erro', cargas=_listar_todas_as_cargas()))
    try:
        extrato, prev, destino, brutos = _analisar(caminho)
    except Exception as e:
        traceback.print_exc()
        return render_template('consiste/consiste_carga.html', **_contexto(
            mensagem=f'Erro ao gerar a conferência: {type(e).__name__}: {str(e)[:300]}', mensagem_tipo='erro', cargas=[]))
    if extrato is None:
        return render_template('consiste/consiste_carga.html', **_contexto(
            mensagem='Não consegui ler o PDF.', mensagem_tipo='erro', cargas=_listar_todas_as_cargas()))
    cab = extrato['cabecalho']
    por_linha, por_sisbov = {}, {}
    for e in brutos['erros']:
        (por_linha if e['linha'] else por_sisbov).setdefault(e['linha'] or e['sisbov'], []).append(('ERRO', e['mensagem']))
    for a in brutos['alertas']:
        por_linha.setdefault(a['linha'], []).append(('ALERTA', a['mensagem']))
    racas = brutos['racas']
    saida = io.StringIO()
    w = csv.writer(saida, delimiter=';')
    w.writerow(['ARQUIVO DE CONFERÊNCIA DA CARGA (nada foi gravado)'])
    w.writerow(['Produtor no arquivo', cab.get('produtor_nome'), 'CPF/CNPJ', cab.get('produtor_documento')])
    w.writerow(['Propriedade no arquivo', cab.get('propriedade_nome'), 'Cód. MAPA', cab.get('cod_propriedade'), 'Nirf', cab.get('nirf')])
    w.writerow(['Animais lidos', prev['lidos'], 'Fêmeas', prev['femeas'], 'Machos', prev['machos'], 'Erros', prev['qtd_erros'], 'Alertas', prev['qtd_alertas']])
    for g in prev['erros']:
        w.writerow(['ERRO GERAL', g['titulo'], g['qtd']])
    w.writerow([])
    w.writerow(['Linha', 'Página', 'SISBOV', 'DV', 'Nascimento', 'Raça no arquivo', 'Raça (código Orion)', 'Sexo', 'Data Inclusão', 'Situação', 'Observação'])
    for a in extrato['animais']:
        achados = por_linha.get(a['linha'], []) + por_sisbov.get(a['sisbov'], [])
        situacao = 'ERRO' if any(k == 'ERRO' for k, _ in achados) else ('ALERTA' if achados else 'OK')
        r = racas.get(ca.normalizar_nome(a['raca_nome']))
        w.writerow([a['linha'], a['pagina'], a['sisbov'], 'ok' if ca.rs.sisbov_confere(a['sisbov']) else 'INVÁLIDO',
                    a['nascimento_texto'], a['raca_nome'], r[1] if r else 'NÃO CADASTRADA', a['sexo_texto'],
                    a['data_inclusao_texto'], situacao, ' | '.join(m for _, m in achados)])
    return Response('\ufeff' + saida.getvalue(), mimetype='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename=Conferencia_Carga_{date.today():%d-%m-%Y}.csv'})


@carga_consiste.route('/consiste/carga/confirmar', methods=['POST'])
def confirmar():
    negado = _acesso_negado()
    if negado:
        return negado
    token = request.form.get('token', '')
    nome_arquivo = (request.form.get('nome_arquivo') or '')[:120]
    caminho = _caminho_token(token)
    if caminho is None or not os.path.exists(caminho):
        return render_template('consiste/consiste_carga.html', **_contexto(
            mensagem='O arquivo enviado não está mais disponível. Envie o PDF de novo.', mensagem_tipo='erro', cargas=_listar_todas_as_cargas()))
    extrato, prev, destino, brutos = _analisar(caminho)
    if extrato is None or prev is None or not prev['pode_gravar'] or destino is None:
        _apagar_temp(caminho)
        return render_template('consiste/consiste_carga.html', **_contexto(
            previa=prev, destino=destino, cabecalho=extrato['cabecalho'] if extrato else None,
            mensagem='A conferência final encontrou problemas e nada foi gravado. Veja abaixo.' if prev else 'Não consegui ler o PDF. Nada foi gravado.',
            mensagem_tipo='erro', cargas=_listar_todas_as_cargas()))
    with open(caminho, 'rb') as f:
        hash_arquivo = hashlib.sha256(f.read()).hexdigest()
    try:
        with Session(engine) as pub:
            racas = ca.racas_do_cadastro(pub)
            id_especie = ca.id_especie_bovina(pub)
        with get_db_produtor(destino['id_produtor']) as db:
            try:
                id_gta, qtd = ca.gravar_carga(db, destino['id_propriedade'], destino['uf'], extrato['animais'], racas, id_especie,
                                              date.today(), session['usuario_id'], hash_arquivo, nome_arquivo)
                db.commit()
            except Exception:
                db.rollback()
                raise
    except ValueError as e:
        return render_template('consiste/consiste_carga.html', **_contexto(mensagem=str(e), mensagem_tipo='erro', cargas=_listar_todas_as_cargas()))
    except Exception:
        return render_template('consiste/consiste_carga.html', **_contexto(
            mensagem='Não foi possível gravar a Carga e nada foi gravado. Tente de novo; se repetir, avise o suporte.', mensagem_tipo='erro', cargas=_listar_todas_as_cargas()))
    _apagar_temp(caminho)
    return render_template('consiste/consiste_carga.html', **_contexto(
        mensagem=f'Carga concluída: {qtd} animais gravados em {destino["propriedade"]} ({destino["produtor"]}).', mensagem_tipo='ok',
        cargas=_listar_todas_as_cargas()))


@carga_consiste.route('/consiste/carga/desfazer', methods=['POST'])
def desfazer():
    negado = _acesso_negado()
    if negado:
        return negado
    id_produtor = request.form.get('id_produtor', type=int)
    id_gta = request.form.get('id_gta', type=int)
    if not id_produtor or not id_gta:
        return render_template('consiste/consiste_carga.html', **_contexto(mensagem='Carga não informada.', mensagem_tipo='erro', cargas=_listar_todas_as_cargas()))
    try:
        with get_db_produtor(id_produtor) as db:
            try:
                ok, msg = ca.desfazer_carga(db, id_gta)
                if ok:
                    db.commit()
                else:
                    db.rollback()
            except Exception:
                db.rollback()
                raise
    except Exception:
        ok, msg = False, 'Não foi possível desfazer a Carga. Nada foi alterado.'
    return render_template('consiste/consiste_carga.html', **_contexto(mensagem=msg, mensagem_tipo='ok' if ok else 'erro', cargas=_listar_todas_as_cargas()))

# =========================================================
# FIM DE ARQUIVO: backend\routers\carga_consiste.py
# =========================================================
