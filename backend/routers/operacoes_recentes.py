# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\operacoes_recentes.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-03 15:30 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.6.0
# v1.6.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Modulo GENERICO "Operacoes Recentes" - tela central onde o
#     Usuario pode ENCONTRAR e desfazer qualquer operacao feita nas
#     ultimas 24h (mecanismo Log de Operacoes, backend/utils/
#     log_operacoes.py), independente de qual modulo a gerou.
#
#     Nasce dentro do novo Hub de Utilitarios (hubs.py, slug
#     'utilitarios') - card unico por enquanto, mas o Hub fica
#     pronto para receber outros utilitarios no futuro.
#
#     PROBLEMA REAL QUE ESTE MODULO RESOLVE (Benedito, Sessao 045,
#     retomada de tarde): o botao "Desfazer" que existia so na tela
#     de resultado do Cancelamento de Brincos so ajudava a corrigir
#     o erro NAQUELE EXATO MOMENTO - se o Usuario saisse da tela e so
#     percebesse o erro depois (mesmo ainda dentro da janela de 24h),
#     nao havia como voltar e desfazer. Esta tela e o "achador" de
#     operacoes que falta para a janela de 24h fazer sentido de
#     verdade.
#
#     A rota /desfazer, que antes vivia dentro de
#     brincos_cancelamento.py (v1.3.0), MUDOU PARA CA nesta versao -
#     agora e compartilhada por QUALQUER modulo que gere operacoes no
#     Log (nao so o Cancelamento). O botao "Desfazer" da tela de
#     resultado do Cancelamento continua existindo, so passou a
#     apontar para esta rota generica em vez de uma copia propria
#     (ver brincos_cancelamento.py v1.4.0 e
#     brincos_cancelamento_resultado.html v1.3.0).
#
#     Fluxo de 3 rotas:
#       1. /produtor/operacoes-recentes/iniciar - resolve
#          Propriedade E Produtor (PADRAO REUTILIZAVEL No1).
#       2. /produtor/operacoes-recentes/lista?id_propriedade=X - lista
#          as operacoes daquela Propriedade que ainda podem ser
#          desfeitas (desfeito_em IS NULL E dentro das 24h), mais
#          recentes primeiro. Cada linha mostra descricao, quem fez,
#          quando, e um botao Desfazer - HABILITADO so se o Usuario
#          logado tem permissao (fez a operacao OU tem Cargo
#          TITULAR/ADMINISTRADOR/ADMINISTRATIVO), mesma regra de
#          backend/utils/log_operacoes.py.
#       3. /produtor/operacoes-recentes/desfazer (POST) - MOVIDA de
#          brincos_cancelamento.py nesta versao. Confere permissao +
#          janela de 24h + conflito (nessa ordem) antes de reverter -
#          bloqueia com aviso claro se qualquer checagem falhar.
#
#     v1.0.0: Criacao do modulo (Sessao 045, 03/09/2026, 15:30 -03),
#         a partir do gap de UX identificado por Benedito em teste
#         real (o botao Desfazer so existia num lugar de cada vez).
#     v1.1.0: Sessao 051 (13/09/2026, 12:30 -03) - BUG REAL de UX
#         reportado por Benedito, testado em producao: a tela
#         "Selecionar Propriedade" (template compartilhado
#         selecionar_propriedade_produtor.html) exibia titulo
#         generico demais ('Selecionar Propriedade'), sem dizer de
#         qual modulo o fluxo tinha partido - usuario clicava em
#         "Operações Recentes" no Hub de Utilitarios e chegava numa
#         tela sem nenhuma referencia a Operacoes Recentes, ficando
#         perdido. Corrigido nas 2 chamadas de render_template()
#         desta funcao iniciar() (fluxo com erro e fluxo normal):
#         titulo agora e 'Operações Recentes — Selecionar
#         Propriedade', seguindo o mesmo padrao ja usado em
#         gta_consulta.py ('Consulta de GTAs — Selecionar
#         Propriedade'). O parametro 'voltar' ja estava correto
#         desde a v1.0.0 (nao precisou mudar). Ver template
#         selecionar_propriedade_produtor.html v1.2.0 para a
#         REGRA DE OURO nova, documentada no cabecalho dele,
#         valendo para todo modulo futuro que use esta tela.
#     v1.2.0: Sessao 091 (08/10/2026, 20:00 -03) - FAZENDA EM USO (Regra de Ouro #13):
#         Com fazenda em uso a tela "Selecionar Propriedade" e pulada (iniciar()
#         abre direto a lista da fazenda). Voltar vai ao Hub de Utilitarios, sem passar
#         pela selecao. TRAVA na lista: Propriedade da URL diferente da fazenda em uso
#         volta ao iniciar() (o log e filtrado por Propriedade). Desfazer, leitura e
#         gravacao intactos. REVERSAO: devolver a versao anterior.
#     v1.3.0: Sessao 092 (09/10/2026, 17:35 -03) - BLOCKCHAIN: no /desfazer, depois das
#         checagens e antes de reverter, chama blockchain.tratar_desfazer():
#         o evento da operacao que ainda nao saiu e CANCELADO; o que ja saiu
#         gera um evento de ESTORNO. Nunca bloqueia o Desfazer (erro vai para
#         o log). Nenhuma outra mudanca.
#     v1.4.0: Sessao 094 (12/10/2026, 19:10 -03) - BLOQUEIO ANTES DE CONFIRMAR: a lista passa a
#         rodar as mesmas checagens do /desfazer (buscar_operacao_desfazivel + verificar_conflitos)
#         para cada operacao e manda o motivo (op.bloqueio) para a tela, que o mostra na linha e
#         avisa ao clicar - sem pedir "Tem certeza?" para algo que vai ser recusado. O /desfazer
#         continua checando tudo de novo (a lista so antecipa o aviso). REVERSAO: devolver
#         operacoes_recentes.py.bak_antes_bloqueio.
#     v1.5.0: Sessao 104 (23/10/2026, 10:15 -03) - DESFAZER SO O QUE NAO COMPROMETE (decisao de Benedito): a lista mostra com botao SO a operacao que ainda pode ser
#         desfeita (regras do log_operacoes.py 1.16.0); o que ficou comprometido some; o historico (modulos so-historico e operacoes sem permissao) aparece
#         numa segunda lista, sem botao. O /desfazer continua conferindo tudo de novo. Precisa do log_operacoes.py 1.16.0 e do operacoes_recentes_lista.html 1.5.0.
#         REVERSAO: .bak_antes_s104e.
# =========================================================

