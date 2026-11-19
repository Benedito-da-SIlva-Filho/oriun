# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\saida_arquivo.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-21 17:30 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.4.0
# v1.4.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Abate por Arquivo Texto (Sessao 102) - grupo "Leitura no brete" do Hub de Saidas.
#     Ultimo recurso quando o brete esta sem internet: o arquivo (ABATE.TXT ou CSV) so
#     tem o numero do brinco (SISBOV, 15 posicoes). O Orion le cada numero como se fosse
#     a leitura no brete e gera o Embarque (tb_2020_embarque), igual ao Leitor do Abate.
#
#     REGRAS (fechadas com Benedito, 21/10/2026):
#       - Formatos: TXT e CSV. Acha os numeros por linha ou separados por ; , ou espaco.
#         Linhas em branco e palavras (cabecalho) sao ignoradas; numero que nao tem 15
#         digitos e recusado; numero repetido no arquivo conta uma vez so.
#       - Data Embarque escolhida na tela. O sexo vem do proprio animal. O PESO fica vazio
#         (preenche-se depois pela Correcao do Consulta Embarque).
#       - Invalido nao trava o resto: mostra uma PREVIA (quantos entram, quais ficam de fora
#         e o motivo) e so grava depois da confirmacao. Recusados: brinco que nao esta na
#         Propriedade / ja saiu / DV incorreto, animal ja em outra leitura em aberto,
#         animal sem Liberacao cadastrada.
#       - ASSUMIDO (Benedito ainda nao confirmou): animal com aviso (fora da Liberacao ou
#         ERAS 0 a 12 meses) so entra se o usuario marcar "Responsabilidade do Produtor" na
#         previa; a marca vale para todos os animais com aviso e fica gravada (quem e quando)
#         em cada leitura, como no Leitor. Sem a marca, esses animais ficam de fora.
#       - Elemento (Botton/Brinco) fica vazio. Grava Log de Operacoes (v1.1.0, modulo saida_arquivo).
#
#     ROTAS (/produtor/saida-arquivo/):
#       iniciar   - resolve a Propriedade (fazenda em uso) e abre a tela do arquivo.
#       arquivo   - GET: escolher a Data Embarque e o arquivo.
#       conferir  - POST (arquivo): le, confere cada brinco e mostra a previa (nada e gravado).
#       gravar    - POST: confere de novo e grava os Embarques.
#
#     v1.0.0: Criacao (Sessao 102).
#     v1.0.1: Sessao 102 (21/10/2026, 17:25 -03) - Os brincos recusados na previa (e o motivo) seguem ate a tela
#             final: antes so os que entravam eram reenviados e o recusado sumia depois de gravar.
#     REVERSAO: remover este arquivo e os templates saida_arquivo_*.html; devolver os
#     .bak_antes_abate_arquivo_s102 de app.py, permissoes.py e hub_entrada_agrupado.py.
#     As leituras gravadas saem pela Consulta Embarque (excluir leitura) ou por SQL.
#     v1.1.0: Sessao 103 (22/10/2026, 08:25 -03) - LOG DE OPERACOES (decisao de Benedito): cada gravacao registra uma operacao (modulo
#             saida_arquivo, so historico) com quem gravou, quando, quantos entraram/recusados e um item por Embarque gravado.
#             Precisa do log_operacoes.py 1.14.0.  REVERSAO: .bak_antes_log_s103.
#     v1.2.0: Sessao 104 (23/10/2026, 08:50 -03) - CAIXA DE SUCESSO (Padrao No7): depois de gravar, a tela de conclusao passa a ser a Caixa padrao
#             (utils/caixa_sucesso.py 1.1.0, com as listas Ficaram de fora e Gravados). Mesmos dados de antes; o aviso do peso vazio vira aviso vermelho.
#             O template saida_arquivo_sucesso.html foi aposentado. Precisa do caixa_sucesso.py/.html 1.1.0.  REVERSAO: .bak_antes_s104 + devolver o template.
#     v1.3.0: Sessao 110 (31/10/2026, 12:15 -03) - PESO: cada leitura grava o ULTIMO PESO do animal (tb_4003_pesos), como o Leitor; o peso nunca e pedido no arquivo (decisao do Benedito: relatorios precisam do peso). Animal sem nenhum peso entra vazio e a tela final avisa so esses. REVERSAO: .bak_antes_s110_peso.
# =========================================================

