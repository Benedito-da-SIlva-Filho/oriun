# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\Orion\backend\utils
# MODULO: backend\utils\carga_animais.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-17 18:38 -03
# ATUALIZADO EM: 2026-11-19 12:10 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     CARGA de animais (Produtor novo, a partir do Extrato do MAPA) - MIOLO: regras, previa, gravacao e Desfazer.
#     So a Consiste usa (router carga_consiste.py). Decisoes do Benedito: ver Carga_Decisoes_Finais_17-11-2026 (Projeto).
#
#     PARTES:
#       1) PURA (sem banco, testada em testar_carga_validacao.py): validar_animais(), montar_previa().
#       2) BANCO: resolver_destino() (acha Produtor e Propriedade), racas_do_cadastro(), carga_existente(),
#          sisbov_ja_no_produtor(), gravar_carga() (transacao unica, quem chama faz o commit), listar_cargas(),
#          desfazer_carga().
#
#     ERROS (barram tudo): Produtor/Propriedade nao cadastrados; Carga ja feita na Propriedade; linha nao lida; totais do
#     cabecalho diferentes da lista; SISBOV repetido no arquivo ou ja existente no Produtor; DV invalido; raca desconhecida;
#     data impossivel; nascimento no futuro; nascimento depois da Data Inclusao.
#     ALERTAS (nao barram): Macho nascido antes de 2000; Femea com mais de 30 anos na data da Carga.
#
#     GRAVACAO: 1 GTA serie 'CAR' (numero_gta_completo 'CARGA', tipo_movimento CARGA, sentido ENTRADA, meio_transporte
#     'CARGA', datas = data da Carga) + N animais na tb_2001 (tipo_entrada CARGA, Data Inclusao do documento em
#     data_inclusao, ativos, sem lote) + N linhas na tb_2017. Sem Comunicado, sem Notificacao, sem blockchain, sem log de
#     Operacoes Recentes (o Desfazer da Carga e so da Consiste). O vinculo animal-Carga e o id_gta_entrada.
#     DEFAULTS que o Benedito pode vetar: liberacao_abate = Data Inclusao + 90 dias (mesma regra da Brincagem; sem isso o
#     Abate recusa o animal); cota_hilton = ESTIMADA (o Extrato nao traz: CTH se Data Inclusao - Nascimento <= DIAS_MAX_COTA_HILTON, a regra de
#     regras_sisbov.eh_cota_hilton; decisao do Benedito 19/11/2026); eras_dias = dias entre nascimento e a Carga;
#     manejo = 6 digitos derivados do SISBOV (regras_sisbov.manejo_do_sisbov); rfid, brincos e aptidao vazios.
#
#     DESFAZER: so se NENHUM animal da Carga tiver movimento depois (saida, pesagem, linkagem, RFID, outra linha na tb_2017).
#     Apaga tb_2017, tb_2001 e a GTA CAR; a Propriedade volta a poder receber uma nova Carga.
#
#   v1.0.0: Criacao (Carga, 17/11/2026).
#   v1.1.0: Sessao 133 (2026-11-19 12:10 -03) - Cota Hilton da Carga passa de False fixo para ESTIMADA: idade na Data de
#           Inclusao (Data Inclusao - Nascimento) pela mesma regra e limite da Brincagem (eh_cota_hilton, 306 dias). Vale na
#           tb_2001 e na tb_2017. eras_dias nao mudou. REVERSAO: .bak_antes_s133_cth.
# =========================================================

import re
import unicodedata
from datetime import date, datetime, timedelta

from sqlalchemy import text

from backend.models.produtor import Produtor
from backend.models.propriedade import Propriedade
from backend.models.propriedade_produtor import PropriedadeProdutor
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2017_movimentacoes import Movimentacao
from backend.models.tb_4001_gta import Gta
from backend.utils import regras_sisbov as rs

# -------------------------------------------------------
# Constantes (um lugar so para mudar)
# -------------------------------------------------------
TIPO_CARGA = 'CARGA'
SERIE_CARGA = 'CAR'
NUMERO_SEQUENCIAL_CARGA = '0000001'    # uma Carga por Propriedade: sempre o 1
NUMERO_COMPLETO_CARGA = 'CARGA'
MEIO_TRANSPORTE_CARGA = 'CARGA'
ANO_MINIMO_DATA = 1980                 # abaixo disso a data e impossivel (ex.: 1900)
ANO_MACHO_ANTIGO = 2000                # alerta: Macho nascido antes deste ano
IDADE_MAX_FEMEA_ANOS = 30              # alerta: Femea com mais anos que isso na data da Carga
DIAS_LIBERACAO_ABATE = 90              # liberacao_abate = Data Inclusao + N dias (mesma regra da Brincagem)
MAX_ANIMAIS_CARGA = 20000              # teto de seguranca (Regra #70)

