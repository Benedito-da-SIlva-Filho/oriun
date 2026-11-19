# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\routers
# MODULO: backend\routers\saida_leitor.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-16 20:30 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.9.0
# v1.9.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (3 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.8.0: Sessao 120 (2026-11-10 14:05 -03) - Animal vinculado a OUTRA GTA nao aparece mais na lista "lidos nesta data" nem no contador GRAVADOS da Leitura (Regra de Ouro #67; decisao do Benedito). REVERSAO: .bak_antes_s120_oculta_vinc.
# v1.7.0: Sessao 120 (2026-11-10 13:40 -03) - Regra de Ouro #67: animal VINCULADO a uma GTA nunca aparece como livre. Selecao separa livres x vinculados (com o numero da GTA); Leitura mostra a etiqueta da GTA no animal vinculado. REVERSAO: .bak_antes_s120_livres_abate.
#
# DESCRICAO:
#     Leitor do Abate (Sessao 098) - leitura dos animais que embarcam,
#     no brete. Molde: brincagem_leitor.py. Navegacao: Home -> card
#     "Saidas" -> Hub de Saidas (hub_entrada_agrupado.py, slug 'saida')
#     -> card "Leitor do Abate".
#
#     FLUXO (3 telas, igual ao Leitor da Brincagem):
#       1. /produtor/saida-leitor/iniciar - resolve Propriedade E Produtor
#          (Padrao Reutilizavel N.1). Com 1 par ou fazenda em uso, pula
#          direto para a Selecao.
#       2. /produtor/saida-leitor/selecao - Data Leitura (hoje, editavel),
#          Sexo (MACHO/FEMEA) e Peso Minimo (padrao 100), mais as leituras
#          em aberto por data (sem botao Limpar Leitura desde a v1.1.0).
#       3. /produtor/saida-leitor/leitura - cursor sempre no SISBOV. A
#          checagem de cada animal e por AJAX (checar), a gravacao tambem
#          (gravar). Botao Manejo: identifica o animal pelo Manejo (+ DV
#          nos brincos 105) quando o brinco foi perdido ou nao le.
#
#     A LEITURA NAO DA BAIXA: grava so em tb_2020_embarque (sts=False).
#     A baixa (tb_2001 -> tb_2002 + tb_2017) acontece na geracao do
#     Comunicado de Saida (pacote futuro). O peso digitado aqui fica em
#     tb_2020.peso_saida; a pesagem em tb_4003 so nasce na baixa.
#
#     REGRAS (fechadas com Benedito, Sessao 098):
#       - BLOQUEIAM: brinco com DV incorreto (modelo 105); animal que nao
#         esta na propriedade (se ja saiu: mensagem propria; se morreu: o
#         brinco nunca mais pode ser usado, e a tentativa fica em
#         tb_5003); Sexo diferente do escolhido na Selecao; animal sem Liberacao
#         de Abate (erro de cadastro); peso vazio ou abaixo do Peso Minimo.
#       - BRINCO JA LIDO (leitura em aberto, ainda sem Comunicado): NAO bloqueia
#         mais. A tela mostra a leitura antiga (data, hora e peso) e o usuario
#         escolhe: EXCLUIR a antiga e usar a nova (a antiga e apagada, sem log) ou
#         MANTER a antiga e desistir da atual. Quem le no brete decide sozinho
#         (sem nivel extra de permissao). Vale para o Leitor e para o Manejo.
#       - AVISOS com "Responsabilidade do Produtor" (so liberam o Gravar
#         depois de marcados; quem aceitou e quando fica gravado):
#           A) fora da Liberacao para Abate (liberacao_abate > Data Leitura);
#           B) idade ERAS de 0 a 12 meses (ate o dia final da faixa
#              "04 a 12 Meses" de tb_4006).
#       - Elemento (opcional): vazio = o animal tem brinco e botton. Pelo
#         Leitor a lista so oferece BOTTON; pelo Manejo, so BRINCO.
#       - Lote de Saida vem com o Lote de Entrada do animal e o brete pode
#         trocar. Hora do embarque gravada sozinha.
#       - Peso Anterior / Ganho / Ganho por dia: calculados na tela a
#         partir da ultima pesagem do animal (tb_4003); Diarias = dias
#         desde essa pesagem.
#     O botao Limpar Leitura (que apagava todas as leituras em aberto) foi
#     RETIRADO na v1.1.0: podia apagar uma leitura importante.
#
#     v1.0.0: Criacao (Sessao 098).
#     v1.1.0: Sessao 099 (17/10/2026, 11:35 -03) - Retirado o Limpar Leitura (rota
#             limpar e imports/constante do Log de Operacoes, que so ela usava).
#             Brinco com leitura em aberto agora devolve 'repetido' (checar) e a
#             nova rota excluir_antiga apaga so a leitura em aberto DAQUELE animal
#             nesta Propriedade, a pedido do usuario. Decisoes do Benedito: sem log,
#             sem nivel extra de permissao. Mensagem de 'ja conferido' do gravar
#             deixou de citar o Limpar Leitura.
#     v1.1.1: Sessao 099 (17/10/2026, 12:50 -03) - Manejo: o DV so e pedido quando ajuda. Se o Manejo
#             digitado casa com mais de um animal e ha brinco modelo 105 entre eles (e o DV ainda nao foi
#             digitado), checar devolve pede_dv=True e a tela mostra o campo DV na hora. Sem brinco 105
#             a mensagem continua a de Manejo duplicado (o DV nao ajudaria). Nada mais mudou.
#     v1.2.0: Sessao 104 (23/10/2026, 12:25 -03) - TRAVA DA SAIDA: animal de Compra sem Comunicado de Entrada, ou de Nascimento sem
#             Notificacao gerada, e BLOQUEADO na leitura (utils/entrada_comunicada.py). Vale tambem para Bastao, Abate por Arquivo,
#             Substituicao e Troca, que reusam _validar_leitura. REVERSAO: .bak_antes_s104h.
#     v1.3.0: Sessao 105 (23/10/2026, 18:15 -03) - Animal que nao esta mais em estoque diz ONDE esta: 'Animal ja saiu da Propriedade: ABATE em dd/mm/aaaa.'
#             (tipo + data, via utils\animal_saiu.py), agora tambem na busca pelo MANEJO (antes so pelo SISBOV). REVERSAO: .bak_antes_s105c.
#     v1.4.0: Sessao 107 (28/10/2026, 09:25 -03) - TRANSFERENCIA (pacote 2): os contadores GRAVADOS/lidos da Leitura e a lista de leituras em aberto da Selecao
#             passam a contar SO tipo_saida = ABATE (antes contavam tudo que estava em tb_2020). Sem isso a Transferencia, que grava na mesma tabela,
#             apareceria como Abate. Nenhuma outra mudanca. REVERSAO: .bak_antes_s107.
#     v1.6.0: Sessao 110 (31/10/2026, 11:31 -03) - CORRECAO: brinco de animal que ja saiu (ex.: Transferencia) estourava erro na tela ('verifique sua conexao') porque o texto da mensagem era lido do objeto DEPOIS do commit da rejeicao; agora o texto e montado ANTES. Brinco sem animal passa a orientar: no estoque de brincos (tb_7017, status vazio) = 'Brinco está no estoque.'; CANCELADO = 'Brinco cancelado...'; nao achou em lugar nenhum = 'Animal não encontrado. Confira o brinco.' REVERSAO: .bak_antes_s110_sem_animal.
#     v1.5.0: Sessao 108 (29/10/2026, 21:00 -03) - Nova rota excluir_leitura (botao X na lista Geral): so leitura em aberto e sem GTA vinculada. Lista Geral passa a informar 'vinculado'. REVERSAO: .bak_antes_s108_excluir_leitura.
#     v1.6.1: Sessao 114 (04/11/2026, 10:37 -03) - Abate: mensagem de peso abaixo do minimo vira "Peso incorreto, verifique.". Regra do Peso Minimo nao mudou.  REVERSAO: .bak_antes_s114_peso.
# =========================================================

