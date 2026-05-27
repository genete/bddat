"""reglas_motor: añadir descripcion para mensajes de bloqueo legibles

Revision ID: 319_descripcion_regla_motor
Revises: e40ce8475305
Create Date: 2026-04-24 16:56:00.916958

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '319_descripcion_regla_motor'
down_revision = 'e40ce8475305'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reglas_motor',
        sa.Column('descripcion', sa.String(500), nullable=True,
                  comment='Explicación en lenguaje natural para el usuario al bloquear'),
        schema='public'
    )
    # Descripciones iniciales para las 2 reglas existentes
    op.execute("""
        UPDATE public.reglas_motor
        SET descripcion = 'Para crear la fase Resolución es necesario que exista una fase de Información Pública finalizada.'
        WHERE accion = 'CREAR' AND sujeto = 'ANY/AAP/RESOLUCION'
    """)
    op.execute("""
        UPDATE public.reglas_motor
        SET descripcion = 'Para finalizar la fase Resolución es necesario que exista el trámite de Publicación.'
        WHERE accion = 'FINALIZAR' AND sujeto = 'ANY/AAP/RESOLUCION'
    """)


def downgrade():
    op.drop_column('reglas_motor', 'descripcion', schema='public')
