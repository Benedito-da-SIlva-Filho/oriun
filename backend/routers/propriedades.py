# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\routers
# MODULO:       backend\routers\propriedades.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-07-02 15:57 -03
# ATUALIZADO EM: 2026-11-12 17:40 -03
# VERSAO: 1.16.0
# v1.16.0: Sessao 122 (2026-11-12 17:40 -03) - Auditoria Etapa 2 (itens 2,3,5,6,10): vinculo encerrado tira o acesso; Codigo ERAS/OESA/Protocolos so Titular/Administrador/Administrativo/Consiste; Area com virgula e obrigatorios validados; Codigo ERAS repetido bloqueia; id inexistente sem erro 500; Protocolos so processados se a tela os enviou (antes o Produtor inativava todos ao salvar). REVERSAO: .bak_antes_s122_etapa2.
# v1.15.0: Sessao 116 (2026-11-06 16:01 -03) - editar() passa pode_adicionar_produtor (so Titular/Administrador; CONSISTE sempre) ao template. REVERSAO: .bak_antes_s116_addprodutor.
#
# DESCRICAO:
#     Rotas do modulo de Propriedades (plataforma Consiste).
#     Cadastro exclusivo da Consiste - Produtor tem apenas
#     consulta (rota separada, fora deste arquivo, ainda a
#     ser construida - navegacao Page-Up/Page-Down) - EXCETO
#     para completar sua propria 1a Propriedade (P-040, ver
#     v1.11.0 abaixo) e para acessar a propria Propriedade a
#     qualquer momento via menu (v1.13.0).
#     - /propriedades              -> lista todas, com busca por nome
#     - /propriedades/nova         -> formulario nova
#     - /propriedades/salvar       -> salva nova ou edicao (inclui
#                                      ativacao/desativacao de
#                                      Protocolos de Certificacao)
#     - /propriedades/editar/<id>  -> formulario edicao
#     - /propriedades/toggle/<id>  -> ativa ou inativa
#     - /produtor/propriedade      -> (v1.13.0) descobre a Propriedade
#                                      do PRODUTOR logado e redireciona
#                                      para editar() - usada pelo item
#                                      "Minha Propriedade" do menu
#
#     Campos preenchidos pela Consiste no cadastro: nome, tipo,
#     inscricao_estadual, nirf_incra, car, oesa, codigo_eras,
#     logradouro, numero, bairro, cep, municipio, uf,
#     roteiro_acesso, distancia_sede_cidade, email, telefone,
#     telefone2, area_hectares, latitude, longitude.
#
#     Campos que ficam de fora do formulario (preenchidos por
#     outro fluxo ou automaticamente): id_certificadora (nasce
#     nulo - preenchido pela Certificadora em fluxo proprio,
#     P-013); ativo (nasce true); status_atividade (nasce
#     'Ativo'); criado_em/atualizado_em (automaticos).
#     codigo_eras SAIU desta lista na v1.14.0 - ver changelog
#     abaixo, agora e capturado pelo formulario.
#
#     v1.0.0: Criacao do modulo.
#     v1.1.0: Sessao 010 - Removido campo complemento (coluna
#             excluida do banco - "fazenda nao tem
#             complemento"). Adicionado campo
#             distancia_sede_cidade (texto livre).
#     v1.2.0: Sessao 010 - Telefone, telefone2 e cep chegam do
#             formulario com mascara visual (JS). Backend agora
#             limpa (so digitos) antes de salvar, como seguranca
#             extra - mesmo raciocinio do uppercase server-side.
#     v1.3.0: Sessao 010 - Validacao de latitude/longitude no
#             servidor (fonte da verdade - Produtor tera acesso
#             direto no futuro, sem a revisao manual da Consiste).
#             Latitude precisa estar entre -90 e 90, longitude
#             entre -180 e 180. Se invalido, cadastro NAO salva -
#             formulario e re-exibido com erro e os dados ja
#             digitados preservados (SimpleNamespace).
#     v1.4.0: Sessao 010 - Validacao de tamanho maximo de cada
#             campo de texto no servidor, batendo com o limite
#             real da coluna no banco. Motivo: erro real em
#             producao - campo oesa com 13 caracteres, coluna
#             so aceita 11, banco rejeitou o INSERT. maxlength
#             no HTML (template) e a primeira camada; esta
#             validacao no servidor e a segunda, definitiva.
#     v1.5.0: Sessao 010 - Campo UF passa a usar lista fechada
#             UFS_BRASIL (27 opcoes), enviada ao template para
#             popular o dropdown. Motivo: "TR" foi aceito como
#             UF valida no formulario antigo (input texto livre
#             com so limite de tamanho, sem validar conteudo).
#     v1.6.0: Sessao 011 - Adicionada logica de Protocolos de
#             Certificacao (ABPO, PEFB, CSCB, Cota Hilton, e
#             futuros cadastrados via Configuracoes). Rotas nova/
#             editar passam a enviar o catalogo de protocolos
#             ativos e os ids dos protocolos ja vinculados
#             (ativos) aquela Propriedade. A rota salvar() so
#             processa protocolos quando ha id (edicao) - secao
#             fica desabilitada no formulario de Propriedade Nova,
#             pois o vinculo depende de id_propriedade existente.
#             Marcar um protocolo novo cria vinculo (status=ativo,
#             data_ativacao=hoje). Desmarcar um protocolo ja ativo
#             exige motivo (voluntaria/compulsoria) e observacao,
#             capturados no modal do template e enviados em campos
#             hidden - atualiza o vinculo existente para
#             status=inativo, sem apagar o historico.
#     v1.7.0: Sessao 011 - Correcao de acentuacao nas mensagens
#             de erro exibidas ao usuario (essas sao texto visivel
#             na tela, mesmo vindo do backend).
#     v1.8.0: Sessao 011.1 - Rota editar() passa a buscar tambem
#             os vinculos de Proprietario ATIVOS (sem data_fim)
#             daquela Propriedade, via nova funcao auxiliar
#             _dados_proprietarios(). Enviados ao template como
#             proprietarios_vinculados, para a nova secao
#             "Proprietario(s)" em propriedade_cadastro.html
#             (lista + botao Encerrar + link "Adicionar
#             Proprietario", que leva para
#             /proprietarios/novo?id_propriedade=<id>).
#             Nao ha rota nova aqui - vincular/criar/encerrar
#             Proprietario sao rotas do proprietarios.py.
#     v1.9.0: Sessao 011.1 - _dados_proprietarios() passa a
#             buscar TODOS os vinculos (ativos e inativos), nao
#             so os ativos - permite reativar um vinculo pelo
#             toggle na tela (mesmo padrao Ativo/Inativo ja usado
#             em Propriedade/Proprietario). Cada item ganha o
#             campo 'ativo' (True quando data_fim e nulo).
#     v1.10.0: Sessao 011.1 - Adicionada funcao auxiliar
#             _dados_produtores(), espelhando
#             _dados_proprietarios() para o modulo Produtor.
#             editar() e o caminho de erro de salvar() passam a
#             buscar e enviar produtores_vinculados ao template,
#             para a nova secao "Produtor(es)" em
#             propriedade_cadastro.html. Nao ha rota nova aqui -
#             vincular/criar/toggle de Produtor sao rotas do
#             produtores.py.
#     v1.11.0: Sessao 032 - P-040: perfil PRODUTOR passa a poder
#             acessar editar()/salvar() (antes exclusivo CONSISTE),
#             MAS APENAS para a Propriedade vinculada a ele mesmo
#             (checagem de posse via PropriedadeProdutor.id_produtor
#             == session['id_produtor']) - qualquer outra Propriedade
#             continua barrada. Produtor NAO pode acessar nova() nem
#             salvar() sem id (criar Propriedade nova) - decisao com
#             Benedito: a 1a Propriedade nasce pelo Convite Publico
#             (ja existe, so precisa completar); da 2a em diante, o
#             cliente entra em contato e a Consiste cadastra direto,
#             ja completa. Ao salvar com sucesso via edicao,
#             p.cadastro_completo e marcado True (o formulario
#             completo exige os campos que estavam em placeholder) -
#             fecha o ciclo do pre-cadastro do Convite. Redirecionamento
#             pos-salvar passa a depender do perfil: CONSISTE vai para
#             propriedades.lista (como sempre); PRODUTOR vai para a
#             Home dele (nao tem acesso a lista de Propriedades).
#     v1.12.0: Sessao 033 - P-040, trava progressiva de onboarding:
#             Benedito trouxe caso real de usabilidade - o Produtor
#             (Titular) deve completar o cadastro em ordem:
#             Proprietario -> Produtor(es) -> Dados da Propriedade,
#             nao tudo liberado de uma vez. Duas funcoes auxiliares
#             novas: _tem_proprietario_ativo() (confere se ja existe
#             >=1 Proprietario ativo vinculado) e
#             _produtor_titular_completo() (confere se o Produtor da
#             sessao ja saiu do placeholder municipio='A COMPLETAR'/
#             uf='XX', preenchido por produtores.py v1.6.0). Essa
#             trava so entra em acao quando perfil == PRODUTOR e
#             propriedade.cadastro_completo == False (onboarding
#             pos-Convite) - CONSISTE nunca e afetada. editar() passa
#             as flags trava_secao_produtor/trava_dados_propriedade
#             ao template (propriedade_cadastro.html v1.16.0), que
#             aplica o mesmo padrao visual secao-desabilitada ja
#             usado em Protocolos. IMPORTANTE: a trava do template e
#             so visual (pointer-events) - salvar() ganhou a MESMA
#             checagem no servidor, bloqueando de verdade (redireciona
#             de volta para editar()) se alguem tentar burlar a ordem
#             manipulando o HTML. Sem isso a trava seria so estetica.
#     v1.13.0: Sessao 034 - Benedito identificou que o menu lateral
#             do PRODUTOR (produtor_menu.html) nao tinha NENHUM
#             caminho de acesso a tela de Propriedade (filiar ou
#             inativar Proprietario(s)/Produtor(es)) fora da trava
#             de onboarding ou do botao "Voltar". Decisao: essa
#             responsabilidade e do proprio PRODUTOR ("porteira
#             para dentro"). Nova rota /produtor/propriedade
#             (funcao minha_propriedade()) - exclusiva perfil
#             PRODUTOR, descobre a Propriedade vinculada via
#             session['id_produtor'] (mesmo padrao ja usado em
#             auth.py/produtor_home()) e redireciona para
#             editar(id=...). Reaproveita 100% a tela e as regras
#             ja existentes (trava progressiva, edicao de vinculos)
#             - nenhuma logica nova de negocio, so um novo caminho
#             de entrada. Usada pelo item "Minha Propriedade" em
#             produtor_menu.html v1.1.0.
#     v1.14.0: Sessao 034 (continuacao 5, 11/08/2026, 16:10 -03) -
#             Rota salvar() passa a capturar, validar tamanho e
#             gravar o campo codigo_eras (Codigo SISBOV/ERAS),
#             tanto na criacao quanto na edicao. Decisao de
#             Benedito: como a tela de Propriedade atende tanto o
#             Produtor comum quanto o exportador/SISBOV, a Consiste
#             pode preencher o codigo ja no cadastro, quando
#             conhecido, sem depender exclusivamente do fluxo
#             futuro da Certificadora (P-013, que continua
#             pendente para o caso de preenchimento/alteracao pela
#             Certificadora). Campo OPCIONAL (sem obrigatoriedade),
#             mesmo padrao de Latitude/Longitude - Produtor comum
#             deixa em branco sem bloquear o cadastro. Adicionado
#             a LIMITES_TAMANHO (20 caracteres, batendo com
#             propriedade.py/codigo_eras = String(20)). NAO exigiu
#             nenhuma mudanca em editar()/nova() - o objeto
#             'propriedade' inteiro ja e passado ao template, que
#             agora so passou a exibir o campo ja existente no
#             model (ver propriedade_cadastro.html v1.20.0).
#     v1.14.1: Sessao 097 (15/10/2026, 11:20 -03) - AUDITORIA DE PERMISSOES: toggle()/salvar() conferiam so o login; passam a
#             exigir perfil CONSISTE, a mesma regra das telas desta rota. Nenhuma outra mudanca.
#     v1.14.2: Sessao 101 (20/10/2026, 17:55 -03) - MINHA PROPRIEDADE RESPEITA A FAZENDA EM USO: minha_propriedade() abria sempre a primeira Propriedade do Produtor; agora, havendo fazenda em uso (session fazenda_ativa) do mesmo Produtor, abre ela. Sem fazenda em uso, tudo como antes. REVERSAO: devolver .bak_antes_fazenda_em_uso_s101.
# =========================================================

