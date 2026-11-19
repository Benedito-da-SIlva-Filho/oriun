# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\busca_municipio.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-08-21 10:15 -03
# ATUALIZADO EM: 2026-11-16 11:45 -03
# VERSAO: 1.4.0
# v1.3.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Rotina de apoio: busca de Municipio (tb_1023_municipios).
#     Duas formas de busca:
#       - GET /api/busca-municipio?termo=XXX (por nome, contendo
#         o termo, ate 20 resultados - autocomplete)
#       - GET /api/busca-municipio?codigo=XXXXXXX (por Codigo
#         IBGE EXATO - usado na GTA Manual/Cadastro Manual de
#         Parceiro, onde o codigo ja vem impresso no documento
#         fisico e o usuario so digita o numero, o Nome/UF
#         aparecem automaticamente)
#
#     v1.0.0: Criacao do modulo (Sessao 036). So busca por nome.
#     v1.1.0: Sessao 036 - Adicionada busca por Codigo IBGE exato
#             (parametro 'codigo'). Motivo: a GTA sempre traz o
#             Codigo do Municipio impresso (ex.: "5006408 - PEDRO
#             GOMES") - o usuario digita o codigo (como esta no
#             documento) e o sistema mostra o nome. Busca por nome
#             (v1.0.0) mantida, sem alteracao de comportamento.
#     v1.2.0: Sessao 095 (13/10/2026, 19:45 -03) - serializar() devolve tambem regiao_brasil, mesorregiao e microrregiao (IBGE) para a tela Novo Parceiro.
#     v1.4.0: Sessao 128 (2026-11-16 11:45 -03) - AUDITORIA ETAPA 8a: a busca de municipio passa a exigir login (antes abria para qualquer pessoa na internet). REVERSAO: .bak_antes_etapa8a.
# =========================================================

from flask import Blueprint, jsonify, request, session
from backend.database import engine
from backend.models.tb_1023_municipios import Municipio
from sqlalchemy.orm import Session


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
busca_municipio = Blueprint('busca_municipio', __name__)


# -------------------------------------------------------
# Funcao: busca Municipios por nome (contendo o termo
# digitado, case-insensitive), com filtro opcional de UF.
# Limita a 20 resultados - suficiente para autocomplete.
# -------------------------------------------------------
def buscar_municipios_por_nome(termo, uf=None):
    termo_limpo = (termo or '').strip()

    if len(termo_limpo) < 3:
        return []

    with Session(engine) as db:
        consulta = db.query(Municipio).filter(
            Municipio.ativo.is_(True),
            Municipio.nome.ilike(f'%{termo_limpo}%')
        )

        if uf:
            consulta = consulta.filter(Municipio.uf == uf.strip().upper())

        municipios = consulta.order_by(Municipio.nome).limit(20).all()

        return [_serializar(m) for m in municipios]


# -------------------------------------------------------
# Funcao: busca 1 Municipio por Codigo IBGE exato (7
# digitos). Usada quando o codigo ja e conhecido (ex.:
# impresso na GTA fisica) - devolve no maximo 1 resultado
# ou None.
# -------------------------------------------------------
def buscar_municipio_por_codigo(codigo):
    codigo_limpo = ''.join(c for c in (codigo or '') if c.isdecimal())

    if not codigo_limpo:
        return None

    with Session(engine) as db:
        municipio = db.query(Municipio).filter_by(
            codigo_ibge=codigo_limpo,
            ativo=True
        ).first()

        return _serializar(municipio) if municipio else None


# -------------------------------------------------------
# Funcao auxiliar: serializa um Municipio para dict JSON.
# -------------------------------------------------------
def _serializar(m):
    return {
        'id':          m.id,
        'codigo_ibge': m.codigo_ibge,
        'nome':        m.nome,
        'uf':          m.uf,
        'regiao_brasil': m.regiao_brasil,
        'mesorregiao':   m.mesorregiao,
        'microrregiao':  m.microrregiao,
    }


# -------------------------------------------------------
# Rota: GET /api/busca-municipio — aceita 'termo' (busca por
# nome, lista) OU 'codigo' (busca por Codigo IBGE exato, 1
# resultado ou null). Se os dois vierem, 'codigo' tem
# prioridade.
# -------------------------------------------------------
@busca_municipio.route('/api/busca-municipio', methods=['GET'])
def rota_busca_municipio():
    if 'usuario_id' not in session:
        return jsonify({'erro': 'Sessao nao autenticada'}), 401

    codigo = request.args.get('codigo')

    if codigo:
        resultado = buscar_municipio_por_codigo(codigo)
        return jsonify(resultado)

    termo = request.args.get('termo', '')
    uf = request.args.get('uf')

    resultado = buscar_municipios_por_nome(termo, uf)
    return jsonify(resultado)

# =========================================================
# FIM DE ARQUIVO: backend\routers\busca_municipio.py
# =========================================================