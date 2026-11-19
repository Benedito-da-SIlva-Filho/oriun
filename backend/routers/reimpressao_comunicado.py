# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\routers
# MODULO:       backend\routers\reimpressao_comunicado.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-09-16 10:25 -03
# ATUALIZADO EM: 2026-11-16 10:40 -03
# VERSAO: 1.7.0
# v1.7.0: Sessao 128 (2026-11-16 10:40 -03) - AUDITORIA ETAPA 7b (Regra #57/#73): a trava _propriedade_permitida() passa a conferir tambem que o Produtor do par Propriedade+Produtor e o Produtor da sessao (antes so conferia a Propriedade). REVERSAO: .bak_antes_etapa7b.
# v1.6.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (2 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Modulo "Reimpressao Comunicado" do Hub de Entrada - reimprime
#     o Anexo XIX de um Comunicado JA impresso, quantas vezes for
#     preciso.
#
#     ESCOPO: lista TODOS os Comunicados da Propriedade (qualquer
#     status - ABERTO tambem aparece aqui, mesmo UX do legado GERAS),
#     do MAIS RECENTE para o mais antigo (v1.2.0). NUNCA grava nada
#     no banco - so gera o PDF de novo. Quem grava status/data_envio
#     e o modulo Impressao (impressao_comunicado.py), na primeira vez.
#
#     Compartilha com a Impressao a montagem de PDF
#     (backend/utils/pdf_anexo_xix.py) e o agrupamento de linhas
#     (backend/utils/comunicado_display.py) - o PDF gerado aqui e
#     PIXEL IGUAL ao da Impressao original.
#
#     Fluxo de tela (Padrao Reutilizavel Nº1):
#         iniciar -> (selecao se 2+ pares Produtor/Propriedade) ->
#         listar (TODOS os Comunicados da Propriedade escolhida) ->
#         pdf (so gera, nunca grava)
#
#     v1.0.0: Criacao do modulo (Sessao 054).
#     v1.1.0: Sessao 054 (16/09/2026, 12:07 -03) - BUG REAL (P-036):
#             iniciar() contava PRODUTORES DISTINTOS em vez de PARES
#             Propriedade+Produtor. Corrigido para len(pares).
#     v1.2.0: Sessao 080 (25/09/2026, 09:10 -03) - Pedido de
#             Benedito + pendencia da Sessao 079:
#               - Lista em ordem DECRESCENTE (Comunicado mais recente
#                 no topo) - query com numero_comunicado DESC e
#                 agrupar_comunicados_por_numero(..., decrescente=
#                 True) (comunicado_display.py v1.1.0).
#               - SEGURANCA: listar() e pdf() conferem se a
#                 Propriedade da URL pertence ao usuario logado (NOVA
#                 funcao _propriedade_permitida(), mesmo padrao de
#                 impressao_comunicado.py v1.2.0).
#             Nenhuma outra mudanca (continua sem gravar nada).
#     v1.3.0: Sessao 090 (08/10/2026, 07:42 -03) - FAZENDA EM USO (Regra de Ouro
#             #13, Lote 2 - Comunicados). Tres pontos:
#               - iniciar(): com fazenda em uso valida (auth.
#                 resolver_fazenda_em_uso), PULA a tela "Selecionar
#                 Propriedade" e abre a Lista direto na fazenda em uso. Sem
#                 fazenda em uso, ou com uma fazenda so, tudo igual a antes.
#               - VOLTAR: passa a ir para o Hub novo "Comunicados de Entrada"
#                 (caminho inverso do de ida). O router informa o destino ao
#                 template pela variavel url_voltar (antes o template tinha o
#                 Voltar fixo no iniciar(), o que com fazenda em uso reabriria
#                 a tela: laco). Sem fazenda em uso, o Voltar vai para a selecao
#                 como antes.
#               - TRAVA (_propriedade_permitida): se a Propriedade da URL for
#                 DIFERENTE da fazenda em uso (ex.: trocada em outra aba), a
#                 rota nao le, nao gera e nao grava nada e manda para o
#                 iniciar(), que abre a fazenda em uso.
#             Nenhuma mudanca em regras de negocio, PDFs, numeracao e gravacao.
#     v1.4.0: Sessao 091 (08/10/2026, 20:45 -03) - SO OS IMPRESSOS (decisao de Benedito:
#             o usuario imprimia o ABERTO por aqui e o sistema nao registrava).
#             A lista mostra apenas comunicados IMPRESSOS, com "Impresso em"
#             (data e hora) e "Por" (usuario). Comunicado ABERTO so aparece e
#             so imprime na Impressao Comunicado. Continua sem gravar nada.
#             Comunicados impressos antes desta versao mostram so a data.
#     v1.5.0: Sessao 095 (13/10/2026, 11:27 -03) - PADRAO DE DOWNLOAD: o PDF passa a ser entregue como DOWNLOAD (pasta Downloads do usuario)
#             e nao mais aberto direto na aba, igual aos demais relatorios do Orion (decisao de Benedito).
#             A tela avisa onde o arquivo fica. Unica mudanca: as_attachment=True.
#             REVERSAO: devolver .bak_antes_download_s095.
# =========================================================

