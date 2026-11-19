# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\pesos_leitor.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-04 11:10 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.2.0
# v1.2.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (3 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     PESOS - Registrar Peso com LEITOR, no brete (Sessao 114, pacote 1). Molde: saida_leitor.py (Leitor do Abate).
#     Fluxo: Hub de Pesos -> Selecao (so a DATA da pesagem, digitada) -> Leitura (SISBOV ou Manejo) -> Gravar.
#     Cada animal grava NA HORA em tb_4003_pesos (sem Comunicado): sequencia = ultima + 1, Ganho = peso - peso anterior,
#     dias = data - data da pesagem anterior, GMD = Ganho / dias (calculados; so o Ganho fica gravado).
#
#     Regras (decisoes do Benedito, 03 e 04/11/2026):
#       - So no brete. A DATA vem da Selecao (nunca pre-preenchida; nao pode ser futura).
#       - Peso: mesma regra do brete da Entrada (superior a 100 kg e ate 1000 kg; mensagem "Peso incorreto, verifique.").
#       - Faixa de peso: SO AVISA "Atencao: Verifique o Peso" (GMD acima de 3 kg/dia ou queda de 5% ou mais em relacao
#         a ultima pesagem). A responsabilidade e do usuario: nao bloqueia, nao pede aceite.
#       - Animal que ja saiu / morto / brinco no estoque / cancelado / inexistente = ERRO GRAVE, com mensagem que orienta.
#       - Mesmo animal NAO pode ter duas pesagens na mesma data; data anterior a ultima pesagem do animal tambem barra
#         (para nao desmontar a sequencia e o Ganho).
#       - Perda de Elemento (Botton ou Brinco): fica na pesagem (tb_4003.elemento_perdido) e no animal (tb_2001.elemento_perdido).
#       - Observacoes (anomalia: bicheira, cuidado...): opcional, grava em tb_4003.observacao.
#       - TODO erro/tentativa recusada fica gravado em tb_4007_pesagem_inconformes (lista "Inconformes" no Hub de Pesos).
#       - CORRECAO so no brete, na propria Leitura: o X da lista Geral exclui a pesagem e o animal e lido de novo.
#         So vale ate a proxima pesagem do animal (so a ULTIMA pesagem dele pode ser excluida) e so de pesagem feita aqui
#         (a pesagem da Brincagem nao e mexida). Nao e dado de auditoria: sem Log, fica uma linha no log do servidor.
#     Fora desta versao: Bastao (proximo), Consulta/Conferidos (pacote 3), evento de peso no blockchain (pacote 4),
#     ligacao da perda de elemento com o Abate (o brete do Abate confere de novo).
#
#     v1.0.0: Criacao (Sessao 114, 04/11/2026, 11:10 -03).
#     v1.1.0: Sessao 114 (04/11/2026, 14:00 -03) - Ficha leva dias_propriedade (data da pesagem - data de inclusao do animal). REVERSAO: .bak_antes_s114_dias.
#     REVERSAO: remover este arquivo, os 3 templates pesos_*.html, o registro em app.py, o Hub 'pesos' e as linhas de
#     permissoes.py; o SQL Tabelas\criar_pesos_s114.sql traz o roteiro de reversao do banco.
# =========================================================

from datetime import date
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, PropriedadeProdutor, Produtor
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.models.tb_4007_pesagem_inconformes import PesagemInconforme
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.models.usuario import Usuario
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.saida_leitor import (
    _propriedade_do_usuario, _data_br, _ler_data_br, _formatar_kg, _faixa_idade, _dv_incorreto,
    TAMANHO_MANEJO, MENSAGEM_DV_INCORRETO, MENSAGEM_SISBOV_TAMANHO, MENSAGEM_MANEJO_INCORRETO,
    MENSAGEM_DV_MANEJO_INCORRETO, MENSAGEM_NAO_ENCONTRADO, MENSAGEM_BRINCO_NO_ESTOQUE,
    MENSAGEM_BRINCO_CANCELADO, MENSAGEM_MANEJO_PEDE_DV, MENSAGEM_MANEJO_DUPLICADO,
)
from backend.utils.animal_saiu import mensagem_animal_saiu, texto_animal_saiu
from backend.utils.conferencia_compra import ler_peso_brete
from backend.utils.pesagem import registrar_pesagem
from backend.utils.multitenant import get_db_produtor
from backend.utils.regras_sisbov import MODELO_SISBOV_ANTIGO, TAMANHO_SISBOV, modelo_do_sisbov


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
pesos_leitor = Blueprint('pesos_leitor', __name__)