from types import SimpleNamespace
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, session
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, Produtor, Usuario
from backend.models.tb_log_operacoes import LogOperacao
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.blockchain import tratar_desfazer
from backend.utils.log_operacoes import (
    CARGOS_PERMITIDOS,
    JANELA_DESFAZER_HORAS,
    MODULOS_SO_HISTORICO,   # v1.5.0
    buscar_operacao_desfazivel,
    verificar_conflitos,
    executar_desfazer,
)


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
operacoes_recentes = Blueprint('operacoes_recentes', __name__)


# -------------------------------------------------------
# v1.2.0 - TRAVA DA FAZENDA EM USO (Regra de Ouro #13): a Propriedade da URL
# difere da fazenda em uso (trocada em outra aba)? Sem fazenda em uso, ou
# valor que nao e numero, devolve False.
# -------------------------------------------------------
def _fora_da_fazenda_em_uso(id_propriedade):
    try:
        id_int = int(id_propriedade)
    except (TypeError, ValueError):
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares)
    return par_em_uso is not None and int(par_em_uso.id_propriedade) != id_int


# -------------------------------------------------------
# v1.5.2 - Desfazer SO da fazenda em uso (decisao do Benedito, 12/11/2026: cada fazenda tem o seu Titular/
# Administrador). True = a operacao NAO e de uma Propriedade do usuario neste Produtor, ou e de outra fazenda
# que nao a fazenda em uso.
# -------------------------------------------------------
def _operacao_fora_da_fazenda(id_propriedade):
    try:
        id_int = int(id_propriedade)
    except (TypeError, ValueError):
        return True
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    ids_do_produtor = {int(p.id_propriedade) for p in pares if int(p.id_produtor) == int(session['id_produtor'])}
    if id_int not in ids_do_produtor:
        return True
    par_em_uso = resolver_fazenda_em_uso(pares)
    return par_em_uso is not None and int(par_em_uso.id_propriedade) != id_int


