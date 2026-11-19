# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\brincagem_consulta.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-20 12:00 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 2.21.0
# v2.21.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v2.20.0: Sessao 122 (2026-11-12 17:40 -03) - Auditoria Etapa 3 (item 4): excluir com id que nao e numero responde com orientacao (antes erro 500). REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Modulo Consulta Brincagem - redesenhado na Sessao 062 a
#     partir de mockups reais do legado GERAS trazidos por
#     Benedito. Escopo continua SOMENTE registros da Brincagem
#     com Leitor (tb_5001_brincagem) - Brincagem Sequencial fica
#     de fora (decisao explicita de Benedito, Sessao 061).
#
#     NAVEGACAO (Regra de Ouro #7): este card existe em DOIS Hubs
#     ao mesmo tempo (hubs.py) - 'entrada' e 'brincagem'. O
#     parametro 'origem' e guardado na SESSAO do Flask (nao
#     encadeado via querystring em 'proximo' da tela
#     selecionar_propriedade_produtor.html - nunca vi o codigo
#     real dela, Regra de Ouro #1).
#
#     TELA PRINCIPAL (lista()), tudo dentro do MESMO uso "conferir
#     o proprio trabalho no Brete" (Benedito, Sessao 062 - nao e
#     campo vs escritorio, e o mesmo usuario no mesmo lugar):
#       - Seletor de Data Brincagem (dropdown com as datas que tem
#         registro para esta Propriedade, mais recente primeiro,
#         ja vem selecionada a mais recente). Trocar recarrega a
#         pagina (GET, querystring data_brincagem).
#       - Quadro "Total de Animais" da Data selecionada.
#       - Dropdown de Lote (dos lotes daquela Data, com
#         quantidade) - filtra a TABELA (client-side, JS puro,
#         sem nova requisicao - confirmado por Benedito, Sessao
#         062) para mostrar so aquele Lote.
#       - Tabela com botoes Alterar e Excluir por linha.
#
#     ALTERAR (rota alterar(), GET mostra formulario / POST grava):
#     edita TODOS os campos MENOS o SISBOV (travado de proposito -
#     "se quiser trocar, exclui e usa o brinco de novo", Benedito,
#     Sessao 062). Data de Brincagem (AJUSTE Sessao 067): campo
#     editavel, vem preenchida com o valor ORIGINAL - so muda se o
#     usuario editar de proposito (ex.: mover o animal pra outra
#     Brincagem). NRO MESES (v2.8.0): o formulario traz o Nro
#     Meses (ja calculado a partir de Data de Brincagem e
#     Nascimento gravados) e, ao salvar, a faixa de idade
#     (id_idade_meses) e recalculada com a MESMA conta do Leitor
#     (meses x 30 dias, dentro de dias_min/dias_max da
#     tb_4006_idade_meses). Mudancas registradas no Log de
#     Operacoes (backend/utils/log_operacoes.py) via
#     registrar_operacao() + registrar_item() - so os campos que
#     de fato mudaram entram em dados_antes/dados_depois.
#     Bloqueado (mesma guarda do Excluir) pela _pode_editar().
#
#     EXCLUIR (v2.6.0 - Sessao 076, decisao de Benedito, Opcao B):
#     mantem a trava de sempre (_pode_editar - bloqueado se
#     numero_comunicado, id_gta ou sts=True). Ao excluir de fato,
#     grava um registro no Log de Operacoes ANTES de apagar a
#     linha - tipo_mudanca='DELETE', dados_antes = SNAPSHOT
#     EXPLICITO (campo a campo, nunca auto-serialize - Regras.txt
#     secao 4) de todos os campos do registro no momento da
#     exclusao. E so um "diario de bordo" (quem excluiu, quando,
#     como era o brinco) - NUNCA aparece como desfazivel na tela
#     de Desfazer (bloqueio feito dentro do proprio
#     log_operacoes.py v1.2.0). Apos excluido, o SISBOV volta a
#     ficar livre pra uma nova leitura.
#
#     ESPECIE/RACA EM MAIUSCULO SEM ACENTO (pedido de Benedito,
#     Sessao 062): o catalogo real (tb_4002_especie/tb_4005_racas)
#     guarda os nomes com acentuacao/case normais - a normalizacao
#     (maiusculo, sem acento) e feita SO NA EXIBICAO (funcao
#     _normalizar() abaixo), o dado gravado no catalogo nao muda.
#
#     v1.0.0: Criacao do modulo (Sessao 061, 20/09/2026, 12:00 -03).
#     v2.0.0: Sessao 062 (20/09/2026, 12:30 -03) - Redesenho
#             completo da tela principal (filtro de Data, contador
#             Total, dropdown de Lote com filtro client-side) e
#             adicao da rota alterar() (edicao completa + Log de
#             Operacoes) - ver DESCRICAO acima para o detalhamento
#             de cada peca.
#     v2.1.0: Sessao 063 (20/09/2026, 12:45 -03) - Trava de
#             Alterar/Excluir AMPLIADA (CONFIRMADO por Benedito -
#             deixou de ser so prudencia minha): alem de
#             numero_comunicado, agora tambem bloqueia se id_gta
#             estiver preenchido (ja vinculado a uma GTA) OU se
#             sts for True (ciclo ja fechado) - nova funcao
#             _pode_editar() centraliza a checagem, usada em
#             lista() (mostra/esconde os botoes), alterar() e
#             excluir() (bloqueio real no servidor).
#     v2.2.0: Sessao 066 (20/09/2026, 15:00 -03) - AJUSTE pedido
#             por Benedito apos teste real: Alterar NAO atualiza
#             mais data_brincagem - o animal continua pertencendo
#             a Brincagem original mesmo apos uma correcao feita
#             depois (antes, mudar so o Lote fazia o registro
#             "sumir" da Data de Brincagem certa na lista). A
#             data/hora da correcao passa a ser exibida na lista
#             como "Alterado em" (usa atualizado_em, ja existente,
#             com tolerancia de 5s pra nao confundir com a
#             diferenca natural do proprio INSERT).
#     v2.3.0: Sessao 067 (20/09/2026, 15:00 -03) - Data de
#             Brincagem volta a ser EDITAVEL no formulario de
#             Alterar (pedido de Benedito) - vem preenchida com o
#             valor original por padrao (nao muda sozinha, mesmo
#             espirito da v2.2.0), mas o usuario pode trocar de
#             proposito pra mover o animal pra outra Brincagem.
#             Mudanca passa a entrar na captura de dados_antes/
#             dados_depois do Log de Operacoes, igual aos demais
#             campos.
#     v2.4.0: Sessao 068 (20/09/2026, 15:20 -03) - Rota
#             inconformidades() NOVA e completa (lista tb_5003_
#             rejeicoes_brincagem filtrada pela Data selecionada).
#             Rotas imprimir() e inconformidades_imprimir() ainda
#             SAO PLACEHOLDER (retornam 501) - aguardando ver o
#             arquivo real backend/utils/pdf_reportlab.py antes de
#             montar os PDFs (Regra de Ouro #1/#3), existem so pra
#             a tela nao ter link morto.
#     v2.5.0: Sessao 068 cont. (20/09/2026, 15:30 -03) - Os 2
#             placeholders de PDF SUBSTITUIDOS pela implementacao
#             real, apos ver pdf_relatorio_eras.py (arquivo real,
#             confirmou a API do utilitario de PDF): imprimir()
#             monta o Relatorio de Brincagem por Lote (delega a
#             backend/utils/pdf_relatorio_brincagem.py, mesmo
#             padrao do ERAS) e inconformidades_imprimir() monta o
#             PDF de Inconformidades direto no router (tabela
#             simples, sem crosstab).
#     v2.6.0: Sessao 076 (21/09/2026, 10:00 -03) - Excluir passa a
#             gravar no Log de Operacoes (decisao de Benedito,
#             Opcao B - historico/auditoria, nunca desfazivel; ver
#             log_operacoes.py v1.2.0 para o bloqueio do lado do
#             "desfazer"). Snapshot explicito de todos os campos
#             do registro capturado ANTES do db.delete() e gravado
#             como dados_antes (tipo_mudanca='DELETE',
#             dados_depois=None). id_propriedade da operacao vem
#             do proprio registro.id_propriedade.
#     v2.7.0: Sessao 076 cont. (21/09/2026, 10:00 -03) - BUG REAL
#             de navegacao corrigido (Regra de Ouro #4): lista()
#             calcula url_voltar pelo numero de pares Propriedade/
#             Produtor (_calcular_url_voltar_lista) - mais de 1
#             par volta pra tela de selecao; 1 par volta pro Hub.
#             Nenhuma mudanca nas demais rotas.
#     v2.8.0: Sessao 079 (24/09/2026, 07:55 -03) - PONTA SOLTA
#             corrigida (apontada na conversa com Benedito): o
#             Alterar nunca atualizava a faixa de idade
#             (id_idade_meses). Corrigir o Nascimento na mao
#             deixava a faixa antiga gravada - e e ela que o
#             Vincular GTA usa para bater as categorias da GTA.
#             Mudancas SO na rota alterar():
#               - NOVO campo Nro Meses (obrigatorio). Ao abrir, vem
#                 calculado de (Data de Brincagem - Nascimento) / 30
#                 (NOVA funcao _calcular_nro_meses()).
#               - A tela recebe as 5 faixas da tb_4006 para mostrar
#                 a faixa ao lado do campo (so conferencia visual).
#               - POST recalcula id_idade_meses com a mesma conta do
#                 Leitor (NOVA funcao _localizar_faixa()); fora de
#                 qualquer faixa = "Numero de Meses incorreto".
#                 Mudanca de faixa entra no Log de Operacoes.
#               - As 3 chamadas de render_template da rota viraram
#                 uma unica funcao interna _tela() (mesmo conteudo).
#               - BUG REAL de Log corrigido: Peso gravado (Decimal
#                 "350.00") comparado com Peso digitado (float
#                 "350.0") sempre parecia diferente - todo Salvar
#                 registrava uma mudanca falsa de Peso. Agora os
#                 dois lados sao comparados como float.
#               - Mensagens "invalida/invalidos" trocadas por
#                 "incorreta/incorretos" (Regras.txt secao 4) - em
#                 alterar() e no "Dados incorretos." de excluir().
#                 Comentario desatualizado da rota ("atualiza
#                 data_brincagem para hoje") corrigido.
#             Nenhuma outra mudanca de comportamento nas demais
#             rotas.
#     v2.9.0: Sessao 079 (24/09/2026, 08:20 -03) - Ajuste VISUAL
#             da lista (pedido de Benedito). Mudancas SO em lista():
#               - Cada linha ganha 'idade' (descricao da faixa da
#                 tb_4006, a mesma do Relatorio de Brincagem).
#               - Peso exibido INTEIRO (300, nao 300.00).
#               - ORDEM DAS LINHAS (NOVA funcao _chave_ordenacao()):
#                 Sexo (FEMEA, depois MACHO) -> Idade (faixa mais
#                 nova primeiro, pela ordem oficial codigo_geras) ->
#                 SISBOV crescente. Antes: ultima gravada primeiro.
#                 Motivo (Benedito): quem vai trocar uma femea por
#                 um macho acha o bloco do sexo inteiro junto, com
#                 os brincos em sequencia.
#             Nenhuma outra rota alterada.
#     v2.10.0: Sessao 082 (29/09/2026, 20:05 -03) - Pacote 3A (Tipo
#             de Entrada + Numero de Controle do Nascimento):
#               - lista(): NOVO filtro TIPO (Compra / Nascimento,
#                 querystring tipo_entrada, padrao Compra). Datas,
#                 total, lotes e linhas passam a ser do Tipo
#                 escolhido. No Nascimento, cada linha mostra o
#                 NUMERO DE CONTROLE (NAS): o aberto da data para as
#                 leituras pendentes, ou o da Notificacao ja gerada
#                 (id_gta). A tela recebe tipo_entrada e a lista de
#                 tipos.
#               - alterar(): animal de NASCIMENTO nao pode trocar a
#                 Data de Brincagem (ela define o Numero de
#                 Controle) - regra de Benedito: "se estiver errado,
#                 exclui e le de novo". Bloqueio no SERVIDOR. O Tipo
#                 nunca foi editavel no Alterar.
#               - excluir(): depois de apagar uma leitura de
#                 Nascimento, acerta o Numero de Controle da data
#                 (backend/utils/gravacao_nascimento.py): atualiza a
#                 quantidade; se zerou, LIBERA o numero (se for o
#                 ultimo NAS) ou deixa registrado com 0 animais -
#                 sempre com Log. A resposta traz 'aviso' quando o
#                 Controle zera.
#               - imprimir(): aceita tipo_entrada (filtra quando
#                 vier) - Compra e Nascimento da mesma data/lote nao
#                 se misturam no Relatorio.
#               - _snapshot_brincagem(): inclui tipo_entrada.
#             Nenhuma mudanca em _pode_editar(), Inconformidades e
#             PDF de Inconformidades.
#     v2.11.0: Sessao 083 (30/09/2026, 12:00 -03) - pedidos de
#             Benedito depois do teste do 3A:
#               - lista(): o filtro TIPO abre EM BRANCO quando se
#                 entra pelo card do Hub (antes vinha Compra, e
#                 Benedito olhou animais de Compra achando que eram
#                 de Nascimento). Sem Tipo escolhido, a tela mostra
#                 so o aviso "Selecione o Tipo de Entrada".
#               - "VOLTAR PARA ONDE ESTAVA": a lista anota na
#                 SESSAO (chave brincagem_consulta_filtro) a
#                 Propriedade, o Tipo e a Data em que o usuario
#                 esta. Quem volta do Alterar, do Vincular GTA ou
#                 das Inconformidades cai no mesmo Tipo e Data, sem
#                 precisar mexer nos outros modulos. iniciar()
#                 (card do Hub) apaga a anotacao = comeca do zero.
#               - LOTE: o link Alterar leva o Lote filtrado (JS da
#                 lista); alterar() GET guarda na anotacao e a
#                 lista reaplica o filtro UMA vez na volta
#                 (lote_inicial) - depois a anotacao do Lote e
#                 descartada.
#               - alterar(): envia tipo_entrada_descricao para a
#                 tela mostrar o Tipo (so leitura). Trava da Data no
#                 Nascimento continua no servidor (decisao de
#                 Benedito: por hora NAO muda de data).
#             Nenhuma mudanca em excluir(), imprimir(),
#             Inconformidades e PDFs.
#     v2.11.1: Sessao 083 (30/09/2026, 12:00 -03) - SEGURANCA,
#             achado na leitura do codigo e autorizado por Benedito:
#             nenhuma rota conferia se a Propriedade da URL era do
#             usuario logado (trocando o numero no endereco dava
#             para abrir a Consulta de outra fazenda do mesmo
#             Produtor). NOVA funcao _propriedade_do_usuario():
#             a Propriedade tem de ser de um par do usuario
#             (buscar_pares_propriedade_produtor) E do Produtor da
#             sessao - mesma regra do escritorio de Nascimento.
#             Aplicada em: lista(), alterar() (URL e tambem a
#             Propriedade do proprio registro), excluir() (a
#             Propriedade do registro - resposta 403),
#             inconformidades(), imprimir() e
#             inconformidades_imprimir(). Falhou = volta para a
#             Home (excluir: erro na tela). Nenhuma outra mudanca.
#     v2.12.0: Sessao 084 (02/10/2026, 13:00 -03) - NASCIMENTO LANCADO PELO
#             ESCRITORIO APARECE NA CONSULTA (pedido de Benedito): os
#             animais de Notificacoes NAS ainda NAO IMPRESSAS entram na
#             lista do Tipo Nascimento SO PARA CONSULTA (sem Alterar e sem
#             Excluir - pode_editar=False), junto das leituras pendentes
#             do brete, na mesma ordem Sexo -> Idade -> SISBOV, com o
#             Controle (NAS) e o status 'conferido'/'a conferir' no brete.
#             As datas das Notificacoes tambem entram no seletor de Data.
#             Impressa a Notificacao, os animais SOMEM desta Consulta. Os
#             campos novos da linha: 'origem' ('notificacao'), 'conferido'.
#             Alterar, Excluir, Inconformidades e PDFs SEM mudanca.
#     v2.13.0: Sessao 085 (04/10/2026, 18:20 -03) - MESMO PROCESSO NO
#             ESCRITORIO E NO BRETE (decisao de Benedito): depois que a
#             Notificacao de Nascimento e IMPRESSA, os animais dela saem
#             da Consulta Brincagem tambem quando vieram de leitura do
#             brete (linhas da tb_5001 com id_gta apontando para uma NAS
#             que ja esta na tb_7020). Antes so os animais lancados pelo
#             escritorio sumiam; as leituras do brete ficavam para sempre
#             (travadas), e 2 animais de Notificacoes impressas se
#             comportavam diferente. A regra vale na lista, no seletor de
#             Data (uma Data so com linhas ja impressas deixa de aparecer)
#             e no PDF do Imprimir Lote - tela e impressao sempre batem.
#             SO Nascimento: Compra nao muda. Nova funcao
#             _fora_de_notificacao_impressa(). O historico do animal
#             continua na Consulta por Manejo. Nenhuma outra mudanca.
#     v2.14.0: Sessao 090 (08/10/2026, 08:35 -03) - FAZENDA EM USO (Lote 4):
#             FAZENDA EM USO (Regra de Ouro #13): a tela "Selecionar Propriedade" deixa
#             de aparecer quando ha fazenda em uso (auth.resolver_fazenda_em_uso).
#               - iniciar(): com fazenda em uso, abre a Consulta direto nela.
#               - VOLTAR (Regra #9): vai para os Hubs NOVOS (entrada ou
#                 brincagem, conforme a origem); so volta para a selecao quem
#                 tem 2+ pares e nenhuma fazenda em uso.
#               - TRAVA em _propriedade_do_usuario(): Propriedade diferente da
#                 fazenda em uso (outra aba) = negado em TODAS as rotas (lista,
#                 alterar, excluir, inconformidades e as 2 impressoes). As telas
#                 mandam para o iniciar() (que abre a fazenda em uso) por
#                 _negado(); o Excluir (AJAX) responde 403 sem apagar nada.
#             Nenhuma outra mudanca. Templates inalterados.
#     v2.15.0: Sessao 094 (12/10/2026, 20:30 -03) - AUDITORIA DE COMPRAS: O nome do Produtor da tela vem do vinculo do Produtor LOGADO (antes, .first() da
#             Propriedade: com 2+ Produtores na fazenda aparecia o nome errado).
#             REVERSAO: devolver .bak_antes_auditoria_compras.
#     v2.16.0: Sessao 094 (12/10/2026, 20:45 -03) - AUDITORIA DE CONSULTAS/CORRECOES: (1) alterar() (POST) e excluir() travam a linha da brincagem (FOR UPDATE): Vincular GTA ou
#             Comunicado no meio nao deixam mais alterar/apagar registro recem-travado. (2) alterar(): peso pela
#             regra do brete (obrigatorio, > 100 kg). (3) alterar(): Nascimento nao pode ser depois da Brincagem,
#             e a Brincagem nao pode ser futura. REVERSAO: devolver .bak_antes_auditoria_consulta.
#     v2.17.0: Sessao 095 (13/10/2026, 10:30 -03) - A CONSULTA SO MOSTRA PENDENTES: animal com sts verdadeiro (ja
#             vinculado a GTA / ja virou estoque; no Nascimento, Notificacao ja GERADA) SOME da lista, do seletor de Data,
#             do Total de Animais, dos Lotes e do Imprimir Lote (tela e PDF usam o mesmo filtro). Vale para Compra e
#             Nascimento (decisao de Benedito). Saiu o filtro por Notificacao IMPRESSA (v2.13.0) e o bloco que mostrava as
#             Notificacoes nao impressas so para consulta (v2.12.0): a impressao da NAS fica na tela Notificacao de
#             Nascimentos. REVERSAO: devolver .bak_antes_sts_pendentes.
#     v2.18.0: Sessao 106 (26/10/2026, 16:00 -03) - PONTA SOLTA (auditoria): leitura RESERVADA a uma GTA no brete (Leitor/Bastao, tb_5001.id_gta_reservada)
#             aparece na lista com o selo 'EM LEITURA - GTA X' em vez de Alterar/Excluir, sem caixa de selecao, e Alterar/Excluir recusam o registro
#             (a reserva so termina no brete). _pode_editar() NAO mudou (alimenta o Vincular). REVERSAO: .bak_antes_s106s.
#     v2.18.1: Sessao 106 - SAIDA DA RESERVA: leitura reservada PODE ser Excluida (e a unica forma de soltar uma GTA abandonada no meio da leitura);
#             so o Alterar continua bloqueado. REVERSAO: .bak_antes_s106t.
#     v2.19.0: Sessao 106 - BRINCO LIDO NO BRETE JA ESTA NO ANIMAL: o Excluir de leitura de COMPRA e recusado (brinco aplicado nunca volta ao estoque;
#             erro de leitura vai pelo Cancelamento de Brincos). Nascimento segue como antes. NOVA rota POST /produtor/brincagem-consulta/soltar-gta:
#             solta a leitura reservada da GTA (id_gta_reservada=None, com Log); a leitura continua existindo e pode ir para outra GTA. REVERSAO: .bak_antes_s106u.
# =========================================================

