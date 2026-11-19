# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\reidentificacao.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-11 11:50 -03
# ATUALIZADO EM: 2026-11-12 19:00 -03
# VERSAO: 1.4.0
# v1.4.0: Sessao 122 (2026-11-12 19:00 -03) - Auditoria Etapa 4 (Entradas): lista de animais adulterada volta mensagem (antes erro 500). REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     REIDENTIFICACAO (Sessao 121) - o animal PERDEU o brinco SISBOV e recebe um brinco novo do estoque. So muda o numero do brinco
#     (15 digitos) e o Manejo (6 digitos): o resto da ficha continua valendo (RFID, lote, peso, historico de pesagens, ERAS/carencia).
#     Navegacao: Home -> Hub de Entrada -> grupo "Consultas e correcoes" -> card "Reidentificacao". Desenho: decisoes do Benedito de 11/11/2026.
#
#     TELA (varios animais de uma vez, o Produtor acumula e lanca tudo junto): Data da Reidentificacao (UMA para o pedido todo) + lista de
#     pares. Cada par = SISBOV do brinco perdido (Leitor ou digitado, 15 digitos) + SISBOV do brinco novo + Motivo (lista fixa, individual
#     por animal: PERDA / QUEBRA / DESGASTE / DEFEITO_LEITURA). O Orion confere o par na hora (rota /checar) e mostra os dados dos dois
#     brincos. GRAVAR grava o PEDIDO inteiro (tb_6005 = pedido, Nro do Pedido = id; tb_6006 = um item por animal) numa operacao so,
#     TUDO OU NADA, com Log e Desfazer (24h).
#
#     O QUE GRAVA POR ANIMAL (mesma transacao, mesmo id de operacao):
#       tb_2001  - o animal do brinco perdido SAI (linha inteira guardada no Log) e ENTRA um animal com o SISBOV e o Manejo novos, ficha igual
#       tb_2002  - saida do brinco perdido (tipo_saida = REIDENTI; sisbov_substituto = SISBOV novo)
#       tb_2017  - uma linha de SAIDA (perdido) e uma de ENTRADA (novo, tipo_entrada = REIDENTIFICACAO)
#       tb_4003  - o historico de pesagens passa para o SISBOV novo (so troca o numero)
#       tb_7017  - perdido: status REIDENTI + Saida Data = data da reidentificacao, Saida GTA = Manejo do NOVO, Saida Origem = REIDENTI
#                  novo:    em uso + Saida Data = data da reidentificacao, Saida GTA = Manejo do PERDIDO, Saida Origem = REIDENTI
#       tb_3008  - o brinco novo entra como em uso (origem REIDENTIFICACAO)
#       tb_3007  - o lote do brinco novo baixa 1 no saldo (qtde_saida sobe 1)
#       tb_7002  - PIA: o brinco novo entra com Motivo = REIDENTIFICACAO
#       tb_6005 / tb_6006 - o pedido e os pares (com Manejo antigo/novo e Motivo)
#       blockchain - evento REIDENTIFICACAO (um no brinco perdido e um no novo); so com provedor ligado, falha nunca derruba a gravacao.
#
#     TRAVAS (viram Inconformidade em tb_4010 e a tela explica):
#       - brinco perdido: precisa estar no REBANHO desta fazenda (tb_2001), com entrada comprovada (mesma regra da Saida) e sem leitura de
#         saida em aberto; animal que ja saiu diz onde esta (Regra #23)
#       - brinco novo: precisa estar DISPONIVEL no estoque desta fazenda (tb_7017); brinco ja usado, cancelado, reidentificado ou reservado
#         para GTA nao serve; nao pode estar em animal do rebanho nem em leitura do brete (Regras #26 e #42)
#       - o RFID acompanha o animal; brinco novo que ja traz OUTRO RFID e recusado
#       - Data da Reidentificacao: nao e futura nem anterior a entrada do animal
#       - motivo da lista fixa; o mesmo brinco nao repete no pedido
#
#     Desfazer: modulo 'reidentificacao' em log_operacoes.py (volta tudo; trava se algo veio depois com os animais ou se o pedido ja foi
#     marcado como ENVIADO a Certificadora - Regra #68). Consulta, Notificacao (PDF) e Inconformidades: reidentificacao_consulta.py.
#
#     v1.0.0: Criacao (Sessao 121, 11/11/2026, 11:50 -03). SQL: Tabelas\criar_reidentificacao_s121.sql (schema 11).
#     v1.1.0: Sessao 121 (2026-11-11 16:50 -03) - NOVO MODELO (decisao do Benedito, 11/11/2026): cada lancamento NAO cria pedido nem numero. Os animais ficam PENDENTES de Notificacao
#         (tb_6006 com id_pedido vazio, id_propriedade e a data de cada lancamento); o numero nasce so ao GERAR a Notificacao (reidentificacao_consulta.py).
#         Cada lancamento tem a sua Data (um Produtor lanca em dias diferentes). Log: itens tb_6006 (nao mais tb_6005). REVERSAO: .bak_antes_s121_pendentes.
#     REVERSAO (v1.0.0): remover este arquivo, reidentificacao_consulta.py, pdf_reidentificacao.py, os 3 templates, o model tb_4010, o registro em app.py,
#     os 3 cards do Hub, as linhas de permissoes.py e voltar os demais arquivos pelos .bak_antes_s121_reidentificacao.
#     v1.2.0: Sessao 121 (2026-11-11 18:10 -03) - NOVA rota /checar-antigo: o brinco PERDIDO e conferido assim que completa 15 digitos (devolve a ficha do animal ou o motivo que impede); o brinco novo continua conferido a parte (/checar). _conferir_par reaproveita a conferencia do perdido. REVERSAO: .bak_antes_s121_validacao.
#     v1.3.0: Sessao 121 (2026-11-11 18:40 -03) - O PIA NAO nasce mais no lancamento: so ao GERAR a Notificacao (decisao do Benedito: o PIA so e impresso depois). Assim o animal pendente pode ser excluido em qualquer ordem, sem buraco na numeracao. REVERSAO: .bak_antes_s121_pia.
# =========================================================

