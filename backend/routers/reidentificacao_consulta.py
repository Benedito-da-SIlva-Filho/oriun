# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\reidentificacao_consulta.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-11 13:00 -03
# ATUALIZADO EM: 2026-11-11 20:45 -03
# VERSAO: 2.2.1
#
# DESCRICAO:
#     Reidentificacao (Sessao 121): CONSULTA dos pedidos, NOTIFICACAO (PDF no modelo do formulario do Magic), marcar como ENVIADO e lista de
#     INCONFORMIDADES.
#
#     ROTAS:
#       /produtor/reidentificacao-consulta/iniciar     - resolve a Propriedade.
#       /produtor/reidentificacao-consulta/lista       - pedidos da Propriedade (mais novo primeiro) + itens do pedido escolhido (?pedido=N).
#       /produtor/reidentificacao-consulta/pdf  (POST) - gera a Notificacao (PDF) e grava notificacao_gerada_em. Pode gerar de novo.
#       /produtor/reidentificacao-consulta/excluir-animal (POST) - exclui UM animal pendente, so ate a Notificacao ser gerada (utils/reidentificacao_exclusao.py).
#       /produtor/reidentificacao-consulta/enviar (POST) - "Marcar como enviado": exige Notificacao gerada; grava enviado_em/enviado_por e
#                                                         registra no Log (modulo 'reidentificacao_envio', so historico).
#       /produtor/reidentificacao-inconformes/iniciar  - resolve a Propriedade.
#       /produtor/reidentificacao-inconformes/lista    - tentativas recusadas (tb_4010), da mais nova para a mais antiga, filtro opcional por dia.
#
#     Situacao do pedido: ABERTO (nada gerado) -> NOTIFICACAO GERADA (PDF gerado) -> ENVIADO (usuario confirmou o envio a Certificadora).
#     Prazo: 30 dias a partir da data da reidentificacao (aparece como 'em aberto ha X dias' enquanto nao for ENVIADO).
#     Permissao: segmentos 'reidentificacao-consulta' e 'reidentificacao-inconformes' = modulo 'entrada'. Os 2 POSTs entram em
#     GETS_QUE_GRAVAM/POST de lancamento conforme permissoes.py (quem so consulta nao gera nem envia).
#
#     v1.0.0: Criacao (Sessao 121, 11/11/2026, 13:00 -03). Molde: linkagem_consulta.py.
#     v1.1.0: Sessao 121 (11/11/2026, 14:45 -03) - Excluir animal do pedido (rota excluir-animal; lista passa o id e 'pode_excluir' de cada item). Por que: o usuario percebe o erro ao conferir antes de gerar a Notificacao. REVERSAO: .bak_antes_s121_exclusao.
#     v1.1.1: Sessao 121 (11/11/2026, 14:15 -03) - Corrige erro 500 depois de excluir: a consulta 'o pedido ainda existe?' rodava depois do commit, sem o schema do Produtor. Agora roda antes do commit. REVERSAO: .bak_antes_s121_exclusao.
#     v2.0.0: Sessao 121 (2026-11-11 18:10 -03) - MODELO PENDENTES (decisao do Benedito, 11/11/2026): a tela tem 2 blocos - 'Pendentes de Notificacao' (animais
#         lancados, sem numero, com ✖ para excluir) e 'Notificacoes geradas'. Rota NOVA /gerar: pega TODOS os pendentes da Propriedade, cria a
#         Notificacao com o proximo numero (sem buracos: so existe depois de gerada), grava notificacao_gerada_em e devolve o PDF (cada animal com a
#         sua data). /pdf passa a so REIMPRIMIR uma Notificacao ja gerada. Prazo de 30 dias conta do animal pendente/nao enviado mais antigo.
#         REVERSAO: .bak_antes_s121_pendentes.
#     REVERSAO (v1.0.0): remover este arquivo, pdf_reidentificacao.py, os 2 templates, o registro em app.py, os cards do Hub e as linhas de permissoes.py.
#     v2.1.0: Sessao 121 (2026-11-11 18:10 -03) - Gerar Notificacao so grava com a conferencia marcada (campo 'confirmo'); sem ela o servidor recusa (erro=sem_confirmacao). REVERSAO: .bak_antes_s121_validacao.
#     v2.2.1: Sessao 121 (2026-11-11 20:45 -03) - Corrige erro 500 ao Marcar como enviado: o numero da Notificacao era lido DEPOIS do commit (objeto expirado, nova consulta sem o schema do produtor). Agora e guardado antes. Reversao: .bak_antes_s121_enviar.
#     v2.2.0: Sessao 121 (2026-11-11 18:40 -03) - Gerar Notificacao grava o PIA (tb_7002, Motivo REIDENTIFICACAO) de cada animal, na ordem do lancamento, com numeracao sequencial da Propriedade; animal de lancamento antigo que ja tem PIA nao ganha outro. REVERSAO: .bak_antes_s121_pia.
# =========================================================