import unicodedata
from datetime import datetime, date
from backend.utils.conferencia_compra import ler_peso_brete   # v2.16.0

from flask import Blueprint, render_template, request, redirect, session, jsonify, send_file
from sqlalchemy import or_, text, true
from sqlalchemy.orm import Session
from io import BytesIO
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from backend.database import engine
from backend.models import Propriedade, PropriedadeProdutor, Produtor
from backend.models.tb_5001_brincagem import Brincagem
from backend.models.tb_5003_rejeicoes_brincagem import RejeicaoBrincagem
from backend.models.tb_4005_racas import Raca
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.pdf_relatorio_brincagem import gerar_pdf_relatorio_brincagem
from backend.models.tb_4001_gta import Gta
from backend.models.tb_2001_entradas import Entrada
from backend.utils.regras_sisbov import (
    TIPOS_ENTRADA, TIPO_ENTRADA_COMPRA, TIPO_ENTRADA_NASCIMENTO, descricao_tipo_entrada,
)
from backend.utils.gravacao_nascimento import buscar_controle_aberto, tratar_controle_apos_exclusao
from backend.utils.pdf_reportlab import (
    LARGURA_UTIL, MARGEM_H, MARGEM_V, PAGE_SIZE,
    criar_bloco_dados, criar_tabela_padrao, estilo_rodape, estilo_titulo,
)


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
brincagem_consulta = Blueprint('brincagem_consulta', __name__)


