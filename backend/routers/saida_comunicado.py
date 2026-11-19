# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\saida_comunicado.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-20 10:47 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.10.0
# v1.10.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.9.1: Sessao 123 (2026-11-13 17:30 -03) - AUDITORIA ETAPA 5: CNPJ alfanumerico nao perde mais as letras ao criar/achar o Parceiro de origem no destino (Transferencia entre Produtores); usa limpar_documento() (Regra #72). _so_digitos fica so para OESA/codigos. REVERSAO: .bak_antes_etapa5.
# v1.9.0: Sessao 117 (2026-11-06 20:50 -03) - VENDA, TRANSFERENCIA e POSSE na BLOCKCHAIN: evento da saida na origem (tipo proprio) e evento ENTRADA no destino (schema dele, se tem provedor ligado); data = Data de Saida. REVERSAO: .bak_antes_s117_saidas.
# v1.8.1: Sessao 117 (2026-11-06 20:10 -03) - Evento ABATE usa a Data de Saida como data do evento (antes: hora do Comunicado). REVERSAO: .bak_antes_s117_abate_data.
# v1.8.0: Sessao 117 (2026-11-06 19:00 -03) - ABATE na BLOCKCHAIN: cada animal baixado gera o evento ABATE (mesma transacao, mesmo id_operacao do Desfazer; so se o Produtor tem provedor ligado; falha da blockchain nao derruba o Comunicado). Demais saidas nao mexidas. REVERSAO: .bak_antes_s117_blockchain_abate.
# v1.7.1: Sessao 115 (2026-11-05 20:00 -03) - Posse: bloqueia o Comunicado se a Propriedade de origem nao tem OESA. REVERSAO: .bak_antes_s115_oesa.
# v1.7.0: Sessao 115 (2026-11-05 19:10 -03) - ALTERACAO DE POSSE (pacote 4): Comunicado de Posse no Gerar Comunicado (mesmo caminho da Venda). Motivo Venda/Heranca + justificativa por Comunicado (tb_2011.motivo_posse/justificativa_posse),
#         numeracao propria (000001), so Titular/Administrador, sem tb_2012 (sem Anexo XIX); Entrada POSSE direto na base do novo Produtor (animal sem lote, DTA copiada como ENTRADA ja comunicada). REVERSAO: .bak_antes_s115_posse_com.
#
# DESCRICAO:
#     Gerar Comunicado de Saida (Abate) - PACOTE 1 (Sessao 101): gera os Comunicados e DA A BAIXA
#     dos animais. Card "Gerar Comunicado de Saida" do Hub de Saidas, grupo "Comunicados a
#     Certificadora". A impressao do Anexo XXI/XX e a substituicao DEPOIS do Comunicado sao
#     pacotes seguintes (2 e 3) - este arquivo so GERA e DA A BAIXA.
#
#     REGRAS FECHADAS COM O BENEDITO (20/10/2026):
#       - AUTOMATICO, igual ao Comunicado de Entrada: o usuario NAO marca GTAs. A plataforma pega
#         TODAS as GTAs de saida vinculadas e sem Comunicado, agrupa por MESMO frigorifico + MESMA
#         Data de Saida e gera Comunicados de ATE 6 GTAs cada (a mais antiga primeiro, por emissao).
#         Passou de 6 no grupo, faz outro Comunicado, e assim ate a ultima GTA. Todas as GTAs do
#         mesmo Comunicado levam o MESMO numero (ex.: 000457).
#       - Data de Saida FUTURA pode: o usuario le os animais, recebe a GTA na hora e ja lanca a
#         Data de Saida de amanha. Lancada a GTA (vinculada, com Data de Saida), gera o Comunicado.
#       - Numero sequencial por Propriedade: maior numero da tb_2011 + 1, sob trava
#         (pg_advisory_xact_lock). tb_2011 = 1 linha por GTA, com o mesmo numero nas GTAs do
#         Comunicado. tb_2017.numero_comunicado e texto de 6 digitos ("000457").
#       - A BAIXA (tudo numa transacao so, tudo ou nada, todos os Comunicados juntos). Para cada
#         animal das GTAs:
#           1) tb_2002 (saida): ganha o animal, com a GTA de saida, frigorifico (nome e CNPJ),
#              Data de Saida, Comunicado, peso, lote de saida e aceites;
#           2) tb_2001: o animal e APAGADO (sai da Propriedade);
#           3) tb_2017: NOVA linha de saida (ABATE), copia fiel do animal como estava na tb_2001
#              no momento da baixa (a linha de Entrada NUNCA e reescrita: a tb_2017 so recebe
#              linhas novas);
#           4) tb_2020 (leitura do brete): sts = True e numero_comunicado.
#         Na GTA (tb_4001): numero_comunicado. Na tb_2011: 1 linha por GTA, status ABERTO.
#         tb_7002 (PIA) e tb_7017: NAO sao mexidas (decisao do Benedito).
#       - Tela de conferencia OBRIGATORIA antes de gravar: mostra todos os Comunicados que serao
#         gerados, com a caixinha "Revisei os dados e confirmo...". O servidor monta os grupos
#         de novo no clique (nada vem confiado do navegador).
#       - GTA que nao pode gerar (sem Data de Saida, animais diferentes da GTA, animal que nao esta
#         mais na Propriedade) NAO trava as outras: aparece na tela com o motivo e fica de fora.
#       - NAO existe "desfazer" neste pacote (a tela avisa). A baixa e registrada no Log de
#         Operacoes (modulo saida_comunicado, SO historico), 1 operacao por Comunicado, com a
#         linha inteira de cada animal apagado da tb_2001.
#
#     ASSUMIDO (Benedito ainda nao confirmou):
#       - GTA so entra se os animais vinculados forem IGUAIS a quantidade da GTA;
#       - tb_2017: negociacao e peso_medio ficam vazios na linha de saida;
#       - v1.8.0: registra o evento ABATE na blockchain, animal a animal, antes da baixa (decidido em 06/11/2026).
#
#     ROTAS (/produtor/saida-comunicado/):
#       iniciar      - resolve a Propriedade (fazenda em uso) e abre a conferencia.
#       conferencia  - GET: monta os Comunicados e mostra o que sera gravado (nada e gravado).
#       gerar        - POST: monta de novo e da a baixa de todos.
#
#     v1.0.0: Criacao (Sessao 101).
#     v1.1.0: Sessao 101 (2026-10-20 11:19 -03) - Automatico (sem marcar GTAs, grupos de ate 6 por frigorifico
#             + Data de Saida) e Data de Saida futura permitida. Sai a rota lista.
#     v1.2.0: Sessao 104 (23/10/2026, 12:25 -03) - (1) GTA com Data de Saida DEPOIS do vencimento da GTA fica bloqueada (a validade e respeitada);
#             (2) segunda trava: GTA com animal cuja entrada nao foi comunicada (Compra sem Comunicado de Entrada / Nascimento sem Notificacao)
#             fica bloqueada. REVERSAO: .bak_antes_s104h.
#     v1.6.0: Sessao 111 (01/11/2026) - VENDA (pacote 4): mesmo caminho da Transferencia entre Produtores, com tipo_saida/negociacao VENDA e numeracao propria da Venda
#             (000001 por Propriedade de origem). Comprador sempre OUTRO Produtor (mesmo Produtor bloqueia). Se o comprador esta na base, a Entrada cai como COMPRA no schema dele:
#             GTA copiada como ENTRADA/COMPRA ja comunicada (status BRINCADO), tb_2012 COMPRA ABERTO com o Parceiro de origem, animal na tb_2001 e nova linha na tb_2017;
#             numero da Entrada = sequencia da Compra do comprador. Bloqueia se o comprador ja tem a mesma GTA lancada na Entrada. REVERSAO: .bak_antes_s111_venda4.
#     v1.4.0: Sessao 108 (29/10/2026, 19:45 -03) - TRANSFERENCIA ENTRE PRODUTORES (Entrada DIRETA, sem aceite - decisao do Benedito): quando o destino e
#             Propriedade de OUTRO Produtor da base, a Saida e a Entrada saem na MESMA transacao (uma so sessao; o search_path troca para o schema do
#             destino so durante a gravacao da Entrada e volta). No schema do destino grava: COPIA da GTA (tb_4001, so como referencia: id_propriedade = a
#             origem, sem parceiro/frigorifico/numero de comunicado), Comunicado de Entrada (tb_2012, ja ABERTO, CPF/CNPJ do Produtor destino), animais
#             (tb_2001, sem brincagem e sem PIA) e a linha de entrada na tb_2017. Destino inativo ou sem schema: GTA bloqueada com o motivo. Erro em qualquer
#             ponto = nada e gravado (rollback unico). Log: modulo 'saida_comunicado_externo' (so historico; o Desfazer da Transferencia vem em outro pacote).
#             REVERSAO: .bak_antes_s108_entre_produtores.
#     v1.3.0: Sessao 107 (28/10/2026) - PACOTE 4: TRANSFERENCIA (mesmo Produtor). Mesmo card/tela do Abate; blocos por tipo (so aparecem se houver).
#             Lotes de ate 6 GTAs de Transferencia por MESMO destino + MESMA Data de Saida. Numeracao PROPRIA por tipo (Transferencia comeca em 000001;
#             o contador do Abate passa a contar so tipo_saida = ABATE). Destino conferido por conferir_destino (destino_transferencia.py):
#               NA_BASE (mesmo Produtor)  -> Saida na origem + ENTRADA automatica no destino, na MESMA transacao: tb_2001 do destino (tipo_entrada
#                                            TRANSFERENCIA, GTA de entrada = a propria GTA, Data de Entrada = Data de Saida, conferido), nova linha de
#                                            ENTRADA na tb_2017 e Comunicado de Entrada na tb_2012 ja ABERTO (numero proprio do destino; o destino so imprime).
#               PROPRIEDADE_FORA / FORA_BASE -> so a Saida (documentacao para a Certificadora no Pacote 5);
#               DIVERGENTE / MESMA_ORIGEM / outro Produtor da base (ainda nao liberado) -> GTA bloqueada, com o motivo.
#             Sem frigorifico na Transferencia. tb_2011.tipo_saida = TRANSFER, id_propriedade_destino quando na base. tb_2017 negociacao = TRANSFERENCIA.
#             REVERSAO: .bak_antes_s107zd.
#     REVERSAO: remover este arquivo e os templates saida_comunicado_*.html; devolver os
#     .bak_antes_comunicado_saida_s101 de app.py, permissoes.py, hub_entrada_agrupado.py e
#     log_operacoes.py. Os dados ja baixados NAO voltam sozinhos (sem desfazer): so por SQL, com
#     o Log de Operacoes.
#     v1.5.0: Sessao 109 (30/10/2026, 18:55 -03) - TRANSFERENCIA ENTRE PRODUTORES grava o id_origem (decisao do Benedito): no schema do destino o Orion
#             reaproveita (pelo CPF/CNPJ) ou cria o Parceiro que representa o Produtor de origem e a Propriedade de origem dele, e grava o id do Parceiro
#             na tb_2001 e na tb_2017_movimentacoes da Entrada. O Parceiro nasce SEM id_produtor (vinculo so por confirmacao manual, regra do model).
#             Mesmo Produtor continua com id_origem vazio. REVERSAO: .bak_antes_s109_id_origem.
# =========================================================

