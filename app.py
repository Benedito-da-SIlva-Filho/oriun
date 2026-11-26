# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion
# MODULO:       app.py
# AUTOR:        Benedito Silva Filho
# CRIADO EM:    2026-06-20 19:49 -03
# ATUALIZADO EM: 2026-11-26 17:15 -03
# VERSAO: 1.61.0
#
# DESCRICAO:
#     Arquivo principal do Orion.
#     Inicializa o Flask e registra as rotas.
#     v1.0.0: Criacao do modulo.
#     v1.1.0: Registro do blueprint de autenticacao.
#     v1.2.0: Flask-Mail inicializado via extensions.py.
#     v1.3.0: Sessao 011 - Registrado o blueprint protocolos
#             (administracao do catalogo de Protocolos de
#             Certificacao - ABPO, PEFB, CSCB, Cota Hilton,
#             e futuros). Import de Protocolo adicionado a
#             lista de models carregados na inicializacao.
#     v1.4.0: Sessao 011.1 - Registrado o blueprint
#             proprietarios (CRUD de Proprietario - dono
#             legal da terra). Import de Proprietario
#             adicionado a lista de models carregados na
#             inicializacao. Model e tabela ja existiam
#             desde a Sessao 010; faltava so o blueprint.
#     v1.5.0: Sessao 011.1 - Registrado o blueprint
#             produtores (CRUD de Produtor - quem opera o
#             rebanho). Model Produtor ja estava na lista de
#             import (usado por outros models via
#             relationship), so faltava o blueprint em si -
#             erro real em producao: BuildError 'Could not
#             build url for endpoint produtores.novo'.
#     v1.6.0: Sessao 011.2 - Configuracao de upload de
#             arquivos (logo de Marca/Criador do Produtor,
#             P-020). Pasta frontend/static/uploads/produtores
#             criada automaticamente na inicializacao, caso
#             ainda nao exista. MAX_CONTENT_LENGTH definido em
#             10MB como teto de seguranca contra uploads
#             acidentalmente grandes - nao afeta uso normal,
#             uma logo tipica fica entre 50KB e 2MB.
#     v1.7.0: Sessao do dia 08/07/2026 - Registrado o
#             blueprint consultas (telas somente leitura:
#             Produtor -> Propriedades e Propriedade ->
#             Produtores, ambas so com vinculos ativos).
#             Nao precisou de nenhum import novo na lista de
#             models - Propriedade e Produtor ja estavam
#             carregados aqui, e PropriedadeProdutor ja e
#             importado dentro do proprio backend/models/__init__.py.
#     v1.8.0: Sessao 032 - Registrado o blueprint convite
#             (fluxo de Convite Publico, /convite - Etapa 1
#             implementada: CPF/CNPJ, Nome, Email, Telefone,
#             honeypot, rate limit, validacao via novo
#             backend/utils/validadores.py). Nao precisou de
#             nenhum import novo na lista de models - Produtor
#             ja estava carregado aqui (usado pela checagem de
#             duplicidade de cpf_cnpj dentro de convite.py).
#     v1.9.0: Sessao 034 (continuacao, 07/08/2026) - Registrado
#             o blueprint produtor_usuarios (tela "Meu Usuario" -
#             gestao da propria equipe pelo Produtor logado,
#             restrito a cargos TITULAR/ADMINISTRADOR do vinculo).
#             Fecha a Frente B do lado Produtor - o lado CONSISTE
#             (blueprint usuarios, ja registrado desde v1.x
#             anterior) ganhou suporte a multi-perfil na mesma
#             sessao (usuarios.py v1.8.0), sem mudanca aqui no
#             app.py (blueprint ja existia, so o conteudo do
#             arquivo mudou). Nao precisou de nenhum import novo
#             na lista de models - Usuario e UsuarioVinculo ja
#             sao importados dentro do proprio
#             backend/models/__init__.py.
#     v1.10.0: Sessao 034 (continuacao 6, 11/08/2026, 19:33 -03) -
#             Registrado o blueprint prospects (Convite de
#             Prospects - Consiste convida Produtores prospects
#             por e-mail, reaproveitando o link fixo do Convite
#             Publico ja existente). Nao precisou de nenhum
#             import novo na lista de models aqui no app.py -
#             ConviteProspect e importado dentro do proprio
#             backend/models/__init__.py (v1.16.0).
#     v1.11.0: Sessao 045 (03/09/2026, 09:22 -03) - Registrado o
#             blueprint brincos_cancelamento (modulo Cancelamento
#             de Brincos, 6o card do Hub de Brincos). Nao precisou
#             de nenhum import novo na lista de models aqui no
#             app.py - BrincoEntrada, BrincoSaida e
#             EntradaBrincoRfid sao importados dentro do proprio
#             backend/routers/brincos_cancelamento.py.
#     v1.12.0: Sessao 045 (03/09/2026, 11:32 -03) - Registrado o
#             blueprint brincos_saidas (modulo Brincos Saidas, 7o e
#             ULTIMO card do Hub de Brincos - HUB COMPLETO). Nao
#             precisou de nenhum import novo na lista de models
#             aqui no app.py - BrincoEntrada e BrincoSaida sao
#             importados dentro do proprio backend/routers/
#             brincos_saidas.py, que tambem reaproveita
#             MOTIVOS_CANCELAMENTO de brincos_cancelamento.py.
#     v1.13.0: Sessao 045 (03/09/2026, 15:30 -03) - Registrado o
#             blueprint operacoes_recentes (modulo "Operações
#             Recentes", tela central do mecanismo Desfazer por
#             Operacao/Log de Operacoes - novo Hub de Utilitarios).
#             Nao precisou de nenhum import novo na lista de models
#             aqui no app.py - LogOperacao, Propriedade, Produtor e
#             Usuario ja importados dentro do proprio backend/
#             routers/operacoes_recentes.py.
#     v1.14.0: Sessao 046 (04/09/2026, 13:40 -03) - Registrado o
#             blueprint backup_restore (mecanismo de Backup/Restore
#             de Schema inteiro do Produtor, via pg_dump/pg_restore
#             reais - 2o card do Hub de Utilitarios + tela nova do
#             Consiste em /consiste/backup-restore). Nao precisou de
#             nenhum import novo na lista de models aqui no app.py -
#             BackupRestorePedido, Produtor e Usuario ja importados
#             dentro do proprio backend/routers/backup_restore.py.
#     v1.15.0: Sessao 055 (17/09/2026, 10:30 -03) - Registrado o
#             blueprint relatorio_eras (Relatorio de ERAS, card do
#             sub-hub 'entrada-consultas'). Nao precisou de nenhum
#             import novo na lista de models aqui no app.py -
#             Entrada, IdadeMeses, Propriedade e Produtor ja
#             importados dentro do proprio backend/routers/
#             relatorio_eras.py.
#     v1.16.0: Sessao 077 (22/09/2026, 13:55 -03) - Registrado o
#             blueprint brincagem_bastao (modulo Brincagem com
#             Bastao - mesma estrutura da Brincagem com Leitor,
#             com a etapa extra de RFID). Nao precisou de nenhum
#             import novo na lista de models aqui no app.py -
#             Entrada, Brincagem, RejeicaoBrincagem, Pia e Raca
#             ja importados dentro do proprio backend/routers/
#             brincagem_bastao.py. BUG REAL corrigido nesta
#             sessao: o card "Brincagem com Bastão" (hubs.py
#             v1.30.0) ja apontava para 'brincagem_bastao.iniciar',
#             mas o blueprint nunca tinha sido registrado aqui -
#             BuildError ao abrir o Hub de Brincagem. Registrado
#             logo apos brincagem_consulta, mesma posicao dos
#             modulos irmaos de Brincagem.
#     v1.17.0: Sessao 077 cont. (22/09/2026, 18:30 -03) -
#             Registrado o blueprint vincular_gta (modulo novo -
#             junta os animais ja brincados no curral com a GTA
#             correspondente). Nao precisou de nenhum import novo
#             na lista de models aqui no app.py - todos os models
#             usados ja sao importados dentro do proprio
#             backend/routers/vincular_gta.py.
#     v1.18.0: Sessao 079 (24/09/2026, 11:15 -03) - Registrado o
#             blueprint inventario_geral (modulo Inventario Geral -
#             1o card do novo Hub de Inventario, hubs.py v1.32.0).
#             Registrado ANTES de o Hub ser aberto no navegador
#             (licao do BuildError da v1.16.0: card apontando para
#             blueprint nao registrado). Nao precisou de nenhum
#             import novo na lista de models aqui no app.py - todos
#             ja importados dentro do proprio backend/routers/
#             inventario_geral.py.
#     v1.19.0: Sessao 080 (25/09/2026, 10:55 -03) - Registrado o
#             blueprint pia_impressao (PIA - Anexo XXIII, sub-hub
#             'entrada-pia' do Hub de Entrada, hubs.py v1.33.0).
#             Registrado junto com a criacao dos cards (licao do
#             BuildError da v1.16.0). Nenhum import novo na lista de
#             models aqui - todos importados dentro do proprio
#             backend/routers/pia_impressao.py.
#     v1.20.0: Sessao 081 (28/09/2026, 20:55 -03) - Registrado o
#             blueprint brincagem_nascimento (Brincagem de
#             Nascimento/Desmame - aberta pelo botao "Nascimento /
#             Desmame" da Lista da Brincagem Sequencial, mesmo card
#             do Hub de Entrada). Registrado logo apos
#             brincagem_sequencial (modulo irmao, do qual importa 2
#             funcoes). Nenhum import novo na lista de models aqui -
#             todos importados dentro do proprio backend/routers/
#             brincagem_nascimento.py.
#     v1.21.0: Sessao 084 (02/10/2026, 10:00 -03) - Registrado o
#             blueprint notificacao_nascimento (Notificacao de
#             Nascimentos - Impressao e Reimpressao, card do sub-hub
#             'entrada-nascimento', hubs.py v1.37.0). Registrado junto
#             com o card (licao do BuildError da v1.16.0). Nenhum
#             import novo na lista de models aqui - todos importados
#             dentro do proprio backend/routers/notificacao_nascimento.py.
#     v1.22.0: Sessao 084 (02/10/2026, 17:00 -03) - Registrado o blueprint
#             nascimentos_periodo (relatorio Nascimentos por Periodo, card
#             do sub-hub 'entrada-nascimento', hubs.py v1.39.0). Nenhum
#             import novo na lista de models aqui.
#     v1.23.0: Sessao 085 (04/10/2026, 14:10 -03) - Registrado o blueprint
#             consulta_manejo (Consulta por Manejo - 1 card no Hub de Entrada
#             e 1 no Hub de Brincagem, hubs.py v1.41.0). Registrado junto com
#             os cards (licao do BuildError da v1.16.0). Nenhum import novo
#             na lista de models aqui - todos importados dentro do proprio
#             backend/routers/consulta_manejo.py.
#     v1.24.0: Sessao 087 (05/10/2026, 20:35 -03) - Registrado o blueprint
#             alterar_dados_animais (Alterar Dados dos Animais - 1 card no Hub de
#             Brincagem e 1 no Hub de Entrada, hubs.py v1.42.0). Registrado junto
#             com os cards (licao do BuildError da v1.16.0). Nenhum import novo na
#             lista de models aqui - todos importados dentro do proprio
#             backend/routers/alterar_dados_animais.py.
#     v1.25.0: Sessao 088 (06/10/2026, 11:25 -03) - Registrado o blueprint
#             hub_entrada_agrupado (Hub de Entrada NOVO, layout agrupado, rota
#             paralela /produtor/hub-novo/entrada). Registrado junto com o
#             sub-hub 'entrada-comunicados' em hubs.py v1.43.0 (licao do
#             BuildError da v1.16.0). Nenhum import novo na lista de models
#             aqui - o novo router nao acessa banco.
#     v1.25.1: Sessao 088 (06/10/2026, 12:10 -03) - Corrigido o carimbo de sessao
#             da v1.25.0 (era "087 cont.", o certo e 088). So texto de
#             comentario - nenhuma mudanca de codigo.
#     v1.26.0: Sessao 089 (07/10/2026, 12:05 -03) - Registrado o blueprint
#             auditoria_eras (Auditorias ERAS: vistorias das Propriedades com
#             codigo ERAS, rotas /produtor/auditoria-eras). Usa os models novos
#             AuditoriaEras e LogAuditoriaEras (models v1.18.0) - rodar antes o
#             SQL Tabelas/criar_tb_auditoria_eras.sql.
#     v1.27.0: Sessao 092 (09/10/2026, 16:10 -03) - Registrado o blueprint troca_rfid
#             (Troca de RFID - 1 card no Hub de Brincagem novo, hub_entrada_agrupado.py
#             v1.9.0). Registrado junto com o card (licao do BuildError da v1.16.0).
#             Nenhum import novo na lista de models aqui - todos importados dentro do
#             proprio backend/routers/troca_rfid.py. Nao precisa de SQL.
#     v1.28.0: Sessao 092 (09/10/2026, 19:05 -03) - Registrado o blueprint
#             consiste_blockchain (menu Consiste > Blockchain: tabela-resumo por
#             Produtor + validacao do blockchain, so leitura, so perfil CONSISTE;
#             rotas /consiste/blockchain e /consiste/blockchain/relatorio.txt).
#             Registrado junto com o item de menu (consiste_menu.html v1.7.0).
#             Nao precisa de SQL.
#     v1.29.0: Sessao 097 (15/10/2026, 10:05 -03) - Registrado o blueprint
#             permissoes (PORTEIRO de permissoes por cargo: barra enderecos
#             /produtor/... conforme o cargo; ajudante pode_ver() para os
#             templates). Rodar antes o SQL Tabelas/criar_tb_permissao_cargo.sql
#             (sem a tabela vale o padrao de cada cargo, nada quebra).
#     v1.30.0: Sessao 097 (15/10/2026, 11:50 -03) - Registrado o blueprint
#             produtor_permissoes (Etapa 2: tela de Permissoes por Cargo dentro da
#             Equipe, rotas /produtor/usuarios/permissoes). Registrado junto com o
#             link na lista da Equipe (usuario_lista.html v1.5.0). Sem SQL novo.
#     v1.31.0: Sessao 098 (16/10/2026, 20:20 -03) - Registra o blueprint saida_leitor (Leitor do Abate).
#     v1.32.0: Sessao 099 (17/10/2026, 12:35 -03) - Registra o blueprint saida_bastao (Leitor do Abate com Bastao).
#     v1.33.0: Sessao 099 (17/10/2026, 14:50 -03) - Registra o blueprint frigorificos (cadastro e consulta de Frigorificos).
#     v1.34.0: Sessao 099 (17/10/2026, 15:00 -03) - Registra o blueprint gta_saida (Cadastro de GTA de Saida).
#     v1.35.0: Sessao 099 (17/10/2026, 15:30 -03) - Registra o blueprint saida_relatorio (Relatorio de Embarque).
#     v1.36.0: Sessao 099 (17/10/2026, 17:15 -03) - Registra o blueprint saida_consulta (Consulta Embarque).
#     v1.37.0: Sessao 100 (19/10/2026, 16:50 -03) - Registra o blueprint saida_vincular (Vincular GTA / Embarque).
#     v1.38.0: Sessao 100 (19/10/2026, 20:40 -03) - Registra o blueprint saida_substituicao (Substituicao de Animal).
#     v1.39.0: Sessao 101 (20/10/2026, 09:22 -03) - Registra o blueprint saida_gta_consulta (Consulta GTA de Saida).
#     v1.40.0: Sessao 101 (20/10/2026, 10:47 -03) - Registra o blueprint saida_comunicado (Gerar Comunicado de Saida, Pacote 1).
#     v1.41.0: Sessao 101 (20/10/2026, 12:15 -03) - Registra o blueprint saida_impressao (Impressao e Reimpressao do Comunicado de Saida, Pacote 2).
#     v1.42.0: Sessao 102 (21/10/2026, 12:20 -03) - Registra o blueprint consulta_animal (Consulta de Animal e Brinco, item do menu lateral).
#     v1.43.0: Sessao 102 (2026-10-21 12:35 -03) - Registra o blueprint saida_troca_comunicado (Troca de Animal depois do Comunicado, Pacote 3).
#     v1.44.0: Sessao 102 (2026-10-21 17:40 -03) - Registra o blueprint saida_arquivo (Abate por Arquivo Texto).
#     v1.45.0: Sessao 104 (2026-10-23 11:35 -03) - SEGURANCA (auditoria): cookie de sessao HttpOnly + SameSite=Lax (+ Secure quando
#         COOKIE_SECURE=True no .env, para quando houver HTTPS) e BARREIRA CONTRA CSRF: POST/PUT/PATCH/DELETE com Origin/Referer de OUTRO
#         endereco e recusado (403). Sem Origin e sem Referer passa (ferramentas internas). REVERSAO: .bak_antes_s104f.
#     v1.46.0: Sessao 107 (2026-10-28 09:40 -03) - Registra o blueprint transferencia (Leitor da Transferencia e Leitor da Transferencia com Bastao). REVERSAO: .bak_antes_s107.
#     v1.47.0: Sessao 110 (2026-10-31 11:51 -03) - Registra o blueprint transferencia_arquivo (Transferencia por Arquivo Texto). REVERSAO: .bak_antes_s110_transf_arquivo.
#     v1.49.0: Sessao 114 (2026-11-04 11:20 -03) - Registra o blueprint pesos_leitor (Leitor de Peso e Inconformes).  REVERSAO: .bak_antes_s114_pesos.
#     v1.57.0: Sessao 129 (2026-11-17 11:30 -03) - Registra o blueprint pesos_relatorios (Relatorios de Pesagem em PDF). REVERSAO: .bak_antes_s129_pesos_relatorios.
#     v1.59.0: Sessao 133 (2026-11-19 11:10 -03) - Celular: after_request "_injetar_mobile" coloca orion_mobile.css/.js (static) e o viewport em TODAS as telas HTML, sem mexer nos templates. REVERSAO: .bak_antes_s133_mobile.
#     v1.60.0: Sessao 133 (2026-11-19 12:40 -03) - Servidor: .env ganha TRUST_PROXY=True (Orion atras de proxy HTTPS: enxerga https e o dominio certo, necessario para cookie seguro e barreira CSRF), ORION_HOST (padrao 0.0.0.0; atras de proxy usar 127.0.0.1) e ORION_PORT (padrao 5001). Sem essas linhas tudo funciona como antes.
#     v1.61.0: Sessao 137 (2026-11-26 17:15 -03) - Icone/aplicativo instalavel (PWA): rotas /manifest.webmanifest e /orion-sw.js e, na _injetar_mobile, manifesto, cor do tema, icone do iPhone e orion_pwa.js em TODAS as telas HTML, sem mexer nos templates. Icone A1 (cinturao de Orion com sinal de satelite), nome "Orion". Nada fica em cache. REVERSAO: .bak_antes_s137_pwa.
#     v1.51.0: Sessao 114 (2026-11-04 19:00 -03) - Registra o blueprint pesos_consulta (Consulta de Peso e Conferidos).  REVERSAO: .bak_antes_s114_consulta.
#     v1.50.0: Sessao 114 (2026-11-04 14:50 -03) - Registra o blueprint pesos_bastao (Leitor de Peso com Bastao).  REVERSAO: .bak_antes_s114_bastao.
#     v1.52.0: Sessao 115 (2026-11-05 13:45 -03) - Registra o blueprint posse (Leitor da Alteracao de Posse e com Bastao).  REVERSAO: .bak_antes_s115_posse_pacote2.
#     v1.55.0: Sessao 121 (2026-11-11 14:20 -03) - Registra os blueprints reidentificacao e reidentificacao_consulta (Reidentificacao de animais).  REVERSAO: .bak_antes_s121_reidentificacao.
#     v1.56.0: Sessao 122 (2026-11-12 13:55 -03) - Auditoria Etapa 1: (a) errorhandler para Produtor inativo/nao migrado (antes: erro 500 em toda tela); (b) para de subir se SECRET_KEY faltar. REVERSAO: .bak_antes_s122_etapa1.
#     v1.54.0: Sessao 120 (2026-11-10 21:50 -03) - Registra o blueprint linkagem_consulta (Consulta, Relatorio PDF e Inconformidades da Linkagem, pacote 2).  REVERSAO: .bak_antes_s120_pacote2.
#     v1.53.0: Sessao 120 (2026-11-10 18:40 -03) - Registra o blueprint linkagem_rfid (Linkagem RFID e Brinco, pacote 1).  REVERSAO: .bak_antes_s120_linkagem.
# =========================================================

