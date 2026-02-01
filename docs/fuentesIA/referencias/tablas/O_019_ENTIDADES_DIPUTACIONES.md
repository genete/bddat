<!--
Tabla: ENTIDADES_DIPUTACIONES
Generado manualmente
Fecha de creación: 01/02/2026
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### ENTIDADES_DIPUTACIONES

Metadatos específicos de diputaciones provinciales que pueden actuar con múltiples roles: organismo consultado, solicitante ocasional y publicador en Boletín Oficial Provincial (BOP).

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ENTIDAD_ID** | INTEGER | Referencia a entidad base | NO | PK y FK → ENTIDADES(ID), UNIQUE, CASCADE |
| **CODIGO_DIR3** | VARCHAR(10) | Código DIR3 oficial de la diputación | NO | UNIQUE. Para notificaciones SIR cuando actúa como organismo consultado |
| **EMAIL_PUBLICACION_BOP** | VARCHAR(255) | Email para solicitar publicaciones en BOP | SÍ | Ej: boletin@bopcadiz.org. Método tradicional: correo con datos pagador + texto a publicar |
| **OBSERVACIONES** | TEXT | Notas adicionales | SÍ | Procedimientos publicación, tarifas, plataformas alternativas, contactos específicos |

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

- **v1.0** (01/02/2026): Creación inicial con estructura minimalista (DIR3 + email publicación BOP + observaciones)

#### Filosofía

Tabla de metadatos para **diputaciones provinciales**:

- **Relación 1:1** con `ENTIDADES` mediante `ENTIDAD_ID` como PK y FK
- **Estructura minimalista:** Solo campos que NO están en `ENTIDADES`
- **CODIGO_DIR3 como clave de negocio:** Identificación oficial para comunicaciones interadministrativas
- **EMAIL_PUBLICACION_BOP:** Método real de trabajo (al menos Cádiz y otras provincias)
- **Sin representante:** La entidad es la corporación en sí (persona jurídica pública)
- **Múltiples roles posibles:** Solicitante + Consultado + Publicador BOP
- **Notificaciones:** SIR (DIR3) cuando actúa como organismo, Notifica cuando actúa como solicitante

#### Campos que YA están en ENTIDADES (no duplicar)

**Todos estos datos viven en `ENTIDADES`:**

- `CIF_NIF`: CIF formato `P` + código provincia + dígito control (ej: `P2800000J` - Diputación Madrid)
- `NOMBRE_COMPLETO`: Denominación oficial (ej: "Diputación Provincial de Cádiz", "Diputació de València")
- `EMAIL`: Email general corporativo
- `TELEFONO`: Teléfono general
- `DIRECCION`, `CODIGO_POSTAL`: Sede de la diputación (Palacio Provincial)
- `MUNICIPIO_ID`: FK a municipio donde tiene sede (capital provincia), pero NO gestiona ese municipio

**Si se necesitan contactos específicos (email área técnica, teléfono informática), usar campo `OBSERVACIONES`.**

#### CIF de Diputaciones

**Formato obligatorio:**
- Letra **P** (personas jurídicas públicas)
- Código de provincia (2 dígitos) + 5 ceros
- 1 dígito de control

**Ejemplos reales:**
- Madrid: `P2800000J` (provincia 28)
- Cádiz: `P1100000B` (provincia 11)
- Valencia: `P4600000A` (provincia 46)
- Sevilla: `P4100000G` (provincia 41)
- Barcelona: `P0800000H` (provincia 08)

**Características:**
- CIF único por diputación (no compartido)
- Cada diputación es entidad jurídica independiente
- CIF obligatorio (NOT NULL en `ENTIDADES.CIF_NIF`)

#### Sistema DIR3: Diputaciones

**¿Qué es DIR3 para diputaciones?**
- Código oficial de la unidad orgánica de la diputación en DIR3
- Obligatorio para facturación electrónica y comunicaciones interadministrativas
- Formato: 1-2 letras + 7-8 números (ej: `L01110002`)