import re
from datetime import date, datetime

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import text

from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_3007_brincos_entrada import BrincoEntrada
from backend.models.tb_3008_brincos_saida import BrincoSaida
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4010_reidentificacao_inconformes import ReidentificacaoInconforme
from backend.models.tb_5001_brincagem import Brincagem
from backend.models.tb_6005_reidentificacao_com_baixa import ReidentificacaoComBaixa
from backend.models.tb_6006_reidentificacao_com_baixa_itens import ReidentificacaoComBaixaItem
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.saida_comunicado import _linha_para_dict
from backend.routers.troca_rfid import _propriedade_do_usuario, _buscar_propriedade_produtor, _numero, SO_DIGITOS, TAMANHO
from backend.utils.animal_saiu import mensagem_animal_saiu
from backend.utils.blockchain import registrar_evento_animal, TIPO_REIDENTIFICACAO
from backend.utils.entrada_comunicada import motivo_entrada_pendente
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.multitenant import get_db_produtor

# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
reidentificacao = Blueprint('reidentificacao', __name__)


@reidentificacao.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


NOME_MODULO_LOG = 'reidentificacao'
URL_HUB_ENTRADA = '/produtor/hub-novo/entrada'
URL_INICIAR = '/produtor/reidentificacao/iniciar'
MAX_ANIMAIS_PEDIDO = 500

# Lista fixa de motivos (chave gravada no banco -> texto da tela). Mesma lista do CHECK chk_tb_6006_motivo.
MOTIVOS = {
    'PERDA': 'Perda',
    'QUEBRA': 'Quebra',
    'DESGASTE': 'Desgaste',
    'DEFEITO_LEITURA': 'Defeito na leitura do chip/RFID',
}

MSG_FORA_DO_REBANHO = 'O brinco perdido não está no rebanho desta fazenda.'
MSG_NOVO_FORA_DO_ESTOQUE = 'O brinco novo não está no estoque desta fazenda.'
MSG_NOVO_NO_REBANHO = 'O brinco novo já está em um animal do rebanho. Use um brinco disponível do estoque.'
MSG_NOVO_EM_LEITURA = 'O brinco novo está em leitura do brete (animal ainda sem Comunicado). Use um brinco disponível do estoque.'
MSG_NOVO_RESERVADO = 'O brinco novo está reservado para uma GTA. Use outro brinco disponível do estoque.'
MSG_NOVO_SEM_MANEJO = 'O brinco novo não tem Manejo cadastrado no estoque.'


# -------------------------------------------------------
# Funcoes auxiliares
# -------------------------------------------------------
def _negado():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect(URL_INICIAR)
    return redirecionar_home()


def _url_voltar():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return URL_INICIAR
    return URL_HUB_ENTRADA


def _contexto_tela():
    return {
        'usuario_nome':   session.get('usuario_nome'),
        'usuario_perfil': session.get('usuario_perfil'),
        'cor_primaria':   session.get('cor_primaria', '#D4370A'),
        'nome_sistema':   session.get('nome_sistema', 'Orion SISBOV'),
        'menu_ativo':     'entrada',
    }


def _data_br(data):
    return data.strftime('%d/%m/%Y') if data else ''


def _ler_data(texto):
    """Aceita dd/mm/aaaa ou aaaa-mm-dd (campo de data do navegador). Devolve date ou None."""
    texto = str(texto or '').strip()
    for formato in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


