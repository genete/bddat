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
5. [Serializador Mermaid](#5-serializador-mermaid)
6. [Interacción: frame único con expansión al clic](#6-interacción-frame-único-con-expansión-al-clic)
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
                                         ▼
                             arbol_to_mmd(arbol, fase_expandida_id)
                                         │
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

## 5. Serializador Mermaid

Un único serializador Python, desacoplado de Flask y testable en aislamiento:

```python
def arbol_to_mmd(arbol, fase_expandida_id=None) -> str:
    ...
```

- `fase_expandida_id=None` — vista macro: todas las fases como nodos simples
- `fase_expandida_id=X` — fase X renderizada como subgraph con sus trámites y tareas; el resto de fases siguen visibles como nodos simples

**Tipo de diagrama: `flowchart TD` en ambos casos.** No se necesita `stateDiagram-v2` — el frame único con expansión al clic (§6) hace innecesario mezclar tipos de diagrama.

El serializador aplica `classDef` para colorear nodos según estado (pendiente / en curso / finalizado / finalizado favorable).

---

## 6. Interacción: frame único con expansión al clic

**Decisión:** un solo `<div>` cuyo contenido Mermaid se regenera al interactuar, sin salto de layout ni segunda zona en pantalla.

### Flujo de interacción

```
Carga inicial
  arbol_to_mmd(arbol, fase_expandida_id=None)
  → flowchart TD con todas las fases como nodos simples

Usuario hace clic en FASE X
  → click callback de mermaid.js
  → arbol_to_mmd(arbol, fase_expandida_id=X)  [cliente o llamada al servidor]
  → mermaid.render('diagrama', nuevoMMD)
  → mismo <div> actualizado, contexto preservado

Usuario hace clic en FASE X (ya expandida) u otra fase
  → colapsa o expande según corresponda
```

### Aspecto visual

```
Vista macro (ninguna fase expandida):

  [ANÁLISIS_SOLICITUD]:::finalizada
        ↓
  [CONSULTAS]:::en_curso
        ↓
  [INFORMACIÓN_PÚBLICA]:::pendiente
        ↓
  [RESOLUCIÓN]:::pendiente


Tras clic en CONSULTAS:

  [ANÁLISIS_SOLICITUD]:::finalizada
        ↓
  subgraph CONSULTAS:::en_curso
    subgraph CONSULTA_SEPARATA:::finalizado
      R --> F --> N --> EP --> INC --> A
    end
    subgraph CONSULTA_TRASLADO_TITULAR:::en_curso
      R --> F --> N:::en_curso
    end
  end
        ↓
  [INFORMACIÓN_PÚBLICA]:::pendiente
        ↓
  [RESOLUCIÓN]:::pendiente
```

El contexto del expediente completo (qué fases hay y en qué estado están) permanece visible mientras se examina el detalle de una fase.

### Generación del MMD: ¿cliente o servidor?

Dos opciones válidas; decisión aplazada a implementación:

| Opción | Descripción | Trade-off |
|---|---|---|
| **Servidor** | JS llama a `/api/expedientes/<id>/arbol/mmd?fase_id=X` y recibe el texto MMD | Lógica de serialización centralizada en Python; más fácil de mantener y testear |
| **Cliente** | JS recibe el JSON del árbol en la carga inicial y genera el MMD localmente | Sin round-trip al servidor en cada clic; requiere duplicar la lógica de serialización en JS |

La opción servidor es preferible si la lógica de serialización es no trivial o puede evolucionar. La opción cliente es preferible si la latencia de red es un problema.

---

## 7. Render client-side con mermaid.js

**Decisión:** `mermaid.js` vía CDN, renderizado en el navegador.

| Aspecto | Valoración |
|---|---|
| **Dependencias servidor** | Ninguna — no requiere Node.js ni `mmdc` instalado |
| **Integración** | Un `<script>` CDN y un `<div id="diagrama">` cuyo contenido se actualiza por JS |
| **Regeneración** | `mermaid.render(id, codigoMMD)` devuelve el SVG sin tocar el DOM — se inserta manualmente |
| **Click callbacks** | `click nodoId callbackFn` en la sintaxis MMD — nativo en mermaid.js |
| **Riesgo** | Dependencia CDN externa. Mitigable cacheando la librería localmente si fuera necesario |

---

## 8. Pendientes antes de implementar

- [ ] Crear issue de implementación y enlazarlo aquí
- [ ] Decidir en qué vista se muestra el diagrama (¿tab en tramitación V3?, ¿modal?, ¿panel lateral?)
- [ ] Prototipar la sintaxis MMD generada para un expediente real de prueba y validar legibilidad
- [ ] Decidir generación del MMD en servidor o cliente (ver §6)
- [ ] Decidir si `mermaid.js` se carga desde CDN externo o se incluye en el bundle del proyecto
