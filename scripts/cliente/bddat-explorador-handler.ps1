param([string]$Uri)
# Extraer la ruta quitando el esquema del protocolo personalizado
$path = $Uri -replace '^bddat-explorador://', ''
# URL-decode por si hay caracteres codificados (%20, etc.)
$path = [System.Uri]::UnescapeDataString($path)
# Convertir slashes a backslashes de Windows (soporta rutas locales y UNC)
$path = $path.Replace('/', '\')
# Abrir el Explorador de Windows seleccionando el fichero
Start-Process explorer.exe -ArgumentList "/select,`"$path`""
