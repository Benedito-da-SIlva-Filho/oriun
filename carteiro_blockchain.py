# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion
# MODULO: carteiro_blockchain.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-09 17:35 -03
# ATUALIZADO EM: 2026-10-10 18:20 -03
# VERSAO: 1.0.1
#
# DESCRICAO:
#     O "CARTEIRO" do blockchain (Sessao 092): script SEPARADO que fica
#     rodando ao lado do Orion. A cada poucos segundos ele percorre os
#     Produtores ativos, pega os envios PENDENTES (ou com ERRO ja na hora de
#     tentar de novo) da fila tb_blk_8003_envios, chama o conector do
#     provedor e marca CONFIRMADO ou ERRO. Uma falha de rede nunca derruba o
#     Orion - quem fica esperando e a fila.
#
#     COMO RODAR (na pasta C:\orion, outro terminal, com o mesmo ambiente do
#     Orion):
#         python carteiro_blockchain.py             - roda sem parar
#         python carteiro_blockchain.py --uma-vez   - uma volta e sai (teste)
#
#     REGRAS:
#       - O envio e "reservado" (status ENVIANDO) antes de sair, com
#         FOR UPDATE SKIP LOCKED: dois carteiros nunca pegam o mesmo envio.
#       - ENVIANDO parado ha mais de 10 minutos (carteiro caiu no meio)
#         volta para PENDENTE.
#       - Erro: tenta de novo com espera crescente (2, 4, 8... ate 60 min);
#         depois de 10 tentativas fica em ERRO e para (olhar na tela).
#       - Provedor sem conector registrado (backend/blockchain/registro.py)
#         fica PENDENTE, sem gastar tentativa, e o aviso sai no log.
#       - Somente conectores com aceita_ficha=True recebem a ficha completa;
#         os demais recebem so os hashes.
#
#     v1.0.0: Criacao (Sessao 092, 09/10/2026, 17:35 -03).
#     v1.0.1: Sessao 093 (10/10/2026, 18:20 -03) - Ctrl+C nao mostra mais o
#             erro feio (Traceback): sai com uma mensagem de "encerrado".
#             Se parar no meio de um envio, ele fica ENVIANDO e volta para
#             PENDENTE sozinho depois de 10 minutos (nada se perde).
# =========================================================

import logging
import sys
import time
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Produtor
from backend.models.tb_blk_8000_provedores import ProvedorBlk
from backend.models.tb_blk_8001_produtor_provedores import ProdutorProvedorBlk
from backend.models.tb_blk_8002_eventos import EventoBlk
from backend.models.tb_blk_8003_envios import EnvioBlk
from backend.blockchain.base import ErroEnvio
from backend.blockchain.registro import CONECTORES
from backend.utils.multitenant import get_db_produtor

logger = logging.getLogger('orion.carteiro')

INTERVALO_SEGUNDOS = 10
LOTE_POR_VOLTA     = 50
MAX_TENTATIVAS     = 10
MINUTOS_PRESO      = 10
ESPERA_SEM_CONECTOR_MIN = 5


def _espera_minutos(tentativas):
    return min(2 ** tentativas, 60)


def _montar_evento(db, envio, evento, ligacao, conector):
    dados = {
        'id_evento': evento.id,
        'tipo_evento': evento.tipo_evento,
        'sisbov_hash': evento.sisbov_hash,
        'versao_chave': evento.versao_chave,
        'hash_animal': evento.hash_animal,
        'hash_dono': evento.hash_dono,
        'hash_evento': evento.hash_evento,
        'ocorrido_em': evento.ocorrido_em.isoformat(),
        'id_evento_anterior': evento.id_evento_anterior,
    }
    if conector.aceita_ficha:
        dados['ficha_animal'] = evento.ficha_animal
        if ligacao is not None and ligacao.envia_dono and evento.ficha_dono:
            dados['ficha_dono'] = evento.ficha_dono
    return dados


