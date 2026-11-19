# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\proprietarios.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-06 11:50 -03
# ATUALIZADO EM: 2026-11-12 19:00 -03
# VERSAO: 2.8.0
# v2.8.0: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras no CNPJ aceitas e conferidas; CNPJ antigo continua valendo. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Rotas do modulo de Proprietario (plataforma Consiste).
#     Cadastro exclusivo da Consiste, perfil CONSISTE - acesso
#     da Certificadora fica para quando o Modulo Certificadora
#     (fluxo MAPA/P-013) for construido - EXCETO para o perfil
#     PRODUTOR cadastrar/vincular/EDITAR um Proprietario da sua
#     PROPRIA Propriedade (P-040, ver v2.4.0 e v2.6.0 abaixo).
#     - /proprietarios                          -> lista todos, com busca
#     - /proprietarios/novo                     -> formulario novo,
#                                                   EXIGE ?id_propriedade=<id>
#     - /proprietarios/salvar                    -> salva novo/edicao/vinculo
#     - /proprietarios/editar/<id>                -> formulario edicao,
#                                                   ACEITA ?id_propriedade=<id>
#                                                   (v2.6.0)
#     - /proprietarios/toggle/<id>                -> ativa ou inativa
#     - /proprietarios/toggle-vinculo/<id_vinculo> -> alterna vinculo com
#                                                   Propriedade entre Ativo e
#                                                   Inativo (reversivel)
#     - /proprietarios/relatorio/<id>              -> gera PDF com dados do
#                                                   Proprietario + Propriedades
#                                                   ativas vinculadas
#
#     Regras de negocio aplicadas:
#     - NAO EXISTE MAIS cadastro avulso de Proprietario. Todo Novo
#       Proprietario nasce vinculado a uma Propriedade especifica -
#       a rota /proprietarios/novo exige id_propriedade na URL.
#     - Ao digitar o CPF/CNPJ na tela de Novo Proprietario, o
#       JAVASCRIPT (proprietario_cadastro.html) chama sempre
#       /api/busca-cpf-cnpj ao sair do campo. Se encontrar, o
#       formulario preenche e TRAVA todos os campos (readonly) -
#       o botao vira "Vincular", e o servidor NAO cria nem
#       atualiza o Proprietario, so cria o vinculo com a
#       Propriedade (campo hidden id_existente identifica quem
#       vincular).
#     - Se nao encontrar, os campos ficam liberados normalmente -
#       o servidor cria o Proprietario E o vinculo com a
#       Propriedade, na mesma operacao (evita 2 passos separados).
#     - Apos salvar com sucesso vindo de uma Propriedade, mostra
#       tela de confirmacao com botoes "Voltar" (retorna a
#       Propriedade de origem) e "Home".
#     - tipo_pessoa (FISICA/JURIDICA) e visibilidade (PUBLICO/
#       PRIVADO) validados contra listas fechadas no servidor.
#     - Quando FISICA: campo nome sempre espelha razao_social
#       (forcado tambem no servidor - JS ja faz isso na tela).
#     - cpf_cnpj: recebido do formulario com mascara (JS), salvo
#       no banco somente com digitos limpos (11 CPF, 14 CNPJ).
#     - UF validado contra lista fechada de 27 estados.
#     - Telefone/Telefone2/CEP: mascara na tela, banco recebe
#       somente digitos.
#     - Validacao de tamanho maximo de cada campo de texto no
#       servidor, batendo com o limite real da coluna no banco.
#     - Todos os campos de texto em UPPERCASE, exceto email.
#     - Relatorio em PDF (xhtml2pdf): mostra apenas Propriedades
#       ATIVAS (vinculo sem data_fim) vinculadas ao Proprietario,
#       com a logo da Consiste no cabecalho. Usa link_callback_pdf
#       (importado de backend/utils/pdf_helper.py - ver P-023)
#       porque o xhtml2pdf nao consegue resolver caminhos
#       "/static/..." sozinho - ele precisa do caminho absoluto do
#       arquivo no disco.
#
#     v1.0.0: Criacao do modulo (CRUD basico).
#     v2.0.0: Sessao 011.1 - Removido cadastro avulso (novo()
#             agora exige id_propriedade). Adicionada logica de
#             vinculo/criacao combinada em salvar(). Adicionada
#             rota encerrar_vinculo(). Adicionada rota
#             relatorio_pdf() com xhtml2pdf. Adicionada tela de
#             confirmacao pos-salvar (Voltar/Home).
#     v2.1.0: Sessao 011.1 - Trocado encerrar_vinculo() (acao
#             unica, so encerrava) por toggle_vinculo() (acao
#             reversivel, mesmo padrao ja usado em Propriedade/
#             Proprietario/Protocolos). Ativo -> Inativo grava
#             data_fim = hoje; Inativo -> Ativo limpa data_fim
#             (reativa o vinculo). Motivo: Benedito preferiu
#             reaproveitar o padrao Ativo/Inativo em vez de um
#             botao "Encerrar" com confirmacao separada.
#     v2.2.0: Sessao 011.2 - Adicionado _link_callback_pdf()
#             (mesma funcao criada em produtores.py) para o
#             xhtml2pdf conseguir carregar a logo da Consiste no
#             cabecalho do relatorio (proprietario_relatorio_pdf.html
#             v1.1.0, padrao visual novo). Sem essa funcao, a
#             imagem apareceria em branco no PDF.
#     v2.3.0: Sessao do dia 08/07/2026 - Resolvida a pendencia
#             P-023 (formalizar o padrao de PDF). A funcao
#             _link_callback_pdf() (identica a de produtores.py -
#             duplicacao real de codigo, confirmada nesta sessao)
#             saiu daqui e virou backend/utils/pdf_helper.py,
#             funcao publica link_callback_pdf(). Este arquivo so
#             importa e usa. Nenhuma mudanca de comportamento no
#             relatorio gerado.
#     v2.4.0: Sessao 032 - P-040, complemento: Benedito identificou
#             que a Propriedade pre-cadastrada pelo Convite Publico
#             ficava sem NENHUM Proprietario (a secao havia sido
#             escondida do Produtor por seguranca de rota, ver
#             propriedade_cadastro.html v1.12.0) - mas o sistema
#             nao tem como saber se aquele Produtor e o dono da
#             terra ou um arrendatario, entao nao da para preencher
#             isso automaticamente. Decisao: reabrir novo()/salvar()/
#             toggle_vinculo() tambem para o perfil PRODUTOR, MAS
#             apenas para a Propriedade vinculada a ele mesmo -
#             reaproveitada a funcao _produtor_possui_propriedade()
#             ja criada em propriedades.py (import direto, sem
#             duplicar). Edicao avulsa (id presente, via
#             /proprietarios/editar/<id>) continuava exclusiva
#             CONSISTE - o Produtor so cria/vincula um Proprietario
#             novo a sua Propriedade, nunca editava um ja existente
#             por essa via (mudou na v2.6.0, ver abaixo).
#     v2.5.0: Sessao 033 - Correcao de linguagem: as 5 mensagens de
#             erro deste arquivo usavam "invalido/invalida" (Tipo de
#             Pessoa, Visibilidade, UF, CPF, CNPJ), escritas antes da
#             regra de linguagem do sistema existir (nunca usar
#             "invalido/invalida" em mensagens voltadas ao usuario -
#             usar "incorreto/incorreta" no lugar). Identificado ao
#             revisar o arquivo durante o teste do wizard de
#             onboarding (P-040). Nenhuma mudanca de comportamento,
#             so o texto das mensagens.
#     v2.6.0: Sessao 033 - Benedito identificou que a lista de
#             Proprietario(s) em propriedade_cadastro.html so tinha
#             Ativar/Inativar, sem nenhuma forma de EDITAR os dados
#             ja vinculados. Decisao: trocar aquele botao por um
#             link "Editar" (propriedade_cadastro.html v1.17.0), o
#             que exige liberar editar()/salvar() tambem para o
#             perfil PRODUTOR - antes exclusivos CONSISTE. Novo
#             helper _vinculo_proprietario_propriedade() confere se
#             ha vinculo (ativo ou inativo) entre o Proprietario e a
#             Propriedade - usado como checagem de seguranca (o
#             PRODUTOR so edita quem ja esta vinculado a sua propria
#             Propriedade) e para buscar o id_vinculo/status a
#             mostrar na tela. Decisao de Benedito: PRODUTOR edita
#             SO dados de contato/endereco - Tipo de Pessoa e
#             CPF/CNPJ ficam travados (o servidor ignora esses dois
#             campos vindos do formulario quando perfil == PRODUTOR
#             e id presente, usando sempre o valor ja gravado no
#             banco - nao confia so na tela travada). O controle de
#             status (Ativo/Inativo) que antes ficava na lista
#             migrou para dentro desta tela (novo bloco "Vinculo com
#             esta Propriedade", que continua chamando a MESMA rota
#             toggle_vinculo() de sempre - nenhuma mudanca nela).
#             Redirecionamento pos-salvar (edicao com id) passa a
#             depender do perfil: CONSISTE -> proprietarios.lista
#             (como sempre); PRODUTOR -> propriedades.editar (nao
#             tem acesso a lista).
#     v2.7.0: Sessao 034 (continuacao 9, 13/08/2026, 09:30 -03) -
#             Mesma lacuna real encontrada e corrigida em
#             produtores.py v1.8.0 (Sessao 034, cont. 8): salvar()
#             so conferia TAMANHO do CPF/CNPJ, nunca o digito
#             verificador. Corrigido: nova validacao logo apos as
#             checagens de tamanho existentes, reaproveitando
#             validar_cpf()/validar_cnpj() de backend/utils/
#             validadores.py (mesmo algoritmo, nenhum codigo novo).
#             Mensagem de erro distinta da checagem de tamanho
#             ("digito verificador nao confere"), para o usuario
#             entender que o problema NAO e faltar/sobrar digito,
#             e sim o numero em si estar incorreto. IMPORTANTE: a
#             validacao e pulada quando perfil == 'PRODUTOR' e id
#             esta presente (edicao de um Proprietario ja vinculado,
#             via link "Editar") - nesse caminho o CPF/CNPJ que
#             chega ao validador NUNCA e o do formulario (o bloco
#             logo acima, ja existente desde a v2.6.0, sobrescreve
#             com o valor gravado no banco, ignorando o campo do
#             form) - validar um dado que o usuario nem consegue
#             corrigir naquela tela (campo travado/readonly)
#             travaria para sempre a edicao de contato/endereco de
#             um cadastro que ja tenha nascido com CPF/CNPJ errado.
#             Nesse cenario, a correcao do documento continua
#             possivel apenas pela CONSISTE (acesso total, sem essa
#             trava, via /proprietarios/editar/<id> sem contexto de
#             Propriedade). Nos demais casos (CONSISTE criando ou
#             editando, PRODUTOR criando um Proprietario novo via
#             novo()) o CPF/CNPJ vem do formulario e a validacao se
#             aplica normalmente.
#     v2.7.1: Sessao 097 (15/10/2026, 11:20 -03) - AUDITORIA DE PERMISSOES: toggle()/salvar() conferiam so o login; passam a
#             exigir perfil CONSISTE, a mesma regra das telas desta rota. Nenhuma outra mudanca.
# =========================================================

