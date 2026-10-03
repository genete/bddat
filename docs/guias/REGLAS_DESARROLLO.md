# Reglas de desarrollo — BDDAT

## Qué leer según la tarea

| Tarea | Secciones relevantes |
|---|---|
| Solo HTML / CSS / JS | Flask › Templates · Notificaciones · Commits |
| Modelos o migraciones | Flask › Modelos · Migraciones · Naming · Commits |
| Commit o rama | Ramas · Commit directo vs rama · Commits |
| Abrir un issue, redactar un PR, actualizar `CONTEXTO_ACTUAL.md` | Issues y pull requests |
| Cierre de milestone | Releases |
| Decisión de diseño | Decisiones arquitectónicas |
| Nueva ruta o template con expediente / rol | Control de acceso |
| Ruta que edita un registro existente (POST/PATCH) | Rutas que editan un registro existente |
| Isla React (nueva o cambio) | React (islas) · `docs/guias/GUIA_REACT_ISLAS.md` |
| Probar una guarda de plazo sin editar fechas a mano | Reloj de desarrollo |
| Código que lee, escribe o sirve el fichero de un documento o de una plantilla | Documentos: la ficha, no el fichero |

---

## Ramas

- `develop` — rama por defecto; todo cambio pasa por aquí
- `main` — solo recibe merges desde develop al cerrar milestone; lleva tags `vMAJOR.MINOR.PATCH`
- Ramas temporales nacen de develop y vuelven via PR; borrar remota inmediatamente tras merge
- No squash merge — preservar historial completo de commits
- **Crear la rama antes de la primera edición**, no después de commitear en `develop`. Vale también al reanudar un issue tras mergear su fase anterior: la rama activa vuelve a ser `develop` y el paso hay que repetirlo.
- **Verificar la rama con `git status` antes de commitear o pushear.** El estado del inicio de la sesión caduca: el usuario puede trabajar en paralelo en el mismo directorio. Si la rama no es la esperada, crear una de seguridad desde `develop` en vez de tocar la del usuario, y devolver el repo a su rama al terminar.
- **Sin worktrees.** Se probaron en #776 (2026-08-22) y se descartaron: cada uno exige reconstruir el bundle de React y `node_modules`. No proponerlos salvo que el usuario lo pida.

**Naming:** `feature/issue-XX-descripcion` · `bugfix/issue-XX-descripcion` · `refactor/descripcion` · `docs/descripcion`

---

## Commit directo vs rama temporal

**Commit directo en develop** — docs, typos, 1-2 ficheros sin lógica de negocio, sin necesidad de `flask run`.
Si el commit resuelve un issue, cerrarlo a mano (sin PR no hay auto-close):
`gh issue close <N> --comment "Resuelto en commit <SHA> (develop)."`

**Documentos de diseño vivos** (ADRs, `docs/diseño/`, `DETALLE_NECESIDADES_BDDAT.md`, `MATRIZ_COBERTURA_BDDAT.md`, `CONTEXTO_ACTUAL.md`): contenido editorial, no una tarea. Commit directo a `develop`, sin issue ni rama; el mensaje lleva el formato habitual sin número si no hay issue. Si hay duda de si algo "es tarea", preguntar.

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

En el mapa, separar siempre tres cosas: las **fuentes de verdad** afectadas (requieren decisión de diseño), los **consumidores reales** (código, checks, migraciones: hay que actualizarlos) y los **documentos derivados** (se sincronizan con `/sync-derivados` cuando cambia su fuente; no son consumidores independientes que editar). Qué es fuente y qué derivado: `docs/historial/REGLAS_ARQUITECTURA.md` §2.1.

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

## Documentos: la ficha, no el fichero

Mientras se implementa ADR-050, **no entran consumidores nuevos del modelo de
rutas**: nada nuevo lee ni escribe un fichero por su ruta en disco. Lo que necesite
el contenido de un documento lo pide por el documento, con `documento.resolver_url()`,
que sobrevive y pasará a leer del almacén. Cada consumidor nuevo es deuda que la
fase 1 tendría que deshacer (ADR-050 §I).

Símbolos congelados: `ruta_absoluta()`, `FILESYSTEM_BASE`, `PLANTILLAS_BASE`,
`hash_md5`, `ruta_plantilla`, `ruta_pdf` y los de `rutas_esftt.py` que mueven o
nombran ficheros (`mover_a_esftt`, `mover_a_pool`, `nombre_pool_unico`,
`ruta_pool_documento`, `ruta_destino_esftt_fichero`).

