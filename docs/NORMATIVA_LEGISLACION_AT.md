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
| [§6](#6-recursos-de-navegación-y-fichas-de-la-junta-de-andalucía) | **Recursos de navegación** — links Consejería/MITECO, fichas de procedimiento y documentos de apoyo | Navegación (normas en `normas_catalog.csv`) |
| [§6.1](#61-energía-eléctrica--distribución-y-transporte) | Distribución y transporte — fichas de procedimiento y formulario VEA | Fichas de procedimiento |
| [§6.2](#62-energías-renovables) | Renovables — recursos de referencia MITECO | Recursos MITECO |
| [§6.3](#63-autoconsumo) | Autoconsumo — documentos de apoyo | Documentos de apoyo |

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

## 6. Recursos de navegación y fichas de la Junta de Andalucía

> **Catálogo de normas:** el inventario completo de legislación aplicable (estado, ID técnico, procedimientos, doc_extraccion) está en `docs/normas_catalog.csv`. Este §6 recoge únicamente recursos de navegación: links a las páginas de la Consejería y MITECO, fichas de procedimiento de la Junta y documentos de apoyo.

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

Fichas de procedimiento y formulario de solicitud de la Consejería de Industria, Energía y Minas:

#### Fichas de procedimiento — catálogo Junta de Andalucía

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

> La página de renovables no tiene fichas de procedimiento propias para AAP/AAC/AE — remite a las mismas fichas del catálogo general (§6.1). Lo específico de renovables es la normativa sectorial de producción y acceso a red (ver `normas_catalog.csv`).

#### Recursos de referencia (MITECO)

| Recurso | Observaciones |
|---|---|
| [Preguntas frecuentes sobre acceso y conexión (MITECO)](https://www.miteco.gob.es/es/energia/energia-electrica/electricidad/preguntas-frecuentes-acceso-conexion.html) | FAQ sobre RD 1183/2020. |
| [Preguntas frecuentes sobre renovables (MITECO)](https://www.miteco.gob.es/es/energia/renovables/preguntas-frecuentes.html) | FAQ sobre RRE y REER. |
| [Registros y aplicación ERIDE (MITECO)](https://www.miteco.gob.es/es/energia/renovables/registro.html) | Registro de régimen retributivo específico y registro electrónico REER. |

---

### 6.3 Autoconsumo

> **Régimen según potencia instalada:**
> - **≤ 500 kW** — legalización mediante ficha técnica BT en el aplicativo PUES (salvo excepciones de la DA única DL 2/2018). Sin AAP ni AAC.
> - **> 500 kW** — obligatoria la tramitación de AAP + AAC + AE del art. 53 LSE, vía fichas del catálogo general (§6.1).

#### Documentos de apoyo (no normativa)

| Documento | Observaciones |
|---|---|
| [Manual SGE tramitación autoconsumo (noviembre 2025, pdf)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2025/11/MANUAL_tramitacion_autoconsumo_noviembre_2025.pdf) | Guía completa de la Secretaría General de Energía para tramitar autorizaciones de autoconsumo en Andalucía. Referencia práctica de primer orden. |
| [Configuraciones de instalaciones de autoconsumo (pdf)](https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/12/Configuraciones_instalaciones_autoconsumo_V2.pdf) | Esquemas de las configuraciones posibles (con/sin excedentes, colectivo, etc.). |
| [Configuraciones de conexión planta–consumo no colindantes (marzo 2025, pdf)](https://www.juntadeandalucia.es/sites/default/files/2025-03/Configuraciones_conexion.pdf) | Para instalaciones en las que la planta de generación y el punto de consumo no están en el mismo emplazamiento. |
| [Preguntas frecuentes sobre autoconsumo (MITECO)](https://www.miteco.gob.es/es/energia/energia-electrica/electricidad/autoconsumo-electrico/preguntas-frecuentes-autoconsumo.html) | FAQ estatal sobre modalidades, registro y trámites de autoconsumo. |
