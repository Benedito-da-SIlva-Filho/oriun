# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\produtor_usuarios.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-08-07 15:20 -03
# ATUALIZADO EM: 2026-11-16 11:45 -03
# VERSAO: 1.3.0
#
# DESCRICAO:
#     Rotas de "Meu Usuário" — gestão de usuários do PROPRIO
#     Produtor logado (equipe: quem tem acesso a esta Propriedade/
#     Produtor). Complementa backend/routers/usuarios.py (que e
#     exclusivo do perfil CONSISTE) - aqui e o Produtor gerindo a
#     propria equipe, dentro do proprio escopo (id_produtor da
#     sessao), nunca de outro Produtor.
#     - /produtor/usuarios              -> lista a equipe deste
#                                          Produtor (?mostrar=todos
#                                          inclui inativos - v1.1.0)
#     - /produtor/usuarios/novo         -> formulario novo
#     - /produtor/usuarios/editar/<id>  -> formulario edicao (NOVO,
#                                          v1.1.0)
#     - /produtor/usuarios/salvar       -> cria OU edita (Usuario +
#                                          UsuarioVinculo)
#     - /produtor/usuarios/toggle/<id>  -> Inativar/Ativar
#
#     PERMISSAO: alem do perfil PRODUTOR (checagem padrao ja usada
#     em todas as rotas /produtor/*), exige que o CARGO do vinculo
#     ativo do usuario logado (session['usuario_cargo']) seja
#     TITULAR ou ADMINISTRADOR - unicos cargos com permissao de
#     gerir a equipe (decisao de Benedito, Sessao 034,
#     continuacao). Demais cargos (ADMINISTRATIVO, CAMPEIRO, etc.)
#     sao redirecionados para a Home com mensagem.
#
#     ESCOPO SEMPRE FILTRADO por session['id_produtor'] - um
#     usuario desta tela NUNCA ve nem cria/edita usuarios de outro
#     Produtor.
#
#     v1.0.0: Criacao do modulo (Sessao 034, continuacao,
#         07/08/2026). Fecha a Frente B do lado Produtor - o lado
#         CONSISTE ja existia desde usuarios.py v1.8.0 (mesma
#         sessao).
#     v1.1.0: Sessao (26/08/2026, 10:43 -03) - Caso real: Catarina
#         (equipe do Claudenor) cadastrada sem e-mail, sem forma de
#         corrigir depois. Tres mudancas alinhadas com Benedito:
#
#         (1) E-mail passa a ser OBRIGATORIO em novo()/salvar() -
#             evita que o proximo cadastro nasca sem e-mail.
#
#         (2) Nova rota editar(id) + ramo de edicao em salvar():
#             permite corrigir Nome/E-mail/Cargo de um usuario ja
#             existente. O LOGIN NUNCA e alterado por aqui - decisao
#             explicita de Benedito (26/08/2026): so o proprio dono
#             da conta pode trocar o proprio login, e isso ja
#             acontece em /trocar-senha (usuarios.py). Um
#             Administrativo/Titular editando OUTRA pessoa nunca
#             mexe no login dela.
#
#         (3) Inativar/Ativar deixou de tocar Usuario.ativo (era
#             GLOBAL - afetaria login em QUALQUER Produtor que este
#             usuario atendesse) e passa a tocar UsuarioVinculo.
#             data_fim (Inativar = data_fim de hoje, Ativar = volta
#             a None) - decisao de Benedito: "o Ativo/Inativo tem
#             que estar no cadastro do Usuario... DATA FIM". Efeito
#             pratico: se a pessoa tiver outro vinculo ativo em
#             outro Produtor, o login dela continua funcionando la;
#             se este era o unico vinculo, ela some da equipe deste
#             Produtor mas o Usuario em si nao e apagado nem
#             bloqueado globalmente.
#
#             CASO FORA DE ESCOPO (decisao explicita de Benedito,
#             26/08/2026): se um colaborador sai de uma Propriedade/
#             Produtor e passa a trabalhar em OUTRO cliente Orion,
#             NAO se reaproveita o Usuario antigo - cadastra-se um
#             Usuario novo, do zero, na equipe do novo Produtor. Ou
#             seja, na pratica um Usuario tem sempre 1 unico vinculo
#             ao longo do tempo (o antigo so fica com data_fim
#             preenchida, sem nunca ganhar um vinculo novo com outro
#             Produtor).
#
#             lista() ganhou o parametro ?mostrar=todos: por padrao
#             mostra so vinculos ativos (uso do dia a dia); com o
#             parametro, mostra tambem os inativos (com o badge
#             correspondente e botao "Ativar"), para o caso do
#             colaborador que saiu e depois volta a mesma
#             Propriedade.
#     v1.2.0: Sessao 096 (14/10/2026) - EQUIPE DA PROPRIEDADE.
#         A equipe deixa de ser "do Produtor" e passa a ser da
#         PROPRIEDADE em uso (fazenda em uso da Home, ou a unica
#         propriedade do usuario). Combinado com Benedito:
#         (1) Colaborador cadastrado UMA vez recebe um vinculo para
#             CADA produtor ativo da propriedade (mesmo cargo, mesma
#             data de inicio). Inativar/Ativar/Editar mexem em todos.
#         (2) Login = numero do CELULAR (DDD + 9 digitos, so digitos).
#             Senha provisoria gerada (troca obrigatoria no 1o acesso);
#             a tela mostra login + senha e o botao "Enviar pelo
#             WhatsApp" (link wa.me, sem custo, envio manual).
#             Acabou a senha fixa 12345.
#         (3) E-mail opcional (serve para "Esqueci minha senha").
#         (4) Cargo TITULAR nao e criado aqui (nasce no Criar Acesso).
#             Titular e o proprio usuario logado aparecem na lista mas
#             nao sao editados/inativados por esta tela.
#         (5) Permissao: TITULAR ou ADMINISTRADOR em ao menos um
#             produtor da propriedade. Pode haver varios
#             ADMINISTRADORES ativos.
#         Rotas e menu iguais. Pendente (proximo passo): quando um
#         produtor novo entrar na propriedade, ligar a equipe dele
#         automaticamente (hoje so a tela cobre os produtores que ja
#         existem na hora do cadastro).
#     v1.3.0: Sessao 128 (2026-11-16 11:45 -03) - AUDITORIA ETAPA 8a: (a) quem tambem trabalha em OUTRA propriedade so tem o Cargo alterado aqui (Nome e e-mail ficam, pois a conta e unica); (b) Nome e e-mail validados no servidor (ate 100 caracteres; e-mail com formato). REVERSAO: .bak_antes_etapa8a.
# =========================================================

