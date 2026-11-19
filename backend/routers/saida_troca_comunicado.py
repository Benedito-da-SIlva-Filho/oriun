# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\saida_troca_comunicado.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-21 12:30 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.2.0
# v1.2.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (2 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Substituicao de Animal DEPOIS do Comunicado de Saida (Sessao 102, Pacote 3) - grupo
#     "Consultas e correcoes" do Hub de Saidas. Troca um animal que JA esta num Comunicado
#     (e ja deu baixa) por outro animal da Propriedade, do MESMO PERFIL (especie + sexo +
#     faixa de idade na Data Embarque). O numero do Comunicado e mantido; o documento e
#     reimpresso depois.
#
#     REGRAS (fechadas com Benedito, 21/10/2026):
#       - Pode trocar SEMPRE, inclusive com o Comunicado ja IMPRESSO: a tela avisa para
#         reimprimir e trocar as vias entregues. O Log guarda quem fez e quando.
#       - NAO existe "desfazer" do Comunicado (nem desta troca): para voltar, faz-se
#         outra troca (o animal que saiu volta pelo mesmo caminho).
#       - So Titular e Administrador fazem a troca (conferido por Cargo na Propriedade).
#       - Perfil igual: especie, sexo e faixa de idade na Data Embarque (mesma regra da
#         troca antes do Comunicado - reaproveita _avaliar_substituto).
#
#     O QUE A TROCA GRAVA (uma transacao so, com a mesma trava do Gerar Comunicado):
#       X = animal que estava no Comunicado   Y = animal que vai no lugar
#       - X VOLTA para a tb_2001: a linha original e recuperada do Log de Operacoes (a baixa
#         guardou a linha inteira) - mesmo id, mesmos dados de antes da baixa.
#       - Y SAI da tb_2001 (linha inteira vai para o Log, como na baixa).
#       - tb_2002: a linha de X fica substituido=True (historico, nunca apagada); nasce a
#         linha de Y com os mesmos dados do Comunicado (GTA, frigorifico, datas, numero).
#       - tb_2020: a leitura passa a ser de Y (continua sts=True, mesmo numero de Comunicado).
#       - tb_2017: nasce a linha de saida de Y e uma linha de retorno de X
#         (negociacao = 'RETORNO-SUBST').  <-- ASSUMIDO, Benedito ainda nao confirmou.
#       - tb_2011 e tb_4001_gta nao mudam (mesma quantidade de animais, mesmo numero).
#       - Log (modulo saida_troca_comunicado, SO historico).
#
#     ROTAS (todas em /produtor/saida-troca-comunicado/):
#       iniciar      - resolve a Propriedade (fazenda em uso) e abre a lista de Comunicados.
#       comunicados  - Comunicados da Propriedade (mais novos primeiro).
#       animais      - animais do Comunicado, com o botao Trocar.
#       trocar       - tela da troca (reaproveita saida_substituicao_trocar.html).
#       checar       - POST JSON: confere o substituto (perfil, avisos).
#       gravar       - POST JSON: confere tudo de novo e grava + Log.
#
#     v1.0.0: Criacao (Sessao 102).
#     v1.1.0: Sessao 103 (22/10/2026, 16:30 -03) - Caixa de Sucesso (utils/caixa_sucesso.py): depois da troca o usuario ve 'Troca feita com
#             sucesso!' (SISBOV que saiu do Comunicado -> SISBOV que entrou, o que voltou ao rebanho e o aviso vermelho de reimprimir quando o
#             Comunicado ja foi impresso) em vez do banner. Nova rota GET /produtor/saida-troca-comunicado/concluida.  REVERSAO: .bak_antes_caixa_pacoteA_s103.
#     REVERSAO: remover este arquivo e os templates saida_troca_comunicado_*.html; devolver
#     os .bak_antes_subst_comunicado_s102 de app.py, permissoes.py, hub_entrada_agrupado.py,
#     log_operacoes.py, comunicado_saida_display.py e saida_substituicao_trocar.html. Trocas
#     ja feitas NAO voltam sozinhas: so por nova troca ou por SQL com o Log de Operacoes.
# =========================================================

from datetime import date, datetime, time
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.sqltypes import Date as SADate, DateTime as SADateTime, Numeric as SANumeric, Time as SATime

