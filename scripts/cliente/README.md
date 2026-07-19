# scripts/cliente/

Instalador cliente del protocolo URI personalizado `bddat-explorador://`.
Se ejecuta en el PC del usuario (no en el servidor) para permitir que un
enlace de la web abra el Explorador de Windows con un fichero local ya
seleccionado — algo que JavaScript no puede hacer directamente por las
restricciones del navegador.

## Ficheros

| Fichero | Rol |
|---|---|
| `install.ps1` | Instalador real. Sin privilegios de admin (usa `HKEY_CURRENT_USER`). Copia el handler y el launcher a `%LOCALAPPDATA%\bddat-tools\` y registra el protocolo en el registro de Windows. |
| `install.bat` | Envoltorio de doble clic para `install.ps1` (`-ExecutionPolicy Bypass` + `pause`). |
| `bddat-explorador-launcher.vbs` | Windows lo invoca al resolver la URI. Lanza PowerShell oculto (`-WindowStyle Hidden`) sin parpadeo de consola. |
| `bddat-explorador-handler.ps1` | Lógica real: decodifica la URI, convierte `/` a `\` y ejecuta `explorer.exe /select,"<ruta>"`. |

## Uso

```bash
scripts\cliente\install.bat
```

Flujo tras la instalación: clic en `bddat-explorador://...` (generado por
`app/modules/admin_plantillas/routes.py::_rutas_fichero`) → registro de
Windows → `wscript` (launcher, oculto) → `powershell` (handler, oculto) →
Explorador abierto con el fichero seleccionado.

## Dónde se usa en el servidor

- **[app/modules/admin_plantillas/routes.py](../../app/modules/admin_plantillas/routes.py)** —
  `_rutas_fichero(plantilla)` construye la URI a partir de la ruta absoluta
  del `.docx`.
- **[_detalle_fragmento.html](../../app/modules/admin_plantillas/templates/admin_plantillas/_detalle_fragmento.html)** —
  botón "Abrir en Explorador" con `href="{{ uri_explorador }}"`.

## Decisión de diseño: sin detección JS del fallo del protocolo

Existe una técnica conocida para detectar si un protocolo personalizado no
está instalado (redirigir a la URI y comprobar si la pestaña pierde el foco
en ~1-2s; si no, asumir fallo). **Decidido no implementarla** (2026-07-19):

- Es poco fiable entre navegadores — depende de heurísticas de
  `blur`/timeout, y da falsos positivos cuando el propio diálogo de
  seguridad del navegador ("¿permitir abrir esta app?") ya dispara el blur.
- No hace falta: el fallback ya está **siempre visible**, no oculto a la
  espera de un fallo. Junto al botón "Abrir en Explorador",
  `_detalle_fragmento.html` siempre muestra:
  1. Enlace **"Descargar"** — vía `admin_plantillas.descargar`, ruta Flask normal.
  2. Campo de **ruta absoluta + botón "Copiar ruta"** — para pegar a mano en el Explorador.

Si el protocolo no está instalado, Windows muestra su diálogo nativo de
"no hay aplicación asociada" al pulsar el botón; la web no lo intercepta,
pero el usuario siempre tiene las otras dos vías disponibles.
