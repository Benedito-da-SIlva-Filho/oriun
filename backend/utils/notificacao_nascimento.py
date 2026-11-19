# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\notificacao_nascimento.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-02 09:00 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.1.0
# v1.1.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Modulo "Notificacao de Nascimentos" - IMPRESSAO e REIMPRESSAO da
#     Notificacao de Nascimento (NAS) a Certificadora, em PDF
#     (backend/utils/pdf_notificacao_nascimento.py). Navegacao real
#     (Regra de Ouro #7): Hub de Entrada -> card "Nascimento /
#     Desmame" -> sub-hub -> card "Notificacao de Nascimentos"
#     (hubs.py v1.37.0) -> Selecionar Propriedade (so com 2+ pares)
#     -> LISTA.
#
#     UMA LISTA so (impressao e reimpressao juntas): todas as
#     Notificacoes NAS da Propriedade, da mais nova para a mais
#     antiga. Cada linha mostra o status:
#       - NAO IMPRESSA: botao "Imprimir" (primeira vez - grava em
#         tb_7020_notificacao_impressao, o que TRAVA o Desfazer) e o
#         PRAZO de 30 dias da Data de Brincagem (alerta: vencido /
#         ate 5 dias). So imprime se TODOS os brincos ja foram
#         conferidos no brete (tb_2001.conferido_brete); senao o
#         botao fica bloqueado mostrando quantos faltam.
#       - JA IMPRESSA: botao "Reimprimir" - quantas vezes precisar,
#         NUNCA grava nada, o PDF sai com a marca "REIMPRESSAO" e a
#         data da impressao original.
#     Ordem da primeira impressao (licao da Sessao 079): monta o
#     contexto e o PDF PRIMEIRO; so depois grava o status - se o PDF
#     falhar, nada muda.
#
#     DESTINATARIO: Certificadora vinculada a Propriedade
#     (propriedades.id_certificadora). O modelo nao leva marca de
#     Certificadora (a QIMA deixou de ser cliente).
#
#     SEGURANCA: toda rota confere se a Propriedade da URL pertence
#     aos pares do usuario logado (_propriedade_permitida).
#
#     v1.0.0: Criacao do modulo (Sessao 084, 02/10/2026, 09:00 -03).
#     v1.0.1: Sessao 084 (02/10/2026, 10:00 -03) - Propriedade SEM
#             Certificadora (caso de hoje): o PDF recebe certificadora
#             vazia e sai com linhas em branco para preencher a mao
#             (antes saia o texto "nao vinculada"). Nenhuma outra
#             mudanca.
# =========================================================

from datetime import date, datetime, timedelta

from flask import Blueprint, redirect, render_template, request, send_file, session
from sqlalchemy.exc import IntegrityError

from backend.models import Produtor, Propriedade
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4005_racas import Raca
from backend.models.tb_7020_notificacao_impressao import NotificacaoImpressao
from backend.routers.auth import buscar_pares_propriedade_produtor, redirecionar_home
from backend.utils.multitenant import get_db_produtor
from backend.utils.pdf_notificacao_nascimento import gerar_pdf_notificacao_nascimento

try:  # modelo da Certificadora (nome do atributo conferido em tempo de execucao)
    from backend.models.certificadora import Certificadora
except Exception:  # pragma: no cover
    Certificadora = None


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
notificacao_nascimento = Blueprint('notificacao_nascimento', __name__)


@notificacao_nascimento.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


TIPO_MOVIMENTO_NAS = 'NASCTO-DESMAME'
SERIE_NAS = 'NAS'
PRAZO_ENVIO_DIAS = 30        # prazo de envio da Notificacao (a partir da Data de Brincagem)
DIAS_ALERTA_PRAZO = 5        # "urgente" quando restam ate N dias

URL_INICIAR = '/produtor/notificacao-nascimento/iniciar'
URL_LISTAR = '/produtor/notificacao-nascimento/listar'
VOLTAR_SUBHUB = '/produtor/hub/entrada-nascimento'
TITULO = 'Notificação de Nascimentos'

MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho',
         'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']

ERROS = {
    'pendente': 'Esta Notificação ainda tem brincos a conferir no brete. Confira todos antes de imprimir.',
    'inexistente': 'Notificação não encontrada.',
}


