# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\Orion\backend\utils
# MODULO: backend\utils\bnd_fazenda.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-18 20:00 -03
# ATUALIZADO EM: 2026-11-19 12:10 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     BND/Fazenda: regra da COMPARACAO entre o Extrato de Animais Vivos do MAPA (BND) e os animais em estoque (tb_2001)
#     e da CORRECAO da base. O que vale e a BND (MAPA): divergencia nao e erro.
#     Sem Flask: recebe as sessoes de banco prontas. NAO guarda o resultado da comparacao (processa e descarta).
#
#     COMPARACAO (por Produtor / Propriedade)
#       01 FAZENDA igual BND  - codigos que constam nos dois lados (inclui os que tem divergencia de dados)
#       02 Fazenda nao BND    - na tb_2001 e nao no Extrato
#       03 BND nao Fazenda    - no Extrato e nao na tb_2001; informa Abate/Venda/Transferencia/Morte registrados no Orion
#                               (POSSE nao conta); sem registro = o Produtor descobre o que houve
#       04 Inconformidades    - mesmos codigos dos dois lados com sexo, nascimento ou raca diferentes. A data de inclusao
#                               NAO entra (a do Orion quase sempre esta errada: e atualizada sem aviso na Correcao).
#
#     CORRECAO (so a Consiste): para cada animal que esta nos dois lados, grava o que a BND diz em
#       tb_2001 (sexo, nascimento, id_raca, data_inclusao), tb_2017 (idem, todas as linhas do animal) e
#       tb_7017 (sexo, nascimento, raca em 2 letras). tb_7002 (PIA) NAO muda: e documento emitido.
#       Quando a data de inclusao muda, a liberacao_abate e recalculada (nova Data Inclusao + 90 dias, mesma regra da
#       Brincagem e da Carga) na tb_2001 e na tb_2017. Nao mexe em eras_dias nem cota_hilton (decisao do Benedito 19/11/2026:
#       a Cota Hilton so e estimada na Carga; as entradas novas ja nascem na regra).
#       Sem Desfazer. Grava 1 registro no Log (quem, quando, quantos), sem o de -> para.
#
#   v1.0.0: Criacao (BND/Fazenda, Sessao 132, 18/11/2026).
#   v1.1.0: Sessao 133 (2026-11-19 12:10 -03) - Correcao recalcula a liberacao_abate junto com a data de inclusao
#           (inclusao + 90 dias). REVERSAO: .bak_antes_s133_cth.
# =========================================================

import re
from datetime import datetime, timedelta

from sqlalchemy import text

from backend.utils import carga_animais as ca
from backend.utils.log_operacoes import registrar_operacao

MODULO_LOG = 'bnd_fazenda'

MSG_NASC = 'Verifique Data de Nascto'
MSG_RACA = 'Verifique a Raça'
MSG_SEXO = 'Verifique o Sexo'

NOMES_EVENTO = {'ABATE': 'Abate', 'VENDA': 'Venda', 'TRANSFER': 'Transferência', 'TRANSFERENCIA': 'Transferência', 'MORTE': 'Morte'}
RACA_DESCONHECIDA = '??'


def formatar_sisbov(sisbov):
    """15 digitos -> 14 digitos + '-' + digito verificador (como o MAPA e o GERAS mostram)."""
    s = str(sisbov or '')
    return f'{s[:14]}-{s[14:]}' if len(s) == 15 else s


def _so_digitos(valor):
    return re.sub(r'\D', '', str(valor or ''))


def escolher_parte(partes, documentos):
    """Parte do Extrato que e do Produtor (pelo CPF/CNPJ). documentos = (cpf, cnpj) do Produtor, so digitos."""
    alvo = {_so_digitos(d) for d in documentos if d}
    alvo.discard('')
    for p in partes:
        if _so_digitos(p['cabecalho'].get('produtor_documento')) in alvo:
            return p
    return None


def propriedade_confere(propriedade, cabecalho):
    """True se o Extrato e da Propriedade (codigo MAPA ou Nirf, so digitos, sem zeros a esquerda)."""
    cod = ca._digitos(cabecalho.get('cod_propriedade')).lstrip('0')
    nirf = ca._digitos(cabecalho.get('nirf')).lstrip('0')
    return bool((cod and ca._digitos(propriedade.codigo_mapa).lstrip('0') == cod)
                or (nirf and ca._digitos(propriedade.nirf_incra).lstrip('0') == nirf))


def racas_por_id(racas_nome):
    """{id: codigo de 2 letras} a partir de ca.racas_do_cadastro()."""
    return {i: c for (i, c) in racas_nome.values()}


