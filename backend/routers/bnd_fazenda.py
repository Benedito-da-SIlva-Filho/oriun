# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\Orion\backend\routers
# MODULO: backend\routers\bnd_fazenda.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-18 20:00 -03
# ATUALIZADO EM: 2026-11-18 20:00 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     BND/Fazenda do PRODUTOR (card no Hub de Entrada, aba Consultas e Correcoes): o Produtor envia o PDF do
#     "Extrato de Animais Vivos" e recebe 4 relatorios em PDF comparando a BND (MAPA) com os animais em estoque.
#     SOMENTE LEITURA: nao corrige nada (a Correcao e so da Consiste: ver bnd_fazenda_consiste.py) e NAO guarda o
#     resultado. O PDF enviado fica guardado so por 1 dia numa pasta temporaria, para baixar os 4 relatorios.
#     Extrato com varios Produtores: pega so a parte do Produtor logado (pelo CPF/CNPJ).
#
#     ROTAS
#       GET  /produtor/bnd-fazenda/iniciar              - escolhe a Propriedade (se houver mais de uma)
#       GET  /produtor/bnd-fazenda?id_propriedade=X     - tela de envio do Extrato
#       POST /produtor/bnd-fazenda/comparar             - le o PDF e mostra os numeros + 4 botoes de download
#       GET  /produtor/bnd-fazenda/relatorio/<1..4>?token=T&id_propriedade=X - o PDF do relatorio
#
#     SEGURANCA (Regra #73): toda rota confere o id_propriedade (do usuario e da fazenda em uso). O token so aponta
#     para o arquivo do PROPRIO Produtor/Propriedade (o nome do arquivo no servidor leva os dois ids da sessao).
#
#   v1.0.0: Criacao (BND/Fazenda, Sessao 132, 18/11/2026).
# =========================================================

import os
import re
import secrets
import time
import traceback

from flask import Blueprint, redirect, render_template, request, send_file, session
from sqlalchemy.orm import Session

from backend.database import engine
from backend.leitores import leitor_mapa_extrato_vivos as leitor
from backend.models import Produtor, Propriedade, PropriedadeProdutor
from backend.routers.auth import buscar_pares_propriedade_produtor, redirecionar_home, resolver_fazenda_em_uso
from backend.utils import bnd_fazenda as bf
from backend.utils import carga_animais as ca
from backend.utils import pdf_bnd_fazenda as pdf
from backend.utils.documentos_produtor import documentos_do_produtor
from backend.utils.multitenant import get_db_produtor

bnd_fazenda = Blueprint('bnd_fazenda', __name__)

VOLTAR_HUB = '/produtor/hub-novo/entrada'
URL_INICIAR = '/produtor/bnd-fazenda/iniciar'
PASTA_TEMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'storage', 'bnd_fazenda_tmp')
PADRAO_TOKEN = re.compile(r'^[0-9a-f]{32}$')


def _contexto(**extra):
    base = dict(
        usuario_nome=session.get('usuario_nome'), usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'), nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada', voltar=VOLTAR_HUB, id_propriedade=None, mensagem=None, resultado=None, token=None,
        nome_arquivo=None, dados=None,
    )
    base.update(extra)
    return base


