# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\morte_relatorios.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-01 19:20 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.2.0
# v1.2.0: Sessao 123 (2026-11-13 20:10 -03) - AUDITORIA ETAPA 6 (leitura a fundo): PDF do Controle sem Controle/animais avisa na lista (faixa amarela, #69). REVERSAO: .bak_antes_etapa6e.
# v1.1.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (3 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     MORTE - os dois relatorios (pacote 6), no visual do Magic. Sao so de consulta: nao gravam nada.
#       - Controle Interno: o PDF de UM MRT (botao "PDF" na lista do Controle Interno): os animais do lancamento, com Tipo, Causa, Destino,
#         Sexo e Eras, e o resumo Sexo x faixa de idade;
#       - Mortes no Periodo: tela com Data Inicial e Data Final (pela DATA DA MORTE) e o PDF "Formulario para Comunicar Mortes ocorridas no Periodo".
#     ROTAS (/produtor/morte/relatorio/): controle/<n> (GET, PDF), periodo/iniciar, periodo (GET tela / POST PDF).
#
#     v1.0.0: Sessao 111 (01/11/2026) - Criacao. REVERSAO: apagar este arquivo e o morte_periodo.html; desfazer o registro em app.py, no Hub e no
#             morte_controle.html.
# =========================================================
from datetime import date, datetime

from flask import Blueprint, redirect, render_template, request, send_file, session

from backend.models import Produtor
from backend.models.tb_2013_com_morte import ControleMorte
from backend.routers.auth import redirecionar_home
from backend.routers.saida_consulta import _contexto_base, _negado, _nomes, _propriedade_do_usuario, _ler_iso, URL_HUB
from backend.routers.morte_lancamento import _texto_controle
from backend.routers.morte_notificacao import _escolher_propriedade
from backend.utils.morte_relatorios_display import contexto_controle, contexto_periodo
from backend.utils.multitenant import get_db_produtor
from backend.utils.pdf_relatorio_morte import gerar_pdf_morte_controle, gerar_pdf_morte_periodo

morte_relatorios = Blueprint('morte_relatorios', __name__)

BASE = '/produtor/morte/relatorio'
URL_CONTROLE = '/produtor/morte/controle'
CHAVE_AVISO_MORTE_CONTROLE = 'aviso_morte_controle'   # Regra #69: aviso que acompanha o redirecionamento


@morte_relatorios.route(f'{BASE}/controle/<int:numero_controle>')
def controle_pdf(numero_controle):
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade.isdecimal() or not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_propriedade = int(id_propriedade)
    with get_db_produtor(session['id_produtor']) as db:
        ctrl = (db.query(ControleMorte).filter(ControleMorte.id_propriedade == id_propriedade,
                                               ControleMorte.controle == numero_controle).first())
        if ctrl is None:
            session[CHAVE_AVISO_MORTE_CONTROLE] = 'Não encontramos este Controle de Morte com animais nesta Propriedade. Escolha o Controle de novo na lista; se repetir, avise a Consiste (usuário, número do Controle, data e hora).'
            return redirect(f'{URL_CONTROLE}?id_propriedade={id_propriedade}')
        produtor = db.get(Produtor, session['id_produtor'])
        texto = _texto_controle(ctrl.controle)
        contexto = contexto_controle(db, produtor, id_propriedade, ctrl, texto, datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        if not contexto['animais']:
            session[CHAVE_AVISO_MORTE_CONTROLE] = 'Não encontramos este Controle de Morte com animais nesta Propriedade. Escolha o Controle de novo na lista; se repetir, avise a Consiste (usuário, número do Controle, data e hora).'
            return redirect(f'{URL_CONTROLE}?id_propriedade={id_propriedade}')
        buffer = gerar_pdf_morte_controle(contexto)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'morte_controle_{texto}.pdf')


@morte_relatorios.route(f'{BASE}/periodo/iniciar')
def periodo_iniciar():
    return _escolher_propriedade(f'{BASE}/periodo', 'Mortes no Período')


def _tela_periodo(id_propriedade, erro=None, ini='', fim=''):
    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, session['id_produtor'])
    hoje = date.today()
    return render_template(
        'produtor/morte_periodo.html', erro=erro, id_propriedade=int(id_propriedade),
        data_ini=ini or date(hoje.year, 1, 1).strftime('%Y-%m-%d'), data_fim=fim or hoje.strftime('%Y-%m-%d'),
        hoje_iso=hoje.strftime('%Y-%m-%d'), url_pdf=f'{BASE}/periodo', url_voltar=URL_HUB,
        produtor_nome=produtor_nome, propriedade_nome=propriedade_nome, propriedade_local=propriedade_local, **_contexto_base())


@morte_relatorios.route(f'{BASE}/periodo')
def periodo():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade.isdecimal() or not _propriedade_do_usuario(id_propriedade):
        return _negado()
    return _tela_periodo(id_propriedade)


@morte_relatorios.route(f'{BASE}/periodo', methods=['POST'])
def periodo_pdf():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.form.get('id_propriedade', '')
    if not id_propriedade.isdecimal() or not _propriedade_do_usuario(id_propriedade):
        return _negado()
    ini_txt, fim_txt = request.form.get('data_ini', ''), request.form.get('data_fim', '')
    ini, fim = _ler_iso(ini_txt), _ler_iso(fim_txt)
    if ini is None or fim is None:
        return _tela_periodo(id_propriedade, 'Informe a Data Inicial e a Data Final.', ini_txt, fim_txt)
    if fim < ini:
        return _tela_periodo(id_propriedade, 'A Data Final não pode ser anterior à Data Inicial.', ini_txt, fim_txt)
    with get_db_produtor(session['id_produtor']) as db:
        produtor = db.get(Produtor, session['id_produtor'])
        contexto = contexto_periodo(db, produtor, int(id_propriedade), ini, fim)
    if not contexto['animais']:
        return _tela_periodo(id_propriedade, 'Nenhuma morte lançada neste período.', ini_txt, fim_txt)
    buffer = gerar_pdf_morte_periodo(contexto)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                     download_name=f'mortes_periodo_{ini.strftime("%Y%m%d")}_{fim.strftime("%Y%m%d")}.pdf')

# =========================================================
# FIM DE ARQUIVO: backend\routers\morte_relatorios.py
# =========================================================