@pesos_leitor.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


# -------------------------------------------------------
# Constantes
# -------------------------------------------------------
URL_HUB            = '/produtor/hub-novo/pesos'
URL_INICIAR        = '/produtor/pesos-leitor/iniciar'
URL_SELECAO        = '/produtor/pesos-leitor/selecao'
URL_INCONF_INICIAR = '/produtor/pesos-inconformes/iniciar'
URL_INCONF_LISTA   = '/produtor/pesos-inconformes/lista'

ORIGEM_PESO        = 'BRETE_PESO'        # tb_4003.origem das pesagens feitas aqui
GMD_AVISO          = 3.0                 # kg/dia: acima disso so avisa
QUEDA_AVISO_PCT    = 5.0                 # queda (%) em relacao a ultima pesagem: a partir disso so avisa
ELEMENTOS          = (('BOTTON', 'Botton'), ('BRINCO', 'Brinco'))
CODIGOS_ELEMENTO   = tuple(c for c, _ in ELEMENTOS)
LIMITE_INCONFORMES = 300

MENSAGENS_ERRO_SELECAO = {
    'data':   'Data da Pesagem incorreta. Digite no formato dd/mm/aaaa.',
    'futura': 'A Data da Pesagem não pode ser futura.',
}


def _negado():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect(URL_INICIAR)
    return redirecionar_home()


# -------------------------------------------------------
# Inconformes: toda tentativa recusada fica gravada (decisao do Benedito).
# Nunca derruba a tela: se nao conseguir gravar, so desfaz e segue.
# -------------------------------------------------------
def _registrar_inconforme(db, id_propriedade, data_pesagem, sisbov, manejo, peso_txt, motivo):
    try:
        db.add(PesagemInconforme(
            id_propriedade=int(id_propriedade),
            id_usuario=session.get('usuario_id'),
            sisbov=(sisbov or '')[:40] or None,
            manejo=(manejo or '')[:10] or None,
            data_pesagem=data_pesagem,
            peso_digitado=(peso_txt or '')[:20] or None,
            motivo=(motivo or '')[:200],
        ))
        db.commit()
    except Exception:
        db.rollback()


# -------------------------------------------------------
# Lista "Geral" da data: pesagens feitas AQUI (origem BRETE_PESO) nesta data.
# pode_excluir = e a ultima pesagem do animal (regra: so ate a proxima pesagem).
# -------------------------------------------------------
def _contar_gravados_na_data(db, id_propriedade, data_pesagem):
    return (
        db.query(func.count(Peso.id))
        .filter(Peso.id_propriedade == int(id_propriedade), Peso.origem == ORIGEM_PESO, Peso.data_pesagem == data_pesagem)
        .scalar()
    ) or 0


def _lidos_da_data(db, id_propriedade, data_pesagem):
    linhas = (
        db.query(Peso)
        .filter(Peso.id_propriedade == int(id_propriedade), Peso.origem == ORIGEM_PESO, Peso.data_pesagem == data_pesagem)
        .order_by(Peso.id.desc())
        .all()
    )
    if not linhas:
        return []
    sisbovs = [l.sisbov for l in linhas]
    ficha = {s: (m or '', x or '') for s, m, x in
             db.query(Entrada.sisbov, Entrada.manejo, Entrada.sexo).filter(Entrada.sisbov.in_(sisbovs)).all()}
    maximas = dict(
        db.query(Peso.sisbov, func.max(Peso.sequencia)).filter(Peso.sisbov.in_(sisbovs)).group_by(Peso.sisbov).all()
    )
    resultado = []
    for l in linhas:
        manejo, sexo = ficha.get(l.sisbov, ('', ''))
        resultado.append({
            'sisbov': l.sisbov,
            'manejo': manejo,
            'sexo': str(sexo or ''),
            'peso': _formatar_kg(l.peso),
            'ganho': _formatar_kg(l.ganho_peso) if l.ganho_peso is not None else '',
            'hora': l.hora_pesagem.strftime('%H:%M') if l.hora_pesagem else '',
            'pode_excluir': maximas.get(l.sisbov) == l.sequencia,
        })
    return resultado


