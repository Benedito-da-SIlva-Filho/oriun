# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\models
# MODULO:       backend\models\__init__.py
# AUTOR:        Benedito Silva Filho.
# CRIADO EM:    2026-06-21 09:41 -03
# ATUALIZADO EM: 2026-10-16 14:16 -03
# VERSAO:       1.20.0
#
# DESCRICAO:
#     Inicializador do modulo de models.
#     v1.0.0: Criacao do modulo.
#     v1.1.0: Sessao 010 - Adicionados os models novos do
#             modulo GERAS (Proprietario, PropriedadeProdutor,
#             PropriedadeProprietario), necessarios para o
#             SQLAlchemy resolver os relationship() que
#             referenciam essas classes pelo nome.
#     v1.2.0: Sessao 011 - Adicionados os models Protocolo e
#             PropriedadeProtocolo (catalogo administravel de
#             protocolos/selos - ABPO, PEFB, CSCB, Cota Hilton -
#             e o vinculo com Propriedade).
#     v1.3.0: Sessao 17 - Adicionado o model Parceiro
#             (tb_parceiros).
#     v1.4.0: Sessao 019 - Adicionados os 4 models novos do
#             modulo Brincos: Fabricante (tb_1021_fabricantes_
#             brincos, schema publico), BrincoEntrada
#             (tb_3007_brincos_entrada), BrincoSaida
#             (tb_3008_brincos_saida) e EntradaBrincoRfid
#             (tb_7017_entrada_brincos_rfid) - estas 3 ultimas
#             vivem no schema do Produtor (Schema-por-Produtor).
#             Pre-requisito para a Rotina de Onboarding do
#             Produtor (proximo passo da sessao).
#     v1.5.0: Sessao 020 - Adicionados os 3 models novos de
#             catalogo do Parelhamento Orion x GERAS, pasta
#             1-Cadastros: MotivoMorte (tb_1007_motivo_mortes),
#             RegimeUso (tb_1011_regime_uso) e Municipio
#             (tb_1023_municipios). Todos schema publico.
#     v1.6.0: Sessao 022 - Adicionados os 5 models novos de
#             catalogo do Parelhamento Orion x GERAS, pasta
#             4-Animais: Especie (tb_4002_especie),
#             TipoIdentificacao (tb_4013_tipos_identificacao),
#             Aptidao (tb_4004_aptidao), IdadeMeses
#             (tb_4006_idade_meses) e Raca (tb_4005_racas).
#             Todos schema publico.
#     v1.7.0: Sessao 022 - Adicionados os models ReIdElementos
#             (tb_6003_re_id_elementos) e ReIdElementosItem
#             (tb_6004_re_id_elementos_itens), pasta 6-Formularios
#             (processo de Reidentificacao por Elementos). Ambos
#             vivem no schema do Produtor (Schema-por-Produtor).
#     v1.8.0: Sessao 022 - Adicionados os models
#             ReidentificacaoComBaixa (tb_6005_reidentificacao_com_
#             baixa) e ReidentificacaoComBaixaItem (tb_6006_
#             reidentificacao_com_baixa_itens), pasta 6-Formularios
#             (processo de Reidentificacao COM Baixa, SISBOV muda
#             de fato). Ambos vivem no schema do Produtor.
#     v1.9.0: Sessao 022 - Adicionados os models PerdaSaidaEstoque
#             (tb_6007_perda_saida_estoque) e PerdaSaidaEstoqueItem
#             (tb_6008_perda_saida_estoque_itens), pasta 6-Formularios
#             (processo de Perda Saida Estoque, animal sem nenhum
#             elemento de identificacao). Ambos vivem no schema do
#             Produtor.
#     v1.10.0: Sessao 022 - Adicionados os models CancelamentoBrinco
#              (tb_6012_cancelamento_brinco) e CancelamentoBrincoItem
#              (tb_6013_cancelamento_brinco_itens), pasta 6-Formularios
#              (processo de Cancelamento de Brinco). Ambos vivem no
#              schema do Produtor. Fecha, por hoje, a familia de
#              tabelas de Reidentificacao/Formularios.
#     v1.11.0: Sessao 024 - Adicionado o model Animal (tb_2001,
#              Estado Atual do Animal), pasta 4-Animais. Vive no
#              schema do Produtor (Schema-por-Produtor) - guarda
#              somente o rebanho vivo, DELETE fisico no evento de
#              saida.
#     v1.12.0: Sessao 026 - Adicionado o model LogConferenciaPropriedade
#              (tb_log_conferencia_propriedade), log de auditoria
#              imutavel do lado interno (Destino/Propriedade) da
#              leitura de GTA - fecha o P-029 do Diario 025. Vive no
#              schema do Produtor (Schema-por-Produtor).
#     v1.13.0: Sessao 026 - Reorganizacao dos imports em dois blocos,
#              sem mudanca de comportamento (mesmas classes, mesmos
#              nomes): TERREO (cadastros base do Orion + catalogos
#              publicos usados por todos os Produtores, sem numero
#              de tabela GERAS ou com numero mas de uso universal) e
#              ANDARES (tabelas com numero GERAS que vivem no schema
#              de cada Produtor, em ordem numerica crescente). Motivo:
#              com quase 40 imports, ficava dificil localizar e
#              conferir se todo model estava registrado. Unico
#              desempate necessario: tb_4001 tem duas tabelas (Gta e
#              GtaAnimal) - mantido Gta (cabecalho) antes de GtaAnimal
#              (linha filha), mesmo criterio ja usado no Inventario de
#              Modulos da Referencia.
#     v1.14.0: Sessao de definicao do modelo de acesso do Produtor/
#              Equipe - Adicionado o model UsuarioVinculo
#              (usuario_vinculo), schema publico. Substitui os campos
#              fixos usuarios.cargo e usuarios.id_produtor (aposentados
#              no codigo, mantidos fisicamente por enquanto). Registrado
#              na secao TERREO, logo apos Usuario, por ser referenciada
#              por auth.py (login) e pelo futuro modulo de cadastro de
#              Equipe.
#     v1.15.0: Sessao 034 (continuacao 5, 11/08/2026, 12:26 -03) -
#              RENOMEACAO (decisao de Benedito): tb_2001_animal.py /
#              classe Animal viram tb_2001_entradas.py / classe
#              Entrada - nome antigo descrevia mal o proposito real
#              da tabela (e o lado ENTRADA do rebanho, par futuro de
#              tb_2002/Saidas). Import atualizado na secao ANDARES,
#              mesma posicao (logo apos os catalogos do TERREO, antes
#              de BrincoEntrada). Nenhuma outra mudanca nesta versao -
#              ver tb_2001_entradas.py v1.1.0 e onboarding.py para o
#              restante da renomeacao.
#     v1.16.0: Sessao 034 (continuacao 6, 11/08/2026, 19:33 -03) -
#              Adicionado o model ConviteProspect (convite_prospects),
#              schema publico. Registrado na secao TERREO, logo apos
#              UsuarioVinculo (mesmo criterio - tabela referenciada
#              por usuarios.id, sem numero de tabela GERAS). Suporta
#              a nova funcionalidade de Convite de Prospects (Consiste
#              convida Produtores prospects por e-mail, reaproveitando
#              o link fixo do Convite Publico existente).
#     v1.17.0: Sessao 034 (continuacao 6, 11/08/2026, 20:30 -03) -
#              Adicionado o model VitrineVisitante (vitrine_visitantes),
#              schema publico. Registrado na secao TERREO, logo apos
#              ConviteProspect. Suporta a Tela Vitrine publica - a
#              Etapa 1 do Convite Publico (/convite) agora leva o
#              visitante para uma vitrine travada do sistema, em vez
#              de criar conta real direto (Etapa 2 pausada, ver
#              convite.py v2.2.0).
#     v1.18.0: Sessao 089 (07/10/2026, 12:05 -03) - Adicionados os models
#              AuditoriaEras (tb_auditoria_eras) e LogAuditoriaEras
#              (tb_log_auditoria_eras), schema publico: vistorias/auditorias
#              das Propriedades com codigo ERAS e o log das correcoes.
#              Registrados na secao TERREO, logo apos
#              LogConferenciaPropriedade (tabelas sem numero GERAS).
#     v1.19.0: Sessao 092 (09/10/2026, 17:35 -03) - BLOCKCHAIN: adicionados os 4
#              models tb_blk_8000_provedores (ProvedorBlk, schema publico, no
#              TERREO) e tb_blk_8001_produtor_provedores, tb_blk_8002_eventos e
#              tb_blk_8003_envios (ProdutorProvedorBlk, EventoBlk, EnvioBlk, no
#              schema de cada Produtor, nos ANDARES).
#     v1.20.0: Sessao 098 (16/10/2026, 14:16 -03) - SAIDAS (Abate): adicionados os 3
#              models Embarque (tb_2020_embarque), SaidaAnimal (tb_2002_saida_animais) e
#              ComunicadoSaida (tb_2011_com_saidas), no schema de cada Produtor, nos
#              ANDARES, em ordem numerica logo apos Entrada (tb_2001).
# =========================================================

