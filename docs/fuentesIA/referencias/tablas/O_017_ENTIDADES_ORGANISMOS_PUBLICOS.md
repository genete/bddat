<!--
Tabla: ENTIDADES_ORGANISMOS_PUBLICOS
Generado manualmente
Fecha de creación: 01/02/2026
Última actualización: 04/02/2026
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### ENTIDADES_ORGANISMOS_PUBLICOS

Metadatos específicos de administraciones públicas y organismos oficiales que actúan como organismos consultados (informes técnicos/administrativos) en procedimientos de autorización. Incluye información sobre ámbito territorial, tipo de organismo y vigencia temporal.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ENTIDAD_ID** | INTEGER | Referencia a entidad base | NO | PK y FK → ENTIDADES(ID), UNIQUE, CASCADE |
| **CODIGO_DIR3** | VARCHAR(20) | Código DIR3 oficial del organismo | SÍ | Identificación para notificaciones vía SIR/BandeJA. Formato: EA0044689, A12002696 |
| **AMBITO** | VARCHAR(50) | Ámbito del organismo | SÍ | ESTATAL, AUTONOMICO, LOCAL |
| **TIPO_ORGANISMO** | VARCHAR(50) | Tipo específico de organismo | SÍ | Consejería, Ministerio, Confederación, Entidad Pública, etc. |
| **LEGISLATURA** | VARCHAR(50) | Legislatura asociada | SÍ | Ej: "2019-2023", "2023-2027" |
| **FECHA_DESDE** | DATE | Fecha inicio vigencia del organismo | SÍ | Desde cuando está operativo |
| **FECHA_HASTA** | DATE | Fecha fin vigencia del organismo | SÍ | NULL si sigue activo |

#### Claves

- **PK:** `ENTIDAD_ID`
- **FK:**
  - `ENTIDAD_ID` → `ENTIDADES(ID)` ON DELETE CASCADE

#### Índices

- `ix_public_entidades_organismos_publicos_codigo_dir3` (sobre `CODIGO_DIR3`)
- `ix_public_entidades_organismos_publicos_ambito` (sobre `AMBITO`)
- `ix_public_entidades_organismos_publicos_legislatura` (sobre `LEGISLATURA`)

#### Relaciones

- **entidad**: ENTIDADES.id (FK, relación 1:1 con entidad base)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial con estructura minimalista
- **v1.1** (04/02/2026): Sincronización con schema.sql - Agregar campos ambito, tipo_organismo, legislatura, fechas. codigo_dir3 nullable y VARCHAR(20)

#### Filosofía

Tabla de metadatos para **organismos públicos** (administraciones y entidades oficiales):

- **Relación 1:1** con `ENTIDADES` mediante `ENTIDAD_ID` como PK y FK
- **Estructura enriquecida:** Campos de clasificación y vigencia temporal
- **CODIGO_DIR3 opcional:** Puede ser NULL (organismos históricos o sin código)
- **Sin representante:** La entidad es el organismo en sí (persona jurídica pública)
- **Roles múltiples posibles:** Un organismo puede ser consultado Y solicitante (doble entrada: esta tabla + `ENTIDADES_ADMINISTRADOS`)
- **Vigencia temporal:** Organismos que cambian con legislaturas o reorganizaciones administrativas
- **Notificaciones interadministrativas:** Sistema SIR (Servicio Integrado de Registro) usando CODIGO_DIR3

#### Campos que YA están en ENTIDADES (no duplicar)

**Todos estos datos viven en `ENTIDADES`:**

- `CIF_NIF`: Puede ser NULL o CIF compartido (AGE: S2833011F, Junta Andalucía: CIF único)
- `NOMBRE_COMPLETO`: Denominación oficial del organismo (ej: "Dirección General de Industria, Energía y Minas")
- `EMAIL`: Email general del organismo
- `TELEFONO`: Teléfono general
- `DIRECCION`, `CODIGO_POSTAL`, `MUNICIPIO_ID`: Sede del organismo
- `ACTIVO`: Borrado lógico
- `NOTAS`: Observaciones generales

#### Campo: AMBITO

**Valores típicos:**

- `ESTATAL`: Organismos de la Administración General del Estado (AGE)
  - Ministerios, Direcciones Generales, Organismos Autónomos
  - Ejemplos: Ministerio para la Transición Ecológica, MITECO, Confederación Hidrográfica
  
- `AUTONOMICO`: Organismos de Comunidades Autónomas
  - Consejerías, Direcciones Generales, Agencias autonómicas
  - Ejemplos: Junta de Andalucía, Xunta de Galicia
  
- `LOCAL`: Organismos de Administración Local (no ayuntamientos individuales)
  - Diputaciones, Consorcios, Mancomunidades
  - **Nota:** Ayuntamientos usan tabla `ENTIDADES_AYUNTAMIENTOS`

**Uso:**
- Clasificación para estadísticas
- Filtrado en interfaces de consulta
- Asignación automática de competencias según ámbito

