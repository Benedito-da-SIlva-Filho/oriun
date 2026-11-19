# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\gta_saida.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-17 15:00 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.17.0
# v1.17.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (8 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.16.0: Sessao 123 (2026-11-13 19:10 -03) - AUDITORIA ETAPA 6 (Regra #72): mascara e limpeza de CPF/CNPJ passam pelas funcoes centrais (validadores.py). REVERSAO: .bak_antes_etapa6c.
# v1.15.3: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras do CNPJ mantidas na limpeza e na formatacao. REVERSAO: .bak_antes_s122_etapa2.
# v1.15.2: Sessao 118 (2026-11-08 15:30 -03) - url_cadastrar da Posse vai direto a Adicionar Produtor (aceita CPF/CNPJ). REVERSAO: .bak_antes_s118_dtacpf
# v1.15.1: Sessao 118 (2026-11-08 13:25 -03) - CORRECAO (Regra #9): a DTA de Posse aberta pelo card do Hub (nova-posse, parametro de=hub) tem o Voltar/Cancelar levando de volta ao Hub de Saidas, e nao a tela dos 4 cartoes. O parametro viaja no formulario (campo hidden) para sobreviver a erro de validacao. REVERSAO: .bak_antes_s118_voltar.
# v1.15.0: Sessao 118 (2026-11-08 13:00 -03) - (1) rota nova-posse: o card "DTA de Alteracao de Posse" do Hub abre direto o formulario da Posse; (2) VENDA: rotas destino-produtor-base (lista as Propriedades do comprador na nossa base) e destino-base-escolher (acha/cria o registro de destino), para escolher a Propriedade do comprador sem depender de Parceiros. REVERSAO: .bak_antes_s118_destino.
# v1.14.0: Sessao 116 (2026-11-06 16:01 -03) - posse-produtores devolve pode_cadastrar (Titular/Administrador), url_cadastrar e mensagem de aviso, para o botao "Cadastrar Produtor novo" da DTA de Posse. REVERSAO: .bak_antes_s116_addprodutor.
# v1.13.2: Sessao 115 (2026-11-05 18:05 -03) - DTA de Posse sem Meio de Transporte (mesma Propriedade): grava NAO_SE_APLICA. REVERSAO: .bak_antes_s115_sem_meio.
# v1.13.1: Sessao 115 (2026-11-05 17:50 -03) - Procedencia da DTA passa a mostrar o OESA da Propriedade (antes lia codigo_mapa, vazio). REVERSAO: .bak_antes_s115_oesa_proc.
# v1.13.0: Sessao 115 (2026-11-05 18:45 -03) - Posse: destino so entre os outros Produtores da MESMA Propriedade (rotas posse-produtores e posse-produtor-escolher); sem busca por CPF nem cadastro de Parceiro. REVERSAO: .bak_antes_s115_posse_lista.
# v1.12.0: Sessao 115 (2026-11-05 17:40 -03) - DTA de ALTERACAO DE POSSE (tipo_movimento POSSE): destino = outro Produtor na MESMA Propriedade (conferir_destino_posse). REVERSAO: .bak_antes_s115_dta3a.
# v1.11.0: Sessao 111 (01/11/2026) - Venda e Morte (ver Diario de Bordo da Sessao 111). REVERSAO: arquivos .bak_antes_s111* ao lado.
#
# DESCRICAO:
#     Cadastro de GTA de SAIDA (Sessao 099) - pacote 1: lancar a GTA
#     a mao e consultar as GTAs de saida ja lancadas. A leitura do PDF
#     da e-GTA fica para um proximo pacote.
#
#     Segue o modelo da GTA de Entrada (gta_manual.py) e REUSA suas
#     regras: serie por UF, numero com 6 digitos, GTA duplicada,
#     meios de transporte, faixas de idade, sexo, soma das categorias
#     igual a Qtde declarada e confirmacao dos dados.
#
#     DIFERENCAS PARA A ENTRADA:
#       - sentido = 'SAIDA' e tipo_movimento = 'ABATE' (fixos).
#       - Procedencia = a propria fazenda em uso (automatica).
#       - Destino = Frigorifico, escolhido por busca (nome, CNPJ, UF,
#         municipio) em /produtor/frigorificos/api/buscar. Gravado em
#         id_frigorifico (nunca junto com id_parceiro_propriedade).
#       - NAO ha Data de Entrega: a data de saida e digitada depois,
#         na tela Vincular GTA / Embarque.
#       - status_brincagem = 'NAO_APLICA' (GTA de saida nao passa
#         pela Brincagem).
#
#     ROTAS (todas em /produtor/gta-saida/):
#       iniciar   - resolve a Propriedade (fazenda em uso) e abre a tela dos 3 cartoes.
#       inicio    - tela dos 3 cartoes (Importar PDF em breve / Manual / Consultar).
#       lista     - GTAs de saida lancadas.
#       nova      - formulario.
#       salvar    - valida e grava (tb_4001_gta + tb_4001_gta_animais).
#       sucesso   - confirmacao.
#       detalhe   - visualizar a GTA (somente leitura).
#
#     v1.10.0: Sessao 108 (29/10/2026, 20:10 -03) - Destino da Transferencia na nossa base: a IE que falta no Parceiro vem da nossa base (so na tela). REVERSAO: .bak_antes_s108_ie_base
#     v1.0.0: Criacao (Sessao 099).
#     v1.1.0: Sessao 099 (17/10/2026, 15:15 -03) - Nova tela de acesso com 3 cartoes (rota inicio), no molde da Entrada:
#             Importar e-GTA (Em breve), Preenchimento Manual, Consultar GTAs. iniciar() agora abre essa tela; Voltar de
#             formulario e lista levam a ela; o Voltar dela leva ao Hub de Saidas.
#     v1.2.0: Sessao 100 (19/10/2026, 17:05 -03) - Detalhe mostra a Data de Saida (coluna data_saida da GTA).
#     v1.3.0: Sessao 103 (22/10/2026, 12:45 -03) - ALTERAR e EXCLUIR GTA de Saida (decisoes de Benedito, ver BLOCO 4): rotas editar,
#             salvar-edicao e excluir; so Titular/Administrador; check dos animais vinculados x categorias (aviso vermelho no detalhe);
#             com Comunicado atualiza tb_2011/tb_2002/tb_2017 e avisa para reimprimir; Log (gta_saida_alterar / gta_saida_excluir).
#             Detalhe ganha os botoes Alterar/Excluir e os avisos. As rotas nova/salvar nao mudaram.
#             Precisa do log_operacoes.py 1.15.0 e do permissoes.py 1.9.0.  REVERSAO: .bak_antes_alterar_excluir_s103.
#     v1.4.0: Sessao 103 (22/10/2026, 15:50 -03) - Alterar: a UF da GTA e SEMPRE a da Propriedade (o servidor ignora a UF do formulario);
#             com Comunicado as categorias e a quantidade de animais nao mudam (aviso no lugar) e so Serie, Numero, Emissao, Validade
#             e Meio de Transporte sao editaveis (moldura + mensagem). Frigorifico e Data de Saida so mostrados.  REVERSAO: .bak_antes_alterar_aviso_s103.
#     v1.5.0: Sessao 103 (22/10/2026, 16:05 -03) - UMA consulta so: depois de Alterar, Excluir ou lancar a GTA, a tela volta para a Consulta GTA
#             (/produtor/saida-gta-consulta/...), que passa a ter Alterar/Excluir e os avisos. As rotas antigas lista/detalhe continuam no ar,
#             sem cartao.  REVERSAO: .bak_antes_consulta_unica_s103.
#     v1.6.0: Sessao 103 (22/10/2026, 16:15 -03) - Padrao 'Caixa de Sucesso' (utils/caixa_sucesso.py): depois de Alterar abre a tela
#             'GTA alterada com sucesso!' com o que mudou (antes -> depois) e o aviso vermelho de reimprimir; Excluir tambem termina na caixa.
#             O banner verde some. Nova rota GET /produtor/gta-saida/alterada/<id> (le e apaga o resumo guardado na sessao).  REVERSAO: .bak_antes_caixa_sucesso_s103.
#     v1.7.0: Sessao 103 (22/10/2026, 16:55 -03) - (1) UF da GTA travada na UF da Propriedade tambem no Cadastro NOVO (salvar ignora a UF do
#             formulario); (2) aposentadas a lista e o detalhe antigos: as rotas lista e detalhe agora REDIRECIONAM para a Consulta GTA
#             (saida_gta_consulta); templates gta_saida_lista.html e gta_saida_detalhe.html renomeados .aposentado_s103.  REVERSAO: .bak_antes_aposentar_s103.
#     v1.8.0: Sessao 107 (28/10/2026, 12:40 -03) - GTA de TRANSFERENCIA (tipo_movimento = 'TRANSFERENCIA'). O destino NAO e o Frigorifico:
#             e um Parceiro + Propriedade do Parceiro (id_parceiro_propriedade), achado pelo CPF/CNPJ em Parceiros (/api/busca-parceiro). Ao
#             escolher, o Orion roda o check-list com a nossa base (utils/destino_transferencia.py: CPF/CNPJ + Codigo MAPA + Inscricao Estadual,
#             nunca o endereco) e mostra o resultado; destino igual a origem ou com dados que se contradizem BLOQUEIA. Nova rota GET
#             /produtor/gta-saida/destino-checar. nova/salvar recebem tipo=TRANSFER. Na alteracao o destino fica TRAVADO (para trocar, exclui e
#             lanca de novo). O vinculo/Comunicado usam tipo_saida TRANSFER nas leituras.  REVERSAO: devolver .bak_antes_s107e.
#     v1.9.0: Sessao 108 (29/10/2026, 09:50 -03) - GTA de TRANSFERENCIA para OUTRA PROPRIEDADE DO PROPRIO PRODUTOR. Quando o CPF/CNPJ digitado
#     v1.11.1: Sessao 113 (03/11/2026, 14:40 -03) - GTA duplicada barrada antes do erro: confere na origem e, se o destino/comprador esta na base, tambem no destino (rota nova gta-checar para a conferencia na hora).  REVERSAO: .bak_antes_s113_gta_dup.
#             no destino e o do Produtor logado, a tela lista "Suas outras Propriedades" (nunca a de origem) em vez de procurar em Parceiros.
#             Ao escolher uma, o Orion acha ou cria sozinho o registro interno de destino (Parceiro com o CPF/CNPJ do Produtor + Propriedade
#             do Parceiro com o OESA de 11 digitos da Propriedade escolhida, sem inventar os 4 digitos da Exploracao) e o check-list normal
#             decide NA_BASE (Entrada automatica). Novas rotas: GET /produtor/gta-saida/destino-proprio e POST /produtor/gta-saida/destino-proprio-escolher.
#             Vincular, Gerar Comunicado e Impressao nao mudaram (leem o mesmo registro de destino).  REVERSAO: .bak_antes_s108_destino_proprio.
#     REVERSAO: remover este arquivo, os templates gta_saida_*.html e
#     devolver os .bak_antes_gta_saida_s099 de app.py, hub e permissoes.
# =========================================================

