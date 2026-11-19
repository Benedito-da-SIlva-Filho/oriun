# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\saida_gta_consulta.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-20 09:20 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.6.0
# v1.6.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.5.0: Sessao 115 (2026-11-05 17:40 -03) - DTA de Alteracao de Posse (tipo POSSE) aparece na Consulta GTA. REVERSAO: .bak_antes_s115_dta3a.
#
# DESCRICAO:
#     Consulta GTA de Saida (Sessao 101) - card proprio no Hub de Saidas,
#     grupo "Consultas e correcoes". Pesquisa as GTAs de saida (Abate) da
#     Propriedade e mostra, de cada uma, os animais vinculados, a categoria
#     que a GTA pede, o Comunicado (quando ja gerado) e o historico das
#     operacoes (vinculo, desvinculo e substituicao). Gera o PDF com a
#     relacao dos animais da GTA. So LE: nao grava nada.
#
#     REGRAS FECHADAS COM O BENEDITO (20/10/2026):
#       - Mostra TODAS as GTAs de saida (opiniao do Claude aceita: Benedito deu o
#         horario depois de perguntar): Pendente (sem animais), Vinculada
#         (com animais, sem Comunicado) e Comunicada (com numero de Comunicado).
#         O filtro Situacao escolhe qual ver.
#       - Depois do Comunicado a GTA continua na consulta, com o numero do Comunicado.
#       - PDF da relacao de animais da GTA, no padrao de download com aviso (Regra #15).
#       - Card a parte, com este unico proposito. Desvincular e Substituir continuam
#         nas telas proprias.
#
#     ASSUMIDO (Benedito ainda nao confirmou): filtros = numero (parte do numero),
#     situacao, frigorifico e Data de Saida (de / ate); historico mostra as ultimas 50
#     operacoes da GTA (modulos saida_vincular e saida_substituicao), achadas pelo
#     numero da GTA no texto da operacao.
#
#     ROTAS (/produtor/saida-gta-consulta/):
#       iniciar  - resolve a Propriedade (fazenda em uso) e abre a lista.
#       lista    - GTAs de saida com filtros.
#       detalhe  - uma GTA: dados, categoria pedida, animais e historico.
#       pdf      - PDF com a relacao dos animais da GTA.
#
#     v1.0.0: Criacao (Sessao 101).
#     v1.0.1: Sessao 101 (20/10/2026, 09:24 -03) - Ordem da lista: Data de Saida decrescente (a mais recente primeiro); GTAs sem Data de Saida (pendentes) ficam no fim, da emissao mais recente para a mais antiga. Antes a Data de Saida se misturava com a Data Embarque.
#     v1.1.0: Sessao 101 (20/10/2026, 09:31 -03) - Botoes de atalho Todas / Pendentes / Vinculadas / Comunicadas com a quantidade de cada um (contam respeitando os outros filtros) e aviso no topo quando ha GTAs pendentes (sem animais), que aplica o filtro Pendentes. Pendentes continua = GTA sem animais.
#     v1.2.0: Sessao 103 (22/10/2026, 16:05 -03) - Passa a ser a UNICA consulta de GTA de Saida: o detalhe ganha os botoes Alterar e Excluir
#             (so Titular/Administrador), o aviso vermelho dos animais vinculados x categorias e os avisos 'GTA alterada' / 'reimprimir o
#             Comunicado'. A regra de alterar/excluir continua em gta_saida.py.  REVERSAO: .bak_antes_consulta_unica_s103.
#     REVERSAO: remover este arquivo e os templates saida_gta_consulta_*.html;
#     devolver os .bak_antes_gta_consulta_s101 de app.py, permissoes.py e hub_entrada_agrupado.py.
# =========================================================

from datetime import datetime, date
from io import BytesIO
from urllib.parse import urlencode, parse_qsl, quote

from flask import Blueprint, render_template, request, redirect, session, send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4001_gta_animais import GtaAnimal
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.models.tb_log_operacoes import LogOperacao
from backend.models.usuario import Usuario
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.gta_manual import _buscar_dados_exibicao
from backend.routers.saida_consulta import _contexto_base, _propriedade_do_usuario, _data_br, _ler_iso, _faixa_em, _nomes, URL_HUB
from backend.routers.saida_vincular import _nomes_frigorificos, ROTULO_SEXO
from backend.routers.gta_saida import _pode_alterar, _gta_digitada_a_mao, _avisos_do_vinculo, URL_EDITAR, URL_EXCLUIR
from backend.utils.multitenant import get_db_produtor
from backend.utils.pdf_reportlab import (
    PAGE_SIZE, MARGEM_H, MARGEM_V, LARGURA_UTIL,
    estilo_titulo, estilo_subtitulo, estilo_rodape,
    criar_bloco_dados, criar_cabecalho_campos, criar_tabela_padrao,
)