from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_2011_com_saidas import ComunicadoSaida
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.models.tb_parceiros import Parceiro
from backend.models.tb_log_operacoes_itens import LogOperacaoItem
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.saida_leitor import _formatar_kg, PESO_MINIMO_PADRAO
from backend.routers.saida_consulta import (
    _contexto_base, _propriedade_do_usuario, _negado, _data_br, _faixa_em, _nomes, URL_HUB,
)
from backend.routers.saida_substituicao import _avaliar_substituto, _validar_peso, _json_valor
from backend.routers.saida_comunicado import _linha_para_dict, _numero_6, _dados_frigorifico, CLASSE_TRAVA
from backend.utils.multitenant import get_db_produtor
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.caixa_sucesso import render_caixa_sucesso

saida_troca_comunicado = Blueprint('saida_troca_comunicado', __name__)

MODULO_LOG = 'saida_troca_comunicado'
CARGOS_TROCA = ('TITULAR', 'ADMINISTRADOR')
NEGOCIACAO_RETORNO = 'RETORNO-SUBST'      # tb_2017: linha de retorno do animal que voltou ao rebanho

URL_INICIAR = '/produtor/saida-troca-comunicado/iniciar'
URL_COMUNICADOS = '/produtor/saida-troca-comunicado/comunicados'
URL_ANIMAIS = '/produtor/saida-troca-comunicado/animais'
URL_TROCAR = '/produtor/saida-troca-comunicado/trocar'
URL_CHECAR = '/produtor/saida-troca-comunicado/checar'
URL_GRAVAR = '/produtor/saida-troca-comunicado/gravar'
URL_CONCLUIDA = '/produtor/saida-troca-comunicado/concluida'

MSG_SEM_PERMISSAO = 'Só o Titular e o Administrador da Propriedade podem trocar animal depois do Comunicado.'
MSG_COMUNICADO_NAO_ACHADO = 'Animal não encontrado neste Comunicado (ou já foi trocado). Volte e abra de novo.'
MSG_AVISO_IMPRESSO = ('Este Comunicado já foi impresso. Depois da troca, imprima de novo (Reimpressão) '
                      'e substitua as vias já entregues.')

# Campos que o Comunicado copia da linha de X para a linha de Y (tb_2002).
CAMPOS_DO_COMUNICADO = (
    'tipo_saida', 'gta_saida', 'gta_saida_emissao', 'gta_saida_validade', 'gta_saida_animais',
    'id_gta', 'id_frigorifico', 'destino_propriedade', 'destino_cpf_cnpj',
    'data_embarque', 'data_saida', 'numero_comunicado', 'lote_saida',
)


# =========================================================
# BLOCO 1 - Funcoes puras (sem banco)
# =========================================================
def _cargo_permitido(cargo):
    """True se o Cargo pode trocar depois do Comunicado (Titular ou Administrador)."""
    return (cargo or '').strip().upper() in CARGOS_TROCA


def _valor_do_log(coluna, valor):
    """Valor gravado no Log (JSON) -> valor do tipo da coluna (data, hora, numero)."""
    if valor is None:
        return None
    tipo = coluna.type
    if isinstance(tipo, SADateTime):
        return datetime.fromisoformat(valor)
    if isinstance(tipo, SADate):
        return date.fromisoformat(valor)
    if isinstance(tipo, SATime):
        return time.fromisoformat(valor)
    if isinstance(tipo, SANumeric):
        return Decimal(valor)
    return valor


def _entrada_do_log(dados):
    """Monta o Entrada (tb_2001) a partir da linha inteira guardada no Log na baixa."""
    campos = {}
    for coluna in Entrada.__table__.columns:
        if coluna.key in dados:
            campos[coluna.key] = _valor_do_log(coluna, dados[coluna.key])
    campos['atualizado_em'] = datetime.now()
    return Entrada(**campos)


# =========================================================
# BLOCO 2 - Acesso ao banco
# =========================================================
def _cargo_na_propriedade(id_propriedade):
    for par in buscar_pares_propriedade_produtor(session['usuario_id']):
        if int(par.id_propriedade) == int(id_propriedade):
            return par.cargo
    return None


def _pode_trocar(id_propriedade):
    return _cargo_permitido(_cargo_na_propriedade(id_propriedade))


def _sem_permissao():
    return (f'<p style="font-family:Arial;padding:24px">{MSG_SEM_PERMISSAO} '
            f'<a href="{URL_HUB}">Voltar</a></p>'), 403