from flask import Flask, request, abort, session
from urllib.parse import urlparse
from dotenv import load_dotenv
import os

# Carrega as variaveis do arquivo .env
load_dotenv()

# Testa a conexao com o banco ao iniciar
from backend.database import testar_conexao
testar_conexao()

# Importa os models
from backend.models import Certificadora, Propriedade, Produtor, Usuario, Protocolo, Proprietario
print('Models carregados: OK!')

# Cria a aplicacao Flask
app = Flask(__name__,
    template_folder='frontend/templates',
    static_folder='frontend/static'
)

# Configuracoes basicas
app.secret_key = os.getenv('SECRET_KEY')
if not app.secret_key:   # v1.56.0 - sem a chave a sessao nao funciona: para aqui, com mensagem clara
    raise RuntimeError('SECRET_KEY nao definida no arquivo .env (pasta C:\\Orion). Abra o .env, confira se existe a linha SECRET_KEY=... e inicie o Orion de novo.')
app.config['DEBUG'] = os.getenv('DEBUG', 'False') == 'True'

# v1.45.0 - Cookie de sessao mais seguro (auditoria da Sessao 104)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('COOKIE_SECURE', 'False') == 'True'   # ligar so quando o sistema rodar em HTTPS

# v1.60.0 - Atras de proxy HTTPS (Caddy/IIS/nginx): confia nos cabecalhos X-Forwarded-* de UM proxy (so liga com TRUST_PROXY=True no .env)
if os.getenv('TRUST_PROXY', 'False') == 'True':
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)


