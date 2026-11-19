# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\blockchain.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-09 17:35 -03
# ATUALIZADO EM: 2026-11-11 14:30 -03
# VERSAO: 1.4.1
#
# DESCRICAO:
#     Utilitario GENERICO do BLOCKCHAIN no Orion (Sessao 092). Qualquer
#     modulo que grave um fato do animal chama registrar_evento() DENTRO da
#     mesma transacao, logo antes do db.commit() - se a operacao falhar, o
#     evento tambem nao existe. O envio para a rede NAO e feito aqui: o
#     evento vai para a fila (tb_blk_8002_eventos / tb_blk_8003_envios) e o
#     "carteiro" (carteiro_blockchain.py) envia em segundo plano.
#
#     REGRAS FECHADAS COM BENEDITO (Sessao 092):
#       - So gera evento se o Produtor tem pelo menos um provedor LIGADO
#         (tb_blk_8001 ativa + provedor ativo em tb_blk_8000). Sem provedor,
#         nada e gravado (zero peso para quem nao usa blockchain).
#       - O SISBOV nunca vai em claro: sisbov_hash = HMAC-SHA256 com a chave
#         da Consiste (.env: BLK_CHAVE_<versao>; versao atual em
#         BLK_VERSAO_CHAVE_ATUAL, padrao 1). A versao fica gravada em cada
#         evento: trocar de chave um dia nao quebra os codigos antigos.
#       - Todos os hashes (animal, dono, evento) tambem sao HMAC com a chave
#         - hash simples de ficha com SISBOV dentro poderia ser adivinhado.
#       - Cada evento guarda a COPIA CONGELADA da ficha (ficha_animal e
#         ficha_dono). Correcao = evento novo apontando para o anterior.
#       - DESFAZER (tratar_desfazer): envio ainda nao enviado (PENDENTE ou
#         ERRO) e CANCELADO; envio ja enviado ou confirmado gera um evento
#         de ESTORNO apontando para o original, so para os provedores que ja
#         receberam.
#       - Falha aqui NUNCA derruba a operacao do usuario: tudo roda dentro de
#         um SAVEPOINT, o erro vai para o log e a funcao devolve None.
#
#     v1.0.0: Criacao (Sessao 092, 09/10/2026, 17:35 -03).
#     v1.1.0: Sessao 092 (09/10/2026, 19:30 -03) - Brincagem/Entrada no
#         blockchain. (1) Tipos novos NASCIMENTO (animal nascido na fazenda:
#         rastreabilidade completa ate o abate) e PESAGEM (cada pesagem da
#         tb_4003_pesos). ENTRADA passa a ser usado pela compra. (2)
#         blockchain_ativo(db): o Produtor tem provedor ligado? (1 consulta
#         por sessao, guardada em db.info) - quem nao usa blockchain nao
#         gasta nada. (3) registrar_evento_animal(): atalho dos modulos -
#         confere blockchain_ativo, monta a ficha do animal (com 'extras') e
#         a do dono (guardada por sessao) e registra o evento, tudo dentro de
#         um SAVEPOINT (falha nunca derruba a operacao do usuario). Usado por
#         brincagem_sequencial, vincular_gta, brincagem_nascimento e, via
#         pesagem.py, por toda pesagem (Leitor, Bastao, Sequencial, Vincular).
#         Nenhuma mudanca no que ja existia (hashes, fichas, Desfazer).
#     v1.1.1: Sessao 117 (2026-11-06 18:05 -03) - Ficha do dono usa o Produtor LOGADO, nao o primeiro vinculo (defeito com 2+ Produtores). Nenhuma outra mudanca. REVERSAO: .bak_antes_s117_produtor.
#     v1.2.0: Sessao 117 (2026-11-06 20:10 -03) - registrar_evento_animal() aceita ocorrido_em (data do evento: Data da Morte, Data de Saida); sem ele, continua agora. REVERSAO: .bak_antes_s117_blockchain_morte.
#     v1.3.0: Sessao 117 (2026-11-06 20:50 -03) - SAIDAS: tipo POSSE; blockchain_ativo() guarda a resposta por schema (Venda entra no schema do comprador); ficha do dono aceita id_produtor (Entrada no destino). REVERSAO: .bak_antes_s117_saidas.
#     v1.4.0: Sessao 121 (2026-11-11 14:00 -03) - Nova constante TIPO_REIDENTIFICACAO (modulo Reidentificacao). Nenhuma outra mudanca. REVERSAO: .bak_antes_s121_reidentificacao.
#     v1.4.1: Sessao 121 (2026-11-11 14:30 -03) - tratar_desfazer() ganha o parametro opcional sisbovs=[...]: cancela/estorna so os eventos desses SISBOVs (Excluir 1 animal do pedido de Reidentificacao). Sem ele, comportamento igual ao anterior. REVERSAO: .bak_antes_s121_exclusao.
# =========================================================