from datetime import datetime, date
from urllib.parse import quote

from flask import Blueprint, render_template, request, redirect, session, send_file
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, Produtor, PropriedadeProdutor
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_4010_reidentificacao_inconformes import ReidentificacaoInconforme
from backend.models.tb_6005_reidentificacao_com_baixa import ReidentificacaoComBaixa
from backend.models.tb_6006_reidentificacao_com_baixa_itens import ReidentificacaoComBaixaItem
from backend.models.tb_4005_racas import Raca
from backend.models.tb_7002_pia import Pia
from backend.models.usuario import Usuario
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.gta_manual import municipio_sem_uf
from backend.routers.saida_leitor import _propriedade_do_usuario, _data_br, _ler_data_br
from backend.utils.documentos_produtor import documentos_do_produtor
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.multitenant import get_db_produtor
from backend.utils.pdf_reidentificacao import gerar_pdf_reidentificacao
from backend.utils.reidentificacao_exclusao import excluir_animal

reidentificacao_consulta = Blueprint('reidentificacao_consulta', __name__)


@reidentificacao_consulta.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


URL_HUB                 = '/produtor/hub-novo/entrada'
URL_CONSULTA_INICIAR    = '/produtor/reidentificacao-consulta/iniciar'
URL_CONSULTA_LISTA      = '/produtor/reidentificacao-consulta/lista'
URL_INCONF_INICIAR      = '/produtor/reidentificacao-inconformes/iniciar'
URL_INCONF_LISTA        = '/produtor/reidentificacao-inconformes/lista'
LIMITE_PEDIDOS = 200
LIMITE_INCONFORMES = 300
PRAZO_DIAS = 30
MOTIVO_TELA = {'PERDA': 'Perda', 'QUEBRA': 'Quebra', 'DESGASTE': 'Desgaste', 'DEFEITO_LEITURA': 'Defeito de leitura'}
SEXO_TELA = {'FEMEA': 'Fêmea', 'MACHO': 'Macho'}


def _contexto_tela():
    return {
        'usuario_nome':   session.get('usuario_nome'),
        'usuario_perfil': session.get('usuario_perfil'),
        'cor_primaria':   session.get('cor_primaria', '#D4370A'),
        'nome_sistema':   session.get('nome_sistema', 'Orion SISBOV'),
        'menu_ativo':     'entrada',
    }


def _negado(url_iniciar):
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect(url_iniciar)
    return redirecionar_home()


def _url_voltar(url_iniciar):
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    return url_iniciar if (len(pares) > 1 and resolver_fazenda_em_uso(pares) is None) else URL_HUB


def _iniciar(titulo, proximo, url_iniciar):
    if 'id_produtor' not in session:
        return redirecionar_home()
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{proximo}?id_propriedade={par_em_uso.id_propriedade}')
    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{proximo}?id_propriedade={par.id_propriedade}')
    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None if pares else 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
        titulo=titulo, proximo=proximo, campo_propriedade='id_propriedade', voltar=URL_HUB,
        **_contexto_tela(),
    )


def _dias_desde(data):
    return max((date.today() - data).days, 0) if data else None