# v1.45.0 - Barreira contra CSRF: pedido que ALTERA dados (POST/PUT/PATCH/DELETE) vindo de outro site e recusado.
# Compara o endereco de origem (Origin ou Referer) com o endereco que o usuario usou para chegar aqui.
# Sem Origin e sem Referer, deixa passar (nao e navegador comum).
@app.before_request
def _barreira_csrf():
    if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
        return None
    origem = request.headers.get('Origin') or request.headers.get('Referer')
    if not origem or origem == 'null':
        return None
    try:
        endereco_origem = urlparse(origem).netloc.lower()
    except Exception:
        return None
    if endereco_origem and endereco_origem != (request.host or '').lower():
        print(f'CSRF: pedido recusado {request.method} {request.path} origem={endereco_origem} host={request.host}')
        abort(403)
    return None


# v1.56.0 - Produtor inativo / nao migrado / nao encontrado: em vez de erro 500, mostra aviso claro (403).
#     v1.56.1: Sessao 122 (2026-11-12 14:25 -03) - Auditoria Etapa 1: pagina "Acesso indisponivel" agora mostra usuario, Produtor, tela e data/hora e diz o que fazer; mensagem da SECRET_KEY diz onde conferir. REVERSAO: .bak_antes_s122_msgs.
# Vale para as telas que abrem o banco do Produtor (get_db_produtor). Pedido que espera JSON recebe JSON.
from flask import jsonify
from backend.utils.multitenant import ProdutorInativo, ProdutorNaoMigrado, ProdutorNaoEncontrado, SchemaNomeInvalido

