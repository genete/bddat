# NORMATIVA — Legislación aplicable al motor de reglas BDDAT

> **Fuente:** Legislación estatal y autonómica sobre instalaciones de alta tensión en Andalucía.
> **Aplica a:** Motor de reglas — base legal de las reglas de tramitación ESFTT.
> **Estado:** Catálogo de normas y estructura de extracción definida. Iteraciones de investigación pendientes.

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

## 2. Legislación base

### Nacional
- **RD 1955/2000**, de 1 de diciembre — Regula actividades de transporte, distribución,
  comercialización, suministro y procedimientos de autorización de instalaciones de energía
  eléctrica. **Norma procedimental principal.**
- **Ley 24/2013**, de 26 de diciembre — Ley del Sector Eléctrico. Marco legal de referencia.
- **Ley 39/2015**, de 1 de octubre — Procedimiento Administrativo Común. Plazos,
  notificaciones, silencio administrativo. → Ver `docs/NORMATIVA_PLAZOS.md` para detalle de arts. 21-25, 29-32 y 112-126.
- **Ley 40/2015** — Régimen Jurídico del Sector Público (procedimiento interadministrativo).
- **RD 842/2002** — Reglamento Electrotécnico de Baja Tensión. Aplica a instalaciones BT incluidas en expedientes de renovables (certificado de instalador).
- **Ley 21/2013** — Evaluación de Impacto Ambiental (EIA). Afecta a fases de consultas y
  pronunciamiento ambiental.

### Autonómica Andalucía
- **Decreto 9/2011**, de 18 de enero (BOJA nº 22) — Medidas para la agilización de trámites
  administrativos. Contiene excepciones relevantes al procedimiento estándar.
- **Ley 2/2007**, de 27 de marzo — Fomento de las Energías Renovables y del Ahorro y Eficiencia
  Energética de Andalucía.
- **Decreto 369/2010** y normas de desarrollo autonómico aplicables.
- **Decreto-ley 26/2021**, de 14 de diciembre — Simplificación administrativa. Incluye la
  Disposición Final Cuarta sobre exención de información pública para instalaciones sin DUP
  y sin AAU (ver DISEÑO_MOTOR_REGLAS.md, regla INICIAR INFORMACION_PUBLICA).

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