from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request, redirect, session, jsonify
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade, PropriedadeProdutor, Produtor
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_2020_embarque import Embarque
from backend.models.tb_4001_gta import Gta
from backend.utils.leituras_vinculo import resumo_abertas, numeros_gta, marcar_gtas_atendidas   # s120 - Regra de Ouro #67
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.models.tb_parceiros import Parceiro
from backend.models.tb_5003_rejeicoes_brincagem import RejeicaoBrincagem
from backend.models.tb_7017_entrada_brincos_rfid import EntradaBrincoRfid   # v1.6.0 - brinco do estoque / cancelado
from backend.routers.auth import redirecionar_home, buscar_pares_propriedade_produtor, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.entrada_comunicada import motivo_entrada_pendente   # v1.2.0 - trava da Saida
from backend.utils.animal_saiu import mensagem_animal_saiu, texto_animal_saiu   # v1.3.0 - onde o animal esta
from backend.utils.regras_sisbov import (
    MODELO_SISBOV_ANTIGO, TAMANHO_SISBOV, modelo_do_sisbov, sisbov_confere,
)


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
saida_leitor = Blueprint('saida_leitor', __name__)


# Mesmo cuidado do Leitor da Brincagem: nada de cache (o catalogo e as
# leituras mudam de Produtor para Produtor).
@saida_leitor.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


# -------------------------------------------------------
# Constantes
# -------------------------------------------------------
URL_HUB       = '/produtor/hub-novo/saida'
URL_INICIAR   = '/produtor/saida-leitor/iniciar'
URL_SELECAO   = '/produtor/saida-leitor/selecao'
VOLTAR_SELECIONAR_PROPRIEDADE = URL_HUB

TIPO_SAIDA_ABATE   = 'ABATE'
SEXOS              = (('MACHO', 'Macho'), ('FEMEA', 'Fêmea'))
CODIGOS_SEXO       = tuple(codigo for codigo, _ in SEXOS)
PESO_MINIMO_PADRAO = Decimal('100')
TAMANHO_MANEJO     = 6
DIAS_MAX_ERA_0_12_PADRAO = 394        # fim da faixa "04 a 12 Meses" (GR4006); a faixa real vem de tb_4006
CODIGO_FAIXA_ERA_0_12    = 2          # codigo_geras da faixa "04 a 12 Meses"

