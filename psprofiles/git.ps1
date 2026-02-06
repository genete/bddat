$esc = [char]27

function Set-TabColor { param([int]$c) Write-Host "$esc[2;15;$c,|" -NoNewline }
function Set-TabTitle { param([string]$t) Write-Host "$esc]0;$t$esc\" -NoNewline }

Set-Location "D:\BDDAT"

Set-TabColor 4   # Azul
Set-TabTitle "GIT"