from datetime import date
import re
import urllib.parse
from types import SimpleNamespace
from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.database import engine
from backend.models import Usuario, UsuarioVinculo, Produtor, Propriedade, PropriedadeProdutor
from backend.models.usuario_vinculo import CARGOS_VALIDOS
from backend.routers.auth import buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.senha_helper import gerar_senha_provisoria

# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
produtor_usuarios = Blueprint('produtor_usuarios', __name__)

# -------------------------------------------------------
# Cargos com permissao de gerir a equipe (Sessao 034,
# continuacao). Demais cargos do ENUM (ADMINISTRATIVO,
# CAMPEIRO, GERENTE_CAPATAZ, VETERINARIO_ZOOTECNISTA, AUXILIAR)
# tem acesso de leitura/operacao ao sistema, mas nao gerem
# usuarios.
# -------------------------------------------------------
CARGOS_COM_PERMISSAO_GESTAO = ('TITULAR', 'ADMINISTRADOR')

# v1.2.0: o TITULAR nasce no "Criar Acesso" (tela Produtores), nunca
# aqui - o colaborador novo escolhe entre os demais cargos.
CARGOS_NOVO_COLABORADOR = tuple(c for c in CARGOS_VALIDOS if c != 'TITULAR')

DDI_BRASIL = '55'
EMAIL_VALIDO = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')   # v1.3.0


