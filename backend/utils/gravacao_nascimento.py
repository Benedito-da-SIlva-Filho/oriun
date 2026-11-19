# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils\
# MODULO: backend\utils\gravacao_nascimento.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-29 20:05 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.7.0
# v1.7.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Utilitario COMPARTILHADO do Nascimento/Desmame (Sessao 082,
#     Pacote 3). Nesta versao (Pacote 3A) cuida SO do NUMERO DE
#     CONTROLE (o NAS). A gravacao da cadeia inteira (7017, 3008,
#     2001, 2017, 7002, 3007, animais da Notificacao) entra aqui no
#     Pacote 3C, para escritorio e brete usarem a mesma funcao.
#
#     NUMERO DE CONTROLE = NAS + 7 digitos (regras de Benedito,
#     Sessao 082):
#       - E uma linha da tb_4001_gta: serie 'NAS', tipo_movimento
#         'NASCTO-DESMAME', sentido 'ENTRADA', meio_transporte 'NAO
#         SE APLICA', datas = Data de Brincagem. Numeracao POR
#         PRODUTOR (cada schema tem a sua) - maior NAS + 1.
#       - BRETE (Leitor/Bastao, Tipo = Nascimento): o NAS e
#         RESERVADO no 1o animal lido na Propriedade + Data de
#         Brincagem. Os seguintes da mesma data entram nele, mesmo
#         lidos em outro dia. Enquanto aberto, o Controle fica com
#         status_brincagem = 'PENDENTE' (as telas de Compra - GTA,
#         Sequencial, Vincular - so olham tipo COMPRA, entao nunca o
#         enxergam). A quantidade (qtde_animais) acompanha as
#         leituras pendentes.
#       - O Controle FECHA quando a Notificacao for gerada no
#         escritorio (Pacote 3C) - status 'BRINCADO'. Depois disso,
#         leitura nova na MESMA data abre OUTRO NAS (nao se sabe se
#         a Notificacao ja foi enviada a Certificadora).
#       - Os animais do Controle aberto sao as leituras da
#         tb_5001_brincagem com tipo_entrada NASCIMENTO, sts False,
#         mesma Propriedade e mesma Data de Brincagem (a Data e o
#         Tipo ficam travados no Alterar da Consulta Brincagem).
#       - CONTROLE ZERADO (todas as leituras excluidas): se for o
#         ULTIMO NAS do Produtor, o numero e LIBERADO (linha
#         apagada); se nao for, fica registrado com 0 animais (sem
#         buraco na numeracao). Os dois casos vao para o Log de
#         Operacoes como HISTORICO (nunca desfazivel) - para
#         ninguem dizer que "a plataforma gerou Notificacao
#         zerada".
#       - A reserva do numero tambem vai para o Log (historico).
#
#     TRAVA: a mesma trava de 2 partes do escritorio
#     (brincagem_nascimento.py - TRAVA_NUMERO_NAS 81001 +
#     id_produtor), para brete e escritorio nunca pegarem o mesmo
#     numero ao mesmo tempo.
#
#     FUNCOES:
#       travar_numeracao_nas(db, id_produtor)
#       proximo_numero_nas(db, id_propriedade) -> (inteiro, '0000015', 'NAS0000015')
#       buscar_controle_aberto(db, id_propriedade, data_brincagem)
#       reservar_controle(db, id_propriedade, id_produtor, uf,
#                         data_brincagem, id_usuario)
#       contar_leituras_do_controle(db, controle)
#       atualizar_qtde_controle(db, controle)
#       existe_nas_maior(db, controle)
#       tratar_controle_apos_exclusao(db, id_propriedade,
#                         data_brincagem, id_usuario, sisbov)
#
#     Nenhuma funcao da commit - quem chama decide (mesmo padrao
#     do log_operacoes.py).
#
#   v1.0.0: Criacao (Sessao 082, Pacote 3A).
#   v1.1.0: Sessao 084 (02/10/2026, 11:30 -03) - INTEGRACAO DO BRINCO LIDO
#           NO BRETE A UMA NOTIFICACAO JA LANCADA PELO ESCRITORIO (decisao
#           de Benedito: animal que nasceu na MESMA Data de Brincagem mas
#           nao foi avisado ao escritorio entra direto na Notificacao, sem
#           retrabalho e sem abrir outro NAS). NOVAS funcoes:
#             buscar_notificacao_para_integracao(db, id_propriedade,
#                       data_brincagem) - NAS lancado (com animais) da
#                       Propriedade + Data que AINDA NAO foi impresso;
#             integrar_animal_na_notificacao(db, gta, ...) - grava a
#                       MESMA cadeia do escritorio para 1 animal (tb_7017,
#                       tb_3008, tb_2001 ja conferido, tb_2017, tb_7002,
#                       tb_4001_gta_animais, qtde da Notificacao e saldo
#                       tb_3007), tudo na transacao de quem chama, e
#                       registra no Log como HISTORICO ('nascimento_
#                       integracao', nunca desfazivel). Notificacao ja
#                       IMPRESSA nunca recebe animal (volta ao fluxo do
#                       Controle novo).
#           Funcoes da v1.0.0 SEM mudanca.
#   v1.1.1: Sessao 084 (02/10/2026, 21:00 -03) - RFID lido no Bastao passa a
#           ser gravado TAMBEM na tb_7017 (decisao de Benedito), quando o
#           brinco do estoque ainda esta sem RFID. integrar_animal_na_
#           notificacao(): nova linha no bloco do tb_7017. Nenhuma outra
#           mudanca.
#   v1.2.0: Sessao 084 (02/10/2026, 22:00 -03) - PESO do animal integrado no
#           brete vira a pesagem de SEQUENCIA 1 na tb_4003_pesos (decisao de
#           Benedito: o peso so e validado no brete). integrar_animal_na_
#           notificacao() ganha o parametro opcional peso (backend/utils/
#           pesagem.py). Peso vazio = nao grava. Nenhuma outra mudanca.
#   v1.3.0: Sessao 084 (02/10/2026, 23:30 -03) - GERAR NOTIFICACAO DO BRETE
#           (o brete pode brincar ANTES de o escritorio lancar - regra de
#           Benedito): NOVA funcao gerar_notificacao_do_brete() fecha um
#           Controle (NAS) PENDENTE - transforma as leituras do brete (tb_5001
#           sts False da Propriedade + Data) em animais da Notificacao, com a
#           MESMA cadeia de integrar_animal_na_notificacao() (tb_7017, tb_3008,
#           tb_2001 ja conferido, tb_2017, tb_7002, tb_4001_gta_animais, saldo
#           tb_3007 e peso na tb_4003), marca as leituras como fechadas (sts
#           True + id_gta) e o Controle como BRINCADO. Tudo na transacao de
#           quem chama; um unico registro de Log (historico, nao desfazivel).
#           integrar_animal_na_notificacao() ganha o parametro opcional
#           id_operacao (reaproveita o Log do lote).
#     v1.4.0: Sessao 094 (12/10/2026, 19:30 -03) - NAS POR PROPRIEDADE (decisao de Benedito):
#         a numeracao da Notificacao de Nascimento (NAS) passa a ser da PROPRIEDADE (dentro do
#         schema do Produtor), nao mais do Produtor inteiro: a primeira NAS de cada fazenda e a
#         NAS0000001. proximo_numero_nas(db, id_propriedade) e existe_nas_maior() olham so as NAS da propriedade.
#         REVERSAO: devolver .bak_antes_nas_propriedade.
#     v1.5.0: Sessao 094 (12/10/2026, 20:40 -03) - AUDITORIA DO NASCIMENTO: (1) integrar_animal_na_notificacao() nao recusa mais brinco livre com reserva (velha ou nao)
#             da Sequencial - o brete prevalece; antes a Notificacao do brete podia travar. (2) manejo_do_brinco():
#             estoque -> regra do modelo (antes: 6 ultimos, errado no 105). REVERSAO: devolver .bak_antes_auditoria_nasc.
#     v1.6.0: Sessao 101 (20/10/2026, 10:10 -03) - tb_2017 passa a ser copia fiel da tb_2001: a linha de Entrada grava tambem lote, data_brincagem, conferido_brete, conferido_em, id_origem e id_gta_entrada (model tb_2017 v1.2.0). Nenhuma outra mudanca. REVERSAO: devolver .bak_antes_2017_copia_s101.
# =========================================================