**Uso en BDDAT:**
- Identificación única para notificaciones vía **SIR** cuando la diputación actúa como **organismo consultado** (emite informe)
- NO se usa para notificar cuando actúa como **solicitante** (ahí usa Notifica con email)

**Consulta de códigos DIR3:**
- Portal oficial: https://administracionelectronica.gob.es/ctt/dir3
- Descargas: https://administracionelectronica.gob.es/ctt/dir3/descargas

#### EMAIL_PUBLICACION_BOP: Método Real de Trabajo

**Sistema tradicional de publicación en BOP:**

1. **BDDAT prepara texto** del anuncio a publicar
2. **Se envía email** a dirección de publicaciones BOP:
   - Datos del pagador (organismo que solicita)
   - Texto completo del anuncio
   - Justificante de pago (si aplica)
3. **BOP procesa** y publica en próxima edición
4. **Confirmación** mediante publicación en boletín oficial

**Ejemplos reales de emails:**
- Cádiz: `boletin@bopcadiz.org`
- Valencia: `bop@dival.es`
- Sevilla: `bop@dipusevilla.es`
- Málaga: `bop@malaga.es`

**Campo nullable:**
- Algunas diputaciones pueden usar exclusivamente plataforma electrónica (SIR u otra)
- Si existe método alternativo, se documenta en `OBSERVACIONES`

#### BOP Cádiz: Caso Real Verificado

**Gestión del Boletín Oficial Provincial de Cádiz:**

- **Responsable:** Diputación Provincial de Cádiz
- **Concesionaria:** Asociación de la Prensa de Cádiz (CIF: G11013232)
- **Domicilio:** Calle Ancha, nº 6 - 11001 Cádiz
- **Email:** `boletin@bopcadiz.org`
- **Teléfonos:** 956 213 861 / 956 212 370
- **Web:** https://www.bopcadiz.es

