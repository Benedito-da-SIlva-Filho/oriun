# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\produtores.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-06 20:33 -03
# ATUALIZADO EM: 2026-11-12 19:00 -03
# VERSAO: 1.14.0
# v1.14.0: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras no CNPJ aceitas e conferidas; CNPJ antigo continua valendo. REVERSAO: .bak_antes_s122_etapa2.
# v1.13.0: Sessao 122 (2026-11-12 17:40 -03) - Auditoria Etapa 2 (item 4): toggle_vinculo so para a Consiste (Produtor nao encerra mais o proprio vinculo nem o dos outros). Cargos com acesso vem do vinculo ATIVO. REVERSAO: .bak_antes_s122_etapa2.
# v1.12.1: Sessao 118 (2026-11-08 15:30 -03) - Novo Produtor aceita &documento= (CPF/CNPJ ja preenchido). REVERSAO: .bak_antes_s118_dtacpf
# v1.12.0: Sessao 116 (2026-11-06 16:01 -03) - Cadastrar/vincular Produtor novo (novo e salvar sem id) so para Titular/Administrador (perfil PRODUTOR); outros cargos voltam a Minha Propriedade. REVERSAO: .bak_antes_s116_addprodutor.
#
# DESCRICAO:
#     Rotas do modulo de Produtor (plataforma Consiste).
#     Cadastro exclusivo da Consiste, perfil CONSISTE - acesso
#     da Certificadora fica para quando o Modulo Certificadora
#     (fluxo MAPA/P-013) for construido - EXCETO para o perfil
#     PRODUTOR cadastrar/vincular/EDITAR OUTRO Produtor da sua
#     PROPRIA Propriedade (P-040, ver v1.5.0 e v1.7.0 abaixo), e
#     EXCETO para o proprio Titular completar os placeholders do
#     seu Produtor ja vinculado (P-040, ver v1.6.0).
#     - /produtores                          -> lista todos, com busca
#     - /produtores/novo                     -> formulario novo,
#                                               EXIGE ?id_propriedade=<id>
#     - /produtores/salvar                   -> salva novo/edicao/vinculo/
#                                               completar placeholder
#     - /produtores/editar/<id>              -> formulario edicao,
#                                               ACEITA ?id_propriedade=<id>
#                                               (v1.7.0)
#     - /produtores/toggle/<id>              -> ativa ou inativa
#     - /produtores/toggle-vinculo/<id_vinculo> -> alterna vinculo com
#                                               Propriedade entre Ativo e
#                                               Inativo (reversivel)
#     - /produtores/onboarding/<id>          -> POST - cria o ambiente
#                                               multi-tenant do Produtor
#                                               (schema fisico + tabelas
#                                               de movimento)
#     - /produtores/criar-acesso/<id>        -> POST - cria o Usuario +
#                                               UsuarioVinculo (login/
#                                               senha) de um Produtor
#                                               ja cadastrado que ainda
#                                               nao tem acesso (v1.9.0)
#     - /produtores/relatorio/<id>           -> gera PDF com dados do
#                                               Produtor + Propriedades
#                                               ativas vinculadas
#
#     Regras de negocio: NAO EXISTE cadastro avulso de Produtor -
#     todo Novo Produtor nasce vinculado a uma Propriedade
#     (id_propriedade na URL). Busca automatica por CPF/CNPJ nas
#     duas tabelas (produtores e proprietarios) via JS, com os
#     comportamentos ja documentados desde a v1.0.0 (achou em
#     Produtores, MAS de OUTRA Propriedade = trava e vincula; achou
#     em Produtores, MAS da MESMA Propriedade (Titular completando
#     placeholder, v1.6.0) = abre para edicao, sem duplicar vinculo;
#     achou so em Proprietarios = pre-preenche editavel; nao achou =
#     campos livres). Upload real da logo Marca/Criador (P-020) via
#     _salvar_logo_produtor(). Onboarding (Sessao 019) cria o schema
#     fisico multi-tenant via criar_ambiente_produtor() (backend/
#     utils/onboarding.py) - continua exclusiva CONSISTE.
#
#     v1.0.0 a v1.4.0: historico completo no arquivo original do
#             projeto (criacao do modulo espelhando proprietarios.py,
#             upload de logo P-020, extracao de link_callback_pdf
#             para pdf_helper.py/P-023, rota de onboarding
#             multi-tenant Sessao 019).
#     v1.5.0: Sessao 032 - P-040, complemento: espelhando a mesma
#             abertura ja feita em proprietarios.py v2.4.0, perfil
#             PRODUTOR passa a poder acessar novo()/salvar()/
#             toggle_vinculo(), MAS apenas para a Propriedade
#             vinculada a ele mesmo - reaproveitada
#             _produtor_possui_propriedade() (import direto de
#             propriedades.py, sem duplicar). Motivado por caso de
#             negocio real trazido por Benedito: irmaos, socios ou
#             amigos que arrendam/operam juntos a mesma terra - mais
#             de um Produtor pode estar ativo na mesma Propriedade
#             (ja documentado desde propriedade_cadastro.html
#             v1.11.0). Edicao avulsa (id presente, via
#             /produtores/editar/<id>) e a rota de onboarding()
#             continuavam exclusivas CONSISTE (mudou na v1.7.0 para
#             editar(), ver abaixo).
#     v1.6.0: Sessao 033 - P-040, wizard de onboarding: novo campo
#             de formulario id_produtor_completar (preenchido pelo
#             JS de produtor_cadastro.html v2.1.0 quando o CPF/CNPJ
#             digitado bate com um Produtor JA vinculado a ESTA
#             MESMA Propriedade - caso do Titular completando os
#             proprios placeholders de municipio/UF, criados pela
#             transacao do Convite Publico). Novo ramo em salvar():
#             passa pela MESMA validacao completa do fluxo de edicao
#             (tamanho de campos, tipo_pessoa, CPF/CNPJ), mas
#             atualiza o Produtor existente em vez de criar vinculo
#             novo (evitaria vinculo duplicado com a mesma
#             Propriedade). Seguranca: confere de novo no servidor,
#             antes de gravar, que o vinculo ativo realmente existe
#             entre id_produtor_completar e id_propriedade - nao
#             confia soh na checagem que o JS ja fez. Ao salvar com
#             sucesso, redireciona direto para propriedades.editar()
#             (decisao de Benedito) - la a proxima secao do wizard
#             (Dados da Propriedade) ja aparece liberada
#             (propriedades.py v1.12.0).
#     v1.7.0: Sessao 033 - Benedito identificou que a lista de
#             Produtor(es) em propriedade_cadastro.html so tinha
#             Ativar/Inativar, sem nenhuma forma de EDITAR os dados
#             ja vinculados. Decisao: trocar aquele botao por um
#             link "Editar" (propriedade_cadastro.html v1.17.0), o
#             que exige liberar editar() tambem para o perfil
#             PRODUTOR - antes exclusiva CONSISTE. Novo helper
#             _vinculo_produtor_propriedade() confere se ha vinculo
#             (ativo ou inativo) entre o Produtor e a Propriedade -
#             usado como checagem de seguranca (o PRODUTOR so edita
#             quem ja esta vinculado a sua propria Propriedade) e
#             para buscar o id_vinculo/status a mostrar na tela.
#             Decisao de Benedito: PRODUTOR edita SO dados de
#             contato/endereco - Tipo de Pessoa e CPF/CNPJ ficam
#             travados (o servidor ignora esses dois campos vindos
#             do formulario quando perfil == PRODUTOR e id presente,
#             usando sempre o valor ja gravado no banco). O controle
#             de status (Ativo/Inativo) que antes ficava na lista
#             migrou para dentro desta tela (novo bloco "Vinculo com
#             esta Propriedade", que continua chamando a MESMA rota
#             toggle_vinculo() de sempre - nenhuma mudanca nela).
#             Redirecionamento pos-salvar (edicao com id, perfil
#             PRODUTOR) passa a ser propriedades.editar (nao tem
#             acesso a produtores.lista).
#     v1.8.0: Sessao 034 (continuacao 8, 12/08/2026, 15:40 -03) -
#             Benedito encontrou dois cadastros de Produtor para a
#             mesma pessoa real (CLAUDENOR ZOPONE JUNIOR), cada um
#             com um CPF diferente e incorreto (11 digitos cada,
#             mas nenhum batendo com o CPF real) - salvar() so
#             conferia TAMANHO do CPF/CNPJ, nunca o digito
#             verificador. Corrigido: nova validacao logo apos as
#             checagens de tamanho existentes, reaproveitando
#             validar_cpf()/validar_cnpj() de backend/utils/
#             validadores.py (ja usadas em convite.py desde a
#             Sessao 032 - nenhum algoritmo novo, so passou a ser
#             chamado tambem aqui). Mensagem de erro distinta da
#             checagem de tamanho ("Digito verificador nao confere"),
#             para o usuario entender que o problema NAO e faltar/
#             sobrar digito, e sim o numero em si estar incorreto.
#             IMPORTANTE: a validacao e pulada quando perfil ==
#             'PRODUTOR' e id esta presente (edicao de um Produtor
#             ja vinculado, via link "Editar") - nesse caminho o
#             CPF/CNPJ que chega ao validador NUNCA e o do
#             formulario (o bloco logo acima, ja existente desde a
#             Sessao 033, sobrescreve com o valor gravado no banco,
#             ignorando o campo do form) - validar um dado que o
#             usuario nem consegue corrigir naquela tela travaria
#             para sempre a edicao de contato/endereco de um
#             cadastro que ja nasceu com CPF errado (caso real do
#             Claudenor). Nos demais casos (CONSISTE criando ou
#             editando, PRODUTOR criando um socio novo via
#             novo(), Titular completando o proprio placeholder via
#             id_produtor_completar) o CPF/CNPJ vem do formulario e
#             a validacao se aplica normalmente.
#     v1.9.0: Sessao 034 (continuacao 9, 13/08/2026, 11:17 -03) -
#             P-040/novo (Cenario 1 - Produtor sem login): Benedito
#             identificou que Produtores cadastrados pela CONSISTE
#             (fluxo antigo, salvar() sem id_propriedade vindo do
#             Convite) NUNCA tinham Usuario/UsuarioVinculo criados
#             junto - caso real: Claudenor e Angelica, com cadastro
#             completo mas sem nenhum acesso ao sistema. Diferente
#             do fluxo /convite (self-service), onde a criacao de
#             conta ja e automatica (ver convite.py, Etapa 2 -
#             hoje pausada, mas o mecanismo existe e foi reaproveitado
#             aqui). Nova rota criar_acesso(id), exclusiva CONSISTE:
#               - Confere que o Produtor existe e que NAO ha nenhum
#                 UsuarioVinculo ATIVO para ele (protecao contra
#                 duplo clique/recriacao - um Produtor, um schema,
#                 um unico login, mesmo que tenha N Propriedades
#                 vinculadas, ex.: as 8 fazendas do Claudenor).
#               - Gera senha provisoria (mesmo gerador ja usado em
#                 auth.py/esqueci_senha() e convite.py).
#               - Cria Usuario (login=CPF/CNPJ sem mascara,
#                 senha_provisoria=False para forcar troca no
#                 primeiro login, login_provisorio=True - nova
#                 coluna v1.4.0 do model, ver Tabelas/
#                 alterar_usuarios_login_provisorio.sql) e
#                 UsuarioVinculo (cargo='TITULAR').
#               - Envia e-mail obrigatorio com login+senha (mesmo
#                 mecanismo Flask-Mail ja usado em esqueci_senha()/
#                 convite.py).
#               - Monta (nao envia sozinho - decisao de Benedito,
#                 "envio final sempre manual", mesmo padrao do
#                 WhatsApp em prospects.py) um link wa.me opcional,
#                 SEM o CPF na mensagem (Benedito: "ela deve saber
#                 o numero ou consultar o documento").
#             editar() ganhou a variavel tem_acesso (True/False,
#             calculada so quando perfil==CONSISTE, consultando
#             UsuarioVinculo por id_produtor com data_fim IS NULL),
#             passada ao template para decidir se mostra o bloco
#             "Criar Acesso". As demais rotas que renderizam
#             produtor_cadastro.html (novo(), salvar() em erro,
#             onboarding() em erro) NAO foram alteradas para passar
#             tem_acesso/acesso_criado_agora/link_whatsapp - o
#             template trata a ausencia dessas variaveis como falsy
#             (padrao do Jinja2 para variavel indefinida), entao o
#             bloco novo so aparece exatamente onde deveria (edicao
#             de um Produtor existente, vindo de editar() ou de
#             criar_acesso() em si).
#             Pendencia registrada para proxima sessao (fora do
#             escopo desta): tela de "escolher login e senha" no
#             primeiro acesso, usando a flag login_provisorio - exige
#             ver usuarios.py e a tela de troca de senha antes de
#             desenhar.
#     v1.9.1: Sessao 034 (continuacao 9, 13/08/2026, 11:50 -03) -
#             Teste real do Cenario 1 (Claudenor) confirmou o fluxo
#             ponta a ponta - e-mail chegou com login/senha certos.
#             Ajuste pedido por Benedito: o corpo do e-mail de
#             criar_acesso() ganhou o link direto de /login
#             (url_for('auth.login', _external=True)), para a pessoa
#             so precisar clicar em vez de digitar o endereco.
#             Mesma limitacao ja registrada na Referencia do Sistema
#             para o link do Convite Publico: hoje aponta para
#             localhost, so funciona testando na mesma rede/maquina -
#             nao e bug, e limitacao conhecida ate haver dominio
#             publico em producao.
#     v1.9.2: Sessao 034 (continuacao 9, 13/08/2026, 13:20 -03) -
#             Funcao local _gerar_senha_provisoria() removida e
#             substituida por import de gerar_senha_provisoria()
#             (backend/utils/senha_helper.py, novo) - mesma logica
#             ja duplicada em auth.py e convite.py, extraida para
#             um lugar so (decisao de Benedito, motivada pelo novo
#             4o ponto de uso em vitrine_visitantes.py). Nenhuma
#             mudanca de comportamento. Imports random/string
#             removidos deste arquivo (nao usados em mais nenhum
#             outro ponto).
#     v1.9.3: Sessao 034 (continuacao 9, 13/08/2026, 14:25 -03) -
#             Correcao de um gap real detectado em teste: o plano
#             original (alinhado ANTES do Cenario 1 ser codado)
#             previa que o "Salvar" de um Produtor totalmente novo
#             ja criaria o acesso (Usuario+UsuarioVinculo+e-mail)
#             automaticamente - essa parte do plano foi perdida no
#             resumo final de alinhamento (so o botao "Criar
#             Acesso" da tela de edicao foi implementado), sem
#             Benedito ter confirmado a remocao - falha de
#             especificacao, corrigida agora. O ramo "else" de
#             salvar() (criacao de Produtor 100% novo - sem
#             id_existente, sem id_produtor_completar) agora cria
#             o acesso na MESMA transacao do cadastro, reaproveitando
#             a mesma receita ja usada em criar_acesso() (Cenario 1)
#             e vitrine_visitantes.py/converter() (Cenario 2). Vale
#             tanto para CONSISTE quanto para PRODUTOR criando um
#             novo socio (P-040) - decisao explicita de Benedito
#             (Sessao 034 cont. 9): "nos dois casos". Se o Produtor
#             nao tiver e-mail (nao deveria acontecer, campo e
#             obrigatorio no formulario, mas por seguranca), o
#             acesso simplesmente nao e criado aqui - fica para o
#             botao "Criar Acesso" da tela de edicao resolver depois,
#             quando o e-mail for completado. produtor_vinculado.html
#             (v1.2.0) ganhou os campos acesso_criado_agora,
#             link_whatsapp e erro_acesso para mostrar o resultado.
#     v1.9.4: Sessao 096 (14/10/2026, 11:10 -03) - ACESSO DO PRODUTOR: _produtor_tem_acesso() passa a
#             contar so vinculo ATIVO com cargo TITULAR. Antes qualquer vinculo (ex.: um
#             ADMINISTRATIVO com acesso a 2 Produtores da mesma fazenda) escondia o botao
#             "Criar Acesso" e fazia criar_acesso() recusar. Nenhuma outra mudanca.
#             REVERSAO: devolver .bak_antes_titular_s096.
#     v1.9.5: Sessao 096 (14/10/2026) - Produtor que ENTRA numa
#         propriedade existente (vincular produtor ja cadastrado, ou
#         cadastrar socio novo) passa a receber a equipe da propriedade
#         automaticamente (backend/utils/equipe_propriedade.py).
#     v1.9.6: Sessao 097 (15/10/2026, 11:20 -03) - AUDITORIA DE PERMISSOES: toggle()/salvar() conferiam so o login; passam a
#             exigir perfil CONSISTE, a mesma regra das telas desta rota. Nenhuma outra mudanca.
#     v1.10.0: Sessao 101 (20/10/2026, 17:18 -03) - CPF E CNPJ DO PRODUTOR: campo novo documento_secundario (opcional; CNPJ do Produtor Fisico ou CPF do Juridico), conferido so quando preenchido; salvar() grava cpf e cnpj nas colunas novas (aplicar_documentos) nos tres caminhos (novo, edicao, completar). REVERSAO: devolver .bak_antes_cpf_cnpj_s101.
#     v1.11.0: Sessao 101 (20/10/2026, 18:10 -03) - CNPJ/CPF SECUNDARIO POR FAZENDA: o documento secundario (CNPJ do Produtor Fisico / CPF do Juridico) passa a ser gravado no VINCULO Produtor+Propriedade (propriedade_produtor.documento_secundario), nao mais no Produtor (v1.10.0 gravava nas colunas cpf/cnpj de produtores; deixam de ser usadas). Sem Propriedade em contexto (CONSISTE avulso) o campo nao aparece. SQL: Tabelas\18_alter_propriedade_produtor_documento_secundario.sql. REVERSAO: devolver .bak_antes_sec_vinculo_s101.
# =========================================================

