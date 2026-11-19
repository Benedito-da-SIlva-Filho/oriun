# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\brincos_cancelamento.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-03 09:40 -03
# ATUALIZADO EM: 2026-11-16 10:40 -03
# VERSAO: 1.11.0
# v1.11.0: Sessao 128 (2026-11-16 10:40 -03) - AUDITORIA ETAPA 7b (Regra #57/#73): a trava _propriedade_permitida() passa a conferir tambem que o Produtor do par Propriedade+Produtor e o Produtor da sessao (antes so conferia a Propriedade); PDF com erro agora mostra a tela de erro dos Brincos com o norte (#69); numero do pedido do PDF passa a ser FIXO (dia desfeito continua contando). REVERSAO: .bak_antes_etapa7b.
# v1.10.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (3 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.9.0: Sessao 122 (2026-11-12 17:40 -03) - Auditoria Etapa 3 (item 1): trava da Propriedade ao salvar o cancelamento (duplo clique/2 abas nao cancelam a mesma faixa 2 vezes). REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Modulo "Cancelamento de Brincos" do Hub de Brincos.
#     Alinhamento de negocio fechado nas Sessoes 044/045.
#
#     Fluxo de 4 rotas:
#       1. /produtor/brincos-cancelamento/iniciar - resolve
#          Propriedade E Produtor (PADRAO REUTILIZAVEL No1).
#       2. /produtor/brincos-cancelamento/nova?id_propriedade=X -
#          formulario: Brinco Inicial (obrigatorio), Brinco Final
#          (OPCIONAL - vazio cancela so 1 brinco, preenchido
#          cancela a faixa DE->ATE) e Motivo (dropdown com os 4
#          valores do enum: DANIFICADO, EXTRAVIADO, INATIVADO,
#          VENDIDO).
#       3. /produtor/brincos-cancelamento/confirmar (POST) - NAO
#          grava nada. Simulacao: para cada SISBOV da faixa,
#          separa "sera cancelado" x "sera pulado" (com o motivo)
#          e mostra a previa para o Usuario confirmar (Benedito,
#          Sessao 045: "dividir a responsabilidade com o Usuario").
#       4. /produtor/brincos-cancelamento/salvar (POST) - repete a
#          mesma verificacao e GRAVA: 1 linha em tb_3008 por brinco
#          + tb_7017 (saida_origem = motivo, status = 'CANCELADO')
#          + lote(s) em tb_3007 (qtde_saida e saldo), tudo na
#          mesma transacao, com Log de Operacoes (Desfazer).
#
#     REGRAS DE NEGOCIO (Sessoes 044/045, reforcadas na 080):
#       - BUSCA COMPLETA (v1.7.0, Benedito): o brinco e localizado
#         por PROPRIEDADE + PRODUTOR + SISBOV - id_propriedade da
#         tela, CPF/CNPJ do Produtor logado (tb_7017.cpf_produtor,
#         gravado na Entrada de Brincos; linhas antigas sem CPF
#         gravado sao aceitas, ja que o schema do Produtor ja
#         isola os dados dele) e o SISBOV.
#       - DISPONIVEL para cancelar (v1.7.0 - MESMA regra do
#         Leitor/Bastao/Vincular): saida_data, saida_gta,
#         saida_origem, numero_comunicado E reservado_id_gta em
#         branco. Duas linhas disponiveis do mesmo SISBOV na mesma
#         Propriedade = "duplicado no estoque" (pulado - avise a
#         Consiste).
#       - BRINCAGEM PENDENTE (v1.7.0): brinco ja lido pelo
#         Leitor/Bastao (tb_5001 com sts=False), aguardando o
#         Vincular GTA, NAO pode ser cancelado (pulado).
#       - Faixa DE->ATE so dentro da MESMA SOLICITACAO (mesmo
#         id_lote_entrada) - v1.1.0.
#       - Brincos indisponiveis na faixa sao PULADOS (os demais
#         sao cancelados) - decisao de Benedito, Sessao 045.
#       - Saldo: qtde_entrada NUNCA muda; qtde_saida sobe e saldo
#         = qtde_entrada - qtde_saida.
#       - SISBOV puro, 15 digitos, SEM digito verificador.
#       - Limite de seguranca MAX_FAIXA brincos por operacao.
#
#     TRAVA DE PERMISSAO (v1.7.0): toda rota que recebe
#     id_propriedade confere se a Propriedade pertence aos pares
#     Propriedade/Produtor do usuario logado
#     (_propriedade_permitida). Numero trocado na URL = volta ao
#     inicio, sem mostrar nem gravar nada.
#
#     v1.0.0: Criacao do modulo (Sessao 045, 03/09/2026, 09:40 -03).
#     v1.1.0: Sessao 045 (10:35) - BUG REAL: faixa DE->ATE cruzava
#         solicitacoes diferentes. NOVA _validar_mesma_solicitacao()
#         + checagem de lote em _verificar_disponibilidade().
#     v1.2.0: Sessao 045 (11:05) - Tela de resultado: botao
#         principal volta para /nova (url_novo_cancelamento) e link
#         secundario para o Hub (url_hub).
#     v1.3.0: Sessao 045 (15:30) - Integracao com o Log de
#         Operacoes ("Desfazer por Operacao").
#     v1.4.0: Sessao 045 (15:30) - Rota /desfazer movida para o
#         modulo generico operacoes_recentes.py.
#     v1.5.0: Sessao 045 (17:36) - NOVO "Documento de
#         Cancelamento" (documentos-iniciar, documentos,
#         documento/pdf).
#     v1.6.0: Sessao 045 (18:10) - Documento agrupado POR DIA
#         (1 comunicado por dia), Nro do Pedido = contagem de dias,
#         Contato = usuario que imprime, NIRF removido.
#     v1.7.0: Sessao 080 (25/09/2026, 20:25 -03) - AUDITORIA
#         (regra de Benedito: sem pontas soltas):
#           - BUSCA COMPLETA Propriedade + Produtor + SISBOV (antes
#             so SISBOV, com .first() - com SISBOVs duplicados no
#             estoque podia cancelar a linha errada, ou de outra
#             Propriedade). NOVA funcao _linhas_estoque().
#           - Regra COMPLETA de disponibilidade (reserva e
#             comunicado entram) + duplicado no estoque.
#           - Brinco em Brincagem pendente (tb_5001 sts=False) e
#             pulado.
#           - _validar_mesma_solicitacao() reescrita sobre a busca
#             completa (duplicado em 2 solicitacoes = bloqueio).
#           - TRAVA DE PERMISSAO em nova/confirmar/salvar/
#             documentos/documento_pdf (NOVA
#             _propriedade_permitida()).
#           - Titulos da tela de Selecionar Propriedade no formato
#             obrigatorio "{Modulo} — Selecionar Propriedade"
#             (Regra de Ouro, Sessao 051).
#     v1.8.0: Sessao 091 (08/10/2026, 18:30 -03) - FAZENDA EM USO (Regra de Ouro #13):
#         Com fazenda em uso a tela "Selecionar Propriedade" e pulada: o iniciar()
#         abre direto a tela do modulo. O Voltar vai ao Hub de Brincos (sem passar pela
#         selecao). TRAVA: Propriedade da URL diferente da fazenda em uso e negada
#         (nunca le nem grava). Sem fazenda em uso o comportamento anterior permanece.
#         Leitura e gravacao dos dados intactas. REVERSAO: devolver a versao anterior.
# =========================================================