from contextlib import contextmanager, nullcontext
from datetime import date, datetime, time
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, session
from sqlalchemy import func, select, text, inspect as sa_inspect
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Produtor, Propriedade
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_2011_com_saidas import ComunicadoSaida
from backend.models.tb_2012_com_entrada import ComunicadoEntrada
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4001_gta import Gta
from backend.models.tb_frigorificos import Frigorifico
from backend.models.tb_parceiros import Parceiro
from backend.models.tb_parceiros_propriedades import ParceiroPropriedades
from backend.utils.destino_transferencia import conferir_destino, conferir_destino_posse, NA_BASE, DIVERGENTE, MESMA_ORIGEM
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.routers.saida_consulta import (
    _contexto_base, _propriedade_do_usuario, _negado, _data_br, _nomes, _filtro_abertas, URL_HUB,
)
from backend.utils.multitenant import get_db_produtor, PADRAO_SCHEMA_NOME
from backend.utils.validadores import limpar_documento   # v1.9.1 - CPF/CNPJ (CNPJ alfanumerico) so pela funcao central
from backend.utils.log_operacoes import registrar_operacao, registrar_item
from backend.utils.blockchain import (registrar_evento_animal, TIPO_ABATE as TIPO_EVENTO_ABATE, TIPO_TRANSFERENCIA as TIPO_EVENTO_TRANSFER,   # v1.8.0 / v1.9.0 - blockchain
                                      TIPO_VENDA as TIPO_EVENTO_VENDA, TIPO_POSSE as TIPO_EVENTO_POSSE, TIPO_ENTRADA as TIPO_EVENTO_ENTRADA)
from types import SimpleNamespace
from backend.utils.entrada_comunicada import motivo_entrada_pendente   # v1.2.0

saida_comunicado = Blueprint('saida_comunicado', __name__)

SENTIDO_SAIDA = 'SAIDA'
TIPO_ABATE = 'ABATE'
TIPO_TRANSFER = 'TRANSFER'                # tipo_saida da Transferencia
TIPO_MOV_TRANSFER = 'TRANSFERENCIA'      # tipo_movimento da GTA / tipo_entrada
TIPO_VENDA = 'VENDA'                      # s111 - tipo_saida da Venda (destino vem da GTA, sempre OUTRO Produtor)
TIPO_MOV_VENDA = 'VENDA'                  # tipo_movimento da GTA de Venda / negociacao da saida
TIPO_MOV_COMPRA = 'COMPRA'                # s111 - a Entrada do comprador (na base) cai como COMPRA
TIPO_POSSE = 'POSSE'                      # s115 - tipo_saida da Alteracao de Posse (mesma Propriedade, muda o Produtor)
TIPO_MOV_POSSE = 'POSSE'                  # s115 - tipo_movimento da DTA / tipo_entrada / negociacao
TIPOS_COM_DESTINO = (TIPO_TRANSFER, TIPO_VENDA, TIPO_POSSE)
MOV_DO_TIPO = {TIPO_ABATE: 'ABATE', TIPO_TRANSFER: TIPO_MOV_TRANSFER, TIPO_VENDA: TIPO_MOV_VENDA, TIPO_POSSE: TIPO_MOV_POSSE}
ROTULO_DO_TIPO = {TIPO_ABATE: 'Abate', TIPO_TRANSFER: 'Transferência', TIPO_VENDA: 'Venda', TIPO_POSSE: 'Alteração de Posse'}
CARGOS_POSSE = ('TITULAR', 'ADMINISTRADOR')   # s115 - so Titular e Administrador geram a Alteracao de Posse
MOTIVOS_POSSE = ('VENDA', 'HERANCA')
MAXIMO_JUSTIFICATIVA_POSSE = 2000
MAXIMO_GTAS_POR_COMUNICADO = 6
TAMANHO_NUMERO_COMUNICADO_2017 = 6     # tb_2017.numero_comunicado e texto de 6 digitos
TAMANHO_GTA_2002 = 10                  # tb_2002/tb_2011/tb_2017: numero da GTA cabe em 10 caracteres
CLASSE_TRAVA = 2011                    # 1o numero da trava: so Comunicado de Saida (nao trava a Entrada)
MODULO_LOG = 'saida_comunicado'
MODULO_LOG_EXTERNO = 'saida_comunicado_externo'   # v1.4.0: Entrada em schema de outro Produtor (so historico)

URL_INICIAR = '/produtor/saida-comunicado/iniciar'
URL_CONFERENCIA = '/produtor/saida-comunicado/conferencia'
URL_GERAR = '/produtor/saida-comunicado/gerar'
CHAVE_MENSAGEM = 'msg_saida_comunicado'


# =========================================================
# BLOCO 1 - Funcoes de apoio
# =========================================================

def _numero_6(numero):
    """457 -> '000457'."""
    return str(numero).zfill(TAMANHO_NUMERO_COMUNICADO_2017)


def _linha_para_dict(obj):
    """Linha inteira do banco como dicionario simples (para o Log guardar o animal apagado)."""
    saida = {}
    for coluna in obj.__table__.columns:
        valor = getattr(obj, coluna.key)
        if valor is None:
            saida[coluna.key] = None
        elif isinstance(valor, (datetime, date, time)):
            saida[coluna.key] = valor.isoformat()
        elif isinstance(valor, Decimal):
            saida[coluna.key] = str(valor)
        elif isinstance(valor, (bool, int, float, str)):
            saida[coluna.key] = valor
        else:
            saida[coluna.key] = str(valor)
    return saida


def _dados_frigorifico(id_frigorifico):
    """(nome, cpf_cnpj) do frigorifico (tabela publica), ou (None, None)."""
    if not id_frigorifico:
        return None, None
    with Session(engine) as dbp:
        f = dbp.get(Frigorifico, int(id_frigorifico))
        if f is None:
            return None, None
        return f.nome, f.cpf_cnpj


def _bloqueio_da_gta(gta, qtd_vinculados, tipo=TIPO_ABATE):
    """Motivo (texto) pelo qual a GTA nao entra em Comunicado agora; ou None. Data futura PODE."""
    if gta.data_saida is None:
        return 'sem Data de Saída'
    if gta.data_validade is not None and gta.data_saida > gta.data_validade:   # v1.2.0
        return 'Data de Saída depois do vencimento da GTA'
    if tipo in TIPOS_COM_DESTINO:
        if gta.id_parceiro_propriedade is None:
            return ('sem comprador da Venda' if tipo == TIPO_VENDA
                    else ('sem Produtor de destino da Posse' if tipo == TIPO_POSSE else 'sem destino da Transferência'))
    elif gta.id_frigorifico is None:
        return 'sem frigorífico'
    if qtd_vinculados != gta.qtde_animais:
        return f'{qtd_vinculados} animal(is) vinculado(s) e a GTA tem {gta.qtde_animais}'
    if len(gta.numero_gta_completo or '') > TAMANHO_GTA_2002:
        return 'número da GTA maior que o campo do Comunicado'
    return None


@contextmanager
def _no_schema_do_destino(db, schema_nome):
    """
    v1.4.0 - Posiciona a MESMA sessao (mesma transacao) no schema do Produtor de destino e devolve ao schema de origem no fim.
    O flush antes e depois garante que cada INSERT caia no schema certo. So aceita schema no formato produtor_NNNNN.
    """
    if not schema_nome or not PADRAO_SCHEMA_NOME.match(schema_nome):
        raise ValueError('Schema do destino inválido.')
    anterior = db.execute(text('SHOW search_path')).scalar()
    db.flush()
    db.execute(text(f'SET LOCAL search_path TO {schema_nome}, public'))
    try:
        yield
    finally:
        db.flush()
        db.execute(text(f'SET LOCAL search_path TO {anterior}'))


