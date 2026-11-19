# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\backup_helper.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-04 16:30
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.17.0
# v1.17.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Motor generico do mecanismo de Backup/Restore de Schema
#     inteiro (Sessao 046). Chama os executaveis REAIS do
#     PostgreSQL (pg_dump/pg_restore) via subprocess.
#
#     VERSIONAMENTO DE SCHEMA (NOVO v1.3.0, Sessao 049, 10/09/2026,
#     17:30 -03): decisao de Benedito apos um Restore real trazer
#     de volta uma estrutura de banco anterior a mudancas de
#     ALTER TABLE ja aplicadas - o codigo Python continuava
#     esperando colunas que o backup restaurado nao tinha,
#     quebrando em produção sem aviso nenhum. Quem aciona o
#     Restore de verdade e SEMPRE a Consiste (nunca o Produtor -
#     ele so grava um pedido, ver backup_restore.py); mesmo assim,
#     "a Consiste vai lembrar sempre de checar scripts pendentes"
#     e uma aposta arriscada demais para um mecanismo usado com
#     frequencia. Solucao: cada Produtor tem uma tabela
#     tb_versao_schema (1 linha, dentro do proprio schema-por-
#     Produtor) com um numero de versao. Toda vez que a Consiste
#     entrega um pacote de ALTER TABLE, o mesmo script incrementa
#     essa versao em todos os schemas (bloco DO $$, mesmo padrao
#     de sempre) - e a constante VERSAO_SCHEMA_ATUAL aqui no
#     codigo sobe junto, no mesmo commit/entrega.
#
#     criar_backup() agora grava, ao lado do arquivo .dump, um
#     arquivo .meta (so um numero dentro) com a versao vigente no
#     momento do backup. executar_restore() le esse .meta do
#     backup escolhido e compara com VERSAO_SCHEMA_ATUAL - se
#     forem diferentes, levanta VersaoSchemaIncompativel em vez de
#     restaurar direto. O CHAMADOR (rota do Consiste) decide o que
#     fazer com isso: nunca bloqueia para sempre, mas exige uma
#     confirmacao explicita antes de seguir (ver backup_restore.py
#     v1.4.0) - nem trava a operacao legitima de restaurar um
#     backup antigo de proposito, nem deixa passar batido sem
#     ninguem perceber.
#
#     v1.0.0 a v1.2.0: ver historico no cabecalho anterior deste
#         arquivo (Sessao 046) - motor de backup/restore, exclusao
#         das tabelas de auditoria via lista de restauracao
#         filtrada.
#     v1.3.0: Sessao 049 (10/09/2026, 17:30 -03) - Versionamento
#         de schema (ver DESCRICAO acima). Nova excecao
#         VersaoSchemaIncompativel. Novas funcoes internas
#         _ler_versao_schema_atual() e _ler_versao_backup().
#         criar_backup() grava o arquivo .meta. listar_backups_
#         disponiveis() passa a incluir a versao de cada backup
#         (para exibicao em tela, se quiserem mostrar). executar_
#         restore() ganhou o parametro confirmar_versao_
#         incompativel (default False).
#     v1.4.0: Sessao 093 (10/10/2026, 14:30 -03) - (1) VERSAO_SCHEMA_ATUAL
#         sobe de 1 para 2 (coluna nova conferido_em em tb_blk_8002_eventos
#         e tabelas do blockchain; script Tabelas\14_alter_blk_conferido_
#         versao2.sql). Backup antigo (versao 1) passa a pedir confirmacao
#         no Restore. (2) As 3 tabelas do blockchain (tb_blk_8001, 8002 e
#         8003) entram em TABELAS_EXCLUIDAS_DO_BACKUP: o Restore NAO mexe
#         nelas. POR QUE (decisao de Benedito): o que ja foi enviado a
#         blockchain nao deve voltar no tempo num Restore.
#     v1.5.0: Sessao 098 (16/10/2026, 14:16 -03) - VERSAO_SCHEMA_ATUAL sobe de 2 para 3
#         (tabelas novas das Saidas/Abate: tb_2020_embarque, tb_2002_saida_animais e
#         tb_2011_com_saidas; script Tabelas\criar_tb_2020_2002_2011_s098.sql, que
#         tambem sobe tb_versao_schema para 3). Backup antigo (versao 2) passa a pedir
#         confirmacao no Restore. Nenhuma outra mudanca.
#     v1.6.0: Sessao 098 (16/10/2026, 19:55 -03) - VERSAO_SCHEMA_ATUAL sobe de 3 para 4 (coluna
#         elemento em tb_2020_embarque e tb_2002_saida_animais; script Tabelas\
#         alterar_tb_2020_2002_elemento_s098.sql, que tambem sobe tb_versao_schema para 4).
#         Backup de versao 3 passa a pedir confirmacao no Restore. Nenhuma outra mudanca.
#     v1.7.0: Sessao 104 (23/10/2026, 09:40 -03) - NOVA listar_backups_validos(): so os backups dentro da RETENCAO_DIAS (30 dias). A limpeza dos arquivos
#         antigos so roda ao fazer um backup novo, entao sem backup novo os vencidos continuavam na lista (decisao de Benedito: nao devem aparecer
#         nem ser escolhidos para restaurar). listar_backups_disponiveis() fica igual (a limpeza precisa ver todos). REVERSAO: .bak_antes_s104c.
#     v1.8.0: Sessao 107 (28/10/2026, 09:10 -03) - VERSAO_SCHEMA_ATUAL sobe de 4 para 5 (Transferencia: coluna id_propriedade_destino em
#         tb_2020_embarque e tb_2011_com_saidas; script Tabelas\alterar_tb_2020_2011_destino_transfer_s107.sql, que tambem sobe
#         tb_versao_schema para 5). Backup de versao 4 passa a pedir confirmacao no Restore. Nenhuma outra mudanca. REVERSAO: .bak_antes_s107.
#     v1.10.0: Sessao 114 (2026-11-04 11:20 -03) - VERSAO_SCHEMA_ATUAL = 7 (Pesos pacote 1).  REVERSAO: .bak_antes_s114_pesos.
#     v1.11.0: Sessao 115 (2026-11-05 11:13 -03) - VERSAO_SCHEMA_ATUAL = 8 (Alteracao de Posse pacote 1: POSSE nos CHECKs de tipo_saida, colunas motivo_posse e
#         justificativa_posse em tb_2011, valor POSSE no ENUM tipo_movimento_gta_enum).  REVERSAO: .bak_antes_s115_posse.
#     v1.14.0: Sessao 121 (2026-11-11 15:00 -03) - VERSAO_SCHEMA_ATUAL = 11 (Reidentificacao: tabela tb_4010, colunas novas em tb_6005/tb_6006, REIDENTI no CHECK de tipo_saida da tb_2002). REVERSAO: .bak_antes_s121_reidentificacao.
#     v1.13.0: Sessao 120 (2026-11-10 21:50 -03) - VERSAO_SCHEMA_ATUAL = 10 (Linkagem pacote 2: tabela tb_4009_linkagem). REVERSAO: .bak_antes_s120_pacote2.
#     v1.12.0: Sessao 120 (2026-11-10 18:40 -03) - VERSAO_SCHEMA_ATUAL = 9 (Linkagem RFID e Brinco pacote 1: tabela tb_4008_linkagem_inconformes).  REVERSAO: .bak_antes_s120_linkagem.
#     v1.15.0: Sessao 121 (2026-11-11 19:00 -03) - VERSAO_SCHEMA_ATUAL = 12 (Reidentificacao modelo pendentes: tb_6006 com id_pedido vazio, id_propriedade, data_reidentificacao, id_usuario). REVERSAO: .bak_antes_s121_pendentes.
#     v1.16.0: Sessao 122 (2026-11-12 13:55 -03) - Auditoria Etapa 1: executar_restore so aceita nome de arquivo simples e que conste na lista de backups do Produtor (fecha caminho com ..). REVERSAO: .bak_antes_s122_etapa1.
# =========================================================

