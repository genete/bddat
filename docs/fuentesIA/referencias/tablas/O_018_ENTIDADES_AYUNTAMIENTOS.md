<!--
Tabla: ENTIDADES_AYUNTAMIENTOS
Generado manualmente
Fecha de creación: 01/02/2026
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### ENTIDADES_AYUNTAMIENTOS

Metadatos específicos de corporaciones locales (ayuntamientos) que pueden actuar con múltiples roles: organismo consultado, solicitante ocasional y publicador de anuncios oficiales.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ENTIDAD_ID** | INTEGER | Referencia a entidad base | NO | PK y FK → ENTIDADES(ID), UNIQUE, CASCADE |
| **CODIGO_DIR3** | VARCHAR(10) | Código DIR3 oficial del ayuntamiento | NO | UNIQUE. Para notificaciones SIR cuando actúa como organismo consultado |
| **OBSERVACIONES** | TEXT | Notas adicionales | SÍ | Horarios atención, contactos específicos, etc. |

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

Tabla de metadatos para **ayuntamientos** (corporaciones locales municipales):

- **Relación 1:1** con `ENTIDADES` mediante `ENTIDAD_ID` como PK y FK
- **Estructura minimalista:** Solo campos que NO están en `ENTIDADES`
- **CODIGO_DIR3 como clave de negocio:** Identificación oficial para comunicaciones interadministrativas
- **Sin representante:** La entidad es la corporación en sí (persona jurídica pública)
- **Múltiples roles posibles:** Solicitante + Consultado + Publicador (triple entrada posible)
- **Notificaciones:** SIR (DIR3) cuando actúa como organismo, Notifica cuando actúa como solicitante

#### Campos que YA están en ENTIDADES (no duplicar)

**Todos estos datos viven en `ENTIDADES`:**

- `CIF_NIF`: CIF formato `P` + código INE (7 dígitos) + dígito control (ej: `P2807901D` - Ayto. Madrid)
- `NOMBRE_COMPLETO`: Denominación oficial (ej: "Ayuntamiento de Madrid", "Concello de Vigo")
- `EMAIL`: Email general corporativo
- `TELEFONO`: Teléfono general
- `DIRECCION`, `CODIGO_POSTAL`: Sede del ayuntamiento (Casa Consistorial)
- `MUNICIPIO_ID`: FK a MUNICIPIOS → **El ayuntamiento ES el municipio que gestiona**

**Si se necesitan contactos específicos (email urbanismo, teléfono medio ambiente), usar campo `OBSERVACIONES`.**

#### CIF de Ayuntamientos

**Formato obligatorio:**
- Letra **P** (personas jurídicas públicas)
- 7 dígitos del código INE del municipio
- 1 dígito de control

**Ejemplos reales:**
- Madrid: `P2807901D` (INE: 28079)
- Barcelona: `P0801900J` (INE: 08019)
- Valencia: `P4690000H` (INE: 46900)
- Sevilla: `P4109100I` (INE: 41091)
- Alcobendas: `P2800700F` (INE: 28007)

**Características:**
- CIF único por ayuntamiento (no compartido como en AGE o CCAA)
- Cada ayuntamiento es entidad jurídica independiente
- CIF obligatorio (NOT NULL en `ENTIDADES.CIF_NIF`)

#### Sistema DIR3: Ayuntamientos

**¿Qué es DIR3 para ayuntamientos?**
- Código oficial de la unidad orgánica del ayuntamiento en DIR3
- Obligatorio para facturación electrónica y comunicaciones interadministrativas
- Formato: 1-2 letras + 7-8 números (ej: `L01410084`)

**Uso en BDDAT:**
- Identificación única para notificaciones vía **SIR** cuando el ayuntamiento actúa como **organismo consultado** (emite informe)
- NO se usa para notificar cuando actúa como **solicitante** (ahí usa Notifica con email)

**Consulta de códigos DIR3:**
- Portal oficial: https://administracionelectronica.gob.es/ctt/dir3
- Descargas: https://administracionelectronica.gob.es/ctt/dir3/descargas

#### Múltiples Roles: Ayuntamiento con Triple Capacidad

**Escenario:** Ayuntamiento de Alcorcón actúa en 3 roles diferentes

**Registros necesarios:**

