# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\certificadoras.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-06-21 14:53 -03
# ATUALIZADO EM: 2026-10-15 11:20 -03
# VERSAO: 1.6.1
#
# DESCRICAO:
#     Rotas do modulo de Certificadoras.
#     - /certificadoras                    -> lista todas
#     - /certificadoras/nova               -> formulario nova
#     - /certificadoras/salvar             -> salva nova ou edicao
#     - /certificadoras/editar/<id>        -> formulario edicao
#     - /certificadoras/toggle/<id>        -> ativa ou inativa
#     - /certificadoras/trocar-master/<id> -> troca o Master
#     - /certificadoras/salvar-master      -> salva novo Master
#     v1.0.0: Criacao do modulo.
#     v1.1.0: Campo nome -> razao_social. Adicionado nome_fantasia.
#     v1.2.0: Cadastro do Usuario Master integrado ao formulario.
#             Gera senha provisoria e envia email automatico ao Master.
#     v1.3.0: Rota trocar-master adicionada.
#             Regra: apenas um Master ativo por Certificadora.
#             Inativa Master antigo e cadastra novo automaticamente.
#     v1.4.0: Caminhos dos templates atualizados para pasta consiste/.
#             certificadora_lista, certificadora_cadastro e
#             certificadora_trocar_master migrados para consiste/.
#     v1.5.0: Sessao 010 - Corrigidas 5 referencias ao campo
#             renomeado no banco/models (certificadora_id ->
#             id_certificadora): busca do Master em editar(),
#             cadastro do Master em salvar(), busca do Master
#             atual em trocar_master(), busca do Master antigo
#             e cadastro do novo Master em salvar_master().
#     v1.6.0: Sessao 097 (15/10/2026, 08:50 -03) - ACESSO FACIL (decisao de
#             Benedito: sem excecoes, um padrao so). A copia propria do
#             gerador de senha provisoria foi REMOVIDA; passa a usar
#             gerar_senha_provisoria() de backend/utils/senha_helper.py
#             (3 letras minusculas + 2 numeros). Nenhuma outra mudanca.
#     v1.6.1: Sessao 097 (15/10/2026, 11:20 -03) - AUDITORIA DE PERMISSOES: salvar(), salvar_master() e toggle() conferiam so o
#             login; passam a exigir perfil CONSISTE, a mesma regra das telas. Nenhuma outra mudanca.
# =========================================================

from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash
from backend.database import engine
from backend.models import Certificadora, Usuario
from backend.extensions import mail
from flask_mail import Message
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.utils.senha_helper import gerar_senha_provisoria

certificadoras = Blueprint('certificadoras', __name__)

# (v1.6.0) A senha provisoria vem de backend/utils/senha_helper.py: gerar_senha_provisoria().

# -------------------------------------------------------
# Funcao auxiliar: envia email de boas-vindas ao Master
# -------------------------------------------------------
def _enviar_email_master(nome, email, login, senha_provisoria):
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
        print(f'ERRO ao enviar email do Master: {e}')
        return False

# -------------------------------------------------------
# Rota: /certificadoras — lista todas
# Requer perfil CONSISTE.
# -------------------------------------------------------
@certificadoras.route('/certificadoras')
def lista():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    with Session(engine) as db:
        lista_cert = db.query(Certificadora).order_by(Certificadora.razao_social).all()

    return render_template('consiste/certificadora_lista.html',
        certificadoras = lista_cert,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'certificadoras'
    )

# -------------------------------------------------------
# Rota: /certificadoras/nova — formulario nova
# Requer perfil CONSISTE.
# -------------------------------------------------------
@certificadoras.route('/certificadoras/nova')
def nova():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    erro = request.args.get('erro')

    return render_template('consiste/certificadora_cadastro.html',
        certificadora  = None,
        master         = None,
        erro           = 'Login ja cadastrado! Escolha outro login.' if erro == 'login_duplicado' else None,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'certificadoras'
    )

