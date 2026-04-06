# ContextAssembler — Diseño del contrato de variables

> **Fecha:** 2026-04-05
> **Estado:** En construcción — diccionario de variables activo; diseño de implementación pendiente.
> **Referencia de arquitectura:** `DISEÑO_MOTOR_AGNOSTICO.md`

Este documento define el contrato de entrada del ContextAssembler: qué variables
existen, cómo se tipan, de qué norma proceden y cuál es su estado de implementación.

El ContextAssembler es la capa de BDDAT que, dado un evento + entidad, sube el árbol
ESFTT, computa todas las variables necesarias y las pasa al motor agnóstico como dict
plano. Sí conoce BDDAT a fondo; el motor no.

Ver `DISEÑO_MOTOR_AGNOSTICO.md` para la decisión arquitectural de separar motor de
dominio, los problemas que resuelve y las advertencias de riesgo del refactor.

---

## Relación con las tablas del Supervisor

La cadena de evaluación es:

```
BDDAT → ContextAssembler → dict de variables → Motor → reglas_motor/condiciones_regla → EvaluacionResult
```

Las tablas editables por el Supervisor (`reglas_motor` + `condiciones_regla`) viven
**después** del ContextAssembler. El Supervisor nunca configura la lógica de cómputo
de variables — eso es código Python. Lo que edita son las reglas que evalúan el
resultado de ese cómputo.

**Trampa a evitar:** una condición en `condiciones_regla` que referencia una variable
que el ContextAssembler no computa falla silenciosamente — variable ausente del dict
equivale a condición que nunca se evalúa correctamente.

**Solución de contrato:** el diccionario de variables de este documento es el catálogo
oficial. La UI del Supervisor solo debe permitir seleccionar variables mediante
dropdown/autocomplete sobre este catálogo — nunca texto libre. Si la variable
necesaria no está en el catálogo, es señal de que falta trabajo previo:

1. Definir la variable en este diccionario (tipo, naturaleza, norma de origen)
2. Implementarla en el ContextAssembler (código Python)
3. Solo entonces estará disponible en el formulario del Supervisor

Variable nueva ≠ regla nueva. Son dos pasos distintos con responsables distintos.

---

## Preguntas de diseño abiertas

Estas preguntas bloquean la implementación; deben cerrarse antes de codificar el
ContextAssembler:

- ¿Qué variables computa para cada `(accion, tipo)`? ¿Hardcoded o configurable en BD?
- El Supervisor debe poder editar acciones, variables y condiciones → equilibrar
  flexibilidad con no hacer todo personalizable.
- Variables derivadas (`intermunicipal`, `plazo_vencido`, `tiene_fase_X_cerrada`)
  requieren queries específicas — ¿cómo se declaran sin hardcodearlas?
- Si el contrato es configurable, el Supervisor necesita UI para declarar variables nuevas.

---

## Columna Naturaleza — valores y significado

| Valor | Significado | Dónde vive | Caché en BD |
|---|---|---|---|
| `dato` | Valor introducido por un humano o aportado en un documento externo. No se calcula. | Campo de `Expediente`, `Proyecto` o `Solicitud` | Sí — es el dato de origen |
| `derivado_documento` | Verdadero si existe (y está vigente) un documento de un tipo concreto asociado al expediente. | Consulta sobre la tabla de documentos; no como campo propio | No — recalcular siempre; el documento puede añadirse o anularse |
| `calculado` | Se obtiene aplicando una función sobre otros datos del sistema. Puede cambiar sin intervención humana directa. | Servicio/propiedad computada; **nunca campo de trámite ni de fase** | No salvo decisión explícita documentada; riesgo de quedar desactualizado |

> **Regla de implementación para variables `calculado` y `derivado_documento`:** el ContextAssembler debe construirlas frescas en cada invocación. No persistir el resultado en BD salvo que exista una decisión de diseño deliberada y documentada que justifique el caché y defina cuándo se invalida.

---

## Columna Estado — valores y significado

| Valor | Significado |
|---|---|
| `definida` | Variable nombrada, tipada y con norma de origen registrada. Puede o no estar en código. |
| `pendiente de implementar` | Definida aquí pero aún no existe en modelo, ContextAssembler ni motor. |
| `implementada` | Existe en el modelo de BD (si es `dato`), o en el ContextAssembler (si es `calculado`/`derivado_documento`), y el motor la evalúa. |
| `obsoleta` | Ya no aplica (norma derogada, diseño cambiado). Mantener fila para trazabilidad; no borrar. |

> Mantener este campo actualizado es tan importante como la propia definición: es el
> **inventario de cobertura real del motor**. Cuando una variable pasa a `implementada`,
> significa que la regla jurídica asociada está activa en producción.

---

## Diccionario de variables

Las variables crecen en el paso `MAPEO_CONTEXTO` del protocolo de extracción
(`GUIA_NORMAS.md §5`). Antes de tocar código, toda variable nueva se define aquí.

| Variable | Tipo | Naturaleza | Norma de origen y descripción | Estado |
|---|---|---|---|---|
| `tension_nominal_kv` | numérico (kV) | `dato` · Proyecto | Decreto 9/2011 DA 1ª — umbral ≤ 30 kV define tercera categoría AT · **RD 337/2014 ITC-RAT 22 §4** — umbral > 30 kV activa inspección inicial obligatoria por Organismo de Control para instalaciones no-PTD | definida |
| `es_linea_subterranea` | boolean | `dato` · Proyecto | Decreto 9/2011 DA 1ª | definida |
| `es_ct_interior` | boolean | `dato` · Proyecto | Decreto 9/2011 DA 1ª | definida |
| `es_suelo_urbano_o_urbanizable` | boolean | `dato` · Proyecto | Decreto 9/2011 DA 1ª — clasificación urbanística de los terrenos afectados | definida |
| `requiere_dup` | boolean | `dato` · Solicitud | Decreto 9/2011 DA 1ª · DL 26/2021 DF 4ª — el promotor solicita declaración de utilidad pública | definida |
| `requiere_aau` | boolean | `dato` · Solicitud | DL 26/2021 DF 4ª (Ley 7/2007 GICA) · **Ley 2/2026 art. 67** — la instalación requiere autorización ambiental unificada | definida |
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
| `longitud_km` | numérico (km) | `dato` · Proyecto | Ley 21/2013 Anexo I Grupo 3g / Anexo II Grupo 4b — longitud total de la línea eléctrica; umbrales: > 15 km (EIA ordinaria), > 3 km (EIA simplificada) | pendiente de implementar |
| `clasificacion_suelo_lista` | enum: `'urbano'`/`'urbanizable'`/`'rustico'` | `dato` · Proyecto | Ley 7/2021 (LISTA) arts. 21-23 — clasificación urbanística del suelo según la Ley de Impulso para la Sostenibilidad del Territorio de Andalucía. Determina: (1) escape de Licencia Ambiental: `= 'urbano'` + `discurre_integra_subterranea = true` (Ley 2/2026 Anexo I Cat.3); (2) escape de umbrales EIA 21/2013: probable equivalencia `'urbano'` ≈ "suelo urbanizado" TRLSRU — **pendiente verificación jurídica**; (3) condición Decreto 9/2011 DA 1ª: `IN ('urbano', 'urbanizable')`. **Deduplicación:** supersede `es_suelo_urbano_o_urbanizable` (l.100), que mezcla urbano+urbanizable en un boolean sin distinción — ese campo queda pendiente de eliminar/unificar una vez implementado este. | pendiente de implementar |
| `discurre_integra_subterranea` | boolean | `dato` · Proyecto | Ley 21/2013 Anexo I Grupo 3g / Anexo II Grupo 4b / Ley 2/2026 Anexo I Cat.3 — la línea discurre íntegramente en subterráneo en toda su longitud. Combinado con `clasificacion_suelo_lista` determina el escape de los umbrales EIA (Ley 21/2013) y de la Licencia Ambiental (Ley 2/2026). **Deduplicación:** distinto de `es_linea_subterranea` (ese no captura "íntegramente"; una línea puede ser parcialmente subterránea). **Redesign:** reemplaza la variable `discurre_integra_subterranea_suelo_urbanizado` que combinaba dos condiciones separables (condición geométrica + clasificación urbanística) en un solo boolean — la separación permite aplicar las distintas normas con precisión. | pendiente de implementar |
| `puede_afectar_red_natura_2000` | boolean | `dato` · Proyecto | Ley 21/2013 art. 7.2.b — el proyecto puede afectar de forma apreciable, directa o indirectamente, a Espacios Protegidos Red Natura 2000 aunque no esté ubicado dentro del perímetro; activa EIA simplificada para proyectos fuera de Anexo I y II. **Deduplicación:** distinto de `ubicacion_red_natura_2000` (ese = dentro del perímetro, criterio 1 Anexo II); este = afectación apreciable desde exterior | pendiente de implementar |
| `requiere_eia_simplificada` | boolean | `calculado` | Ley 21/2013 art. 7.2 — EIA simplificada (IIA); deriva de: proyecto en Anexo II (Grupo 4b ≥15 kV y >3 km, o criterios generales 1/2, o sin RD 1432/2008, o <200 m población) O art. 7.2.b (afectación apreciable Red Natura sin estar en Anexos). **Deduplicación:** más específico que `requiere_eia` (excluye EIA ordinaria); complementario a `requiere_eia_ordinaria` | pendiente de implementar |
| `hito_iia_obtenido` | boolean | `derivado_documento` · Expediente | Ley 21/2013 art. 47 / Ley 2/2026 art. 50 — existe documento de tipo IIA (informe de impacto ambiental) con resultado favorable; desbloqueante de AAUS. **Deduplicación:** distinto de `hito_dia_favorable` (ese = DIA para EIA ordinaria) | pendiente de implementar |
| `requiere_aaus` | boolean | `calculado` | Ley 2/2026 art. 79 + Ley 21/2013 Anexo II — la instalación requiere AAUS (Autorización Ambiental Unificada Simplificada); se activa cuando `requiere_eia_simplificada = true` Y competencia ambiental autonómica. **Deduplicación:** distinto de `requiere_aau` (ese = EIA ordinaria / AAU) | pendiente de implementar |
| `competencia_ambiental_estatal` | boolean | `dato` · Solicitud | Ley 2/2026 arts. 67.3 y 79.3 — la evaluación ambiental del proyecto es de competencia estatal (instalaciones red de transporte, REE); excluye de AAU y AAUS autonómica; el promotor debe obtener pronunciamiento ambiental del MITECO | pendiente de implementar |
| `declarada_utilidad_interes_general` | boolean | `dato` · Solicitud | Ley 2/2026 arts. 67.4 y 79.4 — la actuación ha sido declarada de utilidad e interés general (distinto de DUP energética — las instalaciones de distribución y transporte ya son de interés general per se); cuando true, AAU/AAUS se resuelve por informe vinculante en lugar de resolución de autorización. ⚠️ Pendiente de revisar: casos muy raros en BDDAT (instalaciones promovidas por la propia Administración para uso propio) | pendiente de revisar |
| `fecha_inicio_expediente_ambiental` | date (ISO 8601) | `dato` · Expediente | Ley 2/2026 DT 1ª — fecha de inicio del procedimiento de instrumento de prevención ambiental (AAU/AAUS/CA); si < 20/06/2026 → tramitación por GICA + Decreto 356/2010; si ≥ 20/06/2026 → Ley 2/2026 | pendiente de implementar |
| `hito_aau_obtenida` | boolean | `derivado_documento` · Expediente | Ley 2/2026 art. 67 / GICA art. 31 — existe resolución de AAU (o informe vinculante equivalente si declarada_utilidad_interes_general) favorable; desbloqueante de la AAP cuando requiere_aau = true | pendiente de implementar |
| `hito_aaus_obtenida` | boolean | `derivado_documento` · Expediente | Ley 2/2026 art. 79 — existe resolución de AAUS favorable; desbloqueante de la AAP cuando requiere_aaus = true | pendiente de implementar |
| `requiere_licencia_ambiental` | boolean | `calculado` | Ley 2/2026 Anexo I Categoría 3 — la instalación requiere Licencia Ambiental municipal; se activa cuando la línea cumple los umbrales de Cat.3 (T≥15kV aérea 1-3km; T<15kV aérea >1km; T<15kV subterránea >3km en suelo rústico) **y NO** se activan los criterios\* EIA (si se activan → AAUS, no LA). Escape: `discurre_integra_subterranea = true` AND `clasificacion_suelo_lista = 'urbano'`. **Diseño:** umbrales excluyentes con AAUS por construcción. La Licencia Ambiental es previa a la AAP (art. 89.4). | pendiente de implementar |
| `hito_licencia_ambiental_obtenida` | boolean | `derivado_documento` · Expediente | Ley 2/2026 art. 89.4 / art. 92.6 — existe resolución de Licencia Ambiental favorable del Ayuntamiento competente; desbloqueante de la AAP cuando `requiere_licencia_ambiental = true`. Órgano: Ayuntamiento (distinto de AAU/AAUS: Consejería de Medio Ambiente). Plazo resolución: 3 meses (silencio desestimatorio). | pendiente de implementar |
| `es_ptd` | boolean | `dato` · Solicitud | RD 337/2014 arts. 16.1, 20.1 — el titular/promotor es empresa de producción, transporte o distribución de energía eléctrica. Si `true`: el procedimiento de autorización se rige por la legislación sectorial (RD 1955/2000 / LSE); si `false`: solo requiere puesta en servicio salvo que `instalacion_cedida = true`. **Deduplicación:** distinto de `tipo_promotor` (ese no existe aún); este es el discriminador PTD/no-PTD del RAT. | pendiente de implementar |
| `instalacion_cedida` | boolean | `dato` · Solicitud | RD 337/2014 art. 20.3 / ITC-RAT 22 §5 — la instalación va a ser cedida a una PTD antes de su puesta en servicio (pasa a formar parte de la red de transporte o distribución). Si `true`: se aplica el régimen de autorizaciones del RD 1955/2000 título VII aunque el promotor no sea PTD. **Deduplicación:** distinto de `tiene_linea_evacuacion_comun` (ese es sobre fraccionamiento entre promotores; este es sobre la titularidad final de la instalación). | pendiente de implementar |
