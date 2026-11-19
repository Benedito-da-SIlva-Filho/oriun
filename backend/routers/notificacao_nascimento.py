# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\notificacao_nascimento.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-02 09:00 -03
# ATUALIZADO EM: 2026-11-16 10:40 -03
# VERSAO: 1.8.0
# v1.8.0: Sessao 128 (2026-11-16 10:40 -03) - AUDITORIA ETAPA 7b (Regra #57/#73): a trava _propriedade_permitida() passa a conferir tambem que o Produtor do par Propriedade+Produtor e o Produtor da sessao (antes so conferia a Propriedade). REVERSAO: .bak_antes_etapa7b.
# v1.7.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.6.0: Sessao 122 (2026-11-12 19:00 -03) - Auditoria Etapa 4 (Entradas): trava da Propriedade em Gerar (duplo clique nao gera 2 vezes). REVERSAO: .bak_antes_s122_etapa2.
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
#         NUNCA grava nada; o PDF sai igual ao da primeira vez (a frase de
#         REIMPRESSAO saiu na v1.2.0) e e BAIXADO para a pasta Downloads.
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
#     v1.0.2: Sessao 084 (02/10/2026, 15:10 -03) - pedido de Benedito: a
#             coluna RACA da tabela do PDF leva o CODIGO da raca (tb_4005,
#             campo 'codigo' - os 2 caracteres que a representam), nao o
#             nome por extenso. Nenhuma outra mudanca.
#     v1.0.3: Sessao 084 (02/10/2026, 21:00 -03) - prazo (30 dias) e alerta
#             (5 dias) vem de regras_sisbov.py v1.2.0 (antes constantes
#             locais). Nenhuma outra mudanca.
#     v1.1.0: Sessao 084 (02/10/2026, 23:30 -03) - GERAR NOTIFICACAO DO BRETE
#             (o brete pode brincar ANTES de o escritorio lancar): a lista
#             passa a mostrar tambem os Controles (NAS) PENDENTES com animais
#             lidos no brete, com o botao "Gerar Notificacao" (NOVA rota POST
#             gerar()), que fecha o Controle pela funcao gerar_notificacao_
#             do_brete() de gravacao_nascimento.py v1.3.0 - tudo ou nada.
#             Depois de gerada, a Notificacao segue o fluxo normal (Imprimir,
#             PIA, relatorios). Impressao/Reimpressao SEM mudanca.
#     v1.2.0: Sessao 084 (02/10/2026, 19:20 -03) - pedido de Benedito: Imprimir e
#             Reimprimir passam a BAIXAR o PDF (notificacao_NASxxxxxxx.pdf na
#             pasta Downloads) em vez de abri-lo no navegador/Adobe
#             (send_file com as_attachment=True). Regra de gravar a primeira
#             impressao, ordem PDF-primeiro e travas SEM mudanca.
#     v1.3.0: Sessao 090 (08/10/2026, 07:06 -03) - FAZENDA EM USO (Regra de Ouro
#             #13, Lote 1 - Nascimento). Tres pontos:
#               - iniciar(): com fazenda em uso valida (auth.
#                 resolver_fazenda_em_uso), PULA a tela "Selecionar
#                 Propriedade" e abre a Lista direto nela. Sem fazenda em uso,
#                 ou com uma fazenda so, tudo igual a antes.
#               - VOLTAR: o destino passa a ser o Hub novo "Nascimento /
#                 Desmame" (/produtor/hub-novo/entrada-nascimento). Com fazenda
#                 em uso a selecao nao existe mais, entao a Lista volta direto
#                 ao Hub (nunca ao iniciar(), que reabriria a Lista: laco).
#               - TRAVA (_propriedade_permitida): se a Propriedade da URL for
#                 DIFERENTE da fazenda em uso (ex.: trocada em outra aba), a
#                 rota nao le nem grava nada e manda para o iniciar(), que abre
#                 a Lista na fazenda em uso. Vale para listar, pdf (primeira
#                 impressao) e gerar.
#             Nenhuma mudanca em PDF, impressao, Gerar Notificacao, prazos e Log.
#     v1.4.0: Sessao 101 (20/10/2026, 20:00 -03) - PDF no modelo do GERAS (pdf_notificacao_nascimento.py 2.0.0).
#             _montar_contexto() refeito: dados da origem (CPF/CNPJ pela regra por fazenda, Inscricao Estadual,
#             Cod. ERAS, NIRF, municipio e UF), um GRUPO por fabricante de brinco (tb_7017 -> tb_3007 -> tb_1021,
#             mesmo criterio da PIA; sem fabricante/logo o formulario sai sem logo), especie, brincagem e
#             idade em MESES COMPLETOS (nascimento -> brincagem). Rotas, travas, listagem, impressao unica e
#             Gerar Notificacao SEM mudanca. REVERSAO: .bak_antes_geras_s101
#     v1.5.0: Sessao 104 (23/10/2026, 08:50 -03) - CAIXA DE SUCESSO (Padrao No7): depois de Gerar Notificacao (animais lidos no brete) o usuario ve a tela
#             de conclusao (numero, Propriedade, animais) em vez da faixa verde na lista. Nova rota GET /produtor/notificacao-nascimento/gerada (le e apaga o
#             resumo da sessao; F5 nao repete). A mensagem de ERRO continua na lista. Nenhuma mudanca na geracao, PDF, impressao e prazos.
#             Precisa do caixa_sucesso.py 1.1.0 e do notificacao_nascimento_listar.html 1.3.0.  REVERSAO: .bak_antes_s104 (router e lista).
# =========================================================

