# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\auditoria_eras.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-07 12:05 -03
# ATUALIZADO EM: 2026-10-07 12:05 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Auditorias ERAS: registro das vistorias/auditorias nas
#     Propriedades que tem codigo ERAS (plataforma Produtor).
#
#       - /produtor/auditoria-eras                        lista das fazendas
#         do usuario que tem codigo ERAS, com a situacao de cada uma.
#       - /produtor/auditoria-eras/<id_propriedade>       tela da fazenda:
#         situacao, historico completo, formulario de registro e de
#         correcao.
#       - /produtor/auditoria-eras/<id_propriedade>/salvar (POST)
#         grava uma vistoria nova ou a correcao de uma existente.
#
#     REGRAS (decisoes de Benedito, Sessao 089):
#       - Quem lanca: qualquer usuario com vinculo ativo na fazenda,
#         so em fazenda com codigo ERAS.
#       - Obrigatorios: data da vistoria, veredito da Certificadora
#         (CONFORME / NAO CONFORME), nome do vistoriador/auditor e
#         proxima data. Observacao e opcional.
#       - Vistoria nunca e apagada (nao existe rota de exclusao).
#       - Correcao pode; se a vistoria tem 60 dias ou mais, aparece o
#         alerta "pode comprometer a propriedade" e so grava depois da
#         confirmacao. Toda correcao fica em tb_log_auditoria_eras
#         (uma linha por campo: antes, depois, quem, quando).
#       - O historico e da Propriedade (schema public): nao depende do
#         Produtor, por isso nada e gravado na sessao.
#
#     SEGURANCA: toda rota confere no servidor que a Propriedade e do
#     usuario logado (buscar_pares_propriedade_produtor) e tem codigo
#     ERAS; a correcao confere ainda que a vistoria e DESSA Propriedade.
#
#     VOLTAR (Regra de Ouro #9): o parametro origem (home ou lista, padrao
#     lista) diz de onde a pessoa veio e o Voltar da tela da fazenda
#     acompanha. O Home passara origem=home (Pacote 2).
#
#     Regras de situacao (em dia / vencendo / pendente) e validacao do
#     formulario: backend/utils/auditoria_eras.py.
#
#     v1.0.0: Criacao do modulo (Sessao 089, 07/10/2026, 12:05 -03).
# =========================================================

from datetime import date, datetime

from flask import Blueprint, render_template, request, redirect, url_for, session
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, AuditoriaEras, LogAuditoriaEras
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor
from backend.utils.auditoria_eras import (
    ROTULO_VEREDITO, VEREDITO_NAO_CONFORME, SIT_EM_DIA,
    calcular_situacao, validar_dados, precisa_alerta_60, formatar_data,
    tem_codigo_eras, buscar_ultima_auditoria, buscar_historico,
)

# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
auditoria_eras = Blueprint('auditoria_eras', __name__)

URL_HOME = '/produtor/home'
URL_LISTA = '/produtor/auditoria-eras'

# Mensagens de sucesso (a URL so leva o codigo, nunca o texto)
MENSAGENS_OK = {
    'criada': 'Vistoria registrada.',
    'alterada': 'Vistoria corrigida. A correção ficou registrada no histórico de alterações.',
    'sem_mudanca': 'Nenhum dado foi alterado.',
}


# -------------------------------------------------------
# Funcao auxiliar: confere login e perfil PRODUTOR. Devolve None se
# estiver tudo certo, ou a resposta de redirecionamento pronta.
# -------------------------------------------------------
def _checar_acesso():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    perfil = session.get('usuario_perfil')
    if perfil != 'PRODUTOR':
        return redirecionar_home(perfil)
    return None


# -------------------------------------------------------
# Funcao auxiliar: de onde a pessoa veio (Voltar - Regra #9).
# -------------------------------------------------------
def _origem():
    origem = request.values.get('origem', 'lista')
    return origem if origem in ('home', 'lista') else 'lista'


def _voltar_da_fazenda(origem):
    return URL_HOME if origem == 'home' else URL_LISTA


