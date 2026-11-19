# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\home_resumo.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-04 14:10 -03
# ATUALIZADO EM: 2026-11-19 12:30 -03
# VERSAO: 1.13.1
# v1.13.1: Sessao 133 (2026-11-19 12:30 -03) - CARGA (serie CAR) excluida de forma EXPLICITA dos "Comunicados a gerar" (antes so ficava de fora pelo status NAO_APLICA). Sem mudanca de comportamento hoje. REVERSAO: .bak_antes_s133_carga.
# v1.13.0: Sessao 128 (2026-11-16 10:55 -03) - AUDITORIA ETAPA 7c (desempenho): a contagem de Notificacoes a imprimir busca no banco so as NAS ainda NAO impressas (antes lia todas as NAS do historico a cada abertura da Home). Mesmo resultado. REVERSAO: .bak_antes_etapa7c.
#
# DESCRICAO:
#     Numeros dos 3 cards do topo da Home do Produtor (produtor_home):
#
#       ANIMAIS  - animais em estoque (tb_2001), soma de TODAS as
#                  Propriedades do usuario (de todos os Produtores a
#                  que ele esta vinculado) + a lista por Propriedade.
#       ENTRADAS - card de ALERTA, 3 pendencias que ainda precisam de
#                  documento para a Certificadora (cada uma com seu
#                  atalho):
#                    * Comunicados a gerar: GTAs de entrada ja
#                      BRINCADAS e ainda sem numero de Comunicado,
#                      EXCETO Nascimento (mesmo criterio de
#                      comunicado_entrada.py::_montar_lotes_pendentes).
#                    * Comunicados a imprimir: Comunicados com
#                      status ABERTO (tb_2012) - cada numero conta 1.
#                    * Notificacoes a imprimir: NAS sem linha na
#                      tb_7020 e com animais (mesmo criterio de
#                      alerta_prazo_notificacao.py - o card e o alerta
#                      dos 30 dias nunca discordam).
#       LIBERADOS PARA ABATE - animais em estoque com liberacao_abate
#                  igual ou anterior a hoje, separados em CTH (Cota
#                  Hilton), Livres e Total.
#
#     montar_resumo_home(pares) -> dict. So leitura. Se a busca de UM
#     Produtor falhar, 'erro' vem True e a Home mostra "indisponivel"
#     em vez de numeros: nunca mostra "Tudo em dia" por engano (um
#     zero falso esconderia pendencia). Falha e registrada no log.
#
#     v1.0.0: Criacao do modulo (Sessao 085, 04/10/2026, 14:10 -03).
#     v1.1.0: Sessao 089 (07/10/2026, 10:45 -03) - NOVA funcao
#             montar_resumo_por_fazenda(pares): devolve os mesmos numeros
#             de montar_resumo_home() separados por FAZENDA (um item por par
#             Propriedade+Produtor), para a tabela do Home novo. Cada item
#             reaproveita montar_resumo_home([par]) - nenhuma conta nova,
#             entao os numeros nunca discordam do resumo do grupo. Se a
#             busca de uma fazenda falhar, so a linha dela fica "indisponivel".
#             montar_resumo_home() e o resto do arquivo: sem mudanca.
#     v1.2.0: Sessao 089 (07/10/2026, 12:30 -03) - AUDITORIA ERAS no Home novo:
#             NOVA funcao montar_auditoria_por_propriedade(ids): devolve, por
#             Propriedade, a situacao da auditoria (em dia, vencendo, pendente,
#             sem data) e se a ultima vistoria foi NAO CONFORME, usando as
#             regras de backend/utils/auditoria_eras.py (as mesmas das telas
#             de Auditorias ERAS). A auditoria e da Propriedade (schema
#             public), por isso a busca e por Propriedade, nao por Produtor.
#             montar_resumo_por_fazenda() passa a trazer o item 'auditoria' em
#             cada fazenda. Se a busca de uma Propriedade falhar, so ela vem
#             com erro=True (a tela mostra "indisponivel", nunca em branco por
#             engano). montar_resumo_home() e o restante: sem mudanca.
#     v1.3.0: Sessao 106 (26/10/2026, 10:40 -03) - "Comunicados a gerar" passa a seguir a MESMA regra do Gerar Comunicado
#             (comunicado_entrada.py v1.8.0): so conta a GTA BRINCADO, sem Comunicado, que tem animais E todos conferidos
#             no brete (tb_2001.conferido_brete = True). Antes o card contava tambem a GTA aguardando leitura no brete, e a
#             Home dizia "a gerar" enquanto o Gerar Comunicado nao tinha nada pronto. O card continua contando GTAs (como
#             antes). Nada mais mudou. REVERSAO: .bak_antes_s106c.
#     v1.4.0: Sessao 106 (26/10/2026, 11:25 -03) - NOVA pendencia "GTA de Compra - Brincar" (pedido do Benedito: a GTA de
#             Compra lancada deve avisar na Home que ha animais para brincar). Chave nova 'gtas_brincar' = GTAs de COMPRA com
#             status_brincagem PENDENTE e Data de Entrega preenchida na(s) Propriedade(s) - o MESMO filtro das listas da
#             Brincagem (brincagem_sequencial.py e vincular_gta.py), para a Home e a Brincagem nunca discordarem. Chave nova
#             'url_brincagem' = Hub de Brincagem (/produtor/hub-novo/brincagem). Nada mais mudou. REVERSAO: .bak_antes_s106e.
#     v1.5.0: Sessao 106 (26/10/2026, 12:05 -03) - o destino da pendencia "GTA de Compra - Brincar" passa a ser o Hub de
#             Entrada (/produtor/hub-novo/entrada), onde ficam a Brincagem Sequencial e o Vincular GTA/Brincagem (a GTA PENDENTE
#             nao aparece no Hub de Brincagem). Constante URL_BRINCAR_COMPRA; chave 'url_brincar_compra' (substitui 'url_brincagem').
#             REVERSAO: .bak_antes_s106i.
#     v1.6.0: Sessao 106 (26/10/2026, 14:20 -03) - decisao do Benedito: o destino de "GTA de Compra - Brincar" volta a ser o Hub de Brincagem
#             (/produtor/hub-novo/brincagem), porque a Brincagem com Leitor (brincagem_leitor.py v1.24.0) passou a listar a GTA PENDENTE.
#             Mesma constante URL_BRINCAR_COMPRA, so o endereco mudou. REVERSAO: .bak_antes_s106m.
#     v1.7.0: Sessao 106 (26/10/2026, 18:10 -03) - NOVA pendencia 'brincos_esquecidos': brincos de COMPRA lidos no brete ha 3+ dias (DIAS_BRINCO_ESQUECIDO) sem GTA,
#             sem reserva e sem Comunicado (brinco ja esta no animal e ninguem documentou). Destino URL_BRINCOS_ESQUECIDOS (Consulta de Brincagem, onde se vincula a GTA).
#             REVERSAO: .bak_antes_s106w.
#     v1.11.0: Sessao 121 (2026-11-11 14:40 -03) - Pendencia 'Reidentificacao - Notificacao a enviar' (animais em pedidos nao enviados + dias do mais antigo). REVERSAO: .bak_antes_s121_reidentificacao.
#     v1.9.0: Sessao 108 (29/10/2026, 19:35 -03) - Transferencia ENTRE PRODUTORES: a Entrada so conta na Home quando a Saida (que fica no schema da origem) ja foi impressa.  REVERSAO: .bak_antes_s108_entre_produtores
#     v1.8.0: Sessao 106 (26/10/2026, 18:20 -03) - pedido do Benedito: a pendencia diz o TIPO. Compra continua em 'brincos_esquecidos'; NOVA 'nascimentos_esquecidos' =
#             brincos de NASCIMENTO lidos ha 3+ dias, sem Notificacao gerada (sts aberto, sem id_gta). REVERSAO: .bak_antes_s106x.
#     v1.12.0: Sessao 121 (2026-11-11 19:00 -03) - Pendencia da Reidentificacao agora conta ANIMAIS pendentes de Notificacao (sem numero) + animais de Notificacao gerada e ainda nao enviada; prazo de 30 dias a partir da data do animal mais antigo (modelo pendentes). REVERSAO: .bak_antes_s121_pendentes.
# =========================================================

