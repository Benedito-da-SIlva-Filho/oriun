# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\hub_entrada_agrupado.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-06 11:25 -03
# ATUALIZADO EM: 2026-11-18 20:30 -03
# VERSAO: 1.30.1
# v1.30.1: Sessao 132 (2026-11-18 20:20 -03) - BND/Fazenda entra na lista da aba Consultas e Correcoes + texto curto. REVERSAO: .bak_antes_s132_aba.
# v1.30.0: Sessao 132 (2026-11-18 20:30 -03) - Hub de Entrada, Consultas e correcoes: card BND/Fazenda (bnd_fazenda.iniciar). REVERSAO: .bak_antes_s132_bnd.
# v1.29.0: Sessao 129 (2026-11-17 11:30 -03) - Hub de Pesos ganha o card Relatorios de Pesagem (grupo Conferencia). REVERSAO: .bak_antes_s129_pesos_relatorios.
# v1.28.1: Sessao 121 (2026-11-11 21:25 -03) - Aba Comunicados abre direto com os 4 cards (Gerar Comunicado, Impressao, Reimpressao, PIA), um clique a menos. Reaproveita os cards do sub-hub entrada-comunicados.
# v1.28.0: Sessao 121 (2026-11-11 21:05 -03) - Hub de Entrada em ABAS (decisao do Benedito): Entrada de Animais (Nascimento/Desmame, Compras/GTA, Brincagem Sequencial, Vincular GTA/Brincagem, Racas da Fazenda), Linkagem, Reidentificacao, Consultas e Correcoes, Comunicados (1 card). Por que: 16 cards em grupos empilhados exigiam 2 rolagens. Os grupos continuam em HUBS_NOVOS (usados pelas permissoes e pelo Hub antigo). REVERSAO: .bak_antes_s121_hub_abas.
# v1.27.1: Sessao 121 (2026-11-11 12:20 -03) - Os 3 cards da Reidentificacao ficam em grupo proprio (mesma linha).
# v1.27.0: Sessao 121 (2026-11-11 14:20 -03) - Hub de Entrada, Consultas e correcoes: cards Reidentificacao, Consulta da Reidentificacao e Inconformidades da Reidentificacao. REVERSAO: .bak_antes_s121_reidentificacao.
# v1.26.0: Sessao 120 (2026-11-10 21:50 -03) - Hub de Entrada, Consultas e correcoes: cards Consulta da Linkagem (com PDF) e Inconformidades da Linkagem. REVERSAO: .bak_antes_s120_pacote2.
# v1.25.0: Sessao 120 (2026-11-10 18:40 -03) - Hub de Entrada, grupo Consultas e correcoes: novo card 'Linkagem RFID e Brinco' (linkagem_rfid.iniciar). REVERSAO: .bak_antes_s120_linkagem.
# v1.24.0: Sessao 120 (2026-11-10 13:58 -03) - Card Consulta GTA sai da aba Consultas e correcoes (ficava repetido); fica so na aba GTAs. REVERSAO: .bak_antes_s120_consulta_gta.
# v1.23.0: Sessao 120 (2026-11-10 14:05 -03) - Cards Impressao e Reimpressao de cada aba levam o tipo e o titulo mostra o tipo (ex.: Impressao Comunicado de Saida - Venda). REVERSAO: .bak_antes_s120_imp_tipo.
# v1.22.0: Sessao 120 (2026-11-10 12:43 -03) - Card Vincular GTA / Embarque BLOQUEADO na aba quando nao ha leitura a vincular (texto: Nada a vincular - siga para Gerar Comunicado); aviso de espera no card Operacoes Recentes; card Reimpressao Comunicado de Saida leva o tipo da aba. REVERSAO: .bak_antes_s120_hub_py.
# v1.21.2: Sessao 118 (2026-11-08 14:40 -03) - Vincular de cada aba leva o tipo. REVERSAO: .bak_antes_s118_raca
# v1.21.1: Sessao 118 (2026-11-08 13:30 -03) - Card Relatorio de Embarque sai da aba Consultas e correcoes. REVERSAO: .bak_antes_s118_pedido
# v1.21.0: Sessao 118 (2026-11-08 13:00 -03) - Abas de saida: some o passo "Cadastrar a GTA" de Abate/Transferencia/Venda; entra o passo "Consulta Embarque" (filtrada pelo tipo da aba, parametro qs); Vincular so no fluxo de cada aba (sai da aba GTAs); Posse ganha o card "DTA de Alteracao de Posse" direto no formulario (rota nova-posse). Motivo: a Geane se perdeu na hora de pedir a GTA. REVERSAO: .bak_antes_s118_hub.
# v1.20.1: Sessao 115 (2026-11-05 20:55 -03) - Abas: cards quadrados com texto curto de orientacao (TEXTOS_CURTOS, por titulo; a aba pode trocar o texto em 'textos'), passos sempre na mesma linha. REVERSAO: .bak_antes_s115_abas2.
# v1.20.0: Sessao 115 (2026-11-05 20:45 -03) - Hub de Saidas em ABAS (GTAs, Abate, Transferencia, Morte, Venda, Alteracao de Posse, Consultas), passos em ordem de trabalho; cards inalterados. REVERSAO: .bak_antes_s115_abas.
#
# DESCRICAO:
#     Hub de Entrada NOVO (layout agrupado por intencao), em rotas
#     PARALELAS ao Hub de Entrada atual. O Hub atual
#     (/produtor/hub/entrada, motor generico em hubs.py) NAO e
#     tocado - continua de pe como rede de seguranca ate o novo
#     ser validado por Benedito e pelos usuarios.
#
#     Telas deste modulo (dicionario HUBS_NOVOS, chave = slug da
#     URL /produtor/hub-novo/<slug>):
#       - 'entrada'            Hub de Entrada, 4 grupos, 10 cards.
#       - 'entrada-nascimento' Nascimento / Desmame (sub-hub), 3
#                              grupos, 5 cards.
#       - 'entrada-comunicados' Comunicados de Entrada (sub-hub), 2
#                              grupos, 4 cards.
#       - 'brincagem'          Hub de Brincagem, 2 grupos, 6 cards.
#       - 'brincos'            Hub de Brincos, 3 grupos, 8 cards.
#       - 'utilitarios'        Hub de Utilitarios, 1 grupo, 2 cards.
#       - 'inventario'         Hub de Inventario, 1 grupo, 1 card.
#     Todas usam o MESMO template
#     (produtor/hub_entrada_agrupado.html). Slug desconhecido
#     redireciona para a Home (nunca 404 feio para o usuario -
#     mesmo principio do hubs.py).
#
#     Diferencas em relacao ao Hub atual:
#       - Os cards sao agrupados por intencao, na ordem real do
#         trabalho.
#       - Cada card tem icone de linha + titulo + uma frase
#         (texto real na tela, nao imagem com texto embutido).
#       - "Impressao Comunicado", "Reimpressao Comunicado" e "PIA"
#         deixam de ter card proprio no Hub principal: ficam dentro
#         da tela 'entrada-comunicados' deste modulo, aberta pelo
#         card "Gerar Comunicados".
#       - "Relatorio de ERAS" e "Alterar Dados dos Animais" saem do
#         sub-hub "Manejo e Rastreabilidade" e aparecem direto no
#         Hub principal (o sub-hub continua existindo no Hub atual).
#       - "Parceiros / Fornecedores" NAO aparece aqui - decisao de
#         Benedito: Parceiros vai para o Menu Lateral (grupo
#         Cadastro), trabalho de sessao futura. A rota
#         parceiros_fornecedores.lista continua valendo no Hub
#         atual.
#
#     REGRA DE SEGURANCA: este arquivo so usa nomes de rota
#     (endpoints) que JA aparecem em hubs.py, mais a propria rota
#     'hub_entrada_agrupado.ver' - nenhuma rota nova, nenhuma URL
#     escrita a mao. Um nome de rota errado aqui causaria
#     BuildError ao abrir a tela (licao da v1.16.0 do app.py).
#
#     O Hub nao conhece a Propriedade: cada modulo resolve
#     Propriedade/Produtor sozinho (Padrao Reutilizavel N1). O
#     unico parametro repassado e 'origem', que serve ao botao
#     Voltar de cada modulo (Regra de Ouro #4). ATENCAO: enquanto
#     o Hub novo estiver em rota paralela, o Voltar dos modulos
#     leva ao Hub ATUAL (origem 'entrada'). Isso e esperado nos
#     testes; na troca definitiva o Hub novo passa a responder em
#     /produtor/hub/entrada e o Voltar fica certo sozinho.
#
#     Acesso nos testes: digitar na barra do navegador
#     /produtor/hub-novo/entrada (nenhum item do menu aponta
#     para ele ainda).
#
#     v1.0.0: Criacao do modulo (Sessao 088, 06/10/2026, 11:25 -03).
#         9 cards em 4 grupos. Template:
#         produtor/hub_entrada_agrupado.html v1.0.0.
#     v1.1.0: Sessao 088 (06/10/2026, 12:10 -03) - Reagrupado em 3
#         grupos, seguindo o fluxo real da Compra (Diario de Bordo e
#         Referencia da Sessao 087): "Chegada dos animais" (Nascimento,
#         Compras/GTA, Brincagem Sequencial, Vincular GTA), "Consultas e
#         correcoes" (Consulta Brincagem, Consulta por Manejo, Relatorio
#         de ERAS, Alterar Dados dos Animais) e "Comunicacao". A Brincagem
#         Sequencial e o Vincular GTA saem do antigo grupo "Brincagem"
#         (extinto): a Sequencial e o escritorio das GTAs de Compra ja
#         lancadas (o brete confere depois) e o Vincular GTA fecha o
#         caminho da leitura livre no brete. Descricoes reescritas com
#         as regras confirmadas (R87-05, R87-12) e card renomeado para o
#         nome real "Alterar Dados dos Animais". Mesmos 9 cards, mesmas
#         rotas. Corrigido o carimbo de sessao do v1.0.0 (era "087
#         cont.", o certo e 088).
#     v1.2.0: Sessao 088 (06/10/2026, 12:41 -03) - Duas mudancas:
#         (1) Grupo "Comunicacao" renomeado para "Comunicados a
#         Certificadora" (sugestao de Gilmar e Eduardo, que acharam o
#         nome antigo pouco claro) e a descricao do card "Gerar
#         Comunicados" passa a dizer que o comunicado vai a certificadora.
#         (2) NOVA tela 'entrada-nascimento' (Nascimento / Desmame) com o
#         visual novo: grupos Brincagem, Notificacao a certificadora e
#         Relatorios de nascimentos, 5 cards com as mesmas 5 rotas do
#         sub-hub atual (hubs.py, slug 'entrada-nascimento'), que
#         continua de pe. O card "Nascimento / Desmame" do Hub principal
#         novo passa a abrir essa tela. A rota deixou de ser fixa
#         (/produtor/hub-novo/entrada) e virou /produtor/hub-novo/<slug>;
#         a URL de antes continua valendo. Descricoes dos cards de
#         Nascimento escritas com o que o hubs.py registra e com o que
#         Benedito explicou (o "Numero de Controle" e o numero sequencial
#         da Notificacao; na tela usa-se so "numero de controle").
#         Template e demais arquivos sem mudanca.
#     v1.3.0: Sessao 088 (06/10/2026, 13:00 -03) - Duas mudancas:
#         (1) NOVA tela 'entrada-comunicados' (Comunicados de Entrada)
#         com o visual novo, no lugar do sub-hub de imagens do motor
#         generico: grupo "Comunicado" (Gerar Comunicado, Impressao
#         Comunicado, Reimpressao Comunicado) e grupo "Planilha que
#         acompanha o comunicado" (PIA). Mesmas 4 rotas que o Hub atual
#         ja usa. O card "Gerar Comunicados" do Hub principal novo passa
#         a abrir esta tela. O sub-hub 'entrada-comunicados' do hubs.py
#         (v1.43.0) fica sem uso - inofensivo; pode sair numa limpeza
#         futura. (2) Descricao do card "Compras / GTA" passa a dizer o
#         que a tela dele oferece: importar o PDF da e-GTA, lancar a GTA
#         a mao ou consultar as GTAs. Icone do card "Planilha de
#         Nascimento [PIA]" trocado para o novo desenho 'planilha'.
#         Template com 3 icones novos (hub_entrada_agrupado.html
#         v1.1.0).
#     v1.4.0: Sessao 089 (07/10/2026, 10:20 -03) - NOVA tela 'brincagem'
#         (Hub de Brincagem) no visual novo, em /produtor/hub-novo/brincagem:
#         grupo "Brincar os animais" (Brincagem com Leitor e Brincagem com
#         Bastao) e grupo "Consultas e correcoes" (Consulta Brincagem,
#         Consulta por Manejo, Alterar Dados dos Animais). Mesmas 5 rotas do
#         Hub de Brincagem atual (hubs.py, slug 'brincagem'), cada uma com
#         origem 'brincagem' onde ja era assim; o Hub atual continua de pe.
#         Consulta por Manejo e Alterar Dados aparecem tambem no Hub de
#         Entrada novo (cada um com o seu Voltar). Cada tela agora pode
#         informar o item do menu lateral a destacar (chave menu_ativo no
#         dicionario; se faltar, vale 'entrada' como antes): o Hub de
#         Brincagem destaca "Brincagem". Template com 2 icones novos
#         (hub_entrada_agrupado.html v1.2.0). Regra nova (decisao de
#         Benedito): todo Hub novo nasce neste padrao agrupado, em rota
#         paralela.
#     v1.4.1: Sessao 089 (07/10/2026, 10:40 -03) - Descricao dos cards
#         Brincagem com Leitor e Brincagem com Bastao reescrita com a regra
#         dita por Benedito, igual nas duas: com GTA, os animais ja vem
#         definidos e so recebem o brinco; sem GTA, vincula-se a GTA depois
#         do brinco. Nenhuma outra mudanca.
#     v1.5.0: Sessao 090 (08/10/2026, 07:26 -03) - VOLTAR FIXO DOS HUBS (Regra
#         de Ouro #9). Ate aqui o Voltar dos Hubs novos era o "voltar do
#         navegador": quem voltava de um modulo ao Hub e clicava Voltar de
#         novo caia de volta no modulo (laco). Agora cada Hub tem o seu
#         destino fixo (chave 'voltar' no dicionario), o caminho inverso do
#         de ida: Nascimento / Desmame volta ao Hub de Entrada; Comunicados
#         de Entrada volta ao Hub de Entrada; Hub de Entrada e Hub de
#         Brincagem voltam ao Painel da Fazenda. O Painel e aberto JA COM a
#         fazenda em uso no endereco (identificacao do produtor e da
#         propriedade) - o Home novo aberto sem elas APAGA a fazenda em uso.
#         Sem fazenda em uso (1 fazenda so), abre o Painel simples. Nova
#         funcao _url_voltar(). Template (hub_entrada_agrupado.html) e
#         cards SEM mudanca: o topo ja aceitava o destino do Voltar.
#     v1.6.0: Sessao 090 (08/10/2026, 09:10 -03) - PAINEL SUBSTITUI O HOME: URL_PAINEL passa a
#             /produtor/home (endereco definitivo do Painel). Nenhuma outra
#             mudanca.
#     v1.7.0: Sessao 091 (08/10/2026, 18:20 -03) - NOVA tela 'brincos' (Hub de
#         Brincos) no padrao agrupado, em /produtor/hub-novo/brincos: grupo
#         "Estoque de brincos" (Fornecedor de Brincos, Entrada de Brincos,
#         Brincos Disponiveis), grupo "Baixas" (Cancelamento de Brincos,
#         Historico, Brincos Saidas) e grupo "Relatorios" (Relatorio Resumo,
#         Relatorio N.Fiscais). Mesmas 8 rotas do Hub de Brincos atual
#         (hubs.py, slug 'brincos'); Voltar ao Painel; menu lateral
#         "brincos". Template com 2 icones novos (hub_entrada_agrupado.html
#         v1.3.0). O endereco /produtor/hub/brincos passa a abrir esta tela
#         (hubs.py v1.45.0). Nenhuma outra mudanca.
#     v1.8.0: Sessao 091 (08/10/2026, 19:45 -03) - NOVAS telas 'utilitarios' (Hub de
#         Utilitarios: grupo "Desfazer e proteger" com Operacoes Recentes e
#         Backup e Restore, grupo "Ajustes da fazenda" com Racas da Fazenda)
#         e 'inventario' (Hub de Inventario, so com o Inventario Geral - os
#         outros 2 cards do Hub atual ainda nao tem modulo). Mesmas rotas do
#         hubs.py; Voltar ao Painel; menu lateral de cada um. Template com 4
#         icones novos (hub_entrada_agrupado.html v1.4.0). hubs.py v1.46.0
#         manda /produtor/hub/utilitarios e /produtor/hub/inventario para
#         ca. Nenhuma outra mudanca.
#     v1.9.0: Sessao 092 (09/10/2026, 16:10 -03) - NOVO card "Troca de RFID" no Hub de
#         Brincagem, grupo "Brincar os animais", depois de Brincagem com Bastao
#         (troca o RFID de animal que ja tem o brinco SISBOV; rota
#         troca_rfid.iniciar, modulo backend/routers/troca_rfid.py v1.0.0).
#         Template com 1 icone novo (hub_entrada_agrupado.html v1.5.0).
#         Nenhuma outra mudanca.
#     v1.10.0: Sessao 097 (15/10/2026, 10:05 -03) - PERMISSOES POR CARGO: ver()
#         esconde os cards cujo destino o cargo nao pode abrir
#         (caminho_permitido, routers/permissoes.py) e descarta grupos que
#         ficam vazios. Mesmos cards e rotas para quem tem acesso.
#     v1.11.0: Sessao 097 (15/10/2026, 13:40 -03) - Raças da Fazenda (grupo "Ajustes da fazenda") saiu do Hub de Utilitarios e foi
#         para o Hub de Entrada, como ultimo grupo (decisao do Benedito).
#     v1.12.0: Sessao 098 (16/10/2026, 18:40 -03) - NOVO Hub de Saidas (slug 'saida', /produtor/hub-novo/saida),
#         so com os CARDS: ainda sem telas por tras (rota None). Card sem rota aparece
#         como "Em breve" e nao abre nada. A medida que cada tela nascer, troca-se o
#         None pelo nome da rota. Template v1.6.0 (card Em breve).
#     v1.12.1: Sessao 098 (16/10/2026, 18:45 -03) - Hub de Saidas: card "Leitor do Abate com Bastao" (RFID), Em breve.
#     v1.12.2: Sessao 098 (16/10/2026, 20:20 -03) - Leitor do Abate liga em saida_leitor.iniciar (card deixa de ser Em breve); Bastao segue Em breve.
#     v1.12.3: Sessao 099 (17/10/2026, 12:35 -03) - Leitor do Abate com Bastao liga em saida_bastao.iniciar (card deixa de ser Em breve).
#     v1.12.4: Sessao 099 (17/10/2026, 15:00 -03) - Cadastro de GTA de Saida liga em gta_saida.iniciar (card deixa de ser Em breve).
#     v1.12.5: Sessao 099 (17/10/2026, 15:30 -03) - Relatorio de Embarque liga em saida_relatorio.iniciar (card deixa de ser Em breve).
#     v1.12.6: Sessao 099 (17/10/2026, 17:15 -03) - Consulta Embarque liga em saida_consulta.iniciar (card deixa de ser Em breve).
#     v1.12.7: Sessao 100 (19/10/2026, 17:20 -03) - Card Vincular GTA / Embarque deixa de ser Em breve: abre a Consulta Embarque (escolhe a data e clica em Vincular GTA na linha).
#     v1.12.8: Sessao 100 (19/10/2026, 17:40 -03) - Card Vincular GTA / Embarque abre a tela propria (saida_vincular.iniciar): so embarques pendentes de GTA.
#     v1.12.9: Sessao 100 (19/10/2026, 20:40 -03) - Card Substituicao de Animal liga em saida_substituicao.iniciar (deixa de ser Em breve); descricao ajustada: troca antes do Comunicado.
#     v1.13.0: Sessao 101 (20/10/2026, 09:22 -03) - Novo card Consulta GTA no grupo Consultas e correcoes do Hub de Saidas (saida_gta_consulta.iniciar).
#     v1.13.1: Sessao 101 (20/10/2026, 10:47 -03) - Card Gerar Comunicado de Saida deixa de ser Em breve: abre saida_comunicado.iniciar.
#     v1.13.2: Sessao 101 (20/10/2026, 12:15 -03) - Novos cards Impressao Comunicado de Saida e Reimpressao Comunicado de Saida (saida_impressao) no grupo Comunicados a Certificadora do Hub de Saidas.
#     v1.13.3: Sessao 102 (2026-10-21 12:35 -03) - Novo card Troca depois do Comunicado (abre saida_troca_comunicado.iniciar).
#     v1.13.4: Sessao 102 (2026-10-21 17:40 -03) - Novo card Abate por Arquivo (abre saida_arquivo.iniciar).
#     v1.13.5: Sessao 103 (2026-10-22 16:05 -03) - Texto do card Cadastro de GTA de Saida: a consulta e a Consulta GTA (so texto).  REVERSAO: .bak_antes_consulta_unica_s103.
#     v1.13.6: Sessao 107 (2026-10-28 09:40 -03) - TRANSFERENCIA (pacote 2): dois cards novos no grupo Embarque no brete do Hub de Saidas: Leitor da Transferencia
#         e Leitor da Transferencia com Bastao (transferencia.iniciar, com rota_params via = leitor / bastao). REVERSAO: .bak_antes_s107.
#     v1.13.7: Sessao 107 (2026-10-28 09:58 -03) - Hub de Saidas em duas linhas: grupo Abate no brete (Leitor, Bastao, Arquivo) e grupo Transferencia no brete (Leitor, Bastao e Transferencia
#         por Arquivo, Em breve), com textos genericos (valem para os 3 tipos de transferencia) e icones em azul (nova chave cor_icone do grupo, opcional). REVERSAO: .bak_antes_s107b.
#     v1.13.8: Sessao 110 (2026-10-31 11:51 -03) - Card Transferencia por Arquivo ativado (rota transferencia_arquivo.iniciar). REVERSAO: .bak_antes_s110_transf_arquivo.
#     v1.15.0: Sessao 114 (2026-11-04 11:20 -03) - Hub de Pesos (slug pesos): Leitor de Peso, Leitor de Peso com Bastao (Em breve) e Inconformes.  REVERSAO: .bak_antes_s114_pesos.
#     v1.17.0: Sessao 114 (2026-11-04 19:00 -03) - Hub de Pesos: cards Consulta de Peso e Conferidos (PDF).  REVERSAO: .bak_antes_s114_consulta.
#     v1.16.0: Sessao 114 (2026-11-04 14:50 -03) - Hub de Pesos: Leitor de Peso com Bastao liga em pesos_bastao.iniciar (deixa de ser Em breve).  REVERSAO: .bak_antes_s114_bastao.
#     v1.18.0: Sessao 115 (2026-11-05 13:45 -03) - Hub de Saidas: grupo Alteracao de Posse no brete (Leitor e Bastao), icones laranja.  REVERSAO: .bak_antes_s115_posse_pacote2.
#     v1.19.0: Sessao 115 (2026-11-05 14:20 -03) - Hub de Saidas: card Lista da Alteracao de Posse (via lista).  REVERSAO: .bak_antes_s115_lista.
#     v1.28.2: Sessao 128 (2026-11-16 11:55 -03) - AUDITORIA ETAPA 8b: falha ao checar "Vincular bloqueado" (Hub de Saidas) vai para o log do servidor (antes sumia em silencio; o Hub continua abrindo sem bloquear). REVERSAO: .bak_antes_etapa8b.
# =========================================================