@app.errorhandler(ProdutorInativo)
@app.errorhandler(ProdutorNaoMigrado)
@app.errorhandler(ProdutorNaoEncontrado)
@app.errorhandler(SchemaNomeInvalido)
def _produtor_indisponivel(erro):
    print(f'PRODUTOR INDISPONIVEL: {request.method} {request.path} - {erro}')
    if isinstance(erro, ProdutorInativo):
        msg = 'O cadastro deste Produtor esta inativo. Os dados estao preservados. Fale com a Consiste para reativar.'
    else:
        msg = 'O cadastro deste Produtor ainda nao esta pronto para uso. Fale com a Consiste.'
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest' \
            or request.accept_mimetypes.best == 'application/json':
        return jsonify({'ok': False, 'erro': 'produtor_indisponivel', 'mensagem': msg}), 403
    # v1.56.1 - pagina com orientacao: quem tentou, qual Produtor, qual tela e quando (para o usuario informar a Consiste)
    import html as _html
    from datetime import datetime as _dt
    nome_produtor = '-'
    try:
        from sqlalchemy.orm import Session as _Sessao
        from backend.database import engine as _engine
        with _Sessao(_engine) as _db:
            _p = _db.get(Produtor, session.get('id_produtor')) if session.get('id_produtor') else None
            nome_produtor = _p.nome if _p else '-'
    except Exception:
        pass
    def _esc(v): return _html.escape(str(v or '-'))
    quadro = ('<table style="margin:14px auto;text-align:left;font-size:14px;color:#333">'
              '<tr><td style="padding:3px 12px 3px 0;color:#666">Usuario</td><td>' + _esc(session.get('usuario_nome')) + '</td></tr>'
              '<tr><td style="padding:3px 12px 3px 0;color:#666">Produtor</td><td>' + _esc(nome_produtor) + '</td></tr>'
              '<tr><td style="padding:3px 12px 3px 0;color:#666">Tela</td><td>' + _esc(request.path) + '</td></tr>'
              '<tr><td style="padding:3px 12px 3px 0;color:#666">Data e hora</td><td>' + _dt.now().strftime('%d/%m/%Y %H:%M') + '</td></tr></table>')
    pagina = ('<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><title>Orion SISBOV</title></head>'
              '<body style="font-family:Arial,sans-serif;background:#f5f5f5;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0">'
              '<div style="background:#fff;border-radius:10px;padding:32px;max-width:500px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.15)">'
              '<h2 style="color:#D4370A;margin-top:0">Acesso indisponivel</h2>'
              '<p style="color:#333">' + msg + '</p>' + quadro +
              '<p style="color:#666;font-size:13px">O que fazer: anote ou tire um print desta tela e envie para a Consiste. Os dados do Produtor continuam guardados.</p>'
              '<a href="/logout" style="display:inline-block;margin-top:8px;background:#D4370A;color:#fff;padding:10px 22px;border-radius:6px;text-decoration:none">Sair</a>'
              '</div></body></html>')
    return pagina, 403


