# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\alerta_prazo_notificacao.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-02 19:00 -03
# ATUALIZADO EM: 2026-11-16 10:55 -03
# VERSAO: 1.3.0
# v1.3.0: Sessao 128 (2026-11-16 10:55 -03) - AUDITORIA ETAPA 7c (desempenho e log): busca no banco so as NAS NAO impressas e ja dentro da janela do alerta (antes lia todo o historico a cada abertura da Home); erro de uma fazenda agora fica no log do servidor, sem derrubar a Home. REVERSAO: .bak_antes_etapa7c.
#
# DESCRICAO:
#     ALERTA DOS 30 DIAS da Notificacao de Nascimento (NAS): a
#     Notificacao tem de ser enviada a Certificadora em ate 30 dias,
#     contados da Data de Brincagem (regra de Benedito, Sessao 084).
#     Esta funcao procura, em TODAS as Propriedades do usuario, as
#     Notificacoes AINDA NAO IMPRESSAS (tb_7020) que vencem em ate
#     5 dias ou ja venceram, para a Home do Produtor mostrar o aviso.
#
#     buscar_alertas_notificacao(pares) -> lista de dicts, da mais
#     urgente (vencida ha mais tempo) para a menos:
#         {id_produtor, id_propriedade, propriedade, numero, data,
#          restantes (negativo = vencida), vencida (bool), texto,
#          qtde, url}
#     Nunca levanta erro para a Home: qualquer falha em uma
#     Propriedade e ignorada (o aviso e um extra, nao pode derrubar a
#     tela inicial). So leitura.
#
#     v1.0.0: Criacao do modulo (Sessao 084, 02/10/2026, 19:00 -03).
#     v1.1.0: Sessao 084 (02/10/2026, 21:00 -03) - o prazo (30 dias) e o
#             alerta (5 dias) passam a vir de regras_sisbov.py v1.2.0, nao
#             mais de constantes copiadas aqui. Nenhuma outra mudanca.
#     v1.2.0: Sessao 084 (02/10/2026, 23:30 -03) - o alerta tambem vale para o
#             Controle (NAS) PENDENTE com animais lidos no brete (ainda sem
#             "Gerar Notificacao"): o prazo de 30 dias corre igual. Nenhuma
#             outra mudanca.
# =========================================================

import logging
from datetime import date, timedelta

from sqlalchemy import exists

from backend.models import Propriedade
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_4001_gta import Gta
from backend.models.tb_7020_notificacao_impressao import NotificacaoImpressao
from backend.utils.multitenant import get_db_produtor
from backend.utils.gravacao_nascimento import contar_leituras_do_controle, STATUS_CONTROLE_ABERTO
from backend.utils.regras_sisbov import (
    PRAZO_ENVIO_NOTIFICACAO_DIAS as PRAZO_ENVIO_DIAS,
    DIAS_ALERTA_PRAZO_NOTIFICACAO as DIAS_ALERTA_PRAZO,
)
logger = logging.getLogger(__name__)   # v1.3.0
TIPO_MOVIMENTO_NAS = 'NASCTO-DESMAME'
SERIE_NAS = 'NAS'


def _texto_prazo(restantes):
    if restantes < 0:
        return f'vencida há {-restantes} dia(s)'
    if restantes == 0:
        return 'vence HOJE'
    return f'vence em {restantes} dia(s)'


def _url_lista(id_produtor, id_propriedade):
    # Passa pelo seletor de vinculo (auth.selecionar_vinculo): confere o par
    # e grava o Produtor na sessao antes de abrir a lista.
    return (
        f'/produtor/selecionar-vinculo?id_produtor={id_produtor}&id_propriedade={id_propriedade}'
        f'&proximo=/produtor/notificacao-nascimento/listar&campo_propriedade=id_propriedade'
    )


def buscar_alertas_notificacao(pares):
    hoje = date.today()
    alertas = []
    vistos = set()

    for par in pares or []:
        chave = (par.id_produtor, par.id_propriedade)
        if chave in vistos:
            continue
        vistos.add(chave)

        try:
            with get_db_produtor(par.id_produtor) as db:
                # v1.3.0 (Etapa 7c) - so NAS NAO impressas e ja dentro da janela do alerta
                # (restantes <= DIAS_ALERTA_PRAZO  <=>  data_emissao <= hoje + DIAS_ALERTA_PRAZO - PRAZO_ENVIO_DIAS).
                limite_emissao = hoje + timedelta(days=DIAS_ALERTA_PRAZO - PRAZO_ENVIO_DIAS)
                gtas = (
                    db.query(Gta)
                    .filter(Gta.id_propriedade == int(par.id_propriedade),
                            Gta.tipo_movimento == TIPO_MOVIMENTO_NAS, Gta.serie_gta == SERIE_NAS,
                            Gta.data_emissao.isnot(None), Gta.data_emissao <= limite_emissao,
                            ~exists().where(NotificacaoImpressao.id_gta == Gta.id))
                    .all()
                )
                if not gtas:
                    continue
                propriedade = db.get(Propriedade, int(par.id_propriedade))
                nome_propriedade = propriedade.nome if propriedade else ''

                for gta in gtas:
                    if not gta.data_emissao:
                        continue
                    if gta.status_brincagem == STATUS_CONTROLE_ABERTO:
                        qtde = contar_leituras_do_controle(db, gta)    # v1.2.0 - lidos no brete
                    else:
                        qtde = db.query(Entrada).filter(Entrada.id_gta_entrada == gta.id).count()
                    if qtde == 0:
                        continue    # NAS sem animais: ainda nao e Notificacao
                    restantes = (gta.data_emissao + timedelta(days=PRAZO_ENVIO_DIAS) - hoje).days
                    if restantes > DIAS_ALERTA_PRAZO:
                        continue
                    alertas.append({
                        'id_produtor': par.id_produtor,
                        'id_propriedade': par.id_propriedade,
                        'propriedade': nome_propriedade,
                        'numero': gta.numero_gta_completo,
                        'data': gta.data_emissao.strftime('%d/%m/%Y'),
                        'restantes': restantes,
                        'vencida': restantes < 0,
                        'texto': _texto_prazo(restantes),
                        'qtde': qtde,
                        'url': _url_lista(par.id_produtor, par.id_propriedade),
                    })
        except Exception:
            logger.exception('Alerta de prazo da Notificacao: falha ao ler a Propriedade %s', par.id_propriedade)   # v1.3.0 - o erro fica no log
            continue    # o aviso e um extra - nunca derruba a Home

    alertas.sort(key=lambda a: (a['restantes'], a['numero']))
    return alertas

# =========================================================
# FIM DE ARQUIVO: backend\utils\alerta_prazo_notificacao.py
# =========================================================
