# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\nascimentos_periodo.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-02 17:00 -03
# ATUALIZADO EM: 2026-11-16 10:40 -03
# VERSAO: 1.9.0
# v1.9.0: Sessao 128 (2026-11-16 10:40 -03) - AUDITORIA ETAPA 7b (Regra #57/#73): a trava _propriedade_permitida() passa a conferir tambem que o Produtor do par Propriedade+Produtor e o Produtor da sessao (antes so conferia a Propriedade). REVERSAO: .bak_antes_etapa7b.
# v1.8.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (2 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.7.0: Sessao 123 (2026-11-13 19:25 -03) - AUDITORIA ETAPA 4 (2a passada): PDF do Numero de Controle (Notificacao de Nascimento) nao achada volta para a tela COM aviso (antes em silencio). REVERSAO: .bak_antes_etapa4b.
#
# DESCRICAO:
#     RELATORIO "Nascimentos por Periodo" - os animais nascidos e
#     identificados na propriedade (Nascimento/Desmame) numa janela de
#     Datas de Brincagem. Navegacao real (Regra de Ouro #7): Hub de
#     Entrada -> card "Nascimento / Desmame" -> sub-hub -> card
#     "Nascimentos por Periodo" (hubs.py v1.39.0) -> Selecionar
#     Propriedade (so com 2+ pares) -> TELA (filtro + resultado).
#
#     FONTE: tb_2001 (rebanho vivo) com tipo_entrada NASCTO-DESMAME e
#     Data de Brincagem dentro do periodo - ou seja, so os animais ja
#     EFETIVADOS em uma Notificacao (NAS). Leituras do brete ainda
#     pendentes, sem Notificacao, nao entram.
#
#     TELA: Data Inicial / Data Final (dd/mm/aaaa; padrao = do dia 1
#     do mes ate hoje), quadro-resumo (total, machos, femeas, CTH),
#     tabela por Notificacao e lista dos animais (ate 500 linhas na
#     tela; o PDF traz TODOS). PDF: backend/utils/pdf_nascimentos_
#     periodo.py (A4 paisagem). Colunas SEXO e RACA da tabela de animais
#     em MAIUSCULAS e SEM ACENTO (RACA = codigo da raca).
#     So leitura - nunca grava.
#
#     SEGURANCA: toda rota confere se a Propriedade da URL pertence
#     aos pares do usuario logado (_propriedade_permitida).
#
#     v1.0.0: Criacao do modulo (Sessao 084, 02/10/2026, 17:00 -03).
#     v1.1.0: Sessao 084 (02/10/2026, 18:00 -03) - NOVO relatorio "Nascimento
#             por Numero de Controle" (card do sub-hub, hubs.py v1.40.0), no
#             mesmo blueprint (sem registro novo no app.py): a tela escolhe
#             uma Notificacao (NAS) da Propriedade em lista e mostra os
#             animais dela; mesmo PDF (retrato). 3 rotas novas: controle_
#             iniciar(), controle_tela() e controle_pdf(). _buscar() ganha o
#             parametro opcional id_gta (filtra pela Notificacao em vez do
#             periodo). Nascimentos por Periodo SEM mudanca.
#     v1.2.0: Sessao 090 (08/10/2026, 07:33 -03) - FAZENDA EM USO (Regra de Ouro
#             #13, Lote 1 - Nascimento). Vale para os DOIS relatorios do modulo
#             (Nascimentos por Periodo e Nascimento por Numero de Controle):
#               - iniciar() / controle_iniciar(): com fazenda em uso valida
#                 (auth.resolver_fazenda_em_uso), PULAM a tela "Selecionar
#                 Propriedade" e abrem o relatorio direto na fazenda em uso. Sem
#                 fazenda em uso, ou com uma fazenda so, tudo igual a antes.
#               - VOLTAR: o destino passa a ser o Hub novo "Nascimento /
#                 Desmame" (/produtor/hub-novo/entrada-nascimento). Com fazenda
#                 em uso a selecao nao existe mais, entao nunca volta ao
#                 iniciar() (reabriria o relatorio: laco).
#               - TRAVA (_propriedade_permitida): se a Propriedade da URL for
#                 DIFERENTE da fazenda em uso (ex.: trocada em outra aba), a
#                 rota nao le nem gera PDF e manda para o iniciar() do proprio
#                 relatorio, que abre a fazenda em uso.
#             Nenhuma mudanca nas consultas, totais, filtros e PDFs.
#     v1.3.0: Sessao 095 (13/10/2026, 11:27 -03) - PADRAO DE DOWNLOAD: o PDF passa a ser entregue como DOWNLOAD (pasta Downloads do usuario)
#             e nao mais aberto direto na aba, igual aos demais relatorios do Orion (decisao de Benedito).
#             A tela avisa onde o arquivo fica. Unica mudanca: as_attachment=True.
#             REVERSAO: devolver .bak_antes_download_s095.
#     v1.4.0: Sessao 102 (21/10/2026, 10:10 -03) - PDF DE NASCIMENTOS POR PERIODO NO VISUAL DO MAGIC: pdf() passa a montar o
#             contexto novo (_contexto_magic: Produtor com CPF/CNPJ por fazenda, Inscr. Estadual, Cod. ERAS, NIRF, UF e os
#             animais agrupados por Codigo Interno, com Especie/Aptidao/Raca em codigo). A tela e o Nascimento por Numero de
#             Controle ficam IGUAIS. Nenhuma consulta existente mudou. REVERSAO: devolver .bak_antes_visual_magic_s102.
#     v1.5.0: Sessao 102 (21/10/2026, 10:40 -03) - NASCIMENTO POR NUMERO DE CONTROLE NO MODELO DO MAGIC/GERAS (decisao de Benedito):
#             controle_pdf() usa _contexto_magic(..., id_gta=) e manda o PDF no modo 'controle' (Comunicado de Insercao
#             BND/SISBOV). _contexto_magic ganha o parametro id_gta (filtra pela Notificacao em vez do periodo).
#             Telas e consultas iguais. REVERSAO: devolver .bak_antes_controle_s102.
#     v1.6.0: Sessao 102 (21/10/2026, 10:55 -03) - APTIDAO REMOVIDA do contexto dos PDFs (o campo nao existe mais nos relatorios, decisao
#             de Benedito): saem o import de Aptidao, a consulta e a chave 'aptidao'. Nenhuma outra mudanca. REVERSAO: .bak_antes_aptidao_s102.
# =========================================================