import hashlib
import hmac
import json
import logging
import os
from datetime import date, datetime
from decimal import Decimal

from backend.models import Propriedade, PropriedadeProdutor, Produtor, Raca
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_blk_8000_provedores import ProvedorBlk
from backend.models.tb_blk_8001_produtor_provedores import ProdutorProvedorBlk
from backend.models.tb_blk_8002_eventos import EventoBlk
from backend.models.tb_blk_8003_envios import EnvioBlk

logger = logging.getLogger('orion.blockchain')

# Tipos de evento (lista fixa - acrescentar aqui quando um modulo novo entrar;
# nenhuma tabela precisa mudar).
TIPO_BRINCAGEM     = 'BRINCAGEM'
TIPO_ENTRADA       = 'ENTRADA'          # compra (animal chegou na propriedade)
TIPO_NASCIMENTO    = 'NASCIMENTO'       # nasceu na fazenda (rastreabilidade completa)
TIPO_PESAGEM       = 'PESAGEM'          # cada linha da tb_4003_pesos
TIPO_TROCA_RFID    = 'TROCA_RFID'
TIPO_TRANSFERENCIA = 'TRANSFERENCIA'
TIPO_VENDA         = 'VENDA'
TIPO_POSSE         = 'POSSE'            # v1.3.0 - Alteracao de Posse (mesma Propriedade, muda o Produtor)
TIPO_ABATE         = 'ABATE'
TIPO_MORTE         = 'MORTE'
TIPO_ESTORNO       = 'ESTORNO'
TIPO_REIDENTIFICACAO = 'REIDENTIFICACAO'   # v1.4.0 - Reidentificacao: evento de SAIDA do SISBOV perdido e de ENTRADA do SISBOV novo
TIPOS_EVENTO = (TIPO_BRINCAGEM, TIPO_ENTRADA, TIPO_NASCIMENTO, TIPO_PESAGEM, TIPO_TROCA_RFID,
                TIPO_TRANSFERENCIA, TIPO_VENDA, TIPO_POSSE, TIPO_ABATE, TIPO_MORTE, TIPO_ESTORNO)

STATUS_NAO_SAIU = ('PENDENTE', 'ERRO')            # ainda nao saiu: pode cancelar
STATUS_JA_SAIU  = ('ENVIANDO', 'CONFIRMADO')      # ja saiu (ou esta saindo): so estorno


class ChaveAusente(Exception):
    """A chave BLK_CHAVE_<versao> nao esta no .env."""


# -------------------------------------------------------
# Chave e hashes
# -------------------------------------------------------
def versao_chave_atual():
    try:
        return int(os.getenv('BLK_VERSAO_CHAVE_ATUAL', '1'))
    except ValueError:
        return 1


def _chave(versao):
    valor = os.getenv(f'BLK_CHAVE_{versao}')
    if not valor:
        raise ChaveAusente(f'BLK_CHAVE_{versao} nao encontrada no .env.')
    return valor.encode('utf-8')


def _hmac(versao, texto):
    return hmac.new(_chave(versao), texto.encode('utf-8'), hashlib.sha256).hexdigest()


def _serializar(valor):
    if isinstance(valor, Decimal):
        return format(valor.normalize(), 'f')
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    raise TypeError(f'Tipo nao serializavel: {type(valor)}')


def json_canonico(dado):
    """Texto JSON sempre igual para o mesmo dado (chaves ordenadas, sem espacos)."""
    return json.dumps(dado, sort_keys=True, ensure_ascii=False, separators=(',', ':'), default=_serializar)


