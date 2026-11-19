# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\busca_cpf_cnpj.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-02 15:12 -03
# ATUALIZADO EM: 2026-11-16 09:25 -03
# VERSAO: 1.5.0
# v1.5.0: Sessao 128 (2026-11-16 09:25 -03) - AUDITORIA ETAPA 7 (varredura de id_propriedade, Regra #73): id_propriedade que nao e numero e ignorado (a busca segue normal) em vez de dar erro 500 no int(). REVERSAO: .bak_antes_etapa7a.
# v1.4.0: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras no CNPJ aceitas e conferidas; CNPJ antigo continua valendo. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Rotina de apoio do modulo GERAS: busca de pessoa
#     (Produtor e/ou Proprietario) por CPF/CNPJ.
#     Usada pelas telas de Propriedade, Proprietario e
#     Produtor para reaproveitar cadastro existente, evitando
#     digitar os mesmos dados de novo quando a pessoa ja
#     esta no sistema - em um dos dois papeis, ou nos dois
#     ao mesmo tempo (ex: o proprio dono da terra tambem
#     opera o rebanho).
#     - GET /api/busca-cpf-cnpj?documento=XXXXXXXXXXX
#     - GET /api/busca-cpf-cnpj?documento=XXXXXXXXXXX&id_propriedade=NN
#
#     v1.0.0: Criacao do modulo. Reescrita da primeira versao
#             (geras_api.py, descartada) apos fechamento dos
#             models reais na Sessao 010 (Proprietario,
#             Produtor, Propriedade, PropriedadeProdutor,
#             PropriedadeProprietario) e da limpeza de
#             nomenclatura id_ em todo o projeto.
#     v1.1.0: Sessao 033 - P-040, wizard de onboarding: aceita
#             parametro opcional id_propriedade. Quando
#             informado e o documento bate com um Produtor
#             existente, confere se ha vinculo ATIVO
#             (PropriedadeProdutor.data_fim is None) entre esse
#             Produtor e a Propriedade informada, e devolve o
#             novo campo resultado['produtor']['vinculado_a_
#             esta_propriedade'] (true/false). Usado por
#             produtor_cadastro.html v2.1.0 para distinguir "e o
#             Titular completando os proprios placeholders desta
#             Propriedade" (edicao, sem duplicar vinculo) de
#             "e outra pessoa/outro vinculo" (trava + Vincular,
#             comportamento original). Quando id_propriedade nao
#             e informado, o campo nao e adicionado ao resultado
#             (comportamento antigo preservado).
#     v1.2.0: Sessao 097 (15/10/2026, 11:20 -03) - AUDITORIA DE SEGURANCA: a rota /api/busca-cpf-cnpj passa a exigir login e perfil
#             CONSISTE ou PRODUTOR (antes era aberta a qualquer pessoa, sem login).
#             Nenhuma outra mudanca.
#     v1.3.0: Sessao 097 (15/10/2026, 13:31 -03) - VISIBILIDADE (LGPD). Cadastro
#             PRIVADO so mostra e-mail, telefones e endereco para quem tem
#             relacao com ele: perfil CONSISTE; Produtor ligado a esse
#             cadastro (vinculo ativo); ou Proprietario ligado a uma fazenda
#             do usuario (ou que e a mesma pessoa de um Produtor dele). Para
#             os demais, a busca devolve so id, nome, razao social, CPF/CNPJ,
#             tipo e visibilidade, com "restrito": true - a tela ainda avisa
#             "ja cadastrado" e o Vincular continua funcionando (grava pelo
#             id). Cadastro PUBLICO nao muda. Decisao do Benedito (opcao A).
# =========================================================

import re
from flask import Blueprint, jsonify, request, session
from backend.database import engine
from backend.models import Produtor, Proprietario, PropriedadeProdutor, PropriedadeProprietario
from sqlalchemy.orm import Session


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
busca_cpf_cnpj = Blueprint('busca_cpf_cnpj', __name__)


