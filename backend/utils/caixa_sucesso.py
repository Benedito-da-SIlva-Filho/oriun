# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\caixa_sucesso.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-22 16:15 -03
# ATUALIZADO EM: 2026-10-23 08:50 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     PADRAO REUTILIZAVEL "Caixa de Sucesso" (decisao do Benedito, 22/10/2026): depois de gravar, o usuario e OBRIGADO a ver uma tela
#     de confirmacao (um banner pequeno na tela seguinte passa despercebido). A tela mostra: titulo, o que mudou (campo, antes -> depois),
#     avisos em vermelho (ex.: reimprimir o Comunicado), notas e os botoes do proximo passo.
#
#     USO (no router, depois do commit):
#         return render_caixa_sucesso(_contexto_base(), titulo='GTA alterada com sucesso!', subtitulo='MTA111111',
#                                     mudancas=[{'campo': 'Validade', 'antes': '20/10/2026', 'depois': '25/10/2026'}],
#                                     avisos=['Reimprima o Comunicado.'], notas=[],
#                                     botoes=[{'texto': 'Ver GTA', 'url': '/x', 'primario': True}], url_voltar='/x')
#     Para gravar e redirecionar (PRG, sem reenviar o formulario ao recarregar): guardar o resumo em session['caixa_sucesso'] e
#     redirecionar para uma rota GET que le e apaga esse resumo (ver gta_saida.alterada).
#
#     v1.0.0: Criacao (Sessao 103) - primeiro uso: Alterar e Excluir GTA de Saida.
#     v1.1.0: Sessao 104 (23/10/2026, 08:50 -03) - novo parametro OPCIONAL tabelas (lista de {'titulo','colunas','linhas','ultima_vermelha'}): mostra
#             listas abaixo do resumo (usado pelo Abate por Arquivo: gravados e recusados). Sem tabelas, tudo igual a antes.
#             REVERSAO: .bak_antes_s104 deste arquivo e do caixa_sucesso.html.
#     REVERSAO: remover este arquivo e o template caixa_sucesso.html.
# =========================================================

from flask import render_template


def render_caixa_sucesso(contexto, titulo, subtitulo='', mudancas=None, avisos=None, notas=None, botoes=None,
                         url_voltar='', icone='&#9989;', titulo_pagina='Orion SISBOV', tabelas=None):
    return render_template(
        'produtor/caixa_sucesso.html',
        cs_titulo=titulo, cs_subtitulo=subtitulo, cs_mudancas=mudancas or [], cs_avisos=avisos or [],
        cs_notas=notas or [], cs_botoes=botoes or [], cs_icone=icone, cs_titulo_pagina=titulo_pagina, cs_tabelas=tabelas or [],
        url_voltar=url_voltar,
        **contexto,
    )

# =========================================================
# FIM DE ARQUIVO: backend\utils\caixa_sucesso.py
# =========================================================