import os
import re
import urllib.parse
from datetime import date, datetime
from io import BytesIO
from types import SimpleNamespace
from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, current_app
from backend.database import engine
from backend.models import Produtor, Propriedade, PropriedadeProdutor, Proprietario, Usuario, UsuarioVinculo
from backend.utils.pdf_helper import link_callback_pdf
from backend.utils.onboarding import criar_ambiente_produtor, ProdutorJaOnboardado
from backend.utils.validadores import validar_cpf, validar_cnpj, limpar_documento
from backend.utils.documentos_produtor import secundario_do_vinculo
from backend.utils.senha_helper import gerar_senha_provisoria
from backend.utils.equipe_propriedade import ligar_equipe_ao_produtor
from backend.utils.permissao_produtor import pode_cadastrar_produtor
from backend.routers.auth import redirecionar_home
from backend.routers.propriedades import _produtor_possui_propriedade
from backend.extensions import mail
from flask_mail import Message
from werkzeug.security import generate_password_hash
from sqlalchemy.orm import Session
from xhtml2pdf import pisa

produtores = Blueprint('produtores', __name__)

TIPOS_PESSOA = ['FISICA', 'JURIDICA']
VISIBILIDADES = ['PUBLICO', 'PRIVADO']
EXTENSOES_LOGO_PERMITIDAS = {'.png', '.jpg', '.jpeg'}