saida_gta_consulta = Blueprint('saida_gta_consulta', __name__)

SENTIDO_SAIDA = 'SAIDA'
TIPO_MOVIMENTO_ABATE = 'ABATE'
TIPO_MOVIMENTO_TRANSFER = 'TRANSFERENCIA'          # v107 - GTA de Transferencia tambem aparece na Consulta GTA
TIPO_MOVIMENTO_VENDA = 'VENDA'                     # s111 - GTA de Venda tambem aparece na Consulta GTA
TIPO_MOVIMENTO_POSSE = 'POSSE'                     # s115 - DTA de Alteracao de Posse tambem aparece na Consulta GTA
TIPOS_GTA = (TIPO_MOVIMENTO_ABATE, TIPO_MOVIMENTO_TRANSFER, TIPO_MOVIMENTO_VENDA, TIPO_MOVIMENTO_POSSE)
TIPOS_COM_DESTINO_GTA = (TIPO_MOVIMENTO_TRANSFER, TIPO_MOVIMENTO_VENDA, TIPO_MOVIMENTO_POSSE)
ROTULO_TIPO_GTA = {TIPO_MOVIMENTO_TRANSFER: 'Transferência', TIPO_MOVIMENTO_VENDA: 'Venda', TIPO_MOVIMENTO_POSSE: 'Alteração de Posse'}
TIPOS_SAIDA_LEITURA = ('ABATE', 'TRANSFER', 'VENDA', 'POSSE')


def _tipo_saida_da_gta(tipo_movimento):
    if tipo_movimento == TIPO_MOVIMENTO_VENDA:
        return 'VENDA'
    if tipo_movimento == TIPO_MOVIMENTO_POSSE:
        return 'POSSE'
    return 'TRANSFER' if tipo_movimento == TIPO_MOVIMENTO_TRANSFER else 'ABATE'


from backend.utils.destino_transferencia import nomes_destinos_transfer as _destinos_transfer   # peca unica (v107)
URL_INICIAR = '/produtor/saida-gta-consulta/iniciar'
URL_LISTA   = '/produtor/saida-gta-consulta/lista'
URL_DETALHE = '/produtor/saida-gta-consulta/detalhe'
URL_PDF     = '/produtor/saida-gta-consulta/pdf'

SITUACOES = {'pendente': 'Pendente', 'vinculada': 'Vinculada', 'comunicada': 'Comunicada'}
FILTROS_PERMITIDOS = ('numero', 'situacao', 'frigorifico', 'saida_de', 'saida_ate')
MODULOS_HISTORICO = ('saida_vincular', 'saida_substituicao')
ROTULO_MODULO = {'saida_vincular': 'Vínculo / Desvínculo', 'saida_substituicao': 'Substituição'}
LIMITE_HISTORICO = 50


# =========================================================
# BLOCO 1 - Funcoes de apoio (sem rota)
# =========================================================

def _negado():
    """Propriedade que nao e do usuario: volta ao inicio do modulo ou ao Home."""
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect(URL_INICIAR)
    return redirecionar_home()


def _kg(valor):
    """Peso para a tela e o PDF: '450' ou '450,5'."""
    if valor is None:
        return '-'
    return f'{float(valor):.2f}'.rstrip('0').rstrip('.').replace('.', ',')


def _situacao(gta, qtd_vinculados):
    """pendente = sem animais; vinculada = com animais e sem Comunicado; comunicada = tem numero de Comunicado."""
    if gta.numero_comunicado is not None:
        return 'comunicada'
    return 'vinculada' if qtd_vinculados > 0 else 'pendente'


def _filtros_da_tela(args):
    """Le e limpa os filtros do endereco; so as chaves permitidas, nunca texto solto."""
    f = {k: (args.get(k) or '').strip() for k in FILTROS_PERMITIDOS}
    f['numero'] = f['numero'][:30]
    if f['situacao'] not in SITUACOES:
        f['situacao'] = ''
    if not f['frigorifico'].isdecimal():
        f['frigorifico'] = ''
    for k in ('saida_de', 'saida_ate'):
        if _ler_iso(f[k]) is None:
            f[k] = ''
    return f


