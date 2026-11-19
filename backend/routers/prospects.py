# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\routers
# MODULO:       backend\routers\prospects.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-08-11 19:33 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO:       1.2.0
# v1.2.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Convite comercial de Prospects - Consiste convida um
#     Produtor prospect a conhecer o Orion SISBOV, reaproveitando
#     o link fixo do Convite Publico ja existente (/convite,
#     backend/routers/convite.py - generico, sem token, "boca a
#     boca" por desenho da Sessao 032). Esta rota NAO cria nada
#     em Produtor/Propriedade - so registra o disparo do convite
#     (convite_prospects) e manda o e-mail ou monta o link de
#     WhatsApp. O cadastro de fato, se o prospect aceitar,
#     acontece depois, normalmente, via /convite - sem nenhum
#     vinculo tecnico com este registro.
#
#     - /prospects              -> formulario (Nome + Email +
#                                   Telefone) + lista de quem ja
#                                   foi convidado (com canal usado)
#     - /prospects/enviar        -> valida, envia o e-mail (Flask-
#                                   Mail, mesmo mecanismo ja usado
#                                   em esqueci_senha()/convite.py)
#                                   e grava o registro (canal=EMAIL)
#     - /prospects/enviar_whatsapp -> valida (nome+email+telefone
#                                   obrigatorios), grava o registro
#                                   (canal=WHATSAPP) e redireciona
#                                   para o link wa.me com mensagem
#                                   pre-preenchida - envio final
#                                   sempre manual (clique do usuario
#                                   dentro do WhatsApp)
#
#     Exclusivo perfil CONSISTE.
#
#     v1.0.0: Criacao do modulo (Sessao 034, continuacao 6).
#             Fase 1: so e-mail.
#     v1.1.0: Adicionado canal WhatsApp (Sessao 034, continuacao
#             8). Campo telefone (opcional) no formulario; novo
#             botao/rota enviar_whatsapp(); mensagem curta e
#             informal (decisao de Benedito); link wa.me montado
#             com urllib.parse.quote, mesmo padrao ja usado na
#             Tela Vitrine (templates/convite/vitrine.html).
#             Permite registros duplicados por prospect - nao ha
#             checagem de unicidade por email/nome.
# =========================================================

from flask import Blueprint, render_template, request, redirect, url_for, session
from urllib.parse import quote
from backend.database import engine
from backend.models import ConviteProspect, Usuario
from backend.utils.validadores import email_dominio_existe
from backend.extensions import mail
from flask_mail import Message
from sqlalchemy.orm import Session

prospects = Blueprint('prospects', __name__)


# -------------------------------------------------------
# Funcao auxiliar: busca todos os convites ja enviados,
# mais recente primeiro, ja combinados com o nome do usuario
# Consiste que enviou cada um. Reaproveitada em lista() e em
# todos os caminhos de erro/sucesso de enviar() e
# enviar_whatsapp() (formulario reexibido com a lista
# atualizada, nunca em branco).
# -------------------------------------------------------
def _buscar_convidados(db):
    linhas = db.query(ConviteProspect, Usuario).join(
        Usuario, Usuario.id == ConviteProspect.id_usuario_consiste
    ).order_by(ConviteProspect.enviado_em.desc()).all()

    return [
        {
            'nome':        prospect.nome,
            'email':       prospect.email,
            'telefone':    prospect.telefone,
            'canal':       prospect.canal,
            'enviado_em':  prospect.enviado_em,
            'enviado_por': usuario.nome,
        }
        for prospect, usuario in linhas
    ]


# -------------------------------------------------------
# Funcao auxiliar: limpa o telefone deixando so digitos
# (mascara e limpa tanto no input quanto no submit - regra
# do projeto - mas nunca confiar so na camada HTML/JS, por
# isso a limpeza redundante aqui no servidor).
# -------------------------------------------------------
def _limpar_telefone(telefone_bruto):
    return ''.join(c for c in (telefone_bruto or '') if c.isdecimal())


# -------------------------------------------------------
# Rota: /prospects — formulario + lista de convidados
# -------------------------------------------------------
@prospects.route('/prospects')
def lista():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    with Session(engine) as db:
        convidados = _buscar_convidados(db)

    return render_template('consiste/prospects.html',
        convidados     = convidados,
        nome           = '',
        email          = '',
        telefone       = '',
        erro           = None,
        sucesso        = None,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'prospects'
    )


