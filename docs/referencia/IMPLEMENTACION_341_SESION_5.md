# Plan Sesión 5 — Seed art. 131.1 párr. 2 y tests E2E

> Issue #341 · Generado 2026-04-29 · Revisar antes de implementar.

---

## Objetivo

Materializar en BD el caso canónico del art. 131.1 párr. 2 RD 1955/2000 e integrarlo
con el evaluador de la sesión 4:

1. **Crear `tipo_fase` `INFORME_AAPP`** — tipo de fase que aún no existe en catálogo
   (cabo suelto nº 1 de IMPLEMENTACION_341.md).
2. **Seed de `catalogo_plazos`** — dos entradas para `INFORME_AAPP`:
   - orden=10, 15 días naturales (condicionada: AAP previa favorable + AAC pura)
   - orden=100, 30 días naturales (fallback sin condiciones)
3. **Seed de `condiciones_plazo`** — dos condiciones vinculadas a la entrada de 15 días.
4. **Tests E2E** con BD real (`app_ctx`) que validan los tres escenarios del caso canónico.

**Dependencias:** sesiones 1 (operadores), 2 (modelo+tablas), 3 (variables), 4 (evaluador).

---

## Cabo suelto nº 1 — código `tipo_fase` para INFORME_AAPP

El código exacto no existe aún en `tipos_fases`. Los códigos actuales siguen el patrón:
- Fases genéricas: `CONSULTAS`, `INFORMACION_PUBLICA`, `ANALISIS_TECNICO`
- Fases propias de un procedimiento: `RESOLUCION_AAP`, `RESOLUCION_AAC`

**Propuesta:** código `INFORME_AAPP`, nombre "Solicitud de informes a administraciones
públicas". La diferencia de plazo (15 vs. 30 días) la gestiona el evaluador de condiciones,
no el código de la fase.

**Confirmar con el usuario antes de aplicar la migración** si el código encaja con el
modelo de procedimiento. Si ya existe una fase con otro nombre, sustituir en la migración.

---

## Ficheros afectados

| Fichero | Acción |
|---------|--------|
| `migrations/versions/<rev>_341_seed_art131_informe_aapp.py` | **NUEVO** |
| `tests/test_341_e2e_art131.py` | **NUEVO** |

---

## 1. Migración (NUEVO)

### 1a. Cabeza antes de crear

```bash
flask db heads
```

Debe apuntar a la cabeza de S3 (variables_art131). Si hay dos cabezas, resolver con
`flask db merge heads` antes de continuar.

### 1b. Generar el esqueleto

```bash
flask db revision -m "341_seed_art131_informe_aapp"
```

### 1c. Contenido de la migración

