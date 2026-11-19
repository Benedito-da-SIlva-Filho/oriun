# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\morte_arquivo.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-01 17:40 -03
# ATUALIZADO EM: 2026-11-01 17:40 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     MORTE POR ARQUIVO TEXTO (pacote 3). O .txt traz so a numeracao dos brincos (15 posicoes, um por linha); a Data da Morte, o Tipo, a
#     Causa Mortis e o Destino sao escolhidos UMA vez na tela e valem para TODOS os animais do arquivo (ex.: varios animais mortos por
#     descarga eletrica na mesma data). Um arquivo = UM lancamento = UM Controle Interno (MRT, origem ARQUIVO) com N animais.
#     Fluxo: escolher dados + arquivo -> previa (quem entra e quem fica de fora, com o motivo) -> "Revisei os dados e confirmo" -> gravar.
#     Cada brinco passa pela MESMA conferencia do lancamento individual (_conferir_animal) e pelas mesmas regras de data. A baixa e na hora
#     (morte_lancamento._baixar_animal). Tudo ou nada na gravacao do MRT; quem nao passa na conferencia fica de fora e aparece na tela final.
#     Log de Operacoes modulo 'morte' (UMA operacao por arquivo; o Desfazer devolve todos os animais, so ate gerar a Notificacao).
#
#     ROTAS (/produtor/morte/por-arquivo/): iniciar, arquivo (GET), conferir (POST), gravar (POST).
#
#     v1.0.0: Sessao 111 (01/11/2026) - Criacao. REVERSAO: apagar este arquivo e os morte_arquivo_*.html; desfazer o registro em app.py e no Hub.
# =========================================================
import json
from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models.tb_1007_motivo_mortes import MotivoMorte
from backend.models.tb_2013_com_morte import ControleMorte
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.saida_arquivo import _extrair_brincos, _decodificar, _recusados_da_previa, LIMITE_BRINCOS, LIMITE_BYTES
from backend.routers.saida_consulta import _contexto_base, _propriedade_do_usuario, _negado, _data_br, _nomes, _ler_iso, URL_HUB
from backend.routers.morte_lancamento import (
    _conferir_animal, _data_minima, _baixar_animal, _proximo_controle, _texto_controle, _causas,
    TIPOS_MORTE, DESTINOS_MORTE, CODIGOS_TIPO, CODIGOS_DESTINO, CLASSE_TRAVA_MORTE, MODULO_LOG, URL_LANCAR,
)
from backend.utils.caixa_sucesso import render_caixa_sucesso
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.multitenant import get_db_produtor

morte_arquivo = Blueprint('morte_arquivo', __name__)

URL_INICIAR = '/produtor/morte/por-arquivo/iniciar'
URL_ARQUIVO = '/produtor/morte/por-arquivo/arquivo'
URL_CONFERIR = '/produtor/morte/por-arquivo/conferir'
URL_GRAVAR = '/produtor/morte/por-arquivo/gravar'
ANO_MINIMO = 2000


# =========================================================
# BLOCO 1 - Apoio
# =========================================================
def _ler_dados(form):
    """Data, Tipo, Causa e Destino do formulario. Devolve (dados, erro)."""
    data_iso = form.get('data', '')
    data_morte = _ler_iso(data_iso)
    tipo = str(form.get('tipo_morte') or '').strip().upper()
    destino = str(form.get('destino_morte') or '').strip().upper()
    try:
        id_motivo = int(form.get('id_motivo'))
    except (TypeError, ValueError):
        id_motivo = None
    if data_morte is None or data_morte.year < ANO_MINIMO:
        return None, 'Data da Morte incorreta.'
    if data_morte > date.today():
        return None, 'A Data da Morte não pode ser futura.'
    if tipo not in CODIGOS_TIPO:
        return None, 'Escolha o Tipo da Morte.'
    if id_motivo is None:
        return None, 'Escolha a Causa Mortis.'
    if destino not in CODIGOS_DESTINO:
        return None, 'Escolha o Destino.'
    with Session(engine) as dbp:
        motivo = dbp.query(MotivoMorte).filter(MotivoMorte.id == id_motivo, MotivoMorte.ativo == True).first()   # noqa: E712
        descricao_causa = motivo.descricao if motivo else None
    if descricao_causa is None:
        return None, 'Causa Mortis inválida.'
    return {'data': data_morte, 'data_iso': data_iso, 'tipo': tipo, 'id_motivo': id_motivo, 'causa_texto': descricao_causa, 'destino': destino}, None


