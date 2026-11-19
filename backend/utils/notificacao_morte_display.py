# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\notificacao_morte_display.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-01 18:30 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.1.0
# v1.1.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Monta os dados da NOTIFICACAO DE MORTE (Anexo XXII): a lista das Notificacoes (Impressao/Reimpressao) e o contexto do PDF
#     (pdf_anexo_xxii.py). Os animais da Notificacao sao os da tb_2002 (tipo_saida = MORTE) com o numero dela; saem em ordem de SISBOV.
#     Observacao de cada animal = sexo (F/M) + idade em MESES NA DATA DA MORTE (decisao do Benedito: a ERAS segue a data da morte).
#
#     v1.0.0: Sessao 111 (01/11/2026) - Criacao. REVERSAO: apagar este arquivo.
#     v1.0.1: Sessao 113 (03/11/2026, 15:40 -03) - Anexo XXII sai em ordem de Data da Morte (depois SISBOV), pois as mortes sao lancadas fora de ordem.  REVERSAO: .bak_antes_s113_ordem_data.
# =========================================================
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade
from backend.models.propriedade_produtor import PropriedadeProdutor
from backend.models.tb_1007_motivo_mortes import MotivoMorte
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.models.tb_2013_com_morte import ControleMorte
from backend.models.tb_2021_notificacao_morte import NotificacaoMorte
from backend.utils.documentos_produtor import documentos_do_produtor

ROTULO_TIPO_MORTE = {'ACIDENTAL': 'Acidental', 'DESLIGADO': 'Desligado', 'NATURAL': 'Natural', 'SACRIFICIO': 'Sacrifício'}
ROTULO_DESTINO_MORTE = {'CREMACAO': 'Cremação', 'ENTERRAMENTO': 'Enterramento', 'OUTROS': 'Outros'}


def _data_br(d):
    return d.strftime('%d/%m/%Y') if d else ''


def meses_completos(nascimento, data):
    """Meses completos entre o nascimento e a data (None se faltar algum)."""
    if nascimento is None or data is None or data < nascimento:
        return None
    meses = (data.year - nascimento.year) * 12 + (data.month - nascimento.month)
    if data.day < nascimento.day:
        meses -= 1
    return max(meses, 0)


def observacao_do_animal(sexo, nascimento, data_morte):
    letra = 'F' if sexo == 'FEMEA' else ('M' if sexo == 'MACHO' else '')
    meses = meses_completos(nascimento, data_morte)
    partes = [p for p in (letra, '' if meses is None else str(meses), '' if meses is None else 'meses') if p]
    return ' '.join(partes)


def listar_notificacoes(db, id_propriedade, status):
    """Lista de dicts das Notificacoes da Propriedade com o status pedido (ABERTO / IMPRESSO), mais recente primeiro."""
    linhas = (db.query(NotificacaoMorte)
              .filter(NotificacaoMorte.id_propriedade == int(id_propriedade), NotificacaoMorte.status == status)
              .order_by(NotificacaoMorte.numero_comunicado.desc()).all())
    resultado = []
    for n in linhas:
        qtd_mrt = db.query(ControleMorte).filter(ControleMorte.id_propriedade == int(id_propriedade),
                                                 ControleMorte.numero_comunicado == n.numero_comunicado).count()
        resultado.append({
            'numero_comunicado': n.numero_comunicado, 'gerada_em': n.criado_em.strftime('%d/%m/%Y %H:%M') if n.criado_em else '-',
            'qtd_mrt': qtd_mrt, 'total_animais': n.qtd_animais, 'status': n.status,
            'impresso_em': n.impresso_em, 'id_usuario_impressao': n.id_usuario_impressao,
        })
    return resultado


def montar_contexto_anexo_xxii(db, notificacao, produtor, id_propriedade):
    propriedade = db.get(Propriedade, int(id_propriedade))
    vinculo = None
    if produtor is not None:
        vinculo = (db.query(PropriedadeProdutor)
                   .filter_by(id_propriedade=int(id_propriedade), id_produtor=produtor.id, data_fim=None).first())
    cpf, cnpj = documentos_do_produtor(produtor, vinculo)

    animais = (db.query(SaidaAnimal)
               .filter(SaidaAnimal.id_propriedade == int(id_propriedade), SaidaAnimal.tipo_saida == 'MORTE',
                       SaidaAnimal.numero_comunicado == notificacao.numero_comunicado)
               .order_by(SaidaAnimal.data_saida.asc(), SaidaAnimal.sisbov.asc()).all())   # v1.0.1: em ORDEM DA DATA DA MORTE (Benedito, 03/11/2026)
    with Session(engine) as dbp:
        causas = {m.id: m.descricao for m in dbp.query(MotivoMorte).all()}

    return {
        'numero_comunicado': notificacao.numero_comunicado,
        'origem': {
            'produtor_nome': (produtor.nome if produtor else '') or '',
            'cpf': cpf or '', 'cnpj': cnpj or '',
            'codigo_eras': (propriedade.codigo_eras if propriedade else '') or '',
            'propriedade_nome': (propriedade.nome if propriedade else '') or '',
            'municipio': (f'{propriedade.municipio or ""}/{propriedade.uf or ""}' if propriedade else ''),
            'cep': ''.join(c for c in ((propriedade.cep if propriedade else '') or '') if c.isdecimal()),
        },
        'animais': [{
            'sisbov': a.sisbov,
            'tipo': ROTULO_TIPO_MORTE.get(a.tipo_morte, a.tipo_morte or ''),
            'causa': causas.get(a.id_motivo_morte, ''),
            'data': _data_br(a.data_saida),
            'obs': observacao_do_animal(a.sexo, a.nascimento, a.data_saida),
        } for a in animais],
    }

# =========================================================
# FIM DE ARQUIVO: backend\utils\notificacao_morte_display.py
# =========================================================
