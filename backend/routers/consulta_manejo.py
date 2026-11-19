# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\routers
# MODULO:       backend\routers\consulta_manejo.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-10-04 14:10 -03
# ATUALIZADO EM: 2026-11-19 12:30 -03
# VERSAO:       1.3.1
# v1.3.1: Sessao 133 (2026-11-19 12:30 -03) - "Origem" da ficha mostra o nome (Compra, Nascimento / Desmame, Carga) em vez do codigo cru. REVERSAO: .bak_antes_s133_carga.
# v1.3.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Modulo "Consulta por Manejo" - o usuario digita o Manejo (os 6
#     numeros que identificam o animal na Propriedade) e a tela mostra
#     a ficha do animal EM ESTOQUE (tb_2001). Baseado na tela
#     "Consulta Entradas" do legado GERAS.
#
#     NAVEGACAO: o card existe em DOIS Hubs ao mesmo tempo (hubs.py) -
#     'entrada' (escritorio) e 'brincagem' (campo). O parametro
#     'origem' e guardado na SESSAO do Flask (mesmo padrao de
#     brincagem_consulta.py) so para o Voltar saber de qual Hub o
#     usuario veio. O Voltar NUNCA e fixo (Regra de Ouro #4): com 2+
#     pares Propriedade/Produtor volta para a selecao; com 1 so par
#     (selecao pulada) volta para o Hub de origem.
#
#     Fluxo (Padrao Reutilizavel Nº1):
#         iniciar -> (selecao se 2+ pares) -> consultar
#         (digita o Manejo -> mostra a ficha).
#
#     REGRAS DE NEGOCIO (fechadas com Benedito, 04/10/2026):
#       - Manejo = coluna tb_2001.manejo, 6 numeros. A busca exige os
#         6 numeros completos (nao completa zero a esquerda).
#       - So animais em estoque (presentes na tb_2001) da Propriedade
#         escolhida. Animal que ja saiu fica para o modulo de Saida.
#       - Espécie, Sexo, Origem e Raca aparecem como GRAVADOS (codigos:
#         BOV/BUB, MACHO/FEMEA, COMPRA/NASCTO-DESMAME, NE...).
#       - Dias (idade) = hoje - Nascimento; Confinamento = hoje -
#         Inserção BND (tb_2001.data_inclusao). Calculados na hora,
#         nunca gravados.
#       - Idade em Meses = faixa da tb_4006 que contem os Dias.
#       - GTA / Entrada: numero da GTA (tb_4001_gta) e Data de
#         Brincagem (tb_2001.data_brincagem). Animal de Nascimento
#         mostra o numero da Notificacao (NAS); COM. fica vazio.
#       - Liberação Abate = tb_2001.liberacao_abate, so exibida (nunca
#         recalculada). Selo: "Animal Liberado" ou "Aguardando -
#         liberado em dd/mm/aaaa (faltam N dias)".
#       - Peso = ultima pesagem (maior sequencia) em tb_4003_pesos.
#       - "Liberação Carência" NAO aparece: so passa a existir com o
#         modulo de medicao (Eventos).
#       - Se o mesmo Manejo aparecer em mais de um animal da
#         Propriedade, a tela AVISA e nao mostra nenhum (nunca escolhe
#         um sozinha). Decisao de Benedito: nao criar trava no banco
#         agora - esperar acontecer.
#
#     SEGURANCA: a Propriedade da URL e conferida contra os pares do
#     usuario logado E o Produtor da sessao, em toda rota.
#     Tela SOMENTE LEITURA - nada e gravado nem commitado.
#
#     v1.0.0: Criacao do modulo (Sessao 085, 04/10/2026, 14:10 -03).
#     v1.1.0: Sessao 090 (08/10/2026, 08:35 -03) - FAZENDA EM USO (Lote 4):
#             FAZENDA EM USO (Regra de Ouro #13): a tela "Selecionar Propriedade" deixa
#             de aparecer quando ha fazenda em uso (auth.resolver_fazenda_em_uso).
#               - iniciar(): com fazenda em uso, abre a Consulta direto nela.
#               - VOLTAR (Regra #9): vai para os Hubs NOVOS (entrada ou
#                 brincagem, conforme a origem); so volta para a selecao quem
#                 tem 2+ pares e nenhuma fazenda em uso.
#               - TRAVA em _propriedade_do_usuario(): Propriedade diferente da
#                 fazenda em uso (outra aba) = negado; consultar() ja manda
#                 para o iniciar(), que abre a fazenda em uso.
#             Nenhuma outra mudanca. Template inalterado.
#     v1.2.0: Sessao 105 (23/10/2026, 18:20 -03) - Manejo fora do estoque diz ONDE o animal esta: 'Animal ja saiu da Propriedade: ABATE em dd/mm/aaaa.'
#             (utils\animal_saiu.py). REVERSAO: devolver .bak_antes_s105d.
# =========================================================