def _sexo_texto(sexo):
    return {'MACHO': 'Macho', 'FEMEA': 'Fêmea'}.get(str(sexo or ''), '-')


# -------------------------------------------------------
# Grava a tentativa recusada (tb_4010). Nunca derruba a resposta: se nao der para gravar, segue.
# Commit proprio (solta tambem os bloqueios de linha, se houver).
# -------------------------------------------------------
def _registrar_inconforme(db, id_propriedade, antigo, novo, motivo):
    try:
        db.rollback()
        db.add(ReidentificacaoInconforme(
            id_propriedade=id_propriedade,
            id_usuario=session.get('usuario_id'),
            sisbov_antigo=(antigo or '')[:40] or None,
            sisbov_novo=(novo or '')[:40] or None,
            motivo=(motivo or '')[:200],
        ))
        db.commit()
    except Exception:
        db.rollback()


# -------------------------------------------------------
# Confere SO o brinco PERDIDO (usada pelo /checar-antigo, pelo /checar e pelo /gravar). Devolve (erro, status_http, animal).
# -------------------------------------------------------
def _conferir_antigo(db, id_prop, antigo, travar=False):
    if not SO_DIGITOS.match(antigo):
        return f'SISBOV do brinco perdido inválido: são {TAMANHO} dígitos (somente números).', 400, None
    consulta = db.query(Entrada).filter(Entrada.id_propriedade == id_prop, Entrada.sisbov == antigo)
    animal = (consulta.with_for_update() if travar else consulta).first()
    if animal is None:
        dono = db.query(Entrada.sisbov).filter(Entrada.rfid == antigo, Entrada.id_propriedade == id_prop).first()
        if dono is not None and dono[0]:
            return f'Este número é um RFID (do animal SISBOV {dono[0]}), não um SISBOV. Leia o brinco SISBOV.', 404, None
        pendente = db.query(Brincagem.id).filter(Brincagem.id_propriedade == id_prop, Brincagem.sisbov == antigo).first()
        if pendente is not None:
            return 'O brinco perdido ainda está em leitura do brete (sem Comunicado): não está no rebanho da fazenda.', 409, None
        return mensagem_animal_saiu(db, id_prop, sisbov=antigo) or MSG_FORA_DO_REBANHO, 404, None

    bloqueio = motivo_entrada_pendente(db, animal)   # mesma trava da Saida: entrada ainda nao comprovada
    if bloqueio:
        return bloqueio, 409, None
    aberta = (db.query(Embarque).filter(Embarque.sisbov == animal.sisbov, Embarque.sts == False)   # noqa: E712
              .order_by(Embarque.id.desc()).first())
    if aberta is not None:
        return (f'Animal em leitura de saída em aberto (embarque de {_data_br(aberta.data_embarque)}). '
                'Exclua a leitura na Consulta Embarque antes de reidentificar.'), 409, None
    return None, 200, animal


# -------------------------------------------------------
# Confere UM par (usada pelo /checar e, de novo, pelo /gravar). Devolve (erro, status_http, contexto).
# contexto = {'animal': Entrada, 'brinco_novo': EntradaBrincoRfid, 'brinco_antigo': EntradaBrincoRfid | None}
# travar=True bloqueia as linhas (SELECT ... FOR UPDATE) para ninguem usar o mesmo brinco ao mesmo tempo.
# -------------------------------------------------------
def _conferir_par(db, id_prop, antigo, novo, travar=False):
    if not SO_DIGITOS.match(antigo):
        return f'SISBOV do brinco perdido inválido: são {TAMANHO} dígitos (somente números).', 400, None
    if not SO_DIGITOS.match(novo):
        return f'SISBOV do brinco novo inválido: são {TAMANHO} dígitos (somente números).', 400, None
    if antigo == novo:
        return 'O brinco novo precisa ser diferente do brinco perdido.', 400, None

    erro, status, animal = _conferir_antigo(db, id_prop, antigo, travar)
    if erro:
        return erro, status, None

    # ---- brinco novo: disponivel no estoque desta fazenda ----
    consulta = db.query(EntradaBrincoRfid).filter(EntradaBrincoRfid.id_propriedade == id_prop, EntradaBrincoRfid.sisbov == novo)
    brinco_novo = (consulta.with_for_update() if travar else consulta).first()
    if brinco_novo is None:
        return mensagem_animal_saiu(db, id_prop, sisbov=novo) or MSG_NOVO_FORA_DO_ESTOQUE, 404, None
    if db.query(Entrada.id).filter(Entrada.id_propriedade == id_prop, Entrada.sisbov == novo).first() is not None:
        return MSG_NOVO_NO_REBANHO, 409, None
    if db.query(Brincagem.id).filter(Brincagem.id_propriedade == id_prop, Brincagem.sisbov == novo).first() is not None:
        return MSG_NOVO_EM_LEITURA, 409, None
    if brinco_novo.saida_gta is not None or brinco_novo.saida_origem is not None or brinco_novo.saida_data is not None or brinco_novo.status:
        situacao = str(brinco_novo.status or '').upper()
        if situacao == 'CANCELADO':
            return 'O brinco novo foi cancelado e não pode mais ser usado.', 409, None
        if situacao == 'REIDENTI':
            return 'O brinco novo já foi usado em uma reidentificação e não pode ser usado de novo.', 409, None
        return (mensagem_animal_saiu(db, id_prop, sisbov=novo)
                or 'O brinco novo já foi usado em outro animal e não pode ser usado de novo.'), 409, None
    if brinco_novo.reservado_id_gta is not None and brinco_novo.reservado_ate is not None and brinco_novo.reservado_ate >= datetime.now():
        return MSG_NOVO_RESERVADO, 409, None
    if not brinco_novo.manejo:
        return MSG_NOVO_SEM_MANEJO, 409, None
    if brinco_novo.rfid and animal.rfid and brinco_novo.rfid != animal.rfid:
        return f'O brinco novo já traz outro RFID ({brinco_novo.rfid}). O RFID do animal ({animal.rfid}) precisa acompanhar o animal.', 409, None

    brinco_antigo = db.query(EntradaBrincoRfid).filter(EntradaBrincoRfid.id_propriedade == id_prop, EntradaBrincoRfid.sisbov == antigo).first()
    return None, 200, {'animal': animal, 'brinco_novo': brinco_novo, 'brinco_antigo': brinco_antigo}


