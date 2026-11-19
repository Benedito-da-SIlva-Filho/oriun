# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\morte_lancamento.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-01 17:10 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.2.0
# v1.2.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (3 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     MORTE DE ANIMAIS - lancamento individual (pacote 2). O escritorio lanca a morte do animal pelo Manejo (ou SISBOV), com a data REAL da
#     morte, o Tipo, a Causa Mortis (catalogo MAPA, tb_1007) e o Destino da carcaca. Nada vem pre-preenchido.
#     Cada Confirmar e UM lancamento = UM Controle Interno (MRT000118, tb_2013_com_morte) e DA BAIXA NA HORA (decisao do Benedito):
#       - tb_2013_com_morte: 1 linha nova (controle = maior da Propriedade + 1; numero_comunicado vazio ate a Notificacao);
#       - tb_2002_saida_animais: o animal depois da saida (tipo_saida = MORTE, data_saida = data da morte, tipo/causa/destino, id_com_morte);
#       - tb_2017_movimentacoes: NOVA linha (negociacao e tipo_saida = MORTE; a linha da entrada fica como historico);
#       - tb_2001: o animal sai do estoque (linha inteira guardada no Log: o Desfazer a devolve).
#     O brinco do morto nunca volta (a regra "brinco disponivel" ja exclui o que esta na tb_2002).
#     REGRAS: so animal em estoque; mesma trava da Saida (entrada ja comunicada: Comunicado de Entrada / Notificacao / brete); data nunca
#     futura nem anterior a entrada do animal; animal em leitura de saida aberta nao pode (excluir a leitura antes).
#     Log de Operacoes modulo 'morte': Desfazer pelas Operacoes Recentes SO ate gerar a Notificacao (log_operacoes.py v1.20.0).
#     Notificacao (Anexo XXII), arquivo texto, fotos e relatorios: pacotes seguintes.
#
#     ROTAS:
#       GET  /produtor/morte/iniciar   - escolhe a Propriedade (ou usa a fazenda em uso)
#       GET  /produtor/morte/lancar    - tela do lancamento
#       POST /produtor/morte/checar    - (AJAX) acha o animal e confere as travas
#       POST /produtor/morte/gravar    - (AJAX) grava o lancamento e da a baixa
#
#     v1.0.0: Sessao 111 (01/11/2026) - Criacao. REVERSAO: apagar este arquivo e morte_lancamento.html; desfazer o registro em app.py, no Hub e
#     v1.0.1: Sessao 113 (03/11/2026, 14:10 -03) - MRT aberto na Morte individual (opcao A): a tela manda o Controle aberto e o servidor soma o animal nele; Desfazer de um animal tira so ele (UPDATE no Log), MRT some se for o primeiro/unico.  REVERSAO: .bak_antes_s113_mrt_aberto.
#             em permissoes.py; log_operacoes.py volta ao .bak_antes_s111_morte.
#     v1.1.0: Sessao 117 (06/11/2026, 20:10 -03) - MORTE na BLOCKCHAIN: cada animal baixado (lancamento individual e arquivo) gera o evento MORTE com Tipo, Causa Mortis (texto), Destino, MRT e Data da Morte (data do evento = Data da Morte). Mesma transacao e mesmo id_operacao do Desfazer. REVERSAO: .bak_antes_s117_blockchain_morte.
# =========================================================
from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models.tb_1007_motivo_mortes import MotivoMorte
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_2013_com_morte import ControleMorte
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4005_racas import Raca
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.saida_leitor import _propriedade_do_usuario, _negado, _buscar_animal, _ler_data_br, _data_br, MENSAGEM_MANEJO_PEDE_DV
from backend.routers.saida_consulta import _contexto_base, _nomes, URL_HUB
from backend.routers.saida_comunicado import _linha_para_dict
from backend.utils.entrada_comunicada import motivo_entrada_pendente
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.blockchain import registrar_evento_animal, TIPO_MORTE   # v1.1.0 - blockchain
from backend.utils.multitenant import get_db_produtor

morte = Blueprint('morte', __name__)


@morte.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


