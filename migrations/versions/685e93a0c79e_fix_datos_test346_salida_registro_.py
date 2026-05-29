"""fix datos test346 salida registro_interesados y test448 norma cierre

Revision ID: 685e93a0c79e
Revises: 6a2e29774f16
Create Date: 2026-05-29 19:28:57.545554

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '685e93a0c79e'
down_revision = '6a2e29774f16'
branch_labels = None
depends_on = None


def upgrade():
    # RD 88/2026 modifica el art. 138 RD 1955/2000 — actualizar cita en catálogo de plazos.
    op.execute("""
        UPDATE public.catalogo_plazos
        SET norma_origen = 'Art. 138 RD 1955/2000 (mod. RD 88/2026)'
        WHERE id = 111
          AND norma_origen = 'Art. 138 RD 1955/2000'
    """)


def downgrade():
    op.execute("""
        UPDATE public.catalogo_plazos
        SET norma_origen = 'Art. 138 RD 1955/2000'
        WHERE id = 111
    """)