# Elemento: so o que o brete escolhe (vazio = tem os dois).
ELEMENTO_POR_VIA = {'LEITOR': 'BOTTON', 'MANEJO': 'BRINCO'}

MOTIVO_MORTO       = 'Abate: brinco de animal morto'
MOTIVO_JA_SAIU     = 'Abate: animal ja saiu'

MENSAGEM_DV_INCORRETO = 'Brinco com dígito verificador (DV) incorreto. Confira o número lido ou digitado.'
MENSAGEM_SISBOV_TAMANHO = 'O brinco deve ter 15 dígitos numéricos.'
MENSAGEM_MANEJO_INCORRETO = f'Digite os {TAMANHO_MANEJO} números do Manejo.'
MENSAGEM_DV_MANEJO_INCORRETO = 'O DV do Manejo deve ser um número de 0 a 9.'
MENSAGEM_NAO_ENCONTRADO = 'Animal não encontrado. Confira o brinco.'
MENSAGEM_BRINCO_NO_ESTOQUE = 'Brinco está no estoque.'   # v1.6.0 - brinco comprado, ainda sem animal (tb_7017 status vazio)
MENSAGEM_BRINCO_CANCELADO = 'Brinco cancelado. Não pode ser usado.'   # v1.6.0 - tb_7017 status CANCELADO
MENSAGEM_MANEJO_PEDE_DV = (
    'Há mais de um animal com este Manejo (brincos modelo 105). '
    'Digite o DV do brinco e busque de novo.'
)
MENSAGEM_MANEJO_DUPLICADO = (
    'Este Manejo foi encontrado em mais de um animal desta Propriedade. '
    'Digite o DV do brinco (modelo 105) ou leia o brinco. Se continuar, avise a Consiste.'
)
MENSAGEM_SEM_LIBERACAO = 'Animal sem Liberação de Abate (erro de cadastro). Avise a Consiste.'
MENSAGEM_JA_CONFERIDO = ('Animal já conferido (leitura em aberto). Leia o brinco de novo para escolher '
                         'entre excluir ou manter a leitura anterior.')

MENSAGENS_ERRO_SELECAO = {
    'data':    'Data Leitura incorreta. Digite no formato dd/mm/aaaa.',
    'sexo':    'Escolha o Sexo (Macho ou Fêmea).',
    'peso':    'Peso Mínimo incorreto. Digite um número em quilos.',
}


# -------------------------------------------------------
# Trava de seguranca: a Propriedade tem de ser de um par Propriedade/
# Produtor do usuario logado E do Produtor da sessao (e a fazenda em
# uso, se houver). Mesma regra do Leitor da Brincagem.
# -------------------------------------------------------
def _propriedade_do_usuario(id_propriedade):
    try:
        id_int = int(id_propriedade)
    except (TypeError, ValueError):
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and par_em_uso.id_propriedade != id_int:
        return False
    return any(
        par.id_propriedade == id_int and par.id_produtor == session.get('id_produtor')
        for par in pares
    )


def _negado():
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if resolver_fazenda_em_uso(pares) is not None:
        return redirect(URL_INICIAR)
    return redirecionar_home()


# -------------------------------------------------------
# Utilitarios pequenos
# -------------------------------------------------------
def _data_br(data):
    return data.strftime('%d/%m/%Y') if data else ''


def _ler_data_br(texto):
    try:
        return datetime.strptime((texto or '').strip(), '%d/%m/%Y').date()
    except ValueError:
        return None


def _ler_decimal(texto):
    try:
        valor = Decimal(str(texto).strip().replace(',', '.'))
    except (InvalidOperation, AttributeError):
        return None
    if valor.is_nan() or valor.is_infinite():
        return None
    return valor


def _formatar_kg(valor):
    """Peso para a tela: sem zeros sobrando (500, 500,5, 500,25)."""
    texto = f'{Decimal(valor):.2f}'.rstrip('0').rstrip('.')
    return texto.replace('.', ',')


def _faixa_idade(faixas, dias):
    if dias is None:
        return ''
    for faixa in faixas:
        if faixa.dias_min <= dias <= faixa.dias_max:
            return faixa.descricao
    return ''


def _dias_max_era_0_12(faixas):
    for faixa in faixas:
        if faixa.codigo_geras == CODIGO_FAIXA_ERA_0_12:
            return faixa.dias_max
    return DIAS_MAX_ERA_0_12_PADRAO


def _dv_incorreto(sisbov):
    return modelo_do_sisbov(sisbov) == MODELO_SISBOV_ANTIGO and not sisbov_confere(sisbov)


def _registrar_rejeicao(db, id_propriedade, sisbov, motivo):
    """Tentativa barrada fica em tb_5003 (mesma tabela das rejeicoes da Brincagem)."""
    db.add(RejeicaoBrincagem(
        id_propriedade=int(id_propriedade),
        id_usuario=session['usuario_id'],
        sisbov=sisbov,
        rfid='',
        motivo=motivo[:150],
        data_tentativa=date.today(),
    ))
    db.commit()


