# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\busca_propriedade.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-07 10:30 -03
# ATUALIZADO EM: 2026-09-07 10:30 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Rotina de apoio: busca de Propriedade (tb_parceiros_propriedades)
#     por Insc. Estadual, SEM filtrar por Parceiro/CPF-CNPJ - ao
#     contrario de busca_parceiro.py (que busca as Propriedades DE
#     UM Parceiro), esta rotina varre TODAS as Propriedades ja
#     cadastradas no schema do Produtor, de qualquer Parceiro.
#
#     Motivacao (Sessao 047): cenario real de 2 CPFs diferentes
#     (ex.: pai e filho, socios) donos da MESMA fazenda fisica -
#     a Insc. Estadual e o dado que identifica a fazenda em si,
#     entao serve de "chave de busca" pra reaproveitar os dados
#     ja digitados (Estabelecimento/Codigo MAPA/Municipio/UF) na
#     tela de Cadastro Manual de Parceiro, evitando redigitar tudo
#     pro segundo CPF. NAO faz nenhum vinculo/relacionamento entre
#     os Parceiros - so preenche o formulario, o usuario confere e
#     salva um registro proprio (tb_parceiros_propriedades comum,
#     sem alteracao de modelo).
#
#     Em caso de mais de uma Propriedade com a mesma Insc. Estadual
#     (nao deveria acontecer, mas dado digitado por humano nao e
#     garantido), traz a mais recente (maior id) - decisao simples,
#     o usuario sempre confere antes de salvar.
#
#     - GET /api/busca-propriedade?insc_estadual=XXX
#
#     v1.0.0: Criacao do modulo (Sessao 047).
# =========================================================

from flask import Blueprint, jsonify, request, session
from backend.models.tb_parceiros_propriedades import ParceiroPropriedades
from backend.utils.multitenant import get_db_produtor


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
busca_propriedade = Blueprint('busca_propriedade', __name__)


# -------------------------------------------------------
# Funcao principal: busca 1 Propriedade por Insc. Estadual,
# dentro do schema do Produtor logado, independente de qual
# Parceiro ela pertence hoje.
# -------------------------------------------------------
def buscar_propriedade_por_insc_estadual(id_produtor, insc_estadual):
    valor_limpo = (insc_estadual or '').strip().upper()

    resultado = {
        'encontrado': False,
        'propriedade': None,
    }

    if not valor_limpo:
        return resultado

    with get_db_produtor(id_produtor) as db:
        propriedade = db.query(ParceiroPropriedades).filter_by(
            insc_estadual=valor_limpo,
            ativo=True
        ).order_by(ParceiroPropriedades.id.desc()).first()

        if propriedade:
            resultado['encontrado'] = True
            resultado['propriedade'] = {
                'estabelecimento':  propriedade.estabelecimento,
                'codigo_mapa':      propriedade.codigo_mapa,
                'insc_estadual':    propriedade.insc_estadual,
                'municipio_codigo': propriedade.municipio_codigo,
                'municipio_nome':   propriedade.municipio_nome,
                'uf':               propriedade.uf,
                'regiao':           propriedade.regiao,
            }

        return resultado


# -------------------------------------------------------
# Rota: GET /api/busca-propriedade — chamada via JavaScript
# ao digitar a Insc. Estadual no formulario de Cadastro
# Manual de Parceiro (Parceiro Novo). Exige usuario
# autenticado com id_produtor na sessao (mesmo padrao das
# demais rotas do modulo Produtor).
# -------------------------------------------------------
@busca_propriedade.route('/api/busca-propriedade', methods=['GET'])
def rota_busca_propriedade():
    id_produtor = session.get('id_produtor')
    if not id_produtor:
        return jsonify({'erro': 'Sessao nao autenticada'}), 401

    insc_estadual = request.args.get('insc_estadual', '')

    resultado = buscar_propriedade_por_insc_estadual(id_produtor, insc_estadual)
    return jsonify(resultado)

# =========================================================
# FIM DE ARQUIVO: backend\routers\busca_propriedade.py
# =========================================================