# -------------------------------------------------------
# Funcao auxiliar: variaveis que todo render_template desta tela envia.
# -------------------------------------------------------
def _contexto_base():
    return dict(
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'auditoria_eras',
    )


# -------------------------------------------------------
# Funcao auxiliar: nome de quem registra (retrato do momento).
# -------------------------------------------------------
def _nome_do_usuario():
    nome = (session.get('usuario_nome') or '').strip()[:150]
    return nome or f"Usuário {session.get('usuario_id')}"


# -------------------------------------------------------
# Funcao auxiliar: dados da fazenda, SO se ela for do usuario logado e
# tiver codigo ERAS. Devolve dict simples ou None.
# -------------------------------------------------------
def _dados_fazenda(db, id_propriedade):
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if int(id_propriedade) not in {int(p.id_propriedade) for p in pares}:
        return None

    propriedade = db.get(Propriedade, id_propriedade)
    if propriedade is None or not tem_codigo_eras(propriedade.codigo_eras):
        return None

    return {
        'id_propriedade': propriedade.id,
        'nome': propriedade.nome,
        'codigo_eras': propriedade.codigo_eras.strip(),
        'uf': propriedade.uf,
    }


# -------------------------------------------------------
# Funcao auxiliar: monta a linha de uma vistoria para a tela
# (so valores simples, prontos para o template).
# -------------------------------------------------------
def _item_historico(a, hoje):
    return {
        'id': a.id,
        'data_vistoria': formatar_data(a.data_vistoria),
        'veredito': a.veredito,
        'veredito_rotulo': ROTULO_VEREDITO.get(a.veredito, a.veredito),
        'nao_conforme': a.veredito == VEREDITO_NAO_CONFORME,
        'vistoriador': a.vistoriador,
        'proxima_data': formatar_data(a.proxima_data),
        'observacao': a.observacao or '',
        'registrado_por': a.usuario_nome,
        'registrado_em': a.criado_em.strftime('%d/%m/%Y %H:%M') if a.criado_em else '',
        'corrigido_em': a.atualizado_em.strftime('%d/%m/%Y %H:%M') if a.atualizado_em else '',
        'antiga_60': precisa_alerta_60(a.data_vistoria, hoje),
    }


# -------------------------------------------------------
# Funcao auxiliar: valores do formulario a partir de uma vistoria
# (modo correcao). Datas no formato aaaa-mm-dd do campo de data.
# -------------------------------------------------------
def _form_da_vistoria(a):
    return {
        'data_vistoria': a.data_vistoria.strftime('%Y-%m-%d'),
        'veredito': a.veredito,
        'vistoriador': a.vistoriador,
        'proxima_data': a.proxima_data.strftime('%Y-%m-%d'),
        'observacao': a.observacao or '',
    }


FORM_VAZIO = {'data_vistoria': '', 'veredito': '', 'vistoriador': '', 'proxima_data': '', 'observacao': ''}


# -------------------------------------------------------
# Rota: /produtor/auditoria-eras - lista das fazendas com ERAS
# -------------------------------------------------------
@auditoria_eras.route('/produtor/auditoria-eras')
def lista():
    bloqueio = _checar_acesso()
    if bloqueio:
        return bloqueio

    hoje = date.today()
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    # Uma linha por Propriedade (a mesma fazenda com 2 Produtores vira 1).
    ids = sorted({int(p.id_propriedade) for p in pares})

    fazendas = []
    qtd_sem_eras = 0

    with Session(engine) as db:
        for id_propriedade in ids:
            propriedade = db.get(Propriedade, id_propriedade)
            if propriedade is None:
                continue
            if not tem_codigo_eras(propriedade.codigo_eras):
                qtd_sem_eras += 1
                continue

            ultima = buscar_ultima_auditoria(db, id_propriedade)
            situacao = calcular_situacao(ultima, hoje)
            fazendas.append({
                'id_propriedade': propriedade.id,
                'nome': propriedade.nome,
                'codigo_eras': propriedade.codigo_eras.strip(),
                'ultima_data': formatar_data(ultima.data_vistoria) if ultima else '',
                'ultimo_veredito': ROTULO_VEREDITO.get(ultima.veredito, '') if ultima else '',
                'nao_conforme': (ultima.veredito == VEREDITO_NAO_CONFORME) if ultima else False,
                'proxima_data': formatar_data(ultima.proxima_data) if ultima else '',
                'situacao_codigo': situacao['codigo'],
                'situacao_texto': situacao['texto'],
            })

    fazendas.sort(key=lambda f: (f['nome'] or '').upper())

    return render_template('produtor/auditoria_eras_lista.html',
        fazendas     = fazendas,
        qtd_sem_eras = qtd_sem_eras,
        voltar       = URL_HOME,
        **_contexto_base()
    )