# -------------------------------------------------------
# v1.2.0 - Contexto da tela: PROPRIEDADE em uso + produtores dela.
# Devolve (contexto, None) ou (None, redirect).
#   - propriedade: a "fazenda em uso" (Home) ou, se o usuario so tem
#     uma propriedade, ela; com 2 ou mais e nenhuma em uso, volta
#     para a Home pedindo para escolher a fazenda.
#   - permissao: TITULAR ou ADMINISTRADOR em ao menos um produtor
#     da propriedade (mesmas "personas": o cargo vale para a equipe
#     toda da propriedade).
#   - ids_produtores: produtores ATIVOS ligados a propriedade
#     (propriedade_produtor.data_fim nulo) - o colaborador recebe
#     um vinculo para cada um deles.
# -------------------------------------------------------
def _contexto():
    if 'usuario_id' not in session:
        return None, redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'PRODUTOR':
        return None, redirect(url_for('auth.produtor_home'))

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if not pares:
        return None, redirect(url_for('auth.produtor_home'))

    em_uso = resolver_fazenda_em_uso(pares)
    if em_uso is not None:
        id_propriedade = int(em_uso.id_propriedade)
    else:
        ids = {int(p.id_propriedade) for p in pares}
        if len(ids) != 1:
            return None, redirect(url_for('auth.produtor_home', aviso='fazenda'))
        id_propriedade = ids.pop()

    pares_da_propriedade = [p for p in pares if int(p.id_propriedade) == id_propriedade]
    if not any(p.cargo in CARGOS_COM_PERMISSAO_GESTAO for p in pares_da_propriedade):
        return None, redirect(url_for('auth.produtor_home'))

    with Session(engine) as db:
        ids_produtores = set()
        vinculos_propriedade = db.query(PropriedadeProdutor).filter_by(
            id_propriedade = id_propriedade,
            data_fim       = None
        ).all()
        for vp in vinculos_propriedade:
            produtor = db.get(Produtor, vp.id_produtor)
            if produtor and produtor.ativo:
                ids_produtores.add(int(produtor.id))
        propriedade = db.get(Propriedade, id_propriedade)
        nome_propriedade = propriedade.nome if propriedade else ''

    if not ids_produtores:
        return None, redirect(url_for('auth.produtor_home'))

    return {
        'id_propriedade':   id_propriedade,
        'nome_propriedade': nome_propriedade,
        'ids_produtores':   sorted(ids_produtores),
    }, None


# -------------------------------------------------------
# Dados comuns a todas as telas deste modulo.
# -------------------------------------------------------
def _dados_tela(ctx, **extra):
    dados = dict(
        usuario_nome     = session.get('usuario_nome'),
        usuario_perfil   = session.get('usuario_perfil'),
        cor_primaria     = session.get('cor_primaria', '#D4370A'),
        nome_sistema     = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo       = 'usuario',
        nome_propriedade = ctx['nome_propriedade'],
    )
    dados.update(extra)
    return dados


# -------------------------------------------------------
# Celular -> so digitos, DDD + 9 digitos (11 no total, o 3o digito
# e 9). Aceita colar com +55. Devolve None se nao servir.
# -------------------------------------------------------
def _normalizar_celular(texto):
    digitos = re.sub(r'\D', '', texto or '')
    if len(digitos) in (12, 13) and digitos.startswith(DDI_BRASIL):
        digitos = digitos[2:]
    if len(digitos) != 11 or digitos[0] == '0' or digitos[2] != '9':
        return None
    return digitos


