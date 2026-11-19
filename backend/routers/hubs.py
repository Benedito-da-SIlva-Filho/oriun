# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\hubs.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-08-18 13:45 -03
# ATUALIZADO EM: 2026-11-16 11:55 -03
# VERSAO: 1.48.0
#
# DESCRICAO:
#     Motor generico de telas "Hub" da plataforma Produtor. Um
#     Hub e uma tela intermediaria entre a Home e os modulos de
#     fato - agrupa, em cards visuais (estilo 3D/cartoon, ver
#     Referencia do Sistema), os pontos de entrada de um processo
#     maior (ex.: Hub de Entrada agrupa GTA Compra e Nascimento/
#     Desmame).
#
#     DECISAO DE ARQUITETURA (Benedito, Sessao 034 cont. 9,
#     18/08/2026): em vez de um arquivo + rota + template por
#     Hub, existe UM UNICO motor generico - a rota
#     /produtor/hub/<slug> e o template hub_generico.html sao
#     compartilhados por TODOS os Hubs. Cada Hub e so uma entrada
#     no dict HUBS abaixo (titulo + lista de cards) - criar um Hub
#     novo, no caso comum, e so adicionar uma entrada aqui e subir
#     a(s) imagem(ns), sem tocar em rota nem template. Quando um
#     Hub especifico precisar de logica muito diferente dos demais
#     (ex.: cards com dados dinamicos do banco, nao so estaticos),
#     ele pode ser promovido para arquivo/rota propria nesse
#     momento - este motor generico e o ponto de partida
#     deliberadamente simples, nao uma prisao arquitetural.
#
#     DECISAO DE ARQUITETURA - HUB DENTRO DE HUB (Sessao 041,
#     28/08/2026): um card de HUBS[slug]['cards'] pode apontar,
#     via rota, para OUTRO slug deste mesmo motor generico (ex.:
#     o card "Consultas de Entrada" do Hub de Entrada leva a
#     '/produtor/hub/entrada-consultas", que e ele mesmo outro
#     Hub, com seus proprios cards). Isso NAO exigiu mudanca na
#     rota /produtor/hub/<slug> nem no template - e so mais uma
#     entrada no dict HUBS, com 'rota': 'hubs.ver' e
#     'rota_params': {'slug': 'entrada-consultas'} (ver funcao
#     ver() abaixo para como rota_params e resolvido). Motivo:
#     evitar que Hubs com muitos "cards de consulta/relatorio"
#     (ex.: Hub de Entrada, que teria ido a 17 cards somando GTA
#     Compra + as 9 consultas do fluxo GERAS "Consultas de
#     Animais" + Brincagem/Comunicado) virassem uma parede de
#     cards - as consultas/relatorios de uma area sao agrupadas
#     num sub-hub proprio dessa area (ex.: "Consultas de
#     Entrada"), acessado por 1 card no Hub principal. Mesmo
#     padrao sera repetido no futuro para Abate, Venda,
#     Transferencia e Morte, cada um com seu proprio sub-hub de
#     consultas - decisao explicita de Benedito de nao misturar
#     consultas de areas diferentes no mesmo lugar ("quero saber
#     de ABATE e vejo VENDA confunde").
#
#     FORMATO de cada card dentro de HUBS[slug]['cards']:
#       titulo       - nome do card (so para acessibilidade/alt da
#                      imagem - as artes hoje ja trazem o titulo
#                      embutido na propria imagem).
#       imagem       - caminho dentro de /static/ (estilo 3D/
#                      cartoon, ver Referencia do Sistema).
#       rota         - nome da rota Flask (para url_for) para onde
#                      o card leva ao ser clicado, ou None se o
#                      modulo real ainda nao existe. Card com
#                      rota=None aparece na tela so como visual,
#                      SEM link (mesma decisao ja aplicada aos
#                      cards ainda-nao-prontos da Home: "so eu uso
#                      o Orion hoje, sei que nao esta pronto e nao
#                      vou clicar" - Benedito). Para linkar a OUTRO
#                      Hub (ver Hub dentro de Hub acima), usar
#                      'hubs.ver' e informar 'rota_params'.
#       rota_params  - OPCIONAL. Dict de parametros extras para
#                      url_for(rota, **rota_params). Usado hoje so
#                      para linkar a outro slug (ex.:
#                      {'slug': 'entrada-consultas'}).
#
#     FORMATO de HUBS[slug] (nivel do proprio Hub):
#       titulo        - titulo exibido no topo da tela do Hub.
#       tamanho_card  - OPCIONAL. 'padrao' (default, se a chave
#                       nao existir) ou 'compacto'. Controla o
#                       tamanho dos cards na grade - Hubs com
#                       poucos cards usam 'padrao'; Hubs com muitos
#                       cards usam 'compacto' para caber na tela
#                       sem exigir tanto scroll (Sessao 041,
#                       28/08/2026 - ver hub_generico.html v1.2.0
#                       para a implementacao visual das duas
#                       classes CSS). Decisao manual por Hub, nao
#                       calculada automaticamente pela quantidade
#                       de cards.
#       cards         - lista de cards, ver formato acima.
#
#     Slug desconhecido em /produtor/hub/<slug> NUNCA mostra 404
#     feio para o usuario - redireciona para a Home (mesmo
#     principio geral do Orion: nada quebrado na cara do
#     Produtor).
#
#     v1.0.0: Criacao do modulo (Sessao 034 continuacao 9,
#         18/08/2026). Primeiro Hub construido: Entrada, com 2
#         cards - GTA Compra (rota gta_compra.nova, ja existente
#         e testada de ponta a ponta nesta mesma sessao) e
#         Nascimento/Desmame (rota None). O card "Fornecedor" do
#         desenho original do processo de Entrada foi descartado
#         nesta sessao - decisao de Benedito: a resolucao do
#         Fornecedor/Parceiro ja acontece automaticamente durante
#         a leitura da GTA (ver backend/servicos/
#         resolver_parceiro.py), nao precisa de tela propria.
#     v1.1.0: Sessao 034 (continuacao 9, 18/08/2026, 19:37 -03) -
#         Adicionado 3o card ao Hub de Entrada: "Parceiros /
#         Fornecedores" (P-047), rota parceiros_fornecedores.lista.
#         Imagem hoje e um PLACEHOLDER simples (estilo azul-
#         acinzentado, deliberadamente diferente do padrao
#         dourado das artes definitivas).
#     v1.2.0: Sessao 041 (28/08/2026, 15:00 -03) - Criado o Hub
#         de Brincos, com os 7 cards administrativos combinados
#         com Benedito na Sessao 040. Uso administrativo (compra
#         de insumo), nao dia a dia de fazenda - por isso acessado
#         pela lista compacta do menu lateral, NAO por card grande
#         na Home. Todos os 7 cards com rota=None por enquanto.
#     v1.3.0: Sessao 041 (28/08/2026, 15:50 -03) - Adicionada a
#         chave opcional 'tamanho_card' ('padrao'/'compacto') a
#         cada entrada de HUBS, repassada ao template. Hub de
#         Entrada mantido em 'padrao' (3 cards); Hub de Brincos
#         passou a 'compacto' (7 cards).
#     v1.4.0: Sessao 041 (28/08/2026, 17:23 -03) - Fluxo real de
#         Brincagem/GTA/Comunicado (fluxograma trazido por
#         Benedito) mapeado na arquitetura de Hubs, com os
#         seguintes remanejos combinados em conversa:
#         - Hub de Entrada ganhou 6 novos cards de ACAO (Brincagem
#           Sequencial, Lancar GTA, Gerar Comunicado, Impressao
#           Comunicado, Reimpressao Comunicado) mais 1 card
#           "Consultas de Entrada" que abre um sub-hub (ver
#           abaixo) - total 9 cards, tamanho_card mudado de
#           'padrao' para 'compacto' por causa disso.
#         - "Brincagem com Leitor" e "Brincagem com Bastao" NAO
#           entraram no Hub de Entrada - sao uso de campo (nao
#           administrativo/escritorio como a Brincagem Sequencial)
#           e foram para o novo Hub de Brincagem abaixo, junto com
#           "Consulta Brincagem" (esta ultima tambem usada dentro
#           do fluxo do Hub de Entrada - mesma tela, acessivel
#           dos dois lugares, conforme confirmado por Benedito).
#         - Novo sub-hub 'entrada-consultas' criado com os 9 itens
#           do fluxo GERAS "Consultas de Animais" (Consulta GTA,
#           Consulta Parceiro, Consulta Produtor, Entrada
#           Analitica, Relatorio de GTAs, Relatorio de ERAS,
#           Nascimento por Periodo, Nascimento por No Controle,
#           Alterar Dado do Animal) - primeiro uso do padrao "Hub
#           dentro de Hub" descrito acima.
#         - Novo Hub 'brincagem' criado (Brincagem com Leitor,
#           Brincagem com Bastao, Consulta Brincagem) - card de
#           origem e o card "Brincagem" ja existente na Home
#           (ainda sem link ate esta versao).
#         - Nenhuma imagem definitiva existe ainda para os cards
#           novos (Hub de Entrada v1.4.0, sub-hub entrada-
#           consultas e Hub de Brincagem) - Benedito ainda nao
#           gerou as artes. Todos usam temporariamente o mesmo
#           PLACEHOLDER azul-acinzentado ja usado no card
#           "Parceiros" (img/hubs/entrada/parceiros.png) so para
#           o Hub abrir sem icone quebrado - trocar cada caminho
#           de imagem quando a arte definitiva de cada card
#           existir, sem precisar tocar neste arquivo.
#         - Todos os cards novos desta versao nascem com
#           rota=None (nenhum modulo interno construido ainda) -
#           mesmo principio ja usado no Hub de Brincos: "so cards
#           com rota funcionando entram no Hub a medida que forem
#           construidos" (ordem de construcao a definir em sessao
#           futura).
#     v1.5.0: Sessao 042 (31/08/2026, 18:32 -03) - Modulo real de
#         Entrada de Brincos construido (backend/routers/
#         brincos_entrada.py). Card "Entrada de Brincos" do Hub de
#         Brincos deixa de ter rota=None e passa a apontar para
#         'brincos_entrada.iniciar' - primeiro card do Hub de
#         Brincos com modulo de verdade por tras (os demais 6
#         cards continuam rota=None, na ordem de construcao ja
#         combinada com Benedito: Fornecedor -> Entrada [este] ->
#         Disponiveis -> Cancelamento -> Saidas -> Resumo/N.Fiscais).
#         Nenhuma outra mudanca neste arquivo.
#     v1.6.0: Sessao 043 (01/09/2026, 11:00 -03) - Modulo real de
#         Fornecedor de Brincos construido (backend/routers/
#         brincos_fornecedor.py), consulta SOMENTE LEITURA dos
#         Fabricantes cadastrados. Card "Fornecedor de Brincos" do
#         Hub de Brincos deixa de ter rota=None e passa a apontar
#         para 'brincos_fornecedor.listar' - 2o card do Hub de
#         Brincos com modulo de verdade por tras, seguindo a ordem
#         ja combinada (Fornecedor [este] -> Entrada -> Disponiveis
#         -> Cancelamento -> Saidas -> Resumo/N.Fiscais). Os demais
#         5 cards continuam rota=None. Nenhuma outra mudanca neste
#         arquivo.
#     v1.7.0: Sessao 043 (01/09/2026, 11:50 -03) - Modulo real de
#         Relatorio Resumo de Entrada de Brincos construido
#         (backend/routers/brincos_relatorio_resumo.py). Card
#         "Relatório Resumo" do Hub de Brincos deixa de ter
#         rota=None e passa a apontar para
#         'brincos_relatorio_resumo.iniciar' - 3o card do Hub de
#         Brincos com modulo de verdade por tras. Decisao de
#         Benedito (Sessao 043): seguir a ordem do fluxograma real
#         trazido (Fornecedor -> Entrada -> Relatorio Resumo
#         [este]), pulando por ora Disponiveis/Cancelamento/
#         Saidas/N.Fiscais - continuam rota=None ate serem
#         construidos. Nenhuma outra mudanca neste arquivo.
#     v1.7.1: Sessao 043 (01/09/2026, 13:45 -03) - Correcao de
#         timestamp incorreto na v1.7.0 (Claude codou sem pedir a
#         hora real antes). Nenhuma mudanca de conteudo/logica.
#     v1.8.0: Sessao 044 (02/09/2026, 10:25 -03) - Modulo real de
#         Relatorio N.Fiscais construido (backend/routers/
#         brincos_relatorio_nfiscais.py). Card "Relatório
#         N.Fiscais" do Hub de Brincos deixa de ter rota=None e
#         passa a apontar para 'brincos_relatorio_nfiscais.iniciar'
#         - 4o card do Hub de Brincos com modulo de verdade por
#         tras, ultimo da ordem combinada com Benedito (Fornecedor
#         -> Entrada -> Relatorio Resumo -> Relatorio N.Fiscais
#         [este]). Restam com rota=None: Brincos Disponiveis,
#         Cancelamento de Brincos, Brincos Saidas. Nenhuma outra
#         mudanca neste arquivo.
#     v1.9.0: Sessao 044 (02/09/2026, 14:35 -03) - Modulo real de
#         Brincos Disponiveis construido (backend/routers/
#         brincos_disponiveis.py, PDF direto sem grid). Card
#         "Brincos Disponíveis" do Hub de Brincos deixa de ter
#         rota=None e passa a apontar para
#         'brincos_disponiveis.iniciar' - 5o card do Hub de
#         Brincos com modulo de verdade por tras. Restam com
#         rota=None: Cancelamento de Brincos, Brincos Saidas.
#         Nenhuma outra mudanca neste arquivo.
#     v1.10.0: Sessao 045 (03/09/2026, 09:40 -03) - Modulo real de
#         Cancelamento de Brincos construido (backend/routers/
#         brincos_cancelamento.py). Card "Cancelamento de Brincos"
#         do Hub de Brincos deixa de ter rota=None e passa a
#         apontar para 'brincos_cancelamento.iniciar' - 6o card do
#         Hub de Brincos com modulo de verdade por tras. Resta com
#         rota=None: Brincos Saidas (ultimo card do Hub). Nenhuma
#         outra mudanca neste arquivo.
#     v1.11.0: Sessao 045 (03/09/2026, 11:32 -03) - Modulo real de
#         Brincos Saidas construido (backend/routers/
#         brincos_saidas.py). Card "Brincos Saídas" do Hub de
#         Brincos deixa de ter rota=None e passa a apontar para
#         'brincos_saidas.iniciar' - 7o e ULTIMO card do Hub de
#         Brincos com modulo de verdade por tras. HUB DE BRINCOS
#         COMPLETO - todos os 7 cards com rota funcionando. Nenhuma
#         outra mudanca neste arquivo.
#     v1.12.0: Sessao 045 (03/09/2026, 15:30 -03) - Criado o Hub de
#         Utilitarios (slug 'utilitarios'), com 1 card por enquanto:
#         "Operações Recentes" (rota operacoes_recentes.iniciar,
#         modulo NOVO - tela central do mecanismo "Desfazer por
#         Operacao"/Log de Operacoes). Item "Utilitarios" do menu
#         lateral (produtor_menu.html) atualizado para apontar para
#         este Hub em vez do placeholder antigo /produtor/utilitarios
#         (nunca implementado). Hub nasce pronto para receber outros
#         cards de utilitario no futuro, sem mudanca de arquitetura -
#         mesmo motor generico ja usado pelo Hub de Brincos.
#     v1.13.0: Sessao 045 (03/09/2026, 17:36 -03) - Adicionado 8o
#         card ao Hub de Brincos: "Documentos de Cancelamento" (rota
#         brincos_cancelamento.documentos_iniciar) - lista todos os
#         cancelamentos ja feitos para a Propriedade e permite gerar/
#         imprimir o Documento formal de Cancelamento (Solicitacao de
#         Cancelamento de Codigo SISBOV) em PDF, modelo oficial usado
#         junto a Certificadora. Hub de Brincos, que ja estava
#         "completo" com 7 cards, ganha o 8o - o Hub pode continuar
#         crescendo sem mudanca de arquitetura.
#     v1.14.0: Sessao 045 (03/09/2026, 18:10 -03) - 8o card renomeado
#         de "Documentos de Cancelamento" para "Histórico" (mesma
#         rota, mesma funcionalidade - so nome e imagem mudaram, a
#         pedido de Benedito) e imagem trocada do placeholder cinza
#         para a arte definitiva (08_historico.png, gerada nesta
#         sessao a partir de edicao de imagem sobre a arte original
#         de Benedito - fundo do banner escurecido para bater com o
#         padrao visual dos demais cards do Hub).
#     v1.15.0: Sessao 046 (04/09/2026, 13:40 -03) - Adicionado 2o
#         card ao Hub de Utilitarios: "Backup e Restore" (rota
#         backup_restore.iniciar, modulo NOVO - mecanismo de Backup/
#         Restore de Schema inteiro do Produtor, com pg_dump/
#         pg_restore reais). Segue o mesmo padrao ja usado por
#         "Operações Recentes": card aponta para uma rota .iniciar()
#         que resolve Propriedade/Produtor sozinha (P-036), imagem
#         placeholder ate a arte definitiva ser gerada. Nenhuma
#         outra mudanca neste arquivo.
#     v1.16.0: Sessao 047 (07/09/2026, 17:45 -03) - Adicionado 3o
#         card ao Hub de Utilitarios: "Raças da Fazenda" (rota
#         racas.iniciar, modulo NOVO - selecao de Racas comuns ao
#         Produtor, tb_4005_racas). Mesmo padrao ja usado por
#         "Operações Recentes" e "Backup e Restore": card aponta
#         para uma rota .iniciar() que resolve Propriedade/Produtor
#         sozinha (P-036), imagem placeholder ate a arte definitiva
#         ser gerada. Nenhuma outra mudanca neste arquivo.
#     v1.17.0: Sessao 048 (09/09/2026, 11:40 -03) - Card "Brincagem
#         Sequencial" (posicao 4 do Hub de Entrada) recebe a arte
#         definitiva (Brincagem_Sequencial.png), substituindo o
#         placeholder que ate aqui era o mesmo arquivo usado pelo
#         card "Parceiros" (por isso os dois pareciam duplicados na
#         tela). Rota continua None - so passa a apontar para o
#         router real (brincagem_sequencial) quando o Bloco A/B/C
#         desta sessao estiver pronto. Nenhuma outra mudanca neste
#         arquivo.
#     v1.18.0: Sessao 048 (09/09/2026, 14:55 -03) - Card
#         "Brincagem Sequencial" (posicao 4 do Hub de Entrada)
#         deixa de ter rota=None e passa a apontar para
#         'brincagem_sequencial.iniciar' - Bloco A (rota /lista)
#         construido e testado nesta sessao. Nenhuma outra
#         mudanca neste arquivo.
#     v1.19.0: Sessao 051 (13/09/2026, 12:00 -03) - Hub de
#         Utilitarios (slug 'utilitarios') recebe as 3 artes
#         definitivas, ja geradas por Benedito e salvas em
#         C:\Orion\frontend\static\img\hubs\utilitarios\ - os 3
#         cards deste Hub ja tinham rota funcionando desde as
#         Sessoes 045/046/047 (operacoes_recentes.iniciar,
#         backup_restore.iniciar, racas.iniciar), mas usavam o
#         _PLACEHOLDER generico ate agora (mesma imagem de
#         "Parceiros" do Hub de Entrada) - por isso pareciam
#         modulos nao prontos, quando na verdade ja funcionavam.
#         Substituicoes:
#           - Operações Recentes  -> img/hubs/utilitarios/1-operacoes.jpg
#           - Backup e Restore    -> img/hubs/utilitarios/2-bkp_restaure.jpg
#           - Raças da Fazenda    -> img/hubs/utilitarios/3-racas.jpg
#         Nenhuma mudanca de rota, logica ou de outro Hub neste
#         arquivo.
#     v1.20.0: Sessao 052 (14/09/2026, 13:45 -03) - Hub de Entrada
#         (slug 'entrada') recebe 4 das 5 artes definitivas dos
#         cards de ACAO criados na v1.4.0 (Brincagem/GTA/
#         Comunicado), geradas nesta sessao a partir de prompts de
#         IA de imagem + composicao (Python/Pillow) sobre o padrao
#         visual real do sistema (moldura extraida diretamente de
#         um card existente do proprio Hub, garantindo fidelidade
#         pixel a pixel - nao recriada por estimativa). NENHUM dos
#         4 cards tem modulo interno construido ainda - rota
#         continua None nos 4, seguindo o mesmo principio ja usado
#         no Hub de Utilitarios (v1.19.0): so a arte mudou, a
#         funcionalidade e trabalho de sessao futura. Substituicoes
#         do _PLACEHOLDER generico:
#           - Lançar GTA               -> img/hubs/entrada/lancar_gta.jpg
#           - Gerar Comunicado         -> img/hubs/entrada/gerar_comunicado.jpg
#           - Impressão Comunicado     -> img/hubs/entrada/impressao_comunicado.jpg
#           - Reimpressão Comunicado   -> img/hubs/entrada/reimpressao_comunicado.jpg
#         O 5o card desta familia, "Consultas de Entrada", NAO
#         recebeu arte nesta sessao - continua com _PLACEHOLDER
#         ate o mockup de marca (sem tela real ainda) ser gerado em
#         sessao futura. Nenhuma mudanca de rota, logica ou de
#         outro Hub neste arquivo.
#     v1.21.0: Sessao 052 (14/09/2026, 17:10 -03) - Card "Gerar
#         Comunicado" (Hub de Entrada) deixa de ter rota=None e
#         passa a apontar para 'comunicado_entrada.iniciar' -
#         modulo real construido nesta sessao (backend/routers/
#         comunicado_entrada.py). Os outros 3 cards da familia
#         (Lançar GTA, Impressão Comunicado, Reimpressão
#         Comunicado) continuam com rota=None - modulos ainda nao
#         construidos. Nenhuma outra mudanca neste arquivo.
#     v1.22.0: Sessao 053 (15/09/2026, 17:31 -03) - Card "Consulta
#         Brincagem" adicionado ao Hub de Entrada (slug 'entrada'),
#         na posicao correta do fluxo real: logo APOS "Brincagem
#         Sequencial" e ANTES de "Lançar GTA" - fecha uma pendencia
#         em aberto desde a v1.4.0 (Sessao 041), cujo comentario ja
#         registrava a intencao de que "Consulta Brincagem" fosse
#         "tambem usada dentro do fluxo do Hub de Entrada - mesma
#         tela, acessivel dos dois lugares". O card equivalente
#         continua tambem no Hub de Brincagem (slug 'brincagem'),
#         sem alteracao - os dois apontam, por ora, para o mesmo
#         modulo futuro (ainda rota=None nos dois lugares; nenhum
#         modulo interno construido ate esta sessao). Hub de
#         Entrada passa de 9 para 10 cards - efeito colateral
#         desejado: na grade de 6 colunas (tamanho_card='compacto'),
#         "Gerar Comunicado" e os demais cards da familia
#         Comunicado sao empurrados automaticamente para a 2a linha,
#         sem qualquer reordenacao manual. Nenhuma outra mudanca
#         neste arquivo (nenhum outro Hub, nenhuma rota, nenhuma
#         imagem trocada).
#     v1.23.0: Sessao 053 (15/09/2026, 17:36 -03) - Card "Consulta
#         Brincagem" (Hub de Entrada, posicao 5) recebe a arte
#         definitiva (Consulta_brincagem.jpg), substituindo o
#         _PLACEHOLDER generico. Rota continua None - modulo
#         interno ainda nao construido. Nenhuma outra mudanca
#         neste arquivo (o card irmao no Hub de Brincagem, slug
#         'brincagem', continua com _PLACEHOLDER - fora do escopo
#         desta sessao).
#     v1.24.0: Sessao 054 (16/09/2026, 11:30 -03) - Cards
#         "Impressão Comunicado" e "Reimpressão Comunicado" (Hub
#         de Entrada) deixam de ter rota=None e passam a apontar
#         para 'impressao_comunicado.iniciar' e
#         'reimpressao_comunicado.iniciar' - modulos reais
#         construidos nesta sessao (backend/routers/
#         impressao_comunicado.py e reimpressao_comunicado.py,
#         seguindo o Padrao Reutilizavel Nº3 de Impressao/
#         Reimpressao de Documento Oficial). Mesmo padrao ja usado
#         em "Gerar Comunicado" (v1.21.0). Com isso, os 4 primeiros
#         cards da familia Comunicado (Gerar/Impressao/Reimpressao)
#         ja tem modulo real - resta so "Lançar GTA" com rota=None.
#         Nenhuma outra mudanca neste arquivo (nenhum outro Hub,
#         nenhuma imagem trocada).
#     v1.25.0: Sessao 054 (16/09/2026, 17:15 -03) - Decisao 100%
#         fechada com Benedito: sub-hub 'entrada-consultas' (Hub
#         dentro de Hub, ver DESCRICAO) reduzido de 9 para 4 cards,
#         e renomeado de "Consultas de Entrada" para "Manejo e
#         Rastreabilidade" (titulo do card no Hub de Entrada E
#         titulo da propria pagina do sub-hub - os dois).
#         Cards REMOVIDOS de vez (sem ir para nenhum outro Hub):
#         Consulta GTA, Consulta Parceiro, Consulta Produtor,
#         Entrada Analitica, Relatorio de GTAs.
#         Cards MANTIDOS (4, com pequenos ajustes de nome e arte
#         definitiva nova, confirmada por Benedito a partir de
#         mockup real das 4 imagens):
#           - "Alterar Dado do Animal" -> "Alterar Dados Animais"
#           - "Nascimento por Período" -> "Nascimentos por Período"
#           - "Nascimento por Nº Controle" -> "Nascimento por
#             Número de Controle"
#           - "Relatório de ERAS" (sem mudanca de nome)
#         Ordem dos 4 cards confirmada por Benedito (a mesma do
#         mockup). Imagens: NOVO PADRAO fechado nesta sessao (ver
#         padroes-de-codigo.md) - sub-hub reaproveita a MESMA pasta
#         de imagens do Hub PRINCIPAL ao qual pertence (neste caso,
#         'entrada'), nunca cria subpasta propria; aplicar aos
#         sub-hubs futuros (Saida, Transferencia, Morte) sem
#         reperguntar. Caminhos usados (arquivos ainda a subir por
#         Benedito em C:\Orion\frontend\static\img\hubs\entrada\):
#           - img/hubs/entrada/alterar_dados_animais.jpg
#           - img/hubs/entrada/nascimentos_por_periodo.jpg
#           - img/hubs/entrada/nascimento_por_numero_controle.jpg
#           - img/hubs/entrada/relatorio_eras.jpg
#         O card no Hub de Entrada que ABRE o sub-hub continua com
#         o _PLACEHOLDER generico (sem arte definitiva propria
#         ainda) - so o texto do titulo mudou. Slug da URL
#         ('entrada-consultas') NAO mudou - e so identificador
#         tecnico interno, invisivel ao usuario (confirmado com
#         Benedito). Nenhuma outra mudanca neste arquivo (nenhum
#         outro Hub, nenhuma rota).
#     v1.25.1: Sessao 054 (16/09/2026, 17:25 -03) - Ponta solta da
#         v1.25.0: o card "Manejo e Rastreabilidade" (Hub de
#         Entrada) tinha ficado com o _PLACEHOLDER generico (mesma
#         imagem do card "Parceiros") em vez de arte propria.
#         Corrigido para 'img/hubs/entrada/
#         manejo_rastreabilidade.jpg' (arquivo confirmado por
#         Benedito). Nenhuma outra mudanca neste arquivo.
#     v1.26.0: Sessao 055 (17/09/2026, 10:30 -03) - Card "Relatório
#         de ERAS" (sub-hub 'entrada-consultas') deixa de ter rota=None
#         e passa a apontar para 'relatorio_eras.iniciar'
#         - modulo real construido nesta sessao (backend/routers/
#         relatorio_eras.py, backend/utils/pdf_relatorio_eras.py,
#         template relatorio_eras_faixas.html). Restam com
#         rota=None no sub-hub 'entrada-consultas': Alterar Dados
#         Animais, Nascimentos por Período, Nascimento por Número
#         de Controle. Nenhuma outra mudanca neste arquivo (nenhum
#         outro Hub, nenhuma imagem trocada).
#     v1.27.0: Sessao 057 (20/09/2026, 09:00 -03) - Hub de
#         Brincagem (slug 'brincagem') recebe as 3 artes
#         definitivas dos cards, substituindo o _PLACEHOLDER
#         generico (mesma imagem de "Parceiros" do Hub de Entrada,
#         que deixava os 3 cards visualmente identicos e mal
#         identificados - flagrado por Benedito ao testar o fluxo
#         Home -> Brincagem nesta sessao). Substituicoes:
#           - Brincagem com Leitor  -> img/hubs/brincagem/brincagem_leitor.jpg
#           - Brincagem com Bastão  -> img/hubs/brincagem/brincagem_bastao.jpg
#           - Consulta Brincagem    -> img/hubs/brincagem/consulta_brincagem.jpg
#         Nenhum dos 3 cards tem modulo interno construido ainda -
#         rota continua None nos tres, mesmo principio ja usado no
#         Hub de Utilitarios (v1.19.0) e no Hub de Entrada
#         (v1.20.0): so a arte mudou, a funcionalidade e trabalho
#         desta mesma sessao ("Brincagem com Leitor") e de sessoes
#         futuras ("Brincagem com Bastão", "Consulta Brincagem").
#         Arquivos ja salvos por Benedito em
#         C:\Orion\frontend\static\img\hubs\brincagem\. Nenhuma
#         outra mudanca neste arquivo (nenhum outro Hub, nenhuma
#         rota).
#     v1.28.0: Sessao 057 (20/09/2026, 10:15 -03) - Modulo real
#         de Brincagem com Leitor construido (backend/routers/
#         brincagem_leitor.py, Opcao 2 - sem GTA vinculada). Card
#         "Brincagem com Leitor" (Hub de Brincagem, slug
#         'brincagem') deixa de ter rota=None e passa a apontar
#         para 'brincagem_leitor.iniciar' - 1o card do Hub de
#         Brincagem com modulo de verdade por tras. Restam com
#         rota=None: "Brincagem com Bastão" e "Consulta
#         Brincagem" (sessoes futuras). Nenhuma outra mudanca
#         neste arquivo (nenhum outro Hub, nenhuma imagem
#         trocada).
#     v1.29.0: Sessao 061 (20/09/2026, 12:00 -03) - Modulo real
#         de Consulta Brincagem construido (backend/routers/
#         brincagem_consulta.py, 1a entrega: lista + exclusao,
#         so registros da Brincagem com Leitor). Os DOIS cards
#         "Consulta Brincagem" (Hub de Entrada E Hub de
#         Brincagem, ja previstos desde a v1.4.0 como "mesma
#         tela, acessivel dos dois lugares") deixam de ter
#         rota=None e passam a apontar para
#         'brincagem_consulta.iniciar' - cada um com seu proprio
#         'origem' em rota_params (Regra de Ouro #4/#7, botao
#         Voltar aponta pro Hub certo em cada caso). Resta com
#         rota=None: "Brincagem com Bastão" (sessao futura).
#         Nenhuma outra mudanca neste arquivo (nenhum outro Hub,
#         nenhuma imagem trocada).
#     v1.30.0: Sessao 077 (22/09/2026, 13:55 -03) - Modulo real de
#         Brincagem com Bastao construido (backend/routers/
#         brincagem_bastao.py - mesma estrutura do Leitor, com a
#         etapa extra de leitura de RFID via bastao antes do
#         SISBOV). Card "Brincagem com Bastão" (Hub de Brincagem,
#         slug 'brincagem') deixa de ter rota=None e passa a
#         apontar para 'brincagem_bastao.iniciar' - HUB DE
#         BRINCAGEM COMPLETO, todos os 3 cards com modulo de
#         verdade por tras. Nenhuma outra mudanca neste arquivo
#         (nenhum outro Hub, nenhuma imagem trocada).
#     v1.31.0: Sessao 077 cont. (22/09/2026, 18:30 -03) - Card
#         "Lançar GTA" (Hub de Entrada) RENOMEADO para "Vincular
#         GTA" e deixa de ter rota=None - passa a apontar para
#         'vincular_gta.iniciar_por_gta', o segundo caminho de
#         entrada do modulo (usuario escolhe a GTA primeiro,
#         depois a Data de Brincagem). O primeiro caminho
#         (Consulta Brincagem -> marca os animais -> escolhe a
#         GTA) continua acessivel so pelo botao dentro da propria
#         Consulta Brincagem, sem card proprio no Hub - decisao
#         de Benedito. Nenhuma outra mudanca neste arquivo.
#     v1.32.0: Sessao 079 (24/09/2026, 11:15 -03) - NOVO Hub de
#         Inventario (slug 'inventario'), aberto pelo item
#         "Inventario" do menu lateral (produtor_menu.html v1.6.0 -
#         mesmo padrao de Brincos/Utilitarios, sem card na Home).
#         3 cards do lado PRODUTOR (as outras 3 opcoes do legado -
#         Gerar Inventario Atual, Reimpressao Inventario e
#         Impressao Analitica - sao da Certificadora, fora deste
#         Hub, decisao de Benedito):
#           - Inventário Geral    -> 'inventario_geral.iniciar'
#                                    (modulo real construido nesta
#                                    sessao)
#           - Inventário Consulta -> rota=None (sessao futura)
#           - Inventário Raças    -> rota=None (sessao futura)
#         Imagens: _PLACEHOLDER generico nos 3 ate as artes
#         definitivas existirem - pasta prevista (Padrao de imagens
#         de Hub): img/hubs/inventario/. Nenhuma outra mudanca
#         neste arquivo (nenhum outro Hub, nenhuma rota).
#     v1.33.0: Sessao 080 (25/09/2026, 10:55 -03) - PIA (Planilha
#         de Identificacao Individual de Animais - Anexo XXIII).
#         Decisao de Benedito: "tudo relacionado as ENTRADAS fica
#         no Hub de Entrada" - card novo "PIA" entre "Reimpressao
#         Comunicado" e "Manejo e Rastreabilidade", abrindo o
#         NOVO sub-hub 'entrada-pia' (Hub dentro de Hub) com os 3
#         modos de impressao do legado GERAS:
#           - PIA por Período     -> 'pia_impressao.periodo_iniciar'
#           - PIA por Manejo      -> 'pia_impressao.manejo_iniciar'
#           - PIA por Comunicado  -> 'pia_impressao.comunicado_iniciar'
#         (modulo real construido nesta sessao - backend/routers/
#         pia_impressao.py). Imagens: _PLACEHOLDER ate as artes de
#         Benedito - pasta do Hub principal (img/hubs/entrada/),
#         Padrao de imagens de sub-hub. Nenhuma outra mudanca neste
#         arquivo.
#     v1.34.0: Sessao 080 (25/09/2026, 15:20 -03) - PIA em TELA
#         UNICA (sugestao de Benedito, aceita): o sub-hub
#         'entrada-pia' da v1.33.0 foi REMOVIDO - os 3 modos
#         (Periodo, Manejo, Comunicado) viraram ABAS de uma so
#         tela (pia_impressao.py v1.1.0 / pia.html). Menos cliques,
#         troca de modo sem voltar, uma unica selecao de
#         Propriedade e nenhuma arte extra. O card "PIA" do Hub de
#         Entrada passa a apontar direto para
#         'pia_impressao.iniciar' e recebe a arte definitiva de
#         Benedito (img/hubs/entrada/Pia.jpg). Nenhuma outra
#         mudanca neste arquivo.
#     v1.35.0: Sessao 080 (25/09/2026, 21:05 -03) - ARTES NOVAS de
#         Benedito + reorganizacao do NASCIMENTO ("tudo que for
#         Nascimento tem que ficar junto" - Benedito):
#           - Hub de Inventario: os 3 cards recebem as artes
#             definitivas (fim do _PLACEHOLDER), na pasta
#             img/hubs/inventario/ - Inventario_geral.jpg,
#             Inventario_consulta.jpg, Inventario_racas.jpg. Rotas
#             sem mudanca (Geral funcionando; Consulta e Racas
#             ainda rota=None).
#           - Card "Nascimento / Desmame" do Hub de Entrada deixa
#             de ter rota=None e passa a abrir o NOVO sub-hub
#             'entrada-nascimento' (Hub dentro de Hub), com 4
#             cards, todos rota=None (modulos ainda nao
#             construidos):
#               - Notificacao de Nascimentos (arte nova
#                 Nascto_notificacao.jpg)
#               - Planilha de Nascimento [PIA] (arte nova
#                 Nascto_pia.jpg)
#               - Nascimentos por Periodo      (MOVIDO do sub-hub
#               - Nascimento por Numero de       Manejo e
#                 Controle                        Rastreabilidade)
#             Imagens do sub-hub na pasta do Hub principal
#             (img/hubs/entrada/ - Padrao de imagens de sub-hub).
#           - Sub-hub 'entrada-consultas' (Manejo e
#             Rastreabilidade) fica com 2 cards: Alterar Dados
#             Animais e Relatorio de ERAS.
#     v1.36.0: Sessao 082 (29/09/2026, 17:05 -03) - Sub-hub
#         'entrada-nascimento' ganha, como 1o card, o card
#         "Brincagem Sequencial" (MESMA arte da Brincagem
#         Sequencial do Hub de Entrada - decisao de Benedito: o
#         usuario reconhece na hora qual e a finalidade),
#         apontando para 'brincagem_nascimento.iniciar' - modulo
#         real construido nas Sessoes 081/082 (backend/routers/
#         brincagem_nascimento.py, Brincagem de Nascimento/Desmame
#         no escritorio). Os outros 4 cards do sub-hub continuam
#         com rota=None. Nenhuma outra mudanca neste arquivo
#         (nenhum outro Hub, nenhuma imagem trocada).
#     v1.37.0: Sessao 084 (02/10/2026, 09:00 -03) - Sub-hub 'entrada-
#         nascimento': o card "Notificacao de Nascimentos" deixa de ter
#         rota=None e passa a abrir 'notificacao_nascimento.iniciar' -
#         modulo real (backend/routers/notificacao_nascimento.py,
#         Impressao e Reimpressao da Notificacao). Nenhuma outra mudanca.
#     v1.38.0: Sessao 084 (02/10/2026, 16:00 -03) - Sub-hub 'entrada-
#         nascimento': o card "Planilha de Nascimento [PIA]" deixa de ter
#         rota=None e passa a abrir 'pia_impressao.nascimento_iniciar' -
#         PIA de Nascimentos (pia_impressao.py v1.2.0). Nenhuma outra
#         mudanca.
#     v1.39.0: Sessao 084 (02/10/2026, 17:00 -03) - Sub-hub 'entrada-
#         nascimento': o card "Nascimentos por Periodo" deixa de ter
#         rota=None e passa a abrir 'nascimentos_periodo.iniciar' - relatorio
#         real (backend/routers/nascimentos_periodo.py). Nenhuma outra
#         mudanca.
#     v1.40.0: Sessao 084 (02/10/2026, 18:00 -03) - Sub-hub 'entrada-
#         nascimento': o card "Nascimento por Numero de Controle" deixa de
#         ter rota=None e passa a abrir 'nascimentos_periodo.controle_
#         iniciar' (mesmo blueprint do relatorio por Periodo). Nenhuma
#         outra mudanca.
#     v1.41.0: Sessao 085 (04/10/2026, 14:10 -03) - Novo card "Consulta por
#         Manejo" (backend/routers/consulta_manejo.py) em DOIS Hubs: 'entrada'
#         (escritorio, logo apos Consulta Brincagem) e 'brincagem' (campo, 4o
#         card). Mesmo modulo nos dois - o 'origem' em rota_params so diz ao
#         Voltar de qual Hub o usuario veio. Arte: img/hubs/entrada/
#         consulta_manejo.jpg e img/hubs/brincagem/consulta_manejo.jpg (a
#         mesma imagem copiada nas duas pastas - uma pasta por Hub principal).
#         Nenhuma outra mudanca neste arquivo.
#     v1.42.0: Sessao 087 (05/10/2026, 20:35 -03) - Novo card "Alterar Dados dos
#         Animais" (backend/routers/alterar_dados_animais.py) em DOIS Hubs:
#         'brincagem' (campo, logo apos Consulta Brincagem) e 'entrada'
#         (escritorio, ANTES de Vincular GTA - corrige-se antes de vincular).
#         Mesmo modulo nos dois - o 'origem' em rota_params so diz ao Voltar de
#         qual Hub o usuario veio. Arte (a mesma nos dois Hubs, fornecida por
#         Benedito): img/hubs/entrada/Alterar_Dado.jpg. Nenhuma outra mudanca.
#     v1.43.0: Sessao 088 (06/10/2026, 11:25 -03) - Novo sub-hub
#         'entrada-comunicados' (Hub dentro de Hub) com 4 cards: Gerar
#         Comunicado, Impressao Comunicado, Reimpressao Comunicado e PIA.
#         Todos reaproveitam as rotas e as artes que JA existem no Hub de
#         Entrada (mesma pasta de imagens do Hub principal - Padrao de
#         imagens de sub-hub) - nenhum modulo novo, nenhuma imagem nova.
#         O sub-hub e aberto pelo card "Gerar Comunicados" do Hub de
#         Entrada NOVO (backend/routers/hub_entrada_agrupado.py, rota
#         paralela /produtor/hub-novo/entrada). O Hub de Entrada atual
#         (slug 'entrada') NAO foi alterado - os 4 cards continuam nele.
#         Nenhuma outra mudanca neste arquivo.
#     v1.43.1: Sessao 088 (06/10/2026, 12:10 -03) - Corrigido o carimbo de
#         sessao da v1.43.0 (era "087 cont.", o certo e 088). So texto de
#         comentario - nenhuma mudanca de codigo, rota ou imagem.
#     v1.44.0: Sessao 090 (07/10/2026, 18:40 -03) - TROCA DEFINITIVA DOS HUBS.
#         Os enderecos /produtor/hub/entrada, /produtor/hub/entrada-
#         nascimento, /produtor/hub/entrada-comunicados e /produtor/hub/
#         brincagem passam a abrir as telas NOVAS (hub_entrada_agrupado.py,
#         v1.4.1) - por redirecionamento, na lista SLUGS_HUB_NOVO. Com
#         ?antigo=1 no endereco o Hub antigo abre como antes (e os cards
#         que levam a outro Hub antigo repassam o ?antigo=1). Com isso,
#         todo Voltar que ja apontava para esses enderecos acerta sozinho.
#         O dict HUBS NAO foi tocado. REVERSAO: devolver o hubs.py 1.43.1.
#         Nenhuma outra mudanca.
#     v1.45.0: Sessao 091 (08/10/2026, 18:20 -03) - /produtor/hub/brincos passa
#         a abrir a tela NOVA (slug 'brincos' entra em SLUGS_HUB_NOVO;
#         hub_entrada_agrupado.py v1.7.0). Com ?antigo=1 abre o Hub antigo.
#         O dict HUBS NAO foi tocado. REVERSAO: devolver o hubs.py 1.44.0.
#     v1.46.0: Sessao 091 (08/10/2026, 19:45 -03) - /produtor/hub/utilitarios e
#         /produtor/hub/inventario passam a abrir as telas NOVAS (slugs entram
#         em SLUGS_HUB_NOVO; hub_entrada_agrupado.py v1.8.0). Com ?antigo=1
#         abre o Hub antigo. O dict HUBS NAO foi tocado. REVERSAO: devolver o
#         hubs.py 1.45.0.
#     v1.47.0: Sessao 097 (15/10/2026, 13:40 -03) - Raças da Fazenda saiu do Hub de Utilitarios e entrou no Hub de Entrada, ao lado
#         de Manejo e Rastreabilidade (decisao do Benedito); imagem em img/hubs/entrada/racas.jpg.
#     v1.48.0: Sessao 128 (2026-11-16 11:55 -03) - AUDITORIA ETAPA 8b: os cards do Hub antigo (?antigo=1 e sub-hubs fora da tela nova) tambem somem quando o cargo nao tem acesso, igual ao Hub novo. REVERSAO: .bak_antes_etapa8b.
# =========================================================

