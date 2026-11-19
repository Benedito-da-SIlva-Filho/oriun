# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\consiste_blockchain.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-09 19:00 -03
# ATUALIZADO EM: 2026-10-10 18:00 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Tela CONSISTE > Blockchain (Sessao 092): painel de acompanhamento e
#     validacao do blockchain de TODOS os Produtores ativos. So o perfil
#     CONSISTE acessa (mesmo padrao do Backup/Restore).
#
#     Mostra e confere; nao envia, nao cancela, nao reenvia. A unica coisa
#     que grava (so no "Validar agora") e a marca "conferido" nos eventos que
#     passaram em tudo. O processo do blockchain continua 100% automatico (o
#     carteiro, carteiro_blockchain.py, segue enviando em segundo plano) -
#     abrir ou nao esta tela nao muda nada nele.
#
#     ROTAS
#       GET /consiste/blockchain                - tabela-resumo por Produtor
#                                                 (+ resultado da validacao se
#                                                 vier ?validar=1)
#       GET /consiste/blockchain/relatorio.txt  - o mesmo resultado, para baixar
#
#     PARAMETROS (query string): produtor (id; vazio = todos), tipo (tipo de
#     evento; vazio = todos), mostrar_ok (1 = mostra tambem as linhas OK),
#     validar (1 = roda a validacao), tudo (1 = reconfere tambem os eventos
#     ja conferidos antes).
#
#     "Validar agora": confere so o que ainda nao foi conferido (ou tudo, com
#     tudo=1) e MARCA os eventos que passaram. "Baixar relatorio (.txt)":
#     SEMPRE confere tudo e NUNCA marca nada (comprovante completo).
#
#     As conferencias moram em backend\utils\validador_blockchain.py (mesma
#     "receita" do validar_blockchain.py do terminal).
#
#     v1.0.0: Criacao (Sessao 092, 09/10/2026, 19:00 -03).
#     v1.1.0: Sessao 093 (10/10/2026, 18:00 -03) - Entrega 2: opcao "reconferir
#         tudo" (tudo=1); "Validar agora" so confere o que falta e marca os
#         OK; o relatorio .txt sempre confere tudo sem marcar; a tela recebe
#         as contagens (conferidos agora / pulados / marcados).
# =========================================================

from datetime import datetime

from flask import Blueprint, render_template, request, session, Response

from backend.routers.auth import redirecionar_home
from backend.utils import blockchain as B
from backend.utils import validador_blockchain as V

consiste_blockchain = Blueprint('consiste_blockchain', __name__)


def _acesso_negado():
    """Devolve o redirect se o usuario nao for do perfil CONSISTE; senao None."""
    if 'usuario_id' not in session:
        return redirecionar_home(session.get('usuario_perfil'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirecionar_home(session.get('usuario_perfil'))
    return None


def _ler_filtros():
    """Le e valida os filtros da query string."""
    id_produtor = request.args.get('produtor', type=int)
    tipo = (request.args.get('tipo') or '').strip().upper() or None
    if tipo and tipo not in B.TIPOS_EVENTO:
        tipo = None
    mostrar_ok = request.args.get('mostrar_ok') == '1'
    tudo = request.args.get('tudo') == '1'
    return id_produtor, tipo, mostrar_ok, tudo


@consiste_blockchain.route('/consiste/blockchain')
def tela():
    negado = _acesso_negado()
    if negado:
        return negado

    id_produtor, tipo, mostrar_ok, tudo = _ler_filtros()
    validar = request.args.get('validar') == '1'

    resultados = None
    totais = None
    conferencia = None
    quando = None
    if validar:
        quando = datetime.now()
        resultados = V.validar(id_produtor=id_produtor, tipo=tipo, tudo=tudo, marcar=True)
        totais = V.somar(resultados)
        conferencia = V.somar_conferencia(resultados)
    # O resumo vem DEPOIS da validacao: a coluna "A conferir" ja mostra o
    # efeito das marcas gravadas agora.
    resumo = V.resumo()

    return render_template(
        'consiste/consiste_blockchain.html',
        resumo=resumo,
        resultados=resultados,
        totais=totais,
        conferencia=conferencia,
        quando=quando,
        id_produtor_filtro=id_produtor,
        tipo_filtro=tipo,
        mostrar_ok=mostrar_ok,
        tudo=tudo,
        tipos_evento=B.TIPOS_EVENTO,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='blockchain',
    )


@consiste_blockchain.route('/consiste/blockchain/relatorio.txt')
def relatorio_txt():
    negado = _acesso_negado()
    if negado:
        return negado

    id_produtor, tipo, mostrar_ok, _tudo = _ler_filtros()
    quando = datetime.now()
    # Comprovante completo: SEMPRE confere tudo e NUNCA marca nada.
    resultados = V.validar(id_produtor=id_produtor, tipo=tipo, tudo=True, marcar=False)
    texto = V.formatar_texto(resultados, tipo=tipo, so_problemas=not mostrar_ok, quando=quando,
                             tudo=True, marcar=False)
    texto = texto.replace('\n', '\r\n') + '\r\n'

    return Response(
        texto,
        mimetype='text/plain',
        headers={
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Disposition': f'attachment; filename=validacao_blockchain_{quando:%Y%m%d_%H%M}.txt',
        },
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\consiste_blockchain.py
# =========================================================
