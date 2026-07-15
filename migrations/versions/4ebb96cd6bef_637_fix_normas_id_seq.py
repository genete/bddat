"""637_fix_normas_id_seq

Revision ID: 4ebb96cd6bef
Revises: b4417076e504
Create Date: 2026-07-15 14:43:21.064792

Issue #637 — `normas_id_seq` quedó desincronizada: varias migraciones de seed
(348_seed_normas_base, 451_seed_normas_ampliacion, 07948f0f5f2c_582) insertan
`id` explícito en `normas` sin avanzar la secuencia. Detectado al construir el
alta de Norma (#637): la secuencia estaba en 8 con filas ya hasta id=12 —
cualquier INSERT sin id explícito (incluido el nuevo CRUD) colisionaba con una
fila existente. Resincroniza al máximo id real; sin baja con efecto (no tiene
inverso significativo, downgrade es no-op).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4ebb96cd6bef'
down_revision = 'b4417076e504'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        SELECT setval('public.normas_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.normas))
    """)


def downgrade():
    pass