# -------------------------------------------------------
# Configuracao de Upload de Arquivos
# (logo de Marca/Criador do Produtor - P-020)
# -------------------------------------------------------
# Teto de seguranca contra uploads acidentalmente grandes.
# Nao e uma restricao de uso normal - so protege o servidor
# de um arquivo enorme enviado por engano.
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

# Garante que a pasta de destino das logos existe ANTES do
# sistema subir - se nao existisse, o primeiro upload real
# quebraria com erro de pasta nao encontrada.
PASTA_UPLOAD_PRODUTORES = os.path.join(app.static_folder, 'uploads', 'produtores')
os.makedirs(PASTA_UPLOAD_PRODUTORES, exist_ok=True)
print('Pasta de upload de Produtores: OK!')

# -------------------------------------------------------
# Configuracoes do Flask-Mail
# -------------------------------------------------------
app.config['MAIL_SERVER']   = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT']     = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS']  = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Inicializa o Flask-Mail
from backend.extensions import mail
mail.init_app(app)
print('Flask-Mail inicializado: OK!')

# -------------------------------------------------------
# Registra os blueprints (rotas)
# -------------------------------------------------------
from backend.routers.auth import auth
app.register_blueprint(auth)

from backend.routers.certificadoras import certificadoras
app.register_blueprint(certificadoras)

from backend.routers.usuarios import usuarios
app.register_blueprint(usuarios)

from backend.routers.cert_usuarios import cert_usuarios
app.register_blueprint(cert_usuarios)

from backend.routers.busca_cpf_cnpj import busca_cpf_cnpj
app.register_blueprint(busca_cpf_cnpj)

from backend.routers.propriedades import propriedades
app.register_blueprint(propriedades)
print('Rotas de Busca Propriedades: OK!')

from backend.routers.protocolos import protocolos
app.register_blueprint(protocolos)
print('Rotas de Protocolos: OK!')

from backend.routers.proprietarios import proprietarios
app.register_blueprint(proprietarios)
print('Rotas de Proprietarios: OK!')

from backend.routers.produtores import produtores
app.register_blueprint(produtores)
print('Rotas de Produtores: OK!')

from backend.routers.consultas import consultas
app.register_blueprint(consultas)
print('Rotas de Consultas: OK!')

from backend.routers.gta_compra import gta_compra
app.register_blueprint(gta_compra)
print('Rotas de GTA Compra: OK!')

