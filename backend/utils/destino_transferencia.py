# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\destino_transferencia.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-28 12:15 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.8.0
# v1.8.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.7.0: Sessao 123 (2026-11-13 19:10 -03) - AUDITORIA ETAPA 6 (Regra #72): limpeza de CPF/CNPJ pela funcao central. REVERSAO: .bak_antes_etapa6c.
# v1.6.2: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras do CNPJ mantidas na limpeza e na formatacao. REVERSAO: .bak_antes_s122_etapa2.
#     v1.6.1: Sessao 118 (2026-11-08 13:00 -03) - Aviso "Propriedade do destino fora da nossa base" sem a linha "Propriedades de X na nossa base" (informacao demais; a tela agora lista as Propriedades para escolher). REVERSAO: .bak_antes_s118_info.
#     v1.6.0: Sessao 115 (2026-11-05 17:40 -03) - conferir_destino_posse(): Alteracao de Posse = mesma Propriedade (mesmo OESA), outro Produtor. REVERSAO: .bak_antes_s115_dta3a.
#
# DESCRICAO:
#     Check-list do DESTINO de uma Transferencia (Sessao 107). Peca unica: e usada pela GTA de Saida (mostra o resultado
#     na hora de escolher o destino) e, depois, pelo Gerar Comunicado (decide se a Entrada acontece automaticamente no destino).
#
#     O destino vem da GTA como um Parceiro + Propriedade do Parceiro (tb_parceiros / tb_parceiros_propriedades, dentro do schema
#     do Produtor de ORIGEM). Esta rotina confere esse destino com a NOSSA base (public.produtores / propriedades /
#     propriedades_produtores) e devolve o que acontece:
#
#       NA_BASE          CPF/CNPJ de um Produtor nosso E a Propriedade bate (Codigo MAPA e/ou Inscricao Estadual).
#                        -> a Entrada pode ser feita automaticamente no destino (mesmo Produtor ou outro Produtor da base).
#       PROPRIEDADE_FORA CPF/CNPJ e de um Produtor nosso, mas a Propriedade do destino NAO esta entre as dele (caso "Fazenda Modelo II"
#                        com outra inscricao, mesmo CPF e talvez mesmo endereco). NAO cai na Propriedade parecida: segue como
#                        destino fora da base (documentacao para a Certificadora).
#       FORA_BASE        CPF/CNPJ nao e de Produtor nosso. Documentacao para a Certificadora.
#       DIVERGENTE       Os dados se contradizem (ex.: o Codigo MAPA e de uma Propriedade, mas a Inscricao Estadual e de outra, ou
#                        a Propriedade achada pertence a outro Produtor que nao o do CPF/CNPJ). Nao e seguro decidir sozinho.
#       MESMA_ORIGEM     O destino e a propria Propriedade de origem. Bloqueia.
#
#     CHAVES de comparacao (nunca o endereco): CPF/CNPJ do Produtor (com zeros ate 14 digitos, por causa do legado), Codigo MAPA
#     e Inscricao Estadual (da Propriedade e do vinculo Produtor+Propriedade). Se a GTA traz as duas chaves da Propriedade, as
#     duas precisam concordar.
#
#     Devolve um dicionario:
#       status, nivel ('ok' | 'aviso' | 'bloqueio'), titulo, itens [{ok: True/False/None, texto}],
#       entrada_automatica (bool), id_propriedade_destino, id_produtor_destino, nome_propriedade_destino, nome_produtor_destino
#
#     v1.0.0: Criacao (Sessao 107).
#     v1.5.1: Sessao 108 (29/10/2026, 20:20 -03) - CORRECAO: dados_base usava prop.municipio (a linha achada nao tem essa coluna) e derrubava a conferencia; agora le da Propriedade completa.
#     v1.5.0: Sessao 108 (29/10/2026, 20:10 -03) - Destino NA_BASE devolve 'dados_base' (IE do vinculo/Propriedade, OESA, municipio, UF da nossa base) para a tela completar o que o Parceiro nao tem.  REVERSAO: .bak_antes_s108_ie_base
#     v1.4.0: Sessao 108 (29/10/2026, 20:00 -03) - Destino 'Propriedade fora da nossa base': a conferencia lista as Propriedades do Produtor na nossa base (nome e OESA), para o usuario ver a divergencia.  REVERSAO: .bak_antes_s108_oesa_geral
#     v1.3.0: Sessao 108 (29/10/2026, 10:25 -03) - A INSCRICAO ESTADUAL DEIXA DE ACHAR A PROPRIEDADE: ela e do Produtor e se repete entre as fazendas
#             dele (ex.: Campo Novo e Campo Limpo com a mesma IE), entao so o Codigo MAPA / Estabelecimento (OESA de 11 digitos) acha o destino. A IE
#             segue so CONFERINDO depois que a Propriedade foi achada (se nao bater, continua bloqueando como antes). Destino sem Codigo MAPA /
#             Estabelecimento = 'Propriedade do destino nao identificada' (so a Saida, documentacao a Certificadora).  REVERSAO: .bak_antes_s108_ie_so_confere.
#     v1.2.0: Sessao 107 - chave principal = Codigo MAPA (= Codigo da Exploracao da GTA, 15 digitos) contra Propriedade.codigo_mapa e a Exploracao
#             do vinculo; se a Propriedade nao tem Codigo MAPA, vale o OESA (= Estabelecimento da GTA, 11 digitos). IE e conferencia extra.
#     v1.1.0: Sessao 107 - nomes_destinos_transfer(): texto 'Estabelecimento — Parceiro' do destino das GTAs de Transferencia (lista, detalhe, Vincular).
# =========================================================