def _resumo_notificacao(p, mais_antiga):
    """Notificacao gerada: GERADA (ainda nao enviada, conta o prazo) ou ENVIADO."""
    enviado = p.enviado_em is not None
    dias = None if enviado else _dias_desde(mais_antiga)
    return {
        'id': p.id, 'numero': f'{p.id:06d}', 'data': _data_br(p.data_solicitacao), 'quantidade': p.qtde_animais,
        'situacao': 'ENVIADO' if enviado else 'GERADA', 'situacao_txt': 'Enviado' if enviado else 'Gerada', 'dias': dias,
        'prazo_estourado': bool(dias is not None and dias > PRAZO_DIAS),
        'gerada_em': p.notificacao_gerada_em.strftime('%d/%m/%Y %H:%M') if p.notificacao_gerada_em else '',
        'enviado_em': p.enviado_em.strftime('%d/%m/%Y %H:%M') if p.enviado_em else '',
    }


def _montar_itens(db, id_propriedade, linhas):
    novos = [l.sisbov_novo for l in linhas]
    animais = {}
    if novos:
        for e in db.query(Entrada).filter(Entrada.id_propriedade == int(id_propriedade), Entrada.sisbov.in_(novos)).all():
            animais[e.sisbov] = e
    itens = []
    for seq, l in enumerate(linhas, start=1):
        e = animais.get(l.sisbov_novo)
        sexo = ''
        if e is not None:
            sexo = str(e.sexo.value if hasattr(e.sexo, 'value') else (e.sexo or ''))
        itens.append({
            'id': l.id, 'seq': seq, 'sisbov_antigo': l.sisbov_antigo, 'sisbov_novo': l.sisbov_novo,
            'manejo_antigo': l.manejo_antigo or '', 'manejo_novo': l.manejo_novo or '',
            'rfid': l.rfid or '', 'sexo': SEXO_TELA.get(sexo, sexo),
            'motivo': MOTIVO_TELA.get(l.motivo or '', l.motivo or ''),
            'data': _data_br(l.data_reidentificacao) if l.data_reidentificacao else '',
        })
    return itens


def _itens_do_pedido(db, id_propriedade, id_pedido):
    linhas = (db.query(ReidentificacaoComBaixaItem)
              .filter(ReidentificacaoComBaixaItem.id_pedido == id_pedido)
              .order_by(ReidentificacaoComBaixaItem.id.asc()).all())
    return _montar_itens(db, id_propriedade, linhas)


def _itens_pendentes(db, id_propriedade):
    linhas = (db.query(ReidentificacaoComBaixaItem)
              .filter(ReidentificacaoComBaixaItem.id_propriedade == int(id_propriedade),
                      ReidentificacaoComBaixaItem.id_pedido.is_(None))
              .order_by(ReidentificacaoComBaixaItem.id.asc()).all())
    mais_antiga = min((l.data_reidentificacao for l in linhas if l.data_reidentificacao), default=None)
    return _montar_itens(db, id_propriedade, linhas), mais_antiga


def _ctx_pdf(id_produtor, id_propriedade, numero, data_notificacao, itens):
    """Monta os dados do PDF (usa o banco publico: Produtor, Propriedade)."""
    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
        produtor = db.get(Produtor, id_produtor)
        vinculo = None
        if produtor is not None:
            vinculo = (db.query(PropriedadeProdutor)
                       .filter_by(id_propriedade=int(id_propriedade), id_produtor=produtor.id, data_fim=None).first())
        cpf, cnpj = documentos_do_produtor(produtor, vinculo)
        inscricao = (getattr(vinculo, 'inscricao_estadual', None) or getattr(propriedade, 'inscricao_estadual', None)
                     or '') if propriedade is not None else ''
        endereco = ' '.join(t for t in (getattr(produtor, 'logradouro', None), getattr(produtor, 'numero', None)) if t)
        municipio = municipio_sem_uf(produtor.municipio, produtor.uf) if produtor else ''
        return {
            'data_solicitacao': _data_br(data_notificacao), 'nro_pedido': numero,
            'gerado_em_completo': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'produtor': produtor.nome if produtor else '', 'cpf': cpf, 'cnpj': cnpj,
            'endereco': endereco, 'complemento': (getattr(produtor, 'complemento', None) or ''),
            'bairro': (getattr(produtor, 'bairro', None) or ''), 'municipio': municipio,
            'uf': (produtor.uf if produtor else ''), 'cep': (getattr(produtor, 'cep', None) or ''),
            'email': (getattr(produtor, 'email', None) or ''), 'fone': (getattr(produtor, 'telefone', None) or ''),
            'celular': (getattr(produtor, 'telefone2', None) or ''),
            'propriedade': propriedade.nome if propriedade else '',
            'codigo_eras': propriedade.codigo_eras if propriedade else '', 'inscricao_estadual': inscricao,
            'email_propriedade': (getattr(propriedade, 'email', None) or '') if propriedade else '',
            'contato_propriedade': '',
            'local_data': f"{municipio}, {datetime.now().strftime('%d/%m/%Y')}" if municipio else datetime.now().strftime('%d/%m/%Y'),
            'itens': itens,
        }