from types import SimpleNamespace
from datetime import date, datetime

from flask import Blueprint, render_template, request, redirect, session, send_file

from backend.database import engine
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text
from backend.utils.gravacao_nascimento import TRAVA_BRINCOS_NASC   # Etapa 3: mesma trava da Brincagem

from backend.models import Propriedade, Produtor, Usuario
from backend.models.tb_3007_brincos_entrada import BrincoEntrada
from backend.models.tb_3008_brincos_saida import BrincoSaida
from backend.models.tb_5001_brincagem import Brincagem
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.brincos_propriedade import tela_erro_brincos   # Etapa 7b - tela de erro padrao dos Brincos
from backend.utils.multitenant import get_db_produtor
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.models.tb_log_operacoes import LogOperacao
from backend.models.tb_log_operacoes_itens import LogOperacaoItem
from backend.utils.extenso import numero_por_extenso
from backend.utils.pdf_helper import link_callback_pdf
from xhtml2pdf import pisa
from io import BytesIO


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
brincos_cancelamento = Blueprint('brincos_cancelamento', __name__)


# -------------------------------------------------------
# v1.8.0 - TRAVA DA FAZENDA EM USO (Regra de Ouro #13): a Propriedade da URL
# difere da fazenda em uso (trocada em outra aba)? Sem fazenda em uso, ou
# valor que nao e numero, devolve False (as validacoes de cada tela
# continuam valendo).
# -------------------------------------------------------
def _fora_da_fazenda_em_uso(id_propriedade):
    try:
        id_int = int(id_propriedade)
    except (TypeError, ValueError):
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares)
    return par_em_uso is not None and int(par_em_uso.id_propriedade) != id_int