def _linha_do_comunicado(db, id_propriedade, id_embarque, travar=False):
    """Leitura (tb_2020) de um animal ja baixado num Comunicado; ou None."""
    try:
        id_int = int(id_embarque)
    except (TypeError, ValueError):
        return None
    consulta = db.query(Embarque).filter(
        Embarque.id == id_int, Embarque.id_propriedade == int(id_propriedade),
        Embarque.tipo_saida == 'ABATE', Embarque.sts == True,   # noqa: E712
        Embarque.numero_comunicado.isnot(None))
    if travar:
        consulta = consulta.with_for_update()
    return consulta.first()


def _saida_ativa(db, id_propriedade, linha, travar=False):
    """Linha da tb_2002 do animal que esta no Comunicado agora (nao substituida); ou None."""
    consulta = db.query(SaidaAnimal).filter(
        SaidaAnimal.id_propriedade == int(id_propriedade), SaidaAnimal.id_embarque == linha.id,
        SaidaAnimal.sisbov == linha.sisbov, SaidaAnimal.numero_comunicado == linha.numero_comunicado,
        SaidaAnimal.substituido == False)   # noqa: E712
    if travar:
        consulta = consulta.with_for_update()
    return consulta.first()


def _comunicado_impresso(db, id_propriedade, numero):
    return db.query(ComunicadoSaida.id).filter(
        ComunicadoSaida.id_propriedade_origem == int(id_propriedade),
        ComunicadoSaida.numero_comunicado == numero, ComunicadoSaida.status == 'IMPRESSO',
        ComunicadoSaida.tipo_saida == 'ABATE').first()   # v-s107 is not None


def _linha_do_log(db, id_animal, sisbov, id_propriedade):
    """Linha inteira da tb_2001 guardada no Log quando o animal foi baixado (a ultima); ou None."""
    item = (
        db.query(LogOperacaoItem)
        .filter(LogOperacaoItem.tabela == 'tb_2001', LogOperacaoItem.tipo_mudanca == 'DELETE',
                LogOperacaoItem.id_registro == id_animal)
        .order_by(LogOperacaoItem.id.desc()).first()
    )
    if item is None or not isinstance(item.dados_antes, dict):
        return None
    dados = item.dados_antes
    if dados.get('sisbov') != sisbov or int(dados.get('id_propriedade') or 0) != int(id_propriedade):
        return None
    return dados


def _data_entrega(db, id_gta_entrada):
    gta = db.get(Gta, id_gta_entrada) if id_gta_entrada else None
    return gta.data_entrega if gta else None


def _retrato_movimentacao(e):
    """Campos da tb_2017 que vem do animal da tb_2001 (retrato do animal agora)."""
    return dict(
        id_animal=e.id, id_propriedade=e.id_propriedade, sisbov=e.sisbov, manejo=e.manejo, rfid=e.rfid,
        brincos=e.brincos, id_especie=e.id_especie, sexo=e.sexo, nascimento=e.nascimento, dias=e.eras_dias,
        cota_hilton=e.cota_hilton, id_aptidao=e.id_aptidao, id_raca=e.id_raca, liberacao_abate=e.liberacao_abate,
        tipo_entrada=e.tipo_entrada, data_inclusao=e.data_inclusao, lote=e.lote, data_brincagem=e.data_brincagem,
        conferido_brete=e.conferido_brete, conferido_em=e.conferido_em, id_origem=e.id_origem,
        id_gta_entrada=e.id_gta_entrada,
    )


def _novos_da_leitura(db, animal, peso, avisos, id_usuario, agora):
    """Campos do substituto que vao para a leitura (tb_2020) e para a tb_2002 (mesmos nomes)."""
    gta_ent = db.get(Gta, animal.id_gta_entrada) if animal.id_gta_entrada else None
    origem = db.get(Parceiro, animal.id_origem) if animal.id_origem else None
    fora = bool(avisos['fora_liberacao']['ativo'])
    era = bool(avisos['era_0_12']['ativo'])
    return {
        'id_animal': animal.id, 'sisbov': animal.sisbov, 'manejo': animal.manejo, 'rfid': animal.rfid,
        'id_especie': animal.id_especie, 'sexo': animal.sexo, 'nascimento': animal.nascimento,
        'eras_dias': animal.eras_dias, 'id_aptidao': animal.id_aptidao, 'id_raca': animal.id_raca,
        'cota_hilton': bool(animal.cota_hilton), 'liberacao_abate': animal.liberacao_abate,
        'gta_entrada': ((gta_ent.numero_gta_completo or '')[:10] or None) if gta_ent else None,
        'gta_entrada_emissao': gta_ent.data_emissao if gta_ent else None,
        'gta_entrada_validade': gta_ent.data_validade if gta_ent else None,
        'gta_entrada_animais': gta_ent.qtde_animais if gta_ent else None,
        'data_inclusao': animal.data_inclusao, 'lote_entrada': animal.lote,
        'origem_propriedade': (origem.nome or '')[:150] if origem else None,
        'origem_cpf_cnpj': origem.cpf_cnpj if origem else None,
        'peso_saida': peso, 'elemento': None,
        'aceite_fora_liberacao': fora,
        'aceite_fora_liberacao_por': id_usuario if fora else None,
        'aceite_fora_liberacao_em': agora if fora else None,
        'aceite_era_0_12': era,
        'aceite_era_0_12_por': id_usuario if era else None,
        'aceite_era_0_12_em': agora if era else None,
    }


