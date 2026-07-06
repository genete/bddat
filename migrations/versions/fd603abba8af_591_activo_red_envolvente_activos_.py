"""591 activo_red envolvente activos_expediente

Revision ID: fd603abba8af
Revises: b88f9bb4755b
Create Date: 2026-07-06 09:03:45.107888

Corte mínimo de integración con el modelo técnico de bddat-instalaciones
(https://github.com/genete/bddat-instalaciones, ADR-000/ADR-002/ADR-006):

  - activo_red: tabla base de identidad (id UUID uuid7, autorreferencia
    envolvente_id para contención genérica).
  - envolvente: única subtabla de este corte (recinto físico o agrupación
    lógica de líneas).
  - activos_expediente: tabla puente activo_red x expediente, con el estado
    administrativo de esa relación (eje independiente del físico, que no se
    almacena — ver ADR-000 Frontera de alcance).

Añade al catálogo de variables del motor:
  - aplica_rd223_2008: True si el expediente tiene algún activo con
    envolvente lógica (linea/circuito).
  - aplica_rd337_2014: True si tiene alguna envolvente física.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd603abba8af'
down_revision = 'b88f9bb4755b'
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # Tabla activo_red
    # ------------------------------------------------------------------
    op.create_table(
        'activo_red',
        sa.Column('id', sa.Uuid(), nullable=False,
                  comment='UUID (uuid7) generado en Python — gancho de referencia externo'),
        sa.Column('nombre', sa.Text(), nullable=False,
                  comment='Denominación del activo'),
        sa.Column('envolvente_id', sa.Uuid(), nullable=True,
                  comment='Contenedor (físico o lógico). Autorreferencia'),
        sa.Column('notas', sa.Text(), nullable=True,
                  comment='Texto libre para datos ocasionales'),
        sa.ForeignKeyConstraint(['envolvente_id'], ['public.activo_red.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='public',
    )
    op.create_index(
        'idx_activo_red_envolvente', 'activo_red', ['envolvente_id'], schema='public'
    )

    # ------------------------------------------------------------------
    # Tabla envolvente
    # ------------------------------------------------------------------
    op.create_table(
        'envolvente',
        sa.Column('activo_id', sa.Uuid(), nullable=False),
        sa.Column('tipo', sa.String(30), nullable=False,
                  comment='Tipo físico o lógico de envolvente'),
        sa.CheckConstraint(
            "tipo IN ("
            "'centro_transformacion', 'subestacion', 'posicion', "
            "'armario_seccionamiento', 'celda_prefabricada', "
            "'planta_fotovoltaica', 'parque_eolico', "
            "'planta_almacenamiento', 'planta_hibrida', "
            "'linea', 'circuito'"
            ")",
            name='ck_envolvente_tipo',
        ),
        sa.ForeignKeyConstraint(['activo_id'], ['public.activo_red.id']),
        sa.PrimaryKeyConstraint('activo_id'),
        schema='public',
    )

    # ------------------------------------------------------------------
    # Tabla activos_expediente (puente activo_red x expediente)
    # ------------------------------------------------------------------
    op.create_table(
        'activos_expediente',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('activo_id', sa.Uuid(), nullable=False,
                  comment='FK activo_red. Activo técnico vinculado al expediente'),
        sa.Column('expediente_id', sa.Integer(), nullable=False,
                  comment='FK expedientes'),
        sa.Column('estado_administrativo', sa.String(30), nullable=False,
                  comment='Estado administrativo de la relación activo-expediente'),
        sa.CheckConstraint(
            "estado_administrativo IN ("
            "'solicitado', 'en_tramitacion', 'autorizado_aap', "
            "'autorizado_construir_aac', 'autorizado_explotar_aps', "
            "'inscrito', 'desestimado', 'cerrado', 'desmantelado'"
            ")",
            name='ck_activos_expediente_estado',
        ),
        sa.ForeignKeyConstraint(['activo_id'], ['public.activo_red.id']),
        sa.ForeignKeyConstraint(
            ['expediente_id'], ['public.expedientes.id'], ondelete='CASCADE'
        ),
        sa.UniqueConstraint(
            'activo_id', 'expediente_id', name='uq_activos_expediente_activo_exp'
        ),
        sa.PrimaryKeyConstraint('id'),
        schema='public',
    )
    op.create_index(
        'idx_activos_expediente_activo', 'activos_expediente', ['activo_id'], schema='public'
    )
    op.create_index(
        'idx_activos_expediente_expediente', 'activos_expediente', ['expediente_id'], schema='public'
    )

    # ------------------------------------------------------------------
    # GRANTs para el usuario MCP de desarrollo
    # ------------------------------------------------------------------
    op.execute("GRANT SELECT ON public.activo_red TO claude_desktop")
    op.execute("GRANT SELECT ON public.envolvente TO claude_desktop")
    op.execute("GRANT SELECT ON public.activos_expediente TO claude_desktop")

    # ------------------------------------------------------------------
    # Seed: variables 'aplica_rd223_2008' / 'aplica_rd337_2014'
    # ------------------------------------------------------------------
    op.execute("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES
            ('aplica_rd223_2008',
             'El expediente tiene algún activo con envolvente lógica (línea/circuito)',
             'boolean', NULL, TRUE),
            ('aplica_rd337_2014',
             'El expediente tiene algún activo con envolvente física (CT/subestación/posición...)',
             'boolean', NULL, TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """)


def downgrade():
    op.execute("""
        DELETE FROM public.catalogo_variables
        WHERE nombre IN ('aplica_rd223_2008', 'aplica_rd337_2014')
    """)

    op.drop_table('activos_expediente', schema='public')
    op.drop_table('envolvente', schema='public')
    op.drop_table('activo_red', schema='public')
