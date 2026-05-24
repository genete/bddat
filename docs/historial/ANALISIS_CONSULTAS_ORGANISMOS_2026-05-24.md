# Análisis exhaustivo: Consultas a Organismos — Issue #247

**Fecha:** 2026-05-24
**Estado:** Snapshot estático. La sección §12 (cruce con issues) queda pendiente para sesión posterior.
**Propósito:** Acotar el alcance real del issue #247 y detectar derivados antes de implementar.

---

## Índice

1. [Base de datos y migraciones](#1-base-de-datos-y-migraciones)
2. [Modelo SQLAlchemy](#2-modelo-sqlalchemy)
3. [Seeds y datos maestros](#3-seeds-y-datos-maestros)
4. [Context Builders](#4-context-builders)
5. [Motor de reglas y variables](#5-motor-de-reglas-y-variables)
6. [Invariantes estructurales](#6-invariantes-estructurales)
7. [Motor de plazos](#7-motor-de-plazos)
8. [Rutas y API](#8-rutas-y-api)
9. [Templates y UI](#9-templates-y-ui)
10. [Tests](#10-tests)
11. [ANALISIS_TECNICO — situación real en el sistema](#11-analisis_tecnico--situación-real-en-el-sistema)
12. [Derivados candidatos — cruce con issues](#12-derivados-candidatos--cruce-con-issues)

---

## 1. Base de datos y migraciones

### Tabla `organismos_expediente`

Creada en `migrations/versions/391_organismos_expediente.py`.

| Campo | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER PK autoincrement | — |
| `expediente_id` | INTEGER FK → `expedientes.id` CASCADE | NOT NULL, index |
| `organismo_id` | INTEGER FK → `entidades.id` | NOT NULL, index |
| `via` | VARCHAR(30) | CHECK IN ('consulta','declaracion_responsable') |
| `documento_id` | INTEGER FK → `documentos.id` | nullable |
| `estado` | VARCHAR(40) | CHECK 7 valores; default 'pendiente' |
| `num_iteraciones_organismo` | INTEGER | NOT NULL; default 0 |
| `tramite_id` | INTEGER FK → `tramites.id` | nullable; UNIQUE |
| `plazo_legal_dias` | INTEGER | nullable |

**UNIQUE constraints:** `(expediente_id, organismo_id)` y `tramite_id` por separado.

**Estados válidos:** `pendiente` → `separata_enviada` → `en_tramitacion` → `cerrado_favorable` / `cerrado_con_condicionados` / `audiencia_previa` / `exonerado`. El estado `exonerado` corresponde a `via = declaracion_responsable` y es terminal desde el inicio.

**Notas:**
- `organismo_id` apunta a `entidades` con `rol_consultado = True`. No existe tabla de organismos separada.
- `tramite_id` apunta únicamente al trámite `CONSULTA_SEPARATA` del organismo. La unicidad garantiza correspondencia 1:1. Los trámites de traslado no tienen FK directa al registro de organismo — ver §4 y §12.
- `plazo_legal_dias` se captura al crear la separata (30 días con carácter general; 15 si AAP previa + AAC pura sin DUP).

### Migración GRANT

`migrations/versions/449_grant_organismos_expediente.py` — corrige el GRANT SELECT olvidado en la tabla. Aplicada (#449, PR #452). ✅

### Consulta nombrada

`migrations/versions/395_seed_organismos_consulta.py` — inserta la consulta nombrada `organismos_consulta` en la tabla `consultas_nombradas`. La SQL devuelve nombre, NIF, plazo, estado, fecha envío y fecha respuesta por organismo del expediente. Disponible en plantillas como `{% for org in organismos_consulta %}`. ✅

### Cadena de migraciones CONSULTAS (HEAD → atrás)

```
449_grant_organismos_expediente
  → 405_catalogo_requerimientos
    → ... → 395_seed_organismos_consulta
               → 391_organismos_expediente
                 → 387_eliminar_whitelists_esft
                   → ... → 370_seed_tramites_tareas
```

**Observación — conflicto potencial 345 vs 370:** existen dos migraciones con el mismo propósito:
- `370_seed_tramites_tareas` (down_revision: `370_actualizar_tipos_tramites`): patrón correcto `ELABORAR → NOTIFICAR → ESPERAR_PLAZO → ANALIZAR` para los tres tipos de trámite CONSULTA_*.
- `345_seed_tramites_tareas` (down_revision: `345_tramites_tareas`): patrón antiguo `REDACTAR → FIRMAR → NOTIFICAR → ESPERAR_PLAZO → INCORPORAR → ANALIZAR`.

Son ramas distintas de la cadena alembic. **Pendiente verificar** si 345 está aún activa o fue supersedida por completo al incorporar 370. Si coexisten, podría haber datos duplicados o inconsistentes en `tramites_tareas`.

### Documentos por tarea de trámite (migración 346)

`migrations/versions/346_tramites_tareas_documentos.py` define los vínculos documento↔tarea para los tres tipos de trámite de consultas:

| Tipo trámite | Tarea | Entrada | Salida |
|---|---|---|---|
| CONSULTA_SEPARATA | 1 ELABORAR | DOC_SEPARATA | OFICIO_SEPARATA (obligatorio) |
| CONSULTA_SEPARATA | 2 NOTIFICAR | OFICIO_SEPARATA | — (obligatorio) |
| CONSULTA_SEPARATA | 3 ESPERAR_PLAZO | — | RESPUESTA_ORGANISMO (no oblig.) |
| CONSULTA_SEPARATA | 4 ANALIZAR | RESPUESTA_ORGANISMO | DIAGNOSTICO (obligatorio) |
| CONSULTA_TRASLADO_TITULAR | 1 ELABORAR | RESPUESTA_ORGANISMO (oblig.) | OFICIO_TRASLADO_RESPUESTA (oblig.) |
| CONSULTA_TRASLADO_TITULAR | 2 NOTIFICAR | OFICIO_TRASLADO_RESPUESTA | — |
| CONSULTA_TRASLADO_TITULAR | 3 ESPERAR_PLAZO | — | RESPUESTA_TITULAR |
| CONSULTA_TRASLADO_TITULAR | 4 ANALIZAR | RESPUESTA_TITULAR | DIAGNOSTICO |
| CONSULTA_TRASLADO_ORGANISMO | 1 ELABORAR | RESPUESTA_TITULAR (oblig.) | OFICIO_TRASLADO_REPAROS (oblig.) |
| CONSULTA_TRASLADO_ORGANISMO | 2 NOTIFICAR | OFICIO_TRASLADO_REPAROS | — |
| CONSULTA_TRASLADO_ORGANISMO | 3 ESPERAR_PLAZO | — | RESPUESTA_ORGANISMO |
| CONSULTA_TRASLADO_ORGANISMO | 4 ANALIZAR | RESPUESTA_ORGANISMO | DIAGNOSTICO |

---

## 2. Modelo SQLAlchemy

**Fichero:** `app/models/organismos_expediente.py`

Implementado completo con todos los campos del diseño de referencia (`DISEÑO_CONSULTAS_ORGANISMOS.md §2`). Relaciones ORM: `expediente` (backref `organismos`), `organismo` (→ Entidad), `documento`, `tramite`.

**Método `as_contexto_cb()`** — devuelve dict con `organismo_nombre`, `organismo_nif`, `organismo_plazo_legal`, `organismo_resultado` (=estado). Usado por `ContextoConsultaSeparata`.

**Gap menor:** no existe propiedad `.es_terminal` que evalúe si el estado está en el conjunto `{cerrado_favorable, cerrado_con_condicionados, audiencia_previa, exonerado}`. Las variables del motor (§5) necesitarán construir ese check internamente.

---

## 3. Seeds y datos maestros

### Entidades con `rol_consultado = True`

`scripts/seed_demo.py` crea Endesa, REE y otras distribuidoras con `rol_consultado=True`. ✅ El sistema puede listarlas para asignar organismos a un expediente.

### Registros en `organismos_expediente`

**El seed_demo NO crea ningún registro en `organismos_expediente`.** Los expedientes AT-2002 a AT-2009 tienen fases CONSULTAS (algunas = FIN) pero sin organismos asociados. La fase CONSULTAS se crea y cierra "vacía" con `fase_fin()`. El sistema no tiene ningún dato representativo del ciclo real.

### Tipos de trámite en catálogo (`348_seed_catalogo_base`)

Los tres tipos están registrados con IDs fijos:

| ID | Código |
|---|---|
| 8 | CONSULTA_SEPARATA |
| 9 | CONSULTA_TRASLADO_TITULAR |
| 10 | CONSULTA_TRASLADO_ORGANISMO |

### Plantilla de escrito asociada (migración 402)

`migrations/versions/402_notificacion_organismo.py` registra la plantilla `NOTIF_ORGANISMO` asociada al trámite `CONSULTA_TRASLADO_ORGANISMO` (id=10) y al tipo de documento `OFICIO_TRASLADO_REPAROS`. ✅

### Plazos en `catalogo_plazos`

**No existe seed de plazos para la fase CONSULTAS.** Los plazos (30 días separata, 15 días traslados) están solo capturados en `organismos_expediente.plazo_legal_dias` en el momento de crear la separata. No están modelados en `catalogo_plazos` como sí lo están los plazos de RESOLUCION. Ver §12 (derivado candidato).

---

## 4. Context Builders

| CB | Fichero | Para trámite | Estado |
|---|---|---|---|
| `ContextoConsultaSeparata` | `app/services/context_builders/consulta_separata.py` | CONSULTA_SEPARATA | ✅ implementado |
| CB para traslados | — | CONSULTA_TRASLADO_TITULAR | ❌ no existe |
| CB para traslados | — | CONSULTA_TRASLADO_ORGANISMO | ❌ no existe |

**Campos que aporta `ContextoConsultaSeparata`:** `organismo_nombre`, `organismo_nif`, `organismo_plazo_legal`, `organismo_resultado`, `organismo_fecha_envio`, `organismo_fecha_respuesta`.

**Problema de vinculación para los CBs de traslado:** el campo `tramite_id` de `organismos_expediente` tiene UNIQUE y apunta solo al `CONSULTA_SEPARATA`. Los trámites `CONSULTA_TRASLADO_TITULAR` y `CONSULTA_TRASLADO_ORGANISMO` no tienen FK directa al registro de organismo.

Para navegar desde un trámite de traslado hasta su `organismos_expediente` se necesitaría: `tramite → fase → trámites CONSULTA_SEPARATA de la fase → organismos_expediente`. Si hay un único organismo en la fase la navegación es unívoca; con múltiples organismos podría ser ambigua si los trámites de traslado no están ordenados de forma que permita identificar a cuál organismo pertenece cada uno.

**Decisión de diseño pendiente:** hay dos opciones:
- A) Añadir FK `organismo_expediente_id` al modelo `Tramite` (genérico pero rompería la genericidad del modelo).
- B) Añadir tabla de vínculo `tramite_organismo` (N:M ligero, más flexible).
- C) Asumir que siempre hay un único organismo por fase y navegar por posición (frágil).

Esta decisión está fuera del alcance del núcleo de #247 y es candidata a issue derivado. Ver §12.

---

## 5. Motor de reglas y variables

### Infraestructura

`app/services/motor_reglas.py` — motor completamente agnóstico. Evalúa reglas almacenadas en BD contra un dict de variables. Soporta acciones CREAR y BORRAR; efectos BLOQUEAR y ADVERTIR con excepciones anulantes. ✅

`app/services/assembler.py` — carga todas las variables activas del `catalogo_variables`, las evalúa con funciones del registry, y compila el sujeto calificado ESFTT. Para solicitudes combinadas (AAP+AAC) evalúa el motor por cada tipo simple con `evaluar_multi`. ✅

### Variables actualmente en el registry

| Variable | Descripción |
|---|---|
| `fase_ip_finalizada` | True si existe alguna fase IP finalizada en el expediente |
| `tramite_publicar_existe` | True si hay trámite PUBLICACION en RESOLUCION |
| `existe_fase_finalizadora_cerrada` | True si hay fase finalizadora cerrada en la solicitud |
| `tiene_solicitud_aap_favorable` | True si hay solicitud AAP resuelta favorablemente (plazo 15 días en AAC pura) |
| `tipo_solicitud` | Siglas del tipo de solicitud en contexto |
| `es_solicitud_aac_pura` | True si solicitud contiene AAC y no AAP ni DUP |
| `tipo_sujeto_solicitado` | Código del tipo de objeto actuado |
| `sin_linea_aerea` | Campo del proyecto |
| `max_tension_nominal_kv` | Campo del proyecto |
| `solo_suelo_urbano_urbanizable` | Campo del proyecto |

### Variables necesarias para CONSULTAS — no existen

| Variable a crear | Tipo | Para qué regla |
|---|---|---|
| `organismos_todos_terminados` | calculado | Regla BLOQUEAR cierre de fase CONSULTAS si algún organismo no está en estado terminal |
| `organismo_supera_iteraciones` | calculado | Regla ADVERTIR (o BLOQUEAR) si `num_iteraciones_organismo > 1` en algún organismo de la fase |

Sin estas variables no es posible crear las reglas en BD. El tramitador puede hoy cerrar la fase CONSULTAS aunque todos los organismos estén en estado `pendiente`.

### Variables necesarias para ANALISIS_SOLICITUD — no existen

| Variable a crear | Tipo | Para qué regla |
|---|---|---|
| `tramite_requerimiento_sin_respuesta` | calculado | Bloquear cierre si hay REQUERIMIENTO_SUBSANACION con ESPERAR_PLAZO sin doc producido |
| `tramite_analisis_documental_con_deficiencias` | calculado | Bloquear cierre si hay ANALISIS_DOCUMENTAL con resultado ≠ OK |

---

## 6. Invariantes estructurales

`app/services/invariantes_esftt.py` — `_check_finalizar_fase` verifica actualmente:

1. Tareas de tipos ELABORAR/NOTIFICAR/ANALIZAR sin documento producido → BLOQUEAR.
2. Tareas NOTIFICAR con resultado INCORRECTA (notificación fallida) → BLOQUEAR.

**No hay check específico para CONSULTAS** (verificar que todos los `organismos_expediente` estén en estado terminal). Por diseño, esto debe vivir en el motor como variable calculada + regla en BD, no en `invariantes_esftt.py`. Pero hasta que las variables no existan, este check simplemente no ocurre.

**Conclusión:** al finalizar hoy la fase CONSULTAS, el sistema solo verifica que todas las tareas de los trámites tengan documentos producidos. No verifica el estado de los registros en `organismos_expediente`.

---

## 7. Motor de plazos

`app/services/plazos.py` — `CONSULTA_SEPARATA` está incluido en `_TRAMITES_SUSPENSION`: mientras el trámite está abierto, el plazo del procedimiento queda suspendido (art. 22.1.b LPACAP). ✅

`CONSULTA_TRASLADO_TITULAR` y `CONSULTA_TRASLADO_ORGANISMO` **no están en `_TRAMITES_SUSPENSION`**. Esta ausencia no está documentada como decisión consciente en el diseño. El RD no los menciona expresamente como causa de suspensión, lo que podría ser correcto, pero debe confirmarse.

---

## 8. Rutas y API

### API BC (api_bc.py)

CRUD genérico: crear/editar/borrar/finalizar solicitudes, fases, trámites, tareas. El motor se invoca en todas las acciones CREAR y BORRAR vía `evaluar_multi`. ✅ para el flujo general.

**Sin ningún endpoint para `organismos_expediente`:**

| Operación | Estado |
|---|---|
| GET organismos de un expediente (listado con estado) | ❌ falta |
| POST añadir organismo al expediente | ❌ falta |
| PATCH cambiar estado de organismo manualmente | ❌ falta |
| DELETE quitar organismo del expediente | ❌ falta |
| POST acción en bloque "Enviar consultas" (crea N trámites CONSULTA_SEPARATA) | ❌ falta |
| Lógica de actualizar `organismos_expediente.estado` al finalizar ANALIZAR | ❌ falta |
| Incremento de `num_iteraciones_organismo` al crear CONSULTA_TRASLADO_ORGANISMO | ❌ falta |

### Búsqueda de entidades consultables

`api_entidades.py` no expone búsqueda filtrada por `rol_consultado = True`. Necesario para el formulario de añadir organismo a un expediente.

### api_seguimiento.py

Expone `pista_CONSULTAS` (estado pista de la fase) pero sin detalle de organismos individuales.

---

## 9. Templates y UI

**No existe ningún template** para la gestión de organismos consultados. El inventario completo de templates de la zona de tramitación:

- `templates/expedientes/wizard_paso{1,2,3}.html` — alta de expediente
- `templates/vistas/vista3_bc/_tabla_hijos.html` — partial genérico de tabla (hijos de cualquier nivel ESFTT)
- `templates/macros/bc_cards.html`, `page_header.html` — macros de layout

La arquitectura de la vista de tramitación usa JS en el cliente que consume los endpoints de `api_bc.py`. No hay una plantilla de detalle del expediente como tal: el frontend construye la vista dinámicamente.

**Funcionalidades de UI que faltan completamente:**

- Panel de organismos del expediente (lista con estado, via, plazo, fechas)
- Formulario para añadir organismo (selector entidades con `rol_consultado=True`, campo `via`)
- Cambio de estado manual por organismo (tramitador registra resultado del organismo)
- Indicador visual de organismos bloqueantes (pendientes de respuesta)
- Botón / acción "Enviar consultas en bloque"
- Vista de detalle de organismo (historial de trámites asociados)

---

## 10. Tests

| Test | Fichero | Estado |
|---|---|---|
| `OrganismoExpediente.as_contexto_cb()` — 5 casos | `tests/test_391_organismo_expediente.py` | ✅ |
| `ContextoConsultaSeparata.get_contexto()` — 5 casos | idem | ✅ |
| Variables del motor para CONSULTAS | — | ❌ No existen (las variables no existen) |
| Invariante de cierre de fase CONSULTAS | — | ❌ No existe |
| Acción en bloque "Enviar consultas" | — | ❌ No existe |
| Integración flujo completo (añadir org → enviar → ciclo → cerrar) | — | ❌ No existe |

---

## 11. ANALISIS_TECNICO — situación real en el sistema

`ANALISIS_TECNICO` como fase separada **fue eliminada en FTT v5.5** y absorbida en `ANALISIS_SOLICITUD`. Solo aparece como código legacy en la migración de abreviaturas (`0869cda75380`) pero no existe como `tipos_fases` activo en el sistema operativo.

El issue #247 titula "análisis técnico" refiriéndose a los trámites `ANALISIS_DOCUMENTAL` (= `COMPROBACION_DOCUMENTAL` en el diseño) y `REQUERIMIENTO_SUBSANACION` (= `REQUERIMIENTO_DE_MEJORA`) que viven dentro de la fase `ANALISIS_SOLICITUD`.

**Las reglas de cierre de ANALISIS_SOLICITUD** que menciona `DISEÑO_CONSULTAS_ORGANISMOS.md §7`:
- Ningún `REQUERIMIENTO_SUBSANACION` con `ESPERAR_PLAZO` sin documento producido (titular no ha respondido)
- Ningún `ANALISIS_DOCUMENTAL` con resultado ≠ OK (técnico no ha dado el visto bueno)

Estas reglas no tienen implementación actual ni en invariantes ni en el motor. Son candidatas a issue derivado o a ampliar el alcance de #247. Ver §12.

---

## 12. Derivados candidatos — cruce con issues

Cruce realizado el 2026-05-24 contra el tracker completo (issues abiertos y cerrados).

### Tabla resumen

| Derivado | Issue existente | Estado issue | Decisión |
|---|---|---|---|
| D1 — CB traslados | — | — | **Nuevo issue** |
| D2 — Vinculación trámite-traslado → organismo | — | — | **Nuevo issue** (prerequisito de D1) |
| D3 — Actualizar `estado` en ANALIZAR | — | — | **Nuevo issue** |
| D4 — Incrementar `num_iteraciones_organismo` | — | — | **Nuevo issue** |
| D5 — Variables motor CONSULTAS | — | — | **Nuevo issue** |
| D6 — Variables motor ANALISIS_SOLICITUD | **#442** (parcial) | Abierto | Ampliar alcance de #442 o nuevo complementario |
| D7 — UI panel organismos | **#396** | Abierto | Cubierto — no crear |
| D8 — API endpoints `organismos_expediente` | Parte del core #247 | Abierto | Núcleo de #247, no issue separado |
| D9 — API entidades consultables | — | — | **Nuevo issue** (prereq de D7/#396) |
| D10 — Acción en bloque "Enviar consultas" | — | — | **Nuevo issue** |
| D11 — Seed `catalogo_plazos` CONSULTAS | — | — | **Nuevo issue** (patrón: #448) |
| D12 — Seed demo `organismos_expediente` | — | — | **Nuevo issue** |
| D13 — Auditoría migraciones 345 vs 370 | — | — | **Nuevo issue** |

---

### D1 — CB para CONSULTA_TRASLADO_TITULAR y CONSULTA_TRASLADO_ORGANISMO

Context Builders para los trámites de traslado. Requiere primero resolver D2 (vinculación FK).

**Cruce:** No existe issue. El #391 (cerrado) solo cubre `ContextoConsultaSeparata`. → **Nuevo issue.**

### D2 — Vinculación trámite-traslado → organismo_expediente

Decisión de diseño + implementación de cómo los trámites `CONSULTA_TRASLADO_TITULAR` y `CONSULTA_TRASLADO_ORGANISMO` se vinculan a su `organismos_expediente`. Tres opciones analizadas en §4. Impacta al modelo, migraciones y los CB del D1.

**Cruce:** No existe issue. → **Nuevo issue** (prerequisito de D1; conviene abrir antes de implementar D1).

### D3 — Actualización automática de `organismos_expediente.estado` desde ANALIZAR

Cuando el tramitador finaliza la tarea ANALIZAR de un trámite `CONSULTA_SEPARATA`, el sistema debería actualizar el estado del `organismos_expediente` correspondiente. Actualmente el campo se actualiza a mano. Impacta a `api_bc.py::finalizar_tarea` o a un evento post-tarea.

**Cruce:** No existe issue. → **Nuevo issue.**

### D4 — Incremento automático de `num_iteraciones_organismo`

Al crear un trámite `CONSULTA_TRASLADO_ORGANISMO`, el contador del organismo debe incrementarse. Actualmente no hay ninguna lógica que lo haga.

**Cruce:** No existe issue. → **Nuevo issue** (puede agruparse con D3 si se implementan juntos en `api_bc.py`).

### D5 — Variables del motor para cierre de CONSULTAS

Crear las variables calculadas `organismos_todos_terminados` y `organismo_supera_iteraciones` en el registry, y los seeds de reglas en BD correspondientes.

**Cruce:** No existe issue específico. Las variables del motor de RESOLUCION sí tienen issues (ej. #190, #328, cerrados). → **Nuevo issue.**

### D6 — Variables del motor para cierre de ANALISIS_SOLICITUD

Crear las variables calculadas para los checks técnicos de REQUERIMIENTO sin respuesta y ANALISIS_DOCUMENTAL con deficiencias (`tramite_requerimiento_sin_respuesta`, `tramite_analisis_con_deficiencias`).

**Cruce:** El issue **#442** "[DISEÑO/MODELO] Tabla documentos_analizar — semáforo `tiene_defectos` para el motor" (abierto) cubre parcialmente la variable de ANALISIS_DOCUMENTAL: define el campo `tiene_defectos` como fuente. El chequeo de REQUERIMIENTO sin respuesta no está en #442. → **Evaluar con el usuario**: ampliar alcance de #442 para incluir ambas variables, o abrir issue complementario solo para la parte de REQUERIMIENTO.

### D7 — UI panel de organismos del expediente

Toda la interfaz de usuario para gestionar `organismos_expediente`: listar, añadir, cambiar estado, ver detalle.

**Cruce:** Issue **#396** "[FE] UI gestión organismos_expediente" (abierto). → **Cubierto — no crear issue nuevo.**

### D8 — API endpoints para `organismos_expediente`

CRUD + acción en bloque en `api_bc.py` o blueprint propio. Incluye: GET listado, POST añadir organismo, PATCH cambiar estado, DELETE quitar, lógica actualizar estado al finalizar ANALIZAR, incremento iteraciones.

**Cruce:** El título de #247 es "[DISEÑO] Fase de consultas…" — el diseño lleva implícita la implementación del backend. El #396 lleva el prefijo [FE], lo que sugiere que el backend es parte del núcleo de #247. → **No crear issue separado**; el backend de `organismos_expediente` es el núcleo de #247. D3 y D4 son sub-tareas de implementación de #247.

### D9 — Búsqueda de entidades consultables en `api_entidades.py`

Filtro por `rol_consultado = True` para el selector del formulario de añadir organismo.

**Cruce:** No existe issue. `api_entidades.py` fue creado sin este endpoint. → **Nuevo issue** (prerequisito de #396/D7).

### D10 — Acción en bloque "Enviar consultas"

Endpoint + UI que, desde la lista de organismos con `via = consulta` y `estado = pendiente`, genera automáticamente un trámite `CONSULTA_SEPARATA` por organismo y enlaza cada uno al registro de organismo (`tramite_id`). Incluye cálculo de `plazo_legal_dias` en el momento de creación.

**Cruce:** No existe issue. → **Nuevo issue** (puede ser parte del alcance de #247 o issue independiente por volumen).

### D11 — Seed `catalogo_plazos` para CONSULTAS

Plazos 30 días (SEPARATA) y 15 días (traslados) con condiciones por tipo de solicitud, siguiendo el patrón del issue #448 (cerrado: seed plazos RESOLUCION).

**Cruce:** No existe issue. El #448 (cerrado) es el patrón exacto a seguir. → **Nuevo issue** (análogo a #448).

### D12 — Seed demo con `organismos_expediente` reales

Añadir registros representativos al seed_demo para que AT-2002 y siguientes reflejen el ciclo real de consultas.

**Cruce:** No existe issue. → **Nuevo issue** (puede vincularse al milestone de #247).

### D13 — Auditoría migraciones 345 vs 370

Verificar si ambas migraciones coexisten en la cadena activa o si 345 fue supersedida. Si coexisten, determinar si hay datos duplicados en `tramites_tareas` y limpiar.

**Cruce:** No existe issue específico. El #271 "[AUDITORÍA] Flecos huérfanos" (cerrado) era genérico. → **Nuevo issue** (deuda técnica puntual; puede abrirse con baja prioridad).

---

## Resumen ejecutivo por capa

| Capa | Implementado | Parcial | Falta completamente |
|---|---|---|---|
| Estructura BD (`organismos_expediente`) | ✅ completa | — | — |
| GRANT y permisos | ✅ (#449) | — | — |
| Consulta nombrada SQL | ✅ (#395) | — | — |
| Modelo ORM | ✅ + tests | `.es_terminal` property | — |
| Seed tipos_tramites (patrón ELABORAR) | ✅ (370) | Conflicto 345? | — |
| Documentos por tarea CONSULTA_* | ✅ (346) | — | — |
| Seed entidades consultables | ✅ seed_demo | — | — |
| CB `ContextoConsultaSeparata` | ✅ + tests | — | — |
| CB para trámites de traslado | — | Diseño vinculación pendiente (D1, D2) | — |
| Motor de reglas infraestructura | ✅ | — | — |
| Variables calculadas para CONSULTAS | — | — | `organismos_todos_terminados`, `organismo_supera_iteraciones` |
| Variables para ANALISIS_SOLICITUD | — | — | `tramite_requerimiento_sin_respuesta`, `tramite_analisis_con_deficiencias` |
| Reglas en BD para CONSULTAS | — | — | Dependen de variables |
| Invariante específico CONSULTAS | — | Por diseño vive en motor | — |
| Motor de plazos: CONSULTA_SEPARATA | ✅ suspende plazo | — | — |
| Motor de plazos: traslados | — | Decisión documentada? | — |
| Seed `catalogo_plazos` CONSULTAS | — | — | ✅ (D11) |
| API CRUD `organismos_expediente` | — | — | Completo (D8) |
| API acción en bloque | — | — | D10 |
| API entidades consultables | — | — | D9 |
| UI panel organismos | — | — | D7 |
| Seed demo organismos | — | — | D12 |
| Tests motor CONSULTAS | — | — | D5 |
| Tests integración flujo | — | — | — |