def _data_minima(animal):
    return animal.data_inclusao or animal.nascimento


def _erro_data(animal, data):
    """Data da Reidentificacao: nao futura e nao anterior a entrada do animal. Texto do erro ou None."""
    if data is None:
        return 'Informe a Data da Reidentificação.'
    if data > date.today():
        return 'A Data da Reidentificação não pode ser futura.'
    minima = _data_minima(animal)
    if minima is not None and data < minima:
        return f'A Data da Reidentificação não pode ser anterior à entrada do animal ({_data_br(minima)}).'
    return None


def _ficha_animal(db, animal):
    raca = db.get(Raca, animal.id_raca) if animal.id_raca else None
    return {
        'sisbov': animal.sisbov, 'manejo': animal.manejo or '', 'rfid': animal.rfid or '',
        'sexo': _sexo_texto(animal.sexo), 'raca': raca.codigo if raca else '', 'lote': animal.lote or '',
        'inclusao': _data_br(animal.data_inclusao), 'nascimento': _data_br(animal.nascimento),
        'data_minima_iso': _data_minima(animal).strftime('%Y-%m-%d') if _data_minima(animal) else '',
    }


# -------------------------------------------------------
# Rota: GET /produtor/reidentificacao/iniciar - ponto de partida (card do Hub)
# -------------------------------------------------------
@reidentificacao.route('/produtor/reidentificacao/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/reidentificacao/tela?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/reidentificacao/tela?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None if pares else 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
        titulo='Reidentificação — Selecionar Propriedade',
        proximo='/produtor/reidentificacao/tela',
        campo_propriedade='id_propriedade',
        voltar=URL_HUB_ENTRADA,
        **_contexto_tela(),
    )


# -------------------------------------------------------
# Rota: GET /produtor/reidentificacao/tela?id_propriedade=X
# -------------------------------------------------------
@reidentificacao.route('/produtor/reidentificacao/tela')
def tela():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()

    nome_propriedade, nome_produtor = _buscar_propriedade_produtor(int(id_propriedade))

    return render_template(
        'produtor/reidentificacao.html',
        id_propriedade=id_propriedade,
        propriedade_nome=nome_propriedade,
        produtor_nome=nome_produtor,
        motivos=MOTIVOS,
        hoje_iso=date.today().strftime('%Y-%m-%d'),
        max_animais=MAX_ANIMAIS_PEDIDO,
        url_voltar=_url_voltar(),
        url_consulta=f'/produtor/reidentificacao-consulta/lista?id_propriedade={int(id_propriedade)}',
        **_contexto_tela(),
    )


