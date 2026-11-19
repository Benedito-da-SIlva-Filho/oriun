@echo off
:: =========================================================
:: PROJETO: Orion
:: PASTA: C:\orion
:: MODULO: criar_banco.bat
:: AUTOR: Benedito Silva Filho
:: CRIADO EM: 2026-06-21 08:48 -03
:: ATUALIZADO EM: 2026-06-21 08:48 -03
:: VERSAO: 1.1.0
::
:: DESCRICAO:
::     Cria o banco de dados do projeto.
::     Reutilizavel — substitua as variaveis na secao
::     CONFIGURACOES para usar em qualquer projeto.
::     v1.0.0: Criacao do modulo.
::     v1.1.0: Aviso de senha adicionado.
:: =========================================================

:: -------------------------------------------------------
:: CONFIGURACOES — altere aqui para cada projeto
:: -------------------------------------------------------
set PROJETO=orion
set DB_HOST=localhost
set DB_PORT=5433
set DB_USER=postgres

:: -------------------------------------------------------
:: Adiciona o PostgreSQL ao caminho do sistema
:: -------------------------------------------------------
set PATH=%PATH%;C:\Program Files\PostgreSQL\16\bin

:: -------------------------------------------------------
:: Apresentacao
:: -------------------------------------------------------
echo.
echo =====================================================
echo   CRIADOR DE BANCO DE DADOS — Consiste
echo   Projeto : %PROJETO%
echo   Host    : %DB_HOST%
echo   Porta   : %DB_PORT%
echo   Usuario : %DB_USER%
echo =====================================================
echo.
echo   ATENCAO: Sera solicitada a senha do PostgreSQL!
echo   Use a mesma senha de todos os projetos Consiste.
echo.
echo =====================================================
echo.
pause

:: -------------------------------------------------------
:: Cria o banco de dados
:: -------------------------------------------------------
echo   Criando banco: %PROJETO%...
echo.
psql -U %DB_USER% -p %DB_PORT% -h %DB_HOST% -c "CREATE DATABASE %PROJETO%;"

if %ERRORLEVEL% == 0 (
    echo.
    echo   Banco %PROJETO% criado com sucesso!
) else (
    echo.
    echo   Banco %PROJETO% ja existe ou ocorreu um erro.
)

:: -------------------------------------------------------
:: Executa o script SQL de criacao das tabelas
:: -------------------------------------------------------
echo.
echo =====================================================
echo   Criando tabelas do banco: %PROJETO%...
echo =====================================================
echo.
psql -U %DB_USER% -p %DB_PORT% -h %DB_HOST% -d %PROJETO% -f criar_tabelas.sql

echo.
echo =====================================================
echo   Concluido! Banco %PROJETO% esta pronto.
echo =====================================================
echo.
pause

:: =========================================================
:: FIM DE ARQUIVO: criar_banco.bat
:: =========================================================