# -------------------------------------------------------
# Auxiliares
# -------------------------------------------------------
def _propriedade_permitida(id_propriedade):
    if not str(id_propriedade).isdecimal():
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    return int(id_propriedade) in {int(par.id_propriedade) for par in pares}


def _data_br(data):
    return data.strftime('%d/%m/%Y') if data else ''


def _data_extenso(data):
    return f'{data.day} de {MESES[data.month - 1]} de {data.year}'


def _texto_sexo(sexo):
    return {'MACHO': 'Macho', 'FEMEA': 'Fêmea'}.get(sexo, sexo or '')


def _query_nas(db, id_propriedade):
    return db.query(Gta).filter(
        Gta.id_propriedade == int(id_propriedade),
        Gta.tipo_movimento == TIPO_MOVIMENTO_NAS,
        Gta.serie_gta == SERIE_NAS,
    )


def _nome_certificadora(db, propriedade):
    id_cert = getattr(propriedade, 'id_certificadora', None)
    if not id_cert or Certificadora is None:
        return None
    try:
        cert = db.get(Certificadora, id_cert)
    except Exception:
        return None
    for atributo in ('nome', 'razao_social', 'nome_fantasia'):
        valor = getattr(cert, atributo, None)
        if valor:
            return valor
    return None


def _url_voltar(pares):
    return URL_INICIAR if len(pares) > 1 else VOLTAR_SUBHUB


def _montar_contexto(db, gta, animais, id_propriedade, impressao):
    """Dict so com TEXTO/numeros (nada de objeto do banco) - o PDF e
    montado antes de qualquer commit."""
    propriedade = db.get(Propriedade, int(id_propriedade))
    produtor = db.get(Produtor, session['id_produtor'])
    racas = {r.id: r.nome for r in db.query(Raca).all()}

    data_doc = impressao.data_impressao if impressao else date.today()
    municipio_uf = f'{propriedade.municipio} / {propriedade.uf}' if propriedade else ''

    machos = sum(1 for a in animais if a.sexo == 'MACHO')
    femeas = sum(1 for a in animais if a.sexo == 'FEMEA')

    return {
        'numero': gta.numero_gta_completo,
        'reimpressao': impressao is not None,
        'data_documento': _data_br(data_doc),
        'local_data': f'{municipio_uf}, {_data_extenso(data_doc)}',
        'produtor': produtor.nome if produtor else None,
        'cpf_cnpj': produtor.cpf_cnpj if produtor else None,
        'propriedade': propriedade.nome if propriedade else None,
        'inscricao_estadual': getattr(propriedade, 'inscricao_estadual', None),
        'codigo_eras': propriedade.codigo_eras if propriedade else None,
        'municipio_uf': municipio_uf,
        'certificadora': _nome_certificadora(db, propriedade),   # None = sem Certificadora (linha em branco no PDF)
        'data_identificacao': _data_br(gta.data_emissao),
        'prazo_limite': _data_br(gta.data_emissao + timedelta(days=PRAZO_ENVIO_DIAS)) if gta.data_emissao else '',
        'qtde': len(animais),
        'machos': machos,
        'femeas': femeas,
        'gerado_em': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'animais': [{
            'sisbov': a.sisbov,
            'manejo': a.manejo,
            'sexo': _texto_sexo(a.sexo),
            'raca': racas.get(a.id_raca, ''),
            'nascimento': _data_br(a.nascimento),
            'dias': a.eras_dias,
        } for a in animais],
    }


# -------------------------------------------------------
# Rota: GET /produtor/notificacao-nascimento/iniciar
# Padrao Reutilizavel N.1 - Selecionar Propriedade/Produtor.
# -------------------------------------------------------
@notificacao_nascimento.route('/produtor/notificacao-nascimento/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor'] = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_LISTAR}?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None if pares else 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
        titulo=f'{TITULO} — Selecionar Propriedade',
        proximo=URL_LISTAR,
        campo_propriedade='id_propriedade',
        voltar=VOLTAR_SUBHUB,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/notificacao-nascimento/listar?id_propriedade=X
