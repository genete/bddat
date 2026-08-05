"""728_firmantes_portafirmas

Revision ID: 728_firmantes_portafirmas
Revises: 728_usuario_unidad_organo_id
Create Date: 2026-08-05

Issue #728 — Crea firmantes_portafirmas: catálogo de firmantes de escritos,
desacoplado de usuarios (usuario_id nullable). Ver ADR-039 §2.

Sin datos de partida: catálogo a rellenar por el Supervisor vía la futura
pantalla de mantenimiento.
"""
from alembic import op
import sqlalchemy as sa


revision = '728_firmantes_portafirmas'
down_revision = '728_usuario_unidad_organo_id'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'firmantes_portafirmas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cargo', sa.String(200), nullable=False,
                  comment='Cargo del firmante (p.ej. Delegado/a Territorial, Consejero/a)'),
        sa.Column('dni', sa.String(15), nullable=False,
                  comment='Documento de identidad del firmante. Campo de búsqueda principal en Port@firmas'),
        sa.Column('nombre', sa.String(200), nullable=False,
                  comment='Nombre completo del firmante'),
        sa.Column('unidad_organo_id', sa.Integer(), nullable=False,
                  comment='FK unidades_organo_propio. Unidad territorial del firmante'),
        sa.Column('vigente', sa.Boolean(), nullable=False, server_default='true',
                  comment='TRUE mientras ejerce el cargo. FALSE tras causar baja (histórico, no se elimina la fila)'),
        sa.Column('fecha_baja', sa.Date(), nullable=True,
                  comment='Fecha en la que dejó de ejercer el cargo. NULL mientras VIGENTE=True'),
        sa.Column('usuario_id', sa.Integer(), nullable=True,
                  comment='FK usuarios. Solo si el firmante también tiene cuenta BDDAT; no es requisito'),
        sa.PrimaryKeyConstraint('id', name='pk_firmantes_portafirmas'),
        sa.ForeignKeyConstraint(['unidad_organo_id'], ['public.unidades_organo_propio.id'],
                                name='fk_firmante_unidad_organo'),
        sa.ForeignKeyConstraint(['usuario_id'], ['public.usuarios.id'],
                                name='fk_firmante_usuario'),
        schema='public',
    )
    op.create_index('idx_firmante_portafirmas_dni', 'firmantes_portafirmas', ['dni'], schema='public')

    op.execute("GRANT SELECT ON public.firmantes_portafirmas TO claude_desktop")


def downgrade():
    op.drop_index('idx_firmante_portafirmas_dni', table_name='firmantes_portafirmas', schema='public')
    op.drop_table('firmantes_portafirmas', schema='public')
