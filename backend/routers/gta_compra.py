# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\routers
# MODULO:       backend\routers\gta_compra.py
# AUTOR:        Benedito Silva Filho.
# CRIADO EM:    2026-07-29 12:49 -03
# ATUALIZADO EM: 2026-10-04 17:50 -03
# VERSAO:       2.8.0
#
# DESCRICAO:
#     Rotas da tela de leitura/cadastro de GTA de Entrada por
#     Compra. Primeira tela de movimento (GTA/Brincagem)
#     construida para o perfil PRODUTOR/FAZENDA.
#     - /produtor/entrada/compra/nova    -> formulario (dropzone
#       de upload quando gta e None, formulario preenchido
#       quando gta existe - mesmo padrao ja usado em outras
#       telas do Orion)
#     - /produtor/entrada/compra/ler     -> NOVA (Sessao 029):
#       recebe o PDF, salva em disco, roda o leitor automatico
#       (backend/leitores/) e devolve a MESMA tela ja
#       pre-preenchida, pronta para conferencia humana
#     - /produtor/entrada/compra/salvar  -> valida e captura
#
#     ESCOPO DESTA VERSAO (Sessao 029): a leitura automatica do
#     PDF (MS/IAGRO) e o salvamento do arquivo em disco com hash
#     SHA-256 JA FUNCIONAM DE VERDADE. A logica de busca em duas
#     etapas do Destino (Propriedade propria vs Parceiro externo)
#     e a gravacao real em tb_4001_gta / tb_4001_gta_animais
#     continuam pendentes - salvar() ainda so valida e recaptura,
#     igual as versoes anteriores.
#
#     Layout final fechado com Benedito, campo a campo, contra
#     um e-GTA real (MS/IAGRO):
#       - UF/Serie/Numero + Emissao/Validade/Entrega sao TEXTO
#         LIVRE (transcricao fiel do documento, sem dropdown/
#         calendario - o dado ja vem pronto no papel). A partir
#         da v2.3.0 (Sessao 034, continuacao), Entrega tambem
#         passou a ser texto livre dd/mm/aaaa, igual Emissao/
#         Validade - unifica o padrao de transcricao manual da
#         tela (decisao de Benedito). Continua sendo o UNICO
#         campo desta tela com decisao real do usuario (quando
#         os animais chegaram de fato) - por isso NUNCA vem
#         preenchida pela leitura automatica, nem em ler().
#       - Procedencia e Destino ficam lado a lado, espelhados,
#         com os mesmos 8 campos que a GTA real traz dos dois
#         lados (CPF/CNPJ, Regiao, Nome, Estabelecimento, Codigo
#         MAPA, Insc. Estadual, Municipio, UF) - tudo texto livre,
#         sem nenhuma consulta ao banco (a resolucao de
#         Procedencia/Destino contra o cadastro fica para a
#         proxima etapa). Campo "Tipo" (Parceiro/Frigorifico)
#         removido - decisao de Benedito: a Procedencia ja deixa
#         implicito que e um fornecedor externo, nao precisa
#         qualificar o tipo aqui.
#       - Animais: tabela de linhas (Especie/Sexo/Idade/Quantidade,
#         tudo texto livre, sem dropdown de Sexo). A partir da
#         v2.3.0/template v2.4.0 (Sessao 034, continuacao), os
#         botoes "+ Adicionar Categoria" e de excluir linha foram
#         REMOVIDOS de vez - decisao de Benedito: a tabela de
#         Animais e so exibicao fiel do que a leitura automatica
#         extraiu, o usuario nao pode incluir nem excluir linha
#         (mesmo principio ja aplicado aos demais campos - "o que
#         esta na GTA e LEI"). O fluxo manual (quando a leitura
#         falha) sera redesenhado do zero numa proxima etapa, com
#         mecanismo proprio - nao reaproveita mais este botao.
#         Painel de resumo Femea/Macho/Total/Total por Extenso,
#         tudo CALCULADO automaticamente a partir das linhas -
#         nunca digitado.
#       - REMOVIDOS de vez (P-028): Finalidade, Marca do Rebanho,
#         Rota, Evento, Local Evento, Vacinacoes, Observacoes,
#         Nome/Cargo do Emitente. Ficam so no documento fisico -
#         Benedito: "o que esta na GTA e LEI, nossa
#         responsabilidade e apresentar os dados sem permissao de
#         alterar nada; se o Produtor fraudar o documento, o
#         problema e dele perante o Auditor Federal".
#       - Meio de Transporte (Sessao 027): REABERTO pontualmente
#         do P-028 - volta como texto livre porque ganhou regra
#         de negocio real (ver abaixo). Agora tambem preenchido
#         automaticamente pela leitura.
#       - Codigo de Barras IAGRO (Sessao 029 - decisao de
#         Benedito): REMOVIDO de vez. O leitor nao captura mais
#         esse campo - o Codigo de Autenticidade sozinho ja e
#         resguardo documental suficiente, e a tabela real
#         tb_4001_gta nunca teve coluna para o Codigo de Barras
#         (discrepancia identificada na Sessao 027, Referencia
#         14.5). Campo hidden removido do formulario tambem
#         (template v2.3.0).
#
#     tipo_movimento e sentido continuam fixos (nunca escolhidos
#     pelo usuario): COMPRA / ENTRADA.
#
#     ARMAZENAMENTO DO PDF (Sessao 029): salvo em
#     C:\orion\storage\gtas\, pasta FORA do static do Flask de
#     proposito - o documento carrega CPF/CNPJ de Procedencia e
#     Destino, dado sensivel que nao pode ficar exposto por URL
#     publica (convencao geral de upload do Orion, Referencia
#     Secao 4: nome sempre gerado pelo sistema, nunca sobrescreve,
#     validacao de extensao obrigatoria no servidor). Nome gerado:
#     "{timestamp}_{8 primeiros caracteres do hash}.pdf" - nao usa
#     o numero da GTA no nome porque, no momento de salvar o
#     arquivo, o numero ainda nao foi lido (a leitura acontece
#     DEPOIS do arquivo estar salvo em disco).
#
#     REGRA DE NEGOCIO (Sessao 027, mantida) - Data de Entrega:
#       - Campo obrigatorio, sem valor padrao "hoje".
#       - Janela permitida: Emissao <= Entrega <= Validade.
#       - EXCECAO Comitiva: se Meio de Transporte for exatamente
#         "COMITIVA", a janela se estende para Validade + 30 dias
#         (regra do MAPA para transporte conduzido a pe).
#       - Fora da janela: bloqueia o salvamento, erro unico,
#         formulario reexibido com os dados preservados.
#
#     REGRA DE NEGOCIO (Sessao 027, mantida) - Trava do botao
#     Salvar: 4 checkboxes de confirmacao (Documento, Procedencia,
#     Destino, Animais) - revalidados no servidor, nunca confia
#     so no JavaScript. IMPORTANTE (Sessao 029): mesmo apos a
#     leitura automatica preencher os campos, os 4 checkboxes
#     SEMPRE voltam desmarcados - o usuario precisa conferir os
#     dados lidos contra o documento fisico e marcar manualmente,
#     a leitura automatica nao substitui essa conferencia humana.
#
#     v1.0.0: Criacao do modulo (Sessao 026).
#     v1.1.0: Sessao 026 - Blocos Procedencia e Destino expandidos
#             e deixados simetricos (Regiao, Codigo MAPA, Insc.
#             Estadual, Municipio, UF nos dois lados).
#     v2.0.0: Sessao 026 - Layout definitivo, fechado campo a
#             campo com Benedito contra um e-GTA real.
#     v2.1.0: Sessao 027 - Data de Entrega obrigatoria sem valor
#             padrao; novo campo meio_transporte; nova regra de
#             janela (+30 dias Comitiva); 4 checks de confirmacao
#             revalidados no servidor.
#     v2.2.0: Sessao 029 - Leitura automatica de e-GTA implementada
#             de verdade:
#               (1) Nova rota /produtor/entrada/compra/ler (POST):
#                   recebe o arquivo, valida extensao .pdf,
#                   calcula hash SHA-256, salva em
#                   C:\orion\storage\gtas\, chama
#                   backend.leitores.registry.ler_gta() e devolve
#                   a tela pre-preenchida (checkboxes de
#                   confirmacao sempre desmarcados);
#               (2) Nova funcao auxiliar _resumir_animais(),
#                   reaproveitando a mesma logica de calculo de
#                   _ler_animais_do_formulario(), agora aplicada
#                   sobre a lista de dicts que o leitor devolve
#                   (em vez de arrays de formulario);
#               (3) Removido o campo codigo_barras_iagro de toda
#                   a rota salvar() (leitura e reexibicao) -
#                   decisao de Benedito, Sessao 029: o Codigo de
#                   Autenticidade sozinho ja basta como resguardo
#                   documental.
#     v2.3.0: Sessao 034 (continuacao, 07/08/2026):
#               (1) Data de Entrega deixa de usar <input
#                   type="date"> nativo (formato ISO Y-m-d) e
#                   passa a ser texto livre dd/mm/aaaa, igual
#                   Emissao/Validade - parse no servidor mudou de
#                   '%Y-%m-%d' para '%d/%m/%Y'; adicionada ao
#                   dicionario LIMITES_TAMANHO (10 caracteres,
#                   mesmo padrao das demais datas em texto);
#               (2) Regra de linguagem do sistema (Referencia,
#                   Secao 6): toda ocorrencia de "invalido/
#                   invalida" trocada por "incorreto/incorreta"
#                   nas mensagens de erro desta rota (3 pontos:
#                   Emissao, Validade, Entrega).
#     v2.4.0: Sessao 034 (continuacao 4, 10/08/2026) - Rota
#             salvar() passa a capturar 2 campos novos, escondidos
#             (hidden) no formulario: procedencia_municipio_codigo
#             e destino_municipio_codigo (codigo oficial do
#             Municipio, ex.: 5006408 - ver leitor_ms_iagro.py
#             v1.1.0 e gta_compra_cadastro.html v2.8.0). Adicionados
#             ao dicionario LIMITES_TAMANHO (10 caracteres, mesmo
#             tamanho da coluna municipio_codigo em
#             tb_parceiros_propriedades) e preservados em
#             gta_tentativa para sobreviver a um reexibicao por
#             erro de validacao. NAO SAO OBRIGATORIOS e NAO SAO
#             validados por regra de negocio nesta versao - so
#             capturados e guardados, para uso futuro pela funcao
#             resolver_parceiro() (backend/servicos/, ainda nao
#             implementada). NENHUM campo visivel, mensagem de
#             erro ou comportamento ja existente foi alterado.
#     v2.5.0: Sessao 034 (continuacao 5, 11/08/2026) - BLOCO DE
#             TESTE TEMPORARIO da funcao resolver_parceiro()
#             (backend/servicos/resolver_parceiro.py v1.0.0),
#             alinhado com Benedito. Motivo: salvar() ainda NAO
#             grava a GTA de verdade em tb_4001_gta (ver ESCOPO
#             DESTA VERSAO acima) - integrar resolver_parceiro()
#             com commit real agora criaria Parceiro/Propriedade
#             orfaos no banco, sem a GTA correspondente. Ate a
#             gravacao real da GTA ser implementada, o teste roda
#             assim: quando erro_validacao is None (mesmo ponto
#             onde captura_confirmada vira True), abre
#             `with Session(engine) as db:`, chama
#             resolver_parceiro(db, ...) passando os dados de
#             Procedencia ja capturados do formulario, faz print()
#             do resultado no terminal do Waitress para
#             conferencia manual, e SEMPRE chama db.rollback()
#             explicito no final - nada e gravado de verdade.
#             Motivo do rollback: so existe 1 GTA de teste real
#             disponivel (Faz. Olho D'Agua / Maria Angelica) -
#             gravar de verdade consumiria o dado de teste,
#             impedindo repetir o clique em Salvar sem limpeza
#             manual no banco. NENHUM campo visivel, mensagem de
#             erro ou comportamento ja existente foi alterado -
#             o bloco roda em silencio, so aparece no terminal.
#             Quando a integracao definitiva (com commit real)
#             for feita, este bloco de teste sera removido/
#             substituido - ver Diario de Bordo Sessao 034 cont.4,
#             Secao 10, itens 2 a 5.
#     v2.6.0: Sessao 034 (continuacao 5, 11/08/2026, 11:21 -03) -
#             DUAS correcoes no bloco de teste do resolver_parceiro(),
#             alinhadas com Benedito apos erro real em teste:
#               (1) TROCA de Session(engine) por
#                   get_db_produtor(session['id_produtor'])
#                   (backend/utils/multitenant.py, ja existente).
#                   Motivo: teste real disparou
#                   psycopg2.errors.UndefinedTable para tb_parceiros
#                   - a tabela NAO vive no schema public, vive
#                   dentro do schema de cada Produtor (arquitetura
#                   Schema-por-Produtor, ex.: produtor_00005),
#                   confirmado por query direta em
#                   information_schema.tables. Session(engine) puro
#                   abre a conexao no schema padrao (public), onde
#                   tb_parceiros nao existe - por isso o erro.
#                   get_db_produtor() ja resolve isso (SET
#                   search_path para o schema certo + public), e ja
#                   e o mecanismo oficial do projeto para esse fim -
#                   nao reimplementado na mao aqui.
#               (2) REMOVIDO o db.rollback() explicito do final do
#                   bloco - decisao de Benedito: "vamos testar a
#                   rotina completa, depois a gente faz o rollback"
#                   - ou seja, o teste agora faz commit de verdade
#                   (Parceiro/Propriedade/Log gravados de fato em
#                   produtor_NNNNN), para validar o fluxo ponta a
#                   ponta contra o banco real. A limpeza dos dados de
#                   teste, se for preciso repetir o teste do zero,
#                   passa a ser MANUAL via pgAdmin (nao automatica
#                   por rollback como na v2.5.0). Print() de
#                   resultado no terminal mantido, sem mudanca.
#               Imports ajustados: removidos
#               'from sqlalchemy.orm import Session' e
#               'from backend.database import engine' (nao usados
#               mais diretamente neste arquivo); adicionado
#               'from backend.utils.multitenant import
#               get_db_produtor'.
#     v2.7.0: Sessao 034 (continuacao 9, 18/08/2026, 20:51 -03) -
#             BUG REAL encontrado ao testar a tela de consulta de
#             Parceiros/Fornecedores (backend/routers/parceiros_
#             fornecedores.py, criada nesta mesma sessao): o campo
#             Regiao da Procedencia (procedencia_regiao, ja
#             capturado do formulario desde sempre, e a funcao
#             resolver_parceiro() ja aceita o parametro regiao=
#             desde a v1.0.0) NUNCA era repassado na chamada real
#             dentro do bloco de teste - ficava sempre None em
#             tb_parceiros_propriedades.regiao, mesmo a GTA real
#             trazendo o dado (confirmado comparando a GTA fisica
#             da Roselene/Fazenda Tres Barras, campo Regiao:
#             PLANALTO, contra o registro gravado no teste da
#             Sessao 034 cont. 9, que veio sem regiao). Corrigido:
#             adicionada a linha regiao=procedencia_regiao na
#             chamada de resolver_parceiro() dentro do bloco de
#             teste. NENHUM outro campo, mensagem ou comportamento
#             alterado.
#     v2.8.0: Sessao 085 (04/10/2026, 17:50 -03) - GTA DUPLICADA (regra
#             de Benedito: jamais duas GTAs iguais - UF + Serie + Numero
#             + sentido, dentro do mesmo Produtor; ver backend/utils/
#             gta_duplicada.py). Conferida em 2 pontos, SEMPRE antes de
#             qualquer gravacao:
#               - ler(): assim que o PDF e lido, se a GTA ja existe no
#                 Produtor, avisa na propria tela de upload e o
#                 formulario nem chega a ser preenchido;
#               - salvar(): logo apos a obrigatoriedade de UF/Serie/
#                 Numero e ANTES do bloco de teste que grava o Parceiro
#                 (resolver_parceiro) - GTA repetida nao cria Parceiro.
#             A gravacao real da GTA continua fora desta tela (so
#             gta_manual.py grava hoje); quando esta tela passar a
#             gravar, a trava do banco (uq_tb_4001_gta_uf_serie_numero_
#             sentido) tambem vale para ela. Nenhuma outra mudanca.
# =========================================================

