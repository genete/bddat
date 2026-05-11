"""370_actualizar_tipos_tramites — nuevos trámites AAU_AAUS + IP

Revision ID: 370_actualizar_tipos_tramites
Revises: 370_actualizar_tipos_tareas
Create Date: 2026-05-11

Issue #370 — Actualización de tipos_tramites:
- #372: REMISION_MEDIO_AMBIENTE renombrado a REMISION_RESULTADO_IP_CONSULTAS
         + 3 nuevos trámites AAU_AAUS_INTEGRADA
- #368: REDACTAR_ANUNCIO + ANUNCIO_BOJA (nuevos trámites INFORMACION_PUBLICA)
- #369: ANUNCIO_TITULAR (notificación al titular sobre publicación IP)
"""
from alembic import op
import sqlalchemy as sa


revision = '370_actualizar_tipos_tramites'
down_revision = '370_actualizar_tipos_tareas'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Renombrar REMISION_MEDIO_AMBIENTE (#372)
    conn.execute(sa.text("""
        UPDATE public.tipos_tramites
           SET codigo = 'REMISION_RESULTADO_IP_CONSULTAS',
               nombre = 'Remisión del resultado de IP y consultas a Medio Ambiente'
         WHERE codigo = 'REMISION_MEDIO_AMBIENTE'
    """))

    # Nuevos trámites AAU_AAUS_INTEGRADA (#372)
    conn.execute(sa.text("""
        INSERT INTO public.tipos_tramites (codigo, nombre) VALUES
          ('RECEPCION_PROPUESTA_INF_VINC', 'Recepción de Propuesta de Informe Vinculante'),
          ('RECEPCION_INFORME_VINCULANTE', 'Recepción de Informe Vinculante'),
          ('DISCREPANCIA_INF_VINC',        'Discrepancia con Informe Vinculante')
        ON CONFLICT (codigo) DO NOTHING
    """))

    # Nuevos trámites INFORMACION_PUBLICA (#368, #369)
    conn.execute(sa.text("""
        INSERT INTO public.tipos_tramites (codigo, nombre) VALUES
          ('REDACTAR_ANUNCIO', 'Redacción del Anuncio de Información Pública'),
          ('ANUNCIO_BOJA',     'Anuncio en el BOJA'),
          ('ANUNCIO_TITULAR',  'Notificación al Titular sobre Publicación')
        ON CONFLICT (codigo) DO NOTHING
    """))


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.tipos_tramites
         WHERE codigo IN (
           'RECEPCION_PROPUESTA_INF_VINC', 'RECEPCION_INFORME_VINCULANTE',
           'DISCREPANCIA_INF_VINC', 'REDACTAR_ANUNCIO', 'ANUNCIO_BOJA', 'ANUNCIO_TITULAR'
         )
    """))
    conn.execute(sa.text("""
        UPDATE public.tipos_tramites
           SET codigo = 'REMISION_MEDIO_AMBIENTE',
               nombre = 'Remisión a Medio Ambiente'
         WHERE codigo = 'REMISION_RESULTADO_IP_CONSULTAS'
    """))
