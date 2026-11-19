# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\saida_relatorio.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-17 15:30 -03
# ATUALIZADO EM: 2026-11-08 14:40 -03
# VERSAO: 1.7.0
# v1.7.0: Sessao 123 (2026-11-13 19:50 -03) - AUDITORIA ETAPA 6 (leitura a fundo): lista de datas mostra quantos animais estao sem Sexo (o total somava, mas nao aparecia em machos/femeas). REVERSAO: .bak_antes_etapa6d.
# v1.6.1: Sessao 118 (2026-11-08 14:40 -03) - Raca no Pedido de GTA; Voltar do resumo volta a Consulta Embarque. REVERSAO: .bak_antes_s118_raca
# v1.6.0: Sessao 118 (2026-11-08 13:30 -03) - Rota pedido-pdf (PDF Pedido de GTA, inclui Posse) no lugar do Copiar pedido de GTA. REVERSAO: .bak_antes_s118_pedido
#
# DESCRICAO:
#     Relatorio de Embarque (Sessao 099) - grupo "Consultas e correcoes"
#     do Hub de Saidas. E por ele que o escritorio pede a GTA ao orgao do
#     Estado: mostra, por DATA DA LEITURA no brete, quantos animais
#     (Abate) foram lidos e ainda nao tiveram Comunicado, o resumo
#     Sexo x Faixa de Idade e a lista dos animais; e gera o PDF
#     (resumo + lista) no padrao do Orion (ReportLab, pdf_reportlab.py).
#
#     Le tb_2020_embarque (sts = False). Nao grava nada.
#     Faixa de idade: calculada pela idade do animal NA DATA DA LEITURA
#     (nascimento ate a data do embarque), faixas de tb_4006.
#     Aviso "fora da Liberacao para Abate": liberacao_abate maior que a
#     data da leitura (mostra "ciente" quando o aceite foi dado).
#
#     V1: contagem por categoria + lista. Peso total/@/GMP/diarias
#     ficam para depois (decidido por Benedito em 17/10/2026).
#
#     ROTAS (/produtor/saida-relatorio/):
#       iniciar  - resolve a Propriedade (fazenda em uso) e abre as datas.
#       datas    - datas com leituras em aberto.
#       resumo   - resumo + lista da data escolhida (tela).
#       pdf      - PDF (resumo + lista) da data escolhida.
#
#     v1.0.0: Criacao (Sessao 099).
#     v1.0.1: Sessao 099 (17/10/2026, 15:35 -03) - PDF: colunas Indice e Manejo alargadas (cabecalho quebrava a celula). So as larguras mudaram.
#     v1.1.0: Sessao 102 (21/10/2026, 12:10 -03) - PDF NO VISUAL DO MAGIC/GERAS (paisagem, via utils\pdf_relatorio_embarque.py), com bloco de
#             origem (CPF/CNPJ por fazenda, Insc. Estadual, Cod. ERAS, NIRF). _montar_relatorio ganha chaves novas por animal (rfid,
#             1a pesagem, 1o peso, kgs, dias, GPD, @ vivo, @ abate, lotes) e 'pesos' (peso total/medio, @, GMP, diarias). 1a pesagem =
#             tb_4003_pesos sequencia 1; sem pesagem usa data_inclusao e 1o peso 0. Sem peso_saida: celulas em branco e fora das somas.
#             Imports mortos do PDF antigo removidos. As chaves antigas e a tela NAO mudaram. Numeros em formato brasileiro.
#     REVERSAO: remover este arquivo e os templates saida_relatorio_*.html;
#     devolver os .bak_antes_relatorio_embarque_s099 (ou .bak_antes_embarque_magic_s102 para a 1.0.1).
#     v1.2.0: Sessao 103 (22/10/2026, 08:25 -03) - Relatorio de Embarque: Lote Saida repete o Lote Entrada quando nao ha Lote Saida; chaves novas
#             por animal 'cth' (tb_2020_embarque.cota_hilton) e 'bc' (Blockchain, False ate existir o selo) e totais cth_femeas/cth_machos.
#             A tela nao mudou.  REVERSAO: .bak_antes_cth_bc_s103.
#     v1.3.0: Sessao 103 (22/10/2026, 12:45 -03) - AVISO AO ESCRITORIO (decisao de Benedito: as duas ideias juntas): texto 'Pedido de GTA'
#             (categorias sexo x faixa do embarque) para o botao Copiar pedido de GTA nas telas de datas e de resumo (funcao
#             _texto_pedido_gta). O PDF e a regra do relatorio nao mudaram.  REVERSAO: .bak_antes_pedido_gta_s103.
#     v1.4.0: Sessao 107 (28/10/2026) - Aceita TRANSFERENCIA (parametro tipo=TRANSFER; sem tipo = ABATE). Telas de datas e resumo filtradas por
#             tipo (abas Abate | Transferencia), pedido de GTA com o titulo do tipo, sem aviso de Liberacao e sem PDF (PDF Magic e so do Abate).
#             Coluna Peso so aparece na Transferencia se algum animal tiver peso.  REVERSAO: .bak_antes_s107x.
#     v1.4.1: Sessao 107 - PDF tambem na Transferencia (mesmo layout, titulo TRANSFERENCIA, colunas de peso em branco ate haver peso).  REVERSAO: .bak_antes_s107y.
# =========================================================

