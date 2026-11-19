# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\vincular_gta.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-22 17:40 -03
# ATUALIZADO EM: 2026-11-16 10:40 -03
# VERSAO: 1.20.0
# v1.20.0: Sessao 128 (2026-11-16 10:40 -03) - AUDITORIA ETAPA 7b (Regra #57/#73): a trava _propriedade_permitida() passa a conferir tambem que o Produtor do par Propriedade+Produtor e o Produtor da sessao (antes so conferia a Propriedade). REVERSAO: .bak_antes_etapa7b.
# v1.19.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (6 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.18.0: Sessao 123 (2026-11-13 19:25 -03) - AUDITORIA ETAPA 4 (2a passada): Juntar Datas com trava de linha (GTA e animais, como o Salvar) e JSON fora do formato volta com mensagem (antes erro 500). Data futura PERMITIDA ate 7 dias a frente (decisao de Benedito: leitura na quinta/sexta, junta no sabado, saida na terca); alem disso e recusada no Juntar Datas e no Salvar (erro de digitacao). REVERSAO: .bak_antes_etapa4b.
# v1.17.0: Sessao 122 (2026-11-12 19:00 -03) - Auditoria Etapa 4 (Entradas): confere que a GTA e da Propriedade da sessao. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Modulo "Vincular GTA" (Sessao 077) - card renomeado de
#     "Lancar GTA" no Hub de Entrada (ver hubs.py). Cobre o
#     caminho inverso da Brincagem Sequencial: la a GTA vem
#     primeiro e o sistema reserva/consome os brincos na hora;
#     aqui o Brete ja brincou os animais no curral (Leitor ou
#     Bastao, tb_5001_brincagem com id_gta NULL) SEM saber ainda
#     a qual GTA eles pertencem - o Administrativo junta os dois
#     depois, aqui.
#
#     FLUXO (3 telas + 1 acao):
#       1. Duas portas de entrada:
#          - Consulta Brincagem: checkbox por linha + botao
#            "Vincular GTA" -> POST iniciar() (modo 'por_animais');
#          - Card "Vincular GTA" do Hub de Entrada ->
#            iniciar_por_gta() (modo 'por_gta'): escolhe a GTA e a
#            Data de Brincagem na mesma tela.
#       2. /produtor/vincular-gta/selecionar-gta - GTAs de COMPRA
#          com status_brincagem='PENDENTE' da Propriedade.
#       3. /produtor/vincular-gta/conferencia?id_gta=X - painel
#          por categoria da GTA com RESERVA AUTOMATICA (v1.6.0 -
#          ver abaixo).
#       4. POST /produtor/vincular-gta/salvar - grava SO os
#          animais marcados, com a MESMA cadeia completa da
#          Brincagem Sequencial (7017 update, 3008 create, 2001
#          create, 2017 create, 7002/PIA create, 3007 baixa por
#          lote, GTA status_brincagem='BRINCADO') + marca cada
#          Brincagem com id_gta e sts=True. numero_comunicado NAO
#          e gravado aqui (fica para Gerar Comunicado).
#
#     CONFERENCIA ASSERTIVA (v1.6.0 - desenho fechado com
#     Benedito, Sessao 079):
#       - RESERVA AUTOMATICA: em cada categoria da GTA a tela ja
#         marca exatamente a quantidade pedida, pelos MENORES
#         SISBOVs; os que sobram ficam desmarcados (livres para
#         outra GTA). O usuario troca pela caixinha.
#       - NRO MESES editavel por animal (ja vem calculado pela
#         Data de Brincagem e Nascimento - mesma conta do Alterar
#         Brincagem). Ao gravar, Nascimento e faixa (id_idade_
#         meses) mudam JUNTOS (Nascimento = Data de Brincagem -
#         meses x 30) - nunca ficam descasados. Registro no Log de
#         Operacoes, sem motivo (idade do Brete e estimativa -
#         decisao de Benedito).
#       - SEXO: SO LEITURA na Conferencia (decisao de Benedito -
#         o processo ja organiza quantidades e sexos; correcao de
#         sexo, se houver, e pelo Alterar Brincagem).
#       - DESCASADOS: registro antigo cuja faixa gravada nao bate
#         com o Nascimento ganha aviso na tela; so e regravado se
#         o usuario editar o Nro Meses.
#       - PENDENCIAS (conferidas ao ABRIR a tela e de novo no
#         Salvar - funcao _pendencia_animal()): sem Nascimento,
#         sem Data de Brincagem, Nascimento depois da Brincagem,
#         Brincagem antes da Entrega da GTA, brinco fora do
#         estoque, ja utilizado ou duplicado no estoque. Animal
#         com pendencia NAO pode ser marcado.
#       - IDADE REAL na PIA (v1.6.0): meses = (Data de Brincagem -
#         Nascimento) / 30 - substitui a aproximacao antiga pelo
#         meio da faixa.
#       - COTA HILTON (v1.7.0): idade em DIAS na brincagem (Data de
#         Brincagem - Nascimento), pela regra central backend\
#         utils\regras_sisbov.py::eh_cota_hilton() - ate 306 dias.
#
#     JUNTAR DATAS (v1.5.0, Sessao 078): dentro da Conferencia,
#     puxa para a mesma Data de Brincagem os animais livres de
#     OUTRAS datas. Rota juntar_datas() - so a Data de Brincagem
#     muda, sem Log, grava na hora.
#
#     TRAVA DA ENTREGA (v1.5.0): a Data de Brincagem NUNCA pode
#     ser anterior a Data de Entrega da GTA. v1.6.0: deixou de
#     bloquear a tela inteira - o animal nessa situacao vira
#     PENDENCIA (nao pode ser marcado); os demais seguem.
#
#     SELECAO GUARDADA NA SESSAO: 'vincular_gta_ids' (todos os
#     animais trazidos para a Conferencia), 'vincular_gta_id_
#     propriedade' e 'vincular_gta_modo'. O Salvar recebe da tela
#     SO os ids marcados - e confere que sao um subconjunto da
#     selecao da sessao.
#
#     CASAMENTO DE CATEGORIA (Especie+Sexo+Idade): a GTA guarda
#     texto livre (tb_4001_gta_animais); a Brincagem guarda FK.
#     Casamento normalizando os dois lados para MAIUSCULO SEM
#     ACENTO/ESPACO (_normalizar, copia local do mesmo padrao de
#     brincagem_consulta.py/brincagem_sequencial.py). v1.8.0: a
#     Especie casa pelo CODIGO do catalogo ("BOV") dos dois lados
#     - regra de Benedito, Sessao 082 (banco com codigo, tela com
#     a palavra); a tela recebe a descricao ("Bovino").
#
#     v1.0.0: Criacao do modulo (Sessao 077, 22/09/2026, 17:40
#         -03).
#     v1.1.0: Sessao 077 cont. (22/09/2026, 18:10 -03) - Rota
#         conferencia() passa a montar versoes SERIALIZAVEIS de
#         categorias/animais para o template recalcular o
#         casamento no navegador. _montar_categorias() nao mudou.
#     v1.2.0: Sessao 077 cont. (22/09/2026, 18:30 -03) - SEGUNDO
#         caminho de entrada (card "Vincular GTA" do Hub de
#         Entrada, modo 'por_gta'): iniciar_por_gta(),
#         selecionar_gta() nos dois modos, selecionar_brincagem()
#         e selecionar_brincagem_confirmar(). iniciar() passa a
#         marcar modo 'por_animais'.
#     v1.3.0: Sessao 077 cont. (22/09/2026, 21:20 -03) - 3 ajustes
#         de teste real: (1) changelog registrava a gravacao de
#         session['vincular_gta_id_propriedade'] em
#         selecionar_gta() - AUDITORIA DA v1.6.0 CONSTATOU QUE
#         ESSE CODIGO NUNCA ESTEVE NO ARQUIVO (ver v1.6.0);
#         (2) casamento de especie por descricao ("BOVINO"), nao
#         por codigo ("BOV"); (3) conferencia() manda a Data de
#         Brincagem para exibicao.
#     v1.4.0: Sessao 077 cont. (22/09/2026, 21:35 -03) - Tela
#         separada de Selecionar Brincagem ELIMINADA (Data virou
#         dropdown na tela de Selecionar GTA). Rota GET
#         selecionar-brincagem removida; POST mantido.
#         vincular_gta_selecionar_brincagem.html fica OBSOLETO.
#     v1.5.0: Sessao 078 (23/09/2026, 11:40 -03) - JUNTAR DATAS +
#         TRAVA DA ENTREGA: _listar_outras_datas_livres(),
#         _animais_antes_da_entrega(), rota juntar_datas(), trava
#         no salvar().
#     v1.5.1: Sessao 078 (23/09/2026, 12:01 -03) - BUG REAL: leitura
#         de objetos do banco DEPOIS do db.commit() (juntar_datas()
#         e salvar()) - tudo passa a ser lido ANTES do commit.
#     v1.6.0: Sessao 079 (24/09/2026, 18:30 -03) - CONFERENCIA
#         ASSERTIVA + AUDITORIA (regra de Benedito: erro achado =
#         para tudo, corrige e volta). Primeiro teste real do
#         Confirmar mostrou: Data com 99 animais x GTA de 50 (sem
#         como escolher), troca de idade que so mudava a faixa e
#         deixava o Nascimento descasado, e estoque do brinco so
#         conferido no ultimo segundo. Mudancas:
#           NOVO (desenho combinado - ver DESCRICAO):
#           - Reserva automatica + selecao por caixinha: salvar()
#             recebe 'selecionados' (subconjunto da sessao) e
#             grava SO eles; total tem que ser igual ao da GTA.
#           - Nro Meses editavel: salvar() recebe 'ajustes_meses'
#             e grava Nascimento + faixa juntos (NOVAS funcoes
#             _calcular_nro_meses() e _localizar_faixa(), mesma
#             conta de brincagem_consulta.py v2.8.0), com Log.
#           - Sexo nao e mais alterado aqui (motivo_sexo e a
#             correcao de sexo REMOVIDOS do salvar()).
#           - NOVAS funcoes _situacao_brinco() e
#             _pendencia_animal(): pendencias conferidas ao abrir
#             a Conferencia (mandadas para a tela) e de novo no
#             Salvar, ANTES de gravar qualquer coisa.
#           - Idade REAL (Data de Brincagem - Nascimento) na Cota
#             Hilton e na idade da PIA (fecha a pendencia
#             "aproximacao dias_medio / 30").
#           - Resposta do salvar() traz qtde e 'destino' (proxima
#             tela: Selecionar GTA no modo 'por_gta', Consulta
#             Brincagem no modo 'por_animais').
#           - conferencia() manda tambem o nome da Propriedade
#             (janelinha de confirmacao) e as faixas com
#             dias_min/dias_max (faixa ao vivo na tela).
#           CORRECOES DA AUDITORIA:
#           - (A1) selecionar_gta() NUNCA gravava a Propriedade na
#             sessao (so o changelog da v1.3.0 dizia que sim) -
#             usuario com 2+ Propriedades podia cair no Hub ao
#             escolher a GTA. Agora grava, apos conferir que a
#             Propriedade e mesmo do usuario.
#           - (A2) salvar() apagava a Propriedade da sessao apos
#             gravar - a 2a GTA no mesmo fluxo quebraria. Agora
#             so a selecao de animais e apagada.
#           - (A3) o brinco era buscado na tb_7017 com .first(),
#             sem conferir se estava DISPONIVEL (so se existia) -
#             podia consumir brinco ja baixado/reservado ou pegar
#             a linha errada de um historico repetido. Agora so a
#             linha disponivel (mesma regra do Leitor/Bastao).
#           - (A4) sem Data de Brincagem, gravava a data de HOJE
#             em silencio; sem Nascimento, gravava vazio. Agora e
#             ERRO GRAVE (pendencia) - nada e gravado.
#           - (A5) a baixa do saldo do lote (tb_3007) nao conferia
#             se havia saldo - podia ficar negativo. Agora, se o
#             saldo nao cobre, nada e gravado.
#           - Toda recusa depois de mexer em objetos em memoria
#             faz db.rollback() antes de responder (NOVA funcao
#             _recusar()) - nada fica pendurado na transacao.
#           - Header: removida a ATENCAO sobre a aproximacao da
#             Cota Hilton (substituida pela idade real).
#     v1.6.1: Sessao 080 (25/09/2026, 15:50 -03) - BUG REAL achado
#         na 1a impressao da PIA (coluna Manejo vazia): a
#         Brincagem com Leitor/Bastao gravava manejo=None na
#         tb_5001, e o salvar() copiava esse vazio para tb_2001,
#         tb_2017 e tb_7002. Corrigido na origem (brincagem_
#         leitor.py v1.7.0 / brincagem_bastao.py v1.4.0) e aqui
#         como protecao: se a brincagem vier sem manejo, ele e
#         calculado pelos 6 ultimos digitos do SISBOV (mesma regra
#         da Entrada de Brincos) - NOVA funcao _manejo_do(). Os
#         dados ja gravados foram completados por SQL.
#     v1.7.0: Sessao 081 (28/09/2026, 20:05 -03) - 2 ajustes:
#           - REGRA DA COTA HILTON centralizada (decisao de
#             Benedito): a constante local IDADE_MESES_COTA_HILTON
#             (= 10, regra "meses arredondados < 10") foi
#             REMOVIDA. O CTH passa a vir de backend\utils\
#             regras_sisbov.py::eh_cota_hilton(eras_dias) - ate 306
#             dias na data da brincagem. Corrige de quebra o caso
#             do arredondamento: um animal de ~285 dias virava
#             "10 meses" e perdia o CTH mesmo dentro do prazo.
#           - LOG da baixa do lote (7.7): passa a registrar tambem
#             a qtde_saida antes/depois (a Brincagem Sequencial
#             v1.12.1 ja registrava; aqui so o saldo aparecia).
#         A conta de 1 mes = 30 dias (DIAS_POR_MES local) NAO
#         mudou (decisao de Benedito, Sessao 081). Nenhuma outra
#         mudanca de logica.
#     v1.8.0: Sessao 082 (29/09/2026, 06:55 -03) - ESPECIE PELO
#         CODIGO (regra de Benedito: banco com "BOV", tela com
#         "Bovino"). O casamento da v1.3.0 era pela DESCRICAO -
#         um contorno para os dados gravados por extenso
#         ("BOVINO") pela GTA Manual, que travavam a Brincagem
#         Sequencial. Com a GTA Manual gravando o codigo (v1.6.0)
#         e os dados antigos convertidos por SQL (Tabelas\
#         converter_especie_codigo_s082.sql), _montar_categorias()
#         passa a usar backend\utils\especies.py:
#           - chave da categoria da GTA e do animal = CODIGO
#             (codigo_da_especie() aceita tambem texto antigo por
#             extenso, por seguranca);
#           - 'especie' enviada a tela = DESCRICAO do catalogo
#             (vincular_gta_conferencia.html nao muda - ja mostra
#             cat.especie e compara so pela chave).
#         Leitura direta da tb_4002 (engine.connect) substituida
#         pelo tradutor unico. Nenhuma outra mudanca de logica.
#     v1.9.0: Sessao 082 (29/09/2026, 20:05 -03) - Pacote 3A: o
#         Vincular GTA IGNORA as leituras de NASCIMENTO (regra de
#         Benedito - Nascimento nao tem GTA, vai para o Numero de
#         Controle/Notificacao). NOVA funcao _livre_para_vincular()
#         = _pode_editar() + tipo_entrada COMPRA, usada nos 7 pontos
#         que antes chamavam _pode_editar() direto (iniciar,
#         Datas do modo por GTA, Selecionar Brincagem, Juntar Datas,
#         Outras Datas Livres e Salvar). No iniciar(), leitura de
#         Nascimento marcada por engano recebe mensagem propria.
#         Nenhuma outra mudanca de logica.
#     v1.10.0: Sessao 084 (02/10/2026, 23:00 -03) - PESO DO BRETE VIRA PESAGEM
#         (decisao de Benedito): ao fechar a Brincagem de Compra, o peso lido
#         no brete (tb_5001.peso) vira a pesagem de SEQUENCIA 1 do animal na
#         tb_4003_pesos, na Data de Brincagem (backend/utils/pesagem.py,
#         origem BRETE_COMPRA). Entra no Log (INSERT) - o Desfazer apaga a
#         pesagem junto. Sem peso na leitura, nao grava nada. Nenhuma outra
#         mudanca.
#     v1.10.1: Sessao 087 (05/10/2026, 20:35 -03) - O BRETE PREVALECE (acordo com
#         Benedito apos o caso dos brincos 047-052, barrados no Leitor/Bastao so
#         porque o formulario da Sequencial da GTA AMA111115 fora aberto - o
#         brete nao pode esperar). A checagem de brinco DISPONIVEL do Vincular
#         tambem barrava o brinco com reservado_id_gta preenchido, sem olhar o
#         prazo da reserva (30 min) - um brinco lido no brete poderia ser
#         recusado AQUI. Agora a reserva da Brincagem Sequencial nunca bloqueia o
#         Vincular (a Sequencial se adapta - brincagem_sequencial.py v1.17.0); o
#         brinco continua barrado se tiver saida, Comunicado ou ja for de outro
#         animal. Ao vincular, a reserva do brinco continua sendo limpa (linhas
#         reservado_id_gta = None). Nenhuma outra mudanca.
#     v1.11.0: Sessao 090 (08/10/2026, 08:10 -03) - FAZENDA EM USO (Lote 3):
#             FAZENDA EM USO (Regra de Ouro #13): a tela "Selecionar Propriedade" deixa
#             de aparecer quando ha fazenda em uso (auth.resolver_fazenda_em_uso).
#               - iniciar_por_gta(): com fazenda em uso, abre a lista de GTAs
#                 pendentes direto nela. Sem fazenda em uso, ou com 1 par so,
#                 tudo igual a antes.
#               - TRAVA em _propriedade_permitida() (alem de conferir os pares,
#                 recusa Propriedade diferente da fazenda em uso) e nas 4 rotas
#                 que usam a Propriedade guardada na sessao do vinculo
#                 (selecionar-brincagem, conferencia, juntar-datas e salvar):
#                 nada e lido nem gravado se a fazenda em uso mudou.
#               - VOLTAR (Regra #9): _url_voltar_selecionar_gta() - modo por_gta
#                 com 2+ pares e sem fazenda em uso volta para a selecao; nos
#                 demais casos vai ao Hub de Entrada novo (antes: Hub antigo).
#             Nenhuma outra mudanca. Gravacao, conferencia e Log intactos.
#     v1.12.0: Sessao 092 (09/10/2026, 19:40 -03) - BLOCKCHAIN: cada animal
#             vinculado a GTA (compra, vindo da leitura do brete) gera um
#             evento ENTRADA na fila do blockchain (backend/utils/
#             blockchain.py v1.1.0), logo depois da gravacao na tb_2001 e antes
#             do commit. A ficha leva o numero da GTA como origem. A pesagem do
#             brete passa o id_operacao ao registrar_pesagem(), que gera o
#             evento PESAGEM (pesagem.py v1.1.0). So age se o Produtor tem
#             provedor ligado; uma falha no blockchain nunca derruba a
#             gravacao. O Desfazer ja existente cancela/estorna os eventos.
#             Nenhuma outra mudanca - conferencia, gravacao e Log iguais.
#     v1.13.0: Sessao 094 (12/10/2026, 20:30 -03) - AUDITORIA DE COMPRAS: (1) salvar() trava a GTA e os registros da brincagem (FOR UPDATE): duplo clique ou duas
#             abas nao duplicam mais os animais. (2) _manejo_do(): estoque -> brincagem -> regra do
#             modelo (antes: 6 ultimos digitos, errado no 105). (3) o manejo completado na tb_5001
#             entra no Log (o Desfazer o devolve). REVERSAO: devolver .bak_antes_auditoria_compras.
#     v1.14.0: Sessao 101 (20/10/2026, 10:10 -03) - tb_2017 passa a ser copia fiel da tb_2001: a linha de Entrada grava tambem lote, data_brincagem, conferido_brete, conferido_em, id_origem e id_gta_entrada (model tb_2017 v1.2.0). Nenhuma outra mudanca. REVERSAO: devolver .bak_antes_2017_copia_s101.
#     v1.15.0: Sessao 106 (26/10/2026, 14:10 -03) - NOVA funcao vincular_automatico() no fim do arquivo (mesmo vinculo do salvar(), sem tela/sessao e sem
#             commit), usada pela Brincagem com Leitor (brincagem_leitor.py v1.24.0) no ultimo brinco de uma GTA PENDENTE. O salvar() NAO foi alterado.
#             REVERSAO: .bak_antes_s106l.
#     v1.16.0: Sessao 106 (26/10/2026, 15:00 -03) - PONTA SOLTA (auditoria): _livre_para_vincular(registro, id_gta=None) recusa leitura RESERVADA a outra GTA
#             (tb_5001.id_gta_reservada); as listagens (sem id_gta) deixam de oferecer leituras reservadas; salvar() e vincular_automatico() limpam
#             id_gta_reservada ao vincular (sem log). Fluxo normal sem reserva igual a antes. REVERSAO: .bak_antes_s106s.
# =========================================================

