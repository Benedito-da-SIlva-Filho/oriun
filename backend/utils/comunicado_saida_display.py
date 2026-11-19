# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\comunicado_saida_display.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-20 12:15 -03
# ATUALIZADO EM: 2026-11-01 17:40 -03
# VERSAO: 1.3.0
# v1.3.0: Sessao 115 (05/11/2026) - Posse: montar_contexto_posse (PDF Comunicado de Alteracao de Posse) e POSSE na lista. REVERSAO: .bak_antes_s115_posse_pdf.
#
# DESCRICAO:
#     Apoio da Impressao / Reimpressao do Comunicado de Saida (molde: comunicado_display.py da Entrada).
#         - agrupar_comunicados_saida(db, linhas, decrescente): 1 item por numero de Comunicado, para as listas.
#         - montar_contexto_anexo_saida(db, linhas, produtor, id_propriedade): monta o dicionario que os tres PDFs
#           (pdf_anexo_saida.py) recebem. So LE o banco, nunca grava.
#
#     Regras de preenchimento (combinadas com Benedito, Sessao 101):
#         - CPF e CNPJ do produtor: vem dos DOIS campos do cadastro do Produtor (v1.0.1). So CPF imprime so o CPF,
#           so CNPJ imprime so o CNPJ, os dois imprime os dois (decisao de Benedito, Sessao 101).
#         - Inscricao Estadual do produtor: a do vinculo Produtor x Propriedade; se vazia, a da Propriedade.
#         - Frigorifico: nome, CNPJ, Inscricao Estadual, S.I.F. e Municipio do cadastro; "Estabelecimento" =
#           logradouro + " - " + numero do cadastro do frigorifico.
#         - Animais: os que foram baixados no Comunicado (tb_2002_saida_animais, pelo numero do Comunicado e pelas
#           GTAs), na ordem GTA (emissao) e SISBOV crescente. Numeracao continua atravessando as GTAs.
#
#     v1.0.0: Criacao (Sessao 101, Pacote 2).
#     v1.0.1: Sessao 101 (20/10/2026, 17:18 -03) - CPF e CNPJ vem do Produtor (documentos_do_produtor); some a logica do Proprietario.
#     v1.0.2: Sessao 101 (18:10) - o CNPJ/CPF secundario vem do vinculo Produtor+Propriedade (por fazenda): documentos_do_produtor(produtor, vinculo).
#     v1.1.0: Sessao 107 (28/10/2026) - Transferencia: a lista agrupa por (tipo, numero) e mostra o destino (Estabelecimento do Parceiro); o PDF usa o Parceiro da GTA no bloco DESTINO.  REVERSAO: .bak_antes_s107zg
#     v1.0.3: Sessao 102 (2026-10-21 12:35 -03) - Animal trocado depois do Comunicado (substituido=True) nao entra mais na lista de animais impressa.
# =========================================================

from backend.models import Propriedade
from backend.models.propriedade_produtor import PropriedadeProdutor
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_frigorificos import Frigorifico
from backend.models.tb_4001_gta import Gta
from backend.utils.documentos_produtor import documentos_do_produtor


def _texto(valor):
    texto = str(valor).strip() if valor is not None else ''
    return texto


def _data_br(valor):
    return valor.strftime('%d/%m/%Y') if valor else '-'


def _nomes_frigorificos(db, ids):
    ids = {int(i) for i in ids if i}
    if not ids:
        return {}
    return {f.id: f.nome for f in db.query(Frigorifico).filter(Frigorifico.id.in_(ids)).all()}


# -------------------------------------------------------
# Lista: 1 item por numero de Comunicado (as linhas ja vem filtradas pelo router).
# -------------------------------------------------------
def _destinos_transfer(db, linhas):
    """{id_gta: (Parceiro, ParceiroPropriedade)} das GTAs de Transferencia (destino vem da GTA)."""
    ids = [l.id_gta for l in linhas if l.tipo_saida in ('TRANSFER', 'VENDA', 'POSSE') and l.id_gta]
    if not ids:
        return {}
    resultado = {}
    for gta in db.query(Gta).filter(Gta.id.in_(ids)).all():
        pp = gta.parceiro_propriedade
        resultado[gta.id] = (pp.parceiro if pp else None, pp)
    return resultado