from backend.routers.convite import convite
app.register_blueprint(convite)
print('Rotas de Convite Publico: OK!')

from backend.routers.produtor_usuarios import produtor_usuarios
app.register_blueprint(produtor_usuarios)
print('Rotas de Usuarios Produtor (Minha Equipe): OK!')

from backend.routers.prospects import prospects
app.register_blueprint(prospects)
print('Rotas de Convite de Prospects: OK!')

from backend.routers.vitrine_visitantes import vitrine_visitantes
app.register_blueprint(vitrine_visitantes)
print('Rotas de Vitrine Visitantes: OK!')

from backend.routers.hubs import hubs
app.register_blueprint(hubs)
print('Rotas de Hubs: OK!')

from backend.routers.permissoes import permissoes
app.register_blueprint(permissoes)
print('Porteiro de Permissoes: OK!')

from backend.routers.produtor_permissoes import produtor_permissoes
app.register_blueprint(produtor_permissoes)
print('Tela de Permissoes por Cargo: OK!')

from backend.routers.parceiros_fornecedores import parceiros_fornecedores
app.register_blueprint(parceiros_fornecedores)
print('Rotas de Parceiros/Fornecedores: OK!')

from backend.routers.busca_municipio import busca_municipio
app.register_blueprint(busca_municipio)
print('Municípios: OK!')

from backend.routers.busca_parceiro import busca_parceiro
app.register_blueprint(busca_parceiro)
print('busca_parceiro: OK!')

from backend.routers.parceiro_cadastro_manual import parceiro_cadastro_manual
app.register_blueprint(parceiro_cadastro_manual)
print('parceiro_cadastro_manual: OK!')

from backend.routers.gta_manual import gta_manual
app.register_blueprint(gta_manual)
print('gta_manual: OK!')

from backend.routers.gta_consulta import gta_consulta
app.register_blueprint(gta_consulta)
print('gta_consulta: OK!')

from backend.routers.brincos_entrada import brincos_entrada
app.register_blueprint(brincos_entrada)
print('Rotas de Brincos Entrada: OK!')

from backend.routers.brincos_fornecedor import brincos_fornecedor
app.register_blueprint(brincos_fornecedor)
print('Rotas de Brincos Fornecedor: OK!')

from backend.routers.brincos_relatorio_resumo import brincos_relatorio_resumo
app.register_blueprint(brincos_relatorio_resumo)
print('Rotas de Brincos Relatório Resumo: OK!')

from backend.routers.brincos_relatorio_nfiscais import brincos_relatorio_nfiscais
app.register_blueprint(brincos_relatorio_nfiscais)
print('Rotas de Brincos N.Fiscais: OK!')

from backend.routers.brincos_disponiveis import brincos_disponiveis
app.register_blueprint(brincos_disponiveis)
print('Rotas de Brincos Disponíveis: OK!')

from backend.routers.brincos_cancelamento import brincos_cancelamento
app.register_blueprint(brincos_cancelamento)
print('Rotas de Cancelamento de Brincos: OK!')

from backend.routers.brincos_saidas import brincos_saidas
app.register_blueprint(brincos_saidas)
print('Rotas de Brincos Saídas: OK!')

from backend.routers.operacoes_recentes import operacoes_recentes
app.register_blueprint(operacoes_recentes)
print('Rotas de Operações Recentes: OK!')

from backend.routers.backup_restore import backup_restore
app.register_blueprint(backup_restore)
print('Rotas de Backup/Restore: OK!')

from backend.routers.busca_propriedade import busca_propriedade
app.register_blueprint(busca_propriedade)
print('Rotas de busca_propriedade: OK!')

from backend.routers.racas import racas
app.register_blueprint(racas)
print('Rotas de racas: OK!')

from backend.routers.brincagem_sequencial import brincagem_sequencial
app.register_blueprint(brincagem_sequencial)
print('Brincagem Sequencial: OK!')

from backend.routers.brincagem_nascimento import brincagem_nascimento
app.register_blueprint(brincagem_nascimento)
print('Brincagem de Nascimento: OK!')

from backend.routers.comunicado_entrada import comunicado_entrada
app.register_blueprint(comunicado_entrada)
print('Comunicado Entrada: OK!')

from backend.routers.impressao_comunicado import impressao_comunicado
app.register_blueprint(impressao_comunicado)
print('Impressao Comunicado: OK!')

from backend.routers.reimpressao_comunicado import reimpressao_comunicado
app.register_blueprint(reimpressao_comunicado)
print('Reimpressao Comunicado: OK!')

from backend.routers.relatorio_eras import relatorio_eras
app.register_blueprint(relatorio_eras)
print('Relatorio de ERAS: OK!')

