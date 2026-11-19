# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\conferencia_compra.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-05 16:00 -03
# ATUALIZADO EM: 2026-11-16 10:55 -03
# VERSAO: 1.4.0
# v1.4.0: Sessao 128 (2026-11-16 10:55 -03) - AUDITORIA ETAPA 7c (Regra #73): ler_peso_brete() recusa peso que nao e numero finito (a palavra 'nan' passava nas travas de minimo e maximo e gravava peso invalido). Vale para todos os usos (Pesos, Linkagem, Brincagem, Conferencia de Compra). REVERSAO: .bak_antes_etapa7c.
#
# DESCRICAO:
#     Utilitario COMPARTILHADO pelo Brincagem com Leitor e pelo
#     Brincagem com Bastao (brincagem_leitor.py / brincagem_bastao.py)
#     para a CONFERENCIA NO BRETE de uma GTA de COMPRA lancada pelo
#     escritorio na Brincagem Sequencial (decisao de Benedito, Sessao
#     087). Mesmo desenho do Nascimento lancado pelo escritorio (NAS):
#       - a Sequencial grava os animais na tb_2001 com
#         conferido_brete = FALSE (brincagem_sequencial.py v1.16.0);
#       - o peao escolhe a GTA na Tela 02 e le os brincos dela; cada
#         brinco lido ganha o check (conferido_brete = TRUE + hora);
#       - a GTA ENCERRA SOZINHA ao ler o ultimo brinco (Faltam = 0) -
#         nao existe coluna de "encerrada": o estado e calculado
#         (conferidos = total) e a GTA some da lista de em aberto;
#       - brinco que nao e da GTA escolhida e barrado;
#       - o PESO do brete e obrigatorio e vira a proxima pesagem do
#         animal na tb_4003_pesos (a 1a e a media do Peso Balancao,
#         se a Sequencial a gravou; sem ela, esta e a 1a) - a
#         sequencia e calculada por pesagem.registrar_pesagem().
#
#     A leitura LIVRE (GTAs sem brincos vinculados: o brinco lido e
#     que define a GTA, depois o Vincular GTA) NAO usa este modulo.
#
#     Nenhuma funcao daqui da commit - quem chama decide (mesmo padrao
#     de pesagem.py e log_operacoes.py).
#
#     v1.0.0: Criacao (Sessao 087, 05/10/2026, 16:00 -03).
#     v1.1.0: Sessao 087 (05/10/2026, 17:29 -03) - LOTE LIBERADO NA CONFERENCIA
#             (pedido de Benedito, teste do Pacote 087): a Sequencial nao grava
#             lote (so o brete sabe onde vai colocar os animais) e o campo ficava
#             travado. Agora o brete digita/troca o Lote ao conferir o brinco:
#             ler_lote_brete() valida (maximo 30 caracteres, maiuscula) e
#             conferir_brinco() grava o lote na tb_2001 ANTES da pesagem (a
#             pesagem da tb_4003 leva o lote novo). Nenhuma outra mudanca.
#     v1.2.0: Sessao 087 (05/10/2026, 17:46 -03) - DUAS REGRAS DE BENEDITO: (1) o
#             PESO do brete tem de ser SUPERIOR a 100 kg (PESO_MINIMO_KG; vale para
#             todo o brete: Compra, Nascimento e leitura livre); (2) na conferencia
#             da GTA de Compra o LOTE passa a ser OBRIGATORIO
#             (ler_lote_brete(obrigatorio=True)). Nenhuma outra mudanca.
#     v1.3.0: Sessao 087 (2026-10-05 17:58 -03) - LOTE OBRIGATORIO EM TODO O BRETE (pedido de
#     v1.3.1: Sessao 113 (03/11/2026, 15:55 -03) - Mensagem de peso da Entrada simplificada: "Peso incorreto: Verifique".  REVERSAO: .bak_antes_s113_peso_entrada.
#             Benedito, mesmo desenho do peso): leitura livre, conferencia da GTA
#             de Compra e conferencia do Nascimento. Mensagem generica "Lote e
#             obrigatorio no brete". Nenhuma outra mudanca.
#     v1.3.2: Sessao 114 (04/11/2026, 10:37 -03) - Mensagens de peso da Entrada (texto invalido e acima do maximo) viram "Peso incorreto, verifique." (pedido de Benedito). Nenhuma outra mudanca.  REVERSAO: .bak_antes_s114_peso.
#     v1.3.3: Sessao 114 (04/11/2026, 10:41 -03) - Mensagem de peso da Entrada igual a das outras telas: "Peso incorreto, verifique." (pedido de Benedito).  REVERSAO: .bak_antes_s114_peso2.
# =========================================================

