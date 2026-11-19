# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\validador_blockchain.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-09 18:57 -03
# ATUALIZADO EM: 2026-10-10 18:00 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     "Receita" UNICA das conferencias do blockchain (Sessao 092). Quem usa:
#       - validar_blockchain.py (terminal, na pasta C:\orion);
#       - tela Consiste > Blockchain (backend\routers\consiste_blockchain.py).
#     Assim as conferencias moram num lugar so: uma conferencia nova entra
#     aqui e aparece nos dois.
#
#     Nao envia, nao cancela e nao interfere no carteiro (que continua
#     enviando sozinho em segundo plano). A UNICA coisa que grava, desde a
#     v1.1.0, e a marca tb_blk_8002_eventos.conferido_em (ver abaixo).
#
#     SO CONFERE O QUE FALTA (v1.1.0)
#       Evento com conferido_em preenchido e PULADO (ja conferido antes).
#       Um evento so recebe a marca quando esta TOTALMENTE OK: nenhum
#       ATENCAO/FALHA, pelo menos um envio e todos os envios em estado final
#       (CONFIRMADO ou CANCELADO). Evento pendente, enviando, com erro ou com
#       ATENCAO continua sendo conferido em toda rodada.
#       tudo=True reconfere tudo (inclusive os ja marcados): quem passar
#       continua marcado (data nova); quem FALHAR perde a marca.
#       marcar=False confere sem gravar nada (usado no relatorio .txt).
#       A conferencia de troca de RFID roda sempre (depende do animal hoje).
#
#     FUNCOES PRINCIPAIS
#       validar(id_produtor=None, tipo=None, tudo=False, marcar=True)
#                                            -> lista de ResultadoProdutor
#       resumo(id_produtor=None)             -> lista de ResumoProdutor (leve:
#                                               so contagens, sem conferir hash)
#       formatar_texto(resultados, ...)      -> relatorio em texto (terminal e
#                                               download .txt)
#       somar(resultados)                    -> totais OK / ATENCAO / FALHA
#       somar_conferencia(resultados)        -> conferidos agora / pulados /
#                                               marcados
#
#     O QUE E CONFERIDO
#       Chave:    BLK_CHAVE_<versao> existe no .env (a atual e as usadas).
#       Ligacao:  Produtor com provedor ligado (info).
#       Evento:   tipo valido; hashes da ficha e do evento recalculados e
#                 iguais aos gravados (nada foi alterado); hash do SISBOV
#                 confere com o SISBOV da ficha; codigo_fazenda confere;
#                 tem pelo menos um envio; sem envio duplicado para o mesmo
#                 provedor.
#       Estorno:  aponta para um evento que existe, com o mesmo SISBOV
#                 (hash), e so vai para provedor que ja recebeu o original.
#       Envio:    status valido; CONFIRMADO tem codigo e data; ERRO tem a
#                 mensagem; ENVIANDO preso ha mais de 10 min; PENDENTE
#                 parado ha mais de 30 min (carteiro desligado?); ERRO que
#                 estourou as 10 tentativas; CANCELADO sem motivo.
#       Troca de RFID: o RFID do ultimo evento (nao estornado, nao
#                 cancelado) de cada animal e o que esta hoje no animal.
#
#     v1.0.0: Criacao (Sessao 092, 09/10/2026, 18:57 -03). Logica trazida do
#         validar_blockchain.py v1.0.0 (terminal), agora devolvendo dados
#         estruturados para o terminal e a tela usarem a mesma receita.
#     v1.1.0: Sessao 093 (10/10/2026, 18:00 -03) - ENTREGA 2: so confere o que
#         ainda nao foi conferido (usa conferido_em, criada pelo script
#         Tabelas\14_alter_blk_conferido_versao2.sql). Novos parametros
#         tudo e marcar em validar(); novos campos conferidos_agora, pulados
#         e marcados em ResultadoProdutor; ResumoProdutor ganhou a_conferir
#         (eventos ainda nao conferidos); novo somar_conferencia(); relatorio
#         em texto mostra o modo e as contagens. A gravacao da marca e feita
#         DEPOIS de ler tudo, num unico UPDATE por Produtor (a leitura nao
#         usa objetos depois do commit). Falta da coluna conferido_em vira
#         FALHA com a instrucao do script, nao erro generico.
# =========================================================

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import bindparam, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Produtor
from backend.models.tb_2001_entradas import Entrada
from backend.models.tb_blk_8000_provedores import ProvedorBlk
from backend.models.tb_blk_8001_produtor_provedores import ProdutorProvedorBlk
from backend.models.tb_blk_8002_eventos import EventoBlk
from backend.models.tb_blk_8003_envios import EnvioBlk, STATUS_ENVIO
from backend.utils.multitenant import get_db_produtor
from backend.utils import blockchain as B