from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, PropriedadeProdutor, Produtor
from backend.utils.validadores import limpar_documento

NA_BASE = 'NA_BASE'
PROPRIEDADE_FORA = 'PROPRIEDADE_FORA'
FORA_BASE = 'FORA_BASE'
DIVERGENTE = 'DIVERGENTE'
MESMA_ORIGEM = 'MESMA_ORIGEM'


def _digitos(texto):
    return ''.join(c for c in (texto or '') if c.isdecimal())


def _doc_norm(texto):
    d = limpar_documento(texto)
    return d.zfill(14) if d else ''


def _oesa(texto):
    """OESA = Estabelecimento da GTA (11 digitos). Se vier o Codigo MAPA/Exploracao (15 digitos), os 11 primeiros."""
    d = _digitos(texto)
    return d[:11] if len(d) >= 11 else ''


def _num(texto):
    """Chave numerica (Codigo MAPA, Inscricao Estadual): so digitos; sem zeros a esquerda."""
    return _digitos(texto).lstrip('0')


def _resultado(status, nivel, titulo, itens, **extra):
    r = {
        'status': status, 'nivel': nivel, 'titulo': titulo, 'itens': itens,
        'entrada_automatica': status == NA_BASE,
        'id_propriedade_destino': None, 'id_produtor_destino': None,
        'nome_propriedade_destino': None, 'nome_produtor_destino': None,
    }
    r.update(extra)
    return r


