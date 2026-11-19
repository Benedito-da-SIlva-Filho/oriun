# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\permissoes.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-15 09:41 -03
# ATUALIZADO EM: 2026-11-18 20:30 -03
# VERSAO: 1.21.0
#
# DESCRICAO:
#     Logica PURA das permissoes por cargo (sem Flask, sem banco):
#     catalogo de modulos, mapa de enderecos -> modulo, valores
#     padrao de cada cargo e regra de nivel exigido. Quem usa banco
#     e sessao e o backend\routers\permissoes.py (o porteiro).
#
#     NIVEIS (cada um inclui o anterior):
#       SEM_ACESSO = 0   nao ve o modulo.
#       CONSULTA   = 1   so olha (GET).
#       LANCA      = 2   olha e grava (GET + POST).
#       TUDO       = 3   inclui acoes sensiveis (excluir, desfazer,
#                        backup, restaurar).
#
#     O catalogo e o mapa ficam NO CODIGO. O banco (tabela
#     public.permissao_cargo) guarda so os AJUSTES do Titular.
#     Sem ajuste, vale o padrao abaixo.
#
# HISTORICO DE VERSOES:
#     v1.0.0: Sessao 097 (15/10/2026, 09:41 -03) - Criacao. Etapa 1 do
#             pacote de permissoes por cargo.
#     v1.1.0: Sessao 097 (15/10/2026, 11:20 -03) - AUDITORIA: o porteiro passa a cobrir tambem /propriedades, /proprietarios,
#             /produtores e /api/busca-cpf-cnpj (modulo propriedade). Antes, um cargo sem acesso
#             a Minha Propriedade abria essas telas digitando o endereco.
#     v1.2.0: Sessao 097 (15/10/2026, 11:50 -03) - ETAPA 2: (1) nivel exigido por TELA: telas de lancamento (TELAS_DE_LANCAMENTO)
#             pedem Lanca ate para abrir; listas e relatorios abrem em Consulta; POST de relatorio
#             (POST_SO_LEITURA) vale em Consulta. (2) Campeiro/Auxiliar passam a ter, por padrao,
#             Consulta por Manejo e Alterar Dados dos Animais. (3) Constantes e regras da tela de
#             Permissoes (modulos, cargos, opcoes por modulo, pode_editar_celula).
#     v1.3.0: Sessao 097 (15/10/2026, 13:40 -03) - ETAPA 4: Racas da Fazenda passa do modulo Utilitarios para Entrada
#         (decisao do Benedito); abrir o formulario de pedido de restore (GET) tambem exige Tudo.
#     v1.4.0: Sessao 097 (15/10/2026, 14:00 -03) - Padrao: Gerente/Capataz e Veterinario ficam SEM
#         acesso ao modulo Entrada (decisao do Benedito). O Titular ainda pode liberar na tela de Permissoes.
#     v1.4.0: Sessao 098 (16/10/2026, 18:40 -03) - Hub de Saidas: o slug hub-novo/saida passa a valer como modulo Saidas.
#     v1.4.1: Sessao 098 (16/10/2026, 20:20 -03) - saida-leitor passa a valer como modulo Saidas, e a tela de lancamento; POST /produtor/saida-leitor/limpar = acao sensivel (Tudo).
#     v1.4.2: Sessao 099 (17/10/2026, 11:35 -03) - Retirado POST /produtor/saida-leitor/limpar das acoes sensiveis
#         (o Limpar Leitura deixou de existir). A nova rota POST /produtor/saida-leitor/excluir-antiga vale como tela de
#         lancamento (prefixo /produtor/saida-leitor/), sem nivel extra: quem le no brete decide (Benedito).
#     v1.4.3: Sessao 099 (17/10/2026, 12:35 -03) - saida-bastao (Leitor do Abate com Bastao) vale como modulo Saidas e como tela de
#         lancamento (prefixo /produtor/saida-bastao/), igual ao saida-leitor.
#     v1.4.4: Sessao 099 (17/10/2026, 14:50 -03) - frigorificos vale como modulo Parceiros e Fornecedores (mesma permissao de
#         Parceiros); abrir /produtor/frigorificos/novo (cadastro) exige Lanca. Sem modulo novo na tela de Permissoes.
#     v1.4.5: Sessao 099 (17/10/2026, 15:00 -03) - gta-saida (Cadastro de GTA de Saida) vale como modulo Saidas; abrir o formulario
#         (/produtor/gta-saida/nova) e gravar (salvar) exigem Lanca. Lista e detalhe valem com Consulta.
#     v1.4.6: Sessao 099 (17/10/2026, 15:30 -03) - saida-relatorio (Relatorio de Embarque) vale como modulo Saidas; so leitura/PDF, vale com Consulta.
#     v1.4.7: Sessao 099 (17/10/2026, 17:15 -03) - saida-consulta (Consulta Embarque) vale como modulo Saidas; lista abre em Consulta, Data Embarque e Correcao pedem Lanca.
#     v1.4.8: Sessao 100 (19/10/2026, 16:50 -03) - saida-vincular (Vincular GTA / Embarque) vale como modulo Saidas; todas as telas e acoes (escolher GTA, conferencia, salvar, desvincular) pedem Lanca.
#     v1.4.9: Sessao 100 (19/10/2026, 20:40 -03) - saida-substituicao (Substituicao de Animal) vale como modulo Saidas; todas as telas e acoes (escolher data, animais, trocar, checar, gravar) pedem Lanca.
#     v1.5.0: Sessao 101 (20/10/2026, 09:22 -03) - saida-gta-consulta (Consulta GTA de Saida) vale como modulo Saidas; so consulta e PDF, vale com Consulta (nao entra nas telas de lancamento).
#     v1.5.1: Sessao 101 (20/10/2026, 10:47 -03) - saida-comunicado (Gerar Comunicado de Saida) vale como modulo Saidas; todas as telas e acoes (lista, conferencia, gerar) pedem Lanca.
#     v1.6.0: Sessao 102 (21/10/2026, 12:20 -03) - 'consulta-animal' (Consulta de Animal e Brinco, so leitura) entra no mapa do porteiro como modulo 'consulta_manejo': vale para todos os cargos com acesso a Consulta por Manejo.
#     v1.5.2: Sessao 101 (20/10/2026, 12:15 -03) - saida-impressao (Impressao do Comunicado de Saida, grava IMPRESSO) pede Lanca; saida-reimpressao (so gera o PDF, nunca grava) vale com Consulta. Os dois valem como modulo Saidas.
#     v1.7.0: Sessao 102 (2026-10-21 12:35 -03) - saida-troca-comunicado (Troca de Animal depois do Comunicado) vale como modulo Saidas; todas as telas e acoes pedem Lanca (a regra Titular/Administrador e conferida no proprio router).
#     v1.8.0: Sessao 102 (2026-10-21 17:40 -03) - saida-arquivo (Abate por Arquivo Texto) vale como modulo Saidas; todas as telas e acoes pedem Lanca.
#     v1.9.0: Sessao 103 (2026-10-22 12:45 -03) - gta-saida: editar, salvar-edicao e excluir (Alterar/Excluir GTA de Saida) pedem Lanca; a regra Titular/Administrador e conferida no proprio router.
#     v1.21.0: Sessao 132 (2026-11-18 20:30 -03) - bnd-fazenda (BND/Fazenda, comparacao do Extrato com o estoque) vale como modulo Entrada (consulta, nao grava). REVERSAO: .bak_antes_s132_bnd.
#     v1.20.0: Sessao 129 (2026-11-17 11:30 -03) - pesos-relatorios (Relatorios de Pesagem) vale como modulo Pesagens (tela de consulta, nao e lancamento). REVERSAO: .bak_antes_s129_pesos_relatorios.
#     v1.14.0: Sessao 114 (2026-11-04 19:00 -03) - pesos-consulta e pesos-conferidos (Consulta de Peso e Conferidos) valem como modulo Pesagens (telas de consulta, nao sao lancamento).  REVERSAO: .bak_antes_s114_consulta.
#     v1.13.0: Sessao 114 (2026-11-04 14:50 -03) - pesos-bastao (Leitor de Peso com Bastao) vale como modulo Pesagens e como tela de lancamento (prefixo /produtor/pesos-bastao/).  REVERSAO: .bak_antes_s114_bastao.
#     v1.12.0: Sessao 114 (2026-11-04 11:20 -03) - pesos-leitor e pesos-inconformes valem como modulo Pesagens; hub pesos = Pesagens; /produtor/pesos-leitor/ e tela de lancamento.  REVERSAO: .bak_antes_s114_pesos.
#     v1.11.0: Sessao 111 (2026-11-01 17:00 -03) - venda (Leitor, Bastao e Arquivo da Venda) e morte (lancamento da Morte) valem como modulo Saidas e como tela de lancamento (prefixos /produtor/venda/ e /produtor/morte/), iguais a transferencia. REVERSAO: .bak_antes_s111_venda_morte.
#     v1.10.0: Sessao 107 (2026-10-28 09:45 -03) - transferencia (Leitor da Transferencia e com Bastao) vale como modulo Saidas e como tela de lancamento (prefixo /produtor/transferencia/), igual ao saida-leitor. REVERSAO: .bak_antes_s107.
#     v1.19.0: Sessao 128 (2026-11-16 11:45 -03) - AUDITORIA ETAPA 8a: /api/busca-parceiro (vale com Consulta em Entrada, Saidas ou Parceiros) e /api/busca-propriedade (vale com Consulta em Parceiros) passam pelo porteiro; antes qualquer cargo logado consultava. REVERSAO: .bak_antes_etapa8a.
# =========================================================
#     v1.15.0: Sessao 115 (2026-11-05 13:45 -03) - posse (Leitor da Alteracao de Posse e com Bastao) vale como modulo Saidas e tela de lancamento (prefixo /produtor/posse/), igual a transferencia. REVERSAO: .bak_antes_s115_posse_pacote2.
#     v1.18.0: Sessao 121 (2026-11-11 14:20 -03) - reidentificacao, reidentificacao-consulta e reidentificacao-inconformes valem como modulo Entrada; a tela de lancamento (prefixo /produtor/reidentificacao/) exige Lanca. REVERSAO: .bak_antes_s121_reidentificacao.
#     v1.17.0: Sessao 120 (2026-11-10 21:50 -03) - linkagem-consulta e linkagem-inconformes valem como modulo Entrada (telas de consulta, NAO sao lancamento). REVERSAO: .bak_antes_s120_pacote2.
#     v1.16.0: Sessao 120 (2026-11-10 18:40 -03) - linkagem-rfid (Linkagem RFID e Brinco) vale como modulo Entrada e tela de lancamento (prefixo /produtor/linkagem-rfid/). REVERSAO: .bak_antes_s120_linkagem.