# =========================================================
# BLOCO 3 - Rotas
# =========================================================

# -------------------------------------------------------
# GET /produtor/saida-troca-comunicado/iniciar
# -------------------------------------------------------
@saida_troca_comunicado.route('/produtor/saida-troca-comunicado/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista,
            erro=erro,
            titulo='Trocar Animal depois do Comunicado — Selecionar Propriedade',
            proximo=URL_COMUNICADOS,
            campo_propriedade='id_propriedade',
            voltar=URL_HUB,
            **_contexto_base(),
        )

    if len(pares) == 0:
        return _tela_selecionar([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')

    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{URL_COMUNICADOS}?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_COMUNICADOS}?id_propriedade={par.id_propriedade}')

    return _tela_selecionar(pares, None)


# -------------------------------------------------------
# GET /produtor/saida-troca-comunicado/comunicados - Comunicados da Propriedade.
# -------------------------------------------------------
@saida_troca_comunicado.route('/produtor/saida-troca-comunicado/comunicados')
def comunicados():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    if not _pode_trocar(id_propriedade):
        return _sem_permissao()
    id_produtor = session['id_produtor']

    with get_db_produtor(id_produtor) as db:
        linhas = (
            db.query(ComunicadoSaida)
            .filter(ComunicadoSaida.id_propriedade_origem == int(id_propriedade), ComunicadoSaida.tipo_saida == 'ABATE')   # v-s107
            .order_by(ComunicadoSaida.numero_comunicado.desc(), ComunicadoSaida.id.asc()).all()
        )
        grupos = {}
        for c in linhas:
            g = grupos.setdefault(c.numero_comunicado, {
                'numero': _numero_6(c.numero_comunicado), 'id_frigorifico': c.id_frigorifico,
                'data_saida': c.data_saida, 'gtas': [], 'qtde': 0, 'impresso': False})
            g['gtas'].append(c.gta_numero)
            g['qtde'] += c.qtd_animais or 0
            g['impresso'] = g['impresso'] or c.status == 'IMPRESSO'
        lista = [dict(g, numero_int=n) for n, g in list(grupos.items())[:60]]

    nomes = {}
    for g in lista:
        if g['id_frigorifico'] not in nomes:
            nomes[g['id_frigorifico']] = _dados_frigorifico(g['id_frigorifico'])[0] or '-'
        g['frigorifico'] = nomes[g['id_frigorifico']]
        g['data_saida'] = _data_br(g['data_saida'])
        g['gtas'] = ', '.join(g['gtas'])

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_troca_comunicado_lista.html',
        comunicados=lista,
        id_propriedade=int(id_propriedade),
        url_animais=URL_ANIMAIS,
        url_hub=URL_HUB,
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        **_contexto_base(),
    )


