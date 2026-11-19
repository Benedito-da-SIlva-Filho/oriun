# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\servicos
# MODULO: backend\servicos\resolver_parceiro.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-08-10 16:50 -03
# ATUALIZADO EM: 2026-11-12 19:00 -03
# VERSAO: 1.1.0
# v1.1.0: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras do CNPJ mantidas na limpeza e na formatacao. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Funcao central de resolucao de Parceiro (Procedencia de
#     GTA), compartilhada entre o Fluxo Automatico (gta_compra.py,
#     leitura de e-GTA em PDF) e o futuro Fluxo Manual de GTA.
#     Desenho fechado com Benedito na Sessao 034 continuacao 4,
#     em cima da estrutura real ja existente (tb_parceiros +
#     tb_parceiros_propriedades + tb_log_conferencia_parceiro,
#     todas criadas na Sessao 16/17 - NAO recria nada).
#
#     REGRA DE NEGOCIO (decisao final de Benedito - "criamos um
#     monstro que so existiu para nos"): o sistema NUNCA edita ou
#     sobrescreve um cadastro ja existente. Ele so faz duas
#     coisas - usa o que ja existe, ou cria um registro novo.
#     Nao ha pergunta condicional para o usuario dentro desta
#     funcao; a decisao de "Confirmo/Nao confirmo" na tela
#     acontece DEPOIS que esta funcao ja resolveu (ou criou) o
#     registro - ela so mostra o resultado para conferencia.
#
#     CASCATA DE BUSCA (do mais forte para o mais fraco):
#       1) cpf_cnpj          - identifica o Parceiro em si.
#       2) insc_estadual     - identifica a Propriedade dele.
#       3) municipio_codigo  - reforca a identificacao.
#       4) codigo_mapa       - reforca ainda mais (nem toda
#                              Propriedade tem, so ERAS/SISBOV).
#       O Nome da Propriedade (estabelecimento) NAO entra na
#       cascata como criterio de match - e texto livre, sujeito
#       a abreviacao do orgao emissor a cada GTA. Serve so para
#       exibicao/conferencia humana.
#
#     RESULTADOS POSSIVEIS:
#       - CPF/CNPJ nao encontrado em tb_parceiros:
#           tipo_situacao   = SEM_MATCH
#           decisao_tomada  = CRIOU_NOVO_PARCEIRO
#           Cria o Parceiro E a primeira ParceiroPropriedades
#           juntos, na mesma operacao (nunca existe Parceiro sem
#           pelo menos 1 Propriedade vinculada).
#       - CPF/CNPJ encontrado, e existe uma Propriedade dele que
#         bate em TODOS os criterios informados (insc_estadual,
#         municipio_codigo, codigo_mapa - os que vierem
#         preenchidos; campos vazios nao entram na comparacao):
#           tipo_situacao   = MATCH_PERFEITO
#           decisao_tomada  = CONFIRMOU_EXISTENTE
#           Usa o registro ja existente, sem criar nada.
#       - CPF/CNPJ encontrado, mas NENHUMA Propriedade dele bate
#         em todos os criterios informados:
#           tipo_situacao   = DIVERGENCIA
#           decisao_tomada  = CRIOU_NOVA_PROPRIEDADE
#           Cria uma nova ParceiroPropriedades vinculada ao
#           Parceiro ja existente - NUNCA edita as Propriedades
#           que ja estavam la.
#
#     LOG (tb_log_conferencia_parceiro): gravado SEMPRE, nas 3
#     situacoes acima, inclusive quando o resultado e usar um
#     registro que ja existia (MATCH_PERFEITO) - regra mais
#     restritiva do que o lado Destino/Propriedade (que so loga
#     em caso de ambiguidade real, ver tb_log_conferencia_
#     propriedade). Motivo de negocio: divergencia so pode
#     acontecer do lado Procedencia/Fornecedor (dado externo, nao
#     confiavel), nunca do lado Destino (e sempre o proprio
#     cliente/Produtor logado).
#
#     TRANSACAO: esta funcao NAO abre nem fecha sessao de banco
#     propria - recebe a sessao (db) ja aberta por quem chamou
#     (o router), e so faz db.add(...)/db.flush(...) dentro dela.
#     Quem chamou e responsavel pelo db.commit() final. Isso
#     garante que, se o restante do salvamento da GTA falhar
#     depois, o Parceiro/Propriedade criados aqui sejam desfeitos
#     junto (mesma transacao) - decisao tecnica confirmada com
#     Benedito na Sessao 034 cont. 4.
#
#     v1.0.0: Criacao do modulo (Sessao 034 continuacao 4).
#         Primeira versao - cobre o caso de uso de Procedencia
#         (Fluxo Automatico, chamada futura a partir de
#         gta_compra.py/salvar()). O Fluxo Manual de GTA ainda
#         nao existe como tela - quando for construido, deve
#         chamar esta MESMA funcao, nao duplicar a logica.
# =========================================================

