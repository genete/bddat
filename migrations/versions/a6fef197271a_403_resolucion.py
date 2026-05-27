"""403_resolucion

Revision ID: 403_resolucion
Revises: 402_notificacion_organismo
Create Date: 2026-05-20

Issue #403 — tabla resoluciones + seed plantilla RESOLUCION.
"""
from alembic import op
import sqlalchemy as sa

revision = '403_resolucion'
down_revision = '402_notificacion_organismo'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'resoluciones',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fase_id', sa.Integer(), nullable=False,
                  comment='FK fases. Una resolución por fase RESOLUCION.'),
        sa.Column('antecedentes', sa.Text(), nullable=True,
                  comment='Narración de antecedentes del expediente'),
        sa.Column('fundamentos', sa.Text(), nullable=True,
                  comment='Fundamentos jurídicos del acto (#435)'),
        sa.Column('resuelve', sa.Text(), nullable=True,
                  comment='Expresión verbal del sentido del acto'),
        sa.Column('condicionado', sa.Text(), nullable=True,
                  comment='Condicionado técnico de la autorización (#436)'),
        sa.ForeignKeyConstraint(['fase_id'], ['public.fases.id'],
                                name='fk_resoluciones_fase'),
        sa.PrimaryKeyConstraint('id', name='pk_resoluciones'),
        sa.UniqueConstraint('fase_id', name='uq_resoluciones_fase'),
        schema='public',
    )
    op.execute("GRANT SELECT ON public.resoluciones TO claude_desktop")

    # Seed plantilla RESOLUCION
    # tipo_documento_id: se busca el id de RESOLUCION en tipos_documentos
    op.execute("""
        INSERT INTO public.plantillas
            (codigo, nombre, descripcion, ruta_plantilla, contexto_clase,
             tipo_documento_id, activo)
        VALUES (
            'RESOLUCION',
            'Resolución',
            'Escrito de resolución del expediente (favorable, condicionada o denegatoria)',
            'escritos/resolucion.docx',
            'ContextoResolucion',
            (SELECT id FROM public.tipos_documentos WHERE codigo = 'RESOLUCION'),
            TRUE
        )
    """)


def downgrade():
    op.execute("DELETE FROM public.plantillas WHERE codigo = 'RESOLUCION'")
    op.drop_table('resoluciones', schema='public')