# -------------------------------------------------------
# Animal que NAO esta em tb_2001: morreu, ja saiu, esta no estoque de brincos, cancelado ou nunca existiu.
# Devolve o TEXTO (a tentativa vira Inconforme no chamador, depois de montar o texto).
# -------------------------------------------------------
def _mensagem_sem_animal(db, id_propriedade, sisbov):
    saida = (
        db.query(SaidaAnimal)
        .filter(SaidaAnimal.sisbov == sisbov)
        .order_by(SaidaAnimal.data_saida.desc(), SaidaAnimal.id.desc())
        .first()
    )
    if saida is None:
        brinco = (
            db.query(EntradaBrincoRfid)
            .filter(EntradaBrincoRfid.sisbov == sisbov, EntradaBrincoRfid.id_propriedade == int(id_propriedade))
            .first()
        )
        status = (brinco.status or '').strip().upper() if brinco is not None else None
        if brinco is not None and status == '':
            return MENSAGEM_BRINCO_NO_ESTOQUE
        if brinco is not None and status == 'CANCELADO':
            return MENSAGEM_BRINCO_CANCELADO
        return MENSAGEM_NAO_ENCONTRADO
    if saida.tipo_saida == 'MORTE':
        return (f'Brinco de animal que morreu em {_data_br(saida.data_saida)}. '
                'Este brinco não pode ser usado.')
    return texto_animal_saiu(saida)


# -------------------------------------------------------
# Busca o animal pelo SISBOV ou pelo Manejo (+ DV nos brincos 105). Devolve (animal, bloqueio).
# -------------------------------------------------------
def _buscar_animal(db, id_propriedade, sisbov, manejo, dv):
    if sisbov:
        if len(sisbov) != TAMANHO_SISBOV or not (sisbov.isascii() and sisbov.isdecimal()):
            return None, MENSAGEM_SISBOV_TAMANHO
        if _dv_incorreto(sisbov):
            return None, MENSAGEM_DV_INCORRETO
        animal = (
            db.query(Entrada)
            .filter(Entrada.sisbov == sisbov, Entrada.id_propriedade == int(id_propriedade))
            .first()
        )
        if animal is None:
            return None, _mensagem_sem_animal(db, id_propriedade, sisbov)
        return animal, None

    if len(manejo) != TAMANHO_MANEJO or not (manejo.isascii() and manejo.isdecimal()):
        return None, MENSAGEM_MANEJO_INCORRETO
    if dv and not (len(dv) == 1 and dv.isascii() and dv.isdecimal()):
        return None, MENSAGEM_DV_MANEJO_INCORRETO
    candidatos = (
        db.query(Entrada)
        .filter(Entrada.id_propriedade == int(id_propriedade), Entrada.manejo == manejo)
        .all()
    )
    if dv:
        candidatos = [a for a in candidatos
                      if modelo_do_sisbov(a.sisbov) != MODELO_SISBOV_ANTIGO or a.sisbov[-1] == dv]
    if not candidatos:
        return None, mensagem_animal_saiu(db, id_propriedade, manejo=manejo) or MENSAGEM_NAO_ENCONTRADO
    if len(candidatos) > 1:
        tem_antigo = any(modelo_do_sisbov(a.sisbov) == MODELO_SISBOV_ANTIGO for a in candidatos)
        if tem_antigo and not dv:
            return None, MENSAGEM_MANEJO_PEDE_DV
        return None, MENSAGEM_MANEJO_DUPLICADO
    return candidatos[0], None


