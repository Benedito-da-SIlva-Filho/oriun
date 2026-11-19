# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\saida_bastao.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-17 12:35 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.3.0
# v1.3.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.2.0: Sessao 120 (2026-11-10 13:40 -03) - Selecao do Bastao do Abate separa animais livres x vinculados a GTA (Regra de Ouro #67). REVERSAO: .bak_antes_s120_livres_abate.
#
# DESCRICAO:
#     Leitor do Abate com Bastao (Sessao 099) - leitura dos animais que embarcam,
#     no brete, com o bastao que le o RFID (chip). Tela PROPRIA; o Leitor do Abate
#     (saida_leitor.py) fica como esta. Navegacao: Home -> card "Saidas" -> Hub de
#     Saidas (hub_entrada_agrupado.py, slug 'saida') -> card "Leitor do Abate com
#     Bastao".
#
#     REUSO (peca unica): toda a conferencia do animal (_validar_leitura: DV, animal
#     fora da Propriedade, brinco repetido, sexo, liberacao, avisos de
#     Responsabilidade do Produtor) e os utilitarios vem de saida_leitor.py. Aqui
#     entra so o que o Bastao tem de novo: achar o animal pelo RFID.
#
#     FLUXO (3 telas, igual ao Leitor do Abate):
#       1. /produtor/saida-bastao/iniciar - resolve Propriedade E Produtor.
#       2. /produtor/saida-bastao/selecao - Data Leitura, Sexo e Peso Minimo.
#       3. /produtor/saida-bastao/leitura - cursor sempre no RFID. O bastao le o
#          RFID (15 digitos): se o animal ja tem esse RFID cadastrado nesta
#          Propriedade, o Orion acha o animal sozinho (SISBOV e Manejo vem
#          preenchidos) e segue o fluxo normal (avisos, Elemento, Lote, Peso,
#          Gravar). RFID que nao existe nesta Propriedade: mensagem vermelha, e o
#          brete pode seguir pelo SISBOV ou pelo Manejo na mesma tela (animal sem
#          RFID cadastrado, ou chip que falhou).
#
#     REGRAS NOVAS DO BASTAO (Benedito, 17/10/2026):
#       - RFID cadastrado -> acha o animal sozinho, sem ler o codigo de barras.
#       - RFID que nao existe no Produtor -> trava com mensagem vermelha. Se o
#         RFID e de animal que ja saiu ou morreu, a mensagem e a mesma do Leitor
#         (e a tentativa de brinco de morto fica em tb_5003).
#       - RFID repetido em mais de um animal da Propriedade -> trava (erro de
#         cadastro; avisar a Consiste).
#       - Elemento (opcional): vazio = o animal tem brinco e botton. Pelo bastao
#         a lista oferece BRINCO e BOTTON (o brete escolhe); pelo SISBOV
#         digitado, so BOTTON; pelo Manejo, so BRINCO (igual ao Leitor).
#
#     A LEITURA NAO DA BAIXA: grava so em tb_2020_embarque (sts=False), exatamente
#     como o Leitor do Abate. O brinco repetido (leitura em aberto) usa a MESMA rota
#     excluir_antiga do Leitor (saida_leitor.excluir_antiga).
#
#     v1.0.0: Criacao (Sessao 099).
#     v1.1.0: Sessao 110 (31/10/2026, 31/10/2026, 11:36 -03) - RFID de brinco que esta no estoque de brincos (tb_7017, status vazio) diz 'Brinco está no estoque.'; CANCELADO diz que foi cancelado (antes: 'RFID nao encontrado'). REVERSAO: .bak_antes_s110_rfid_estoque.
#     v1.0.1: Sessao 107 (28/10/2026, 09:25 -03) - TRANSFERENCIA (pacote 2): a lista de leituras em aberto da Selecao passa a contar SO tipo_saida = ABATE.
#             Nenhuma outra mudanca. REVERSAO: .bak_antes_s107.
#     v1.1.1: Sessao 114 (04/11/2026, 10:37 -03) - Abate: mensagem de peso abaixo do minimo vira "Peso incorreto, verifique.". Regra do Peso Minimo nao mudou.  REVERSAO: .bak_antes_s114_peso.
# =========================================================