import logging

from flask import Blueprint, render_template, redirect, url_for, session

from backend.routers.auth import redirecionar_home
from backend.routers.permissoes import caminho_permitido

# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
hub_entrada_agrupado = Blueprint('hub_entrada_agrupado', __name__)
logger = logging.getLogger(__name__)

# -------------------------------------------------------
# Configuracao das telas: chave = slug da URL. Cada tela tem um
# titulo e uma lista de grupos, cada grupo com seus cards.
# 'icone' e o nome do icone desenhado no template (macro
# icone). 'rota' e 'rota_params' seguem o mesmo formato do
# hubs.py (nome de rota para url_for + parametros extras).
# -------------------------------------------------------
HUBS_NOVOS = {
    'entrada': {
        'titulo': 'Hub de Entrada',
        'voltar': 'painel',                                  # v1.5.0
        'grupos': [
            {
                'titulo': 'Chegada dos animais',
                'cards': [
                    {
                        'titulo':    'Nascimento / Desmame',
                        'descricao': 'Brincagem, notificação, planilhas e relatórios dos nascimentos.',
                        'icone':     'nascimento',
                        'rota':      'hub_entrada_agrupado.ver',
                        'rota_params': {'slug': 'entrada-nascimento'},
                    },
                    {
                        'titulo':    'Compras / GTA',
                        'descricao': 'Importa o PDF da e-GTA, lança a GTA à mão ou consulta as GTAs lançadas.',
                        'icone':     'compras',
                        'rota':      'gta_compra.nova',
                    },
                    {
                        'titulo':    'Brincagem Sequencial',
                        'descricao': 'Brincagem no escritório das GTAs de compra já lançadas. O brete confere depois.',
                        'icone':     'brinco',
                        'rota':      'brincagem_sequencial.iniciar',
                    },
                    {
                        'titulo':    'Vincular GTA / Brincagem',
                        'descricao': 'Vincula à GTA os brincos lidos no brete sem GTA.',
                        'icone':     'vincular',
                        'rota':      'vincular_gta.iniciar_por_gta',
                    },
                ],
            },
            {
                'titulo': 'Consultas e correções',
                'cards': [
                    {
                        'titulo':    'Consulta Brincagem',
                        'descricao': 'Brincagens realizadas, consultadas por data.',
                        'icone':     'calendario',
                        'rota':      'brincagem_consulta.iniciar',
                        'rota_params': {'origem': 'entrada'},
                    },
                    {
                        'titulo':    'Consulta por Manejo',
                        'descricao': 'Ficha do animal pelo número de manejo: origem, GTA, lote, peso e liberação de abate.',
                        'icone':     'lupa',
                        'rota':      'consulta_manejo.iniciar',
                        'rota_params': {'origem': 'entrada'},
                    },
                    {
                        'titulo':    'Relatório de ERAS',
                        'descricao': 'Lista do rebanho por faixa de idade.',
                        'icone':     'relatorio',
                        'rota':      'relatorio_eras.iniciar',
                    },
                    {
                        'titulo':    'Relatório da Carga',
                        'descricao': 'Lista dos animais recebidos na Carga inicial, com totais por sexo e faixa de idade.',
                        'icone':     'relatorio',
                        'rota':      'carga_relatorio.iniciar',
                    },
                    {
                        'titulo':    'BND/Fazenda',
                        'descricao': 'Compara o Extrato de Animais Vivos do MAPA com os animais da fazenda e gera 4 relatórios em PDF.',
                        'icone':     'relatorio',
                        'rota':      'bnd_fazenda.iniciar',
                    },
                    {
                        'titulo':    'Alterar Dados dos Animais',
                        'descricao': 'Corrige lote, peso, sexo e raça, até gerar o comunicado.',
                        'icone':     'lapis',
                        'rota':      'alterar_dados_animais.iniciar',
                        'rota_params': {'origem': 'entrada'},
                    },
                    {
                        'titulo':    'Linkagem RFID e Brinco',
                        'descricao': 'Liga o RFID ao brinco SISBOV do animal em estoque que ainda não tem RFID. Lê o RFID primeiro, depois o brinco; grava na hora.',
                        'icone':     'bastao',
                        'rota':      'linkagem_rfid.iniciar',
                    },
                    {
                        'titulo':    'Consulta da Linkagem',
                        'descricao': 'Pares RFID + brinco ligados por data, com o relatório em PDF.',
                        'icone':     'lupa',
                        'rota':      'linkagem_consulta.consulta_iniciar',
                    },
                    {
                        'titulo':    'Inconformidades da Linkagem',
                        'descricao': 'Tentativas recusadas: brinco fora do estoque, já com RFID ou RFID em outro animal.',
                        'icone':     'lista',
                        'rota':      'linkagem_consulta.inconformes_iniciar',
                    },
                ],
            },
            {
                'titulo': 'Reidentificação',
                'cards': [
                    {
                        'titulo':    'Reidentificação',
                        'descricao': 'Animal que perdeu o brinco SISBOV recebe um novo do estoque. Vários de uma vez; gera a Notificação à Certificadora.',
                        'icone':     'bastao',
                        'rota':      'reidentificacao.iniciar',
                    },
                    {
                        'titulo':    'Consulta da Reidentificação',
                        'descricao': 'Pedidos por data, Notificação em PDF e marcar como enviado à Certificadora.',
                        'icone':     'lupa',
                        'rota':      'reidentificacao_consulta.consulta_iniciar',
                    },
                    {
                        'titulo':    'Inconformidades da Reidentificação',
                        'descricao': 'Tentativas recusadas: brinco novo fora do estoque, brinco perdido que não está no rebanho, data inválida.',
                        'icone':     'lista',
                        'rota':      'reidentificacao_consulta.inconformes_iniciar',
                    },
                ],
            },
            {
                'titulo': 'Comunicados à Certificadora',
                'cards': [
                    {
                        'titulo':    'Gerar Comunicados',
                        'descricao': 'Comunicado de entrada à certificadora, com impressão, reimpressão e a planilha PIA.',
                        'icone':     'enviar',
                        'rota':      'hub_entrada_agrupado.ver',
                        'rota_params': {'slug': 'entrada-comunicados'},
                    },
                ],
            },
            {
                'titulo': 'Ajustes da fazenda',
                'cards': [
                    {
                        'titulo':    'Raças da Fazenda',
                        'descricao': 'Marca as raças que você mais usa, para aparecerem na lista de Raça da Brincagem Sequencial.',
                        'icone':     'lista',
                        'rota':      'racas.iniciar',
                    },
                ],
            },
        ],
    },

    # v1.2.0: sub-hub de Nascimento / Desmame com o visual novo.
    # Mesmas 5 rotas do sub-hub 'entrada-nascimento' do hubs.py.
    'entrada-nascimento': {
        'titulo': 'Nascimento / Desmame',
        'voltar': '/produtor/hub-novo/entrada',              # v1.5.0
        'grupos': [
            {
                'titulo': 'Brincagem',
                'cards': [
                    {
                        'titulo':    'Brincagem Sequencial',
                        'descricao': 'Brincagem no escritório dos bezerros nascidos ou desmamados, em sequência.',
                        'icone':     'brinco',
                        'rota':      'brincagem_nascimento.iniciar',
                    },
                ],
            },
            {
                'titulo': 'Notificação à certificadora',
                'cards': [
                    {
                        'titulo':    'Notificação de Nascimentos',
                        'descricao': 'Notificação de nascimentos à certificadora, com número de controle, impressão e reimpressão.',
                        'icone':     'enviar',
                        'rota':      'notificacao_nascimento.iniciar',
                    },
                    {
                        'titulo':    'Planilha de Nascimento [PIA]',
                        'descricao': 'Planilha de Identificação Individual (PIA) dos nascimentos de uma notificação.',
                        'icone':     'planilha',
                        'rota':      'pia_impressao.nascimento_iniciar',
                    },
                ],
            },
            {
                'titulo': 'Relatórios de nascimentos',
                'cards': [
                    {
                        'titulo':    'Nascimentos por Período',
                        'descricao': 'Relatório dos nascimentos de um período.',
                        'icone':     'calendario',
                        'rota':      'nascimentos_periodo.iniciar',
                    },
                    {
                        'titulo':    'Nascimento por Número de Controle',
                        'descricao': 'Nascimentos de uma notificação, buscados pelo número de controle.',
                        'icone':     'lupa',
                        'rota':      'nascimentos_periodo.controle_iniciar',
                    },
                ],
            },
        ],
    },
    # v1.3.0: sub-hub dos Comunicados de Entrada com o visual novo.
    # Mesmas 4 rotas do Hub de Entrada atual (hubs.py, slug 'entrada').
    'entrada-comunicados': {
        'titulo': 'Comunicados de Entrada',
        'voltar': '/produtor/hub-novo/entrada',              # v1.5.0
        'grupos': [
            {
                'titulo': 'Comunicado',
                'cards': [
                    {
                        'titulo':    'Gerar Comunicado',
                        'descricao': 'Gera o comunicado de entrada das GTAs de compra já brincadas.',
                        'icone':     'documento',
                        'rota':      'comunicado_entrada.iniciar',
                    },
                    {
                        'titulo':    'Impressão Comunicado',
                        'descricao': 'Imprime os comunicados gerados e ainda não impressos.',
                        'icone':     'impressora',
                        'rota':      'impressao_comunicado.iniciar',
                    },
                    {
                        'titulo':    'Reimpressão Comunicado',
                        'descricao': 'Imprime de novo comunicados já emitidos.',
                        'icone':     'copiar',
                        'rota':      'reimpressao_comunicado.iniciar',
                    },
                ],
            },
            {
                'titulo': 'Planilha que acompanha o comunicado',
                'cards': [
                    {
                        'titulo':    'PIA - Planilha de Identificação Individual',
                        'descricao': 'Planilha de Identificação Individual, por período, por manejo ou por comunicado.',
                        'icone':     'planilha',
                        'rota':      'pia_impressao.iniciar',
                    },
                ],
            },
        ],
    },

    # v1.4.0: Hub de Brincagem com o visual novo (Sessao 089).
    # Mesmas 5 rotas do Hub de Brincagem atual (hubs.py, slug 'brincagem').
    'brincagem': {
        'titulo': 'Hub de Brincagem',
        'menu_ativo': 'brincagem',
        'voltar': 'painel',                                  # v1.5.0
        'grupos': [
            {
                'titulo': 'Brincar os animais',
                'cards': [
                    {
                        'titulo':    'Brincagem com Leitor',
                        'descricao': 'Brincagem no brete com o leitor. Com GTA, os animais já vêm definidos e só recebem o brinco. Sem GTA, vincula-se a GTA depois do brinco.',
                        'icone':     'leitor',
                        'rota':      'brincagem_leitor.iniciar',
                    },
                    {
                        'titulo':    'Brincagem com Bastão',
                        'descricao': 'Brincagem no brete com o bastão, que lê o RFID antes do número SISBOV. Com GTA, os animais já vêm definidos e só recebem o brinco. Sem GTA, vincula-se a GTA depois do brinco.',
                        'icone':     'bastao',
                        'rota':      'brincagem_bastao.iniciar',
                    },
                    {
                        'titulo':    'Troca de RFID',
                        'descricao': 'Troca o RFID do animal que já tem o brinco SISBOV e perdeu o elemento amarelo. Digita o SISBOV, confere o animal e lê o RFID novo.',
                        'icone':     'troca',
                        'rota':      'troca_rfid.iniciar',
                    },
                ],
            },
            {
                'titulo': 'Consultas e correções',
                'cards': [
                    {
                        'titulo':    'Consulta Brincagem',
                        'descricao': 'Brincagens realizadas, consultadas por data.',
                        'icone':     'calendario',
                        'rota':      'brincagem_consulta.iniciar',
                        'rota_params': {'origem': 'brincagem'},
                    },
                    {
                        'titulo':    'Consulta por Manejo',
                        'descricao': 'Ficha do animal pelo número de manejo: origem, GTA, lote, peso e liberação de abate.',
                        'icone':     'lupa',
                        'rota':      'consulta_manejo.iniciar',
                        'rota_params': {'origem': 'brincagem'},
                    },
                    {
                        'titulo':    'Alterar Dados dos Animais',
                        'descricao': 'Corrige lote, peso, sexo e raça, até gerar o comunicado.',
                        'icone':     'lapis',
                        'rota':      'alterar_dados_animais.iniciar',
                        'rota_params': {'origem': 'brincagem'},
                    },
                ],
            },
        ],
    },

    # v1.7.0: Hub de Brincos com o visual novo (Sessao 091).
    # Mesmas 8 rotas do Hub de Brincos atual (hubs.py, slug 'brincos').
    'brincos': {
        'titulo': 'Hub de Brincos',
        'menu_ativo': 'brincos',
        'voltar': 'painel',
        'grupos': [
            {
                'titulo': 'Estoque de brincos',
                'cards': [
                    {
                        'titulo':    'Fornecedor de Brincos',
                        'descricao': 'Fabricantes de brincos cadastrados na plataforma, para consulta. A lista é a mesma para todos.',
                        'icone':     'fornecedor',
                        'rota':      'brincos_fornecedor.listar',
                    },
                    {
                        'titulo':    'Entrada de Brincos',
                        'descricao': 'Registra o lote de brincos recebido: solicitação, nota fiscal, fornecedor e faixa de SISBOV.',
                        'icone':     'brinco',
                        'rota':      'brincos_entrada.iniciar',
                    },
                    {
                        'titulo':    'Brincos Disponíveis',
                        'descricao': 'Imprime a relação dos brincos que ainda estão no estoque, prontos para uso.',
                        'icone':     'impressora',
                        'rota':      'brincos_disponiveis.iniciar',
                    },
                ],
            },
            {
                'titulo': 'Baixas',
                'cards': [
                    {
                        'titulo':    'Cancelamento de Brincos',
                        'descricao': 'Dá baixa em brincos que não serão usados e gera o documento do cancelamento.',
                        'icone':     'cancelar',
                        'rota':      'brincos_cancelamento.iniciar',
                    },
                    {
                        'titulo':    'Histórico',
                        'descricao': 'Cancelamentos já feitos, por dia, com o documento para imprimir de novo.',
                        'icone':     'copiar',
                        'rota':      'brincos_cancelamento.documentos_iniciar',
                    },
                    {
                        'titulo':    'Brincos Saídas',
                        'descricao': 'Todo brinco que saiu do estoque, por uso em animal ou por cancelamento, em PDF.',
                        'icone':     'planilha',
                        'rota':      'brincos_saidas.iniciar',
                    },
                ],
            },
            {
                'titulo': 'Relatórios',
                'cards': [
                    {
                        'titulo':    'Relatório Resumo',
                        'descricao': 'Entradas de brincos no período: uma linha por lote e nota fiscal, com totais.',
                        'icone':     'relatorio',
                        'rota':      'brincos_relatorio_resumo.iniciar',
                    },
                    {
                        'titulo':    'Relatório N.Fiscais',
                        'descricao': 'Notas fiscais dos lotes de brincos, na ordem de entrada, com faixa de SISBOV.',
                        'icone':     'documento',
                        'rota':      'brincos_relatorio_nfiscais.iniciar',
                    },
                ],
            },
        ],
    },

    # v1.8.0: Hub de Utilitarios com o visual novo (Sessao 091).
    'utilitarios': {
        'titulo': 'Hub de Utilitários',
        'menu_ativo': 'utilitarios',
        'voltar': 'painel',
        'grupos': [
            {
                'titulo': 'Desfazer e proteger',
                'cards': [
                    {
                        'titulo':    'Operações Recentes',
                        'descricao': 'Encontra e desfaz as operações feitas nas últimas 24 horas, de qualquer módulo.',
                        'icone':     'relogio',
                        'rota':      'operacoes_recentes.iniciar',
                    },
                    {
                        'titulo':    'Backup e Restore',
                        'descricao': 'Cria uma cópia de segurança dos seus dados e solicita à Consiste a restauração de uma cópia anterior.',
                        'icone':     'backup',
                        'rota':      'backup_restore.iniciar',
                    },
                ],
            },
        ],
    },

    # v1.12.0: Hub de Saidas (Sessao 098) - SO os cards; rota None = "Em breve".
    'saida': {
        'titulo': 'Hub de Saídas',
        'menu_ativo': 'saidas',
        'voltar': 'painel',
        'grupos': [
            {
                'titulo': 'Abate no brete',
                'cor_icone': '#D4370A',   # S108 - borda vermelha do topo, igual a GTA de Abate
                'cards': [
                    {
                        'titulo':    'Leitor do Abate',
                        'descricao': 'Leitura dos animais que embarcam, no brete: lê o brinco, confere o animal, avisa fora da liberação e registra peso e lote de saída.',
                        'icone':     'leitor',
                        'rota':      'saida_leitor.iniciar',
                    },
                    {
                        'titulo':    'Leitor do Abate com Bastão',
                        'descricao': 'Leitura dos animais que embarcam, no brete, com o bastão, que lê o RFID antes do número SISBOV. Confere o animal, avisa fora da liberação e registra peso e lote de saída.',
                        'icone':     'bastao',
                        'rota':      'saida_bastao.iniciar',
                    },
                    {
                        'titulo':    'Abate por Arquivo',
                        'descricao': 'Último recurso sem internet no brete: lê o arquivo ABATE.TXT (ou CSV) com o número dos brincos e gera o Embarque, com prévia dos que entram e dos que ficam de fora.',
                        'icone':     'enviar',
                        'rota':      'saida_arquivo.iniciar',
                    },
                ],
            },
            {
                'titulo': 'Transferência no brete',
                'cor_icone': '#1565C0',   # v1.13.7 - icones em azul (o Abate fica na cor da marca)
                'cards': [
                    {
                        'titulo':    'Leitor da Transferência',
                        'descricao': 'Leitura, no brete, dos animais que saem para outra Propriedade, seja qual for o destino: lê o brinco, confere o animal e registra o destino.',
                        'icone':     'leitor',
                        'rota':      'transferencia.iniciar',
                        'rota_params': {'via': 'leitor'},
                    },
                    {
                        'titulo':    'Leitor da Transferência com Bastão',
                        'descricao': 'Leitura da Transferência no brete com o bastão, que lê o RFID antes do número SISBOV. Confere o animal e registra o destino.',
                        'icone':     'bastao',
                        'rota':      'transferencia.iniciar',
                        'rota_params': {'via': 'bastao'},
                    },
                    {
                        'titulo':    'Transferência por Arquivo',
                        'descricao': 'Último recurso sem internet no brete: lê o arquivo TXT (ou CSV) com o número dos brincos e gera a leitura da Transferência, com prévia dos que entram e dos que ficam de fora.',
                        'icone':     'enviar',
                        'rota':      'transferencia_arquivo.iniciar',
                    },
                ],
            },
            {
                'titulo': 'Alteração de Posse no brete',
                'cor_icone': '#EF6C00',   # s115 - icones em laranja Orion
                'cards': [
                    {
                        'titulo':    'Leitor da Alteração de Posse',
                        'descricao': 'Leitura, no brete, dos animais que continuam na mesma Propriedade e passam para outro Produtor (venda ou herança): lê o brinco e confere o animal. A DTA vem depois.',
                        'icone':     'leitor',
                        'rota':      'posse.iniciar',
                        'rota_params': {'via': 'leitor'},
                    },
                    {
                        'titulo':    'Leitor da Alteração de Posse com Bastão',
                        'descricao': 'Leitura da Alteração de Posse no brete com o bastão, que lê o RFID antes do número SISBOV.',
                        'icone':     'bastao',
                        'rota':      'posse.iniciar',
                        'rota_params': {'via': 'bastao'},
                    },
                    {
                        'titulo':    'Lista da Alteração de Posse',
                        'descricao': 'Sem ir ao brete: mostra os animais com Sexo e ERAS, você marca um a um ou todos do filtro e grava a Alteração de Posse.',
                        'icone':     'enviar',
                        'rota':      'posse.iniciar',
                        'rota_params': {'via': 'lista'},
                    },
                ],
            },
            {
                'titulo': 'Venda no brete',
                'cor_icone': '#2E7D32',   # s111 - icones em verde (Abate na cor da marca, Transferencia em azul)
                'cards': [
                    {
                        'titulo':    'Leitor da Venda',
                        'descricao': 'Leitura, no brete, dos animais vendidos para outro Produtor: lê o brinco, confere o animal e registra o comprador pela GTA.',
                        'icone':     'leitor',
                        'rota':      'venda.iniciar',
                        'rota_params': {'via': 'leitor'},
                    },
                    {
                        'titulo':    'Leitor da Venda com Bastão',
                        'descricao': 'Leitura da Venda no brete com o bastão, que lê o RFID antes do número SISBOV. Confere o animal e registra o comprador pela GTA.',
                        'icone':     'bastao',
                        'rota':      'venda.iniciar',
                        'rota_params': {'via': 'bastao'},
                    },
                    {
                        'titulo':    'Venda por Arquivo',
                        'descricao': 'Último recurso sem internet no brete: lê o arquivo TXT (ou CSV) com o número dos brincos e gera a leitura da Venda, com prévia dos que entram e dos que ficam de fora.',
                        'icone':     'enviar',
                        'rota':      'venda_arquivo.iniciar',
                    },
                ],
            },
            {
                'titulo': 'Morte de animais (escritório)',
                'cor_icone': '#6A1B9A',   # s111 - icones em roxo, a cor da Morte (Abate na cor da marca, Transferencia azul, Venda verde)
                'cards': [
                    {
                        'titulo':    'Lançar Morte',
                        'descricao': 'Lança a morte de um animal pelo Manejo ou pelo brinco: data, tipo, causa e destino. O animal sai do estoque na hora e o brinco não pode mais ser usado.',
                        'icone':     'brinco',
                        'rota':      'morte.iniciar',
                    },
                    {
                        'titulo':    'Morte por Arquivo',
                        'descricao': 'Lê um arquivo TXT (ou CSV) com o número dos brincos. Data, tipo, causa e destino valem para todos os animais do arquivo, que saem do estoque na hora.',
                        'icone':     'enviar',
                        'rota':      'morte_arquivo.iniciar',
                    },
                    {
                        'titulo':    'Controle Interno da Morte',
                        'descricao': 'Lista dos lançamentos de morte (MRT) da Propriedade, com a Notificação e as fotos do animal e do brinco. Aqui você anexa, troca ou exclui fotos.',
                        'icone':     'lupa',
                        'rota':      'morte_fotos.controle',
                    },
                    {
                        'titulo':    'Gerar Notificação de Morte',
                        'descricao': 'Junta todas as mortes ainda sem Notificação em um só documento (Anexo XXII), com número próprio. Depois de gerada, as mortes não podem mais ser desfeitas.',
                        'icone':     'copiar',
                        'rota':      'morte_notificacao.gerar_iniciar',
                    },
                    {
                        'titulo':    'Impressão da Notificação de Morte',
                        'descricao': 'Imprime a Notificação de Morte (Anexo XXII) recém-gerada, em 2 vias: Certificadora e Arquivo ERAS.',
                        'icone':     'impressora',
                        'rota':      'morte_notificacao.impressao_iniciar',
                    },
                    {
                        'titulo':    'Reimpressão da Notificação de Morte',
                        'descricao': 'Reimprime uma Notificação de Morte já impressa. Não altera nada.',
                        'icone':     'impressora',
                        'rota':      'morte_notificacao.reimpressao_iniciar',
                    },
                    {
                        'titulo':    'Mortes no Período',
                        'descricao': 'Relatório em PDF das mortes ocorridas entre duas datas, com tipo, causa, destino, sexo e faixa de idade. Só consulta.',
                        'icone':     'relatorio',
                        'rota':      'morte_relatorios.periodo_iniciar',
                    },
                ],
            },
            {
                'titulo': 'GTA de saída (escritório)',
                'cards': [
                    {
                        'titulo':    'Cadastro de GTA de Saída',
                        'descricao': 'Importa o PDF da e-GTA ou lança a GTA à mão. Para consultar, alterar ou excluir, use a Consulta GTA.',
                        'icone':     'compras',
                        'rota':      'gta_saida.iniciar',
                    },
                    {
                        'titulo':    'Vincular GTA / Embarque',
                        'descricao': 'Vincula à GTA de saída os animais lidos no brete e informa o frigorífico e a data de saída.',
                        'icone':     'vincular',
                        'rota':      'saida_vincular.iniciar',
                    },
                    {
                        'titulo':    'DTA de Alteração de Posse',
                        'descricao': 'Lança à mão a DTA da Alteração de Posse (mesma Propriedade, outro Produtor).',
                        'icone':     'compras',
                        'rota':      'gta_saida.nova_posse',
                    },
                ],
            },
            {
                'titulo': 'Consultas e correções',
                'cards': [
                    {
                        'titulo':    'Consulta Embarque',
                        'descricao': 'Embarques realizados, consultados por data.',
                        'icone':     'calendario',
                        'rota':      'saida_consulta.iniciar',
                    },
                    {
                        'titulo':    'Relatório de Embarque',
                        'descricao': 'Relação dos animais lidos no embarque, em PDF.',
                        'icone':     'impressora',
                        'rota':      'saida_relatorio.iniciar',
                    },
                    {
                        'titulo':    'Substituição de Animal',
                        'descricao': 'Troca o animal lido pelo que realmente embarcou, antes do comunicado, mantendo o histórico.',
                        'icone':     'troca',
                        'rota':      'saida_substituicao.iniciar',
                    },
                    {
                        'titulo':    'Troca depois do Comunicado',
                        'descricao': 'Troca um animal que já está num Comunicado de Saída por outro do mesmo perfil, mantendo o número. Só Titular e Administrador.',
                        'icone':     'troca',
                        'rota':      'saida_troca_comunicado.iniciar',
                    },
                    {
                        'titulo':    'Consulta GTA',
                        'descricao': 'Pesquisa as GTAs de saída, vê os animais de cada uma e baixa a relação em PDF.',
                        'icone':     'lupa',
                        'rota':      'saida_gta_consulta.iniciar',
                    },
                ],
            },
            {
                'titulo': 'Comunicados à Certificadora',
                'cards': [
                    {
                        'titulo':    'Gerar Comunicado de Saída',
                        'descricao': 'Gera o comunicado de saída à certificadora, com os anexos XX e XXI (código de barras e QR Code).',
                        'icone':     'enviar',
                        'rota':      'saida_comunicado.iniciar',
                    },
                    {
                        'titulo':    'Impressão Comunicado de Saída',
                        'descricao': 'Imprime os comunicados de saída gerados e ainda não impressos (Anexo XX, XXI com barras ou XXI com QR Code).',
                        'icone':     'impressora',
                        'rota':      'saida_impressao.impressao_iniciar',
                    },
                    {
                        'titulo':    'Reimpressão Comunicado de Saída',
                        'descricao': 'Imprime de novo comunicados de saída já impressos.',
                        'icone':     'copiar',
                        'rota':      'saida_impressao.reimpressao_iniciar',
                    },
                ],
            },
        ],
    },

    # v1.15.0: Hub de Pesos (Sessao 114) - Registrar Peso no brete.
    'pesos': {
        'titulo': 'Hub de Pesos',
        'menu_ativo': 'pesagens',
        'voltar': 'painel',
        'grupos': [
            {
                'titulo': 'Pesagem no brete',
                'cards': [
                    {
                        'titulo':    'Leitor de Peso',
                        'descricao': 'Pesagem dos animais no brete: lê o brinco, confere o animal, registra o peso e calcula o ganho. Perda de Botton ou Brinco e observações ficam na pesagem.',
                        'icone':     'leitor',
                        'rota':      'pesos_leitor.iniciar',
                    },
                    {
                        'titulo':    'Leitor de Peso com Bastão',
                        'descricao': 'Pesagem no brete com o bastão, que lê o RFID antes do número SISBOV.',
                        'icone':     'bastao',
                        'rota':      'pesos_bastao.iniciar',
                    },
                ],
            },
            {
                'titulo': 'Conferência',
                'cards': [
                    {
                        'titulo':    'Inconformes',
                        'descricao': 'Tudo que deu errado no Leitor de Peso: brinco com dígitos faltando, animal morto ou que já saiu, peso incorreto, pesagem repetida.',
                        'icone':     'lista',
                        'rota':      'pesos_leitor.inconformes_iniciar',
                    },
                    {
                        'titulo':    'Consulta de Peso',
                        'descricao': 'Animais pesados numa data (Leitor, Bastão e brete da Brincagem), com peso, ganho, GMD, dias e perda de elemento, e o resumo por ERAS.',
                        'icone':     'lista',
                        'rota':      'pesos_consulta.consulta_iniciar',
                    },
                    {
                        'titulo':    'Conferidos',
                        'descricao': 'Relatório de Conferências do dia em PDF: animais pesados na data, com o resumo de fêmeas e machos por faixa de idade.',
                        'icone':     'lista',
                        'rota':      'pesos_consulta.conferidos_iniciar',
                    },
                    {
                        'titulo':    'Relatórios de Pesagem',
                        'descricao': 'Relatórios em PDF: pesagem por período, último peso do lote, primeiras 3 pesagens, todas as pesagens, resumo dos lotes, resumo por data, primeira e última, resumo por faixa de peso e pesagem por seleção.',
                        'icone':     'lista',
                        'rota':      'pesos_relatorios.iniciar',
                    },
                ],
            },
        ],
    },

    # v1.8.0: Hub de Inventario com o visual novo (Sessao 091).
    'inventario': {
        'titulo': 'Hub de Inventário',
        'menu_ativo': 'inventario',
        'voltar': 'painel',
        'grupos': [
            {
                'titulo': 'Inventário da propriedade',
                'cards': [
                    {
                        'titulo':    'Inventário Geral',
                        'descricao': 'Gera os PDFs do inventário da propriedade: animais disponíveis na BND e saldo por espécie.',
                        'icone':     'inventario',
                        'rota':      'inventario_geral.iniciar',
                    },
                ],
            },
        ],
    },
}