import logging
from datetime import date, timedelta

from sqlalchemy import exists, func, or_
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2012_com_entrada import ComunicadoEntrada
from backend.models.tb_2013_com_morte import ControleMorte   # s111 - pendencia das mortes sem Notificacao
from backend.models.tb_4001_gta import Gta
from backend.models.tb_6005_reidentificacao_com_baixa import ReidentificacaoComBaixa   # s121 - pendencia da Reidentificacao a enviar
from backend.models.tb_6006_reidentificacao_com_baixa_itens import ReidentificacaoComBaixaItem   # s121 v1.12.0
from backend.models.tb_5001_brincagem import Brincagem   # v1.7.0
from backend.models.tb_7020_notificacao_impressao import NotificacaoImpressao
from backend.utils.multitenant import get_db_produtor
from backend.utils.auditoria_eras import calcular_situacao, buscar_ultima_auditoria, tem_codigo_eras
from backend.utils.gravacao_nascimento import contar_leituras_do_controle, STATUS_CONTROLE_ABERTO
from backend.utils.conferencia_compra import contadores_gta   # v1.3.0 - (total, conferidos) dos animais da GTA

logger = logging.getLogger(__name__)

# -------------------------------------------------------
# Constantes (mesmos valores usados em comunicado_entrada.py e
# notificacao_nascimento.py)
# -------------------------------------------------------
TIPO_MOVIMENTO_NAS = 'NASCTO-DESMAME'
SERIE_NAS = 'NAS'
STATUS_GTA_BRINCADO = 'BRINCADO'
STATUS_GTA_PENDENTE = 'PENDENTE'     # v1.4.0 - GTA lancada, animais ainda por brincar
TIPO_MOVIMENTO_COMPRA = 'COMPRA'     # v1.4.0
STATUS_COMUNICADO_ABERTO = 'ABERTO'