def _rotulo(opcoes, codigo):
    return dict(opcoes).get(codigo, codigo)


def _conferir_brincos(db, id_propriedade, data_morte, brincos):
    """Cada brinco passa pela conferencia do lancamento individual + regra da data. Lista: {sisbov, situacao ok|recusado, motivo, manejo, sexo, animal}."""
    saida = []
    for sisbov in brincos:
        item = {'sisbov': sisbov, 'situacao': 'recusado', 'motivo': '', 'manejo': '', 'sexo': '', 'lote': '', 'animal': None}
        resultado = _conferir_animal(db, id_propriedade, sisbov, '', '')
        if 'bloqueio' in resultado:
            item['motivo'] = resultado['bloqueio']
        else:
            animal = resultado['animal']
            minima = _data_minima(animal)
            if minima is not None and data_morte < minima:
                item['motivo'] = f'Data da Morte anterior à entrada do animal ({_data_br(minima)}).'
            else:
                item.update({'situacao': 'ok', 'manejo': animal.manejo or '', 'lote': animal.lote or '',
                             'sexo': 'Fêmea' if animal.sexo == 'FEMEA' else ('Macho' if animal.sexo == 'MACHO' else '-'),
                             'animal': animal})
        saida.append(item)
    return saida


def _tela_arquivo(id_propriedade, erro=None, valores=None):
    id_produtor = session['id_produtor']
    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    valores = valores or {}
    return render_template(
        'produtor/morte_arquivo_selecao.html',
        erro=erro, id_propriedade=int(id_propriedade), valores=valores,
        causas=_causas(), tipos=TIPOS_MORTE, destinos=DESTINOS_MORTE,
        hoje_iso=date.today().strftime('%Y-%m-%d'),
        url_conferir=URL_CONFERIR, url_voltar=URL_HUB,
        produtor_nome=produtor_nome, propriedade_nome=propriedade_nome, propriedade_local=propriedade_local,
        **_contexto_base())


# =========================================================
# BLOCO 2 - Rotas
# =========================================================
@morte_arquivo.route('/produtor/morte/por-arquivo/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html', pares=pares_lista, erro=erro,
            titulo='Morte por Arquivo — Selecionar Propriedade', proximo=URL_ARQUIVO, campo_propriedade='id_propriedade',
            voltar=URL_HUB, **_contexto_base())

    if len(pares) == 0:
        return _tela_selecionar([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor'] = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{URL_ARQUIVO}?id_propriedade={par_em_uso.id_propriedade}')
    if len(pares) == 1:
        par = pares[0]
        session['id_produtor'] = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_ARQUIVO}?id_propriedade={par.id_propriedade}')
    return _tela_selecionar(pares, None)


@morte_arquivo.route('/produtor/morte/por-arquivo/arquivo')
def arquivo():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    return _tela_arquivo(id_propriedade)