from datetime import datetime, timedelta

from sqlalchemy import func, text

from backend.models import Produtor, Propriedade
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_3008_brincos_saida import BrincoSaida
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4001_gta_animais import GtaAnimal
from backend.models.tb_4002_especie import Especie
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.models.tb_5001_brincagem import Brincagem
from backend.models.tb_7002_pia import Pia
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.models.tb_7020_notificacao_impressao import NotificacaoImpressao
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.pesagem import registrar_pesagem, ORIGEM_BRETE_NASCIMENTO
from backend.utils.regras_sisbov import TIPO_ENTRADA_NASCIMENTO, eh_cota_hilton, DIAS_POR_MES, manejo_do_sisbov


# -------------------------------------------------------
# Constantes (MESMOS valores de brincagem_nascimento.py v1.2.0 -
# o escritorio passa a importar daqui no Pacote 3D).
# -------------------------------------------------------
TIPO_MOVIMENTO_NASCIMENTO = 'NASCTO-DESMAME'
SERIE_NOTIFICACAO         = 'NAS'
DIGITOS_NOTIFICACAO       = 7
MEIO_TRANSPORTE           = 'NAO SE APLICA'
TRAVA_NUMERO_NAS          = 81001        # + id_produtor

STATUS_CONTROLE_ABERTO    = 'PENDENTE'   # brete lendo, Notificacao nao gerada
STATUS_CONTROLE_FECHADO   = 'BRINCADO'   # Notificacao gerada