# -------------------------------------------------------
# Funcao auxiliar: monta e devolve a tela da fazenda. Usada pelo GET
# e pelo POST (quando ha erro ou pedido de confirmacao dos 60 dias).
# Devolve a resposta pronta, ou redireciona para a lista se a
# fazenda nao for do usuario / nao tiver ERAS.
# -------------------------------------------------------
def _tela_fazenda(id_propriedade, origem, form=None, editar_id=None, erro=None, aviso_60=False, ok=None):
    hoje = date.today()

    with Session(engine) as db:
        fazenda = _dados_fazenda(db, id_propriedade)
        if fazenda is None:
            return redirect(url_for('auditoria_eras.lista'))

        historico = buscar_historico(db, id_propriedade)
        situacao = calcular_situacao(historico[0] if historico else None, hoje)
        itens = [_item_historico(a, hoje) for a in historico]

        # Modo correcao: carrega os dados da vistoria escolhida (so se
        # ela for DESTA fazenda).
        vistoria_em_correcao = None
        for a in historico:
            if editar_id is not None and a.id == editar_id:
                vistoria_em_correcao = a
                break
        if vistoria_em_correcao is None:
            editar_id = None
        elif form is None:
            form = _form_da_vistoria(vistoria_em_correcao)
        data_em_correcao = formatar_data(vistoria_em_correcao.data_vistoria) if vistoria_em_correcao else ''

    return render_template('produtor/auditoria_eras_fazenda.html',
        fazenda          = fazenda,
        situacao         = situacao,
        historico        = itens,
        form             = form or dict(FORM_VAZIO),
        editar_id        = editar_id,
        data_em_correcao = data_em_correcao,
        aviso_60         = aviso_60,
        erro             = erro,
        mensagem_ok      = MENSAGENS_OK.get(ok),
        origem           = origem,
        voltar           = _voltar_da_fazenda(origem),
        hoje_iso         = hoje.strftime('%Y-%m-%d'),
        **_contexto_base()
    )


# -------------------------------------------------------
# Rota: /produtor/auditoria-eras/<id_propriedade> - tela da fazenda
# -------------------------------------------------------
@auditoria_eras.route('/produtor/auditoria-eras/<int:id_propriedade>')
def fazenda(id_propriedade):
    bloqueio = _checar_acesso()
    if bloqueio:
        return bloqueio

    return _tela_fazenda(
        id_propriedade,
        origem    = _origem(),
        editar_id = request.args.get('editar', type=int),
        ok        = request.args.get('ok'),
    )


