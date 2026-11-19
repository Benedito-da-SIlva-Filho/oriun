# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\busca_parceiro.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-08-21 10:15 -03
# ATUALIZADO EM: 2026-11-12 19:00 -03
# VERSAO: 1.2.0
# v1.2.0: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras no CNPJ aceitas e conferidas; CNPJ antigo continua valendo. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Rotina de apoio: busca de Parceiro (tb_parceiros) por
#     CPF/CNPJ, trazendo junto suas Propriedades vinculadas
#     (tb_parceiros_propriedades). Usada pela tela de Cadastro
#     Manual de Parceiro / GTA Manual - ao digitar o CPF/CNPJ
#     da Procedencia, confere se o Parceiro ja existe: se sim,
#     devolve os dados para o usuario escolher a Propriedade
#     (quando houver mais de uma) e seguir direto pra GTA
#     Manual; se nao, a tela abre o formulario de cadastro
#     novo. Mesmo padrao de busca_cpf_cnpj.py.
#     - GET /api/busca-parceiro?documento=XXXXXXXXXXX
#
#     v1.0.0: Criacao do modulo (Sessao 036).
#     v1.1.0: Sessao 036 - CORRECAO CRITICA. Versao anterior
#             usava Session(engine) puro (schema public),
#             causando UndefinedTable: "tb_parceiros" nao
#             existe. tb_parceiros mora dentro do schema de
#             cada Produtor (Schema-por-Produtor), nao no
#             public - mesmo padrao ja usado por
#             resolver_parceiro.py e parceiros_fornecedores.py.
#             Corrigido para usar get_db_produtor(id_produtor),
#             com id_produtor lido de session['id_produtor'].
#             Erro cometido pelo Piloto - regra de ouro
#             (ver arquivo real antes de codar) nao foi
#             seguida na v1.0.0.
# =========================================================

import re
from flask import Blueprint, jsonify, request, session
from backend.models.tb_parceiros import Parceiro
from backend.models.tb_parceiros_propriedades import ParceiroPropriedades
from backend.utils.multitenant import get_db_produtor


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
busca_parceiro = Blueprint('busca_parceiro', __name__)


# -------------------------------------------------------
# Funcao auxiliar: normaliza CPF/CNPJ (mesma logica de
# busca_cpf_cnpj.py - remove pontos, tracos e barras).
# -------------------------------------------------------
def _normalizar_documento(documento):
    if not documento:
        return ''
    return re.sub(r'[^0-9A-Za-z]', '', documento).upper()   # v1.2.0: CNPJ alfanumerico


# -------------------------------------------------------
# Funcao principal: busca Parceiro por CPF/CNPJ dentro do
# schema do Produtor logado, trazendo junto a lista de
# Propriedades vinculadas (so as ativas).
# -------------------------------------------------------
def buscar_parceiro_por_documento(id_produtor, documento):
    doc_limpo = _normalizar_documento(documento)

    with get_db_produtor(id_produtor) as db:
        parceiro = db.query(Parceiro).filter_by(
            cpf_cnpj=doc_limpo,
            ativo=True
        ).first()

        resultado = {
            'encontrado': parceiro is not None,
            'parceiro': None,
            'propriedades': [],
        }

        if parceiro:
            resultado['parceiro'] = {
                'id':        parceiro.id,
                'cpf_cnpj':  parceiro.cpf_cnpj,
                'nome':      parceiro.nome,
            }

            propriedades = db.query(ParceiroPropriedades).filter_by(
                id_parceiro=parceiro.id,
                ativo=True
            ).order_by(ParceiroPropriedades.estabelecimento).all()

            resultado['propriedades'] = [
                {
                    'id':               p.id,
                    'estabelecimento':  p.estabelecimento,
                    'codigo_mapa':      p.codigo_mapa,
                    'insc_estadual':    p.insc_estadual,
                    'municipio_codigo': p.municipio_codigo,
                    'municipio_nome':   p.municipio_nome,
                    'uf':               p.uf,
                    'regiao':           p.regiao,
                }
                for p in propriedades
            ]

        return resultado


# -------------------------------------------------------
# Rota: GET /api/busca-parceiro — endpoint chamado via
# JavaScript/AJAX ao sair do campo de CPF/CNPJ da
# Procedencia, na tela de Cadastro Manual de Parceiro.
# Exige usuario autenticado com id_produtor na sessao
# (mesmo padrao das demais rotas do modulo Produtor).
# -------------------------------------------------------
@busca_parceiro.route('/api/busca-parceiro', methods=['GET'])
def rota_busca_parceiro():
    id_produtor = session.get('id_produtor')
    if not id_produtor:
        return jsonify({'erro': 'Sessao nao autenticada'}), 401

    documento = request.args.get('documento', '')

    if not documento:
        return jsonify({'erro': 'Documento nao informado'}), 400

    resultado = buscar_parceiro_por_documento(id_produtor, documento)
    return jsonify(resultado)

# =========================================================
# FIM DE ARQUIVO: backend\routers\busca_parceiro.py
# =========================================================