from flask import Blueprint, render_template, redirect, url_for, session, request

from backend.routers.auth import redirecionar_home
from backend.routers.permissoes import caminho_permitido

# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
hubs = Blueprint('hubs', __name__)

# -------------------------------------------------------
# Caminho do placeholder temporario (v1.4.0) - reaproveitado em
# todos os cards novos ate cada arte definitiva ser gerada por
# Benedito. Ver changelog v1.4.0 acima.
# -------------------------------------------------------
_PLACEHOLDER = 'img/hubs/entrada/parceiros.png'

# -------------------------------------------------------
# v1.44.0 (Sessao 090): slugs que agora abrem a tela NOVA
# (hub_entrada_agrupado.py). Lista explicita de proposito: um Hub
# novo so entra na troca quando for colocado aqui. Com ?antigo=1
# no endereco, abre o Hub antigo (rede de seguranca).
# -------------------------------------------------------
SLUGS_HUB_NOVO = ('entrada', 'entrada-nascimento', 'entrada-comunicados', 'brincagem', 'brincos', 'utilitarios', 'inventario')


# -------------------------------------------------------
# Configuracao central de todos os Hubs. Chave = slug usado na
# URL (/produtor/hub/<slug>). Ver DESCRICAO no topo do arquivo
# para o formato de cada card e de cada Hub.
# -------------------------------------------------------
HUBS = {
    'entrada': {
        'titulo': 'Hub de Entrada',
        'tamanho_card': 'compacto',
        'cards': [
            {
                'titulo': 'GTA Compra',
                'imagem': 'img/hubs/entrada/gta_compra.png',
                'rota':   'gta_compra.nova',
            },
            {
                'titulo': 'Nascimento / Desmame',
                'imagem': 'img/hubs/entrada/nascimento_desmame.png',
                # v1.35.0: abre o sub-hub de Nascimento.
                'rota':   'hubs.ver',
                'rota_params': {'slug': 'entrada-nascimento'},
            },
            {
                'titulo': 'Parceiros / Fornecedores',
                'imagem': 'img/hubs/entrada/parceiros.png',
                'rota':   'parceiros_fornecedores.lista',
            },
            {
                'titulo': 'Brincagem Sequencial',
                'imagem': 'img/hubs/entrada/Brincagem_Sequencial.png',
                'rota':   'brincagem_sequencial.iniciar',
            },
            {
                'titulo': 'Consulta Brincagem',
                'imagem': 'img/hubs/entrada/Consulta_brincagem.jpg',
                # v1.29.0 (Sessao 061): modulo real construido -
                # backend/routers/brincagem_consulta.py.
                'rota':   'brincagem_consulta.iniciar',
                'rota_params': {'origem': 'entrada'},
            },
            {
                # v1.41.0 (Sessao 085): modulo real - backend/routers/
                # consulta_manejo.py (escritorio).
                'titulo': 'Consulta por Manejo',
                'imagem': 'img/hubs/entrada/consulta_manejo.jpg',
                'rota':   'consulta_manejo.iniciar',
                'rota_params': {'origem': 'entrada'},
            },
            {
                # v1.42.0 (Sessao 087): modulo real - backend/routers/alterar_dados_animais.py.
                'titulo': 'Alterar Dados dos Animais',
                'imagem': 'img/hubs/entrada/Alterar_Dado.jpg',
                'rota':   'alterar_dados_animais.iniciar',
                'rota_params': {'origem': 'entrada'},
            },
            {
                'titulo': 'Vincular GTA',
                'imagem': 'img/hubs/entrada/lancar_gta.jpg',
                # v1.31.0 (Sessao 077): modulo real construido -
                # backend/routers/vincular_gta.py. Renomeado de
                # "Lançar GTA" - a arte definitiva ja trazia o
                # titulo "VINCULAR GTA/BRINCAGEM" embutido na
                # imagem, o texto do card estava desatualizado.
                'rota':   'vincular_gta.iniciar_por_gta',
            },
            {
                'titulo': 'Gerar Comunicado',
                'imagem': 'img/hubs/entrada/gerar_comunicado.jpg',
                'rota':   'comunicado_entrada.iniciar',
            },
            {
                'titulo': 'Impressão Comunicado',
                'imagem': 'img/hubs/entrada/impressao_comunicado.jpg',
                'rota':   'impressao_comunicado.iniciar',
            },
            {
                'titulo': 'Reimpressão Comunicado',
                'imagem': 'img/hubs/entrada/reimpressao_comunicado.jpg',
                'rota':   'reimpressao_comunicado.iniciar',
            },
            {
                # v1.34.0 (Sessao 080): tela unica com 3 abas
                # (Periodo/Manejo/Comunicado) - pia_impressao.py.
                'titulo': 'PIA - Planilha de Identificação Individual',
                'imagem': 'img/hubs/entrada/Pia.jpg',
                'rota':   'pia_impressao.iniciar',
            },
            {
                'titulo': 'Manejo e Rastreabilidade',
                'imagem': 'img/hubs/entrada/manejo_rastreabilidade.jpg',
                'rota':   'hubs.ver',
                'rota_params': {'slug': 'entrada-consultas'},
            },
            {
                'titulo': 'Raças da Fazenda',
                'imagem': 'img/hubs/entrada/racas.jpg',
                'rota':   'racas.iniciar',
            },
        ],
    },
    'entrada-consultas': {
        'titulo': 'Manejo e Rastreabilidade',
        'tamanho_card': 'compacto',
        'cards': [
            {
                'titulo': 'Alterar Dados Animais',
                'imagem': 'img/hubs/entrada/alterar_dados_animais.jpg',
                'rota':   None,
            },
            # v1.35.0: os 2 cards de Nascimento foram MOVIDOS para o
            # sub-hub 'entrada-nascimento'.
            {
                'titulo': 'Relatório de ERAS',
                # v1.26.0 (Sessao 055): rota real - modulo
                # relatorio_eras.py construido e testado.
                'imagem': 'img/hubs/entrada/relatorio_eras.jpg',
                'rota':   'relatorio_eras.iniciar',
            },
        ],
    },
    # v1.35.0 (Sessao 080): sub-hub de Nascimento - tudo que for
    # Nascimento fica junto (Benedito). Imagens na pasta do Hub
    # principal (img/hubs/entrada/). Os demais modulos ainda nao
    # foram construidos (rota=None).
    'entrada-nascimento': {
        'titulo': 'Nascimento / Desmame',
        'tamanho_card': 'padrao',
        'cards': [
            {
                # v1.36.0 (Sessao 082): a Brincagem de Nascimento usa o
                # MESMO card (mesma arte) da Brincagem Sequencial do
                # Hub de Entrada - o usuario reconhece a finalidade.
                # Modulo real: backend/routers/brincagem_nascimento.py.
                'titulo': 'Brincagem Sequencial',
                'imagem': 'img/hubs/entrada/Brincagem_Sequencial.png',
                'rota':   'brincagem_nascimento.iniciar',
            },
            {
                'titulo': 'Notificação de Nascimentos',
                'imagem': 'img/hubs/entrada/Nascto_notificacao.jpg',
                # v1.37.0 (Sessao 084): modulo real - Impressao/Reimpressao.
                'rota':   'notificacao_nascimento.iniciar',
            },
            {
                'titulo': 'Planilha de Nascimento [PIA]',
                'imagem': 'img/hubs/entrada/Nascto_pia.jpg',
                # v1.38.0 (Sessao 084): modulo real - PIA por Notificacao.
                'rota':   'pia_impressao.nascimento_iniciar',
            },
            {
                'titulo': 'Nascimentos por Período',
                'imagem': 'img/hubs/entrada/nascimentos_por_periodo.jpg',
                # v1.39.0 (Sessao 084): relatorio real.
                'rota':   'nascimentos_periodo.iniciar',
            },
            {
                'titulo': 'Nascimento por Número de Controle',
                'imagem': 'img/hubs/entrada/nascimento_por_numero_controle.jpg',
                # v1.40.0 (Sessao 084): relatorio real.
                'rota':   'nascimentos_periodo.controle_iniciar',
            },
        ],
    },
    # v1.43.0 (Sessao 088): sub-hub dos Comunicados de Entrada,
    # aberto pelo card "Gerar Comunicados" do Hub de Entrada NOVO
    # (hub_entrada_agrupado.py). Rotas e artes reaproveitadas do Hub
    # 'entrada' - imagens na pasta do Hub principal (img/hubs/entrada/).
    'entrada-comunicados': {
        'titulo': 'Comunicados de Entrada',
        'tamanho_card': 'padrao',
        'cards': [
            {
                'titulo': 'Gerar Comunicado',
                'imagem': 'img/hubs/entrada/gerar_comunicado.jpg',
                'rota':   'comunicado_entrada.iniciar',
            },
            {
                'titulo': 'Impressão Comunicado',
                'imagem': 'img/hubs/entrada/impressao_comunicado.jpg',
                'rota':   'impressao_comunicado.iniciar',
            },
            {
                'titulo': 'Reimpressão Comunicado',
                'imagem': 'img/hubs/entrada/reimpressao_comunicado.jpg',
                'rota':   'reimpressao_comunicado.iniciar',
            },
            {
                'titulo': 'PIA - Planilha de Identificação Individual',
                'imagem': 'img/hubs/entrada/Pia.jpg',
                'rota':   'pia_impressao.iniciar',
            },
        ],
    },
    'brincagem': {
        'titulo': 'Hub de Brincagem',
        'tamanho_card': 'padrao',
        'cards': [
            {
                'titulo': 'Brincagem com Leitor',
                # v1.27.0 (Sessao 057): arte definitiva - antes
                # era o _PLACEHOLDER generico (Parceiros).
                'imagem': 'img/hubs/brincagem/brincagem_leitor.jpg',
                # v1.28.0 (Sessao 057): modulo real construido -
                # backend/routers/brincagem_leitor.py.
                'rota':   'brincagem_leitor.iniciar',
            },
            {
                'titulo': 'Brincagem com Bastão',
                # v1.27.0 (Sessao 057): arte definitiva - antes
                # era o _PLACEHOLDER generico (Parceiros).
                'imagem': 'img/hubs/brincagem/brincagem_bastao.jpg',
                # v1.30.0 (Sessao 077): modulo real construido -
                # backend/routers/brincagem_bastao.py.
                'rota':   'brincagem_bastao.iniciar',
            },
            {
                'titulo': 'Consulta Brincagem',
                # v1.27.0 (Sessao 057): arte definitiva - antes
                # era o _PLACEHOLDER generico (Parceiros).
                'imagem': 'img/hubs/brincagem/consulta_brincagem.jpg',
                # v1.29.0 (Sessao 061): modulo real construido -
                # backend/routers/brincagem_consulta.py. Mesmo
                # modulo do card irmao no Hub de Entrada, so muda
                # o 'origem' (para o botao Voltar).
                'rota':   'brincagem_consulta.iniciar',
                'rota_params': {'origem': 'brincagem'},
            },
            {
                # v1.42.0 (Sessao 087): modulo real - backend/routers/alterar_dados_animais.py.
                'titulo': 'Alterar Dados dos Animais',
                'imagem': 'img/hubs/entrada/Alterar_Dado.jpg',
                'rota':   'alterar_dados_animais.iniciar',
                'rota_params': {'origem': 'brincagem'},
            },
            {
                # v1.41.0 (Sessao 085): mesmo modulo do card irmao no Hub
                # de Entrada, so muda o 'origem' (Voltar) - pessoal de campo.
                'titulo': 'Consulta por Manejo',
                'imagem': 'img/hubs/brincagem/consulta_manejo.jpg',
                'rota':   'consulta_manejo.iniciar',
                'rota_params': {'origem': 'brincagem'},
            },
        ],
    },
    'brincos': {
        'titulo': 'Hub de Brincos',
        'tamanho_card': 'compacto',
        'cards': [
            {
                'titulo': 'Fornecedor de Brincos',
                'imagem': 'img/hubs/brincos/1-fornecedor.png',
                'rota':   'brincos_fornecedor.listar',
            },
            {
                'titulo': 'Entrada de Brincos',
                'imagem': 'img/hubs/brincos/2-entrada.png',
                'rota':   'brincos_entrada.iniciar',
            },
            {
                'titulo': 'Brincos Disponíveis',
                'imagem': 'img/hubs/brincos/3-dispo.png',
                'rota':   'brincos_disponiveis.iniciar',
            },
            {
                'titulo': 'Cancelamento de Brincos',
                'imagem': 'img/hubs/brincos/4-cancel.png',
                'rota':   'brincos_cancelamento.iniciar',
            },
            {
                'titulo': 'Brincos Saídas',
                'imagem': 'img/hubs/brincos/5-saida.png',
                'rota':   'brincos_saidas.iniciar',
            },
            {
                'titulo': 'Relatório Resumo',
                'imagem': 'img/hubs/brincos/6_resumo.png',
                'rota':   'brincos_relatorio_resumo.iniciar',
            },
            {
                'titulo': 'Relatório N.Fiscais',
                'imagem': 'img/hubs/brincos/7_N_Fiscais.png',
                'rota':   'brincos_relatorio_nfiscais.iniciar',
            },
            {
                'titulo': 'Histórico',
                'imagem': 'img/hubs/brincos/08_historico.png',
                'rota':   'brincos_cancelamento.documentos_iniciar',
            },
        ],
    },
    'utilitarios': {
        'titulo': 'Hub de Utilitários',
        'tamanho_card': 'padrao',
        'cards': [
            {
                'titulo': 'Operações Recentes',
                'imagem': 'img/hubs/utilitarios/1-operacoes.jpg',
                'rota':   'operacoes_recentes.iniciar',
            },
            {
                'titulo': 'Backup e Restore',
                'imagem': 'img/hubs/utilitarios/2-bkp_restaure.jpg',
                'rota':   'backup_restore.iniciar',
            },
        ],
    },
    # v1.32.0 (Sessao 079): Hub de Inventario - lado Produtor.
    # v1.35.0 (Sessao 080): artes definitivas em img/hubs/inventario/.
    'inventario': {
        'titulo': 'Hub de Inventário',
        'tamanho_card': 'padrao',
        'cards': [
            {
                'titulo': 'Inventário Geral',
                'imagem': 'img/hubs/inventario/Inventario_geral.jpg',
                # Modulo real - backend/routers/inventario_geral.py.
                'rota':   'inventario_geral.iniciar',
            },
            {
                'titulo': 'Inventário Consulta',
                'imagem': 'img/hubs/inventario/Inventario_consulta.jpg',
                'rota':   None,
            },
            {
                'titulo': 'Inventário Raças',
                'imagem': 'img/hubs/inventario/Inventario_racas.jpg',
                'rota':   None,
            },
        ],
    },
}


