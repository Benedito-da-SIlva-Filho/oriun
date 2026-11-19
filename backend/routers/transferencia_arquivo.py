# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\transferencia_arquivo.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-31 11:50 -03
# ATUALIZADO EM: 2026-10-31 11:50 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Transferencia por Arquivo Texto (Sessao 110) - grupo "Transferencia no brete" do Hub de Saidas.
#     Ultimo recurso sem internet no brete: o arquivo (TXT ou CSV) so tem o numero do brinco (SISBOV,
#     15 posicoes). O Orion le cada numero como se fosse a leitura no brete e grava a leitura da
#     Transferencia em tb_2020_embarque (tipo TRANSFER, SEM destino), igual ao Leitor da Transferencia.
#
#     REGRAS (fechadas com Benedito, 31/10/2026):
#       - O arquivo traz so a numeracao dos animais. A GTA NAO vem no arquivo: o destino vem da GTA de
#         Transferencia, depois, pelo Vincular (uma regra so, igual ao Leitor e ao Abate).
#       - Cada brinco e conferido pela MESMA conferencia do Leitor da Transferencia (_validar_transferencia):
#         animal na Propriedade, DV, ja saiu, entrada sem Comunicado, leitura em aberto.
#       - Data Leitura escolhida na tela. O PESO e o ultimo peso do animal (tb_4003_pesos), como no Leitor:
#         nunca e pedido no arquivo. Animal sem nenhum peso (base de teste) entra sem peso e a tela final avisa.
#       - Brinco invalido nao trava o resto: mostra uma PREVIA (quantos entram, quais ficam de fora e o motivo)
#         e so grava depois da confirmacao. Numero repetido no arquivo conta uma vez so.
#       - Depois de gravar, a leitura fica em aberto (sem GTA): o usuario abre a Selecao da Transferencia,
#         clica na leitura da data e usa "Concluir e vincular" com a GTA de Transferencia.
#       - Grava Log de Operacoes (modulo saida_arquivo, so historico, descricao 'Transferencia por Arquivo').
#
#     REUSO (peca unica): funcoes de leitura do arquivo de saida_arquivo.py (_extrair_brincos, _decodificar,
#     _data_valida, _recusados_da_previa) e a conferencia/peso do transferencia_leitura.py.
#
#     ROTAS (/produtor/transferencia/por-arquivo/):
#       iniciar   - resolve a Propriedade (fazenda em uso) e abre a tela do arquivo.
#       arquivo   - GET: escolher a Data Leitura e o arquivo.
#       conferir  - POST (arquivo): le, confere cada brinco e mostra a previa (nada e gravado).
#       gravar    - POST: confere de novo e grava as leituras.
#
#     v1.0.0: Sessao 110 (31/10/2026, 11:50 -03) - Criacao.
#     REVERSAO: remover este arquivo e os templates transferencia_arquivo_*.html; devolver os
#     .bak_antes_s110_transf_arquivo de app.py e hub_entrada_agrupado.py. As leituras gravadas saem
#     pelo X da lista Geral da Selecao da Transferencia (leitura em aberto) ou por SQL.
# =========================================================

import json
from datetime import datetime
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, session
from sqlalchemy.exc import IntegrityError

from backend.utils.caixa_sucesso import render_caixa_sucesso
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4001_gta import Gta
from backend.models.tb_parceiros import Parceiro
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.saida_arquivo import _extrair_brincos, _decodificar, _data_valida, _recusados_da_previa, LIMITE_BRINCOS, LIMITE_BYTES
from backend.routers.saida_consulta import (
    _contexto_base, _propriedade_do_usuario, _negado, _data_br, _nomes, _ler_iso, URL_HUB,
)
from backend.routers.transferencia_leitura import (
    _validar_transferencia, _ultimo_peso, _formatar_kg, TIPO_SAIDA_TRANSFER, _url as _url_transferencia,
)
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.multitenant import get_db_produtor

transferencia_arquivo = Blueprint('transferencia_arquivo', __name__)

URL_INICIAR = '/produtor/transferencia/por-arquivo/iniciar'
URL_ARQUIVO = '/produtor/transferencia/por-arquivo/arquivo'
URL_CONFERIR = '/produtor/transferencia/por-arquivo/conferir'
URL_GRAVAR = '/produtor/transferencia/por-arquivo/gravar'
MODULO_LOG = 'saida_arquivo'   # modulo do Log de Operacoes (so historico), o mesmo do Abate por Arquivo


