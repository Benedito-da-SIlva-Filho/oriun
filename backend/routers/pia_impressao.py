# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\pia_impressao.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-25 10:55 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.6.0
# v1.6.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (4 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.5.0: Sessao 123 (2026-11-13 19:25 -03) - AUDITORIA ETAPA 4 (2a passada): a quantidade do erro 'fabricante' vinda da URL so aparece se for numero. REVERSAO: .bak_antes_etapa4b.
#
# DESCRICAO:
#     Modulo PIA - impressao do Anexo XXIII (Formulario para
#     Planilha de Identificacao Individual de Animais) a partir
#     da tb_7002_pia (gravada pela Brincagem Sequencial e pelo
#     Vincular GTA). Navegacao real (Regra de Ouro #7): Hub de
#     Entrada -> card "PIA" (hubs.py v1.34.0) -> Selecionar
#     Propriedade (Padrao Reutilizavel N.1, so com 2+ pares) ->
#     TELA UNICA com 3 ABAS (v1.1.0).
#
#     3 MODOS = 3 ABAS da mesma tela (os mesmos do legado GERAS -
#     PIA.docx, Sessao 080):
#       1. POR PERIODO   - Data Inicial/Final da Identificacao
#          (data_identificacao = Data de Brincagem).
#       2. POR MANEJO    - Manejo Inicial/Final (6 digitos). A
#          tela mostra, ao vivo, o SISBOV de cada ponta (rota
#          manejo_previa) e AVISA se a faixa pegar mais de uma
#          SERIE (os 9 primeiros digitos do SISBOV) - o manejo
#          sozinho nao e unico entre series (decisao de Benedito).
#       3. POR COMUNICADO - lista dos Comunicados de Entrada em
#          ordem DECRESCENTE (mesma funcao da Reimpressao,
#          comunicado_display.py v1.1.0); clique = PIA das GTAs
#          daquele Comunicado.
#
#     FABRICANTE (cabecalho do documento): PIA -> SISBOV ->
#     tb_7017 (mesma Propriedade; linha consumida, status
#     'ENTRADA', tem prioridade) -> lote tb_3007 -> id_fabricante
#     -> tb_1021 (schema public). UMA PIA POR FABRICANTE (cada
#     grupo em pagina nova, 1 arquivo so - decisao de Benedito).
#
#     ERRO GRAVE (decisao de Benedito, Sessao 080 - "os brincos
#     estao na nossa base, tem que sair dali"): animal cujo brinco
#     nao leva a um lote/fabricante BLOQUEIA o PDF - a tela lista
#     os SISBOVs com a orientacao "avise a Consiste". A PIA e
#     documento oficial: nunca sai com cabecalho incompleto.
#
#     SEGURANCA: toda rota confere se a Propriedade da URL
#     pertence aos pares do usuario logado (_pares_se_permitido).
#     So leitura - este modulo NUNCA grava no banco.
#
#     v1.0.0: Criacao do modulo (Sessao 080, 25/09/2026, 10:55 -03).
#     v1.1.0: Sessao 080 (25/09/2026, 15:20 -03) - TELA UNICA
#         (sugestao de Benedito, aceita): os 3 modos deixaram de
#         ser 3 cards de um sub-hub e viraram ABAS de uma so tela
#         (template pia.html, que substitui pia_filtro.html e
#         pia_comunicado.html). Mudancas:
#           - UMA rota iniciar() e UMA rota tela() (parametro
#             'aba': periodo/manejo/comunicado) - substituem as 3
#             rotas *_iniciar e as 3 rotas *_tela da v1.0.0.
#           - _renderizar() sempre usa pia.html, ja com a lista de
#             Comunicados carregada (aba Comunicado pronta sem
#             recarregar) e a aba ativa.
#           - Voltar: Selecionar Propriedade (2+ pares) ou Hub de
#             Entrada (1 par) - o sub-hub nao existe mais.
#           - Rotas de PDF e a previa do Manejo: SEM mudanca.
#     v1.1.1: Sessao 080 (25/09/2026, 15:50 -03) - Aba Por
#         Comunicado passa o numero do Comunicado para o PDF
#         (caixa "000002" no canto superior direito - pdf_pia.py
#         v1.1.0, igual ao legado). _gerar() ganha o parametro
#         opcional numero_pia. Abas Periodo/Manejo: sem numero.
#     v1.2.0: Sessao 084 (02/10/2026, 16:00 -03) - PLANILHA PIA DE NASCIMENTOS
#         (card "Planilha de Nascimento [PIA]" do sub-hub 'entrada-
#         nascimento', hubs.py v1.38.0). 3 rotas novas, mesmo PDF (pdf_pia.py)
#         e mesma montagem por Fabricante das abas existentes:
#           - nascimento_iniciar(): Padrao Reutilizavel N.1;
#           - nascimento_lista(): Notificacoes NAS da Propriedade (mais nova
#             primeiro) com a quantidade de animais da PIA e a situacao da
#             conferencia no brete;
#           - nascimento_pdf(<id_gta>): PIA daquela Notificacao (tb_7002 pelo
#             id_gta; a caixa do numero leva o numero do NAS). So sai com TODOS
#             os brincos conferidos no brete; mesmo ERRO GRAVE do Fabricante.
#             So leitura - nunca grava. Reimprime quantas vezes precisar.
#         As 3 abas (Periodo/Manejo/Comunicado) SEM mudanca.
#     v1.3.0: Sessao 090 (08/10/2026, 07:29 -03) - FAZENDA EM USO (Regra de Ouro
#         #13, Lote 1 - Nascimento). Vale para as DUAS entradas do modulo
#         (iniciar da PIA geral e nascimento_iniciar da PIA de Nascimento):
#           - iniciar() / nascimento_iniciar(): com fazenda em uso valida
#             (auth.resolver_fazenda_em_uso), PULAM a tela "Selecionar
#             Propriedade" e abrem a tela direto na fazenda em uso. Sem fazenda
#             em uso, ou com uma fazenda so, tudo igual a antes.
#           - VOLTAR (caminho inverso do de ida, Regra de Ouro #9): a PIA geral
#             volta para o Hub "Comunicados de Entrada" (onde mora o card); a
#             PIA de Nascimento volta para o Hub "Nascimento / Desmame". Com
#             fazenda em uso a selecao nao existe mais, entao nunca volta ao
#             iniciar() (reabriria a tela: laco).
#           - TRAVA (_pares_se_permitido): se a Propriedade da URL for DIFERENTE
#             da fazenda em uso (ex.: trocada em outra aba), a rota nao le nem
#             imprime nada e manda para o iniciar() do proprio modulo (que abre
#             a fazenda em uso) - nova funcao _negado().
#         Nenhuma mudanca nas abas, na montagem da PIA e nos PDFs.
#     v1.4.0: Sessao 101 (20/10/2026, 20:30 -03) - PDF no visual do Magic (pdf_pia.py 2.0.0). Aqui:
#         - _dados_propriedade() passa tambem 'cpf' e 'cnpj' (regra por fazenda: documentos_do_produtor +
#           vinculo Produtor x Propriedade); 'cpf_cnpj' continua para a tela.
#         - _animal_pia() passa 'nascimento_data' (data completa, usada no Anexo IX).
#         - PIA de NASCIMENTO sai no modelo 'IX' (Anexo IX, sem caixa de numero); as 3 abas da PIA geral
#           continuam no 'XXIII'. Rotas, travas e filtros SEM mudanca. REVERSAO: .bak_antes_geras_s101
# =========================================================

