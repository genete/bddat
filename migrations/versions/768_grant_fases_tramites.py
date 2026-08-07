"""768_grant_fases_tramites

Revision ID: 768_grant_fases_tramites
Revises: 728_firmantes_portafirmas
Create Date: 2026-08-07

Issue #768 — Mismo defecto que corrigió #449 para organismos_expediente: la
tabla fases_tramites existe pero el rol claude_desktop no tiene GRANT SELECT,
contra lo que exige REGLAS_DESARROLLO.md.

Consecuencia previa al fix:
- El MCP PostgreSQL no puede leer fases_tramites («permiso denegado»), así que
  no se puede mapear un tipo de trámite con la fase a la que pertenece.
- Detectado al analizar #764 (regla de recepción en ESPERAR_PLAZO), donde hubo
  que renunciar a atribuir cada trámite a su fase.

Barrido sobre pg_class (no sobre information_schema.tables, que solo muestra
objetos sobre los que el rol ya tiene algún privilegio): fases_tramites era la
única tabla, vista o vista materializada de public sin SELECT para el rol.
"""
from alembic import op


revision = '768_grant_fases_tramites'
down_revision = '728_firmantes_portafirmas'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("GRANT SELECT ON public.fases_tramites TO claude_desktop")


def downgrade():
    op.execute("REVOKE SELECT ON public.fases_tramites FROM claude_desktop")
