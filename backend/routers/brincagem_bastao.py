# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\brincagem_bastao.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-22 13:55 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.24.0
# v1.24.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (7 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.23.0: Sessao 122 (2026-11-12 17:40 -03) - Auditoria Etapa 3 (itens 2 e 3): a trava da Propriedade vale para Compra e Nascimento (mesmo brinco lido em 2 aparelhos nao grava 2 vezes); Especie/Raca conferidas (antes erro 500 com dado adulterado). REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Modulo Brincagem com Bastao (Sessao 077) - mesma estrutura
#     do modulo irmao brincagem_leitor.py (Opcao 2, sem GTA
#     vinculada, id_gta fica NULL), com UMA diferenca real: antes
#     de ler o SISBOV (codigo de barras do brinco visual), o
#     usuario le primeiro o RFID (chip eletronico) com o bastao
#     leitor - as duas leituras sao vinculadas ao mesmo registro
#     em tb_5001_brincagem (colunas rfid + sisbov, ambas
#     preenchidas). Decisao fechada com Benedito (Sessao 077):
#     "utilizaremos a estrutura do Brincagem com Leitor e
#     incluiremos a Leitura com o Bastao, o restante e igual."
#
#     FLUXO (3 telas, igual ao Leitor):
#       1. /produtor/brincagem-bastao/iniciar - resolve
#          Propriedade E Produtor via
#          auth.buscar_pares_propriedade_produtor() (Padrao
#          Reutilizavel N.1). Com 1 unico par, pula DIRETO para
#          a Tela 02.
#       2. /produtor/brincagem-bastao/selecao - Tela 02: igual a
#          brincagem_leitor_selecao.html, so nome/rotas mudam.
#          O destino do Voltar (url_voltar) ja nasce calculado
#          pelo numero real de pares (Regra de Ouro #9), sem
#          precisar do ciclo de bug->correcao que o modulo Leitor
#          passou na Sessao 076/077 - licao aplicada direto aqui.
#       3. /produtor/brincagem-bastao/leitura - Tela de Leitura:
#          cursor sempre no RFID primeiro. RFID completo (15
#          digitos, ou Enter/Tab/blur) dispara checagem de
#          duplicidade via AJAX (rota checar_rfid() abaixo) e,
#          se livre, libera e move o foco para o SISBOV. SISBOV
#          completo dispara a MESMA checagem que o Leitor ja usa
#          (rota checar_sisbov() abaixo, reaproveitada sem
#          alteracao) e libera o resto da tela (Especie -> Raca
#          -> Sexo -> Nro Meses -> Nascimento -> Lote -> Peso ->
#          Gravar, toda a cadeia de avanco automatico de foco
#          fechada com Benedito na Sessao 077 - ver
#          brincagem_leitor_leitura.html v1.5.0, mesmo padrao
#          copiado aqui). Gravar (AJAX, rota gravar() abaixo)
#          grava rfid E sisbov no mesmo registro; APOS o sucesso,
#          os DOIS campos (RFID e SISBOV) limpam sozinhos - unica
#          diferenca do Leitor, onde so o SISBOV limpa (aqui os
#          dois sao sempre diferentes a cada animal, o Nro Meses/
#          Nascimento/Lote/Peso continuam mantendo o valor
#          anterior, igual ao Leitor).
#
#     CONTADOR "GRAVADOS" (v1.1.0): conta SO os registros desta
#     Propriedade NA Data de Brincagem da tela - mesma regra e
#     mesma funcao (copia local) do Leitor v1.4.0,
#     _contar_gravados_na_data().
#
#     VALIDACAO DE DUPLICIDADE:
#       - SISBOV: EXATAMENTE a mesma checagem do Leitor - 3
#         tabelas (tb_2001_entradas, tb_5001_brincagem com
#         sts=False, tb_7002_pia).
#       - RFID (NOVO): SO 2 tabelas - tb_2001_entradas.rfid e
#         tb_5001_brincagem.rfid (sts=False). Confirmado com
#         Benedito (Sessao 077): tb_7002_pia NAO tem coluna rfid
#         (ver model real, tb_7002_pia.py), entao fica de fora
#         desta checagem.
#       Ambas as tentativas bloqueadas (RFID ou SISBOV duplicado)
#       sao gravadas em tb_5003_rejeicoes_brincagem, com o motivo
#       correspondente - mesma tabela que o Leitor ja usa,
#       reaproveitada sem mudanca de estrutura.
#
#     MANEJO (v1.4.0): gravado como os 6 ULTIMOS DIGITOS do
#     SISBOV - mesma regra do Leitor v1.7.0 e da Entrada de
#     Brincos. Ate a v1.3.0 era gravado vazio (manejo=None).
#
#     CATALOGOS/CONSTANTES: identicos ao Leitor (Especie/Raca via
#     as mesmas fontes, DIAS_POR_MES=30, PESO_MAXIMO_KG=1000) -
#     ver ATENCAO em brincagem_leitor.py sobre a aproximacao de
#     30 dias/mes, que vale igual aqui.
#
#     v1.0.0: Criacao do modulo (Sessao 077, 22/09/2026, 13:55
#         -03).
#     v1.1.0: Sessao 078 (23/09/2026, 17:15 -03) - BUG REAL
#         apontado por Benedito em teste real (mesmo bug do
#         Leitor, corrigido junto em brincagem_leitor.py v1.4.0):
#         o contador GRAVADOS somava TODAS as brincagens da
#         Propriedade, de qualquer data. Mudancas:
#           - NOVA funcao _contar_gravados_na_data() - conta por
#             Propriedade + Data de Brincagem.
#           - leitura(): converte a Data de Brincagem da URL
#             (dd/mm/aaaa) e usa a funcao nova. Data incorreta
#             na URL volta para a Tela 02.
#           - gravar(): usa a funcao nova, contando ANTES do
#             db.commit() (regra da Sessao 078), com db.flush()
#             antes para o animal recem-gravado entrar na conta.
#         Nenhuma outra rota alterada.
#     v1.2.0: Sessao 078 (23/09/2026, 18:40 -03) - BUG REAL
#         apontado por Benedito em teste real (RFID digitado no
#         campo do SISBOV foi aceito ate Gravar). Regra fechada:
#           - SISBOV: NOVA _validar_sisbov() - duplicidade +
#             existe no estoque da Propriedade (tb_7017) + esta
#             disponivel (saidas, comunicado e reserva em branco)
#             + NUNCA igual ao RFID lido.
#           - RFID: NOVA _validar_rfid() - livre so se nao estiver
#             no rebanho vivo (tb_2001) nem numa brincagem
#             pendente (tb_5001 sts=False); o alerta mostra o
#             SISBOV ao qual o RFID ja esta vinculado. A tb_7017
#             NAO e consultada para o RFID (chip reutilizavel - o
#             historico antigo fica la). Checagem de "par" RFID x
#             SISBOV descartada: o casamento nasce na brincagem.
#           - checar_sisbov() passa a receber tambem o rfid lido.
#           - Respostas AJAX trazem 'mensagem' (texto do alerta),
#             mostrado pela tela (brincagem_bastao_leitura.html
#             v1.4.0). gravar() reconfere tudo no servidor.
#         _rfid_duplicado() deixa de ser usada (substituida por
#         _validar_rfid()), mas continua no arquivo, sem mudanca.
#     v1.3.0: Sessao 078 (23/09/2026, 19:15 -03) - Alerta de
#         SISBOV ja usado passa a mostrar ONDE o brinco esta
#         (rebanho ou brincagem pendente) e o RFID vinculado a
#         ele, se houver (pedido de Benedito - simetrico ao
#         alerta do RFID). NOVA funcao _mensagem_sisbov_
#         duplicado() (copia local da mesma do Leitor v1.6.0),
#         chamada por _validar_sisbov(). Nenhuma mudanca de regra
#         de bloqueio - so o texto. Template sem mudanca.
#     v1.4.0: Sessao 080 (25/09/2026, 15:50 -03) - BUG REAL achado
#         na 1a impressao da PIA (coluna Manejo vazia): gravar()
#         gravava manejo=None na tb_5001 (o Vincular GTA copiava
#         o vazio para tb_2001/tb_2017/tb_7002). Agora grava
#         manejo = 6 ULTIMOS DIGITOS do SISBOV (constante
#         TAMANHO_MANEJO) - mesma correcao do Leitor v1.7.0.
#         Nenhuma outra mudanca.
#     v1.5.0: Sessao 083 (30/09/2026, 16:49 -03) - PACOTE 3B: o
#         Bastao recebe o Pacote 3A do Leitor (brincagem_leitor.py
#         v1.8.0, validado por Benedito), com as MESMAS regras
#         (Sessao 082) e mantendo a diferenca real do Bastao (RFID
#         lido antes do SISBOV):
#           - Tela 02 com 3 campos OBRIGATORIOS: Tipo de Entrada
#             (Compra / Nascimento - lista fixa de regras_sisbov.py),
#             Data de Brincagem e Brincos. selecao() manda a lista.
#           - leitura(): exige o Tipo (invalido/ausente volta para a
#             Tela 02); contador GRAVADOS por Data + TIPO; no
#             Nascimento mostra o Numero de Controle (NAS) aberto da
#             data, se existir, e a regra da Cota Hilton.
#           - gravar(): Data de Brincagem OBRIGATORIA no servidor;
#             grava tipo_entrada; no Nascimento RESERVA o NAS no 1o
#             animal da Propriedade + Data (ou usa o aberto) e
#             atualiza a quantidade do Controle, na MESMA transacao
#             do animal (backend/utils/gravacao_nascimento.py).
#             Resposta traz 'controle' e 'controle_novo'.
#           - _contar_gravados_na_data() ganha o parametro
#             tipo_entrada.
#         SEGURANCA (Pacote Seguranca, aprovado por Benedito para
#         o Bastao ja nascer protegido): NOVA funcao
#         _propriedade_do_usuario() - a Propriedade tem de ser de um
#         par do usuario logado E do Produtor da sessao (mesma regra
#         de brincagem_consulta.py v2.11.1). Aplicada em selecao(),
#         leitura(), checar_rfid(), checar_sisbov() e gravar().
#         Validacoes de RFID e SISBOV (duplicidade/estoque/
#         disponibilidade) SEM mudanca - valem igual para os 2 tipos.
#     v1.6.0: Sessao 084 (01/10/2026, 23:10 -03) - O BRETE ENXERGA O
#         NASCIMENTO LANCADO PELO ESCRITORIO (mesmo desenho do Leitor
#         v1.9.1, mantendo o RFID):
#           - Tipo Nascimento: ler o RFID de um animal lancado pelo
#             escritorio (mesma Data de Brincagem) NAO bloqueia -
#             devolve os dados do lancamento (conferencia). Depois o
#             SISBOV lido tem de ser o do animal; se for outro, avisa
#             qual era o esperado.
#           - RFID novo + SISBOV de animal lancado ainda SEM RFID:
#             tambem confere, e o RFID lido passa a ser do animal
#             (tb_2001 e tb_2017).
#           - NOVA rota conferir(): marca tb_2001.conferido_brete =
#             TRUE (+ conferido_em) e devolve Lancados/Conferidos/
#             Faltam do NAS. Nao cria animal.
#           - leitura(): manda a lista de NAS lancados na data, com
#             os brincos, para o painel da tela.
#           - checar_rfid()/checar_sisbov(): passam a receber
#             tipo_entrada e data_brincagem. Brinco ja conferido
#             continua bloqueado; lancado em OUTRA data avisa a data.
#         Nenhuma mudanca em gravar() nem nas validacoes dos demais
#         casos.
#     v1.6.1: Sessao 084 (01/10/2026, 23:45 -03) - Tela 02: ao escolher o
#         Tipo de Entrada, a tela mostra as BRINCAGENS EM ABERTO daquele
#         tipo (lidas no brete aguardando fechamento e, no Nascimento, as
#         Notificacoes NAS do escritorio com conferencia pendente).
#         Clicar numa delas preenche a Data de Brincagem. selecao() manda
#         'abertas'; NOVA funcao _brincagens_em_aberto(). Nenhuma outra
#         mudanca.
#     v1.6.2: Sessao 084 (01/10/2026, 23:59 -03) - leitura(): no modo
#         lancamento, manda tambem 'extras' (brincos lidos nesta Data e
#         Tipo que NAO estao no lancamento do escritorio), para o quadro
#         lateral mostra-los. Nenhuma outra mudanca.
#     v1.7.0: Sessao 084 (02/10/2026, 12:00 -03) - BRINCO LIDO NO BRETE QUE NAO ESTAVA
#         NO LANCAMENTO ENTRA DIRETO NA NOTIFICACAO (decisao de Benedito:
#         o animal nasceu na mesma Data de Brincagem mas nao foi avisado ao
#         escritorio - integrar ja no brete evita retrabalho e outro NAS):
#           - gravar(): Tipo Nascimento + Notificacao do escritorio da MESMA
#             Data ainda NAO impressa -> o animal e gravado na Notificacao
#             (cadeia completa, ja conferido) por gravacao_nascimento.py
#             v1.1.0 (integrar_animal_na_notificacao). Nao cria leitura
#             pendente nem reserva NAS novo. Resposta traz 'integrado',
#             'controle', 'total_lancado', 'conferidos' e 'faltam'.
#           - Notificacao ja IMPRESSA nunca recebe animal: segue o fluxo de
#             sempre (Controle novo).
#           - Tela 02 (brincagens em aberto) e painel da leitura: so
#             Notificacoes NAO impressas; Notificacao totalmente conferida
#             continua aparecendo (aceita novos animais) ate ser impressa.
#         Validacoes do SISBOV/RFID e a conferencia SEM mudanca.
#     v1.7.1: Sessao 084 (02/10/2026, 21:00 -03) - conferir(): quando o
#         lancamento do escritorio nao tinha RFID e o RFID lido passa a ser
#         do animal, ele agora vai TAMBEM para a tb_7017 (decisao de
#         Benedito) e, por consistencia, para a tb_3008 (saida do brinco),
#         alem da tb_2001 e da tb_2017. So preenche onde o RFID esta vazio.
#         Nenhuma outra mudanca.
#     v1.8.0: Sessao 084 (02/10/2026, 22:00 -03) - PESO NO BRETE DO NASCIMENTO
#         (decisao de Benedito: o peso so e validado no brete): ao conferir
#         um animal lancado pelo escritorio (conferir()) ou integra-lo a
#         Notificacao (gravar()), o peso digitado vira a pesagem de
#         SEQUENCIA 1 do animal na tb_4003_pesos, na Data de Brincagem
#         (backend/utils/pesagem.py). conferir() passa a receber 'peso'
#         (opcional, maximo 1000 kg). Nenhuma outra mudanca.
#     v1.9.0: Sessao 084 (02/10/2026, 19:20 -03) - DATA DA BRINCAGEM DO NASCIMENTO COM
#         MAIS DE 30 DIAS E BLOQUEADA (decisao de Benedito; regra unica em
#         regras_sisbov.py v1.3.0, a mesma do escritorio):
#           - gravar(): Tipo Nascimento com Data de mais de 30 dias recusa o
#             animal novo (erro na tela). Vale tambem para o brinco que
#             integraria uma Notificacao.
#           - leitura(): data antiga so entra na tela de leitura se houver
#             Notificacao do escritorio ainda NAO impressa nessa data (para
#             poder CONFERIR); sem isso volta para a Tela 02 com o aviso.
#           - selecao(): mostra o aviso quando volta da leitura (?erro=
#             data_vencida).
#           - conferir() NAO muda: conferir um animal ja lancado pelo
#             escritorio continua liberado em qualquer data (senao a
#             Notificacao antiga ficaria presa e nao poderia ser impressa).
#         Compra e demais tipos SEM mudanca.
#     v1.10.0: Sessao 087 (05/10/2026, 16:00 -03) - CONFERENCIA NO BRETE DA
#             GTA DE COMPRA LANCADA PELO ESCRITORIO + PESO OBRIGATORIO
#             (pedidos de Benedito, testes do Pacote 087; mesmo desenho do
#             brincagem_leitor.py v1.14.0).
#               - Tipo COMPRA: a Tela 02 lista as GTAs lancadas pela Brincagem
#                 Sequencial com conferencia pendente; clicar numa GTA abre a
#                 Leitura SO dela (parametro id_gta). O RFID lido que ja esta
#                 vinculado a um brinco de OUTRA GTA e barrado (checar_rfid);
#                 o SISBOV lido tem de ser de um brinco DESTA GTA e, se ele ja
#                 tem RFID, o mesmo lido (checar_sisbov). conferir() marca
#                 tb_2001.conferido_brete, grava o RFID lido onde estava vazio
#                 (mesmas tabelas do Nascimento), grava o peso na tb_4003
#                 (origem BRETE_COMPRA) e devolve 'encerrada' ao conferir o
#                 ULTIMO brinco - a GTA encerra sozinha e nao aceita mais leitura.
#                 Regras compartilhadas com o Leitor em backend/utils/
#                 conferencia_compra.py v1.0.0.
#               - PESO OBRIGATORIO em toda gravacao/conferencia do brete
#                 (gravar() e conferir(), qualquer tipo): vazio, zero ou acima
#                 de 1.000 kg e recusado.
#               - A leitura LIVRE da Compra (sem GTA escolhida) NAO mudou.
#             Nenhuma outra mudanca.
#     v1.10.1: Sessao 087 (05/10/2026, 17:29 -03) - LOTE LIBERADO NA CONFERENCIA
#             DA GTA DE COMPRA (pedido de Benedito): conferir() passa a receber o
#             campo lote e grava na tb_2001 antes da pesagem (a Sequencial nao
#             grava lote - so o brete sabe onde vai colocar os animais - e o
#             brete pode trocar um lote que ja exista). Maximo 30 caracteres.
#             Conferencia do Nascimento (NAS) NAO mudou. Nenhuma outra mudanca.
#     v1.10.2: Sessao 087 (05/10/2026, 17:46 -03) - DUAS REGRAS DE BENEDITO: (1) o PESO
#             do brete tem de ser SUPERIOR a 100 kg em toda gravacao/conferencia
#             (conferencia_compra.ler_peso_brete); (2) na conferencia da GTA de
#             Compra o LOTE e OBRIGATORIO (sem lote o brinco nao e conferido).
#             Nenhuma outra mudanca.
#     v1.10.3: Sessao 087 (2026-10-05 17:58 -03) - LOTE OBRIGATORIO EM TODO O BRETE (pedido de Benedito,
#             mesmo desenho do peso): gravar() (leitura livre, Compra e Nascimento) e
#             conferir() (GTA de Compra E Nascimento/NAS) recusam sem lote. Na
#             conferencia do Nascimento o lote tambem passa a ser digitado/trocado
#             pelo brete (antes vinha travado do lancamento do escritorio) e grava na
#             tb_2001 antes da pesagem. Maximo 30 caracteres, maiuscula. Nenhuma outra
#             mudanca.
#     v1.10.4: Sessao 087 (2026-10-05 18:07 -03) - DATA BRINCAGEM DA GTA DE COMPRA (pedido de Benedito):
#             a Tela 02 deixou de preencher a data ao clicar na GTA (induzia ao erro); o
#             usuario DIGITA a Data Brincagem e leitura() so abre a GTA se ela for IGUAL
#             a lancada pelo escritorio - senao volta para a Tela 02 com o aviso (sem
#             mostrar a data certa; ela esta na lista). Nenhuma outra mudanca.
#     v1.11.0: Sessao 087 (05/10/2026, 19:00 -03) - O BRETE PREVALECE (acordo com Benedito
#             apos o caso dos brincos 047-052, barrados como "ja utilizados" so porque o
#             formulario da Sequencial da GTA AMA111115 fora aberto - "imagine ficar 30
#             minutos no Brete esperando"). (1) A RESERVA da Sequencial nunca mais bloqueia o
#             brete (nem a valida, nem a vencida - antes valia para sempre, pois o prazo
#             reservado_ate nao era olhado); a Sequencial e que se adapta (v1.17.0). (2)
#             Brinco que o escritorio JA SALVOU numa GTA de Compra e ainda nao foi conferido
#             ganha o aviso "Brinco ... lancado pelo escritorio na GTA X. Escolha a GTA X na
#             Selecao para conferir." no lugar do generico (SISBOV e RFID). Nenhuma outra mudanca.
#     v1.12.0: Sessao 090 (08/10/2026, 08:50 -03) - FAZENDA EM USO (Lote 4):
#             FAZENDA EM USO (Regra de Ouro #13): a tela "Selecionar Propriedade" deixa
#             de aparecer quando ha fazenda em uso (auth.resolver_fazenda_em_uso).
#               - iniciar(): com fazenda em uso, abre a Tela 02 direto nela.
#               - VOLTAR (Regra #9): da Tela 02 vai ao Hub de Brincagem NOVO
#                 (/produtor/hub-novo/brincagem); so volta para a selecao quem
#                 tem 2+ pares e nenhuma fazenda em uso.
#               - TRAVA em _propriedade_do_usuario(): Propriedade diferente da
#                 fazenda em uso (outra aba) = negado. As telas (selecao e
#                 leitura) mandam para o iniciar() por _negado(); as chamadas
#                 do brete (checar, gravar, conferir) respondem 403 SEM gravar
#                 e com mensagem que pede para reabrir pelo Hub.
#             Nenhuma mudanca nas regras de leitura, validacao, peso, lote,
#             conferencia e gravacao. Templates inalterados.
#     v1.13.0: Sessao 094 (12/10/2026, 18:30 -03) - CONTADOR GRAVADOS NA CONFERENCIA:
#             Nascimento lancado pelo escritorio: a conferencia nao cria linha em tb_5001,
#             entao o contador GRAVADOS (nesta data e tipo) ficava em 0. Agora soma os brincos
#             CONFERIDOS das Notificacoes (NAS, nao impressas) da data. A rota conferir()
#             devolve total_gravados e a tela (sem GTA) atualiza o contador. Compra por GTA
#             continua mostrando CONFERIDOS da GTA. REVERSAO: devolver .bak_antes_contador.
#     v1.14.0: Sessao 094 (12/10/2026, 18:50 -03) - ENCERRAMENTO NO NASCIMENTO: a rota
#             conferir() devolve 'encerrada' tambem para a Notificacao de Nascimento (todos
#             os brincos lancados conferidos); a tela mostra "BRINCAGEM ENCERRADA".
#             REVERSAO: devolver .bak_antes_contador.
#     v1.15.0: Sessao 094 (12/10/2026, 20:15 -03) - AUDITORIA, PAR DO LEITOR: (1) MANEJO:
#             gravar() usa o manejo JA GRAVADO no estoque (tb_7017); sem ele, calcula pela
#             regra do modelo (regras_sisbov.manejo_do_sisbov). Antes gravava os 6 ultimos
#             digitos, errado no modelo antigo (105), onde o manejo sao os 6 ANTES do DV.
#             (2) DV: checar_sisbov(), gravar() e conferir() recusam brinco 105 com DV
#             incorreto (mesma mensagem do Leitor v1.17.0). Modelo novo nao tem DV.
#             REVERSAO: devolver .bak_antes_dv_manejo.
#     v1.16.0: Sessao 094 (12/10/2026, 20:30 -03) - AUDITORIA DE COMPRAS: O nome do Produtor da tela vem do vinculo do Produtor LOGADO (antes, .first() da
#             Propriedade: com 2+ Produtores na fazenda aparecia o nome errado).
#             REVERSAO: devolver .bak_antes_auditoria_compras.
#     v1.17.0: Sessao 094 (12/10/2026, 20:40 -03) - AUDITORIA DO NASCIMENTO: gravar() pega a trava de brincos do Nascimento (TRAVA_BRINCOS_NASC) antes de validar o brinco.
#             REVERSAO: devolver .bak_antes_auditoria_nasc.
#     v1.18.0: Sessao 096 (14/10/2026, 10:05 -03) - NASCIMENTO DEPOIS DA BRINCAGEM: gravar() recusa,
#             em Compra e Nascimento, a Data de Nascimento posterior a Data de Brincagem
#             (regras_sisbov.py v1.6.0). conferir() continua liberado. Nenhuma outra mudanca.
#             REVERSAO: devolver .bak_antes_nasc_cth_s096.
#     v1.19.0: Sessao 098 (16/10/2026, 20:20 -03) - _sisbov_duplicado tambem confere tb_2002 (animal que ja saiu nao reusa o brinco).
#     v1.20.0: Sessao 106 (26/10/2026, 15:30 -03) - CASO 1 (mesmo molde do Leitor v1.24.0): GTA de Compra PENDENTE aparece na Selecao; a Leitura grava cada
#             brinco (RFID + SISBOV) RESERVADO a ela (tb_5001.id_gta_reservada), confere sexo/idade contra as categorias da GTA e, no ULTIMO brinco,
#             executa o vinculo automatico (vincular_gta.vincular_automatico v1.15.0): GTA BRINCADO, ja conferida, pronta para Gerar Comunicado.
#             Usa _lidos_reservados e _montar_reserva do Leitor. Exige o SQL Tabelas\tb_5001_id_gta_reservada_s106.sql. REVERSAO: .bak_antes_s106n.
#     v1.21.0: Sessao 106 (26/10/2026, 16:20 -03) - AVISO NA HORA (caso 1): nova rota POST /produtor/brincagem-bastao/checar-categoria (usa a regra do Leitor
#             v1.25.0): avisa assim que Sexo / Especie / Nascimento nao batem com a GTA PENDENTE. O gravar() continua conferindo. REVERSAO: .bak_antes_s106q.
#     v1.22.0: Sessao 106 (26/10/2026, 17:50 -03) - AVISO DE ESQUECIDO: o quadro 'Brincagens em aberto' mostra ha quantos dias a leitura esta sem GTA (campo 'atrasado' com 3+ dias fica em vermelho). Nenhuma outra mudanca. REVERSAO: .bak_antes_s106v.
# =========================================================