import unicodedata
from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import text

from backend.models import Produtor
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4001_gta_animais import GtaAnimal
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.models.tb_5001_brincagem import Brincagem
from backend.models.tb_3007_brincos_entrada import BrincoEntrada
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.models.tb_3008_brincos_saida import BrincoSaida
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_7002_pia import Pia
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.brincagem_consulta import _pode_editar
from backend.utils.multitenant import get_db_produtor
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.pesagem import registrar_pesagem, ORIGEM_BRETE_COMPRA
from backend.utils.blockchain import registrar_evento_animal, TIPO_ENTRADA   # v1.12.0 - blockchain
from backend.utils.regras_sisbov import eh_cota_hilton, manejo_do_sisbov   # v1.13.0
from backend.utils.especies import carregar_especies, codigo_da_especie, mapa_codigo_descricao
from backend.utils.regras_sisbov import TIPO_ENTRADA_COMPRA, TIPO_ENTRADA_NASCIMENTO


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
vincular_gta = Blueprint('vincular_gta', __name__)


# -------------------------------------------------------
# Funcao auxiliar (v1.9.0): a leitura do brete pode ir para uma
# GTA? Precisa estar livre (_pode_editar - sem Comunicado, sem GTA,
# sts aberto) E ser de COMPRA. Nascimento nunca vai para GTA.
# -------------------------------------------------------
def _livre_para_vincular(registro, id_gta=None):
    # v1.16.0 - leitura RESERVADA a uma GTA (Leitor/Bastao) so e livre para a propria GTA.
    # Sem id_gta (listagens), nenhuma leitura reservada aparece para vincular.
    reservada = getattr(registro, 'id_gta_reservada', None)
    if reservada:
        try:
            if int(id_gta) != int(reservada):
                return False
        except (TypeError, ValueError):
            return False
    return _pode_editar(registro) and registro.tipo_entrada == TIPO_ENTRADA_COMPRA


