# ADR-038 — Hub propio del TRAMITADOR: Seguimiento y Huérfanos

**Estado:** Adoptada
**Fecha:** 2026-08-04
**Issue:** #630
**Relacionado con:** ADR-017 §5/Deuda conocida (caso 3) · ADR-027 §2 (huérfano, `integra_expediente`) · ADR-029 §1bis (páginas-destino de rol) · ADR-010 (N:M documento-tarea) · ADR-016 (árbol del expediente) · ADR-023 (listado+inspector universal) · ADR-013 (permisos blandos)

---

## Contexto

Tres ADR adoptadas dejaban el mismo cabo suelto sin fecha ni nombre:

- **ADR-017**, "Deuda conocida — heterogeneidad de URLs de «Mi trabajo»": el caso 3
  (TRAMITADOR → `/expedientes/seguimiento/`) queda como "única deuda real, sin resolver" — vista
  prestada del dominio de expedientes, sin espacio propio. El momento natural para resolverlo:
  "cuando el TRAMITADOR necesite su propio hub".
- **ADR-027 §2** ("Huérfano = documento del pool sin vínculo a tarea"): "El radar que se lo
  presenta [al técnico] es trabajo aparte (ADR-017 §5, 'Mi trabajo' del técnico)" — candidato
  concreto al disparador que ADR-017 dejaba condicionado.
- **ADR-029 §1bis**: nombra explícitamente "el futuro hub del TRAMITADOR" como una de las dos
  categorías con entrada propia de sidebar (junto a Expedientes/Proyectos/Entidades/Usuarios),
  sin construir todavía.

El radar de documentos huérfanos (el administrativo sube documentos al pool sin vínculo a tarea;
el técnico decide enlazarlos o borrarlos) es un segundo contenido propio del TRAMITADOR,
genuinamente distinto de seguimiento — deja de ser hipotético y se convierte en la pieza que
dispara la construcción del hub.

---

## Decisión

### 1. Módulo nuevo, pestañas separadas (no vista fusionada)

`app/modules/seguimiento_y_huerfanos/`, ruta `/seguimiento_y_huerfanos/`. Dos pestañas
independientes vía `nav-tabs` de Bootstrap (patrón `tablas_maestras/listado.html`, **no** isla
React) — coherente con que `seguimiento` ya es Jinja + `ScrollInfinito` (`app/static/js/`), no
tiene sentido envolverlo en React para esto:

- **Seguimiento**: contenido movido tal cual desde `expedientes/seguimiento.html` +
  `_inspector_seguimiento.html`. Mismas columnas, mismo `api_seguimiento` (no cambia de URL —
  API JSON desacoplada de la URL de página).
- **Huérfanos**: listado nuevo, mismo patrón `listado_v2` + `ScrollInfinito` (paginado por
  cursor) — **no** el patrón de `pool_documentos.html` (carga completa + filtro client-side),
  que solo es seguro para el pool acotado de un expediente; huérfanos es cross-expediente,
  potencialmente miles de filas.

`mi_trabajo.routes` — el redirect de TRAMITADOR pasa de `expedientes.seguimiento` a
`seguimiento_y_huerfanos.index`. Sin alias de compatibilidad en `/expedientes/seguimiento/` —
corte limpio, mismo criterio que la extracción de `tareas_y_subidas` en #588.

### 2. Independencia de #572 confirmada

