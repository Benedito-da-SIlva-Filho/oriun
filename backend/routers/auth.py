# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\auth.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-06-21 10:01 -03
# ATUALIZADO EM: 2026-11-16 11:45 -03
# VERSAO: 1.34.0
# v1.33.0: Sessao 122 (2026-11-12 17:40 -03) - Auditoria Etapa 2 (item 1): redirecionar_home() aceita chamada sem perfil (usa a sessao; sem sessao vai ao login). Antes dava erro 500 em ~220 chamadas. REVERSAO: .bak_antes_s122_etapa2.
# v1.31.0: Sessao 121 (2026-11-11 14:40 -03) - Destino aceito da pendencia da Home: Reidentificacao a enviar (URL_REIDENTIFICACAO_ENVIAR). REVERSAO: .bak_antes_s121_reidentificacao.
#     v1.32.0: Sessao 122 (2026-11-12 14:40 -03) - Auditoria Etapa 1: o logout ignora pedido que o navegador marca como vindo de outro site (Sec-Fetch-Site cross-site). REVERSAO: .bak_antes_s122_logout.
# v1.30.0: Sessao 111 (01/11/2026) - Venda e Morte (ver Diario de Bordo da Sessao 111). REVERSAO: arquivos .bak_antes_s111* ao lado.
#
# DESCRICAO:
#     Rotas de autenticacao do Orion.
#     - /                    -> redireciona para login ou home
#     - /login               -> tela e processamento do login
#     - /logout              -> encerra a sessao
#     - /consiste/home       -> painel Consiste (requer login)
#     - /certificadora/home  -> painel Certificadora (requer login)
#     - /produtor/home       -> painel Produtor (requer login)
#     - /produtor/selecionar-vinculo -> resolve qual Produtor/
#                              Propriedade usar numa acao (NOVO,
#                              v1.12.0 - P-036)
#     - /esqueci-senha       -> gera senha provisoria e envia por email
#     v1.0.0: Criacao do modulo.
#     v1.1.0: Adicionadas variaveis White Label no home.
#     v1.2.0: Adicionada rota esqueci-senha para CERTIFICADORA.
#     v1.3.0: Esqueci-senha reescrito — senha aleatoria + email.
#             Login verifica senha_provisoria apos autenticacao.
#     v1.4.0: Importacoes de Message e mail movidas para o topo.
#             Boa pratica — evita importacao dentro de try/except.
#     v1.5.0: Separacao de plataformas — cada perfil tem seu home.
#             Totais do banco passados dinamicamente para os homes.
#             Rota /home antiga removida.
#     v1.6.0: make_response no redirect para /trocar-senha —
#             impede navegador de registrar pagina no historico.
#     v1.7.0: Sessao 010 - Corrigidas referencias ao campo
#             renomeado no banco/models (certificadora_id ->
#             id_certificadora): usuario.certificadora_id e
#             filter_by(certificadora_id=...) em Propriedade.
#             A chave de sessao session['certificadora_id']
#             foi mantida como esta — e so uma variavel de
#             sessao, nao depende do nome da coluna no banco.
#     v1.8.0: Sessao 026 - Adicionado session['id_produtor'] no
#             login(), a partir de usuario.id_produtor. Lacuna
#             identificada ao construir a primeira rota de
#             movimento (GTA/Entrada/Compra) para o perfil
#             PRODUTOR/FAZENDA: o mecanismo de Schema-por-
#             Produtor (backend/utils/multitenant.py,
#             get_db_produtor()) depende de session['id_produtor']
#             para saber em qual schema entrar, e essa chave nunca
#             tinha sido gravada — o Multi-tenant foi decidido
#             (Sessao 17/018) depois deste modulo ja existir.
#             Sem FK id_produtor em Usuario para preencher (usuario
#             nao vinculado a nenhum Produtor), a chave grava None -
#             get_db_produtor() so e chamado dentro das rotas de
#             movimento do perfil PRODUTOR/FAZENDA, entao um usuario
#             sem produtor vinculado nunca chegaria la de qualquer
#             forma.
#     v1.9.0: Sessao de definicao do modelo de acesso do Produtor/
#             Equipe - Migracao para usuario_vinculo:
#             - Removido o perfil FAZENDA (redundante com PRODUTOR
#               + cargo do vinculo). redirecionar_home() e a
#               checagem de perfil em produtor_home() so aceitam
#               PRODUTOR agora.
#             - Removida a bifurcacao de template fazenda_home.html
#               - produtor_home() sempre usa produtor/produtor_home.html.
#               O arquivo fazenda_home.html fica orfao (sem uso),
#               nao foi apagado do disco nesta sessao.
#             - usuario.cargo e usuario.id_produtor deixam de ser
#               lidos diretamente do Usuario. Nova funcao auxiliar
#               buscar_vinculo_ativo() consulta usuario_vinculo
#               (data_fim IS NULL) para usuarios perfil PRODUTOR.
#               CONSISTE e CERTIFICADORA nao usam vinculo - seguem
#               sem essas chaves na sessao.
#             - login() bloqueia o acesso (mensagem de erro, sem
#               abrir sessao) se um usuario PRODUTOR nao tiver
#               nenhum vinculo ativo - rede de seguranca contra
#               inconsistencia de dados (cadastro sempre deve
#               nascer com vinculo, via modulo de Usuarios; isto
#               cobre o caso residual de um vinculo ser encerrado
#               sem um novo ser criado).
#             - buscar_vinculo_ativo() assume 1 vinculo ativo por
#               usuario (pega o primeiro se houver mais de um) -
#               a tela de selecao para usuarios com multiplos
#               vinculos simultaneos (ex.: colaborador atendendo
#               varias Propriedades/Produtores) fica para quando o
#               primeiro caso real aparecer (pendencia P-036).
#             - colunas usuarios.cargo e usuarios.id_produtor NAO
#               foram removidas do banco nesta migracao - so
#               deixaram de ser lidas/gravadas pelo codigo.
#     v1.10.0: Sessao 032 - P-040: produtor_home() passa a checar,
#             antes de renderizar o painel, se a Propriedade
#             vinculada ao Produtor (via PropriedadeProdutor) tem
#             cadastro_completo=False. Se tiver, redireciona
#             direto para propriedades.editar(id) (agora liberado
#             para o perfil PRODUTOR, ver propriedades.py v1.11.0
#             e _produtor_possui_propriedade()) em vez de mostrar
#             a Home - forca completar o pre-cadastro nascido pelo
#             Convite Publico antes de liberar o resto do sistema.
#             So se aplica a 1a Propriedade (decisao com Benedito:
#             da 2a em diante, o cadastro e feito pela Consiste,
#             ja nasce completo - nunca cai neste caso). Se o
#             Produtor nao tiver nenhuma Propriedade vinculada
#             (nao deveria acontecer, mas por seguranca), segue
#             normalmente para a Home sem travar.
#     v1.11.0: Sessao 034 (continuacao 9, 13/08/2026, 13:20 -03) -
#             Geracao inline de senha provisoria em esqueci_senha()
#             extraida para backend/utils/senha_helper.py,
#             funcao publica gerar_senha_provisoria() - a mesma
#             logica ja estava duplicada em convite.py e
#             produtores.py (Cenario 1, sessao anterior); com um 4o
#             ponto de uso surgindo (vitrine_visitantes.py, Cenario
#             2), Benedito decidiu extrair agora em vez de duplicar
#             de novo. Nenhuma mudanca de comportamento - mesmo
#             algoritmo exato. Imports random/string removidos
#             deste arquivo (nao usados em mais nenhum outro ponto).
#     v1.12.0: Sessao (26/08/2026, 15:23 -03) - Resolve a pendencia
#             P-036 (usuario com vinculo ativo em mais de um
#             Produtor simultaneamente - caso real: administrativo
#             que atende Maria Angelica E Sebastiao, ambos na
#             Fazenda Olho D'Agua). Espelha o padrao real do GERAS
#             (tela mostrada por Benedito: lista Propriedade+
#             Produtor, clique na linha inteira resolve os dois de
#             uma vez).
#
#             DECISAO DE ARQUITETURA (alinhada com Benedito): a
#             escolha NAO acontece no login, e NAO fica "grudada"
#             na sessao inteira - vale so para a acao em andamento
#             (mesmo espirito de resolucao de Propriedade ja usado
#             em GTA Manual/Consulta). Ao entrar noutra tela que
#             tambem precise resolver Produtor, o usuario escolhe
#             de novo se ainda houver mais de 1 vinculo.
#
#             Duas pecas novas:
#             (1) buscar_vinculos_ativos_usuario(db, id_usuario) -
#                 versao "todos", ao contrario de
#                 buscar_vinculo_ativo() (que so pega o primeiro).
#             (2) buscar_pares_propriedade_produtor(id_usuario) -
#                 monta a lista de pares Propriedade+Produtor
#                 disponiveis para o usuario (1 por vinculo ativo x
#                 Propriedade ativa vinculada aquele Produtor) - e
#                 o que telas como gta_manual.iniciar() e
#                 gta_consulta.iniciar() agora consultam para
#                 decidir se mostram a tela de selecao
#                 (produtor/selecionar_propriedade_produtor.html,
#                 template unico compartilhado, substitui os dois
#                 templates antigos e quase identicos
#                 gta_manual_selecionar_propriedade.html e
#                 gta_consulta_selecionar_propriedade.html) ou
#                 seguem direto (so 1 par).
#
#             Nova rota /produtor/selecionar-vinculo recebe a
#             escolha (id_produtor + id_propriedade + para onde
#             seguir), CONFERE DE NOVO no servidor que aquele par
#             realmente pertence ao usuario logado (nunca confia
#             so no que veio da URL), grava id_produtor E
#             usuario_cargo na sessao (o Cargo pode ser diferente
#             em cada vinculo - TITULAR num Produtor,
#             ADMINISTRATIVO noutro, por exemplo) e redireciona
#             para o destino informado. Protecao contra open
#             redirect: so aceita destino comecando com
#             "/produtor/".
#
#             buscar_vinculo_ativo() (v1.9.0) e mantida sem
#             mudancas - continua usada em login() para decidir um
#             id_produtor/cargo inicial na sessao (o primeiro
#             encontrado); as telas de acao que exigem um Produtor
#             especifico e que tem mais de 1 vinculo disponivel
#             agora resolvem de novo via selecionar-vinculo, entao
#             o valor inicial do login e so um "palpite de partida"
#             para quem tem 1 unico vinculo (o caso mais comum).
#     v1.13.0: Sessao 076 (21/09/2026, 10:00 -03) - produtor_home()
#             passa mostrar_navegacao=False ao template - a Home e
#             a UNICA tela que nao tem Voltar/Home (ja esta na
#             Home), diferente das outras 37 telas do sistema.
#             Variavel lida por produtor_topo.html (peca-mestra
#             nova do topo, reutilizada via {% include %} - Ideia
#             registrada na Sessao 057, retomada agora). Nenhuma
#             outra rota/logica deste arquivo foi alterada.
#     v1.14.0: Sessao 084 (02/10/2026, 19:00 -03) - ALERTA DOS 30 DIAS na Home
#             do Produtor (produtor_home): busca as Notificacoes de Nascimento
#             ainda NAO impressas que vencem em ate 5 dias (ou ja venceram) em
#             todas as Propriedades do usuario (backend/utils/alerta_prazo_
#             notificacao.py) e manda 'alertas_notificacao' ao template
#             (produtor_home.html v1.6.0). Qualquer falha na busca e ignorada
#             - o aviso nunca derruba a Home. Nenhuma outra mudanca.
#     v1.15.0: Sessao 085 (04/10/2026, 14:10 -03) - CARDS DO TOPO DA HOME com
#             numeros reais (backend/utils/home_resumo.py): Animais (estoque),
#             Entradas (alerta de Comunicados/Notificacoes pendentes) e
#             Liberados para abate. produtor_home() manda 'resumo' ao template
#             (produtor_home.html v1.7.0) e deixa de mandar total_animais,
#             total_entradas e total_saidas (eram placeholders fixos em 0; o
#             card Saidas foi descartado). Qualquer falha ao montar o resumo
#             vira resumo=None (a Home mostra "indisponivel", nunca cai).
#             Nenhuma outra mudanca neste arquivo.
#     v1.16.0: Sessao 089 (07/10/2026, 09:45 -03) - HOME NOVO em rota paralela:
#             nova rota /produtor/home-novo (produtor_home_novo()), que monta
#             os mesmos dados da Home atual (alerta dos 30 dias e resumo) e
#             abre produtor/produtor_home_novo.html. A Home atual
#             (produtor_home) NAO foi alterada: continua de pe como rede de
#             seguranca ate a troca definitiva. Corrigida tambem a mensagem de
#             carga do arquivo, que ainda dizia VERSAO 1.13.0.
#     v1.17.0: Sessao 089 (07/10/2026, 10:45 -03) - HOME NOVO, Etapa 2:
#             produtor_home_novo() passa a tratar a FAZENDA ESCOLHIDA. Quem
#             tem 1 so fazenda ja entra com ela escolhida; quem tem 2 ou mais
#             ve a visao do grupo (tabela de fazendas) e escolhe pela URL
#             (id_produtor + id_propriedade). O servidor CONFERE se o par
#             pertence ao usuario logado; se nao pertencer, volta a visao do
#             grupo. A escolha NAO e gravada na sessao (duas abas, duas
#             fazendas). Os 3 quadros mostram so a fazenda escolhida. O alerta
#             dos 30 dias continua para o grupo todo. Usa a funcao nova
#             montar_resumo_por_fazenda() de home_resumo.py v1.1.0. A Home
#             atual (produtor_home) continua sem mudanca.
#     v1.17.1: Sessao 089 (07/10/2026, 11:05 -03) - HOME NOVO: o quadro
#             Pendencias passa a contar tambem as Notificacoes com prazo de 30
#             dias vencendo ou vencido. Nova variavel alertas_quadro: os
#             alertas da fazenda escolhida (ou do grupo, sem escolha). A faixa
#             de alerta do topo continua com os alertas do grupo todo
#             (alertas_notificacao). Nenhuma outra mudanca.
#     v1.18.0: Sessao 089 (07/10/2026, 12:30 -03) - HOME NOVO: AUDITORIA ERAS.
#             Com uma fazenda escolhida (ou usuario de 1 so fazenda),
#             produtor_home_novo() manda 'auditoria_selecionada' ao template
#             (situacao da auditoria dessa fazenda, via
#             home_resumo.montar_auditoria_por_propriedade). Na visao do grupo,
#             a auditoria de cada fazenda ja vem em montar_resumo_por_fazenda.
#             Falha na busca vira "indisponivel", nunca derruba a Home. Exige
#             o blueprint auditoria_eras registrado (app.py v1.26.0). A Home
#             atual (produtor_home) continua sem mudanca.
#     v1.19.0: Sessao 089 (07/10/2026, 16:45 -03) - FAZENDA EM USO (faixa em
#             todas as telas, desenhada em produtor_topo.html v1.3.0). Nova
#             chave de sessao fazenda_ativa (id_produtor, id_propriedade, nome,
#             produtor_nome, uf), SO para quem tem 2 ou mais fazendas:
#               - produtor_home_novo(): ao escolher a fazenda (Selecionar) grava
#                 fazenda_ativa e tambem id_produtor + usuario_cargo (mesmo que o
#                 selecionar-vinculo faz), para a faixa e as telas concordarem;
#                 na visao do grupo (Todas as fazendas / Mudar Fazenda) e para
#                 quem tem so 1 fazenda, apaga fazenda_ativa. Esconde a faixa do
#                 topo na propria tela (ela ja tem a sua).
#               - selecionar_vinculo(): se a pessoa escolher outro par num
#                 modulo ainda nao migrado, a faixa passa a mostrar esse par (a
#                 faixa nunca mostra uma fazenda diferente da que a tela usa).
#               - produtor_home() (Home atual): so passa mostrar_faixa_fazenda
#                 falso (a Home atual mostra numeros do grupo todo). Nenhuma
#                 outra mudanca nela.
#             A escolha agora GRUDA na sessao ate Mudar Fazenda ou logout
#             (antes, a escolha dos modulos valia so para a acao).
#     v1.20.0: Sessao 089 (07/10/2026, 17:00 -03) - NOVA funcao
#             resolver_fazenda_em_uso(pares): devolve o par Propriedade+Produtor
#             da fazenda em uso (sessao fazenda_ativa), CONFERIDO contra os
#             pares do usuario logado, ou None (sem fazenda em uso, ou que nao
#             e dele). Os modulos usam no iniciar() para PULAR a tela
#             "Selecionar Propriedade". Piloto: brincagem_nascimento.py
#             v2.3.0. Nenhuma outra mudanca neste arquivo.
#     v1.21.0: Sessao 089 (07/10/2026, 17:58 -03) - SEM FAZENDA, SEM ENTRADA
#             (decisao de Benedito: a tela "Selecionar Propriedade" nao deve
#             existir em lugar nenhum). GUARDA CENTRAL
#             _guarda_fazenda_em_uso(): antes de qualquer pagina de ENTRADA de
#             modulo (endpoint terminado em "iniciar" - todos os modulos que
#             hoje mostram a selecao), se o usuario PRODUTOR tem 2 ou mais
#             fazendas e nao ha fazenda em uso valida, manda para o Home novo com
#             o aviso "Selecione uma fazenda para continuar". Com fazenda em uso,
#             ou 1 fazenda so, ou erro ao buscar os pares (na duvida nao
#             bloqueia), nada muda. Modulos que ainda nao pulam a lista (migrados
#             um a um) continuam mostrando-a SO quando ha fazenda em uso. O Home
#             novo recebe aviso_fazenda para mostrar o aviso e inibe os cartoes
#             de modulo enquanto nao houver fazenda escolhida.
#     v1.22.0: Sessao 090 (08/10/2026, 09:10 -03) - PAINEL DA FAZENDA SUBSTITUI O HOME:
#             o Home novo assume o endereco /produtor/home (login, botao Home,
#             menu e todo redirect para a Home passam a abrir o Painel novo).
#               - produtor_home(): agora e o Painel novo (antes era
#                 produtor_home_novo). Mesmos dados, mesmas conferencias.
#               - /produtor/home-novo: vira ALIAS que repassa para /produtor/home
#                 (mantem id_produtor/id_propriedade), para links antigos.
#               - Home ANTIGO: guardado em /produtor/home-antigo
#                 (produtor_home_antigo) ate o OK de Benedito para apagar.
#               - url_for('auth.produtor_home_novo') internos trocados por
#                 url_for('auth.produtor_home').
#             Nenhuma mudanca na regra da fazenda em uso, nos quadros ou nos
#             numeros.
#     v1.23.0: Sessao 097 (15/10/2026, 08:20 -03) - ACESSO FACIL (decisao de
#             Benedito): login e senha NAO diferenciam maiuscula de minuscula,
#             para todos os perfis.
#               - login(): o usuario e buscado ignorando a caixa (func.lower);
#                 a senha e conferida por conferir_senha() (senha_helper.py
#                 v1.1.0). Senha antiga com maiuscula que entra certa e
#                 regravada em minusculo (sessao propria, falha nao trava o
#                 login) - ninguem precisa resetar.
#               - esqueci_senha(): o login tambem e buscado ignorando a caixa.
#             Nenhuma outra mudanca neste arquivo.
#     v1.24.0: Sessao 097 (15/10/2026, 08:50 -03) - ESPACOS NAS PONTAS:
#             login(): o usuario digitado passa por normalizar_login()
#             (tira espacos do inicio e do fim); a senha ja e tratada em
#             conferir_senha() (senha_helper.py v1.2.0). Nenhuma outra
#             mudanca neste arquivo.
#     v1.25.0: Sessao 097 (15/10/2026, 10:05 -03) - PERMISSOES POR CARGO (Etapa 1):
#             produtor_home() passa aviso_permissao (?aviso=permissao) para a
#             Home mostrar "Seu cargo nao tem acesso a essa tela" quando o
#             porteiro (routers/permissoes.py) barra um endereco. Nenhuma outra
#             mudanca neste arquivo.
#     v1.26.0: Sessao 104 (23/10/2026, 11:50 -03) - LIMITE DE TENTATIVAS DE LOGIN: 5 senhas erradas seguidas bloqueiam o login por 15 minutos
#             (memoria do servidor; senha certa zera). REVERSAO: .bak_antes_s104g.
#     v1.27.0: Sessao 106 (26/10/2026, 11:50 -03) - HOME: DESTINO DA PENDENCIA (pedido do Benedito: clicar na fazenda dentro de uma
#             pendencia da visao do grupo deve abrir a TELA da pendencia, ja na fazenda escolhida, e nao so o Painel). produtor_home()
#             aceita o parametro opcional 'destino': depois de conferir o par (id_produtor + id_propriedade) e gravar a fazenda em uso,
#             redireciona para o destino SE ele for um dos 4 enderecos das pendencias (constantes URL_* de utils/home_resumo.py:
#             Hub de Brincagem, Gerar Comunicado, Imprimir Comunicado, Notificacao de Nascimento). Qualquer outro valor e ignorado e a
#             Home abre normal (nunca redireciona para endereco de fora). Sem 'destino', nada muda. REVERSAO: .bak_antes_s106g.
#     v1.28.0: Sessao 106 (26/10/2026, 12:05 -03) - o destino da GTA de Compra passa a ser o Hub de Entrada (URL_BRINCAR_COMPRA, em
#             utils/home_resumo.py v1.5.0), no lugar do Hub de Brincagem. REVERSAO: .bak_antes_s106j.
#     v1.29.0: Sessao 106 (26/10/2026, 18:10 -03) - a lista de destinos aceitos ganha URL_BRINCOS_ESQUECIDOS (pendencia de brincos lidos sem GTA). REVERSAO: .bak_antes_s106w.
#     v1.34.0: Sessao 128 (2026-11-16 11:45 -03) - AUDITORIA ETAPA 8a: /esqueci-senha (a) limite de 3 pedidos por hora por login; (b) mesma mensagem exista o login ou nao (nao revela quais logins existem); (c) a senha so e trocada se o e-mail sair (antes, falha no envio deixava a pessoa sem a senha antiga); (d) erros no log. REVERSAO: .bak_antes_etapa8a.
# =========================================================