def agrupar_comunicados_saida(db, linhas, decrescente=False):
    grupos = {}
    for linha in linhas:
        grupos.setdefault((linha.tipo_saida, linha.numero_comunicado), []).append(linha)

    nomes = _nomes_frigorificos(db, [l.id_frigorifico for l in linhas])
    destinos = _destinos_transfer(db, linhas)

    resultado = []
    for (tipo, numero), grupo in grupos.items():
        data_saida = max((l.data_saida for l in grupo if l.data_saida), default=None)
        if tipo == 'POSSE':   # s115: o destino da Posse e o novo Produtor
            parceiro = destinos.get(grupo[0].id_gta, (None, None))[0]
            destino = parceiro.nome if parceiro else '-'
        elif tipo in ('TRANSFER', 'VENDA'):
            pp = destinos.get(grupo[0].id_gta, (None, None))[1]
            destino = pp.estabelecimento if pp else '-'
        else:
            destino = nomes.get(grupo[0].id_frigorifico, '-')
        resultado.append({
            'numero_comunicado': numero,
            'tipo':              tipo,
            'tipo_rotulo':       {'TRANSFER': 'Transferência', 'VENDA': 'Venda', 'POSSE': 'Alteração de Posse'}.get(tipo, 'Abate'),
            'qtde_gtas':         len(grupo),
            'total_animais':     sum(l.qtd_animais or 0 for l in grupo),
            'frigorifico':       destino,
            'data_saida':        _data_br(data_saida),
            'status':            grupo[0].status,
            'data_envio':        grupo[0].data_envio,
            'impresso_em':       grupo[0].impresso_em,
            'id_usuario_impressao': grupo[0].id_usuario_impressao,
        })

    resultado.sort(key=lambda c: (c['numero_comunicado'], c['tipo']), reverse=decrescente)
    return resultado


