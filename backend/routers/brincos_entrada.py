# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\brincos_entrada.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-08-31 18:32 -03
# ATUALIZADO EM: 2026-11-16 10:40 -03
# VERSAO: 1.9.0
# v1.9.0: Sessao 128 (2026-11-16 10:40 -03) - AUDITORIA ETAPA 7b (Regra #57/#73): a trava _propriedade_permitida() passa a conferir tambem que o Produtor do par Propriedade+Produtor e o Produtor da sessao (antes so conferia a Propriedade). REVERSAO: .bak_antes_etapa7b.
# v1.8.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (5 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.7.0: Sessao 122 (2026-11-12 19:00 -03) - Auditoria Etapa 4 (Entradas): limite de 50.000 brincos por entrada (e de Solicitacao/Caixas), trava da Propriedade contra duplo clique, Fornecedor conferido. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Fluxo completo de Entrada de Brincos (Sessao 042), primeiro
#     modulo real do Hub de Brincos a ser construido, seguindo a
#     ordem ja combinada com Benedito (Fornecedor de Brincos ja
#     existe/cadastrado -> Entrada de Brincos, este arquivo).
#
#     Mesmo padrao arquitetural ja fechado em gta_manual.py:
#       1. /produtor/brincos-entrada/iniciar - resolve Propriedade
#          E Produtor, reaproveitando
#          auth.buscar_pares_propriedade_produtor() e o template
#          compartilhado produtor/selecionar_propriedade_produtor.html
#          (0 pares -> erro; 1 par -> segue direto; 2+ -> tela de
#          selecao via /produtor/selecionar-vinculo).
#       2. /produtor/brincos-entrada/nova - formulario completo,
#          com Propriedade/Produtor ja resolvidos e exibidos so
#          para conferencia (bloco readonly, mesmo espirito do
#          bloco Destino em gta_manual_cadastro.html).
#       3. /produtor/brincos-entrada/salvar - valida e grava DE
#          VERDADE em tb_3007_brincos_entrada (1 linha, cabecalho
#          do lote) E tb_7017_entrada_brincos_rfid (N linhas, uma
#          por SISBOV individual, do codigo_inicial ao
#          codigo_final) - AMBAS gravadas SIMULTANEAMENTE, na
#          mesma transacao (decisao de arquitetura fechada com
#          Benedito, Sessao 042).
#
#     REGRAS DE NEGOCIO (todas fechadas com Benedito, Sessao 042):
#       - data_fabricacao DEVE ser ESTRITAMENTE maior que
#         solicitacao_data (nao pode ser igual).
#       - data_nf DEVE ser maior OU IGUAL a solicitacao_data.
#       - impressao_pia DEVE ser maior OU IGUAL a data_fabricacao.
#       - total_caixas (Qtde de Caixas) DEVE ser >= 1.
#       - qtde_entrada (Qtde de Brincos) DEVE ser >= 1.
#       - codigo_inicial: EXATAMENTE 15 digitos numericos (novo
#         formato SISBOV, sem digito verificador separado).
#       - codigo_final = codigo_inicial + (qtde_entrada - 1),
#         calculado no servidor, nunca digitado pelo usuario -
#         (v1.3.0) nunca pode passar de 15 digitos.
#       - (v1.3.0) Nenhum SISBOV da faixa pode ja existir na
#         tb_7017 deste Produtor (qualquer Propriedade dele).
#       - sequencia (tb_3007.sequencia): numero sequencial 1,2,3...
#         relativo a CADA Propriedade - calculado como
#         MAX(sequencia) WHERE id_propriedade + 1.
#       - saldo nasce igual a qtde_entrada, qtde_saida nasce 0.
#       - data_entrada = data do Windows no momento do Salvar
#         (date.today(), nao datetime.now()).
#       - cpf_produtor: resolvido a partir do Produtor escolhido no
#         passo 1, gravado tanto no cabecalho (tb_3007) quanto
#         replicado em CADA linha da tb_7017 gerada.
#       - id_responsavel (tb_3007): usuario logado
#         (session['usuario_id']) - campo Responsavel REMOVIDO da
#         tela.
#       - Cada linha da tb_7017 nasce so com: sisbov, manejo (6
#         ultimos digitos do sisbov), cpf_produtor, id_propriedade,
#         id_lote_entrada - status nasce NULO (Disponivel).
#       - Campo "Controle" do desenho original do GERAS: REMOVIDO
#         de vez.
#       - Nao ha checagem de duplicidade GLOBAL de numero SISBOV
#         entre schemas de Produtores diferentes nesta versao
#         (decisao de Benedito: "vamos aguardar").
#
#     Fabricantes (tb_1021_fabricantes_brincos) vivem no schema
#     PUBLIC (compartilhado entre Produtores) - dropdown desta
#     tela consulta direto essa tabela (Fabricante.ativo=True).
#
#     v1.0.0: Criacao do modulo (Sessao 042, 31/08/2026, 18:32 -03).
#     v1.1.0: Sessao 043 (01/09/2026, 11:50 -03) - Correcao de bug
#         real encontrado na revisao da tela: a validacao do
#         Nro Nota Fiscal ainda limitava a 6 digitos
#         (len(nota_fiscal) > 6), mas o template
#         brincos_entrada_cadastro.html v1.1.0 (Sessao 043) ja
#         aceita ate 10 digitos no campo - sem esta correcao, o
#         usuario digitava ate 10 e o servidor rejeitava acima de
#         6. Limite alinhado para 10 nesta versao (constante
#         TAMANHO_MAX_NOTA_FISCAL). Nenhuma outra mudanca de regra
#         de negocio.
#     v1.2.0: Sessao 044 (02/09/2026, 16:00 -03) - Cadeia de
#         navegacao "Voltar" corrigida (Benedito, teste real,
#         mesma correcao aplicada em todos os modulos do Hub de
#         Brincos): (1) chamadas a selecionar_propriedade_produtor.
#         html agora passam voltar='/produtor/hub/brincos' (antes
#         o template compartilhado ia sempre para /produtor/home);
#         (2) nova funcao _url_voltar_formulario() calcula
#         dinamicamente o destino do Voltar/Cancelar da tela de
#         formulario: volta para /produtor/brincos-entrada/iniciar
#         (re-exibe a Selecao de Propriedade) se o usuario tem 2+
#         pares, ou direto para o Hub se tem so 1 par (a tela de
#         selecao nunca apareceu nesse caso).
#     v1.3.0: Sessao 079 (24/09/2026, 13:00 -03) - BLINDAGEM da
#         Entrada de Brincos (pedido de Benedito apos teste real
#         em que "nada apareceu" ao Salvar e a entrada nao foi
#         gravada). Mudancas:
#           - BUG REAL (mesmo vicio da Sessao 078): lote.id era
#             lido DEPOIS do db.commit() - o objeto expira e a
#             releitura acontece sem o schema do Produtor ("nao
#             existe a relacao"), estourando erro APOS gravar.
#             Agora o id e guardado ANTES do commit.
#           - SEGURANCA: nova() e salvar() conferem se o
#             id_propriedade pertence aos pares do usuario
#             logado (NOVA funcao _propriedade_permitida()) -
#             antes o servidor aceitava qualquer numero vindo do
#             formulario.
#           - NOVA regra: Nro Final nunca passa de 15 digitos.
#           - NOVA regra: brinco repetido - se QUALQUER SISBOV da
#             faixa ja existir na tb_7017 deste Produtor, nada e
#             gravado e a mensagem lista os primeiros numeros
#             repetidos (NOVA funcao _sisbovs_ja_cadastrados()).
#           - Mensagem "Fornecedor selecionado e invalido" trocada
#             para "incorreto" (Regras.txt secao 4).
#         A tela (brincos_entrada_cadastro.html v1.4.0) passa a
#         validar tudo ao vivo e pedir confirmacao antes de
#         gravar - o servidor continua reconferindo tudo.
#     v1.4.0: Sessao 091 (08/10/2026, 18:30 -03) - FAZENDA EM USO (Regra de Ouro #13):
#         Com fazenda em uso a tela "Selecionar Propriedade" e pulada: o iniciar()
#         abre direto a tela do modulo. O Voltar vai ao Hub de Brincos (sem passar pela
#         selecao). TRAVA: Propriedade da URL diferente da fazenda em uso e negada
#         (nunca le nem grava). Sem fazenda em uso o comportamento anterior permanece.
#         Leitura e gravacao dos dados intactas. REVERSAO: devolver a versao anterior.
#     v1.5.0: Sessao 094 (12/10/2026, 15:50 -03) - BRINCO EM DOIS MODELOS (demanda do MAPA).
#         ANTIGO (comeca com 105): o usuario digita 14 digitos e o DV e calculado; a faixa soma na
#         base de 14 e recalcula o DV de cada brinco; grava 15 digitos; manejo = 6 antes do DV.
#         NOVO (outro inicio): 15 digitos sequenciais, sem DV; manejo = 6 ultimos. Regras em
#         regras_sisbov.py v1.5.0 (numero, faixa e manejo vem de la - nada calculado aqui).
#         NOVA rota GET /produtor/brincos-entrada/calcular-faixa (a tela mostra Nro Final e DV ao
#         vivo, sem repetir o algoritmo em JavaScript). Brinco repetido no modelo antigo compara
#         pela BASE de 14 digitos (qualquer DV). tb_3007 e tb_7017 guardam sempre 15 digitos.
#         Sem coluna nova no banco. REVERSAO: devolver brincos_entrada.py.bak_antes_s094.
#     v1.6.0: Sessao 094 (12/10/2026, 17:00 -03) - ENTRADA NO DESFAZER (Operacoes Recentes).
#         salvar() passa a registrar a operacao (modulo 'brincos_entrada') com 1 item INSERT
#         do lote (tb_3007), na mesma transacao. Regras do desfazer em log_operacoes.py v1.8.0.
#         Lotes gravados antes desta versao nao tem registro e so saem pelo banco.
#         REVERSAO: devolver brincos_entrada.py.bak_antes_desfazer.
# =========================================================

