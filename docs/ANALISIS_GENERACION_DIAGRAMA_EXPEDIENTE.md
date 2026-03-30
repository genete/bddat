# Análisis: Generación dinámica de diagrama de un expediente

> Fuente de verdad: `ESTRUCTURA_FTT.json`
> Última sincronización: 2026-03-30

**Estado:** En análisis — sin issue de implementación aún
**Relacionado con:** `DISEÑO_DIAGRAMAS_ESFTT.md` (diagramas estáticos de documentación) · #274 (revisión visual vista tramitación)

---

## Índice

1. [Concepto y motivación](#1-concepto-y-motivación)
2. [Diferencia con los diagramas estáticos](#2-diferencia-con-los-diagramas-estáticos)
3. [Decisión de arquitectura: tres capas](#3-decisión-de-arquitectura-tres-capas)
4. [Capa 1 — Endpoint `/api/expedientes/<id>/arbol` (JSON bruto)](#4-capa-1--endpoint-apiexpedientesidarbol-json-bruto)
5. [Capa 2 — Masticador por renderer](#5-capa-2--masticador-por-renderer)
6. [Capa 3 — Serializador Mermaid](#6-capa-3--serializador-mermaid)
7. [Interacción: frame único con expansión al clic](#7-interacción-frame-único-con-expansión-al-clic)
8. [Render y navegación en el navegador](#8-render-y-navegación-en-el-navegador)
9. [Pendientes antes de implementar](#9-pendientes-antes-de-implementar)

---

## 1. Concepto y motivación

El objetivo es generar **al vuelo** un diagrama visual del árbol ESFTT real de un expediente concreto — fases, trámites y tareas con sus estados actuales — y mostrarlo embebido en BDDAT.

A diferencia de los diagramas de documentación (capas 0–3 en `DISEÑO_DIAGRAMAS_ESFTT.md`), este diagrama:

- Se genera en runtime a partir de datos reales de BD, no de fuentes documentales
- Refleja el estado actual de cada nodo (pendiente / en curso / finalizado)
- Es específico de un expediente concreto, no del procedimiento genérico
- Se muestra en la propia aplicación, no en git ni en Miro

---

## 2. Diferencia con los diagramas estáticos

| Aspecto | Diagramas estáticos (`DISEÑO_DIAGRAMAS_ESFTT.md`) | Este análisis |
|---|---|---|
| **Origen** | JSON estructural + MDs de diseño | BD en tiempo real |
| **Sujeto** | El procedimiento genérico (todas las fases posibles) | Un expediente concreto (las fases que tiene) |
| **Estados** | Sin estados operacionales | Pendiente / En curso / Finalizado |
| **Render** | `mmdc` CLI → SVG comprometido en git | `mermaid.js` CDN en el navegador |
| **Destino** | Documentación, manual, Miro | Vista de tramitación en BDDAT |
| **Ciclo de vida** | Actualización manual cuando cambia la arquitectura | Regenerado en cada carga de página |

---

## 3. Decisión de arquitectura: tres capas

El sistema se estructura en tres capas independientes:

```
BD  →  _construir_arbol()  →  /api/expedientes/<id>/arbol  (JSON bruto)
                                         │
                          ┌──────────────┼──────────────┐
                          ▼              ▼              ▼
                   preparar_mmd()  preparar_excel()  preparar_*()
                          │
                          ▼
              arbol_to_mmd(arbol_preparado, fase_expandida_id)
                          │
                          ▼
                    mermaid.js (browser)
```

**Capa 1 — API bruta:** expone los datos tal como están en BD. Sin interpretación, sin decisiones de presentación.

**Capa 2 — Masticador:** transforma el JSON bruto en la forma que necesita cada renderer. Cada renderer tiene el suyo. El masticador para MMD decide qué es `en_curso`; el de Excel decide el formato de fecha; uno estadístico puede ignorar el detalle de tareas y agregar contadores.

**Capa 3 — Serializador:** toma el JSON ya preparado y emite el formato final (texto MMD, fichero xlsx, HTML…).

**Por qué no generar MMD directamente desde Flask:** el JSON bruto es útil por sí solo y agnóstico a cualquier renderer. Acoplar Flask a sintaxis Mermaid — o a cualquier formato de salida — contamina la API con decisiones de presentación.

---

## 4. Capa 1 — Endpoint `/api/expedientes/<id>/arbol` (JSON bruto)

### Por qué un endpoint nuevo y no ampliar `/jerarquia`

El endpoint existente `GET /api/expedientes/<id>/jerarquia` solo desciende hasta el nivel **Fase** y es consumido actualmente por Vista V3. Ampliarlo para incluir trámites y tareas rompería el contrato con ese consumidor o lo cargaría de datos que no necesita.

**Decisión:** endpoint nuevo `GET /api/expedientes/<id>/arbol`.

### Fuente de la lógica

La función `_construir_arbol()` en `app/routes/vista3.py` ya construye el árbol completo a 4 niveles con estados incluidos. El nuevo endpoint la reutiliza y devuelve el resultado como JSON puro en lugar de HTML renderizado.

### Estructura JSON bruta esperada

El JSON expone los campos reales de BD sin interpretación. El estado no se deduce aquí — eso es responsabilidad del masticador.

```json
[
  {
    "id": 1,
    "tipo_solicitud": {"id": 2, "siglas": "AAP"},
    "fecha_solicitud": "2025-06-15",
    "fecha_fin": null,
    "fases": [
      {
        "id": 12,
        "tipo_fase": {"id": 3, "codigo": "ANÁLISIS_SOLICITUD", "nombre": "Análisis de solicitud"},
        "fecha_inicio": "2025-06-20",
        "fecha_fin": "2025-07-10",
        "resultado_fase": {"id": 1, "codigo": "FAVORABLE"},
        "tramites": [
          {
            "id": 45,
            "tipo_tramite": {"id": 7, "codigo": "ANALISIS_DOCUMENTAL", "nombre": "Análisis documental"},
            "fecha_inicio": "2025-06-20",
            "fecha_fin": "2025-07-10",
            "tareas": [
              {
                "id": 101,
                "tipo_tarea": {"id": 1, "codigo": "ANALIZAR", "nombre": "Análisis"},
                "fecha_inicio": "2025-06-20",
                "fecha_fin": "2025-07-10",
                "documento_usado_id": 55,
                "documento_producido_id": 56
              }
            ]
          }
        ]
      }
    ]
  }
]
```

---

## 5. Capa 2 — Masticador por renderer

Función que transforma el JSON bruto en la forma que necesita un renderer concreto. Cada renderer tiene la suya.

### `preparar_para_mmd(arbol_bruto)`

Recorre el árbol bruto y produce un árbol enriquecido con las propiedades que necesita el serializador MMD:

- `estado`: deduce `pendiente` / `en_curso` / `finalizado` / `finalizado_favorable` a partir de `fecha_inicio`, `fecha_fin` y `resultado_fase`
- `label`: texto a mostrar en el nodo (nombre corto, código…)
- `clase`: nombre de la `classDef` Mermaid a aplicar
- `clickable`: booleano — si el nodo debe responder al clic (fases) o no (tareas)

El masticador es el único lugar donde vive la lógica "si `fecha_fin` es nulo y `fecha_inicio` no es nulo → en_curso". Ni la API ni el serializador la conocen.

### Otros masticadores (ejemplos futuros)

| Masticador | Qué produce |
|---|---|
| `preparar_para_excel(arbol_bruto)` | Fechas formateadas, duraciones calculadas, contadores de tareas |
| `preparar_para_timeline(arbol_bruto)` | Segmentos con inicio/fin absolutos para una vista Gantt |
| `preparar_para_stats(arbol_bruto)` | Agregados por fase, sin detalle de tareas |

---

## 6. Capa 3 — Serializador Mermaid

Un único serializador Python, desacoplado de Flask y testable en aislamiento. Recibe el árbol **ya masticado** por `preparar_para_mmd()`:

```python
def arbol_to_mmd(arbol_preparado, fase_expandida_id=None) -> str:
    ...
```

- `fase_expandida_id=None` — vista macro: todas las fases como nodos simples
- `fase_expandida_id=X` — fase X renderizada como subgraph con sus trámites y tareas; el resto de fases siguen visibles como nodos simples

### Orientación del diagrama

**`flowchart LR`** para el flujo principal — las fases se leen de izquierda a derecha, como una línea de tiempo. Esto produce un diagrama ancho y bajo que encaja naturalmente en un contenedor Bootstrap full-width (`col-12`).

Cuando una fase se expande, su subgraph usa `direction TB` — los trámites y tareas dentro de esa fase crecen verticalmente sin alterar la orientación horizontal general:

```
flowchart LR
  F1[ANÁLISIS]:::finalizada --> F2
  subgraph F2[CONSULTAS]:::en_curso
    direction TB
    T1[CONSULTA_SEPARATA]:::finalizado --> T2[TRASLADO_TITULAR]:::en_curso
  end
  F2 --> F3[INF_PÚBLICA]:::pendiente
```

El serializador usa los campos `clase` del árbol preparado para emitir `classDef` y colorear nodos según estado.

### El servidor genera el texto MMD

**Decisión:** Flask ejecuta el masticador y el serializador y devuelve el texto MMD. El navegador solo renderiza.

- Endpoint: `GET /api/expedientes/<id>/arbol/mmd?fase_id=X`
- El texto MMD es ligero (pocos KB) — la latencia del AJAX es imperceptible
- Toda la lógica de serialización permanece en Python, sin duplicar en JS

---

## 7. Interacción: frame único con expansión al clic

**Decisión:** un solo `<div>` cuyo contenido Mermaid se regenera al interactuar, sin salto de layout ni segunda zona en pantalla.

### Flujo de interacción

```
Carga inicial
  GET /api/expedientes/<id>/arbol/mmd  →  texto MMD (macro)
  mermaid.render()  →  SVG en el <div>
  svgPanZoom()      →  zoom/pan activo

Usuario hace clic en FASE X
  GET /api/expedientes/<id>/arbol/mmd?fase_id=X  →  texto MMD (fase expandida)
  svgPanZoomInstance.destroy()
  mermaid.render()  →  nuevo SVG en el mismo <div>
  svgPanZoom()      →  reinstanciar zoom/pan

Usuario hace clic en FASE X (ya expandida)
  → colapsa (misma llamada sin fase_id o con fase_id=null)
```

### Aspecto visual (orientación LR)

```
Vista macro:
  [ANÁLISIS]:::finalizada → [CONSULTAS]:::en_curso → [INF_PÚBLICA]:::pendiente → [RESOLUCIÓN]:::pendiente

Tras clic en CONSULTAS:
  [ANÁLISIS]:::finalizada →  subgraph CONSULTAS:::en_curso  → [INF_PÚBLICA]:::pendiente → [RESOLUCIÓN]:::pendiente
                               direction TB
                               [CONSULTA_SEPARATA]:::finalizado
                                      ↓
                               [TRASLADO_TITULAR]:::en_curso
```

El contexto del expediente completo permanece visible mientras se examina el detalle de una fase.

### Gestión del clic: problema de coexistencia con zoom/pan

svg-pan-zoom intercepta eventos de ratón para el pan (mousedown + drag). Los click callbacks de Mermaid se registran directamente sobre los nodos SVG. Ambos compiten por el mismo evento.

**En la práctica:** un click simple (sin arrastrar) generalmente llega al nodo porque svg-pan-zoom distingue click de drag. Pero hay casos problemáticos:
- Movimiento mínimo durante el click → svg-pan-zoom lo interpreta como pan y el click no llega al nodo
- En touch (tablet) la distinción tap/pan es más ambigua

**Opciones:**

| Opción | Descripción | Estado |
|---|---|---|
| **A) Umbral de sensibilidad** | Configurar svg-pan-zoom con umbral alto para considerar drag. El pan se vuelve menos fluido. | Compromiso incómodo |
| **B) Evento propio** | Capturar el click en el contenedor SVG e inspeccionar el elemento clicado. svg-pan-zoom expone si hubo drag antes del mouseup — permite discriminar limpiamente sin depender de los callbacks de Mermaid. | **Abierto — valorar en implementación** |
| **C) Separar interacción del diagrama** | El diagrama es solo visual + zoom/pan. La selección de fase se hace con un control externo al SVG (lista, breadcrumb). Sin conflicto posible. | Más robusta, menos integrada |

### Feedback visual: cursor

Los nodos clickables deben mostrar `cursor: pointer`. Mermaid genera clases CSS sobre los nodos SVG — se puede apuntar con CSS de mayor especificidad que el `cursor: grab` que aplica svg-pan-zoom sobre el área general. El campo `clickable` del masticador (§5) informa al serializador de qué nodos recibirán esta clase.

---

## 8. Render y navegación en el navegador

**Decisión:** `mermaid.js` vía CDN para renderizar SVG + `svg-pan-zoom` para zoom y pan.

### mermaid.js

| Aspecto | Valoración |
|---|---|
| **Dependencias servidor** | Ninguna — no requiere Node.js ni `mmdc` |
| **Integración** | `<script>` CDN + `<div id="diagrama">` actualizado por JS |
| **Regeneración** | `mermaid.render(id, codigoMMD)` devuelve SVG sin tocar el DOM — se inserta manualmente |
| **Riesgo** | Dependencia CDN externa — mitigable cacheando localmente si fuera necesario |

### svg-pan-zoom

Biblioteca ligera (~17KB, MIT) diseñada para añadir zoom y pan a SVGs generados dinámicamente.

| Funcionalidad | Detalle |
|---|---|
| **Zoom** | Rueda del ratón + botones +/− |
| **Pan** | Click + arrastrar |
| **Fit automático** | Ajusta el diagrama al contenedor en la carga inicial |
| **Reset** | Botón para volver al estado inicial |
| **Ciclo de vida** | `destroy()` antes de cada regeneración del SVG, reinstanciar después |

El fit automático resuelve el problema de aspecto: independientemente del tamaño del diagrama generado, el punto de partida siempre es el diagrama completo visible en el contenedor. El usuario ajusta desde ahí con zoom/pan libre.

---

## 9. Pendientes antes de implementar

- [ ] Crear issue de implementación y enlazarlo aquí
- [ ] Decidir en qué vista se muestra el diagrama (¿tab en tramitación?, ¿modal?, ¿panel lateral?)
- [ ] Prototipar la sintaxis MMD generada para un expediente real de prueba y validar legibilidad
- [ ] Decidir estrategia de gestión del clic con svg-pan-zoom: opción B (evento propio) u opción C (control externo) — ver §7
- [ ] Decidir si `mermaid.js` y `svg-pan-zoom` se cargan desde CDN o se incluyen en el bundle del proyecto
