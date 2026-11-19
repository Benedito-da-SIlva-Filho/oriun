# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\protocolos.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-03 16:40 -03
# ATUALIZADO EM: 2026-07-03 17:36 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Rotas de administracao do catalogo de Protocolos de
#     Certificacao (ABPO, PEFB, CSCB, Cota Hilton, e quaisquer
#     futuros). Tela de administracao - nao e um cadastro de
#     fazenda (isso e Propriedade/Produtor), e sim uma entidade
#     de sistema, por isso vive em ADMINISTRACAO no menu, ao
#     lado de Certificadoras.
#     Acesso: CONSISTE e CERTIFICADORA. Hoje so CONSISTE tem
#     portal proprio (link no consiste_menu.html) - a checagem
#     de perfil ja inclui CERTIFICADORA para quando o portal
#     dela existir, sem precisar mexer nesta rota depois.
#
#     - /protocolos              -> lista todos, com busca por nome/codigo
#     - /protocolos/novo         -> formulario novo
#     - /protocolos/salvar       -> salva novo ou edicao
#     - /protocolos/editar/<id>  -> formulario edicao
#     - /protocolos/toggle/<id>  -> ativa ou inativa
#
#     Todos os campos de texto (codigo, nome, resumo, descricao)
#     seguem a regra padrao do projeto: UPPERCASE, sem excecao
#     (decisao explicita da Sessao 011 - a descricao e editavel,
#     entao segue a mesma regra dos demais campos editaveis).
#
#     v1.0.0: Criacao do modulo (Sessao 011).
#     v1.1.0: Sessao 011 - Correcao de acentuacao nas mensagens
#             de erro exibidas ao usuario.
# =========================================================

from types import SimpleNamespace
from flask import Blueprint, render_template, request, redirect, url_for, session
from backend.database import engine
from backend.models import Protocolo
from sqlalchemy.orm import Session

# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
protocolos = Blueprint('protocolos', __name__)

# -------------------------------------------------------
# Perfis com acesso a esta tela
# -------------------------------------------------------
PERFIS_PERMITIDOS = ['CONSISTE', 'CERTIFICADORA']

# -------------------------------------------------------
# Tipos de vinculo disponiveis (valor gravado, rotulo exibido)
# Valor gravado bate com o CHECK constraint da tabela protocolos
# -------------------------------------------------------
TIPOS_VINCULO = [
    ('propriedade', 'Propriedade'),
    ('planta_industrial', 'Planta Industrial'),
]


# -------------------------------------------------------
# Rota: /protocolos — lista todos, com busca por nome/codigo
# -------------------------------------------------------
@protocolos.route('/protocolos')
def lista():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') not in PERFIS_PERMITIDOS:
        return redirect(url_for('auth.consiste_home'))

    termo_busca = request.args.get('busca', '').strip()

    with Session(engine) as db:
        query = db.query(Protocolo)
        if termo_busca:
            query = query.filter(
                (Protocolo.nome.ilike(f'%{termo_busca}%')) |
                (Protocolo.codigo.ilike(f'%{termo_busca}%'))
            )
        lista_protocolos = query.order_by(Protocolo.nome).all()

    return render_template('consiste/protocolo_lista.html',
        protocolos     = lista_protocolos,
        termo_busca    = termo_busca,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'protocolos'
    )

# -------------------------------------------------------
# Rota: /protocolos/novo — formulario novo
# -------------------------------------------------------
@protocolos.route('/protocolos/novo')
def novo():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') not in PERFIS_PERMITIDOS:
        return redirect(url_for('auth.consiste_home'))

    return render_template('consiste/protocolo_cadastro.html',
        protocolo       = None,
        tipos_vinculo    = TIPOS_VINCULO,
        erro             = None,
        usuario_nome     = session.get('usuario_nome'),
        usuario_perfil   = session.get('usuario_perfil'),
        cor_primaria     = session.get('cor_primaria', '#D4370A'),
        nome_sistema     = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo       = 'protocolos'
    )

