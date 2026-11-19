# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\onboarding.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-07-17 15:15 -03
# ATUALIZADO EM: 2026-11-16 11:10 -03
# VERSAO: 1.12.0
#
# DESCRICAO:
#     Rotina de Onboarding do Produtor - transforma um Produtor
#     "cadastrado" (so uma linha em produtores, schema_nome vazio)
#     em um Produtor "operacional" (schema fisico proprio, com as
#     tabelas de movimento criadas dentro dele).
#
#     Separado de multitenant.py de proposito (Sessao 019,
#     conversa com Benedito): multitenant.py tem a responsabilidade
#     de ROTEAR para o schema certo em tempo de uso (get_db_produtor,
#     chamado toda vez que uma rota precisa ler/escrever dados de
#     um Produtor ja existente); este arquivo tem a responsabilidade
#     de CRIAR o schema, uma vez so, na fundacao do ambiente daquele
#     Produtor.
#
#     TABELAS_SCHEMA_PRODUTOR e a lista central de quais Models
#     pertencem ao schema do Produtor (nao ao schema publico/
#     "terreo"). Sempre que uma tabela nova do modulo Animais
#     (ou qualquer outro modulo futuro) for classificada como
#     "schema do Produtor", ela entra nesta lista - e SO nesta
#     lista, nao precisa mexer no resto da funcao de criacao.
#
#     IDEMPOTENTE POR DESIGN (decisao com Benedito, Sessao 019):
#     o modulo Animais no GERAS tem 36 tabelas, das quais so 11
#     estao mapeadas no Orion ate hoje. Para nao deixar Produtores
#     onboardados hoje desatualizados no futuro, a criacao das
#     tabelas usa checkfirst=True (nunca tenta recriar uma tabela
#     que ja existe naquele schema).
#
#     v1.1.0 - CORRECAO DE CONTRATO (Sessao 022): a docstring desta
#     rotina sempre prometeu que ela poderia "ser chamada de novo no
#     futuro, apos a lista crescer, para completar schemas ja
#     existentes sem duplicar nem apagar nada" - mas o codigo da
#     v1.0.0 nao cumpria essa promessa: criar_ambiente_produtor()
#     recusava de saida (ProdutorJaOnboardado) qualquer Produtor que
#     ja tivesse schema_nome preenchido, nunca chegando no
#     checkfirst=True que faria a "reforma". Identificado por Clau
#     ao revisar o arquivo real antes de adicionar as tabelas do
#     GR6003/GR6004 (Reidentificacao por Elementos) - decisao com
#     Benedito: manter criar_ambiente_produtor() com responsabilidade
#     unica (onboarding do zero, intocada) e adicionar uma funcao
#     NOVA e separada, completar_ambiente_produtor(), para o caso de
#     "reforma" (schema ja existente ganhando tabelas que a planta
#     ganhou depois que aquele Produtor ja tinha sido onboardado).
#
#     ROLLBACK TOTAL em caso de falha no meio da criacao (decisao
#     com Benedito, Sessao 019) - se aplica a criar_ambiente_produtor:
#     se qualquer tabela falhar ao ser criada, o schema inteiro e
#     apagado (DROP SCHEMA ... CASCADE) e a excecao original e
#     relancada - nunca fica um schema pela metade no banco. Esta e a
#     UNICA situacao em que dados sao apagados por esta rotina - antes
#     de gravar schema_nome no Produtor, ainda nao existe dado real
#     para perder. completar_ambiente_produtor() NAO faz rollback de
#     schema (o schema ja existe e pode ja ter dados reais dentro -
#     ver docstring da propria funcao para o tratamento de erro).
#     IMPORTANTE: isto NAO tem relacao com Inativar um Produtor
#     (ver multitenant.py v1.1.0 / ProdutorInativo) - inativacao
#     de um ambiente ja funcionando NUNCA apaga schema ou dados,
#     so bloqueia escrita.
#
#     v1.0.0: Criacao do modulo (Sessao 019). Cobre a criacao do
#             ambiente para um Produtor por vez, acionada por
#             botao manual na tela /produtores/editar/<id> (perfil
#             CONSISTE). Acesso pela Certificadora fica para o
#             modulo Certificadora (P-013), quando existir.
#     v1.1.0: Sessao 022 - Adicionadas ReIdElementos (tb_6003_re_id_
#             elementos) e ReIdElementosItem (tb_6004_re_id_elementos_
#             itens) a TABELAS_SCHEMA_PRODUTOR. Nova funcao
#             completar_ambiente_produtor() para "reformar" schemas
#             ja existentes (ver nota de correcao de contrato acima).
#     v1.2.0: Sessao 022 - Adicionadas ReidentificacaoComBaixa
#             (tb_6005_reidentificacao_com_baixa) e
#             ReidentificacaoComBaixaItem (tb_6006_reidentificacao_
#             com_baixa_itens) a TABELAS_SCHEMA_PRODUTOR - processo
#             de Reidentificacao COM Baixa (SISBOV muda de fato),
#             distinto de Elementos (mesmo SISBOV, so troca a peca
#             fisica).
#     v1.3.0: Sessao 022 - Adicionadas PerdaSaidaEstoque
#             (tb_6007_perda_saida_estoque) e PerdaSaidaEstoqueItem
#             (tb_6008_perda_saida_estoque_itens) a TABELAS_SCHEMA_
#             PRODUTOR - processo de Perda Saida Estoque (animal
#             sem nenhum elemento de identificacao, aviso previo ao
#             MAPA).
#     v1.4.0: Sessao 022 - Adicionadas CancelamentoBrinco
#             (tb_6012_cancelamento_brinco) e CancelamentoBrincoItem
#             (tb_6013_cancelamento_brinco_itens) a TABELAS_SCHEMA_
#             PRODUTOR - processo de Cancelamento de Brinco (brinco
#             quebrado/danificado antes de ser aplicado no animal).
#             Fecha, por hoje, a familia de tabelas de
#             Reidentificacao/Formularios (pasta 6-Formularios).
#     v1.5.0: Sessao 024 - Adicionada Animal (tb_2001, Estado Atual
#             do Animal) a TABELAS_SCHEMA_PRODUTOR - pasta 4-Animais.
#             Unico Produtor onboardado hoje (produtor_00001) ja
#             recebeu a tabela manualmente antes desta atualizacao
#             (ver script criar_tb_2001_animal.sql); nao foi
#             necessario rodar completar_ambiente_produtor() para
#             ele. A partir de agora, todo Produtor novo nasce com
#             tb_2001 automaticamente.
#     v1.6.0: Sessao 034 (continuacao 5, 11/08/2026, 12:26 -03) -
#             RENOMEACAO (decisao de Benedito): tb_2001_animal.py /
#             classe Animal viram tb_2001_entradas.py / classe
#             Entrada (nome antigo descrevia mal o proposito real -
#             ver tb_2001_entradas.py v1.1.0 para a explicacao
#             completa). Import atualizado; entrada correspondente
#             em TABELAS_SCHEMA_PRODUTOR trocada de Animal para
#             Entrada - mesma posicao na lista, mesma tabela fisica
#             (tb_2001), nenhuma mudanca de comportamento desta
#             rotina.
#     v1.7.0: Sessao 093 (10/10/2026, 14:30 -03) - ATUALIZACAO DA LISTA
#             (erro achado pelo Claude ao comparar a lista com o banco
#             real: o produtor_00004 tinha 33 tabelas e a lista criava so
#             18). Produtor NOVO agora nasce com as 15 que faltavam:
#             - 13 Models: ComunicadoEntrada (tb_2012), Movimentacao
#               (tb_2017), Peso (tb_4003), RejeicaoBrincagem (tb_5003),
#               Pia (tb_7002), NotificacaoImpressao (tb_7020),
#               LogAlteracaoGta, BackupRestorePedido, LogOperacao,
#               LogOperacaoItem, ProdutorProvedorBlk (tb_blk_8001),
#               EventoBlk (tb_blk_8002) e EnvioBlk (tb_blk_8003);
#             - Raca (tb_4005_racas) - no TOPO da lista, porque tb_5001 e
#               tb_2001 tem ForeignKey para ela: alem de criar, CARREGA a lista de
#               racas (reaproveita popular_tabela de popular_racas.py -
#               nao ha lista duplicada);
#             - tb_versao_schema (sem Model, criada por SQL aqui): nasce
#               com 1 linha = VERSAO_SCHEMA_ATUAL (de backup_helper.py).
#             Nova funcao interna _criar_dados_iniciais(), chamada dentro
#             do try de criar_ambiente_produtor (falhou = rollback total
#             do schema, como ja era). completar_ambiente_produtor() NAO
#             foi alterada (usa a mesma lista, entao tambem enxerga as
#             novas tabelas; nao mexe em tb_versao_schema nem em racas).
#     v1.7.1: Sessao 093 (10/10/2026, 16:06 -03) - CORRECAO de erro achado
#             no teste real (produtor id 11): o onboarding falhou com
#             NotNullViolation na coluna "ativo" de tb_4005_racas. CAUSA: a
#             tabela criada a partir do Model nao tem os valores PADRAO do
#             banco (ativo = true, criado_em = now()...), porque os Models
#             so tem o padrao do lado do Python; as tabelas criadas pelos
#             scripts SQL tem. A carga de racas insere sem esses campos e
#             quebrou. O MESMO PADRAO existe em 27 dos 28 Models da lista
#             (64 colunas). SOLUCAO (um unico lugar): nova funcao
#             _alinhar_defaults_com_models() copia o padrao de cada coluna
#             do Model para o banco (ALTER ... SET DEFAULT), logo apos criar
#             as tabelas e ANTES de carregar as racas. Padrao so do tipo
#             verdadeiro/falso, numero, texto, agora (datetime.now) e hoje
#             (date.today); qualquer outro tipo e ignorado. Nao altera nenhum
#             Model. O rollback total do schema funcionou: o schema do teste
#             foi apagado, nada ficou pela metade.
#     v1.7.3: Sessao 098 (16/10/2026, 14:16 -03) - SAIDAS (Abate): Produtor NOVO passa a
#             nascer tambem com Embarque (tb_2020_embarque), SaidaAnimal (tb_2002_saida_
#             animais) e ComunicadoSaida (tb_2011_com_saidas), na lista central, logo
#             apos Entrada (Embarque antes de SaidaAnimal: tb_2002 tem ForeignKey para
#             tb_2020). Em _criar_travas_e_indices: 5 CHECKs novos, 5 indices novos e o
#             indice unico parcial uq_tb_2020_sisbov_aberto - mesmos nomes e regras do
#             script Tabelas\criar_tb_2020_2002_2011_s098.sql dos schemas antigos.
#     v1.7.4: Sessao 098 (16/10/2026, 18:05 -03) - Produtor NOVO passa a nascer tambem com
#             LogConferenciaPropriedade (tb_log_conferencia_propriedade), que faltava na
#             lista central (auditoria Benedito/Claude).
#     v1.7.5: Sessao 098 (16/10/2026, 19:55 -03) - 2 CHECKs novos em _criar_travas_e_indices:
#             chk_tb_2020_elemento e chk_tb_2002_elemento (elemento vazio, BOTTON ou BRINCO) -
#             mesmos nomes do script Tabelas\alterar_tb_2020_2002_elemento_s098.sql.
#     v1.8.0: Sessao 114 (2026-11-04 11:20 -03) - Onboarding: Model PesagemInconforme (tb_4007), CHECKs elemento_perdido (tb_4003 e tb_2001) e indice da tb_4007.  REVERSAO: .bak_antes_s114_pesos.
#     v1.9.0: Sessao 115 (2026-11-05 11:13 -03) - ALTERACAO DE POSSE (pacote 1): os 3 CHECKs de tipo_saida (tb_2020, tb_2002, tb_2011) aceitam POSSE e
#         nova trava chk_tb_2011_motivo_posse (VENDA / HERANCA). Mesmas definicoes do script Tabelas\alterar_posse_s115.sql.  REVERSAO: .bak_antes_s115_posse.
#     v1.10.0: Sessao 121 (2026-11-11 15:00 -03) - REIDENTIFICACAO: Model ReidentificacaoInconforme (tb_4010), CHECK REIDENTI no tipo_saida da tb_2002, CHECK chk_tb_6006_motivo e indices (mesmas definicoes do
#         script Tabelas\criar_reidentificacao_s121.sql). CORRECAO: tb_4008/tb_4009 (Linkagem, s120) tambem entram na lista (faltavam: produtor novo nascia sem elas).  REVERSAO: .bak_antes_s121_reidentificacao.
#     v1.12.0: Sessao 128 (2026-11-16 11:10 -03) - AUDITORIA ETAPA 7d: Produtor novo nasce com o indice unico uq_tb_2001_rfid (RFID nao repete no Produtor), mesmo nome e regra do script Tabelas\SQL_criar_indice_rfid_16-11-2026.sql. REVERSAO: .bak_antes_etapa7d.
#     v1.11.1: Sessao 123 (2026-11-13 17:50 -03) - AUDITORIA ETAPA 5: Produtor novo nasce com os 3 indices unicos das Saidas (uq_tb_2002_animal_valido, uq_tb_2002_embarque_valido, uq_tb_3008_sisbov), mesmos nomes e regras do script SQL_criar_indices_saidas_etapa5_13-11-2026.sql. REVERSAO: .bak_antes_etapa5.
#     v1.11.0: Sessao 121 (2026-11-11 19:00 -03) - Indice ix_tb_6006_prop (id_propriedade, id_pedido) para os animais pendentes; schema versao 12. REVERSAO: .bak_antes_s121_pendentes.
# =========================================================