# =========================================================
# BLOCO 1 - Acesso ao banco
# =========================================================
def _conferir_brincos(db, id_propriedade, data_leitura, brincos):
    """
    Confere cada brinco como o Leitor da Transferencia confere (sem GTA escolhida).
    Devolve lista de dicts na ordem do arquivo:
      {sisbov, situacao: 'ok' | 'recusado', motivo, manejo, sexo, faixa, peso, animal}
    """
    saida = []
    for sisbov in brincos:
        item = {'sisbov': sisbov, 'situacao': 'recusado', 'motivo': '', 'manejo': '', 'sexo': '',
                'faixa': '', 'peso': '', 'animal': None}
        resultado = _validar_transferencia(db, id_propriedade, data_leitura, sisbov, '', '', None)
        if 'bloqueio' in resultado:
            item['motivo'] = resultado['bloqueio']
        elif 'repetido' in resultado:
            item['motivo'] = f"Já está em leitura em aberto (data {resultado['repetido']['data']})."
        else:
            animal, ficha = resultado['animal'], resultado['ficha']
            item.update({
                'situacao': 'ok', 'manejo': ficha['manejo'], 'faixa': ficha['idade_meses'],
                'peso': ficha['peso_anterior'],
                'sexo': 'Fêmea' if animal.sexo == 'FEMEA' else ('Macho' if animal.sexo == 'MACHO' else '-'),
                'animal': animal,
            })
        saida.append(item)
    return saida


def _novo_embarque(db, id_propriedade, data_leitura, animal, agora):
    """Mesma leitura que o gravar() do Leitor da Transferencia monta (tipo TRANSFER, sem destino)."""
    gta = db.get(Gta, animal.id_gta_entrada) if animal.id_gta_entrada else None
    origem = db.get(Parceiro, animal.id_origem) if animal.id_origem else None
    ultimo = _ultimo_peso(db, animal.sisbov)
    peso = Decimal(str(ultimo.peso)).quantize(Decimal('0.01')) if ultimo is not None else None
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
        tipo_saida=TIPO_SAIDA_TRANSFER, data_embarque=data_leitura,
        hora_embarque=agora.time().replace(microsecond=0),
        lote_saida=None, peso_saida=peso, elemento=None,
        sts=False,
    ), peso