from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import text, func, or_
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, PropriedadeProdutor, Produtor
from backend.models.tb_5001_brincagem import Brincagem
from backend.models.tb_5003_rejeicoes_brincagem import RejeicaoBrincagem
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_4001_gta import Gta
from backend.models.tb_7020_notificacao_impressao import NotificacaoImpressao
from backend.models.tb_7002_pia import Pia
from backend.models.tb_2002_saida_animais import SaidaAnimal  # Sessao 098: brinco de animal que ja saiu nao pode ser reusado
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.models.tb_3008_brincos_saida import BrincoSaida
from backend.models.tb_4005_racas import Raca
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.brincagem_leitor import _lidos_reservados, _montar_reserva, _checar_categoria_json   # v1.20.0 / v1.21.0 - caso 1 (mesma regra do Leitor)
from backend.utils.multitenant import get_db_produtor
from backend.utils.regras_sisbov import (
    TIPOS_ENTRADA, TIPO_ENTRADA_NASCIMENTO, DIAS_MAX_COTA_HILTON, descricao_tipo_entrada,
    MENSAGEM_DATA_BRINCAGEM_VENCIDA, data_brincagem_vencida,   # v1.9.0
    nascimento_depois_da_brincagem, MENSAGEM_NASCIMENTO_DEPOIS_BRINCAGEM,   # v1.18.0
    MODELO_SISBOV_ANTIGO, modelo_do_sisbov, sisbov_confere, manejo_do_sisbov,   # v1.15.0
)
from backend.utils.pesagem import registrar_pesagem, ORIGEM_BRETE_NASCIMENTO, ORIGEM_BRETE_COMPRA
from backend.utils.conferencia_compra import (   # v1.10.0
    TIPO_BANCO_COMPRA, MOTIVO_JA_CONFERIDO_COMPRA, ler_peso_brete, ler_lote_brete,
    listar_gtas_abertas, montar_lancamento, buscar_brinco, bloqueio_brinco, numero_gta,
)
from backend.utils.gravacao_nascimento import (
    reservar_controle, atualizar_qtde_controle, buscar_controle_aberto,
    buscar_notificacao_para_integracao, integrar_animal_na_notificacao,
    TRAVA_BRINCOS_NASC,   # v1.17.0
)


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
brincagem_bastao = Blueprint('brincagem_bastao', __name__)


