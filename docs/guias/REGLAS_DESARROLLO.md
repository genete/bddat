# Reglas de desarrollo — BDDAT

## Qué leer según la tarea

| Tarea | Secciones relevantes |
|---|---|
| Solo HTML / CSS / JS | Flask › Templates · Notificaciones · Commits |
| Modelos o migraciones | Flask › Modelos · Migraciones · Naming · Commits |
| Commit o rama | Ramas · Commit directo vs rama · Commits |
| Cierre de milestone | Releases |
| Decisión de diseño | Decisiones arquitectónicas |
| Nueva ruta o template con expediente / rol | Control de acceso |
| Ruta que edita un registro existente (POST/PATCH) | Rutas que editan un registro existente |
| Isla React (nueva o cambio) | React (islas) · `docs/guias/GUIA_REACT_ISLAS.md` |
| Probar una guarda de plazo sin editar fechas a mano | Reloj de desarrollo |

---

## Ramas

- `develop` — rama por defecto; todo cambio pasa por aquí
- `main` — solo recibe merges desde develop al cerrar milestone; lleva tags `vMAJOR.MINOR.PATCH`
- Ramas temporales nacen de develop y vuelven via PR; borrar remota inmediatamente tras merge
- No squash merge — preservar historial completo de commits

**Naming:** `feature/issue-XX-descripcion` · `bugfix/issue-XX-descripcion` · `refactor/descripcion` · `docs/descripcion`

---

## Commit directo vs rama temporal

**Commit directo en develop** — docs, typos, 1-2 ficheros sin lógica de negocio, sin necesidad de `flask run`.
Si el commit resuelve un issue, cerrarlo a mano (sin PR no hay auto-close):
`gh issue close <N> --comment "Resuelto en commit <SHA> (develop)."`

**Rama + PR** — 3+ ficheros, modelos, rutas, templates, migraciones, cualquier cambio que requiera prueba funcional.

---

## Análisis de impacto previo a refactorizaciones

Ante cualquier cambio de diseño que elimine o cambie el contrato de un concepto
(tabla, modelo, servicio, función, endpoint, verbo del motor, script...):

**Antes de escribir código**, enumerar todos los consumidores en TODO el sistema
y clasificar cada uno con una acción:

| Capa | Dónde buscar |
|------|--------------|
| Modelos y servicios | `app/models/`, `app/services/` |
| Rutas y módulos | `app/routes/`, `app/modules/` |
| Tests | `tests/` |
| Scripts | `scripts/` — incluyendo prerequisitos documentados entre scripts |
| Migraciones | `migrations/versions/` |
| Documentación | `docs/*/*`, `*/README.md`, docstrings de módulo |

Acción para cada consumidor encontrado:
- **Actualizar** — sigue siendo válido con el nuevo diseño
- **Eliminar** — asumía algo que ya no existe
- **Dejar** — zona congelada (historial, ADRs); anotarlo explícitamente

Presentar ese mapa como tabla al usuario y esperar confirmación **antes de implementar**.
No hay excepciones por "es pequeño" o "es evidente".

---

## Rutas que editan un registro existente

Una petición HTTP tiene **tres** estados posibles para cada campo, y hay que
distinguir los tres:

| Estado | Qué significa | Qué hacer |
|---|---|---|
| **Ausente** | el cliente no habla de ese campo | **no tocarlo** |
| **Presente y vacío** | el usuario lo ha vaciado a propósito | vaciarlo (NULL), o error de validación si la columna es NOT NULL |
| **Presente con valor** | edición normal | escribirlo |

`request.form.get('x') or None` colapsa los dos primeros, así que cualquier cuerpo
parcial —un `fetch` que manda solo lo que cambió, un test, un template cacheado
antiguo— **borra en silencio todo lo que no menciona**. En #832 eso vació dos FK,
tres flags técnicos y la tensión de tres expedientes, y las observaciones de tres
solicitudes; en #825, los vínculos CONSUMIDO que disparan un plazo.

No escribir esto a mano: usar `app/utils/formularios.py`.