URL_INICIAR = '/produtor/morte/iniciar'
URL_LANCAR = '/produtor/morte/lancar'
URL_CHECAR = '/produtor/morte/checar'
URL_GRAVAR = '/produtor/morte/gravar'
URL_CONTROLE = '/produtor/morte/controle'
URL_FOTOS = '/produtor/morte/fotos'
CLASSE_TRAVA_MORTE = 2013          # 1o numero da trava de numeracao (Controle MRT), por Propriedade
MODULO_LOG = 'morte'

TIPOS_MORTE = (('ACIDENTAL', 'Acidental'), ('DESLIGADO', 'Desligado'), ('NATURAL', 'Natural'), ('SACRIFICIO', 'Sacrifício'))
DESTINOS_MORTE = (('CREMACAO', 'Cremação'), ('ENTERRAMENTO', 'Enterramento'), ('OUTROS', 'Outros'))
CODIGOS_TIPO = tuple(c for c, _ in TIPOS_MORTE)
CODIGOS_DESTINO = tuple(c for c, _ in DESTINOS_MORTE)


def _texto_controle(numero):
    return f'MRT{int(numero):06d}'


def _proximo_controle(db, id_propriedade):
    maximo = db.query(func.max(ControleMorte.controle)).filter(ControleMorte.id_propriedade == int(id_propriedade)).scalar()
    return (maximo or 0) + 1


def _causas():
    """Causa Mortis (catalogo MAPA, tb_1007): so as ativas, em ordem alfabetica."""
    with Session(engine) as db:
        linhas = db.query(MotivoMorte).filter(MotivoMorte.ativo == True).order_by(MotivoMorte.descricao.asc()).all()   # noqa: E712
        return [{'id': m.id, 'descricao': m.descricao} for m in linhas]


# -------------------------------------------------------
# Conferencia de UM animal (usada pelo checar e, de novo, pelo gravar). Devolve {'bloqueio': texto} ou {'animal': Entrada}.
# -------------------------------------------------------
def _conferir_animal(db, id_propriedade, sisbov, manejo, dv):
    animal, bloqueio = _buscar_animal(db, id_propriedade, sisbov, manejo, dv)
    if bloqueio:
        return {'bloqueio': bloqueio, 'pede_dv': bloqueio == MENSAGEM_MANEJO_PEDE_DV}
    motivo = motivo_entrada_pendente(db, animal)     # mesma trava da Saida: entrada ainda nao comunicada
    if motivo:
        return {'bloqueio': motivo}
    aberta = (db.query(Embarque).filter(Embarque.sisbov == animal.sisbov, Embarque.sts == False)   # noqa: E712
              .order_by(Embarque.id.desc()).first())
    if aberta is not None:
        return {'bloqueio': (f'Animal em leitura de saída em aberto (embarque de {_data_br(aberta.data_embarque)}). '
                             'Exclua a leitura na Consulta Embarque antes de lançar a morte.')}
    return {'animal': animal}


def _data_minima(animal):
    return animal.data_inclusao or animal.nascimento


def _ficha(db, animal):
    raca = db.get(Raca, animal.id_raca) if animal.id_raca else None
    minima = _data_minima(animal)
    return {
        'sisbov': animal.sisbov, 'manejo': animal.manejo or '', 'rfid': animal.rfid or '',
        'sexo': 'Fêmea' if animal.sexo == 'FEMEA' else ('Macho' if animal.sexo == 'MACHO' else '-'),
        'raca': raca.codigo if raca else '', 'lote': animal.lote or '',
        'inclusao': _data_br(animal.data_inclusao), 'nascimento': _data_br(animal.nascimento),
        'data_minima_iso': minima.strftime('%Y-%m-%d') if minima else '',
        'data_minima_br': _data_br(minima) if minima else '',
    }


