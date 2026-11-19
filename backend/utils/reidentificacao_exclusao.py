# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\reidentificacao_exclusao.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-11 14:10 -03
# ATUALIZADO EM: 2026-11-11 18:40 -03
# VERSAO: 2.1.0
#
# DESCRICAO:
#     Reidentificacao (Sessao 121): EXCLUIR UM ANIMAL PENDENTE de Notificacao, na tela Consulta da Reidentificacao (o usuario percebeu o erro
#     ao conferir). Decisao do Benedito (11/11/2026): so enquanto o animal esta PENDENTE (sem Notificacao gerada); sem motivo; sem tabela de
#     exclusoes: o brinco volta ao estado anterior e fica apenas o registro interno no Log. O numero da Notificacao nao e afetado (ele so
#     nasce ao gerar).
#
#     O que volta ao que era (tudo ou nada, na mesma transacao): o brinco perdido volta ao rebanho (linha inteira guardada no Log), o
#     brinco novo sai do rebanho e volta ao estoque (tb_7017), o historico de pesos volta ao SISBOV perdido, saem as linhas de tb_2002,
#     tb_2017, tb_3008, tb_7002 (PIA) e tb_6006 do animal, e o lote do brinco novo recupera o saldo (tb_3007). Blockchain: os 2 eventos do
#     animal sao cancelados (ou estornados, se ja foram enviados).
#
#     TRAVAS (mensagem diz o motivo e nada e alterado): animal ja em Notificacao gerada; brinco perdido de volta ao rebanho; brinco novo que
#     ja nao esta no rebanho; outra movimentacao ou pesagem do animal depois da reidentificacao. A ordem da exclusao e livre.
#
#     Registra no Log a operacao 'reidentificacao_exclusao' (so historico).
#
#     Funcao: excluir_animal(db, id_propriedade, id_item, id_usuario) -> (ok, mensagem). Nao da commit (quem chama decide).
#
#     v1.0.0: Criacao (Sessao 121, 11/11/2026, 14:10 -03) - exclusao de animal dentro de um pedido.
#     v2.0.0: Sessao 121 (2026-11-11 17:30 -03) - Modelo PENDENTES: o animal nao pertence a pedido; localiza o lancamento pelo item tb_6006 INSERT do Log; exige id_pedido vazio. REVERSAO: .bak_antes_s121_pendentes.
#     v2.1.0: Sessao 121 (2026-11-11 18:40 -03) - Sem a trava 'PIA nao e o ultimo': exclui em qualquer ordem (decisao do Benedito; o numero do PIA excluido nunca e reaproveitado). Animais novos nem tem PIA ate gerar a Notificacao; PIA de lancamento antigo (teste) sai junto. REVERSAO: .bak_antes_s121_pia.
# =========================================================

from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_3007_brincos_entrada import BrincoEntrada
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_6006_reidentificacao_com_baixa_itens import ReidentificacaoComBaixaItem
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.models.tb_log_operacoes import LogOperacao
from backend.models.tb_log_operacoes_itens import LogOperacaoItem
from backend.utils.blockchain import tratar_desfazer
from backend.utils.log_operacoes import registrar_operacao, registrar_item, _refletir_tabela, _valor_do_log

MODULO_LANCAMENTO = 'reidentificacao'
MODULO_EXCLUSAO = 'reidentificacao_exclusao'


def _campo(dados, nome):
    return (dados or {}).get(nome)