from datetime import date, datetime
from types import SimpleNamespace
from flask import Blueprint, jsonify, render_template, request, redirect, session

from sqlalchemy import func, text
from sqlalchemy.orm import Session
from backend.utils.gravacao_nascimento import TRAVA_BRINCOS_NASC

from backend.database import engine
from backend.models import Propriedade, Produtor, PropriedadeProdutor
from backend.models.tb_1021_fabricantes_brincos import Fabricante
from backend.models.tb_3007_brincos_entrada import BrincoEntrada
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils import regras_sisbov
from backend.utils.log_operacoes import registrar_operacao, registrar_item


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
brincos_entrada = Blueprint('brincos_entrada', __name__)


# -------------------------------------------------------
# v1.4.0 - TRAVA DA FAZENDA EM USO (Regra de Ouro #13): a Propriedade da URL
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
# v1.5.0 - o brinco tem 2 modelos (antigo 105 + DV, novo 15 digitos).
# Todas as regras vivem em regras_sisbov.py; aqui so os numeros que a
# tela precisa para limitar a digitacao.
# -------------------------------------------------------
REGRAS_SISBOV_TELA = SimpleNamespace(
    prefixo_antigo = regras_sisbov.PREFIXO_SISBOV_ANTIGO,
    tamanho_antigo = regras_sisbov.TAMANHO_BASE_SISBOV_ANTIGO,
    tamanho_novo   = regras_sisbov.TAMANHO_SISBOV,
)

