# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\log_operacoes.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-09-03 15:30 -03
# ATUALIZADO EM: 2026-11-18 20:30 -03
# VERSAO: 1.27.0
#
# DESCRICAO:
#     Utilitario GENERICO e REAPROVEITAVEL do mecanismo "Desfazer
#     por Operacao" (Log de Operacoes, alinhado com Benedito na
#     Sessao 045 - retomada de tarde, 15:00-15:30). Piloto de uso:
#     backend/routers/brincos_cancelamento.py.
#
#     Qualquer modulo que grave dados pode usar estas funcoes sem
#     escrever sua propria logica de desfazer - o "desfazer" e
#     GENERICO de verdade: le o nome da tabela + id da linha
#     mexida, usa REFLEXAO DE TABELA do SQLAlchemy (Table(...,
#     autoload_with=...)) para montar o UPDATE/DELETE na hora,
#     sem precisar conhecer o Model Python daquela tabela.
#
#     FLUXO DE USO (dentro da mesma transacao/sessao do modulo
#     que esta gravando, ex.: brincos_cancelamento.py /salvar):
#       1. id_operacao = registrar_operacao(db, id_usuario,
#          id_propriedade, modulo, descricao)
#       2. Para cada linha mexida, ANTES de gravar a mudanca:
#          capturar os campos antigos num dict.
#       3. Depois de gravar: registrar_item(db, id_operacao,
#          tabela, id_registro, tipo_mudanca, dados_antes,
#          dados_depois) - dados_antes/dados_depois sao dicts SO
#          com os campos que mudaram (nao a linha inteira).
#
#     v1.2.0 - Um modulo TAMBEM pode chamar registrar_item() com
#     tipo_mudanca='DELETE' para deixar rastro/historico de uma
#     exclusao definitiva (ex.: Excluir da Consulta Brincagem,
#     Sessao 076). Esse tipo NUNCA e desfazivel automaticamente -
#     ver bloqueio explicito dentro de buscar_operacao_desfazivel()
#     abaixo. E so um "diario de bordo" de quem excluiu o que e
#     quando, gravando a linha inteira como dados_antes.
#
#     FLUXO DE DESFAZER (rota /desfazer do modulo):
#       1. operacao, itens, erro = buscar_operacao_desfazivel(db,
#          id_operacao, id_usuario_logado, cargo_logado) - confere
#          permissao (quem fez OU Cargo permitido), janela de 24h,
#          se ja foi desfeita antes, E (v1.2.0) se algum item e uma
#          exclusao definitiva (tipo_mudanca='DELETE') - qualquer
#          um desses casos PARA AQUI, nao desfaz nada.
#       2. conflitos = verificar_conflitos(db, itens) - confere SE
#          o dado atual ainda bate com o que foi gravado
#          (dados_depois). Se houver qualquer conflito, PARA AQUI -
#          nao desfaz nada (Benedito, Sessao 045: "bloquear com
#          aviso, nunca sobrescrever").
#       3. Se passou nas 2 checagens: executar_desfazer(db,
#          operacao, itens, id_usuario_logado) - aplica os
#          UPDATEs/DELETEs de reversao e marca desfeito_em/
#          desfeito_por na operacao.
#
#     REGRA "SO A ULTIMA" (v1.3.0, Benedito, Sessao 082): alguns
#     modulos geram documento com NUMERACAO OFICIAL sequencial
#     (hoje: a Notificacao de Nascimento, NAS + 7 digitos). Desfazer
#     uma que nao seja a ULTIMA deixaria um buraco na sequencia, e a
#     Certificadora estranha buracos. Esses modulos ficam na lista
#     MODULOS_SO_ULTIMA: a operacao so pode ser desfeita se NAO
#     existir outra operacao do MESMO modulo, mais recente e ainda
#     nao desfeita. Desfeita a ultima, o proximo numero reaproveita o
#     dela (o numero sai do MAX da tabela do documento).
#     PENDENCIA FUTURA (combinada com Benedito): quando a Impressao
#     da Notificacao existir, Notificacao ja IMPRESSA (Certificadora
#     avisada) nao podera mais ser desfeita - a checagem entra em
#     buscar_operacao_desfazivel().
#
#     REGRAS DE NEGOCIO FECHADAS (Benedito, Sessao 045):
#       - JANELA_DESFAZER_HORAS = 24.
#       - CARGOS_PERMITIDOS = TITULAR, ADMINISTRADOR, ADMINISTRATIVO
#         (valores REAIS da coluna usuario_vinculo.cargo, tudo
#         maiusculo - confirmado por Benedito, nao GERAS/suposicao).
#       - Pode desfazer quem fez a operacao (id_usuario) OU quem
#         tem um dos Cargos permitidos - "nao expor quem cometeu o
#         erro se ele tiver condicao de corrigi-lo" (Benedito).
#
#     v1.0.0: Criacao do modulo (Sessao 045, 03/09/2026, 15:30 -03).
#     v1.1.0: Sessao 045 (03/09/2026, 17:00 -03) - BUG REAL em
#         producao, reportado por Benedito (Erro do Servidor Interno
#         ao clicar em Desfazer): _refletir_tabela() usava
#         db.get_bind() para a reflexao de tabela - isso devolve o
#         ENGINE, nao a conexao em uso, e o SQLAlchemy abre uma
#         CONEXAO NOVA/separada para refletir, que nunca recebeu o
#         "SET search_path TO produtor_NNNNN, public" executado por
#         get_db_produtor() (backend/utils/multitenant.py). A tabela
#         era procurada no schema errado - sqlalchemy.exc.
#         NoSuchTableError: tb_3008_brincos_saida. Corrigido trocando
#         para db.connection() - reaproveita a MESMA conexao/
#         transacao ja em uso pela sessao, que ja tem o search_path
#         certo. Bug reproduzido e a correcao validada com Postgres
#         real (nao so SQLite, que nao tem search_path) antes desta
#         entrega - fluxo completo salvar+desfazer testado de ponta a
#         ponta em schema separado, replicando o cenario exato de
#         producao.
#     v1.2.0: Sessao 076 (21/09/2026, 10:00 -03) - Decisao de
#         Benedito (Opcao B): exclusao definitiva pode ser
#         registrada no Log de Operacoes como HISTORICO/AUDITORIA
#         (tipo_mudanca='DELETE'), mas NUNCA deve aparecer como
#         desfazivel - executar_desfazer()/_refletir_tabela() so
#         sabem reverter UPDATE e INSERT (nunca foram ensinados a
#         "reencarnar" uma linha apagada) e deixar passar batido
#         faria a tela de Desfazer MENTIR pro usuario: ele clicaria,
#         o sistema marcaria desfeito_em/desfeito_por como se tivesse
#         dado certo, mas a linha continuaria apagada. Bloqueio
#         adicionado em buscar_operacao_desfazivel() - 4a checagem,
#         ANTES de verificar_conflitos() - fecha essa porta para
#         QUALQUER modulo futuro que reusar este mecanismo, nao so
#         para a Consulta Brincagem.
#     v1.3.0: Sessao 082 (29/09/2026, 17:05 -03) - 2 mudancas para
#         o Desfazer da Brincagem de Nascimento (decisao de Benedito:
#         "SIM, o Nascimento entra no Desfazer"):
#           - NOVA regra "so a ultima" (ver DESCRICAO): constante
#             MODULOS_SO_ULTIMA + 5a checagem em
#             buscar_operacao_desfazivel(), ANTES de
#             verificar_conflitos(). Qualquer modulo fora da lista
#             continua exatamente como era (ex.: Cancelamento de
#             Brincos).
#           - Os itens da operacao passam a ser lidos em ORDEM DE
#             REGISTRO (id crescente). executar_desfazer() ja os
#             percorria de tras para frente, mas a busca nao pedia
#             ordem - na pratica saia certa, sem garantia. A ordem
#             importa: a Notificacao (tb_4001_gta) so pode ser
#             apagada DEPOIS da linha de animais dela
#             (tb_4001_gta_animais, vinculo obrigatorio).
#         Nenhuma outra mudanca.
#     v1.4.0: Sessao 082 (29/09/2026, 20:05 -03) - Pacote 3A
#     v1.21.1: Sessao 113 (03/11/2026, 14:15 -03) - Desfazer da Morte tambem confere a Notificacao quando o animal foi somado a um MRT aberto (UPDATE do tb_2013); o UPDATE restaura a quantidade.  REVERSAO: .bak_antes_s113_mrt_aberto.
#         (Numero de Controle do Nascimento no brete):
#           - NOVA constante MODULOS_SO_HISTORICO: operacoes que
#             sao SO registro (auditoria) e nunca podem ser
#             desfeitas. Hoje: 'nascimento_controle' (Reserva,
#             Zerado e Liberacao do NAS - backend/utils/
#             gravacao_nascimento.py). Checagem nova em
#             buscar_operacao_desfazivel(), logo depois da
#             permissao.
#           - Regra "so a ultima" REFORCADA para a Notificacao de
#             Nascimento: alem de olhar a ordem das operacoes do
#             mesmo modulo (v1.3.0), agora olha a NUMERACAO real -
#             se existe algum NAS MAIOR (ex.: um Controle reservado
#             pelo brete depois do lancamento do escritorio),
#             desfazer abriria buraco, entao bloqueia. NOVA funcao
#             _existe_nas_maior_que_o_da_operacao().
#         Nenhuma outra mudanca (Cancelamento de Brincos, Consulta
#         Brincagem e demais continuam exatamente como eram).
#     v1.5.0: Sessao 084 (02/10/2026, 09:00 -03) - TRAVA DA NOTIFICACAO
#         IMPRESSA (pendencia combinada com Benedito): Notificacao de
#         Nascimento ja IMPRESSA (Certificadora avisada) nao pode mais
#         ser desfeita. NOVA funcao _notificacao_ja_impressa() consulta
#         tb_7020_notificacao_impressao (backend/models/tb_7020_
#         notificacao_impressao.py, gravada por backend/routers/
#         notificacao_nascimento.py na primeira impressao). Checagem nova
#         dentro do bloco MODULOS_SO_ULTIMA de buscar_operacao_
#         desfazivel(), ANTES da regra "so a ultima". Nenhuma outra
#         mudanca.
#     v1.6.0: Sessao 084 (02/10/2026, 11:30 -03) - INTEGRACAO DE ANIMAL DO
#         BRETE NA NOTIFICACAO (gravacao_nascimento.py v1.1.0): (a) NOVO
#         modulo so-historico 'nascimento_integracao' em MODULOS_SO_
#         HISTORICO (nunca desfazivel); (b) a Notificacao que RECEBEU
#         animal do brete tambem nao pode mais ser desfeita (o Desfazer
#         dela nao conhece esses animais) - NOVA funcao _notificacao_
#         recebeu_animal_do_brete(). Nenhuma outra mudanca.
#     v1.7.0: Sessao 084 (02/10/2026, 12:10 -03) - LANCAMENTO DO ESCRITORIO
#         EM NAS JA EXISTENTE (brincagem_nascimento.py v2.1.0): esse
#         lancamento nao cria numero novo (registra UPDATE, nao INSERT, da
#         tb_4001_gta), entao a trava "existe NAS de numero maior" deixa de
#         valer para ele - _existe_nas_maior_que_o_da_operacao() so
#         considera a operacao que CRIOU o NAS (INSERT). Continuam valendo
#         para ele: so a ultima operacao do modulo, Notificacao impressa
#         e Notificacao que recebeu animal do brete. Nenhuma outra mudanca.
#     v1.8.0: Sessao 094 (12/10/2026, 17:00 -03) - ENTRADA DE BRINCOS NO DESFAZER.
#         Modulo 'brincos_entrada': qualquer lote INTACTO pode ser desfeito (sem regra
#         "so a ultima"). Intacto = nenhum brinco do lote usado (status, RFID, brincagem,
#         reserva de GTA ou saida) e nenhuma linha em tb_3008 para o lote. Desfazer apaga
#         os brincos do lote (tb_7017) e depois o lote (tb_3007). O item de log e um unico
#         INSERT do lote; os brincos saem pela chave id_lote_entrada. NOVA funcao
#         _lote_de_brincos_intacto(). Os demais modulos nao mudam.
#         REVERSAO: devolver log_operacoes.py.bak_antes_entrada_desfazer.
#     v1.9.0: Sessao 094 (12/10/2026, 19:30 -03) - NAS POR PROPRIEDADE (decisao de Benedito):
#         a numeracao da Notificacao de Nascimento (NAS) passa a ser da PROPRIEDADE (dentro do
#         schema do Produtor), nao mais do Produtor inteiro: a primeira NAS de cada fazenda e a
#         NAS0000001. "So a ultima" e "existe NAS maior" passam a valer dentro da propriedade da operacao.
#         REVERSAO: devolver .bak_antes_nas_propriedade.
#     v1.10.0: Sessao 100 (19/10/2026, 18:20 -03) - SAIDAS DO ABATE NO LOG (decisao de Benedito): Vincular GTA,
#         Desvincular, troca de Data Embarque e Correcao do embarque gravam Log. Tres modulos novos em
#         MODULOS_SO_HISTORICO (aparecem em Operacoes Recentes e nunca sao desfeitos aqui; o "desfazer" do
#         vinculo e o botao Desvincular). Nenhuma outra mudanca.
#         REVERSAO: devolver .bak_antes_log_saidas_s100.
#     v1.11.0: Sessao 100 (19/10/2026, 20:40 -03) - Modulo 'saida_substituicao' (Substituicao de Animal) em MODULOS_SO_HISTORICO. Nenhuma outra mudanca.
#         REVERSAO: devolver .bak_antes_substituicao_s100.
#     v1.12.0: Sessao 101 (20/10/2026, 10:47 -03) - Modulo 'saida_comunicado' (Gerar Comunicado de Saida: baixa dos animais) em MODULOS_SO_HISTORICO. Nenhuma outra mudanca.
#         REVERSAO: devolver .bak_antes_comunicado_saida_s101.
#     v1.13.0: Sessao 102 (2026-10-21 12:35 -03) - Modulo saida_troca_comunicado entra em MODULOS_SO_HISTORICO (troca de animal depois do Comunicado; nao se desfaz).
#     v1.14.0: Sessao 103 (2026-10-22 08:25 -03) - Modulo saida_arquivo (Abate por Arquivo Texto) entra em MODULOS_SO_HISTORICO. Nenhuma outra mudanca.
#         REVERSAO: devolver .bak_antes_saida_arquivo_s103.
#     v1.15.0: Sessao 103 (2026-10-22 12:45 -03) - Modulos gta_saida_alterar e gta_saida_excluir (Alterar/Excluir GTA de Saida) entram em MODULOS_SO_HISTORICO. Nenhuma outra mudanca.
#         REVERSAO: devolver .bak_antes_gta_saida_s103.
#     v1.16.0: Sessao 104 (2026-10-23 10:15 -03) - DESFAZER SO O QUE NAO COMPROMETE (decisao de Benedito): (1) SO A ULTIMA da Propriedade: com qualquer operacao
#         mais recente nao desfeita (de qualquer modulo, inclusive so-historico), a operacao nao pode ser desfeita; (2) Brincagem Sequencial: nova checagem
#         _brincagem_sequencial_comprometida() - Comunicado de Entrada ja gerado, Embarque/Saida, nova pesagem, outra movimentacao, cancelamento/
#         reidentificacao/troca do brinco e ficha alterada depois. A tela de Operacoes Recentes esconde o que nao pode mais ser desfeito (operacoes_recentes.py 1.5.0).
#         Demais modulos: so a regra (1) por enquanto; refino modulo a modulo. REVERSAO: devolver .bak_antes_s104e.
#     v1.17.0: Sessao 104 (23/10/2026, 12:40 -03) - TRILHA DE AUDITORIA: modulos so-historico novos 'gta_manual' (GTA de Entrada lancada) e
#         'comunicado_entrada' (Comunicado de Entrada gerado); sem Desfazer. REVERSAO: .bak_antes_s104i.
#     v1.19.0: Sessao 108 (29/10/2026, 19:40 -03) - modulo 'saida_comunicado_externo' (Transferencia ENTRE PRODUTORES: a Entrada fica no schema de outro Produtor) entra em MODULOS_SO_HISTORICO. Nenhuma outra mudanca.
#     v1.21.0: Sessao 111 (01/11/2026) - modulo 'morte_notificacao' (Gerar Notificacao de Morte) entra em MODULOS_SO_HISTORICO. REVERSAO: .bak_antes_s111_notificacao.
#     v1.20.0: Sessao 111 (01/11/2026) - DESFAZER DA MORTE: modulo 'morte' (lancamento individual): so ate gerar a Notificacao (tb_2013.numero_comunicado vazio), animal sem outra
#         movimentacao e fora da tb_2001; a baixa da tb_2001 e reversivel (linha inteira no Log). As fotos (FK com cascata) somem junto. REVERSAO: .bak_antes_s111_morte.
#     v1.18.0: Sessao 104 (23/10/2026, 13:10 -03) - DESFAZER DO COMUNICADO DE SAIDA (decisao de Benedito): 'saida_comunicado' deixa de ser so-historico.
#         Regras: so a ultima da Propriedade (v1.16.0), dentro de 24h, Comunicado ainda ABERTO (nao impresso), e nenhum animal teve outra movimentacao
#         depois nem ja esta de volta na tb_2001 (_saida_comunicado_comprometida). A exclusao da tb_2001 da baixa e reversivel (linha inteira guardada no
#         Log): executar_desfazer() agora reinsere itens DELETE da tb_2001 (so deste modulo). REVERSAO: .bak_antes_s104j.
#     v1.22.0: Sessao 119 (09/11/2026, 18:40 -03) - DESFAZER DA TRANSFERENCIA (mesmo Produtor) E DA VENDA PARA COMPRADOR FORA DA BASE (decisao de Benedito, REGRA B):
#         (1) NAO vale mais "so a ultima operacao da Propriedade" para esses dois tipos; vale: o Comunicado e o de maior numero do Produtor+Propriedade+tipo (e, na Transferencia, a Entrada e a de maior numero da Propriedade de destino) e nenhum animal teve nada depois (movimentacao, pesagem, embarque/saida, cancelamento/troca de brinco, ficha alterada), com conferencia de contagem;
#         (2) Comunicado ja IMPRESSO nao impede (a correcao e interna); (3) a GTA volta a ficar sem Comunicado; (4) blockchain: tratar_desfazer() ja cancela o pendente e estorna o confirmado (mesmo id_operacao).
#         ABATE segue exatamente como era (v1.18.0). Venda/Posse COM destino na plataforma continuam so-historico. REVERSAO: .bak_antes_s119_desfazer_transf_venda.
#     v1.23.0: Sessao 121 (11/11/2026, 14:00 -03) - DESFAZER DA REIDENTIFICACAO: modulo 'reidentificacao' (a baixa da tb_2001 e reversivel); vale 'so a ultima da Propriedade';
#         bloqueia se o pedido ja foi ENVIADO, se o brinco perdido voltou, ou se o animal teve movimentacao/pesagem depois (_reidentificacao_comprometida).
#         Modulo 'reidentificacao_envio' (Marcar como enviado) entra em MODULOS_SO_HISTORICO. REVERSAO: .bak_antes_s121_reidentificacao.
#     v1.24.0: Sessao 121 (2026-11-11 14:30 -03) - Modulo 'reidentificacao_exclusao' (Excluir animal do pedido) entra em MODULOS_SO_HISTORICO; _reidentificacao_comprometida() tambem bloqueia o Desfazer do pedido inteiro quando a Notificacao ja foi gerada. REVERSAO: .bak_antes_s121_exclusao.
#     v1.25.0: Sessao 121 (2026-11-11 19:00 -03) - Modelo pendentes: _reidentificacao_comprometida so deixa desfazer o lancamento enquanto os animais estao pendentes (sem Notificacao); modulo 'reidentificacao_notificacao' entra em MODULOS_SO_HISTORICO. REVERSAO: .bak_antes_s121_pendentes.
#     v1.27.0: Sessao 132 (2026-11-18 20:30 -03) - Modulo 'bnd_fazenda' (Correcao BND/Fazenda pela Consiste) entra em MODULOS_SO_HISTORICO: so registra quem corrigiu, quando e quantos; nao se desfaz. REVERSAO: .bak_antes_s132_bnd.
#     v1.26.0: Sessao 122 (2026-11-12 13:55 -03) - Auditoria Etapa 1: (a) Desfazer da Morte nao apaga mais os arquivos das fotos antes do commit - executar_desfazer devolve os nomes e a rota apaga depois do commit; (b) buscar_operacao_desfazivel ganha travar=True (trava de linha contra duplo clique). REVERSAO: .bak_antes_s122_etapa1.
#     v1.26.1: Sessao 122 (2026-11-12 14:25 -03) - Auditoria Etapa 1: mensagens do Desfazer (nao encontrada, ja desfeita, sem permissao) agora dizem o que aconteceu e o que fazer / quem pode. REVERSAO: .bak_antes_s122_msgs.
#     v1.26.2: Sessao 122 (2026-11-12 14:50 -03) - Auditoria Etapa 1 (item 3): Desfazer bloqueia operacao com UPDATE sem dados_antes (antes ignorava e marcava como desfeita). REVERSAO: .bak_antes_s122_trava.
# =========================================================