from datetime import datetime, date
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, PropriedadeProdutor, Produtor
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4001_gta import Gta
from backend.utils.leituras_vinculo import resumo_abertas, numeros_gta, marcar_gtas_atendidas   # s120 - Regra de Ouro #67
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid   # v1.1.0
from backend.models.tb_parceiros import Parceiro
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from sqlalchemy import func
from backend.routers.saida_leitor import (
    MENSAGEM_JA_CONFERIDO, MENSAGENS_ERRO_SELECAO,
    PESO_MINIMO_PADRAO, SEXOS, CODIGOS_SEXO, TIPO_SAIDA_ABATE, URL_HUB,
    _propriedade_do_usuario, _data_br, _ler_data_br, _ler_decimal,
    _formatar_kg, _contar_gravados_na_data, _lidos_da_data, _validar_leitura,
    _mensagem_sem_animal, MENSAGEM_BRINCO_NO_ESTOQUE, MENSAGEM_BRINCO_CANCELADO,
)


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
saida_bastao = Blueprint('saida_bastao', __name__)


@saida_bastao.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


# -------------------------------------------------------
# Constantes
# -------------------------------------------------------
URL_INICIAR = '/produtor/saida-bastao/iniciar'
URL_SELECAO = '/produtor/saida-bastao/selecao'
VOLTAR_SELECIONAR_PROPRIEDADE = URL_HUB

TAMANHO_RFID = 15

# Elemento: so o que o brete escolhe (vazio = tem os dois). BASTAO oferece os dois.
ELEMENTOS_POR_VIA = {
    'BASTAO': ('BRINCO', 'BOTTON'),
    'LEITOR': ('BOTTON',),
    'MANEJO': ('BRINCO',),
}

MENSAGEM_RFID_TAMANHO = f'O RFID deve ter {TAMANHO_RFID} dígitos numéricos.'
MENSAGEM_RFID_NAO_ENCONTRADO = ('RFID não encontrado nesta Propriedade. '
                                'Leia o código de barras (SISBOV) ou use o Manejo.')
MENSAGEM_RFID_DUPLICADO = ('Este RFID foi encontrado em mais de um animal desta Propriedade. '
                           'Leia o código de barras (SISBOV) ou use o Manejo. Se continuar, avise a Consiste.')


# -------------------------------------------------------
# Acha o animal pelo RFID. Devolve (animal, mensagem_de_bloqueio).
# -------------------------------------------------------
def _buscar_animal_por_rfid(db, id_propriedade, rfid):
    if len(rfid) != TAMANHO_RFID or not (rfid.isascii() and rfid.isdecimal()):
        return None, MENSAGEM_RFID_TAMANHO
    candidatos = (
        db.query(Entrada)
        .filter(Entrada.id_propriedade == int(id_propriedade), Entrada.rfid == rfid)
        .all()
    )
    if len(candidatos) == 1:
        return candidatos[0], None
    if len(candidatos) > 1:
        return None, MENSAGEM_RFID_DUPLICADO
    # nao esta mais em tb_2001: se saiu ou morreu, usa a mesma mensagem do Leitor
    saida = (
        db.query(SaidaAnimal)
        .filter(SaidaAnimal.rfid == rfid)
        .order_by(SaidaAnimal.data_saida.desc(), SaidaAnimal.id.desc())
        .first()
    )
    if saida is not None and saida.sisbov:
        return None, _mensagem_sem_animal(db, id_propriedade, saida.sisbov)
    # v1.1.0 - nao saiu: ve se o RFID e de um brinco do estoque (tb_7017, status vazio) ou cancelado
    brinco = (
        db.query(EntradaBrincoRfid)
        .filter(EntradaBrincoRfid.rfid == rfid, EntradaBrincoRfid.id_propriedade == int(id_propriedade))
        .first()
    )
    if brinco is not None:
        status = (brinco.status or '').strip().upper()
        if status == '':
            return None, MENSAGEM_BRINCO_NO_ESTOQUE
        if status == 'CANCELADO':
            return None, MENSAGEM_BRINCO_CANCELADO
    return None, MENSAGEM_RFID_NAO_ENCONTRADO


