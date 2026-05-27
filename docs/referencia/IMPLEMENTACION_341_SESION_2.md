# Plan Sesión 2 — Modelo `CondicionPlazo` y migración

> Issue #341 · Generado 2026-04-29 · Revisar antes de implementar.

---

## Objetivo

Añadir la infraestructura de BD y ORM necesaria para que una entrada de `catalogo_plazos`
pueda tener condiciones de aplicabilidad. Concretamente:

1. Columna `orden` en `catalogo_plazos` — permite priorizar entradas condicionadas sobre
   el fallback general (`orden` bajo → mayor prioridad).
2. Tabla `condiciones_plazo` — análoga a `condiciones_regla`, enlaza `catalogo_plazos` con
   `catalogo_variables` + operador + valor de referencia.
3. Modelo ORM `CondicionPlazo` y actualización de `CatalogoPlazo`.

**Ningún cambio de comportamiento en `plazos.py`** — el evaluador se implementa en la
sesión 4. Esta sesión solo crea el esquema y el ORM.

---

## Ficheros afectados

| Fichero | Acción |
|---------|--------|
| `app/models/condiciones_plazo.py` | **NUEVO** |
| `app/models/catalogo_plazos.py` | Modificar — añadir `orden`, relationship `condiciones` |
| `app/models/__init__.py` | Modificar — registrar import y `__all__` |
| `migrations/versions/<rev>_341_condiciones_plazo.py` | **NUEVO** |
| `tests/test_341_modelo_condicion_plazo.py` | **NUEVO** |

---

## 1. `app/models/condiciones_plazo.py` (NUEVO)

Espejo de `CondicionRegla` (en `app/models/motor_reglas.py`) pero anclado a
`catalogo_plazos` en lugar de `reglas_motor`. Misma lista de operadores; misma
semántica de `valor` (JSON).

```python
"""Modelo CondicionPlazo — condición de aplicabilidad de una entrada del catálogo de plazos.

Referencia: IMPLEMENTACION_341.md decisión B.
"""
from app import db


class CondicionPlazo(db.Model):
    """
    Condición individual que debe cumplirse para que una entrada de CatalogoPlazo
    sea la aplicable en un contexto dado.

    Todas las condiciones de la misma entrada se evalúan con AND implícito.
    Para expresar OR: crear entradas separadas en catalogo_plazos.

    La semántica de operadores y valor es idéntica a CondicionRegla.
    """
    __tablename__ = 'condiciones_plazo'
    __table_args__ = (
        db.CheckConstraint(
            "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL',"
            "'GT','GTE','LT','LTE','BETWEEN','NOT_BETWEEN')",
            name='ck_condiciones_plazo_operador',
        ),
        db.Index('idx_condiciones_plazo_catalogo', 'catalogo_plazo_id'),
        db.Index('idx_condiciones_plazo_variable', 'variable_id'),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    catalogo_plazo_id = db.Column(
        db.Integer,
        db.ForeignKey('public.catalogo_plazos.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a catalogo_plazos — entrada condicionada',
    )
    variable_id = db.Column(
        db.Integer,
        db.ForeignKey('public.catalogo_variables.id'),
        nullable=False,
        comment='FK a catalogo_variables — variable evaluada',
    )
    operador = db.Column(
        db.String(20), nullable=False,
        comment='Operador de comparación (ver catálogo en docstring)',
    )
    valor = db.Column(
        db.JSON, nullable=True,
        comment='Valor de referencia. Lista para IN/BETWEEN, None para IS_NULL/NOT_NULL',
    )
    orden = db.Column(
        db.Integer, nullable=False, default=1,
        comment='Orden de evaluación dentro de la entrada (informativo)',
    )

    variable = db.relationship('CatalogoVariable')

    def __repr__(self):
        nombre = self.variable.nombre if self.variable else f'var_id={self.variable_id}'
        return (
            f'<CondicionPlazo id={self.id} '
            f'plazo={self.catalogo_plazo_id} {nombre} {self.operador} {self.valor!r}>'
        )
```

---

## 2. `app/models/catalogo_plazos.py` (MODIFICAR)

Dos adiciones al modelo `CatalogoPlazo`, sin tocar ningún campo existente.

### 2a. Columna `orden`

Insertar **antes** del campo `efecto_plazo`:

```python
orden = db.Column(
    db.Integer, nullable=False, default=100, server_default='100',
    comment='Prioridad de selección: menor → se evalúa primero. '
            'Fallback sin condiciones: orden alto (100). No unique.',
)
```

### 2b. Índice en `__table_args__`

Añadir al tuple existente (antes del dict `{'schema': 'public'}`):

