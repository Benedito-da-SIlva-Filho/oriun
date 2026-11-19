# -*- coding: utf-8 -*-
# =========================================================
# PROJETO:      Orion
# PASTA:        C:\orion\backend\routers
# MODULO:       backend\routers\convite.py
# AUTOR:        Benedito Silva Filho.
# CRIADO EM:    2026-08-04 11:10 -03
# ATUALIZADO EM: 2026-08-13 13:20 -03
# VERSAO:       2.3.0
#
# DESCRICAO:
#     Fluxo de Convite Publico (/convite) - caminho de
#     aquisicao de novos Produtores, sem token, de uso livre
#     (boca a boca entre Produtores e Certificadoras, e agora
#     tambem via convite comercial direto da Consiste - ver
#     prospects.py).
#
#     Rota unica /convite, com renderizacao condicional por
#     campo hidden 'etapa' no formulario:
#     - GET sem session['convite_dados']  -> mostra Etapa 1
#     - GET com session['convite_dados']  -> mostra Etapa 2
#       (preservado, ver nota de PAUSA abaixo - v2.2.0)
#     - POST etapa=1 -> valida Etapa 1 (honeypot, rate limit,
#       campos obrigatorios, formato/digito verificador do
#       CPF-CNPJ, duplicidade em Produtor). Se tudo ok, A PARTIR
#       DA v2.2.0 grava o visitante em vitrine_visitantes e
#       mostra a Tela Vitrine (nao mais a Etapa 2 - ver nota
#       abaixo).
#     - POST etapa=2 -> valida Nome/Inscricao Estadual/Municipio/
#       UF da Propriedade e dispara a transacao unica de criacao
#       (Propriedade + Produtor + PropriedadeProdutor + Usuario +
#       UsuarioVinculo) + envia o e-mail de acesso. PRESERVADA
#       tal como estava - so fica sem ninguem chegando nela pelo
#       fluxo automatico (ver nota de PAUSA abaixo).
#
#     v1.0.0: Criacao do modulo - Etapa 1 implementada:
#             - Formulario CPF/CNPJ + Nome + Email + Telefone.
#             - Honeypot anti-spam (campo 'apelido_contato',
#               escondido via CSS, nunca preenchido por humano).
#             - Rate limit de 5 envios/hora por IP, guardado em
#               dicionario Python em memoria (sem tabela nova no
#               banco - decisao registrada na Sessao 032. Limitacao
#               conhecida: contagem zera se o processo Flask/
#               Waitress reiniciar, e nao e compartilhada entre
#               workers se um dia houver mais de um - aceitavel
#               para rate limit anti-spam, nao e controle critico).
#             - Validacao de CPF/CNPJ (formato + digito verificador)
#               criada localmente neste modulo - nao ha utilitario
#               equivalente em outro lugar do projeto ate esta
#               versao (Regra de Ouro: sem utils/validadores.py
#               confirmado na Sessao 032).
#             - Bloqueio se o CPF/CNPJ ja existir em Produtor
#               (produtor.cpf_cnpj).
#             - Dados validos da Etapa 1 guardados em
#               session['convite_dados'] ate a Etapa 2 confirmar
#               (sessao Flask, expira com o navegador/tempo padrao).
#             - Etapa 2 (dados da Propriedade) e a logica de
#               confirmacao (transacao unica) ainda NAO
#               implementadas - placeholder ao final do POST.
#     v1.1.0: Sessao 032 - Benedito confirmou que backend/utils/ ja
#             existia (pdf_helper.py, multitenant.py, onboarding.py,
#             etc.), so nao tinha validador ainda. Extraidas as
#             funcoes de validacao de CPF/CNPJ, e-mail e telefone
#             para o novo backend/utils/validadores.py (mesmo
#             criterio ja usado em pdf_helper.py/P-023: existir em
#             um unico lugar, reaproveitavel por outros routers no
#             futuro). Este arquivo passa a importar de la - nenhuma
#             mudanca de comportamento, so de organizacao.
#     v1.2.0: Sessao 032 - Regra de linguagem definida por Benedito
#             (registrada como regra permanente do projeto): a
#             palavra "invalido/invalida" carrega conotacao negativa
#             associada a limitacao/deficiencia de pessoas e nao
#             deve ser usada em mensagens de erro voltadas ao
#             usuario. Substituida por "incorreto/incorreta" nas
#             tres mensagens desta rota (e-mail, telefone,
#             CPF/CNPJ). Nenhuma mudanca de comportamento - so de
#             texto.
#     v1.3.0: Sessao 032 - E-mail com dominio inexistente (ex.:
#             nome@dominio.com.bt fake) passava pela validacao de
#             formato mas nunca receberia a senha provisoria de
#             acesso. Troca de validar_email() por
#             email_dominio_existe() (novo em validadores.py
#             v1.1.0), que confere formato + registro MX real do
#             dominio. Sem filtro por lista de provedores nem por
#             pais/TLD (decisao de escopo com Benedito) - qualquer
#             dominio com MX valido passa, incluindo corporativo/
#             institucional.
#     v1.4.0: Sessao 032 - Teste real revelou que o e-mail era
#             gravado exatamente como digitado (ex.: em UPPERCASE,
#             por autofill do navegador), sem normalizacao.
#             Decisao com Benedito: e-mail sempre em lowercase
#             (convencao padrao - evita duplicidade futura por
#               diferenca de caixa, ex.: Nome@X.com vs nome@x.com
#               sendo tratados como diferentes). Normalizado logo
#             na coleta do campo, antes de qualquer validacao.
#     v2.0.0: Sessao 032 - Etapa 2 implementada (Nome, Inscricao
#             Estadual, Municipio, UF da Propriedade - cadastro
#             minimo, decisao com Benedito: "e um pre nao um
#             cadastro", resto completado depois ja dentro do
#             sistema, fluxo forcado registrado como pendencia
#             P-040). Transacao unica de confirmacao criada:
#             Propriedade, Produtor, PropriedadeProdutor, Usuario
#             (login=CPF/CNPJ sem mascara, senha provisoria com o
#             mesmo gerador de auth.py/esqueci_senha) e
#             UsuarioVinculo (cargo=TITULAR). E-mail de acesso
#             reaproveita o mesmo mecanismo Flask-Mail de
#             esqueci_senha(). Campos obrigatorios no banco sem
#             fonte de dado real neste pre-cadastro recebem
#             placeholder fixo (decisao com Benedito - "fica algo
#             ficticio obrigando a ser atualizado"):
#               Propriedade.tipo = 'MISTA'
#               Propriedade.roteiro_acesso = 'A COMPLETAR'
#               Propriedade.area_hectares = 0
#               Produtor.municipio = 'A COMPLETAR'
#               Produtor.uf = 'XX'
#             Propriedade.email/telefone e Produtor.email/telefone
#             reaproveitam os dados reais informados na Etapa 1
#             (decisao com Benedito - "opcao A certou"). Produtor.
#             razao_social = mesmo valor de nome, para Fisica ou
#             Juridica (decisao com Benedito - "replica para Fisica
#             ou Juridica"). Produtor.visibilidade = 'Privada'.
#             NENHUM registro de Proprietario e criado nesta
#             transacao (decisao com Benedito: Propriedade->
#             Proprietario->libera Produtor completo e fluxo do
#             P-040, fora do escopo do Convite).
#     v2.1.0: Sessao 032 - P-040 implementado: Propriedade nasce
#             com cadastro_completo=False (nova coluna, Sessao
#             032 - ver propriedade.py v2.5.0). O redirecionamento
#             do Produtor para completar o cadastro no primeiro
#             acesso e feito em auth.py/produtor_home(), nao aqui -
#             este arquivo so marca a flag no momento da criacao.
#             Decisao com Benedito: apenas a 1a Propriedade (a do
#             Convite) passa por este fluxo de completar depois -
#             a 2a em diante e cadastrada diretamente pela Consiste
#             (cliente entra em contato), ja nascendo completa.
#     v2.2.0: Sessao 034 (continuacao 6, 11/08/2026, 20:30 -03) -
#             PAUSA DA ETAPA 2 + TELA VITRINE. Decisao de Benedito,
#             motivada pela fricao real percebida ao testar o
#             fluxo completo do Convite (Proprietario -> Produtor
#             -> Propriedade, todos obrigatorios, antes de ver
#             qualquer tela) para um prospect que so quer "conhecer
#             o trabalho": criar conta real (com login/senha) na
#             Etapa 1 e forcar o cadastro completo e fricao demais
#             para quem ainda nem decidiu virar cliente.
#
#             NOVO COMPORTAMENTO: quando a Etapa 1 passa em todas as
#             validacoes (inalteradas - honeypot, rate limit, campos
#             obrigatorios, e-mail, telefone, CPF/CNPJ, duplicidade),
#             em vez de guardar os dados em session e mostrar a
#             Etapa 2, o visitante e gravado em vitrine_visitantes
#             (novo model, backend/models/vitrine_visitante.py) e
#             vê a Tela Vitrine (templates/convite/vitrine.html) -
#             uma demonstracao publica e travada de todos os
#             modulos do sistema, sem login, sem criar Produtor/
#             Propriedade/Usuario nenhum. O CTA final da Vitrine e
#             um link direto de WhatsApp para a Consiste conversar
#             com o prospect.
#
#             ETAPA 2 PRESERVADA, NAO REMOVIDA: toda a logica de
#             _processar_etapa2() (transacao de criacao de conta
#             real, e-mail de acesso) continua exatamente como
#             estava - so ficou sem ninguem chegando nela pelo
#             fluxo automatico, ja que session['convite_dados']
#             deixou de ser gravado na Etapa 1. Decisao explicita
#             de Benedito: "vamos usar a etapa 2 quando ele comprar
#             a ideia e se tornar nosso cliente" - o gatilho de
#             como a Consiste reativa esse caminho (apos a
#             conversa/ligacao) FICA COMO PENDENCIA para uma
#             proxima sessao, ainda nao definido. Ate la, a rota
#             GET /convite com session['convite_dados'] preenchida
#             tecnicamente ainda mostraria a Etapa 2 se alguem
#             chegasse la de algum jeito manual - comportamento
#             mantido de proposito, para nao quebrar a base pronta
#             quando essa reconexao for desenhada.
#     v2.3.0: Sessao 034 (continuacao 9, 13/08/2026, 13:20 -03) -
#             O gatilho de reconexao mencionado na nota de PAUSA
#             acima (v2.2.0) foi definido nesta sessao: NAO reusa
#             a Etapa 2 deste arquivo (que exige a Propriedade
#             preenchida manualmente por quem confirma) - em vez
#             disso, ganhou fluxo proprio e mais simples em
#             backend/routers/vitrine_visitantes.py (tela "Visitantes
#             da Vitrine", exclusiva CONSISTE, 1 clique = "Converter
#             em Cliente", sem pedir dados de Propriedade antes -
#             reaproveita o mesmo padrao cadastro_completo=False +
#             completar no primeiro acesso, ja usado aqui). A Etapa
#             2 deste arquivo CONTINUA preservada e inalterada (nao
#             foi removida nem chamada por lugar nenhum nesta
#             mudanca) - fica como caminho alternativo ja pronto,
#             caso um dia a Consiste prefira coletar os dados da
#             Propriedade antes de criar a conta.
#             Unica mudanca de fato neste arquivo: a funcao local
#             _gerar_senha_provisoria() foi removida e substituida
#             por import de gerar_senha_provisoria() (backend/utils/
#             senha_helper.py, novo) - mesma logica ja duplicada em
#             auth.py e produtores.py, extraida para um lugar so
#             (decisao de Benedito, motivada pelo novo 4o ponto de
#             uso em vitrine_visitantes.py). Nenhuma mudanca de
#             comportamento na Etapa 2. Imports random/string
#             removidos deste arquivo (nao usados em mais nenhum
#             outro ponto).
# =========================================================

