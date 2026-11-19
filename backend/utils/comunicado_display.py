# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\utils
# MODULO:       backend\utils\comunicado_display.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-09-16 10:25 -03
# ATUALIZADO EM: 2026-11-13 19:10 -03
# VERSAO: 1.6.0
# v1.6.0: Sessao 123 (2026-11-13 19:10 -03) - AUDITORIA ETAPA 6 (Regra #72): limpeza de CPF/CNPJ pela funcao central. REVERSAO: .bak_antes_etapa6c.
# v1.5.1: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras do CNPJ mantidas na limpeza e na formatacao. REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Funcoes compartilhadas entre "Impressao Comunicado" e
#     "Reimpressao Comunicado" (backend/routers/impressao_
#     comunicado.py e reimpressao_comunicado.py) - evita duplicar a
#     logica de agrupamento de linhas de tb_2012_com_entrada por
#     numero_comunicado, e a montagem do "contexto" usado para gerar
#     o PDF do Anexo XIX (backend/utils/pdf_anexo_xix.py).
#
#     Nao faz commit/flush - so leitura e montagem de estrutura em
#     memoria. Quem grava (status/data_envio) e o router de
#     Impressao, nunca este arquivo. ATENCAO: por ler atributos dos
#     objetos do banco, estas funcoes precisam ser chamadas ANTES de
#     qualquer commit na mesma sessao (regra da Sessao 078 - ver
#     impressao_comunicado.py v1.2.0).
#
#     Este mesmo padrao (agrupar por numero de documento oficial +
#     montar contexto para PDF) tende a se repetir quando
#     construirmos Impressao/Reimpressao de Saida, Transferencia e
#     Morte - ver "Padrao Reutilizavel Nº3" na base de padroes do
#     projeto.
#
#     v1.0.0: Criacao do modulo (Sessao 054), junto com os modulos
#             de Impressao/Reimpressao de Comunicado de Entrada.
#     v1.1.0: Sessao 080 (25/09/2026, 09:10 -03) - agrupar_
#             comunicados_por_numero() ganha o parametro opcional
#             'decrescente' (padrao False = crescente, comportamento
#             de sempre). A Reimpressao passa a listar o Comunicado
#             mais recente no topo (pedido de Benedito); a Impressao
#             continua crescente (primeiro o mais antigo a imprimir).
#             Nenhuma outra mudanca.
#     v1.2.0: Sessao 091 (08/10/2026, 20:45 -03) - agrupar_comunicados_por_numero()
#             passa a devolver tambem data_envio, impresso_em e
#             id_usuario_impressao (para a Reimpressao mostrar quando e por
#             quem). Nenhuma outra mudanca.
#     v1.3.0: Sessao 101 (20/10/2026, 18:55 -03) - Anexo XIX no visual do Magic: o contexto passa a trazer cpf e cnpj (destino: principal do Produtor + secundario da fazenda; origem: pelo tamanho do documento do Parceiro) no lugar de produtor_cpf.  REVERSAO: .bak_antes_visual_magic_s101
#     v1.3.1: Sessao 101 (20/10/2026, 19:10 -03) - Municipio da ORIGEM sai so como municipio_nome (a UF ja vem na Localidade; antes saia "... / AM / AM").  REVERSAO: .bak_antes_uf_s101
#     v1.5.0: Sessao 108 (29/10/2026, 19:30 -03) - Transferencia ENTRE PRODUTORES: 'Saida ja impressa?' tambem olha o schema do Produtor de origem; Anexo XIX mostra o Produtor de origem (nome e CPF/CNPJ dele).  REVERSAO: .bak_antes_s108_entre_produtores
#     v1.4.0: Sessao 107 (28/10/2026) - Transferencia: agrupar (tipo, numero) e mostrar Propriedade de origem; so imprime depois da Saida impressa; Anexo XIX com origem = Propriedade de origem da GTA e Data de Entrada = Data de Saida.  REVERSAO: .bak_antes_s107zh
# =========================================================

from backend.models import Propriedade
from backend.models.tb_2011_com_saidas import ComunicadoSaida
from backend.models.tb_4001_gta import Gta
from backend.models.propriedade_produtor import PropriedadeProdutor
from backend.models.tb_2001_entradas import Entrada
from backend.utils.documentos_produtor import documentos_do_produtor
from backend.utils.saida_transfer_impressa import ids_gta_com_saida_impressa
from backend.models.produtor import Produtor
from backend.utils.validadores import limpar_documento