def _inserir_no_destino(db, Modelo, campos):
    """
    v1.4.0 - INSERT direto (Core) no schema onde a sessao esta posicionada, devolvendo o id novo. Usado so na Transferencia entre
    Produtores: objeto ORM novo poderia ter o MESMO id de um objeto da origem ja carregado na sessao (as sequencias de cada schema
    sao independentes) e o SQLAlchemy recusaria. 'campos' usa os nomes dos atributos do modelo.
    """
    tabela = Modelo.__table__
    colunas = {a.key: a.columns[0].name for a in sa_inspect(Modelo).column_attrs}
    valores = {colunas[k]: v for k, v in campos.items()}
    return db.execute(tabela.insert().values(**valores).returning(tabela.c.id)).scalar_one()


def _so_digitos(texto):
    """v1.5.0 - So os digitos do texto (CPF/CNPJ e codigos chegam com ou sem pontuacao)."""
    return ''.join(c for c in (texto or '') if c.isdecimal())


def _garantir_parceiro_origem(db, produtor, prop_origem, com_pp=False):
    """
    v1.5.0 - Parceiro que representa o Produtor de ORIGEM no schema do destino (Transferencia entre Produtores). Chamar DENTRO do
    _no_schema_do_destino. Usa Core (sem ORM): objetos de dois schemas na mesma sessao podem ter o mesmo id. Procura o Parceiro pelo
    CPF/CNPJ (so digitos) e reaproveita; se nao existir, cria. Garante tambem a Propriedade de origem do Parceiro (chave: OESA, 11 digitos;
    sem OESA, o nome). O Parceiro nasce SEM id_produtor: o vinculo so se faz por confirmacao manual (regra do model, Benedito 30/10/2026).
    Devolve o id do Parceiro (e o que vai em id_origem).
    """
    cpf = limpar_documento(produtor.cpf_cnpj)   # v1.9.1 - mantem as letras do CNPJ alfanumerico
    tp = Parceiro.__table__
    tpp = ParceiroPropriedades.__table__
    agora = datetime.now()
    achado = db.execute(
        select(tp.c.id).where(func.regexp_replace(func.upper(tp.c.cpf_cnpj), '[^0-9A-Z]', '', 'g') == cpf).order_by(tp.c.id)
    ).first()
    if achado:
        id_parceiro = achado[0]
    else:
        id_parceiro = _inserir_no_destino(db, Parceiro, dict(
            cpf_cnpj=cpf, nome=(produtor.nome or '')[:150], ativo=True, criado_em=agora, atualizado_em=agora))
    if prop_origem is None:
        return (id_parceiro, None) if com_pp else id_parceiro

    # Propriedade de origem: OESA (11 primeiros digitos do codigo); sem OESA, o Codigo MAPA (15 digitos) vale pelos 11 primeiros.
    oesa = _so_digitos(prop_origem.oesa)[:11] or _so_digitos(prop_origem.codigo_mapa)[:11]
    nome_prop = (prop_origem.nome or '').strip()
    existentes = db.execute(
        select(tpp.c.codigo_mapa, tpp.c.estabelecimento, tpp.c.id).where(tpp.c.id_parceiro == id_parceiro)).all()
    for codigo, estabelecimento, id_pp_achado in existentes:
        if oesa:
            if _so_digitos(codigo)[:11] == oesa:
                return (id_parceiro, id_pp_achado) if com_pp else id_parceiro
        elif (estabelecimento or '').strip().upper() == nome_prop.upper():
            return (id_parceiro, id_pp_achado) if com_pp else id_parceiro
    id_pp_novo = _inserir_no_destino(db, ParceiroPropriedades, dict(
        id_parceiro=id_parceiro, estabelecimento=nome_prop[:150], codigo_mapa=oesa or None,
        insc_estadual=(prop_origem.inscricao_estadual or None) and prop_origem.inscricao_estadual[:20],
        municipio_codigo=(prop_origem.municipio_codigo or None) and prop_origem.municipio_codigo[:10],
        municipio_nome=(prop_origem.municipio or None) and prop_origem.municipio[:100],
        uf=prop_origem.uf, regiao=prop_origem.regiao, ativo=True, criado_em=agora, atualizado_em=agora))
    return (id_parceiro, id_pp_novo) if com_pp else id_parceiro


def _destino_transfer(db, id_parceiro_propriedade, id_propriedade_origem, id_produtor, tipo=TIPO_TRANSFER):
    """
    Destino da GTA de Transferencia (Parceiro + Propriedade do Parceiro, no schema do Produtor) conferido com a nossa base.
    Devolve dict: status, titulo, na_base (Entrada automatica), rotulo (texto do destino), cpf_cnpj, id_propriedade_destino,
    nome_propriedade_destino, motivo_bloqueio (None se pode gerar). None se o destino nao existe.
    """
    pp = db.get(ParceiroPropriedades, int(id_parceiro_propriedade)) if id_parceiro_propriedade else None
    parceiro = db.get(Parceiro, pp.id_parceiro) if pp else None
    if pp is None or parceiro is None:
        return None
    if tipo == TIPO_POSSE:   # s115 - mesma Propriedade (OESA), outro Produtor
        conf = conferir_destino_posse(id_propriedade_origem, id_produtor, parceiro.cpf_cnpj, pp.codigo_mapa, pp.insc_estadual, pp.uf)
    else:
        conf = conferir_destino(id_propriedade_origem, parceiro.cpf_cnpj, pp.codigo_mapa, pp.insc_estadual, pp.uf)
    status = conf['status']
    destino = {
        'status': status, 'titulo': conf['titulo'], 'na_base': status == NA_BASE,
        'rotulo': f'{pp.estabelecimento} — {parceiro.nome}'[:150], 'cpf_cnpj': parceiro.cpf_cnpj,
        'id_propriedade_destino': conf.get('id_propriedade_destino'),
        'id_produtor_destino': conf.get('id_produtor_destino'),   # v1.4.0
        'nome_propriedade_destino': conf.get('nome_propriedade_destino') or pp.estabelecimento,
        'motivo_bloqueio': None,
    }
    if status in (DIVERGENTE, MESMA_ORIGEM):
        destino['motivo_bloqueio'] = f'destino não confere: {conf["titulo"]}'
    elif status == NA_BASE and conf.get('id_produtor_destino') != id_produtor:
        # v1.4.0: outro Produtor da base e liberado, desde que esteja ativo e com schema pronto.
        produtor_dest = db.get(Produtor, conf.get('id_produtor_destino'))
        if (produtor_dest is None or not produtor_dest.ativo or not produtor_dest.schema_nome
                or not PADRAO_SCHEMA_NOME.match(produtor_dest.schema_nome)):
            destino['motivo_bloqueio'] = 'destino é de outro Produtor da nossa base, que está inativo ou ainda não está pronto para receber animais'
    return destino


def _bloqueio_venda(db, gta, destino, id_produtor):
    """
    s111 - Regras so da Venda: o comprador e SEMPRE outro Produtor; e, se ele esta na nossa base, a GTA ainda nao pode estar lancada na
    Entrada dele (a Entrada nasce como COMPRA com esta mesma GTA). Devolve o motivo (texto) ou None.
    """
    id_prod_dest = destino.get('id_produtor_destino')
    if id_prod_dest is not None and id_prod_dest == id_produtor:
        return 'Venda é para outro Produtor (para as suas Propriedades use a Transferência)'
    if destino['na_base'] and id_prod_dest is not None:
        produtor_dest = db.get(Produtor, id_prod_dest)
        if produtor_dest is not None and produtor_dest.schema_nome and PADRAO_SCHEMA_NOME.match(produtor_dest.schema_nome):
            tg = Gta.__table__
            with _no_schema_do_destino(db, produtor_dest.schema_nome):
                existe = db.execute(select(tg.c.id).where(
                    tg.c.uf_gta == gta.uf_gta, tg.c.serie_gta == gta.serie_gta,
                    tg.c.numero_gta_sequencial == gta.numero_gta_sequencial, tg.c.sentido == 'ENTRADA')).first()
            if existe:
                return 'o comprador já tem esta GTA lançada na Entrada dele'
    return None


def _bloqueio_posse(db, gta, destino, id_produtor, id_propriedade=None):
    """
    s115 - Regras so da Alteracao de Posse: o novo Produtor e SEMPRE outro Produtor da nossa base, na mesma Propriedade; e a DTA ainda nao
    pode estar lancada na Entrada dele (a Entrada nasce como POSSE com esta mesma DTA). Devolve o motivo (texto) ou None.
    """
    if id_propriedade is not None:   # s115 - toda Propriedade tem OESA; sem ele a DTA sairia sem Procedencia
        prop_origem = db.get(Propriedade, id_propriedade)
        if prop_origem is None or len(_so_digitos(prop_origem.oesa)) < 11:
            return 'a Propriedade não tem o Código OESA cadastrado (Minha Propriedade)'
    id_prod_dest = destino.get('id_produtor_destino')
    if not destino['na_base'] or id_prod_dest is None:
        return 'o novo Produtor precisa estar na nossa base, vinculado a esta Propriedade'
    if id_prod_dest == id_produtor:
        return 'Alteração de Posse é para outro Produtor'
    produtor_dest = db.get(Produtor, id_prod_dest)
    if produtor_dest is not None and produtor_dest.schema_nome and PADRAO_SCHEMA_NOME.match(produtor_dest.schema_nome):
        tg = Gta.__table__
        with _no_schema_do_destino(db, produtor_dest.schema_nome):
            existe = db.execute(select(tg.c.id).where(
                tg.c.uf_gta == gta.uf_gta, tg.c.serie_gta == gta.serie_gta,
                tg.c.numero_gta_sequencial == gta.numero_gta_sequencial, tg.c.sentido == 'ENTRADA')).first()
        if existe:
            return 'o novo Produtor já tem esta DTA lançada na Entrada dele'
    return None


