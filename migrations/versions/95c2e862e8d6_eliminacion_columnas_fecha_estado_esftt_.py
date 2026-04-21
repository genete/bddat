"""eliminacion columnas fecha estado ESFTT paso9

Revision ID: 95c2e862e8d6
Revises: b7f95d61a7a9
Create Date: 2026-04-20 14:38:14.450807

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '95c2e862e8d6'
down_revision = 'b7f95d61a7a9'
branch_labels = None
depends_on = None


def upgrade():
    # Solicitudes
    op.drop_index('idx_solicitudes_fecha', table_name='solicitudes', schema='public')
    op.drop_index('idx_solicitudes_estado', table_name='solicitudes', schema='public')
    op.drop_column('solicitudes', 'fecha_solicitud', schema='public')
    op.drop_column('solicitudes', 'fecha_fin', schema='public')
    op.drop_column('solicitudes', 'estado', schema='public')

    # Fases
    op.drop_index('idx_fases_fechas', table_name='fases', schema='public')
    op.drop_column('fases', 'fecha_inicio', schema='public')
    op.drop_column('fases', 'fecha_fin', schema='public')

    # Tramites
    op.drop_index('idx_tramites_fechas', table_name='tramites', schema='public')
    op.drop_column('tramites', 'fecha_inicio', schema='public')
    op.drop_column('tramites', 'fecha_fin', schema='public')

    # Tareas
    op.drop_index('idx_tareas_fechas', table_name='tareas', schema='public')
    op.drop_column('tareas', 'fecha_inicio', schema='public')
    op.drop_column('tareas', 'fecha_fin', schema='public')


def downgrade():
    # Tareas
    op.add_column('tareas', sa.Column('fecha_fin',    sa.Date(), nullable=True), schema='public')
    op.add_column('tareas', sa.Column('fecha_inicio', sa.Date(), nullable=True), schema='public')
    op.create_index('idx_tareas_fechas', 'tareas', ['fecha_inicio', 'fecha_fin'], schema='public')

    # Tramites
    op.add_column('tramites', sa.Column('fecha_fin',    sa.Date(), nullable=True), schema='public')
    op.add_column('tramites', sa.Column('fecha_inicio', sa.Date(), nullable=True), schema='public')
    op.create_index('idx_tramites_fechas', 'tramites', ['fecha_inicio', 'fecha_fin'], schema='public')

    # Fases
    op.add_column('fases', sa.Column('fecha_fin',    sa.Date(), nullable=True), schema='public')
    op.add_column('fases', sa.Column('fecha_inicio', sa.Date(), nullable=True), schema='public')
    op.create_index('idx_fases_fechas', 'fases', ['fecha_inicio', 'fecha_fin'], schema='public')

    # Solicitudes (sin datos — recuperación de emergencia)
    op.add_column('solicitudes', sa.Column('estado',          sa.String(20), nullable=True), schema='public')
    op.add_column('solicitudes', sa.Column('fecha_fin',       sa.Date(),     nullable=True), schema='public')
    op.add_column('solicitudes', sa.Column('fecha_solicitud', sa.Date(),     nullable=True), schema='public')
    op.create_index('idx_solicitudes_estado', 'solicitudes', ['estado'],          schema='public')
    op.create_index('idx_solicitudes_fecha',  'solicitudes', ['fecha_solicitud'], schema='public')
