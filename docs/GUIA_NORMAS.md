# GUIA_NORMAS — Proceso de trabajo con normativa AT

> **Aplica a:** Proceso de investigación y extracción normativa para el motor de reglas BDDAT.
> **No es fuente de verdad normativa** — para el catálogo de normas ver `docs/NORMATIVA_LEGISLACION_AT.md §6`.
> Contenido migrado desde `NORMATIVA_LEGISLACION_AT.md §3-§5` (sesión 2026-04-04).

---

## Índice

| § | Contenido |
|---|---|
| [§1](#1-qué-extraer-por-tipo-de-solicitud) | Qué extraer — variables y excepciones por tipo de solicitud |
| [§2](#2-formato-de-documentación-de-reglas) | Formato de documentación de reglas — plantilla |
| [§3](#3-resultados-por-iteración) | Resultados por iteración — estado de avance |
| [§4](#4-cola-de-trabajo--normas-pendientes) | Cola de trabajo — pointer a `NORMATIVA_LEGISLACION_AT.md §6` |
| [§5](#5-protocolo-de-extracción) | Protocolo de extracción — skills de localización + pasos al trabajar una norma |
| [§6](#6-diccionario-de-variables-de-contexto) | Diccionario de Variables de Contexto — pointer a `DISEÑO_CONTEXT_ASSEMBLER.md` |

---

## 1. Qué extraer por tipo de solicitud

Para cada tipo de solicitud (AAP, AAC, APO, DUP...):
- Fases obligatorias y su orden
- Fases opcionales o condicionales
- Plazos legales aplicables (días hábiles o naturales)
- Puntos de silencio administrativo positivo/negativo
- Organismos de consulta obligatoria

### Variables que modifican las reglas estándar
- Tensión de la instalación (< 30 kV, 30-132 kV, > 132 kV)
- Tipo de instalación (aérea, subterránea, mixta)
- Clasificación del suelo afectado
- Longitud o potencia (umbrales de cambio de procedimiento)
- Tipo de promotor (distribuidora, generador, consumidor directo)
- Necesidad de EIA: cuándo es obligatoria
- Afectación a espacios protegidos (Red Natura 2000, ZEPA, LIC)
- Instalaciones de generación renovable (régimen especial)

### Excepciones y regímenes especiales
- Instalaciones exentas de alguna fase (DA1ª del Decreto 9/2011)
- Procedimientos abreviados o simplificados
- Régimen especial para generación renovable
- Instalaciones de uso privado vs. uso público
- Pequeñas instalaciones bajo umbrales de simplificación

---

## 2. Formato de documentación de reglas

Para cada regla identificada, documentar:

| Campo | Contenido |
|-------|-----------|
| ID_regla | Identificador único (ej: R-AAP-01) |
| Descripción | Qué dice la regla en lenguaje natural |
| Tipo_solicitud | A qué tipo de solicitud aplica |
| Fase_afectada | Qué fase(s) afecta |
| Condición_activación | Cuándo aplica (siempre / si tensión > X / si suelo urbano...) |
| Excepción_de | Si es excepción, a qué regla estándar contradice |
| Fuente_legal | Norma, artículo y apartado |
| Notas | Observaciones de interpretación |

---

## 3. Resultados por iteración

Los resultados se distribuyen en documentos propios:

| Iteración | Documento | Estado |
|---|---|---|
| **1** — Mapa procedimental | `docs/NORMATIVA_MAPA_PROCEDIMENTAL.md` | En curso |
| **2+4** — Excepciones, regímenes especiales y casos límite | `docs/NORMATIVA_EXCEPCIONES_AT.md` | En curso |
| **3** — Plazos y silencio administrativo | `docs/NORMATIVA_PLAZOS.md §2` | En curso |

### Iteración 3 — Plazos (ver NORMATIVA_PLAZOS.md)
- §1 LPACAP 39/2015 — ✅ completo (sesión 2026-04-01)
- §2.1 LSE 24/2013 — ✅ completo (sesión 2026-04-02)
- §2.2 RD 1955/2000 — ✅ completo (sesión 2026-04-02)
- §2.3+ Resto de normas sectoriales — pendiente (ver §4 de este documento)

---

## 4. Cola de trabajo — normas pendientes

La fuente de verdad de todas las normas aplicables, su estado de extracción, los IDs técnicos (sedeboja, BOE-A) y las observaciones de trabajo está en **`NORMATIVA_LEGISLACION_AT.md §6`**. Esta sección no mantiene lista propia para evitar duplicidades.

Los estados de madurez (`IDENTIFICADA` → `EXTRAÍDA` → `MAPEO_CONTEXTO` → `IMPLEMENTADA`) y su significado también están definidos en `NORMATIVA_LEGISLACION_AT.md §6`.

### Protocolo de adición de norma nueva al catálogo

Cuando se identifica una norma no registrada en §6:
1. Añadir fila en `NORMATIVA_LEGISLACION_AT.md §6` con URL + procedimientos que afecta + `Estado=IDENTIFICADA` + ID técnico (sedeboja o BOE-A).

---

## 5. Protocolo de extracción

### 0. Localizar la norma — uso de skills

Antes de leer cualquier norma seguir este orden para minimizar consumo de contexto:

| Paso | Skill | Cuándo |
|---|---|---|
| 1 | `/legalize <referencia>` | **Siempre primero** — busca en el repo local `D:\legalize-es` |
| 2a | `/boe <referencia>` | Si NOT_FOUND y es **norma estatal** (RD, Ley, RDL estatales) |
| 2b | `/boja <referencia>` | Si NOT_FOUND y es **norma andaluza de rango de Ley** (Ley del Parlamento de Andalucía) → prueba BOE internamente, luego sedeboja |
| 2c | `/boja <referencia>` | Si NOT_FOUND y es **norma BOJA sub-Ley** (Decreto-ley, Decreto, Orden andaluz) → sedeboja directamente |

**Regla crítica:** no llamar a `/boe` ni a `/boja` sin haber recibido `NOT_FOUND` de `/legalize` primero, salvo indicación explícita.

El ID técnico de sedeboja (columna "ID técnico" de `NORMATIVA_LEGISLACION_AT.md §6`) permite construir la URL de ficha directamente sin pasar por búsqueda.

---

Pasos al trabajar una norma de la cola (§4):

1. **Localizar la norma** siguiendo el protocolo de skills del paso 0.
2. Actualizar `NORMATIVA_LEGISLACION_AT.md §6`: cambiar `Estado` de la norma a `EXTRAÍDA`.
3. Si genera fases o procedimientos → añadir en `NORMATIVA_MAPA_PROCEDIMENTAL.md` con `Implicación en BDDAT`.
4. Si genera excepciones → añadir en `NORMATIVA_EXCEPCIONES_AT.md` con `Implicación en BDDAT`.
5. Si genera plazos → añadir en `NORMATIVA_PLAZOS.md §2.x` con plazo + silencio + cómputo.
6. **MAPEO_CONTEXTO:** identificar qué variables necesita el ContextAssembler para evaluar esta norma; actualizar `Estado` en la cola a `MAPEO_CONTEXTO`.
   - **6a. Deduplicación:** antes de añadir cada variable al §6, buscar en la tabla si el concepto ya existe con otro nombre. Riesgo típico: sinónimos (`tiene_X` / `es_X` / `X_obtenida`), generalizaciones (`requiere_eia` vs. `requiere_eia_ordinaria`) o variables que en un contexto son condición de trámite y en otro son hito ya cumplido (`tiene_aap_previa` vs. `hito_aap_obtenida`). Si el concepto ya existe: reutilizar la variable y añadir la nueva norma de origen en la columna correspondiente. Solo crear variable nueva si el concepto es genuinamente distinto.
7. Traducir las "Implicaciones en BDDAT" de los puntos 3 y 4 a filas del mapa de reglas en `DISEÑO_MOTOR_REGLAS.md`.
8. Traducir los plazos del punto 5 al bloque "Constantes sectoriales" de `DISEÑO_FECHAS_PLAZOS.md §5.2`.
9. Actualizar "Última sincronización" en los docs de diseño afectados; cambiar `Estado` en la cola a `IMPLEMENTADA`.

---

## 6. Diccionario de Variables de Contexto

El diccionario de variables vive en **`docs/DISEÑO_CONTEXT_ASSEMBLER.md`**.

Contiene: tabla completa de variables (tipo, naturaleza, norma de origen, estado),
definición de los valores de Naturaleza (`dato`, `calculado`, `derivado_documento`),
definición de los valores de Estado (`definida`, `pendiente de implementar`,
`implementada`, `obsoleta`), y las preguntas de diseño abiertas del ContextAssembler.

Las variables nuevas identificadas en el paso `MAPEO_CONTEXTO` del protocolo (paso 6
de §5) se añaden directamente en ese documento, no aquí.