# Modulo do Log de Operacoes para Reserva/Zerado/Liberacao do
# Controle - HISTORICO, nunca desfazivel (log_operacoes.py v1.4.0,
# MODULOS_SO_HISTORICO).
MODULO_LOG_CONTROLE       = 'nascimento_controle'

# v1.1.0 - integracao de animal do brete numa Notificacao do escritorio
# (HISTORICO, nunca desfazivel - log_operacoes.py v1.6.0).
MODULO_LOG_INTEGRACAO     = 'nascimento_integracao'
TRAVA_BRINCOS_NASC        = 81002        # + id_propriedade (mesma do escritorio)
DIAS_LIBERACAO_ABATE      = 90           # mesma regra do escritorio
TAMANHO_MANEJO            = 6


# -------------------------------------------------------
# Funcao: trava a numeracao NAS do Produtor ate o fim da
# transacao (forma de 2 partes do Postgres - nunca colide com as
# travas de 1 parte da PIA e do Comunicado).
# -------------------------------------------------------
# -------------------------------------------------------
# v1.5.0 - Manejo do brinco: o do ESTOQUE (tb_7017); sem ele, a regra do modelo
# (antigo 105: os 6 ANTES do DV; novo: os 6 ultimos). Numero fora do formato
# cai nos 6 ultimos digitos (comportamento antigo).
# -------------------------------------------------------
def manejo_do_brinco(brinco, sisbov=None):
    if brinco is not None and getattr(brinco, 'manejo', None):
        return brinco.manejo
    numero = sisbov or (getattr(brinco, 'sisbov', None) or '')
    try:
        return manejo_do_sisbov(numero)
    except ValueError:
        return numero[-TAMANHO_MANEJO:] or None


def travar_numeracao_nas(db, id_produtor):
    db.execute(
        text('SELECT pg_advisory_xact_lock(:ns, :id)'),
        {'ns': TRAVA_NUMERO_NAS, 'id': int(id_produtor)},
    )


# -------------------------------------------------------
# Funcao: proximo NAS do Produtor (maior + 1). Chamar SEMPRE
# depois de travar_numeracao_nas(). Mesma conta do escritorio.
# -------------------------------------------------------
def proximo_numero_nas(db, id_propriedade):
    maior_atual = (
        db.query(func.max(Gta.numero_gta_sequencial))
        .filter(
            Gta.id_propriedade == int(id_propriedade),   # v1.4.0 - fila da PROPRIEDADE
            Gta.tipo_movimento == TIPO_MOVIMENTO_NASCIMENTO,
            Gta.serie_gta == SERIE_NOTIFICACAO,
        )
        .scalar()
    )
    proximo = int(maior_atual) + 1 if maior_atual and str(maior_atual).isdecimal() else 1
    numero_sequencial = str(proximo).zfill(DIGITOS_NOTIFICACAO)
    return proximo, numero_sequencial, f'{SERIE_NOTIFICACAO}{numero_sequencial}'


# -------------------------------------------------------
# Funcao: Controle ABERTO (reservado, Notificacao ainda nao
# gerada) desta Propriedade nesta Data de Brincagem. None se nao
# existir.
# -------------------------------------------------------
def buscar_controle_aberto(db, id_propriedade, data_brincagem):
    return (
        db.query(Gta)
        .filter(
            Gta.id_propriedade == int(id_propriedade),
            Gta.tipo_movimento == TIPO_MOVIMENTO_NASCIMENTO,
            Gta.serie_gta == SERIE_NOTIFICACAO,
            Gta.status_brincagem == STATUS_CONTROLE_ABERTO,
            Gta.data_emissao == data_brincagem,
        )
        .order_by(Gta.id.asc())
        .first()
    )