from flask import Blueprint, render_template, request, redirect, url_for, session, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database import engine
from backend.models import Usuario, Certificadora, Propriedade, Produtor, UsuarioVinculo, PropriedadeProdutor
from backend.extensions import mail
from backend.utils.senha_helper import gerar_senha_provisoria, conferir_senha, normalizar_login
from flask_mail import Message
from sqlalchemy import func
import logging
import threading
import time
from sqlalchemy.orm import Session
from types import SimpleNamespace

print('AUTH.PY CARREGADO — VERSAO 1.22.0!')

auth = Blueprint('auth', __name__)

# -------------------------------------------------------
# Funcao auxiliar: redireciona para o home do perfil
# Usada no login e no index para centralizar a logica.
# -------------------------------------------------------
def redirecionar_home(perfil=None):
    # Etapa 2 (item 1): quase todas as telas chamam redirecionar_home() sem
    # informar o perfil. Sem argumento, usa o perfil da sessao; sem sessao, vai ao login.
    if perfil is None:
        perfil = session.get('usuario_perfil')
    if perfil == 'CONSISTE':
        return redirect('/consiste/home')
    elif perfil == 'CERTIFICADORA':
        return redirect('/certificadora/home')
    elif perfil == 'PRODUTOR':
        return redirect('/produtor/home')
    else:
        return redirect(url_for('auth.login'))