from datetime import datetime

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, Produtor
from backend.models.propriedade_produtor import PropriedadeProdutor
from backend.models.tb_1021_fabricantes_brincos import Fabricante
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2012_com_entrada import ComunicadoEntrada
from backend.models.tb_4001_gta import Gta
from backend.models.tb_3007_brincos_entrada import BrincoEntrada
from backend.models.tb_7002_pia import Pia
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.comunicado_display import agrupar_comunicados_por_numero
from backend.utils.multitenant import get_db_produtor
from backend.utils.documentos_produtor import documentos_do_produtor
from backend.utils.pdf_pia import gerar_pdf_pia


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
pia_impressao = Blueprint('pia_impressao', __name__)


@pia_impressao.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


MENU_ATIVO = 'entrada'
VOLTAR_HUB = '/produtor/hub-novo/entrada-comunicados'   # v1.3.0 - Hub "Comunicados de Entrada" (onde mora o card da PIA)
VOLTAR_SELECAO = '/produtor/pia/iniciar'

# v1.2.0 - PIA de Nascimento
VOLTAR_SUBHUB_NASCIMENTO = '/produtor/hub-novo/entrada-nascimento'   # v1.3.0 - Hub novo Nascimento / Desmame
VOLTAR_SELECAO_NASCIMENTO = '/produtor/pia/nascimento/iniciar'
TITULO_NASCIMENTO = 'Planilha de Nascimento [PIA]'
ERROS_NASCIMENTO = {
    'pendente': 'Esta Notificação ainda tem brincos a conferir no brete. Confira todos antes de imprimir a PIA.',
    'sem_pia': 'Nenhum animal encontrado na PIA desta Notificação.',
    'inexistente': 'Notificação não encontrada.',
}

