@echo off
:: =========================================================
:: PROJETO: Orion
:: PASTA: C:\orion
:: MODULO: setup.bat
:: AUTOR: Benedito Silva Filho
:: CRIADO EM: 2026-06-21 09:00 -03
:: ATUALIZADO EM: 2026-06-21 09:00 -03
:: VERSAO: 1.0.0
::
:: DESCRICAO:
::     Prepara o ambiente do projeto do zero.
::     Reutilizavel — substitua as variaveis na secao
::     CONFIGURACOES para usar em qualquer projeto.
::     v1.0.0: Criacao do modulo.
:: =========================================================

:: -------------------------------------------------------
:: CONFIGURACOES — altere aqui para cada projeto
:: -------------------------------------------------------
set PROJETO=orion
set DB_HOST=localhost
set DB_PORT=5433
set DB_USER=postgres
set PASTA=C:\orion

:: -------------------------------------------------------
:: Adiciona o PostgreSQL ao caminho do sistema
:: -------------------------------------------------------
set PATH=%PATH%;C:\Program Files\PostgreSQL\16\bin

:: -------------------------------------------------------
:: Apresentacao
:: -------------------------------------------------------
echo.
echo =====================================================
echo   SETUP DO AMBIENTE — Consiste
echo   Projeto : %PROJETO%
echo   Pasta   : %PASTA%
echo   Porta   : %PORTA_APP%
echo =====================================================
echo.
echo   Este script vai:
echo   1. Verificar o Python instalado
echo   2. Instalar as bibliotecas necessarias
echo   3. Criar o banco de dados
echo   4. Criar as tabelas
echo.
echo   ATENCAO: Sera solicitada a senha do PostgreSQL!
echo   Use a mesma senha de todos os projetos Consiste.
echo.
echo =====================================================
echo.
pause

:: -------------------------------------------------------
:: Passo 1 — Verifica o Python
:: -------------------------------------------------------
echo.
echo   [1/4] Verificando Python instalado...
echo.
python --version
if %ERRORLEVEL% NEQ 0 (
    echo   ERRO: Python nao encontrado!
    echo   Instale o Python em: https://www.python.org
    pause
    exit /b 1
)
echo   Python OK!

:: -------------------------------------------------------
:: Passo 2 — Instala as bibliotecas
:: -------------------------------------------------------
echo.
echo   [2/4] Instalando bibliotecas do requirements.txt...
echo.
cd /d %PASTA%
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo   ERRO: Falha ao instalar bibliotecas!
    pause
    exit /b 1
)
echo   Bibliotecas instaladas com sucesso!

:: -------------------------------------------------------
:: Passo 3 — Cria o banco de dados
:: -------------------------------------------------------
echo.
echo   [3/4] Criando banco de dados: %PROJETO%...
echo.
psql -U %DB_USER% -p %DB_PORT% -h %DB_HOST% -c "CREATE DATABASE %PROJETO%;"
if %ERRORLEVEL% == 0 (
    echo   Banco %PROJETO% criado com sucesso!
) else (
    echo   Banco %PROJETO% ja existe ou ocorreu um erro.
)

:: -------------------------------------------------------
:: Passo 4 — Cria as tabelas
:: -------------------------------------------------------
echo.
echo   [4/4] Criando tabelas do banco: %PROJETO%...
echo.
psql -U %DB_USER% -p %DB_PORT% -h %DB_HOST% -d %PROJETO% -f criar_tabelas.sql
if %ERRORLEVEL% == 0 (
    echo   Tabelas criadas com sucesso!
) else (
    echo   ERRO: Falha ao criar tabelas!
    pause
    exit /b 1
)

:: -------------------------------------------------------
:: Conclusao
:: -------------------------------------------------------
echo.
echo =====================================================
echo   SETUP CONCLUIDO COM SUCESSO!
echo   Projeto : %PROJETO%
echo   Para iniciar: execute o iniciar.bat
echo   ou rode: python app.py
echo =====================================================
echo.
pause

:: =========================================================
:: FIM DE ARQUIVO: setup.bat
:: ===========================