def _montar_lotes(db, id_propriedade, travar, tipo=TIPO_ABATE):
    """
    Monta TODOS os Comunicados pendentes da Propriedade, de UM tipo (mesmo criterio na conferencia e no gerar).
    ABATE: GTAs de saida vinculadas e sem Comunicado -> grupos por (frigorifico, Data de Saida) -> lotes de ate 6.
    TRANSFER: idem, mas por (destino, Data de Saida); o destino e conferido com a nossa base (ver _destino_transfer).
    A mais antiga (emissao) primeiro. travar=True: trava as linhas (GTAs, leituras e animais) ate o commit.
    Devolve dict: lotes (lista de {tipo, id_frigorifico, destino, data_saida, gtas}), linhas_por_gta, entradas (por sisbov),
    bloqueadas (lista de (gta, motivo)).
    """
    transfer = (tipo in TIPOS_COM_DESTINO)
    resultado = {'lotes': [], 'linhas_por_gta': {}, 'entradas': {}, 'bloqueadas': []}

    filtro_linhas = db.query(Embarque).filter(
        *_filtro_abertas(id_propriedade, tipo), Embarque.id_gta.isnot(None)).order_by(Embarque.sisbov.asc())
    if travar:
        filtro_linhas = filtro_linhas.with_for_update()
    for l in filtro_linhas.all():
        resultado['linhas_por_gta'].setdefault(l.id_gta, []).append(l)
    if not resultado['linhas_por_gta']:
        return resultado

    consulta = db.query(Gta).filter(
        Gta.id.in_(list(resultado['linhas_por_gta'].keys())), Gta.id_propriedade == int(id_propriedade),
        Gta.sentido == SENTIDO_SAIDA, Gta.tipo_movimento == MOV_DO_TIPO[tipo],
        Gta.numero_comunicado.is_(None))
    if travar:
        consulta = consulta.with_for_update()
    gtas = consulta.all()

    sisbovs = [l.sisbov for g in gtas for l in resultado['linhas_por_gta'][g.id]]
    if sisbovs:
        consulta_e = db.query(Entrada).filter(Entrada.sisbov.in_(sisbovs))
        if travar:
            consulta_e = consulta_e.with_for_update()
        for e in consulta_e.all():
            resultado['entradas'][e.sisbov] = e

    id_produtor = session.get('id_produtor')
    nomes_frig = {}
    destinos = {}
    prontas = []
    for g in gtas:
        linhas = resultado['linhas_por_gta'][g.id]
        motivo = _bloqueio_da_gta(g, len(linhas), tipo)
        if transfer:
            if motivo is None and g.id_parceiro_propriedade not in destinos:
                destinos[g.id_parceiro_propriedade] = _destino_transfer(db, g.id_parceiro_propriedade, id_propriedade, id_produtor, tipo)
            if motivo is None and destinos[g.id_parceiro_propriedade] is None:
                motivo = 'destino não encontrado no cadastro de Parceiros'
            if motivo is None and destinos[g.id_parceiro_propriedade]['motivo_bloqueio']:
                motivo = destinos[g.id_parceiro_propriedade]['motivo_bloqueio']
            if motivo is None and tipo == TIPO_VENDA:   # s111
                motivo = _bloqueio_venda(db, g, destinos[g.id_parceiro_propriedade], id_produtor)
            if motivo is None and tipo == TIPO_POSSE:   # s115
                motivo = _bloqueio_posse(db, g, destinos[g.id_parceiro_propriedade], id_produtor, id_propriedade)
        else:
            if motivo is None and g.id_frigorifico not in nomes_frig:
                nomes_frig[g.id_frigorifico] = _dados_frigorifico(g.id_frigorifico)[0]
            if motivo is None and nomes_frig[g.id_frigorifico] is None:
                motivo = 'frigorífico não encontrado no cadastro'
        if motivo is None:
            faltando = [
                l.sisbov for l in linhas
                if resultado['entradas'].get(l.sisbov) is None
                or (resultado['entradas'][l.sisbov].id_propriedade is not None
                    and int(resultado['entradas'][l.sisbov].id_propriedade) != int(id_propriedade))
            ]
            if faltando:
                amostra = ', '.join(faltando[:3]) + (' ...' if len(faltando) > 3 else '')
                motivo = f'{len(faltando)} animal(is) não estão mais na Propriedade ({amostra})'
        if motivo is None:   # v1.2.0 - segunda trava: entrada ainda nao comunicada
            sem_entrada = [l.sisbov for l in linhas if motivo_entrada_pendente(db, resultado['entradas'][l.sisbov])]
            if sem_entrada:
                amostra = ', '.join(sem_entrada[:3]) + (' ...' if len(sem_entrada) > 3 else '')
                motivo = f'{len(sem_entrada)} animal(is) sem Comunicado de Entrada / Notificação gerada ({amostra})'
        if motivo:
            resultado['bloqueadas'].append((g, motivo))
        else:
            prontas.append(g)

    resultado['bloqueadas'].sort(key=lambda x: (x[0].data_emissao or date.min, x[0].id))

    def _chave_destino(g):
        if not transfer:
            return g.id_frigorifico
        d = destinos[g.id_parceiro_propriedade]
        if tipo == TIPO_POSSE:   # s115 - mesma Propriedade para todos: o que separa os Comunicados e o novo Produtor
            return ('P', d['id_propriedade_destino'], d.get('id_produtor_destino'))
        return ('P', d['id_propriedade_destino']) if d['na_base'] else ('X', g.id_parceiro_propriedade)

    grupos = {}
    for g in prontas:
        grupos.setdefault((g.data_saida, _chave_destino(g)), []).append(g)
    for (data_saida, chave) in sorted(grupos.keys(), key=lambda k: (k[0], str(k[1]))):
        lista = sorted(grupos[(data_saida, chave)], key=lambda g: (g.data_emissao or date.min, g.id))
        for inicio in range(0, len(lista), MAXIMO_GTAS_POR_COMUNICADO):
            parte = lista[inicio:inicio + MAXIMO_GTAS_POR_COMUNICADO]
            resultado['lotes'].append({
                'tipo': tipo,
                'id_frigorifico': None if transfer else chave,
                'destino': destinos[parte[0].id_parceiro_propriedade] if transfer else None,
                'data_saida': data_saida,
                'gtas': parte,
                'chave': '-'.join(str(g.id) for g in parte),   # s115 - identifica o lote nos campos da Posse
            })
    return resultado


def _guardar_mensagem(textos):
    session[CHAVE_MENSAGEM] = list(textos)


# =========================================================
# BLOCO 2 - Rotas
# =========================================================