# -------------------------------------------------------
# CONSULTA (tela)
# -------------------------------------------------------
@reidentificacao_consulta.route('/produtor/reidentificacao-consulta/iniciar')
def consulta_iniciar():
    return _iniciar('Consulta da Reidentificação — Selecionar Propriedade', URL_CONSULTA_LISTA, URL_CONSULTA_INICIAR)


@reidentificacao_consulta.route('/produtor/reidentificacao-consulta/lista')
def consulta_lista():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado(URL_CONSULTA_INICIAR)

    msg_livre = (request.args.get('msg', '') or '')[:300]
    erro = {'sem_pdf': 'Gere a Notificação antes de marcar como enviado.',
            'inexistente': 'Notificação não encontrada.',
            'ja_enviado': 'Esta Notificação já foi marcada como enviada.',
            'sem_pendentes': 'Não há animais pendentes de Notificação.',
            'gerar': 'Não foi possível gerar a Notificação. Nada foi alterado.',
            'sem_confirmacao': 'Marque a conferência dos animais antes de gerar a Notificação.',
            'exclusao': msg_livre}.get(request.args.get('erro', ''))
    aviso = {'enviado': 'Notificação marcada como enviada à Certificadora.',
             'excluido': msg_livre}.get(request.args.get('ok', ''))
    try:
        escolhido = int(request.args.get('pedido', '') or 0)
    except ValueError:
        escolhido = 0

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
    pendentes, pend_antiga, pend_dias, notificacoes, pedido_sel, itens = [], None, None, [], None, []
    try:
        with get_db_produtor(session['id_produtor']) as db:
            pendentes, antiga = _itens_pendentes(db, id_propriedade)
            if antiga is not None:
                pend_antiga, pend_dias = _data_br(antiga), _dias_desde(antiga)
            linhas = (db.query(ReidentificacaoComBaixa)
                      .filter(ReidentificacaoComBaixa.id_propriedade == int(id_propriedade))
                      .order_by(ReidentificacaoComBaixa.id.desc()).limit(LIMITE_PEDIDOS).all())
            ids = [p.id for p in linhas]
            menores = {}
            if ids:
                menores = dict(db.query(ReidentificacaoComBaixaItem.id_pedido, func.min(ReidentificacaoComBaixaItem.data_reidentificacao))
                               .filter(ReidentificacaoComBaixaItem.id_pedido.in_(ids))
                               .group_by(ReidentificacaoComBaixaItem.id_pedido).all())
            notificacoes = [_resumo_notificacao(p, menores.get(p.id) or p.data_solicitacao) for p in linhas]
            if escolhido:
                alvo = next((p for p in linhas if p.id == escolhido), None)
                if alvo is not None:
                    pedido_sel = _resumo_notificacao(alvo, menores.get(alvo.id) or alvo.data_solicitacao)
                    itens = _itens_do_pedido(db, id_propriedade, alvo.id)
                else:
                    erro = erro or 'Notificação não encontrada.'
    except Exception:
        erro = erro or 'Não foi possível consultar a Reidentificação agora. Verifique se o script do banco foi aplicado.'

    return render_template(
        'produtor/reidentificacao_consulta.html',
        erro=erro, aviso=aviso, propriedade=propriedade, id_propriedade=id_propriedade,
        pendentes=pendentes, pend_antiga=pend_antiga, pend_dias=pend_dias,
        pend_estourado=bool(pend_dias is not None and pend_dias > PRAZO_DIAS),
        notificacoes=notificacoes, pedido=pedido_sel, itens=itens, prazo_dias=PRAZO_DIAS,
        url_voltar=_url_voltar(URL_CONSULTA_INICIAR), **_contexto_tela(),
    )


