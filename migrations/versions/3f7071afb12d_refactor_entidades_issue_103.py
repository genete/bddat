"""refactor entidades issue 103

Revision ID: 3f7071afb12d
Revises: 4a972bf8399a
Create Date: 2026-02-11 17:54:10.236751

CAMBIOS:
- DROP tablas obsoletas: tipos_entidades, entidades_* (administrados, empresas, organismos, ayuntamientos, diputaciones)
- ALTER entidades: DROP tipo_entidad_id, RENAME cif_nif → nif, ADD roles booleanos
- CREATE direcciones_notificacion con bit flags de roles
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3f7071afb12d'
down_revision = '4a972bf8399a'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================
    # PASO 1: DROP TABLAS OBSOLETAS (en orden de dependencias)
    # ========================================
    
    # Tablas de metadatos de entidades (dependen de entidades)
    op.drop_table('entidades_administrados')
    op.drop_table('entidades_empresas_servicio_publico')
    op.drop_table('entidades_organismos_publicos')
    op.drop_table('entidades_ayuntamientos')
    op.drop_table('entidades_diputaciones')
    
    # Tabla de tipos (no tiene dependencias hacia arriba)
    op.drop_table('tipos_entidades')
    
    # ========================================
    # PASO 2: MODIFICAR TABLA ENTIDADES
    # ========================================
    
    with op.batch_alter_table('entidades', schema=None) as batch_op:
        # Eliminar FK y columna tipo_entidad_id
        batch_op.drop_constraint('entidades_tipo_entidad_id_fkey', type_='foreignkey')
        batch_op.drop_column('tipo_entidad_id')
        
        # Renombrar cif_nif → nif
        batch_op.alter_column('cif_nif', new_column_name='nif')
        
        # Añadir columnas de roles booleanos
        batch_op.add_column(sa.Column('rol_titular', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('rol_consultado', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('rol_publicador', sa.Boolean(), nullable=False, server_default='false'))
        
        # Añadir constraint: al menos un rol activo
        batch_op.create_check_constraint(
            'chk_al_menos_un_rol',
            'rol_titular OR rol_consultado OR rol_publicador'
        )
    
    # ========================================
    # PASO 3: CREAR TABLA DIRECCIONES_NOTIFICACION
    # ========================================
    
    op.create_table(
        'direcciones_notificacion',
        # Identificación
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entidad_id', sa.Integer(), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        
        # Bit flags de roles (1=TITULAR, 2=CONSULTADO, 4=PUBLICADOR)
        sa.Column('tipo_rol', sa.SmallInteger(), nullable=False),
        
        # Canales digitales
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('telefono', sa.String(length=20), nullable=True),
        sa.Column('codigo_sir', sa.String(length=50), nullable=True),
        sa.Column('codigo_dir3', sa.String(length=20), nullable=True),
        
        # Dirección postal (campos separados)
        sa.Column('direccion', sa.Text(), nullable=True),
        sa.Column('codigo_postal', sa.String(length=10), nullable=True),
        sa.Column('municipio_id', sa.Integer(), nullable=True),
        sa.Column('direccion_fallback', sa.Text(), nullable=True),
        
        # Identificación fiscal
        sa.Column('nif', sa.String(length=20), nullable=True),
        
        # Documento soporte
        sa.Column('documento_autorizacion_id', sa.Integer(), nullable=True),
        
        # Control temporal
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('fecha_inicio', sa.Date(), nullable=True, server_default=sa.text('CURRENT_DATE')),
        sa.Column('fecha_fin', sa.Date(), nullable=True),
        sa.Column('notas', sa.Text(), nullable=True),
        
        # Auditoría
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        
        # Constraints
        sa.CheckConstraint('tipo_rol BETWEEN 1 AND 7', name='chk_tipo_rol_valido'),
        sa.CheckConstraint(
            'email IS NOT NULL OR codigo_sir IS NOT NULL OR codigo_dir3 IS NOT NULL OR direccion IS NOT NULL',
            name='chk_al_menos_un_canal'
        ),
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign Keys
        sa.ForeignKeyConstraint(['entidad_id'], ['entidades.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id']),
        sa.ForeignKeyConstraint(['documento_autorizacion_id'], ['documentos.id'], ondelete='SET NULL'),
        
        schema=None
    )
    
    # Crear índices
    op.create_index(op.f('ix_direcciones_notificacion_entidad_id'), 'direcciones_notificacion', ['entidad_id'], unique=False)
    op.create_index(op.f('ix_direcciones_notificacion_tipo_rol'), 'direcciones_notificacion', ['tipo_rol'], unique=False)
    op.create_index(op.f('ix_direcciones_notificacion_activo'), 'direcciones_notificacion', ['activo'], unique=False)


def downgrade():
    # ========================================
    # REVERSO: ELIMINAR CAMBIOS EN ORDEN INVERSO
    # ========================================
    
    # PASO 3 REVERSO: DROP tabla direcciones_notificacion
    op.drop_index(op.f('ix_direcciones_notificacion_activo'), table_name='direcciones_notificacion')
    op.drop_index(op.f('ix_direcciones_notificacion_tipo_rol'), table_name='direcciones_notificacion')
    op.drop_index(op.f('ix_direcciones_notificacion_entidad_id'), table_name='direcciones_notificacion')
    op.drop_table('direcciones_notificacion')
    
    # PASO 2 REVERSO: Revertir cambios en entidades
    with op.batch_alter_table('entidades', schema=None) as batch_op:
        # Eliminar constraint y columnas de roles
        batch_op.drop_constraint('chk_al_menos_un_rol', type_='check')
        batch_op.drop_column('rol_publicador')
        batch_op.drop_column('rol_consultado')
        batch_op.drop_column('rol_titular')
        
        # Renombrar nif → cif_nif
        batch_op.alter_column('nif', new_column_name='cif_nif')
        
        # Restaurar tipo_entidad_id (requiere recrear tabla tipos_entidades primero)
    
    # PASO 1 REVERSO: Recrear tabla tipos_entidades
    op.create_table(
        'tipos_entidades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('tabla_metadatos', sa.String(length=100), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('orden', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo')
    )
    
    # Recrear FK en entidades
    with op.batch_alter_table('entidades', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tipo_entidad_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('entidades_tipo_entidad_id_fkey', 'tipos_entidades', ['tipo_entidad_id'], ['id'])
    
    # Recrear tablas de metadatos (NOTA: Datos se perderán)
    op.create_table(
        'entidades_administrados',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entidad_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entidad_id'], ['entidades.id'], ondelete='CASCADE')
    )
    
    op.create_table(
        'entidades_empresas_servicio_publico',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entidad_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entidad_id'], ['entidades.id'], ondelete='CASCADE')
    )
    
    op.create_table(
        'entidades_organismos_publicos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entidad_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entidad_id'], ['entidades.id'], ondelete='CASCADE')
    )
    
    op.create_table(
        'entidades_ayuntamientos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entidad_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entidad_id'], ['entidades.id'], ondelete='CASCADE')
    )
    
    op.create_table(
        'entidades_diputaciones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entidad_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entidad_id'], ['entidades.id'], ondelete='CASCADE')
    )
