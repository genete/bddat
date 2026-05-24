"""460_variables_motor_consultas

Revision ID: 460_variables_motor_consultas
Revises: 456_tramites_organismos
Create Date: 2026-05-24

Issue #460 — Registra variables del motor para el ciclo de CONSULTAS y
la regla ADVERTIR al crear un segundo CONSULTA_TRASLADO_ORGANISMO.
La regla BLOQUEAR de organismos_todos_terminados va en #470.
"""
from alembic import op
import sqlalchemy as sa

revision = '460_variables_motor_consultas'
down_revision = '456_tramites_organismos'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. catalogo_variables
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES
            ('organismos_todos_terminados',
             'Todos los organismos del expediente han alcanzado estado terminal',
             'boolean', NULL, TRUE),
            ('organismo_supera_iteraciones',
             'Algún organismo acumula más de una iteración TRASLADO_ORGANISMO',
             'boolean', NULL, TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """))

    # 2. Regla ADVERTIR al crear CONSULTA_TRASLADO_ORGANISMO con iteraciones previas
    result = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, prioridad, activa, descripcion)
        VALUES (
            'CREAR',
            'ANY/ANY/CONSULTAS/CONSULTA_TRASLADO_ORGANISMO',
            'ADVERTIR',
            10,
            TRUE,
            'Uno o más organismos han requerido más de un traslado de reparos'
        )
        RETURNING id
    """))
    regla_id = result.scalar()

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla
            (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'true'::json, 1
        FROM public.catalogo_variables cv
        WHERE cv.nombre = 'organismo_supera_iteraciones'
    """), {'regla_id': regla_id})


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_regla
        WHERE regla_id IN (
            SELECT id FROM public.reglas_motor
            WHERE sujeto = 'ANY/ANY/CONSULTAS/CONSULTA_TRASLADO_ORGANISMO'
              AND efecto = 'ADVERTIR'
        )
    """))
    conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE sujeto = 'ANY/ANY/CONSULTAS/CONSULTA_TRASLADO_ORGANISMO'
          AND efecto = 'ADVERTIR'
    """))
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_variables
        WHERE nombre IN ('organismos_todos_terminados', 'organismo_supera_iteraciones')
    """))