def _contar_gravados_na_data(db, id_propriedade, data_leitura):
    return (
        db.query(func.count(Embarque.id))
        .filter(
            Embarque.id_propriedade == int(id_propriedade),
            Embarque.tipo_saida == TIPO_SAIDA_ABATE,   # v1.4.0 - so Abate (Transferencia tem contador proprio)
            Embarque.data_embarque == data_leitura,
            Embarque.sts == False,   # noqa: E712
            Embarque.id_gta.is_(None),   # s120 - so os livres
        )
        .scalar()
    ) or 0


def _lidos_da_data(db, id_propriedade, data_leitura):
    linhas = (
        db.query(Embarque)
        .filter(
            Embarque.id_propriedade == int(id_propriedade),
            Embarque.tipo_saida == TIPO_SAIDA_ABATE,   # v1.4.0 - so Abate
            Embarque.data_embarque == data_leitura,
            Embarque.sts == False,   # noqa: E712
            Embarque.id_gta.is_(None),   # s120 - vinculado a GTA nao aparece
        )
        .order_by(Embarque.id.desc())
        .all()
    )
    _nums_gta = numeros_gta(db, [l.id_gta for l in linhas])   # s120 - numero da GTA do animal vinculado
    return [{
        'sisbov': l.sisbov,
        'manejo': l.manejo or '',
        'sexo': l.sexo or '',
        'peso': _formatar_kg(l.peso_saida) if l.peso_saida is not None else '',
        'hora': l.hora_embarque.strftime('%H:%M') if l.hora_embarque else '',
        'vinculado': l.id_gta is not None,
        'gta': _nums_gta.get(l.id_gta, ''),   # s120
    } for l in linhas]


# -------------------------------------------------------
# Mensagem quando o brinco NAO esta mais em tb_2001: morreu, ja saiu
# ou nunca esteve na Propriedade. Brinco de animal morto e tentativa
# de reutilizacao: barra e registra a tentativa em tb_5003.
# -------------------------------------------------------
def _mensagem_sem_animal(db, id_propriedade, sisbov):
    saida = (
        db.query(SaidaAnimal)
        .filter(SaidaAnimal.sisbov == sisbov)
        .order_by(SaidaAnimal.data_saida.desc(), SaidaAnimal.id.desc())
        .first()
    )
    if saida is None:
        # v1.6.0 - nao saiu: ve se o brinco esta no estoque de brincos (tb_7017) ou foi cancelado
        brinco = (
            db.query(EntradaBrincoRfid)
            .filter(EntradaBrincoRfid.sisbov == sisbov, EntradaBrincoRfid.id_propriedade == int(id_propriedade))
            .first()
        )
        status = (brinco.status or '').strip().upper() if brinco is not None else None
        if brinco is not None and status == '':
            return MENSAGEM_BRINCO_NO_ESTOQUE
        if brinco is not None and status == 'CANCELADO':
            return MENSAGEM_BRINCO_CANCELADO
        return MENSAGEM_NAO_ENCONTRADO
    # v1.6.0 - o texto e montado ANTES do commit da rejeicao (depois do commit o objeto expira e a leitura estoura erro)
    if saida.tipo_saida == 'MORTE':
        texto = (f'Brinco de animal que morreu em {_data_br(saida.data_saida)}. '
                 'Este brinco não pode ser usado.')
        motivo = MOTIVO_MORTO
    else:
        texto = texto_animal_saiu(saida)   # v1.3.0 - 'Animal já saiu da Propriedade: ABATE em dd/mm/aaaa.'
        motivo = MOTIVO_JA_SAIU
    _registrar_rejeicao(db, id_propriedade, sisbov, motivo)
    return texto


# -------------------------------------------------------
# Busca o animal pelo SISBOV ou pelo Manejo (+ DV, nos brincos 105).
# Devolve (animal, mensagem_de_bloqueio).
# -------------------------------------------------------
def _buscar_animal(db, id_propriedade, sisbov, manejo, dv):
    if sisbov:
        if len(sisbov) != TAMANHO_SISBOV or not (sisbov.isascii() and sisbov.isdecimal()):
            return None, MENSAGEM_SISBOV_TAMANHO
        if _dv_incorreto(sisbov):
            return None, MENSAGEM_DV_INCORRETO
        animal = (
            db.query(Entrada)
            .filter(Entrada.sisbov == sisbov, Entrada.id_propriedade == int(id_propriedade))
            .first()
        )
        if animal is None:
            return None, _mensagem_sem_animal(db, id_propriedade, sisbov)
        return animal, None

    if len(manejo) != TAMANHO_MANEJO or not (manejo.isascii() and manejo.isdecimal()):
        return None, MENSAGEM_MANEJO_INCORRETO
    if dv and not (len(dv) == 1 and dv.isascii() and dv.isdecimal()):
        return None, MENSAGEM_DV_MANEJO_INCORRETO
    candidatos = (
        db.query(Entrada)
        .filter(Entrada.id_propriedade == int(id_propriedade), Entrada.manejo == manejo)
        .all()
    )
    if dv:
        candidatos = [
            a for a in candidatos
            if modelo_do_sisbov(a.sisbov) != MODELO_SISBOV_ANTIGO or a.sisbov[-1] == dv
        ]
    if not candidatos:
        # v1.3.0 - pelo Manejo tambem diz onde o animal esta (Abate, Venda... + data)
        return None, mensagem_animal_saiu(db, id_propriedade, manejo=manejo) or MENSAGEM_NAO_ENCONTRADO
    if len(candidatos) > 1:
        # v1.1.1 - pede o DV so quando ha brinco 105 entre os candidatos e o DV ainda nao foi digitado
        tem_antigo = any(modelo_do_sisbov(a.sisbov) == MODELO_SISBOV_ANTIGO for a in candidatos)
        if tem_antigo and not dv:
            return None, MENSAGEM_MANEJO_PEDE_DV
        return None, MENSAGEM_MANEJO_DUPLICADO
    return candidatos[0], None


