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
| **Ley 2/2026, de 12 de marzo (Gestión Ambiental de Andalucía)** — nueva ley marco ambiental autonómica; sustituye (total o parcialmente) la GICA (Ley 7/2007). Impacto amplio: AAU, EIA autonómica, declaración responsable ambiental, comunicación ambiental. Afecta directamente a `requiere_aau`, a las exenciones del DL 26/2021 DF 4ª (que referencia Ley 7/2007) y al Decreto 356/2010 (AAU). **Entrada en vigor: 12/09/2026.** Solo disponible en BOJA (PDF: boja.es/2026/55, web: juntadeandalucia.es/boja/2026/55/1) | REF-L2-2026 | D (§3, §4), variables `requiere_aau` | **Alta** | IDENTIFICADA — ⚠️ **Revisar antes de 12/09/2026**: entrará en vigor en esa fecha y puede dejar obsoletas las referencias a Ley 7/2007 GICA en todo el catálogo normativo y en `NORMATIVA_EXCEPCIONES_AT.md §4`. |
| **Ley 21/2013 (EIA)** — consultas previas, info pública ambiental, plazos DIA | REF-EIA | C, D, E§2.3+, motor, plazos | Alta | IDENTIFICADA — ⚠️ **Pendiente de revisión previa**: puede haber quedado desactualizada por nueva ley ambiental andaluza (Ley 2/2026). No extraer reglas hasta que el Servicio evalúe el impacto. |
| **RD-ley 23/2020 + RD-ley 8/2023** — hitos administrativos renovables; condicionan admisión a trámite de AAP según punto de acceso/conexión | REF-RDL23-2020 | C, E§2.3 | Media | MAPEO_CONTEXTO — extraído en sesión 2026-04-04, ver `NORMATIVA_MAPA_PROCEDIMENTAL.md §2.7` y `NORMATIVA_PLAZOS.md §2.3` |
| **RD-ley 6/2022 + RD-ley 20/2022** — tramitación conjunta AAP+AAC renovables; afección ambiental simplificada en zonas de baja/moderada sensibilidad | REF-RDL6-2022 · REF-RDL20-2022 | D, E§2.4 | Media | MAPEO_CONTEXTO — extraído en sesión 2026-04-04, ver `NORMATIVA_EXCEPCIONES_AT.md §5` y `§6`. ⚠️ Tramitación conjunta (arts. 7/23) solo aplica a proyectos **competencia AGE**; el art. 6/22 (afección ambiental) sí puede aplicarlo la CCAA. Plazos añadidos en `NORMATIVA_PLAZOS.md §2.4` (sesión 2026-04-04). |
| **RD 1183/2020** — acceso y conexión; DF 3ª: nueva definición potencia instalada FV = min(DC módulos, AC inversores); DA 1ª: sistema de control si potencia total > capacidad de acceso; régimen de hitos y concursos | REF-RD1183 | C§2.7 (complemento), E§5/§6 (nota competencia), E§2.3 (plazos acceso) | Media | MAPEO_CONTEXTO — extraído en sesión 2026-04-04, ver `NORMATIVA_MAPA_PROCEDIMENTAL.md §2.8`. DA 1ª y DF 3ª documentadas; concursos de acceso resumidos. |
| **RD-ley 7/2025** — **DEROGADO ÍNTEGRAMENTE** por el Congreso el 22/07/2025 (BOE-A-2025-15313, no convalidado). Arts. 9 (almacenamiento hibridado AGE), 10 (nueva def. potencia instalada híbrida) y 29 (repotenciación) ya no están en vigor. El catálogo lo reflejaba como "derogado parcialmente" — era derogación total. | REF-RDL7-2025 | — | — | OBSOLETA — norma derogada; no extraer reglas. Verificar si algún contenido fue incorporado por norma posterior (RDL 7/2026, BOE-A-2026-6544). |
| **RD 997/2025** — no localizado en el BOE. El identificador puede ser incorrecto o la norma puede no existir bajo ese nombre. Las modificaciones de RD 1183/2020 que se atribuían a esta norma provienen de RDL 7/2026 (BOE-A-2026-6544, marzo 2026). | REF-RDL7-2025 | — | — | IDENTIFICADA — ⚠️ **Verificar existencia real**: buscar en BOE si existe RD 997/2025 con ese número exacto. Si no existe, eliminar esta fila. |
| **RDL 7/2026 (BOE-A-2026-6544)** — modificó RD 1183/2020 arts. 20 ter, 20 quater y 20 quinquies (concursos de acceso de demanda). Vigente desde 22/03/2026. **Norma nueva no catalogada aún.** | — | C§2.8 (complemento) | Baja | IDENTIFICADA — añadir al catálogo §6; revisar alcance completo. |
| **Resolución CNMC 27/06/2024 + Circulares CNMC** — especificaciones de detalle para capacidad de acceso de generación; metodología acceso/conexión. Las Circulares CNMC son fuente normativa adicional (acceso, peajes, conexión). Pendiente catalogar cuáles aplican al ámbito BDDAT | REF-CNMC-2024 | C§2.7 (complemento) | Baja | IDENTIFICADA |
| **Ley 4/2025 (Espacios productivos)** — tramitación simplificada renovables en polígonos; acometidas y líneas directas de un solo titular (DA 7ª); líneas directas y redes cerradas (arts. 59-61); almacenamiento hibridado autonómico (DA 12ª) | REF-L4-2025 | C, D | Media | IDENTIFICADA |
| **Decreto-ley 2/2018 (Simplificación energía)** — DA única: cauce RD 1955/2000 para FV; ≤500 kW → puesta en servicio; anti-fraccionamiento 3.000 m/ref. catastral; DR consultas; incidencia territorial LISTA (apdo. 4 añadido por DL 3/2024). No toca Decreto 9/2011. | REF-DL2-2018 | D§7 ✅ | Media | MAPEO_CONTEXTO — extraído sesión 2026-04-04, ver `NORMATIVA_EXCEPCIONES_AT.md §7`. Variables nuevas: `tiene_linea_evacuacion_comun`, `suma_potencia_grupo_evacuacion_kw`, `misma_referencia_catastral_grupo`, `distancia_minima_instalaciones_grupo_m`, `promotor_presento_dr_consultas`, `requiere_informe_incidencia_territorial`, `promotor_aporto_doc_incidencia_territorial`. Pendiente: trasladar a motor (paso 7). |
| **Ley 7/2021 LISTA + Decreto 550/2022 (Reglamento General)** — **arts. 71-72 Reglamento**: supuestos de informe de incidencia territorial para instalaciones energéticas; necesario para completar la lógica de `requiere_informe_incidencia_territorial` | — | D§7.5 (complemento) | Media | IDENTIFICADA — añadidos al catálogo §6.1 sesión 2026-04-04. Pendiente leer arts. 71-72 Reglamento LISTA. |
| **Decreto-ley 3/2024 (Simplificación administrativa)** — medidas de simplificación y racionalización; puede afectar trámites generales. **Art. 260:** modifica DA única DL 2/2018 (apdo. 4 incidencia territorial) — ya documentado en `NORMATIVA_EXCEPCIONES_AT.md §7.5`. | REF-DL3-2024 | C, D | Media | IDENTIFICADA — art. 260 ya recogido vía DL 2/2018. Pendiente revisar alcance completo del resto del articulado. |
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
6. **MAPEO_CONTEXTO:** identificar qué variables necesita el ContextAssembler para evaluar esta norma; actualizar `Estado` en la cola a `MAPEO_CONTEXTO`.
   - **6a. Deduplicación:** antes de añadir cada variable al §6, buscar en la tabla si el concepto ya existe con otro nombre. Riesgo típico: sinónimos (`tiene_X` / `es_X` / `X_obtenida`), generalizaciones (`requiere_eia` vs. `requiere_eia_ordinaria`) o variables que en un contexto son condición de trámite y en otro son hito ya cumplido (`tiene_aap_previa` vs. `hito_aap_obtenida`). Si el concepto ya existe: reutilizar la variable y añadir la nueva norma de origen en la columna correspondiente. Solo crear variable nueva si el concepto es genuinamente distinto.