SEM_ACESSO = 0
CONSULTA   = 1
LANCA      = 2
TUDO       = 3

NIVEIS = {
    'SEM_ACESSO': SEM_ACESSO,
    'CONSULTA':   CONSULTA,
    'LANCA':      LANCA,
    'TUDO':       TUDO,
}
NOMES_NIVEL = {valor: nome for nome, valor in NIVEIS.items()}

# Cargos do vinculo (UsuarioVinculo.cargo), na ordem de exibicao.
CARGOS = (
    'TITULAR',
    'ADMINISTRADOR',
    'ADMINISTRATIVO',
    'GERENTE_CAPATAZ',
    'VETERINARIO_ZOOTECNISTA',
    'CAMPEIRO',
    'AUXILIAR',
)

CARGOS_CAMPO       = ('CAMPEIRO', 'AUXILIAR')
CARGOS_ESCRITORIO  = ('ADMINISTRADOR', 'ADMINISTRATIVO', 'GERENTE_CAPATAZ',
                      'VETERINARIO_ZOOTECNISTA')

# Modulos (codigo -> nome mostrado ao Titular).
MODULOS = {
    'painel':               'Painel (Home e Hubs)',
    'brincagem':            'Brincagem (Brete)',
    'brincagem_sequencial': 'Brincagem Sequencial',
    'consulta_manejo':      'Consulta por Manejo e de Animal e Brinco',
    'alterar_dados':        'Alterar Dados dos Animais',
    'entrada':              'Entrada de animais',
    'saidas':               'Saidas',
    'pesagens':             'Pesagens',
    'brincos':              'Brincos',
    'inventario':           'Inventario',
    'parceiros':            'Parceiros',
    'propriedade':          'Minha Propriedade e Auditorias ERAS',
    'utilitarios':          'Utilitarios',
    'equipe':               'Equipe da Propriedade',
}
PAINEL = 'painel'

