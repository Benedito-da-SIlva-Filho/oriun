# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\backup_restore.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-04 13:40 -03
# ATUALIZADO EM: 2026-11-16 09:25 -03
# VERSAO: 1.11.0
# v1.11.0: Sessao 128 (2026-11-16 09:25 -03) - AUDITORIA ETAPA 7 (varredura de id_propriedade, Regra #73): a Propriedade vinda da URL/formulario nas telas Backup, Criar e Solicitar Restore so e repassada (Voltar, Caixa de Sucesso) se for numero E do usuario; senao e descartada, sem erro. Funcao nova _id_propriedade_para_tela(). REVERSAO: .bak_antes_etapa7a.
# v1.10.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (4 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Rotas do mecanismo de Backup/Restore de Schema inteiro.
#     Ver v1.3.0 para a descricao completa das rotas LADO
#     PRODUTOR e LADO CONSISTE (inalteradas nesta versao).
#
#     v1.0.0 a v1.3.0: ver historico no cabecalho anterior deste
#         arquivo (Sessao 046).
#     v1.4.0: Sessao 049 (10/09/2026, 17:30 -03) - consiste_
#         executar() passa a tratar VersaoSchemaIncompativel
#         (backup_helper.py v1.3.0): se o backup escolhido for de
#         uma versao de estrutura diferente da atual, NAO restaura
#         direto - reexibe uma tela de confirmacao explicita
#         (consiste/consiste_confirmar_versao.html), exigindo um
#         checkbox marcado antes de tentar de novo com
#         confirmar_versao_incompativel=on. Decisao de Benedito:
#         nunca bloquear a operacao legitima de restaurar backup
#         antigo, mas nunca deixar passar batido sem a Consiste
#         perceber - quem aciona o Restore de verdade e sempre a
#         Consiste (nunca o Produtor), entao a protecao mora aqui.
#     v1.5.0: Sessao 051 (13/09/2026, 12:30 -03) - DUAS correcoes
#         de UX na funcao iniciar() (fluxo com erro e fluxo
#         normal), mesmo bug relatado por Benedito em Operacoes
#         Recentes:
#         (1) titulo generico 'Selecionar Propriedade' trocado por
#             'Backup e Restore — Selecionar Propriedade', seguindo
#             a Regra de Ouro nova documentada em
#             selecionar_propriedade_produtor.html v1.2.0.
#         (2) FALTAVA o parametro 'voltar' nas 2 chamadas de
#             render_template() - o botao "Voltar" desta tela
#             levava sempre para a Home em vez do Hub de
#             Utilitarios. Corrigido com voltar='/produtor/hub/
#             utilitarios' nas 2 chamadas. Nenhuma outra rota deste
#             arquivo foi alterada.
#     v1.5.1: Sessao 080 (25/09/2026, 10:05 -03) - LIMPEZA DE
#         ARQUIVO CONTAMINADO (achado em varredura por "pia" nos
#         routers): depois do rodape "FIM DE ARQUIVO" havia uma
#         COPIA INTEIRA do vincular_gta.py v1.0.0 (22/09) colada no
#         mesmo arquivo - cerca de 600 linhas de codigo morto
#         (o blueprint 'vincular_gta' copiado aqui nunca foi
#         registrado no app.py, por isso nada quebrou; o Vincular
#         GTA real continua em vincular_gta.py). Todo esse bloco
#         foi REMOVIDO. Tambem: mensagem "Data selecionada e
#         invalida" -> "incorreta" (Regras.txt secao 4). NENHUMA
#         mudanca de logica no Backup/Restore.
#     v1.6.0: Sessao 091 (08/10/2026, 20:00 -03) - FAZENDA EM USO (Regra de Ouro #13):
#         Com fazenda em uso a tela "Selecionar Propriedade" e pulada (iniciar()
#         abre direto a tela do Backup). O Backup e do produtor INTEIRO (schema todo),
#         por isso NAO ha trava por Propriedade. Voltar da tela principal vai ao Hub de
#         Utilitarios (sem parametros na URL). Criar backup e pedido de restore
#         intactos. REVERSAO: devolver a versao anterior.
#     v1.7.0: Sessao 091 (08/10/2026, 20:15 -03) - MENSAGEM DE RESULTADO (pedido de
#         Benedito: o backup era gravado certo mas a tela ficava muda e o
#         usuario esperava um aviso). criar() agora avisa: sucesso (com data e
#         hora), erro ao fazer o backup e falta de permissao; o envio do pedido
#         de restore tambem avisa. Usa flash (aparece uma vez so, nao repete ao
#         atualizar a pagina); tela_principal() entrega a mensagem ao template
#         (backup_principal.html v1.3.0). Nenhuma regra de backup mudou.
#     v1.8.0: Sessao 097 (15/10/2026, 13:40 -03) - ETAPA 4 (permissoes): as 3 checagens de cargo avulsas (criar backup, abrir e
#         enviar pedido de restore) sairam; o porteiro (Utilitarios, nivel Tudo) decide. O botao
#         da tela usa caminho_permitido. REVERSAO: devolver a versao anterior (.bak_antes_etapa4_s097).
#     v1.9.0: Sessao 104 (23/10/2026, 08:50 -03) - CAIXA DE SUCESSO (Padrao No7): depois de Fazer Backup e depois de Enviar o pedido de restauracao
#         o usuario ve a tela de conclusao (rotas GET /produtor/backup/concluido e /produtor/backup/pedido-enviado; o resumo vai pela sessao e
#         aparece uma vez so) em vez da faixa verde na tela de Backup. A faixa vermelha de ERRO continua (flash backup_erro). Nenhuma regra de
#         backup/restore mudou. Precisa do caixa_sucesso.py 1.1.0 e do backup_principal.html 1.4.0.  REVERSAO: .bak_antes_s104 (router e tela).
#     v1.9.1: Sessao 104 (23/10/2026, 09:40 -03) - as 4 telas que listam backups (Backup, pedir restauracao, reexibicao com erro e o lado Consiste)
#         passam a usar listar_backups_validos(): backup com mais de 30 dias nao aparece nem pode ser escolhido. Precisa do backup_helper.py 1.7.0.
#         REVERSAO: .bak_antes_s104c.
#     v1.9.2: Sessao 104 (23/10/2026, 10:00 -03) - LISTA DE PEDIDOS de restauracao (decisao de Benedito): pedido PENDENTE aparece sempre; pedido ja
#         ATENDIDO ou EXPIRADO so aparece no dia em que foi atendido/expirou. Nenhuma outra mudanca. REVERSAO: .bak_antes_s104d.
# =========================================================