```python
"""341_seed_art131_informe_aapp

Revision ID: <rev>
Revises: <rev_s3_variables_art131>
Create Date: <fecha>

Issue #341 sesión 5 — Seed del caso canónico art. 131.1 párr. 2 RD 1955/2000:
  - Nuevo tipo_fase INFORME_AAPP (solicitud de informes a AAPP en AAC).
  - Dos entradas en catalogo_plazos: 15 días (condicionada) y 30 días (fallback).
  - Dos condiciones en condiciones_plazo para la entrada de 15 días.
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # A. Tipo de fase INFORME_AAPP (si no existe)
    # ------------------------------------------------------------------
    # Verificar primero que no existe ya con otro nombre/código.
    # Ajustar 'INFORME_AAPP' y el nombre si el usuario lo confirma con
    # otro valor en el diseño de procedimiento.
    conn.execute(sa.text("""
        INSERT INTO public.tipos_fases (codigo, nombre, abrev, es_finalizadora)
        VALUES (
            'INFORME_AAPP',
            'Solicitud de informes a administraciones públicas',
            'INF.AAPP',
            FALSE
        )
        ON CONFLICT DO NOTHING
    """))

    # Asociar INFORME_AAPP a los tipos de solicitud AAC.
    # tipo_solicitud con siglas 'AAC' puede tener más de una fila si existen
    # variantes; el JOIN lo resuelve automáticamente.
    conn.execute(sa.text("""
        INSERT INTO public.solicitudes_fases (tipo_solicitud_id, tipo_fase_id)
        SELECT ts.id, tf.id
        FROM   public.tipos_solicitudes ts
        CROSS JOIN public.tipos_fases tf
        WHERE  ts.siglas = 'AAC'
          AND  tf.codigo = 'INFORME_AAPP'
        ON CONFLICT DO NOTHING
    """))

    # ------------------------------------------------------------------
    # B. Dos entradas en catalogo_plazos para INFORME_AAPP
    # ------------------------------------------------------------------
    # B.1 Entrada condicionada — 15 días naturales (orden=10)
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_plazos
            (tipo_elemento, tipo_elemento_id, campo_fecha,
             plazo_valor, plazo_unidad,
             efecto_vencimiento_id, norma_origen, orden, activo)
        SELECT
            'FASE',
            tf.id,
            '{"fk": "documento_solicitud_id"}'::jsonb,
            15,
            'DIAS_NATURALES',
            ep.id,
            'Art. 131.1 párr. 2 RD 1955/2000 — plazo reducido con AAP previa favorable',
            10,
            TRUE
        FROM public.tipos_fases tf
        CROSS JOIN public.efectos_plazo ep
        WHERE tf.codigo = 'INFORME_AAPP'
          AND ep.codigo = 'CONFORMIDAD_PRESUNTA'
    """))

    # B.2 Entrada fallback — 30 días naturales (orden=100)
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_plazos
            (tipo_elemento, tipo_elemento_id, campo_fecha,
             plazo_valor, plazo_unidad,
             efecto_vencimiento_id, norma_origen, orden, activo)
        SELECT
            'FASE',
            tf.id,
            '{"fk": "documento_solicitud_id"}'::jsonb,
            30,
            'DIAS_NATURALES',
            ep.id,
            'Art. 131.1 párr. 1 RD 1955/2000 — plazo general de consultas en AAC',
            100,
            TRUE
        FROM public.tipos_fases tf
        CROSS JOIN public.efectos_plazo ep
        WHERE tf.codigo = 'INFORME_AAPP'
          AND ep.codigo = 'CONFORMIDAD_PRESUNTA'
    """))

    # ------------------------------------------------------------------
    # C. Condiciones para la entrada de 15 días
    # ------------------------------------------------------------------
    # Obtener el id de la entrada de 15 días recién insertada.
    # El identificador único es (tipo_elemento_id, orden=10) para INFORME_AAPP.
    conn.execute(sa.text("""
        INSERT INTO public.condiciones_plazo
            (catalogo_plazo_id, variable_id, operador, valor, orden)
        SELECT
            cp.id,
            cv.id,
            'EQ',
            'true'::jsonb,
            cond.orden
        FROM public.catalogo_plazos cp
        JOIN public.tipos_fases tf ON tf.id = cp.tipo_elemento_id
        CROSS JOIN (
            VALUES
                ('tiene_solicitud_aap_favorable', 1),
                ('es_solicitud_aac_pura',          2)
        ) AS cond(nombre_var, orden)
        JOIN public.catalogo_variables cv ON cv.nombre = cond.nombre_var
        WHERE tf.codigo = 'INFORME_AAPP'
          AND cp.orden = 10
          AND cp.tipo_elemento = 'FASE'
    """))


def downgrade():
    conn = op.get_bind()

    # Eliminar condiciones
    conn.execute(sa.text("""
        DELETE FROM public.condiciones_plazo
        WHERE catalogo_plazo_id IN (
            SELECT cp.id FROM public.catalogo_plazos cp
            JOIN public.tipos_fases tf ON tf.id = cp.tipo_elemento_id
            WHERE tf.codigo = 'INFORME_AAPP'
        )
    """))

    # Eliminar entradas de catálogo
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_plazos
        WHERE tipo_elemento_id = (
            SELECT id FROM public.tipos_fases WHERE codigo = 'INFORME_AAPP'
        )
    """))

    # Eliminar asociación solicitud-fase
    conn.execute(sa.text("""
        DELETE FROM public.solicitudes_fases
        WHERE tipo_fase_id = (
            SELECT id FROM public.tipos_fases WHERE codigo = 'INFORME_AAPP'
        )
    """))

    # Eliminar tipo_fase
    conn.execute(sa.text("""
        DELETE FROM public.tipos_fases WHERE codigo = 'INFORME_AAPP'
    """))
```

