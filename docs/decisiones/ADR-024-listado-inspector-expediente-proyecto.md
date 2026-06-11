# ADR-024 — Listado único y inspector de expediente/proyecto

**Estado:** Adoptada
**Fecha:** 2026-06-11
**Issue:** #543
**Depende de:** ADR-023 (#534) — inspector overlay universal y modelo de tres capas.

---

## Contexto

Expediente y Proyecto son 1:1 en el modelo ORM (`expedientes.proyecto_id UNIQUE`). Sin embargo, la app tiene dos listados separados que llevan al mismo destino:

- `/expedientes/` — filtro por estado, botón "Tramitar", contexto tramitación.
- `/proyectos/` — filtro por IA, contexto técnico. Sus rutas de detalle y edición son redirects a las vistas del expediente.

El formulario de edición actual (`expedientes.editar`) ya mezcla campos de ambas tablas: tipo_expediente, heredado, responsable (del expediente) y título, descripción, finalidad, emplazamiento, ia_id, municipios (del proyecto).

La dualidad de listados es deuda histórica, no dos vistas con propósito distinto. Este ADR la resuelve aplicando el patrón ADR-023 al par expediente/proyecto.

**Nota de dominio:** el modelo `Proyecto` actual contiene solo los metadatos de cabecera de la instalación y variables del motor de reglas. Las entidades eléctricas del proyecto (líneas, subestaciones, centros de transformación) no existen aún como modelo ORM y se gestionarán en una isla React futura. Este ADR diseña solo para los datos actuales del modelo.

---

## Decisión

### 1. Listado único en `/expedientes/`

Se elimina la dualidad. Un único listado bajo `/expedientes/` con columnas y filtros que cubren ambos contextos (tramitación y técnico). Rutas del módulo de proyectos:

- `GET /proyectos/` → redirect 302 a `/expedientes/`
- `GET /proyectos/<id>` → redirect 302 a `/expedientes/?sel=<id>`
- `GET /proyectos/<id>/editar` → redirect 302 a `/expedientes/?sel=<id>` (el inspector abre en modo edición)

### 2. Columnas del listado

| Columna | Fuente | Visible por defecto |
|---|---|---|
| AT | `expediente.numero_at` | ✓ |
| Tipo | `tipo_expediente.abreviatura` | ✓ |
| Título | `proyecto.titulo` | ✓ |
| Titular | `expediente.titular` (snapshot) | ✓ |
| IA | `proyecto.ia.abreviatura` | ✓ |
| Municipios | resumen N municipios | ✓ |
| Responsable | `responsable.siglas` | ✓ |
| Estado pista | calculado `seguimiento.py` | ✓ |

**Maestro reducido** (cuando el inspector está abierto): AT + Tipo + Título + Titular.

### 3. Filtros del listado

Los filtros existentes (estado, responsable) se conservan. Se añaden:
- Tipo de expediente
- Instrumento ambiental (IA)
- Municipio
- Titular

### 4. Estructura del inspector (capa 2 ADR-023)

El fragmento `/expedientes/<id>/fragmento` sirve el partial HTML del inspector. Organización en secciones:

#### 4.1 Cabecera — siempre visible, solo lectura

- Número AT + tipo expediente
- Titular actual (snapshot `titular_id`) — etiqueta "Titular del expediente" (no "titular de la instalación", distinción relevante en el futuro)
- Estado resumido por pistas (calculado `seguimiento.py`)

#### 4.2 Acción primaria

Botón "Tramitar" prominente (primer elemento tras la cabecera) → árbol del expediente.

No se expone en la fila del listado — la fila selecciona y abre el inspector; la acción principal vive ahí.

#### 4.3 Datos administrativos — editable con permiso

- `tipo_expediente_id` (selector)
- `heredado` (checkbox)
- `responsable_id` (selector usuarios) — solo visible si `puede_cambiar_responsable()`

#### 4.4 Datos del proyecto — editable con permiso

- `titulo`, `finalidad`, `emplazamiento` (texto)
- `descripcion` (textarea, colapsable por longitud)
- `ia_id` (selector instrumento ambiental)
- `fecha` del proyecto (fecha técnica firma/visado)
- `es_modificacion` (checkbox)

#### 4.5 Variables del motor — editable ADMIN/SUPERVISOR

- `sin_linea_aerea` (checkbox)
- `max_tension_nominal_kv` (numérico)
- `solo_suelo_urbano_urbanizable` (checkbox)

#### 4.6 Municipios — solo lectura + delegación a modal

Lista compacta de municipios afectados + botón "Gestionar municipios" → modal grande (§5).

#### 4.7 Placeholder "Instalaciones"

Botón **desactivado** "Instalaciones" con tooltip informativo. Punto de entrada reservado para la futura vista de entidades técnicas del proyecto (isla React). Se activa cuando esa isla exista; mientras tanto es un marcador visual de que la entidad tiene esa dimensión.

No se muestra como "slot vacío" — es un botón con texto claro que comunica que esa funcionalidad es futura.

### 5. Modal grande — municipios (capa 3 ADR-023)

`SelectorBusqueda` múltiple con búsqueda para los municipios afectados por el proyecto. Se lanza desde §4.6. Al cerrar, el inspector se refresca con la lista actualizada.

Municipios no va en el inspector directo porque el widget de selección múltiple con búsqueda no es cómodo en el panel estrecho (contrasta con la lectura compacta de §4.6). Es el criterio de "lo que no cabe" de ADR-023 §6.

### 6. Responsable: inspector, no modal

`responsable_id` es un campo escalar del expediente — va en el inspector (§4.3), condicional a `puede_cambiar_responsable()`. No escala a modal porque no es una sub-colección con CRUD propio.

---

## Fuera de alcance de este ADR

- **Cambio formal de titular via solicitud** — es una cadena ESFTT completa (issue #429). El inspector muestra el titular en lectura. La corrección de error de titular y el historial de titularidad se dejan para un issue específico posterior.
- **Editor de entidades técnicas del proyecto** — isla React futura; modelo ORM aún no existe.
- **Número de registro de instalación** — campo que existirá cuando el proceso de puesta en marcha esté modelado.
- **Titularidad de las instalaciones** — difiere conceptualmente del titular del expediente; requiere modelo propio.

---

## Alternativas descartadas

### A. Mantener dos listados con inspector compartido
El inspector sería idéntico en ambos casos. La dualidad de URLs solo añade fricción de navegación sin valor. Descartada.

### B. Municipios en el inspector (panel lateral)
El `SelectorBusqueda` múltiple necesita espacio para su input de búsqueda, las chips de selección y la lista de resultados. En el panel estrecho (900px compartidos con la cabecera y las secciones de texto) resulta apretado. Modal grande es más cómodo y coherente con ADR-023 §6. Descartada.

### C. "Tramitar" como acción de fila (hover / menú contextual)
El clic en la fila ya tiene un significado (seleccionar → inspector). Añadir una acción secundaria de fila requiere hover + menú, que no es el patrón del sistema (ADR-023 §1 elimina la columna de acciones). "Tramitar" vive en el inspector, que es el contexto natural para decidir actuar sobre un expediente. Descartada como acción primaria de fila.