from datetime import datetime, timedelta
from types import SimpleNamespace
from flask import Blueprint, render_template, request, redirect, session, flash, get_flashed_messages

from backend.database import engine
from backend.models import Produtor, Usuario
from backend.models.tb_backup_restore_pedido import BackupRestorePedido
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.permissoes import caminho_permitido
from backend.utils.multitenant import get_db_produtor
from backend.utils.caixa_sucesso import render_caixa_sucesso   # v1.9.0 - Padrao No7
from backend.utils.backup_helper import (
    criar_backup,
    listar_backups_validos,   # v1.9.1
    executar_restore,
    BackupNaoEncontrado,
    ErroBackup,
    ErroRestore,
    ExecutavelPostgresNaoEncontrado,
    VersaoSchemaIncompativel,
)
from sqlalchemy.orm import Session


backup_restore = Blueprint('backup_restore', __name__)

# v1.8.0 - quem faz backup/pede restore vem do PORTEIRO (modulo Utilitarios, nivel Tudo).
DIAS_PARA_EXPIRAR_PEDIDO = 7

# v1.9.0 - Caixa de Sucesso (Padrao No7)
URL_BACKUP_CONCLUIDO = '/produtor/backup/concluido'
URL_PEDIDO_ENVIADO   = '/produtor/backup/pedido-enviado'
CHAVE_SUCESSO_SESSAO = 'backup_sucesso'   # resumo da Caixa de Sucesso (1 vez)