# -------------------------------------------------------
# Mapa de enderecos: 1o pedaco do caminho depois de /produtor/
# -> modulo. Endereco que nao estiver aqui e BARRADO (menos para
# o Titular), para nada ficar aberto por esquecimento.
# -------------------------------------------------------
MODULO_POR_SEGMENTO = {
    # Painel (sempre liberado em CONSULTA, no minimo)
    'home': PAINEL, 'home-novo': PAINEL, 'home-antigo': PAINEL,
    'selecionar-vinculo': PAINEL,
    # Brincagem (Brete)
    'saida-leitor': 'saidas', 'saida-bastao': 'saidas', 'transferencia': 'saidas', 'posse': 'saidas', 'venda': 'saidas', 'morte': 'saidas', 'gta-saida': 'saidas', 'saida-relatorio': 'saidas', 'saida-consulta': 'saidas', 'saida-vincular': 'saidas', 'saida-substituicao': 'saidas', 'saida-troca-comunicado': 'saidas', 'saida-arquivo': 'saidas', 'saida-gta-consulta': 'saidas', 'saida-comunicado': 'saidas', 'saida-impressao': 'saidas', 'saida-reimpressao': 'saidas', 'brincagem-leitor': 'brincagem', 'brincagem-bastao': 'brincagem', 'pesos-leitor': 'pesagens', 'pesos-bastao': 'pesagens', 'pesos-inconformes': 'pesagens', 'pesos-consulta': 'pesagens', 'pesos-conferidos': 'pesagens', 'pesos-relatorios': 'pesagens',
    'troca-rfid': 'brincagem', 'linkagem-rfid': 'entrada', 'linkagem-consulta': 'entrada', 'linkagem-inconformes': 'entrada', 'reidentificacao': 'entrada', 'reidentificacao-consulta': 'entrada', 'reidentificacao-inconformes': 'entrada', 'brincagem-consulta': 'brincagem',
    # De escritorio
    'brincagem-sequencial': 'brincagem_sequencial',
    'consulta-manejo': 'consulta_manejo',
    'consulta-animal': 'consulta_manejo',
    'alterar-dados-animais': 'alterar_dados',
    # Entrada
    'entrada': 'entrada', 'gta-manual': 'entrada', 'gta-consulta': 'entrada',
    'vincular-gta': 'entrada', 'comunicado-entrada': 'entrada',
    'impressao-comunicado': 'entrada', 'reimpressao-comunicado': 'entrada',
    'notificacao-nascimento': 'entrada', 'nascimentos-periodo': 'entrada',
    'nascimentos-controle': 'entrada', 'pia': 'entrada',
    'relatorio-eras': 'entrada', 'carga-relatorio': 'entrada', 'bnd-fazenda': 'entrada',
    # Inventario, Parceiros, Propriedade, Utilitarios, Equipe
    'inventario-geral': 'inventario',
    'parceiros': 'parceiros', 'parceiro-manual': 'parceiros', 'frigorificos': 'parceiros',
    'propriedade': 'propriedade', 'auditoria-eras': 'propriedade',
    'operacoes-recentes': 'utilitarios', 'backup': 'utilitarios',
    'racas': 'entrada',
    'usuarios': 'equipe',
}
# Telas do Produtor que ficam FORA de /produtor/ (cadastro de Propriedade,
# Proprietarios e Produtores) e a busca de CPF/CNPJ: tambem sao do modulo
# 'propriedade' (v1.1.0 - auditoria). So valem para PRODUTOR; a Consiste
# nao passa pelo porteiro.
MODULO_POR_PREFIXO_FORA = {
    'propriedades': 'propriedade', 'proprietarios': 'propriedade',
    'produtores': 'propriedade',
}
MODULO_POR_CAMINHO_EXATO = {
    '/api/busca-cpf-cnpj': 'propriedade',
    '/api/busca-parceiro': 'parceiros',      # v1.19.0
    '/api/busca-propriedade': 'parceiros',   # v1.19.0
}
# v1.19.0: busca usada por telas de mais de um modulo - basta Consulta em UM deles.
MODULOS_ALTERNATIVOS_POR_CAMINHO = {
    '/api/busca-parceiro': ('entrada', 'saidas', 'parceiros'),
    '/api/busca-propriedade': ('parceiros',),
}