def _qs_filtros(filtros):
    """Filtros preenchidos, em texto de endereco (para o Voltar do detalhe devolver a mesma lista)."""
    return urlencode({k: v for k, v in filtros.items() if v})


def _gta_da_propriedade(db, id_propriedade, id_gta):
    """A GTA de saida (Abate) da Propriedade, com ou sem Comunicado; ou None."""
    try:
        id_int = int(id_gta)
    except (TypeError, ValueError):
        return None
    return (
        db.query(Gta)
        .filter(
            Gta.id == id_int,
            Gta.id_propriedade == int(id_propriedade),
            Gta.sentido == SENTIDO_SAIDA,
            Gta.tipo_movimento.in_(TIPOS_GTA),
        )
        .first()
    )


def _montar_gta(id_produtor, id_propriedade, id_gta):
    """
    Dados de uma GTA para a tela e o PDF. Devolve None se a GTA nao e desta
    Propriedade. Tudo vira texto/numero comum antes de fechar o banco.
    """
    with get_db_produtor(id_produtor) as db:
        gta = _gta_da_propriedade(db, id_propriedade, id_gta)
        if gta is None:
            return None

        leituras = (
            db.query(Embarque)
            .filter(Embarque.id_propriedade == int(id_propriedade),
                    Embarque.tipo_saida == _tipo_saida_da_gta(gta.tipo_movimento),
                    Embarque.id_gta == gta.id)
            .order_by(Embarque.sisbov.asc())
            .all()
        )
        faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
        pedido_linhas = db.query(GtaAnimal).filter(GtaAnimal.id_gta == gta.id).all()

        animais = []
        for i, l in enumerate(leituras, start=1):
            obs = ''
            if l.liberacao_abate and l.liberacao_abate > l.data_embarque:
                obs = 'Fora da liberação' + (' (ciente)' if l.aceite_fora_liberacao else '')
            animais.append({
                'indice': i,
                'sisbov': l.sisbov,
                'manejo': l.manejo or '-',
                'sexo': l.sexo or '-',
                'nascimento': _data_br(l.nascimento),
                'faixa': _faixa_em(faixas, l.nascimento, l.data_embarque),
                'peso': _kg(l.peso_saida),
                'data_embarque': _data_br(l.data_embarque),
                'obs': obs,
            })
        datas_embarque = sorted({l.data_embarque for l in leituras})

        pedido = [{
            'sexo': ROTULO_SEXO.get((p.sexo or '').upper(), p.sexo or '-'),
            'faixa': p.idade_meses,
            'quantidade': p.quantidade,
        } for p in pedido_linhas]

        # Historico: operacoes do vinculo e da substituicao desta GTA, achadas pelo numero
        # da GTA no texto da operacao (com espaco ou parenteses depois, para nao confundir
        # com outro numero que comece igual).
        numero = gta.numero_gta_completo
        ops = (
            db.query(LogOperacao)
            .filter(LogOperacao.id_propriedade == int(id_propriedade),
                    LogOperacao.modulo.in_(MODULOS_HISTORICO),
                    or_(LogOperacao.descricao.contains(f'GTA {numero} '),
                        LogOperacao.descricao.contains(f'GTA {numero})')))
            .order_by(LogOperacao.criado_em.desc())
            .limit(LIMITE_HISTORICO)
            .all()
        )
        brutas_hist = [(o.criado_em, o.id_usuario, o.modulo, o.descricao) for o in ops]

        dados = {
            'id': gta.id,
            'numero': numero,
            'id_frigorifico': gta.id_frigorifico,
            'transfer': gta.tipo_movimento in TIPOS_COM_DESTINO_GTA,
            'tipo_rotulo': ROTULO_TIPO_GTA.get(gta.tipo_movimento, 'Abate'),
            'destino_transfer': _destinos_transfer(db, [gta.id_parceiro_propriedade]).get(gta.id_parceiro_propriedade, '-'),
            'emissao': _data_br(gta.data_emissao),
            'validade': _data_br(gta.data_validade),
            'data_saida': _data_br(gta.data_saida),
            'qtde_gta': gta.qtde_animais,
            'numero_comunicado': gta.numero_comunicado,
            'situacao': _situacao(gta, len(animais)),
        }

    nomes_frig = _nomes_frigorificos([dados['id_frigorifico']])
    dados['frigorifico'] = dados['destino_transfer'] if dados['transfer'] else nomes_frig.get(dados['id_frigorifico'], '-')
    dados['destino_rotulo'] = {'Venda': 'Comprador', 'Alteração de Posse': 'Produtor de destino'}.get(dados.get('tipo_rotulo'), 'Destino') if dados['transfer'] else 'Frigorífico'

    ids_usuarios = {h[1] for h in brutas_hist if h[1]}
    nomes_usuarios = {}
    if ids_usuarios:
        with Session(engine) as dbp:
            for u in dbp.query(Usuario).filter(Usuario.id.in_(ids_usuarios)).all():
                nomes_usuarios[u.id] = u.nome or u.login
    historico = [{
        'quando': criado.strftime('%d/%m/%Y %H:%M') if criado else '-',
        'usuario': nomes_usuarios.get(id_u, '-'),
        'tipo': ROTULO_MODULO.get(modulo, modulo),
        'descricao': descricao,
    } for criado, id_u, modulo, descricao in brutas_hist]

    dados.update({
        'animais': animais,
        'total': len(animais),
        'pedido': pedido,
        'historico': historico,
        'data_embarque': (_data_br(datas_embarque[0]) if len(datas_embarque) == 1
                          else (' a '.join([_data_br(datas_embarque[0]), _data_br(datas_embarque[-1])])
                                if datas_embarque else '-')),
    })
    return dados