# -------------------------------------------------------
# Validacao completa de UM animal para a pesagem (usada no checar() e, de novo, no gravar()).
# Devolve {'bloqueio': texto, 'pede_dv': bool} ou {'animal': Entrada, 'ficha': {...}, 'ultimo': Peso|None}
# -------------------------------------------------------
def _validar(db, id_propriedade, data_pesagem, sisbov, manejo, dv):
    animal, bloqueio = _buscar_animal(db, id_propriedade, sisbov, manejo, dv)
    if bloqueio:
        return {'bloqueio': bloqueio, 'pede_dv': bloqueio == MENSAGEM_MANEJO_PEDE_DV}

    ultimo = (
        db.query(Peso).filter(Peso.sisbov == animal.sisbov).order_by(Peso.sequencia.desc()).first()
    )
    mesma_data = (
        db.query(Peso).filter(Peso.sisbov == animal.sisbov, Peso.data_pesagem == data_pesagem).first()
    )
    if mesma_data is not None:
        if mesma_data.origem == ORIGEM_PESO:
            return {'bloqueio': f'Este animal já foi pesado em {_data_br(data_pesagem)}. '
                                'Para refazer, exclua a pesagem pela lista Geral.'}
        return {'bloqueio': f'Este animal já tem pesagem em {_data_br(data_pesagem)} (feita na Brincagem). '
                            'Essa pesagem não pode ser refeita aqui.'}
    if ultimo is not None and data_pesagem < ultimo.data_pesagem:
        return {'bloqueio': f'A Data da Pesagem é anterior à última pesagem deste animal ({_data_br(ultimo.data_pesagem)}). '
                            'Confira a data da Seleção.'}

    faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
    dias_idade = (data_pesagem - animal.nascimento).days if animal.nascimento else None
    raca = db.get(Raca, animal.id_raca) if animal.id_raca else None
    dias_anterior = (data_pesagem - ultimo.data_pesagem).days if ultimo is not None else None

    ficha = {
        'sisbov': animal.sisbov,
        'manejo': animal.manejo or '',
        'rfid': animal.rfid or '',
        'sexo': str(animal.sexo or ''),
        'raca': raca.codigo if raca else '',
        'nascimento': _data_br(animal.nascimento),
        'idade_meses': _faixa_idade(faixas, dias_idade),
        'liberacao_abate': _data_br(animal.liberacao_abate),
        'lote': animal.lote or '',
        'dias_propriedade': ((data_pesagem - animal.data_inclusao).days if animal.data_inclusao else ''),   # v1.1.0
        'peso_anterior': float(ultimo.peso) if ultimo is not None else None,
        'data_anterior': _data_br(ultimo.data_pesagem) if ultimo is not None else '',
        'dias': dias_anterior,
        'elemento_perdido': (getattr(animal, 'elemento_perdido', None) or ''),
    }
    return {'animal': animal, 'ficha': ficha, 'ultimo': ultimo}


# -------------------------------------------------------
# Rota: GET /produtor/pesos-leitor/iniciar - ponto de partida (escolhe a Propriedade).
# -------------------------------------------------------
def _iniciar_generico(titulo, proximo):
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista, erro=erro, titulo=titulo, proximo=proximo,
            campo_propriedade='id_propriedade', voltar=URL_HUB,
            usuario_nome=session.get('usuario_nome'), usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A', nome_sistema='Orion SISBOV', menu_ativo='pesagens',
        )

    if len(pares) == 0:
        return _tela_selecionar([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')

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

    return _tela_selecionar(pares, None)


@pesos_leitor.route('/produtor/pesos-leitor/iniciar')
def iniciar():
    return _iniciar_generico('Leitor de Peso — Selecionar Propriedade', URL_SELECAO)


# -------------------------------------------------------
# Rota: GET /produtor/pesos-leitor/selecao - Selecao (so a Data da Pesagem).
# -------------------------------------------------------
@pesos_leitor.route('/produtor/pesos-leitor/selecao')
def selecao():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    url_voltar = URL_INICIAR if (len(pares) > 1 and resolver_fazenda_em_uso(pares) is None) else URL_HUB

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
        nome_produtor = None
        if propriedade:
            vinculo = db.query(PropriedadeProdutor).filter_by(
                id_propriedade=propriedade.id, id_produtor=session['id_produtor'], data_fim=None
            ).first()
            if vinculo:
                produtor = db.get(Produtor, vinculo.id_produtor)
                if produtor:
                    nome_produtor = produtor.nome

    # Ultimas datas pesadas nesta Propriedade (clicar usa a data).
    try:
        with get_db_produtor(session['id_produtor']) as db_prod:
            linhas = (
                db_prod.query(Peso.data_pesagem, func.count(Peso.id))
                .filter(Peso.id_propriedade == int(id_propriedade), Peso.origem == ORIGEM_PESO)
                .group_by(Peso.data_pesagem)
                .order_by(Peso.data_pesagem.desc())
                .limit(8)
                .all()
            )
            recentes = [{'data': _data_br(d), 'quantidade': int(q)} for d, q in linhas]
    except Exception:
        recentes = []

    return render_template(
        'produtor/pesos_leitor_selecao.html',
        erro=MENSAGENS_ERRO_SELECAO.get(request.args.get('erro', '')),
        propriedade=propriedade,
        nome_produtor=nome_produtor,
        id_propriedade=id_propriedade,
        url_voltar=url_voltar,
        recentes=recentes,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='pesagens',
    )


# -------------------------------------------------------
# Rota: GET /produtor/pesos-leitor/leitura - Tela de Leitura.
# -------------------------------------------------------
@pesos_leitor.route('/produtor/pesos-leitor/leitura')
def leitura():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()

    base = f'{URL_SELECAO}?id_propriedade={id_propriedade}'
    data_pesagem = _ler_data_br(request.args.get('data_pesagem', ''))
    if data_pesagem is None:
        return redirect(f'{base}&erro=data')
    if data_pesagem > date.today():
        return redirect(f'{base}&erro=futura')

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))

    with get_db_produtor(session['id_produtor']) as db:
        total_gravados = _contar_gravados_na_data(db, id_propriedade, data_pesagem)
        lidos = _lidos_da_data(db, id_propriedade, data_pesagem)

    return render_template(
        'produtor/pesos_leitor_leitura.html',
        propriedade=propriedade,
        id_propriedade=id_propriedade,
        data_pesagem=_data_br(data_pesagem),
        total_gravados=total_gravados,
        lidos=lidos,
        elementos=ELEMENTOS,
        gmd_aviso=GMD_AVISO,
        queda_pct=QUEDA_AVISO_PCT,
        url_selecao=base,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='pesagens',
    )


