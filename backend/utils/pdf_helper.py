# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\pdf_helper.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-08 21:02 -03
# ATUALIZADO EM: 2026-07-08 21:02 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Funcao auxiliar compartilhada para geracao de relatorios
#     em PDF (xhtml2pdf), usada por qualquer router que gere
#     relatorio (hoje: Produtor e Proprietario; no futuro:
#     Propriedade, Animais, etc.).
#
#     Resolve a pendencia P-023 (formalizar o padrao de PDF
#     como convencao oficial). Antes desta versao, a funcao
#     abaixo estava copiada palavra por palavra dentro de
#     backend/routers/produtores.py (como _link_callback_pdf)
#     e backend/routers/proprietarios.py (idem) - risco real
#     de as duas copias divergirem se alguem corrigisse uma
#     e esquecesse a outra. Agora existe em um unico lugar, e
#     os routers so importam.
#
#     Pasta backend/utils/ e nova no projeto - esta e a
#     primeira vez que ela aparece (confirmado com Benedito
#     em 08/07/2026, sessao do dia).
#
#     v1.0.0: Extracao da funcao de produtores.py v1.2.0 e
#             proprietarios.py v2.2.0 (as duas copias eram
#             identicas). Renomeada de _link_callback_pdf
#             (privada, prefixo _) para link_callback_pdf
#             (publica, sem prefixo) - agora que a funcao e
#             compartilhada entre arquivos, o prefixo de
#             "privada deste modulo" deixou de fazer sentido.
#             Nenhuma mudanca de comportamento - so mudou de
#             lugar e de nome.
# =========================================================

import os
from flask import current_app


# -------------------------------------------------------
# Funcao: link_callback_pdf
# Ensina o xhtml2pdf a encontrar imagens locais no disco.
# Sem isso, qualquer <img src="/static/..."> dentro de um
# template de relatorio fica quebrada no PDF - o xhtml2pdf
# nao tem um navegador por tras, entao nao sabe resolver a
# URL sozinho, precisa do caminho absoluto do arquivo no
# sistema de arquivos.
#
# Uso (dentro de qualquer rota de relatorio):
#     from backend.utils.pdf_helper import link_callback_pdf
#     ...
#     pisa.CreatePDF(html_renderizado, dest=buffer_pdf,
#                     link_callback=link_callback_pdf)
# -------------------------------------------------------
def link_callback_pdf(uri, rel):
    if uri.startswith('/static/'):
        caminho_relativo = uri.replace('/static/', '', 1)
        return os.path.join(current_app.static_folder, caminho_relativo)
    return uri

# =========================================================
# FIM DE ARQUIVO: backend\utils\pdf_helper.py
# =========================================================