# -------------------------------------------------------
# Funcao: devolve o Controle aberto da Propriedade + Data; se nao
# existir, RESERVA um NAS novo (linha na tb_4001_gta, qtde 0) e
# registra a reserva no Log (historico). Trava a numeracao antes
# de procurar, para duas leituras simultaneas nunca abrirem 2
# Controles para a mesma data.
# Devolve (controle, reservado_agora).
# -------------------------------------------------------
def reservar_controle(db, id_propriedade, id_produtor, uf, data_brincagem, id_usuario):
    travar_numeracao_nas(db, id_produtor)

    controle = buscar_controle_aberto(db, id_propriedade, data_brincagem)
    if controle:
        return controle, False

    _, numero_sequencial, numero_completo = proximo_numero_nas(db, id_propriedade)

    controle = Gta(
        id_propriedade=int(id_propriedade),
        uf_gta=uf,
        serie_gta=SERIE_NOTIFICACAO,
        numero_gta_sequencial=numero_sequencial,
        numero_gta_completo=numero_completo,
        qtde_animais=0,
        tipo_movimento=TIPO_MOVIMENTO_NASCIMENTO,
        sentido='ENTRADA',
        data_emissao=data_brincagem,
        data_validade=data_brincagem,
        data_entrega=data_brincagem,
        meio_transporte=MEIO_TRANSPORTE,
        status_brincagem=STATUS_CONTROLE_ABERTO,
    )
    db.add(controle)
    db.flush()

    id_operacao = registrar_operacao(
        db,
        id_usuario=id_usuario,
        id_propriedade=int(id_propriedade),
        modulo=MODULO_LOG_CONTROLE,
        descricao=(
            f'Reserva do Número de Controle {numero_completo} — '
            f'Brincagem de Nascimento de {data_brincagem.strftime("%d/%m/%Y")} (1º animal lido)'
        ),
    )
    registrar_item(
        db, id_operacao, tabela='tb_4001_gta', id_registro=controle.id,
        tipo_mudanca='INSERT', dados_antes=None,
        dados_depois={'numero_gta_completo': numero_completo, 'status_brincagem': STATUS_CONTROLE_ABERTO},
    )

    return controle, True


# -------------------------------------------------------
# Funcao: quantas leituras pendentes pertencem ao Controle aberto
# (Nascimento, sts False, mesma Propriedade e mesma Data).
# -------------------------------------------------------
def contar_leituras_do_controle(db, controle):
    return (
        db.query(Brincagem)
        .filter(
            Brincagem.id_propriedade == controle.id_propriedade,
            Brincagem.tipo_entrada == TIPO_ENTRADA_NASCIMENTO,
            Brincagem.sts == False,  # noqa: E712
            Brincagem.data_brincagem == controle.data_emissao,
        )
        .count()
    )


# -------------------------------------------------------
# Funcao: qtde_animais do Controle = leituras pendentes dele.
# Chamar DEPOIS do flush() da leitura nova. Sem Log (e so o
# contador acompanhando as leituras).
# -------------------------------------------------------
def atualizar_qtde_controle(db, controle):
    controle.qtde_animais = contar_leituras_do_controle(db, controle)
    db.flush()
    return controle.qtde_animais


# -------------------------------------------------------
# Funcao: existe algum NAS MAIOR que o deste Controle? (se nao
# existir, este e o ULTIMO numero do Produtor).
# -------------------------------------------------------
def existe_nas_maior(db, controle):
    return (
        db.query(Gta.id)
        .filter(
            Gta.id_propriedade == controle.id_propriedade,   # v1.4.0 - so a fila da PROPRIEDADE
            Gta.tipo_movimento == TIPO_MOVIMENTO_NASCIMENTO,
            Gta.serie_gta == SERIE_NOTIFICACAO,
            Gta.numero_gta_sequencial > controle.numero_gta_sequencial,
        )
        .first()
    ) is not None


