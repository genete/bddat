"""891_regla_orden_dup_aac — RESOLUCION_DUP no se elabora sin AAC previa

Revision ID: 891_regla_orden_dup_aac
Revises: 918_regla_orden_aap_aac
Create Date: 2026-09-17

Issue #891, ADR-045 §C. La DUP lleva implícita la relación concreta e
individualizada de bienes y derechos (art. 143.3.e RD 1955/2000) y la
urgente ocupación (art. 149.1), y esa relación solo es definitiva cuando
lo es la implantación — de ahí la doctrina del TS sobre Morata de Tajuña
(22, 23, 24-03 y 25-05-2010): no cabe declarar la utilidad pública sin
aprobar previa o simultáneamente el proyecto ejecutivo. Articulo/apartado
del catálogo citan el 149.1 (20 car. máx.); el 143.3.e) y la doctrina
quedan en la descripción y en el ADR.

Ancla real: accion='CREAR', sujeto='ANY/RESOLUCION_DUP/ELABORACION' — mismo
criterio que #918 fijó para RESOLUCION_AAC: el motor no compila sujeto a
nivel de tarea, así que se bloquea un paso antes (abrir el trámite
ELABORACION), no la tarea ELABORAR.

Efecto: BLOQUEAR con escape (patrón por defecto del proyecto para reglas de
reglas_motor — el acto de DUP no ha salido del sistema todavía, así que no
hay motivo para cerrar la puerta del todo). Decisión confirmada con Carlos,
2026-09-17.
"""
from alembic import op
import sqlalchemy as sa


revision = '891_regla_orden_dup_aac'
down_revision = '918_regla_orden_aap_aac'
branch_labels = None
depends_on = None

_VARIABLE = 'tiene_aac_previa'
_ETIQUETA = (
    'Consta AAC (o AAP+AAC conjunta) favorable en la misma solicitud o en '
    'solicitud anterior del expediente'
)
_DESCRIPCION = (
    'No se puede abrir la elaboración de la resolución de DUP: no consta '
    'aprobado el proyecto de ejecución (AAC, en esta misma solicitud o en '
    'solicitud anterior del expediente) con resultado favorable. La DUP no '
    'puede declararse sin el proyecto ejecutivo aprobado (RD 1955/2000 arts. '
    '143.3.e y 149.1; doctrina TS Morata de Tajuña, SSTS 22, 23, 24-03 y '
    '25-05-2010).'
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
        VALUES ('CREAR', 'ANY/RESOLUCION_DUP/ELABORACION', 'BLOQUEAR', :norma_id,
                '149.1', NULL, 15, TRUE, :descripcion)
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
            WHERE sujeto = 'ANY/RESOLUCION_DUP/ELABORACION' AND accion = 'CREAR'
              AND efecto = 'BLOQUEAR' AND descripcion = :descripcion
        )
    """), {'descripcion': _DESCRIPCION})
    conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE sujeto = 'ANY/RESOLUCION_DUP/ELABORACION' AND accion = 'CREAR'
          AND efecto = 'BLOQUEAR' AND descripcion = :descripcion
    """), {'descripcion': _DESCRIPCION})
    conn.execute(sa.text(
        "DELETE FROM public.catalogo_variables WHERE nombre = :nombre"
    ), {'nombre': _VARIABLE})