UFS_BRASIL = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
    'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
    'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]

# -------------------------------------------------------
# WhatsApp da Consiste - mesmo numero usado como CTA na Tela
# Vitrine (convite.py) e em prospects.py. Aqui o uso e o
# INVERSO: nao e o prospect chamando a Consiste, e a Consiste
# enviando a MENSAGEM DE ACESSO para o TELEFONE DO PRODUTOR
# (ver criar_acesso() abaixo - link wa.me/<telefone_do_produtor>).
# -------------------------------------------------------
DDI_BRASIL = '55'


def _salvar_logo_produtor(id_produtor, arquivo):
    if not arquivo or not arquivo.filename:
        return None

    extensao = os.path.splitext(arquivo.filename)[1].lower()
    if extensao not in EXTENSOES_LOGO_PERMITIDAS:
        return 'ERRO_EXTENSAO'

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    nome_arquivo = f'produtor_{id_produtor}_{timestamp}{extensao}'

    pasta_destino = os.path.join(current_app.static_folder, 'uploads', 'produtores')
    os.makedirs(pasta_destino, exist_ok=True)

    caminho_completo = os.path.join(pasta_destino, nome_arquivo)
    arquivo.save(caminho_completo)

    return f'uploads/produtores/{nome_arquivo}'


# -------------------------------------------------------
# Funcao auxiliar (Sessao 033): confere se ha vinculo ATIVO
# (data_fim is None) entre o Produtor e a Propriedade
# informados. Usada como checagem de seguranca no servidor
# em salvar() - ver ramo id_produtor_completar.
# -------------------------------------------------------
def _vinculo_ativo_existe(db, id_produtor, id_propriedade):
    vinculo = db.query(PropriedadeProdutor).filter(
        PropriedadeProdutor.id_produtor == id_produtor,
        PropriedadeProdutor.id_propriedade == id_propriedade,
        PropriedadeProdutor.data_fim.is_(None)
    ).first()
    return vinculo is not None