MINUTOS_PRESO = 10
MINUTOS_PENDENTE_PARADO = 30
MAX_TENTATIVAS = 10          # igual ao carteiro_blockchain.py

NIVEIS = ('OK', 'ATENCAO', 'FALHA')


# -------------------------------------------------------
# Estruturas de resultado
# -------------------------------------------------------
@dataclass
class Achado:
    nivel: str          # OK / ATENCAO / FALHA
    texto: str


class Achados:
    """Junta os achados de UM Produtor e conta OK / ATENCAO / FALHA."""

    def __init__(self):
        self.itens: List[Achado] = []
        self.total = {'OK': 0, 'ATENCAO': 0, 'FALHA': 0}

    def _add(self, nivel, texto):
        self.total[nivel] += 1
        self.itens.append(Achado(nivel, texto))

    def ok(self, texto):
        self._add('OK', texto)

    def atencao(self, texto):
        self._add('ATENCAO', texto)

    def falha(self, texto):
        self._add('FALHA', texto)

    def conferir(self, condicao, texto_ok, texto_falha, nivel_falha='FALHA'):
        if condicao:
            self.ok(texto_ok)
        else:
            self._add(nivel_falha, texto_falha)
        return condicao


@dataclass
class ResultadoProdutor:
    id_produtor: int
    nome: str = ''
    achados: List[Achado] = field(default_factory=list)
    total: dict = field(default_factory=lambda: {'OK': 0, 'ATENCAO': 0, 'FALHA': 0})
    eventos: int = 0
    envios: dict = field(default_factory=dict)     # status -> quantidade
    conferidos_agora: int = 0      # eventos conferidos nesta rodada
    pulados: int = 0               # eventos que ja tinham sido conferidos antes
    marcados: int = 0              # eventos que receberam/renovaram a marca agora

    @property
    def rotulo(self):
        return f'produtor_{self.id_produtor:05d}'

    @property
    def tem_falha(self):
        return self.total['FALHA'] > 0

    @property
    def resumo_envios(self):
        return ', '.join(f'{k}={v}' for k, v in sorted(self.envios.items())) or 'nenhum'


@dataclass
class ResumoProdutor:
    id_produtor: int
    nome: str = ''
    provedores: List[str] = field(default_factory=list)
    eventos: int = 0
    a_conferir: int = 0            # eventos ainda sem conferido_em
    envios: dict = field(default_factory=dict)
    sem_tabelas: bool = False
    erro: Optional[str] = None

    @property
    def rotulo(self):
        return f'produtor_{self.id_produtor:05d}'


# -------------------------------------------------------
# Lista de Produtores
# -------------------------------------------------------
def listar_produtores(id_produtor=None):
    """[(id, nome)] dos Produtores a conferir. Com id_produtor: so aquele
    (mesmo inativo); sem: todos os ativos."""
    with Session(engine) as sessao:
        consulta = sessao.query(Produtor.id, Produtor.nome).filter(Produtor.schema_nome.isnot(None))
        if id_produtor:
            consulta = consulta.filter(Produtor.id == id_produtor)
        else:
            consulta = consulta.filter(Produtor.ativo.is_(True))
        return [(linha[0], linha[1] or '') for linha in consulta.order_by(Produtor.id).all()]


