# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\equipe_propriedade.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-14 12:55 -03
# ATUALIZADO EM: 2026-10-14 12:55 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Quando um Produtor ENTRA numa propriedade que ja existe, a
#     equipe (colaboradores) dos outros produtores dessa propriedade
#     ganha automaticamente um vinculo com o novo produtor - mesmo
#     cargo, data_inicio de hoje. Combinado com Benedito (Sessao 096):
#     a equipe e da PROPRIEDADE, vale para todos os produtores dela.
#
#     Regras:
#       - So copia vinculos ATIVOS (data_fim nulo).
#       - Nao copia TITULAR (titular e o proprio produtor).
#       - Pessoa que e TITULAR de algum produtor da propriedade nao
#         e tratada como equipe (ela e produtora), nao e copiada.
#       - Nao duplica: quem ja tem qualquer vinculo com o novo
#         produtor e pulado.
#       - Nao faz commit: roda dentro da transacao de quem chama.
#
#     v1.0.0: Criacao (Sessao 096, 14/10/2026).
# =========================================================

from datetime import date
from backend.models import PropriedadeProdutor, UsuarioVinculo


def ligar_equipe_ao_produtor(db, id_propriedade, id_produtor_novo):
    # Demais produtores ativos da propriedade (sem o novo).
    outros = [
        vp.id_produtor
        for vp in db.query(PropriedadeProdutor).filter(
            PropriedadeProdutor.id_propriedade == id_propriedade,
            PropriedadeProdutor.data_fim.is_(None),
            PropriedadeProdutor.id_produtor != id_produtor_novo
        ).all()
    ]
    if not outros:
        return 0

    vinculos = db.query(UsuarioVinculo).filter(
        UsuarioVinculo.id_produtor.in_(outros),
        UsuarioVinculo.data_fim.is_(None)
    ).all()

    # Quem e titular de algum produtor da propriedade nao e equipe.
    titulares = {v.id_usuario for v in vinculos if v.cargo == 'TITULAR'}

    # Quem ja tem vinculo com o novo produtor nao entra de novo.
    ja_tem = {
        v.id_usuario
        for v in db.query(UsuarioVinculo).filter(
            UsuarioVinculo.id_produtor == id_produtor_novo
        ).all()
    }

    criados = 0
    vistos = set()
    for v in vinculos:
        if v.id_usuario in titulares or v.id_usuario in ja_tem or v.id_usuario in vistos:
            continue
        vistos.add(v.id_usuario)
        db.add(UsuarioVinculo(
            id_usuario  = v.id_usuario,
            id_produtor = id_produtor_novo,
            cargo       = v.cargo,
            data_inicio = date.today(),
            data_fim    = None
        ))
        criados += 1

    return criados

# =========================================================
# FIM DE ARQUIVO: backend\utils\equipe_propriedade.py
# =========================================================