from datetime import datetime, timedelta, date, time
from decimal import Decimal

from sqlalchemy import Table, MetaData, select, func, DateTime as _SADateTime, Date as _SADate, Time as _SATime, Numeric as _SANumeric
from sqlalchemy.exc import NoSuchTableError   # v1.16.0

from backend.models.tb_4001_gta import Gta
from backend.models.tb_log_operacoes import LogOperacao
from backend.models.tb_log_operacoes_itens import LogOperacaoItem
from backend.models.tb_7020_notificacao_impressao import NotificacaoImpressao


# -------------------------------------------------------
# Constantes do mecanismo (regras de negocio fechadas com
# Benedito, Sessao 045).
# -------------------------------------------------------
JANELA_DESFAZER_HORAS = 24
CARGOS_PERMITIDOS     = ('TITULAR', 'ADMINISTRADOR', 'ADMINISTRATIVO')

# v1.3.0 - modulos com numeracao oficial sequencial: so a ULTIMA
# operacao de cada um pode ser desfeita. Chave = valor da coluna
# modulo (tb_log_operacoes); valor = nome do documento, usado na
# mensagem ao usuario.
MODULOS_SO_ULTIMA = {
    'brincagem_nascimento': 'Notificação de Nascimento',
}

# v1.4.0 - modulos cujas operacoes sao SO historico/auditoria:
# aparecem na tela de Operacoes Recentes, mas nunca podem ser
# desfeitas. Chave = coluna modulo; valor = texto da mensagem.
MODULOS_SO_HISTORICO = {
    'bnd_fazenda': 'registro da Correção BND/Fazenda feita pela Consiste (a BND prevalece); não se desfaz',   # v1.27.0
    'reidentificacao_exclusao': 'registro da exclusão de um animal pendente de Notificação da Reidentificação; os demais se excluem um a um na Consulta',   # v1.24.0
    'reidentificacao_notificacao': 'registro da geração da Notificação de Reidentificação; os animais não voltam depois dela',   # v1.25.0
    'reidentificacao_envio': 'registro de que o Pedido de Reidentificação foi marcado como enviado à Certificadora; não se desfaz',   # v1.23.0
    'saida_comunicado_externo': 'registro do Comunicado de Transferência para OUTRO Produtor (a Entrada ficou no schema dele); não se desfaz aqui',   # v1.19.0
    'gta_manual': 'registro do lançamento de uma GTA de Entrada (GTA Manual); não se desfaz',   # v1.17.0
    'comunicado_entrada': 'registro do Comunicado de Entrada gerado (animais da GTA passam a comunicados); não se desfaz',   # v1.17.0
    'nascimento_controle': 'registro do Número de Controle (reserva, zerado ou liberação)',
    'nascimento_integracao': 'registro de animal lido no brete e integrado a uma Notificação',   # v1.6.0
    'saida_vincular': 'registro do vínculo (ou desvínculo) de uma GTA de saída aos animais do embarque; o vínculo se desfaz pelo botão Desvincular',   # v1.10.0
    'saida_data_embarque': 'registro da troca de Data Embarque do embarque',   # v1.10.0
    'saida_liberar': 'registro dos animais liberados (leitura apagada) do embarque; não se desfaz (para voltar, leia o animal de novo)',   # Sessao 107
    'saida_correcao': 'registro da correção de Data Embarque e Peso do embarque',   # v1.10.0
    'saida_substituicao': 'registro da substituição de um animal do embarque por outro',   # v1.11.0
    'gta_saida_alterar': 'registro da alteração de uma GTA de Saída (e das cópias no Comunicado, quando havia); não se desfaz (para voltar, altera-se de novo)',   # v1.15.0
    'gta_saida_excluir': 'registro da exclusão de uma GTA de Saída (linha inteira guardada como prova de quem excluiu); não se desfaz (para voltar, cadastra-se a GTA de novo)',   # v1.15.0
    'morte_notificacao': 'registro da Notificação de Morte (Anexo XXII) gerada; não se desfaz (depois dela as mortes seguem para a certificadora)',   # v1.21.0 - Sessao 111
    'saida_arquivo': 'registro do Abate por Arquivo Texto: animais gravados no Embarque; não se desfaz aqui (para voltar, exclua a leitura pela Consulta Embarque)',   # v1.14.0
    'saida_troca_comunicado': 'registro da troca de um animal do Comunicado de Saída por outro; não se desfaz (para voltar, faz-se outra troca)',   # v1.13.0
}