# -------------------------------------------------------
# Rota: /prospects/enviar — valida, envia o e-mail e grava
# (canal=EMAIL)
# -------------------------------------------------------
@prospects.route('/prospects/enviar', methods=['POST'])
def enviar():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    nome     = request.form.get('nome', '').strip()
    email    = request.form.get('email', '').strip().lower()
    telefone = _limpar_telefone(request.form.get('telefone', ''))

    erro = None
    if not nome or not email:
        erro = 'Nome e Email sao obrigatorios.'
    elif not email_dominio_existe(email):
        erro = 'E-mail incorreto ou domínio inexistente.'

    if erro:
        with Session(engine) as db:
            convidados = _buscar_convidados(db)

        return render_template('consiste/prospects.html',
            convidados     = convidados,
            nome           = nome,
            email          = email,
            telefone       = telefone,
            erro           = erro,
            sucesso        = None,
            usuario_nome   = session.get('usuario_nome'),
            usuario_perfil = session.get('usuario_perfil'),
            cor_primaria   = session.get('cor_primaria', '#D4370A'),
            nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo     = 'prospects'
        )

    # Link fixo do Convite Publico (sem token - ver DESCRICAO
    # no topo do arquivo). _external=True gera a URL completa
    # (com dominio), necessaria dentro do corpo do e-mail.
    link_convite = url_for('convite.convite_etapa1', _external=True)

    try:
        msg = Message(
            subject    = 'Orion SISBOV — Conheça a plataforma de rastreabilidade bovina',
            sender     = 'noreply.consisteti@gmail.com',
            recipients = [email]
        )
        msg.body = (
            f'Ola, {nome}!\n\n'
            f'Somos da Consiste Informatica e desenvolvemos o Orion SISBOV, '
            f'uma plataforma de rastreabilidade bovina para produtores e '
            f'certificadoras credenciadas pelo MAPA.\n\n'
            f'Gostariamos de te convidar a conhecer o sistema. Voce pode '
            f'fazer seu cadastro gratuito pelo link abaixo:\n\n'
            f'{link_convite}\n\n'
            f'Qualquer duvida, estamos a disposicao.\n\n'
            f'Atenciosamente,\n'
            f'Equipe Consiste Informatica'
        )
        mail.send(msg)
    except Exception as erro_envio:
        print(f'ERRO Flask-Mail (Convite Prospect): {erro_envio}')
        with Session(engine) as db:
            convidados = _buscar_convidados(db)

        return render_template('consiste/prospects.html',
            convidados     = convidados,
            nome           = nome,
            email          = email,
            telefone       = telefone,
            erro           = 'Não foi possível enviar o e-mail. Tente novamente.',
            sucesso        = None,
            usuario_nome   = session.get('usuario_nome'),
            usuario_perfil = session.get('usuario_perfil'),
            cor_primaria   = session.get('cor_primaria', '#D4370A'),
            nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo     = 'prospects'
        )

    with Session(engine) as db:
        novo_convite = ConviteProspect(
            nome                = nome,
            email               = email,
            telefone            = telefone or None,
            canal               = 'EMAIL',
            id_usuario_consiste = session.get('usuario_id'),
        )
        db.add(novo_convite)
        db.commit()

    with Session(engine) as db:
        convidados = _buscar_convidados(db)

    return render_template('consiste/prospects.html',
        convidados     = convidados,
        nome           = '',
        email          = '',
        telefone       = '',
        erro           = None,
        sucesso        = f'Convite enviado para {nome} ({email}).',
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'prospects'
    )


# -------------------------------------------------------
# Rota: /prospects/enviar_whatsapp — valida (nome+email+
# telefone), grava o registro (canal=WHATSAPP) e redireciona
# para o link wa.me com mensagem pre-preenchida. Sem custo,
# sem API paga - o envio final e sempre um clique manual do
# usuario dentro do WhatsApp (mesmo padrao ja usado e testado
# na Tela Vitrine, templates/convite/vitrine.html).
# -------------------------------------------------------
@prospects.route('/prospects/enviar_whatsapp', methods=['POST'])
def enviar_whatsapp():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    nome     = request.form.get('nome', '').strip()
    email    = request.form.get('email', '').strip().lower()
    telefone = _limpar_telefone(request.form.get('telefone', ''))

    erro = None
    if not nome or not email:
        erro = 'Nome e Email sao obrigatorios.'
    elif not email_dominio_existe(email):
        erro = 'E-mail incorreto ou domínio inexistente.'
    elif not telefone:
        erro = 'Telefone é obrigatório para enviar por WhatsApp.'
    elif len(telefone) != 11:
        erro = 'Telefone incorreto — informe DDD + número (11 dígitos).'

    if erro:
        with Session(engine) as db:
            convidados = _buscar_convidados(db)

        return render_template('consiste/prospects.html',
            convidados     = convidados,
            nome           = nome,
            email          = email,
            telefone       = telefone,
            erro           = erro,
            sucesso        = None,
            usuario_nome   = session.get('usuario_nome'),
            usuario_perfil = session.get('usuario_perfil'),
            cor_primaria   = session.get('cor_primaria', '#D4370A'),
            nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo     = 'prospects'
        )

    # Link fixo do Convite Publico (sem token - ver DESCRICAO
    # no topo do arquivo). _external=True gera a URL completa
    # (com dominio), necessaria dentro da mensagem do WhatsApp.
    link_convite = url_for('convite.convite_etapa1', _external=True)

    mensagem = (
        f'Oi, {nome}! 👋 Aqui é da Consiste Informática. Criamos o Orion '
        f'SISBOV, uma plataforma de rastreabilidade bovina bem prática pra '
        f'produtores e certificadoras do MAPA. Dá uma conferida: {link_convite}'
    )
    link_whatsapp = f'https://wa.me/55{telefone}?text={quote(mensagem)}'

    with Session(engine) as db:
        novo_convite = ConviteProspect(
            nome                = nome,
            email               = email,
            telefone            = telefone,
            canal               = 'WHATSAPP',
            id_usuario_consiste = session.get('usuario_id'),
        )
        db.add(novo_convite)
        db.commit()

    return redirect(link_whatsapp)

# =========================================================
# FIM DE ARQUIVO: backend\routers\prospects.py
# =========================================================