# -------------------------------------------------------
# Funcao auxiliar: normaliza CPF/CNPJ
# Remove pontos, tracos e barras, deixando so os digitos.
# Assim a busca funciona independente de como o usuario
# digitou (com ou sem mascara).
# Exemplo: "123.456.789-01" -> "12345678901"
# -------------------------------------------------------
def _normalizar_documento(documento):
    if not documento:
        return ''
    return re.sub(r'[^0-9A-Za-z]', '', documento).upper()   # v1.4.0: CNPJ alfanumerico


# -------------------------------------------------------
# Funcao auxiliar (Sessao 033): confere se ha vinculo ATIVO
# (data_fim is None) entre o Produtor e a Propriedade
# informados. Usada so quando id_propriedade e passado na
# busca - ver buscar_pessoa_por_documento().
# -------------------------------------------------------
def _produtor_vinculado_a_propriedade(db, id_produtor, id_propriedade):
    vinculo = db.query(PropriedadeProdutor).filter(
        PropriedadeProdutor.id_produtor == id_produtor,
        PropriedadeProdutor.id_propriedade == id_propriedade,
        PropriedadeProdutor.data_fim.is_(None)
    ).first()
    return vinculo is not None


# -------------------------------------------------------
# v1.3.0 - VISIBILIDADE. Campos pessoais que ficam ocultos de quem nao tem
# relacao com um cadastro PRIVADO.
# -------------------------------------------------------
SEM_RESTRICAO = 'SEM_RESTRICAO'
CAMPOS_RESERVADOS = ('email', 'telefone', 'telefone2', 'logradouro', 'numero',
                     'complemento', 'bairro', 'cep', 'municipio', 'uf')


def _e_privado(visibilidade):
    # Valores ja gravados: 'Privada' (convite), 'PRIVADO'/'PUBLICO' (tela de Produtor).
    return (visibilidade or '').strip().upper().startswith('PRIV')


def _escopo_do_usuario():
    """None = ve tudo (perfil CONSISTE). Senao (ids_produtores, ids_propriedades)
    a que o usuario logado esta ligado."""
    if session.get('usuario_perfil') == 'CONSISTE':
        return None
    from backend.routers.auth import buscar_pares_propriedade_produtor
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    return ({int(p.id_produtor) for p in pares}, {int(p.id_propriedade) for p in pares})


def _restringir(dados):
    """Mantem o minimo para a tela avisar 'ja cadastrado' e vincular."""
    for campo in CAMPOS_RESERVADOS:
        dados[campo] = None
    dados['restrito'] = True
    return dados