# -------------------------------------------------------
# Rota: /protocolos/editar/<id> — formulario edicao
# -------------------------------------------------------
@protocolos.route('/protocolos/editar/<int:id>')
def editar(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') not in PERFIS_PERMITIDOS:
        return redirect(url_for('auth.consiste_home'))

    with Session(engine) as db:
        protocolo = db.get(Protocolo, id)

    return render_template('consiste/protocolo_cadastro.html',
        protocolo       = protocolo,
        tipos_vinculo    = TIPOS_VINCULO,
        erro             = None,
        usuario_nome     = session.get('usuario_nome'),
        usuario_perfil   = session.get('usuario_perfil'),
        cor_primaria     = session.get('cor_primaria', '#D4370A'),
        nome_sistema     = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo       = 'protocolos'
    )

# -------------------------------------------------------
# Rota: /protocolos/salvar — salva novo ou edicao
# codigo, nome, resumo, descricao: UPPERCASE (regra padrao
# do projeto - decisao explicita da Sessao 011, pois estes
# campos sao editaveis, nao texto fixo).
# -------------------------------------------------------
@protocolos.route('/protocolos/salvar', methods=['POST'])
def salvar():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    id            = request.form.get('id')
    codigo        = request.form.get('codigo', '').strip().upper()
    nome          = request.form.get('nome', '').strip().upper()
    resumo        = request.form.get('resumo', '').strip().upper()
    descricao     = request.form.get('descricao', '').strip().upper()
    tipo_vinculo  = request.form.get('tipo_vinculo')

    # -----------------------------------------------------
    # Validacao de tamanho maximo (servidor = fonte da verdade),
    # batendo com o limite real da coluna no banco - mesmo
    # raciocinio ja usado em Propriedade (erro real do OESA).
    # -----------------------------------------------------
    erro_validacao = None

    LIMITES_TAMANHO = {
        'Código': (codigo, 20),
        'Nome':   (nome, 150),
        'Resumo': (resumo, 200),
    }

    for nome_campo, (valor, limite) in LIMITES_TAMANHO.items():
        if valor and len(valor) > limite:
            erro_validacao = f'Campo "{nome_campo}" excede o limite de {limite} caracteres (digitado: {len(valor)}).'
            break

    if not erro_validacao and tipo_vinculo not in ('propriedade', 'planta_industrial'):
        erro_validacao = 'Tipo de Vínculo inválido. Selecione Propriedade ou Planta Industrial.'

    if erro_validacao:
        protocolo_tentativa = SimpleNamespace(
            id           = id,
            codigo       = codigo,
            nome         = nome,
            resumo       = resumo,
            descricao    = descricao,
            tipo_vinculo = tipo_vinculo
        )
        return render_template('consiste/protocolo_cadastro.html',
            protocolo       = protocolo_tentativa,
            tipos_vinculo    = TIPOS_VINCULO,
            erro             = erro_validacao,
            usuario_nome     = session.get('usuario_nome'),
            usuario_perfil   = session.get('usuario_perfil'),
            cor_primaria     = session.get('cor_primaria', '#D4370A'),
            nome_sistema     = session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo       = 'protocolos'
        )

    with Session(engine) as db:
        if id:
            # Edicao
            p = db.get(Protocolo, int(id))
            p.codigo       = codigo
            p.nome         = nome
            p.resumo       = resumo
            p.descricao    = descricao
            p.tipo_vinculo = tipo_vinculo
        else:
            # Novo — ativo nasce True por padrao
            p = Protocolo(
                codigo       = codigo,
                nome         = nome,
                resumo       = resumo,
                descricao    = descricao,
                tipo_vinculo = tipo_vinculo,
                ativo        = True
            )
            db.add(p)

        db.commit()

    return redirect(url_for('protocolos.lista'))

# -------------------------------------------------------
# Rota: /protocolos/toggle/<id> — ativa ou inativa
# Inativar aqui NAO apaga o catalogo nem os vinculos
# historicos ja existentes em propriedade_protocolo -
# so impede que o protocolo apareca como opcao nova na
# tela de Propriedade (filtro Protocolo.ativo == True).
# -------------------------------------------------------
@protocolos.route('/protocolos/toggle/<int:id>', methods=['POST'])
def toggle(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') not in PERFIS_PERMITIDOS:
        return redirect(url_for('auth.consiste_home'))

    with Session(engine) as db:
        p = db.get(Protocolo, id)
        p.ativo = not p.ativo
        db.commit()

    return redirect(url_for('protocolos.lista'))

# =========================================================
# FIM DE ARQUIVO: backend\routers\protocolos.py
# =========================================================