def _baixar_animal(db, id_operacao, id_propriedade, e, ctrl, controle, data_morte, tipo_morte, id_motivo, destino_morte):
    """
    Da a baixa de UM animal da Morte (usado pelo lancamento individual e pelo arquivo): tb_2002 (saida MORTE), nova linha na tb_2017 e
    o animal sai da tb_2001 (linha inteira guardada no Log, para o Desfazer). Devolve o SISBOV.
    """
    saida = SaidaAnimal(
        id_propriedade=id_propriedade, id_animal=e.id, id_embarque=None,
        sisbov=e.sisbov, manejo=e.manejo, rfid=e.rfid,
        id_especie=e.id_especie, sexo=e.sexo, nascimento=e.nascimento, eras_dias=e.eras_dias,
        id_aptidao=e.id_aptidao, id_raca=e.id_raca, cota_hilton=e.cota_hilton, liberacao_abate=e.liberacao_abate,
        data_inclusao=e.data_inclusao, lote_entrada=e.lote,
        origem_propriedade=None, origem_cpf_cnpj=None,
        tipo_saida='MORTE', data_saida=data_morte, numero_comunicado=None,
        tipo_morte=tipo_morte, id_motivo_morte=id_motivo, destino_morte=destino_morte, id_com_morte=ctrl.id)
    db.add(saida)

    movimentacao = Movimentacao(
        id_animal=e.id, id_propriedade=id_propriedade, sisbov=e.sisbov, manejo=e.manejo, rfid=e.rfid,
        negociacao='MORTE', brincos=e.brincos, id_especie=e.id_especie, sexo=e.sexo, nascimento=e.nascimento,
        dias=e.eras_dias, cota_hilton=e.cota_hilton, id_aptidao=e.id_aptidao, id_raca=e.id_raca,
        liberacao_abate=e.liberacao_abate, tipo_entrada=e.tipo_entrada, data_inclusao=e.data_inclusao,
        lote=e.lote, data_brincagem=e.data_brincagem,
        conferido_brete=e.conferido_brete, conferido_em=e.conferido_em,
        id_origem=e.id_origem, id_gta_entrada=e.id_gta_entrada,
        tipo_saida='MORTE', data_movimentacao=data_morte, numero_comunicado=None)
    db.add(movimentacao)
    db.flush()

    registrar_item(db, id_operacao, 'tb_2001', e.id, 'DELETE', _linha_para_dict(e), None)
    registrar_item(db, id_operacao, 'tb_2002_saida_animais', saida.id, 'INSERT', None, {'sisbov': saida.sisbov, 'controle': controle})
    registrar_item(db, id_operacao, 'tb_2017_movimentacoes', movimentacao.id, 'INSERT', None, {'sisbov': movimentacao.sisbov, 'controle': controle})

    # ---- BLOCKCHAIN (v1.1.0) - evento MORTE, gravado ANTES do animal sair da tb_2001; data do evento = Data da Morte ----
    causa_texto = None
    if id_motivo:
        with Session(engine) as db_cat:
            motivo = db_cat.get(MotivoMorte, id_motivo)
            causa_texto = motivo.descricao if motivo else None
    registrar_evento_animal(
        db, e, TIPO_MORTE, id_usuario=session.get('usuario_id'), id_operacao=id_operacao, ocorrido_em=data_morte,
        extras={'tipo_morte': tipo_morte, 'causa_mortis': causa_texto, 'destino_morte': destino_morte,
                'controle_mrt': _texto_controle(controle), 'data_morte': data_morte})

    db.delete(e)
    return e.sisbov