# Atalhos do card de Entradas: abrem o 'iniciar' de cada modulo
# (que resolve Propriedade/Produtor se houver mais de um par).
URL_GERAR_COMUNICADO = '/produtor/comunicado-entrada/iniciar'
URL_IMPRIMIR_COMUNICADO = '/produtor/impressao-comunicado/iniciar'
URL_NOTIFICACAO = '/produtor/notificacao-nascimento/iniciar'
URL_BRINCOS_ESQUECIDOS = '/produtor/brincagem-consulta/iniciar'   # v1.7.0
URL_GERAR_NOTIFICACAO_MORTE = '/produtor/morte/notificacao/gerar/iniciar'   # s111 - Morte: Gerar Notificacao
URL_REIDENTIFICACAO_ENVIAR = '/produtor/reidentificacao-consulta/iniciar'   # s121 - Reidentificacao: Notificacao a enviar
DIAS_BRINCO_ESQUECIDO = 3   # v1.7.0 - lido no brete ha este numero de dias (ou mais) sem GTA = esquecido
URL_BRINCAR_COMPRA = '/produtor/hub-novo/brincagem'   # v1.6.0 - Hub de Brincagem (o Leitor ja lista a GTA PENDENTE)


# -------------------------------------------------------
# Funcao auxiliar: agrupa os pares por Produtor, sem repetir a
# mesma Propriedade (cada Produtor tem o proprio schema).
# Retorna {id_produtor: {id_propriedade: par}}.
# -------------------------------------------------------
def _agrupar_por_produtor(pares):
    grupos = {}
    for par in pares or []:
        grupos.setdefault(par.id_produtor, {})[int(par.id_propriedade)] = par
    return grupos


# -------------------------------------------------------
# Funcao auxiliar: conta as Notificacoes (NAS) ainda NAO impressas
# e com animais, nas Propriedades informadas (criterio identico ao
# de alerta_prazo_notificacao.py).
# -------------------------------------------------------
def _contar_notificacoes_a_imprimir(db, ids_propriedade):
    # v1.13.0 (Etapa 7c) - so as NAS ainda NAO impressas (o banco descarta as ja impressas).
    gtas = (
        db.query(Gta)
        .filter(
            Gta.id_propriedade.in_(ids_propriedade),
            Gta.tipo_movimento == TIPO_MOVIMENTO_NAS,
            Gta.serie_gta == SERIE_NAS,
            ~exists().where(NotificacaoImpressao.id_gta == Gta.id),
        )
        .all()
    )
    if not gtas:
        return 0

    total = 0
    for gta in gtas:
        if gta.status_brincagem == STATUS_CONTROLE_ABERTO:
            qtde = contar_leituras_do_controle(db, gta)      # lidos no brete
        else:
            qtde = db.query(Entrada).filter(Entrada.id_gta_entrada == gta.id).count()
        if qtde > 0:                                          # NAS sem animais: ainda nao e Notificacao
            total += 1
    return total


