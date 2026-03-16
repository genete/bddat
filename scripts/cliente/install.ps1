# Instalador del protocolo URI bddat-explorador://
# No requiere privilegios de administrador (usa HKEY_CURRENT_USER)
# Instala los scripts en %LOCALAPPDATA%\bddat-tools\

$installDir = "$env:LOCALAPPDATA\bddat-tools"
$handlerSrc  = Join-Path $PSScriptRoot "bddat-explorador-handler.ps1"
$handlerDst  = Join-Path $installDir   "bddat-explorador-handler.ps1"
$launcherSrc = Join-Path $PSScriptRoot "bddat-explorador-launcher.vbs"
$launcherDst = Join-Path $installDir   "bddat-explorador-launcher.vbs"

# Crear directorio de instalacion
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

# Copiar el handler y el launcher VBS
Copy-Item -Path $handlerSrc  -Destination $handlerDst  -Force
Copy-Item -Path $launcherSrc -Destination $launcherDst -Force

# Construir el comando que el registro ejecutara al activarse la URI.
# wscript.exe //B lanza el VBS completamente oculto (sin ventana de consola).
# El VBS a su vez invoca powershell con ventana oculta desde el nivel del SO.
$command = "`"$env:SystemRoot\System32\wscript.exe`" //B //NoLogo `"$launcherDst`" `"%1`""

# Registrar el protocolo en HKEY_CURRENT_USER (sin admin)
$regBase = "HKCU:\SOFTWARE\Classes\bddat-explorador"
New-Item -Path $regBase -Force | Out-Null
Set-ItemProperty -Path $regBase -Name "(Default)" -Value "BDDAT Explorador de Plantillas"
Set-ItemProperty -Path $regBase -Name "URL Protocol" -Value ""
New-Item -Path "$regBase\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path "$regBase\shell\open\command" -Name "(Default)" -Value $command

Write-Host ""
Write-Host "Protocolo bddat-explorador:// instalado correctamente." -ForegroundColor Green
Write-Host "Handler en: $handlerDst" -ForegroundColor Cyan
Write-Host ""