def hash_sisbov(sisbov, versao=None):
    versao = versao or versao_chave_atual()
    return _hmac(versao, 'sisbov:' + str(sisbov))


def codigo_fazenda(id_propriedade, versao=None):
    """Codigo anonimo da fazenda (identidade preservada): nunca o nome."""
    versao = versao or versao_chave_atual()
    return _hmac(versao, f'fazenda:{id_propriedade}')[:16]


def hash_ficha(ficha, versao):
    return _hmac(versao, json_canonico(ficha))


def _hash_do_evento(versao, tipo_evento, sisbov_hash, ocorrido_em, hash_animal, hash_dono, id_anterior):
    corpo = {
        'tipo': tipo_evento, 'sisbov': sisbov_hash, 'ocorrido_em': ocorrido_em,
        'animal': hash_animal, 'dono': hash_dono, 'versao': versao, 'anterior': id_anterior,
    }
    return _hmac(versao, json_canonico(corpo))


# -------------------------------------------------------
# Fichas (copia congelada)
# -------------------------------------------------------
def ficha_do_animal(db, entrada, extras=None):
    """Ficha do animal (tb_2001) como esta AGORA. 'extras' acrescenta campos
    do evento (ex.: rfid_anterior)."""
    raca = db.get(Raca, entrada.id_raca) if entrada.id_raca else None
    gta = db.get(Gta, entrada.id_gta_entrada) if entrada.id_gta_entrada else None
    ultimo_peso = (
        db.query(Peso)
        .filter(Peso.id_propriedade == entrada.id_propriedade, Peso.sisbov == entrada.sisbov)
        .order_by(Peso.sequencia.desc())
        .first()
    )
    ficha = {
        'sisbov': entrada.sisbov,
        'manejo': entrada.manejo,
        'rfid': entrada.rfid,
        'sexo': str(entrada.sexo) if entrada.sexo is not None else None,
        'nascimento': entrada.nascimento,
        'raca': getattr(raca, 'codigo', None),
        'tipo_entrada': str(entrada.tipo_entrada) if entrada.tipo_entrada is not None else None,
        'data_inclusao': entrada.data_inclusao,
        'data_brincagem': entrada.data_brincagem,
        'liberacao_abate': entrada.liberacao_abate,
        'lote': entrada.lote,
        'gta_entrada': getattr(gta, 'numero_gta_completo', None),
        'numero_comunicado': entrada.numero_comunicado,
        'peso': ultimo_peso.peso if ultimo_peso is not None else None,
        'data_peso': ultimo_peso.data_pesagem if ultimo_peso is not None else None,
    }
    if extras:
        ficha.update(extras)
    return ficha


def ficha_do_dono(db, id_propriedade, id_produtor=None):
    """Ficha do dono (propriedade + produtor). So sai se o provedor liberar."""
    propriedade = db.get(Propriedade, id_propriedade)
    if propriedade is None:
        return None
    # v1.1.1: Produtor LOGADO (se ha login); sem login (rotina de fundo) cai no primeiro vinculo, como antes.
    from flask import session, has_request_context
    id_logado = id_produtor or (session.get('id_produtor') if has_request_context() else None)   # v1.3.0: id_produtor explicito (Entrada no destino)
    consulta = db.query(PropriedadeProdutor).filter_by(id_propriedade=propriedade.id, data_fim=None)
    vinculo = (consulta.filter_by(id_produtor=int(id_logado)).first() if id_logado else None) or consulta.first()
    produtor = db.get(Produtor, vinculo.id_produtor) if vinculo else None
    return {
        'propriedade': propriedade.nome,
        'codigo_mapa': propriedade.codigo_mapa,
        'municipio': propriedade.municipio,
        'uf': propriedade.uf,
        'produtor': produtor.nome if produtor else None,
        'documento': produtor.cpf_cnpj if produtor else None,
    }


# -------------------------------------------------------
# Provedores ligados para o Produtor da sessao
# -------------------------------------------------------
def _provedores_ligados(db):
    return (
        db.query(ProdutorProvedorBlk, ProvedorBlk)
        .join(ProvedorBlk, ProvedorBlk.id == ProdutorProvedorBlk.id_provedor)
        .filter(ProdutorProvedorBlk.ativo.is_(True), ProvedorBlk.ativo.is_(True))
        .order_by(ProvedorBlk.id)
        .all()
    )


