# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\validadores.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-08-04 11:23 -03
# ATUALIZADO EM: 2026-11-13 19:55 -03
# VERSAO: 1.4.0
# v1.4.0: Sessao 123 (2026-11-13 19:55 -03) - AUDITORIA ETAPA 4 (2a passada, Regra #73): .isdigit() trocado por .isdecimal() (1 uso(s)) - caracteres como '²' e '①' passavam na conferencia e quebravam o int() seguinte (erro 500). REVERSAO: .bak_antes_etapa4d.
# v1.3.0: Sessao 123 (2026-11-13 19:10 -03) - AUDITORIA ETAPA 6 (Regra #72): nova formatar_documento() central (mascara CPF/CNPJ); limpar_documento aceita qualquer tipo. REVERSAO: .bak_antes_etapa6c.
# v1.2.0: Sessao 122 (2026-11-12 19:00 -03) - CNPJ alfanumerico (Receita, jul/2026): letras no CNPJ aceitas e conferidas; CNPJ antigo continua valendo. Nova limpar_documento(). REVERSAO: .bak_antes_s122_etapa2.
#
# DESCRICAO:
#     Funcoes auxiliares compartilhadas de validacao de dados de
#     entrada - CPF/CNPJ (com digito verificador), e-mail (formato
#     e existencia real de dominio via MX) e telefone. Extraido de
#     backend/routers/convite.py v1.0.0, que havia criado essas
#     funcoes localmente por nao existir, ate entao, nenhum
#     validador equivalente em backend/utils/ (confirmado com
#     Benedito na Sessao 032).
#
#     Primeira funcao de validacao de CPF/CNPJ do projeto - segue
#     o mesmo espirito de pdf_helper.py (P-023): existir em um
#     unico lugar, para que qualquer router que precise validar
#     CPF/CNPJ (hoje: convite.py; no futuro, possivelmente cadastro
#     manual interno de Produtor pela Consiste) importe daqui, sem
#     duplicar o algoritmo do digito verificador.
#
#     v1.0.0: Extracao de convite.py v1.0.0 (_validar_cpf,
#             _validar_cnpj, _validar_cpf_cnpj, _validar_email,
#             _validar_telefone) - renomeadas de privadas (prefixo
#             _) para publicas, mesmo criterio ja usado em
#             pdf_helper.py v1.0.0. Nenhuma mudanca de
#             comportamento - so mudou de lugar e de nome.
#     v1.1.0: Sessao 032 - Teste real do /convite (email fake do
#             tipo nome@dominio.com.bt, TLD real mas inexistente na
#             pratica) revelou que validar_email() confere so
#             formato, nao se o dominio existe de verdade - um
#             e-mail bem formatado mas com dominio inexistente
#             nunca vai receber a senha provisoria, deixando o
#             Produtor com cadastro "fantasma", sem acesso.
#             Decisao com Benedito: NAO restringir por lista de
#             provedores (bloquearia e-mail corporativo/institucional
#             legitimo, comum no publico do Orion) - em vez disso,
#             checar se o dominio tem registro MX (servidor de
#             e-mail configurado). Nova dependencia: dnspython
#             (adicionada a requirements.txt). Nova funcao
#             dominio_possui_mx() - timeout de 3 segundos; em caso
#             de falha de rede/instabilidade do DNS (nao dominio
#             inexistente), decisao permissiva: deixa passar, para
#             nao bloquear um Produtor real por uma instabilidade
#             momentanea que nao e culpa dele. Regra de escopo
#             tambem definida por Benedito: sem filtro por pais/TLD
#             (ex.: exigir .com.br) - se o Orion um dia atender
#             Propriedades fora do Brasil, isso vira uma decisao de
#             negocio explicita (IF por pais do Cliente), nao uma
#             restricao de validador.
# =========================================================

import re
import dns.resolver
import dns.exception


# -------------------------------------------------------
# Funcao: limpar_documento (v1.2.0)
# Tira pontos, tracos, barras e espacos e deixa em MAIUSCULO,
# MANTENDO as letras (CNPJ alfanumerico). Use no lugar de
# re.sub(r'\D', '', ...) para CPF/CNPJ.
# -------------------------------------------------------
def limpar_documento(valor):
    return re.sub(r'[^0-9A-Za-z]', '', str(valor or '')).upper()


# -------------------------------------------------------
# Funcao: formatar_documento  (v1.3.0, Regra #72)
# UNICA maquina de mascara de CPF/CNPJ do sistema.
# 11 caracteres -> 000.000.000-00 | 14 -> 00.000.000/0000-00
# (CNPJ alfanumerico: letras mantidas). Outro tamanho: devolve o texto como veio.
# -------------------------------------------------------
def formatar_documento(valor):
    texto = str(valor or '').strip()
    d = limpar_documento(texto)
    if len(d) == 11:
        return f'{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}'
    if len(d) == 14:
        return f'{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}'
    return texto


