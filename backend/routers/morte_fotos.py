# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\morte_fotos.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-01 18:00 -03
# ATUALIZADO EM: 2026-11-03 15:40 -03
# VERSAO: 1.1.0
# v1.1.0: Sessao 123 (2026-11-13 20:10 -03) - AUDITORIA ETAPA 6 (leitura a fundo): lista do Controle mostra o aviso vindo do PDF (faixa amarela, #69). REVERSAO: .bak_antes_etapa6e.
#
# DESCRICAO:
#     MORTE - Controle Interno (lista dos MRT) e FOTOS do animal morto e do brinco (pacote 4). Prova para a Vistoria/Auditoria.
#     Decisoes do Benedito (01/11/2026): foto OPCIONAL, ate 2 por animal (uma do animal, uma do brinco, ou uma so com os dois), com aviso
#     "sem foto" na lista; pode anexar, trocar e excluir DEPOIS, mesmo com a Notificacao ja gerada (a foto nao muda o documento); a foto
#     aparece na Consulta do Controle Interno e NAO no PDF do Anexo XXII; se o lancamento for desfeito, as fotos somem junto (banco com
#     cascata + arquivos apagados pelo Desfazer).
#     Seguranca: toda rota confere se a Propriedade e do usuario logado e se a foto pertence a um animal MORTE dessa Propriedade.
#
#     ROTAS:
#       GET  /produtor/morte/controle?id_propriedade=            - lista dos Controles (MRT) da Propriedade
#       GET  /produtor/morte/fotos/<controle>?id_propriedade=    - animais do MRT, com as 2 vagas de foto de cada um
#       POST /produtor/morte/foto/enviar   (multipart, AJAX)     - anexa ou troca a foto da vaga 1 ou 2
#       GET  /produtor/morte/foto/ver/<id_foto>?id_propriedade=  - mostra a imagem
#       POST /produtor/morte/foto/excluir  (JSON, AJAX)          - exclui a foto
#
#     v1.0.0: Sessao 111 (01/11/2026) - Criacao. REVERSAO: apagar este arquivo e os morte_controle.html / morte_fotos.html; desfazer o registro
#     v1.0.1: Sessao 113 (03/11/2026, 13:50 -03) - Tela de Fotos: data da morte de CADA animal (o cabecalho nao mostra mais uma data unica do Controle).  REVERSAO: .bak_antes_s113_fotos.
#     v1.0.2: Sessao 113 (03/11/2026, 15:40 -03) - Lista do Controle mostra a data (ou o periodo) da morte de CADA animal do MRT.  REVERSAO: .bak_antes_s113_ordem_data.
#             em app.py e no Hub. As fotos ja gravadas ficam em C:\orion\storage\morte.
# =========================================================
from flask import Blueprint, render_template, request, redirect, session, jsonify, send_file, abort
from sqlalchemy import func

from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_2013_com_morte import ControleMorte
from backend.models.tb_2022_morte_fotos import MorteFoto
from backend.routers.auth import redirecionar_home
from backend.routers.saida_consulta import _contexto_base, _propriedade_do_usuario, _negado, _nomes, URL_HUB
from backend.routers.morte_lancamento import _texto_controle, URL_LANCAR
from backend.utils.morte_fotos import (
    preparar_imagem, gravar_arquivo, apagar_arquivo, caminho_do_arquivo, MAXIMO_FOTOS_POR_ANIMAL, LIMITE_BYTES_FOTO,
)
from backend.utils.multitenant import get_db_produtor

morte_fotos = Blueprint('morte_fotos', __name__)

URL_CONTROLE = '/produtor/morte/controle'
CHAVE_AVISO_MORTE_CONTROLE = 'aviso_morte_controle'   # mesma chave gravada por morte_relatorios.py (Regra #69)
URL_FOTOS = '/produtor/morte/fotos'
URL_ENVIAR = '/produtor/morte/foto/enviar'
URL_VER = '/produtor/morte/foto/ver'
URL_EXCLUIR = '/produtor/morte/foto/excluir'


def _data_hora(valor):
    return valor.strftime('%d/%m/%Y %H:%M') if valor else '-'