from backend.routers.brincagem_leitor import brincagem_leitor
app.register_blueprint(brincagem_leitor)
from backend.routers.saida_leitor import saida_leitor  # Sessao 098 - Leitor do Abate
app.register_blueprint(saida_leitor)
from backend.routers.pesos_leitor import pesos_leitor  # Sessao 114 - Leitor de Peso e Inconformes dos Pesos
app.register_blueprint(pesos_leitor)
from backend.routers.pesos_bastao import pesos_bastao  # Sessao 114 - Leitor de Peso com Bastao
app.register_blueprint(pesos_bastao)
from backend.routers.pesos_consulta import pesos_consulta  # Sessao 114 - Consulta de Peso e Conferidos
app.register_blueprint(pesos_consulta)
from backend.routers.pesos_relatorios import pesos_relatorios  # Sessao 129 - Relatorios de Pesagem
app.register_blueprint(pesos_relatorios)
from backend.routers.saida_bastao import saida_bastao  # Sessao 099 - Leitor do Abate com Bastao
app.register_blueprint(saida_bastao)
from backend.routers.transferencia_leitura import transferencia  # Sessao 107 - Leitor da Transferencia (e com Bastao)
app.register_blueprint(transferencia)
from backend.routers.posse_leitura import posse  # Sessao 115 - Leitor da Alteracao de Posse (e com Bastao)
app.register_blueprint(posse)
from backend.routers.frigorificos import frigorificos  # Sessao 099 - Frigorificos
app.register_blueprint(frigorificos)
from backend.routers.gta_saida import gta_saida  # Sessao 099 - Cadastro de GTA de Saida
app.register_blueprint(gta_saida)
from backend.routers.saida_relatorio import saida_relatorio  # Sessao 099 - Relatorio de Embarque
app.register_blueprint(saida_relatorio)
from backend.routers.saida_consulta import saida_consulta  # Sessao 099 - Consulta Embarque
app.register_blueprint(saida_consulta)
from backend.routers.saida_vincular import saida_vincular  # Sessao 100 - Vincular GTA / Embarque
app.register_blueprint(saida_vincular)
from backend.routers.saida_substituicao import saida_substituicao  # Sessao 100 - Substituicao de Animal
app.register_blueprint(saida_substituicao)
from backend.routers.saida_gta_consulta import saida_gta_consulta  # Sessao 101 - Consulta GTA de Saida
app.register_blueprint(saida_gta_consulta)
from backend.routers.saida_comunicado import saida_comunicado  # Sessao 101 - Gerar Comunicado de Saida
app.register_blueprint(saida_comunicado)

from backend.routers.saida_troca_comunicado import saida_troca_comunicado  # Sessao 102 - Troca de animal depois do Comunicado
app.register_blueprint(saida_troca_comunicado)

from backend.routers.saida_arquivo import saida_arquivo  # Sessao 102 - Abate por Arquivo Texto
app.register_blueprint(saida_arquivo)
from backend.routers.transferencia_arquivo import transferencia_arquivo  # Sessao 110 - Transferencia por Arquivo Texto
app.register_blueprint(transferencia_arquivo)
from backend.routers.venda_leitura import venda  # Sessao 111 - Leitor da Venda (e com Bastao)
app.register_blueprint(venda)
from backend.routers.venda_arquivo import venda_arquivo  # Sessao 111 - Venda por Arquivo Texto
app.register_blueprint(venda_arquivo)
from backend.routers.morte_lancamento import morte  # Sessao 111 - Morte de Animais (lancamento individual)
app.register_blueprint(morte)
from backend.routers.morte_arquivo import morte_arquivo  # Sessao 111 - Morte por Arquivo Texto
app.register_blueprint(morte_arquivo)
from backend.routers.morte_fotos import morte_fotos  # Sessao 111 - Morte: Controle Interno e fotos
app.register_blueprint(morte_fotos)
from backend.routers.morte_notificacao import morte_notificacao  # Sessao 111 - Morte: Notificacao (Anexo XXII)
app.register_blueprint(morte_notificacao)
from backend.routers.morte_relatorios import morte_relatorios  # Sessao 111 - Morte: Controle Interno (PDF) e Mortes no Periodo
app.register_blueprint(morte_relatorios)
from backend.routers.saida_impressao import saida_impressao  # Sessao 101 - Impressao/Reimpressao do Comunicado de Saida
app.register_blueprint(saida_impressao)

from backend.routers.consulta_animal import consulta_animal  # Sessao 102 - Consulta de Animal e Brinco
app.register_blueprint(consulta_animal)
print('Consulta de Animal e Brinco: OK!')
print('Brincagem Leitor: OK!')

from backend.routers.brincagem_consulta import brincagem_consulta
app.register_blueprint(brincagem_consulta)
print('Brincagem Consulta: OK!')

from backend.routers.brincagem_bastao import brincagem_bastao
app.register_blueprint(brincagem_bastao)
print('Brincagem Bastão: OK!')

# v1.24.0 (Sessao 087) - Alterar Dados dos Animais (corrigir Lote/Peso/Sexo/Raca no brete)
from backend.routers.alterar_dados_animais import alterar_dados_animais
app.register_blueprint(alterar_dados_animais)
from backend.routers.troca_rfid import troca_rfid
app.register_blueprint(troca_rfid)
from backend.routers.linkagem_rfid import linkagem_rfid  # Sessao 120 - Linkagem RFID e Brinco
app.register_blueprint(linkagem_rfid)
from backend.routers.linkagem_consulta import linkagem_consulta  # Sessao 120 - Consulta/PDF/Inconformidades da Linkagem
app.register_blueprint(linkagem_consulta)
from backend.routers.reidentificacao import reidentificacao  # Sessao 121 - Reidentificacao (lancamento em lote)
app.register_blueprint(reidentificacao)
from backend.routers.reidentificacao_consulta import reidentificacao_consulta  # Sessao 121 - Consulta/Notificacao PDF/Enviado/Inconformidades da Reidentificacao
app.register_blueprint(reidentificacao_consulta)
print('Alterar Dados dos Animais: OK!')

# v1.28.0 (Sessao 092) - Menu Consiste > Blockchain (acompanhamento e validacao)
from backend.routers.consiste_blockchain import consiste_blockchain
app.register_blueprint(consiste_blockchain)
print('Consiste Blockchain: OK!')

# Carga de animais (Consiste > Carga de Animais)
from backend.routers.carga_consiste import carga_consiste
app.register_blueprint(carga_consiste)
print('Carga de Animais: OK!')
from backend.routers.carga_relatorio import carga_relatorio  # Relatorio da Carga (PDF)
app.register_blueprint(carga_relatorio)

# BND/Fazenda: comparacao (Produtor, card do Hub de Entrada) e Correcao (Consiste)
from backend.routers.bnd_fazenda import bnd_fazenda
app.register_blueprint(bnd_fazenda)
from backend.routers.bnd_fazenda_consiste import bnd_fazenda_consiste
app.register_blueprint(bnd_fazenda_consiste)
print('BND/Fazenda: OK!')

