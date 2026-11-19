# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_5001_brincagem.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-15 11:50 -03
# ATUALIZADO EM: 2026-10-26 14:30 -03
# VERSAO: 1.6.0
#
# DESCRICAO:
#     Model da tabela tb_5001_brincagem.
#     Staging de pre-Comunicado - nasce pre-populada por
#     categoria a partir de tb_4001_gta_animais (Opcao 1, GTA ja
#     lancada - fora de escopo ate ter mockups reais) OU nasce do
#     ZERO na leitura, sem GTA vinculada (Opcao 2, escopo da
#     Sessao 057 - modulo Brincagem com Leitor,
#     backend/routers/brincagem_leitor.py).
#
#     Usada pela Brincagem FISICA (Leitor/Bastao, no Brete) -
#     distinta da Brincagem Sequencial de escritorio, ja pronta,
#     que usa tb_3007/tb_7017/tb_2001/tb_2017/tb_7002 diretamente,
#     sem passar por esta tabela.
#
#     Campo sts (boolean, default False): Sts = False significa
#     que a brincagem ja foi feita mas o Comunicado ainda nao
#     foi gerado. Este e o mesmo campo consultado na validacao de
#     duplicidade da leitura (junto com tb_2001_entradas e
#     tb_7002_pia - ver brincagem_leitor.py).
#
#     Campo saida_brincos (COM/SEM) protegido por CHECK
#     constraint no banco (chk_tb_5001_brincagem_saida_brincos).
#
#     numero_comunicado - preenchido depois, quando o ciclo for
#     fechado (Gerar Comunicado de Entrada, tb_2012_com_entrada).
#     SEM ForeignKey de proposito - mesmo padrao/mesmo NOME de
#     campo ja usado em tb_4001_gta, tb_2001 e
#     tb_7017_entrada_brincos_rfid.
#
#     id_propriedade (obrigatorio) diferencia, dentro do mesmo
#     schema de Produtor, para qual Propriedade dele cada linha
#     de brincagem pertence.
#
#     v1.0.0: Criacao do modulo (Sessao 17), a partir da
#             estrutura real de tb_5001_brincagem conferida no
#             pgAdmin (16 colunas). Nascida com coluna
#             id_produtor (suporte a RLS, decisao vigente
#             naquele momento).
#     v1.1.0: Sessao 018 - Decisao arquitetural revertida: RLS
#             descartado, Schema-por-Produtor confirmado como
#             modelo definitivo. Coluna id_produtor removida.
#     v1.3.0: Sessao 052 (14/09/2026, 17:10 -03) - Coluna
#             id_comunicado RENOMEADA para numero_comunicado.
#     v1.4.0: Sessao 057 (20/09/2026, 10:15 -03) - As 8
#             alteracoes fechadas na Especificacao do modulo
#             Brincagem com Leitor (Especificacao_Brincagem_
#             Leitor.docx, Sessao 056), aplicadas via script SQL
#             Tabelas\N_recriar_tb_5001_brincagem_criar_tb_5003.sql
#             (ambiente de teste - tabela recriada, sem migracao
#             de dados, conforme confirmado por Benedito):
#               - id_gta: nullable=False -> nullable=True
#                 (opcional agora - Opcao 2 nasce sem GTA).
#               - raca (varchar) REMOVIDA -> SUBSTITUIDA por
#                 id_raca (FK). NOTA: a FK abaixo segue o MESMO
#                 padrao ja usado em tb_2001_entradas.py (SEM
#                 prefixo 'public.' na string, embora a tabela
#                 viva no schema public) - padrao copiado
#                 literalmente do arquivo real (Regra de Ouro
#                 #1), nao corrigido por conta propria.
#               - idade_meses (varchar) REMOVIDA -> SUBSTITUIDA
#                 por id_idade_meses (FK, schema public,
#                 confirmado na secao 13 do Regras.txt).
#               - sexo: PADRONIZADO de String(10) solto para o
#                 MESMO sexo_enum ja usado em tb_2001_entradas.py
#                 (schema public, create_type=False).
#               - id_especie: NOVA coluna (FK, schema public,
#                 mesmo padrao ja usado em tb_2001_entradas.py).
#               - peso: NOVA coluna (Numeric 10,2).
#               - nascimento: NOVA coluna (Date) - calculada na
#                 tela de Leitura, mas editavel.
#               - data_brincagem: NOVA coluna (Date) - informada
#                 na Tela 02 (Selecao), base do calculo de
#                 Nascimento.
#     v1.4.1: Sessao 059 (20/09/2026, 11:20 -03) - Comentario do
#             id_raca ATUALIZADO (sem mudanca de coluna/tipo/FK):
#             a Sessao 059 confirmou, ao ver backend/routers/
#             racas.py, que tb_4005_racas de fato vive no schema
#             do Produtor (nao e catalogo compartilhado) - o que
#             era uma suposicao copiada de tb_2001_entradas.py
#             agora esta confirmado de verdade.
#     v1.5.0: Sessao 082 (29/09/2026, 20:05 -03) - NOVA coluna
#             tipo_entrada (VARCHAR 10, NOT NULL, default
#             'COMPRA'), criada em todos os schemas pelo script
#             Tabelas\tb_5001_tipo_entrada_s082.sql (linhas antigas
#             viraram COMPRA). Valores: COMPRA / NASCIMENTO - lista
#             fixa em backend\utils\regras_sisbov.py v1.1.0,
#             protegida por CHECK no banco
#             (chk_tb_5001_brincagem_tipo_entrada). Leitura de
#             NASCIMENTO no brete nao passa pelo Vincular GTA: ela
#             entra no Numero de Controle (NAS) da Propriedade +
#             Data de Brincagem (backend\utils\gravacao_
#             nascimento.py). Nenhuma outra mudanca de coluna.
#     v1.6.0: Sessao 106 (26/10/2026, 14:30 -03) - NOVA coluna id_gta_reservada (INTEGER, NULL, FK tb_4001_gta): leitura do brete
#             reservada a uma GTA de Compra PENDENTE (Brincagem com Leitor). Script SQL: Tabelas\tb_5001_id_gta_reservada_s106.sql.
#             REVERSAO: .bak_antes_s106l.
# =========================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# ENUM ja existente no banco (create_type=False: apenas
# referencia, nunca tenta recriar) - MESMO de tb_2001_entradas.py
# e tb_7002_pia.py (v1.4.0).
# -------------------------------------------------------
sexo_enum = PgEnum('MACHO', 'FEMEA', name='sexo_enum', schema='public', create_type=False)


