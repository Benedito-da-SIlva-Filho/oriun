# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\saida_substituicao.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-19 20:40 -03
# ATUALIZADO EM: 2026-11-04 10:37 -03
# VERSAO: 1.1.1
#
# DESCRICAO:
#     Substituicao de Animal (Sessao 100) - grupo "Consultas e correcoes" do
#     Hub de Saidas. Troca o animal LIDO no embarque pelo animal que realmente
#     embarcou. A GTA, o frigorifico, a Data Embarque e a Data de Saida da linha
#     NAO mudam: so o animal (e o peso dele). Sempre grava Log.
#
#     REGRAS (fechadas com Benedito, 19/10/2026):
#       - A troca pode acontecer a qualquer momento ANTES do Comunicado de Saida
#         (leitura com sts = False), com a GTA vinculada ou nao. Depois do
#         Comunicado a troca entra junto com o pacote do Comunicado (baixa).
#       - O substituto tem de ser da MESMA CATEGORIA do animal trocado (especie,
#         sexo e faixa de idade na Data Embarque) - que e a categoria da GTA.
#       - Peso do substituto obrigatorio: de 100 kg (Peso Minimo padrao) a 2000 kg.
#       - O substituto precisa estar na Propriedade e nao pode estar em outra
#         leitura em aberto. Os avisos "fora da Liberacao" e "ERAS 0 a 12 meses"
#         valem como no Leitor (so grava com o "Responsabilidade do Produtor");
#         quem aceitou e quando fica gravado na linha.
#       - Animal que nao embarcou e nao tem substituto NAO e tratado aqui: a GTA
#         tem de fechar com o numero exato de animais (ou se cancela a GTA).
#       - Log (modulo saida_substituicao, so historico): antes e depois do animal.
#       - O animal trocado continua na Propriedade (tb_2001), livre.
#
#     ROTAS (todas em /produtor/saida-substituicao/):
#       iniciar    - escolhe a Propriedade (se precisar) e abre embarques.
#       embarques  - datas de embarque em aberto (com um so, abre direto os animais).
#       animais    - animais lidos da data, com o botao Substituir.
#       substituir - tela da troca (busca o substituto por SISBOV ou Manejo).
#       checar     - POST JSON: confere o substituto (categoria, avisos).
#       gravar     - POST JSON: confere tudo de novo e grava + Log.
#
#     v1.0.0: Criacao (Sessao 100).
#     v1.1.0: Sessao 103 (22/10/2026, 16:30 -03) - Caixa de Sucesso (utils/caixa_sucesso.py): depois de substituir, o usuario ve a tela
#             'Animal substituido com sucesso!' (SISBOV que saiu -> SISBOV que embarcou, peso, avisos aceitos) em vez do banner verde.
#             Nova rota GET /produtor/saida-substituicao/concluida. Regras da substituicao nao mudaram.  REVERSAO: .bak_antes_caixa_pacoteA_s103.
#     REVERSAO: remover este arquivo e os templates saida_substituicao_*.html; devolver
#     os .bak_antes_substituicao_s100 de app.py, permissoes.py, hub_entrada_agrupado.py
#     e log_operacoes.py.
#     v1.1.1: Sessao 114 (04/11/2026, 10:37 -03) - Substituicao: mensagem de peso abaixo do minimo vira "Peso incorreto, verifique.".  REVERSAO: .bak_antes_s114_peso.
# =========================================================

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, request, redirect, session, jsonify

from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.models.tb_parceiros import Parceiro
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.saida_leitor import (
    _validar_leitura, _formatar_kg, _ler_decimal, PESO_MINIMO_PADRAO,
)
from backend.routers.saida_consulta import (
    _contexto_base, _propriedade_do_usuario, _negado, _data_br, _ler_iso,
    _faixa_em, _filtro_abertas, _nomes, URL_HUB, PESO_MAXIMO,
)
from backend.utils.multitenant import get_db_produtor
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.caixa_sucesso import render_caixa_sucesso

saida_substituicao = Blueprint('saida_substituicao', __name__)

URL_INICIAR   = '/produtor/saida-substituicao/iniciar'
URL_EMBARQUES = '/produtor/saida-substituicao/embarques'
URL_ANIMAIS   = '/produtor/saida-substituicao/animais'
URL_SUBSTITUIR = '/produtor/saida-substituicao/substituir'
URL_CONCLUIDA = '/produtor/saida-substituicao/concluida'

MSG_MESMO_ANIMAL = 'Este é o próprio animal que já está na leitura. Digite o animal que realmente embarcou.'
MSG_OUTRA_LEITURA = ('Este animal já está em outra leitura em aberto (embarque de {data}). '
                     'Ele não pode ser o substituto enquanto essa leitura existir.')