def conferir_destino(id_propriedade_origem, cpf_cnpj, codigo_mapa, insc_estadual, uf=None):
    """Confere o destino (dados vindos da GTA) com a base. Veja o cabecalho para os status."""
    doc = _doc_norm(cpf_cnpj)
    mapa = _num(codigo_mapa)
    oesa = _oesa(codigo_mapa)
    ie = _num(insc_estadual)
    itens = []

    if not doc:
        return _resultado(FORA_BASE, 'aviso', 'Destino sem CPF/CNPJ',
                          [{'ok': False, 'texto': 'O destino não tem CPF/CNPJ: não dá para conferir com a nossa base.'}])

    with Session(engine) as db:
        produtores = [p for p in db.query(Produtor).filter(Produtor.ativo == True).all()   # noqa: E712
                      if _doc_norm(p.cpf_cnpj) == doc]

        # Propriedades da base com o mesmo Codigo MAPA ou a mesma Inscricao Estadual (o endereco nunca entra)
        achadas = {}
        if mapa:
            ie_dos_vinculos = {}
            exp_dos_vinculos = {}
            for id_prop, exp_v in db.query(PropriedadeProdutor.id_propriedade, PropriedadeProdutor.codigo_exploracao).filter(
                    PropriedadeProdutor.data_fim.is_(None)).all():
                if _num(exp_v):
                    exp_dos_vinculos.setdefault(id_prop, set()).add(_num(exp_v))
            for id_prop, ie_v in db.query(PropriedadeProdutor.id_propriedade, PropriedadeProdutor.inscricao_estadual).filter(
                    PropriedadeProdutor.data_fim.is_(None)).all():
                if _num(ie_v):
                    ie_dos_vinculos.setdefault(id_prop, set()).add(_num(ie_v))
            for p in db.query(Propriedade.id, Propriedade.nome, Propriedade.uf, Propriedade.codigo_mapa, Propriedade.oesa,
                              Propriedade.inscricao_estadual).filter(Propriedade.ativo == True).all():   # noqa: E712
                por_mapa = bool(mapa) and (_num(p.codigo_mapa) == mapa or mapa in exp_dos_vinculos.get(p.id, set())
                                           or (not _num(p.codigo_mapa) and bool(oesa) and _digitos(p.oesa) == oesa))
                por_ie = bool(ie) and (_num(p.inscricao_estadual) == ie or ie in ie_dos_vinculos.get(p.id, set()))
                if por_mapa:   # v1.3.0 - so o Codigo MAPA / Estabelecimento acha a Propriedade; a IE so confere (ver abaixo)
                    achadas[p.id] = {'prop': p, 'por_mapa': por_mapa, 'por_ie': por_ie}

        # --- Produtor ---
        if not produtores:
            itens.append({'ok': False, 'texto': 'CPF/CNPJ do destino não é de um Produtor da nossa base.'})
            if achadas:
                nomes = ', '.join(sorted(a['prop'].nome for a in achadas.values()))
                itens.append({'ok': False, 'texto': f'Atenção: o Código MAPA/Inscrição Estadual informados batem com a Propriedade '
                                                    f'"{nomes}", que é de outro CPF/CNPJ. Confira o documento do destino.'})
                return _resultado(DIVERGENTE, 'bloqueio', 'Dados do destino se contradizem', itens)
            return _resultado(FORA_BASE, 'aviso', 'Destino fora da nossa base', itens + [
                {'ok': None, 'texto': 'A baixa acontece na origem; a Entrada não é feita aqui. A documentação para a Certificadora será gerada.'}])

        produtor = produtores[0]
        itens.append({'ok': True, 'texto': f'CPF/CNPJ confere com o Produtor {produtor.nome}.'})

        # Propriedades ativas do Produtor
        vinculos = (
            db.query(PropriedadeProdutor, Propriedade)
            .join(Propriedade, Propriedade.id == PropriedadeProdutor.id_propriedade)
            .filter(PropriedadeProdutor.id_produtor == produtor.id,
                    PropriedadeProdutor.data_fim.is_(None),
                    Propriedade.ativo == True)   # noqa: E712
            .all()
        )
        props_do_produtor = {p.id: p for _v, p in vinculos}
        _lista_props = '; '.join(
            f'{p.nome} (OESA {(_digitos(p.oesa)[:11] or "não cadastrado")})'
            for p in sorted(props_do_produtor.values(), key=lambda x: x.nome or '')) or 'nenhuma Propriedade ativa'
        _info_props = {'ok': None, 'texto': f'Propriedades de {produtor.nome} na nossa base: {_lista_props}.'}

        if not mapa:
            itens.append({'ok': False, 'texto': 'O destino não traz o Código MAPA / Estabelecimento (OESA): não dá para saber qual Propriedade do Produtor recebe. A Inscrição Estadual sozinha não identifica a Propriedade.'})
            return _resultado(PROPRIEDADE_FORA, 'aviso', 'Propriedade do destino não identificada', itens,
                              nome_produtor_destino=produtor.nome, id_produtor_destino=produtor.id)

        do_produtor = {pid: a for pid, a in achadas.items() if pid in props_do_produtor}
        de_outros = {pid: a for pid, a in achadas.items() if pid not in props_do_produtor}

        if not do_produtor:
            itens.append({'ok': False, 'texto': 'A Propriedade do destino (Código MAPA / Estabelecimento) NÃO está entre as deste Produtor na nossa base.'})
            # s118 - linha informativa das Propriedades retirada (a tela de destino ja lista as Propriedades para escolher)
            if de_outros:
                nomes = ', '.join(sorted(a['prop'].nome for a in de_outros.values()))
                itens.append({'ok': False, 'texto': f'Atenção: esses dados batem com "{nomes}", que pertence a outro Produtor. Confira.'})
                return _resultado(DIVERGENTE, 'bloqueio', 'Dados do destino se contradizem', itens,
                                  nome_produtor_destino=produtor.nome, id_produtor_destino=produtor.id)
            return _resultado(PROPRIEDADE_FORA, 'aviso', 'Propriedade do destino fora da nossa base', itens + [
                {'ok': None, 'texto': 'A baixa acontece na origem; a Entrada não é feita aqui. A documentação para a Certificadora será gerada.'}],
                nome_produtor_destino=produtor.nome, id_produtor_destino=produtor.id)

        if len(do_produtor) > 1:
            nomes = ', '.join(sorted(a['prop'].nome for a in do_produtor.values()))
            itens.append({'ok': False, 'texto': f'Mais de uma Propriedade do Produtor bate com os dados do destino ({nomes}). Ajuste o cadastro.'})
            return _resultado(DIVERGENTE, 'bloqueio', 'Mais de uma Propriedade possível', itens,
                              nome_produtor_destino=produtor.nome, id_produtor_destino=produtor.id)

        pid, achada = next(iter(do_produtor.items()))
        prop = achada['prop']

        # as duas chaves da GTA precisam concordar entre si
        if mapa and ie and (achada['por_mapa'] != achada['por_ie']):
            qual = 'Código MAPA' if achada['por_mapa'] else 'Inscrição Estadual'
            outra = 'Inscrição Estadual' if achada['por_mapa'] else 'Código MAPA'
            itens.append({'ok': False, 'texto': f'O {qual} bate com "{prop.nome}", mas o {outra} informado não bate. Confira a GTA.'})
            return _resultado(DIVERGENTE, 'bloqueio', 'Dados do destino se contradizem', itens,
                              nome_produtor_destino=produtor.nome, id_produtor_destino=produtor.id)

        if mapa:
            itens.append({'ok': True, 'texto': f'Código MAPA confere com "{prop.nome}".'})
        if ie:
            itens.append({'ok': True, 'texto': f'Inscrição Estadual confere com "{prop.nome}".'})
        if uf and prop.uf and uf.upper() != prop.uf.upper():
            itens.append({'ok': False, 'texto': f'UF do destino ({uf}) é diferente da UF cadastrada para "{prop.nome}" ({prop.uf}). Confira.'})
            return _resultado(DIVERGENTE, 'bloqueio', 'Dados do destino se contradizem', itens,
                              nome_produtor_destino=produtor.nome, id_produtor_destino=produtor.id)

        if int(prop.id) == int(id_propriedade_origem):
            itens.append({'ok': False, 'texto': 'O destino é a própria Propriedade de origem.'})
            return _resultado(MESMA_ORIGEM, 'bloqueio', 'Destino igual à origem', itens,
                              id_propriedade_destino=prop.id, nome_propriedade_destino=prop.nome,
                              id_produtor_destino=produtor.id, nome_produtor_destino=produtor.nome)

        itens.append({'ok': True, 'texto': 'Destino na nossa base: a Entrada será feita automaticamente no Comunicado.'})
        _v_base = next((v for v, pr in vinculos if pr.id == prop.id), None)
        _prop_completa = props_do_produtor.get(prop.id)   # 'prop' aqui so tem algumas colunas (sem municipio)
        dados_base = {
            'ie': (getattr(_v_base, 'inscricao_estadual', None) or prop.inscricao_estadual or '').strip(),
            'oesa': _digitos(prop.oesa)[:11],
            'municipio': (getattr(_prop_completa, 'municipio', None) or ''), 'uf': (prop.uf or '').upper(),
        }
        return _resultado(NA_BASE, 'ok', 'Destino na nossa base', itens, dados_base=dados_base,
                          id_propriedade_destino=prop.id, nome_propriedade_destino=prop.nome,
                          id_produtor_destino=produtor.id, nome_produtor_destino=produtor.nome)

