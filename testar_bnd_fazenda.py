# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\Orion
# MODULO: testar_bnd_fazenda.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-18 20:40 -03
# VERSAO: 1.0.0
#
# DESCRICAO: Teste do BND/Fazenda SEM banco (Sessao 132). Rodar na pasta C:\Orion:  python testar_bnd_fazenda.py
#   1) leitor por Produtor com o EXTRATO DE VIVOS.pdf real e com um PDF sintetico de 2 Produtores;
#   2) comparacao (01 a 04) com dados montados na mao;
#   3) plano de correcao e as instrucoes SQL (gravadas num "banco de mentira");
#   4) os 4 PDFs saem em C:\Orion\_tmp_s132\ (para olhar).
# =========================================================
import copy
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.leitores import leitor_mapa_extrato_vivos as leitor
from backend.utils import bnd_fazenda as bf
from backend.utils import carga_animais as ca
from backend.utils import pdf_bnd_fazenda as pdf

OK, FALHAS = 0, []


def confere(nome, condicao, detalhe=''):
    global OK
    if condicao:
        OK += 1
        print('  ok  ', nome)
    else:
        FALHAS.append(nome)
        print('  FALHA', nome, detalhe)


PASTA = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(PASTA, '_tmp_s132')
os.makedirs(SAIDA, exist_ok=True)

# ---------------------------------------------------------
print('1) Leitor por Produtor - arquivo real')
real = os.path.join(PASTA, 'EXTRATO DE VIVOS.pdf')
partes = leitor.ler_partes(real)
confere('1 parte', len(partes) == 1, len(partes))
p = partes[0]
confere('1.244 animais', len(p['animais']) == 1244, len(p['animais']))
confere('CPF do Produtor', p['cabecalho']['produtor_documento'] == '00453021972', p['cabecalho']['produtor_documento'])
confere('Propriedade e codigo', p['cabecalho']['cod_propriedade'] == '32570' and p['cabecalho']['nirf'] == '08806306', p['cabecalho'])
confere('totais 31 F / 1213 M', (p['cabecalho']['total_femea'], p['cabecalho']['total_macho']) == (31, 1213))
antigo = leitor.ler(real)
confere('igual ao ler() antigo', [a['sisbov'] for a in antigo['animais']] == [a['sisbov'] for a in p['animais']])
confere('nenhuma linha nao lida', not p['linhas_nao_lidas'], p['linhas_nao_lidas'][:2])

# ---------------------------------------------------------
print('2) Leitor por Produtor - PDF sintetico com 2 Produtores')
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

sint = os.path.join(SAIDA, 'sintetico_2_produtores.pdf')
c = canvas.Canvas(sint, pagesize=A4)
y = 800


def linha(t):
    global y
    c.drawString(40, y, t)
    y -= 14


for nome, doc, animais in [('JOSE LUIZ FRAGNAN', '004.530.219-72', [('105500191288651', '15/10/2004', 'Nelore', 'Macho', '17/10/2006'), ('105500191288660', '15/10/2004', 'Nelore', 'Fêmea', '17/10/2006')]),
                           ('MARIA DA SILVA', '123.456.789-09', [('105500191288759', '01/02/2020', 'Composto', 'Macho', '05/03/2021')])]:
    linha('Entidade Certificadora: QIMA RASTREABILIDADE E CERTIFICACOES LTDA')
    linha('Propriedade: FAZENDA SÃO JOSÉ Nirf / Incra: 08806306 Cód. Propriedade: 32570')
    linha('Município: ITAQUIRAÍ UF: MS')
    linha('Proprietário dos Animais (Produtor)')
    linha(f'Nome: {nome} CPF/CNPJ: {doc}')
    linha('Animais Vivos')
    linha(f'Total Fêmea: {sum(1 for a in animais if a[3] != "Macho")} Total Macho: {sum(1 for a in animais if a[3] == "Macho")}')
    linha('Nº Sisbov Data Nasc.Raça Sexo Data Inclusão Invent.')
    for a in animais:
        linha(f'{a[0]} {a[1]} {a[2]} {a[3]} {a[4]} S')
