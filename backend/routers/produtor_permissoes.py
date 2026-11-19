# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\produtor_permissoes.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-15 11:50 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.2.0
# v1.2.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Tela de PERMISSOES POR CARGO (Etapa 2 do pacote de permissoes), dentro
#     da Equipe da Propriedade. O Titular (e o Administrador, com limites)
#     ajusta o nivel de cada cargo em cada modulo da FAZENDA EM USO:
#     Sem acesso / Consulta / Lanca / Tudo. Sem ajuste, vale o padrao do
#     codigo (backend\utils\permissoes.py). Quem barra de verdade e o porteiro
#     (backend\routers\permissoes.py); esta tela so grava os ajustes em
#     public.permissao_cargo.
#
#     REGRAS (decididas com Benedito, Sessao 097):
#       - Quem entra: TITULAR ou ADMINISTRADOR (mesma regra da Equipe, _contexto).
#       - Titular nao aparece na tabela: e sempre Tudo.
#       - Administrador nao mexe na propria coluna; so o Titular mexe nela.
#       - Modulo Equipe: so o Titular decide, e so para o Administrador.
#       - O ajuste vale so para a fazenda (propriedade) em uso.
#       - Escolher o valor padrao apaga o ajuste (a tabela guarda so o que
#         foge do padrao).
#
#     Rotas:
#       GET  /produtor/usuarios/permissoes            - a tabela
#       POST /produtor/usuarios/permissoes/salvar     - grava as mudancas
#       POST /produtor/usuarios/permissoes/restaurar  - volta tudo ao padrao
#       GET  /produtor/usuarios/relatorio             - Relatorio de Colaboradores (tela)
#       GET  /produtor/usuarios/relatorio/pdf         - o mesmo relatorio em PDF
#
# HISTORICO DE VERSOES:
#     v1.0.0: Sessao 097 (15/10/2026, 11:50 -03) - Criacao.
#     v1.1.0: Sessao 097 (15/10/2026, 12:15 -03) - RELATORIO DE COLABORADORES
#         (pedido do Benedito no teste da Etapa 2): por pessoa da equipe da
#         fazenda em uso mostra cadastro (nome, login/celular, e-mail), cargo,
#         situacao, inicio/fim do vinculo, ultimo acesso e as permissoes por
#         modulo agrupadas por nivel (* = ajuste fora do padrao). Decisoes:
#         so Titular e Administrador; tela + PDF; CPF NAO aparece (login so
#         aparece como celular valido ou texto; login so de digitos do Titular
#         e oculto, pode ser CPF/CNPJ). Tela de Permissoes: o aviso do
#         navegador no Restaurar padrao virou a janela padrao do Orion.
# =========================================================

from datetime import datetime
from io import BytesIO

from flask import Blueprint, render_template, request, redirect, url_for, session, send_file
from sqlalchemy import text
from sqlalchemy.orm import Session
from xhtml2pdf import pisa

from backend.database import engine
from backend.routers.auth import buscar_pares_propriedade_produtor
from backend.models import Usuario, UsuarioVinculo
from backend.routers.produtor_usuarios import _contexto, _dados_tela, _normalizar_celular
from backend.utils.pdf_helper import link_callback_pdf
from backend.utils.permissoes import (
    NIVEIS, NOMES_NIVEL, NOMES_NIVEL_TELA, NOMES_CARGO, MODULOS, MODULOS_DA_TELA,
    CARGOS_DA_TELA, NIVEIS_DO_MODULO, DESCRICAO_MODULO,
    nivel_efetivo, nivel_padrao, nivel_para_tela, pode_editar_celula,
    TUDO, LANCA, CONSULTA, SEM_ACESSO,
)

produtor_permissoes = Blueprint('produtor_permissoes', __name__)


# -------------------------------------------------------
# Papel de quem esta na tela, na propriedade em uso: TITULAR se for titular
# em algum produtor dela, senao ADMINISTRADOR (o _contexto ja garante um dos dois).
# -------------------------------------------------------
def _papel(ctx):
    cargos = {
        p.cargo for p in buscar_pares_propriedade_produtor(session['usuario_id'])
        if int(p.id_propriedade) == ctx['id_propriedade']
    }
    if 'TITULAR' in cargos:
        return 'TITULAR'
    if 'ADMINISTRADOR' in cargos:
        return 'ADMINISTRADOR'
    return None