# -------------------------------------------------------
# Funcao auxiliar: busca os dados de cabecalho (Propriedade +
# Produtor vinculado) - copia curta local (PADRAO REUTILIZAVEL
# No1), mesma usada em todos os modulos do Hub de Brincos.
# -------------------------------------------------------
def _buscar_dados_cabecalho(id_produtor, id_propriedade):
    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade)) if id_propriedade else None
        produtor    = db.get(Produtor, int(id_produtor)) if id_produtor else None

        if not propriedade or not produtor:
            return None

        return SimpleNamespace(
            propriedade_nome = propriedade.nome,
            municipio        = propriedade.municipio,
            uf               = propriedade.uf,
            produtor_nome    = produtor.nome,
        )


# -------------------------------------------------------
# Funcao auxiliar: calcula a URL de "Voltar" pos-selecao (Regra de
# Ouro No4), mesma logica ja fechada nos demais modulos.
# -------------------------------------------------------
def _url_voltar_pos_selecao():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return '/produtor/operacoes-recentes/iniciar'
    return '/produtor/hub/utilitarios'


# -------------------------------------------------------
# Funcao auxiliar: dict {id_usuario: nome}, 1 query so (evita N+1
# ao montar a lista de operacoes) - mesmo padrao ja usado em
# _mapa_fabricantes() (brincos_disponiveis.py).
# -------------------------------------------------------
def _mapa_usuarios(ids_usuario):
    if not ids_usuario:
        return {}
    with Session(engine) as db:
        usuarios = db.query(Usuario).filter(Usuario.id.in_(ids_usuario)).all()
        return {u.id: u.nome for u in usuarios}


# -------------------------------------------------------
# Rota: GET /produtor/operacoes-recentes/iniciar - ponto de
# partida, MESMO padrao ja usado em todos os modulos do Hub de
# Brincos (PADRAO REUTILIZAVEL No1).
# -------------------------------------------------------
@operacoes_recentes.route('/produtor/operacoes-recentes/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            # v1.1.0: titulo com prefixo do modulo (Regra de Ouro
            # nova - ver selecionar_propriedade_produtor.html v1.2.0).
            titulo='Operações Recentes — Selecionar Propriedade',
            proximo='/produtor/operacoes-recentes/lista',
            campo_propriedade='id_propriedade',
            voltar='/produtor/hub/utilitarios',
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='utilitarios',
        )

    # v1.2.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/operacoes-recentes/lista?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/operacoes-recentes/lista?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        # v1.1.0: titulo com prefixo do modulo (Regra de Ouro nova -
        # ver selecionar_propriedade_produtor.html v1.2.0).
        titulo='Operações Recentes — Selecionar Propriedade',
        proximo='/produtor/operacoes-recentes/lista',
        campo_propriedade='id_propriedade',
        voltar='/produtor/hub/utilitarios',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='utilitarios',
    )


