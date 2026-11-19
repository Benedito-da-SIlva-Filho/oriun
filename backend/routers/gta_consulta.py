# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\gta_consulta.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-08-21 17:08 -03
# ATUALIZADO EM: 2026-11-19 12:30 -03
# VERSAO: 1.25.0
# v1.25.0: Sessao 133 (2026-11-19 12:30 -03) - CARGA (serie CAR) NAO E GTA: sai da lista da Consulta de GTA e detalhe, opcoes, relatorio, editar e salvar-edicao nao abrem por endereco digitado (voltam ao inicio com aviso, Regra #69). Antes a Carga aparecia e dava para editar. REVERSAO: .bak_antes_s133_carga.
# v1.24.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.23.0: Sessao 123 (2026-11-13 18:50 -03) - AUDITORIA ETAPA 6 (Regra #69): relatorio de GTA nao brincada, editar/salvar com GTA brincada ou em leitura e gravacao interrompida pela leitura do brete voltam para as opcoes COM faixa de aviso (antes em silencio; no ultimo caso o usuario perdia a edicao sem saber). REVERSAO: .bak_antes_etapa6b.
# v1.22.0: Sessao 123 (2026-11-13 18:35 -03) - AUDITORIA ETAPA 6 (Regras #69 e #73): detalhe, opcoes, relatorio, editar e salvar-edicao nao voltam mais em silencio quando a GTA nao existe ou nao e da Propriedade: a lista mostra faixa com o que fazer e o que informar a Consiste; lista() confere o tipo do id_propriedade (antes um valor adulterado dava erro 500). REVERSAO: .bak_antes_etapa6.
# v1.21.0: Sessao 122 (2026-11-12 19:00 -03) - Auditoria Etapa 4 (Entradas): editar GTA trava a Propriedade e confere de novo se ja foi brincada/em leitura. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Tela de consulta de GTAs ja gravadas (Sessao 037/038).
#     Espelha o padrao real do GERAS (telas mostradas por
#     Benedito): Entrada > GTA de Entrada (Conferencia) ->
#     seleciona Propriedade (E Produtor, desde v1.5.0) -> lista
#     de GTAs, ordenada por Data de Emissao decrescente -> clica
#     numa linha para Visualizar o detalhe completo (Procedencia/
#     Destino/Animais).
#
#     Fluxo:
#       1. /produtor/gta-consulta/iniciar - resolve Propriedade E
#          Produtor (v1.5.0: usa
#          auth.buscar_pares_propriedade_produtor(); antes so
#          resolvia Propriedade, assumindo o Produtor da sessao).
#       2. /produtor/gta-consulta/lista?id_propriedade=<id> -
#          lista as GTAs de Entrada daquela Propriedade,
#          ordenadas por data_emissao desc, com o nome da
#          Procedencia resolvido via ParceiroPropriedades/
#          Parceiro. Padrao "Lista Clicavel" do Orion.
#       3. /produtor/gta-consulta/detalhe/<id_gta> - mostra a
#          GTA completa (Procedencia/Destino/Animais), somente
#          leitura. Reaproveita _buscar_dados_exibicao() de
#          gta_manual.py (mesma logica de montar os blocos de
#          conferencia), para nao duplicar a consulta.
#       4. /produtor/gta-consulta/relatorio/<id_gta> - "Relatorio
#          por GTA" (equivalente ao botao Imprimir/Consulta GTA do
#          GERAS), so disponivel para GTAs com
#          status_brincagem='BRINCADO' (dados individuais reais de
#          tb_2001, com SISBOV ja gravado - antes da Brincagem so
#          existe a distribuicao PLANEJADA por categoria em
#          tb_4001_gta_animais, sem SISBOV individual). Gerado via
#          ReportLab puro, ver changelog abaixo.
#
#     ESCOPO DESTA VERSAO: GTAs de sentido ENTRADA (unico tipo
#     gravado no projeto ate agora). Impressao/PDF do proprio
#     documento de Entrada (o "e-GTA" em si) NAO faz parte desta
#     entrega - so o Relatorio por GTA (item 4 acima).
#
#     NOTIFICACAO DE NASCIMENTO (v1.12.0, Sessao 081): a
#     Notificacao de Nascimento e gravada na propria tb_4001_gta
#     (tipo_movimento='NASCTO-DESMAME', serie 'NAS'), mas NAO e
#     uma GTA - fica FORA da lista desta Consulta. O Alterar ja
#     estava protegido (a Notificacao nasce BRINCADO, e GTA
#     BRINCADO nao pode ser alterada - v1.7.0).
#
#     Seguranca: antes de listar/detalhar/relatorio, confere que a
#     Propriedade informada realmente pertence (vinculo ativo,
#     data_fim IS NULL) ao Produtor logado - protege contra um
#     usuario tentar ver GTAs de outra Propriedade so trocando o
#     id na URL.
#
#     v1.0.0: Criacao do modulo (Sessao 037/038).
#     v1.1.0: Sessao 037/038 (17:28) - CORRECAO DE BUG apontada
#             por Benedito: lista() nao trazia o(s) nome(s) do(s)
#             Produtor(es) vinculado(s) a Propriedade - so o nome
#             da Propriedade. Uma mesma Propriedade pode ter mais
#             de um Produtor vinculado (ex.: familia Jose Jr,
#             variacoes de composicao societaria). Adicionada
#             consulta a PropriedadeProdutor + Produtor (vinculo
#             ativo), concatenando os nomes quando houver mais de
#             um, repassado ao template como produtor_nomes.
#     v1.2.0: Sessao 037/038 (17:35) - Adicionadas as rotas de
#             Alteracao (Benedito: "mesmo com todos os controles
#             eles vao errar"):
#               (1) opcoes() - tela intermediaria entre Lista e
#                   Visualizar/Alterar, mesmo padrao do GERAS
#                   (botoes separados "Alterar" e "GTA de
#                   Entrada");
#               (2) editar() - formulario de edicao pre-
#                   preenchido, mesmas validacoes de
#                   gta_manual.salvar() (datas, Meio de
#                   Transporte, soma de Animais);
#               (3) salvar_edicao() - grava as alteracoes e cria
#                   um log DETALHADO em tb_log_alteracao_gta (1
#                   linha por campo do documento alterado + 1
#                   linha por categoria de Animal adicionada/
#                   removida/com quantidade alterada) - decisao
#                   de Benedito de log detalhado, nao resumido.
#                   Animais: a estrategia de gravacao e apagar
#                   todas as linhas antigas de GtaAnimal e
#                   recriar com os valores novos (mais simples e
#                   confiavel que tentar UPDATE linha a linha);
#                   o diff para o log e calculado ANTES dessa
#                   substituicao, comparando os dicts antigo/novo
#                   por chave (especie, sexo, idade_meses).
#             BUG REAL corrigido de passagem: Produtor nao estava
#             importado em backend.models nesta rota (usado em
#             lista() desde a v1.1.0, mas faltava no import) -
#             corrigido no topo do arquivo.
#     v1.3.0: Sessao 037/038 (19:32) - CORRECAO REAL identificada
#             em teste com Benedito, usando a Fazenda Olhos
#             D'Agua (vinculada a Maria Angelica E Sebastiao): a
#             v1.1.0 mostrava os nomes de TODOS os Produtores
#             vinculados a Propriedade, sugerindo enganosamente
#             que a lista reunia GTAs dos dois. Na pratica, cada
#             Produtor tem seu PROPRIO schema (tb_4001_gta
#             separada) - a tela so pode mostrar as GTAs do
#             Produtor da SESSAO LOGADA. Corrigido: produtor_nomes
#             agora vem so de session['id_produtor'], nunca da
#             lista de vinculos da Propriedade. Discussao levou a
#             identificar que a visao unificada (todas as GTAs de
#             uma Propriedade, juntando os Produtores vinculados)
#             e a selecao de Produtor no login para usuarios com
#             multiplos vinculos (ja mapeada como P-036, pendente
#             desde sessoes anteriores) ficam registradas como
#             pendencia formal - fora do escopo de hoje, por
#             decisao de Benedito.
#     v1.4.0: Sessao 037/038 (20:05) - CORRECAO DE BUG real: o
#             titulo da tela de Alterar mostrava so o numero
#             sequencial (ex.: "123456"), nao o numero completo da
#             GTA (ex.: "MST123456") - o SimpleNamespace montado em
#             editar() nao trazia o campo numero_gta_completo,
#             mesmo ja tendo o valor disponivel (gta.numero_gta_
#             completo, ja gravado no banco). Corrigido em dois
#             pontos: gta_form (editar(), GET) e gta_tentativa
#             (dentro de _reexibir(), salvar_edicao() apos erro de
#             validacao).
#     v1.5.0: Sessao (26/08/2026, 15:23 -03) - Resolve a P-036
#             registrada como pendencia na v1.3.0: iniciar()
#             deixou de usar _buscar_propriedades_ativas() (so
#             resolvia Propriedade, mostrando as GTAs do Produtor
#             da sessao independente de qual Propriedade fosse
#             clicada) e passa a usar
#             auth.buscar_pares_propriedade_produtor(), que
#             resolve Propriedade E Produtor juntos - cobre o
#             caso real da Fazenda Olho D'Agua (Maria Angelica E
#             Sebastiao). Template
#             gta_consulta_selecionar_propriedade.html foi
#             substituido pelo novo template compartilhado
#             produtor/selecionar_propriedade_produtor.html (o
#             antigo pode ser apagado, mesma troca feita em
#             gta_manual.py v1.4.0). Com 1 unico par disponivel,
#             segue direto - nenhuma mudanca de comportamento
#             nesse caso, mais comum. _buscar_propriedades_ativas()
#             removida deste arquivo (nao usada em mais nenhum
#             outro ponto - lista()/detalhe()/editar()/
#             salvar_edicao() continuam usando
#             _propriedade_pertence_ao_produtor() normalmente,
#             sem mudanca).
#     v1.6.0: Sessao 048 (09/09/2026, 18:17 -03) - BUG REAL
#             encontrado por Benedito em teste: os botoes "Voltar"
#             (topo) e "Voltar à Lista" (cabecalho) da tela de
#             Editar, e o "Voltar à Lista" da tela de Detalhe,
#             usavam javascript:history.back() - funcionava mal
#             depois de um Salvar (o historico do navegador ainda
#             tinha a tela de Editar no meio do caminho, entao
#             "Voltar" de Detalhe caia de novo em Editar, pedindo
#             para salvar de novo algo que ja tinha sido salvo).
#             Corrigido: editar() e _reexibir() (dentro de
#             salvar_edicao()) agora passam id_propriedade=
#             gta.id_propriedade explicitamente ao template, que
#             passa a montar o link direto para
#             /produtor/gta-consulta/lista?id_propriedade=X (mesmo
#             padrao ja usado em gta_consulta_detalhe.html desde a
#             v1.1.0) em vez de history.back(). Nenhuma mudanca de
#             logica de negocio - so os 2 templates (ver
#             changelogs proprios) e este passo extra de variavel.
#     v1.7.0: Sessao 048 (09/09/2026, 18:40 -03) - NOVA regra de
#             negocio fechada com Benedito: GTA com
#             status_brincagem='BRINCADO' (Brincagem Sequencial ja
#             concluida) nao pode mais ser alterada por um
#             Produtor comum - os brincos ja consumidos ficariam
#             sem correspondencia se Quantidade/Categorias
#             mudassem depois. Card "Alterar" de
#             gta_consulta_opcoes.html (v1.2.0) passa a renderizar
#             desabilitado nesse caso - mas isso e so a camada
#             visual; a trava de verdade e no servidor, nos 2
#             pontos abaixo (nunca confiar so na tela):
#               - editar() (GET): bloqueia e redireciona para
#                 /opcoes/<id_gta> se a GTA estiver BRINCADO -
#                 protege contra alguem digitar a URL direto.
#               - salvar_edicao() (POST): mesma checagem, ANTES de
#                 qualquer validacao de campo - protege contra POST
#                 manipulado direto para a rota, pulando a tela.
#             PENDENCIA ANOTADA (nao implementada nesta sessao, por
#             decisao explicita de Benedito): no futuro, a equipe
#             CONSISTE (usuario_perfil='CONSISTE') deve poder
#             alterar mesmo GTAs ja brincadas, para corrigir erros
#             graves de UF/Numero/Serie ja gravados em cascata
#             noutras tabelas. Fica so anotado - sem excecao de
#             perfil implementada aqui.
#     v1.8.0: Sessao 050 (12/09/2026, 13:05 -03) - NOVA rota
#             relatorio() - "Relatorio por GTA" (equivalente ao
#             botao Imprimir/Consulta GTA do GERAS, ver imagens
#             reais mostradas por Benedito). Alinhamento fechado
#             na propria sessao: PDF via xhtml2pdf, so disponivel
#             para GTAs BRINCADAS (dados individuais reais de
#             tb_2001 - SISBOV completo de 15 digitos, sem DV
#             separado; Categoria calculada pela IDADE ATUAL do
#             animal, sem gravar nada novo, comparando o nascimento
#             contra tb_4006_idade_meses; Raca impressa como sigla
#             de 2 letras, igual gravado; Especie resolvida via
#             tb_4002_especie; Aptidao REMOVIDA do relatorio, por
#             decisao de Benedito - sem uso real ainda). Layout
#             segue de perto o padrao GERAS.
#     v1.9.0: Sessao 050 (12/09/2026, 16:10 -03) - "Relatorio por
#             GTA" MIGRADO de xhtml2pdf/Jinja para ReportLab puro
#             (Padrao Reutilizavel Nº2 NOVA VERSAO, ver backend\
#             utils\pdf_reportlab.py) - decisao de Benedito apos
#             uma manha inteira brigando com ajuste de coluna via
#             CSS 2.1 do xhtml2pdf, sem conseguir controle
#             confiavel de largura/alinhamento. ReportLab desenha o
#             PDF em Python com larguras em pontos - sem ambiguidade.
#             Template gta_consulta_relatorio_pdf.html REMOVIDO (nao
#             e mais usado). ESCOPO: so este relatorio migrou - os
#             demais relatorios do sistema continuam em xhtml2pdf.
#     v1.10.0: Sessao 050 (12/09/2026, 19:05 -03) - BUG REAL
#             corrigido em teste ao vivo: cabecalho da tabela de
#             animais quebrava no meio da palavra ("Ín/dice",
#             "Espé/cie", "Nascimen/to") - colunas Indice/Especie/
#             Sexo/Nascimento estreitas demais. Larguras
#             redistribuidas, puxando espaco da coluna "Idade
#             Meses" (que estava com folga de sobra).
#     v1.11.0: Sessao 050 (12/09/2026, 19:30 -03) - pacote de
#             ajustes apos nova rodada de teste visual: (1) blocos
#             Origem/Destino atualizados para a nova API de
#             criar_bloco_dados() v1.2.0 - CPF/CNPJ e Insc. Estadual
#             deixam de ser rotulo+valor em colunas separadas e
#             passam a ser um UNICO texto combinado ("CPF/CNPJ:
#             80257631887"), alinhado a direita, sempre grudado -
#             libera espaco extra para Nome do Produtor/Propriedade;
#             (2) BUG REAL: cabecalho "Índice"/"Espécie"/"Raça"
#             AINDA quebravam mesmo apos a v1.10.0 - larguras
#             recalculadas de novo, com folga extra testada contra
#             o texto real do rotulo; Idade Meses reduzida (cabe ate
#             ~15 caracteres, sem desperdicio de espaço).
#     v1.12.0: Sessao 081 (28/09/2026, 20:45 -03) - Notificacao de
#             Nascimento (tipo_movimento='NASCTO-DESMAME') FORA da
#             lista() - ver DESCRICAO "NOTIFICACAO DE NASCIMENTO".
#             Filtro "diferente de NASCTO-DESMAME" (e nao "igual a
#             COMPRA") de proposito: uma futura Entrada por
#             Transferencia com GTA continua aparecendo sem mexer
#             de novo. Protecao criada ANTES da primeira
#             Notificacao ser gravada. Nenhuma outra mudanca.
#     v1.13.0: Sessao 082 (29/09/2026, 06:55 -03) - ESPECIE PELO
#             CATALOGO (regra de Benedito: banco com codigo "BOV",
#             tela com a palavra "Bovino"). A lista fixa
#             ESPECIES_VALIDAS de gta_manual.py foi removida (ela
#             fazia gravar "BOVINO" por extenso e travava a
#             Brincagem Sequencial). Mudancas:
#               - editar()/salvar_edicao(): dropdown com a lista do
#                 catalogo (carregar_especies()); a especie
#                 recebida e convertida para o codigo
#                 (codigo_da_especie()) e validada contra
#                 codigos_validos().
#               - _animais_para_dict() converte a especie gravada
#                 para o codigo (registro antigo com "BOVINO" nao
#                 aparece como alteracao falsa no log nem some do
#                 dropdown).
#               - detalhe(): manda mapa_especies ao template, que
#                 mostra "Bovino" (gta_consulta_detalhe.html
#                 v1.4.0).
#             Relatorio por GTA nao muda (ja usava o codigo do
#             catalogo pelo id_especie da tb_2001).
#     v1.14.0: Sessao 085 (04/10/2026, 17:50 -03) - GTA DUPLICADA (regra
#             de Benedito: jamais duas GTAs iguais - UF + Serie + Numero
#             + sentido, dentro do mesmo Produtor; ver backend/utils/
#             gta_duplicada.py). salvar_edicao() agora confere ANTES de
#             gravar: se a UF/Serie/Numero digitados ja pertencem a OUTRA
#             GTA do mesmo sentido, avisa e impede (a propria GTA nunca
#             conta contra si mesma). Sem isso, alterar o numero seria a
#             porta dos fundos para criar uma GTA repetida. Se duas
#             pessoas gravarem ao mesmo tempo, a trava do banco
#             (uq_tb_4001_gta_uf_serie_numero_sentido) recusa: o
#             IntegrityError e tratado (rollback) e vira a mesma
#             mensagem. Nenhuma outra mudanca.
#     v1.15.0: Sessao 085 (04/10/2026, 18:20 -03) - SERIE DA GTA POR UF
#             (regra de Benedito: Goias com 2 letras, demais UFs com 1 -
#             regras_sisbov.py v1.4.0). salvar_edicao() valida o tamanho
#             da Serie conforme a UF (antes: sempre 1 letra). Mesma regra
#             do gta_manual.py v1.8.0. gta_consulta_editar.html v1.8.0
#             ajusta o campo na tela. Nenhuma outra mudanca.
#     v1.16.0: Sessao 087 (05/10/2026, 11:05 -03) - LACO NO VOLTAR (Regra de
#             Ouro #4, achado no pente fino de Benedito): com 1 so par
#             Propriedade/Produtor, iniciar() pula a Selecao e redireciona
#             para a Lista, e o Voltar/Trocar Propriedade da Lista voltavam
#             para iniciar() - laco. lista() agora passa varias_propriedades
#             (2+ pares) ao template gta_consulta_lista.html v1.9.0, que
#             ajusta o Voltar e esconde Trocar Propriedade quando e 1 so.
#             Nenhuma outra mudanca.
#     v1.17.0: Sessao 090 (08/10/2026, 08:10 -03) - FAZENDA EM USO (Lote 3):
#             FAZENDA EM USO (Regra de Ouro #13): a tela "Selecionar Propriedade" deixa
#             de aparecer quando ha fazenda em uso (auth.resolver_fazenda_em_uso).
#               - iniciar(): com fazenda em uso, abre a Lista direto nela.
#               - _propriedade_pertence_ao_produtor() ganha a TRAVA: Propriedade
#                 diferente da fazenda em uso (trocada em outra aba) = negado,
#                 e todas as rotas (lista, detalhe, opcoes, relatorio, editar,
#                 salvar-edicao) mandam para o iniciar(), que abre a fazenda
#                 em uso.
#               - lista(): varias_propriedades fica False com fazenda em uso,
#                 entao o Voltar da Lista vai ao card Consultar GTAs (e nao a
#                 iniciar(): laco) e Trocar Propriedade fica escondido.
#             Nenhuma outra mudanca. Template inalterado.
#     v1.18.0: Sessao 091 (08/10/2026, 19:35 -03) - SITUACAO NA LISTA: lista() passa
#             ao template o status_brincagem de cada GTA, para a coluna
#             "Situacao" (Vinculada / Pendente). So leitura; nenhuma regra,
#             gravacao ou outra rota mudou.
#     v1.19.0: Sessao 102 (21/10/2026, 09:20 -03) - UF DUPLICADA: o Municipio da Procedencia no PDF passa a sair "MUNICIPIO / UF"
#             (igual ao Destino), ja que gta_manual.py v1.12.0 devolve o municipio sem a UF. Nenhuma outra mudanca. REVERSAO: devolver .bak_antes_uf_s102.
#     v1.20.0: Sessao 106 (26/10/2026, 15:30 -03) - PONTA SOLTA (auditoria): GTA com leitura RESERVADA no brete (Leitor/Bastao, tb_5001.id_gta_reservada)
#             nao pode ser alterada (mudar categorias/quantidade no meio da leitura quebraria a conferencia): opcoes() avisa 'Em leitura no brete: N de M' e
#             editar()/salvar_edicao() redirecionam para as Opcoes. Nenhuma outra mudanca. REVERSAO: .bak_antes_s106s.
# =========================================================