import os
import re
import subprocess
import psycopg2
from datetime import datetime, timedelta

from backend.database import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS


# -------------------------------------------------------
# Configuracao - ambos os caminhos vem do .env.
# -------------------------------------------------------
PG_BIN_DIR = os.getenv('PG_BIN_DIR', r'C:\Program Files\PostgreSQL\16\bin')
BACKUP_DIR = os.getenv('BACKUP_DIR', r'C:\Orion\XX Orion\backup')

CAMINHO_PG_DUMP    = os.path.join(PG_BIN_DIR, 'pg_dump.exe')
CAMINHO_PG_RESTORE = os.path.join(PG_BIN_DIR, 'pg_restore.exe')

RETENCAO_DIAS = 30

# -------------------------------------------------------
# NOVO v1.3.0 - versao ATUAL da estrutura de banco esperada pelo
# codigo. Incrementar aqui SEMPRE junto com um script de ALTER
# TABLE novo que atualize tb_versao_schema em todos os schemas
# (ver Tabelas\criar_tb_versao_schema.sql, marco zero = 1).
# v1.4.0 (Sessao 093): versao 2 = blockchain (conferido_em) -
# script Tabelas\14_alter_blk_conferido_versao2.sql.
# v1.5.0 (Sessao 098): versao 3 = Saidas/Abate (tb_2020, tb_2002 e tb_2011) -
# script Tabelas\criar_tb_2020_2002_2011_s098.sql.
# v1.6.0 (Sessao 098): versao 4 = coluna elemento (tb_2020 e tb_2002) -
# script Tabelas\alterar_tb_2020_2002_elemento_s098.sql.
# v1.8.0 (Sessao 107): versao 5 = coluna id_propriedade_destino (tb_2020 e tb_2011) -
# script Tabelas\alterar_tb_2020_2011_destino_transfer_s107.sql.
# v1.9.0 (Sessao 111): versao 6 = Morte (tb_2013_com_morte (Controle MRT), coluna id_com_morte em tb_2002 e tabelas tb_2021_notificacao_morte e tb_2022_morte_fotos) -
# scripts Tabelas\criar_morte_s111.sql e criar_morte_s111_b.sql.
# v1.10.0 (Sessao 114): versao 7 = Pesos (coluna elemento_perdido em tb_4003 e tb_2001; tabela tb_4007_pesagem_inconformes) -
# script Tabelas\criar_pesos_s114.sql.
# v1.11.0 (Sessao 115): versao 8 = Alteracao de Posse (colunas motivo_posse e justificativa_posse em tb_2011; POSSE em tipo_saida) -
# script Tabelas\alterar_posse_s115.sql.
# v1.12.0 (Sessao 120): versao 9 = Linkagem RFID e Brinco (tabela tb_4008_linkagem_inconformes) -
# script Tabelas\criar_linkagem_s120.sql.
# -------------------------------------------------------
VERSAO_SCHEMA_ATUAL = 12   # s121 v1.15.0 - tb_6006 pendentes (id_propriedade, data_reidentificacao, id_usuario, id_pedido vazio); s121 - Reidentificacao (tb_4010, colunas novas de tb_6005/tb_6006, REIDENTI no CHECK da tb_2002)
# v1.4.0: as 3 tabelas do blockchain ficam FORA do Restore (o que ja
# foi enviado a blockchain nao volta no tempo).
TABELAS_EXCLUIDAS_DO_BACKUP = [
    'tb_log_operacoes',
    'tb_log_operacoes_itens',
    'tb_backup_restore_pedido',
    'tb_blk_8001_produtor_provedores',
    'tb_blk_8002_eventos',
    'tb_blk_8003_envios',
]