# Todo endereco que comeca com "brincos-" e do modulo Brincos.
PREFIXO_BRINCOS = 'brincos-'

# Hubs: o modulo vem do slug (3o pedaco do caminho).
MODULO_POR_SLUG_HUB = {
    'entrada': 'entrada', 'entrada-consultas': 'entrada',
    'entrada-nascimento': 'entrada', 'entrada-comunicados': 'entrada',
    'brincagem': 'brincagem', 'brincos': 'brincos',
    'inventario': 'inventario', 'utilitarios': 'utilitarios',
    'saida': 'saidas',   # v1.4.0 - Hub de Saidas (Sessao 098)
    'pesos': 'pesagens',   # v1.12.0 - Hub de Pesos (Sessao 114)
}

# Acoes que pedem nivel TUDO (metodo, caminho).
ACOES_SENSIVEIS = {
    ('POST', '/produtor/brincagem-consulta/excluir'),
    ('POST', '/produtor/operacoes-recentes/desfazer'),
    ('POST', '/produtor/backup/criar'),
    ('POST', '/produtor/backup/solicitar-restore'),
    ('GET', '/produtor/backup/solicitar-restore'),
}

# GET que, na pratica, grava algo: exigem LANCA.
GETS_QUE_GRAVAM = {
    '/produtor/brincos-disponiveis/confirmar',
    '/produtor/comunicado-entrada/confirmar',
}