# =========================================================
# BLOCO 2 - Rotas
# =========================================================
def _tela_arquivo(id_propriedade, erro=None, data_iso=None):
    from datetime import date
    id_produtor = session['id_produtor']
    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/transferencia_arquivo_selecao.html',
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
# GET /produtor/transferencia/por-arquivo/iniciar
# -------------------------------------------------------
@transferencia_arquivo.route('/produtor/transferencia/por-arquivo/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista,
            erro=erro,
            titulo='Transferência por Arquivo — Selecionar Propriedade',
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
# GET /produtor/transferencia/por-arquivo/arquivo
# -------------------------------------------------------
@transferencia_arquivo.route('/produtor/transferencia/por-arquivo/arquivo')
def arquivo():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    return _tela_arquivo(id_propriedade)


# -------------------------------------------------------
# POST /produtor/transferencia/por-arquivo/conferir - le o arquivo e mostra a previa (nao grava nada).
# -------------------------------------------------------
@transferencia_arquivo.route('/produtor/transferencia/por-arquivo/conferir', methods=['POST'])
def conferir():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.form.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']

    data_iso = request.form.get('data', '')
    data_leitura = _ler_iso(data_iso)
    if not _data_valida(data_leitura):
        return _tela_arquivo(id_propriedade, 'Data Leitura inválida (de 2020 até 30 dias à frente).', data_iso)
    arq = request.files.get('arquivo')
    if arq is None or not arq.filename:
        return _tela_arquivo(id_propriedade, 'Escolha o arquivo TXT (ou CSV) com os brincos.', data_iso)
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
        itens = _conferir_brincos(db, id_propriedade, data_leitura, lido['brincos'])

    linhas = [{k: v for k, v in i.items() if k != 'animal'} for i in itens]
    recusados = [l for l in linhas if l['situacao'] == 'recusado']
    recusados += [{'sisbov': n, 'situacao': 'recusado', 'motivo': f'Fora do padrão: tem {len(n)} dígitos (o brinco tem 15).',
                   'manejo': '', 'sexo': '', 'faixa': '', 'peso': ''} for n in lido['fora_padrao']]
    entram = [l for l in linhas if l['situacao'] == 'ok']

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/transferencia_arquivo_conferencia.html',
        entram=entram,
        recusados=recusados,
        qtd_sem_peso=sum(1 for e in entram if not e['peso']),
        repetidos=lido['repetidos'],
        ignorados=lido['ignorados'],
        nome_arquivo=arq.filename,
        data_iso=data_leitura.strftime('%Y-%m-%d'),
        data_leitura=_data_br(data_leitura),
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
# POST /produtor/transferencia/por-arquivo/gravar - confere de novo e grava as leituras.
# -------------------------------------------------------
@transferencia_arquivo.route('/produtor/transferencia/por-arquivo/gravar', methods=['POST'])
def gravar():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.form.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']

    data_leitura = _ler_iso(request.form.get('data', ''))
    if not _data_valida(data_leitura):
        return _tela_arquivo(id_propriedade, 'Data Leitura inválida. Envie o arquivo de novo.')
    if request.form.get('confirmo') != '1':
        return _tela_arquivo(id_propriedade, 'Faltou marcar "Revisei os dados e confirmo". Envie o arquivo de novo.')
    brincos = _extrair_brincos(request.form.get('sisbovs', ''))['brincos'][:LIMITE_BRINCOS]
    if not brincos:
        return _tela_arquivo(id_propriedade, 'Nenhum brinco para gravar. Envie o arquivo de novo.')
    id_usuario = session.get('usuario_id')

    gravados, recusados = [], _recusados_da_previa(request.form.get('recusados', ''))
    ids_gravados = []   # ids dos Embarques gravados (para o Log)
    with get_db_produtor(id_produtor) as db:
        itens = _conferir_brincos(db, id_propriedade, data_leitura, brincos)
        agora = datetime.now()
        for item in itens:
            if item['situacao'] == 'recusado':
                recusados.append({'sisbov': item['sisbov'], 'motivo': item['motivo']})
                continue
            emb, peso = _novo_embarque(db, id_propriedade, data_leitura, item['animal'], agora)
            try:
                with db.begin_nested():
                    db.add(emb)
                    db.flush()
            except IntegrityError:
                recusados.append({'sisbov': item['sisbov'], 'motivo': 'Já está em uma leitura em aberto.'})
                continue
            gravados.append({'sisbov': item['sisbov'], 'manejo': item['manejo'], 'sexo': item['sexo'],
                             'faixa': item['faixa'], 'peso': _formatar_kg(peso) if peso is not None else ''})
            ids_gravados.append((emb.id, item['sisbov']))
        # ---- Log de Operacoes (uma operacao por importacao; so historico) ----
        if ids_gravados:
            descricao = (f'Transferência por Arquivo: {len(gravados)} animal(is) gravado(s) como leitura de {_data_br(data_leitura)}; '
                         f'{len(recusados)} recusado(s)')
            id_operacao = registrar_operacao(db, id_usuario=id_usuario, id_propriedade=int(id_propriedade),
                                             modulo=MODULO_LOG, descricao=descricao[:255])
            for id_emb, sisbov_emb in ids_gravados:
                registrar_item(db, id_operacao, 'tb_2020_embarque', id_emb, 'INSERT', None,
                               {'sisbov': sisbov_emb, 'data_embarque': data_leitura.strftime('%Y-%m-%d'), 'tipo_saida': TIPO_SAIDA_TRANSFER})
        db.commit()

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)

    # ---- CAIXA DE SUCESSO (Padrao No7): resumo montado aqui, com tudo ja lido antes do commit ----
    sem_peso = sum(1 for g in gravados if not g['peso'])
    mudancas = [
        {'campo': 'Propriedade', 'antes': None, 'depois': f'{produtor_nome} — {propriedade_nome} — {propriedade_local}'},
        {'campo': 'Animais gravados', 'antes': None, 'depois': str(len(gravados))},
        {'campo': 'Ficaram de fora', 'antes': None, 'depois': str(len(recusados))},
    ]
    avisos = []
    if gravados:
        avisos.append('Falta vincular à GTA de Transferência: abra a Seleção, clique na leitura desta data e use "Concluir e vincular".')
    if sem_peso:
        avisos.append(f'{sem_peso} animal(is) sem peso anterior: preencha o peso na Consulta Embarque (Correção).')
    if recusados:
        avisos.append(f'{len(recusados)} brinco(s) ficou(aram) de fora. Veja o motivo na lista abaixo.')
    tabelas = []
    if recusados:
        tabelas.append({'titulo': f'Ficaram de fora ({len(recusados)})', 'colunas': ['Brinco', 'Motivo'],
                        'linhas': [[r['sisbov'], r['motivo']] for r in recusados], 'ultima_vermelha': True})
    if gravados:
        tabelas.append({'titulo': f'Gravados ({len(gravados)})', 'colunas': ['SISBOV', 'Manejo', 'Sexo', 'Idade (na leitura)', 'Peso (kg)'],
                        'linhas': [[g['sisbov'], g['manejo'], g['sexo'], g['faixa'], g['peso'] or '—'] for g in gravados]})
    url_selecao = f"{_url_transferencia('leitor', 'selecao')}?id_propriedade={int(id_propriedade)}"
    return render_caixa_sucesso(
        _contexto_base(),
        titulo=('Transferência por Arquivo concluída!' if gravados else 'Nenhum animal foi gravado'),
        subtitulo=f'Leitura de {_data_br(data_leitura)}',
        mudancas=mudancas, avisos=avisos, tabelas=tabelas,
        botoes=[{'texto': 'Abrir a Transferência (vincular à GTA)', 'url': url_selecao, 'primario': True},
                {'texto': 'Enviar outro arquivo', 'url': f'{URL_ARQUIVO}?id_propriedade={int(id_propriedade)}', 'primario': False},
                {'texto': 'Hub de Saídas', 'url': URL_HUB, 'primario': False}],
        url_voltar=URL_HUB,
        icone=('&#9989;' if gravados else '&#9888;&#65039;'),
        titulo_pagina='Orion SISBOV — Transferência por Arquivo',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\transferencia_arquivo.py
# =========================================================