import re
from datetime import date
from types import SimpleNamespace
from flask import Blueprint, render_template, request, redirect, url_for, session
from backend.database import engine
from backend.models import Propriedade, Protocolo, PropriedadeProtocolo, PropriedadeProprietario, Proprietario, PropriedadeProdutor, Produtor
from backend.routers.auth import redirecionar_home
from backend.utils.permissao_produtor import pode_cadastrar_produtor, MSG_SO_TITULAR_ADMIN, pode_alterar_certificacao, MSG_SO_CARGOS_CERTIFICACAO
from sqlalchemy.orm import Session

# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
propriedades = Blueprint('propriedades', __name__)

# -------------------------------------------------------
# Tipos disponiveis para Propriedade
# -------------------------------------------------------
TIPOS_PROPRIEDADE = ['MISTA', 'CORTE', 'LEITE']

# -------------------------------------------------------
# UFs do Brasil - lista fechada para o dropdown de UF
# -------------------------------------------------------
UFS_BRASIL = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
    'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
    'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]


# -------------------------------------------------------
# Funcao auxiliar: confere se a Propriedade id_propriedade
# esta vinculada ao Produtor da sessao atual (session
# ['id_produtor'], gravada no login() a partir do vinculo
# ativo). Usada para liberar o perfil PRODUTOR a
# editar()/salvar() SOMENTE a sua propria Propriedade
# (P-040, Sessao 032) - qualquer outra continua barrada.
# -------------------------------------------------------
def _produtor_possui_propriedade(db, id_propriedade):
    id_produtor_sessao = session.get('id_produtor')
    if not id_produtor_sessao:
        return False

    # Etapa 2 (item 2): so conta vinculo ATIVO (data_fim vazio). Vinculo encerrado
    # pela Consiste tira o acesso do Produtor a tela da Propriedade.
    vinculo = db.query(PropriedadeProdutor).filter_by(
        id_propriedade=id_propriedade,
        id_produtor=id_produtor_sessao,
        data_fim=None
    ).first()
    return vinculo is not None