# -------------------------------------------------------
# GET /produtor/morte/controle - lista dos Controles Internos (MRT)
# -------------------------------------------------------
@morte_fotos.route('/produtor/morte/controle')
def controle():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:   # entrada pelo Hub: usa a fazenda em uso (ou a unica)
        return redirect('/produtor/morte/iniciar?destino=controle')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_propriedade = int(id_propriedade)

    with get_db_produtor(session['id_produtor']) as db:
        controles = (db.query(ControleMorte).filter(ControleMorte.id_propriedade == id_propriedade)
                     .order_by(ControleMorte.controle.desc()).all())
        ids = [c.id for c in controles]
        com_foto = {}
        if ids:
            linhas = (db.query(SaidaAnimal.id_com_morte, func.count(func.distinct(SaidaAnimal.id)))
                      .join(MorteFoto, MorteFoto.id_saida_animal == SaidaAnimal.id)
                      .filter(SaidaAnimal.id_com_morte.in_(ids)).group_by(SaidaAnimal.id_com_morte).all())
            com_foto = {i: q for i, q in linhas}
        periodos = {}
        if ids:
            for idc, menor, maior in (db.query(SaidaAnimal.id_com_morte, func.min(SaidaAnimal.data_saida), func.max(SaidaAnimal.data_saida))
                                      .filter(SaidaAnimal.id_com_morte.in_(ids), SaidaAnimal.tipo_saida == 'MORTE')
                                      .group_by(SaidaAnimal.id_com_morte).all()):
                if menor is not None:   # o mesmo MRT pode ter datas diferentes: mostra o periodo
                    periodos[idc] = menor.strftime('%d/%m/%Y') if menor == maior else f"{menor.strftime('%d/%m/%Y')} a {maior.strftime('%d/%m/%Y')}"
        itens = [{
            'controle': c.controle, 'texto': _texto_controle(c.controle), 'insercao': _data_hora(c.criado_em),
            'data_morte': periodos.get(c.id, c.data_morte.strftime('%d/%m/%Y')), 'qtd': c.qtd_animais, 'origem': c.origem,
            'notificacao': f'{c.numero_comunicado:06d}' if c.numero_comunicado else '',
            'com_foto': com_foto.get(c.id, 0), 'sem_foto': max(c.qtd_animais - com_foto.get(c.id, 0), 0),
        } for c in controles]

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, session['id_produtor'])
    return render_template(
        'produtor/morte_controle.html', aviso=session.pop(CHAVE_AVISO_MORTE_CONTROLE, None), itens=itens, id_propriedade=id_propriedade, url_fotos=URL_FOTOS, url_lancar=URL_LANCAR,
        url_voltar=URL_HUB, produtor_nome=produtor_nome, propriedade_nome=propriedade_nome, propriedade_local=propriedade_local,
        **_contexto_base())


# -------------------------------------------------------
# GET /produtor/morte/fotos/<controle> - animais do MRT e as vagas de foto
# -------------------------------------------------------
@morte_fotos.route('/produtor/morte/fotos/<int:numero_controle>')
def fotos(numero_controle):
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_propriedade = int(id_propriedade)

    with get_db_produtor(session['id_produtor']) as db:
        ctrl = (db.query(ControleMorte).filter(ControleMorte.id_propriedade == id_propriedade,
                                               ControleMorte.controle == numero_controle).first())
        if ctrl is None:
            return redirect(f'{URL_CONTROLE}?id_propriedade={id_propriedade}')
        animais = (db.query(SaidaAnimal).filter(SaidaAnimal.id_com_morte == ctrl.id, SaidaAnimal.tipo_saida == 'MORTE')
                   .order_by(SaidaAnimal.sisbov.asc()).all())
        ids = [a.id for a in animais]
        por_animal = {}
        if ids:
            for f in db.query(MorteFoto).filter(MorteFoto.id_saida_animal.in_(ids)).all():
                por_animal.setdefault(f.id_saida_animal, {})[f.ordem] = f.id
        linhas = [{
            'id': a.id, 'sisbov': a.sisbov, 'manejo': a.manejo or '',
            'data_morte': a.data_saida.strftime('%d/%m/%Y') if a.data_saida else '-',   # data de CADA animal (no mesmo MRT podem diferir)
            'sexo': 'Fêmea' if a.sexo == 'FEMEA' else ('Macho' if a.sexo == 'MACHO' else '-'),
            'fotos': {1: por_animal.get(a.id, {}).get(1), 2: por_animal.get(a.id, {}).get(2)},
        } for a in animais]
        cabecalho = {'texto': _texto_controle(ctrl.controle),
                     'notificacao': f'{ctrl.numero_comunicado:06d}' if ctrl.numero_comunicado else ''}

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, session['id_produtor'])
    return render_template(
        'produtor/morte_fotos.html', linhas=linhas, cab=cabecalho, id_propriedade=id_propriedade,
        url_enviar=URL_ENVIAR, url_ver=URL_VER, url_excluir=URL_EXCLUIR, url_voltar=f'{URL_CONTROLE}?id_propriedade={id_propriedade}',
        produtor_nome=produtor_nome, propriedade_nome=propriedade_nome, propriedade_local=propriedade_local,
        **_contexto_base())