# -------------------------------------------------------
# Ajustes gravados da propriedade: ({(cargo, modulo): nivel}, tabela_ok)
# -------------------------------------------------------
def _carregar_ajustes(id_propriedade):
    ajustes = {}
    try:
        with Session(engine) as db:
            linhas = db.execute(
                text("SELECT cargo, modulo, nivel FROM public.permissao_cargo "
                     "WHERE id_propriedade = :p"),
                {'p': id_propriedade}
            ).fetchall()
        for cargo, modulo, nivel in linhas:
            if nivel in NIVEIS:
                ajustes[(cargo, modulo)] = NIVEIS[nivel]
        return ajustes, True
    except Exception:
        return {}, False


def _ultima_alteracao(id_propriedade):
    try:
        with Session(engine) as db:
            linha = db.execute(
                text("SELECT u.nome, p.atualizado_em FROM public.permissao_cargo p "
                     "LEFT JOIN public.usuarios u ON u.id = p.atualizado_por "
                     "WHERE p.id_propriedade = :p ORDER BY p.atualizado_em DESC LIMIT 1"),
                {'p': id_propriedade}
            ).first()
        if linha:
            return {'nome': linha[0] or '', 'quando': linha[1]}
    except Exception:
        pass
    return None


# -------------------------------------------------------
# GET /produtor/usuarios/permissoes - a tabela
# -------------------------------------------------------
@produtor_permissoes.route('/produtor/usuarios/permissoes')
def tela():
    ctx, bloqueio = _contexto()
    if bloqueio:
        return bloqueio

    papel = _papel(ctx)
    ajustes, tabela_ok = _carregar_ajustes(ctx['id_propriedade'])

    linhas = []
    for modulo in MODULOS_DA_TELA:
        celulas = []
        for cargo in CARGOS_DA_TELA:
            efetivo = nivel_para_tela(modulo, nivel_efetivo(cargo, modulo, ajustes))
            padrao = nivel_para_tela(modulo, nivel_padrao(cargo, modulo))
            celulas.append({
                'cargo':    cargo,
                'campo':    f'n__{cargo}__{modulo}',
                'codigo':   NOMES_NIVEL[efetivo],
                'nome':     NOMES_NIVEL_TELA[efetivo],
                'editavel': pode_editar_celula(papel, cargo, modulo),
                'ajustado': efetivo != padrao,
                'opcoes':   [(NOMES_NIVEL[o], NOMES_NIVEL_TELA[o]) for o in NIVEIS_DO_MODULO[modulo]],
            })
        linhas.append({
            'modulo':    modulo,
            'nome':      MODULOS[modulo],
            'descricao': DESCRICAO_MODULO.get(modulo, ''),
            'celulas':   celulas,
        })

    return render_template('produtor/produtor_permissoes.html',
        **_dados_tela(ctx,
            linhas     = linhas,
            cargos     = [(c, NOMES_CARGO[c]) for c in CARGOS_DA_TELA],
            papel      = papel,
            tabela_ok  = tabela_ok,
            ultima     = _ultima_alteracao(ctx['id_propriedade']) if tabela_ok else None,
            ok         = request.args.get('ok'),
            erro       = request.args.get('erro'),
            ha_ajustes = any(c['ajustado'] for l in linhas for c in l['celulas']),
        )
    )


