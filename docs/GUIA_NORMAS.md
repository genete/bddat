# GUIA_NORMAS — Proceso de trabajo con normativa AT

> **Aplica a:** Proceso de investigación y extracción normativa para el motor de reglas BDDAT.
> **No es fuente de verdad normativa** — para el catálogo de normas ver `docs/normas_catalog.csv`.
> Contenido migrado desde `NORMATIVA_LEGISLACION_AT.md §3-§5` (sesión 2026-04-04).

---

## Índice

| § | Contenido |
|---|---|
| [§1](#1-qué-extraer-por-tipo-de-solicitud) | Qué extraer — variables y excepciones por tipo de solicitud |
| [§2](#2-formato-de-documentación-de-reglas) | Formato de documentación de reglas — plantilla |
| [§3](#3-resultados-por-iteración) | Resultados por iteración — estado de avance |
| [§4](#4-cola-de-trabajo--normas-pendientes) | Cola de trabajo — pointer a `normas_catalog.csv` |
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

| Iteración | Documento |
|---|---|
| **1** — Mapa procedimental | `docs/NORMATIVA_MAPA_PROCEDIMENTAL.md` |
| **2+4** — Excepciones, regímenes especiales y casos límite | `docs/NORMATIVA_EXCEPCIONES_AT.md` |
| **3** — Plazos y silencio administrativo | `docs/NORMATIVA_PLAZOS.md §2` |

El estado de extracción de cada norma está en `docs/normas_catalog.csv` (columna `estado`).

---

## 4. Cola de trabajo — normas pendientes

La **fuente de verdad estructurada** de todas las normas aplicables —estado de extracción, IDs técnicos (sedeboja, BOE-A), procedimientos afectados y doc_extraccion— está en **`docs/normas_catalog.csv`**. Esta sección no mantiene lista propia para evitar duplicidades.

Los estados de madurez (`IDENTIFICADA` → `EXTRAÍDA` → `MAPEO_CONTEXTO` → `IMPLEMENTADA`) y su significado están definidos en el propio CSV (columna `estado`).

### Protocolo de adición de norma nueva al catálogo

Cuando se identifica una norma no registrada:
1. Añadir fila en `normas_catalog.csv` con: `id_ref`, `nombre_corto`, `ambito`, `procedimientos` (separados por `|`), `estado=IDENTIFICADA`, `id_tecnico` (sedeboja o BOE-A), `url_consolidado`.

---

## 5. Protocolo de extracción

### 0. Localizar la norma — uso de skills

Antes de leer cualquier norma seguir este orden para minimizar consumo de contexto:

| Paso | Herramienta | Cuándo |
|---|---|---|
| 1 | `/legalize <referencia>` | **Siempre primero** — busca en el repo local `D:\legalize-es` |
| 2a | `/boe <referencia>` | Si NOT_FOUND y es **norma estatal** (RD, Ley, RDL estatales) |
| 2b | `python scripts/sedeboja_buscar.py "<nombre>"` | Si NOT_FOUND y es **norma andaluza** y **no** se conoce el `id_tecnico` — localiza el ID sin Playwright |
| 2c | `python scripts/sedeboja_extract.py <id_tecnico>` | Si se conoce el `id_tecnico` (de normas_catalog.csv o del paso 2b) — extrae el texto consolidado directamente, sin Playwright |
| 2d | `/boja <referencia>` | Solo si los scripts fallan o la norma no está en sedeboja (Instrucciones, PDFs directos BOJA) |

> **⚠️ Ahorro de tokens:** los scripts Python (`sedeboja_buscar` y `sedeboja_extract`) no usan Playwright y consumen muy pocos tokens. Usarlos **siempre que la norma esté en sedeboja**. Reservar `/boja` para los casos que no lo estén.

**Regla crítica:** no llamar a `/boe` ni a `/boja` sin haber recibido `NOT_FOUND` de `/legalize` primero, salvo indicación explícita.

El ID técnico de sedeboja (campo `id_tecnico` de `normas_catalog.csv`) permite ir directamente al paso 2c sin búsqueda.

---

Pasos al trabajar una norma de la cola (§4):

1. **Localizar la norma** siguiendo el protocolo de skills del paso 0.
2. Actualizar `normas_catalog.csv`: cambiar campo `estado` a `EXTRAÍDA` y rellenar `doc_extraccion` con los documentos donde se recoge el resultado (separados por `|`).
3. Si genera fases o procedimientos → añadir en `NORMATIVA_MAPA_PROCEDIMENTAL.md` con `Implicación en BDDAT`.
4. Si genera excepciones → añadir en `NORMATIVA_EXCEPCIONES_AT.md` con `Implicación en BDDAT`.
5. Si genera plazos → añadir en `NORMATIVA_PLAZOS.md §2.x` con plazo + silencio + cómputo.
6. **MAPEO_CONTEXTO:** identificar qué variables necesita el ContextAssembler para evaluar esta norma; actualizar `estado` en `normas_catalog.csv` a `MAPEO_CONTEXTO`.
   - **6a. Deduplicación:** antes de añadir cada variable, buscar en `DISEÑO_CONTEXT_ASSEMBLER.md` si el concepto ya existe con otro nombre. Riesgo típico: sinónimos (`tiene_X` / `es_X` / `X_obtenida`), generalizaciones (`requiere_eia` vs. `requiere_eia_ordinaria`) o variables que en un contexto son condición de trámite y en otro son hito ya cumplido (`tiene_aap_previa` vs. `hito_aap_obtenida`). Si el concepto ya existe: reutilizar la variable y añadir la nueva norma de origen en la columna correspondiente. Solo crear variable nueva si el concepto es genuinamente distinto.
7. Traducir las "Implicaciones en BDDAT" de los puntos 3 y 4 a filas del mapa de reglas en `DISEÑO_MOTOR_REGLAS.md`.
8. Traducir los plazos del punto 5 al bloque "Constantes sectoriales" de `DISEÑO_FECHAS_PLAZOS.md §5.2`.
9. Actualizar "Última sincronización" en los docs de diseño afectados; cambiar `estado` en `normas_catalog.csv` a `IMPLEMENTADA`.

---

## 6. Diccionario de Variables de Contexto

El diccionario de variables vive en **`docs/DISEÑO_CONTEXT_ASSEMBLER.md`**.

Contiene: tabla completa de variables (tipo, naturaleza, norma de origen, estado),
definición de los valores de Naturaleza (`dato`, `calculado`, `derivado_documento`),
definición de los valores de Estado (`definida`, `pendiente de implementar`,
`implementada`, `obsoleta`), y las preguntas de diseño abiertas del ContextAssembler.

Las variables nuevas identificadas en el paso `MAPEO_CONTEXTO` del protocolo (paso 6
de §5) se añaden directamente en ese documento, no aquí.