ABAS = ('periodo', 'manejo', 'comunicado')
TITULO_TELA = 'Planilha de Identificação Individual (PIA)'

TAMANHO_MANEJO = 6
TAMANHO_SERIE = 9          # 9 primeiros digitos do SISBOV = serie
LIMITE_SISBOVS_ERRO = 30   # SISBOVs listados na tela de erro
TAMANHO_LOTE_IN = 900      # consultas IN(...) em lotes


# =======================================================
# BLOCO 1 - Auxiliares de permissao, tela e dados
# =======================================================

def _pares_se_permitido(id_propriedade):
    if not str(id_propriedade).isdecimal():
        return None
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if str(id_propriedade) not in {str(par.id_propriedade) for par in pares}:
        return None
    # v1.3.0 - TRAVA: se ha fazenda em uso e ela e DIFERENTE da Propriedade da
    # URL (trocada em outra aba, por exemplo), nao ha permissao - nada e lido
    # nem impresso numa fazenda enquanto a faixa mostra outra.
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and str(par_em_uso.id_propriedade) != str(id_propriedade):
        return None
    return pares


# -------------------------------------------------------
# v1.3.0 - Para onde mandar quando _abrir() recusa. Se a recusa foi a TRAVA
# (Propriedade da URL e do usuario, mas diferente da fazenda em uso), vai para
# o iniciar() do modulo, que abre a fazenda em uso. Qualquer outra recusa
# (Propriedade que nao e dele, sessao) segue como antes: Home. So manda ao
# iniciar() no caso da trava (la a fazenda em uso e outra), por isso nao ha laco.
# -------------------------------------------------------
def _negado(id_propriedade, url_iniciar):
    if str(id_propriedade).isdecimal():
        pares = buscar_pares_propriedade_produtor(session['usuario_id'])
        par_em_uso = resolver_fazenda_em_uso(pares)
        dono = str(id_propriedade) in {str(par.id_propriedade) for par in pares}
        if dono and par_em_uso is not None and str(par_em_uso.id_propriedade) != str(id_propriedade):
            return redirect(url_iniciar)
    return redirecionar_home()


# -------------------------------------------------------
# Destino do Voltar da PIA geral (Regra de Ouro #9). v1.3.0: com fazenda em
# uso a selecao e pulada - volta direto ao Hub (voltar ao iniciar() reabriria
# a tela: laco).
# -------------------------------------------------------
def _url_voltar(pares):
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return VOLTAR_SELECAO
    return VOLTAR_HUB