# -------------------------------------------------------
# GERAR NOTIFICACAO - POST: pega TODOS os pendentes, cria o proximo numero (sem buracos) e devolve o PDF
# -------------------------------------------------------
@reidentificacao_consulta.route('/produtor/reidentificacao-consulta/gerar', methods=['POST'])
def consulta_gerar():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.form.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado(URL_CONSULTA_INICIAR)
    volta = f'{URL_CONSULTA_LISTA}?id_propriedade={int(id_propriedade)}'
    if request.form.get('confirmo') != '1':   # v2.1.0 - o usuario precisa marcar a conferencia
        return redirect(f'{volta}&erro=sem_confirmacao')

    id_produtor = session['id_produtor']
    with get_db_produtor(id_produtor) as db:
        try:
            # trava a tabela: duas pessoas gerando ao mesmo tempo nao pegam o mesmo numero
            db.execute(text('LOCK TABLE tb_6005_reidentificacao_com_baixa IN EXCLUSIVE MODE'))
            linhas = (db.query(ReidentificacaoComBaixaItem)
                      .filter(ReidentificacaoComBaixaItem.id_propriedade == int(id_propriedade),
                              ReidentificacaoComBaixaItem.id_pedido.is_(None))
                      .order_by(ReidentificacaoComBaixaItem.id.asc()).with_for_update().all())
            if not linhas:
                db.rollback()
                return redirect(f'{volta}&erro=sem_pendentes')
            numero_int = (db.query(func.max(ReidentificacaoComBaixa.id)).scalar() or 0) + 1
            agora = datetime.now()
            pedido = ReidentificacaoComBaixa(
                id=numero_int, id_propriedade=int(id_propriedade), qtde_animais=len(linhas),
                data_solicitacao=agora.date(), id_usuario=session.get('usuario_id'), notificacao_gerada_em=agora)
            db.add(pedido)
            db.flush()
            for l in linhas:
                l.id_pedido = numero_int
            db.flush()
            itens = _montar_itens(db, id_propriedade, linhas)
            id_operacao = registrar_operacao(
                db, id_usuario=session['usuario_id'], id_propriedade=int(id_propriedade),
                modulo='reidentificacao_notificacao',
                descricao=f'Reidentificação — Notificação {numero_int:06d} gerada ({len(linhas)} animal(is))'[:120],
            )
            registrar_item(db, id_operacao, 'tb_6005_reidentificacao_com_baixa', numero_int, 'INSERT', None,
                           {'qtde_animais': len(linhas), 'notificacao_gerada_em': agora.isoformat(timespec='seconds')})

            # PIA de cada animal (so agora, na ordem do lancamento): sequencial por Propriedade, com bloqueio
            db.execute(text('SELECT pg_advisory_xact_lock(:id_propriedade)'), {'id_propriedade': int(id_propriedade)})
            numero_pia = db.query(func.max(Pia.numero_pia)).filter(Pia.id_propriedade == int(id_propriedade)).scalar() or 0
            for l in linhas:
                if db.query(Pia.id).filter(Pia.id_propriedade == int(id_propriedade), Pia.sisbov == l.sisbov_novo).first() is not None:
                    continue   # lancamento antigo (teste) que ja gravou o PIA
                animal = db.query(Entrada).filter(Entrada.id_propriedade == int(id_propriedade), Entrada.sisbov == l.sisbov_novo).first()
                raca = db.get(Raca, animal.id_raca) if (animal is not None and animal.id_raca) else None
                numero_pia += 1
                pia = Pia(
                    id_propriedade=int(id_propriedade), numero_pia=numero_pia, id_gta=None, sisbov=l.sisbov_novo, manejo=l.manejo_novo,
                    nascimento=(animal.nascimento if animal is not None else None),
                    idade_meses=(round(animal.eras_dias / 30) if (animal is not None and animal.eras_dias) else None),
                    sexo=(animal.sexo if animal is not None else None), raca_codigo=(raca.codigo if raca else None),
                    motivo='REIDENTIFICACAO', data_identificacao=l.data_reidentificacao)
                db.add(pia)
                db.flush()
                registrar_item(db, id_operacao, 'tb_7002_pia', pia.id, 'INSERT', None, {'numero_pia': pia.numero_pia, 'sisbov': l.sisbov_novo})
            db.commit()
        except Exception:
            db.rollback()
            return redirect(f'{volta}&erro=gerar')
    numero = f'{numero_int:06d}'
    buffer = gerar_pdf_reidentificacao(_ctx_pdf(id_produtor, id_propriedade, numero, agora.date(), itens))
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                     download_name=f'Reidentificacao_Notificacao_{numero}.pdf')


