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
| [§3](#3-qué-extraer-por-tipo-de-solicitud) | Qué extraer por tipo de solicitud — variables y excepciones | Guía de extracción (investigación) |
| [§4](#4-formato-de-documentación-de-reglas) | Formato de documentación de reglas — plantilla | Guía de trabajo (investigación) |
| [§5](#5-resultados-por-iteración) | Resultados por iteración — estado de avance | Log de progreso |
| [§6](#6-fuentes-normativas-por-ámbito--junta-de-andalucía) | **Catálogo normativo completo** — todas las normas ordenadas por ámbito | **Fuente de verdad normativa** |
| [§6.1](#61-energía-eléctrica--distribución-y-transporte) | Energía eléctrica — distribución y transporte (Junta + BOE) | Catálogo normativo |
| [§6.2](#62-energías-renovables) | Energías renovables (Junta + BOE) | Catálogo normativo |
| [§6.3](#63-autoconsumo) | Autoconsumo (Junta + BOE) | Catálogo normativo |

> **Nota de uso:** Los documentos derivados (`NORMATIVA_PLAZOS.md`, `NORMATIVA_SOLICITUDES.md`, `DISEÑO_MOTOR_REGLAS.md`) deben referenciar §6.x como punto de entrada al catálogo normativo. Las secciones §3–§5 son andamiaje del proceso de investigación, no fuente de verdad.

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

## 3. Qué extraer por tipo de solicitud

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

## 4. Formato de documentación de reglas

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

## 5. Resultados por iteración

Los resultados se distribuyen en documentos propios, siguiendo el patrón de `NORMATIVA_PLAZOS.md`:

| Iteración | Documento | Estado |
|---|---|---|
| **1** — Mapa procedimental | `docs/NORMATIVA_MAPA_PROCEDIMENTAL.md` | En curso |
| **2+4** — Excepciones, regímenes especiales y casos límite | `docs/NORMATIVA_EXCEPCIONES_AT.md` | En curso |
| **3** — Plazos y silencio administrativo | `docs/NORMATIVA_PLAZOS.md §2` | En curso |

### Iteración 3 — Plazos (ver NORMATIVA_PLAZOS.md)
- §1 LPACAP 39/2015 — ✅ completo (sesión 2026-04-01)
- §2.1 LSE 24/2013 — ✅ completo (sesión 2026-04-02)
- §2.2 RD 1955/2000 — ✅ completo (sesión 2026-04-02)
- §2.3+ Resto de normas sectoriales — pendiente

---

## 6. Fuentes normativas por ámbito — Junta de Andalucía

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

| Norma | Afecta a | Observaciones |
|---|---|---|
| [Ley 24/2013, de 26 de diciembre (LSE)](https://www.boe.es/eli/es/l/2013/12/26/24/con) | General | **Marco legal del sector eléctrico.** Define los tipos de autorización (AAP, AAC, AE), el régimen de silencio (desestimatorio) y el reparto competencial AGE/CCAA. Ver `NORMATIVA_PLAZOS.md §2.1`. |
| [RD 1955/2000, de 1 de diciembre](https://www.boe.es/eli/es/rd/2000/12/01/1955/con) | AAP, AAC, AE, Trans., Cierre | **Norma procedimental principal.** Regula el procedimiento de autorización de instalaciones eléctricas. Ver `NORMATIVA_PLAZOS.md §2.2` para plazos detallados. |
| [Ley 39/2015, de 1 de octubre (LPACAP)](https://www.boe.es/eli/es/l/2015/10/01/39/con) | General | Procedimiento administrativo común. Plazos, notificaciones, silencio administrativo. Actúa como fallback cuando la norma sectorial no fija plazo. Ver `NORMATIVA_PLAZOS.md §1` para detalle completo. |
| [Ley 21/2013, de 9 de diciembre (EIA)](https://www.boe.es/eli/es/l/2013/12/09/21/con) | AAP | Evaluación de Impacto Ambiental. Afecta a la fase de consultas y al pronunciamiento ambiental previo a la resolución de la AAP. Plazos pendientes de extracción — ver `NORMATIVA_PLAZOS.md §2` (pendiente). |
| [RD 842/2002, de 2 de agosto (REBT)](https://www.boe.es/eli/es/rd/2002/08/02/842/con) | AE · BT | Reglamento Electrotécnico de Baja Tensión. Aplica a instalaciones BT incluidas en expedientes de renovables y autoconsumo (certificado de instalador). |
| [Decreto 9/2011, de 18 de enero](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=22168) | AAP, AAC | Modifica procedimientos administrativos de industria y energía para agilizar trámites. Contiene excepciones relevantes al procedimiento estándar. Pendiente de revisar. |
| [Decreto-ley 26/2021, de 14 de diciembre](https://www.boe.es/buscar/act.php?id=BOJA-b-2021-90434) | General | Simplificación administrativa y mejora de la calidad regulatoria. DF 4ª: exención de información pública para instalaciones sin DUP y sin AAU (ver DISEÑO_MOTOR_REGLAS.md, regla INICIAR INFORMACION_PUBLICA). Pendiente de revisar resto del articulado. |
| [RD 337/2014, de 9 de mayo (RAT)](https://www.boe.es/eli/es/rd/2014/05/09/337/con) | AAP, AAC, AE, Trans., Cierre | Reglamento de condiciones técnicas y garantías en instalaciones AT e ITCs RAT 01-23. Incide en documentación técnica de solicitudes. |
| [RD 223/2008, de 15 de febrero](https://www.boe.es/eli/es/rd/2008/02/15/223/con) | AAP, AAC, AE, Trans., Cierre | Reglamento de condiciones técnicas y garantías en líneas eléctricas AT e ITCs LAT 01-09. |
| [Decreto 356/2010, de 3 de agosto — AAU](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=21892) | AAP, Cierre | Autorización ambiental unificada autonómica; aplica cuando la instalación está sometida a prevención ambiental de la Junta. |
| [Decreto-ley 2/2018, de 26 de junio — Simplificación energía y renovables](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=26974) | AAP, AAC, Trans., Cierre | Puede modificar trámites o umbrales del procedimiento estándar. Pendiente de revisar. |
| [RD 413/2014, de 6 de junio](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2014-6123) | AAC, AE, Trans., Cierre | Regula la actividad de producción de energía eléctrica a partir de fuentes renovables, cogeneración y residuos. |
| [RD 917/2025, de 15 de octubre](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-20694) | AAC, AE | Modifica el RD 413/2014. Pendiente de revisar alcance concreto sobre requisitos de tramitación. |
| [Resolución de 9 de marzo de 2016 — Delegación de competencias a las DTs](http://juntadeandalucia.es/boja/2016/51/23) | General | **Clave para BDDAT:** título habilitante por el que las Delegaciones Territoriales tramitan y resuelven los expedientes. |
| [Instrucción 1/2023, de 11 de julio — SGE AT (pdf)](https://www.juntadeandalucia.es/sites/default/files/2023-10/7_20230711_INSTRUCCI%C3%93N%201-2023%20de%20SGE%20AT(F).pdf) | General | Instrucción interna de la Secretaría General de Energía sobre tramitación AT. Pendiente de revisar. |
| [Instrucción Conjunta 1/2022 — SGE + DGSAyCC (pdf)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2022/10/INSTRUCCION_CONJUNTA_1_2022_SGE_DGSAyCC_F_F.pdf) | AAP | Conjunta con la Dirección General de Sostenibilidad Ambiental y Cambio Climático. Relevante para trámites EIA. Pendiente de revisar. |
| [Resolución de 13 de octubre de 2023 — Formulario de solicitud](https://www.juntadeandalucia.es/eboja/2023/206/BOJA23-206-00006-16391-01_00291369.pdf) | General | Aprueba el formulario oficial de solicitud de autorizaciones eléctricas de Andalucía. |
| [Corrección de errores — Resolución 13 octubre 2023](https://www.juntadeandalucia.es/eboja/2023/233/BOJA23-233-00005-18542-01_00293610.pdf) | General | — |
| [Decreto-ley 3/2024, de 6 de febrero — Simplificación administrativa](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=35380) | General | Medidas de simplificación y racionalización; puede afectar trámites. Pendiente de revisar. |
| [Decreto-ley 4/2024, de 27 de febrero — Modifica DL 3/2024](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=35417) | General | — |
| [Ley 4/2025, de 15 de diciembre — Espacios productivos](https://www.boe.es/buscar/doc.php?id=BOE-A-2026-422) | AAP, AAC, AE | **Ley de espacios productivos para el fomento de la industria en Andalucía.** Art. 42: tramitación simplificada de renovables en espacios productivos. Art. 43: declaración de utilidad pública de líneas eléctricas en polígonos. Arts. 59–61: autoconsumo industrial, líneas directas de un solo titular, redes cerradas. DA 7ª: simplificación de acometidas eléctricas y líneas directas de autoconsumo para un único titular. DA 12ª: almacenamiento electroquímico hibridado en instalaciones autonómicas. Pendiente de revisar articulado completo. |
| [Decreto 59/2005 (BOJA 2005/118)](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=17891) | AE · BT | Certificados de instalaciones de BT en el ámbito de renovables. |
| [Orden de 5 de marzo de 2013 (BOJA 2013/48)](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=29083) | AE · BT | Normas de desarrollo del Decreto 59/2005. Modificada por Resoluciones de 2015, 2019, 2020, 2022, 2023 y 2026. Ver versión consolidada. |
| [Resolución de 23 de marzo de 2026 — Ficha técnica AT](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=40778) | AE | Modifica la ficha técnica descriptiva de **alta tensión** del Anexo II de la Orden de 5/3/2013. Relevante para la AE de instalaciones AT en BDDAT. |
| [Orden de 24 de octubre de 2005 (BOJA 2005/217)](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=18144) | AE · BT | — |
| [Resolución de 9 de mayo de 2024 (BOJA 2024/95/52)](https://www.juntadeandalucia.es/boja/2024/95/52) | AE · BT | — |
| [Modelo certificado instalación BT (pdf rellenable)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/02/140223_Certificado_BT_rellenable_mod.pdf) | AE · BT | Modelo oficial de certificado de instalador para BT. |

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

| Norma | Afecta a | Observaciones |
|---|---|---|
| [Ley 2/2007, de 27 de marzo](https://www.boe.es/eli/es-an/l/2007/03/27/2/con) | General | **Marco legal autonómico de renovables.** Fomento de energías renovables y ahorro y eficiencia energética en Andalucía. |
| [RD-ley 23/2020, de 23 de junio](https://www.boe.es/buscar/act.php?id=BOE-A-2020-6621) | AAP, AAC | Establece hitos administrativos para instalaciones de energías renovables; condiciona la admisión a trámite de solicitudes según disponibilidad de punto de acceso/conexión. |
| [RD-ley 6/2022, de 29 de marzo](https://www.boe.es/buscar/act.php?id=BOE-A-2022-4972) | AAP, AAC | Crisis Ucrania. Arts. 14-20: tramitación **conjunta AAP+AAC** para renovables, determinación de afección ambiental simplificada en zonas de sensibilidad baja/moderada (eólica ≤75 MW, fotovoltaica ≤150 MW), reducción de plazos por urgencia de interés público (art. 33 Ley 39/2015). |
| [RD-ley 20/2022, de 27 de diciembre](https://www.boe.es/buscar/act.php?id=BOE-A-2022-22685) | AAP, AAC, AE | Crisis Ucrania/La Palma. Arts. 34-38: procedimiento de determinación de afección ambiental simplificada para renovables (excl. Red Natura 2000), tramitación y resolución conjunta AAP+AAC acumulando información pública, suspensión de tramitación de proyectos especulativos en nudos de concurso sin permiso de acceso/conexión. |
| [RD-ley 8/2023, de 27 de diciembre](https://www.boe.es/buscar/act.php?id=BOE-A-2023-26452) | AAP, AAC | Modifica el régimen de hitos administrativos del RD-ley 23/2020. Pendiente de revisar alcance concreto. |
| [RD-ley 7/2025, de 24 de junio](https://www.boe.es/buscar/act.php?id=BOE-A-2025-12857) | AAP, AAC, AE | Refuerzo del sistema eléctrico. Art. 9: almacenamiento hibridado — tramitación conjunta AAP+AAC, plazos de información pública reducidos a la mitad, exención de nueva EIA si el proyecto original la tenía. Art. 11: repotenciación — plazos a la mitad, EIA solo sobre impacto diferencial. Modifica RD 1955/2000 y RD 1183/2020. |
| [RD 1183/2020, de 29 de diciembre](https://www.boe.es/eli/es/rd/2020/12/29/1183/con) | AAP, AAC | Regula el acceso y la conexión a la red eléctrica de transporte y distribución. Determina si la instalación tiene punto de acceso/conexión concedido — requisito para admisión a trámite. |
| [RD 413/2014, de 6 de junio](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2014-6123) | AAC, AE | → Ver §6.1 |
| [RD 1699/2011, de 18 de noviembre](https://www.boe.es/buscar/doc.php?id=BOE-A-2011-19242) | AE | Regula la conexión a red de instalaciones de producción de pequeña potencia (autoconsumo y mini-generación). |
| [RD 2019/1997, de 26 de diciembre](https://www.boe.es/buscar/act.php?id=BOE-A-1997-27817) | AE | Organiza y regula el mercado de producción de energía eléctrica. Norma de 1997; en vigor con modificaciones. Pendiente de revisar vigencia real en el contexto actual. |
| [Resolución de 30 de abril de 2018 (BOJA 2018/88)](https://www.juntadeandalucia.es/boja/2018/88/BOJA18-088-00015-7901-01_00135302.pdf) | General | Pendiente de identificar objeto. |
| [Resolución de 28 de septiembre de 2023 (pdf)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/10/Resolucion_de_28_de_septiembre_de_2023.pdf) | AE | De la SGE. Aprueba la ficha técnica PUES para legalización de autoconsumo ≤ 500 kW. → Ver §6.3. |
| [RD 960/2020, de 3 de noviembre](https://www.boe.es/buscar/doc.php?id=BOE-A-2020-13591) | AAP, AAC | Regula el régimen económico de energías renovables (REER). Marco económico de instalaciones renovables; puede condicionar admisión a trámite. Pendiente de revisar alcance concreto. |

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

| Norma | Afecta a | Observaciones |
|---|---|---|
| [RD 244/2019, de 5 de abril](https://www.boe.es/buscar/act.php?id=BOE-A-2019-5089) | AE | **Norma central del autoconsumo.** Regula las condiciones administrativas, técnicas y económicas del autoconsumo de energía eléctrica. Establece el Registro de Autoconsumo. |
| [RD-ley 29/2021, de 21 de diciembre](https://www.boe.es/eli/es/rdl/2021/12/21/29/con) | AE | Modifica el régimen de autoconsumo; amplía supuestos y simplifica trámites. Pendiente de revisar alcance concreto. |
| [Resolución de 21 de julio de 2022 (CNMC)](https://www.boe.es/diario_boe/txt.php?id=BOE-B-2022-23914) | AE | De la Comisión Nacional de los Mercados y la Competencia. Establece la flexibilización del flujo de contratación para autoconsumo conectado en BT con generación < 100 kW (en vigor desde 30/01/2023). |
| [Resolución de 28 de septiembre de 2023 (pdf)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/10/Resolucion_de_28_de_septiembre_de_2023.pdf) | AE | De la Secretaría General de Energía. Aprueba la ficha técnica descriptiva de baja tensión del aplicativo PUES — documento de legalización para autoconsumo ≤ 500 kW. → Ver también §6.2. |
| [RD-ley 15/2018, de 5 de octubre](https://www.boe.es/buscar/act.php?id=BOE-A-2018-13593) | AE | Modifica el art. 9 de la Ley 24/2013 (definición y modalidades de autoconsumo: sin excedentes, con excedentes individual/colectivo). |

#### Documentos de apoyo (no normativa)

| Documento | Observaciones |
|---|---|
| [Manual SGE tramitación autoconsumo (noviembre 2025, pdf)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2025/11/MANUAL_tramitacion_autoconsumo_noviembre_2025.pdf) | Guía completa de la Secretaría General de Energía para tramitar autorizaciones de autoconsumo en Andalucía. Referencia práctica de primer orden. |
| [Configuraciones de instalaciones de autoconsumo (pdf)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/12/Configuraciones_instalaciones_autoconsumo_V2.pdf) | Esquemas de las configuraciones posibles (con/sin excedentes, colectivo, etc.). |
| [Configuraciones de conexión planta–consumo no colindantes (marzo 2025, pdf)](https://www.juntadeandalucia.es/sites/default/files/2025-03/Configuraciones_conexion.pdf) | Para instalaciones en las que la planta de generación y el punto de consumo no están en el mismo emplazamiento. |
| [Preguntas frecuentes sobre autoconsumo (MITECO)](https://www.miteco.gob.es/es/energia/energia-electrica/electricidad/autoconsumo-electrico/preguntas-frecuentes-autoconsumo.html) | FAQ estatal sobre modalidades, registro y trámites de autoconsumo. |