def _dados_propriedade(id_propriedade):
    """Dados da Propriedade + Produtor (tela e bloco do PDF),
    copiados para dict DENTRO da sessao do banco."""
    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
        produtor = db.get(Produtor, session['id_produtor'])
        if not propriedade:
            return None

        partes_endereco = [p for p in (propriedade.logradouro, propriedade.numero) if p]
        endereco = ', '.join(partes_endereco)
        if propriedade.bairro:
            endereco = f'{endereco} - {propriedade.bairro}' if endereco else propriedade.bairro

        vinculo = None
        if produtor is not None:
            vinculo = (
                db.query(PropriedadeProdutor)
                .filter_by(id_propriedade=int(id_propriedade), id_produtor=produtor.id, data_fim=None)
                .first()
            )
        cpf, cnpj = documentos_do_produtor(produtor, vinculo)   # v1.4.0 - principal + secundario DESTA fazenda

        return {
            'nome':        produtor.nome if produtor else None,
            'cpf_cnpj':    produtor.cpf_cnpj if produtor else None,
            'cpf':         cpf,
            'cnpj':        cnpj,
            'codigo_eras': propriedade.codigo_eras,
            'propriedade': propriedade.nome,
            'endereco':    endereco,
            'cidade':      f'{propriedade.municipio} / {propriedade.uf}',
            'cep':         propriedade.cep,
        }


def _renderizar(modo, id_propriedade, pares, dados, **extra):
    """v1.1.0: tela unica (pia.html) - 'modo' = aba ativa. A lista
    de Comunicados vem sempre carregada."""
    comunicados = extra.get('comunicados')
    if comunicados is None:
        comunicados = _listar_comunicados(id_propriedade)
    return render_template(
        'produtor/pia.html',
        aba=modo if modo in ABAS else 'periodo',
        titulo=TITULO_TELA,
        id_propriedade=id_propriedade,
        dados=dados,
        erro=extra.get('erro'),
        sisbovs_erro=extra.get('sisbovs_erro') or [],
        qtde_extra_erro=extra.get('qtde_extra_erro', 0),
        valores=extra.get('valores') or {},
        comunicados=comunicados,
        url_voltar=_url_voltar(pares),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo=MENU_ATIVO,
    )


@pia_impressao.route('/produtor/pia/iniciar')
def iniciar():
    """Padrao Reutilizavel N.1 - com 1 unico par, pula direto."""
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    # v1.3.0 - FAZENDA EM USO: pula a tela de selecao e abre a PIA direto.
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/pia?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/pia?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None if pares else 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
        titulo='PIA — Selecionar Propriedade',
        proximo='/produtor/pia',
        campo_propriedade='id_propriedade',
        voltar=VOLTAR_HUB,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo=MENU_ATIVO,
    )


@pia_impressao.route('/produtor/pia')
def tela():
    """v1.1.0: tela unica com as 3 abas (?aba= opcional)."""
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    pares, dados = _abrir(id_propriedade)
    if not pares:
        return _negado(id_propriedade, VOLTAR_SELECAO)   # v1.3.0 - trava: fazenda em uso e outra
    return _renderizar(request.args.get('aba', 'periodo'), id_propriedade, pares, dados)


def _abrir(id_propriedade):
    """Confere sessao/permissao e carrega os dados. Devolve
    (pares, dados) ou (None, None)."""
    pares = _pares_se_permitido(id_propriedade)
    if not pares:
        return None, None
    dados = _dados_propriedade(id_propriedade)
    if not dados:
        return None, None
    return pares, dados


# =======================================================
# BLOCO 2 - Montagem da PIA (comum aos 3 modos)
# =======================================================

def _em_lotes(lista):
    for i in range(0, len(lista), TAMANHO_LOTE_IN):
        yield lista[i:i + TAMANHO_LOTE_IN]


def _animal_pia(p):
    return {
        'sisbov':             p.sisbov,
        'manejo':             p.manejo,
        'nascimento_mes_ano': p.nascimento.strftime('%m/%Y') if p.nascimento else '',
        'nascimento_data':    p.nascimento.strftime('%d/%m/%Y') if p.nascimento else '',
        'idade_meses':        '' if p.idade_meses is None else str(p.idade_meses),
        'sexo':               p.sexo,
        'raca_codigo':        p.raca_codigo,
        'motivo':             p.motivo,
        'data_identificacao': p.data_identificacao.strftime('%d/%m/%Y') if p.data_identificacao else '',
    }


