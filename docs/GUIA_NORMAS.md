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
| [§4](#4-cola-de-trabajo-unificada) | Cola de trabajo unificada — normas pendientes de extracción |
| [§5](#5-protocolo-de-extracción) | Protocolo de extracción — pasos al trabajar una norma nueva |
| [§6](#6-diccionario-de-variables-de-contexto) | Diccionario de Variables de Contexto — variables del ContextAssembler |

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

## 4. Cola de trabajo unificada

Normas pendientes de extracción o completar. Unificada desde `NORMATIVA_MAPA_PROCEDIMENTAL.md §3` (eliminado), `NORMATIVA_EXCEPCIONES_AT.md §5` (eliminado) y nota de §2 de `NORMATIVA_PLAZOS.md`.

**Estados de madurez:** `IDENTIFICADA` → `EXTRAÍDA` → `MAPEO_CONTEXTO` → `IMPLEMENTADA`
- `IDENTIFICADA`: norma en §6 del catálogo; no se ha leído en profundidad.
- `EXTRAÍDA`: leída y volcada en C (mapa procedimental), D (excepciones) o E (plazos) según corresponde.
- `MAPEO_CONTEXTO`: variables concretas definidas en el Diccionario de Variables (§6 de este doc).
- `IMPLEMENTADA`: variables y reglas en `DISEÑO_MOTOR_REGLAS.md` y/o `DISEÑO_FECHAS_PLAZOS.md`.

| Norma | ID-REF | Ficheros a actualizar | Prioridad | Estado |
|---|---|---|---|---|
| **Modificaciones RD 1955/2000** — cuándo una modificación requiere nueva AAP vs. solo AAC vs. solo AE | REF-RD1955 | C (§2.6) | Alta | MAPEO_CONTEXTO — extraído en sesión 2026-04-04, ver `NORMATIVA_MAPA_PROCEDIMENTAL.md §2.6` |
| **Ley 21/2013 (EIA)** — consultas previas, info pública ambiental, plazos DIA | REF-EIA | C, D, E§2.3+, motor, plazos | Alta | IDENTIFICADA — ⚠️ **Pendiente de revisión previa**: puede haber quedado desactualizada por nueva ley ambiental andaluza. No extraer reglas hasta que el Servicio evalúe el impacto. |
| **RD-ley 23/2020 + RD-ley 8/2023** — hitos administrativos renovables; condicionan admisión a trámite de AAP según punto de acceso/conexión | REF-RDL23-2020 | C, E§2.3 | Media | MAPEO_CONTEXTO — extraído en sesión 2026-04-04, ver `NORMATIVA_MAPA_PROCEDIMENTAL.md §2.7` y `NORMATIVA_PLAZOS.md §2.3` |
| **RD-ley 6/2022 + RD-ley 20/2022** — tramitación conjunta AAP+AAC renovables; afección ambiental simplificada en zonas de baja/moderada sensibilidad | — | C, D | Media | IDENTIFICADA |
| **RD-ley 7/2025** — almacenamiento hibridado: tramitación conjunta, plazos a la mitad, exención EIA si proyecto original ya la tenía; repotenciación: impacto diferencial | REF-RDL7-2025 | C, D | Media | IDENTIFICADA |
| **Ley 4/2025 (Espacios productivos)** — tramitación simplificada renovables en polígonos; acometidas y líneas directas de un solo titular (DA 7ª); líneas directas y redes cerradas (arts. 59-61); almacenamiento hibridado autonómico (DA 12ª) | REF-L4-2025 | C, D | Media | IDENTIFICADA |
| **Decreto-ley 2/2018 (Simplificación energía)** — puede modificar trámites o umbrales del procedimiento estándar en energía y renovables | REF-DL2-2018 | C, D | Media | IDENTIFICADA |
| **Decreto-ley 3/2024 (Simplificación administrativa)** — medidas de simplificación y racionalización; puede afectar trámites generales | REF-DL3-2024 | C, D | Media | IDENTIFICADA |
| **Decreto-ley 4/2024** — modifica el DL 3/2024; revisar alcance conjunto con él | REF-DL4-2024 | C, D | Media | IDENTIFICADA — extraer junto con DL 3/2024 |
| **Art. 95.3 LPACAP** — reutilización de actos y trámites de expediente caducado en nuevo procedimiento | REF-LPACAP | D | Baja | IDENTIFICADA |

### Protocolo de adición de norma nueva al catálogo

Cuando se identifica una norma no registrada en §6:
1. Añadir fila en `NORMATIVA_LEGISLACION_AT.md §6` con URL + procedimientos que afecta + `Estado=IDENTIFICADA`.
2. Añadir fila en la tabla de esta sección con el ID-REF asignado.

---

## 5. Protocolo de extracción

Pasos al trabajar una norma de la cola (§4):

1. Usar `/boe` para leer la norma — BOE: ELI URL del catálogo §6; BOJA: sedeboja URL del catálogo §6 (el `recursoLegalAbstractoId` ya está en la columna ID técnico).
2. Actualizar `NORMATIVA_LEGISLACION_AT.md §6`: cambiar `Estado` de la norma a `EXTRAÍDA`.
3. Si genera fases o procedimientos → añadir en `NORMATIVA_MAPA_PROCEDIMENTAL.md` con `Implicación en BDDAT`.
4. Si genera excepciones → añadir en `NORMATIVA_EXCEPCIONES_AT.md` con `Implicación en BDDAT`.
5. Si genera plazos → añadir en `NORMATIVA_PLAZOS.md §2.x` con plazo + silencio + cómputo.
6. **MAPEO_CONTEXTO:** identificar qué variables necesita el ContextAssembler para evaluar esta norma; añadirlas al Diccionario de Variables (§6 de este doc) si son nuevas; actualizar `Estado` en la cola a `MAPEO_CONTEXTO`.
7. Traducir las "Implicaciones en BDDAT" de los puntos 3 y 4 a filas del mapa de reglas en `DISEÑO_MOTOR_REGLAS.md`.
8. Traducir los plazos del punto 5 al bloque "Constantes sectoriales" de `DISEÑO_FECHAS_PLAZOS.md §5.2`.
9. Actualizar "Última sincronización" en los docs de diseño afectados; cambiar `Estado` en la cola a `IMPLEMENTADA`.

---

## 6. Diccionario de Variables de Contexto

Variables que el ContextAssembler puede pasar al motor de reglas. Crecen en el paso `MAPEO_CONTEXTO` del protocolo de extracción. Antes de tocar código, toda variable nueva se define aquí.

| Variable | Tipo | Norma de origen | Estado |
|---|---|---|---|
| `tension_nominal_kv` | numérico (kV) | Decreto 9/2011 DA 1ª (umbral ≤ 30 kV — tercera categoría AT) | definida |
| `es_linea_subterranea` | boolean | Decreto 9/2011 DA 1ª | definida |
| `es_ct_interior` | boolean | Decreto 9/2011 DA 1ª | definida |
| `es_suelo_urbano_o_urbanizable` | boolean | Decreto 9/2011 DA 1ª | definida |
| `requiere_dup` | boolean | Decreto 9/2011 DA 1ª · DL 26/2021 DF 4ª | definida |
| `requiere_aau` | boolean | DL 26/2021 DF 4ª (Ley 7/2007 GICA) | definida |
| `tiene_aap_previa` | boolean | RD 1955/2000 art. 131 (reducción plazo consultas AAC de 30 a 15 días) | definida |
| `es_instalacion_transporte` | boolean | RD 1955/2000 art. 114 (informe DGPEM obligatorio para transporte CCAA) | definida |
| `requiere_eia` | boolean | Ley 21/2013 (EIA) — cualquier tipo de evaluación ambiental | pendiente de implementar |
| `requiere_eia_ordinaria` | boolean | Art. 115.2 y 115.3 RD 1955/2000 — evaluación ambiental **ordinaria** específicamente (art. 7.1 Ley 21/2013). Más restrictivo que `requiere_eia` (excluye EIA simplificada). Condición de acceso a niveles 2 y 3 del régimen de modificaciones. | definida |
| `es_modificacion_instalacion` | boolean | Art. 115 RD 1955/2000 — la solicitud es una modificación de instalación ya autorizada (no instalación nueva) | definida |
| `modificacion_exceso_potencia_pct` | numérico (%) | Art. 115.2.c RD 1955/2000 — incremento de potencia instalada respecto al proyecto original. Umbral: >15% requiere nueva AAP (instalaciones de generación). | definida |
| `modificacion_variacion_tecnica_pct` | numérico (%) | Art. 115.3.b RD 1955/2000 — variación de características técnicas básicas (potencia, capacidad de transformación/transporte) respecto al original. Umbral: >10% impide nivel 3 (solo AE). | definida |
| `modificacion_cambia_tecnologia` | boolean | Art. 115.2.d RD 1955/2000 — la modificación implica cambio en la tecnología de generación. Impide nivel 2 para generación. | definida |
| `modificacion_dentro_poligonal_o_sin_expropiacion` | boolean | Art. 115.2.b RD 1955/2000 — los terrenos afectados no exceden la poligonal autorizada, o si la exceden no requieren expropiación forzosa y tienen compatibilidad urbanística. Condición de nivel 2 para generación. | definida |
| `modificacion_afecta_otras_instalaciones` | boolean | Art. 115.2.g RD 1955/2000 — las modificaciones producen afecciones sobre otras instalaciones de producción en servicio. Impide nivel 2 para generación. | definida |
| `modificacion_excede_condiciones_aap_dia` | boolean | Art. 115.2.b RD 1955/2000 (transporte/distribución) — los cambios exceden las condiciones establecidas en la AAP concedida y en la DIA. Impide nivel 2 para transporte/distribución. | definida |
| `tiene_punto_acceso_conexion` | boolean | RD-ley 23/2020 art. 1 — permiso de acceso y conexión a red concedido (condición de admisión a trámite AAP renovables) | pendiente de implementar |
| `es_renovable_rdl23` | boolean | RD-ley 23/2020 art. 1 — la instalación es de generación renovable sujeta al régimen de hitos (permiso de acceso posterior al 27/12/2013) | pendiente de implementar |
| `fecha_permiso_acceso` | fecha (ISO 8601) | RD-ley 23/2020 art. 1 — fecha de obtención del permiso de acceso a la red; determina el grupo (A: 28/12/2013–31/12/2017 / B: desde 01/01/2018) y el cómputo de plazos de hitos | pendiente de implementar |
| `rdl23_grupo_permiso_acceso` | enum: `'a'`/`'b'` | RD-ley 23/2020 art. 1 — grupo de plazos aplicable: `'a'` = permiso entre 28/12/2013 y 31/12/2017; `'b'` = permiso desde 01/01/2018 | pendiente de implementar |
| `hito_dia_favorable` | boolean | RD-ley 23/2020 art. 1.1 — DIA favorable obtenida (Hito 2 acreditado ante el gestor de red); para semáforo de prioridad | pendiente de implementar |