# -------------------------------------------------------
# Rota: /produtor/auditoria-eras/<id_propriedade>/salvar (POST)
# Grava uma vistoria nova (sem id_auditoria) ou a correcao de uma
# existente (com id_auditoria). Nunca apaga nada.
# -------------------------------------------------------
@auditoria_eras.route('/produtor/auditoria-eras/<int:id_propriedade>/salvar', methods=['POST'])
def salvar(id_propriedade):
    bloqueio = _checar_acesso()
    if bloqueio:
        return bloqueio

    origem = _origem()
    hoje = date.today()
    id_auditoria = request.form.get('id_auditoria', type=int)
    confirmou_60 = request.form.get('confirmar_60') == '1'

    form = {campo: request.form.get(campo, '') for campo in FORM_VAZIO}

    # 1) A fazenda e do usuario e tem ERAS?
    with Session(engine) as db:
        if _dados_fazenda(db, id_propriedade) is None:
            return redirect(url_for('auditoria_eras.lista'))

    # 2) Dados corretos? (para no primeiro problema e reexibe o formulario)
    dados, erro = validar_dados(
        form['data_vistoria'], form['veredito'], form['vistoriador'],
        form['proxima_data'], form['observacao'], hoje,
    )
    if erro:
        return _tela_fazenda(id_propriedade, origem, form=form, editar_id=id_auditoria, erro=erro)

    # 3) Grava
    resultado = None
    pedir_confirmacao = False

    with Session(engine) as db:
        if id_auditoria is None:
            # ---- Vistoria nova ----
            db.add(AuditoriaEras(
                id_propriedade = id_propriedade,
                data_vistoria  = dados['data_vistoria'],
                veredito       = dados['veredito'],
                vistoriador    = dados['vistoriador'],
                proxima_data   = dados['proxima_data'],
                observacao     = dados['observacao'],
                id_usuario     = session['usuario_id'],
                usuario_nome   = _nome_do_usuario(),
            ))
            db.commit()
            resultado = 'criada'
        else:
            # ---- Correcao de vistoria existente ----
            registro = db.get(AuditoriaEras, id_auditoria)
            if registro is None or registro.id_propriedade != id_propriedade:
                return redirect(url_for('auditoria_eras.fazenda', id_propriedade=id_propriedade, origem=origem))

            if precisa_alerta_60(registro.data_vistoria, hoje) and not confirmou_60:
                pedir_confirmacao = True
            else:
                alterou_alerta = precisa_alerta_60(registro.data_vistoria, hoje)
                mudancas = _comparar(registro, dados)
                if not mudancas:
                    resultado = 'sem_mudanca'
                else:
                    agora = datetime.now()
                    for campo, antes, depois in mudancas:
                        db.add(LogAuditoriaEras(
                            id_auditoria        = registro.id,
                            id_usuario          = session['usuario_id'],
                            usuario_nome        = _nome_do_usuario(),
                            campo_alterado      = campo,
                            valor_anterior      = antes,
                            valor_novo          = depois,
                            confirmou_alerta_60 = alterou_alerta,
                            alterado_em         = agora,
                        ))
                    registro.data_vistoria = dados['data_vistoria']
                    registro.veredito      = dados['veredito']
                    registro.vistoriador   = dados['vistoriador']
                    registro.proxima_data  = dados['proxima_data']
                    registro.observacao    = dados['observacao']
                    registro.atualizado_em = agora
                    db.commit()
                    resultado = 'alterada'

    # 4) Resposta (nada do banco e lido depois do commit)
    if pedir_confirmacao:
        return _tela_fazenda(id_propriedade, origem, form=form, editar_id=id_auditoria, aviso_60=True)

    return redirect(url_for('auditoria_eras.fazenda', id_propriedade=id_propriedade, origem=origem, ok=resultado))


# -------------------------------------------------------
# Funcao auxiliar: compara a vistoria gravada com os dados novos e
# devolve a lista (campo, antes, depois) so do que MUDOU, em texto.
# -------------------------------------------------------
def _comparar(registro, dados):
    pares = [
        ('Data da vistoria',    formatar_data(registro.data_vistoria),   formatar_data(dados['data_vistoria'])),
        ('Veredito',            ROTULO_VEREDITO.get(registro.veredito),  ROTULO_VEREDITO.get(dados['veredito'])),
        ('Vistoriador/auditor', registro.vistoriador,                    dados['vistoriador']),
        ('Próxima vistoria',    formatar_data(registro.proxima_data),    formatar_data(dados['proxima_data'])),
        ('Observação',          registro.observacao or '',               dados['observacao'] or ''),
    ]
    return [(campo, antes, depois) for campo, antes, depois in pares if antes != depois]

# =========================================================
# FIM DE ARQUIVO: backend\routers\auditoria_eras.py
# =========================================================
