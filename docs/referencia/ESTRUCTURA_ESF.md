# Estructura Expediente-Solicitud-Fase (ESF)

**Versión:** 2.0 | **Fecha:** 2026-05-20

Fuente de verdad de qué fases aplican a cada combinación (tipo_solicitud × tipo_expediente). El JSON derivado `ESTRUCTURA_ESF.json` refleja este documento; en caso de discrepancia prevalece este MD.

Las fases referenciadas son las definidas en `ESTRUCTURA_FTT.json`. Las restricciones operativas viven en el motor de reglas (ADR-007).

**Principio S-dominante:** la solicitud define el procedimiento; el tipo de expediente actúa como condición modificadora.

---

## Leyenda

| Símbolo | Significado |
|---|---|
| ✅ | Fase obligatoria para este tipo de expediente |
| ⚠️ | Condicional — condición en nota al pie (no depende del tipo de expediente) |
| — | No aplica |

**Abreviaturas de tipos de expediente:**
`Transp.`=Transporte · `Distrib.`=Distribución · `D.Ced.`=Distribución cedida · `Renov.`=Renovable · `Autocons.`=Autoconsumo · `L.Dir.`=Línea directa · `Convenc.`=Convencional · `Otros`=Otros

---

## Instrucción completa de nueva instalación

### `AAP` — Autorización Administrativa Previa (sola)

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅¹ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | ✅ | — | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² |
| `CONSULTAS` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `INFORMACION_PUBLICA` | ✅³ | ✅³ | ✅³ | ✅³ | ✅³ | ✅³ | ✅³ |
| `FIGURA_AMBIENTAL_EXTERNA` | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ |
| `AAU_AAUS_INTEGRADA` | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — | — | — |
| `RESOLUCION` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

¹ Trámite `COMUNICACION_INICIO` obligatorio — acredita Hito 1 ante el gestor de red (RD-ley 23/2020 art. 1.2 in fine).  
² Solo si `ia_previa ∈ {AAU, AAUS}` — Decreto 356/2010; IC 1/2022 IV.3.3.  
³ Suprimible si 3ª cat. AT + subterránea + suelo urbano + sin DUP — Decreto 9/2011 DA 1ª; ver NORMATIVA_EXCEPCIONES_AT §3.1.  
⁴ Solo si `ia_tipo == externa`.  
⁵ Solo si `ia_tipo == integrada`.

---

### `AAC` — Autorización Administrativa de Construcción (sola)

*Sin IP propia. Puede ir sola cuando la AAP ya está obtenida o la instalación no la requiere.*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | — | — | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — | — | — | — | — | — |
| `CONSULTAS` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |
| `INFORMACION_PUBLICA` | — | — | — | — | — | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — | — | — | — | — | — |
| `AAU_AAUS_INTEGRADA` | — | — | — | — | — | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — | — | — |
| `RESOLUCION` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

¹ 30 días. 15 días si AAP previa y sin DUP ni modificación de AAP (art. 131.1 RD 1955/2000).

---

### `DUP` — Declaración de Utilidad Pública autónoma

*Posterior a AAP o AAC ya obtenida (art. 143.2 RD 1955/2000). No aplica a Autoconsumo ni Otros.*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | L.Dir. | Convenc. |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |
| `CONSULTA_MINISTERIO` | — | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — | — | — | — | — |
| `CONSULTAS` | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² |
| `INFORMACION_PUBLICA` | ✅³ | ✅³ | ✅³ | ✅³ | ✅³ | ✅³ |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — | — | — | — | — |
| `AAU_AAUS_INTEGRADA` | — | — | — | — | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — | — |
| `RESOLUCION` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

¹ Incluye anejo de afecciones con relación concreta de bienes/derechos a expropiar o servidumbre (art. 143.3).  
² Simultáneas a IP; 30 días, silencio positivo. Si DUP va con AAC, consultas del art. 127 satisfacen este requisito (art. 146.2).  
³ 30 días. BOE + BOP provincias afectadas + prensa + tablones ayuntamientos. Si la IP ya se realizó conjuntamente en la AAP/AAC, puede no requerirse IP separada.

---

### `AAP+AAC` — Instrucción conjunta nueva instalación

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅¹ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | ✅ | — | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² |
| `CONSULTAS` | ✅³ | ✅³ | ✅³ | ✅³ | ✅³ | ✅³ | ✅³ |
| `INFORMACION_PUBLICA` | ✅⁴ | ✅⁴ | ✅⁴ | ✅⁴ | ✅⁴ | ✅⁴ | ✅⁴ |
| `FIGURA_AMBIENTAL_EXTERNA` | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ |
| `AAU_AAUS_INTEGRADA` | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — | — | — |
| `RESOLUCION` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