# -------------------------------------------------------
# Rota: /certificadoras/editar/<id> — formulario edicao
# Busca o Master ativo da Certificadora para exibir.
# Requer perfil CONSISTE.
# -------------------------------------------------------
@certificadoras.route('/certificadoras/editar/<int:id>')
def editar(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    with Session(engine) as db:
        certificadora = db.get(Certificadora, id)
        master = db.query(Usuario).filter_by(
            id_certificadora = id,
            perfil            = 'CERTIFICADORA',
            cargo             = 'Master',
            ativo             = True
        ).first()

    return render_template('consiste/certificadora_cadastro.html',
        certificadora  = certificadora,
        master         = master,
        erro           = None,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'certificadoras'
    )

# -------------------------------------------------------
# Rota: /certificadoras/salvar — salva nova ou edicao
# Nova: cadastra Certificadora + Usuario Master + envia email.
# Edicao: apenas atualiza dados da Certificadora.
# -------------------------------------------------------
@certificadoras.route('/certificadoras/salvar', methods=['POST'])
def salvar():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    id            = request.form.get('id')
    razao_social  = request.form.get('razao_social', '').upper()
    nome_fantasia = request.form.get('nome_fantasia', '').upper()
    cnpj          = request.form.get('cnpj')
    insc_est      = request.form.get('inscricao_est')
    email         = request.form.get('email')
    telefone      = request.form.get('telefone')
    endereco      = request.form.get('endereco', '').upper()
    cidade        = request.form.get('cidade', '').upper()
    uf            = request.form.get('uf', '').upper()
    cep           = request.form.get('cep')

    master_nome  = request.form.get('master_nome', '').upper()
    master_login = request.form.get('master_login', '').strip()
    master_email = request.form.get('master_email', '').strip().lower()

    if not nome_fantasia:
        nome_fantasia = razao_social

    with Session(engine) as db:
        try:
            if id:
                # Edicao — apenas atualiza dados da Certificadora
                cert = db.get(Certificadora, int(id))
                cert.razao_social  = razao_social
                cert.nome_fantasia = nome_fantasia
                cert.cnpj          = cnpj
                cert.inscricao_est = insc_est
                cert.email         = email
                cert.telefone      = telefone
                cert.endereco      = endereco
                cert.cidade        = cidade
                cert.uf            = uf
                cert.cep           = cep
                db.commit()

            else:
                # Nova — cadastra Certificadora + Master + envia email
                cert = Certificadora(
                    razao_social  = razao_social,
                    nome_fantasia = nome_fantasia,
                    cnpj          = cnpj,
                    inscricao_est = insc_est,
                    email         = email,
                    telefone      = telefone,
                    endereco      = endereco,
                    cidade        = cidade,
                    uf            = uf,
                    cep           = cep,
                    ativo         = True
                )
                db.add(cert)
                db.flush()

                senha_provisoria = gerar_senha_provisoria()

                master = Usuario(
                    nome              = master_nome,
                    login             = master_login,
                    senha             = generate_password_hash(senha_provisoria),
                    perfil            = 'CERTIFICADORA',
                    cargo             = 'Master',
                    email             = master_email,
                    id_certificadora  = cert.id,
                    ativo             = True,
                    senha_provisoria  = False
                )
                db.add(master)
                db.commit()

                _enviar_email_master(master_nome, master_email, master_login, senha_provisoria)

            return redirect(url_for('certificadoras.lista'))

        except IntegrityError:
            db.rollback()
            return redirect(url_for('certificadoras.nova') + '?erro=login_duplicado')

# -------------------------------------------------------
# Rota: /certificadoras/trocar-master/<id> — formulario troca
# Exibe Master atual em somente leitura + campos do novo Master.
# Requer perfil CONSISTE.
# -------------------------------------------------------
@certificadoras.route('/certificadoras/trocar-master/<int:id>')
def trocar_master(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    erro = request.args.get('erro')

    with Session(engine) as db:
        certificadora = db.get(Certificadora, id)
        master_atual = db.query(Usuario).filter_by(
            id_certificadora = id,
            perfil            = 'CERTIFICADORA',
            cargo             = 'Master',
            ativo             = True
        ).first()

    return render_template('consiste/certificadora_trocar_master.html',
        certificadora  = certificadora,
        master_atual   = master_atual,
        erro           = 'Login ja cadastrado! Escolha outro login.' if erro == 'login_duplicado' else None,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'certificadoras'
    )

# -------------------------------------------------------
# Rota: /certificadoras/salvar-master — salva novo Master
# Inativa Master antigo e cadastra novo automaticamente.
# Garante regra: apenas um Master ativo por Certificadora.
# -------------------------------------------------------
@certificadoras.route('/certificadoras/salvar-master', methods=['POST'])
def salvar_master():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    cert_id      = int(request.form.get('cert_id'))
    master_nome  = request.form.get('master_nome', '').upper()
    master_login = request.form.get('master_login', '').strip()
    master_email = request.form.get('master_email', '').strip().lower()

    with Session(engine) as db:
        try:
            # Inativa o Master atual
            master_antigo = db.query(Usuario).filter_by(
                id_certificadora = cert_id,
                perfil            = 'CERTIFICADORA',
                cargo             = 'Master',
                ativo             = True
            ).first()

            if master_antigo:
                master_antigo.ativo = False

            # Cadastra o novo Master com senha provisoria
            senha_provisoria = gerar_senha_provisoria()

            novo_master = Usuario(
                nome              = master_nome,
                login             = master_login,
                senha             = generate_password_hash(senha_provisoria),
                perfil            = 'CERTIFICADORA',
                cargo             = 'Master',
                email             = master_email,
                id_certificadora  = cert_id,
                ativo             = True,
                senha_provisoria  = False
            )
            db.add(novo_master)
            db.commit()

            # Envia email ao novo Master
            _enviar_email_master(master_nome, master_email, master_login, senha_provisoria)

            return redirect(url_for('certificadoras.lista'))

        except IntegrityError:
            db.rollback()
            return redirect(
                url_for('certificadoras.trocar_master', id=cert_id) + '?erro=login_duplicado'
            )

# -------------------------------------------------------
# Rota: /certificadoras/toggle/<id> — ativa ou inativa
# -------------------------------------------------------
@certificadoras.route('/certificadoras/toggle/<int:id>', methods=['POST'])
def toggle(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    with Session(engine) as db:
        cert = db.get(Certificadora, id)
        cert.ativo = not cert.ativo
        db.commit()

    return redirect(url_for('certificadoras.lista'))

# =========================================================
# FIM DE ARQUIVO: backend\routers\certificadoras.py
# =========================================================