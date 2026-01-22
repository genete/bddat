### TIPOS_SOLICITUDES (Actualización v3.0)

Tipos **individuales** de actos administrativos solicitables. Las combinaciones se gestionan mediante tabla puente `SOLICITUDES_TIPOS`.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del tipo de solicitud | NO | PK, autoincremental |
| **SIGLAS** | VARCHAR(100) | Siglas o código del tipo de solicitud | SÍ | Abreviatura normalizada: AAP, AAC, DUP, AAE_PROVISIONAL, AAE_DEFINITIVA, RAIPEE_PREVIA, RAIPEE_DEFINITIVA, RADNE, etc. |
| **DESCRIPCION** | VARCHAR(200) | Descripción completa del tipo de solicitud | SÍ | Denominación legal del acto administrativo solicitado |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `SIGLAS` (recomendado para evitar duplicados)

#### Índices Recomendados

- `SIGLAS` (búsqueda rápida por código)

#### Notas de Versión

- **v3.0:** **CAMBIO DE FILOSOFÍA**. Ahora contiene **17 tipos individuales** en lugar de 20+ tipos combinados hardcodeados.
- **v3.0:** Tipos combinados (AAP+AAC, AAP+DUP, etc.) se gestionan mediante tabla puente `SOLICITUDES_TIPOS` (relación N:M).
- **v3.0:** Incorporadas novedades normativas: RDL 7/2025 (AAE dividida), RD 244/2019 (RADNE autoconsumo Andalucía), RD 413/2014 (RAIPEE renovables).

#### Filosofía v3.0: Tipos Individuales

**Cambio conceptual:**

- **Antes (v2.0):** Tipos combinados hardcodeados
  - AAP (ID=1)
  - AAC (ID=2)
  - AAP+AAC (ID=3)
  - AAP+DUP (ID=4)
  - AAC+DUP (ID=5)
  - AAP+AAC+DUP (ID=6)
  - AAE+AAT (ID=9)
  - ... hasta 20+ tipos

- **Ahora (v3.0):** Tipos individuales + tabla puente
  - AAP (ID=1)
  - AAC (ID=2)
  - DUP (ID=3)
  - AAE_PROVISIONAL (ID=4)
  - AAE_DEFINITIVA (ID=5)
  - ... hasta 17 tipos
  - Combinaciones mediante `SOLICITUDES_TIPOS`

**Ventajas:**

1. **Flexibilidad:** Cualquier combinación posible sin modificar maestras
2. **Escalabilidad:** Nuevos tipos se añaden una sola vez
3. **Mantenibilidad:** 17 tipos vs 20+ combinaciones
4. **Adaptabilidad normativa:** RDL 7/2025 implementado sin reestructuración
5. **Estadísticas precisas:** Conteo individual de cada tipo

#### Catálogo de Tipos Individuales (17 tipos)

##### 1. Fase PREVIA (art. 53.1.a LSE 24/2013)

| ID | Siglas | Descripción | Base Legal |
|:---|:---|:---|:---|
| 1 | **AAP** | Autorización Administrativa Previa | art. 53.1.a LSE 24/2013 |

**Nota:** Fase inicial que autoriza el proyecto técnico y la inversión. Necesaria antes de construcción.

##### 2. Fase CONSTRUCCIÓN (art. 53.1.b LSE)

| ID | Siglas | Descripción | Base Legal |
|:---|:---|:---|:---|
| 2 | **AAC** | Autorización Administrativa de Construcción | art. 53.1.b LSE 24/2013 |

**Nota:** Autoriza la ejecución de las obras. Requiere AAP previa concedida.

##### 3. Declaración Utilidad Pública (art. 54 LSE)

| ID | Siglas | Descripción | Base Legal |
|:---|:---|:---|:---|
| 3 | **DUP** | Declaración de Utilidad Pública | art. 54 LSE 24/2013 |

**Nota:** Habilita expropiación forzosa y ocupación de dominio público. Solo para instalaciones de transporte y distribución de interés general.

##### 4. Fase EXPLOTACIÓN (art. 53.1.c LSE - dividida desde RDL 7/2025)

| ID | Siglas | Descripción | Base Legal | Novedad |
|:---|:---|:---|:---|:---|
| 4 | **AAE_PROVISIONAL** | Autorización de Explotación Provisional para Pruebas | art. 53.1.c LSE + RDL 7/2025 | ✅ **Nueva 2025** |
| 5 | **AAE_DEFINITIVA** | Autorización de Explotación Definitiva | art. 53.1.c LSE + RDL 7/2025 | ✅ **Nueva 2025** |

