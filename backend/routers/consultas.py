# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\consultas.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-08 19:26 -03
# ATUALIZADO EM: 2026-07-08 20:13 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Rotas de Consulta cruzada entre Produtor e Propriedade
#     (plataforma Consiste). Telas somente leitura - sem
#     cadastro, edicao ou exclusao.
#     - /consultas/produtor-propriedades  -> lista, agrupada por
#       Produtor, as Propriedades vinculadas ATIVAS (vinculo
#       propriedade_produtor com data_fim nulo)
#     - /consultas/propriedade-produtores -> espelho, agrupada
#       por Propriedade, os Produtores vinculados ATIVOS
#
#     Regras de negocio aplicadas (definidas com Benedito em
#     08/07/2026):
#     - So entram no resultado vinculos ATIVOS (data_fim IS NULL)
#       na tabela propriedade_produtor. Vinculo encerrado
#       (data_fim preenchido) nao aparece em nenhuma das duas
#       consultas.
#     - Produtor ou Propriedade INATIVOS (campo ativo=False)
#       continuam aparecendo normalmente (mesmo padrao de
#       produtor_lista.html, que tambem nao esconde inativos) -
#       decisao consciente para nao esconder uma inconsistencia
#       de cadastro (vinculo ainda ativo, mas uma das partes ja
#       foi inativada).
#     - Coluna calculada "Pode Movimentar" (nao existe no banco,
#       calculada na hora): Sim somente quando
#       Propriedade.ativo == True E Produtor.ativo == True ao
#       mesmo tempo. Registrado como pendencia P-024 para o
#       futuro modulo de Entrada de Animais/Movimentacao -
#       aquele modulo tera que aplicar essa mesma checagem antes
#       de liberar qualquer transacao (vinculo ativo sozinho nao
#       e suficiente).
#
#     v1.0.0: Criacao do modulo (Sessao do dia 08/07/2026).
#     v1.1.0: Sessao do dia 08/07/2026 - Ajuste de ordenacao a
#             pedido de Benedito, depois de ver a tela renderizada
#             (muito poluida visualmente na v1.0.0). Dentro de
#             cada bloco (e a ordem dos proprios blocos), quem
#             esta ATIVO vem primeiro em ordem alfabetica, e quem
#             esta INATIVO vai para o final, tambem em ordem
#             alfabetica. Isso deixa os itens problematicos
#             (que nao podem movimentar) juntos, no fim da lista,
#             sem precisar caca-los no meio dos ativos. O template
#             usa essa ordem para destacar visualmente (fundo
#             cinza) as linhas de quem esta inativo.
# =========================================================

from flask import Blueprint, render_template, redirect, url_for, session
from backend.database import engine
from backend.models import Produtor, Propriedade, PropriedadeProdutor
from sqlalchemy.orm import Session

# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
consultas = Blueprint('consultas', __name__)


# -------------------------------------------------------
# Rota: /consultas/produtor-propriedades
# Agrupa por Produtor: cada bloco traz os dados do Produtor
# e a lista de Propriedades vinculadas ATIVAS (data_fim nulo).
# -------------------------------------------------------
@consultas.route('/consultas/produtor-propriedades')
def produtor_propriedades():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    with Session(engine) as db:
        vinculos_ativos = db.query(PropriedadeProdutor).filter(
            PropriedadeProdutor.data_fim.is_(None)
        ).all()

        # Agrupa os vinculos por Produtor - um bloco por Produtor,
        # com a lista de Propriedades vinculadas dentro dele.
        produtores_agrupados = {}
        for vinculo in vinculos_ativos:
            produtor    = vinculo.produtor
            propriedade = vinculo.propriedade
            if not produtor or not propriedade:
                continue

            if produtor.id not in produtores_agrupados:
                produtores_agrupados[produtor.id] = {
                    'produtor': produtor,
                    'propriedades': []
                }

            produtores_agrupados[produtor.id]['propriedades'].append({
                'propriedade':      propriedade,
                'pode_movimentar':  bool(propriedade.ativo and produtor.ativo)
            })

        # Ordena os blocos: Produtor ATIVO primeiro (alfabetico),
        # Produtor INATIVO por ultimo (tambem alfabetico). Mesma
        # logica dentro de cada bloco, para as Propriedades.
        blocos = sorted(
            produtores_agrupados.values(),
            key=lambda b: (not b['produtor'].ativo, b['produtor'].nome)
        )
        for bloco in blocos:
            bloco['propriedades'].sort(
                key=lambda p: (not p['propriedade'].ativo, p['propriedade'].nome)
            )

    return render_template('consiste/consulta_produtor_propriedades.html',
        blocos         = blocos,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'consulta_produtor'
    )


# -------------------------------------------------------
# Rota: /consultas/propriedade-produtores
# Espelho da consulta acima. Agrupa por Propriedade: cada
# bloco traz os dados da Propriedade e a lista de Produtores
# vinculados ATIVOS (data_fim nulo).
# -------------------------------------------------------
@consultas.route('/consultas/propriedade-produtores')
def propriedade_produtores():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    with Session(engine) as db:
        vinculos_ativos = db.query(PropriedadeProdutor).filter(
            PropriedadeProdutor.data_fim.is_(None)
        ).all()

        # Agrupa os vinculos por Propriedade - um bloco por
        # Propriedade, com a lista de Produtores vinculados dentro.
        propriedades_agrupadas = {}
        for vinculo in vinculos_ativos:
            produtor    = vinculo.produtor
            propriedade = vinculo.propriedade
            if not produtor or not propriedade:
                continue

            if propriedade.id not in propriedades_agrupadas:
                propriedades_agrupadas[propriedade.id] = {
                    'propriedade': propriedade,
                    'produtores': []
                }

            propriedades_agrupadas[propriedade.id]['produtores'].append({
                'produtor':         produtor,
                'pode_movimentar':  bool(propriedade.ativo and produtor.ativo)
            })

        # Ordena os blocos por nome da Propriedade, e cada lista
        # interna por nome do Produtor.
        blocos = sorted(
            propriedades_agrupadas.values(),
            key=lambda b: (not b['propriedade'].ativo, b['propriedade'].nome)
        )
        for bloco in blocos:
            bloco['produtores'].sort(
                key=lambda p: (not p['produtor'].ativo, p['produtor'].nome)
            )

    return render_template('consiste/consulta_propriedade_produtores.html',
        blocos         = blocos,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'consulta_propriedade'
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\consultas.py
# =========================================================