# -------------------------------------------------------
# Funcao auxiliar: busca o vinculo ATIVO do usuario em
# usuario_vinculo (data_fim IS NULL). So se aplica a perfil
# PRODUTOR - CONSISTE e CERTIFICADORA nao usam vinculo.
#
# Retorna o objeto UsuarioVinculo se encontrar, ou None se
# nao encontrar nenhum vinculo ativo (cadastro incompleto/
# inconsistente - bloqueado no login()).
#
# OBS (v1.12.0): usada em login() so para dar um id_produtor/
# cargo inicial na sessao (pega o primeiro vinculo encontrado).
# Para usuarios com mais de 1 vinculo ativo simultaneo, as telas
# de acao resolvem de novo via buscar_pares_propriedade_produtor()
# + /produtor/selecionar-vinculo (P-036, resolvida nesta versao).
# -------------------------------------------------------
def buscar_vinculo_ativo(db, id_usuario):
    return db.query(UsuarioVinculo).filter_by(
        id_usuario=id_usuario,
        data_fim=None
    ).first()


# -------------------------------------------------------
# Funcao auxiliar (v1.12.0, P-036): busca TODOS os vinculos
# ativos do usuario (data_fim IS NULL) - ao contrario de
# buscar_vinculo_ativo(), que so pega o primeiro.
# -------------------------------------------------------
def buscar_vinculos_ativos_usuario(db, id_usuario):
    return db.query(UsuarioVinculo).filter_by(
        id_usuario=id_usuario,
        data_fim=None
    ).all()