# -------------------------------------------------------
# BUG REAL corrigido (Sessao 064): o navegador guardava em cache
# as telas deste modulo (Selecionar Propriedade, Lista, Alterar) -
# como o conteudo muda de Produtor pra Produtor (cada um com seu
# proprio catalogo de Racas), um cache antigo podia reenviar um
# id_raca que so existia no Produtor testado anteriormente,
# quebrando o INSERT/UPDATE com ForeignKeyViolation. Aplicado em
# TODAS as rotas deste blueprint.
# -------------------------------------------------------
@brincagem_consulta.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta

NOME_MODULO_LOG = 'brincagem_consulta'

SEXOS_VALIDOS = ['MACHO', 'FEMEA']

# v2.8.0 - mesma aproximacao do Leitor/Bastao (1 mes = 30 dias),
# usada para converter Nro Meses em dias e achar a faixa.
DIAS_POR_MES = 30

# v2.8.0 - limite do campo Nro Meses (2 digitos, mesma regra do
# Leitor: "nenhum animal na entrada tera mais de 99 meses").
NRO_MESES_MAXIMO = 99

# v2.10.0 - codigos aceitos do Tipo de Entrada (lista fixa).
CODIGOS_TIPO_ENTRADA = tuple(codigo for codigo, _ in TIPOS_ENTRADA)

# v2.11.0 - chave da SESSAO onde a lista anota onde o usuario esta
# (Propriedade, Tipo, Data e, so na ida para o Alterar, o Lote).
SESSAO_FILTRO = 'brincagem_consulta_filtro'


