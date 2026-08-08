"""585_baja_tabla_metadata

Revision ID: 585_baja_tabla_metadata
Revises: 28_mensajes_internos
Create Date: 2026-08-08

Issue #585 — Baja de public.tabla_metadata, el primer intento de control de
acceso (#85): permisos de lectura/escritura/borrado por tabla y por rol.

Nunca tuvo consumidores en el código y su premisa contradice ADR-013 (la
visibilidad no se restringe por rol). El modelo TablaMetadata se eliminó en el
commit anterior; aquí cae la tabla.

La tabla estaba vacía (0 filas) al aplicar esta migración: no hay dato que
migrar ni que preservar. El downgrade la recrea con la estructura vigente —la
que dejó 0f6a72b443e5 (#85 fase 2), no la de la creación original—, pero
lógicamente vacía.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '585_baja_tabla_metadata'
down_revision = '28_mensajes_internos'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index('ix_public_tabla_metadata_nombre_tabla',
                  table_name='tabla_metadata', schema='public')
    op.drop_table('tabla_metadata', schema='public')


def downgrade():
    op.create_table(
        'tabla_metadata',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nombre_tabla', sa.String(length=100), nullable=False),
        sa.Column('roles_lectura', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('roles_escritura', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('roles_eliminacion', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('categoria', sa.String(length=50), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
        sa.Column('ultima_modificacion', sa.DateTime(), nullable=False),
        sa.CheckConstraint("nombre_tabla IS NOT NULL AND TRIM(nombre_tabla) != ''",
                           name='chk_nombre_tabla_not_empty'),
        sa.PrimaryKeyConstraint('id'),
        schema='public',
    )
    op.create_index('ix_public_tabla_metadata_nombre_tabla', 'tabla_metadata',
                    ['nombre_tabla'], unique=True, schema='public')
    op.execute("GRANT SELECT ON public.tabla_metadata TO claude_desktop")