MSG_CATEGORIA = ('Categoria diferente. Animal trocado: {antes}. Substituto: {depois}. '
                 'O substituto precisa ser da mesma categoria (espécie, sexo e faixa de idade na Data Embarque).')

# Campos do animal copiados para a linha do embarque (mesmos do Leitor do Abate).
CAMPOS_ANIMAL = (
    'id_animal', 'sisbov', 'manejo', 'rfid', 'id_especie', 'sexo', 'nascimento', 'eras_dias',
    'id_aptidao', 'id_raca', 'cota_hilton', 'liberacao_abate', 'gta_entrada', 'gta_entrada_emissao',
    'gta_entrada_validade', 'gta_entrada_animais', 'data_inclusao', 'lote_entrada',
    'origem_propriedade', 'origem_cpf_cnpj',
)
CAMPOS_ACEITE = (
    'aceite_fora_liberacao', 'aceite_fora_liberacao_por', 'aceite_fora_liberacao_em',
    'aceite_era_0_12', 'aceite_era_0_12_por', 'aceite_era_0_12_em',
)


# =========================================================
# BLOCO 1 - Funcoes puras (sem banco)
# =========================================================
def _categoria_texto(sexo, faixa):
    sexo_txt = {'MACHO': 'Macho', 'FEMEA': 'Fêmea'}.get(sexo, sexo or '?')
    return f'{sexo_txt} · {faixa or "sem faixa"}'


def _mesma_categoria(especie_a, sexo_a, faixa_a, especie_b, sexo_b, faixa_b):
    """Categoria idêntica: espécie, sexo e faixa de idade (e a faixa precisa existir)."""
    if not faixa_a or not faixa_b or faixa_a == '-' or faixa_b == '-':
        return False
    return (especie_a == especie_b) and (sexo_a == sexo_b) and (faixa_a == faixa_b)


def _validar_peso(texto):
    """Devolve (Decimal, None) ou (None, mensagem)."""
    peso = _ler_decimal(texto)
    if peso is None or peso <= 0:
        return None, 'Digite o Peso do substituto.'
    if peso < PESO_MINIMO_PADRAO:
        return None, 'Peso incorreto, verifique.'
    if peso > PESO_MAXIMO:
        return None, f'Peso acima de {_formatar_kg(PESO_MAXIMO)} kg. Confira o valor.'
    return peso.quantize(Decimal('0.01')), None


def _json_valor(v):
    """Valor pronto para o Log (JSON)."""
    if v is None:
        return None
    if hasattr(v, 'isoformat'):
        return v.isoformat()
    if isinstance(v, Decimal):
        return str(v)
    return v


# =========================================================
# BLOCO 2 - Acesso ao banco
# =========================================================
def _linha_aberta(db, id_propriedade, id_linha):
    try:
        id_int = int(id_linha)
    except (TypeError, ValueError):
        return None
    return db.query(Embarque).filter(*_filtro_abertas(id_propriedade), Embarque.id == id_int).first()


def _datas_em_aberto(db, id_propriedade):
    return (
        db.query(Embarque.data_embarque, func.count(Embarque.id))
        .filter(*_filtro_abertas(id_propriedade))
        .group_by(Embarque.data_embarque)
        .order_by(Embarque.data_embarque.desc()).all()
    )


def _avaliar_substituto(db, id_propriedade, linha, sisbov, manejo, dv):
    """
    Confere o substituto para a linha. Devolve
      {'bloqueio': texto, 'pede_dv': bool} ou
      {'animal': Entrada, 'ficha': {...}, 'avisos': {...}, 'categoria': texto}
    """
    resultado = _validar_leitura(db, id_propriedade, linha.data_embarque, linha.sexo, sisbov, manejo, dv)
    if 'bloqueio' in resultado:
        texto = resultado['bloqueio']
        if texto.startswith('Sexo divergente'):
            texto = ('Sexo diferente do animal trocado. O substituto precisa ser da mesma categoria '
                     '(espécie, sexo e faixa de idade na Data Embarque).')
        return {'bloqueio': texto, 'pede_dv': bool(resultado.get('pede_dv'))}
    if 'repetido' in resultado:
        rep = resultado['repetido']
        if rep['sisbov'] == linha.sisbov:
            return {'bloqueio': MSG_MESMO_ANIMAL}
        return {'bloqueio': MSG_OUTRA_LEITURA.format(data=rep['data'])}

    animal = resultado['animal']
    faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
    faixa_antiga = _faixa_em(faixas, linha.nascimento, linha.data_embarque)
    faixa_nova = _faixa_em(faixas, animal.nascimento, linha.data_embarque)
    if not _mesma_categoria(linha.id_especie, linha.sexo, faixa_antiga, animal.id_especie, animal.sexo, faixa_nova):
        return {'bloqueio': MSG_CATEGORIA.format(
            antes=_categoria_texto(linha.sexo, faixa_antiga), depois=_categoria_texto(animal.sexo, faixa_nova))}
    resultado['categoria'] = _categoria_texto(animal.sexo, faixa_nova)
    return resultado


