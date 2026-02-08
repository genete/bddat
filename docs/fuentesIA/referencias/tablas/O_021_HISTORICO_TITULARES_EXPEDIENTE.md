<!--
Tabla: HISTORICO_TITULARES_EXPEDIENTE
Generado manualmente
Fecha de creación: 07/02/2026
Issue: #64
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### HISTORICO_TITULARES_EXPEDIENTE

Tabla de auditoría inmutable que registra todos los cambios de titularidad de expedientes a lo largo del tiempo. Mantiene trazabilidad completa de la cadena de titularidad desde el origen, permitiendo consultar quién fue titular en cualquier momento histórico.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del registro histórico | NO | PK, autoincremental |
| **EXPEDIENTE_ID** | INTEGER | Expediente cuya titularidad cambia | NO | FK → EXPEDIENTES(ID), ondelete=CASCADE. Indexed |
| **TITULAR_ID** | INTEGER | Titular durante este periodo de vigencia | NO | FK → ENTIDADES(ID). Indexed |
| **FECHA_DESDE** | TIMESTAMP | Timestamp inicio vigencia de este titular | NO | UNIQUE(expediente_id, fecha_desde). Indexed |
| **FECHA_HASTA** | TIMESTAMP | Timestamp fin vigencia | SÍ | NULL = titular actual vigente. Indexed |
| **SOLICITUD_CAMBIO_ID** | INTEGER | Solicitud que motivó el cambio de titularidad | SÍ | FK → SOLICITUDES(ID). NULL para registro INICIAL |
| **MOTIVO** | VARCHAR(50) | Motivo del cambio de titularidad | SÍ | Valores: INICIAL, VENTA, HERENCIA, FUSION, ESCISION, CAMBIO_TITULAR, OTRO |
| **OBSERVACIONES** | TEXT | Observaciones adicionales sobre el cambio | SÍ | Campo libre para detalles |
| **CREATED_AT** | TIMESTAMP | Timestamp de creación del registro (auditoría) | NO | Default: NOW() |

#### Claves

- **PK:** `ID`
- **FK:**
  - `EXPEDIENTE_ID` → `EXPEDIENTES(ID)` (CASCADE)
  - `TITULAR_ID` → `ENTIDADES(ID)`
  - `SOLICITUD_CAMBIO_ID` → `SOLICITUDES(ID)`
- **UNIQUE:** `(EXPEDIENTE_ID, FECHA_DESDE)`

#### Índices Recomendados

- `EXPEDIENTE_ID` (consultas por expediente)
- `TITULAR_ID` (consultas por titular)
- `FECHA_HASTA` (filtrar registros vigentes: WHERE fecha_hasta IS NULL)
- `(EXPEDIENTE_ID, FECHA_DESDE)` (UNIQUE constraint, evita duplicados)

#### Constraints

```sql
-- Vigencia: fecha_hasta debe ser posterior a fecha_desde
CONSTRAINT chk_vigencia_titular 
    CHECK (fecha_hasta IS NULL OR fecha_hasta >= fecha_desde)

-- Unicidad: solo un registro por expediente+timestamp
CONSTRAINT uq_expediente_titular_desde 
    UNIQUE (expediente_id, fecha_desde)
```

#### Relaciones

- **expediente**: EXPEDIENTES.id (FK, expediente afectado)
- **titular**: ENTIDADES.id (FK, titular en este periodo)
- **solicitud_cambio**: SOLICITUDES.id (FK, acto administrativo que motivó el cambio)
- **expediente.historico_titulares**: Relación inversa 1:N desde Expediente
- **titular.historico_como_titular**: Relación inversa 1:N desde Entidad

#### Notas de Versión