c.save()
ps = leitor.ler_partes(sint)
confere('2 partes', len(ps) == 2, len(ps))
confere('docs por parte', [x['cabecalho']['produtor_documento'] for x in ps] == ['00453021972', '12345678909'])
confere('animais por parte 2 e 1', [len(x['animais']) for x in ps] == [2, 1])
confere('totais por parte', (ps[0]['cabecalho']['total_femea'], ps[0]['cabecalho']['total_macho']) == (1, 1))
confere('escolher_parte pelo CPF', bf.escolher_parte(ps, ('', '12345678909'))['cabecalho']['produtor_nome'] == 'MARIA DA SILVA')
confere('escolher_parte sem achar', bf.escolher_parte(ps, ('99999999999', '')) is None)

# ---------------------------------------------------------
print('3) Comparacao 01 a 04')
racas_nome = {ca.normalizar_nome('Nelore'): (1, 'NE'), ca.normalizar_nome('Composto'): (2, 'CO')}
for _n in sorted({a['raca_nome'] for a in p['animais']}):   # as outras racas do Extrato real entram no cadastro de mentira
    racas_nome.setdefault(ca.normalizar_nome(_n), (len(racas_nome) + 1, 'R%d' % (len(racas_nome) + 1)))
racas_id = bf.racas_por_id(racas_nome)
bnd = p['animais']
fazenda = {a['sisbov']: {'sexo': a['sexo'], 'nascimento': a['nascimento'], 'id_raca': racas_nome[ca.normalizar_nome(a['raca_nome'])][0],
                         'data_inclusao': a['data_inclusao']} for a in bnd}
codigos = [a['sisbov'] for a in bnd]
# 3 animais so na BND (saem da fazenda)
for s in codigos[:3]:
    del fazenda[s]
# 2 animais so na fazenda
fazenda['105500000000011'] = {'sexo': 'MACHO', 'nascimento': date(2020, 1, 1), 'id_raca': 1, 'data_inclusao': date(2021, 1, 1)}
fazenda['105500000000020'] = {'sexo': 'FEMEA', 'nascimento': date(2020, 1, 1), 'id_raca': 1, 'data_inclusao': date(2021, 1, 1)}
# divergencias: 5 nascimento, 1 sexo, 1 raca, 1 so inclusao
alvo = codigos[10:20]
for s in alvo[:5]:
    fazenda[s]['nascimento'] = date(2004, 10, 17)
fazenda[alvo[5]]['sexo'] = 'FEMEA' if fazenda[alvo[5]]['sexo'] == 'MACHO' else 'MACHO'
fazenda[alvo[6]]['id_raca'] = 2
fazenda[alvo[7]]['data_inclusao'] = date(2001, 1, 1)
comp = bf.comparar(fazenda, bnd, racas_nome, racas_id)
confere('01 = 1241 nos dois', len(comp['igual']) == 1241, len(comp['igual']))
confere('02 = 2 so fazenda', len(comp['so_fazenda']) == 2)
confere('03 = 3 so BND', comp['so_bnd'] == sorted(codigos[:3]))
confere('04 = 7 inconformidades (inclusao nao entra)', len(comp['inconformidades']) == 7, len(comp['inconformidades']))
res = bf.resumo_comparacao(comp)
confere('resumo nasc 5, sexo 1, raca 1', (res['nasc'], res['sexo'], res['raca']) == (5, 1, 1), res)
confere('formato do codigo com DV', bf.formatar_sisbov('105500191288651') == '10550019128865-1')
plano = bf.plano_correcao(fazenda, bnd, racas_nome)
confere('plano: 7 animais, 5 nasc, 1 sexo, 1 raca, 1 inclusao', (plano['animais'], plano['nascimento'], plano['sexo'], plano['raca'], plano['data_inclusao']) == (7, 5, 1, 1, 1), plano)
bnd2 = copy.deepcopy(bnd)
bnd2[30]['raca_nome'] = 'Raca Inexistente'
bnd2[31]['nascimento'] = None
plano2 = bf.plano_correcao(fazenda, bnd2, racas_nome)
confere('raca desconhecida e nascimento invalido sao avisos, nao correcao', plano2['raca_desconhecida'] == 1 and plano2['nasc_invalido'] == 1, plano2)