**Cambio RDL 7/2025:** La AAE se divide en:
- **AAE_PROVISIONAL:** Autoriza pruebas de funcionamiento (máximo 6 meses)
- **AAE_DEFINITIVA:** Autoriza explotación comercial permanente (requiere AAE_PROVISIONAL previa)

##### 5. Transmisión de Titularidad (art. 56 LSE)

| ID | Siglas | Descripción | Base Legal |
|:---|:---|:---|:---|
| 6 | **AAT** | Autorización de Transmisión de Titularidad | art. 56 LSE 24/2013 |

**Nota:** Cambio de titular de instalación autorizada. Requiere AAC o AAE previa.

##### 6. RAIPEE - Renovables Producción (RD 413/2014 art. 37-42)

| ID | Siglas | Descripción | Base Legal | Tipo Expediente |
|:---|:---|:---|:---|:---|
| 7 | **RAIPEE_PREVIA** | Inscripción Previa en RAIPEE | RD 413/2014 art. 37-39 | Renovable |
| 8 | **RAIPEE_DEFINITIVA** | Inscripción Definitiva en RAIPEE | RD 413/2014 art. 40-42 | Renovable |

**Uso exclusivo:** Instalaciones de generación renovable.

**Secuencia:**
1. **RAIPEE_PREVIA:** Antes o junto con AAP (reserva punto de conexión)
2. **RAIPEE_DEFINITIVA:** Junto con AAE_DEFINITIVA (instalación construida y probada)

##### 7. RADNE - Autoconsumo (RD 244/2019)

| ID | Siglas | Descripción | Base Legal | Ámbito | Novedad |
|:---|:---|:---|:---|:---|:---|
| 9 | **RADNE** | Inscripción en Registro de Autoconsumo | RD 244/2019 + Normativa autonómica | Andalucía: obligatorio AT | ✅ **Andalucía 2024** |

**Particularidad Andalucía:** Desde 2024, RADNE es **obligatorio** para instalaciones de autoconsumo en alta tensión (antes era voluntario o BT).

**Uso exclusivo:** Expedientes tipo `Autoconsumo`.

##### 8. Cierre de Instalación

| ID | Siglas | Descripción | Base Legal |
|:---|:---|:---|:---|
| 10 | **CIERRE** | Autorización de Cierre de Instalación | art. 53.1.d LSE 24/2013 |

**Nota:** Desmantelamiento definitivo de instalación autorizada.

##### 9. Actos sobre Solicitudes (art. 94 Ley 39/2015)

| ID | Siglas | Descripción | Base Legal | Campo especial |
|:---|:---|:---|:---|:---|
| 11 | **DESISTIMIENTO** | Desistimiento de la Solicitud | art. 94.1 Ley 39/2015 | `SOLICITUD_AFECTADA_ID` |
| 12 | **RENUNCIA** | Renuncia de la Autorización | art. 94.2 Ley 39/2015 | `SOLICITUD_AFECTADA_ID` |

**Nota:** Requieren campo `SOLICITUDES.SOLICITUD_AFECTADA_ID` NOT NULL apuntando a la solicitud que se desiste/renuncia.

##### 10. Gestión de Expedientes

| ID | Siglas | Descripción | Base Legal |
|:---|:---|:---|:---|
| 13 | **AMPLIACION_PLAZO** | Ampliación de Plazo de Ejecución | art. 32 Ley 39/2015 |
| 14 | **INTERESADO** | Condición de Interesado en el Expediente | art. 4 Ley 39/2015 |
| 15 | **RECURSO** | Recurso Administrativo | art. 112-126 Ley 39/2015 |

##### 11. Otros Procedimientos Administrativos

| ID | Siglas | Descripción | Base Legal |
|:---|:---|:---|:---|
| 16 | **CORRECCION_ERRORES** | Corrección de Errores en Resolución | art. 109.2 Ley 39/2015 |
| 17 | **OTRO** | Otro tipo de solicitud | Genérico |

#### Combinaciones Típicas mediante SOLICITUDES_TIPOS

**Transporte/Distribución con DUP:**
```
AAP + AAC + DUP → solicitud_id vinculada a tipos [1, 2, 3]
```

**Renovable con RAIPEE:**
```
AAP + RAIPEE_PREVIA → solicitud_id vinculada a tipos [1, 7]
AAE_DEFINITIVA + RAIPEE_DEFINITIVA → solicitud_id vinculada a tipos [5, 8]
```