**Nota sobre `CONFORMIDAD_PRESUNTA`:** el efecto del vencimiento del plazo de consultas a AAPP
en AAC es la conformidad presunta del organismo (art. 131.1 párr. 3 RD 1955/2000).
Si el usuario prefiere `NINGUNO` mientras no se automatiza el efecto, cambiar en ambos INSERT.

**Nota sobre el valor de `condiciones_plazo.valor`:** el JSON `'true'::jsonb` es el valor
que SQLAlchemy deserializa como `True` en Python. El operador `EQ` lo compara con el resultado
booleano de `tiene_solicitud_aap_favorable` y `es_solicitud_aac_pura`.

### 1d. Verificar

```bash
flask db upgrade
flask db downgrade
flask db upgrade
```

Verificar manualmente tras el upgrade final:

```bash
# En flask shell:
from app.models import CatalogoPlazo, CondicionPlazo, TipoFase
tf = TipoFase.query.filter_by(codigo='INFORME_AAPP').first()
print(tf)                                          # debe existir
plazos = CatalogoPlazo.query.filter_by(tipo_elemento_id=tf.id).all()
print([(p.orden, p.plazo_valor, len(p.condiciones)) for p in plazos])
# → [(10, 15, 2), (100, 30, 0)]
```

---

## 2. `tests/test_341_e2e_art131.py` (NUEVO)

Tests E2E con BD real (`app_ctx`). Crean el grafo mínimo de objetos ORM y llaman
a `obtener_estado_plazo` a través de `ExpedienteContext`, verificando que la selección
de catálogo responde a las variables de contexto.

