# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\routers
# MODULO:       backend\routers\comunicado_entrada.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-09-14 17:10 -03
# ATUALIZADO EM: 2026-11-19 12:30 -03
# VERSAO: 1.10.1
# v1.10.1: Sessao 133 (2026-11-19 12:30 -03) - CARGA (serie CAR) excluida de forma EXPLICITA das GTAs a comunicar (antes so ficava de fora pelo status NAO_APLICA). Sem mudanca de comportamento hoje. REVERSAO: .bak_antes_s133_carga.
# v1.10.0: Sessao 128 (2026-11-16 10:40 -03) - AUDITORIA ETAPA 7b (Regra #57/#73): a trava _propriedade_permitida() passa a conferir tambem que o Produtor do par Propriedade+Produtor e o Produtor da sessao (antes so conferia a Propriedade). REVERSAO: .bak_antes_etapa7b.
# v1.9.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (2 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Modulo "Gerar Comunicado" do Hub de Entrada (5o card,
#     familia Brincagem/GTA/Comunicado). Alinhamento de negocio
#     fechado na Sessao 052 (14/09/2026), a partir do documento
#     real Anexo XIX (Formulario para Comunicado de Entrada) e do
#     dicionario de dados real "2012 Com Entrada" mostrado por
#     Benedito.
#
#     ESCOPO DESTE ARQUIVO: so a GERACAO (grava os registros
#     oficiais, atribui numero_comunicado). A IMPRESSAO do PDF
#     (Anexo XIX) e a REIMPRESSAO ficam em modulos SEPARADOS
#     ("Impressão Comunicado" / "Reimpressão Comunicado",
#     construidos na Sessao 054) - Gerar so grava o registro com
#     status='ABERTO'; e a Impressao que monta o PDF (ReportLab) e
#     grava status='IMPRESSO' + data_envio.
#
#     REGRAS DE NEGOCIO (fechadas com Benedito, Sessao 052):
#       - Gatilho: GTA com tb_4001_gta.status_brincagem='BRINCADO'
#         E ainda sem numero_comunicado (tb_4001_gta.
#         numero_comunicado IS NULL) - "em aberto".
#       - NASCIMENTO NAO TEM COMUNICADO (v1.4.0, Benedito, Sessao
#         081): a Notificacao de Nascimento e gravada na propria
#         tb_4001_gta (tipo_movimento='NASCTO-DESMAME'), ja nasce
#         BRINCADO e sem numero_comunicado - por isso e EXCLUIDA
#         explicitamente aqui. Filtro "diferente de NASCTO-
#         DESMAME" (e nao "igual a COMPRA") de proposito: uma
#         futura Entrada por Transferencia com GTA continua
#         entrando sem mexer de novo neste arquivo.
#       - Agrupamento: por PROCEDENCIA (id_parceiro_propriedade),
#         dentro da Propriedade/Produtor DESTINO escolhida na tela
#         de selecao (Padrao Reutilizavel Nº1) - GTAs de outros
#         Produtores/Propriedades NUNCA entram, mesmo que estejam
#         brincadas e abertas.
#       - Lotes de ATE 6 GTAs por Comunicado, ordenados por
#         gta_data_emissao ASC (a mais antiga primeiro) - "a
#         primeira que entra, desde que brincada, e a primeira que
#         sai" (Benedito). Mais de 6 GTAs da mesma procedencia ->
#         vira mais de um Comunicado (lotes de 6, na mesma ordem).
#       - numero_comunicado: sequencial por Propriedade destino
#         (MAX + 1), com pg_advisory_xact_lock (mesmo mecanismo ja
#         usado para numero_pia em brincagem_sequencial.py) - "o
#         primeiro que clicar leva o numero" (Benedito).
#       - O MESMO numero_comunicado e gravado, na mesma transacao,
#         em: tb_2012_com_entrada (1 linha por GTA do lote),
#         tb_2001.numero_comunicado e tb_7017.numero_comunicado
#         (nivel do animal/brinco, localizados pelo SISBOV das
#         entradas da GTA), tb_4001_gta.numero_comunicado (nivel
#         da GTA), tb_5001_brincagem.numero_comunicado (v1.2.0 -
#         animais que vieram da Brincagem com Leitor/Bastao via
#         Vincular GTA), tb_2017_movimentacoes.numero_comunicado
#         (v1.3.0 - SO a linha de ENTRADA do kardex, texto de 6
#         digitos, ex. "000002") e tb_7002_pia.numero_pia recebe
#         UPDATE com este MESMO valor (Benedito: "o numero do
#         Comunicado sera o numero da PIA").
#       - data_liberacao_abate e data_brincagem da linha de
#         tb_2012_com_entrada sao COPIADAS de tb_2001 - nunca
#         recalculadas aqui.
#       - Tela de confirmacao OBRIGATORIA antes de gravar (previa).
#       - NAO entra no Log de Operacoes/Desfazer (decisao explicita
#         de Benedito, Sessao 052: numeracao oficial sequencial -
#         desfazer criaria buraco na sequencia). A propria
#         tb_2012_com_entrada (data_inclusao, status, data_envio) e
#         a trilha de auditoria.
#       - LIMITACAO ACEITA: a previa pode diferir levemente da
#         geracao real se alguma GTA mudar de estado entre as duas
#         (gerar() RECALCULA os lotes, nunca confia no cliente).
#
#     v1.0.0: Criacao do modulo (Sessao 052).
#     v1.1.0: Sessao 054 (16/09/2026, 12:25 -03) - BUG REAL (P-036):
#             iniciar() contava PRODUTORES DISTINTOS em vez de PARES
#             Propriedade+Produtor. Corrigido para len(pares).
#     v1.2.0: Sessao 079 (24/09/2026, 19:15 -03) - AUDITORIA no 1o
#             ciclo completo (Vincular GTA -> Gerar -> Imprimir):
#               - ELO QUE FALTAVA: tb_5001_brincagem.numero_
#                 comunicado nunca era preenchido (o modulo foi
#                 construido antes da Brincagem com Leitor/Bastao
#                 existir; o proprio model da tb_5001 ja dizia que o
#                 campo e preenchido "quando o ciclo for fechado").
#                 Agora recebe o numero junto com as demais tabelas
#                 (filtro por id_gta). Animais da Brincagem
#                 Sequencial nao passam pela tb_5001 - o UPDATE
#                 simplesmente nao encontra linhas, sem efeito.
#               - PRECISAO NA tb_7017: o UPDATE filtrava SO pelo
#                 SISBOV - o historico da tb_7017 pode ter o mesmo
#                 SISBOV em linhas antigas (chip/brinco reutilizado,
#                 ver brincagem_bastao.py) e elas seriam
#                 "carimbadas" tambem. Agora filtra tambem pela
#                 Propriedade destino e SO linhas ainda sem
#                 numero_comunicado.
#               - SEGURANCA: confirmar() e gerar() conferem se a
#                 Propriedade pertence ao usuario logado (NOVA
#                 funcao _propriedade_permitida()).
#             Regras de numeracao, agrupamento e lotes intactas.
#     v1.3.0: Sessao 080 (25/09/2026) - RECONSTRUIDA na Sessao 081:
#             a v1.3.0 foi entregue na Sessao 080 mas NUNCA chegou
#             a C:\orion (conferencia de versoes da Sessao 081
#             encontrou a v1.2.0 em uso). Refeita a partir da
#             Referencia do Sistema 080, secao 115.2. Regra de
#             Benedito: cada movimentacao do animal e uma linha
#             propria na tb_2017 (kardex), com o SEU documento - o
#             numero do Comunicado de Entrada vai SO na linha de
#             ENTRADA, como texto de 6 digitos ("000002",
#             tb_2017.numero_comunicado e String(6)). NOVO bloco g)
#             em gerar(). Filtro preciso para nao carimbar linha
#             errada: mesmo SISBOV + mesma Propriedade +
#             gta_entrada = numero desta GTA + tipo_saida vazio
#             (linha de Entrada) + numero_comunicado ainda vazio.
#     v1.4.0: Sessao 081 (28/09/2026, 20:45 -03) - Notificacao de
#             Nascimento EXCLUIDA do Gerar Comunicado (ver REGRAS
#             DE NEGOCIO acima): _montar_lotes_pendentes() ganhou o
#             filtro tipo_movimento diferente de 'NASCTO-DESMAME'.
#             Protecao criada ANTES da primeira Notificacao ser
#             gravada. Nenhuma outra mudanca de logica.
#     v1.5.0: Sessao 090 (08/10/2026, 07:42 -03) - FAZENDA EM USO (Regra de Ouro
#             #13, Lote 2 - Comunicados). Tres pontos:
#               - iniciar(): com fazenda em uso valida (auth.
#                 resolver_fazenda_em_uso), PULA a tela "Selecionar
#                 Propriedade" e abre a tela de Confirmacao direto na fazenda em uso. Sem
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
#     v1.6.0: Sessao 094 (12/10/2026, 20:30 -03) - AUDITORIA DE COMPRAS: gerar() pega a trava da Propriedade ANTES de calcular os lotes pendentes (dois cliques
#             ou duas abas geravam dois Comunicados para as mesmas GTAs). Nenhuma outra mudanca.
#             REVERSAO: devolver .bak_antes_auditoria_compras.
#     v1.7.0: Sessao 104 (23/10/2026, 12:40 -03) - TRILHA DE AUDITORIA: gerar() registra no Log de Operacoes um item por Comunicado
#             (quem gerou e quando), modulo 'comunicado_entrada', so-historico (sem Desfazer). REVERSAO: .bak_antes_s104i.
#     v1.8.0: Sessao 106 (26/10/2026, 10:30 -03) - TRAVA DO BRETE NA GERACAO (regra do Benedito: "o Comunicado de Entrada so
#             pode acontecer depois que os animais foram identificados"). Caso real: a GTA AMA111118 (6 animais lancados pelo
#             escritorio na Brincagem Sequencial, conferido_brete = False) entrou no Comunicado nº 2 so porque a GTA ja estava
#             BRINCADO. Agora _montar_lotes_pendentes() so deixa entrar a GTA cujos animais estao TODOS conferidos no brete
#             (tb_2001.conferido_brete = True, via conferencia_compra.contadores_gta). A GTA com animal pendente - ou sem
#             nenhum animal na tb_2001 - fica de fora e a Confirmacao avisa "aguardando leitura no brete". gerar() recalcula
#             dentro da trava da Propriedade (mesma funcao), entao duas abas ou dois cliques nao furam a regra. Numeracao,
#             lotes de 6, agrupamento por procedencia e gravacao nas tabelas intactos. REVERSAO: .bak_antes_s106a.
# =========================================================

