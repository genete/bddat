"""393_alegantes

Revision ID: 393_alegantes
Revises: 392_diagnosticos
Create Date: 2026-05-15

Issue #393 — Crea la tabla alegantes para almacenar el alegante de cada
trámite RECEPCION_ALEGACION, con referencia opcional a la tabla entidades.
"""
from alembic import op
import sqlalchemy as sa

revision = '393_alegantes'
down_revision = '392_diagnosticos'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'alegantes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tramite_id', sa.Integer(), nullable=False,
                  comment='FK tramites. Trámite RECEPCION_ALEGACION al que pertenece'),
        sa.Column('entidad_id', sa.Integer(), nullable=True,
                  comment='FK entidades. Relleno si el alegante ya existe como entidad del sistema'),
        sa.Column('nombre', sa.String(255), nullable=True,
                  comment='Nombre del alegante cuando entidad_id es NULL'),
        sa.Column('nif', sa.String(20), nullable=True,
                  comment='NIF del alegante cuando entidad_id es NULL'),
        sa.Column('tipo_interesado', sa.String(50), nullable=False,
                  comment='Tipo de interesado: particular, administracion, asociacion, empresa'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tramite_id', name='uq_alegante_tramite'),
        sa.CheckConstraint(
            "tipo_interesado IN ('particular', 'administracion', 'asociacion', 'empresa')",
            name='ck_alegante_tipo_interesado',
        ),
        sa.ForeignKeyConstraint(
            ['tramite_id'], ['public.tramites.id'],
            name='fk_alegante_tramite', ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['entidad_id'], ['public.entidades.id'],
            name='fk_alegante_entidad',
        ),
        schema='public',
    )

    op.execute("GRANT SELECT ON public.alegantes TO claude_desktop")


def downgrade():
    op.drop_table('alegantes', schema='public')