# -------------------------------------------------------
# Funcao (NOVA, v2.11.0): _ler_filtro_sessao() - devolve a
# anotacao da lista SO se for da mesma Propriedade (trocou de
# Propriedade = anotacao nao vale). Sempre devolve um dict.
# -------------------------------------------------------
def _propriedade_do_usuario(id_propriedade):
    # ---------------------------------------------------
    # v2.11.1 - trava de seguranca: a Propriedade precisa ser de um
    # par Propriedade/Produtor do usuario logado E do Produtor que
    # esta na sessao. Qualquer coisa estranha (vazio, nao numero)
    # = False.
    # ---------------------------------------------------
    try:
        id_int = int(id_propriedade)
    except (TypeError, ValueError):
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    # v2.14.0 - TRAVA DA FAZENDA EM USO: Propriedade diferente da fazenda em
    # uso (trocada em outra aba) = negado.
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and par_em_uso.id_propriedade != id_int:
        return False
    return any(
        par.id_propriedade == id_int and par.id_produtor == session.get('id_produtor')
        for par in pares
    )


# -------------------------------------------------------
# Negado (v2.14.0): com fazenda em uso, a Propriedade errada manda para o
# iniciar() (que abre a fazenda em uso); sem fazenda em uso, Home como antes.
# -------------------------------------------------------
def _negado():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        origem = session.get('brincagem_consulta_origem', 'brincagem')
        return redirect(f'/produtor/brincagem-consulta/iniciar?origem={origem}')
    return redirecionar_home()


def _ler_filtro_sessao(id_propriedade):
    filtro = session.get(SESSAO_FILTRO) or {}
    if filtro.get('id_propriedade') != str(id_propriedade):
        return {}
    return filtro


def _voltar_por_origem(origem):
    # v2.14.0 - Hubs novos (agrupados).
    return '/produtor/hub-novo/entrada' if origem == 'entrada' else '/produtor/hub-novo/brincagem'


# -------------------------------------------------------
# Funcao (v2.7.0): calcula o destino REAL do Voltar para a tela
# lista(), respeitando o caminho que o usuario de fato percorreu
# (Regra de Ouro #4 - nunca fixo).
# - Mais de 1 par Propriedade/Produtor -> passou pela tela de
#   Selecionar Propriedade -> Voltar aponta pra ela.
# - So 1 par -> a selecao foi pulada -> Voltar aponta pro Hub.
# -------------------------------------------------------
def _calcular_url_voltar_lista(origem):
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    # v2.14.0 - com fazenda em uso a selecao e pulada: volta direto ao Hub.
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return f'/produtor/brincagem-consulta/iniciar?origem={origem}'
    return _voltar_por_origem(origem)


# -------------------------------------------------------
# Normaliza texto para MAIUSCULO SEM ACENTO, so para exibicao
# (Especie/Raca) - pedido de Benedito, Sessao 062. O dado gravado
# no catalogo NAO muda, so o que aparece na tela.
# -------------------------------------------------------
def _normalizar(texto):
    if not texto:
        return texto
    sem_acento = unicodedata.normalize('NFKD', texto)
    sem_acento = ''.join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.upper()


# -------------------------------------------------------
# Trava de Alterar/Excluir (CONFIRMADO por Benedito, Sessao 063):
# um registro NAO pode ser alterado nem excluido se:
#   - numero_comunicado preenchido (ja virou documento oficial)
#   - id_gta preenchido (ja foi vinculado a uma GTA)
#   - sts = True (ciclo ja fechado)
# -------------------------------------------------------
def _pode_editar(registro):
    return (
        registro.numero_comunicado is None
        and registro.id_gta is None
        and registro.sts is not True
    )


# -------------------------------------------------------
# Filtro (v2.17.0): so as linhas PENDENTES da tb_5001 (sts falso
# ou vazio). sts vira True quando o animal e vinculado a uma GTA
# (Compra) ou quando a Notificacao de Nascimento e GERADA - dai ele
# ja e estoque e sai da Consulta. Substitui o filtro da v2.13.0.
# -------------------------------------------------------
def _so_pendentes():
    return or_(Brincagem.sts.is_(None), Brincagem.sts == False)   # noqa: E712


# -------------------------------------------------------
# Funcao (NOVA, v2.8.0): _calcular_nro_meses() - Nro Meses que
# aparece ao ABRIR o Alterar. A tb_5001 nao guarda o numero
# digitado no Brete, so o Nascimento - entao ele e reconstruido:
# (Data de Brincagem - Nascimento) em dias / 30, arredondado.
# Sem uma das duas datas, devolve vazio (usuario digita).
# -------------------------------------------------------
def _calcular_nro_meses(registro):
    if not (registro.data_brincagem and registro.nascimento):
        return ''
    dias = (registro.data_brincagem - registro.nascimento).days
    return str(max(round(dias / DIAS_POR_MES), 0))


# -------------------------------------------------------
# Funcao (NOVA, v2.8.0): _localizar_faixa() - acha o id da faixa
# (tb_4006_idade_meses) para um Nro Meses. MESMA conta do
# brincagem_leitor.py/gravar(): meses x 30 dias, dentro de
# dias_min..dias_max. Fora de todas as faixas: None.
# 'faixas' = lista ja carregada do banco (dicts com id,
# dias_min, dias_max).
# -------------------------------------------------------
def _localizar_faixa(faixas, nro_meses):
    dias = nro_meses * DIAS_POR_MES
    for faixa in faixas:
        if faixa['dias_min'] <= dias <= faixa['dias_max']:
            return faixa['id']
    return None


# -------------------------------------------------------
# Funcao (NOVA, v2.9.0): _chave_ordenacao() - ordem das linhas da
# lista (pedido de Benedito, Sessao 079):
#   1. Sexo: FEMEA primeiro, depois MACHO (outro/vazio no fim);
#   2. Idade: faixa mais nova primeiro (codigo_geras da tb_4006;
#      sem faixa vai para o fim do seu Sexo);
#   3. SISBOV crescente (brincos em sequencia).
# 'ordem_faixa' = dict id_idade_meses -> codigo_geras.
# -------------------------------------------------------
ORDEM_SEXO = {'FEMEA': 0, 'MACHO': 1}


def _chave_ordenacao(registro, ordem_faixa):
    return (
        ORDEM_SEXO.get(registro.sexo, 9),
        ordem_faixa.get(registro.id_idade_meses, 99),
        registro.sisbov or '',
    )


# -------------------------------------------------------
# Funcao: _snapshot_brincagem() - monta um dict com TODOS os
# campos de um registro Brincagem, campo a campo (NUNCA
# auto-serialize - Regras.txt secao 4). Usada SO pela exclusao
# (v2.6.0), pra gravar a linha inteira como dados_antes no Log de
# Operacoes.
# -------------------------------------------------------
def _snapshot_brincagem(registro):
    def _str(valor):
        return str(valor) if valor is not None else None

    return {
        'id_gta':             _str(registro.id_gta),
        'id_propriedade':     _str(registro.id_propriedade),
        'sexo':               _str(registro.sexo),
        'id_especie':         _str(registro.id_especie),
        'id_raca':            _str(registro.id_raca),
        'id_idade_meses':     _str(registro.id_idade_meses),
        'sisbov':             _str(registro.sisbov),
        'rfid':                _str(registro.rfid),
        'manejo':              _str(registro.manejo),
        'lote':                _str(registro.lote),
        'saida_brincos':       _str(registro.saida_brincos),
        'peso':                _str(registro.peso),
        'nascimento':          _str(registro.nascimento),
        'data_brincagem':      _str(registro.data_brincagem),
        'tipo_entrada':        _str(registro.tipo_entrada),   # v2.10.0
        'sts':                 _str(registro.sts),
        'numero_comunicado':   _str(registro.numero_comunicado),
        'criado_em':           _str(registro.criado_em),
        'atualizado_em':       _str(registro.atualizado_em),
    }


