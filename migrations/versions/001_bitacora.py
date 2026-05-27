"""001_bitacora

Revision ID: 001_bitacora
Revises: 323_configuracion_sistema
Create Date: 2026-05-25

Issue #1 — Tabla bitacora: cuaderno de bitácora agnóstico de operaciones.
"""
import sqlalchemy as sa
from alembic import op


revision = '001_bitacora'
down_revision = '323_configuracion_sistema'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'bitacora',
        sa.Column('id',          sa.Integer(),     primary_key=True),
        sa.Column('usuario_id',  sa.Integer(),     sa.ForeignKey('public.usuarios.id'), nullable=False),
        sa.Column('operacion',   sa.String(10),    nullable=False),
        sa.Column('tabla',       sa.String(60),    nullable=False),
        sa.Column('registro_id', sa.Integer(),     nullable=False),
        sa.Column('columna',     sa.String(60),    nullable=True),
        sa.Column('created_at',  sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('detalle',     sa.JSON(),        nullable=True),
        sa.CheckConstraint("operacion IN ('CREAR','BORRAR','ALTERAR')", name='ck_bitacora_operacion'),
        schema='public',
    )

    op.create_index('ix_bitacora_usuario_fecha', 'bitacora', ['usuario_id', 'created_at'], schema='public')
    op.create_index('ix_bitacora_tabla_registro', 'bitacora', ['tabla', 'registro_id'], schema='public')

    op.execute("GRANT SELECT ON public.bitacora TO claude_desktop")


def downgrade():
    op.drop_index('ix_bitacora_tabla_registro', table_name='bitacora', schema='public')
    op.drop_index('ix_bitacora_usuario_fecha', table_name='bitacora', schema='public')
    op.drop_table('bitacora', schema='public')