from flask import Blueprint, render_template, request, session, url_for
from backend.database import engine
from backend.models import Produtor, Propriedade, PropriedadeProdutor, Usuario, UsuarioVinculo, VitrineVisitante
from backend.utils.validadores import validar_cpf_cnpj, email_dominio_existe, validar_telefone
from backend.utils.senha_helper import gerar_senha_provisoria
from backend.extensions import mail
from flask_mail import Message
from werkzeug.security import generate_password_hash
from sqlalchemy.orm import Session
from datetime import date
import re
import time
import urllib.parse

print('CONVITE.PY CARREGADO — VERSAO 2.3.0!')

convite = Blueprint('convite', __name__)

# -------------------------------------------------------
# Rate limit em memoria: 5 envios/hora por IP.
# Formato: { '123.45.67.89': [timestamp1, timestamp2, ...] }
# Variavel de modulo - vive enquanto o processo Flask/Waitress
# estiver rodando. Ver nota de limitacao no cabecalho (v1.0.0).
# -------------------------------------------------------
_TENTATIVAS_POR_IP = {}
_LIMITE_TENTATIVAS = 5
_JANELA_SEGUNDOS    = 3600  # 1 hora


def _ip_excedeu_limite(ip):
    """
    Verifica se o IP ja excedeu o limite de tentativas na ultima
    hora. Limpa timestamps antigos (fora da janela) antes de contar.
    Se ainda nao excedeu, ja registra a tentativa atual e libera.
    Retorna True se o IP deve ser bloqueado, False se pode seguir.
    """
    agora = time.time()
    tentativas = _TENTATIVAS_POR_IP.get(ip, [])

    # Remove tentativas com mais de 1 hora
    tentativas = [t for t in tentativas if agora - t < _JANELA_SEGUNDOS]

    if len(tentativas) >= _LIMITE_TENTATIVAS:
        _TENTATIVAS_POR_IP[ip] = tentativas  # mantem lista limpa
        return True

    tentativas.append(agora)
    _TENTATIVAS_POR_IP[ip] = tentativas
    return False