*(Se completarán en sesiones de trabajo dedicadas — ver issue #250 para planificación)*

### Iteración 1 — Mapa de alto nivel
Para cada tipo de solicitud estándar (AAP, AAC, APO, DUP):
qué fases son obligatorias según RD 1955/2000 y cuáles son los plazos.

### Iteración 2 — Excepciones y regímenes especiales
Generación renovable, instalaciones < 30 kV.

### Iteración 3 — Plazos y silencio administrativo
→ En curso. Ver `docs/NORMATIVA_PLAZOS.md` para extracción detallada por norma.
- §1 LPACAP 39/2015 — completo (sesión 2026-04-01)
- §2.1 LSE 24/2013 — completo (sesión 2026-04-02)
- §2.2 RD 1955/2000 — completo (sesión 2026-04-02)

### Iteración 4 — Casos límite y casuística especial

---

## 6. Fuentes normativas por ámbito — Junta de Andalucía

Páginas de referencia de la Consejería de Industria, Energía y Minas:

| Ámbito |
|---|
| [Energía eléctrica (distribución y transporte)](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/electricidad.html) |
| [Energías renovables](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/renovables.html) |

---

### 6.1 Energía eléctrica — distribución y transporte

Normas no recogidas en §2, identificadas en la página de la Consejería y en las fichas de procedimiento:

> **Glosario:** AAP = Autorización Administrativa Previa · AAC = Autorización Administrativa de Construcción · AE = Autorización de Explotación · Trans. = Transmisión de titularidad · Cierre = Autorización de cierre · BT = instalaciones de baja tensión (en renovables) · General = todos los procedimientos / marco competencial

| Norma | Afecta a | Observaciones |
|---|---|---|
| [RD 337/2014, de 9 de mayo (RAT)](https://www.boe.es/eli/es/rd/2014/05/09/337/con) | AAP, AAC, AE, Trans., Cierre | Reglamento de condiciones técnicas y garantías en instalaciones AT e ITCs RAT 01-23. Incide en documentación técnica de solicitudes. |
| [RD 223/2008, de 15 de febrero](https://www.boe.es/eli/es/rd/2008/02/15/223/con) | AAP, AAC, AE, Trans., Cierre | Reglamento de condiciones técnicas y garantías en líneas eléctricas AT e ITCs LAT 01-09. |
| [Decreto 356/2010, de 3 de agosto — AAU](http://www.juntadeandalucia.es/boja/2010/157/d2.pdf) | AAP, Cierre | Autorización ambiental unificada autonómica; aplica cuando la instalación está sometida a prevención ambiental de la Junta. |
| [Decreto-ley 2/2018, de 26 de junio — Simplificación energía y renovables](https://www.juntadeandalucia.es/eboja/2018/127/BOJA18-127-00006-11489-01_00138802.pdf) | AAP, AAC, Trans., Cierre | Puede modificar trámites o umbrales del procedimiento estándar. Pendiente de revisar. |
| [RD 413/2014, de 6 de junio](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2014-6123) | AAC, AE, Trans., Cierre | Regula la actividad de producción de energía eléctrica a partir de fuentes renovables, cogeneración y residuos. |
| [Resolución de 9 de marzo de 2016 — Delegación de competencias a las DTs](http://juntadeandalucia.es/boja/2016/51/23) | General | **Clave para BDDAT:** título habilitante por el que las Delegaciones Territoriales tramitan y resuelven los expedientes. |
| [Instrucción 1/2023, de 11 de julio — SGE AT (pdf)](https://www.juntadeandalucia.es/sites/default/files/2023-10/7_20230711_INSTRUCCI%C3%93N%201-2023%20de%20SGE%20AT(F).pdf) | General | Instrucción interna de la Secretaría General de Energía sobre tramitación AT. Pendiente de revisar. |
| [Instrucción Conjunta 1/2022 — SGE + DGSAyCC (pdf)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2022/10/INSTRUCCION_CONJUNTA_1_2022_SGE_DGSAyCC_F_F.pdf) | AAP | Conjunta con la Dirección General de Sostenibilidad Ambiental y Cambio Climático. Relevante para trámites EIA. Pendiente de revisar. |
| [Resolución de 13 de octubre de 2023 — Formulario de solicitud](https://www.juntadeandalucia.es/eboja/2023/206/BOJA23-206-00006-16391-01_00291369.pdf) | General | Aprueba el formulario oficial de solicitud de autorizaciones eléctricas de Andalucía. |
| [Corrección de errores — Resolución 13 octubre 2023](https://www.juntadeandalucia.es/eboja/2023/233/BOJA23-233-00005-18542-01_00293610.pdf) | General | — |
| [Decreto-ley 3/2024, de 6 de febrero — Simplificación administrativa](https://www.juntadeandalucia.es/eboja/2024/34/index.html) | General | Medidas de simplificación y racionalización; puede afectar trámites. Pendiente de revisar. |
| [Decreto-ley 4/2024, de 27 de febrero — Modifica DL 3/2024](https://www.boe.es/ccaa/boja/2024/044/b00001-00005.pdf) | General | — |
| [Decreto 59/2005 (BOJA 2005/118)](https://www.juntadeandalucia.es/boja/2005/118/3) | AE · BT | Certificados de instalaciones de BT en el ámbito de renovables. |
| [Orden de 5 de marzo de 2013 (BOJA 2013/48)](https://www.juntadeandalucia.es/boja/2013/48/1) | AE · BT | — |
| [Orden de 24 de octubre de 2005 (BOJA 2005/217)](https://www.juntadeandalucia.es/boja/2005/217/4) | AE · BT | — |
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

Normas no recogidas en §2 ni en §6.1, identificadas en la [página de renovables](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/renovables.html) y en la ficha de procedimiento [12083](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/12083.html) (Registro de instalaciones de producción):

> La página de renovables no tiene fichas de procedimiento propias para AAP/AAC/AE — remite a las mismas fichas del catálogo general (§6.1). Lo específico de renovables es la normativa sectorial de producción y acceso a red.

| Norma | Afecta a | Observaciones |
|---|---|---|
| [RD-ley 23/2020, de 23 de junio](https://www.boe.es/buscar/act.php?id=BOE-A-2020-6621) | AAP, AAC | Establece hitos administrativos para instalaciones de energías renovables; condiciona la admisión a trámite de solicitudes según disponibilidad de punto de acceso/conexión. |
| [RD-ley 8/2023, de 27 de diciembre](https://www.boe.es/buscar/act.php?id=BOE-A-2023-26452) | AAP, AAC | Modifica el régimen de hitos administrativos del RD-ley 23/2020. Pendiente de revisar alcance concreto. |
| [RD 1183/2020, de 29 de diciembre](https://www.boe.es/eli/es/rd/2020/12/29/1183/con) | AAP, AAC | Regula el acceso y la conexión a la red eléctrica de transporte y distribución. Determina si la instalación tiene punto de acceso/conexión concedido — requisito para admisión a trámite. |
| [RD 413/2014, de 6 de junio](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2014-6123) | AAC, AE | → Ver §6.1 |
| [RD 1699/2011, de 18 de noviembre](https://www.boe.es/buscar/doc.php?id=BOE-A-2011-19242) | AE | Regula la conexión a red de instalaciones de producción de pequeña potencia (autoconsumo y mini-generación). |
| [RD 2019/1997, de 26 de diciembre](https://www.boe.es/buscar/act.php?id=BOE-A-1997-27817) | AE | Organiza y regula el mercado de producción de energía eléctrica. Norma de 1997; en vigor con modificaciones. Pendiente de revisar vigencia real en el contexto actual. |
| [Resolución de 30 de abril de 2018 (BOJA 2018/88)](https://www.juntadeandalucia.es/boja/2018/88/BOJA18-088-00015-7901-01_00135302.pdf) | General | Pendiente de identificar objeto. |
| [Resolución de 28 de septiembre de 2023 (pdf)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/10/Resolucion_de_28_de_septiembre_de_2023.pdf) | General | Pendiente de identificar objeto. |
