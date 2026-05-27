"""192_requisitos_documentales

Revision ID: 6a2e29774f16
Revises: 410_compatibilidad_tipos_solicitud
Create Date: 2026-05-27 15:32:38.816419

Crea las tablas del modelo de requisitos documentales (#192):
  - requisitos_documentales
  - condiciones_requisito
  - documentos_requisito

Añade la variable 'tipo_expediente' al catálogo de variables del motor.
"""
from alembic import op
import sqlalchemy as sa


revision = '6a2e29774f16'
down_revision = '410_compatibilidad_tipos_solicitud'
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # Tabla requisitos_documentales
    # ------------------------------------------------------------------
    op.create_table(
        'requisitos_documentales',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False,
                  comment='Identificador único autogenerado'),
        sa.Column('tipo_documento_id', sa.Integer(), nullable=False,
                  comment='FK a tipos_documentos — tipo semántico del documento requerido'),
        sa.Column('descripcion_legal', sa.Text(), nullable=True,
                  comment='Descripción del requisito en lenguaje natural para el técnico'),
        sa.Column('norma_id', sa.Integer(), nullable=True,
                  comment='FK a normas — norma que establece este requisito'),
        sa.Column('articulo', sa.String(20), nullable=True,
                  comment='Artículo concreto de la norma: "4.1" | "DA2" | "DF1"'),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='1',
                  comment='Orden de presentación en el checklist de la UI'),
        sa.ForeignKeyConstraint(['tipo_documento_id'], ['public.tipos_documentos.id']),
        sa.ForeignKeyConstraint(['norma_id'], ['public.normas.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='public',
    )
    op.create_index(
        'idx_requisitos_documentales_tipo_doc',
        'requisitos_documentales', ['tipo_documento_id'], schema='public'
    )

    # ------------------------------------------------------------------
    # Tabla condiciones_requisito
    # ------------------------------------------------------------------
    op.create_table(
        'condiciones_requisito',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False,
                  comment='Identificador único autogenerado'),
        sa.Column('requisito_id', sa.Integer(), nullable=False,
                  comment='FK a requisitos_documentales'),
        sa.Column('variable_id', sa.Integer(), nullable=False,
                  comment='FK a catalogo_variables — variable evaluada'),
        sa.Column('operador', sa.String(20), nullable=False,
                  comment='Operador de comparación: EQ|NEQ|IN|NOT_IN|IS_NULL|NOT_NULL'),
        sa.Column('valor', sa.JSON(), nullable=True,
                  comment='Valor de referencia. Lista para IN/NOT_IN, None para IS_NULL/NOT_NULL'),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='1',
                  comment='Orden informativo dentro del requisito'),
        sa.CheckConstraint(
            "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL')",
            name='ck_condiciones_requisito_operador'
        ),
        sa.ForeignKeyConstraint(
            ['requisito_id'], ['public.requisitos_documentales.id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['variable_id'], ['public.catalogo_variables.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='public',
    )
    op.create_index(
        'idx_condiciones_requisito_requisito',
        'condiciones_requisito', ['requisito_id'], schema='public'
    )
    op.create_index(
        'idx_condiciones_requisito_variable',
        'condiciones_requisito', ['variable_id'], schema='public'
    )

    # ------------------------------------------------------------------
    # Tabla documentos_requisito
    # ------------------------------------------------------------------
    op.create_table(
        'documentos_requisito',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False,
                  comment='Identificador único autogenerado'),
        sa.Column('requisito_id', sa.Integer(), nullable=False,
                  comment='FK a requisitos_documentales'),
        sa.Column('solicitud_id', sa.Integer(), nullable=False,
                  comment='FK a solicitudes — solicitud en la que se cubre el requisito'),
        sa.Column('documento_id', sa.Integer(), nullable=False,
                  comment='FK a documentos — documento del pool que satisface el requisito'),
        sa.ForeignKeyConstraint(
            ['requisito_id'], ['public.requisitos_documentales.id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['solicitud_id'], ['public.solicitudes.id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['documento_id'], ['public.documentos.id']),
        sa.UniqueConstraint(
            'requisito_id', 'solicitud_id',
            name='uq_documentos_requisito_req_sol'
        ),
        sa.PrimaryKeyConstraint('id'),
        schema='public',
    )
    op.create_index(
        'idx_documentos_requisito_requisito',
        'documentos_requisito', ['requisito_id'], schema='public'
    )
    op.create_index(
        'idx_documentos_requisito_solicitud',
        'documentos_requisito', ['solicitud_id'], schema='public'
    )
    op.create_index(
        'idx_documentos_requisito_documento',
        'documentos_requisito', ['documento_id'], schema='public'
    )

    # ------------------------------------------------------------------
    # GRANTs para el usuario MCP de desarrollo
    # ------------------------------------------------------------------
    op.execute("GRANT SELECT ON public.requisitos_documentales TO claude_desktop")
    op.execute("GRANT SELECT ON public.condiciones_requisito TO claude_desktop")
    op.execute("GRANT SELECT ON public.documentos_requisito TO claude_desktop")

    # ------------------------------------------------------------------
    # Seed: variable 'tipo_expediente' en catalogo_variables
    # ------------------------------------------------------------------
    op.execute("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES (
            'tipo_expediente',
            'Tipo de expediente (Distribucion / Transporte / Renovable / Convencional)',
            'texto',
            NULL,
            TRUE
        )
        ON CONFLICT (nombre) DO NOTHING
    """)


def downgrade():
    # Eliminar seed
    op.execute("""
        DELETE FROM public.catalogo_variables WHERE nombre = 'tipo_expediente'
    """)

    # Eliminar tablas en orden inverso de dependencias
    op.drop_table('documentos_requisito', schema='public')
    op.drop_table('condiciones_requisito', schema='public')
    op.drop_table('requisitos_documentales', schema='public')
