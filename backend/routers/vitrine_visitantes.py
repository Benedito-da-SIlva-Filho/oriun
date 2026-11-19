# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\routers
# MODULO:       backend\routers\vitrine_visitantes.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-08-13 13:20 -03
# ATUALIZADO EM: 2026-08-13 13:20 -03
# VERSAO:       1.0.0
#
# DESCRICAO:
#     Tela "Visitantes da Vitrine" (Cenario 2, Sessao 034
#     continuacao 9) - o gatilho de reconexao da Etapa 2 do
#     Convite Publico (ver convite.py v2.3.0, nota de PAUSA em
#     v2.2.0), definido nesta sessao. NAO reaproveita a Etapa 2
#     original (que exige a Propriedade preenchida manualmente por
#     quem confirma) - em vez disso, fluxo proprio e mais simples:
#     a CONSISTE, depois de conversar com o visitante (WhatsApp,
#     CTA da Tela Vitrine), converte ele em cliente real com 1
#     clique, sem pedir dados de Propriedade antes. O Produtor
#     completa o resto sozinho no primeiro acesso, reaproveitando
#     o MESMO padrao ja usado no Convite Publico
#     (cadastro_completo=False + auth.py/produtor_home()) e o
#     mesmo padrao de criacao de acesso ja usado em produtores.py/
#     criar_acesso() (Cenario 1, sessao anterior).
#
#     - GET  /vitrine-visitantes             -> lista visitantes
#            ainda NAO convertidos (mais recente primeiro). Antes
#            de montar a lista, roda _auto_detectar_conversoes()
#            (ver abaixo).
#     - POST /vitrine-visitantes/converter/<id> -> dispara a
#            transacao de criacao (Produtor + Propriedade +
#            PropriedadeProdutor + Usuario + UsuarioVinculo),
#            envia e-mail com login/senha, marca convertido_em/
#            id_produtor_criado, e re-renderiza a lista com banner
#            de sucesso + link opcional de WhatsApp.
#
#     Exclusivo perfil CONSISTE. Sem item proprio no menu lateral
#     por enquanto (decisao de Benedito) - acesso via link direto,
#     mesmo padrao ja usado em prospects.html.
#
#     Auto-deteccao de conversao (decisao de Benedito): se um
#     visitante ainda sem convertido_em ja tiver um Produtor com o
#     mesmo CPF/CNPJ por QUALQUER outro caminho (ex.: a Consiste
#     cadastrou ele manualmente, ou ele fez o Convite de novo e
#     completou a Etapa 2 antiga), a lista se autocorrige sozinha
#     a cada carregamento - vincula id_produtor_criado/
#     convertido_em sem aviso, sem acao manual, e o visitante some
#     da lista na mesma renderizacao.
#
#     Placeholders da Propriedade criada na conversao (mesmo
#     criterio ja usado em convite.py/_processar_etapa2 - "fica
#     algo ficticio obrigando a ser atualizado", mas agora cobrindo
#     TODOS os campos obrigatorios, ja que ninguem digita nada
#     antes da conversao):
#       nome = 'A COMPLETAR' (obrigatorio no banco - propriedade.py)
#       municipio = 'A COMPLETAR' (obrigatorio)
#       uf = 'XX' (obrigatorio)
#       inscricao_estadual = None (NAO obrigatorio - fica em
#           branco, confirmado direto no model antes de codar,
#           regra de Benedito: "se foram campos obrigatorios sim
#           caso contrario deixa em branco")
#       tipo = 'MISTA', roteiro_acesso = 'A COMPLETAR',
#           area_hectares = 0, cadastro_completo = False (mesmos
#           placeholders ja usados no Convite Publico)
#
#     v1.0.0: Criacao do modulo (Sessao 034, continuacao 9).
# =========================================================

import urllib.parse
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, session
from backend.database import engine
from backend.models import VitrineVisitante, Produtor, Propriedade, PropriedadeProdutor, Usuario, UsuarioVinculo
from backend.utils.senha_helper import gerar_senha_provisoria
from backend.extensions import mail
from flask_mail import Message
from werkzeug.security import generate_password_hash
from sqlalchemy.orm import Session

vitrine_visitantes = Blueprint('vitrine_visitantes', __name__)

# -------------------------------------------------------
# DDI Brasil - mesmo padrao ja usado em produtores.py/
# criar_acesso() (Cenario 1) para montar o link wa.me.
# -------------------------------------------------------
DDI_BRASIL = '55'