# -------------------------------------------------------
# Rota: GET /produtor/operacoes-recentes/lista?id_propriedade=X -
# lista as operacoes daquela Propriedade ainda desfazivel (nao
# desfeitas, dentro das 24h), mais recente primeiro.
# -------------------------------------------------------
@operacoes_recentes.route('/produtor/operacoes-recentes/lista')
def lista():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if _fora_da_fazenda_em_uso(id_propriedade):
        return redirect('/produtor/operacoes-recentes/iniciar')
    if not id_propriedade:
        return 'Propriedade não informada. Reinicie o fluxo pelo Hub de Utilitários.', 400

    cabecalho = _buscar_dados_cabecalho(session['id_produtor'], id_propriedade)
    if cabecalho is None:
        return 'Propriedade ou Produtor não encontrado(s). Reinicie o fluxo pelo Hub de Utilitários.', 400

    limite_janela = datetime.now() - timedelta(hours=JANELA_DESFAZER_HORAS)

    with get_db_produtor(session['id_produtor']) as db:
        operacoes_db = (
            db.query(LogOperacao)
            .filter_by(id_propriedade=int(id_propriedade))
            .filter(LogOperacao.desfeito_em.is_(None))
            .filter(LogOperacao.criado_em >= limite_janela)
            .order_by(LogOperacao.criado_em.desc())
            .all()
        )

        mapa_usuarios = _mapa_usuarios([op.id_usuario for op in operacoes_db])

        cargo_logado = session.get('usuario_cargo', '')
        id_usuario_logado = session['usuario_id']

        # v1.5.0 - DESFAZER SO O QUE NAO COMPROMETE (decisao de Benedito, S104):
        #   operacoes      = o que ainda pode ser desfeito agora (com botao);
        #   historico      = so consulta (modulos so-historico ou sem permissao), sem botao;
        #   o resto (algo foi feito depois, conflito, prazo) SOME da lista.
#     v1.5.1: Sessao 122 (2026-11-12 13:55 -03) - Auditoria Etapa 1: id da operacao validado (texto dava 500); trava de linha no Desfazer; arquivos das fotos da Morte apagados depois do commit. REVERSAO: .bak_antes_s122_etapa1.
#     v1.5.2: Sessao 122 (2026-11-12 14:10 -03) - Auditoria Etapa 1, item 2 (decisao do Benedito): o Desfazer so vale para operacao da FAZENDA EM USO (e de Propriedade do usuario neste Produtor); outra fazenda mostra aviso. REVERSAO: .bak_antes_s122_item2.
#     v1.5.3: Sessao 122 (2026-11-12 14:25 -03) - Auditoria Etapa 1: operacao nao informada/invalida agora abre a tela padrao com orientacao (antes: texto solto). REVERSAO: .bak_antes_s122_msgs.
        operacoes = []
        historico = []
        for op in operacoes_db:
            pode_desfazer = (
                op.id_usuario == id_usuario_logado
                or (cargo_logado or '').upper() in CARGOS_PERMITIDOS
            )
            linha = SimpleNamespace(
                id=op.id,
                descricao=op.descricao,
                usuario_nome=mapa_usuarios.get(op.id_usuario, '-'),
                criado_em=op.criado_em.strftime('%d/%m/%Y %H:%M'),
                pode_desfazer=pode_desfazer,
                bloqueio=None,
            )
            if op.modulo in MODULOS_SO_HISTORICO or not pode_desfazer:
                historico.append(linha)
                continue
            _, itens_op, erro_op = buscar_operacao_desfazivel(
                db, op.id, id_usuario_logado, cargo_logado
            )
            if erro_op:
                continue   # compromete o que veio depois (ou prazo): some da lista
            if verificar_conflitos(db, itens_op):
                continue   # algo mudou depois: some da lista
            operacoes.append(linha)

    return render_template(
        'produtor/operacoes_recentes_lista.html',
        cabecalho=cabecalho,
        id_propriedade=id_propriedade,
        operacoes=operacoes,
        historico=historico,   # v1.5.0
        janela_horas=JANELA_DESFAZER_HORAS,
        url_voltar=_url_voltar_pos_selecao(),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='utilitarios',
    )