# -------------------------------------------------------
# Funcao: chamada pela Consulta Brincagem DEPOIS de excluir uma
# leitura de Nascimento (e do flush da exclusao). Acerta o
# Controle aberto daquela Propriedade + Data:
#   - ainda tem leituras -> so atualiza a quantidade;
#   - zerou e e o ULTIMO NAS -> libera o numero (apaga a linha);
#   - zerou e NAO e o ultimo -> fica registrado com 0 animais.
# Os 2 casos de zerado vao para o Log (historico). Devolve um
# texto curto para a tela (None quando so atualizou).
# id_produtor: para a trava da numeracao (o "ultimo" nao pode
# mudar no meio da conta).
# -------------------------------------------------------
def tratar_controle_apos_exclusao(db, id_propriedade, id_produtor, data_brincagem, id_usuario, sisbov):
    if data_brincagem is None:
        return None

    travar_numeracao_nas(db, id_produtor)

    controle = buscar_controle_aberto(db, id_propriedade, data_brincagem)
    if not controle:
        return None

    qtde_antes = controle.qtde_animais
    restantes = contar_leituras_do_controle(db, controle)
    if restantes > 0:
        controle.qtde_animais = restantes
        db.flush()
        return None

    numero = controle.numero_gta_completo
    data_br = data_brincagem.strftime('%d/%m/%Y')

    if not existe_nas_maior(db, controle):
        id_operacao = registrar_operacao(
            db,
            id_usuario=id_usuario,
            id_propriedade=int(id_propriedade),
            modulo=MODULO_LOG_CONTROLE,
            descricao=(
                f'Número de Controle {numero} LIBERADO — todos os animais da Brincagem de '
                f'Nascimento de {data_br} foram excluídos (último excluído: SISBOV {sisbov})'
            ),
        )
        registrar_item(
            db, id_operacao, tabela='tb_4001_gta', id_registro=controle.id,
            tipo_mudanca='DELETE',
            dados_antes={
                'numero_gta_completo': numero,
                'data_emissao': str(controle.data_emissao),
                'qtde_animais': str(qtde_antes),
                'status_brincagem': controle.status_brincagem,
            },
            dados_depois=None,
        )
        db.delete(controle)
        db.flush()
        return f'Número de Controle {numero} liberado (ficou sem animais).'

    id_operacao = registrar_operacao(
        db,
        id_usuario=id_usuario,
        id_propriedade=int(id_propriedade),
        modulo=MODULO_LOG_CONTROLE,
        descricao=(
            f'Número de Controle {numero} ZERADO pelo usuário — todos os animais da Brincagem de '
            f'Nascimento de {data_br} foram excluídos (último excluído: SISBOV {sisbov}). '
            f'O número fica registrado com 0 animais para não deixar buraco na numeração.'
        ),
    )
    registrar_item(
        db, id_operacao, tabela='tb_4001_gta', id_registro=controle.id,
        tipo_mudanca='UPDATE',
        dados_antes={'qtde_animais': qtde_antes},
        dados_depois={'qtde_animais': 0},
    )
    controle.qtde_animais = 0
    db.flush()
    return f'Número de Controle {numero} ficou com 0 animais (registrado no Log).'


# -------------------------------------------------------
# Funcao (v1.1.0): Notificacao NAS lancada pelo escritorio (com
# animais) na Propriedade + Data de Brincagem que AINDA NAO foi
# impressa. E nela que o brinco lido no brete entra. None se nao
# existir (ou se ja foi impressa).
# -------------------------------------------------------
def buscar_notificacao_para_integracao(db, id_propriedade, data_brincagem):
    candidatas = (
        db.query(Gta)
        .filter(
            Gta.id_propriedade == int(id_propriedade),
            Gta.tipo_movimento == TIPO_MOVIMENTO_NASCIMENTO,
            Gta.serie_gta == SERIE_NOTIFICACAO,
            Gta.status_brincagem == STATUS_CONTROLE_FECHADO,
            Gta.data_emissao == data_brincagem,
        )
        .order_by(Gta.id.desc())
        .all()
    )
    for gta in candidatas:
        tem_animais = db.query(Entrada.id).filter(Entrada.id_gta_entrada == gta.id).first() is not None
        impressa = db.query(NotificacaoImpressao.id).filter_by(id_gta=gta.id).first() is not None
        if tem_animais and not impressa:
            return gta
    return None