from datetime import date, datetime

from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models.produtor import Produtor
from backend.models.tb_parceiros import Parceiro
from backend.models.tb_parceiros_propriedades import ParceiroPropriedades
from backend.models.tb_log_conferencia_parceiro import LogConferenciaParceiro
from backend.models.tb_log_conferencia_propriedade import LogConferenciaPropriedade
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_2011_com_saidas import ComunicadoSaida
from backend.models.tb_2013_com_morte import ControleMorte                # s111 - Morte (Controle Interno MRT)
from backend.models.tb_2021_notificacao_morte import NotificacaoMorte   # s111 - Morte
from backend.models.tb_2022_morte_fotos import MorteFoto                 # s111 - Morte (fotos)
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4001_gta_animais import GtaAnimal
from backend.models.tb_5001_brincagem import Brincagem
from backend.models.tb_3007_brincos_entrada import BrincoEntrada
from backend.models.tb_3008_brincos_saida import BrincoSaida
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from backend.models.tb_6003_re_id_elementos import ReIdElementos
from backend.models.tb_6004_re_id_elementos_itens import ReIdElementosItem
from backend.models.tb_6005_reidentificacao_com_baixa import ReidentificacaoComBaixa
from backend.models.tb_6006_reidentificacao_com_baixa_itens import ReidentificacaoComBaixaItem
from backend.models.tb_6007_perda_saida_estoque import PerdaSaidaEstoque
from backend.models.tb_6008_perda_saida_estoque_itens import PerdaSaidaEstoqueItem
from backend.models.tb_6012_cancelamento_brinco import CancelamentoBrinco
from backend.models.tb_6013_cancelamento_brinco_itens import CancelamentoBrincoItem
from backend.utils.multitenant import gerar_schema_nome, PADRAO_SCHEMA_NOME