# -------------------------------------------------------
# Conferencias
# -------------------------------------------------------
def _rotulo(evento):
    return f'evento {evento.id} ({evento.tipo_evento})'


def _validar_chaves(ach, versoes):
    """Confere se a chave de cada versao usada esta no .env."""
    for versao in sorted(versoes):
        try:
            B._chave(versao)
            ach.ok(f'Chave BLK_CHAVE_{versao} encontrada no .env.')
        except B.ChaveAusente:
            ach.falha(f'Chave BLK_CHAVE_{versao} NAO esta no .env - nao da para conferir os hashes dessa versao.')


def _validar_evento(ach, db, evento, envios, por_id, envios_por_evento):
    nome = _rotulo(evento)
    ficha = evento.ficha_animal or {}

    ach.conferir(evento.tipo_evento in B.TIPOS_EVENTO,
                 f'{nome}: tipo de evento valido.',
                 f'{nome}: tipo de evento "{evento.tipo_evento}" nao existe na lista do Orion.')

    # Hashes recalculados (so da para conferir se a chave dessa versao existe)
    try:
        B._chave(evento.versao_chave)
        tem_chave = True
    except B.ChaveAusente:
        tem_chave = False

    if tem_chave:
        ach.conferir(B.verificar_evento(db, evento.id),
                     f'{nome}: hashes da ficha e do evento conferem (nada foi alterado).',
                     f'{nome}: HASH NAO CONFERE - a ficha ou o evento foi alterado depois de gravado.')
        if evento.tipo_evento != B.TIPO_ESTORNO:
            sisbov = ficha.get('sisbov')
            if sisbov:
                ach.conferir(B.hash_sisbov(sisbov, evento.versao_chave) == evento.sisbov_hash,
                             f'{nome}: hash do SISBOV confere com o SISBOV da ficha.',
                             f'{nome}: hash do SISBOV diferente do SISBOV que esta na ficha.')
            else:
                ach.falha(f'{nome}: a ficha nao tem o SISBOV.')
            ach.conferir(B.codigo_fazenda(evento.id_propriedade, evento.versao_chave) == ficha.get('codigo_fazenda'),
                         f'{nome}: codigo anonimo da fazenda confere.',
                         f'{nome}: codigo_fazenda da ficha nao bate com a propriedade {evento.id_propriedade}.')
            ach.conferir('manejo' in ficha and 'rfid' in ficha,
                         f'{nome}: ficha do animal completa (manejo e RFID presentes).',
                         f'{nome}: ficha do animal sem manejo/RFID.', 'ATENCAO')
    else:
        ach.atencao(f'{nome}: hashes nao conferidos (falta a chave da versao {evento.versao_chave}).')

    # Envios do evento
    ach.conferir(len(envios) >= 1,
                 f'{nome}: tem envio na fila.',
                 f'{nome}: NAO tem nenhum envio - ficou fora da fila.')
    vistos = set()
    for envio in envios:
        if envio.id_provedor in vistos:
            ach.falha(f'{nome}: envio duplicado para o provedor {envio.id_provedor}.')
        vistos.add(envio.id_provedor)

    # Estorno
    if evento.tipo_evento == B.TIPO_ESTORNO:
        original = por_id.get(evento.id_evento_anterior)
        if original is None:
            ach.falha(f'{nome}: estorno aponta para um evento que nao existe ({evento.id_evento_anterior}).')
        else:
            ach.conferir(original.sisbov_hash == evento.sisbov_hash,
                         f'{nome}: estorno do evento {original.id} - mesmo animal.',
                         f'{nome}: estorno aponta para o evento {original.id}, mas e de OUTRO animal.')
            ach.conferir(original.tipo_evento != B.TIPO_ESTORNO,
                         f'{nome}: estorno de um evento normal.',
                         f'{nome}: estorno de outro estorno.', 'ATENCAO')
            provedores_originais = {e.id_provedor for e in envios_por_evento.get(original.id, [])
                                    if e.status in ('ENVIANDO', 'CONFIRMADO')}
            extras = [e.id_provedor for e in envios if e.id_provedor not in provedores_originais]
            ach.conferir(not extras,
                         f'{nome}: estorno so para provedor que ja tinha recebido o original.',
                         f'{nome}: estorno vai para provedor que nunca recebeu o evento {original.id}.', 'ATENCAO')


