# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. Los issues cerrados están en `git log` — no se duplican aquí.
> Detalle y porqué de cada decisión: `docs/diseño/DECISIONES_UI.md` y los ADRs.

---

**Último cerrado:** #594 — `items_tecnicos` + `condiciones_item_tecnico` + `coberturas_item_tecnico` (catálogo de apartados de contenido técnico exigidos por RD 223/2008 / RD 337/2014) y su CRUD Supervisor, mismo patrón que `requisitos_documentales` (#583) con editor de condiciones anidado. `coberturas_item_tecnico` usa una máquina de 2 campos/3 estados (`texto` + `cubierto`: NO REVISADO / DESFAVORABLE / FAVORABLE) en vez de indexar contra un documento concreto. Entra como tarjeta del hub "Control y Gestión" (ADR-029 §1), sin `metadata.json` propio. PR #600.

**Último hito:** PR #580 (parte de #579) — panel de estadísticas del supervisor: servicio `estadisticas_supervisor` sobre el núcleo `estado_dominio`, isla React + Recharts tematizada.

**#579 sigue abierto:** bloque GESTIÓN aparcado (2026-07-02) para priorizar M3. Piezas en issues propios: config motor #170/#171/#479, plazos legales, operaciones masivas #295 — **antes de construir cualquiera de estas, resolver #588/#589/#590 (ADR-029, navegación administrativa)**, que fijan dónde encajan (hub universal "Control y Gestión"); construirlas antes repetiría el problema que #583 destapó.

**Próximo: #442** — redefinido en sesión 2026-07-06/07 (al analizar el alcance de #581): pasa de "formulario suelto" a dueño del fragmento contenedor del inspector de la tarea ANALIZAR (ADR-023) — layout + contrato de consolidación de defectos + formulario de resultado. Va primero porque #495/#581/#440 se enchufan a su contrato; #581 deja de ser "el siguiente" en solitario y pasa a ser una de las tres secciones que confluyen ahí, en otro plano de la secuencia (ver hoja de ruta abajo, bloque análisis documental/requerimientos redefinido). Resto del foco M3 sigue igual. Spin-offs vivos de #558/#559 pendientes: #566/#567 (árbol), #568 (`NOTIFICACION_INFRUCTUOSA`), #570/#571 (filtros y tokens del seguimiento). Tras M3: bloque escritos/motor adaptativo (M4).

## Hoja de ruta — Implementación

### Bloque UI — revamping

Diseño cerrado (7 ADRs + `DECISIONES_UI.md`). Implementados y cerrados: #497 (ADR-013 permisos), #498 (ADR-014 layout `base_app`), #499 (ADR-015 scaffolding React), #503 (ADR-019 smoke tests), #500 (ADR-016 árbol), #506 (ADR-020 dock global), #531/#532 (ADR-018 command palette + búsqueda unificada), #533 (ADR-022 sistema visual), #534 (ADR-023 list-detail/inspector), #558 (núcleo `estado_dominio`), #501 (ADR-017 Mi trabajo), #559 (inspector de seguimiento). Detalle de cada uno en git log / PRs asociados.

Activo:

- **#579 — Mi trabajo del supervisor (ADR-028).** Bloque CONTROL hecho (PR #580). Bloque GESTIÓN aparcado. Permanece abierto como paraguas.
- **#588/#589/#590 — Navegación administrativa (ADR-029).** Van **antes** que cualquier issue que pueble el bloque GESTIÓN de #579 (#170/#171/#479/plazos/#295): fijan la estructura (hub universal "Control y Gestión", dashboard 1:1 con el sidebar, retirada del prefijo `/admin`) donde esas piezas tienen que encajar.

**Total estimado bloque UI: ~10-13 semanas** (1 dev + IA, ratio observado).

### Bloque análisis documental / requerimientos (M3) — foco actual