```python
from app.utils.formularios import aplicar_fk, aplicar_texto_obligatorio, form_completo

completo = form_completo(request.form)   # centinela _form_completo
errores = []

aplicar_fk(request.form, 'tipo_expediente_id', expediente)
aplicar_texto_obligatorio(request.form, 'titulo', proyecto,
                          'El título del proyecto es obligatorio.', errores)
aplicar_checkbox(request.form, 'sin_linea_aerea', proyecto, completo)
```

Tres cosas que no son obvias:

1. **Las casillas necesitan centinela.** En HTML un checkbox desmarcado **no se
   envía**, así que su ausencia no se distingue de un cuerpo parcial. El formulario
   completo declara `<input type="hidden" name="_form_completo" value="1">` y sin él
   `aplicar_checkbox` no escribe nada.
2. **`or objeto.campo` no es el arreglo.** Conserva el valor por omisión, sí, pero a
   cambio hace imposible vaciar el campo a propósito: el usuario lo borra, guarda, y
   reaparece. Si la columna es NOT NULL, lo correcto es validar y devolver error —
   con el mismo mensaje que exige el alta, para que ambas puertas digan lo mismo.
3. **En las rutas de API (JSON) el criterio es el mismo**, pero el matiz cambia:
   clave **ausente** conserva; clave presente con `null` (o `[]`) sí vacía. Usar
   `leer_json(data, clave, valor_actual)` — importa especialmente cuando el cuerpo
   se reenvía a un servicio cuyo contrato es "esto es el estado completo deseado"
   (`mutaciones_arbol.editar_*`, que diffea y libera lo que sobre).

