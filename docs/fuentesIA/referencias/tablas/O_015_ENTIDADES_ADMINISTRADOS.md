<!--
Tabla: ENTIDADES_ADMINISTRADOS
Generado manualmente
Fecha de creación: 01/02/2026
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### ENTIDADES_ADMINISTRADOS

Metadatos específicos de personas físicas o jurídicas que actúan como administrados (titulares, solicitantes, autorizados) en el sistema.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ENTIDAD_ID** | INTEGER | Referencia a entidad base | NO | PK y FK → ENTIDADES(ID), UNIQUE, CASCADE |
| **EMAIL_NOTIFICACIONES** | VARCHAR(120) | Email oficial para sistema Notifica | NO | Email donde se reciben notificaciones electrónicas oficiales. Puede ser personal o corporativo |
| **REPRESENTANTE_NIF_CIF** | VARCHAR(20) | NIF/CIF de quien representa/gestiona | SÍ | NULL si autorepresentado (persona física) o gestión corporativa directa. Normalizado como CIF/NIF |
| **REPRESENTANTE_NOMBRE** | VARCHAR(200) | Nombre completo del representante | SÍ | NULL si autorepresentado. Puede ser persona física (administrador único) o jurídica (consultora contratada) |
| **REPRESENTANTE_TELEFONO** | VARCHAR(20) | Teléfono del representante | SÍ | Contacto directo con quien gestiona |
| **REPRESENTANTE_EMAIL** | VARCHAR(120) | Email del representante | SÍ | Email de contacto (NO oficial para notificaciones, solo coordinación) |
| **NOTAS_REPRESENTACION** | TEXT | Observaciones sobre la representación | SÍ | Tipo de cargo o relación: "Administrador único", "Consultora ACME SL contratada", "Apoderado con poder notarial", etc. |

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

- **v1.0** (01/02/2026): Creación inicial con estructura simplificada de representación genérica

#### Filosofía

Tabla de metadatos para **administrados** (personas físicas o jurídicas privadas):

- **Relación 1:1** con `ENTIDADES` mediante `ENTIDAD_ID` como PK y FK
- **Representación simplificada:** Un solo campo `REPRESENTANTE_*` que cubre todos los casos (persona física, jurídica, consultora)
- **Autorepresentación:** Si `REPRESENTANTE_NIF_CIF` es NULL, el administrado se representa a sí mismo
- **Par obligatorio Notifica:** `(CIF/NIF, EMAIL_NOTIFICACIONES)` debe estar completo para poder notificar

#### Casos de Uso

**Caso A: Persona física autorepresentada**
```sql
-- ENTIDADES
INSERT INTO entidades (tipo_entidad_id, cif_nif, nombre_completo, ...) 
VALUES (1, '12345678A', 'Juan Pérez García', ...);

-- ENTIDADES_ADMINISTRADOS
INSERT INTO entidades_administrados (entidad_id, email_notificaciones, representante_nif_cif, representante_nombre)
VALUES (1, 'juan.perez@gmail.com', NULL, NULL);

-- Par Notifica: ('12345678A', 'juan.perez@gmail.com')
```

**Caso B: Persona jurídica con administrador único**
```sql
-- ENTIDADES
INSERT INTO entidades (tipo_entidad_id, cif_nif, nombre_completo, ...) 
VALUES (1, 'B12345678', 'Constructora García SL', ...);

-- ENTIDADES_ADMINISTRADOS
INSERT INTO entidades_administrados (
    entidad_id, 
    email_notificaciones, 
    representante_nif_cif, 
    representante_nombre,
    notas_representacion
)
VALUES (
    2, 
    'notificaciones@constructoragarcia.com', 
    '12345678A', 
    'Juan García López',
    'Administrador único'
);

-- Par Notifica: ('12345678A', 'notificaciones@constructoragarcia.com')
```

**Caso C: Persona jurídica con gestión corporativa directa**
```sql
-- ENTIDADES
INSERT INTO entidades (tipo_entidad_id, cif_nif, nombre_completo, ...) 
VALUES (1, 'B87654321', 'Gran Empresa Eléctrica SA', ...);

-- ENTIDADES_ADMINISTRADOS
INSERT INTO entidades_administrados (
    entidad_id, 
    email_notificaciones, 
    representante_nif_cif, 
    representante_nombre,
    notas_representacion
)
VALUES (
    3, 
    'tramites.juridico@granempresa.com', 
    NULL, 
    NULL,
    'Gestión corporativa directa'
);

-- Par Notifica: ('B87654321', 'tramites.juridico@granempresa.com')
```

**Caso D: Persona jurídica representada por consultora**
```sql
-- ENTIDADES
INSERT INTO entidades (tipo_entidad_id, cif_nif, nombre_completo, ...) 
VALUES (1, 'B11111111', 'Promotora Solar XXX SL', ...);

-- ENTIDADES_ADMINISTRADOS
INSERT INTO entidades_administrados (
    entidad_id, 
    email_notificaciones, 
    representante_nif_cif, 
    representante_nombre,
    representante_telefono,
    representante_email,
    notas_representacion
)
VALUES (
    4, 
    'notifica@consultoraacme.com', 
    'B22222222', 
    'Consultora ACME SL',
    '956123456',
    'contacto@consultoraacme.com',
    'Consultora contratada para tramitación completa'
);

-- Par Notifica: ('B22222222', 'notifica@consultoraacme.com')
```

