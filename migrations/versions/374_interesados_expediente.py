"""374_interesados_expediente — tabla de interesados por expediente

Revision ID: 374_interesados_expediente
Revises: 425_certificados
Create Date: 2026-05-19

Issue #374 — Tabla interesados_expediente + seed TipoTramite REGISTRO_INTERESADOS.
"""
from alembic import op
import sqlalchemy as sa


revision = '374_interesados_expediente'
down_revision = '425_certificados'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'interesados_expediente',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('expediente_id', sa.Integer(), nullable=False),
        sa.Column('entidad_id', sa.Integer(), nullable=True),
        sa.Column('nombre', sa.String(255), nullable=True),
        sa.Column('nif', sa.String(20), nullable=True),
        sa.Column('tipo_origen', sa.String(30), nullable=False),
        sa.Column('fuente_doc_id', sa.Integer(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['expediente_id'], ['public.expedientes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entidad_id'], ['public.entidades.id']),
        sa.ForeignKeyConstraint(['fuente_doc_id'], ['public.documentos.id']),
        sa.CheckConstraint(
            "tipo_origen IN ('TITULAR','ORGANISMO_CONSULTADO','MEDIO_AMBIENTE','INTERESADO_RECONOCIDO','DUP')",
            name='ck_interesados_expediente_tipo_origen',
        ),
        sa.PrimaryKeyConstraint('id'),
        schema='public',
    )
    op.create_index(
        'idx_interesados_expediente_expediente',
        'interesados_expediente', ['expediente_id'], schema='public',
    )
    op.create_index(
        'idx_interesados_expediente_entidad',
        'interesados_expediente', ['entidad_id'], schema='public',
    )
    op.execute("GRANT SELECT ON public.interesados_expediente TO claude_desktop")

    # Seed TipoTramite
    op.get_bind().execute(sa.text("""
        INSERT INTO public.tipos_tramites (codigo, nombre)
        VALUES ('REGISTRO_INTERESADOS', 'Registro de Interesados')
        ON CONFLICT (codigo) DO NOTHING
    """))


def downgrade():
    op.get_bind().execute(sa.text(
        "DELETE FROM public.tipos_tramites WHERE codigo = 'REGISTRO_INTERESADOS'"
    ))
    op.drop_index('idx_interesados_expediente_entidad', table_name='interesados_expediente', schema='public')
    op.drop_index('idx_interesados_expediente_expediente', table_name='interesados_expediente', schema='public')
    op.drop_table('interesados_expediente', schema='public')
