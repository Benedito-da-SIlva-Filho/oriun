# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\racas.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-07 17:45 -03
# ATUALIZADO EM: 2026-11-12 17:40 -03
# VERSAO: 1.3.1
# v1.3.1: Sessao 122 (2026-11-12 17:40 -03) - Auditoria Etapa 2 (item 11): id da Raca que nao e numero responde 400 com orientacao (antes dava erro 500); a tela so aceita id_propriedade do proprio usuario. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Tela de selecao de Racas comuns ao Produtor (Sessao 047) -
#     tb_4005_racas ja chega populada (script avulso backend/
#     scripts/popular_racas.py) com ~106 racas por Schema-por-
#     Produtor, cada uma com o campo `comum` controlando se
#     aparece no dropdown de Raca da futura Brincagem Sequencial.
#     Esta tela deixa o Produtor marcar/desmarcar quais racas sao
#     comuns a ELE, evitando uma lista de ~106 opcoes no dia a dia.
#
#     Padrao de tela: lista simples (sem paginacao/busca, volume
#     baixo o suficiente), 1 checkbox por linha, SEM botao Salvar -
#     cada marcar/desmarcar dispara AJAX (POST /produtor/racas/
#     toggle) e grava na hora (decisao de Benedito, Sessao 047).
#
#     Resolucao de Propriedade/Produtor: mesmo Padrao Reutilizavel
#     Nº1 do projeto (ver backup_restore.py/gta_manual.py) - rota
#     iniciar() resolve os pares, tela_principal() so le
#     id_propriedade da querystring.
#
#     Permissao: mesma regra do Backup/Restore e do Log de
#     Operacoes - so TITULAR/ADMINISTRADOR/ADMINISTRATIVO podem
#     marcar/desmarcar (decisao de Benedito, Sessao 047). Demais
#     Cargos veem a lista, mas os checkboxes chegam desabilitados.
#
#     v1.0.0: Criacao do modulo (Sessao 047).
#     v1.1.0: Sessao 051 (13/09/2026, 12:30 -03) - DUAS correcoes
#         de UX na funcao iniciar() (fluxo com erro e fluxo
#         normal), mesmo bug relatado por Benedito em Operacoes
#         Recentes:
#         (1) titulo generico 'Selecionar Propriedade' trocado por
#             'Raças da Fazenda — Selecionar Propriedade', seguindo
#             a Regra de Ouro nova documentada em
#             selecionar_propriedade_produtor.html v1.2.0.
#         (2) FALTAVA o parametro 'voltar' nas 2 chamadas de
#             render_template() - sem ele, o template cai no
#             default '/produtor/home' (ver template v1.1.0,
#             Sessao 044), entao o botao "Voltar" desta tela
#             levava sempre para a Home em vez do Hub de
#             Utilitarios. Corrigido com voltar='/produtor/hub/
#             utilitarios' nas 2 chamadas. Nenhuma outra rota deste
#             arquivo foi alterada.
#     v1.2.0: Sessao 091 (08/10/2026, 20:00 -03) - FAZENDA EM USO (Regra de Ouro #13):
#         Com fazenda em uso a tela "Selecionar Propriedade" e pulada (iniciar()
#         abre direto a lista de racas). As racas ficam no cadastro do produtor (nao
#         por fazenda), por isso NAO ha trava por Propriedade. Voltar vai ao Hub de
#         Utilitarios (sem parametros na URL). Marcar/desmarcar intacto.
#         REVERSAO: devolver a versao anterior.
#     v1.3.0: Sessao 097 (15/10/2026, 13:40 -03) - ETAPA 4 (permissoes) + Racas na ENTRADA. A checagem de cargo avulsa saiu: o
#         porteiro (modulo Entrada) decide quem ve (Consulta) e quem marca (Lanca); a tela usa
#         caminho_permitido para travar os checkboxes. Voltar vai ao Hub de Entrada.
#         REVERSAO: devolver a versao anterior (.bak_antes_etapa4_s097).
# =========================================================

from flask import Blueprint, render_template, request, redirect, jsonify, session