# -------------------------------------------------------
# v1.5.0 - Destino fixo do botao Voltar de cada Hub (Regra de Ouro #9).
# Chave 'voltar' do Hub: um endereco fixo (Hub -> Hub) ou 'painel'
# (Painel da Fazenda = Home novo). Sem a chave, vale 'painel'.
# O Painel e aberto COM a fazenda em uso (identificacao do produtor e da
# propriedade no endereco, igual ao botao Selecionar do Home): o Home novo
# aberto sem elas APAGA a fazenda em uso. Sem fazenda em uso (ou dado
# incompleto na sessao), abre o Painel simples.
# -------------------------------------------------------
# -------------------------------------------------------
# v1.20.0 (s115) - Hub de Saidas em ABAS. Os cards continuam sendo os de HUBS_NOVOS['saida']['grupos'] (nada muda neles); aqui so se
# diz, por titulo de card, em qual aba e em qual passo cada um aparece. Titulo que nao existe (ou sem permissao) e ignorado.
# -------------------------------------------------------
_CAD = 'Cadastro de GTA de Saída'
_VINC = 'Vincular GTA / Embarque'
_IMP = 'Impressão Comunicado de Saída'   # s120
_REIMP = 'Reimpressão Comunicado de Saída'   # s120 - a Reimpressao de cada aba mostra so o tipo da aba
_COM = ['Gerar Comunicado de Saída', 'Impressão Comunicado de Saída', 'Reimpressão Comunicado de Saída']
_BASTAO = 'Leia o RFID com o bastão, mais rápido no brete.'
_ARQUIVO = 'Sem internet no brete? Envie o arquivo com os brincos.'
TEXTOS_CURTOS = {
    'Cadastro de GTA de Saída': 'Lance a GTA do embarque antes de ir ao brete.',
    'Vincular GTA / Embarque': 'Amarre os animais lidos à GTA.',
    'DTA de Alteração de Posse': 'Preencha a DTA à mão (mesma Propriedade, outro Produtor).',
    'Consulta GTA': 'Veja as GTAs lançadas e a situação de cada uma.',
    'Leitor do Abate': 'Leia o brinco de cada animal que embarca.',
    'Leitor do Abate com Bastão': _BASTAO,
    'Abate por Arquivo': _ARQUIVO,
    'Leitor da Transferência': 'Leia o brinco de cada animal que sai para outra Propriedade.',
    'Leitor da Transferência com Bastão': _BASTAO,
    'Transferência por Arquivo': _ARQUIVO,
    'Leitor da Venda': 'Leia o brinco de cada animal vendido.',
    'Leitor da Venda com Bastão': _BASTAO,
    'Venda por Arquivo': _ARQUIVO,
    'Lançar Morte': 'Registre a morte de um animal pelo escritório.',
    'Morte por Arquivo': 'Lance várias mortes de uma vez, por arquivo.',
    'Controle Interno da Morte': 'Acompanhe as fotos e o controle de cada morte.',
    'Gerar Notificação de Morte': 'Gere a Notificação das mortes lançadas.',
    'Impressão da Notificação de Morte': 'Imprima a Notificação pela primeira vez.',
    'Reimpressão da Notificação de Morte': 'Imprima de novo uma Notificação já impressa.',
    'Mortes no Período': 'Relatório das mortes entre duas datas.',
    'Leitor da Alteração de Posse': 'Leia o brinco dos animais que passam para outro Produtor.',
    'Leitor da Alteração de Posse com Bastão': 'Leia o RFID com o bastão, no brete.',
    'Lista da Alteração de Posse': 'Sem ir ao brete: marque os animais numa lista.',
    'Gerar Comunicado de Saída': 'Gere o Comunicado à Certificadora.',
    'Impressão Comunicado de Saída': 'Imprima o Comunicado pela primeira vez.',
    'Reimpressão Comunicado de Saída': 'Imprima de novo um Comunicado já impresso.',
    'Consulta Embarque': 'Veja os embarques já feitos e seus animais.',
    'Nascimento / Desmame': 'Brincagem, notificação, planilhas e relatórios dos nascimentos.',   # s121 - abas do Hub de Entrada
    'Compras / GTA': 'Importe a e-GTA, lance à mão ou consulte as GTAs.',
    'Brincagem Sequencial': 'Brince no escritório as GTAs de compra já lançadas.',
    'Vincular GTA / Brincagem': 'Amarre à GTA os brincos lidos no brete.',
    'Raças da Fazenda': 'Marque as raças que mais usa na Brincagem.',
    'Linkagem RFID e Brinco': 'Ligue o RFID ao brinco SISBOV do animal.',
    'Consulta da Linkagem': 'Pares ligados por data, com relatório em PDF.',
    'Inconformidades da Linkagem': 'Tentativas recusadas na Linkagem.',
    'Reidentificação': 'Novo brinco para o animal que perdeu o SISBOV.',
    'Consulta da Reidentificação': 'Notificações, PDF e marcar como enviado.',
    'Inconformidades da Reidentificação': 'Tentativas recusadas na Reidentificação.',
    'Consulta Brincagem': 'Brincagens realizadas, por data.',
    'Consulta por Manejo': 'Ficha do animal pelo número de manejo.',
    'Relatório de ERAS': 'Rebanho por faixa de idade.',
    'Relatório da Carga': 'Animais recebidos na Carga inicial.',
    'BND/Fazenda': 'Compare o Extrato da BND com a sua fazenda.',
    'Alterar Dados dos Animais': 'Corrija lote, peso, sexo e raça.',
    'Gerar Comunicados': 'Comunicado de entrada, impressão e planilha PIA.',
    'Gerar Comunicado': 'Gere o Comunicado de Entrada à Certificadora.',
    'Impressão Comunicado': 'Imprima o Comunicado pela primeira vez.',
    'Reimpressão Comunicado': 'Imprima de novo um Comunicado já impresso.',
    'PIA - Planilha de Identificação Individual': 'Planilha que acompanha o Comunicado.',
    'Relatório de Embarque': 'Relatório do embarque por data ou GTA.',
    'Substituição de Animal': 'Troque um animal lido que não embarcou.',
    'Troca depois do Comunicado': 'Troque um animal de um Comunicado já gerado.',
}