# =========================================================
# BLOCO 3 - Rotas
# =========================================================

# -------------------------------------------------------
# GET /produtor/saida-substituicao/iniciar
# -------------------------------------------------------
@saida_substituicao.route('/produtor/saida-substituicao/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista,
            erro=erro,
            titulo='Substituição de Animal — Selecionar Propriedade',
            proximo=URL_EMBARQUES,
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
        return redirect(f'{URL_EMBARQUES}?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_EMBARQUES}?id_propriedade={par.id_propriedade}')

    return _tela_selecionar(pares, None)


# -------------------------------------------------------
# GET /produtor/saida-substituicao/embarques - datas em aberto.
# -------------------------------------------------------
@saida_substituicao.route('/produtor/saida-substituicao/embarques')
def embarques():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']

    with get_db_produtor(id_produtor) as db:
        datas = _datas_em_aberto(db, id_propriedade)

    if len(datas) == 1:
        iso = datas[0][0].strftime('%Y-%m-%d')
        return redirect(f'{URL_ANIMAIS}?id_propriedade={int(id_propriedade)}&data={iso}')

    linhas = [{'iso': d.strftime('%Y-%m-%d'), 'data': _data_br(d), 'qtde': q} for d, q in datas]
    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_substituicao_embarques.html',
        embarques=linhas,
        id_propriedade=int(id_propriedade),
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        url_hub=URL_HUB,
        **_contexto_base(),
    )


# -------------------------------------------------------
# GET /produtor/saida-substituicao/animais - animais lidos da data.
# -------------------------------------------------------
@saida_substituicao.route('/produtor/saida-substituicao/animais')
def animais():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    data = _ler_iso(request.args.get('data', ''))
    url_embarques = f'{URL_EMBARQUES}?id_propriedade={int(id_propriedade)}'
    if not data:
        return redirect(url_embarques)
    id_produtor = session['id_produtor']

    with get_db_produtor(id_produtor) as db:
        datas = _datas_em_aberto(db, id_propriedade)
        voltar = URL_HUB if len(datas) <= 1 else url_embarques
        faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
        leituras = (
            db.query(Embarque)
            .filter(*_filtro_abertas(id_propriedade), Embarque.data_embarque == data)
            .order_by(Embarque.sisbov.asc()).all()
        )
        if not leituras:
            return redirect(url_embarques)
        ids_gta = {l.id_gta for l in leituras if l.id_gta is not None}
        numeros = {g.id: g.numero_gta_completo for g in db.query(Gta).filter(Gta.id.in_(ids_gta)).all()} if ids_gta else {}
        lista = [{
            'id': l.id,
            'sisbov': l.sisbov,
            'manejo': l.manejo or '',
            'sexo': {'FEMEA': 'Fêmea', 'MACHO': 'Macho'}.get(l.sexo, l.sexo or '-'),
            'faixa': _faixa_em(faixas, l.nascimento, data),
            'peso': _formatar_kg(l.peso_saida) if l.peso_saida is not None else '',
            'gta': numeros.get(l.id_gta, '') if l.id_gta is not None else '',
        } for l in leituras]
        mensagem = None
        try:
            id_ok = int(request.args.get('ok', '0'))
        except ValueError:
            id_ok = 0
        if id_ok:
            novo = next((l for l in leituras if l.id == id_ok), None)
            if novo is not None:
                mensagem = f'Animal substituído. Agora a leitura é do SISBOV {novo.sisbov}.'

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_substituicao_animais.html',
        animais=lista,
        mensagem=mensagem,
        id_propriedade=int(id_propriedade),
        iso=data.strftime('%Y-%m-%d'),
        data_embarque=_data_br(data),
        url_voltar=voltar,
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        **_contexto_base(),
    )