# -------------------------------------------------------
# Funcao auxiliar: auto-deteccao de conversao (ver DESCRICAO
# no topo do arquivo). Roda a cada carregamento da lista -
# para cada visitante ainda sem convertido_em, confere se o
# CPF/CNPJ ja virou Produtor por QUALQUER caminho. Se sim,
# vincula sozinho, sem aviso, sem acao manual. Decisao de
# Benedito (Sessao 034 cont. 9): "se ele e visitante mas a
# Consiste o cadastrou, apos salvar, check na lista de
# visitantes e altera o status".
# -------------------------------------------------------
def _auto_detectar_conversoes(db):
    pendentes = db.query(VitrineVisitante).filter(
        VitrineVisitante.convertido_em.is_(None)
    ).all()

    algo_mudou = False
    for visitante in pendentes:
        produtor_existente = db.query(Produtor).filter_by(
            cpf_cnpj=visitante.cpf_cnpj
        ).first()
        if produtor_existente:
            visitante.convertido_em = datetime.now()
            visitante.id_produtor_criado = produtor_existente.id
            algo_mudou = True

    if algo_mudou:
        db.commit()


# -------------------------------------------------------
# Funcao auxiliar: busca todos os visitantes ainda NAO
# convertidos (convertido_em IS NULL), mais recente primeiro.
# Reaproveitada em lista() e no retorno de converter() (lista
# atualizada apos a conversao, nunca em branco).
# -------------------------------------------------------
def _buscar_visitantes_pendentes(db):
    return db.query(VitrineVisitante).filter(
        VitrineVisitante.convertido_em.is_(None)
    ).order_by(VitrineVisitante.visitado_em.desc()).all()


# -------------------------------------------------------
# Rota: /vitrine-visitantes — lista visitantes pendentes
# -------------------------------------------------------
@vitrine_visitantes.route('/vitrine-visitantes')
def lista():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    with Session(engine) as db:
        _auto_detectar_conversoes(db)
        visitantes = _buscar_visitantes_pendentes(db)

    return render_template('consiste/vitrine_visitantes.html',
        visitantes           = visitantes,
        acesso_criado_agora  = False,
        link_whatsapp        = None,
        erro                 = None,
        usuario_nome         = session.get('usuario_nome'),
        usuario_perfil       = session.get('usuario_perfil'),
        cor_primaria         = session.get('cor_primaria', '#D4370A'),
        nome_sistema         = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo           = 'vitrine_visitantes'
    )


