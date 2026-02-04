<!--
Tabla: ENTIDADES_EMPRESAS_SERVICIO_PUBLICO
Generado manualmente
Fecha de creación: 01/02/2026
Última actualización: 04/02/2026
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### ENTIDADES_EMPRESAS_SERVICIO_PUBLICO

Metadatos específicos de empresas operadoras de infraestructuras críticas y servicios públicos que actúan como organismos consultados (informes sobre afecciones a sus infraestructuras). A diferencia de otras entidades, estas empresas pueden actuar simultáneamente como solicitantes (necesitan entrada en ENTIDADES_ADMINISTRADOS) y consultados.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ENTIDAD_ID** | INTEGER | Referencia a entidad base | NO | PK y FK → ENTIDADES(ID), UNIQUE, CASCADE |
| **CODIGO_DIR3** | VARCHAR(20) | Código DIR3 para notificaciones SIR | SÍ | Opcional, no todas las empresas tienen. Para comunicaciones interadministrativas |

#### Claves

- **PK:** `ENTIDAD_ID`
- **FK:**
  - `ENTIDAD_ID` → `ENTIDADES(ID)` ON DELETE CASCADE

#### Índices

- `ix_public_entidades_empresas_servicio_publico_codigo_dir3` (único, sobre `CODIGO_DIR3`)

#### Relaciones

- **entidad**: ENTIDADES.id (FK, relación 1:1 con entidad base)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial con estructura minimalista (solo DIR3 opcional)
- **v1.1** (04/02/2026): Sincronización con schema.sql - Eliminar campos de representante que NO existen en la tabla real

#### Filosofía

Tabla de metadatos para **empresas de servicio público** (operadores de infraestructuras críticas):

- **Relación 1:1** con `ENTIDADES` mediante `ENTIDAD_ID` como PK y FK
- **Estructura minimalista:** Solo código DIR3 opcional
- **Doble rol simultáneo:**
  - Como **organismo consultado**: Emiten informes sobre afecciones a sus infraestructuras existentes (uso DIR3 si lo tienen)
  - Como **solicitante**: Si necesitan presentar solicitudes propias, deben tener entrada adicional en `ENTIDADES_ADMINISTRADOS`
- **DIR3 opcional:** No todas las empresas privadas tienen código DIR3 (solo si son operadores de infraestructuras con convenios interadministrativos)

#### Campos que YA están en ENTIDADES (no duplicar)

**Todos estos datos viven en `ENTIDADES`:**

- `CIF_NIF`: CIF de la empresa operadora
- `NOMBRE_COMPLETO`: Razón social (ej: "E-Distribución Redes Digitales S.L.U.", "Gas Natural Distribución SDG S.A.")
- `EMAIL`: Email general corporativo
- `TELEFONO`: Teléfono general
- `DIRECCION`, `CODIGO_POSTAL`, `MUNICIPIO_ID`: Domicilio social
- `ACTIVO`: Borrado lógico

**Para contactos específicos o representantes, usar campo `NOTAS` en `ENTIDADES`.**

#### Representación y Notificaciones

**A DIFERENCIA de las tablas MD anteriores:**

Esta tabla **NO tiene campos de representante** (`representante_nif_cif`, `representante_nombre`, etc.). 

**¿Por qué?**

1. **Cuando actúan como consultadas:** No necesitan notificaciones vía Notifica (emiten informes, no los reciben)
2. **Cuando actúan como solicitantes:** Deben tener entrada en `ENTIDADES_ADMINISTRADOS` donde SÍ están los campos de representante

**Patrón real:**
```
Empresa X (ENTIDADES)
│
├─ ENTIDADES_EMPRESAS_SERVICIO_PUBLICO (rol: consultada)
│   └─ codigo_dir3 (opcional)
│
└─ ENTIDADES_ADMINISTRADOS (rol: solicitante)
    ├─ email_notificaciones
    ├─ representante_nif_cif
    └─ representante_nombre
```

#### Ejemplos de Entidades (tipos)

**Sector energético:**
- E-Distribución Redes Digitales S.L.U. (distribuidora eléctrica)
- Red Eléctrica de España S.A.U. (transporte eléctrica)
- Gas Natural Distribución SDG S.A. (distribuidora gas)

**Sector agua:**
- Consorcio de Aguas de la provincia
- Empresa Metropolitana de Abastecimiento

**Sector transporte:**
- ADIF (Administrador de Infraestructuras Ferroviarias)
- Operadores de transporte por cable

**Sector telecomunicaciones:**
- Telefónica de España S.A.U.
- Operadores de fibra óptica

#### Sistema DIR3: Empresas de Servicio Público

**¿Qué es DIR3 para empresas privadas?**
- Código opcional que algunas empresas de servicio público tienen cuando operan infraestructuras con convenios interadministrativos
- Formato: 1-2 letras + 7-8 números (ej: `E12345678`)
- **NO todas las empresas lo tienen** (mayormente empresas públicas o con participación pública)

**Uso en BDDAT:**
- Identificación para notificaciones vía **SIR** cuando actúan como **organismos consultados**
- Si no tienen DIR3, se usan métodos tradicionales (email, correo postal)

**Campo nullable:**
- TRUE (no obligatorio)
- Mayoría de empresas privadas no tienen DIR3

#### Regla de Negocio: Doble Entrada Posible

**Una empresa puede estar en DOS tablas de metadatos:**