# -------------------------------------------------------
# Busca Propriedade + Produtor vinculado (vinculo ativo,
# data_fim IS NULL) - MESMO padrao ja usado em
# gta_manual.py::_buscar_dados_exibicao(), so pra montar o
# cabecalho dos PDFs.
# -------------------------------------------------------
def _buscar_propriedade_produtor(id_propriedade):
    with Session(engine) as db:
        propriedade = db.get(Propriedade, id_propriedade)
        produtor = None

        if propriedade:
            vinculo = db.query(PropriedadeProdutor).filter_by(
                id_propriedade=propriedade.id, id_produtor=session['id_produtor'], data_fim=None   # Sessao 094
            ).first()
            if vinculo:
                produtor = db.get(Produtor, vinculo.id_produtor)

    return propriedade, produtor


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-consulta/iniciar — ponto de
# partida. Guarda 'origem' na sessao e resolve Propriedade/
# Produtor (Padrao Reutilizavel N.1). Com 1 unico par, pula direto
# para a lista.
# -------------------------------------------------------
@brincagem_consulta.route('/produtor/brincagem-consulta/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    origem = request.args.get('origem', 'brincagem')
    session['brincagem_consulta_origem'] = origem
    voltar = _voltar_por_origem(origem)

    # v2.11.0 - entrou pelo card do Hub: comeca do zero (Tipo em
    # branco), apagando a anotacao de onde o usuario estava.
    session.pop(SESSAO_FILTRO, None)

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            titulo='Consulta Brincagem — Selecionar Propriedade',
            proximo='/produtor/brincagem-consulta',
            campo_propriedade='id_propriedade',
            voltar=voltar,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='brincagem' if origem == 'brincagem' else 'entrada',
        )

    # v2.14.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/brincagem-consulta?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/brincagem-consulta?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        titulo='Consulta Brincagem — Selecionar Propriedade',
        proximo='/produtor/brincagem-consulta',
        campo_propriedade='id_propriedade',
        voltar=voltar,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='brincagem' if origem == 'brincagem' else 'entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-consulta?id_propriedade=X
# [&data_brincagem=dd/mm/aaaa] — lista principal, com filtro de
# Data e dropdown/contadores de Lote. v2.9.0: coluna Idade em
# Meses, Peso inteiro e linhas ordenadas por Sexo -> Idade ->
# SISBOV (_chave_ordenacao()). v2.11.0: Tipo em branco pelo card;
# Tipo/Data/Lote de volta pela anotacao da sessao.
# -------------------------------------------------------
@brincagem_consulta.route('/produtor/brincagem-consulta')
def lista():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):   # v2.11.1
        return _negado()

    origem = session.get('brincagem_consulta_origem', 'brincagem')

    # v2.11.0 - filtro de Tipo de Entrada:
    #   - veio na URL (mesmo vazio) -> vale o da URL;
    #   - nao veio -> o anotado na sessao (voltando do Alterar,
    #     Vincular GTA, Inconformidades);
    #   - sem nada -> EM BRANCO (antes era Compra).
    filtro_sessao = _ler_filtro_sessao(id_propriedade)
    if 'tipo_entrada' in request.args:
        tipo_entrada = request.args.get('tipo_entrada', '').strip().upper()
    else:
        tipo_entrada = filtro_sessao.get('tipo', '')
    if tipo_entrada not in CODIGOS_TIPO_ENTRADA:
        tipo_entrada = ''

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))

    with engine.connect() as conn:
        especies = {
            row['id']: _normalizar(row['descricao'])
            for row in conn.execute(text('SELECT id, descricao FROM public.tb_4002_especie')).mappings().all()
        }
        # v2.9.0 - faixas de idade: descricao (coluna nova) e
        # codigo_geras (ordem oficial, usada na ordenacao).
        faixas = conn.execute(text(
            'SELECT id, descricao, codigo_geras, dias_min, dias_max FROM public.tb_4006_idade_meses'
        )).mappings().all()
    idade_descricao = {f['id']: f['descricao'] for f in faixas}
    ordem_faixa = {f['id']: f['codigo_geras'] for f in faixas}

    # v2.11.0 - valores de partida; sem Tipo escolhido a tela sai
    # vazia, so com o aviso, sem consultar o banco.
    datas_disponiveis = []
    data_selecionada = None
    registros = []
    racas = {}
    controle_aberto_numero = None
    numeros_por_id_gta = {}
    numeros_reservadas = {}   # v2.18.0

    if tipo_entrada:
        with get_db_produtor(session['id_produtor']) as db:
            racas = {r.id: _normalizar(r.nome) for r in db.query(Raca).all()}

            # Datas disponiveis para esta Propriedade (mais recente
            # primeiro) - popula o seletor de Data Brincagem.
            datas_disponiveis = (
                db.query(Brincagem.data_brincagem)
                .filter_by(id_propriedade=int(id_propriedade), tipo_entrada=tipo_entrada)
                .filter(Brincagem.data_brincagem.isnot(None))
                .filter(_so_pendentes())   # v2.17.0
                .distinct()
                .order_by(Brincagem.data_brincagem.desc())
                .all()
            )
            datas_disponiveis = [d[0] for d in datas_disponiveis]

            # v2.11.0 - Data: a da URL; se nao veio, a anotada na
            # sessao (so se for do mesmo Tipo e ainda existir na
            # lista de datas); senao, a mais recente (como antes).
            data_brincagem_str = request.args.get('data_brincagem', '')
            data_da_sessao = False
            if not data_brincagem_str and filtro_sessao.get('tipo') == tipo_entrada:
                data_brincagem_str = filtro_sessao.get('data', '')
                data_da_sessao = True
            data_selecionada = None
            if data_brincagem_str:
                try:
                    data_selecionada = datetime.strptime(data_brincagem_str, '%d/%m/%Y').date()
                except ValueError:
                    data_selecionada = None
            if data_da_sessao and data_selecionada not in datas_disponiveis:
                data_selecionada = None
            if data_selecionada is None and datas_disponiveis:
                data_selecionada = datas_disponiveis[0]

            query = db.query(Brincagem).filter_by(id_propriedade=int(id_propriedade), tipo_entrada=tipo_entrada)
            query = query.filter(_so_pendentes())   # v2.17.0
            if data_selecionada:
                query = query.filter(Brincagem.data_brincagem == data_selecionada)
            registros = query.all()

            # v2.18.0 - GTA a que cada leitura reservada pertence.
            ids_reservadas = {r.id_gta_reservada for r in registros if r.id_gta_reservada}
            if ids_reservadas:
                numeros_reservadas = {
                    g.id: g.numero_gta_completo
                    for g in db.query(Gta).filter(Gta.id.in_(ids_reservadas)).all()
                }

            # v2.10.0 - Nascimento: Numero de Controle de cada linha.
            # Pendente (sem id_gta) -> o Controle aberto da data;
            # ja gerado (id_gta) -> o NAS da propria Notificacao.
            controle_aberto_numero = None
            numeros_por_id_gta = {}
            if tipo_entrada == TIPO_ENTRADA_NASCIMENTO:
                if data_selecionada:
                    controle_aberto = buscar_controle_aberto(db, id_propriedade, data_selecionada)
                    controle_aberto_numero = controle_aberto.numero_gta_completo if controle_aberto else None
                ids_gta = {r.id_gta for r in registros if r.id_gta}
                if ids_gta:
                    numeros_por_id_gta = {
                        g.id: g.numero_gta_completo
                        for g in db.query(Gta).filter(Gta.id.in_(ids_gta)).all()
                    }

    # v2.9.0 - ordem Sexo -> Idade -> SISBOV (antes: id desc).
    registros.sort(key=lambda r: _chave_ordenacao(r, ordem_faixa))

    linhas = []
    contagem_lotes = {}
    for r in registros:
        lote_exibicao = r.lote or '(sem lote)'
        contagem_lotes[lote_exibicao] = contagem_lotes.get(lote_exibicao, 0) + 1

        linhas.append({
            'id': r.id,
            'sisbov': r.sisbov,
            'especie': especies.get(r.id_especie, '-'),
            'raca': racas.get(r.id_raca, '-'),
            'sexo': r.sexo or '-',
            'idade': idade_descricao.get(r.id_idade_meses, '-'),   # v2.9.0
            'nascimento': r.nascimento.strftime('%d/%m/%Y') if r.nascimento else '-',
            'peso': ('%.0f' % r.peso) if r.peso is not None else '-',   # v2.9.0 - inteiro
            'lote': lote_exibicao,
            'gravado_em': r.criado_em.strftime('%d/%m/%Y %H:%M') if r.criado_em else '-',
            'alterado_em': (
                r.atualizado_em.strftime('%d/%m/%Y %H:%M')
                if r.atualizado_em and r.criado_em and (r.atualizado_em - r.criado_em).total_seconds() > 5
                else None
            ),
            'pode_editar': _pode_editar(r) and not r.id_gta_reservada,   # v2.18.0
            'reservada_gta': numeros_reservadas.get(r.id_gta_reservada, '') if r.id_gta_reservada else '',   # v2.18.0
            # v2.10.0 - Numero de Controle (so Nascimento)
            'controle': (
                numeros_por_id_gta.get(r.id_gta, '-') if r.id_gta
                else (controle_aberto_numero or '-')
            ) if tipo_entrada == TIPO_ENTRADA_NASCIMENTO else None,
        })

    lotes_resumo = [{'lote': lote, 'qtde': qtde} for lote, qtde in sorted(contagem_lotes.items())]

    data_selecionada_str = data_selecionada.strftime('%d/%m/%Y') if data_selecionada else ''

    # v2.11.0 - Lote que estava filtrado quando o usuario clicou em
    # Alterar: reaplicado UMA vez (mesmo Tipo e mesma Data).
    lote_inicial = ''
    if (filtro_sessao.get('lote') and filtro_sessao.get('tipo') == tipo_entrada
            and filtro_sessao.get('data') == data_selecionada_str):
        lote_inicial = filtro_sessao['lote']

    # v2.11.0 - anota onde o usuario esta (sem o Lote, que ja foi
    # usado) - base do "voltar para onde estava".
    session[SESSAO_FILTRO] = {
        'id_propriedade': str(id_propriedade),
        'tipo': tipo_entrada,
        'data': data_selecionada_str,
    }

    return render_template(
        'produtor/brincagem_consulta_lista.html',
        propriedade=propriedade,
        id_propriedade=id_propriedade,
        datas_disponiveis=[d.strftime('%d/%m/%Y') for d in datas_disponiveis],
        data_selecionada=data_selecionada_str,     # v2.11.0
        total_animais=len(linhas),
        lotes_resumo=lotes_resumo,
        linhas=linhas,
        tipo_entrada=tipo_entrada,        # v2.10.0 (v2.11.0: pode vir vazio)
        tipos_entrada=TIPOS_ENTRADA,      # v2.10.0
        lote_inicial=lote_inicial,        # v2.11.0
        url_voltar=_calcular_url_voltar_lista(origem),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincagem' if origem == 'brincagem' else 'entrada',
    )