```python
db.Index('idx_catalogo_plazos_tipo_orden',
         'tipo_elemento', 'tipo_elemento_id', 'orden'),
```

El `__table_args__` resultante:

```python
__table_args__ = (
    db.Index('idx_catalogo_plazos_tipo_elem',  'tipo_elemento', 'tipo_elemento_id'),
    db.Index('idx_catalogo_plazos_tipo_orden', 'tipo_elemento', 'tipo_elemento_id', 'orden'),
    {'schema': 'public'},
)
```

### 2c. Relationship `condiciones`

Añadir **al final del modelo**, tras `efecto_plazo = db.relationship(...)`:

```python
condiciones = db.relationship(
    'CondicionPlazo',
    backref='catalogo_plazo',
    cascade='all, delete-orphan',
    order_by='CondicionPlazo.orden',
)
```

---

## 3. `app/models/__init__.py` (MODIFICAR)

### 3a. Import

Añadir inmediatamente después de la línea de `CatalogoPlazo`:

```python
from app.models.condiciones_plazo import CondicionPlazo  # depende de CatalogoPlazo y CatalogoVariable
```

La sección de plazos queda:

```python
# Plazos — maestros sin dependencias operacionales (efectos_plazo, ambitos ya importados arriba)
from app.models.dias_inhabiles import DiaInhabil        # depende de AmbitoInhabilidad
from app.models.catalogo_plazos import CatalogoPlazo    # depende de EfectoPlazo
from app.models.condiciones_plazo import CondicionPlazo # depende de CatalogoPlazo y CatalogoVariable
```

### 3b. `__all__`

Añadir `'CondicionPlazo'` en el bloque `# Plazos`, después de `'CatalogoPlazo'`:

```python
    # Plazos
    'DiaInhabil',
    'CatalogoPlazo',
    'CondicionPlazo',
```

---

## 4. Migración (NUEVO)

### 4a. Obtener la cabeza actual antes de crear

```bash
cd /d/BDDAT && source venv/Scripts/activate
flask db heads
```

Debe aparecer `c9379e09ae01` como única cabeza. Si hay más de una, resolver antes de continuar.

### 4b. Generar el esqueleto

```bash
flask db revision -m "341_condiciones_plazo"
```

Alembic crea `migrations/versions/<rev>_341_condiciones_plazo.py` con `down_revision = 'c9379e09ae01'`.

### 4c. Contenido del fichero de migración

Sustituir las funciones `upgrade()` y `downgrade()` generadas por:

```python
"""341_condiciones_plazo

Revision ID: <rev>                ← el que generó Alembic
Revises: c9379e09ae01
Create Date: <fecha>

Issue #341 — Condiciones de aplicabilidad en catalogo_plazos:
  - Columna 'orden' en catalogo_plazos (server_default=100; las 7 entradas
    existentes quedan con orden=100, comportando como fallback general).
  - Índice idx_catalogo_plazos_tipo_orden para ordenación por prioridad.
  - Tabla condiciones_plazo: condiciones AND para selección de entrada.
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # 1. Columna orden en catalogo_plazos
    op.add_column(
        'catalogo_plazos',
        sa.Column(
            'orden', sa.Integer, nullable=False,
            server_default='100',
            comment='Prioridad de selección: menor primero. No unique. '
                    'Fallback sin condiciones: 100.',
        ),
        schema='public',
    )

    # 2. Índice compuesto para la consulta de selección (sesión 4)
    op.create_index(
        'idx_catalogo_plazos_tipo_orden',
        'catalogo_plazos',
        ['tipo_elemento', 'tipo_elemento_id', 'orden'],
        schema='public',
    )

    # 3. Tabla condiciones_plazo
    op.create_table(
        'condiciones_plazo',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            'catalogo_plazo_id', sa.Integer, nullable=False,
            comment='FK a catalogo_plazos — entrada condicionada',
        ),
        sa.Column(
            'variable_id', sa.Integer, nullable=False,
            comment='FK a catalogo_variables — variable evaluada',
        ),
        sa.Column(
            'operador', sa.String(20), nullable=False,
            comment='Operador de comparación',
        ),
        sa.Column(
            'valor', sa.JSON, nullable=True,
            comment='Valor de referencia. Lista para IN/BETWEEN, None para IS_NULL/NOT_NULL',
        ),
        sa.Column(
            'orden', sa.Integer, nullable=False,
            server_default='1',
            comment='Orden de evaluación dentro de la entrada',
        ),
        sa.ForeignKeyConstraint(
            ['catalogo_plazo_id'], ['public.catalogo_plazos.id'],
            name='fk_condiciones_plazo_catalogo', ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['variable_id'], ['public.catalogo_variables.id'],
            name='fk_condiciones_plazo_variable', ondelete='RESTRICT',
        ),
        sa.CheckConstraint(
            "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL',"
            "'GT','GTE','LT','LTE','BETWEEN','NOT_BETWEEN')",
            name='ck_condiciones_plazo_operador',
        ),
        sa.Index('idx_condiciones_plazo_catalogo', 'catalogo_plazo_id'),
        sa.Index('idx_condiciones_plazo_variable', 'variable_id'),
        schema='public',
    )


def downgrade():
    op.drop_table('condiciones_plazo', schema='public')
    op.drop_index('idx_catalogo_plazos_tipo_orden',
                  table_name='catalogo_plazos', schema='public')
    op.drop_column('catalogo_plazos', 'orden', schema='public')
```

