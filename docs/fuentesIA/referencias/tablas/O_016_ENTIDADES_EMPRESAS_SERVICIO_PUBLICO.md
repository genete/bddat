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
   - Al crear consulta a organismo → Solo aparecen entidades con capacidad de emisión de informes
   - El filtrado es automático según `tipos_entidades.puede_ser_consultado`

#### Ejemplos de Entidades (tipos)

**Sector energético:**
- Operadores de redes eléctricas (distribución, transporte)
- Operadores de redes de gas
- Empresas de servicios energéticos

**Sector agua:**
- Consorcios de Aguas provinciales
- Empresas metropolitanas de abastecimiento

**Sector transporte:**
- Operadores de infraestructuras ferroviarias
- Operadores de transporte por cable

**Sector telecomunicaciones:**
- Operadores de telecomunicaciones
- Operadores de fibra óptica

#### Regla de Negocio: CIF/NIF para Notifica

**Idéntica a `ENTIDADES_ADMINISTRADOS`** (ver O_015):

- Si hay `representante_nif_cif` → usar ese (quien gestiona)
- Si `representante_nif_cif` es NULL → usar `entidades.cif_nif` (empresa titular)

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

**Flujo:**
1. Usuario introduce CIF que ya existe en el sistema
2. Sistema detecta que CIF ya tiene uno o más roles activos
3. Sistema ofrece copiar datos de representación de rol existente
4. Usuario selecciona de qué rol copiar o introduce datos nuevos

**Interfaz (mockup):**
```
┌─────────────────────────────────────────────────┐
│ AÑADIR ROL: Empresa Servicio Público            │
├─────────────────────────────────────────────────┤
│ Entidad: [Nombre detectado del CIF]             │
│ CIF: [CIF introducido]                          │
│                                                 │
│ ⓘ Este CIF ya tiene roles activos:             │
│    • [Lista de roles existentes]               │
│                                                 │
│ [📋 Copiar datos del rol: [Selector] ▼]        │
│                                                 │
├─────────────────────────────────────────────────┤
│ Email notificaciones:                           │
│ [campo autocompletado o vacío]                  │
│                                                 │
│ Representante NIF/CIF:                          │
│ [campo autocompletado o vacío]                  │
│                                                 │
│ Representante nombre:                           │
│ [campo autocompletado o vacío]                  │
│                                                 │
│ ...                                             │
└─────────────────────────────────────────────────┘
```

**Lógica Python:**
```python
def sugerir_copia_datos(cif_nif):
    """
    Al añadir nuevo rol, detecta roles existentes y sugiere copia.
    Retorna lista de roles disponibles para copiar datos.
    """
    entidad = Entidad.query.filter_by(cif_nif=cif_nif).first()
    if not entidad:
        return None  # CIF nuevo, no sugerir nada
    
    roles_existentes = []
    
    # Detectar roles con metadatos de representación
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
    
    # ... otros roles con representación
    
    return roles_existentes
```

#### Validaciones y Reglas de Negocio

**Las validaciones son idénticas a `ENTIDADES_ADMINISTRADOS`** (ver O_015):

1. `EMAIL_NOTIFICACIONES` obligatorio (NOT NULL)
2. Coherencia representante: si hay CIF, debe haber nombre (constraint)
3. Validación algoritmo CIF/NIF (si no es NULL)
4. Par `(CIF_NOTIFICA, EMAIL_NOTIFICACIONES)` debe estar completo

**Consultar O_015_ENTIDADES_ADMINISTRADOS.md** para detalles completos de validaciones Python y consultas SQL.

---