# -------------------------------------------------------
# Rota: GET/POST /produtor/brincagem-consulta/alterar/<id>
# GET mostra o formulario (tudo menos SISBOV, com Nro Meses ja
# calculado - v2.8.0). POST valida, grava, recalcula a faixa de
# idade pelo Nro Meses (v2.8.0) e registra no Log de Operacoes
# SO os campos que mudaram. A Data de Brincagem so muda se o
# usuario editar o campo de proposito.
# -------------------------------------------------------
@brincagem_consulta.route('/produtor/brincagem-consulta/alterar/<int:id_brincagem>', methods=['GET', 'POST'])
def alterar(id_brincagem):
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):   # v2.11.1
        return _negado()

    # ---------------------------------------------------
    # v2.11.0 - o link Alterar da lista leva o Lote que estava
    # filtrado: guarda na anotacao da sessao para a lista
    # reaplicar o filtro na volta (so se a anotacao for da mesma
    # Propriedade).
    # ---------------------------------------------------
    if request.method == 'GET' and 'lote' in request.args:
        filtro = dict(_ler_filtro_sessao(id_propriedade))
        if filtro:
            filtro['lote'] = request.args.get('lote', '')
            session[SESSAO_FILTRO] = filtro

    # ---------------------------------------------------
    # Catalogos do schema public: Especies + (v2.8.0) as 5
    # faixas de idade, em ordem oficial (codigo_geras). As faixas
    # vao para a tela (conferencia visual) e sao usadas aqui no
    # POST para gravar id_idade_meses.
    # ---------------------------------------------------
    with engine.connect() as conn:
        especies = conn.execute(text(
            'SELECT id, codigo, descricao FROM public.tb_4002_especie ORDER BY descricao'
        )).mappings().all()
        faixas_idade = [
            dict(row) for row in conn.execute(text(
                'SELECT id, descricao, dias_min, dias_max '
                'FROM public.tb_4006_idade_meses ORDER BY codigo_geras'
            )).mappings().all()
        ]

    with get_db_produtor(session['id_produtor']) as db:
        racas = db.query(Raca).filter_by(ativo=True, comum=True).order_by(Raca.nome).all()
        consulta_registro = db.query(Brincagem).filter_by(id=id_brincagem)
        if request.method == 'POST':
            consulta_registro = consulta_registro.with_for_update()   # v2.16.0 - trava ate o commit
        registro = consulta_registro.first()

        # ---------------------------------------------------
        # v2.8.0 - funcao interna unica de renderizacao (antes
        # eram 3 blocos iguais de render_template).
        # ---------------------------------------------------
        def _tela(erro, registro_tela, nro_meses_tela):
            return render_template(
                'produtor/brincagem_consulta_alterar.html',
                erro=erro,
                registro=registro_tela,
                especies=especies,
                racas=racas,
                faixas_idade=faixas_idade,
                nro_meses=nro_meses_tela,
                # v2.11.0 - Tipo so para leitura na tela
                tipo_entrada_descricao=(
                    descricao_tipo_entrada(registro_tela.tipo_entrada) if registro_tela else ''
                ),
                id_propriedade=id_propriedade,
                usuario_nome=session.get('usuario_nome'),
                usuario_perfil=session.get('usuario_perfil'),
                cor_primaria='#D4370A',
                nome_sistema='Orion SISBOV',
                menu_ativo='brincagem',
            )

        if not registro:
            return redirecionar_home()
        # v2.11.1 - o animal tem de ser da Propriedade da URL
        if registro.id_propriedade != int(id_propriedade):
            return redirecionar_home()

        if registro.id_gta_reservada and _pode_editar(registro):   # v2.18.0
            return _tela(
                'Este brinco está reservado a uma GTA em leitura no brete (Leitor/Bastão) e não pode ser alterado aqui. Termine a leitura da GTA.',
                None,
                '',
            )

        if not _pode_editar(registro):
            return _tela(
                'Este brinco já saiu do estado "recém-lido" (Comunicado, GTA vinculada ou status fechado) e não pode ser alterado.',
                None,
                '',
            )

        if request.method == 'GET':
            return _tela(None, registro, _calcular_nro_meses(registro))

        # ---------------------------------------------------
        # POST - leitura do formulario
        # ---------------------------------------------------
        id_especie         = request.form.get('id_especie', '')
        id_raca            = request.form.get('id_raca', '')
        sexo               = (request.form.get('sexo') or '').strip().upper()
        nro_meses_str      = (request.form.get('nro_meses') or '').strip()
        nascimento_str     = (request.form.get('nascimento') or '').strip()
        data_brincagem_str = (request.form.get('data_brincagem') or '').strip()
        peso_str           = (request.form.get('peso') or '').strip()
        lote               = (request.form.get('lote') or '').strip().upper()

        def _reexibir(mensagem_erro):
            return _tela(mensagem_erro, registro, nro_meses_str)

        # ---------------------------------------------------
        # POST - validacoes (para no primeiro erro)
        # ---------------------------------------------------
        if not (id_especie and id_raca and sexo and nro_meses_str and nascimento_str):
            return _reexibir('Preencha todos os campos obrigatórios (Espécie, Raça, Sexo, Nro Meses e Nascimento).')
        if sexo not in SEXOS_VALIDOS:
            return _reexibir('Sexo incorreto.')

        ids_especie_validos = {str(e['id']) for e in especies}
        ids_raca_validos = {str(r.id) for r in racas}

        if id_especie not in ids_especie_validos:
            return _reexibir('Espécie incorreta para este Produtor — atualize a página e tente novamente.')
        if id_raca not in ids_raca_validos:
            return _reexibir('Raça incorreta para este Produtor — atualize a página e tente novamente.')

        # ---- v2.8.0 - Nro Meses -> faixa de idade ----
        if not nro_meses_str.isdecimal() or int(nro_meses_str) > NRO_MESES_MAXIMO:
            return _reexibir('Número de Meses incorreto.')
        id_idade_meses = _localizar_faixa(faixas_idade, int(nro_meses_str))
        if id_idade_meses is None:
            return _reexibir('Número de Meses incorreto — fora das faixas de idade.')

        try:
            nascimento = datetime.strptime(nascimento_str, '%d/%m/%Y').date()
        except ValueError:
            return _reexibir('Data de Nascimento incorreta! Use o formato dd/mm/aaaa.')

        if not data_brincagem_str:
            return _reexibir('Data de Brincagem é obrigatória!')
        try:
            data_brincagem = datetime.strptime(data_brincagem_str, '%d/%m/%Y').date()
        except ValueError:
            return _reexibir('Data de Brincagem incorreta! Use o formato dd/mm/aaaa.')

        # v2.10.0 - Nascimento: a Data de Brincagem define o Numero
        # de Controle, entao nao pode ser trocada aqui.
        if registro.tipo_entrada == TIPO_ENTRADA_NASCIMENTO and data_brincagem != registro.data_brincagem:
            return _reexibir(
                'Animal de Nascimento: a Data de Brincagem não pode ser alterada (ela define o '
                'Número de Controle). Se estiver errada, exclua o animal e leia de novo com a data certa.'
            )

        # v2.16.0 - mesma regra do brete: peso obrigatorio e superior a 100 kg (ate 1000).
        peso, erro_peso = ler_peso_brete(peso_str)
        if erro_peso:
            return _reexibir(erro_peso)

        # v2.16.0 - datas coerentes (antes so o Vincular GTA barrava, tarde demais).
        if nascimento > data_brincagem:
            return _reexibir('Data de Nascimento não pode ser depois da Data de Brincagem.')
        if data_brincagem > date.today():
            return _reexibir('Data de Brincagem não pode ser uma data futura.')

        # ---------------------------------------------------
        # POST - captura SO o que mudou (Log de Operacoes)
        # ---------------------------------------------------
        dados_antes = {}
        dados_depois = {}

        def _registrar_mudanca(campo, valor_antigo, valor_novo):
            if str(valor_antigo) != str(valor_novo):
                dados_antes[campo] = str(valor_antigo) if valor_antigo is not None else None
                dados_depois[campo] = str(valor_novo) if valor_novo is not None else None

        # v2.8.0 - Peso comparado como float dos dois lados (antes
        # Decimal "350.00" x float "350.0" gerava mudanca falsa).
        peso_antigo = float(registro.peso) if registro.peso is not None else None

        _registrar_mudanca('id_especie', registro.id_especie, int(id_especie))
        _registrar_mudanca('id_raca', registro.id_raca, int(id_raca))
        _registrar_mudanca('sexo', registro.sexo, sexo)
        _registrar_mudanca('id_idade_meses', registro.id_idade_meses, id_idade_meses)
        _registrar_mudanca('nascimento', registro.nascimento, nascimento)
        _registrar_mudanca('peso', peso_antigo, peso)
        _registrar_mudanca('lote', registro.lote, lote or None)
        _registrar_mudanca('data_brincagem', registro.data_brincagem, data_brincagem)

        # ---------------------------------------------------
        # POST - grava (so se algo mudou) + Log de Operacoes
        # ---------------------------------------------------
        if dados_antes:
            registro.id_especie     = int(id_especie)
            registro.id_raca        = int(id_raca)
            registro.sexo           = sexo
            registro.id_idade_meses = id_idade_meses
            registro.nascimento     = nascimento
            registro.peso           = peso
            registro.lote           = lote or None
            registro.data_brincagem = data_brincagem

            id_operacao = registrar_operacao(
                db,
                id_usuario=session['usuario_id'],
                id_propriedade=int(id_propriedade) if id_propriedade else registro.id_propriedade,
                modulo=NOME_MODULO_LOG,
                descricao=f'Alteração de dados da Brincagem — SISBOV {registro.sisbov}',
            )
            registrar_item(
                db,
                id_operacao=id_operacao,
                tabela='tb_5001_brincagem',
                id_registro=registro.id,
                tipo_mudanca='UPDATE',
                dados_antes=dados_antes,
                dados_depois=dados_depois,
            )

        # Depois do commit nada mais e lido do banco (regra da
        # Sessao 078) - o destino usa so o id_propriedade da URL.
        db.commit()

    destino = f'/produtor/brincagem-consulta?id_propriedade={id_propriedade}'
    return redirect(destino)