_CONS = 'Consulta Embarque'
_DTA = 'DTA de Alteração de Posse'
_TXT_CONS = 'Confira o embarque e copie o pedido da GTA.'   # s118 - passo novo das abas (igual ao GERAS)

HUBS_NOVOS['saida']['abas'] = [
    {'id': 'gta', 'titulo': 'GTAs', 'cor': '#455A64', 'passos': [
        {'n': '', 'titulo': 'GTA de saída (escritório)', 'cards': [_CAD, 'Consulta GTA']}]},
    {'id': 'abate', 'titulo': 'Abate', 'cor': '#D4370A', 'qs': {_CONS: 'tipo=ABATE', _VINC: 'tipo=ABATE', _REIMP: 'tipo=ABATE', _IMP: 'tipo=ABATE'}, 'titulos': {_IMP: 'Impressão Comunicado de Saída – Abate', _REIMP: 'Reimpressão Comunicado de Saída – Abate'}, 'textos': {_CONS: _TXT_CONS}, 'passos': [
        {'n': '1', 'titulo': 'Ler os animais no brete', 'cards': ['Leitor do Abate', 'Leitor do Abate com Bastão', 'Abate por Arquivo']},
        {'n': '2', 'titulo': 'Consultar o embarque', 'cards': [_CONS]},
        {'n': '3', 'titulo': 'Vincular à GTA', 'cards': [_VINC]},
        {'n': '4', 'titulo': 'Comunicado à Certificadora', 'cards': _COM}]},
    {'id': 'transferencia', 'titulo': 'Transferência', 'cor': '#1565C0', 'qs': {_CONS: 'tipo=TRANSFER', _VINC: 'tipo=TRANSFER', _REIMP: 'tipo=TRANSFER', _IMP: 'tipo=TRANSFER'}, 'titulos': {_IMP: 'Impressão Comunicado de Saída – Transferência', _REIMP: 'Reimpressão Comunicado de Saída – Transferência'}, 'textos': {_CONS: _TXT_CONS}, 'passos': [
        {'n': '1', 'titulo': 'Ler os animais no brete', 'cards': ['Leitor da Transferência', 'Leitor da Transferência com Bastão', 'Transferência por Arquivo']},
        {'n': '2', 'titulo': 'Consultar o embarque', 'cards': [_CONS]},
        {'n': '3', 'titulo': 'Vincular à GTA', 'cards': [_VINC]},
        {'n': '4', 'titulo': 'Comunicado à Certificadora', 'cards': _COM}]},
    {'id': 'morte', 'titulo': 'Morte', 'cor': '#6A1B9A', 'passos': [
        {'n': '1', 'titulo': 'Lançar', 'cards': ['Lançar Morte', 'Morte por Arquivo']},
        {'n': '2', 'titulo': 'Notificação de Morte', 'cards': ['Controle Interno da Morte', 'Gerar Notificação de Morte', 'Impressão da Notificação de Morte', 'Reimpressão da Notificação de Morte']},
        {'n': '3', 'titulo': 'Relatório', 'cards': ['Mortes no Período']}]},
    {'id': 'venda', 'titulo': 'Venda', 'cor': '#2E7D32', 'qs': {_CONS: 'tipo=VENDA', _VINC: 'tipo=VENDA', _REIMP: 'tipo=VENDA', _IMP: 'tipo=VENDA'}, 'titulos': {_IMP: 'Impressão Comunicado de Saída – Venda', _REIMP: 'Reimpressão Comunicado de Saída – Venda'}, 'textos': {_CONS: _TXT_CONS}, 'passos': [
        {'n': '1', 'titulo': 'Ler os animais no brete', 'cards': ['Leitor da Venda', 'Leitor da Venda com Bastão', 'Venda por Arquivo']},
        {'n': '2', 'titulo': 'Consultar o embarque', 'cards': [_CONS]},
        {'n': '3', 'titulo': 'Vincular à GTA', 'cards': [_VINC]},
        {'n': '4', 'titulo': 'Comunicado à Certificadora', 'cards': _COM}]},
    {'id': 'posse', 'titulo': 'Alteração de Posse', 'cor': '#EF6C00', 'qs': {_CONS: 'tipo=POSSE', _VINC: 'tipo=POSSE', _REIMP: 'tipo=POSSE', _IMP: 'tipo=POSSE'}, 'titulos': {_IMP: 'Impressão Comunicado de Saída – Posse', _REIMP: 'Reimpressão Comunicado de Saída – Posse'},
     'textos': {_VINC: 'Amarre os animais escolhidos à DTA.', _CONS: 'Confira o embarque antes de lançar a DTA.'}, 'passos': [
        {'n': '1', 'titulo': 'Cadastrar a DTA', 'cards': [_DTA]},
        {'n': '2', 'titulo': 'Escolher os animais', 'cards': ['Leitor da Alteração de Posse', 'Leitor da Alteração de Posse com Bastão', 'Lista da Alteração de Posse']},
        {'n': '3', 'titulo': 'Consultar o embarque', 'cards': [_CONS]},
        {'n': '4', 'titulo': 'Vincular à DTA', 'cards': [_VINC]},
        {'n': '5', 'titulo': 'Comunicado de Posse', 'cards': _COM}]},
    {'id': 'consultas', 'titulo': 'Consultas e correções', 'cor': '#00838F', 'passos': [
        {'n': '', 'titulo': 'Consultas e correções', 'cards': ['Consulta Embarque', 'Substituição de Animal', 'Troca depois do Comunicado']}]},
]


