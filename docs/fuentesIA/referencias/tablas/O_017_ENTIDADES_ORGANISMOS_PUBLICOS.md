<!--
Tabla: ENTIDADES_ORGANISMOS_PUBLICOS
Generado manualmente
Fecha de creación: 01/02/2026
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### ENTIDADES_ORGANISMOS_PUBLICOS

Metadatos específicos de administraciones públicas y organismos oficiales que actúan como organismos consultados (informes técnicos/administrativos) en procedimientos de autorización.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ENTIDAD_ID** | INTEGER | Referencia a entidad base | NO | PK y FK → ENTIDADES(ID), UNIQUE, CASCADE |
| **CODIGO_DIR3** | VARCHAR(10) | Código DIR3 oficial del organismo | NO | UNIQUE. Identificación única para notificaciones vía SIR/BandeJA. Formato: EA0044689, A12002696, etc. |
| **OBSERVACIONES** | TEXT | Notas sobre competencias y ámbito | SÍ | Ámbito territorial, materias específicas, contactos alternativos, etc. |

#### Claves

- **PK:** `ENTIDAD_ID`
- **UNIQUE:** `CODIGO_DIR3`
- **FK:**
  - `ENTIDAD_ID` → `ENTIDADES(ID)` ON DELETE CASCADE

#### Índices Recomendados

- `CODIGO_DIR3` (único, búsqueda rápida por código oficial)

#### Relaciones

- **entidad**: ENTIDADES.id (FK, relación 1:1 con entidad base)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial con estructura minimalista (solo DIR3 + observaciones)

#### Filosofía

Tabla de metadatos para **organismos públicos** (administraciones y entidades oficiales):

- **Relación 1:1** con `ENTIDADES` mediante `ENTIDAD_ID` como PK y FK
- **Estructura minimalista:** Solo campos que NO están en `ENTIDADES`
- **CODIGO_DIR3 como clave de negocio:** Identificación oficial para comunicaciones interadministrativas
- **Sin representante:** La entidad es el organismo en sí (persona jurídica pública)
- **Roles múltiples posibles:** Un organismo puede ser consultado Y solicitante (doble entrada: esta tabla + `ENTIDADES_ADMINISTRADOS`)
- **Notificaciones vía SIR/BandeJA:** No usan sistema Notifica (a diferencia de administrados)

#### Campos que YA están en ENTIDADES (no duplicar)

**Todos estos datos viven en `ENTIDADES`:**

- `CIF_NIF`: Puede ser NULL o CIF compartido (AGE: S2833011F, Junta Andalucía: CIF único)
- `NOMBRE_COMPLETO`: Denominación oficial del organismo (ej: "Dirección General de Industria, Energía y Minas")
- `EMAIL`: Email general del organismo
- `TELEFONO`: Teléfono general
- `DIRECCION`, `CODIGO_POSTAL`, `MUNICIPIO_ID`: Sede del organismo

**Si se necesitan contactos específicos (email técnico diferente, teléfono consultas), usar campo `OBSERVACIONES`.**

#### CIF de Organismos Públicos: Casos Especiales

**Administración General del Estado (AGE):**
- **CIF único compartido:** `S2833011F`
- Todos los Ministerios, organismos autónomos, etc. comparten el mismo CIF
- Identificación real mediante **CODIGO_DIR3**

**Comunidades Autónomas (ej: Junta de Andalucía):**
- **CIF único compartido** por todas las Consejerías y Direcciones Generales
- Cada organismo se identifica mediante **CODIGO_DIR3**

**Ayuntamientos:**
- **CIF propio único** por ayuntamiento (letra P + código)
- Son entidades jurídicas independientes
- **No usan esta tabla** → Usan `ENTIDADES_AYUNTAMIENTOS`

**Entidades locales menores, consorcios, etc.:**
- Pueden tener CIF propio o compartido según su naturaleza jurídica

#### Sistema DIR3: Directorio Común de Unidades Orgánicas

**¿Qué es DIR3?**
- Directorio oficial de unidades orgánicas y oficinas de las AAPP españolas
- Obligatorio para facturación electrónica y comunicaciones interadministrativas
- Formato: 1-2 letras + 7-8 números (ej: `EA0044689`, `A12002696`)

**Uso en BDDAT:**
- Identificación única del organismo (más fiable que CIF)
- Clave para enviar notificaciones vía **SIR** (Servicio Integrado de Registro)
- Clave para enviar notificaciones vía **BandeJA** (Bandeja Electrónica de Justicia y Administración)

**Consulta de códigos DIR3:**
- Portal oficial: https://administracionelectronica.gob.es/ctt/dir3
- Descargas: https://administracionelectronica.gob.es/ctt/dir3/descargas

#### Ejemplos de Entidades (tipos)

**Administración General del Estado:**
- Ministerios (Transición Ecológica, Defensa, Fomento, etc.)
- Organismos autónomos (ADIF, Puertos del Estado, AESA, etc.)
- Confederaciones Hidrográficas
- Demarcaciones de Carreteras