@morte_arquivo.route('/produtor/morte/por-arquivo/conferir', methods=['POST'])
def conferir():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.form.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']
    valores = {'data': request.form.get('data', ''), 'tipo_morte': request.form.get('tipo_morte', ''),
               'id_motivo': request.form.get('id_motivo', ''), 'destino_morte': request.form.get('destino_morte', '')}

    dados, erro = _ler_dados(request.form)
    if erro:
        return _tela_arquivo(id_propriedade, erro, valores)
    arq = request.files.get('arquivo')
    if arq is None or not arq.filename:
        return _tela_arquivo(id_propriedade, 'Escolha o arquivo (TXT ou CSV).', valores)
    if not arq.filename.lower().endswith(('.txt', '.csv')):
        return _tela_arquivo(id_propriedade, 'Formato não aceito. Use arquivo TXT ou CSV.', valores)
    bruto = arq.read(LIMITE_BYTES + 1)
    if len(bruto) > LIMITE_BYTES:
        return _tela_arquivo(id_propriedade, 'Arquivo grande demais (máximo 1 MB).', valores)
    lido = _extrair_brincos(_decodificar(bruto))
    if not lido['brincos'] and not lido['fora_padrao']:
        return _tela_arquivo(id_propriedade, 'Não encontrei nenhum número de brinco no arquivo.', valores)
    if len(lido['brincos']) > LIMITE_BRINCOS:
        return _tela_arquivo(id_propriedade, f'Arquivo com mais de {LIMITE_BRINCOS} brincos. Divida em dois.', valores)

    with get_db_produtor(id_produtor) as db:
        itens = _conferir_brincos(db, id_propriedade, dados['data'], lido['brincos'])
        proximo = _proximo_controle(db, id_propriedade)

    linhas = [{k: v for k, v in i.items() if k != 'animal'} for i in itens]
    recusados = [l for l in linhas if l['situacao'] == 'recusado']
    recusados += [{'sisbov': n, 'situacao': 'recusado', 'motivo': f'Fora do padrão: tem {len(n)} dígitos (o brinco tem 15).',
                   'manejo': '', 'sexo': '', 'lote': ''} for n in lido['fora_padrao']]
    entram = [l for l in linhas if l['situacao'] == 'ok']

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/morte_arquivo_conferencia.html',
        entram=entram, recusados=recusados, repetidos=lido['repetidos'], ignorados=lido['ignorados'],
        nome_arquivo=arq.filename, data_br=_data_br(dados['data']), data_iso=dados['data_iso'],
        tipo_morte=dados['tipo'], tipo_texto=_rotulo(TIPOS_MORTE, dados['tipo']),
        id_motivo=dados['id_motivo'], causa_texto=dados['causa_texto'],
        destino_morte=dados['destino'], destino_texto=_rotulo(DESTINOS_MORTE, dados['destino']),
        controle_texto=_texto_controle(proximo),
        sisbovs='\n'.join(l['sisbov'] for l in entram),
        recusados_json=json.dumps([{'sisbov': r['sisbov'], 'motivo': r['motivo']} for r in recusados], ensure_ascii=False),
        id_propriedade=int(id_propriedade), url_gravar=URL_GRAVAR,
        url_voltar=f'{URL_ARQUIVO}?id_propriedade={int(id_propriedade)}',
        produtor_nome=produtor_nome, propriedade_nome=propriedade_nome, propriedade_local=propriedade_local,
        **_contexto_base())


