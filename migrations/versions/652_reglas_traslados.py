"""652_reglas_traslados — reglas de orden de los traslados al titular y al organismo

Revision ID: 652_reglas_traslados
Revises: 652_reglas_orden_4_tramos
Create Date: 2026-11-09

Issue #652 (ADR-042 §D, DISEÑO_CONSULTAS_ORGANISMOS.md §4). Dos reglas BLOQUEAR sobre la
creación de los traslados del ciclo de consultas, forzables con justificación (el motor
no distingue «puerta cerrada»: todo BLOQUEAR de reglas_motor tiene escape):

  - CONSULTA_TRASLADO_TITULAR: bloquea si el organismo no ha respondido de verdad o su
    respuesta no está analizada. Procede ante cualquier respuesta real (conformidad,
    condicionados u oposición: arts. 127.3, 131.3 y 147.1) y no ante el silencio
    (arts. 127.2, 131.1 y 146.1, conformidad tácita).
  - CONSULTA_TRASLADO_ORGANISMO: bloquea si la última respuesta del organismo no fue
    desfavorable, o el titular aún no ha contestado al traslado o su respuesta no está
    analizada (arts. 127.4, 131.4 y 147.2).

El camino lleva cuatro tramos (tipo de expediente / tipo de solicitud / fase / trámite):
el motor compila así la creación de un trámite desde esta misma issue. DUP se comporta
como AAC y la ley no distingue procedimientos en esto, así que no hay una regla por tipo
de solicitud (decisión de Carlos, 2026-11-07).

Las vueltas del ciclo no se limitan con una regla: la ley no dice cuántas, y el aviso es
un texto declarativo en la ANALIZAR del organismo, no del motor.

Variables nuevas (boolean): `organismo_respuesta_analizada` y `traslado_organismo_procede`.
Miran SOLO el organismo del traslado que se intenta crear (devuelven None si el contexto
no trae organismo, y entonces la condición `EQ false` no dispara).

Localiza la norma por título, nunca por id (los ids no son estables entre instalaciones),
y falla con error si no la encuentra. Cada INSERT es simple —sin ON CONFLICT— para que una
fila ya existente rompa la migración en vez de saltarse en silencio.
"""
from alembic import op
import sqlalchemy as sa


revision = '652_reglas_traslados'
down_revision = '652_reglas_orden_4_tramos'
branch_labels = None
depends_on = None


_VARIABLES = (
    ('organismo_respuesta_analizada',
     'El organismo ha respondido de verdad y su última respuesta está analizada'),
    ('traslado_organismo_procede',
     'La última respuesta del organismo fue desfavorable y el titular ya contestó al traslado, '
     'con su respuesta analizada'),
)

# (sujeto, variable, articulo, descripcion)
_REGLAS = (
    ('ANY/ANY/CONSULTAS/CONSULTA_TRASLADO_TITULAR',
     'organismo_respuesta_analizada',
     '127.3/131.3/147.1',
     'No se puede dar traslado al titular: el organismo no consta que haya respondido, o su '
     'respuesta aún no está analizada. Un organismo que calla no ha respondido y no hay nada '
     'que trasladar (RD 1955/2000 arts. 127.2, 127.3, 131.1, 131.3, 146.1 y 147.1).'),
    ('ANY/ANY/CONSULTAS/CONSULTA_TRASLADO_ORGANISMO',
     'traslado_organismo_procede',
     '127.4/131.4/147.2',
     'No procede el traslado al organismo: su última respuesta no fue desfavorable, o el '
     'titular aún no ha contestado al traslado, o su respuesta no está analizada '
     '(RD 1955/2000 arts. 127.4, 131.4 y 147.2).'),
)


def upgrade():
    conn = op.get_bind()

    norma_id = conn.execute(sa.text(
        "SELECT id FROM public.normas WHERE titulo ILIKE '%1955/2000%' ORDER BY id LIMIT 1"
    )).scalar()
    if norma_id is None:
        raise RuntimeError(
            '652_reglas_traslados: no se encuentra la norma RD 1955/2000 en public.normas.')

    for nombre, etiqueta in _VARIABLES:
        conn.execute(sa.text("""
            INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
            VALUES (:nombre, :etiqueta, 'boolean', :norma_id, TRUE)
        """), {'nombre': nombre, 'etiqueta': etiqueta, 'norma_id': norma_id})

    for sujeto, variable, articulo, descripcion in _REGLAS:
        regla_id = conn.execute(sa.text("""
            INSERT INTO public.reglas_motor
                (accion, sujeto, efecto, norma_id, articulo, prioridad, activa, descripcion)
            VALUES ('CREAR', :sujeto, 'BLOQUEAR', :norma_id, :articulo, 15, TRUE, :descripcion)
            RETURNING id
        """), {'sujeto': sujeto, 'norma_id': norma_id, 'articulo': articulo,
               'descripcion': descripcion}).scalar()
        conn.execute(sa.text("""
            INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
            SELECT :regla_id, cv.id, 'EQ', 'false'::json, 1
            FROM public.catalogo_variables cv WHERE cv.nombre = :variable
        """), {'regla_id': regla_id, 'variable': variable})


def downgrade():
    conn = op.get_bind()

    for sujeto, _variable, _articulo, descripcion in _REGLAS:
        # Sus condiciones se van con la regla (ON DELETE CASCADE).
        conn.execute(sa.text("""
            DELETE FROM public.reglas_motor
            WHERE accion = 'CREAR' AND sujeto = :sujeto AND descripcion = :descripcion
        """), {'sujeto': sujeto, 'descripcion': descripcion})

    for nombre, _etiqueta in _VARIABLES:
        conn.execute(sa.text(
            "DELETE FROM public.catalogo_variables WHERE nombre = :nombre"), {'nombre': nombre})