- **v3.2** (07/02/2026): Creación inicial de la tabla (Issue #64)
- **v3.3** (07/02/2026): Cambio DATE → DateTime para permitir múltiples cambios/día

#### Filosofía

Esta tabla implementa un **histórico inmutable** con las siguientes características:

- **Auditoría completa**: Cada cambio queda registrado permanentemente
- **Solo INSERT**: No se permite UPDATE ni DELETE (integridad histórica)
- **Titular actual**: Solo un registro puede tener `FECHA_HASTA = NULL` por expediente
- **Snapshot en expedientes**: `EXPEDIENTES.TITULAR_ID` almacena snapshot desnormalizado del titular actual (optimización de rendimiento)
- **Fuente de verdad**: Esta tabla es la fuente autoritativa del histórico completo
- **TIMESTAMP**: Permite múltiples cambios el mismo día (corrección de errores, regularizaciones)

#### Relación con EXPEDIENTES.TITULAR_ID

**Desnormalización intencional para rendimiento:**

```
EXPEDIENTES.TITULAR_ID = snapshot del titular actual
↑
MANTENIDO SINCRONIZADO AUTOMÁTICAMENTE
↓
HISTORICO_TITULARES_EXPEDIENTE (WHERE fecha_hasta IS NULL)
```

**¿Por qué duplicar el dato?**

- Evita JOIN en consultas frecuentes (listar expedientes con titular)
- Optimización: 95% de consultas solo necesitan titular actual
- El histórico completo se consulta raramente (auditoría, informes)

**Sincronización automática:**

1. Al crear expediente con titular → signal crea registro histórico INICIAL
2. Al cambiar titular → método `registrar_cambio()` actualiza ambos lugares
3. Garantía: `expedientes.titular_id` siempre apunta al titular vigente en histórico

#### Motivos de Cambio

| Motivo | Descripción | Solicitud Requerida |
|:---|:---|:---|
| **INICIAL** | Primer titular del expediente | NO (automático) |
| **VENTA** | Compraventa de la instalación | SÍ |
| **HERENCIA** | Transmisión mortis causa | SÍ |
| **FUSION** | Absorción o fusión empresarial | SÍ |
| **ESCISION** | División empresarial | SÍ |
| **CAMBIO_TITULAR** | Cambio genérico (especificar en observaciones) | SÍ |
| **OTRO** | Otros motivos (detallar en observaciones) | SÍ |

#### Uso de TIMESTAMP (no DATE)

**Decisión de diseño: TIMESTAMP en lugar de DATE**

**Casos de uso que justifican TIMESTAMP:**

1. **Corrección inmediata de errores**
   ```
   09:00 - Se asigna titular erróneo por error
   09:15 - Se detecta error y se corrige
   → Dos cambios el mismo día, diferente hora
   ```

2. **Procesos de regularización**
   ```
   Expediente con múltiples titulares históricos sin registrar
   Se regularizan todos el mismo día con horas secuenciales
   ```

3. **Auditoría precisa**
   ```
   Saber exactamente cuándo se realizó cada cambio (hora exacta)
   ```

**Con DATE esto fallaría:**
```sql
-- CONSTRAINT UNIQUE(expediente_id, fecha_desde) fallaría si:
INSERT ... fecha_desde='2026-02-07'  -- OK
INSERT ... fecha_desde='2026-02-07'  -- ERROR: duplicate key
```

**Con TIMESTAMP funciona:**
```sql
INSERT ... fecha_desde='2026-02-07 09:00:00'  -- OK
INSERT ... fecha_desde='2026-02-07 09:15:00'  -- OK (diferente timestamp)
```

#### Reglas de Negocio

1. **Inmutabilidad**: Los registros NO se actualizan ni eliminan (solo INSERT)
2. **Registro inicial automático**: Al crear expediente con titular_id, signal crea registro con motivo INICIAL
3. **Un único titular vigente**: Solo un registro puede tener `fecha_hasta = NULL` por expediente
4. **Validación de fechas**: `fecha_hasta` debe ser posterior o igual a `fecha_desde`
5. **Trazabilidad**: Cambios posteriores al inicial deben tener `solicitud_cambio_id` (recomendado)
6. **Sincronización snapshot**: Al cambiar titular, actualizar `expedientes.titular_id` simultáneamente
7. **Cierre de vigencia**: Al crear nuevo titular vigente, cerrar el anterior con `fecha_hasta`

#### Flujo de Creación de Expediente

**Caso 1: Expediente con titular desde el inicio**

```python
expediente = Expediente(
    numero_at=123,
    proyecto_id=45,
    titular_id=10,  # ← Titular asignado
    tipo_expediente_id=1
)
db.session.add(expediente)
db.session.commit()

# → Signal 'after_insert' ejecuta automáticamente:
# INSERT INTO historico_titulares_expediente (
#     expediente_id=123,
#     titular_id=10,
#     fecha_desde=NOW(),
#     fecha_hasta=NULL,
#     motivo='INICIAL'
# )
```

**Caso 2: Expediente sin titular inicial**

```python
expediente = Expediente(
    numero_at=124,
    proyecto_id=46,
    titular_id=None,  # ← Sin titular
    tipo_expediente_id=1
)
db.session.add(expediente)
db.session.commit()

# → Signal no crea registro histórico (titular_id es NULL)
# El titular se asignará posteriormente mediante solicitud
```

#### Flujo de Cambio de Titular

**Cuando se aprueba solicitud de cambio de titularidad:**

```python
from datetime import datetime
from app.models import HistoricoTitularExpediente

# Usuario aprueba solicitud de cambio de titularidad
solicitud = Solicitud.query.get(120)
solicitud.estado = 'RESUELTA'

# Registrar cambio de titular
HistoricoTitularExpediente.registrar_cambio(
    expediente_id=expediente.id,
    nuevo_titular_id=15,  # Nueva entidad
    fecha_cambio=datetime.now(),
    motivo='VENTA',
    solicitud_cambio_id=solicitud.id,
    observaciones='Venta según escritura pública nº 1234'
)

db.session.commit()

# → Método registrar_cambio() ejecuta:
# 1. UPDATE historico_titulares_expediente 
#    SET fecha_hasta=NOW() 
#    WHERE expediente_id=X AND fecha_hasta IS NULL
#
# 2. INSERT INTO historico_titulares_expediente (
#      expediente_id=X,
#      titular_id=15,
#      fecha_desde=NOW(),
#      fecha_hasta=NULL,
#      solicitud_cambio_id=120,
#      motivo='VENTA'
#    )
#
# 3. UPDATE expedientes 
#    SET titular_id=15 
#    WHERE id=X
```

#### Consultas Habituales

**Obtener titular actual de un expediente:**

```python
# Opción 1: Snapshot (rápido, sin JOIN)
expediente = Expediente.query.get(123)
titular_actual = expediente.titular  # Relación eager loaded

# Opción 2: Desde histórico (con metadatos)
registro = HistoricoTitularExpediente.titular_actual(expediente_id=123)
if registro:
    titular = registro.titular
    desde = registro.fecha_desde
    motivo = registro.motivo
```

**Obtener histórico completo de un expediente:**

```python
historico = HistoricoTitularExpediente.query\
    .filter_by(expediente_id=123)\
    .order_by('fecha_desde')\
    .all()

for registro in historico:
    print(f"{registro.titular.nombre_completo}: "
          f"{registro.fecha_desde} - {registro.fecha_hasta or 'ACTUAL'} "
          f"({registro.motivo})")
```

**Consultar quién era titular en una fecha concreta:**

```sql
SELECT e.nombre_completo, h.fecha_desde, h.fecha_hasta
FROM historico_titulares_expediente h
JOIN entidades e ON e.id = h.titular_id
WHERE h.expediente_id = 123
  AND h.fecha_desde <= '2025-06-15 10:30:00'
  AND (h.fecha_hasta IS NULL OR h.fecha_hasta >= '2025-06-15 10:30:00')
```

**Obtener todos los expedientes de un titular (actual):**

```sql
-- Opción 1: Desde snapshot (rápido)
SELECT * FROM expedientes WHERE titular_id = 10;

-- Opción 2: Desde histórico (verifica vigencia)
SELECT e.* 
FROM expedientes e
JOIN historico_titulares_expediente h ON h.expediente_id = e.id
WHERE h.titular_id = 10 AND h.fecha_hasta IS NULL;
```

**Obtener expedientes donde una entidad FUE titular (histórico):**

```sql
SELECT DISTINCT e.numero_at, e.id
FROM expedientes e
JOIN historico_titulares_expediente h ON h.expediente_id = e.id
WHERE h.titular_id = 10
ORDER BY e.numero_at;
```

#### Property vs Método Estático

**Property en Expediente:**

```python
expediente = Expediente.query.get(123)
registro = expediente.titular_actual  # Property
```

**Método estático en HistoricoTitularExpediente:**

```python
registro = HistoricoTitularExpediente.titular_actual(expediente_id=123)
```

Ambos retornan el mismo objeto `HistoricoTitularExpediente` vigente.

#### Métodos del Modelo

**Método estático: titular_actual(expediente_id)**

Obtiene el registro histórico del titular actual vigente.

```python
registro = HistoricoTitularExpediente.titular_actual(expediente_id=42)
if registro:
    print(f"Titular: {registro.titular.nombre_completo}")
    print(f"Desde: {registro.fecha_desde}")
    print(f"Motivo: {registro.motivo}")
```

**Método estático: registrar_cambio(...)**

Registra un cambio de titularidad completo:
1. Cierra registro actual (`fecha_hasta = fecha_cambio`)
2. Crea nuevo registro vigente (`fecha_hasta = NULL`)
3. Actualiza snapshot en `expedientes.titular_id`

```python
nuevo_registro = HistoricoTitularExpediente.registrar_cambio(
    expediente_id=42,
    nuevo_titular_id=15,
    fecha_cambio=datetime.now(),
    motivo='VENTA',
    solicitud_cambio_id=120,
    observaciones='Cambio aprobado por resolución favorable'
)
db.session.commit()
```

**Método estático: crear_inicial(...)**

Crea el registro INICIAL del primer titular (usado por signal).

```python
registro = HistoricoTitularExpediente.crear_inicial(
    expediente_id=42,
    titular_id=10,
    fecha_desde=datetime.now(),
    observaciones='Titular original del expediente'
)
db.session.add(registro)
db.session.commit()
```

#### Signals SQLAlchemy

**Signal: after_insert en Expediente**

Cuando se crea un expediente con `titular_id` asignado, automáticamente se crea el registro histórico inicial.

```python
@event.listens_for(Expediente, 'after_insert')
def crear_registro_historico_inicial(mapper, connection, target):
    if target.titular_id is None:
        return  # Sin titular, no crear histórico
    
    # INSERT en historico_titulares_expediente
    connection.execute(
        insert(historico_table).values(
            expediente_id=target.id,
            titular_id=target.titular_id,
            fecha_desde=datetime.now(),
            fecha_hasta=None,
            motivo='INICIAL',
            observaciones='Titular inicial del expediente'
        )
    )
```

#### Validaciones

**Prevenir múltiples titulares vigentes:**

```python
# Antes de insertar nuevo registro vigente, cerrar el anterior
registro_actual = HistoricoTitularExpediente.titular_actual(expediente_id)
if registro_actual:
    registro_actual.fecha_hasta = datetime.now()
```

**Validar fecha_cambio no anterior a fecha_desde:**

```python
if fecha_cambio < registro_actual.fecha_desde:
    raise ValueError(
        f"Fecha cambio ({fecha_cambio}) anterior a vigencia actual "
        f"({registro_actual.fecha_desde})"
    )
```

#### Integración con Interfaz Web

**Vista de histórico en detalle de expediente:**

```html
<h3>Histórico de Titularidad</h3>
<table>
    <tr>
        <th>Titular</th>
        <th>Desde</th>
        <th>Hasta</th>
        <th>Motivo</th>
        <th>Solicitud</th>
    </tr>
    {% for registro in expediente.historico_titulares|sort(attribute='fecha_desde') %}
    <tr>
        <td>{{ registro.titular.nombre_completo }}</td>
        <td>{{ registro.fecha_desde|datetime }}</td>
        <td>{{ registro.fecha_hasta|datetime if registro.fecha_hasta else 'VIGENTE' }}</td>
        <td>{{ registro.motivo }}</td>
        <td>
            {% if registro.solicitud_cambio %}
                <a href="{{ url_for('solicitudes.detalle', id=registro.solicitud_cambio_id) }}">
                    Solicitud {{ registro.solicitud_cambio_id }}
                </a>
            {% else %}
                -
            {% endif %}
        </td>
    </tr>
    {% endfor %}
</table>
```

**Formulario de cambio de titular:**

```python
@bp.route('/expediente/<int:id>/cambiar-titular', methods=['POST'])
@login_required
def cambiar_titular(id):
    expediente = Expediente.query.get_or_404(id)
    nuevo_titular_id = request.form.get('nuevo_titular_id')
    motivo = request.form.get('motivo')
    observaciones = request.form.get('observaciones')
    
    try:
        HistoricoTitularExpediente.registrar_cambio(
            expediente_id=expediente.id,
            nuevo_titular_id=nuevo_titular_id,
            fecha_cambio=datetime.now(),
            motivo=motivo,
            solicitud_cambio_id=None,  # O ID de solicitud aprobada
            observaciones=observaciones
        )
        db.session.commit()
        flash('Titular actualizado correctamente', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('expedientes.detalle', id=id))
```

#### Migraciones

**Creación inicial:** `bf66f512eaf4_add_historico_titulares_expediente_table.py`

**Cambio DATE → DateTime:** `0d6742443660_cambiar_fecha_desde_y_fecha_hasta_de.py`

---