def conferir_destino_posse(id_propriedade_origem, id_produtor_origem, cpf_cnpj, codigo_mapa, insc_estadual, uf=None):
    """ALTERACAO DE POSSE (s115): o destino e a MESMA Propriedade (mesmo OESA = 11 primeiros digitos do Codigo MAPA) em nome de OUTRO Produtor.
    Parte da conferencia normal e inverte o que a Transferencia bloqueia (MESMA_ORIGEM):
      - sem Codigo MAPA / OESA no destino ........ bloqueia (nao da para saber a Propriedade);
      - OESA do destino diferente do da origem ... bloqueia (para outra Propriedade, use a Transferencia);
      - destino na base, mesma Propriedade, outro Produtor ... NA_BASE (a Entrada nasce no Comunicado de Posse);
      - destino e o proprio Produtor da origem ... bloqueia (Posse e para outro Produtor);
      - destino fora da base (Produtor ou Propriedade) ... aviso: so sai da origem, documentacao para a Certificadora."""
    base = conferir_destino(id_propriedade_origem, cpf_cnpj, codigo_mapa, insc_estadual, uf)
    oesa_dest = _oesa(codigo_mapa)
    with Session(engine) as db:
        prop_origem = db.get(Propriedade, int(id_propriedade_origem))
        oesa_origem = _digitos(prop_origem.oesa)[:11] if prop_origem else ''
    itens = list(base['itens'])
    extra = dict(id_propriedade_destino=base.get('id_propriedade_destino'), id_produtor_destino=base.get('id_produtor_destino'),
                 nome_propriedade_destino=base.get('nome_propriedade_destino'), nome_produtor_destino=base.get('nome_produtor_destino'))

    if not oesa_dest:
        return _resultado(DIVERGENTE, 'bloqueio', 'Destino sem Código MAPA / OESA', itens + [
            {'ok': False, 'texto': 'A Alteração de Posse é na mesma Propriedade: o destino precisa trazer o Código MAPA / Estabelecimento (OESA).'}], **extra)
    if oesa_origem and oesa_dest != oesa_origem:
        return _resultado(DIVERGENTE, 'bloqueio', 'Destino em outra Propriedade', itens + [
            {'ok': False, 'texto': f'A Alteração de Posse é na MESMA Propriedade: o OESA do destino ({oesa_dest}) é diferente do da origem ({oesa_origem}). '
                                   f'Para outra Propriedade, use a Transferência ou a Venda.'}], **extra)

    if base['status'] == MESMA_ORIGEM:
        itens = [i for i in itens if i.get('texto') != 'O destino é a própria Propriedade de origem.']
        if str(base.get('id_produtor_destino')) == str(id_produtor_origem):
            return _resultado(MESMA_ORIGEM, 'bloqueio', 'Posse é para outro Produtor', itens + [
                {'ok': False, 'texto': 'O destino é o próprio Produtor. A Alteração de Posse muda a Propriedade de Produtor.'}], **extra)
        itens.append({'ok': True, 'texto': 'Mesma Propriedade (OESA igual), outro Produtor na nossa base: a Entrada será feita automaticamente no Comunicado de Posse.'})
        return _resultado(NA_BASE, 'ok', 'Destino na nossa base (mesma Propriedade, outro Produtor)', itens, **extra)

    if base['status'] == NA_BASE:   # achou outra Propriedade com o mesmo OESA: nao deveria acontecer; nao arrisca
        return _resultado(DIVERGENTE, 'bloqueio', 'Destino em outra Propriedade', itens + [
            {'ok': False, 'texto': 'O destino bate com uma Propriedade diferente da origem. Confira o Código MAPA.'}], **extra)

    return base   # FORA_BASE / PROPRIEDADE_FORA (aviso) e DIVERGENTE (bloqueio) seguem como estao


def nomes_destinos_transfer(db, ids_parceiro_propriedade):
    """{id_parceiro_propriedade: 'Estabelecimento — Parceiro'}. `db` = sessao do schema do Produtor (get_db_produtor)."""
    ids = {i for i in ids_parceiro_propriedade if i}
    if not ids:
        return {}
    from backend.models.tb_parceiros import Parceiro
    from backend.models.tb_parceiros_propriedades import ParceiroPropriedades
    saida = {}
    for pp, parceiro in (db.query(ParceiroPropriedades, Parceiro)
                         .join(Parceiro, Parceiro.id == ParceiroPropriedades.id_parceiro)
                         .filter(ParceiroPropriedades.id.in_(ids)).all()):
        saida[pp.id] = f'{pp.estabelecimento} — {parceiro.nome}'
    return saida


# =========================================================
# FIM DE ARQUIVO: backend\utils\destino_transferencia.py
# =========================================================