# -------------------------------------------------------
# Rota: POST /produtor/reidentificacao/checar (AJAX)
# Corpo: {id_propriedade, sisbov_antigo, sisbov_novo, data?}. Confere o par SEM gravar e devolve os dados dos dois brincos
# para o usuario ter certeza. Recusa (e grava a Inconformidade) quando algo nao passa.
# -------------------------------------------------------
@reidentificacao.route('/produtor/reidentificacao/checar-antigo', methods=['POST'])
def checar_antigo():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    antigo = _numero(dados.get('sisbov_antigo'))

    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário.'}), 403
    id_prop = int(id_propriedade)

    with get_db_produtor(session['id_produtor']) as db:
        erro, status, animal = _conferir_antigo(db, id_prop, antigo)
        if not erro and dados.get('data'):
            erro, status = _erro_data(animal, _ler_data(dados.get('data'))), 400
        if erro:
            _registrar_inconforme(db, id_prop, antigo, None, erro)
            return jsonify({'erro': erro}), status
        ficha = _ficha_animal(db, animal)

    return jsonify({'sucesso': True, 'animal': ficha})


@reidentificacao.route('/produtor/reidentificacao/checar', methods=['POST'])
def checar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    antigo = _numero(dados.get('sisbov_antigo'))
    novo = _numero(dados.get('sisbov_novo'))

    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário.'}), 403
    id_prop = int(id_propriedade)

    with get_db_produtor(session['id_produtor']) as db:
        erro, status, contexto = _conferir_par(db, id_prop, antigo, novo)
        if not erro and dados.get('data'):
            erro, status = _erro_data(contexto['animal'], _ler_data(dados.get('data'))), 400
        if erro:
            _registrar_inconforme(db, id_prop, antigo, novo, erro)
            return jsonify({'erro': erro}), status

        ficha = _ficha_animal(db, contexto['animal'])
        novo_brinco = contexto['brinco_novo']
        ficha['manejo_novo'] = novo_brinco.manejo or ''
        ficha['rfid_novo_brinco'] = novo_brinco.rfid or ''

    return jsonify({'sucesso': True, 'animal': ficha})


