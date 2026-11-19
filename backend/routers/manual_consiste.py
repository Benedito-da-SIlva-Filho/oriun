# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\Orion\backend\routers
# MODULO: backend\routers\manual_consiste.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-17 22:12 -03
# ATUALIZADO EM: 2026-11-17 22:12 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Abre o Manual (PDF) do Cadastro (Propriedade, Proprietario, Produtor e
#     Ambiente) no HUB Consiste. So o perfil CONSISTE.
#
#       GET /consiste/manual/cadastro                 - abre o manual no inicio
#       GET /consiste/manual/cadastro/<capitulo>      - abre ja no capitulo
#       GET /consiste/manual/cadastro.pdf             - o PDF em si
#
#     O PDF e gerado por C:\Orion\Manual\gerar_manual_cadastro.py, que tambem
#     grava Manual\paginas.json (pagina de cada capitulo).
#
#     v1.0.0: Criacao (Sessao 130).
#     v1.1.0: Manuais separados: GET /consiste/manual/<propriedade|proprietario|produtor> (um PDF so para cada tela).
# =========================================================

import json
import os

from flask import Blueprint, Response, redirect, send_file, session

from backend.routers.auth import redirecionar_home

manual_consiste = Blueprint('manual_consiste', __name__)

PASTA_MANUAL = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Manual'))
ARQUIVO_PDF = os.path.join(PASTA_MANUAL, 'Manual_Cadastro_Propriedade_Produtor_Ambiente.pdf')
ARQUIVO_JSON = os.path.join(PASTA_MANUAL, 'paginas.json')


def _acesso_negado():
    if 'usuario_id' not in session or session.get('usuario_perfil') != 'CONSISTE':
        return redirecionar_home(session.get('usuario_perfil'))
    return None


def _pagina_do_capitulo(capitulo):
    try:
        with open(ARQUIVO_JSON, 'r', encoding='utf-8') as f:
            return int(json.load(f).get(capitulo, 1))
    except Exception:
        return 1


@manual_consiste.route('/consiste/manual/cadastro.pdf')
def manual_pdf():
    negado = _acesso_negado()
    if negado:
        return negado
    if not os.path.exists(ARQUIVO_PDF):
        return Response('O manual ainda nao foi gerado. Rode: python Manual\\gerar_manual_cadastro.py', status=404,
                        mimetype='text/plain; charset=utf-8')
    return send_file(ARQUIVO_PDF, mimetype='application/pdf', as_attachment=False)


@manual_consiste.route('/consiste/manual/cadastro')
@manual_consiste.route('/consiste/manual/cadastro/<capitulo>')
def manual_cadastro(capitulo='antes'):
    negado = _acesso_negado()
    if negado:
        return negado
    return redirect('/consiste/manual/cadastro.pdf#page=%d' % _pagina_do_capitulo(capitulo))


SEPARADOS = {
    'propriedade': 'Manual_Propriedade.pdf',
    'proprietario': 'Manual_Proprietario.pdf',
    'produtor': 'Manual_Produtor.pdf',
}


@manual_consiste.route('/consiste/manual/<nome>')
def manual_separado(nome):
    negado = _acesso_negado()
    if negado:
        return negado
    arquivo = SEPARADOS.get(nome)
    caminho = os.path.join(PASTA_MANUAL, arquivo) if arquivo else ''
    if not arquivo or not os.path.exists(caminho):
        return Response('Manual nao encontrado. Gere com: python Manual\\gerar_manual_cadastro.py', status=404,
                        mimetype='text/plain; charset=utf-8')
    return send_file(caminho, mimetype='application/pdf', as_attachment=False)


# FIM DE ARQUIVO: backend\routers\manual_consiste.py
