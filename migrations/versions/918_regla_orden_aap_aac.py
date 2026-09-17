"""918_regla_orden_aap_aac — RESOLUCION_AAC no se elabora sin AAP favorable

Revision ID: 918_regla_orden_aap_aac
Revises: 918_reglas_motor_duplicado_resolucion
Create Date: 2026-09-17

Issue #918, ADR-047 §F. Cita normativa (ya confirmada en el ADR, commit
e2ac9de): RD 1955/2000 arts. 128.4, 130.1 y 131.1 párr. 2 — la Sección 2.ª
(aprobación de proyecto de ejecución, AAC) está construida como fase que
sigue a la AAP ya resuelta. Articulo/apartado del catálogo citan el 131.1
párr. 2 (20 car. máx. en el esquema, no caben las tres referencias juntas;
las otras dos quedan en la descripción y en el ADR).

Ancla real: accion='CREAR', sujeto='ANY/RESOLUCION_AAC/ELABORACION' — NO
'RESOLUCION_AAC.ELABORACION.ELABORAR' (tarea) como dice literalmente el ADR:
el motor no compila sujeto a nivel de tarea (ver docstring de la variable
en calculado.py). Bloquea abrir el trámite ELABORACION bajo RESOLUCION_AAC,
un paso antes de la tarea ELABORAR — decisión explícita con Carlos,
2026-09-17, para no construir plumbing nuevo en el motor. Mismo criterio
aplicará a #891 cuando llegue su turno (ADR-046 §E, RESOLUCION_DUP).
"""
from alembic import op
import sqlalchemy as sa


revision = '918_regla_orden_aap_aac'
down_revision = '918_reglas_motor_duplicado_resolucion'
branch_labels = None
depends_on = None

_VARIABLE = 'tiene_aap_favorable_misma_solicitud'
_ETIQUETA = 'Existe RESOLUCION_AAP en la misma solicitud, finalizada con resultado favorable'
_DESCRIPCION = (
    'No se puede abrir la elaboración de la resolución de AAC: la RESOLUCION_AAP '
    'de esta misma solicitud no consta finalizada con resultado favorable. Resuelva '
    'primero la AAP (RD 1955/2000 arts. 128.4, 130.1 y 131.1 párr. 2).'
)


def upgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, activa)
        VALUES (:nombre, :etiqueta, 'boolean', TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """), {'nombre': _VARIABLE, 'etiqueta': _ETIQUETA})

    norma_id = conn.execute(sa.text(
        "SELECT id FROM public.normas WHERE titulo ILIKE '%1955/2000%' LIMIT 1"
    )).scalar()

    regla_id = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, norma_id, articulo, apartado, prioridad,
             activa, descripcion)
        VALUES ('CREAR', 'ANY/RESOLUCION_AAC/ELABORACION', 'BLOQUEAR', :norma_id,
                '131.1', 'párr. 2', 15, TRUE, :descripcion)
        RETURNING id
    """), {'norma_id': norma_id, 'descripcion': _DESCRIPCION}).scalar()

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'false'::json, 1
        FROM public.catalogo_variables cv WHERE cv.nombre = :variable
    """), {'regla_id': regla_id, 'variable': _VARIABLE})


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_regla
        WHERE regla_id IN (
            SELECT id FROM public.reglas_motor
            WHERE sujeto = 'ANY/RESOLUCION_AAC/ELABORACION' AND accion = 'CREAR'
              AND efecto = 'BLOQUEAR' AND descripcion = :descripcion
        )
    """), {'descripcion': _DESCRIPCION})
    conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE sujeto = 'ANY/RESOLUCION_AAC/ELABORACION' AND accion = 'CREAR'
          AND efecto = 'BLOQUEAR' AND descripcion = :descripcion
    """), {'descripcion': _DESCRIPCION})
    conn.execute(sa.text(
        "DELETE FROM public.catalogo_variables WHERE nombre = :nombre"
    ), {'nombre': _VARIABLE})
