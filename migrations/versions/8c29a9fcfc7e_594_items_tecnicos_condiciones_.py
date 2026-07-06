"""594 items_tecnicos condiciones coberturas

Revision ID: 8c29a9fcfc7e
Revises: 07948f0f5f2c
Create Date: 2026-07-06 13:53:34.324254

Crea las tablas del catálogo de ítems técnicos del proyecto (#594):
  - items_tecnicos
  - condiciones_item_tecnico
  - coberturas_item_tecnico
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c29a9fcfc7e'
down_revision = '07948f0f5f2c'
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # Tabla items_tecnicos
    # ------------------------------------------------------------------
    op.create_table(
        'items_tecnicos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False,
                  comment='Identificador único autogenerado'),
        sa.Column('descripcion', sa.Text(), nullable=False,
                  comment='Apartado de contenido técnico exigido, texto libre'),
        sa.Column('norma_id', sa.Integer(), nullable=True,
                  comment='FK a normas — norma que establece este ítem'),
        sa.Column('articulo', sa.String(20), nullable=True,
                  comment='Artículo concreto de la norma: "4.1" | "DA2" | "DF1"'),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='1',
                  comment='Orden de presentación en el checklist de la UI'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true',
                  comment='Baja lógica (decisión humana del Supervisor, no automática)'),
        sa.ForeignKeyConstraint(['norma_id'], ['public.normas.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='public',
    )

    # ------------------------------------------------------------------
    # Tabla condiciones_item_tecnico
    # ------------------------------------------------------------------
    op.create_table(
        'condiciones_item_tecnico',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False,
                  comment='Identificador único autogenerado'),
        sa.Column('item_tecnico_id', sa.Integer(), nullable=False,
                  comment='FK a items_tecnicos'),
        sa.Column('variable_id', sa.Integer(), nullable=False,
                  comment='FK a catalogo_variables — variable evaluada'),
        sa.Column('operador', sa.String(20), nullable=False,
                  comment='Operador de comparación: EQ|NEQ|IN|NOT_IN|IS_NULL|NOT_NULL'),
        sa.Column('valor', sa.JSON(), nullable=True,
                  comment='Valor de referencia. Lista para IN/NOT_IN, None para IS_NULL/NOT_NULL'),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='1',
                  comment='Orden informativo dentro del ítem'),
        sa.CheckConstraint(
            "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL')",
            name='ck_condiciones_item_tecnico_operador'
        ),
        sa.ForeignKeyConstraint(
            ['item_tecnico_id'], ['public.items_tecnicos.id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['variable_id'], ['public.catalogo_variables.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='public',
    )
    op.create_index(
        'idx_condiciones_item_tecnico_item',
        'condiciones_item_tecnico', ['item_tecnico_id'], schema='public'
    )
    op.create_index(
        'idx_condiciones_item_tecnico_variable',
        'condiciones_item_tecnico', ['variable_id'], schema='public'
    )

    # ------------------------------------------------------------------
    # Tabla coberturas_item_tecnico
    # ------------------------------------------------------------------
    op.create_table(
        'coberturas_item_tecnico',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False,
                  comment='Identificador único autogenerado'),
        sa.Column('item_tecnico_id', sa.Integer(), nullable=False,
                  comment='FK a items_tecnicos'),
        sa.Column('solicitud_id', sa.Integer(), nullable=False,
                  comment='FK a solicitudes — solicitud en la que se verifica el ítem'),
        sa.Column('texto', sa.Text(), nullable=True,
                  comment='Ubicación/justificación en lenguaje natural. Vacío = no revisado'),
        sa.Column('cubierto', sa.Boolean(), nullable=False, server_default='false',
                  comment='Veredicto de cumplimiento — ver máquina de estados en el modelo'),
        sa.ForeignKeyConstraint(
            ['item_tecnico_id'], ['public.items_tecnicos.id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['solicitud_id'], ['public.solicitudes.id'],
            ondelete='CASCADE'
        ),
        sa.UniqueConstraint(
            'item_tecnico_id', 'solicitud_id',
            name='uq_coberturas_item_tecnico_item_sol'
        ),
        sa.PrimaryKeyConstraint('id'),
        schema='public',
    )
    op.create_index(
        'idx_coberturas_item_tecnico_item',
        'coberturas_item_tecnico', ['item_tecnico_id'], schema='public'
    )
    op.create_index(
        'idx_coberturas_item_tecnico_solicitud',
        'coberturas_item_tecnico', ['solicitud_id'], schema='public'
    )

    # ------------------------------------------------------------------
    # GRANTs para el usuario MCP de desarrollo
    # ------------------------------------------------------------------
    op.execute("GRANT SELECT ON public.items_tecnicos TO claude_desktop")
    op.execute("GRANT SELECT ON public.condiciones_item_tecnico TO claude_desktop")
    op.execute("GRANT SELECT ON public.coberturas_item_tecnico TO claude_desktop")


def downgrade():
    op.drop_table('coberturas_item_tecnico', schema='public')
    op.drop_table('condiciones_item_tecnico', schema='public')
    op.drop_table('items_tecnicos', schema='public')