_MODULO_INTEGRACAO = 'nascimento_integracao'   # v1.6.0

# v1.8.0 - Entrada de Brincos: tabela do lote e dos brincos.
_MODULO_ENTRADA_BRINCOS = 'brincos_entrada'
_TABELA_LOTE_BRINCOS    = 'tb_3007_brincos_entrada'
_TABELA_BRINCOS         = 'tb_7017_entrada_brincos_rfid'
_TABELA_SAIDA_BRINCOS   = 'tb_3008_brincos_saida'

# v1.4.0 - identificacao do NAS na tb_4001_gta (mesmos valores de
# backend/utils/gravacao_nascimento.py - repetidos aqui de proposito
# para este utilitario generico nao importar um modulo de negocio).
_SERIE_NAS          = 'NAS'
_TIPO_MOVIMENTO_NAS = 'NASCTO-DESMAME'


# -------------------------------------------------------
# Funcao auxiliar (v1.4.0): a operacao gravou um NAS (tb_4001_gta)
# e existe outro NAS MAIOR no schema? Se existir, desfazer esta
# deixaria buraco na numeracao oficial. Operacao sem NAS -> False.
# v1.7.0 - so conta quando a operacao CRIOU o NAS (INSERT); lancamento
# que entrou em NAS existente (UPDATE) nao cria numero, nao abre buraco.
# -------------------------------------------------------
def _existe_nas_maior_que_o_da_operacao(db, itens):
    for item in itens:
        if item.tabela != 'tb_4001_gta':
            continue
        if item.tipo_mudanca != 'INSERT':   # v1.7.0
            continue
        gta = db.get(Gta, item.id_registro)
        if gta is None or gta.serie_gta != _SERIE_NAS:
            continue
        maior = (
            db.query(Gta.id)
            .filter(
                Gta.id_propriedade == gta.id_propriedade,   # v1.9.0 - fila da PROPRIEDADE
                Gta.tipo_movimento == _TIPO_MOVIMENTO_NAS,
                Gta.serie_gta == _SERIE_NAS,
                Gta.numero_gta_sequencial > gta.numero_gta_sequencial,
            )
            .first()
        )
        if maior is not None:
            return True
    return False