**Fuente:** [Boletín Oficial Provincia Cádiz - Contacto](https://www.bopcadiz.es/contacto/)

**Procedimiento:**
- La Diputación de Cádiz contrata a la Asociación de la Prensa como concesionaria
- La Asociación gestiona la edición, publicación y administración del BOP
- Los organismos envían anuncios al email indicado

#### Múltiples Roles: Diputación con Triple Capacidad

**Escenario:** Diputación de Cádiz actúa en 3 roles diferentes

**Registros necesarios:**

1. **ENTIDADES** (tabla base):
   - `cif_nif`: "P1100000B" (CIF único)
   - `nombre_completo`: "Diputación Provincial de Cádiz"
   - `tipo_entidad_id`: DIPUTACION
   - `municipio_id`: FK a Cádiz capital (sede, NO gestión)

2. **ENTIDADES_DIPUTACIONES** (rol: consultado + publicador BOP):
   - `codigo_dir3`: "L01110002" (código oficial)
   - `email_publicacion_bop`: "boletin@bopcadiz.org"
   - `observaciones`: "Concesionaria: Asociación Prensa Cádiz. Tarifas: consultar Ordenanza. Publicación L-V días hábiles."

3. **ENTIDADES_ADMINISTRADOS** (rol: solicitante ocasional):
   - `email_notificaciones`: "notifica@dipucadiz.es"
   - `representante_nif_cif`: NULL (gestión corporativa)
   - `representante_nombre`: NULL

**Filtrado automático en interfaz:**

```sql
-- Contexto: Solicitar informe (fase CONSULTAS)
-- Aparecen diputaciones con tipo DIPUTACION
SELECT e.* FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.puede_ser_consultado = TRUE;

-- Contexto: Crear solicitud (diputación solicita instalación propia)
-- Solo aparecen entidades con registro en ENTIDADES_ADMINISTRADOS
SELECT e.* FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE;

-- Contexto: Publicar en BOP
-- Solo aparecen diputaciones
SELECT e.* FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.codigo = 'DIPUTACION'
AND e.activo = TRUE;
```

#### Diferencia con Ayuntamientos: Publicación

**AYUNTAMIENTOS:**
- Publican en su **tablón edictos municipal** (Ley 39/2015 Art. 45.4)
- BDDAT notifica vía **SIR** al ayuntamiento
- Ayuntamiento publica en su sede electrónica
- Sin campo `email_publicacion` (proceso interno del ayuntamiento)

**DIPUTACIONES:**
- Publican en **BOP** (Boletín Oficial Provincial)
- BDDAT solicita publicación vía **email** tradicional (método real)
- Campo `EMAIL_PUBLICACION_BOP` necesario (ej: `boletin@bopcadiz.org`)
- BOP puede estar gestionado por concesionaria (caso Cádiz: Asociación Prensa)

#### Flujo UX: Copia de Datos entre Roles

**Aplica la misma lógica que otras tablas de metadatos:**

1. Usuario introduce CIF o nombre que ya existe
2. Sistema detecta roles activos de la diputación
3. Sistema ofrece copiar datos de rol existente (si aplica)
4. Usuario selecciona o introduce datos nuevos

**Campos relevantes para copiar:**
- `email_notificaciones` (si actúa como solicitante)
- `email_publicacion_bop` (si ya existe registro previo)

#### Reglas de Negocio

1. **CODIGO_DIR3 obligatorio** (NOT NULL, UNIQUE)
2. **CIF_NIF obligatorio** en `ENTIDADES` (formato P+provincia+00000+control)
3. **EMAIL_PUBLICACION_BOP opcional** (nullable, algunas usan solo plataforma electrónica)
4. **Sin representante** (no aplican campos `REPRESENTANTE_*`)
5. **Múltiples roles:** Una diputación puede estar en esta tabla Y en `ENTIDADES_ADMINISTRADOS`
6. **Notificaciones duales:**
   - Como **organismo consultado**: SIR (usa CODIGO_DIR3)
   - Como **solicitante**: Notifica (usa email de `ENTIDADES_ADMINISTRADOS`)
7. **Publicación BOP:** Método tradicional email (datos pagador + texto anuncio)
8. **Validación DIR3:** Formato alfanumérico, 8-10 caracteres
9. **MUNICIPIO_ID en ENTIDADES:** Sede de la diputación (capital), NO implica gestión de ese municipio

#### Validaciones

**Validación Python:**

```python
import re

def validar_cif_diputacion(cif):
    """
    Valida CIF de diputación.
    Formato: P + código provincia (2 dígitos) + 00000 + dígito control
    Ejemplo válido: P2800000J (Diputación Madrid)
    """
    if not cif:
        return False
    
    # Patrón: P + 2 dígitos + 5 ceros + 1 letra/dígito
    patron = r'^P\d{2}00000[A-Z0-9]$'
    return re.match(patron, cif.upper()) is not None

def validar_codigo_dir3(codigo):
    """
    Valida formato de código DIR3.
    Formato: 1-2 letras + 7-8 números
    Ejemplos válidos: L01110002, A12002696
    """
    if not codigo:
        return False
    
    # Patrón: 1-2 letras mayúsculas + 7-8 dígitos
    patron = r'^[A-Z]{1,2}\d{7,8}$'
    return re.match(patron, codigo.upper()) is not None

def validar_email(email):
    """
    Valida formato básico de email.
    """
    if not email:
        return True  # Nullable
    
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

class EntidadDiputacion(db.Model):
    # ...
    
    @validates('codigo_dir3')
    def validate_codigo_dir3(self, key, value):
        if not value:
            raise ValueError("Código DIR3 es obligatorio")
        
        value_upper = value.upper().strip()
        
        if not validar_codigo_dir3(value_upper):
            raise ValueError(
                f"Código DIR3 inválido: {value}. "
                "Formato esperado: 1-2 letras + 7-8 dígitos (ej: L01110002)"
            )
        
        return value_upper
    
    @validates('email_publicacion_bop')
    def validate_email_publicacion(self, key, value):
        if value and not validar_email(value):
            raise ValueError(
                f"Email inválido: {value}. "
                "Formato esperado: usuario@dominio.ext"
            )
        
        return value.lower().strip() if value else None
```

**Validación en interfaz:**

```javascript
// Validación cliente (JavaScript)
function validarCIFDiputacion(cif) {
    const patron = /^P\d{2}00000[A-Z0-9]$/;
    return patron.test(cif.toUpperCase());
}

function validarDIR3(codigo) {
    const patron = /^[A-Z]{1,2}\d{7,8}$/;
    return patron.test(codigo.toUpperCase());
}

function validarEmail(email) {
    if (!email) return true; // Nullable
    const patron = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return patron.test(email);
}
```

#### Consultas Frecuentes

**1. Listar diputaciones con su DIR3, CIF y email publicación:**

```sql
SELECT 
    e.id,
    e.nombre_completo,
    e.cif_nif,
    ed.codigo_dir3,
    ed.email_publicacion_bop,
    e.email,
    e.telefono,
    p.nombre AS provincia
FROM entidades e
JOIN entidades_diputaciones ed ON e.id = ed.entidad_id
JOIN municipios m ON e.municipio_id = m.id
JOIN provincias p ON m.provincia_id = p.id
WHERE e.activo = TRUE
ORDER BY p.nombre;
```

**2. Buscar diputación por código DIR3:**

```sql
SELECT e.*, ed.*
FROM entidades e
JOIN entidades_diputaciones ed ON e.id = ed.entidad_id
WHERE ed.codigo_dir3 = :codigo_dir3;
```

**3. Buscar diputación por CIF:**

```sql
SELECT e.*, ed.*
FROM entidades e
JOIN entidades_diputaciones ed ON e.id = ed.entidad_id
WHERE e.cif_nif = :cif;
```

**4. Diputaciones que son consultadas Y solicitantes:**

```sql
SELECT 
    e.nombre_completo,
    e.cif_nif,
    ed.codigo_dir3,
    ed.email_publicacion_bop,
    ead.email_notificaciones
FROM entidades e
JOIN entidades_diputaciones ed ON e.id = ed.entidad_id
JOIN entidades_administrados ead ON e.id = ead.entidad_id
WHERE e.activo = TRUE
ORDER BY e.nombre_completo;
```

**5. Obtener email publicación BOP para una provincia:**

```sql
SELECT 
    p.nombre AS provincia,
    e.nombre_completo,
    ed.email_publicacion_bop,
    e.telefono
FROM entidades e
JOIN entidades_diputaciones ed ON e.id = ed.entidad_id
JOIN municipios m ON e.municipio_id = m.id
JOIN provincias p ON m.provincia_id = p.id
WHERE p.codigo = '11'  -- Cádiz
AND e.activo = TRUE;
```

**6. Verificar si una diputación puede actuar como solicitante:**

```sql
SELECT 
    e.nombre_completo,
    CASE 
        WHEN ead.entidad_id IS NOT NULL THEN 'SÍ'
        ELSE 'NO'
    END AS puede_solicitar
FROM entidades e
JOIN entidades_diputaciones ed ON e.id = ed.entidad_id
LEFT JOIN entidades_administrados ead ON e.id = ead.entidad_id
WHERE e.cif_nif = :cif;
```

**7. Diputaciones sin email publicación BOP (usan plataforma electrónica):**

```sql
SELECT 
    e.nombre_completo,
    ed.codigo_dir3,
    ed.observaciones
FROM entidades e
JOIN entidades_diputaciones ed ON e.id = ed.entidad_id
WHERE ed.email_publicacion_bop IS NULL
AND e.activo = TRUE;
```

---