# -------------------------------------------------------
# Rota: POST /produtor/brincagem-consulta/excluir (AJAX) — exclui
# um registro de tb_5001_brincagem. Bloqueado se ja tiver
# numero_comunicado, id_gta ou sts=True (_pode_editar()).
#
# v2.6.0 (Sessao 076, decisao de Benedito - Opcao B): ANTES de
# apagar, captura um snapshot da linha inteira e grava no Log de
# Operacoes como tipo_mudanca='DELETE'.
# -------------------------------------------------------
@brincagem_consulta.route('/produtor/brincagem-consulta/soltar-gta', methods=['POST'])
def soltar_gta():   # v2.19.0
    if 'id_produtor' not in session:
        return jsonify({'ok': False, 'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    try:
        id_brincagem = int(dados.get('id'))
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'erro': 'Dados incorretos.'}), 400

    with get_db_produtor(session['id_produtor']) as db:
        registro = db.query(Brincagem).filter_by(id=id_brincagem).with_for_update().first()
        if not registro:
            return jsonify({'ok': False, 'erro': 'Registro não encontrado.'}), 404
        if not _propriedade_do_usuario(registro.id_propriedade):
            return jsonify({'ok': False, 'erro': 'Este brinco não pertence a uma Propriedade sua.'}), 403
        if not registro.id_gta_reservada or not _pode_editar(registro):
            return jsonify({'ok': False, 'erro': 'Este brinco não está reservado a uma GTA em leitura.'}), 409

        id_operacao = registrar_operacao(
            db,
            id_usuario=session['usuario_id'],
            id_propriedade=registro.id_propriedade,
            modulo=NOME_MODULO_LOG,
            descricao=f'Soltar da GTA em leitura — SISBOV {registro.sisbov}',
        )
        registrar_item(
            db,
            id_operacao=id_operacao,
            tabela='tb_5001_brincagem',
            id_registro=registro.id,
            tipo_mudanca='UPDATE',
            dados_antes={'id_gta_reservada': str(registro.id_gta_reservada)},
            dados_depois={'id_gta_reservada': None},
        )
        registro.id_gta_reservada = None
        db.commit()

    return jsonify({'ok': True})