import json
import re
from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, session
from sqlalchemy.exc import IntegrityError

from backend.utils.caixa_sucesso import render_caixa_sucesso   # v1.2.0 - Padrao No7
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4003_pesos import Peso   # v1.3.0 - ultimo peso do animal
from backend.models.tb_parceiros import Parceiro
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.saida_leitor import _buscar_animal, _validar_leitura, TIPO_SAIDA_ABATE
from backend.routers.saida_consulta import (
    _contexto_base, _propriedade_do_usuario, _negado, _data_br, _nomes, _ler_iso, URL_HUB,
)
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.multitenant import get_db_produtor

saida_arquivo = Blueprint('saida_arquivo', __name__)

URL_INICIAR = '/produtor/saida-arquivo/iniciar'
URL_ARQUIVO = '/produtor/saida-arquivo/arquivo'
URL_CONFERIR = '/produtor/saida-arquivo/conferir'
URL_GRAVAR = '/produtor/saida-arquivo/gravar'
URL_CONSULTA_EMBARQUE = '/produtor/saida-consulta/iniciar'

TAMANHO_BRINCO = 15
LIMITE_BRINCOS = 2000
MODULO_LOG = 'saida_arquivo'   # v1.1.0 - modulo do Log de Operacoes (so historico)
LIMITE_BYTES = 1024 * 1024          # 1 MB
DIAS_A_FRENTE = 30
ANO_MINIMO = 2020

MSG_AVISO_NAO_ASSUMIDO = 'Tem aviso e a Responsabilidade do Produtor não foi marcada.'


# =========================================================
# BLOCO 1 - Funcoes puras (sem banco)
# =========================================================
def _decodificar(dados):
    """Bytes do arquivo -> texto (UTF-8 com ou sem BOM; senao Latin-1)."""
    try:
        return dados.decode('utf-8-sig')
    except UnicodeDecodeError:
        return dados.decode('latin-1')


def _extrair_brincos(texto):
    """
    Devolve dict: brincos (15 digitos, sem repetir, na ordem do arquivo), fora_padrao (numeros
    sem 15 digitos), repetidos (quantos numeros iguais foram descartados) e ignorados (palavras).
    """
    brincos, vistos = [], set()
    fora_padrao, repetidos, ignorados = [], 0, 0
    for pedaco in re.split(r'[\s;,|]+', texto or ''):
        pedaco = pedaco.strip().strip('"\'')
        if not pedaco:
            continue
        if not (pedaco.isascii() and pedaco.isdecimal()):
            ignorados += 1
            continue
        if len(pedaco) != TAMANHO_BRINCO:
            fora_padrao.append(pedaco)
            continue
        if pedaco in vistos:
            repetidos += 1
            continue
        vistos.add(pedaco)
        brincos.append(pedaco)
    return {'brincos': brincos, 'fora_padrao': fora_padrao, 'repetidos': repetidos, 'ignorados': ignorados}


def _data_valida(data):
    """Mesma regra da Consulta Embarque: de 2020 ate 30 dias a frente."""
    return data is not None and data.year >= ANO_MINIMO and data <= date.today() + timedelta(days=DIAS_A_FRENTE)