# -------------------------------------------------------
# Validacao completa de UM animal para a leitura. Usada pelo checar() e,
# de novo, pelo gravar() (defesa em profundidade). Devolve
#   {'bloqueio': texto}  ou  {'repetido': {leitura em aberto}}  ou
#   {'animal': Entrada, 'ficha': {...}, 'avisos': {...}}
# -------------------------------------------------------
def _validar_leitura(db, id_propriedade, data_leitura, sexo_escolha, sisbov, manejo, dv):
    animal, bloqueio = _buscar_animal(db, id_propriedade, sisbov, manejo, dv)
    if bloqueio:
        if bloqueio == MENSAGEM_MANEJO_PEDE_DV:
            return {'bloqueio': bloqueio, 'pede_dv': True}
        return {'bloqueio': bloqueio}

    motivo_entrada = motivo_entrada_pendente(db, animal)   # v1.2.0 - entrada ainda nao comunicada
    if motivo_entrada:
        return {'bloqueio': motivo_entrada}

    aberta = (
        db.query(Embarque)
        .filter(Embarque.sisbov == animal.sisbov, Embarque.sts == False)   # noqa: E712
        .order_by(Embarque.id.desc())
        .first()
    )
    if aberta is not None:
        # v1.1.0 - nao bloqueia: devolve a leitura antiga para a tela perguntar
        # (excluir a antiga e usar a nova, ou manter a antiga e desistir da atual).
        return {'repetido': {
            'sisbov': animal.sisbov,
            'data': _data_br(aberta.data_embarque),
            'peso': _formatar_kg(aberta.peso_saida) if aberta.peso_saida is not None else '',
            'hora': aberta.hora_embarque.strftime('%H:%M') if aberta.hora_embarque else '',
        }}

    if (animal.sexo or '') != sexo_escolha:
        return {'bloqueio': (f'Sexo divergente da escolha [{sexo_escolha} <> {animal.sexo or "?"}]. '
                             'Retire o animal e troque o Sexo na Seleção.')}

    if animal.liberacao_abate is None:
        return {'bloqueio': MENSAGEM_SEM_LIBERACAO}

    faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
    dias_idade = (data_leitura - animal.nascimento).days if animal.nascimento else None
    fora_liberacao = animal.liberacao_abate > data_leitura
    era_0_12 = dias_idade is not None and dias_idade <= _dias_max_era_0_12(faixas)
    faixa_texto = _faixa_idade(faixas, dias_idade)

    raca = db.get(Raca, animal.id_raca) if animal.id_raca else None
    ultimo = (
        db.query(Peso)
        .filter(Peso.sisbov == animal.sisbov)
        .order_by(Peso.sequencia.desc())
        .first()
    )
    peso_anterior = float(ultimo.peso) if ultimo is not None else None
    diarias = (data_leitura - ultimo.data_pesagem).days if ultimo is not None else None

    ficha = {
        'sisbov': animal.sisbov,
        'manejo': animal.manejo or '',
        'rfid': animal.rfid or '',
        'sexo': animal.sexo or '',
        'raca': raca.codigo if raca else '',
        'nascimento': _data_br(animal.nascimento),
        'idade_meses': faixa_texto,
        'lote_entrada': animal.lote or '',
        'liberacao_abate': _data_br(animal.liberacao_abate),
        'diarias': '' if diarias is None else diarias,
        'peso_anterior': peso_anterior,
    }
    avisos = {
        'fora_liberacao': {
            'ativo': bool(fora_liberacao),
            'texto': (f'Animal fora da Liberação para Abate: liberado em {_data_br(animal.liberacao_abate)} '
                      f'(faltam {(animal.liberacao_abate - data_leitura).days} dia(s)).') if fora_liberacao else '',
        },
        'era_0_12': {
            'ativo': bool(era_0_12),
            'texto': (f'Animal com idade ERAS de 0 a 12 meses ({faixa_texto}).') if era_0_12 else '',
        },
    }
    return {'animal': animal, 'ficha': ficha, 'avisos': avisos}