# -------------------------------------------------------
# Lista de UFs para o dropdown da Etapa 2.
# -------------------------------------------------------
UFS = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
    'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
    'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
]

# -------------------------------------------------------
# WhatsApp da Consiste - CTA final da Tela Vitrine (v2.2.0).
# Numero fixo, decisao de Benedito (Sessao 034 cont. 6):
# contato direto e imediato, sem exigir consulta a mais
# nenhuma pagina/site.
# -------------------------------------------------------
WHATSAPP_CONSISTE = '5534996918209'


# -------------------------------------------------------
# Rota: /convite — Etapa 1 (leva a Vitrine desde v2.2.0) e
# Etapa 2 (preservada, pausada - ver DESCRICAO no topo).
#
# GET  -> mostra Etapa 2 se ja houver session['convite_dados']
#         (caminho preservado, mas nada mais grava essa chave
#         de sessao desde v2.2.0), senao mostra Etapa 1.
# POST etapa=1 -> valida honeypot, rate limit, campos
#         obrigatorios, formato/digito verificador do
#         CPF-CNPJ, duplicidade em Produtor. Se tudo ok,
#         grava o visitante em vitrine_visitantes e mostra
#         a Tela Vitrine.
# POST etapa=2 -> PRESERVADA, inalterada - valida Nome/
#         Inscricao Estadual/Municipio/UF da Propriedade e
#         dispara a transacao unica de criacao de conta real.
# -------------------------------------------------------
@convite.route('/convite', methods=['GET', 'POST'])
def convite_etapa1():
    if request.method == 'GET':
        if 'convite_dados' in session:
            return render_template('convite/convite_etapa2.html', erro=None, dados={}, ufs=UFS)
        return render_template('convite/convite_etapa1.html', erro=None, dados={})

    if request.form.get('etapa') == '2':
        return _processar_etapa2()

    return _processar_etapa1()