# -------------------------------------------------------
# Funcao principal.
# -------------------------------------------------------
def montar_resumo_home(pares):
    hoje = date.today()

    resumo = {
        'erro': False,
        'animais_total': 0,
        'animais_por_propriedade': [],     # [{'nome': ..., 'qtde': ...}]
        'liberados_cth': 0,
        'liberados_livres': 0,
        'liberados_total': 0,
        'comunicados_gerar': 0,
        'comunicados_imprimir': 0,
        'notificacoes_imprimir': 0,
        'gtas_brincar': 0,                 # v1.4.0
        'brincos_esquecidos': 0,           # v1.7.0
        'nascimentos_esquecidos': 0,       # v1.8.0
        'mortes_sem_notificacao': 0,       # s111 - animais mortos ainda sem Notificacao (Anexo XXII)
        'url_gerar_notificacao_morte': URL_GERAR_NOTIFICACAO_MORTE,
        'reidentificacoes_a_enviar': 0,    # s121 - animais reidentificados em pedidos ainda NAO enviados a Certificadora
        'reidentificacao_dias': 0,         # s121 - ha quantos dias o pedido mais antigo esta em aberto
        'url_reidentificacao_enviar': URL_REIDENTIFICACAO_ENVIAR,
        'url_brincos_esquecidos': URL_BRINCOS_ESQUECIDOS,
        'url_brincar_compra': URL_BRINCAR_COMPRA,    # v1.5.0
        'url_gerar_comunicado': URL_GERAR_COMUNICADO,
        'url_imprimir_comunicado': URL_IMPRIMIR_COMUNICADO,
        'url_notificacao': URL_NOTIFICACAO,
    }

    # Nome na lista por Propriedade: se o mesmo nome aparece mais de
    # uma vez (copropriedade, Produtores diferentes), acrescenta o
    # Produtor para o usuario distinguir.
    nomes = [par.propriedade_nome for par in (pares or [])]

    for id_produtor, propriedades in _agrupar_por_produtor(pares).items():
        ids = list(propriedades.keys())
        try:
            with get_db_produtor(id_produtor) as db:
                # ---- Animais em estoque, por Propriedade ----
                contagem = dict(
                    db.query(Entrada.id_propriedade, func.count(Entrada.id))
                    .filter(Entrada.id_propriedade.in_(ids))
                    .group_by(Entrada.id_propriedade)
                    .all()
                )
                for id_propriedade, par in propriedades.items():
                    qtde = int(contagem.get(id_propriedade, 0))
                    nome = par.propriedade_nome or ''
                    if nomes.count(par.propriedade_nome) > 1:
                        nome = f'{nome} ({par.produtor_nome})'
                    resumo['animais_por_propriedade'].append({'nome': nome, 'qtde': qtde})
                    resumo['animais_total'] += qtde

                # ---- Liberados para abate (CTH x Livres) ----
                for cota_hilton, qtde in (
                    db.query(Entrada.cota_hilton, func.count(Entrada.id))
                    .filter(
                        Entrada.id_propriedade.in_(ids),
                        Entrada.liberacao_abate.isnot(None),
                        Entrada.liberacao_abate <= hoje,
                    )
                    .group_by(Entrada.cota_hilton)
                    .all()
                ):
                    if cota_hilton:
                        resumo['liberados_cth'] += int(qtde)
                    else:
                        resumo['liberados_livres'] += int(qtde)

                # ---- GTAs de Compra a brincar (v1.4.0): COMPRA + PENDENTE + com Data de Entrega
                # (mesmo filtro das listas da Brincagem) ----
                resumo['gtas_brincar'] += int(
                    db.query(func.count(Gta.id))
                    .filter(
                        Gta.id_propriedade.in_(ids),
                        Gta.tipo_movimento == TIPO_MOVIMENTO_COMPRA,
                        Gta.status_brincagem == STATUS_GTA_PENDENTE,
                        Gta.data_entrega.isnot(None),
                    )
                    .scalar() or 0
                )

                # ---- Brincos de Compra lidos no brete ha 3+ dias, sem GTA/reserva/Comunicado (v1.7.0) ----
                resumo['brincos_esquecidos'] += int(
                    db.query(func.count(Brincagem.id))
                    .filter(
                        Brincagem.id_propriedade.in_(ids),
                        Brincagem.tipo_entrada == 'COMPRA',
                        Brincagem.sts == False,   # noqa: E712
                        Brincagem.id_gta.is_(None),
                        Brincagem.id_gta_reservada.is_(None),
                        Brincagem.numero_comunicado.is_(None),
                        Brincagem.data_brincagem.isnot(None),
                        Brincagem.data_brincagem <= hoje - timedelta(days=DIAS_BRINCO_ESQUECIDO),
                    )
                    .scalar() or 0
                )

                # ---- Brincos de NASCIMENTO lidos ha 3+ dias, ainda sem Notificacao (v1.8.0) ----
                resumo['nascimentos_esquecidos'] += int(
                    db.query(func.count(Brincagem.id))
                    .filter(
                        Brincagem.id_propriedade.in_(ids),
                        Brincagem.tipo_entrada == 'NASCIMENTO',
                        Brincagem.sts == False,   # noqa: E712
                        Brincagem.id_gta.is_(None),
                        Brincagem.data_brincagem.isnot(None),
                        Brincagem.data_brincagem <= hoje - timedelta(days=DIAS_BRINCO_ESQUECIDO),
                    )
                    .scalar() or 0
                )

                # ---- Mortes sem Notificacao (s111): animais mortos cujo Controle (MRT) ainda nao tem numero de Notificacao.
                # Os Produtores esquecem de gerar: o numero de mortos aparece na Home (decisao do Benedito). ----
                resumo['mortes_sem_notificacao'] += int(
                    db.query(func.coalesce(func.sum(ControleMorte.qtd_animais), 0))
                    .filter(ControleMorte.id_propriedade.in_(ids), ControleMorte.numero_comunicado.is_(None))
                    .scalar() or 0
                )

                # ---- Reidentificacao (s121): animais pendentes de Notificacao ou de Notificacao ainda nao enviada a Certificadora (prazo de 30 dias a partir da data do animal mais antigo) ----
                try:
                    qtde_reid, mais_antiga = (
                        db.query(func.count(ReidentificacaoComBaixaItem.id), func.min(ReidentificacaoComBaixaItem.data_reidentificacao))
                        .outerjoin(ReidentificacaoComBaixa, ReidentificacaoComBaixaItem.id_pedido == ReidentificacaoComBaixa.id)
                        .filter(ReidentificacaoComBaixaItem.id_propriedade.in_(ids),
                                or_(ReidentificacaoComBaixaItem.id_pedido.is_(None), ReidentificacaoComBaixa.enviado_em.is_(None)))
                        .one()
                    )
                    resumo['reidentificacoes_a_enviar'] += int(qtde_reid or 0)
                    if mais_antiga is not None:
                        resumo['reidentificacao_dias'] = max(resumo['reidentificacao_dias'], (hoje - mais_antiga).days)
                except Exception:
                    db.rollback()

                # ---- Comunicados a gerar (GTAs brincadas sem Comunicado E com todos os animais
                # conferidos no brete - v1.3.0, mesma regra do Gerar Comunicado) ----
                ids_gtas_sem_comunicado = [
                    linha[0] for linha in
                    db.query(Gta.id)
                    .filter(
                        Gta.id_propriedade.in_(ids),
                        Gta.status_brincagem == STATUS_GTA_BRINCADO,
                        Gta.numero_comunicado.is_(None),
                        Gta.tipo_movimento != TIPO_MOVIMENTO_NAS,
                        Gta.serie_gta != 'CAR',   # v1.13.1 - a Carga nunca tem Comunicado
                    )
                    .all()
                ]
                for id_gta in ids_gtas_sem_comunicado:
                    total_animais, conferidos = contadores_gta(db, id_gta)
                    if total_animais > 0 and conferidos >= total_animais:
                        resumo['comunicados_gerar'] += 1

                # ---- Comunicados a imprimir (ABERTOS - cada numero conta 1) ----
                resumo['comunicados_imprimir'] += (
                    db.query(ComunicadoEntrada.id_propriedade_destino, ComunicadoEntrada.numero_comunicado)
                    .filter(
                        ComunicadoEntrada.id_propriedade_destino.in_(ids),
                        ComunicadoEntrada.status == STATUS_COMUNICADO_ABERTO,
                        ComunicadoEntrada.tipo_entrada != 'TRANSFERENCIA',
                    )
                    .distinct()
                    .count()
                )
                # Transferencia (Pacote 5): so conta a Entrada cuja Saida ja foi impressa.
                linhas_t = (
                    db.query(ComunicadoEntrada.id_propriedade_destino, ComunicadoEntrada.numero_comunicado, ComunicadoEntrada.id_gta)
                    .filter(
                        ComunicadoEntrada.id_propriedade_destino.in_(ids),
                        ComunicadoEntrada.status == STATUS_COMUNICADO_ABERTO,
                        ComunicadoEntrada.tipo_entrada == 'TRANSFERENCIA',
                    )
                    .all()
                )
                if linhas_t:
                    from backend.utils.saida_transfer_impressa import ids_gta_com_saida_impressa
                    gtas_t = db.query(Gta).filter(Gta.id.in_([l[2] for l in linhas_t])).all()
                    impressas = ids_gta_com_saida_impressa(db, gtas_t)   # v1.9.0: olha tambem o schema da origem
                    resumo['comunicados_imprimir'] += len({(l[0], l[1]) for l in linhas_t if l[2] in impressas})

                # ---- Notificacoes de Nascimento a imprimir ----
                resumo['notificacoes_imprimir'] += _contar_notificacoes_a_imprimir(db, ids)

        except Exception:
            logger.exception('Resumo da Home: falha ao ler o Produtor %s', id_produtor)
            resumo['erro'] = True

    resumo['liberados_total'] = resumo['liberados_cth'] + resumo['liberados_livres']
    return resumo