from datetime import date, datetime, timedelta

from flask import Blueprint, redirect, render_template, request, send_file, session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.utils.gravacao_nascimento import TRAVA_BRINCOS_NASC

from backend.database import engine
from backend.models import Produtor, Propriedade
from backend.models.propriedade_produtor import PropriedadeProdutor
from backend.models.tb_1021_fabricantes_brincos import Fabricante
from backend.models.tb_3007_brincos_entrada import BrincoEntrada
from backend.models.tb_4002_especie import Especie
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4005_racas import Raca
from backend.models.tb_7020_notificacao_impressao import NotificacaoImpressao
from backend.routers.auth import buscar_pares_propriedade_produtor, redirecionar_home, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.caixa_sucesso import render_caixa_sucesso   # v1.5.0 - Padrao No7
from backend.utils.documentos_produtor import documentos_do_produtor
from backend.utils.gravacao_nascimento import contar_leituras_do_controle, gerar_notificacao_do_brete, STATUS_CONTROLE_ABERTO
from backend.utils.pdf_notificacao_nascimento import gerar_pdf_notificacao_nascimento
from backend.utils.pdf_pia import _caminho_logo
from backend.utils.regras_sisbov import PRAZO_ENVIO_NOTIFICACAO_DIAS, DIAS_ALERTA_PRAZO_NOTIFICACAO

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
PRAZO_ENVIO_DIAS = PRAZO_ENVIO_NOTIFICACAO_DIAS      # v1.0.3 - regras_sisbov.py
DIAS_ALERTA_PRAZO = DIAS_ALERTA_PRAZO_NOTIFICACAO    # v1.0.3 - regras_sisbov.py

URL_INICIAR = '/produtor/notificacao-nascimento/iniciar'
URL_LISTAR = '/produtor/notificacao-nascimento/listar'
CHAVE_MENSAGEM_SESSAO = 'notificacao_mensagem'   # v1.1.0 - faixa vermelha de erro (1 vez); v1.5.0: o sucesso saiu daqui
URL_GERADA = '/produtor/notificacao-nascimento/gerada'   # v1.5.0 - Caixa de Sucesso
CHAVE_SUCESSO_SESSAO = 'notificacao_sucesso'     # v1.5.0 - resumo da Caixa de Sucesso (1 vez)
VOLTAR_SUBHUB = '/produtor/hub-novo/entrada-nascimento'   # v1.3.0 - Hub novo Nascimento / Desmame
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
# -------------------------------------------------------
# Trava de permissao (usada por TODAS as rotas do modulo).
# 1) a Propriedade da URL tem de ser de um par do usuario logado;
# 2) v1.3.0 - FAZENDA EM USO: se ha uma e ela e DIFERENTE da Propriedade
#    da URL (trocada em outra aba, por exemplo), devolve False - o chamador
#    manda para o iniciar(), que abre a fazenda em uso. Nada e lido nem
#    gravado numa fazenda enquanto a faixa mostra outra.
# -------------------------------------------------------
def _propriedade_permitida(id_propriedade):
    if not str(id_propriedade).isdecimal():
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if int(id_propriedade) not in {int(par.id_propriedade) for par in pares if str(par.id_produtor) == str(session.get('id_produtor'))}:   # v1.8.0 - Produtor do par = Produtor da sessao (Etapa 7b)
        return False
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and int(par_em_uso.id_propriedade) != int(id_propriedade):
        return False
    return True


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