from backend.models.tb_4005_racas import Raca
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.permissoes import caminho_permitido
from backend.utils.multitenant import get_db_produtor


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
racas = Blueprint('racas', __name__)

# -------------------------------------------------------
# v1.3.0 - Quem pode ver/marcar Racas vem do PORTEIRO (modulo Entrada, tela
# Permissoes por Cargo): Consulta so olha, Lanca marca/desmarca.
# -------------------------------------------------------


# -------------------------------------------------------
# Rota: GET /produtor/racas/iniciar — ponto de partida, mesmo
# padrao de backup_restore.iniciar() (P-036): resolve Propriedade
# E Produtor juntos.
# -------------------------------------------------------
@racas.route('/produtor/racas/iniciar')
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
            titulo='Raças da Fazenda — Selecionar Propriedade',
            proximo='/produtor/racas',
            campo_propriedade='id_propriedade',
            # v1.1.0: FALTAVA - sem isso o botao Voltar caia sempre
            # em '/produtor/home' (default do template).
            voltar='/produtor/hub/entrada',
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='entrada',
        )

    # v1.2.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/racas?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/racas?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        # v1.1.0: titulo com prefixo do modulo (Regra de Ouro nova -
        # ver selecionar_propriedade_produtor.html v1.2.0).
        titulo='Raças da Fazenda — Selecionar Propriedade',
        proximo='/produtor/racas',
        campo_propriedade='id_propriedade',
        # v1.1.0: FALTAVA - sem isso o botao Voltar caia sempre em
        # '/produtor/home' (default do template).
        voltar='/produtor/hub/entrada',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/racas?id_propriedade=X — tela principal,
# lista todas as Racas (ativas) do schema do Produtor, ordenadas
# por Nome.
# -------------------------------------------------------
@racas.route('/produtor/racas')
def tela_principal():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    id_produtor = session['id_produtor']

    # Etapa 2 (item 11): so repassa ao template uma Propriedade que e do usuario.
    if id_propriedade:
        ids_do_usuario = {str(par.id_propriedade) for par in buscar_pares_propriedade_produtor(session['usuario_id'])}
        if id_propriedade not in ids_do_usuario:
            return redirecionar_home(session.get('usuario_perfil'))

    with get_db_produtor(id_produtor) as db:
        lista_racas = db.query(Raca).filter_by(ativo=True).order_by(Raca.nome).all()

    return render_template(
        'produtor/racas_lista.html',
        racas=lista_racas,
        id_propriedade=id_propriedade,
        pode_editar=caminho_permitido('/produtor/racas/toggle', 'POST'),
        url_voltar='/produtor/hub/entrada',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: POST /produtor/racas/toggle — AJAX, grava na hora (sem
# botao Salvar, decisao de Benedito). Espera JSON:
#   { "id": <id da Raca>, "comum": true|false }
# Devolve JSON: { "ok": true } ou { "ok": false, "erro": "..." }
# -------------------------------------------------------
@racas.route('/produtor/racas/toggle', methods=['POST'])
def toggle():
    if 'id_produtor' not in session:
        return jsonify({'ok': False, 'erro': 'Sessão não autenticada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_raca = dados.get('id')
    novo_valor = dados.get('comum')

    if id_raca is None or not isinstance(novo_valor, bool):
        return jsonify({'ok': False, 'erro': 'Dados inválidos.'}), 400

    # Etapa 2 (item 11): id que nao e numero antes dava erro 500.
    try:
        id_raca = int(id_raca)
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'erro': 'Dados inválidos. Recarregue a página e tente de novo.'}), 400

    id_produtor = session['id_produtor']

    with get_db_produtor(id_produtor) as db:
        raca = db.query(Raca).filter_by(id=id_raca).first()

        if not raca:
            return jsonify({'ok': False, 'erro': 'Raça não encontrada.'}), 404

        raca.comum = novo_valor
        db.commit()

    return jsonify({'ok': True})

# =========================================================
# FIM DE ARQUIVO: backend\routers\racas.py
# =========================================================