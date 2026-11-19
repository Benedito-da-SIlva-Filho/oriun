# Orion no servidor Windows — passo a passo (v1.0.0 · 19/11/2026 · Sessao 133)

## 0. Antes de tudo (no servidor)
- Dominio ORIUN apontando (DNS tipo A) para o IP publico do servidor.
- Portas 80 e 443 liberadas no roteador/firewall para o servidor (Let's Encrypt precisa da 80 e do 443).
- A porta 5001 NAO deve ficar aberta para fora (so o proxy fala com ela).

## 1. Programas
1. Python 3.13.7 (marcar "Add to PATH").
2. PostgreSQL (porta 5433), usuario e senha NOVOS (nao reaproveitar os do notebook).
3. Caddy para Windows (caddy.exe, 1 arquivo) — ele faz o HTTPS/certificado sozinho.

## 2. Copiar o Orion
- Copiar a pasta C:\Orion do notebook para o servidor SEM: .env, *.bak*, _to_delete, _tmp_*, XX Orion, __pycache__.
- No servidor: `pip install -r requirements.txt`

## 3. Base nova
- Criar a base vazia (mesmo nome de DB_NAME) e rodar os scripts de criacao do schema public (pasta Tabelas, na ordem de sempre).
- NAO restaurar backup do notebook (tem Produtores de teste).

## 4. .env DO SERVIDOR (arquivo novo; copie so os NOMES, valores novos)
DB_HOST=localhost
DB_PORT=5433
DB_NAME=...
DB_USER=...
DB_PASS=...            (senha forte, nova)
MASTER_LOGIN=...
MASTER_SENHA=...       (forte, nova)
MASTER_NOME=...
SECRET_KEY=...         (nova, 40+ caracteres aleatorios — gerar: python -c "import secrets;print(secrets.token_hex(32))")
DEBUG=False
COOKIE_SECURE=True
TRUST_PROXY=True
ORION_HOST=127.0.0.1
ORION_PORT=5001
MAIL_*  e  ANTHROPIC_*  (os mesmos do notebook, se for usar)
BLK_VERSAO_CHAVE_ATUAL / BLK_CHAVE_1  (ver com o Claude antes: chave da blockchain nao pode mudar sem plano)

## 5. Caddyfile (na pasta do Caddy) — trocar SEU-DOMINIO
SEU-DOMINIO {
    reverse_proxy 127.0.0.1:5001
}
Rodar: `caddy run --config Caddyfile`  (testar) e depois instalar como servico (ver nota abaixo).

## 6. Subir o Orion
- iniciar.bat (abre o Orion e o carteiro_blockchain).
- Testar: https://SEU-DOMINIO  -> cadeado, login do master.
- Conferir no log: nenhuma linha "CSRF: pedido recusado".

## 7. Deixar permanente (nao fechar ao deslogar)
- Orion e Caddy como servico do Windows (NSSM) ou Agendador de Tarefas "ao iniciar o computador".
- Backup agendado do PostgreSQL (pg_dump) todo dia, copia para fora do servidor.

## 8. Depois de subir
- Cadastrar Produtor real, Propriedade, Ambiente, Acesso -> Carga -> BND/Fazenda.
- Celular: acessar https://SEU-DOMINIO (camera/bastao passam a funcionar por ser HTTPS).

FIM DE ARQUIVO
