# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\frigorificos.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-17 14:50 -03
# ATUALIZADO EM: 2026-11-12 19:00 -03
# VERSAO: 1.1.0
# v1.1.0: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras no CNPJ aceitas e conferidas; CNPJ antigo continua valendo. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Cadastro de Frigorificos (Sessao 099) - tela de consulta e cadastro da
#     tabela public.tb_frigorificos, que e COMUM a todos os Produtores (397
#     plantas importadas do GERAS). Molde: parceiros_fornecedores.py.
#     Menu lateral: CADASTRO, abaixo de "Parceiros". Permissao: a mesma de
#     Parceiros e Fornecedores (modulo 'parceiros', permissoes.py v1.4.4).
#
#     ROTAS:
#       /produtor/frigorificos             - lista com busca por Nome ou CNPJ (sem
#                                            acento, sem maiuscula), filtro de UF e
#                                            de Municipio. A UF abre na UF da fazenda
#                                            em uso; "Todas" mostra todas.
#       /produtor/frigorificos/novo        - cadastro de Frigorifico novo.
#       /produtor/frigorificos/novo/salvar - grava (POST).
#       /produtor/frigorificos/api/buscar  - JSON da mesma busca (atalho que a tela de
#                                            Cadastro de GTA de Saida vai usar).
#       /produtor/frigorificos/api/cnpj    - JSON: o CNPJ ja existe?
#
#     REGRAS (Benedito, 17/10/2026):
#       - O Produtor INCLUI, mas nao ALTERA frigorifico que ja existe (a lista e de
#         todos; corrigir um cadastro afeta todo mundo). Nao ha tela de edicao.
#       - CNPJ unico: se ja existe, a tela avisa e nao cria outro.
#       - Quem vende conhece o cliente: o Produtor procura as informacoes, a Consiste
#         nao completa cadastro.
#       - OBRIGATORIOS: CNPJ (com conferencia dos digitos), Nome, UF + Municipio (da
#         tb_1023, com o codigo IBGE) e PELO MENOS UM selo de inspecao (SIF, SIE ou
#         SIM). Opcionais: inscricao estadual, codigo MAPA e endereco.
#       - O CNPJ e gravado so com digitos (padrao da importacao do GERAS).
#       - Parte dos 397 frigorificos importados veio sem municipio/UF/selo: eles
#         aparecem com "-" e so entram numa busca com a UF em "Todas".
#
#     v1.0.0: Criacao (Sessao 099).
# =========================================================

import re
import unicodedata

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade
from backend.models.tb_frigorificos import Frigorifico
from backend.routers.auth import redirecionar_home
from backend.routers.busca_municipio import buscar_municipio_por_codigo
from backend.utils.validadores import validar_cnpj, limpar_documento

# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
frigorificos = Blueprint('frigorificos', __name__)

LIMITE_LISTA = 100
LIMITE_API_PADRAO = 20
LIMITE_API_MAXIMO = 50
UFS = ('AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG',
       'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO')

_CAMPOS_NOVO = ('cpf_cnpj', 'nome', 'insc_estadual', 'codigo_mapa', 'cod_sif', 'cod_sie', 'cod_sim',
                'logradouro', 'numero', 'bairro', 'cep', 'municipio_codigo', 'municipio_nome', 'uf')


# -------------------------------------------------------
# Acesso: perfil PRODUTOR/FAZENDA e produtor na sessao (mesma conferencia de Parceiros).
# -------------------------------------------------------
def _checar_acesso():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    perfil = session.get('usuario_perfil')
    if perfil not in ('PRODUTOR', 'FAZENDA'):
        return redirecionar_home(perfil)
    if not session.get('id_produtor'):
        return redirecionar_home(perfil)
    return None


def _checar_acesso_api():
    if 'usuario_id' not in session or session.get('usuario_perfil') not in ('PRODUTOR', 'FAZENDA') \
            or not session.get('id_produtor'):
        return jsonify({'erro': 'Sessão expirada.'}), 401
    return None


# -------------------------------------------------------
# Utilitarios
# -------------------------------------------------------
def _norm(texto):
    """Minusculo e sem acento, para a busca."""
    base = unicodedata.normalize('NFKD', texto or '')
    return ''.join(c for c in base if not unicodedata.combining(c)).lower().strip()


def _so_digitos(texto):
    return re.sub(r'\D', '', texto or '')


def _mascara_cnpj(digitos):
    d = limpar_documento(digitos)
    if len(d) != 14:
        return digitos or ''
    return f'{d[0:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}'


def _uf_da_fazenda():
    """UF da fazenda em uso ('' se nao houver)."""
    fazenda = session.get('fazenda_ativa') or {}
    try:
        id_propriedade = int(fazenda.get('id_propriedade'))
    except (TypeError, ValueError):
        return ''
    with Session(engine) as db:
        propriedade = db.get(Propriedade, id_propriedade)
        return (propriedade.uf or '').upper() if propriedade else ''