# -------------------------------------------------------
# Funcao auxiliar (v1.12.0, P-036): monta a lista de pares
# Propriedade+Produtor disponiveis para o usuario logado - 1
# entrada por Propriedade ativa vinculada a cada Produtor de um
# vinculo ativo do usuario. Espelha o padrao real do GERAS
# (tela mostrada por Benedito: mesma Propriedade pode aparecer
# mais de uma vez, uma por Produtor diferente).
#
# Cada par traz tambem o Cargo do vinculo (pode ser diferente
# por Produtor - TITULAR num, ADMINISTRATIVO noutro) - usado
# por /produtor/selecionar-vinculo para atualizar
# session['usuario_cargo'] corretamente ao trocar de contexto.
#
# Retorna lista de SimpleNamespace(id_produtor, produtor_nome,
# cargo, id_propriedade, propriedade_nome, municipio, uf).
# -------------------------------------------------------
def buscar_pares_propriedade_produtor(id_usuario):
    pares = []

    with Session(engine) as db:
        vinculos = buscar_vinculos_ativos_usuario(db, id_usuario)

        for vinculo in vinculos:
            produtor = db.get(Produtor, vinculo.id_produtor)
            if not produtor or not produtor.ativo:
                continue

            vinculos_propriedade = db.query(PropriedadeProdutor).filter_by(
                id_produtor=vinculo.id_produtor,
                data_fim=None
            ).all()

            for vinculo_propriedade in vinculos_propriedade:
                propriedade = db.get(Propriedade, vinculo_propriedade.id_propriedade)
                if not propriedade or not propriedade.ativo:
                    continue

                pares.append(SimpleNamespace(
                    id_produtor       = produtor.id,
                    produtor_nome     = produtor.nome,
                    cargo             = vinculo.cargo,
                    id_propriedade    = propriedade.id,
                    propriedade_nome  = propriedade.nome,
                    municipio         = propriedade.municipio,
                    uf                = propriedade.uf,
                ))

    pares.sort(key=lambda p: (p.propriedade_nome or '', p.produtor_nome or ''))
    return pares


# -------------------------------------------------------
# Funcao (v1.20.0): FAZENDA EM USO - devolve o par (Propriedade +
# Produtor) da fazenda escolhida no Home novo (session
# ['fazenda_ativa']), CONFERIDO contra a lista de pares do usuario
# logado (nunca confia so no que esta na sessao). Devolve None se
# nao ha fazenda em uso ou se ela nao e mais dele. Recebe os pares
# ja buscados pelo chamador (evita outra consulta). Os modulos usam
# no iniciar() para pular a tela de selecao de Propriedade.
# -------------------------------------------------------
def resolver_fazenda_em_uso(pares):
    fazenda = session.get('fazenda_ativa')
    if not fazenda:
        return None

    try:
        id_produtor    = int(fazenda['id_produtor'])
        id_propriedade = int(fazenda['id_propriedade'])
    except (KeyError, TypeError, ValueError):
        return None

    for par in pares or []:
        if int(par.id_propriedade) == id_propriedade and int(par.id_produtor) == id_produtor:
            return par
    return None


# -------------------------------------------------------
# GUARDA CENTRAL (v1.21.0): SEM FAZENDA EM USO, NAO HA ENTRADA NOS
# MODULOS. Roda antes de toda requisicao do sistema, mas so age nas
# paginas de ENTRADA de modulo (endpoint terminado em "iniciar":
# brincagem_nascimento.iniciar, pia_impressao.nascimento_iniciar etc. -
# as mesmas que hoje abrem a tela "Selecionar Propriedade"). Age so se o
# usuario e PRODUTOR, tem 2 ou mais fazendas e nao ha fazenda em uso
# valida (conferida contra os pares dele): manda para o Home novo com o
# aviso. Qualquer duvida (erro ao buscar os pares) NAO bloqueia - fica o
# comportamento de antes.
# -------------------------------------------------------
@auth.before_app_request
def _guarda_fazenda_em_uso():
    endpoint = request.endpoint or ''
    if not endpoint.endswith('iniciar'):
        return None
    if 'usuario_id' not in session or session.get('usuario_perfil') != 'PRODUTOR':
        return None

    try:
        pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    except Exception:
        return None

    if len(pares) < 2:
        return None
    if resolver_fazenda_em_uso(pares) is not None:
        return None

    return redirect(url_for('auth.produtor_home', aviso='fazenda'))


