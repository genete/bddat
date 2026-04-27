"""302_fase_finalizadora

Revision ID: 8deef1de808e
Revises: a3f1c8e290bd
Create Date: 2026-04-27 19:02:19.513121

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8deef1de808e'
down_revision = 'a3f1c8e290bd'
branch_labels = None
depends_on = None


def upgrade():
    # A. Campo es_finalizadora en tipos_fases
    op.add_column('tipos_fases',
        sa.Column('es_finalizadora', sa.Boolean, nullable=False,
                  server_default='false',
                  comment='True si esta fase cierra la solicitud al finalizarse')
    )
    op.execute("UPDATE tipos_fases SET es_finalizadora = TRUE WHERE codigo = 'RESOLUCION'")

    # B. Nuevo tipo_fase RECONOCIMIENTO_INTERESADO
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "INSERT INTO tipos_fases (codigo, nombre, abrev, nombre_en_plantilla, es_finalizadora) "
        "VALUES ('RECONOCIMIENTO_INTERESADO', 'Reconocimiento de Interesado', "
        "'Rec. Interesado', 'Reconocimiento de Interesado', TRUE) RETURNING id"
    ))
    nuevo_id = result.scalar()

    # C. fases_tramites: ELABORACION(22) y NOTIFICACION(23)
    conn.execute(sa.text(
        f"INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES "
        f"({nuevo_id}, 22), ({nuevo_id}, 23)"
    ))

    # D. solicitudes_fases — 4 entradas de whitelist
    conn.execute(sa.text(
        f"INSERT INTO solicitudes_fases (tipo_solicitud_id, tipo_fase_id) VALUES "
        f"(14, {nuevo_id}), "   # INTERESADO → RECONOCIMIENTO_INTERESADO
        f"(11, 8), "            # DESISTIMIENTO → RESOLUCION
        f"(12, 8), "            # RENUNCIA → RESOLUCION
        f"(17, 8)"              # OTRO → RESOLUCION
    ))

    # E. catalogo_variables — nueva variable del motor
    result2 = conn.execute(sa.text(
        "INSERT INTO catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa) "
        "VALUES ('existe_fase_finalizadora_cerrada', "
        "'Existe fase finalizadora cerrada en la solicitud', "
        "'boolean', NULL, TRUE) RETURNING id"
    ))
    var_id = result2.scalar()

    # F. regla FINALIZAR SOLICITUD + condición
    result3 = conn.execute(sa.text(
        "INSERT INTO reglas_motor (accion, sujeto, efecto, prioridad, activa, descripcion) "
        "VALUES ('FINALIZAR', 'ANY/ANY', 'BLOQUEAR', 0, TRUE, "
        "'No se puede finalizar la solicitud: no existe ninguna fase finalizadora cerrada') "
        "RETURNING id"
    ))
    regla_id = result3.scalar()

    conn.execute(sa.text(
        f"INSERT INTO condiciones_regla (regla_id, variable_id, operador, valor, orden) "
        f"VALUES ({regla_id}, {var_id}, 'EQ', 'false'::json, 1)"
    ))


def downgrade():
    conn = op.get_bind()

    # Eliminar condición y regla FINALIZAR SOLICITUD
    conn.execute(sa.text(
        "DELETE FROM condiciones_regla WHERE regla_id = "
        "(SELECT id FROM reglas_motor WHERE accion='FINALIZAR' AND sujeto='ANY/ANY')"
    ))
    conn.execute(sa.text(
        "DELETE FROM reglas_motor WHERE accion='FINALIZAR' AND sujeto='ANY/ANY'"
    ))

    # Eliminar variable del catálogo
    conn.execute(sa.text(
        "DELETE FROM catalogo_variables WHERE nombre='existe_fase_finalizadora_cerrada'"
    ))

    # Eliminar entradas de solicitudes_fases
    conn.execute(sa.text(
        "DELETE FROM solicitudes_fases WHERE tipo_fase_id IN "
        "(SELECT id FROM tipos_fases WHERE codigo='RECONOCIMIENTO_INTERESADO') "
        "OR (tipo_solicitud_id IN (11,12,17) AND tipo_fase_id=8)"
    ))

    # Eliminar fases_tramites y tipo_fase RECONOCIMIENTO_INTERESADO
    conn.execute(sa.text(
        "DELETE FROM fases_tramites WHERE tipo_fase_id = "
        "(SELECT id FROM tipos_fases WHERE codigo='RECONOCIMIENTO_INTERESADO')"
    ))
    conn.execute(sa.text(
        "DELETE FROM tipos_fases WHERE codigo='RECONOCIMIENTO_INTERESADO'"
    ))

    # Revertir es_finalizadora en RESOLUCION y eliminar columna
    op.execute("UPDATE tipos_fases SET es_finalizadora = FALSE WHERE codigo = 'RESOLUCION'")
    op.drop_column('tipos_fases', 'es_finalizadora')
