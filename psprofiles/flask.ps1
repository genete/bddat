$esc = [char]27

function Set-TabColor { param([int]$c) Write-Host "$esc[2;15;$c,|" -NoNewline }
function Set-TabTitle { param([string]$t) Write-Host "$esc]0;$t$esc\" -NoNewline }

Set-Location "D:\BDDAT"

# Activar entorno virtual si existe
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
}

Set-TabColor 2   # Verde
Set-TabTitle "FLASK"