# -------------------------------------------------------
# Mesma protecao de cache do modulo irmao brincagem_leitor.py
# (Sessao 064) - evita o navegador reenviar catalogo de
# Raca/Especie de outro Produtor testado antes.
# -------------------------------------------------------
@brincagem_bastao.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta

# -------------------------------------------------------
# Destino do Voltar quando a tela de Selecionar Propriedade
# nunca existiu no caminho real (0 ou 1 par) - Regra de Ouro,
# Sessao 051. Origem real deste fluxo e o Hub de Brincagem
# (Regra de Ouro #7).
# -------------------------------------------------------
VOLTAR_SELECIONAR_PROPRIEDADE = '/produtor/hub-novo/brincagem'   # v1.12.0 - Hub novo (agrupado)

# Destino do Voltar da Tela 02 (selecao) quando o caminho real
# passou pela tela de Selecionar Propriedade (2+ pares) - Regra
# de Ouro #9, aplicada aqui desde a criacao do modulo (mesma
# licao do bug real corrigido em brincagem_leitor.py v1.3.0).
VOLTAR_TELA_SELECAO_COM_MULTIPLOS_PARES = '/produtor/brincagem-bastao/iniciar'

MOTIVO_DUPLICIDADE_SISBOV = 'Sisbov do Animal ja Inserido'
MOTIVO_DUPLICIDADE_RFID = 'RFID do Animal ja Inserido'

# v1.2.0 - motivos novos da validacao de estoque (texto curto para
# tb_5003 - ver _validar_sisbov()).
MOTIVO_FORA_ESTOQUE = 'Brinco fora do estoque'
MOTIVO_JA_UTILIZADO = 'Brinco ja utilizado'
MOTIVO_RFID_IGUAL_SISBOV = 'Sisbov igual ao RFID'
MOTIVO_DV_INCORRETO   = 'Brinco com DV incorreto'   # v1.15.0
MENSAGEM_DV_INCORRETO = 'Brinco com dígito verificador (DV) incorreto. Confira o número lido ou digitado.'   # v1.15.0

# Aproximacao usada para converter "Nro Meses" em dias - mesma
# do Leitor. Ver ATENCAO em brincagem_leitor.py.
DIAS_POR_MES = 30

# Peso maximo aceito na Tela de Leitura - mesma regra do Leitor.
PESO_MAXIMO_KG = 1000

# v1.4.0 - manejo = 6 ultimos digitos do SISBOV (mesma regra do
# Leitor v1.7.0 e da Entrada de Brincos).
TAMANHO_MANEJO = 6

# v1.5.0 - codigos aceitos do Tipo de Entrada (lista fixa).
CODIGOS_TIPO_ENTRADA = tuple(codigo for codigo, _ in TIPOS_ENTRADA)

# v1.6.0 - valor gravado no banco para Nascimento/Desmame (tb_2001 e
# tb_4001_gta) e serie da Notificacao lancada pelo escritorio.
TIPO_BANCO_NASCIMENTO = 'NASCTO-DESMAME'
SERIE_NOTIFICACAO = 'NAS'
MOTIVO_JA_CONFERIDO = 'Brinco ja conferido no brete'
MOTIVO_DATA_DIFERENTE = 'Data diferente do lancamento'
MOTIVO_RFID_OUTRO = 'RFID diferente do lancamento'

# v1.10.0 - mensagens da Tela 02 quando a Leitura devolve o usuario com ?erro=...
MENSAGENS_ERRO_SELECAO = {
    'data_vencida':  MENSAGEM_DATA_BRINCAGEM_VENCIDA,
    'gta_encerrada': 'GTA já encerrada — todos os brincos foram conferidos.',
    'gta_invalida':  'GTA não encontrada, ou sem brincos para conferir.',
    'gta_data_entrega': 'Data Brincagem anterior à Entrega da GTA {numero}. Digite uma data igual ou posterior à Entrega.',   # v1.20.0
    'gta_data':      'Data Brincagem diferente da lançada pelo escritório para a GTA {numero}. '
                     'Confira a data da GTA e digite novamente.',   # v1.10.4
}


# v1.10.4 - monta a mensagem de erro da Tela 02 (a GTA vem na URL; so letras, numeros e hifen)
def _mensagem_erro_selecao(codigo, numero=''):
    mensagem = MENSAGENS_ERRO_SELECAO.get(codigo)
    if mensagem and '{numero}' in mensagem:
        numero = ''.join(c for c in (numero or '') if c.isalnum() or c == '-')
        mensagem = mensagem.format(numero=numero or 'escolhida')
    return mensagem


# -------------------------------------------------------
# Funcao (NOVA, v1.5.0): trava de seguranca - a Propriedade tem
# de ser de um par Propriedade/Produtor do usuario logado E do
# Produtor da sessao. Vazio ou nao numero = False. Mesma regra de
# brincagem_consulta.py v2.11.1.
# -------------------------------------------------------
def _propriedade_do_usuario(id_propriedade):
    try:
        id_int = int(id_propriedade)
    except (TypeError, ValueError):
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    # v1.12.0 - TRAVA DA FAZENDA EM USO: Propriedade diferente da fazenda em
    # uso (trocada em outra aba) = negado.
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and par_em_uso.id_propriedade != id_int:
        return False
    return any(
        par.id_propriedade == id_int and par.id_produtor == session.get('id_produtor')
        for par in pares
    )


# -------------------------------------------------------
# Negado (v1.12.0): com fazenda em uso, a Propriedade errada manda para o
# iniciar() (que abre a fazenda em uso); sem fazenda em uso, Home como antes.
# -------------------------------------------------------
def _negado():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect('/produtor/brincagem-bastao/iniciar')
    return redirecionar_home()


# -------------------------------------------------------
# Funcao auxiliar: verifica se um SISBOV ja existe em qualquer
# uma das 3 tabelas de duplicidade - IDENTICA a
# brincagem_leitor.py, sem alteracao.
# -------------------------------------------------------
def _sisbov_duplicado(db, sisbov):
    if db.query(Entrada).filter_by(sisbov=sisbov).first():
        return True
    if db.query(Brincagem).filter_by(sisbov=sisbov, sts=False).first():
        return True
    if db.query(Pia).filter_by(sisbov=sisbov).first():
        return True
    if db.query(SaidaAnimal).filter_by(sisbov=sisbov).first():  # S098
        return True
    return False


# -------------------------------------------------------
# Funcao auxiliar (NOVA, v1.3.0): monta o texto do alerta quando o
# SISBOV ja foi usado, mostrando ONDE ele esta e o RFID vinculado
# (pedido de Benedito, Sessao 078 - simetrico ao alerta do RFID,
# que ja mostra o Brinco vinculado). Ordem da busca:
#   1. Rebanho vivo (tb_2001) -> "(rebanho)"
#   2. Brincagem pendente (tb_5001 sts=False) -> "(brincagem
#      pendente)"
# Registro sem RFID (ex.: brincado pelo Leitor) -> a mensagem para
# no brinco. Achado SO na PIA (tb_7002) -> texto simples de sempre
# (a PIA continua bloqueando, mas nao entra na mensagem).
# -------------------------------------------------------
# -------------------------------------------------------
# v1.11.0 - brinco que o ESCRITORIO ja salvou numa GTA de Compra (Brincagem Sequencial) e
# ainda nao foi conferido no brete: avisa de qual GTA e o que o peao deve fazer.
# -------------------------------------------------------
def _mensagem_brinco_do_escritorio(db, animal):
    if animal.tipo_entrada == TIPO_BANCO_COMPRA and animal.id_gta_entrada and not animal.conferido_brete:
        numero = numero_gta(db, animal.id_gta_entrada)
        return (
            f'Brinco {animal.sisbov} lançado pelo escritório na GTA {numero}. '
            f'Escolha a GTA {numero} na Seleção para conferir.'
        )
    return None


def _mensagem_sisbov_duplicado(db, sisbov):
    animal = db.query(Entrada).filter_by(sisbov=sisbov).first()
    if animal:
        mensagem_escritorio = _mensagem_brinco_do_escritorio(db, animal)   # v1.11.0
        if mensagem_escritorio:
            return mensagem_escritorio
        local, rfid_vinculado = 'rebanho', animal.rfid
    else:
        pendente = db.query(Brincagem).filter_by(sisbov=sisbov, sts=False).first()
        if not pendente:
            return 'Sisbov do Animal já Inserido'
        local, rfid_vinculado = 'brincagem pendente', pendente.rfid

    mensagem = f'Brinco {sisbov} já inserido ({local})'
    if rfid_vinculado:
        mensagem += f' — RFID vinculado: {rfid_vinculado}'
    return mensagem