from flask import Blueprint, render_template, redirect, request, session
from sqlalchemy import text, func

from backend.models import Propriedade, Produtor
from backend.models.tb_4001_gta import Gta
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_5001_brincagem import Brincagem
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.models.tb_7002_pia import Pia
from backend.models.tb_2012_com_entrada import ComunicadoEntrada
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.conferencia_compra import contadores_gta   # v1.8.0 - (total, conferidos) dos animais da GTA
from backend.utils.log_operacoes import registrar_operacao, registrar_item   # v1.7.0 - trilha de auditoria


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
comunicado_entrada = Blueprint('comunicado_entrada', __name__)


# -------------------------------------------------------
# Constantes do modulo.
# -------------------------------------------------------
MAXIMO_GTAS_POR_COMUNICADO = 6

# v1.3.0 - tb_2017_movimentacoes.numero_comunicado e String(6):
# o numero vai com zeros a esquerda (ex.: 2 -> "000002").
TAMANHO_NUMERO_COMUNICADO_2017 = 6

# v1.4.0 - Notificacao de Nascimento mora na tb_4001_gta mas NAO
# tem Comunicado de Entrada (ver DESCRICAO).
TIPO_MOVIMENTO_SEM_COMUNICADO = 'NASCTO-DESMAME'


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
URL_INICIAR = '/produtor/comunicado-entrada/iniciar'