# s118 - acrescenta um trecho de URL (ex.: tipo=VENDA) ao link do card, so dentro da aba que pediu (chave 'qs' da aba).
def _url_com_qs(url, qs):
    if not url or not qs:
        return url
    return url + ('&' if '?' in url else '?') + qs


# -------------------------------------------------------
# s120 - AVISO DE ESPERA: titulo do aviso (peca produtor/aviso_aguarde.html) por card. Card que abre tela lenta entra aqui.
# -------------------------------------------------------
AGUARDAR = {'Operações Recentes': 'Buscando as operações...'}

# -------------------------------------------------------
# s120 - VINCULAR BLOQUEADO quando nao ha o que vincular (Regra de Ouro #64). Aba do Hub de Saidas -> tipo_saida.
# -------------------------------------------------------
TIPO_DA_ABA = {'abate': 'ABATE', 'transferencia': 'TRANSFER', 'venda': 'VENDA', 'posse': 'POSSE'}
TEXTO_NADA_A_VINCULAR = 'Nada a vincular — siga para Gerar Comunicado'


# -------------------------------------------------------
# s120 - Devolve {tipo: True/False} = existe leitura em aberto, SEM GTA, na Propriedade da fazenda em uso. Sem fazenda em uso (ou erro)
# devolve {} e nada e bloqueado (o Hub nunca quebra por causa disto). Mesmo criterio da tela Vincular (embarque aberto sem id_gta).
# -------------------------------------------------------
def _vincular_pendente_por_tipo():
    try:
        fazenda = session.get('fazenda_ativa')
        id_produtor = int(fazenda['id_produtor'])
        id_propriedade = int(fazenda['id_propriedade'])
        from sqlalchemy import func
        from backend.models.tb_2020_embarque import Embarque
        from backend.routers.saida_consulta import _filtro_abertas
        from backend.utils.multitenant import get_db_produtor
        resultado = {}
        with get_db_produtor(id_produtor) as db:
            for tipo in ('ABATE', 'TRANSFER', 'VENDA', 'POSSE'):
                qtd = db.query(func.count(Embarque.id)).filter(*_filtro_abertas(id_propriedade, tipo), Embarque.id_gta.is_(None)).scalar() or 0
                resultado[tipo] = qtd > 0
        return resultado
    except Exception:
        logger.exception('Hub de Saidas: falha ao checar leituras pendentes de Vincular')
        return {}


