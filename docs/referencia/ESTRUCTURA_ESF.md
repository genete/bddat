# Estructura Expediente-Solicitud-Fase (ESF)

**Versión:** 2.2 | **Fecha:** 2026-05-21

Fuente de verdad de qué fases aplican a cada combinación (tipo_solicitud × tipo_expediente). El JSON `ESTRUCTURA_ESF.json` es derivado de este documento; en caso de discrepancia prevalece este MD.

Las fases referenciadas son las definidas en `ESTRUCTURA_FTT.json`. Las restricciones operativas viven en el motor de reglas (ADR-007).

**Principio S-dominante:** la solicitud define el procedimiento; el tipo de expediente actúa como condición modificadora.

---

## Leyenda

| Símbolo | Significado |
|---|---|
| ✅ | Fase obligatoria para este tipo de solicitud y expediente — siempre ocurre |
| ⚠️ | Fase obligatoria si se dan condiciones adicionales (ajenas al par solicitud/expediente) — ver nota |
| 🔀 | Fase opcional: no es obligatoria ni condicionada, pero si ocurre es una fase completa del procedimiento |
| 🚫 | Fase no aplicable y prohibida — no procede crearla para esta combinación |

**Abreviaturas de tipos de expediente:**
`Transp.`=Transporte · `Distrib.`=Distribución · `D.Ced.`=Distribución cedida · `Renov.`=Renovable · `Autocons.`=Autoconsumo · `L.Dir.`=Línea directa · `Convenc.`=Convencional · `Otros`=Otros

---

## Instrucción completa de nueva instalación

### `AAP` — Autorización Administrativa Previa (sola)

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅¹ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | ✅ | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² |
| `CONSULTAS` | 🔀⁶ | 🔀⁶ | 🔀⁶ | 🔀⁶ | 🔀⁶ | 🔀⁶ | 🔀⁶ |
| `INFORMACION_PUBLICA` | ⚠️³ | ⚠️³ | ⚠️³ | ⚠️³ | ⚠️³ | ⚠️³ | ⚠️³ |
| `FIGURA_AMBIENTAL_EXTERNA` | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ |
| `AAU_AAUS_INTEGRADA` | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | ✅⁷ | ✅⁷ | ✅⁷ | ✅⁷ | ✅⁷ | ✅⁷ | ✅⁷ |

¹ Trámite `COMUNICACION_INICIO` obligatorio — la notificación de admisión a trámite de la AAP acredita el Hito 1 ante el gestor de red (RD-ley 23/2020 art. 1.2 in fine).  
² Solo si `proyecto.ia.siglas ∈ {AAU, AAUS}` — Decreto 356/2010; IC 1/2022 IV.3.3.  
³ Suprimible si `requiere_dup = false` AND `proyecto.ia.siglas ∉ {AAU, AAUS}` (DL 26/2021 DF 4ª). Suprimible también para instalaciones con tensión ≤ 30 kV + líneas subterráneas (con CT interior o solas) + suelo urbano/urbanizable (Decreto 9/2011 DA 1ª).  
⁴ Solo si el instrumento ambiental se tramita externamente al procedimiento sustantivo (procedimiento separado ante órgano ambiental).  
⁵ Solo si el instrumento ambiental se tramita integrado en el procedimiento sustantivo.  
⁶ Simultáneas a IP cuando proceda; 30 días (arts. 127, 131 RD 1955/2000).  
⁷ La publicación de la resolución en BOP (art. 128.3 RD 1955/2000) se suprime adicionalmente si tensión ≤ 30 kV + líneas subterráneas (con CT interior o solas) + suelo urbano/urbanizable (Decreto 9/2011 DA 1ª).

---

### `AAC` — Autorización Administrativa de Construcción (sola)

*Sin IP propia. Puede ir sola cuando la AAP ya está obtenida o la instalación no la requiere.*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🔀¹ | 🔀¹ | 🔀¹ | 🔀¹ | 🔀¹ | 🔀¹ | 🔀¹ |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

¹ 30 días. 15 días si existe AAP concedida en el mismo expediente y sin DUP pendiente (art. 131.1 RD 1955/2000).

---

### `DUP` — Declaración de Utilidad Pública autónoma

*Posterior a AAP o AAC ya obtenida (art. 143.2 RD 1955/2000).*

🚫 **Autoconsumo / Otros:** la DUP habilita la expropiación forzosa y/o servidumbre de paso de bienes ajenos. Las instalaciones de autoconsumo no implican ocupación de dominio público ajeno (excluidas estructuralmente — pendiente de confirmar con servicio, consultando normativa). El tipo Otros es un comodín residual sin vocación expropiadora propia; cualquier instalación que requiera DUP pertenece a una categoría tipificada.