# -------------------------------------------------------
# registrar_evento() - coloca o evento na fila (mesma transacao do modulo).
# Devolve o id do evento, ou None (sem provedor ligado, ou falha - logada).
# -------------------------------------------------------
def registrar_evento(db, id_propriedade, tipo_evento, sisbov, ficha_animal,
                     ficha_dono=None, id_usuario=None, id_operacao=None,
                     id_evento_anterior=None, ocorrido_em=None,
                     sisbov_hash=None, so_provedores=None):
    try:
        with db.begin_nested():
            ligados = _provedores_ligados(db)
            if so_provedores is not None:
                ligados = [(lig, prov) for lig, prov in ligados if prov.id in so_provedores]
            if not ligados:
                return None

            versao = versao_chave_atual()
            ficha_animal = dict(ficha_animal)
            ficha_animal['codigo_fazenda'] = codigo_fazenda(id_propriedade, versao)
            ocorrido = (ocorrido_em or datetime.now()).replace(microsecond=0)

            hash_sisbov_ev = sisbov_hash or hash_sisbov(sisbov, versao)
            hash_animal = hash_ficha(ficha_animal, versao)
            hash_dono = hash_ficha(ficha_dono, versao) if ficha_dono else None
            hash_evento = _hash_do_evento(versao, tipo_evento, hash_sisbov_ev, ocorrido.isoformat(),
                                          hash_animal, hash_dono, id_evento_anterior)

            evento = EventoBlk(
                id_propriedade=id_propriedade, tipo_evento=tipo_evento,
                sisbov_hash=hash_sisbov_ev, versao_chave=versao,
                ficha_animal=json.loads(json_canonico(ficha_animal)),
                ficha_dono=json.loads(json_canonico(ficha_dono)) if ficha_dono else None,
                hash_animal=hash_animal, hash_dono=hash_dono, hash_evento=hash_evento,
                id_evento_anterior=id_evento_anterior, id_operacao=id_operacao,
                id_usuario=id_usuario, ocorrido_em=ocorrido,
            )
            db.add(evento)
            db.flush()
            for lig, prov in ligados:
                db.add(EnvioBlk(id_evento=evento.id, id_provedor=prov.id, ambiente=lig.ambiente, status='PENDENTE'))
            db.flush()
            return evento.id
    except Exception:
        logger.exception('Blockchain: nao foi possivel registrar o evento %s (a operacao segue normalmente).', tipo_evento)
        return None


# -------------------------------------------------------
# blockchain_ativo() - o Produtor da sessao tem provedor ligado? Uma consulta
# por sessao (guardada em db.info). Os modulos chamam ANTES de montar ficha:
# quem nao usa blockchain nao gasta nada.
# -------------------------------------------------------
def blockchain_ativo(db):
    try:
        # v1.3.0: a resposta e guardada POR schema (search_path): na Venda a mesma sessao entra no schema do comprador.
        from sqlalchemy import text
        chave = 'blk_ativo:' + str(db.execute(text('SHOW search_path')).scalar())
        if chave not in db.info:
            with db.begin_nested():
                db.info[chave] = bool(_provedores_ligados(db))
        return db.info[chave]
    except Exception:
        logger.exception('Blockchain: nao foi possivel checar os provedores ligados.')
        return False


def _ficha_do_dono_da_sessao(db, id_propriedade, id_produtor=None):
    chave = f'blk_dono_{id_propriedade}_{id_produtor}'
    if chave not in db.info:
        db.info[chave] = ficha_do_dono(db, id_propriedade, id_produtor)
    return db.info[chave]


