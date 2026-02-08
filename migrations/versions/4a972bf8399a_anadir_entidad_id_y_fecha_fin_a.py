"""Añadir entidad_id y fecha_fin a solicitudes - Issue 65

Revision ID: 4a972bf8399a
Revises: 0d6742443660
Create Date: 2026-02-07 15:13:02.298254

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a972bf8399a'
down_revision = '0d6742443660'
branch_labels = None
depends_on = None


def upgrade():
    """
    MIGRACIÓN MANUAL LIMPIA - Issue #65
    
    SOLO añade campos entidad_id y fecha_fin a tabla solicitudes.
    
    NO toca FKs existentes (Alembic los detecta erróneamente como cambios).
    """
    # Añadir campos nuevos a solicitudes
    with op.batch_alter_table('solicitudes', schema='public') as batch_op:
        batch_op.add_column(
            sa.Column(
                'entidad_id', 
                sa.Integer(), 
                nullable=False, 
                comment='FK a ENTIDADES. Solicitante (promotor/titular) de la solicitud'
            )
        )
        batch_op.add_column(
            sa.Column(
                'fecha_fin', 
                sa.Date(), 
                nullable=True, 
                comment='Fecha real de finalización de la solicitud. NULL si aún en curso'
            )
        )
        
        # Crear índice para entidad_id
        batch_op.create_index('idx_solicitudes_entidad', ['entidad_id'], unique=False)
        
        # Crear FK para entidad_id
        batch_op.create_foreign_key(
            'fk_solicitudes_entidad', 
            'entidades', 
            ['entidad_id'], 
            ['id'], 
            referent_schema='public',
            use_alter=True
        )


def downgrade():
    """
    Revierte cambios: elimina entidad_id y fecha_fin de solicitudes.
    """
    with op.batch_alter_table('solicitudes', schema='public') as batch_op:
        batch_op.drop_constraint('fk_solicitudes_entidad', type_='foreignkey')
        batch_op.drop_index('idx_solicitudes_entidad')
        batch_op.drop_column('fecha_fin')
        batch_op.drop_column('entidad_id')