def _todos_ativos():
    with Session(engine) as db:
        linhas = (
            db.query(Frigorifico)
            .filter(Frigorifico.ativo == True)   # noqa: E712
            .order_by(Frigorifico.nome)
            .all()
        )
        itens = []
        for f in linhas:
            selos = []
            if f.cod_sif: selos.append('SIF ' + f.cod_sif)
            if f.cod_sie: selos.append('SIE ' + f.cod_sie)
            if f.cod_sim: selos.append('SIM ' + f.cod_sim)
            itens.append({
                'id': f.id,
                'nome': f.nome or '',
                'cnpj': limpar_documento(f.cpf_cnpj),
                'cnpj_fmt': _mascara_cnpj(f.cpf_cnpj),
                'municipio': f.municipio_nome or '',
                'uf': (f.uf or '').upper(),
                'selos': ' · '.join(selos),
                'codigo_mapa': f.codigo_mapa or '',
                'nome_norm': _norm(f.nome),
                'mun_norm': _norm(f.municipio_nome),
            })
        return itens


def _filtrar(itens, termo, uf, municipio):
    termo = (termo or '').strip()
    digitos = _so_digitos(termo)
    so_numero = bool(digitos) and not re.search(r'[A-Za-z]', termo)
    palavras = [] if so_numero else _norm(termo).split()
    mun = _norm(municipio)
    resultado = []
    for i in itens:
        if uf and i['uf'] != uf:
            continue
        if mun and mun not in i['mun_norm']:
            continue
        if so_numero and digitos not in i['cnpj']:
            continue
        if palavras and not all(p in i['nome_norm'] for p in palavras):
            continue
        resultado.append(i)
    return resultado


def _contexto_base():
    return dict(
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'frigorificos',
    )


# -------------------------------------------------------
# Rota: GET /produtor/frigorificos - lista com busca.
# -------------------------------------------------------
@frigorificos.route('/produtor/frigorificos')
def lista():
    bloqueio = _checar_acesso()
    if bloqueio:
        return bloqueio

    termo = request.args.get('busca', '').strip()
    municipio = request.args.get('municipio', '').strip()
    if 'uf' in request.args:
        uf = request.args.get('uf', '').strip().upper()
    else:
        uf = _uf_da_fazenda()          # primeira abertura: UF da fazenda em uso
    if uf and uf not in UFS:
        uf = ''

    encontrados = _filtrar(_todos_ativos(), termo, uf, municipio)

    return render_template(
        'produtor/frigorifico_lista.html',
        itens=encontrados[:LIMITE_LISTA],
        total=len(encontrados),
        limite=LIMITE_LISTA,
        termo_busca=termo,
        municipio_busca=municipio,
        uf_busca=uf,
        ufs=UFS,
        mensagem_ok=('Frigorífico cadastrado com sucesso!' if request.args.get('salvo') == '1' else ''),
        **_contexto_base()
    )


# -------------------------------------------------------
# Rota: GET /produtor/frigorificos/api/buscar (JSON) - mesma busca, para o atalho
# dentro de outras telas (Cadastro de GTA de Saida).
# -------------------------------------------------------
@frigorificos.route('/produtor/frigorificos/api/buscar')
def api_buscar():
    bloqueio = _checar_acesso_api()
    if bloqueio:
        return bloqueio
    try:
        limite = int(request.args.get('limite', LIMITE_API_PADRAO))
    except ValueError:
        limite = LIMITE_API_PADRAO
    limite = max(1, min(limite, LIMITE_API_MAXIMO))
    uf = request.args.get('uf', '').strip().upper()
    if uf and uf not in UFS:
        uf = ''
    encontrados = _filtrar(_todos_ativos(), request.args.get('termo', ''), uf,
                           request.args.get('municipio', ''))
    return jsonify({
        'total': len(encontrados),
        'itens': [{
            'id': i['id'], 'nome': i['nome'], 'cnpj': i['cnpj_fmt'],
            'municipio': i['municipio'], 'uf': i['uf'], 'selos': i['selos'],
            'codigo_mapa': i['codigo_mapa'],
        } for i in encontrados[:limite]],
    })


# -------------------------------------------------------
# Rota: GET /produtor/frigorificos/api/cnpj (JSON) - o CNPJ ja existe?
# -------------------------------------------------------
@frigorificos.route('/produtor/frigorificos/api/cnpj')
def api_cnpj():
    bloqueio = _checar_acesso_api()
    if bloqueio:
        return bloqueio
    doc = limpar_documento(request.args.get('documento', ''))
    if len(doc) != 14:
        return jsonify({'encontrado': False})
    existente = _buscar_por_cnpj(doc)
    if existente is None:
        return jsonify({'encontrado': False})
    return jsonify({'encontrado': True, 'frigorifico': {'id': existente['id'], 'nome': existente['nome']}})