def _expirar_pedidos_antigos(db):
    limite = datetime.now() - timedelta(days=DIAS_PARA_EXPIRAR_PEDIDO)

    pedidos_vencidos = db.query(BackupRestorePedido).filter(
        BackupRestorePedido.atendido_em.is_(None),
        BackupRestorePedido.expirado_em.is_(None),
        BackupRestorePedido.criado_em < limite,
    ).all()

    if pedidos_vencidos:
        for pedido in pedidos_vencidos:
            pedido.expirado_em = datetime.now()
        db.commit()


def _propriedade_e_do_usuario(id_propriedade, id_produtor):
    # v1.9.3 - a Propriedade do pedido tem de ser do usuario logado (par Propriedade + Produtor)
    if not str(id_propriedade).isdecimal():
        return False
    try:
        pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    except Exception:
        return False
    return any(int(p.id_propriedade) == int(id_propriedade) and int(p.id_produtor) == int(id_produtor) for p in pares)


# v1.11.0 - Regra #73: valor de Propriedade vindo do navegador so segue adiante (link Voltar, Caixa de Sucesso)
# se for numero E de uma fazenda do usuario logado. Qualquer outro valor vira '' (descartado, sem erro).
def _id_propriedade_para_tela(valor):
    valor = str(valor or '').strip()
    if not valor.isdecimal():
        return ''
    try:
        pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    except Exception:
        return ''
    return valor if any(int(p.id_propriedade) == int(valor) for p in pares) else ''


def _buscar_produtor(id_produtor):
    with Session(engine) as db:
        return db.get(Produtor, id_produtor)


# ==========================================================
# LADO PRODUTOR (inalterado desde v1.3.0, exceto iniciar() v1.5.0)
# ==========================================================

@backup_restore.route('/produtor/backup/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            # v1.5.0: titulo com prefixo do modulo (Regra de Ouro
            # nova - ver selecionar_propriedade_produtor.html v1.2.0).
            titulo='Backup e Restore — Selecionar Propriedade',
            proximo='/produtor/backup',
            campo_propriedade='id_propriedade',
            # v1.5.0: FALTAVA - sem isso o botao Voltar caia sempre
            # em '/produtor/home' (default do template).
            voltar='/produtor/hub/utilitarios',
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='utilitarios',
        )

    # v1.6.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/backup?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/backup?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        # v1.5.0: titulo com prefixo do modulo (Regra de Ouro nova -
        # ver selecionar_propriedade_produtor.html v1.2.0).
        titulo='Backup e Restore — Selecionar Propriedade',
        proximo='/produtor/backup',
        campo_propriedade='id_propriedade',
        # v1.5.0: FALTAVA - sem isso o botao Voltar caia sempre em
        # '/produtor/home' (default do template).
        voltar='/produtor/hub/utilitarios',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='utilitarios',
    )


@backup_restore.route('/produtor/backup')
def tela_principal():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = _id_propriedade_para_tela(request.args.get('id_propriedade', ''))   # v1.11.0
    id_produtor = session['id_produtor']
    produtor = _buscar_produtor(id_produtor)

    backups = listar_backups_validos(produtor.schema_nome)

    with get_db_produtor(id_produtor) as db:
        _expirar_pedidos_antigos(db)

        pedidos = db.query(BackupRestorePedido).order_by(
            BackupRestorePedido.criado_em.desc()
        ).all()

    # v1.9.2 - pendente aparece sempre; atendido/expirado so no proprio dia.
#     v1.9.3: Sessao 122 (2026-11-12 13:55 -03) - Auditoria Etapa 1: pedido de Restore confere se a Propriedade e do usuario; Restore do Consiste valida os numeros antes de converter. REVERSAO: .bak_antes_s122_etapa1.
#     v1.9.4: Sessao 122 (2026-11-12 14:25 -03) - Auditoria Etapa 1: erro de Propriedade no pedido de Restore agora diz o que fazer e quem pode pedir. REVERSAO: .bak_antes_s122_msgs.
    hoje = datetime.now().date()
    pedidos = [
        p for p in pedidos
        if (p.atendido_em is None and p.expirado_em is None)
        or (p.atendido_em is not None and p.atendido_em.date() == hoje)
        or (p.expirado_em is not None and p.expirado_em.date() == hoje)
    ]

    # v1.7.0 - mensagens de resultado (aparecem uma vez so).
    msgs_erro = get_flashed_messages(category_filter=['backup_erro'])

    return render_template(
        'produtor/backup_principal.html',
        erro=msgs_erro[0] if msgs_erro else None,
        backups=backups,
        pedidos=pedidos,
        id_propriedade=id_propriedade,
        pode_acionar=caminho_permitido('/produtor/backup/criar', 'POST'),
        url_voltar='/produtor/hub/utilitarios',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='utilitarios',
    )