# -------------------------------------------------------
# GET /produtor/saida-substituicao/substituir - tela da troca.
# -------------------------------------------------------
@saida_substituicao.route('/produtor/saida-substituicao/substituir')
def substituir():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']
    url_embarques = f'{URL_EMBARQUES}?id_propriedade={int(id_propriedade)}'

    with get_db_produtor(id_produtor) as db:
        linha = _linha_aberta(db, id_propriedade, request.args.get('id', ''))
        if linha is None:
            return redirect(url_embarques)
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
        iso = linha.data_embarque.strftime('%Y-%m-%d')
        data_br = _data_br(linha.data_embarque)

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_substituicao_trocar.html',
        antigo=antigo,
        id_propriedade=int(id_propriedade),
        iso=iso,
        data_embarque=data_br,
        peso_minimo=_formatar_kg(PESO_MINIMO_PADRAO),
        url_voltar=f'{URL_ANIMAIS}?id_propriedade={int(id_propriedade)}&data={iso}',
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        **_contexto_base(),
    )


# -------------------------------------------------------
# POST /produtor/saida-substituicao/checar - confere o substituto.
# -------------------------------------------------------
@saida_substituicao.route('/produtor/saida-substituicao/checar', methods=['POST'])
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

    with get_db_produtor(session['id_produtor']) as db:
        linha = _linha_aberta(db, id_propriedade, dados.get('id'))
        if linha is None:
            return jsonify({'erro': 'Leitura não encontrada ou já com Comunicado. Volte e abra de novo.'}), 400
        resultado = _avaliar_substituto(db, id_propriedade, linha, sisbov, manejo, dv)

    if 'bloqueio' in resultado:
        return jsonify({'bloqueio': True, 'mensagem': resultado['bloqueio'], 'pede_dv': bool(resultado.get('pede_dv'))})
    return jsonify({'ok': True, 'animal': resultado['ficha'], 'avisos': resultado['avisos'],
                    'categoria': resultado['categoria']})


# -------------------------------------------------------
# POST /produtor/saida-substituicao/gravar - confere tudo de novo e troca.
# -------------------------------------------------------
@saida_substituicao.route('/produtor/saida-substituicao/gravar', methods=['POST'])
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
    peso, erro_peso = _validar_peso(dados.get('peso'))
    if erro_peso:
        return jsonify({'erro': erro_peso}), 400

    with get_db_produtor(session['id_produtor']) as db:
        linha = _linha_aberta(db, id_propriedade, dados.get('id'))
        if linha is None:
            return jsonify({'erro': 'Leitura não encontrada ou já com Comunicado. Volte e abra de novo.'}), 400
        resultado = _avaliar_substituto(db, id_propriedade, linha, sisbov, '', '')
        if 'bloqueio' in resultado:
            return jsonify({'bloqueio': True, 'erro': resultado['bloqueio'], 'mensagem': resultado['bloqueio']}), 409

        avisos = resultado['avisos']
        if avisos['fora_liberacao']['ativo'] and not aceite_fora:
            return jsonify({'erro': 'Animal fora da Liberação para Abate: marque "Responsabilidade do Produtor".'}), 400
        if avisos['era_0_12']['ativo'] and not aceite_era:
            return jsonify({'erro': 'Animal com idade ERAS de 0 a 12 meses: marque "Responsabilidade do Produtor".'}), 400

        animal = resultado['animal']
        gta_ent = db.get(Gta, animal.id_gta_entrada) if animal.id_gta_entrada else None
        origem = db.get(Parceiro, animal.id_origem) if animal.id_origem else None
        agora = datetime.now()
        id_usuario = session.get('usuario_id')

        novos = {
            'id_animal': animal.id,
            'sisbov': animal.sisbov,
            'manejo': animal.manejo,
            'rfid': animal.rfid,
            'id_especie': animal.id_especie,
            'sexo': animal.sexo,
            'nascimento': animal.nascimento,
            'eras_dias': animal.eras_dias,
            'id_aptidao': animal.id_aptidao,
            'id_raca': animal.id_raca,
            'cota_hilton': bool(animal.cota_hilton),
            'liberacao_abate': animal.liberacao_abate,
            'gta_entrada': ((gta_ent.numero_gta_completo or '')[:10] or None) if gta_ent else None,
            'gta_entrada_emissao': gta_ent.data_emissao if gta_ent else None,
            'gta_entrada_validade': gta_ent.data_validade if gta_ent else None,
            'gta_entrada_animais': gta_ent.qtde_animais if gta_ent else None,
            'data_inclusao': animal.data_inclusao,
            'lote_entrada': animal.lote,
            'origem_propriedade': (origem.nome or '')[:150] if origem else None,
            'origem_cpf_cnpj': origem.cpf_cnpj if origem else None,
            'peso_saida': peso,
            'elemento': None,
            'aceite_fora_liberacao': bool(avisos['fora_liberacao']['ativo']),
            'aceite_fora_liberacao_por': id_usuario if avisos['fora_liberacao']['ativo'] else None,
            'aceite_fora_liberacao_em': agora if avisos['fora_liberacao']['ativo'] else None,
            'aceite_era_0_12': bool(avisos['era_0_12']['ativo']),
            'aceite_era_0_12_por': id_usuario if avisos['era_0_12']['ativo'] else None,
            'aceite_era_0_12_em': agora if avisos['era_0_12']['ativo'] else None,
        }
        antes_completo = {c: getattr(linha, c) for c in novos}
        antes = {c: _json_valor(antes_completo[c]) for c in novos if antes_completo[c] != novos[c]}
        depois = {c: _json_valor(novos[c]) for c in novos if antes_completo[c] != novos[c]}

        sisbov_antigo = linha.sisbov
        numero_gta = ''
        if linha.id_gta is not None:
            g = db.get(Gta, linha.id_gta)
            numero_gta = g.numero_gta_completo if g else ''
        id_operacao = registrar_operacao(
            db, id_usuario=id_usuario, id_propriedade=int(id_propriedade),
            modulo='saida_substituicao',
            descricao=(f'Substituição no embarque de {_data_br(linha.data_embarque)}: '
                       f'SISBOV {sisbov_antigo} trocado por {animal.sisbov}'
                       + (f' (GTA {numero_gta})' if numero_gta else '')))
        for campo, valor in novos.items():
            setattr(linha, campo, valor)
        registrar_item(db, id_operacao, 'tb_2020_embarque', linha.id, 'UPDATE', antes, depois)
        id_linha = linha.id
        sisbov_novo = animal.sisbov
        iso = linha.data_embarque.strftime('%Y-%m-%d')
        resumo_caixa = {
            'sisbov_antigo': sisbov_antigo, 'sisbov_novo': sisbov_novo, 'iso': iso, 'gta': numero_gta,
            'data_br': _data_br(linha.data_embarque), 'peso': _formatar_kg(peso) if peso is not None else '',
            'fora_liberacao': bool(avisos['fora_liberacao']['ativo']), 'era_0_12': bool(avisos['era_0_12']['ativo']),
        }
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            msg = 'Este animal já está em uma leitura em aberto. Confira e tente de novo.'
            return jsonify({'bloqueio': True, 'erro': msg, 'mensagem': msg}), 409

    session['caixa_substituicao'] = resumo_caixa
    return jsonify({
        'ok': True,
        'sisbov_antigo': sisbov_antigo,
        'sisbov_novo': sisbov_novo,
        'url': f'{URL_CONCLUIDA}?id_propriedade={int(id_propriedade)}&data={iso}',
    })