```python
"""Tests E2E issue #341 sesión 5 — art. 131.1 párr. 2 RD 1955/2000.

Requieren:
  - BD con migraciones S1-S5 aplicadas.
  - Fixture app_ctx (rollback automático por test).

Escenarios:
  A) AAC con AAP previa favorable → 15 días naturales
  B) AAC sin AAP previa → 30 días naturales
  C) AAC con DUP (no es_solicitud_aac_pura) → 30 días naturales
"""
import pytest
from datetime import date
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers de construcción del grafo ORM
# ---------------------------------------------------------------------------

def _get_tipo(model_class, **filtros):
    """Obtiene un tipo por filtro o falla con mensaje claro."""
    obj = model_class.query.filter_by(**filtros).first()
    assert obj is not None, (
        f'{model_class.__name__} con {filtros} no encontrado — '
        f'¿migración S5 aplicada?'
    )
    return obj


def _crear_solicitud(db, expediente, tipo_solicitud, solicitudes_list=None):
    """Crea una Solicitud mínima y la añade al expediente."""
    from app.models import Solicitud
    sol = Solicitud(
        expediente=expediente,
        tipo_solicitud=tipo_solicitud,
    )
    db.session.add(sol)
    db.session.flush()
    return sol


def _crear_fase_finalizadora_favorable(db, solicitud, tipo_fase_resolucion, resultado_favorable):
    """
    Crea una Fase finalizadora con resultado FAVORABLE para la solicitud dada.
    Simula la resolución AAP aprobada.
    """
    from app.models import Fase, Documento
    doc = Documento(fecha_administrativa=date(2025, 1, 15))
    db.session.add(doc)
    db.session.flush()

    fase = Fase(
        solicitud=solicitud,
        tipo_fase=tipo_fase_resolucion,
        resultado_fase=resultado_favorable,
        documento_resultado=doc,
    )
    db.session.add(fase)
    db.session.flush()
    return fase


def _crear_fase_informe_aapp(db, solicitud, tipo_fase_informe, fecha_admin):
    """
    Crea la fase INFORME_AAPP con su documento_solicitud.
    campo_fecha apunta a {'fk': 'documento_solicitud_id'} vía solicitud.
    """
    from app.models import Fase, Documento
    doc_sol = Documento(fecha_administrativa=fecha_admin)
    db.session.add(doc_sol)
    db.session.flush()

    # La fase pertenece a la solicitud; el campo_fecha navega
    # fase → fase.solicitud → solicitud.documento_solicitud
    solicitud.documento_solicitud = doc_sol
    db.session.flush()

    fase = Fase(
        solicitud=solicitud,
        tipo_fase=tipo_fase_informe,
    )
    db.session.add(fase)
    db.session.flush()
    return fase


# ---------------------------------------------------------------------------
# Fixture compartida — tipos maestros
# ---------------------------------------------------------------------------

@pytest.fixture()
def tipos(app_ctx):
    """Devuelve los tipos maestros necesarios para los tests E2E."""
    from app import db
    from app.models import TipoFase, TipoSolicitud, ResultadoFase, TipoExpediente

    return {
        'tf_resolucion_aap': _get_tipo(TipoFase, codigo='RESOLUCION_AAP'),
        'tf_informe_aapp':   _get_tipo(TipoFase, codigo='INFORME_AAPP'),
        'ts_aap':            _get_tipo(TipoSolicitud, siglas='AAP'),
        'ts_aac':            _get_tipo(TipoSolicitud, siglas='AAC'),
        'ts_dup':            _get_tipo(TipoSolicitud, siglas='DUP'),
        'resultado_fav':     _get_tipo(ResultadoFase, codigo='FAVORABLE'),
        'tipo_exp':          TipoExpediente.query.first(),
    }


@pytest.fixture()
def expediente_base(app_ctx, tipos):
    """Expediente mínimo reutilizable."""
    from app import db
    from app.models import Expediente
    exp = Expediente(tipo_expediente=tipos['tipo_exp'])
    db.session.add(exp)
    db.session.flush()
    return exp


# ---------------------------------------------------------------------------
# A) AAC con AAP previa favorable → 15 días
# ---------------------------------------------------------------------------

def test_e2e_aac_con_aap_previa_usa_plazo_15_dias(app_ctx, tipos, expediente_base):
    """
    Expediente con S1 AAP resuelta favorablemente + S2 AAC pura.
    INFORME_AAPP de S2 → selecciona entrada orden=10 → 15 días naturales.
    """
    from app import db
    from app.services.assembler import ExpedienteContext
    from app.services.plazos import obtener_estado_plazo

    exp = expediente_base

    # S1: AAP con resolución favorable
    sol_aap = _crear_solicitud(db, exp, tipos['ts_aap'])
    _crear_fase_finalizadora_favorable(
        db, sol_aap, tipos['tf_resolucion_aap'], tipos['resultado_fav']
    )

    # S2: AAC pura (sin AAP ni DUP en la misma solicitud)
    sol_aac = _crear_solicitud(db, exp, tipos['ts_aac'])
    fecha_admin = date(2025, 5, 5)   # lunes
    fase_informe = _crear_fase_informe_aapp(
        db, sol_aac, tipos['tf_informe_aapp'], fecha_admin
    )

    ctx = ExpedienteContext(expediente=exp, objeto=fase_informe)

    with patch('app.services.plazos._hoy', return_value=date(2025, 5, 6)), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        estado = obtener_estado_plazo(fase_informe, 'FASE', ctx=ctx)

    # fecha_admin=5 may + 15 días naturales = 20 may (martes, hábil → sin prórroga)
    assert estado.fecha_limite == date(2025, 5, 20), (
        f'Se esperaba fecha_limite=2025-05-20 (15 días); '
        f'obtenido {estado.fecha_limite} — ¿evaluador seleccionó entrada correcta?'
    )
    assert estado.estado != 'SIN_PLAZO'


# ---------------------------------------------------------------------------
# B) AAC sin AAP previa → 30 días
# ---------------------------------------------------------------------------

def test_e2e_aac_sin_aap_previa_usa_plazo_30_dias(app_ctx, tipos, expediente_base):
    """
    Expediente solo con S2 AAC (sin ninguna AAP previa).
    INFORME_AAPP de S2 → condición falla → selecciona fallback orden=100 → 30 días.
    """
    from app import db
    from app.services.assembler import ExpedienteContext
    from app.services.plazos import obtener_estado_plazo

    exp = expediente_base

    sol_aac = _crear_solicitud(db, exp, tipos['ts_aac'])
    fecha_admin = date(2025, 5, 5)
    fase_informe = _crear_fase_informe_aapp(
        db, sol_aac, tipos['tf_informe_aapp'], fecha_admin
    )

    ctx = ExpedienteContext(expediente=exp, objeto=fase_informe)

    with patch('app.services.plazos._hoy', return_value=date(2025, 5, 6)), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        estado = obtener_estado_plazo(fase_informe, 'FASE', ctx=ctx)

    # fecha_admin=5 may + 30 días naturales = 4 jun (miércoles, hábil)
    assert estado.fecha_limite == date(2025, 6, 4), (
        f'Se esperaba fecha_limite=2025-06-04 (30 días); '
        f'obtenido {estado.fecha_limite} — ¿fallback aplicado correctamente?'
    )
    assert estado.estado != 'SIN_PLAZO'


# ---------------------------------------------------------------------------
# C) AAC con DUP en la misma solicitud → no es_solicitud_aac_pura → 30 días
# ---------------------------------------------------------------------------

def test_e2e_aac_con_dup_no_es_pura_usa_plazo_30_dias(app_ctx, tipos, expediente_base):
    """
    S2 = solicitud AAC+DUP combinada.
    es_solicitud_aac_pura → False (contiene DUP).
    Aunque haya AAP previa favorable, la condición AND no se cumple → 30 días.

    Nota: TipoSolicitud 'AAC+DUP' puede no existir como fila única.
    Si el modelo usa tipos simples relacionados, ajustar la creación del stub.
    """
    from app import db
    from app.services.assembler import ExpedienteContext
    from app.services.plazos import obtener_estado_plazo

    exp = expediente_base

    # S1: AAP favorable (la condición tiene_solicitud_aap_favorable=True se cumplirá)
    sol_aap = _crear_solicitud(db, exp, tipos['ts_aap'])
    _crear_fase_finalizadora_favorable(
        db, sol_aap, tipos['tf_resolucion_aap'], tipos['resultado_fav']
    )

    # S2: solicitud que contiene AAC+DUP → es_solicitud_aac_pura = False
    # Si el sistema usa tipos combinados como una sola fila en tipos_solicitudes,
    # usar _get_tipo(TipoSolicitud, siglas='AAC+DUP').
    # Si no existe, el test verifica el comportamiento vía la variable directamente.
    # Ver nota al final del fichero.
    ts_aac_dup = TipoSolicitud.query.filter(
        TipoSolicitud.siglas.in_(['AAC+DUP', 'AAC-DUP'])
    ).first()
    if ts_aac_dup is None:
        pytest.skip(
            'No existe tipo_solicitud AAC+DUP en BD — '
            'ajustar cuando se modele la solicitud combinada'
        )

    sol_aac_dup = _crear_solicitud(db, exp, ts_aac_dup)
    fecha_admin = date(2025, 5, 5)
    fase_informe = _crear_fase_informe_aapp(
        db, sol_aac_dup, tipos['tf_informe_aapp'], fecha_admin
    )

    ctx = ExpedienteContext(expediente=exp, objeto=fase_informe)

    with patch('app.services.plazos._hoy', return_value=date(2025, 5, 6)), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        estado = obtener_estado_plazo(fase_informe, 'FASE', ctx=ctx)

    assert estado.fecha_limite == date(2025, 6, 4)   # 30 días
```