# -------------------------------------------------------
# Monta a equipe da propriedade: 1 linha por PESSOA (a pessoa tem
# um vinculo por produtor da propriedade). Ativo = ao menos um
# vinculo sem data_fim.
# -------------------------------------------------------
def _montar_equipe(ctx, mostrar_todos):
    equipe = []
    with Session(engine) as db:
        vinculos = db.query(UsuarioVinculo).filter(
            UsuarioVinculo.id_produtor.in_(ctx['ids_produtores'])
        ).all()

        por_usuario = {}
        for v in vinculos:
            por_usuario.setdefault(v.id_usuario, []).append(v)

        for id_usuario, vs in por_usuario.items():
            ativos = [v for v in vs if v.data_fim is None]
            ativo = bool(ativos)
            if not ativo and not mostrar_todos:
                continue
            usuario = db.get(Usuario, id_usuario)
            if not usuario:
                continue
            base = (ativos or vs)[0]
            e_titular = any(v.cargo == 'TITULAR' for v in vs)
            sou_eu = (id_usuario == session.get('usuario_id'))
            equipe.append({
                'usuario':   usuario,
                'vinculo':   base,
                'ativo':     ativo,
                'pode_agir': (not e_titular) and (not sou_eu),
            })

    equipe.sort(key=lambda item: item['usuario'].nome or '')
    return equipe


def _render_lista(ctx, mostrar_todos, acesso_novo=None):
    return render_template('produtor/usuario_lista.html',
        **_dados_tela(ctx,
            equipe        = _montar_equipe(ctx, mostrar_todos),
            mostrar_todos = mostrar_todos,
            acesso_novo   = acesso_novo
        )
    )


def _render_cadastro(ctx, erro=None, **extra):
    return render_template('produtor/usuario_cadastro.html',
        **_dados_tela(ctx,
            usuario_edit   = extra.get('usuario_edit'),
            vinculo_edit   = extra.get('vinculo_edit'),
            cargos_validos = CARGOS_NOVO_COLABORADOR,
            erro           = erro,
            nome_tentativa    = extra.get('nome_tentativa'),
            email_tentativa   = extra.get('email_tentativa'),
            cargo_tentativa   = extra.get('cargo_tentativa'),
            celular_tentativa = extra.get('celular_tentativa'),
        )
    )


# -------------------------------------------------------
# Rota: /produtor/usuarios — equipe da PROPRIEDADE em uso.
# ?mostrar=todos inclui inativos.
# -------------------------------------------------------
@produtor_usuarios.route('/produtor/usuarios')
def lista():
    ctx, bloqueio = _contexto()
    if bloqueio:
        return bloqueio
    return _render_lista(ctx, request.args.get('mostrar') == 'todos')


# -------------------------------------------------------
# Rota: /produtor/usuarios/novo — formulario novo colaborador
# -------------------------------------------------------
@produtor_usuarios.route('/produtor/usuarios/novo')
def novo():
    ctx, bloqueio = _contexto()
    if bloqueio:
        return bloqueio
    return _render_cadastro(ctx)


# -------------------------------------------------------
# Rota: /produtor/usuarios/editar/<id> — formulario edicao.
# So Nome/E-mail/Cargo. Titular e o proprio usuario logado nao
# sao editados por aqui.
# -------------------------------------------------------
@produtor_usuarios.route('/produtor/usuarios/editar/<int:id>')
def editar(id):
    ctx, bloqueio = _contexto()
    if bloqueio:
        return bloqueio

    if id == session.get('usuario_id'):
        return redirect(url_for('produtor_usuarios.lista'))

    with Session(engine) as db:
        vinculos = db.query(UsuarioVinculo).filter(
            UsuarioVinculo.id_usuario == id,
            UsuarioVinculo.id_produtor.in_(ctx['ids_produtores'])
        ).all()

        if not vinculos or any(v.cargo == 'TITULAR' for v in vinculos):
            return redirect(url_for('produtor_usuarios.lista'))

        usuario_edit = db.get(Usuario, id)
        vinculo_edit = (
            [v for v in vinculos if v.data_fim is None] or vinculos
        )[0]

    return _render_cadastro(ctx, usuario_edit=usuario_edit, vinculo_edit=vinculo_edit)


