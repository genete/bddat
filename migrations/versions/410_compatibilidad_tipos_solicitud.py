"""410_compatibilidad_tipos_solicitud

Revision ID: 410_compatibilidad_tipos_solicitud
Revises: 342a6f032b38
Create Date: 2026-05-27

Issue #410 — Compatibilidad de tipos de solicitud como reglas CREAR del motor.

Variables nuevas:
  - es_expediente_produccion:
      True si el expediente es de tipo Renovable o Convencional.
      RAIPEE y AE_PROVISIONAL solo tienen base legal en instalaciones de generación.

  - tiene_aac_resuelta_favorable:
      True si existe en el expediente una solicitud AAC con fase finalizadora
      favorable. Prerequisito para AE_PROVISIONAL y AE_DEFINITIVA.

Reglas nuevas (CREAR, BLOQUEAR):
  - ANY/RAIPEE_PREVIA     → si es_expediente_produccion == False
  - ANY/RAIPEE_DEFINITIVA → si es_expediente_produccion == False
  - ANY/AE_PROVISIONAL    → si tiene_aac_resuelta_favorable == False
  - ANY/AE_DEFINITIVA     → si tiene_aac_resuelta_favorable == False

Los sujetos tienen 2 segmentos porque se evalúan al CREAR la solicitud
(nivel E/S, sin fase ni trámite).
"""
from alembic import op
import sqlalchemy as sa

revision = '410_compatibilidad_tipos_solicitud'
down_revision = '342a6f032b38'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. Variables nuevas en catalogo_variables
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES
            ('es_expediente_produccion',
             'El expediente es de tipo producción (Renovable o Convencional)',
             'boolean', NULL, TRUE),
            ('tiene_aac_resuelta_favorable',
             'Existe en el expediente una AAC resuelta favorablemente',
             'boolean', NULL, TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """))

    # 2. Reglas RAIPEE — bloqueadas fuera de expedientes de producción

    result = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, prioridad, activa, descripcion)
        VALUES (
            'CREAR',
            'ANY/RAIPEE_PREVIA',
            'BLOQUEAR',
            10,
            TRUE,
            'La inscripción previa en RAIPEE solo aplica a instalaciones de producción '
            '(Renovable o Convencional)'
        )
        RETURNING id
    """))
    regla_raipee_previa_id = result.scalar()

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla
            (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'false'::json, 1
        FROM public.catalogo_variables cv
        WHERE cv.nombre = 'es_expediente_produccion'
    """), {'regla_id': regla_raipee_previa_id})

    result = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, prioridad, activa, descripcion)
        VALUES (
            'CREAR',
            'ANY/RAIPEE_DEFINITIVA',
            'BLOQUEAR',
            10,
            TRUE,
            'La inscripción definitiva en RAIPEE solo aplica a instalaciones de producción '
            '(Renovable o Convencional)'
        )
        RETURNING id
    """))
    regla_raipee_def_id = result.scalar()

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla
            (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'false'::json, 1
        FROM public.catalogo_variables cv
        WHERE cv.nombre = 'es_expediente_produccion'
    """), {'regla_id': regla_raipee_def_id})

    # 3. Reglas AE — bloqueadas sin AAC resuelta favorable

    result = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, prioridad, activa, descripcion)
        VALUES (
            'CREAR',
            'ANY/AE_PROVISIONAL',
            'BLOQUEAR',
            10,
            TRUE,
            'No se puede solicitar autorización de explotación provisional sin AAC '
            'resuelta favorablemente en el expediente'
        )
        RETURNING id
    """))
    regla_ae_prov_id = result.scalar()

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla
            (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'false'::json, 1
        FROM public.catalogo_variables cv
        WHERE cv.nombre = 'tiene_aac_resuelta_favorable'
    """), {'regla_id': regla_ae_prov_id})

    result = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, prioridad, activa, descripcion)
        VALUES (
            'CREAR',
            'ANY/AE_DEFINITIVA',
            'BLOQUEAR',
            10,
            TRUE,
            'No se puede solicitar autorización de explotación definitiva sin AAC '
            'resuelta favorablemente en el expediente'
        )
        RETURNING id
    """))
    regla_ae_def_id = result.scalar()

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla
            (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'false'::json, 1
        FROM public.catalogo_variables cv
        WHERE cv.nombre = 'tiene_aac_resuelta_favorable'
    """), {'regla_id': regla_ae_def_id})


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_regla
        WHERE regla_id IN (
            SELECT id FROM public.reglas_motor
            WHERE sujeto IN (
                'ANY/RAIPEE_PREVIA',
                'ANY/RAIPEE_DEFINITIVA',
                'ANY/AE_PROVISIONAL',
                'ANY/AE_DEFINITIVA'
            )
              AND efecto = 'BLOQUEAR'
              AND accion = 'CREAR'
        )
    """))
    conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE sujeto IN (
            'ANY/RAIPEE_PREVIA',
            'ANY/RAIPEE_DEFINITIVA',
            'ANY/AE_PROVISIONAL',
            'ANY/AE_DEFINITIVA'
        )
          AND efecto = 'BLOQUEAR'
          AND accion = 'CREAR'
    """))
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_variables
        WHERE nombre IN (
            'es_expediente_produccion',
            'tiene_aac_resuelta_favorable'
        )
    """))