# -------------------------------------------------------
# Trava de permissao (usada por TODAS as rotas do modulo).
# 1) a Propriedade tem de ser de um par do usuario logado;
# 2) FAZENDA EM USO (Sessao 090): se ha uma e ela e DIFERENTE da Propriedade
#    da URL (trocada em outra aba, por exemplo), devolve False - o chamador
#    manda para o iniciar(), que abre a fazenda em uso. Nada e lido, gerado
#    nem gravado numa fazenda enquanto a faixa mostra outra.
# -------------------------------------------------------
def _propriedade_permitida(id_propriedade):
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if int(id_propriedade) not in {int(par.id_propriedade) for par in pares if str(par.id_produtor) == str(session.get('id_produtor'))}:   # v1.10.0 - Produtor do par = Produtor da sessao (Etapa 7b)
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
# Funcao auxiliar - monta os lotes (ate 6 GTAs cada) agrupados por
# procedencia, para a Propriedade destino informada. Usada TANTO
# pela tela de confirmacao (previa) QUANTO pela geracao real
# (recalculada de novo no momento do POST).
# v1.4.0: Notificacoes de Nascimento ficam de fora.
# v1.8.0: so entra GTA com TODOS os animais conferidos no brete. Devolve
#         (lotes, gtas_aguardando): gtas_aguardando = lista de dicts
#         {'gta', 'total', 'conferidos'} das GTAs BRINCADO que ficaram de fora
#         (animal sem leitura no brete, ou GTA sem nenhum animal na tb_2001).
# -------------------------------------------------------
def _montar_lotes_pendentes(db, id_propriedade):
    gtas_pendentes = (
        db.query(Gta)
        .filter(
            Gta.id_propriedade == id_propriedade,
            Gta.status_brincagem == 'BRINCADO',
            Gta.numero_comunicado.is_(None),
            Gta.tipo_movimento != TIPO_MOVIMENTO_SEM_COMUNICADO,
            Gta.serie_gta != 'CAR',   # v1.10.1 - a Carga nunca tem Comunicado
        )
        .order_by(Gta.data_emissao.asc(), Gta.id.asc())
        .all()
    )

    # v1.8.0 - TRAVA DO BRETE: separa as GTAs prontas das que aguardam leitura.
    gtas_prontas = []
    gtas_aguardando = []
    for gta in gtas_pendentes:
        total_animais, conferidos = contadores_gta(db, gta.id)
        if total_animais == 0 or conferidos < total_animais:
            gtas_aguardando.append({'gta': gta, 'total': total_animais, 'conferidos': conferidos})
        else:
            gtas_prontas.append(gta)

    # Agrupa por procedencia, preservando a ordem de data_emissao ASC.
    grupos_por_procedencia = {}
    for gta in gtas_prontas:
        grupos_por_procedencia.setdefault(gta.id_parceiro_propriedade, []).append(gta)

    lotes = []
    for id_parceiro_propriedade, lista_gtas in grupos_por_procedencia.items():
        for inicio in range(0, len(lista_gtas), MAXIMO_GTAS_POR_COMUNICADO):
            lotes.append({
                'id_parceiro_propriedade': id_parceiro_propriedade,
                'gtas': lista_gtas[inicio:inicio + MAXIMO_GTAS_POR_COMUNICADO],
            })

    return lotes, gtas_aguardando