# -------------------------------------------------------
# Destino do botao Voltar da Lista (Regra de Ouro #9). v1.3.0: com fazenda
# em uso a selecao e pulada - volta direto ao Hub (voltar ao iniciar()
# reabriria a Lista: laco). So volta para a selecao quem tem 2+ pares e
# nenhuma fazenda em uso (caso que a guarda central do auth.py ja barra).
# -------------------------------------------------------
def _url_voltar(pares):
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return URL_INICIAR
    return VOLTAR_SUBHUB


def _meses_completos(nascimento, brincagem):
    """Meses COMPLETOS entre o nascimento e a brincagem (v1.4.0); None se faltar data."""
    if not nascimento or not brincagem:
        return None
    meses = (brincagem.year - nascimento.year) * 12 + (brincagem.month - nascimento.month)
    if brincagem.day < nascimento.day:
        meses -= 1
    return max(meses, 0)


def _fabricante_por_sisbov(db, id_propriedade, sisbovs):
    """{sisbov: dados do fabricante} - mesma cadeia da PIA: tb_7017 (linha ENTRADA tem prioridade) -> lote
    tb_3007 -> fabricante tb_1021. SISBOV sem fabricante simplesmente nao aparece no dicionario."""
    lote_por_sisbov = {}
    sisbovs = sorted(set(sisbovs))
    for i in range(0, len(sisbovs), 500):
        linhas = (
            db.query(EntradaBrincoRfid)
            .filter(EntradaBrincoRfid.id_propriedade == int(id_propriedade),
                    EntradaBrincoRfid.sisbov.in_(sisbovs[i:i + 500]))
            .all()
        )
        for linha in linhas:
            atual = lote_por_sisbov.get(linha.sisbov)
            prioridade = 2 if linha.status == 'ENTRADA' else (1 if linha.saida_gta else 0)
            if atual is None or prioridade > atual[1]:
                lote_por_sisbov[linha.sisbov] = (linha.id_lote_entrada, prioridade)

    ids_lotes = sorted({v[0] for v in lote_por_sisbov.values() if v[0]})
    fabricante_por_lote = {}
    for i in range(0, len(ids_lotes), 500):
        for lote in db.query(BrincoEntrada).filter(BrincoEntrada.id.in_(ids_lotes[i:i + 500])).all():
            fabricante_por_lote[lote.id] = lote.id_fabricante

    ids_fab = sorted({f for f in fabricante_por_lote.values() if f})
    fabricantes = {}
    if ids_fab:
        with Session(engine) as db_public:
            for f in db_public.query(Fabricante).filter(Fabricante.id.in_(ids_fab)).all():
                fabricantes[f.id] = {'id': f.id, 'nome': f.nome or '', 'logo': f.logo}

    resultado = {}
    for sisbov, (id_lote, _) in lote_por_sisbov.items():
        fab = fabricantes.get(fabricante_por_lote.get(id_lote))
        if fab:
            resultado[sisbov] = fab
    return resultado


