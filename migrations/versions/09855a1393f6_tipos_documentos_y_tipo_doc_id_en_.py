"""tipos_documentos y tipo_doc_id en Documento

Revision ID: 09855a1393f6
Revises: 0869cda75380
Create Date: 2026-03-04 18:16:16.921554

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '09855a1393f6'
down_revision = '0869cda75380'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Crear tabla maestra de tipos de documentos
    op.create_table(
        'tipos_documentos',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('codigo', sa.Text(), nullable=False),
        sa.Column('nombre', sa.Text(), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.UniqueConstraint('codigo', name='uq_tipos_documentos_codigo'),
        schema='public'
    )

    # 2. Datos iniciales mínimos (OTROS id=1 es el server_default de documentos)
    op.execute("""
        INSERT INTO public.tipos_documentos (codigo, nombre, descripcion) VALUES
        ('OTROS',     'Otros / Sin clasificar',
         'Cajón de sastre para documentos sin tipo semántico definido'),
        ('DR_NO_DUP', 'Declaración Responsable de No Duplicidad',
         'Requerida para iniciar la fase de Información Pública (salvo AAU/AAUS)')
    """)

    # 3. Añadir FK en documentos (tabla vacía → NOT NULL directo)
    op.add_column(
        'documentos',
        sa.Column(
            'tipo_doc_id',
            sa.Integer(),
            nullable=False,
            server_default='1',
            comment='FK a TIPOS_DOCUMENTOS. Tipo semántico de negocio del documento'
        ),
        schema='public'
    )
    op.create_foreign_key(
        'fk_documentos_tipo_doc',
        'documentos', 'tipos_documentos',
        ['tipo_doc_id'], ['id'],
        source_schema='public', referent_schema='public'
    )
    op.create_index('idx_documentos_tipo_doc', 'documentos', ['tipo_doc_id'], schema='public')


def downgrade():
    op.drop_index('idx_documentos_tipo_doc', table_name='documentos', schema='public')
    op.drop_constraint('fk_documentos_tipo_doc', 'documentos', schema='public', type_='foreignkey')
    op.drop_column('documentos', 'tipo_doc_id', schema='public')
    op.drop_table('tipos_documentos', schema='public')
