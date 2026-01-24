"""Mover solicitudes_tipos de estructura a public

Revision ID: 2026_01_24_1053
Revises: 
Create Date: 2026-01-24 10:53:00.000000

CORRECCIÓN ISSUE #21:
    La tabla solicitudes_tipos estaba erróneamente en schema 'estructura'.
    Es una tabla OPERACIONAL (datos de instancias), no maestra (catálogos).
    Esta migración la mueve a schema 'public' donde pertenece.

PROCESO:
    1. Crear tabla en public con estructura idéntica
    2. Copiar datos existentes (si hay)
    3. Recrear foreign keys con CASCADE correcto
    4. Recrear índices
    5. Eliminar tabla antigua en estructura

REVERSIÓN:
    downgrade() revierte el proceso completamente
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2026_01_24_1053'
down_revision = None  # NOTA: Usuario debe ajustar esto al último revision ID existente
branch_labels = None
depends_on = None


def upgrade():
    """
    Mover solicitudes_tipos de schema 'estructura' a schema 'public'.
    """
    # 1. Crear tabla en public con estructura completa
    op.create_table(
        'solicitudes_tipos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False,
                 comment='Identificador único autogenerado del registro puente'),
        sa.Column('solicitudid', sa.Integer(), nullable=False,
                 comment='FK a SOLICITUDES. Solicitud que contiene este tipo'),
        sa.Column('tiposolicitudid', sa.Integer(), nullable=False,
                 comment='FK a TIPOS_SOLICITUDES. Tipo individual asignado a la solicitud'),
        sa.PrimaryKeyConstraint('id', name='solicitudes_tipos_pkey'),
        sa.UniqueConstraint('solicitudid', 'tiposolicitudid',
                           name='solicitudes_tipos_solicitudid_tiposolicitudid_key'),
        schema='public',
        comment='Tabla puente que relaciona solicitudes con sus tipos individuales. '
                'Una solicitud puede tener múltiples tipos (AAP+AAC+DUP → 3 registros). '
                'Permite motor de reglas basado en tipos individuales sin duplicación de lógica.'
    )
    
    # 2. Copiar datos existentes de estructura a public (si existen)
    op.execute("""
        INSERT INTO public.solicitudes_tipos (id, solicitudid, tiposolicitudid)
        SELECT id, solicitudid, tiposolicitudid
        FROM estructura.solicitudes_tipos
        ORDER BY id
    """)
    
    # 3. Ajustar secuencia de autoincremento al valor correcto
    op.execute("""
        SELECT setval('public.solicitudes_tipos_id_seq', 
                      COALESCE((SELECT MAX(id) FROM public.solicitudes_tipos), 0) + 1, 
                      false)
    """)
    
    # 4. Crear foreign keys con DELETE CASCADE correcto
    op.create_foreign_key(
        'fk_solicitudes_tipos_solicitud',
        'solicitudes_tipos', 'solicitudes',
        ['solicitudid'], ['id'],
        source_schema='public',
        referent_schema='public',
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_solicitudes_tipos_tipo',
        'solicitudes_tipos', 'tipos_solicitudes',
        ['tiposolicitudid'], ['id'],
        source_schema='public',
        referent_schema='estructura'
    )
    
    # 5. Recrear índices para optimización
    op.create_index(
        'idx_solicitudes_tipos_solicitud',
        'solicitudes_tipos',
        ['solicitudid'],
        schema='public'
    )
    
    op.create_index(
        'idx_solicitudes_tipos_tipo',
        'solicitudes_tipos',
        ['tiposolicitudid'],
        schema='public'
    )
    
    # 6. Eliminar tabla antigua en estructura
    op.drop_table('solicitudes_tipos', schema='estructura')


def downgrade():
    """
    Revertir: Mover solicitudes_tipos de public de vuelta a estructura.
    """
    # 1. Crear tabla en estructura
    op.create_table(
        'solicitudes_tipos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('solicitudid', sa.Integer(), nullable=False),
        sa.Column('tiposolicitudid', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='solicitudes_tipos_pkey'),
        sa.UniqueConstraint('solicitudid', 'tiposolicitudid',
                           name='solicitudes_tipos_solicitudid_tiposolicitudid_key'),
        schema='estructura'
    )
    
    # 2. Copiar datos de public a estructura
    op.execute("""
        INSERT INTO estructura.solicitudes_tipos (id, solicitudid, tiposolicitudid)
        SELECT id, solicitudid, tiposolicitudid
        FROM public.solicitudes_tipos
        ORDER BY id
    """)
    
    # 3. Ajustar secuencia
    op.execute("""
        SELECT setval('estructura.solicitudes_tipos_id_seq', 
                      COALESCE((SELECT MAX(id) FROM estructura.solicitudes_tipos), 0) + 1, 
                      false)
    """)
    
    # 4. Recrear FKs antiguas (sin ondelete CASCADE explícito en solicitud)
    op.create_foreign_key(
        None,  # Sin nombre explícito, deja que Alembic genere
        'solicitudes_tipos', 'solicitudes',
        ['solicitudid'], ['id'],
        source_schema='estructura',
        referent_schema='public',
        use_alter=True  # Como estaba antes
    )
    
    op.create_foreign_key(
        None,
        'solicitudes_tipos', 'tipos_solicitudes',
        ['tiposolicitudid'], ['id'],
        source_schema='estructura',
        referent_schema='estructura'
    )
    
    # 5. Recrear índices
    op.create_index(
        'idx_solicitudes_tipos_solicitud',
        'solicitudes_tipos',
        ['solicitudid'],
        schema='estructura'
    )
    
    op.create_index(
        'idx_solicitudes_tipos_tipo',
        'solicitudes_tipos',
        ['tiposolicitudid'],
        schema='estructura'
    )
    
    # 6. Eliminar tabla en public
    op.drop_table('solicitudes_tipos', schema='public')
