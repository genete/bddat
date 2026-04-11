---
name: ctx
description: Muestra el valor de contexto actual (ctx %) de la barra de estado del CLI capturando la franja inferior de la ventana WindowsTerminal.
allowed-tools: mcp__windows-mcp__PowerShell, Read
---

Muestra el porcentaje de contexto visible en la barra de estado de Claude Code.

## Pasos

### 1. Localizar la ventana WindowsTerminal y obtener sus coordenadas

Usa `mcp__windows-mcp__PowerShell` con este script para encontrar la ventana y capturar la franja inferior:

```powershell
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public struct WRECT { public int Left, Top, Right, Bottom; }
public class WFinder {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out WRECT rect);
}
"@
Add-Type -AssemblyName System.Drawing

$found = $null
$cb = [WFinder+EnumWindowsProc]{
    param($h, $l)
    if ([WFinder]::IsWindowVisible($h)) {
        $sb = New-Object System.Text.StringBuilder(256)
        [WFinder]::GetWindowText($h, $sb, 256) | Out-Null
        if ($sb.ToString() -match "WindowsTerminal|Claude|Terminal|PowerShell") {
            $r = New-Object WRECT
            [WFinder]::GetWindowRect($h, [ref]$r) | Out-Null
            if (($r.Right - $r.Left) -gt 400) {
                $script:found = $r
                return $false
            }
        }
    }
    return $true
}
[WFinder]::EnumWindows($cb, [IntPtr]::Zero) | Out-Null

if ($null -eq $found) { Write-Host "ERROR: ventana no encontrada"; exit 1 }

$left = $found.Left; $bottom = $found.Bottom; $right = $found.Right; $top = $found.Top
$width = $right - $left
$stripH = 80
$stripTop = $bottom - $stripH

$bmp = New-Object System.Drawing.Bitmap($width, $stripH)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($left, $stripTop, 0, 0, [System.Drawing.Size]::new($width, $stripH))
$g.Dispose()
$out = "D:\BDDAT\docs_prueba\temp\ctx_strip.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Host "OK:$left,$top,$right,$bottom"
```

### 2. Leer la imagen capturada

Usa la herramienta `Read` para leer el fichero `D:\BDDAT\docs_prueba\temp\ctx_strip.png`.
Claude interpretará visualmente la imagen y extraerá el texto de la barra de estado.

### 3. Mostrar el resultado

Extrae el valor `ctx XX%` de la barra de estado y muéstralo de forma destacada.
El formato típico es: `HH:MM:SS | ruta | modelo | ctx XX%`

Responde con una sola línea concisa mostrando el porcentaje de contexto encontrado.
Por ejemplo: **ctx 13%** (o el valor que aparezca en la imagen).