# -------------------------------------------------------
# Rota: POST /produtor/pesos-leitor/checar (AJAX) - confere o animal assim que o SISBOV e lido
# (ou o Manejo digitado). Bloqueio vira Inconforme (menos o pedido de DV, que nao e erro).
# -------------------------------------------------------
@pesos_leitor.route('/produtor/pesos-leitor/checar', methods=['POST'])
def checar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = (dados.get('sisbov') or '').strip()
    manejo = (dados.get('manejo') or '').strip()
    dv     = (dados.get('dv') or '').strip()
    data_pesagem = _ler_data_br(dados.get('data_pesagem'))

    if not id_propriedade or (not sisbov and not manejo) or data_pesagem is None:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou. Volte ao Hub de Pesos e abra de novo.'}), 403

    with get_db_produtor(session['id_produtor']) as db:
        resultado = _validar(db, id_propriedade, data_pesagem, sisbov, manejo, dv)
        if 'bloqueio' in resultado:
            mensagem = resultado['bloqueio']
            pede_dv = bool(resultado.get('pede_dv'))
            if not pede_dv:
                _registrar_inconforme(db, id_propriedade, data_pesagem, sisbov, manejo, None, mensagem)
            return jsonify({'bloqueio': True, 'mensagem': mensagem, 'pede_dv': pede_dv})
        ficha = resultado['ficha']

    return jsonify({'ok': True, 'animal': ficha, 'gmd_aviso': GMD_AVISO, 'queda_pct': QUEDA_AVISO_PCT})