def _validar_envio(ach, envio, evento, agora):
    nome = f'{_rotulo(evento)} / envio {envio.id}'
    if envio.status not in STATUS_ENVIO:
        ach.falha(f'{nome}: status "{envio.status}" invalido.')
        return

    if envio.status == 'CONFIRMADO':
        ach.conferir(bool(envio.codigo_retorno) and envio.confirmado_em is not None,
                     f'{nome}: CONFIRMADO com codigo de retorno e data.',
                     f'{nome}: CONFIRMADO sem codigo de retorno ou sem data.')
    elif envio.status == 'ERRO':
        if envio.tentativas >= MAX_TENTATIVAS:
            ach.falha(f'{nome}: ERRO definitivo ({envio.tentativas} tentativas): {(envio.erro or "")[:120]}')
        else:
            ach.atencao(f'{nome}: ERRO ({envio.tentativas} tentativa(s)), proxima em {envio.proximo_envio:%d/%m %H:%M}: '
                        f'{(envio.erro or "sem mensagem")[:120]}')
            ach.conferir(bool(envio.erro), f'{nome}: erro com mensagem.', f'{nome}: ERRO sem mensagem gravada.')
    elif envio.status == 'ENVIANDO':
        parado = agora - (envio.atualizado_em or agora)
        if parado > timedelta(minutes=MINUTOS_PRESO):
            ach.atencao(f'{nome}: ENVIANDO ha {int(parado.total_seconds() // 60)} min (o carteiro volta para PENDENTE sozinho).')
        else:
            ach.ok(f'{nome}: ENVIANDO agora (em andamento).')
    elif envio.status == 'PENDENTE':
        espera = agora - (envio.criado_em or agora)
        if espera > timedelta(minutes=MINUTOS_PENDENTE_PARADO):
            ach.atencao(f'{nome}: PENDENTE ha {int(espera.total_seconds() // 60)} min - carteiro desligado '
                        f'ou provedor sem conector?')
        else:
            ach.ok(f'{nome}: PENDENTE (aguardando o carteiro).')
    elif envio.status == 'CANCELADO':
        ach.conferir(bool(envio.erro),
                     f'{nome}: CANCELADO com motivo (Desfazer antes do envio).',
                     f'{nome}: CANCELADO sem motivo gravado.', 'ATENCAO')
        ach.conferir(envio.codigo_retorno is None,
                     f'{nome}: CANCELADO nunca saiu (sem codigo de retorno).',
                     f'{nome}: CANCELADO mas tem codigo de retorno - chegou a sair?')