# -------------------------------------------------------
# Funcao auxiliar (NOVA, v1.2.0): validacao COMPLETA do SISBOV,
# regra fechada com Benedito (Sessao 078). Devolve None se o
# brinco pode ser usado, ou (motivo_log, mensagem_tela) se deve
# ser bloqueado. Ordem das checagens:
#   1. Duplicidade (checagem de sempre - 3 tabelas).
#   2. Existe no ESTOQUE desta Propriedade
#      (tb_7017_entrada_brincos_rfid, gravado na Entrada de
#      Brincos)? Nao existe -> "fora do estoque" (pega tambem o
#      caso de digitar o RFID no campo do SISBOV - o numero do
#      RFID nunca e igual ao de um brinco).
#   3. Esta DISPONIVEL? Disponivel = saida_data, saida_gta,
#      saida_origem e numero_comunicado todos em branco. v1.11.0 - a RESERVA
#      de brincos da Brincagem Sequencial (formulario aberto, 30 min) NAO
#      bloqueia mais o brete: o animal vivo prevalece (acordo com Benedito,
#      Sessao 087). Brinco ja SALVO pelo escritorio numa GTA tem mensagem
#      propria (_mensagem_brinco_do_escritorio).
# motivo_log vai para tb_5003 (texto CURTO de proposito - nunca vi
# o model de tb_5003, entao nao sei o tamanho maximo da coluna
# motivo; os textos novos tem no maximo o mesmo tamanho dos ja
# usados). mensagem_tela e o texto completo mostrado no alerta.
# -------------------------------------------------------
def _validar_sisbov(db, id_propriedade, sisbov, motivo_duplicidade):
    if _sisbov_duplicado(db, sisbov):
        # v1.3.0 - mensagem mostra onde o brinco esta + RFID vinculado.
        return (motivo_duplicidade, _mensagem_sisbov_duplicado(db, sisbov))

    brincos_estoque = (
        db.query(EntradaBrincoRfid)
        .filter_by(id_propriedade=int(id_propriedade), sisbov=sisbov)
        .all()
    )
    if not brincos_estoque:
        return (MOTIVO_FORA_ESTOQUE, 'Brinco não pertence ao estoque desta Propriedade')

    disponivel = any(
        b.saida_data is None
        and b.saida_gta is None
        and b.saida_origem is None
        and b.numero_comunicado is None
        for b in brincos_estoque
    )
    if not disponivel:
        return (MOTIVO_JA_UTILIZADO, 'Brinco já utilizado')

    return None


# -------------------------------------------------------
# Funcao auxiliar (NOVA): verifica se um RFID ja existe em
# qualquer uma das 2 tabelas de duplicidade - SO 2, pois
# tb_7002_pia nao tem coluna rfid (confirmado por Benedito,
# Sessao 077).
# -------------------------------------------------------
def _rfid_duplicado(db, rfid):
    if db.query(Entrada).filter_by(rfid=rfid).first():
        return True
    if db.query(Brincagem).filter_by(rfid=rfid, sts=False).first():
        return True
    return False


# -------------------------------------------------------
# Funcao auxiliar (NOVA, v1.2.0): validacao do RFID, regra
# fechada com Benedito (Sessao 078). O chip RFID e REUTILIZAVEL -
# pode aparecer em linhas antigas da tb_7017 (historico) sem
# estar em uso hoje, por isso a tb_7017 NAO e consultada aqui.
# O RFID so esta livre se:
#   1. NAO estiver em nenhum animal do rebanho vivo (tb_2001);
#   2. NAO estiver numa brincagem ainda pendente (tb_5001 com
#      sts=False) - senao o mesmo chip iria em 2 animais.
# Bloqueado: devolve (motivo_log, mensagem_tela), com o SISBOV
# do brinco ao qual o RFID ja esta vinculado. Livre: None.
# O casamento RFID + SISBOV nasce na propria brincagem (RFID
# livre na tb_2001 + SISBOV disponivel na tb_7017).
# -------------------------------------------------------
def _validar_rfid(db, rfid):
    animal = db.query(Entrada).filter_by(rfid=rfid).first()
    if animal:
        mensagem_escritorio = _mensagem_brinco_do_escritorio(db, animal)   # v1.11.0
        if mensagem_escritorio:
            return (MOTIVO_DUPLICIDADE_RFID, mensagem_escritorio)
        return (MOTIVO_DUPLICIDADE_RFID, f'RFID já vinculado ao Brinco {animal.sisbov}')

    pendente = db.query(Brincagem).filter_by(rfid=rfid, sts=False).first()
    if pendente:
        return (MOTIVO_DUPLICIDADE_RFID, f'RFID já vinculado ao Brinco {pendente.sisbov} (brincagem pendente)')

    return None


# -------------------------------------------------------
# Funcao auxiliar (NOVA, v1.1.0): conta quantos brincos ja foram
# gravados nesta Propriedade NESTA Data de Brincagem - copia
# local da mesma funcao de brincagem_leitor.py v1.4.0.
# -------------------------------------------------------
def _contar_gravados_na_data(db, id_propriedade, data_brincagem, tipo_entrada):
    # v1.5.0 - conta por Data + TIPO (mesma do Leitor v1.8.0)
    total = (
        db.query(Brincagem)
        .filter_by(
            id_propriedade=int(id_propriedade),
            data_brincagem=data_brincagem,
            tipo_entrada=tipo_entrada,
        )
        .count()
    )
    # v1.13.0 - NASCIMENTO: soma os brincos CONFERIDOS das Notificacoes (NAS) lancadas pelo
    # escritorio nesta data (a conferencia nao cria linha em tb_5001, so marca tb_2001).
    if tipo_entrada == TIPO_ENTRADA_NASCIMENTO:
        total += (
            db.query(Entrada)
            .join(Gta, Gta.id == Entrada.id_gta_entrada)
            .filter(
                Entrada.id_propriedade == int(id_propriedade),
                Entrada.conferido_brete.is_(True),
                Gta.id_propriedade == int(id_propriedade),
                Gta.tipo_movimento == TIPO_BANCO_NASCIMENTO,
                Gta.serie_gta == SERIE_NOTIFICACAO,
                Gta.data_emissao == data_brincagem,
                ~db.query(NotificacaoImpressao.id).filter(NotificacaoImpressao.id_gta == Gta.id).exists(),
            )
            .count()
        )
    return total


# -------------------------------------------------------
# Funcoes auxiliares (NOVAS, v1.6.0): Nascimento lancado pelo
# escritorio x conferencia no brete (com RFID).
# -------------------------------------------------------
def _query_lancado(db, id_propriedade):
    return db.query(Entrada).filter(
        Entrada.id_propriedade == int(id_propriedade),
        Entrada.tipo_entrada == TIPO_BANCO_NASCIMENTO,
        Entrada.id_gta_entrada.isnot(None),
    )


def _buscar_lancado_por_sisbov(db, id_propriedade, sisbov):
    return _query_lancado(db, id_propriedade).filter(Entrada.sisbov == sisbov).first()


def _buscar_lancado_por_rfid(db, id_propriedade, rfid):
    return _query_lancado(db, id_propriedade).filter(Entrada.rfid == rfid).first()


def _data_br(data):
    return data.strftime('%d/%m/%Y') if data else ''


def _data_tela(texto):
    try:
        return datetime.strptime((texto or '').strip(), '%d/%m/%Y').date()
    except ValueError:
        return None


def _contadores_notificacao(db, id_gta):
    total = db.query(Entrada).filter(Entrada.id_gta_entrada == id_gta).count()
    conferidos = (
        db.query(Entrada)
        .filter(Entrada.id_gta_entrada == id_gta, Entrada.conferido_brete.is_(True))
        .count()
    )
    return total, conferidos


def _numero_notificacao(db, lancado):
    gta = db.get(Gta, lancado.id_gta_entrada)
    return gta.numero_gta_completo if gta else ''


def _bloqueio_conferencia(db, lancado, data_tela):
    """None se o brinco pode ser conferido agora; senao (motivo, mensagem)."""
    numero = _numero_notificacao(db, lancado)
    if lancado.conferido_brete:
        quando = ''
        if lancado.conferido_em:
            quando = ' em ' + lancado.conferido_em.strftime('%d/%m/%Y %H:%M')
        return (MOTIVO_JA_CONFERIDO, f'Brinco {lancado.sisbov} já conferido no brete{quando} ({numero})')
    if lancado.data_brincagem != data_tela:
        return (
            MOTIVO_DATA_DIFERENTE,
            f'Brinco {lancado.sisbov} foi lançado pelo escritório em {_data_br(lancado.data_brincagem)} '
            f'({numero}). A Data de Brincagem desta tela é {_data_br(data_tela)} — '
            f'volte e escolha a data certa.'
        )
    return None


def _dados_conferencia(db, lancado):
    raca = db.get(Raca, lancado.id_raca) if lancado.id_raca else None
    nro_meses = None
    if lancado.eras_dias is not None:
        nro_meses = int(round(lancado.eras_dias / DIAS_POR_MES))
    return {
        'sisbov': lancado.sisbov,
        'rfid': lancado.rfid or '',
        'id_especie': lancado.id_especie,
        'id_raca': lancado.id_raca,
        'raca_nome': raca.nome if raca else '',
        'sexo': lancado.sexo,
        'nro_meses': nro_meses,
        'nascimento': _data_br(lancado.nascimento),
        'lote': lancado.lote or '',
    }


# -------------------------------------------------------
# Funcao auxiliar (NOVA, v1.6.1): brincagens EM ABERTO por Tipo de
# Entrada, mostradas na Tela 02 assim que o Tipo e escolhido -
# clicar numa delas preenche a Data de Brincagem.
#   - lidas no brete e ainda aguardando fechamento (tb_5001
#     sts=False), por Data + Tipo;
#   - Nascimento lancado pelo escritorio com conferencia pendente
#     (Notificacao NAS com Faltam > 0).
# -------------------------------------------------------
def _brincagens_em_aberto(db, id_propriedade):
    abertas = {'COMPRA': [], 'NASCIMENTO': []}

    linhas = (
        db.query(Brincagem.tipo_entrada, Brincagem.data_brincagem, func.count())
        .filter(
            Brincagem.id_propriedade == int(id_propriedade),
            Brincagem.sts == False,   # noqa: E712
            Brincagem.data_brincagem.isnot(None),
            Brincagem.id_gta_reservada.is_(None),   # v1.20.0 - leitura reservada a GTA nao e 'em aberto'
        )
        .group_by(Brincagem.tipo_entrada, Brincagem.data_brincagem)
        .order_by(Brincagem.data_brincagem.desc())
        .all()
    )
    for tipo, data, qtde in linhas:
        if tipo in abertas:
            abertas[tipo].append({
                'data': _data_br(data),
                'rotulo': f'{qtde} brinco(s) lido(s) no brete, aguardando fechamento' + (f' — há {(date.today() - data).days} dia(s)' if (date.today() - data).days >= 1 else ''),
                'atrasado': (date.today() - data).days >= 3,   # v1.26.0 - esquecido: 3+ dias sem GTA
            })

    gtas = (
        db.query(Gta)
        .filter(
            Gta.id_propriedade == int(id_propriedade),
            Gta.tipo_movimento == TIPO_BANCO_NASCIMENTO,
            Gta.serie_gta == SERIE_NOTIFICACAO,
        )
        .order_by(Gta.data_emissao.desc(), Gta.id.desc())
        .all()
    )
    for gta in gtas:
        total, conferidos = _contadores_notificacao(db, gta.id)
        if total == 0 or db.query(NotificacaoImpressao.id).filter_by(id_gta=gta.id).first() is not None:
            continue   # v1.7.0 - impressa nao entra na brincagem
        if conferidos < total:
            rotulo = f'{gta.numero_gta_completo} — lançados {total}, faltam {total - conferidos}'
        else:
            rotulo = f'{gta.numero_gta_completo} — lançados {total}, todos conferidos (aceita novos animais)'
        abertas['NASCIMENTO'].append({'data': _data_br(gta.data_emissao), 'rotulo': rotulo})

    # v1.10.0 - Compra: GTAs lancadas pela Sequencial com conferencia pendente
    # (vem ANTES das leituras livres; id_gta leva o peao direto a GTA).
    gtas_compra = [{
        'data': _data_br(g['data']),
        'rotulo': f"{g['numero']} — lançados {g['total']}, faltam {g['faltam']} (lançada pelo escritório)",
        'id_gta': g['id_gta'],
    } for g in listar_gtas_abertas(db, id_propriedade)]
    # v1.20.0 - GTAs de Compra PENDENTES (lancadas so como GTA): o brete le os brincos ja reservados a elas.
    gtas_pendentes = []
    pendentes = (
        db.query(Gta)
        .filter(
            Gta.id_propriedade == int(id_propriedade),
            Gta.tipo_movimento == TIPO_BANCO_COMPRA,
            Gta.sentido == 'ENTRADA',
            Gta.status_brincagem == 'PENDENTE',
            Gta.data_entrega.isnot(None),
        )
        .order_by(Gta.data_emissao.desc(), Gta.id.desc())
        .all()
    )
    for g in pendentes:
        reserva = _montar_reserva(db, id_propriedade, g)
        if reserva is None or reserva['lidos'] >= reserva['total']:
            continue
        gtas_pendentes.append({
            'data': _data_br(g.data_entrega),
            'rotulo': (f"{reserva['numero']} — a brincar: {reserva['categorias']}; "
                       f"lidos {reserva['lidos']}, faltam {reserva['faltam']} (GTA lançada, sem brincos)"),
            'id_gta': g.id,
        })
    abertas['COMPRA'] = gtas_compra + gtas_pendentes + abertas['COMPRA']

    return abertas