# -------------------------------------------------------
# Rota: / — redireciona para login ou home do perfil
# -------------------------------------------------------
@auth.route('/')
def index():
    if 'usuario_id' in session:
        return redirecionar_home(session.get('usuario_perfil'))
    return redirect(url_for('auth.login'))

# -------------------------------------------------------
# v1.26.0 (Sessao 104) - LIMITE DE TENTATIVAS DE LOGIN (decisao do Benedito):
# 5 senhas erradas seguidas para o MESMO login bloqueiam esse login por 15 minutos.
# Guardado na memoria do servidor (reiniciar o Orion zera). Vale tambem para login que
# nao existe (assim ninguem descobre quais logins existem). Senha certa zera a contagem.
# -------------------------------------------------------
MAX_TENTATIVAS_LOGIN = 5
BLOQUEIO_LOGIN_SEGUNDOS = 15 * 60
MENSAGEM_LOGIN_BLOQUEADO = 'Muitas tentativas. Tente novamente em 15 minutos.'
_tentativas_login = {}          # chave -> {'erros': n, 'bloqueado_ate': timestamp}
_trava_tentativas = threading.Lock()


def _chave_login(login_informado):
    return normalizar_login(login_informado or '').lower()


def _login_bloqueado(chave):
    with _trava_tentativas:
        reg = _tentativas_login.get(chave)
        if not reg:
            return False
        if reg['bloqueado_ate'] and reg['bloqueado_ate'] > time.time():
            return True
        if reg['bloqueado_ate']:        # bloqueio ja venceu: comeca do zero
            _tentativas_login.pop(chave, None)
        return False


def _registrar_erro_login(chave):
    with _trava_tentativas:
        reg = _tentativas_login.setdefault(chave, {'erros': 0, 'bloqueado_ate': 0})
        reg['erros'] += 1
        if reg['erros'] >= MAX_TENTATIVAS_LOGIN:
            reg['bloqueado_ate'] = time.time() + BLOQUEIO_LOGIN_SEGUNDOS
        if len(_tentativas_login) > 5000:   # limpeza simples para nao crescer sem fim
            agora = time.time()
            for k in [k for k, v in _tentativas_login.items() if v['bloqueado_ate'] and v['bloqueado_ate'] < agora]:
                _tentativas_login.pop(k, None)


def _zerar_erros_login(chave):
    with _trava_tentativas:
        _tentativas_login.pop(chave, None)


# -------------------------------------------------------
# Rota: /login — tela e processamento do login
# Apos autenticacao bem sucedida, verifica senha_provisoria.
# Se False (senha provisoria), redireciona para troca de senha.
# Se True (senha definitiva), redireciona para home do perfil.
# -------------------------------------------------------
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario_id' in session:
        return redirecionar_home(session.get('usuario_perfil'))

    erro = None

    if request.method == 'POST':
        login_informado = request.form.get('login')
        senha_informada = request.form.get('senha')

        chave_login = _chave_login(login_informado)   # v1.26.0
        if _login_bloqueado(chave_login):
            return render_template('auth/login.html', erro=MENSAGEM_LOGIN_BLOQUEADO)

        with Session(engine) as db:
            # v1.23.0: login ignora maiuscula/minuscula; senha idem
            # (conferir_senha). Ver senha_helper.py v1.1.0.
            usuario = db.query(Usuario).filter(
                func.lower(Usuario.login) == normalizar_login(login_informado).lower(),
                Usuario.ativo == True
            ).first()

            senha_ok, novo_hash_senha = False, None
            if usuario:
                senha_ok, novo_hash_senha = conferir_senha(usuario.senha, senha_informada)

            if usuario and senha_ok:
                _zerar_erros_login(chave_login)   # v1.26.0

                # Senha antiga (com maiuscula) que entrou certa: regrava em
                # minusculo, em sessao propria (nao mexe no objeto usuario
                # desta sessao). Falha aqui nunca impede o login.
                if novo_hash_senha:
                    try:
                        with Session(engine) as db_hash:
                            u_hash = db_hash.get(Usuario, usuario.id)
                            u_hash.senha = novo_hash_senha
                            db_hash.commit()
                    except Exception:
                        pass

                # Perfil PRODUTOR depende de vinculo ativo em
                # usuario_vinculo - CONSISTE e CERTIFICADORA nao
                # usam vinculo, seguem direto.
                vinculo = None
                if usuario.perfil == 'PRODUTOR':
                    vinculo = buscar_vinculo_ativo(db, usuario.id)

                    if not vinculo:
                        erro = 'Seu acesso está sem vínculo ativo com nenhum Produtor. Contate o administrador.'
                        return render_template('auth/login.html', erro=erro)

                # Carrega dados do usuario na sessao
                session['usuario_id']       = usuario.id
                session['usuario_nome']     = usuario.nome
                session['usuario_perfil']   = usuario.perfil
                session['certificadora_id'] = usuario.id_certificadora
                session['cor_primaria']     = '#D4370A'
                session['nome_sistema']     = 'Orion SISBOV'

                # So grava cargo/id_produtor na sessao se houver
                # vinculo (perfil PRODUTOR) - CONSISTE/CERTIFICADORA
                # ficam sem essas chaves na sessao (nao se aplicam).
                #
                # v1.12.0: se o usuario tiver mais de 1 vinculo
                # ativo (P-036), este e so um valor de partida - as
                # telas de acao que precisarem de um Produtor
                # especifico vao resolver de novo via
                # /produtor/selecionar-vinculo quando necessario.
                if vinculo:
                    session['usuario_cargo'] = vinculo.cargo
                    session['id_produtor']   = vinculo.id_produtor

                # Verifica se usuario esta com senha provisoria
                # False = senha provisoria — obriga troca antes de acessar o home
                if not usuario.senha_provisoria:
                    response = make_response(redirect(url_for('usuarios.trocar_senha')))
                    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
                    response.headers['Pragma'] = 'no-cache'
                    return response

                # True = senha definitiva — redireciona para home do perfil
                return redirecionar_home(usuario.perfil)

            else:
                _registrar_erro_login(chave_login)   # v1.26.0
                if _login_bloqueado(chave_login):
                    erro = MENSAGEM_LOGIN_BLOQUEADO
                else:
                    erro = 'Login ou senha incorretos!'

    return render_template('auth/login.html', erro=erro)

# -------------------------------------------------------
# Rota: /logout — encerra a sessao
# -------------------------------------------------------
@auth.route('/logout')
def logout():
    # v1.32.0 - Auditoria Etapa 1: se o navegador avisa que o pedido veio de OUTRO site (link/imagem de fora), nao desloga
    if request.headers.get('Sec-Fetch-Site') == 'cross-site':
        return redirect(url_for('auth.index'))
    session.clear()
    return redirect(url_for('auth.login'))