# -------------------------------------------------------
# Funcao auxiliar (v1.5.0): a operacao gravou uma Notificacao
# (tb_4001_gta) que ja foi IMPRESSA? Impressa = Certificadora avisada,
# nao pode mais ser desfeita.
# -------------------------------------------------------
def _notificacao_ja_impressa(db, itens):
    for item in itens:
        if item.tabela != 'tb_4001_gta':
            continue
        impressa = db.query(NotificacaoImpressao.id).filter_by(id_gta=item.id_registro).first()
        if impressa is not None:
            return True
    return False


# -------------------------------------------------------
# Funcao auxiliar (v1.6.0): a Notificacao das operacoes ja recebeu
# animal lido no brete (integracao)? Entao o Desfazer dela nao
# enxerga todos os animais - bloqueia.
# -------------------------------------------------------
def _notificacao_recebeu_animal_do_brete(db, itens):
    for item in itens:
        if item.tabela != 'tb_4001_gta':
            continue
        achou = (
            db.query(LogOperacaoItem.id)
            .join(LogOperacao, LogOperacao.id == LogOperacaoItem.id_operacao)
            .filter(
                LogOperacao.modulo == _MODULO_INTEGRACAO,
                LogOperacaoItem.tabela == 'tb_4001_gta',
                LogOperacaoItem.id_registro == item.id_registro,
            )
            .first()
        )
        if achou is not None:
            return True
    return False


# -------------------------------------------------------
# Funcao auxiliar (v1.8.0): o lote de brincos esta INTACTO? Retorna
# None se sim, ou a mensagem de motivo se algum brinco ja foi usado.
# Usado (qualquer um) = status preenchido, RFID, data de brincagem,
# reserva de GTA ou saida; ou ha linha em tb_3008 para o lote.
# -------------------------------------------------------
def _lote_de_brincos_intacto(db, id_lote):
    brincos  = _refletir_tabela(db, _TABELA_BRINCOS)
    saidas   = _refletir_tabela(db, _TABELA_SAIDA_BRINCOS)
    c        = brincos.c

    usados = db.execute(
        select(c.id).where(
            c.id_lote_entrada == id_lote,
            (c.status.isnot(None)) | (c.rfid.isnot(None))
            | (c.data_brincagem.isnot(None)) | (c.reservado_id_gta.isnot(None))
            | (c.saida_data.isnot(None)),
        ).limit(1)
    ).first()
    if usados is not None:
        return 'Há brincos deste lote já utilizados (brincagem, reserva, saída ou cancelamento).'

    com_saida = db.execute(
        select(saidas.c.id).where(saidas.c.id_lote_entrada == id_lote).limit(1)
    ).first()
    if com_saida is not None:
        return 'Há saída de brincos registrada para este lote.'
    return None


# -------------------------------------------------------
# Funcao (v1.16.0): a Brincagem Sequencial desta operacao esta COMPROMETIDA? (decisao de Benedito, S104: se desfazer
# pode quebrar algo que veio depois, o Desfazer some da lista). Retorna a mensagem do motivo, ou None se esta tudo intacto.
# Confere, para os animais (SISBOV) criados pela operacao:
#   1. o Comunicado de Entrada da GTA ja foi gerado (numero_comunicado)  - o numero do Comunicado prevalece;
#   2. ja existe leitura/Embarque (tb_2020) ou Saida (tb_2002) do animal;
#   3. ja existe nova pesagem (tb_4003, sequencia maior que 1) ou outra movimentacao alem da Entrada (tb_2017);
#   4. o brinco entrou em cancelamento, reidentificacao, perda ou troca de elemento (tb_6004, 6006, 6008, 6013);
#   5. a ficha do animal (tb_2001, tb_2017, tb_7002) foi alterada depois (atualizado_em bem depois do criado_em).
# Tabela que nao existe no schema = nao da para conferir = BLOQUEIA (lado seguro).
# -------------------------------------------------------
_MARGEM_ALTERACAO_SEGUNDOS = 5
_TABELAS_FICHA_BRINCAGEM   = ('tb_2001', 'tb_2017_movimentacoes', 'tb_7002_pia')


def _sisbovs_da_operacao(itens):
    sisbovs = set()
    for item in itens:
        if item.tipo_mudanca == 'INSERT' and item.tabela in _TABELAS_FICHA_BRINCAGEM + ('tb_4003_pesos',):
            sisbov = (item.dados_depois or {}).get('sisbov')
            if sisbov:
                sisbovs.add(str(sisbov))
    return sorted(sisbovs)


def _brincagem_sequencial_comprometida(db, itens):
    try:
        # ---- 1. Comunicado de Entrada ja gerado ----
        for item in itens:
            if item.tabela == 'tb_4001_gta':
                gta = db.get(Gta, item.id_registro)
                if gta is not None and gta.numero_comunicado is not None:
                    return f'O Comunicado de Entrada desta GTA já foi gerado (nº {gta.numero_comunicado}).'

        sisbovs = _sisbovs_da_operacao(itens)
        ids_mov = [i.id_registro for i in itens if i.tabela == 'tb_2017_movimentacoes' and i.tipo_mudanca == 'INSERT']

        for inicio in range(0, len(sisbovs), 500):
            lote = sisbovs[inicio:inicio + 500]

            # ---- 2. Embarque / Saida ----
            for nome in ('tb_2020_embarque', 'tb_2002_saida_animais'):
                t = _refletir_tabela(db, nome)
                if db.execute(select(t.c.id).where(t.c.sisbov.in_(lote)).limit(1)).first() is not None:
                    return 'Já existe leitura de Embarque ou Saída de animal desta Brincagem.'

            # ---- 3. Nova pesagem / outra movimentacao ----
            pesos = _refletir_tabela(db, 'tb_4003_pesos')
            if db.execute(select(pesos.c.id).where(pesos.c.sisbov.in_(lote), pesos.c.sequencia > 1).limit(1)).first() is not None:
                return 'Já existe nova pesagem de animal desta Brincagem.'
            mov = _refletir_tabela(db, 'tb_2017_movimentacoes')
            consulta_mov = select(mov.c.id).where(mov.c.sisbov.in_(lote))
            if ids_mov:
                consulta_mov = consulta_mov.where(mov.c.id.notin_(ids_mov))
            if db.execute(consulta_mov.limit(1)).first() is not None:
                return 'Já existe outra movimentação de animal desta Brincagem.'

            # ---- 4. Cancelamento / reidentificacao / perda / troca de elemento ----
            for nome, colunas in (('tb_6004_re_id_elementos_itens', ('codigo_sisbov',)),
                                  ('tb_6006_reidentificacao_com_baixa_itens', ('sisbov_antigo', 'sisbov_novo')),
                                  ('tb_6008_perda_saida_estoque_itens', ('sisbov_atribuido',)),
                                  ('tb_6013_cancelamento_brinco_itens', ('codigo_sisbov',))):
                t = _refletir_tabela(db, nome)
                for coluna in colunas:
                    if db.execute(select(t.c.id).where(t.c[coluna].in_(lote)).limit(1)).first() is not None:
                        return 'Brinco de animal desta Brincagem já foi cancelado, reidentificado ou trocado.'

        # ---- 5. Ficha alterada depois ----
        for nome in _TABELAS_FICHA_BRINCAGEM:
            ids = [i.id_registro for i in itens if i.tabela == nome and i.tipo_mudanca == 'INSERT']
            for inicio in range(0, len(ids), 500):
                t = _refletir_tabela(db, nome)
                linhas = db.execute(
                    select(t.c.criado_em, t.c.atualizado_em).where(t.c.id.in_(ids[inicio:inicio + 500]))
                ).all()
                for criado, atualizado in linhas:
                    if criado and atualizado and (atualizado - criado).total_seconds() > _MARGEM_ALTERACAO_SEGUNDOS:
                        return 'A ficha de animal desta Brincagem foi alterada depois.'
    except NoSuchTableError:
        return 'Não foi possível conferir tudo o que veio depois desta operação.'
    return None