import re

from backend.models.tb_parceiros import Parceiro
from backend.models.tb_parceiros_propriedades import ParceiroPropriedades
from backend.models.tb_log_conferencia_parceiro import LogConferenciaParceiro


# -------------------------------------------------------
# Valores fechados de tipo_situacao / decisao_tomada usados por
# esta funcao - mantidos como constantes para nao espalhar
# strings soltas pelo codigo (e para o router/tela poderem
# comparar o resultado sem risco de erro de digitacao).
# -------------------------------------------------------
SITUACAO_MATCH_PERFEITO = 'MATCH_PERFEITO'
SITUACAO_SEM_MATCH      = 'SEM_MATCH'
SITUACAO_DIVERGENCIA    = 'DIVERGENCIA'

DECISAO_CONFIRMOU_EXISTENTE   = 'CONFIRMOU_EXISTENTE'
DECISAO_CRIOU_NOVO_PARCEIRO   = 'CRIOU_NOVO_PARCEIRO'
DECISAO_CRIOU_NOVA_PROPRIEDADE = 'CRIOU_NOVA_PROPRIEDADE'


def _normalizar_documento(documento):
    """Remove pontuacao do CPF/CNPJ, deixando so digitos - mesmo
    criterio ja usado em backend/routers/busca_cpf_cnpj.py, para
    a busca funcionar independente de como o dado chegou (com ou
    sem mascara)."""
    return re.sub(r'[^0-9A-Za-z]', '', documento or '').upper()   # CNPJ alfanumerico: mantem letras


def _buscar_propriedade_correspondente(db, id_parceiro, insc_estadual, municipio_codigo, codigo_mapa):
    """Procura, entre as Propriedades ja vinculadas a este
    Parceiro, uma que bata em TODOS os criterios informados
    (insc_estadual, municipio_codigo, codigo_mapa). Campos vazios
    ('' ou None) NAO entram na comparacao - um criterio ausente
    no documento lido nao pode, sozinho, impedir um match que os
    outros criterios ja confirmam. Devolve o registro
    ParceiroPropriedades encontrado, ou None se nenhuma bater em
    tudo que foi informado."""
    query = db.query(ParceiroPropriedades).filter(
        ParceiroPropriedades.id_parceiro == id_parceiro
    )

    if insc_estadual:
        query = query.filter(ParceiroPropriedades.insc_estadual == insc_estadual)
    if municipio_codigo:
        query = query.filter(ParceiroPropriedades.municipio_codigo == municipio_codigo)
    if codigo_mapa:
        query = query.filter(ParceiroPropriedades.codigo_mapa == codigo_mapa)

    return query.first()