def _processar_etapa1():
    erro = None
    dados_preenchidos = {}

    # --- Honeypot: campo invisivel, humano nunca preenche ---
    if request.form.get('apelido_contato', '').strip():
        # Bot detectado - descarta silenciosamente, sem avisar
        # que foi pego. Responde como se tivesse dado certo.
        return render_template('convite/convite_etapa1.html',
            erro=None,
            sucesso='Recebemos seus dados. Prosseguindo...',
            dados=dados_preenchidos
        )

    # --- Rate limit: 5 envios/hora por IP ---
    ip_origem = request.remote_addr
    if _ip_excedeu_limite(ip_origem):
        erro = 'Muitas tentativas. Tente novamente mais tarde.'
        return render_template('convite/convite_etapa1.html',
            erro=erro, dados=dados_preenchidos
        )

    # --- Coleta dos campos ---
    cpf_cnpj_informado = request.form.get('cpf_cnpj', '').strip()
    nome_informado      = request.form.get('nome', '').strip()
    email_informado      = request.form.get('email', '').strip().lower()
    telefone_informado   = request.form.get('telefone', '').strip()

    dados_preenchidos = {
        'cpf_cnpj': cpf_cnpj_informado,
        'nome': nome_informado,
        'email': email_informado,
        'telefone': telefone_informado,
    }

    # --- Validacoes de preenchimento ---
    if not cpf_cnpj_informado or not nome_informado or not email_informado or not telefone_informado:
        erro = 'Todos os campos sao obrigatorios.'

    elif not email_dominio_existe(email_informado):
        erro = 'E-mail incorreto ou domínio inexistente.'

    elif not validar_telefone(telefone_informado):
        erro = 'Telefone incorreto. Informe DDD + numero.'

    else:
        cpf_cnpj_valido, cpf_cnpj_limpo = validar_cpf_cnpj(cpf_cnpj_informado)

        if not cpf_cnpj_valido:
            erro = 'CPF ou CNPJ incorreto. Verifique os numeros digitados.'
        else:
            with Session(engine) as db:
                ja_existe = db.query(Produtor).filter_by(
                    cpf_cnpj=cpf_cnpj_limpo
                ).first()

            if ja_existe:
                erro = 'Voce ja tem cadastro. Faca login.'
            else:
                # --- Etapa 1 validada (v2.2.0): grava o visitante
                # em vitrine_visitantes e mostra a Tela Vitrine -
                # NAO mais session['convite_dados'] + Etapa 2 (ver
                # DESCRICAO no topo do arquivo, nota de PAUSA).
                telefone_limpo = re.sub(r'\D', '', telefone_informado)

                with Session(engine) as db:
                    visitante = VitrineVisitante(
                        cpf_cnpj=cpf_cnpj_limpo,
                        nome=nome_informado,
                        email=email_informado,
                        telefone=telefone_limpo,
                    )
                    db.add(visitante)
                    db.commit()

                # Link de WhatsApp com mensagem pre-preenchida,
                # personalizada com o nome do visitante.
                mensagem_whatsapp = (
                    f'Olá! Sou {nome_informado} e vi a demonstração '
                    f'do Orion SISBOV. Quero saber mais!'
                )
                link_whatsapp = (
                    f'https://wa.me/{WHATSAPP_CONSISTE}'
                    f'?text={urllib.parse.quote(mensagem_whatsapp)}'
                )

                return render_template('convite/vitrine.html',
                    nome=nome_informado,
                    link_whatsapp=link_whatsapp,
                )

    return render_template('convite/convite_etapa1.html',
        erro=erro,
        dados=dados_preenchidos
    )