def ler_fazenda(db, id_propriedade):
    """Animais em estoque da Propriedade (tb_2001 do schema do Produtor): {sisbov: dados}."""
    linhas = db.execute(text(
        'SELECT sisbov, sexo::text, nascimento, id_raca, data_inclusao FROM tb_2001 WHERE id_propriedade = :p'),
        {'p': id_propriedade}).all()
    return {s: {'sexo': sx, 'nascimento': n, 'id_raca': r, 'data_inclusao': i} for (s, sx, n, r, i) in linhas}


def _bnd_por_sisbov(animais_bnd):
    bnd = {}
    for a in animais_bnd:
        bnd.setdefault(a['sisbov'], a)   # repetido no arquivo: vale o primeiro
    return bnd


def comparar(fazenda, animais_bnd, racas_nome, racas_id):
    """Devolve {'igual': [sisbov], 'so_fazenda': [sisbov], 'so_bnd': [sisbov], 'inconformidades': [dict]}, tudo em ordem de codigo."""
    bnd = _bnd_por_sisbov(animais_bnd)
    ambos = sorted(s for s in bnd if s in fazenda)
    inconf = []
    for s in ambos:
        f, b = fazenda[s], bnd[s]
        raca_b = racas_nome.get(ca.normalizar_nome(b['raca_nome']))
        id_raca_b = raca_b[0] if raca_b else None
        cod_b = raca_b[1] if raca_b else RACA_DESCONHECIDA
        msgs = []
        if f['nascimento'] != b['nascimento']:
            msgs.append(MSG_NASC)
        if f['id_raca'] != id_raca_b:
            msgs.append(MSG_RACA)
        if f['sexo'] != b['sexo']:
            msgs.append(MSG_SEXO)
        if msgs:
            inconf.append({
                'sisbov': s,
                'f_sexo': f['sexo'], 'f_nascimento': f['nascimento'], 'f_raca': racas_id.get(f['id_raca'], ''),
                'b_sexo': b['sexo'], 'b_nascimento': b['nascimento'], 'b_raca': cod_b,
                'mensagem': ' / '.join(msgs),
            })
    return {
        'igual': ambos,
        'so_fazenda': sorted(s for s in fazenda if s not in bnd),
        'so_bnd': sorted(s for s in bnd if s not in fazenda),
        'inconformidades': inconf,
    }


def eventos_orion(db, sisbovs):
    """Para os animais que a BND tem e a Fazenda nao: ultimo Abate/Venda/Transferencia/Morte registrado no Orion
    (tb_2002). POSSE nao conta. {sisbov: (nome do evento, data)}; quem nao esta no dicionario nao tem registro."""
    if not sisbovs:
        return {}
    saida = {}
    lista = list(sisbovs)
    for i in range(0, len(lista), 2000):
        linhas = db.execute(text(
            "SELECT DISTINCT ON (sisbov) sisbov, tipo_saida, data_saida FROM tb_2002 "
            "WHERE sisbov = ANY(:l) AND tipo_saida <> 'POSSE' ORDER BY sisbov, data_saida DESC, id DESC"),
            {'l': lista[i:i + 2000]}).all()
        for s, tipo, data in linhas:
            saida[s] = (NOMES_EVENTO.get(str(tipo).upper(), str(tipo).title()), data)
    return saida


def resumo_comparacao(comp):
    """Numeros que a tela mostra (sem os codigos)."""
    inc = comp['inconformidades']
    return {
        'igual': len(comp['igual']), 'so_fazenda': len(comp['so_fazenda']), 'so_bnd': len(comp['so_bnd']),
        'inconformidades': len(inc),
        'nasc': sum(1 for x in inc if MSG_NASC in x['mensagem']),
        'raca': sum(1 for x in inc if MSG_RACA in x['mensagem']),
        'sexo': sum(1 for x in inc if MSG_SEXO in x['mensagem']),
    }


# ---------------------------------------------------------
# CORRECAO
# ---------------------------------------------------------
def mudancas_do_animal(f, b, racas_nome):
    """O que a BND diz e a Fazenda tem diferente, so onde a BND tem dado utilizavel.
    Devolve (mudancas, avisos): mudancas = {'nascimento','sexo','id_raca','raca','data_inclusao'}; avisos = lista de textos curtos."""
    mud, avisos = {}, []
    if b['nascimento'] is None:
        avisos.append('nasc_invalido')
    elif f['nascimento'] != b['nascimento']:
        mud['nascimento'] = b['nascimento']
    if b['sexo'] is None:
        avisos.append('sexo_invalido')
    elif f['sexo'] != b['sexo']:
        mud['sexo'] = b['sexo']
    raca_b = racas_nome.get(ca.normalizar_nome(b['raca_nome']))
    if raca_b is None:
        avisos.append('raca_desconhecida')
    elif f['id_raca'] != raca_b[0]:
        mud['id_raca'], mud['raca'] = raca_b[0], raca_b[1]
    if b['data_inclusao'] is not None and f['data_inclusao'] != b['data_inclusao']:
        mud['data_inclusao'] = b['data_inclusao']
    return mud, avisos