# -------------------------------------------------------
# registrar_evento_animal() - atalho dos modulos de Brincagem/Entrada/Pesagem:
# monta a ficha do animal (tb_2001 como esta AGORA, + 'extras') e a do dono e
# coloca o evento na fila. Deve ser chamada antes do db.commit() do modulo, com
# o animal ja gravado (db.flush()). Tudo dentro de um SAVEPOINT: se qualquer
# coisa falhar, o erro vai para o log e a operacao do usuario segue normalmente.
# Devolve o id do evento, ou None (sem provedor ligado, ou falha).
# -------------------------------------------------------
def registrar_evento_animal(db, entrada, tipo_evento, id_usuario=None, id_operacao=None, extras=None, ocorrido_em=None, id_produtor_dono=None):
    if not blockchain_ativo(db):
        return None
    try:
        with db.begin_nested():
            ficha = ficha_do_animal(db, entrada, extras=extras)
            dono = _ficha_do_dono_da_sessao(db, entrada.id_propriedade, id_produtor_dono)
            # v1.2.0: data do evento opcional (ex.: Data da Morte, Data de Saida). Aceita date ou datetime.
            if ocorrido_em is not None and not isinstance(ocorrido_em, datetime):
                ocorrido_em = datetime.combine(ocorrido_em, datetime.min.time())
            return registrar_evento(
                db, entrada.id_propriedade, tipo_evento, entrada.sisbov, ficha,
                ficha_dono=dono, id_usuario=id_usuario, id_operacao=id_operacao, ocorrido_em=ocorrido_em,
            )
    except Exception:
        logger.exception('Blockchain: nao foi possivel registrar o evento %s do animal %s (a operacao segue).',
                         tipo_evento, getattr(entrada, 'sisbov', None))
        return None


# -------------------------------------------------------
# tratar_desfazer() - chamada pelo Desfazer (operacoes_recentes) ANTES de
# reverter a operacao. Para cada evento daquela operacao: o que ainda nao
# saiu e CANCELADO; o que ja saiu gera um evento de ESTORNO.
# -------------------------------------------------------
def tratar_desfazer(db, id_operacao, id_usuario=None, sisbovs=None):
    try:
        with db.begin_nested():
            eventos = (
                db.query(EventoBlk)
                .filter(EventoBlk.id_operacao == id_operacao, EventoBlk.tipo_evento != TIPO_ESTORNO)
                .all()
            )
            if sisbovs:   # v1.4.1 - so os eventos destes SISBOVs
                eventos = [e for e in eventos if any(e.sisbov_hash == hash_sisbov(x, e.versao_chave) for x in sisbovs)]
            for evento in eventos:
                envios = db.query(EnvioBlk).filter(EnvioBlk.id_evento == evento.id).all()
                for envio in envios:
                    if envio.status in STATUS_NAO_SAIU:
                        envio.status = 'CANCELADO'
                        envio.erro = 'Cancelado: a operacao foi desfeita antes do envio.'
                provedores_enviados = [e.id_provedor for e in envios if e.status in STATUS_JA_SAIU]
                if provedores_enviados:
                    registrar_evento(
                        db, evento.id_propriedade, TIPO_ESTORNO, None,
                        {'estorno_de_evento': evento.id, 'tipo_original': evento.tipo_evento,
                         'hash_evento_original': evento.hash_evento, 'motivo': 'DESFAZER_OPERACAO'},
                        id_usuario=id_usuario, id_operacao=id_operacao,
                        id_evento_anterior=evento.id, sisbov_hash=evento.sisbov_hash,
                        so_provedores=provedores_enviados,
                    )
    except Exception:
        logger.exception('Blockchain: nao foi possivel tratar o Desfazer da operacao %s (o Desfazer segue).', id_operacao)


# -------------------------------------------------------
# verificar_evento() - recalcula os hashes a partir da copia congelada e
# compara com os gravados. True = nada foi alterado.
# -------------------------------------------------------
def verificar_evento(db, id_evento):
    evento = db.get(EventoBlk, id_evento)
    if evento is None:
        return False
    versao = evento.versao_chave
    if hash_ficha(evento.ficha_animal, versao) != evento.hash_animal:
        return False
    if evento.ficha_dono and hash_ficha(evento.ficha_dono, versao) != evento.hash_dono:
        return False
    esperado = _hash_do_evento(versao, evento.tipo_evento, evento.sisbov_hash,
                               evento.ocorrido_em.isoformat(), evento.hash_animal,
                               evento.hash_dono, evento.id_evento_anterior)
    return esperado == evento.hash_evento

# =========================================================
# FIM DE ARQUIVO: backend\utils\blockchain.py
# =========================================================