# NOVO v1.7.0 - Models que faltavam na lista (ver changelog).
from backend.models.tb_2012_com_entrada import ComunicadoEntrada
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_4007_pesagem_inconformes import PesagemInconforme   # s114 - Leitor de Peso
from backend.models.tb_4008_linkagem_inconformes import LinkagemInconforme   # s121 - faltava desde a s120 (Linkagem)
from backend.models.tb_4009_linkagem import Linkagem   # s121 - faltava desde a s120 (Linkagem)
from backend.models.tb_4010_reidentificacao_inconformes import ReidentificacaoInconforme   # s121 - Reidentificacao
from backend.models.tb_4005_racas import Raca
from backend.models.tb_5003_rejeicoes_brincagem import RejeicaoBrincagem
from backend.models.tb_7002_pia import Pia
from backend.models.tb_7020_notificacao_impressao import NotificacaoImpressao
from backend.models.tb_log_alteracao_gta import LogAlteracaoGta
from backend.models.tb_backup_restore_pedido import BackupRestorePedido
from backend.models.tb_log_operacoes import LogOperacao
from backend.models.tb_log_operacoes_itens import LogOperacaoItem
from backend.models.tb_blk_8001_produtor_provedores import ProdutorProvedorBlk
from backend.models.tb_blk_8002_eventos import EventoBlk
from backend.models.tb_blk_8003_envios import EnvioBlk