# -------------------------------------------------------
# Rota: GET /produtor/saida-leitor/iniciar - ponto de partida.
# -------------------------------------------------------
@saida_leitor.route('/produtor/saida-leitor/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    def _tela_selecionar(pares_lista, erro):
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=pares_lista,
            erro=erro,
            titulo='Leitor do Abate — Selecionar Propriedade',
            proximo=URL_SELECAO,
            campo_propriedade='id_propriedade',
            voltar=VOLTAR_SELECIONAR_PROPRIEDADE,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria='#D4370A',
            nome_sistema='Orion SISBOV',
            menu_ativo='saidas',
        )

    if len(pares) == 0:
        return _tela_selecionar([], 'Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.')

    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{URL_SELECAO}?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_SELECAO}?id_propriedade={par.id_propriedade}')

    return _tela_selecionar(pares, None)


# -------------------------------------------------------
# Rota: GET /produtor/saida-leitor/selecao - Tela 02.
# -------------------------------------------------------
@saida_leitor.route('/produtor/saida-leitor/selecao')
def selecao():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not id_propriedade:
        return redirecionar_home()
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        url_voltar = URL_INICIAR
    else:
        url_voltar = URL_HUB

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))
        nome_produtor = None
        if propriedade:
            vinculo = db.query(PropriedadeProdutor).filter_by(
                id_propriedade=propriedade.id, id_produtor=session['id_produtor'], data_fim=None
            ).first()
            if vinculo:
                produtor = db.get(Produtor, vinculo.id_produtor)
                if produtor:
                    nome_produtor = produtor.nome

    # Leituras em aberto (sem Comunicado), uma linha por data.
    try:
        with get_db_produtor(session['id_produtor']) as db_prod:
            resumo = resumo_abertas(db_prod, id_propriedade, TIPO_SAIDA_ABATE)   # s120 - livres x vinculadas
            abertas = [{'data': _data_br(r['data']), 'quantidade': r['livres'] + r['vinculados'], 'livres': r['livres'], 'vinculados': r['vinculados'], 'gtas': r['gtas_txt']} for r in resumo]
    except Exception:
        abertas = []

    return render_template(
        'produtor/saida_leitor_selecao.html',
        erro=MENSAGENS_ERRO_SELECAO.get(request.args.get('erro', '')),
        propriedade=propriedade,
        nome_produtor=nome_produtor,
        id_propriedade=id_propriedade,
        url_voltar=url_voltar,
        sexos=SEXOS,
        data_hoje=_data_br(date.today()),
        peso_minimo_padrao=_formatar_kg(PESO_MINIMO_PADRAO),
        abertas=abertas,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='saidas',
    )


# -------------------------------------------------------
# Rota: GET /produtor/saida-leitor/leitura - Tela de Leitura.
# -------------------------------------------------------
@saida_leitor.route('/produtor/saida-leitor/leitura')
def leitura():
    if 'id_produtor' not in session:
        return redirecionar_home()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return _negado()

    base = f'{URL_SELECAO}?id_propriedade={id_propriedade}'
    data_leitura = _ler_data_br(request.args.get('data_leitura', ''))
    if data_leitura is None:
        return redirect(f'{base}&erro=data')
    sexo = (request.args.get('sexo', '') or '').strip().upper()
    if sexo not in CODIGOS_SEXO:
        return redirect(f'{base}&erro=sexo')
    peso_minimo = _ler_decimal(request.args.get('peso_minimo', '')) if request.args.get('peso_minimo', '').strip() else PESO_MINIMO_PADRAO
    if peso_minimo is None or peso_minimo < 0:
        return redirect(f'{base}&erro=peso')

    with Session(engine) as db:
        propriedade = db.get(Propriedade, int(id_propriedade))

    with get_db_produtor(session['id_produtor']) as db:
        total_gravados = _contar_gravados_na_data(db, id_propriedade, data_leitura)
        lidos = _lidos_da_data(db, id_propriedade, data_leitura)

    return render_template(
        'produtor/saida_leitor_leitura.html',
        propriedade=propriedade,
        id_propriedade=id_propriedade,
        data_leitura=_data_br(data_leitura),
        sexo=sexo,
        sexo_descricao=dict(SEXOS).get(sexo, sexo),
        peso_minimo=_formatar_kg(peso_minimo),
        total_gravados=total_gravados,
        lidos=lidos,
        url_selecao=f'{URL_SELECAO}?id_propriedade={id_propriedade}',
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria='#D4370A',
        nome_sistema='Orion SISBOV',
        menu_ativo='saidas',
    )


# -------------------------------------------------------
# Rota: POST /produtor/saida-leitor/checar (AJAX) - confere o animal
# assim que o SISBOV e lido (ou o Manejo e digitado).
# -------------------------------------------------------
@saida_leitor.route('/produtor/saida-leitor/checar', methods=['POST'])
def checar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = (dados.get('sisbov') or '').strip()
    manejo = (dados.get('manejo') or '').strip()
    dv     = (dados.get('dv') or '').strip()
    sexo   = (dados.get('sexo') or '').strip().upper()
    data_leitura = _ler_data_br(dados.get('data_leitura'))

    if not id_propriedade or (not sisbov and not manejo) or data_leitura is None or sexo not in CODIGOS_SEXO:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou. Volte ao Hub de Saídas e abra de novo.'}), 403

    with get_db_produtor(session['id_produtor']) as db:
        resultado = _validar_leitura(db, id_propriedade, data_leitura, sexo, sisbov, manejo, dv)

    if 'bloqueio' in resultado:
        return jsonify({'bloqueio': True, 'mensagem': resultado['bloqueio'], 'pede_dv': bool(resultado.get('pede_dv'))})
    if 'repetido' in resultado:
        return jsonify({'repetido': True, 'leitura_antiga': resultado['repetido']})
    return jsonify({'ok': True, 'animal': resultado['ficha'], 'avisos': resultado['avisos']})