# =========================================================
# BLOCO 2 - Rotas
# =========================================================

# -------------------------------------------------------
# GET /produtor/saida-gta-consulta/iniciar
# -------------------------------------------------------
@saida_gta_consulta.route('/produtor/saida-gta-consulta/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista,
            erro=erro,
            titulo='Consulta GTA — Selecionar Propriedade',
            proximo=URL_LISTA,
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
        return redirect(f'{URL_LISTA}?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_LISTA}?id_propriedade={par.id_propriedade}')

    return _tela_selecionar(pares, None)


# -------------------------------------------------------
# GET /produtor/saida-gta-consulta/lista - uma linha por GTA de saida.
# -------------------------------------------------------
@saida_gta_consulta.route('/produtor/saida-gta-consulta/lista')
def lista():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']
    filtros = _filtros_da_tela(request.args)

    base = (Gta.id_propriedade == int(id_propriedade),
            Gta.sentido == SENTIDO_SAIDA,
            Gta.tipo_movimento.in_(TIPOS_GTA))

    with get_db_produtor(id_produtor) as db:
        consulta = db.query(Gta).filter(*base)
        if filtros['numero']:
            texto = filtros['numero'].replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            consulta = consulta.filter(Gta.numero_gta_completo.ilike(f'%{texto}%', escape='\\'))
        if filtros['frigorifico']:
            consulta = consulta.filter(Gta.id_frigorifico == int(filtros['frigorifico']))
        if filtros['saida_de']:
            consulta = consulta.filter(Gta.data_saida >= _ler_iso(filtros['saida_de']))
        if filtros['saida_ate']:
            consulta = consulta.filter(Gta.data_saida <= _ler_iso(filtros['saida_ate']))
        gtas = consulta.all()

        ids = [g.id for g in gtas]
        contagem = {}
        if ids:
            for id_gta, qtd, primeira in (
                db.query(Embarque.id_gta, func.count(Embarque.id), func.min(Embarque.data_embarque))
                .filter(Embarque.id_propriedade == int(id_propriedade),
                        Embarque.tipo_saida.in_(TIPOS_SAIDA_LEITURA),
                        Embarque.id_gta.in_(ids))
                .group_by(Embarque.id_gta).all()
            ):
                contagem[id_gta] = (qtd, primeira)

        # Frigorificos que aparecem nas GTAs da Propriedade (para o filtro), sem olhar os outros filtros.
        ids_frig = {r[0] for r in db.query(Gta.id_frigorifico).filter(*base).distinct().all() if r[0]}

        destinos_transfer = _destinos_transfer(db, [g.id_parceiro_propriedade for g in gtas])
        brutas = []
        for g in gtas:
            qtd, primeira = contagem.get(g.id, (0, None))
            situacao = _situacao(g, qtd)
            brutas.append({
                'id': g.id,
                'numero': g.numero_gta_completo,
                'id_frigorifico': g.id_frigorifico,
                'transfer': g.tipo_movimento in TIPOS_COM_DESTINO_GTA,
                'tipo_rotulo': ROTULO_TIPO_GTA.get(g.tipo_movimento, 'Abate'),
                'destino_transfer': destinos_transfer.get(g.id_parceiro_propriedade, '-'),
                'data_embarque': _data_br(primeira) if primeira else '-',
                'data_saida': _data_br(g.data_saida),
                'qtde_gta': g.qtde_animais,
                'vinculados': qtd,
                'situacao': situacao,
                'rotulo_situacao': SITUACOES[situacao],
                'numero_comunicado': g.numero_comunicado,
                '_ordem': (g.data_saida is not None, g.data_saida or date.min, g.data_emissao or date.min, g.id),
            })

    # Quantidade de cada situacao (respeita numero, frigorifico e datas) e, so depois, o filtro Situacao.
    contagens = {'todas': len(brutas), 'pendente': 0, 'vinculada': 0, 'comunicada': 0}
    for b in brutas:
        contagens[b['situacao']] += 1
    if filtros['situacao']:
        brutas = [b for b in brutas if b['situacao'] == filtros['situacao']]

    def _url_situacao(chave):
        """Mesma lista, com os outros filtros mantidos e a situacao trocada."""
        outros = dict(filtros)
        outros['situacao'] = chave
        texto = _qs_filtros(outros)
        return f'{URL_LISTA}?id_propriedade={int(id_propriedade)}' + (f'&{texto}' if texto else '')

    atalhos = [{'rotulo': 'Todas', 'qtd': contagens['todas'], 'url': _url_situacao(''), 'ativo': not filtros['situacao']}]
    for chave, rotulo in SITUACOES.items():
        atalhos.append({'rotulo': rotulo + 's', 'qtd': contagens[chave], 'url': _url_situacao(chave),
                        'ativo': filtros['situacao'] == chave})
    url_pendentes = _url_situacao('pendente')

    brutas.sort(key=lambda b: b['_ordem'], reverse=True)
    nomes = _nomes_frigorificos([b['id_frigorifico'] for b in brutas] + list(ids_frig))
    qs = _qs_filtros(filtros)
    for b in brutas:
        b['frigorifico'] = b['destino_transfer'] if b['transfer'] else nomes.get(b['id_frigorifico'], '-')
        b['url'] = f'{URL_DETALHE}?id_propriedade={int(id_propriedade)}&id={b["id"]}' + (f'&f={_qs_codificado(qs)}' if qs else '')
        del b['_ordem']
    opcoes_frig = sorted(({'id': i, 'nome': nomes.get(i, '-')} for i in ids_frig), key=lambda o: o['nome'])

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_gta_consulta_lista.html',
        gtas=brutas,
        filtros=filtros,
        situacoes=SITUACOES,
        atalhos=atalhos,
        qtd_pendentes=contagens['pendente'],
        url_pendentes=url_pendentes,
        opcoes_frig=opcoes_frig,
        id_propriedade=int(id_propriedade),
        url_limpar=f'{URL_LISTA}?id_propriedade={int(id_propriedade)}',
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        url_hub=URL_HUB,
        **_contexto_base(),
    )


