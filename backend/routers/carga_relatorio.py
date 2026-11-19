# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\Orion\backend\routers
# MODULO: backend\routers\carga_relatorio.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-17 18:43 -03
# ATUALIZADO EM: 2026-11-17 18:43 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Relatorio da Carga em PDF (Produtor e Consiste). Montagem do PDF em
#     backend\utils\pdf_carga.py. Somente leitura.
#
#     ROTAS
#       GET /produtor/carga-relatorio/iniciar          - card do Hub de Entrada (Consultas e Correcoes):
#                                                         escolhe a Propriedade e baixa o PDF
#       GET /produtor/carga-relatorio/gerar?id_propriedade=X - PDF da Propriedade (do Produtor logado)
#       GET /consiste/carga/relatorio?id_produtor=X&id_gta=Y - PDF de qualquer Carga (so CONSISTE)
#
#     v1.0.0: Criacao (Carga, 17/11/2026).
# =========================================================

from flask import Blueprint, redirect, render_template, request, session
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Produtor, Propriedade, PropriedadeProdutor
from backend.routers.auth import buscar_pares_propriedade_produtor, redirecionar_home, resolver_fazenda_em_uso
from backend.routers.inventario_geral import TITULO_PRIMEIRA_FAIXA, _coluna_da_idade
from backend.utils import carga_animais as ca
from backend.utils.documentos_produtor import documentos_do_produtor
from backend.utils.multitenant import get_db_produtor
from backend.utils.pdf_carga import gerar_pdf_carga

carga_relatorio = Blueprint('carga_relatorio', __name__)

VOLTAR_HUB = '/produtor/hub-novo/entrada'
URL_INICIAR = '/produtor/carga-relatorio/iniciar'


def _dados_cabecalho(id_produtor, id_propriedade):
    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
        produtor = db.get(Produtor, int(id_produtor))
        if propriedade is None or produtor is None:
            return None
        vinculo = db.query(PropriedadeProdutor).filter_by(id_propriedade=propriedade.id, id_produtor=produtor.id, data_fim=None).first()
        cpf, cnpj = documentos_do_produtor(produtor, vinculo)
        return {
            'nome': propriedade.nome, 'municipio': propriedade.municipio, 'uf': propriedade.uf,
            'codigo_mapa': propriedade.codigo_mapa, 'nirf': propriedade.nirf_incra, 'produtor_nome': produtor.nome,
            'cpf': cpf, 'cnpj': cnpj, 'inscricao_estadual': propriedade.inscricao_estadual,
            'codigo_eras': propriedade.codigo_eras, 'cep': propriedade.cep,
        }


def _pdf_da_carga(id_produtor, id_propriedade, id_gta=None):
    """Monta e devolve a resposta com o PDF, ou None se nao houver Carga."""
    dados = _dados_cabecalho(id_produtor, id_propriedade)
    if dados is None:
        return None
    with engine.connect() as conn:
        faixas = [dict(r) for r in conn.execute(text(
            'SELECT id, descricao, dias_min, dias_max FROM public.tb_4006_idade_meses ORDER BY codigo_geras')).mappings().all()]
        racas = {i: c for i, c in conn.execute(text('SELECT id, codigo FROM public.tb_4005_racas')).all()}
    colunas = [TITULO_PRIMEIRA_FAIXA] + [f['descricao'] for f in faixas[2:]]

    with get_db_produtor(int(id_produtor)) as db:
        gta = ca.carga_existente(db, int(id_propriedade))
        if gta is None or (id_gta is not None and gta.id != int(id_gta)):
            return None
        data_carga = gta.data_entrega
        linhas = db.execute(text(
            'SELECT DISTINCT ON (sisbov) sisbov, nascimento, sexo, id_raca, data_inclusao '
            'FROM tb_2017_movimentacoes WHERE id_gta_entrada = :g AND tipo_entrada = \'CARGA\' '
            'ORDER BY sisbov, id'), {'g': gta.id}).all()

    resumo = {'FEMEA': [0] * len(colunas), 'MACHO': [0] * len(colunas)}
    animais = []
    for n, (sisbov, nasc, sexo, id_raca, incl) in enumerate(linhas, 1):
        col = _coluna_da_idade((data_carga - nasc).days, faixas) if nasc else None
        col = 0 if col is None else col
        sexo = str(sexo).upper()
        if sexo in resumo:
            resumo[sexo][col] += 1
        animais.append((n, sisbov, nasc.strftime('%d/%m/%Y') if nasc else '', racas.get(id_raca, ''),
                        {'MACHO': 'M', 'FEMEA': 'F'}.get(sexo, ''), incl.strftime('%d/%m/%Y') if incl else '', colunas[col]))
    return gerar_pdf_carga(dados, data_carga, animais, colunas, resumo)


def _tela_aviso(pares, erro=None):
    return render_template(
        'produtor/selecionar_propriedade_produtor.html', pares=pares, erro=erro,
        titulo='Relatório da Carga — Selecionar Propriedade', proximo='/produtor/carga-relatorio/gerar',
        campo_propriedade='id_propriedade', voltar=VOLTAR_HUB,
        usuario_nome=session.get('usuario_nome'), usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A', nome_sistema='Orion SISBOV', menu_ativo='entrada')


@carga_relatorio.route('/produtor/carga-relatorio/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if not pares:
        return _tela_aviso([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')
    par = resolver_fazenda_em_uso(pares)
    if par is None and len(pares) == 1:
        par = pares[0]
    if par is not None:
        session['id_produtor'] = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/carga-relatorio/gerar?id_propriedade={par.id_propriedade}')
    return _tela_aviso(pares)


@carga_relatorio.route('/produtor/carga-relatorio/gerar')
def gerar():
    if 'id_produtor' not in session:
        return redirecionar_home()
    id_propriedade = request.args.get('id_propriedade', '')
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if not id_propriedade.isdecimal() or int(id_propriedade) not in {int(p.id_propriedade) for p in pares if str(p.id_produtor) == str(session.get('id_produtor'))}:
        return redirect(URL_INICIAR)
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and int(par_em_uso.id_propriedade) != int(id_propriedade):
        return redirect(URL_INICIAR)
    resposta = _pdf_da_carga(session['id_produtor'], id_propriedade)
    if resposta is None:
        return _tela_aviso([], 'Esta Propriedade ainda não tem Carga de animais. Quando a Consiste fizer a Carga, o relatório aparece aqui.')
    return resposta


@carga_relatorio.route('/consiste/carga/relatorio')
def relatorio_consiste():
    if 'usuario_id' not in session or session.get('usuario_perfil') != 'CONSISTE':
        return redirecionar_home(session.get('usuario_perfil'))
    id_produtor = request.args.get('id_produtor', type=int)
    id_propriedade = request.args.get('id_propriedade', type=int)
    id_gta = request.args.get('id_gta', type=int)
    if not id_produtor or not id_propriedade or not id_gta:
        return redirect('/consiste/carga')
    resposta = _pdf_da_carga(id_produtor, id_propriedade, id_gta)
    return resposta if resposta is not None else redirect('/consiste/carga')

# =========================================================
# FIM DE ARQUIVO: backend\routers\carga_relatorio.py
# =========================================================
