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

## Ficheros

| Fichero | Qué hace |
|---|---|
| `preparar_entorno.sh` | Parte A de #949: Python 3.14 en `~/.venvs/bddat`, PostgreSQL 16, roles, `.env`, BD de tests y LibreOffice Writer. Lo llama el hook (`.claude/hooks/session-start.sh`). Idempotente, ~2 s si ya está todo. Detalle en `tests/README.md` §Fuera del PC. |
| `preparar_bd_desarrollo.py` | BD `bddat` desde las migraciones más la semilla de tests: 4 expedientes y 7 usuarios. **Se niega a correr fuera de la nube**, sin opción de forzarlo: en el PC sembraría usuarios con contraseña `test` en la BD de desarrollo real. |
| `arrancar_app.sh` | Entorno → BD de desarrollo → build de React si faltan bundles → `python run.py` en segundo plano (`127.0.0.1:5000`, log en `~/.cache/bddat-app.log`). Avisa si los CDN están bloqueados. |
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

## Requisito que no está en el repo: los CDN

`base_app.html` y `base_login.html` cargan la CSS de la Junta y Bootstrap desde
`cdn.juntadeandalucia.es` y `cdn.jsdelivr.net`. Si la política de red del
entorno los bloquea, la app funciona pero se ve rota: sin estilos, con
`bootstrap is not defined` y los modales y menús desplegados. **Se arregla en
claude.ai**, en la configuración del entorno, apartado *Network access*,
añadiendo esos dos dominios.

Mientras tanto, hay un apaño **solo para las capturas**. `arrancar_app.sh`
descarga de npm, que sí es accesible, Bootstrap 5.3.3 y bootstrap-icons 1.11.1 en
`~/.cache/bddat-cdn`, y `captura.mjs` sirve desde ahí las peticiones al CDN:

| Recurso del CDN | Se sirve | Fidelidad |
|---|---|---|
| `bootstrap-icons@1.11.1` | el mismo paquete de npm | idéntico |
| `bootstrap.bundle.min.js` de la Junta | el de Bootstrap 5.3.3 | equivalente (modales, menús) |
| `custom-jda-bootstrap.css` | `bootstrap.min.css` estándar | **aproximado**: sin colores ni fuentes de la Junta |
| `fonts.css`, `all.css` de la Junta | vacíos | se pierden las fuentes y los iconos propios de la Junta |

La captura sale legible, pero **no sirve para juzgar detalles visuales finos**.
`captura.mjs` lo avisa cada vez que usa la copia, y deja de usarla en cuanto el
CDN responde.

## Lo que sigue necesitando el PC (#949 §D)

Datos reales de la BD de desarrollo, rutas de Windows y plantillas reales, el MCP
de PostgreSQL y el de Windows, `flask_console.py`, `comparar_catalogo.py` contra
la BD real y regenerar los fixtures ODT (`scripts/fabricar_*.py`).