PADRAO_SCHEMA_NOME = re.compile(r'^produtor_\d{5}$')


class SchemaNomeInvalido(Exception):
    pass


class ExecutavelPostgresNaoEncontrado(Exception):
    pass


class BackupNaoEncontrado(Exception):
    pass


class ErroBackup(Exception):
    pass


class ErroRestore(Exception):
    pass


# -------------------------------------------------------
# NOVO v1.3.0: levantada quando o backup escolhido para Restore
# foi gerado numa versao de estrutura diferente da atual - o
# chamador decide se pede confirmacao explicita (ver DESCRICAO no
# cabecalho do arquivo).
# -------------------------------------------------------
class VersaoSchemaIncompativel(Exception):
    def __init__(self, schema_nome, versao_backup, versao_atual):
        self.schema_nome    = schema_nome
        self.versao_backup  = versao_backup
        self.versao_atual   = versao_atual
        super().__init__(
            f'O backup escolhido para "{schema_nome}" foi gerado quando a '
            f'estrutura do banco estava na versão {versao_backup}, mas o '
            f'sistema hoje espera a versão {versao_atual}. Restaurar sem '
            f'reaplicar os scripts de atualização pendentes pode causar erros.'
        )


def _validar_schema_nome(schema_nome: str):
    if not PADRAO_SCHEMA_NOME.match(schema_nome):
        raise SchemaNomeInvalido(
            f'schema_nome "{schema_nome}" nao bate com o padrao esperado '
            f'(produtor_NNNNN).'
        )