7. Traducir las "Implicaciones en BDDAT" de los puntos 3 y 4 a filas del mapa de reglas en `DISEÑO_MOTOR_REGLAS.md`.
8. Traducir los plazos del punto 5 al bloque "Constantes sectoriales" de `DISEÑO_FECHAS_PLAZOS.md §5.2`.
9. Actualizar "Última sincronización" en los docs de diseño afectados; cambiar `Estado` en la cola a `IMPLEMENTADA`.

---

## 6. Diccionario de Variables de Contexto

Variables que el ContextAssembler puede pasar al motor de reglas. Crecen en el paso `MAPEO_CONTEXTO` del protocolo de extracción. Antes de tocar código, toda variable nueva se define aquí.

**Columna Naturaleza — valores y significado:**

| Valor | Significado | Dónde vive | Caché en BD |
|---|---|---|---|
| `dato` | Valor introducido por un humano o aportado en un documento externo. No se calcula. | Campo de `Expediente`, `Proyecto` o `Solicitud` | Sí — es el dato de origen |
| `derivado_documento` | Verdadero si existe (y está vigente) un documento de un tipo concreto asociado al expediente. | Consulta sobre la tabla de documentos; no como campo propio | No — recalcular siempre; el documento puede añadirse o anularse |
| `calculado` | Se obtiene aplicando una función sobre otros datos del sistema. Puede cambiar sin intervención humana directa. | Servicio/propiedad computada; **nunca campo de trámite ni de fase** | No salvo decisión explícita documentada; riesgo de quedar desactualizado |