# -------------------------------------------------------
# Funcao NOVA (v1.2.0): situacao da AUDITORIA ERAS de cada Propriedade
# (para a coluna Auditoria da tabela de fazendas e para a faixa da
# fazenda escolhida). A auditoria vive no schema public, entao a
# busca e por Propriedade. Retorna {id_propriedade: dict}, dict com:
#   erro          True se a busca desta Propriedade falhou
#   tem_eras      False = fazenda sem codigo ERAS (coluna mostra "-")
#   codigo        EM_DIA / ATENCAO / URGENTE / PENDENTE / SEM_REGISTRO
#   texto         frase da situacao ("" quando em dia)
#   nao_conforme  True se a ULTIMA vistoria foi NAO CONFORME
# -------------------------------------------------------
def montar_auditoria_por_propriedade(ids_propriedade):
    ids = sorted({int(i) for i in (ids_propriedade or [])})
    resultado = {}
    if not ids:
        return resultado

    try:
        with Session(engine) as db:
            for id_propriedade in ids:
                try:
                    propriedade = db.get(Propriedade, id_propriedade)
                    if propriedade is None or not tem_codigo_eras(propriedade.codigo_eras):
                        resultado[id_propriedade] = {
                            'erro': False, 'tem_eras': False,
                            'codigo': None, 'texto': '', 'nao_conforme': False,
                        }
                        continue

                    situacao = calcular_situacao(buscar_ultima_auditoria(db, id_propriedade))
                    resultado[id_propriedade] = {
                        'erro': False, 'tem_eras': True,
                        'codigo': situacao['codigo'],
                        'texto': situacao['texto'],
                        'nao_conforme': situacao['nao_conforme'],
                    }
                except Exception:
                    logger.exception('Resumo da Home: falha na auditoria ERAS da Propriedade %s', id_propriedade)
                    db.rollback()
                    resultado[id_propriedade] = {'erro': True}
    except Exception:
        logger.exception('Resumo da Home: falha ao abrir a busca de auditorias ERAS')

    for id_propriedade in ids:
        resultado.setdefault(id_propriedade, {'erro': True})
    return resultado