# -------------------------------------------------------
# Rota: /produtor/usuarios/salvar — cria OU edita.
#
# NOVO: login = celular; senha provisoria gerada (troca obrigatoria
# no 1o acesso); 1 vinculo por produtor da propriedade, mesmo cargo
# e mesma data de inicio. Ao terminar, mostra login + senha e o
# botao do WhatsApp (link wa.me, sem custo - envio manual).
# EDITAR: Nome, E-mail e Cargo (em todos os vinculos da pessoa na
# propriedade). Login nunca muda por aqui.
# -------------------------------------------------------
@produtor_usuarios.route('/produtor/usuarios/salvar', methods=['POST'])
def salvar():
    ctx, bloqueio = _contexto()
    if bloqueio:
        return bloqueio

    id     = request.form.get('id', '').strip()
    nome   = request.form.get('nome', '').strip()
    email  = request.form.get('email', '').strip().lower()
    cargo  = request.form.get('cargo', '').strip()
    celular_digitado = request.form.get('celular', '').strip()

    erro_validacao = None
    if not nome:
        erro_validacao = 'Sr. Usuário(a), o Nome Completo é obrigatório!'
    elif len(nome) > 100:
        erro_validacao = 'Sr. Usuário(a), o Nome Completo deve ter no máximo 100 caracteres.'
    elif cargo not in CARGOS_NOVO_COLABORADOR:
        erro_validacao = 'Sr. Usuário(a), selecione um Cargo válido.'
    elif email and (len(email) > 100 or not EMAIL_VALIDO.match(email)):
        erro_validacao = 'Sr. Usuário(a), o e-mail informado não parece válido. Confira e tente de novo.'

    # -----------------------------------------------------
    # Edicao
    # -----------------------------------------------------
    if id:
        try:
            id_usuario = int(id)
        except ValueError:
            return redirect(url_for('produtor_usuarios.lista'))

        with Session(engine) as db:
            vinculos = db.query(UsuarioVinculo).filter(
                UsuarioVinculo.id_usuario == id_usuario,
                UsuarioVinculo.id_produtor.in_(ctx['ids_produtores'])
            ).all()

            if (not vinculos
                    or any(v.cargo == 'TITULAR' for v in vinculos)
                    or id_usuario == session.get('usuario_id')):
                return redirect(url_for('produtor_usuarios.lista'))

            usuario = db.get(Usuario, id_usuario)
            if not usuario:
                return redirect(url_for('produtor_usuarios.lista'))

            if erro_validacao:
                return _render_cadastro(ctx, erro=erro_validacao,
                    usuario_edit = SimpleNamespace(id=usuario.id, nome=nome, email=email, login=usuario.login),
                    vinculo_edit = SimpleNamespace(cargo=cargo)
                )

            # v1.3.0: a conta e unica no sistema. Quem tambem trabalha em OUTRA propriedade
            # nao tem Nome/e-mail alterados por aqui (so o Cargo).
            outras = db.query(UsuarioVinculo).filter(
                UsuarioVinculo.id_usuario == id_usuario,
                UsuarioVinculo.data_fim.is_(None),
                ~UsuarioVinculo.id_produtor.in_(ctx['ids_produtores'])
            ).count()
            mudou_dados = (nome != (usuario.nome or '')
                           or (email or '').lower() != (usuario.email or '').lower())
            if outras and mudou_dados:
                return _render_cadastro(ctx,
                    erro='Sr. Usuário(a), esta pessoa também trabalha em outra propriedade. Nome e e-mail não podem ser alterados por aqui; altere só o Cargo.',
                    usuario_edit = SimpleNamespace(id=usuario.id, nome=usuario.nome, email=usuario.email, login=usuario.login),
                    vinculo_edit = SimpleNamespace(cargo=cargo)
                )

            if not outras:
                usuario.nome  = nome
                usuario.email = email or None
            for v in vinculos:
                v.cargo = cargo
            db.commit()

        return redirect(url_for('produtor_usuarios.lista'))

    # -----------------------------------------------------
    # Novo colaborador
    # -----------------------------------------------------
    def _volta_com_erro(mensagem):
        return _render_cadastro(ctx, erro=mensagem,
            nome_tentativa    = nome,
            email_tentativa   = email,
            cargo_tentativa   = cargo,
            celular_tentativa = celular_digitado
        )

    if erro_validacao:
        return _volta_com_erro(erro_validacao)

    celular = _normalizar_celular(celular_digitado)
    if not celular:
        return _volta_com_erro('Sr. Usuário(a), informe o celular com DDD e 9 dígitos. Exemplo: (34) 99999-9999.')

    senha_provisoria = gerar_senha_provisoria()

    try:
        with Session(engine) as db:
            if db.query(Usuario).filter_by(login=celular).first():
                return _volta_com_erro('Sr. Usuário(a), este celular já está cadastrado como login de outro acesso.')

            novo_usuario = Usuario(
                nome              = nome,
                login             = celular,
                email             = email or None,
                senha             = generate_password_hash(senha_provisoria),
                perfil            = 'PRODUTOR',
                id_certificadora  = None,
                ativo             = True,
                senha_provisoria  = False,   # False = obriga trocar a senha no 1o acesso
                login_provisorio  = False    # o login (celular) e definitivo
            )
            db.add(novo_usuario)
            db.flush()

            for id_produtor in ctx['ids_produtores']:
                db.add(UsuarioVinculo(
                    id_usuario  = novo_usuario.id,
                    id_produtor = id_produtor,
                    cargo       = cargo,
                    data_inicio = date.today(),
                    data_fim    = None
                ))

            db.commit()
    except IntegrityError:
        return _volta_com_erro('Sr. Usuário(a), este celular já está cadastrado como login de outro acesso.')

    primeiro_nome = nome.split()[0].title()
    link_login = url_for('auth.login', _external=True)
    mensagem = (
        f'Olá, {primeiro_nome}! 🎉 Seu acesso ao Orion SISBOV ({ctx["nome_propriedade"]}) foi criado.\n'
        f'Seu login é o seu número de celular: {celular}\n'
        f'Sua senha provisória é: {senha_provisoria}\n'
        f'Acesse: {link_login}\n'
        f'No primeiro acesso o sistema vai pedir para você criar uma senha nova.'
    )
    link_whatsapp = f'https://wa.me/{DDI_BRASIL}{celular}?text={urllib.parse.quote(mensagem)}'

    return _render_lista(ctx, False, acesso_novo={
        'nome':          nome,
        'login':         celular,
        'senha':         senha_provisoria,
        'link_whatsapp': link_whatsapp,
    })