# -------------------------------------------------------
@notificacao_nascimento.route('/produtor/notificacao-nascimento/listar')
def listar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_permitida(id_propriedade):
        return redirect(URL_INICIAR)
    id_propriedade = int(id_propriedade)

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    hoje = date.today()

    with get_db_produtor(session['id_produtor']) as db:
        propriedade = db.get(Propriedade, id_propriedade)
        if not propriedade:
            return redirect(URL_INICIAR)

        gtas = _query_nas(db, id_propriedade).order_by(Gta.numero_gta_sequencial.desc()).all()
        impressas = {
            i.id_gta: i for i in db.query(NotificacaoImpressao).filter(
                NotificacaoImpressao.id_gta.in_([g.id for g in gtas] or [0])).all()
        }

        notificacoes = []
        for gta in gtas:
            total = db.query(Entrada).filter(Entrada.id_gta_entrada == gta.id).count()
            if total == 0:
                continue    # NAS aberto sem animais (ainda nao e Notificacao)
            conferidos = (
                db.query(Entrada)
                .filter(Entrada.id_gta_entrada == gta.id, Entrada.conferido_brete.is_(True))
                .count()
            )
            impressao = impressas.get(gta.id)

            prazo_texto, prazo_classe = '—', ''
            if impressao is None and gta.data_emissao:
                restantes = (gta.data_emissao + timedelta(days=PRAZO_ENVIO_DIAS) - hoje).days
                if restantes < 0:
                    prazo_texto, prazo_classe = f'Vencido há {-restantes} dia(s)', 'vencido'
                elif restantes <= DIAS_ALERTA_PRAZO:
                    prazo_texto, prazo_classe = f'{restantes} dia(s) restantes', 'urgente'
                else:
                    prazo_texto, prazo_classe = f'{restantes} dia(s) restantes', 'ok'

            notificacoes.append({
                'id': gta.id,
                'numero': gta.numero_gta_completo,
                'data': _data_br(gta.data_emissao),
                'qtde': total,
                'faltam': total - conferidos,
                'impressa': impressao is not None,
                'data_impressao': _data_br(impressao.data_impressao) if impressao else '',
                'prazo_texto': prazo_texto,
                'prazo_classe': prazo_classe,
            })

        propriedade_nome = propriedade.nome

    return render_template(
        'produtor/notificacao_nascimento_listar.html',
        propriedade_nome=propriedade_nome,
        id_propriedade=id_propriedade,
        notificacoes=notificacoes,
        erro=ERROS.get(request.args.get('erro', '')),
        url_voltar=_url_voltar(pares),
        titulo=TITULO,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/notificacao-nascimento/pdf/<id_gta>
# Primeira vez: monta o PDF, DEPOIS grava a impressao. Ja impressa:
# so reimprime (nunca grava).
# -------------------------------------------------------
@notificacao_nascimento.route('/produtor/notificacao-nascimento/pdf/<int:id_gta>')
def pdf(id_gta):
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_permitida(id_propriedade):
        return redirect(URL_INICIAR)
    id_propriedade = int(id_propriedade)
    url_lista = f'{URL_LISTAR}?id_propriedade={id_propriedade}'

    with get_db_produtor(session['id_produtor']) as db:
        gta = _query_nas(db, id_propriedade).filter(Gta.id == id_gta).first()
        if not gta:
            return redirect(f'{url_lista}&erro=inexistente')

        animais = (
            db.query(Entrada)
            .filter(Entrada.id_gta_entrada == gta.id)
            .order_by(Entrada.sisbov)
            .all()
        )
        if not animais:
            return redirect(f'{url_lista}&erro=inexistente')

        impressao = db.query(NotificacaoImpressao).filter_by(id_gta=gta.id).first()
        primeira_vez = impressao is None

        if primeira_vez and any(not a.conferido_brete for a in animais):
            return redirect(f'{url_lista}&erro=pendente')

        numero = gta.numero_gta_completo

        # ---- PDF primeiro (objetos ainda validos) ----
        contexto = _montar_contexto(db, gta, animais, id_propriedade, impressao)
        buffer = gerar_pdf_notificacao_nascimento(contexto)

        # ---- So agora grava a primeira impressao ----
        if primeira_vez:
            try:
                db.add(NotificacaoImpressao(
                    id_gta=gta.id,
                    data_impressao=date.today(),
                    id_usuario=session['usuario_id'],
                ))
                db.commit()
            except IntegrityError:
                db.rollback()    # duplo clique: ja foi gravada pela outra chamada

    nome_arquivo = f'notificacao_{numero}.pdf'
    return send_file(buffer, mimetype='application/pdf', as_attachment=False, download_name=nome_arquivo)

# =========================================================
# FIM DE ARQUIVO: backend\routers\notificacao_nascimento.py
# =========================================================
