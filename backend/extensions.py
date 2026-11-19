# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend
# MODULO: backend/extensions.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-06-25 09:08 -03
# ATUALIZADO EM: 2026-06-25 09:08 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Extensoes Flask do Orion.
#     Instancias criadas aqui e inicializadas no app.py.
#     Evita importacao circular entre modulos.
#     v1.0.0: Criacao do modulo. Flask-Mail adicionado.
# =========================================================

from flask_mail import Mail

# Instancia do Flask-Mail
# Sera inicializada com mail.init_app(app) no app.py
mail = Mail()

# =========================================================
# FIM DE ARQUIVO: backend/extensions.py
# =========================================================