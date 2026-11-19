# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\usuarios.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-06-21 16:50 -03
# ATUALIZADO EM: 2026-10-15 11:20 -03
# VERSAO: 1.12.0
#
# DESCRICAO:
#     Rotas do modulo de Usuarios Consiste.
#     - /usuarios             -> lista todos (perfil CONSISTE)
#     - /usuarios/novo        -> formulario novo (multi-perfil)
#     - /usuarios/salvar      -> salva novo ou edicao
#     - /usuarios/editar/<id> -> formulario edicao
#     - /usuarios/toggle/<id> -> ativa ou inativa
#     - /trocar-senha         -> tela trocar senha obrigatoria
#     v1.0.0: Criacao do modulo.
#     v1.1.0 a v1.6.0: ver historico anterior (nao repetido aqui).
#     v1.7.0: Sessao 032 - campo "Novo Login" em /trocar-senha.
#     v1.8.0: Sessao 034 (continuacao, 07/08/2026) - Tela de
#             cadastro passa a suportar 3 perfis (CONSISTE,
#             CERTIFICADORA, PRODUTOR), escolhidos por um novo
#             dropdown "Perfil" no formulario.
#
#             ESCOPO DESTA VERSAO: somente CONSISTE e PRODUTOR
#             realmente salvam. CERTIFICADORA aparece no dropdown
#             (arquitetura ja fechada - vinculo direto via
#             usuarios.id_certificadora, sem tabela propria de
#             vinculo) mas salvar() devolve erro explicito se
#             escolhido - depende da tela de cadastro de
#             Certificadora, que ainda nao existe (P-013). Nao
#             finge que salvou (regra de qualidade do Benedito:
#             nunca avancar com algo pela metade sem avisar).
#
#             Para perfil PRODUTOR: alem do Usuario, cria tambem
#             o UsuarioVinculo (id_produtor + cargo do ENUM
#             fechado CARGOS_VALIDOS + data_inicio=hoje +
#             data_fim=None) - na MESMA transacao (db.flush()
#             para obter o id do Usuario recem-criado antes do
#             commit final). Se qualquer parte falhar, nada e
#             gravado - nunca fica um Usuario orfao sem vinculo.
#
#             novo() e editar() passam a carregar tambem a lista
#             de Produtores ativos (dropdown de vinculo) e a
#             lista CARGOS_VALIDOS - importada direto de
#             backend.models.usuario_vinculo, fonte unica da
#             verdade (nunca duplicada aqui).
#
#             FORA DO ESCOPO desta versao (fica pendente):
#               - editar() um usuario PRODUTOR existente ainda
#                 nao atualiza o UsuarioVinculo - reaproveita o
#                 fluxo antigo (so mexe em nome/login/cargo do
#                 proprio Usuario). Edicao de vinculo fica para
#                 quando a Frente B for retomada.
#               - lista() continua mostrando so perfil CONSISTE -
#                 usuarios PRODUTOR criados aqui nao aparecem na
#                 listagem ainda (limitacao conhecida, nao e bug).
#     v1.9.0: Sessao 040 (27/08/2026) - Correcao de gap real: a
#             coluna usuarios.email ja existia no model (usada
#             pelo lado Produtor desde a Sessao 039, caso
#             Catarina), mas nenhuma rota deste arquivo gravava
#             email para usuarios CONSISTE. Corrigido nos 3
#             pontos que criam/editam Usuario aqui:
#               - salvar() edicao: grava u.email.
#               - salvar() CONSISTE novo: exige e grava email.
#               - salvar() PRODUTOR novo (criado por esta tela):
#                 exige e grava email.
#             Validacao de tamanho (redundante ao maxlength do
#             HTML, servidor e sempre a fonte da verdade) usando
#             o mesmo limite de usuarios.email = String(100).
#             ESCOPO MANTIDO: lista() continua mostrando so
#             perfil CONSISTE - decisao explicita de Benedito
#             nesta sessao de NAO alterar esse comportamento
#             (usuarios PRODUTOR criados por esta tela continuam
#             sem aparecer na listagem, gap de visibilidade
#             registrado como pendencia, nao resolvido agora).
#     v1.10.0: Sessao 097 (15/10/2026, 08:20 -03) - ACESSO FACIL (decisao de
#             Benedito): login e senha nao diferenciam maiuscula de minuscula.
#               - trocar_senha(): a nova senha e gravada por gerar_hash_senha()
#                 (minusculo); o aviso de login repetido ignora a caixa e
#                 passa a dizer "Este login ja existe. Escolha outro."
#               - salvar(): ao criar usuario CONSISTE ou PRODUTOR e ao editar,
#                 login repetido (ignorando a caixa) mostra aviso amigavel em
#                 vez de erro 500 (pendencia antiga do Diario 096).
#             Nenhuma outra mudanca neste arquivo.
#     v1.11.0: Sessao 097 (15/10/2026, 08:50 -03) - ESPACOS NAS PONTAS:
#               - salvar(): o login digitado passa por normalizar_login()
#                 (tira espacos do inicio e do fim) antes de checar
#                 duplicidade e gravar.
#               - trocar_senha(): nova senha e confirmacao ignoram espacos
#                 do inicio e do fim (comparacao e tamanho minimo).
#             Nenhuma outra mudanca neste arquivo.
#     v1.12.0: Sessao 097 (15/10/2026, 11:20 -03) - AUDITORIA DE PERMISSOES: toggle()/salvar() conferiam so o login; passam a
#             exigir perfil CONSISTE, a mesma regra das telas desta rota. Nenhuma outra mudanca.
# =========================================================