import math
from datetime import datetime

from sqlalchemy import func

from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_4001_gta import Gta
from backend.utils.pesagem import registrar_pesagem, ORIGEM_BRETE_COMPRA

TIPO_BANCO_COMPRA = 'COMPRA'
DIAS_POR_MES      = 30      # mesma aproximacao dos routers do brete
PESO_MAXIMO_KG    = 1000    # mesma trava do Leitor/Bastao
PESO_MINIMO_KG    = 100     # v1.2.0 - o peso do brete tem de ser SUPERIOR a este valor

LOTE_TAMANHO_MAXIMO        = 30     # tb_2001.lote e tb_4003_pesos.lote (v1.1.0)

MOTIVO_JA_CONFERIDO_COMPRA = 'Brinco ja conferido no brete'
MOTIVO_OUTRA_GTA           = 'Brinco de outra GTA'
MOTIVO_FORA_DA_GTA         = 'Brinco fora da GTA'


# -------------------------------------------------------
# Peso do brete: OBRIGATORIO (Benedito, Sessao 087 - o brete tem
# balanca). Devolve (peso_float, None) ou (None, mensagem_de_erro).
# Vale para todo o brete (Compra, Nascimento e leitura livre).
# -------------------------------------------------------
def ler_peso_brete(peso_str):
    texto = str(peso_str or '').strip()
    if not texto:
        return None, 'Peso é obrigatório no brete.'
    try:
        peso = float(texto.replace(',', '.'))
    except ValueError:
        return None, 'Peso incorreto, verifique.'
    if not math.isfinite(peso):   # v1.4.0 (Etapa 7c) - 'nan' e 'inf' nao sao peso
        return None, 'Peso incorreto, verifique.'
    if peso <= PESO_MINIMO_KG:   # v1.2.0
        return None, 'Peso incorreto, verifique.'
    if peso > PESO_MAXIMO_KG:
        return None, 'Peso incorreto, verifique.'
    return peso, None


# -------------------------------------------------------
# v1.1.0 - Lote digitado no brete na conferencia (campo livre, opcional).
# Devolve (lote_ou_None, None) ou (None, mensagem_de_erro). Vazio = sem lote
# (obrigatorio=True: vazio e erro - todo o brete, v1.3.0).
# -------------------------------------------------------
def ler_lote_brete(texto, obrigatorio=False):
    lote = str(texto or '').strip().upper()
    if obrigatorio and not lote:   # v1.2.0 - conferencia da GTA: lote obrigatorio
        return None, 'Lote é obrigatório no brete.'
    if len(lote) > LOTE_TAMANHO_MAXIMO:
        return None, f'Lote excede {LOTE_TAMANHO_MAXIMO} caracteres.'
    return (lote or None), None


def _data_br(data):
    return data.strftime('%d/%m/%Y') if data else ''


def contadores_gta(db, id_gta):
    """(total, conferidos) dos animais da GTA na tb_2001."""
    total = db.query(Entrada).filter(Entrada.id_gta_entrada == id_gta).count()
    conferidos = (
        db.query(Entrada)
        .filter(Entrada.id_gta_entrada == id_gta, Entrada.conferido_brete.is_(True))
        .count()
    )
    return total, conferidos


def numero_gta(db, id_gta):
    gta = db.get(Gta, int(id_gta))
    return gta.numero_gta_completo if gta else ''


# -------------------------------------------------------
# GTAs de Compra lancadas pelo escritorio com conferencia PENDENTE
# (Faltam > 0) - lista da Tela 02. GTA encerrada nao entra.
# Devolve dicts: id_gta, numero, data (date), total, conferidos, faltam.
# -------------------------------------------------------
def listar_gtas_abertas(db, id_propriedade):
    gtas = (
        db.query(Gta)
        .filter(
            Gta.id_propriedade == int(id_propriedade),
            Gta.tipo_movimento == TIPO_BANCO_COMPRA,
            Gta.sentido == 'ENTRADA',
            Gta.status_brincagem == 'BRINCADO',
        )
        .order_by(Gta.data_emissao.desc(), Gta.id.desc())
        .all()
    )
    abertas = []
    for gta in gtas:
        total, conferidos = contadores_gta(db, gta.id)
        if total == 0 or conferidos >= total:
            continue
        data = (
            db.query(func.min(Entrada.data_brincagem))
            .filter(Entrada.id_gta_entrada == gta.id)
            .scalar()
        )
        abertas.append({
            'id_gta': gta.id,
            'numero': gta.numero_gta_completo,
            'data': data,
            'total': total,
            'conferidos': conferidos,
            'faltam': total - conferidos,
        })
    return abertas


