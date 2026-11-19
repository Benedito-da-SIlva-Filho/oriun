# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\tb_2022_morte_fotos.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-11-01 16:30 -03
# ATUALIZADO EM: 2026-11-01 16:30 -03
# VERSAO:       1.0.0
#
# DESCRICAO:
#     Model da tabela tb_2022_morte_fotos - fotos do animal morto e do brinco (prova para Vistoria/Auditoria). Tabela POR-PRODUTOR.
#     Ate 2 fotos por animal (ordem 1 e 2), opcionais. A linha aponta para o animal na tb_2002 (tipo_saida = MORTE) com
#     ON DELETE CASCADE: quando o Desfazer apaga o lancamento, as fotos somem junto (decisao do Benedito, 01/11/2026); o arquivo
#     em disco e apagado pelo codigo do Desfazer. Pode anexar/trocar mesmo depois da Notificacao gerada (a foto nao muda o documento).
#     O arquivo fica em disco; aqui so o nome guardado e o controle (tamanho e hash).
#
#     v1.0.0: Sessao 111 (01/11/2026) - Criacao. REVERSAO: DROP TABLE produtor_NNNNN.tb_2022_morte_fotos (todos os schemas)
#             e voltar tb_versao_schema para 5.
# =========================================================
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from .certificadora import Base


class MorteFoto(Base):
    __tablename__ = 'tb_2022_morte_fotos'
    __table_args__ = (UniqueConstraint('id_saida_animal', 'ordem', name='uq_tb_2022_animal_ordem'),)

    id               = Column(Integer, primary_key=True)
    id_saida_animal  = Column(Integer, ForeignKey('tb_2002_saida_animais.id', ondelete='CASCADE'), nullable=False)
    ordem            = Column(Integer, nullable=False)           # 1 ou 2
    arquivo_nome     = Column(String(120), nullable=False)       # nome guardado em disco
    nome_original    = Column(String(200))
    tamanho_bytes    = Column(Integer)
    hash_sha256      = Column(String(64))
    id_usuario       = Column(Integer)
    criado_em        = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<MorteFoto {self.id_saida_animal}/{self.ordem}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_2022_morte_fotos.py
# =========================================================