# -------------------------------------------------------
# Funcao (v1.1.0): grava 1 animal lido no brete DENTRO de uma
# Notificacao ja lancada - a MESMA cadeia do escritorio
# (brincagem_nascimento.py), ja com o animal CONFERIDO. Nao da
# commit. Levanta ValueError(mensagem) se algo impedir (quem chama
# faz rollback e mostra a mensagem). rfid: so o Bastao informa.
# Devolve {'controle', 'total', 'conferidos', 'faltam'}.
# -------------------------------------------------------
def integrar_animal_na_notificacao(db, gta, id_produtor, id_usuario, sisbov, rfid,
                                   id_especie, id_raca, sexo, nascimento, lote, peso=None,
                                   id_operacao=None):
    # Import tardio (evita ciclo: o router da Sequencial importa utils).
    from backend.routers.brincagem_sequencial import _decrementar_saldo_lotes

    id_propriedade = int(gta.id_propriedade)
    data_brincagem = gta.data_emissao
    numero = gta.numero_gta_completo

    if sexo not in ('MACHO', 'FEMEA'):
        raise ValueError('Sexo incorreto.')
    if nascimento is None or nascimento > data_brincagem:
        raise ValueError('Data de Nascimento depois da Data de Brincagem — confira as datas.')

    especie = db.get(Especie, int(id_especie))
    raca = db.get(Raca, int(id_raca))
    if not especie or not raca:
        raise ValueError('Espécie ou Raça não encontrada no catálogo.')

    eras_dias = (data_brincagem - nascimento).days
    faixa = next(
        (f for f in db.query(IdadeMeses).all() if f.dias_min <= eras_dias <= f.dias_max), None
    )
    if not faixa:
        raise ValueError('A idade do animal não se encaixa em nenhuma faixa de idade.')

    # ---- brinco do estoque (mesma trava do escritorio) ----
    db.execute(text('SELECT pg_advisory_xact_lock(:ns, :id)'),
               {'ns': TRAVA_BRINCOS_NASC, 'id': id_propriedade})
    brinco = (
        db.query(EntradaBrincoRfid)
        .filter(
            EntradaBrincoRfid.id_propriedade == id_propriedade,
            EntradaBrincoRfid.sisbov == sisbov,
            EntradaBrincoRfid.saida_data.is_(None),
            EntradaBrincoRfid.saida_gta.is_(None),
            EntradaBrincoRfid.saida_origem.is_(None),
            EntradaBrincoRfid.numero_comunicado.is_(None),
            # v1.5.0 - reserva da Sequencial NAO bloqueia (o brete prevalece, igual ao
            # Vincular GTA): a reserva nao e limpa quando expira, e um brinco livre com
            # reserva velha travava a geracao da Notificacao do brete. A Sequencial
            # reconfere os brincos no Salvar.
        )
        .first()
    )
    if not brinco:
        raise ValueError('Brinco já utilizado ou fora do estoque desta Propriedade.')

    manejo = manejo_do_brinco(brinco, sisbov)   # v1.5.0
    rfid_final = rfid or brinco.rfid
    cota_hilton = eh_cota_hilton(eras_dias)
    liberacao_abate = data_brincagem + timedelta(days=DIAS_LIBERACAO_ABATE)
    agora = datetime.now()

    propriedade = db.get(Propriedade, id_propriedade)
    produtor = db.get(Produtor, int(id_produtor))
    cpf_produtor = produtor.cpf_cnpj if produtor else None

    # ---- Log (HISTORICO): operacao + itens (v1.3.0: reaproveita a do lote) ----
    if id_operacao is None:
        id_operacao = registrar_operacao(
            db,
            id_usuario=id_usuario,
            id_propriedade=id_propriedade,
            modulo=MODULO_LOG_INTEGRACAO,
            descricao=f'Brinco {sisbov} lido no brete e integrado à Notificação {numero} (Brincagem de {data_brincagem.strftime("%d/%m/%Y")})',
        )

    # ---- tb_7017 (UPDATE) ----
    brinco.status = 'ENTRADA'
    brinco.raca = raca.codigo
    brinco.sexo = sexo
    brinco.data_brincagem = data_brincagem
    brinco.nascimento = nascimento
    brinco.eras_dias = eras_dias
    brinco.saida_data = data_brincagem
    brinco.saida_gta = numero
    brinco.reservado_id_gta = None
    brinco.reservado_ate = None
    if rfid and not brinco.rfid:
        brinco.rfid = rfid      # v1.1.1 - RFID lido no Bastao tambem na tb_7017
    db.flush()
    registrar_item(db, id_operacao, tabela='tb_7017_entrada_brincos_rfid', id_registro=brinco.id,
                   tipo_mudanca='UPDATE', dados_antes=None,
                   dados_depois={'status': 'ENTRADA', 'saida_gta': numero})

    # ---- tb_3008 (CREATE) ----
    brinco_saida = BrincoSaida(
        id_propriedade=id_propriedade,
        id_lote_entrada=brinco.id_lote_entrada,
        sisbov=sisbov,
        rfid=rfid_final,
        data_saida=data_brincagem,
        gta=numero,
        origem=TIPO_MOVIMENTO_NASCIMENTO,
    )
    db.add(brinco_saida)
    db.flush()
    registrar_item(db, id_operacao, tabela='tb_3008_brincos_saida', id_registro=brinco_saida.id,
                   tipo_mudanca='INSERT', dados_antes=None, dados_depois={'sisbov': sisbov})

    # ---- tb_2001 (CREATE) - ja CONFERIDO no brete ----
    entrada = Entrada(
        sisbov=sisbov,
        manejo=manejo,
        rfid=rfid_final,
        id_especie=especie.id,
        sexo=sexo,
        nascimento=nascimento,
        eras_dias=eras_dias,
        id_raca=raca.id,
        id_aptidao=None,
        cota_hilton=cota_hilton,
        data_brincagem=data_brincagem,
        liberacao_abate=liberacao_abate,
        tipo_entrada=TIPO_MOVIMENTO_NASCIMENTO,
        brincos='INTERNO',
        conferido_brete=True,
        conferido_em=agora,
        id_gta_entrada=gta.id,
        data_inclusao=data_brincagem,
        lote=(lote or None),
        id_origem=None,
        id_propriedade=id_propriedade,
    )
    db.add(entrada)
    db.flush()
    registrar_item(db, id_operacao, tabela='tb_2001', id_registro=entrada.id,
                   tipo_mudanca='INSERT', dados_antes=None, dados_depois={'sisbov': sisbov})

    # ---- v1.2.0 - peso do brete = pesagem de sequencia 1 (tb_4003) ----
    registrar_pesagem(db, id_propriedade, sisbov, rfid_final, data_brincagem, peso, eras_dias,
                      lote, ORIGEM_BRETE_NASCIMENTO, id_usuario)

    # ---- total da Notificacao (animais ja gravados + este) ----
    total = db.query(Entrada).filter(Entrada.id_gta_entrada == gta.id).count()

    # ---- tb_2017 (CREATE) ----
    movimentacao = Movimentacao(
        # v1.6.0 (Sessao 101) - copia fiel da tb_2001: campos novos da tb_2017
        lote=entrada.lote, data_brincagem=entrada.data_brincagem,
        conferido_brete=entrada.conferido_brete, conferido_em=entrada.conferido_em,
        id_origem=entrada.id_origem, id_gta_entrada=entrada.id_gta_entrada,
        id_animal=entrada.id,
        id_propriedade=id_propriedade,
        sisbov=sisbov,
        manejo=manejo,
        rfid=rfid_final,
        negociacao=TIPO_MOVIMENTO_NASCIMENTO,
        brincos='INTERNO',
        id_especie=especie.id,
        sexo=sexo,
        nascimento=nascimento,
        dias=eras_dias,
        cota_hilton=cota_hilton,
        id_aptidao=None,
        id_raca=raca.id,
        tipo_entrada=TIPO_MOVIMENTO_NASCIMENTO,
        gta_entrada=numero,
        gta_entrada_emissao=data_brincagem,
        gta_entrada_validade=data_brincagem,
        gta_entrada_animais=total,
        data_inclusao=data_brincagem,
        entrada=data_brincagem,
        origem_propriedade=propriedade.nome if propriedade else None,
        origem_cpf_cnpj=cpf_produtor,
        destino_propriedade=propriedade.nome if propriedade else None,
        destino_cpf_cnpj=cpf_produtor,
        data_movimentacao=data_brincagem,
    )
    db.add(movimentacao)
    db.flush()
    registrar_item(db, id_operacao, tabela='tb_2017_movimentacoes', id_registro=movimentacao.id,
                   tipo_mudanca='INSERT', dados_antes=None, dados_depois={'sisbov': sisbov})
    # os animais ja gravados desta Notificacao passam a mostrar o total novo
    (
        db.query(Movimentacao)
        .filter(Movimentacao.gta_entrada == numero, Movimentacao.id_propriedade == id_propriedade)
        .update({Movimentacao.gta_entrada_animais: total}, synchronize_session=False)
    )

    # ---- tb_7002 PIA (CREATE) - numero da PIA = numero da Notificacao ----
    pia = Pia(
        id_propriedade=id_propriedade,
        numero_pia=int(gta.numero_gta_sequencial),
        id_gta=gta.id,
        sisbov=sisbov,
        manejo=manejo,
        nascimento=nascimento,
        idade_meses=round(eras_dias / DIAS_POR_MES),
        sexo=sexo,
        raca_codigo=raca.codigo,
        motivo='NASCIMENTO',
        data_identificacao=data_brincagem,
    )
    db.add(pia)
    db.flush()
    registrar_item(db, id_operacao, tabela='tb_7002_pia', id_registro=pia.id,
                   tipo_mudanca='INSERT', dados_antes=None,
                   dados_depois={'numero_pia': pia.numero_pia, 'sisbov': sisbov})

    # ---- tb_4001_gta_animais: soma 1 na categoria (ou cria) ----
    linha_gta = (
        db.query(GtaAnimal)
        .filter(GtaAnimal.id_gta == gta.id, GtaAnimal.sexo == sexo, GtaAnimal.idade_meses == faixa.descricao)
        .first()
    )
    if linha_gta:
        linha_gta.quantidade = (linha_gta.quantidade or 0) + 1
    else:
        linha_gta = GtaAnimal(id_gta=gta.id, especie=especie.codigo, sexo=sexo,
                              idade_meses=faixa.descricao, quantidade=1)
        db.add(linha_gta)
    db.flush()

    # ---- qtde da Notificacao (no Log: marca que recebeu animal do brete) ----
    qtde_antes = gta.qtde_animais
    gta.qtde_animais = total
    db.flush()
    registrar_item(db, id_operacao, tabela='tb_4001_gta', id_registro=gta.id,
                   tipo_mudanca='UPDATE', dados_antes={'qtde_animais': qtde_antes},
                   dados_depois={'qtde_animais': total})

    # ---- tb_3007: saldo e qtde_saida do lote (funcao da Sequencial) ----
    _decrementar_saldo_lotes(db, id_operacao, [brinco])

    conferidos = db.query(Entrada).filter(
        Entrada.id_gta_entrada == gta.id, Entrada.conferido_brete.is_(True)).count()
    return {
        'controle': numero,
        'total': total,
        'conferidos': conferidos,
        'faltam': total - conferidos,
    }


