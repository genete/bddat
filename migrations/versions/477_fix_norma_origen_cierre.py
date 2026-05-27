"""477_fix_norma_origen_cierre

Revision ID: 477_fix_norma_origen_cierre
Revises: 451_seed_normas_ampliacion
Create Date: 2026-05-25

Corrige norma_origen en catalogo_plazos para RESOLUCION_CIERRE.

RD 88/2026 solo modifica art. 137 RD 1955/2000 (informe del operador del
sistema). El art. 138 (resolución del cierre) no fue modificado por RD 88/2026
ni renumerado. La migración 448 insertó erróneamente el calificador
"(mod. RD 88/2026)" en la base legal de CIERRE (id=111).
"""
from alembic import op


revision = '477_fix_norma_origen_cierre'
down_revision = '451_seed_normas_ampliacion'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        UPDATE public.catalogo_plazos
        SET norma_origen = 'Art. 138 RD 1955/2000'
        WHERE id = 111
          AND norma_origen = 'Art. 138 RD 1955/2000 (mod. RD 88/2026)'
    """)


def downgrade():
    op.execute("""
        UPDATE public.catalogo_plazos
        SET norma_origen = 'Art. 138 RD 1955/2000 (mod. RD 88/2026)'
        WHERE id = 111
          AND norma_origen = 'Art. 138 RD 1955/2000'
    """)