#### Campo: TIPO_ORGANISMO

**Ejemplos de valores:**

- `Ministerio`: Ministerio para la Transición Ecológica y el Reto Demográfico
- `Dirección General`: Dirección General de Política Energética y Minas
- `Organismo Autónomo`: ADIF, Puertos del Estado
- `Consejería`: Consejería de Agricultura, Agua y Desarrollo Rural
- `Viceconsejería`: Viceconsejería de Medio Ambiente
- `Confederación`: Confederación Hidrográfica del Miño-Sil
- `Agencia`: Agencia Andaluza de la Energía
- `Entidad Pública`: Entidad Pública Empresarial de X

**Uso:**
- Clasificación fina para organización administrativa
- Ayuda en autocompletado de formularios
- Filtrado por nivel jerárquico

#### Campo: LEGISLATURA

**Formato:** "YYYY-YYYY" (año inicio - año fin)

**Ejemplos:**
- `2019-2023`: XIV Legislatura
- `2023-2027`: XV Legislatura (actual)
- `2015-2019`: Legislatura anterior

**Uso:**
- Tracking de reorganizaciones administrativas tras cambios de gobierno
- Consulta de organismos vigentes en momento histórico
- Auditoría de cambios de competencias

**Nota:** Puede ser NULL si el organismo no está vinculado a legislaturas (ej: organismos técnicos permanentes)

#### Campos: FECHA_DESDE / FECHA_HASTA

**FECHA_DESDE:**
- Fecha en que el organismo comenzó a operar
- Puede coincidir con inicio de legislatura o ser independiente
- NULL si no se conoce fecha exacta (organismos históricos)

**FECHA_HASTA:**
- NULL = organismo activo actualmente
- Fecha = organismo cesado/reorganizado/fusionado
- Permite mantener histórico de organismos que ya no existen

**Ejemplos:**

```sql
-- Organismo actual (Ministerio actual)
fecha_desde = '2020-01-13'  -- Formación gobierno
fecha_hasta = NULL           -- Activo

-- Organismo histórico (Ministerio anterior, reorganizado)
fecha_desde = '2016-11-04'
fecha_hasta = '2020-01-13'   -- Reorganización

-- Consejería tras cambio autonómico
fecha_desde = '2022-07-20'  -- Nueva legislatura
fecha_hasta = NULL           -- Activa
```

**Uso:**
- Mantener histórico de informes emitidos por organismos desaparecidos
- Validar competencias según fecha de solicitud
- Migración automática a nuevo organismo competente

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
- En Junta de Andalucía: Sistema **BandeJA** (Bandeja de la Junta de Andalucía) para comunicaciones interiores electrónicas

**Campo NULLABLE:**
- Organismos históricos pueden no tener DIR3
- Organismos extranjeros o especiales sin código DIR3
- Organismos en proceso de registro

**Consulta de códigos DIR3:**
- Portal oficial: https://administracionelectronica.gob.es/ctt/dir3
- Descargas: https://administracionelectronica.gob.es/ctt/dir3/descargas

#### Roles Múltiples: Organismo Consultado Y Solicitante

**Escenario:** Consejería de Medio Ambiente solicita autorización para instalación eléctrica en depuradora propia

**Registros necesarios:**

1. **ENTIDADES** (tabla base):
   - `cif_nif`: CIF único Junta Andalucía (o NULL)
   - `nombre_completo`: "Consejería de Agricultura, Agua y Desarrollo Rural"
   - `tipo_entidad_id`: ORGANISMO_PUBLICO

2. **ENTIDADES_ORGANISMOS_PUBLICOS** (rol: consultado):
   - `codigo_dir3`: "A12002696" (código oficial)
   - `ambito`: "AUTONOMICO"
   - `tipo_organismo`: "Consejería"
   - `legislatura`: "2023-2027"
   - `fecha_desde`: "2022-07-20"
   - `fecha_hasta`: NULL

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
WHERE te.puede_ser_consultado = TRUE
AND e.activo = TRUE;

-- Contexto: Crear solicitud
-- Solo aparecen entidades con registro en ENTIDADES_ADMINISTRADOS
SELECT e.* FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE;
```

#### Reglas de Negocio

1. **CODIGO_DIR3 opcional** (puede ser NULL)
2. **CIF_NIF opcional** en `ENTIDADES` (puede ser NULL o compartido)
3. **Sin representante** (no aplican campos `REPRESENTANTE_*`)
4. **Múltiples roles:** Un organismo puede estar en esta tabla Y en `ENTIDADES_ADMINISTRADOS`
5. **Notificaciones interadministrativas:** Usar CODIGO_DIR3 para SIR, no email Notifica
6. **Vigencia temporal:** `fecha_hasta` NULL = organismo activo
7. **Reorganizaciones:** Crear nuevo registro con nuevo `entidad_id` y cerrar anterior con `fecha_hasta`

#### Validaciones

**Validación Python:**

```python
import re
from datetime import date

