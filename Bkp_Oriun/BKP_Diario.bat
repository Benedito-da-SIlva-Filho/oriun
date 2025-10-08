# Caminhos
$origem = "C:\oriun\oriun-app"
$destinoBase = "C:\oriun\bkp_oriun"

# Data atual
$data = Get-Date -Format "yyyy-MM-dd"
$destino = "$destinoBase\$data\projeto"

# Criar pasta somente se não existir
if (!(Test-Path $destino)) {
    New-Item -ItemType Directory -Path $destino -Force
}

# Copiar arquivos (exceto node_modules)
robocopy $origem $destino /E /XD "$origem\node_modules"

Write-Host "✅ Backup realizado com sucesso em: $destino"