# -------------------------------------------------------
# Funcao auxiliar: grava uma tentativa bloqueada em
# tb_5003_rejeicoes_brincagem - reaproveita a mesma tabela do
# Leitor, agora com o campo (sisbov OU rfid) preenchido de
# acordo com qual leitura foi rejeitada, e o motivo
# correspondente.
# -------------------------------------------------------
# -------------------------------------------------------
# v1.15.0 - Brinco do modelo antigo (comeca com 105) com DV que nao
# bate? Modelo novo nao tem DV: nunca e recusado por isso.
# -------------------------------------------------------
def _dv_incorreto(sisbov):
    return modelo_do_sisbov(sisbov) == MODELO_SISBOV_ANTIGO and not sisbov_confere(sisbov)


# -------------------------------------------------------
# v1.15.0 - Manejo do brinco: usa o JA GRAVADO no estoque (tb_7017);
# sem ele, calcula pela regra do modelo; numero fora do formato cai
# no comportamento antigo (6 ultimos digitos). Igual ao Leitor.
# -------------------------------------------------------
def _manejo_do_brinco(db, id_propriedade, sisbov):
    brinco = (
        db.query(EntradaBrincoRfid)
        .filter_by(id_propriedade=int(id_propriedade), sisbov=sisbov)
        .first()
    )
    if brinco is not None and brinco.manejo:
        return brinco.manejo
    try:
        return manejo_do_sisbov(sisbov)
    except ValueError:
        return sisbov[-TAMANHO_MANEJO:]


def _registrar_rejeicao(db, id_propriedade, motivo, sisbov='', rfid=''):
    db.add(RejeicaoBrincagem(
        id_propriedade=int(id_propriedade),
        id_usuario=session['usuario_id'],
        sisbov=sisbov,
        rfid=rfid,
        motivo=motivo,
        data_tentativa=date.today(),
    ))
    db.commit()


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-bastao/iniciar — ponto de
# partida. IDENTICA a brincagem_leitor.iniciar(), so trocando o
# destino da Tela 02.
# -------------------------------------------------------
@brincagem_bastao.route('/produtor/brincagem-bastao/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            titulo='Brincagem com Bastão — Selecionar Propriedade',
            proximo='/produtor/brincagem-bastao/selecao',
            campo_propriedade='id_propriedade',
            voltar=VOLTAR_SELECIONAR_PROPRIEDADE,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='brincagem',
        )

    # v1.12.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/brincagem-bastao/selecao?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/brincagem-bastao/selecao?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        titulo='Brincagem com Bastão — Selecionar Propriedade',
        proximo='/produtor/brincagem-bastao/selecao',
        campo_propriedade='id_propriedade',
        voltar=VOLTAR_SELECIONAR_PROPRIEDADE,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='brincagem',
    )


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-bastao/selecao — Tela 02.
# Fazenda/Produtor travados (so exibicao) + Data Brincagem +
# dropdown Brincos - identica a selecao() do Leitor, com o
# destino do Voltar ja calculado direto pelo numero de pares
# (Regra de Ouro #9 aplicada desde a criacao).
# -------------------------------------------------------
@brincagem_bastao.route('/produtor/brincagem-bastao/selecao')
def selecao():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):   # v1.5.0
        return _negado()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    # v1.12.0 - com fazenda em uso a selecao e pulada: Voltar vai direto ao Hub.
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        url_voltar = VOLTAR_TELA_SELECAO_COM_MULTIPLOS_PARES
    else:
        url_voltar = VOLTAR_SELECIONAR_PROPRIEDADE

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))

        nome_produtor = None
        if propriedade:
            vinculo = db.query(PropriedadeProdutor).filter_by(
                id_propriedade=propriedade.id, id_produtor=session['id_produtor'], data_fim=None   # Sessao 094
            ).first()
            if vinculo:
                produtor = db.get(Produtor, vinculo.id_produtor)
                if produtor:
                    nome_produtor = produtor.nome

    # v1.6.1 - brincagens em aberto por Tipo (clicaveis na Tela 02).
    try:
        with get_db_produtor(session['id_produtor']) as db_prod:
            abertas = _brincagens_em_aberto(db_prod, id_propriedade)
    except Exception:
        abertas = {'COMPRA': [], 'NASCIMENTO': []}

    return render_template(
        'produtor/brincagem_bastao_selecao.html',
        erro=_mensagem_erro_selecao(request.args.get('erro', ''), request.args.get('numero', '')),   # v1.9.0 / v1.10.0 / v1.10.4
        propriedade=propriedade,
        nome_produtor=nome_produtor,
        id_propriedade=id_propriedade,
        url_voltar=url_voltar,
        tipos_entrada=TIPOS_ENTRADA,   # v1.5.0
        abertas=abertas,               # v1.6.1
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='brincagem',
    )


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-bastao/leitura — Tela de
# Leitura (Tela 3). Carrega os catalogos (Especie/Raca) e o
# total ja gravado NESTA Data de Brincagem (v1.1.0 - antes era o
# total geral da Propriedade).
# -------------------------------------------------------
@brincagem_bastao.route('/produtor/brincagem-bastao/leitura')
def leitura():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    data_brincagem = request.args.get('data_brincagem', '')
    saida_brincos  = request.args.get('saida_brincos', '')
    tipo_entrada   = request.args.get('tipo_entrada', '').strip().upper()   # v1.5.0
    id_gta         = request.args.get('id_gta', '').strip()                 # v1.10.0 - Compra: GTA lancada escolhida
    modo_gta       = tipo_entrada == TIPO_BANCO_COMPRA and id_gta.isdecimal()

    if not _propriedade_do_usuario(id_propriedade):   # v1.5.0
        return _negado()

    if not (id_propriedade and data_brincagem and saida_brincos):
        return redirect(f'/produtor/brincagem-bastao/selecao?id_propriedade={id_propriedade}')

    # v1.5.0 - Tipo de Entrada obrigatorio (lista fixa).
    if tipo_entrada not in CODIGOS_TIPO_ENTRADA:
        return redirect(f'/produtor/brincagem-bastao/selecao?id_propriedade={id_propriedade}')

    # v1.1.0 - Data de Brincagem da URL (dd/mm/aaaa) convertida
    # para data de verdade, usada no contador GRAVADOS. Data
    # incorreta: volta para a Tela 02 escolher de novo.
    try:
        data_brincagem_obj = datetime.strptime(data_brincagem, '%d/%m/%Y').date()
    except ValueError:
        return redirect(f'/produtor/brincagem-bastao/selecao?id_propriedade={id_propriedade}')

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))

    with engine.connect() as conn:
        especies = conn.execute(text(
            'SELECT id, codigo, descricao FROM public.tb_4002_especie ORDER BY descricao'
        )).mappings().all()

    with get_db_produtor(session['id_produtor']) as db:
        racas = db.query(Raca).filter_by(ativo=True, comum=True).order_by(Raca.nome).all()
        # v1.10.0 - Compra: GTA lancada pelo escritorio escolhida na Tela 02. A Data
        # Brincagem e a da propria GTA; GTA ja encerrada ou invalida volta para a Tela 02.
        lancamento_gta = None
        gta_reserva = None   # v1.20.0 - CASO 1: GTA PENDENTE escolhida (leitura livre RESERVADA a ela)
        if modo_gta:
            gta_pendente = db.get(Gta, int(id_gta))
            if gta_pendente is not None and gta_pendente.status_brincagem == 'PENDENTE':
                modo_gta = False   # nao e conferencia de GTA lancada pelo escritorio
                gta_reserva = _montar_reserva(db, id_propriedade, gta_pendente)
                if gta_reserva is None:
                    return redirect(f'/produtor/brincagem-bastao/selecao?id_propriedade={id_propriedade}&erro=gta_invalida')
                if gta_reserva['lidos'] >= gta_reserva['total']:
                    return redirect(f'/produtor/brincagem-bastao/selecao?id_propriedade={id_propriedade}&erro=gta_encerrada')
                if data_brincagem_obj < gta_reserva['data_entrega']:
                    return redirect(f'/produtor/brincagem-bastao/selecao?id_propriedade={id_propriedade}'
                                    f"&erro=gta_data_entrega&numero={gta_reserva['numero']}")
        if modo_gta:
            lancamento_gta = montar_lancamento(db, id_propriedade, id_gta)
            if lancamento_gta is None:
                return redirect(f'/produtor/brincagem-bastao/selecao?id_propriedade={id_propriedade}&erro=gta_invalida')
            if lancamento_gta['conferidos'] >= lancamento_gta['total']:
                return redirect(f'/produtor/brincagem-bastao/selecao?id_propriedade={id_propriedade}&erro=gta_encerrada')
            # v1.10.4 - a Data Brincagem DIGITADA tem de ser a lancada pelo escritorio (a Tela 02 nao
            # preenche mais a data: o usuario confere e digita).
            if lancamento_gta['data'] and data_brincagem_obj != lancamento_gta['data']:
                return redirect(f'/produtor/brincagem-bastao/selecao?id_propriedade={id_propriedade}'
                                f"&erro=gta_data&numero={lancamento_gta['numero']}")

        total_gravados = _contar_gravados_na_data(db, id_propriedade, data_brincagem_obj, tipo_entrada)
        if lancamento_gta:
            total_gravados = lancamento_gta['conferidos']   # v1.10.0 - contador vira CONFERIDOS da GTA
        if gta_reserva:
            total_gravados = gta_reserva['lidos']   # v1.20.0 - contador vira LIDOS da GTA

        # v1.5.0 - Nascimento: Numero de Controle ja aberto nesta
        # data (None = sera reservado no 1o animal gravado).
        controle_numero = None
        if tipo_entrada == TIPO_ENTRADA_NASCIMENTO:
            controle = buscar_controle_aberto(db, id_propriedade, data_brincagem_obj)
            controle_numero = controle.numero_gta_completo if controle else None

        # v1.6.0 - Nascimento: Notificacoes (NAS) lancadas pelo escritorio
        # nesta Data de Brincagem, com os brincos e Lancados/Conferidos.
        lancamentos = [lancamento_gta] if lancamento_gta else []   # v1.10.0
        extras = []   # lidos na data que NAO estao no lancamento do escritorio
        if tipo_entrada == TIPO_ENTRADA_NASCIMENTO:
            gtas = (
                db.query(Gta)
                .filter(
                    Gta.id_propriedade == int(id_propriedade),
                    Gta.tipo_movimento == TIPO_BANCO_NASCIMENTO,
                    Gta.serie_gta == SERIE_NOTIFICACAO,
                    Gta.data_emissao == data_brincagem_obj,
                )
                .order_by(Gta.id)
                .all()
            )
            for gta in gtas:
                total, conferidos = _contadores_notificacao(db, gta.id)
                if db.query(NotificacaoImpressao.id).filter_by(id_gta=gta.id).first() is not None:
                    continue   # v1.7.0 - Notificacao impressa nao entra na brincagem
                if total > 0:
                    animais = (
                        db.query(Entrada)
                        .filter(Entrada.id_gta_entrada == gta.id)
                        .order_by(Entrada.sisbov)
                        .all()
                    )
                    brincos = [{
                        'sisbov': a.sisbov,
                        'sexo': a.sexo,
                        'meses': int(round(a.eras_dias / DIAS_POR_MES)) if a.eras_dias is not None else None,
                        'lote': a.lote or '',
                        'conferido': bool(a.conferido_brete),
                        'hora': a.conferido_em.strftime('%H:%M') if (a.conferido_brete and a.conferido_em) else '',
                    } for a in animais]
                    lancamentos.append({
                        'numero': gta.numero_gta_completo,
                        'total': total,
                        'conferidos': conferidos,
                        'brincos': brincos,
                    })

            if lancamentos:
                lidos_fora = (
                    db.query(Brincagem)
                    .filter(
                        Brincagem.id_propriedade == int(id_propriedade),
                        Brincagem.data_brincagem == data_brincagem_obj,
                        Brincagem.tipo_entrada == tipo_entrada,
                        Brincagem.sts == False,   # noqa: E712
                    )
                    .order_by(Brincagem.sisbov)
                    .all()
                )
                extras = [{
                    'sisbov': b.sisbov,
                    'sexo': b.sexo,
                    'lote': b.lote or '',
                } for b in lidos_fora]

    # v1.9.0 - Nascimento com Data de mais de 30 dias: so entra se houver
    # Notificacao do escritorio nao impressa nessa data (para conferir).
    if (tipo_entrada == TIPO_ENTRADA_NASCIMENTO and data_brincagem_vencida(data_brincagem_obj)
            and not lancamentos):
        return redirect(f'/produtor/brincagem-bastao/selecao?id_propriedade={id_propriedade}&erro=data_vencida')

    return render_template(
        'produtor/brincagem_bastao_leitura.html',
        propriedade=propriedade,
        id_propriedade=id_propriedade,
        data_brincagem=data_brincagem,
        saida_brincos=saida_brincos,
        tipo_entrada=tipo_entrada,                                        # v1.5.0
        tipo_entrada_descricao=descricao_tipo_entrada(tipo_entrada),     # v1.5.0
        controle_numero=controle_numero,                                  # v1.5.0
        extras=extras,                                                    # v1.6.2
        lancamentos=lancamentos,                                          # v1.6.0
        id_gta=id_gta if modo_gta else '',                                # v1.10.0
        gta_reserva=gta_reserva,                                          # v1.20.0
        dias_max_cota_hilton=DIAS_MAX_COTA_HILTON,                        # v1.5.0
        especies=especies,
        racas=racas,
        total_gravados=total_gravados,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='brincagem',
    )