def _montar_contexto(db, gta, animais, id_propriedade, impressao):
    """Dict so com TEXTO/numeros (nada de objeto do banco) - o PDF e
    montado antes de qualquer commit."""
    propriedade = db.get(Propriedade, int(id_propriedade))
    produtor = db.get(Produtor, session['id_produtor'])
    racas = {r.id: r.codigo for r in db.query(Raca).all()}   # v1.0.2 - codigo, nao o nome
    try:
        especies = {e.id: e.descricao for e in db.query(Especie).all()}
    except Exception:
        especies = {}

    vinculo = None
    if produtor is not None:
        vinculo = (
            db.query(PropriedadeProdutor)
            .filter_by(id_propriedade=int(id_propriedade), id_produtor=produtor.id, data_fim=None)
            .first()
        )
    cpf, cnpj = documentos_do_produtor(produtor, vinculo)   # principal + secundario DESTA fazenda
    inscricao = (getattr(vinculo, 'inscricao_estadual', None) or getattr(propriedade, 'inscricao_estadual', None)
                 or '') if propriedade is not None else ''

    fabricante_do_sisbov = _fabricante_por_sisbov(db, id_propriedade, [a.sisbov for a in animais])

    por_fabricante = {}
    for a in animais:
        fab = fabricante_do_sisbov.get(a.sisbov)
        chave = fab['id'] if fab else None
        grupo = por_fabricante.setdefault(chave, {'fab': fab, 'animais': []})
        brincagem = a.data_brincagem or gta.data_emissao
        grupo['animais'].append({
            'sisbov': a.sisbov,
            'manejo': a.manejo,
            'especie': especies.get(a.id_especie, 'Bovinos'),
            'sexo': 'MACHO' if a.sexo == 'MACHO' else ('FEMEA' if a.sexo == 'FEMEA' else (a.sexo or '')),
            'raca': racas.get(a.id_raca, ''),
            'nascimento': _data_br(a.nascimento),
            'brincagem': _data_br(brincagem),
            'meses': _meses_completos(a.nascimento, brincagem),
        })

    grupos = []
    # fabricantes por nome; os animais sem fabricante (sem logo) por ultimo
    for chave, grupo in sorted(por_fabricante.items(), key=lambda kv: (kv[0] is None, (kv[1]['fab'] or {}).get('nome', ''))):
        logo = None
        if grupo['fab'] and grupo['fab'].get('logo'):
            try:
                logo = _caminho_logo(grupo['fab']['logo'])
            except Exception as erro:   # sem logo nunca quebra a Notificacao
                print(f'[NASCIMENTO] Logo nao resolvida: {erro}')
        grupos.append({'logo': logo, 'animais': grupo['animais']})

    return {
        'numero': gta.numero_gta_completo,
        'reimpressao': impressao is not None,
        'produtor': produtor.nome if produtor else None,
        'cpf': cpf,
        'cnpj': cnpj,
        'inscricao_estadual': inscricao,
        'codigo_eras': propriedade.codigo_eras if propriedade else None,
        'propriedade': propriedade.nome if propriedade else None,
        'municipio': propriedade.municipio if propriedade else '',
        'uf': propriedade.uf if propriedade else '',
        'nirf': getattr(propriedade, 'nirf_incra', None) or '',
        'gerado_em': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'grupos': grupos,
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

    # v1.3.0 - FAZENDA EM USO: ja escolhida no Home novo (conferida contra os
    # pares do usuario) - pula a tela de selecao e abre a Lista direto.
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor'] = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{URL_LISTAR}?id_propriedade={par_em_uso.id_propriedade}')

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
            # v1.1.0 - Controle PENDENTE (o brete leu primeiro): aguarda "Gerar Notificacao"
            if gta.status_brincagem == STATUS_CONTROLE_ABERTO:
                lidos = contar_leituras_do_controle(db, gta)
                if lidos > 0:
                    prazo_texto, prazo_classe = '—', ''
                    if gta.data_emissao:
                        restantes = (gta.data_emissao + timedelta(days=PRAZO_ENVIO_DIAS) - hoje).days
                        if restantes < 0:
                            prazo_texto, prazo_classe = f'Vencido há {-restantes} dia(s)', 'vencido'
                        elif restantes <= DIAS_ALERTA_PRAZO:
                            prazo_texto, prazo_classe = f'{restantes} dia(s) restantes', 'urgente'
                        else:
                            prazo_texto, prazo_classe = f'{restantes} dia(s) restantes', 'ok'
                    notificacoes.append({
                        'id': gta.id, 'numero': gta.numero_gta_completo, 'data': _data_br(gta.data_emissao),
                        'qtde': lidos, 'faltam': 0, 'impressa': False, 'data_impressao': '',
                        'prazo_texto': prazo_texto, 'prazo_classe': prazo_classe, 'aberto': True,
                    })
                continue

            total = db.query(Entrada).filter(Entrada.id_gta_entrada == gta.id).count()
            if total == 0:
                continue    # NAS sem animais (ainda nao e Notificacao)
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
                'aberto': False,
            })

        propriedade_nome = propriedade.nome

    return render_template(
        'produtor/notificacao_nascimento_listar.html',
        propriedade_nome=propriedade_nome,
        id_propriedade=id_propriedade,
        notificacoes=notificacoes,
        erro=ERROS.get(request.args.get('erro', '')) or session.pop(CHAVE_MENSAGEM_SESSAO + '_erro', None),
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
    # v1.2.0 - BAIXA o arquivo (pasta Downloads) em vez de abrir no navegador/Adobe.
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)