from datetime import datetime

from flask import Blueprint, render_template, request, redirect, session, send_file
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, Produtor, PropriedadeProdutor
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.models.tb_4005_racas import Raca
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.gta_manual import municipio_sem_uf
from backend.utils.documentos_produtor import documentos_do_produtor
from backend.utils.multitenant import get_db_produtor
from backend.utils.pdf_relatorio_embarque import gerar_pdf_relatorio_embarque
from backend.utils.pdf_pedido_gta import gerar_pdf_pedido_gta

saida_relatorio = Blueprint('saida_relatorio', __name__)

TIPO_SAIDA_ABATE = 'ABATE'
TIPO_SAIDA_TRANSFER = 'TRANSFER'
TIPO_SAIDA_VENDA = 'VENDA'                  # s111
TIPOS_COM_DESTINO = (TIPO_SAIDA_TRANSFER, TIPO_SAIDA_VENDA)
URL_HUB    = '/produtor/hub-novo/saida'
URL_INICIAR = '/produtor/saida-relatorio/iniciar'
URL_DATAS  = '/produtor/saida-relatorio/datas'
URL_RESUMO = '/produtor/saida-relatorio/resumo'
URL_PDF    = '/produtor/saida-relatorio/pdf'
URL_PEDIDO_PDF = '/produtor/saida-relatorio/pedido-pdf'   # s118


def _contexto_base():
    return dict(
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='saidas',
    )


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


def _data_br(d):
    return d.strftime('%d/%m/%Y') if d else '-'


