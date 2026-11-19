# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\cert_usuarios.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-06-23 14:28 -03
# ATUALIZADO EM: 2026-10-15 08:50 -03
# VERSAO: 1.5.0
#
# DESCRICAO:
#     Rotas do modulo de Usuarios da Certificadora.
#     Acesso exclusivo: perfil CONSISTE (cadastro do Master)
#     e perfis CERTIFICADORA com cargo Master ou Administrativo.
#     - /cert-usuarios              -> lista usuarios da certificadora
#     - /cert-usuarios/novo         -> formulario novo usuario
#     - /cert-usuarios/salvar       -> salva novo ou edicao
#     - /cert-usuarios/editar/<id>  -> formulario edicao
#     - /cert-usuarios/toggle/<id>  -> ativa ou inativa
#     v1.0.0: Criacao do modulo.
#     v1.1.0: joinedload para evitar DetachedInstanceError.
#             Tratamento de login duplicado com IntegrityError.
#     v1.2.0: Senha provisoria gerada automaticamente no cadastro.
#             Email automatico enviado ao novo usuario com login e senha.
#             Removida senha fixa 12345.
#     v1.3.0: Caminhos dos templates atualizados para pasta certificadora/.
#             cert_lista_usuario e cert_cadastro_usuario migrados para certificadora/.
#     v1.4.0: Sessao 010 - Corrigidas 3 referencias ao campo
#             renomeado no banco/models (certificadora_id ->
#             id_certificadora): filtro em lista(), atribuicao
#             na edicao e no cadastro novo, dentro de salvar().
#             Corrigido tambem bug pre-existente em
#             _get_cert_id_filtro(): lia a chave de sessao
#             'usuario_certificadora_id' (nunca gravada) em vez
#             de 'certificadora_id' (chave real gravada pelo
#             login em auth.py). O efeito pratico era o filtro
#             por certificadora nunca funcionar para usuarios
#             de perfil CERTIFICADORA - a lista mostrava
#             usuarios de todas as certificadoras.
#     v1.5.0: Sessao 097 (15/10/2026, 08:50 -03) - ACESSO FACIL (decisao de
#             Benedito: sem excecoes, um padrao so). (1) A copia propria do
#             gerador de senha provisoria foi REMOVIDA; passa a usar
#             gerar_senha_provisoria() de backend/utils/senha_helper.py
#             (3 letras minusculas + 2 numeros). (2) salvar(): o login
#             digitado passa por normalizar_login() (tira espacos do inicio
#             e do fim). Nenhuma outra mudanca.
# =========================================================

from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash
from backend.database import engine
from backend.models import Usuario, Certificadora
from backend.extensions import mail
from flask_mail import Message
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from backend.utils.senha_helper import gerar_senha_provisoria, normalizar_login

# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
cert_usuarios = Blueprint('cert_usuarios', __name__)

# -------------------------------------------------------
# Cargos disponiveis para Certificadora
# -------------------------------------------------------
CARGOS_CERTIFICADORA = [
    'Master',
    'Administrativo',
    'RT',
    'Operacional',
    'Auditor de Campo'
]

# -------------------------------------------------------
# Funcao auxiliar: verifica acesso
# Consiste ve tudo. Master e Administrativo da Cert
# veem apenas a propria certificadora.
# -------------------------------------------------------
def _verificar_acesso():
    if 'usuario_id' not in session:
        return False
    perfil = session.get('usuario_perfil')
    cargo  = session.get('usuario_cargo')
    if perfil == 'CONSISTE':
        return True
    if perfil == 'CERTIFICADORA' and cargo in ('Master', 'Administrativo'):
        return True
    return False

def _get_cert_id_filtro():
    """Retorna o id_certificadora para filtrar. None = ve todas (Consiste)."""
    if session.get('usuario_perfil') == 'CONSISTE':
        return None
    return session.get('certificadora_id')

# (v1.5.0) A senha provisoria vem de backend/utils/senha_helper.py: gerar_senha_provisoria().

# -------------------------------------------------------
# Funcao auxiliar: envia email de boas-vindas
# Enviado automaticamente ao cadastrar novo usuario.
# Contem login, senha provisoria e instrucoes de acesso.
# -------------------------------------------------------
def _enviar_email_boas_vindas(nome, email, login, senha_provisoria):
    try:
        msg = Message(
            subject    = 'Orion SISBOV — Seu acesso foi criado',
            sender     = 'noreply.consisteti@gmail.com',
            recipients = [email]
        )
        msg.body = (
            f'Ola, {nome}!\n\n'
            f'Seu acesso ao Orion SISBOV foi criado. Seguem seus dados:\n\n'
            f'   Login: {login}\n'
            f'   Senha provisoria: {senha_provisoria}\n\n'
            f'Acesse o sistema em: http://localhost:5001/login\n\n'
            f'Na primeira entrada voce sera solicitado a criar uma nova senha.\n\n'
            f'Se nao reconhece este cadastro, contate o administrador.\n\n'
            f'Atenciosamente,\n'
            f'Orion SISBOV — Consiste Informatica'
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f'ERRO ao enviar email de boas-vindas: {e}')
        return False