# -------------------------------------------------------
# Contexto dos PDFs. linhas = linhas de tb_2011 do Comunicado, ja em ordem (gta_data_emissao, id).
# -------------------------------------------------------
def montar_contexto_anexo_saida(db, linhas, produtor, id_propriedade):
    propriedade = db.get(Propriedade, int(id_propriedade))
    inscricao = ''
    vinculo = None
    if produtor is not None:
        vinculo = (
            db.query(PropriedadeProdutor)
            .filter_by(id_propriedade=int(id_propriedade), id_produtor=produtor.id, data_fim=None)
            .first()
        )
        inscricao = _texto(vinculo.inscricao_estadual) if vinculo else ''
    cpf, cnpj = documentos_do_produtor(produtor, vinculo)   # principal do Produtor + secundario DESTA fazenda
    if not inscricao and propriedade is not None:
        inscricao = _texto(propriedade.inscricao_estadual)

    frigorifico = db.get(Frigorifico, linhas[0].id_frigorifico) if linhas[0].id_frigorifico else None
    if frigorifico is not None:
        partes = [p for p in (_texto(frigorifico.logradouro), _texto(frigorifico.numero)) if p]
        estabelecimento = ' - '.join(partes)
        municipio_frig = ' / '.join(p for p in (_texto(frigorifico.municipio_nome), _texto(frigorifico.uf)) if p)
    else:
        estabelecimento = ''
        municipio_frig = ''

    # Animais baixados neste Comunicado, na ordem das GTAs; dentro de cada GTA, SISBOV crescente.
    numero = linhas[0].numero_comunicado
    posicao_gta = {linha.id_gta: indice for indice, linha in enumerate(linhas)}
    animais = (
        db.query(SaidaAnimal)
        .filter(
            SaidaAnimal.id_propriedade == int(id_propriedade),
            SaidaAnimal.numero_comunicado == numero,
            SaidaAnimal.tipo_saida == linhas[0].tipo_saida,   # v-s107: numero repete entre tipos
            SaidaAnimal.substituido == False,   # noqa: E712 - animal trocado depois do Comunicado fica so no historico
            SaidaAnimal.id_gta.in_(list(posicao_gta.keys())),
        )
        .all()
    )
    animais.sort(key=lambda a: (posicao_gta.get(a.id_gta, 999), a.sisbov))

    data_saida = max((l.data_saida for l in linhas if l.data_saida), default=None)

    destino = {
        'frigorifico_nome':   _texto(frigorifico.nome) if frigorifico else '-',
        'estabelecimento':    estabelecimento,
        'cnpj':               _texto(frigorifico.cpf_cnpj) if frigorifico else '',
        'inscricao_estadual': _texto(frigorifico.insc_estadual) if frigorifico else '',
        'municipio':          municipio_frig,
        'sif':                _texto(frigorifico.cod_sif) if frigorifico else '',
    }
    if linhas[0].tipo_saida in ('TRANSFER', 'VENDA'):   # s111: Venda = destino pela GTA, igual a Transferencia
        parceiro, pp = _destinos_transfer(db, linhas).get(linhas[0].id_gta, (None, None))
        destino = {
            'frigorifico_nome':   _texto(parceiro.nome) if parceiro else '-',
            'estabelecimento':    _texto(pp.estabelecimento) if pp else '',
            'cnpj':               _texto(parceiro.cpf_cnpj) if parceiro else '',
            'inscricao_estadual': _texto(pp.insc_estadual) if pp else '',
            'municipio':          _texto(pp.municipio_nome) if pp else '',
            'sif':                '',
        }

    return {
        'numero_comunicado': numero,
        'tipo_saida': linhas[0].tipo_saida,
        'origem': {
            'produtor_nome':      _texto(produtor.nome) if produtor else '-',
            'cpf':                cpf,
            'cnpj':               cnpj,
            'inscricao_estadual': inscricao,
            'codigo_eras':        _texto(propriedade.codigo_eras) if propriedade else '',
            'propriedade_nome':   _texto(propriedade.nome) if propriedade else '-',
            'municipio':          (f'{propriedade.municipio} / {propriedade.uf}' if propriedade else '-'),
            'cep':                _texto(propriedade.cep) if propriedade else '',
        },
        'destino': destino,
        'gtas': [
            {
                'numero':       linha.gta_numero,
                'qtde_animais': linha.qtd_animais,
                'data_emissao': _data_br(linha.gta_data_emissao),
            }
            for linha in linhas
        ],
        'total_animais': sum(l.qtd_animais or 0 for l in linhas),
        'data_saida':    _data_br(data_saida),
        'sisbov':        [a.sisbov for a in animais],
    }