# ---------------------------------------------------------
print('4) Instrucoes SQL da correcao (banco de mentira)')


class Fake:
    def __init__(self):
        self.sqls = []
        self.itens = []

    def execute(self, stmt, params=None):
        self.sqls.append((str(stmt), dict(params or {})))
        class R:
            def all(self_inner):
                return []
        return R()

    def add(self, obj):
        self.itens.append(obj)

    def flush(self):
        for o in self.itens:
            if getattr(o, 'id', None) is None:
                o.id = 1


fake = Fake()
resumo = bf.aplicar_correcao(fake, 7, fazenda, bnd, racas_nome, 99)
confere('mesmo resumo do plano', resumo == plano)
tabelas = {}
for sql, par in fake.sqls:
    t = sql.split()[1]
    tabelas[t] = tabelas.get(t, 0) + 1
    confere_ok = par.get('p') == 7 and 's' in par
    if not confere_ok:
        FALHAS.append('sql sem filtro de Propriedade/SISBOV: ' + sql)
confere('so tb_2001, tb_2017_movimentacoes e tb_7017 sao tocadas', set(tabelas) == {'tb_2001', 'tb_2017_movimentacoes', 'tb_7017_entrada_brincos_rfid'}, tabelas)
confere('nada em tb_7002 (PIA)', not any('tb_7002' in s for s, _ in fake.sqls))
confere('tb_7017 nao leva data de inclusao', not any('tb_7017' in s and 'data_inclusao' in s for s, _ in fake.sqls))
confere('1 Log gravado', len(fake.itens) == 1 and fake.itens[0].modulo == 'bnd_fazenda', [getattr(o, "modulo", None) for o in fake.itens])
print('     descricao do Log:', fake.itens[0].descricao if fake.itens else None)
sql_exemplo = next(s for s, par in fake.sqls if s.split()[1] == 'tb_2001' and 'sexo' in s)
print('     exemplo:', sql_exemplo)

# ---------------------------------------------------------
print('5) Os 4 PDFs (em _tmp_s132)')
dados = {'prod_nome': 'JOSE LUIZ FRAGNAN', 'prop_nome': 'FAZENDA SÃO JOSÉ'}
eventos = {codigos[0]: ('Venda', date(2026, 10, 2)), codigos[1]: ('Morte', date(2026, 9, 12))}
saidas = {
    1: pdf.montar_codigos(1, dados, comp['igual']),
    2: pdf.montar_codigos(2, dados, comp['so_fazenda']),
    3: pdf.montar_bnd_nao_fazenda(dados, comp['so_bnd'], eventos),
    4: pdf.montar_inconformidades(dados, comp['inconformidades']),
}
for n, buf in saidas.items():
    caminho = os.path.join(SAIDA, pdf.nome_arquivo(n, dados))
    with open(caminho, 'wb') as f:
        f.write(buf.getvalue())
    confere(f'PDF {n} gerado', buf.getbuffer().nbytes > 1500, caminho)
vazio = pdf.montar_inconformidades(dados, [])
confere('PDF 04 sem divergencias gera', vazio.getbuffer().nbytes > 1000)

print()
print(f'{OK} verificacoes OK, {len(FALHAS)} falhas')
if FALHAS:
    for f in FALHAS:
        print('  -', f)
    sys.exit(1)
print('TUDO OK')
