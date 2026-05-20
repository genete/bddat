"""404_informacion_publica

Revision ID: 404_informacion_publica
Revises: 403_resolucion
Create Date: 2026-05-20

Issue #404 — tabla informaciones_publicas + seed plantilla ANUNCIO_IP.
"""
from alembic import op
import sqlalchemy as sa

revision = '404_informacion_publica'
down_revision = '403_resolucion'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'informaciones_publicas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fase_id', sa.Integer(), nullable=False,
                  comment='FK fases. Un registro por fase INFORMACION_PUBLICA.'),
        sa.Column('antecedentes', sa.Text(), nullable=True,
                  comment='Narración de la necesidad del anuncio de información pública'),
        sa.Column('fundamentos', sa.Text(), nullable=True,
                  comment='Fundamento normativo que exige el trámite de IP (#435)'),
        sa.Column('exposicion_publica', sa.Text(), nullable=True,
                  comment='Período de exposición, plazo, sede y lugar de consulta'),
        sa.ForeignKeyConstraint(['fase_id'], ['public.fases.id'],
                                name='fk_informaciones_publicas_fase'),
        sa.PrimaryKeyConstraint('id', name='pk_informaciones_publicas'),
        sa.UniqueConstraint('fase_id', name='uq_informaciones_publicas_fase'),
        schema='public',
    )
    op.execute("GRANT SELECT ON public.informaciones_publicas TO claude_desktop")

    # Seed plantilla ANUNCIO_IP
    op.execute("""
        INSERT INTO public.plantillas
            (codigo, nombre, descripcion, ruta_plantilla, contexto_clase,
             tipo_documento_id, activo)
        VALUES (
            'ANUNCIO_IP',
            'Anuncio de información pública',
            'Anuncio de sometimiento a información pública de la instalación',
            'escritos/informacion_publica.docx',
            'ContextoInformacionPublica',
            (SELECT id FROM public.tipos_documentos WHERE codigo = 'ANUNCIO_IP'),
            TRUE
        )
    """)


def downgrade():
    op.execute("DELETE FROM public.plantillas WHERE codigo = 'ANUNCIO_IP'")
    op.drop_table('informaciones_publicas', schema='public')