def _validar_troca_rfid(ach, db, eventos, estornados, envios_por_evento):
    """O RFID do ultimo evento TROCA_RFID (nao estornado e nao cancelado) de
    cada animal tem que ser o RFID que o animal tem hoje."""
    ultimo = {}
    for ev in eventos:                      # ja vem em ordem de id
        if ev.tipo_evento != B.TIPO_TROCA_RFID or ev.id in estornados:
            continue
        envios_ev = envios_por_evento.get(ev.id, [])
        if envios_ev and all(e.status == 'CANCELADO' for e in envios_ev):
            continue                        # Desfazer antes de sair: nunca valeu
        ultimo[ev.sisbov_hash] = ev
    for ev in ultimo.values():
        ficha = ev.ficha_animal or {}
        sisbov = ficha.get('sisbov')
        if not sisbov:
            continue
        animal = db.query(Entrada).filter_by(id_propriedade=ev.id_propriedade, sisbov=sisbov).first()
        nome = _rotulo(ev)
        if animal is None:
            ach.atencao(f'{nome}: animal da ficha nao esta mais na tb_2001 (saiu do rebanho?).')
            continue
        esperado = ficha.get('rfid_novo')
        ach.conferir((animal.rfid or None) == (esperado or None),
                     f'{nome}: RFID da ficha bate com o RFID atual do animal.',
                     f'{nome}: ficha diz RFID {esperado}, mas o animal tem {animal.rfid} hoje '
                     f'(mudou depois, sem novo evento?).', 'ATENCAO')


# -------------------------------------------------------
# validar() - confere os Produtores
# -------------------------------------------------------
ESTADOS_FINAIS = ('CONFIRMADO', 'CANCELADO')


def _validar_um(id_produtor, nome, tipo_filtro, tudo=False, marcar=True):
    res = ResultadoProdutor(id_produtor=id_produtor, nome=nome)
    ach = Achados()
    try:
        with get_db_produtor(id_produtor) as db:
            ligados = (
                db.query(ProdutorProvedorBlk, ProvedorBlk)
                .join(ProvedorBlk, ProvedorBlk.id == ProdutorProvedorBlk.id_provedor)
                .filter(ProdutorProvedorBlk.ativo.is_(True))
                .all()
            )
            if ligados:
                ach.ok('Provedores ligados: ' + ', '.join(f'{p.codigo} ({l.ambiente})' for l, p in ligados))
            else:
                ach.atencao('Nenhum provedor ligado - este Produtor nao gera eventos de blockchain.')

            eventos = db.query(EventoBlk).order_by(EventoBlk.id).all()
            envios = db.query(EnvioBlk).order_by(EnvioBlk.id).all()
            res.eventos = len(eventos)
            ids_marcar = []      # passaram em tudo, em estado final -> recebem a marca
            ids_limpar = []      # ja tinham a marca e agora NAO passaram -> perdem a marca
            if not eventos:
                ach.ok('Sem eventos ainda.')
            else:
                envios_por_evento = defaultdict(list)
                for e in envios:
                    envios_por_evento[e.id_evento].append(e)
                por_id = {ev.id: ev for ev in eventos}
                estornados = {ev.id_evento_anterior for ev in eventos
                              if ev.tipo_evento == B.TIPO_ESTORNO and ev.id_evento_anterior}

                _validar_chaves(ach, {B.versao_chave_atual()} | {ev.versao_chave for ev in eventos})

                orfaos = [e for e in envios if e.id_evento not in por_id]
                ach.conferir(not orfaos, 'Nenhum envio solto (sem evento).', f'{len(orfaos)} envio(s) sem evento.')

                # Quais eventos conferir nesta rodada
                no_filtro = [ev for ev in eventos if not tipo_filtro or ev.tipo_evento == tipo_filtro]
                if tudo:
                    a_conferir = no_filtro
                else:
                    a_conferir = [ev for ev in no_filtro if ev.conferido_em is None]
                res.pulados = len(no_filtro) - len(a_conferir)
                res.conferidos_agora = len(a_conferir)
                if not a_conferir and no_filtro:
                    ach.ok(f'Nada novo a conferir: {len(no_filtro)} evento(s) ja conferido(s) antes.')

                agora = datetime.now()
                for ev in a_conferir:
                    antes = ach.total['ATENCAO'] + ach.total['FALHA']
                    envios_ev = envios_por_evento.get(ev.id, [])
                    _validar_evento(ach, db, ev, envios_ev, por_id, envios_por_evento)
                    for envio in envios_ev:
                        _validar_envio(ach, envio, ev, agora)
                    tudo_ok = (ach.total['ATENCAO'] + ach.total['FALHA'] == antes
                               and len(envios_ev) >= 1
                               and all(e.status in ESTADOS_FINAIS for e in envios_ev))
                    if tudo_ok:
                        ids_marcar.append(ev.id)
                    elif ev.conferido_em is not None:
                        ids_limpar.append(ev.id)

                if not tipo_filtro or tipo_filtro == B.TIPO_TROCA_RFID:
                    _validar_troca_rfid(ach, db, eventos, estornados, envios_por_evento)

                contagem = defaultdict(int)
                for e in envios:
                    contagem[e.status] += 1
                res.envios = dict(contagem)

            # Grava a marca por ultimo, depois de ler tudo (um UPDATE por
            # Produtor). Nada do banco e lido depois do commit.
            if marcar and (ids_marcar or ids_limpar):
                if ids_marcar:
                    db.execute(
                        text('UPDATE tb_blk_8002_eventos SET conferido_em = :agora WHERE id IN :ids')
                        .bindparams(bindparam('ids', expanding=True)),
                        {'agora': datetime.now(), 'ids': ids_marcar})
                if ids_limpar:
                    db.execute(
                        text('UPDATE tb_blk_8002_eventos SET conferido_em = NULL WHERE id IN :ids')
                        .bindparams(bindparam('ids', expanding=True)),
                        {'ids': ids_limpar})
                db.commit()
                res.marcados = len(ids_marcar)
    except ProgrammingError as erro:
        # So a 1a linha do erro: o texto completo traz o SQL inteiro (que
        # sempre cita conferido_em e tb_blk_800x) e confundiria o teste.
        texto = str(getattr(erro, 'orig', erro))
        primeira = texto.splitlines()[0] if texto else ''
        if 'conferido_em' in primeira:
            ach.falha('falta a coluna conferido_em em tb_blk_8002_eventos. '
                      'Rode o script Tabelas\\14_alter_blk_conferido_versao2.sql.')
        elif 'tb_blk_800' in primeira and 'does not exist' in primeira:
            ach.falha('faltam as tabelas do blockchain (tb_blk_8001/8002/8003). '
                      'Rode o script Tabelas\\12_create_tb_blk_8001_8003_produtor.sql.')
        else:
            ach.falha(f'erro no banco: {primeira[:200]}')
    except Exception as erro:
        ach.falha(f'nao foi possivel validar ({type(erro).__name__}: {str(erro)[:200]}).')

    res.achados = ach.itens
    res.total = ach.total
    return res