TITULOS_ERRO = {
    'LINHA_NAO_LIDA':          'Linha do arquivo que o sistema não conseguiu ler',
    'TOTAL_DIVERGE':           'Total do cabeçalho diferente da quantidade de animais lidos',
    'SISBOV_REPETIDO_ARQUIVO': 'SISBOV repetido dentro do arquivo',
    'SISBOV_JA_NO_PRODUTOR':   'SISBOV que já existe no Produtor',
    'DV_INVALIDO':             'SISBOV com dígito verificador inválido',
    'RACA_DESCONHECIDA':       'Raça que não existe no cadastro do Orion',
    'SEXO_INVALIDO':           'Sexo inválido',
    'DATA_IMPOSSIVEL':         'Data impossível',
    'NASC_FUTURO':             'Nascimento no futuro',
    'NASC_DEPOIS_INCLUSAO':    'Nascimento depois da Data Inclusão',
    'ARQUIVO_VAZIO':           'Arquivo sem nenhum animal',
    'ARQUIVO_GRANDE':          'Arquivo com animais demais',
}
TITULOS_ALERTA = {
    'MACHO_ANTIGO': 'Macho nascido antes de %d' % ANO_MACHO_ANTIGO,
    'FEMEA_VELHA':  'Fêmea com mais de %d anos na data da Carga' % IDADE_MAX_FEMEA_ANOS,
}


# =========================================================
# 1) PARTE PURA
# =========================================================
def normalizar_nome(texto):
    """Raca comparada sem acento, sem maiuscula/minuscula e sem espaco duplicado."""
    sem_acento = unicodedata.normalize('NFKD', str(texto or ''))
    sem_acento = ''.join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', sem_acento).strip().upper()


def _br(d):
    return d.strftime('%d/%m/%Y') if d else ''


def _idade_em_anos(nascimento, referencia):
    return referencia.year - nascimento.year - ((referencia.month, referencia.day) < (nascimento.month, nascimento.day))


def _data_ok(data, hoje):
    """None se a data e utilizavel; senao devolve o codigo do erro."""
    if data is None or data.year < ANO_MINIMO_DATA:
        return 'DATA_IMPOSSIVEL'
    if data > hoje:
        return 'NASC_FUTURO'
    return None


