# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\saida_transfer_impressa.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-29 19:20 -03
# ATUALIZADO EM: 2026-10-29 19:20 -03
# VERSAO:       1.0.0
#
# DESCRICAO:
#     Transferencia ENTRE PRODUTORES (Sessao 108): a Entrada do destino so imprime depois que a
#     Saida da origem foi impressa. Quando origem e destino estao no mesmo schema, o Comunicado de
#     Saida esta na mesma base; quando sao Produtores diferentes, ele esta no schema do Produtor
#     de origem. Esta funcao olha primeiro o schema atual e, se nao achar, o(s) schema(s) do(s)
#     Produtor(es) vinculado(s) a Propriedade de origem da GTA. So leitura.
#
#     v1.0.0: Criacao (Sessao 108, 29/10/2026, 19:20 -03).
#     REVERSAO: apagar este arquivo (e devolver os .bak_antes_s108_entre_produtores).
# =========================================================

from sqlalchemy.orm import Session

from backend.database import engine
from backend.models.propriedade_produtor import PropriedadeProdutor
from backend.models.tb_2011_com_saidas import ComunicadoSaida
from backend.utils.multitenant import get_db_produtor


def ids_gta_com_saida_impressa(db, gtas):
    """
    gtas: lista de objetos Gta (do schema de 'db'). Devolve o conjunto de gta.id cuja Saida de
    Transferencia ja esta IMPRESSA - no schema atual ou no schema do Produtor de origem.
    """
    gtas = [g for g in (gtas or []) if g is not None]
    if not gtas:
        return set()

    ids = [g.id for g in gtas]
    impressas = {
        s.id_gta for s in db.query(ComunicadoSaida)
        .filter(ComunicadoSaida.id_gta.in_(ids), ComunicadoSaida.tipo_saida == 'TRANSFER',
                ComunicadoSaida.status == 'IMPRESSO').all()
    }

    faltam = [g for g in gtas if g.id not in impressas]
    if not faltam:
        return impressas

    # Saida de outro schema: procura no Produtor vinculado a Propriedade de origem da GTA.
    with Session(engine) as dbp:
        vinculos = {}
        for g in faltam:
            if g.id_propriedade not in vinculos:
                vinculos[g.id_propriedade] = [
                    v[0] for v in dbp.query(PropriedadeProdutor.id_produtor)
                    .filter(PropriedadeProdutor.id_propriedade == g.id_propriedade,
                            PropriedadeProdutor.data_fim.is_(None)).all()
                ]

    por_produtor = {}
    for g in faltam:
        for id_produtor in vinculos.get(g.id_propriedade, []):
            por_produtor.setdefault(id_produtor, []).append(g)

    for id_produtor, lista in por_produtor.items():
        try:
            with get_db_produtor(id_produtor) as db_origem:
                for g in lista:
                    if g.id in impressas:
                        continue
                    achou = (
                        db_origem.query(ComunicadoSaida.id)
                        .filter(ComunicadoSaida.gta_numero == g.numero_gta_completo,
                                ComunicadoSaida.id_propriedade_origem == g.id_propriedade,
                                ComunicadoSaida.tipo_saida == 'TRANSFER',
                                ComunicadoSaida.status == 'IMPRESSO').first()
                    )
                    if achou:
                        impressas.add(g.id)
        except Exception:
            continue   # Produtor inativo/sem schema: nao achou, a Entrada continua aguardando a Saida

    return impressas

# =========================================================
# FIM DE ARQUIVO: backend\utils\saida_transfer_impressa.py
# =========================================================