# -------------------------------------------------------
# Rota: GET /produtor/saida-bastao/iniciar - ponto de partida.
# -------------------------------------------------------
@saida_bastao.route('/produtor/saida-bastao/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista,
            erro=erro,
            titulo='Leitor do Abate com Bastão — Selecionar Propriedade',
            proximo=URL_SELECAO,
            campo_propriedade='id_propriedade',
            voltar=VOLTAR_SELECIONAR_PROPRIEDADE,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='saidas',
        )

    if len(pares) == 0:
        return _tela_selecionar([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')

    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{URL_SELECAO}?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_SELECAO}?id_propriedade={par.id_propriedade}')

    return _tela_selecionar(pares, None)


# -------------------------------------------------------
# Rota: GET /produtor/saida-bastao/selecao - Tela 02.
# -------------------------------------------------------
@saida_bastao.route('/produtor/saida-bastao/selecao')
def selecao():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado_bastao()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        url_voltar = URL_INICIAR
    else:
        url_voltar = URL_HUB

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

    # Leituras em aberto (sem Comunicado), uma linha por data (as mesmas do Leitor do Abate).
    try:
        with get_db_produtor(session['id_produtor']) as db_prod:
            resumo = resumo_abertas(db_prod, id_propriedade, TIPO_SAIDA_ABATE)   # s120 - livres x vinculadas
            abertas = [{'data': _data_br(r['data']), 'quantidade': r['livres'] + r['vinculados'], 'livres': r['livres'], 'vinculados': r['vinculados'], 'gtas': r['gtas_txt']} for r in resumo]
    except Exception:
        abertas = []

    return render_template(
        'produtor/saida_bastao_selecao.html',
        erro=MENSAGENS_ERRO_SELECAO.get(request.args.get('erro', '')),
        propriedade=propriedade,
        nome_produtor=nome_produtor,
        id_propriedade=id_propriedade,
        url_voltar=url_voltar,
        sexos=SEXOS,
        data_hoje=_data_br(date.today()),
        peso_minimo_padrao=_formatar_kg(PESO_MINIMO_PADRAO),
        abertas=abertas,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='saidas',
    )


def _negado_bastao():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect(URL_INICIAR)
    return redirecionar_home()


# -------------------------------------------------------
# Rota: GET /produtor/saida-bastao/leitura - Tela de Leitura.
# -------------------------------------------------------
@saida_bastao.route('/produtor/saida-bastao/leitura')
def leitura():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado_bastao()

    base = f'{URL_SELECAO}?id_propriedade={id_propriedade}'
    data_leitura = _ler_data_br(request.args.get('data_leitura', ''))
    if data_leitura is None:
        return redirect(f'{base}&erro=data')
    sexo = (request.args.get('sexo', '') or '').strip().upper()
    if sexo not in CODIGOS_SEXO:
        return redirect(f'{base}&erro=sexo')
    peso_minimo = _ler_decimal(request.args.get('peso_minimo', '')) if request.args.get('peso_minimo', '').strip() else PESO_MINIMO_PADRAO
    if peso_minimo is None or peso_minimo < 0:
        return redirect(f'{base}&erro=peso')

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))

    with get_db_produtor(session['id_produtor']) as db:
        total_gravados = _contar_gravados_na_data(db, id_propriedade, data_leitura)
        lidos = _lidos_da_data(db, id_propriedade, data_leitura)

    return render_template(
        'produtor/saida_bastao_leitura.html',
        propriedade=propriedade,
        id_propriedade=id_propriedade,
        data_leitura=_data_br(data_leitura),
        sexo=sexo,
        sexo_descricao=dict(SEXOS).get(sexo, sexo),
        peso_minimo=_formatar_kg(peso_minimo),
        total_gravados=total_gravados,
        lidos=lidos,
        url_selecao=f'{URL_SELECAO}?id_propriedade={id_propriedade}',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='saidas',
    )