# -------------------------------------------------------
# Funcao: registrar_operacao() - cria o "recibo" (tb_log_operacoes)
# de uma nova operacao. Deve ser chamada DENTRO da mesma sessao/
# transacao (db) do modulo que esta gravando, ANTES dos itens.
# Retorna o id da operacao (precisa de flush para existir antes
# do commit final da transacao do modulo chamador).
# -------------------------------------------------------
_MODULO_SAIDA_COMUNICADO = 'saida_comunicado'   # v1.18.0
_MODULO_MORTE = 'morte'                         # v1.20.0 - lancamento da Morte (baixa na hora)
_MODULO_REIDENTIFICACAO = 'reidentificacao'     # v1.23.0 - Reidentificacao (brinco perdido -> brinco novo)


def _morte_comprometida(db, itens):
    """v1.20.0 - Morte: a Notificacao ja foi gerada, o animal ja voltou para a tb_2001 ou teve outra movimentacao depois? Texto do motivo ou None."""
    try:
        ids_ctrl = [i.id_registro for i in itens if i.tabela == 'tb_2013_com_morte' and i.tipo_mudanca in ('INSERT', 'UPDATE')]   # v1.21.1: UPDATE = animal somado a um MRT aberto
        if ids_ctrl:
            t = _refletir_tabela(db, 'tb_2013_com_morte')
            for controle, numero in db.execute(select(t.c.controle, t.c.numero_comunicado).where(t.c.id.in_(ids_ctrl))).all():
                if numero is not None:
                    return (f'A Notificação de Morte nº {int(numero):06d} já foi gerada: depois dela a morte (Controle MRT{int(controle):06d}) '
                            'segue para a certificadora e não volta.')

        t_ativos = _refletir_tabela(db, 'tb_2001')
        for item in itens:
            if item.tabela == 'tb_2001' and item.tipo_mudanca == 'DELETE':
                sisbov = (item.dados_antes or {}).get('sisbov')
                if sisbov and db.execute(select(t_ativos.c.id).where(t_ativos.c.sisbov == sisbov)).first() is not None:
                    return f'O animal {sisbov} já está de volta na Propriedade.'

        t_mov = _refletir_tabela(db, 'tb_2017_movimentacoes')
        for item in itens:
            if item.tabela == 'tb_2017_movimentacoes' and item.tipo_mudanca == 'INSERT':
                sisbov = (item.dados_depois or {}).get('sisbov')
                if sisbov and db.execute(
                    select(t_mov.c.id).where(t_mov.c.sisbov == sisbov, t_mov.c.id > item.id_registro)
                ).first() is not None:
                    return f'O animal {sisbov} teve outra movimentação depois da morte.'
    except NoSuchTableError:
        return 'Não foi possível conferir tudo o que veio depois desta operação.'
    return None


def _reidentificacao_comprometida(db, itens):
    """v1.23.0 - Reidentificacao: a Notificacao ja foi gerada, o brinco perdido voltou, ou algum animal teve movimentacao / pesagem depois? Texto do motivo ou None."""
    try:
        # v1.25.0 - so desfaz o lancamento enquanto os animais estao PENDENTES (id_pedido vazio): depois da Notificacao gerada nao volta
        ids_linhas = [i.id_registro for i in itens if i.tabela == 'tb_6006_reidentificacao_com_baixa_itens' and i.tipo_mudanca == 'INSERT']
        if ids_linhas:
            t = _refletir_tabela(db, 'tb_6006_reidentificacao_com_baixa_itens')
            for (id_pedido,) in db.execute(select(t.c.id_pedido).where(t.c.id.in_(ids_linhas))).all():
                if id_pedido is not None:
                    return f'A Notificação {int(id_pedido):06d} já foi gerada com estes animais e eles não voltam.'

        t_ativos = _refletir_tabela(db, 'tb_2001')
        for item in itens:
            if item.tabela == 'tb_2001' and item.tipo_mudanca == 'DELETE':
                sisbov = (item.dados_antes or {}).get('sisbov')
                if sisbov and db.execute(select(t_ativos.c.id).where(t_ativos.c.sisbov == sisbov)).first() is not None:
                    return f'O brinco {sisbov} já está de volta na Propriedade.'
            if item.tabela == 'tb_2001' and item.tipo_mudanca == 'INSERT':
                if db.execute(select(t_ativos.c.id).where(t_ativos.c.id == item.id_registro)).first() is None:
                    sisbov = (item.dados_depois or {}).get('sisbov')
                    return f'O animal {sisbov} (brinco novo) já não está na Propriedade.'

        t_mov = _refletir_tabela(db, 'tb_2017_movimentacoes')
        for item in itens:
            if item.tabela == 'tb_2017_movimentacoes' and item.tipo_mudanca == 'INSERT':
                sisbov = (item.dados_depois or {}).get('sisbov')
                if sisbov and db.execute(
                    select(t_mov.c.id).where(t_mov.c.sisbov == sisbov, t_mov.c.id > item.id_registro)
                ).first() is not None:
                    return f'O animal {sisbov} teve outra movimentação depois da Reidentificação.'

        ids_peso = [i.id_registro for i in itens if i.tabela == 'tb_4003_pesos' and i.tipo_mudanca == 'UPDATE']
        novos = [(i.dados_depois or {}).get('sisbov') for i in itens if i.tabela == 'tb_2001' and i.tipo_mudanca == 'INSERT']
        novos = [n for n in novos if n]
        if novos:
            t_peso = _refletir_tabela(db, 'tb_4003_pesos')
            consulta = select(t_peso.c.id).where(t_peso.c.sisbov.in_(novos))
            if ids_peso:
                consulta = consulta.where(~t_peso.c.id.in_(ids_peso))
            if db.execute(consulta).first() is not None:
                return 'Um dos animais foi pesado depois da Reidentificação.'
    except NoSuchTableError:
        return 'Não foi possível conferir tudo o que veio depois desta operação.'
    return None


def _saida_comunicado_comprometida(db, itens):
    """v1.18.0 - Comunicado de Saida: ja foi impresso, ou algum animal teve outra movimentacao / ja voltou para a tb_2001? Texto do motivo ou None."""
    try:
        ids_com = [i.id_registro for i in itens if i.tabela == 'tb_2011_com_saidas' and i.tipo_mudanca == 'INSERT']
        if ids_com:
            t = _refletir_tabela(db, 'tb_2011_com_saidas')
            for numero, status, data_envio, impresso_em in db.execute(
                select(t.c.numero_comunicado, t.c.status, t.c.data_envio, t.c.impresso_em).where(t.c.id.in_(ids_com))
            ).all():
                if str(status or '').upper() != 'ABERTO' or data_envio is not None or impresso_em is not None:
                    return (f'O Comunicado nº {numero} já foi impresso: depois de impresso ele segue para a certificadora e não volta.')

        t_ativos = _refletir_tabela(db, 'tb_2001')
        for item in itens:
            if item.tabela == 'tb_2001' and item.tipo_mudanca == 'DELETE':
                sisbov = (item.dados_antes or {}).get('sisbov')
                if sisbov and db.execute(select(t_ativos.c.id).where(t_ativos.c.sisbov == sisbov)).first() is not None:
                    return f'O animal {sisbov} já está de volta na Propriedade (troca de animal depois do Comunicado).'

        t_mov = _refletir_tabela(db, 'tb_2017_movimentacoes')
        for item in itens:
            if item.tabela == 'tb_2017_movimentacoes' and item.tipo_mudanca == 'INSERT':
                sisbov = (item.dados_depois or {}).get('sisbov')
                if sisbov and db.execute(
                    select(t_mov.c.id).where(t_mov.c.sisbov == sisbov, t_mov.c.id > item.id_registro)
                ).first() is not None:
                    return f'O animal {sisbov} teve outra movimentação depois do Comunicado.'
    except NoSuchTableError:
        return 'Não foi possível conferir tudo o que veio depois desta operação.'
    return None


# -------------------------------------------------------
# v1.22.0 - REGRA B (Benedito, 09/11/2026): Desfazer do Comunicado de TRANSFERENCIA (mesmo Produtor) e de VENDA para comprador FORA da base.
# So desfaz se, ao mesmo tempo:
#   1. o Comunicado e o de MAIOR numero do Produtor + Propriedade + tipo (nao deixa buraco; o numero volta sozinho, pois vem do MAX);
#   2. na Transferencia, a Entrada tambem e a de maior numero da Propriedade de destino (tipo Transferencia);
#   3. a conta bate (animais do Comunicado = animais do registro = linhas do destino);
#   4. nenhum animal teve nada DEPOIS: outra movimentacao, pesagem, leitura de embarque/saida, cancelamento/troca de brinco,
#      ficha do destino alterada, ou voltou para a Propriedade.
# Comunicado ja impresso NAO impede. Tabela que nao existe = nao da para conferir = BLOQUEIA (lado seguro).
# -------------------------------------------------------
_TIPOS_SAIDA_REGRA_B = {'TRANSFER': 'Transferência', 'VENDA': 'Venda'}