# -------------------------------------------------------
# GET /produtor/saida-troca-comunicado/animais - animais do Comunicado.
# -------------------------------------------------------
@saida_troca_comunicado.route('/produtor/saida-troca-comunicado/animais')
def animais():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    if not _pode_trocar(id_propriedade):
        return _sem_permissao()
    try:
        numero = int(request.args.get('numero', ''))
    except ValueError:
        numero = 0
    url_lista = f'{URL_COMUNICADOS}?id_propriedade={int(id_propriedade)}'
    if not numero:
        return redirect(url_lista)
    id_produtor = session['id_produtor']

    with get_db_produtor(id_produtor) as db:
        gtas = (
            db.query(ComunicadoSaida)
            .filter(ComunicadoSaida.id_propriedade_origem == int(id_propriedade),
                    ComunicadoSaida.numero_comunicado == numero, ComunicadoSaida.tipo_saida == 'ABATE').all()   # v-s107
        )
        if not gtas:
            return redirect(url_lista)
        impresso = any(c.status == 'IMPRESSO' for c in gtas)
        id_frig = gtas[0].id_frigorifico
        data_saida = _data_br(gtas[0].data_saida)

        faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
        saidas = (
            db.query(SaidaAnimal)
            .filter(SaidaAnimal.id_propriedade == int(id_propriedade), SaidaAnimal.numero_comunicado == numero,
                    SaidaAnimal.tipo_saida == 'ABATE', SaidaAnimal.substituido == False,   # noqa: E712
                    SaidaAnimal.id_embarque.isnot(None))
            .order_by(SaidaAnimal.gta_saida.asc(), SaidaAnimal.sisbov.asc()).all()
        )
        lista = [{
            'id_embarque': s.id_embarque,
            'sisbov': s.sisbov,
            'manejo': s.manejo or '',
            'sexo': {'FEMEA': 'Fêmea', 'MACHO': 'Macho'}.get(s.sexo, s.sexo or '-'),
            'faixa': _faixa_em(faixas, s.nascimento, s.data_embarque),
            'peso': _formatar_kg(s.peso_saida) if s.peso_saida is not None else '',
            'gta': s.gta_saida or '',
        } for s in saidas]
        trocados = (
            db.query(SaidaAnimal.id)
            .filter(SaidaAnimal.id_propriedade == int(id_propriedade), SaidaAnimal.numero_comunicado == numero,
                    SaidaAnimal.substituido == True).count())   # noqa: E712

    mensagem = None
    ok = (request.args.get('ok') or '').strip()
    voltou = (request.args.get('voltou') or '').strip()
    if ok.isdecimal() and voltou.isdecimal():
        mensagem = f'Troca feita. O SISBOV {voltou} voltou ao rebanho e o SISBOV {ok} saiu no lugar dele.'

    frigorifico = _dados_frigorifico(id_frig)[0] or '-'
    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_troca_comunicado_animais.html',
        animais=lista,
        mensagem=mensagem,
        aviso_impresso=MSG_AVISO_IMPRESSO if impresso else None,
        trocados=trocados,
        numero_6=_numero_6(numero),
        frigorifico=frigorifico,
        data_saida=data_saida,
        id_propriedade=int(id_propriedade),
        numero=numero,
        url_trocar=URL_TROCAR,
        url_voltar=url_lista,
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        **_contexto_base(),
    )


# -------------------------------------------------------
# GET /produtor/saida-troca-comunicado/trocar - tela da troca (id = id da leitura, tb_2020).
# -------------------------------------------------------
@saida_troca_comunicado.route('/produtor/saida-troca-comunicado/trocar')
def trocar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    if not _pode_trocar(id_propriedade):
        return _sem_permissao()
    id_produtor = session['id_produtor']
    url_lista = f'{URL_COMUNICADOS}?id_propriedade={int(id_propriedade)}'

    with get_db_produtor(id_produtor) as db:
        linha = _linha_do_comunicado(db, id_propriedade, request.args.get('id', ''))
        if linha is None or _saida_ativa(db, id_propriedade, linha) is None:
            return redirect(url_lista)
        numero = linha.numero_comunicado
        impresso = _comunicado_impresso(db, id_propriedade, numero)
        faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
        raca = db.get(Raca, linha.id_raca) if linha.id_raca else None
        numero_gta = ''
        if linha.id_gta is not None:
            gta = db.get(Gta, linha.id_gta)
            numero_gta = gta.numero_gta_completo if gta else ''
        antigo = {
            'id': linha.id,
            'sisbov': linha.sisbov,
            'manejo': linha.manejo or '',
            'rfid': linha.rfid or '',
            'sexo': {'FEMEA': 'Fêmea', 'MACHO': 'Macho'}.get(linha.sexo, linha.sexo or '-'),
            'faixa': _faixa_em(faixas, linha.nascimento, linha.data_embarque),
            'raca': raca.codigo if raca else '-',
            'nascimento': _data_br(linha.nascimento),
            'peso': _formatar_kg(linha.peso_saida) if linha.peso_saida is not None else '',
            'gta': numero_gta,
        }
        data_br = _data_br(linha.data_embarque)

    avisos_topo = [f'Comunicado nº {_numero_6(numero)}: o número é mantido. O animal trocado volta para o rebanho '
                   'e o substituto sai no lugar dele. Não existe desfazer.']
    if impresso:
        avisos_topo.append(MSG_AVISO_IMPRESSO)

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_substituicao_trocar.html',
        antigo=antigo,
        id_propriedade=int(id_propriedade),
        data_embarque=data_br,
        peso_minimo=_formatar_kg(PESO_MINIMO_PADRAO),
        url_voltar=f'{URL_ANIMAIS}?id_propriedade={int(id_propriedade)}&numero={numero}',
        url_checar=URL_CHECAR,
        url_gravar=URL_GRAVAR,
        titulo_tela='Troca depois do Comunicado',
        titulo_antigo='Animal trocado (volta para o rebanho)',
        avisos_topo=avisos_topo,
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        **_contexto_base(),
    )


