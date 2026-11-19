# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_4001_gta_animais.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-15 11:45 -03
# ATUALIZADO EM: 2026-09-29 06:55 -03
# VERSAO: 1.3.0
#
# DESCRICAO:
#     Model da tabela tb_4001_gta_animais.
#     Tabela filha de tb_4001_gta (1:N) - uma linha por
#     categoria de animal declarada na GTA (especie/sexo/
#     idade em meses/quantidade), ex.: "BOV MACHO 13 a 24
#     Meses: 37". E o "Esperado" que alimenta a pre-criacao
#     das linhas da tb_5001_brincagem e o Quadro de
#     visualizacao do Brete (COUNT em tempo real de linhas
#     com Sisbov NULL, agrupado por categoria).
#
#     Sem correspondente no legado GERAS (a 4001 legada
#     guardava so um total unico de animais, nao quebrado por
#     categoria) - motivado pela leitura de uma e-GTA real
#     (IAGRO/MS), que lista quantidade por Sexo + Faixa de
#     Idade.
#
#     ESPECIE (v1.3.0, regra de Benedito, Sessao 082): grava
#     SEMPRE o CODIGO do catalogo tb_4002_especie ("BOV",
#     "BUB") - nunca a palavra por extenso. A tela mostra a
#     descricao ("Bovino") via backend\utils\especies.py.
#
#     v1.0.0: Criacao do modulo (Sessao 17), a partir da
#             estrutura real de tb_4001_gta_animais conferida
#             no pgAdmin (8 colunas).
#     v1.1.0: Sessao 17 (continuacao) - Decisao arquitetural:
#             banco unico + RLS por produtor (schema-por-produtor
#             descartado apos pesquisa mostrar degradacao entre
#             1.000-2.000 schemas). Adicionada coluna id_produtor
#             direta, para a politica de RLS nao depender de JOIN
#             via id_gta.
#     v1.2.0: Sessao 018 - Decisao arquitetural revertida: RLS
#             descartado, Schema-por-Produtor confirmado como
#             modelo definitivo. Coluna id_produtor removida -
#             era suporte tecnico exclusivo do RLS. No modelo de
#             Schema-por-Produtor o isolamento ja e fisico (a
#             tabela inteira, incluindo esta linha filha de Gta,
#             mora dentro do schema do Produtor dono) - manter a
#             coluna seria redundante e um risco de dessincronia.
#     v1.3.0: Sessao 082 (29/09/2026, 06:55 -03) - Valor padrao
#             de especie trocado de 'BOVINO' para 'BOV' (codigo do
#             catalogo tb_4002). O padrao existe SO aqui no Python
#             - a coluna no banco nao tem DEFAULT (conferido na
#             Sessao 082 em todos os schemas). Motivo: a especie
#             por extenso travava a Brincagem Sequencial, que
#             procura o codigo. Dados antigos convertidos por SQL
#             (Tabelas\converter_especie_codigo_s082.sql). Nenhuma
#             outra mudanca de coluna/tipo/FK.
# =========================================================

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model GtaAnimal
# Espelha a tabela tb_4001_gta_animais no PostgreSQL
# -------------------------------------------------------
class GtaAnimal(Base):
    __tablename__ = 'tb_4001_gta_animais'

    # Identificacao
    id              = Column(Integer, primary_key=True)

    # Vinculo obrigatorio com o cabecalho da GTA. Isolamento
    # entre Produtores diferentes e garantido pelo schema
    # (Schema-por-Produtor) - nao precisa de coluna id_produtor
    # aqui, ver changelog v1.2.0.
    id_gta          = Column(Integer, ForeignKey('tb_4001_gta.id'), nullable=False)
    gta             = relationship('Gta', foreign_keys=[id_gta], backref='animais')

    # Categoria declarada na GTA. v1.3.0: especie = CODIGO do
    # catalogo tb_4002 ("BOV"/"BUB") - ver DESCRICAO.
    especie         = Column(String(20), nullable=False, default='BOV')
    sexo            = Column(String(10), nullable=False)
    idade_meses     = Column(String(20), nullable=False)   # faixa em texto livre, ex.: "13 A 24"
    quantidade      = Column(Integer, nullable=False)

    # Controle de datas
    criado_em       = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em   = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<GtaAnimal {self.especie} {self.sexo} {self.idade_meses} qtd={self.quantidade}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_4001_gta_animais.py
# =========================================================