def _montar_grupos(db, id_propriedade, pias):
    """Separa os animais por Fabricante. Devolve (grupos,
    sisbovs_sem_fabricante). 'pias' ja vem ordenada por SISBOV."""
    sisbovs = sorted({p.sisbov for p in pias})

    # ---- SISBOV -> lote (tb_7017; linha consumida tem prioridade) ----
    lote_por_sisbov = {}
    for pedaco in _em_lotes(sisbovs):
        linhas = (
            db.query(EntradaBrincoRfid)
            .filter(EntradaBrincoRfid.id_propriedade == int(id_propriedade),
                    EntradaBrincoRfid.sisbov.in_(pedaco))
            .all()
        )
        for linha in linhas:
            atual = lote_por_sisbov.get(linha.sisbov)
            prioridade = 2 if linha.status == 'ENTRADA' else (1 if linha.saida_gta else 0)
            if atual is None or prioridade > atual[1]:
                lote_por_sisbov[linha.sisbov] = (linha.id_lote_entrada, prioridade)

    # ---- lote -> fabricante (tb_3007) ----
    ids_lotes = sorted({v[0] for v in lote_por_sisbov.values() if v[0]})
    fabricante_por_lote = {}
    for pedaco in _em_lotes(ids_lotes):
        for lote in db.query(BrincoEntrada).filter(BrincoEntrada.id.in_(pedaco)).all():
            fabricante_por_lote[lote.id] = lote.id_fabricante

    # ---- fabricantes (tb_1021, schema public) ----
    ids_fabricantes = sorted({f for f in fabricante_por_lote.values() if f})
    fabricantes = {}
    if ids_fabricantes:
        with Session(engine) as db_public:
            for f in db_public.query(Fabricante).filter(Fabricante.id.in_(ids_fabricantes)).all():
                fabricantes[f.id] = {
                    'nome': f.nome, 'logo': f.logo, 'endereco': f.endereco,
                    'complemento': f.complemento, 'bairro': f.bairro,
                    'cidade': f.cidade, 'uf': f.uf, 'cep': f.cep,
                }

    # ---- agrupa ----
    por_fabricante = {}
    sem_fabricante = []
    for p in pias:
        lote = lote_por_sisbov.get(p.sisbov, (None, 0))[0]
        id_fab = fabricante_por_lote.get(lote)
        if id_fab not in fabricantes:
            sem_fabricante.append(p.sisbov)
            continue
        por_fabricante.setdefault(id_fab, []).append(_animal_pia(p))

    grupos = [
        {'fabricante': fabricantes[id_fab], 'animais': animais}
        for id_fab, animais in sorted(por_fabricante.items(), key=lambda kv: fabricantes[kv[0]]['nome'] or '')
    ]
    return grupos, sem_fabricante


def _gerar(modo, id_propriedade, pares, dados, filtros, sufixo, valores, extra_tela=None, numero_pia=None):
    """Le a PIA com os filtros, confere o ERRO GRAVE e gera o PDF
    (ou volta para a tela com a mensagem)."""
    # Tudo lido e montado DENTRO da sessao; a tela de erro (que
    # abre outra sessao para a lista de Comunicados) so e montada
    # depois de fechar esta.
    with get_db_produtor(session['id_produtor']) as db:
        pias = (
            db.query(Pia)
            .filter(Pia.id_propriedade == int(id_propriedade), *filtros)
            .order_by(Pia.sisbov)
            .all()
        )
        if pias:
            grupos, sem_fabricante = _montar_grupos(db, id_propriedade, pias)

    if not pias:
        return _renderizar(modo, id_propriedade, pares, dados, valores=valores,
                           erro='Nenhum animal encontrado na PIA para o filtro informado.',
                           **(extra_tela or {}))

    if sem_fabricante:
        return _renderizar(
            modo, id_propriedade, pares, dados, valores=valores,
            erro=(f'ERRO GRAVE — PIA não gerada: {len(sem_fabricante)} brinco(s) sem lote de origem '
                  f'no estoque (fabricante não identificado). Avise a Consiste.'),
            sisbovs_erro=sem_fabricante[:LIMITE_SISBOVS_ERRO],
            qtde_extra_erro=max(len(sem_fabricante) - LIMITE_SISBOVS_ERRO, 0),
            **(extra_tela or {}),
        )

    return gerar_pdf_pia(grupos, dados, sufixo, numero_pia)


