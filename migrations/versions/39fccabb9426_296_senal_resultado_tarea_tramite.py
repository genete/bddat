"""296_senal_resultado_tarea_tramite

Revision ID: 39fccabb9426
Revises: 8deef1de808e
Create Date: 2026-04-28

Tres tablas nuevas para la señal de resultado en Tarea y Trámite (#296):
  - tipos_resultado_documentos  — catálogo de efectos (INDIFERENTE/CORRECTA/INCORRECTA)
  - tipos_documentos_resultados_validos — whitelist N:M tipo_documento × tipo_resultado
  - resultados_documentos       — tabla operativa: resultado registrado para un documento
"""
from alembic import op
import sqlalchemy as sa


revision = '39fccabb9426'
down_revision = '8deef1de808e'
branch_labels = None
depends_on = None


def upgrade():
    # A. Catálogo de efectos de resultado sobre la tarea
    op.create_table(
        'tipos_resultado_documentos',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('codigo', sa.String(50), nullable=False,
                  comment='Código único: INDIFERENTE | CORRECTA | INCORRECTA'),
        sa.Column('nombre', sa.String(200), nullable=False,
                  comment='Descripción legible del resultado'),
        sa.Column('efecto_tarea', sa.String(20), nullable=False,
                  comment='Efecto que produce en la tarea propietaria del documento'),
        sa.UniqueConstraint('codigo', name='uq_tipos_resultado_documentos_codigo'),
        schema='public',
    )

    op.execute(
        "INSERT INTO public.tipos_resultado_documentos (codigo, nombre, efecto_tarea) VALUES "
        "('INDIFERENTE', 'Sin efecto en el resultado de la tarea', 'INDIFERENTE'), "
        "('CORRECTA', 'Notificación practicada correctamente', 'CORRECTA'), "
        "('INCORRECTA', 'Notificación caducada o fallida', 'INCORRECTA')"
    )

    # B. Whitelist N:M — qué resultados son válidos para cada tipo de documento
    op.create_table(
        'tipos_documentos_resultados_validos',
        sa.Column('tipo_documento_id', sa.Integer, nullable=False,
                  comment='FK a tipos_documentos'),
        sa.Column('tipo_resultado_documento_id', sa.Integer, nullable=False,
                  comment='FK a tipos_resultado_documentos'),
        sa.ForeignKeyConstraint(
            ['tipo_documento_id'], ['public.tipos_documentos.id'],
            name='fk_tdrv_tipo_documento', ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['tipo_resultado_documento_id'], ['public.tipos_resultado_documentos.id'],
            name='fk_tdrv_tipo_resultado_documento', ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('tipo_documento_id', 'tipo_resultado_documento_id',
                                name='pk_tipos_documentos_resultados_validos'),
        schema='public',
    )

    # C. Tabla operativa — resultado registrado para un documento concreto
    op.create_table(
        'resultados_documentos',
        sa.Column('documento_id', sa.Integer, nullable=False,
                  comment='FK única a documentos — un documento tiene como máximo un resultado'),
        sa.Column('tipo_resultado_documento_id', sa.Integer, nullable=False,
                  comment='FK a tipos_resultado_documentos'),
        sa.ForeignKeyConstraint(
            ['documento_id'], ['public.documentos.id'],
            name='fk_resultados_documentos_documento', ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['tipo_resultado_documento_id'], ['public.tipos_resultado_documentos.id'],
            name='fk_resultados_documentos_tipo_resultado', ondelete='RESTRICT',
        ),
        sa.PrimaryKeyConstraint('documento_id', name='pk_resultados_documentos'),
        schema='public',
    )

    op.create_index(
        'idx_resultados_documentos_tipo_resultado',
        'resultados_documentos',
        ['tipo_resultado_documento_id'],
        schema='public',
    )


def downgrade():
    op.drop_index('idx_resultados_documentos_tipo_resultado',
                  table_name='resultados_documentos', schema='public')
    op.drop_table('resultados_documentos', schema='public')
    op.drop_table('tipos_documentos_resultados_validos', schema='public')
    op.drop_table('tipos_resultado_documentos', schema='public')