# -------------------------------------------------------
# Rota: /cert-usuarios — lista usuarios da certificadora
# Consiste ve todos. Master/Administrativo ve apenas a propria.
# -------------------------------------------------------
@cert_usuarios.route('/cert-usuarios')
def lista():
    if not _verificar_acesso():
        return redirect(url_for('auth.login'))

    cert_id = _get_cert_id_filtro()

    with Session(engine) as db:
        query = db.query(Usuario).filter_by(perfil='CERTIFICADORA')
        if cert_id:
            query = query.filter_by(id_certificadora=cert_id)
        lista_usuarios = query.options(
            joinedload(Usuario.certificadora)
        ).order_by(Usuario.nome).all()

        certificadoras = db.query(Certificadora).filter_by(
            ativo=True
        ).order_by(Certificadora.razao_social).all()

    return render_template('certificadora/cert_lista_usuario.html',
        usuarios       = lista_usuarios,
        certificadoras = certificadoras,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'cert_usuarios'
    )

# -------------------------------------------------------
# Rota: /cert-usuarios/novo — formulario novo usuario
# -------------------------------------------------------
@cert_usuarios.route('/cert-usuarios/novo')
def novo():
    if not _verificar_acesso():
        return redirect(url_for('auth.login'))

    cert_id = _get_cert_id_filtro()
    erro    = request.args.get('erro')

    with Session(engine) as db:
        certificadoras = db.query(Certificadora).filter_by(
            ativo=True
        ).order_by(Certificadora.razao_social).all()

    return render_template('certificadora/cert_cadastro_usuario.html',
        usuario_edit   = None,
        certificadoras = certificadoras,
        cargos         = CARGOS_CERTIFICADORA,
        cert_id_fixo   = cert_id,
        erro           = 'Login ja cadastrado! Escolha outro login.' if erro == 'login_duplicado' else None,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'cert_usuarios'
    )

# -------------------------------------------------------
# Rota: /cert-usuarios/editar/<id> — formulario edicao
# -------------------------------------------------------
@cert_usuarios.route('/cert-usuarios/editar/<int:id>')
def editar(id):
    if not _verificar_acesso():
        return redirect(url_for('auth.login'))

    cert_id = _get_cert_id_filtro()

    with Session(engine) as db:
        usuario_edit   = db.get(Usuario, id)
        certificadoras = db.query(Certificadora).filter_by(
            ativo=True
        ).order_by(Certificadora.razao_social).all()

    return render_template('certificadora/cert_cadastro_usuario.html',
        usuario_edit   = usuario_edit,
        certificadoras = certificadoras,
        cargos         = CARGOS_CERTIFICADORA,
        cert_id_fixo   = cert_id,
        erro           = None,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'cert_usuarios'
    )

# -------------------------------------------------------
# Rota: /cert-usuarios/salvar — salva novo ou edicao
# Novo usuario: gera senha provisoria e envia email.
# Edicao: apenas atualiza dados — senha nao e alterada.
# -------------------------------------------------------
@cert_usuarios.route('/cert-usuarios/salvar', methods=['POST'])
def salvar():
    if not _verificar_acesso():
        return redirect(url_for('auth.login'))

    id               = request.form.get('id')
    nome             = request.form.get('nome', '').upper()
    login            = normalizar_login(request.form.get('login'))
    cargo            = request.form.get('cargo')
    email            = request.form.get('email', '').strip().lower()
    certificadora_id = request.form.get('certificadora_id')

    with Session(engine) as db:
        try:
            if id:
                # Edicao — apenas atualiza dados, senha nao muda
                u = db.get(Usuario, int(id))
                u.nome            = nome
                u.login           = login
                u.cargo           = cargo
                u.email           = email
                u.id_certificadora = int(certificadora_id)
                db.commit()

            else:
                # Novo usuario — gera senha provisoria e envia email
                senha_provisoria = gerar_senha_provisoria()

                u = Usuario(
                    nome             = nome,
                    login            = login,
                    senha            = generate_password_hash(senha_provisoria),
                    perfil           = 'CERTIFICADORA',
                    cargo            = cargo,
                    email            = email,
                    id_certificadora = int(certificadora_id),
                    ativo            = True,
                    senha_provisoria = False  # obriga troca no primeiro acesso
                )
                db.add(u)
                db.commit()

                # Envia email com login e senha provisoria
                _enviar_email_boas_vindas(nome, email, login, senha_provisoria)

            return redirect(url_for('cert_usuarios.lista'))

        except IntegrityError:
            db.rollback()
            return redirect(url_for('cert_usuarios.novo') + '?erro=login_duplicado')

# -------------------------------------------------------
# Rota: /cert-usuarios/toggle/<id> — ativa ou inativa
# -------------------------------------------------------
@cert_usuarios.route('/cert-usuarios/toggle/<int:id>', methods=['POST'])
def toggle(id):
    if not _verificar_acesso():
        return redirect(url_for('auth.login'))

    with Session(engine) as db:
        u = db.get(Usuario, id)
        u.ativo = not u.ativo
        db.commit()

    return redirect(url_for('cert_usuarios.lista'))

# =========================================================
# FIM DE ARQUIVO: backend\routers\cert_usuarios.py
# =========================================================