def _processar_etapa2():
    # PRESERVADA, INALTERADA (v2.2.0) - ver DESCRICAO no topo do
    # arquivo (nota de PAUSA). Sessao expirada ou acesso direto
    # sem passar pela Etapa 1 - nao ha o que confirmar, volta
    # para o inicio.
    dados_pessoa = session.get('convite_dados')
    if not dados_pessoa:
        return render_template('convite/convite_etapa1.html',
            erro='Sua sessao expirou. Preencha seus dados novamente.',
            dados={}
        )

    nome_propriedade      = request.form.get('nome_propriedade', '').strip()
    inscricao_estadual    = request.form.get('inscricao_estadual', '').strip()
    municipio_propriedade = request.form.get('municipio', '').strip()
    uf_propriedade         = request.form.get('uf', '').strip()

    dados_preenchidos = {
        'nome_propriedade': nome_propriedade,
        'inscricao_estadual': inscricao_estadual,
        'municipio': municipio_propriedade,
        'uf': uf_propriedade,
    }

    erro = None
    if not nome_propriedade or not inscricao_estadual or not municipio_propriedade or not uf_propriedade:
        erro = 'Todos os campos sao obrigatorios.'
    elif uf_propriedade not in UFS:
        erro = 'UF incorreta.'

    if erro:
        return render_template('convite/convite_etapa2.html',
            erro=erro, dados=dados_preenchidos, ufs=UFS
        )

    # --- Tudo validado - dispara a transacao unica de criacao ---
    tipo_pessoa = 'FISICA' if len(dados_pessoa['cpf_cnpj']) == 11 else 'JURIDICA'
    senha_provisoria = gerar_senha_provisoria()

    with Session(engine) as db:
        try:
            propriedade = Propriedade(
                nome=nome_propriedade,
                inscricao_estadual=inscricao_estadual,
                municipio=municipio_propriedade,
                uf=uf_propriedade,
                # Placeholder - sem fonte de dado real neste
                # pre-cadastro (decisao com Benedito, Sessao 032).
                tipo='MISTA',
                roteiro_acesso='A COMPLETAR',
                area_hectares=0,
                # P-040: pre-cadastro incompleto - Produtor sera
                # direcionado a completar no primeiro acesso
                # (auth.py/produtor_home()).
                cadastro_completo=False,
                # Dado real, reaproveitado do Titular (Etapa 1).
                email=dados_pessoa['email'],
                telefone=dados_pessoa['telefone'],
            )
            db.add(propriedade)
            db.flush()  # garante propriedade.id antes do vinculo

            produtor = Produtor(
                nome=dados_pessoa['nome'],
                razao_social=dados_pessoa['nome'],  # replica p/ Fisica ou Juridica
                cpf_cnpj=dados_pessoa['cpf_cnpj'],
                tipo_pessoa=tipo_pessoa,
                visibilidade='Privada',
                email=dados_pessoa['email'],
                telefone=dados_pessoa['telefone'],
                # Placeholder - sem fonte de dado real neste
                # pre-cadastro (decisao com Benedito, Sessao 032).
                municipio='A COMPLETAR',
                uf='XX',
            )
            db.add(produtor)
            db.flush()  # garante produtor.id antes do vinculo

            vinculo_propriedade = PropriedadeProdutor(
                id_propriedade=propriedade.id,
                id_produtor=produtor.id,
                principal=True,
                data_inicio=date.today(),
            )
            db.add(vinculo_propriedade)

            usuario = Usuario(
                id_produtor=produtor.id,
                login=dados_pessoa['cpf_cnpj'],
                senha=generate_password_hash(senha_provisoria),
                perfil='PRODUTOR',
                nome=dados_pessoa['nome'],
                email=dados_pessoa['email'],
                # False = senha provisoria, obriga troca no
                # proximo login (mesmo padrao de esqueci_senha()).
                senha_provisoria=False,
            )
            db.add(usuario)
            db.flush()  # garante usuario.id antes do vinculo

            vinculo_acesso = UsuarioVinculo(
                id_usuario=usuario.id,
                id_produtor=produtor.id,
                cargo='TITULAR',
                data_inicio=date.today(),
            )
            db.add(vinculo_acesso)

            db.commit()

        except Exception as e:
            db.rollback()
            print(f'ERRO na transacao do Convite Publico: {e}')
            return render_template('convite/convite_etapa2.html',
                erro='Nao foi possivel concluir seu cadastro. Tente novamente ou contate o suporte.',
                dados=dados_preenchidos, ufs=UFS
            )

    # --- Cadastro criado com sucesso - envia o e-mail de acesso
    # (mesmo mecanismo Flask-Mail ja usado em esqueci_senha()) ---
    try:
        msg = Message(
            subject    = 'Orion SISBOV — Seu acesso foi criado',
            sender     = 'noreply.consisteti@gmail.com',
            recipients = [dados_pessoa['email']]
        )
        msg.body = (
            f'Ola, {dados_pessoa["nome"]}!\n\n'
            f'Seu cadastro no Orion SISBOV foi criado com sucesso.\n\n'
            f'Login: {dados_pessoa["cpf_cnpj"]}\n'
            f'Senha provisoria: {senha_provisoria}\n\n'
            f'Acesse o sistema com este login e senha.\n'
            f'Voce sera redirecionado para criar uma nova senha imediatamente.\n\n'
            f'Atenciosamente,\n'
            f'Orion SISBOV — Consiste Informatica'
        )
        mail.send(msg)
    except Exception as e:
        print(f'ERRO Flask-Mail (Convite Publico): {e}')
        # O cadastro ja foi criado com sucesso no banco (nao ha o
        # que desfazer aqui) - so o e-mail falhou. O usuario pode
        # recuperar o acesso depois via /esqueci-senha, ja que o
        # login (CPF/CNPJ) ja existe.
        session.pop('convite_dados', None)
        return render_template('convite/convite_etapa2.html',
            erro='Cadastro criado, mas houve falha ao enviar o e-mail de acesso. '
                 'Use "Esqueci minha senha" na tela de login, informando seu CPF/CNPJ.',
            dados={}, ufs=UFS
        )

    session.pop('convite_dados', None)
    return render_template('convite/convite_etapa2.html',
        erro=None,
        sucesso='Cadastro concluido! Enviamos um e-mail com seu login e senha de acesso.',
        dados={}, ufs=UFS
    )

# =========================================================
# FIM DE ARQUIVO: backend\routers\convite.py
# =========================================================