1. **Esta tabla** (`ENTIDADES_EMPRESAS_SERVICIO_PUBLICO`):
   - Para actuar como consultada (emitir informes)
   - Solo necesita `codigo_dir3` (opcional)

2. **`ENTIDADES_ADMINISTRADOS`**:
   - Para actuar como solicitante (presentar solicitudes)
   - Necesita `email_notificaciones`, `representante_*`, etc.

**Ejemplo real:**
```sql
-- E-Distribución solicita autorización para nueva subestación
-- Y también es consultada sobre afecciones en proyectos de terceros

-- 1. ENTIDADES (base)
INSERT INTO entidades (tipo_entidad_id, cif_nif, nombre_completo)
VALUES (tipo_empresa_servicio_publico_id, 'B12345678', 'E-Distribución Redes Digitales S.L.U.');

-- 2. ENTIDADES_EMPRESAS_SERVICIO_PUBLICO (rol: consultada)
INSERT INTO entidades_empresas_servicio_publico (entidad_id, codigo_dir3)
VALUES (entidad_id, NULL);  -- Sin DIR3

-- 3. ENTIDADES_ADMINISTRADOS (rol: solicitante)
INSERT INTO entidades_administrados (
    entidad_id, 
    email_notificaciones,
    representante_nif_cif,
    representante_nombre
) VALUES (
    entidad_id,
    'notificaciones@edistribucion.com',
    'B98765432',
    'Consultora ACME Proyectos S.L.'
);
```

#### Filtrado Automático en Interfaz

**Contexto 1: Solicitar informe sobre afecciones (fase CONSULTAS)**
```sql
-- Solo aparecen empresas servicio público + organismos + ayuntamientos
SELECT e.* FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.puede_ser_consultado = TRUE
AND e.activo = TRUE;
```

**Contexto 2: Crear solicitud (empresa solicita autorización propia)**
```sql
-- Solo aparecen entidades con registro en ENTIDADES_ADMINISTRADOS
SELECT e.* FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE;
```

#### Validaciones

**Validación Python:**

```python
import re

def validar_codigo_dir3(codigo):
    """
    Valida formato de código DIR3.
    Formato: 1-2 letras + 7-8 números
    Ejemplos válidos: E12345678, EA0044689
    """
    if not codigo:
        return True  # Nullable, válido si es None/vacío
    
    # Patrón: 1-2 letras mayúsculas + 7-8 dígitos
    patron = r'^[A-Z]{1,2}\d{7,8}$'
    return re.match(patron, codigo.upper()) is not None

class EntidadEmpresaServicioPublico(db.Model):
    # ...
    
    @validates('codigo_dir3')
    def validate_codigo_dir3(self, key, value):
        if not value:
            return None  # Nullable
        
        value_upper = value.upper().strip()
        
        if not validar_codigo_dir3(value_upper):
            raise ValueError(
                f"Código DIR3 inválido: {value}. "
                "Formato esperado: 1-2 letras + 7-8 dígitos (ej: E12345678)"
            )
        
        return value_upper
```

**Validación en interfaz:**

```javascript
// Validación cliente (JavaScript)
function validarDIR3(codigo) {
    if (!codigo || codigo.trim() === '') return true; // Nullable
    const patron = /^[A-Z]{1,2}\d{7,8}$/;
    return patron.test(codigo.toUpperCase());
}
```

#### Consultas Frecuentes

**1. Listar empresas de servicio público con DIR3:**

```sql
SELECT 
    e.id,
    e.nombre_completo,
    e.cif_nif,
    ees.codigo_dir3,
    e.email,
    e.telefono
FROM entidades e
JOIN entidades_empresas_servicio_publico ees ON e.id = ees.entidad_id
WHERE e.activo = TRUE
ORDER BY e.nombre_completo;
```

**2. Empresas que son consultadas Y solicitantes:**

```sql
SELECT 
    e.nombre_completo,
    e.cif_nif,
    ees.codigo_dir3,
    ea.email_notificaciones,
    ea.representante_nombre
FROM entidades e
JOIN entidades_empresas_servicio_publico ees ON e.id = ees.entidad_id
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE
ORDER BY e.nombre_completo;
```

**3. Empresas sin DIR3 (solo métodos tradicionales):**

```sql
SELECT 
    e.nombre_completo,
    e.cif_nif,
    e.email,
    e.telefono
FROM entidades e
JOIN entidades_empresas_servicio_publico ees ON e.id = ees.entidad_id
WHERE ees.codigo_dir3 IS NULL
AND e.activo = TRUE
ORDER BY e.nombre_completo;
```

**4. Verificar si empresa puede actuar como solicitante:**

```sql
SELECT 
    e.nombre_completo,
    CASE 
        WHEN ea.entidad_id IS NOT NULL THEN 'SÍ'
        ELSE 'NO'
    END AS puede_solicitar,
    ea.email_notificaciones
FROM entidades e
JOIN entidades_empresas_servicio_publico ees ON e.id = ees.entidad_id
LEFT JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.cif_nif = :cif;
```

**5. Empresas por sector (usando notas o clasificación):**

```sql
-- Asumiendo que el sector está en campo NOTAS o en un futuro campo sector
SELECT 
    e.nombre_completo,
    e.cif_nif,
    ees.codigo_dir3
FROM entidades e
JOIN entidades_empresas_servicio_publico ees ON e.id = ees.entidad_id
WHERE e.notas ILIKE '%energía%'  -- Filtro ejemplo
AND e.activo = TRUE
ORDER BY e.nombre_completo;
```

---