def _validar_executaveis():
    if not os.path.isfile(CAMINHO_PG_DUMP):
        raise ExecutavelPostgresNaoEncontrado(
            f'pg_dump.exe nao encontrado em "{CAMINHO_PG_DUMP}". '
            f'Confira a variavel PG_BIN_DIR no .env.'
        )
    if not os.path.isfile(CAMINHO_PG_RESTORE):
        raise ExecutavelPostgresNaoEncontrado(
            f'pg_restore.exe nao encontrado em "{CAMINHO_PG_RESTORE}". '
            f'Confira a variavel PG_BIN_DIR no .env.'
        )


def _pasta_produtor(schema_nome: str) -> str:
    _validar_schema_nome(schema_nome)
    pasta = os.path.join(BACKUP_DIR, schema_nome)
    os.makedirs(pasta, exist_ok=True)
    return pasta


def _ambiente_com_senha() -> dict:
    ambiente = os.environ.copy()
    ambiente['PGPASSWORD'] = DB_PASS
    return ambiente


# -------------------------------------------------------
# Funcao auxiliar - NOVO v1.3.0: le tb_versao_schema do schema do
# Produtor, via conexao direta psycopg2 (backup_helper.py nao usa
# SQLAlchemy/ORM em nenhum outro ponto, mantido o mesmo estilo).
# Devolve None se a tabela nao existir ainda (schema muito antigo,
# anterior a esta funcionalidade) - tratado como "sem informacao
# de versao", nunca quebra por conta disso.
# -------------------------------------------------------
def _ler_versao_schema_atual(schema_nome: str):
    _validar_schema_nome(schema_nome)
    conexao = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                f'SELECT versao FROM "{schema_nome}".tb_versao_schema LIMIT 1'
            )
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None
    except psycopg2.errors.UndefinedTable:
        return None
    finally:
        conexao.close()


# -------------------------------------------------------
# Funcao auxiliar - NOVO v1.3.0: le a versao gravada no arquivo
# .meta de um backup especifico. Devolve None se o arquivo .meta
# nao existir (backups criados ANTES desta funcionalidade nao tem
# .meta - tratado como "sem informacao de versao", nunca bloqueia
# por conta disso).
# -------------------------------------------------------
def _ler_versao_backup(caminho_dump: str):
    caminho_meta = caminho_dump + '.meta'
    if not os.path.isfile(caminho_meta):
        return None
    with open(caminho_meta, 'r', encoding='utf-8') as arquivo_meta:
        conteudo = arquivo_meta.read().strip()
    return int(conteudo) if conteudo.isdecimal() else None