# -------------------------------------------------------
# Painel da Leitura: a GTA escolhida, com a lista dos brincos e o
# check de cada um. None = GTA inexistente, de outra Propriedade, de
# outro tipo ou sem animais.
# -------------------------------------------------------
def montar_lancamento(db, id_propriedade, id_gta):
    gta = db.get(Gta, int(id_gta))
    if (not gta or gta.id_propriedade != int(id_propriedade)
            or gta.tipo_movimento != TIPO_BANCO_COMPRA):
        return None
    animais = (
        db.query(Entrada)
        .filter(Entrada.id_gta_entrada == gta.id)
        .order_by(Entrada.sisbov)
        .all()
    )
    if not animais:
        return None
    brincos = [{
        'sisbov': a.sisbov,
        'sexo': a.sexo,
        'meses': int(round(a.eras_dias / DIAS_POR_MES)) if a.eras_dias is not None else None,
        'lote': a.lote or '',
        'conferido': bool(a.conferido_brete),
        'hora': a.conferido_em.strftime('%H:%M') if (a.conferido_brete and a.conferido_em) else '',
    } for a in animais]
    conferidos = sum(1 for b in brincos if b['conferido'])
    return {
        'id_gta': gta.id,
        'numero': gta.numero_gta_completo,
        'data': animais[0].data_brincagem,
        'total': len(brincos),
        'conferidos': conferidos,
        'brincos': brincos,
    }


# -------------------------------------------------------
# Acha o animal lancado (tb_2001, Compra, com GTA) pelo SISBOV ou pelo
# RFID, em QUALQUER GTA da Propriedade - quem chama confere se e da GTA
# escolhida (bloqueio_brinco). para_update trava a linha (conferir).
# -------------------------------------------------------
def buscar_brinco(db, id_propriedade, sisbov=None, rfid=None, para_update=False):
    consulta = db.query(Entrada).filter(
        Entrada.id_propriedade == int(id_propriedade),
        Entrada.tipo_entrada == TIPO_BANCO_COMPRA,
        Entrada.id_gta_entrada.isnot(None),
    )
    if sisbov:
        consulta = consulta.filter(Entrada.sisbov == sisbov)
    if rfid:
        consulta = consulta.filter(Entrada.rfid == rfid)
    if para_update:
        consulta = consulta.with_for_update()
    return consulta.first()


# -------------------------------------------------------
# O brinco lido pode ser conferido NESTA GTA agora?
# None = pode; senao (motivo, mensagem).
# -------------------------------------------------------
def bloqueio_brinco(db, lancado, id_gta, sisbov):
    numero_esta = numero_gta(db, id_gta)
    if lancado is None:
        return (MOTIVO_FORA_DA_GTA, f'Brinco {sisbov} não consta na GTA {numero_esta}.')
    if lancado.id_gta_entrada != int(id_gta):
        numero_outra = numero_gta(db, lancado.id_gta_entrada)
        return (
            MOTIVO_OUTRA_GTA,
            f'Brinco {sisbov} pertence à GTA {numero_outra}, e não à {numero_esta}.',
        )
    if lancado.conferido_brete:
        quando = ''
        if lancado.conferido_em:
            quando = ' em ' + lancado.conferido_em.strftime('%d/%m/%Y %H:%M')
        return (
            MOTIVO_JA_CONFERIDO_COMPRA,
            f'Brinco {sisbov} já conferido no brete{quando} ({numero_esta})',
        )
    return None


# -------------------------------------------------------
# Marca o animal como conferido e grava a pesagem do brete (proxima
# sequencia do SISBOV na tb_4003_pesos). Devolve (total, conferidos)
# da GTA - lidos ANTES do commit (regra da Sessao 078).
# -------------------------------------------------------
def conferir_brinco(db, lancado, peso, id_usuario, alterar_lote=False, lote=None):
    if alterar_lote:   # v1.1.0 - o brete decide o lote (a Sequencial nao grava)
        lancado.lote = lote
    lancado.conferido_brete = True
    lancado.conferido_em = datetime.now()
    db.flush()

    registrar_pesagem(
        db, lancado.id_propriedade, lancado.sisbov, lancado.rfid, lancado.data_brincagem,
        peso, lancado.eras_dias, lancado.lote, ORIGEM_BRETE_COMPRA, id_usuario,
    )
    return contadores_gta(db, lancado.id_gta_entrada)

# =========================================================
# FIM DE ARQUIVO: backend\utils\conferencia_compra.py
# =========================================================