URL_PAINEL = '/produtor/home'


def _url_voltar(hub):
    voltar = hub.get('voltar', 'painel')
    if voltar != 'painel':
        return voltar

    fazenda = session.get('fazenda_ativa')
    try:
        id_produtor = int(fazenda['id_produtor'])
        id_propriedade = int(fazenda['id_propriedade'])
    except (TypeError, KeyError, ValueError):
        return URL_PAINEL
    return f'{URL_PAINEL}?id_produtor={id_produtor}&id_propriedade={id_propriedade}'


# -------------------------------------------------------
# Rota: /produtor/hub-novo/<slug> - telas do Hub agrupado.
# Mesma regra de acesso do motor generico de Hubs: precisa de
# login e perfil PRODUTOR ou FAZENDA. Slug desconhecido
# redireciona para a Home (nunca 404 feio para o usuario).
# -------------------------------------------------------
@hub_entrada_agrupado.route('/produtor/hub-novo/<slug>')
def ver(slug):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    perfil = session.get('usuario_perfil')
    if perfil not in ('PRODUTOR', 'FAZENDA'):
        return redirecionar_home(perfil)

    hub = HUBS_NOVOS.get(slug)
    if hub is None:
        return redirect(url_for('auth.produtor_home'))

    grupos = []
    mapa_cards = {}   # v1.20.0 - titulo -> card ja filtrado por permissao (usado pelas abas)
    for grupo in hub['grupos']:
        cards = []
        for card in grupo['cards']:
            params = card.get('rota_params', {})
            url_card = url_for(card['rota'], **params) if card['rota'] else None   # v1.12.0 - rota None = Em breve
            if url_card and not caminho_permitido(url_card.split('?')[0]):
                continue
            cards.append({
                'titulo':    card['titulo'],
                'descricao': card['descricao'],
                'icone':     card['icone'],
                'url':       url_card,
                'em_breve':  url_card is None,   # v1.12.0
                'aguarde':   AGUARDAR.get(card['titulo']),   # s120 - aviso de espera
            })
            mapa_cards[card['titulo']] = cards[-1]
        if cards:
            grupos.append({'titulo': grupo['titulo'], 'cards': cards, 'cor_icone': grupo.get('cor_icone')})   # v1.13.7 - cor_icone opcional

    pendente_por_tipo = _vincular_pendente_por_tipo() if slug == 'saida' else {}   # s120 - Vincular bloqueado sem leitura pendente
    abas = []   # v1.20.0 - Hub em abas (so o Hub de Saidas tem 'abas'); aba/passo sem card permitido some
    for aba in hub.get('abas', []):
        passos = []
        tipo_da_aba = TIPO_DA_ABA.get(aba['id'])   # s120
        for passo in aba['passos']:
            textos_aba = aba.get('textos', {})
            qs_aba = aba.get('qs', {})   # s118 - filtro por tipo no card Consulta Embarque
            cards_passo = [dict(mapa_cards[t], titulo=aba.get('titulos', {}).get(t) or mapa_cards[t]['titulo'], texto=textos_aba.get(t) or TEXTOS_CURTOS.get(t, ''), url=_url_com_qs(mapa_cards[t]['url'], qs_aba.get(t))) for t in passo['cards'] if t in mapa_cards]
            for c in cards_passo:   # s120 - Vincular sem nada a vincular: bloqueado, com a saida (Gerar Comunicado)
                if c['titulo'] == _VINC and tipo_da_aba and pendente_por_tipo.get(tipo_da_aba) is False:
                    c['bloqueado'] = True
                    c['texto_bloqueio'] = TEXTO_NADA_A_VINCULAR
            if cards_passo:
                passos.append({'n': passo['n'], 'titulo': passo['titulo'], 'cards': cards_passo})
        if passos:
            abas.append({'id': aba['id'], 'titulo': aba['titulo'], 'cor': aba['cor'], 'passos': passos})

    return render_template('produtor/hub_entrada_agrupado.html',
        titulo_hub     = hub['titulo'],
        grupos         = grupos,
        abas           = abas,
        url_voltar     = _url_voltar(hub),                 # v1.5.0 - Voltar fixo (caminho inverso)
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = hub.get('menu_ativo', 'entrada')   # v1.4.0: cada tela escolhe o item do menu
    )