from flask import Blueprint, redirect, render_template, request, send_file, session
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Produtor, Propriedade, Usuario
from backend.models.tb_2012_com_entrada import ComunicadoEntrada
from backend.routers.auth import buscar_pares_propriedade_produtor, redirecionar_home, resolver_fazenda_em_uso
from backend.utils.comunicado_display import agrupar_comunicados_por_numero, montar_contexto_anexo_xix
from backend.utils.multitenant import get_db_produtor
from backend.utils.pdf_anexo_xix import gerar_pdf_anexo_xix


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
reimpressao_comunicado = Blueprint('reimpressao_comunicado', __name__)


# -------------------------------------------------------
# Funcao auxiliar (NOVA, v1.2.0): a Propriedade pertence aos
# pares Propriedade/Produtor do usuario logado?
# -------------------------------------------------------
# -------------------------------------------------------
# Constantes de navegacao (v1.2.0 / Sessao 090 - Lote 2).
# VOLTAR_HUB: o Hub onde mora o card deste modulo (caminho inverso do de
# ida: Hub de Entrada > Gerar Comunicados > Comunicados de Entrada).
# -------------------------------------------------------
VOLTAR_HUB = '/produtor/hub-novo/entrada-comunicados'
URL_INICIAR = '/produtor/reimpressao-comunicado/iniciar'


# -------------------------------------------------------
# Trava de permissao (usada por TODAS as rotas do modulo).
# 1) a Propriedade tem de ser de um par do usuario logado;
# 2) FAZENDA EM USO (Sessao 090): se ha uma e ela e DIFERENTE da Propriedade
#    da URL (trocada em outra aba, por exemplo), devolve False - o chamador
#    manda para o iniciar(), que abre a fazenda em uso. Nada e lido, gerado
#    nem gravado numa fazenda enquanto a faixa mostra outra.
# -------------------------------------------------------
def _mapa_usuarios(ids_usuario):
    if not ids_usuario:
        return {}
    with Session(engine) as dbp:
        return {u.id: u.nome for u in dbp.query(Usuario).filter(Usuario.id.in_(ids_usuario)).all()}


def _propriedade_permitida(id_propriedade):
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if int(id_propriedade) not in {int(par.id_propriedade) for par in pares if str(par.id_produtor) == str(session.get('id_produtor'))}:   # v1.7.0 - Produtor do par = Produtor da sessao (Etapa 7b)
        return False
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and int(par_em_uso.id_propriedade) != int(id_propriedade):
        return False
    return True


# -------------------------------------------------------
# Destino do botao Voltar (Regra de Ouro #9). Com fazenda em uso a selecao
# e pulada - volta direto ao Hub (voltar ao iniciar() reabriria a tela: laco).
# So volta para a selecao quem tem 2+ pares e nenhuma fazenda em uso.
# -------------------------------------------------------
def _url_voltar(pares):
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return URL_INICIAR
    return VOLTAR_HUB


# -------------------------------------------------------
# Rota: GET /produtor/reimpressao-comunicado/iniciar
# Padrao Reutilizavel Nº1 - Selecionar Propriedade/Produtor.
# -------------------------------------------------------
@reimpressao_comunicado.route('/produtor/reimpressao-comunicado/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            titulo='Reimpressão Comunicado — Selecionar Propriedade',
            proximo='/produtor/reimpressao-comunicado/listar',
            campo_propriedade='id_propriedade',
            voltar='/produtor/hub/entrada',
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='entrada',
        )

    # FAZENDA EM USO (Sessao 090): ja escolhida no Home novo (conferida contra os
    # pares do usuario) - pula a tela de selecao e abre a tela direto.
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/reimpressao-comunicado/listar?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/reimpressao-comunicado/listar?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        titulo='Reimpressão Comunicado — Selecionar Propriedade',
        proximo='/produtor/reimpressao-comunicado/listar',
        campo_propriedade='id_propriedade',
        voltar='/produtor/hub/entrada',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/reimpressao-comunicado/listar?id_propriedade=X