@backup_restore.route('/produtor/backup/criar', methods=['POST'])
def criar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = _id_propriedade_para_tela(request.form.get('id_propriedade', ''))   # v1.11.0 (conferido so depois do login)
    destino = f'/produtor/backup?id_propriedade={id_propriedade}'

    id_produtor = session['id_produtor']
    produtor = _buscar_produtor(id_produtor)

    try:
        criar_backup(produtor.schema_nome)
    except (ErroBackup, ExecutavelPostgresNaoEncontrado) as e:
        print(f'ERRO ao criar Backup: {e}')
        flash('Não foi possível fazer o backup. Tente de novo; se repetir, avise a Consiste.', 'backup_erro')
        return redirect(destino)

    # v1.9.0 - CAIXA DE SUCESSO: o usuario precisa ver que deu certo (resumo vai pela sessao, aparece uma vez so).
    session[CHAVE_SUCESSO_SESSAO] = {'tipo': 'backup', 'id_propriedade': id_propriedade,
                                     'quando': datetime.now().strftime('%d/%m/%Y às %H:%M')}
    return redirect(URL_BACKUP_CONCLUIDO)


@backup_restore.route('/produtor/backup/solicitar-restore', methods=['GET'])
def solicitar_restore_form():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = _id_propriedade_para_tela(request.args.get('id_propriedade', ''))   # v1.11.0

    id_produtor = session['id_produtor']
    produtor = _buscar_produtor(id_produtor)

    backups = listar_backups_validos(produtor.schema_nome)

    return render_template(
        'produtor/backup_solicitar_restore.html',
        erro=None,
        backups=backups,
        id_propriedade=id_propriedade,
        url_voltar=f'/produtor/backup?id_propriedade={id_propriedade}',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='utilitarios',
    )


@backup_restore.route('/produtor/backup/solicitar-restore', methods=['POST'])
def solicitar_restore_salvar():
    id_propriedade    = request.form.get('id_propriedade', '')
    motivo            = request.form.get('motivo', '').strip()
    data_backup_str   = request.form.get('data_backup_desejada', '').strip()

    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_produtor = session['id_produtor']
    produtor = _buscar_produtor(id_produtor)

    backups = listar_backups_validos(produtor.schema_nome)

    def _reexibir(mensagem_erro):
        id_eco = _id_propriedade_para_tela(id_propriedade)   # v1.11.0 - so ecoa na tela valor numerico e do usuario
        return render_template(
            'produtor/backup_solicitar_restore.html',
            erro=mensagem_erro,
            backups=backups,
            id_propriedade=id_eco,
            url_voltar=f'/produtor/backup?id_propriedade={id_eco}',
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='utilitarios',
        )

    if not id_propriedade or not _propriedade_e_do_usuario(id_propriedade, id_produtor):
        return _reexibir('Não foi possível confirmar a fazenda deste pedido. Volte ao Home, selecione a fazenda desejada e abra Utilitários > Backup de novo. Só quem tem acesso a essa fazenda (Titular, Administrador ou quem o Titular liberou) pode pedir a restauração.')
    if not motivo:
        return _reexibir('Motivo é obrigatório!')
    if not data_backup_str:
        return _reexibir('Selecione a data do backup que deseja restaurar!')

    try:
        data_backup_desejada = datetime.strptime(data_backup_str, '%Y-%m-%d').date()
    except ValueError:
        return _reexibir('Data selecionada é incorreta.')

    with get_db_produtor(id_produtor) as db:
        pedido = BackupRestorePedido(
            id_usuario=session['usuario_id'],
            id_propriedade=int(id_propriedade),
            motivo=motivo,
            data_backup_desejada=data_backup_desejada,
        )
        db.add(pedido)
        db.commit()

    # v1.9.0 - CAIXA DE SUCESSO (motivo e data ja eram variaveis locais: nada lido do banco depois do commit).
    session[CHAVE_SUCESSO_SESSAO] = {'tipo': 'pedido', 'id_propriedade': id_propriedade,
                                     'data_backup': data_backup_desejada.strftime('%d/%m/%Y'), 'motivo': motivo}
    return redirect(URL_PEDIDO_ENVIADO)