# -------------------------------------------------------
# Tamanho maximo do Nro da Nota Fiscal (Sessao 043 - alinhado
# com o campo da tela, que aceita ate 10 digitos).
# -------------------------------------------------------
TAMANHO_MAX_NOTA_FISCAL = 10
# Etapa 4 (item 1): limites de seguranca. Quantidade absurda (um zero a mais) monta a lista inteira na memoria e trava o servidor;
# Solicitacao e Caixas sao Integer no banco (acima de 2.147.483.647 daria erro 500).
LIMITE_BRINCOS_ENTRADA = 50000
LIMITE_INTEIRO_BANCO = 2147483647
LIMITE_CAIXAS = 99999

# -------------------------------------------------------
# v1.3.0 - quantos SISBOVs repetidos aparecem na mensagem de
# erro (o resto vira "e mais N").
# -------------------------------------------------------
LIMITE_REPETIDOS_MENSAGEM = 10


# -------------------------------------------------------
# Rota: GET /produtor/brincos-entrada/iniciar — ponto de partida
# do fluxo, MESMO padrao ja usado em gta_manual.iniciar() (P-036).
# -------------------------------------------------------
@brincos_entrada.route('/produtor/brincos-entrada/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            titulo='Selecionar Propriedade',
            proximo='/produtor/brincos-entrada/nova',
            campo_propriedade='id_propriedade',
            voltar='/produtor/hub/brincos',
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='brincos',
        )

    # v1.4.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/brincos-entrada/nova?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/brincos-entrada/nova?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        titulo='Selecionar Propriedade',
        proximo='/produtor/brincos-entrada/nova',
        campo_propriedade='id_propriedade',
        voltar='/produtor/hub/brincos',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )


# -------------------------------------------------------
# Funcao auxiliar: busca os dados de cabecalho (Propriedade +
# Produtor vinculado) para exibicao/conferencia na tela.
# -------------------------------------------------------
def _buscar_dados_cabecalho(id_produtor, id_propriedade):
    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade)) if id_propriedade else None
        produtor    = db.get(Produtor, int(id_produtor)) if id_produtor else None

        if not propriedade or not produtor:
            return None

        return SimpleNamespace(
            id_propriedade   = propriedade.id,
            propriedade_nome = propriedade.nome,
            municipio        = propriedade.municipio,
            uf               = propriedade.uf,
            id_produtor      = produtor.id,
            produtor_nome    = produtor.nome,
            cpf_produtor     = produtor.cpf_cnpj,
        )


# -------------------------------------------------------
# Funcao auxiliar (NOVA, v1.3.0): o id_propriedade informado
# pertence mesmo aos pares Propriedade/Produtor do usuario
# logado? O servidor nunca confia so no numero que veio da URL
# ou do formulario.
# -------------------------------------------------------
def _propriedade_permitida(id_propriedade):
    if not str(id_propriedade).isdecimal():
        return False
    if _fora_da_fazenda_em_uso(id_propriedade):
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    return str(id_propriedade) in {str(par.id_propriedade) for par in pares if str(par.id_produtor) == str(session.get('id_produtor'))}   # v1.9.0 - Produtor do par = Produtor da sessao (Etapa 7b)


# -------------------------------------------------------
# Funcao auxiliar (NOVA, v1.3.0): devolve (quantidade, lista dos
# primeiros SISBOVs) da faixa que JA existem na tb_7017 deste
# Produtor (qualquer Propriedade dele). Comparacao por texto
# funciona porque todo SISBOV tem exatamente 15 digitos (com
# zeros a esquerda).
# -------------------------------------------------------
def _sisbovs_ja_cadastrados(db, codigo_inicial, codigo_final, modelo):
    # v1.5.0 - modelo antigo: o DV muda a ordem do texto, entao compara pela
    # BASE de 14 digitos (qualquer DV): de base_inicial+'0' ate base_final+'9'.
    if modelo == regras_sisbov.MODELO_SISBOV_ANTIGO:
        tamanho_base = regras_sisbov.TAMANHO_BASE_SISBOV_ANTIGO
        codigo_inicial = codigo_inicial[:tamanho_base] + '0'
        codigo_final   = codigo_final[:tamanho_base] + '9'
    filtro = (
        db.query(EntradaBrincoRfid.sisbov)
        .filter(EntradaBrincoRfid.sisbov >= codigo_inicial)
        .filter(EntradaBrincoRfid.sisbov <= codigo_final)
    )
    quantidade = filtro.count()
    primeiros = [linha[0] for linha in filtro.order_by(EntradaBrincoRfid.sisbov).limit(LIMITE_REPETIDOS_MENSAGEM).all()]
    return quantidade, primeiros