> **Regla de implementación para variables `calculado` y `derivado_documento`:** el ContextAssembler debe construirlas frescas en cada invocación. No persistir el resultado en BD salvo que exista una decisión de diseño deliberada y documentada que justifique el caché y defina cuándo se invalida.

**Columna Estado — valores y significado:**

| Valor | Significado |
|---|---|
| `definida` | Variable nombrada, tipada y con norma de origen registrada. Puede o no estar en código. |
| `pendiente de implementar` | Definida aquí pero aún no existe en modelo, ContextAssembler ni motor. |
| `implementada` | Existe en el modelo de BD (si es `dato`), o en el ContextAssembler (si es `calculado`/`derivado_documento`), y el motor la evalúa. |
| `obsoleta` | Ya no aplica (norma derogada, diseño cambiado). Mantener fila para trazabilidad; no borrar. |

> Mantener este campo actualizado es tan importante como la propia definición: es el **inventario de cobertura real del motor**. Cuando una variable pasa a `implementada`, significa que la regla jurídica asociada está activa en producción.

| Variable | Tipo | Naturaleza | Norma de origen y descripción | Estado |
|---|---|---|---|---|
| `tension_nominal_kv` | numérico (kV) | `dato` · Proyecto | Decreto 9/2011 DA 1ª — umbral ≤ 30 kV define tercera categoría AT | definida |
| `es_linea_subterranea` | boolean | `dato` · Proyecto | Decreto 9/2011 DA 1ª | definida |
| `es_ct_interior` | boolean | `dato` · Proyecto | Decreto 9/2011 DA 1ª | definida |
| `es_suelo_urbano_o_urbanizable` | boolean | `dato` · Proyecto | Decreto 9/2011 DA 1ª — clasificación urbanística de los terrenos afectados | definida |
| `requiere_dup` | boolean | `dato` · Solicitud | Decreto 9/2011 DA 1ª · DL 26/2021 DF 4ª — el promotor solicita declaración de utilidad pública | definida |
| `requiere_aau` | boolean | `dato` · Solicitud | DL 26/2021 DF 4ª (Ley 7/2007 GICA) — la instalación requiere autorización ambiental unificada | definida |
| `es_instalacion_transporte` | boolean | `dato` · Proyecto | RD 1955/2000 art. 114 — instalación de transporte tramitada por CCAA; condiciona el informe DGPEM | definida |
| `es_modificacion_instalacion` | boolean | `dato` · Solicitud | Art. 115 RD 1955/2000 — la solicitud es una modificación de instalación ya autorizada (no instalación nueva) | definida |
| `modificacion_cambia_tecnologia` | boolean | `dato` · Proyecto | Art. 115.2.d RD 1955/2000 — la modificación implica cambio en la tecnología de generación; impide nivel 2 | definida |
| `modificacion_dentro_poligonal_o_sin_expropiacion` | boolean | `dato` · Proyecto | Art. 115.2.b RD 1955/2000 — terrenos afectados no exceden la poligonal autorizada, o si la exceden: sin expropiación forzosa y con compatibilidad urbanística; condición de nivel 2 para generación | definida |
| `modificacion_afecta_otras_instalaciones` | boolean | `dato` · Proyecto | Art. 115.2.g RD 1955/2000 — las modificaciones producen afecciones sobre otras instalaciones de producción en servicio; impide nivel 2 para generación | definida |
| `fecha_permiso_acceso` | fecha (ISO 8601) | `dato` · Expediente | RD-ley 23/2020 art. 1 — fecha de obtención del permiso de acceso a la red, aportada por el promotor | pendiente de implementar |
| `tiene_punto_acceso_conexion` | boolean | `derivado_documento` · Expediente | RD-ley 23/2020 art. 1 — existe documento de tipo PERMISO_ACCESO_CONEXION vigente en el expediente; condición de admisión a trámite de AAP renovables | pendiente de implementar |
| `hito_dia_favorable` | boolean | `derivado_documento` · Expediente | RD-ley 23/2020 art. 1.1 — existe documento de tipo DIA con resultado favorable asociado al expediente (Hito 2); para semáforo de prioridad | pendiente de implementar |
| `tiene_aap_previa` | boolean | `derivado_documento` · Expediente | RD 1955/2000 art. 131 — existe resolución de AAP favorable vinculada a este proyecto en BDDAT; reduce plazo de consultas AAC de 30 a 15 días. **Nota:** no leer el estado de la fase AAP — consultar la existencia del documento de resolución | definida |
| `requiere_eia` | boolean | `calculado` | Ley 21/2013 — cualquier tipo de evaluación ambiental; deriva de características del proyecto según anexos de la Ley 21/2013 | pendiente de implementar |
| `requiere_eia_ordinaria` | boolean | `calculado` | Art. 115.2 y 115.3 RD 1955/2000 — evaluación ambiental **ordinaria** (art. 7.1 Ley 21/2013); más restrictivo que `requiere_eia` (excluye EIA simplificada); condición de acceso a niveles 2 y 3 del régimen de modificaciones | definida |
| `modificacion_exceso_potencia_pct` | numérico (%) | `calculado` | Art. 115.2.c RD 1955/2000 — deriva de: (potencia_propuesta − potencia_original) / potencia_original × 100; umbral >15% impide nivel 2 en generación | definida |
| `modificacion_variacion_tecnica_pct` | numérico (%) | `calculado` | Art. 115.3.b RD 1955/2000 — variación de características técnicas básicas (potencia, capacidad de transformación/transporte) respecto al original; umbral >10% impide nivel 3 | definida |
| `modificacion_excede_condiciones_aap_dia` | boolean | `calculado` | Art. 115.2.b RD 1955/2000 (transporte/distribución) — deriva de comparar el proyecto modificado con las condiciones establecidas en la AAP concedida y en la DIA; impide nivel 2 | definida |
| `es_renovable_rdl23` | boolean | `calculado` | RD-ley 23/2020 art. 1 — deriva de: tipo de instalación = generación renovable AND `fecha_permiso_acceso` > 27/12/2013 | pendiente de implementar |
| `rdl23_grupo_permiso_acceso` | enum: `'a'`/`'b'` | `calculado` | RD-ley 23/2020 art. 1 — deriva de `fecha_permiso_acceso`: `'a'` si entre 28/12/2013 y 31/12/2017; `'b'` si desde 01/01/2018 | pendiente de implementar |
| `es_instalacion_generacion_renovable` | boolean | `dato` · Proyecto | RD-ley 6/2022 art. 6 · RD-ley 20/2022 art. 22 — la instalación es de generación eléctrica a partir de fuentes renovables (eólica, fotovoltaica, hidráulica, biomasa…). **Deduplicación:** `es_renovable_rdl23` es `calculado` y requiere también `fecha_permiso_acceso`; este campo es el `dato` de origen que lo alimenta. | pendiente de implementar |
| `tipo_fuente_renovable` | enum: `'eolica'`/`'fotovoltaica'`/`'otras'` | `dato` · Proyecto | RD-ley 6/2022 art. 6 — necesario para aplicar los umbrales de potencia diferenciados (eólica ≤75 MW, fotovoltaica ≤150 MW). Solo relevante cuando `es_instalacion_generacion_renovable = true`. El art. 22 RDL 20/2022 no tiene umbrales, pero el campo es útil para ambas normas. | pendiente de implementar |
| `potencia_instalada_mw` | numérico (MW) | `dato` · Proyecto | RD-ley 6/2022 art. 6 · LSE art. 3.13.a · **DL 2/2018 DA única apdo. 2** — potencia instalada total del proyecto en MW. Umbrales: RDL6/2022 eólica ≤ 75 MW / fotovoltaica ≤ 150 MW; competencia AGE > 50 MW; **DL 2/2018: ≤ 0,5 MW (500 kW) → puesta en servicio en lugar de AE (producción)**. **FV:** desde RD 1183/2020 DF 3ª, `potencia instalada = min(Σ Wp módulos DC en STC, Σ W inversores AC)` — sustituye a la antigua «potencia pico». **Deduplicación:** distinto de `tension_nominal_kv` y de `modificacion_exceso_potencia_pct`. | pendiente de implementar |
| `ubicacion_red_natura_2000` | boolean | `dato` · Proyecto | RD-ley 6/2022 art. 6.1.c · RD-ley 20/2022 art. 22.1.1º — el proyecto está ubicado (total o parcialmente) en superficie integrante de la Red Natura 2000; excluye de ambos procedimientos de afección ambiental simplificada. **Deduplicación:** ninguna variable existente recoge esta condición geográfica (distinto de `es_suelo_urbano_o_urbanizable`). | pendiente de implementar |
| `ubicacion_espacio_natural_protegido` | boolean | `dato` · Proyecto | RD-ley 20/2022 art. 22.1.2º — el proyecto está en un espacio natural protegido (art. 28 Ley 42/2007 del Patrimonio Natural y de la Biodiversidad); excluye del procedimiento ampliado del art. 22. **No** es exclusión bajo el art. 6 del RDL 6/2022 (ese solo excluye Red Natura 2000). | pendiente de implementar |
| `zona_sensibilidad_ambiental_miteco` | enum: `'baja'`/`'alta_o_moderada'`/`'no_determinada'` | `dato` · Proyecto | RD-ley 6/2022 art. 6.1.c — clasificación según la herramienta MITECO "Zonificación ambiental para la implantación de energías renovables". Condición de activación del art. 6: el proyecto debe estar **íntegramente** en zona `'baja'`. **No requerida** bajo el art. 22 RDL 20/2022 (sin restricción de zona). Se aplica solo si `es_instalacion_generacion_renovable = true`. | pendiente de implementar |
| `tiene_informe_afeccion_ambiental_favorable` | boolean | `derivado_documento` · Expediente | RD-ley 6/2022 art. 6 · RD-ley 20/2022 art. 22 — existe documento de tipo INFORME_AFECCION_AMBIENTAL con resultado favorable asociado al expediente; habilita el procedimiento simplificado (art. 7/23) y reemplaza el track de EIA ordinaria. **Deduplicación:** distinto de `hito_dia_favorable` — la DIA es el instrumento de la EIA ordinaria; el informe de afección ambiental es el instrumento alternativo. No usar `requiere_eia` como proxy: ese indica si hay EIA; este indica que ya se determinó que no la hay. | pendiente de implementar |
| `es_infraestructura_recarga_ve` | boolean | `dato` · Proyecto | LSE art. 53.1 — la instalación es infraestructura eléctrica (acceso/extensión de red, CT, seccionamiento) asociada a una estación de recarga de vehículos eléctricos. Solo relevante conjuntamente con `potencia_recarga_ve_kw`. | pendiente de implementar |
| `potencia_recarga_ve_kw` | numérico (kW) | `dato` · Proyecto | LSE art. 53.1 — potencia de la estación de recarga VE. Solo relevante si `es_infraestructura_recarga_ve = true`. Umbral: ≤ 3.000 kW → exenta del régimen de autorizaciones del art. 53 (AAP, AAC, AE); > 3.000 kW → procedimiento estándar. | pendiente de implementar |
| `tiene_linea_evacuacion_comun` | boolean | `dato` · Proyecto | DL 2/2018 DA única apdo. 2 — la instalación de producción comparte línea de evacuación con otras instalaciones del mismo promotor o bajo el mismo punto de interconexión. Condición de entrada para el cálculo del anti-fraccionamiento. | pendiente de implementar |
| `suma_potencia_grupo_evacuacion_kw` | numérico (kW) | `calculado` | DL 2/2018 DA única apdo. 2 — suma de potencias instaladas de todas las instalaciones que comparten la línea de evacuación común. Solo se calcula si `tiene_linea_evacuacion_comun = true`. Umbral: > 500 kW activa el análisis de anti-fraccionamiento. | pendiente de implementar |
| `misma_referencia_catastral_grupo` | boolean | `dato` · Proyecto | DL 2/2018 DA única apdo. 2.a — alguna instalación del grupo de evacuación comparte referencia catastral con otra del mismo grupo. Sub-condición del anti-fraccionamiento. | pendiente de implementar |
| `distancia_minima_instalaciones_grupo_m` | numérico (m) | `dato` · Proyecto | DL 2/2018 DA única apdo. 2.b — distancia mínima entre cualquier par de instalaciones del grupo de evacuación. Sub-condición del anti-fraccionamiento. Umbral: < 3.000 m activa el régimen completo. Solo relevante si `misma_referencia_catastral_grupo = false`. | pendiente de implementar |
| `promotor_presento_dr_consultas` | boolean | `derivado_documento` · Expediente | DL 2/2018 DA única apdo. 3 — existe documento de tipo DR_CONSULTAS_PREVIAS presentado por el promotor junto a la solicitud de AAP o AAC. Si es `true`, el órgano solo envía separatas a los organismos no cubiertos por la DR. | pendiente de implementar |
| `requiere_informe_incidencia_territorial` | boolean | `calculado` | DL 2/2018 DA única apdo. 4 (añadido por DL 3/2024) — el promotor ha concluido (y declarado) que el proyecto cae en algún supuesto del art. 71 Reglamento LISTA (Decreto 550/2022). Si `true` → debe aportarse documentación art. 72 LISTA; si `false` → DR de no-incidencia. Deriva del análisis del promotor; el motor registra el resultado. Pendiente de revisar art. 71 Reglamento LISTA para completar la lógica de cálculo. | pendiente de implementar |
| `promotor_aporto_doc_incidencia_territorial` | boolean | `derivado_documento` · Expediente | DL 2/2018 DA única apdo. 4 (añadido por DL 3/2024) — existe documento de tipo DR_NO_INCIDENCIA_TERRITORIAL o INFORME_INCIDENCIA_TERRITORIAL asociado a la solicitud. Requisito previo a considerar la solicitud completa. | pendiente de implementar |