# -------------------------------------------------------
# Rota: POST /produtor/pesos-leitor/gravar (AJAX) - grava a pesagem em tb_4003_pesos.
# Confere TUDO de novo no servidor. Peso fora da regra vira Inconforme.
# -------------------------------------------------------
@pesos_leitor.route('/produtor/pesos-leitor/gravar', methods=['POST'])
def gravar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = (dados.get('sisbov') or '').strip()
    data_pesagem = _ler_data_br(dados.get('data_pesagem'))
    peso_txt = str(dados.get('peso') or '').strip()
    elemento = (dados.get('elemento_perdido') or '').strip().upper()
    observacao = (dados.get('observacao') or '').strip()

    if not id_propriedade or not sisbov or data_pesagem is None:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou. Volte ao Hub de Pesos e abra de novo.'}), 403
    if data_pesagem > date.today():
        return jsonify({'erro': MENSAGENS_ERRO_SELECAO['futura']}), 400
    if elemento and elemento not in CODIGOS_ELEMENTO:
        return jsonify({'erro': 'Elemento perdido incorreto.'}), 400
    if len(observacao) > 300:
        return jsonify({'erro': 'Observações com mais de 300 caracteres.'}), 400

    with get_db_produtor(session['id_produtor']) as db:
        resultado = _validar(db, id_propriedade, data_pesagem, sisbov, '', '')
        if 'bloqueio' in resultado:
            mensagem = resultado['bloqueio']
            _registrar_inconforme(db, id_propriedade, data_pesagem, sisbov, '', peso_txt, mensagem)
            return jsonify({'bloqueio': True, 'mensagem': mensagem, 'erro': mensagem}), 409

        peso_valor, erro_peso = ler_peso_brete(peso_txt)
        if erro_peso:
            _registrar_inconforme(db, id_propriedade, data_pesagem, sisbov, resultado['animal'].manejo, peso_txt, f'Peso recusado: {erro_peso}')
            return jsonify({'erro': erro_peso}), 400

        animal = resultado['animal']
        ultimo = resultado['ultimo']
        peso = Decimal(str(peso_valor)).quantize(Decimal('0.01'))
        dias = (data_pesagem - ultimo.data_pesagem).days if ultimo is not None else None

        # Funcao COMPARTILHADA (sequencia, ganho e evento PESAGEM do blockchain, se o Produtor usa).
        try:
            pesagem = registrar_pesagem(
                db, id_propriedade, animal.sisbov, animal.rfid, data_pesagem, peso,
                ((data_pesagem - animal.nascimento).days if animal.nascimento else None),
                animal.lote, ORIGEM_PESO, session.get('usuario_id'), observacao=(observacao or None),
            )
            if elemento:
                pesagem.elemento_perdido = elemento
                animal.elemento_perdido = elemento   # fica tambem no animal (o Abate confere de novo)
            db.flush()
        except IntegrityError:
            db.rollback()
            mensagem = 'Pesagem repetida para este animal. Leia o brinco de novo.'
            _registrar_inconforme(db, id_propriedade, data_pesagem, sisbov, '', peso_txt, mensagem)
            return jsonify({'bloqueio': True, 'mensagem': mensagem, 'erro': mensagem}), 409

        ganho = pesagem.ganho_peso
        total_gravados = _contar_gravados_na_data(db, id_propriedade, data_pesagem)
        hora_txt = pesagem.hora_pesagem.strftime('%H:%M')
        manejo_txt = animal.manejo or ''
        sexo_txt = str(animal.sexo or '')
        ganho_txt = _formatar_kg(ganho) if ganho is not None else ''
        gmd_txt = ''
        if ganho is not None and dias and dias > 0:
            gmd_txt = f'{(ganho / Decimal(dias)):.3f}'.replace('.', ',')
        peso_fmt = _formatar_kg(peso)
        db.commit()

    return jsonify({
        'sucesso': True,
        'mensagem': 'Gravação Efetuada com Sucesso',
        'sisbov': sisbov,
        'manejo': manejo_txt,
        'sexo': sexo_txt,
        'peso': peso_fmt,
        'ganho': ganho_txt,
        'gmd': gmd_txt,
        'hora': hora_txt,
        'pode_excluir': True,
        'total_gravados': total_gravados,
    })