@vincular_gta.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


TAMANHO_MAXIMO_GTA_3008 = 10   # mesmo limite real de tb_3008.gta (String(10))
DIAS_LIBERACAO_ABATE    = 90   # liberacao_abate = data_brincagem + N dias
# v1.7.0: IDADE_MESES_COTA_HILTON removida - a regra da Cota
# Hilton mora em backend\utils\regras_sisbov.py.

# v1.6.0 - mesma aproximacao do Leitor/Bastao/Alterar (1 mes = 30
# dias) e mesmo limite do campo Nro Meses (2 digitos).
DIAS_POR_MES     = 30
NRO_MESES_MAXIMO = 99
DIAS_MAX_BRINCAGEM_FUTURA = 7   # Etapa 4 (2a passada, decisao de Benedito): Data de Brincagem pode ser ate 7 dias a frente (leitura na quinta, junta no sabado, saida na terca); alem disso e erro de digitacao

NOME_MODULO_LOG = 'vincular_gta'

# Destino do Voltar quando a tela de Selecionar Propriedade nunca
# existiu no caminho real (0 ou 1 par) - Regra de Ouro, mesma
# logica ja usada em brincagem_leitor.py/brincagem_bastao.py.
VOLTAR_SELECIONAR_PROPRIEDADE = '/produtor/hub-novo/entrada'
VOLTAR_TELA_SELECAO_COM_MULTIPLOS_PARES = '/produtor/vincular-gta/iniciar-por-gta'


# -------------------------------------------------------
# Normaliza texto para MAIUSCULO SEM ACENTO/ESPACO - mesma
# funcao (copia local) ja usada em brincagem_consulta.py e
# brincagem_sequencial.py.
# -------------------------------------------------------
def _normalizar(texto):
    if not texto:
        return ''
    sem_acento = unicodedata.normalize('NFKD', texto)
    sem_acento = ''.join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.upper().replace(' ', '')


# -------------------------------------------------------
# Funcao (NOVA, v1.6.1): manejo do animal - o gravado na
# brincagem ou, se vazio, os 6 ultimos digitos do SISBOV (mesma
# regra da Entrada de Brincos, brincos_entrada.py).
# -------------------------------------------------------
TAMANHO_MANEJO = 6


def _manejo_do(registro, brinco=None):
    # v1.13.0 - primeiro o manejo do ESTOQUE (tb_7017), depois o da brincagem, depois a regra
    # do modelo (antigo 105: os 6 ANTES do DV). Os 6 ultimos so como ultimo recurso.
    if brinco is not None and brinco.manejo:
        return brinco.manejo
    if registro.manejo:
        return registro.manejo
    try:
        return manejo_do_sisbov(registro.sisbov)
    except ValueError:
        return (registro.sisbov or '')[-TAMANHO_MANEJO:] or None


# -------------------------------------------------------
# Funcao (NOVA, v1.6.0): Nro Meses de um registro, reconstruido
# de (Data de Brincagem - Nascimento) / 30, arredondado - mesma
# conta de brincagem_consulta.py::_calcular_nro_meses(). Sem uma
# das datas: None.
# -------------------------------------------------------
def _calcular_nro_meses(data_brincagem, nascimento):
    if not (data_brincagem and nascimento):
        return None
    return max(round((data_brincagem - nascimento).days / DIAS_POR_MES), 0)


# -------------------------------------------------------
# Funcao (NOVA, v1.6.0): id da faixa (tb_4006) para um Nro Meses -
# meses x 30 dias dentro de dias_min..dias_max. 'faixas' = objetos
# IdadeMeses. Fora de todas: None.
# -------------------------------------------------------
def _localizar_faixa(faixas, nro_meses):
    dias = nro_meses * DIAS_POR_MES
    for faixa in faixas:
        if faixa.dias_min <= dias <= faixa.dias_max:
            return faixa.id
    return None


# -------------------------------------------------------
# Funcao (NOVA, v1.6.0): situacao do brinco no estoque da
# Propriedade (tb_7017). Devolve (linha_disponivel, motivo):
#   - (linha, None)   -> pode ser consumido;
#   - (None, motivo)  -> fora do estoque / ja utilizado /
#                        duplicado no estoque.
# Disponivel = saida_data, saida_gta, saida_origem,
# numero_comunicado e reservado_id_gta todos em branco (mesma
# regra de brincagem_leitor.py::_validar_sisbov()).
# -------------------------------------------------------
def _situacao_brinco(db, id_propriedade, sisbov):
    linhas = (
        db.query(EntradaBrincoRfid)
        .filter_by(id_propriedade=int(id_propriedade), sisbov=sisbov)
        .all()
    )
    if not linhas:
        return None, 'Brinco fora do estoque desta Propriedade'

    disponiveis = [
        b for b in linhas
        if b.saida_data is None and b.saida_gta is None and b.saida_origem is None
        and b.numero_comunicado is None   # v1.10.1 - reserva da Sequencial NAO bloqueia (o brete prevalece)
    ]
    if not disponiveis:
        return None, 'Brinco já utilizado'
    if len(disponiveis) > 1:
        return None, 'Brinco duplicado no estoque — avise a Consiste'
    return disponiveis[0], None


# -------------------------------------------------------
# Funcao (NOVA, v1.6.0): pendencia que IMPEDE o animal de ser
# vinculado (texto curto para a tela) ou None. Conferida ao abrir
# a Conferencia e de novo no Salvar (o servidor nunca confia so
# na tela). Devolve (motivo, linha_brinco_disponivel).
# -------------------------------------------------------
def _pendencia_animal(db, registro, gta, id_propriedade):
    if not registro.nascimento:
        return 'Sem Data de Nascimento', None
    if not registro.data_brincagem:
        return 'Sem Data de Brincagem', None
    if registro.nascimento > registro.data_brincagem:
        return 'Nascimento depois da Brincagem', None
    if registro.data_brincagem > date.today() + timedelta(days=DIAS_MAX_BRINCAGEM_FUTURA):   # Etapa 4 (2a passada)
        return f'Brincagem ({registro.data_brincagem.strftime("%d/%m/%Y")}) mais de {DIAS_MAX_BRINCAGEM_FUTURA} dias no futuro — use Juntar Datas', None
    if gta.data_entrega and registro.data_brincagem < gta.data_entrega:
        return (
            f'Brincagem ({registro.data_brincagem.strftime("%d/%m/%Y")}) antes da Entrega da GTA '
            f'({gta.data_entrega.strftime("%d/%m/%Y")}) — use Juntar Datas'
        ), None

    brinco, motivo = _situacao_brinco(db, id_propriedade, registro.sisbov)
    if motivo:
        return motivo, None
    return None, brinco


# -------------------------------------------------------
# Funcao (NOVA, v1.6.0): recusa do salvar() - desfaz qualquer
# mudanca em memoria/autoflush da transacao ANTES de responder.
# -------------------------------------------------------
def _recusar(db, mensagem, status=400):
    db.rollback()
    return jsonify({'erro': mensagem}), status


# -------------------------------------------------------
# Funcao auxiliar (v1.5.0 - Juntar Datas): Datas de Brincagem com
# animais LIVRES (_pode_editar) FORA da selecao atual, com a
# quantidade de cada uma. Mais recente primeiro.
# -------------------------------------------------------
def _listar_outras_datas_livres(db, id_propriedade, ids_selecionados):
    ids_ja_na_conferencia = set(ids_selecionados or [])

    registros = (
        db.query(Brincagem)
        .filter_by(id_propriedade=id_propriedade)
        .filter(Brincagem.data_brincagem.isnot(None))
        .all()
    )

    contagem_por_data = {}
    for r in registros:
        if r.id in ids_ja_na_conferencia:
            continue
        if not _livre_para_vincular(r):
            continue
        contagem_por_data[r.data_brincagem] = contagem_por_data.get(r.data_brincagem, 0) + 1

    return [
        {'data_br': d.strftime('%d/%m/%Y'), 'data_iso': d.isoformat(), 'quantidade': q}
        for d, q in sorted(contagem_por_data.items(), reverse=True)
    ]


# -------------------------------------------------------
# Funcao auxiliar (v1.6.0): o id_propriedade pertence aos pares
# Propriedade/Produtor do usuario logado?
# -------------------------------------------------------
def _propriedade_permitida(id_propriedade):
    if not str(id_propriedade).isdecimal():
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if str(id_propriedade) not in {str(par.id_propriedade) for par in pares if str(par.id_produtor) == str(session.get('id_produtor'))}:   # v1.20.0 - Produtor do par = Produtor da sessao (Etapa 7b)
        return False
    # v1.11.0 - TRAVA DA FAZENDA EM USO: Propriedade diferente da fazenda em
    # uso (trocada em outra aba) nao e permitida.
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and int(par_em_uso.id_propriedade) != int(id_propriedade):
        return False
    return True


# -------------------------------------------------------
# Destino do Voltar da lista de GTAs pendentes (v1.11.0, Regra de Ouro #9).
# Modo por_gta com 2+ pares e SEM fazenda em uso: a selecao existe, volta
# para ela. Nos demais casos (1 par, fazenda em uso, ou modo por_animais,
# que nasce na Consulta Brincagem): Hub de Entrada novo, como antes.
# -------------------------------------------------------
def _url_voltar_selecionar_gta(modo):
    if modo == 'por_gta':
        pares = buscar_pares_propriedade_produtor(session['usuario_id'])
        if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
            return VOLTAR_TELA_SELECAO_COM_MULTIPLOS_PARES
    return VOLTAR_SELECIONAR_PROPRIEDADE