1. **ENTIDADES** (tabla base):
   - `cif_nif`: "P2800600A" (CIF único)
   - `nombre_completo`: "Ayuntamiento de Alcorcón"
   - `tipo_entidad_id`: AYUNTAMIENTO
   - `municipio_id`: FK al municipio de Alcorcón

2. **ENTIDADES_AYUNTAMIENTOS** (rol: consultado + publicador):
   - `codigo_dir3`: "L01280061" (código oficial)
   - `observaciones`: "Horario: L-V 9-14h. Email urbanismo: urbanismo@aytoalcorcon.es"

3. **ENTIDADES_ADMINISTRADOS** (rol: solicitante ocasional):
   - `email_notificaciones`: "notifica@aytoalcorcon.es"
   - `representante_nif_cif`: NULL (gestión corporativa)
   - `representante_nombre`: NULL

**Filtrado automático en interfaz:**

```sql
-- Contexto: Solicitar informe urbanismo (fase CONSULTAS)
-- Aparecen ayuntamientos con tipo AYUNTAMIENTO
SELECT e.* FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.puede_ser_consultado = TRUE;

-- Contexto: Crear solicitud (ayto. solicita instalación propia)
-- Solo aparecen entidades con registro en ENTIDADES_ADMINISTRADOS
SELECT e.* FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE;

-- Contexto: Publicar en tablón municipal
-- Solo aparecen ayuntamientos
SELECT e.* FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.codigo = 'AYUNTAMIENTO'
AND e.activo = TRUE;
```

#### Flujo UX: Copia de Datos entre Roles

**Aplica la misma lógica que otras tablas de metadatos:**

1. Usuario introduce CIF o nombre que ya existe
2. Sistema detecta roles activos del ayuntamiento
3. Sistema ofrece copiar datos de rol existente (si aplica)
4. Usuario selecciona o introduce datos nuevos

**Nota:** El campo más relevante para copiar es `email_notificaciones` (si actúa como solicitante).

#### Reglas de Negocio

1. **CODIGO_DIR3 obligatorio** (NOT NULL, UNIQUE)
2. **CIF_NIF obligatorio** en `ENTIDADES` (formato P+INE+control)
3. **Sin representante** (no aplican campos `REPRESENTANTE_*`)
4. **Múltiples roles:** Un ayuntamiento puede estar en esta tabla Y en `ENTIDADES_ADMINISTRADOS`
5. **Notificaciones duales:**
   - Como **organismo consultado**: SIR (usa CODIGO_DIR3)
   - Como **solicitante**: Notifica (usa email de `ENTIDADES_ADMINISTRADOS`)
6. **Publicación anuncios:** Tablón edictos propio según Ley 39/2015 Art. 45.4 (obligación vs administrados, no dato BDDAT)
7. **Validación DIR3:** Formato alfanumérico, 8-10 caracteres
8. **MUNICIPIO_ID en ENTIDADES:** El ayuntamiento gestiona el municipio al que pertenece (relación 1:1)

#### Tablón de Edictos Electrónico: Aclaración Legal

**Ley 39/2015, Artículo 45.4:**

> "Las Administraciones Locales deberán tener un tablón de edictos electrónico único, donde se publicarán todos los anuncios que deban publicarse en el tablón de edictos de la entidad."

**Interpretación correcta:**
- **Obligación:** Para que **ciudadanos** puedan leer notificaciones públicas
- **Destinatarios:** Administrados (personas físicas/jurídicas privadas)
- **Sistema BDDAT:** No publica directamente en tablón municipal

**Flujo real desde BDDAT:**

```
BDDAT → Sistema SIR (Servicio Integrado de Registro) → Ayuntamiento recibe notificación
                                                      ↓
                                            Ayuntamiento publica en su tablón electrónico
                                                      ↓
                                            Ciudadanos leen en sede electrónica municipal
```

**Conclusión:**
- **NO almacenamos URL del tablón** (no es dato estructurado que necesitemos)
- **Usamos SIR** para enviar anuncios al ayuntamiento
- **El ayuntamiento** es responsable de publicar en su tablón (sede electrónica)
- **Campo URL_TABLON_EDICTOS no existe** (estaría NULL eternamente)

#### Validaciones

**Validación Python:**

