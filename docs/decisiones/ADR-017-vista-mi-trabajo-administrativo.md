# ADR-017 — Vista "Mi trabajo" del administrativo

**Estado:** Adoptada
**Fecha:** 2026-05-28
**Issue:** #501

> **Revisión 2026-06-22 (#501, en implementación):**
> 1. **Permiso "puerta abierta"** — `gestionar_tareas` habilita completar **cualquier tarea ya prevista** (no solo las que la cola ofrece); la frontera es **hoja / estructura**, no el tipo de tarea. Trazabilidad por bitácora. Ver §6.
> 2. **La cola lista todo `ESPERAR_PLAZO`** que espera un producido externo (ADR-004), no solo el de publicación: ese es el grueso del trabajo administrativo ("incorporar lo que llega"). Ver §2.
> 3. **Columna y filtro "Tocado por" diferidos** a spin-off (placeholder en v1). Ver §3.
>
> **Apartado B (resuelto 2026-06-22):** (a) el `CERT_PLAZO_CUMPLIDO` del Caso B de `ESPERAR_PLAZO` **no se restringe por rol** — lo emite quien sea (admin, técnico o trabajo programado); no es un juicio de valor sino una **comprobación objetiva del motor** (solo emite si el plazo ha vencido), así que su validez es independiente de quién lo registre. Ver §2. (b) La pertenencia documental al EXPEDIENTE y el concepto de **documentos huérfanos** quedan fijados en **ADR-027** (#572).

---

## Contexto

El estudio de usuario fase 2 identificó al perfil **ADMINISTRATIVO** como el que más radicalmente cambia su flujo con BDDAT (4-6 personas). Hoy su trabajo vive entre BandeJA, carpetas del servidor y un Calc vitaminado con días hábiles. La presentación POC (S08 bullet 6) promete públicamente "vista propia para administrativo" con 🚧 pendiente de implementar.

El análisis crítico fase 3 marcó este perfil como decisión 5.6 — propuesta inicial de hacer mini-estudio con un administrativo real antes de diseñar. En conversación de fase 4 se descartó el mini-estudio: el supervisor (Carlos) conoce el flujo administrativo en lo que afecta a BDDAT y diseñamos por inferencia, iterando con feedback real en uso.

### Naturaleza del trabajo administrativo

Tras conversación detallada con el supervisor, se establecen estos rasgos:

- **Los administrativos NO tienen expedientes propios** ni tareas pre-asignadas. Son ayudantes colectivos del equipo.
- **El expediente sigue siendo del técnico**; el administrativo actúa sobre **hojas del árbol** (tareas, vínculos documentales) y nunca sobre estructura (solicitudes, fases, trámites).
- **No hay asignación previa** de tareas administrativas a un admin concreto. La organización surge del trabajo: si tengo el documento, actúo; si lo empezó otro, no pasa nada — la siguiente cosa que llegue irá a otro y todo fluye.
- **Pistas (cosas que llegan)**: comunicaciones de BandeJA (documentos firmados para notificar, anuncios para publicar) + entradas externas (alegaciones, informes de organismos).
- **Sustituye al Calc vitaminado** del admin: BDDAT calcula automáticamente plazos hábiles, plazo de exposición, etc.

### Tareas administrativas concretas en BDDAT

1. **Subir documentos al pool del expediente** y clasificarlos (no necesariamente vinculados a tarea).
2. **Notificaciones**: subir doc firmado a tarea NOTIFICAR (rol consumido), notificar fuera de BDDAT, subir justificante (rol producido), registrar resultado.
3. **Publicaciones**: generar oficios de remisión (tarea ELABORAR — el admin sí puede crearla), enviar a firma, notificar al publicador, esperar publicación efectiva (tarea ESPERAR_PLAZO del trámite PUBLICACION), subir anuncio publicado como producido, calcular plazo de exposición.
4. **Separatas**: misma mecánica que notificación. El técnico gobierna a quién van; el admin ejecuta.

---

## Decisión

### 1. Nueva vista `Mi trabajo` con dos modos en v1

Acceso por entrada en sidebar: **📥 Mi trabajo**. Visible para todos los roles (ADR-013 permisos blandos), pero **pantalla por defecto al login del rol ADMINISTRATIVO**.

Dos modos seleccionables por tabs en viewbar:

```
┌─ viewbar ──────────────────────────────────────────────┐
│ 📥 Mi trabajo                                          │
│ [📋 Cola] [📤 Subir documento]                         │
└────────────────────────────────────────────────────────┘
```

Un tercer modo (📅 Calendario de publicaciones) se difiere a v1.5 — la cola con filtro "esperando publicación" cubre el caso operativamente.

### 2. Modo Cola — listado de tareas administrativas pendientes

**Listado común a todos los administrativos**, sin asignación previa. Las tareas pendientes se infieren del estado actual del expediente; no se modela una tabla nueva.

#### Origen de filas en la cola

Toda recepción de documento externo se modela como `ESPERAR_PLAZO` esperando su
`documento_producido` (ADR-004). La cola los lista **todos**, no solo los de publicación —
el grueso del trabajo administrativo es precisamente incorporar lo que llega del exterior.

| Estado de la tarea | Mensaje en cola |
|---|---|
| NOTIFICAR sin doc consumido | "falta doc firmado" |
| NOTIFICAR con consumido sin producido | "esperando justificante" |
| NOTIFICAR con producido sin resultado | "esperando registro de resultado" |
| ELABORAR pendiente para tramitación admin (oficio remisión, etc.) | "pendiente elaborar" |
| ESPERAR_PLAZO esperando producido externo — información pública | "esperando alegaciones" |
| ESPERAR_PLAZO esperando producido externo — consulta a organismo | "esperando informe del organismo" |
| ESPERAR_PLAZO esperando producido externo — requerimiento / subsanación | "esperando subsanación" |
| ESPERAR_PLAZO de trámite PUBLICACION sin doc producido | "esperando publicación efectiva" |

Los tres orígenes `ESPERAR_PLAZO` no-publicación son **nuevos en la revisión 2026-06-22**.
La tabla es ilustrativa: el mensaje genérico de cualquier `ESPERAR_PLAZO` que espere un
producido externo es "esperando recepción", afinable por tipo de trámite. **Añadirlos no
toca columnas** del listado — solo amplía qué tareas selecciona el agregador y el texto de
"Pendiente". El **Caso B** (plazo vencido → `CERT_PLAZO_CUMPLIDO`) **lo puede emitir cualquier
rol**: no es un juicio de valor sino una comprobación del motor (solo emite si el plazo ha
vencido), por lo que su validez es independiente de quién lo registre — admin, técnico o el
trabajo programado nocturno.

#### Contexto por fila

Cada fila lleva contexto completo para que el admin sepa rápido qué hace y por qué:

| Expediente | Titular | Solicitud | Fase | Trámite | Tarea | Pendiente | Tocado por |
|---|---|---|---|---|---|---|---|
| AT-1234 | ENDESA SA | AAP | Resolución | NOTIFICACION_RESOLUCION | NOTIFICAR | esperando justificante | Pepa |
| AT-5678 | ALMENDRA SL | AAP+AAC | Información Pública | PUBLICACION_BOJA | ESPERAR_PLAZO | esperando publicación | — |
| AT-9012 | EDISTRIBUCIÓN | DUP | Información Pública | NOTIFICACION_TITULAR | NOTIFICAR | falta doc firmado | Juan |

#### Filtros

- Por estado pendiente (texto): falta doc firmado / esperando justificante / etc.
- Por plazo: hoy / esta semana / vencido / sin plazo.
- Por "Tocado por": sin tocar / tocado por mí / tocado por otros.
- Por tipo de expediente (Distribución / Transporte / Renovable / Convencional).
- Búsqueda libre en expediente, titular, proyecto.

#### Acción al clicar fila

Click en fila → abre la **vista de árbol del expediente** (ADR-016) con la tarea seleccionada y modo edición activado. El admin actúa sobre la tarea (sube doc, registra resultado, etc.) desde el inspector del árbol, no desde la cola.

### 3. Modo "Tocado por" como tag puramente informativo

> **Diferido en #501 (revisión 2026-06-22).** La columna y el filtro "Tocado por" se dejan
> como **placeholder** (`—` atenuado) en v1, por dos motivos que se suman: (a) el modelo de
> "propiedad emergente" está aún por validar con el equipo administrativo real; (b) requiere
> agregación por tarea sobre bitácora (coste no trivial en una cola transversal). Se cablea
> en un spin-off cuando se decida. Ninguna otra columna depende de esta.

- **No hay asignación**, no hay timeout, no hay botón "soltar".
- La columna "Tocado por" muestra el **último usuario que actuó sobre la tarea**, deducido de la bitácora (`tabla='tareas' AND registro_id=X ORDER BY created_at DESC LIMIT 1`).
- Sirve como **filtro de ayuda** ("¿qué llevo yo?", "¿qué hay sin tocar?"), no como mecanismo de bloqueo. Si Pepa tocó una tarea y se va de vacaciones, cualquier otro admin puede continuar la cadena cuando llegue la siguiente cosa — sin ceremonia, sin botones.
- La cadena ELABORAR → consumido → producido implica varias tareas; cada una tiene su propio "Tocado por". No se persiste propiedad de la cadena entera — solo el último que tocó cada tarea.

### 4. Modo Subir documento

Formulario de subida puntual al pool, con dos sub-modos:

#### A. Subida con clasificación manual (v1)

Pasos del admin:

1. Drag-drop o botón "Examinar" → selecciona fichero local.
2. Buscar expediente destino (autocompletado por número/titular/proyecto — reutiliza la API de búsqueda global, la misma que `Ctrl+K`).
3. Clasificar tipo de documento (select con tipos de `TipoDocumento`, agrupados por categoría).
4. Asunto (opcional).
5. Fecha administrativa (si el tipo la requiere).
6. Guardar → doc queda en el pool del expediente clasificado, sin vínculo a tarea.

**El admin NO vincula el doc a tarea.** Eso lo hace el tramitador (o el propio admin desde modo Cola si es notificación / publicación).

#### B. Subida con auto-clasificación heurística (diferido)

Sub-modo previsto pero **diferido** hasta que existan los scripts del descubridor heurístico:

- **#304** — Script de detección del tipo de solicitud por análisis del PDF.
- **#305** — Script de detección del tipo de expediente por análisis del proyecto.

Cuando estén disponibles, este sub-modo permitirá:

1. Subir uno o varios documentos sin más datos.
2. El descubridor analiza cada fichero y sugiere: expediente, tipo de documento, si está firmado, fecha administrativa, etc.
3. El admin confirma o ajusta cada sugerencia.
4. Guardar.

El ADR-017 **deja el espacio reservado en la vista** para este sub-modo, pero no lo implementa en v1.

#### Histórico de subidas del admin

La vista "Subir documento" muestra debajo del formulario las últimas N subidas hechas por el admin actual (referencia rápida si se equivocó de expediente o quiere repetir un patrón).

### 5. Caso "tarea no existe todavía"

Cuando llega un documento al admin pero la tarea destino no existe aún (ej. alegación en IP que llega antes de que el técnico cree el trámite de gestión de esa alegación):

- El admin sube el doc al pool clasificado (Modo Subir documento).
- El doc queda en el pool sin vínculo.
- El tramitador, al revisar, ve la alegación y crea el trámite correspondiente con su tarea.

Esto es flujo correcto, sin bloqueos. La cola **no muestra** docs sueltos en el pool como "tareas pendientes admin" — quien decide qué se hace con ellos es el tramitador.

### 6. Restricciones de permisos del administrativo

Ampliación de ADR-013 con dos permisos nuevos:

```python
PERMISOS = {
    # ... (los anteriores)
    'gestionar_tareas': {ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO},
    'gestionar_estructura_expediente': {ADMIN, SUPERVISOR, TRAMITADOR},
}
```

| Acción | Permiso | Incluye ADMINISTRATIVO |
|---|---|---|
| Crear / editar / borrar tarea ELABORAR, NOTIFICAR, ESPERAR_PLAZO, ANALIZAR | `gestionar_tareas` | ✓ |
| Vincular documento a tarea (consumido / producido) | `gestionar_tareas` | ✓ |
| Crear / editar / borrar solicitud, fase, trámite | `gestionar_estructura_expediente` | ✗ |
| Editar campos generales del expediente | `editar_expediente` (ya existe) | ✗ |
| Cambiar responsable | `cambiar_responsable` (ya existe) | ✗ |

Esto materializa **"admin actúa solo sobre hojas del árbol"**.

**Principio "puerta abierta" (revisión 2026-06-22, #501).** El permiso es de **grano
grueso**: `gestionar_tareas` habilita **completar cualquier tarea ya prevista** —incluida
ANALIZAR— sin discriminar por tipo de tarea ni por trámite. La frontera real es **hoja sí /
estructura no**: el admin nunca **tramita** (crear trámites, fases, solicitudes y sus
ancestros) — eso es `gestionar_estructura_expediente`, propio del rol TRAMITADOR ("tramitar"
es literalmente su función). Se decide **dejar la puerta abierta a propósito**: en caso de
necesidad el admin puede impulsar tareas que normalmente hace el tramitador, y eso beneficia
al sistema. La **bitácora** registra quién hizo qué, de modo que la apertura no compromete la
trazabilidad. El admin no tiene capada la búsqueda de expedientes ni la entrada al árbol; el
camino para cualquier tarea es siempre el mismo: hacia el árbol. La cola (§2) solo **ofrece**
el subconjunto que es trabajo administrativo típico — es una guía, no un límite de acceso.

En la vista de árbol del expediente, las acciones (botón Crear hijo, menú contextual Crear/Borrar sobre nodos no-tarea) se filtran por permiso: el admin las ve atenuadas con tooltip explicativo, o no las ve, según política — refinable en implementación.

### 7. Integración con el árbol del expediente (ADR-016)

La vista del admin **alimenta** al árbol; el árbol es donde se materializa cada acción concreta.

- Click en fila de cola → árbol con tarea seleccionada en modo edición.
- Click en doc del histórico de subidas → árbol con expediente abierto y doc seleccionado en pool.

**No se duplica funcionalidad.** El árbol del expediente ya está construido (ADR-016 #500).

### 8. Calendario de publicaciones (diferido a v1.5)

Vista mes/semana con publicaciones esperadas (ESPERAR_PLAZO de trámites PUBLICACION). Por construirse cuando v1 esté validada en uso. La cola con filtro "esperando publicación" cubre el caso operativo en v1.

---

## Por qué

- **Cumple la promesa pública** del POC S08 bullet 6 ("vista propia con todos los expedientes y solicitudes... pueden acceder directamente a la tarea concreta").
- **Materializa el flujo real** del admin sin inventar asignaciones que no existen en la organización.
- **Sustituye el Calc vitaminado** y la doble anotación manual entre Calc, BandeJA, y carpetas.
- **Reutiliza el árbol del expediente** (ADR-016) sin duplicar UI ni lógica.
- **Coherente con ADR-013** (permisos blandos): el admin ve la misma sidebar que los demás roles, su vista es accesible a todos como referencia, sus restricciones se expresan como ausencia de permisos sobre estructura.
- **El "Tocado por" como tag informativo** preserva la organización emergente del equipo real, sin imponer ceremonia ni introducir conceptos artificiales.

---

## Cómo implementar

1. **Backend — endpoints:**
   - `GET /api/administrativo/cola?filtros=...`: agrega tareas pendientes administrativas. Cada fila lleva el contexto completo (expediente, titular, solicitud, fase, trámite, tarea, pendiente, último tocado por).
   - `POST /api/administrativo/subir_doc`: recibe fichero + expediente_id + tipo_doc_id + asunto + fecha_administrativa. Crea registro en `documentos`.
   - `GET /api/administrativo/mis_subidas?limit=10`: histórico de subidas del usuario actual.
2. **Backend — ampliación PERMISOS** (`app/utils/permisos.py`) con `gestionar_tareas` y `gestionar_estructura_expediente`.
3. **Backend — refactor de decoradores** en endpoints CRUD de tareas (usan `gestionar_tareas`) y de solicitud/fase/trámite (usan `gestionar_estructura_expediente`).
4. **Frontend — isla React** `react-src/src/mi-trabajo/`:
   - Componente `<Cola>` con tabla virtual (puede ser densa).
   - Componente `<SubirDocumento>` con formulario + drag-drop + autocompletado de expediente reutilizando la API de búsqueda global.
   - Componente `<HistoricoSubidas>`.
5. **Template Jinja** `app/templates/mi_trabajo/index.html` extiende `base_app.html`. Sin `aside_right` ni `panel_bottom` definidos (modo página simple en v1 — la viewbar lleva los tabs).
6. **Ruta Flask** `GET /mi_trabajo/` con `@require_permiso('acceder_expediente')` (universal post ADR-013).
7. **Sidebar** — añadir entrada "📥 Mi trabajo" en `metadata.json` con su ruta e icono.
8. **Configuración de "pantalla por defecto"**: la redirección post-login al rol ADMINISTRATIVO apunta a `/mi_trabajo/`, no a `/dashboard/`.
9. **Smoke test pytest**: `/mi_trabajo/` devuelve 200 con el shell `base_app`.
10. **Smoke test Playwright MCP**: flujo de subir un documento, ver que aparece en histórico y en el pool del expediente.

---

## Alternativa descartada

### A. Sistema de asignación explícita de tareas administrativas a un admin concreto

Considerada (y planteada inicialmente como "cola personal" en la discusión). Descartada porque NO refleja la realidad de la organización — los admin son ayudantes colectivos sin propietario de tarea. Forzar un modelo de asignación introduce conceptos artificiales que el equipo no usa.

### B. Mini-estudio con administrativo real antes de mockups

Considerada como decisión 5.6 del análisis crítico. Descartada porque el supervisor conoce el flujo administrativo en lo que afecta a BDDAT y porque la parte externa (Drupal, sedeBOJA, SIR) no entra en el alcance del rediseño. Diseñamos por inferencia y se itera con feedback real en uso.

### C. Vista del administrativo como "versión recortada" de la del tramitador

Descartada en análisis crítico §2.4. El flujo del admin es **estructuralmente distinto** (cola transversal de tareas atravesando muchos expedientes) — no es un subconjunto de la vista del expediente.

### D. Botón "Soltar tarea" + timeout

Considerada como mecánica de liberación de propiedad. Descartada porque introduce ceremonia que el flujo real no necesita: si el admin tiene el dato para actuar, actúa. El "Tocado por" es solo un filtro de ayuda, no un mecanismo de bloqueo.

---

## Deuda conocida — heterogeneidad de URLs del concepto «Mi trabajo»  `[PARCIALMENTE RESUELTO — #588, ADR-029]`

> Anotado 2026-06-23, en contexto de #579 (al completar el hub del supervisor, que
> cierra el tercer patrón distinto del mismo concepto).
> **Actualizado 2026-07-13 (#588, ADR-029):** los dos primeros casos se resuelven —
> ambos eran blueprints reales con contenido propio, así que "renombrar" es solo tocar
> un `url_prefix` (mecánico, `url_for()` no se entera). El tercer caso sigue abierto,
> como estaba: no es simétrico con los otros dos.

El concepto «Mi trabajo» **está unificado donde importa**: una sola entrada de sidebar
role-adaptive (ADR-013) y un único punto de entrada navegable `/mi_trabajo/`, que
despacha por rol activo (`mi_trabajo.index`):

| Rol activo | Destino tras el dispatcher | Naturaleza del destino |
|---|---|---|
| ADMINISTRATIVO | `redirect → /tareas_y_subidas/` | Isla cola/subir (este ADR), ruta propia desde #588 |
| SUPERVISOR / ADMIN | `redirect → /gestion_y_control/` | Hub de dos bloques (#579 ADR-028; renombrado #588 ADR-029) |
| TRAMITADOR | `redirect → /expedientes/seguimiento/` | **Vista prestada** de otro dominio — sigue abierto |

La heterogeneidad de las URLs finales **no es un bug**: es reflejo fiel de que los tres
roles están en fases de madurez distintas. El usuario nunca teclea esas URLs (clica la
entrada única); la indirección del dispatcher permite cambiar los destinos por debajo
sin tocar la navegación. Matices, por gravedad:

1. `/gestion_y_control/` (antes `/supervisor/`) — sano: blueprint con identidad propia,
   es más que «mi trabajo». Renombrado en #588 y con `metadata.json` propio (ADR-029 §2):
   además de alcanzable vía «Mi trabajo», tiene su propia entrada de sidebar «Control y
   Gestión» — redundancia asumida, mismo patrón que ya tiene Usuarios.
2. `/tareas_y_subidas/` (antes `/mi_trabajo/`, contenido administrativo) — **resuelto en
   #588**: la colisión semántica (la raíz hacía de dispatcher genérico **y** de vista
   concreta del administrativo) se elimina extrayendo el contenido a un blueprint propio,
   universal (`acceder_tareas_y_subidas`, 4 roles) con su propia entrada de sidebar. La
   escritura (`gestionar_tareas`) ya era universal desde ADR-017 §6 — solo la navegación
   la escondía tras el rol ADMINISTRATIVO. `mi_trabajo.index` queda como dispatcher puro
   y simétrico para los tres roles.
3. `/expedientes/seguimiento/` (tramitador) — **sigue siendo la única deuda real, sin
   resolver**: no es un blueprint propio que renombrar, es una vista prestada del dominio
   de expedientes; no tiene espacio propio. El **momento natural** para fijarla sigue
   siendo cuando el TRAMITADOR necesite su propio hub (como ya lo tiene Control y
   Gestión) — ahí `/expedientes/seguimiento/` se queda corto y fuerza la decisión de
   forma informada, en vez de inventarla en frío. No se aborda en #588: construir un hub
   nuevo no es un renombrado, es trabajo de alcance distinto.