from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, session, make_response
from werkzeug.security import generate_password_hash
from sqlalchemy import func
from backend.utils.senha_helper import gerar_hash_senha, normalizar_login
from backend.database import engine
from backend.models import Usuario, Produtor, UsuarioVinculo
from backend.models.usuario_vinculo import CARGOS_VALIDOS
from backend.routers.auth import redirecionar_home
from sqlalchemy.orm import Session

# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
usuarios = Blueprint('usuarios', __name__)

# -------------------------------------------------------
# Funcao auxiliar: redireciona para home com headers
# anti-cache — impede voltar para tela anterior pelo
# botao Voltar do navegador apos operacoes sensiveis.
# -------------------------------------------------------
def _redirecionar_sem_cache(perfil):
    response = make_response(redirecionar_home(perfil))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    return response

# -------------------------------------------------------
# Rota: /usuarios — lista usuarios Consiste
# Requer perfil CONSISTE.
# v1.9.0: escopo mantido de proposito - so perfil CONSISTE.
# Ver changelog acima.
# -------------------------------------------------------
@usuarios.route('/usuarios')
def lista():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return _redirecionar_sem_cache(session.get('usuario_perfil'))

    with Session(engine) as db:
        lista_usuarios = db.query(Usuario).filter_by(
            perfil='CONSISTE'
        ).order_by(Usuario.nome).all()

    return render_template('consiste/usuario_lista.html',
        usuarios       = lista_usuarios,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'usuarios'
    )

# -------------------------------------------------------
# Rota: /usuarios/novo — formulario novo usuario (multi-perfil)
# Requer perfil CONSISTE.
# -------------------------------------------------------
@usuarios.route('/usuarios/novo')
def novo():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return _redirecionar_sem_cache(session.get('usuario_perfil'))

    with Session(engine) as db:
        lista_produtores = db.query(Produtor).filter_by(
            ativo=True
        ).order_by(Produtor.nome).all()

    return render_template('consiste/usuario_cadastro.html',
        usuario_edit     = None,
        lista_produtores = lista_produtores,
        cargos_validos   = CARGOS_VALIDOS,
        erro             = None,
        usuario_nome     = session.get('usuario_nome'),
        usuario_perfil   = session.get('usuario_perfil'),
        cor_primaria     = session.get('cor_primaria', '#D4370A'),
        nome_sistema     = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo       = 'usuarios'
    )

