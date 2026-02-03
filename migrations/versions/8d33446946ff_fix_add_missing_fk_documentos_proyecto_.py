"""fix_add_missing_fk_documentos_proyecto_proyecto

Revision ID: 8d33446946ff
Revises: c21871f08bb2
Create Date: 2026-02-03 18:06:18.255340
Corrige bug en migración inicial donde use_alter=True no creó
la FK fk_documentos_proyecto_proyecto en PostgreSQL.

Esta migración añade explícitamente la constraint faltante.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d33446946ff'
down_revision = 'c21871f08bb2'
branch_labels = None
depends_on = None


def upgrade():
    # Verificar si la FK ya existe antes de crearla (idempotente)
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT COUNT(*) 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_documentos_proyecto_proyecto'
          AND table_schema = 'public'
          AND table_name = 'documentos_proyecto'
    """))
    
    if result.scalar() == 0:
        op.create_foreign_key(
            'fk_documentos_proyecto_proyecto',
            'documentos_proyecto', 'proyectos',
            ['proyecto_id'], ['id'],
            source_schema='public', referent_schema='public',
            ondelete='CASCADE'
        )


def downgrade():
    op.drop_constraint(
        'fk_documentos_proyecto_proyecto',
        'documentos_proyecto',
        schema='public',
        type_='foreignkey'
    )