# -------------------------------------------------------
# Funcao: validar_cpf
# Confere formato (11 digitos, nao repetidos) e os dois digitos
# verificadores pelo algoritmo padrao da Receita Federal.
# Espera a string ja limpa (so digitos).
# -------------------------------------------------------
def validar_cpf(cpf):
    if len(cpf) != 11 or not cpf.isascii() or not cpf.isdecimal() or cpf == cpf[0] * 11:   # v1.2.0: CPF e so numero
        return False

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    dv1 = 0 if resto == 10 else resto
    if dv1 != int(cpf[9]):
        return False

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    dv2 = 0 if resto == 10 else resto
    if dv2 != int(cpf[10]):
        return False

    return True


# -------------------------------------------------------
# Funcao: validar_cnpj
# Confere formato (14 digitos, nao repetidos) e os dois digitos
# verificadores pelo algoritmo padrao da Receita Federal.
# Espera a string ja limpa (so digitos).
# -------------------------------------------------------
def validar_cnpj(cnpj):
    # v1.2.0: CNPJ alfanumerico (Receita, a partir de jul/2026): 12 primeiros caracteres
    # letras (A-Z) ou numeros, 2 ultimos (digitos verificadores) so numeros. Cada caractere
    # vale (codigo ASCII - 48): '0'-'9' = 0-9, 'A' = 17 ... 'Z' = 42. CNPJ so de numeros (antigo)
    # segue valendo, pois o calculo e o mesmo.
    cnpj = (cnpj or '').upper()
    if len(cnpj) != 14 or not re.fullmatch(r'[0-9A-Z]{12}[0-9]{2}', cnpj) or cnpj == cnpj[0] * 14:
        return False

    valores = [ord(c) - 48 for c in cnpj]
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(valores[i] * pesos1[i] for i in range(12))
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    if dv1 != int(cnpj[12]):
        return False

    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(valores[i] * pesos2[i] for i in range(13))
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    if dv2 != int(cnpj[13]):
        return False

    return True


# -------------------------------------------------------
# Funcao: validar_cpf_cnpj
# Recebe o valor com ou sem mascara, limpa (so digitos) e decide
# se valida como CPF (11 digitos) ou CNPJ (14 digitos).
#
# Retorna uma tupla (valido: bool, valor_limpo: str) - o valor
# limpo e util para quem chamou gravar no banco sem mascara,
# mesmo quando valido=False (o chamador decide o que fazer).
# -------------------------------------------------------
def validar_cpf_cnpj(valor):
    limpo = limpar_documento(valor)
    if len(limpo) == 11:
        return validar_cpf(limpo), limpo
    elif len(limpo) == 14:
        return validar_cnpj(limpo), limpo
    else:
        return False, limpo


# -------------------------------------------------------
# Funcao: validar_email
# Checagem simples de formato (nao confirma existencia real do
# endereco - isso so o envio de e-mail de fato confirma).
# -------------------------------------------------------
def validar_email(valor):
    padrao = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(padrao, valor or '') is not None


# -------------------------------------------------------
# Funcao: dominio_possui_mx
# Confere se o dominio de um e-mail tem registro MX configurado
# (ou seja, se existe de verdade um servidor pronto para receber
# e-mail naquele dominio). Nao confirma que a CAIXA especifica
# existe (isso so o envio real confirma) - so que o dominio nao e
# fantasia/erro de digitacao.
#
# Timeout de 3 segundos (decisao com Benedito, Sessao 032) - nao
# trava a tela do usuario esperando resposta de DNS.
#
# Comportamento em caso de falha de REDE/instabilidade (nao
# dominio inexistente): PERMISSIVO - retorna True, deixa passar.
# Decisao de negocio com Benedito: nao bloquear um Produtor real
# por uma instabilidade momentanea que nao e culpa dele. So
# retorna False quando o DNS respondeu com clareza que o dominio
# nao tem MX (NXDOMAIN ou NoAnswer).
# -------------------------------------------------------
def dominio_possui_mx(dominio):
    try:
        dns.resolver.resolve(dominio, 'MX', lifetime=3)
        return True

    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        # DNS respondeu com clareza: dominio nao existe ou nao
        # tem servidor de e-mail configurado.
        return False

    except dns.exception.DNSException:
        # Timeout, falha de rede ou qualquer outra instabilidade -
        # nao e uma resposta clara de "dominio invalido". Permissivo.
        return True


# -------------------------------------------------------
# Funcao: email_dominio_existe
# Combina validar_email (formato) + dominio_possui_mx (existencia
# real do dominio). So chega a checar o dominio se o formato ja
# estiver correto - evita consulta DNS desperdicada para um
# e-mail obviamente mal formatado.
# -------------------------------------------------------
def email_dominio_existe(valor):
    if not validar_email(valor):
        return False

    dominio = valor.rsplit('@', 1)[-1]
    return dominio_possui_mx(dominio)


# -------------------------------------------------------
# Funcao: validar_telefone
# Aceita telefone fixo (10 digitos, com DDD) ou celular
# (11 digitos, com DDD + 9). Espera a string com ou sem mascara -
# faz a limpeza internamente.
# -------------------------------------------------------
def validar_telefone(valor):
    limpo = re.sub(r'\D', '', valor or '')
    return len(limpo) in (10, 11)

# =========================================================
# FIM DE ARQUIVO: backend\utils\validadores.py
# =========================================================