# -------------------------------------------------------
# Rota: POST /produtor/pesos-leitor/excluir-pesagem (AJAX) - X da lista Geral.
# CORRECAO no brete: exclui a pesagem e o animal e lido de novo. So a ULTIMA pesagem do animal,
# so de pesagem feita aqui (BRETE_PESO), nesta data. A perda de elemento volta ao que era antes.
# Nao e dado de auditoria (decisao do Benedito): sem Log, so uma linha no log do servidor.
# -------------------------------------------------------
@pesos_leitor.route('/produtor/pesos-leitor/excluir-pesagem', methods=['POST'])
def excluir_pesagem():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = (dados.get('sisbov') or '').strip()
    data_pesagem = _ler_data_br(dados.get('data_pesagem'))
    if not id_propriedade or not sisbov or data_pesagem is None:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou.'}), 403

    with get_db_produtor(session['id_produtor']) as db:
        linha = (
            db.query(Peso)
            .filter(Peso.id_propriedade == int(id_propriedade), Peso.sisbov == sisbov,
                    Peso.data_pesagem == data_pesagem, Peso.origem == ORIGEM_PESO)
            .first()
        )
        if linha is None:
            return jsonify({'erro': 'Pesagem não encontrada (já foi excluída).'}), 404
        maxima = db.query(func.max(Peso.sequencia)).filter(Peso.sisbov == sisbov).scalar()
        if maxima != linha.sequencia:
            return jsonify({'erro': 'Este animal já tem uma pesagem mais nova. Só a última pesagem pode ser excluída.'}), 409

        tinha_elemento = linha.elemento_perdido
        db.delete(linha)
        db.flush()
        if tinha_elemento:
            # volta o animal para o ultimo elemento perdido registrado em pesagem anterior (ou nenhum)
            anterior = (
                db.query(Peso.elemento_perdido)
                .filter(Peso.sisbov == sisbov, Peso.elemento_perdido.isnot(None))
                .order_by(Peso.sequencia.desc())
                .first()
            )
            animal = db.query(Entrada).filter(Entrada.sisbov == sisbov, Entrada.id_propriedade == int(id_propriedade)).first()
            if animal is not None:
                animal.elemento_perdido = anterior[0] if anterior else None
        total_gravados = _contar_gravados_na_data(db, id_propriedade, data_pesagem)
        db.commit()

    try:
        from flask import current_app
        current_app.logger.info('EXCLUIR PESAGEM: produtor=%s propriedade=%s sisbov=%s data=%s usuario=%s',
                                session.get('id_produtor'), id_propriedade, sisbov, dados.get('data_pesagem'), session.get('usuario_id'))
    except Exception:
        pass
    return jsonify({'sucesso': True, 'total_gravados': total_gravados})


# -------------------------------------------------------
# INCONFORMES (Hub de Pesos): lista das tentativas recusadas / erros, da mais nova para a mais antiga.
# Filtro opcional por data (dd/mm/aaaa) = dia da tentativa. Tela de CONSULTA (so le).
# -------------------------------------------------------
@pesos_leitor.route('/produtor/pesos-inconformes/iniciar')
def inconformes_iniciar():
    return _iniciar_generico('Inconformes dos Pesos — Selecionar Propriedade', URL_INCONF_LISTA)


@pesos_leitor.route('/produtor/pesos-inconformes/lista')
def inconformes():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()

    filtro_txt = (request.args.get('data', '') or '').strip()
    filtro = _ler_data_br(filtro_txt) if filtro_txt else None
    erro = 'Data incorreta. Digite no formato dd/mm/aaaa.' if (filtro_txt and filtro is None) else None

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    url_voltar = URL_INCONF_INICIAR if (len(pares) > 1 and resolver_fazenda_em_uso(pares) is None) else URL_HUB

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))

    itens = []
    total = 0
    with get_db_produtor(session['id_produtor']) as db:
        q = db.query(PesagemInconforme).filter(PesagemInconforme.id_propriedade == int(id_propriedade))
        if filtro is not None:
            q = q.filter(func.date(PesagemInconforme.criado_em) == filtro)
        total = q.count()
        linhas = q.order_by(PesagemInconforme.id.desc()).limit(LIMITE_INCONFORMES).all()
        ids_usuarios = {l.id_usuario for l in linhas if l.id_usuario}
        itens_brutos = [{
            'quando': l.criado_em.strftime('%d/%m/%Y %H:%M') if l.criado_em else '',
            'data_pesagem': _data_br(l.data_pesagem),
            'sisbov': l.sisbov or '',
            'manejo': l.manejo or '',
            'peso': l.peso_digitado or '',
            'motivo': l.motivo or '',
            'id_usuario': l.id_usuario,
        } for l in linhas]

    nomes = {}
    if ids_usuarios:
        with Session(engine) as db:
            nomes = {i: n for i, n in db.query(Usuario.id, Usuario.nome).filter(Usuario.id.in_(ids_usuarios)).all()}
    for item in itens_brutos:
        item['usuario'] = nomes.get(item['id_usuario'], '')
        itens.append(item)

    return render_template(
        'produtor/pesos_inconformes_lista.html',
        erro=erro,
        propriedade=propriedade,
        id_propriedade=id_propriedade,
        filtro=filtro_txt,
        itens=itens,
        total=total,
        limite=LIMITE_INCONFORMES,
        url_voltar=url_voltar,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='pesagens',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\pesos_leitor.py
# =========================================================
