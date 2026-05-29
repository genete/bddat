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
    # test_346: REGISTRO_INTERESADOS (tipo_tramite_id=31) le faltaba la fila SALIDA
    # en tramites_tareas_documentos. Mismo patrón que el resto de tareas ANALIZAR orden=1.
    op.execute("""
        INSERT INTO public.tramites_tareas_documentos
            (tipo_tramite_id, orden_tarea, rol, tipo_documento_id, obligatorio)
        VALUES (31, 1, 'SALIDA', 15, true)
        ON CONFLICT DO NOTHING
    """)

    # test_448: norma_origen de CIERRE en catalogo_plazos desactualizada.
    # RD 88/2026 modifica el art. 138 RD 1955/2000.
    op.execute("""
        UPDATE public.catalogo_plazos
        SET norma_origen = 'Art. 138 RD 1955/2000 (mod. RD 88/2026)'
        WHERE id = 111
          AND norma_origen = 'Art. 138 RD 1955/2000'
    """)


def downgrade():
    op.execute("""
        DELETE FROM public.tramites_tareas_documentos
        WHERE tipo_tramite_id = 31 AND orden_tarea = 1 AND rol = 'SALIDA'
    """)
    op.execute("""
        UPDATE public.catalogo_plazos
        SET norma_origen = 'Art. 138 RD 1955/2000'
        WHERE id = 111
    """)
