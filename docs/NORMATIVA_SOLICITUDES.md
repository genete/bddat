# NORMATIVA — Tipos de solicitud como entidades del dominio

> **Fuente:** Legislación de tramitación AT en Andalucía (RD 1955/2000, Ley 24/2013 y desarrollo autonómico).
> **Aplica a:** Modelo `tipos_solicitudes`, motor de reglas, whitelist ESFTT, plantillas de escritos.
> **Decisión de implementación:** Issue #167 Fase 1.

---

## Tipos atómicos de solicitud

| Siglas | Nombre completo | Descripción |
|--------|----------------|-------------|
| AAP | Autorización Administrativa Previa | Primera autorización del proyecto de instalación |
| AAC | Autorización Administrativa de Construcción | Autoriza la ejecución de las obras |
| APO | Autorización de Puesta en Operación | Autoriza la entrada en servicio de la instalación |
| DUP | Declaración de Utilidad Pública | Necesaria para la ocupación de terrenos privados |
| AAE_PROVISIONAL | Autorización de Explotación Provisional | Explotación temporal mientras se tramita la definitiva |
| AAE_DEFINITIVA | Autorización de Explotación Definitiva | Autorización final de explotación |
| AAT | Autorización de Transmisión de Titularidad | Cambio de titular de la instalación autorizada |
| MODIFICACION | Modificación de instalación autorizada | Modificación de características ya autorizadas |
| DESISTIMIENTO | Desistimiento | El solicitante renuncia a la tramitación en curso |
| RENUNCIA | Renuncia | El titular renuncia a derechos ya concedidos |
| RECURSO | Recurso | Recurso administrativo contra resolución |
| CIERRE | Cierre / Baja de instalación | Cierre definitivo de una instalación en servicio |
| RAIPEE_PREVIA | RAIPEE Previa | Resolución de Aptitud de Infraestructuras Previas |
| RAIPEE_DEFINITIVA | RAIPEE Definitiva | Requiere RAIPEE_PREVIA resuelta (ver motor de reglas) |

---

## Tipos combinados de solicitud

Las combinaciones legales son un número finito y cerrado. Se representan como
entidades propias en `tipos_solicitudes` (no como tabla puente M:N).

**Justificación:**
- Cada combinación tiene implicaciones procedimentales distintas (fases, texto de resoluciones)
- Las plantillas necesitan FK directa para saber qué texto administrativo usar
- Si aparece una nueva combinación legal, es un INSERT + actualización de whitelist

| Siglas | Descripción |
|--------|-------------|
| AAP_AAC | Autorización Administrativa Previa y de Construcción — tramitación conjunta estándar |
| AAP_AAC_DUP | AAP + AAC + Declaración de Utilidad Pública |
| AAP_AAC_AAU | AAP + AAC + Autorización Ambiental Unificada |
| AAP_AAC_AAU_DUP | AAP + AAC + AAU + Declaración de Utilidad Pública |
| AAC_DUP | AAC + Declaración de Utilidad Pública |
| AAE_DEFINITIVA_AAT | Explotación Definitiva + Transmisión de Titularidad |

---

## Tipos de expediente

Los tipos de expediente condicionan qué solicitudes y fases son aplicables
(whitelist `expedientes_solicitudes`).

| id | Tipo | Descripción |
|----|------|-------------|
| 1 | Transporte | Instalaciones de transporte (REE) |
| 2 | Distribución | Instalaciones de distribución |
| 3 | Distribución cedida | Distribución con cesión |
| 4 | Renovable | Instalaciones de generación renovable |
| 5 | Autoconsumo | Instalaciones de autoconsumo |
| 6 | LineaDirecta | Línea directa |
| 7 | Convencional | Generación convencional |
| 8 | Otros | Otros tipos |

---

## Reglas de compatibilidad entre tipos en una solicitud

Ver `docs/DISEÑO_MOTOR_REGLAS.md` — sección "Compatibilidad de tipos en una solicitud".

Ejemplos:
- `AAP + AAE` → PROHIBIDO (AAE implica instalación construida; AAP es anterior a la construcción)
- `DUP + CIERRE` → PROHIBIDO (DUP implica que no se pudo construir; CIERRE implica existente)
- `AAP + AAC` → PERMITIDO → representado como tipo combinado `AAP_AAC`
- `AAP + AAC + DUP` → PERMITIDO → representado como tipo combinado `AAP_AAC_DUP`

**Pendiente:** definir la lista completa de pares compatibles con el técnico del servicio
y poblar la tabla `tipos_solicitudes_compatibles`.