Lo vigila `tests/test_1001_consumidores_modelo_rutas.py`, con el número de
apariciones permitido en cada fichero de `app/`. **Si falla, el arreglo es pedir el
contenido por el documento, no subir el número ni añadir el fichero.** Cada fase de
ADR-050 lo baja; cuando no quede ninguno, el test se borra.

### Estilos ODT

Una variante de un estilo de párrafo existente (p. ej. el mismo título en mayúsculas) se crea como estilo **hijo** (`style:parent-style-name` apuntando al original) que declara solo la propiedad añadida. Nunca se muta el estilo compartido: así queda reutilizable, el hijo hereda los cambios del padre y la variante se quita sin riesgo. Antes de tocar una plantilla compartida entre carta y resolución, confirmar en qué fichero vive el texto que describe el ADR: «cabecera» o «encabezamiento» puede ser el membrete (familia `Cabecera - *`) o el título del cuerpo.

---

## Tests

Cómo ejecutar la suite, qué protege cada tipo de test, cuándo escribir uno (y
cuándo no) y reglas al escribirlos:
[`tests/README.md`](../../tests/README.md).

### Smoke tests pytest (ADR-019 Fase 1)

**Convención: cada PR que introduce una nueva vista debe añadir su smoke test en el mismo PR.**

- Ubicación: `tests/smoke/test_smoke_<vista>.py`
- Un fichero por vista (o dominio relacionado).
- Contenido mínimo: `GET <ruta>` → `assert status_code == 200` + `assert b'class="app-main"' in r.data`.
- Login via fixture de rol: `usuario_admin`, `usuario_supervisor`, `usuario_tramitador`, `usuario_administrativo` (definidos en `tests/conftest.py`).
- Si la vista necesita datos (expediente, entidad…): fabricarlos con
  `crear_expediente_de_prueba()` o el builder `ArbolESFTT` de `tests/conftest.py`,
  o apoyarse en las fixtures de semilla (`expediente_seed`, `entidad_seed`).
  **Nunca `pytest.skip` por falta de datos** (#849): la base de tests la
  sembramos nosotros, así que un dato ausente es un defecto de la semilla y el
  test debe decirlo fallando — `assert x is not None, 'la semilla debe traer…'`.
  El tope de skips de la suite es **0**, y solo baja.
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

### Commits atómicos

- En refactors grandes, y también cuando una petición agrupa varias piezas, trocear en commits atómicos y verificar cada uno (visualmente o con tests) antes del siguiente. No acumular todo en un commit monolítico.
- Si dos piezas añaden bloques contiguos al mismo fichero y `git add -p` no puede partir el hunk: quitar temporalmente el segundo bloque, commitear la primera pieza, volver a añadirlo y commitear la segunda.
- En implementaciones largas con varios commits planificados, enseñar el contenido completo de cada pieza (catálogo, migración, código) y esperar confirmación **antes** de `git commit`. Enmendar después es costoso si ya hay commits encima.
- Si el issue elimina ficheros (modelos, servicios…), el `git rm` va en el mismo commit que los cambios de código; no dejar código muerto.
- Si un fichero tiene cambios del usuario ajenos al commit, no descartarlos con `git checkout -- <fichero>` (irrecuperable): preguntar qué hacer.

---

## Issues y pull requests

- **Antes de abrir un issue**, buscar los existentes sobre esa pieza, abiertos **y cerrados**, por el nombre del artefacto del dominio (tipo documental, tabla, servicio, código de catálogo) y no por palabras del título. Comprobar dos cosas: que no se repite y que ninguno propone un diseño **opuesto** al que se va a escribir. Al abrirlo, listar los issues afectados y qué pasa con cada uno (se cierra, se reduce, se reescribe la premisa).
- **Tareas pendientes y checklists, en el cuerpo del issue**, no en comentarios: se revisan por el cuerpo y solo los checkboxes del cuerpo cuentan para la barra de progreso (`gh issue edit --body-file`).
- **Milestone:** un issue relacionado con otro que ya tiene milestone va al mismo que su dependencia.
- **Una conversación, un issue.** Al cerrar uno, el siguiente va en sesión nueva; actualizar el texto de un issue derivado es editar GitHub, implementarlo es sesión nueva. Encadenar issues muy relacionados en una sola sesión, o pedir issue e implementación juntos, solo lo decide el usuario; no se propone por iniciativa propia.
- **`Refs #N` en issues de varias fases**, nunca `Closes #N`, hasta el PR de cierre. El skill `/pr` añade `Closes #XX` por defecto: sustituirlo.
- **`docs/CONTEXTO_ACTUAL.md`:**
  - «Hecho» se actualiza solo tras mergear el PR (`gh pr view <N> --json state,mergedAt`), y **sustituye** al anterior: lo último, sin encolar histórico.
  - Registra solo lo que no está en ADRs, documentos de diseño ni issues, con un puntero a dónde está el detalle.
  - «Próximo»: issues por su título, sin el porqué extendido. Sí merecen quedarse los huecos de diseño sin issue, las ausencias deliberadas («sin issue a propósito») y el motivo de cada aplazamiento en pocas palabras.
  - «Próximo» exige propuesta y confirmación (ver `CLAUDE.md`).

---

## Migraciones de BD

**Nunca `flask db migrate`** — bug conocido con `include_schemas` que regenera todas las FK existentes.

```bash
flask db revision -m "descripcion"   # crear vacía
# editar manualmente: solo añadir los cambios necesarios, nunca tocar FK existentes
flask db upgrade
```

`env.py` sin `include_schemas` (estado por defecto del repo). Todas las tablas usan `schema='public'` explícito.

**Un solo head.** Antes de crear una migración, `flask db heads` / `flask db current`. Si hay varios, resolverlos primero con una migración de merge (`down_revision = (head_A, head_B, ...)`, puede ir vacía o combinarse con la primera migración real). Ramas con migraciones en paralelo sin coordinar son la causa habitual de «Multiple head revisions».

**No aplicar en el mismo turno en que se escribe.** Tras escribir una migración, enseñar el fichero completo al usuario y esperar confirmación explícita antes de `flask db upgrade`, también en la BD de desarrollo: ejecutarla escribe en una fuente de verdad (el catálogo) y necesita luz verde aparte.

Toda migración que cree una tabla nueva debe incluir el GRANT al usuario MCP de desarrollo:

```python
op.execute("GRANT SELECT ON public.<tabla> TO claude_desktop")
```

En producción este usuario no existe y el GRANT se omite o revoca, pero en desarrollo es necesario para que el MCP PostgreSQL pueda leerla.

Si la tabla nueva es **operacional** (la escribe la tramitación o la semilla de tests, no el catálogo), añadirla también a `TABLAS_OPERACIONALES` en `scripts/comparar_catalogo.py`. Si no, sus filas, distintas en cada base, salen como divergencia falsa; mientras esté vacía en las dos no se nota (`certificados_fase`, 2026-09-29).

### Cuatro reglas que solo se notan instalando desde cero (#849)

La BD de desarrollo lleva años acumulando ajustes hechos a mano que nunca se
formalizaron, así que una migración puede estar rota y funcionar aquí. Las dos
primeras rompían el `upgrade` sobre una base vacía; las dos últimas son peores,
porque no rompen nada: dejan una instalación que arranca y trabaja con el
catálogo equivocado.

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

**Una migración de datos nunca localiza la fila por `id`.** Los ids no son
estables entre instalaciones: `MODELO_SOLICITUD` es 146 en desarrollo y 56 en
una base limpia. Un `WHERE id = 111` sobre una base construida desde cero
afecta a 0 filas **y no da ningún error**; o peor, acierta de fila y falla de
significado — `c3d4e5f6a7b8` puebla `nombre_en_plantilla` con un `CASE id`
escrito para el catálogo de tres meses antes, y en la base limpia cada fase
recibe el nombre de otra. Se resuelve siempre por clave natural (`codigo`,
`camino`, `nombre`…) y, si la tabla no tiene ninguna —`reglas_motor` no la
tiene—, por la combinación que la identifica de hecho: `(sujeto, descripcion)`.

La misma trampa con otra cara: `ON CONFLICT (…) DO NOTHING` cuando lo que se
quería era actualizar. Dos migraciones que siembran la misma variable con
etiquetas distintas dejan la de la primera y descartan la de la segunda sin
decir nada.

**El curado de datos estructurales va por migración, nunca a mano.** Los datos
operacionales se maltratan; los estructurales se miman. Si algo del catálogo
está mal en desarrollo, se corrige con una migración, no editándolo por la
interfaz de tablas maestras ni con SQL suelto: lo que solo vive en esa base no
existe para ninguna otra instalación, y #856 va a recrearla. Seis de las once
divergencias que arregló `849_catalogo_replicado` eran exactamente esto.

Se comprueba con `scripts/comparar_catalogo.py`, que enfrenta la base de
desarrollo con una construida desde las migraciones, por contenido y por clave
natural. Conviene pasarlo tras cualquier migración que toque catálogo:

```bash
venv/Scripts/python.exe scripts/preparar_bd_test.py --recrear
venv/Scripts/python.exe scripts/comparar_catalogo.py
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
- **El nombre se tiene que leer solo**, sin mirar el tipo ni el contexto. Si se puede leer como otra cosa, no vale: `nombre` en `documentos` parecía el nombre del documento y era el del fichero (`nombre_fichero`).
- **Fechas: `fecha_<qué>`** (`fecha_administrativa`, `fecha_modificacion_fichero`), **nunca `<participio>_en`** (`creado_en`, `generado_en`). `_en` es un calco del `_at` inglés: en español «modificado en 24/10/2025» no se dice (es «el 24/10»), y nada en `creado_en` indica que sea una fecha. Matiz: `fecha_` no dice si lleva hora (`fecha_administrativa` no la lleva, `fecha_modificacion_fichero` sí); eso lo dice el tipo de la columna. Las columnas que ya existen con `_en` (`generado_en`, `destinatario_fijado_en`) se quedan: renombrarlas cuesta una migración y todos sus consumidores sin ganar nada. Decisión de Carlos, 2026-10-03 (#1007).

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

**Sin responsive móvil.** BDDAT es una herramienta de escritorio Windows (decidido 2026-04-15). No añadir breakpoints ni CSS orientado a móvil; el responsive solo cubre la variación entre resoluciones de monitor. Ignorar viewports de menos de ~1024 px.

**Fragmentos del inspector y del modal grande (ADR-023).** El inspector overlay (`inspector-overlay.js`) inyecta el fragmento con `innerHTML`, así que sus `<script>` **no se ejecutan**: el comportamiento va a JS global con delegación de eventos a nivel `document`. El modal grande (`modal-large.js`) sí reconstruye y re-ejecuta los `<script>`: un fragmento con JS inline funciona tal cual. El JS pesado (cascadas, exploradores, paneles con botones) va, por tanto, al modal. Al cerrarse, el modal llama a `onSaved` (por defecto `AppInspector.refresh()`): si se abre desde una edición en curso del inspector, pasar `onSaved: ()=>{}` para no perderla; el atributo declarativo `data-modal-large-url` usa el valor por defecto.

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

**Sin entradas «de conveniencia» en la interfaz de un servicio.** No añadir una función que acepte un nivel que, según el modelo, no tiene esa propiedad (p. ej. «plazo de un trámite» si el plazo cuelga de la solicitud o la tarea): la interfaz enseña el modelo y reintroduce un nivel que un rediseño eliminó. Antes de añadirla, mirar quién la llama y por qué llega con ese objeto: si llega por el nivel equivocado, la bajada al nivel correcto es una utilidad de navegación del árbol ESFTT, no una entrada del servicio de dominio.

### Notificaciones

`flash()` con toasts Bootstrap, categorías `success/danger/warning/info`. Nunca modales para notificaciones.

---

## React (islas)

Stack JS del revamping: islas React sobre templates Jinja (ADR-015). Detalle operativo y cómo crear una isla: `docs/guias/GUIA_REACT_ISLAS.md`.

- **CSS único:** los componentes React usan **exclusivamente clases de Bootstrap 5.3 + CDN JdA**. Prohibido Tailwind, Material UI, shadcn/ui o cualquier librería con sistema visual propio. Toda librería externa con CSS propio (xyflow, cmdk, react-arborist…) requiere un **pase de tematizado documentado** que sobrescriba sus variables/clases con la paleta JdA.
- **Auth:** las islas no autentican. Leen permisos del data-attribute inyectado por Jinja (`user_ctx_attrs()`) solo para condicionar la UI. La autorización real la imponen los decoradores del backend (ver Control de acceso).
- **Build:** una isla = una entry en `react-src/vite.config.js`. Compilar con el botón "Build React" de `flask_console.py` o `scripts/build_react.sh`. Montar con `{{ react_bundle('nombre') }}` + `<div data-react-island="nombre">`.