# Telas de LANCAMENTO: abrir ja exige Lanca (v1.2.0). Quem so tem Consulta abre as
# listas e relatorios do modulo, nao estas. Prefixo = caminho que comeca assim.
TELAS_DE_LANCAMENTO = (
    '/produtor/saida-leitor/', '/produtor/saida-bastao/', '/produtor/transferencia/', '/produtor/posse/', '/produtor/venda/', '/produtor/morte/', '/produtor/gta-saida/nova', '/produtor/gta-saida/salvar', '/produtor/gta-saida/editar/', '/produtor/gta-saida/salvar-edicao/', '/produtor/gta-saida/excluir/', '/produtor/saida-consulta/data-embarque', '/produtor/saida-consulta/correcao', '/produtor/saida-vincular/', '/produtor/saida-substituicao/', '/produtor/saida-troca-comunicado/', '/produtor/saida-arquivo/', '/produtor/saida-comunicado/', '/produtor/saida-impressao/', '/produtor/brincagem-leitor/', '/produtor/brincagem-bastao/', '/produtor/troca-rfid/', '/produtor/linkagem-rfid/', '/produtor/pesos-leitor/', '/produtor/pesos-bastao/',
    '/produtor/brincagem-consulta/alterar/',
    '/produtor/brincagem-sequencial/',
    '/produtor/reidentificacao/',
    '/produtor/alterar-dados-animais/',
    '/produtor/gta-manual/', '/produtor/entrada/compra/', '/produtor/vincular-gta/',
    '/produtor/comunicado-entrada/', '/produtor/impressao-comunicado/',
    '/produtor/notificacao-nascimento/',
    '/produtor/gta-consulta/editar/', '/produtor/gta-consulta/salvar-edicao/',
    '/produtor/brincos-entrada/',
    '/produtor/brincos-cancelamento/iniciar', '/produtor/brincos-cancelamento/nova',
    '/produtor/brincos-cancelamento/confirmar', '/produtor/brincos-cancelamento/salvar',
    '/produtor/parceiros/novo', '/produtor/parceiro-manual', '/produtor/frigorificos/novo',
    '/produtor/usuarios/novo', '/produtor/usuarios/editar/',
    '/propriedades/editar/', '/propriedades/nova',
    '/proprietarios/editar/', '/proprietarios/novo',
    '/produtores/editar/', '/produtores/novo',
)

# POST que so LE (gera relatorio): vale com Consulta.
POST_SO_LEITURA = {
    '/produtor/brincos-relatorio-resumo/gerar',
}


