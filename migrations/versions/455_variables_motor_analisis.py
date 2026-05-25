"""455_variables_motor_analisis

Revision ID: 455_variables_motor_analisis
Revises: 463_seed_plazos_consultas
Create Date: 2026-05-25

Issue #455 — Variables del motor para ANALISIS_SOLICITUD:

  - tramite_analisis_con_deficiencias:
      True si algún trámite ANALISIS_DOCUMENTAL tiene diagnóstico desfavorable.
      Regla: BLOQUEAR CREAR ANY/ANY/ANALISIS_SOLICITUD/COMUNICACION_INICIO.

  - tramite_requerimiento_sin_respuesta:
      True si algún trámite REQUERIMIENTO_SUBSANACION tiene ESPERAR_PLAZO sin
      documento producido (titular no ha respondido).
      Regla: BLOQUEAR CREAR ANY/ANY/RESOLUCION.
"""
from alembic import op
import sqlalchemy as sa

revision = '455_variables_motor_analisis'
down_revision = '463_seed_plazos_consultas'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. catalogo_variables
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES
            ('tramite_analisis_con_deficiencias',
             'Existe trámite ANALISIS_DOCUMENTAL con diagnóstico desfavorable',
             'boolean', NULL, TRUE),
            ('tramite_requerimiento_sin_respuesta',
             'Existe trámite REQUERIMIENTO_SUBSANACION con ESPERAR_PLAZO sin respuesta del titular',
             'boolean', NULL, TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """))

    # 2. Regla: BLOQUEAR CREAR COMUNICACION_INICIO si análisis con deficiencias
    result = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, prioridad, activa, descripcion)
        VALUES (
            'CREAR',
            'ANY/ANY/ANALISIS_SOLICITUD/COMUNICACION_INICIO',
            'BLOQUEAR',
            10,
            TRUE,
            'No se puede comunicar el inicio con deficiencias pendientes en el análisis documental'
        )
        RETURNING id
    """))
    regla_analisis_id = result.scalar()

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla
            (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'true'::json, 1
        FROM public.catalogo_variables cv
        WHERE cv.nombre = 'tramite_analisis_con_deficiencias'
    """), {'regla_id': regla_analisis_id})

    # 3. Regla: BLOQUEAR CREAR fase RESOLUCION si requerimiento sin respuesta
    result = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, prioridad, activa, descripcion)
        VALUES (
            'CREAR',
            'ANY/ANY/RESOLUCION',
            'BLOQUEAR',
            10,
            TRUE,
            'No se puede abrir la fase de resolución con un requerimiento de subsanación sin respuesta'
        )
        RETURNING id
    """))
    regla_req_id = result.scalar()

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla
            (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'true'::json, 1
        FROM public.catalogo_variables cv
        WHERE cv.nombre = 'tramite_requerimiento_sin_respuesta'
    """), {'regla_id': regla_req_id})


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_regla
        WHERE regla_id IN (
            SELECT id FROM public.reglas_motor
            WHERE sujeto IN (
                'ANY/ANY/ANALISIS_SOLICITUD/COMUNICACION_INICIO',
                'ANY/ANY/RESOLUCION'
            )
              AND efecto = 'BLOQUEAR'
        )
    """))
    conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE sujeto IN (
            'ANY/ANY/ANALISIS_SOLICITUD/COMUNICACION_INICIO',
            'ANY/ANY/RESOLUCION'
        )
          AND efecto = 'BLOQUEAR'
    """))
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_variables
        WHERE nombre IN (
            'tramite_analisis_con_deficiencias',
            'tramite_requerimiento_sin_respuesta'
        )
    """))