Orden (sesión 2026-07-03, re-troceado 2026-07-05, **redefinido 2026-07-06/07** al
analizar el alcance de #581 — detalle en `docs/referencia/DISEÑO_ANALISIS_SOLICITUD.md`
§4/§7 y en el alcance actualizado de #442 en GitHub): las tres ramas de catálogo
(documental, requerimientos, ítems técnicos) siguen su CRUD→poblado propio, pero la
convergencia en la tarea ANALIZAR ya no es una cola `#495 → #581 → #440 → #442`.
Aplicando ADR-023 (seleccionar→inspector→modal), **#442 pasa a ir primero**: es el
dueño del fragmento contenedor del inspector (layout + contrato de consolidación de
defectos + formulario de resultado). #495 (check documental) y #581 (check ítems
técnicos) son secciones inline que se enchufan a ese contrato; #440 (selector de
requerimientos) es el modal grande lanzado desde el contenedor. Los tres son
**independientes entre sí** una vez existe #442 — no hace falta construirlos a la vez
ni en un orden fijo (sugerido por esfuerzo: #440 → #495 → #581).

**Rama documental (sin cambios):**
- ~~**#583**~~ ✅ CRUD admin de `requisitos_documentales`. PR #584.
- **#408** — Poblar catálogo de requisitos documentales (modelo ya construido en #192).

**Rama requerimientos (#441 re-troceado 2026-07-05):**
- ~~**#593**~~ ✅ [ADMIN] CRUD de `catalogo_requerimientos` (gemelo simplificado de #583,
  sin condiciones anidadas). PR #597.
- **#441** — poblado puro de `catalogo_requerimientos`, ya no bloqueado (CRUD de #593
  existe). Antes pedía script+migración; descartado, mismo criterio que #408.

**Rama ítems técnicos (#581 redefinido 2026-07-06/07 — ya no es "el siguiente" en
solitario, ver "Contenedor + secciones" abajo):**
- ~~**#591**~~ ✅ Corte mínimo de integración con
  [bddat-instalaciones](https://github.com/genete/bddat-instalaciones)
  (`activo_red`/`envolvente`/tabla puente) — deriva el RD aplicable sin campo proxy. PR #598.
- ~~**#594**~~ ✅ [MODELO][ADMIN] `items_tecnicos` + `condiciones_item_tecnico` + CRUD
  Supervisor. PR #600.
- **#595** — poblado normativo puro de `items_tecnicos` (RD 223/2008, RD 337/2014). No
  bloqueado (#594 resuelto), no se prioriza mientras se pueda avanzar sin él — la
  sección de #581 solo depende de #595 para tener datos reales, no para construirse.
- **#581** — check de contenido técnico del proyecto, sección inline en el contenedor
  de #442. Redefinido a solo la UI de verificación del tramitador (antes bundlaba
  diseño+poblado+UI). Necesita un evaluador nuevo (`evaluar_items_tecnicos`, gemelo de
  `evaluar_requisitos`). No bloqueado por #594/#595; sí depende de que exista el
  contrato de consolidación de #442.

**Contenedor + secciones (tarea ANALIZAR, ADR-023):**
- **#442 — primero.** Redefinido: fragmento contenedor del inspector + contrato de
  consolidación de defectos + formulario de resultado (`favorable`/`desfavorable`) +
  persistencia en `diagnosticos`. Detalle del reparto y de la regla de cita normativa
  en su alcance actualizado (GitHub).
- **#495** — check documental, sección inline (evaluador `evaluar_requisitos` ya
  existe, falta integrarlo + fragmento).
- **#581** — check de ítems técnicos, sección inline (ver arriba).
- **#440** — selector de requerimientos, modal grande (CRUD del catálogo ya existe en
  #593, falta el modal + rutas de shuttle).
- ~~**#582**~~ ✅ Regla de motor: tasa impagada bloquea toda fase posterior. PR #596.

### Bloque escritos / motor adaptativo (M4)

Se aborda tras consolidar M3.

- **#555** — Clasificación ESFT de plantillas.
- **#556** — Variables del motor en plantillas (documento adaptativo). Depende de la cobertura de catálogo (M3).
- **#561** — Drop `catalogo_variables.activa` + red de tests (ADR-026).

**ADR-021** (operaciones externas BandeJA/Notifica-PNT): diseño acordado, issue pendiente de crear.

## Decisiones pendientes a tomar en construcción

- Sub-stack React por isla (state management, data fetching, librerías concretas).
- Contenido fino del inspector/dock/viewbar por nivel del árbol — se refina durante implementación.

## Documentos vivos del revamping

- `docs/diseño/DECISIONES_UI.md` — punto de entrada al estado del revamping.
- `docs/guias/NOMENCLATURA_LAYOUT.md` — referencia de las 7 áreas del layout.
- `docs/decisiones/` — ADR-013 en adelante (revamping); `DECISIONES_UI.md` mantiene el listado curado y actualizado, no un rango fijo aquí.

## Backlog M3/M4/M5 no afectado por el revamping

Sigue en GitHub con sus milestones. Ejemplos: #170, #171, #322, #408, #409, #432, #495, etc.

**#592** (M5) — Integración completa del modelo de activos técnicos de
[bddat-instalaciones](https://github.com/genete/bddat-instalaciones) (líneas, aparamenta,
geometría/PostGIS, generación). Corte mínimo ya resuelto en #591 (M3).