**Nota sobre el escenario C:** si el sistema no modela solicitudes combinadas como una sola
fila en `tipos_solicitudes`, el test puede saltearse (`pytest.skip`) sin que ello invalide
el criterio de aceptación. La variable `es_solicitud_aac_pura` ya se prueba en test_341_variables_art131.py.
El escenario C es una garantía de integración, no el único test del comportamiento.

---

## Secuencia de implementación

1. **Confirmar código `tipo_fase`** con el usuario (§ Cabo suelto nº 1).
   Si el código es distinto de `INFORME_AAPP`, actualizar el `campo_fecha` y la
   asociación en `solicitudes_fases` de la migración.

2. Generar el esqueleto de migración y rellenar con el contenido de §1c.

3. Ejecutar `flask db upgrade`. Verificar con el shell (§1d).

4. Ejecutar `flask db downgrade` y `flask db upgrade` de nuevo para validar idempotencia.

5. Crear `tests/test_341_e2e_art131.py`.

6. Ejecutar el criterio de aceptación.

---

## Criterio de aceptación

```bash
# E2E (con BD real — requiere migraciones S1-S5 aplicadas)
pytest tests/test_341_e2e_art131.py -v

# Regresión completa de #341 (sin BD para S1-S4, con BD para S2 y S5)
pytest tests/test_172_plazos_computo.py \
       tests/test_190_plazos_contrato.py \
       tests/test_341_operadores.py \
       tests/test_341_variables_art131.py \
       tests/test_341_evaluador_plazo.py \
       tests/test_341_e2e_art131.py -v
```