# -------------------------------------------------------
# Funcao auxiliar (Sessao 033): confere se ha vinculo (ativo
# OU inativo) entre o Produtor e a Propriedade informados, e
# devolve o objeto PropriedadeProdutor (ou None). Usada como
# checagem de seguranca em editar()/salvar() (PRODUTOR so
# edita quem ja esta vinculado a sua propria Propriedade) e
# para buscar o id_vinculo/status a mostrar na tela (bloco
# "Vinculo com esta Propriedade"). Diferente de
# _vinculo_ativo_existe() acima, que so aceita vinculo ATIVO
# (usada no ramo "completar placeholder").
# -------------------------------------------------------
def _vinculo_produtor_propriedade(db, id_produtor, id_propriedade):
    return db.query(PropriedadeProdutor).filter(
        PropriedadeProdutor.id_produtor == id_produtor,
        PropriedadeProdutor.id_propriedade == id_propriedade
    ).first()


# -------------------------------------------------------
# Funcao auxiliar (v1.9.0): confere se o Produtor JA TEM
# acesso ao sistema - ou seja, se ha algum UsuarioVinculo
# ATIVO (data_fim is None) para ele. Um Produtor tem UM
# unico login/schema, mesmo com N Propriedades vinculadas
# (ex.: as 8 fazendas do Claudenor) - entao esta checagem e
# por id_produtor, nunca por Propriedade. Usada em editar()
# para decidir se mostra o bloco "Criar Acesso", e em
# criar_acesso() como protecao contra duplo clique/recriacao.
# -------------------------------------------------------
def _produtor_tem_acesso(db, id_produtor):
    # v1.9.4 - so conta o login do proprio Produtor (cargo TITULAR). Um
    # ADMINISTRATIVO de outro Produtor (ex.: usuario com vinculo em 2 Produtores
    # da mesma fazenda) NAO e o acesso do Produtor.
    vinculo = db.query(UsuarioVinculo).filter(
        UsuarioVinculo.id_produtor == id_produtor,
        UsuarioVinculo.cargo == 'TITULAR',
        UsuarioVinculo.data_fim.is_(None)
    ).first()
    return vinculo is not None


@produtores.route('/produtores')
def lista():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    termo_busca = request.args.get('busca', '').strip()

    with Session(engine) as db:
        query = db.query(Produtor)
        if termo_busca:
            query = query.filter(
                (Produtor.nome.ilike(f'%{termo_busca}%')) |
                (Produtor.razao_social.ilike(f'%{termo_busca}%'))
            )
        lista_produtores = query.order_by(Produtor.nome).all()

    return render_template('consiste/produtor_lista.html',
        produtores     = lista_produtores,
        termo_busca    = termo_busca,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'produtores'
    )


@produtores.route('/produtores/novo')
def novo():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    perfil = session.get('usuario_perfil')
    id_propriedade = request.args.get('id_propriedade')

    if not id_propriedade:
        return redirecionar_home(perfil) if perfil == 'PRODUTOR' else redirect(url_for('propriedades.lista'))

    with Session(engine) as db:
        if perfil == 'CONSISTE':
            pass
        elif perfil == 'PRODUTOR' and _produtor_possui_propriedade(db, int(id_propriedade)):
            # v1.12.0: so Titular/Administrador cadastram Produtor novo
            if not pode_cadastrar_produtor(id_propriedade):
                return redirect(url_for('propriedades.editar', id=int(id_propriedade)))
        else:
            return redirecionar_home(perfil)

        propriedade = db.get(Propriedade, int(id_propriedade))
        if not propriedade:
            return redirecionar_home(perfil) if perfil == 'PRODUTOR' else redirect(url_for('propriedades.lista'))

    documento_inicial = limpar_documento(request.args.get('documento', ''))[:14]   # s118 - vem da DTA de Posse
    return render_template('consiste/produtor_cadastro.html',
        documento_inicial        = documento_inicial,
        produtor               = None,
        id_propriedade          = id_propriedade,
        nome_propriedade        = propriedade.nome,
        id_produtor_completar    = None,
        travar_documento         = False,
        id_vinculo               = None,
        vinculo_ativo            = None,
        tipos_pessoa            = TIPOS_PESSOA,
        visibilidades           = VISIBILIDADES,
        ufs                      = UFS_BRASIL,
        erro                     = None,
        usuario_nome             = session.get('usuario_nome'),
        usuario_perfil           = session.get('usuario_perfil'),
        cor_primaria             = session.get('cor_primaria', '#D4370A'),
        nome_sistema             = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo               = 'produtores'
    )


# -------------------------------------------------------
# Rota: /produtores/editar/<id> — formulario edicao
#
# Ate a v1.6.0, exclusiva CONSISTE (consulta/alteracao avulsa,
# sem vinculo com Propriedade). A partir da v1.7.0, tambem
# aceita ?id_propriedade=<id> e libera o perfil PRODUTOR -
# MAS apenas para um Produtor ja vinculado (ativo ou inativo)
# a Propriedade dele mesmo (P-040, Sessao 033 -
# _vinculo_produtor_propriedade()). Quando o perfil e
# PRODUTOR, a flag travar_documento vai True para o template
# travar Tipo de Pessoa e CPF/CNPJ. O bloco "Vinculo com esta
# Propriedade" (status + botao Ativar/Inativar) so aparece
# quando id_propriedade foi informado - tanto para CONSISTE
# quanto para PRODUTOR.
#
# v1.9.0: passa tambem tem_acesso (so calculada quando
# perfil==CONSISTE) para o template decidir se mostra o bloco
# "Criar Acesso" - ver _produtor_tem_acesso() acima.
# -------------------------------------------------------
@produtores.route('/produtores/editar/<int:id>')
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
            vinculo = _vinculo_produtor_propriedade(db, id, int(id_propriedade))
            if perfil == 'PRODUTOR' and not vinculo:
                # PRODUTOR so edita Produtor ja vinculado a
                # SUA Propriedade - qualquer outro caso e barrado.
                return redirecionar_home(perfil)

        produtor = db.get(Produtor, id)
        propriedade = db.get(Propriedade, int(id_propriedade)) if id_propriedade else None

        # v1.9.0: so calcula para CONSISTE - PRODUTOR nunca ve
        # nem aciona o bloco "Criar Acesso" (nao e dele decidir
        # sobre o proprio acesso).
        tem_acesso = _produtor_tem_acesso(db, id) if perfil == 'CONSISTE' else False

    return render_template('consiste/produtor_cadastro.html',
        produtor              = produtor,
        doc_secundario         = secundario_do_vinculo(vinculo),
        id_propriedade         = id_propriedade,
        nome_propriedade       = propriedade.nome if propriedade else None,
        id_produtor_completar  = None,
        travar_documento       = (perfil == 'PRODUTOR'),
        id_vinculo             = vinculo.id if vinculo else None,
        vinculo_ativo          = (vinculo.data_fim is None) if vinculo else None,
        tem_acesso              = tem_acesso,
        tipos_pessoa           = TIPOS_PESSOA,
        visibilidades          = VISIBILIDADES,
        ufs                    = UFS_BRASIL,
        erro                   = None,
        usuario_nome           = session.get('usuario_nome'),
        usuario_perfil         = session.get('usuario_perfil'),
        cor_primaria           = session.get('cor_primaria', '#D4370A'),
        nome_sistema           = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo             = 'produtores'
    )


