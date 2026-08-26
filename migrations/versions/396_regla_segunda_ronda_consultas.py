"""396_regla_segunda_ronda_consultas

Revision ID: 396_regla_segunda_ronda_consultas
Revises: 396_consulta_separata_no_generica
Create Date: 2026-08-26

Issue #396 bloque 6 — Aviso de motor al crear una segunda fase CONSULTAS
(modificado de proyecto, DISEÑO_CONSULTAS_ORGANISMOS.md §6 bis). Duplicar la
fase ya está permitido hoy (`crear_fase` no comprueba duplicidad, ninguna
regla lo impedía) — este bloque solo añade el ADVERTIR informativo, no
habilita nada. Texto estático porque `reglas_motor.descripcion` no interpola
variables.
"""
from alembic import op
import sqlalchemy as sa


revision = '396_regla_segunda_ronda_consultas'
down_revision = '396_consulta_separata_no_generica'
branch_labels = None
depends_on = None

_SUJETO = 'ANY/ANY/CONSULTAS'
_DESCRIPCION = ('Nueva ronda de consultas. Compruebe que los documentos del '
                 'proyecto y las separatas lo reflejan.')


def upgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES (
            'existe_fase_consultas_previa',
            'La solicitud ya tiene una fase CONSULTAS previa',
            'boolean', NULL, TRUE
        )
        ON CONFLICT (nombre) DO NOTHING
    """))

    result = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, prioridad, activa, descripcion)
        VALUES ('CREAR', :sujeto, 'ADVERTIR', 10, TRUE, :descripcion)
        RETURNING id
    """), {'sujeto': _SUJETO, 'descripcion': _DESCRIPCION})
    regla_id = result.scalar()

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla
            (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'true'::json, 1
        FROM public.catalogo_variables cv
        WHERE cv.nombre = 'existe_fase_consultas_previa'
    """), {'regla_id': regla_id})


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_regla
        WHERE regla_id IN (
            SELECT id FROM public.reglas_motor
            WHERE sujeto = :sujeto AND efecto = 'ADVERTIR' AND descripcion = :descripcion
        )
    """), {'sujeto': _SUJETO, 'descripcion': _DESCRIPCION})
    conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE sujeto = :sujeto AND efecto = 'ADVERTIR' AND descripcion = :descripcion
    """), {'sujeto': _SUJETO, 'descripcion': _DESCRIPCION})
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_variables
        WHERE nombre = 'existe_fase_consultas_previa'
    """))