Los tres tests E2E de `test_341_e2e_art131.py` deben ser verdes (el C puede ser
`skip` si no existe el tipo AAC+DUP en BD).

---

## Riesgos y notas

### `campo_fecha` de la fase INFORME_AAPP

El seed usa `{"fk": "documento_solicitud_id"}` navegando `fase → solicitud → documento_solicitud`.
La función `_resolver_campo_fecha` en `plazos.py` ya soporta este camino (rama FASE sin
`via_tarea_tipo`). Si el campo_fecha real de la fase es otro documento (ej. el oficio de
solicitud de informe), actualizar el seed y los helpers de los tests.

### `ON CONFLICT DO NOTHING` en `tipos_fases`

Permite ejecutar `upgrade` más de una vez sin error. El riesgo es silenciar conflictos por
tipos con el mismo nombre pero código distinto. Verificar con el shell tras el upgrade.

### Fixture `expediente_base` y falta de `numero_expediente`

Si `Expediente` tiene campos obligatorios adicionales (ej. `numero_expediente`, `fecha_inicio`),
el `flush()` fallará con `IntegrityError`. Añadir los campos mínimos requeridos en el
helper `expediente_base`. Inspeccionar la migración de creación de `expedientes` o el modelo
ORM antes de implementar.

### Relación `Solicitud.documento_solicitud`

El helper `_crear_fase_informe_aapp` asigna `solicitud.documento_solicitud = doc_sol`.
Si el modelo usa un FK distinto para el documento de la solicitud (ej. `doc_solicitud` o
`documento_id`), ajustar el helper. Verificar en `app/models/solicitudes.py` antes de
implementar.

### Relación `Fase.resultado_fase` y `Fase.finalizada`

La variable `tiene_solicitud_aap_favorable` comprueba `fase.finalizada and fase.resultado_fase`.
Si `finalizada` es una property derivada de un campo de BD (ej. `fecha_fin is not None`),
asegurarse de que el helper `_crear_fase_finalizadora_favorable` lo rellena correctamente.

### Dependencia de orden en `down_revision`

La migración de S5 apunta a la de S3 (`341_variables_art131`) como `down_revision`.
Si S2 y S3 se crearon en paralelo y se fusionaron con `flask db merge`, el `down_revision`
puede ser el merge commit. Verificar con `flask db heads` antes de crear la revisión.