# NOVO v1.7.0 - versao do banco (tb_versao_schema) e carga das racas.
from backend.utils.backup_helper import VERSAO_SCHEMA_ATUAL
from backend.scripts.popular_racas import popular_tabela as popular_racas_no_schema


# -------------------------------------------------------
# Lista central - UNICO lugar que precisa ser atualizado
# quando uma tabela nova entrar no grupo "schema do Produtor".
# Fabricante e Frigorifico NAO entram aqui - vivem no schema
# publico (terreo), sao compartilhados entre todos os
# Produtores.
# -------------------------------------------------------
TABELAS_SCHEMA_PRODUTOR = [
    # NOVO v1.7.0: Raca TEM que vir ANTES de Brincagem e Entrada (tb_5001 e
    # tb_2001 tem ForeignKey para tb_4005_racas no mesmo schema).
    Raca,
    Parceiro,
    ParceiroPropriedades,
    LogConferenciaParceiro,
    LogConferenciaPropriedade,  # NOVO v1.7.4 (Sessao 098)
    Gta,
    GtaAnimal,
    Brincagem,
    BrincoEntrada,
    BrincoSaida,
    EntradaBrincoRfid,
    ReIdElementos,
    ReIdElementosItem,
    ReidentificacaoComBaixa,
    ReidentificacaoComBaixaItem,
    PerdaSaidaEstoque,
    PerdaSaidaEstoqueItem,
    CancelamentoBrinco,
    CancelamentoBrincoItem,
    Entrada,
    # ---- NOVO v1.7.3 (Sessao 098) - Saidas/Abate. Embarque ANTES de SaidaAnimal ----
    Embarque,
    ControleMorte,      # s111 - Morte (MRT; ANTES de SaidaAnimal, que tem FK para ele)
    SaidaAnimal,
    ComunicadoSaida,
    NotificacaoMorte,   # s111 - Morte (Notificacao, Anexo XXII)
    MorteFoto,          # s111 - Morte (fotos; FK para tb_2002, por isso depois de SaidaAnimal)
    # ---- NOVO v1.7.0 (Sessao 093) ----
    # ORDEM IMPORTA: quem tem ForeignKey para tabela do mesmo schema
    # vem DEPOIS dela (Gta e ParceiroPropriedades ja estao acima;
    # LogOperacao antes de LogOperacaoItem; EventoBlk antes de EnvioBlk).
    ComunicadoEntrada,
    Movimentacao,
    Peso,
    PesagemInconforme,   # s114
    LinkagemInconforme,  # s121 (faltava da s120)
    Linkagem,            # s121 (faltava da s120)
    ReidentificacaoInconforme,   # s121
    RejeicaoBrincagem,
    Pia,
    NotificacaoImpressao,
    LogAlteracaoGta,
    BackupRestorePedido,
    LogOperacao,
    LogOperacaoItem,
    ProdutorProvedorBlk,
    EventoBlk,
    EnvioBlk,
]