# -------------------------------------------------------
# Rota: POST /produtor/saida-bastao/checar (AJAX) - confere o animal assim que
# o RFID e lido (ou o SISBOV, ou o Manejo, quando o chip nao serve).
# -------------------------------------------------------
@saida_bastao.route('/produtor/saida-bastao/checar', methods=['POST'])
def checar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    rfid   = (dados.get('rfid') or '').strip()
    sisbov = (dados.get('sisbov') or '').strip()
    manejo = (dados.get('manejo') or '').strip()
    dv     = (dados.get('dv') or '').strip()
    sexo   = (dados.get('sexo') or '').strip().upper()
    data_leitura = _ler_data_br(dados.get('data_leitura'))

    if not id_propriedade or (not rfid and not sisbov and not manejo) or data_leitura is None or sexo not in CODIGOS_SEXO:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou. Volte ao Hub de Saídas e abra de novo.'}), 403

    with get_db_produtor(session['id_produtor']) as db:
        if rfid:
            animal, bloqueio = _buscar_animal_por_rfid(db, id_propriedade, rfid)
            if bloqueio:
                return jsonify({'bloqueio': True, 'mensagem': bloqueio, 'pede_dv': False})
            # achou o animal pelo chip: a conferencia daqui em diante e a do Leitor, pelo SISBOV dele
            resultado = _validar_leitura(db, id_propriedade, data_leitura, sexo, animal.sisbov, '', '')
        else:
            resultado = _validar_leitura(db, id_propriedade, data_leitura, sexo, sisbov, manejo, dv)

    if 'bloqueio' in resultado:
        return jsonify({'bloqueio': True, 'mensagem': resultado['bloqueio'], 'pede_dv': bool(resultado.get('pede_dv'))})
    if 'repetido' in resultado:
        return jsonify({'repetido': True, 'leitura_antiga': resultado['repetido']})
    return jsonify({'ok': True, 'animal': resultado['ficha'], 'avisos': resultado['avisos']})