¹ Trámite `COMUNICACION_INICIO` obligatorio — acredita Hito 1 (RD-ley 23/2020 art. 1.2 in fine).  
² Solo si `ia_previa ∈ {AAU, AAUS}`.  
³ 30 días. 15 días si solo AAC con AAP previa y sin DUP (art. 131.1).  
⁴ Suprimible si 3ª cat. AT + subterránea + suelo urbano + sin DUP.  
⁵ Solo si `ia_tipo == externa`.  
⁶ Solo si `ia_tipo == integrada`.

---

### `AAP+AAC+DUP` — Instrucción conjunta con declaración de utilidad pública

*No aplica a Autoconsumo ni Otros.*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | L.Dir. | Convenc. |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅¹ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | ✅ | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² |
| `CONSULTAS` | ✅³ | ✅³ | ✅³ | ✅³ | ✅³ | ✅³ |
| `INFORMACION_PUBLICA` | ✅⁴ | ✅⁴ | ✅⁴ | ✅⁴ | ✅⁴ | ✅⁴ |
| `FIGURA_AMBIENTAL_EXTERNA` | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ | ⚠️⁵ |
| `AAU_AAUS_INTEGRADA` | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ | ⚠️⁶ |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — | — |
| `RESOLUCION` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

¹ Trámite `COMUNICACION_INICIO` obligatorio — acredita Hito 1 (RD-ley 23/2020 art. 1.2 in fine).  
² Solo si `ia_previa ∈ {AAU, AAUS}`.  
³ 30 días. La DUP no reduce el plazo de consultas.  
⁴ IP **siempre** obligatoria — la DUP suprime la excepción del Decreto 9/2011 DA 1ª.  
⁵ Solo si `ia_tipo == externa`.  
⁶ Solo si `ia_tipo == integrada`.

---

### `AAC+DUP` — AAC con DUP posterior a AAP ya obtenida

*No aplica a Autoconsumo ni Otros.*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | L.Dir. | Convenc. |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | — | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — | — | — | — | — |
| `CONSULTAS` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |
| `INFORMACION_PUBLICA` | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² | ⚠️² |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — | — | — | — | — |
| `AAU_AAUS_INTEGRADA` | — | — | — | — | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — | — |
| `RESOLUCION` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

¹ 15 días — AAP ya obtenida (art. 131.1 RD 1955/2000).  
² PENDIENTE CONFIRMACIÓN NORMATIVA: si la AAP ya incluyó IP con alcance suficiente para la DUP, puede no requerirse IP adicional.

---

## Puesta en servicio

### `AE_PROVISIONAL` — Autorización de Explotación Provisional

*Exclusivo generación. Habilita período de pruebas previo a AE_DEFINITIVA.*

| Fase | Renov. | Convenc. |
|---|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — |
| `CONSULTAS` | — | — |
| `INFORMACION_PUBLICA` | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — |
| `AAU_AAUS_INTEGRADA` | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — |
| `RESOLUCION` | ✅¹ | ✅¹ |

¹ Plazo 1 mes. Silencio desestimatorio (DA 3ª LSE). Base legal: art. 132 bis RD 1955/2000.

---

### `AE_DEFINITIVA` — Autorización de Explotación Definitiva

*Procedimiento distinto según tipo de instalación: red (Transp./Distrib./D.Ced.) vs. generación (Renov./Convenc.).*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Convenc. |
|---|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅¹ | ✅¹ | ✅¹ | ✅² | ✅² |
| `CONSULTA_MINISTERIO` | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — | — | — | — |
| `CONSULTAS` | — | — | — | — | — |
| `INFORMACION_PUBLICA` | — | — | — | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — | — | — | — |
| `AAU_AAUS_INTEGRADA` | — | — | — | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — |
| `RESOLUCION` | ✅¹ | ✅¹ | ✅¹ | ✅² | ✅² |

¹ Instalaciones de red — art. 132 RD 1955/2000. Procedimiento simplificado. Plazo 1 mes.  
² Generación — art. 132 ter. Requiere AE_PROVISIONAL resuelta favorablemente y período de pruebas completado. Plazo 1 mes. Excepción ≤500 kW: puesta en servicio industrial (DL 2/2018 DA única apdo. 2).

---

### `AE_DEFINITIVA+AAT` — Explotación definitiva con transmisión en resolución única