def modulo_do_caminho(caminho):
    """Devolve o modulo de um caminho /produtor/... (ou das telas do Produtor
    fora dele, ver MODULO_POR_PREFIXO_FORA), ou None se nao esta registrado."""
    if not caminho:
        return None
    if caminho in MODULO_POR_CAMINHO_EXATO:
        return MODULO_POR_CAMINHO_EXATO[caminho]
    if not caminho.startswith('/produtor/'):
        primeiro_fora = caminho.strip('/').split('/')[0]
        return MODULO_POR_PREFIXO_FORA.get(primeiro_fora)
    partes = [p for p in caminho[len('/produtor/'):].split('/') if p]
    if not partes:
        return None
    primeiro = partes[0]
    if primeiro in ('hub', 'hub-novo'):
        if len(partes) < 2:
            return None
        return MODULO_POR_SLUG_HUB.get(partes[1])
    if primeiro.startswith(PREFIXO_BRINCOS):
        return 'brincos'
    return MODULO_POR_SEGMENTO.get(primeiro)


def nivel_exigido(metodo, caminho):
    """Nivel minimo que a requisicao pede."""
    metodo = (metodo or 'GET').upper()
    if (metodo, caminho) in ACOES_SENSIVEIS:
        return TUDO
    if metodo == 'POST' and caminho in POST_SO_LEITURA:
        return CONSULTA
    if metodo in ('GET', 'HEAD', 'OPTIONS'):
        if caminho in GETS_QUE_GRAVAM or caminho.startswith(TELAS_DE_LANCAMENTO):
            return LANCA
        return CONSULTA
    return LANCA


def nivel_padrao(cargo, modulo):
    """Valor inicial de cada cargo em cada modulo (sem ajuste do Titular)."""
    if cargo == 'TITULAR':
        return TUDO
    if modulo == PAINEL:
        return CONSULTA if cargo in CARGOS_CAMPO else TUDO
    if cargo in CARGOS_CAMPO:
        return TUDO if modulo in ('brincagem', 'pesagens', 'consulta_manejo', 'alterar_dados') else SEM_ACESSO
    if cargo in CARGOS_ESCRITORIO:
        # v1.4.0 - decisao do Benedito: Gerente/Capataz e Veterinario NAO acessam Entrada.
        if modulo == 'entrada' and cargo in ('GERENTE_CAPATAZ', 'VETERINARIO_ZOOTECNISTA'):
            return SEM_ACESSO
        if modulo == 'equipe':
            return TUDO if cargo == 'ADMINISTRADOR' else SEM_ACESSO
        return TUDO
    return SEM_ACESSO


def nivel_efetivo(cargo, modulo, ajustes=None):
    """Nivel valendo: ajuste do Titular, senao o padrao. Titular e
    sempre TUDO; o Painel e sempre CONSULTA no minimo."""
    if cargo == 'TITULAR':
        return TUDO
    nivel = None
    if ajustes:
        nivel = ajustes.get((cargo, modulo))
    if nivel is None:
        nivel = nivel_padrao(cargo, modulo)
    if modulo == PAINEL and nivel < CONSULTA:
        nivel = CONSULTA
    return nivel


def autorizado(cargo, metodo, caminho, ajustes=None):
    """Decisao completa. Devolve (liberado, modulo). Modulo None = endereco
    sem registro (so o Titular passa)."""
    modulo = modulo_do_caminho(caminho)
    if modulo is None:
        return (cargo == 'TITULAR', None)
    alternativos = MODULOS_ALTERNATIVOS_POR_CAMINHO.get(caminho)
    if alternativos:
        return (any(nivel_efetivo(cargo, m, ajustes) >= CONSULTA for m in alternativos), modulo)
    if modulo == PAINEL:
        exigido = CONSULTA
    else:
        exigido = nivel_exigido(metodo, caminho)
    return (nivel_efetivo(cargo, modulo, ajustes) >= exigido, modulo)