# -------------------------------------------------------
# Agrupa uma lista PLANA de linhas de ComunicadoEntrada (1 linha por
# GTA) em uma lista de dicionarios, 1 por numero_comunicado - usado
# nas telas de listagem (Impressao mostra so ABERTO, Reimpressao
# mostra TODOS - o filtro de status fica no router, nao aqui).
#
# decrescente (v1.1.0): False (padrao) = numero_comunicado crescente;
# True = mais recente primeiro (Reimpressao).
#
# Assume que todas as linhas de um mesmo numero_comunicado
# compartilham a mesma procedencia (id_parceiro_propriedade) - valido
# porque a geracao (comunicado_entrada.py, _montar_lotes_pendentes)
# so agrupa GTAs da MESMA procedencia num mesmo lote/numero.
# -------------------------------------------------------
def info_transferencia(db, linhas):
    """{id_gta: (Propriedade de origem, Saida ja impressa?)} das linhas de Transferencia (Pacote 5)."""
    ids = [l.id_gta for l in linhas if l.tipo_entrada == 'TRANSFERENCIA' and l.id_gta]
    if not ids or db is None:
        return {}
    origem = {}
    gtas = db.query(Gta).filter(Gta.id.in_(ids)).all()
    for gta in gtas:
        origem[gta.id] = db.get(Propriedade, gta.id_propriedade)
    impressas = ids_gta_com_saida_impressa(db, gtas)   # v1.5.0: schema atual ou o do Produtor de origem
    return {i: (origem.get(i), i in impressas) for i in ids}


def agrupar_comunicados_por_numero(linhas, decrescente=False, db=None):
    grupos = {}
    for linha in linhas:
        grupos.setdefault((linha.tipo_entrada == 'TRANSFERENCIA', linha.numero_comunicado), []).append(linha)

    info_t = info_transferencia(db, linhas)

    resultado = []
    for (eh_transfer, numero), grupo in grupos.items():
        parceiro_propriedade = grupo[0].parceiro_propriedade
        parceiro = parceiro_propriedade.parceiro if parceiro_propriedade else None

        # "Data Entrada" = gta_data_validade (confirmado por Benedito,
        # Sessao 054). MAX() e so uma garantia extra caso um dia as
        # GTAs do mesmo Comunicado divirjam.
        data_entrada = max(
            (linha.gta_data_validade for linha in grupo if linha.gta_data_validade),
            default=None,
        )

        produtor_origem = parceiro.nome if parceiro else '-'
        aguarda_saida = False
        if eh_transfer:
            props = [info_t.get(l.id_gta, (None, False)) for l in grupo]
            nomes = sorted({p[0].nome for p in props if p[0]})
            produtor_origem = ' / '.join(nomes) if nomes else '-'
            aguarda_saida = not all(p[1] for p in props)
            data_entrada = max((l.gta_data_entrega for l in grupo if l.gta_data_entrega), default=None)

        resultado.append({
            'numero_comunicado': numero,
            'transfer':          eh_transfer,
            'aguarda_saida':     aguarda_saida,
            'qtde_gtas':         len(grupo),
            'total_animais':     sum(linha.qtd_animais or 0 for linha in grupo),
            'tipo_entrada':      grupo[0].tipo_entrada,
            'produtor_origem':   produtor_origem,
            'data_entrada':      data_entrada.strftime('%d/%m/%Y') if data_entrada else '-',
            'status':            grupo[0].status,
            # v1.2.0 - quando e por quem foi impresso (so leitura).
            'data_envio':        grupo[0].data_envio,
            'impresso_em':       grupo[0].impresso_em,
            'id_usuario_impressao': grupo[0].id_usuario_impressao,
        })

    resultado.sort(key=lambda c: (c['numero_comunicado'], c['transfer']), reverse=decrescente)
    return resultado