# -------------------------------------------------------
# GET /produtor/saida-substituicao/concluida - Caixa de Sucesso (v1.1.0). Le e apaga o resumo guardado na sessao.
# -------------------------------------------------------
@saida_substituicao.route('/produtor/saida-substituicao/concluida')
def concluida():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    iso = request.args.get('data', '')
    url_animais = f'{URL_ANIMAIS}?id_propriedade={int(id_propriedade)}&data={iso}'
    r = session.pop('caixa_substituicao', None)
    if not r:
        return redirect(url_animais)               # recarregou a pagina: a caixa ja foi vista
    notas = ['A GTA, o frigorífico e a data do embarque continuam os mesmos.']
    if r['gta']:
        notas.insert(0, f'GTA {r["gta"]}')
    if r['fora_liberacao']:
        notas.append('Animal fora da Liberação para Abate: ficou registrada a Responsabilidade do Produtor.')
    if r['era_0_12']:
        notas.append('Animal com idade ERAS de 0 a 12 meses: ficou registrada a Responsabilidade do Produtor.')
    notas.append('A troca ficou registrada no Log de Operações.')
    mudancas = [{'campo': 'SISBOV da leitura', 'antes': r['sisbov_antigo'], 'depois': r['sisbov_novo']}]
    if r['peso']:
        mudancas.append({'campo': 'Peso de saída', 'antes': None, 'depois': f'{r["peso"]} kg'})
    return render_caixa_sucesso(
        _contexto_base(), titulo='Animal substituído com sucesso!', subtitulo=f'Embarque de {r["data_br"]}',
        mudancas=mudancas, notas=notas,
        botoes=[{'texto': 'Substituir outro animal', 'url': url_animais, 'primario': True},
                {'texto': 'Voltar ao Hub de Saídas', 'url': URL_HUB, 'primario': False}],
        url_voltar=url_animais, titulo_pagina='Orion SISBOV — Animal substituído',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\saida_substituicao.py
# =========================================================