# -------------------------------------------------------
# TELA DE PERMISSOES (Etapa 2, v1.2.0)
# -------------------------------------------------------
MODULOS_DA_TELA = (
    'brincagem', 'brincagem_sequencial', 'consulta_manejo', 'alterar_dados',
    'entrada', 'brincos', 'inventario', 'parceiros', 'propriedade',
    'utilitarios', 'equipe',
)
CARGOS_DA_TELA = (
    'ADMINISTRADOR', 'ADMINISTRATIVO', 'GERENTE_CAPATAZ',
    'VETERINARIO_ZOOTECNISTA', 'CAMPEIRO', 'AUXILIAR',
)
NOMES_CARGO = {
    'ADMINISTRADOR': 'Administrador', 'ADMINISTRATIVO': 'Administrativo',
    'GERENTE_CAPATAZ': 'Gerente / Capataz',
    'VETERINARIO_ZOOTECNISTA': 'Veterin\u00e1rio / Zootecnista',
    'CAMPEIRO': 'Campeiro', 'AUXILIAR': 'Auxiliar',
}
NOMES_NIVEL_TELA = {SEM_ACESSO: 'Sem acesso', CONSULTA: 'Consulta', LANCA: 'Lan\u00e7a', TUDO: 'Tudo'}

# Opcoes que fazem sentido em cada modulo (Tudo so onde existe excluir/desfazer/backup;
# Consulta so onde ha telas de consulta).
NIVEIS_DO_MODULO = {
    'brincagem':            (SEM_ACESSO, CONSULTA, LANCA, TUDO),
    'brincagem_sequencial': (SEM_ACESSO, LANCA),
    'consulta_manejo':      (SEM_ACESSO, CONSULTA),
    'alterar_dados':        (SEM_ACESSO, LANCA),
    'entrada':              (SEM_ACESSO, CONSULTA, LANCA),
    'brincos':              (SEM_ACESSO, CONSULTA, LANCA),
    'inventario':           (SEM_ACESSO, CONSULTA),
    'parceiros':            (SEM_ACESSO, CONSULTA, LANCA),
    'propriedade':          (SEM_ACESSO, CONSULTA, LANCA),
    'utilitarios':          (SEM_ACESSO, CONSULTA, LANCA, TUDO),
    'equipe':               (SEM_ACESSO, TUDO),
}
DESCRICAO_MODULO = {
    'brincagem':            'Leitor, Bast\u00e3o, Troca de RFID e Consulta Brincagem (Tudo = excluir registro)',
    'brincagem_sequencial': 'Brincagem Sequencial (tela de escrit\u00f3rio)',
    'consulta_manejo':      'Consulta por Manejo e Consulta de Animal e Brinco',
    'alterar_dados':        'Alterar Dados dos Animais',
    'entrada':              'GTA, Compra, Comunicados, Notifica\u00e7\u00e3o de Nascimento, PIA e Relat\u00f3rio ERAS e Ra\u00e7as da Fazenda',
    'brincos':              'Entrada, Dispon\u00edveis, Cancelamento, Sa\u00eddas e Relat\u00f3rios de brincos',
    'inventario':           'Invent\u00e1rio Geral',
    'parceiros':            'Parceiros e Fornecedores',
    'propriedade':          'Minha Propriedade, Propriet\u00e1rios, Produtores e Auditorias ERAS',
    'utilitarios':          'Opera\u00e7\u00f5es recentes e Backup (Tudo = desfazer e backup)',
    'equipe':               'Equipe da Propriedade e Permiss\u00f5es',
}


def nivel_para_tela(modulo, nivel):
    """Maior opcao oferecida pelo modulo que nao passa do nivel dado (o que a
    tela mostra; Tudo num modulo sem acao sensivel aparece como Lanca)."""
    opcoes = NIVEIS_DO_MODULO[modulo]
    validos = [o for o in opcoes if o <= nivel]
    return max(validos) if validos else opcoes[0]


def pode_editar_celula(papel, cargo, modulo):
    """Quem ajusta o que. papel = TITULAR ou ADMINISTRADOR (quem esta na tela).
    - Equipe: so o Titular decide, e so para o Administrador (os demais cargos nao
      gerem a equipe, regra do produtor_usuarios.py).
    - Coluna Administrador: so o Titular mexe (o Administrador nao mexe na propria).
    - Demais: Titular e Administrador."""
    if cargo not in CARGOS_DA_TELA or modulo not in MODULOS_DA_TELA:
        return False
    if modulo == 'equipe':
        return papel == 'TITULAR' and cargo == 'ADMINISTRADOR'
    if cargo == 'ADMINISTRADOR':
        return papel == 'TITULAR'
    return papel in ('TITULAR', 'ADMINISTRADOR')

# =========================================================
# FIM DE ARQUIVO: backend\utils\permissoes.py
# =========================================================