@produtores.route('/produtores/salvar', methods=['POST'])
def salvar():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    perfil                     = session.get('usuario_perfil')
    id                         = request.form.get('id')
    id_propriedade             = request.form.get('id_propriedade')
    id_existente                = request.form.get('id_existente')
    id_proprietario_encontrado = request.form.get('id_proprietario_encontrado')
    id_produtor_completar       = request.form.get('id_produtor_completar')

    if perfil == 'CONSISTE':
        pass
    elif perfil == 'PRODUTOR':
        if not id_propriedade:
            return redirecionar_home(perfil)
        with Session(engine) as db:
            if not _produtor_possui_propriedade(db, int(id_propriedade)):
                return redirecionar_home(perfil)
            # Sessao 033: se vier com id (edicao via link "Editar"),
            # exige que o Produtor ja esteja vinculado a esta
            # Propriedade - qualquer outro caso e barrado.
            if id and not _vinculo_produtor_propriedade(db, int(id), int(id_propriedade)):
                return redirecionar_home(perfil)
            # v1.12.0: cadastrar/vincular Produtor NOVO (sem id) so Titular/Administrador
            if not id and not id_produtor_completar and not pode_cadastrar_produtor(id_propriedade):
                return redirect(url_for('propriedades.editar', id=int(id_propriedade)))
    else:
        return redirecionar_home(perfil)

    if id_propriedade and id_existente:
        with Session(engine) as db:
            novo_vinculo = PropriedadeProdutor(
                id_propriedade = int(id_propriedade),
                id_produtor    = int(id_existente),
                data_inicio    = date.today()
            )
            db.add(novo_vinculo)
            ligar_equipe_ao_produtor(db, int(id_propriedade), int(id_existente))
            db.commit()

            produtor    = db.get(Produtor, int(id_existente))
            propriedade = db.get(Propriedade, int(id_propriedade))

            return render_template('consiste/produtor_vinculado.html',
                produtor       = produtor,
                propriedade    = propriedade,
                usuario_nome   = session.get('usuario_nome'),
                usuario_perfil = session.get('usuario_perfil'),
                cor_primaria   = session.get('cor_primaria', '#D4370A'),
                nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
                menu_ativo     = 'produtores'
            )

    tipo_pessoa   = request.form.get('tipo_pessoa', '').upper()
    razao_social  = request.form.get('razao_social', '').upper()
    nome          = request.form.get('nome', '').upper()
    visibilidade  = request.form.get('visibilidade', '').upper()
    cpf_cnpj      = limpar_documento(request.form.get('cpf_cnpj', ''))
    # v1.10.0: documento SECUNDARIO (opcional) - o CNPJ do Produtor Fisico ou o CPF do Juridico.
    documento_secundario = limpar_documento(request.form.get('documento_secundario', ''))
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

    arquivo_logo  = request.files.get('marca_criador')

    # Sessao 033: PRODUTOR editando um Produtor ja vinculado
    # (via link "Editar", id presente) NAO pode alterar Tipo
    # de Pessoa nem CPF/CNPJ - trava no servidor, ignorando o
    # que veio do formulario (a tela ja vem travada, mas isso
    # garante mesmo que o HTML seja manipulado). Nao se aplica
    # ao ramo id_produtor_completar (Titular completando os
    # proprios placeholders) - la Tipo de Pessoa/CPF/CNPJ ja
    # sao os dele mesmo, nascidos do Convite.
    #
    # v1.8.0: esta e a MESMA trava que faz a validacao de DV
    # (logo abaixo) ser pulada nesse caminho especifico - a
    # partir daqui, cpf_cnpj JA NAO E MAIS o que veio do
    # formulario, e sim o valor gravado no banco.
    edicao_produtor_vinculado_por_produtor = (perfil == 'PRODUTOR' and bool(id))

    if edicao_produtor_vinculado_por_produtor:
        with Session(engine) as db:
            produtor_atual = db.get(Produtor, int(id))
            tipo_pessoa = produtor_atual.tipo_pessoa
            cpf_cnpj = produtor_atual.cpf_cnpj

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

    # v1.8.0: confere o digito verificador (algoritmo real da
    # Receita Federal, ja pronto em backend/utils/validadores.py,
    # o mesmo usado pelo /convite desde a Sessao 032). Pulada
    # quando o CPF/CNPJ nao veio do formulario, e sim do banco
    # (ver edicao_produtor_vinculado_por_produtor acima) - nesse
    # caminho o usuario nao tem como corrigir o documento naquela
    # tela, entao validar aqui so travaria para sempre a edicao
    # de contato/endereco de um cadastro que ja nasceu errado.
    if not erro_validacao and not edicao_produtor_vinculado_por_produtor:
        if tipo_pessoa == 'FISICA' and not validar_cpf(cpf_cnpj):
            erro_validacao = 'CPF incorreto! O dígito verificador não confere — confira o número.'
        elif tipo_pessoa == 'JURIDICA' and not validar_cnpj(cpf_cnpj):
            erro_validacao = 'CNPJ incorreto! O dígito verificador não confere — confira o número.'

    # v1.10.0: confere o documento secundario SO quando preenchido (os dois sao opcionais na tela).
    if not erro_validacao and documento_secundario:
        if tipo_pessoa == 'FISICA':
            if len(documento_secundario) != 14:
                erro_validacao = 'CNPJ incorreto! Deve conter 14 caracteres (ou deixe em branco).'
            elif not validar_cnpj(documento_secundario):
                erro_validacao = 'CNPJ incorreto! O dígito verificador não confere — confira o número.'
        else:
            if len(documento_secundario) != 11:
                erro_validacao = 'CPF incorreto! Deve conter 11 dígitos (ou deixe em branco).'
            elif not validar_cpf(documento_secundario):
                erro_validacao = 'CPF incorreto! O dígito verificador não confere — confira o número.'

    if not erro_validacao and arquivo_logo and arquivo_logo.filename:
        extensao_logo = os.path.splitext(arquivo_logo.filename)[1].lower()
        if extensao_logo not in EXTENSOES_LOGO_PERMITIDAS:
            erro_validacao = 'Marca/Criador: formato de arquivo incorreto! Envie apenas imagens PNG ou JPG.'

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

    # P-040, Sessao 033: checagem de seguranca no servidor para
    # o ramo "completar placeholder" - confere de novo (nao
    # confia so no JS) que o vinculo ativo realmente existe
    # entre este Produtor e esta Propriedade, antes de aceitar
    # a edicao.
    if not erro_validacao and id_produtor_completar and id_propriedade:
        with Session(engine) as db:
            if not _vinculo_ativo_existe(db, int(id_produtor_completar), int(id_propriedade)):
                erro_validacao = 'Não foi possível confirmar o vínculo deste Produtor com esta Propriedade.'

    if erro_validacao:
        marca_criador_atual = None
        id_para_buscar_logo = id or id_produtor_completar
        if id_para_buscar_logo:
            with Session(engine) as db:
                produtor_existente = db.get(Produtor, int(id_para_buscar_logo))
                if produtor_existente:
                    marca_criador_atual = produtor_existente.marca_criador

        vinculo = None
        tem_acesso = False
        with Session(engine) as db:
            propriedade = db.get(Propriedade, int(id_propriedade)) if id_propriedade else None
            if id and id_propriedade:
                vinculo = _vinculo_produtor_propriedade(db, int(id), int(id_propriedade))
            # v1.9.0: recalcula tem_acesso mesmo na volta com erro de
            # validacao, para o banner "Criar Acesso" nao aparecer
            # incorretamente num Produtor que ja tem login.
            if id and perfil == 'CONSISTE':
                tem_acesso = _produtor_tem_acesso(db, int(id))

        produtor_tentativa = SimpleNamespace(
            id            = id,
            tipo_pessoa   = tipo_pessoa,
            razao_social  = razao_social,
            nome          = nome,
            visibilidade  = visibilidade,
            cpf_cnpj      = cpf_cnpj,
            email         = email,
            telefone      = telefone,
            telefone2     = telefone2,
            logradouro    = logradouro,
            numero        = numero,
            complemento   = complemento,
            bairro        = bairro,
            cep           = cep,
            municipio     = municipio,
            uf            = uf,
            marca_criador = marca_criador_atual
        )

        return render_template('consiste/produtor_cadastro.html',
            produtor              = produtor_tentativa,
            doc_secundario         = documento_secundario,
            id_propriedade         = id_propriedade,
            nome_propriedade       = propriedade.nome if propriedade else None,
            id_produtor_completar  = id_produtor_completar,
            travar_documento       = (perfil == 'PRODUTOR'),
            id_vinculo             = vinculo.id if vinculo else None,
            vinculo_ativo          = (vinculo.data_fim is None) if vinculo else None,
            tem_acesso              = tem_acesso,
            tipos_pessoa           = TIPOS_PESSOA,
            visibilidades          = VISIBILIDADES,
            ufs                    = UFS_BRASIL,
            erro                   = erro_validacao,
            usuario_nome           = session.get('usuario_nome'),
            usuario_perfil         = session.get('usuario_perfil'),
            cor_primaria           = session.get('cor_primaria', '#D4370A'),
            nome_sistema           = session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo             = 'produtores'
        )

    with Session(engine) as db:
        if id:
            # Edicao - CONSISTE (avulsa, sem contexto de
            # Propriedade) OU PRODUTOR (Produtor ja vinculado a
            # sua Propriedade - v1.7.0). Tipo de Pessoa e CPF/CNPJ
            # ja foram travados acima quando PRODUTOR.
            p = db.get(Produtor, int(id))
            p.tipo_pessoa   = tipo_pessoa
            p.razao_social  = razao_social
            p.nome          = nome
            p.visibilidade  = visibilidade
            p.cpf_cnpj      = cpf_cnpj
            p.email         = email
            p.telefone      = telefone
            p.telefone2     = telefone2
            p.logradouro    = logradouro
            p.numero        = numero
            p.complemento   = complemento
            p.bairro        = bairro
            p.cep           = cep
            p.municipio     = municipio
            p.uf            = uf
            if id_propriedade:   # Sessao 101: documento secundario e POR FAZENDA (vinculo)
                vinculo_doc = _vinculo_produtor_propriedade(db, int(id), int(id_propriedade))
                if vinculo_doc:
                    vinculo_doc.documento_secundario = documento_secundario or None

            novo_caminho_logo = _salvar_logo_produtor(p.id, arquivo_logo)
            if novo_caminho_logo and novo_caminho_logo != 'ERRO_EXTENSAO':
                p.marca_criador = novo_caminho_logo

            db.commit()

            # v1.7.0: PRODUTOR nao tem acesso a produtores.lista -
            # volta para a Propriedade de origem.
            if perfil == 'PRODUTOR':
                return redirect(url_for('propriedades.editar', id=int(id_propriedade)))
            return redirect(url_for('produtores.editar', id=id))

        elif id_produtor_completar:
            # P-040, Sessao 033: Titular completando os proprios
            # placeholders (municipio/UF) do Produtor ja vinculado
            # a ESTA Propriedade - atualiza o registro existente,
            # NAO cria vinculo novo (ja existe desde a transacao
            # do Convite). Redireciona direto para propriedades.
            # editar() - decisao de Benedito - onde a proxima
            # secao do wizard (Dados da Propriedade) ja aparece
            # liberada.
            p = db.get(Produtor, int(id_produtor_completar))
            p.tipo_pessoa   = tipo_pessoa
            p.razao_social  = razao_social
            p.nome          = nome
            p.visibilidade  = visibilidade
            p.cpf_cnpj      = cpf_cnpj
            p.email         = email
            p.telefone      = telefone
            p.telefone2     = telefone2
            p.logradouro    = logradouro
            p.numero        = numero
            p.complemento   = complemento
            p.bairro        = bairro
            p.cep           = cep
            p.municipio     = municipio
            p.uf            = uf
            vinculo_doc = _vinculo_produtor_propriedade(db, int(id_produtor_completar), int(id_propriedade))
            if vinculo_doc:   # Sessao 101: documento secundario e POR FAZENDA (vinculo)
                vinculo_doc.documento_secundario = documento_secundario or None

            novo_caminho_logo = _salvar_logo_produtor(p.id, arquivo_logo)
            if novo_caminho_logo and novo_caminho_logo != 'ERRO_EXTENSAO':
                p.marca_criador = novo_caminho_logo

            db.commit()

            return redirect(url_for('propriedades.editar', id=int(id_propriedade)))

        else:
            p = Produtor(
                tipo_pessoa     = tipo_pessoa,
                razao_social    = razao_social,
                nome            = nome,
                visibilidade    = visibilidade,
                cpf_cnpj        = cpf_cnpj,
                email           = email,
                telefone        = telefone,
                telefone2       = telefone2,
                logradouro      = logradouro,
                numero          = numero,
                complemento     = complemento,
                bairro          = bairro,
                cep             = cep,
                municipio       = municipio,
                uf              = uf,
                marca_criador   = None,
                id_proprietario = int(id_proprietario_encontrado) if id_proprietario_encontrado else None,
                ativo           = True
            )
            db.add(p)
            db.flush()

            novo_caminho_logo = _salvar_logo_produtor(p.id, arquivo_logo)
            if novo_caminho_logo and novo_caminho_logo != 'ERRO_EXTENSAO':
                p.marca_criador = novo_caminho_logo

            novo_vinculo = PropriedadeProdutor(
                id_propriedade = int(id_propriedade),
                id_produtor    = p.id,
                data_inicio    = date.today(),
                documento_secundario = documento_secundario or None
            )
            db.add(novo_vinculo)
            ligar_equipe_ao_produtor(db, int(id_propriedade), p.id)

            # v1.9.3: 1o cadastro deste Produtor - cria o acesso
            # (Usuario+UsuarioVinculo) na MESMA transacao, mesma
            # receita ja usada em criar_acesso() (Cenario 1) e em
            # vitrine_visitantes.py/converter() (Cenario 2). Vale
            # tanto para CONSISTE quanto para PRODUTOR criando um
            # novo socio (P-040) - decisao de Benedito, Sessao 034
            # cont. 9: "nos dois casos".
            link_whatsapp_acesso = None
            erro_envio_email = None

            if p.email:
                senha_provisoria = gerar_senha_provisoria()

                novo_usuario = Usuario(
                    id_produtor      = p.id,
                    login            = p.cpf_cnpj,
                    senha            = generate_password_hash(senha_provisoria),
                    perfil           = 'PRODUTOR',
                    nome             = p.nome,
                    email            = p.email,
                    senha_provisoria = False,
                    login_provisorio = True
                )
                db.add(novo_usuario)
                db.flush()  # garante novo_usuario.id antes do vinculo

                novo_vinculo_acesso = UsuarioVinculo(
                    id_usuario  = novo_usuario.id,
                    id_produtor = p.id,
                    cargo       = 'TITULAR',
                    data_inicio = date.today()
                )
                db.add(novo_vinculo_acesso)

            db.commit()

            acesso_criado_agora = bool(p.email)

            # --- Envio de e-mail (obrigatorio quando ha acesso) ---
            if acesso_criado_agora:
                try:
                    link_login = url_for('auth.login', _external=True)
                    msg = Message(
                        subject    = 'Orion SISBOV — Seu acesso foi criado',
                        sender     = 'noreply.consisteti@gmail.com',
                        recipients = [p.email]
                    )
                    msg.body = (
                        f'Ola, {p.nome}!\n\n'
                        f'Seu cadastro no Orion SISBOV foi criado com sucesso.\n\n'
                        f'Login: {p.cpf_cnpj}\n'
                        f'Senha provisoria: {senha_provisoria}\n\n'
                        f'Acesse o sistema com este login e senha: {link_login}\n'
                        f'Voce sera redirecionado para criar um login e uma senha novos.\n\n'
                        f'Atenciosamente,\n'
                        f'Orion SISBOV — Consiste Informatica'
                    )
                    mail.send(msg)
                except Exception as e:
                    erro_envio_email = (
                        'Produtor cadastrado, mas houve falha ao enviar o e-mail de acesso. '
                        'Oriente-o a usar "Esqueci minha senha" na tela de login, informando o CPF/CNPJ.'
                    )
                    print(f'ERRO Flask-Mail (Novo Produtor - acesso automatico): {e}')

                # Link de WhatsApp opcional (envio manual, sem o CPF -
                # mesmo padrao ja usado em criar_acesso()).
                if p.telefone:
                    mensagem_whatsapp = (
                        f'Olá, {p.nome}! 🎉 Seu acesso na plataforma Orion SISBOV foi criado.\n'
                        f'Seu login é o seu CPF.\n'
                        f'Sua senha provisória é: {senha_provisoria}\n'
                        f'É só entrar que o sistema já vai pedir pra você criar um login e uma senha novos. '
                        f'Qualquer dúvida, chama a gente!'
                    )
                    link_whatsapp_acesso = (
                        f'https://wa.me/{DDI_BRASIL}{p.telefone}'
                        f'?text={urllib.parse.quote(mensagem_whatsapp)}'
                    )

            propriedade = db.get(Propriedade, int(id_propriedade))

            return render_template('consiste/produtor_vinculado.html',
                produtor             = p,
                propriedade          = propriedade,
                acesso_criado_agora  = acesso_criado_agora,
                link_whatsapp        = link_whatsapp_acesso,
                erro_acesso          = erro_envio_email,
                usuario_nome         = session.get('usuario_nome'),
                usuario_perfil       = session.get('usuario_perfil'),
                cor_primaria         = session.get('cor_primaria', '#D4370A'),
                nome_sistema         = session.get('nome_sistema', 'Orion SISBOV'),
                menu_ativo           = 'produtores'
            )