def _recusados_da_previa(texto):
    """Recusados da previa (JSON do formulario), so para mostrar na tela final. Nada e gravado a partir deles."""
    try:
        lista = json.loads(texto or '[]')
    except ValueError:
        return []
    saida = []
    if isinstance(lista, list):
        for r in lista[:LIMITE_BRINCOS]:
            if isinstance(r, dict) and isinstance(r.get('sisbov'), str) and isinstance(r.get('motivo'), str):
                saida.append({'sisbov': r['sisbov'][:30], 'motivo': r['motivo'][:300]})
    return saida


# =========================================================
# BLOCO 2 - Acesso ao banco
# =========================================================
def _conferir_brincos(db, id_propriedade, data_embarque, brincos):
    """
    Confere cada brinco como o Leitor confere. Devolve lista de dicts na ordem do arquivo:
      {sisbov, situacao: 'ok' | 'aviso' | 'recusado', motivo, manejo, sexo, faixa, avisos: [textos], animal}
    """
    saida = []
    for sisbov in brincos:
        item = {'sisbov': sisbov, 'situacao': 'recusado', 'motivo': '', 'manejo': '', 'sexo': '',
                'faixa': '', 'avisos': [], 'animal': None}
        animal, bloqueio = _buscar_animal(db, id_propriedade, sisbov, '', '')
        if bloqueio:
            item['motivo'] = bloqueio
            saida.append(item)
            continue
        resultado = _validar_leitura(db, id_propriedade, data_embarque, animal.sexo, sisbov, '', '')
        if 'bloqueio' in resultado:
            item['motivo'] = resultado['bloqueio']
        elif 'repetido' in resultado:
            item['motivo'] = f"Já está em leitura em aberto (embarque de {resultado['repetido']['data']})."
        else:
            ficha, avisos = resultado['ficha'], resultado['avisos']
            textos = [avisos[k]['texto'] for k in ('fora_liberacao', 'era_0_12') if avisos[k]['ativo']]
            item.update({
                'situacao': 'aviso' if textos else 'ok', 'avisos': textos,
                'manejo': ficha['manejo'], 'faixa': ficha['idade_meses'],
                'sexo': 'Fêmea' if animal.sexo == 'FEMEA' else ('Macho' if animal.sexo == 'MACHO' else '-'),
                'animal': animal, 'avisos_flags': avisos,
            })
        saida.append(item)
    return saida


def _novo_embarque(db, id_propriedade, data_embarque, animal, avisos, id_usuario, agora):
    gta = db.get(Gta, animal.id_gta_entrada) if animal.id_gta_entrada else None
    origem = db.get(Parceiro, animal.id_origem) if animal.id_origem else None
    # v1.3.0 - ultimo peso do animal (tb_4003_pesos); sem pesagem nenhuma, fica vazio
    ultimo = db.query(Peso).filter(Peso.sisbov == animal.sisbov).order_by(Peso.sequencia.desc()).first()
    peso = Decimal(str(ultimo.peso)).quantize(Decimal('0.01')) if ultimo is not None else None
    fora = bool(avisos['fora_liberacao']['ativo'])
    era = bool(avisos['era_0_12']['ativo'])
    return Embarque(
        id_propriedade=int(id_propriedade), id_animal=animal.id, sisbov=animal.sisbov, manejo=animal.manejo,
        rfid=animal.rfid, id_especie=animal.id_especie, sexo=animal.sexo, nascimento=animal.nascimento,
        eras_dias=animal.eras_dias, id_aptidao=animal.id_aptidao, id_raca=animal.id_raca,
        cota_hilton=bool(animal.cota_hilton), liberacao_abate=animal.liberacao_abate,
        gta_entrada=((gta.numero_gta_completo or '')[:10] or None) if gta else None,
        gta_entrada_emissao=gta.data_emissao if gta else None,
        gta_entrada_validade=gta.data_validade if gta else None,
        gta_entrada_animais=gta.qtde_animais if gta else None,
        data_inclusao=animal.data_inclusao, lote_entrada=animal.lote,
        origem_propriedade=(origem.nome or '')[:150] if origem else None,
        origem_cpf_cnpj=origem.cpf_cnpj if origem else None,
        tipo_saida=TIPO_SAIDA_ABATE, data_embarque=data_embarque,
        hora_embarque=agora.time().replace(microsecond=0),
        lote_saida=None, peso_saida=peso, elemento=None,
        aceite_fora_liberacao=fora, aceite_fora_liberacao_por=id_usuario if fora else None,
        aceite_fora_liberacao_em=agora if fora else None,
        aceite_era_0_12=era, aceite_era_0_12_por=id_usuario if era else None,
        aceite_era_0_12_em=agora if era else None,
        sts=False,
    )