class ProdutorJaOnboardado(Exception):
    """Levantada quando o Produtor ja tem schema_nome preenchido -
    evita tentar criar um schema que ja existe (o que geraria erro
    feio do Postgres, 'schema already exists'). Levantada apenas por
    criar_ambiente_produtor() - completar_ambiente_produtor() e o
    caminho correto quando o schema ja existe."""
    pass


class ProdutorAindaNaoOnboardado(Exception):
    """Levantada por completar_ambiente_produtor() quando o Produtor
    ainda NAO tem schema_nome preenchido - nao ha o que 'completar'
    em um andar que ainda nao foi construido. Nesse caso, o caminho
    correto e criar_ambiente_produtor()."""
    pass


# -------------------------------------------------------
# NOVO v1.7.1 - Converte o valor padrao de uma coluna do Model (lado
# Python) no texto SQL equivalente. Devolve None se o tipo nao for
# suportado (a coluna e simplesmente ignorada).
#   verdadeiro/falso -> true / false      numero -> o proprio numero
#   texto            -> 'texto'            datetime.now -> now()
#   date.today       -> CURRENT_DATE
# -------------------------------------------------------
def _padrao_sql_da_coluna(padrao):
    if getattr(padrao, 'is_scalar', False):
        valor = padrao.arg
        if isinstance(valor, bool):
            return 'true' if valor else 'false'
        if isinstance(valor, (int, float)):
            return str(valor)
        if isinstance(valor, str):
            return "'" + valor.replace("'", "''") + "'"
        return None
    if getattr(padrao, 'is_callable', False):
        funcao = getattr(padrao.arg, '__wrapped__', padrao.arg)
        if funcao == datetime.now:
            return 'now()'
        if funcao == date.today:
            return 'CURRENT_DATE'
    return None


# -------------------------------------------------------
# NOVO v1.7.1 - Alinha os valores PADRAO do banco com os dos Models.
# Tabela criada a partir do Model nasce sem DEFAULT no banco (o
# Model so tem o padrao no Python); as criadas por script SQL tem.
# Esta rotina copia o padrao de cada coluna do Model para o banco,
# em todas as tabelas de TABELAS_SCHEMA_PRODUTOR. Colunas que ja
# tem padrao do lado do banco (server_default) ou chave primaria
# sao puladas. Chamada por _criar_dados_iniciais, ANTES das racas.
# -------------------------------------------------------
def _alinhar_defaults_com_models(conexao, schema_nome: str) -> None:
    for model in TABELAS_SCHEMA_PRODUTOR:
        tabela = model.__table__
        for coluna in tabela.columns:
            if coluna.primary_key or coluna.server_default is not None or coluna.default is None:
                continue
            padrao_sql = _padrao_sql_da_coluna(coluna.default)
            if padrao_sql is None:
                continue
            conexao.execute(text(
                f'ALTER TABLE "{schema_nome}"."{tabela.name}" '
                f'ALTER COLUMN "{coluna.name}" SET DEFAULT {padrao_sql}'
            ))