def plano_correcao(fazenda, animais_bnd, racas_nome):
    """Contagem do que a Correcao faria (nao grava). Mesmo calculo da gravacao."""
    bnd = _bnd_por_sisbov(animais_bnd)
    r = {'animais': 0, 'nascimento': 0, 'sexo': 0, 'raca': 0, 'data_inclusao': 0,
         'raca_desconhecida': 0, 'nasc_invalido': 0, 'sexo_invalido': 0}
    for s, b in bnd.items():
        if s not in fazenda:
            continue
        mud, avisos = mudancas_do_animal(fazenda[s], b, racas_nome)
        for a in avisos:
            r[a] += 1
        if any(k in mud for k in ('nascimento', 'sexo', 'id_raca')):
            r['animais'] += 1   # animais com divergencia de nascimento/sexo/raca (a data de inclusao e contada a parte)
        if mud:
            for k in ('nascimento', 'sexo', 'data_inclusao'):
                r[k] += 1 if k in mud else 0
            r['raca'] += 1 if 'id_raca' in mud else 0
    return r


def aplicar_correcao(db, id_propriedade, fazenda, animais_bnd, racas_nome, id_usuario):
    """Grava a correcao (a sessao db e do Produtor; quem chama faz commit/rollback). Devolve a mesma contagem de plano_correcao()."""
    bnd = _bnd_por_sisbov(animais_bnd)
    resumo = plano_correcao(fazenda, animais_bnd, racas_nome)
    for s, b in bnd.items():
        if s not in fazenda:
            continue
        mud, _ = mudancas_do_animal(fazenda[s], b, racas_nome)
        if not mud:
            continue
        p = {'s': s, 'p': id_propriedade}
        # tb_2001 e tb_2017 (mesmas colunas)
        sets = []
        if 'nascimento' in mud:
            sets.append('nascimento = :nasc'); p['nasc'] = mud['nascimento']
        if 'sexo' in mud:
            sets.append('sexo = CAST(:sexo AS public.sexo_enum)'); p['sexo'] = mud['sexo']
        if 'id_raca' in mud:
            sets.append('id_raca = :id_raca'); p['id_raca'] = mud['id_raca']
        if 'data_inclusao' in mud:
            sets.append('data_inclusao = :incl'); p['incl'] = mud['data_inclusao']
            # v1.1.0: a liberacao para abate acompanha a nova data de inclusao (inclusao + 90 dias)
            sets.append('liberacao_abate = :libera'); p['libera'] = mud['data_inclusao'] + timedelta(days=ca.DIAS_LIBERACAO_ABATE)
        if sets:
            db.execute(text(f'UPDATE tb_2001 SET {", ".join(sets)}, atualizado_em = :agora WHERE sisbov = :s AND id_propriedade = :p'),
                       dict(p, agora=datetime.now()))
            db.execute(text(f'UPDATE tb_2017_movimentacoes SET {", ".join(sets)} WHERE sisbov = :s AND id_propriedade = :p'), p)
        # tb_7017 (brinco): sexo, nascimento e raca em 2 letras; nao tem data de inclusao
        sets7, p7 = [], {'s': s, 'p': id_propriedade}
        if 'nascimento' in mud:
            sets7.append('nascimento = :nasc'); p7['nasc'] = mud['nascimento']
        if 'sexo' in mud:
            sets7.append('sexo = :sexo'); p7['sexo'] = mud['sexo']
        if 'raca' in mud:
            sets7.append('raca = :raca'); p7['raca'] = mud['raca']
        if sets7:
            db.execute(text(f'UPDATE tb_7017_entrada_brincos_rfid SET {", ".join(sets7)}, atualizado_em = :agora WHERE sisbov = :s AND id_propriedade = :p'),
                       dict(p7, agora=datetime.now()))
    if resumo['animais'] or resumo['data_inclusao']:
        registrar_operacao(
            db, id_usuario, id_propriedade, MODULO_LOG,
            f'Correção BND/Fazenda pela Consiste: {resumo["animais"]} animais corrigidos '
            f'(nascimento {resumo["nascimento"]}, sexo {resumo["sexo"]}, raça {resumo["raca"]}); '
            f'data de inclusão e liberação para abate atualizadas em {resumo["data_inclusao"]}.'[:255])
    return resumo

# =========================================================
# FIM DE ARQUIVO: backend\utils\bnd_fazenda.py
# =========================================================
