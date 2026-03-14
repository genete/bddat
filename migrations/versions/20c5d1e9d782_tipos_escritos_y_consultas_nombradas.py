"""tipos_escritos y consultas_nombradas

Revision ID: 20c5d1e9d782
Revises: 45b0d1302dd4
Create Date: 2026-03-14 16:59:08.440463

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '20c5d1e9d782'
down_revision = '45b0d1302dd4'
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # consultas_nombradas
    # Catálogo de consultas SQL predefinidas para uso en plantillas .docx.
    # El supervisor referencia por nombre; BDDAT ejecuta el SQL parametrizado.
    # ------------------------------------------------------------------
    op.create_table(
        'consultas_nombradas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False,
                  comment='Identificador único autogenerado'),
        sa.Column('nombre', sa.Text(), nullable=False,
                  comment='Slug estable usado en plantillas: municipios_afectados'),
        sa.Column('descripcion', sa.Text(), nullable=False,
                  comment='Descripción legible para el supervisor en la UI'),
        sa.Column('sql', sa.Text(), nullable=False,
                  comment='SQL parametrizado. Parámetro esperado: :expediente_id'),
        sa.Column('columnas', JSONB(), nullable=False,
                  comment='[{campo, descripcion}] — columnas disponibles para el supervisor'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true',
                  comment='FALSE = oculta en UI pero conservada para histórico'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre', name='uq_consultas_nombradas_nombre'),
        schema='public'
    )

    # ------------------------------------------------------------------
    # tipos_escritos
    # Catálogo de tipos de escritos generables. Cada registro vincula
    # una plantilla .docx con su contexto ESFTT y su tipo de documento.
    # ------------------------------------------------------------------
    op.create_table(
        'tipos_escritos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False,
                  comment='Identificador único autogenerado'),
        sa.Column('codigo', sa.Text(), nullable=False,
                  comment='Slug estable para referencias en código: REQUERIMIENTO_SUBSANACION'),
        sa.Column('nombre', sa.Text(), nullable=False,
                  comment='Nombre legible para la UI'),
        sa.Column('descripcion', sa.Text(), nullable=True,
                  comment='Descripción ampliada del tipo de escrito'),
        sa.Column('ruta_plantilla', sa.Text(), nullable=False,
                  comment='Ruta relativa a PLANTILLAS_BASE/plantillas/'),
        sa.Column('tipo_documento_id', sa.Integer(), nullable=False,
                  comment='FK tipos_documentos — tipo que se asignará al documento generado'),
        sa.Column('contexto_clase', sa.Text(), nullable=True,
                  comment='Nombre de clase Python del Context Builder. NULL = solo Capa 1 (ContextoBaseExpediente)'),
        sa.Column('campos_catalogo', JSONB(), nullable=True,
                  comment='[{campo, descripcion}] — campos disponibles para mostrar en UI del contextualizador'),
        sa.Column('tipo_solicitud_id', sa.Integer(), nullable=True,
                  comment='FK tipos_solicitudes. NULL = aplica a cualquier tipo de solicitud'),
        sa.Column('tipo_fase_id', sa.Integer(), nullable=True,
                  comment='FK tipos_fases. NULL = aplica a cualquier fase'),
        sa.Column('tipo_tramite_id', sa.Integer(), nullable=True,
                  comment='FK tipos_tramites. NULL = aplica a cualquier trámite'),
        sa.Column('filtros_adicionales', JSONB(), nullable=False, server_default='{}',
                  comment='Variables de negocio futuras (tensión, tecnología...). Vacío por ahora.'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true',
                  comment='FALSE = oculta en tarea REDACTAR pero conservada para histórico'),
        sa.ForeignKeyConstraint(['tipo_documento_id'], ['public.tipos_documentos.id'],
                                name='fk_tipos_escritos_tipo_documento'),
        sa.ForeignKeyConstraint(['tipo_solicitud_id'], ['public.tipos_solicitudes.id'],
                                name='fk_tipos_escritos_tipo_solicitud'),
        sa.ForeignKeyConstraint(['tipo_fase_id'], ['public.tipos_fases.id'],
                                name='fk_tipos_escritos_tipo_fase'),
        sa.ForeignKeyConstraint(['tipo_tramite_id'], ['public.tipos_tramites.id'],
                                name='fk_tipos_escritos_tipo_tramite'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo', name='uq_tipos_escritos_codigo'),
        schema='public'
    )


def downgrade():
    op.drop_table('tipos_escritos', schema='public')
    op.drop_table('consultas_nombradas', schema='public')