**Comunidades Autónomas:**
- Consejerías (Medio Ambiente, Agricultura, Cultura, etc.)
- Direcciones Generales (Industria y Energía, Patrimonio, etc.)
- Agencias autonómicas

**Otros:**
- Diputaciones Provinciales (aunque pueden usar `ENTIDADES_DIPUTACIONES`)
- Consorcios interadministrativos
- Entidades locales menores

#### Roles Múltiples: Organismo Consultado Y Solicitante

**Escenario:** Consejería de Medio Ambiente solicita autorización para instalación eléctrica en depuradora propia

**Registros necesarios:**

1. **ENTIDADES** (tabla base):
   - `cif_nif`: CIF único Junta Andalucía (o NULL)
   - `nombre_completo`: "Consejería de Agricultura, Agua y Desarrollo Rural"
   - `tipo_entidad_id`: ORGANISMO_PUBLICO

2. **ENTIDADES_ORGANISMOS_PUBLICOS** (rol: consultado):
   - `codigo_dir3`: "A12002696" (código oficial)
   - `observaciones`: "Competencias: medio ambiente, agua, agricultura. Ámbito: Andalucía"

3. **ENTIDADES_ADMINISTRADOS** (rol: solicitante):
   - `email_notificaciones`: "notifica.medioambiente@juntadeandalucia.es"
   - `representante_nif_cif`: NULL (gestión corporativa)
   - `representante_nombre`: NULL

**Filtrado automático en interfaz:**

```sql
-- Contexto: Solicitar informe (fase CONSULTAS)
-- Solo aparecen organismos con tipo ORGANISMO_PUBLICO + otros consultables
SELECT e.* FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.puede_ser_consultado = TRUE;

-- Contexto: Crear solicitud
-- Solo aparecen entidades con registro en ENTIDADES_ADMINISTRADOS
SELECT e.* FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE;
```

#### Flujo UX: Copia de Datos entre Roles

**Aplica la misma lógica que `ENTIDADES_EMPRESAS_SERVICIO_PUBLICO`:**

1. Usuario introduce CIF o nombre que ya existe
2. Sistema detecta roles activos
3. Sistema ofrece copiar datos de rol existente (si aplica)
4. Usuario selecciona o introduce datos nuevos

**Nota:** En organismos públicos, el campo más relevante para copiar es `email_notificaciones` (si actúa como solicitante).

#### Reglas de Negocio

1. **CODIGO_DIR3 obligatorio** (NOT NULL, UNIQUE)
2. **CIF_NIF opcional** en `ENTIDADES` (puede ser NULL o compartido)
3. **Sin representante** (no aplican campos `REPRESENTANTE_*`)
4. **Múltiples roles:** Un organismo puede estar en esta tabla Y en `ENTIDADES_ADMINISTRADOS`
5. **Notificaciones interadministrativas:** Usar CODIGO_DIR3 para SIR/BandeJA, no email Notifica
6. **Validación DIR3:** Formato alfanumérico, 8-10 caracteres

#### Validaciones

**Validación Python:**

```python
import re

def validar_codigo_dir3(codigo):
    """
    Valida formato de código DIR3.
    Formato: 1-2 letras + 7-8 números
    Ejemplos válidos: EA0044689, A12002696
    """
    if not codigo:
        return False
    
    # Patrón: 1-2 letras mayúsculas + 7-8 dígitos
    patron = r'^[A-Z]{1,2}\d{7,8}$'
    return re.match(patron, codigo.upper()) is not None

class EntidadOrganismoPublico(db.Model):
    # ...
    
    @validates('codigo_dir3')
    def validate_codigo_dir3(self, key, value):
        if not value:
            raise ValueError("Código DIR3 es obligatorio")
        
        value_upper = value.upper().strip()
        
        if not validar_codigo_dir3(value_upper):
            raise ValueError(
                f"Código DIR3 inválido: {value}. "
                "Formato esperado: 1-2 letras + 7-8 dígitos (ej: EA0044689)"
            )
        
        return value_upper
```

**Validación en interfaz:**

```javascript
// Validación cliente (JavaScript)
function validarDIR3(codigo) {
    const patron = /^[A-Z]{1,2}\d{7,8}$/;
    return patron.test(codigo.toUpperCase());
}
```

#### Consultas Frecuentes

**1. Listar organismos con su DIR3:**

```sql
SELECT 
    e.id,
    e.nombre_completo,
    eop.codigo_dir3,
    e.email,
    e.telefono
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE e.activo = TRUE
ORDER BY e.nombre_completo;
```

**2. Buscar organismo por código DIR3:**

```sql
SELECT e.*, eop.*
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE eop.codigo_dir3 = :codigo_dir3;
```

**3. Organismos que son consultados Y solicitantes:**

```sql
SELECT 
    e.nombre_completo,
    eop.codigo_dir3,
    ea.email_notificaciones
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE;
```

**4. Organismos de la Administración General del Estado (AGE):**

```sql
SELECT e.*, eop.*
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE e.cif_nif = 'S2833011F'  -- CIF único AGE
OR eop.codigo_dir3 LIKE 'E%'    -- Códigos DIR3 estatales
ORDER BY e.nombre_completo;
```

---
