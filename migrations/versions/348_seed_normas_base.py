"""seed_normas_base — normas RD1955/2000 y D9/2011

Revision ID: seed_normas_base
Revises:
Create Date: 2026-05-07

Rama paralela (down_revision=None, depends_on='a9cd38df8797').
a9cd38df8797 crea la tabla normas sin seed; esta migración la puebla.
No puede formar parte de seed_catalogo_base porque la tabla normas no existe
cuando corre seed_catalogo_base (a9cd38df8797 es posterior a dfdeb43518d6).
"""
from alembic import op


revision = 'seed_normas_base'
down_revision = None
branch_labels = None
depends_on = 'a9cd38df8797'


def upgrade():
    op.execute("""
        INSERT INTO public.normas (id, codigo, titulo, url_eli) VALUES
        (3, 'RD1955_2000', 'Real Decreto 1955/2000, de 1 de diciembre',           NULL),
        (4, 'D9_2011',     'Decreto 9/2011, de 26 de enero (Junta de Andalucía)', NULL)
        ON CONFLICT (codigo) DO NOTHING
    """)


def downgrade():
    op.execute("DELETE FROM public.normas WHERE id IN (3, 4)")
