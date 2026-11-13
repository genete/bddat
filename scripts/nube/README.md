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
| **Expediente-tipo por la interfaz (#1106)** | `bash scripts/nube/guion_interfaz.sh --nuevo` | a demanda; arranca la app y prepara Playwright |
| **Consultar legislación con `/legalize`** | `bash scripts/nube/preparar_legalize.sh` | una vez por contenedor; a demanda, no en el hook |

## Ficheros

| Fichero | Qué hace |
|---|---|
| `preparar_entorno.sh` | Parte A de #949: Python 3.14 en `~/.venvs/bddat`, PostgreSQL 16, roles, `.env`, BD de tests y LibreOffice Writer. Lo llama el hook (`.claude/hooks/session-start.sh`). Idempotente, ~2 s si ya está todo. Detalle en `tests/README.md` §Fuera del PC. |
| `preparar_bd_desarrollo.py` | BD `bddat` desde las migraciones más la semilla de tests: 4 expedientes y 7 usuarios. **Se niega a correr fuera de la nube**, sin opción de forzarlo: en el PC sembraría usuarios con contraseña `test` en la BD de desarrollo real. |
| `arrancar_app.sh` | Entorno → BD de desarrollo → build de React si faltan bundles → `python run.py` en segundo plano (`127.0.0.1:5000`, log en `~/.cache/bddat-app.log`). |
| `guion_interfaz.sh` | Preparador del guion de interfaz de #1106: `arrancar_app.sh`, `playwright` para Python en el venv si falta, `CHROMIUM_PATH` y las credenciales de la semilla (`BDDAT_UI_USUARIO`/`BDDAT_UI_PASSWORD`, solo si no vienen puestas) y el guion con los argumentos que se le pasen. No duplica el guion: es el mismo módulo que en el PC. |
| `preparar_legalize.sh` / `legalize_patrones.py` | Clon reducido de legalize-es para `/legalize` (ver más abajo). A demanda. |
| `captura.mjs` | Login, navegación y captura con el Playwright para Node del contenedor. Informa de peticiones fallidas por host, respuestas 4xx/5xx de la app y errores de consola. |

## La BD de desarrollo de la nube

No es la del PC ni debe parecerlo: la construye `semilla_test.sembrar()`, la
misma de la suite.

- **Usuarios** (contraseña `test`): TADM, TSUP, TTRA, TADV, TMUL (varios roles:
  login de dos pasos), TTR2 y TOFF.
- **Expedientes:** los tres de `scripts/expedientes_dummy/` y uno sin responsable.
- **Plantillas:** las cinco que siembran las migraciones no tienen fichero y están
  desactivadas. La semilla añade cinco **de demostración** (`DEMO_*`, activas) y un
  fragmento (`DEMO_Pie`), una por trámite ELABORAR de los expedientes-tipo, para generar
  escritos (ver «Generar escritos» más abajo).
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
los ficheros de `es/` de cada `id_tecnico` `BOE-A-*` de
`docs/referencia/normas_catalog.csv` (los patrones los calcula
`legalize_patrones.py`). Es idempotente: si el clon existe, hace `fetch --depth 1`
y recalcula los patrones; si `LEGALIZE_DIR` apunta a un clon no sparse, se niega a
tocarlo. Al final imprime nº de normas, tamaño, commit y fecha.

**Layout de legalize-es**: los ficheros no están en `es/<id>.md`, sino repartidos en
subcarpetas con los 2 primeros hex del SHA-1 del id (`es/fa/BOE-A-2000-24019.md`,
`es-an/17/BOJA-b-2020-90326.md`; lo declara el `.legalize.yml` del repo). El layout
plano de antes dejó el script con «0 de 101 ids» (2026-11-06). `legalize_patrones.py`
ya no lo asume ni calcula el SHA-1: indexa el árbol de git por nombre de fichero. Si
no encuentra **ningún** id del catálogo, sale con error y enseña qué rutas ve (en vez
de dejar un clon casi vacío), y `preparar_legalize.sh` no toca el sparse checkout.
Los skills y scripts que lean el clon deben localizar por nombre (`Glob
"*/*/<id>.md"`), no por ruta directa.

Medido en la nube (2026-11-06, commit `10a77ba` de legalize-es): **~74 MB (16 MB de
`.git`), 18 s, 422 ficheros** (`es/` 98, `es-an/` 324). El catálogo tiene 101 ids
`BOE-A-*`/`BOJA-b-*`: están los 101 (el RD 917/2025, `BOE-A-2025-20694`, que en
septiembre aún no estaba publicado, ya figura).

### `/boe` y `/boja` en la nube

Necesitan que el entorno permita `www.boe.es` y `ws040.juntadeandalucia.es` (*Network
access*, en la configuración del entorno). Con eso funcionan sin más: `/boe` por
`scripts/boe_extract.py` y `/boja` por `scripts/sedeboja_extract.py` (probado el
2026-09-29: índice, artículos y `--todo`). Lo que no existe en la nube es Playwright
MCP ni windows-mcp: los flujos de navegador de esos skills son solo del PC.

Límites:

- **`NOT_FOUND` no prueba nada** en el clon reducido: `es/` solo trae las normas del
  catálogo. Para una fuera de él, `/boe` o `/boja`.
- **`legalize_xref.py` y `legalize_compile.py` necesitan el clon COMPLETO** (solo PC):
  buscan en todo el corpus y con este darían resultados incompletos sin avisar.

## Generar escritos: no con plantillas reales

Las plantillas reales del supervisor no están en git: viven en el almacén y la BD
(ADR-050 §J, #1009), subidas desde el navegador. En la nube **no hay ninguna**, y no las
habrá. Lo único versionado son
las bases canónicas de `app/data/plantillas_base/` (`carta_base.odt`,
`resolucion_base.odt`, `fragmento_base.odt`), que son esqueletos sin tokens.

Comprobado el 2026-09-29: con LibreOffice Writer, `generar_escrito` produce un `.odt`
desde esas bases y `soffice --headless --convert-to pdf` lo convierte (código 0). Es
decir, el motor y la conversión funcionan en la nube; lo que no se puede verificar
es que **una plantilla real, con sus tokens y fragmentos, saque el escrito correcto
con los datos de un expediente**. Eso se verifica en el PC. Los tests
(`test_182`, `test_732`) usan fixtures propios de `tests/fixtures/`.

No se repuntan a las bases las plantillas que crean las migraciones (`RESOLUCION`,
`NOTIF_ORGANISMO`…): representan las plantillas reales y quedarían haciéndose pasar
por ellas. Con la fase 4 de ADR-050 (#1009) la semilla registra, con su propio código,
**plantillas de demostración** (`scripts/plantillas_demo.py`): sintéticas, hechas desde
las bases con unos marcadores (`numero_at`, `titular_nombre`, `fecha_hoy`) y la cita al
fragmento `DEMO_Pie`, y con el tipo de documento y el contexto ESFTT de cada trámite. Las
dos del análisis de la solicitud (`REQUERIMIENTO_SUBSANACION` y `COMUNICACION_INICIO_ADMISION`)
declaran además su Context Builder y escriben sus tokens (`defectos_*`; `actos` y
`fecha_recepcion_solicitud`).
Con ellas se puede generar un escrito de punta a punta desde un expediente dummy, por la
ruta real (`POST /api/escritos/generar`). Para registrarlas (o quitarlas) a mano en la BD
del `.env`: `python scripts/plantillas_demo.py [--claves …] [--prefijo …] [--quitar]`. Dos límites: la tarea tiene que estar en una
fase **abierta** (en una cerrada el sellado de fase lo impide), y solo hay `.odt`.

## Expedientes-tipo por la interfaz (#1106)

`scripts/expedientes_dummy/interfaz/` recrea un expediente-tipo con Playwright **para Python** (el de Node de arriba
solo sirve a `captura.mjs`). Un solo comando, que prepara lo que falte y pasa los argumentos al guion:

```bash
bash scripts/nube/guion_interfaz.sh --nuevo
```

Qué hace por debajo, por si hay que hacerlo a mano: `arrancar_app.sh`; `uv pip install --python ~/.venvs/bddat/bin/python
playwright` (el venv lo crea `uv` y **no tiene `pip`**: `-m pip` da «No module named pip»); `CHROMIUM_PATH=/opt/pw-browsers/chromium`
(sin él, Playwright busca su propio Chromium y falla con «Executable doesn't exist»; `playwright install` no sirve aquí) y
las credenciales de la semilla, que el guion lee de `BDDAT_UI_USUARIO` / `BDDAT_UI_PASSWORD` (el script usa `TTRA` /
`test` si no están puestas; con otro usuario, exportarlas o pasar `--usuario` / `--password`).

Necesita las plantillas DEMO de `REQUERIMIENTO_SUBSANACION` y `COMUNICACION_INICIO_ADMISION`, que la semilla de la nube
ya registra. Por defecto el responsable es el usuario del login (con TTRA está en el desplegable del alta; si no
estuviera, el guion falla y pide `--responsable "Apellido, Nombre"`).

**Probado en la nube (2026-11-13), contenedor limpio:** 79/79 acciones (80/80 con `--nuevo` sobre un expediente anterior,
que añade el reciclado), fase «pendiente de cierre» y reloj de desarrollo fijado en la fecha de la última respuesta del
titular. Tiempos: `arrancar_app.sh` ~75 s la primera vez (BD y semilla ~20 s, bundles de React ~9 s, arranque ~40 s);
Playwright ~26 s (51 MB); el guion ~90 s. Resolvió Playwright 1.65.1 con el Chromium 153 de la imagen (Playwright espera el
158): funciona con `CHROMIUM_PATH`; fijar `playwright==1.63.0`, la versión del Playwright de Node de la imagen, también
encuentra el Chromium sin esa variable (probado el arranque, no el guion entero). Cada ejecución deja datos en la BD de
desarrollo de la nube y el reloj fijado: «Usar fecha real» en la barra superior lo quita. Detalle y requisitos en
`scripts/expedientes_dummy/interfaz/README.md`.

## Lo que sigue necesitando el PC (#949 §D)

Datos reales de la BD de desarrollo, rutas de Windows y plantillas reales, el MCP
de PostgreSQL y el de Windows, `flask_console.py`, `comparar_catalogo.py` contra
la BD real y regenerar los fixtures ODT (`scripts/fabricar_*.py`).