def _foto_da_propriedade(db, id_foto, id_propriedade):
    """A foto so e valida se o animal dela e uma MORTE desta Propriedade."""
    return (db.query(MorteFoto).join(SaidaAnimal, SaidaAnimal.id == MorteFoto.id_saida_animal)
            .filter(MorteFoto.id == id_foto, SaidaAnimal.id_propriedade == int(id_propriedade),
                    SaidaAnimal.tipo_saida == 'MORTE').first())


# -------------------------------------------------------
# POST /produtor/morte/foto/enviar - anexa ou troca (vaga 1 ou 2)
# -------------------------------------------------------
@morte_fotos.route('/produtor/morte/foto/enviar', methods=['POST'])
def enviar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    id_propriedade = request.form.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou.'}), 403
    try:
        id_animal = int(request.form.get('id_saida_animal'))
        ordem = int(request.form.get('ordem'))
    except (TypeError, ValueError):
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if ordem < 1 or ordem > MAXIMO_FOTOS_POR_ANIMAL:
        return jsonify({'erro': 'Vaga de foto inválida.'}), 400
    arq = request.files.get('arquivo')
    if arq is None or not arq.filename:
        return jsonify({'erro': 'Escolha a foto.'}), 400
    dados = arq.read(LIMITE_BYTES_FOTO + 1)
    jpeg, erro = preparar_imagem(dados)
    if erro:
        return jsonify({'erro': erro}), 400

    nome_antigo = None
    with get_db_produtor(session['id_produtor']) as db:
        animal = db.query(SaidaAnimal).filter(SaidaAnimal.id == id_animal, SaidaAnimal.id_propriedade == int(id_propriedade),
                                              SaidaAnimal.tipo_saida == 'MORTE').first()
        if animal is None:
            return jsonify({'erro': 'Animal não encontrado entre as mortes desta Propriedade.'}), 404
        nome, hash_, tamanho = gravar_arquivo(id_propriedade, animal.id, ordem, jpeg)
        existente = db.query(MorteFoto).filter(MorteFoto.id_saida_animal == animal.id, MorteFoto.ordem == ordem).first()
        try:
            if existente is not None:
                nome_antigo = existente.arquivo_nome
                existente.arquivo_nome = nome
                existente.nome_original = (arq.filename or '')[:200]
                existente.tamanho_bytes = tamanho
                existente.hash_sha256 = hash_
                existente.id_usuario = session.get('usuario_id')
                foto = existente
            else:
                foto = MorteFoto(id_saida_animal=animal.id, ordem=ordem, arquivo_nome=nome, nome_original=(arq.filename or '')[:200],
                                 tamanho_bytes=tamanho, hash_sha256=hash_, id_usuario=session.get('usuario_id'))
                db.add(foto)
            db.flush()
            id_foto = foto.id
            db.commit()
        except Exception:
            db.rollback()
            apagar_arquivo(nome)
            return jsonify({'erro': 'Não foi possível gravar a foto. Tente de novo.'}), 500
    if nome_antigo:
        apagar_arquivo(nome_antigo)
    return jsonify({'ok': True, 'id_foto': id_foto, 'ordem': ordem})


# -------------------------------------------------------
# GET /produtor/morte/foto/ver/<id_foto>
# -------------------------------------------------------
@morte_fotos.route('/produtor/morte/foto/ver/<int:id_foto>')
def ver(id_foto):
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        abort(403)
    with get_db_produtor(session['id_produtor']) as db:
        foto = _foto_da_propriedade(db, id_foto, id_propriedade)
        nome = foto.arquivo_nome if foto is not None else None
    if not nome:
        abort(404)
    try:
        resposta = send_file(caminho_do_arquivo(nome), mimetype='image/jpeg', max_age=0)
    except (FileNotFoundError, OSError):
        abort(404)
    resposta.headers['Cache-Control'] = 'private, no-store'
    return resposta


# -------------------------------------------------------
# POST /produtor/morte/foto/excluir
# -------------------------------------------------------
@morte_fotos.route('/produtor/morte/foto/excluir', methods=['POST'])
def excluir():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou.'}), 403
    try:
        id_foto = int(dados.get('id_foto'))
    except (TypeError, ValueError):
        return jsonify({'erro': 'Dados incompletos.'}), 400
    with get_db_produtor(session['id_produtor']) as db:
        foto = _foto_da_propriedade(db, id_foto, id_propriedade)
        if foto is None:
            return jsonify({'erro': 'Foto não encontrada.'}), 404
        nome = foto.arquivo_nome
        db.delete(foto)
        db.commit()
    apagar_arquivo(nome)
    return jsonify({'ok': True})

# =========================================================
# FIM DE ARQUIVO: backend\routers\morte_fotos.py
# =========================================================