# -------------------------------------------------------
# Rota: POST /produtor/notificacao-nascimento/gerar/<id_gta>
# v1.1.0 - gera a Notificacao de um Controle PENDENTE (animais lidos no
# brete antes do lancamento do escritorio). Tudo ou nada.
# -------------------------------------------------------
@notificacao_nascimento.route('/produtor/notificacao-nascimento/gerar/<int:id_gta>', methods=['POST'])
def gerar(id_gta):
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.form.get('id_propriedade', '')
    if not _propriedade_permitida(id_propriedade):
        return redirect(URL_INICIAR)
    id_propriedade = int(id_propriedade)
    url_lista = f'{URL_LISTAR}?id_propriedade={id_propriedade}'

    with get_db_produtor(session['id_produtor']) as db:
        # Etapa 4 (item 3): trava da Propriedade ANTES de ler o Controle - duplo clique / 2 abas nao geram a Notificacao 2 vezes.
        db.execute(text('SELECT pg_advisory_xact_lock(:ns, :id)'), {'ns': TRAVA_BRINCOS_NASC, 'id': int(id_propriedade)})
        controle = _query_nas(db, id_propriedade).filter(Gta.id == id_gta).first()
        if not controle:
            return redirect(f'{url_lista}&erro=inexistente')
        try:
            numero, qtde = gerar_notificacao_do_brete(
                db, controle, session['id_produtor'], session.get('usuario_id'))
            propriedade = db.get(Propriedade, id_propriedade)   # v1.5.0 - lido ANTES do commit
            propriedade_nome = propriedade.nome if propriedade else ''
            db.commit()
        except ValueError as erro:
            db.rollback()
            session[CHAVE_MENSAGEM_SESSAO + '_erro'] = f'Notificação não gerada — {erro} Nada foi gravado.'
            return redirect(url_lista)

    session[CHAVE_SUCESSO_SESSAO] = {'numero': numero, 'qtde': qtde, 'propriedade': propriedade_nome, 'id_propriedade': id_propriedade}
    return redirect(URL_GERADA)


# -------------------------------------------------------
# Rota: GET /produtor/notificacao-nascimento/gerada  (v1.5.0)
# CAIXA DE SUCESSO (Padrao No7) depois de Gerar Notificacao. Le e apaga o
# resumo guardado na sessao; sem resumo (F5, link antigo), volta para a lista.
# A Propriedade do resumo e conferida de novo (trava de permissao).
# -------------------------------------------------------
@notificacao_nascimento.route(URL_GERADA)
def gerada():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    resumo = session.pop(CHAVE_SUCESSO_SESSAO, None)
    if not resumo or not _propriedade_permitida(resumo['id_propriedade']):
        return redirect(URL_INICIAR)

    url_lista = f"{URL_LISTAR}?id_propriedade={int(resumo['id_propriedade'])}"
    mudancas = [
        {'campo': 'Notificação', 'antes': None, 'depois': resumo['numero']},
        {'campo': 'Propriedade', 'antes': None, 'depois': resumo['propriedade']},
        {'campo': 'Animais lidos no brete', 'antes': None, 'depois': str(resumo['qtde'])},
    ]
    contexto = dict(
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )
    return render_caixa_sucesso(
        contexto, titulo='Notificação gerada com sucesso!', subtitulo=resumo['numero'],
        mudancas=mudancas,
        botoes=[{'texto': 'Voltar à lista de Notificações', 'url': url_lista, 'primario': True}],
        url_voltar=url_lista, titulo_pagina='Orion SISBOV — Notificação gerada',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\notificacao_nascimento.py
# =========================================================