def validar_codigo_dir3(codigo):
    """
    Valida formato de código DIR3.
    Formato: 1-2 letras + 7-8 números
    Ejemplos válidos: EA0044689, A12002696
    """
    if not codigo:
        return True  # Nullable
    
    # Patrón: 1-2 letras mayúsculas + 7-8 dígitos
    patron = r'^[A-Z]{1,2}\d{7,8}$'
    return re.match(patron, codigo.upper()) is not None

def validar_legislatura(legislatura):
    """
    Valida formato de legislatura: YYYY-YYYY
    """
    if not legislatura:
        return True  # Nullable
    
    patron = r'^\d{4}-\d{4}$'
    if not re.match(patron, legislatura):
        return False
    
    inicio, fin = legislatura.split('-')
    return int(inicio) < int(fin)

class EntidadOrganismoPublico(db.Model):
    # ...
    
    @validates('codigo_dir3')
    def validate_codigo_dir3(self, key, value):
        if not value:
            return None  # Nullable
        
        value_upper = value.upper().strip()
        
        if not validar_codigo_dir3(value_upper):
            raise ValueError(
                f"Código DIR3 inválido: {value}. "
                "Formato esperado: 1-2 letras + 7-8 dígitos (ej: EA0044689)"
            )
        
        return value_upper
    
    @validates('ambito')
    def validate_ambito(self, key, value):
        if not value:
            return None
        
        ambitos_validos = ['ESTATAL', 'AUTONOMICO', 'LOCAL']
        value_upper = value.upper().strip()
        
        if value_upper not in ambitos_validos:
            raise ValueError(
                f"Ámbito inválido: {value}. "
                f"Valores permitidos: {', '.join(ambitos_validos)}"
            )
        
        return value_upper
    
    @validates('legislatura')
    def validate_legislatura(self, key, value):
        if not value:
            return None
        
        if not validar_legislatura(value):
            raise ValueError(
                f"Legislatura inválida: {value}. "
                "Formato esperado: YYYY-YYYY (ej: 2023-2027)"
            )
        
        return value
    
    @validates('fecha_hasta')
    def validate_fecha_hasta(self, key, value):
        if not value:
            return None  # NULL = activo
        
        if self.fecha_desde and value < self.fecha_desde:
            raise ValueError(
                "fecha_hasta no puede ser anterior a fecha_desde"
            )
        
        return value
```

#### Consultas Frecuentes

**1. Listar organismos activos con su clasificación:**

```sql
SELECT 
    e.id,
    e.nombre_completo,
    eop.codigo_dir3,
    eop.ambito,
    eop.tipo_organismo,
    eop.legislatura,
    e.email,
    e.telefono
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE e.activo = TRUE
AND (eop.fecha_hasta IS NULL OR eop.fecha_hasta > CURRENT_DATE)
ORDER BY eop.ambito, e.nombre_completo;
```

**2. Buscar organismo por código DIR3:**

```sql
SELECT e.*, eop.*
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE eop.codigo_dir3 = :codigo_dir3;
```

**3. Organismos de ámbito ESTATAL activos:**

```sql
SELECT 
    e.nombre_completo,
    eop.codigo_dir3,
    eop.tipo_organismo
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE eop.ambito = 'ESTATAL'
AND e.activo = TRUE
AND (eop.fecha_hasta IS NULL OR eop.fecha_hasta > CURRENT_DATE)
ORDER BY e.nombre_completo;
```

**4. Organismos de legislatura actual:**

```sql
SELECT 
    e.nombre_completo,
    eop.codigo_dir3,
    eop.ambito,
    eop.legislatura,
    eop.fecha_desde
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE eop.legislatura = '2023-2027'
AND e.activo = TRUE
ORDER BY eop.ambito, e.nombre_completo;
```

**5. Organismos que cesaron (histórico):**

```sql
SELECT 
    e.nombre_completo,
    eop.codigo_dir3,
    eop.ambito,
    eop.fecha_desde,
    eop.fecha_hasta,
    eop.legislatura
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE eop.fecha_hasta IS NOT NULL
ORDER BY eop.fecha_hasta DESC;
```

**6. Organismos que son consultados Y solicitantes:**

```sql
SELECT 
    e.nombre_completo,
    eop.codigo_dir3,
    eop.ambito,
    ea.email_notificaciones
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE
AND (eop.fecha_hasta IS NULL OR eop.fecha_hasta > CURRENT_DATE);
```

**7. Organismos por tipo (ej: Consejerías):**

```sql
SELECT 
    e.nombre_completo,
    eop.codigo_dir3,
    eop.legislatura
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE eop.tipo_organismo = 'Consejería'
AND e.activo = TRUE
AND (eop.fecha_hasta IS NULL OR eop.fecha_hasta > CURRENT_DATE)
ORDER BY e.nombre_completo;
```

---