# -------------------------------------------------------
# NOVO v1.7.2 - Travas (CHECK) e indices que os Models nao criam
# (nos schemas antigos vieram de scripts SQL). Mesmas definicoes
# do produtor_00004. So e chamada por _criar_dados_iniciais, logo
# apos a criacao das tabelas (schema_nome ja validado).
# -------------------------------------------------------
def _criar_travas_e_indices(conexao, schema_nome: str) -> None:
    numero = schema_nome.replace('produtor_', '')

    travas = [
        ('tb_4003_pesos', 'tb_4003_pesos_peso_check',
         'peso > 0'),
        ('tb_4003_pesos', 'chk_tb_4003_elemento_perdido',
         "elemento_perdido IS NULL OR elemento_perdido IN ('BOTTON', 'BRINCO')"),   # s114
        ('tb_2001', 'chk_tb_2001_elemento_perdido',
         "elemento_perdido IS NULL OR elemento_perdido IN ('BOTTON', 'BRINCO')"),   # s114
        ('tb_5001_brincagem', 'chk_tb_5001_brincagem_saida_brincos',
         "saida_brincos IS NULL OR saida_brincos IN ('COM', 'SEM')"),
        ('tb_5001_brincagem', 'chk_tb_5001_brincagem_tipo_entrada',
         "tipo_entrada IN ('COMPRA', 'NASCIMENTO')"),
        ('tb_2012_com_entrada', 'chk_tb_2012_tipo_entrada',
         "tipo_entrada IN ('COMPRA', 'NASCTO-DESMAME', 'TRANSFERENCIA')"),
        ('tb_2020_embarque', 'chk_tb_2020_tipo_saida',
         "tipo_saida IN ('ABATE', 'VENDA', 'MORTE', 'TRANSFER', 'POSSE')"),
        ('tb_2020_embarque', 'chk_tb_2020_elemento',
         "elemento IS NULL OR elemento IN ('BOTTON', 'BRINCO')"),
        ('tb_2002_saida_animais', 'chk_tb_2002_elemento',
         "elemento IS NULL OR elemento IN ('BOTTON', 'BRINCO')"),
        ('tb_2002_saida_animais', 'chk_tb_2002_tipo_saida',
         "tipo_saida IN ('ABATE', 'VENDA', 'MORTE', 'TRANSFER', 'POSSE', 'REIDENTI')"),   # s121
        ('tb_2002_saida_animais', 'chk_tb_2002_tipo_morte',
         "tipo_morte IS NULL OR tipo_morte IN ('ACIDENTAL', 'DESLIGADO', 'NATURAL', 'SACRIFICIO')"),
        ('tb_2002_saida_animais', 'chk_tb_2002_destino_morte',
         "destino_morte IS NULL OR destino_morte IN ('CREMACAO', 'ENTERRAMENTO', 'OUTROS')"),
        ('tb_2011_com_saidas', 'chk_tb_2011_tipo_saida',
         "tipo_saida IN ('ABATE', 'VENDA', 'MORTE', 'TRANSFER', 'POSSE')"),
        ('tb_2011_com_saidas', 'chk_tb_2011_motivo_posse',
         "motivo_posse IS NULL OR motivo_posse IN ('VENDA', 'HERANCA')"),   # s115
        ('tb_6006_reidentificacao_com_baixa_itens', 'chk_tb_6006_motivo',
         "motivo IS NULL OR motivo IN ('PERDA', 'QUEBRA', 'DESGASTE', 'DEFEITO_LEITURA')"),   # s121
    ]
    for tabela, nome, condicao in travas:
        conexao.execute(text(
            f'ALTER TABLE "{schema_nome}"."{tabela}" '
            f'ADD CONSTRAINT {nome} CHECK ({condicao})'
        ))

    indices = [
        (f'idx_{numero}_2017_sisbov', 'tb_2017_movimentacoes', 'sisbov'),
        ('ix_tb_4003_prop_sisbov', 'tb_4003_pesos', 'id_propriedade, sisbov'),
        ('ix_tb_4007_prop_criado', 'tb_4007_pesagem_inconformes', 'id_propriedade, criado_em'),   # s114
        ('ix_tb_4010_prop_data', 'tb_4010_reidentificacao_inconformes', 'id_propriedade, criado_em'),   # s121
        ('ix_tb_6005_prop_data', 'tb_6005_reidentificacao_com_baixa', 'id_propriedade, data_solicitacao'),   # s121
        ('ix_tb_6006_prop', 'tb_6006_reidentificacao_com_baixa_itens', 'id_propriedade, id_pedido'),   # s121 v1.11.0
        ('ix_tb_6006_sisbov_antigo', 'tb_6006_reidentificacao_com_baixa_itens', 'sisbov_antigo'),   # s121
        ('ix_tb_6006_sisbov_novo', 'tb_6006_reidentificacao_com_baixa_itens', 'sisbov_novo'),   # s121
        (f'idx_{numero}_7002_propriedade_numero', 'tb_7002_pia', 'id_propriedade, numero_pia'),
        ('idx_tb_2020_embarque_data', 'tb_2020_embarque', 'id_propriedade, data_embarque'),
        ('idx_tb_2002_sisbov', 'tb_2002_saida_animais', 'sisbov'),
        ('idx_tb_2002_comunicado', 'tb_2002_saida_animais', 'id_propriedade, numero_comunicado'),
        ('idx_tb_2011_comunicado', 'tb_2011_com_saidas', 'id_propriedade_origem, numero_comunicado'),
        ('idx_tb_2002_com_morte', 'tb_2002_saida_animais', 'id_com_morte'),   # s111 - Morte
    ]
    for nome, tabela, colunas in indices:
        conexao.execute(text(
            f'CREATE INDEX IF NOT EXISTS {nome} '
            f'ON "{schema_nome}"."{tabela}" ({colunas})'
        ))

    # v1.7.3 (Sessao 098): o mesmo animal nao fica em duas leituras de saida ABERTAS.
    conexao.execute(text(
        f'CREATE UNIQUE INDEX IF NOT EXISTS uq_tb_2020_sisbov_aberto '
        f'ON "{schema_nome}"."tb_2020_embarque" (sisbov) WHERE sts = FALSE'
    ))

    # v1.11.1 (Sessao 123): uma entrada = uma saida valida; brinco baixado uma vez. Linha 'substituido' (Troca de Comunicado) e historico e nao conta.
    conexao.execute(text(
        f'CREATE UNIQUE INDEX IF NOT EXISTS uq_tb_2002_animal_valido '
        f'ON "{schema_nome}"."tb_2002_saida_animais" (id_animal) WHERE id_animal IS NOT NULL AND substituido = FALSE'
    ))
    conexao.execute(text(
        f'CREATE UNIQUE INDEX IF NOT EXISTS uq_tb_2002_embarque_valido '
        f'ON "{schema_nome}"."tb_2002_saida_animais" (id_embarque) WHERE id_embarque IS NOT NULL AND substituido = FALSE'
    ))
    conexao.execute(text(
        f'CREATE UNIQUE INDEX IF NOT EXISTS uq_tb_3008_sisbov '
        f'ON "{schema_nome}"."tb_3008_brincos_saida" (sisbov)'
    ))

    # v1.12.0 (Sessao 128): o mesmo RFID so em UM animal do Produtor. RFID vazio/nulo nao conta.
    conexao.execute(text(
        f'CREATE UNIQUE INDEX IF NOT EXISTS uq_tb_2001_rfid '
        f'ON "{schema_nome}"."tb_2001" (rfid) WHERE rfid IS NOT NULL AND rfid <> \'\''
    ))


