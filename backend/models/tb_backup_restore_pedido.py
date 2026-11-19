# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\models
# MODULO: backend\models\tb_backup_restore_pedido.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-04 13:40 -03
# ATUALIZADO EM: 2026-09-04 20:00
# VERSAO: 1.1.0
#
# DESCRICAO:
#     Model da tabela tb_backup_restore_pedido - registra o
#     PEDIDO DE RESTORE feito pelo TITULAR (Sessao 046,
#     04/09/2026). O Backup em si (arquivo .dump) nao tem
#     Model/tabela - vive so no disco.
#
#     Vive dentro do schema do Produtor (Schema-por-Produtor,
#     mesma logica de tb_log_operacoes) - isolamento garantido
#     pelo proprio schema, sem coluna id_produtor.
#
#     atendido_em/atendido_por ficam NULOS ate a Consiste
#     executar o Restore - usados tanto para saber SE ja foi
#     atendido (nao aparece mais como pendente) quanto para
#     auditoria (quem executou, quando).
#
#     Regras de negocio (Sessao 046):
#       - Quem pode pedir: TITULAR/ADMINISTRADOR/ADMINISTRATIVO.
#       - Quem executa: so perfil CONSISTE, tela propria.
#       - arquivo_seguranca_gerado guarda o nome do backup extra
#         tirado automaticamente do estado atual, antes do
#         Restore rodar - rede de seguranca contra arrependimento.
#
#     v1.0.0: Criacao do modulo (Sessao 046, 04/09/2026, 13:40 -03).
#     v1.1.0: Sessao 046 (04/09/2026, 17:30 -03) - Adicionada
#             coluna expirado_em (mecanismo de expiracao
#             automatica de Pedidos de Restore nao atendidos em 7
#             dias corridos - decisao de Benedito). Fica NULA ate
#             o pedido vencer sem atendimento - usada tanto para
#             sumir da lista de pendentes da Consiste quanto para
#             exibir o selo "Expirado" do lado do Produtor. Nunca
#             apaga o registro - mesmo espirito de auditoria ja
#             usado em atendido_em.
# =========================================================

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from datetime import datetime
from .certificadora import Base


# -------------------------------------------------------
# Model BackupRestorePedido
# Espelha a tabela tb_backup_restore_pedido no PostgreSQL
# -------------------------------------------------------
class BackupRestorePedido(Base):
    __tablename__ = 'tb_backup_restore_pedido'

    id                       = Column(Integer, primary_key=True)

    # Quem pediu o Restore - TITULAR/ADMINISTRADOR/ADMINISTRATIVO
    id_usuario               = Column(Integer, ForeignKey('public.usuarios.id'), nullable=False)

    id_propriedade           = Column(Integer, ForeignKey('public.propriedades.id'), nullable=False)

    # Texto livre explicando o motivo do pedido.
    motivo                   = Column(String(255), nullable=False)

    # Qual backup diario (data) o Titular quer que seja restaurado.
    data_backup_desejada     = Column(Date, nullable=False)

    criado_em                = Column(DateTime, nullable=False, default=datetime.now)

    # Preenchidos so quando a Consiste executa o Restore - NULOS
    # ate la. atendido_em preenchido = pedido ja resolvido.
    atendido_em              = Column(DateTime)
    atendido_por             = Column(Integer, ForeignKey('public.usuarios.id'))

    # Nome do arquivo de backup que foi de fato usado no Restore
    # (pode nao ser exatamente a data pedida, ex.: se aquele dia
    # nao tiver backup disponivel e a Consiste usar outro).
    arquivo_backup_usado     = Column(String(255))

    # Nome do backup extra tirado automaticamente do estado ATUAL
    # antes do Restore rodar - rede de seguranca.
    arquivo_seguranca_gerado = Column(String(255))

    # NULO ate o pedido passar de 7 dias sem atendimento (v1.1.0) -
    # preenchido automaticamente, nunca pelo Usuario. Um pedido
    # nunca fica com atendido_em E expirado_em preenchidos ao
    # mesmo tempo (um exclui o outro na pratica).
    expirado_em              = Column(DateTime)

    def __repr__(self):
        return f'<BackupRestorePedido {self.id} (Propriedade {self.id_propriedade})>'

# =========================================================
# FIM DE ARQUIVO: backend\models\tb_backup_restore_pedido.py
# =========================================================