# -------------------------------------------------------
# Rota: POST /produtor/vincular-gta/iniciar — recebe os ids de
# Brincagem marcados na Consulta Brincagem (modo 'por_animais').
# -------------------------------------------------------
@vincular_gta.route('/produtor/vincular-gta/iniciar', methods=['POST'])
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.form.get('id_propriedade', '')
    ids_str = request.form.getlist('ids')

    if not id_propriedade or not ids_str:
        return 'Selecione ao menos um animal antes de clicar em Vincular GTA.', 400

    if not _propriedade_permitida(id_propriedade):
        return redirecionar_home()

    ids = [int(i) for i in ids_str if i.isdecimal()]

    with get_db_produtor(session['id_produtor']) as db:
        registros = db.query(Brincagem).filter(Brincagem.id.in_(ids)).all()

        if len(registros) != len(ids):
            return 'Um ou mais registros selecionados não foram encontrados. Atualize a página e tente novamente.', 400

        for r in registros:
            if r.id_propriedade != int(id_propriedade):
                return 'Os registros selecionados não pertencem todos à mesma Propriedade.', 400
            # v1.9.0 - Nascimento nunca vai para GTA.
            if r.tipo_entrada == TIPO_ENTRADA_NASCIMENTO:
                return f'O brinco {r.sisbov} é de Nascimento e não pode ser vinculado a uma GTA.', 409
            if not _livre_para_vincular(r):
                return f'O brinco {r.sisbov} já saiu do estado "recém-lido" e não pode ser vinculado a uma GTA.', 409

    session['vincular_gta_ids'] = ids
    session['vincular_gta_id_propriedade'] = id_propriedade
    session['vincular_gta_modo'] = 'por_animais'

    return redirect(f'/produtor/vincular-gta/selecionar-gta?id_propriedade={id_propriedade}')