# -------------------------------------------------------
# POST /produtor/saida-troca-comunicado/checar - confere o substituto.
# -------------------------------------------------------
@saida_troca_comunicado.route('/produtor/saida-troca-comunicado/checar', methods=['POST'])
def checar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = (dados.get('sisbov') or '').strip()
    manejo = (dados.get('manejo') or '').strip()
    dv = (dados.get('dv') or '').strip()
    if not id_propriedade or (not sisbov and not manejo):
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    if not _pode_trocar(id_propriedade):
        return jsonify({'erro': MSG_SEM_PERMISSAO}), 403

    with get_db_produtor(session['id_produtor']) as db:
        linha = _linha_do_comunicado(db, id_propriedade, dados.get('id'))
        if linha is None or _saida_ativa(db, id_propriedade, linha) is None:
            return jsonify({'erro': MSG_COMUNICADO_NAO_ACHADO}), 400
        resultado = _avaliar_substituto(db, id_propriedade, linha, sisbov, manejo, dv)

    if 'bloqueio' in resultado:
        return jsonify({'bloqueio': True, 'mensagem': resultado['bloqueio'], 'pede_dv': bool(resultado.get('pede_dv'))})
    return jsonify({'ok': True, 'animal': resultado['ficha'], 'avisos': resultado['avisos'],
                    'categoria': resultado['categoria']})