from datetime import datetime, date
from types import SimpleNamespace
from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, Produtor, PropriedadeProdutor
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4001_gta_animais import GtaAnimal
from backend.models.tb_frigorificos import Frigorifico
from backend.models.tb_parceiros import Parceiro
from backend.models.tb_parceiros_propriedades import ParceiroPropriedades
from backend.utils.destino_transferencia import conferir_destino, conferir_destino_posse, _doc_norm
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.gta_manual import (
    FAIXAS_IDADE, SEXOS_VALIDOS, MEIOS_TRANSPORTE_VALIDOS,
    _buscar_dados_exibicao, _ler_animais_do_formulario,
)
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_2011_com_saidas import ComunicadoSaida
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.routers.saida_comunicado import _linha_para_dict, _numero_6, _no_schema_do_destino
from backend.routers.saida_consulta import _faixa_em
from backend.routers.saida_vincular import _necessidades, _chave, _rotulo_categoria, _codigos_de_especie
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.caixa_sucesso import render_caixa_sucesso
from backend.utils.multitenant import get_db_produtor
from backend.utils.permissao_produtor import pode_cadastrar_produtor, MSG_SO_TITULAR_ADMIN
from backend.utils.regras_sisbov import tamanho_serie_gta, mensagem_serie_gta
from backend.utils.especies import carregar_especies, codigos_validos, mapa_codigo_descricao
from backend.utils.gta_duplicada import buscar_gta_duplicada, mensagem_gta_duplicada, eh_violacao_unicidade_gta
from backend.utils.validadores import limpar_documento, formatar_documento

# -------------------------------------------------------
# Blueprint e fixos
# -------------------------------------------------------
gta_saida = Blueprint('gta_saida', __name__)

SENTIDO_FIXO            = 'SAIDA'
TIPO_MOVIMENTO_FIXO     = 'ABATE'
STATUS_BRINCAGEM_SAIDA  = 'NAO_APLICA'
TIPO_MOVIMENTO_TRANSFER = 'TRANSFERENCIA'   # v1.8.0 - GTA de Transferencia
TIPO_SAIDA_TRANSFER     = 'TRANSFER'        # tipo_saida das leituras/saidas da Transferencia
MEIO_NAO_SE_APLICA      = 'NAO_SE_APLICA'   # s115 - DTA de Posse (mesma Propriedade) nao tem meio de transporte
TIPO_MOVIMENTO_VENDA    = 'VENDA'           # v1.11.0 - GTA de Venda (destino = outro Produtor, vem da GTA como na Transferencia)
TIPO_SAIDA_VENDA        = 'VENDA'           # tipo_saida das leituras/saidas da Venda
TIPO_MOVIMENTO_POSSE    = 'POSSE'           # s115 - DTA de Alteracao de Posse (mesma Propriedade, outro Produtor)
TIPO_SAIDA_POSSE        = 'POSSE'           # tipo_saida das leituras/saidas da Posse
TIPOS_GTA_DESTINO       = ('TRANSFER', 'VENDA', 'POSSE')                        # tipo_gta (tela) com destino Parceiro + Propriedade
MOVIMENTOS_DESTINO      = (TIPO_MOVIMENTO_TRANSFER, TIPO_MOVIMENTO_VENDA, TIPO_MOVIMENTO_POSSE)   # tipo_movimento da GTA com destino


def _tipo_gta_da_tela(texto):
    """'ABATE' / 'TRANSFER' / 'VENDA' a partir do que veio da tela (qualquer outra coisa = ABATE)."""
    t = str(texto or '').strip().upper()
    return t if t in TIPOS_GTA_DESTINO else 'ABATE'


def _tipo_gta_do_movimento(tipo_movimento):
    return {TIPO_MOVIMENTO_TRANSFER: 'TRANSFER', TIPO_MOVIMENTO_VENDA: 'VENDA', TIPO_MOVIMENTO_POSSE: 'POSSE'}.get(tipo_movimento, 'ABATE')


def _movimento_do_tipo_gta(tipo_gta):
    return {'TRANSFER': TIPO_MOVIMENTO_TRANSFER, 'VENDA': TIPO_MOVIMENTO_VENDA, 'POSSE': TIPO_MOVIMENTO_POSSE}.get(tipo_gta, TIPO_MOVIMENTO_FIXO)


def _rotulo_destino(tipo_gta):
    return {'VENDA': 'da Venda', 'POSSE': 'da Alteração de Posse'}.get(tipo_gta, 'da Transferência')


def _tipo_gta_destino_da_tela(texto):
    """s115 - Nas conferencias do destino: 'VENDA', 'POSSE' ou (qualquer outra coisa) 'TRANSFER'."""
    t = str(texto or '').strip().upper()
    return t if t in ('VENDA', 'POSSE') else 'TRANSFER'

URL_HUB    = '/produtor/hub-novo/saida'
URL_INICIO = '/produtor/gta-saida/inicio'
URL_LISTA  = '/produtor/gta-saida/lista'
URL_NOVA   = '/produtor/gta-saida/nova'
URL_INICIAR = '/produtor/gta-saida/iniciar'
URL_DETALHE = '/produtor/gta-saida/detalhe/'
URL_EDITAR  = '/produtor/gta-saida/editar/'
URL_EXCLUIR = '/produtor/gta-saida/excluir/'
URL_CONSULTA_LISTA = '/produtor/saida-gta-consulta/lista'      # v1.5.0 - a Consulta GTA e a unica consulta
URL_CONSULTA_DETALHE = '/produtor/saida-gta-consulta/detalhe'


def _url_consulta_lista(id_propriedade):
    return f'{URL_CONSULTA_LISTA}?id_propriedade={int(id_propriedade)}'


def _url_consulta_detalhe(id_propriedade, id_gta, extra=''):
    return f'{URL_CONSULTA_DETALHE}?id_propriedade={int(id_propriedade)}&id={int(id_gta)}{extra}'

MODULO_LOG_ALTERAR = 'gta_saida_alterar'     # v1.3.0 - Log (so historico)
MODULO_LOG_EXCLUIR = 'gta_saida_excluir'     # v1.3.0 - Log (so historico)
CARGOS_ALTERAR = ('TITULAR', 'ADMINISTRADOR')   # v1.3.0 - so um responsavel altera/exclui (Benedito)
MSG_SEM_PERMISSAO = 'Só o Titular e o Administrador da Propriedade podem alterar ou excluir uma GTA de Saída.'


def _contexto_base():
    return dict(
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='saidas',
    )


# -------------------------------------------------------
# A Propriedade pertence ao usuario logado e (se houver fazenda
# em uso) e a fazenda em uso? Mesmo criterio do Leitor do Abate.
# -------------------------------------------------------
def _propriedade_do_usuario(id_propriedade):
    try:
        id_int = int(id_propriedade)
    except (TypeError, ValueError):
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and par_em_uso.id_propriedade != id_int:
        return False
    return any(
        par.id_propriedade == id_int and par.id_produtor == session.get('id_produtor')
        for par in pares
    )


def _negado():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect(URL_INICIAR)
    return redirecionar_home()


def _uf_da_propriedade(id_propriedade):
    with Session(engine) as db:
        prop = db.get(Propriedade, int(id_propriedade))
        return (prop.uf or '').upper() if prop else ''


def _data_br(data):
    return data.strftime('%d/%m/%Y') if data else '-'


