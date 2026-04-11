"""Añadir campo abrev a tipos_fases, tipos_tramites, tipos_tareas

Revision ID: 0869cda75380
Revises: f0d0988bb956
Create Date: 2026-03-03 20:15:38.257083

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0869cda75380'
down_revision = 'f0d0988bb956'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tipos_fases',
        sa.Column('abrev', sa.String(20), nullable=True,
                  comment='Abreviatura para breadcrumb (máx 20 car.). Si nula, se usa nombre.'),
        schema='public'
    )
    op.add_column('tipos_tramites',
        sa.Column('abrev', sa.String(20), nullable=True,
                  comment='Abreviatura para breadcrumb (máx 20 car.). Si nula, se usa nombre.'),
        schema='public'
    )
    op.add_column('tipos_tareas',
        sa.Column('abrev', sa.String(20), nullable=True,
                  comment='Abreviatura para breadcrumb (máx 20 car.). Si nula, se usa nombre.'),
        schema='public'
    )

    # Valores iniciales para tipos_fases
    op.execute("""
        UPDATE public.tipos_fases SET abrev = CASE codigo
            WHEN 'REGISTRO_SOLICITUD'     THEN 'REG.SOL.'
            WHEN 'ADMISIBILIDAD'          THEN 'ADMIS.'
            WHEN 'ANALISIS_TECNICO'       THEN 'AN.TÉC.'
            WHEN 'CONSULTA_MINISTERIO'    THEN 'CONS.MIN.'
            WHEN 'COMPATIBILIDAD_AMBIENTAL' THEN 'COMP.AMB.'
            WHEN 'ADMISION_TRAMITE'       THEN 'ADMIS.TR.'
            WHEN 'CONSULTAS'              THEN 'CONSULTAS'
            WHEN 'INFORMACION_PUBLICA'    THEN 'INF.PÚB.'
            WHEN 'FIGURA_AMBIENTAL_EXTERNA' THEN 'FIG.AMB.'
            WHEN 'AAU_AAUS_INTEGRADA'     THEN 'AAU/AAUS'
            ELSE NULL
        END
    """)

    # Valores iniciales para tipos_tramites
    op.execute("""
        UPDATE public.tipos_tramites SET abrev = CASE codigo
            WHEN 'RECEPCION_SOLICITUD'         THEN 'REC.SOL.'
            WHEN 'COMUNICACION_INICIO'         THEN 'COM.INI.'
            WHEN 'COMPROBACION_ADMISIBILIDAD'  THEN 'COMP.ADM.'
            WHEN 'REQUERIMIENTO_SUBSANACION'   THEN 'REQ.SUB.'
            WHEN 'COMPROBACION_DOCUMENTAL'     THEN 'COMP.DOC.'
            WHEN 'REQUERIMIENTO_MEJORA'        THEN 'REQ.MEJ.'
            WHEN 'SOLICITUD_INFORME_MINISTERIO' THEN 'SOL.INF.'
            WHEN 'RECEPCION_INFORME_MINISTERIO' THEN 'REC.INF.'
            WHEN 'SOLICITUD_COMPATIBILIDAD'    THEN 'SOL.COMP.'
            WHEN 'AUDIENCIA_COMPATIBILIDAD'    THEN 'AUD.COMP.'
            ELSE NULL
        END
    """)

    # Valores iniciales para tipos_tareas
    op.execute("""
        UPDATE public.tipos_tareas SET abrev = CASE codigo
            WHEN 'ANALISIS'     THEN 'ANÁLISIS'
            WHEN 'REDACTAR'     THEN 'REDACTAR'
            WHEN 'FIRMAR'       THEN 'FIRMAR'
            WHEN 'NOTIFICAR'    THEN 'NOTIFICAR'
            WHEN 'PUBLICAR'     THEN 'PUBLICAR'
            WHEN 'ESPERAR_PLAZO' THEN 'PLAZO'
            WHEN 'INCORPORAR'   THEN 'INCORPORAR'
            ELSE NULL
        END
    """)


def downgrade():
    op.drop_column('tipos_tareas',   'abrev', schema='public')
    op.drop_column('tipos_tramites', 'abrev', schema='public')
    op.drop_column('tipos_fases',    'abrev', schema='public')
