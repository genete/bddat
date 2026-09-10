"""901_certificado_sol_reformado

Revision ID: 901_certificado_sol_reformado
Revises: 899_requerimientos_version
Create Date: 2026-09-10

`certificados.solicitud_id` + `certificados.reformado_id` (ADR-044 R5, #901).

Certificado no sabía de qué solicitud ni de qué ronda hablaba ningún
certificado, de ningún tipo — solo `documento_id`. CERT_FIN_IP_CONSULTAS
necesita las dos para poder re-emitirse por ronda sin confundirse con el
certificado de otra solicitud del mismo expediente (defecto anterior a los
reformados, que estos hacen mucho más visible). El resto de tipos de
certificado se quedan con las dos columnas a NULL.

`ON DELETE RESTRICT` en las dos FK, mismo criterio que `fases.reformado_id`
(R3, #895): no tiene sentido borrar una solicitud o revertir un reformado
mientras un certificado siga anclado a ellos.

Dos índices únicos parciales por la misma razón que en R4
(`documentos_requisito`, `coberturas_item_tecnico`): Postgres no deduplica
NULL en un índice único multi-columna, y aquí además `solicitud_id` es NULL
para la inmensa mayoría de filas (todo certificado que no sea
CERT_FIN_IP_CONSULTAS), así que el predicado exige explícitamente
`solicitud_id IS NOT NULL` para no confundir esas filas con un intento de
solicitud repetida.

Sin backfill: las dos columnas nacen NULL en las filas existentes (0
CERT_FIN_IP_CONSULTAS en desarrollo a fecha de esta migración).
"""
from alembic import op
import sqlalchemy as sa

revision = '901_certificado_sol_reformado'
down_revision = '899_requerimientos_version'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'certificados',
        sa.Column(
            'solicitud_id', sa.Integer(), nullable=True,
            comment='FK a SOLICITUDES. NULL salvo en certificados que necesitan scoping por '
                    'solicitud (hoy, CERT_FIN_IP_CONSULTAS)',
        ),
        schema='public',
    )
    op.add_column(
        'certificados',
        sa.Column(
            'reformado_id', sa.Integer(), nullable=True,
            comment='FK a REFORMADOS_PROYECTO. NULL = versión inicial (o certificado sin '
                    'scoping por versión)',
        ),
        schema='public',
    )

    op.create_foreign_key(
        'fk_certificado_solicitud', 'certificados', 'solicitudes',
        ['solicitud_id'], ['id'],
        source_schema='public', referent_schema='public',
        ondelete='RESTRICT',
    )
    op.create_foreign_key(
        'fk_certificado_reformado', 'certificados', 'reformados_proyecto',
        ['reformado_id'], ['id'],
        source_schema='public', referent_schema='public',
        ondelete='RESTRICT',
    )

    op.create_index('idx_certificados_solicitud', 'certificados', ['solicitud_id'],
                     schema='public')
    op.create_index('idx_certificados_reformado', 'certificados', ['reformado_id'],
                     schema='public')

    op.create_index(
        'uq_certificado_ip_consultas_no_reformado', 'certificados', ['solicitud_id'],
        unique=True, schema='public',
        postgresql_where=sa.text('solicitud_id IS NOT NULL AND reformado_id IS NULL'),
    )
    op.create_index(
        'uq_certificado_ip_consultas_por_version', 'certificados',
        ['solicitud_id', 'reformado_id'],
        unique=True, schema='public',
        postgresql_where=sa.text('solicitud_id IS NOT NULL AND reformado_id IS NOT NULL'),
    )


def downgrade():
    op.drop_index('uq_certificado_ip_consultas_por_version', table_name='certificados',
                   schema='public')
    op.drop_index('uq_certificado_ip_consultas_no_reformado', table_name='certificados',
                   schema='public')

    op.drop_index('idx_certificados_reformado', table_name='certificados', schema='public')
    op.drop_index('idx_certificados_solicitud', table_name='certificados', schema='public')

    op.drop_constraint('fk_certificado_reformado', 'certificados',
                        type_='foreignkey', schema='public')
    op.drop_constraint('fk_certificado_solicitud', 'certificados',
                        type_='foreignkey', schema='public')

    op.drop_column('certificados', 'reformado_id', schema='public')
    op.drop_column('certificados', 'solicitud_id', schema='public')