`DocumentoTarea` (vínculo tarea↔documento, ADR-010) ya existe y es plenamente operativo.
`integra_expediente` **no existe todavía** en el modelo (`app/models/tipos_documentos.py` no lo
tiene; #572 sigue `OPEN`, milestone M2, sin empezar). ADR-027 §2 ya lo fijaba por escrito:
huérfano = documento sin fila en `documentos_tarea`, punto — `integra_expediente` solo afina la
consulta del expediente de remisión (ADR-027 §5), no la de huérfanos. Este hub **no depende de
#572** y no espera a que se implemente.

Tampoco es parte del "estudio de alcance global" de organización documental que #572 aparca
pendiente (decisión de Carlos, independiente de esta ADR): cuando la pertenencia documental se
implante, podrá afinar qué se lista como huérfano, pero no es requisito previo.

### 3. Forma del radar — columnas y filtro por defecto

| Columna | Contenido |
|---|---|
| Expediente | AT, filtrable |
| Asignación | Dato crudo `responsable: {id, siglas}` (o `null` → "Sin asignar", mismo cubo que `_SIN_ASIGNAR` de `estadisticas_supervisor.py`) — el render lo decide el cliente por rol, ver más abajo |
| Tipo documento | `TipoDocumento.nombre` |
| Descripción | `Documento.asunto` |
| Fichero | Nombre + acción "Ver" — reutiliza `info_apertura_documento()` (`app/services/detalle_nodo.py`), el mismo helper que ya usa la Despensa del árbol para documentos aún no enlazados (#609). Cero backend nuevo. |
| Acciones | Enlazar (abre panel de candidatas) · Borrar |

**Asignación y filtro, adaptados por rol** (refinado 2026-08-04 tras discusión con Carlos, para
dejar la vía abierta a un futuro agregado por técnico en Control y Gestión → Estadísticas, y a
una vista de detalle de ese agregado — sin tener que tocar el contrato de datos cuando llegue):
`GET /api/documentos/huerfanos` devuelve siempre el dato **crudo** (`responsable.siglas`), nunca
un booleano pre-renderizado — mismo patrón que ya usa `pista_*` en `seguimiento.html` (JSON
crudo, `renderFns` client-side decide el HTML por columna). Solo TRAMITADOR puede ser responsable
de expediente (invariante ya fijado por `_usuarios_tramitadores()`,
`app/modules/expedientes/routes.py`) — ese hecho decide la forma:

| Rol activo | Render de "Asignación" | Filtro |
|---|---|---|
| TRAMITADOR | Bombilla 🔴/🟢 — mismo lenguaje visual que el indicador del header (`bi-lightbulb-fill`, `text-danger`/`text-success`), misma condición que `es_expediente_ajeno()` (`app/utils/permisos.py`), calculada **por fila** sobre `responsable.id` — no reutiliza el mecanismo de página única (`g.expediente_actual`/context processor), incompatible en forma con una tabla de N expedientes | `ver=mis` (por defecto) / `todos`, mismo patrón que `seguimiento` |
| SUPERVISOR / ADMIN / ADMINISTRATIVO | Texto plano con las siglas (o "Sin asignar") | `todos` fijo + selector `responsable_id=<id>`, poblado reutilizando `_usuarios_tramitadores()` |

Con `ver=mis` todas las filas son del propio técnico (la bombilla sale siempre verde); el modo
`todos` con filtro por usuario es lo que permite al supervisor ver cuántos huérfanos quedan en
todo el sistema y de quién.

### 4. Inferencia de tareas candidatas — usa el catálogo hoy muerto

`tramites_tareas_documentos` (`TramiteTareaDocumento`) ya mapea, por
`(tipo_tramite, orden_tarea, rol ENTRADA/SALIDA)`, qué `tipo_documento` es admisible (`NULL` =
polimórfico). Hoy solo se **edita** desde `tablas_maestras` — ningún endpoint runtime lo
consulta ni la Despensa filtra por él. Este hub le da su primer uso real.

**Grieta estructural aceptada para v1**: `Tarea` (instancia) no persiste `orden` — solo
`tramite_id` + `tipo_tarea_id`. El catálogo `TramiteTarea` sí ordena por
`(tipo_tramite_id, orden)`, y su propio docstring da el caso que rompe cualquier atajo simple:
`ANUNCIO_BOE` tiene **dos** `ESPERAR_PLAZO` en el mismo trámite (publicación y alegaciones), con
tipos de documento admisibles distintos en cada slot. Resolver la posición exacta de una `Tarea`
instanciada contra el catálogo requeriría una función de resolución nueva, sin precedente en el
código — **se descarta para v1** (ver Alternativas). Candidatas = tareas del expediente cuyo
`(tipo_tramite, tipo_tarea)` tenga algún slot que admita el tipo del huérfano (exacto o
polimórfico), sin diferenciar el slot exacto si hay varios del mismo tipo — cubre la mayoría de
trámites reales (no repiten tipo de tarea); el caso doble-slot queda con candidatas algo menos
precisas, nunca incorrectas.

**Reglas de exclusión por seguridad** (motivo: sustituir un `PRODUCIDO` dispara consecuencias
encadenadas — hooks de notificación, ADR-033 §5 para ANALIZAR/diagnóstico — mientras que añadir
un `CONSUMIDO` es aditivo y sin efecto colateral conocido):

- Candidata como **CONSUMIDO**: el catálogo admite el tipo en un slot ENTRADA, y la tarea
  **no está `ejecutada`** (no tiene ya producido). No se sugiere reabrir trabajo cerrado desde
  una sugerencia automática.
- Candidata como **PRODUCIDO**: el catálogo admite el tipo en un slot SALIDA, y
  `documento_producido is None` (slot vacío). Nunca se sugiere una tarea cuyo producido ya está
  ocupado.

Una misma tarea puede aparecer etiquetada como Consumido, Producido, o ambas.

### 5. Vinculación — dos vías, ninguna duplica la mutación existente

El árbol no tiene ninguna superficie que muestre "documentos del pool en paralelo a las tareas"
— el pool solo aparece dentro del editor de una tarea concreta (Despensa, ADR-016 §S3b-3). El
radar necesita conducir al técnico desde el documento hasta la tarea, no al revés.

**Vía A — "Ir a la tarea" (segura, por defecto).** El árbol ya navega con `?nodo=tarea-<id>`
(patrón "Ir a tramitar" de `seguimiento`/`tareas_y_subidas`). Se añade un parámetro hermano
`?doc_pendiente=<id>`: al montar la isla en modo edición sobre esa tarea, llama automáticamente
a `seleccionarDocVincular(doc)` (acción ya existente en `useArbolStore`,
`react-src/src/expediente-arbol/store.js`) — el huérfano llega pre-cargado en la zona de
staging de la Despensa, pero **no guarda nada**: el clic en "+ Consumido"/"+ Producido" y el
guardado siguen siendo del técnico, viendo el contexto completo de la tarea. Toda la maquinaria
de seguridad existente (candados vía `check_invariante`, hooks, guardado consciente) se
reutiliza sin tocarla. Cero endpoint nuevo de vinculación para esta vía.

**Vía B — "Vincular aquí" (rápida, para candidatas de alta confianza).** Nuevo endpoint fino
`POST /api/expedientes/<id>/nodo/tarea/<tarea_id>/vincular_huerfano`, body `{documento_id, rol}`.
Internamente: lee `documentos_consumidos` / `documento_producido` / `notas` actuales de la tarea
(necesario porque `svc.editar_tarea` sustituye la lista completa, no es incremental), añade el
huérfano al rol pedido, llama a `svc.editar_tarea(...)` — el mismo mutador que usa el guardado
del árbol, sin lógica nueva. Repite server-side las reglas de exclusión de §4 (422 si
`rol=PRODUCIDO` y ya hay un producido distinto; 422 si `rol=CONSUMIDO` y la tarea está
`ejecutada`) — defensa en profundidad ante una lista de candidatas desactualizada en cliente.

Cada candidata en el panel muestra ambos botones: "Ir a la tarea" (primario) y "Vincular aquí"
(secundario).

**Descartado**: vinculación directa como única vía, sin paso por el árbol. El usuario no vería
qué ocurre — riesgo que señaló Carlos explícitamente. Se ofrece como atajo opt-in, no como
único camino.

### 6. Borrado de huérfano

Nuevo endpoint `DELETE /api/documentos/<id>`, solo si el documento **sigue** siendo huérfano en
el momento de borrar (defensa en profundidad, aunque la UI solo lo ofrezca ahí). Permiso
`gestionar_estructura_expediente` (TRAMITADOR/SUPERVISOR/ADMIN, no ADMINISTRATIVO) — "decisión
del técnico" (ADR-027 §2), no tarea administrativa de hoja.

### 7. Bitácora

Sin tratamiento especial en v1 — reutiliza el patrón ya existente de bitácora en acciones sobre
el pool. Cuando se acometa el revamping de bitácora se ajustará su API donde corresponda
(decisión explícita de Carlos, fuera de alcance de este ADR).

### 8. Ruta, permiso y sidebar

```python
# app/utils/permisos.py
'acceder_seguimiento_y_huerfanos': {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
```

Universal en lectura (ADR-013), mismo patrón que `acceder_tareas_y_subidas` /
`acceder_gestion_control`. `metadata.json` propio → entrada de sidebar (test de ADR-029 §1bis:
página-destino de rol, categoría ya prevista).

---

## Por qué

- **Resuelve el cabo suelto que citan tres ADR adoptadas** (ADR-017 caso 3, ADR-027 §2,
  ADR-029 §1bis) con una sola pieza de trabajo, en el momento que ADR-017 fijaba como disparador
  natural.
- **No añade backend nuevo donde ya existe uno que sirve**: `info_apertura_documento` (Ver),
  `svc.editar_tarea` (vincular), `es_expediente_ajeno` (bombilla), `ScrollInfinito` (listado),
  `tramites_tareas_documentos` (candidatas) — todo reutilizado, no reinventado.
- **La seguridad de la mutación vive en un solo sitio**: `svc.editar_tarea` + `check_invariante`,
  tanto si se llega por el árbol como por la vía rápida — no hay una segunda implementación de
  "qué es seguro vincular" que mantener sincronizada.
- **El filtro `ver=mis/todos` y la bombilla dan al supervisor visibilidad real** (cuántos
  huérfanos quedan en todo el sistema) sin sacrificar que la vista por defecto sea la cola de
  trabajo del técnico concreto, igual que ya resuelve `seguimiento`.

---

## Cómo implementar

Repartido en el propio #630:

1. **Backend — módulo nuevo**: `app/modules/seguimiento_y_huerfanos/` (blueprint, `metadata.json`,
   permiso `acceder_seguimiento_y_huerfanos`). Mover rutas/templates de `expedientes.seguimiento`
   y `expedientes.seguimiento_fragmento`. Actualizar `mi_trabajo.routes`.
2. **Backend — Huérfanos**: `GET /api/documentos/huerfanos` (cursor, filtro `ver`/expediente),
   `DELETE /api/documentos/<id>`, `POST /api/expedientes/<id>/nodo/tarea/<tarea_id>/vincular_huerfano`.
   Servicio de candidatas sobre `tramites_tareas_documentos` (reglas §4).
3. **Frontend — pestañas** `nav-tabs` (patrón `tablas_maestras`), tabla `ScrollInfinito` para
   Huérfanos, fragmento-inspector de candidatas (patrón ADR-023 / `AppInspector`).
4. **Frontend — árbol**: leer `?doc_pendiente=<id>` en `useArbolStore`, llamar
   `seleccionarDocVincular` al montar en modo edición.
5. **Tests**: smoke test movido/renombrado para Seguimiento; smoke test nuevo para Huérfanos
   (listado, candidatas, vincular directo, borrar, bombilla).
6. **Notas de implementación** en ADR-017 (Deuda conocida, caso 3 → resuelto), ADR-027 §2 y
   ADR-029 §1bis, apuntando a esta ADR y a #630 — mismo patrón que dejó #588.

Tabla de consumidores del movimiento de `seguimiento` (impacto verificado antes de escribir
código, `REGLAS_DESARROLLO.md` §Análisis de impacto): rutas y templates de
`app/modules/expedientes/`, `mi_trabajo.routes`, `tests/smoke/test_smoke_expedientes_seguimiento.py`,
`tests/smoke/test_smoke_mi_trabajo.py`, `docs/diseño/INVENTARIO_BACKEND.md`. Sin cambios en
`api_seguimiento.py` (API desacoplada de la URL de página) ni en documentación histórica
congelada (`ANALISIS_LISTADO_INTELIGENTE.md`, `PRE-ADR-navegacion-administrativa.md`).

---

## Alternativas descartadas

### A. Vista fusionada (Seguimiento + Huérfanos en una sola tabla)

Descartada — decisión directa de Carlos. Son cola de trabajo (seguimiento) y radar de
saneamiento del pool (huérfanos): audiencias y ritmos de uso distintos, aunque compartan hub y
técnico. Mismo criterio que ya separó Cola/Subir documento en `tareas_y_subidas`.

### B. Inferencia con desambiguación posicional exacta (opción C original)

Resolver qué `orden_tarea` del catálogo corresponde a cada `Tarea` instanciada (por orden de
creación dentro del trámite), para acertar también el caso doble-`ESPERAR_PLAZO`. Descartada
para v1: sin precedente en el código, coste desproporcionado frente al beneficio (el caso que
resuelve es raro, y sin ella las candidatas siguen siendo correctas, solo algo menos precisas).
Queda como refinamiento futuro si el uso real lo pide.

### C. Patrón `pool_documentos.html` (carga completa + filtro client-side) para Huérfanos

Descartada por tamaño del problema, no por preferencia: `pool_documentos` es seguro porque el
pool de un expediente es acotado; huérfanos es cross-expediente y potencialmente masivo. No es
una alternativa arquitectónica válida para esta vista.

### D. Vinculación directa como único camino (sin paso por el árbol)

Descartada como único camino — el usuario no ve qué ocurre antes de guardar. Sobrevive como
atajo opt-in (Vía B, §5) para candidatas de alta confianza, nunca como reemplazo de la vía seguro
del árbol.

---

## Aparcado — no se aborda en esta ADR

**"Volver dinámico" según origen de invocación.** Al saltar del radar al árbol (Vía A) se pierde
la vista de listado — mismo problema que ya tienen `seguimiento` y la cola de `tareas_y_subidas`
al saltar al árbol hoy. Un mecanismo genérico de "volver" contextual por origen de navegación,
reutilizable en varias vistas, se identifica como necesidad real (anotado por Carlos en la
discusión de #630) pero es un issue aparte, sin filear todavía — no se construye aquí.

---

## Referencias

- ADR-010 — `docs/decisiones/ADR-010-modelo-nm-documento-tarea.md`
- ADR-013 — `docs/decisiones/ADR-013-permisos-blandos-generalizados.md`
- ADR-016 — árbol del expediente
- ADR-017 — `docs/decisiones/ADR-017-vista-mi-trabajo-administrativo.md` (Deuda conocida, caso 3)
- ADR-023 — `docs/decisiones/ADR-023-list-detail-inspector-universal.md`
- ADR-027 — `docs/decisiones/ADR-027-pertenencia-documental-expediente.md` (§2, §5)
- ADR-029 — `docs/decisiones/ADR-029-navegacion-administrativa.md` (§1bis)
- ADR-033 — `docs/decisiones/ADR-033-ciclo-vida-diagnostico-analizar.md` (§5, candado)
- #630 — issue de diseño