def criar_backup(schema_nome: str, sufixo: str = '') -> str:
    _validar_schema_nome(schema_nome)
    _validar_executaveis()

    pasta = _pasta_produtor(schema_nome)

    data_hoje = datetime.now().strftime('%Y%m%d')
    nome_arquivo = f'{schema_nome}_{data_hoje}{sufixo}.dump'
    caminho_completo = os.path.join(pasta, nome_arquivo)

    comando = [
        CAMINHO_PG_DUMP,
        '-h', DB_HOST,
        '-p', str(DB_PORT),
        '-U', DB_USER,
        '-d', DB_NAME,
        '-n', schema_nome,
        '-Fc',
        '-f', caminho_completo,
    ]

    resultado = subprocess.run(
        comando,
        env=_ambiente_com_senha(),
        capture_output=True,
        text=True,
    )

    if resultado.returncode != 0:
        raise ErroBackup(
            f'pg_dump retornou erro ao gerar backup de "{schema_nome}": '
            f'{resultado.stderr.strip()}'
        )

    # NOVO v1.3.0: grava a versao vigente ao lado do .dump.
    versao_atual = _ler_versao_schema_atual(schema_nome)
    with open(caminho_completo + '.meta', 'w', encoding='utf-8') as arquivo_meta:
        arquivo_meta.write(str(versao_atual) if versao_atual is not None else '')

    if not sufixo:
        _expurgar_backups_antigos(schema_nome)

    return nome_arquivo


def listar_backups_disponiveis(schema_nome: str) -> list:
    pasta = _pasta_produtor(schema_nome)

    padrao_arquivo_diario = re.compile(
        rf'^{re.escape(schema_nome)}_(\d{{8}})\.dump$'
    )

    backups = []
    for nome_arquivo in os.listdir(pasta):
        combinou = padrao_arquivo_diario.match(nome_arquivo)
        if combinou:
            data_str = combinou.group(1)
            data_backup = datetime.strptime(data_str, '%Y%m%d').date()
            # NOVO v1.3.0: versao gravada no .meta, para exibicao
            # se a tela do Consiste quiser mostrar.
            caminho_completo = os.path.join(pasta, nome_arquivo)
            backups.append({
                'nome_arquivo': nome_arquivo,
                'data': data_backup,
                'versao': _ler_versao_backup(caminho_completo),
            })

    backups.sort(key=lambda item: item['data'], reverse=True)
    return backups


# -------------------------------------------------------
# v1.7.0 - So os backups ainda validos (ate RETENCAO_DIAS dias). E a lista que as telas mostram.
# -------------------------------------------------------
def listar_backups_validos(schema_nome: str) -> list:
    limite = datetime.now().date() - timedelta(days=RETENCAO_DIAS)
    return [b for b in listar_backups_disponiveis(schema_nome) if b['data'] >= limite]


def _expurgar_backups_antigos(schema_nome: str):
    limite = datetime.now().date() - timedelta(days=RETENCAO_DIAS)

    for backup in listar_backups_disponiveis(schema_nome):
        if backup['data'] < limite:
            pasta = _pasta_produtor(schema_nome)
            caminho_completo = os.path.join(pasta, backup['nome_arquivo'])
            os.remove(caminho_completo)
            caminho_meta = caminho_completo + '.meta'
            if os.path.isfile(caminho_meta):
                os.remove(caminho_meta)