def validar_animais(animais, cabecalho, racas_por_nome, hoje):
    """Valida a lista padrao. Devolve (erros, alertas); cada item e um dict com codigo, linha, sisbov e mensagem."""
    erros, alertas = [], []

    def erro(codigo, a, msg):
        erros.append({'codigo': codigo, 'linha': a.get('linha') if a else None,
                      'sisbov': a.get('sisbov') if a else '', 'mensagem': msg})

    if not animais:
        erro('ARQUIVO_VAZIO', None, 'O arquivo não tem nenhum animal. Confira se é o Extrato de Animais Vivos do MAPA e envie de novo.')
        return erros, alertas
    if len(animais) > MAX_ANIMAIS_CARGA:
        erro('ARQUIVO_GRANDE', None, f'O arquivo tem {len(animais)} animais; o limite da Carga é {MAX_ANIMAIS_CARGA}. Divida com a Consiste.')
        return erros, alertas

    vistos = {}
    for a in animais:
        sisbov = a['sisbov']
        # SISBOV repetido no arquivo
        if sisbov in vistos:
            erro('SISBOV_REPETIDO_ARQUIVO', a, f'SISBOV {sisbov} repetido (linhas {vistos[sisbov]} e {a["linha"]}). Corrija o Extrato no MAPA e envie de novo.')
        else:
            vistos[sisbov] = a['linha']
        # digito verificador
        if not rs.sisbov_confere(sisbov):
            erro('DV_INVALIDO', a, f'SISBOV {sisbov} com dígito verificador inválido (linha {a["linha"]}). Confira o número no MAPA.')
        # raca
        if normalizar_nome(a['raca_nome']) not in racas_por_nome:
            erro('RACA_DESCONHECIDA', a, f'Raça "{a["raca_nome"]}" não existe no cadastro do Orion (linha {a["linha"]}). Peça à Consiste para cadastrar a raça.')
        # sexo
        if a['sexo'] not in ('MACHO', 'FEMEA'):
            erro('SEXO_INVALIDO', a, f'Sexo "{a["sexo_texto"]}" inválido (linha {a["linha"]}).')
        # datas
        nasc, incl = a['nascimento'], a['data_inclusao']
        cod_n, cod_i = _data_ok(nasc, hoje), _data_ok(incl, hoje)
        if cod_n == 'DATA_IMPOSSIVEL':
            erro('DATA_IMPOSSIVEL', a, f'Nascimento "{a["nascimento_texto"]}" é uma data impossível (linha {a["linha"]}).')
        elif cod_n == 'NASC_FUTURO':
            erro('NASC_FUTURO', a, f'Nascimento {_br(nasc)} está no futuro (linha {a["linha"]}).')
        if cod_i is not None:
            erro('DATA_IMPOSSIVEL', a, f'Data Inclusão "{a["data_inclusao_texto"]}" é uma data impossível ou futura (linha {a["linha"]}).')
        if cod_n is None and cod_i is None and nasc > incl:
            erro('NASC_DEPOIS_INCLUSAO', a, f'Nascimento {_br(nasc)} é depois da Data Inclusão {_br(incl)} (linha {a["linha"]}).')
        # alertas (nao barram)
        if cod_n is None:
            if a['sexo'] == 'MACHO' and nasc.year < ANO_MACHO_ANTIGO:
                alertas.append({'codigo': 'MACHO_ANTIGO', 'linha': a['linha'], 'sisbov': sisbov,
                                'mensagem': f'Macho nascido em {_br(nasc)} (antes de {ANO_MACHO_ANTIGO}). Confira se está certo.'})
            if a['sexo'] == 'FEMEA' and _idade_em_anos(nasc, hoje) > IDADE_MAX_FEMEA_ANOS:
                alertas.append({'codigo': 'FEMEA_VELHA', 'linha': a['linha'], 'sisbov': sisbov,
                                'mensagem': f'Fêmea nascida em {_br(nasc)} (mais de {IDADE_MAX_FEMEA_ANOS} anos). Confira se está certo.'})

    # totais do cabecalho x lista
    tf, tm = cabecalho.get('total_femea'), cabecalho.get('total_macho')
    lf = sum(1 for a in animais if a['sexo'] == 'FEMEA')
    lm = sum(1 for a in animais if a['sexo'] == 'MACHO')
    if tf is not None and tm is not None and (tf, tm) != (lf, lm):
        erro('TOTAL_DIVERGE', None, f'O cabeçalho do Extrato diz {tf} fêmeas e {tm} machos, mas foram lidos {lf} fêmeas e {lm} machos. O arquivo pode estar incompleto: gere o Extrato de novo no MAPA.')
    return erros, alertas


def montar_previa(extrato, racas_por_nome, hoje, erros_extra=None):
    """Junta tudo numa previa pronta para a tela. erros_extra: erros que vem do banco (destino, Carga existente, SISBOV no Produtor)."""
    animais = extrato['animais']
    erros, alertas = validar_animais(animais, extrato['cabecalho'], racas_por_nome, hoje)
    for n in extrato.get('linhas_nao_lidas', []):
        erros.append({'codigo': 'LINHA_NAO_LIDA', 'linha': None, 'sisbov': '',
                      'mensagem': f'Linha não lida na página {n["pagina"]}: "{n["texto"]}". Gere o Extrato de novo no MAPA.'})
    erros = list(erros_extra or []) + erros

    def agrupar(itens, titulos):
        grupos = {}
        for i in itens:
            g = grupos.setdefault(i['codigo'], {'codigo': i['codigo'], 'titulo': titulos.get(i['codigo'], i['codigo']), 'qtd': 0, 'exemplos': []})
            g['qtd'] += 1
            if len(g['exemplos']) < 10:
                g['exemplos'].append(i['mensagem'])
        return list(grupos.values())

    return {
        'lidos': len(animais),
        'femeas': sum(1 for a in animais if a['sexo'] == 'FEMEA'),
        'machos': sum(1 for a in animais if a['sexo'] == 'MACHO'),
        'qtd_erros': len(erros),
        'qtd_alertas': len(alertas),
        'erros': agrupar(erros, TITULOS_ERRO),
        'alertas': agrupar(alertas, TITULOS_ALERTA),
        'pode_gravar': len(erros) == 0 and len(animais) > 0,
    }