import hashlib
import os
from datetime import datetime, date, timedelta
from types import SimpleNamespace
from flask import Blueprint, render_template, request, redirect, url_for, session

from backend.leitores import registry as leitores_registry
from backend.servicos.resolver_parceiro import resolver_parceiro
from backend.utils.multitenant import get_db_produtor
from backend.utils.gta_duplicada import buscar_gta_duplicada, mensagem_gta_duplicada

# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
gta_compra = Blueprint('gta_compra', __name__)

# -------------------------------------------------------
# Fixos desta tela (nunca escolhidos pelo usuario)
# -------------------------------------------------------
SENTIDO_FIXO         = 'ENTRADA'
TIPO_MOVIMENTO_FIXO  = 'COMPRA'

# -------------------------------------------------------
# Valor exato (apos normalizacao maiuscula/trim) que, transcrito
# no campo Meio de Transporte, aciona a tolerancia de 30 dias na
# Data de Entrega (regra do MAPA para transporte conduzido a pe -
# Sessao 027, ver DESCRICAO acima).
# -------------------------------------------------------
MEIO_TRANSPORTE_COMITIVA   = 'COMITIVA'
TOLERANCIA_COMITIVA_DIAS   = 30

# -------------------------------------------------------
# Pasta onde os PDFs de e-GTA lidos automaticamente sao salvos
# (Sessao 029). FORA da pasta static do Flask, de proposito - o
# documento carrega CPF/CNPJ de Procedencia e Destino, dado
# sensivel que nao pode ficar exposto por URL publica (ver
# DESCRICAO acima).
# -------------------------------------------------------
PASTA_ARMAZENAMENTO_GTA = r'C:\orion\storage\gtas'