@brincagem_consulta.route('/produtor/brincagem-consulta/excluir', methods=['POST'])
def excluir():
    if 'id_produtor' not in session:
        return jsonify({'ok': False, 'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    # Etapa 3 (item 4): id que nao e numero antes dava erro 500.
    try:
        id_brincagem = int(dados.get('id'))
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'erro': 'Dados incorretos. Atualize a página e tente de novo.'}), 400

    with get_db_produtor(session['id_produtor']) as db:
        registro = db.query(Brincagem).filter_by(id=int(id_brincagem)).with_for_update().first()   # v2.16.0

        if not registro:
            return jsonify({'ok': False, 'erro': 'Registro não encontrado.'}), 404

        # v2.11.1 - o animal tem de ser de uma Propriedade do usuario
        if not _propriedade_do_usuario(registro.id_propriedade):
            return jsonify({'ok': False, 'erro': 'Este brinco não pertence a uma Propriedade sua.'}), 403

        if not _pode_editar(registro):
            return jsonify({'ok': False, 'erro': 'Este brinco já saiu do estado "recém-lido" (Comunicado, GTA vinculada ou status fechado) e não pode ser excluído.'}), 409

        if registro.tipo_entrada != TIPO_ENTRADA_NASCIMENTO:   # v2.19.0
            return jsonify({'ok': False, 'erro': 'Brinco lido no brete já está no animal e não pode ser excluído (ele não volta ao estoque). Se foi erro de leitura, use o Cancelamento de Brincos.'}), 409

        snapshot = _snapshot_brincagem(registro)

        # v2.10.0 - guardados ANTES de apagar (para acertar o Numero
        # de Controle do Nascimento depois).
        era_nascimento   = registro.tipo_entrada == TIPO_ENTRADA_NASCIMENTO
        id_propriedade_r = registro.id_propriedade
        data_brincagem_r = registro.data_brincagem
        sisbov_r         = registro.sisbov

        id_operacao = registrar_operacao(
            db,
            id_usuario=session['usuario_id'],
            id_propriedade=registro.id_propriedade,
            modulo=NOME_MODULO_LOG,
            descricao=f'Exclusão de Brincagem — SISBOV {registro.sisbov}',
        )
        registrar_item(
            db,
            id_operacao=id_operacao,
            tabela='tb_5001_brincagem',
            id_registro=registro.id,
            tipo_mudanca='DELETE',
            dados_antes=snapshot,
            dados_depois=None,
        )

        db.delete(registro)

        # v2.10.0 - Nascimento: acerta o Numero de Controle da data
        # (quantidade; se zerar, libera ou registra com 0 - com Log).
        aviso = None
        if era_nascimento:
            db.flush()
            aviso = tratar_controle_apos_exclusao(
                db,
                id_propriedade=id_propriedade_r,
                id_produtor=session['id_produtor'],
                data_brincagem=data_brincagem_r,
                id_usuario=session['usuario_id'],
                sisbov=sisbov_r,
            )

        db.commit()

    return jsonify({'ok': True, 'aviso': aviso})


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-consulta/inconformidades — lista
# as tentativas de leitura BLOQUEADAS (tb_5003_rejeicoes_
# brincagem), filtradas pela mesma Data Brincagem selecionada na
# tela principal.
# -------------------------------------------------------
@brincagem_consulta.route('/produtor/brincagem-consulta/inconformidades')
def inconformidades():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    data_brincagem_str = request.args.get('data_brincagem', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):   # v2.11.1
        return _negado()

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))

    data_selecionada = None
    if data_brincagem_str:
        try:
            data_selecionada = datetime.strptime(data_brincagem_str, '%d/%m/%Y').date()
        except ValueError:
            data_selecionada = None

    with get_db_produtor(session['id_produtor']) as db:
        query = db.query(RejeicaoBrincagem).filter_by(id_propriedade=int(id_propriedade))
        if data_selecionada:
            query = query.filter(RejeicaoBrincagem.data_tentativa == data_selecionada)
        registros = query.order_by(RejeicaoBrincagem.id.desc()).all()

    linhas = [{
        'sisbov': r.sisbov,
        'rfid': r.rfid or '-',
        'motivo': r.motivo,
        'criado_em': r.criado_em.strftime('%d/%m/%Y %H:%M') if r.criado_em else '-',
    } for r in registros]

    return render_template(
        'produtor/brincagem_consulta_inconformidades.html',
        propriedade=propriedade,
        id_propriedade=id_propriedade,
        data_selecionada=data_brincagem_str,
        linhas=linhas,
        total=len(linhas),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='brincagem',
    )


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-consulta/imprimir — PDF do
# Relatório de Brincagem (Data + Lote especifico, obrigatorio).
# -------------------------------------------------------
@brincagem_consulta.route('/produtor/brincagem-consulta/imprimir')
def imprimir():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    data_brincagem_str = request.args.get('data_brincagem', '')
    lote = request.args.get('lote', '')
    tipo_entrada = request.args.get('tipo_entrada', '').strip().upper()   # v2.10.0

    if not (id_propriedade and data_brincagem_str and lote):
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):   # v2.11.1
        return _negado()

    try:
        data_brincagem = datetime.strptime(data_brincagem_str, '%d/%m/%Y').date()
    except ValueError:
        return redirecionar_home()

    propriedade, produtor = _buscar_propriedade_produtor(int(id_propriedade))

    with engine.connect() as conn:
        idades = conn.execute(text(
            'SELECT id, descricao FROM public.tb_4006_idade_meses ORDER BY id'
        )).mappings().all()
    faixas_idade = [row['descricao'] for row in idades]
    idades_desc = {row['id']: row['descricao'] for row in idades}

    with get_db_produtor(session['id_produtor']) as db:
        racas_codigo = {r.id: r.codigo for r in db.query(Raca).all()}

        filtro_lote = Brincagem.lote == (None if lote == '(sem lote)' else lote)
        registros = (
            db.query(Brincagem)
            .filter_by(id_propriedade=int(id_propriedade), data_brincagem=data_brincagem)
            .filter(filtro_lote)
        )
        # v2.10.0 - Compra e Nascimento nao se misturam no Relatorio.
        if tipo_entrada in CODIGOS_TIPO_ENTRADA:
            registros = registros.filter(Brincagem.tipo_entrada == tipo_entrada)
        # v2.17.0 - so pendentes, igual a tela (tela e impressao sempre batem).
        registros = registros.filter(_so_pendentes())
        registros = registros.order_by(Brincagem.id).all()

    animais = [{
        'sisbov': r.sisbov,
        'manejo': r.manejo,
        'rfid': r.rfid,
        'sexo': r.sexo,
        'nascimento': r.nascimento,
        'idade_faixa': idades_desc.get(r.id_idade_meses),
        'raca_codigo': racas_codigo.get(r.id_raca, '-'),
        'lote': r.lote,
        'peso': float(r.peso) if r.peso is not None else None,
    } for r in registros]

    if not animais:
        return 'Nenhum animal encontrado para esta Data e Lote.', 404

    return gerar_pdf_relatorio_brincagem(animais, faixas_idade, lote, data_brincagem, propriedade, produtor)


# -------------------------------------------------------
# Rota: GET /produtor/brincagem-consulta/inconformidades/imprimir
# — PDF das Inconformidades da Data selecionada.
# -------------------------------------------------------
@brincagem_consulta.route('/produtor/brincagem-consulta/inconformidades/imprimir')
def inconformidades_imprimir():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    data_brincagem_str = request.args.get('data_brincagem', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):   # v2.11.1
        return _negado()

    propriedade, produtor = _buscar_propriedade_produtor(int(id_propriedade))

    data_selecionada = None
    if data_brincagem_str:
        try:
            data_selecionada = datetime.strptime(data_brincagem_str, '%d/%m/%Y').date()
        except ValueError:
            data_selecionada = None

    with get_db_produtor(session['id_produtor']) as db:
        query = db.query(RejeicaoBrincagem).filter_by(id_propriedade=int(id_propriedade))
        if data_selecionada:
            query = query.filter(RejeicaoBrincagem.data_tentativa == data_selecionada)
        registros = query.order_by(RejeicaoBrincagem.id).all()

    linhas_tabela = [
        [indice, r.sisbov, r.rfid or '-', r.motivo]
        for indice, r in enumerate(registros, start=1)
    ]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=PAGE_SIZE,
        leftMargin=MARGEM_H, rightMargin=MARGEM_H,
        topMargin=MARGEM_V, bottomMargin=MARGEM_V,
    )

    titulo_data = data_brincagem_str or datetime.now().strftime('%d/%m/%Y')
    story = [Paragraph(f'INCONFORMIDADES DE CONFERÊNCIAS DO DIA {titulo_data}', estilo_titulo)]

    story += criar_bloco_dados('DADOS DA PROPRIEDADE', [
        ('Produtor:', produtor.nome if produtor else '-', None),
        ('Propriedade:', propriedade.nome if propriedade else '-', None),
    ])
    story.append(Spacer(1, 10))

    if linhas_tabela:
        larguras = [w * LARGURA_UTIL for w in (0.08, 0.28, 0.24, 0.40)]
        story.append(criar_tabela_padrao(
            cabecalhos=['Ind.', 'SISBOV', 'RFID', 'Mensagem'],
            linhas=linhas_tabela,
            larguras=larguras,
            alinhamentos=['CENTER', 'LEFT', 'LEFT', 'LEFT'],
            colunas_destaque=[1],
        ))
    else:
        story.append(Paragraph('Nenhuma inconformidade registrada para esta Data.', estilo_rodape))

    story.append(Spacer(1, 10))
    story.append(Paragraph(f'Total: {len(linhas_tabela)}', estilo_rodape))
    story.append(Paragraph(
        f'Impressão: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}',
        estilo_rodape,
    ))

    doc.build(story)
    buffer.seek(0)

    nome_propriedade = (propriedade.nome if propriedade else 'Propriedade').replace(' ', '_')
    nome_arquivo = f'Inconformidades_{nome_propriedade}_{(data_brincagem_str or "").replace("/", "-")}.pdf'

    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)

# =========================================================
# FIM DE ARQUIVO: backend\routers\brincagem_consulta.py
# =========================================================