# -------------------------------------------------------
# POST /produtor/usuarios/permissoes/salvar
# -------------------------------------------------------
@produtor_permissoes.route('/produtor/usuarios/permissoes/salvar', methods=['POST'])
def salvar():
    ctx, bloqueio = _contexto()
    if bloqueio:
        return bloqueio

    papel = _papel(ctx)
    id_propriedade = ctx['id_propriedade']
    ajustes, tabela_ok = _carregar_ajustes(id_propriedade)
    if not tabela_ok:
        return redirect(url_for('produtor_permissoes.tela', erro='tabela'))

    mudancas = 0
    try:
        with Session(engine) as db:
            for cargo in CARGOS_DA_TELA:
                for modulo in MODULOS_DA_TELA:
                    valor = request.form.get(f'n__{cargo}__{modulo}')
                    if valor is None or valor not in NIVEIS:
                        continue
                    if not pode_editar_celula(papel, cargo, modulo):
                        continue
                    nivel = NIVEIS[valor]
                    if nivel not in NIVEIS_DO_MODULO[modulo]:
                        continue

                    atual = nivel_para_tela(modulo, nivel_efetivo(cargo, modulo, ajustes))
                    if nivel == atual:
                        continue

                    padrao = nivel_para_tela(modulo, nivel_padrao(cargo, modulo))
                    params = {'p': id_propriedade, 'c': cargo, 'm': modulo}
                    if nivel == padrao:
                        db.execute(text(
                            "DELETE FROM public.permissao_cargo "
                            "WHERE id_propriedade = :p AND cargo = :c AND modulo = :m"), params)
                    else:
                        params.update({'n': NOMES_NIVEL[nivel], 'u': session['usuario_id']})
                        db.execute(text(
                            "INSERT INTO public.permissao_cargo "
                            "(id_propriedade, cargo, modulo, nivel, atualizado_em, atualizado_por) "
                            "VALUES (:p, :c, :m, :n, NOW(), :u) "
                            "ON CONFLICT (id_propriedade, cargo, modulo) DO UPDATE SET "
                            "nivel = EXCLUDED.nivel, atualizado_em = NOW(), "
                            "atualizado_por = EXCLUDED.atualizado_por"), params)
                    mudancas += 1
            db.commit()
    except Exception as e:
        print(f'PERMISSOES: erro ao gravar ajustes: {e}')
        return redirect(url_for('produtor_permissoes.tela', erro='gravar'))

    return redirect(url_for('produtor_permissoes.tela', ok=mudancas))


# -------------------------------------------------------
# POST /produtor/usuarios/permissoes/restaurar - apaga os ajustes que
# este papel pode mexer (Titular: todos; Administrador: sem a propria
# coluna e sem a linha Equipe). Volta ao padrao do codigo.
# -------------------------------------------------------
@produtor_permissoes.route('/produtor/usuarios/permissoes/restaurar', methods=['POST'])
def restaurar():
    ctx, bloqueio = _contexto()
    if bloqueio:
        return bloqueio

    papel = _papel(ctx)
    id_propriedade = ctx['id_propriedade']
    ajustes, tabela_ok = _carregar_ajustes(id_propriedade)
    if not tabela_ok:
        return redirect(url_for('produtor_permissoes.tela', erro='tabela'))

    apagados = 0
    try:
        with Session(engine) as db:
            for (cargo, modulo) in list(ajustes.keys()):
                if not pode_editar_celula(papel, cargo, modulo):
                    continue
                db.execute(text(
                    "DELETE FROM public.permissao_cargo "
                    "WHERE id_propriedade = :p AND cargo = :c AND modulo = :m"),
                    {'p': id_propriedade, 'c': cargo, 'm': modulo})
                apagados += 1
            db.commit()
    except Exception as e:
        print(f'PERMISSOES: erro ao restaurar ajustes: {e}')
        return redirect(url_for('produtor_permissoes.tela', erro='gravar'))

    return redirect(url_for('produtor_permissoes.tela', ok=apagados))

# -------------------------------------------------------
# v1.1.0 - RELATORIO DE COLABORADORES
# -------------------------------------------------------
CLASSE_NIVEL = {TUDO: 'n-tudo', LANCA: 'n-lanca', CONSULTA: 'n-consulta', SEM_ACESSO: 'n-sem'}


def _formatar_login(usuario, e_titular):
    """Login para exibir. Celular valido vira (DD) 9XXXX-XXXX; texto comum
    aparece como esta; login so de digitos que nao e celular, ou de Titular,
    fica oculto (pode ser CPF/CNPJ - decisao: CPF nao aparece)."""
    login = (usuario.login or '').strip()
    if not login:
        return '-'
    if login.isdecimal():
        if e_titular:
            return '-'
        cel = _normalizar_celular(login)
        if cel:
            return f'({cel[:2]}) {cel[2:7]}-{cel[7:]}'
        return '-'
    return login


def _data(d):
    return d.strftime('%d/%m/%Y') if d else '-'