# ---------------------------------------------------------
# TERREO — Cadastros base do Orion + catalogos publicos de
# uso universal (todo Produtor consulta). Ordem: cadastros
# base primeiro (como historicamente estavam), depois os
# catalogos numerados GERAS em ordem crescente.
# ---------------------------------------------------------
from .certificadora import Certificadora
from .propriedade import Propriedade
from .produtor import Produtor
from .usuario import Usuario
from .usuario_vinculo import UsuarioVinculo
from .convite_prospect import ConviteProspect
from .vitrine_visitante import VitrineVisitante
from .proprietario import Proprietario
from .propriedade_produtor import PropriedadeProdutor
from .propriedade_proprietario import PropriedadeProprietario
from .protocolo import Protocolo
from .propriedade_protocolo import PropriedadeProtocolo
from .tb_parceiros import Parceiro
from .tb_parceiros_propriedades import ParceiroPropriedades
from .tb_frigorificos import Frigorifico
from .tb_log_conferencia_parceiro import LogConferenciaParceiro
from .tb_log_conferencia_propriedade import LogConferenciaPropriedade
from .tb_auditoria_eras import AuditoriaEras
from .tb_log_auditoria_eras import LogAuditoriaEras
from .tb_1007_motivo_mortes import MotivoMorte
from .tb_1011_regime_uso import RegimeUso
from .tb_1021_fabricantes_brincos import Fabricante
from .tb_1023_municipios import Municipio
from .tb_4002_especie import Especie
from .tb_4004_aptidao import Aptidao
from .tb_4005_racas import Raca
from .tb_4006_idade_meses import IdadeMeses
from .tb_4013_tipos_identificacao import TipoIdentificacao
from .tb_blk_8000_provedores import ProvedorBlk