# -------------------------------------------------------
# POST /produtor/saida-troca-comunicado/gravar - confere tudo de novo e troca.
# Tudo ou nada: uma transacao so, com a mesma trava por Propriedade do Gerar Comunicado.
# -------------------------------------------------------
@saida_troca_comunicado.route('/produtor/saida-troca-comunicado/gravar', methods=['POST'])
def gravar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = (dados.get('sisbov') or '').strip()
    aceite_fora = bool(dados.get('aceite_fora_liberacao'))
    aceite_era = bool(dados.get('aceite_era_0_12'))
    if not id_propriedade or not sisbov:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    if not _pode_trocar(id_propriedade):
        return jsonify({'erro': MSG_SEM_PERMISSAO}), 403
    peso, erro_peso = _validar_peso(dados.get('peso'))
    if erro_peso:
        return jsonify({'erro': erro_peso}), 400
    id_propriedade = int(id_propriedade)

    def _bloqueio(msg):
        return jsonify({'bloqueio': True, 'erro': msg, 'mensagem': msg}), 409

    with get_db_produtor(session['id_produtor']) as db:
        db.execute(text('SELECT pg_advisory_xact_lock(:classe, :id_propriedade)'),
                   {'classe': CLASSE_TRAVA, 'id_propriedade': id_propriedade})

        linha = _linha_do_comunicado(db, id_propriedade, dados.get('id'), travar=True)
        saida_x = _saida_ativa(db, id_propriedade, linha, travar=True) if linha is not None else None
        if linha is None or saida_x is None:
            return jsonify({'erro': MSG_COMUNICADO_NAO_ACHADO}), 400

        resultado = _avaliar_substituto(db, id_propriedade, linha, sisbov, '', '')
        if 'bloqueio' in resultado:
            return _bloqueio(resultado['bloqueio'])
        avisos = resultado['avisos']
        if avisos['fora_liberacao']['ativo'] and not aceite_fora:
            return jsonify({'erro': 'Animal fora da Liberação para Abate: marque "Responsabilidade do Produtor".'}), 400
        if avisos['era_0_12']['ativo'] and not aceite_era:
            return jsonify({'erro': 'Animal com idade ERAS de 0 a 12 meses: marque "Responsabilidade do Produtor".'}), 400

        # ---- Y: o substituto, travado ----
        animal_y = db.query(Entrada).filter(Entrada.id == resultado['animal'].id).with_for_update().first()
        if animal_y is None or animal_y.id_propriedade != id_propriedade:
            return _bloqueio('O substituto não está mais na Propriedade. Confira e tente de novo.')

        # ---- X: recupera a linha original guardada no Log da baixa ----
        sisbov_x = linha.sisbov
        dados_x = _linha_do_log(db, saida_x.id_animal, sisbov_x, id_propriedade)
        if dados_x is None:
            return _bloqueio(f'Não encontrei no Log a linha original do SISBOV {sisbov_x}. A troca não pode ser '
                             'feita por aqui. Avise a Consiste.')
        if db.query(Entrada.id).filter(or_(Entrada.id == saida_x.id_animal, Entrada.sisbov == sisbov_x)).first():
            return _bloqueio(f'O SISBOV {sisbov_x} já aparece no rebanho. Confira antes de trocar.')

        agora = datetime.now()
        id_usuario = session.get('usuario_id')
        numero = linha.numero_comunicado
        numero_6 = _numero_6(numero)
        impresso = _comunicado_impresso(db, id_propriedade, numero)
        sisbov_y = animal_y.sisbov
        id_embarque = linha.id
        data_saida = saida_x.data_saida
        gta_saida_txt = saida_x.gta_saida or ''      # guardado ANTES do commit (a sessao fecha depois)

        novos = _novos_da_leitura(db, animal_y, peso, avisos, id_usuario, agora)
        antes_completo = {c: getattr(linha, c) for c in novos}
        antes = {c: _json_valor(antes_completo[c]) for c in novos if antes_completo[c] != novos[c]}
        depois = {c: _json_valor(novos[c]) for c in novos if antes_completo[c] != novos[c]}
        entrega_y = _data_entrega(db, animal_y.id_gta_entrada)
        entrega_x = _data_entrega(db, dados_x.get('id_gta_entrada'))

        descricao = (f'Troca depois do Comunicado nº {numero_6}: SISBOV {sisbov_x} volta ao rebanho e '
                     f'SISBOV {sisbov_y} sai no lugar (GTA {saida_x.gta_saida})'
                     + (' — Comunicado já impresso: reimprimir' if impresso else ''))
        id_operacao = registrar_operacao(
            db, id_usuario=id_usuario, id_propriedade=id_propriedade, modulo=MODULO_LOG, descricao=descricao[:255])

        # ---- X volta para a tb_2001 ----
        entrada_x = _entrada_do_log(dados_x)
        db.add(entrada_x)
        db.flush()
        registrar_item(db, id_operacao, 'tb_2001', entrada_x.id, 'INSERT', None,
                       {'sisbov': sisbov_x, 'motivo': f'volta ao rebanho - troca no Comunicado {numero_6}'})

        # ---- Y sai da tb_2001 (linha inteira vai para o Log) ----
        registrar_item(db, id_operacao, 'tb_2001', animal_y.id, 'DELETE', _linha_para_dict(animal_y), None)
        retrato_y = _retrato_movimentacao(animal_y)
        db.delete(animal_y)
        db.flush()

        # ---- tb_2002: X fica como historico; nasce a linha de Y ----
        antes_x = {'substituido': False, 'substituido_em': None, 'id_usuario_substituicao': None,
                   'sisbov_substituto': None}
        saida_x.substituido = True
        saida_x.substituido_em = agora
        saida_x.id_usuario_substituicao = id_usuario
        saida_x.sisbov_substituto = sisbov_y
        registrar_item(db, id_operacao, 'tb_2002_saida_animais', saida_x.id, 'UPDATE', antes_x,
                       {'substituido': True, 'substituido_em': agora.isoformat(),
                        'id_usuario_substituicao': id_usuario, 'sisbov_substituto': sisbov_y})

        saida_y = SaidaAnimal(id_propriedade=id_propriedade, id_embarque=id_embarque, **novos)
        for campo in CAMPOS_DO_COMUNICADO:
            setattr(saida_y, campo, getattr(saida_x, campo))
        db.add(saida_y)

        # ---- tb_2020: a leitura passa a ser de Y (continua baixada, mesmo Comunicado) ----
        for campo, valor in novos.items():
            setattr(linha, campo, valor)
        registrar_item(db, id_operacao, 'tb_2020_embarque', id_embarque, 'UPDATE', antes, depois)

        # ---- tb_2017: saida de Y e retorno de X ----
        mov_y = Movimentacao(
            **retrato_y,
            gta_entrada=novos['gta_entrada'], gta_entrada_emissao=novos['gta_entrada_emissao'],
            gta_entrada_validade=novos['gta_entrada_validade'], gta_entrada_animais=novos['gta_entrada_animais'],
            entrada=entrega_y, origem_propriedade=novos['origem_propriedade'], origem_cpf_cnpj=novos['origem_cpf_cnpj'],
            tipo_saida=saida_x.tipo_saida,
            gta_saida=saida_x.gta_saida, gta_saida_emissao=saida_x.gta_saida_emissao,
            gta_saida_validade=saida_x.gta_saida_validade, gta_saida_animais=saida_x.gta_saida_animais,
            destino_propriedade=saida_x.destino_propriedade, destino_cpf_cnpj=saida_x.destino_cpf_cnpj,
            data_movimentacao=data_saida, numero_comunicado=numero_6)
        db.add(mov_y)
        mov_x = Movimentacao(
            **_retrato_movimentacao(entrada_x),
            negociacao=NEGOCIACAO_RETORNO,
            gta_entrada=saida_x.gta_entrada, gta_entrada_emissao=saida_x.gta_entrada_emissao,
            gta_entrada_validade=saida_x.gta_entrada_validade, gta_entrada_animais=saida_x.gta_entrada_animais,
            entrada=entrega_x, origem_propriedade=saida_x.origem_propriedade, origem_cpf_cnpj=saida_x.origem_cpf_cnpj,
            data_movimentacao=agora.date(), numero_comunicado=numero_6)
        db.add(mov_x)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            return _bloqueio('Não foi possível gravar a troca (registro duplicado). Confira e tente de novo.')
        registrar_item(db, id_operacao, 'tb_2002_saida_animais', saida_y.id, 'INSERT', None,
                       {'sisbov': sisbov_y, 'numero_comunicado': numero})
        registrar_item(db, id_operacao, 'tb_2017_movimentacoes', mov_y.id, 'INSERT', None,
                       {'sisbov': sisbov_y, 'numero_comunicado': numero_6})
        registrar_item(db, id_operacao, 'tb_2017_movimentacoes', mov_x.id, 'INSERT', None,
                       {'sisbov': sisbov_x, 'negociacao': NEGOCIACAO_RETORNO, 'numero_comunicado': numero_6})

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return _bloqueio('Não foi possível gravar a troca (registro duplicado). Confira e tente de novo.')

    session['caixa_troca_comunicado'] = {
        'sisbov_x': sisbov_x, 'sisbov_y': sisbov_y, 'numero': numero, 'numero_6': numero_6, 'impresso': bool(impresso),
        'gta': gta_saida_txt, 'data_saida': _data_br(data_saida),
    }
    return jsonify({
        'ok': True,
        'sisbov_antigo': sisbov_x,
        'sisbov_novo': sisbov_y,
        'url': f'{URL_CONCLUIDA}?id_propriedade={id_propriedade}&numero={numero}',
    })


