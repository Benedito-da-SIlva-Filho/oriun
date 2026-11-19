# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\entrada_comunicada.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-23 12:20 -03
# ATUALIZADO EM: 2026-10-23 18:00 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     TRAVA DA SAIDA (decisao do Benedito, Sessoes 104 e 105): o animal so existe de verdade - e so pode sair da
#     Propriedade - se a entrada dele estiver comprovada:
#         - QUALQUER TIPO: conferido_brete = False (lancado pelo escritorio, o brete ainda nao leu o brinco) bloqueia.
#         - COMPRA: precisa do Comunicado de Entrada gerado (tb_2001.numero_comunicado preenchido).
#         - NASCTO-DESMAME: precisa da Notificacao de Nascimento (NAS) com status_brincagem = 'BRINCADO' E o animal
#           conferido no brete (o Numero de Controle so vale depois da leitura no brete).
#         - TRANSFERENCIA: precisa da GTA de Entrada (id_gta_entrada preenchido); nao passa pelo brete.
#         - REIDENTIFICACAO: sem trava de entrada (so a regra do brete acima).
#
#     Funcao:
#         motivo_entrada_pendente(db, animal) -> texto do bloqueio, ou None se o animal pode sair.
#
#     Usada por: saida_leitor._validar_leitura (Leitor, Bastao, Abate por Arquivo e Substituicao/Troca, que reusam essa
#     conferencia) e saida_comunicado._montar_lotes (segunda trava, na geracao do Comunicado de Saida).
#
#     v1.0.0: Sessao 104 (23/10/2026, 12:20 -03) - Criacao.
#     v1.1.0: Sessao 105 (23/10/2026, 18:00 -03) - (1) conferido_brete = False bloqueia qualquer tipo (caso real: brinco
#             123456789010093, Nascimento lancado pelo escritorio e ainda nao lido no brete passava na Saida);
#             (2) TRANSFERENCIA passa a exigir GTA de Entrada. REVERSAO: devolver .bak_antes_s105b.
# =========================================================

from backend.models.tb_4001_gta import Gta

TIPO_COMPRA = 'COMPRA'
TIPO_NASCIMENTO = 'NASCTO-DESMAME'
TIPO_TRANSFERENCIA = 'TRANSFERENCIA'
STATUS_NOTIFICACAO_GERADA = 'BRINCADO'

MENSAGEM_SEM_COMUNICADO_ENTRADA = 'Animal sem Comunicado de Entrada. Gere o Comunicado de Entrada antes da Saída.'
MENSAGEM_SEM_NOTIFICACAO = 'Animal de Nascimento sem Notificação gerada. Gere a Notificação de Nascimento antes da Saída.'
MENSAGEM_NAO_CONFERIDO_BRETE = ('Animal lançado pelo escritório e ainda não conferido no brete. '
                                'Faça a leitura no brete antes da Saída.')
MENSAGEM_SEM_GTA_ENTRADA = 'Animal de Transferência sem GTA de Entrada. Registre a GTA de Entrada antes da Saída.'


def motivo_entrada_pendente(db, animal):
    """Texto do bloqueio quando a entrada do animal ainda nao foi comprovada; None quando pode sair."""
    if getattr(animal, 'conferido_brete', True) is False:
        return MENSAGEM_NAO_CONFERIDO_BRETE
    tipo = str(getattr(animal, 'tipo_entrada', '') or '')
    if tipo == TIPO_COMPRA:
        if animal.numero_comunicado is None:
            return MENSAGEM_SEM_COMUNICADO_ENTRADA
        return None
    if tipo == TIPO_NASCIMENTO:
        gta = db.get(Gta, animal.id_gta_entrada) if animal.id_gta_entrada else None
        if gta is None or str(gta.status_brincagem or '') != STATUS_NOTIFICACAO_GERADA:
            return MENSAGEM_SEM_NOTIFICACAO
        return None
    if tipo == TIPO_TRANSFERENCIA:
        if not animal.id_gta_entrada:
            return MENSAGEM_SEM_GTA_ENTRADA
        return None
    return None

# =========================================================
# FIM DE ARQUIVO: backend\utils\entrada_comunicada.py
# =========================================================
