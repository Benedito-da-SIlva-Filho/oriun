# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_7017_entrada_brincos_rfid.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-07-17 10:20 -03
# ATUALIZADO EM: 2026-09-14 17:10 -03
# VERSAO: 1.3.0
#
# DESCRICAO:
#     Model da tabela tb_7017_entrada_brincos_rfid.
#     Registro definitivo/consolidado do brinco aplicado a um
#     animal - une dados de entrada (lote, raca, nascimento) e
#     dados de saida (quando o animal sai da Propriedade), num
#     unico registro por SISBOV.
#
#     Vive dentro do schema do Produtor (Schema-por-Produtor,
#     conforme classificacao fechada na Sessao 018).
#
#     Ultimo elo antes do ciclo de Brincagem/Comunicado:
#     1021 (Fabricantes) -> 3007 (Brincos Entrada) -> gera ->
#     7017 (este) -> atualizado por -> Brincagem Sequencial
#     (Sessoes 047/048/049) -> carrega definitivamente em ->
#     2001 (Animal) -> recebe numero_comunicado ao Gerar
#     Comunicado (Sessao 052, este arquivo tambem recebe).
#
#     id_lote_entrada: FK para tb_3007_brincos_entrada - mesmo
#     padrao usado em tb_3008_brincos_saida.
#
#     numero_comunicado (NOVA v1.3.0, Sessao 052, 14/09/2026, 17:10
#     -03): mesmo campo/mesma logica de tb_2001.numero_comunicado
#     (ver esse Model para a explicacao completa) - gravado quando
#     o Comunicado de Entrada e gerado para a GTA que consumiu este
#     brinco. NULLABLE, SEM ForeignKey. Script:
#     Tabelas\2_alter_numero_comunicado_2001_7017.sql.
#
#     v1.0.0: Criacao do modulo (Sessao 019), a partir da
#             estrutura real de tb_7017_entrada_brincos_rfid
#             conferida no pgAdmin (16 colunas).
#     v1.1.0: Sessao 042 (31/08/2026, 18:32 -03) - Adicionadas
#             cpf_produtor (String(18)) e status (String(20)).
#     v1.2.0: Sessao 049 (10/09/2026, 13:40 -03) - Adicionadas 2
#             colunas novas (reservado_id_gta Integer, reservado_ate
#             DateTime).
#     v1.3.0: Sessao 052 (14/09/2026, 17:10 -03) - Adicionada
#             coluna numero_comunicado (Integer, NULLABLE, SEM
#             ForeignKey), ja aplicada via ALTER TABLE (bloco DO $$
#             em loop) em todos os schemas produtor_NNNNN. Ver
#             DESCRICAO acima.
# =========================================================

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model EntradaBrincoRfid
# Espelha a tabela tb_7017_entrada_brincos_rfid no PostgreSQL
# -------------------------------------------------------
class EntradaBrincoRfid(Base):
    __tablename__ = 'tb_7017_entrada_brincos_rfid'

    # Identificacao
    id                 = Column(Integer, primary_key=True)

    # Propriedade do Produtor (dentro do schema) a que este
    # registro pertence - mesma logica de Gta.id_propriedade
    id_propriedade     = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    propriedade        = relationship('Propriedade', foreign_keys=[id_propriedade])

    # Lote de origem deste brinco (cadeia de rastreabilidade)
    id_lote_entrada    = Column(Integer, ForeignKey('tb_3007_brincos_entrada.id'), nullable=False)
    lote_entrada       = relationship('BrincoEntrada', foreign_keys=[id_lote_entrada])

    # Identificacao do animal
    sisbov              = Column(String(15), nullable=False)
    manejo               = Column(String(6))
    rfid                  = Column(String(15))

    # CPF/CNPJ do Produtor dono deste brinco (v1.1.0)
    cpf_produtor            = Column(String(18))

    # Status do brinco (v1.1.0) - NULO = Disponivel,
    # 'ENTRADA' = aplicado via Brincagem Sequencial, 'REIDENTI' =
    # trocado depois de aplicado.
    status                    = Column(String(20))

    # Dados de saida (preenchidos quando o animal sai da Propriedade,
    # OU quando e consumido pela Brincagem Sequencial - Sessao 049)
    saida_data             = Column(Date)
    saida_gta               = Column(String(10))
    saida_origem              = Column(String(20))  # texto livre, mesmo padrao de tb_2017

    # Dados de entrada/caracteristicas do animal
    raca                        = Column(String(2))
    nascimento                    = Column(Date)
    eras_dias                       = Column(Integer)
    sexo                              = Column(String(6))
    data_brincagem                     = Column(Date)

    # Reserva temporaria (v1.2.0, Sessao 049)
    reservado_id_gta                     = Column(Integer)
    reservado_ate                          = Column(DateTime)

    # Comunicado de Entrada (NOVO v1.3.0) - ver DESCRICAO acima.
    # SEM ForeignKey de proposito.
    numero_comunicado                       = Column(Integer)

    # Controle de datas
    criado_em                            = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em                          = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<EntradaBrincoRfid {self.sisbov} (RFID {self.rfid})>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_7017_entrada_brincos_rfid.py
# =========================================================