Lo comprueba `tests/test_832_contrato_edicion_parcial.py` sobre las rutas de
formulario, con un manifiesto explícito de la deuda pendiente (#834). El detector
que usa (`scripts/auditar_escrituras_parciales.py`) **no ve el caso de API JSON**:
ahí el criterio se sostiene con la revisión y esta regla.

---

## Tests

### Smoke tests pytest (ADR-019 Fase 1)

**Convención: cada PR que introduce una nueva vista debe añadir su smoke test en el mismo PR.**

- Ubicación: `tests/smoke/test_smoke_<vista>.py`
- Un fichero por vista (o dominio relacionado).
- Contenido mínimo: `GET <ruta>` → `assert status_code == 200` + `assert b'class="app-main"' in r.data`.
- Login via fixture de rol: `usuario_admin`, `usuario_supervisor`, `usuario_tramitador`, `usuario_administrativo` (definidos en `tests/conftest.py`).
- Si la vista necesita datos (expediente, entidad…): usar `expediente_seed` o consultar `Model.query.first()` + `pytest.skip` si no hay datos.
- Vistas sin login: usar `client` directamente.
- Los smoke tests se ejecutan con el resto de la suite pytest (`pytest tests/`). No hay configuración separada.

---

## Commits

Formato: `[CATEGORÍA] #N descripción en imperativo`

| Categoría | Cuándo |
|-----------|--------|
| `[BD]` | SQL directo, cambios en schema |
| `[MODELO]` | Modelos SQLAlchemy |
| `[RUTA]` | Rutas Flask |
| `[TEMPLATE]` | Templates HTML |
| `[STYLE]` | CSS / JS |
| `[MIGA]` | Ficheros en migrations/versions/ |
| `[SERVICIO]` | app/services/ |
| `[FEATURE]` | Feature completa multi-capa |
| `[FIX]` | Corrección de bug |
| `[TEST]` | Tests |
| `[DOCS]` | Documentación |
| `[MERGE]` | Merge commits |
| `[RELEASE]` | Releases y tags |

---

## Migraciones de BD

**Nunca `flask db migrate`** — bug conocido con `include_schemas` que regenera todas las FK existentes.

```bash
flask db revision -m "descripcion"   # crear vacía
# editar manualmente: solo añadir los cambios necesarios, nunca tocar FK existentes
flask db upgrade
```

`env.py` sin `include_schemas` (estado por defecto del repo). Todas las tablas usan `schema='public'` explícito.

Toda migración que cree una tabla nueva debe incluir el GRANT al usuario MCP de desarrollo:

```python
op.execute("GRANT SELECT ON public.<tabla> TO claude_desktop")
```

En producción este usuario no existe y el GRANT se omite o revoca, pero en desarrollo es necesario para que el MCP PostgreSQL pueda leerla.

### Dos reglas que solo se notan instalando desde cero (#849)

La BD de desarrollo lleva años acumulando ajustes hechos a mano que nunca se
formalizaron, así que una migración puede estar rota y funcionar aquí. Estas
dos rompían el `upgrade` sobre una base vacía:

**Identificador de revisión: 32 caracteres como máximo.** Alembic crea
`alembic_version.version_num` como `VARCHAR(32)` y no ofrece forma de
configurar ese ancho. Siete revisiones del repo lo superan (la mayor, 45), y
el upgrade limpio moría al registrar la primera de ellas. Las existentes se
quedan como están —renombrarlas dejaría huérfana cualquier copia de la BD
registrada en una de ellas—; `scripts/preparar_bd_test.py` crea la tabla con
128 antes de que la cree Alembic, igual que la de desarrollo. De las nuevas,
ninguna debe pasar de 32.

**Sembrar con `id` explícito obliga a ajustar la secuencia.** Un
`INSERT ... (id, ...)` no la mueve, así que el siguiente INSERT sin id recibe
el valor 1 y choca con la fila ya sembrada:

```python
op.execute(
    "SELECT setval(pg_get_serial_sequence('public.<tabla>', 'id'), "
    "(SELECT COALESCE(MAX(id), 1) FROM public.<tabla>))"
)
```

---

## Reloj de desarrollo (fecha "hoy" simulada) — #820

Para probar guardas de plazo sin editar a mano las fechas de los documentos de un
expediente: `_hoy()` en `app/services/plazos.py` puede leer una fecha simulada en
vez de `date.today()`. Solo tiene efecto con `DEBUG=True` (en producción,
`ProductionConfig.DEBUG = False`, se ignora siempre).

```bash
flask reloj set 2026-09-15   # fija la fecha simulada
flask reloj show             # consulta la fecha activa
flask reloj clear            # vuelve a la fecha real
```

También hay un badge (icono de reloj) en la topbar, visible solo con `DEBUG=True`,
con el mismo efecto que el CLI. Cambia sin reiniciar Flask: el valor vive en
`instance/reloj_simulado.txt` (fuera de git), que `_hoy()` relee en cada llamada —
no es una variable de entorno, que no se propagaría a un `python run.py` ya en
marcha.

---

## Naming

- snake_case en todo: tablas, columnas, variables, funciones, rutas, ficheros
- CamelCase solo para clases de modelo Python (`Expediente`, `Solicitud`, `DocumentoPuro`)

---

## Releases

Al cerrar milestone: PR develop → main, tag anotado `vX.Y.Z`, GitHub Release con changelog.
No hay CHANGELOG.md — los PRs cerrados en GitHub son la fuente de verdad.

---

## Decisiones arquitectónicas

Registrar en `docs/decisiones/` como ADR numerado. Ver ADR-001 y ADR-002 como referencia de formato.

---

## Control de acceso

El sistema de permisos está centralizado en `app/utils/permisos.py` (ADR-012).
**Nunca** usar `current_user.tiene_rol('ADMIN', ...)` directamente en rutas ni templates nuevos.

Antes de dar de alta una pantalla administrativa nueva, decidir **dónde vive** con el
criterio de ADR-029 (entrada propia de sidebar vs. tarjeta dentro del hub del supervisor) —
no copiar el emplazamiento de navegación del módulo hermano más parecido sin releerlo primero.

### Qué usar en cada caso

| Situación | Qué usar |
|---|---|
| Ruta que opera sobre un expediente concreto | `verificar_acceso_expediente(expediente, 'ver'\|'editar')` al inicio del handler |
| Endpoint de sección admin (usuarios, plantillas…) | `@require_permiso('nombre_permiso')` como decorador |
| Filtro de lista según rol (proyectos, seguimiento…) | `if not tiene_permiso('ver_todos_proyectos'):` |
| Mostrar/ocultar control en template | `{% if tiene_permiso('nombre_permiso') %}` |
| Permiso nuevo necesario | Añadir entrada en `PERMISOS` de `app/utils/permisos.py` |

### Efectos automáticos de `verificar_acceso_expediente`

Llamar a esta función en una ruta activa **gratuitamente**:

- El indicador de bombilla en el header (verde/rojo) para TRAMITADOR.
- El registro en bitácora si TRAMITADOR edita un expediente no asignado.
- La protección de acceso según `PERMISOS['editar_expediente']` o `PERMISOS['acceder_expediente']`.

Si la ruta no llama a `verificar_acceso_expediente`, el indicador no aparece aunque haya un expediente en contexto.

### Añadir un permiso nuevo

1. Añadir la clave y el conjunto de roles en `PERMISOS` (`app/utils/permisos.py`).
2. Usar `tiene_permiso('nueva_clave')` o `@require_permiso('nueva_clave')` en el punto de uso.
3. No hay migración de BD ni cambio de esquema.

---

## Flask

### Templates

- `app/modules/X/` → blueprint con `template_folder` propio → templates en `app/modules/X/templates/X/`
- `app/routes/` → sin `template_folder` → templates en `app/templates/` global

No mezclar. Flask hace fallback silencioso a la global sin lanzar error — difícil de depurar. (#127)

### Modelos

Orden de imports en `app/models/__init__.py`: primero modelos sin FKs operacionales, luego dependencias simples, luego múltiples. Romper el orden causa circular imports.

FK format: `db.ForeignKey('public.tabla.campo')` — siempre con prefijo de schema.

### Servicios con dependencias de catálogo (#347)

Todo servicio que acceda a una tabla de catálogo (`TipoTramite`, `TipoTarea`, `TipoFase`, `TipoSolicitud`, `CatalogoPlazo`, etc.) debe:

1. Capturar `OperationalError` / `ProgrammingError` (tabla inexistente o BD caída).
2. Tratar resultado `None` de `.first()` / `.get()` como registro ausente.
3. Devolver un valor degradado y loguear con `log.warning`, **sin propagar la excepción**.

```python
from sqlalchemy.exc import OperationalError, ProgrammingError

def mi_servicio(elemento):
    try:
        resultado = MiModelo.query.filter_by(codigo='ESPERADO').first()
        if resultado is None:
            log.warning("Registro de catálogo 'ESPERADO' no encontrado")
            return VALOR_DEGRADADO
        return resultado
    except (OperationalError, ProgrammingError):
        log.warning("Tabla de catálogo no disponible — devolviendo valor degradado")
        return VALOR_DEGRADADO
```

Cuando se use un código nuevo en cualquier servicio, añadirlo en `app/checks/catalogo_requerido.py` (`REGISTROS_REQUERIDOS`).

### Notificaciones

`flash()` con toasts Bootstrap, categorías `success/danger/warning/info`. Nunca modales para notificaciones.

---

## React (islas)

Stack JS del revamping: islas React sobre templates Jinja (ADR-015). Detalle operativo y cómo crear una isla: `docs/guias/GUIA_REACT_ISLAS.md`.

- **CSS único:** los componentes React usan **exclusivamente clases de Bootstrap 5.3 + CDN JdA**. Prohibido Tailwind, Material UI, shadcn/ui o cualquier librería con sistema visual propio. Toda librería externa con CSS propio (xyflow, cmdk, react-arborist…) requiere un **pase de tematizado documentado** que sobrescriba sus variables/clases con la paleta JdA.
- **Auth:** las islas no autentican. Leen permisos del data-attribute inyectado por Jinja (`user_ctx_attrs()`) solo para condicionar la UI. La autorización real la imponen los decoradores del backend (ver Control de acceso).
- **Build:** una isla = una entry en `react-src/vite.config.js`. Compilar con el botón "Build React" de `flask_console.py` o `scripts/build_react.sh`. Montar con `{{ react_bundle('nombre') }}` + `<div data-react-island="nombre">`.
