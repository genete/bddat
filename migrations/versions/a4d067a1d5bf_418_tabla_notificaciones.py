"""418_tabla_notificaciones

Revision ID: a4d067a1d5bf
Revises: 420_modelo_nm_documento_tarea
Create Date: 2026-05-17 20:20:26.737011

Crea tabla notificaciones (documento vitaminado para NOTIFICAR) y elimina
las tres tablas del diseño previo, que estaban vacías (ADR-008, #418).
"""
from alembic import op
import sqlalchemy as sa


revision = 'a4d067a1d5bf'
down_revision = '420_modelo_nm_documento_tarea'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'notificaciones',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('documento_id', sa.Integer(), nullable=False),
        sa.Column('resultado', sa.String(12), nullable=False),
        sa.Column('canal', sa.String(10), nullable=False),
        sa.Column('fecha_notificacion', sa.Date(), nullable=False),
        sa.Column('numero_intento', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.CheckConstraint("resultado IN ('CORRECTA', 'INCORRECTA')", name='ck_notificaciones_resultado'),
        sa.CheckConstraint("canal IN ('NOTIFICA', 'BANDEJA', 'SIR', 'POSTAL')", name='ck_notificaciones_canal'),
        sa.CheckConstraint('numero_intento IN (1, 2)', name='ck_notificaciones_numero_intento'),
        sa.ForeignKeyConstraint(['documento_id'], ['public.documentos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_notificaciones'),
        sa.UniqueConstraint('documento_id', name='uq_notificaciones_documento'),
        schema='public',
    )
    op.execute("GRANT SELECT ON public.notificaciones TO claude_desktop")

    # Eliminar tablas del diseño previo (vacías — ADR-008 §"Tablas eliminadas")
    # Orden: primero las que tienen FK a tipos_resultado_documentos
    op.drop_table('tipos_documentos_resultados_validos', schema='public')
    op.drop_table('resultados_documentos', schema='public')
    op.drop_table('tipos_resultado_documentos', schema='public')


def downgrade():
    op.drop_table('notificaciones', schema='public')

    op.create_table(
        'tipos_resultado_documentos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('codigo', sa.String(50), nullable=False),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('efecto_tarea', sa.String(20), nullable=False),
        sa.UniqueConstraint('codigo', name='uq_tipos_resultado_documentos_codigo'),
        sa.PrimaryKeyConstraint('id'),
        schema='public',
    )
    op.create_table(
        'resultados_documentos',
        sa.Column('documento_id', sa.Integer(), nullable=False),
        sa.Column('tipo_resultado_documento_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['documento_id'], ['public.documentos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['tipo_resultado_documento_id'],
            ['public.tipos_resultado_documentos.id'],
            ondelete='RESTRICT',
        ),
        sa.PrimaryKeyConstraint('documento_id', name='pk_resultados_documentos'),
        schema='public',
    )
    op.create_table(
        'tipos_documentos_resultados_validos',
        sa.Column('tipo_documento_id', sa.Integer(), nullable=False),
        sa.Column('tipo_resultado_documento_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['tipo_documento_id'], ['public.tipos_documentos.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['tipo_resultado_documento_id'],
            ['public.tipos_resultado_documentos.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint(
            'tipo_documento_id', 'tipo_resultado_documento_id',
            name='pk_tipos_documentos_resultados_validos',
        ),
        schema='public',
    )