| Fase | Transp. | Distrib. | D.Ced. | Renov. | L.Dir. | Convenc. | Autocons. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | 🚫 | 🚫 |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🔀² | 🔀² | 🔀² | 🔀² | 🔀² | 🔀² | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | ✅³ | ✅³ | ✅³ | ✅³ | ✅³ | ✅³ | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🚫 | 🚫 |

¹ La solicitud debe incluir anejo de afecciones con relación concreta e individualizada de bienes/derechos a expropiar o sobre los que imponer servidumbre (art. 143.3 RD 1955/2000).  
² Simultáneas a IP; 30 días, silencio positivo. Si DUP va con AAC, las consultas del art. 127 satisfacen este requisito (art. 146.2 RD 1955/2000).  
³ 30 días. BOE + BOP de provincias afectadas + prensa + tablones de ayuntamientos. Si la IP se realizó conjuntamente durante la tramitación de la AAP (art. 125 + 143.4), puede no requerirse IP separada — **PENDIENTE CONFIRMACIÓN NORMATIVA**.

---

### `AAP+AAC` — Tramitación conjunta nueva instalación

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅¹ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | ✅ | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² |
| `CONSULTAS` | 🔀³ | 🔀³ | 🔀³ | 🔀³ | 🔀³ | 🔀³ | 🔀³ |
| `INFORMACION_PUBLICA` | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ |
| `FIGURA_AMBIENTAL_EXTERNA` | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ |
| `AAU_AAUS_INTEGRADA` | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | ✅⁷ | ✅⁷ | ✅⁷ | ✅⁷ | ✅⁷ | ✅⁷ | ✅⁷ |

¹ Trámite `COMUNICACION_INICIO` obligatorio — acredita Hito 1 (RD-ley 23/2020 art. 1.2 in fine).  
² Solo si `proyecto.ia.siglas ∈ {AAU, AAUS}`.  
³ Simultáneas a IP cuando proceda; 30 días (arts. 127, 131 RD 1955/2000). 15 días si la tramitación es exclusivamente la AAC con AAP ya concedida en el mismo expediente y sin DUP.  
⁴ Suprimible si `requiere_dup = false` AND `proyecto.ia.siglas ∉ {AAU, AAUS}` (DL 26/2021 DF 4ª). Suprimible también para instalaciones con tensión ≤ 30 kV + líneas subterráneas (con CT interior o solas) + suelo urbano/urbanizable (Decreto 9/2011 DA 1ª).  
⁵ Solo si el instrumento ambiental se tramita externamente al procedimiento sustantivo.  
⁶ Solo si el instrumento ambiental se tramita integrado en el procedimiento sustantivo.  
⁷ La publicación de la resolución en BOP (art. 128.3 RD 1955/2000) se suprime adicionalmente si tensión ≤ 30 kV + líneas subterráneas (con CT interior o solas) + suelo urbano/urbanizable (Decreto 9/2011 DA 1ª).

---

### `AAP+AAC+DUP` — Tramitación conjunta con declaración de utilidad pública

🚫 **Autoconsumo / Otros:** misma razón que en `DUP` sola.

| Fase | Transp. | Distrib. | D.Ced. | Renov. | L.Dir. | Convenc. | Autocons. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅¹ | ✅ | ✅ | 🚫 | 🚫 |
| `CONSULTA_MINISTERIO` | ✅ | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² | 🚫 | 🚫 |
| `CONSULTAS` | 🔀³ | 🔀³ | 🔀³ | 🔀³ | 🔀³ | 🔀³ | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | ✅⁴ | ✅⁴ | ✅⁴ | ✅⁴ | ✅⁴ | ✅⁴ | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🚫 | 🚫 |

¹ Trámite `COMUNICACION_INICIO` obligatorio — acredita Hito 1 (RD-ley 23/2020 art. 1.2 in fine).  
² Solo si `proyecto.ia.siglas ∈ {AAU, AAUS}`.  
³ Simultáneas a IP; 30 días. La DUP no reduce el plazo de consultas.  
⁴ IP **siempre** obligatoria — la DUP suprime tanto la excepción del DL 26/2021 DF 4ª como la del Decreto 9/2011 DA 1ª.  
⁵ Solo si el instrumento ambiental se tramita externamente al procedimiento sustantivo.  
⁶ Solo si el instrumento ambiental se tramita integrado en el procedimiento sustantivo.

---

### `AAC+DUP` — AAC con DUP posterior a AAP ya obtenida

🚫 **Autoconsumo / Otros:** misma razón que en `DUP` sola.

| Fase | Transp. | Distrib. | D.Ced. | Renov. | L.Dir. | Convenc. | Autocons. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🚫 | 🚫 |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🔀¹ | 🔀¹ | 🔀¹ | 🔀¹ | 🔀¹ | 🔀¹ | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🚫 | 🚫 |