# -------------------------------------------------------
# Funcao (v1.3.0): GERA a Notificacao de um Controle (NAS) PENDENTE -
# o brete leu primeiro. Cada leitura pendente (tb_5001, Nascimento,
# sts False, mesma Propriedade + Data) vira animal da Notificacao pela
# mesma cadeia da integracao. Nao da commit. Levanta ValueError(msg)
# (quem chama faz rollback). Devolve (numero, qtde).
# -------------------------------------------------------
def gerar_notificacao_do_brete(db, controle, id_produtor, id_usuario):
    if controle.status_brincagem != STATUS_CONTROLE_ABERTO:
        raise ValueError('Este Controle não está aberto para gerar a Notificação.')

    leituras = (
        db.query(Brincagem)
        .filter(
            Brincagem.id_propriedade == controle.id_propriedade,
            Brincagem.tipo_entrada == TIPO_ENTRADA_NASCIMENTO,
            Brincagem.sts == False,  # noqa: E712
            Brincagem.data_brincagem == controle.data_emissao,
        )
        .order_by(Brincagem.sisbov)
        .all()
    )
    if not leituras:
        raise ValueError('Este Controle não tem animais lidos no brete.')

    numero = controle.numero_gta_completo
    id_operacao = registrar_operacao(
        db,
        id_usuario=id_usuario,
        id_propriedade=int(controle.id_propriedade),
        modulo=MODULO_LOG_INTEGRACAO,
        descricao=f'Notificação {numero} gerada a partir de {len(leituras)} animal(is) lidos no brete '
                  f'(Brincagem de {controle.data_emissao.strftime("%d/%m/%Y")})',
    )

    for leitura in leituras:
        try:
            integrar_animal_na_notificacao(
                db, controle, id_produtor, id_usuario, leitura.sisbov, leitura.rfid,
                leitura.id_especie, leitura.id_raca, leitura.sexo, leitura.nascimento,
                leitura.lote, peso=leitura.peso, id_operacao=id_operacao,
            )
        except ValueError as erro:
            raise ValueError(f'Brinco {leitura.sisbov}: {erro}')
        leitura.id_gta = controle.id
        leitura.sts = True
        if not leitura.manejo:
            leitura.manejo = manejo_do_brinco(None, leitura.sisbov)   # v1.5.0 - regra do modelo

    controle.status_brincagem = STATUS_CONTROLE_FECHADO
    db.flush()
    registrar_item(
        db, id_operacao, tabela='tb_4001_gta', id_registro=controle.id, tipo_mudanca='UPDATE',
        dados_antes={'status_brincagem': STATUS_CONTROLE_ABERTO},
        dados_depois={'status_brincagem': STATUS_CONTROLE_FECHADO},
    )
    return numero, len(leituras)

# =========================================================
# FIM DE ARQUIVO: backend\utils\gravacao_nascimento.py
# =========================================================