@produtores.route('/produtores/toggle/<int:id>', methods=['POST'])
def toggle(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirecionar_home(session.get('usuario_perfil'))

    with Session(engine) as db:
        p = db.get(Produtor, id)
        p.ativo = not p.ativo
        p.ativo_alterado_em = datetime.now()
        p.id_usuario_alteracao_status = session.get('usuario_id')
        db.commit()

    return redirect(url_for('produtores.lista'))


# -------------------------------------------------------
# Rota: /produtores/toggle-vinculo/<id_vinculo> — alterna o
# vinculo com uma Propriedade entre Ativo e Inativo.
#
# Sessao 033: nenhuma mudanca de logica aqui - so mudou QUEM
# chama esta rota. Ate a v1.16.0 (propriedade_cadastro.html),
# era chamada direto da lista de Produtor(es). A partir da
# v1.17.0/v1.7.0, e chamada de dentro da tela de edicao do
# Produtor (bloco "Vinculo com esta Propriedade").
# -------------------------------------------------------
@produtores.route('/produtores/toggle-vinculo/<int:id_vinculo>', methods=['POST'])
def toggle_vinculo(id_vinculo):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    perfil = session.get('usuario_perfil')

    with Session(engine) as db:
        vinculo = db.get(PropriedadeProdutor, id_vinculo)
        if perfil != 'CONSISTE':
            return redirecionar_home(perfil)
        if not vinculo:
            return redirect(url_for('propriedades.lista'))

        id_propriedade = vinculo.id_propriedade

        # Etapa 2 (item 4): so a Consiste ativa/inativa o vinculo de um Produtor.
        # Antes, qualquer Produtor com acesso a Propriedade podia encerrar o proprio
        # vinculo (e o dos outros), ficando sem acesso ou deixando a Propriedade sem dono.
        if perfil != 'CONSISTE':
            return redirecionar_home(perfil)

        if vinculo.data_fim is None:
            vinculo.data_fim = date.today()
        else:
            vinculo.data_fim = None

        db.commit()

    return redirect(url_for('propriedades.editar', id=id_propriedade))


@produtores.route('/produtores/onboarding/<int:id>', methods=['POST'])
def onboarding(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    erro_onboarding = None

    try:
        criar_ambiente_produtor(id)
    except ProdutorJaOnboardado:
        erro_onboarding = 'Este Produtor já foi cadastrado — o ambiente já está ativo.'
    except Exception as e:
        erro_onboarding = f'Não foi possível ativar o ambiente deste Produtor: {e}'

    if erro_onboarding:
        with Session(engine) as db:
            produtor = db.get(Produtor, id)
            # v1.9.0: mesma logica de editar() - so calcula para
            # CONSISTE, evita o banner "Criar Acesso" aparecer
            # incorreto num Produtor que ja tem login.
            tem_acesso = _produtor_tem_acesso(db, id)

        return render_template('consiste/produtor_cadastro.html',
            produtor              = produtor,
            id_propriedade         = None,
            nome_propriedade       = None,
            id_produtor_completar  = None,
            travar_documento       = False,
            id_vinculo             = None,
            vinculo_ativo          = None,
            tem_acesso              = tem_acesso,
            tipos_pessoa           = TIPOS_PESSOA,
            visibilidades          = VISIBILIDADES,
            ufs                    = UFS_BRASIL,
            erro                   = erro_onboarding,
            usuario_nome           = session.get('usuario_nome'),
            usuario_perfil         = session.get('usuario_perfil'),
            cor_primaria           = session.get('cor_primaria', '#D4370A'),
            nome_sistema           = session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo             = 'produtores'
        )

    return redirect(url_for('produtores.editar', id=id))


# -------------------------------------------------------
# Rota: /produtores/criar-acesso/<id> — cria o Usuario +
# UsuarioVinculo (login/senha) de um Produtor ja cadastrado
# que ainda nao tem acesso ao sistema (v1.9.0, Cenario 1 -
# ver DESCRICAO no topo do arquivo).
#
# Exclusiva CONSISTE. Protecao contra duplo clique/recriacao:
# se o Produtor ja tiver um UsuarioVinculo ATIVO, a rota nao
# faz nada e so volta para a tela de edicao (nao gera um
# segundo Usuario nem reenvia e-mail).
#
# Login = CPF/CNPJ sem mascara (mesmo padrao do Convite
# Publico). Senha provisoria gerada e enviada por e-mail
# (obrigatorio - mesmo mecanismo Flask-Mail ja usado em
# esqueci_senha()/convite.py). Link de WhatsApp opcional e
# OPCIONAL (envio manual, decisao de Benedito - o CPF NAO
# entra na mensagem, so a senha e o aviso de que o login e o
# CPF - "ela deve saber o numero ou consultar o documento").
#
# Nao redireciona - re-renderiza a MESMA tela de edicao do
# Produtor, com um aviso de sucesso e o link de WhatsApp
# (esses dois dados so existem neste momento da requisicao;
# nao sao gravados em lugar nenhum, entao um redirect os
# perderia).
# -------------------------------------------------------
@produtores.route('/produtores/criar-acesso/<int:id>', methods=['POST'])
def criar_acesso(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    link_whatsapp = None
    erro_criacao = None
    acesso_criado_agora = False

    with Session(engine) as db:
        produtor = db.get(Produtor, id)
        if not produtor:
            return redirect(url_for('produtores.lista'))

        # Protecao contra duplo clique/recriacao - um Produtor,
        # um unico login, mesmo com N Propriedades vinculadas.
        if _produtor_tem_acesso(db, id):
            return redirect(url_for('produtores.editar', id=id))

        if not produtor.email:
            erro_criacao = 'Este Produtor não possui e-mail cadastrado. Edite o cadastro e informe um e-mail antes de criar o acesso.'
        else:
            senha_provisoria = gerar_senha_provisoria()

            novo_usuario = Usuario(
                id_produtor      = produtor.id,
                login            = produtor.cpf_cnpj,
                senha            = generate_password_hash(senha_provisoria),
                perfil           = 'PRODUTOR',
                nome             = produtor.nome,
                email            = produtor.email,
                # False = senha provisoria, obriga troca no
                # proximo login (mesmo padrao de esqueci_senha()).
                senha_provisoria = False,
                # True = login ainda e o CPF/CNPJ, usuario ainda
                # nao escolheu um login proprio (feature futura,
                # ver Tabelas/alterar_usuarios_login_provisorio.sql).
                login_provisorio = True
            )
            db.add(novo_usuario)
            db.flush()  # garante novo_usuario.id antes do vinculo

            novo_vinculo_acesso = UsuarioVinculo(
                id_usuario  = novo_usuario.id,
                id_produtor = produtor.id,
                cargo       = 'TITULAR',
                data_inicio = date.today()
            )
            db.add(novo_vinculo_acesso)
            db.commit()

            # Usuario/UsuarioVinculo ja foram criados e commitados
            # neste ponto - acesso_criado_agora reflete isso, mesmo
            # que o envio do e-mail (logo abaixo) venha a falhar.
            acesso_criado_agora = True

            # --- Envio de e-mail (obrigatorio) ---
            try:
                msg = Message(
                    subject    = 'Orion SISBOV — Seu acesso foi criado',
                    sender     = 'noreply.consisteti@gmail.com',
                    recipients = [produtor.email]
                )
                link_login = url_for('auth.login', _external=True)
                msg.body = (
                    f'Ola, {produtor.nome}!\n\n'
                    f'Seu cadastro no Orion SISBOV foi criado com sucesso.\n\n'
                    f'Login: {produtor.cpf_cnpj}\n'
                    f'Senha provisoria: {senha_provisoria}\n\n'
                    f'Acesse o sistema com este login e senha: {link_login}\n'
                    f'Voce sera redirecionado para criar um login e uma senha novos.\n\n'
                    f'Atenciosamente,\n'
                    f'Orion SISBOV — Consiste Informatica'
                )
                mail.send(msg)
            except Exception as e:
                erro_criacao = (
                    'Acesso criado, mas houve falha ao enviar o e-mail. '
                    'Confira o e-mail cadastrado ou oriente o Produtor a usar '
                    '"Esqueci minha senha" na tela de login, informando o CPF/CNPJ.'
                )
                print(f'ERRO Flask-Mail (Criar Acesso Produtor): {e}')

            # --- Link de WhatsApp (opcional, envio manual - mesmo
            # padrao "envio final sempre manual" de prospects.py).
            # SEM o CPF na mensagem (decisao de Benedito). ---
            if produtor.telefone:
                mensagem_whatsapp = (
                    f'Olá, {produtor.nome}! 🎉 Seu acesso na plataforma Orion SISBOV foi criado.\n'
                    f'Seu login é o seu CPF.\n'
                    f'Sua senha provisória é: {senha_provisoria}\n'
                    f'É só entrar que o sistema já vai pedir pra você criar um login e uma senha novos. '
                    f'Qualquer dúvida, chama a gente!'
                )
                link_whatsapp = (
                    f'https://wa.me/{DDI_BRASIL}{produtor.telefone}'
                    f'?text={urllib.parse.quote(mensagem_whatsapp)}'
                )

    # Re-renderiza a MESMA tela de edicao do Produtor - a senha
    # provisoria e o link de WhatsApp so existem neste momento,
    # nao sao gravados em lugar nenhum (nunca em texto puro no
    # banco), entao um redirect os perderia.
    with Session(engine) as db:
        produtor_atualizado = db.get(Produtor, id)

    return render_template('consiste/produtor_cadastro.html',
        produtor              = produtor_atualizado,
        id_propriedade         = None,
        nome_propriedade       = None,
        id_produtor_completar  = None,
        travar_documento       = False,
        id_vinculo             = None,
        vinculo_ativo          = None,
        tem_acesso              = acesso_criado_agora,
        acesso_criado_agora     = acesso_criado_agora,
        link_whatsapp           = link_whatsapp,
        tipos_pessoa           = TIPOS_PESSOA,
        visibilidades          = VISIBILIDADES,
        ufs                    = UFS_BRASIL,
        erro                   = erro_criacao,
        usuario_nome           = session.get('usuario_nome'),
        usuario_perfil         = session.get('usuario_perfil'),
        cor_primaria           = session.get('cor_primaria', '#D4370A'),
        nome_sistema           = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo             = 'produtores'
    )


@produtores.route('/produtores/relatorio/<int:id>')
def relatorio_pdf(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    with Session(engine) as db:
        produtor = db.get(Produtor, id)
        if not produtor:
            return redirect(url_for('produtores.lista'))

        vinculos_ativos = db.query(PropriedadeProdutor).filter(
            PropriedadeProdutor.id_produtor == id,
            PropriedadeProdutor.data_fim.is_(None)
        ).all()

        propriedades_ativas = []
        for vinculo in vinculos_ativos:
            propriedade = db.get(Propriedade, vinculo.id_propriedade)
            if propriedade:
                propriedades_ativas.append({
                    'propriedade': propriedade,
                    'data_inicio': vinculo.data_inicio
                })

        html_renderizado = render_template('consiste/produtor_relatorio_pdf.html',
            produtor             = produtor,
            propriedades_ativas  = propriedades_ativas,
            data_emissao         = date.today().strftime('%d/%m/%Y')
        )

    buffer_pdf = BytesIO()
    pisa.CreatePDF(html_renderizado, dest=buffer_pdf, link_callback=link_callback_pdf)
    buffer_pdf.seek(0)

    nome_arquivo = f'produtor_{id}_relatorio.pdf'
    return send_file(
        buffer_pdf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=nome_arquivo
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\produtores.py
# =========================================================