from datetime import datetime, date, timedelta
from io import BytesIO
from types import SimpleNamespace
from flask import Blueprint, render_template, request, redirect, session, send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from backend.database import engine
from backend.models import Propriedade, PropriedadeProdutor, Produtor
from backend.models.tb_parceiros import Parceiro
from backend.models.tb_parceiros_propriedades import ParceiroPropriedades
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4001_gta_animais import GtaAnimal
from backend.models.tb_4002_especie import Especie
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_5001_brincagem import Brincagem   # v1.20.0 - leituras reservadas
from sqlalchemy import func, text   # v1.20.0
from backend.utils.gravacao_nascimento import TRAVA_BRINCOS_NASC
from backend.models.tb_log_alteracao_gta import LogAlteracaoGta
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.gta_manual import _buscar_dados_exibicao, FAIXAS_IDADE, SEXOS_VALIDOS, MEIOS_TRANSPORTE_VALIDOS, MEIO_TRANSPORTE_COMITIVA, TOLERANCIA_COMITIVA_DIAS
from backend.utils.especies import carregar_especies, codigo_da_especie, codigos_validos, mapa_codigo_descricao
from backend.utils.multitenant import get_db_produtor
from backend.utils.regras_sisbov import tamanho_serie_gta, mensagem_serie_gta
from backend.utils.gta_duplicada import buscar_gta_duplicada, mensagem_gta_duplicada, eh_violacao_unicidade_gta
from backend.utils.pdf_reportlab import (
    PAGE_SIZE, MARGEM_H, MARGEM_V, LARGURA_UTIL,
    estilo_titulo, estilo_subtitulo, estilo_rodape,
    criar_bloco_dados, criar_cabecalho_campos, criar_tabela_padrao, criar_tabela_resumo,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
gta_consulta = Blueprint('gta_consulta', __name__)


# -------------------------------------------------------
# Constante (NOVA, v1.12.0): tipo de movimento que mora na
# tb_4001_gta mas NAO e GTA (Notificacao de Nascimento).
# -------------------------------------------------------
TIPO_MOVIMENTO_NAO_GTA = 'NASCTO-DESMAME'

# v1.25.0 - a CARGA de animais (Produtor novo) tambem mora na tb_4001_gta (serie 'CAR') mas NAO e GTA.
SERIE_CARGA = 'CAR'


def _eh_carga(gta):
    return (gta.serie_gta or '') == SERIE_CARGA


# -------------------------------------------------------
# Funcao auxiliar: confere se a Propriedade informada pertence
# de fato (vinculo ativo) ao Produtor logado. Protege contra
# tentativa de ver GTAs de outra Propriedade trocando o id na
# URL.
# -------------------------------------------------------
def _lidos_reservados_gta(db, id_gta):
    # v1.20.0 - brincos RESERVADOS a esta GTA no brete (Leitor/Bastao), ainda sem vinculo.
    return (
        db.query(func.count(Brincagem.id))
        .filter(
            Brincagem.id_gta_reservada == int(id_gta),
            Brincagem.sts == False,   # noqa: E712
            Brincagem.id_gta.is_(None),
        )
        .scalar()
    ) or 0


def _propriedade_pertence_ao_produtor(id_produtor, id_propriedade):
    with Session(engine) as db:
        vinculo = db.query(PropriedadeProdutor).filter_by(
            id_produtor=id_produtor,
            id_propriedade=id_propriedade,
            data_fim=None
        ).first()
        if vinculo is None:
            return False

    # v1.17.0 - TRAVA DA FAZENDA EM USO: se ha fazenda em uso e a Propriedade
    # pedida e OUTRA (trocada em outra aba), nega. Quem chama manda para o
    # iniciar(), que abre a fazenda em uso.
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and int(par_em_uso.id_propriedade) != int(id_propriedade):
        return False
    return True


# -------------------------------------------------------
# Rota: GET /produtor/gta-consulta/iniciar — ponto de partida.
#
# v1.5.0 (P-036): resolve Propriedade E Produtor juntos, via
# auth.buscar_pares_propriedade_produtor() - cobre o caso real
# da Fazenda Olho D'Agua (Maria Angelica E Sebastiao, mesmo
# usuario administrativo atendendo os dois). Com 1 unico par,
# segue direto - mesmo comportamento de sempre.
# -------------------------------------------------------
# -------------------------------------------------------
# v1.22.0 (Regra #69) - volta ao inicio da Consulta de GTAs COM mensagem que da um norte:
# o que aconteceu, o que fazer e o que informar a Consiste. A lista mostra a faixa e apaga o aviso.
# -------------------------------------------------------
CHAVE_AVISO = 'gta_consulta_aviso'
AVISOS_VOLTAR = {
    'carga': 'A Carga não é uma GTA, por isso ela não aparece nem abre aqui. Para ver os animais da Carga, use o Relatório da Carga (Entrada > Consultas e Correções). Se precisar corrigir algo nela, peça à Consiste.',
    'nao_achada': 'Não encontramos essa GTA nesta Propriedade. Ela pode ter sido excluída ou ser de outra fazenda. Escolha a GTA na lista abaixo. Se o problema continuar, avise a Consiste informando seu usuário, a fazenda, o número da GTA, a data e a hora.',
    'propriedade_invalida': 'Não foi possível abrir a lista dessa Propriedade. Escolha a GTA abaixo ou volte ao Home e abra a Consulta de GTAs de novo. Se o problema continuar, avise a Consiste informando seu usuário, a fazenda, a data e a hora.',
}


CHAVE_AVISO_OPCOES = 'gta_consulta_aviso_opcoes'
AVISOS_OPCOES = {
    'relatorio_nao_brincada': 'O Relatório por GTA só existe depois que os animais desta GTA forem brincados (lidos e conferidos no brete). Faça a Brincagem desta GTA e volte aqui. Se já fez e o relatório não abre, avise a Consiste informando seu usuário, o número da GTA, a data e a hora.',
    'editar_bloqueada': 'Esta GTA já tem animais brincados ou em leitura no brete, por isso os dados dela não podem mais ser alterados por aqui. Se precisar corrigir algo, peça à Consiste informando seu usuário, o número da GTA, o que precisa mudar, a data e a hora.',
    'salvar_bloqueado': 'A leitura dos animais desta GTA começou enquanto você editava, então suas alterações NÃO foram gravadas. Termine ou cancele a leitura no brete. Se ainda precisar alterar a GTA, peça à Consiste informando seu usuário, o número da GTA, o que precisa mudar, a data e a hora.',
}


def _ir_para_opcoes_com_aviso(id_gta, motivo):
    """v1.23.0 (Regra #69) - volta para as opcoes da GTA COM mensagem (antes voltava em silencio)."""
    session[CHAVE_AVISO_OPCOES] = AVISOS_OPCOES[motivo]
    return redirect(f'/produtor/gta-consulta/opcoes/{id_gta}')


def _voltar_ao_inicio_com_aviso(motivo):
    session[CHAVE_AVISO] = AVISOS_VOLTAR[motivo]
    return redirect('/produtor/gta-consulta/iniciar')


@gta_consulta.route('/produtor/gta-consulta/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            titulo="Consulta de GTAs — Selecionar Propriedade",
            proximo='/produtor/gta-consulta/lista',
            campo_propriedade='id_propriedade',
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='entrada',
        )

    # v1.17.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'/produtor/gta-consulta/lista?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'/produtor/gta-consulta/lista?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        titulo="Consulta de GTAs — Selecionar Propriedade",
        proximo='/produtor/gta-consulta/lista',
        campo_propriedade='id_propriedade',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/gta-consulta/lista — lista as GTAs de
# Entrada da Propriedade escolhida, ordenadas por Data de
# Emissao decrescente (padrao GERAS).
# v1.12.0: Notificacoes de Nascimento ficam de fora.
# -------------------------------------------------------
@gta_consulta.route('/produtor/gta-consulta/lista')
def lista():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_produtor = session['id_produtor']
    id_propriedade = request.args.get('id_propriedade', '')

    # v1.22.0 (Regra #73): id_propriedade vindo da URL tem o tipo conferido (nunca erro 500)
    try:
        id_propriedade_int = int(id_propriedade)
    except (TypeError, ValueError):
        id_propriedade_int = 0
    if not id_propriedade_int or not _propriedade_pertence_ao_produtor(id_produtor, id_propriedade_int):
        return _voltar_ao_inicio_com_aviso('propriedade_invalida')

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))

        # v1.3.0 - CORRECAO: mostra APENAS o nome do Produtor da
        # SESSAO LOGADA (session['id_produtor']), nunca todos os
        # Produtores vinculados a Propriedade. Motivo (esclarecido
        # em teste real com Benedito): esta tela consulta a tabela
        # tb_4001_gta dentro do schema do Produtor logado - se a
        # mesma Propriedade fisica tiver mais de um Produtor
        # vinculado (ex.: familia Jose Jr), cada um tem seu PROPRIO
        # schema com suas PROPRIAS GTAs. Mostrar os dois nomes
        # juntos (como a v1.1.0 fazia) sugeria enganosamente que a
        # lista reunia GTAs dos dois - na pratica so mostra as do
        # Produtor logado. v1.5.0: agora session['id_produtor'] ja
        # vem corretamente resolvido pela tela de selecao
        # Propriedade+Produtor (iniciar()), entao este nome sempre
        # bate com o par escolhido.
        produtor_logado = db.get(Produtor, id_produtor)
        produtor_nomes = produtor_logado.nome if produtor_logado else '-'

    gtas_exibicao = []

    with get_db_produtor(id_produtor) as db:
        gtas = (
            db.query(Gta)
            .filter_by(
                id_propriedade=int(id_propriedade),
                sentido='ENTRADA'
            )
            .filter(Gta.tipo_movimento != TIPO_MOVIMENTO_NAO_GTA)   # v1.12.0
            .filter(Gta.serie_gta != SERIE_CARGA)   # v1.25.0 - a Carga (serie CAR) nao e GTA
            .order_by(Gta.data_emissao.desc(), Gta.numero_gta_completo.desc())
            .all()
        )

        for gta in gtas:
            nome_procedencia = '-'
            if gta.id_parceiro_propriedade:
                propriedade_externa = db.get(ParceiroPropriedades, gta.id_parceiro_propriedade)
                if propriedade_externa:
                    parceiro = db.get(Parceiro, propriedade_externa.id_parceiro)
                    if parceiro:
                        nome_procedencia = parceiro.nome

            gtas_exibicao.append({
                'id': gta.id,
                'numero_gta_completo': gta.numero_gta_completo,
                'data_emissao': gta.data_emissao.strftime('%d/%m/%Y') if gta.data_emissao else '-',
                'qtde_animais': gta.qtde_animais,
                'tipo_movimento': gta.tipo_movimento,
                'procedencia_nome': nome_procedencia,
                'status_brincagem': gta.status_brincagem,   # v1.18.0
            })

    # v1.16.0 - so mostra Trocar Propriedade / volta para a Selecao quando
    # existe Selecao de verdade (2+ pares Propriedade/Produtor).
    # v1.17.0 - com fazenda em uso a Selecao nao existe: tambem escondido.
    pares_usuario = buscar_pares_propriedade_produtor(session['usuario_id'])
    varias_propriedades = len(pares_usuario) > 1 and resolver_fazenda_em_uso(pares_usuario) is None

    return render_template(
        'produtor/gta_consulta_lista.html',
        gtas=gtas_exibicao,
        varias_propriedades=varias_propriedades,
        propriedade=propriedade,
        produtor_nomes=produtor_nomes,
        aviso=session.pop(CHAVE_AVISO, None),   # v1.22.0 (Regra #69)
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/gta-consulta/detalhe/<id_gta> — Visualizar
# a GTA completa (somente leitura). Reaproveita
# _buscar_dados_exibicao() de gta_manual.py.
# -------------------------------------------------------
@gta_consulta.route('/produtor/gta-consulta/detalhe/<int:id_gta>')
def detalhe(id_gta):
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_produtor = session['id_produtor']

    with get_db_produtor(id_produtor) as db:
        gta = db.get(Gta, id_gta)

        if not gta:
            return _voltar_ao_inicio_com_aviso('nao_achada')

        # Seguranca: confere que a GTA pertence mesmo a uma
        # Propriedade vinculada ao Produtor logado.
        if not _propriedade_pertence_ao_produtor(id_produtor, gta.id_propriedade):
            return _voltar_ao_inicio_com_aviso('nao_achada')
        if _eh_carga(gta):   # v1.25.0 - a Carga nao e GTA: nao abre, nao edita, nao gera relatorio
            return _voltar_ao_inicio_com_aviso('carga')

        animais = list(gta.animais)

    # _buscar_dados_exibicao() espera o id_parceiro (nao o
    # id_parceiro_propriedade que a Gta guarda) - resolve o
    # Parceiro real primeiro.
    with get_db_produtor(id_produtor) as db:
        propriedade_externa = db.get(ParceiroPropriedades, gta.id_parceiro_propriedade) if gta.id_parceiro_propriedade else None
        id_parceiro_real = propriedade_externa.id_parceiro if propriedade_externa else None

    procedencia, destino = _buscar_dados_exibicao(
        id_produtor, id_parceiro_real, gta.id_parceiro_propriedade, gta.id_propriedade
    )

    return render_template(
        'produtor/gta_consulta_detalhe.html',
        gta=gta,
        animais=animais,
        mapa_especies=mapa_codigo_descricao(),   # v1.13.0 - "BOV" -> "Bovino"
        procedencia=procedencia,
        destino=destino,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/gta-consulta/opcoes/<id_gta> — tela
# intermediaria entre a Lista e o Visualizar/Alterar, mesmo
# padrao do GERAS (coluna CONFERENCIA com botoes separados
# "Alterar" e "GTA de Entrada"). Mostra um resumo rapido da GTA
# + os dois botoes.
# -------------------------------------------------------
@gta_consulta.route('/produtor/gta-consulta/opcoes/<int:id_gta>')
def opcoes(id_gta):
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_produtor = session['id_produtor']

    with get_db_produtor(id_produtor) as db:
        gta = db.get(Gta, id_gta)

        if not gta or not _propriedade_pertence_ao_produtor(id_produtor, gta.id_propriedade):
            return _voltar_ao_inicio_com_aviso('nao_achada')
        if _eh_carga(gta):   # v1.25.0 - a Carga nao e GTA: nao abre, nao edita, nao gera relatorio
            return _voltar_ao_inicio_com_aviso('carga')

        lidos_brete = _lidos_reservados_gta(db, gta.id)   # v1.20.0

    return render_template(
        'produtor/gta_consulta_opcoes.html',
        gta=gta,
        em_leitura=(f'{lidos_brete} de {gta.qtde_animais}' if lidos_brete else ''),   # v1.20.0
        aviso=session.pop(CHAVE_AVISO_OPCOES, None),   # v1.23.0 (Regra #69)
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: GET /produtor/gta-consulta/relatorio/<id_gta> — "Relatorio
# por GTA". Gerado via ReportLab puro (ver backend\utils\
# pdf_reportlab.py) - padrao de PDF do Orion, ver changelog no
# cabecalho. So funciona para GTAs com status_brincagem='BRINCADO' -
# antes disso nao ha SISBOV individual real gravado em tb_2001 (so a
# distribuicao planejada por categoria em tb_4001_gta_animais).
# -------------------------------------------------------
@gta_consulta.route('/produtor/gta-consulta/relatorio/<int:id_gta>')
def relatorio(id_gta):
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_produtor = session['id_produtor']

    with get_db_produtor(id_produtor) as db:
        gta = db.get(Gta, id_gta)

        if not gta or not _propriedade_pertence_ao_produtor(id_produtor, gta.id_propriedade):
            return _voltar_ao_inicio_com_aviso('nao_achada')
        if _eh_carga(gta):   # v1.25.0 - a Carga nao e GTA: nao abre, nao edita, nao gera relatorio
            return _voltar_ao_inicio_com_aviso('carga')

        # Trava de negocio (Benedito, Sessao 050): relatorio so
        # existe para GTAs ja BRINCADAS.
        if gta.status_brincagem != 'BRINCADO':
            return _ir_para_opcoes_com_aviso(id_gta, 'relatorio_nao_brincada')

        entradas = (
            db.query(Entrada)
            .filter_by(id_gta_entrada=id_gta)
            .order_by(Entrada.sisbov.asc())
            .all()
        )

        # Catalogos resolvidos em bloco (1 query cada) - evita
        # N+1 query por animal.
        especies_db  = db.query(Especie).all()
        mapa_especie = {especie.id: especie.codigo for especie in especies_db}

        racas_db  = db.query(Raca).all()
        mapa_raca = {raca.id: raca.codigo for raca in racas_db}

        faixas_idade_db = db.query(IdadeMeses).order_by(IdadeMeses.dias_min.asc()).all()

        propriedade_externa = db.get(ParceiroPropriedades, gta.id_parceiro_propriedade) if gta.id_parceiro_propriedade else None
        id_parceiro_real = propriedade_externa.id_parceiro if propriedade_externa else None

    procedencia, destino = _buscar_dados_exibicao(
        id_produtor, id_parceiro_real, gta.id_parceiro_propriedade, gta.id_propriedade
    )

    # ---------------------------------------------------
    # Monta a linha de cada animal + resumo por Sexo x Faixa
    # Etaria ("Idade Meses"). Calculada pela IDADE ATUAL (hoje -
    # nascimento) - decisao de Benedito: a categoria nao muda com
    # a data da Brincagem, entao nao precisa gravar nada novo.
    # ---------------------------------------------------
    hoje = date.today()
    linhas_tabela = []
    resumo_contagem = {}  # {descricao_faixa: {'FEMEA': n, 'MACHO': n}}

    for indice, entrada in enumerate(entradas, start=1):
        idade_dias = (hoje - entrada.nascimento).days if entrada.nascimento else None

        faixa_descricao = '-'
        for faixa in faixas_idade_db:
            if idade_dias is not None and faixa.dias_min <= idade_dias <= faixa.dias_max:
                faixa_descricao = faixa.descricao
                break

        linhas_tabela.append([
            indice,
            entrada.sisbov,
            entrada.manejo or '-',
            mapa_especie.get(entrada.id_especie, '-'),
            entrada.sexo,
            entrada.nascimento.strftime('%d/%m/%Y') if entrada.nascimento else '-',
            faixa_descricao,
            mapa_raca.get(entrada.id_raca, '-'),
        ])

        resumo_contagem.setdefault(faixa_descricao, {'FEMEA': 0, 'MACHO': 0})
        if entrada.sexo in ('FEMEA', 'MACHO'):
            resumo_contagem[faixa_descricao][entrada.sexo] += 1

    # Colunas do resumo na ordem oficial das faixas (dias_min ASC),
    # igual ao padrao GERAS (Sexo nas linhas, Faixa nas colunas).
    colunas_faixas = [faixa.descricao for faixa in faixas_idade_db]
    resumo_femeas  = [resumo_contagem.get(descricao, {}).get('FEMEA', 0) for descricao in colunas_faixas]
    resumo_machos  = [resumo_contagem.get(descricao, {}).get('MACHO', 0) for descricao in colunas_faixas]
    total_femeas   = sum(resumo_femeas)
    total_machos   = sum(resumo_machos)

    # ---------------------------------------------------
    # Monta o PDF via ReportLab puro (padrao Sessao 050 - ver
    # backend/utils/pdf_reportlab.py).
    # ---------------------------------------------------
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=PAGE_SIZE,
        leftMargin=MARGEM_H, rightMargin=MARGEM_H,
        topMargin=MARGEM_V, bottomMargin=MARGEM_V,
    )

    story = [
        Paragraph('RELATÓRIO POR GTA — ENTRADA DE ANIMAIS', estilo_titulo),
        Paragraph(gta.tipo_movimento, estilo_subtitulo),
    ]

    # v1.11.0: nova API de criar_bloco_dados() - linhas de 3
    # elementos (rotulo, valor, texto_direita), CPF/CNPJ e Insc.
    # Estadual combinados num unico texto (rotulo+valor grudados,
    # alinhado a direita) em vez de colunas separadas.
    story += criar_bloco_dados('DADOS DA ORIGEM DOS ANIMAIS', [
        ('Produtor:', procedencia.nome if procedencia else '-',
         f'CPF/CNPJ: {procedencia.cpf_cnpj}' if procedencia and procedencia.cpf_cnpj else 'CPF/CNPJ: -'),
        ('Propriedade:', procedencia.estabelecimento if procedencia else '-',
         f'Insc. Estadual: {procedencia.insc_estadual}' if procedencia and procedencia.insc_estadual else 'Insc. Estadual: -'),
        ('Município:', (f'{procedencia.municipio_nome} / {procedencia.uf}' if procedencia.uf else procedencia.municipio_nome) if procedencia and procedencia.municipio_nome else '-', None),   # v1.19.0
    ])

    story += criar_bloco_dados('DADOS DO DESTINO DOS ANIMAIS', [
        ('Produtor:', destino.produtor_nome if destino else '-',
         f'CPF/CNPJ: {destino.cpf_cnpj}' if destino and destino.cpf_cnpj else 'CPF/CNPJ: -'),
        ('Propriedade:', destino.nome if destino else '-',
         f'Insc. Estadual: {destino.insc_estadual}' if destino and destino.insc_estadual else 'Insc. Estadual: -'),
        ('Município:', f'{destino.municipio_nome} / {destino.uf}' if destino and destino.municipio_nome else '-', None),
    ])

    story.append(criar_cabecalho_campos([
        ('Código GTA', gta.numero_gta_completo),
        ('Validade', gta.data_validade.strftime('%d/%m/%Y') if gta.data_validade else '-'),
        ('Emissão', gta.data_emissao.strftime('%d/%m/%Y') if gta.data_emissao else '-'),
        ('Entrada', gta.data_entrega.strftime('%d/%m/%Y') if gta.data_entrega else '-'),
        ('Qtde', str(gta.qtde_animais)),
    ]))
    story.append(Spacer(1, 10))

    # v1.11.0: Indice/Especie/Raça alargados (cabecalho nao quebra
    # mais); Idade Meses reduzida (cabe ate ~15 caracteres, sem
    # desperdicio de espaço).
    larguras_animais = [
        w * LARGURA_UTIL for w in (0.07, 0.22, 0.12, 0.09, 0.09, 0.13, 0.18, 0.10)
    ]
    story.append(criar_tabela_padrao(
        cabecalhos=['Índice', 'Código SISBOV', 'Manejo', 'Espécie', 'Sexo', 'Nascimento', 'Idade Meses', 'Raça'],
        linhas=linhas_tabela,
        larguras=larguras_animais,
        alinhamentos=['CENTER', 'LEFT', 'LEFT', 'CENTER', 'CENTER', 'CENTER', 'LEFT', 'CENTER'],
        colunas_destaque=[1, 2],  # SISBOV e Manejo - fonte maior
    ))
    story.append(Spacer(1, 10))

    story.append(criar_tabela_resumo(colunas_faixas, resumo_femeas, resumo_machos, total_femeas, total_machos))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f'Total Geral: {total_femeas + total_machos} animais &#8212; '
        f'Impressão: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}',
        estilo_rodape,
    ))

    doc.build(story)
    buffer.seek(0)

    nome_arquivo = f'Relatorio_GTA_{gta.numero_gta_completo}.pdf'
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)