# =========================================================
# BLOCO 3 - Rotas
# =========================================================
def _tela_arquivo(id_propriedade, erro=None, data_iso=None):
    id_produtor = session['id_produtor']
    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_arquivo_selecao.html',
        erro=erro,
        id_propriedade=int(id_propriedade),
        data_iso=data_iso or date.today().strftime('%Y-%m-%d'),
        url_conferir=URL_CONFERIR,
        url_voltar=URL_HUB,
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        **_contexto_base(),
    )


# -------------------------------------------------------
# GET /produtor/saida-arquivo/iniciar
# -------------------------------------------------------
@saida_arquivo.route('/produtor/saida-arquivo/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista,
            erro=erro,
            titulo='Abate por Arquivo — Selecionar Propriedade',
            proximo=URL_ARQUIVO,
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
        return redirect(f'{URL_ARQUIVO}?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_ARQUIVO}?id_propriedade={par.id_propriedade}')

    return _tela_selecionar(pares, None)


# -------------------------------------------------------
# GET /produtor/saida-arquivo/arquivo
# -------------------------------------------------------
@saida_arquivo.route('/produtor/saida-arquivo/arquivo')
def arquivo():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    return _tela_arquivo(id_propriedade)


# -------------------------------------------------------
# POST /produtor/saida-arquivo/conferir - le o arquivo e mostra a previa (nao grava nada).
# -------------------------------------------------------
@saida_arquivo.route('/produtor/saida-arquivo/conferir', methods=['POST'])
def conferir():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.form.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']

    data_iso = request.form.get('data', '')
    data_embarque = _ler_iso(data_iso)
    if not _data_valida(data_embarque):
        return _tela_arquivo(id_propriedade, 'Data Embarque inválida (de 2020 até 30 dias à frente).', data_iso)
    arq = request.files.get('arquivo')
    if arq is None or not arq.filename:
        return _tela_arquivo(id_propriedade, 'Escolha o arquivo ABATE.TXT (ou CSV).', data_iso)
    if not arq.filename.lower().endswith(('.txt', '.csv')):
        return _tela_arquivo(id_propriedade, 'Formato não aceito. Use arquivo TXT ou CSV.', data_iso)
    dados = arq.read(LIMITE_BYTES + 1)
    if len(dados) > LIMITE_BYTES:
        return _tela_arquivo(id_propriedade, 'Arquivo grande demais (máximo 1 MB).', data_iso)

    lido = _extrair_brincos(_decodificar(dados))
    if not lido['brincos'] and not lido['fora_padrao']:
        return _tela_arquivo(id_propriedade, 'Não encontrei nenhum número de brinco no arquivo.', data_iso)
    if len(lido['brincos']) > LIMITE_BRINCOS:
        return _tela_arquivo(id_propriedade, f'Arquivo com mais de {LIMITE_BRINCOS} brincos. Divida em dois.', data_iso)

    with get_db_produtor(id_produtor) as db:
        itens = _conferir_brincos(db, id_propriedade, data_embarque, lido['brincos'])

    linhas = [{k: v for k, v in i.items() if k not in ('animal', 'avisos_flags')} for i in itens]
    recusados = [l for l in linhas if l['situacao'] == 'recusado']
    recusados += [{'sisbov': n, 'situacao': 'recusado', 'motivo': f'Fora do padrão: tem {len(n)} dígitos (o brinco tem 15).',
                   'manejo': '', 'sexo': '', 'faixa': '', 'avisos': []} for n in lido['fora_padrao']]
    entram = [l for l in linhas if l['situacao'] != 'recusado']
    com_aviso = [l for l in entram if l['situacao'] == 'aviso']

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_arquivo_conferencia.html',
        entram=entram,
        recusados=recusados,
        qtd_aviso=len(com_aviso),
        repetidos=lido['repetidos'],
        ignorados=lido['ignorados'],
        nome_arquivo=arq.filename,
        data_iso=data_embarque.strftime('%Y-%m-%d'),
        data_embarque=_data_br(data_embarque),
        sisbovs='\n'.join(l['sisbov'] for l in entram),
        recusados_json=json.dumps([{'sisbov': r['sisbov'], 'motivo': r['motivo']} for r in recusados], ensure_ascii=False),
        id_propriedade=int(id_propriedade),
        url_gravar=URL_GRAVAR,
        url_voltar=f'{URL_ARQUIVO}?id_propriedade={int(id_propriedade)}',
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        **_contexto_base(),
    )