# -------------------------------------------------------
# Funcao auxiliar: converte um numero inteiro (0 a 999.999)
# para extenso em portugues. Usada no painel de resumo de
# Animais (Total por Extenso), espelhando o mesmo calculo
# feito no JS da tela - o servidor recalcula ao reexibir o
# formulario (apos erro, leitura automatica, ou captura
# confirmada), nunca confia so no que o JS mandou.
# -------------------------------------------------------
_UNIDADES = ['', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove']
_DEZ_A_DEZENOVE = ['dez', 'onze', 'doze', 'treze', 'quatorze', 'quinze', 'dezesseis', 'dezessete', 'dezoito', 'dezenove']
_DEZENAS = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa']
_CENTENAS = ['', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos', 'seiscentos', 'setecentos', 'oitocentos', 'novecentos']


def _grupo_ate_999_por_extenso(n):
    """Converte um numero de 0 a 999 para extenso, sem sufixo de milhar."""
    if n == 0:
        return ''
    if n == 100:
        return 'cem'

    partes = []
    centena, resto = divmod(n, 100)
    if centena:
        partes.append(_CENTENAS[centena])

    if resto:
        if partes:
            partes.append('e')
        if resto < 10:
            partes.append(_UNIDADES[resto])
        elif resto < 20:
            partes.append(_DEZ_A_DEZENOVE[resto - 10])
        else:
            dezena, unidade = divmod(resto, 10)
            if unidade:
                partes.append(_DEZENAS[dezena] + ' e ' + _UNIDADES[unidade])
            else:
                partes.append(_DEZENAS[dezena])

    return ' '.join(partes)


def numero_para_extenso(n):
    """Converte um numero inteiro (0 a 999.999) para extenso em
    portugues. Ex.: 21 -> 'vinte e um'; 1234 -> 'mil, duzentos e
    trinta e quatro'. Numeros fora da faixa retornam o proprio
    numero como string (protecao, nao deve acontecer em uso
    normal - lote de animais nesta grandeza seria excepcional)."""
    if n < 0 or n > 999999:
        return str(n)

    if n == 0:
        return 'zero'

    milhar, resto_grupo = divmod(n, 1000)

    partes = []
    if milhar:
        if milhar == 1:
            partes.append('mil')
        else:
            partes.append(_grupo_ate_999_por_extenso(milhar) + ' mil')

    if resto_grupo:
        texto_resto = _grupo_ate_999_por_extenso(resto_grupo)
        if milhar:
            # Separador de milhar por virgula quando o resto nao
            # comeca com "e" natural (regra de portugues formal
            # simplificada - suficiente para o uso desta tela)
            if resto_grupo < 100:
                partes.append('e ' + texto_resto)
            else:
                partes[-1] = partes[-1] + ','
                partes.append(texto_resto)
        else:
            partes.append(texto_resto)

    return ' '.join(partes)


def _resumir_animais(animais):
    """Calcula o resumo Femea/Macho/Total/Total por Extenso a
    partir de uma lista de dicts {especie, sexo, idade_meses,
    quantidade} - MESMO formato de saida que
    _ler_animais_do_formulario() ja produzia a partir dos arrays
    do formulario, e MESMO formato que
    backend/leitores/leitor_ms_iagro.py devolve na chave
    'animais'. Reaproveitada tanto por ler() (Sessao 029) quanto
    poderia ser reaproveitada por salvar() no futuro, se um dia
    fizer sentido unificar as duas funcoes de resumo."""
    total_femea = 0
    total_macho = 0

    for animal in animais:
        sexo = (animal.get('sexo') or '').strip().upper()
        quantidade = animal.get('quantidade') or 0

        if sexo.startswith('F'):
            total_femea += quantidade
        elif sexo.startswith('M'):
            total_macho += quantidade

    total_geral = total_femea + total_macho
    total_extenso = f'{numero_para_extenso(total_geral)} animais'.upper() if total_geral else ''

    return {
        'femea':         total_femea,
        'macho':         total_macho,
        'total':         total_geral,
        'total_extenso': total_extenso
    }


# -------------------------------------------------------
# Funcao auxiliar: le as linhas dinamicas da tabela de Animais
# vindas do formulario (arrays especie[]/sexo[]/idade_meses[]/
# quantidade[]), devolve a lista de dicts + o resumo (femea,
# macho, total, total_extenso). Reaproveitada em nova() (recarga
# apos erro) e salvar(). Continua funcionando mesmo sem os botoes
# de adicionar/excluir linha no template (v2.4.0 do template) -
# as linhas ainda chegam como arrays de formulario, so nao podem
# mais ser adicionadas/removidas pela interface.
# -------------------------------------------------------
def _ler_animais_do_formulario():
    especies      = request.form.getlist('especie[]')
    sexos         = request.form.getlist('sexo[]')
    idades_meses  = request.form.getlist('idade_meses[]')
    quantidades   = request.form.getlist('quantidade[]')

    animais = []

    for especie, sexo, idade_meses, quantidade in zip(especies, sexos, idades_meses, quantidades):
        especie     = (especie or '').strip().upper()
        sexo        = (sexo or '').strip().upper()
        idade_meses = (idade_meses or '').strip().upper()
        qtd_str     = (quantidade or '').strip()

        # Ignora linha totalmente vazia
        if not especie and not sexo and not idade_meses and not qtd_str:
            continue

        try:
            qtd = int(qtd_str)
        except ValueError:
            qtd = 0

        animais.append({
            'especie':     especie or 'BOVINO',
            'sexo':        sexo,
            'idade_meses': idade_meses,
            'quantidade':  qtd
        })

    resumo = _resumir_animais(animais)

    return animais, resumo


# -------------------------------------------------------
# Rota: /produtor/entrada/compra/nova — formulario
# Requer perfil PRODUTOR ou FAZENDA.
# -------------------------------------------------------
@gta_compra.route('/produtor/entrada/compra/nova')
def nova():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') not in ('PRODUTOR', 'FAZENDA'):
        return redirect(url_for('auth.produtor_home'))

    return render_template('produtor/gta_compra_cadastro.html',
        gta                  = None,
        animais              = [],
        resumo_animais       = {'femea': 0, 'macho': 0, 'total': 0, 'total_extenso': ''},
        captura_confirmada   = False,
        erro                 = None,
        usuario_nome         = session.get('usuario_nome'),
        usuario_perfil       = session.get('usuario_perfil'),
        cor_primaria         = session.get('cor_primaria', '#D4370A'),
        nome_sistema         = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo           = 'entrada'
    )


# -------------------------------------------------------
# Rota: /produtor/entrada/compra/ler — NOVA (Sessao 029)
# Recebe o PDF enviado no dropzone, salva em disco com hash
# SHA-256, roda o leitor automatico (backend/leitores/registry.py)
# e devolve a MESMA tela ja pre-preenchida com os dados lidos -
# checkboxes de confirmacao sempre desmarcados, forcando a
# conferencia humana contra o documento fisico antes de salvar.
#
# NOTA (Sessao 034 cont. 4): a partir de leitor_ms_iagro.py
# v1.1.0, o dict devolvido por ler_gta() ja inclui as chaves
# procedencia_municipio_codigo / destino_municipio_codigo. Como
# esta rota so faz dados_lidos.pop(...)/dados_lidos.update(...)
# e depois SimpleNamespace(**dados_lidos), essas duas chaves
# novas ja chegam automaticamente em gta_lida, sem precisar
# tocar em nada aqui - so o template precisou ganhar os 2 campos
# hidden novos (ver gta_compra_cadastro.html v2.8.0) para elas
# sobreviverem ate o clique em Salvar.
#
# Se o arquivo nao for reconhecido (ValueError vindo do
# registry/leitor), reexibe o dropzone de upload (gta=None) com
# a mensagem de erro - nunca preenche a tela pela metade.
# -------------------------------------------------------
@gta_compra.route('/produtor/entrada/compra/ler', methods=['POST'])
def ler():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') not in ('PRODUTOR', 'FAZENDA'):
        return redirect(url_for('auth.produtor_home'))

    def _reexibir_dropzone(mensagem_erro):
        """Reexibe a tela no estado inicial (dropzone de upload),
        com a mensagem de erro. Usada em todos os pontos de saida
        com falha desta rota - nunca preenche o formulario pela
        metade."""
        return render_template('produtor/gta_compra_cadastro.html',
            gta                  = None,
            animais              = [],
            resumo_animais       = {'femea': 0, 'macho': 0, 'total': 0, 'total_extenso': ''},
            captura_confirmada   = False,
            erro                 = mensagem_erro,
            usuario_nome         = session.get('usuario_nome'),
            usuario_perfil       = session.get('usuario_perfil'),
            cor_primaria         = session.get('cor_primaria', '#D4370A'),
            nome_sistema         = session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo           = 'entrada'
        )

    arquivo = request.files.get('arquivo_gta')

    if arquivo is None or arquivo.filename == '':
        return _reexibir_dropzone(
            'Sr. Usuário(a), nenhum arquivo foi selecionado. '
            'Escolha o PDF da e-GTA antes de enviar.'
        )

    if not arquivo.filename.lower().endswith('.pdf'):
        # Validacao de extensao no servidor - o atributo accept do
        # HTML e so sugestao visual, nunca garantia (convencao
        # geral de upload do Orion, Referencia Secao 4).
        return _reexibir_dropzone(
            'Sr. Usuário(a), o arquivo enviado precisa ser um PDF (.pdf).'
        )

    conteudo_binario = arquivo.read()
    hash_sha256 = hashlib.sha256(conteudo_binario).hexdigest()

    # Nome sempre gerado pelo sistema (nunca o nome original
    # enviado pelo usuario) - convencao geral de upload do Orion.
    # Usa timestamp + 8 primeiros caracteres do hash (nao usa o
    # numero da GTA no nome porque, no momento de salvar o
    # arquivo, o numero ainda nao foi lido).
    nome_gerado = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_{hash_sha256[:8]}.pdf'
    os.makedirs(PASTA_ARMAZENAMENTO_GTA, exist_ok=True)
    caminho_completo = os.path.join(PASTA_ARMAZENAMENTO_GTA, nome_gerado)

    with open(caminho_completo, 'wb') as arquivo_no_disco:
        arquivo_no_disco.write(conteudo_binario)

    try:
        dados_lidos = leitores_registry.ler_gta(caminho_completo)
    except ValueError as erro_leitura:
        # O arquivo ja ficou salvo em disco mesmo assim (orfao,
        # mas preservado - mesma convencao geral de upload do
        # Orion). Nao apaga: pode ser util para diagnostico do
        # motivo da falha de leitura.
        return _reexibir_dropzone(str(erro_leitura))

    # -----------------------------------------------------
    # v2.8.0 - GTA DUPLICADA: se a GTA lida ja existe neste Produtor
    # (mesma UF + Serie + Numero, sentido ENTRADA), avisa AQUI e impede
    # a entrada. O PDF ja ficou guardado em disco acima (mesma
    # convencao do erro de leitura - preservado para diagnostico).
    # -----------------------------------------------------
    if session.get('id_produtor'):
        with get_db_produtor(session.get('id_produtor')) as db:
            gta_existente = buscar_gta_duplicada(
                db,
                dados_lidos.get('uf_gta'),
                dados_lidos.get('serie_gta'),
                dados_lidos.get('numero_gta_sequencial'),
                SENTIDO_FIXO,
            )
            mensagem_duplicada = mensagem_gta_duplicada(gta_existente) if gta_existente else None
        if mensagem_duplicada:
            return _reexibir_dropzone(mensagem_duplicada)

    animais = dados_lidos.pop('animais')
    dados_lidos.pop('orgao_emissor_identificado', None)
    resumo_animais = _resumir_animais(animais)

    dados_lidos['arquivo_pdf_caminho'] = nome_gerado
    dados_lidos['arquivo_pdf_hash']    = hash_sha256

    # Data de Entrega e a UNICA decisao real do usuario nesta
    # tela - nunca vem preenchida pela leitura automatica (ver
    # DESCRICAO no topo do arquivo).
    dados_lidos['data_entrega'] = ''

    # Os 4 checkboxes de confirmacao SEMPRE comecam desmarcados,
    # mesmo apos a leitura automatica - o usuario precisa
    # conferir os dados lidos contra o documento fisico e marcar
    # manualmente (decisao de Benedito, Sessao 027, reafirmada na
    # Sessao 029: a leitura automatica nao substitui a conferencia
    # humana).
    dados_lidos['confirma_documento']   = False
    dados_lidos['confirma_procedencia'] = False
    dados_lidos['confirma_destino']     = False
    dados_lidos['confirma_animais']     = False

    gta_lida = SimpleNamespace(**dados_lidos)

    return render_template('produtor/gta_compra_cadastro.html',
        gta                  = gta_lida,
        animais              = animais,
        resumo_animais       = resumo_animais,
        captura_confirmada   = False,
        erro                 = None,
        usuario_nome         = session.get('usuario_nome'),
        usuario_perfil       = session.get('usuario_perfil'),
        cor_primaria         = session.get('cor_primaria', '#D4370A'),
        nome_sistema         = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo           = 'entrada'
    )


# -------------------------------------------------------
# Rota: /produtor/entrada/compra/salvar — valida e captura
# NAO grava no banco ainda (decisao de Benedito, Sessao 026 -
# a logica de busca em duas etapas do Destino e a gravacao real
# entram numa proxima sessao).
# -------------------------------------------------------
@gta_compra.route('/produtor/entrada/compra/salvar', methods=['POST'])
def salvar():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('usuario_perfil') not in ('PRODUTOR', 'FAZENDA'):
        return redirect(url_for('auth.produtor_home'))

    uf_gta                   = request.form.get('uf_gta', '').upper()
    serie_gta                = request.form.get('serie_gta', '').upper()
    numero_gta_sequencial    = request.form.get('numero_gta_sequencial', '').upper()
    data_emissao_str         = request.form.get('data_emissao', '').strip()
    data_validade_str        = request.form.get('data_validade', '').strip()
    data_entrega_str         = request.form.get('data_entrega', '').strip()
    meio_transporte          = request.form.get('meio_transporte', '').strip().upper()

    procedencia_documento      = request.form.get('procedencia_documento', '')
    procedencia_regiao         = request.form.get('procedencia_regiao', '').upper()
    procedencia_nome           = request.form.get('procedencia_nome', '').upper()
    procedencia_propriedade    = request.form.get('procedencia_propriedade', '').upper()
    procedencia_codigo_mapa    = request.form.get('procedencia_codigo_mapa', '').upper()
    procedencia_insc_estadual  = request.form.get('procedencia_insc_estadual', '').upper()
    procedencia_municipio      = request.form.get('procedencia_municipio', '').upper()
    # Codigo do Municipio (Sessao 034 cont. 4) - viaja escondido
    # (campo hidden), nao aparece na tela. Alimenta a
    # resolver_parceiro() (ver bloco de teste no final desta
    # funcao); nao e obrigatorio nem validado por regra de
    # negocio nesta versao.
    procedencia_municipio_codigo = request.form.get('procedencia_municipio_codigo', '')
    procedencia_uf             = request.form.get('procedencia_uf', '').upper()

    destino_documento           = request.form.get('destino_documento', '')
    destino_regiao               = request.form.get('destino_regiao', '').upper()
    destino_produtor            = request.form.get('destino_produtor', '').upper()
    destino_propriedade         = request.form.get('destino_propriedade', '').upper()
    destino_codigo_mapa         = request.form.get('destino_codigo_mapa', '').upper()
    destino_insc_estadual       = request.form.get('destino_insc_estadual', '').upper()
    destino_municipio           = request.form.get('destino_municipio', '').upper()
    # Codigo do Municipio (Sessao 034 cont. 4) - mesma logica do
    # lado Procedencia, ver comentario acima.
    destino_municipio_codigo    = request.form.get('destino_municipio_codigo', '')
    destino_uf                  = request.form.get('destino_uf', '').upper()

    # Codigo de Autenticidade - guardado em silencio, nao aparece
    # na tela, ninguem digita manualmente (vem preenchido pela
    # leitura automatica quando a GTA foi lida por upload). Codigo
    # de Barras IAGRO REMOVIDO nesta versao (Sessao 029) - decisao
    # de Benedito: o Codigo de Autenticidade sozinho ja basta.
    codigo_autenticidade   = request.form.get('codigo_autenticidade', '')

    # Resguardo documental do PDF (Sessao 029) - preenchidos em
    # silencio pela rota ler(), reaproveitados aqui se o usuario
    # salvar logo em seguida sem sair da tela.
    arquivo_pdf_caminho    = request.form.get('arquivo_pdf_caminho', '')
    arquivo_pdf_hash       = request.form.get('arquivo_pdf_hash', '')

    # -----------------------------------------------------
    # Trava do botao Salvar (Sessao 027) - 4 checks de confirmacao,
    # um por Quadro. Servidor e a fonte da verdade: revalida mesmo
    # que o JavaScript ja tenha travado o botao no navegador.
    # -----------------------------------------------------
    confirma_documento    = request.form.get('confirma_documento') == 'on'
    confirma_procedencia  = request.form.get('confirma_procedencia') == 'on'
    confirma_destino      = request.form.get('confirma_destino') == 'on'
    confirma_animais      = request.form.get('confirma_animais') == 'on'

    animais, resumo_animais = _ler_animais_do_formulario()

    # Numero completo calculado no servidor, mesmo sem aparecer na
    # tela - continua disponivel para uso futuro (busca/duplicidade).
    numero_gta_completo = f'{uf_gta}{serie_gta}{numero_gta_sequencial}'

    # -----------------------------------------------------
    # Validacao de tamanho maximo (servidor = fonte da verdade),
    # batendo com o tamanho real de cada coluna em tb_4001_gta
    # (ou tamanho razoavel para os campos novos, ainda nao
    # persistidos em tabela propria).
    # -----------------------------------------------------
    LIMITES_TAMANHO = {
        'UF da GTA':                     (uf_gta, 2),
        'Serie da GTA':                  (serie_gta, 5),
        'Numero':                        (numero_gta_sequencial, 15),
        'Data de Entrega':               (data_entrega_str, 10),
        'Meio de Transporte':            (meio_transporte, 30),
        'CPF/CNPJ Procedencia':          (procedencia_documento, 18),
        'Regiao Procedencia':            (procedencia_regiao, 50),
        'Nome/Razao Social Procedencia': (procedencia_nome, 150),
        'Estabelecimento Procedencia':   (procedencia_propriedade, 150),
        'Codigo MAPA Procedencia':       (procedencia_codigo_mapa, 30),
        'Insc. Estadual Procedencia':    (procedencia_insc_estadual, 30),
        'Municipio Procedencia':         (procedencia_municipio, 100),
        'Codigo Municipio Procedencia':  (procedencia_municipio_codigo, 10),
        'UF Procedencia':                (procedencia_uf, 2),
        'CPF/CNPJ Destino':              (destino_documento, 18),
        'Regiao Destino':                (destino_regiao, 50),
        'Produtor Destino':              (destino_produtor, 150),
        'Estabelecimento Destino':       (destino_propriedade, 150),
        'Codigo MAPA Destino':           (destino_codigo_mapa, 30),
        'Insc. Estadual Destino':        (destino_insc_estadual, 30),
        'Municipio Destino':             (destino_municipio, 100),
        'Codigo Municipio Destino':      (destino_municipio_codigo, 10),
        'UF Destino':                    (destino_uf, 2),
    }

    erro_validacao = None

    for nome_campo, (valor, limite) in LIMITES_TAMANHO.items():
        if valor and len(valor) > limite:
            erro_validacao = f'Campo "{nome_campo}" excede o limite de {limite} caracteres (digitado: {len(valor)}).'
            break

    # -----------------------------------------------------
    # Validacao de obrigatoriedade
    # -----------------------------------------------------
    if not erro_validacao and not uf_gta:
        erro_validacao = 'UF da GTA e obrigatoria!'

    if not erro_validacao and not serie_gta:
        erro_validacao = 'Serie da GTA e obrigatoria!'

    if not erro_validacao and not numero_gta_sequencial:
        erro_validacao = 'Numero da GTA e obrigatorio!'

    # -----------------------------------------------------
    # v2.8.0 - GTA DUPLICADA: ja existe uma GTA identica (UF + Serie +
    # Numero, sentido ENTRADA) neste Produtor? Avisa e IMPEDE - antes
    # do bloco de teste abaixo, para uma GTA repetida nao criar Parceiro.
    # -----------------------------------------------------
    if not erro_validacao and session.get('id_produtor'):
        with get_db_produtor(session.get('id_produtor')) as db:
            gta_existente = buscar_gta_duplicada(db, uf_gta, serie_gta, numero_gta_sequencial, SENTIDO_FIXO)
            if gta_existente:
                erro_validacao = mensagem_gta_duplicada(gta_existente)

    if not erro_validacao and not meio_transporte:
        erro_validacao = 'Meio de Transporte e obrigatorio (transcreva exatamente como esta impresso na GTA)!'

    # -----------------------------------------------------
    # Datas de Emissao/Validade/Entrega: texto livre (dd/mm/aaaa),
    # como esta escrito na GTA - nao usa <input type="date"> do
    # navegador (decisao de Benedito; Entrega passou a seguir o
    # mesmo padrao a partir da Sessao 034, continuacao). Validamos
    # o formato no servidor mesmo assim, fonte da verdade.
    # -----------------------------------------------------
    data_emissao  = None
    data_validade = None
    data_entrega  = None

    if not erro_validacao:
        if not data_emissao_str:
            erro_validacao = 'Data de Emissao e obrigatoria!'
        else:
            try:
                data_emissao = datetime.strptime(data_emissao_str, '%d/%m/%Y').date()
            except ValueError:
                erro_validacao = 'Data de Emissao incorreta! Use o formato dd/mm/aaaa.'

    if not erro_validacao:
        if not data_validade_str:
            erro_validacao = 'Data de Validade e obrigatoria!'
        else:
            try:
                data_validade = datetime.strptime(data_validade_str, '%d/%m/%Y').date()
            except ValueError:
                erro_validacao = 'Data de Validade incorreta! Use o formato dd/mm/aaaa.'

    if not erro_validacao and data_emissao and data_validade and data_validade < data_emissao:
        erro_validacao = 'Data de Validade nao pode ser anterior a Data de Emissao!'

    # -----------------------------------------------------
    # Data de Entrega (Sessao 027, formato alterado na v2.3.0 -
    # Sessao 034 continuacao): texto livre dd/mm/aaaa, igual
    # Emissao/Validade. Continua OBRIGATORIA e SEM valor padrao
    # "hoje" - e continua sem vir preenchida mesmo apos a leitura
    # automatica (ver DESCRICAO no topo do arquivo) - e a UNICA
    # decisao real do usuario nesta tela.
    # -----------------------------------------------------
    if not erro_validacao:
        if not data_entrega_str:
            erro_validacao = 'Data de Entrega e obrigatoria!'
        else:
            try:
                data_entrega = datetime.strptime(data_entrega_str, '%d/%m/%Y').date()
            except ValueError:
                erro_validacao = 'Data de Entrega incorreta! Use o formato dd/mm/aaaa.'

    # -----------------------------------------------------
    # Janela permitida para a Data de Entrega (Sessao 027):
    #   - Normal:   Emissao <= Entrega <= Validade
    #   - Comitiva: Emissao <= Entrega <= Validade + 30 dias
    #     (aciona quando o texto transcrito em Meio de Transporte
    #     for exatamente "COMITIVA" - regra do MAPA para
    #     transporte conduzido a pe).
    # So roda se todas as tres datas + o texto ja passaram nas
    # validacoes de formato/obrigatoriedade acima.
    # -----------------------------------------------------
    if not erro_validacao and data_emissao and data_validade and data_entrega:
        eh_comitiva = (meio_transporte == MEIO_TRANSPORTE_COMITIVA)
        limite_superior = data_validade + timedelta(days=TOLERANCIA_COMITIVA_DIAS) if eh_comitiva else data_validade

        if data_entrega < data_emissao:
            erro_validacao = 'Data de Entrega nao pode ser anterior a Data de Emissao!'
        elif data_entrega > limite_superior:
            if eh_comitiva:
                erro_validacao = (
                    f'Data de Entrega alem do limite de tolerancia para Comitiva '
                    f'(ate 30 dias apos a Validade, {limite_superior.strftime("%d/%m/%Y")})!'
                )
            else:
                erro_validacao = (
                    f'Data de Entrega deve estar entre a Emissao ({data_emissao.strftime("%d/%m/%Y")}) '
                    f'e a Validade ({data_validade.strftime("%d/%m/%Y")})! '
                    f'Se o transporte foi por Comitiva, confira a transcricao do campo Meio de Transporte.'
                )

    if not erro_validacao and not procedencia_documento:
        erro_validacao = 'CPF/CNPJ da Procedencia e obrigatorio!'

    if not erro_validacao and not procedencia_nome:
        erro_validacao = 'Nome/Razao Social da Procedencia e obrigatorio!'

    if not erro_validacao and not destino_propriedade:
        erro_validacao = 'Estabelecimento (Propriedade) de Destino e obrigatorio!'

    if not erro_validacao and (not animais or resumo_animais['total'] <= 0):
        erro_validacao = 'Informe ao menos uma categoria de Animais, com quantidade maior que zero!'

    # -----------------------------------------------------
    # Trava do botao Salvar (Sessao 027) - revalidacao no servidor
    # dos 4 checks de confirmacao (Documento, Procedencia, Destino,
    # Animais). Verificada por ultimo, de proposito: se ja existe
    # um erro de campo, o usuario corrige primeiro; se os campos
    # estao todos certos mas algum check nao veio marcado, e essa
    # mensagem que aparece.
    # -----------------------------------------------------
    if not erro_validacao and not (confirma_documento and confirma_procedencia and confirma_destino and confirma_animais):
        erro_validacao = 'Confirme a conferencia de todos os Quadros (Documento, Procedencia, Destino e Animais) antes de salvar!'

    # -----------------------------------------------------
    # BLOCO DE TESTE - resolver_parceiro() (v2.6.0, Sessao 034
    # cont. 5). So roda quando toda a validacao acima passou
    # (mesmo ponto onde captura_confirmada vira True). Usa
    # get_db_produtor() (backend/utils/multitenant.py) para abrir
    # a sessao ja dentro do schema correto do Produtor logado -
    # tb_parceiros vive no schema dele (produtor_NNNNN), nao no
    # schema public (ver changelog v2.6.0 para o erro real que
    # revelou isso). COMMIT REAL - decisao de Benedito nesta
    # sessao: testar a rotina completa contra o banco de verdade;
    # limpeza de dados de teste (se precisar repetir) e MANUAL via
    # pgAdmin, nao ha rollback automatico aqui. Resultado tambem
    # aparece no terminal do Waitress via print(), para
    # conferencia imediata sem precisar abrir o pgAdmin toda vez.
    #
    # v2.7.0: adicionado regiao=procedencia_regiao - campo ja
    # capturado do formulario desde sempre, mas nunca tinha sido
    # repassado aqui (bug real encontrado ao testar a tela de
    # consulta de Parceiros/Fornecedores - ver changelog v2.7.0
    # no topo do arquivo).
    # -----------------------------------------------------
    if erro_validacao is None:
        with get_db_produtor(session.get('id_produtor')) as db:
            resultado_teste = resolver_parceiro(
                db,
                session.get('usuario_id'),
                cpf_cnpj=procedencia_documento,
                nome=procedencia_nome,
                estabelecimento=procedencia_propriedade,
                insc_estadual=procedencia_insc_estadual,
                municipio_codigo=procedencia_municipio_codigo,
                municipio_nome=procedencia_municipio,
                codigo_mapa=procedencia_codigo_mapa,
                uf=procedencia_uf,
                regiao=procedencia_regiao,
            )
            db.commit()
            print('=== TESTE resolver_parceiro() - COMMIT REAL, GRAVADO NO BANCO ===')
            print(resultado_teste)
            print('===================================================================')

    # -----------------------------------------------------
    # Reconstroi um objeto com os dados ja digitados, para o
    # formulario reaparecer preenchido - nao perde o trabalho,
    # mesmo caminho ja usado em propriedades.py. Os 4 checks
    # tambem sao preservados - se o erro foi em outro Quadro, o
    # usuario nao precisa marcar de novo o que ja tinha marcado.
    # -----------------------------------------------------
    gta_tentativa = SimpleNamespace(
        uf_gta                     = uf_gta,
        serie_gta                  = serie_gta,
        numero_gta_sequencial      = numero_gta_sequencial,
        numero_gta_completo        = numero_gta_completo,
        data_emissao               = data_emissao_str,
        data_validade               = data_validade_str,
        data_entrega                = data_entrega_str,
        meio_transporte             = meio_transporte,
        procedencia_documento       = procedencia_documento,
        procedencia_regiao          = procedencia_regiao,
        procedencia_nome            = procedencia_nome,
        procedencia_propriedade     = procedencia_propriedade,
        procedencia_codigo_mapa     = procedencia_codigo_mapa,
        procedencia_insc_estadual   = procedencia_insc_estadual,
        procedencia_municipio       = procedencia_municipio,
        procedencia_municipio_codigo = procedencia_municipio_codigo,
        procedencia_uf              = procedencia_uf,
        destino_documento           = destino_documento,
        destino_regiao              = destino_regiao,
        destino_produtor            = destino_produtor,
        destino_propriedade         = destino_propriedade,
        destino_codigo_mapa         = destino_codigo_mapa,
        destino_insc_estadual       = destino_insc_estadual,
        destino_municipio           = destino_municipio,
        destino_municipio_codigo    = destino_municipio_codigo,
        destino_uf                  = destino_uf,
        codigo_autenticidade        = codigo_autenticidade,
        arquivo_pdf_caminho         = arquivo_pdf_caminho,
        arquivo_pdf_hash            = arquivo_pdf_hash,
        confirma_documento          = confirma_documento,
        confirma_procedencia        = confirma_procedencia,
        confirma_destino            = confirma_destino,
        confirma_animais            = confirma_animais
    )

    return render_template('produtor/gta_compra_cadastro.html',
        gta                  = gta_tentativa,
        animais              = animais,
        resumo_animais       = resumo_animais,
        captura_confirmada   = (erro_validacao is None),
        erro                 = erro_validacao,
        usuario_nome         = session.get('usuario_nome'),
        usuario_perfil       = session.get('usuario_perfil'),
        cor_primaria         = session.get('cor_primaria', '#D4370A'),
        nome_sistema         = session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo           = 'entrada'
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\gta_compra.py
# =========================================================