def _normalizar_manejo(texto):
    digitos = ''.join(c for c in (texto or '') if c.isdecimal())
    if not digitos or len(digitos) > TAMANHO_MANEJO:
        return None
    return digitos.zfill(TAMANHO_MANEJO)


# =======================================================
# BLOCO 3 - Aba 1: POR PERIODO (PDF)
# =======================================================

@pia_impressao.route('/produtor/pia/periodo/pdf')
def periodo_pdf():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    pares, dados = _abrir(id_propriedade)
    if not pares:
        return _negado(id_propriedade, VOLTAR_SELECAO)   # v1.3.0 - trava: fazenda em uso e outra

    texto_inicial = request.args.get('data_inicial', '').strip()
    texto_final = request.args.get('data_final', '').strip()
    valores = {'data_inicial': texto_inicial, 'data_final': texto_final}

    try:
        data_inicial = datetime.strptime(texto_inicial, '%d/%m/%Y').date()
        data_final = datetime.strptime(texto_final, '%d/%m/%Y').date()
    except ValueError:
        return _renderizar('periodo', id_propriedade, pares, dados, valores=valores,
                           erro='Data incorreta! Use o formato dd/mm/aaaa nas duas datas.')
    if data_inicial > data_final:
        return _renderizar('periodo', id_propriedade, pares, dados, valores=valores,
                           erro='A Data Inicial não pode ser posterior à Data Final.')

    filtros = [Pia.data_identificacao >= data_inicial, Pia.data_identificacao <= data_final]
    sufixo = f'{data_inicial.strftime("%d-%m-%Y")}_a_{data_final.strftime("%d-%m-%Y")}'
    return _gerar('periodo', id_propriedade, pares, dados, filtros, sufixo, valores)


# =======================================================
# BLOCO 4 - Aba 2: POR MANEJO (previa + PDF)
# =======================================================

