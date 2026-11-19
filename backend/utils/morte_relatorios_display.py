# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\morte_relatorios_display.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-01 19:20 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.1.0
# v1.1.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
#
# DESCRICAO:
#     Monta os dados dos relatorios da Morte (pdf_relatorio_morte.py): Controle Interno (um MRT) e Mortes no Periodo (por data da morte).
#     Cada animal vem da tb_2002 (tipo_saida = MORTE); Eras = faixa de idade em meses completos NA DATA DA MORTE; Sexo escrito como no Magic
#     (MACHO / FEMEA). Origem: Produtor, CPF/CNPJ (regra por fazenda), NIRF, IE, Cod. ERAS, Propriedade, Municipio/UF e CEP. O campo
#     "Produtor Rural" do relatorio do GERAS (codigo interno do Produtor) nao existe no Orion e sai em branco.
#
#     v1.0.0: Sessao 111 (01/11/2026) - Criacao. REVERSAO: apagar este arquivo.
#     v1.0.1: Sessao 113 (03/11/2026, 16:05 -03) - PDF do Controle em ordem de Data da Morte (depois SISBOV).  REVERSAO: .bak_antes_s113_ordem_controle.
# =========================================================
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Propriedade
from backend.models.propriedade_produtor import PropriedadeProdutor
from backend.models.tb_1007_motivo_mortes import MotivoMorte
from backend.models.tb_2002_saida_animais import SaidaAnimal
from backend.utils.documentos_produtor import documentos_do_produtor
from backend.utils.notificacao_morte_display import ROTULO_TIPO_MORTE, ROTULO_DESTINO_MORTE, meses_completos
from backend.utils.pdf_relatorio_morte import faixa_eras


def _data_br(d):
    return d.strftime('%d/%m/%Y') if d else ''


def montar_origem(db, produtor, id_propriedade):
    propriedade = db.get(Propriedade, int(id_propriedade))
    vinculo = None
    if produtor is not None:
        vinculo = (db.query(PropriedadeProdutor)
                   .filter_by(id_propriedade=int(id_propriedade), id_produtor=produtor.id, data_fim=None).first())
    cpf, cnpj = documentos_do_produtor(produtor, vinculo)
    inscricao = (getattr(vinculo, 'inscricao_estadual', None) or getattr(propriedade, 'inscricao_estadual', None) or '') if propriedade else ''
    return {
        'produtor_nome': (produtor.nome if produtor else '') or '', 'cpf': cpf or '', 'cnpj': cnpj or '',
        'nirf': (getattr(propriedade, 'nirf_incra', None) or '') if propriedade else '',
        'inscricao_estadual': inscricao, 'codigo_eras': (propriedade.codigo_eras if propriedade else '') or '',
        'produtor_rural': '', 'propriedade_nome': (propriedade.nome if propriedade else '') or '',
        'municipio': (f'{propriedade.municipio or ""}/{propriedade.uf or ""}' if propriedade else ''),
        'cep': ''.join(c for c in ((propriedade.cep if propriedade else '') or '') if c.isdecimal()),
    }


def _animais(linhas):
    with Session(engine) as dbp:
        causas = {m.id: m.descricao for m in dbp.query(MotivoMorte).all()}
    saida = []
    for a in linhas:
        meses = meses_completos(a.nascimento, a.data_saida)
        saida.append({
            'sisbov': a.sisbov, 'tipo': ROTULO_TIPO_MORTE.get(a.tipo_morte, a.tipo_morte or ''), 'data': _data_br(a.data_saida),
            'causa': causas.get(a.id_motivo_morte, ''), 'destino': (ROTULO_DESTINO_MORTE.get(a.destino_morte, a.destino_morte or '')).upper(),
            'sexo': a.sexo, 'sexo_texto': 'FEMEA' if a.sexo == 'FEMEA' else ('MACHO' if a.sexo == 'MACHO' else ''),
            'eras': faixa_eras(meses),
        })
    return saida


def contexto_controle(db, produtor, id_propriedade, controle, texto_controle, impresso_em):
    linhas = (db.query(SaidaAnimal).filter(SaidaAnimal.id_com_morte == controle.id, SaidaAnimal.tipo_saida == 'MORTE',
                                           SaidaAnimal.id_propriedade == int(id_propriedade)).order_by(SaidaAnimal.data_saida.asc(), SaidaAnimal.sisbov.asc()).all())   # em ordem da Data da Morte
    return {'origem': montar_origem(db, produtor, id_propriedade), 'animais': _animais(linhas),
            'controle_texto': texto_controle, 'impresso_em': impresso_em}


def contexto_periodo(db, produtor, id_propriedade, data_ini, data_fim):
    linhas = (db.query(SaidaAnimal).filter(SaidaAnimal.id_propriedade == int(id_propriedade), SaidaAnimal.tipo_saida == 'MORTE',
                                           SaidaAnimal.data_saida >= data_ini, SaidaAnimal.data_saida <= data_fim)
              .order_by(SaidaAnimal.data_saida.asc(), SaidaAnimal.sisbov.asc()).all())
    return {'origem': montar_origem(db, produtor, id_propriedade), 'animais': _animais(linhas),
            'periodo': (_data_br(data_ini), _data_br(data_fim))}

# =========================================================
# FIM DE ARQUIVO: backend\utils\morte_relatorios_display.py
# =========================================================