# -------------------------------------------------------
# Rota: /produtor/usuarios/toggle/<id> — Inativar/Ativar.
# Mexe em TODOS os vinculos da pessoa dentro da propriedade
# (data_fim = hoje / volta a None). Titular e o proprio usuario
# logado nao sao tocados. Preserva o filtro ?mostrar=todos.
# -------------------------------------------------------
@produtor_usuarios.route('/produtor/usuarios/toggle/<int:id>', methods=['POST'])
def toggle(id):
    ctx, bloqueio = _contexto()
    if bloqueio:
        return bloqueio

    with Session(engine) as db:
        vinculos = db.query(UsuarioVinculo).filter(
            UsuarioVinculo.id_usuario == id,
            UsuarioVinculo.id_produtor.in_(ctx['ids_produtores'])
        ).all()

        pode = (vinculos
                and not any(v.cargo == 'TITULAR' for v in vinculos)
                and id != session.get('usuario_id'))

        if pode:
            ha_ativo = any(v.data_fim is None for v in vinculos)
            hoje = date.today()
            for v in vinculos:
                if ha_ativo:
                    if v.data_fim is None:
                        v.data_fim = hoje
                else:
                    v.data_fim = None
            db.commit()

    if request.args.get('mostrar') == 'todos':
        return redirect(url_for('produtor_usuarios.lista', mostrar='todos'))
    return redirect(url_for('produtor_usuarios.lista'))

# =========================================================
# FIM DE ARQUIVO: backend\routers\produtor_usuarios.py
# =========================================================
