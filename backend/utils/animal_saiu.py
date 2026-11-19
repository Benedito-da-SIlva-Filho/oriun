# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\animal_saiu.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-23 18:10 -03
# ATUALIZADO EM: 2026-11-11 11:40 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     MENSAGEM UNICA "ANIMAL JA SAIU" (decisao do Benedito, Sessao 105): quando a busca por Manejo, SISBOV ou RFID nao
#     acha o animal em estoque (tb_2001) na Propriedade em uso, o usuario precisa saber ONDE ele esta - nao so
#     "nao encontrado". Foco so na Propriedade em uso: outra fazenda do mesmo Produtor nao entra.
#
#     Funcao:
#         saida_do_animal(db, id_propriedade, sisbov=None, manejo=None, rfid=None) -> SaidaAnimal mais recente (tb_2002)
#                                                                                      da Propriedade, ou None
#         texto_animal_saiu(saida) -> 'Animal já saiu da Propriedade: ABATE em 19/10/2026.'
#         mensagem_animal_saiu(db, id_propriedade, sisbov=None, manejo=None, rfid=None) -> texto ou None
#
#     Manejo repetido (mais de um animal diferente ja saiu com o mesmo Manejo): mostra o mais recente e avisa quantos.
#
#     v1.0.0: Sessao 105 (23/10/2026, 18:10 -03) - Criacao.
#     v1.1.0: Sessao 121 (11/11/2026, 14:00 -03) - tipo de saida REIDENTI ('REIDENTIFICADO') na mensagem. REVERSAO: .bak_antes_s121_reidentificacao.
# =========================================================

from backend.models.tb_2002_saida_animais import SaidaAnimal

ROTULO_TIPO_SAIDA = {
    'ABATE': 'ABATE',
    'VENDA': 'VENDA',
    'MORTE': 'MORTE',
    'TRANSFER': 'TRANSFERÊNCIA',
    'TRANSFERENCIA': 'TRANSFERÊNCIA',
    'REIDENTI': 'REIDENTIFICADO',   # v1.1.0 - brinco perdido, animal ganhou outro SISBOV
}


def _data_br(data):
    return data.strftime('%d/%m/%Y') if data else ''


def saida_do_animal(db, id_propriedade, sisbov=None, manejo=None, rfid=None):
    """Saida mais recente (tb_2002) da Propriedade para o brinco informado; None se nao houver."""
    q = db.query(SaidaAnimal).filter(SaidaAnimal.id_propriedade == int(id_propriedade))
    if sisbov:
        q = q.filter(SaidaAnimal.sisbov == sisbov)
    elif manejo:
        q = q.filter(SaidaAnimal.manejo == manejo)
    elif rfid:
        q = q.filter(SaidaAnimal.rfid == rfid)
    else:
        return None
    return q.order_by(SaidaAnimal.data_saida.desc(), SaidaAnimal.id.desc()).first()


def texto_animal_saiu(saida):
    tipo = ROTULO_TIPO_SAIDA.get(str(saida.tipo_saida or '').upper(), str(saida.tipo_saida or '').upper())
    return f'Animal já saiu da Propriedade: {tipo} em {_data_br(saida.data_saida)}.'


def mensagem_animal_saiu(db, id_propriedade, sisbov=None, manejo=None, rfid=None):
    """Texto 'Animal ja saiu da Propriedade: TIPO em dd/mm/aaaa.' ou None quando nunca saiu desta Propriedade."""
    saida = saida_do_animal(db, id_propriedade, sisbov=sisbov, manejo=manejo, rfid=rfid)
    if saida is None:
        return None
    texto = texto_animal_saiu(saida)
    if manejo and not sisbov:
        quantos = (
            db.query(SaidaAnimal.sisbov)
            .filter(SaidaAnimal.id_propriedade == int(id_propriedade), SaidaAnimal.manejo == manejo)
            .distinct().count()
        )
        if quantos > 1:
            texto += f' (há {quantos} animais que já saíram com este Manejo; este é o mais recente.)'
    return texto

# =========================================================
# FIM DE ARQUIVO: backend\utils\animal_saiu.py
# =========================================================
