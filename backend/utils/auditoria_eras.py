# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\auditoria_eras.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-07 12:05 -03
# ATUALIZADO EM: 2026-10-07 12:05 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Regras das Auditorias ERAS num lugar so, para as telas e o
#     Home nunca discordarem:
#
#       - calcular_situacao(ultima): situacao da fazenda a partir da
#         ULTIMA vistoria (ou None, se nunca houve):
#             SEM_REGISTRO  ERAS sem nenhuma vistoria -> "Sem data:
#                           contatar a Certificadora" (ambar)
#             EM_DIA        proxima data a mais de 15 dias (sem aviso)
#             ATENCAO       faltam de 8 a 15 dias (amarelo)
#             URGENTE       faltam de 1 a 7 dias (vermelho)
#             PENDENTE      a data chegou ou passou, sem nova vistoria
#                           registrada (vermelho)
#         Mais a marca nao_conforme (a ultima vistoria foi NAO
#         CONFORME), usada pelo Home.
#       - validar_dados(...): validacao do formulario (erro = texto
#         unico, para no primeiro problema; mensagens dizem
#         "incorreta", nunca "invalida").
#       - precisa_alerta_60(...): vistoria com 60 dias ou mais - a
#         correcao exige confirmacao.
#       - buscar_ultima_auditoria / buscar_historico: leitura.
#
#     So le o banco nas 2 funcoes de busca; nenhuma grava.
#
#     v1.0.0: Criacao do modulo (Sessao 089, 07/10/2026, 12:05 -03).
# =========================================================

from datetime import date, datetime

from backend.models import AuditoriaEras

# -------------------------------------------------------
# Constantes
# -------------------------------------------------------
VEREDITO_CONFORME = 'CONFORME'
VEREDITO_NAO_CONFORME = 'NAO_CONFORME'
VEREDITOS = (VEREDITO_CONFORME, VEREDITO_NAO_CONFORME)
ROTULO_VEREDITO = {
    VEREDITO_CONFORME: 'CONFORME',
    VEREDITO_NAO_CONFORME: 'NÃO CONFORME',
}

DIAS_ATENCAO = 15            # faltam 15 dias ou menos: amarelo
DIAS_URGENTE = 7             # faltam 7 dias ou menos: vermelho
DIAS_ALERTA_CORRECAO = 60    # vistoria com 60 dias ou mais: correcao pede confirmacao

MAX_VISTORIADOR = 100        # bate com tb_auditoria_eras.vistoriador
MAX_OBSERVACAO = 1000        # limite da tela (a coluna e TEXT)

SIT_SEM_REGISTRO = 'SEM_REGISTRO'
SIT_EM_DIA = 'EM_DIA'
SIT_ATENCAO = 'ATENCAO'
SIT_URGENTE = 'URGENTE'
SIT_PENDENTE = 'PENDENTE'


# -------------------------------------------------------
# Funcao auxiliar: a Propriedade participa do ERAS? (codigo_eras
# preenchido = unico indicador, ver models/propriedade.py)
# -------------------------------------------------------
def tem_codigo_eras(codigo_eras):
    return bool((codigo_eras or '').strip())


# -------------------------------------------------------
# Situacao da fazenda a partir da ULTIMA vistoria.
# 'ultima' e qualquer objeto com proxima_data e veredito (ou None).
# Devolve um dict: codigo, texto, dias (ate a proxima data; negativo
# se passou), nao_conforme.
# -------------------------------------------------------
def calcular_situacao(ultima, hoje=None):
    hoje = hoje or date.today()

    if ultima is None:
        return {
            'codigo': SIT_SEM_REGISTRO,
            'texto': 'Sem data: contatar a Certificadora',
            'dias': None,
            'nao_conforme': False,
        }

    dias = (ultima.proxima_data - hoje).days
    nao_conforme = (ultima.veredito == VEREDITO_NAO_CONFORME)

    if dias <= 0:
        codigo, texto = SIT_PENDENTE, 'Auditoria pendente'
    elif dias <= DIAS_URGENTE:
        codigo, texto = SIT_URGENTE, _texto_em_dias(dias)
    elif dias <= DIAS_ATENCAO:
        codigo, texto = SIT_ATENCAO, _texto_em_dias(dias)
    else:
        codigo, texto = SIT_EM_DIA, ''

    return {'codigo': codigo, 'texto': texto, 'dias': dias, 'nao_conforme': nao_conforme}


