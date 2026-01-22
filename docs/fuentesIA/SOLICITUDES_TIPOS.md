### SOLICITUDES_TIPOS

Tabla puente que gestiona relaciones muchos a muchos entre solicitudes y tipos de solicitudes individuales.

#### Modelo SQLAlchemy

```python
# app/models/solicitud_tipo.py
from app import db

class SolicitudTipo(db.Model):
    __tablename__ = 'solicitudes_tipos'
    
    id = db.Column(db.Integer, primary_key=True)
    solicitud_id = db.Column(db.Integer, db.ForeignKey('solicitudes.id', ondelete='CASCADE'), nullable=False)
    tipo_solicitud_id = db.Column(db.Integer, db.ForeignKey('tipos_solicitudes.id'), nullable=False)
    
    # Relaciones
    solicitud = db.relationship('Solicitud', back_populates='solicitudes_tipos')
    tipo = db.relationship('TipoSolicitud')
    
    # Constraint UNIQUE
    __table_args__ = (
        db.UniqueConstraint('solicitud_id', 'tipo_solicitud_id', name='uq_solicitud_tipo'),
        db.Index('idx_solicitudes_tipos_solicitud', 'solicitud_id'),
        db.Index('idx_solicitudes_tipos_tipo', 'tipo_solicitud_id'),
    )
    
    def __repr__(self):
        return f'<SolicitudTipo solicitud={self.solicitud_id} tipo={self.tipo_solicitud_id}>'
```

**Actualización modelo Solicitud:**
```python
# app/models/solicitud.py (añadir relación)
class Solicitud(db.Model):
    # ... campos existentes ...
    
    # Relación many-to-many con tipos
    solicitudes_tipos = db.relationship('SolicitudTipo', back_populates='solicitud', cascade='all, delete-orphan')
```

**Migración Alembic:**
```bash
flask db migrate -m "Añadir tabla solicitudes_tipos para tipos individuales"
flask db upgrade
```

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del registro | NO | PK, autoincremental |
| **SOLICITUD_ID** | INTEGER | Solicitud a la que se aplica el tipo | NO | FK → SOLICITUDES(ID). Una solicitud puede contener múltiples tipos |
| **TIPO_SOLICITUD_ID** | INTEGER | Tipo individual de solicitud aplicado | NO | FK → TIPOS_SOLICITUDES(ID). Los tipos individuales se definen en TIPOS_SOLICITUDES |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `(SOLICITUD_ID, TIPO_SOLICITUD_ID)` - Una solicitud no puede tener el mismo tipo duplicado
- **FK:**
  - `SOLICITUD_ID` → `SOLICITUDES(ID)` ON DELETE CASCADE
  - `TIPO_SOLICITUD_ID` → `TIPOS_SOLICITUDES(ID)`

#### Índices

- `idx_solicitudes_tipos_solicitud` en `SOLICITUD_ID`
- `idx_solicitudes_tipos_tipo` en `TIPO_SOLICITUD_ID`

#### Notas de Versión
- **v3.0:** **NUEVA TABLA**. Implementa arquitectura de tipos individuales con combinaciones flexibles mediante tabla puente N:M.

#### Filosofía

Arquitectura v3.0: **17 tipos individuales** + combinaciones flexibles.

**v2.0:** AAP+AAC, AAP+DUP (20+ combinados hardcodeados)  
**v3.0:** AAP, AAC, DUP (tabla puente para combinar)

#### Uso en Python

**Añadir tipos a solicitud:**
```python
solicitud = Solicitud(expediente_id=1, fecha=date.today())

# Añadir AAP
tipo_aap = TipoSolicitud.query.filter_by(siglas='AAP').first()
solicitud.solicitudes_tipos.append(SolicitudTipo(tipo=tipo_aap))

# Añadir AAC
tipo_aac = TipoSolicitud.query.filter_by(siglas='AAC').first()
solicitud.solicitudes_tipos.append(SolicitudTipo(tipo=tipo_aac))

db.session.add(solicitud)
db.session.commit()
```

**Consultar tipos de solicitud:**
```python
solicitud = Solicitud.query.get(1)
tipos = [st.tipo.siglas for st in solicitud.solicitudes_tipos]
print(tipos)  # ['AAP', 'AAC']
```

**Verificar si tiene tipo:**
```python
tiene_aap = any(st.tipo.siglas == 'AAP' for st in solicitud.solicitudes_tipos)
```

#### Consultas SQL (cuando sea necesario)

**Obtener tipos de solicitud:**
```sql
SELECT ts.siglas, ts.descripcion
FROM solicitudes_tipos st
JOIN tipos_solicitudes ts ON st.tipo_solicitud_id = ts.id
WHERE st.solicitud_id = ?
ORDER BY ts.siglas;
```

**Contar por tipo:**
```sql
SELECT ts.siglas, COUNT(st.solicitud_id) AS total
FROM tipos_solicitudes ts
LEFT JOIN solicitudes_tipos st ON ts.id = st.tipo_solicitud_id
GROUP BY ts.id, ts.siglas
ORDER BY total DESC;
```

#### Reglas de Negocio

1. **Tipos incompatibles:** AAE_PROVISIONAL y AAE_DEFINITIVA mutuamente excluyentes
2. **Secuencias:** RAIPEE_DEFINITIVA requiere PREVIA anterior, AAE_DEFINITIVA requiere PROVISIONAL
3. **Coherencia:** RAIPEE solo para renovables, RADNE solo para autoconsumo

#### Ventajas v3.0

1. Flexibilidad total (cualquier combinación)
2. 17 tipos vs 20+ combinaciones
3. Escalable (nuevos tipos una vez)
4. Estadísticas precisas por tipo

---

**Versión:** 3.0  
**Fecha:** 22 de enero de 2026  
**Proyecto:** BDDAT