def _ler_data(texto):
    try:
        return datetime.strptime((texto or '').strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def _ler_tipo(texto):
    t = str(texto or '').strip().upper()
    return t if t in TIPOS_COM_DESTINO else TIPO_SAIDA_ABATE


def _qs_tipo(tipo):
    return f'&tipo={tipo}' if tipo in TIPOS_COM_DESTINO else ''


def _kg(valor):
    if valor is None:
        return '-'
    return f'{float(valor):.2f}'.rstrip('0').rstrip('.').replace('.', ',')


# -------------------------------------------------------
# v1.3.0 - Texto "Pedido de GTA" (botao Copiar pedido de GTA): categorias (sexo x faixa) do embarque, para o escritorio pedir a GTA
# ao orgao do Estado com as MESMAS categorias dos animais lidos. Funcao pura (sem banco).
# -------------------------------------------------------
def _texto_pedido_gta(rel, data_br, produtor_nome, propriedade_nome, tipo=TIPO_SAIDA_ABATE):
    rotulo = {TIPO_SAIDA_TRANSFER: 'TRANSFERENCIA', TIPO_SAIDA_VENDA: 'VENDA'}.get(tipo, 'ABATE')
    linhas = [f'PEDIDO DE GTA - {rotulo}',
              f'Propriedade: {propriedade_nome}' + (f' ({produtor_nome})' if produtor_nome else ''),
              f'Embarque (leitura no brete) de {data_br} - Total: {rel["total"]} animal(is)', '']
    colunas = rel.get('colunas') or []
    for i, faixa in enumerate(colunas):
        femeas = rel['resumo_femeas'][i] if i < len(rel['resumo_femeas']) else 0
        machos = rel['resumo_machos'][i] if i < len(rel['resumo_machos']) else 0
        if machos:
            linhas.append(f'- {machos} Macho(s) de {faixa}')
        if femeas:
            linhas.append(f'- {femeas} Fêmea(s) de {faixa}')
    if rel.get('sem_faixa_machos'):
        linhas.append(f'- {rel["sem_faixa_machos"]} Macho(s) SEM FAIXA (sem data de nascimento) - conferir antes de pedir')
    if rel.get('sem_faixa_femeas'):
        linhas.append(f'- {rel["sem_faixa_femeas"]} Fêmea(s) SEM FAIXA (sem data de nascimento) - conferir antes de pedir')
    linhas += ['', 'Peça a GTA com estas categorias (sexo e idade). Se a GTA vier diferente, o Orion não deixa vincular.']
    return '\n'.join(linhas)


# -------------------------------------------------------
# GET /produtor/saida-relatorio/iniciar
# -------------------------------------------------------
@saida_relatorio.route('/produtor/saida-relatorio/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    qs_t = _qs_tipo(_ler_tipo(request.args.get('tipo', '')))

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista,
            erro=erro,
            titulo='Relatório de Embarque — Selecionar Propriedade',
            proximo=URL_DATAS,
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
        return redirect(f'{URL_DATAS}?id_propriedade={par_em_uso.id_propriedade}{qs_t}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_DATAS}?id_propriedade={par.id_propriedade}{qs_t}')

    return _tela_selecionar(pares, None)


# -------------------------------------------------------
# GET /produtor/saida-relatorio/datas
# -------------------------------------------------------
@saida_relatorio.route('/produtor/saida-relatorio/datas')
def datas():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']
    tipo = _ler_tipo(request.args.get('tipo', ''))

    with get_db_produtor(id_produtor) as db:
        linhas = (
            db.query(Embarque.data_embarque, Embarque.sexo, func.count(Embarque.id))
            .filter(
                Embarque.id_propriedade == int(id_propriedade),
                Embarque.tipo_saida == tipo,
                Embarque.sts == False,   # noqa: E712
            )
            .group_by(Embarque.data_embarque, Embarque.sexo)
            .all()
        )

    por_data = {}
    for data_emb, sexo, qtd in linhas:
        item = por_data.setdefault(data_emb, {'machos': 0, 'femeas': 0, 'sem_sexo': 0, 'total': 0})
        if sexo == 'MACHO':
            item['machos'] += qtd
        elif sexo == 'FEMEA':
            item['femeas'] += qtd
        else:
            item['sem_sexo'] += qtd
        item['total'] += qtd

    lista = [{
        'iso': d.strftime('%Y-%m-%d'),
        'data': _data_br(d),
        'machos': v['machos'], 'femeas': v['femeas'], 'sem_sexo': v['sem_sexo'], 'total': v['total'],
    } for d, v in sorted(por_data.items(), reverse=True)]

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
        produtor = db.get(Produtor, id_produtor)
        produtor_nome = produtor.nome if produtor else '-'
        propriedade_nome = propriedade.nome if propriedade else '-'
        propriedade_local = f'{propriedade.municipio or ""} / {propriedade.uf or ""}' if propriedade else ''

    # v1.3.0 - texto do botao "Copiar pedido de GTA" de cada data
    for item in lista:
        rel_data = _montar_relatorio(id_produtor, id_propriedade, _ler_data(item['iso']), tipo)
        item['texto'] = (_texto_pedido_gta(rel_data, item['data'], produtor_nome, propriedade_nome, tipo)
                         if rel_data else '')

    return render_template(
        'produtor/saida_relatorio_datas.html',
        datas=lista,
        tipo=tipo,
        id_propriedade=int(id_propriedade),
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        url_hub=URL_HUB,
        **_contexto_base(),
    )


# -------------------------------------------------------
# Monta os dados do relatorio de uma data (usado pela tela e pelo PDF).
# Devolve None se nao ha leituras em aberto na data.
# -------------------------------------------------------
def _montar_relatorio(id_produtor, id_propriedade, data_emb, tipo=TIPO_SAIDA_ABATE):
    with get_db_produtor(id_produtor) as db:
        leituras = (
            db.query(Embarque)
            .filter(
                Embarque.id_propriedade == int(id_propriedade),
                Embarque.tipo_saida == tipo,
                Embarque.data_embarque == data_emb,
                Embarque.sts == False,   # noqa: E712
            )
            .order_by(Embarque.sisbov.asc())
            .all()
        )
        if not leituras:
            return None
        faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
        nomes_raca = {r.id: r.nome for r in db.query(Raca).all()}   # s118
        # v1.1.0 - 1a pesagem de cada animal (tb_4003_pesos, sequencia 1)
        lista_sisbov = [l.sisbov for l in leituras]
        primeiras = {}
        for pw in (db.query(Peso).filter(Peso.id_propriedade == int(id_propriedade), Peso.sisbov.in_(lista_sisbov),
                                         Peso.sequencia == 1).all()):
            primeiras[pw.sisbov] = pw

        animais = []
        for i, l in enumerate(leituras, start=1):
            dias = (data_emb - l.nascimento).days if l.nascimento else None
            faixa = '-'
            if dias is not None:
                for f in faixas:
                    if f.dias_min <= dias <= f.dias_max:
                        faixa = f.descricao
                        break
            obs = ''
            if tipo == TIPO_SAIDA_ABATE and l.liberacao_abate and l.liberacao_abate > data_emb:
                obs = 'Fora da liberação' + (' (ciente)' if l.aceite_fora_liberacao else '')
            item = {
                'indice': i,
                'sisbov': l.sisbov,
                'manejo': l.manejo or '-',
                'sexo': l.sexo or '-',
                'raca': nomes_raca.get(l.id_raca) or 'Sem raça',
                'nascimento': _data_br(l.nascimento),
                'faixa': faixa,
                'peso': _kg(l.peso_saida),
                'obs': obs,
            }
            animais.append(item)
            # --- v1.1.0: campos do PDF Magic ---
            pw1 = primeiras.get(l.sisbov)
            if pw1 is not None:
                data1, peso1 = pw1.data_pesagem, float(pw1.peso)
            else:
                data1, peso1 = l.data_inclusao, 0.0
            kgs = float(l.peso_saida) if l.peso_saida is not None else None
            dias = (data_emb - data1).days if data1 else None
            gpd = ((kgs - peso1) / dias) if (kgs is not None and dias and dias > 0) else None
            item.update({
                'rfid': l.rfid or '', 'lote_entrada': l.lote_entrada or '', 'lote_saida': l.lote_saida or l.lote_entrada or '',
                'cth': bool(l.cota_hilton), 'bc': False,
                'data_pesagem1': data1.strftime('%d/%m/%Y') if data1 else '', 'peso1': peso1 if data1 else None,
                'kgs': kgs, 'dias': dias, 'gpd': gpd,
                'arroba_vivo': kgs / 15 if kgs is not None else None,
                'arroba_abate': kgs / 30 if kgs is not None else None,
            })

    colunas = [f.descricao for f in faixas]
    mapa = {c: {'FEMEA': 0, 'MACHO': 0} for c in colunas}
    sem_faixa = {'FEMEA': 0, 'MACHO': 0}
    for a in animais:
        alvo = mapa.get(a['faixa'], sem_faixa)
        if a['sexo'] in ('FEMEA', 'MACHO'):
            alvo[a['sexo']] += 1
    resumo_femeas = [mapa[c]['FEMEA'] for c in colunas]
    resumo_machos = [mapa[c]['MACHO'] for c in colunas]
    com_peso = [a['kgs'] for a in animais if a.get('kgs') is not None]
    gpds = [a['gpd'] for a in animais if a.get('gpd') is not None]
    dias_ok = [a['dias'] for a in animais if a.get('dias') is not None and a.get('kgs') is not None]
    pesos = {
        'peso_total': sum(com_peso) if com_peso else None,
        'peso_medio': (sum(com_peso) / len(com_peso)) if com_peso else None,
        'arroba_vivo': (sum(com_peso) / 15) if com_peso else None,
        'arroba_abate': (sum(com_peso) / 30) if com_peso else None,
        'gmp': (sum(gpds) / len(gpds)) if gpds else None,
        'diarias': int(sum(dias_ok) / len(dias_ok) + 0.5) if dias_ok else None,
    }
    return {
        'pesos': pesos,
        'animais': animais,
        'colunas': colunas,
        'resumo_femeas': resumo_femeas,
        'resumo_machos': resumo_machos,
        'sem_faixa_femeas': sem_faixa['FEMEA'],
        'sem_faixa_machos': sem_faixa['MACHO'],
        'total_femeas': sum(resumo_femeas) + sem_faixa['FEMEA'],
        'total_machos': sum(resumo_machos) + sem_faixa['MACHO'],
        'total': len(animais),
        'cth_femeas': sum(1 for a in animais if a.get('cth') and a['sexo'] == 'FEMEA'),
        'cth_machos': sum(1 for a in animais if a.get('cth') and a['sexo'] == 'MACHO'),
        'fora_liberacao': sum(1 for a in animais if a['obs']),
        'tem_peso': bool(com_peso),
    }


# -------------------------------------------------------
# GET /produtor/saida-relatorio/resumo
# -------------------------------------------------------
@saida_relatorio.route('/produtor/saida-relatorio/resumo')
def resumo():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    tipo = _ler_tipo(request.args.get('tipo', ''))
    qs_t = _qs_tipo(tipo)
    data_emb = _ler_data(request.args.get('data', ''))
    if not data_emb:
        return redirect(f'{URL_DATAS}?id_propriedade={int(id_propriedade)}{qs_t}')

    rel = _montar_relatorio(session['id_produtor'], id_propriedade, data_emb, tipo)
    if rel is None:
        return redirect(f'{URL_DATAS}?id_propriedade={int(id_propriedade)}{qs_t}')

    iso = data_emb.strftime('%Y-%m-%d')
    with Session(engine) as db:   # v1.3.0 - nomes para o texto "Pedido de GTA"
        propriedade = db.get(Propriedade, int(id_propriedade))
        produtor = db.get(Produtor, session['id_produtor'])
        nome_propriedade = propriedade.nome if propriedade else '-'
        nome_produtor = produtor.nome if produtor else ''
    return render_template(
        'produtor/saida_relatorio_resumo.html',
        rel=rel,
        texto_pedido=_texto_pedido_gta(rel, _data_br(data_emb), nome_produtor, nome_propriedade, tipo),
        data_br=_data_br(data_emb),
        tipo=tipo,
        url_pdf=f'{URL_PDF}?id_propriedade={int(id_propriedade)}&data={iso}{qs_t}',
        url_pedido_pdf=f'{URL_PEDIDO_PDF}?id_propriedade={int(id_propriedade)}&data={iso}{qs_t}',
        url_datas=(f'/produtor/saida-consulta/lista?id_propriedade={int(id_propriedade)}&tipo={tipo}' if request.args.get('de') == 'consulta'
                   else f'{URL_DATAS}?id_propriedade={int(id_propriedade)}{qs_t}'),   # s118 - Voltar = caminho real
        **_contexto_base(),
    )


# -------------------------------------------------------
# GET /produtor/saida-relatorio/pdf
# -------------------------------------------------------
@saida_relatorio.route('/produtor/saida-relatorio/pdf')
def pdf():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    data_emb = _ler_data(request.args.get('data', ''))
    if not data_emb:
        return redirect(f'{URL_DATAS}?id_propriedade={int(id_propriedade)}')

    id_produtor = session['id_produtor']
    tipo = _ler_tipo(request.args.get('tipo', ''))
    rel = _montar_relatorio(id_produtor, id_propriedade, data_emb, tipo)
    if rel is None:
        return redirect(f'{URL_DATAS}?id_propriedade={int(id_propriedade)}{_qs_tipo(tipo)}')

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
        produtor = db.get(Produtor, id_produtor)
        vinculo = None
        if produtor is not None:
            vinculo = (db.query(PropriedadeProdutor)
                       .filter_by(id_propriedade=int(id_propriedade), id_produtor=produtor.id, data_fim=None).first())
        cpf, cnpj = documentos_do_produtor(produtor, vinculo)
        inscricao = (getattr(vinculo, 'inscricao_estadual', None) or getattr(propriedade, 'inscricao_estadual', None)
                     or '') if propriedade is not None else ''
        agora = datetime.now()
        ctx = {
            'produtor': produtor.nome if produtor else '',
            'cpf': cpf, 'cnpj': cnpj, 'inscricao_estadual': inscricao,
            'codigo_eras': propriedade.codigo_eras if propriedade else '',
            'propriedade': propriedade.nome if propriedade else '',
            'municipio': municipio_sem_uf(propriedade.municipio, propriedade.uf) if propriedade else '',
            'uf': propriedade.uf if propriedade else '',
            'nirf': (getattr(propriedade, 'nirf_incra', None) or '') if propriedade else '',
            'data_embarque': _data_br(data_emb),
            'gerado_em_completo': agora.strftime('%d/%m/%Y %H:%M:%S'),
        }
    ctx.update(rel)
    ctx['tipo'] = tipo
    buffer = gerar_pdf_relatorio_embarque(ctx)
    nome = f'Relatorio_Embarque_{({TIPO_SAIDA_TRANSFER: "Transferencia_", TIPO_SAIDA_VENDA: "Venda_"}).get(tipo, "")}{data_emb.strftime("%Y-%m-%d")}.pdf'
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome)

# =========================================================
# FIM DE ARQUIVO: backend\routers\saida_relatorio.py
# =========================================================


# -------------------------------------------------------
# GET /produtor/saida-relatorio/pedido-pdf   (s118) - PDF "Pedido de GTA" (sexo x faixa de idade) de um embarque
# -------------------------------------------------------
@saida_relatorio.route('/produtor/saida-relatorio/pedido-pdf')
def pedido_pdf():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    data_emb = _ler_data(request.args.get('data', ''))
    if not data_emb:
        return redirect(URL_INICIAR)
    t = str(request.args.get('tipo', '')).strip().upper()
    tipo = t if t in (TIPO_SAIDA_ABATE, TIPO_SAIDA_TRANSFER, TIPO_SAIDA_VENDA, 'POSSE') else TIPO_SAIDA_ABATE
    id_produtor = session['id_produtor']
    rel = _montar_relatorio(id_produtor, id_propriedade, data_emb, tipo)
    if rel is None:
        return redirect(URL_INICIAR)
    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
        produtor = db.get(Produtor, id_produtor)
        ctx = {
            'produtor': produtor.nome if produtor else '',
            'propriedade': propriedade.nome if propriedade else '',
            'data_embarque': _data_br(data_emb),
            'gerado_em_completo': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'tipo': tipo,
        }
    ctx.update(rel)
    # s118 - Raca x faixa de idade x sexo
    ordem = {f: i for i, f in enumerate(rel['colunas'])}
    grupos = {}
    for a in rel['animais']:
        g = grupos.setdefault((a['raca'], a['faixa']), {'MACHO': 0, 'FEMEA': 0})
        if a['sexo'] in ('MACHO', 'FEMEA'):
            g[a['sexo']] += 1
    ctx['linhas_raca'] = [(r, f if f != '-' else 'SEM FAIXA (sem data de nascimento)', g['MACHO'], g['FEMEA'])
                          for (r, f), g in sorted(grupos.items(), key=lambda kv: (kv[0][0], ordem.get(kv[0][1], 99)))]
    buffer = gerar_pdf_pedido_gta(ctx)
    nome = f'Pedido_de_GTA_{tipo}_{data_emb.strftime("%Y-%m-%d")}.pdf'
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome)