# -------------------------------------------------------
# Funcao auxiliar: monta a lista de categorias de Animais de uma
# GTA como dicts simples {especie, sexo, idade_meses, quantidade},
# na mesma forma usada tanto para exibir no formulario de edicao
# quanto para comparar (diff) antes/depois ao salvar.
# -------------------------------------------------------
def _animais_para_dict(animais, especies=None):
    # v1.13.0: especie sempre no CODIGO do catalogo ("BOVINO" -> "BOV").
    return [
        {
            'especie': codigo_da_especie(a.especie, especies) or a.especie,
            'sexo': a.sexo,
            'idade_meses': a.idade_meses,
            'quantidade': a.quantidade,
        }
        for a in animais
    ]


# -------------------------------------------------------
# Rota: GET /produtor/gta-consulta/editar/<id_gta> — formulario
# de Alteracao, pre-preenchido com os dados atuais da GTA.
# Reaproveita o mesmo layout/validacao do formulario de
# lancamento (gta_manual_cadastro.html), mas via template
# proprio (gta_consulta_editar.html) que aponta o POST para
# salvar_edicao().
# -------------------------------------------------------
@gta_consulta.route('/produtor/gta-consulta/editar/<int:id_gta>')
def editar(id_gta):
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_produtor = session['id_produtor']

    with get_db_produtor(id_produtor) as db:
        gta = db.get(Gta, id_gta)

        if not gta or not _propriedade_pertence_ao_produtor(id_produtor, gta.id_propriedade):
            return _voltar_ao_inicio_com_aviso('nao_achada')
        if _eh_carga(gta):   # v1.25.0 - a Carga nao e GTA: nao abre, nao edita, nao gera relatorio
            return _voltar_ao_inicio_com_aviso('carga')

        # NOVO v1.7.0: GTA ja brincada nao pode ser alterada por um
        # Produtor comum - protege contra URL digitada direto.
        if gta.status_brincagem == 'BRINCADO' or _lidos_reservados_gta(db, gta.id):   # v1.20.0 - ou em leitura no brete
            return _ir_para_opcoes_com_aviso(id_gta, 'editar_bloqueada')

        especies = carregar_especies()   # v1.13.0
        animais = _animais_para_dict(list(gta.animais), especies)
        id_propriedade = gta.id_propriedade  # NOVO v1.6.0 - ver changelog

        propriedade_externa = db.get(ParceiroPropriedades, gta.id_parceiro_propriedade) if gta.id_parceiro_propriedade else None
        id_parceiro_real = propriedade_externa.id_parceiro if propriedade_externa else None

    procedencia, destino = _buscar_dados_exibicao(
        id_produtor, id_parceiro_real, gta.id_parceiro_propriedade, gta.id_propriedade
    )

    # SimpleNamespace com os mesmos nomes de campo que o
    # template de edicao espera (mesmo formato usado por
    # gta_manual_cadastro.html) - datas formatadas como texto
    # dd/mm/aaaa, igual ao formulario espera reexibir.
    gta_form = SimpleNamespace(
        uf_gta=gta.uf_gta,
        serie_gta=gta.serie_gta,
        numero_gta_sequencial=gta.numero_gta_sequencial,
        numero_gta_completo=gta.numero_gta_completo,
        data_emissao=gta.data_emissao.strftime('%d/%m/%Y') if gta.data_emissao else '',
        data_validade=gta.data_validade.strftime('%d/%m/%Y') if gta.data_validade else '',
        data_entrega=gta.data_entrega.strftime('%d/%m/%Y') if gta.data_entrega else '',
        meio_transporte=gta.meio_transporte,
        qtde_animais_gta=gta.qtde_animais,
        confirma_dados=False,
    )

    return render_template(
        'produtor/gta_consulta_editar.html',
        erro=None,
        gta=gta_form,
        id_gta=id_gta,
        id_propriedade=id_propriedade,
        procedencia=procedencia,
        destino=destino,
        animais=animais,
        faixas_idade=FAIXAS_IDADE,
        especies=especies,
        sexos=SEXOS_VALIDOS,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='entrada',
    )


