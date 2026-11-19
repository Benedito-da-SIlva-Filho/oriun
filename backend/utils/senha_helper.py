# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\senha_helper.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-08-13 13:20 -03
# ATUALIZADO EM: 2026-11-16 11:45 -03
# VERSAO:       1.3.0
#
# DESCRICAO:
#     Utilitario compartilhado de login e senha: geracao de senha
#     provisoria e, desde a v1.1.0, gravacao e conferencia de
#     senha SEM diferenca entre maiuscula e minuscula e, desde a
#     v1.2.0, SEM espacos no inicio e no fim (login e senha).
#
#     v1.0.0: Criacao do modulo (Sessao 034, continuacao 9).
#             Extraido de auth.py, convite.py e produtores.py.
#     v1.1.0: Sessao 097 (15/10/2026, 08:20 -03) - ACESSO FACIL
#             (decisao de Benedito: o sistema nao guarda dado que
#             exija seguranca maxima; facilitar o acesso).
#             - gerar_senha_provisoria(): agora 3 letras
#               minusculas + 2 numeros (antes tinha maiusculas,
#               que atrapalhavam a digitacao no celular).
#             - NOVA gerar_hash_senha(): grava o hash da senha
#               sempre em minusculo.
#             - NOVA conferir_senha(): aceita a senha como foi
#               digitada OU em minusculo. Se a senha antiga tinha
#               maiuscula e entrou certa, devolve o hash novo
#               (minusculo) para o login regravar sozinho - assim
#               ninguem precisa resetar a senha.
#     v1.2.0: Sessao 097 (15/10/2026, 08:50 -03) - ESPACOS NAS
#             PONTAS (decisao de Benedito: nenhum login ou senha
#             do sistema tem espaco; o corretor do celular costuma
#             colocar um sozinho no fim).
#             - NOVA normalizar_login(): tira espacos do inicio e
#               do fim do login.
#             - gerar_hash_senha() e conferir_senha(): tambem
#               ignoram espacos do inicio e do fim da senha.
#     v1.3.0: Sessao 128 (2026-11-16 11:45 -03) - AUDITORIA ETAPA 8a: gerar_senha_provisoria() sorteia com secrets (imprevisivel) em vez de random. Mesmo formato: 3 letras minusculas + 2 numeros. REVERSAO: .bak_antes_etapa8a.
# =========================================================

from werkzeug.security import check_password_hash, generate_password_hash

import secrets
import string


# -------------------------------------------------------
# Funcao: gerar_senha_provisoria
# Gera uma senha aleatoria de 5 caracteres: 3 letras
# minusculas + 2 numeros, embaralhados. Usada em todo ponto do
# sistema que precisa criar um acesso com senha provisoria
# (obriga troca no proximo login via campo senha_provisoria
# do model Usuario).
# -------------------------------------------------------
def gerar_senha_provisoria():
    caracteres = (
        [secrets.choice(string.ascii_lowercase) for _ in range(3)] +
        [secrets.choice(string.digits) for _ in range(2)]
    )
    secrets.SystemRandom().shuffle(caracteres)
    return ''.join(caracteres)


# -------------------------------------------------------
# Funcao: normalizar_login
# Tira os espacos do inicio e do fim do login digitado.
# (A comparacao sem diferenca de maiuscula e feita na consulta
# ao banco, com func.lower.)
# -------------------------------------------------------
def normalizar_login(login):
    return (login or '').strip()


# -------------------------------------------------------
# Funcao: gerar_hash_senha
# Grava a senha sempre em minusculo e sem espacos nas pontas
# (a senha nao diferencia maiuscula de minuscula). Use no lugar
# de generate_password_hash() ao salvar uma senha escolhida
# pelo usuario.
# -------------------------------------------------------
def gerar_hash_senha(senha):
    return generate_password_hash((senha or '').strip().lower())


# -------------------------------------------------------
# Funcao: conferir_senha
# Devolve (ok, novo_hash).
#   ok        = True se a senha confere: como digitada, sem os
#               espacos das pontas ou em minusculo sem espacos.
#   novo_hash = hash novo (minusculo, sem espacos) quando a senha
#               gravada ainda era de antes da regra e entrou
#               certa; o login regrava para a proxima vez valer
#               em qualquer caixa. None nos demais casos.
# -------------------------------------------------------
def conferir_senha(hash_gravado, senha_digitada):
    digitada = senha_digitada or ''
    padrao   = digitada.strip().lower()

    candidatas = []
    for c in (digitada, digitada.strip(), padrao):
        if c not in candidatas:
            candidatas.append(c)

    for c in candidatas:
        if check_password_hash(hash_gravado, c):
            if c != padrao:
                return True, generate_password_hash(padrao)
            return True, None

    return False, None

# =========================================================
# FIM DE ARQUIVO: backend\utils\senha_helper.py
# =========================================================