import os
import re
from datetime import date
from io import BytesIO
from types import SimpleNamespace
from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, current_app
from backend.database import engine
from backend.models import Proprietario, Propriedade, PropriedadeProprietario
from backend.utils.pdf_helper import link_callback_pdf
from backend.utils.validadores import validar_cpf, validar_cnpj, limpar_documento
from backend.routers.auth import redirecionar_home
from backend.routers.propriedades import _produtor_possui_propriedade
from sqlalchemy.orm import Session
from xhtml2pdf import pisa

# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
proprietarios = Blueprint('proprietarios', __name__)

# -------------------------------------------------------
# Listas fechadas de validacao
# -------------------------------------------------------
TIPOS_PESSOA = ['FISICA', 'JURIDICA']
VISIBILIDADES = ['PUBLICO', 'PRIVADO']

# -------------------------------------------------------
# UFs do Brasil - lista fechada para o dropdown de UF
# -------------------------------------------------------
UFS_BRASIL = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
    'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
    'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]


# -------------------------------------------------------
# Funcao auxiliar (Sessao 033): confere se ha vinculo (ativo
# OU inativo) entre o Proprietario e a Propriedade informados,
# e devolve o objeto PropriedadeProprietario (ou None). Usada
# como checagem de seguranca em editar()/salvar() - PRODUTOR
# so edita quem ja esta vinculado a sua propria Propriedade -
# e para buscar o id_vinculo/status a mostrar na tela (bloco
# "Vinculo com esta Propriedade").
# -------------------------------------------------------
def _vinculo_proprietario_propriedade(db, id_proprietario, id_propriedade):
    return db.query(PropriedadeProprietario).filter(
        PropriedadeProprietario.id_proprietario == id_proprietario,
        PropriedadeProprietario.id_propriedade == id_propriedade
    ).first()