def _qs_codificado(qs):
    """Texto de filtros dentro de outro endereco (os & e = viram %26 e %3D)."""
    return quote(qs, safe='')


# -------------------------------------------------------
# GET /produtor/saida-gta-consulta/detalhe
# -------------------------------------------------------
@saida_gta_consulta.route('/produtor/saida-gta-consulta/detalhe')
def detalhe():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']

    # Voltar = caminho real (Regra #9): a mesma lista, com os mesmos filtros de onde o usuario veio.
    filtros_origem = {k: v for k, v in parse_qsl(request.args.get('f', '')) if k in FILTROS_PERMITIDOS}
    filtros_origem = _filtros_da_tela(filtros_origem)
    qs_origem = _qs_filtros(filtros_origem)
    url_lista = f'{URL_LISTA}?id_propriedade={int(id_propriedade)}' + (f'&{qs_origem}' if qs_origem else '')

    dados = _montar_gta(id_produtor, id_propriedade, request.args.get('id', ''))
    if dados is None:
        return redirect(url_lista)

    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    # v1.2.0 - Alterar/Excluir e o check dos animais (regras em gta_saida.py)
    pode_alterar = _pode_alterar(id_propriedade) and _gta_digitada_a_mao(dados)
    return render_template(
        'produtor/saida_gta_consulta_detalhe.html',
        g=dados,
        pode_alterar=pode_alterar,
        url_editar=f'{URL_EDITAR}{dados["id"]}',
        url_excluir=f'{URL_EXCLUIR}{dados["id"]}',
        avisos_vinculo=_avisos_do_vinculo(dados['id']),
        msg_alterada=request.args.get('alterada') == '1',
        msg_reimprimir=request.args.get('reimprimir') == '1',
        rotulo_situacao=SITUACOES[dados['situacao']],
        url_pdf=f'{URL_PDF}?id_propriedade={int(id_propriedade)}&id={dados["id"]}',
        nome_pdf=_nome_pdf(dados['numero']),
        url_lista=url_lista,
        id_propriedade=int(id_propriedade),
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        **_contexto_base(),
    )