# -------------------------------------------------------
# Funcao principal: busca pessoa por CPF/CNPJ
# Consulta as tabelas produtores e proprietarios ao mesmo
# tempo. Cobre os 4 cenarios possiveis:
#   1) So existe como Produtor
#   2) So existe como Proprietario
#   3) Existe nos dois (mesma pessoa, dois papeis)
#   4) Nao existe em nenhum -> tela abre cadastro novo
#
# id_propriedade (Sessao 033, opcional): quando informado e
# o documento bate com um Produtor, adiciona o campo
# 'vinculado_a_esta_propriedade' ao resultado do Produtor.
# -------------------------------------------------------
def buscar_pessoa_por_documento(documento, id_propriedade=None, escopo=SEM_RESTRICAO):
    doc_limpo = _normalizar_documento(documento)

    with Session(engine) as db:
        produtor = db.query(Produtor).filter_by(cpf_cnpj=doc_limpo).first()
        proprietario = db.query(Proprietario).filter_by(cpf_cnpj=doc_limpo).first()

        resultado = {
            'encontrado': bool(produtor or proprietario),
            'produtor': None,
            'proprietario': None,
        }

        if produtor:
            resultado['produtor'] = {
                'id':             produtor.id,
                'nome':           produtor.nome,
                'razao_social':   produtor.razao_social,
                'cpf_cnpj':       produtor.cpf_cnpj,
                'tipo_pessoa':    produtor.tipo_pessoa,
                'visibilidade':   produtor.visibilidade,
                'email':          produtor.email,
                'telefone':       produtor.telefone,
                'telefone2':      produtor.telefone2,
                'logradouro':     produtor.logradouro,
                'numero':         produtor.numero,
                'complemento':    produtor.complemento,
                'bairro':         produtor.bairro,
                'cep':            produtor.cep,
                'municipio':      produtor.municipio,
                'uf':             produtor.uf,
            }

            if id_propriedade:
                resultado['produtor']['vinculado_a_esta_propriedade'] = _produtor_vinculado_a_propriedade(
                    db, produtor.id, int(id_propriedade)
                )

            produtor_liberado = (
                escopo == SEM_RESTRICAO or escopo is None
                or not _e_privado(produtor.visibilidade)
                or int(produtor.id) in escopo[0]
            )
            if not produtor_liberado:
                _restringir(resultado['produtor'])

        if proprietario:
            resultado['proprietario'] = {
                'id':             proprietario.id,
                'nome':           proprietario.nome,
                'razao_social':   proprietario.razao_social,
                'cpf_cnpj':       proprietario.cpf_cnpj,
                'tipo_pessoa':    proprietario.tipo_pessoa,
                'visibilidade':   proprietario.visibilidade,
                'email':          proprietario.email,
                'telefone':       proprietario.telefone,
                'telefone2':      proprietario.telefone2,
                'logradouro':     proprietario.logradouro,
                'numero':         proprietario.numero,
                'complemento':    proprietario.complemento,
                'bairro':         proprietario.bairro,
                'cep':            proprietario.cep,
                'municipio':      proprietario.municipio,
                'uf':             proprietario.uf,
            }

            proprietario_liberado = (
                escopo == SEM_RESTRICAO or escopo is None
                or not _e_privado(proprietario.visibilidade)
                or (produtor is not None and int(produtor.id) in escopo[0])
                or db.query(PropriedadeProprietario).filter(
                    PropriedadeProprietario.id_proprietario == proprietario.id,
                    PropriedadeProprietario.id_propriedade.in_(escopo[1] or {0}),
                    PropriedadeProprietario.data_fim.is_(None)
                ).first() is not None
            )
            if not proprietario_liberado:
                _restringir(resultado['proprietario'])

        return resultado


# -------------------------------------------------------
# Rota: GET /api/busca-cpf-cnpj — endpoint chamado via
# JavaScript/AJAX nas telas de Propriedade, Proprietario
# e Produtor, ao sair do campo de CPF/CNPJ. Aceita
# id_propriedade opcional (Sessao 033, ver acima).
# -------------------------------------------------------
@busca_cpf_cnpj.route('/api/busca-cpf-cnpj', methods=['GET'])
def rota_busca_cpf_cnpj():
    # v1.2.0 (auditoria): antes qualquer pessoa, sem login, consultava e-mail,
    # telefone e endereco pelo CPF/CNPJ. Agora exige login e perfil CONSISTE ou
    # PRODUTOR (as telas de cadastro que chamam esta busca).
    if 'usuario_id' not in session:
        return jsonify({'erro': 'Sessao nao autenticada'}), 401
    if session.get('usuario_perfil') not in ('CONSISTE', 'PRODUTOR'):
        return jsonify({'erro': 'Sem permissao'}), 403

    documento = request.args.get('documento', '')
    id_propriedade = request.args.get('id_propriedade')
    # v1.5.0 - Regra #73: so segue se for numero; senao ignora (a busca continua sem o campo de vinculo).
    if id_propriedade is not None and not str(id_propriedade).strip().isdecimal():
        id_propriedade = None

    if not documento:
        return jsonify({'erro': 'Documento nao informado'}), 400

    # v1.3.0: cadastro PRIVADO de quem nao tem relacao com o usuario sai sem contatos/endereco.
    resultado = buscar_pessoa_por_documento(documento, id_propriedade, _escopo_do_usuario())
    return jsonify(resultado)

# =========================================================
# FIM DE ARQUIVO: backend\routers\busca_cpf_cnpj.py
# =========================================================