<!--
Tabla: ENTIDADES_EMPRESAS_SERVICIO_PUBLICO
Generado manualmente
Fecha de creación: 01/02/2026
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### ENTIDADES_EMPRESAS_SERVICIO_PUBLICO

Metadatos específicos de empresas operadoras de infraestructuras críticas y servicios públicos que pueden actuar simultáneamente como solicitantes (instalaciones propias) y como organismos consultados (informes sobre afecciones a sus infraestructuras).

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ENTIDAD_ID** | INTEGER | Referencia a entidad base | NO | PK y FK → ENTIDADES(ID), UNIQUE, CASCADE |
| **EMAIL_NOTIFICACIONES** | VARCHAR(120) | Email oficial para sistema Notifica | NO | Email donde se reciben notificaciones electrónicas oficiales cuando actúan como solicitantes. Puede ser corporativo |
| **REPRESENTANTE_NIF_CIF** | VARCHAR(20) | NIF/CIF de quien representa/gestiona | SÍ | NULL si gestión corporativa directa. Normalizado como CIF/NIF |
| **REPRESENTANTE_NOMBRE** | VARCHAR(200) | Nombre completo del representante | SÍ | NULL si gestión corporativa. Puede ser persona física (responsable) o jurídica (consultora contratada) |
| **REPRESENTANTE_TELEFONO** | VARCHAR(20) | Teléfono del representante | SÍ | Contacto directo con quien gestiona |
| **REPRESENTANTE_EMAIL** | VARCHAR(120) | Email del representante | SÍ | Email de contacto (NO oficial para notificaciones, solo coordinación) |
| **NOTAS_REPRESENTACION** | TEXT | Observaciones sobre la representación | SÍ | Tipo de cargo o relación: "Responsable zona sur", "Dpto. Afecciones", etc. |

#### Claves

- **PK:** `ENTIDAD_ID`
- **FK:**
  - `ENTIDAD_ID` → `ENTIDADES(ID)` ON DELETE CASCADE

#### Índices Recomendados

- `REPRESENTANTE_NIF_CIF` (búsquedas por representante)
- `EMAIL_NOTIFICACIONES` (búsquedas por email oficial)

#### Constraints

```sql
-- Si hay representante_nif_cif, debe haber representante_nombre
CONSTRAINT chk_representante_coherente
    CHECK (
        (representante_nif_cif IS NULL AND representante_nombre IS NULL)
        OR
        (representante_nif_cif IS NOT NULL AND representante_nombre IS NOT NULL)
    )
```

#### Relaciones

- **entidad**: ENTIDADES.id (FK, relación 1:1 con entidad base)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial con estructura idéntica a ENTIDADES_ADMINISTRADOS (diferenciación semántica por tipo)

#### Filosofía

Tabla de metadatos para **empresas de servicio público** (operadores de infraestructuras críticas):

- **Relación 1:1** con `ENTIDADES` mediante `ENTIDAD_ID` como PK y FK
- **Estructura idéntica a ENTIDADES_ADMINISTRADOS:** Los campos son los mismos, la diferencia es **semántica**
- **Doble rol simultáneo:**
  - Como **solicitante**: Presentan solicitudes para sus propias instalaciones (ej: nueva subestación eléctrica)
  - Como **organismo consultado**: Emiten informes sobre afecciones a sus infraestructuras existentes
- **Notificaciones vía Notifica:** Cuando actúan como solicitantes, usan sistema Notifica (como administrados)
- **Par obligatorio Notifica:** `(CIF/NIF, EMAIL_NOTIFICACIONES)` debe estar completo

#### ¿Por qué tabla separada si campos son iguales?

**La diferencia es SEMÁNTICA, no estructural:**

1. **Tipo de entidad diferente** en `TIPOS_ENTIDADES`:
   - `ADMINISTRADO`: Puede ser solicitante, NO puede ser consultado
   - `EMPRESA_SERVICIO_PUBLICO`: Puede ser solicitante Y consultado

2. **Filtrado automático en interfaz:**
   ```sql
   -- Fase CONSULTAS: Solicitar informe sobre afecciones
   -- Solo aparecen empresas servicio público + organismos + ayuntamientos
   SELECT e.* FROM entidades e
   JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
   WHERE te.puede_ser_consultado = TRUE;
   ```

3. **Lógica de negocio distinta:**
   - Administrado: Solo recibe notificaciones
   - Empresa servicio público: Recibe Y emite documentos oficiales (informes)

4. **Facilidad para el tramitador:**
   - Al crear consulta a Enagas → NO aparece "Juan Renegas" (administrado)
   - Solo aparecen entidades con `tipo = EMPRESA_SERVICIO_PUBLICO`