# -------------------------------------------------------
# Rota: POST /produtor/brincagem-bastao/checar-rfid (AJAX) —
# NOVA. Chamada assim que o RFID e lido (bastao), ANTES do
# SISBOV. Retorna {duplicado: bool}. Se duplicado, ja grava a
# tentativa em tb_5003.
# -------------------------------------------------------
@brincagem_bastao.route('/produtor/brincagem-bastao/checar-rfid', methods=['POST'])
def checar_rfid():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    rfid           = (dados.get('rfid') or '').strip()
    id_propriedade = dados.get('id_propriedade')
    tipo_entrada   = (dados.get('tipo_entrada') or '').strip().upper()      # v1.6.0
    data_tela      = _data_tela(dados.get('data_brincagem'))                # v1.6.0
    id_gta         = str(dados.get('id_gta') or '').strip()                 # v1.10.0

    if not rfid or not id_propriedade:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):   # v1.5.0
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou. Volte ao Hub de Brincagem e abra de novo.'}), 403

    # v1.2.0 - _validar_rfid() (tb_2001 + tb_5001 pendente). A
    # chave 'duplicado' continua significando "bloqueado".
    with get_db_produtor(session['id_produtor']) as db:
        # v1.10.0 - Compra com GTA lancada escolhida: RFID ja vinculado a brinco de
        # OUTRA GTA (ou ja conferido) e barrado; RFID ainda sem animal segue a
        # validacao normal - o SISBOV lido depois e que identifica o animal.
        if tipo_entrada == TIPO_BANCO_COMPRA and id_gta.isdecimal():
            lancado_gta = buscar_brinco(db, id_propriedade, rfid=rfid)
            if lancado_gta:
                bloqueio_gta = bloqueio_brinco(db, lancado_gta, id_gta, lancado_gta.sisbov)
                if bloqueio_gta:
                    if bloqueio_gta[0] == MOTIVO_JA_CONFERIDO_COMPRA:
                        _registrar_rejeicao(db, id_propriedade, MOTIVO_JA_CONFERIDO, rfid=rfid)
                    return jsonify({'duplicado': True, 'motivo': bloqueio_gta[0], 'mensagem': bloqueio_gta[1]})
                return jsonify({
                    'duplicado': False,
                    'conferencia': True,
                    'controle': _numero_notificacao(db, lancado_gta),
                    'animal': _dados_conferencia(db, lancado_gta),
                })

        # v1.6.0 - RFID de animal lancado pelo escritorio: o brete CONFERE.
        if tipo_entrada == TIPO_ENTRADA_NASCIMENTO:
            lancado = _buscar_lancado_por_rfid(db, id_propriedade, rfid)
            if lancado:
                bloqueio_conf = _bloqueio_conferencia(db, lancado, data_tela)
                if bloqueio_conf:
                    if bloqueio_conf[0] == MOTIVO_JA_CONFERIDO:
                        _registrar_rejeicao(db, id_propriedade, bloqueio_conf[0], rfid=rfid)
                    return jsonify({'duplicado': True, 'motivo': bloqueio_conf[0], 'mensagem': bloqueio_conf[1]})
                return jsonify({
                    'duplicado': False,
                    'conferencia': True,
                    'controle': _numero_notificacao(db, lancado),
                    'animal': _dados_conferencia(db, lancado),
                })

        bloqueio = _validar_rfid(db, rfid)
        if bloqueio:
            _registrar_rejeicao(db, id_propriedade, bloqueio[0], rfid=rfid)

    return jsonify({
        'duplicado': bool(bloqueio),
        'motivo': bloqueio[0] if bloqueio else None,
        'mensagem': bloqueio[1] if bloqueio else None,
    })


# -------------------------------------------------------
# Rota: POST /produtor/brincagem-bastao/checar-sisbov (AJAX) —
# IDENTICA a checar_sisbov() do Leitor, reaproveitada sem
# alteracao (mesma checagem de 3 tabelas).
# -------------------------------------------------------
@brincagem_bastao.route('/produtor/brincagem-bastao/checar-sisbov', methods=['POST'])
def checar_sisbov():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    sisbov         = (dados.get('sisbov') or '').strip()
    rfid           = (dados.get('rfid') or '').strip()   # v1.2.0
    id_propriedade = dados.get('id_propriedade')
    tipo_entrada   = (dados.get('tipo_entrada') or '').strip().upper()      # v1.6.0
    data_tela      = _data_tela(dados.get('data_brincagem'))                # v1.6.0
    id_gta         = str(dados.get('id_gta') or '').strip()                 # v1.10.0

    if not sisbov or not id_propriedade:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):   # v1.5.0
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou. Volte ao Hub de Brincagem e abra de novo.'}), 403

    # v1.2.0 - SISBOV nunca pode ser igual ao RFID lido (regra de
    # Benedito: o numero do RFID jamais sera igual ao do brinco).
    if rfid and sisbov == rfid:
        bloqueio = (MOTIVO_RFID_IGUAL_SISBOV, 'SISBOV igual ao RFID — leia o brinco visual')
    elif _dv_incorreto(sisbov):   # v1.15.0
        bloqueio = (MOTIVO_DV_INCORRETO, MENSAGEM_DV_INCORRETO)
    else:
        bloqueio = None

    with get_db_produtor(session['id_produtor']) as db:
        # v1.10.0 - Compra com GTA lancada escolhida: so brinco DESTA GTA passa, com
        # o RFID lido (se o brinco ja tem RFID, tem de ser o mesmo).
        if not bloqueio and tipo_entrada == TIPO_BANCO_COMPRA and id_gta.isdecimal():
            lancado_gta = buscar_brinco(db, id_propriedade, sisbov=sisbov)
            bloqueio_conf = bloqueio_brinco(db, lancado_gta, id_gta, sisbov)
            if not bloqueio_conf and lancado_gta.rfid and lancado_gta.rfid != rfid:
                bloqueio_conf = (MOTIVO_RFID_OUTRO,
                                 f'O Brinco {sisbov} está lançado com o RFID {lancado_gta.rfid}, e não com o RFID lido.')
            if not bloqueio_conf and not lancado_gta.rfid:
                bloqueio_rfid = _validar_rfid(db, rfid) if rfid else None
                if bloqueio_rfid:
                    bloqueio_conf = bloqueio_rfid
            if bloqueio_conf:
                if bloqueio_conf[0] == MOTIVO_JA_CONFERIDO_COMPRA:
                    _registrar_rejeicao(db, id_propriedade, MOTIVO_JA_CONFERIDO, sisbov=sisbov)
                return jsonify({'duplicado': True, 'motivo': bloqueio_conf[0], 'mensagem': bloqueio_conf[1]})
            return jsonify({
                'duplicado': False,
                'conferencia': True,
                'controle': _numero_notificacao(db, lancado_gta),
                'animal': _dados_conferencia(db, lancado_gta),
            })

        # v1.6.0 - Nascimento lancado pelo escritorio: o brete CONFERE o
        # brinco (SISBOV lido tem de ser o do animal do RFID lido).
        if not bloqueio and tipo_entrada == TIPO_ENTRADA_NASCIMENTO:
            lancado = _buscar_lancado_por_sisbov(db, id_propriedade, sisbov)
            lancado_rfid = _buscar_lancado_por_rfid(db, id_propriedade, rfid) if rfid else None

            if lancado:
                bloqueio_conf = _bloqueio_conferencia(db, lancado, data_tela)
                if not bloqueio_conf and lancado.rfid and lancado.rfid != rfid:
                    bloqueio_conf = (MOTIVO_RFID_OUTRO,
                                     f'O Brinco {sisbov} está lançado com o RFID {lancado.rfid}, e não com o RFID lido.')
                if not bloqueio_conf and not lancado.rfid:
                    bloqueio_rfid = _validar_rfid(db, rfid) if rfid else None
                    if bloqueio_rfid:
                        bloqueio_conf = bloqueio_rfid
                if bloqueio_conf:
                    if bloqueio_conf[0] == MOTIVO_JA_CONFERIDO:
                        _registrar_rejeicao(db, id_propriedade, bloqueio_conf[0], sisbov=sisbov)
                    return jsonify({'duplicado': True, 'motivo': bloqueio_conf[0], 'mensagem': bloqueio_conf[1]})
                return jsonify({
                    'duplicado': False,
                    'conferencia': True,
                    'controle': _numero_notificacao(db, lancado),
                    'animal': _dados_conferencia(db, lancado),
                })

            if lancado_rfid:
                mensagem = (f'SISBOV não corresponde ao RFID lido — o brinco esperado é '
                            f'{lancado_rfid.sisbov}.')
                return jsonify({'duplicado': True, 'motivo': 'SISBOV diferente do RFID', 'mensagem': mensagem})

        if not bloqueio:
            bloqueio = _validar_sisbov(db, id_propriedade, sisbov, MOTIVO_DUPLICIDADE_SISBOV)
        if bloqueio:
            _registrar_rejeicao(db, id_propriedade, bloqueio[0], sisbov=sisbov)

    return jsonify({
        'duplicado': bool(bloqueio),
        'motivo': bloqueio[0] if bloqueio else None,
        'mensagem': bloqueio[1] if bloqueio else None,
    })


# -------------------------------------------------------
# Rota: POST /produtor/brincagem-bastao/gravar (AJAX) — grava um
# animal em tb_5001_brincagem, com RFID e SISBOV no mesmo
# registro. Reconfirma a duplicidade dos DOIS no servidor por
# seguranca (defesa em profundidade), na ordem RFID -> SISBOV.
# -------------------------------------------------------
@brincagem_bastao.route('/produtor/brincagem-bastao/checar-categoria', methods=['POST'])
def checar_categoria():   # v1.21.0 - aviso na hora (caso 1)
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401
    dados = request.get_json(silent=True) or {}
    if not _propriedade_do_usuario(dados.get('id_propriedade')):
        return jsonify({'ok': False, 'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou.'}), 403
    return jsonify(_checar_categoria_json(dados, session['id_produtor']))