# -------------------------------------------------------
# Funcao auxiliar: lista os Fabricantes ativos
# (tb_1021_fabricantes_brincos, schema public) para o dropdown de
# Fornecedor.
# -------------------------------------------------------
def _listar_fabricantes_ativos():
    with Session(engine) as db:
        fabricantes = db.query(Fabricante).filter_by(ativo=True).order_by(Fabricante.nome).all()
        return [SimpleNamespace(id=f.id, nome=f.nome) for f in fabricantes]


# -------------------------------------------------------
# Funcao auxiliar: URL de "Voltar" da tela 04 (formulario) - volta
# para a tela 03 (Selecionar Propriedade) se o usuario tem 2+
# pares Propriedade/Produtor (ela foi mostrada antes), ou direto
# para o Hub de Brincos se so tem 1 par (a tela 03 nunca apareceu)
# - cadeia de navegacao correta confirmada por Benedito, Sessao
# 044: 04 -> 03 (se existiu) -> 01-Hub.
# -------------------------------------------------------
def _url_voltar_formulario():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return '/produtor/brincos-entrada/iniciar'
    return '/produtor/hub/brincos'


# -------------------------------------------------------
# Funcao auxiliar: tela do formulario so com mensagem de erro
# (sem formulario) - usada quando a Propriedade nao pode ser
# resolvida.
# -------------------------------------------------------
def _tela_so_erro(mensagem, url_voltar):
    return render_template(
        'produtor/brincos_entrada_cadastro.html',
        erro=mensagem,
        cabecalho=None,
        fabricantes=[],
        lote=None,
        url_voltar=url_voltar,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )


# -------------------------------------------------------
# Rota: GET /produtor/brincos-entrada/nova?id_propriedade=X —
# formulario completo de Entrada de Brincos.
# -------------------------------------------------------
@brincos_entrada.route('/produtor/brincos-entrada/nova')
def nova():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    url_voltar = _url_voltar_formulario()
    id_propriedade = request.args.get('id_propriedade', '')

    if not id_propriedade:
        return _tela_so_erro('Propriedade não informada. Reinicie o fluxo pelo Hub de Brincos.', url_voltar)

    # v1.3.0 - a Propriedade precisa ser do usuario logado.
    if not _propriedade_permitida(id_propriedade):
        return _tela_so_erro('Propriedade não pertence ao seu cadastro. Reinicie o fluxo pelo Hub de Brincos.', url_voltar)

    cabecalho = _buscar_dados_cabecalho(session['id_produtor'], id_propriedade)

    if cabecalho is None:
        return _tela_so_erro('Propriedade ou Produtor não encontrado(s). Reinicie o fluxo pelo Hub de Brincos.', url_voltar)

    fabricantes = _listar_fabricantes_ativos()

    return render_template(
        'produtor/brincos_entrada_cadastro.html',
        erro=None,
        cabecalho=cabecalho,
        fabricantes=fabricantes,
        lote=None,
        regras_sisbov=REGRAS_SISBOV_TELA,
        url_voltar=url_voltar,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )


# -------------------------------------------------------
# Rota: POST /produtor/brincos-entrada/salvar — valida e grava DE
# VERDADE em tb_3007 (1 linha) + tb_7017 (N linhas), na MESMA
# transacao, dentro do schema do Produtor logado. Blocos:
#   1. Permissao + cabecalho.
#   2. Leitura do formulario.
#   3. Validacoes (param no primeiro erro, reexibindo a tela).
#   4. Calculos (codigo_final) + limite de 15 digitos.
#   5. Gravacao (com checagem de brinco repetido antes).
# -------------------------------------------------------
@brincos_entrada.route('/produtor/brincos-entrada/salvar', methods=['POST'])
def salvar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    # ---- 1. Permissao + cabecalho ----
    url_voltar = _url_voltar_formulario()
    id_produtor    = session['id_produtor']
    id_propriedade = request.form.get('id_propriedade', '')

    if not _propriedade_permitida(id_propriedade):
        return _tela_so_erro('Propriedade não pertence ao seu cadastro. Reinicie o fluxo pelo Hub de Brincos.', url_voltar)

    cabecalho = _buscar_dados_cabecalho(id_produtor, id_propriedade)
    fabricantes = _listar_fabricantes_ativos()

    # ---- 2. Leitura do formulario ----
    solicitacao_nro_str   = ''.join(c for c in request.form.get('solicitacao_nro', '') if c.isdecimal())
    solicitacao_data_str  = request.form.get('solicitacao_data', '').strip()
    data_fabricacao_str   = request.form.get('data_fabricacao', '').strip()
    nota_fiscal           = ''.join(c for c in request.form.get('nota_fiscal', '') if c.isdecimal())
    data_nf_str           = request.form.get('data_nf', '').strip()
    total_caixas_str      = request.form.get('total_caixas', '').strip()
    impressao_pia_str     = request.form.get('impressao_pia', '').strip()
    id_fabricante_str     = request.form.get('id_fabricante', '').strip()
    qtde_entrada_str      = request.form.get('qtde_entrada', '').strip()
    codigo_inicial        = ''.join(c for c in request.form.get('codigo_inicial', '') if c.isdecimal())
    confirma_dados        = request.form.get('confirma_dados') == 'on'

    lote_tentativa = SimpleNamespace(
        solicitacao_nro   = solicitacao_nro_str,
        solicitacao_data  = solicitacao_data_str,
        data_fabricacao   = data_fabricacao_str,
        nota_fiscal       = nota_fiscal,
        data_nf           = data_nf_str,
        total_caixas      = total_caixas_str,
        impressao_pia     = impressao_pia_str,
        id_fabricante     = id_fabricante_str,
        qtde_entrada      = qtde_entrada_str,
        codigo_inicial    = codigo_inicial,
        confirma_dados    = confirma_dados,
    )

    def _reexibir(mensagem_erro):
        return render_template(
            'produtor/brincos_entrada_cadastro.html',
            erro=mensagem_erro,
            cabecalho=cabecalho,
            fabricantes=fabricantes,
            lote=lote_tentativa,
            regras_sisbov=REGRAS_SISBOV_TELA,
            url_voltar=url_voltar,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='brincos',
        )

    if cabecalho is None:
        return _reexibir('Propriedade ou Produtor não encontrado(s). Reinicie o fluxo pelo Hub de Brincos.')

    # ---- 3. Validacoes de obrigatoriedade / formato ----
    if not solicitacao_nro_str:
        return _reexibir('Número de Solicitação é obrigatório e deve conter apenas números!')
    if int(solicitacao_nro_str) > LIMITE_INTEIRO_BANCO:
        return _reexibir('Número de Solicitação grande demais! Confira o número digitado.')

    if not solicitacao_data_str:
        return _reexibir('Data de Solicitação é obrigatória!')
    try:
        solicitacao_data = datetime.strptime(solicitacao_data_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data de Solicitação incorreta! Use o formato dd/mm/aaaa.')

    if not data_fabricacao_str:
        return _reexibir('Data de Fabricação é obrigatória!')
    try:
        data_fabricacao = datetime.strptime(data_fabricacao_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data de Fabricação incorreta! Use o formato dd/mm/aaaa.')

    if data_fabricacao <= solicitacao_data:
        return _reexibir('Data de Fabricação deve ser posterior à Data de Solicitação!')

    if not nota_fiscal:
        return _reexibir('Número da Nota Fiscal é obrigatório e deve conter apenas números!')
    if len(nota_fiscal) > TAMANHO_MAX_NOTA_FISCAL:
        return _reexibir(f'Número da Nota Fiscal excede o limite de {TAMANHO_MAX_NOTA_FISCAL} dígitos!')

    if not data_nf_str:
        return _reexibir('Data da Nota Fiscal é obrigatória!')
    try:
        data_nf = datetime.strptime(data_nf_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data da Nota Fiscal incorreta! Use o formato dd/mm/aaaa.')

    if data_nf < solicitacao_data:
        return _reexibir('Data da Nota Fiscal não pode ser anterior à Data de Solicitação!')

    try:
        total_caixas = int(total_caixas_str)
        if total_caixas < 1:
            raise ValueError()
    except ValueError:
        return _reexibir('Quantidade de Caixas é obrigatória e deve ser maior ou igual a 1!')
    if total_caixas > LIMITE_CAIXAS:
        return _reexibir(f'Quantidade de Caixas acima do limite ({LIMITE_CAIXAS})! Confira o número digitado.')

    if not impressao_pia_str:
        return _reexibir('Data de Impressão da PIA é obrigatória!')
    try:
        impressao_pia = datetime.strptime(impressao_pia_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data de Impressão da PIA incorreta! Use o formato dd/mm/aaaa.')

    if impressao_pia < data_fabricacao:
        return _reexibir('Data de Impressão da PIA não pode ser anterior à Data de Fabricação!')

    if not id_fabricante_str:
        return _reexibir('Selecione o Fornecedor (Fabricante)!')
    try:
        id_fabricante = int(id_fabricante_str)
    except ValueError:
        return _reexibir('Fornecedor selecionado é incorreto!')
    if id_fabricante not in {f.id for f in fabricantes}:   # Etapa 4 (item 10)
        return _reexibir('Fornecedor selecionado é incorreto! Escolha um da lista.')

    try:
        qtde_entrada = int(qtde_entrada_str)
        if qtde_entrada < 1:
            raise ValueError()
    except ValueError:
        return _reexibir('Quantidade de Brincos é obrigatória e deve ser maior ou igual a 1!')
    if qtde_entrada > LIMITE_BRINCOS_ENTRADA:
        return _reexibir(
            f'Quantidade de Brincos acima do limite de {LIMITE_BRINCOS_ENTRADA:,} por entrada! '.replace(',', '.') +
            'Confira o número digitado (um zero a mais?). Para entradas maiores, faça mais de um lançamento.')

    if not codigo_inicial:
        return _reexibir('Número Inicial do Brinco é obrigatório!')

    if not confirma_dados:
        return _reexibir('Confirme que os dados foram conferidos antes de salvar!')

    # ---- 4. Calculos no servidor (nunca digitados) ----
    # v1.5.0 - modelo, DV, Nro Final e a lista de brincos vem de
    # regras_sisbov.py. Daqui em diante codigo_inicial e codigo_final tem
    # sempre 15 digitos (antigo: base + DV). O que o usuario digitou
    # continua guardado em lote_tentativa para reexibir a tela.
    try:
        modelo_sisbov, codigo_inicial, codigo_final = regras_sisbov.extremos_faixa_sisbov(codigo_inicial, qtde_entrada)
        faixa_sisbov = regras_sisbov.gerar_faixa_sisbov(lote_tentativa.codigo_inicial, qtde_entrada)
    except ValueError as erro_faixa:
        return _reexibir(str(erro_faixa))

    # ---- 5. Gravacao - tb_3007 + N linhas de tb_7017, na MESMA
    # transacao, dentro do schema do Produtor logado ----
    with get_db_produtor(id_produtor) as db:
        # Etapa 4 (item 2): trava da Propriedade - duplo clique / 2 abas com a mesma faixa nao gravam 2 vezes nem repetem a sequencia.
        db.execute(text('SELECT pg_advisory_xact_lock(:ns, :id)'), {'ns': TRAVA_BRINCOS_NASC, 'id': int(id_propriedade)})
        # v1.3.0 - brinco repetido: nada e gravado se QUALQUER
        # SISBOV da faixa ja existir neste Produtor.
        qtde_repetidos, repetidos = _sisbovs_ja_cadastrados(db, codigo_inicial, codigo_final, modelo_sisbov)
        if qtde_repetidos:
            lista = ', '.join(repetidos)
            if qtde_repetidos > len(repetidos):
                lista += f' ... e mais {qtde_repetidos - len(repetidos)}'
            return _reexibir(f'{qtde_repetidos} brinco(s) desta faixa já cadastrado(s) — nada foi gravado: {lista}')

        proxima_sequencia = (
            db.query(func.max(BrincoEntrada.sequencia))
            .filter_by(id_propriedade=int(id_propriedade))
            .scalar()
        ) or 0
        proxima_sequencia += 1

        lote = BrincoEntrada(
            id_propriedade    = int(id_propriedade),
            cpf_produtor      = cabecalho.cpf_produtor,
            id_fabricante     = id_fabricante,
            id_responsavel    = session.get('usuario_id'),
            sequencia         = proxima_sequencia,
            codigo_inicial    = codigo_inicial,
            codigo_final      = codigo_final,
            nota_fiscal       = nota_fiscal,
            data_nf           = data_nf,
            qtde_entrada      = qtde_entrada,
            data_entrada      = date.today(),
            qtde_saida        = 0,
            saldo             = qtde_entrada,
            solicitacao_nro   = int(solicitacao_nro_str),
            solicitacao_data  = solicitacao_data,
            data_fabricacao   = data_fabricacao,
            impressao_pia     = impressao_pia,
            total_caixas      = total_caixas,
        )
        db.add(lote)
        db.flush()  # garante lote.id antes de criar as linhas da 7017

        for numero_sisbov in faixa_sisbov:
            db.add(EntradaBrincoRfid(
                id_propriedade  = int(id_propriedade),
                id_lote_entrada = lote.id,
                sisbov          = numero_sisbov,
                manejo          = regras_sisbov.manejo_do_sisbov(numero_sisbov),
                cpf_produtor    = cabecalho.cpf_produtor,
                status          = None,
            ))

        # v1.6.0 - registro para o Desfazer (Operacoes Recentes).
        id_operacao = registrar_operacao(
            db,
            id_usuario=session['usuario_id'],
            id_propriedade=int(id_propriedade),
            modulo='brincos_entrada',
            descricao=f'Entrada de brincos - NF {nota_fiscal or "s/n"} - '
                      f'{qtde_entrada} brincos ({codigo_inicial} a {codigo_final})',
        )
        registrar_item(
            db, id_operacao, 'tb_3007_brincos_entrada', lote.id, 'INSERT',
            None, {'codigo_inicial': codigo_inicial, 'codigo_final': codigo_final,
                   'qtde_entrada': qtde_entrada},
        )

        # v1.3.0 - BUG REAL corrigido: o id e guardado ANTES do
        # commit (regra da Sessao 078 - depois do commit nao se le
        # mais nada dos objetos do banco).
        id_lote_gravado = lote.id

        db.commit()

    return redirect(f'/produtor/brincos-entrada/sucesso/{id_lote_gravado}')


# -------------------------------------------------------
# Rota (NOVA, v1.5.0): GET /produtor/brincos-entrada/calcular-faixa
# ?inicial=...&qtde=... - so calcula, nao grava nada. A tela chama a
# cada digitacao para mostrar o Nro Final e o DV (modelo antigo) sem
# repetir o algoritmo em JavaScript. Resposta JSON:
#   {ok: true, modelo, inicial, final}  (inicial e final com 15 digitos)
#   {ok: false, erro: "mensagem pronta"}
# -------------------------------------------------------
@brincos_entrada.route('/produtor/brincos-entrada/calcular-faixa')
def calcular_faixa():
    if 'id_produtor' not in session:
        return jsonify({'ok': False, 'erro': 'Sessão expirada. Entre novamente.'}), 401

    inicial = ''.join(c for c in request.args.get('inicial', '') if c.isdecimal())
    qtde    = request.args.get('qtde', '').strip()
    try:
        modelo, primeiro, ultimo = regras_sisbov.extremos_faixa_sisbov(inicial, qtde)
    except ValueError as erro:
        return jsonify({'ok': False, 'erro': str(erro)})
    return jsonify({'ok': True, 'modelo': modelo, 'inicial': primeiro, 'final': ultimo})


# -------------------------------------------------------
# Rota: GET /produtor/brincos-entrada/sucesso/<id> — confirmacao
# simples apos a gravacao (so leitura, sem commit).
# -------------------------------------------------------
@brincos_entrada.route('/produtor/brincos-entrada/sucesso/<int:id_lote>')
def sucesso(id_lote):
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    with get_db_produtor(session['id_produtor']) as db:
        lote = db.get(BrincoEntrada, id_lote)

    return render_template(
        'produtor/brincos_entrada_sucesso.html',
        lote=lote,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincos',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\brincos_entrada.py
# =========================================================