**Autoconsumo AT Andalucía:**
```
AAP + AAC + RADNE → solicitud_id vinculada a tipos [1, 2, 9]
```

**Explotación (nueva normativa RDL 7/2025):**
```
AAE_PROVISIONAL → solicitud_id vinculada a tipo [4] (pruebas)
AAE_DEFINITIVA → solicitud_id vinculada a tipo [5] (definitiva)
```

**Transmisión con cambio simultáneo:**
```
AAT + AAE_DEFINITIVA → solicitud_id vinculada a tipos [6, 5]
```

#### Tipos Especiales

**DESISTIMIENTO y RENUNCIA:**

- Solicitudes que afectan a otra solicitud previa
- Requieren campo `SOLICITUD_AFECTADA_ID` NOT NULL en `SOLICITUDES`
- Finalizan la solicitud referenciada sin resolución de fondo

**RAIPEE_PREVIA vs RAIPEE_DEFINITIVA:**

- **RAIPEE_PREVIA:** Reserva punto de conexión. Se solicita con AAP.
- **RAIPEE_DEFINITIVA:** Inscripción definitiva tras instalación construida. Se solicita con AAE_DEFINITIVA.
- Secuencia obligatoria: PREVIA debe existir antes de solicitar DEFINITIVA.

**AAE_PROVISIONAL vs AAE_DEFINITIVA (RDL 7/2025):**

- **AAE_PROVISIONAL:** Máximo 6 meses. Solo para pruebas de funcionamiento. No permite facturación comercial.
- **AAE_DEFINITIVA:** Indefinida. Autoriza explotación comercial permanente. Requiere AAE_PROVISIONAL previa concedida.

#### Uso en Reglas de Negocio

El `TIPO_SOLICITUD_ID` (individual) determina:

- **Fases obligatorias** del procedimiento
- **Requisitos documentales** (proyectos, estudios ambientales, etc.)
- **Plazos máximos** de resolución
- **Posibilidad de silencio administrativo** (positivo/negativo)
- **Compatibilidad con tipo de expediente**

**Validaciones de combinaciones:**

- DUP requiere AAP o AAC simultánea o previa
- AAE_DEFINITIVA requiere AAE_PROVISIONAL previa
- RAIPEE_DEFINITIVA requiere RAIPEE_PREVIA previa
- RADNE solo para tipo_expediente = 'Autoconsumo'
- RAIPEE solo para tipo_expediente = 'Renovable'

#### Relación con Otras Tablas

**Usado en:**
- `SOLICITUDES.TIPO_SOLICITUD_ID` (clasificación principal - **puede ser deprecated**)
- `SOLICITUDES_TIPOS.TIPO_SOLICITUD_ID` (vinculación múltiple - **fuente de verdad v3.0**)

**Relacionado con motor de reglas:**
- Tablas de configuración que definen fases obligatorias por tipo de solicitud
- Validaciones de secuencia (MOD requiere AAC previa concedida)
- Validaciones de compatibilidad (RAIPEE solo para renovables)

#### Notas de Migración v2.0 → v3.0

**Script de conversión:**

Ver archivo `SOLICITUDES_TIPOS.md` sección "Migración desde v2.0" para script SQL completo.

**Estrategia:**

1. Mantener `SOLICITUDES.TIPO_SOLICITUD_ID` temporalmente para compatibilidad
2. Poblar `SOLICITUDES_TIPOS` dividiendo tipos combinados en individuales
3. Actualizar aplicación para consultar `SOLICITUDES_TIPOS` en lugar de `TIPO_SOLICITUD_ID`
4. Deprecar y eliminar `SOLICITUDES.TIPO_SOLICITUD_ID` en versión futura

#### Marco Legal Actualizado

- **LSE 24/2013:** Ley del Sector Eléctrico (base de autorizaciones)
- **RDL 7/2025:** División AAE en provisional/definitiva
- **RD 1955/2000:** Transporte, distribución, producción (procedimiento)
- **RD 413/2014:** RAIPEE renovables
- **RD 244/2019:** RADNE autoconsumo
- **Ley 39/2015:** Procedimiento Administrativo Común (desistimiento, recurso, etc.)
- **Normativa autonómica Andalucía:** RADNE obligatorio AT (2024)

---

**Versión:** 3.0  
**Fecha:** 22 de enero de 2026  
**Proyecto:** BDDAT - Sistema de Tramitación de Expedientes de Alta Tensión