def _buscar_por_cnpj(doc):
    with Session(engine) as db:
        f = (
            db.query(Frigorifico)
            .filter(Frigorifico.cpf_cnpj.in_([doc, _mascara_cnpj(doc)]))
            .first()
        )
        return {'id': f.id, 'nome': f.nome} if f else None


# -------------------------------------------------------
# Rota: GET /produtor/frigorificos/novo - formulario de cadastro.
# -------------------------------------------------------
@frigorificos.route('/produtor/frigorificos/novo', methods=['GET'])
def novo():
    bloqueio = _checar_acesso()
    if bloqueio:
        return bloqueio
    dados = {c: '' for c in _CAMPOS_NOVO}
    return render_template('produtor/frigorifico_novo.html', erro=None, dados=dados, **_contexto_base())


# -------------------------------------------------------
# Rota: POST /produtor/frigorificos/novo/salvar - grava o frigorifico.
# -------------------------------------------------------
@frigorificos.route('/produtor/frigorificos/novo/salvar', methods=['POST'])
def novo_salvar():
    bloqueio = _checar_acesso()
    if bloqueio:
        return bloqueio

    dados = {c: (request.form.get(c) or '').strip() for c in _CAMPOS_NOVO}
    for c in ('nome', 'insc_estadual', 'logradouro', 'bairro', 'municipio_nome', 'uf', 'cod_sie', 'cod_sim'):
        dados[c] = dados[c].upper()

    doc = limpar_documento(dados['cpf_cnpj'])
    dados['cpf_cnpj'] = doc
    municipio = buscar_municipio_por_codigo(dados['municipio_codigo'])
    tem_selo = bool(dados['cod_sif'] or dados['cod_sie'] or dados['cod_sim'])

    erro = None
    if not doc:
        erro = 'Informe o CNPJ do Frigorífico.'
    elif len(doc) != 14:
        erro = 'O CNPJ deve ter 14 caracteres.'
    elif not validar_cnpj(doc):
        erro = 'CNPJ incorreto.'
    elif not dados['nome'] or len(dados['nome']) > 150:
        erro = 'Informe o Nome / Razão Social do Frigorífico.'
    elif not municipio:
        erro = 'Escolha o Município na lista.'
    elif not tem_selo:
        erro = 'Informe pelo menos um selo de inspeção: SIF, SIE ou SIM.'
    elif len(dados['cod_sif']) > 7:
        erro = 'SIF excede 7 caracteres.'
    elif len(dados['cod_sie']) > 10:
        erro = 'SIE excede 10 caracteres.'
    elif len(dados['cod_sim']) > 10:
        erro = 'SIM excede 10 caracteres.'
    elif len(dados['insc_estadual']) > 20:
        erro = 'Inscrição Estadual excede 20 caracteres.'
    elif len(dados['codigo_mapa']) > 15:
        erro = 'Código MAPA excede 15 caracteres.'
    elif len(dados['logradouro']) > 60 or len(dados['numero']) > 10 or len(dados['bairro']) > 30 or len(dados['cep']) > 9:
        erro = 'Endereço com campo maior que o permitido (Logradouro 60, Número 10, Bairro 30, CEP 9).'

    if not erro:
        existente = _buscar_por_cnpj(doc)
        if existente is not None:
            erro = 'Este CNPJ já está cadastrado: %s. Procure na lista de Frigoríficos.' % existente['nome']

    if not erro:
        with Session(engine) as db:
            db.add(Frigorifico(
                cpf_cnpj         = doc,
                nome             = dados['nome'],
                insc_estadual    = dados['insc_estadual'] or None,
                codigo_mapa      = dados['codigo_mapa'] or None,
                logradouro       = dados['logradouro'] or None,
                numero           = dados['numero'] or None,
                bairro           = dados['bairro'] or None,
                cep              = dados['cep'] or None,
                municipio_codigo = municipio['codigo_ibge'],
                municipio_nome   = municipio['nome'].upper(),
                uf               = municipio['uf'].upper(),
                cod_sif          = dados['cod_sif'] or None,
                cod_sie          = dados['cod_sie'] or None,
                cod_sim          = dados['cod_sim'] or None,
                ativo            = True,
            ))
            db.commit()
        return redirect(url_for('frigorificos.lista', salvo='1', busca=doc, uf=''))

    return render_template('produtor/frigorifico_novo.html', erro=erro, dados=dados, **_contexto_base())

# =========================================================
# FIM DE ARQUIVO: backend\routers\frigorificos.py
# =========================================================
