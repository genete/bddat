"""885_reformados_proyecto

Revision ID: 885_reformados_proyecto
Revises: 802_jsonb_bitacora
Create Date: 2026-09-09

Crea `reformados_proyecto` —el corte que parte el proyecto en versiones— y retira
`documentos_proyecto` (ADR-044 §B/§C).

La tabla retirada tenía 0 filas y ninguna escritura en el código: su `proyecto_id`
era redundante (expedientes.proyecto_id es NOT NULL y UNIQUE), «todos los
documentos del proyecto» es una consulta por tipo_doc sobre el pool, y su único
valor añadido —el apellido PRINCIPAL/MODIFICADO/REFUNDIDO/ANEXO— vivía en un
varchar(20) sin CHECK ni FK. El downgrade la recrea vacía, calcada del esquema
inicial.
"""
from alembic import op
import sqlalchemy as sa

revision = '885_reformados_proyecto'
down_revision = '802_jsonb_bitacora'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'reformados_proyecto',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('documento_id', sa.Integer(), nullable=False,
                  comment='FK UNIQUE a DOCUMENTOS. El documento que abre la versión; '
                          'un documento no abre dos cortes'),
        sa.Column('origen', sa.String(20), nullable=False,
                  comment='VOLUNTARIO (art. 76.1 LPACAP) o REQUERIDO por la Administración (art. 68.3)'),
        sa.PrimaryKeyConstraint('id', name='pk_reformados_proyecto'),
        sa.ForeignKeyConstraint(['documento_id'], ['public.documentos.id'],
                                name='fk_reformado_documento', ondelete='CASCADE'),
        sa.UniqueConstraint('documento_id', name='uq_reformado_documento'),
        sa.CheckConstraint("origen IN ('VOLUNTARIO', 'REQUERIDO')", name='ck_reformado_origen'),
        schema='public',
    )
    op.execute("GRANT SELECT ON public.reformados_proyecto TO claude_desktop")

    # Los índices y la FK con use_alter caen con la tabla.
    op.drop_table('documentos_proyecto', schema='public')


def downgrade():
    op.create_table(
        'documentos_proyecto',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False,
                  comment='Identificador único autogenerado del registro'),
        sa.Column('proyecto_id', sa.Integer(), nullable=False,
                  comment='FK a PROYECTOS. Proyecto al que pertenece el documento'),
        sa.Column('documento_id', sa.Integer(), nullable=False,
                  comment='FK UNIQUE a DOCUMENTOS. Un documento solo puede estar en un proyecto'),
        sa.Column('tipo', sa.String(length=20), nullable=False,
                  comment='Tipo de documento: PRINCIPAL, MODIFICADO, REFUNDIDO, ANEXO'),
        sa.Column('observaciones', sa.String(length=500), nullable=True,
                  comment='Notas del técnico sobre la incorporación del documento'),
        sa.ForeignKeyConstraint(['documento_id'], ['public.documentos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['proyecto_id'], ['public.proyectos.id'],
                                name='fk_documentos_proyecto_proyecto', ondelete='CASCADE',
                                use_alter=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('documento_id'),
        schema='public',
    )
    op.create_index('idx_documentos_proyecto_proyecto', 'documentos_proyecto',
                    ['proyecto_id'], schema='public')
    op.create_index('idx_documentos_proyecto_tipo', 'documentos_proyecto',
                    ['proyecto_id', 'tipo'], schema='public')

    op.drop_table('reformados_proyecto', schema='public')