```python
import re

def validar_cif_ayuntamiento(cif):
    """
    Valida CIF de ayuntamiento.
    Formato: P + 7 dígitos INE + 1 dígito control
    Ejemplo válido: P2807901D
    """
    if not cif:
        return False
    
    # Patrón: P + 7 dígitos + 1 letra/dígito
    patron = r'^P\d{7}[A-Z0-9]$'
    return re.match(patron, cif.upper()) is not None

def validar_codigo_dir3(codigo):
    """
    Valida formato de código DIR3.
    Formato: 1-2 letras + 7-8 números
    Ejemplos válidos: L01410084, A12002696
    """
    if not codigo:
        return False
    
    # Patrón: 1-2 letras mayúsculas + 7-8 dígitos
    patron = r'^[A-Z]{1,2}\d{7,8}$'
    return re.match(patron, codigo.upper()) is not None

class EntidadAyuntamiento(db.Model):
    # ...
    
    @validates('codigo_dir3')
    def validate_codigo_dir3(self, key, value):
        if not value:
            raise ValueError("Código DIR3 es obligatorio")
        
        value_upper = value.upper().strip()
        
        if not validar_codigo_dir3(value_upper):
            raise ValueError(
                f"Código DIR3 inválido: {value}. "
                "Formato esperado: 1-2 letras + 7-8 dígitos (ej: L01410084)"
            )
        
        return value_upper
```

**Validación en interfaz:**

```javascript
// Validación cliente (JavaScript)
function validarCIFAyuntamiento(cif) {
    const patron = /^P\d{7}[A-Z0-9]$/;
    return patron.test(cif.toUpperCase());
}

function validarDIR3(codigo) {
    const patron = /^[A-Z]{1,2}\d{7,8}$/;
    return patron.test(codigo.toUpperCase());
}
```

#### Consultas Frecuentes

**1. Listar ayuntamientos con su DIR3 y CIF:**

```sql
SELECT 
    e.id,
    e.nombre_completo,
    e.cif_nif,
    ea.codigo_dir3,
    e.email,
    e.telefono,
    m.nombre AS municipio
FROM entidades e
JOIN entidades_ayuntamientos ea ON e.id = ea.entidad_id
JOIN municipios m ON e.municipio_id = m.id
WHERE e.activo = TRUE
ORDER BY e.nombre_completo;
```

**2. Buscar ayuntamiento por código DIR3:**

```sql
SELECT e.*, ea.*
FROM entidades e
JOIN entidades_ayuntamientos ea ON e.id = ea.entidad_id
WHERE ea.codigo_dir3 = :codigo_dir3;
```

**3. Buscar ayuntamiento por CIF:**

```sql
SELECT e.*, ea.*
FROM entidades e
JOIN entidades_ayuntamientos ea ON e.id = ea.entidad_id
WHERE e.cif_nif = :cif;
```

**4. Ayuntamientos que son consultados Y solicitantes:**

```sql
SELECT 
    e.nombre_completo,
    e.cif_nif,
    ea.codigo_dir3,
    ead.email_notificaciones
FROM entidades e
JOIN entidades_ayuntamientos ea ON e.id = ea.entidad_id
JOIN entidades_administrados ead ON e.id = ead.entidad_id
WHERE e.activo = TRUE
ORDER BY e.nombre_completo;
```

**5. Ayuntamientos de una provincia específica:**

```sql
SELECT 
    e.nombre_completo,
    m.nombre AS municipio,
    p.nombre AS provincia,
    ea.codigo_dir3
FROM entidades e
JOIN entidades_ayuntamientos ea ON e.id = ea.entidad_id
JOIN municipios m ON e.municipio_id = m.id
JOIN provincias p ON m.provincia_id = p.id
WHERE p.codigo = '28'  -- Madrid
AND e.activo = TRUE
ORDER BY m.nombre;
```

**6. Verificar si un ayuntamiento puede actuar como solicitante:**

```sql
SELECT 
    e.nombre_completo,
    CASE 
        WHEN ead.entidad_id IS NOT NULL THEN 'SÍ'
        ELSE 'NO'
    END AS puede_solicitar
FROM entidades e
JOIN entidades_ayuntamientos ea ON e.id = ea.entidad_id
LEFT JOIN entidades_administrados ead ON e.id = ead.entidad_id
WHERE e.cif_nif = :cif;
```

---
