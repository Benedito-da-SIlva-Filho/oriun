# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_6005_reidentificacao_com_baixa.py
# AUTOR: Benedito Silva Filho.
# CRIADO EM: 2026-07-25 12:45 -03
# ATUALIZADO EM: 2026-11-11 11:40 -03
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Model da tabela tb_6005_reidentificacao_com_baixa.
#     Cabecalho do pedido de Reidentificacao COM Baixa (origem
#     GR6005 do GERAS, pasta 6-Formularios, tela "Cadastrar
#     Reidentificacao" do menu Formularios) - o animal recebe um
#     SISBOV novo de fato (Antigo -> Novo), o codigo antigo e
#     baixado. Diferente de tb_6003_re_id_elementos (mesmo
#     SISBOV, so troca a peca fisica) e de Perda Saida Estoque
#     (GR6007/6008, pendente - animal sem nenhum elemento,
#     recadastro completo com dados biologicos).
#
#     Confirmado por Benedito (Sessao 022): esta tela e uma das
#     3 telas distintas do menu Formularios (Reidentificacao com
#     Baixa / sem Baixa / Cancelamento de Brinco), propositalmente
#     separadas na interface para evitar erro do usuario - o
#     Orion segue o mesmo principio, sem dropdown escondendo o
#     processo.
#
#     Vive no SCHEMA DO PRODUTOR (Schema-por-Produtor), mesmo
#     raciocinio ja validado em tb_5001_brincagem/tb_6003_re_id_
#     elementos: id_propriedade diferencia, dentro do mesmo
#     schema, para qual Propriedade daquele Produtor pertence
#     cada pedido.
#
#     Campo qtde_animais: mesma logica de tb_6003_re_id_elementos -
#     trava de conferencia manual do usuario, nao um status
#     automatico (nao existe coluna ABERTO/ENCERRADO).
#
#     Campo "Tipo Reidentificacao" do legado (GR6005) foi
#     DELIBERADAMENTE OMITIDO aqui - nos 15 registros reais
#     conferidos com Benedito, o valor era sempre o mesmo dentro
#     desta tabela (redundante, ja que a tabela inteira e dedicada
#     a este unico processo). Sem campo motivo (nao existe no
#     legado para este processo, diferente do GR6003).
#
#     "Codigo Reidentificacao" do legado = o proprio id (SERIAL)
#     desta tabela, sem coluna duplicada - mesmo padrao ja usado
#     em tb_6003_re_id_elementos.
#
#     v1.0.0: Criacao do modulo.
#     v1.1.0: Sessao 121 (2026-11-11 11:40 -03) - REIDENTIFICACAO do Orion (decisao do Benedito, 11/11/2026): este cabecalho e o PEDIDO
#         (Nro do Pedido = id). data_solicitacao = Data da Reidentificacao (igual para todos os animais do pedido). Colunas novas:
#         id_usuario (quem lancou), notificacao_gerada_em (PDF gerado), enviado_em / enviado_por (usuario marcou que enviou a
#         Notificacao a Certificadora; prazo de 30 dias). SQL: Tabelas\criar_reidentificacao_s121.sql. REVERSAO: .bak_antes_s121_reidentificacao.
# =========================================================

from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model ReidentificacaoComBaixa
# Espelha a tabela tb_6005_reidentificacao_com_baixa no PostgreSQL
# -------------------------------------------------------
class ReidentificacaoComBaixa(Base):
    __tablename__ = 'tb_6005_reidentificacao_com_baixa'

    # Identificacao - tambem cumpre o papel de "Codigo Reidentificacao"
    id                  = Column(Integer, primary_key=True)

    # Lado interno (Propriedade dona do pedido). Isolamento entre
    # Produtores diferentes e garantido pelo schema
    # (Schema-por-Produtor) - id_propriedade diferencia entre as
    # varias Propriedades que um mesmo Produtor pode ter.
    id_propriedade      = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)
    propriedade         = relationship('Propriedade', foreign_keys=[id_propriedade])

    # Trava de conferencia manual do usuario (nao e status automatico)
    qtde_animais        = Column(Integer, nullable=False)

    # Informada pelo usuario, pode ser retroativa
    data_solicitacao    = Column(Date, nullable=False)

    # v1.1.0 (s121) - quem lancou o pedido e o andamento da Notificacao a Certificadora
    id_usuario            = Column(Integer)
    notificacao_gerada_em = Column(DateTime)   # PDF da Notificacao gerado (vazio = ainda nao gerou)
    enviado_em            = Column(DateTime)   # usuario marcou 'enviado a Certificadora' (vazio = ABERTO: aparece na Home)
    enviado_por           = Column(Integer)

    # Controle de datas (gravacao real no banco)
    criado_em           = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em       = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<ReidentificacaoComBaixa {self.id}>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_6005_reidentificacao_com_baixa.py
# =========================================================