# -------------------------------------------------------
# Constantes do modulo
# -------------------------------------------------------

# Motivos do dropdown - espelham os 4 valores do enum
# tipo_entrada_enum (ver tb_3008_brincos_saida.py v1.1.0)
MOTIVOS_CANCELAMENTO = ('DANIFICADO', 'EXTRAVIADO', 'INATIVADO', 'VENDIDO')

# Limite de seguranca por operacao (ver DESCRICAO acima)
MAX_FAIXA = 500

INICIO_FLUXO = '/produtor/brincos-cancelamento/iniciar'
INICIO_DOCUMENTOS = '/produtor/brincos-cancelamento/documentos-iniciar'


# -------------------------------------------------------
# Funcao auxiliar (NOVA, v1.7.0): TRAVA DE PERMISSAO - a
# Propriedade pertence aos pares Propriedade/Produtor do usuario
# logado?
# -------------------------------------------------------
def _propriedade_permitida(id_propriedade):
    if not str(id_propriedade).isdecimal():
        return False
    if _fora_da_fazenda_em_uso(id_propriedade):
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    return int(id_propriedade) in {int(par.id_propriedade) for par in pares if str(par.id_produtor) == str(session.get('id_produtor'))}   # v1.11.0 - Produtor do par = Produtor da sessao (Etapa 7b)


# -------------------------------------------------------
# Funcao auxiliar (NOVA, v1.7.0): CPF/CNPJ do Produtor logado -
# terceiro filtro da busca completa do brinco.
# -------------------------------------------------------
def _cpf_produtor_logado():
    with Session(engine) as db:
        produtor = db.get(Produtor, int(session['id_produtor']))
        return produtor.cpf_cnpj if produtor else None


# -------------------------------------------------------
# Funcao auxiliar: busca os dados de cabecalho (Propriedade +
# Produtor vinculado) - copia curta local (PADRAO REUTILIZAVEL
# No1), mesma usada em brincos_disponiveis.py.
# -------------------------------------------------------
def _buscar_dados_cabecalho(id_produtor, id_propriedade):
    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade)) if id_propriedade else None
        produtor    = db.get(Produtor, int(id_produtor)) if id_produtor else None

        if not propriedade or not produtor:
            return None

        return SimpleNamespace(
            propriedade_nome = propriedade.nome,
            municipio        = propriedade.municipio,
            uf               = propriedade.uf,
            produtor_nome    = produtor.nome,
        )


# -------------------------------------------------------
# Funcao auxiliar: URL de "Voltar" pelo numero de pares
# Propriedade/Produtor (Regra de Ouro No4 - nunca hardcoded).
# -------------------------------------------------------
def _url_voltar_pos_selecao():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return INICIO_FLUXO
    return '/produtor/hub/brincos'


# -------------------------------------------------------
# Funcao auxiliar: Brinco Inicial (+ Final opcional) -> lista de
# SISBOVs (15 digitos, zeros a esquerda preservados).
# -------------------------------------------------------
def _gerar_faixa_sisbov(brinco_inicial, brinco_final):
    if not brinco_final:
        return [brinco_inicial]

    largura  = len(brinco_inicial)
    num_ini  = int(brinco_inicial)
    num_fim  = int(brinco_final)

    if num_fim < num_ini:
        raise ValueError('O Brinco Final não pode ser menor que o Brinco Inicial.')

    qtde = num_fim - num_ini + 1
    if qtde > MAX_FAIXA:
        raise ValueError(
            f'Faixa muito grande ({qtde} brincos). '
            f'O limite por operação é {MAX_FAIXA}. Divida em faixas menores.'
        )

    return [str(n).zfill(largura) for n in range(num_ini, num_fim + 1)]


# -------------------------------------------------------
# Funcao auxiliar (NOVA, v1.7.0): BUSCA COMPLETA do brinco no
# estoque - Propriedade + Produtor (CPF/CNPJ gravado na linha;
# linha antiga sem CPF e aceita, o schema ja isola o Produtor) +
# SISBOV. Devolve TODAS as linhas encontradas.
# -------------------------------------------------------
def _linhas_estoque(db, id_propriedade, cpf_produtor, sisbov):
    return (
        db.query(EntradaBrincoRfid)
        .filter(
            EntradaBrincoRfid.id_propriedade == int(id_propriedade),
            EntradaBrincoRfid.sisbov == sisbov,
            or_(EntradaBrincoRfid.cpf_produtor == cpf_produtor,
                EntradaBrincoRfid.cpf_produtor.is_(None)),
        )
        .all()
    )