# -------------------------------------------------------
# Funcao auxiliar (P-040, Sessao 033): confere se a
# Propriedade ja tem pelo menos 1 Proprietario ATIVO
# (data_fim is None) vinculado. Usada para travar a secao
# Produtor(es) no onboarding do Convite (perfil PRODUTOR +
# cadastro_completo == False) - o Produtor so pode avancar
# depois de cadastrar o Proprietario. Para CONSISTE, essa
# trava nunca e aplicada (ver onboarding_ativo em editar()).
# -------------------------------------------------------
def _tem_proprietario_ativo(db, id_propriedade):
    vinculo = db.query(PropriedadeProprietario).filter(
        PropriedadeProprietario.id_propriedade == id_propriedade,
        PropriedadeProprietario.data_fim.is_(None)
    ).first()
    return vinculo is not None


# -------------------------------------------------------
# Funcao auxiliar (P-040, Sessao 033): confere se o Produtor
# (Titular, criado na transacao do Convite) ja completou os
# campos que nasceram em placeholder (municipio = 'A
# COMPLETAR', uf = 'XX'). Usada para travar a secao Dados da
# Propriedade no onboarding - so libera depois que o Titular
# completar os proprios dados via produtor_cadastro.html
# (modo edicao, ver produtores.py v1.6.0).
# -------------------------------------------------------
def _produtor_titular_completo(db, id_produtor):
    if not id_produtor:
        return False
    produtor = db.get(Produtor, id_produtor)
    if not produtor:
        return False
    return produtor.municipio != 'A COMPLETAR' and produtor.uf != 'XX'


# -------------------------------------------------------
# Funcao auxiliar: busca o catalogo de protocolos ativos e
# os ids dos protocolos ja vinculados (ativos) a uma
# Propriedade. Reaproveitada em nova(), editar() e no
# caminho de erro de salvar().
# -------------------------------------------------------
def _dados_protocolos(db, id_propriedade):
    protocolos_catalogo = db.query(Protocolo).filter(
        Protocolo.ativo == True
    ).order_by(Protocolo.nome).all()

    vinculos_ativos_ids = []
    if id_propriedade:
        vinculos = db.query(PropriedadeProtocolo).filter(
            PropriedadeProtocolo.id_propriedade == id_propriedade,
            PropriedadeProtocolo.status == 'ativo'
        ).all()
        vinculos_ativos_ids = [v.id_protocolo for v in vinculos]

    return protocolos_catalogo, vinculos_ativos_ids


