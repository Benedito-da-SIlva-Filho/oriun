# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\gta_duplicada.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-04 17:50 -03
# ATUALIZADO EM: 2026-10-04 17:50 -03
# VERSAO:       1.0.0
#
# DESCRICAO:
#     Regra unica de GTA DUPLICADA do Orion (decisao de Benedito,
#     04/10/2026): jamais pode haver duas GTAs iguais - e um
#     documento emitido pelo orgao do Estado. O problema deve ser
#     identificado NA ENTRADA da GTA, por qualquer meio (PDF,
#     digitacao manual, alteracao do numero), nunca depois.
#
#     GTA IDENTICA = mesma UF + Serie + Numero + SENTIDO, dentro do
#     MESMO Produtor (schema do Produtor - o banco nao enxerga outro
#     Produtor, e o aviso nunca deve revelar o dado de outro
#     cliente):
#       - UF diferente = GTA diferente (a mesma Serie e o mesmo
#         Numero podem existir em Estados diferentes);
#       - o SENTIDO conta: a mesma GTA pode existir UMA vez como
#         ENTRADA e outra como SAIDA (Transferencia entre
#         Propriedades do mesmo Produtor). Duas ENTRADAS (ou duas
#         SAIDAS) iguais, nunca.
#       - ZEROS A ESQUERDA CONTAM: o Numero e comparado EXATAMENTE
#         como gravado (o documento tem os zeros). Compara-se so
#         UF e Serie em MAIUSCULO e sem espacos nas pontas.
#
#     DUAS BARREIRAS (as duas valem):
#       1. Esta checagem, ANTES de gravar - da a mensagem clara.
#       2. A trava do banco (constraint uq_tb_4001_gta_uf_serie_
#          numero_sentido em tb_4001_gta) - garante o "jamais" mesmo
#          se uma rota esquecer de chamar esta funcao ou se duas
#          pessoas salvarem a mesma GTA ao mesmo tempo (a segunda
#          recebe IntegrityError, que a rota transforma na mesma
#          mensagem - ver eh_violacao_unicidade_gta()).
#     Toda rota NOVA que grave ou altere UF/Serie/Numero de uma GTA
#     deve chamar buscar_gta_duplicada() antes de gravar.
#
#     FUNCOES:
#       buscar_gta_duplicada(db, uf, serie, numero, sentido,
#                            id_ignorar=None) -> Gta ou None.
#           id_ignorar = id da PROPRIA GTA ao alterar (nunca se
#           acusa duplicada contra si mesma).
#       mensagem_gta_duplicada(gta) -> texto da mensagem aprovada.
#           Chamar com a sessao do banco ainda aberta.
#       eh_violacao_unicidade_gta(erro) -> True se o IntegrityError
#           e desta trava (e nao de outra restricao).
#
#     So leitura - nunca grava nem da commit.
#
#     v1.0.0: Criacao do modulo (Sessao 085, 04/10/2026, 17:50 -03).
# =========================================================

from backend.models.tb_4001_gta import Gta

# Nome da trava no banco (tb_4001_gta) - o mesmo do model e do script SQL.
NOME_TRAVA_GTA_UNICA = 'uq_tb_4001_gta_uf_serie_numero_sentido'


# -------------------------------------------------------
# Procura, no schema do Produtor da sessao 'db', uma GTA com a
# mesma UF + Serie + Numero + sentido. Devolve a GTA encontrada ou
# None. 'id_ignorar' exclui a propria GTA (usado ao alterar).
# -------------------------------------------------------
def buscar_gta_duplicada(db, uf_gta, serie_gta, numero_gta_sequencial, sentido, id_ignorar=None):
    uf = (uf_gta or '').strip().upper()
    serie = (serie_gta or '').strip().upper()
    numero = (numero_gta_sequencial or '').strip()     # zeros a esquerda CONTAM - nao normalizar

    # Sem os 3 campos nao ha o que comparar - as rotas ja validam a
    # obrigatoriedade antes (e a trava do banco cobre o resto).
    if not uf or not serie or not numero:
        return None

    consulta = db.query(Gta).filter(
        Gta.uf_gta == uf,
        Gta.serie_gta == serie,
        Gta.numero_gta_sequencial == numero,
        Gta.sentido == sentido,
    )
    if id_ignorar is not None:
        consulta = consulta.filter(Gta.id != int(id_ignorar))
    return consulta.first()


# -------------------------------------------------------
# Mensagem aprovada por Benedito (04/10/2026). Le a GTA ja
# encontrada - chamar com a sessao do banco ainda aberta.
# -------------------------------------------------------
def mensagem_gta_duplicada(gta):
    numero = f'{gta.uf_gta}-{gta.serie_gta}-{gta.numero_gta_sequencial}'
    sentido = 'Saída' if gta.sentido == 'SAIDA' else 'Entrada'
    emissao = gta.data_emissao.strftime('%d/%m/%Y') if gta.data_emissao else '-'
    return (
        f'A GTA {numero} já está cadastrada neste Produtor ({sentido}, emitida em {emissao}). '
        f'Não é permitido cadastrar a mesma GTA duas vezes.'
    )


# -------------------------------------------------------
# O IntegrityError veio da trava de GTA unica? (e nao de outra FK/
# restricao qualquer, que deve continuar estourando normalmente).
# -------------------------------------------------------
def eh_violacao_unicidade_gta(erro):
    return NOME_TRAVA_GTA_UNICA in str(getattr(erro, 'orig', erro))

# =========================================================
# FIM DE ARQUIVO: backend\utils\gta_duplicada.py
# =========================================================