# -------------------------------------------------------
# Rota: POST /produtor/saida-leitor/gravar (AJAX) - grava a leitura em
# tb_2020_embarque. Confere TUDO de novo no servidor.
# -------------------------------------------------------
@saida_leitor.route('/produtor/saida-leitor/gravar', methods=['POST'])
def gravar():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = (dados.get('sisbov') or '').strip()
    sexo   = (dados.get('sexo') or '').strip().upper()
    via    = (dados.get('via') or '').strip().upper()
    elemento = (dados.get('elemento') or '').strip().upper()
    lote_saida = (dados.get('lote_saida') or '').strip()
    data_leitura = _ler_data_br(dados.get('data_leitura'))
    peso_minimo = _ler_decimal(dados.get('peso_minimo'))
    peso = _ler_decimal(dados.get('peso'))
    aceite_fora = bool(dados.get('aceite_fora_liberacao'))
    aceite_era  = bool(dados.get('aceite_era_0_12'))

    if not id_propriedade or not sisbov or data_leitura is None or sexo not in CODIGOS_SEXO or via not in ELEMENTO_POR_VIA:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou. Volte ao Hub de Saídas e abra de novo.'}), 403
    if peso_minimo is None or peso_minimo < 0:
        peso_minimo = PESO_MINIMO_PADRAO
    if peso is None or peso <= 0:
        return jsonify({'erro': 'Digite o Peso do animal.'}), 400
    if peso < peso_minimo:
        return jsonify({'erro': 'Peso incorreto, verifique.'}), 400
    if elemento and elemento != ELEMENTO_POR_VIA[via]:
        return jsonify({'erro': 'Elemento incorreto para esta forma de leitura.'}), 400
    if len(lote_saida) > 30:
        return jsonify({'erro': 'Lote de Saída com mais de 30 caracteres.'}), 400

    with get_db_produtor(session['id_produtor']) as db:
        resultado = _validar_leitura(db, id_propriedade, data_leitura, sexo, sisbov, '', '')
        if 'bloqueio' in resultado:
            return jsonify({'bloqueio': True, 'mensagem': resultado['bloqueio'], 'erro': resultado['bloqueio']}), 409
        if 'repetido' in resultado:
            # a tela deveria ter perguntado antes; se chegou aqui, o servidor nao grava por cima
            return jsonify({'bloqueio': True, 'mensagem': MENSAGEM_JA_CONFERIDO, 'erro': MENSAGEM_JA_CONFERIDO}), 409

        avisos = resultado['avisos']
        if avisos['fora_liberacao']['ativo'] and not aceite_fora:
            return jsonify({'erro': 'Animal fora da Liberação para Abate: marque "Responsabilidade do Produtor".'}), 400
        if avisos['era_0_12']['ativo'] and not aceite_era:
            return jsonify({'erro': 'Animal com idade ERAS de 0 a 12 meses: marque "Responsabilidade do Produtor".'}), 400

        animal = resultado['animal']
        gta = db.get(Gta, animal.id_gta_entrada) if animal.id_gta_entrada else None
        origem = db.get(Parceiro, animal.id_origem) if animal.id_origem else None
        agora = datetime.now()
        id_usuario = session.get('usuario_id')

        embarque = Embarque(
            id_propriedade=int(id_propriedade),
            id_animal=animal.id,
            sisbov=animal.sisbov,
            manejo=animal.manejo,
            rfid=animal.rfid,
            id_especie=animal.id_especie,
            sexo=animal.sexo,
            nascimento=animal.nascimento,
            eras_dias=animal.eras_dias,
            id_aptidao=animal.id_aptidao,
            id_raca=animal.id_raca,
            cota_hilton=bool(animal.cota_hilton),
            liberacao_abate=animal.liberacao_abate,
            gta_entrada=((gta.numero_gta_completo or '')[:10] or None) if gta else None,
            gta_entrada_emissao=gta.data_emissao if gta else None,
            gta_entrada_validade=gta.data_validade if gta else None,
            gta_entrada_animais=gta.qtde_animais if gta else None,
            data_inclusao=animal.data_inclusao,
            lote_entrada=animal.lote,
            origem_propriedade=(origem.nome or '')[:150] if origem else None,
            origem_cpf_cnpj=origem.cpf_cnpj if origem else None,
            tipo_saida=TIPO_SAIDA_ABATE,
            data_embarque=data_leitura,
            hora_embarque=agora.time().replace(microsecond=0),
            lote_saida=lote_saida or None,
            peso_saida=peso.quantize(Decimal('0.01')),
            elemento=elemento or None,
            aceite_fora_liberacao=bool(avisos['fora_liberacao']['ativo']),
            aceite_fora_liberacao_por=id_usuario if avisos['fora_liberacao']['ativo'] else None,
            aceite_fora_liberacao_em=agora if avisos['fora_liberacao']['ativo'] else None,
            aceite_era_0_12=bool(avisos['era_0_12']['ativo']),
            aceite_era_0_12_por=id_usuario if avisos['era_0_12']['ativo'] else None,
            aceite_era_0_12_em=agora if avisos['era_0_12']['ativo'] else None,
            sts=False,
        )
        db.add(embarque)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            return jsonify({'bloqueio': True, 'erro': MENSAGEM_JA_CONFERIDO,
                            'mensagem': MENSAGEM_JA_CONFERIDO}), 409

        total_gravados = _contar_gravados_na_data(db, id_propriedade, data_leitura)
        hora_txt = embarque.hora_embarque.strftime('%H:%M')
        manejo_txt = animal.manejo or ''
        db.commit()

    return jsonify({
        'sucesso': True,
        'mensagem': 'Gravação Efetuada com Sucesso',
        'sisbov': sisbov,
        'manejo': manejo_txt,
        'sexo': sexo,
        'peso': _formatar_kg(peso),
        'hora': hora_txt,
        'total_gravados': total_gravados,
    })


