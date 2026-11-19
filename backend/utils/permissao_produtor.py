# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\permissao_produtor.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-06 16:01 -03
# ATUALIZADO EM: 2026-11-12 17:40 -03
# VERSAO: 1.1.0
# v1.1.0: Sessao 122 (2026-11-12 17:40 -03) - Auditoria Etapa 2 (item 3): nova funcao pode_alterar_certificacao() - Titular, Administrador e Administrativo (e a Consiste) alteram Codigo ERAS, OESA e Protocolos. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Quem pode CADASTRAR / VINCULAR um Produtor novo a uma Propriedade:
#     so o Titular e o Administrador (decisao do Benedito, 05/11/2026).
#     Perfil CONSISTE pode sempre. Usada pela tela Minha Propriedade,
#     pelo cadastro de Produtor (/produtores/novo e /produtores/salvar)
#     e pela DTA da Alteracao de Posse.
#
#     v1.0.0: Criacao (Sessao 116). REVERSAO: apagar o arquivo e
#             restaurar os .bak_antes_s116_addprodutor.
# =========================================================

from flask import session

CARGOS_CADASTRAR_PRODUTOR = ('TITULAR', 'ADMINISTRADOR')
MSG_SO_TITULAR_ADMIN = 'Só o Titular ou o Administrador pode cadastrar um Produtor novo. Peça a um deles.'

# Etapa 2 (item 3): quem pode alterar Codigo ERAS, OESA e Protocolos da Propriedade.
CARGOS_ALTERAR_CERTIFICACAO = ('TITULAR', 'ADMINISTRADOR', 'ADMINISTRATIVO')
MSG_SO_CARGOS_CERTIFICACAO = 'Código ERAS, OESA e Protocolos só podem ser alterados pelo Titular, Administrador ou Administrativo. Peça a um deles.'


def pode_alterar_certificacao(id_propriedade):
    perfil = session.get('usuario_perfil')
    if perfil == 'CONSISTE':
        return True
    if perfil != 'PRODUTOR' or 'usuario_id' not in session:
        return False
    try:
        id_prop = int(id_propriedade)
    except (TypeError, ValueError):
        return False
    from backend.routers.auth import buscar_pares_propriedade_produtor   # import tardio: evita circular
    for par in buscar_pares_propriedade_produtor(session['usuario_id']):
        if int(par.id_propriedade) == id_prop and (par.cargo or '').strip().upper() in CARGOS_ALTERAR_CERTIFICACAO:
            return True
    return False


# -------------------------------------------------------
# Funcao: pode_cadastrar_produtor(id_propriedade)
# True se o usuario logado e CONSISTE, ou PRODUTOR com cargo
# Titular/Administrador NESTA Propriedade.
# -------------------------------------------------------
def pode_cadastrar_produtor(id_propriedade):
    perfil = session.get('usuario_perfil')
    if perfil == 'CONSISTE':
        return True
    if perfil != 'PRODUTOR' or 'usuario_id' not in session:
        return False
    try:
        id_prop = int(id_propriedade)
    except (TypeError, ValueError):
        return False
    from backend.routers.auth import buscar_pares_propriedade_produtor   # import tardio: evita circular
    for par in buscar_pares_propriedade_produtor(session['usuario_id']):
        if int(par.id_propriedade) == id_prop and (par.cargo or '').strip().upper() in CARGOS_CADASTRAR_PRODUTOR:
            return True
    return False

# =========================================================
# FIM DE ARQUIVO: backend\utils\permissao_produtor.py
# =========================================================