# -------------------------------------------------------
# Rota: /consiste/home — painel da plataforma Consiste
# Busca totais do banco para exibir nos cards.
# Requer login e perfil CONSISTE.
# -------------------------------------------------------
@auth.route('/consiste/home')
def consiste_home():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CONSISTE':
        return redirecionar_home(session.get('usuario_perfil'))

    with Session(engine) as db:
        total_certificadoras = db.query(Certificadora).filter_by(ativo=True).count()
        total_propriedades   = db.query(Propriedade).filter_by(ativo=True).count()
        total_produtores     = db.query(Produtor).filter_by(ativo=True).count()
        total_animais        = 0  # modulo de animais ainda nao implementado

    return render_template('consiste/consiste_home.html',
        usuario_nome         = session.get('usuario_nome'),
        usuario_perfil       = session.get('usuario_perfil'),
        cor_primaria         = session.get('cor_primaria', '#D4370A'),
        nome_sistema         = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo           = 'home',
        total_certificadoras = total_certificadoras,
        total_propriedades   = total_propriedades,
        total_produtores     = total_produtores,
        total_animais        = total_animais
    )

# -------------------------------------------------------
# Rota: /certificadora/home — painel da plataforma Certificadora
# Busca totais apenas da certificadora logada.
# Requer login e perfil CERTIFICADORA.
# -------------------------------------------------------
@auth.route('/certificadora/home')
def certificadora_home():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'CERTIFICADORA':
        return redirecionar_home(session.get('usuario_perfil'))

    cert_id = session.get('certificadora_id')

    with Session(engine) as db:
        total_propriedades = db.query(Propriedade).filter_by(
            id_certificadora=cert_id, ativo=True
        ).count()
        total_produtores   = 0
        total_pendentes    = 0  # modulo de comunicados ainda nao implementado
        total_animais      = 0  # modulo de animais ainda nao implementado

    return render_template('certificadora/certificadora_home.html',
        usuario_nome       = session.get('usuario_nome'),
        usuario_perfil     = session.get('usuario_perfil'),
        cor_primaria       = session.get('cor_primaria', '#D4370A'),
        nome_sistema       = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo         = 'home',
        total_propriedades = total_propriedades,
        total_produtores   = total_produtores,
        total_pendentes    = total_pendentes,
        total_animais      = total_animais
    )

# -------------------------------------------------------
# Rota: /produtor/home — painel da plataforma Produtor
# Busca totais da propriedade do usuario logado.
# Requer login e perfil PRODUTOR.
#
# P-040 (Sessao 032): antes de renderizar o painel, confere se
# a Propriedade vinculada tem cadastro_completo=False (nasceu
# pelo Convite Publico, com campos em placeholder). Se sim,
# redireciona para completar o cadastro em vez de mostrar a
# Home. So se aplica a 1a Propriedade - da 2a em diante, quem
# cadastra e a Consiste, ja nasce completa (nunca cai aqui).
#
# v1.13.0 (Sessao 076): passa mostrar_navegacao=False ao
# template - a Home e a UNICA tela que nao tem Voltar/Home (ja
# esta na Home), diferente das outras 37 telas do sistema. Essa
# variavel e lida por produtor_topo.html (peca-mestra nova do
# topo, reutilizada via include - ver Regras.txt, Ideia
# registrada na Sessao 057, retomada agora).
# -------------------------------------------------------
# v1.22.0 - HOME ANTIGO: saiu do endereco /produtor/home (agora e o Painel novo)
# e fica guardado em /produtor/home-antigo ate o OK de Benedito para apagar.
@auth.route('/produtor/home-antigo')
def produtor_home_antigo():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'PRODUTOR':
        return redirecionar_home(session.get('usuario_perfil'))

    with Session(engine) as db:
        # P-040: checa se ha Propriedade vinculada com cadastro
        # ainda incompleto (pre-cadastro do Convite Publico).
        vinculo_propriedade = db.query(PropriedadeProdutor).filter_by(
            id_produtor=session.get('id_produtor')
        ).first()

        if vinculo_propriedade:
            propriedade_vinculada = db.get(Propriedade, vinculo_propriedade.id_propriedade)
            if propriedade_vinculada and not propriedade_vinculada.cadastro_completo:
                return redirect(url_for('propriedades.editar', id=propriedade_vinculada.id))

    # v1.14.0 - alerta dos 30 dias da Notificacao de Nascimento.
    alertas_notificacao = []
    try:
        from backend.utils.alerta_prazo_notificacao import buscar_alertas_notificacao
        alertas_notificacao = buscar_alertas_notificacao(
            buscar_pares_propriedade_produtor(session['usuario_id'])
        )
    except Exception:
        alertas_notificacao = []

    # v1.15.0 - numeros reais dos cards do topo da Home.
    resumo = None
    try:
        from backend.utils.home_resumo import montar_resumo_home
        resumo = montar_resumo_home(
            buscar_pares_propriedade_produtor(session['usuario_id'])
        )
    except Exception:
        resumo = None

    return render_template('produtor/produtor_home.html',
        usuario_nome       = session.get('usuario_nome'),
        usuario_perfil     = session.get('usuario_perfil'),
        cor_primaria       = session.get('cor_primaria', '#D4370A'),
        nome_sistema       = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo         = 'home',
        mostrar_navegacao  = False,
        alertas_notificacao = alertas_notificacao,   # v1.14.0
        resumo             = resumo,                 # v1.15.0
        mostrar_faixa_fazenda = False,               # v1.19.0
    )