# s121 - Hub de Entrada em ABAS (mesmo mecanismo do Hub de Saidas)
HUBS_NOVOS['entrada']['abas'] = [
    {'id': 'entrada', 'titulo': 'Entrada de Animais', 'cor': '#D4370A', 'passos': [
        {'n': '', 'titulo': 'Entrada de Animais', 'cards': ['Nascimento / Desmame', 'Compras / GTA', 'Brincagem Sequencial', 'Vincular GTA / Brincagem', 'Raças da Fazenda']}]},
    {'id': 'linkagem', 'titulo': 'Linkagem', 'cor': '#1565C0', 'passos': [
        {'n': '', 'titulo': 'Linkagem RFID e Brinco', 'cards': ['Linkagem RFID e Brinco', 'Consulta da Linkagem', 'Inconformidades da Linkagem']}]},
    {'id': 'reidentificacao', 'titulo': 'Reidentificação', 'cor': '#EF6C00', 'passos': [
        {'n': '', 'titulo': 'Reidentificação', 'cards': ['Reidentificação', 'Consulta da Reidentificação', 'Inconformidades da Reidentificação']}]},
    {'id': 'consultas', 'titulo': 'Consultas e Correções', 'cor': '#455A64', 'passos': [
        {'n': '', 'titulo': 'Consultas e correções', 'cards': ['Consulta Brincagem', 'Consulta por Manejo', 'Relatório de ERAS', 'Relatório da Carga', 'BND/Fazenda', 'Alterar Dados dos Animais']}]},
    {'id': 'comunicados', 'titulo': 'Comunicados', 'cor': '#2E7D32', 'passos': [
        {'n': '1', 'titulo': 'Comunicado', 'cards': ['Gerar Comunicado', 'Impressão Comunicado', 'Reimpressão Comunicado']},
        {'n': '2', 'titulo': 'Planilha que acompanha o comunicado', 'cards': ['PIA - Planilha de Identificação Individual']}]},
]
# v1.28.1 - os cards do sub-hub 'entrada-comunicados' entram no Hub de Entrada (so alimentam a aba; a aba nao passa pelo sub-hub)
HUBS_NOVOS['entrada']['grupos'].append({'titulo': 'Comunicados de Entrada', 'cards': [c for g in HUBS_NOVOS['entrada-comunicados']['grupos'] for c in g['cards']]})

# =========================================================
# FIM DE ARQUIVO: backend\routers\hub_entrada_agrupado.py
# =========================================================