### 4d. Verificar upgrade y downgrade

```bash
flask db upgrade
flask db downgrade
flask db upgrade
```

Los tres comandos deben terminar sin error. En particular, el `downgrade` verifica que
las 7 entradas existentes de `catalogo_plazos` no causan problemas al eliminar `orden`
(la columna es independiente; `condiciones_plazo` se borra primero).

---

## 5. `tests/test_341_modelo_condicion_plazo.py` (NUEVO)

Dos bloques: sin BD (importación y estructura) y con BD (`app_ctx` fixture).

```python
"""Tests issue #341 sesión 2 — modelo CondicionPlazo y extensiones de CatalogoPlazo."""
import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# A) Sin BD — importación y estructura del modelo
# ---------------------------------------------------------------------------

def test_condicion_plazo_importable():
    from app.models.condiciones_plazo import CondicionPlazo
    assert CondicionPlazo.__tablename__ == 'condiciones_plazo'


def test_condicion_plazo_en_all():
    import app.models as m
    assert 'CondicionPlazo' in m.__all__


def test_catalogo_plazo_tiene_orden():
    from app.models.catalogo_plazos import CatalogoPlazo
    assert hasattr(CatalogoPlazo, 'orden')


def test_catalogo_plazo_tiene_condiciones():
    from app.models.catalogo_plazos import CatalogoPlazo
    assert hasattr(CatalogoPlazo, 'condiciones')


# ---------------------------------------------------------------------------
# B) Con BD — integridad referencial y cascade (requiere app_ctx)
# ---------------------------------------------------------------------------

@pytest.fixture()
def plazo_base(app_ctx):
    """Crea una entrada mínima en catalogo_plazos y la devuelve."""
    from app import db
    from app.models.catalogo_plazos import CatalogoPlazo
    from app.models.efectos_plazo import EfectoPlazo

    efecto = EfectoPlazo.query.filter_by(codigo='NINGUNO').first()
    assert efecto is not None, 'Seed de efectos_plazo no encontrado — ¿migración aplicada?'

    # tipo_elemento_id=9999 no existe en tipos_fases pero la FK es polimórfica (sin constraint)
    plazo = CatalogoPlazo(
        tipo_elemento='FASE',
        tipo_elemento_id=9999,
        plazo_valor=30,
        plazo_unidad='DIAS_NATURALES',
        efecto_vencimiento_id=efecto.id,
        orden=10,
    )
    db.session.add(plazo)
    db.session.flush()
    return plazo


def test_condicion_plazo_creacion(app_ctx, plazo_base):
    """Crea CondicionPlazo vinculada a CatalogoPlazo y verifica atributos."""
    from app import db
    from app.models.condiciones_plazo import CondicionPlazo
    from app.models.motor_reglas import CatalogoVariable

    var = CatalogoVariable.query.filter_by(nombre='estado_plazo').first()
    assert var is not None, 'Variable estado_plazo no encontrada — ¿migración bc4a9f1d8e02 aplicada?'

    cond = CondicionPlazo(
        catalogo_plazo_id=plazo_base.id,
        variable_id=var.id,
        operador='EQ',
        valor='EN_PLAZO',
        orden=1,
    )
    db.session.add(cond)
    db.session.flush()

    assert cond.id is not None
    assert cond.variable.nombre == 'estado_plazo'
    assert cond.catalogo_plazo.id == plazo_base.id


def test_condicion_plazo_cascade_delete(app_ctx, plazo_base):
    """Al borrar CatalogoPlazo, sus CondicionPlazo se eliminan en cascada."""
    from app import db
    from app.models.condiciones_plazo import CondicionPlazo
    from app.models.motor_reglas import CatalogoVariable

    var = CatalogoVariable.query.filter_by(nombre='estado_plazo').first()
    cond = CondicionPlazo(
        catalogo_plazo_id=plazo_base.id,
        variable_id=var.id,
        operador='EQ',
        valor='VENCIDO',
        orden=1,
    )
    db.session.add(cond)
    db.session.flush()
    cond_id = cond.id

    db.session.delete(plazo_base)
    db.session.flush()

    assert CondicionPlazo.query.get(cond_id) is None


def test_condicion_plazo_check_operador_invalido(app_ctx, plazo_base):
    """CheckConstraint rechaza operadores no reconocidos."""
    import sqlalchemy.exc
    from app import db
    from app.models.condiciones_plazo import CondicionPlazo
    from app.models.motor_reglas import CatalogoVariable

    var = CatalogoVariable.query.filter_by(nombre='estado_plazo').first()
    cond = CondicionPlazo(
        catalogo_plazo_id=plazo_base.id,
        variable_id=var.id,
        operador='LIKE',   # inválido — no está en el CheckConstraint
        valor='algo',
        orden=1,
    )
    db.session.add(cond)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.session.flush()


def test_catalogo_plazo_orden_default(app_ctx):
    """Entradas existentes tienen orden=100 tras la migración."""
    from app.models.catalogo_plazos import CatalogoPlazo
    plazos = CatalogoPlazo.query.all()
    assert plazos, 'No hay entradas en catalogo_plazos — ¿migración c9379e09ae01 aplicada?'
    assert all(p.orden == 100 for p in plazos), (
        'Alguna entrada existente tiene orden != 100; el server_default no se aplicó'
    )


def test_catalogo_plazo_relationship_condiciones_vacia(app_ctx, plazo_base):
    """Una entrada nueva sin condiciones tiene lista vacía (no None)."""
    assert plazo_base.condiciones == []
```

