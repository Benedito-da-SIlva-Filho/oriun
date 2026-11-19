# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\brincos_fornecedor.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-01 11:00 -03
# ATUALIZADO EM: 2026-10-08 18:55 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Consulta (SOMENTE LEITURA) dos Fabricantes de Brincos
#     cadastrados em tb_1021_fabricantes_brincos (schema public).
#     Primeiro modulo real do Hub de Brincos, na ordem de
#     construcao combinada na Sessao 040 (Fornecedor -> Entrada
#     [ja construido, Sessao 042] -> Disponiveis -> Cancelamento
#     -> Saidas -> Resumo/N.Fiscais).
#
#     Nao ha CRUD nesta tela (sem Novo/Editar/Inativar) - so
#     apresenta o cadastro completo de cada Fabricante para
#     conferencia do usuario. Cadastro/edicao de Fabricante fica
#     fora do escopo do Produtor (mantido via script/SQL direto
#     pela Consiste, ver Sessao 043).
#
#     tb_1021_fabricantes_brincos vive no schema PUBLIC (catalogo
#     unico, nao por Produtor) - por isso esta tela NAO passa pelo
#     fluxo de selecao de Propriedade/Produtor (diferente de
#     brincos_entrada.py). Query direta via Session(engine), mesmo
#     padrao ja usado em _buscar_dados_cabecalho() de
#     brincos_entrada.py para tabelas do schema public.
#
#     Exibe TODOS os Fabricantes (ativos e inativos), com selo de
#     status visivel - decisao de Benedito (Sessao 043): "Cadastro
#     Completo", nao so os campos resumidos.
#
#     v1.0.0: Criacao do modulo (Sessao 043, 01/09/2026, 11:00 -03).
#     v1.1.0: Sessao 091 (08/10/2026, 18:55 -03) - LOGOS QUEBRADOS: a tela montava
#         o endereco da imagem com o texto gravado no banco, ao pe da letra
#         (img/ + logo). Se o texto diferir do nome do arquivo (maiusculas,
#         extensao, prefixo), a imagem quebra. Agora a logo e localizada com a
#         mesma busca tolerante do PIA (pdf_pia._caminho_logo), e o endereco
#         e montado a partir do arquivo realmente encontrado. Sem arquivo
#         achado, aparece o icone padrao (nunca imagem quebrada). Template
#         sem mudanca. REVERSAO: devolver a versao 1.0.0.
# =========================================================

import os
from types import SimpleNamespace
from flask import Blueprint, render_template, redirect, url_for, session, current_app

from sqlalchemy.orm import Session

from backend.database import engine
from backend.models.tb_1021_fabricantes_brincos import Fabricante
from backend.routers.auth import redirecionar_home
from backend.utils.pdf_pia import _caminho_logo


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
brincos_fornecedor = Blueprint('brincos_fornecedor', __name__)


# -------------------------------------------------------
# v1.1.0 - Caminho da logo relativo a img/ (o template junta 'img/' + logo).
# Usa a busca tolerante do PIA; devolve None se o arquivo nao existir ou
# estiver fora de static/img (o template mostra o icone padrao).
# -------------------------------------------------------
def _logo_para_tela(logo_gravado):
    try:
        caminho = _caminho_logo(logo_gravado)
        if not caminho:
            return None
        relativo = os.path.relpath(caminho, current_app.static_folder).replace('\\', '/')
        if not relativo.startswith('img/'):
            return None
        return relativo[len('img/'):]
    except Exception:
        return None


# -------------------------------------------------------
# Rota: GET /produtor/brincos-fornecedor — listagem read-only dos
# Fabricantes de Brincos, ordenada alfabeticamente por nome.
# Requer perfil PRODUTOR ou FAZENDA (mesmo padrao de hubs.ver()).
# -------------------------------------------------------
@brincos_fornecedor.route('/produtor/brincos-fornecedor')
def listar():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    perfil = session.get('usuario_perfil')
    if perfil not in ('PRODUTOR', 'FAZENDA'):
        return redirecionar_home(perfil)

    with Session(engine) as db:
        registros = db.query(Fabricante).order_by(Fabricante.nome).all()
        # Desanexa os objetos da sessao antes de fechar (evita
        # DetachedInstanceError ao acessar atributos no template
        # apos o "with" fechar a conexao) - mesmo padrao ja usado
        # em _listar_fabricantes_ativos() de brincos_entrada.py.
        fabricantes = [
            SimpleNamespace(
                id           = f.id,
                nome         = f.nome,
                logo         = _logo_para_tela(f.logo),
                endereco     = f.endereco,
                complemento  = f.complemento,
                bairro       = f.bairro,
                cidade       = f.cidade,
                uf           = f.uf,
                cep          = f.cep,
                ativo        = f.ativo,
            )
            for f in registros
        ]

    return render_template(
        'produtor/brincos_fornecedor_lista.html',
        fabricantes=fabricantes,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\brincos_fornecedor.py
# =========================================================