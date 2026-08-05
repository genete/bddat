"""728_unidades_organo_propio

Revision ID: 728_unidades_organo_propio
Revises: 728_consejerias_delegaciones_territoriales
Create Date: 2026-08-05

Issue #728 — Crea unidades_organo_propio: una fila por provincia (8), FK a
consejerias_delegaciones_territoriales. Ver ADR-039 §1.

sede_direccion/sede_telefono/sede_correo quedan NULL en esta migración: no
existe fuente de ese dato en el repo todavía, se completará vía la futura
pantalla de mantenimiento — confirmado con Carlos, no se inventan datos.

codigo_bandeja_texto se puebla con el nodo "SV. ENERGIA (IND) (<PROVINCIA>)"
de app/data/bandeja_destinos/destinos_industria_energia_minas.csv por
provincia, confirmado con Carlos como el nodo correcto (columna "text" del
CSV). No se incluye fila de servicios centrales (provincia NULL): fuera del
alcance mínimo de #728, se añadirá si hay adopción de BDDAT en centrales.
"""
from alembic import op
import sqlalchemy as sa


revision = '728_unidades_organo_propio'
down_revision = '728_consejerias_delegaciones_territoriales'
branch_labels = None
depends_on = None

_PROVINCIAS_CODIGO_BANDEJA = (
    ('Almería', 'SV. ENERGIA (IND) (ALMERIA)'),
    ('Cádiz', 'SV. ENERGIA (IND) (CADIZ)'),
    ('Córdoba', 'SV. ENERGIA (IND) (CORDOBA)'),
    ('Granada', 'SV. ENERGIA (IND) (GRANADA)'),
    ('Huelva', 'SV. ENERGIA (IND) (HUELVA)'),
    ('Jaén', 'SV. ENERGIA (IND) (JAEN)'),
    ('Málaga', 'SV. ENERGIA (IND) (MALAGA)'),
    ('Sevilla', 'SV. ENERGIA (IND) (SEVILLA)'),
)


def upgrade():
    op.create_table(
        'unidades_organo_propio',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('consejerias_delegacion_id', sa.Integer(), nullable=False,
                  comment='FK consejerias_delegaciones_territoriales. Composición de consejerías de esta unidad'),
        sa.Column('provincia', sa.String(100), nullable=True,
                  comment='Provincia de la unidad. NULL reservado para servicios centrales'),
        sa.Column('sede_direccion', sa.String(300), nullable=True,
                  comment='Dirección postal de la sede. NULL hasta que se complete vía la pantalla de mantenimiento'),
        sa.Column('sede_telefono', sa.String(30), nullable=True,
                  comment='Teléfono de la sede. NULL hasta que se complete vía la pantalla de mantenimiento'),
        sa.Column('sede_correo', sa.String(150), nullable=True,
                  comment='Correo de la sede. NULL hasta que se complete vía la pantalla de mantenimiento'),
        sa.Column('codigo_bandeja_texto', sa.String(200), nullable=True,
                  comment='Rótulo tal cual aparece en BandeJA, para localizar el nodo por texto en la automatización de #758'),
        sa.PrimaryKeyConstraint('id', name='pk_unidades_organo_propio'),
        sa.ForeignKeyConstraint(['consejerias_delegacion_id'], ['public.consejerias_delegaciones_territoriales.id'],
                                name='fk_unidad_organo_consejerias_delegacion'),
        schema='public',
    )
    op.create_index('idx_unidad_organo_provincia', 'unidades_organo_propio', ['provincia'], schema='public')

    conn = op.get_bind()
    for provincia, codigo_bandeja_texto in _PROVINCIAS_CODIGO_BANDEJA:
        conn.execute(
            sa.text(
                "INSERT INTO public.unidades_organo_propio "
                "(consejerias_delegacion_id, provincia, codigo_bandeja_texto) "
                "VALUES (1, :provincia, :codigo_bandeja_texto)"
            ),
            {'provincia': provincia, 'codigo_bandeja_texto': codigo_bandeja_texto},
        )

    op.execute("GRANT SELECT ON public.unidades_organo_propio TO claude_desktop")


def downgrade():
    op.drop_index('idx_unidad_organo_provincia', table_name='unidades_organo_propio', schema='public')
    op.drop_table('unidades_organo_propio', schema='public')
