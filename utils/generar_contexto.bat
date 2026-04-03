@echo off
SETLOCAL
:: Definir la raíz del proyecto relativa a la ubicación del bat
SET "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

echo [IA-TOOLS] Iniciando generacion de contexto para Gemini...
echo [IA-TOOLS] Directorio raiz: %CD%

:: Ejecutar PowerShell saltando la restricción de ejecución solo para este proceso
powershell -NoProfile -ExecutionPolicy Bypass -File "utils\preparar_contexto.ps1"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Archivo generado con exito.
    echo [!] Recuerda subirlo a la nueva conversacion y borrarlo despues.
) else (
    echo.
    echo [ERROR] Hubo un problema al generar el archivo.
)

pause
ENDLOCAL