# -------------------------------------------------------
# Rota: /produtor/home-novo — HOME NOVO (v1.16.0, Sessao 089)
# Rota PARALELA: mesmos dados da Home atual (produtor_home),
# so muda o template (produtor/produtor_home_novo.html). Mesmas
# conferencias de acesso e do cadastro incompleto (P-040).
# Quando o Home novo substituir o atual, esta rota assume o
# endereco /produtor/home e a antiga sai.
# v1.17.0 (Etapa 2): trata a fazenda escolhida - ver changelog
# no topo do arquivo. Parametros opcionais na URL: id_produtor e
# id_propriedade (os dois juntos; conferidos contra os pares do
# usuario logado).
# -------------------------------------------------------
@auth.route('/produtor/home')
def produtor_home():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'PRODUTOR':
        return redirecionar_home(session.get('usuario_perfil'))

    with Session(engine) as db:
        # P-040: Propriedade com cadastro incompleto vai completar
        # o cadastro antes de ver a Home.
        vinculo_propriedade = db.query(PropriedadeProdutor).filter_by(
            id_produtor=session.get('id_produtor')
        ).first()

        if vinculo_propriedade:
            propriedade_vinculada = db.get(Propriedade, vinculo_propriedade.id_propriedade)
            if propriedade_vinculada and not propriedade_vinculada.cadastro_completo:
                return redirect(url_for('propriedades.editar', id=propriedade_vinculada.id))

    # v1.17.0 - fazendas (pares Propriedade+Produtor) do usuario,
    # buscadas UMA vez e reaproveitadas abaixo.
    try:
        pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    except Exception:
        pares = []
    multiplas_fazendas = len(pares) > 1

    # v1.17.0 - fazenda escolhida. 1 so fazenda: ja vem escolhida. 2 ou mais:
    # vem da URL (id_produtor + id_propriedade) e o servidor CONFERE se o par
    # realmente e do usuario logado (nunca confia so no id vindo da URL). Par
    # que nao e dele (ou so um dos dois ids): volta a visao do grupo.
    selecionado = None
    if len(pares) == 1:
        selecionado = pares[0]
    else:
        id_propriedade_url = request.args.get('id_propriedade', type=int)
        id_produtor_url = request.args.get('id_produtor', type=int)
        if id_propriedade_url is not None or id_produtor_url is not None:
            for par in pares:
                if int(par.id_propriedade) == id_propriedade_url and int(par.id_produtor) == id_produtor_url:
                    selecionado = par
                    break
            if selecionado is None:
                return redirect(url_for('auth.produtor_home'))

    # Alerta dos 30 dias da Notificacao de Nascimento (falha e ignorada).
    # Vale para o grupo todo, mesmo com uma fazenda escolhida.
    alertas_notificacao = []
    try:
        from backend.utils.alerta_prazo_notificacao import buscar_alertas_notificacao
        alertas_notificacao = buscar_alertas_notificacao(pares)
    except Exception:
        alertas_notificacao = []

    # v1.17.1 - alertas que entram no QUADRO Pendencias: so os da fazenda
    # escolhida (quando ha 2 ou mais fazendas) ou os do grupo, sem escolha.
    alertas_quadro = alertas_notificacao
    if selecionado is not None and multiplas_fazendas:
        try:
            from backend.utils.alerta_prazo_notificacao import buscar_alertas_notificacao
            alertas_quadro = buscar_alertas_notificacao([selecionado])
        except Exception:
            alertas_quadro = []

    # Numeros dos quadros do topo: so da fazenda escolhida, ou do grupo
    # todo (falha vira "indisponivel").
    resumo = None
    try:
        from backend.utils.home_resumo import montar_resumo_home
        if selecionado is not None:
            resumo = montar_resumo_home([selecionado])
        else:
            resumo = montar_resumo_home(pares)
    except Exception:
        resumo = None

    # v1.18.0 - auditoria ERAS da fazenda escolhida (faixa do topo).
    auditoria_selecionada = None
    if selecionado is not None:
        try:
            from backend.utils.home_resumo import montar_auditoria_por_propriedade
            auditoria_selecionada = montar_auditoria_por_propriedade(
                [selecionado.id_propriedade]
            ).get(int(selecionado.id_propriedade))
        except Exception:
            auditoria_selecionada = {'erro': True}

    # Tabela de fazendas (so na visao do grupo, com 2 ou mais fazendas).
    # Falha aqui nao derruba a Home: a tela avisa que a lista esta indisponivel.
    fazendas = None
    if multiplas_fazendas and selecionado is None:
        try:
            from backend.utils.home_resumo import montar_resumo_por_fazenda
            fazendas = montar_resumo_por_fazenda(pares)
        except Exception:
            fazendas = None

    # v1.19.0 - FAZENDA EM USO. So para quem tem 2 ou mais fazendas e
    # escolheu uma (selecionado ja foi conferido contra os pares do usuario).
    # Grava tambem id_produtor + usuario_cargo, como o selecionar-vinculo, para
    # as telas internas trabalharem no mesmo Produtor da faixa. Visao do grupo
    # (ou 1 so fazenda): apaga a fazenda em uso.
    if multiplas_fazendas and selecionado is not None:
        session['fazenda_ativa'] = {
            'id_produtor':    int(selecionado.id_produtor),
            'id_propriedade': int(selecionado.id_propriedade),
            'nome':           selecionado.propriedade_nome or '',
            'produtor_nome':  selecionado.produtor_nome or '',
            'uf':             selecionado.uf or '',
        }
        session['id_produtor']   = int(selecionado.id_produtor)
        session['usuario_cargo'] = selecionado.cargo
    else:
        session.pop('fazenda_ativa', None)

    # v1.27.0 - DESTINO da pendencia: com a fazenda ja escolhida e gravada acima, abre direto a tela da
    # pendencia. So os 4 enderecos das pendencias da Home sao aceitos; qualquer outro valor e ignorado.
    destino = request.args.get('destino', '')
    if destino and multiplas_fazendas and selecionado is not None:
        from backend.utils.home_resumo import (
            URL_BRINCAR_COMPRA, URL_GERAR_COMUNICADO, URL_IMPRIMIR_COMUNICADO, URL_NOTIFICACAO, URL_BRINCOS_ESQUECIDOS, URL_GERAR_NOTIFICACAO_MORTE, URL_REIDENTIFICACAO_ENVIAR,
        )
        if destino in (URL_BRINCAR_COMPRA, URL_GERAR_COMUNICADO, URL_IMPRIMIR_COMUNICADO, URL_NOTIFICACAO, URL_BRINCOS_ESQUECIDOS, URL_GERAR_NOTIFICACAO_MORTE, URL_REIDENTIFICACAO_ENVIAR):
            return redirect(destino)

    return render_template('produtor/produtor_home_novo.html',
        usuario_nome       = session.get('usuario_nome'),
        usuario_perfil     = session.get('usuario_perfil'),
        cor_primaria       = session.get('cor_primaria', '#D4370A'),
        nome_sistema       = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo         = 'home',
        mostrar_navegacao  = False,
        alertas_notificacao = alertas_notificacao,
        alertas_quadro     = alertas_quadro,       # v1.17.1
        resumo             = resumo,
        selecionado        = selecionado,          # v1.17.0
        multiplas_fazendas = multiplas_fazendas,   # v1.17.0
        fazendas           = fazendas,             # v1.17.0
        auditoria_selecionada = auditoria_selecionada,   # v1.18.0
        mostrar_faixa_fazenda = False,                   # v1.19.0 (a tela ja tem a faixa propria)
        aviso_fazenda      = (request.args.get('aviso') == 'fazenda'),   # v1.21.0
        aviso_permissao    = (request.args.get('aviso') == 'permissao'), # v1.25.0
    )



# -------------------------------------------------------
# Alias (v1.22.0): /produtor/home-novo continua existindo para links e
# favoritos antigos - repassa tudo (inclusive id_produtor/id_propriedade) para
# o endereco definitivo /produtor/home.
# -------------------------------------------------------
@auth.route('/produtor/home-novo')
def produtor_home_novo():
    return redirect(url_for('auth.produtor_home', **request.args.to_dict(flat=True)))