# -------------------------------------------------------
# Rota: GET /produtor/comunicado-entrada/iniciar
# Padrao Reutilizavel Nº1 - Selecionar Propriedade/Produtor
# (len(pares), v1.1.0).
# -------------------------------------------------------
@comunicado_entrada.route('/produtor/comunicado-entrada/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            titulo='Gerar Comunicado — Selecionar Propriedade',
            proximo='/produtor/comunicado-entrada/confirmar',
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
        return redirect(f'/produtor/comunicado-entrada/confirmar?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/comunicado-entrada/confirmar?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        titulo='Gerar Comunicado — Selecionar Propriedade',
        proximo='/produtor/comunicado-entrada/confirmar',
        campo_propriedade='id_propriedade',
        voltar='/produtor/hub/entrada',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/comunicado-entrada/confirmar?id_propriedade=X
# Tela de confirmacao - mostra a PREVIA dos Comunicados que serao
# gerados (obrigatoria antes de gravar). Somente leitura.
# -------------------------------------------------------
@comunicado_entrada.route('/produtor/comunicado-entrada/confirmar')
def confirmar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade.isdecimal() or not _propriedade_permitida(id_propriedade):
        return redirect('/produtor/comunicado-entrada/iniciar')
    id_propriedade = int(id_propriedade)

    from backend.models.tb_parceiros_propriedades import ParceiroPropriedades

    with get_db_produtor(session['id_produtor']) as db:
        propriedade = db.get(Propriedade, id_propriedade)
        if not propriedade:
            return redirect('/produtor/comunicado-entrada/iniciar')

        lotes, gtas_aguardando = _montar_lotes_pendentes(db, id_propriedade)

        # v1.8.0 - GTAs que ficaram de fora por falta de leitura no brete (so exibicao).
        aguardando_exibicao = []
        for item in gtas_aguardando:
            aguardando_exibicao.append({
                'numero_gta_completo': item['gta'].numero_gta_completo,
                'total':               item['total'],
                'faltam':              item['total'] - item['conferidos'],
            })

        lotes_exibicao = []
        for lote in lotes:
            parceiro_propriedade = None
            if lote['id_parceiro_propriedade']:
                parceiro_propriedade = db.get(ParceiroPropriedades, lote['id_parceiro_propriedade'])
            parceiro = parceiro_propriedade.parceiro if parceiro_propriedade else None

            gtas_exibicao = []
            total_animais = 0
            for gta in lote['gtas']:
                total_animais += gta.qtde_animais
                gtas_exibicao.append({
                    'numero_gta_completo': gta.numero_gta_completo,
                    'data_emissao_br':     gta.data_emissao.strftime('%d/%m/%Y') if gta.data_emissao else '-',
                    'qtde_animais':        gta.qtde_animais,
                })

            lotes_exibicao.append({
                'procedencia_nome':            parceiro.nome if parceiro else '-',
                'procedencia_estabelecimento': parceiro_propriedade.estabelecimento if parceiro_propriedade else '-',
                'gtas':                        gtas_exibicao,
                'total_gtas':                  len(lote['gtas']),
                'total_animais':               total_animais,
            })

        return render_template(
            'produtor/comunicado_entrada_confirmar.html',
            propriedade=propriedade,
            lotes=lotes_exibicao,
            aguardando=aguardando_exibicao,   # v1.8.0
            id_propriedade=id_propriedade,
            url_voltar=_url_voltar(buscar_pares_propriedade_produtor(session['usuario_id'])),   # Sessao 090
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo='entrada',
        )


# -------------------------------------------------------
# Rota: POST /produtor/comunicado-entrada/gerar
# Geracao real - RECALCULA os lotes (nunca confia em lista vinda do
# cliente), grava tb_2012_com_entrada + atualiza 2001/7017/4001/
# 5001/7002/2017 - 1 transacao unica. Blocos por GTA:
#   a) linha da tb_2012;
#   b) numero_comunicado em 2001 (entradas da GTA);
#   c) 7017 - so linhas da Propriedade, sem comunicado ainda;
#   d) 4001 (GTA);
#   e) 5001 (v1.2.0 - brincagens vinculadas a esta GTA);
#   f) 7002 - numero_pia recebe o numero do Comunicado;
#   g) 2017 (v1.3.0) - SO a linha de ENTRADA do kardex, 6 digitos.
# -------------------------------------------------------
@comunicado_entrada.route('/produtor/comunicado-entrada/gerar', methods=['POST'])
def gerar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.form.get('id_propriedade', '')
    if not id_propriedade.isdecimal() or not _propriedade_permitida(id_propriedade):
        return redirect('/produtor/comunicado-entrada/iniciar')
    id_propriedade = int(id_propriedade)

    from backend.models.tb_parceiros_propriedades import ParceiroPropriedades

    with get_db_produtor(session['id_produtor']) as db:
        # v1.6.0 - a trava vem ANTES de calcular os lotes pendentes: quem chega depois
        # espera e ja enxerga o que o primeiro gerou (antes, dois cliques geravam dois
        # Comunicados para as mesmas GTAs). A trava vale ate o commit.
        db.execute(text('SELECT pg_advisory_xact_lock(:id_propriedade)'), {'id_propriedade': id_propriedade})

        lotes, _gtas_aguardando = _montar_lotes_pendentes(db, id_propriedade)   # v1.8.0 - so GTAs 100% conferidas no brete

        if not lotes:
            # Nada pendente (pode ter sido gerado por outra aba entre a
            # Confirmacao e este clique).
            return redirect(f'/produtor/comunicado-entrada/confirmar?id_propriedade={id_propriedade}')

        produtor_destino = db.get(Produtor, session['id_produtor'])

        numeros_gerados = []

        for lote in lotes:
            # Trava por Propriedade destino - "o primeiro que clicar
            # leva o numero" (Benedito).
            db.execute(text('SELECT pg_advisory_xact_lock(:id_propriedade)'), {'id_propriedade': id_propriedade})

            maximo_atual = (
                db.query(func.max(ComunicadoEntrada.numero_comunicado))
                .filter(ComunicadoEntrada.id_propriedade_destino == id_propriedade,
                        ComunicadoEntrada.tipo_entrada != 'TRANSFERENCIA',)   # v-s107: sequencia propria da Compra (a da Transferencia e separada)
                .scalar()
            )
            numero_comunicado = (maximo_atual or 0) + 1
            numeros_gerados.append(numero_comunicado)
            id_operacao_log = registrar_operacao(   # v1.7.0 - trilha: quem gerou e quando (sem Desfazer)
                db, id_usuario=session['usuario_id'], id_propriedade=id_propriedade, modulo='comunicado_entrada',
                descricao=(f'Comunicado de Entrada nº {str(numero_comunicado).zfill(6)} — GTA '
                           + ', '.join(g.numero_gta_completo for g in lote['gtas']))[:255])

            # v1.3.0 - texto de 6 digitos para o kardex (tb_2017).
            numero_comunicado_2017 = str(numero_comunicado).zfill(TAMANHO_NUMERO_COMUNICADO_2017)

            parceiro_propriedade = db.get(ParceiroPropriedades, lote['id_parceiro_propriedade']) if lote['id_parceiro_propriedade'] else None
            parceiro = parceiro_propriedade.parceiro if parceiro_propriedade else None

            for gta in lote['gtas']:
                entradas_gta = (
                    db.query(Entrada)
                    .filter_by(id_gta_entrada=gta.id)
                    .all()
                )
                sisbovs_gta = [entrada.sisbov for entrada in entradas_gta]

                # data_brincagem/liberacao_abate COPIADAS de tb_2001.
                data_brincagem_gta  = entradas_gta[0].data_brincagem if entradas_gta else None
                liberacao_abate_gta = entradas_gta[0].liberacao_abate if entradas_gta else None

                # ---- a) linha oficial da tb_2012 ----
                comunicado = ComunicadoEntrada(
                    id_propriedade_destino=id_propriedade,
                    cpf_cnpj_produtor_destino=produtor_destino.cpf_cnpj if produtor_destino else None,
                    numero_comunicado=numero_comunicado,
                    id_gta=gta.id,
                    gta_numero=gta.numero_gta_completo,
                    gta_data_emissao=gta.data_emissao,
                    gta_data_validade=gta.data_validade,
                    data_brincagem=data_brincagem_gta,
                    gta_data_entrega=gta.data_entrega,
                    qtd_animais=len(entradas_gta),
                    data_liberacao_abate=liberacao_abate_gta,
                    id_parceiro_propriedade=lote['id_parceiro_propriedade'],
                    cpf_cnpj_produtor_origem=parceiro.cpf_cnpj if parceiro else None,
                    tipo_entrada=gta.tipo_movimento,
                    status='ABERTO',
                )
                db.add(comunicado)
                db.flush()
                registrar_item(db, id_operacao_log, 'tb_2012_com_entrada', comunicado.id, 'INSERT', None,
                               {'numero_comunicado': numero_comunicado, 'gta_numero': gta.numero_gta_completo,
                                'animais': len(entradas_gta)})

                # ---- b) tb_2001 ----
                for entrada in entradas_gta:
                    entrada.numero_comunicado = numero_comunicado

                # ---- c) tb_7017 - v1.2.0: so da Propriedade destino e
                # so linhas ainda sem comunicado (historico antigo com
                # o mesmo SISBOV nao e tocado) ----
                if sisbovs_gta:
                    db.query(EntradaBrincoRfid).filter(
                        EntradaBrincoRfid.sisbov.in_(sisbovs_gta),
                        EntradaBrincoRfid.id_propriedade == id_propriedade,
                        EntradaBrincoRfid.numero_comunicado.is_(None),
                    ).update({'numero_comunicado': numero_comunicado}, synchronize_session=False)

                # ---- d) tb_4001 (GTA) ----
                gta.numero_comunicado = numero_comunicado

                # ---- e) tb_5001 - v1.2.0: elo que faltava ----
                db.query(Brincagem).filter(
                    Brincagem.id_gta == gta.id,
                    Brincagem.numero_comunicado.is_(None),
                ).update({'numero_comunicado': numero_comunicado}, synchronize_session=False)

                # ---- f) tb_7002 - numero_pia vira o numero oficial ----
                db.query(Pia).filter_by(id_gta=gta.id).update(
                    {'numero_pia': numero_comunicado}, synchronize_session=False
                )

                # ---- g) tb_2017 - v1.3.0: SO a linha de ENTRADA do
                # kardex desta GTA (cada movimentacao leva o SEU
                # documento - regra de Benedito). Texto de 6 digitos.
                if sisbovs_gta:
                    db.query(Movimentacao).filter(
                        Movimentacao.sisbov.in_(sisbovs_gta),
                        Movimentacao.id_propriedade == id_propriedade,
                        Movimentacao.gta_entrada == gta.numero_gta_completo,
                        Movimentacao.tipo_saida.is_(None),
                        Movimentacao.numero_comunicado.is_(None),
                    ).update({'numero_comunicado': numero_comunicado_2017}, synchronize_session=False)

            db.flush()

        # numeros_gerados ja esta pronto (lista de inteiros) - nada e
        # lido do banco depois do commit (regra da Sessao 078).
        db.commit()

    return render_template(
        'produtor/comunicado_entrada_sucesso.html',
        numeros_gerados=numeros_gerados,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\comunicado_entrada.py
# =========================================================