# -------------------------------------------------------
# Rota: POST /produtor/gta-consulta/salvar-edicao/<id_gta> —
# valida (mesmas regras de gta_manual.salvar()), grava as
# alteracoes na Gta/GtaAnimal e cria um log detalhado (1 linha
# por campo alterado) em tb_log_alteracao_gta.
# -------------------------------------------------------
@gta_consulta.route('/produtor/gta-consulta/salvar-edicao/<int:id_gta>', methods=['POST'])
def salvar_edicao(id_gta):
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_produtor = session['id_produtor']
    id_usuario = session.get('usuario_id')
    usuario_nome = session.get('usuario_nome', '')

    uf_gta                  = request.form.get('uf_gta', '').strip().upper()
    serie_gta                = request.form.get('serie_gta', '').strip().upper()
    numero_gta_sequencial    = ''.join(c for c in request.form.get('numero_gta_sequencial', '') if c.isdecimal())
    if numero_gta_sequencial:
        numero_gta_sequencial = numero_gta_sequencial.zfill(6)
    data_emissao_str         = request.form.get('data_emissao', '').strip()
    data_validade_str        = request.form.get('data_validade', '').strip()
    data_entrega_str         = request.form.get('data_entrega', '').strip()
    meio_transporte          = request.form.get('meio_transporte', '').strip().upper()
    qtde_animais_gta_str     = request.form.get('qtde_animais_gta', '').strip()
    confirma_dados           = request.form.get('confirma_dados') == 'on'

    especies = carregar_especies()   # v1.13.0 - catalogo tb_4002
    codigos_especie = codigos_validos(especies)

    especies_form    = request.form.getlist('especie[]')
    sexos_form       = request.form.getlist('sexo[]')
    idades_form      = request.form.getlist('idade_faixa[]')
    quantidades_form = request.form.getlist('quantidade[]')

    animais_novos = []
    for especie, sexo, idade, quantidade in zip(especies_form, sexos_form, idades_form, quantidades_form):
        especie = (especie or '').strip().upper()
        sexo    = (sexo or '').strip().upper()
        idade   = (idade or '').strip()
        qtd_str = (quantidade or '').strip()
        if not especie and not sexo and not idade and not qtd_str:
            continue
        try:
            qtd = int(qtd_str)
        except ValueError:
            qtd = 0
        animais_novos.append({
            'especie': codigo_da_especie(especie, especies) or especie,   # v1.13.0
            'sexo': sexo, 'idade_meses': idade, 'quantidade': qtd,
        })

    numero_gta_completo = f'{uf_gta}{serie_gta}{numero_gta_sequencial}'
    soma_animais = sum(a['quantidade'] for a in animais_novos)

    # Recarrega a GTA atual (antes da edicao) para comparacao e
    # para os blocos de conferencia da tela, caso precise reexibir
    # com erro.
    with get_db_produtor(id_produtor) as db:
        gta = db.get(Gta, id_gta)
        if not gta or not _propriedade_pertence_ao_produtor(id_produtor, gta.id_propriedade):
            return _voltar_ao_inicio_com_aviso('nao_achada')
        if _eh_carga(gta):   # v1.25.0 - a Carga nao e GTA: nao abre, nao edita, nao gera relatorio
            return _voltar_ao_inicio_com_aviso('carga')

        # NOVO v1.7.0: mesma trava de editar() - protege contra POST
        # manipulado direto para esta rota, pulando a tela/o GET.
        if gta.status_brincagem == 'BRINCADO' or _lidos_reservados_gta(db, gta.id):   # v1.20.0 - ou em leitura no brete
            return _ir_para_opcoes_com_aviso(id_gta, 'editar_bloqueada')

        animais_antigos = _animais_para_dict(list(gta.animais), especies)
        id_propriedade = gta.id_propriedade  # NOVO v1.6.0 - ver changelog
        sentido_gta = gta.sentido            # NOVO v1.14.0 - GTA duplicada compara no mesmo sentido

        propriedade_externa = db.get(ParceiroPropriedades, gta.id_parceiro_propriedade) if gta.id_parceiro_propriedade else None
        id_parceiro_real = propriedade_externa.id_parceiro if propriedade_externa else None

    procedencia, destino = _buscar_dados_exibicao(
        id_produtor, id_parceiro_real, gta.id_parceiro_propriedade, gta.id_propriedade
    )


    def _reexibir(mensagem_erro):
        gta_tentativa = SimpleNamespace(
            uf_gta=uf_gta, serie_gta=serie_gta, numero_gta_sequencial=numero_gta_sequencial,
            numero_gta_completo=numero_gta_completo,
            data_emissao=data_emissao_str, data_validade=data_validade_str, data_entrega=data_entrega_str,
            meio_transporte=meio_transporte, qtde_animais_gta=qtde_animais_gta_str, confirma_dados=confirma_dados,
        )
        return render_template(
            'produtor/gta_consulta_editar.html',
            erro=mensagem_erro,
            gta=gta_tentativa,
            id_gta=id_gta,
            id_propriedade=id_propriedade,
            procedencia=procedencia,
            destino=destino,
            animais=animais_novos,
            faixas_idade=FAIXAS_IDADE,
            especies=especies,
            sexos=SEXOS_VALIDOS,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='entrada',
        )

    # ---- Validacoes (mesmas regras de gta_manual.salvar()) ----
    if not uf_gta or len(uf_gta) != 2:
        return _reexibir('UF da GTA é obrigatória!')
    if not serie_gta or len(serie_gta) != tamanho_serie_gta(uf_gta) or not serie_gta.isalpha():
        return _reexibir(mensagem_serie_gta(uf_gta))
    if not numero_gta_sequencial or len(numero_gta_sequencial) != 6:
        return _reexibir('Número da GTA é obrigatório e deve ter 6 dígitos!')

    # ---------------------------------------------------
    # v1.14.0 - GTA DUPLICADA: outra GTA (que nao seja esta) ja tem a
    # mesma UF + Serie + Numero neste sentido? Avisa e IMPEDE.
    # ---------------------------------------------------
    with get_db_produtor(id_produtor) as db:
        gta_existente = buscar_gta_duplicada(
            db, uf_gta, serie_gta, numero_gta_sequencial, sentido_gta, id_ignorar=id_gta
        )
        mensagem_duplicada = mensagem_gta_duplicada(gta_existente) if gta_existente else None
    if mensagem_duplicada:
        return _reexibir(mensagem_duplicada)

    if not meio_transporte or meio_transporte not in MEIOS_TRANSPORTE_VALIDOS:
        return _reexibir('Selecione o Meio de Transporte!')

    try:
        qtde_animais_gta = int(qtde_animais_gta_str)
        if qtde_animais_gta <= 0:
            raise ValueError()
    except ValueError:
        return _reexibir('Quantidade de Animais na GTA é obrigatória e deve ser maior que zero!')

    data_emissao = data_validade = data_entrega = None

    if not data_emissao_str:
        return _reexibir('Data de Emissão é obrigatória!')
    try:
        data_emissao = datetime.strptime(data_emissao_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data de Emissão incorreta! Use o formato dd/mm/aaaa.')

    if not data_validade_str:
        return _reexibir('Data de Validade é obrigatória!')
    try:
        data_validade = datetime.strptime(data_validade_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data de Validade incorreta! Use o formato dd/mm/aaaa.')

    if data_validade < data_emissao:
        return _reexibir('Data de Validade não pode ser anterior à Data de Emissão!')

    if not data_entrega_str:
        return _reexibir('Data de Entrega é obrigatória!')
    try:
        data_entrega = datetime.strptime(data_entrega_str, '%d/%m/%Y').date()
    except ValueError:
        return _reexibir('Data de Entrega incorreta! Use o formato dd/mm/aaaa.')

    eh_comitiva = (meio_transporte == MEIO_TRANSPORTE_COMITIVA)
    limite_superior = data_validade + timedelta(days=TOLERANCIA_COMITIVA_DIAS) if eh_comitiva else data_validade

    if data_entrega < data_emissao:
        return _reexibir('Data de Entrega não pode ser anterior à Data de Emissão!')
    if data_entrega > limite_superior:
        if eh_comitiva:
            return _reexibir(f'Data de Entrega além do limite de tolerância para Comitiva (até 30 dias após a Validade, {limite_superior.strftime("%d/%m/%Y")})!')
        return _reexibir(f'Data de Entrega deve estar entre a Emissão ({data_emissao.strftime("%d/%m/%Y")}) e a Validade ({data_validade.strftime("%d/%m/%Y")})!')

    if not animais_novos:
        return _reexibir('Informe ao menos uma categoria de Animais!')

    for animal in animais_novos:
        if animal['especie'] not in codigos_especie:
            return _reexibir('Selecione a Espécie em todas as categorias de Animais.')
        if animal['sexo'] not in SEXOS_VALIDOS:
            return _reexibir('Selecione o Sexo em todas as categorias de Animais.')
        if animal['idade_meses'] not in FAIXAS_IDADE:
            return _reexibir('Selecione a Idade em todas as categorias de Animais.')
        if animal['quantidade'] <= 0:
            return _reexibir('Quantidade deve ser maior que zero em todas as categorias de Animais.')

    if soma_animais != qtde_animais_gta:
        if soma_animais < qtde_animais_gta:
            return _reexibir(f'Falta incluir {qtde_animais_gta - soma_animais} animal(is) para bater com a Quantidade declarada ({qtde_animais_gta}).')
        return _reexibir(f'A soma das categorias ({soma_animais}) excede a Quantidade declarada na GTA ({qtde_animais_gta}). Confira os valores.')

    if not confirma_dados:
        return _reexibir('Confirme que os dados foram conferidos antes de salvar!')

    # ---------------------------------------------------
    # Tudo validado - monta o diff (log) ANTES de gravar, comparando
    # contra os valores originais (gta, animais_antigos).
    # ---------------------------------------------------
    logs = []

    def _registrar(campo, valor_anterior, valor_novo):
        if str(valor_anterior) != str(valor_novo):
            logs.append(LogAlteracaoGta(
                id_gta=id_gta,
                id_usuario=id_usuario,
                usuario_nome=usuario_nome,
                campo_alterado=campo,
                valor_anterior=str(valor_anterior) if valor_anterior is not None else None,
                valor_novo=str(valor_novo) if valor_novo is not None else None,
            ))

    _registrar('UF', gta.uf_gta, uf_gta)
    _registrar('Série', gta.serie_gta, serie_gta)
    _registrar('Número', gta.numero_gta_sequencial, numero_gta_sequencial)
    _registrar('Data de Emissão', gta.data_emissao.strftime('%d/%m/%Y') if gta.data_emissao else '', data_emissao.strftime('%d/%m/%Y'))
    _registrar('Data de Validade', gta.data_validade.strftime('%d/%m/%Y') if gta.data_validade else '', data_validade.strftime('%d/%m/%Y'))
    _registrar('Data de Entrega', gta.data_entrega.strftime('%d/%m/%Y') if gta.data_entrega else '', data_entrega.strftime('%d/%m/%Y'))
    _registrar('Meio de Transporte', gta.meio_transporte, meio_transporte)
    _registrar('Quantidade de Animais na GTA', gta.qtde_animais, qtde_animais_gta)

    # ---- Diff detalhado por categoria de Animal ----
    def _chave(a):
        return (a['especie'], a['sexo'], a['idade_meses'])

    mapa_antigo = {_chave(a): a['quantidade'] for a in animais_antigos}
    mapa_novo = {_chave(a): a['quantidade'] for a in animais_novos}

    todas_chaves = set(mapa_antigo.keys()) | set(mapa_novo.keys())
    for chave in todas_chaves:
        rotulo = f'Animal: {chave[0]} {chave[1]} {chave[2]}'
        qtd_antiga = mapa_antigo.get(chave)
        qtd_nova = mapa_novo.get(chave)

        if qtd_antiga is None and qtd_nova is not None:
            logs.append(LogAlteracaoGta(
                id_gta=id_gta, id_usuario=id_usuario, usuario_nome=usuario_nome,
                campo_alterado=rotulo, valor_anterior=None, valor_novo=f'ADICIONADA (qtd {qtd_nova})',
            ))
        elif qtd_antiga is not None and qtd_nova is None:
            logs.append(LogAlteracaoGta(
                id_gta=id_gta, id_usuario=id_usuario, usuario_nome=usuario_nome,
                campo_alterado=rotulo, valor_anterior=f'qtd {qtd_antiga}', valor_novo='REMOVIDA',
            ))
        elif qtd_antiga != qtd_nova:
            logs.append(LogAlteracaoGta(
                id_gta=id_gta, id_usuario=id_usuario, usuario_nome=usuario_nome,
                campo_alterado=rotulo, valor_anterior=str(qtd_antiga), valor_novo=str(qtd_nova),
            ))

    # ---------------------------------------------------
    # Grava: atualiza a Gta, apaga as linhas antigas de
    # GtaAnimal e recria com os valores novos, grava o log -
    # tudo na mesma transacao.
    # ---------------------------------------------------
    with get_db_produtor(id_produtor) as db:
        try:
            # Etapa 4 (item 5): trava da Propriedade e confere de novo, DENTRO da gravacao: se o brete comecou a ler no meio, nao edita.
            db.execute(text('SELECT pg_advisory_xact_lock(:ns, :id)'), {'ns': TRAVA_BRINCOS_NASC, 'id': int(id_propriedade)})
            gta_db = db.get(Gta, id_gta)
            if gta_db is None or gta_db.status_brincagem == 'BRINCADO' or _lidos_reservados_gta(db, id_gta):
                db.rollback()
                return _ir_para_opcoes_com_aviso(id_gta, 'salvar_bloqueado')

            gta_db.uf_gta = uf_gta
            gta_db.serie_gta = serie_gta
            gta_db.numero_gta_sequencial = numero_gta_sequencial
            gta_db.numero_gta_completo = numero_gta_completo
            gta_db.qtde_animais = qtde_animais_gta
            gta_db.data_emissao = data_emissao
            gta_db.data_validade = data_validade
            gta_db.data_entrega = data_entrega
            gta_db.meio_transporte = meio_transporte
            gta_db.atualizado_em = datetime.now()

            db.query(GtaAnimal).filter_by(id_gta=id_gta).delete()

            for animal in animais_novos:
                db.add(GtaAnimal(
                    id_gta=id_gta,
                    especie=animal['especie'],
                    sexo=animal['sexo'],
                    idade_meses=animal['idade_meses'],
                    quantidade=animal['quantidade'],
                ))

            for log in logs:
                db.add(log)

            db.commit()
        except IntegrityError as erro_banco:
            # v1.14.0 - outra pessoa gravou a MESMA GTA no mesmo instante:
            # a trava do banco recusou. Nada foi gravado (rollback).
            db.rollback()
            if not eh_violacao_unicidade_gta(erro_banco):
                raise
            gta_existente = buscar_gta_duplicada(
                db, uf_gta, serie_gta, numero_gta_sequencial, sentido_gta, id_ignorar=id_gta
            )
            if gta_existente:
                return _reexibir(mensagem_gta_duplicada(gta_existente))
            return _reexibir(
                'Esta GTA acabou de ser cadastrada por outra pessoa. '
                'Não é permitido cadastrar a mesma GTA duas vezes.'
            )

    return redirect(f'/produtor/gta-consulta/detalhe/{id_gta}')

# =========================================================
# FIM DE ARQUIVO: backend\routers\gta_consulta.py
# =========================================================
