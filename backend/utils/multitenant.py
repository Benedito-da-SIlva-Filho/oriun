# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\multitenant.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-16 13:20 -03
# ATUALIZADO EM: 2026-07-17 11:40 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Mecanismo central do modelo Schema-por-Produtor
#     (multi-tenant). Cada Produtor tem seu proprio schema
#     dentro do banco Postgres "orion" (ex.: produtor_00042),
#     onde ficam as tabelas de movimento (GTA, Brincagem,
#     Parceiros, e futuramente Animal/Comunicado). Os dados
#     compartilhados (Certificadora, Produtor, Propriedade,
#     Protocolo) continuam no schema publico (public).
#
#     Analogia de referencia (usada nas conversas da Sessao
#     018 - ver Diario de Bordo): o banco e um predio, o
#     schema public e o terreo (cadastros basicos), e cada
#     Produtor mora em um andar proprio (seu schema). Esta
#     funcao e o "porteiro" que, depois do usuario ja estar
#     autenticado (login/senha - mecanismo separado, nao tem
#     relacao com isto aqui), descobre em qual andar ele mora
#     e leva a conexao do banco ate la.
#
#     Uso tipico dentro de uma rota:
#
#         from backend.utils.multitenant import get_db_produtor
#
#         @app.route('/gtas')
#         def listar_gtas():
#             id_produtor = session['id_produtor']
#             with get_db_produtor(id_produtor) as db:
#                 gtas = db.query(Gta).all()
#                 ...
#
#     Depois do "with", toda consulta feita em "db" ja busca
#     automaticamente dentro do schema daquele Produtor - nao
#     precisa (e nao deve) filtrar por id_produtor no WHERE,
#     porque o isolamento e fisico (schema), nao logico.
#
#     v1.0.0: Criacao do modulo (Sessao 018). Cobre apenas o
#             caso de um Produtor por vez. Visao consolidada
#             de Certificadora (varios Produtores ao mesmo
#             tempo) fica para quando o modelo da Certificadora
#             for desenhado (pendente - aguardando levantamento
#             da Geane sobre o sistema Maker).
#     v1.1.0: Sessao 019 - Adicionada checagem de produtor.ativo
#             e a excecao ProdutorInativo. Regra de negocio
#             (Benedito, Sessao 019): "Inativar" um Produtor
#             NUNCA apaga dados - o schema e as tabelas
#             permanecem intactos, a Consiste continua com
#             acesso livre para consulta. O que muda e que
#             nenhuma ESCRITA deve ser aceita enquanto o
#             Produtor estiver inativo. Como get_db_produtor()
#             e o unico ponto central por onde toda rota do
#             modulo Animais/Entrada vai passar (presente ou
#             futura), a checagem aqui garante a trava "de
#             graca" em qualquer rota nova, sem precisar
#             lembrar de repetir a checagem em cada uma.
#             Checagem de ativo colocada ANTES da checagem de
#             schema_nome/migracao - um Produtor inativo deve
#             ser barrado independente do estado de migracao
#             dele.
# =========================================================

import re
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models.produtor import Produtor


# -------------------------------------------------------
# Padrao valido de nome de schema: produtor_ + 5 digitos.
# Ex.: produtor_00042
# Usado como trava de seguranca antes de colocar o valor
# dentro de um comando SQL (SET search_path). Nao tem
# relacao com senha/autenticacao - e so uma checagem de
# formato, para pegar dado corrompido ou erro de digitacao
# antes que ele vire comando no banco.
# -------------------------------------------------------
PADRAO_SCHEMA_NOME = re.compile(r'^produtor_\d{5}$')


class ProdutorNaoEncontrado(Exception):
    """Levantada quando o id_produtor informado nao existe na tabela produtores."""
    pass


class ProdutorInativo(Exception):
    """Levantada quando o Produtor existe mas esta com ativo=False.
    Nao indica ausencia de dados - o schema e as tabelas continuam
    intactos, so o acesso operacional (escrita) esta suspenso."""
    pass


class ProdutorNaoMigrado(Exception):
    """Levantada quando o Produtor existe mas ainda nao tem schema_nome
    preenchido (nao passou pela rotina de onboarding multi-tenant)."""
    pass


class SchemaNomeInvalido(Exception):
    """Levantada quando o schema_nome gravado no banco nao bate com o
    padrao esperado (produtor_ + 5 digitos). Protecao contra dado
    corrompido antes de usar o valor em um comando SQL."""
    pass


@contextmanager
def get_db_produtor(id_produtor: int):
    """
    Abre uma sessao de banco ja posicionada dentro do schema do
    Produtor informado.

    Passo a passo:
      1. Abre uma sessao normal (schema public, onde fica a tabela
         produtores).
      2. Busca o Produtor pelo id e le o schema_nome dele.
      3. Confere se o Produtor existe, se esta ativo, se ja foi
         migrado (schema_nome preenchido) e se o valor tem o formato
         esperado.
      4. Executa "SET search_path" para essa sessao, fazendo com que
         toda consulta seguinte procure primeiro no schema do Produtor
         e, se nao achar, no schema public (para as tabelas
         compartilhadas, como Propriedade).
      5. Entrega a sessao pronta para uso dentro do "with".

    Parametros:
        id_produtor: id (PK) do Produtor, normalmente vindo de
                     session['id_produtor'] apos o login.

    Levanta:
        ProdutorNaoEncontrado: id_produtor nao existe na tabela.
        ProdutorInativo: Produtor existe mas esta com ativo=False -
                         acesso operacional suspenso (dados preservados).
        ProdutorNaoMigrado: Produtor existe mas schema_nome esta NULL.
        SchemaNomeInvalido: schema_nome nao bate com o padrao esperado.
    """
    with Session(engine) as db:
        produtor = db.get(Produtor, id_produtor)

        if produtor is None:
            raise ProdutorNaoEncontrado(
                f'Produtor com id={id_produtor} nao encontrado na tabela produtores.'
            )

        if not produtor.ativo:
            raise ProdutorInativo(
                f'Produtor id={id_produtor} ({produtor.nome}) esta inativo. '
                f'Os dados permanecem preservados, mas nenhuma operacao de '
                f'escrita e permitida ate a reativacao.'
            )

        if not produtor.schema_nome:
            raise ProdutorNaoMigrado(
                f'Produtor id={id_produtor} ({produtor.nome}) ainda nao foi '
                f'migrado para o modelo multi-tenant (schema_nome esta vazio).'
            )

        if not PADRAO_SCHEMA_NOME.match(produtor.schema_nome):
            raise SchemaNomeInvalido(
                f'schema_nome "{produtor.schema_nome}" do Produtor id={id_produtor} '
                f'nao bate com o padrao esperado (produtor_NNNNN).'
            )

        # SET search_path afeta apenas esta sessao/conexao. Nao usamos
        # parametro (:nome) aqui porque SET search_path nao aceita bind
        # de parametro para nome de schema - por isso a checagem de
        # formato acima e obrigatoria antes desta linha.
        db.execute(text(f'SET search_path TO {produtor.schema_nome}, public'))

        yield db


def gerar_schema_nome(id_produtor: int) -> str:
    """
    Gera o nome de schema padrao para um Produtor, a partir da PK.
    Usado apenas pela rotina de onboarding (proximo passo) - nunca
    deve ser chamado para "adivinhar" o schema de um Produtor ja
    existente, sempre ler o valor gravado em produtor.schema_nome.

    Ex.: gerar_schema_nome(42) -> "produtor_00042"
    """
    return f'produtor_{id_produtor:05d}'

# =========================================================
# FIM DE ARQUIVO: backend\utils\multitenant.py
# =========================================================