# -------------------------------------------------------
# Rota: POST /produtor/operacoes-recentes/desfazer - MOVIDA de
# brincos_cancelamento.py nesta versao (agora generica, usada por
# qualquer modulo que gere operacoes no Log). Confere, NESSA ORDEM:
# (1) permissao + janela de 24h + se ja foi desfeita
# (buscar_operacao_desfazivel), (2) conflito - algo mudou depois
# (verificar_conflitos). Se QUALQUER checagem falhar, bloqueia com
# aviso claro e NAO desfaz nada (nunca parcial).
# -------------------------------------------------------
@operacoes_recentes.route('/produtor/operacoes-recentes/desfazer', methods=['POST'])
def desfazer():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_operacao_str = request.form.get('id_operacao', '')
    # Para onde "Voltar" apos o resultado - opcional, cai no Hub de
    # Utilitarios se o chamador nao informar.
    url_origem = request.form.get('url_origem', '/produtor/hub/utilitarios')

    if not id_operacao_str or not id_operacao_str.isdecimal():   # v1.5.1/v1.5.3 - sem id ou id com texto: pagina com orientacao (antes: texto solto / erro 500)
        return render_template(
            'produtor/operacoes_recentes_desfeito.html',
            sucesso=False,
            mensagem='Não foi possível identificar qual operação desfazer. Volte para a lista de Operações Recentes e clique em Desfazer de novo. Se repetir, avise a Consiste.',
            url_voltar=url_origem,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='utilitarios',
        )

    with get_db_produtor(session['id_produtor']) as db:
        operacao, itens, erro = buscar_operacao_desfazivel(
            db, int(id_operacao_str), session['usuario_id'], session.get('usuario_cargo'), travar=True
        )

        if erro:
            return render_template(
                'produtor/operacoes_recentes_desfeito.html',
                sucesso=False,
                mensagem=erro,
                url_voltar=url_origem,
                usuario_nome=session.get('usuario_nome'),
                usuario_perfil=session.get('usuario_perfil'),
                cor_primaria=session.get('cor_primaria', '#D4370A'),
                nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
                menu_ativo='utilitarios',
            )

        if _operacao_fora_da_fazenda(operacao.id_propriedade):   # v1.5.2
            return render_template(
                'produtor/operacoes_recentes_desfeito.html',
                sucesso=False,
                mensagem='Esta operação é de outra fazenda. Selecione aquela fazenda no Home para poder desfazê-la.',
                url_voltar=url_origem,
                usuario_nome=session.get('usuario_nome'),
                usuario_perfil=session.get('usuario_perfil'),
                cor_primaria=session.get('cor_primaria', '#D4370A'),
                nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
                menu_ativo='utilitarios',
            )

        conflitos = verificar_conflitos(db, itens)
        if conflitos:
            return render_template(
                'produtor/operacoes_recentes_desfeito.html',
                sucesso=False,
                mensagem='Não foi possível desfazer — algo mudou depois desta operação:',
                conflitos=conflitos,
                url_voltar=url_origem,
                usuario_nome=session.get('usuario_nome'),
                usuario_perfil=session.get('usuario_perfil'),
                cor_primaria=session.get('cor_primaria', '#D4370A'),
                nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
                menu_ativo='utilitarios',
            )

        tratar_desfazer(db, operacao.id, session['usuario_id'])   # v1.3.0 - blockchain
        nomes_fotos = executar_desfazer(db, operacao, itens, session['usuario_id'])
        db.commit()
        if nomes_fotos:   # v1.5.1 - arquivos das fotos da Morte so saem DEPOIS do commit
            try:
                from backend.utils.morte_fotos import apagar_arquivos_das_fotos
                apagar_arquivos_das_fotos(nomes_fotos)
            except Exception as e:
                print(f'AVISO: Desfazer feito, mas nao apagou os arquivos das fotos: {e}')

    return render_template(
        'produtor/operacoes_recentes_desfeito.html',
        sucesso=True,
        mensagem='Operação desfeita com sucesso.',
        url_voltar=url_origem,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='utilitarios',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\operacoes_recentes.py
# =========================================================