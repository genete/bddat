"""Crear tabla autorizados_titular

Revision ID: f6aa3dfeb81b
Revises: 8d33446946ff
Create Date: 2026-02-03 19:37:21.096223

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6aa3dfeb81b'
down_revision = '8d33446946ff'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla AUTORIZADOS_TITULAR en public (N:N entre entidades)
    op.create_table(
        'autorizados_titular',
        sa.Column('id', sa.Integer(), nullable=False, comment='Identificador único del registro de autorización'),
        sa.Column('titular_entidad_id', sa.Integer(), nullable=False, comment='Administrado titular que concede la autorización. Debe tener entrada en entidades_administrados'),
        sa.Column('autorizado_entidad_id', sa.Integer(), nullable=False, comment='Administrado autorizado para representar al titular. Debe tener entrada en entidades_administrados'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true', comment='Indica si la autorización está vigente. FALSE = revocada/suspendida'),
        sa.Column('observaciones', sa.Text(), nullable=True, comment='Notas libres del tramitador. Usos: ámbito (expediente específico/general), vigencia temporal, motivo desactivación, tipo de poder'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Fecha y hora de creación del registro'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Fecha y hora de última actualización'),
        sa.CheckConstraint(
            'titular_entidad_id != autorizado_entidad_id',
            name='chk_no_autoautorizacion'
        ),
        sa.ForeignKeyConstraint(['autorizado_entidad_id'], ['public.entidades.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['titular_entidad_id'], ['public.entidades.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('titular_entidad_id', 'autorizado_entidad_id', name='uq_titular_autorizado'),
        schema='public'
    )
    
    # Índices
    op.create_index('ix_public_autorizados_titular_titular_entidad_id', 'autorizados_titular', ['titular_entidad_id'], unique=False, schema='public')
    op.create_index('ix_public_autorizados_titular_autorizado_entidad_id', 'autorizados_titular', ['autorizado_entidad_id'], unique=False, schema='public')
    op.create_index('ix_public_autorizados_titular_activo', 'autorizados_titular', ['activo'], unique=False, schema='public')
    
    # Índice compuesto para queries frecuentes (autorizados activos de un titular)
    op.create_index('idx_titular_activo', 'autorizados_titular', ['titular_entidad_id', 'activo'], unique=False, schema='public')



def downgrade():
    # Borrar índices primero
    op.drop_index('idx_titular_activo', table_name='autorizados_titular', schema='public')
    op.drop_index('ix_public_autorizados_titular_activo', table_name='autorizados_titular', schema='public')
    op.drop_index('ix_public_autorizados_titular_autorizado_entidad_id', table_name='autorizados_titular', schema='public')
    op.drop_index('ix_public_autorizados_titular_titular_entidad_id', table_name='autorizados_titular', schema='public')
    
    # Borrar tabla
    op.drop_table('autorizados_titular', schema='public')
