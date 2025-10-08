@echo off
setlocal

set "origem=C:\oriun\oriun-app"
set "destino=C:\oriun\10-bkp"

for /f %%i in ('powershell -command "Get-Date -Format yyyy-MM-dd"') do set "data=%%i"

set "pastaBackup=%destino%\%data%"
mkdir "%pastaBackup%\projeto"

xcopy "%origem%" "%pastaBackup%\projeto\" /E /I

echo Backup realizado com sucesso em: %pastaBackup%
pause