def _tela_selecao(pares, erro=None):
    return render_template(
        'produtor/selecionar_propriedade_produtor.html', pares=pares, erro=erro,
        titulo='BND/Fazenda — Selecionar Propriedade', proximo='/produtor/bnd-fazenda',
        campo_propriedade='id_propriedade', voltar=VOLTAR_HUB,
        usuario_nome=session.get('usuario_nome'), usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A', nome_sistema='Orion SISBOV', menu_ativo='entrada')


def _propriedade_valida(valor):
    """Regra #73: o numero existe, e do Produtor logado e e a fazenda em uso. Devolve int ou None."""
    if 'id_produtor' not in session:
        return None
    valor = str(valor or '')
    if not valor.isdecimal():
        return None
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if int(valor) not in {int(p.id_propriedade) for p in pares if str(p.id_produtor) == str(session.get('id_produtor'))}:
        return None
    em_uso = resolver_fazenda_em_uso(pares)
    if em_uso is not None and int(em_uso.id_propriedade) != int(valor):
        return None
    return int(valor)


def _caminho_token(token, id_propriedade):
    if not token or not PADRAO_TOKEN.match(token):
        return None
    nome = f'{int(session["id_produtor"])}_{int(id_propriedade)}_{token}.pdf'
    return os.path.normpath(os.path.join(PASTA_TEMP, nome))


def _limpar_antigos():
    try:
        for nome in os.listdir(PASTA_TEMP):
            c = os.path.join(PASTA_TEMP, nome)
            if nome.endswith('.pdf') and time.time() - os.path.getmtime(c) > 86400:
                os.remove(c)
    except OSError:
        pass


def _analisar(caminho, id_propriedade):
    """Le o PDF e compara. Devolve (resultado, None) ou (None, mensagem de erro)."""
    id_produtor = int(session['id_produtor'])
    try:
        partes = leitor.ler_partes(caminho)
    except Exception:
        traceback.print_exc()
        return None, 'Não consegui ler este PDF. Confira se é o "Extrato de Animais Vivos" gerado pela Certificadora (sem converter) e tente de novo.'
    if not partes or not any(p['animais'] for p in partes):
        return None, 'Não encontrei animais neste PDF. Confira se é o "Extrato de Animais Vivos" gerado pela Certificadora.'
    with Session(engine) as pub:
        produtor = pub.get(Produtor, id_produtor)
        propriedade = pub.get(Propriedade, id_propriedade)
        if produtor is None or propriedade is None:
            return None, 'Produtor ou Propriedade não encontrados.'
        vinculo = pub.query(PropriedadeProdutor).filter_by(id_propriedade=id_propriedade, id_produtor=id_produtor, data_fim=None).first()
        cpf, cnpj = documentos_do_produtor(produtor, vinculo)
        racas = ca.racas_do_cadastro(pub)
        dados = {'prod_nome': produtor.nome, 'prop_nome': propriedade.nome}
        parte = bf.escolher_parte(partes, (cpf, cnpj))
        if parte is None:
            nomes = ', '.join(sorted({str(p['cabecalho'].get('produtor_nome') or '?') for p in partes}))
            return None, f'Este Extrato não traz animais do Produtor {produtor.nome}. Produtores no arquivo: {nomes}.'
        if not bf.propriedade_confere(propriedade, parte['cabecalho']):
            return None, (f'Este Extrato é da Propriedade "{parte["cabecalho"].get("propriedade_nome")}" '
                          f'(Cód. {parte["cabecalho"].get("cod_propriedade")}), e não de {propriedade.nome}.')
    racas_id = bf.racas_por_id(racas)
    with get_db_produtor(id_produtor) as db:
        fazenda = bf.ler_fazenda(db, id_propriedade)
        comp = bf.comparar(fazenda, parte['animais'], racas, racas_id)
        eventos = bf.eventos_orion(db, comp['so_bnd'])
    return {'dados': dados, 'comp': comp, 'eventos': eventos, 'resumo': bf.resumo_comparacao(comp),
            'nao_lidas': len(parte['linhas_nao_lidas']), 'qtd_extrato': len(parte['animais'])}, None


@bnd_fazenda.route('/produtor/bnd-fazenda/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if not pares:
        return _tela_selecao([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')
    par = resolver_fazenda_em_uso(pares)
    if par is None and len(pares) == 1:
        par = pares[0]
    if par is not None:
        session['id_produtor'] = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/bnd-fazenda?id_propriedade={par.id_propriedade}')
    return _tela_selecao(pares)


@bnd_fazenda.route('/produtor/bnd-fazenda')
def tela():
    id_propriedade = _propriedade_valida(request.args.get('id_propriedade'))
    if id_propriedade is None:
        return redirect(URL_INICIAR)
    return render_template('produtor/bnd_fazenda.html', **_contexto(id_propriedade=id_propriedade))


@bnd_fazenda.route('/produtor/bnd-fazenda/comparar', methods=['POST'])
def comparar():
    id_propriedade = _propriedade_valida(request.form.get('id_propriedade'))
    if id_propriedade is None:
        return redirect(URL_INICIAR)
    ctx = dict(id_propriedade=id_propriedade)
    arq = request.files.get('arquivo')
    if arq is None or not arq.filename:
        return render_template('produtor/bnd_fazenda.html', **_contexto(mensagem='Escolha o arquivo PDF do Extrato de Animais Vivos.', **ctx))
    conteudo = arq.read()
    if not conteudo.startswith(b'%PDF'):
        return render_template('produtor/bnd_fazenda.html', **_contexto(
            mensagem='O arquivo enviado não é um PDF. Envie o "Extrato de Animais Vivos" como a Certificadora mandou.', **ctx))
    os.makedirs(PASTA_TEMP, exist_ok=True)
    _limpar_antigos()
    token = secrets.token_hex(16)
    caminho = _caminho_token(token, id_propriedade)
    with open(caminho, 'wb') as f:
        f.write(conteudo)
    try:
        resultado, erro = _analisar(caminho, id_propriedade)
    except Exception as e:
        traceback.print_exc()
        resultado, erro = None, f'Erro ao comparar (nada foi alterado): {type(e).__name__}: {str(e)[:200]}'
    if erro:
        try:
            os.remove(caminho)
        except OSError:
            pass
        return render_template('produtor/bnd_fazenda.html', **_contexto(mensagem=erro, **ctx))
    return render_template('produtor/bnd_fazenda.html', **_contexto(
        resultado=resultado['resumo'], dados=resultado['dados'], token=token, nome_arquivo=arq.filename[:120],
        nao_lidas=resultado['nao_lidas'], qtd_extrato=resultado['qtd_extrato'], **ctx))


@bnd_fazenda.route('/produtor/bnd-fazenda/relatorio/<int:numero>')
def relatorio(numero):
    id_propriedade = _propriedade_valida(request.args.get('id_propriedade'))
    if id_propriedade is None or numero not in (1, 2, 3, 4):
        return redirect(URL_INICIAR)
    caminho = _caminho_token(request.args.get('token', ''), id_propriedade)
    if caminho is None or not os.path.exists(caminho):
        return render_template('produtor/bnd_fazenda.html', **_contexto(
            id_propriedade=id_propriedade, mensagem='O arquivo enviado não está mais disponível. Envie o PDF de novo.'))
    try:
        resultado, erro = _analisar(caminho, id_propriedade)
    except Exception as e:
        traceback.print_exc()
        resultado, erro = None, f'Erro ao gerar o relatório: {type(e).__name__}: {str(e)[:200]}'
    if erro:
        return render_template('produtor/bnd_fazenda.html', **_contexto(id_propriedade=id_propriedade, mensagem=erro))
    comp, dados = resultado['comp'], resultado['dados']
    if numero == 1:
        buffer = pdf.montar_codigos(1, dados, comp['igual'])
    elif numero == 2:
        buffer = pdf.montar_codigos(2, dados, comp['so_fazenda'])
    elif numero == 3:
        buffer = pdf.montar_bnd_nao_fazenda(dados, comp['so_bnd'], resultado['eventos'])
    else:
        buffer = pdf.montar_inconformidades(dados, comp['inconformidades'])
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=pdf.nome_arquivo(numero, dados))

# =========================================================
# FIM DE ARQUIVO: backend\routers\bnd_fazenda.py
# =========================================================
