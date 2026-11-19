# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\routers
# MODULO:       backend\routers\relatorio_eras.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-09-17 10:00 -03
# ATUALIZADO EM: 2026-11-16 10:40 -03
# VERSAO: 1.5.0
# v1.5.0: Sessao 128 (2026-11-16 10:40 -03) - AUDITORIA ETAPA 7b (Regra #57/#73): a trava _propriedade_permitida() passa a conferir tambem que o Produtor do par Propriedade+Produtor e o Produtor da sessao (antes so conferia a Propriedade). REVERSAO: .bak_antes_etapa7b.
# v1.4.0: Sessao 123 (2026-11-13 19:50 -03) - AUDITORIA ETAPA 6 (leitura a fundo): (a) tela das faixas avisa quantos animais estao sem Data de Nascimento (nao entram em nenhuma faixa); (b) gerar(): redirecionamentos silenciosos passam a mostrar faixa amarela (Regra #69). REVERSAO: .bak_antes_etapa6d.
# v1.3.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Relatorio de ERAS (faixa etaria) - Sessao 054/055.
#     Fluxo (Padrao Reutilizavel No 1, sem tela intermediaria de
#     "Consultas de Animais" do legado GERAS):
#
#       1. /produtor/relatorio-eras/iniciar - resolve Propriedade
#          E Produtor (mesmo padrao de gta_manual.py::iniciar()
#          v1.4.0). Com 1 unico par, pula direto pra faixas().
#          Com 2+ pares, mostra selecionar_propriedade_produtor.html.
#
#       2. /produtor/relatorio-eras/faixas - mostra os 5 botoes de
#          faixa etaria, lidos DINAMICAMENTE de tb_4006_idade_meses
#          (nunca fixados no codigo - decisao Sessao 054).
#
#       3. /produtor/relatorio-eras/gerar - usuario escolheu a
#          faixa; filtra os animais em estoque (presenca em
#          tb_2001, ver Semantica de Estoque) da Propriedade
#          escolhida, calcula a idade em dias NA HORA a partir de
#          Entrada.nascimento (NUNCA le/grava Entrada.eras_dias -
#          esse campo e residuo do legado GERAS e fica intocado),
#          filtra pelo intervalo dias_min/dias_max da faixa, ordena
#          por numero de Manejo, e entrega o PDF (gerado em
#          backend/utils/pdf_relatorio_eras.py - PROXIMO ARQUIVO).
#
#     Padrao de idade calculada-vs-gravada (Sessao 054): idade
#     ATUAL nunca e gravada, sempre calculada na hora. Este modulo
#     e o primeiro a aplicar essa regra na pratica.
#
#     Semantica de estoque (Sessao 054): todo animal presente em
#     tb_2001 esta em estoque - nao existe campo de status
#     separado, a query simplesmente le tb_2001 da Propriedade.
#
#     v1.0.0: Criacao do modulo (Sessao 055, 17/09/2026, 10:00 -03).
#     v1.1.0: Sessao 090 (08/10/2026, 08:35 -03) - FAZENDA EM USO (Lote 4):
#             FAZENDA EM USO (Regra de Ouro #13): a tela "Selecionar Propriedade" deixa
#             de aparecer quando ha fazenda em uso (auth.resolver_fazenda_em_uso).
#               - iniciar(): com fazenda em uso, abre as Faixas direto nela.
#               - VOLTAR (Regra #9): faixas() passa url_voltar ao template (Hub
#                 de Entrada novo; so volta para a selecao quem tem 2+ pares e
#                 nenhuma fazenda em uso); a tela de selecao tambem volta ao Hub.
#               - TRAVA (_propriedade_permitida): faixas() e gerar() passam a
#                 conferir que a Propriedade e do usuario (antes nao conferiam)
#                 e, havendo fazenda em uso, que e a propria fazenda em uso.
#                 Se nao for, mandam para o iniciar(). Nenhum PDF e gerado.
#             Nenhuma mudanca no calculo de idade nem no PDF. Template
#             inalterado (o topo ja le url_voltar).
#     v1.2.0: Sessao 102 (21/10/2026, 11:50 -03) - PDF NO VISUAL DO MAGIC/GERAS: gerar() monta o contexto do cabecalho (Produtor com
#             CPF/CNPJ DESTA fazenda, Insc. Estadual, Cod. ERAS, Municipio/UF sem duplicar, NIRF) e o mapa de Raca (id -> codigo) e
#             manda ao pdf_relatorio_eras 2.0.0. Filtro de faixa, ordenacao e telas IGUAIS. REVERSAO: .bak_antes_visual_magic_s102.
#     v1.2.1: Sessao 117 (2026-11-06 18:05 -03) - PDF mostra o Produtor LOGADO, nao o primeiro vinculo da Propriedade (defeito com 2+ Produtores). Nenhuma outra mudanca. REVERSAO: .bak_antes_s117_produtor.
# =========================================================