# -------------------------------------------------------
# Funcao auxiliar: busca TODOS os vinculos de Proprietario
# (ativos e inativos) de uma Propriedade, ja combinados com
# os dados do Proprietario (nome, cpf_cnpj), para exibir na
# secao "Proprietario(s)" do template com o toggle Ativo/
# Inativo. Reaproveitada so em editar() - Propriedade Nova
# nao tem vinculo ainda, pois depende de id_propriedade
# existente (mesma regra ja usada em Protocolos).
# -------------------------------------------------------
def _dados_proprietarios(db, id_propriedade):
    vinculos = db.query(PropriedadeProprietario).filter(
        PropriedadeProprietario.id_propriedade == id_propriedade
    ).order_by(PropriedadeProprietario.data_inicio).all()

    proprietarios_vinculados = []
    for vinculo in vinculos:
        proprietario = db.get(Proprietario, vinculo.id_proprietario)
        if proprietario:
            proprietarios_vinculados.append({
                'id_vinculo':   vinculo.id,
                'proprietario': proprietario,
                'data_inicio':  vinculo.data_inicio,
                'data_fim':     vinculo.data_fim,
                'ativo':        vinculo.data_fim is None
            })

    return proprietarios_vinculados


# -------------------------------------------------------
# Funcao auxiliar: busca TODOS os vinculos de Produtor
# (ativos e inativos) de uma Propriedade, ja combinados com
# os dados do Produtor (nome, cpf_cnpj), para exibir na
# secao "Produtor(es)" do template com o toggle Ativo/
# Inativo. Espelha _dados_proprietarios(). Reaproveitada so
# em editar() - Propriedade Nova nao tem vinculo ainda.
# -------------------------------------------------------
def _dados_produtores(db, id_propriedade):
    vinculos = db.query(PropriedadeProdutor).filter(
        PropriedadeProdutor.id_propriedade == id_propriedade
    ).order_by(PropriedadeProdutor.data_inicio).all()

    produtores_vinculados = []
    for vinculo in vinculos:
        produtor = db.get(Produtor, vinculo.id_produtor)
        if produtor:
            produtores_vinculados.append({
                'id_vinculo':  vinculo.id,
                'produtor':    produtor,
                'data_inicio': vinculo.data_inicio,
                'data_fim':    vinculo.data_fim,
                'ativo':       vinculo.data_fim is None
            })

    return produtores_vinculados


# -------------------------------------------------------
# Rota: /propriedades — lista todas, com busca por nome
# Requer perfil CONSISTE.
# -------------------------------------------------------
@propriedades.route('/propriedades')
def lista():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    termo_busca = request.args.get('busca', '').strip()

    with Session(engine) as db:
        query = db.query(Propriedade)
        if termo_busca:
            query = query.filter(Propriedade.nome.ilike(f'%{termo_busca}%'))
        lista_propriedades = query.order_by(Propriedade.nome).all()

    return render_template('consiste/propriedade_lista.html',
        propriedades   = lista_propriedades,
        termo_busca    = termo_busca,
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = 'propriedades'
    )

# -------------------------------------------------------
# Rota: /propriedades/nova — formulario nova
# Requer perfil CONSISTE. Secao de Protocolos e a secao de
# Proprietario(s) aparecem desabilitadas (nao ha
# id_propriedade ainda).
# PRODUTOR NAO acessa esta rota (P-040, Sessao 032) - a 1a
# Propriedade ja existe (nasceu pelo Convite Publico), so
# precisa ser completada via editar(); da 2a em diante, o
# cadastro e feito pela Consiste (cliente entra em contato).
# -------------------------------------------------------
@propriedades.route('/propriedades/nova')
def nova():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirect(url_for('auth.consiste_home'))

    with Session(engine) as db:
        protocolos_catalogo, vinculos_ativos_ids = _dados_protocolos(db, None)

    return render_template('consiste/propriedade_cadastro.html',
        propriedade              = None,
        tipos                     = TIPOS_PROPRIEDADE,
        ufs                       = UFS_BRASIL,
        protocolos                = protocolos_catalogo,
        vinculos_ativos_ids       = vinculos_ativos_ids,
        proprietarios_vinculados  = [],
        produtores_vinculados     = [],
        trava_secao_produtor      = False,
        trava_dados_propriedade   = False,
        erro                      = None,
        usuario_nome              = session.get('usuario_nome'),
        usuario_perfil            = session.get('usuario_perfil'),
        cor_primaria              = session.get('cor_primaria', '#D4370A'),
        nome_sistema              = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo                = 'propriedades'
    )