*Típico en instalaciones construidas por promotor y cedidas a la distribuidora.*

| Fase | Distrib. | D.Ced. |
|---|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — |
| `CONSULTAS` | — | — |
| `INFORMACION_PUBLICA` | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — |
| `AAU_AAUS_INTEGRADA` | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — |
| `RESOLUCION` | ✅¹ | ✅¹ |

¹ Resolución única: concede AE definitiva y autoriza simultáneamente la transmisión al distribuidor (arts. 132, 133 RD 1955/2000).

---

## Post-autorización

### `AAT` — Autorización de Transmisión de Titularidad

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | — | — | — | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — | — | — | — | — | — | — |
| `CONSULTAS` | — | — | — | — | — | — | — | — |
| `INFORMACION_PUBLICA` | — | — | — | — | — | — | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — | — | — | — | — | — | — |
| `AAU_AAUS_INTEGRADA` | — | — | — | — | — | — | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — | — | — | — |
| `RESOLUCION` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |

¹ Plazo 3 meses. Solicitud conjunta transmitente + adquirente. Formalización posterior (art. 133) y comunicación del adquirente en 1 mes (art. 134) son obligaciones del administrado, no fases del procedimiento.

---

### `CIERRE` — Cierre definitivo de instalación

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | — | — | — | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — | — | — | — | — | — | — |
| `CONSULTAS` | — | — | — | — | — | — | — | — |
| `INFORMACION_PUBLICA` | — | — | — | — | — | — | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — | — | — | — | — | — | — |
| `AAU_AAUS_INTEGRADA` | — | — | — | — | — | — | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — | — | — | — |
| `RESOLUCION` | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² | ✅² |

¹ 90 días, silencio positivo (art. 136 RD 1955/2000). Operador: REE en Transporte, distribuidora en Distribución.  
² Plazo 3 meses. La resolución fija el plazo de ejecución; caducidad si vence sin ejecución (art. 138).

---

### `AMPLIACION_PLAZO` — Ampliación de Plazo de Ejecución

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | — | — | — | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — | — | — | — | — | — | — |
| `CONSULTAS` | — | — | — | — | — | — | — | — |
| `INFORMACION_PUBLICA` | — | — | — | — | — | — | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — | — | — | — | — | — | — |
| `AAU_AAUS_INTEGRADA` | — | — | — | — | — | — | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — | — | — | — |
| `RESOLUCION` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |

¹ Art. 128.4 RD 1955/2000: prórroga del plazo fijado en la AAP para solicitar la AAC. LPACAP art. 32: ampliación de plazos administrativos. Aplica también a prórrogas del plazo de ejecución de la AAC o de la AE.

---

### `CORRECCION_ERRORES` — Corrección de Errores en Resolución

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | — | — | — | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — | — | — | — | — | — | — |
| `CONSULTAS` | — | — | — | — | — | — | — | — |
| `INFORMACION_PUBLICA` | — | — | — | — | — | — | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — | — | — | — | — | — | — |
| `AAU_AAUS_INTEGRADA` | — | — | — | — | — | — | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — | — | — | — |
| `RESOLUCION` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |

¹ Corrección de errores materiales, aritméticos o de hecho. No puede alterar el fondo de la resolución (LPACAP art. 109.2).

---

## Registros

### `RAIPEE_PREVIA` — Inscripción Previa en RAIPEE

*Resolución de Aptitud de Infraestructuras Previas al Expediente de Evacuación. Exclusivo generación.*

| Fase | Renov. | Convenc. |
|---|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — |
| `CONSULTAS` | — | — |
| `INFORMACION_PUBLICA` | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — |
| `AAU_AAUS_INTEGRADA` | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — |
| `RESOLUCION` | ✅¹ | ✅¹ |

¹ Base legal: RD 1183/2020. Previa a RAIPEE_DEFINITIVA.

---

### `RAIPEE_DEFINITIVA` — Inscripción Definitiva en RAIPEE

| Fase | Renov. | Convenc. |
|---|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — |
| `CONSULTAS` | — | — |
| `INFORMACION_PUBLICA` | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — |
| `AAU_AAUS_INTEGRADA` | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — |
| `RESOLUCION` | ✅¹ | ✅¹ |

¹ Base legal: RD 1183/2020. Requiere RAIPEE_PREVIA resuelta favorablemente.

---

### `RADNE` — Inscripción en Registro de Autoconsumo

| Fase | Autocons. |
|---|:---:|
| `ANALISIS_SOLICITUD` | ✅ |
| `CONSULTA_MINISTERIO` | — |
| `COMPATIBILIDAD_AMBIENTAL` | — |
| `CONSULTAS` | — |
| `INFORMACION_PUBLICA` | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — |
| `AAU_AAUS_INTEGRADA` | — |
| `CONSULTA_OPERADOR_SISTEMA` | — |
| `RECONOCIMIENTO_INTERESADO` | — |
| `RESOLUCION` | ✅¹ |

¹ Inscripción en el Registro Administrativo de Instalaciones de Producción en modalidad de autoconsumo (RD 244/2019).

---

## Incidencias procedimentales

### `DESISTIMIENTO` — Desistimiento de Solicitud

*Requiere `solicitud_afectada_id`. Finalizadora directa sin instrucción.*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | — | — | — | — | — | — | — | — |
| `CONSULTA_MINISTERIO` | — | — | — | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — | — | — | — | — | — | — |
| `CONSULTAS` | — | — | — | — | — | — | — | — |
| `INFORMACION_PUBLICA` | — | — | — | — | — | — | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — | — | — | — | — | — | — |
| `AAU_AAUS_INTEGRADA` | — | — | — | — | — | — | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — | — | — | — |
| `RESOLUCION` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |

¹ LPACAP art. 93. La Administración acepta el desistimiento y archiva la solicitud afectada.

---

### `RENUNCIA` — Renuncia a Autorización

*Requiere `solicitud_afectada_id`. El titular renuncia a derechos ya concedidos.*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | — | — | — | — | — | — | — | — |
| `CONSULTA_MINISTERIO` | — | — | — | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — | — | — | — | — | — | — |
| `CONSULTAS` | — | — | — | — | — | — | — | — |
| `INFORMACION_PUBLICA` | — | — | — | — | — | — | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — | — | — | — | — | — | — |
| `AAU_AAUS_INTEGRADA` | — | — | — | — | — | — | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — | — | — | — |
| `RESOLUCION` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |

¹ LPACAP art. 94. Finalizadora directa.

---

### `RECURSO` — Recurso Administrativo

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CONSULTA_MINISTERIO` | — | — | — | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — | — | — | — | — | — | — |
| `CONSULTAS` | — | — | — | — | — | — | — | — |
| `INFORMACION_PUBLICA` | — | — | — | — | — | — | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — | — | — | — | — | — | — |
| `AAU_AAUS_INTEGRADA` | — | — | — | — | — | — | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — | — | — | — |
| `RESOLUCION` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |

¹ LPACAP arts. 112-126. Puede ser estimatoria, desestimatoria o inadmisión.

---

## Especiales

### `INTERESADO` — Reconocimiento de Condición de Interesado

*Fase finalizadora propia: `RECONOCIMIENTO_INTERESADO` — no usa `RESOLUCION`.*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | — | — | — | — | — | — | — | — |
| `CONSULTA_MINISTERIO` | — | — | — | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — | — | — | — | — | — | — |
| `CONSULTAS` | — | — | — | — | — | — | — | — |
| `INFORMACION_PUBLICA` | — | — | — | — | — | — | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — | — | — | — | — | — | — |
| `AAU_AAUS_INTEGRADA` | — | — | — | — | — | — | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ |
| `RESOLUCION` | — | — | — | — | — | — | — | — |

¹ LPACAP art. 4. Evalúa si el solicitante acredita interés legítimo en el procedimiento principal.

---

### `OTRO` — Otro Tipo de Solicitud

*Comodín para solicitudes no clasificadas. El tramitador gestiona discrecionalmente las actuaciones previas.*

| Fase | Transp. | Distrib. | D.Ced. | Renov. | Autocons. | L.Dir. | Convenc. | Otros |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ANALISIS_SOLICITUD` | — | — | — | — | — | — | — | — |
| `CONSULTA_MINISTERIO` | — | — | — | — | — | — | — | — |
| `COMPATIBILIDAD_AMBIENTAL` | — | — | — | — | — | — | — | — |
| `CONSULTAS` | — | — | — | — | — | — | — | — |
| `INFORMACION_PUBLICA` | — | — | — | — | — | — | — | — |
| `FIGURA_AMBIENTAL_EXTERNA` | — | — | — | — | — | — | — | — |
| `AAU_AAUS_INTEGRADA` | — | — | — | — | — | — | — | — |
| `CONSULTA_OPERADOR_SISTEMA` | — | — | — | — | — | — | — | — |
| `RECONOCIMIENTO_INTERESADO` | — | — | — | — | — | — | — | — |
| `RESOLUCION` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