def _montar_relatorio(ctx, so_ativos):
    """1 item por PESSOA da equipe da propriedade em uso (ela tem um vinculo
    por produtor da propriedade). Permissoes = nivel efetivo do cargo em cada
    modulo (ajuste da fazenda ou padrao), agrupado por nivel."""
    ajustes, _ok = _carregar_ajustes(ctx['id_propriedade'])
    pessoas = []
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
            if so_ativos and not ativo:
                continue
            usuario = db.get(Usuario, id_usuario)
            if not usuario:
                continue
            e_titular = any(v.cargo == 'TITULAR' for v in vs)
            cargo = 'TITULAR' if e_titular else (ativos or vs)[0].cargo
            inicios = [v.data_inicio for v in vs if v.data_inicio]
            fins = [v.data_fim for v in vs if v.data_fim]

            grupos = []
            tem_ajuste = False
            if ativo:
                por_nivel = {}
                for modulo in MODULOS_DA_TELA:
                    efetivo = nivel_para_tela(modulo, nivel_efetivo(cargo, modulo, ajustes))
                    padrao = nivel_para_tela(modulo, nivel_padrao(cargo, modulo))
                    marca = efetivo != padrao
                    tem_ajuste = tem_ajuste or marca
                    por_nivel.setdefault(efetivo, []).append(MODULOS[modulo] + ('*' if marca else ''))
                for nivel in (TUDO, LANCA, CONSULTA, SEM_ACESSO):
                    if nivel in por_nivel:
                        grupos.append({
                            'nome':    NOMES_NIVEL_TELA[nivel],
                            'classe':  CLASSE_NIVEL[nivel],
                            'modulos': por_nivel[nivel],
                        })

            pessoas.append({
                'nome':          usuario.nome or '-',
                'login':         _formatar_login(usuario, e_titular),
                'email':         usuario.email or '-',
                'cargo_codigo':  cargo,
                'cargo':         NOMES_CARGO.get(cargo, (cargo or '-').replace('_', ' ').title()),
                'ativo':         ativo,
                'inicio':        _data(min(inicios)) if inicios else '-',
                'fim':           '-' if ativo else _data(max(fins) if fins else None),
                'ultimo_acesso': usuario.ultimo_acesso.strftime('%d/%m/%Y %H:%M') if usuario.ultimo_acesso else 'Nunca acessou',
                'grupos':        grupos,
                'tem_ajuste':    tem_ajuste,
            })

    pessoas.sort(key=lambda x: (not x['ativo'], x['cargo_codigo'] != 'TITULAR', x['nome']))
    return pessoas


def _resumo_relatorio(pessoas):
    ativos = sum(1 for x in pessoas if x['ativo'])
    return {'total': len(pessoas), 'ativos': ativos, 'encerrados': len(pessoas) - ativos,
            'ha_ajuste': any(x['tem_ajuste'] for x in pessoas)}


# -------------------------------------------------------
# GET /produtor/usuarios/relatorio - tela. ?mostrar=ativos esconde os encerrados.
# -------------------------------------------------------
@produtor_permissoes.route('/produtor/usuarios/relatorio')
def relatorio():
    ctx, bloqueio = _contexto()
    if bloqueio:
        return bloqueio

    so_ativos = request.args.get('mostrar') == 'ativos'
    pessoas = _montar_relatorio(ctx, so_ativos)
    return render_template('produtor/produtor_colaboradores_relatorio.html',
        **_dados_tela(ctx,
            pessoas        = pessoas,
            resumo         = _resumo_relatorio(pessoas),
            so_ativos      = so_ativos,
            data_impressao = datetime.now().strftime('%d/%m/%Y %H:%M'),
        )
    )


# -------------------------------------------------------
# GET /produtor/usuarios/relatorio/pdf - o mesmo relatorio em PDF (xhtml2pdf)
# -------------------------------------------------------
@produtor_permissoes.route('/produtor/usuarios/relatorio/pdf')
def relatorio_pdf():
    ctx, bloqueio = _contexto()
    if bloqueio:
        return bloqueio

    so_ativos = request.args.get('mostrar') == 'ativos'
    pessoas = _montar_relatorio(ctx, so_ativos)
    html = render_template('produtor/produtor_colaboradores_relatorio_pdf.html',
        nome_propriedade = ctx['nome_propriedade'],
        pessoas          = pessoas,
        resumo           = _resumo_relatorio(pessoas),
        so_ativos        = so_ativos,
        gerado_por       = session.get('usuario_nome') or '',
        data_impressao   = datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
    )
    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer, link_callback=link_callback_pdf)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                     download_name='colaboradores_permissoes.pdf')


# =========================================================
# FIM DE ARQUIVO: backend\routers\produtor_permissoes.py
# =========================================================