from datetime import date
from flask import Blueprint, render_template, request, redirect, session
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, PropriedadeProdutor, Produtor
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.routers.gta_manual import municipio_sem_uf
from backend.utils.documentos_produtor import documentos_do_produtor
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.pdf_relatorio_eras import gerar_pdf_relatorio_eras


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
relatorio_eras = Blueprint('relatorio_eras', __name__)


# -------------------------------------------------------
# Constantes e auxiliares de navegacao (v1.1.0 / Sessao 090 - Lote 4).
# VOLTAR_HUB: o Hub onde mora o card deste modulo (Hub de Entrada novo).
# -------------------------------------------------------
VOLTAR_HUB = '/produtor/hub-novo/entrada'
URL_INICIAR = '/produtor/relatorio-eras/iniciar'
CHAVE_AVISO_ERAS = 'aviso_relatorio_eras'   # Regra #69: aviso que acompanha o redirecionamento


# Destino do Voltar (Regra de Ouro #9): so volta para a selecao quem tem 2+
# pares e nenhuma fazenda em uso; nos demais casos a selecao e pulada e o
# Voltar vai direto ao Hub (voltar ao iniciar() reabriria a tela: laco).
def _url_voltar(pares):
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return URL_INICIAR
    return VOLTAR_HUB


# TRAVA DA FAZENDA EM USO (v1.1.0): a Propriedade tem de ser de um par do
# usuario logado E, havendo fazenda em uso, ser a propria fazenda em uso.
def _propriedade_permitida(id_propriedade, pares):
    if not str(id_propriedade).isdecimal():
        return False
    if int(id_propriedade) not in {int(par.id_propriedade) for par in pares if str(par.id_produtor) == str(session.get('id_produtor'))}:   # v1.5.0 - Produtor do par = Produtor da sessao (Etapa 7b)
        return False
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and int(par_em_uso.id_propriedade) != int(id_propriedade):
        return False
    return True


# -------------------------------------------------------
# Rota: GET /produtor/relatorio-eras/iniciar - ponto de partida.
# Copia exata da logica de gta_manual.py::iniciar() v1.4.0
# (Padrao Reutilizavel No 1) - so troca o destino final: em vez
# de seguir pro fluxo de GTA, segue pra faixas() deste modulo.
# -------------------------------------------------------
@relatorio_eras.route('/produtor/relatorio-eras/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            titulo='Relatório de ERAS — Selecionar Propriedade',
            proximo='/produtor/relatorio-eras/faixas',
            campo_propriedade='id_propriedade',
            voltar=VOLTAR_HUB,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='entrada',
        )

    # v1.1.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/relatorio-eras/faixas?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/relatorio-eras/faixas?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        titulo='Relatório de ERAS — Selecionar Propriedade',
        proximo='/produtor/relatorio-eras/faixas',
        campo_propriedade='id_propriedade',
        voltar=VOLTAR_HUB,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/relatorio-eras/faixas - mostra os 5 botoes
# de faixa etaria. Le tb_4006_idade_meses dinamicamente (nunca
# hardcoded) - se um dia mudar no banco, a tela acompanha sem
# precisar tocar em codigo.
# -------------------------------------------------------
@relatorio_eras.route('/produtor/relatorio-eras/faixas')
def faixas():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')

    if not id_propriedade:
        return redirect('/produtor/relatorio-eras/iniciar')

    # v1.1.0 - trava da fazenda em uso (e Propriedade tem de ser do usuario).
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if not _propriedade_permitida(id_propriedade, pares):
        return redirect('/produtor/relatorio-eras/iniciar')

    with Session(engine) as db:
        faixas_etarias = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras).all()

    # v1.4.0 - animais sem Data de Nascimento nao entram em nenhuma faixa: avisa (Regra #69)
    with get_db_produtor(session['id_produtor']) as db:
        sem_nascimento = db.query(Entrada).filter(
            Entrada.id_propriedade == int(id_propriedade),
            Entrada.nascimento.is_(None)
        ).count()

    return render_template(
        'produtor/relatorio_eras_faixas.html',
        faixas_etarias=faixas_etarias,
        sem_nascimento=sem_nascimento,
        aviso=session.pop(CHAVE_AVISO_ERAS, None),
        id_propriedade=id_propriedade,
        url_voltar=_url_voltar(pares),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Funcao auxiliar: busca Propriedade + Produtor vinculado, para
# o cabeçalho do PDF (mesmo padrao de
# gta_manual.py::_buscar_dados_exibicao() - vinculo ativo,
# data_fim IS NULL). So leitura, so para exibicao no cabecalho.
# -------------------------------------------------------
def _buscar_propriedade_produtor(id_propriedade):
    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))

        produtor = None
        if propriedade:
            vinculo = db.query(PropriedadeProdutor).filter_by(
                id_propriedade=propriedade.id,
                id_produtor=session['id_produtor'],   # v1.2.1: Produtor LOGADO
                data_fim=None
            ).first()
            if vinculo:
                produtor = db.get(Produtor, vinculo.id_produtor)

    return propriedade, produtor