# -------------------------------------------------------
# Rota: /usuarios/editar/<id> — formulario edicao
# Requer perfil CONSISTE.
# -------------------------------------------------------
@usuarios.route('/usuarios/editar/<int:id>')
def editar(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return _redirecionar_sem_cache(session.get('usuario_perfil'))

    with Session(engine) as db:
        usuario_edit = db.get(Usuario, id)
        lista_produtores = db.query(Produtor).filter_by(
            ativo=True
        ).order_by(Produtor.nome).all()

    return render_template('consiste/usuario_cadastro.html',
        usuario_edit     = usuario_edit,
        lista_produtores = lista_produtores,
        cargos_validos   = CARGOS_VALIDOS,
        erro             = None,
        usuario_nome     = session.get('usuario_nome'),
        usuario_perfil   = session.get('usuario_perfil'),
        cor_primaria     = session.get('cor_primaria', '#D4370A'),
        nome_sistema     = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo       = 'usuarios'
    )

# -------------------------------------------------------
# Rota: /usuarios/salvar — salva novo ou edicao
# v1.9.0: email passa a ser obrigatorio e gravado nos 3
# pontos de criacao/edicao de Usuario deste arquivo.
# -------------------------------------------------------
@usuarios.route('/usuarios/salvar', methods=['POST'])
def salvar():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    id     = request.form.get('id')
    nome   = request.form.get('nome')
    login  = normalizar_login(request.form.get('login'))
    email  = request.form.get('email', '').strip()
    perfil = request.form.get('perfil', 'CONSISTE')

    # -----------------------------------------------------
    # Edicao (fluxo original, agora tambem grava email do
    # proprio Usuario CONSISTE). Login continua travado na
    # tela (nao vem no form de edicao) - mesma regra ja usada
    # do lado Produtor: so o dono da conta troca o proprio
    # login, via /trocar-senha.
    # -----------------------------------------------------
    if id:
        cargo = request.form.get('cargo')

        if not email:
            return 'Sr. Usuário(a), o e-mail é obrigatório.', 400
        if len(email) > 100:
            return 'Sr. Usuário(a), o e-mail deve ter no máximo 100 caracteres.', 400

        with Session(engine) as db:
            u = db.get(Usuario, int(id))
            if db.query(Usuario).filter(
                func.lower(Usuario.login) == (login or '').lower(),
                Usuario.id != u.id
            ).first():
                return 'Sr. Usuário(a), este login já existe. Escolha outro.', 400
            u.nome  = nome
            u.login = login
            u.email = email
            u.cargo = cargo
            db.commit()
        return redirect(url_for('usuarios.lista'))

    # -----------------------------------------------------
    # Funcao auxiliar interna: reexibe o formulario de novo
    # cadastro com uma mensagem de erro, sem perder o que ja
    # foi carregado (lista de Produtores/Cargos).
    # -----------------------------------------------------
    def _reexibir_com_erro(mensagem_erro):
        with Session(engine) as db:
            lista_produtores = db.query(Produtor).filter_by(
                ativo=True
            ).order_by(Produtor.nome).all()
        return render_template('consiste/usuario_cadastro.html',
            usuario_edit     = None,
            lista_produtores = lista_produtores,
            cargos_validos   = CARGOS_VALIDOS,
            erro             = mensagem_erro,
            usuario_nome     = session.get('usuario_nome'),
            usuario_perfil   = session.get('usuario_perfil'),
            cor_primaria     = session.get('cor_primaria', '#D4370A'),
            nome_sistema     = session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo       = 'usuarios'
        )

    # -----------------------------------------------------
    # Validacao de email — comum aos ramos de criacao nova
    # (CERTIFICADORA fica fora, pois nem chega a salvar).
    # -----------------------------------------------------
    if perfil in ('CONSISTE', 'PRODUTOR'):
        if not email:
            return _reexibir_com_erro('Sr. Usuário(a), o e-mail é obrigatório.')
        if len(email) > 100:
            return _reexibir_com_erro('Sr. Usuário(a), o e-mail deve ter no máximo 100 caracteres.')

    # -----------------------------------------------------
    # Novo usuario CERTIFICADORA: arquitetura ja fechada
    # (vinculo direto via usuarios.id_certificadora), mas a
    # tela de cadastro de Certificadora ainda nao existe
    # (P-013) - nao finge que salvou.
    # -----------------------------------------------------
    if perfil == 'CERTIFICADORA':
        return _reexibir_com_erro(
            'Sr. Usuário(a), o cadastro de usuário Certificadora ainda não '
            'está disponível — depende da tela de cadastro de Certificadora '
            '(pendência P-013), que ainda não foi construída.'
        )

    # -----------------------------------------------------
    # Novo usuario PRODUTOR: cria Usuario + UsuarioVinculo na
    # MESMA transacao (db.flush() para obter o id do Usuario
    # recem-criado antes do commit final). Se qualquer parte
    # falhar, nada e gravado - nunca fica Usuario orfao.
    # -----------------------------------------------------
    if perfil == 'PRODUTOR':
        id_produtor_str = request.form.get('id_produtor', '').strip()
        cargo_vinculo   = request.form.get('cargo_vinculo', '').strip()

        if not id_produtor_str:
            return _reexibir_com_erro('Sr. Usuário(a), selecione o Produtor ao qual este usuário será vinculado.')

        if cargo_vinculo not in CARGOS_VALIDOS:
            return _reexibir_com_erro('Sr. Usuário(a), selecione um Cargo válido para o vínculo.')

        with Session(engine) as db_dup:
            if db_dup.query(Usuario).filter(
                func.lower(Usuario.login) == (login or '').lower()
            ).first():
                return _reexibir_com_erro('Sr. Usuário(a), este login já existe. Escolha outro.')

        with Session(engine) as db:
            novo_usuario = Usuario(
                nome              = nome,
                login             = login,
                email             = email,
                senha             = generate_password_hash('12345'),
                perfil            = 'PRODUTOR',
                id_certificadora  = None,
                ativo             = True,
                # False = senha provisoria de verdade (ver auth.py) -
                # obriga troca no primeiro acesso, mesmo padrao ja
                # usado no cadastro CONSISTE abaixo.
                senha_provisoria  = False
            )
            db.add(novo_usuario)
            db.flush()  # gera novo_usuario.id sem fechar a transacao

            novo_vinculo = UsuarioVinculo(
                id_usuario    = novo_usuario.id,
                id_produtor   = int(id_produtor_str),
                cargo         = cargo_vinculo,
                data_inicio   = date.today(),
                data_fim      = None
            )
            db.add(novo_vinculo)

            db.commit()

        return redirect(url_for('usuarios.lista'))

    # -----------------------------------------------------
    # Novo usuario CONSISTE (fluxo original, agora grava email)
    # -----------------------------------------------------
    cargo = request.form.get('cargo')
    with Session(engine) as db_dup:
        if db_dup.query(Usuario).filter(
            func.lower(Usuario.login) == (login or '').lower()
        ).first():
            return _reexibir_com_erro('Sr. Usuário(a), este login já existe. Escolha outro.')
    with Session(engine) as db:
        novo_usuario = Usuario(
            nome              = nome,
            login             = login,
            email             = email,
            senha             = generate_password_hash('12345'),
            perfil            = 'CONSISTE',
            cargo             = cargo,
            id_certificadora  = None,
            ativo             = True,
            senha_provisoria  = False
        )
        db.add(novo_usuario)
        db.commit()

    return redirect(url_for('usuarios.lista'))

# -------------------------------------------------------
# Rota: /usuarios/toggle/<id> — ativa ou inativa
# -------------------------------------------------------
@usuarios.route('/usuarios/toggle/<int:id>', methods=['POST'])
def toggle(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return _redirecionar_sem_cache(session.get('usuario_perfil'))

    with Session(engine) as db:
        u = db.get(Usuario, id)
        u.ativo = not u.ativo
        db.commit()

    return redirect(url_for('usuarios.lista'))

# -------------------------------------------------------
# Rota: /trocar-senha — troca de senha obrigatoria
# (INALTERADA nesta versao - identica a v1.7.0)
# -------------------------------------------------------
@usuarios.route('/trocar-senha', methods=['GET', 'POST'])
def trocar_senha():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    erro    = None
    sucesso = None

    with Session(engine) as db:
        u = db.get(Usuario, session['usuario_id'])
        eh_provisoria = not u.senha_provisoria
        login_atual   = u.login

    if request.method == 'POST':
        senha_nova = (request.form.get('senha_nova') or '').strip()
        senha_conf = (request.form.get('senha_confirmacao') or '').strip()
        novo_login = request.form.get('novo_login', '').strip()

        with Session(engine) as db:
            u = db.get(Usuario, session['usuario_id'])

            if novo_login and novo_login.lower() != (u.login or '').lower():
                ja_existe = db.query(Usuario).filter(
                    func.lower(Usuario.login) == novo_login.lower(),
                    Usuario.id != u.id
                ).first()
                if ja_existe:
                    erro = 'Este login ja existe. Escolha outro.'

            if not erro:
                if eh_provisoria:
                    if senha_nova != senha_conf:
                        erro = 'Nova senha e confirmacao nao conferem!'
                    elif len(senha_nova) < 6:
                        erro = 'A nova senha deve ter pelo menos 6 caracteres!'
                    else:
                        if novo_login:
                            u.login = novo_login
                        u.senha            = gerar_hash_senha(senha_nova)
                        u.senha_provisoria = True
                        db.commit()
                        return _redirecionar_sem_cache(session.get('usuario_perfil'))
                else:
                    if senha_nova != senha_conf:
                        erro = 'Nova senha e confirmacao nao conferem!'
                    elif len(senha_nova) < 6:
                        erro = 'A nova senha deve ter pelo menos 6 caracteres!'
                    else:
                        if novo_login:
                            u.login = novo_login
                        u.senha = gerar_hash_senha(senha_nova)
                        db.commit()
                        sucesso = 'Senha alterada com sucesso!'

            login_atual = u.login

    return render_template('usuarios/usuario_senha.html',
        erro           = erro,
        sucesso        = sucesso,
        eh_provisoria  = eh_provisoria,
        login_atual    = login_atual,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV')
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\usuarios.py
# =========================================================