# -------------------------------------------------------
# Rota: /propriedades/editar/<id> — formulario edicao
# Requer perfil CONSISTE, OU perfil PRODUTOR desde que a
# Propriedade seja a dele mesmo (P-040, Sessao 032 -
# _produtor_possui_propriedade()). Qualquer outro caso e
# barrado e redirecionado para a home do proprio perfil.
# Secao de Protocolos vem com os checkboxes ja marcados
# conforme vinculos ativos. Secao de Proprietario(s) vem
# com a lista de vinculos ativos (novidade da v1.8.0).
#
# P-040, Sessao 033: calcula as flags trava_secao_produtor
# e trava_dados_propriedade (ver funcoes auxiliares acima) -
# so ficam True quando perfil == PRODUTOR e a Propriedade
# ainda esta em onboarding (cadastro_completo == False).
# CONSISTE nunca recebe estas flags como True.
# -------------------------------------------------------
@propriedades.route('/propriedades/editar/<int:id>')
def editar(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    perfil = session.get('usuario_perfil')

    with Session(engine) as db:
        if perfil == 'CONSISTE':
            pass  # acesso total, como sempre
        elif perfil == 'PRODUTOR' and _produtor_possui_propriedade(db, id):
            pass  # acesso liberado so a esta Propriedade (P-040)
        else:
            return redirecionar_home(perfil)

        propriedade = db.get(Propriedade, id)
        if not propriedade:
            # Etapa 2: id que nao existe (endereco digitado errado) - volta sem erro 500.
            if perfil == 'CONSISTE':
                return redirect(url_for('propriedades.lista'))
            return redirecionar_home(perfil)
        protocolos_catalogo, vinculos_ativos_ids = _dados_protocolos(db, id)
        proprietarios_vinculados = _dados_proprietarios(db, id)
        produtores_vinculados = _dados_produtores(db, id)

        # P-040, Sessao 033: trava progressiva Proprietario ->
        # Produtor -> Dados da Propriedade, exclusiva do
        # onboarding pos-Convite.
        onboarding_ativo = (perfil == 'PRODUTOR' and not propriedade.cadastro_completo)
        trava_secao_produtor = onboarding_ativo and not _tem_proprietario_ativo(db, id)
        trava_dados_propriedade = onboarding_ativo and not _produtor_titular_completo(db, session.get('id_produtor'))

    return render_template('consiste/propriedade_cadastro.html',
        propriedade               = propriedade,
        tipos                      = TIPOS_PROPRIEDADE,
        ufs                        = UFS_BRASIL,
        protocolos                 = protocolos_catalogo,
        vinculos_ativos_ids        = vinculos_ativos_ids,
        proprietarios_vinculados   = proprietarios_vinculados,
        produtores_vinculados      = produtores_vinculados,
        pode_adicionar_produtor    = pode_cadastrar_produtor(id),
        msg_so_titular_admin       = MSG_SO_TITULAR_ADMIN,
        pode_alterar_certificacao  = pode_alterar_certificacao(id),
        msg_so_cargos_certificacao = MSG_SO_CARGOS_CERTIFICACAO,
        trava_secao_produtor       = trava_secao_produtor,
        trava_dados_propriedade    = trava_dados_propriedade,
        erro                       = None,
        usuario_nome               = session.get('usuario_nome'),
        usuario_perfil             = session.get('usuario_perfil'),
        cor_primaria               = session.get('cor_primaria', '#D4370A'),
        nome_sistema               = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo                 = 'propriedades'
    )

# -------------------------------------------------------
# Rota: /propriedades/salvar — salva nova ou edicao
# Nova: id_certificadora nasce nulo. ativo nasce True,
# status_atividade nasce 'Ativo'. codigo_eras agora e
# capturado do formulario (v1.14.0), OPCIONAL - nasce vazio
# se o Produtor for comum/nao-SISBOV.
# Protocolos so sao processados quando ha id (edicao) -
# na Propriedade Nova a secao vem desabilitada no template,
# entao nenhum campo protocolo_<id> chega ao servidor.
# Proprietario(s) NAO sao processados aqui - vinculo/
# criacao/encerramento sao rotas proprias em
# proprietarios.py, chamadas direto da tela de Propriedade.
#
# P-040 (Sessao 032): perfil PRODUTOR so pode submeter com
# id preenchido (edicao) E dono da Propriedade - nunca cria
# Propriedade nova (sem id e barrado). Ao salvar com sucesso
# via edicao, cadastro_completo e marcado True. Redirecionamento
# pos-salvar depende do perfil (CONSISTE -> lista; PRODUTOR ->
# home dele).
#
# P-040, Sessao 033: checagem de SEGURANCA NO SERVIDOR da
# trava progressiva. A trava do template (propriedade_
# cadastro.html v1.16.0) e so visual (pointer-events) - um
# Produtor mal-intencionado poderia manipular o HTML e tentar
# salvar os Dados da Propriedade fora de ordem. Esta checagem
# bloqueia isso de verdade: se a Propriedade ainda esta em
# onboarding e a ordem nao foi respeitada (sem Proprietario
# ativo, ou Produtor Titular ainda em placeholder), redireciona
# de volta para editar() sem salvar nada.
# -------------------------------------------------------
@propriedades.route('/propriedades/salvar', methods=['POST'])
def salvar():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    perfil = session.get('usuario_perfil')
    id     = request.form.get('id')

    # --- Checagem de permissao (P-040) ---
    if perfil == 'CONSISTE':
        pass  # acesso total, como sempre
    elif perfil == 'PRODUTOR':
        if not id:
            # Produtor nunca cria Propriedade nova - da 2a em
            # diante e a Consiste quem cadastra (cliente entra
            # em contato).
            return redirecionar_home(perfil)
        with Session(engine) as db:
            if not _produtor_possui_propriedade(db, int(id)):
                return redirecionar_home(perfil)

            # P-040, Sessao 033: checagem de seguranca da trava
            # progressiva - ver explicacao no cabecalho da rota.
            propriedade_atual = db.get(Propriedade, int(id))
            if propriedade_atual and not propriedade_atual.cadastro_completo:
                if not _tem_proprietario_ativo(db, int(id)):
                    return redirect(url_for('propriedades.editar', id=id))
                if not _produtor_titular_completo(db, session.get('id_produtor')):
                    return redirect(url_for('propriedades.editar', id=id))
    else:
        return redirecionar_home(perfil)

    # Etapa 2 (item 3): Codigo ERAS, OESA e Protocolos so mudam com Titular,
    # Administrador, Administrativo ou Consiste. Para os outros cargos o servidor
    # ignora esses campos (mantem o que ja esta gravado), mesmo que o formulario
    # seja manipulado. Propriedade nova so a Consiste cria.
    pode_cert = True if not id else pode_alterar_certificacao(id)

    nome                  = request.form.get('nome', '').upper()
    tipo                  = request.form.get('tipo')
    inscricao_estadual    = request.form.get('inscricao_estadual', '').upper()
    nirf_incra            = request.form.get('nirf_incra', '').upper()
    car                   = request.form.get('car', '').upper()
    codigo_eras           = request.form.get('codigo_eras', '').upper()
    oesa                  = request.form.get('oesa', '').upper()
    logradouro            = request.form.get('logradouro', '').upper()
    numero                = request.form.get('numero', '').upper()
    bairro                = request.form.get('bairro', '').upper()
    cep                   = re.sub(r'\D', '', request.form.get('cep', ''))
    municipio             = request.form.get('municipio', '').upper()
    uf                    = request.form.get('uf', '').upper()
    roteiro_acesso        = request.form.get('roteiro_acesso', '').upper()
    distancia_sede_cidade = request.form.get('distancia_sede_cidade', '').upper()
    email                 = request.form.get('email', '').strip().lower()
    telefone              = re.sub(r'\D', '', request.form.get('telefone', ''))
    telefone2             = re.sub(r'\D', '', request.form.get('telefone2', ''))
    area_hectares         = request.form.get('area_hectares')
    if id and not pode_cert:
        with Session(engine) as db:
            p_atual = db.get(Propriedade, int(id))
            if p_atual:
                codigo_eras = p_atual.codigo_eras or ''
                oesa        = p_atual.oesa or ''
    latitude              = request.form.get('latitude') or None
    longitude             = request.form.get('longitude') or None

    # -----------------------------------------------------
    # Validacao de latitude/longitude (servidor = fonte da
    # verdade). Latitude: -90 a 90. Longitude: -180 a 180.
    # Se incorreto, NAO salva - re-exibe o formulario com erro
    # e os dados ja digitados preservados, para o usuario nao
    # perder o preenchimento. O template (v1.20.0) ja converte
    # formatos alternativos (GMS, decimal com virgula) para
    # decimal com ponto ANTES do submit - esta validacao aqui
    # continua sendo a fonte da verdade final, sem mudanca.
    # -----------------------------------------------------
    erro_validacao = None

    # -----------------------------------------------------
    # Validacao de tamanho maximo (servidor = fonte da verdade).
    # Bate exatamente com o tamanho de cada coluna no banco -
    # evita o erro "value too long for type character varying"
    # que travou o INSERT quando o campo oesa veio com mais
    # de 11 caracteres.
    # -----------------------------------------------------
    LIMITES_TAMANHO = {
        'Nome':                  (nome, 150),
        'Inscrição Estadual':    (inscricao_estadual, 30),
        'NIRF/INCRA':            (nirf_incra, 30),
        'CAR':                   (car, 50),
        'Código SISBOV (ERAS)':  (codigo_eras, 20),
        'OESA':                  (oesa, 11),
        'Logradouro':            (logradouro, 200),
        'Numero':                (numero, 10),
        'Bairro':                (bairro, 100),
        'Município':             (municipio, 100),
        'UF':                    (uf, 2),
        'Distância Sede-Cidade': (distancia_sede_cidade, 200),
        'Email':                 (email, 150),
    }

    for nome_campo, (valor, limite) in LIMITES_TAMANHO.items():
        if valor and len(valor) > limite:
            erro_validacao = f'Campo "{nome_campo}" excede o limite de {limite} caracteres (digitado: {len(valor)}).'
            break

    # Etapa 2 (itens 5 e 6): campos obrigatorios, Area com virgula e Codigo ERAS repetido.
    # Antes, Area vazia ou texto virava erro 500 e nada conferia obrigatorios no servidor.
    if not erro_validacao:
        obrigatorios = [
            ('Nome', nome), ('Tipo', tipo), ('UF', uf), ('Município', municipio),
            ('Roteiro de acesso', roteiro_acesso), ('E-mail', email), ('Telefone', telefone),
        ]
        for nome_campo, valor in obrigatorios:
            if not (valor or '').strip():
                erro_validacao = f'Preencha o campo "{nome_campo}" e salve de novo.'
                break
    if not erro_validacao and tipo not in TIPOS_PROPRIEDADE:
        erro_validacao = 'Escolha o Tipo da Propriedade (Mista, Corte ou Leite) e salve de novo.'
    if not erro_validacao and uf not in UFS_BRASIL:
        erro_validacao = 'Escolha a UF na lista e salve de novo.'
    if not erro_validacao:
        area_txt = (area_hectares or '').strip().replace(',', '.')
        try:
            area_num = float(area_txt)
            if area_num <= 0 or area_num >= 100000000:
                raise ValueError
            area_hectares = f'{area_num:.2f}'
        except ValueError:
            erro_validacao = 'Área (hectares) incorreta! Informe um número maior que zero (ex: 150,5).'
    if not erro_validacao and codigo_eras:
        with Session(engine) as db:
            q_eras = db.query(Propriedade).filter(Propriedade.codigo_eras == codigo_eras)
            if id:
                q_eras = q_eras.filter(Propriedade.id != int(id))
            outra = q_eras.first()
            if outra:
                erro_validacao = (f'O Código ERAS {codigo_eras} já está cadastrado na Propriedade '
                                  f'{outra.nome} ({outra.municipio}/{outra.uf}). Confira o número digitado. '
                                  f'Se o código estiver certo, o cadastro repetido precisa ser tratado pela Consiste.')

    if not erro_validacao and latitude:
        try:
            lat_num = float(latitude)
            if lat_num < -90 or lat_num > 90:
                erro_validacao = 'Latitude incorreta! Deve estar entre -90 e 90 (ex: -19.3232123).'
        except ValueError:
            erro_validacao = 'Latitude incorreta! Use apenas números e ponto decimal (ex: -19.3232123).'

    if not erro_validacao and longitude:
        try:
            long_num = float(longitude)
            if long_num < -180 or long_num > 180:
                erro_validacao = 'Longitude incorreta! Deve estar entre -180 e 180 (ex: -49.2121330).'
        except ValueError:
            erro_validacao = 'Longitude incorreta! Use apenas números e ponto decimal (ex: -49.2121330).'

    if erro_validacao:
        # Reconstroi um objeto com os dados ja digitados, para
        # o formulario reaparecer preenchido (nao perde o trabalho).
        propriedade_tentativa = SimpleNamespace(
            id                    = id,
            nome                  = nome,
            tipo                  = tipo,
            inscricao_estadual    = inscricao_estadual,
            nirf_incra            = nirf_incra,
            car                   = car,
            codigo_eras           = codigo_eras,
            oesa                  = oesa,
            logradouro            = logradouro,
            numero                = numero,
            bairro                = bairro,
            cep                   = cep,
            municipio             = municipio,
            uf                    = uf,
            roteiro_acesso        = roteiro_acesso,
            distancia_sede_cidade = distancia_sede_cidade,
            email                 = email,
            telefone              = telefone,
            telefone2             = telefone2,
            area_hectares         = area_hectares,
            latitude              = latitude,
            longitude             = longitude
        )

        with Session(engine) as db:
            protocolos_catalogo, vinculos_ativos_ids = _dados_protocolos(
                db, int(id) if id else None
            )
            proprietarios_vinculados = _dados_proprietarios(db, int(id)) if id else []
            produtores_vinculados = _dados_produtores(db, int(id)) if id else []

        return render_template('consiste/propriedade_cadastro.html',
            propriedade               = propriedade_tentativa,
            tipos                      = TIPOS_PROPRIEDADE,
            ufs                        = UFS_BRASIL,
            protocolos                 = protocolos_catalogo,
            vinculos_ativos_ids        = vinculos_ativos_ids,
            proprietarios_vinculados   = proprietarios_vinculados,
            produtores_vinculados      = produtores_vinculados,
            pode_adicionar_produtor    = pode_cadastrar_produtor(id) if id else False,
            msg_so_titular_admin       = MSG_SO_TITULAR_ADMIN,
            pode_alterar_certificacao  = pode_cert,
            msg_so_cargos_certificacao = MSG_SO_CARGOS_CERTIFICACAO,
            trava_secao_produtor       = False,
            trava_dados_propriedade    = False,
            erro                       = erro_validacao,
            usuario_nome               = session.get('usuario_nome'),
            usuario_perfil             = session.get('usuario_perfil'),
            cor_primaria               = session.get('cor_primaria', '#D4370A'),
            nome_sistema               = session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo                 = 'propriedades'
        )

    with Session(engine) as db:
        if id:
            # Edicao — atualiza dados da Propriedade
            # (id_certificadora, status_atividade NAO sao
            # tocados aqui - pertencem a outro fluxo)
            p = db.get(Propriedade, int(id))
            if not p:
                return redirect(url_for('propriedades.lista')) if perfil == 'CONSISTE' else redirecionar_home(perfil)
            p.nome                  = nome
            p.tipo                  = tipo
            p.inscricao_estadual    = inscricao_estadual
            p.nirf_incra            = nirf_incra
            p.car                   = car
            p.codigo_eras           = codigo_eras or None
            p.oesa                  = oesa
            p.logradouro            = logradouro
            p.numero                = numero
            p.bairro                = bairro
            p.cep                   = cep
            p.municipio             = municipio
            p.uf                    = uf
            p.roteiro_acesso        = roteiro_acesso
            p.distancia_sede_cidade = distancia_sede_cidade
            p.email                 = email
            p.telefone              = telefone
            p.telefone2             = telefone2
            p.area_hectares         = area_hectares
            p.latitude              = latitude
            p.longitude             = longitude
            # P-040: formulario completo exige os campos que
            # nasceram em placeholder pelo Convite - fecha o
            # ciclo do pre-cadastro.
            p.cadastro_completo     = True

            # -------------------------------------------------
            # Protocolos de Certificacao
            # Compara o catalogo de protocolos ativos contra o
            # que veio marcado no formulario. Um checkbox
            # marcado que ainda nao tinha vinculo ativo -> cria
            # vinculo novo. Um checkbox desmarcado que tinha
            # vinculo ativo -> inativa o vinculo existente,
            # usando motivo/observacao que vieram do modal
            # (campos hidden). Sem mudanca -> nao mexe.
            # -------------------------------------------------
            # Etapa 2: so mexe nos Protocolos se o usuario pode E a tela enviou a secao
            # (campo protocolos_enviados). Antes, quem salvava sem a secao na tela
            # (Produtor) fazia o servidor entender "tudo desmarcado" e inativar todos.
            processar_protocolos = pode_cert and request.form.get('protocolos_enviados') == '1'
            protocolos_catalogo = db.query(Protocolo).filter(
                Protocolo.ativo == True
            ).all() if processar_protocolos else []

            vinculos_ativos = db.query(PropriedadeProtocolo).filter(
                PropriedadeProtocolo.id_propriedade == p.id,
                PropriedadeProtocolo.status == 'ativo'
            ).all()
            vinculos_por_protocolo = {v.id_protocolo: v for v in vinculos_ativos}

            for protocolo in protocolos_catalogo:
                marcado = request.form.get(f'protocolo_{protocolo.id}') is not None
                vinculo_atual = vinculos_por_protocolo.get(protocolo.id)

                if marcado and not vinculo_atual:
                    # Ativando um protocolo novo para esta Propriedade
                    novo_vinculo = PropriedadeProtocolo(
                        id_propriedade = p.id,
                        id_protocolo   = protocolo.id,
                        data_ativacao  = date.today(),
                        status         = 'ativo'
                    )
                    db.add(novo_vinculo)

                elif not marcado and vinculo_atual:
                    # Desativando - motivo e observacao vieram do
                    # modal do template (campos hidden). Se por
                    # algum motivo chegarem vazios, assume
                    # 'voluntaria' como motivo padrao (nao deve
                    # acontecer, pois o modal exige selecao).
                    motivo = request.form.get(f'motivo_inativacao_{protocolo.id}', '').strip()
                    observacao = request.form.get(f'observacao_inativacao_{protocolo.id}', '').strip()

                    vinculo_atual.status = 'inativo'
                    vinculo_atual.motivo_inativacao = motivo or 'voluntaria'
                    vinculo_atual.observacao_inativacao = observacao or None
                    vinculo_atual.data_desativacao = date.today()

        else:
            # Nova — id_certificadora nasce nulo (preenchido
            # pela Certificadora em fluxo proprio). ativo=True e
            # status_atividade='Ativo' por padrao. codigo_eras
            # agora e capturado do formulario (v1.14.0) - fica
            # None se o campo vier vazio (Produtor comum/nao-
            # SISBOV). cadastro_completo nasce True (default da
            # coluna) - cadastro pela Consiste, via formulario
            # completo, ja nasce completo. Protocolos e
            # Proprietario(s) nao se aplicam aqui - ambas as
            # secoes vem desabilitadas no template para
            # Propriedade Nova. So CONSISTE chega aqui (PRODUTOR
            # e barrado antes, ver checagem acima).
            p = Propriedade(
                nome                  = nome,
                tipo                  = tipo,
                inscricao_estadual    = inscricao_estadual,
                nirf_incra            = nirf_incra,
                car                   = car,
                codigo_eras           = codigo_eras or None,
                oesa                  = oesa,
                logradouro            = logradouro,
                numero                = numero,
                bairro                = bairro,
                cep                   = cep,
                municipio             = municipio,
                uf                    = uf,
                roteiro_acesso        = roteiro_acesso,
                distancia_sede_cidade = distancia_sede_cidade,
                email                 = email,
                telefone              = telefone,
                telefone2             = telefone2,
                area_hectares         = area_hectares,
                latitude              = latitude,
                longitude             = longitude,
                ativo                 = True,
                status_atividade      = 'Ativo'
            )
            db.add(p)

        db.commit()

    # P-040: redirecionamento pos-salvar depende do perfil -
    # PRODUTOR nao tem acesso a lista de Propriedades (essa
    # continua exclusiva CONSISTE), vai para a propria Home.
    if perfil == 'PRODUTOR':
        return redirecionar_home(perfil)

    return redirect(url_for('propriedades.lista'))

# -------------------------------------------------------
# Rota: /propriedades/toggle/<id> — ativa ou inativa
# -------------------------------------------------------
@propriedades.route('/propriedades/toggle/<int:id>', methods=['POST'])
def toggle(id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirecionar_home(session.get('usuario_perfil'))

    with Session(engine) as db:
        p = db.get(Propriedade, id)
        if not p:
            return redirect(url_for('propriedades.lista'))
        p.ativo = not p.ativo
        db.commit()

    return redirect(url_for('propriedades.lista'))

# -------------------------------------------------------
# Rota: /produtor/propriedade — descobre a Propriedade do
# PRODUTOR logado e redireciona para editar().
#
# Sessao 034: criada para dar ao PRODUTOR um caminho de
# acesso a propria Propriedade a partir do menu lateral
# (produtor_menu.html v1.1.0, item "Minha Propriedade") -
# antes, so era possivel chegar la pela trava de onboarding
# (P-040) ou pelo botao "Voltar" (propriedade_cadastro.html
# v1.18.0). Reaproveita 100% a tela e as regras de editar()
# ja existentes - esta rota so descobre o id e redireciona,
# nenhuma logica de negocio nova.
#
# Exclusiva perfil PRODUTOR. Busca a Propriedade vinculada
# via session['id_produtor'] (mesmo padrao ja usado em
# auth.py/produtor_home() e em _produtor_possui_propriedade()
# acima). Se por algum motivo o Produtor nao tiver nenhuma
# Propriedade vinculada (nao deveria acontecer, mas por
# seguranca), volta para a Home sem quebrar.
# -------------------------------------------------------
@propriedades.route('/produtor/propriedade')
def minha_propriedade():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    perfil = session.get('usuario_perfil')
    if perfil != 'PRODUTOR':
        return redirecionar_home(perfil)

    # v1.14.2: fazenda em uso (Home com 2+ fazendas) manda; sem ela, a primeira, como antes.
    fazenda = session.get('fazenda_ativa') or {}
    try:
        id_prop_em_uso = int(fazenda.get('id_propriedade')) if int(fazenda.get('id_produtor')) == int(session.get('id_produtor')) else None
    except (TypeError, ValueError):
        id_prop_em_uso = None

    with Session(engine) as db:
        consulta = db.query(PropriedadeProdutor).filter_by(id_produtor=session.get('id_produtor'))
        vinculo = consulta.filter_by(id_propriedade=id_prop_em_uso).first() if id_prop_em_uso else None
        if not vinculo:
            vinculo = consulta.first()

        if not vinculo:
            return redirecionar_home(perfil)

    return redirect(url_for('propriedades.editar', id=vinculo.id_propriedade))

# =========================================================
# FIM DE ARQUIVO: backend\routers\propriedades.py
# =========================================================