from datetime import date, datetime

from flask import Blueprint, redirect, render_template, request, send_file, session

CHAVE_AVISO_CONTROLE = 'nascimento_controle_aviso'   # Etapa 4 (2a passada) - Regra #69

from backend.models import Produtor, Propriedade, PropriedadeProdutor   # v1.4.0 - PropriedadeProdutor
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4002_especie import Especie   # v1.4.0
from backend.models.tb_4005_racas import Raca
from backend.models.tb_7020_notificacao_impressao import NotificacaoImpressao
from backend.routers.auth import buscar_pares_propriedade_produtor, redirecionar_home, resolver_fazenda_em_uso
from backend.routers.gta_manual import municipio_sem_uf   # v1.4.0 - tira o ' / UF' do nome do municipio
from backend.utils.documentos_produtor import documentos_do_produtor   # v1.4.0 - CPF/CNPJ por fazenda
from backend.utils.multitenant import get_db_produtor
from backend.utils.pdf_nascimentos_periodo import gerar_pdf_nascimentos_periodo, maiusculo_sem_acento


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
nascimentos_periodo = Blueprint('nascimentos_periodo', __name__)


@nascimentos_periodo.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


TIPO_BANCO_NASCIMENTO = 'NASCTO-DESMAME'
DIAS_POR_MES = 30
LIMITE_LINHAS_TELA = 500