@pia_impressao.route('/produtor/pia/manejo/previa')
def manejo_previa():
    """AJAX: SISBOV(s) de cada ponta da faixa, quantidade e
    quantas series a faixa pega (aviso de Benedito)."""
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    id_propriedade = request.args.get('id_propriedade', '')
    if not _pares_se_permitido(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403

    inicial = _normalizar_manejo(request.args.get('manejo_inicial'))
    final = _normalizar_manejo(request.args.get('manejo_final'))
    resposta = {'sisbov_inicial': [], 'sisbov_final': [], 'qtde': 0, 'series': 0}

    with get_db_produtor(session['id_produtor']) as db:
        base = db.query(Pia.sisbov, Pia.manejo).filter(Pia.id_propriedade == int(id_propriedade))
        if inicial:
            resposta['sisbov_inicial'] = sorted({s for s, _ in base.filter(Pia.manejo == inicial).all()})
        if final:
            resposta['sisbov_final'] = sorted({s for s, _ in base.filter(Pia.manejo == final).all()})
        if inicial and final and inicial <= final:
            faixa = base.filter(Pia.manejo >= inicial, Pia.manejo <= final).all()
            resposta['qtde'] = len(faixa)
            resposta['series'] = len({s[:TAMANHO_SERIE] for s, _ in faixa})

    return jsonify(resposta)


@pia_impressao.route('/produtor/pia/manejo/pdf')
def manejo_pdf():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    pares, dados = _abrir(id_propriedade)
    if not pares:
        return _negado(id_propriedade, VOLTAR_SELECAO)   # v1.3.0 - trava: fazenda em uso e outra

    valores = {
        'manejo_inicial': request.args.get('manejo_inicial', '').strip(),
        'manejo_final': request.args.get('manejo_final', '').strip(),
    }
    inicial = _normalizar_manejo(valores['manejo_inicial'])
    final = _normalizar_manejo(valores['manejo_final'])
    if not inicial or not final:
        return _renderizar('manejo', id_propriedade, pares, dados, valores=valores,
                           erro=f'Manejo incorreto! Informe até {TAMANHO_MANEJO} dígitos nos dois campos.')
    if inicial > final:
        return _renderizar('manejo', id_propriedade, pares, dados, valores=valores,
                           erro='O Manejo Inicial não pode ser maior que o Manejo Final.')

    filtros = [Pia.manejo >= inicial, Pia.manejo <= final]
    return _gerar('manejo', id_propriedade, pares, dados, filtros, f'manejo_{inicial}_a_{final}', valores)


# =======================================================
# BLOCO 5 - Aba 3: POR COMUNICADO (lista + PDF)
# =======================================================

def _listar_comunicados(id_propriedade):
    with get_db_produtor(session['id_produtor']) as db:
        linhas = (
            db.query(ComunicadoEntrada)
            .filter(ComunicadoEntrada.id_propriedade_destino == int(id_propriedade), ComunicadoEntrada.tipo_entrada != 'TRANSFERENCIA',)   # v-s107: PIA nao existe na Transferencia
            .order_by(ComunicadoEntrada.numero_comunicado.desc(), ComunicadoEntrada.gta_data_emissao.asc())
            .all()
        )
        # agrupar_... le relacionamentos - chamado DENTRO da sessao.
        return agrupar_comunicados_por_numero(linhas, decrescente=True)


@pia_impressao.route('/produtor/pia/comunicado/pdf/<int:numero_comunicado>')
def comunicado_pdf(numero_comunicado):
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    pares, dados = _abrir(id_propriedade)
    if not pares:
        return _negado(id_propriedade, VOLTAR_SELECAO)   # v1.3.0 - trava: fazenda em uso e outra

    with get_db_produtor(session['id_produtor']) as db:
        ids_gta = [
            linha.id_gta for linha in db.query(ComunicadoEntrada).filter(
                ComunicadoEntrada.id_propriedade_destino == int(id_propriedade),
                ComunicadoEntrada.numero_comunicado == numero_comunicado,
                ComunicadoEntrada.tipo_entrada != 'TRANSFERENCIA',   # v-s107
            ).all()
            if linha.id_gta
        ]

    if not ids_gta:
        return _renderizar('comunicado', id_propriedade, pares, dados,
                           erro=f'Comunicado {numero_comunicado:06d} não encontrado nesta Propriedade.')

    # Em caso de erro, a tela volta na aba Comunicado (a lista e
    # recarregada sozinha pelo _renderizar).
    return _gerar('comunicado', id_propriedade, pares, dados,
                  [Pia.id_gta.in_(ids_gta)], f'comunicado_{numero_comunicado:06d}', {},
                  numero_pia=numero_comunicado)


# =======================================================
# BLOCO 6 - PLANILHA PIA DE NASCIMENTOS (v1.2.0)
# =======================================================

def _url_voltar_nascimento(pares):
    # v1.3.0 - com fazenda em uso a selecao e pulada: volta direto ao Hub.
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return VOLTAR_SELECAO_NASCIMENTO
    return VOLTAR_SUBHUB_NASCIMENTO


@pia_impressao.route('/produtor/pia/nascimento/iniciar')
def nascimento_iniciar():
    """Padrao Reutilizavel N.1 - com 1 unico par, pula direto."""
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    # v1.3.0 - FAZENDA EM USO: pula a tela de selecao e abre a Lista direto.
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/pia/nascimento?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/pia/nascimento?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None if pares else 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
        titulo=f'{TITULO_NASCIMENTO} — Selecionar Propriedade',
        proximo='/produtor/pia/nascimento',
        campo_propriedade='id_propriedade',
        voltar=VOLTAR_SUBHUB_NASCIMENTO,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo=MENU_ATIVO,
    )


def _so_numero(texto):   # Etapa 4 (2a passada): a quantidade vem da URL - so numero aparece na tela
    texto = str(texto or '').strip()
    return texto if (texto.isdecimal() and len(texto) <= 6) else '?'