# -------------------------------------------------------
# Rota: /proprietarios — lista todos, com busca por nome
# Requer perfil CONSISTE. Serve so para consulta/alteracao/
# impressao - nao tem mais botao "Novo" aqui (ver v2.0.0).
# -------------------------------------------------------
@proprietarios.route('/proprietarios')
def lista():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    termo_busca = request.args.get('busca', '').strip()

    with Session(engine) as db:
        query = db.query(Proprietario)
        if termo_busca:
            query = query.filter(
                (Proprietario.nome.ilike(f'%{termo_busca}%')) |
                (Proprietario.razao_social.ilike(f'%{termo_busca}%'))
            )
        lista_proprietarios = query.order_by(Proprietario.nome).all()

    return render_template('consiste/proprietario_lista.html',
        proprietarios  = lista_proprietarios,
        termo_busca    = termo_busca,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'proprietarios'
    )


# -------------------------------------------------------
# Rota: /proprietarios/novo — formulario novo
# EXIGE ?id_propriedade=<id> - nao existe mais cadastro
# avulso. Sem o parametro, redireciona para a lista de
# Propriedades (nao ha contexto para vincular).
#
# Requer perfil CONSISTE, OU perfil PRODUTOR desde que a
# Propriedade seja a dele mesmo (P-040, Sessao 032 -
# _produtor_possui_propriedade(), importada de propriedades.py).
# -------------------------------------------------------
@proprietarios.route('/proprietarios/novo')
def novo():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    perfil = session.get('usuario_perfil')
    id_propriedade = request.args.get('id_propriedade')

    if not id_propriedade:
        # PRODUTOR nunca chega aqui sem contexto de Propriedade -
        # nao ha lista de Propriedades para ele acessar.
        return redirecionar_home(perfil) if perfil == 'PRODUTOR' else redirect(url_for('propriedades.lista'))

    with Session(engine) as db:
        if perfil == 'CONSISTE':
            pass  # acesso total, como sempre
        elif perfil == 'PRODUTOR' and _produtor_possui_propriedade(db, int(id_propriedade)):
            pass  # acesso liberado so a esta Propriedade (P-040)
        else:
            return redirecionar_home(perfil)

        propriedade = db.get(Propriedade, int(id_propriedade))
        if not propriedade:
            return redirecionar_home(perfil) if perfil == 'PRODUTOR' else redirect(url_for('propriedades.lista'))

    return render_template('consiste/proprietario_cadastro.html',
        proprietario     = None,
        id_propriedade   = id_propriedade,
        nome_propriedade = propriedade.nome,
        travar_documento = False,
        id_vinculo       = None,
        vinculo_ativo    = None,
        tipos_pessoa     = TIPOS_PESSOA,
        visibilidades    = VISIBILIDADES,
        ufs              = UFS_BRASIL,
        erro             = None,
        usuario_nome     = session.get('usuario_nome'),
        usuario_perfil   = session.get('usuario_perfil'),
        cor_primaria     = session.get('cor_primaria', '#D4370A'),
        nome_sistema     = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo       = 'proprietarios'
    )