URL_INICIAR = '/produtor/nascimentos-periodo/iniciar'
URL_TELA = '/produtor/nascimentos-periodo'
VOLTAR_SUBHUB = '/produtor/hub-novo/entrada-nascimento'   # v1.2.0 - Hub novo Nascimento / Desmame
TITULO = 'Nascimentos por Período'


# -------------------------------------------------------
# Auxiliares
# -------------------------------------------------------
# -------------------------------------------------------
# Trava de permissao (usada por TODAS as rotas do modulo).
# 1) a Propriedade da URL tem de ser de um par do usuario logado;
# 2) v1.2.0 - FAZENDA EM USO: se ha uma e ela e DIFERENTE da Propriedade
#    da URL (trocada em outra aba, por exemplo), devolve False - o chamador
#    manda para o iniciar() do relatorio, que abre a fazenda em uso.
# -------------------------------------------------------
def _propriedade_permitida(id_propriedade):
    if not str(id_propriedade).isdecimal():
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if int(id_propriedade) not in {int(par.id_propriedade) for par in pares if str(par.id_produtor) == str(session.get('id_produtor'))}:   # v1.9.0 - Produtor do par = Produtor da sessao (Etapa 7b)
        return False
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and int(par_em_uso.id_propriedade) != int(id_propriedade):
        return False
    return True


# -------------------------------------------------------
# Destino do Voltar (Regra de Ouro #9). v1.2.0: com fazenda em uso a selecao
# e pulada - volta direto ao Hub (voltar ao iniciar() reabriria a tela: laco).
# -------------------------------------------------------
def _url_voltar(pares):
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return URL_INICIAR
    return VOLTAR_SUBHUB


def _data_br(data):
    return data.strftime('%d/%m/%Y') if data else ''


def _ler_periodo():
    """Devolve (data_inicial, data_final, texto_inicial, texto_final, erro)."""
    hoje = date.today()
    padrao_inicial = hoje.replace(day=1)
    texto_inicial = request.args.get('data_inicial', '').strip() or _data_br(padrao_inicial)
    texto_final = request.args.get('data_final', '').strip() or _data_br(hoje)
    try:
        inicial = datetime.strptime(texto_inicial, '%d/%m/%Y').date()
        final = datetime.strptime(texto_final, '%d/%m/%Y').date()
    except ValueError:
        return None, None, texto_inicial, texto_final, 'Data incorreta! Use o formato dd/mm/aaaa nas duas datas.'
    if inicial > final:
        return None, None, texto_inicial, texto_final, 'A Data Inicial não pode ser posterior à Data Final.'
    return inicial, final, texto_inicial, texto_final, None