@pia_impressao.route('/produtor/pia/nascimento')
def nascimento_lista():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    pares, dados = _abrir(id_propriedade)
    if not pares:
        return _negado(id_propriedade, VOLTAR_SELECAO_NASCIMENTO)   # v1.3.0 - trava: fazenda em uso e outra

    erro = ERROS_NASCIMENTO.get(request.args.get('erro', ''))
    if request.args.get('erro') == 'fabricante':
        erro = (f'ERRO GRAVE — PIA não gerada: {_so_numero(request.args.get("qtde", ""))} brinco(s) sem lote de origem '
                f'no estoque (fabricante não identificado). Avise a Consiste.')

    with get_db_produtor(session['id_produtor']) as db:
        gtas = (
            db.query(Gta)
            .filter(Gta.id_propriedade == int(id_propriedade),
                    Gta.tipo_movimento == 'NASCTO-DESMAME', Gta.serie_gta == 'NAS')
            .order_by(Gta.numero_gta_sequencial.desc())
            .all()
        )
        notificacoes = []
        for gta in gtas:
            total = db.query(Entrada).filter(Entrada.id_gta_entrada == gta.id).count()
            if total == 0:
                continue
            conferidos = db.query(Entrada).filter(
                Entrada.id_gta_entrada == gta.id, Entrada.conferido_brete.is_(True)).count()
            qtde_pia = db.query(Pia).filter(Pia.id_gta == gta.id).count()
            notificacoes.append({
                'id': gta.id,
                'numero': gta.numero_gta_completo,
                'data': gta.data_emissao.strftime('%d/%m/%Y') if gta.data_emissao else '',
                'qtde': qtde_pia,
                'faltam': total - conferidos,
            })

    return render_template(
        'produtor/pia_nascimento_listar.html',
        titulo=TITULO_NASCIMENTO,
        propriedade_nome=dados['propriedade'],
        id_propriedade=id_propriedade,
        notificacoes=notificacoes,
        erro=erro,
        url_voltar=_url_voltar_nascimento(pares),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo=MENU_ATIVO,
    )


@pia_impressao.route('/produtor/pia/nascimento/pdf/<int:id_gta>')
def nascimento_pdf(id_gta):
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    pares, dados = _abrir(id_propriedade)
    if not pares:
        return _negado(id_propriedade, VOLTAR_SELECAO_NASCIMENTO)   # v1.3.0 - trava: fazenda em uso e outra
    url_lista = f'/produtor/pia/nascimento?id_propriedade={id_propriedade}'

    with get_db_produtor(session['id_produtor']) as db:
        gta = (
            db.query(Gta)
            .filter(Gta.id == id_gta, Gta.id_propriedade == int(id_propriedade),
                    Gta.tipo_movimento == 'NASCTO-DESMAME', Gta.serie_gta == 'NAS')
            .first()
        )
        if not gta:
            return redirect(f'{url_lista}&erro=inexistente')

        numero_nas = gta.numero_gta_completo
        numero_pia = int(gta.numero_gta_sequencial) if str(gta.numero_gta_sequencial).isdecimal() else None

        pendentes = db.query(Entrada).filter(
            Entrada.id_gta_entrada == gta.id, Entrada.conferido_brete.is_(False)).count()
        if pendentes:
            return redirect(f'{url_lista}&erro=pendente')

        pias = (
            db.query(Pia)
            .filter(Pia.id_propriedade == int(id_propriedade), Pia.id_gta == gta.id)
            .order_by(Pia.sisbov)
            .all()
        )
        if not pias:
            return redirect(f'{url_lista}&erro=sem_pia')

        grupos, sem_fabricante = _montar_grupos(db, id_propriedade, pias)

    if sem_fabricante:
        return redirect(f'{url_lista}&erro=fabricante&qtde={len(sem_fabricante)}')

    return gerar_pdf_pia(grupos, dados, numero_nas, numero_pia, modelo='IX')   # v1.4.0 - Anexo IX

# =========================================================
# FIM DE ARQUIVO: backend\routers\pia_impressao.py
# =========================================================