# =========================================================
# 2) PARTE DO BANCO
# =========================================================
def _digitos(valor):
    return re.sub(r'[^0-9A-Za-z]', '', str(valor or '')).upper()


def resolver_destino(db, cabecalho):
    """Acha Produtor (pelo CPF/CNPJ do Extrato) e Propriedade (pelo codigo MAPA ou Nirf), com vinculo ativo.
    db = sessao no schema public. Devolve (produtor, propriedade, vinculo, erros)."""
    erros = []
    doc = _digitos(cabecalho.get('produtor_documento'))
    if not doc:
        return None, None, None, [{'codigo': 'PRODUTOR_NAO_CADASTRADO', 'linha': None, 'sisbov': '',
                                   'mensagem': 'O Extrato não traz CPF/CNPJ do Produtor. Confira o arquivo.'}]
    produtor = None
    for p in db.query(Produtor).filter(Produtor.ativo.is_(True)).all():
        principal = _digitos(p.cpf_cnpj)
        if str(p.tipo_pessoa or '').upper() == 'FISICA' and len(principal) == 14 and principal.startswith('000'):
            principal = principal[-11:]
        if principal == doc:
            produtor = p
            break
    # Propriedade: codigo MAPA ou Nirf/Incra (so digitos; zeros a esquerda nao contam)
    cod = _digitos(cabecalho.get('cod_propriedade')).lstrip('0')
    nirf = _digitos(cabecalho.get('nirf')).lstrip('0')
    propriedade = None
    for pr in db.query(Propriedade).filter(Propriedade.ativo.is_(True)).all():
        if (cod and _digitos(pr.codigo_mapa).lstrip('0') == cod) or (nirf and _digitos(pr.nirf_incra).lstrip('0') == nirf):
            propriedade = pr
            break
    if produtor is None:
        erros.append({'codigo': 'PRODUTOR_NAO_CADASTRADO', 'linha': None, 'sisbov': '',
                      'mensagem': f'Produtor "{cabecalho.get("produtor_nome")}" (CPF/CNPJ {cabecalho.get("produtor_documento")}) não está cadastrado no Orion. Cadastre o Produtor e envie de novo.'})
    if propriedade is None:
        erros.append({'codigo': 'PROPRIEDADE_NAO_CADASTRADA', 'linha': None, 'sisbov': '',
                      'mensagem': f'Propriedade "{cabecalho.get("propriedade_nome")}" (Cód. {cabecalho.get("cod_propriedade")} / Nirf {cabecalho.get("nirf")}) não está cadastrada no Orion. Cadastre a Propriedade e envie de novo.'})
    vinculo = None
    if produtor is not None and propriedade is not None:
        vinculo = (db.query(PropriedadeProdutor)
                   .filter(PropriedadeProdutor.id_propriedade == propriedade.id,
                           PropriedadeProdutor.id_produtor == produtor.id,
                           PropriedadeProdutor.data_fim.is_(None)).first())
        if vinculo is None:
            erros.append({'codigo': 'SEM_VINCULO', 'linha': None, 'sisbov': '',
                          'mensagem': f'O Produtor {produtor.nome} não está vinculado à Propriedade {propriedade.nome}. Faça o vínculo no cadastro e envie de novo.'})
    return produtor, propriedade, vinculo, erros