from datetime import date

from flask import Blueprint, redirect, render_template, request, session

from backend.models import Produtor, Propriedade
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_4001_gta import Gta
from backend.models.tb_4002_especie import Especie
from backend.models.tb_4003_pesos import Peso
from backend.models.tb_4005_racas import Raca
from backend.models.tb_4006_idade_meses import IdadeMeses
from backend.routers.auth import buscar_pares_propriedade_produtor, redirecionar_home, resolver_fazenda_em_uso
from backend.utils.multitenant import get_db_produtor
from backend.utils.animal_saiu import mensagem_animal_saiu   # v1.2.0 - onde o animal esta


# -------------------------------------------------------
# Blueprint
# -------------------------------------------------------
consulta_manejo = Blueprint('consulta_manejo', __name__)


# -------------------------------------------------------
# Constantes do modulo
# -------------------------------------------------------
URL_INICIAR  = '/produtor/consulta-manejo/iniciar'
URL_CONSULTA = '/produtor/consulta-manejo'
SESSAO_ORIGEM = 'consulta_manejo_origem'     # 'entrada' ou 'brincagem'
TAMANHO_MANEJO = 6                           # tamanho da coluna tb_2001.manejo
TITULO = 'Consulta por Manejo'

MENSAGEM_NAO_ENCONTRADO = 'Animal não encontrado em estoque nesta Propriedade.'
MENSAGEM_MANEJO_INCORRETO = f'Digite os {TAMANHO_MANEJO} números do Manejo.'
MENSAGEM_DUPLICADO = (
    'Este Manejo foi encontrado em mais de um animal desta Propriedade. '
    'Nenhum foi exibido. Avise a Consiste.'
)


# -------------------------------------------------------
# Sem cache: a ficha do animal precisa ser sempre a mais nova
# (mesmo padrao de notificacao_nascimento.py).
# -------------------------------------------------------
@consulta_manejo.after_request
def _sem_cache(resposta):
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta


# -------------------------------------------------------
# Auxiliares de navegacao
# -------------------------------------------------------
def _ler_origem():
    origem = session.get(SESSAO_ORIGEM, 'brincagem')
    return origem if origem in ('entrada', 'brincagem') else 'brincagem'


def _voltar_por_origem(origem):
    # v1.1.0 - Hubs novos (agrupados).
    return '/produtor/hub-novo/entrada' if origem == 'entrada' else '/produtor/hub-novo/brincagem'


def _menu_por_origem(origem):
    return 'entrada' if origem == 'entrada' else 'brincagem'


# Destino REAL do Voltar da tela de consulta (Regra de Ouro #4): com
# 2+ pares passou pela selecao -> volta para ela; com 1 par a selecao
# foi pulada -> volta para o Hub.
def _calcular_url_voltar(origem):
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    # v1.1.0 - com fazenda em uso a selecao e pulada: volta direto ao Hub.
    if len(pares) > 1 and resolver_fazenda_em_uso(pares) is None:
        return f'{URL_INICIAR}?origem={origem}'
    return _voltar_por_origem(origem)


# A Propriedade pertence a um par do usuario logado E ao Produtor que
# esta na sessao? Qualquer coisa estranha (vazio, nao numero) = False.
def _propriedade_do_usuario(id_propriedade):
    try:
        id_int = int(id_propriedade)
    except (TypeError, ValueError):
        return False
    pares = buscar_pares_propriedade_produtor(session['usuario_id'])
    # v1.1.0 - TRAVA DA FAZENDA EM USO: Propriedade diferente da fazenda em
    # uso (trocada em outra aba) = negado (consultar() manda para o iniciar(),
    # que abre a fazenda em uso).
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None and par_em_uso.id_propriedade != id_int:
        return False
    return any(
        par.id_propriedade == id_int and par.id_produtor == session.get('id_produtor')
        for par in pares
    )


def _data_br(data):
    return data.strftime('%d/%m/%Y') if data else ''