def _tipo_saida_regra_b(itens):
    """v1.22.0 - tipo (TRANSFER / VENDA) se a operacao e um Comunicado desses tipos; None para Abate e demais."""
    for item in itens:
        if item.tabela == 'tb_2011_com_saidas' and item.tipo_mudanca == 'INSERT':
            tipo = str((item.dados_depois or {}).get('tipo_saida') or '').upper()
            return tipo if tipo in _TIPOS_SAIDA_REGRA_B else None
    return None


def _saida_transfer_venda_comprometida(db, operacao, itens, tipo):
    """v1.22.0 - Transferencia / Venda (comprador fora da base): algo impede o Desfazer? Texto do motivo ou None."""
    nome = _TIPOS_SAIDA_REGRA_B[tipo]
    try:
        # ---- 1. Comunicado de Saida: o de maior numero (Produtor + Propriedade + tipo) ----
        ids_com = [i.id_registro for i in itens if i.tabela == 'tb_2011_com_saidas' and i.tipo_mudanca == 'INSERT']
        t_com = _refletir_tabela(db, 'tb_2011_com_saidas')
        linhas_com = db.execute(
            select(t_com.c.numero_comunicado, t_com.c.id_propriedade_origem, t_com.c.qtd_animais).where(t_com.c.id.in_(ids_com))
        ).all()
        if not ids_com or len(linhas_com) != len(ids_com):
            return 'O Comunicado desta operação não foi encontrado no banco.'
        numero, id_prop = linhas_com[0][0], linhas_com[0][1]
        total_esperado = sum(int(l[2] or 0) for l in linhas_com)
        if db.execute(select(t_com.c.id).where(t_com.c.id_propriedade_origem == id_prop, t_com.c.tipo_saida == tipo,
                                              t_com.c.numero_comunicado > numero).limit(1)).first() is not None:
            return (f'Já existe Comunicado de {nome} com número maior que o nº {int(numero):06d}: '
                    'desfazer deixaria um buraco na numeração.')

        # ---- 2. Comunicado de Entrada (Transferencia): o de maior numero da Propriedade de destino ----
        ids_ent = [i.id_registro for i in itens if i.tabela == 'tb_2012_com_entrada' and i.tipo_mudanca == 'INSERT']
        if ids_ent:
            t_ent = _refletir_tabela(db, 'tb_2012_com_entrada')
            linhas_ent = db.execute(
                select(t_ent.c.numero_comunicado, t_ent.c.id_propriedade_destino, t_ent.c.tipo_entrada).where(t_ent.c.id.in_(ids_ent))
            ).all()
            if len(linhas_ent) != len(ids_ent):
                return 'O Comunicado de Entrada desta operação não foi encontrado no banco.'
            for num_e, id_dest, tipo_e in linhas_ent:
                if db.execute(select(t_ent.c.id).where(t_ent.c.id_propriedade_destino == id_dest, t_ent.c.tipo_entrada == tipo_e,
                                                      t_ent.c.numero_comunicado > num_e).limit(1)).first() is not None:
                    return (f'Já existe Comunicado de Entrada de {nome} com número maior que o nº {int(num_e):06d} '
                            'na Propriedade de destino: desfazer deixaria um buraco na numeração.')

        # ---- 3. A conta bate ----
        sisbovs = sorted({str((i.dados_depois or {}).get('sisbov')) for i in itens
                          if i.tabela == 'tb_2002_saida_animais' and i.tipo_mudanca == 'INSERT' and (i.dados_depois or {}).get('sisbov')})
        if not sisbovs or len(sisbovs) != total_esperado:
            return (f'A conta não bate: o Comunicado diz {total_esperado} animal(is) e o registro da operação tem {len(sisbovs)}. '
                    'Nada foi desfeito, por segurança.')
        ids_dest = [i.id_registro for i in itens if i.tabela == 'tb_2001' and i.tipo_mudanca == 'INSERT']   # animais criados no destino (Transferencia)
        if ids_dest and len(ids_dest) != len(sisbovs):
            return (f'A conta não bate: {len(sisbovs)} animal(is) saíram, mas o registro tem {len(ids_dest)} no destino. '
                    'Nada foi desfeito, por segurança.')
        ids_saida_op = [i.id_registro for i in itens if i.tabela == 'tb_2002_saida_animais' and i.tipo_mudanca == 'INSERT']
        mov_op = {}   # sisbov -> maior id da tb_2017 gravado POR ESTA operacao
        for i in itens:
            if i.tabela == 'tb_2017_movimentacoes' and i.tipo_mudanca == 'INSERT':
                s = str((i.dados_depois or {}).get('sisbov') or '')
                if s:
                    mov_op[s] = max(mov_op.get(s, 0), i.id_registro)

        # ---- 4. Nenhum animal teve nada depois ----
        t_ativos = _refletir_tabela(db, 'tb_2001')
        t_mov = _refletir_tabela(db, 'tb_2017_movimentacoes')
        t_emb = _refletir_tabela(db, 'tb_2020_embarque')
        t_sai = _refletir_tabela(db, 'tb_2002_saida_animais')
        t_peso = _refletir_tabela(db, 'tb_4003_pesos')
        achados_dest = set()
        for inicio in range(0, len(sisbovs), 500):
            lote = sisbovs[inicio:inicio + 500]

            # 4.1 o animal esta so onde deveria: na Transferencia, so na linha criada pelo destino; na Venda, em lugar nenhum
            for id_a, sisbov_a, criado, atualizado in db.execute(
                select(t_ativos.c.id, t_ativos.c.sisbov, t_ativos.c.criado_em, t_ativos.c.atualizado_em).where(t_ativos.c.sisbov.in_(lote))
            ).all():
                if id_a not in ids_dest:
                    return f'O animal {sisbov_a} já está de volta na Propriedade.'
                achados_dest.add(id_a)
                if criado and atualizado and (atualizado - criado).total_seconds() > _MARGEM_ALTERACAO_SEGUNDOS:
                    return f'A ficha do animal {sisbov_a} foi alterada depois da {nome}.'

            # 4.2 nenhuma movimentacao nova
            for sisbov_m, maior in db.execute(
                select(t_mov.c.sisbov, func.max(t_mov.c.id)).where(t_mov.c.sisbov.in_(lote)).group_by(t_mov.c.sisbov)
            ).all():
                if maior > mov_op.get(str(sisbov_m), 0):
                    return f'O animal {sisbov_m} teve outra movimentação depois da {nome}.'

            # 4.3 nenhuma leitura nova de embarque / saida e nenhuma pesagem nova
            if db.execute(select(t_emb.c.id).where(t_emb.c.sisbov.in_(lote), t_emb.c.criado_em > operacao.criado_em).limit(1)).first() is not None:
                return f'Há animal desta {nome} lido em um novo Embarque.'
            consulta_sai = select(t_sai.c.id).where(t_sai.c.sisbov.in_(lote), t_sai.c.criado_em > operacao.criado_em)
            if ids_saida_op:
                consulta_sai = consulta_sai.where(t_sai.c.id.notin_(ids_saida_op))
            if db.execute(consulta_sai.limit(1)).first() is not None:
                return f'Há animal desta {nome} com outra saída registrada depois.'
            if db.execute(select(t_peso.c.id).where(t_peso.c.sisbov.in_(lote), t_peso.c.criado_em > operacao.criado_em).limit(1)).first() is not None:
                return f'Há animal desta {nome} com nova pesagem depois.'

            # 4.4 nenhum brinco cancelado / reidentificado / perdido / trocado depois
            for nome_t, colunas in (('tb_6004_re_id_elementos_itens', ('codigo_sisbov',)),
                                    ('tb_6006_reidentificacao_com_baixa_itens', ('sisbov_antigo', 'sisbov_novo')),
                                    ('tb_6008_perda_saida_estoque_itens', ('sisbov_atribuido',)),
                                    ('tb_6013_cancelamento_brinco_itens', ('codigo_sisbov',))):
                t = _refletir_tabela(db, nome_t)
                for coluna in colunas:
                    if db.execute(select(t.c.id).where(t.c[coluna].in_(lote), t.c.criado_em > operacao.criado_em).limit(1)).first() is not None:
                        return f'Brinco de animal desta {nome} foi cancelado, reidentificado ou trocado depois.'

        # 4.5 todos os animais do destino ainda estao la
        if set(ids_dest) != achados_dest:
            return f'Algum animal desta {nome} não está mais na Propriedade de destino.'
    except NoSuchTableError:
        return 'Não foi possível conferir tudo o que veio depois desta operação.'
    return None


def _valor_do_log(coluna, valor):
    """v1.18.0 - valor guardado no Log (JSON) -> valor do tipo da coluna (data, hora, numero)."""
    if valor is None:
        return None
    tipo = coluna.type
    if isinstance(tipo, _SADateTime):
        return datetime.fromisoformat(valor)
    if isinstance(tipo, _SADate):
        return date.fromisoformat(valor)
    if isinstance(tipo, _SATime):
        return time.fromisoformat(valor)
    if isinstance(tipo, _SANumeric):
        return Decimal(valor)
    return valor


def registrar_operacao(db, id_usuario, id_propriedade, modulo, descricao):
    operacao = LogOperacao(
        id_usuario=id_usuario,
        id_propriedade=id_propriedade,
        modulo=modulo,
        descricao=descricao,
    )
    db.add(operacao)
    db.flush()  # garante que operacao.id existe, sem commitar a transacao toda
    return operacao.id


