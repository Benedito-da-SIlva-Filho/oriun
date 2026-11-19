# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\documentos_produtor.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-20 17:18 -03
# ATUALIZADO EM: 2026-11-12 19:00 -03
# VERSAO: 2.0.1
# v2.0.1: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras do CNPJ mantidas na limpeza e na formatacao. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     CPF e CNPJ do Produtor (Sessao 101, decisao de Benedito). No Magic o cadastro do Produtor e POR FAZENDA,
#     entao o Produtor pode ter CPF e CNPJ numa fazenda e so um deles em outra. No Orion:
#         - Produtor (tabela produtores): tipo_pessoa + cpf_cnpj = documento PRINCIPAL (login, busca, blockchain).
#         - Vinculo Produtor+Propriedade (propriedade_produtor.documento_secundario) = documento SECUNDARIO
#           daquela fazenda: o CNPJ do Produtor Fisico ou o CPF do Produtor Juridico. Opcional.
#
#     Funcoes:
#         documentos_do_produtor(produtor, vinculo=None) -> (cpf, cnpj)   so digitos ('' se nao tem).
#             Principal pelo tipo de pessoa; secundario vem do vinculo. Nunca devolve CPF no lugar de CNPJ.
#             CPF de 14 digitos comecando com 000 (legado) e aparado para os 11 digitos finais.
#         secundario_do_vinculo(vinculo) -> texto do documento secundario (so digitos) para a tela de cadastro.
#
#     v1.0.0: Criacao (Sessao 101) - documentos nas colunas cpf/cnpj de produtores.
#     v2.0.0: Sessao 101 (18:10) - o secundario passa a ficar no VINCULO (por fazenda); some aplicar_documentos.
# =========================================================

import re


def _digitos(valor):
    return re.sub(r'[^0-9A-Za-z]', '', str(valor or '')).upper()   # CNPJ alfanumerico: mantem letras


def documentos_do_produtor(produtor, vinculo=None):
    """(cpf, cnpj) do Produtor nesta fazenda, so digitos; '' quando nao tem."""
    if produtor is None:
        return '', ''
    principal = _digitos(getattr(produtor, 'cpf_cnpj', None))
    secundario = _digitos(getattr(vinculo, 'documento_secundario', None)) if vinculo is not None else ''
    tipo = str(getattr(produtor, 'tipo_pessoa', '') or '').upper()
    if tipo == 'FISICA':
        if len(principal) == 14 and principal.startswith('000'):
            principal = principal[-11:]
        return principal, secundario
    if tipo == 'JURIDICA':
        return secundario, principal
    return '', ''


def secundario_do_vinculo(vinculo):
    """Documento secundario do vinculo (so digitos), '' se nao ha."""
    if vinculo is None:
        return ''
    return _digitos(getattr(vinculo, 'documento_secundario', None))

# =========================================================
# FIM DE ARQUIVO: backend\utils\documentos_produtor.py
# =========================================================
