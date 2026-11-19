# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\leitores
# MODULO: backend\leitores\__init__.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-08-01 11:15 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Pacote de leitores automaticos de e-GTA (PDF). Cada orgao
#     estadual (IAGRO/MS, INDEA/MT, etc.) tem seu proprio modulo
#     leitor_<orgao>.py, com uma funcao publica ler(caminho_pdf)
#     que devolve um dicionario com os campos ja prontos para
#     preencher o formulario de Compra.
#
#     O registry.py decide automaticamente qual leitor usar, por
#     assinatura no texto do documento - o usuario nunca escolhe
#     manualmente o Estado/orgao (decisao de Benedito, Sessao
#     029: evitar que o Produtor selecione a opcao errada e
#     depois alegue que "o software errou", jogando a
#     responsabilidade do erro para a Consiste).
#
#     v1.0.0: Criacao do pacote (Sessao 029).
# =========================================================
# FIM DE ARQUIVO: backend\leitores\__init__.py
# =========================================================