# -------------------------------------------------------
# Rotas GET (v1.9.0): CAIXA DE SUCESSO do Backup e do pedido de restauracao.
# Leem e apagam o resumo guardado na sessao; sem resumo (F5, link antigo),
# voltam para a tela de Backup. Cada rota so mostra o resumo do seu tipo.
# -------------------------------------------------------
def _caixa_backup(tipo):
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    resumo = session.get(CHAVE_SUCESSO_SESSAO)
    if not resumo or resumo.get('tipo') != tipo:
        return redirect('/produtor/backup')
    session.pop(CHAVE_SUCESSO_SESSAO, None)

    id_propriedade = str(resumo.get('id_propriedade', ''))
    url_backup = '/produtor/backup' + (f'?id_propriedade={id_propriedade}' if id_propriedade.isdecimal() else '')
    contexto = dict(
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='utilitarios',
    )
    botoes = [{'texto': 'Voltar ao Backup', 'url': url_backup, 'primario': True},
              {'texto': 'Utilitários', 'url': '/produtor/hub/utilitarios', 'primario': False}]

    if tipo == 'backup':
        return render_caixa_sucesso(
            contexto, titulo='Backup concluído com sucesso!', subtitulo=resumo['quando'],
            mudancas=[{'campo': 'Backup feito em', 'antes': None, 'depois': resumo['quando']}],
            notas=['Seus dados estão protegidos.'],
            botoes=botoes, url_voltar=url_backup, titulo_pagina='Orion SISBOV — Backup concluído',
        )
    return render_caixa_sucesso(
        contexto, titulo='Pedido de restauração enviado à Consiste!',
        mudancas=[{'campo': 'Data do backup', 'antes': None, 'depois': resumo['data_backup']},
                  {'campo': 'Motivo', 'antes': None, 'depois': resumo['motivo']}],
        notas=['Acompanhe o andamento na lista de pedidos da tela de Backup.'],
        botoes=botoes, url_voltar=url_backup, titulo_pagina='Orion SISBOV — Pedido enviado',
    )


@backup_restore.route(URL_BACKUP_CONCLUIDO)
def backup_concluido():
    return _caixa_backup('backup')


@backup_restore.route(URL_PEDIDO_ENVIADO)
def pedido_enviado():
    return _caixa_backup('pedido')


# ==========================================================
# LADO CONSISTE
# ==========================================================

def _montar_pedidos_pendentes():
    from backend.models import Propriedade

    pedidos_consolidados = []

    with Session(engine) as db_public:
        produtores_ativos = db_public.query(Produtor).filter_by(ativo=True).all()

    for produtor in produtores_ativos:
        if not produtor.schema_nome:
            continue

        with get_db_produtor(produtor.id) as db:
            _expirar_pedidos_antigos(db)

            pedidos = db.query(BackupRestorePedido).filter_by(
                atendido_em=None,
                expirado_em=None,
            ).order_by(BackupRestorePedido.criado_em.asc()).all()

            for pedido in pedidos:
                propriedade = db.get(Propriedade, pedido.id_propriedade)
                usuario = db.get(Usuario, pedido.id_usuario)

                pedidos_consolidados.append(SimpleNamespace(
                    id_pedido            = pedido.id,
                    id_produtor          = produtor.id,
                    schema_nome          = produtor.schema_nome,
                    produtor_nome        = produtor.nome,
                    propriedade_nome     = propriedade.nome if propriedade else '(Propriedade não encontrada)',
                    usuario_nome         = usuario.nome if usuario else '(Usuário não encontrado)',
                    motivo               = pedido.motivo,
                    data_backup_desejada = pedido.data_backup_desejada,
                    criado_em            = pedido.criado_em,
                    backups_disponiveis  = listar_backups_validos(produtor.schema_nome),
                ))

    return pedidos_consolidados


