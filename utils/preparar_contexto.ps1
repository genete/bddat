# 1. Configuración de exclusiones (Lista Negra)
# Se incluye 'utils' para que el script no se procese a sí mismo
$carpetasIgnorar = @("venv", ".venv", "__pycache__", ".git", ".playwright-mcp", "docs_prueba", "utils")
$archivosIgnorar  = @(".env", ".DS_Store", "contexto_completo_gemini.txt")

# Extensiones de archivos con lógica o configuración relevante
$extensionesValidas = @(
    ".py", ".html", ".md", ".css", ".js", ".json", 
    ".sql", ".toml", ".yaml", ".yml", ".ini", 
    ".mako", ".sh", ".ps1", ".bat", ".vbs", ".txt"
)

# El archivo se generará en la raíz del proyecto (..) para facilitar su detección y borrado
$output = "..\contexto_completo_gemini.txt"
"--- INICIO DE DUMP DE PROYECTO ---" | Out-File -FilePath $output -Encoding utf8

Write-Host "Iniciando empaquetado de contexto desde la raiz..." -ForegroundColor Cyan

# 2. Obtener todos los archivos desde la raíz del repositorio
# Al lanzarse desde 'utils', usamos '..' para subir un nivel
Get-ChildItem -Path ".." -Recurse -File | ForEach-Object {
    $item = $_
    
    # Calculamos la ruta relativa respecto a la raíz D:\BDDAT para que el log sea limpio
    $rootPath = (Resolve-Path "..").Path
    $relPath = $item.FullName.Replace($rootPath + "\", "")
    
    # Verificar si el archivo pertenece a una carpeta que debemos ignorar
    $ignorarPorCarpeta = $false
    foreach ($carpeta in $carpetasIgnorar) {
        if ($relPath -like "$carpeta\*" -or $relPath -split '\\' -contains $carpeta) {
            $ignorarPorCarpeta = $true
            break
        }
    }

    # FILTRO CRÍTICO: 
    # 1. No está en carpeta ignorada
    # 2. No es un nombre de archivo prohibido (.env, etc.)
    # 3. Tiene una extensión válida O es el archivo de licencia (LICENSE)
    if (-not $ignorarPorCarpeta -and $item.Name -notin $archivosIgnorar) {
        
        if ($item.Extension.ToLower() -in $extensionesValidas -or $item.Name -eq "LICENSE") {
            
            Add-Content -Path $output -Value "`n--- FILE: $relPath ---"
            
            # Intentamos leer el contenido. Si hay error (archivo binario o bloqueo), lo saltamos.
            try {
                $contenido = Get-Content $item.FullName -Raw -ErrorAction Stop
                Add-Content -Path $output -Value $contenido
                Add-Content -Path $output -Value "`n"
                Write-Host "Incluido: $relPath" -ForegroundColor Green
            } catch {
                Write-Host "Saltado (Error de lectura): $relPath" -ForegroundColor Yellow
            }
        }
    }
}

Write-Host "`n¡Listo! El contexto se ha guardado en la raiz: contexto_completo_gemini.txt" -ForegroundColor Cyan