def _texto_em_dias(dias):
    return 'Auditoria em 1 dia' if dias == 1 else f'Auditoria em {dias} dias'


# -------------------------------------------------------
# Correcao de vistoria com 60 dias ou mais exige confirmacao.
# -------------------------------------------------------
def precisa_alerta_60(data_vistoria, hoje=None):
    hoje = hoje or date.today()
    return (hoje - data_vistoria).days >= DIAS_ALERTA_CORRECAO


# -------------------------------------------------------
# Texto de data no padrao da tela (dd/mm/aaaa).
# -------------------------------------------------------
def formatar_data(valor):
    return valor.strftime('%d/%m/%Y') if valor else ''


# -------------------------------------------------------
# Converte o texto do campo de data (aaaa-mm-dd, do navegador)
# em date. Devolve None se estiver vazio ou incorreto.
# -------------------------------------------------------
def _ler_data(texto):
    try:
        return datetime.strptime((texto or '').strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


# -------------------------------------------------------
# Validacao do formulario de vistoria. Recebe os textos crus do
# formulario. Devolve (dados, erro): se houver erro, dados e None e
# erro e UMA mensagem (para no primeiro problema).
# dados = {data_vistoria, veredito, vistoriador, proxima_data,
# observacao} ja convertidos.
# -------------------------------------------------------
def validar_dados(data_vistoria, veredito, vistoriador, proxima_data, observacao, hoje=None):
    hoje = hoje or date.today()

    data_v = _ler_data(data_vistoria)
    if not (data_vistoria or '').strip():
        return None, 'Informe a data da vistoria.'
    if data_v is None:
        return None, 'Data da vistoria incorreta.'
    if data_v > hoje:
        return None, 'A data da vistoria não pode ser futura.'

    if (veredito or '').strip() not in VEREDITOS:
        return None, 'Informe o veredito da Certificadora: CONFORME ou NÃO CONFORME.'

    nome = ' '.join((vistoriador or '').split())
    if not nome:
        return None, 'Informe o nome do vistoriador/auditor.'
    if len(nome) > MAX_VISTORIADOR:
        return None, f'Nome do vistoriador/auditor muito longo (máximo {MAX_VISTORIADOR} caracteres).'

    data_p = _ler_data(proxima_data)
    if not (proxima_data or '').strip():
        return None, 'Informe a data da próxima vistoria.'
    if data_p is None:
        return None, 'Data da próxima vistoria incorreta.'
    if data_p <= data_v:
        return None, 'A próxima vistoria deve ser depois da data desta vistoria.'

    obs = (observacao or '').strip()
    if len(obs) > MAX_OBSERVACAO:
        return None, f'Observação muito longa (máximo {MAX_OBSERVACAO} caracteres).'

    return {
        'data_vistoria': data_v,
        'veredito': veredito.strip(),
        'vistoriador': nome,
        'proxima_data': data_p,
        'observacao': obs or None,
    }, None


# -------------------------------------------------------
# Leitura: ultima vistoria da Propriedade (mais recente pela data
# da vistoria; empate pelo id). None se nunca houve.
# -------------------------------------------------------
def buscar_ultima_auditoria(db, id_propriedade):
    return (
        db.query(AuditoriaEras)
        .filter(AuditoriaEras.id_propriedade == id_propriedade)
        .order_by(AuditoriaEras.data_vistoria.desc(), AuditoriaEras.id.desc())
        .first()
    )


# -------------------------------------------------------
# Leitura: historico completo da Propriedade, mais recente primeiro.
# -------------------------------------------------------
def buscar_historico(db, id_propriedade):
    return (
        db.query(AuditoriaEras)
        .filter(AuditoriaEras.id_propriedade == id_propriedade)
        .order_by(AuditoriaEras.data_vistoria.desc(), AuditoriaEras.id.desc())
        .all()
    )

# =========================================================
# FIM DE ARQUIVO: backend\utils\auditoria_eras.py
# =========================================================