from backend.routers.manual_consiste import manual_consiste  # Manual (PDF) do Cadastro
app.register_blueprint(manual_consiste)
print('Relatorio da Carga: OK!')

from backend.routers.vincular_gta import vincular_gta
app.register_blueprint(vincular_gta)
print('Vincular GTA: OK!')

from backend.routers.inventario_geral import inventario_geral
app.register_blueprint(inventario_geral)
print('Inventario Geral: OK!')

from backend.routers.pia_impressao import pia_impressao
app.register_blueprint(pia_impressao)
print('PIA (Anexo XXIII): OK!')

from backend.routers.notificacao_nascimento import notificacao_nascimento
app.register_blueprint(notificacao_nascimento)
print('Notificacao de Nascimentos: OK!')

from backend.routers.nascimentos_periodo import nascimentos_periodo
app.register_blueprint(nascimentos_periodo)
print('Nascimentos por Periodo: OK!')

from backend.routers.consulta_manejo import consulta_manejo
app.register_blueprint(consulta_manejo)
print('Consulta por Manejo: OK!')

from backend.routers.hub_entrada_agrupado import hub_entrada_agrupado
app.register_blueprint(hub_entrada_agrupado)
print('Hub de Entrada Agrupado: OK!')

from backend.routers.auditoria_eras import auditoria_eras
app.register_blueprint(auditoria_eras)
print('Auditorias ERAS: OK!')

# v1.61.0 - Aplicativo instalavel do Orion (PWA): manifesto e service worker.
# O manifesto e montado aqui (JSON nao aceita comentario). O service worker fica em static/pwa e e
# servido na RAIZ (/orion-sw.js) para valer em todas as telas. Nada de cache de dados.
from flask import send_from_directory

def _carimbo_static(caminho):   # carimbo de data do arquivo: o navegador pega o icone novo sozinho
    try:
        return str(int(os.path.getmtime(os.path.join(app.static_folder, caminho))))
    except OSError:
        return '0'

@app.route('/manifest.webmanifest')
def pwa_manifesto():
    manifesto = {
        'name': 'Orion',
        'short_name': 'Orion',
        'description': 'Orion SISBOV - Sistema de Rastreabilidade Bovina',
        'id': '/',
        'start_url': '/',
        'scope': '/',
        'display': 'standalone',
        'lang': 'pt-BR',
        'background_color': '#FFFFFF',
        'theme_color': '#D4370A',
        'icons': [
            {'src': '/static/img/pwa/icon-192.png?v=' + _carimbo_static('img/pwa/icon-192.png'),
             'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': '/static/img/pwa/icon-512.png?v=' + _carimbo_static('img/pwa/icon-512.png'),
             'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': '/static/img/pwa/icon-maskable-512.png?v=' + _carimbo_static('img/pwa/icon-maskable-512.png'),
             'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
    }
    resposta = jsonify(manifesto)
    resposta.mimetype = 'application/manifest+json'
    resposta.headers['Cache-Control'] = 'no-cache'
    return resposta

@app.route('/orion-sw.js')
def pwa_service_worker():
    resposta = send_from_directory(os.path.join(app.static_folder, 'pwa'), 'orion-sw.js',
                                   mimetype='application/javascript')
    resposta.headers['Cache-Control'] = 'no-cache'
    resposta.headers['Service-Worker-Allowed'] = '/'
    return resposta

# v1.59.0 - Celular: coloca o CSS/JS de tela pequena e o viewport em toda tela HTML (os arquivos so agem ate 768px).
@app.after_request
def _injetar_mobile(resposta):
    try:
        if (resposta.direct_passthrough or resposta.is_streamed or resposta.status_code != 200
                or resposta.mimetype != 'text/html'):
            return resposta
        dados = resposta.get_data()
        pos = dados.lower().find(b'</head>')
        if pos < 0:
            return resposta
        def _v(caminho):   # carimbo de data do arquivo: o celular pega a versao nova sozinho
            try:
                return str(int(os.path.getmtime(os.path.join(app.static_folder, caminho))))
            except OSError:
                return '0'
        extra = b''
        if b'name="viewport"' not in dados and b"name='viewport'" not in dados:
            extra += b'<meta name="viewport" content="width=device-width, initial-scale=1">'
        extra += ('<link rel="stylesheet" href="/static/css/orion_mobile.css?v=' + _v('css/orion_mobile.css') + '">'
                  '<script src="/static/js/orion_mobile.js?v=' + _v('js/orion_mobile.js') + '" defer></script>').encode('utf-8')
        if b'rel="manifest"' not in dados:   # v1.61.0 - aplicativo instalavel (icone do Orion)
            extra += ('<link rel="manifest" href="/manifest.webmanifest">'
                      '<meta name="theme-color" content="#D4370A">'
                      '<meta name="apple-mobile-web-app-title" content="Orion">'
                      '<link rel="apple-touch-icon" href="/static/img/pwa/apple-touch-icon.png?v=' + _v('img/pwa/apple-touch-icon.png') + '">'
                      '<script src="/static/js/orion_pwa.js?v=' + _v('js/orion_pwa.js') + '" defer></script>').encode('utf-8')
        resposta.set_data(dados[:pos] + extra + dados[pos:])
    except Exception as erro:   # nunca derruba a tela por causa do celular
        print(f'_injetar_mobile: ignorado ({erro})')
    return resposta


# -------------------------------------------------------
# Inicializacao do servidor
# -------------------------------------------------------
if __name__ == '__main__':
    from waitress import serve
    print('=' * 50)
    print('ORION SISBOV — Iniciando o sistema...')
    _host = os.getenv('ORION_HOST', '0.0.0.0')
    _porta = int(os.getenv('ORION_PORT', '5001'))
    print(f'Acesse: http://localhost:{_porta}')
    print('=' * 50)
    serve(app, host=_host, port=_porta)

# =========================================================
# FIM DE ARQUIVO: app.py
# =========================================================