def _gerar_lista_restore_filtrada(caminho_backup: str) -> str:
    resultado = subprocess.run(
        [CAMINHO_PG_RESTORE, '--list', caminho_backup],
        env=_ambiente_com_senha(),
        capture_output=True,
        text=True,
    )

    if resultado.returncode != 0:
        raise ErroRestore(
            f'Não foi possível ler o conteúdo do backup "{caminho_backup}": '
            f'{resultado.stderr.strip()}'
        )

    nomes_excluidos = set()
    for tabela in TABELAS_EXCLUIDAS_DO_BACKUP:
        nomes_excluidos.add(tabela)
        nomes_excluidos.add(f'{tabela}_id_seq')

    linhas_filtradas = []
    for linha in resultado.stdout.splitlines():
        tokens = linha.replace(';', ' ').split()
        if any(token in nomes_excluidos for token in tokens):
            linhas_filtradas.append(f';{linha}')
        else:
            linhas_filtradas.append(linha)

    caminho_lista = caminho_backup + '.list'
    with open(caminho_lista, 'w', encoding='utf-8') as arquivo_lista:
        arquivo_lista.write('\n'.join(linhas_filtradas))

    return caminho_lista


# -------------------------------------------------------
# ALTERADO v1.3.0: novo parametro confirmar_versao_incompativel
# (default False) - ver VersaoSchemaIncompativel e DESCRICAO no
# cabecalho do arquivo. A checagem so acontece se o backup tiver
# .meta (versao_backup nao None); backups antigos sem .meta nunca
# bloqueiam por falta dessa informacao.
# -------------------------------------------------------
def executar_restore(schema_nome: str, nome_arquivo_backup: str, confirmar_versao_incompativel: bool = False) -> str:
    _validar_schema_nome(schema_nome)
    _validar_executaveis()

    pasta = _pasta_produtor(schema_nome)
    # v1.16.0 - so o NOME do arquivo (sem pasta) e que esteja na lista de backups deste Produtor
    if (os.path.basename(nome_arquivo_backup) != nome_arquivo_backup
            or nome_arquivo_backup not in {b['nome_arquivo'] for b in listar_backups_disponiveis(schema_nome)}):
        raise BackupNaoEncontrado(
            f'Arquivo de backup "{nome_arquivo_backup}" nao encontrado '
            f'para o Produtor "{schema_nome}".'
        )
    caminho_backup_escolhido = os.path.join(pasta, nome_arquivo_backup)

    if not os.path.isfile(caminho_backup_escolhido):
        raise BackupNaoEncontrado(
            f'Arquivo de backup "{nome_arquivo_backup}" nao encontrado '
            f'para o Produtor "{schema_nome}".'
        )

    # NOVO v1.3.0: checagem de versao ANTES de qualquer coisa
    # irreversivel (nem o backup de seguranca ainda foi tirado).
    versao_backup = _ler_versao_backup(caminho_backup_escolhido)
    if (
        versao_backup is not None
        and versao_backup != VERSAO_SCHEMA_ATUAL
        and not confirmar_versao_incompativel
    ):
        raise VersaoSchemaIncompativel(schema_nome, versao_backup, VERSAO_SCHEMA_ATUAL)

    hora_agora = datetime.now().strftime('%H%M%S')
    nome_arquivo_seguranca = criar_backup(schema_nome, sufixo=f'_pre_restore_{hora_agora}')

    caminho_lista_filtrada = _gerar_lista_restore_filtrada(caminho_backup_escolhido)

    comando = [
        CAMINHO_PG_RESTORE,
        '-h', DB_HOST,
        '-p', str(DB_PORT),
        '-U', DB_USER,
        '-d', DB_NAME,
        '-n', schema_nome,
        '--clean',
        '--if-exists',
        '--no-owner',
        '--use-list', caminho_lista_filtrada,
        caminho_backup_escolhido,
    ]

    resultado = subprocess.run(
        comando,
        env=_ambiente_com_senha(),
        capture_output=True,
        text=True,
    )

    if resultado.returncode != 0:
        raise ErroRestore(
            f'pg_restore retornou erro ao restaurar "{schema_nome}" a partir '
            f'de "{nome_arquivo_backup}": {resultado.stderr.strip()}'
        )

    return nome_arquivo_seguranca

# =========================================================
# FIM DE ARQUIVO: backend\utils\backup_helper.py
# =========================================================