# -------------------------------------------------------
# Funcao: registrar_item() - grava 1 linha de mudanca dentro de
# uma operacao ja registrada. dados_antes/dados_depois devem ser
# dicts SO com os campos que mudaram (nunca a linha inteira) -
# evita gravar informacao irrelevante e deixa o "desfazer" mais
# preciso.
#
# EXCECAO (v1.2.0): para tipo_mudanca='DELETE', dados_antes e a
# LINHA INTEIRA (snapshot de auditoria, nao "so o que mudou" -
# faz sentido, a linha inteira e o que muda) e dados_depois e
# sempre None (nao existe "depois" - a linha sumiu).
# -------------------------------------------------------
def registrar_item(db, id_operacao, tabela, id_registro, tipo_mudanca, dados_antes, dados_depois):
    item = LogOperacaoItem(
        id_operacao=id_operacao,
        tabela=tabela,
        id_registro=id_registro,
        tipo_mudanca=tipo_mudanca,
        dados_antes=dados_antes,
        dados_depois=dados_depois,
    )
    db.add(item)


# -------------------------------------------------------
# Funcao: buscar_operacao_desfazivel() - busca a operacao + itens
# e confere as regras de bloqueio (nesta ordem): ja foi desfeita
# antes? passou da janela de 24h? o usuario logado tem permissao
# (fez a operacao OU tem Cargo permitido)? a operacao inclui
# alguma exclusao definitiva (v1.2.0, nunca desfazivel)?
#
# v1.3.0: 5a checagem - modulos de MODULOS_SO_ULTIMA so desfazem a
# operacao mais recente (sem buraco na numeracao oficial).
#
# Retorna (operacao, itens, erro) - erro=None se pode prosseguir
# para a checagem de conflitos; caso contrario, operacao/itens
# vem como None e erro tem a mensagem amigavel para mostrar.
# -------------------------------------------------------
def buscar_operacao_desfazivel(db, id_operacao, id_usuario_logado, cargo_logado, travar=False):
    # v1.26.0 - travar=True (so no Desfazer de verdade): trava a linha da operacao ate o commit, para duplo clique nao desfazer 2x
    operacao = db.get(LogOperacao, id_operacao, with_for_update=True) if travar else db.get(LogOperacao, id_operacao)

    if not operacao:
        return None, None, 'Esta operação não foi encontrada. Atualize a lista de Operações Recentes e tente de novo. Se continuar, avise a Consiste.'

    if operacao.desfeito_em is not None:
        return None, None, 'Esta operação já foi desfeita (talvez o botão tenha sido clicado duas vezes). Não precisa fazer mais nada: confira o resultado em Operações Recentes.'

    prazo_limite = operacao.criado_em + timedelta(hours=JANELA_DESFAZER_HORAS)
    if datetime.now() > prazo_limite:
        return None, None, (
            f'O prazo de {JANELA_DESFAZER_HORAS}h para desfazer esta operação já passou.'
        )

    pode = (
        id_usuario_logado == operacao.id_usuario
        or (cargo_logado or '').upper() in CARGOS_PERMITIDOS
    )
    if not pode:
        return None, None, 'Você não tem permissão para desfazer esta operação. Só quem a fez, ou o Titular, o Administrador ou o Administrativo da fazenda, pode desfazer. Peça a um deles.'

    # v1.4.0 - operacao que e so historico (ex.: Reserva do Numero
    # de Controle) nunca e desfeita.
    texto_historico = MODULOS_SO_HISTORICO.get(operacao.modulo)
    if texto_historico:
        return None, None, (
            f'Esta operação é apenas o {texto_historico} e fica registrada como '
            f'histórico — não pode ser desfeita.'
        )

    # v1.3.0 - itens em ORDEM DE REGISTRO (id crescente): o
    # executar_desfazer() os percorre de tras para frente, entao a
    # ordem precisa ser a de gravacao (ver DESCRICAO v1.3.0).
    consulta_itens = db.query(LogOperacaoItem).filter_by(id_operacao=id_operacao)
    coluna_id_item = getattr(LogOperacaoItem, 'id', None)
    if coluna_id_item is not None:
        consulta_itens = consulta_itens.order_by(coluna_id_item.asc())
    itens = consulta_itens.all()

    # ---------------------------------------------------
    # v1.2.0 - Bloqueio de exclusao definitiva (Benedito,
    # Sessao 076, Opcao B): nunca deixar a tela de Desfazer
    # oferecer "reverter" algo que o mecanismo nao sabe
    # reverter de verdade - ver DESCRICAO do cabecalho.
    # ---------------------------------------------------
    # v1.26.2 - Auditoria Etapa 1: UPDATE sem o registro de 'como era antes' nao tem como ser revertido;
    # antes era ignorado em silencio e a operacao aparecia como desfeita. Agora bloqueia, com orientacao.
    if any(item.tipo_mudanca == 'UPDATE' and (not item.dados_antes) for item in itens):
        return None, None, (
            f'Esta operação não pode ser desfeita automaticamente: falta o registro de como estava antes. '
            f'Ela fica só como histórico. Se precisar corrigir, avise a Consiste informando o número da operação ({id_operacao}).'
        )

    tem_exclusao = any(item.tipo_mudanca == 'DELETE' for item in itens)
    if tem_exclusao and operacao.modulo in (_MODULO_SAIDA_COMUNICADO, _MODULO_MORTE, _MODULO_REIDENTIFICACAO):   # v1.18.0 / v1.20.0 / v1.23.0 - a baixa guarda a linha inteira da tb_2001: reversivel
        tem_exclusao = any(item.tipo_mudanca == 'DELETE' and item.tabela != 'tb_2001' for item in itens)
    if tem_exclusao:
        return None, None, (
            'Esta operação inclui uma exclusão definitiva e não pode ser desfeita '
            'automaticamente — fica apenas registrada como histórico.'
        )

    # ---------------------------------------------------
    # v1.3.0 - Regra "so a ultima" (Benedito, Sessao 082): modulo de
    # numeracao oficial nao deixa buraco na sequencia. Existe
    # operacao MAIS RECENTE, do mesmo modulo, ainda nao desfeita?
    # Entao esta nao e a ultima - bloqueia com aviso claro.
    # ---------------------------------------------------
    # ---------------------------------------------------
    # v1.16.0 - SO A ULTIMA DA PROPRIEDADE (Benedito, S104): existe operacao MAIS RECENTE nesta Propriedade, de qualquer modulo, ainda
    # nao desfeita? Entao algo foi feito depois e desfazer esta poderia quebrar o que veio depois. Bloqueia.
    # ---------------------------------------------------
    tipo_regra_b = _tipo_saida_regra_b(itens) if operacao.modulo == _MODULO_SAIDA_COMUNICADO else None   # v1.22.0 - Transferencia / Venda fora da base
    posterior = (
        db.query(LogOperacao.id)
        .filter(
            LogOperacao.id_propriedade == operacao.id_propriedade,
            LogOperacao.id > operacao.id,
            LogOperacao.desfeito_em.is_(None),
        )
        .first()
    )
    if posterior is not None and tipo_regra_b is None:   # v1.22.0 - a Regra B troca esta trava pelas conferencias de numero e de animal
        return None, None, (
            'Existe uma operação mais recente nesta Propriedade. Para não comprometer o que veio depois, '
            'só a última operação pode ser desfeita.'
        )
    # v1.18.0 - Comunicado de Saida: ja impresso, ou animal com outra movimentacao?
    if operacao.modulo == _MODULO_SAIDA_COMUNICADO:
        if tipo_regra_b:   # v1.22.0 - Regra B (Transferencia / Venda fora da base); Abate segue na regra antiga
            motivo_saida = _saida_transfer_venda_comprometida(db, operacao, itens, tipo_regra_b)
        else:
            motivo_saida = _saida_comunicado_comprometida(db, itens)
        if motivo_saida:
            return None, None, f'Este Comunicado de Saída não pode mais ser desfeito. {motivo_saida}'

    # v1.20.0 - Morte: so ate gerar a Notificacao (decisao do Benedito, 01/11/2026)
    if operacao.modulo == _MODULO_MORTE:
        motivo_morte = _morte_comprometida(db, itens)
        if motivo_morte:
            return None, None, f'Esta morte não pode mais ser desfeita. {motivo_morte}'

    # v1.23.0 - Reidentificacao: so enquanto o pedido nao foi enviado e nada aconteceu depois com os animais
    if operacao.modulo == _MODULO_REIDENTIFICACAO:
        motivo_reid = _reidentificacao_comprometida(db, itens)
        if motivo_reid:
            return None, None, f'Esta Reidentificação não pode mais ser desfeita. {motivo_reid}'

    # v1.16.0 - Brincagem Sequencial: algo foi feito depois com os animais dela?
    if operacao.modulo == 'brincagem_sequencial':
        motivo_brincagem = _brincagem_sequencial_comprometida(db, itens)
        if motivo_brincagem:
            return None, None, f'Esta Brincagem não pode mais ser desfeita. {motivo_brincagem}'

    # v1.8.0 - Entrada de Brincos: so desfaz lote INTACTO (qualquer um, nao so o ultimo).
    if operacao.modulo == _MODULO_ENTRADA_BRINCOS:
        for item in itens:
            if item.tabela == _TABELA_LOTE_BRINCOS and item.tipo_mudanca == 'INSERT':
                motivo = _lote_de_brincos_intacto(db, item.id_registro)
                if motivo:
                    return None, None, (
                        f'Esta entrada de brincos não pode mais ser desfeita. {motivo}'
                    )

    nome_documento = MODULOS_SO_ULTIMA.get(operacao.modulo)
    if nome_documento:
        # v1.6.0 - Notificacao que recebeu animal lido no brete: nao desfaz.
        if _notificacao_recebeu_animal_do_brete(db, itens):
            return None, None, (
                f'Esta {nome_documento} recebeu animais lidos no brete e não pode mais ser '
                f'desfeita automaticamente.'
            )

        # v1.5.0 - Notificacao ja IMPRESSA (Certificadora avisada): nao desfaz.
        if _notificacao_ja_impressa(db, itens):
            return None, None, (
                f'Esta {nome_documento} já foi IMPRESSA (a Certificadora já foi avisada) '
                f'e não pode mais ser desfeita.'
            )

        mais_recente = (
            db.query(LogOperacao)
            .filter(
                LogOperacao.modulo == operacao.modulo,
                LogOperacao.id_propriedade == operacao.id_propriedade,   # v1.9.0 - "so a ultima" da PROPRIEDADE
                LogOperacao.id > operacao.id,
                LogOperacao.desfeito_em.is_(None),
            )
            .first()
        )
        if mais_recente is not None:
            return None, None, (
                f'Só a última {nome_documento} pode ser desfeita, para não deixar '
                f'buraco na numeração oficial. Existe uma mais recente — desfaça '
                f'primeiro a mais recente.'
            )

        # v1.4.0 - e pela NUMERACAO real: existe NAS maior (ex.:
        # Controle reservado pelo brete depois deste lancamento)?
        if _existe_nas_maior_que_o_da_operacao(db, itens):
            return None, None, (
                f'Só a última {nome_documento} pode ser desfeita, para não deixar '
                f'buraco na numeração oficial. Já existe um Número de Controle '
                f'maior que o desta operação.'
            )

    return operacao, itens, None