def _buscar(db, id_propriedade, inicial, final, id_gta=None):
    """Le os animais nascidos no periodo e monta (linhas, notificacoes,
    totais). Tudo em dicts/texto - nada de objeto do banco sai daqui."""
    consulta = db.query(Entrada).filter(
        Entrada.id_propriedade == int(id_propriedade),
        Entrada.tipo_entrada == TIPO_BANCO_NASCIMENTO,
    )
    if id_gta:    # v1.1.0 - por Numero de Controle (Notificacao)
        consulta = consulta.filter(Entrada.id_gta_entrada == int(id_gta))
    else:
        consulta = consulta.filter(Entrada.data_brincagem >= inicial, Entrada.data_brincagem <= final)
    animais = consulta.all()

    ids_gta = sorted({a.id_gta_entrada for a in animais if a.id_gta_entrada})
    numeros = {}
    impressas = {}
    if ids_gta:
        numeros = {g.id: g.numero_gta_completo for g in db.query(Gta).filter(Gta.id.in_(ids_gta)).all()}
        impressas = {
            i.id_gta: i.data_impressao
            for i in db.query(NotificacaoImpressao).filter(NotificacaoImpressao.id_gta.in_(ids_gta)).all()
        }
    codigos_raca = {r.id: r.codigo for r in db.query(Raca).all()}

    animais.sort(key=lambda a: (a.data_brincagem or date.min, numeros.get(a.id_gta_entrada, ''), a.sisbov or ''))

    linhas = []
    resumo = {}   # chave = numero da Notificacao
    for a in animais:
        numero = numeros.get(a.id_gta_entrada, '-')
        meses = int(round(a.eras_dias / DIAS_POR_MES)) if a.eras_dias is not None else None
        linhas.append({
            'notificacao': numero,
            'data_brincagem': _data_br(a.data_brincagem),
            'sisbov': a.sisbov,
            'manejo': a.manejo or '',
            'sexo': maiusculo_sem_acento(a.sexo),
            'raca': maiusculo_sem_acento(codigos_raca.get(a.id_raca, '')),
            'nascimento': _data_br(a.nascimento),
            'meses': '' if meses is None else str(meses),
            'lote': a.lote or '',
            'cth': 'SIM' if a.cota_hilton else 'NAO',
        })
        grupo = resumo.setdefault(numero, {
            'notificacao': numero, 'data_brincagem': _data_br(a.data_brincagem),
            'qtde': 0, 'machos': 0, 'femeas': 0, 'cth': 0,
            'situacao': 'Impressa em ' + _data_br(impressas[a.id_gta_entrada]) if a.id_gta_entrada in impressas else 'Não impressa',
        })
        grupo['qtde'] += 1
        grupo['machos'] += 1 if a.sexo == 'MACHO' else 0
        grupo['femeas'] += 1 if a.sexo == 'FEMEA' else 0
        grupo['cth'] += 1 if a.cota_hilton else 0

    notificacoes = sorted(resumo.values(), key=lambda g: (g['data_brincagem'][6:] + g['data_brincagem'][3:5] + g['data_brincagem'][:2], g['notificacao']))
    totais = {
        'qtde': len(linhas),
        'machos': sum(g['machos'] for g in notificacoes),
        'femeas': sum(g['femeas'] for g in notificacoes),
        'cth': sum(g['cth'] for g in notificacoes),
        'notificacoes': len(notificacoes),
    }
    return linhas, notificacoes, totais


def _cabecalho_propriedade(db, id_propriedade):
    propriedade = db.get(Propriedade, int(id_propriedade))
    produtor = db.get(Produtor, session['id_produtor'])
    return {
        'propriedade': propriedade.nome if propriedade else '',
        'municipio_uf': f'{propriedade.municipio} / {propriedade.uf}' if propriedade else '',
        'codigo_eras': propriedade.codigo_eras if propriedade else '',
        'produtor': produtor.nome if produtor else '',
        'cpf_cnpj': produtor.cpf_cnpj if produtor else '',
    }


# -------------------------------------------------------
# v1.4.0 - Meses COMPLETOS entre o nascimento e a brincagem (mesma regra da Notificacao de Nascimento).
# -------------------------------------------------------
def _meses_completos(nascimento, brincagem):
    if not nascimento or not brincagem:
        return None
    meses = (brincagem.year - nascimento.year) * 12 + (brincagem.month - nascimento.month)
    if brincagem.day < nascimento.day:
        meses -= 1
    return max(meses, 0)