# -------------------------------------------------------
# REIMPRIMIR a Notificacao ja gerada (PDF) - POST
# -------------------------------------------------------
@reidentificacao_consulta.route('/produtor/reidentificacao-consulta/pdf', methods=['POST'])
def consulta_pdf():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.form.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado(URL_CONSULTA_INICIAR)
    try:
        id_pedido = int(request.form.get('pedido', '') or 0)
    except ValueError:
        id_pedido = 0
    volta = f'{URL_CONSULTA_LISTA}?id_propriedade={int(id_propriedade)}'

    id_produtor = session['id_produtor']
    with get_db_produtor(id_produtor) as db:
        pedido = db.get(ReidentificacaoComBaixa, id_pedido) if id_pedido else None
        if pedido is None or pedido.id_propriedade != int(id_propriedade):
            return redirect(f'{volta}&erro=inexistente')
        itens = _itens_do_pedido(db, id_propriedade, pedido.id)
        numero, data_notificacao = f'{pedido.id:06d}', pedido.data_solicitacao

    ctx = _ctx_pdf(id_produtor, id_propriedade, numero, data_notificacao, itens)
    buffer = gerar_pdf_reidentificacao(ctx)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                     download_name=f'Reidentificacao_Notificacao_{numero}.pdf')


# -------------------------------------------------------
# MARCAR COMO ENVIADO - POST (exige Notificacao gerada)
# -------------------------------------------------------
@reidentificacao_consulta.route('/produtor/reidentificacao-consulta/enviar', methods=['POST'])
def consulta_enviar():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.form.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado(URL_CONSULTA_INICIAR)
    try:
        id_pedido = int(request.form.get('pedido', '') or 0)
    except ValueError:
        id_pedido = 0
    volta = f'{URL_CONSULTA_LISTA}?id_propriedade={int(id_propriedade)}'

    with get_db_produtor(session['id_produtor']) as db:
        pedido = db.get(ReidentificacaoComBaixa, id_pedido) if id_pedido else None
        if pedido is None or pedido.id_propriedade != int(id_propriedade):
            return redirect(f'{volta}&erro=inexistente')
        if pedido.enviado_em is not None:
            return redirect(f'{volta}&pedido={pedido.id}&erro=ja_enviado')
        if pedido.notificacao_gerada_em is None:
            return redirect(f'{volta}&pedido={pedido.id}&erro=sem_pdf')
        try:
            numero = pedido.id
            agora = datetime.now()
            pedido.enviado_em = agora
            pedido.enviado_por = session.get('usuario_id')
            id_operacao = registrar_operacao(
                db, id_usuario=session['usuario_id'], id_propriedade=int(id_propriedade),
                modulo='reidentificacao_envio',
                descricao=f'Reidentificação — Notificação {numero:06d} — marcada como enviada'[:120],
            )
            registrar_item(db, id_operacao, 'tb_6005_reidentificacao_com_baixa', numero, 'UPDATE',
                           {'enviado_em': None}, {'enviado_em': agora.isoformat(timespec='seconds')})
            db.commit()
        except Exception:
            db.rollback()
            return redirect(f'{volta}&pedido={id_pedido}&erro=inexistente')
    return redirect(f'{volta}&pedido={numero}&ok=enviado')