def _esta_disponivel(linha):
    """Regra COMPLETA (mesma do Leitor/Bastao/Vincular)."""
    return (
        linha.saida_data is None and linha.saida_gta is None and linha.saida_origem is None
        and linha.numero_comunicado is None and linha.reservado_id_gta is None
    )


# -------------------------------------------------------
# Funcao auxiliar: o SISBOV pode ser cancelado? v1.7.0 - busca
# completa + regra completa + Brincagem pendente. Devolve
# (linha_disponivel, None) ou (None, 'motivo do pulo').
# id_lote_esperado=None = modo individual (sem faixa).
# -------------------------------------------------------
def _verificar_disponibilidade(db, id_propriedade, cpf_produtor, sisbov, id_lote_esperado=None):
    linhas = _linhas_estoque(db, id_propriedade, cpf_produtor, sisbov)
    if not linhas:
        return None, 'SISBOV não encontrado no estoque desta Propriedade'

    disponiveis = [l for l in linhas if _esta_disponivel(l)]
    if len(disponiveis) > 1:
        return None, 'duplicado no estoque — avise a Consiste'
    if not disponiveis:
        return None, 'já indisponível (utilizado, reservado, com comunicado ou já cancelado)'

    registro = disponiveis[0]

    if id_lote_esperado is not None and registro.id_lote_entrada != id_lote_esperado:
        return None, 'pertence a outra solicitação (fora da faixa segura)'

    pendente = (
        db.query(Brincagem)
        .filter_by(id_propriedade=int(id_propriedade), sisbov=sisbov, sts=False)
        .first()
    )
    if pendente:
        return None, 'lido na Brincagem, aguardando Vincular GTA'

    return registro, None


# -------------------------------------------------------
# Funcao auxiliar (v1.1.0, reescrita v1.7.0): Brinco Inicial e
# Final pertencem a MESMA solicitacao (id_lote_entrada)? Usa a
# busca completa. So vale no modo faixa.
# Devolve (id_lote, None), (None, None) no modo individual, ou
# (None, 'mensagem de erro').
# -------------------------------------------------------
def _validar_mesma_solicitacao(db, id_propriedade, cpf_produtor, brinco_inicial, brinco_final):
    if not brinco_final:
        return None, None

    lotes_inicial = {l.id_lote_entrada for l in _linhas_estoque(db, id_propriedade, cpf_produtor, brinco_inicial)}
    if not lotes_inicial:
        return None, 'Brinco Inicial não encontrado no estoque desta Propriedade. Confira o número digitado.'

    lotes_final = {l.id_lote_entrada for l in _linhas_estoque(db, id_propriedade, cpf_produtor, brinco_final)}
    if not lotes_final:
        return None, 'Brinco Final não encontrado no estoque desta Propriedade. Confira o número digitado.'

    em_comum = lotes_inicial & lotes_final
    if not em_comum:
        return None, (
            'Brinco Inicial e Brinco Final pertencem a solicitações diferentes. '
            'Cancele cada solicitação separadamente.'
        )
    if len(em_comum) > 1:
        return None, (
            'Esta faixa existe em mais de uma solicitação (brincos duplicados no estoque). '
            'Nada foi processado — avise a Consiste.'
        )

    return em_comum.pop(), None


# -------------------------------------------------------
# Funcao auxiliar: valida os campos do formulario e devolve a
# faixa de SISBOVs, ou uma mensagem de erro (usada por /confirmar
# e /salvar - validacao identica).
# -------------------------------------------------------
def _validar_formulario(brinco_inicial, brinco_final, motivo):
    if not brinco_inicial:
        return None, 'Informe o Brinco Inicial.'

    if not brinco_inicial.isdecimal() or len(brinco_inicial) != 15:
        return None, 'Brinco Inicial deve ter 15 dígitos numéricos (SISBOV puro, sem dígito verificador).'

    if brinco_final and (not brinco_final.isdecimal() or len(brinco_final) != 15):
        return None, 'Brinco Final deve ter 15 dígitos numéricos (SISBOV puro, sem dígito verificador).'

    if motivo not in MOTIVOS_CANCELAMENTO:
        return None, 'Selecione um Motivo válido.'

    try:
        faixa = _gerar_faixa_sisbov(brinco_inicial, brinco_final)
    except ValueError as erro:
        return None, str(erro)

    return faixa, None


def _render_formulario(cabecalho, id_propriedade, brinco_inicial, brinco_final, motivo, erro):
    return render_template(
        'produtor/brincos_cancelamento_nova.html',
        cabecalho=cabecalho,
        id_propriedade=id_propriedade,
        motivos=MOTIVOS_CANCELAMENTO,
        form=SimpleNamespace(brinco_inicial=brinco_inicial, brinco_final=brinco_final, motivo=motivo),
        erro=erro,
        url_voltar=_url_voltar_pos_selecao(),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )


def _render_selecao(pares, titulo, proximo):
    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None if pares else 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
        titulo=titulo,
        proximo=proximo,
        campo_propriedade='id_propriedade',
        voltar='/produtor/hub/brincos',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )


# -------------------------------------------------------
# Rota: GET /produtor/brincos-cancelamento/iniciar - ponto de
# partida (PADRAO REUTILIZAVEL No1).
# -------------------------------------------------------
@brincos_cancelamento.route('/produtor/brincos-cancelamento/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    # v1.8.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/brincos-cancelamento/nova?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/brincos-cancelamento/nova?id_propriedade={par.id_propriedade}')

    return _render_selecao(pares, 'Cancelamento de Brincos — Selecionar Propriedade',
                           '/produtor/brincos-cancelamento/nova')


# -------------------------------------------------------
# Rota: GET /produtor/brincos-cancelamento/nova?id_propriedade=X -
# formulario (Brinco Inicial, Brinco Final opcional, Motivo).
# -------------------------------------------------------
@brincos_cancelamento.route('/produtor/brincos-cancelamento/nova')
def nova():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_permitida(id_propriedade):
        return redirect(INICIO_FLUXO)

    cabecalho = _buscar_dados_cabecalho(session['id_produtor'], id_propriedade)
    if cabecalho is None:
        return redirect(INICIO_FLUXO)

    return _render_formulario(cabecalho, id_propriedade, '', '', '', None)


# -------------------------------------------------------
# Rota: POST /produtor/brincos-cancelamento/confirmar - NAO grava
# nada. Simula e mostra a previa (cancelado x pulado).
# -------------------------------------------------------
@brincos_cancelamento.route('/produtor/brincos-cancelamento/confirmar', methods=['POST'])
def confirmar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade  = request.form.get('id_propriedade', '')
    brinco_inicial  = request.form.get('brinco_inicial', '').strip()
    brinco_final    = request.form.get('brinco_final', '').strip()
    motivo          = request.form.get('motivo', '')

    if not _propriedade_permitida(id_propriedade):
        return redirect(INICIO_FLUXO)

    cabecalho = _buscar_dados_cabecalho(session['id_produtor'], id_propriedade)
    if cabecalho is None:
        return redirect(INICIO_FLUXO)

    faixa, erro = _validar_formulario(brinco_inicial, brinco_final, motivo)
    if erro:
        return _render_formulario(cabecalho, id_propriedade, brinco_inicial, brinco_final, motivo, erro)

    cpf_produtor = _cpf_produtor_logado()
    a_cancelar = []
    pulados    = []

    with get_db_produtor(session['id_produtor']) as db:
        id_lote_esperado, erro_lote = _validar_mesma_solicitacao(
            db, id_propriedade, cpf_produtor, brinco_inicial, brinco_final
        )
        if not erro_lote:
            for sisbov in faixa:
                registro, motivo_pulo = _verificar_disponibilidade(
                    db, id_propriedade, cpf_produtor, sisbov, id_lote_esperado
                )
                if motivo_pulo:
                    pulados.append(SimpleNamespace(sisbov=sisbov, motivo=motivo_pulo))
                else:
                    a_cancelar.append(sisbov)

    if erro_lote:
        return _render_formulario(cabecalho, id_propriedade, brinco_inicial, brinco_final, motivo, erro_lote)

    return render_template(
        'produtor/brincos_cancelamento_confirmar.html',
        cabecalho=cabecalho,
        id_propriedade=id_propriedade,
        brinco_inicial=brinco_inicial,
        brinco_final=brinco_final,
        motivo=motivo,
        a_cancelar=a_cancelar,
        total_a_cancelar=len(a_cancelar),
        pulados=pulados,
        total_pulados=len(pulados),
        url_voltar=f'/produtor/brincos-cancelamento/nova?id_propriedade={id_propriedade}',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )


# -------------------------------------------------------
# Rota: POST /produtor/brincos-cancelamento/salvar - grava de
# verdade. Repete a verificacao completa (evita janela de corrida
# e POST manipulado) e, para cada brinco disponivel: 1 linha em
# tb_3008 + tb_7017 (saida_origem, status) + lote(s) em tb_3007
# (qtde_saida, saldo), com Log de Operacoes. Tudo o que a tela de
# resultado usa e montado ANTES do commit (so valores simples).
# -------------------------------------------------------
@brincos_cancelamento.route('/produtor/brincos-cancelamento/salvar', methods=['POST'])
def salvar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade  = request.form.get('id_propriedade', '')
    brinco_inicial  = request.form.get('brinco_inicial', '').strip()
    brinco_final    = request.form.get('brinco_final', '').strip()
    motivo          = request.form.get('motivo', '')

    if not _propriedade_permitida(id_propriedade):
        return redirect(INICIO_FLUXO)

    cabecalho = _buscar_dados_cabecalho(session['id_produtor'], id_propriedade)
    if cabecalho is None:
        return redirect(INICIO_FLUXO)

    faixa, erro = _validar_formulario(brinco_inicial, brinco_final, motivo)
    if erro:
        # A previa ja validou isso - so cai aqui com POST manipulado.
        return _render_formulario(cabecalho, id_propriedade, brinco_inicial, brinco_final, motivo, erro)

    cpf_produtor = _cpf_produtor_logado()
    cancelados = []
    pulados    = []

    with get_db_produtor(session['id_produtor']) as db:
        # Etapa 3 (item 1): trava da Propriedade (a mesma da Brincagem). Duplo clique ou 2 abas
        # nao cancelam a mesma faixa duas vezes; a verificacao abaixo ja roda com a trava pegada.
        db.execute(text('SELECT pg_advisory_xact_lock(:ns, :id)'),
                   {'ns': TRAVA_BRINCOS_NASC, 'id': int(id_propriedade)})

        id_lote_esperado, erro_lote = _validar_mesma_solicitacao(
            db, id_propriedade, cpf_produtor, brinco_inicial, brinco_final
        )
        if erro_lote:
            db.rollback()
            return _render_formulario(cabecalho, id_propriedade, brinco_inicial, brinco_final, motivo, erro_lote)

        lote_contagem = {}  # id_lote_entrada -> quantidade cancelada neste lote

        # "Recibo" da operacao ANTES do loop (descricao provisoria,
        # atualizada no fim ou apagada se nada for cancelado).
        id_operacao = registrar_operacao(
            db,
            id_usuario=session['usuario_id'],
            id_propriedade=int(id_propriedade),
            modulo='cancelamento_brincos',
            descricao='Cancelamento de brincos (em processamento)',
        )

        for sisbov in faixa:
            registro, motivo_pulo = _verificar_disponibilidade(
                db, id_propriedade, cpf_produtor, sisbov, id_lote_esperado
            )

            if motivo_pulo:
                pulados.append(SimpleNamespace(sisbov=sisbov, motivo=motivo_pulo))
                continue

            dados_antes_rfid = {
                'saida_origem': registro.saida_origem,
                'status': registro.status,
            }

            saida = BrincoSaida(
                id_propriedade=int(id_propriedade),
                id_lote_entrada=registro.id_lote_entrada,
                sisbov=registro.sisbov,
                rfid=registro.rfid,
                data_saida=date.today(),
                gta=None,
                origem=motivo,
            )
            db.add(saida)
            db.flush()  # garante saida.id para o Log de Operacoes

            registro.saida_origem = motivo
            registro.status       = 'CANCELADO'

            registrar_item(
                db, id_operacao,
                tabela='tb_3008_brincos_saida',
                id_registro=saida.id,
                tipo_mudanca='INSERT',
                dados_antes=None,
                dados_depois={
                    'sisbov': saida.sisbov,
                    'origem': saida.origem,
                    'id_lote_entrada': saida.id_lote_entrada,
                },
            )
            registrar_item(
                db, id_operacao,
                tabela='tb_7017_entrada_brincos_rfid',
                id_registro=registro.id,
                tipo_mudanca='UPDATE',
                dados_antes=dados_antes_rfid,
                dados_depois={'saida_origem': motivo, 'status': 'CANCELADO'},
            )

            cancelados.append(sisbov)
            lote_contagem[registro.id_lote_entrada] = lote_contagem.get(registro.id_lote_entrada, 0) + 1

        # tb_3007 - qtde_entrada NUNCA muda; qtde_saida sobe e saldo
        # recalcula.
        for id_lote, qtde_cancelada in lote_contagem.items():
            lote = db.get(BrincoEntrada, id_lote)
            if lote:
                dados_antes_lote = {'qtde_saida': lote.qtde_saida, 'saldo': lote.saldo}

                lote.qtde_saida = (lote.qtde_saida or 0) + qtde_cancelada
                lote.saldo      = lote.qtde_entrada - lote.qtde_saida

                registrar_item(
                    db, id_operacao,
                    tabela='tb_3007_brincos_entrada',
                    id_registro=lote.id,
                    tipo_mudanca='UPDATE',
                    dados_antes=dados_antes_lote,
                    dados_depois={'qtde_saida': lote.qtde_saida, 'saldo': lote.saldo},
                )

        # Fecha o "recibo". Nada cancelado = recibo vazio apagado.
        if cancelados:
            operacao = db.get(LogOperacao, id_operacao)
            operacao.descricao = f'Cancelamento de {len(cancelados)} brinco(s) — Motivo: {motivo}'
        else:
            operacao_vazia = db.get(LogOperacao, id_operacao)
            db.delete(operacao_vazia)
            id_operacao = None

        db.commit()

    return render_template(
        'produtor/brincos_cancelamento_resultado.html',
        cabecalho=cabecalho,
        motivo=motivo,
        cancelados=cancelados,
        total_cancelados=len(cancelados),
        pulados=pulados,
        total_pulados=len(pulados),
        id_operacao=id_operacao,
        url_novo_cancelamento=f'/produtor/brincos-cancelamento/nova?id_propriedade={id_propriedade}',
        url_hub='/produtor/hub/brincos',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )

# -------------------------------------------------------
# Funcao auxiliar: dados COMPLETOS de Produtor e Propriedade
# para o Documento de Cancelamento.
# -------------------------------------------------------
def _buscar_dados_documento(id_produtor, id_propriedade, id_usuario):
    with Session(engine) as db:
        produtor    = db.get(Produtor, int(id_produtor)) if id_produtor else None
        propriedade = db.get(Propriedade, int(id_propriedade)) if id_propriedade else None
        usuario     = db.get(Usuario, int(id_usuario)) if id_usuario else None

        if not produtor or not propriedade:
            return None

        return SimpleNamespace(
            produtor_nome        = produtor.nome,
            produtor_cpf_cnpj    = produtor.cpf_cnpj,
            produtor_endereco    = f'{produtor.logradouro or ""}, {produtor.numero or ""}'.strip(', '),
            produtor_complemento = produtor.complemento,
            produtor_bairro      = produtor.bairro,
            produtor_municipio   = produtor.municipio,
            produtor_uf          = produtor.uf,
            produtor_cep         = produtor.cep,
            produtor_email       = produtor.email,
            produtor_telefone    = produtor.telefone,
            propriedade_nome        = propriedade.nome,
            propriedade_inscricao    = propriedade.inscricao_estadual,
            propriedade_email        = propriedade.email,
            contato_nome              = usuario.nome if usuario else '-',
        )


# -------------------------------------------------------
# Rota: GET /produtor/brincos-cancelamento/documentos-iniciar -
# card "Historico" do Hub de Brincos (PADRAO REUTILIZAVEL No1).
# -------------------------------------------------------
@brincos_cancelamento.route('/produtor/brincos-cancelamento/documentos-iniciar')
def documentos_iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    # v1.8.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/brincos-cancelamento/documentos?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/brincos-cancelamento/documentos?id_propriedade={par.id_propriedade}')

    return _render_selecao(pares, 'Histórico de Cancelamentos — Selecionar Propriedade',
                           '/produtor/brincos-cancelamento/documentos')


# -------------------------------------------------------
# Rota: GET /produtor/brincos-cancelamento/documentos?id_propriedade=X
# - lista os cancelamentos (nao desfeitos) agrupados POR DIA.
# -------------------------------------------------------
@brincos_cancelamento.route('/produtor/brincos-cancelamento/documentos')
def documentos():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_permitida(id_propriedade):
        return redirect(INICIO_DOCUMENTOS)

    cabecalho = _buscar_dados_cabecalho(session['id_produtor'], id_propriedade)
    if cabecalho is None:
        return redirect(INICIO_DOCUMENTOS)

    with get_db_produtor(session['id_produtor']) as db:
        operacoes_db = (
            db.query(LogOperacao)
            .filter_by(id_propriedade=int(id_propriedade), modulo='cancelamento_brincos')
            .filter(LogOperacao.desfeito_em.is_(None))
            .order_by(LogOperacao.criado_em.desc())
            .all()
        )

        # Agrupa por DIA (1 comunicado por dia - Benedito, Sessao 045).
        grupos_por_dia = {}
        for op in operacoes_db:
            dia = op.criado_em.date()
            grupos_por_dia.setdefault(dia, []).append(op)

        dias_lista = []
        for dia in sorted(grupos_por_dia.keys(), reverse=True):
            ops_do_dia = grupos_por_dia[dia]
            total_brincos = 0
            for op in ops_do_dia:
                total_brincos += (
                    db.query(LogOperacaoItem)
                    .filter_by(id_operacao=op.id, tabela='tb_3008_brincos_saida', tipo_mudanca='INSERT')
                    .count()
                )
            dias_lista.append(SimpleNamespace(
                data_iso=dia.isoformat(),
                data_br=dia.strftime('%d/%m/%Y'),
                total_operacoes=len(ops_do_dia),
                total_brincos=total_brincos,
            ))

    return render_template(
        'produtor/brincos_cancelamento_documentos_lista.html',
        cabecalho=cabecalho,
        id_propriedade=id_propriedade,
        dias=dias_lista,
        url_voltar=_url_voltar_pos_selecao(),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )


# -------------------------------------------------------
# Rota: GET /produtor/brincos-cancelamento/documento/pdf?id_propriedade=X
# &data=AAAA-MM-DD - Documento formal de Cancelamento (PDF),
# combinando todas as operacoes do dia.
# -------------------------------------------------------
@brincos_cancelamento.route('/produtor/brincos-cancelamento/documento/pdf')
def documento_pdf():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    data_str        = request.args.get('data', '')
    if not _propriedade_permitida(id_propriedade) or not data_str:
        return redirect(INICIO_DOCUMENTOS)

    try:
        data_alvo = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return tela_erro_brincos('A data do documento não é válida. Volte à lista do Histórico de Cancelamentos, escolha o dia de novo e tente imprimir; se o problema repetir, avise a Consiste (usuário, tela, data e hora).')   # Etapa 7b - #69

    with get_db_produtor(session['id_produtor']) as db:
        operacoes_do_dia = (
            db.query(LogOperacao)
            .filter_by(id_propriedade=int(id_propriedade), modulo='cancelamento_brincos')
            .filter(LogOperacao.desfeito_em.is_(None))
            .filter(func.date(LogOperacao.criado_em) == data_alvo)
            .order_by(LogOperacao.criado_em)
            .all()
        )

        if not operacoes_do_dia:
            return tela_erro_brincos('Não há cancelamento válido nesta data (pode ter sido desfeito em Operações Recentes). Volte à lista do Histórico de Cancelamentos, atualize a tela e escolha outro dia.')   # Etapa 7b - #69

        # Nro do Pedido = contagem de dias distintos com
        # cancelamento ate esta data (inclusive).
        nro_pedido = (
            db.query(func.count(func.distinct(func.date(LogOperacao.criado_em))))
            .filter(
                LogOperacao.id_propriedade == int(id_propriedade),
                LogOperacao.modulo == 'cancelamento_brincos',
                # Etapa 7b (decisao do Benedito 16/11/2026): o numero do pedido e FIXO - dia desfeito continua contando, entao reimprimir um dia antigo nunca muda o numero.
                func.date(LogOperacao.criado_em) <= data_alvo,
            )
            .scalar()
        )

        linhas_dados = []
        for op in operacoes_do_dia:
            itens = (
                db.query(LogOperacaoItem)
                .filter_by(id_operacao=op.id, tabela='tb_3008_brincos_saida', tipo_mudanca='INSERT')
                .all()
            )
            for item in itens:
                linhas_dados.append(SimpleNamespace(
                    sisbov=item.dados_depois.get('sisbov'),
                    motivo=item.dados_depois.get('origem'),
                ))

        linhas_dados.sort(key=lambda x: x.sisbov)

    # Contato = quem esta imprimindo agora.
    dados = _buscar_dados_documento(session['id_produtor'], id_propriedade, session['usuario_id'])
    if dados is None:
        return tela_erro_brincos('Não encontramos o Produtor ou a Propriedade deste documento. Volte ao Hub de Brincos e escolha a Propriedade de novo; se o problema repetir, avise a Consiste (usuário, tela, data e hora).')   # Etapa 7b - #69

    # Grid de 2 pares (Codigo SISBOV | Motivo) por linha.
    linhas = [linhas_dados[i:i + 2] for i in range(0, len(linhas_dados), 2)]

    html = render_template(
        'produtor/brincos_cancelamento_documento_pdf.html',
        dados=dados,
        nro_pedido=str(nro_pedido).zfill(6),
        data_solicitacao=data_alvo.strftime('%d/%m/%Y'),
        quantidade=len(linhas_dados),
        quantidade_extenso=numero_por_extenso(len(linhas_dados)),
        linhas=linhas,
    )

    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer, link_callback=link_callback_pdf)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'cancelamento_{data_alvo.strftime("%Y%m%d")}.pdf',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\brincos_cancelamento.py
# =========================================================