#### Ejemplos de Entidades

**Sector energético:**
- Enagas SA (gas natural)
- E-Distribución Redes Digitales SLU (electricidad)
- Red Eléctrica de España (REE)
- Iberdrola Distribución Eléctrica
- Endesa Distribución

**Sector agua:**
- Consorcios de Aguas provinciales
- EMASESA (Empresa Metropolitana de Abastecimiento y Saneamiento de Aguas de Sevilla)
- EMACSA (Empresa Municipal de Aguas de Córdoba)

**Sector transporte:**
- ADIF (como empresa pública, aunque también puede ser ORGANISMO_PUBLICO)
- Operadores ferroviarios privados

**Sector telecomunicaciones:**
- Telefonica de España
- Orange
- Vodafone
- Operadores de fibra óptica

#### Casos de Uso

**Caso A: E-Distribución con gestión corporativa directa**
```sql
-- ENTIDADES
INSERT INTO entidades (tipo_entidad_id, cif_nif, nombre_completo, email) 
VALUES (2, 'A12345678', 'E-Distribución Redes Digitales SLU', 'info@edistribucion.com');

-- ENTIDADES_EMPRESAS_SERVICIO_PUBLICO
INSERT INTO entidades_empresas_servicio_publico (
    entidad_id, 
    email_notificaciones, 
    representante_nif_cif, 
    representante_nombre,
    notas_representacion
)
VALUES (
    1, 
    'tramites.andalucia@edistribucion.com', 
    NULL, 
    NULL,
    'Gestión corporativa - Delegación Andalucía'
);

-- Par Notifica: ('A12345678', 'tramites.andalucia@edistribucion.com')
```

**Caso B: Enagas con responsable zona**
```sql
-- ENTIDADES
INSERT INTO entidades (tipo_entidad_id, cif_nif, nombre_completo, email) 
VALUES (2, 'A11223344', 'Enagas SA', 'info@enagas.es');

-- ENTIDADES_EMPRESAS_SERVICIO_PUBLICO
INSERT INTO entidades_empresas_servicio_publico (
    entidad_id, 
    email_notificaciones, 
    representante_nif_cif, 
    representante_nombre,
    representante_telefono,
    representante_email,
    notas_representacion
)
VALUES (
    2, 
    'notificaciones.sur@enagas.es', 
    '87654321B', 
    'Carlos Martínez Ruiz',
    '954123456',
    'carlos.martinez@enagas.es',
    'Responsable zona sur - Afecciones gasoductos'
);

-- Par Notifica: ('87654321B', 'notificaciones.sur@enagas.es')
```

**Caso C: Consorcio Aguas (gestión por empresa contratada)**
```sql
-- ENTIDADES
INSERT INTO entidades (tipo_entidad_id, cif_nif, nombre_completo, email) 
VALUES (2, 'P4100000A', 'Consorcio Provincial de Aguas de Sevilla', 'info@consorcioaguas-sevilla.es');

-- ENTIDADES_EMPRESAS_SERVICIO_PUBLICO
INSERT INTO entidades_empresas_servicio_publico (
    entidad_id, 
    email_notificaciones, 
    representante_nif_cif, 
    representante_nombre,
    representante_telefono,
    representante_email,
    notas_representacion
)
VALUES (
    3, 
    'tramites@gestionaguas.com', 
    'B99887766', 
    'Gestión Integral de Aguas SL',
    '955999888',
    'contacto@gestionaguas.com',
    'Empresa contratada para gestión administrativa y técnica'
);

-- Par Notifica: ('B99887766', 'tramites@gestionaguas.com')
```

#### Regla de Negocio: CIF/NIF para Notifica

**Idéntica a ENTIDADES_ADMINISTRADOS:**

```python
def obtener_cif_notifica(empresa_servicio):
    """
    Devuelve el CIF/NIF que debe usarse para notificar.
    
    Regla:
    - Si hay representante_nif_cif → usar ese (quien gestiona)
    - Si representante_nif_cif es NULL → usar entidades.cif_nif (empresa)
    """
    if empresa_servicio.representante_nif_cif:
        return empresa_servicio.representante_nif_cif
    else:
        return empresa_servicio.entidad.cif_nif
```

**Consulta SQL:**
```sql
-- Obtener par para notificar
SELECT 
    COALESCE(ees.representante_nif_cif, e.cif_nif) AS cif_notifica,
    ees.email_notificaciones
FROM entidades_empresas_servicio_publico ees
JOIN entidades e ON ees.entidad_id = e.id
WHERE ees.entidad_id = :id;
```