# -------------------------------------------------------
# s115 - Contexto do PDF "Comunicado de Alteracao de Posse" (so le o banco).
# -------------------------------------------------------
def montar_contexto_posse(db, linhas, produtor, id_propriedade):
    from backend.database import engine
    from sqlalchemy.orm import Session
    from backend.models import Produtor as _Produtor
    from backend.models.tb_2001_entradas import Entrada
    from backend.models.tb_4005_racas import Raca
    from backend.utils.destino_transferencia import conferir_destino_posse
    from backend.utils.multitenant import get_db_produtor

    propriedade = db.get(Propriedade, int(id_propriedade))
    vinculo = None
    inscricao = ''
    if produtor is not None:
        vinculo = (db.query(PropriedadeProdutor)
                   .filter_by(id_propriedade=int(id_propriedade), id_produtor=produtor.id, data_fim=None).first())
        inscricao = _texto(vinculo.inscricao_estadual) if vinculo else ''
    cpf, cnpj = documentos_do_produtor(produtor, vinculo)
    if not inscricao and propriedade is not None:
        inscricao = _texto(propriedade.inscricao_estadual)

    primeira = linhas[0]
    gtas = {g.id: g for g in db.query(Gta).filter(Gta.id.in_([l.id_gta for l in linhas if l.id_gta])).all()}
    parceiro, pp = _destinos_transfer(db, linhas).get(primeira.id_gta, (None, None))

    id_produtor_destino = None
    if parceiro is not None and pp is not None and produtor is not None:
        try:
            conf = conferir_destino_posse(int(id_propriedade), produtor.id, parceiro.cpf_cnpj, pp.codigo_mapa, pp.insc_estadual, pp.uf)
            id_produtor_destino = conf.get('id_produtor_destino')
        except Exception:
            id_produtor_destino = None

    numero = primeira.numero_comunicado
    posicao_gta = {l.id_gta: i for i, l in enumerate(linhas)}
    animais = (db.query(SaidaAnimal)
               .filter(SaidaAnimal.id_propriedade == int(id_propriedade), SaidaAnimal.numero_comunicado == numero,
                       SaidaAnimal.tipo_saida == 'POSSE', SaidaAnimal.substituido == False,   # noqa: E712
                       SaidaAnimal.id_gta.in_(list(posicao_gta.keys()))).all())
    animais.sort(key=lambda a: (posicao_gta.get(a.id_gta, 999), a.sisbov))

    # Data de Identificacao = data da Brincagem; a tb_2001 da origem ja perdeu o animal, entao le a do novo Produtor.
    identificacao = {}
    if id_produtor_destino:
        try:
            with get_db_produtor(id_produtor_destino) as db_dest:
                for e in db_dest.query(Entrada).filter(Entrada.sisbov.in_([a.sisbov for a in animais])).all():
                    identificacao[e.sisbov] = e.data_brincagem
        except Exception:
            identificacao = {}
    racas = {r.id: r.nome for r in db.query(Raca).filter(Raca.id.in_({a.id_raca for a in animais if a.id_raca} or {0})).all()}

    prop_destino_nome = _texto(pp.estabelecimento) if pp else ''
    codigo_mapa_dest = _texto(pp.codigo_mapa) if pp else ''
    certificadora = ''
    if propriedade is not None and propriedade.certificadora is not None:
        certificadora = _texto(propriedade.certificadora.razao_social)
    data_saida = max((l.data_saida for l in linhas if l.data_saida), default=None)

    return {
        'numero_comunicado': numero,
        'cidade': _texto(propriedade.municipio) if propriedade else '',
        'data': _data_br(data_saida),
        'certificadora': certificadora,
        'origem': {
            'produtor_nome': _texto(produtor.nome) if produtor else '-', 'cpf': cpf, 'cnpj': cnpj,
            'inscricao_estadual': inscricao,
            'propriedade_nome': _texto(propriedade.nome) if propriedade else '-',
            'codigo_mapa': _texto(propriedade.codigo_mapa) if propriedade and propriedade.codigo_mapa else (_texto(propriedade.oesa) if propriedade else ''),
            'nirf_incra': _texto(propriedade.nirf_incra) if propriedade else '',
            'municipio': _texto(propriedade.municipio) if propriedade else '', 'uf': _texto(propriedade.uf) if propriedade else '',
        },
        'destino': {
            'produtor_nome': _texto(parceiro.nome) if parceiro else '-',
            'cpf_cnpj': _texto(parceiro.cpf_cnpj) if parceiro else '',
            'propriedade_nome': prop_destino_nome, 'codigo_mapa': codigo_mapa_dest,
        },
        'motivo': primeira.motivo_posse,
        'justificativa': primeira.justificativa_posse or '',
        'dtas': [{
            'serie': _texto(gtas[l.id_gta].serie_gta) if l.id_gta in gtas else '',
            'numero': _texto(l.gta_numero), 'emissao': _data_br(l.gta_data_emissao),
            'validade': _data_br(l.gta_data_validade), 'animais': l.qtd_animais or 0,
        } for l in linhas],
        'total': len(animais),
        'machos': sum(1 for a in animais if 'FEMEA' not in str(a.sexo).upper()),
        'femeas': sum(1 for a in animais if 'FEMEA' in str(a.sexo).upper()),
        'animais': [{
            'sisbov': a.sisbov, 'nascimento': _data_br(a.nascimento), 'raca': racas.get(a.id_raca, '-'),
            'sexo': 'Fêmea' if 'FEMEA' in str(a.sexo).upper() else 'Macho',
            'identificacao': _data_br(identificacao.get(a.sisbov)),
        } for a in animais],
    }


# =========================================================
# FIM DE ARQUIVO: backend\utils\comunicado_saida_display.py
# =========================================================
