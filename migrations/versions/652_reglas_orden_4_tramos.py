"""652_reglas_orden_4_tramos — reglas de orden a cuatro tramos y retirada del aviso de vuelta

Revision ID: 652_reglas_orden_4_tramos
Revises: 1040_comentario_documento_principal
Create Date: 2026-11-09

Issue #652. El motor compila el sujeto de crear un trámite con cuatro tramos (tipo de
expediente / tipo de solicitud / fase / trámite), como el de un trámite existente y como
el que construye la interfaz del supervisor (#170): `ExpedienteContext.solicitud` deriva la
solicitud de la fase del dict de crear trámite. Hasta ahora compilaba tres y dos reglas se
habían escrito a medida de ese fallo:

  - ANY/RESOLUCION_AAC/ELABORACION (#918, ADR-047 §F) y
  - ANY/RESOLUCION_DUP/ELABORACION (#891, ADR-046 §E)

pasan a ANY/ANY/<fase>/ELABORACION: cuatro tramos, expresables desde el editor del
supervisor (con tres, el editor las mostraba como «Cualquiera» y al guardar las habría
reescrito). No cambia su condición, su efecto ni su descripción.

También se retira el aviso «Uno o más organismos han requerido más de un traslado de
reparos» (#460) y su variable `organismo_supera_iteraciones`: miraba los traslados de
TODOS los organismos del expediente y no los del que se tramita, y nunca disparó porque su
sujeto de cuatro tramos no casaba. El aviso de las vueltas pasa a ser un texto declarativo
en la tarea ANALIZAR del organismo (#652, ADR-042 §D), no una regla del motor.

La migración localiza cada regla por (sujeto, descripción), nunca por id (los ids no son
estables entre instalaciones) y FALLA con error si no encuentra exactamente una fila: una
migración de datos que afecta a 0 filas no avisa de nada, y aquí sería una regla que se
queda sin migrar en silencio. Si falla en una base con la descripción editada a mano, hay
que revisar esa regla antes de seguir, no saltarse la comprobación.
"""
from alembic import op
import sqlalchemy as sa


revision = '652_reglas_orden_4_tramos'
down_revision = '1040_comentario_documento_principal'
branch_labels = None
depends_on = None


# (sujeto viejo, sujeto nuevo, comienzo de la descripción)
_REGLAS_ORDEN = (
    ('ANY/RESOLUCION_AAC/ELABORACION', 'ANY/ANY/RESOLUCION_AAC/ELABORACION',
     'No se puede abrir la elaboración de la resolución de AAC%'),
    ('ANY/RESOLUCION_DUP/ELABORACION', 'ANY/ANY/RESOLUCION_DUP/ELABORACION',
     'No se puede abrir la elaboración de la resolución de DUP%'),
)

_SUJETO_AVISO = 'ANY/ANY/CONSULTAS/CONSULTA_TRASLADO_ORGANISMO'
_DESCRIPCION_AVISO = 'Uno o más organismos han requerido más de un traslado de reparos'
_VARIABLE_AVISO = 'organismo_supera_iteraciones'
_ETIQUETA_AVISO = 'Algún organismo acumula más de una iteración TRASLADO_ORGANISMO'

# Tablas con FK a catalogo_variables: la variable no se borra si alguna la usa.
_USOS_VARIABLE = (
    'condiciones_regla', 'condiciones_excepcion', 'condiciones_plazo',
    'condiciones_requisito', 'condiciones_item_tecnico',
)


def _exactamente_una(resultado, que):
    if resultado.rowcount != 1:
        raise RuntimeError(
            f'652_reglas_orden_4_tramos: se esperaba 1 fila para {que} y hay {resultado.rowcount}. '
            'Revisar la regla en la base (¿descripción o sujeto editados a mano?) antes de seguir.')


def upgrade():
    conn = op.get_bind()

    for viejo, nuevo, descripcion in _REGLAS_ORDEN:
        resultado = conn.execute(sa.text("""
            UPDATE public.reglas_motor
            SET sujeto = :nuevo
            WHERE accion = 'CREAR' AND sujeto = :viejo AND descripcion LIKE :descripcion
        """), {'nuevo': nuevo, 'viejo': viejo, 'descripcion': descripcion})
        _exactamente_una(resultado, f'la regla {viejo}')

    # Aviso de vuelta (#460): sus condiciones y excepciones se van con la regla (ON DELETE CASCADE).
    resultado = conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE accion = 'CREAR' AND sujeto = :sujeto AND efecto = 'ADVERTIR'
          AND descripcion = :descripcion
    """), {'sujeto': _SUJETO_AVISO, 'descripcion': _DESCRIPCION_AVISO})
    _exactamente_una(resultado, f'la regla de aviso {_SUJETO_AVISO}')

    variable_id = conn.execute(sa.text(
        "SELECT id FROM public.catalogo_variables WHERE nombre = :nombre"
    ), {'nombre': _VARIABLE_AVISO}).scalar()
    if variable_id is None:
        raise RuntimeError(f"652_reglas_orden_4_tramos: no existe la variable '{_VARIABLE_AVISO}'.")
    for tabla in _USOS_VARIABLE:
        usos = conn.execute(sa.text(
            f"SELECT count(*) FROM public.{tabla} WHERE variable_id = :id"), {'id': variable_id}).scalar()
        if usos:
            raise RuntimeError(
                f"652_reglas_orden_4_tramos: la variable '{_VARIABLE_AVISO}' la usa aún {tabla} "
                f'({usos} fila/s); no se borra.')
    resultado = conn.execute(sa.text(
        "DELETE FROM public.catalogo_variables WHERE id = :id"), {'id': variable_id})
    _exactamente_una(resultado, f"la variable '{_VARIABLE_AVISO}'")


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES (:nombre, :etiqueta, 'boolean', NULL, TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """), {'nombre': _VARIABLE_AVISO, 'etiqueta': _ETIQUETA_AVISO})

    regla_id = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor (accion, sujeto, efecto, prioridad, activa, descripcion)
        VALUES ('CREAR', :sujeto, 'ADVERTIR', 10, TRUE, :descripcion)
        RETURNING id
    """), {'sujeto': _SUJETO_AVISO, 'descripcion': _DESCRIPCION_AVISO}).scalar()
    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'true'::json, 1
        FROM public.catalogo_variables cv WHERE cv.nombre = :variable
    """), {'regla_id': regla_id, 'variable': _VARIABLE_AVISO})

    for viejo, nuevo, descripcion in _REGLAS_ORDEN:
        conn.execute(sa.text("""
            UPDATE public.reglas_motor
            SET sujeto = :viejo
            WHERE accion = 'CREAR' AND sujeto = :nuevo AND descripcion LIKE :descripcion
        """), {'viejo': viejo, 'nuevo': nuevo, 'descripcion': descripcion})