# -------------------------------------------------------
# v1.4.0 - Contexto do PDF no visual do Magic. So leitura; devolve apenas texto e numeros (nada de objeto do
# banco). Animais da Propriedade, tipo NASCTO-DESMAME, com Data de Brincagem no periodo, agrupados por
# Codigo Interno (Notificacao NAS) na ordem Data de Brincagem > Numero > SISBOV.
# -------------------------------------------------------
def _contexto_magic(db, id_propriedade, inicial, final, id_gta=None):
    propriedade = db.get(Propriedade, int(id_propriedade))
    produtor = db.get(Produtor, session['id_produtor'])
    vinculo = None
    if produtor is not None:
        vinculo = (
            db.query(PropriedadeProdutor)
            .filter_by(id_propriedade=int(id_propriedade), id_produtor=produtor.id, data_fim=None)
            .first()
        )
    cpf, cnpj = documentos_do_produtor(produtor, vinculo)   # principal + secundario DESTA fazenda
    inscricao = (getattr(vinculo, 'inscricao_estadual', None) or getattr(propriedade, 'inscricao_estadual', None)
                 or '') if propriedade is not None else ''

    consulta = db.query(Entrada).filter(
        Entrada.id_propriedade == int(id_propriedade),
        Entrada.tipo_entrada == TIPO_BANCO_NASCIMENTO,
    )
    if id_gta:    # v1.5.0 - por Numero de Controle (Notificacao)
        consulta = consulta.filter(Entrada.id_gta_entrada == int(id_gta))
    else:
        consulta = consulta.filter(Entrada.data_brincagem >= inicial, Entrada.data_brincagem <= final)
    animais = consulta.all()
    ids_gta = sorted({a.id_gta_entrada for a in animais if a.id_gta_entrada})
    numeros = {g.id: g.numero_gta_completo for g in db.query(Gta).filter(Gta.id.in_(ids_gta)).all()} if ids_gta else {}
    racas = {r.id: r.codigo for r in db.query(Raca).all()}
    especies = {e.id: e.codigo for e in db.query(Especie).all()}

    animais.sort(key=lambda a: (a.data_brincagem or date.min, numeros.get(a.id_gta_entrada, ''), a.sisbov or ''))

    grupos = []
    por_numero = {}
    for a in animais:
        numero = numeros.get(a.id_gta_entrada, '-')
        chave = (numero, a.data_brincagem)
        if chave not in por_numero:
            por_numero[chave] = {'numero': numero, 'data_entrada': _data_br(a.data_brincagem), 'animais': []}
            grupos.append(por_numero[chave])
        por_numero[chave]['animais'].append({
            'sisbov': a.sisbov,
            'manejo': a.manejo or '',
            'especie': especies.get(a.id_especie, ''),
            'sexo': a.sexo,
            'nascimento': _data_br(a.nascimento),
            'brincagem': _data_br(a.data_brincagem),
            'raca': racas.get(a.id_raca, ''),
            'meses': _meses_completos(a.nascimento, a.data_brincagem),
        })

    agora = datetime.now()
    return {
        'produtor': produtor.nome if produtor else '',
        'cpf': cpf,
        'cnpj': cnpj,
        'inscricao_estadual': inscricao,
        'codigo_eras': propriedade.codigo_eras if propriedade else '',
        'propriedade': propriedade.nome if propriedade else '',
        'municipio': municipio_sem_uf(propriedade.municipio, propriedade.uf) if propriedade else '',
        'uf': propriedade.uf if propriedade else '',
        'nirf': (getattr(propriedade, 'nirf_incra', None) or '') if propriedade else '',
        'periodo_inicial': _data_br(inicial),
        'periodo_final': _data_br(final),
        'periodo': f'{_data_br(inicial)} a {_data_br(final)}',
        'gerado_em': agora.strftime('%d/%m/%Y %H:%M'),
        'gerado_em_completo': agora.strftime('%d/%m/%Y %H:%M:%S'),
        'grupos': grupos,
    }


# -------------------------------------------------------
# Rota: GET /produtor/nascimentos-periodo/iniciar
# Padrao Reutilizavel N.1 - Selecionar Propriedade/Produtor.
# -------------------------------------------------------
@nascimentos_periodo.route('/produtor/nascimentos-periodo/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    # v1.2.0 - FAZENDA EM USO: pula a tela de selecao e abre o relatorio direto.
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor'] = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{URL_TELA}?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor'] = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_TELA}?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None if pares else 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
        titulo=f'{TITULO} — Selecionar Propriedade',
        proximo=URL_TELA,
        campo_propriedade='id_propriedade',
        voltar=VOLTAR_SUBHUB,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/nascimentos-periodo?id_propriedade=X&...