#### Flujo UX: Copia de Datos entre Roles

**Escenario:** Una empresa ya existe con un rol, se añade segundo rol

**Ejemplo:**
1. E-Distribución se crea inicialmente como **Administrado** (solicitud de instalación)
2. Semanas después, necesita añadirse como **Empresa Servicio Público** (para emitir informes)
3. Sistema detecta que CIF A12345678 ya tiene rol activo

**Interfaz:**
```
┌─────────────────────────────────────────────────┐
│ AÑADIR ROL: Empresa Servicio Público            │
├─────────────────────────────────────────────────┤
│ Entidad: E-Distribución Redes Digitales SLU     │
│ CIF: A12345678                                  │
│                                                 │
│ ⓘ Este CIF ya tiene roles activos:             │
│    • Administrado                              │
│                                                 │
│ [📋 Copiar datos del rol: Administrado ▼]       │
│                                                 │
├─────────────────────────────────────────────────┤
│ Email notificaciones:                           │
│ [tramites@edistribucion.com]                    │
│                                                 │
│ Representante NIF/CIF:                          │
│ [12345678A]                                     │
│                                                 │
│ Representante nombre:                           │
│ [María López García]                            │
│                                                 │
│ ...                                             │
└─────────────────────────────────────────────────┘
```

**Lógica Python:**
```python
def sugerir_copia_datos(cif_nif):
    """
    Al añadir nuevo rol, detecta roles existentes y sugiere copia.
    """
    entidad = Entidad.query.filter_by(cif_nif=cif_nif).first()
    if not entidad:
        return None  # CIF nuevo, no sugerir nada
    
    roles_existentes = []
    
    if entidad.datos_administrado:
        roles_existentes.append({
            'tipo': 'Administrado',
            'datos': entidad.datos_administrado
        })
    
    if entidad.datos_empresa_servicio:
        roles_existentes.append({
            'tipo': 'Empresa Servicio Público',
            'datos': entidad.datos_empresa_servicio
        })
    
    # ... otros roles
    
    return roles_existentes
```

#### Validaciones

**Idénticas a ENTIDADES_ADMINISTRADOS:**

1. `EMAIL_NOTIFICACIONES` obligatorio (NOT NULL)
2. Si `REPRESENTANTE_NIF_CIF` tiene valor → `REPRESENTANTE_NOMBRE` obligatorio
3. Si `REPRESENTANTE_NIF_CIF` es NULL → `REPRESENTANTE_NOMBRE` debe ser NULL
4. `REPRESENTANTE_NIF_CIF` debe pasar validación algoritmo NIF/CIF (si no es NULL)
5. Par `(CIF_NOTIFICA, EMAIL_NOTIFICACIONES)` debe estar completo

#### Consultas Frecuentes

**1. Listar empresas servicio público con datos de notificación:**
```sql
SELECT 
    e.id,
    e.cif_nif AS cif_empresa,
    e.nombre_completo AS nombre_empresa,
    COALESCE(ees.representante_nif_cif, e.cif_nif) AS cif_notifica,
    COALESCE(ees.representante_nombre, e.nombre_completo) AS nombre_notifica,
    ees.email_notificaciones
FROM entidades e
JOIN entidades_empresas_servicio_publico ees ON e.id = ees.entidad_id
WHERE e.activo = TRUE
ORDER BY e.nombre_completo;
```

**2. Empresas del sector eléctrico (por nombre, sin campo tipo_infraestructura):**
```sql
SELECT e.*, ees.*
FROM entidades e
JOIN entidades_empresas_servicio_publico ees ON e.id = ees.entidad_id
WHERE (
    e.nombre_completo ILIKE '%distribución%electric%'
    OR e.nombre_completo ILIKE '%red eléctrica%'
    OR e.nombre_completo ILIKE '%iberdrola%'
    OR e.nombre_completo ILIKE '%endesa%'
)
AND e.activo = TRUE;
```

**3. Empresas con gestión corporativa directa (sin representante):**
```sql
SELECT e.*, ees.*
FROM entidades e
JOIN entidades_empresas_servicio_publico ees ON e.id = ees.entidad_id
WHERE ees.representante_nif_cif IS NULL
AND e.activo = TRUE;
```

**4. Buscar por email de notificaciones:**
```sql
SELECT e.*, ees.*
FROM entidades e
JOIN entidades_empresas_servicio_publico ees ON e.id = ees.entidad_id
WHERE ees.email_notificaciones ILIKE '%@edistribucion.com';
```

---