# -------------------------------------------------------
# NOVO v1.7.0 - Dados iniciais de um schema recem-criado:
#   0. (v1.7.2) travas e indices que os Models nao criam.
#   1. tb_versao_schema (sem Model): 1 coluna "versao" (inteiro,
#      obrigatorio) e 1 linha = VERSAO_SCHEMA_ATUAL (backup_helper.py).
#   2. tb_4005_racas: carrega a lista de racas (ON CONFLICT DO
#      NOTHING - pode rodar de novo sem duplicar).
# So e chamada por criar_ambiente_produtor (schema_nome ja validado
# pelo PADRAO_SCHEMA_NOME antes de chegar aqui).
# -------------------------------------------------------
def _criar_dados_iniciais(schema_nome: str) -> None:
    with engine.begin() as conexao:
        _alinhar_defaults_com_models(conexao, schema_nome)
        _criar_travas_e_indices(conexao, schema_nome)
        conexao.execute(text(
            f'CREATE TABLE IF NOT EXISTS "{schema_nome}".tb_versao_schema '
            f'(versao INTEGER NOT NULL)'
        ))
        linhas = conexao.execute(text(
            f'SELECT count(*) FROM "{schema_nome}".tb_versao_schema'
        )).scalar()
        if not linhas:
            conexao.execute(
                text(f'INSERT INTO "{schema_nome}".tb_versao_schema (versao) VALUES (:v)'),
                {'v': VERSAO_SCHEMA_ATUAL}
            )
        popular_racas_no_schema(conexao, schema_nome)


def criar_ambiente_produtor(id_produtor: int) -> str:
    """
    Cria o schema fisico do Produtor e as tabelas de movimento
    dentro dele. Uso: Produtor NOVO, ainda sem schema_nome.

    Idempotente em relacao as tabelas (checkfirst), mas NAO
    idempotente em relacao ao Produtor - se ele ja foi onboardado,
    recusa e levanta ProdutorJaOnboardado (o caminho correto nesse
    caso e completar_ambiente_produtor(), nao esta funcao).

    Passo a passo:
      1. Busca o Produtor, confere que ainda nao foi onboardado.
      2. Gera o schema_nome a partir do id (gerar_schema_nome, ja
         existe em multitenant.py - reaproveitado, nao duplicado).
      3. CREATE SCHEMA.
      4. Para cada Model em TABELAS_SCHEMA_PRODUTOR, cria a tabela
         dentro do schema novo (via schema_translate_map - "traduz"
         o destino da criacao sem precisar de Models duplicados).
      4b. NOVO v1.7.0: _criar_dados_iniciais() - cria tb_versao_schema
         (com a versao atual) e carrega as racas.
      5. Se tudo deu certo: grava schema_nome no Produtor, commit.
      6. Se qualquer passo do meio falhar: DROP SCHEMA ... CASCADE
         (rollback total) e relanca a excecao original.

    Retorna:
        O schema_nome gerado, em caso de sucesso (ex.: 'produtor_00042').

    Levanta:
        ProdutorJaOnboardado: Produtor ja tem schema_nome preenchido.
        Exception original: qualquer falha durante a criacao das
                             tabelas (apos rollback total do schema).
    """
    with Session(engine) as db:
        produtor = db.get(Produtor, id_produtor)

        if produtor is None:
            raise ValueError(f'Produtor com id={id_produtor} nao encontrado.')

        if produtor.schema_nome:
            raise ProdutorJaOnboardado(
                f'Produtor id={id_produtor} ({produtor.nome}) ja foi '
                f'cadastrado anteriormente (schema_nome={produtor.schema_nome}).'
            )

        schema_nome = gerar_schema_nome(produtor.id)

        # Trava de seguranca - mesmo padrao usado em multitenant.py
        # antes de colocar um valor dentro de um comando SQL.
        if not PADRAO_SCHEMA_NOME.match(schema_nome):
            raise ValueError(f'schema_nome gerado "{schema_nome}" nao bate com o padrao esperado.')

        db.execute(text(f'CREATE SCHEMA {schema_nome}'))
        db.commit()

        try:
            engine_traduzido = engine.execution_options(
                schema_translate_map={None: schema_nome}
            )

            for model in TABELAS_SCHEMA_PRODUTOR:
                model.metadata.create_all(
                    bind=engine_traduzido,
                    tables=[model.__table__],
                    checkfirst=True
                )

            # NOVO v1.7.0: versao do banco + racas (dentro do try:
            # se falhar, o rollback total apaga o schema).
            _criar_dados_iniciais(schema_nome)

            produtor.schema_nome = schema_nome
            db.commit()

        except Exception:
            # Rollback total - qualquer falha no meio da criacao das
            # tabelas apaga o schema inteiro, nunca fica pela metade.
            db.execute(text(f'DROP SCHEMA {schema_nome} CASCADE'))
            db.commit()
            raise

        return schema_nome