def validar(id_produtor=None, tipo=None, tudo=False, marcar=True):
    """Confere os Produtores (todos os ativos, ou so id_produtor) e devolve
    uma lista de ResultadoProdutor.
      tipo   = so um tipo de evento (opcional);
      tudo   = True reconfere tambem os eventos ja conferidos antes;
      marcar = False confere sem gravar a marca conferido_em."""
    return [_validar_um(pid, nome, tipo, tudo, marcar) for pid, nome in listar_produtores(id_produtor)]


def somar(resultados):
    total = {'OK': 0, 'ATENCAO': 0, 'FALHA': 0}
    for r in resultados:
        for k in total:
            total[k] += r.total[k]
    return total


def somar_conferencia(resultados):
    """Totais da conferencia: eventos conferidos agora, pulados (ja
    conferidos antes) e marcados como conferidos nesta rodada."""
    total = {'conferidos_agora': 0, 'pulados': 0, 'marcados': 0}
    for r in resultados:
        total['conferidos_agora'] += r.conferidos_agora
        total['pulados'] += r.pulados
        total['marcados'] += r.marcados
    return total


# -------------------------------------------------------
# resumo() - contagens leves (sem conferir hash) para a tabela da tela
# -------------------------------------------------------
def resumo(id_produtor=None):
    saida = []
    for pid, nome in listar_produtores(id_produtor):
        item = ResumoProdutor(id_produtor=pid, nome=nome)
        try:
            with get_db_produtor(pid) as db:
                ligados = (
                    db.query(ProdutorProvedorBlk, ProvedorBlk)
                    .join(ProvedorBlk, ProvedorBlk.id == ProdutorProvedorBlk.id_provedor)
                    .filter(ProdutorProvedorBlk.ativo.is_(True))
                    .all()
                )
                item.provedores = [f'{p.codigo} ({l.ambiente})' for l, p in ligados]
                item.eventos = db.execute(text('SELECT count(*) FROM tb_blk_8002_eventos')).scalar() or 0
                item.a_conferir = db.execute(
                    text('SELECT count(*) FROM tb_blk_8002_eventos WHERE conferido_em IS NULL')).scalar() or 0
                linhas = db.execute(text('SELECT status, count(*) FROM tb_blk_8003_envios GROUP BY status')).all()
                item.envios = {linha[0]: linha[1] for linha in linhas}
        except ProgrammingError as erro:
            primeira = (str(getattr(erro, 'orig', erro)).splitlines() or [''])[0]
            if 'conferido_em' in primeira:
                item.erro = 'falta a coluna conferido_em - rode Tabelas\\14_alter_blk_conferido_versao2.sql'
            elif 'tb_blk_800' in primeira:
                item.sem_tabelas = True
            else:
                item.erro = str(erro).splitlines()[0][:200]
        except Exception as erro:
            item.erro = f'{type(erro).__name__}: {str(erro)[:200]}'
        saida.append(item)
    return saida