# -------------------------------------------------------
# Funcao auxiliar: reflete uma tabela pelo nome usando a MESMA
# conexao ja aberta da sessao (db.connection(), NAO db.get_bind()) -
# critico para funcionar dentro do schema do Produtor.
#
# BUG REAL corrigido aqui (Benedito, Sessao 045, teste em producao):
# db.get_bind() devolve o ENGINE, nao a conexao em uso - o
# SQLAlchemy abre uma CONEXAO NOVA e separada para fazer a reflexao,
# que nunca recebeu o "SET search_path TO produtor_NNNNN, public"
# executado por get_db_produtor() (backend/utils/multitenant.py).
# Resultado: a tabela era procurada no schema padrao (nao encontrava
# tb_3008_brincos_saida, por exemplo - erro real:
# sqlalchemy.exc.NoSuchTableError). db.connection() devolve a MESMA
# conexao ja em uso pela sessao (mesma transacao), que ja tem o
# search_path certo - corrige o problema na raiz.
# -------------------------------------------------------
def _refletir_tabela(db, nome_tabela):
    metadata = MetaData()
    return Table(nome_tabela, metadata, autoload_with=db.connection())


# -------------------------------------------------------
# Funcao: verificar_conflitos() - para cada item tipo UPDATE,
# confere se o valor ATUAL no banco ainda bate com o que foi
# gravado em dados_depois - se qualquer campo mudou, e um
# conflito (algo mexeu depois desta operacao). Itens tipo INSERT
# so conferem se a linha ainda existe (se ja sumiu, nao e
# bloqueio - so nao ha o que desfazer, sera ignorado no
# executar_desfazer). Itens tipo DELETE nunca chegam aqui - ja
# foram barrados em buscar_operacao_desfazivel() (v1.2.0).
#
# Retorna lista de strings (descricao do conflito) - vazia se
# nao houver nenhum. Regra de negocio (Benedito, Sessao 045):
# QUALQUER conflito bloqueia a operacao INTEIRA - nada e desfeito
# parcialmente.
# -------------------------------------------------------
def verificar_conflitos(db, itens):
    conflitos = []

    for item in itens:
        tabela_obj = _refletir_tabela(db, item.tabela)

        linha_atual = db.execute(
            select(tabela_obj).where(tabela_obj.c.id == item.id_registro)
        ).mappings().first()

        if item.tipo_mudanca == 'UPDATE':
            if linha_atual is None:
                conflitos.append(
                    f'{item.tabela} #{item.id_registro}: registro não existe mais.'
                )
                continue

            for campo, valor_esperado in (item.dados_depois or {}).items():
                valor_atual = linha_atual.get(campo)
                # Compara como string pra evitar falso-positivo por
                # tipo (ex.: Decimal vs float, date vs string ISO).
                if str(valor_atual) != str(valor_esperado):
                    conflitos.append(
                        f'{item.tabela} #{item.id_registro}: campo "{campo}" foi alterado '
                        f'depois desta operação (era "{valor_esperado}", está "{valor_atual}").'
                    )

        # INSERT: nao gera conflito se a linha ja nao existir mais -
        # so significa que nao ha nada a desfazer para esse item
        # especifico (tratado em executar_desfazer).

    return conflitos


# -------------------------------------------------------
# Funcao: executar_desfazer() - aplica a reversao de fato. So deve
# ser chamada DEPOIS de buscar_operacao_desfazivel() (sem erro) E
# verificar_conflitos() (lista vazia). Processa os itens em ORDEM
# REVERSA (desfaz o mais recente primeiro - relevante quando ha
# dependencia entre linhas da mesma operacao).
#
# UPDATE -> aplica dados_antes de volta na linha.
# INSERT -> apaga a linha (se ainda existir).
# DELETE nunca chega aqui - barrado antes (v1.2.0).
#
# Marca a operacao como desfeita (desfeito_em, desfeito_por) ao
# final. Nao da commit - quem chama decide o commit final, mesmo
# padrao das demais rotinas do sistema.
# -------------------------------------------------------
def _nomes_das_fotos_da_morte(db, itens):
    """v1.20.0 - nomes dos arquivos de foto dos animais deste lancamento da Morte (para apagar do disco depois do Desfazer)."""
    ids = [i.id_registro for i in itens if i.tabela == 'tb_2002_saida_animais' and i.tipo_mudanca == 'INSERT']
    if not ids:
        return []
    try:
        t = _refletir_tabela(db, 'tb_2022_morte_fotos')
        return [n for (n,) in db.execute(select(t.c.arquivo_nome).where(t.c.id_saida_animal.in_(ids))).all()]
    except NoSuchTableError:
        return []


def executar_desfazer(db, operacao, itens, id_usuario_logado):
    nomes_fotos = _nomes_das_fotos_da_morte(db, itens) if operacao.modulo == _MODULO_MORTE else []
    for item in reversed(itens):
        tabela_obj = _refletir_tabela(db, item.tabela)

        if item.tipo_mudanca == 'UPDATE':
            if item.dados_antes:
                db.execute(
                    tabela_obj.update()
                    .where(tabela_obj.c.id == item.id_registro)
                    .values(**item.dados_antes)
                )
        elif item.tipo_mudanca == 'DELETE' and item.tabela == 'tb_2001' and operacao.modulo in (_MODULO_SAIDA_COMUNICADO, _MODULO_MORTE, _MODULO_REIDENTIFICACAO):
            # v1.18.0 - o animal volta para a Propriedade: reinsere a linha inteira guardada na baixa
            campos = {c.key: _valor_do_log(c, item.dados_antes[c.key]) for c in tabela_obj.columns if c.key in (item.dados_antes or {})}
            db.execute(tabela_obj.insert().values(**campos))
        elif item.tipo_mudanca == 'INSERT':
            # v1.8.0 - lote de brincos: apaga antes os brincos do lote (FK).
            if item.tabela == _TABELA_LOTE_BRINCOS:
                brincos = _refletir_tabela(db, _TABELA_BRINCOS)
                db.execute(
                    brincos.delete().where(brincos.c.id_lote_entrada == item.id_registro)
                )
            db.execute(
                tabela_obj.delete().where(tabela_obj.c.id == item.id_registro)
            )

    operacao.desfeito_em  = datetime.now()
    operacao.desfeito_por = id_usuario_logado
    # v1.26.0 - as linhas das fotos saem por cascata (banco); os ARQUIVOS so podem sair DEPOIS do commit:
    # devolve os nomes e a rota apaga os arquivos apos o db.commit() (se o commit falhar, nenhuma foto some).
    return nomes_fotos

# =========================================================
# FIM DE ARQUIVO: backend\utils\log_operacoes.py
# =========================================================