def _processar_envio(db, id_envio):
    envio = db.get(EnvioBlk, id_envio)
    provedor = db.get(ProvedorBlk, envio.id_provedor)
    conector = CONECTORES.get(provedor.codigo)
    agora = datetime.now()

    if conector is None:
        envio.status = 'PENDENTE'
        envio.proximo_envio = agora + timedelta(minutes=ESPERA_SEM_CONECTOR_MIN)
        db.commit()
        logger.warning('Sem conector para o provedor %s (envio %s fica pendente).', provedor.codigo, id_envio)
        return False

    evento = db.get(EventoBlk, envio.id_evento)
    ligacao = db.query(ProdutorProvedorBlk).filter_by(id_provedor=envio.id_provedor).first()
    try:
        resultado = conector.enviar(_montar_evento(db, envio, evento, ligacao, conector), envio.ambiente)
    except ErroEnvio as erro:
        envio.tentativas += 1
        envio.erro = str(erro)[:2000]
        envio.status = 'ERRO'
        if erro.definitivo:
            envio.tentativas = MAX_TENTATIVAS
        envio.proximo_envio = agora + timedelta(minutes=_espera_minutos(envio.tentativas))
        db.commit()
        logger.warning('Envio %s (%s) falhou: %s', id_envio, provedor.codigo, erro)
        return False
    except Exception as erro:   # falha inesperada do conector
        envio.tentativas += 1
        envio.erro = f'Erro inesperado: {erro}'[:2000]
        envio.status = 'ERRO'
        envio.proximo_envio = agora + timedelta(minutes=_espera_minutos(envio.tentativas))
        db.commit()
        logger.exception('Envio %s (%s) falhou de forma inesperada.', id_envio, provedor.codigo)
        return False

    envio.status = 'CONFIRMADO'
    envio.codigo_retorno = resultado.codigo
    envio.url_verificacao = resultado.url_verificacao
    envio.erro = None
    envio.tentativas += 1
    envio.enviado_em = agora
    envio.confirmado_em = datetime.now()
    db.commit()
    logger.info('Envio %s (%s) confirmado: %s', id_envio, provedor.codigo, resultado.codigo)
    return True


def processar_produtor(id_produtor):
    """Uma volta num Produtor. Devolve quantos envios foram confirmados."""
    confirmados = 0
    with get_db_produtor(id_produtor) as db:
        # Preso em ENVIANDO (carteiro caiu no meio) -> volta para a fila
        db.execute(text(
            "UPDATE tb_blk_8003_envios SET status = 'PENDENTE', atualizado_em = now() "
            "WHERE status = 'ENVIANDO' AND atualizado_em < now() - make_interval(mins => :min)"
        ), {'min': MINUTOS_PRESO})

        reservados = (
            db.query(EnvioBlk)
            .filter(
                EnvioBlk.status.in_(('PENDENTE', 'ERRO')),
                EnvioBlk.proximo_envio <= datetime.now(),
                EnvioBlk.tentativas < MAX_TENTATIVAS,
            )
            .order_by(EnvioBlk.id)
            .limit(LOTE_POR_VOLTA)
            .with_for_update(skip_locked=True)
            .all()
        )
        ids = []
        for envio in reservados:
            envio.status = 'ENVIANDO'
            envio.enviado_em = datetime.now()
            ids.append(envio.id)
        db.commit()

        for id_envio in ids:
            if _processar_envio(db, id_envio):
                confirmados += 1
    return confirmados


def uma_volta():
    with Session(engine) as db:
        ids = [
            linha[0] for linha in
            db.query(Produtor.id)
            .filter(Produtor.ativo.is_(True), Produtor.schema_nome.isnot(None))
            .order_by(Produtor.id)
            .all()
        ]
    total = 0
    for id_produtor in ids:
        try:
            total += processar_produtor(id_produtor)
        except Exception:
            logger.exception('Carteiro: falha ao processar o Produtor %s (segue para o proximo).', id_produtor)
    return total


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    if '--uma-vez' in sys.argv:
        print(f'Envios confirmados nesta volta: {uma_volta()}')
        return
    logger.info('Carteiro do blockchain iniciado (volta a cada %s s). Ctrl+C para parar.', INTERVALO_SEGUNDOS)
    try:
        while True:
            try:
                uma_volta()
            except Exception:
                logger.exception('Carteiro: falha na volta (tenta de novo).')
            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        logger.info('Carteiro do blockchain encerrado (Ctrl+C). Pode fechar esta janela.')


if __name__ == '__main__':
    main()

# =========================================================
# FIM DE ARQUIVO: carteiro_blockchain.py
# =========================================================