# -------------------------------------------------------
# Funcao NOVA (v1.1.0): numeros de CADA fazenda (par
# Propriedade+Produtor), para a tabela de fazendas do Home novo.
# Retorna uma lista de dicts, na mesma ordem dos pares:
#   id_produtor, id_propriedade, nome, produtor_nome, uf,
#   mesma_fazenda_varios_produtores (True se a mesma Propriedade
#   aparece em mais de um par), resumo (o mesmo dict de
#   montar_resumo_home, calculado so para aquele par) e
#   auditoria (v1.2.0: situacao da auditoria ERAS da Propriedade).
# -------------------------------------------------------
def montar_resumo_por_fazenda(pares):
    pares = list(pares or [])

    vezes_por_propriedade = {}
    for par in pares:
        chave = int(par.id_propriedade)
        vezes_por_propriedade[chave] = vezes_por_propriedade.get(chave, 0) + 1

    auditorias = montar_auditoria_por_propriedade([par.id_propriedade for par in pares])

    fazendas = []
    for par in pares:
        fazendas.append({
            'id_produtor': par.id_produtor,
            'id_propriedade': par.id_propriedade,
            'nome': par.propriedade_nome,
            'produtor_nome': par.produtor_nome,
            'uf': par.uf,
            'mesma_fazenda_varios_produtores': vezes_por_propriedade[int(par.id_propriedade)] > 1,
            'resumo': montar_resumo_home([par]),
            'auditoria': auditorias[int(par.id_propriedade)],
        })
    return fazendas


# =========================================================
# FIM DE ARQUIVO: backend\utils\home_resumo.py
# =========================================================