# -------------------------------------------------------
# EXCLUIR UM ANIMAL PENDENTE (POST) - so antes de gerar a Notificacao
# -------------------------------------------------------
@reidentificacao_consulta.route('/produtor/reidentificacao-consulta/excluir-animal', methods=['POST'])
def consulta_excluir_animal():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.form.get('id_propriedade', '')
    if not id_propriedade or not _propriedade_do_usuario(id_propriedade):
        return _negado(URL_CONSULTA_INICIAR)
    try:
        id_item = int(request.form.get('item', '') or 0)
    except ValueError:
        id_item = 0
    volta = f'{URL_CONSULTA_LISTA}?id_propriedade={int(id_propriedade)}'
    with get_db_produtor(session['id_produtor']) as db:
        try:
            ok, mensagem = excluir_animal(db, int(id_propriedade), id_item, session['usuario_id'])
            if ok:
                db.commit()
            else:
                db.rollback()
        except Exception:
            db.rollback()
            ok, mensagem = False, 'Não foi possível excluir o animal. Nada foi alterado.'
    return redirect(f'{volta}&{"ok=excluido" if ok else "erro=exclusao"}&msg={quote(mensagem)}')


# -------------------------------------------------------
# INCONFORMIDADES (tela): tentativas recusadas, da mais nova para a mais antiga
# -------------------------------------------------------
@reidentificacao_consulta.route('/produtor/reidentificacao-inconformes/iniciar')
def inconformes_iniciar():
    return _iniciar('Inconformidades da Reidentificação — Selecionar Propriedade', URL_INCONF_LISTA, URL_INCONF_INICIAR)


@reidentificacao_consulta.route('/produtor/reidentificacao-inconformes/lista')
def inconformes_lista():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado(URL_INCONF_INICIAR)

    filtro_txt = (request.args.get('data', '') or '').strip()
    filtro = _ler_data_br(filtro_txt) if filtro_txt else None
    erro = 'Data incorreta. Digite no formato dd/mm/aaaa.' if (filtro_txt and filtro is None) else None

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))

    itens_brutos = []
    total = 0
    try:
        with get_db_produtor(session['id_produtor']) as db:
            q = db.query(ReidentificacaoInconforme).filter(ReidentificacaoInconforme.id_propriedade == int(id_propriedade))
            if filtro is not None:
                q = q.filter(func.date(ReidentificacaoInconforme.criado_em) == filtro)
            total = q.count()
            linhas = q.order_by(ReidentificacaoInconforme.id.desc()).limit(LIMITE_INCONFORMES).all()
            itens_brutos = [{
                'quando': l.criado_em.strftime('%d/%m/%Y %H:%M') if l.criado_em else '',
                'sisbov_antigo': l.sisbov_antigo or '', 'sisbov_novo': l.sisbov_novo or '', 'motivo': l.motivo or '',
                'id_usuario': l.id_usuario,
            } for l in linhas]
    except Exception:
        erro = erro or 'Não foi possível consultar as Inconformidades agora. Verifique se o script do banco foi aplicado.'

    ids = {i['id_usuario'] for i in itens_brutos if i['id_usuario']}
    nomes = {}
    if ids:
        with Session(engine) as db:
            nomes = {i: n for i, n in db.query(Usuario.id, Usuario.nome).filter(Usuario.id.in_(ids)).all()}
    for i in itens_brutos:
        i['usuario'] = nomes.get(i['id_usuario'], '')

    return render_template(
        'produtor/reidentificacao_inconformes_lista.html',
        erro=erro, propriedade=propriedade, id_propriedade=id_propriedade, filtro=filtro_txt,
        itens=itens_brutos, total=total, limite=LIMITE_INCONFORMES,
        url_voltar=_url_voltar(URL_INCONF_INICIAR), **_contexto_tela(),
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\reidentificacao_consulta.py
# =========================================================
