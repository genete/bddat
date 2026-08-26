"""396_consulta_separata_no_generica

Revision ID: 396_consulta_separata_no_generica
Revises: 396_organismos_fase_resultado
Create Date: 2026-08-26

Issue #396 bloque 5 (ADR-042 §C) — CONSULTA_SEPARATA pasa a
`creacion_generica = false`, mismo criterio que CONSULTA_TRASLADO_ORGANISMO/
TITULAR (migración 725_creacion_generica_tramite): hoy la despensa genérica
del árbol permite crear separatas huérfanas sin vincular a ningún organismo
(en la BD de desarrollo hay trámites CONSULTA_* con 0 vínculos). Con `fase_id`
ya resuelto (bloque 1) esto no cierra ninguna puerta legítima: toda separata
nace desde `enviar_consultas()`, vinculada a su organismo en el mismo commit.

`mutaciones_arbol.crear_tramite` ya rechaza la creación genérica de trámites
con `creacion_generica=false` (guardia existente desde #725) — este cambio de
dato basta para activarlo también sobre CONSULTA_SEPARATA, sin tocar código.
"""
from alembic import op
import sqlalchemy as sa


revision = '396_consulta_separata_no_generica'
down_revision = '396_organismos_fase_resultado'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE public.tipos_tramites SET creacion_generica = false "
                "WHERE codigo = 'CONSULTA_SEPARATA'"),
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE public.tipos_tramites SET creacion_generica = true "
                "WHERE codigo = 'CONSULTA_SEPARATA'"),
    )