# -------------------------------------------------------
# GET /produtor/morte/iniciar
# -------------------------------------------------------
@morte.route('/produtor/morte/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    alvo = URL_CONTROLE if request.args.get('destino') == 'controle' else URL_LANCAR   # s111: o Controle Interno usa a mesma escolha de Propriedade

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html', pares=pares_lista, erro=erro,
            titulo='Morte de Animais — Selecionar Propriedade', proximo=alvo, campo_propriedade='id_propriedade',
            voltar=URL_HUB, usuario_nome=session.get('usuario_nome'), usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A', nome_sistema='Orion SISBOV', menu_ativo='saidas')

    if len(pares) == 0:
        return _tela_selecionar([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor'] = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{alvo}?id_propriedade={par_em_uso.id_propriedade}')
    if len(pares) == 1:
        par = pares[0]
        session['id_produtor'] = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{alvo}?id_propriedade={par.id_propriedade}')
    return _tela_selecionar(pares, None)


# -------------------------------------------------------
# GET /produtor/morte/lancar
# -------------------------------------------------------
@morte.route('/produtor/morte/lancar')
def lancar():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    with get_db_produtor(session['id_produtor']) as db:
        proximo = _proximo_controle(db, id_propriedade)
    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, session['id_produtor'])
    return render_template(
        'produtor/morte_lancamento.html',
        id_propriedade=int(id_propriedade), controle_texto=_texto_controle(proximo),
        causas=_causas(), tipos=TIPOS_MORTE, destinos=DESTINOS_MORTE,
        hoje_iso=date.today().strftime('%Y-%m-%d'),
        url_checar=URL_CHECAR, url_gravar=URL_GRAVAR, url_voltar=URL_HUB,
        produtor_nome=produtor_nome, propriedade_nome=propriedade_nome, propriedade_local=propriedade_local,
        **_contexto_base())


# -------------------------------------------------------
# POST /produtor/morte/checar (AJAX) - acha o animal pelo Manejo (+DV) ou pelo SISBOV e confere as travas.
# -------------------------------------------------------
@morte.route('/produtor/morte/checar', methods=['POST'])
def checar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    codigo = ''.join(c for c in str(dados.get('codigo') or '') if c.isdecimal())
    dv = ''.join(c for c in str(dados.get('dv') or '') if c.isdecimal())[:1]
    if not id_propriedade or not codigo:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou. Volte ao Hub de Saídas e abra de novo.'}), 403
    sisbov, manejo = (codigo, '') if len(codigo) == 15 else ('', codigo)
    with get_db_produtor(session['id_produtor']) as db:
        resultado = _conferir_animal(db, id_propriedade, sisbov, manejo, dv)
        if 'bloqueio' in resultado:
            return jsonify({'bloqueio': True, 'mensagem': resultado['bloqueio'], 'pede_dv': bool(resultado.get('pede_dv'))})
        return jsonify({'ok': True, 'animal': _ficha(db, resultado['animal'])})


# -------------------------------------------------------
# POST /produtor/morte/gravar (AJAX) - grava o lancamento e da a baixa. Confere TUDO de novo no servidor. Tudo ou nada.
# -------------------------------------------------------
@morte.route('/produtor/morte/gravar', methods=['POST'])
def gravar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = ''.join(c for c in str(dados.get('sisbov') or '') if c.isdecimal())
    data_morte = _ler_data_br(dados.get('data_morte'))
    tipo_morte = str(dados.get('tipo_morte') or '').strip().upper()
    destino_morte = str(dados.get('destino_morte') or '').strip().upper()
    try:
        id_motivo = int(dados.get('id_motivo'))
    except (TypeError, ValueError):
        id_motivo = None
    try:
        controle_aberto = int(dados.get('controle_aberto')) if dados.get('controle_aberto') else None   # v1.2.0: MRT aberto na tela
    except (TypeError, ValueError):
        controle_aberto = None

    if not id_propriedade or len(sisbov) != 15:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou. Volte ao Hub de Saídas e abra de novo.'}), 403
    if data_morte is None:
        return jsonify({'erro': 'Data da Morte incorreta. Digite no formato dd/mm/aaaa.'}), 400
    if data_morte > date.today():
        return jsonify({'erro': 'A Data da Morte não pode ser futura.'}), 400
    if tipo_morte not in CODIGOS_TIPO:
        return jsonify({'erro': 'Escolha o Tipo da Morte.'}), 400
    if id_motivo is None:
        return jsonify({'erro': 'Escolha a Causa Mortis.'}), 400
    if destino_morte not in CODIGOS_DESTINO:
        return jsonify({'erro': 'Escolha o Destino.'}), 400
    with Session(engine) as dbp:
        motivo_ok = dbp.query(MotivoMorte.id).filter(MotivoMorte.id == id_motivo, MotivoMorte.ativo == True).first()   # noqa: E712
    if motivo_ok is None:
        return jsonify({'erro': 'Causa Mortis inválida.'}), 400

    id_propriedade = int(id_propriedade)
    id_usuario = session['usuario_id']
    try:
        with get_db_produtor(session['id_produtor']) as db:
            # trava da numeracao: o primeiro que clicar leva o numero
            db.execute(text('SELECT pg_advisory_xact_lock(:classe, :id_propriedade)'),
                       {'classe': CLASSE_TRAVA_MORTE, 'id_propriedade': id_propriedade})
            resultado = _conferir_animal(db, id_propriedade, sisbov, '', '')
            if 'bloqueio' in resultado:
                return jsonify({'bloqueio': True, 'erro': resultado['bloqueio'], 'mensagem': resultado['bloqueio']}), 409
            e = resultado['animal']
            minima = _data_minima(e)
            if minima is not None and data_morte < minima:
                return jsonify({'erro': f'A Data da Morte não pode ser anterior à entrada do animal ({_data_br(minima)}).'}), 400

            # v1.2.0 - MRT aberto (opcao A): a tela manda o numero do Controle que ela mantem aberto; vale so se for desta Propriedade,
            # deste usuario, INDIVIDUAL e ainda sem Notificacao. Senao abre um MRT novo (sem erro).
            ctrl = None
            if controle_aberto:
                ctrl = (db.query(ControleMorte)
                        .filter(ControleMorte.id_propriedade == id_propriedade, ControleMorte.controle == controle_aberto,
                                ControleMorte.origem == 'INDIVIDUAL', ControleMorte.numero_comunicado.is_(None),
                                ControleMorte.id_usuario == id_usuario)
                        .with_for_update().first())
            data_br = _data_br(data_morte)
            if ctrl is None:
                controle = _proximo_controle(db, id_propriedade)
                texto_mrt = _texto_controle(controle)
                id_operacao = registrar_operacao(
                    db, id_usuario=id_usuario, id_propriedade=id_propriedade, modulo=MODULO_LOG,
                    descricao=f'Morte {texto_mrt} — SISBOV {e.sisbov} — {data_br}'[:255])
                ctrl = ControleMorte(id_propriedade=id_propriedade, controle=controle, data_morte=data_morte,
                                     qtd_animais=1, origem='INDIVIDUAL', id_usuario=id_usuario)
                db.add(ctrl)
                db.flush()
                registrar_item(db, id_operacao, 'tb_2013_com_morte', ctrl.id, 'INSERT', None, {'controle': controle, 'data_morte': data_br})
            else:
                controle = ctrl.controle
                texto_mrt = _texto_controle(controle)
                id_operacao = registrar_operacao(
                    db, id_usuario=id_usuario, id_propriedade=id_propriedade, modulo=MODULO_LOG,
                    descricao=f'Morte {texto_mrt} — SISBOV {e.sisbov} — {data_br}'[:255])
                antes = int(ctrl.qtd_animais or 0)
                ctrl.qtd_animais = antes + 1
                db.flush()
                registrar_item(db, id_operacao, 'tb_2013_com_morte', ctrl.id, 'UPDATE', {'qtd_animais': antes}, {'qtd_animais': antes + 1})

            sisbov_gravado = _baixar_animal(db, id_operacao, id_propriedade, e, ctrl, controle, data_morte, tipo_morte, id_motivo, destino_morte)
            proximo_texto = _texto_controle(_proximo_controle(db, id_propriedade))
            qtd_no_controle = int(ctrl.qtd_animais or 1)
            db.commit()
    except IntegrityError:
        return jsonify({'erro': 'Não foi possível gravar (o animal pode ter sido lançado em outra tela). Confira e tente de novo.'}), 409

    return jsonify({'ok': True, 'controle': texto_mrt, 'controle_numero': controle, 'qtd_no_controle': qtd_no_controle,
                    'proximo': proximo_texto, 'sisbov': sisbov_gravado,
                    'url_fotos': f'{URL_FOTOS}/{controle}?id_propriedade={id_propriedade}'})

# =========================================================
# FIM DE ARQUIVO: backend\routers\morte_lancamento.py
# =========================================================