# -------------------------------------------------------
# Rota: /produtor/selecionar-vinculo — (NOVO, v1.12.0, P-036)
# Recebe a escolha feita na tela
# produtor/selecionar_propriedade_produtor.html (clique numa
# linha Propriedade+Produtor), CONFERE DE NOVO no servidor que
# aquele par realmente pertence ao usuario logado (nunca confia
# so no id vindo da URL), grava id_produtor + usuario_cargo na
# sessao (o Cargo pode variar por Produtor) e redireciona para
# o destino informado, ja com o id_propriedade escolhido anexado.
#
# Parametros esperados na querystring:
#   id_produtor        - id do Produtor escolhido
#   id_propriedade     - id da Propriedade escolhida
#   proximo            - path de destino (DEVE comecar com
#                         "/produtor/" - protecao contra open
#                         redirect)
#   campo_propriedade  - nome do parametro de querystring que o
#                         destino espera para receber o
#                         id_propriedade (cada fluxo usa um nome
#                         diferente: id_propriedade_interna no
#                         GTA Manual, id_propriedade na Consulta)
#
# A escolha vale so para esta acao - nao "gruda" na sessao alem
# disso (decisao de Benedito, 26/08/2026): a proxima tela que
# precisar de Produtor volta a perguntar, se ainda houver mais
# de 1 vinculo.
# -------------------------------------------------------
@auth.route('/produtor/selecionar-vinculo')
def selecionar_vinculo():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') != 'PRODUTOR':
        return redirecionar_home(session.get('usuario_perfil'))

    id_produtor_str    = request.args.get('id_produtor', '')
    id_propriedade_str = request.args.get('id_propriedade', '')
    proximo             = request.args.get('proximo', '')
    campo_propriedade   = request.args.get('campo_propriedade', 'id_propriedade')

    # Protecao contra open redirect - so aceita destino dentro do
    # proprio modulo Produtor.
    if not proximo.startswith('/produtor/'):
        return redirect(url_for('auth.produtor_home'))

    if not id_produtor_str or not id_propriedade_str:
        return redirect(url_for('auth.produtor_home'))

    id_produtor    = int(id_produtor_str)
    id_propriedade = int(id_propriedade_str)

    fazenda_escolhida = None     # v1.19.0 - dados da faixa Fazenda em uso

    with Session(engine) as db:
        # Seguranca: confere que o par escolhido REALMENTE
        # pertence ao usuario logado - nunca confia no id vindo da
        # URL sem checar (protege contra id manipulado
        # manualmente).
        vinculo = db.query(UsuarioVinculo).filter_by(
            id_usuario  = session['usuario_id'],
            id_produtor = id_produtor,
            data_fim    = None
        ).first()

        if not vinculo:
            return redirect(url_for('auth.produtor_home'))

        vinculo_propriedade = db.query(PropriedadeProdutor).filter_by(
            id_produtor    = id_produtor,
            id_propriedade = id_propriedade,
            data_fim       = None
        ).first()

        if not vinculo_propriedade:
            return redirect(url_for('auth.produtor_home'))

        session['id_produtor']   = id_produtor
        session['usuario_cargo'] = vinculo.cargo

        # v1.19.0 - guarda a escolha para a faixa Fazenda em uso.
        produtor_escolhido    = db.get(Produtor, id_produtor)
        propriedade_escolhida = db.get(Propriedade, id_propriedade)
        if produtor_escolhido and propriedade_escolhida:
            fazenda_escolhida = {
                'id_produtor':    id_produtor,
                'id_propriedade': id_propriedade,
                'nome':           propriedade_escolhida.nome or '',
                'produtor_nome':  produtor_escolhido.nome or '',
                'uf':             propriedade_escolhida.uf or '',
            }

    # v1.19.0 - a faixa so existe para quem tem 2 ou mais fazendas; ela passa
    # a mostrar o par que a pessoa acabou de escolher neste modulo.
    try:
        tem_varias_fazendas = len(buscar_pares_propriedade_produtor(session['usuario_id'])) > 1
    except Exception:
        tem_varias_fazendas = False
    if tem_varias_fazendas and fazenda_escolhida:
        session['fazenda_ativa'] = fazenda_escolhida
    else:
        session.pop('fazenda_ativa', None)

    separador = '&' if '?' in proximo else '?'
    return redirect(f'{proximo}{separador}{campo_propriedade}={id_propriedade}')


# -------------------------------------------------------
# Rota: /esqueci-senha — gera senha provisoria e envia por email
# Recebe apenas o login. Busca email no banco automaticamente.
# Gera senha aleatoria de 5 caracteres (2 maiusculas + 2 numeros
# + 1 minuscula embaralhados, via gerar_senha_provisoria() -
# backend/utils/senha_helper.py, v1.11.0) e envia por email.
# Marca senha_provisoria = False para obrigar troca no proximo login.
# -------------------------------------------------------
# v1.34.0 - limite de pedidos de senha provisoria (por login, em memoria como o limite do login)
logger = logging.getLogger(__name__)
MAX_PEDIDOS_SENHA = 3
JANELA_PEDIDOS_SENHA = 3600
MENSAGEM_PEDIDOS_SENHA = 'Muitos pedidos de senha. Tente novamente em 1 hora.'
MENSAGEM_SENHA_PEDIDA = ('Se o login existir e tiver e-mail cadastrado, enviamos uma senha provisória. '
                         'Confira a caixa de entrada e o spam. Se não chegar em alguns minutos, fale com o administrador da fazenda.')
_pedidos_senha = {}
_trava_pedidos_senha = threading.Lock()


def _pedido_senha_liberado(chave):
    agora = time.time()
    with _trava_pedidos_senha:
        marcas = [t for t in _pedidos_senha.get(chave, []) if agora - t < JANELA_PEDIDOS_SENHA]
        if len(marcas) >= MAX_PEDIDOS_SENHA:
            _pedidos_senha[chave] = marcas
            return False
        marcas.append(agora)
        _pedidos_senha[chave] = marcas
        if len(_pedidos_senha) > 5000:   # limpeza simples para nao crescer sem fim
            for k in [k for k, v in _pedidos_senha.items() if not v or agora - v[-1] >= JANELA_PEDIDOS_SENHA]:
                _pedidos_senha.pop(k, None)
        return True


@auth.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    mensagem = None
    erro     = None

    if request.method == 'POST':
        login_informado = request.form.get('login', '').strip()
        chave = login_informado.lower()[:50]

        if not chave:
            erro = 'Informe o seu login.'

        elif not _pedido_senha_liberado(chave):
            erro = MENSAGEM_PEDIDOS_SENHA

        else:
            with Session(engine) as db:
                usuario = db.query(Usuario).filter(
                    func.lower(Usuario.login) == chave,
                    Usuario.ativo == True
                ).first()

                if usuario and usuario.email:
                    # v1.11.0: geracao movida para o helper compartilhado
                    senha_provisoria = gerar_senha_provisoria()
                    usuario.senha            = generate_password_hash(senha_provisoria)
                    usuario.senha_provisoria = False   # False = obriga trocar a senha no proximo login

                    # v1.34.0: so grava a senha nova se o e-mail sair
                    try:
                        msg = Message(
                            subject    = 'Orion SISBOV — Sua senha provisoria',
                            sender     = 'noreply.consisteti@gmail.com',
                            recipients = [usuario.email]
                        )
                        msg.body = (
                            f'Ola, {usuario.nome}!\n\n'
                            f'Sua senha provisoria de acesso ao Orion SISBOV e:\n\n'
                            f'   {senha_provisoria}\n\n'
                            f'Acesse o sistema com seu login e esta senha.\n'
                            f'Voce sera redirecionado para criar uma nova senha imediatamente.\n\n'
                            f'Se nao foi voce quem solicitou, contate o administrador.\n\n'
                            f'Atenciosamente,\n'
                            f'Orion SISBOV — Consiste Informatica'
                        )
                        mail.send(msg)
                        db.commit()
                    except Exception:
                        db.rollback()
                        logger.exception('Esqueci-senha: falha ao enviar o e-mail (login %s)', chave)

            # mesma resposta exista o login, tenha e-mail ou nao (nao revela quais logins existem)
            mensagem = MENSAGEM_SENHA_PEDIDA

    return render_template('auth/auth_esqueci_senha.html',
        mensagem = mensagem,
        erro     = erro
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\auth.py
# =========================================================