# -------------------------------------------------------
# Idade em Meses: a faixa da tb_4006 que contem os Dias do animal.
# As faixas vem do banco (nunca fixas no codigo). Sem Dias ou fora de
# qualquer faixa (ex.: Nascimento no futuro) -> vazio.
# -------------------------------------------------------
def _faixa_idade_meses(db, dias):
    if dias is None:
        return ''
    faixas = db.query(IdadeMeses).order_by(IdadeMeses.codigo_geras.asc()).all()
    for faixa in faixas:
        if faixa.dias_min <= dias <= faixa.dias_max:
            return faixa.descricao
    return ''


# -------------------------------------------------------
# Selo da Liberacao para Abate. Devolve (texto, classe) ou
# ('', '') se a data nao existir.
# -------------------------------------------------------
def _selo_liberacao(liberacao_abate, hoje):
    if liberacao_abate is None:
        return '', ''
    if liberacao_abate <= hoje:
        return 'Animal Liberado', 'liberado'
    faltam = (liberacao_abate - hoje).days
    return (
        f'Aguardando — liberado em {_data_br(liberacao_abate)} (faltam {faltam} dia(s))',
        'aguardando',
    )


# -------------------------------------------------------
# Monta o dict de TEXTO da ficha do animal (nada de objeto do banco
# sai daqui - o template so recebe texto e numeros).
# -------------------------------------------------------
ROTULO_ORIGEM = {'COMPRA': 'Compra', 'NASCIMENTO': 'Nascimento / Desmame', 'NASCTO-DESMAME': 'Nascimento / Desmame', 'CARGA': 'Carga'}   # v1.3.1


def _montar_ficha(db, animal, hoje):
    especie = db.get(Especie, animal.id_especie) if animal.id_especie else None
    raca = db.get(Raca, animal.id_raca) if animal.id_raca else None
    gta = db.get(Gta, animal.id_gta_entrada) if animal.id_gta_entrada else None

    dias_nascimento = (hoje - animal.nascimento).days if animal.nascimento else None
    confinamento = (hoje - animal.data_inclusao).days if animal.data_inclusao else None

    # Ultima pesagem = maior sequencia do SISBOV (pesagem.py numera 1, 2, 3...).
    ultimo_peso = (
        db.query(Peso)
        .filter(Peso.sisbov == animal.sisbov)
        .order_by(Peso.sequencia.desc())
        .first()
    )

    selo_texto, selo_classe = _selo_liberacao(animal.liberacao_abate, hoje)

    return {
        'sisbov': animal.sisbov or '',
        'rfid': animal.rfid or '',
        'origem': ROTULO_ORIGEM.get(animal.tipo_entrada, animal.tipo_entrada or ''),   # v1.3.1
        'especie': especie.codigo if especie else '',
        'sexo': animal.sexo or '',
        'raca': raca.codigo if raca else '',
        'nascimento': _data_br(animal.nascimento),
        'dias_nascimento': '' if dias_nascimento is None else dias_nascimento,
        'idade_meses': _faixa_idade_meses(db, dias_nascimento),
        'lote': animal.lote or '',
        'gta': gta.numero_gta_completo if gta else '',
        'data_entrada': _data_br(animal.data_brincagem),
        'inclusao_bnd': _data_br(animal.data_inclusao),
        'comunicado': '' if animal.numero_comunicado is None else animal.numero_comunicado,
        'liberacao_abate': _data_br(animal.liberacao_abate),
        'selo_texto': selo_texto,
        'selo_classe': selo_classe,
        'confinamento': '' if confinamento is None else confinamento,
        'peso': f'{ultimo_peso.peso:.2f}' if ultimo_peso is not None else '',
    }