def completar_ambiente_produtor(id_produtor: int) -> list[str]:
    """
    "Reforma" o andar de um Produtor que JA FOI onboardado - cria,
    dentro do schema_nome existente dele, qualquer tabela de
    TABELAS_SCHEMA_PRODUTOR que ainda nao exista fisicamente
    (checkfirst=True: tabela ja existente e ignorada, nunca
    recriada nem apagada).

    Nasceu na Sessao 022, quando ficou claro que
    criar_ambiente_produtor() nunca havia cumprido, de fato, a
    promessa original de "completar schemas existentes" - ela
    sempre recusou de saida qualquer Produtor ja onboardado. Esta
    funcao cobre exatamente esse caso, com responsabilidade unica:
    reformar, nunca construir do zero.

    Uso tipico: apos a lista TABELAS_SCHEMA_PRODUTOR crescer com
    uma tabela nova (ex.: ReIdElementos/ReIdElementosItem), rodar
    esta funcao para cada Produtor ja onboardado, um de cada vez,
    para que o andar dele "alcance" a planta mais recente.

    Passo a passo:
      1. Busca o Produtor, confere que JA foi onboardado (schema_
         nome preenchido) - senao, levanta ProdutorAindaNaoOnboardado.
      2. Para cada Model em TABELAS_SCHEMA_PRODUTOR, tenta criar a
         tabela dentro do schema_nome existente, com checkfirst=True.
      3. Retorna a lista de tabelas que de fato foram criadas agora
         (uteis para log/conferencia - tabelas que ja existiam nao
         entram nessa lista).

    Diferente de criar_ambiente_produtor(), esta funcao NAO faz
    DROP SCHEMA em caso de erro - o schema ja existe e pode conter
    dados reais de producao; um erro no meio do caminho e relancado
    tal como veio, sem apagar nada.

    Retorna:
        Lista com os __tablename__ das tabelas que foram criadas
        nesta chamada (lista vazia = schema ja estava completo).

    Levanta:
        ProdutorAindaNaoOnboardado: Produtor ainda nao tem schema_
                                     nome (usar criar_ambiente_produtor
                                     neste caso, nao esta funcao).
        Exception original: qualquer falha durante a criacao das
                             tabelas (sem rollback de schema).
    """
    with Session(engine) as db:
        produtor = db.get(Produtor, id_produtor)

        if produtor is None:
            raise ValueError(f'Produtor com id={id_produtor} nao encontrado.')

        if not produtor.schema_nome:
            raise ProdutorAindaNaoOnboardado(
                f'Produtor id={id_produtor} ({produtor.nome}) ainda nao foi '
                f'onboardado (schema_nome vazio). Use criar_ambiente_produtor().'
            )

        schema_nome = produtor.schema_nome

        engine_traduzido = engine.execution_options(
            schema_translate_map={None: schema_nome}
        )

        tabelas_criadas_agora = []
        inspetor = inspect(engine)

        for model in TABELAS_SCHEMA_PRODUTOR:
            tabela = model.__table__

            ja_existe = inspetor.has_table(tabela.name, schema=schema_nome)

            model.metadata.create_all(
                bind=engine_traduzido,
                tables=[tabela],
                checkfirst=True
            )

            if not ja_existe:
                tabelas_criadas_agora.append(tabela.name)

        return tabelas_criadas_agora

# =========================================================
# FIM DE ARQUIVO: backend\utils\onboarding.py
# =========================================================