# -------------------------------------------------------
# Rota: /proprietarios/editar/<id> — formulario edicao
#
# Ate a v2.5.0, exclusiva CONSISTE (consulta/alteracao avulsa,
# sem vinculo com Propriedade). A partir da v2.6.0, tambem
# aceita ?id_propriedade=<id> e libera o perfil PRODUTOR -
# MAS apenas para um Proprietario ja vinculado (ativo ou
# inativo) a Propriedade dele mesmo (P-040, Sessao 033 -
# _vinculo_proprietario_propriedade()). Quando o perfil e
# PRODUTOR, a flag travar_documento vai True para o template
# travar Tipo de Pessoa e CPF/CNPJ (ele so edita contato/
# endereco). O bloco "Vinculo com esta Propriedade" (status +
# botao Ativar/Inativar) so aparece quando id_propriedade foi
# informado - tanto para CONSISTE quanto para PRODUTOR.
# -------------------------------------------------------
@proprietarios.route('/proprietarios/editar/<int:id>')
def editar(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    perfil = session.get('usuario_perfil')
    id_propriedade = request.args.get('id_propriedade')

    with Session(engine) as db:
        if perfil == 'CONSISTE':
            pass  # acesso total, como sempre
        elif perfil == 'PRODUTOR':
            if not id_propriedade or not _produtor_possui_propriedade(db, int(id_propriedade)):
                return redirecionar_home(perfil)
        else:
            return redirecionar_home(perfil)

        vinculo = None
        if id_propriedade:
            vinculo = _vinculo_proprietario_propriedade(db, id, int(id_propriedade))
            if perfil == 'PRODUTOR' and not vinculo:
                # PRODUTOR so edita Proprietario ja vinculado a
                # SUA Propriedade - qualquer outro caso e barrado.
                return redirecionar_home(perfil)

        proprietario = db.get(Proprietario, id)
        propriedade = db.get(Propriedade, int(id_propriedade)) if id_propriedade else None

    return render_template('consiste/proprietario_cadastro.html',
        proprietario     = proprietario,
        id_propriedade   = id_propriedade,
        nome_propriedade = propriedade.nome if propriedade else None,
        travar_documento = (perfil == 'PRODUTOR'),
        id_vinculo       = vinculo.id if vinculo else None,
        vinculo_ativo    = (vinculo.data_fim is None) if vinculo else None,
        tipos_pessoa     = TIPOS_PESSOA,
        visibilidades    = VISIBILIDADES,
        ufs              = UFS_BRASIL,
        erro             = None,
        usuario_nome     = session.get('usuario_nome'),
        usuario_perfil   = session.get('usuario_perfil'),
        cor_primaria     = session.get('cor_primaria', '#D4370A'),
        nome_sistema     = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo       = 'proprietarios'
    )


# -------------------------------------------------------
# Rota: /proprietarios/salvar — salva novo, edicao, ou
# apenas vincula um Proprietario ja existente a uma
# Propriedade.
#
# Campos hidden que controlam o comportamento:
#   - id            -> presente = edicao (avulsa CONSISTE, ou
#                       agora tambem PRODUTOR editando alguem
#                       ja vinculado a sua Propriedade - v2.6.0)
#   - id_propriedade -> presente = veio do fluxo "Adicionar
#                        Proprietario"/"Editar" dentro de uma
#                        Propriedade
#   - id_existente   -> presente = o JS encontrou este CPF/CNPJ
#                        no banco (busca-cpf-cnpj); so vincula,
#                        NAO cria nem atualiza o Proprietario
#
# P-040 (Sessao 032, ajustado na v2.6.0): perfil PRODUTOR so
# pode submeter com id_propriedade preenchido E dono da
# Propriedade. Se vier com id (edicao), exige tambem que o
# Proprietario ja esteja vinculado aquela Propriedade. Quando
# PRODUTOR edita (id presente), Tipo de Pessoa e CPF/CNPJ sao
# SEMPRE recarregados do banco, ignorando o que veio do
# formulario - nao confia so na tela travada (a mesma logica
# ja usada na trava de onboarding da Propriedade).
# -------------------------------------------------------
@proprietarios.route('/proprietarios/salvar', methods=['POST'])
def salvar():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    perfil         = session.get('usuario_perfil')
    id             = request.form.get('id')
    id_propriedade = request.form.get('id_propriedade')
    id_existente   = request.form.get('id_existente')

    # --- Checagem de permissao (P-040, ajustado v2.6.0) ---
    if perfil == 'CONSISTE':
        pass  # acesso total, como sempre
    elif perfil == 'PRODUTOR':
        if not id_propriedade:
            return redirecionar_home(perfil)
        with Session(engine) as db:
            if not _produtor_possui_propriedade(db, int(id_propriedade)):
                return redirecionar_home(perfil)
            if id and not _vinculo_proprietario_propriedade(db, int(id), int(id_propriedade)):
                return redirecionar_home(perfil)
    else:
        return redirecionar_home(perfil)

    # -----------------------------------------------------
    # Caso B1: Proprietario ja existe (achou pelo CPF/CNPJ) -
    # so cria o vinculo, nao mexe nos dados do Proprietario.
    # -----------------------------------------------------
    if id_propriedade and id_existente:
        with Session(engine) as db:
            novo_vinculo = PropriedadeProprietario(
                id_propriedade  = int(id_propriedade),
                id_proprietario = int(id_existente),
                data_inicio     = date.today()
            )
            db.add(novo_vinculo)
            db.commit()

            proprietario = db.get(Proprietario, int(id_existente))
            propriedade  = db.get(Propriedade, int(id_propriedade))

            return render_template('consiste/proprietario_vinculado.html',
                proprietario     = proprietario,
                propriedade      = propriedade,
                usuario_nome     = session.get('usuario_nome'),
                usuario_perfil   = session.get('usuario_perfil'),
                cor_primaria     = session.get('cor_primaria', '#D4370A'),
                nome_sistema     = session.get('nome_sistema', 'Orion SISBOV'),
                menu_ativo       = 'proprietarios'
            )

    # -----------------------------------------------------
    # Casos A e B2: cria novo Proprietario, ou atualiza um
    # ja existente (edicao avulsa CONSISTE, ou edicao PRODUTOR
    # de alguem ja vinculado - v2.6.0).
    # -----------------------------------------------------
    tipo_pessoa   = request.form.get('tipo_pessoa', '').upper()
    razao_social  = request.form.get('razao_social', '').upper()
    nome          = request.form.get('nome', '').upper()
    visibilidade  = request.form.get('visibilidade', '').upper()
    cpf_cnpj      = limpar_documento(request.form.get('cpf_cnpj', ''))
    email         = request.form.get('email', '').strip().lower()
    telefone      = re.sub(r'\D', '', request.form.get('telefone', ''))
    telefone2     = re.sub(r'\D', '', request.form.get('telefone2', ''))
    logradouro    = request.form.get('logradouro', '').upper()
    numero        = request.form.get('numero', '').upper()
    complemento   = request.form.get('complemento', '').upper()
    bairro        = request.form.get('bairro', '').upper()
    cep           = re.sub(r'\D', '', request.form.get('cep', ''))
    municipio     = request.form.get('municipio', '').upper()
    uf            = request.form.get('uf', '').upper()

    # P-040, Sessao 033: PRODUTOR editando um Proprietario ja
    # vinculado NAO pode alterar Tipo de Pessoa nem CPF/CNPJ -
    # trava no servidor, ignorando o que veio do formulario
    # (a tela ja vem travada, mas isso garante mesmo que o
    # HTML seja manipulado).
    #
    # v2.7.0: esta e a MESMA trava que faz a validacao de DV
    # (logo abaixo) ser pulada nesse caminho especifico - a
    # partir daqui, cpf_cnpj JA NAO E MAIS o que veio do
    # formulario, e sim o valor gravado no banco.
    edicao_proprietario_vinculado_por_produtor = (perfil == 'PRODUTOR' and bool(id))

    if edicao_proprietario_vinculado_por_produtor:
        with Session(engine) as db:
            proprietario_atual = db.get(Proprietario, int(id))
            tipo_pessoa = proprietario_atual.tipo_pessoa
            cpf_cnpj = proprietario_atual.cpf_cnpj

    # Regra: quando FISICA, nome sempre espelha razao_social
    if tipo_pessoa == 'FISICA':
        nome = razao_social

    erro_validacao = None

    if not erro_validacao and tipo_pessoa not in TIPOS_PESSOA:
        erro_validacao = 'Tipo de Pessoa incorreto! Selecione Física ou Jurídica.'

    if not erro_validacao and visibilidade not in VISIBILIDADES:
        erro_validacao = 'Visibilidade incorreta! Selecione Público ou Privado.'

    if not erro_validacao and uf not in UFS_BRASIL:
        erro_validacao = 'UF incorreta! Selecione um estado da lista.'

    if not erro_validacao and tipo_pessoa == 'FISICA' and len(cpf_cnpj) != 11:
        erro_validacao = 'CPF incorreto! Deve conter 11 dígitos.'

    if not erro_validacao and tipo_pessoa == 'JURIDICA' and len(cpf_cnpj) != 14:
        erro_validacao = 'CNPJ incorreto! Deve conter 14 dígitos.'

    # v2.7.0: confere o digito verificador (algoritmo real da
    # Receita Federal, ja pronto em backend/utils/validadores.py,
    # o mesmo usado por produtores.py desde a v1.8.0 e pelo
    # /convite desde a Sessao 032). Pulada quando o CPF/CNPJ nao
    # veio do formulario, e sim do banco (ver
    # edicao_proprietario_vinculado_por_produtor acima) - nesse
    # caminho o usuario nao tem como corrigir o documento naquela
    # tela (campo travado/readonly), entao validar aqui so
    # travaria para sempre a edicao de contato/endereco de um
    # cadastro que ja tenha nascido com CPF/CNPJ errado.
    if not erro_validacao and not edicao_proprietario_vinculado_por_produtor:
        if tipo_pessoa == 'FISICA' and not validar_cpf(cpf_cnpj):
            erro_validacao = 'CPF incorreto! O dígito verificador não confere — confira o número.'
        elif tipo_pessoa == 'JURIDICA' and not validar_cnpj(cpf_cnpj):
            erro_validacao = 'CNPJ incorreto! O dígito verificador não confere — confira o número.'

    LIMITES_TAMANHO = {
        'Nome':          (nome, 150),
        'Razão Social':  (razao_social, 150),
        'CPF/CNPJ':      (cpf_cnpj, 14),
        'Email':         (email, 150),
        'Logradouro':    (logradouro, 200),
        'Número':        (numero, 10),
        'Complemento':   (complemento, 100),
        'Bairro':        (bairro, 100),
        'Município':     (municipio, 100),
        'UF':            (uf, 2),
    }

    if not erro_validacao:
        for nome_campo, (valor, limite) in LIMITES_TAMANHO.items():
            if valor and len(valor) > limite:
                erro_validacao = f'Campo "{nome_campo}" excede o limite de {limite} caracteres (digitado: {len(valor)}).'
                break

    if erro_validacao:
        proprietario_tentativa = SimpleNamespace(
            id           = id,
            tipo_pessoa  = tipo_pessoa,
            razao_social = razao_social,
            nome         = nome,
            visibilidade = visibilidade,
            cpf_cnpj     = cpf_cnpj,
            email        = email,
            telefone     = telefone,
            telefone2    = telefone2,
            logradouro   = logradouro,
            numero       = numero,
            complemento  = complemento,
            bairro       = bairro,
            cep          = cep,
            municipio    = municipio,
            uf           = uf
        )

        with Session(engine) as db:
            propriedade = db.get(Propriedade, int(id_propriedade)) if id_propriedade else None
            vinculo = _vinculo_proprietario_propriedade(db, int(id), int(id_propriedade)) if (id and id_propriedade) else None

        return render_template('consiste/proprietario_cadastro.html',
            proprietario     = proprietario_tentativa,
            id_propriedade   = id_propriedade,
            nome_propriedade = propriedade.nome if propriedade else None,
            travar_documento = (perfil == 'PRODUTOR'),
            id_vinculo       = vinculo.id if vinculo else None,
            vinculo_ativo    = (vinculo.data_fim is None) if vinculo else None,
            tipos_pessoa     = TIPOS_PESSOA,
            visibilidades    = VISIBILIDADES,
            ufs              = UFS_BRASIL,
            erro             = erro_validacao,
            usuario_nome     = session.get('usuario_nome'),
            usuario_perfil   = session.get('usuario_perfil'),
            cor_primaria     = session.get('cor_primaria', '#D4370A'),
            nome_sistema     = session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo       = 'proprietarios'
        )

    with Session(engine) as db:
        if id:
            # Edicao - CONSISTE (avulsa, sem contexto de
            # Propriedade) OU PRODUTOR (Proprietario ja vinculado
            # a sua Propriedade - v2.6.0). Tipo de Pessoa e
            # CPF/CNPJ ja foram travados acima quando PRODUTOR.
            p = db.get(Proprietario, int(id))
            p.tipo_pessoa  = tipo_pessoa
            p.razao_social = razao_social
            p.nome         = nome
            p.visibilidade = visibilidade
            p.cpf_cnpj     = cpf_cnpj
            p.email        = email
            p.telefone     = telefone
            p.telefone2    = telefone2
            p.logradouro   = logradouro
            p.numero       = numero
            p.complemento  = complemento
            p.bairro       = bairro
            p.cep          = cep
            p.municipio    = municipio
            p.uf           = uf
            db.commit()

            # v2.6.0: PRODUTOR nao tem acesso a lista de
            # Proprietarios - volta para a Propriedade de origem.
            if perfil == 'PRODUTOR':
                return redirect(url_for('propriedades.editar', id=int(id_propriedade)))
            return redirect(url_for('proprietarios.lista'))

        else:
            # Novo - sempre vinculado a uma Propriedade (id_propriedade
            # obrigatorio neste ponto, pois nao existe mais avulso)
            p = Proprietario(
                tipo_pessoa  = tipo_pessoa,
                razao_social = razao_social,
                nome         = nome,
                visibilidade = visibilidade,
                cpf_cnpj     = cpf_cnpj,
                email        = email,
                telefone     = telefone,
                telefone2    = telefone2,
                logradouro   = logradouro,
                numero       = numero,
                complemento  = complemento,
                bairro       = bairro,
                cep          = cep,
                municipio    = municipio,
                uf           = uf,
                ativo        = True
            )
            db.add(p)
            db.flush()  # garante que p.id ja existe, sem precisar commitar ainda

            novo_vinculo = PropriedadeProprietario(
                id_propriedade  = int(id_propriedade),
                id_proprietario = p.id,
                data_inicio     = date.today()
            )
            db.add(novo_vinculo)
            db.commit()

            propriedade = db.get(Propriedade, int(id_propriedade))

            return render_template('consiste/proprietario_vinculado.html',
                proprietario     = p,
                propriedade      = propriedade,
                usuario_nome     = session.get('usuario_nome'),
                usuario_perfil   = session.get('usuario_perfil'),
                cor_primaria     = session.get('cor_primaria', '#D4370A'),
                nome_sistema     = session.get('nome_sistema', 'Orion SISBOV'),
                menu_ativo       = 'proprietarios'
            )


# -------------------------------------------------------
# Rota: /proprietarios/toggle/<id> — ativa ou inativa
# (status geral da pessoa - NAO mexe em vinculos com
# Propriedades, que sao encerrados separadamente)
# -------------------------------------------------------
@proprietarios.route('/proprietarios/toggle/<int:id>', methods=['POST'])
def toggle(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirecionar_home(session.get('usuario_perfil'))

    with Session(engine) as db:
        p = db.get(Proprietario, id)
        p.ativo = not p.ativo
        db.commit()

    return redirect(url_for('proprietarios.lista'))


# -------------------------------------------------------
# Rota: /proprietarios/toggle-vinculo/<id_vinculo> — alterna
# o vinculo com uma Propriedade entre Ativo e Inativo.
# Ativo -> Inativo: data_fim = hoje.
# Inativo -> Ativo: data_fim = None (reativa o vinculo).
#
# Sessao 033: nenhuma mudanca de logica aqui - so mudou QUEM
# chama esta rota. Ate a v1.16.0 (propriedade_cadastro.html),
# era chamada direto da lista de Proprietario(s). A partir da
# v1.17.0/v2.6.0, e chamada de dentro da tela de edicao do
# Proprietario (bloco "Vinculo com esta Propriedade").
#
# Requer perfil CONSISTE, OU perfil PRODUTOR desde que o
# vinculo pertenca a sua propria Propriedade (P-040, Sessao 032).
# -------------------------------------------------------
@proprietarios.route('/proprietarios/toggle-vinculo/<int:id_vinculo>', methods=['POST'])
def toggle_vinculo(id_vinculo):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    perfil = session.get('usuario_perfil')

    with Session(engine) as db:
        vinculo = db.get(PropriedadeProprietario, id_vinculo)
        if not vinculo:
            return redirecionar_home(perfil) if perfil == 'PRODUTOR' else redirect(url_for('propriedades.lista'))

        id_propriedade = vinculo.id_propriedade

        if perfil == 'CONSISTE':
            pass  # acesso total, como sempre
        elif perfil == 'PRODUTOR' and _produtor_possui_propriedade(db, id_propriedade):
            pass  # acesso liberado so a esta Propriedade (P-040)
        else:
            return redirecionar_home(perfil)

        if vinculo.data_fim is None:
            vinculo.data_fim = date.today()
        else:
            vinculo.data_fim = None

        db.commit()

    return redirect(url_for('propriedades.editar', id=id_propriedade))


# -------------------------------------------------------
# Rota: /proprietarios/relatorio/<id> — gera PDF com dados
# do Proprietario + lista de Propriedades ATIVAS vinculadas
# (vinculo sem data_fim). Usa xhtml2pdf (HTML/CSS -> PDF),
# com link_callback_pdf (importado de backend/utils/pdf_helper.py)
# para conseguir carregar a logo da Consiste no cabecalho do
# relatorio. Continua exclusiva CONSISTE.
# -------------------------------------------------------
@proprietarios.route('/proprietarios/relatorio/<int:id>')
def relatorio_pdf(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    with Session(engine) as db:
        proprietario = db.get(Proprietario, id)
        if not proprietario:
            return redirect(url_for('proprietarios.lista'))

        vinculos_ativos = db.query(PropriedadeProprietario).filter(
            PropriedadeProprietario.id_proprietario == id,
            PropriedadeProprietario.data_fim.is_(None)
        ).all()

        propriedades_ativas = []
        for vinculo in vinculos_ativos:
            propriedade = db.get(Propriedade, vinculo.id_propriedade)
            if propriedade:
                propriedades_ativas.append({
                    'propriedade': propriedade,
                    'data_inicio': vinculo.data_inicio
                })

        html_renderizado = render_template('consiste/proprietario_relatorio_pdf.html',
            proprietario         = proprietario,
            propriedades_ativas  = propriedades_ativas,
            data_emissao         = date.today().strftime('%d/%m/%Y')
        )

    buffer_pdf = BytesIO()
    pisa.CreatePDF(html_renderizado, dest=buffer_pdf, link_callback=link_callback_pdf)
    buffer_pdf.seek(0)

    nome_arquivo = f'proprietario_{id}_relatorio.pdf'
    return send_file(
        buffer_pdf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=nome_arquivo
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\proprietarios.py
# =========================================================