# -------------------------------------------------------
# Rota: POST /produtor/saida-leitor/excluir-antiga (AJAX) - o usuario
# escolheu "Excluir a antiga e usar a nova" para um brinco que ja tinha
# leitura em aberto. Apaga SO a leitura em aberto (sem Comunicado) DESTE
# animal nesta Propriedade. Sem log: nao existe historico dessa leitura
# (decisao do Benedito, Sessao 099). Confere que a Propriedade e do usuario.
# -------------------------------------------------------
@saida_leitor.route('/produtor/saida-leitor/excluir-antiga', methods=['POST'])
def excluir_antiga():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = (dados.get('sisbov') or '').strip()
    if not id_propriedade or not sisbov:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou.'}), 403

    with get_db_produtor(session['id_produtor']) as db:
        removidos = (
            db.query(Embarque)
            .filter(
                Embarque.id_propriedade == int(id_propriedade),
                Embarque.sisbov == sisbov,
                Embarque.sts == False,   # noqa: E712
            )
            .delete(synchronize_session=False)
        )
        db.commit()

    return jsonify({'removidos': int(removidos)})


# -------------------------------------------------------
# Rota: POST /produtor/saida-leitor/excluir-leitura (AJAX) - EXCLUIR UMA LEITURA da lista "Geral" (Sessao 108).
# Apaga SO a leitura em aberto (sem Comunicado) e AINDA NAO vinculada a uma GTA.
# Depois de vinculada, o caminho e o Desvincular. Fica uma linha no log do servidor (quem, qual brinco, quando).
# -------------------------------------------------------
@saida_leitor.route('/produtor/saida-leitor/excluir-leitura', methods=['POST'])
def excluir_leitura():
    if 'id_produtor' not in session:
        return jsonify({'erro': 'Sessão expirada.'}), 401

    dados = request.get_json(silent=True) or {}
    id_propriedade = dados.get('id_propriedade')
    sisbov = (dados.get('sisbov') or '').strip()
    data_leitura = _ler_data_br(dados.get('data_leitura'))
    id_gta_tela = dados.get('id_gta')
    if not id_propriedade or not sisbov or data_leitura is None:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    if not _propriedade_do_usuario(id_propriedade):
        return jsonify({'erro': 'Propriedade não pertence ao seu usuário ou a fazenda em uso mudou.'}), 403

    with get_db_produtor(session['id_produtor']) as db:
        linha = (
            db.query(Embarque)
            .filter(Embarque.id_propriedade == int(id_propriedade),
                    Embarque.tipo_saida == TIPO_SAIDA_ABATE,
                    Embarque.data_embarque == data_leitura,
                    Embarque.sts == False, Embarque.sisbov == sisbov)
            .first()
        )
        if linha is None:
            return jsonify({'erro': 'Leitura não encontrada (já foi excluída ou o embarque já foi concluído).'}), 404
        if linha.id_gta is not None:
            return jsonify({'erro': 'Esta leitura já está vinculada a uma GTA. Use o Desvincular antes de excluir.'}), 409
        db.delete(linha)
        db.flush()
        total_gravados = _contar_gravados_na_data(db, id_propriedade, data_leitura)
        db.commit()

    try:
        from flask import current_app
        current_app.logger.info('EXCLUIR LEITURA Abate: produtor=%s propriedade=%s sisbov=%s data=%s',
                                session.get('id_produtor'), id_propriedade, sisbov, dados.get('data_leitura'))
    except Exception:
        pass
    return jsonify({'sucesso': True, 'total_gravados': total_gravados, 'gta_progresso': None})

# =========================================================
# FIM DE ARQUIVO: backend\routers\saida_leitor.py
# =========================================================
