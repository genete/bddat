"""728_usuario_unidad_organo_id

Revision ID: 728_usuario_unidad_organo_id
Revises: 728_unidades_organo_propio
Create Date: 2026-08-05

Issue #728 — Añade usuarios.unidad_organo_id (FK a unidades_organo_propio,
nullable). Resuelve la unidad territorial por usuario, no por instancia
global ni por expediente: el destino real usado al enviar a Port@firmas es
el puesto del usuario que envía (ADR-039 §1). Nullable hasta que se asigne
manualmente a cada usuario — no se puebla en esta migración.

No requiere GRANT nuevo: usuarios ya tiene GRANT SELECT a nivel de tabla
para claude_desktop, que cubre columnas añadidas.
"""
from alembic import op
import sqlalchemy as sa


revision = '728_usuario_unidad_organo_id'
down_revision = '728_unidades_organo_propio'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'usuarios',
        sa.Column('unidad_organo_id', sa.Integer(), nullable=True,
                  comment='FK unidades_organo_propio. Unidad territorial (provincia) desde la que tramita este usuario'),
        schema='public',
    )
    op.create_foreign_key(
        'fk_usuario_unidad_organo', 'usuarios', 'unidades_organo_propio',
        ['unidad_organo_id'], ['id'],
        source_schema='public', referent_schema='public',
    )


def downgrade():
    op.drop_constraint('fk_usuario_unidad_organo', 'usuarios', schema='public', type_='foreignkey')
    op.drop_column('usuarios', 'unidad_organo_id', schema='public')