@brincagem_bastao.route('/produtor/brincagem-bastao/gravar', methods=['POST'])
def gravar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}

    id_propriedade      = dados.get('id_propriedade')
    data_brincagem_str  = (dados.get('data_brincagem') or '').strip()
    saida_brincos        = (dados.get('saida_brincos') or '').strip().upper()
    rfid                   = (dados.get('rfid') or '').strip()
    sisbov                   = (dados.get('sisbov') or '').strip()
    id_especie                = dados.get('id_especie')
    id_raca                     = dados.get('id_raca')
    sexo                          = (dados.get('sexo') or '').strip().upper()
    nro_meses_str                   = str(dados.get('nro_meses') or '').strip()
    nascimento_str                    = (dados.get('nascimento') or '').strip()
    peso_str                            = str(dados.get('peso') or '').strip()
    lote                                  = (dados.get('lote') or '').strip()
    tipo_entrada = (dados.get('tipo_entrada') or '').strip().upper()   # v1.5.0
    id_gta_reserva = str(dados.get('id_gta_reserva') or '').strip()    # v1.20.0 - caso 1

    # ---------------------------------------------------
    # Validacoes basicas - inclui RFID, alem dos mesmos campos
    # obrigatorios do Leitor.
    # ---------------------------------------------------
    if not (id_propriedade and rfid and sisbov and id_especie and id_raca and sexo and nascimento_str):
        return jsonify({'erro': 'Preencha todos os campos obrigatórios (RFID, SISBOV, Espécie, Raça, Sexo e Nascimento).'}), 400

    if not _propriedade_do_usuario(id_propriedade):   # v1.5.0
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou. Volte ao Hub de Brincagem e abra de novo.'}), 403

    # v1.5.0 - Tipo de Entrada e Data de Brincagem obrigatorios.
    if tipo_entrada not in CODIGOS_TIPO_ENTRADA:
        return jsonify({'erro': 'Tipo de Entrada incorreto. Volte e escolha Compra ou Nascimento.'}), 400
    if not data_brincagem_str:
        return jsonify({'erro': 'Data de Brincagem é obrigatória. Volte e informe a data.'}), 400

    if sexo not in ('MACHO', 'FEMEA'):
        return jsonify({'erro': 'Sexo incorreto.'}), 400

    # Etapa 3 (item 3): Especie e Raca precisam ser numeros; antes, valor adulterado dava erro 500.
    if not (str(id_especie).isdecimal() and str(id_raca).isdecimal()):
        return jsonify({'erro': 'Espécie ou Raça incorreta. Atualize a página e leia o brinco de novo.'}), 400

    try:
        nascimento = datetime.strptime(nascimento_str, '%d/%m/%Y').date()
    except ValueError:
        return jsonify({'erro': 'Data de Nascimento incorreta! Use o formato dd/mm/aaaa.'}), 400

    # v1.5.0 - Data de Brincagem agora sempre presente (conferida acima)
    try:
        data_brincagem = datetime.strptime(data_brincagem_str, '%d/%m/%Y').date()
    except ValueError:
        return jsonify({'erro': 'Data de Brincagem incorreta! Use o formato dd/mm/aaaa.'}), 400

    # v1.18.0 - Nascimento DEPOIS da Data de Brincagem e impossivel: bloqueia
    # (Compra e Nascimento). conferir() continua liberado.
    if nascimento_depois_da_brincagem(nascimento, data_brincagem):
        return jsonify({'erro': MENSAGEM_NASCIMENTO_DEPOIS_BRINCAGEM}), 400

    # v1.9.0 - Nascimento: Data de Brincagem com mais de 30 dias e bloqueada
    # (prazo de envio da Notificacao vencido). conferir() continua liberado.
    if tipo_entrada == TIPO_ENTRADA_NASCIMENTO and data_brincagem_vencida(data_brincagem):
        return jsonify({'erro': MENSAGEM_DATA_BRINCAGEM_VENCIDA}), 400

    # v1.10.0 - peso OBRIGATORIO no brete (o brete tem balanca).
    peso, erro_peso = ler_peso_brete(peso_str)
    if erro_peso:
        return jsonify({'erro': erro_peso}), 400

    # 1.10.3 - LOTE OBRIGATORIO no brete (pedido de Benedito).
    lote, erro_lote = ler_lote_brete(lote, obrigatorio=True)
    if erro_lote:
        return jsonify({'erro': erro_lote}), 400

    # ---------------------------------------------------
    # Nro Meses -> faixa (id_idade_meses) - mesma aproximacao do
    # Leitor.
    # ---------------------------------------------------
    id_idade_meses = None
    if nro_meses_str:
        try:
            nro_meses = int(nro_meses_str)
        except ValueError:
            return jsonify({'erro': 'Número de Meses incorreto.'}), 400

        dias_estimados = nro_meses * DIAS_POR_MES
        with engine.connect() as conn:
            faixa = conn.execute(text(
                'SELECT id FROM public.tb_4006_idade_meses '
                'WHERE :dias BETWEEN dias_min AND dias_max LIMIT 1'
            ), {'dias': dias_estimados}).fetchone()
        id_idade_meses = faixa[0] if faixa else None

    # v1.5.0 - UF da Propriedade (schema public), usada so na
    # reserva do Numero de Controle do Nascimento.
    if id_gta_reserva:   # v1.20.0 - na reserva a faixa de idade vem do NASCIMENTO (mesma conta do Vincular)
        if tipo_entrada != TIPO_BANCO_COMPRA or not id_gta_reserva.isdecimal():
            return jsonify({'erro': 'GTA de Compra incorreta. Volte à Seleção e escolha de novo.'}), 400
        dias_vida = (data_brincagem - nascimento).days
        meses_vida = max(round(dias_vida / DIAS_POR_MES), 0)
        with engine.connect() as conn:
            faixa = conn.execute(text(
                'SELECT id FROM public.tb_4006_idade_meses '
                'WHERE :dias BETWEEN dias_min AND dias_max LIMIT 1'
            ), {'dias': meses_vida * DIAS_POR_MES}).fetchone()
        id_idade_meses = faixa[0] if faixa else None

    uf_propriedade = None
    if tipo_entrada == TIPO_ENTRADA_NASCIMENTO:
        with Session(engine) as db_public:
            propriedade = db_public.get(Propriedade, int(id_propriedade))
            if not propriedade:
                return jsonify({'erro': 'Propriedade não encontrada.'}), 400
            uf_propriedade = propriedade.uf

    with get_db_produtor(session['id_produtor']) as db:
        # Etapa 3 (item 2): a trava vale para TODOS os tipos de entrada (Compra e Nascimento): dois aparelhos
        # lendo o mesmo brinco ao mesmo tempo nao gravam duas vezes. Tambem vale para o escritorio e o Cancelamento.
        db.execute(text('SELECT pg_advisory_xact_lock(:ns, :id)'),
                   {'ns': TRAVA_BRINCOS_NASC, 'id': int(id_propriedade)})

        # Etapa 3 (item 3): Especie e Raca precisam existir (antes, id inexistente dava erro 500).
        if db.execute(text('SELECT 1 FROM public.tb_4002_especie WHERE id = :i'), {'i': int(id_especie)}).first() is None:
            return jsonify({'erro': 'Espécie incorreta. Atualize a página e leia o brinco de novo.'}), 400
        if db.query(Raca).filter_by(id=int(id_raca), ativo=True).first() is None:
            return jsonify({'erro': 'Raça incorreta para este Produtor. Atualize a página e leia o brinco de novo.'}), 400

        # Reconfirmacao de duplicidade no servidor - RFID primeiro,
        # depois SISBOV (mesma ordem da leitura na tela).
        # v1.2.0 - mesmas validacoes COMPLETAS das rotas de checar.
        # v1.15.0 - DV incorreto (modelo antigo, 105) e recusado antes de tudo.
        if _dv_incorreto(sisbov):
            _registrar_rejeicao(db, id_propriedade, MOTIVO_DV_INCORRETO, sisbov=sisbov)
            return jsonify({'erro': MENSAGEM_DV_INCORRETO, 'mensagem': MENSAGEM_DV_INCORRETO, 'duplicado': True, 'campo': 'sisbov'}), 409

        bloqueio_rfid = _validar_rfid(db, rfid)
        if bloqueio_rfid:
            _registrar_rejeicao(db, id_propriedade, bloqueio_rfid[0], rfid=rfid)
            return jsonify({'erro': bloqueio_rfid[1], 'mensagem': bloqueio_rfid[1], 'duplicado': True, 'campo': 'rfid'}), 409

        if sisbov == rfid:
            bloqueio_sisbov = (MOTIVO_RFID_IGUAL_SISBOV, 'SISBOV igual ao RFID — leia o brinco visual')
        else:
            bloqueio_sisbov = _validar_sisbov(db, id_propriedade, sisbov, MOTIVO_DUPLICIDADE_SISBOV)
        if bloqueio_sisbov:
            _registrar_rejeicao(db, id_propriedade, bloqueio_sisbov[0], sisbov=sisbov)
            return jsonify({'erro': bloqueio_sisbov[1], 'mensagem': bloqueio_sisbov[1], 'duplicado': True, 'campo': 'sisbov'}), 409

        # v1.7.0 - Nascimento com Notificacao do escritorio da MESMA Data
        # ainda NAO impressa: o animal entra direto nela (ja conferido).
        if tipo_entrada == TIPO_ENTRADA_NASCIMENTO:
            gta_integra = buscar_notificacao_para_integracao(db, id_propriedade, data_brincagem)
            if gta_integra:
                try:
                    resultado = integrar_animal_na_notificacao(
                        db, gta_integra, session['id_produtor'], session.get('usuario_id'),
                        sisbov, rfid, id_especie, id_raca, sexo, nascimento, lote, peso=peso,
                    )
                    total_gravados = _contar_gravados_na_data(db, id_propriedade, data_brincagem, tipo_entrada)
                except ValueError as erro:
                    db.rollback()
                    return jsonify({'erro': str(erro)}), 400
                db.commit()
                return jsonify({
                    'sucesso': True,
                    'mensagem': 'Brinco integrado à Notificação com Sucesso',
                    'integrado': True,
                    'sisbov': sisbov,
                    'rfid': rfid,
                    'sexo': sexo,
                    'lote': lote or '',
                    'nro_meses': nro_meses_str,
                    'total_gravados': total_gravados,
                    'controle': resultado['controle'],
                    'controle_novo': False,
                    'total_lancado': resultado['total'],
                    'conferidos': resultado['conferidos'],
                    'faltam': resultado['faltam'],
                })

        gta_reserva = None
        if id_gta_reserva:   # v1.20.0 - CASO 1: confere a GTA antes de gravar a leitura reservada
            gta_reserva = (
                db.query(Gta).filter(Gta.id == int(id_gta_reserva)).with_for_update().first()
            )
            if (gta_reserva is None or gta_reserva.id_propriedade != int(id_propriedade)
                    or gta_reserva.tipo_movimento != TIPO_BANCO_COMPRA
                    or gta_reserva.status_brincagem != 'PENDENTE'):
                return jsonify({'erro': 'Esta GTA não está mais pendente de Brincagem. Volte à Seleção.'}), 409
            if gta_reserva.data_entrega and data_brincagem < gta_reserva.data_entrega:
                return jsonify({'erro': f'Data de Brincagem anterior à Entrega da GTA '
                                        f'({gta_reserva.data_entrega.strftime("%d/%m/%Y")}).'}), 400
            if _lidos_reservados(db, gta_reserva.id) >= (gta_reserva.qtde_animais or 0):
                return jsonify({'erro': 'GTA completa: todos os animais já foram lidos.'}), 409

        brincagem = Brincagem(
            id_gta=None,
            id_gta_reservada=gta_reserva.id if gta_reserva is not None else None,   # v1.20.0
            id_propriedade=int(id_propriedade),
            sexo=sexo,
            id_especie=int(id_especie),
            id_raca=int(id_raca),
            id_idade_meses=id_idade_meses,
            sisbov=sisbov,
            rfid=rfid,
            # v1.4.0 - manejo = 6 ultimos digitos do SISBOV (antes None).
            manejo=_manejo_do_brinco(db, id_propriedade, sisbov),   # v1.15.0 - do estoque
            lote=lote or None,
            saida_brincos=saida_brincos or 'COM',
            peso=peso,
            nascimento=nascimento,
            data_brincagem=data_brincagem,
            tipo_entrada=tipo_entrada,      # v1.5.0
            sts=False,
            numero_comunicado=None,
        )
        db.add(brincagem)

        # v1.1.0 - contador GRAVADOS da DATA (nao mais o total
        # geral), contado ANTES do commit (regra da Sessao 078). O
        # flush() manda o animal novo para o banco dentro da
        # transacao, para ele ja entrar na conta.
        db.flush()

        if gta_reserva is not None:   # v1.20.0 - CASO 1: confere categoria, estoque e, no ultimo brinco, fecha a GTA
            from backend.routers.vincular_gta import _montar_categorias, _pendencia_animal, vincular_automatico
            reservados = (
                db.query(Brincagem)
                .filter(
                    Brincagem.id_gta_reservada == gta_reserva.id,
                    Brincagem.sts == False,   # noqa: E712
                    Brincagem.id_gta.is_(None),
                )
                .order_by(Brincagem.sisbov)
                .all()
            )
            categorias, animais_cat, _mapa = _montar_categorias(db, gta_reserva, reservados)
            novo = next((a for a in animais_cat if a['id'] == brincagem.id), None)
            cat = next((c for c in categorias if novo and c['chave'] == novo['chave']), None)
            texto_gta = ' / '.join(f"{c['necessario']} {c['sexo']} {c['idade_meses']}" for c in categorias)
            if cat is None:
                db.rollback()
                return jsonify({'erro': (
                    f"Este animal ({sexo.title()}, faixa \"{novo['idade_descricao'] if novo else '?'}\") não bate com "
                    f"nenhuma categoria da GTA ({texto_gta}). Confira o sexo e o nascimento."
                )}), 400
            if cat['brincados'] > cat['necessario']:
                db.rollback()
                return jsonify({'erro': (
                    f"A GTA já tem todos os animais de {cat['sexo']} {cat['idade_meses']} "
                    f"({cat['necessario']}). Categorias da GTA: {texto_gta}."
                )}), 400
            pendencia, _brinco = _pendencia_animal(db, brincagem, gta_reserva, id_propriedade)
            if pendencia:
                db.rollback()
                return jsonify({'erro': f'Brinco {sisbov}: {pendencia}.'}), 400

            lidos = len(reservados)
            total = gta_reserva.qtde_animais or 0
            numero_gta_reserva = gta_reserva.numero_gta_completo
            db.commit()   # a leitura fica gravada mesmo que o fechamento da GTA falhe

            completa = False
            aviso = None
            if lidos >= total:
                try:
                    gta_fechar = db.query(Gta).filter(Gta.id == int(id_gta_reserva)).with_for_update().first()
                    reservados = (
                        db.query(Brincagem)
                        .filter(
                            Brincagem.id_gta_reservada == gta_fechar.id,
                            Brincagem.sts == False,   # noqa: E712
                            Brincagem.id_gta.is_(None),
                        )
                        .order_by(Brincagem.sisbov)
                        .with_for_update()
                        .all()
                    )
                    vincular_automatico(db, gta_fechar, reservados, int(id_propriedade),
                                        session['id_produtor'], session['usuario_id'])
                    db.commit()
                    completa = True
                except ValueError as erro:
                    db.rollback()
                    aviso = (f'Os {total} animais foram lidos, mas não foi possível fechar a GTA: {erro} '
                             f'Use Vincular GTA / Brincagem no Hub de Entrada.')
                except Exception:
                    db.rollback()
                    import logging
                    logging.getLogger(__name__).exception('Brincagem com Leitor: falha ao fechar a GTA %s', numero_gta_reserva)
                    aviso = (f'Os {total} animais foram lidos, mas houve erro ao fechar a GTA. '
                             f'Use Vincular GTA / Brincagem no Hub de Entrada e avise a Consiste.')

            return jsonify({
                'sucesso': True,
                'mensagem': 'Gravação Efetuada com Sucesso',
                'rfid': rfid,
                'sisbov': sisbov,
                'total_gravados': lidos,
                'reserva': True,
                'lidos': lidos,
                'total_lancado': total,
                'faltam': max(total - lidos, 0),
                'completa': completa,
                'numero_gta': numero_gta_reserva,
                'aviso': aviso,
            })

        # v1.5.0 - Nascimento: reserva (ou reaproveita) o Numero de
        # Controle da Propriedade + Data e atualiza a quantidade
        # dele - MESMA transacao do animal (mesma logica do Leitor
        # v1.8.0, funcoes compartilhadas de gravacao_nascimento.py).
        controle_numero = None
        controle_novo = False
        if tipo_entrada == TIPO_ENTRADA_NASCIMENTO:
            controle, controle_novo = reservar_controle(
                db,
                id_propriedade=id_propriedade,
                id_produtor=session['id_produtor'],
                uf=uf_propriedade,
                data_brincagem=data_brincagem,
                id_usuario=session.get('usuario_id'),
            )
            atualizar_qtde_controle(db, controle)
            controle_numero = controle.numero_gta_completo

        total_gravados = _contar_gravados_na_data(db, id_propriedade, data_brincagem, tipo_entrada)

        db.commit()

    return jsonify({
        'sucesso': True,
        'mensagem': 'Gravação Efetuada com Sucesso',
        'rfid': rfid,
        'sisbov': sisbov,
        'total_gravados': total_gravados,
        'controle': controle_numero,        # v1.5.0
        'controle_novo': controle_novo,     # v1.5.0
    })