#### Regla de Negocio: CIF/NIF para Notifica

**Par obligatorio para notificar:** `(CIF/NIF, EMAIL_NOTIFICACIONES)`

**Lógica de obtención del CIF/NIF:**

```python
def obtener_cif_notifica(administrado):
    """
    Devuelve el CIF/NIF que debe usarse para notificar.
    
    Regla:
    - Si hay representante_nif_cif → usar ese (quien gestiona)
    - Si representante_nif_cif es NULL → usar entidades.cif_nif (titular)
    """
    if administrado.representante_nif_cif:
        return administrado.representante_nif_cif
    else:
        return administrado.entidad.cif_nif

def obtener_par_notifica(administrado):
    """
    Devuelve el par (CIF/NIF, EMAIL) para sistema Notifica.
    """
    return (
        obtener_cif_notifica(administrado),
        administrado.email_notificaciones
    )
```

**Consulta SQL:**
```sql
-- Obtener par para notificar
SELECT 
    COALESCE(ea.representante_nif_cif, e.cif_nif) AS cif_notifica,
    ea.email_notificaciones
FROM entidades_administrados ea
JOIN entidades e ON ea.entidad_id = e.id
WHERE ea.entidad_id = :id;
```

#### Visualización en Interfaz

**Al crear/editar administrado:**

```
┌─────────────────────────────────────────────────┐
│ DATOS DEL TITULAR                               │
├─────────────────────────────────────────────────┤
│ CIF/NIF: B12345678                              │
│ Nombre: Constructora García SL                  │
│ ...                                             │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ NOTIFICACIONES ELECTRÓNICAS (Notifica)          │
├─────────────────────────────────────────────────┤
│ Email notificaciones: [_____________________]   │
│   ⓘ Email oficial donde se recibirán las       │
│     notificaciones electrónicas                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ REPRESENTACIÓN (Opcional)                       │
├─────────────────────────────────────────────────┤
│ ☐ El titular se representa a sí mismo           │
│                                                 │
│ ☑ Hay representante/apoderado                   │
│   NIF/CIF: [12345678A]                          │
│   Nombre:  [Juan García López]                  │
│   Teléfono: [____________]                      │
│   Email:    [____________]                      │
│   Notas:    [Administrador único]               │
│                                                 │
│ ⚠️ NOTIFICACIONES SE ENVIARÁN A:                │
│    CIF/NIF: 12345678A  (representante)          │
│    Email:   notificaciones@constructora...      │
└─────────────────────────────────────────────────┘
```

#### Validaciones

**Al guardar:**

1. `EMAIL_NOTIFICACIONES` obligatorio (NOT NULL)
2. Si `REPRESENTANTE_NIF_CIF` tiene valor → `REPRESENTANTE_NOMBRE` obligatorio
3. Si `REPRESENTANTE_NIF_CIF` es NULL → `REPRESENTANTE_NOMBRE` debe ser NULL
4. `REPRESENTANTE_NIF_CIF` debe pasar validación algoritmo NIF/CIF (si no es NULL)
5. Par `(CIF_NOTIFICA, EMAIL_NOTIFICACIONES)` debe estar completo

**Validación Python:**
```python
from models import Entidad, EntidadAdministrado

def validar_administrado(administrado):
    # Email notificaciones obligatorio
    if not administrado.email_notificaciones:
        raise ValidationError("Email de notificaciones es obligatorio")
    
    # Coherencia representante
    tiene_cif = administrado.representante_nif_cif is not None
    tiene_nombre = administrado.representante_nombre is not None
    
    if tiene_cif != tiene_nombre:
        raise ValidationError(
            "Si hay CIF de representante, debe haber nombre (y viceversa)"
        )
    
    # Validar CIF representante
    if tiene_cif:
        if not Entidad.validar_cif_nif(administrado.representante_nif_cif):
            raise ValidationError("CIF/NIF del representante no es válido")
    
    # Par Notifica completo
    cif_notifica = administrado.representante_nif_cif or administrado.entidad.cif_nif
    if not cif_notifica or not administrado.email_notificaciones:
        raise ValidationError(
            "No se puede determinar el par (CIF/NIF, email) para notificar"
        )
```

#### Consultas Frecuentes

**1. Listar administrados con sus datos de notificación:**
```sql
SELECT 
    e.id,
    e.cif_nif AS cif_titular,
    e.nombre_completo AS nombre_titular,
    COALESCE(ea.representante_nif_cif, e.cif_nif) AS cif_notifica,
    COALESCE(ea.representante_nombre, e.nombre_completo) AS nombre_notifica,
    ea.email_notificaciones
FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE
ORDER BY e.nombre_completo;
```

**2. Buscar por email de notificaciones:**
```sql
SELECT e.*, ea.*
FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE ea.email_notificaciones ILIKE '%@consultoraacme.com';
```

**3. Administrados representados por una consultora específica:**
```sql
SELECT e.*, ea.*
FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE ea.representante_nif_cif = 'B22222222'  -- CIF consultora
AND e.activo = TRUE;
```

**4. Administrados autorepresentados (personas físicas):**
```sql
SELECT e.*, ea.*
FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE ea.representante_nif_cif IS NULL
AND e.cif_nif LIKE '_________'  -- NIF (8 dígitos + letra)
AND e.activo = TRUE;
```

---
