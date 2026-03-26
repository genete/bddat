"""eliminar fase ADMISION_TRAMITE y tramites ANALISIS_ADMISION ALEGACIONES

Revision ID: d65a957ade7d
Revises: c3d4e5f6a7b8
Create Date: 2026-03-26 19:51:10.167762

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd65a957ade7d'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    # Eliminar pares fases_tramites de ADMISION_TRAMITE (por codigo, no por id)
    op.execute("""
        DELETE FROM public.fases_tramites
        WHERE tipo_fase_id = (
            SELECT id FROM public.tipos_fases WHERE codigo = 'ADMISION_TRAMITE'
        )
    """)
    # Eliminar trámites propios (ANALISIS_ADMISION, ALEGACIONES)
    op.execute("""
        DELETE FROM public.tipos_tramites
        WHERE codigo IN ('ANALISIS_ADMISION', 'ALEGACIONES')
    """)
    # Eliminar la fase
    op.execute("""
        DELETE FROM public.tipos_fases WHERE codigo = 'ADMISION_TRAMITE'
    """)


def downgrade():
    # Restaurar tipos_tramites
    op.execute("""
        INSERT INTO public.tipos_tramites (codigo, nombre) VALUES
        ('ANALISIS_ADMISION', 'Análisis de Admisión a Trámite'),
        ('ALEGACIONES', 'Alegaciones a Admisión')
    """)
    # Restaurar tipos_fases
    op.execute("""
        INSERT INTO public.tipos_fases (codigo, nombre)
        VALUES ('ADMISION_TRAMITE', 'Admisión a Trámite')
    """)
    # Restaurar pares fases_tramites
    op.execute("""
        INSERT INTO public.fases_tramites (tipo_fase_id, tipo_tramite_id)
        SELECT f.id, t.id
        FROM public.tipos_fases f, public.tipos_tramites t
        WHERE f.codigo = 'ADMISION_TRAMITE'
          AND t.codigo IN ('ANALISIS_ADMISION', 'ALEGACIONES')
    """)