# -------------------------------------------------------
# Monta o "contexto" (dict) esperado por gerar_pdf_anexo_xix() a
# partir das linhas reais de ComunicadoEntrada de UM numero_
# comunicado (ja filtradas/ordenadas pelo chamador - ordem
# gta_data_emissao ASC).
#
# db: sessao aberta (get_db_produtor) - usada so para buscar os
#     SISBOV de cada GTA (tb_2001), nao grava nada.
# linhas: lista de ComunicadoEntrada do mesmo numero_comunicado.
# produtor_destino: objeto Produtor (schema public) do titular do
#     schema/tenant atual - nao vem de tb_2012_com_entrada porque a
#     tabela so guarda o CPF/CNPJ denormalizado, sem FK para
#     Produtor.
# -------------------------------------------------------
def montar_contexto_anexo_xix(db, linhas, produtor_destino):
    propriedade_destino  = linhas[0].propriedade_destino
    parceiro_propriedade = linhas[0].parceiro_propriedade
    parceiro_origem      = parceiro_propriedade.parceiro if parceiro_propriedade else None

    # SISBOV de todas as GTAs do Comunicado, numeracao continua na
    # MESMA ordem das linhas recebidas (gta_data_emissao ASC) e, para
    # as entradas dentro de cada GTA, ordenadas por sisbov ASC - bate
    # com a sequencia observada no Anexo XIX real (Sessao 054).
    lista_sisbov = []
    for linha in linhas:
        entradas_gta = (
            db.query(Entrada)
            .filter_by(id_gta_entrada=linha.id_gta)
            .order_by(Entrada.sisbov.asc())
            .all()
        )
        lista_sisbov.extend(entrada.sisbov for entrada in entradas_gta)

    data_entrada = max(
        (linha.gta_data_validade for linha in linhas if linha.gta_data_validade),
        default=None,
    )
    eh_transfer = linhas[0].tipo_entrada == 'TRANSFERENCIA'
    origem_transfer = None
    if eh_transfer:
        # Transferencia: Data de Entrada = Data de Saida; a origem e a Propriedade de origem da GTA (nossa base).
        data_entrada = max((l.gta_data_entrega for l in linhas if l.gta_data_entrega), default=None)
        gta_origem = db.get(Gta, linhas[0].id_gta)
        origem_transfer = db.get(Propriedade, gta_origem.id_propriedade) if gta_origem else None

    # v1.3.0 (Sessao 101): CPF/CNPJ do Produtor DESTINO = documento principal + secundario DESTA fazenda
    # (vinculo). O Parceiro de ORIGEM tem um documento so: 11 digitos = CPF, 14 = CNPJ.
    vinculo_destino = None
    if produtor_destino is not None and propriedade_destino is not None:
        vinculo_destino = (
            db.query(PropriedadeProdutor)
            .filter_by(id_propriedade=propriedade_destino.id, id_produtor=produtor_destino.id, data_fim=None)
            .first()
        )
    cpf_destino, cnpj_destino = documentos_do_produtor(produtor_destino, vinculo_destino)

    if eh_transfer:
        # v1.5.0: Produtor de ORIGEM = o vinculado a Propriedade de origem (o proprio destino, se for o mesmo Produtor)
        produtor_origem_t = produtor_destino
        vinculo_origem = None
        if origem_transfer is not None:
            vinculos_o = db.query(PropriedadeProdutor).filter_by(id_propriedade=origem_transfer.id, data_fim=None).all()
            escolhido = next((v for v in vinculos_o if produtor_destino is not None and v.id_produtor == produtor_destino.id), None) \
                or (vinculos_o[0] if vinculos_o else None)
            if escolhido is not None:
                vinculo_origem = escolhido
                if produtor_destino is None or escolhido.id_produtor != produtor_destino.id:
                    produtor_origem_t = db.get(Produtor, escolhido.id_produtor)
        cpf_origem, cnpj_origem = documentos_do_produtor(produtor_origem_t, vinculo_origem)
        origem_dict = {
            'produtor_nome': produtor_origem_t.nome if produtor_origem_t else '-',
            'cpf':           cpf_origem,
            'cnpj':          cnpj_origem,
            'propriedade_nome': origem_transfer.nome if origem_transfer else '-',
            'municipio': (f'{origem_transfer.municipio} / {origem_transfer.uf}' if origem_transfer else '-'),
        }
    doc_origem = limpar_documento(parceiro_origem.cpf_cnpj if parceiro_origem else '')
    cpf_origem = doc_origem if len(doc_origem) != 14 else ''
    cnpj_origem = doc_origem if len(doc_origem) == 14 else ''

    return {
        'numero_comunicado': linhas[0].numero_comunicado,
        'destino': {
            'produtor_nome': produtor_destino.nome if produtor_destino else '-',
            'cpf':           cpf_destino,
            'cnpj':          cnpj_destino,
            'codigo_eras':   propriedade_destino.codigo_eras if propriedade_destino else '-',
            'propriedade_nome': propriedade_destino.nome if propriedade_destino else '-',
            'municipio': (
                f'{propriedade_destino.municipio} / {propriedade_destino.uf}'
                if propriedade_destino else '-'
            ),
        },
        'origem': origem_dict if eh_transfer else {
            'produtor_nome': parceiro_origem.nome if parceiro_origem else '-',
            'cpf':           cpf_origem,
            'cnpj':          cnpj_origem,
            'propriedade_nome': parceiro_propriedade.estabelecimento if parceiro_propriedade else '-',
            # a UF ja vem na Localidade (municipio_nome); nao se acrescenta a UF do cadastro (Benedito, Sessao 101)
            'municipio': parceiro_propriedade.municipio_nome if parceiro_propriedade else '-',
        },
        'gtas': [
            {
                'numero':       linha.gta_numero,
                'qtde_animais': linha.qtd_animais,
                'data_emissao': linha.gta_data_emissao.strftime('%d/%m/%Y') if linha.gta_data_emissao else '-',
            }
            for linha in linhas
        ],
        'total_animais': sum(linha.qtd_animais or 0 for linha in linhas),
        'data_entrada':  data_entrada.strftime('%d/%m/%Y') if data_entrada else '-',
        'sisbov':        lista_sisbov,
    }

# =========================================================
# FIM DE ARQUIVO: backend\utils\comunicado_display.py
# =========================================================