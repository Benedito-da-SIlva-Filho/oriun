@echo off
:: =========================================================
:: PROJETO: Orion
:: PASTA: C:\orion
:: MODULO: iniciar.bat
:: AUTOR: Benedito Silva Filho
:: CRIADO EM: 2026-06-21 08:48 -03
:: ATUALIZADO EM: 2026-10-10 18:00 -03
:: VERSAO: 1.1.0
::
:: DESCRICAO:
::     Inicia o sistema Orion com um duplo clique. Desde a v1.1.0 abre
::     tambem, numa SEGUNDA JANELA, o carteiro do blockchain
::     (carteiro_blockchain.py), que envia os eventos da fila sozinho.
::     Para encerrar tudo: feche as duas janelas.
::     v1.0.0: Criacao do modulo.
::     v1.1.0: Sessao 093 (10/10/2026, 18:00 -03) - o carteiro do blockchain
::             nao subia junto com o Orion: os eventos ficavam PENDENTE ate
::             alguem abrir uma janela e rodar o carteiro a mao (achado no
::             teste da Entrada de Compra). Agora sobe junto, em outra janela.
:: =========================================================

:: Vai para a pasta do Orion
cd /d C:\orion

:: Adiciona o PostgreSQL ao caminho do sistema
set PATH=%PATH%;C:\Program Files\PostgreSQL\16\bin

:: Exibe mensagem de boas vindas
echo =====================================================
echo   ORION SISBOV — Iniciando o sistema...
echo   Acesse: http://localhost:5001
echo   Carteiro do blockchain: abre em outra janela
echo   Para encerrar: feche as duas janelas ou Ctrl+C
echo =====================================================

:: Inicia o carteiro do blockchain numa segunda janela (envia os eventos sozinho)
start "Orion - Carteiro do Blockchain" cmd /k "cd /d C:\orion && python carteiro_blockchain.py"

:: Inicia o Orion
python app.py

:: Mantem a janela aberta se houver erro
pause

:: =========================================================
:: FIM DE ARQUIVO: iniciar.bat
:: =========================================================