¹ Simultáneas a IP; 15 días — AAP ya concedida, sin nueva AAP ni modificación (art. 131.1 RD 1955/2000).  
² IP obligatoria aunque la AAP ya incluyera IP con igual alcance: los efectos jurídicos de la DUP son distintos a los de la AAP y requieren su propia publicidad (confirmado).

---

## Puesta en servicio

### `AE_PROVISIONAL` — Autorización de Explotación Provisional

🚫 **Transp., Distrib., D.Ced., Autocons., L.Dir., Otros:** la AE provisional es exclusiva del procedimiento de puesta en servicio de instalaciones de generación (período de pruebas previo a la AE definitiva). Estas categorías no son instalaciones de generación en el sentido del art. 132 bis RD 1955/2000.

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | 🚫 | 🚫 | 🚫 | ✅ | 🚫 | 🚫 | ✅ | 🚫 |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | 🚫 | 🚫 | 🚫 | ✅¹ | 🚫 | 🚫 | ✅¹ | 🚫 |

¹ Plazo 1 mes. Silencio desestimatorio (DA 3ª LSE). Habilita el período de pruebas previo a la AE definitiva (art. 132 bis RD 1955/2000).

---

### `AE_DEFINITIVA` — Autorización de Explotación Definitiva

*Procedimiento diferenciado según naturaleza: instalaciones de red (art. 132 RD 1955/2000) vs. generación (art. 132 ter). Para Autoconsumo, L.Dir. y Otros ver nota ³.*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅¹ | ✅¹ | ✅¹ | ✅² | ✅³ | ✅³ | ✅² | ✅³ |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | ✅¹ | ✅¹ | ✅¹ | ✅² | ✅³ | ✅³ | ✅² | ✅³ |

¹ Instalaciones de red — art. 132 RD 1955/2000. Procedimiento simplificado. Plazo 1 mes. Silencio desestimatorio.  
² Instalaciones de generación — art. 132 ter RD 1955/2000. Requiere AE_PROVISIONAL resuelta favorablemente y período de pruebas completado. Plazo 1 mes. Excepción ≤500 kW: puesta en servicio industrial (DL 2/2018 DA única apdo. 2).  
³ Autoconsumo, L.Dir., Otros: la LSE exige AE definitiva pero RD 1955/2000 arts. 132-132 ter no regula explícitamente estas categorías. Régimen aplicable pendiente de confirmar.

---

### `AE_DEFINITIVA+AAT` — Explotación definitiva con transmisión en resolución única

🚫 **Todos excepto D.Ced.:** la resolución simultánea AE+AAT es el mecanismo jurídico para la cesión de la instalación al distribuidor en el mismo acto de autorización de explotación. Solo aplica a instalaciones construidas por un promotor y cedidas a la distribuidora (D.Ced.). En instalaciones de Distribución ordinaria la titularidad ya es del distribuidor desde el inicio; en el resto no hay cesión de este tipo.

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | 🚫 | 🚫 | ✅ | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | 🚫 | 🚫 | ✅¹ | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |

¹ Resolución única que concede la AE definitiva y autoriza simultáneamente la transmisión de titularidad al distribuidor (arts. 132, 133 RD 1955/2000).

---

## Post-autorización

### `AAT` — Autorización de Transmisión de Titularidad

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |

¹ Plazo 3 meses. Solicitud conjunta transmitente + adquirente. La formalización (art. 133) y comunicación del adquirente en 1 mes (art. 134) son obligaciones del administrado, no fases del procedimiento (art. 133 RD 1955/2000).

---

### `CIERRE` — Cierre definitivo de instalación

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² |

¹ Informe previo del operador del sistema; plazo 90 días; silencio: se continúa el procedimiento (art. 137 RD 1955/2000, modificado por RD 88/2026). Operador: REE en Transporte, distribuidora en Distribución. Para instalaciones de transporte cuya autorización corresponde a la CCAA se solicita además informe previo a la DGPEM (art. 137.2).  
² Plazo: 6 meses (LSE art. 53.5, prevalece sobre los 3 meses del art. 138.1 RD 1955/2000 por rango jerárquico). La resolución **se publica obligatoriamente en el BOE y en el BOP** de las provincias donde radique la instalación ("en todo caso" — art. 138.3 RD 1955/2000). Sin posibilidad de excepción ni supresión.

---

### `AMPLIACION_PLAZO` — Ampliación de Plazo de Ejecución

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |

¹ Art. 128.4 RD 1955/2000: prórroga del plazo fijado en la AAP para solicitar la AAC, por razones justificadas. LPACAP art. 32: ampliación de plazos administrativos de carácter general.

---

### `CORRECCION_ERRORES` — Corrección de Errores en Resolución

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |

¹ Corrección de errores materiales, aritméticos o de hecho. No puede alterar el fondo de la resolución (LPACAP art. 109.2).

---

## Registros

### `RAIPEE_PREVIA` — Inscripción Previa en RAIPEE

🚫 **Transp., Distrib., D.Ced., Autocons., L.Dir., Otros:** el RAIPEE (Registro de Aptitud de Instalaciones para Percibir la Energía Evacuada) es exclusivo de instalaciones de generación bajo el régimen del RD 1183/2020. Las categorías marcadas no son instalaciones de generación en este sentido.

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | 🚫 | 🚫 | 🚫 | ✅ | 🚫 | 🚫 | ✅ | 🚫 |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | 🚫 | 🚫 | 🚫 | ✅¹ | 🚫 | 🚫 | ✅¹ | 🚫 |

¹ Resolución de aptitud de infraestructuras previas al expediente de evacuación. Previa a RAIPEE_DEFINITIVA (RD 1183/2020).

---

### `RAIPEE_DEFINITIVA` — Inscripción Definitiva en RAIPEE

🚫 mismas categorías y razón que `RAIPEE_PREVIA`.

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | 🚫 | 🚫 | 🚫 | ✅ | 🚫 | 🚫 | ✅ | 🚫 |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | 🚫 | 🚫 | 🚫 | ✅¹ | 🚫 | 🚫 | ✅¹ | 🚫 |

¹ Requiere RAIPEE_PREVIA resuelta favorablemente (RD 1183/2020).

---

### `RADNE` — Inscripción en Registro de Autoconsumo

🚫 **Transp., Distrib., D.Ced., Renov., L.Dir., Convenc., Otros:** el RADNE (Registro Administrativo de Instalaciones de Producción en modalidad de autoconsumo) es exclusivo de instalaciones de autoconsumo (RD 244/2019).

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | 🚫 | 🚫 | 🚫 | 🚫 | ✅ | 🚫 | 🚫 | 🚫 |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | 🚫 | 🚫 | 🚫 | 🚫 | ✅¹ | 🚫 | 🚫 | 🚫 |

¹ Inscripción en el Registro Administrativo de Instalaciones de Producción en modalidad de autoconsumo (RD 244/2019).

---

## Incidencias procedimentales

### `DESISTIMIENTO` — Desistimiento de Solicitud

*Requiere `solicitud_afectada_id`.*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² |

¹ Verifica solicitud afectada en tramitación activa; produce CERT_FIN_INSTRUCCION consumido por RESOLUCION.ELABORACION.  
² La Administración acepta el desistimiento y archiva la solicitud afectada (LPACAP art. 93).

---

### `RENUNCIA` — Renuncia a Autorización

*Requiere `solicitud_afectada_id`. El titular renuncia a derechos ya concedidos.*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² |

¹ Verifica solicitud afectada y derechos concedidos; produce CERT_FIN_INSTRUCCION consumido por RESOLUCION.ELABORACION.  
² Requiere resolución expresa que acepte la renuncia (LPACAP art. 94).

---

### `RECURSO` — Recurso Administrativo

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RESOLUCION` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |

¹ Puede ser estimatoria, desestimatoria o inadmisión (LPACAP arts. 112-126).

---

## Especiales

### `INTERESADO` — Reconocimiento de Condición de Interesado

*Fase finalizadora propia: `RECONOCIMIENTO_INTERESADO` — no usa `RESOLUCION`.*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |
| `CONSULTA_MINISTERIO` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `COMPATIBILIDAD_AMBIENTAL` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTAS` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `INFORMACION_PUBLICA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `AAU_AAUS_INTEGRADA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `CONSULTA_OPERADOR_SISTEMA` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |
| `RECONOCIMIENTO_INTERESADO` | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² |
| `RESOLUCION` | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 | 🚫 |

¹ Verifica la solicitud y produce CERT_FIN_INSTRUCCION consumido por RECONOCIMIENTO_INTERESADO.ELABORACION.  
² Evalúa si el solicitante acredita interés legítimo en el procedimiento principal (LPACAP art. 4).

---

### `OTRO` — Otro Tipo de Solicitud

*Comodín para solicitudes no clasificadas. El tramitador gestiona discrecionalmente todas las actuaciones previas a la resolución.*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 |
| `CONSULTA_MINISTERIO` | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 |
| `COMPATIBILIDAD_AMBIENTAL` | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 |
| `CONSULTAS` | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 |
| `INFORMACION_PUBLICA` | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 |
| `FIGURA_AMBIENTAL_EXTERNA` | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 |
| `AAU_AAUS_INTEGRADA` | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 |
| `CONSULTA_OPERADOR_SISTEMA` | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 |
| `RECONOCIMIENTO_INTERESADO` | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 | 🔀 |
| `RESOLUCION` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
