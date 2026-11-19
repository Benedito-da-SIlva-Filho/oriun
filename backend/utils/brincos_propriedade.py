# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\brincos_propriedade.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-11-13 20:10 -03
# ATUALIZADO EM: 2026-11-13 20:10 -03
# VERSAO: 1.0.0
# v1.0.0: Sessao 123 (2026-11-13 20:10 -03) - AUDITORIA ETAPA 6 (leitura a fundo, itens 1/2/4): conferencia unica da Propriedade
#         nos relatorios de Brincos (Disponiveis, Saidas, Relatorio de NFs, Resumo) e tela de erro com norte (Regra #69).
#         Antes: so a trava "fazenda em uso mudou"; valor nao numerico dava erro 500 e Propriedade de outro cliente mostrava o cabecalho dela.
#         REVERSAO: apagar este arquivo e devolver os .bak_antes_etapa6e dos 4 relatorios.
#
# DESCRICAO:
#   propriedade_do_usuario_brincos(id) -> True so se o valor e numero (Regra #73), a Propriedade e do usuario
#   (par Propriedade/Produtor do Produtor logado) e coincide com a fazenda em uso (se houver).
#   tela_erro_brincos(msg) -> tela do Orion com a mensagem e o caminho de volta (Hub de Brincos).
# =========================================================

from flask import render_template, session

from backend.routers.auth import buscar_pares_propriedade_produtor, resolver_fazenda_em_uso

URL_HUB_BRINCOS = '/produtor/hub/brincos'
MSG_PROPRIEDADE_INVALIDA = (
    'Não encontramos esta Propriedade na sua conta. Volte ao Hub de Brincos e escolha a Propriedade de novo; '
    'se o problema repetir, avise a Consiste (usuário, tela, data e hora).'
)


def propriedade_do_usuario_brincos(id_propriedade):
    texto = str(id_propriedade or '').strip()
    if not texto.isdecimal() or len(texto) > 9:
        return False
    id_int = int(texto)
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and int(par_em_uso.id_propriedade) != id_int:
        return False
    return any(
        int(par.id_propriedade) == id_int and par.id_produtor == session.get('id_produtor')
        for par in pares
    )


def tela_erro_brincos(mensagem=MSG_PROPRIEDADE_INVALIDA):
    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=[],
        erro=mensagem,
        titulo='Selecionar Propriedade',
        proximo=URL_HUB_BRINCOS,
        campo_propriedade='id_propriedade',
        voltar=URL_HUB_BRINCOS,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )
