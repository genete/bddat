# NORMATIVA — Legislación aplicable al motor de reglas BDDAT

> **Aplica a:** Motor de reglas — base legal de las reglas de tramitación ESFTT.
> **Estado:** Catálogo de normas y estructura de extracción definida. Iteraciones de investigación pendientes.

Este documento es el **catálogo normativo de referencia** del motor de reglas de BDDAT. Recoge la legislación estatal y autonómica aplicable a los procedimientos de autorización de instalaciones de alta tensión en Andalucía, organizada por ámbito (distribución y transporte, renovables, autoconsumo). Su función es servir de fuente de verdad sobre qué normas rigen cada tipo de solicitud (AAP, AAC, AE, transmisión, cierre), de manera que los documentos de diseño del motor —`DISEÑO_MOTOR_REGLAS.md`, `NORMATIVA_SOLICITUDES.md`— puedan referenciar una base legal verificada. Los plazos procedimentales se extraen y documentan en profundidad en `NORMATIVA_PLAZOS.md`; este documento se centra en el catálogo de normas y en el proceso de extracción de las reglas de tramitación.

Esa extracción se articula como un proceso iterativo (§5) de complejidad creciente: desde el mapa de fases obligatorias por tipo de solicitud hasta los casos límite y la casuística especial, pasando por los regímenes de excepción. Este enfoque responde a la densidad normativa del ámbito: las reglas que gobiernan un expediente de AT emergen de la interacción entre normas de distinto rango y ámbito —estatal, autonómica, sectorial, ambiental— y no pueden identificarse de forma exhaustiva en una sola lectura.

---

## Índice

| § | Contenido | Naturaleza |
|---|---|---|
| [§1](#1-contexto-del-sistema-bddat) | Contexto del sistema BDDAT — jerarquía ESFTT y tipos de instalación | Referencia de dominio |
| [§6](#6-fuentes-normativas-por-ámbito--junta-de-andalucía) | **Vista legible del catálogo** — todas las normas ordenadas por ámbito | Vista legible (fuente de verdad: `normas_catalog.csv`) |
| [§6.1](#61-energía-eléctrica--distribución-y-transporte) | Energía eléctrica — distribución y transporte (Junta + BOE) | Catálogo normativo |
| [§6.2](#62-energías-renovables) | Energías renovables (Junta + BOE) | Catálogo normativo |
| [§6.3](#63-autoconsumo) | Autoconsumo (Junta + BOE) | Catálogo normativo |

> **Nota de uso:** Los documentos derivados (`NORMATIVA_PLAZOS.md`, `NORMATIVA_SOLICITUDES.md`, `DISEÑO_MOTOR_REGLAS.md`) deben referenciar §6.x como punto de entrada al catálogo normativo. La **fuente de verdad estructurada** (estado, ID técnico, doc_extraccion) es `docs/normas_catalog.csv` — usar para consultas de estado o adición de normas nuevas. El proceso de investigación (protocolo, cola de trabajo) se gestiona en `docs/GUIA_NORMAS.md`; el diccionario de variables del ContextAssembler en `docs/DISEÑO_CONTEXT_ASSEMBLER.md`.

---

## 1. Contexto del sistema BDDAT

La tramitación de cada expediente sigue la jerarquía ESFTT:

```
EXPEDIENTE (proyecto de instalación eléctrica)
  └── SOLICITUD (qué se pide: AAP, AAC, APO, utilidad pública...)
        └── FASE (etapas procedimentales: análisis, info pública, consultas, resolución...)
              └── TRÁMITE (acciones concretas dentro de la fase)
                    └── TAREA (unidad de trabajo: redactar, firmar, notificar, publicar, esperar plazo)
```

**Tipos de instalaciones de alta tensión:**
- Líneas eléctricas aéreas y subterráneas
- Subestaciones y centros de transformación
- Instalaciones de generación (renovable y convencional)
- Elementos de conexión y seccionamiento

**Tipos de solicitud:** AAP, AAC, APO, DUP, Modificación, Desistimiento/Renuncia
(Ver `docs/NORMATIVA_SOLICITUDES.md` para detalle y combinaciones.)

---

## 6. Fuentes normativas por ámbito — Junta de Andalucía

> **Fuente de verdad estructurada:** `docs/normas_catalog.csv` — estado, ID técnico, procedimientos y doc_extraccion en formato machine-readable. Las tablas siguientes son una vista legible; para añadir o actualizar normas, editar el CSV.

Páginas de referencia de la Consejería de Industria, Energía y Minas (Junta de Andalucía):

| Ámbito |
|---|
| [Energía eléctrica (distribución y transporte)](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/electricidad.html) |
| [Energías renovables](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/renovables.html) |
| [Autoconsumo](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/autoconsumo.html) |

Página de referencia del Ministerio para la Transición Ecológica y el Reto Demográfico (MITECO — Estado):

| Ámbito |
|---|
| [Energía — MITECO](https://www.miteco.gob.es/es/energia.html) *(explorado 2026-04-02)* |

> **Aviso de obsolescencia:** Las páginas de la Consejería y las fichas de procedimiento se actualizan con retraso o de forma incompleta. Para detectar cambios normativos conviene combinar estas fuentes con:
> - **BOE / BOJA consolidados** — [boe.es](https://www.boe.es) y [juntadeandalucia.es/eboja](https://www.juntadeandalucia.es/eboja/) como fuentes de verdad de texto legal vigente.
> - **Alertas BOE** — el BOE ofrece servicio de alertas por materia o norma concreta.
> - **Revisión periódica de estas dos páginas** — volver a ejecutar la extracción de normativa de los apartados §6.1 y §6.2 para detectar nuevas entradas o modificaciones.

---

### 6.1 Energía eléctrica — distribución y transporte

Normas identificadas en la página de la Consejería, fichas de procedimiento y legislación general aplicable:

> **Glosario:** AAP = Autorización Administrativa Previa · AAC = Autorización Administrativa de Construcción · AE = Autorización de Explotación · Trans. = Transmisión de titularidad · Cierre = Autorización de cierre · BT = instalaciones de baja tensión (en renovables) · General = todos los procedimientos / marco competencial

| Norma | Afecta a | ID-REF | Estado | ID técnico |
|---|---|---|---|---|
| [Ley 24/2013, de 26 de diciembre (LSE)](https://www.boe.es/eli/es/l/2013/12/26/24/con) | General | REF-LSE | MAPEO_CONTEXTO | BOE-A-2013-13645 |
| [RD 1955/2000, de 1 de diciembre](https://www.boe.es/eli/es/rd/2000/12/01/1955/con) | AAP, AAC, AE, Trans., Cierre | REF-RD1955 | MAPEO_CONTEXTO | BOE-A-2000-24019 |
| [Ley 39/2015, de 1 de octubre (LPACAP)](https://www.boe.es/eli/es/l/2015/10/01/39/con) | General | REF-LPACAP | MAPEO_CONTEXTO | (ver ELI) |
| [Ley 21/2013, de 9 de diciembre (EIA)](https://www.boe.es/eli/es/l/2013/12/09/21/con) | AAP | REF-EIA | IDENTIFICADA | (ver ELI) |
| [RD 842/2002, de 2 de agosto (REBT)](https://www.boe.es/eli/es/rd/2002/08/02/842/con) | AE · BT | — | IDENTIFICADA | (ver ELI) |
| [Decreto 9/2011, de 18 de enero](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=22168) | AAP | REF-D9-2011 | EXTRAÍDA | 22168 |
| [Decreto-ley 26/2021, de 14 de diciembre](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=33520) | AAP | REF-DL26-2021 | EXTRAÍDA | 33520 |
| [RD 337/2014, de 9 de mayo (RAT)](https://www.boe.es/eli/es/rd/2014/05/09/337/con) | AAP, AAC, AE, Trans., Cierre | REF-RAT | IDENTIFICADA | (ver ELI) |
| [RD 223/2008, de 15 de febrero](https://www.boe.es/eli/es/rd/2008/02/15/223/con) | AAP, AAC, AE, Trans., Cierre | REF-LAT | IDENTIFICADA | (ver ELI) |
| [Decreto 356/2010, de 3 de agosto — AAU](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=21892) | AAP, Cierre | — | IDENTIFICADA | 21892 |
| [Ley 2/2026, de 12 de marzo — Gestión Ambiental de Andalucía](https://www.juntadeandalucia.es/boja/2026/55/1) | AAP, AAC, General | REF-L2-2026 | IDENTIFICADA | 40751 |
| [Decreto-ley 2/2018, de 26 de junio — Simplificación energía y renovables](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=26974) | AAP, AAC, AE, General | REF-DL2-2018 | EXTRAÍDA | 26974 |
| [RD 413/2014, de 6 de junio](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2014-6123) | AAC, AE, Trans., Cierre | — | IDENTIFICADA | BOE-A-2014-6123 |
| [RD 917/2025, de 15 de octubre](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-20694) | AAC, AE | — | IDENTIFICADA | BOE-A-2025-20694 |
| [Resolución de 9 de marzo de 2016 — Delegación de competencias a las DTs](http://juntadeandalucia.es/boja/2016/51/23) | General | REF-RES2016 | IDENTIFICADA | sin consolidar |
| [Instrucción 1/2023, de 11 de julio — SGE AT (pdf)](https://www.juntadeandalucia.es/sites/default/files/2023-10/7_20230711_INSTRUCCI%C3%93N%201-2023%20de%20SGE%20AT(F).pdf) | General | — | IDENTIFICADA | sin consolidar |
| [Instrucción Conjunta 1/2022 — SGE + DGSAyCC (pdf)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2022/10/INSTRUCCION_CONJUNTA_1_2022_SGE_DGSAyCC_F_F.pdf) | AAP | — | IDENTIFICADA | sin consolidar |
| [Resolución de 13 de octubre de 2023 — Formulario de solicitud](https://www.juntadeandalucia.es/eboja/2023/206/BOJA23-206-00006-16391-01_00291369.pdf) | General | — | IDENTIFICADA | sin consolidar |
| [Corrección de errores — Resolución 13 octubre 2023](https://www.juntadeandalucia.es/eboja/2023/233/BOJA23-233-00005-18542-01_00293610.pdf) | General | — | — | — |
| [Ley 7/2021, de 1 de diciembre — LISTA](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=34218) | AAP, General | — | IDENTIFICADA | (ver BOJA) |
| [Decreto 550/2022, de 29 de noviembre — Reglamento General de la LISTA](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=34756) | AAP, General | — | IDENTIFICADA | (ver BOJA) |
| [Decreto-ley 3/2024, de 6 de febrero — Simplificación administrativa](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=35380) | General | — | IDENTIFICADA | 35380 |
| [Decreto-ley 4/2024, de 27 de febrero — Modifica DL 3/2024](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=35417) | General | — | IDENTIFICADA | 35417 |
| [Ley 4/2025, de 15 de diciembre — Espacios productivos](https://www.boe.es/buscar/doc.php?id=BOE-A-2026-422) | AAP, AAC, AE | REF-L4-2025 | IDENTIFICADA | BOE-A-2026-422 |
| [Decreto 59/2005 (BOJA 2005/118)](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=17891) | AE · BT | — | IDENTIFICADA | 17891 |
| [Orden de 5 de marzo de 2013 (BOJA 2013/48)](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=29083) | AE · BT | — | IDENTIFICADA | 29083 |
| [Resolución de 23 de marzo de 2026 — Ficha técnica AT](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=40778) | AE | — | IDENTIFICADA | 40778 |
| [Orden de 24 de octubre de 2005 (BOJA 2005/217)](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=18144) | AE · BT | — | IDENTIFICADA | 18144 |
| [Resolución de 9 de mayo de 2024 (BOJA 2024/95/52)](https://www.juntadeandalucia.es/boja/2024/95/52) | AE · BT | — | IDENTIFICADA | sin consolidar |
| [Modelo certificado instalación BT (pdf rellenable)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/02/140223_Certificado_BT_rellenable_mod.pdf) | AE · BT | — | — | — |

#### Clasificación de procedimientos — catálogo Junta de Andalucía

> La Consejería divide las autorizaciones en fichas de procedimiento que no siempre se corresponden con la estructura real de los expedientes en BDDAT. Se recogen aquí como referencia para navegación y extracción de datos de las fichas (normativa, plazos, documentación), no como modelo de clasificación.

| Tipo (denominación Junta) | Ficha |
|---|---|
| AAP — producción, distribución, transporte y líneas directas | [9588](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/9588.html) |
| AAC — producción, distribución, transporte y líneas directas | [11944](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/11944.html) |
| AE — instalaciones de producción (excl. líneas de evacuación) | [11954](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/11954.html) |
| AE — distribución, transporte secundario, acometidas (<380 kV), líneas directas e infraestructuras de evacuación | [11996](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/11996.html) |
| Transmisión — producción, distribución, transporte, líneas directas y líneas a ceder | [11955](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/11955.html) |
| Cierre — producción, distribución, transporte y líneas directas | [11963](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/11963.html) |

> [Formulario electrónico de solicitud (VEA)](https://ws050.juntadeandalucia.es/vea/accesoDirecto?codProcedimiento=CHFE_DGE_9588)

---

### 6.2 Energías renovables

Normas no recogidas en §6.1, identificadas en la [página de renovables](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/renovables.html) y en la ficha de procedimiento [12083](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/12083.html) (Registro de instalaciones de producción):

> La página de renovables no tiene fichas de procedimiento propias para AAP/AAC/AE — remite a las mismas fichas del catálogo general (§6.1). Lo específico de renovables es la normativa sectorial de producción y acceso a red.

| Norma | Afecta a | ID-REF | Estado | ID técnico |
|---|---|---|---|---|
| [Ley 2/2007, de 27 de marzo](https://www.boe.es/eli/es-an/l/2007/03/27/2/con) | General | — | IDENTIFICADA | (ver ELI) |
| [RD-ley 23/2020, de 23 de junio](https://www.boe.es/buscar/act.php?id=BOE-A-2020-6621) | AAP, AAC | REF-RDL23-2020 | MAPEO_CONTEXTO | BOE-A-2020-6621 |
| [RD-ley 6/2022, de 29 de marzo](https://www.boe.es/buscar/act.php?id=BOE-A-2022-4972) | AAP, AAC | REF-RDL6-2022 | EXTRAÍDA | BOE-A-2022-4972 |
| [RD-ley 20/2022, de 27 de diciembre](https://www.boe.es/buscar/act.php?id=BOE-A-2022-22685) | AAP, AAC | REF-RDL20-2022 | EXTRAÍDA | BOE-A-2022-22685 |
| [RD-ley 8/2023, de 27 de diciembre](https://www.boe.es/buscar/act.php?id=BOE-A-2023-26452) | AAP, AAC | REF-RDL23-2020 | EXTRAÍDA | BOE-A-2023-26452 |
| [RD-ley 7/2025, de 24 de junio](https://www.boe.es/buscar/act.php?id=BOE-A-2025-12857) | — | REF-RDL7-2025 | OBSOLETA | BOE-A-2025-12857 |
| RD 997/2025 | — | REF-RDL7-2025 | OBSOLETA | pendiente — ⚠️ verificar existencia |
| [RD 1183/2020, de 29 de diciembre](https://www.boe.es/eli/es/rd/2020/12/29/1183/con) | AAP, AAC | REF-RD1183 | MAPEO_CONTEXTO | BOE-A-2020-17278 |
| [RD-ley 7/2026, de 20 de marzo](https://www.boe.es/buscar/act.php?id=BOE-A-2026-6544) | AAP, AAC | — | IDENTIFICADA | BOE-A-2026-6544 |
| [Resolución CNMC de 27 de junio de 2024](https://www.boe.es/buscar/doc.php?id=BOE-A-2024-13823) | AAP, AAC | REF-CNMC-2024 | IDENTIFICADA | BOE-A-2024-13823 |
| [RD 413/2014, de 6 de junio](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2014-6123) | AAC, AE | — | — | — |
| [RD 1699/2011, de 18 de noviembre](https://www.boe.es/buscar/doc.php?id=BOE-A-2011-19242) | AE | — | IDENTIFICADA | BOE-A-2011-19242 |
| [RD 2019/1997, de 26 de diciembre](https://www.boe.es/buscar/act.php?id=BOE-A-1997-27817) | AE | — | IDENTIFICADA | BOE-A-1997-27817 |
| [Resolución de 30 de abril de 2018 (BOJA 2018/88)](https://www.juntadeandalucia.es/boja/2018/88/BOJA18-088-00015-7901-01_00135302.pdf) | General | — | IDENTIFICADA | sin consolidar |
| [Resolución de 28 de septiembre de 2023 (pdf)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/10/Resolucion_de_28_de_septiembre_de_2023.pdf) | AE | — | IDENTIFICADA | sin consolidar |
| [RD 960/2020, de 3 de noviembre](https://www.boe.es/buscar/doc.php?id=BOE-A-2020-13591) | AAP, AAC | — | IDENTIFICADA | BOE-A-2020-13591 |

#### Recursos de referencia (MITECO)

| Recurso | Observaciones |
|---|---|
| [Preguntas frecuentes sobre acceso y conexión (MITECO)](https://www.miteco.gob.es/es/energia/energia-electrica/electricidad/preguntas-frecuentes-acceso-conexion.html) | FAQ sobre RD 1183/2020. |
| [Preguntas frecuentes sobre renovables (MITECO)](https://www.miteco.gob.es/es/energia/renovables/preguntas-frecuentes.html) | FAQ sobre RRE y REER. |
| [Registros y aplicación ERIDE (MITECO)](https://www.miteco.gob.es/es/energia/renovables/registro.html) | Registro de régimen retributivo específico y registro electrónico REER. |

---

### 6.3 Autoconsumo

Normas no recogidas en §6.1 ni §6.2, identificadas en la [página de autoconsumo](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/autoconsumo.html) y en la ficha de procedimiento [18494](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/18494.html) (Registro de autoconsumo):

> **Régimen según potencia instalada:**
> - **≤ 500 kW** — legalización mediante ficha técnica BT en el aplicativo PUES (salvo excepciones de la DA única DL 2/2018). Sin AAP ni AAC.
> - **> 500 kW** — obligatoria la tramitación de AAP + AAC + AE del art. 53 LSE, vía fichas del catálogo general (§6.1).

| Norma | Afecta a | ID-REF | Estado | ID técnico |
|---|---|---|---|---|
| [RD 244/2019, de 5 de abril](https://www.boe.es/buscar/act.php?id=BOE-A-2019-5089) | AE | — | IDENTIFICADA | BOE-A-2019-5089 |
| [RD-ley 29/2021, de 21 de diciembre](https://www.boe.es/eli/es/rdl/2021/12/21/29/con) | AE | — | IDENTIFICADA | (ver ELI) |
| [Resolución de 21 de julio de 2022 (CNMC)](https://www.boe.es/diario_boe/txt.php?id=BOE-B-2022-23914) | AE | — | IDENTIFICADA | BOE-B-2022-23914 |
| [Resolución de 28 de septiembre de 2023 (pdf)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/10/Resolucion_de_28_de_septiembre_de_2023.pdf) | AE | — | IDENTIFICADA | sin consolidar |
| [RD-ley 15/2018, de 5 de octubre](https://www.boe.es/buscar/act.php?id=BOE-A-2018-13593) | AE | — | IDENTIFICADA | BOE-A-2018-13593 |

#### Documentos de apoyo (no normativa)

| Documento | Observaciones |
|---|---|
| [Manual SGE tramitación autoconsumo (noviembre 2025, pdf)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2025/11/MANUAL_tramitacion_autoconsumo_noviembre_2025.pdf) | Guía completa de la Secretaría General de Energía para tramitar autorizaciones de autoconsumo en Andalucía. Referencia práctica de primer orden. |
| [Configuraciones de instalaciones de autoconsumo (pdf)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/12/Configuraciones_instalaciones_autoconsumo_V2.pdf) | Esquemas de las configuraciones posibles (con/sin excedentes, colectivo, etc.). |
| [Configuraciones de conexión planta–consumo no colindantes (marzo 2025, pdf)](https://www.juntadeandalucia.es/sites/default/files/2025-03/Configuraciones_conexion.pdf) | Para instalaciones en las que la planta de generación y el punto de consumo no están en el mismo emplazamiento. |
| [Preguntas frecuentes sobre autoconsumo (MITECO)](https://www.miteco.gob.es/es/energia/energia-electrica/electricidad/autoconsumo-electrico/preguntas-frecuentes-autoconsumo.html) | FAQ estatal sobre modalidades, registro y trámites de autoconsumo. |
