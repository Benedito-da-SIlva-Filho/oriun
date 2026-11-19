# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\leituras_vinculo.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-10 13:40 -03
# ATUALIZADO EM: 2026-11-10 13:40 -03
# VERSAO: 1.0.0
# v1.0.0: Sessao 120 (2026-11-10 13:40 -03) - Criacao. Regra de Ouro #67: animal VINCULADO a uma GTA nunca aparece como livre; a tela diz a qual GTA ele esta. REVERSAO: apagar este arquivo e devolver os .bak_antes_s120_livres_* dos routers/templates.
#
# DESCRICAO:
#     Pecas COMPARTILHADAS pelas telas de Selecao e Leitura de Abate, Transferencia, Venda e Posse:
#       - resumo_abertas(db, id_propriedade, tipo): leituras em aberto (sem Comunicado) por data, SEPARADAS em
#         LIVRES (sem GTA) e VINCULADAS (ja numa GTA, com o numero da GTA).
#       - numeros_gta(db, ids): {id_gta: numero completo da GTA}.
#       - marcar_gtas_atendidas(...): marca, na lista de GTAs da Selecao, as que os animais LIVRES ja lidos atendem
#         (atendida_em) ou ultrapassam (sobra_em).
#     So leitura - nunca grava nem da commit.
# =========================================================

from sqlalchemy import func

from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4001_gta import Gta


# -------------------------------------------------------
# {id_gta: numero completo}. Ids vazios sao ignorados.
# -------------------------------------------------------
def numeros_gta(db, ids):
    ids = {int(i) for i in ids if i is not None}
    if not ids:
        return {}
    return {g.id: g.numero_gta_completo for g in db.query(Gta).filter(Gta.id.in_(ids)).all()}


# -------------------------------------------------------
# Leituras em aberto (sts = False) de UM tipo, por data, mais recente primeiro.
# Devolve [{'data': date, 'livres': n, 'vinculados': m, 'gtas_txt': 'MTS112233, ...'}].
# -------------------------------------------------------
def resumo_abertas(db, id_propriedade, tipo):
    linhas = (
        db.query(Embarque.data_embarque, Embarque.id_gta, func.count(Embarque.id))
        .filter(Embarque.id_propriedade == int(id_propriedade), Embarque.tipo_saida == tipo, Embarque.sts == False)   # noqa: E712
        .group_by(Embarque.data_embarque, Embarque.id_gta)
        .order_by(Embarque.data_embarque.desc())
        .all()
    )
    nomes = numeros_gta(db, [g for _d, g, _q in linhas])
    por_data = {}
    ordem = []
    for data, id_gta, qtd in linhas:
        if data not in por_data:
            por_data[data] = {'data': data, 'livres': 0, 'vinculados': 0, 'gtas': []}
            ordem.append(data)
        item = por_data[data]
        if id_gta is None:
            item['livres'] += int(qtd)
        else:
            item['vinculados'] += int(qtd)
            numero = nomes.get(id_gta, '')
            if numero and numero not in item['gtas']:
                item['gtas'].append(numero)
    resultado = []
    for data in ordem:
        item = por_data[data]
        item['gtas_txt'] = ', '.join(item.pop('gtas'))
        resultado.append(item)
    return resultado


# -------------------------------------------------------
# Marca cada GTA da lista da Selecao (dicts com 'id'):
#   atendida_em = data (texto dd/mm/aaaa) em que os animais LIVRES lidos atendem EXATAMENTE o pedido;
#   sobra_em    = data em que cobrem o pedido mas ha animais a mais (escolher na conferencia).
# progresso_fn = o _progresso_gta do proprio router (db, id_propriedade, data, gta) -> dict. Erro em uma GTA nao quebra a tela.
# -------------------------------------------------------
def marcar_gtas_atendidas(db, id_propriedade, gtas, resumo, progresso_fn):
    for g in gtas:
        try:
            gta = db.get(Gta, g['id'])
            if gta is None:
                continue
            for r in resumo:
                if not r['livres']:
                    continue
                p = progresso_fn(db, id_propriedade, r['data'], gta)
                texto = r['data'].strftime('%d/%m/%Y')
                if p.get('completo'):
                    g['atendida_em'] = texto
                    break
                if p.get('linhas') and all(l['lidos'] >= l['pede'] for l in p['linhas']) and 'sobra_em' not in g:
                    g['sobra_em'] = texto
        except Exception:
            continue

# =========================================================
# FIM DE ARQUIVO: backend\utils\leituras_vinculo.py
# =========================================================
