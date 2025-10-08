@echo off
setlocal enabledelayedexpansion

:: Obter data atual no formato YYYY-MM-DD
for /f "tokens=1-3 delims=/" %%a in ("%date%") do (
    set "dia=%%a"
    set "mes=%%b"
    set "ano=%%c"
)

:: Ajustar formato para YYYY-MM-DD
set "data=!ano!-!mes!-!dia!"

:: Criar pasta de teste
set "destino=C:\oriun\10-bkp"
set "pastaBackup=!destino!\!data!"
mkdir "!pastaBackup!\projeto"

echo Pasta criada em: !pastaBackup!\projeto
pause