@morte_arquivo.route('/produtor/morte/por-arquivo/gravar', methods=['POST'])
def gravar():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.form.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_propriedade = int(id_propriedade)
    id_produtor = session['id_produtor']
    id_usuario = session.get('usuario_id')

    dados, erro = _ler_dados(request.form)
    if erro:
        return _tela_arquivo(id_propriedade, f'{erro} Envie o arquivo de novo.')
    if request.form.get('confirmo') != '1':
        return _tela_arquivo(id_propriedade, 'Faltou marcar "Revisei os dados e confirmo". Envie o arquivo de novo.')
    brincos = _extrair_brincos(request.form.get('sisbovs', ''))['brincos'][:LIMITE_BRINCOS]
    if not brincos:
        return _tela_arquivo(id_propriedade, 'Nenhum brinco para gravar. Envie o arquivo de novo.')

    recusados = _recusados_da_previa(request.form.get('recusados', ''))
    gravados = []
    texto_mrt = None
    controle = None
    try:
        with get_db_produtor(id_produtor) as db:
            db.execute(text('SELECT pg_advisory_xact_lock(:classe, :id_propriedade)'),
                       {'classe': CLASSE_TRAVA_MORTE, 'id_propriedade': id_propriedade})
            itens = _conferir_brincos(db, id_propriedade, dados['data'], brincos)   # confere de novo (defesa em profundidade)
            ok = []
            for item in itens:
                if item['situacao'] == 'ok':
                    ok.append(item)
                else:
                    recusados.append({'sisbov': item['sisbov'], 'motivo': item['motivo']})
            if ok:
                controle = _proximo_controle(db, id_propriedade)
                texto_mrt = _texto_controle(controle)
                id_operacao = registrar_operacao(
                    db, id_usuario=id_usuario, id_propriedade=id_propriedade, modulo=MODULO_LOG,
                    descricao=(f'Morte por Arquivo {texto_mrt} — {len(ok)} animal(is) — {_data_br(dados["data"])} — '
                               f'{_rotulo(TIPOS_MORTE, dados["tipo"])} — {dados["causa_texto"]}')[:255])
                ctrl = ControleMorte(id_propriedade=id_propriedade, controle=controle, data_morte=dados['data'],
                                     qtd_animais=len(ok), origem='ARQUIVO', id_usuario=id_usuario)
                db.add(ctrl)
                db.flush()
                registrar_item(db, id_operacao, 'tb_2013_com_morte', ctrl.id, 'INSERT', None,
                               {'controle': controle, 'data_morte': _data_br(dados['data'])})
                for item in ok:
                    animal = item['animal']
                    _baixar_animal(db, id_operacao, id_propriedade, animal, ctrl, controle, dados['data'],
                                   dados['tipo'], dados['id_motivo'], dados['destino'])
                    gravados.append({'sisbov': item['sisbov'], 'manejo': item['manejo'], 'sexo': item['sexo']})
            db.commit()
    except IntegrityError:
        return _tela_arquivo(id_propriedade, 'Não foi possível gravar (algum animal pode ter sido lançado em outra tela). Envie o arquivo de novo.')

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    mudancas = [
        {'campo': 'Propriedade', 'antes': None, 'depois': f'{produtor_nome} — {propriedade_nome} — {propriedade_local}'},
        {'campo': 'Controle Interno', 'antes': None, 'depois': texto_mrt or '-'},
        {'campo': 'Data da Morte', 'antes': None, 'depois': _data_br(dados['data'])},
        {'campo': 'Tipo / Causa / Destino', 'antes': None,
         'depois': f'{_rotulo(TIPOS_MORTE, dados["tipo"])} — {dados["causa_texto"]} — {_rotulo(DESTINOS_MORTE, dados["destino"])}'},
        {'campo': 'Animais baixados', 'antes': None, 'depois': str(len(gravados))},
        {'campo': 'Ficaram de fora', 'antes': None, 'depois': str(len(recusados))},
    ]
    avisos = []
    if recusados:
        avisos.append(f'{len(recusados)} brinco(s) ficou(aram) de fora. Veja o motivo na lista abaixo.')
    tabelas = []
    if recusados:
        tabelas.append({'titulo': f'Ficaram de fora ({len(recusados)})', 'colunas': ['Brinco', 'Motivo'],
                        'linhas': [[r['sisbov'], r['motivo']] for r in recusados], 'ultima_vermelha': True})
    if gravados:
        tabelas.append({'titulo': f'Baixados ({len(gravados)})', 'colunas': ['SISBOV', 'Manejo', 'Sexo'],
                        'linhas': [[g['sisbov'], g['manejo'], g['sexo']] for g in gravados]})
    return render_caixa_sucesso(
        _contexto_base(),
        titulo=('Morte por Arquivo concluída!' if gravados else 'Nenhum animal foi baixado'),
        subtitulo=(f'{texto_mrt} — {_data_br(dados["data"])}' if texto_mrt else _data_br(dados['data'])),
        mudancas=mudancas, avisos=avisos, tabelas=tabelas,
        botoes=([{'texto': 'Anexar fotos', 'url': f'/produtor/morte/fotos/{controle}?id_propriedade={id_propriedade}', 'primario': True}] if (gravados and controle) else [])
               + [{'texto': 'Enviar outro arquivo', 'url': f'{URL_ARQUIVO}?id_propriedade={id_propriedade}', 'primario': not (gravados and controle)},
                {'texto': 'Lançar uma Morte', 'url': f'{URL_LANCAR}?id_propriedade={id_propriedade}', 'primario': False},
                {'texto': 'Hub de Saídas', 'url': URL_HUB, 'primario': False}],
        url_voltar=URL_HUB,
        icone=('&#9989;' if gravados else '&#9888;&#65039;'),
        titulo_pagina='Orion SISBOV — Morte por Arquivo',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\morte_arquivo.py
# =========================================================