# -------------------------------------------------------
# Model Brincagem
# Espelha a tabela tb_5001_brincagem no PostgreSQL
# -------------------------------------------------------
class Brincagem(Base):
    __tablename__ = 'tb_5001_brincagem'

    # Identificacao
    id                  = Column(Integer, primary_key=True)

    # Vinculo com o cabecalho da GTA - v1.4.0: agora OPCIONAL
    # (Opcao 2 do modulo Brincagem com Leitor nasce sem GTA
    # vinculada; a vinculacao acontece depois, via futuro modulo
    # Consulta Brincagem).
    id_gta              = Column(Integer, ForeignKey('tb_4001_gta.id'), nullable=True)
    gta                 = relationship('Gta', foreign_keys=[id_gta], backref='linhas_brincagem')

    # Lado interno (Propriedade dona da brincagem). Isolamento
    # entre Produtores diferentes e garantido pelo schema
    # (Schema-por-Produtor) - nao precisa de coluna id_produtor.
    id_propriedade      = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    propriedade         = relationship('Propriedade', foreign_keys=[id_propriedade])

    # Categoria do animal - v1.4.0: raca/idade_meses (varchar
    # solto) SUBSTITUIDOS por FKs para os catalogos reais
    # (Regra de Ouro #8 - confirmado com Benedito, Sessao 057,
    # que Especie/Raca/Idade em Meses SAO tabelas de catalogo
    # de verdade, nao listas fixas).
    sexo                = Column(sexo_enum, nullable=False)
    id_especie          = Column(Integer, ForeignKey('public.tb_4002_especie.id'), nullable=False)
    # id_raca: SEM prefixo 'public.' de proposito - CONFIRMADO na
    # Sessao 059 (ao ver backend/routers/racas.py): tb_4005_racas
    # NAO e catalogo compartilhado, vive DENTRO do schema de cada
    # Produtor (populada via backend/scripts/popular_racas.py,
    # Sessao 047, ~106 racas por Produtor, com o campo 'comum'
    # controlando quais aparecem no dia a dia). A suposicao
    # inicial (copiada de tb_2001_entradas.py sem confirmar o
    # motivo) estava certa por sorte - agora esta confirmada de
    # verdade, nao mais um "padrao copiado sem entender".
    id_raca             = Column(Integer, ForeignKey('tb_4005_racas.id'), nullable=False)
    id_idade_meses      = Column(Integer, ForeignKey('public.tb_4006_idade_meses.id'))

    # Identificacao do animal - em branco ate o Peao ocupar a linha no Brete
    sisbov              = Column(String(15))
    rfid                = Column(String(30))
    manejo              = Column(String(6))

    # Dados operacionais da brincagem
    lote                = Column(String(100))       # texto livre, piquete/pasto
    saida_brincos       = Column(String(3))          # COM / SEM (CHECK no banco)

    # v1.4.0: NOVAS colunas (ver Especificacao_Brincagem_Leitor.docx secao 5.1)
    peso                = Column(Numeric(10, 2))
    nascimento          = Column(Date)
    data_brincagem      = Column(Date)

    # v1.5.0: COMPRA ou NASCIMENTO (lista fixa em regras_sisbov.py,
    # CHECK no banco). Default COMPRA = comportamento de sempre.
    tipo_entrada        = Column(String(10), nullable=False, default='COMPRA')

    # Sts = False: brincagem feita, Comunicado ainda nao gerado
    sts                 = Column(Boolean, nullable=False, default=False)

    # Numero oficial do Comunicado de Entrada. SEM ForeignKey de
    # proposito - mesmo padrao das outras 3 tabelas.
    numero_comunicado   = Column(Integer)

    # v1.6.0 (Sessao 106): leitura do brete RESERVADA a uma GTA de Compra ainda PENDENTE (Brincagem com Leitor, caso 1).
    # So vale enquanto id_gta for nulo e sts for False; no ultimo brinco o vinculo automatico preenche id_gta e a reserva deixa de contar.
    id_gta_reservada    = Column(Integer, ForeignKey('tb_4001_gta.id'), nullable=True)

    # Controle de datas
    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em       = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Brincagem sisbov={self.sisbov or "(vazio)"}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_5001_brincagem.py
# =========================================================