@backup_restore.route('/consiste/backup-restore')
def consiste_lista():
    if 'usuario_id' not in session:
        return redirecionar_home(session.get('usuario_perfil'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirecionar_home(session.get('usuario_perfil'))

    pedidos = _montar_pedidos_pendentes()

    return render_template(
        'consiste/consiste_backup_restore.html',
        erro=None,
        pedidos=pedidos,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='backup-restore',
    )


# -------------------------------------------------------
# ALTERADO v1.4.0: agora le confirmar_versao_incompativel do
# POST e trata VersaoSchemaIncompativel (backup_helper.py v1.3.0) -
# reexibe uma tela de confirmacao explicita em vez de restaurar
# direto quando as versoes divergem (ver DESCRICAO no cabecalho).
# -------------------------------------------------------
@backup_restore.route('/consiste/backup-restore/executar', methods=['POST'])
def consiste_executar():
    if 'usuario_id' not in session:
        return redirecionar_home(session.get('usuario_perfil'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirecionar_home(session.get('usuario_perfil'))

    id_produtor_str      = request.form.get('id_produtor', '')
    id_pedido_str         = request.form.get('id_pedido', '')
    nome_arquivo_backup   = request.form.get('nome_arquivo_backup', '').strip()
    confirmar_versao      = request.form.get('confirmar_versao_incompativel') == 'on'

    if not (id_produtor_str and id_pedido_str and nome_arquivo_backup):
        return redirect('/consiste/backup-restore')

    if not (id_produtor_str.isdecimal() and id_pedido_str.isdecimal()):   # v1.9.3 - valor com texto dava erro 500
        return redirect('/consiste/backup-restore')
    id_produtor = int(id_produtor_str)
    id_pedido   = int(id_pedido_str)

    produtor = _buscar_produtor(id_produtor)
    if not produtor or not produtor.schema_nome:
        return redirect('/consiste/backup-restore')

    with get_db_produtor(id_produtor) as db:
        pedido = db.query(BackupRestorePedido).filter_by(
            id=id_pedido,
            atendido_em=None,
            expirado_em=None,
        ).first()

        if not pedido:
            return redirect('/consiste/backup-restore')

    try:
        nome_arquivo_seguranca = executar_restore(
            produtor.schema_nome, nome_arquivo_backup,
            confirmar_versao_incompativel=confirmar_versao,
        )
    except VersaoSchemaIncompativel as e:
        # v1.4.0: nao restaura, nao marca nada como atendido -
        # reexibe pedindo confirmacao explicita da Consiste.
        return render_template(
            'consiste/consiste_confirmar_versao.html',
            erro=None,
            id_produtor=id_produtor,
            id_pedido=id_pedido,
            nome_arquivo_backup=nome_arquivo_backup,
            versao_backup=e.versao_backup,
            versao_atual=e.versao_atual,
            schema_nome=produtor.schema_nome,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='backup-restore',
        )
    except (BackupNaoEncontrado, ErroRestore, ExecutavelPostgresNaoEncontrado) as e:
        print(f'ERRO ao executar Restore: {e}')
        return redirect('/consiste/backup-restore')

    with get_db_produtor(id_produtor) as db:
        pedido = db.query(BackupRestorePedido).filter_by(id=id_pedido).first()
        if pedido:
            pedido.atendido_em              = datetime.now()
            pedido.atendido_por             = session['usuario_id']
            pedido.arquivo_backup_usado     = nome_arquivo_backup
            pedido.arquivo_seguranca_gerado = nome_arquivo_seguranca
            db.commit()

    return redirect('/consiste/backup-restore')

# =========================================================
# FIM DE ARQUIVO: backend\routers\backup_restore.py
# =========================================================