"""918_regla_exclusion_mutua_resolucion — RESOLUCION vs. RESOLUCION_AAP/AAC

Revision ID: 918_regla_exclusion_mutua_resolucion
Revises: 918_fases_tramites_aap_aac
Create Date: 2026-09-17

Issue #918, ADR-047 §B. Resolver conjunto o partido es elección del técnico,
declarada en catálogo, no una regla de motor por sí misma — pero una vez
elegido un camino, el otro se bloquea: dos actos resolviendo la misma
autorización serían una duplicación estructural, mismo tipo de invariante
que `version_ya_cubierta` (#895, ADR-044 §F). Sin `norma_id`, mismo criterio
que aquella: no es cita de LPACAP/RD 1955-2000, es consistencia de catálogo.

Deliberadamente NO se exige `RESOLUCION_AAP` creada para poder crear
`RESOLUCION_AAC` (ni viceversa): esa es la regla de orden sustantiva de
ADR-047 §F, con ancla distinta (`RESOLUCION_AAC.ELABORACION.ELABORAR`,
migración propia #918 siguiente commit) y semántica distinta (exige
favorable, no solo existencia). Mezclarla aquí duplicaría el mismo
invariante en dos reglas con ancla distinta.

3 filas `accion='CREAR'`, `efecto='BLOQUEAR'`, prioridad 10 (igual que 895).
"""
from alembic import op
import sqlalchemy as sa


revision = '918_regla_exclusion_mutua_resolucion'
down_revision = '918_fases_tramites_aap_aac'
branch_labels = None
depends_on = None

_VARIABLES = [
    ('existe_resolucion_conjunta',
     'Ya existe una fase RESOLUCION (acto conjunto) en la solicitud'),
    ('existe_resolucion_partida',
     'Ya existe una fase RESOLUCION_AAP o RESOLUCION_AAC (acto partido) en la solicitud'),
]

_MSG_BLOQUEA_PARTIDA = (
    'No se puede crear esta fase: ya existe una RESOLUCION conjunta en esta solicitud. '
    'AAP y AAC se resuelven juntas o por separado desde el inicio — no se puede partir '
    'una resolución ya conjunta.'
)
_MSG_BLOQUEA_CONJUNTA = (
    'No se puede crear esta fase: ya existe una resolución partida (RESOLUCION_AAP o '
    'RESOLUCION_AAC) en esta solicitud. AAP y AAC se resuelven juntas o por separado '
    'desde el inicio — no se puede unificar una resolución ya partida.'
)

# (sujeto, variable, descripcion)
_REGLAS = [
    ('ANY/ANY/RESOLUCION_AAP', 'existe_resolucion_conjunta', _MSG_BLOQUEA_PARTIDA),
    ('ANY/ANY/RESOLUCION_AAC', 'existe_resolucion_conjunta', _MSG_BLOQUEA_PARTIDA),
    ('ANY/ANY/RESOLUCION', 'existe_resolucion_partida', _MSG_BLOQUEA_CONJUNTA),
]


def upgrade():
    conn = op.get_bind()

    for nombre, etiqueta in _VARIABLES:
        conn.execute(sa.text("""
            INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, activa)
            VALUES (:nombre, :etiqueta, 'boolean', TRUE)
            ON CONFLICT (nombre) DO NOTHING
        """), {'nombre': nombre, 'etiqueta': etiqueta})

    for sujeto, variable, descripcion in _REGLAS:
        regla_id = conn.execute(sa.text("""
            INSERT INTO public.reglas_motor
                (accion, sujeto, efecto, prioridad, activa, descripcion)
            VALUES ('CREAR', :sujeto, 'BLOQUEAR', 10, TRUE, :descripcion)
            RETURNING id
        """), {'sujeto': sujeto, 'descripcion': descripcion}).scalar()

        conn.execute(sa.text("""
            INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
            SELECT :regla_id, cv.id, 'EQ', 'true'::json, 1
            FROM public.catalogo_variables cv WHERE cv.nombre = :variable
        """), {'regla_id': regla_id, 'variable': variable})


def downgrade():
    conn = op.get_bind()

    for sujeto, _variable, descripcion in _REGLAS:
        conn.execute(sa.text("""
            DELETE FROM public.condiciones_regla
            WHERE regla_id IN (
                SELECT id FROM public.reglas_motor
                WHERE sujeto = :sujeto AND accion = 'CREAR' AND efecto = 'BLOQUEAR'
                  AND descripcion = :descripcion
            )
        """), {'sujeto': sujeto, 'descripcion': descripcion})
        conn.execute(sa.text("""
            DELETE FROM public.reglas_motor
            WHERE sujeto = :sujeto AND accion = 'CREAR' AND efecto = 'BLOQUEAR'
              AND descripcion = :descripcion
        """), {'sujeto': sujeto, 'descripcion': descripcion})

    for nombre, _etiqueta in _VARIABLES:
        conn.execute(sa.text(
            "DELETE FROM public.catalogo_variables WHERE nombre = :nombre"
        ), {'nombre': nombre})