# -------------------------------------------------------
# Rota: GET /produtor/consulta-manejo/iniciar?origem=entrada|brincagem
# Padrao Reutilizavel Nº1 - Selecionar Propriedade/Produtor.
# Guarda 'origem' na sessao. Com 1 unico par, pula direto para a
# consulta (len(pares), nunca produtores distintos - bug P-036).
# -------------------------------------------------------
@consulta_manejo.route('/produtor/consulta-manejo/iniciar')
def iniciar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    origem = request.args.get('origem', 'brincagem')
    if origem not in ('entrada', 'brincagem'):
        origem = 'brincagem'
    session[SESSAO_ORIGEM] = origem
    voltar = _voltar_por_origem(origem)

    pares = buscar_pares_propriedade_produtor(session['usuario_id'])

    if len(pares) == 0:
        return render_template(
            'produtor/selecionar_propriedade_produtor.html',
            pares=[],
            erro='Nenhuma Propriedade ativa vinculada ao seu cadastro. Contate a Consiste.',
            titulo=f'{TITULO} — Selecionar Propriedade',
            proximo=URL_CONSULTA,
            campo_propriedade='id_propriedade',
            voltar=voltar,
            usuario_nome=session.get('usuario_nome'),
            usuario_perfil=session.get('usuario_perfil'),
            cor_primaria=session.get('cor_primaria', '#D4370A'),
            nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
            menu_ativo=_menu_por_origem(origem),
        )

    # v1.1.0 - FAZENDA EM USO: pula a tela "Selecionar Propriedade".
    par_em_uso = resolver_fazenda_em_uso(pares)
    if par_em_uso is not None:
        session['id_produtor']   = par_em_uso.id_produtor
        session['usuario_cargo'] = par_em_uso.cargo
        return redirect(f'{URL_CONSULTA}?id_propriedade={par_em_uso.id_propriedade}')

    if len(pares) == 1:
        par = pares[0]
        session['id_produtor']   = par.id_produtor
        session['usuario_cargo'] = par.cargo
        return redirect(f'{URL_CONSULTA}?id_propriedade={par.id_propriedade}')

    return render_template(
        'produtor/selecionar_propriedade_produtor.html',
        pares=pares,
        erro=None,
        titulo=f'{TITULO} — Selecionar Propriedade',
        proximo=URL_CONSULTA,
        campo_propriedade='id_propriedade',
        voltar=voltar,
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo=_menu_por_origem(origem),
    )


# -------------------------------------------------------
# Rota: GET /produtor/consulta-manejo?id_propriedade=X[&manejo=NNNNNN]
# Sem 'manejo' mostra so o campo para digitar. Com 'manejo' valida,
# busca o animal em estoque da Propriedade e mostra a ficha.
# -------------------------------------------------------
@consulta_manejo.route('/produtor/consulta-manejo')
def consultar():
    if 'id_produtor' not in session:
        return redirecionar_home(session.get('usuario_perfil'))

    origem = _ler_origem()

    id_propriedade = request.args.get('id_propriedade', '')
    if not _propriedade_do_usuario(id_propriedade):
        return redirect(f'{URL_INICIAR}?origem={origem}')
    id_propriedade = int(id_propriedade)

    manejo = request.args.get('manejo', '').strip()
    hoje = date.today()

    erro = None
    aviso = None
    ficha = None

    with get_db_produtor(session['id_produtor']) as db:
        propriedade = db.get(Propriedade, id_propriedade)
        if not propriedade:
            return redirect(f'{URL_INICIAR}?origem={origem}')
        produtor = db.get(Produtor, session['id_produtor'])

        propriedade_nome = propriedade.nome or ''
        produtor_nome = produtor.nome if produtor else ''

        if manejo:
            if len(manejo) != TAMANHO_MANEJO or not (manejo.isascii() and manejo.isdecimal()):
                erro = MENSAGEM_MANEJO_INCORRETO
            else:
                animais = (
                    db.query(Entrada)
                    .filter(Entrada.id_propriedade == id_propriedade, Entrada.manejo == manejo)
                    .all()
                )
                if len(animais) == 0:
                    aviso = mensagem_animal_saiu(db, id_propriedade, manejo=manejo) or MENSAGEM_NAO_ENCONTRADO   # v1.2.0
                elif len(animais) > 1:
                    erro = MENSAGEM_DUPLICADO
                else:
                    ficha = _montar_ficha(db, animais[0], hoje)

    return render_template(
        'produtor/consulta_manejo.html',
        id_propriedade=id_propriedade,
        propriedade_nome=propriedade_nome,
        produtor_nome=produtor_nome,
        manejo=manejo,
        erro=erro,
        aviso=aviso,
        ficha=ficha,
        url_voltar=_calcular_url_voltar(origem),
        usuario_nome=session.get('usuario_nome'),
        usuario_perfil=session.get('usuario_perfil'),
        cor_primaria=session.get('cor_primaria', '#D4370A'),
        nome_sistema=session.get('nome_sistema', 'Orion SISBOV'),
        menu_ativo=_menu_por_origem(origem),
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\consulta_manejo.py
# =========================================================
