# Análisis: Generación dinámica de diagrama de un expediente

> Fuente de verdad: `ESTRUCTURA_FTT.json`
> Última sincronización: 2026-03-30

**Estado:** En análisis — sin issue de implementación aún
**Relacionado con:** `DISEÑO_DIAGRAMAS_ESFTT.md` (diagramas estáticos de documentación)

---

## Índice

1. [Concepto y motivación](#1-concepto-y-motivación)
2. [Diferencia con los diagramas estáticos](#2-diferencia-con-los-diagramas-estáticos)
3. [Decisión de arquitectura: API JSON agnóstica](#3-decisión-de-arquitectura-api-json-agnóstica)
4. [Endpoint `/api/expedientes/<id>/arbol`](#4-endpoint-apiexpedientesidarbol)
5. [Serializadores Mermaid](#5-serializadores-mermaid)
6. [Estrategia híbrida: dos diagramas](#6-estrategia-híbrida-dos-diagramas)
7. [Render client-side con mermaid.js](#7-render-client-side-con-mermaidjs)
8. [Pendientes antes de implementar](#8-pendientes-antes-de-implementar)

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

## 3. Decisión de arquitectura: API JSON agnóstica

**Decisión:** el backend expone un endpoint JSON puro a 4 niveles. El serializador Mermaid es una capa posterior independiente.

**Por qué no generar MMD directamente desde Flask:** el árbol JSON del expediente es útil por sí solo y puede ser consumido por múltiples renderers (Mermaid, una futura vista de timeline, exportación a Excel, tests de integración). Acoplar Flask directamente a sintaxis Mermaid sacrifica esa reusabilidad sin ningún beneficio.

```
BD  →  _construir_arbol()  →  /api/expedientes/<id>/arbol (JSON)
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                    arbol_to_mmd_macro()   arbol_to_mmd_detalle()
                              │                     │
                              └──────────┬──────────┘
                                         ▼
                                   mermaid.js (browser)
```

---

## 4. Endpoint `/api/expedientes/<id>/arbol`

### Por qué un endpoint nuevo y no ampliar `/jerarquia`

El endpoint existente `GET /api/expedientes/<id>/jerarquia` solo desciende hasta el nivel **Fase** y es consumido actualmente por Vista V3. Ampliarlo para incluir trámites y tareas rompería el contrato con ese consumidor o lo cargaría de datos que no necesita.

**Decisión:** endpoint nuevo `GET /api/expedientes/<id>/arbol`.

### Fuente de la lógica

La función `_construir_arbol()` en `app/routes/vista3.py` ya construye el árbol completo a 4 niveles con estados incluidos. El nuevo endpoint la reutiliza y devuelve el resultado como JSON puro en lugar de HTML renderizado.

### Estructura JSON esperada

```json
[
  {
    "id": 1,
    "codigo": "SOL-1",
    "tipos": "AAP + AAC",
    "estado": "EN_CURSO",
    "fases": [
      {
        "id": 12,
        "codigo": "ANÁLISIS_SOLICITUD",
        "nombre": "Análisis de solicitud",
        "estado": "Finalizada",
        "tramites": [
          {
            "id": 45,
            "codigo": "ANALISIS_DOCUMENTAL",
            "nombre": "Análisis documental",
            "estado": "Finalizado",
            "tareas": [
              {
                "id": 101,
                "codigo": "ANALIZAR",
                "nombre": "Análisis",
                "estado": "Ejecutada"
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

## 5. Serializadores Mermaid

Dos funciones Python independientes, desacopladas de Flask y testables en aislamiento:

### `arbol_to_mmd_macro(arbol)`

Genera un `stateDiagram-v2` con el mapa de fases del expediente. Muestra qué fases existen y cuál está activa. No desciende a trámites ni tareas.

Útil para: ¿en qué punto del procedimiento está este expediente?

### `arbol_to_mmd_detalle(arbol, fase_id)`

Genera un `flowchart TD` con subgraphs anidados para la fase seleccionada: sus trámites como subgraphs y las tareas como nodos dentro de cada subgraph.

Útil para: ¿qué hay que hacer en esta fase y en qué estado está cada tarea?

Ambos serializadores aplican `classDef` para colorear nodos según estado (pendiente / en curso / finalizado / finalizado favorable).

---

## 6. Estrategia híbrida: dos diagramas

Mermaid no permite mezclar tipos de diagrama (`stateDiagram-v2` y `flowchart`) en un solo bloque. La solución son dos bloques `<div class="mermaid">` independientes renderizados en la misma vista:

```
┌─────────────────────────────────────────────────┐
│  stateDiagram-v2  — Mapa de fases               │
│  ANÁLISIS_SOLICITUD → CONSULTAS → ...           │
│  (fase activa resaltada)                        │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  flowchart TD  — Detalle de fase activa         │
│  subgraph ANALISIS_DOCUMENTAL                   │
│    ANALIZAR[Análisis]:::ejecutada               │
│  end                                            │
│  subgraph COMUNICACION_INICIO                   │
│    REDACTAR --> FIRMAR --> NOTIFICAR             │
│  end                                            │
└─────────────────────────────────────────────────┘
```

El diagrama de detalle se regenera cuando el usuario selecciona una fase distinta.

### Consideración sobre el tamaño

Un ESFTT completo (8 fases × varios trámites × hasta 6 tareas) genera un grafo grande en el diagrama de detalle. Opciones a valorar en implementación:

- Mostrar solo la fase activa en el detalle (lo más probable)
- Mostrar todas las fases con posibilidad de colapsar

---

## 7. Render client-side con mermaid.js

**Decisión:** `mermaid.js` vía CDN, renderizado en el navegador.

| Aspecto | Valoración |
|---|---|
| **Dependencias servidor** | Ninguna — no requiere Node.js ni `mmdc` instalado |
| **Integración** | Un `<script>` CDN y `<div class="mermaid">…</div>` con el código generado por Flask |
| **Interactividad** | `mermaid.js` soporta `click` callbacks en nodos — posible navegación al trámite al hacer clic |
| **Actualización dinámica** | Con JS: regenerar el `div` y llamar a `mermaid.init()` al cambiar de fase |
| **Riesgo** | Dependencia CDN externa. Mitigable cacheando la librería localmente si fuera necesario |

---

## 8. Pendientes antes de implementar

- [ ] Crear issue de implementación y enlazarlo aquí
- [ ] Decidir en qué vista se muestra el diagrama (¿tab en tramitación V3?, ¿modal?, ¿panel lateral?)
- [ ] Prototipar la sintaxis MMD generada para un expediente real de prueba y validar legibilidad
- [ ] Valorar el tamaño máximo del diagrama de detalle (¿solo fase activa o todas?)
- [ ] Decidir si `mermaid.js` se carga desde CDN externo o se incluye en el bundle del proyecto