# -------------------------------------------------------
# Baixa UM animal e entra o animal com o brinco novo (tudo no Log). Devolve o animal novo (Entrada).
# -------------------------------------------------------
def _reidentificar_animal(db, id_operacao, id_prop, item, contexto, data, lotes_consumidos):
    animal = contexto['animal']
    brinco_novo = contexto['brinco_novo']
    brinco_antigo = contexto['brinco_antigo']
    antigo, novo, motivo = item['antigo'], item['novo'], item['motivo']
    manejo_antigo, manejo_novo = animal.manejo, brinco_novo.manejo
    rfid = animal.rfid or brinco_novo.rfid or None
    id_usuario = session.get('usuario_id')
    raca = db.get(Raca, animal.id_raca) if animal.id_raca else None
    sexo = str(animal.sexo) if animal.sexo is not None else None

    # ---- BLOCKCHAIN (1/2): evento no brinco PERDIDO, gravado ANTES de o animal sair da tb_2001 ----
    registrar_evento_animal(
        db, animal, TIPO_REIDENTIFICACAO, id_usuario=id_usuario, id_operacao=id_operacao, ocorrido_em=data,
        extras={'papel': 'BRINCO_PERDIDO', 'sisbov_novo': novo, 'manejo_novo': manejo_novo, 'motivo': motivo, 'data_reidentificacao': data},
    )

    # ---- tb_2002: saida do brinco perdido (REIDENTI). sisbov_substituto guarda o SISBOV novo ----
    saida = SaidaAnimal(
        id_propriedade=id_prop, id_animal=animal.id, id_embarque=None,
        sisbov=animal.sisbov, manejo=animal.manejo, rfid=animal.rfid,
        id_especie=animal.id_especie, sexo=animal.sexo, nascimento=animal.nascimento, eras_dias=animal.eras_dias,
        id_aptidao=animal.id_aptidao, id_raca=animal.id_raca, cota_hilton=animal.cota_hilton, liberacao_abate=animal.liberacao_abate,
        data_inclusao=animal.data_inclusao, lote_entrada=animal.lote,
        origem_propriedade=None, origem_cpf_cnpj=None,
        tipo_saida='REIDENTI', data_saida=data, numero_comunicado=None, sisbov_substituto=novo)
    db.add(saida)

    # ---- tb_2017: linha de SAIDA do brinco perdido ----
    mov_saida = Movimentacao(
        id_animal=animal.id, id_propriedade=id_prop, sisbov=animal.sisbov, manejo=animal.manejo, rfid=animal.rfid,
        negociacao='REIDENTIFICACAO', brincos=animal.brincos, id_especie=animal.id_especie, sexo=animal.sexo,
        nascimento=animal.nascimento, dias=animal.eras_dias, cota_hilton=animal.cota_hilton, id_aptidao=animal.id_aptidao,
        id_raca=animal.id_raca, liberacao_abate=animal.liberacao_abate, tipo_entrada=animal.tipo_entrada,
        data_inclusao=animal.data_inclusao, lote=animal.lote, data_brincagem=animal.data_brincagem,
        conferido_brete=animal.conferido_brete, conferido_em=animal.conferido_em,
        id_origem=animal.id_origem, id_gta_entrada=animal.id_gta_entrada,
        tipo_saida='REIDENTI', data_movimentacao=data, numero_comunicado=None)
    db.add(mov_saida)
    db.flush()

    # ---- tb_2001: o animal do brinco perdido SAI (linha inteira guardada no Log, para o Desfazer) ----
    linha_antiga = _linha_para_dict(animal)
    registrar_item(db, id_operacao, 'tb_2001', animal.id, 'DELETE', linha_antiga, None)
    registrar_item(db, id_operacao, 'tb_2002_saida_animais', saida.id, 'INSERT', None,
                   {'sisbov': saida.sisbov, 'tipo_saida': 'REIDENTI'})
    registrar_item(db, id_operacao, 'tb_2017_movimentacoes', mov_saida.id, 'INSERT', None,
                   {'sisbov': mov_saida.sisbov, 'tipo_saida': 'REIDENTI'})
    campos_novo = dict(
        id_especie=animal.id_especie, sexo=animal.sexo, nascimento=animal.nascimento, eras_dias=animal.eras_dias,
        id_raca=animal.id_raca, id_aptidao=animal.id_aptidao, cota_hilton=animal.cota_hilton,
        liberacao_abate=animal.liberacao_abate, tipo_entrada=animal.tipo_entrada, brincos=animal.brincos,
        id_gta_entrada=animal.id_gta_entrada, data_inclusao=animal.data_inclusao, lote=animal.lote, id_origem=animal.id_origem,
        id_propriedade=id_prop, numero_comunicado=animal.numero_comunicado, data_brincagem=animal.data_brincagem,
        conferido_brete=animal.conferido_brete, conferido_em=animal.conferido_em,
    )
    db.delete(animal)
    db.flush()

    # ---- tb_2001: ENTRA o animal com o SISBOV e o Manejo novos (resto da ficha igual; RFID acompanha) ----
    animal_novo = Entrada(sisbov=novo, manejo=manejo_novo, rfid=rfid, **campos_novo)
    db.add(animal_novo)
    db.flush()
    registrar_item(db, id_operacao, 'tb_2001', animal_novo.id, 'INSERT', None,
                   {'sisbov': animal_novo.sisbov, 'manejo': animal_novo.manejo})

    # ---- tb_2017: linha de ENTRADA do brinco novo (tipo_entrada REIDENTIFICACAO) ----
    mov_entrada = Movimentacao(
        id_animal=animal_novo.id, id_propriedade=id_prop, sisbov=novo, manejo=manejo_novo, rfid=rfid,
        negociacao='REIDENTIFICACAO', brincos=campos_novo['brincos'], id_especie=campos_novo['id_especie'], sexo=campos_novo['sexo'],
        nascimento=campos_novo['nascimento'], dias=campos_novo['eras_dias'], cota_hilton=campos_novo['cota_hilton'],
        id_aptidao=campos_novo['id_aptidao'], id_raca=campos_novo['id_raca'], liberacao_abate=campos_novo['liberacao_abate'],
        tipo_entrada='REIDENTIFICACAO', data_inclusao=campos_novo['data_inclusao'], lote=campos_novo['lote'],
        data_brincagem=campos_novo['data_brincagem'], conferido_brete=campos_novo['conferido_brete'],
        conferido_em=campos_novo['conferido_em'], id_origem=campos_novo['id_origem'], id_gta_entrada=campos_novo['id_gta_entrada'],
        data_movimentacao=data, numero_comunicado=None)
    db.add(mov_entrada)
    db.flush()
    registrar_item(db, id_operacao, 'tb_2017_movimentacoes', mov_entrada.id, 'INSERT', None,
                   {'sisbov': mov_entrada.sisbov, 'tipo_entrada': 'REIDENTIFICACAO'})

    # ---- tb_4003: o historico de pesagens passa para o SISBOV novo (so troca o numero) ----
    for peso in db.query(Peso).filter(Peso.id_propriedade == id_prop, Peso.sisbov == antigo).all():
        peso.sisbov = novo
        db.flush()
        registrar_item(db, id_operacao, 'tb_4003_pesos', peso.id, 'UPDATE',
                       {'sisbov': antigo}, {'sisbov': novo})

    # ---- tb_7017: brinco perdido (se veio do estoque) -> REIDENTI; Saida GTA = Manejo do NOVO ----
    if brinco_antigo is not None:
        antes = {'status': brinco_antigo.status, 'saida_data': brinco_antigo.saida_data.isoformat() if brinco_antigo.saida_data else None,
                 'saida_gta': brinco_antigo.saida_gta, 'saida_origem': brinco_antigo.saida_origem}
        brinco_antigo.status = 'REIDENTI'
        brinco_antigo.saida_data = data
        brinco_antigo.saida_gta = manejo_novo
        brinco_antigo.saida_origem = 'REIDENTI'
        db.flush()
        registrar_item(db, id_operacao, 'tb_7017_entrada_brincos_rfid', brinco_antigo.id, 'UPDATE', antes,
                       {'status': 'REIDENTI', 'saida_data': data.isoformat(), 'saida_gta': manejo_novo, 'saida_origem': 'REIDENTI'})

    # ---- tb_7017: brinco novo -> em uso; Saida GTA = Manejo do PERDIDO; RFID acompanha o animal ----
    antes = {'status': brinco_novo.status, 'rfid': brinco_novo.rfid, 'raca': brinco_novo.raca, 'sexo': brinco_novo.sexo,
             'nascimento': brinco_novo.nascimento.isoformat() if brinco_novo.nascimento else None, 'eras_dias': brinco_novo.eras_dias,
             'data_brincagem': brinco_novo.data_brincagem.isoformat() if brinco_novo.data_brincagem else None,
             'saida_data': None, 'saida_gta': None, 'saida_origem': None}
    brinco_novo.status = 'ENTRADA'
    brinco_novo.rfid = rfid
    brinco_novo.raca = raca.codigo if raca else None
    brinco_novo.sexo = sexo
    brinco_novo.nascimento = animal_novo.nascimento
    brinco_novo.eras_dias = animal_novo.eras_dias
    brinco_novo.data_brincagem = animal_novo.data_brincagem
    brinco_novo.saida_data = data
    brinco_novo.saida_gta = manejo_antigo
    brinco_novo.saida_origem = 'REIDENTI'
    db.flush()
    registrar_item(db, id_operacao, 'tb_7017_entrada_brincos_rfid', brinco_novo.id, 'UPDATE', antes,
                   {'status': 'ENTRADA', 'rfid': rfid, 'raca': brinco_novo.raca, 'sexo': sexo,
                    'nascimento': animal_novo.nascimento.isoformat() if animal_novo.nascimento else None,
                    'eras_dias': animal_novo.eras_dias,
                    'data_brincagem': animal_novo.data_brincagem.isoformat() if animal_novo.data_brincagem else None,
                    'saida_data': data.isoformat(), 'saida_gta': manejo_antigo, 'saida_origem': 'REIDENTI'})

    # ---- tb_3008: o brinco novo entra como em uso ----
    baixa = BrincoSaida(
        id_propriedade=id_prop, id_lote_entrada=brinco_novo.id_lote_entrada, sisbov=novo, rfid=rfid,
        data_saida=data, gta=manejo_antigo, origem='REIDENTIFICACAO')
    db.add(baixa)
    db.flush()
    registrar_item(db, id_operacao, 'tb_3008_brincos_saida', baixa.id, 'INSERT', None, {'sisbov': novo, 'origem': 'REIDENTIFICACAO'})
    lotes_consumidos[brinco_novo.id_lote_entrada] = lotes_consumidos.get(brinco_novo.id_lote_entrada, 0) + 1

    # (v1.3.0) o PIA do brinco novo (tb_7002, Motivo = REIDENTIFICACAO) e gravado so ao GERAR a Notificacao (reidentificacao_consulta.py)

    # ---- tb_6006: o par, PENDENTE de Notificacao ----
    linha = ReidentificacaoComBaixaItem(
        id_pedido=None, id_propriedade=id_prop, data_reidentificacao=data, id_usuario=id_usuario,   # pendente: sem Notificacao ainda
        sisbov_antigo=antigo, sisbov_novo=novo, rfid=rfid,
        manejo_antigo=manejo_antigo, manejo_novo=manejo_novo, motivo=motivo)
    db.add(linha)
    db.flush()
    registrar_item(db, id_operacao, 'tb_6006_reidentificacao_com_baixa_itens', linha.id, 'INSERT', None,
                   {'sisbov_antigo': antigo, 'sisbov_novo': novo, 'motivo': motivo})

    # ---- BLOCKCHAIN (2/2): evento no brinco NOVO (liga o novo ao perdido) ----
    registrar_evento_animal(
        db, animal_novo, TIPO_REIDENTIFICACAO, id_usuario=id_usuario, id_operacao=id_operacao, ocorrido_em=data,
        extras={'papel': 'BRINCO_NOVO', 'sisbov_anterior': antigo, 'manejo_anterior': manejo_antigo, 'motivo': motivo, 'data_reidentificacao': data},
    )
    return animal_novo


