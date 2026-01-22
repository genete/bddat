### TIPOS_SOLICITUDES (v3.0)

Tipos **individuales** de actos administrativos. Combinaciones mediante tabla puente `SOLICITUDES_TIPOS`.

#### Filosofía v3.0

**v2.0:** 20+ tipos combinados (AAP+AAC, AAP+DUP...)  
**v3.0:** 17 tipos individuales + tabla puente

#### Catálogo (17 Tipos)

##### Fase PREVIA (art. 53.1.a LSE)
| ID | Siglas | Descripción |
|:---|:---|:---|
| 1 | AAP | Autorización Administrativa Previa |

##### Fase CONSTRUCCIÓN (art. 53.1.b LSE)
| ID | Siglas | Descripción |
|:---|:---|:---|
| 2 | AAC | Autorización Administrativa de Construcción |

##### Declaración Utilidad Pública (art. 54 LSE)
| ID | Siglas | Descripción |
|:---|:---|:---|
| 3 | DUP | Declaración de Utilidad Pública |

##### Fase EXPLOTACIÓN (art. 53.1.c LSE + RDL 7/2025) ⭐ **NOVEDAD 2025**
| ID | Siglas | Descripción |
|:---|:---|:---|
| 4 | AAE_PROVISIONAL | Autorización Explotación Provisional (pruebas, 6 meses) |
| 5 | AAE_DEFINITIVA | Autorización Explotación Definitiva |

**RDL 7/2025:** AAE dividida en PROVISIONAL (pruebas) → DEFINITIVA (comercial).

##### Transmisión (art. 56 LSE)
| ID | Siglas | Descripción |
|:---|:---|:---|
| 6 | AAT | Autorización de Transmisión de Titularidad |

##### RAIPEE Renovables (RD 413/2014)
| ID | Siglas | Descripción |
|:---|:---|:---|
| 7 | RAIPEE_PREVIA | Inscripción Previa (reserva conexión) |
| 8 | RAIPEE_DEFINITIVA | Inscripción Definitiva |

##### RADNE Autoconsumo (RD 244/2019) ⭐ **Andalucía: Obligatorio AT desde 2024**
| ID | Siglas | Descripción |
|:---|:---|:---|
| 9 | RADNE | Inscripción Registro Autoconsumo |

##### Cierre (art. 53.1.d LSE)
| ID | Siglas | Descripción |
|:---|:---|:---|
| 10 | CIERRE | Autorización de Cierre de Instalación |

##### Actos Administrativos (Ley 39/2015)
| ID | Siglas | Descripción |
|:---|:---|:---|
| 11 | DESISTIMIENTO | Desistimiento de Solicitud |
| 12 | RENUNCIA | Renuncia de Autorización |
| 13 | AMPLIACION_PLAZO | Ampliación de Plazo |
| 14 | INTERESADO | Condición de Interesado |
| 15 | RECURSO | Recurso Administrativo |
| 16 | CORRECCION_ERRORES | Corrección de Errores |
| 17 | OTRO | Otro tipo |

#### Combinaciones Típicas (vía SOLICITUDES_TIPOS)

**Transporte con DUP:**
```python
# AAP + AAC + DUP
solicitud.solicitudes_tipos = [
    SolicitudTipo(tipo_solicitud_id=1),  # AAP
    SolicitudTipo(tipo_solicitud_id=2),  # AAC
    SolicitudTipo(tipo_solicitud_id=3),  # DUP
]
```

**Renovable con RAIPEE:**
```python
# AAP + RAIPEE_PREVIA
solicitud.solicitudes_tipos = [
    SolicitudTipo(tipo_solicitud_id=1),  # AAP
    SolicitudTipo(tipo_solicitud_id=7),  # RAIPEE_PREVIA
]
```

**Autoconsumo AT Andalucía:**
```python
# AAP + AAC + RADNE (obligatorio)
solicitud.solicitudes_tipos = [
    SolicitudTipo(tipo_solicitud_id=1),  # AAP
    SolicitudTipo(tipo_solicitud_id=2),  # AAC
    SolicitudTipo(tipo_solicitud_id=9),  # RADNE
]
```

#### Validaciones

1. **Incompatibilidades:** AAE_PROVISIONAL y AAE_DEFINITIVA mutuamente excluyentes
2. **Secuencias:** AAE_DEFINITIVA requiere PROVISIONAL previa, RAIPEE_DEFINITIVA requiere PREVIA
3. **Coherencia expediente:** RAIPEE solo renovables, RADNE solo autoconsumo

#### Datos Maestros

Ver archivo `datos_maestros.sql` para INSERT completo de los 17 tipos.

#### Marco Legal

- LSE 24/2013: Base autorizaciones eléctricas
- RDL 7/2025: División AAE provisional/definitiva
- RD 413/2014: RAIPEE renovables
- RD 244/2019: RADNE autoconsumo
- Ley 39/2015: Procedimiento Administrativo Común

---

**Versión:** 3.0  
**Fecha:** 22 de enero de 2026  
**Proyecto:** BDDAT