# -------------------------------------------------------
# formatar_texto() - relatorio em texto (terminal e download)
# -------------------------------------------------------
_ETIQUETA = {'OK': '[OK]     ', 'ATENCAO': '[ATENCAO]', 'FALHA': '[FALHA]  '}


def formatar_texto(resultados, tipo=None, so_problemas=False, quando=None, tudo=False, marcar=True):
    quando = quando or datetime.now()
    linhas = [f'VALIDACAO DO BLOCKCHAIN - Orion - {quando:%d/%m/%Y %H:%M:%S}']
    if tipo:
        linhas.append(f'Filtro: tipo {tipo}')
    modo = 'confere TUDO (reconferencia)' if tudo else 'confere so o que ainda nao foi conferido'
    linhas.append(f'Modo: {modo}; ' + ('marca os eventos OK como conferidos' if marcar else 'NAO marca nada'))

    for r in resultados:
        linhas.append('')
        linhas.append(f'=== {r.rotulo} ===')
        for a in r.achados:
            if a.nivel == 'OK' and so_problemas:
                continue
            linhas.append(f'  {_ETIQUETA[a.nivel]} {a.texto}')
        if r.eventos > 0:
            linhas.append('')
            linhas.append(f'  Resumo: {r.eventos} evento(s); conferidos agora: {r.conferidos_agora}; '
                          f'ja conferidos antes (pulados): {r.pulados}; marcados: {r.marcados}; '
                          f'envios: {r.resumo_envios}')

    t = somar(resultados)
    linhas.append('')
    linhas.append('-' * 60)
    linhas.append(f'RESULTADO: {t["OK"]} OK | {t["ATENCAO"]} ATENCAO | {t["FALHA"]} FALHA')
    if t['FALHA'] == 0 and t['ATENCAO'] == 0:
        linhas.append('TUDO CERTO.')
    elif t['FALHA'] == 0:
        linhas.append('SEM FALHAS (ha pontos de atencao).')
    else:
        linhas.append('HA FALHAS - olhar acima.')
    return '\n'.join(linhas)

# =========================================================
# FIM DE ARQUIVO: backend\utils\validador_blockchain.py
# =========================================================