# -------------------------------------------------------
# Rota: POST /produtor/reidentificacao/gravar (AJAX)
# Corpo: {id_propriedade, data, itens: [{sisbov_antigo, sisbov_novo, motivo}]}. Confere TUDO de novo no servidor antes de gravar qualquer
# coisa; se um par falhar, NADA e gravado (tudo ou nada) e a resposta diz qual par e porque.
# -------------------------------------------------------
@reidentificacao.route('/produtor/reidentificacao/gravar', methods=['POST'])
def gravar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    itens_brutos = dados.get('itens') or []
    data = _ler_data(dados.get('data'))

    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário.'}), 403
    id_prop = int(id_propriedade)

    if not itens_brutos:
        return jsonify({'erro': 'Inclua pelo menos um animal na lista.'}), 400
    if not isinstance(itens_brutos, list) or not all(isinstance(b, dict) for b in itens_brutos):   # Etapa 4 (item 11)
        return jsonify({'erro': 'Lista de animais incorreta. Atualize a página e tente de novo.'}), 400
    if len(itens_brutos) > MAX_ANIMAIS_PEDIDO:
        return jsonify({'erro': f'Máximo de {MAX_ANIMAIS_PEDIDO} animais por lançamento. Grave este e faça outro.'}), 400
    if data is None:
        return jsonify({'erro': 'Informe a Data da Reidentificação.'}), 400

    itens, vistos = [], set()
    for posicao, bruto in enumerate(itens_brutos, start=1):
        antigo = _numero((bruto or {}).get('sisbov_antigo'))
        novo = _numero((bruto or {}).get('sisbov_novo'))
        motivo = str((bruto or {}).get('motivo') or '').strip().upper()
        if motivo not in MOTIVOS:
            return jsonify({'erro': f'Linha {posicao}: escolha o motivo da reidentificação.', 'linha': posicao}), 400
        if antigo in vistos or novo in vistos:
            return jsonify({'erro': f'Linha {posicao}: este brinco já está em outra linha da lista.', 'linha': posicao}), 400
        vistos.update((antigo, novo))
        itens.append({'antigo': antigo, 'novo': novo, 'motivo': motivo, 'posicao': posicao})

    with get_db_produtor(session['id_produtor']) as db:
        # ---- 1. confere todos os pares (com bloqueio de linha) ANTES de gravar qualquer coisa ----
        contextos = []
        for item in itens:
            erro, status, contexto = _conferir_par(db, id_prop, item['antigo'], item['novo'], travar=True)
            if not erro:
                erro = _erro_data(contexto['animal'], data)
                status = 400
            if erro:
                _registrar_inconforme(db, id_prop, item['antigo'], item['novo'], erro)
                return jsonify({'erro': f"Linha {item['posicao']}: {erro} Nada foi gravado.", 'linha': item['posicao']}), status
            contextos.append(contexto)

        # ---- 2. grava o lancamento inteiro, numa transacao so (os animais ficam PENDENTES de Notificacao) ----
        try:
            id_operacao = registrar_operacao(
                db,
                id_usuario=session['usuario_id'],
                id_propriedade=id_prop,
                modulo=NOME_MODULO_LOG,
                descricao=f'Reidentificação — {len(itens)} animal(is) pendente(s) de Notificação'[:120],
            )

            lotes_consumidos = {}
            for item, contexto in zip(itens, contextos):
                _reidentificar_animal(db, id_operacao, id_prop, item, contexto, data, lotes_consumidos)

            # tb_3007: cada lote baixa o que foi usado (saldo e qtde_saida), igual a Brincagem
            for id_lote, quantidade in lotes_consumidos.items():
                lote = db.get(BrincoEntrada, id_lote)
                saldo_antes, saida_antes = lote.saldo, (lote.qtde_saida or 0)
                lote.saldo = saldo_antes - quantidade
                lote.qtde_saida = saida_antes + quantidade
                db.flush()
                registrar_item(db, id_operacao, 'tb_3007_brincos_entrada', lote.id, 'UPDATE',
                               {'saldo': saldo_antes, 'qtde_saida': saida_antes},
                               {'saldo': lote.saldo, 'qtde_saida': lote.qtde_saida})

            quantidade_total = len(itens)
            db.commit()
        except Exception:
            db.rollback()
            return jsonify({'erro': 'Não foi possível gravar. Nada foi alterado.'}), 500

    return jsonify({
        'sucesso': True,
        'mensagem': f'{quantidade_total} animal(is) reidentificado(s). Eles ficam pendentes de Notificação até você gerar a Notificação na Consulta.',
        'quantidade': quantidade_total,
        'url_consulta': f'/produtor/reidentificacao-consulta/lista?id_propriedade={id_prop}',
    })

# =========================================================
# FIM DE ARQUIVO: backend\routers\reidentificacao.py
# =========================================================