# ---------------------------------------------------------
# ANDARES — Tabelas com numero GERAS que vivem no schema de
# cada Produtor (Schema-por-Produtor), em ordem numerica
# crescente. Desempate do 4001: Gta (cabecalho) antes de
# GtaAnimal (linha filha).
# ---------------------------------------------------------
from .tb_2001_entradas import Entrada
from .tb_2002_saida_animais import SaidaAnimal
from .tb_2011_com_saidas import ComunicadoSaida
from .tb_2020_embarque import Embarque
from .tb_3007_brincos_entrada import BrincoEntrada
from .tb_3008_brincos_saida import BrincoSaida
from .tb_4001_gta import Gta
from .tb_4001_gta_animais import GtaAnimal
from .tb_5001_brincagem import Brincagem
from .tb_6003_re_id_elementos import ReIdElementos
from .tb_6004_re_id_elementos_itens import ReIdElementosItem
from .tb_6005_reidentificacao_com_baixa import ReidentificacaoComBaixa
from .tb_6006_reidentificacao_com_baixa_itens import ReidentificacaoComBaixaItem
from .tb_6007_perda_saida_estoque import PerdaSaidaEstoque
from .tb_6008_perda_saida_estoque_itens import PerdaSaidaEstoqueItem
from .tb_6012_cancelamento_brinco import CancelamentoBrinco
from .tb_6013_cancelamento_brinco_itens import CancelamentoBrincoItem
from .tb_7017_entrada_brincos_rfid import EntradaBrincoRfid
from .tb_blk_8001_produtor_provedores import ProdutorProvedorBlk
from .tb_blk_8002_eventos import EventoBlk
from .tb_blk_8003_envios import EnvioBlk

# =========================================================
# FIM DE ARQUIVO: backend\models\__init__.py
# =========================================================