# -------------------------------------------------------
# Rota: GET /produtor/relatorio-eras/gerar - usuario escolheu a
# faixa; filtra, calcula idade NA HORA e entrega o PDF.
#
# REGRA DE OURO (idade calculada, nunca gravada - Sessao 054):
# idade_dias = (hoje - Entrada.nascimento).days, calculado a cada
# chamada desta rota. NUNCA le Entrada.eras_dias (residuo do
# legado GERAS, fica intocado - confirmado com Benedito,
# Sessao 055).
# -------------------------------------------------------
@relatorio_eras.route('/produtor/relatorio-eras/gerar')
def gerar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    codigo_geras_str = request.args.get('codigo_geras', '')

    if not (id_propriedade and codigo_geras_str):
        session[CHAVE_AVISO_ERAS] = 'O pedido do relatório veio incompleto. Escolha a faixa de idade de novo nos botões abaixo.'
        return redirect('/produtor/relatorio-eras/iniciar')

    # v1.1.0 - trava da fazenda em uso (e Propriedade tem de ser do usuario).
    if not _propriedade_permitida(id_propriedade, buscar_pares_propriedade_produtor(session['usuario_id'])):
        return redirect('/produtor/relatorio-eras/iniciar')

    try:
        codigo_geras = int(codigo_geras_str)
    except ValueError:
        session[CHAVE_AVISO_ERAS] = 'O pedido do relatório veio incompleto. Escolha a faixa de idade de novo nos botões abaixo.'
        return redirect(f'/produtor/relatorio-eras/faixas?id_propriedade={id_propriedade}')

    with Session(engine) as db:
        faixa = db.query(IdadeMeses).filter_by(codigo_geras=codigo_geras).first()

    if not faixa:
        session[CHAVE_AVISO_ERAS] = 'Essa faixa de idade não existe mais na lista. Escolha uma das faixas abaixo; se o problema repetir, avise a Consiste.'
        return redirect(f'/produtor/relatorio-eras/faixas?id_propriedade={id_propriedade}')

    # ---------------------------------------------------
    # Bloco: filtro por faixa etaria, idade calculada na hora.
    # Estoque = presenca em tb_2001 (Semantica de Estoque,
    # Sessao 054) - a query ja e o proprio filtro de estoque.
    # ---------------------------------------------------
    hoje = date.today()

    with get_db_produtor(session['id_produtor']) as db:
        animais_propriedade = db.query(Entrada).filter(
            Entrada.id_propriedade == int(id_propriedade)
        ).all()

        animais_na_faixa = []
        for animal in animais_propriedade:
            if not animal.nascimento:
                continue  # sem data de Nascimento nao entra em nenhuma faixa

            idade_dias = (hoje - animal.nascimento).days

            if faixa.dias_min <= idade_dias <= faixa.dias_max:
                animais_na_faixa.append(animal)

        animais_na_faixa.sort(key=lambda a: a.manejo or '')
        racas = {r.id: r.codigo for r in db.query(Raca).all()}

    # ---------------------------------------------------
    # Bloco: cabecalho do PDF (Propriedade/Produtor).
    # ---------------------------------------------------
    propriedade, produtor = _buscar_propriedade_produtor(id_propriedade)

    # v1.2.0 - cabecalho do Magic: Produtor com CPF/CNPJ desta fazenda
    vinculo = None
    if produtor is not None:
        with Session(engine) as db:
            vinculo = db.query(PropriedadeProdutor).filter_by(
                id_propriedade=int(id_propriedade), id_produtor=produtor.id, data_fim=None).first()
    cpf, cnpj = documentos_do_produtor(produtor, vinculo)
    contexto = {
        'produtor': produtor.nome if produtor else '',
        'cpf': cpf, 'cnpj': cnpj,
        'inscricao_estadual': (getattr(vinculo, 'inscricao_estadual', None)
                               or getattr(propriedade, 'inscricao_estadual', None) or '') if propriedade else '',
        'codigo_eras': propriedade.codigo_eras if propriedade else '',
        'propriedade': propriedade.nome if propriedade else '',
        'municipio': municipio_sem_uf(propriedade.municipio, propriedade.uf) if propriedade else '',
        'uf': propriedade.uf if propriedade else '',
        'nirf': (getattr(propriedade, 'nirf_incra', None) or '') if propriedade else '',
        'racas': racas,
    }

    return gerar_pdf_relatorio_eras(
        animais=animais_na_faixa,
        faixa=faixa,
        propriedade=propriedade,
        produtor=produtor,
        contexto=contexto,
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\relatorio_eras.py
# =========================================================