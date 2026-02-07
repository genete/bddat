"""Add historico_titulares_expediente table

Revision ID: bf66f512eaf4
Revises: 0f6a72b443e5
Create Date: 2026-02-07 07:35:39.337359

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'bf66f512eaf4'
down_revision = '0f6a72b443e5'
branch_labels = None
depends_on = None

def upgrade():
    """
    Crea tabla historico_titulares_expediente para registrar cambios de titularidad.
    
    IMPORTANTE: Esta es una migración MANUAL.
    Alembic genera automáticamente operaciones de drop/create de todas las FKs
    existentes debido a un bug conocido con include_schemas. Esas operaciones
    han sido ELIMINADAS de esta migración.
    
    Solo se incluye:
    - CREATE TABLE historico_titulares_expediente
    - CREATE INDEX (3 índices)
    
    Ref: Issue #64
    """
    # Crear tabla historico_titulares_expediente
    op.create_table(
        'historico_titulares_expediente',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, 
                  comment='Identificador técnico único autogenerado'),
        sa.Column('expediente_id', sa.Integer(), nullable=False, 
                  comment='FK a EXPEDIENTES. Expediente cuya titularidad cambia'),
        sa.Column('titular_id', sa.Integer(), nullable=False, 
                  comment='FK a ENTIDADES. Titular durante este periodo de vigencia'),
        sa.Column('fecha_desde', sa.Date(), nullable=False, 
                  comment='Fecha inicio vigencia de este titular. Para registro INICIAL = fecha creación expediente'),
        sa.Column('fecha_hasta', sa.Date(), nullable=True, 
                  comment='Fecha fin vigencia. NULL = titular actual vigente. NOT NULL = titular histórico'),
        sa.Column('solicitud_cambio_id', sa.Integer(), nullable=True, 
                  comment='FK a SOLICITUDES. Solicitud que motivó el cambio de titularidad. NULL para registro INICIAL'),
        sa.Column('motivo', sa.String(length=50), nullable=True, 
                  comment='Motivo del cambio: INICIAL, VENTA, HERENCIA, FUSION, ESCISION, OTRO'),
        sa.Column('observaciones', sa.Text(), nullable=True, 
                  comment='Observaciones adicionales sobre el cambio de titularidad'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False, 
                  comment='Timestamp de creación del registro (auditoría)'),
        
        # Constraints
        sa.CheckConstraint(
            'fecha_hasta IS NULL OR fecha_hasta >= fecha_desde', 
            name='chk_vigencia_titular'
        ),
        sa.ForeignKeyConstraint(
            ['expediente_id'], 
            ['public.expedientes.id'], 
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['solicitud_cambio_id'], 
            ['public.solicitudes.id']
        ),
        sa.ForeignKeyConstraint(
            ['titular_id'], 
            ['public.entidades.id']
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'expediente_id', 'fecha_desde', 
            name='uq_expediente_titular_desde'
        ),
        schema='public'
    )
    
    # Crear índices
    with op.batch_alter_table('historico_titulares_expediente', schema='public') as batch_op:
        batch_op.create_index(
            'idx_historico_titular_expediente', 
            ['expediente_id'], 
            unique=False
        )
        batch_op.create_index(
            'idx_historico_titular_titular', 
            ['titular_id'], 
            unique=False
        )
        batch_op.create_index(
            'idx_historico_titular_vigencia', 
            ['fecha_hasta'], 
            unique=False
        )

def downgrade():
    """
    Elimina tabla historico_titulares_expediente.
    
    Los índices se eliminan automáticamente con DROP TABLE CASCADE.
    """
    # Eliminar índices primero (aunque DROP TABLE los eliminaría)
    with op.batch_alter_table('historico_titulares_expediente', schema='public') as batch_op:
        batch_op.drop_index('idx_historico_titular_vigencia')
        batch_op.drop_index('idx_historico_titular_titular')
        batch_op.drop_index('idx_historico_titular_expediente')
    
    # Eliminar tabla
    op.drop_table('historico_titulares_expediente', schema='public')