# Filtro + resultado na mesma tela.
# -------------------------------------------------------
@nascimentos_periodo.route('/produtor/nascimentos-periodo')
def tela():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_permitida(id_propriedade):
        return redirect(URL_INICIAR)

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    inicial, final, texto_inicial, texto_final, erro = _ler_periodo()

    linhas, notificacoes, totais = [], [], {'qtde': 0, 'machos': 0, 'femeas': 0, 'cth': 0, 'notificacoes': 0}
    cabecalho = {}
    with get_db_produtor(session['id_produtor']) as db:
        cabecalho = _cabecalho_propriedade(db, id_propriedade)
        if not erro:
            linhas, notificacoes, totais = _buscar(db, id_propriedade, inicial, final)

    excedeu = len(linhas) > LIMITE_LINHAS_TELA
    return render_template(
        'produtor/nascimentos_periodo.html',
        titulo=TITULO,
        id_propriedade=id_propriedade,
        propriedade_nome=cabecalho.get('propriedade', ''),
        data_inicial=texto_inicial,
        data_final=texto_final,
        erro=erro,
        consultou=not erro,
        totais=totais,
        notificacoes=notificacoes,
        linhas=linhas[:LIMITE_LINHAS_TELA],
        excedeu=excedeu,
        limite_tela=LIMITE_LINHAS_TELA,
        url_voltar=_url_voltar(pares),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/nascimentos-periodo/pdf?id_propriedade=X&...
# -------------------------------------------------------
@nascimentos_periodo.route('/produtor/nascimentos-periodo/pdf')
def pdf():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_permitida(id_propriedade):
        return redirect(URL_INICIAR)

    inicial, final, texto_inicial, texto_final, erro = _ler_periodo()
    if erro:
        return redirect(f'{URL_TELA}?id_propriedade={id_propriedade}&data_inicial={texto_inicial}&data_final={texto_final}')

    with get_db_produtor(session['id_produtor']) as db:
        contexto = _contexto_magic(db, id_propriedade, inicial, final)   # v1.4.0 - visual do Magic

    buffer = gerar_pdf_nascimentos_periodo(contexto)
    nome_arquivo = f'nascimentos_{inicial.strftime("%d-%m-%Y")}_a_{final.strftime("%d-%m-%Y")}.pdf'
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)


# =======================================================
# v1.1.0 - RELATORIO NASCIMENTO POR NUMERO DE CONTROLE
# =======================================================
URL_CONTROLE_INICIAR = '/produtor/nascimentos-controle/iniciar'
URL_CONTROLE_TELA = '/produtor/nascimentos-controle'
TITULO_CONTROLE = 'Nascimento por Número de Controle'


def _opcoes_controle(db, id_propriedade):
    """Notificacoes (NAS) da Propriedade que tem animais, da mais nova para a mais antiga."""
    gtas = (
        db.query(Gta)
        .filter(Gta.id_propriedade == int(id_propriedade),
                Gta.tipo_movimento == TIPO_BANCO_NASCIMENTO, Gta.serie_gta == 'NAS')
        .order_by(Gta.numero_gta_sequencial.desc())
        .all()
    )
    opcoes = []
    for gta in gtas:
        qtde = db.query(Entrada).filter(Entrada.id_gta_entrada == gta.id).count()
        if qtde > 0:
            opcoes.append({'id': gta.id, 'numero': gta.numero_gta_completo,
                           'data': _data_br(gta.data_emissao), 'qtde': qtde})
    return opcoes


def _gta_da_propriedade(db, id_propriedade, id_gta):
    if not str(id_gta).isdecimal():
        return None
    return (
        db.query(Gta)
        .filter(Gta.id == int(id_gta), Gta.id_propriedade == int(id_propriedade),
                Gta.tipo_movimento == TIPO_BANCO_NASCIMENTO, Gta.serie_gta == 'NAS')
        .first()
    )