# -------------------------------------------------------
# GET /produtor/saida-comunicado/iniciar
# -------------------------------------------------------
@saida_comunicado.route('/produtor/saida-comunicado/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista,
            erro=erro,
            titulo='Gerar Comunicado de Saída — Selecionar Propriedade',
            proximo=URL_CONFERENCIA,
            campo_propriedade='id_propriedade',
            voltar=URL_HUB,
            **_contexto_base(),
        )

    if len(pares) == 0:
        return _tela_selecionar([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')

    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{URL_CONFERENCIA}?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_CONFERENCIA}?id_propriedade={par.id_propriedade}')

    return _tela_selecionar(pares, None)


# -------------------------------------------------------
# Dados de um bloco (um tipo) para a tela de conferencia.
# -------------------------------------------------------
def _bloco_conferencia(db, sel, tipo, rotulo):
    lotes_tela = []
    total_animais = 0
    total_gtas = 0
    for lote in sel['lotes']:
        gtas_tela = []
        animais_lote = 0
        for g in lote['gtas']:
            animais = []
            for l in sel['linhas_por_gta'][g.id]:
                e = sel['entradas'][l.sisbov]
                animais.append({
                    'sisbov': l.sisbov,
                    'manejo': e.manejo or '-',
                    'sexo': 'Fêmea' if e.sexo == 'FEMEA' else ('Macho' if e.sexo == 'MACHO' else '-'),
                    'nascimento': _data_br(e.nascimento),
                    'peso': (f'{l.peso_saida:.2f}'.replace('.', ',') if l.peso_saida is not None else '-'),
                })
            animais_lote += len(animais)
            gtas_tela.append({
                'numero': g.numero_gta_completo,
                'emissao': _data_br(g.data_emissao),
                'validade': _data_br(g.data_validade),
                'qtde_gta': g.qtde_animais,
                'vinculados': len(animais),
                'animais': animais,
            })
        total_animais += animais_lote
        total_gtas += len(gtas_tela)
        destino = lote.get('destino')
        lotes_tela.append({
            'id_frigorifico': lote['id_frigorifico'],
            'data_saida': _data_br(lote['data_saida']),
            'futura': lote['data_saida'] > date.today(),
            'gtas': gtas_tela,
            'total_animais': animais_lote,
            'destino_rotulo': destino['rotulo'] if destino else None,
            'destino_cpf_cnpj': destino['cpf_cnpj'] if destino else None,
            'destino_na_base': bool(destino and destino['na_base']),
            'destino_nome_base': destino['nome_propriedade_destino'] if destino and destino['na_base'] else None,
            'chave': lote.get('chave'),
        })
    bloqueadas = [{
        'numero': g.numero_gta_completo,
        'data_saida': _data_br(g.data_saida) if g.data_saida else '-',
        'id_frigorifico': g.id_frigorifico,
        'motivo': motivo,
    } for g, motivo in sel['bloqueadas']]
    for lote in lotes_tela:
        if tipo in TIPOS_COM_DESTINO:
            lote['frigorifico'] = lote['destino_rotulo']
            lote['frigorifico_cnpj'] = lote['destino_cpf_cnpj'] or '-'
        else:
            lote['frigorifico'], lote['frigorifico_cnpj'] = _dados_frigorifico(lote['id_frigorifico'])
            lote['frigorifico_cnpj'] = lote['frigorifico_cnpj'] or '-'
    nomes = {}
    for b in bloqueadas:
        if tipo in TIPOS_COM_DESTINO:
            b['frigorifico'] = '-'
            continue
        if b['id_frigorifico'] not in nomes:
            nomes[b['id_frigorifico']] = _dados_frigorifico(b['id_frigorifico'])[0] or '-'
        b['frigorifico'] = nomes[b['id_frigorifico']]
    return {
        'tipo': tipo, 'rotulo': rotulo, 'transfer': tipo in TIPOS_COM_DESTINO, 'posse': tipo == TIPO_POSSE,
        'lotes': lotes_tela, 'bloqueadas': bloqueadas,
        'total_animais': total_animais, 'total_gtas': total_gtas,
        'tem_algo': bool(lotes_tela or bloqueadas),
    }


# -------------------------------------------------------
# GET /produtor/saida-comunicado/conferencia - mostra os Comunicados que serao gerados (nao grava nada).
# v1.3.0: blocos por tipo (Abate, Transferencia); so aparece o bloco que tem GTA pendente.
# -------------------------------------------------------
@saida_comunicado.route('/produtor/saida-comunicado/conferencia')
def conferencia():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_produtor = session['id_produtor']

    with get_db_produtor(id_produtor) as db:
        blocos = [
            _bloco_conferencia(db, _montar_lotes(db, id_propriedade, travar=False, tipo=TIPO_ABATE), TIPO_ABATE, 'Abate'),
            _bloco_conferencia(db, _montar_lotes(db, id_propriedade, travar=False, tipo=TIPO_TRANSFER), TIPO_TRANSFER, 'Transferência'),
            _bloco_conferencia(db, _montar_lotes(db, id_propriedade, travar=False, tipo=TIPO_VENDA), TIPO_VENDA, 'Venda'),   # s111
            _bloco_conferencia(db, _montar_lotes(db, id_propriedade, travar=False, tipo=TIPO_POSSE), TIPO_POSSE, 'Alteração de Posse'),   # s115
        ]
    blocos = [b for b in blocos if b['tem_algo']]
    total_animais = sum(b['total_animais'] for b in blocos)
    total_gtas = sum(b['total_gtas'] for b in blocos)
    total_lotes = sum(len(b['lotes']) for b in blocos)

    mensagens = session.pop(CHAVE_MENSAGEM, None) or []
    produtor_nome, propriedade_nome, propriedade_local = _nomes(id_propriedade, id_produtor)
    return render_template(
        'produtor/saida_comunicado_conferencia.html',
        blocos=blocos,
        mensagens=mensagens,
        total_animais=total_animais,
        total_gtas=total_gtas,
        total_lotes=total_lotes,
        maximo=MAXIMO_GTAS_POR_COMUNICADO,
        id_propriedade=int(id_propriedade),
        url_gerar=URL_GERAR,
        produtor_nome=produtor_nome,
        propriedade_nome=propriedade_nome,
        propriedade_local=propriedade_local,
        url_voltar=URL_HUB,
        **_contexto_base(),
    )


# -------------------------------------------------------
# v1.3.0 - UM lote de Transferencia: Saida na origem e, se o destino e da nossa base, Entrada no destino. Chamado dentro da
# transacao do gerar() (tudo ou nada). Devolve o dicionario da tela de sucesso.
# -------------------------------------------------------
def _gerar_lote_transfer(db, id_propriedade, nome_origem, produtor, lote, sel, posse_dados=None):
    destino = lote['destino']
    tipo_lote = lote.get('tipo') or TIPO_TRANSFER
    venda = (tipo_lote == TIPO_VENDA)             # s111: Venda = Transferencia com tipo VENDA e Entrada como COMPRA
    posse = (tipo_lote == TIPO_POSSE)             # s115: Alteracao de Posse = mesma Propriedade, outro Produtor; Entrada POSSE, sem tb_2012
    posse_motivo, posse_justificativa = (posse_dados or {}).get(lote.get('chave'), (None, None))
    rotulo_tipo = ROTULO_DO_TIPO[tipo_lote]
    tipo_ent_dest = TIPO_MOV_POSSE if posse else (TIPO_MOV_COMPRA if venda else TIPO_MOV_TRANSFER)
    negociacao_saida = TIPO_MOV_POSSE if posse else (TIPO_MOV_VENDA if venda else TIPO_MOV_TRANSFER)
    na_base = bool(destino['na_base'])
    id_dest = destino['id_propriedade_destino'] if na_base else None
    data_saida = lote['data_saida']
    nome_destino = (destino['nome_propriedade_destino'] if (na_base and not posse) else destino['rotulo']) or ''
    cpf_origem = produtor.cpf_cnpj if produtor else None

    # v1.4.0 - destino em OUTRO Produtor: a Entrada e gravada no schema dele, na mesma transacao.
    id_produtor_dest = destino.get('id_produtor_destino') if na_base else None
    externo = bool(na_base and id_produtor_dest and produtor and id_produtor_dest != produtor.id)
    produtor_dest = db.get(Produtor, id_produtor_dest) if externo else None
    if externo:
        ctx_destino = lambda: _no_schema_do_destino(db, produtor_dest.schema_nome)   # noqa: E731
        cpf_destino = produtor_dest.cpf_cnpj
    else:
        ctx_destino = nullcontext
        cpf_destino = cpf_origem
    modulo_log = MODULO_LOG_EXTERNO if externo else MODULO_LOG
    if posse and not externo:
        raise ValueError('Alteração de Posse exige outro Produtor da nossa base.')

    # ---- numero da SAIDA: sequencia propria da Transferencia, por Propriedade de origem ----
    maximo = (db.query(func.max(ComunicadoSaida.numero_comunicado))
              .filter(ComunicadoSaida.id_propriedade_origem == id_propriedade,
                      ComunicadoSaida.tipo_saida == tipo_lote).scalar())
    numero = (maximo or 0) + 1
    numero_6 = _numero_6(numero)

    # ---- numero da ENTRADA: sequencia propria da Transferencia, por Propriedade de destino ----
    numero_e = numero_e_6 = None
    if posse:   # s115 - sem Comunicado de Entrada (tb_2012): o Comunicado de Posse e o proprio documento; o animal leva o mesmo numero
        numero_e, numero_e_6 = numero, numero_6
    elif na_base:
        with ctx_destino():
            maximo_e = (db.query(func.max(ComunicadoEntrada.numero_comunicado))
                        .filter(ComunicadoEntrada.id_propriedade_destino == int(id_dest),
                                ((ComunicadoEntrada.tipo_entrada != TIPO_MOV_TRANSFER) if venda   # Compra: sequencia da Compra (a da Transferencia e separada)
                                 else (ComunicadoEntrada.tipo_entrada == TIPO_MOV_TRANSFER))).scalar())
        numero_e = (maximo_e or 0) + 1
        numero_e_6 = _numero_6(numero_e)

    # v1.5.0 - Entrada em OUTRO Produtor: o Parceiro que representa o Produtor de origem (e a Propriedade dele) no schema do destino.
    # Mesmo Produtor: id_origem continua vazio (a origem e outra fazenda dele mesmo).
    id_origem_dest = None
    id_pp_origem_dest = None
    if externo:
        prop_origem = db.get(Propriedade, int(id_propriedade))
        with ctx_destino():
            if venda or posse:
                id_origem_dest, id_pp_origem_dest = _garantir_parceiro_origem(db, produtor, prop_origem, com_pp=True)
            else:
                id_origem_dest = _garantir_parceiro_origem(db, produtor, prop_origem)

    numeros_gta = [g.numero_gta_completo for g in lote['gtas']]
    total_lote = sum(len(sel['linhas_por_gta'][g.id]) for g in lote['gtas'])
    id_operacao = registrar_operacao(
        db, id_usuario=session['usuario_id'], id_propriedade=id_propriedade, modulo=modulo_log,
        descricao=(f'Comunicado de {rotulo_tipo} nº {numero_6} — GTA {", ".join(numeros_gta)} — {total_lote} animal(is) — '
                   f'Data de Saída {_data_br(data_saida)} — {nome_destino}'
                   + ((' — Entrada automática no novo Produtor' if posse else f' — Entrada nº {numero_e_6}') if na_base else ' — destino fora da base')
                   + (f' — Motivo {posse_motivo}' if posse else ''))[:255])

    for g in lote['gtas']:
        linhas = sel['linhas_por_gta'][g.id]

        # ---- tb_2011: 1 linha por GTA, mesmo numero ----
        comunicado = ComunicadoSaida(
            id_propriedade_origem=id_propriedade, cpf_cnpj_produtor_origem=cpf_origem,
            numero_comunicado=numero, tipo_saida=tipo_lote,
            id_gta=g.id, gta_numero=g.numero_gta_completo, gta_data_emissao=g.data_emissao, gta_data_validade=g.data_validade,
            data_saida=data_saida, qtd_animais=len(linhas),
            id_frigorifico=None, cpf_cnpj_destino=destino['cpf_cnpj'],
            id_propriedade_destino=int(id_dest) if na_base else None,
            motivo_posse=posse_motivo if posse else None,
            justificativa_posse=posse_justificativa if posse else None,
            status='ABERTO',
        )
        db.add(comunicado)
        db.flush()
        registrar_item(db, id_operacao, 'tb_2011_com_saidas', comunicado.id, 'INSERT', None,
                       {'numero_comunicado': numero, 'tipo_saida': tipo_lote, 'gta_numero': g.numero_gta_completo})

        # ---- tb_2012: Comunicado de Entrada do destino (ja ABERTO; o destino so imprime) ----
        id_gta_destino = g.id   # no mesmo schema e a propria GTA; em outro Produtor, e a COPIA dela no schema do destino
        if posse:   # s115 - sem tb_2012; a DTA vai como COPIA de ENTRADA ja comunicada na propriedade do novo Produtor (que e a mesma)
            with ctx_destino():
                campos_gta = {a.key: getattr(g, a.key) for a in sa_inspect(Gta).column_attrs if a.key != 'id'}
                campos_gta.update(id_propriedade=int(id_dest), sentido='ENTRADA', tipo_movimento=TIPO_MOV_POSSE,
                                  id_parceiro_propriedade=id_pp_origem_dest, id_frigorifico=None, numero_comunicado=numero,
                                  data_entrega=data_saida, status_brincagem='BRINCADO')
                id_gta_destino = _inserir_no_destino(db, Gta, campos_gta)
        elif na_base:
            campos_ce = dict(
                id_propriedade_destino=int(id_dest),
                cpf_cnpj_produtor_destino=cpf_destino,         # v1.4.0: CPF/CNPJ do Produtor DESTINO (igual a origem quando e o mesmo)
                numero_comunicado=numero_e,
                gta_numero=g.numero_gta_completo,
                gta_data_emissao=g.data_emissao, gta_data_validade=g.data_validade,
                data_brincagem=None, gta_data_entrega=data_saida,   # Data de Entrada = Data de Saida
                qtd_animais=len(linhas),
                data_liberacao_abate=sel['entradas'][linhas[0].sisbov].liberacao_abate if linhas else None,
                id_parceiro_propriedade=(id_pp_origem_dest if venda else None),   # Transferencia: a origem e uma Propriedade nossa (GTA -> id_propriedade); Venda (COMPRA): o Parceiro de origem
                cpf_cnpj_produtor_origem=cpf_origem,
                tipo_entrada=tipo_ent_dest, status='ABERTO',
            )
            if externo:
                # Outro schema: INSERT direto (ver _inserir_no_destino). A GTA vai como COPIA de referencia.
                with ctx_destino():
                    campos_gta = {a.key: getattr(g, a.key) for a in sa_inspect(Gta).column_attrs if a.key != 'id'}
                    campos_gta.update(id_parceiro_propriedade=None, id_frigorifico=None, numero_comunicado=None)
                    if venda:   # s111: no comprador a GTA e uma GTA de ENTRADA (Compra), ja comunicada, da propriedade dele
                        campos_gta.update(id_propriedade=int(id_dest), sentido='ENTRADA', tipo_movimento=TIPO_MOV_COMPRA,
                                          id_parceiro_propriedade=id_pp_origem_dest, numero_comunicado=numero_e,
                                          data_entrega=data_saida, status_brincagem='BRINCADO')
                    id_gta_destino = _inserir_no_destino(db, Gta, campos_gta)
                    _inserir_no_destino(db, ComunicadoEntrada, dict(campos_ce, id_gta=id_gta_destino))
            else:
                entrada_com = ComunicadoEntrada(id_gta=g.id, **campos_ce)
                db.add(entrada_com)
                db.flush()
                registrar_item(db, id_operacao, 'tb_2012_com_entrada', entrada_com.id, 'INSERT', None,
                               {'numero_comunicado': numero_e, 'tipo_entrada': TIPO_MOV_TRANSFER, 'gta_numero': g.numero_gta_completo})

        for l in linhas:
            e = sel['entradas'][l.sisbov]
            dados_e = dict(
                sisbov=e.sisbov, manejo=e.manejo, rfid=e.rfid, id_especie=e.id_especie, sexo=e.sexo, nascimento=e.nascimento,
                eras_dias=e.eras_dias, id_raca=e.id_raca, id_aptidao=e.id_aptidao, cota_hilton=e.cota_hilton,
                liberacao_abate=e.liberacao_abate, brincos=e.brincos, lote=(None if posse else e.lote), data_brincagem=e.data_brincagem)   # Posse: lote nao tem sentido no destino

            # ---- tb_2002: o animal depois da saida ----
            saida = SaidaAnimal(
                id_propriedade=id_propriedade, id_animal=e.id, id_embarque=l.id,
                sisbov=e.sisbov, manejo=e.manejo, rfid=e.rfid,
                id_especie=e.id_especie, sexo=e.sexo, nascimento=e.nascimento, eras_dias=e.eras_dias,
                id_aptidao=e.id_aptidao, id_raca=e.id_raca, cota_hilton=e.cota_hilton,
                liberacao_abate=e.liberacao_abate,
                gta_entrada=l.gta_entrada, gta_entrada_emissao=l.gta_entrada_emissao,
                gta_entrada_validade=l.gta_entrada_validade, gta_entrada_animais=l.gta_entrada_animais,
                data_inclusao=e.data_inclusao, lote_entrada=e.lote or l.lote_entrada,
                origem_propriedade=l.origem_propriedade, origem_cpf_cnpj=l.origem_cpf_cnpj,
                tipo_saida=tipo_lote,
                gta_saida=g.numero_gta_completo, gta_saida_emissao=g.data_emissao,
                gta_saida_validade=g.data_validade, gta_saida_animais=g.qtde_animais,
                id_gta=g.id, id_frigorifico=None,
                destino_propriedade=nome_destino[:150], destino_cpf_cnpj=destino['cpf_cnpj'],
                data_embarque=l.data_embarque, data_saida=data_saida, numero_comunicado=numero,
                lote_saida=l.lote_saida, peso_saida=l.peso_saida, elemento=l.elemento,
            )
            db.add(saida)

            # ---- tb_2017: NOVA linha de saida (retrato do animal na tb_2001 agora) ----
            data_entrega_entrada = None
            if e.id_gta_entrada:
                gta_ent = db.get(Gta, e.id_gta_entrada)
                data_entrega_entrada = gta_ent.data_entrega if gta_ent else None
            movimentacao = Movimentacao(
                id_animal=e.id, id_propriedade=id_propriedade, sisbov=e.sisbov, manejo=e.manejo, rfid=e.rfid,
                negociacao=negociacao_saida,
                brincos=e.brincos, id_especie=e.id_especie, sexo=e.sexo, nascimento=e.nascimento,
                dias=e.eras_dias, cota_hilton=e.cota_hilton, id_aptidao=e.id_aptidao,
                id_raca=e.id_raca, liberacao_abate=e.liberacao_abate,
                tipo_entrada=e.tipo_entrada,
                gta_entrada=l.gta_entrada, gta_entrada_emissao=l.gta_entrada_emissao,
                gta_entrada_validade=l.gta_entrada_validade, gta_entrada_animais=l.gta_entrada_animais,
                data_inclusao=e.data_inclusao, entrada=data_entrega_entrada,
                origem_propriedade=l.origem_propriedade, origem_cpf_cnpj=l.origem_cpf_cnpj,
                lote=e.lote, data_brincagem=e.data_brincagem,
                conferido_brete=e.conferido_brete, conferido_em=e.conferido_em,
                id_origem=e.id_origem, id_gta_entrada=e.id_gta_entrada,
                tipo_saida=tipo_lote,
                gta_saida=g.numero_gta_completo, gta_saida_emissao=g.data_emissao,
                gta_saida_validade=g.data_validade, gta_saida_animais=g.qtde_animais,
                destino_propriedade=nome_destino[:150], destino_cpf_cnpj=destino['cpf_cnpj'],
                data_movimentacao=data_saida, numero_comunicado=numero_6,
            )
            db.add(movimentacao)
            db.flush()

            # ---- Log + o animal sai da tb_2001 da origem (flush antes: o SISBOV e unico na tb_2001) ----
            registrar_item(db, id_operacao, 'tb_2001', e.id, 'DELETE', _linha_para_dict(e), None)
            registrar_item(db, id_operacao, 'tb_2002_saida_animais', saida.id, 'INSERT', None,
                           {'sisbov': saida.sisbov, 'numero_comunicado': numero})
            registrar_item(db, id_operacao, 'tb_2017_movimentacoes', movimentacao.id, 'INSERT', None,
                           {'sisbov': movimentacao.sisbov, 'numero_comunicado': numero_6})

            # ---- BLOCKCHAIN (v1.9.0) - evento da SAIDA (VENDA / TRANSFERENCIA / POSSE) na origem, ANTES do animal sair da tb_2001;
            # data do evento = Data de Saida. Sem nome/CPF do destino (dados pessoais ficam fora). ----
            registrar_evento_animal(
                db, e, (TIPO_EVENTO_POSSE if posse else (TIPO_EVENTO_VENDA if venda else TIPO_EVENTO_TRANSFER)),
                id_usuario=session['usuario_id'], id_operacao=id_operacao, ocorrido_em=data_saida,
                extras={'numero_comunicado_saida': numero_6, 'gta_saida': g.numero_gta_completo,
                        'data_saida': data_saida, 'peso_saida': l.peso_saida})

            db.delete(e)
            db.flush()

            # ---- ENTRADA no destino: tb_2001 + nova linha de entrada na tb_2017 ----
            if na_base:
                agora = datetime.now()
                campos_novo = dict(
                    **dados_e, tipo_entrada=tipo_ent_dest, id_gta_entrada=id_gta_destino,
                    data_inclusao=data_saida,                      # Data de Entrada = Data de Saida
                    id_propriedade=int(id_dest), numero_comunicado=numero_e,
                    conferido_brete=True, conferido_em=agora,      # lido no brete da origem
                    id_origem=id_origem_dest,                      # v1.5.0: Parceiro de origem (so entre Produtores)
                )

                def _campos_mov_entrada(id_animal):
                    return dict(
                        id_animal=id_animal, id_propriedade=int(id_dest), sisbov=dados_e['sisbov'], manejo=dados_e['manejo'], rfid=dados_e['rfid'],
                        negociacao=tipo_ent_dest,
                        brincos=dados_e['brincos'], id_especie=dados_e['id_especie'], sexo=dados_e['sexo'], nascimento=dados_e['nascimento'],
                        dias=dados_e['eras_dias'], cota_hilton=dados_e['cota_hilton'], id_aptidao=dados_e['id_aptidao'],
                        id_raca=dados_e['id_raca'], liberacao_abate=dados_e['liberacao_abate'],
                        tipo_entrada=tipo_ent_dest,
                        gta_entrada=(g.numero_gta_completo or '')[:10], gta_entrada_emissao=g.data_emissao,
                        gta_entrada_validade=g.data_validade, gta_entrada_animais=g.qtde_animais,
                        data_inclusao=data_saida, entrada=data_saida,
                        origem_propriedade=nome_origem[:150], origem_cpf_cnpj=cpf_origem,
                        lote=dados_e['lote'], data_brincagem=dados_e['data_brincagem'],
                        conferido_brete=True, conferido_em=agora,
                        id_origem=id_origem_dest, id_gta_entrada=id_gta_destino,
                        tipo_saida=None,
                        data_movimentacao=data_saida, numero_comunicado=numero_e_6,
                    )

                if externo:
                    with ctx_destino():
                        id_novo = _inserir_no_destino(db, Entrada, campos_novo)
                        _inserir_no_destino(db, Movimentacao, _campos_mov_entrada(id_novo))
                        # ---- BLOCKCHAIN (v1.9.0) - evento ENTRADA no schema do DESTINO (so se ele tem provedor ligado). id_operacao vazio:
                        # a numeracao de operacoes e por schema; o estorno dos dois lados fica para o Desfazer da Venda. ----
                        registrar_evento_animal(
                            db, SimpleNamespace(**campos_novo), TIPO_EVENTO_ENTRADA,
                            id_usuario=session['usuario_id'], id_operacao=None, ocorrido_em=data_saida, id_produtor_dono=id_produtor_dest,
                            extras={'numero_comunicado_entrada': numero_e_6, 'gta_entrada': g.numero_gta_completo})
                else:
                    novo = Entrada(**campos_novo)
                    db.add(novo)
                    db.flush()
                    mov_e = Movimentacao(**_campos_mov_entrada(novo.id))
                    db.add(mov_e)
                    db.flush()
                    registrar_item(db, id_operacao, 'tb_2001', novo.id, 'INSERT', None,
                                   {'sisbov': novo.sisbov, 'id_propriedade': int(id_dest), 'numero_comunicado': numero_e})
                    registrar_item(db, id_operacao, 'tb_2017_movimentacoes', mov_e.id, 'INSERT', None,
                                   {'sisbov': mov_e.sisbov, 'numero_comunicado': numero_e_6})
                    # ---- BLOCKCHAIN (v1.9.0) - evento ENTRADA no destino (mesmo Produtor), mesma operacao do Desfazer ----
                    registrar_evento_animal(
                        db, novo, TIPO_EVENTO_ENTRADA, id_usuario=session['usuario_id'], id_operacao=id_operacao, ocorrido_em=data_saida,
                        extras={'numero_comunicado_entrada': numero_e_6, 'gta_entrada': g.numero_gta_completo})

            # ---- tb_2020: leitura do brete fechada ----
            registrar_item(db, id_operacao, 'tb_2020_embarque', l.id, 'UPDATE',
                           {'sts': False, 'numero_comunicado': None}, {'sts': True, 'numero_comunicado': numero})
            l.sts = True
            l.numero_comunicado = numero
            if na_base:
                l.id_propriedade_destino = int(id_dest)

        # ---- tb_4001_gta (a GTA de Transferencia guarda o numero da SAIDA) ----
        registrar_item(db, id_operacao, 'tb_4001_gta', g.id, 'UPDATE', {'numero_comunicado': None}, {'numero_comunicado': numero})
        g.numero_comunicado = numero
        db.flush()

    return {
        'tipo': tipo_lote, 'rotulo_tipo': rotulo_tipo,
        'numero': numero_6, 'numero_entrada': (None if posse else numero_e_6),
        'frigorifico': nome_destino, 'destino_na_base': na_base,
        'data_saida': _data_br(data_saida), 'total_animais': total_lote,
        'gtas': [{'numero': g.numero_gta_completo, 'animais': len(sel['linhas_por_gta'][g.id])} for g in lote['gtas']],
    }


# -------------------------------------------------------
# POST /produtor/saida-comunicado/gerar - monta de novo e da a baixa de todos os Comunicados.
# Tudo ou nada: uma transacao so, com trava por Propriedade.
# -------------------------------------------------------
@saida_comunicado.route('/produtor/saida-comunicado/gerar', methods=['POST'])
def gerar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.form.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()
    id_propriedade = int(id_propriedade)
    id_produtor = session['id_produtor']
    url_conferencia = f'{URL_CONFERENCIA}?id_propriedade={id_propriedade}'

    if request.form.get('confirmo') != '1':
        _guardar_mensagem(['Marque a caixinha "Revisei os dados e confirmo" para gerar os Comunicados.'])
        return redirect(url_conferencia)

    with get_db_produtor(id_produtor) as db:
        # A trava vem ANTES de montar: quem chega depois espera e ja enxerga o que o primeiro gerou.
        db.execute(text('SELECT pg_advisory_xact_lock(:classe, :id_propriedade)'),
                   {'classe': CLASSE_TRAVA, 'id_propriedade': id_propriedade})

        sel = _montar_lotes(db, id_propriedade, travar=True)
        sel_t = _montar_lotes(db, id_propriedade, travar=True, tipo=TIPO_TRANSFER)   # v1.3.0
        sel_v = _montar_lotes(db, id_propriedade, travar=True, tipo=TIPO_VENDA)      # s111
        sel_p = _montar_lotes(db, id_propriedade, travar=True, tipo=TIPO_POSSE)      # s115
        if not sel['lotes'] and not sel_t['lotes'] and not sel_v['lotes'] and not sel_p['lotes']:
            _guardar_mensagem(['Não há GTA pronta para Comunicado agora. Pode ter sido gerado em outra tela.'])
            return redirect(url_conferencia)

        # v1.3.0 - trava dos destinos (numero do Comunicado de Entrada), sempre em ordem crescente: sem impasse entre dois cliques
        for id_dest in sorted({l['destino']['id_propriedade_destino'] for l in (sel_t['lotes'] + sel_v['lotes'] + sel_p['lotes']) if l['destino']['na_base']}):
            db.execute(text('SELECT pg_advisory_xact_lock(:id_propriedade)'), {'id_propriedade': int(id_dest)})

        # s115 - Alteracao de Posse: so Titular/Administrador; motivo (Venda/Heranca) e justificativa digitada de cada Comunicado
        posse_dados = {}
        if sel_p['lotes']:
            if session.get('usuario_cargo') not in CARGOS_POSSE:
                _guardar_mensagem(['A Alteração de Posse só pode ser gerada pelo Titular ou pelo Administrador.'])
                return redirect(url_conferencia)
            erros_posse = []
            for lote_p in sel_p['lotes']:
                motivo_p = (request.form.get('posse_motivo_' + lote_p['chave']) or '').strip().upper()
                just_p = (request.form.get('posse_just_' + lote_p['chave']) or '').strip()
                rotulo_p = f"DTA {', '.join(g.numero_gta_completo for g in lote_p['gtas'])}"
                if motivo_p not in MOTIVOS_POSSE:
                    erros_posse.append(f'{rotulo_p}: escolha o Motivo da Alteração de Posse (Venda ou Herança).')
                elif not just_p:
                    erros_posse.append(f'{rotulo_p}: digite a Justificativa.')
                elif len(just_p) > MAXIMO_JUSTIFICATIVA_POSSE:
                    erros_posse.append(f'{rotulo_p}: a Justificativa passa de {MAXIMO_JUSTIFICATIVA_POSSE} caracteres.')
                else:
                    posse_dados[lote_p['chave']] = (motivo_p, just_p)
            if erros_posse:
                _guardar_mensagem(erros_posse)
                return redirect(url_conferencia)

        produtor = db.get(Produtor, id_produtor)
        gerados = []   # tela de sucesso: numero, frigorifico, data, GTAs, animais

        for lote in sel['lotes']:
            frig_nome, frig_cnpj = _dados_frigorifico(lote['id_frigorifico'])
            data_saida = lote['data_saida']

            # ---- numero do Comunicado: maior da tb_2011 + 1 ----
            maximo_atual = (
                db.query(func.max(ComunicadoSaida.numero_comunicado))
                .filter(ComunicadoSaida.id_propriedade_origem == id_propriedade,
                        ComunicadoSaida.tipo_saida == TIPO_ABATE)   # v1.3.0: sequencia propria por tipo
                .scalar()
            )
            numero = (maximo_atual or 0) + 1
            numero_6 = _numero_6(numero)

            numeros_gta = [g.numero_gta_completo for g in lote['gtas']]
            total_lote = sum(len(sel['linhas_por_gta'][g.id]) for g in lote['gtas'])
            id_operacao = registrar_operacao(
                db, id_usuario=session['usuario_id'], id_propriedade=id_propriedade,
                modulo=MODULO_LOG,
                descricao=(f'Comunicado de Saída nº {numero_6} — GTA {", ".join(numeros_gta)} — '
                           f'{total_lote} animal(is) — Data de Saída {_data_br(data_saida)} — '
                           f'{frig_nome}')[:255])

            for g in lote['gtas']:
                linhas = sel['linhas_por_gta'][g.id]

                # ---- tb_2011: 1 linha por GTA, mesmo numero ----
                comunicado = ComunicadoSaida(
                    id_propriedade_origem=id_propriedade,
                    cpf_cnpj_produtor_origem=produtor.cpf_cnpj if produtor else None,
                    numero_comunicado=numero,
                    tipo_saida=TIPO_ABATE,
                    id_gta=g.id,
                    gta_numero=g.numero_gta_completo,
                    gta_data_emissao=g.data_emissao,
                    gta_data_validade=g.data_validade,
                    data_saida=data_saida,
                    qtd_animais=len(linhas),
                    id_frigorifico=g.id_frigorifico,
                    cpf_cnpj_destino=frig_cnpj,
                    status='ABERTO',
                )
                db.add(comunicado)
                db.flush()
                registrar_item(db, id_operacao, 'tb_2011_com_saidas', comunicado.id, 'INSERT', None,
                               {'numero_comunicado': numero, 'gta_numero': g.numero_gta_completo})

                # Data de Entrega da GTA de entrada do animal (tb_2017.entrada), por GTA de entrada.
                entregas = {}

                for l in linhas:
                    e = sel['entradas'][l.sisbov]

                    if e.id_gta_entrada not in entregas:
                        gta_entrada = db.get(Gta, e.id_gta_entrada) if e.id_gta_entrada else None
                        entregas[e.id_gta_entrada] = gta_entrada.data_entrega if gta_entrada else None
                    data_entrega_entrada = entregas[e.id_gta_entrada]

                    # ---- tb_2002: o animal depois da saida ----
                    saida = SaidaAnimal(
                        id_propriedade=id_propriedade, id_animal=e.id, id_embarque=l.id,
                        sisbov=e.sisbov, manejo=e.manejo, rfid=e.rfid,
                        id_especie=e.id_especie, sexo=e.sexo, nascimento=e.nascimento, eras_dias=e.eras_dias,
                        id_aptidao=e.id_aptidao, id_raca=e.id_raca, cota_hilton=e.cota_hilton,
                        liberacao_abate=e.liberacao_abate,
                        gta_entrada=l.gta_entrada, gta_entrada_emissao=l.gta_entrada_emissao,
                        gta_entrada_validade=l.gta_entrada_validade, gta_entrada_animais=l.gta_entrada_animais,
                        data_inclusao=e.data_inclusao, lote_entrada=e.lote or l.lote_entrada,
                        origem_propriedade=l.origem_propriedade, origem_cpf_cnpj=l.origem_cpf_cnpj,
                        tipo_saida=TIPO_ABATE,
                        gta_saida=g.numero_gta_completo, gta_saida_emissao=g.data_emissao,
                        gta_saida_validade=g.data_validade, gta_saida_animais=g.qtde_animais,
                        id_gta=g.id, id_frigorifico=g.id_frigorifico,
                        destino_propriedade=(frig_nome or '')[:150], destino_cpf_cnpj=frig_cnpj,
                        data_embarque=l.data_embarque, data_saida=data_saida, numero_comunicado=numero,
                        lote_saida=l.lote_saida, peso_saida=l.peso_saida, elemento=l.elemento,
                        aceite_fora_liberacao=l.aceite_fora_liberacao,
                        aceite_fora_liberacao_por=l.aceite_fora_liberacao_por,
                        aceite_fora_liberacao_em=l.aceite_fora_liberacao_em,
                        aceite_era_0_12=l.aceite_era_0_12, aceite_era_0_12_por=l.aceite_era_0_12_por,
                        aceite_era_0_12_em=l.aceite_era_0_12_em,
                    )
                    db.add(saida)

                    # ---- tb_2017: NOVA linha de saida (retrato do animal na tb_2001 agora) ----
                    movimentacao = Movimentacao(
                        id_animal=e.id, id_propriedade=id_propriedade, sisbov=e.sisbov,
                        manejo=e.manejo, rfid=e.rfid,
                        brincos=e.brincos, id_especie=e.id_especie, sexo=e.sexo, nascimento=e.nascimento,
                        dias=e.eras_dias, cota_hilton=e.cota_hilton, id_aptidao=e.id_aptidao,
                        id_raca=e.id_raca, liberacao_abate=e.liberacao_abate,
                        tipo_entrada=e.tipo_entrada,
                        gta_entrada=l.gta_entrada, gta_entrada_emissao=l.gta_entrada_emissao,
                        gta_entrada_validade=l.gta_entrada_validade, gta_entrada_animais=l.gta_entrada_animais,
                        data_inclusao=e.data_inclusao, entrada=data_entrega_entrada,
                        origem_propriedade=l.origem_propriedade, origem_cpf_cnpj=l.origem_cpf_cnpj,
                        lote=e.lote, data_brincagem=e.data_brincagem,
                        conferido_brete=e.conferido_brete, conferido_em=e.conferido_em,
                        id_origem=e.id_origem, id_gta_entrada=e.id_gta_entrada,
                        tipo_saida=TIPO_ABATE,
                        gta_saida=g.numero_gta_completo, gta_saida_emissao=g.data_emissao,
                        gta_saida_validade=g.data_validade, gta_saida_animais=g.qtde_animais,
                        destino_propriedade=(frig_nome or '')[:150], destino_cpf_cnpj=frig_cnpj,
                        data_movimentacao=data_saida, numero_comunicado=numero_6,
                    )
                    db.add(movimentacao)
                    db.flush()

                    # ---- Log: linha inteira do animal ANTES de sair da tb_2001 ----
                    registrar_item(db, id_operacao, 'tb_2001', e.id, 'DELETE', _linha_para_dict(e), None)
                    registrar_item(db, id_operacao, 'tb_2002_saida_animais', saida.id, 'INSERT', None,
                                   {'sisbov': saida.sisbov, 'numero_comunicado': numero})
                    registrar_item(db, id_operacao, 'tb_2017_movimentacoes', movimentacao.id, 'INSERT', None,
                                   {'sisbov': movimentacao.sisbov, 'numero_comunicado': numero_6})

                    # ---- BLOCKCHAIN (v1.8.0) - evento ABATE, gravado ANTES do animal sair da tb_2001 ----
                    registrar_evento_animal(
                        db, e, TIPO_EVENTO_ABATE, id_usuario=session['usuario_id'], id_operacao=id_operacao, ocorrido_em=data_saida,
                        extras={'numero_comunicado_saida': numero_6, 'gta_saida': g.numero_gta_completo,
                                'data_saida': data_saida, 'peso_saida': l.peso_saida})

                    # ---- tb_2001: o animal sai da Propriedade ----
                    db.delete(e)

                    # ---- tb_2020: leitura do brete fechada ----
                    registrar_item(db, id_operacao, 'tb_2020_embarque', l.id, 'UPDATE',
                                   {'sts': False, 'numero_comunicado': None},
                                   {'sts': True, 'numero_comunicado': numero})
                    l.sts = True
                    l.numero_comunicado = numero

                # ---- tb_4001_gta ----
                registrar_item(db, id_operacao, 'tb_4001_gta', g.id, 'UPDATE',
                               {'numero_comunicado': None}, {'numero_comunicado': numero})
                g.numero_comunicado = numero
                db.flush()

            # Tudo pronto para a tela de sucesso (nada e lido do banco depois do commit).
            gerados.append({
                'tipo': TIPO_ABATE, 'rotulo_tipo': 'Abate', 'numero_entrada': None,
                'numero': numero_6,
                'frigorifico': frig_nome,
                'data_saida': _data_br(data_saida),
                'total_animais': total_lote,
                'gtas': [{'numero': g.numero_gta_completo, 'animais': len(sel['linhas_por_gta'][g.id])}
                         for g in lote['gtas']],
            })

        # ---- v1.3.0: Transferencias (Saida na origem + Entrada automatica no destino, quando na base) ----
        with Session(engine) as dbp:
            prop_origem = dbp.get(Propriedade, id_propriedade)
        nome_origem = (prop_origem.nome if prop_origem else '') or ''
        for lote in sel_t['lotes']:
            gerados.append(_gerar_lote_transfer(db, id_propriedade, nome_origem, produtor, lote, sel_t))
        for lote in sel_v['lotes']:   # s111 - Vendas (Saida na origem + Entrada COMPRA no comprador, quando na base)
            gerados.append(_gerar_lote_transfer(db, id_propriedade, nome_origem, produtor, lote, sel_v))
        for lote in sel_p['lotes']:   # s115 - Alteracoes de Posse (Saida na origem + Entrada POSSE no novo Produtor, sem tb_2012)
            gerados.append(_gerar_lote_transfer(db, id_propriedade, nome_origem, produtor, lote, sel_p, posse_dados))

        total_geral = sum(c['total_animais'] for c in gerados)
        db.commit()

    return render_template(
        'produtor/saida_comunicado_sucesso.html',
        gerados=gerados,
        total_animais=total_geral,
        url_conferencia=url_conferencia,
        url_hub=URL_HUB,
        **_contexto_base(),
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\saida_comunicado.py
# =========================================================
