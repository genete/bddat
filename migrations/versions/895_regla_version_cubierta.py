"""895_regla_version_cubierta

Revision ID: 895_regla_version_cubierta
Revises: 895_fases_reformado_id
Create Date: 2026-09-10

Regla genérica de §F (ADR-044, R3 #895): «se prohíbe crear una fase que cubra
una versión ya cubierta por otra fase del mismo tipo».

**Sujeto `ANY/ANY/ANY` sin condición de encuadre por fase, y no por descuido**:
son tres segmentos y `camino_casa` exige misma longitud, así que solo casa con
la creación de una fase (crear trámite compila cuatro segmentos, crear
solicitud dos). Cubre las nueve fases del catálogo, incluidas `RESOLUCION` y
`RECONOCIMIENTO_INTERESADO`, que no se repiten ni con reformado.

Sin `norma_id`: no es una cita de LPACAP/RD 1955-2000, sino un invariante de
consistencia entre `fases.reformado_id` y el catálogo — la misma versión no
puede instruirse dos veces por el mismo tipo de fase.

La variable `version_ya_cubierta` se registra en `app/services/variables/` en
el commit anterior a esta migración (orden de #780/#887): `activa=TRUE` solo
se marca cuando la función ya existe en el registry.

No se toca la regla 1683 (`ADVERTIR`, segunda ronda de consultas, #396): el
`BLOQUEAR` gana siempre, así que esa advertencia solo se ve cuando sí hay
reformado — que es cuando su texto sirve.
"""
from alembic import op
import sqlalchemy as sa

revision = '895_regla_version_cubierta'
down_revision = '895_fases_reformado_id'
branch_labels = None
depends_on = None


DESCRIPCION = (
    'No se puede crear esta fase: la versión del proyecto que le correspondería '
    'ya está cubierta por otra fase del mismo tipo. Para abrir una ronda nueva, '
    'declare antes un reformado de proyecto (ADR-044 §F).'
)


def upgrade():
    conn = op.get_bind()

    # 1. La variable
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, activa)
        VALUES ('version_ya_cubierta',
                'Ya existe una fase del tipo que se pretende crear cubriendo la misma '
                'versión del proyecto',
                'boolean', TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """))

    # 2. La regla
    regla_id = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, prioridad, activa, descripcion)
        VALUES ('CREAR', 'ANY/ANY/ANY', 'BLOQUEAR', 10, TRUE, :descripcion)
        RETURNING id
    """), {'descripcion': DESCRIPCION}).scalar()

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'true'::json, 1
        FROM public.catalogo_variables cv WHERE cv.nombre = 'version_ya_cubierta'
    """), {'regla_id': regla_id})


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_regla
        WHERE regla_id IN (
            SELECT id FROM public.reglas_motor
            WHERE sujeto = 'ANY/ANY/ANY' AND accion = 'CREAR' AND efecto = 'BLOQUEAR'
              AND descripcion = :descripcion
        )
    """), {'descripcion': DESCRIPCION})
    conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE sujeto = 'ANY/ANY/ANY' AND accion = 'CREAR' AND efecto = 'BLOQUEAR'
          AND descripcion = :descripcion
    """), {'descripcion': DESCRIPCION})
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_variables WHERE nombre = 'version_ya_cubierta'
    """))