@nascimentos_periodo.route('/produtor/nascimentos-controle/iniciar')
def controle_iniciar():
    """Padrao Reutilizavel N.1 - com 1 unico par, pula direto."""
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    # v1.2.0 - FAZENDA EM USO: pula a tela de selecao e abre o relatorio direto.
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor'] = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{URL_CONTROLE_TELA}?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor'] = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_CONTROLE_TELA}?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None if pares else 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
        titulo=f'{TITULO_CONTROLE} — Selecionar Propriedade',
        proximo=URL_CONTROLE_TELA,
        campo_propriedade='id_propriedade',
        voltar=VOLTAR_SUBHUB,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )


@nascimentos_periodo.route('/produtor/nascimentos-controle')
def controle_tela():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_permitida(id_propriedade):
        return redirect(URL_CONTROLE_INICIAR)

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    id_gta = request.args.get('id_gta', '').strip()

    erro = session.pop(CHAVE_AVISO_CONTROLE, None)   # aviso deixado pelo PDF (Regra #69)
    consultou = False
    linhas, notificacoes, totais = [], [], {'qtde': 0, 'machos': 0, 'femeas': 0, 'cth': 0, 'notificacoes': 0}
    with get_db_produtor(session['id_produtor']) as db:
        cabecalho = _cabecalho_propriedade(db, id_propriedade)
        opcoes = _opcoes_controle(db, id_propriedade)
        if id_gta:
            if _gta_da_propriedade(db, id_propriedade, id_gta):
                consultou = True
                linhas, notificacoes, totais = _buscar(db, id_propriedade, None, None, id_gta=id_gta)
            else:
                erro = 'Número de Controle não encontrado nesta Propriedade.'

    excedeu = len(linhas) > LIMITE_LINHAS_TELA
    return render_template(
        'produtor/nascimento_controle.html',
        titulo=TITULO_CONTROLE,
        id_propriedade=id_propriedade,
        propriedade_nome=cabecalho.get('propriedade', ''),
        opcoes=opcoes,
        id_gta=id_gta,
        erro=erro,
        consultou=consultou,
        totais=totais,
        notificacoes=notificacoes,
        linhas=linhas[:LIMITE_LINHAS_TELA],
        excedeu=excedeu,
        limite_tela=LIMITE_LINHAS_TELA,
        url_voltar=_url_voltar_controle(pares),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )


def _url_voltar_controle(pares):
    # v1.2.0 - com fazenda em uso a selecao e pulada: volta direto ao Hub.
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return URL_CONTROLE_INICIAR
    return VOLTAR_SUBHUB


@nascimentos_periodo.route('/produtor/nascimentos-controle/pdf')
def controle_pdf():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_permitida(id_propriedade):
        return redirect(URL_CONTROLE_INICIAR)
    id_gta = request.args.get('id_gta', '').strip()

    with get_db_produtor(session['id_produtor']) as db:
        gta = _gta_da_propriedade(db, id_propriedade, id_gta)
        if not gta:
            session[CHAVE_AVISO_CONTROLE] = ('Não encontramos esta Notificação de Nascimento nesta Propriedade. Volte à lista e escolha o Número de Controle de novo. '
                                             'Os Números de Controle são gerados pelo Orion, então isto não deveria acontecer: se repetir, avise a Consiste (usuário, Número de Controle, data e hora).')
            return redirect(f'{URL_CONTROLE_TELA}?id_propriedade={id_propriedade}')
        numero = gta.numero_gta_completo
        contexto = _contexto_magic(db, id_propriedade, None, None, id_gta=gta.id)   # v1.5.0 - visual do Magic

    contexto.update({'tipo': 'controle', 'titulo_rodape': 'Nascimento por Número de Controle', 'periodo': numero})
    buffer = gerar_pdf_nascimentos_periodo(contexto)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'nascimento_{numero}.pdf')

# =========================================================
# FIM DE ARQUIVO: backend\routers\nascimentos_periodo.py
# =========================================================