# -------------------------------------------------------
# GET /produtor/gta-saida/iniciar
# -------------------------------------------------------
@gta_saida.route('/produtor/gta-saida/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista,
            erro=erro,
            titulo='Cadastro de GTA de Saída — Selecionar Propriedade',
            proximo=URL_INICIO,
            campo_propriedade='id_propriedade',
            voltar=URL_HUB,
            **_contexto_base(),
        )

    if len(pares) == 0:
        return _tela_selecionar([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')

    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{URL_INICIO}?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_INICIO}?id_propriedade={par.id_propriedade}')

    return _tela_selecionar(pares, None)


# -------------------------------------------------------
# GET /produtor/gta-saida/inicio - tela dos 3 cartoes.
# -------------------------------------------------------
@gta_saida.route('/produtor/gta-saida/inicio')
def inicio():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    varias_propriedades = len(pares) > 1 and resolver_fazenda_em_uso(pares) is None

    return render_template(
        'produtor/gta_saida_inicio.html',
        id_propriedade=int(id_propriedade),
        varias_propriedades=varias_propriedades,
        url_hub=URL_HUB,
        **_contexto_base(),
    )


# -------------------------------------------------------
# GET /produtor/gta-saida/lista - GTAs de saida lancadas.
# -------------------------------------------------------
@gta_saida.route('/produtor/gta-saida/lista')
def lista():
    # v1.7.0 - lista antiga aposentada: a consulta e uma so (Consulta GTA).
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    return redirect(_url_consulta_lista(id_propriedade))


# -------------------------------------------------------
# v1.8.0 - Transferencia: tipo da GTA, destino (Parceiro + Propriedade do Parceiro) e check-list com a base.
# -------------------------------------------------------
def _tipo_saida_da_gta(tipo_movimento):
    """tipo_saida das leituras (tb_2020) que pertencem a uma GTA deste tipo_movimento."""
    if tipo_movimento == TIPO_MOVIMENTO_VENDA:
        return TIPO_SAIDA_VENDA
    if tipo_movimento == TIPO_MOVIMENTO_POSSE:
        return TIPO_SAIDA_POSSE
    return TIPO_SAIDA_TRANSFER if tipo_movimento == TIPO_MOVIMENTO_TRANSFER else TIPO_MOVIMENTO_FIXO


def _fmt_doc(texto):
    d = limpar_documento(texto)
    if len(d) == 14 and d[:3] == '000':
        d = d[3:]
    return formatar_documento(d) if len(d) in (11, 14) else d   # mascara central (validadores.py)


def _dados_destino_transfer(id_parceiro_propriedade, id_propriedade_origem, tipo_gta='TRANSFER'):
    """Destino da GTA de Transferencia + check-list com a base. None se nao existe ou esta inativo."""
    try:
        id_int = int(id_parceiro_propriedade)
    except (TypeError, ValueError):
        return None
    with get_db_produtor(session['id_produtor']) as db:
        pp = db.get(ParceiroPropriedades, id_int)
        if not pp or not pp.ativo:
            return None
        parceiro = db.get(Parceiro, pp.id_parceiro)
        if not parceiro or not parceiro.ativo:
            return None
        dados = {
            'id': pp.id,
            'parceiro_nome': parceiro.nome or '',
            'cpf_cnpj': _fmt_doc(parceiro.cpf_cnpj),
            'estabelecimento': pp.estabelecimento or '',
            'codigo_mapa': pp.codigo_mapa or '',
            'insc_estadual': pp.insc_estadual or '',
            'municipio': pp.municipio_nome or '',
            'uf': pp.uf or '',
        }
        doc, mapa, ie, uf = parceiro.cpf_cnpj, pp.codigo_mapa, pp.insc_estadual, pp.uf
    if tipo_gta == 'POSSE':   # s115 - mesma Propriedade (OESA), outro Produtor
        dados['conferencia'] = conferir_destino_posse(id_propriedade_origem, session.get('id_produtor'), doc, mapa, ie, uf)
    else:
        dados['conferencia'] = conferir_destino(id_propriedade_origem, doc, mapa, ie, uf)
    # v1.11.0 - VENDA e sempre para OUTRO Produtor: destino do proprio Produtor logado bloqueia (para as suas outras Propriedades, Transferencia).
    if tipo_gta == 'VENDA' and dados['conferencia'].get('id_produtor_destino') is not None \
            and str(dados['conferencia']['id_produtor_destino']) == str(session.get('id_produtor')):
        dados['conferencia'] = dict(dados['conferencia'])
        dados['conferencia']['nivel'] = 'bloqueio'
        dados['conferencia']['titulo'] = 'Venda é para outro Produtor'
        dados['conferencia']['entrada_automatica'] = False
        dados['conferencia']['itens'] = list(dados['conferencia']['itens']) + [
            {'ok': False, 'texto': 'O comprador é o próprio Produtor. Para passar animais para outra Propriedade sua, use a GTA de Transferência.'}]
    # v-s108: destino na nossa base -> completa a IE que o Parceiro nao tem com a IE da nossa base (so mostra; nao grava no Parceiro)
    base = dados['conferencia'].get('dados_base') or {}
    dados['ie_da_base'] = False
    if base.get('ie') and not dados['insc_estadual']:
        dados['insc_estadual'] = base['ie']
        dados['ie_da_base'] = True
    return dados


# -------------------------------------------------------
# v1.11.1 - GTA DUPLICADA barrada ANTES do erro (Sessao 112/113): confere na ORIGEM (a GTA de Saida ja existe) e, se o destino
# esta na base e ja tem esta GTA lancada na Entrada, tambem no DESTINO. Devolve o texto do motivo ou ''.
# Destino fora da base: nao ha como conferir.
# -------------------------------------------------------
def _conflito_gta(id_produtor, uf_gta, serie_gta, numero, conferencia, tipo_gta):
    uf, serie, num = (uf_gta or '').strip().upper(), (serie_gta or '').strip().upper(), (numero or '').strip()
    if not uf or not serie or len(num) != 6:
        return ''
    with get_db_produtor(id_produtor) as db:
        existente = buscar_gta_duplicada(db, uf, serie, num, SENTIDO_FIXO)
        if existente:
            return mensagem_gta_duplicada(existente)
        id_dest = (conferencia or {}).get('id_produtor_destino')
        if id_dest is None or (conferencia or {}).get('nivel') == 'bloqueio':
            return ''
        quem = 'O comprador' if tipo_gta == 'VENDA' else 'O destino'
        texto = f'{quem} já tem a GTA {uf}-{serie}-{num} lançada na Entrada dele. Confira o número da GTA.'
        if str(id_dest) == str(id_produtor):
            # Transferencia entre Propriedades do mesmo Produtor: a Entrada nasce no mesmo schema
            return texto if buscar_gta_duplicada(db, uf, serie, num, 'ENTRADA') else ''
        with Session(engine) as dbp:
            produtor_dest = dbp.get(Produtor, id_dest)
            schema = produtor_dest.schema_nome if produtor_dest else None
        if not schema:
            return ''
        tg = Gta.__table__
        with _no_schema_do_destino(db, schema):
            achou = db.execute(select(tg.c.id).where(
                tg.c.uf_gta == uf, tg.c.serie_gta == serie, tg.c.numero_gta_sequencial == num, tg.c.sentido == 'ENTRADA')).first()
        return texto if achou else ''


# -------------------------------------------------------
# GET /produtor/gta-saida/gta-checar (JSON) - confere a GTA digitada (origem + destino) na hora.
# -------------------------------------------------------
@gta_saida.route('/produtor/gta-saida/gta-checar')
def gta_checar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    tipo_gta = _tipo_gta_destino_da_tela(request.args.get('tipo'))   # s115: VENDA, POSSE ou TRANSFER
    conferencia = None
    if request.args.get('id_parceiro_propriedade'):
        destino = _dados_destino_transfer(request.args.get('id_parceiro_propriedade', ''), id_propriedade, tipo_gta)
        conferencia = destino['conferencia'] if destino else None
    try:
        mensagem = _conflito_gta(session['id_produtor'], request.args.get('uf', ''), request.args.get('serie', ''),
                                 request.args.get('numero', ''), conferencia, tipo_gta)
    except Exception:
        return jsonify({'ok': True, 'mensagem': ''})   # a conferencia na hora e ajuda; quem barra de verdade e o Salvar
    return jsonify({'ok': True, 'mensagem': mensagem})


# -------------------------------------------------------
# GET /produtor/gta-saida/destino-checar (JSON) - check-list do destino escolhido.
# -------------------------------------------------------
@gta_saida.route('/produtor/gta-saida/destino-checar')
def destino_checar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    destino = _dados_destino_transfer(request.args.get('id_parceiro_propriedade', ''), id_propriedade,
                                      _tipo_gta_destino_da_tela(request.args.get('tipo')))
    if destino is None:
        return jsonify({'erro': 'Destino não encontrado ou inativo em Parceiros.'}), 404
    return jsonify({'ok': True, 'destino': destino})


# -------------------------------------------------------
# v1.9.0 - DESTINO = OUTRA PROPRIEDADE DO PROPRIO PRODUTOR
# Funcao auxiliar: as OUTRAS Propriedades ativas do Produtor logado
# (vinculo ativo, sem a Propriedade de origem), como dicts simples.
# O codigo_mapa devolvido e o OESA de 11 digitos (Codigo do Estabelecimento).
# -------------------------------------------------------
def _outras_propriedades_do_produtor(id_produtor, id_propriedade_origem):
    saida = {}
    with Session(engine) as db:
        linhas = (
            db.query(Propriedade)
            .join(PropriedadeProdutor, PropriedadeProdutor.id_propriedade == Propriedade.id)
            .filter(PropriedadeProdutor.id_produtor == id_produtor,
                    PropriedadeProdutor.data_fim.is_(None),
                    Propriedade.ativo == True,   # noqa: E712
                    Propriedade.id != int(id_propriedade_origem))
            .order_by(Propriedade.nome)
            .all()
        )
        for p in linhas:
            saida[p.id] = {
                'id_propriedade': p.id,
                'estabelecimento': p.nome or '',
                'codigo_mapa': ''.join(c for c in (p.oesa or '') if c.isdecimal()),
                'insc_estadual': p.inscricao_estadual or '',
                'municipio_codigo': p.municipio_codigo or '',
                'municipio_nome': p.municipio or '',
                'uf': (p.uf or '').upper(),
            }
    return list(saida.values())


# -------------------------------------------------------
# GET /produtor/gta-saida/destino-proprio (JSON)
# O CPF/CNPJ digitado no destino e o do Produtor logado? Se sim,
# devolve as OUTRAS Propriedades dele. Se nao, {proprio: false} e a
# tela segue a busca normal em Parceiros.
# -------------------------------------------------------
@gta_saida.route('/produtor/gta-saida/destino-proprio')
def destino_proprio():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    with Session(engine) as db:
        produtor = db.get(Produtor, session['id_produtor'])
        doc_produtor = _doc_norm(produtor.cpf_cnpj) if produtor else ''
        nome_produtor = (produtor.nome or '') if produtor else ''
    doc_digitado = _doc_norm(request.args.get('documento', ''))
    if not doc_produtor or doc_digitado != doc_produtor:
        return jsonify({'proprio': False})
    return jsonify({
        'proprio': True,
        'produtor_nome': nome_produtor,
        'propriedades': _outras_propriedades_do_produtor(session['id_produtor'], id_propriedade),
    })


# -------------------------------------------------------
# POST /produtor/gta-saida/destino-proprio-escolher (JSON)
# Escolheu uma das suas outras Propriedades: acha ou cria o registro
# interno de destino (Parceiro com o CPF/CNPJ do Produtor + Propriedade
# do Parceiro com o OESA de 11 digitos) e devolve o id para o check-list.
# Pode ser repetido a vontade: reaproveita o que ja existe.
# -------------------------------------------------------
@gta_saida.route('/produtor/gta-saida/destino-proprio-escolher', methods=['POST'])
def destino_proprio_escolher():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    id_propriedade = request.form.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    try:
        id_destino = int(request.form.get('id_propriedade_destino', ''))
    except (TypeError, ValueError):
        return jsonify({'erro': 'Propriedade de destino não informada.'}), 400

    alvo = next((x for x in _outras_propriedades_do_produtor(session['id_produtor'], id_propriedade)
                 if x['id_propriedade'] == id_destino), None)
    if alvo is None:
        return jsonify({'erro': 'Esta não é uma das suas outras Propriedades ativas.'}), 404

    with Session(engine) as db:
        produtor = db.get(Produtor, session['id_produtor'])
        if not produtor:
            return jsonify({'erro': 'Produtor não encontrado.'}), 404
        doc_digitos = limpar_documento(produtor.cpf_cnpj)
        if len(doc_digitos) == 14 and doc_digitos[:3] == '000':
            doc_digitos = doc_digitos[3:]
        doc_comparar = _doc_norm(produtor.cpf_cnpj)
        nome_produtor = (produtor.nome or '').upper()

    with get_db_produtor(session['id_produtor']) as db:
        parceiro = next((x for x in db.query(Parceiro).filter(Parceiro.ativo == True).all()   # noqa: E712
                         if _doc_norm(x.cpf_cnpj) == doc_comparar), None)
        if parceiro is None:
            parceiro = Parceiro(cpf_cnpj=doc_digitos, nome=nome_produtor, ativo=True)
            db.add(parceiro)
            db.flush()

        pp = (db.query(ParceiroPropriedades)
              .filter(ParceiroPropriedades.id_parceiro == parceiro.id,
                      ParceiroPropriedades.ativo == True,   # noqa: E712
                      ParceiroPropriedades.codigo_mapa == (alvo['codigo_mapa'] or None))
              .first()) if alvo['codigo_mapa'] else None
        if pp is None:
            pp = ParceiroPropriedades(id_parceiro=parceiro.id, ativo=True)
            db.add(pp)
        pp.estabelecimento = alvo['estabelecimento'].upper()
        pp.codigo_mapa = alvo['codigo_mapa'] or None
        pp.insc_estadual = alvo['insc_estadual'] or None
        pp.municipio_codigo = alvo['municipio_codigo'] or None
        pp.municipio_nome = alvo['municipio_nome'].upper()
        pp.uf = alvo['uf']
        db.flush()
        id_pp = pp.id
        db.commit()

    return jsonify({'ok': True, 'id': id_pp})


# -------------------------------------------------------
# s115 - ALTERACAO DE POSSE: o destino e SEMPRE outro Produtor ja vinculado a MESMA Propriedade (decisao do Benedito, 05/11/2026).
# Nada de digitar CPF/CNPJ nem cadastrar Parceiro: a tela lista os outros Produtores da Propriedade; ao escolher, o servidor
# acha/cria o registro de destino (Parceiro + Propriedade do Parceiro) e o check-list normal da Posse roda.
# -------------------------------------------------------
def _outros_produtores_da_propriedade(id_propriedade, id_produtor_origem):
    saida = []
    with Session(engine) as db:
        prop = db.get(Propriedade, int(id_propriedade))
        if not prop:
            return saida
        oesa = ''.join(c for c in (prop.oesa or '') if c.isdecimal())[:11]
        linhas = (
            db.query(PropriedadeProdutor, Produtor)
            .join(Produtor, Produtor.id == PropriedadeProdutor.id_produtor)
            .filter(PropriedadeProdutor.id_propriedade == int(id_propriedade),
                    PropriedadeProdutor.data_fim.is_(None),
                    PropriedadeProdutor.id_produtor != int(id_produtor_origem),
                    Produtor.ativo == True)   # noqa: E712
            .order_by(Produtor.nome)
            .all()
        )
        for vinculo, prod in linhas:
            exploracao = ''.join(c for c in (vinculo.codigo_exploracao or '') if c.isdecimal())
            saida.append({
                'id_produtor': prod.id,
                'nome': prod.nome or '',
                'cpf_cnpj': _fmt_doc(prod.cpf_cnpj),
                'cpf_cnpj_digitos': limpar_documento(prod.cpf_cnpj),
                'estabelecimento': prop.nome or '',
                'codigo_mapa': exploracao or oesa,
                'insc_estadual': (vinculo.inscricao_estadual or prop.inscricao_estadual or '').strip(),
                'municipio_codigo': prop.municipio_codigo or '',
                'municipio_nome': prop.municipio or '',
                'uf': (prop.uf or '').upper(),
            })
    return saida


@gta_saida.route('/produtor/gta-saida/posse-produtores')
def posse_produtores():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    lista = _outros_produtores_da_propriedade(id_propriedade, session['id_produtor'])
    for x in lista:
        x.pop('cpf_cnpj_digitos', None)
    return jsonify({
        'ok': True, 'produtores': lista,
        'pode_cadastrar': pode_cadastrar_produtor(id_propriedade),
        'url_cadastrar': f'/produtores/novo?id_propriedade={int(id_propriedade)}',   # s118 - recebe &documento=
        'msg_sem_permissao': MSG_SO_TITULAR_ADMIN,
    })


@gta_saida.route('/produtor/gta-saida/posse-produtor-escolher', methods=['POST'])
def posse_produtor_escolher():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    id_propriedade = request.form.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    try:
        id_dest = int(request.form.get('id_produtor_destino', ''))
    except (TypeError, ValueError):
        return jsonify({'erro': 'Produtor de destino não informado.'}), 400
    alvo = next((x for x in _outros_produtores_da_propriedade(id_propriedade, session['id_produtor'])
                 if x['id_produtor'] == id_dest), None)
    if alvo is None:
        return jsonify({'erro': 'Este Produtor não está vinculado a esta Propriedade.'}), 404

    doc_digitos = alvo['cpf_cnpj_digitos']
    if len(doc_digitos) == 14 and doc_digitos[:3] == '000':
        doc_digitos = doc_digitos[3:]
    doc_comparar = _doc_norm(alvo['cpf_cnpj_digitos'])
    with get_db_produtor(session['id_produtor']) as db:
        parceiro = next((x for x in db.query(Parceiro).filter(Parceiro.ativo == True).all()   # noqa: E712
                         if _doc_norm(x.cpf_cnpj) == doc_comparar), None)
        if parceiro is None:
            parceiro = Parceiro(cpf_cnpj=doc_digitos, nome=(alvo['nome'] or '').upper(), ativo=True)
            db.add(parceiro)
            db.flush()
        pp = (db.query(ParceiroPropriedades)
              .filter(ParceiroPropriedades.id_parceiro == parceiro.id,
                      ParceiroPropriedades.ativo == True,   # noqa: E712
                      ParceiroPropriedades.codigo_mapa == (alvo['codigo_mapa'] or None))
              .first()) if alvo['codigo_mapa'] else None
        if pp is None:
            pp = ParceiroPropriedades(id_parceiro=parceiro.id, ativo=True)
            db.add(pp)
        pp.estabelecimento = alvo['estabelecimento'].upper()
        pp.codigo_mapa = alvo['codigo_mapa'] or None
        pp.insc_estadual = alvo['insc_estadual'] or None
        pp.municipio_codigo = alvo['municipio_codigo'] or None
        pp.municipio_nome = alvo['municipio_nome'].upper()
        pp.uf = alvo['uf']
        db.flush()
        id_pp = pp.id
        db.commit()
    return jsonify({'ok': True, 'id': id_pp})


# -------------------------------------------------------
# s118 - GET /produtor/gta-saida/nova-posse
# Atalho do Hub (aba Alteracao de Posse): resolve a Propriedade (fazenda em uso ou unica) e abre DIRETO o formulario da
# DTA de Posse (preenchida a mao). Sem fazenda em uso e com varias Propriedades, cai na tela de escolha de sempre (iniciar).
# O nome comeca com "nova", entao a permissao de Lanca (TELAS_DE_LANCAMENTO) vale sozinha.
# -------------------------------------------------------
@gta_saida.route('/produtor/gta-saida/nova-posse')
def nova_posse():
    if 'id_produtor' not in session:
        return redirecionar_home()
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par = resolver_fazenda_em_uso(pares)
    if par is None and len(pares) == 1:
        par = pares[0]
    if par is None:
        return redirect(URL_INICIAR)
    session['id_produtor']   = par.id_produtor
    session['usuario_cargo'] = par.cargo
    return redirect(f'{URL_NOVA}?id_propriedade={par.id_propriedade}&tipo=POSSE&de=hub')


# -------------------------------------------------------
# s118 - VENDA: Propriedades de um Produtor QUE ESTA NA NOSSA BASE (o comprador), para o usuario escolher a que recebe os animais.
# Funcao auxiliar: acha o Produtor ativo pelo CPF/CNPJ e lista as Propriedades ativas dele (sem a de origem), como dicts simples.
# codigo_mapa = Exploracao do vinculo, ou o OESA de 11 digitos (mesmo criterio da Posse).
# -------------------------------------------------------
def _produtor_base_e_propriedades(documento, id_propriedade_origem):
    doc = _doc_norm(documento)
    if not doc:
        return None, []
    with Session(engine) as db:
        produtor = next((p for p in db.query(Produtor).filter(Produtor.ativo == True).all()   # noqa: E712
                         if _doc_norm(p.cpf_cnpj) == doc), None)
        if produtor is None:
            return None, []
        dados_produtor = {'id_produtor': produtor.id, 'nome': produtor.nome or '',
                          'cpf_cnpj': _fmt_doc(produtor.cpf_cnpj),
                          'cpf_cnpj_digitos': limpar_documento(produtor.cpf_cnpj)}
        linhas = (
            db.query(PropriedadeProdutor, Propriedade)
            .join(Propriedade, Propriedade.id == PropriedadeProdutor.id_propriedade)
            .filter(PropriedadeProdutor.id_produtor == produtor.id,
                    PropriedadeProdutor.data_fim.is_(None),
                    Propriedade.ativo == True,   # noqa: E712
                    Propriedade.id != int(id_propriedade_origem))
            .order_by(Propriedade.nome)
            .all()
        )
        lista = []
        for vinculo, prop in linhas:
            exploracao = ''.join(c for c in (vinculo.codigo_exploracao or '') if c.isdecimal())
            oesa = ''.join(c for c in (prop.oesa or '') if c.isdecimal())[:11]
            lista.append({
                'id_propriedade': prop.id,
                'estabelecimento': prop.nome or '',
                'codigo_mapa': exploracao or oesa,
                'oesa': oesa,
                'insc_estadual': (vinculo.inscricao_estadual or prop.inscricao_estadual or '').strip(),
                'municipio_codigo': prop.municipio_codigo or '',
                'municipio_nome': prop.municipio or '',
                'uf': (prop.uf or '').upper(),
            })
    return dados_produtor, lista


@gta_saida.route('/produtor/gta-saida/destino-produtor-base')
def destino_produtor_base():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    produtor, lista = _produtor_base_e_propriedades(request.args.get('documento', ''), id_propriedade)
    if produtor is None or str(produtor['id_produtor']) == str(session.get('id_produtor')):
        return jsonify({'ok': True, 'encontrado': False})   # fora da base (ou o proprio Produtor, que tem a sua propria regra)
    produtor.pop('cpf_cnpj_digitos', None)
    return jsonify({'ok': True, 'encontrado': True, 'produtor': produtor, 'propriedades': lista})


# s118 - POST: escolheu uma Propriedade do comprador (na nossa base): acha ou cria o registro interno de destino
# (Parceiro com o CPF/CNPJ do comprador + Propriedade do Parceiro com o codigo/OESA) e devolve o id para o check-list normal.
@gta_saida.route('/produtor/gta-saida/destino-base-escolher', methods=['POST'])
def destino_base_escolher():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    id_propriedade = request.form.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não permitida.'}), 403
    try:
        id_prop_dest = int(request.form.get('id_propriedade_destino', ''))
    except (TypeError, ValueError):
        return jsonify({'erro': 'Propriedade de destino não informada.'}), 400
    # o servidor refaz a busca pelo documento: nunca confia no que o navegador diz sobre o comprador
    produtor, lista = _produtor_base_e_propriedades(request.form.get('documento', ''), id_propriedade)
    if produtor is None or str(produtor['id_produtor']) == str(session.get('id_produtor')):
        return jsonify({'erro': 'Comprador não encontrado na nossa base.'}), 404
    alvo = next((x for x in lista if x['id_propriedade'] == id_prop_dest), None)
    if alvo is None:
        return jsonify({'erro': 'Esta não é uma Propriedade ativa do comprador.'}), 404

    doc_digitos = produtor['cpf_cnpj_digitos']
    if len(doc_digitos) == 14 and doc_digitos[:3] == '000':
        doc_digitos = doc_digitos[3:]
    doc_comparar = _doc_norm(produtor['cpf_cnpj_digitos'])
    with get_db_produtor(session['id_produtor']) as db:
        parceiro = next((x for x in db.query(Parceiro).filter(Parceiro.ativo == True).all()   # noqa: E712
                         if _doc_norm(x.cpf_cnpj) == doc_comparar), None)
        if parceiro is None:
            parceiro = Parceiro(cpf_cnpj=doc_digitos, nome=(produtor['nome'] or '').upper(), ativo=True)
            db.add(parceiro)
            db.flush()
        pp = (db.query(ParceiroPropriedades)
              .filter(ParceiroPropriedades.id_parceiro == parceiro.id,
                      ParceiroPropriedades.ativo == True,   # noqa: E712
                      ParceiroPropriedades.codigo_mapa == (alvo['codigo_mapa'] or None))
              .first()) if alvo['codigo_mapa'] else None
        if pp is None:
            pp = ParceiroPropriedades(id_parceiro=parceiro.id, ativo=True)
            db.add(pp)
        pp.estabelecimento = alvo['estabelecimento'].upper()
        pp.codigo_mapa = alvo['codigo_mapa'] or None
        pp.insc_estadual = alvo['insc_estadual'] or None
        pp.municipio_codigo = alvo['municipio_codigo'] or None
        pp.municipio_nome = alvo['municipio_nome'].upper()
        pp.uf = alvo['uf']
        db.flush()
        id_pp = pp.id
        db.commit()
    return jsonify({'ok': True, 'id': id_pp})


# s115 - o quadro Procedencia mostrava Propriedade.codigo_mapa (vazio); o rotulo e OESA, entao usa Propriedade.oesa.
def _procedencia_com_oesa(propria, id_propriedade):
    if propria is None:
        return
    with Session(engine) as db:
        prop = db.get(Propriedade, int(id_propriedade))
        oesa = ''.join(c for c in ((prop.oesa if prop else '') or '') if c.isdecimal())
    if oesa:
        propria.codigo_mapa = oesa


# -------------------------------------------------------
# Monta e renderiza o formulario (usado por nova() e salvar()).
# -------------------------------------------------------
def _render_formulario(id_propriedade, erro=None, gta=None, animais=None, frigorifico=None, especies=None,
                       tipo_gta='ABATE', destino=None):
    id_produtor = session['id_produtor']
    de_hub = (request.values.get('de', '') == 'hub') and tipo_gta == 'POSSE'   # s118 - veio do card do Hub (args no GET, form no POST)
    _, propria = _buscar_dados_exibicao(id_produtor, None, None, id_propriedade)
    _procedencia_com_oesa(propria, id_propriedade)
    return render_template(
        'produtor/gta_saida_cadastro.html',
        erro=erro,
        procedencia=propria,
        gta=gta,
        animais=animais or [],
        frigorifico=frigorifico,
        tipo_gta=tipo_gta,
        destino=destino,
        documento_inicial=limpar_documento(request.args.get('documento', ''))[:14] if tipo_gta in TIPOS_GTA_DESTINO else '',
        id_propriedade=int(id_propriedade),
        uf_fazenda=_uf_da_propriedade(id_propriedade),
        faixas_idade=FAIXAS_IDADE,
        especies=especies if especies is not None else carregar_especies(),
        sexos=SEXOS_VALIDOS,
        url_inicio=(URL_HUB if de_hub else f'{URL_INICIO}?id_propriedade={id_propriedade}'),   # s118 - Voltar = caminho real
        de='hub' if de_hub else '',
        **_contexto_base(),
    )


def _dados_frigorifico(id_frigorifico):
    """Dict para exibir o Frigorifico escolhido, ou None se nao existe/inativo."""
    try:
        id_int = int(id_frigorifico)
    except (TypeError, ValueError):
        return None
    with Session(engine) as db:
        f = db.get(Frigorifico, id_int)
        if not f or not f.ativo:
            return None
        cnpj = limpar_documento(f.cpf_cnpj)
        if len(cnpj) == 14:
            cnpj = formatar_documento(cnpj)
        selos = []
        if f.cod_sif: selos.append('SIF ' + f.cod_sif)
        if f.cod_sie: selos.append('SIE ' + f.cod_sie)
        if f.cod_sim: selos.append('SIM ' + f.cod_sim)
        return {
            'id': f.id,
            'nome': f.nome or '',
            'cnpj': cnpj,
            'municipio': f.municipio_nome or '',
            'uf': f.uf or '',
            'selos': ' · '.join(selos),
        }


# -------------------------------------------------------
# GET /produtor/gta-saida/nova
# -------------------------------------------------------
@gta_saida.route('/produtor/gta-saida/nova')
def nova():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()

    tipo_gta = _tipo_gta_da_tela(request.args.get('tipo'))
    return _render_formulario(id_propriedade, tipo_gta=tipo_gta)


# -------------------------------------------------------
# POST /produtor/gta-saida/salvar
# -------------------------------------------------------
@gta_saida.route('/produtor/gta-saida/salvar', methods=['POST'])
def salvar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_produtor = session['id_produtor']
    id_propriedade = request.form.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()

    # A UF da GTA de Saida e SEMPRE a da Propriedade (v1.7.0); se a Propriedade nao tiver UF, vale a do formulario.
    uf_gta = (_uf_da_propriedade(id_propriedade) or request.form.get('uf_gta', '')).strip().upper()
    serie_gta = request.form.get('serie_gta', '').strip().upper()
    numero = ''.join(c for c in request.form.get('numero_gta_sequencial', '') if c.isdecimal())
    if numero:
        numero = numero.zfill(6)
    data_emissao_str = request.form.get('data_emissao', '').strip()
    data_validade_str = request.form.get('data_validade', '').strip()
    meio_transporte = request.form.get('meio_transporte', '').strip().upper()
    qtde_str = request.form.get('qtde_animais_gta', '').strip()
    confirma_dados = request.form.get('confirma_dados') == 'on'
    id_frigorifico = request.form.get('id_frigorifico', '').strip()
    tipo_gta = _tipo_gta_da_tela(request.form.get('tipo_gta'))
    transfer = tipo_gta in TIPOS_GTA_DESTINO   # v1.11.0: 'transfer' = GTA com destino Parceiro (Transferencia ou Venda)

    especies = carregar_especies()
    codigos_especie = codigos_validos(especies)
    animais = _ler_animais_do_formulario(especies)
    soma_animais = sum(a['quantidade'] for a in animais)
    frigorifico = _dados_frigorifico(id_frigorifico) if (id_frigorifico and not transfer) else None
    destino = (_dados_destino_transfer(request.form.get('id_parceiro_propriedade', ''), id_propriedade, tipo_gta)
               if transfer else None)

    gta_tentativa = SimpleNamespace(
        uf_gta=uf_gta, serie_gta=serie_gta, numero_gta_sequencial=numero,
        data_emissao=data_emissao_str, data_validade=data_validade_str,
        meio_transporte=meio_transporte, qtde_animais_gta=qtde_str,
        confirma_dados=confirma_dados,
    )

    def _reexibir(mensagem):
        return _render_formulario(id_propriedade, erro=mensagem, gta=gta_tentativa,
                                  animais=animais, frigorifico=frigorifico, especies=especies,
                                  tipo_gta=tipo_gta, destino=destino)

    if transfer:
        if not destino:
            return _reexibir({'VENDA': 'Escolha o Comprador da Venda!', 'POSSE': 'Escolha o Produtor de destino da Alteração de Posse!'}.get(tipo_gta, 'Escolha o Destino da Transferência!'))
        if destino['conferencia']['nivel'] == 'bloqueio':
            return _reexibir('Destino não permitido: ' + destino['conferencia']['titulo'] + '. Confira o check-list do destino.')
    elif not frigorifico:
        return _reexibir('Escolha o Frigorífico de destino!')

    if not uf_gta or len(uf_gta) != 2:
        return _reexibir('UF da GTA é obrigatória!')
    if not serie_gta or len(serie_gta) != tamanho_serie_gta(uf_gta) or not serie_gta.isalpha():
        return _reexibir(mensagem_serie_gta(uf_gta))
    if not numero or len(numero) != 6:
        return _reexibir('Número da GTA é obrigatório e deve ter 6 dígitos!')

    msg_dup = _conflito_gta(id_produtor, uf_gta, serie_gta, numero, (destino or {}).get('conferencia') if transfer else None, tipo_gta)   # v1.11.1: origem + destino
    if msg_dup:
        return _reexibir(msg_dup)

    if tipo_gta == 'POSSE':
        meio_transporte = MEIO_NAO_SE_APLICA   # s115 - mesma Propriedade: nao ha transporte
    if not meio_transporte or (meio_transporte not in MEIOS_TRANSPORTE_VALIDOS and meio_transporte != MEIO_NAO_SE_APLICA):
        return _reexibir('Selecione o Meio de Transporte!')

    try:
        qtde_gta = int(qtde_str)
        if qtde_gta <= 0:
            raise ValueError()
    except ValueError:
        return _reexibir('Quantidade de Animais na GTA é obrigatória e deve ser maior que zero!')

    if not data_emissao_str:
        return _reexibir('Data de Emissão é obrigatória!')
    try:
        data_emissao = datetime.strptime(data_emissao_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data de Emissão incorreta! Use o formato dd/mm/aaaa.')
    if data_emissao > date.today():
        return _reexibir(
            f'Data de Emissão não pode ser uma data futura (hoje é {date.today().strftime("%d/%m/%Y")})! '
            f'Confira o dia, o mês e o ano digitados.'
        )

    if not data_validade_str:
        return _reexibir('Data de Validade é obrigatória!')
    try:
        data_validade = datetime.strptime(data_validade_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data de Validade incorreta! Use o formato dd/mm/aaaa.')
    if data_validade < data_emissao:
        return _reexibir('Data de Validade não pode ser anterior à Data de Emissão!')

    if not animais:
        return _reexibir('Informe ao menos uma categoria de Animais!')
    for animal in animais:
        if animal['especie'] not in codigos_especie:
            return _reexibir('Selecione a Espécie em todas as categorias de Animais.')
        if animal['sexo'] not in SEXOS_VALIDOS:
            return _reexibir('Selecione o Sexo em todas as categorias de Animais.')
        if animal['idade_meses'] not in FAIXAS_IDADE:
            return _reexibir('Selecione a Idade em todas as categorias de Animais.')
        if animal['quantidade'] <= 0:
            return _reexibir('Quantidade deve ser maior que zero em todas as categorias de Animais.')

    if soma_animais != qtde_gta:
        if soma_animais < qtde_gta:
            return _reexibir(f'Falta incluir {qtde_gta - soma_animais} animal(is) para bater com a Quantidade declarada ({qtde_gta}).')
        return _reexibir(f'A soma das categorias ({soma_animais}) excede a Quantidade declarada na GTA ({qtde_gta}). Confira os valores.')

    if not confirma_dados:
        return _reexibir('Confirme que os dados foram conferidos antes de salvar!')

    # ---------------------------------------------------
    # Tudo validado - grava.
    # ---------------------------------------------------
    with get_db_produtor(id_produtor) as db:
        try:
            gta = Gta(
                id_propriedade=int(id_propriedade),
                uf_gta=uf_gta,
                serie_gta=serie_gta,
                numero_gta_sequencial=numero,
                numero_gta_completo=f'{uf_gta}{serie_gta}{numero}',
                qtde_animais=qtde_gta,
                tipo_movimento=_movimento_do_tipo_gta(tipo_gta),
                sentido=SENTIDO_FIXO,
                data_emissao=data_emissao,
                data_validade=data_validade,
                data_entrega=None,
                meio_transporte=meio_transporte,
                id_parceiro_propriedade=destino['id'] if transfer else None,
                id_frigorifico=None if transfer else frigorifico['id'],
                status_brincagem=STATUS_BRINCAGEM_SAIDA,
            )
            db.add(gta)
            db.flush()
            for animal in animais:
                db.add(GtaAnimal(
                    id_gta=gta.id,
                    especie=animal['especie'],
                    sexo=animal['sexo'],
                    idade_meses=animal['idade_meses'],
                    quantidade=animal['quantidade'],
                ))
            id_gta_gravada = gta.id      # guardado ANTES do commit
            db.commit()
        except IntegrityError as erro_banco:
            db.rollback()
            if not eh_violacao_unicidade_gta(erro_banco):
                raise
            existente = buscar_gta_duplicada(db, uf_gta, serie_gta, numero, SENTIDO_FIXO)
            if existente:
                return _reexibir(mensagem_gta_duplicada(existente))
            return _reexibir(
                'Esta GTA acabou de ser cadastrada por outra pessoa. '
                'Não é permitido cadastrar a mesma GTA duas vezes.'
            )

    return redirect(f'/produtor/gta-saida/sucesso/{id_gta_gravada}')


# -------------------------------------------------------
# Le uma GTA de saida do Produtor logado (ou None).
# -------------------------------------------------------
def _carregar_gta_saida(id_gta):
    with get_db_produtor(session['id_produtor']) as db:
        gta = db.get(Gta, id_gta)
        if not gta or gta.sentido != SENTIDO_FIXO:
            return None
        if not _propriedade_do_usuario(gta.id_propriedade):
            return None
        dados = SimpleNamespace(
            id=gta.id,
            id_propriedade=gta.id_propriedade,
            id_frigorifico=gta.id_frigorifico,
            id_parceiro_propriedade=gta.id_parceiro_propriedade,
            numero_gta_completo=gta.numero_gta_completo,
            qtde_animais=gta.qtde_animais,
            data_emissao=_data_br(gta.data_emissao),
            data_validade=_data_br(gta.data_validade),
            data_saida=_data_br(gta.data_saida) if gta.data_saida else '-',
            meio_transporte=gta.meio_transporte,
            tipo_movimento=gta.tipo_movimento,
            numero_comunicado=gta.numero_comunicado,
        )
        animais = [SimpleNamespace(especie=a.especie, sexo=a.sexo,
                                   idade_meses=a.idade_meses, quantidade=a.quantidade)
                   for a in gta.animais]
    return dados, animais


# -------------------------------------------------------
# GET /produtor/gta-saida/sucesso/<id>
# -------------------------------------------------------
@gta_saida.route('/produtor/gta-saida/sucesso/<int:id_gta>')
def sucesso(id_gta):
    if 'id_produtor' not in session:
        return redirecionar_home()
    achou = _carregar_gta_saida(id_gta)
    if not achou:
        return _negado()
    gta, _ = achou
    return render_template(
        'produtor/gta_saida_sucesso.html',
        gta=gta,
        frigorifico=_dados_frigorifico(gta.id_frigorifico),
        destino=(_dados_destino_transfer(gta.id_parceiro_propriedade, gta.id_propriedade, _tipo_gta_do_movimento(gta.tipo_movimento))
                 if gta.tipo_movimento in MOVIMENTOS_DESTINO else None),
        url_nova=f'{URL_NOVA}?id_propriedade={gta.id_propriedade}' + (f'&tipo={_tipo_gta_do_movimento(gta.tipo_movimento)}' if gta.tipo_movimento in MOVIMENTOS_DESTINO else ''),
        url_lista=_url_consulta_lista(gta.id_propriedade),
        **_contexto_base(),
    )


# -------------------------------------------------------
# GET /produtor/gta-saida/detalhe/<id> - somente leitura.
# -------------------------------------------------------
@gta_saida.route('/produtor/gta-saida/detalhe/<int:id_gta>')
def detalhe(id_gta):
    # v1.7.0 - detalhe antigo aposentado: a consulta e uma so (Consulta GTA).
    if 'id_produtor' not in session:
        return redirecionar_home()
    achou = _carregar_gta_saida(id_gta)
    if not achou:
        return _negado()
    gta, _ = achou
    return redirect(_url_consulta_detalhe(gta.id_propriedade, gta.id))


# =========================================================
# BLOCO 4 (v1.3.0) - ALTERAR e EXCLUIR GTA de Saida
# Regras fechadas com Benedito (22/10/2026):
#   - So GTA digitada a mao (hoje toda GTA de Saida e) e so Titular/Administrador.
#   - Alterar vale com a GTA ja vinculada e mesmo com Comunicado. Se as categorias mudarem e os animais vinculados deixarem de
#     bater, o sistema CONFERE sozinho (_avisos_do_vinculo) e mostra um aviso vermelho no topo com o que divergiu; o usuario
#     corrige pela Substituicao de Animal (antes do Comunicado) ou pela Troca depois do Comunicado.
#   - Com Comunicado, as copias dos dados da GTA (tb_2011, tb_2002 e tb_2017) sao atualizadas junto, e a tela avisa para
#     reimprimir se o Comunicado ja foi impresso. O Frigorifico NAO muda depois do Comunicado (o Comunicado e por frigorifico).
#   - Excluir: so sem animais vinculados e sem Comunicado; a linha inteira vai para o Log (prova de quem excluiu). Nao se desfaz.
# =========================================================

def _gta_digitada_a_mao(gta):
    """Hoje toda GTA de Saida e digitada a mao (a leitura do PDF da e-GTA ainda nao existe). Quando existir, marcar aqui a origem."""
    return True


def _cargo_na_propriedade(id_propriedade):
    for par in buscar_pares_propriedade_produtor(session['usuario_id']):
        if int(par.id_propriedade) == int(id_propriedade):
            return par.cargo
    return None


def _pode_alterar(id_propriedade):
    return (_cargo_na_propriedade(id_propriedade) or '').strip().upper() in CARGOS_ALTERAR


def _sem_permissao():
    return (f'<p style="font-family:Arial;padding:24px">{MSG_SEM_PERMISSAO} '
            f'<a href="{URL_HUB}">Voltar</a></p>'), 403


def _lista_sisbov(lista, limite=6):
    """'1234, 5678 e mais 3' - para as mensagens do check."""
    mostra = ', '.join(lista[:limite])
    return mostra + (f' e mais {len(lista) - limite}' if len(lista) > limite else '')


def _montar_divergencias(necessidades, contagem, rotulos, sem_categoria):
    """
    Funcao PURA do check: compara o que a GTA pede (necessidades: chave -> {'qtd','rotulo'}) com os animais vinculados
    (contagem: chave -> lista de SISBOVs; rotulos: chave -> texto). Devolve a lista de textos do que NAO bate (vazia = tudo certo).
    """
    avisos = []
    for chave, lista in contagem.items():
        pede = necessidades[chave]['qtd'] if chave in necessidades else 0
        rotulo = necessidades[chave]['rotulo'] if chave in necessidades else rotulos.get(chave, '-')
        if pede == 0:
            avisos.append(f'{rotulo}: a GTA não pede esta categoria, mas há {len(lista)} animal(is) vinculado(s) '
                          f'(SISBOV {_lista_sisbov(lista)}).')
        elif len(lista) > pede:
            avisos.append(f'{rotulo}: a GTA pede {pede}, mas há {len(lista)} vinculado(s) — sobram {len(lista) - pede} '
                          f'(SISBOV {_lista_sisbov(lista[pede:])}).')
    for chave, n in necessidades.items():
        tem = len(contagem.get(chave, []))
        if 0 < tem < n['qtd'] or (tem == 0 and contagem):
            avisos.append(f"{n['rotulo']}: a GTA pede {n['qtd']}, há só {tem} vinculado(s) — faltam {n['qtd'] - tem}.")
    if sem_categoria:
        avisos.append(f'{len(sem_categoria)} animal(is) vinculado(s) sem sexo, nascimento ou espécie — não dá para conferir '
                      f'(SISBOV {_lista_sisbov(sem_categoria)}).')
    return avisos


def _divergencias_do_vinculo(db, gta):
    """
    CHECK dos animais vinculados x categorias da GTA. Antes do Comunicado usa as leituras vinculadas (tb_2020, id_gta);
    depois do Comunicado usa os animais que estao nele (tb_2002, nao substituidos). Sem animais vinculados: sem aviso.
    """
    if gta.numero_comunicado is not None:
        linhas = db.query(SaidaAnimal).filter(SaidaAnimal.id_gta == gta.id, SaidaAnimal.substituido == False).all()   # noqa: E712
    else:
        linhas = db.query(Embarque).filter(Embarque.id_gta == gta.id, Embarque.tipo_saida == _tipo_saida_da_gta(gta.tipo_movimento)).all()
    if not linhas:
        return []
    faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
    codigos = _codigos_de_especie()
    necessidades = _necessidades(gta.animais)
    contagem, rotulos, sem_categoria = {}, {}, []
    for l in sorted(linhas, key=lambda x: x.sisbov or ''):
        faixa = _faixa_em(faixas, l.nascimento, l.data_embarque) if l.data_embarque else '-'
        especie = codigos.get(l.id_especie)
        if faixa == '-' or not l.sexo or not especie:
            sem_categoria.append(l.sisbov)
            continue
        chave = _chave(especie, l.sexo, faixa)
        contagem.setdefault(chave, []).append(l.sisbov)
        rotulos.setdefault(chave, _rotulo_categoria(l.sexo, faixa))
    return _montar_divergencias(necessidades, contagem, rotulos, sem_categoria)


def _avisos_do_vinculo(id_gta):
    with get_db_produtor(session['id_produtor']) as db:
        gta = db.get(Gta, id_gta)
        if not gta or gta.sentido != SENTIDO_FIXO:
            return []
        return _divergencias_do_vinculo(db, gta)


def _ler_gta_bruta(id_gta):
    """Dados crus da GTA (para o formulario de alteracao). None se nao e GTA de Saida da fazenda do usuario."""
    with get_db_produtor(session['id_produtor']) as db:
        gta = db.get(Gta, id_gta)
        if not gta or gta.sentido != SENTIDO_FIXO or not _propriedade_do_usuario(gta.id_propriedade):
            return None
        dados = SimpleNamespace(
            id=gta.id, id_propriedade=gta.id_propriedade, id_frigorifico=gta.id_frigorifico,
            id_parceiro_propriedade=gta.id_parceiro_propriedade, tipo_movimento=gta.tipo_movimento,
            uf_gta=gta.uf_gta, serie_gta=gta.serie_gta, numero_gta_sequencial=gta.numero_gta_sequencial,
            numero_gta_completo=gta.numero_gta_completo, qtde_animais_gta=str(gta.qtde_animais),
            data_emissao=_data_br(gta.data_emissao), data_validade=_data_br(gta.data_validade),
            data_saida=gta.data_saida, meio_transporte=gta.meio_transporte,
            numero_comunicado=gta.numero_comunicado, confirma_dados=False,
        )
        animais = [{'especie': a.especie, 'sexo': a.sexo, 'idade_meses': a.idade_meses, 'quantidade': a.quantidade}
                   for a in gta.animais]
        qtd_vinculados = db.query(Embarque).filter(Embarque.id_gta == gta.id).count()
    return dados, animais, qtd_vinculados


def _render_edicao(gta, animais, frigorifico, erro=None, especies=None, destino=None):
    id_propriedade = gta.id_propriedade
    _, propria = _buscar_dados_exibicao(session['id_produtor'], None, None, id_propriedade)
    _procedencia_com_oesa(propria, id_propriedade)
    avisos_topo = []
    com_comunicado = gta.numero_comunicado is not None
    uf_fixa = _uf_da_propriedade(id_propriedade) or (getattr(gta, 'uf_gta', '') or '')
    return render_template(
        'produtor/gta_saida_cadastro.html',
        erro=erro,
        modo_edicao=True,
        numero_atual=gta.numero_gta_completo,
        acao_form=f'/produtor/gta-saida/salvar-edicao/{gta.id}',
        avisos_topo=avisos_topo,
        frigo_travado=com_comunicado or (getattr(gta, 'tipo_movimento', None) in MOVIMENTOS_DESTINO),
        tipo_gta=_tipo_gta_do_movimento(getattr(gta, 'tipo_movimento', None)),
        destino=destino,
        travar_animais=com_comunicado,
        numero_comunicado_6=_numero_6(gta.numero_comunicado) if com_comunicado else '',
        uf_fixa=uf_fixa,
        data_saida_txt=_data_br(getattr(gta, 'data_saida', None)) if getattr(gta, 'data_saida', None) else '',
        procedencia=propria,
        gta=gta,
        animais=animais or [],
        frigorifico=frigorifico,
        id_propriedade=int(id_propriedade),
        uf_fazenda=_uf_da_propriedade(id_propriedade),
        faixas_idade=FAIXAS_IDADE,
        especies=especies if especies is not None else carregar_especies(),
        sexos=SEXOS_VALIDOS,
        url_inicio=_url_consulta_detalhe(gta.id_propriedade, gta.id),
        **_contexto_base(),
    )


def _json_data(valor):
    return valor.isoformat() if valor is not None else None


# -------------------------------------------------------
# GET /produtor/gta-saida/editar/<id>
# -------------------------------------------------------
@gta_saida.route('/produtor/gta-saida/editar/<int:id_gta>')
def editar(id_gta):
    if 'id_produtor' not in session:
        return redirecionar_home()
    achou = _ler_gta_bruta(id_gta)
    if not achou:
        return _negado()
    gta, animais, _ = achou
    if not _pode_alterar(gta.id_propriedade):
        return _sem_permissao()
    if not _gta_digitada_a_mao(gta):
        return redirect(_url_consulta_detalhe(gta.id_propriedade, id_gta))
    if gta.tipo_movimento in MOVIMENTOS_DESTINO:
        return _render_edicao(gta, animais, None,
                              destino=_dados_destino_transfer(gta.id_parceiro_propriedade, gta.id_propriedade,
                                                              _tipo_gta_do_movimento(gta.tipo_movimento)))
    return _render_edicao(gta, animais, _dados_frigorifico(gta.id_frigorifico))


# -------------------------------------------------------
# POST /produtor/gta-saida/salvar-edicao/<id>
# -------------------------------------------------------
@gta_saida.route('/produtor/gta-saida/salvar-edicao/<int:id_gta>', methods=['POST'])
def salvar_edicao(id_gta):
    if 'id_produtor' not in session:
        return redirecionar_home()
    achou = _ler_gta_bruta(id_gta)
    if not achou:
        return _negado()
    atual, _animais_atuais, _ = achou
    if not _pode_alterar(atual.id_propriedade):
        return _sem_permissao()
    if not _gta_digitada_a_mao(atual):
        return redirect(_url_consulta_detalhe(atual.id_propriedade, id_gta))

    id_produtor = session['id_produtor']
    id_propriedade = atual.id_propriedade
    com_comunicado = atual.numero_comunicado is not None

    # A UF da GTA de Saida e SEMPRE a da Propriedade (decisao do Benedito, 22/10/2026): o que vier do formulario e ignorado.
    uf_gta = (_uf_da_propriedade(id_propriedade) or atual.uf_gta or '').strip().upper()
    serie_gta = request.form.get('serie_gta', '').strip().upper()
    numero = ''.join(c for c in request.form.get('numero_gta_sequencial', '') if c.isdecimal())
    if numero:
        numero = numero.zfill(6)
    data_emissao_str = request.form.get('data_emissao', '').strip()
    data_validade_str = request.form.get('data_validade', '').strip()
    meio_transporte = request.form.get('meio_transporte', '').strip().upper()
    qtde_str = request.form.get('qtde_animais_gta', '').strip()
    confirma_dados = request.form.get('confirma_dados') == 'on'

    especies = carregar_especies()
    codigos_especie = codigos_validos(especies)
    animais = _ler_animais_do_formulario(especies)
    if com_comunicado:
        # Com Comunicado as categorias e a quantidade NAO mudam aqui (troca de animal = Substituicao / Troca depois do Comunicado).
        animais = [dict(a) for a in _animais_atuais]
        qtde_str = atual.qtde_animais_gta
    soma_animais = sum(a['quantidade'] for a in animais)
    # Com Comunicado o Frigorifico nao muda (o Comunicado e por frigorifico); sem Comunicado vale o escolhido na tela.
    transfer = atual.tipo_movimento in MOVIMENTOS_DESTINO
    id_frigorifico = atual.id_frigorifico if (com_comunicado or transfer) else request.form.get('id_frigorifico', '').strip()
    frigorifico = _dados_frigorifico(id_frigorifico) if (id_frigorifico and not transfer) else None
    destino = (_dados_destino_transfer(atual.id_parceiro_propriedade, id_propriedade, _tipo_gta_do_movimento(atual.tipo_movimento)) if transfer else None)   # destino travado na alteracao

    tentativa = SimpleNamespace(
        id=atual.id, id_propriedade=id_propriedade, numero_gta_completo=atual.numero_gta_completo,
        numero_comunicado=atual.numero_comunicado, id_frigorifico=atual.id_frigorifico, data_saida=atual.data_saida,
        tipo_movimento=atual.tipo_movimento, id_parceiro_propriedade=atual.id_parceiro_propriedade,
        uf_gta=uf_gta, serie_gta=serie_gta, numero_gta_sequencial=numero,
        data_emissao=data_emissao_str, data_validade=data_validade_str,
        meio_transporte=meio_transporte, qtde_animais_gta=qtde_str, confirma_dados=confirma_dados,
    )

    def _reexibir(mensagem):
        return _render_edicao(tentativa, animais, frigorifico, erro=mensagem, especies=especies, destino=destino)

    if not frigorifico and not com_comunicado and not transfer:
        return _reexibir('Escolha o Frigorífico de destino!')
    if not uf_gta or len(uf_gta) != 2:
        return _reexibir('UF da GTA é obrigatória!')
    if not serie_gta or len(serie_gta) != tamanho_serie_gta(uf_gta) or not serie_gta.isalpha():
        return _reexibir(mensagem_serie_gta(uf_gta))
    if not numero or len(numero) != 6:
        return _reexibir('Número da GTA é obrigatório e deve ter 6 dígitos!')

    with get_db_produtor(id_produtor) as db:
        existente = buscar_gta_duplicada(db, uf_gta, serie_gta, numero, SENTIDO_FIXO, id_ignorar=atual.id)
        msg_dup = mensagem_gta_duplicada(existente) if existente else None
    if msg_dup:
        return _reexibir(msg_dup)

    if atual.tipo_movimento == TIPO_MOVIMENTO_POSSE:
        meio_transporte = MEIO_NAO_SE_APLICA   # s115 - mesma Propriedade: nao ha transporte
    if not meio_transporte or (meio_transporte not in MEIOS_TRANSPORTE_VALIDOS and meio_transporte != MEIO_NAO_SE_APLICA):
        return _reexibir('Selecione o Meio de Transporte!')
    try:
        qtde_gta = int(qtde_str)
        if qtde_gta <= 0:
            raise ValueError()
    except ValueError:
        return _reexibir('Quantidade de Animais na GTA é obrigatória e deve ser maior que zero!')

    if not data_emissao_str:
        return _reexibir('Data de Emissão é obrigatória!')
    try:
        data_emissao = datetime.strptime(data_emissao_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data de Emissão incorreta! Use o formato dd/mm/aaaa.')
    if data_emissao > date.today():
        return _reexibir(f'Data de Emissão não pode ser uma data futura (hoje é {date.today().strftime("%d/%m/%Y")})! '
                         f'Confira o dia, o mês e o ano digitados.')
    if not data_validade_str:
        return _reexibir('Data de Validade é obrigatória!')
    try:
        data_validade = datetime.strptime(data_validade_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data de Validade incorreta! Use o formato dd/mm/aaaa.')
    if data_validade < data_emissao:
        return _reexibir('Data de Validade não pode ser anterior à Data de Emissão!')
    # A Data de Saida (digitada no Vincular GTA) precisa continuar dentro da validade - mesma regra do Vincular.
    if atual.data_saida and not (data_emissao <= atual.data_saida <= data_validade):
        return _reexibir(f'A Data de Saída desta GTA ({_data_br(atual.data_saida)}) ficaria fora da validade '
                         f'({_data_br(data_emissao)} a {_data_br(data_validade)}). Ajuste as datas.')

    if not animais:
        return _reexibir('Informe ao menos uma categoria de Animais!')
    for animal in animais:
        if animal['especie'] not in codigos_especie:
            return _reexibir('Selecione a Espécie em todas as categorias de Animais.')
        if animal['sexo'] not in SEXOS_VALIDOS:
            return _reexibir('Selecione o Sexo em todas as categorias de Animais.')
        if animal['idade_meses'] not in FAIXAS_IDADE:
            return _reexibir('Selecione a Idade em todas as categorias de Animais.')
        if animal['quantidade'] <= 0:
            return _reexibir('Quantidade deve ser maior que zero em todas as categorias de Animais.')
    if soma_animais != qtde_gta:
        if soma_animais < qtde_gta:
            return _reexibir(f'Falta incluir {qtde_gta - soma_animais} animal(is) para bater com a Quantidade declarada ({qtde_gta}).')
        return _reexibir(f'A soma das categorias ({soma_animais}) excede a Quantidade declarada na GTA ({qtde_gta}). Confira os valores.')
    if not confirma_dados:
        return _reexibir('Confirme que os dados foram conferidos antes de salvar!')

    # ---------------------------------------------------
    # Tudo validado - grava (uma transacao so: GTA, categorias, copias do Comunicado e Log).
    # ---------------------------------------------------
    novo_completo = f'{uf_gta}{serie_gta}{numero}'
    agora_impresso = False
    with get_db_produtor(id_produtor) as db:
        try:
            gta = (db.query(Gta).filter(Gta.id == atual.id, Gta.sentido == SENTIDO_FIXO,
                                        Gta.id_propriedade == int(id_propriedade)).with_for_update().first())
            if not gta:
                return _negado()
            com_comunicado = gta.numero_comunicado is not None     # confere de novo, ja com a linha travada
            id_frigo_final = gta.id_frigorifico if com_comunicado else (frigorifico['id'] if frigorifico else gta.id_frigorifico)
            numero_antigo = gta.numero_gta_completo

            novos = {
                'uf_gta': uf_gta, 'serie_gta': serie_gta, 'numero_gta_sequencial': numero,
                'numero_gta_completo': novo_completo, 'qtde_animais': qtde_gta,
                'data_emissao': data_emissao, 'data_validade': data_validade,
                'meio_transporte': meio_transporte, 'id_frigorifico': id_frigo_final,
            }
            antes, depois = {}, {}
            for campo, valor_novo in novos.items():
                valor_antigo = getattr(gta, campo)
                if valor_antigo != valor_novo:
                    antes[campo] = _json_data(valor_antigo) if isinstance(valor_antigo, date) else valor_antigo
                    depois[campo] = _json_data(valor_novo) if isinstance(valor_novo, date) else valor_novo
                    setattr(gta, campo, valor_novo)

            antigas = list(gta.animais)
            antigas_dict = [_linha_para_dict(a) for a in antigas]
            antigas_ids = [a.id for a in antigas]
            mudou_categoria = (sorted((a.especie, a.sexo, a.idade_meses, int(a.quantidade)) for a in antigas)
                               != sorted((a['especie'], a['sexo'], a['idade_meses'], int(a['quantidade'])) for a in animais))
            if mudou_categoria:
                for a in antigas:
                    db.delete(a)
                db.flush()
                novas_linhas = []
                for animal in animais:
                    nova = GtaAnimal(id_gta=gta.id, especie=animal['especie'], sexo=animal['sexo'],
                                     idade_meses=animal['idade_meses'], quantidade=animal['quantidade'])
                    db.add(nova)
                    novas_linhas.append(nova)
                db.flush()

            if not antes and not mudou_categoria:
                session['caixa_gta_alterada'] = {'id': atual.id, 'numero': atual.numero_gta_completo, 'mudancas': [],
                                                 'comunicado': '', 'reimprimir': False}
                return redirect(f'/produtor/gta-saida/alterada/{atual.id}')     # nada mudou: nao grava nada

            # ---- Com Comunicado: atualiza as copias da GTA (Comunicado, animais e movimentacao) ----
            copias = {}
            if com_comunicado:
                n6 = _numero_6(gta.numero_comunicado)
                copias['tb_2011'] = (db.query(ComunicadoSaida).filter(ComunicadoSaida.id_gta == gta.id)
                                     .update({'gta_numero': novo_completo, 'gta_data_emissao': data_emissao,
                                              'gta_data_validade': data_validade}, synchronize_session=False))
                copias['tb_2002'] = (db.query(SaidaAnimal).filter(SaidaAnimal.id_gta == gta.id)
                                     .update({'gta_saida': novo_completo, 'gta_saida_emissao': data_emissao,
                                              'gta_saida_validade': data_validade, 'gta_saida_animais': qtde_gta},
                                             synchronize_session=False))
                copias['tb_2017'] = (db.query(Movimentacao).filter(
                    Movimentacao.id_propriedade == int(id_propriedade), Movimentacao.numero_comunicado == n6,
                    Movimentacao.tipo_saida == _tipo_saida_da_gta(gta.tipo_movimento), Movimentacao.gta_saida == numero_antigo)
                    .update({'gta_saida': novo_completo, 'gta_saida_emissao': data_emissao,
                             'gta_saida_validade': data_validade, 'gta_saida_animais': qtde_gta},
                            synchronize_session=False))
                agora_impresso = db.query(ComunicadoSaida.id).filter(
                    ComunicadoSaida.id_gta == gta.id, ComunicadoSaida.status == 'IMPRESSO').first() is not None

            # ---- Log de Operacoes (so historico) ----
            partes = []
            if antes:
                partes.append('campos: ' + ', '.join(sorted(antes.keys())))
            if mudou_categoria:
                partes.append('categorias de animais')
            descricao = f'Alterou a GTA de Saída {numero_antigo}'
            if numero_antigo != novo_completo:
                descricao += f' (agora {novo_completo})'
            descricao += ' — ' + '; '.join(partes)
            if com_comunicado:
                descricao += (f'. Comunicado nº {n6} atualizado ({copias["tb_2002"]} animal(is))'
                              + ('; já impresso: reimprimir' if agora_impresso else ''))
            id_operacao = registrar_operacao(db, id_usuario=session.get('usuario_id'), id_propriedade=int(id_propriedade),
                                             modulo=MODULO_LOG_ALTERAR, descricao=descricao[:255])
            if antes:
                registrar_item(db, id_operacao, 'tb_4001_gta', gta.id, 'UPDATE', antes, depois)
            if mudou_categoria:
                for linha_antiga, id_antigo in zip(antigas_dict, antigas_ids):
                    registrar_item(db, id_operacao, 'tb_4001_gta_animais', id_antigo, 'DELETE', linha_antiga, None)
                for nova in novas_linhas:
                    registrar_item(db, id_operacao, 'tb_4001_gta_animais', nova.id, 'INSERT', None,
                                   {'especie': nova.especie, 'sexo': nova.sexo, 'idade_meses': nova.idade_meses,
                                    'quantidade': nova.quantidade})
            id_gta_gravada = gta.id          # guardado ANTES do commit
            resumo_caixa = {
                'id': id_gta_gravada, 'numero': novo_completo,
                'mudancas': _mudancas_para_caixa(antes, depois,
                                                 antigas_dict if mudou_categoria else None,
                                                 [{'sexo': a['sexo'], 'idade_meses': a['idade_meses'], 'quantidade': a['quantidade']}
                                                  for a in animais] if mudou_categoria else None),
                'comunicado': _numero_6(gta.numero_comunicado) if com_comunicado else '',
                'reimprimir': bool(agora_impresso),
            }
            db.commit()
        except IntegrityError as erro_banco:
            db.rollback()
            if not eh_violacao_unicidade_gta(erro_banco):
                raise
            return _reexibir('Esta GTA acabou de ser cadastrada por outra pessoa. '
                             'Não é permitido cadastrar a mesma GTA duas vezes.')

    session['caixa_gta_alterada'] = resumo_caixa
    return redirect(f'/produtor/gta-saida/alterada/{id_gta_gravada}')


# -------------------------------------------------------
# Caixa de Sucesso do Alterar (v1.6.0)
# -------------------------------------------------------
ROTULO_CAMPO_ALTERADO = {
    'uf_gta': 'UF', 'serie_gta': 'Série', 'numero_gta_sequencial': 'Número', 'numero_gta_completo': 'GTA',
    'data_emissao': 'Emissão', 'data_validade': 'Validade', 'meio_transporte': 'Meio de Transporte',
    'qtde_animais': 'Quantidade de animais', 'id_frigorifico': 'Frigorífico',
}
ROTULO_MEIO = {'NAO_SE_APLICA': 'Não se aplica', 'RODOVIARIO': 'Rodoviário', 'COMITIVA': 'A Pé (Comitiva / Tocada)', 'FLUVIAL_MARITIMO': 'Fluvial / Marítimo',
               'FERROVIARIO': 'Ferroviário', 'AEREO': 'Aéreo'}
CAMPOS_SO_DETALHE = {'serie_gta', 'numero_gta_sequencial', 'uf_gta'}      # ja aparecem no 'GTA' (numero completo)


def _texto_valor_alterado(campo, valor):
    if valor is None or valor == '':
        return '-'
    if campo in ('data_emissao', 'data_validade'):
        try:
            return datetime.strptime(str(valor)[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
        except ValueError:
            return str(valor)
    if campo == 'meio_transporte':
        return ROTULO_MEIO.get(valor, str(valor))
    return str(valor)


def _resumo_categorias(linhas):
    return ', '.join(f"{l.get('quantidade')} {str(l.get('sexo') or '').lower()} de {l.get('idade_meses')}" for l in linhas) or '-'


def _mudancas_para_caixa(antes, depois, antigas, novas):
    mudancas = []
    for campo in ('numero_gta_completo', 'data_emissao', 'data_validade', 'meio_transporte', 'qtde_animais', 'id_frigorifico'):
        if campo in antes:
            if campo == 'id_frigorifico':
                mudancas.append({'campo': ROTULO_CAMPO_ALTERADO[campo], 'antes': None, 'depois': 'alterado'})
            else:
                mudancas.append({'campo': ROTULO_CAMPO_ALTERADO[campo], 'antes': _texto_valor_alterado(campo, antes[campo]),
                                 'depois': _texto_valor_alterado(campo, depois[campo])})
    if antigas is not None:
        mudancas.append({'campo': 'Categorias de animais', 'antes': _resumo_categorias(antigas), 'depois': _resumo_categorias(novas)})
    return mudancas


@gta_saida.route('/produtor/gta-saida/alterada/<int:id_gta>')
def alterada(id_gta):
    if 'id_produtor' not in session:
        return redirecionar_home()
    achou = _carregar_gta_saida(id_gta)
    if not achou:
        return _negado()
    gta, _ = achou
    resumo = session.pop('caixa_gta_alterada', None)
    url_gta = _url_consulta_detalhe(gta.id_propriedade, gta.id)
    if not resumo or resumo.get('id') != id_gta:
        return redirect(url_gta)                       # recarregou a pagina: a caixa ja foi vista
    avisos = []
    if resumo.get('reimprimir'):
        avisos.append(f'Esta GTA está no Comunicado nº {resumo["comunicado"]}, que já foi impresso. Imprima de novo (Reimpressão) '
                      f'e substitua as vias já entregues.')
    elif resumo.get('comunicado'):
        avisos.append(f'Esta GTA está no Comunicado nº {resumo["comunicado"]}: os dados dele já foram atualizados. '
                      f'Se for imprimir, use a versão nova.')
    nada = not resumo.get('mudancas')
    return render_caixa_sucesso(
        _contexto_base(),
        titulo='Nada foi alterado.' if nada else 'GTA alterada com sucesso!',
        subtitulo=resumo['numero'],
        mudancas=resumo.get('mudancas'),
        avisos=avisos,
        notas=[] if nada else ['O que mudou ficou registrado no Log de Operações.'],
        botoes=[{'texto': 'Ver GTA', 'url': url_gta, 'primario': True},
                {'texto': 'Voltar à lista', 'url': _url_consulta_lista(gta.id_propriedade), 'primario': False}],
        url_voltar=url_gta, icone='&#9989;' if not nada else '&#8505;&#65039;', titulo_pagina='Orion SISBOV — GTA alterada',
    )


# -------------------------------------------------------
# GET/POST /produtor/gta-saida/excluir/<id>
# -------------------------------------------------------
def _bloqueios_exclusao(db, gta):
    """Motivos que impedem excluir (vazio = pode excluir)."""
    motivos = []
    if gta.numero_comunicado is not None:
        motivos.append(f'Esta GTA já está no Comunicado nº {_numero_6(gta.numero_comunicado)}. Para excluir, o Comunicado '
                       f'não pode existir.')
    elif db.query(ComunicadoSaida.id).filter(ComunicadoSaida.id_gta == gta.id).first() is not None:
        motivos.append('Esta GTA está em um Comunicado de Saída.')
    qtd = db.query(Embarque).filter(Embarque.id_gta == gta.id).count()
    if qtd:
        motivos.append(f'Esta GTA tem {qtd} animal(is) vinculado(s). Desvincule antes (Vincular GTA / Embarque > '
                       f'Ver GTAs já vinculadas > Desvincular).')
    return motivos


def _tela_excluir(gta_ns, motivos, erro=None, concluido=False):
    return render_template(
        'produtor/gta_saida_excluir.html',
        gta=gta_ns, motivos=motivos, erro=erro, concluido=concluido,
        url_detalhe=_url_consulta_detalhe(gta_ns.id_propriedade, gta_ns.id),
        url_lista=_url_consulta_lista(gta_ns.id_propriedade),
        url_acao=f'{URL_EXCLUIR}{gta_ns.id}',
        **_contexto_base(),
    )


@gta_saida.route('/produtor/gta-saida/excluir/<int:id_gta>', methods=['GET', 'POST'])
def excluir(id_gta):
    if 'id_produtor' not in session:
        return redirecionar_home()
    achou = _carregar_gta_saida(id_gta)
    if not achou:
        return _negado()
    gta_ns, _animais_ns = achou
    if not _pode_alterar(gta_ns.id_propriedade):
        return _sem_permissao()
    if not _gta_digitada_a_mao(gta_ns):
        return redirect(_url_consulta_detalhe(gta_ns.id_propriedade, id_gta))
    id_produtor = session['id_produtor']

    if request.method == 'GET':
        with get_db_produtor(id_produtor) as db:
            gta = db.get(Gta, id_gta)
            motivos = _bloqueios_exclusao(db, gta)
        return _tela_excluir(gta_ns, motivos)

    # ---- POST: confere tudo de novo, com a linha travada ----
    if request.form.get('confirmo') != '1':
        return _tela_excluir(gta_ns, [], erro='Marque "Confirmo a exclusão desta GTA" para excluir.')
    with get_db_produtor(id_produtor) as db:
        try:
            gta = (db.query(Gta).filter(Gta.id == id_gta, Gta.sentido == SENTIDO_FIXO,
                                        Gta.id_propriedade == int(gta_ns.id_propriedade)).with_for_update().first())
            if not gta:
                return _negado()
            motivos = _bloqueios_exclusao(db, gta)
            if motivos:
                return _tela_excluir(gta_ns, motivos)
            numero_gta = gta.numero_gta_completo
            descricao = (f'Excluiu a GTA de Saída {numero_gta} ({gta.qtde_animais} animal(is), emissão '
                         f'{_data_br(gta.data_emissao)})')
            id_operacao = registrar_operacao(db, id_usuario=session.get('usuario_id'),
                                             id_propriedade=int(gta.id_propriedade), modulo=MODULO_LOG_EXCLUIR,
                                             descricao=descricao[:255])
            for a in list(gta.animais):
                registrar_item(db, id_operacao, 'tb_4001_gta_animais', a.id, 'DELETE', _linha_para_dict(a), None)
                db.delete(a)
            db.flush()
            registrar_item(db, id_operacao, 'tb_4001_gta', gta.id, 'DELETE', _linha_para_dict(gta), None)
            db.delete(gta)
            db.commit()
        except IntegrityError:
            db.rollback()
            return _tela_excluir(gta_ns, [], erro='Não foi possível excluir: a GTA ainda está ligada a outros registros.')
    return render_caixa_sucesso(
        _contexto_base(),
        titulo='GTA excluída.', subtitulo=gta_ns.numero_gta_completo, icone='&#128465;&#65039;',
        notas=['A linha inteira da GTA ficou guardada no Log de Operações (quem excluiu e quando).',
               'Não existe desfazer: para voltar, a GTA precisa ser lançada de novo.'],
        botoes=[{'texto': 'Voltar à lista', 'url': _url_consulta_lista(gta_ns.id_propriedade), 'primario': True}],
        url_voltar=_url_consulta_lista(gta_ns.id_propriedade), titulo_pagina='Orion SISBOV — GTA excluída',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\gta_saida.py
# =========================================================