# -------------------------------------------------------
# GET /produtor/saida-troca-comunicado/concluida - Caixa de Sucesso (v1.1.0). Le e apaga o resumo guardado na sessao.
# -------------------------------------------------------
@saida_troca_comunicado.route('/produtor/saida-troca-comunicado/concluida')
def concluida():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    numero = request.args.get('numero', '')
    url_animais = f'{URL_ANIMAIS}?id_propriedade={int(id_propriedade)}&numero={numero}'
    r = session.pop('caixa_troca_comunicado', None)
    if not r:
        return redirect(url_animais)               # recarregou a pagina: a caixa ja foi vista
    avisos, notas = [], []
    if r['impresso']:
        avisos.append(f'O Comunicado nº {r["numero_6"]} já foi impresso. Imprima de novo (Reimpressão) e substitua as vias já entregues.')
    else:
        notas.append(f'O Comunicado nº {r["numero_6"]} ainda não foi impresso: imprima já com a troca.')
    notas.insert(0, f'O SISBOV {r["sisbov_x"]} voltou ao rebanho. A GTA {r["gta"]} e o número do Comunicado continuam os mesmos.')
    notas.append('A troca ficou registrada no Log de Operações.')
    return render_caixa_sucesso(
        _contexto_base(), titulo='Troca feita com sucesso!', subtitulo=f'Comunicado nº {r["numero_6"]}',
        mudancas=[{'campo': 'SISBOV no Comunicado', 'antes': r['sisbov_x'], 'depois': r['sisbov_y']},
                  {'campo': 'Data de saída', 'antes': None, 'depois': r['data_saida']}],
        avisos=avisos, notas=notas,
        botoes=[{'texto': 'Trocar outro animal', 'url': url_animais, 'primario': True},
                {'texto': 'Voltar ao Hub de Saídas', 'url': URL_HUB, 'primario': False}],
        url_voltar=url_animais, titulo_pagina='Orion SISBOV — Troca feita',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\saida_troca_comunicado.py
# =========================================================