# -------------------------------------------------------
# Rota: POST /produtor/brincagem-bastao/conferir (AJAX) - v1.6.0.
# O peao leu RFID + SISBOV, no brete, de um animal que o ESCRITORIO
# ja lancou no Nascimento: marca como conferido (tb_2001.
# conferido_brete) e devolve os contadores do NAS. Nao cria animal.
# Se o lancamento ainda nao tinha RFID, o RFID lido passa a ser do
# animal (tb_2001 e tb_2017).
# -------------------------------------------------------
@brincagem_bastao.route('/produtor/brincagem-bastao/conferir', methods=['POST'])
def conferir():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    sisbov         = (dados.get('sisbov') or '').strip()
    rfid           = (dados.get('rfid') or '').strip()
    id_propriedade = dados.get('id_propriedade')
    data_tela      = _data_tela(dados.get('data_brincagem'))
    peso_str       = str(dados.get('peso') or '').strip()      # v1.8.0
    tipo_entrada   = (dados.get('tipo_entrada') or '').strip().upper()   # v1.10.0
    id_gta         = str(dados.get('id_gta') or '').strip()              # v1.10.0
    modo_gta       = tipo_entrada == TIPO_BANCO_COMPRA and id_gta.isdecimal()

    if not (sisbov and rfid and id_propriedade and data_tela):
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou. Volte ao Hub de Brincagem e abra de novo.'}), 403
    if sisbov == rfid:
        return jsonify({'erro': 'SISBOV igual ao RFID — leia o brinco visual.'}), 400

    # v1.8.0 / v1.10.0 - peso OBRIGATORIO no brete.
    peso, erro_peso = ler_peso_brete(peso_str)
    if erro_peso:
        return jsonify({'erro': erro_peso}), 400

    # v1.10.1 - Compra por GTA: o brete pode informar/trocar o Lote ao conferir.
    alterar_lote = True   # 1.10.3 - lote OBRIGATORIO em toda conferencia (Compra por GTA e Nascimento)
    lote, erro_lote = ler_lote_brete(dados.get('lote'), obrigatorio=True)
    if erro_lote:
        return jsonify({'erro': erro_lote}), 400

    with get_db_produtor(session['id_produtor']) as db:
        # v1.15.0 - DV incorreto (modelo antigo, 105) e recusado tambem na conferencia.
        if _dv_incorreto(sisbov):
            _registrar_rejeicao(db, id_propriedade, MOTIVO_DV_INCORRETO, sisbov=sisbov)
            return jsonify({'erro': MENSAGEM_DV_INCORRETO, 'mensagem': MENSAGEM_DV_INCORRETO, 'duplicado': True, 'campo': 'sisbov'}), 409

        if modo_gta:
            # v1.10.0 - Compra: o brinco tem de ser DESTA GTA e ainda nao conferido.
            lancado = buscar_brinco(db, id_propriedade, sisbov=sisbov, para_update=True)
            bloqueio = bloqueio_brinco(db, lancado, id_gta, sisbov)
            if bloqueio:
                return jsonify({'erro': bloqueio[1], 'mensagem': bloqueio[1], 'duplicado': True, 'campo': 'sisbov'}), 409
        else:
            lancado = (
                _query_lancado(db, id_propriedade)
                .filter(Entrada.sisbov == sisbov)
                .with_for_update()
                .first()
            )
            if not lancado:
                return jsonify({'erro': 'Brinco não consta em nenhum Nascimento lançado pelo escritório.'}), 404

            bloqueio = _bloqueio_conferencia(db, lancado, data_tela)
            if bloqueio:
                return jsonify({'erro': bloqueio[1], 'mensagem': bloqueio[1], 'duplicado': True, 'campo': 'sisbov'}), 409

        if lancado.rfid and lancado.rfid != rfid:
            mensagem = f'O Brinco {sisbov} está lançado com o RFID {lancado.rfid}, e não com o RFID lido.'
            return jsonify({'erro': mensagem, 'mensagem': mensagem, 'duplicado': True, 'campo': 'rfid'}), 409

        numero = _numero_notificacao(db, lancado)

        if not lancado.rfid:
            bloqueio_rfid = _validar_rfid(db, rfid)
            if bloqueio_rfid:
                return jsonify({'erro': bloqueio_rfid[1], 'mensagem': bloqueio_rfid[1], 'duplicado': True, 'campo': 'rfid'}), 409
            lancado.rfid = rfid
            (
                db.query(Movimentacao)
                .filter(Movimentacao.id_animal == lancado.id)
                .update({Movimentacao.rfid: rfid}, synchronize_session=False)
            )
            # v1.7.1 - tb_7017 (estoque consumido) e tb_3008 (saida do brinco):
            # so onde o RFID ainda esta vazio.
            (
                db.query(EntradaBrincoRfid)
                .filter(
                    EntradaBrincoRfid.id_propriedade == int(id_propriedade),
                    EntradaBrincoRfid.sisbov == sisbov,
                    EntradaBrincoRfid.saida_gta == numero,
                    or_(EntradaBrincoRfid.rfid.is_(None), EntradaBrincoRfid.rfid == ''),
                )
                .update({EntradaBrincoRfid.rfid: rfid}, synchronize_session=False)
            )
            (
                db.query(BrincoSaida)
                .filter(
                    BrincoSaida.id_propriedade == int(id_propriedade),
                    BrincoSaida.sisbov == sisbov,
                    BrincoSaida.gta == numero,
                    or_(BrincoSaida.rfid.is_(None), BrincoSaida.rfid == ''),
                )
                .update({BrincoSaida.rfid: rfid}, synchronize_session=False)
            )
        if alterar_lote:   # v1.10.1 - o brete decide o lote (a pesagem abaixo leva o lote novo)
            lancado.lote = lote
        lancado.conferido_brete = True
        lancado.conferido_em = datetime.now()
        db.flush()

        # v1.8.0 - peso do brete = pesagem de sequencia 1 (tb_4003). v1.10.0 - na Compra, a
        # sequencia seguinte (a 1a pode ser a media do Peso Balancao da Sequencial); o
        # registrar_pesagem calcula a sequencia sozinho.
        registrar_pesagem(db, id_propriedade, sisbov, lancado.rfid, lancado.data_brincagem, peso,
                          lancado.eras_dias, lancado.lote,
                          ORIGEM_BRETE_COMPRA if modo_gta else ORIGEM_BRETE_NASCIMENTO,
                          session.get('usuario_id'))

        # Contadores ANTES do commit (regra da Sessao 078).
        total, conferidos = _contadores_notificacao(db, lancado.id_gta_entrada)
        total_gravados = _contar_gravados_na_data(db, id_propriedade, data_tela, tipo_entrada)   # v1.13.0

        db.commit()

    return jsonify({
        'sucesso': True,
        'mensagem': 'Conferência Efetuada com Sucesso',
        'total_gravados': total_gravados,
        'sisbov': sisbov,
        'rfid': rfid,
        'controle': numero,
        'total_lancado': total,
        'conferidos': conferidos,
        'faltam': total - conferidos,
        'encerrada': (total - conferidos) <= 0,   # v1.10.0; v1.14.0 - tambem Nascimento (Notificacao toda conferida)
    })

# =========================================================
# FIM DE ARQUIVO: backend\routers\brincagem_bastao.py
# =========================================================