def resolver_parceiro(
    db,
    id_usuario,
    cpf_cnpj,
    nome,
    estabelecimento,
    insc_estadual='',
    municipio_codigo='',
    municipio_nome='',
    codigo_mapa='',
    uf='',
    regiao='',
):
    """
    Resolve a Procedencia de uma GTA contra tb_parceiros +
    tb_parceiros_propriedades, criando o que for necessario e
    registrando a decisao em tb_log_conferencia_parceiro. Ver
    DESCRICAO no topo do arquivo para a regra completa.

    Parametros:
        db                - sessao de banco JA ABERTA pelo
                             chamador (nao abre/fecha sessao
                             propria - ver DESCRICAO, secao
                             TRANSACAO).
        id_usuario         - usuario logado, para o log (nunca
                             fica em branco - toda decisao tem um
                             responsavel humano).
        cpf_cnpj            - documento da Procedencia, com ou sem
                             mascara (normalizado aqui dentro).
        nome                - Nome/Razao Social - so gravado se for
                             preciso CRIAR um Parceiro novo; nunca
                             usado como criterio de busca.
        estabelecimento     - nome da Propriedade - mesma regra do
                             campo nome acima (so grava em criacao,
                             nunca e criterio de match).
        insc_estadual       - opcional, 2o nivel da cascata.
        municipio_codigo    - opcional, 3o nivel da cascata.
        municipio_nome      - opcional, so gravado em criacao.
        codigo_mapa         - opcional, 4o nivel da cascata.
        uf, regiao          - opcionais, so gravados em criacao.

    Devolve um dict:
        {
            'id_parceiro':             int,
            'id_parceiro_propriedade': int,
            'tipo_situacao':           str (uma das constantes SITUACAO_*),
            'decisao_tomada':          str (uma das constantes DECISAO_*),
        }
    """
    cpf_cnpj_limpo = _normalizar_documento(cpf_cnpj)

    parceiro = db.query(Parceiro).filter_by(cpf_cnpj=cpf_cnpj_limpo).first()

    # ---------------------------------------------------
    # CASO 1 - Parceiro nao existe: cria Parceiro + primeira
    # Propriedade juntos, na mesma operacao.
    # ---------------------------------------------------
    if parceiro is None:
        parceiro = Parceiro(
            cpf_cnpj=cpf_cnpj_limpo,
            nome=nome,
            ativo=True,
        )
        db.add(parceiro)
        db.flush()  # garante parceiro.id preenchido, sem precisar commit

        propriedade = ParceiroPropriedades(
            id_parceiro=parceiro.id,
            estabelecimento=estabelecimento,
            codigo_mapa=codigo_mapa or None,
            insc_estadual=insc_estadual or None,
            municipio_codigo=municipio_codigo or None,
            municipio_nome=municipio_nome or None,
            uf=uf or None,
            regiao=regiao or None,
            ativo=True,
        )
        db.add(propriedade)
        db.flush()

        tipo_situacao  = SITUACAO_SEM_MATCH
        decisao_tomada = DECISAO_CRIOU_NOVO_PARCEIRO

    else:
        propriedade = _buscar_propriedade_correspondente(
            db, parceiro.id, insc_estadual, municipio_codigo, codigo_mapa
        )

        # -----------------------------------------------
        # CASO 2 - Parceiro existe e uma Propriedade dele bate
        # em tudo que foi informado: usa o que ja existe, NAO
        # cria nem edita nada.
        # -----------------------------------------------
        if propriedade is not None:
            tipo_situacao  = SITUACAO_MATCH_PERFEITO
            decisao_tomada = DECISAO_CONFIRMOU_EXISTENTE

        # -----------------------------------------------
        # CASO 3 - Parceiro existe, mas nenhuma Propriedade dele
        # bate em tudo: cria uma NOVA Propriedade vinculada a
        # este Parceiro - o cadastro antigo NUNCA e alterado.
        # -----------------------------------------------
        else:
            propriedade = ParceiroPropriedades(
                id_parceiro=parceiro.id,
                estabelecimento=estabelecimento,
                codigo_mapa=codigo_mapa or None,
                insc_estadual=insc_estadual or None,
                municipio_codigo=municipio_codigo or None,
                municipio_nome=municipio_nome or None,
                uf=uf or None,
                regiao=regiao or None,
                ativo=True,
            )
            db.add(propriedade)
            db.flush()

            tipo_situacao  = SITUACAO_DIVERGENCIA
            decisao_tomada = DECISAO_CRIOU_NOVA_PROPRIEDADE

    # ---------------------------------------------------
    # Log gravado SEMPRE, nas 3 situacoes (inclusive Match
    # Perfeito) - regra restritiva do lado Parceiro/Procedencia,
    # ver DESCRICAO no topo do arquivo.
    # ---------------------------------------------------
    log = LogConferenciaParceiro(
        id_usuario=id_usuario,
        id_parceiro=parceiro.id,
        id_parceiro_propriedade=propriedade.id,
        tipo_situacao=tipo_situacao,
        decisao_tomada=decisao_tomada,
    )
    db.add(log)
    db.flush()

    return {
        'id_parceiro': parceiro.id,
        'id_parceiro_propriedade': propriedade.id,
        'tipo_situacao': tipo_situacao,
        'decisao_tomada': decisao_tomada,
    }

# =========================================================
# FIM DE ARQUIVO: backend\servicos\resolver_parceiro.py
# =========================================================