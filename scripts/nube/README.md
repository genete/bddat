# scripts/nube/ — desarrollo en una sesión de Claude Code en la nube

Todo lo que hace falta para trabajar en BDDAT desde una sesión en la nube
(contenedor Linux, abierta desde el navegador o el móvil) sin el PC de
desarrollo. Origen: #949. **Nada de esto actúa en el PC**: cada script comprueba
`CLAUDE_CODE_REMOTE=true`.

| Para | Qué ejecutar | Cuándo |
|---|---|---|
| **Tests** | nada: lo hace el hook `SessionStart` al abrir la sesión | siempre |
| Rearrancar tras un reciclado del contenedor | `bash scripts/nube/preparar_entorno.sh` | los tests dan «connection refused» |
| **Arrancar la app** | `bash scripts/nube/arrancar_app.sh` | antes de verificar la interfaz |
| Parar la app | `bash scripts/nube/arrancar_app.sh --parar` | |
| **Verificar en el navegador** | `node scripts/nube/captura.mjs <ruta> [--usuario X --rol Y]` | con la app arrancada |
| **Consultar legislación con `/legalize`** | `bash scripts/nube/preparar_legalize.sh` | una vez por contenedor; a demanda, no en el hook |

## Ficheros

| Fichero | Qué hace |
|---|---|
| `preparar_entorno.sh` | Parte A de #949: Python 3.14 en `~/.venvs/bddat`, PostgreSQL 16, roles, `.env`, BD de tests y LibreOffice Writer. Lo llama el hook (`.claude/hooks/session-start.sh`). Idempotente, ~2 s si ya está todo. Detalle en `tests/README.md` §Fuera del PC. |
| `preparar_bd_desarrollo.py` | BD `bddat` desde las migraciones más la semilla de tests: 4 expedientes y 7 usuarios. **Se niega a correr fuera de la nube**, sin opción de forzarlo: en el PC sembraría usuarios con contraseña `test` en la BD de desarrollo real. |
| `arrancar_app.sh` | Entorno → BD de desarrollo → build de React si faltan bundles → `python run.py` en segundo plano (`127.0.0.1:5000`, log en `~/.cache/bddat-app.log`). |
| `preparar_legalize.sh` / `legalize_patrones.py` | Clon reducido de legalize-es para `/legalize` (ver más abajo). A demanda. |
| `captura.mjs` | Login, navegación y captura con el Playwright para Node del contenedor. Informa de peticiones fallidas por host, respuestas 4xx/5xx de la app y errores de consola. |

## La BD de desarrollo de la nube

No es la del PC ni debe parecerlo: la construye `semilla_test.sembrar()`, la
misma de la suite.

- **Usuarios** (contraseña `test`): TADM, TSUP, TTRA, TADV, TMUL (varios roles:
  login de dos pasos), TTR2 y TOFF.
- **Expedientes:** los tres de `scripts/expedientes_dummy/` y uno sin responsable.
- **Plantillas desactivadas:** las que siembran las migraciones apuntan a `.docx`
  que aquí no existen. Para generar un escrito hay que registrar antes una
  plantilla.
- **Sin reloj simulado:** los expedientes se construyen con `efectos_desarrollo=False`.

## Login de dos pasos

`/auth/login` pide `siglas` y `password`. Con un usuario de un solo rol (TTRA)
basta con eso. Con varios (TMUL), la página vuelve con un `<select name="rol_id">`:
se elige el rol y se envía otra vez. En los dos casos se entra en
`/seguimiento_y_huerfanos/`. `captura.mjs` ya lo hace (`--usuario TMUL --rol SUPERVISOR`).

## Estilos: sin CDN (#984)

La app ya no carga nada de fuera: la base de la Junta (CSS, JS y tipografías) y
Bootstrap Icons se sirven desde `app/static/vendor/`. Las capturas de la nube
salen con la identidad visual real de la Junta, sin apaños de red ni permisos en
claude.ai. Origen, licencias y cómo actualizar: `app/static/vendor/LEEME.md`.

## legalize-es reducido (`preparar_legalize.sh`)

El skill `/legalize` lee de un clon de legalize-es. En la nube no existe
`/d/legalize-es`, así que el script deja uno **reducido** en
`${LEGALIZE_DIR:-$HOME/legalize-es}` (fuera del repo): `git clone --depth 1
--filter=blob:none --sparse` y sparse checkout sin conos con `es-an/` completo más
los ficheros `es/<id>.md` de cada `id_tecnico` `BOE-A-*` de
`docs/referencia/normas_catalog.csv` (los patrones los calcula
`legalize_patrones.py`). Es idempotente: si el clon existe, hace `fetch --depth 1`
y recalcula los patrones; si `LEGALIZE_DIR` apunta a un clon no sparse, se niega a
tocarlo. Al final imprime nº de normas, tamaño, commit y fecha.

Medido en la nube (2026-09-29, commit `3afca50` de legalize-es): **~56 MB (14 MB de
`.git`), 5 s, 339 ficheros** (`es/` 97, `es-an/` 242). El catálogo tiene 101 ids
`BOE-A-*`/`BOJA-b-*`: 100 están en el clon; falta `BOE-A-2025-20694` (RD 917/2025),
que legalize-es aún no publica.

Límites:

- **`NOT_FOUND` no prueba nada** en el clon reducido: `es/` solo trae las normas del
  catálogo. Para una fuera de él, `/boe` o `/boja`.
- **`legalize_xref.py` y `legalize_compile.py` necesitan el clon COMPLETO** (solo PC):
  buscan en todo el corpus y con este darían resultados incompletos sin avisar.

## Lo que sigue necesitando el PC (#949 §D)

Datos reales de la BD de desarrollo, rutas de Windows y plantillas reales, el MCP
de PostgreSQL y el de Windows, `flask_console.py`, `comparar_catalogo.py` contra
la BD real y regenerar los fixtures ODT (`scripts/fabricar_*.py`).