def racas_do_cadastro(db):
    """{nome normalizado: (id, codigo)} das racas ativas (public.tb_4005_racas)."""
    colunas = {c for (c,) in db.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tb_4005_racas'")).all()}
    col_nome = 'nome' if 'nome' in colunas else 'descricao'   # o catalogo ja teve as 2 grafias
    filtro = ' WHERE ativo IS TRUE' if 'ativo' in colunas else ''
    linhas = db.execute(text(f'SELECT id, codigo, {col_nome} FROM public.tb_4005_racas{filtro}')).all()
    return {normalizar_nome(n): (i, c) for (i, c, n) in linhas}


def id_especie_bovina(db):
    return db.execute(text("SELECT id FROM public.tb_4002_especie WHERE codigo = 'BOV'")).scalar()


def carga_existente(db, id_propriedade):
    """GTA CAR da Propriedade (db no schema do Produtor), ou None."""
    return db.query(Gta).filter(Gta.id_propriedade == id_propriedade, Gta.serie_gta == SERIE_CARGA).first()


def sisbov_ja_no_produtor(db, sisbovs):
    """SISBOV da lista que ja existe no Produtor (animal ativo, animal que saiu, brinco baixado ou brinco no estoque)."""
    lista = list(sisbovs)
    achados = set()
    for tabela in ('tb_2001', 'tb_2002_saida_animais', 'tb_3008_brincos_saida', 'tb_7017_entrada_brincos_rfid'):
        for (s,) in db.execute(text(f'SELECT sisbov FROM {tabela} WHERE sisbov = ANY(:l)'), {'l': lista}):
            achados.add(s)
    return sorted(achados)


def erros_do_banco(db_produtor, id_propriedade, animais):
    """Erros que dependem do schema do Produtor: Carga ja feita e SISBOV ja existente."""
    erros = []
    if carga_existente(db_produtor, id_propriedade) is not None:
        erros.append({'codigo': 'CARGA_JA_FEITA', 'linha': None, 'sisbov': '',
                      'mensagem': 'Esta Propriedade já recebeu a Carga. É uma Carga só por Propriedade; para refazer, desfaça a Carga atual primeiro.'})
    for s in sisbov_ja_no_produtor(db_produtor, [a['sisbov'] for a in animais]):
        erros.append({'codigo': 'SISBOV_JA_NO_PRODUTOR', 'linha': None, 'sisbov': s,
                      'mensagem': f'SISBOV {s} já existe neste Produtor (animal, saída ou brinco). Confira com a Consiste.'})
    return erros


TITULOS_ERRO.update({
    'PRODUTOR_NAO_CADASTRADO': 'Produtor não cadastrado no Orion',
    'PROPRIEDADE_NAO_CADASTRADA': 'Propriedade não cadastrada no Orion',
    'SEM_VINCULO': 'Produtor sem vínculo com a Propriedade',
    'CARGA_JA_FEITA': 'Esta Propriedade já recebeu a Carga',
})


def gravar_carga(db, id_propriedade, uf, animais, racas_por_nome, id_especie, data_carga, id_usuario, hash_arquivo=None, nome_arquivo=None):
    """Grava a Carga INTEIRA na sessao db (schema do Produtor) e devolve (id_gta, quantidade).
    NAO faz commit: quem chama commita (ou da rollback se der erro). Regra #71: trava da Propriedade ANTES e conferencia DENTRO."""
    # trava a Propriedade (duas Cargas ao mesmo tempo nao passam) e confere de novo dentro da trava
    db.execute(text('SELECT id FROM public.propriedades WHERE id = :i FOR UPDATE'), {'i': id_propriedade})
    if carga_existente(db, id_propriedade) is not None:
        raise ValueError('Esta Propriedade já recebeu a Carga.')

    observacao = f'Carga de animais (Extrato do MAPA) feita por usuário {id_usuario} em {datetime.now():%d/%m/%Y %H:%M}'
    if nome_arquivo:
        observacao += f'; arquivo {nome_arquivo[:80]}'
    gta = Gta(
        id_propriedade=id_propriedade, uf_gta=uf, serie_gta=SERIE_CARGA,
        numero_gta_sequencial=NUMERO_SEQUENCIAL_CARGA, numero_gta_completo=NUMERO_COMPLETO_CARGA,
        qtde_animais=len(animais), tipo_movimento=TIPO_CARGA, sentido='ENTRADA',
        data_emissao=data_carga, data_validade=data_carga, data_entrega=data_carga,
        meio_transporte=MEIO_TRANSPORTE_CARGA, observacoes=observacao, arquivo_pdf_hash=hash_arquivo,
    )
    db.add(gta)
    db.flush()

    entradas = []
    for a in animais:
        id_raca = racas_por_nome[normalizar_nome(a['raca_nome'])][0]
        e = Entrada(
            sisbov=a['sisbov'], manejo=rs.manejo_do_sisbov(a['sisbov']), rfid=None,
            id_especie=id_especie, sexo=a['sexo'], nascimento=a['nascimento'],
            eras_dias=(data_carga - a['nascimento']).days, id_raca=id_raca,
            id_aptidao=None, cota_hilton=rs.eh_cota_hilton((a['data_inclusao'] - a['nascimento']).days),   # v1.1.0: estimada
            liberacao_abate=a['data_inclusao'] + timedelta(days=DIAS_LIBERACAO_ABATE),
            tipo_entrada=TIPO_CARGA, brincos=None, id_gta_entrada=gta.id,
            data_inclusao=a['data_inclusao'], lote=None, id_origem=None,
            id_propriedade=id_propriedade, conferido_brete=True,
        )
        entradas.append((a, e))
    db.add_all([e for _, e in entradas])
    db.flush()

    movs = []
    for a, e in entradas:
        movs.append(Movimentacao(
            id_animal=e.id, id_propriedade=id_propriedade, sisbov=e.sisbov, manejo=e.manejo, rfid=None,
            negociacao=TIPO_CARGA, brincos=None, id_especie=id_especie, sexo=e.sexo, nascimento=e.nascimento,
            dias=e.eras_dias, cota_hilton=e.cota_hilton, id_aptidao=None, id_raca=e.id_raca, liberacao_abate=e.liberacao_abate,
            tipo_entrada=TIPO_CARGA, gta_entrada=NUMERO_COMPLETO_CARGA, gta_entrada_emissao=data_carga,
            gta_entrada_validade=data_carga, gta_entrada_animais=len(animais), data_inclusao=e.data_inclusao,
            entrada=data_carga, lote=None, data_brincagem=None, conferido_brete=True, conferido_em=None,
            id_origem=None, id_gta_entrada=gta.id, data_movimentacao=data_carga,
        ))
    db.add_all(movs)
    db.flush()
    return gta.id, len(entradas)


def listar_cargas(db):
    """Cargas do Produtor (db no schema dele): lista de dicts, mais nova primeiro."""
    gtas = db.query(Gta).filter(Gta.serie_gta == SERIE_CARGA).order_by(Gta.criado_em.desc()).all()
    return [{'id': g.id, 'id_propriedade': g.id_propriedade, 'quantidade': g.qtde_animais,
             'data': g.data_entrega, 'criado_em': g.criado_em, 'observacoes': g.observacoes} for g in gtas]


def _tabela_existe(db, nome):
    return db.execute(text('SELECT to_regclass(:n)'), {'n': nome}).scalar() is not None


def motivo_nao_desfaz(db, gta):
    """Texto do bloqueio se a Carga NAO pode ser desfeita (algum animal ja teve movimento depois), senao None."""
    animais = db.query(Entrada).filter(Entrada.id_gta_entrada == gta.id, Entrada.tipo_entrada == TIPO_CARGA).all()
    if len(animais) != gta.qtde_animais:
        return (f'A Carga tinha {gta.qtde_animais} animais e só {len(animais)} continuam na Propriedade '
                f'(os demais já tiveram saída). Não dá para desfazer.')
    sisbovs = [a.sisbov for a in animais]
    if any(a.rfid for a in animais):
        return 'Algum animal da Carga já recebeu RFID (Linkagem ou Troca de RFID). Não dá para desfazer.'
    checagens = [
        ('tb_2002_saida_animais', 'sisbov', None, 'saída'),
        ('tb_4003_pesos', 'sisbov', None, 'pesagem'),
        ('tb_4009_linkagem', 'sisbov', None, 'linkagem'),
        ('tb_2017_movimentacoes', 'sisbov', "NOT (tipo_entrada = 'CARGA' AND tipo_saida IS NULL)", 'movimentação'),
    ]
    for tabela, coluna, extra, nome in checagens:
        if not _tabela_existe(db, tabela):
            continue
        filtro = f'{coluna} = ANY(:l)' + (f' AND {extra}' if extra else '')
        qtd = db.execute(text(f'SELECT count(*) FROM {tabela} WHERE {filtro}'), {'l': sisbovs}).scalar()
        if qtd:
            return f'Há {qtd} registro(s) de {nome} depois da Carga. Não dá para desfazer.'
    return None


def desfazer_carga(db, id_gta):
    """Desfaz a Carga (db no schema do Produtor). Devolve (ok, mensagem). NAO faz commit."""
    gta = db.get(Gta, id_gta, with_for_update=True)
    if gta is None or gta.serie_gta != SERIE_CARGA:
        return False, 'Carga não encontrada.'
    motivo = motivo_nao_desfaz(db, gta)
    if motivo:
        return False, motivo
    qtd = gta.qtde_animais
    db.query(Movimentacao).filter(Movimentacao.id_gta_entrada == gta.id, Movimentacao.tipo_entrada == TIPO_CARGA).delete(synchronize_session=False)
    db.query(Entrada).filter(Entrada.id_gta_entrada == gta.id, Entrada.tipo_entrada == TIPO_CARGA).delete(synchronize_session=False)
    db.delete(gta)
    db.flush()
    return True, f'Carga desfeita: {qtd} animais removidos. A Propriedade pode receber uma nova Carga.'

# =========================================================
# FIM DE ARQUIVO: backend\utils\carga_animais.py
# =========================================================