# -------------------------------------------------------
# Rota: /produtor/hub/<slug> — tela generica de Hub, compartilhada
# por todos os Hubs cadastrados no dict HUBS acima. Requer perfil
# PRODUTOR ou FAZENDA. Slug desconhecido redireciona para a Home
# (nunca 404 feio para o usuario).
# -------------------------------------------------------
@hubs.route('/produtor/hub/<slug>')
def ver(slug):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    perfil = session.get('usuario_perfil')
    if perfil not in ('PRODUTOR', 'FAZENDA'):
        return redirecionar_home(perfil)

    # v1.44.0: troca definitiva - abre a tela nova, salvo ?antigo=1.
    antigo = request.args.get('antigo') == '1'
    if slug in SLUGS_HUB_NOVO and not antigo:
        return redirect(url_for('hub_entrada_agrupado.ver', slug=slug))

    hub = HUBS.get(slug)
    if hub is None:
        return redirect(url_for('auth.produtor_home'))

    cards = []
    for card in hub['cards']:
        if card['rota']:
            params = dict(card.get('rota_params', {}))
            # v1.44.0: dentro do Hub antigo, os cards que levam a outro Hub
            # antigo mantem o ?antigo=1 (senao cairiam na tela nova).
            if antigo and card['rota'] == 'hubs.ver':
                params['antigo'] = 1
            url = url_for(card['rota'], **params)
            if not caminho_permitido(url.split('?')[0]):   # v1.48.0 - cargo sem acesso nao ve o card
                continue
        else:
            url = None
        cards.append({
            'titulo': card['titulo'],
            'imagem': card['imagem'],
            'url':    url,
        })

    return render_template('produtor/hub_generico.html',
        titulo_hub     = hub['titulo'],
        cards          = cards,
        tamanho_card   = hub.get('tamanho_card', 'padrao'),
        usuario_nome   = session.get('usuario_nome'),
        usuario_perfil = session.get('usuario_perfil'),
        cor_primaria   = session.get('cor_primaria', '#D4370A'),
        nome_sistema   = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo     = None
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\hubs.py
# =========================================================