def _nome_pdf(numero):
    """Nome do arquivo: so letras e numeros da GTA."""
    limpo = ''.join(c for c in (numero or '') if c.isalnum())
    return f'GTA_{limpo}_Animais.pdf'


# -------------------------------------------------------
# GET /produtor/saida-gta-consulta/pdf - relacao dos animais da GTA.
# -------------------------------------------------------
@saida_gta_consulta.route('/produtor/saida-gta-consulta/pdf')
def pdf():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']

    dados = _montar_gta(id_produtor, id_propriedade, request.args.get('id', ''))
    if dados is None:
        return redirect(f'{URL_LISTA}?id_propriedade={int(id_propriedade)}')

    _, propria = _buscar_dados_exibicao(id_produtor, None, None, id_propriedade)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=PAGE_SIZE,
        leftMargin=MARGEM_H, rightMargin=MARGEM_H,
        topMargin=MARGEM_V, bottomMargin=MARGEM_V,
    )

    story = [
        Paragraph('RELAÇÃO DE ANIMAIS DA GTA DE SAÍDA', estilo_titulo),
        Paragraph((dados.get('tipo_rotulo') or 'Transferência').upper() if dados.get('transfer') else 'ABATE', estilo_subtitulo),
    ]
    story += criar_bloco_dados('DADOS DA ORIGEM DOS ANIMAIS', [
        ('Produtor:', propria.produtor_nome if propria and propria.produtor_nome else '-',
         f'CPF/CNPJ: {propria.cpf_cnpj}' if propria and propria.cpf_cnpj else 'CPF/CNPJ: -'),
        ('Propriedade:', propria.nome if propria else '-',
         f'Insc. Estadual: {propria.insc_estadual}' if propria and propria.insc_estadual else 'Insc. Estadual: -'),
        ('Município:', f'{propria.municipio_nome} / {propria.uf}' if propria and propria.municipio_nome else '-', None),
    ])
    story.append(Spacer(1, 6))
    story += criar_bloco_dados('DADOS DA GTA', [
        (dados.get('destino_rotulo', 'Frigorífico') + ':', dados['frigorifico'],
         f'Comunicado: {dados["numero_comunicado"]}' if dados['numero_comunicado'] is not None else 'Comunicado: -'),
        ('Emissão:', dados['emissao'], f'Validade: {dados["validade"]}'),
    ])
    story.append(criar_cabecalho_campos([
        ('Nº da GTA', dados['numero']),
        ('Data Embarque', dados['data_embarque']),
        ('Data de Saída', dados['data_saida']),
        ('Animais', str(dados['total'])),
    ]))
    story.append(Spacer(1, 12))

    larguras = [w * LARGURA_UTIL for w in (0.08, 0.20, 0.11, 0.08, 0.12, 0.14, 0.09, 0.18)]
    story.append(criar_tabela_padrao(
        cabecalhos=['Índice', 'Código SISBOV', 'Manejo', 'Sexo', 'Nascimento', 'Idade Meses', 'Peso (kg)', 'Obs.'],
        linhas=[[a['indice'], a['sisbov'], a['manejo'],
                 {'FEMEA': 'Fêmea', 'MACHO': 'Macho'}.get(a['sexo'], a['sexo']),
                 a['nascimento'], a['faixa'], a['peso'], a['obs']]
                for a in dados['animais']],
        larguras=larguras,
        alinhamentos=['CENTER', 'LEFT', 'LEFT', 'CENTER', 'CENTER', 'LEFT', 'RIGHT', 'LEFT'],
        colunas_destaque=[1, 2],
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f'Total Geral: {dados["total"]} animais &#8212; Impressão: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}',
        estilo_rodape,
    ))

    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=_nome_pdf(dados['numero']))

# =========================================================
# FIM DE ARQUIVO: backend\routers\saida_gta_consulta.py
# =========================================================