# -------------------------------------------------------
# Rota: POST /produtor/saida-bastao/gravar (AJAX) - grava a leitura em
# tb_2020_embarque. Confere TUDO de novo no servidor (mesma gravacao do Leitor).
# -------------------------------------------------------
@saida_bastao.route('/produtor/saida-bastao/gravar', methods=['POST'])
def gravar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = (dados.get('sisbov') or '').strip()
    sexo   = (dados.get('sexo') or '').strip().upper()
    via    = (dados.get('via') or '').strip().upper()
    elemento = (dados.get('elemento') or '').strip().upper()
    lote_saida = (dados.get('lote_saida') or '').strip()
    data_leitura = _ler_data_br(dados.get('data_leitura'))
    peso_minimo = _ler_decimal(dados.get('peso_minimo'))
    peso = _ler_decimal(dados.get('peso'))
    aceite_fora = bool(dados.get('aceite_fora_liberacao'))
    aceite_era  = bool(dados.get('aceite_era_0_12'))

    if not id_propriedade or not sisbov or data_leitura is None or sexo not in CODIGOS_SEXO or via not in ELEMENTOS_POR_VIA:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou. Volte ao Hub de Saídas e abra de novo.'}), 403
    if peso_minimo is None or peso_minimo < 0:
        peso_minimo = PESO_MINIMO_PADRAO
    if peso is None or peso <= 0:
        return jsonify({'erro': 'Digite o Peso do animal.'}), 400
    if peso < peso_minimo:
        return jsonify({'erro': 'Peso incorreto, verifique.'}), 400
    if elemento and elemento not in ELEMENTOS_POR_VIA[via]:
        return jsonify({'erro': 'Elemento incorreto para esta forma de leitura.'}), 400
    if len(lote_saida) > 30:
        return jsonify({'erro': 'Lote de Saída com mais de 30 caracteres.'}), 400

    with get_db_produtor(session['id_produtor']) as db:
        resultado = _validar_leitura(db, id_propriedade, data_leitura, sexo, sisbov, '', '')
        if 'bloqueio' in resultado:
            return jsonify({'bloqueio': True, 'mensagem': resultado['bloqueio'], 'erro': resultado['bloqueio']}), 409
        if 'repetido' in resultado:
            # a tela deveria ter perguntado antes; se chegou aqui, o servidor nao grava por cima
            return jsonify({'bloqueio': True, 'mensagem': MENSAGEM_JA_CONFERIDO, 'erro': MENSAGEM_JA_CONFERIDO}), 409

        avisos = resultado['avisos']
        if avisos['fora_liberacao']['ativo'] and not aceite_fora:
            return jsonify({'erro': 'Animal fora da Liberação para Abate: marque "Responsabilidade do Produtor".'}), 400
        if avisos['era_0_12']['ativo'] and not aceite_era:
            return jsonify({'erro': 'Animal com idade ERAS de 0 a 12 meses: marque "Responsabilidade do Produtor".'}), 400

        animal = resultado['animal']
        gta = db.get(Gta, animal.id_gta_entrada) if animal.id_gta_entrada else None
        origem = db.get(Parceiro, animal.id_origem) if animal.id_origem else None
        agora = datetime.now()
        id_usuario = session.get('usuario_id')

        embarque = Embarque(
            id_propriedade=int(id_propriedade),
            id_animal=animal.id,
            sisbov=animal.sisbov,
            manejo=animal.manejo,
            rfid=animal.rfid,
            id_especie=animal.id_especie,
            sexo=animal.sexo,
            nascimento=animal.nascimento,
            eras_dias=animal.eras_dias,
            id_aptidao=animal.id_aptidao,
            id_raca=animal.id_raca,
            cota_hilton=bool(animal.cota_hilton),
            liberacao_abate=animal.liberacao_abate,
            gta_entrada=((gta.numero_gta_completo or '')[:10] or None) if gta else None,
            gta_entrada_emissao=gta.data_emissao if gta else None,
            gta_entrada_validade=gta.data_validade if gta else None,
            gta_entrada_animais=gta.qtde_animais if gta else None,
            data_inclusao=animal.data_inclusao,
            lote_entrada=animal.lote,
            origem_propriedade=(origem.nome or '')[:150] if origem else None,
            origem_cpf_cnpj=origem.cpf_cnpj if origem else None,
            tipo_saida=TIPO_SAIDA_ABATE,
            data_embarque=data_leitura,
            hora_embarque=agora.time().replace(microsecond=0),
            lote_saida=lote_saida or None,
            peso_saida=peso.quantize(Decimal('0.01')),
            elemento=elemento or None,
            aceite_fora_liberacao=bool(avisos['fora_liberacao']['ativo']),
            aceite_fora_liberacao_por=id_usuario if avisos['fora_liberacao']['ativo'] else None,
            aceite_fora_liberacao_em=agora if avisos['fora_liberacao']['ativo'] else None,
            aceite_era_0_12=bool(avisos['era_0_12']['ativo']),
            aceite_era_0_12_por=id_usuario if avisos['era_0_12']['ativo'] else None,
            aceite_era_0_12_em=agora if avisos['era_0_12']['ativo'] else None,
            sts=False,
        )
        db.add(embarque)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            return jsonify({'bloqueio': True, 'erro': MENSAGEM_JA_CONFERIDO,
                            'mensagem': MENSAGEM_JA_CONFERIDO}), 409

        total_gravados = _contar_gravados_na_data(db, id_propriedade, data_leitura)
        hora_txt = embarque.hora_embarque.strftime('%H:%M')
        manejo_txt = animal.manejo or ''
        db.commit()

    return jsonify({
        'sucesso': True,
        'mensagem': 'Gravação Efetuada com Sucesso',
        'sisbov': sisbov,
        'manejo': manejo_txt,
        'sexo': sexo,
        'peso': _formatar_kg(peso),
        'hora': hora_txt,
        'total_gravados': total_gravados,
    })

# =========================================================
# FIM DE ARQUIVO: backend\routers\saida_bastao.py
# =========================================================