def excluir_animal(db, id_propriedade, id_item, id_usuario):
    linha = db.get(ReidentificacaoComBaixaItem, id_item)
    if linha is None or linha.id_propriedade != int(id_propriedade):
        return False, 'Animal não encontrado.'
    if linha.id_pedido is not None:
        return False, 'A Notificação deste animal já foi gerada: não é mais possível excluí-lo.'
    antigo, novo = linha.sisbov_antigo, linha.sisbov_novo

    # ---- operacao do lancamento (Log) e os itens que pertencem a ESTE animal ----
    operacao = (
        db.query(LogOperacao)
        .join(LogOperacaoItem, LogOperacaoItem.id_operacao == LogOperacao.id)
        .filter(LogOperacao.modulo == MODULO_LANCAMENTO, LogOperacao.id_propriedade == int(id_propriedade),
                LogOperacao.desfeito_em.is_(None),
                LogOperacaoItem.tabela == 'tb_6006_reidentificacao_com_baixa_itens',
                LogOperacaoItem.id_registro == linha.id, LogOperacaoItem.tipo_mudanca == 'INSERT')
        .first()
    )
    if operacao is None:
        return False, 'Não foi possível localizar o registro deste lançamento no Log.'
    itens_log = db.query(LogOperacaoItem).filter(LogOperacaoItem.id_operacao == operacao.id).order_by(LogOperacaoItem.id.asc()).all()

    brincos = db.query(EntradaBrincoRfid).filter(EntradaBrincoRfid.sisbov.in_([antigo, novo])).all()
    ids_brincos = {b.id for b in brincos}
    brinco_novo = next((b for b in brincos if b.sisbov == novo), None)

    sel, id_animal_novo, id_pia, ids_mov, ids_peso = [], None, None, [], []
    achou_baixa = achou_entrada = achou_linha = False
    for i in itens_log:
        t, m = i.tabela, i.tipo_mudanca
        if t == 'tb_2001' and m == 'DELETE' and _campo(i.dados_antes, 'sisbov') == antigo:
            sel.append(i); achou_baixa = True
        elif t == 'tb_2001' and m == 'INSERT' and _campo(i.dados_depois, 'sisbov') == novo:
            sel.append(i); id_animal_novo = i.id_registro; achou_entrada = True
        elif t == 'tb_2002_saida_animais' and m == 'INSERT' and _campo(i.dados_depois, 'sisbov') == antigo:
            sel.append(i)
        elif t == 'tb_2017_movimentacoes' and m == 'INSERT' and _campo(i.dados_depois, 'sisbov') in (antigo, novo):
            sel.append(i); ids_mov.append(i.id_registro)
        elif t == 'tb_4003_pesos' and m == 'UPDATE' and _campo(i.dados_depois, 'sisbov') == novo:
            sel.append(i); ids_peso.append(i.id_registro)
        elif t == 'tb_7017_entrada_brincos_rfid' and m == 'UPDATE' and i.id_registro in ids_brincos:
            sel.append(i)
        elif t == 'tb_3008_brincos_saida' and m == 'INSERT' and _campo(i.dados_depois, 'sisbov') == novo:
            sel.append(i)
        elif t == 'tb_7002_pia' and m == 'INSERT' and _campo(i.dados_depois, 'sisbov') == novo:
            sel.append(i); id_pia = i.id_registro
        elif t == 'tb_6006_reidentificacao_com_baixa_itens' and m == 'INSERT' and i.id_registro == linha.id:
            sel.append(i); achou_linha = True
    if not (achou_baixa and achou_entrada and achou_linha) or brinco_novo is None:
        return False, 'Não foi possível localizar todos os registros deste animal no Log.'

    # ---- travas: algo aconteceu depois com este animal? ----
    if db.query(Entrada.id).filter(Entrada.id == id_animal_novo).first() is None:
        return False, f'O animal {novo} (brinco novo) já não está na Propriedade.'
    if db.query(Entrada.id).filter(Entrada.id_propriedade == int(id_propriedade), Entrada.sisbov == antigo).first() is not None:
        return False, f'O brinco {antigo} já está de volta na Propriedade.'
    if ids_mov and db.query(Movimentacao.id).filter(Movimentacao.sisbov.in_([antigo, novo]), Movimentacao.id > max(ids_mov)).first() is not None:
        return False, f'O animal {novo} teve outra movimentação depois da Reidentificação.'
    consulta_peso = db.query(Peso.id).filter(Peso.sisbov == novo)
    if ids_peso:
        consulta_peso = consulta_peso.filter(~Peso.id.in_(ids_peso))
    if consulta_peso.first() is not None:
        return False, f'O animal {novo} foi pesado depois da Reidentificação.'
    id_lote = brinco_novo.id_lote_entrada

    # ---- blockchain: cancela/estorna so os 2 eventos deste animal ----
    tratar_desfazer(db, operacao.id, id_usuario, sisbovs=[antigo, novo])

    # ---- reverte os itens deste animal, do ultimo para o primeiro ----
    for i in reversed(sel):
        tabela = _refletir_tabela(db, i.tabela)
        if i.tipo_mudanca == 'UPDATE':
            if i.dados_antes:
                db.execute(tabela.update().where(tabela.c.id == i.id_registro).values(**i.dados_antes))
        elif i.tipo_mudanca == 'DELETE' and i.tabela == 'tb_2001':
            campos = {c.key: _valor_do_log(c, i.dados_antes[c.key]) for c in tabela.columns if c.key in (i.dados_antes or {})}
            db.execute(tabela.insert().values(**campos))
        elif i.tipo_mudanca == 'INSERT':
            db.execute(tabela.delete().where(tabela.c.id == i.id_registro))

    # ---- lote do brinco novo recupera o saldo ----
    if id_lote:
        lote = db.get(BrincoEntrada, id_lote)
        if lote is not None:
            lote.saldo = (lote.saldo or 0) + 1
            lote.qtde_saida = max((lote.qtde_saida or 0) - 1, 0)
    db.flush()

    id_op = registrar_operacao(
        db, id_usuario=id_usuario, id_propriedade=int(id_propriedade), modulo=MODULO_EXCLUSAO,
        descricao=f'Reidentificação — animal {antigo} excluído antes da Notificação'[:120],
    )
    registrar_item(db, id_op, 'tb_6006_reidentificacao_com_baixa_itens', linha.id, 'DELETE',
                   {'sisbov_antigo': antigo, 'sisbov_novo': novo}, None)
    return True, f'Animal {antigo} excluído. O brinco perdido voltou ao rebanho e o brinco novo voltou ao estoque.'

# =========================================================
# FIM DE ARQUIVO: backend\utils\reidentificacao_exclusao.py
# =========================================================