# -------------------------------------------------------
# Rota: /vitrine-visitantes/converter/<id> — converte um
# visitante em cliente real (Produtor + Propriedade + vinculo
# + Usuario + UsuarioVinculo), com 1 clique, sem pedir dados
# de Propriedade antes (ver DESCRICAO no topo do arquivo).
#
# Protecao contra duplo clique: se o visitante ja tiver
# convertido_em preenchido, nao faz nada, so volta pra lista.
#
# Checagem defensiva de duplicidade (mesmo com a auto-deteccao
# ja rodando no GET da lista, pode haver corrida entre o
# carregamento da tela e o clique - ex.: duas abas abertas):
# se o CPF/CNPJ ja virou Produtor entre o load e o clique, NAO
# cria um segundo Produtor - so vincula o visitante ao ja
# existente e segue normalmente (sem erro, sem aviso extra -
# mesmo espirito da auto-deteccao, decisao de Benedito).
# -------------------------------------------------------
@vitrine_visitantes.route('/vitrine-visitantes/converter/<int:id>', methods=['POST'])
def converter(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    link_whatsapp = None
    erro_conversao = None
    acesso_criado_agora = False

    with Session(engine) as db:
        visitante = db.get(VitrineVisitante, id)
        if not visitante:
            return redirect(url_for('vitrine_visitantes.lista'))

        # Protecao contra duplo clique/recriacao.
        if visitante.convertido_em:
            return redirect(url_for('vitrine_visitantes.lista'))

        # Checagem defensiva de duplicidade (corrida entre load e
        # clique) - so vincula, nao cria de novo.
        produtor_existente = db.query(Produtor).filter_by(
            cpf_cnpj=visitante.cpf_cnpj
        ).first()

        if produtor_existente:
            visitante.convertido_em = datetime.now()
            visitante.id_produtor_criado = produtor_existente.id
            db.commit()
            return redirect(url_for('vitrine_visitantes.lista'))

        # --- Cria o Produtor, com placeholders nos campos
        # obrigatorios sem fonte de dado real (ver DESCRICAO). ---
        tipo_pessoa = 'FISICA' if len(visitante.cpf_cnpj) == 11 else 'JURIDICA'

        novo_produtor = Produtor(
            tipo_pessoa     = tipo_pessoa,
            razao_social    = visitante.nome,
            nome            = visitante.nome,
            visibilidade    = 'PRIVADO',
            cpf_cnpj        = visitante.cpf_cnpj,
            email           = visitante.email,
            telefone        = visitante.telefone,
            municipio       = 'A COMPLETAR',
            uf              = 'XX',
            ativo           = True
        )
        db.add(novo_produtor)
        db.flush()  # garante novo_produtor.id antes dos vinculos

        # --- Cria a Propriedade placeholder (cadastro_completo=
        # False - o Produtor completa sozinho no primeiro acesso,
        # mesmo padrao ja usado no Convite Publico). ---
        nova_propriedade = Propriedade(
            nome                = 'A COMPLETAR',
            tipo                = 'MISTA',
            roteiro_acesso      = 'A COMPLETAR',
            area_hectares       = 0,
            inscricao_estadual  = None,
            municipio           = 'A COMPLETAR',
            uf                  = 'XX',
            cadastro_completo   = False,
            email               = visitante.email,
            telefone            = visitante.telefone,
            ativo               = True
        )
        db.add(nova_propriedade)
        db.flush()  # garante nova_propriedade.id antes do vinculo

        novo_vinculo_propriedade = PropriedadeProdutor(
            id_propriedade = nova_propriedade.id,
            id_produtor    = novo_produtor.id,
            principal      = True,
            data_inicio    = date.today()
        )
        db.add(novo_vinculo_propriedade)

        # --- Cria o acesso (Usuario + UsuarioVinculo) - mesmo
        # padrao ja usado em produtores.py/criar_acesso()
        # (Cenario 1). ---
        senha_provisoria = gerar_senha_provisoria()

        novo_usuario = Usuario(
            id_produtor      = novo_produtor.id,
            login            = novo_produtor.cpf_cnpj,
            senha            = generate_password_hash(senha_provisoria),
            perfil           = 'PRODUTOR',
            nome             = novo_produtor.nome,
            email            = novo_produtor.email,
            senha_provisoria = False,
            login_provisorio = True
        )
        db.add(novo_usuario)
        db.flush()  # garante novo_usuario.id antes do vinculo

        novo_vinculo_acesso = UsuarioVinculo(
            id_usuario  = novo_usuario.id,
            id_produtor = novo_produtor.id,
            cargo       = 'TITULAR',
            data_inicio = date.today()
        )
        db.add(novo_vinculo_acesso)

        # --- Marca o visitante como convertido ---
        visitante.convertido_em = datetime.now()
        visitante.id_produtor_criado = novo_produtor.id

        db.commit()
        acesso_criado_agora = True

        # --- Envio de e-mail (obrigatorio) ---
        try:
            link_login = url_for('auth.login', _external=True)
            msg = Message(
                subject    = 'Orion SISBOV — Seu acesso foi criado',
                sender     = 'noreply.consisteti@gmail.com',
                recipients = [novo_produtor.email]
            )
            msg.body = (
                f'Ola, {novo_produtor.nome}!\n\n'
                f'Seu cadastro no Orion SISBOV foi criado com sucesso.\n\n'
                f'Login: {novo_produtor.cpf_cnpj}\n'
                f'Senha provisoria: {senha_provisoria}\n\n'
                f'Acesse o sistema com este login e senha: {link_login}\n'
                f'Voce sera redirecionado para criar um login e uma senha novos.\n\n'
                f'Atenciosamente,\n'
                f'Orion SISBOV — Consiste Informatica'
            )
            mail.send(msg)
        except Exception as e:
            erro_conversao = (
                'Cliente convertido, mas houve falha ao enviar o e-mail. '
                'Oriente o Produtor a usar "Esqueci minha senha" na tela de '
                'login, informando o CPF/CNPJ.'
            )
            print(f'ERRO Flask-Mail (Converter Visitante Vitrine): {e}')

        # --- Link de WhatsApp (opcional, envio manual - mesmo
        # padrao "envio final sempre manual" de prospects.py e de
        # produtores.py/criar_acesso()). SEM o CPF na mensagem
        # (mesma decisao do Cenario 1). ---
        if novo_produtor.telefone:
            mensagem_whatsapp = (
                f'Olá, {novo_produtor.nome}! 🎉 Seu acesso na plataforma Orion SISBOV foi criado.\n'
                f'Seu login é o seu CPF.\n'
                f'Sua senha provisória é: {senha_provisoria}\n'
                f'É só entrar que o sistema já vai pedir pra você criar um login e uma senha novos. '
                f'Qualquer dúvida, chama a gente!'
            )
            link_whatsapp = (
                f'https://wa.me/{DDI_BRASIL}{novo_produtor.telefone}'
                f'?text={urllib.parse.quote(mensagem_whatsapp)}'
            )

    # Re-renderiza a lista (ja atualizada, sem o visitante recem
    # convertido) com o banner de sucesso + link de WhatsApp -
    # esses dois dados so existem neste momento da requisicao.
    with Session(engine) as db:
        visitantes = _buscar_visitantes_pendentes(db)

    return render_template('consiste/vitrine_visitantes.html',
        visitantes           = visitantes,
        acesso_criado_agora  = acesso_criado_agora,
        link_whatsapp        = link_whatsapp,
        erro                 = erro_conversao,
        usuario_nome         = session.get('usuario_nome'),
        usuario_perfil       = session.get('usuario_perfil'),
        cor_primaria         = session.get('cor_primaria', '#D4370A'),
        nome_sistema         = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo           = 'vitrine_visitantes'
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\vitrine_visitantes.py
# =========================================================