# -------------------------------------------------------
# POST /produtor/saida-arquivo/gravar - confere de novo e grava os Embarques.
# -------------------------------------------------------
@saida_arquivo.route('/produtor/saida-arquivo/gravar', methods=['POST'])
def gravar():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.form.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']

    data_embarque = _ler_iso(request.form.get('data', ''))
    if not _data_valida(data_embarque):
        return _tela_arquivo(id_propriedade, 'Data Embarque inválida. Envie o arquivo de novo.')
    if request.form.get('confirmo') != '1':
        return _tela_arquivo(id_propriedade, 'Faltou marcar "Revisei os dados e confirmo". Envie o arquivo de novo.')
    brincos = _extrair_brincos(request.form.get('sisbovs', ''))['brincos'][:LIMITE_BRINCOS]
    if not brincos:
        return _tela_arquivo(id_propriedade, 'Nenhum brinco para gravar. Envie o arquivo de novo.')
    assumiu = request.form.get('assumo') == '1'
    id_usuario = session.get('usuario_id')

    gravados, recusados = [], _recusados_da_previa(request.form.get('recusados', ''))
    ids_gravados = []   # v1.1.0 - ids dos Embarques gravados (para o Log)
    with get_db_produtor(id_produtor) as db:
        itens = _conferir_brincos(db, id_propriedade, data_embarque, brincos)
        agora = datetime.now()
        for item in itens:
            if item['situacao'] == 'recusado':
                recusados.append({'sisbov': item['sisbov'], 'motivo': item['motivo']})
                continue
            if item['situacao'] == 'aviso' and not assumiu:
                recusados.append({'sisbov': item['sisbov'], 'motivo': MSG_AVISO_NAO_ASSUMIDO})
                continue
            emb = _novo_embarque(db, id_propriedade, data_embarque, item['animal'], item['avisos_flags'],
                                 id_usuario, agora)
            try:
                with db.begin_nested():
                    db.add(emb)
                    db.flush()
            except IntegrityError:
                recusados.append({'sisbov': item['sisbov'], 'motivo': 'Já está em uma leitura em aberto.'})
                continue
            gravados.append({'sisbov': item['sisbov'], 'manejo': item['manejo'], 'sexo': item['sexo'],
                             'faixa': item['faixa'], 'aviso': item['situacao'] == 'aviso',
                             'peso': (f'{emb.peso_saida:.2f}'.replace('.', ',') if emb.peso_saida is not None else '')})
            ids_gravados.append((emb.id, item['sisbov']))
        # ---- v1.1.0: Log de Operacoes (uma operacao por importacao; so historico) ----
        if ids_gravados:
            qtd_aviso = sum(1 for g in gravados if g['aviso'])
            descricao = (f'Abate por Arquivo: {len(gravados)} animal(is) gravado(s) no Embarque de {_data_br(data_embarque)}; '
                         f'{len(recusados)} recusado(s)'
                         + (f'; {qtd_aviso} com Responsabilidade do Produtor' if qtd_aviso else ''))
            id_operacao = registrar_operacao(db, id_usuario=id_usuario, id_propriedade=int(id_propriedade),
                                             modulo=MODULO_LOG, descricao=descricao[:255])
            for id_emb, sisbov_emb in ids_gravados:
                registrar_item(db, id_operacao, 'tb_2020_embarque', id_emb, 'INSERT', None,
                               {'sisbov': sisbov_emb, 'data_embarque': data_embarque.strftime('%Y-%m-%d')})
        db.commit()

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)

    # ---- v1.2.0: CAIXA DE SUCESSO (Padrao No7) ----
    # O resumo e montado aqui (tudo ja lido antes do commit) e mostrado direto, sem banner na tela seguinte.
    qtd_aviso = sum(1 for g in gravados if g['aviso'])
    mudancas = [
        {'campo': 'Propriedade', 'antes': None, 'depois': f'{produtor_nome} — {propriedade_nome} — {propriedade_local}'},
        {'campo': 'Animais gravados', 'antes': None, 'depois': str(len(gravados))},
        {'campo': 'Ficaram de fora', 'antes': None, 'depois': str(len(recusados))},
    ]
    if qtd_aviso:
        mudancas.append({'campo': 'Responsabilidade do Produtor', 'antes': None, 'depois': f'{qtd_aviso} animal(is) assumido(s)'})
    avisos = []
    sem_peso = sum(1 for g in gravados if not g['peso'])   # v1.3.0 - so avisa quem nao tem nenhum peso anterior
    if sem_peso:
        avisos.append(f'{sem_peso} animal(is) sem peso anterior: preencha o peso na Consulta Embarque (Correção).')
    if recusados:
        avisos.append(f'{len(recusados)} brinco(s) ficou(aram) de fora. Veja o motivo na lista abaixo.')
    tabelas = []
    if recusados:
        tabelas.append({'titulo': f'Ficaram de fora ({len(recusados)})', 'colunas': ['Brinco', 'Motivo'],
                        'linhas': [[r['sisbov'], r['motivo']] for r in recusados], 'ultima_vermelha': True})
    if gravados:
        tabelas.append({'titulo': f'Gravados ({len(gravados)})', 'colunas': ['SISBOV', 'Manejo', 'Sexo', 'Idade (no embarque)', 'Peso (kg)', 'Aviso'],
                        'linhas': [[g['sisbov'], g['manejo'], g['sexo'], g['faixa'], g['peso'] or '—',
                                    'assumido pelo Produtor' if g['aviso'] else '—'] for g in gravados]})
    return render_caixa_sucesso(
        _contexto_base(),
        titulo=('Abate por Arquivo concluído!' if gravados else 'Nenhum animal foi gravado'),
        subtitulo=f'Embarque de {_data_br(data_embarque)}',
        mudancas=mudancas, avisos=avisos, tabelas=tabelas,
        botoes=[{'texto': 'Abrir Consulta Embarque', 'url': URL_CONSULTA_EMBARQUE, 'primario': True},
                {'texto': 'Enviar outro arquivo', 'url': f'{URL_ARQUIVO}?id_propriedade={int(id_propriedade)}', 'primario': False},
                {'texto': 'Hub de Saídas', 'url': URL_HUB, 'primario': False}],
        url_voltar=URL_HUB,
        icone=('&#9989;' if gravados else '&#9888;&#65039;'),
        titulo_pagina='Orion SISBOV — Abate por Arquivo',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\saida_arquivo.py
# =========================================================