# -------------------------------------------------------
# Rota: GET /produtor/vincular-gta/iniciar-por-gta — SEGUNDO
# caminho de entrada (card do Hub de Entrada, modo 'por_gta').
# -------------------------------------------------------
@vincular_gta.route('/produtor/vincular-gta/iniciar-por-gta')
def iniciar_por_gta():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            titulo='Vincular GTA — Selecionar Propriedade',
            proximo='/produtor/vincular-gta/selecionar-gta',
            campo_propriedade='id_propriedade',
            voltar=VOLTAR_SELECIONAR_PROPRIEDADE,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='entrada',
        )

    session['vincular_gta_ids'] = None
    session['vincular_gta_modo'] = 'por_gta'

    # v1.11.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        session['vincular_gta_id_propriedade'] = str(par_em_uso.id_propriedade)
        return redirect(f'/produtor/vincular-gta/selecionar-gta?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        session['vincular_gta_id_propriedade'] = str(par.id_propriedade)
        return redirect(f'/produtor/vincular-gta/selecionar-gta?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        titulo='Vincular GTA — Selecionar Propriedade',
        proximo='/produtor/vincular-gta/selecionar-gta',
        campo_propriedade='id_propriedade',
        voltar=VOLTAR_SELECIONAR_PROPRIEDADE,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/vincular-gta/selecionar-gta — lista as
# GTAs de COMPRA pendentes de Brincagem desta Propriedade.
#
# v1.6.0 (A1): confere que a Propriedade e do usuario e GRAVA-A
# NA SESSAO (o changelog da v1.3.0 dizia que isso existia, mas
# o codigo nunca esteve aqui).
# -------------------------------------------------------
@vincular_gta.route('/produtor/vincular-gta/selecionar-gta')
def selecionar_gta():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    modo = session.get('vincular_gta_modo', 'por_animais')
    ids = session.get('vincular_gta_ids')

    if not id_propriedade or not _propriedade_permitida(id_propriedade):
        return redirect('/produtor/hub/entrada')
    if modo == 'por_animais' and not ids:
        return redirect('/produtor/hub/entrada')

    # v1.6.0 (A1) - Propriedade gravada na sessao aqui, nos 2 modos.
    session['vincular_gta_id_propriedade'] = str(id_propriedade)

    with get_db_produtor(session['id_produtor']) as db:
        gtas_db = (
            db.query(Gta)
            .filter(
                Gta.id_propriedade == int(id_propriedade),
                Gta.tipo_movimento == 'COMPRA',
                Gta.status_brincagem == 'PENDENTE',
                Gta.data_entrega.isnot(None),
            )
            .order_by(Gta.data_entrega.asc())
            .all()
        )

        gtas_lista = [{
            'id': gta.id,
            'numero_gta_completo': gta.numero_gta_completo,
            'data_entrega_br': gta.data_entrega.strftime('%d/%m/%Y'),
            'qtde_animais': gta.qtde_animais,
        } for gta in gtas_db]

        # v1.4.0 - modo 'por_gta': lista de Datas de Brincagem na
        # mesma tela (nao depende da GTA escolhida).
        datas_disponiveis = None
        if modo == 'por_gta':
            registros = (
                db.query(Brincagem)
                .filter_by(id_propriedade=int(id_propriedade))
                .filter(Brincagem.data_brincagem.isnot(None))
                .all()
            )
            registros = [r for r in registros if _livre_para_vincular(r)]

            contagem_por_data = {}
            for r in registros:
                contagem_por_data[r.data_brincagem] = contagem_por_data.get(r.data_brincagem, 0) + 1

            datas_disponiveis = [
                {'data_br': d.strftime('%d/%m/%Y'), 'data_iso': d.isoformat(), 'quantidade': q}
                for d, q in sorted(contagem_por_data.items(), reverse=True)
            ]

    return render_template(
        'produtor/vincular_gta_selecionar.html',
        gtas=gtas_lista,
        modo=modo,
        datas_disponiveis=datas_disponiveis,
        total_selecionados=len(ids) if ids else None,
        id_propriedade=id_propriedade,
        url_voltar=_url_voltar_selecionar_gta(modo),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: POST /produtor/vincular-gta/selecionar-brincagem — recebe
# a GTA e a Data escolhidas na tela de Selecionar GTA e carrega
# TODOS os animais livres daquela Data (qualquer Lote) na sessao.
# -------------------------------------------------------
@vincular_gta.route('/produtor/vincular-gta/selecionar-brincagem', methods=['POST'])
def selecionar_brincagem_confirmar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_gta = request.form.get('id_gta', '')
    data_iso = request.form.get('data_brincagem', '')
    id_propriedade = session.get('vincular_gta_id_propriedade')

    if not id_gta.isdecimal() or not data_iso or not id_propriedade:
        return redirect('/produtor/hub/entrada')

    # v1.11.0 - trava da fazenda em uso.
    if not _propriedade_permitida(id_propriedade):
        return redirect(VOLTAR_SELECIONAR_PROPRIEDADE)

    with get_db_produtor(session['id_produtor']) as db:
        registros = (
            db.query(Brincagem)
            .filter_by(id_propriedade=int(id_propriedade), data_brincagem=date.fromisoformat(data_iso))
            .all()
        )
        registros = [r for r in registros if _livre_para_vincular(r)]

        if not registros:
            return redirect(f'/produtor/vincular-gta/selecionar-gta?id_propriedade={id_propriedade}')

        ids = [r.id for r in registros]

    session['vincular_gta_ids'] = ids

    return redirect(f'/produtor/vincular-gta/conferencia?id_gta={id_gta}')


# -------------------------------------------------------
# Funcao auxiliar: monta a comparacao Categoria da GTA x animais.
# Usada no GET (conferencia) e no POST (salvar - revalidar com os
# valores ja ajustados em memoria).
# -------------------------------------------------------
def _montar_categorias(db, gta, registros):
    # v1.8.0 - catalogo pelo tradutor unico: id -> codigo ("BOV")
    # para casar; codigo -> descricao ("Bovino") para a tela.
    especies = carregar_especies()
    mapa_especie_codigo = {e['id']: e['codigo'] for e in especies}
    mapa_descricao = mapa_codigo_descricao(especies)

    idades_db = db.query(IdadeMeses).all()
    mapa_idade_descricao = {i.id: i.descricao for i in idades_db}
    mapa_idade_normalizada = {_normalizar(i.descricao): i.id for i in idades_db}

    categorias_db = db.query(GtaAnimal).filter_by(id_gta=gta.id).order_by(GtaAnimal.id).all()

    categorias = []
    for cat in categorias_db:
        chave = (
            _normalizar(codigo_da_especie(cat.especie, especies) or cat.especie),
            _normalizar(cat.sexo),
            _normalizar(cat.idade_meses),
        )
        categorias.append({
            'chave': chave,
            'especie': mapa_descricao.get(codigo_da_especie(cat.especie, especies), cat.especie),
            'sexo': cat.sexo,
            'idade_meses': cat.idade_meses,
            'necessario': cat.quantidade,
        })

    animais = []
    for r in registros:
        codigo_especie = mapa_especie_codigo.get(r.id_especie, '')
        descricao_idade = mapa_idade_descricao.get(r.id_idade_meses, '')
        chave = (_normalizar(codigo_especie), _normalizar(r.sexo), _normalizar(descricao_idade))
        animais.append({
            'id': r.id,
            'sisbov': r.sisbov,
            'sexo': r.sexo,
            'id_idade_meses': r.id_idade_meses,
            'idade_descricao': descricao_idade,
            'chave': chave,
        })

    for cat in categorias:
        cat['brincados'] = sum(1 for a in animais if a['chave'] == cat['chave'])

    return categorias, animais, mapa_idade_normalizada


# -------------------------------------------------------
# Rota: GET /produtor/vincular-gta/conferencia?id_gta=X — Tela 3.
# v1.6.0: cada animal vai para a tela com Nro Meses calculado,
# aviso de "descasado" e a pendencia (se houver). As faixas vao
# com dias_min/dias_max (faixa ao vivo no navegador).
# -------------------------------------------------------
@vincular_gta.route('/produtor/vincular-gta/conferencia')
def conferencia():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_gta = request.args.get('id_gta', '')
    ids = session.get('vincular_gta_ids')
    id_propriedade = session.get('vincular_gta_id_propriedade')

    if not id_gta.isdecimal() or not ids or not id_propriedade:
        return redirect('/produtor/hub/entrada')

    # v1.11.0 - trava da fazenda em uso.
    if not _propriedade_permitida(id_propriedade):
        return redirect(VOLTAR_SELECIONAR_PROPRIEDADE)

    with get_db_produtor(session['id_produtor']) as db:
        gta = db.get(Gta, int(id_gta))
        if not gta or gta.tipo_movimento != 'COMPRA' or gta.status_brincagem != 'PENDENTE':
            return 'Esta GTA não está pendente de Brincagem (pode já ter sido vinculada). Volte e atualize.', 400

        registros = db.query(Brincagem).filter(Brincagem.id.in_(ids)).order_by(Brincagem.sisbov).all()
        categorias, animais, _ = _montar_categorias(db, gta, registros)

        faixas = db.query(IdadeMeses).order_by(IdadeMeses.id).all()
        idades_disponiveis = [
            {'id': i.id, 'descricao': i.descricao, 'normalizada': _normalizar(i.descricao),
             'dias_min': i.dias_min, 'dias_max': i.dias_max}
            for i in faixas
        ]

        categorias_js = [{
            'especie': cat['especie'], 'sexo': cat['sexo'], 'idade_meses': cat['idade_meses'],
            'necessario': cat['necessario'], 'chave': '|'.join(cat['chave']),
        } for cat in categorias]

        # ---- v1.6.0 - animal completo para a tela ----
        registros_por_id = {r.id: r for r in registros}
        animais_js = []
        for a in animais:
            r = registros_por_id[a['id']]
            nro_meses = _calcular_nro_meses(r.data_brincagem, r.nascimento)
            faixa_pelos_meses = _localizar_faixa(faixas, nro_meses) if nro_meses is not None else None
            pendencia, _ = _pendencia_animal(db, r, gta, id_propriedade)
            animais_js.append({
                'id': a['id'],
                'sisbov': a['sisbov'],
                'sexo': a['sexo'],
                'id_idade_meses': a['id_idade_meses'],
                'especie_norm': a['chave'][0],
                'nro_meses': nro_meses,
                'descasado': faixa_pelos_meses is not None and faixa_pelos_meses != r.id_idade_meses,
                'pendencia': pendencia,
            })

        data_atual = registros[0].data_brincagem if registros else None
        outras_datas = _listar_outras_datas_livres(db, int(id_propriedade), ids)
        nome_propriedade = gta.propriedade.nome if gta.propriedade else ''

        # Valores do GTA lidos aqui, dentro da sessao do banco.
        gta_dados = {
            'id': gta.id,
            'numero_gta_completo': gta.numero_gta_completo,
            'qtde_animais': gta.qtde_animais,
        }
        data_entrega = gta.data_entrega

    return render_template(
        'produtor/vincular_gta_conferencia.html',
        gta=gta_dados,
        categorias=categorias_js,
        animais=animais_js,
        total_selecionados=len(animais_js),
        qtde_pendencias=sum(1 for a in animais_js if a['pendencia']),
        nome_propriedade=nome_propriedade,
        data_brincagem_br=(data_atual.strftime('%d/%m/%Y') if data_atual else '-'),
        data_brincagem_iso=(data_atual.isoformat() if data_atual else ''),
        data_entrega_br=(data_entrega.strftime('%d/%m/%Y') if data_entrega else ''),
        data_entrega_iso=(data_entrega.isoformat() if data_entrega else ''),
        outras_datas=outras_datas,
        idades_disponiveis=idades_disponiveis,
        id_propriedade=id_propriedade,
        url_voltar=f'/produtor/vincular-gta/selecionar-gta?id_propriedade={id_propriedade}',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota (v1.5.0): POST /produtor/vincular-gta/juntar-datas — AJAX
# da janelinha "Juntar Datas". JSON: {id_gta, datas: [iso...],
# nova_data: 'dd/mm/aaaa'}. Troca SO a Data de Brincagem da
# selecao atual + livres das datas marcadas + livres da propria
# Nova Data, e soma os novos ids a selecao da sessao. Sem Log,
# grava na hora (decisoes de Benedito, Sessao 078).
# -------------------------------------------------------
@vincular_gta.route('/produtor/vincular-gta/juntar-datas', methods=['POST'])
def juntar_datas():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):   # Etapa 4 (2a passada) - #73
        return jsonify({'erro': 'Dados da tela incorretos. Atualize a página e tente novamente. Se continuar, avise a Consiste (usuário, GTA, data e hora).'}), 400
    id_gta = str(dados.get('id_gta') or '')
    datas_iso = dados.get('datas') or []
    if not isinstance(datas_iso, list):
        return jsonify({'erro': 'Uma ou mais datas marcadas estão incorretas. Atualize a página e tente novamente.'}), 400
    nova_data_str = (dados.get('nova_data') or '').strip()

    ids = session.get('vincular_gta_ids')
    id_propriedade = session.get('vincular_gta_id_propriedade')

    if not id_gta.isdecimal() or not ids or not id_propriedade:
        return jsonify({'erro': 'Sessão de vínculo expirada. Reinicie pelo Hub de Entrada.'}), 400

    # v1.11.0 - trava da fazenda em uso.
    if not _propriedade_permitida(id_propriedade):
        return jsonify({'erro': 'A fazenda em uso mudou. Reinicie pelo Hub de Entrada.'}), 403

    try:
        nova_data = datetime.strptime(nova_data_str, '%d/%m/%Y').date()
    except ValueError:
        return jsonify({'erro': 'Nova Data incorreta! Use o formato dd/mm/aaaa.'}), 400

    limite_futuro = date.today() + timedelta(days=DIAS_MAX_BRINCAGEM_FUTURA)
    if nova_data > limite_futuro:
        return jsonify({'erro': f'A Nova Data ({nova_data.strftime("%d/%m/%Y")}) está longe demais no futuro. O máximo aceito é {limite_futuro.strftime("%d/%m/%Y")} (até {DIAS_MAX_BRINCAGEM_FUTURA} dias a partir de hoje). Confira o ano e o mês digitados.'}), 400

    try:
        datas_marcadas = {date.fromisoformat(d) for d in datas_iso}
    except (ValueError, TypeError):
        return jsonify({'erro': 'Uma ou mais datas marcadas estão incorretas. Atualize a página e tente novamente.'}), 400

    with get_db_produtor(session['id_produtor']) as db:
        # Etapa 4 (2a passada) - mesma trava de linha do salvar() (GTA, depois animais por SISBOV): Juntar e Salvar nao se atropelam.
        gta = db.query(Gta).filter(Gta.id == int(id_gta)).with_for_update().first()
        if not gta or gta.tipo_movimento != 'COMPRA' or gta.status_brincagem != 'PENDENTE':
            return jsonify({'erro': 'Esta GTA não está mais pendente de Brincagem.'}), 409

        if gta.data_entrega and nova_data < gta.data_entrega:
            return jsonify({
                'erro': (
                    f'A Nova Data ({nova_data.strftime("%d/%m/%Y")}) não pode ser anterior à '
                    f'Entrega da GTA ({gta.data_entrega.strftime("%d/%m/%Y")}).'
                )
            }), 400

        registros_atuais = db.query(Brincagem).filter(Brincagem.id.in_(ids)).order_by(Brincagem.sisbov).with_for_update().all()
        if len(registros_atuais) != len(ids):
            return jsonify({'erro': 'Um ou mais registros não foram encontrados. Reinicie pelo Hub de Entrada.'}), 400

        for r in registros_atuais:
            if not _livre_para_vincular(r, id_gta):
                return jsonify({'erro': f'O brinco {r.sisbov} já saiu do estado "recém-lido" (ou está reservado a outra GTA no brete) e não pode ser alterado.'}), 409

        datas_alvo = datas_marcadas | {nova_data}
        candidatos = (
            db.query(Brincagem)
            .filter_by(id_propriedade=int(id_propriedade))
            .filter(Brincagem.data_brincagem.in_(list(datas_alvo)))
            .order_by(Brincagem.sisbov)
            .with_for_update()
            .all()
        )
        ids_ja_na_conferencia = set(ids)
        registros_novos = [
            r for r in candidatos
            if r.id not in ids_ja_na_conferencia and _livre_para_vincular(r, id_gta)
        ]

        nada_muda = (
            not registros_novos
            and all(r.data_brincagem == nova_data for r in registros_atuais)
        )
        if nada_muda:
            return jsonify({
                'erro': 'Nada para juntar: marque ao menos 1 data ou informe uma Nova Data diferente da atual.'
            }), 400

        for r in registros_atuais + registros_novos:
            r.data_brincagem = nova_data

        # v1.5.1 - tudo lido ANTES do commit.
        ids_finais = list(ids) + [r.id for r in registros_novos]
        qtde_adicionados = len(registros_novos)

        db.commit()

    session['vincular_gta_ids'] = ids_finais

    return jsonify({
        'sucesso': True,
        'nova_data': nova_data.strftime('%d/%m/%Y'),
        'total': len(ids_finais),
        'adicionados': qtde_adicionados,
    })


# -------------------------------------------------------
# Rota: POST /produtor/vincular-gta/salvar — grava de verdade.
# JSON (v1.6.0): {id_gta, selecionados: [ids marcados],
# ajustes_meses: [{id, nro_meses}]}. Blocos:
#   1. Sessao, GTA e selecao (subconjunto da sessao, total igual
#      ao da GTA, todos ainda livres).
#   2. Ajustes de Nro Meses em memoria (Nascimento + faixa).
#   3. Pendencias (datas, Entrega, estoque do brinco).
#   4. Categorias exatas.
#   5. Saldo dos lotes de brinco (tb_3007).
#   6. Dados auxiliares + Log de Operacoes.
#   7. Gravacao da cadeia por animal (7017, 3008, 2001, 2017,
#      7002, 5001), baixa por lote (3007) e GTA BRINCADO.
# Qualquer recusa -> _recusar() (rollback) - nada e gravado.
# v1.7.0: Cota Hilton pela regra central (eh_cota_hilton) e Log
# da baixa do lote com qtde_saida.
# -------------------------------------------------------
@vincular_gta.route('/produtor/vincular-gta/salvar', methods=['POST'])
def salvar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):   # Etapa 4 (2a passada) - #73
        return jsonify({'erro': 'Dados da tela incorretos. Atualize a página e tente novamente. Se continuar, avise a Consiste (usuário, GTA, data e hora).'}), 400
    id_gta = str(dados.get('id_gta') or '')
    selecionados_brutos = dados.get('selecionados') or []
    ajustes_meses = dados.get('ajustes_meses') or []
    if not isinstance(selecionados_brutos, list) or not isinstance(ajustes_meses, list):
        return jsonify({'erro': 'Seleção de animais incorreta. Atualize a página e tente novamente.'}), 400

    ids_sessao = session.get('vincular_gta_ids')
    id_propriedade = session.get('vincular_gta_id_propriedade')
    modo = session.get('vincular_gta_modo', 'por_animais')

    if not id_gta.isdecimal() or not ids_sessao or not id_propriedade:
        return jsonify({'erro': 'Sessão de vínculo expirada. Reinicie pelo Hub de Entrada.'}), 400

    # v1.11.0 - trava da fazenda em uso: nada e gravado.
    if not _propriedade_permitida(id_propriedade):
        return jsonify({'erro': 'A fazenda em uso mudou. Reinicie pelo Hub de Entrada.'}), 403

    try:
        selecionados = {int(i) for i in selecionados_brutos}
    except (ValueError, TypeError):
        return jsonify({'erro': 'Seleção de animais incorreta. Atualize a página e tente novamente.'}), 400

    if not selecionados:
        return jsonify({'erro': 'Nenhum animal marcado.'}), 400
    if not selecionados.issubset(set(ids_sessao)):
        return jsonify({'erro': 'Há animal marcado fora desta Conferência. Atualize a página e tente novamente.'}), 400

    with get_db_produtor(session['id_produtor']) as db:

        # ---- 1. GTA e selecao ----
        # v1.13.0 - trava de linha: duplo clique/duas abas esperam e caem na recusa abaixo.
        gta = db.query(Gta).filter(Gta.id == int(id_gta)).with_for_update().first()
        if not gta or gta.tipo_movimento != 'COMPRA' or gta.status_brincagem != 'PENDENTE':
            return _recusar(db, 'Esta GTA não está mais pendente de Brincagem.', 409)
        if gta.id_propriedade != int(id_propriedade):   # Etapa 4 (item 6)
            return _recusar(db, 'Esta GTA não pertence a esta Propriedade. Reinicie pelo Hub de Entrada.', 403)

        if len(selecionados) != gta.qtde_animais:
            return _recusar(db, f'A GTA pede {gta.qtde_animais} animal(is), mas há {len(selecionados)} marcado(s).')

        registros = db.query(Brincagem).filter(Brincagem.id.in_(list(selecionados))).order_by(Brincagem.sisbov).with_for_update().all()
        if len(registros) != len(selecionados):
            return _recusar(db, 'Um ou mais registros não foram encontrados. Reinicie pelo Hub de Entrada.')

        for r in registros:
            if r.id_propriedade != int(id_propriedade):
                return _recusar(db, f'O brinco {r.sisbov} não pertence a esta Propriedade.')
            if not _livre_para_vincular(r, gta.id):
                return _recusar(db, f'O brinco {r.sisbov} já saiu do estado "recém-lido" (ou está reservado a outra GTA no brete) e não pode ser vinculado.', 409)

        # ---- 2. Ajustes de Nro Meses (em memoria) ----
        faixas = db.query(IdadeMeses).all()
        idades_map = {i.id: i for i in faixas}
        registros_por_id = {r.id: r for r in registros}
        mudancas_idade = {}   # id -> (dados_antes, dados_depois)

        for ajuste in ajustes_meses:
            try:
                id_animal = int(ajuste.get('id'))
                nro_meses = int(str(ajuste.get('nro_meses')).strip())
            except (ValueError, TypeError, AttributeError):
                return _recusar(db, 'Número de Meses incorreto em um dos animais.')

            registro = registros_por_id.get(id_animal)
            if registro is None:
                continue   # ajuste de animal nao marcado - ignorado
            if not (0 <= nro_meses <= NRO_MESES_MAXIMO):
                return _recusar(db, f'Número de Meses incorreto no brinco {registro.sisbov}.')
            if not registro.data_brincagem:
                return _recusar(db, f'O brinco {registro.sisbov} está sem Data de Brincagem — nada foi gravado.')

            id_faixa = _localizar_faixa(faixas, nro_meses)
            if id_faixa is None:
                return _recusar(db, f'Número de Meses do brinco {registro.sisbov} fora das faixas de idade.')

            novo_nascimento = registro.data_brincagem - timedelta(days=nro_meses * DIAS_POR_MES)
            if novo_nascimento != registro.nascimento or id_faixa != registro.id_idade_meses:
                mudancas_idade[registro.id] = (
                    {'nascimento': str(registro.nascimento), 'id_idade_meses': str(registro.id_idade_meses)},
                    {'nascimento': str(novo_nascimento), 'id_idade_meses': str(id_faixa), 'nro_meses': str(nro_meses)},
                )
                registro.nascimento = novo_nascimento
                registro.id_idade_meses = id_faixa

        # ---- 3. Pendencias (datas, Entrega, estoque) ----
        brincos_por_registro = {}
        brincos_ja_usados = set()
        for r in registros:
            pendencia, brinco = _pendencia_animal(db, r, gta, id_propriedade)
            if pendencia:
                return _recusar(db, f'Brinco {r.sisbov}: {pendencia}. Nada foi gravado.')
            if brinco.id in brincos_ja_usados:
                return _recusar(db, f'Brinco {r.sisbov} repetido na seleção. Nada foi gravado.')
            brincos_ja_usados.add(brinco.id)
            brincos_por_registro[r.id] = brinco

        # ---- 4. Categorias exatas ----
        categorias, animais, _ = _montar_categorias(db, gta, registros)
        for cat in categorias:
            if cat['brincados'] != cat['necessario']:
                return _recusar(db, (
                    f'A categoria {cat["especie"]} {cat["sexo"]} {cat["idade_meses"]} precisa de '
                    f'{cat["necessario"]} animal(is), mas há {cat["brincados"]} marcado(s).'
                ))
        chaves_gta = {cat['chave'] for cat in categorias}
        for a in animais:
            if a['chave'] not in chaves_gta:
                return _recusar(db, f'O brinco {a["sisbov"]} está numa categoria que não existe nesta GTA.')

        # ---- 5. Saldo dos lotes de brinco (A5) ----
        consumo_por_lote = {}
        for brinco in brincos_por_registro.values():
            consumo_por_lote[brinco.id_lote_entrada] = consumo_por_lote.get(brinco.id_lote_entrada, 0) + 1
        lotes = {}
        for id_lote, quantidade in consumo_por_lote.items():
            lote = db.get(BrincoEntrada, id_lote)
            if lote is None or (lote.saldo or 0) < quantidade:
                return _recusar(db, (
                    f'Saldo insuficiente no lote de brincos {id_lote}: precisa de {quantidade}, '
                    f'tem {lote.saldo if lote else 0}. Nada foi gravado. Avise a Consiste.'
                ))
            lotes[id_lote] = lote

        # ---- 6. Dados auxiliares + Log ----
        parceiro_propriedade = gta.parceiro_propriedade
        parceiro = parceiro_propriedade.parceiro if parceiro_propriedade else None
        id_origem = parceiro.id if parceiro else None
        origem_propriedade = parceiro_propriedade.estabelecimento if parceiro_propriedade else None
        origem_cpf_cnpj = parceiro.cpf_cnpj if parceiro else None

        propriedade_destino_obj = gta.propriedade
        produtor_destino = db.get(Produtor, session['id_produtor'])
        destino_propriedade = propriedade_destino_obj.nome if propriedade_destino_obj else None
        destino_cpf_cnpj = produtor_destino.cpf_cnpj if produtor_destino else None

        numero_gta_para_3008 = gta.numero_gta_completo
        if len(numero_gta_para_3008) > TAMANHO_MAXIMO_GTA_3008:
            return _recusar(db, (
                f'Número da GTA "{numero_gta_para_3008}" excede o limite de '
                f'{TAMANHO_MAXIMO_GTA_3008} caracteres do sistema. Nada foi gravado. Avise a Consiste.'
            ))

        id_operacao = registrar_operacao(
            db,
            id_usuario=session['usuario_id'],
            id_propriedade=int(id_propriedade),
            modulo=NOME_MODULO_LOG,
            descricao=f'Vincular GTA {gta.numero_gta_completo} — {len(registros)} animal(is)',
        )

        # v1.6.0 - ajustes de idade no Log (sem motivo - decisao
        # de Benedito).
        for id_brincagem, (antes, depois) in mudancas_idade.items():
            registrar_item(
                db, id_operacao, tabela='tb_5001_brincagem', id_registro=id_brincagem,
                tipo_mudanca='UPDATE', dados_antes=antes, dados_depois=depois,
            )

        # ---- 7. Gravacao da cadeia, animal por animal ----
        for registro in registros:
            brinco = brincos_por_registro[registro.id]

            data_brincagem = registro.data_brincagem
            nascimento = registro.nascimento
            eras_dias = (data_brincagem - nascimento).days
            manejo = _manejo_do(registro, brinco)   # v1.6.1 / v1.13.0

            # v1.6.0 - idade REAL (nao mais o meio da faixa) - usada
            # na idade da PIA.
            nro_meses_real = _calcular_nro_meses(data_brincagem, nascimento)

            # v1.7.0 - regra central: idade ATE 306 dias na brincagem.
            cota_hilton = eh_cota_hilton(eras_dias)

            raca_obj = db.get(Raca, registro.id_raca)
            codigo_raca = raca_obj.codigo if raca_obj else None

            liberacao_abate = data_brincagem + timedelta(days=DIAS_LIBERACAO_ABATE)

            # ---- 7.1 tb_7017 (UPDATE) ----
            dados_antes_7017 = {
                'status': brinco.status, 'raca': brinco.raca, 'sexo': brinco.sexo,
                'data_brincagem': brinco.data_brincagem, 'nascimento': brinco.nascimento,
                'eras_dias': brinco.eras_dias, 'saida_data': brinco.saida_data, 'saida_gta': brinco.saida_gta,
            }
            brinco.status = 'ENTRADA'
            brinco.raca = codigo_raca
            brinco.sexo = registro.sexo
            brinco.data_brincagem = data_brincagem
            brinco.nascimento = nascimento
            brinco.eras_dias = eras_dias
            brinco.saida_data = data_brincagem
            brinco.saida_gta = numero_gta_para_3008
            brinco.reservado_id_gta = None
            brinco.reservado_ate = None
            db.flush()

            registrar_item(
                db, id_operacao, tabela='tb_7017_entrada_brincos_rfid',
                id_registro=brinco.id, tipo_mudanca='UPDATE',
                dados_antes=dados_antes_7017,
                dados_depois={'status': 'ENTRADA', 'saida_gta': numero_gta_para_3008},
            )

            # ---- 7.2 tb_3008 (CREATE) ----
            brinco_saida = BrincoSaida(
                id_propriedade=int(id_propriedade), id_lote_entrada=brinco.id_lote_entrada,
                sisbov=brinco.sisbov, rfid=brinco.rfid, data_saida=data_brincagem,
                gta=numero_gta_para_3008, origem='COMPRA',
            )
            db.add(brinco_saida)
            db.flush()
            registrar_item(
                db, id_operacao, tabela='tb_3008_brincos_saida',
                id_registro=brinco_saida.id, tipo_mudanca='INSERT',
                dados_antes=None, dados_depois={'sisbov': brinco.sisbov},
            )

            # ---- 7.3 tb_2001 (CREATE) ----
            entrada = Entrada(
                sisbov=registro.sisbov, manejo=manejo, rfid=registro.rfid,
                id_especie=registro.id_especie, sexo=registro.sexo, nascimento=nascimento,
                eras_dias=eras_dias, id_raca=registro.id_raca, id_aptidao=None,
                cota_hilton=cota_hilton, data_brincagem=data_brincagem,
                liberacao_abate=liberacao_abate, tipo_entrada='COMPRA', brincos='INTERNO',
                id_gta_entrada=gta.id, data_inclusao=gta.data_entrega, lote=registro.lote,
                id_origem=id_origem, id_propriedade=int(id_propriedade),
            )
            db.add(entrada)
            db.flush()
            registrar_item(
                db, id_operacao, tabela='tb_2001', id_registro=entrada.id,
                tipo_mudanca='INSERT', dados_antes=None, dados_depois={'sisbov': entrada.sisbov},
            )

            # ---- 7.3a BLOCKCHAIN (v1.12.0) - evento ENTRADA (compra) do animal ----
            registrar_evento_animal(db, entrada, TIPO_ENTRADA, id_usuario=session['usuario_id'], id_operacao=id_operacao)

            # ---- 7.3b tb_4003_pesos (CREATE) - v1.10.0: peso do brete = pesagem
            # de sequencia 1 (so se a leitura tinha peso) ----
            pesagem = registrar_pesagem(
                db, int(id_propriedade), registro.sisbov, registro.rfid, data_brincagem,
                registro.peso, eras_dias, registro.lote, ORIGEM_BRETE_COMPRA, session['usuario_id'],
                id_operacao=id_operacao,
            )
            if pesagem is not None:
                registrar_item(
                    db, id_operacao, tabela='tb_4003_pesos', id_registro=pesagem.id,
                    tipo_mudanca='INSERT', dados_antes=None,
                    dados_depois={'sisbov': pesagem.sisbov, 'sequencia': pesagem.sequencia},
                )

            # ---- 7.4 tb_2017 (CREATE) ----
            movimentacao = Movimentacao(
                # v1.14.0 (Sessao 101) - copia fiel da tb_2001: campos novos da tb_2017
                lote=entrada.lote, data_brincagem=entrada.data_brincagem,
                conferido_brete=entrada.conferido_brete, conferido_em=entrada.conferido_em,
                id_origem=entrada.id_origem, id_gta_entrada=entrada.id_gta_entrada,
                id_animal=entrada.id, id_propriedade=int(id_propriedade), sisbov=registro.sisbov,
                manejo=manejo, rfid=registro.rfid, negociacao='COMPRA', brincos='INTERNO',
                id_especie=registro.id_especie, sexo=registro.sexo, nascimento=nascimento,
                dias=eras_dias, cota_hilton=cota_hilton, id_aptidao=None, id_raca=registro.id_raca,
                tipo_entrada='COMPRA', gta_entrada=gta.numero_gta_completo,
                gta_entrada_emissao=gta.data_emissao, gta_entrada_validade=gta.data_validade,
                gta_entrada_animais=gta.qtde_animais, data_inclusao=gta.data_entrega,
                entrada=gta.data_entrega, origem_propriedade=origem_propriedade,
                origem_cpf_cnpj=origem_cpf_cnpj, destino_propriedade=destino_propriedade,
                destino_cpf_cnpj=destino_cpf_cnpj, data_movimentacao=gta.data_entrega,
                peso_medio=gta.peso_medio_entrada,
            )
            db.add(movimentacao)
            db.flush()
            registrar_item(
                db, id_operacao, tabela='tb_2017_movimentacoes',
                id_registro=movimentacao.id, tipo_mudanca='INSERT',
                dados_antes=None, dados_depois={'sisbov': movimentacao.sisbov},
            )

            # ---- 7.5 tb_7002 PIA (CREATE) - numero_pia com lock ----
            db.execute(text('SELECT pg_advisory_xact_lock(:id_propriedade)'), {'id_propriedade': int(id_propriedade)})
            maximo_atual = (
                db.query(Pia.numero_pia).filter(Pia.id_propriedade == int(id_propriedade))
                .order_by(Pia.numero_pia.desc()).limit(1).scalar()
            )
            numero_pia = (maximo_atual or 0) + 1

            pia = Pia(
                id_propriedade=int(id_propriedade), numero_pia=numero_pia, id_gta=gta.id,
                sisbov=registro.sisbov, manejo=manejo, nascimento=nascimento,
                idade_meses=nro_meses_real, sexo=registro.sexo, raca_codigo=codigo_raca,
                motivo='ENTRADA', data_identificacao=data_brincagem,
            )
            db.add(pia)
            db.flush()
            registrar_item(
                db, id_operacao, tabela='tb_7002_pia', id_registro=pia.id,
                tipo_mudanca='INSERT', dados_antes=None,
                dados_depois={'numero_pia': numero_pia, 'sisbov': pia.sisbov},
            )

            # ---- 7.6 tb_5001 (UPDATE) - fecha o ciclo da Brincagem ----
            antes_5001 = {'id_gta': None, 'sts': str(registro.sts)}
            depois_5001 = {'id_gta': str(gta.id), 'sts': 'True'}
            completa_manejo = not registro.manejo
            if completa_manejo:   # v1.13.0 - o Desfazer tambem devolve o manejo vazio
                antes_5001['manejo'] = None
                depois_5001['manejo'] = manejo
            registrar_item(
                db, id_operacao, tabela='tb_5001_brincagem', id_registro=registro.id,
                tipo_mudanca='UPDATE', dados_antes=antes_5001, dados_depois=depois_5001,
            )
            registro.id_gta = gta.id
            registro.sts = True
            registro.id_gta_reservada = None   # v1.16.0 - reserva do brete encerrada
            if completa_manejo:
                registro.manejo = manejo   # v1.6.1 - completa a brincagem

        # ---- 7.7 tb_3007 (UPDATE, por lote - saldo ja conferido no bloco 5) ----
        # v1.7.0 - Log registra tambem a qtde_saida (igual a Sequencial).
        for id_lote, quantidade_consumida in consumo_por_lote.items():
            lote = lotes[id_lote]
            saldo_antes = lote.saldo
            qtde_saida_antes = lote.qtde_saida or 0
            lote.saldo = saldo_antes - quantidade_consumida
            lote.qtde_saida = qtde_saida_antes + quantidade_consumida
            db.flush()
            registrar_item(
                db, id_operacao, tabela='tb_3007_brincos_entrada',
                id_registro=lote.id, tipo_mudanca='UPDATE',
                dados_antes={'saldo': saldo_antes, 'qtde_saida': qtde_saida_antes},
                dados_depois={'saldo': lote.saldo, 'qtde_saida': lote.qtde_saida},
            )

        # ---- 7.8 tb_4001_gta.status_brincagem (UPDATE) ----
        dados_antes_gta = {'status_brincagem': gta.status_brincagem}
        gta.status_brincagem = 'BRINCADO'
        db.flush()
        registrar_item(
            db, id_operacao, tabela='tb_4001_gta', id_registro=gta.id,
            tipo_mudanca='UPDATE',
            dados_antes=dados_antes_gta, dados_depois={'status_brincagem': 'BRINCADO'},
        )

        # v1.5.1 - tudo o que a resposta usa e lido ANTES do commit.
        numero_gta_confirmada = gta.numero_gta_completo
        qtde_vinculada = len(registros)

        db.commit()

    # v1.6.0 (A2) - so a selecao de animais sai da sessao; a
    # Propriedade e o modo ficam (proxima GTA no mesmo fluxo).
    session.pop('vincular_gta_ids', None)

    if modo == 'por_gta':
        destino = f'/produtor/vincular-gta/selecionar-gta?id_propriedade={id_propriedade}'
    else:
        destino = f'/produtor/brincagem-consulta?id_propriedade={id_propriedade}'

    return jsonify({
        'sucesso': True,
        'numero_gta': numero_gta_confirmada,
        'qtde': qtde_vinculada,
        'destino': destino,
    })

# -------------------------------------------------------
# v1.15.0 (Sessao 106) - VINCULO AUTOMATICO da Brincagem com Leitor (caso 1: GTA de Compra PENDENTE escolhida na
# selecao; o brete le os brincos ja reservados a ela). E o MESMO vinculo do salvar() acima (animal, pesagem, PIA,
# movimentacao, estoque de brincos, GTA BRINCADO), copiado para uma funcao que nao depende de tela/sessao, para o
# salvar() e a Brincagem Sequencial ficarem como estavam. NAO faz commit: quem chama decide. Qualquer problema vira
# ValueError(mensagem) e quem chama desfaz. Sem ajuste de meses (a idade ja vem da leitura do brete).
# -------------------------------------------------------
def vincular_automatico(db, gta, registros, id_propriedade, id_produtor, id_usuario):
    if not gta or gta.tipo_movimento != 'COMPRA' or gta.status_brincagem != 'PENDENTE':
        raise ValueError('Esta GTA não está mais pendente de Brincagem.')
    if len(registros) != gta.qtde_animais:
        raise ValueError(f'A GTA pede {gta.qtde_animais} animal(is), mas há {len(registros)} lido(s).')
    for r in registros:
        if r.id_propriedade != int(id_propriedade):
            raise ValueError(f'O brinco {r.sisbov} não pertence a esta Propriedade.')
        if not _livre_para_vincular(r, gta.id):
            raise ValueError(f'O brinco {r.sisbov} já saiu do estado "recém-lido" e não pode ser vinculado.')

    faixas = db.query(IdadeMeses).all()
    idades_map = {i.id: i for i in faixas}
    registros_por_id = {r.id: r for r in registros}
    mudancas_idade = {}   # id -> (dados_antes, dados_depois)

    brincos_por_registro = {}
    brincos_ja_usados = set()
    for r in registros:
        pendencia, brinco = _pendencia_animal(db, r, gta, id_propriedade)
        if pendencia:
            raise ValueError(f'Brinco {r.sisbov}: {pendencia}. Nada foi gravado.')
        if brinco.id in brincos_ja_usados:
            raise ValueError(f'Brinco {r.sisbov} repetido na seleção. Nada foi gravado.')
        brincos_ja_usados.add(brinco.id)
        brincos_por_registro[r.id] = brinco

    # ---- 4. Categorias exatas ----
    categorias, animais, _ = _montar_categorias(db, gta, registros)
    for cat in categorias:
        if cat['brincados'] != cat['necessario']:
            raise ValueError((
                f'A categoria {cat["especie"]} {cat["sexo"]} {cat["idade_meses"]} precisa de '
                f'{cat["necessario"]} animal(is), mas há {cat["brincados"]} marcado(s).'
            ))
    chaves_gta = {cat['chave'] for cat in categorias}
    for a in animais:
        if a['chave'] not in chaves_gta:
            raise ValueError(f'O brinco {a["sisbov"]} está numa categoria que não existe nesta GTA.')

    # ---- 5. Saldo dos lotes de brinco (A5) ----
    consumo_por_lote = {}
    for brinco in brincos_por_registro.values():
        consumo_por_lote[brinco.id_lote_entrada] = consumo_por_lote.get(brinco.id_lote_entrada, 0) + 1
    lotes = {}
    for id_lote, quantidade in consumo_por_lote.items():
        lote = db.get(BrincoEntrada, id_lote)
        if lote is None or (lote.saldo or 0) < quantidade:
            raise ValueError((
                f'Saldo insuficiente no lote de brincos {id_lote}: precisa de {quantidade}, '
                f'tem {lote.saldo if lote else 0}. Nada foi gravado. Avise a Consiste.'
            ))
        lotes[id_lote] = lote

    # ---- 6. Dados auxiliares + Log ----
    parceiro_propriedade = gta.parceiro_propriedade
    parceiro = parceiro_propriedade.parceiro if parceiro_propriedade else None
    id_origem = parceiro.id if parceiro else None
    origem_propriedade = parceiro_propriedade.estabelecimento if parceiro_propriedade else None
    origem_cpf_cnpj = parceiro.cpf_cnpj if parceiro else None

    propriedade_destino_obj = gta.propriedade
    produtor_destino = db.get(Produtor, id_produtor)
    destino_propriedade = propriedade_destino_obj.nome if propriedade_destino_obj else None
    destino_cpf_cnpj = produtor_destino.cpf_cnpj if produtor_destino else None

    numero_gta_para_3008 = gta.numero_gta_completo
    if len(numero_gta_para_3008) > TAMANHO_MAXIMO_GTA_3008:
        raise ValueError((
            f'Número da GTA "{numero_gta_para_3008}" excede o limite de '
            f'{TAMANHO_MAXIMO_GTA_3008} caracteres do sistema. Nada foi gravado. Avise a Consiste.'
        ))

    id_operacao = registrar_operacao(
        db,
        id_usuario=id_usuario,
        id_propriedade=int(id_propriedade),
        modulo=NOME_MODULO_LOG,
        descricao=f'Vincular GTA {gta.numero_gta_completo} — {len(registros)} animal(is)',
    )

    # v1.6.0 - ajustes de idade no Log (sem motivo - decisao
    # de Benedito).
    for id_brincagem, (antes, depois) in mudancas_idade.items():
        registrar_item(
            db, id_operacao, tabela='tb_5001_brincagem', id_registro=id_brincagem,
            tipo_mudanca='UPDATE', dados_antes=antes, dados_depois=depois,
        )

    # ---- 7. Gravacao da cadeia, animal por animal ----
    for registro in registros:
        brinco = brincos_por_registro[registro.id]

        data_brincagem = registro.data_brincagem
        nascimento = registro.nascimento
        eras_dias = (data_brincagem - nascimento).days
        manejo = _manejo_do(registro, brinco)   # v1.6.1 / v1.13.0

        # v1.6.0 - idade REAL (nao mais o meio da faixa) - usada
        # na idade da PIA.
        nro_meses_real = _calcular_nro_meses(data_brincagem, nascimento)

        # v1.7.0 - regra central: idade ATE 306 dias na brincagem.
        cota_hilton = eh_cota_hilton(eras_dias)

        raca_obj = db.get(Raca, registro.id_raca)
        codigo_raca = raca_obj.codigo if raca_obj else None

        liberacao_abate = data_brincagem + timedelta(days=DIAS_LIBERACAO_ABATE)

        # ---- 7.1 tb_7017 (UPDATE) ----
        dados_antes_7017 = {
            'status': brinco.status, 'raca': brinco.raca, 'sexo': brinco.sexo,
            'data_brincagem': brinco.data_brincagem, 'nascimento': brinco.nascimento,
            'eras_dias': brinco.eras_dias, 'saida_data': brinco.saida_data, 'saida_gta': brinco.saida_gta,
        }
        brinco.status = 'ENTRADA'
        brinco.raca = codigo_raca
        brinco.sexo = registro.sexo
        brinco.data_brincagem = data_brincagem
        brinco.nascimento = nascimento
        brinco.eras_dias = eras_dias
        brinco.saida_data = data_brincagem
        brinco.saida_gta = numero_gta_para_3008
        brinco.reservado_id_gta = None
        brinco.reservado_ate = None
        db.flush()

        registrar_item(
            db, id_operacao, tabela='tb_7017_entrada_brincos_rfid',
            id_registro=brinco.id, tipo_mudanca='UPDATE',
            dados_antes=dados_antes_7017,
            dados_depois={'status': 'ENTRADA', 'saida_gta': numero_gta_para_3008},
        )

        # ---- 7.2 tb_3008 (CREATE) ----
        brinco_saida = BrincoSaida(
            id_propriedade=int(id_propriedade), id_lote_entrada=brinco.id_lote_entrada,
            sisbov=brinco.sisbov, rfid=brinco.rfid, data_saida=data_brincagem,
            gta=numero_gta_para_3008, origem='COMPRA',
        )
        db.add(brinco_saida)
        db.flush()
        registrar_item(
            db, id_operacao, tabela='tb_3008_brincos_saida',
            id_registro=brinco_saida.id, tipo_mudanca='INSERT',
            dados_antes=None, dados_depois={'sisbov': brinco.sisbov},
        )

        # ---- 7.3 tb_2001 (CREATE) ----
        entrada = Entrada(
            sisbov=registro.sisbov, manejo=manejo, rfid=registro.rfid,
            id_especie=registro.id_especie, sexo=registro.sexo, nascimento=nascimento,
            eras_dias=eras_dias, id_raca=registro.id_raca, id_aptidao=None,
            cota_hilton=cota_hilton, data_brincagem=data_brincagem,
            liberacao_abate=liberacao_abate, tipo_entrada='COMPRA', brincos='INTERNO',
            id_gta_entrada=gta.id, data_inclusao=gta.data_entrega, lote=registro.lote,
            id_origem=id_origem, id_propriedade=int(id_propriedade),
        )
        db.add(entrada)
        db.flush()
        registrar_item(
            db, id_operacao, tabela='tb_2001', id_registro=entrada.id,
            tipo_mudanca='INSERT', dados_antes=None, dados_depois={'sisbov': entrada.sisbov},
        )

        # ---- 7.3a BLOCKCHAIN (v1.12.0) - evento ENTRADA (compra) do animal ----
        registrar_evento_animal(db, entrada, TIPO_ENTRADA, id_usuario=id_usuario, id_operacao=id_operacao)

        # ---- 7.3b tb_4003_pesos (CREATE) - v1.10.0: peso do brete = pesagem
        # de sequencia 1 (so se a leitura tinha peso) ----
        pesagem = registrar_pesagem(
            db, int(id_propriedade), registro.sisbov, registro.rfid, data_brincagem,
            registro.peso, eras_dias, registro.lote, ORIGEM_BRETE_COMPRA, id_usuario,
            id_operacao=id_operacao,
        )
        if pesagem is not None:
            registrar_item(
                db, id_operacao, tabela='tb_4003_pesos', id_registro=pesagem.id,
                tipo_mudanca='INSERT', dados_antes=None,
                dados_depois={'sisbov': pesagem.sisbov, 'sequencia': pesagem.sequencia},
            )

        # ---- 7.4 tb_2017 (CREATE) ----
        movimentacao = Movimentacao(
            # v1.14.0 (Sessao 101) - copia fiel da tb_2001: campos novos da tb_2017
            lote=entrada.lote, data_brincagem=entrada.data_brincagem,
            conferido_brete=entrada.conferido_brete, conferido_em=entrada.conferido_em,
            id_origem=entrada.id_origem, id_gta_entrada=entrada.id_gta_entrada,
            id_animal=entrada.id, id_propriedade=int(id_propriedade), sisbov=registro.sisbov,
            manejo=manejo, rfid=registro.rfid, negociacao='COMPRA', brincos='INTERNO',
            id_especie=registro.id_especie, sexo=registro.sexo, nascimento=nascimento,
            dias=eras_dias, cota_hilton=cota_hilton, id_aptidao=None, id_raca=registro.id_raca,
            tipo_entrada='COMPRA', gta_entrada=gta.numero_gta_completo,
            gta_entrada_emissao=gta.data_emissao, gta_entrada_validade=gta.data_validade,
            gta_entrada_animais=gta.qtde_animais, data_inclusao=gta.data_entrega,
            entrada=gta.data_entrega, origem_propriedade=origem_propriedade,
            origem_cpf_cnpj=origem_cpf_cnpj, destino_propriedade=destino_propriedade,
            destino_cpf_cnpj=destino_cpf_cnpj, data_movimentacao=gta.data_entrega,
            peso_medio=gta.peso_medio_entrada,
        )
        db.add(movimentacao)
        db.flush()
        registrar_item(
            db, id_operacao, tabela='tb_2017_movimentacoes',
            id_registro=movimentacao.id, tipo_mudanca='INSERT',
            dados_antes=None, dados_depois={'sisbov': movimentacao.sisbov},
        )

        # ---- 7.5 tb_7002 PIA (CREATE) - numero_pia com lock ----
        db.execute(text('SELECT pg_advisory_xact_lock(:id_propriedade)'), {'id_propriedade': int(id_propriedade)})
        maximo_atual = (
            db.query(Pia.numero_pia).filter(Pia.id_propriedade == int(id_propriedade))
            .order_by(Pia.numero_pia.desc()).limit(1).scalar()
        )
        numero_pia = (maximo_atual or 0) + 1

        pia = Pia(
            id_propriedade=int(id_propriedade), numero_pia=numero_pia, id_gta=gta.id,
            sisbov=registro.sisbov, manejo=manejo, nascimento=nascimento,
            idade_meses=nro_meses_real, sexo=registro.sexo, raca_codigo=codigo_raca,
            motivo='ENTRADA', data_identificacao=data_brincagem,
        )
        db.add(pia)
        db.flush()
        registrar_item(
            db, id_operacao, tabela='tb_7002_pia', id_registro=pia.id,
            tipo_mudanca='INSERT', dados_antes=None,
            dados_depois={'numero_pia': numero_pia, 'sisbov': pia.sisbov},
        )

        # ---- 7.6 tb_5001 (UPDATE) - fecha o ciclo da Brincagem ----
        antes_5001 = {'id_gta': None, 'sts': str(registro.sts)}
        depois_5001 = {'id_gta': str(gta.id), 'sts': 'True'}
        completa_manejo = not registro.manejo
        if completa_manejo:   # v1.13.0 - o Desfazer tambem devolve o manejo vazio
            antes_5001['manejo'] = None
            depois_5001['manejo'] = manejo
        registrar_item(
            db, id_operacao, tabela='tb_5001_brincagem', id_registro=registro.id,
            tipo_mudanca='UPDATE', dados_antes=antes_5001, dados_depois=depois_5001,
        )
        registro.id_gta = gta.id
        registro.sts = True
        registro.id_gta_reservada = None   # v1.16.0 - reserva do brete encerrada
        if completa_manejo:
            registro.manejo = manejo   # v1.6.1 - completa a brincagem

    # ---- 7.7 tb_3007 (UPDATE, por lote - saldo ja conferido no bloco 5) ----
    # v1.7.0 - Log registra tambem a qtde_saida (igual a Sequencial).
    for id_lote, quantidade_consumida in consumo_por_lote.items():
        lote = lotes[id_lote]
        saldo_antes = lote.saldo
        qtde_saida_antes = lote.qtde_saida or 0
        lote.saldo = saldo_antes - quantidade_consumida
        lote.qtde_saida = qtde_saida_antes + quantidade_consumida
        db.flush()
        registrar_item(
            db, id_operacao, tabela='tb_3007_brincos_entrada',
            id_registro=lote.id, tipo_mudanca='UPDATE',
            dados_antes={'saldo': saldo_antes, 'qtde_saida': qtde_saida_antes},
            dados_depois={'saldo': lote.saldo, 'qtde_saida': lote.qtde_saida},
        )

    # ---- 7.8 tb_4001_gta.status_brincagem (UPDATE) ----
    dados_antes_gta = {'status_brincagem': gta.status_brincagem}
    gta.status_brincagem = 'BRINCADO'
    db.flush()
    registrar_item(
        db, id_operacao, tabela='tb_4001_gta', id_registro=gta.id,
        tipo_mudanca='UPDATE',
        dados_antes=dados_antes_gta, dados_depois={'status_brincagem': 'BRINCADO'},
    )

    # v1.5.1 - tudo o que a resposta usa e lido ANTES do commit.
    numero_gta_confirmada = gta.numero_gta_completo

    return {'numero_gta': numero_gta_confirmada, 'qtde': len(registros)}

# =========================================================
# FIM DE ARQUIVO: backend\routers\vincular_gta.py
# =========================================================