# Lista TODOS os Comunicados da Propriedade (qualquer status), do
# mais recente para o mais antigo (v1.2.0).
# -------------------------------------------------------
@reimpressao_comunicado.route('/produtor/reimpressao-comunicado/listar')
def listar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade.isdecimal() or not _propriedade_permitida(id_propriedade):
        return redirect('/produtor/reimpressao-comunicado/iniciar')
    id_propriedade = int(id_propriedade)

    with get_db_produtor(session['id_produtor']) as db:
        propriedade = db.get(Propriedade, id_propriedade)
        if not propriedade:
            return redirect('/produtor/reimpressao-comunicado/iniciar')

        # v1.4.0 - so os JA IMPRESSOS: o ABERTO so aparece (e so imprime) na
        # Impressao Comunicado, que e quem registra data, hora e usuario.
        todas_as_linhas = (
            db.query(ComunicadoEntrada)
            .filter(
                ComunicadoEntrada.id_propriedade_destino == id_propriedade,
                ComunicadoEntrada.status == 'IMPRESSO',
            )
            .order_by(ComunicadoEntrada.numero_comunicado.desc(), ComunicadoEntrada.gta_data_emissao.asc())
            .all()
        )

        # v1.2.0 - mais recente no topo.
        comunicados = agrupar_comunicados_por_numero(todas_as_linhas, decrescente=True, db=db)

        # v1.4.0 - "Impresso em" (data e hora; so a data nos antigos) e "Por".
        nomes = _mapa_usuarios([c['id_usuario_impressao'] for c in comunicados if c['id_usuario_impressao']])
        for c in comunicados:
            if c['impresso_em']:
                c['impresso_texto'] = c['impresso_em'].strftime('%d/%m/%Y %H:%M')
            elif c['data_envio']:
                c['impresso_texto'] = c['data_envio'].strftime('%d/%m/%Y')
            else:
                c['impresso_texto'] = '-'
            c['impresso_por'] = nomes.get(c['id_usuario_impressao'], '-') if c['id_usuario_impressao'] else '-'

        return render_template(
            'produtor/reimpressao_comunicado_listar.html',
            propriedade=propriedade,
            id_propriedade=id_propriedade,
            comunicados=comunicados,
            url_voltar=_url_voltar(buscar_pares_propriedade_produtor(session['usuario_id'])),   # Sessao 090
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='entrada',
        )


# -------------------------------------------------------
# Rota: GET /produtor/reimpressao-comunicado/pdf/<numero_comunicado>
# So gera e devolve o PDF - NUNCA grava status/data_envio.
# -------------------------------------------------------
@reimpressao_comunicado.route('/produtor/reimpressao-comunicado/pdf/<int:numero_comunicado>')
def pdf(numero_comunicado):
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade.isdecimal() or not _propriedade_permitida(id_propriedade):
        return redirect('/produtor/reimpressao-comunicado/iniciar')
    id_propriedade = int(id_propriedade)

    eh_transfer = request.args.get('tipo') == 'TRANSFER'

    with get_db_produtor(session['id_produtor']) as db:
        linhas = (
            db.query(ComunicadoEntrada)
            .filter(
                ComunicadoEntrada.id_propriedade_destino == id_propriedade,
                ComunicadoEntrada.numero_comunicado == numero_comunicado,
                (ComunicadoEntrada.tipo_entrada == 'TRANSFERENCIA') if eh_transfer else (ComunicadoEntrada.tipo_entrada != 'TRANSFERENCIA'),
            )
            .order_by(ComunicadoEntrada.gta_data_emissao.asc(), ComunicadoEntrada.id.asc())
            .all()
        )

        if not linhas:
            return redirect(f'/produtor/reimpressao-comunicado/listar?id_propriedade={id_propriedade}')

        produtor_destino = db.get(Produtor, session['id_produtor'])
        contexto = montar_contexto_anexo_xix(db, linhas, produtor_destino)
        buffer = gerar_pdf_anexo_xix(contexto)

    nome_arquivo = f"comunicado{'_transfer' if eh_transfer else ''}_{numero_comunicado:06d}_anexo_xix.pdf"
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)

# =========================================================
# FIM DE ARQUIVO: backend\routers\reimpressao_comunicado.py
# =========================================================