---

## Secuencia de implementación

1. Crear `app/models/condiciones_plazo.py` (§1).
2. Editar `app/models/catalogo_plazos.py` (§2a columna, §2b índice, §2c relationship).
3. Editar `app/models/__init__.py` (§3a import, §3b `__all__`).
4. Verificar que `flask shell` importa correctamente sin errores:
   ```python
   from app.models import CondicionPlazo, CatalogoPlazo
   CatalogoPlazo.__table__.columns.keys()   # debe incluir 'orden'
   ```
5. Generar el esqueleto de migración (`flask db revision -m "341_condiciones_plazo"`).
6. Rellenar la migración con el contenido de §4c.
7. Ejecutar upgrade + downgrade + upgrade (§4d).
8. Crear `tests/test_341_modelo_condicion_plazo.py` (§5).
9. Ejecutar el criterio de aceptación.

---

## Criterio de aceptación

```bash
# 1. Migración limpia (manual)
flask db upgrade    # verde
flask db downgrade  # verde
flask db upgrade    # verde

# 2. Tests automáticos
pytest tests/test_341_modelo_condicion_plazo.py -v
pytest tests/test_172_plazos_computo.py tests/test_190_plazos_contrato.py -v
```

- Todos los tests de `test_341_modelo_condicion_plazo.py` verdes (con BD real).
- Tests de #172 y #190 verdes sin modificarlos.

---

## Riesgos y notas

- **`tipo_elemento_id=9999` en el fixture de test:** la FK es polimórfica sin constraint BD
  (igual que en `ReglaMotor`). El valor 9999 es seguro para tests — no existe en
  `tipos_fases` pero la BD no lo valida.
- **`ck_condiciones_plazo_operador`:** el CheckConstraint se verifica al hacer `flush()`
  en PostgreSQL. El test `test_condicion_plazo_check_operador_invalido` depende de que la
  migración esté aplicada (el constraint vive en BD, no en el ORM Python).
- **`app_ctx` y transacción:** el fixture de `conftest.py` usa savepoint + rollback.
  Todos los cambios de los tests con BD se deshacen automáticamente. No hay riesgo de
  contaminación entre tests.
- **Orden de `downgrade`:** `condiciones_plazo` debe borrarse antes que la columna
  `orden` de `catalogo_plazos`. El `drop_table` ya lo garantiza implícitamente (la FK
  CASCADE es de `condiciones_plazo → catalogo_plazos`, no al revés). Aun así, el orden
  explícito en `downgrade()` (tabla primero, columna después) lo hace inequívoco.
- **`ExcepcionMotor` y `CondicionExcepcion`** en `motor_reglas.py` se importan en
  `motor_reglas.py` pero **no** se registran en `app/models/__init__.py`. No cambiar ese
  patrón — `CondicionPlazo` sí se registra porque `plazos.py` la necesitará con
  `joinedload` en sesión 4.
