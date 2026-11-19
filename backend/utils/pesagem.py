# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\pesagem.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-02 22:00 -03
# ATUALIZADO EM: 2026-10-09 19:35 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Utilitario COMPARTILHADO para gravar uma pesagem do animal na
#     tb_4003_pesos. registrar_pesagem() calcula sozinha a SEQUENCIA
#     (1, 2, 3... por SISBOV) e o GANHO de peso em relacao a pesagem
#     anterior. Nao da commit - quem chama decide (mesmo padrao do
#     log_operacoes.py). Peso vazio/zero = nao grava nada (devolve None).
#
#     Usada pela conferencia e pela integracao do Nascimento no brete
#     (Leitor e Bastao): o peso digitado vira a pesagem de sequencia 1
#     do animal, na Data de Brincagem (decisao de Benedito, Sessao 084).
#
#     v1.0.0: Criacao (Sessao 084, 02/10/2026, 22:00 -03).
#     v1.1.0: Sessao 092 (09/10/2026, 19:35 -03) - BLOCKCHAIN: toda pesagem
#         gravada aqui gera um evento PESAGEM na fila do blockchain (se o
#         Produtor tem provedor ligado). Como TODAS as pesagens passam por
#         esta funcao (brete do Leitor e do Bastao, Vincular GTA, Brincagem
#         Sequencial e qualquer pesagem manual futura), o gancho mora so
#         aqui. Parametro novo, opcional: id_operacao (os modulos com Log/
#         Desfazer passam o seu, para o Desfazer cancelar/estornar o evento).
#         A ficha leva o animal como esta agora + sequencia, ganho de peso,
#         origem e idade em dias da pesagem. O evento entra na mesma
#         transacao do modulo (antes do commit dele) e uma falha nele nunca
#         derruba a pesagem. Quem nao usa blockchain nao gasta nada.
#         Nenhuma outra mudanca - a pesagem em si (sequencia, ganho,
#         gravacao na tb_4003) e identica.
# =========================================================

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func

from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_4003_pesos import Peso
from backend.utils.blockchain import blockchain_ativo, registrar_evento_animal, TIPO_PESAGEM

ORIGEM_BRETE_NASCIMENTO = 'BRETE_NASCIMENTO'
ORIGEM_BRETE_COMPRA     = 'BRETE_COMPRA'
ORIGEM_MANUAL           = 'MANUAL'


def registrar_pesagem(db, id_propriedade, sisbov, rfid, data_pesagem, peso, eras_dias,
                      lote, origem, id_usuario, observacao=None, id_operacao=None):
    if peso is None or float(peso) <= 0:
        return None

    ultima = (
        db.query(Peso)
        .filter(Peso.sisbov == sisbov)
        .order_by(Peso.sequencia.desc())
        .first()
    )
    sequencia = (ultima.sequencia + 1) if ultima else 1
    ganho = None
    if ultima is not None:
        ganho = Decimal(str(peso)) - Decimal(str(ultima.peso))

    pesagem = Peso(
        id_propriedade=int(id_propriedade),
        sisbov=sisbov,
        rfid=rfid or None,
        sequencia=sequencia,
        data_pesagem=data_pesagem,
        hora_pesagem=datetime.now().time().replace(microsecond=0),
        peso=Decimal(str(peso)),
        ganho_peso=ganho,
        eras_dias=eras_dias,
        lote=lote or None,
        origem=origem,
        observacao=observacao,
        id_usuario=id_usuario,
    )
    db.add(pesagem)
    db.flush()

    # v1.1.0 - BLOCKCHAIN: evento PESAGEM (mesma transacao, antes do commit de quem chamou)
    if blockchain_ativo(db):
        animal = (
            db.query(Entrada)
            .filter(Entrada.id_propriedade == int(id_propriedade), Entrada.sisbov == sisbov)
            .first()
        )
        if animal is not None:
            registrar_evento_animal(
                db, animal, TIPO_PESAGEM, id_usuario=id_usuario, id_operacao=id_operacao,
                extras={
                    'pesagem_sequencia': sequencia,
                    'pesagem_ganho': ganho,
                    'pesagem_origem': origem,
                    'pesagem_eras_dias': eras_dias,
                },
            )
    return pesagem

# =========================================================
# FIM DE ARQUIVO: backend\utils\pesagem.py
# =========================================================
