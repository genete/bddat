"""449_grant_organismos_expediente

Revision ID: 449_grant_organismos_expediente
Revises: 405_catalogo_requerimientos
Create Date: 2026-05-22

Issue #449 — Fix de la migración 391_organismos_expediente.py, que olvidó
otorgar GRANT SELECT al rol claude_desktop sobre la tabla recién creada.

Es la única tabla del proyecto sin ese GRANT; el resto de migraciones
equivalentes (392, 393, 402, 403, 418, 420, 425, …) sí lo incluyen.

Consecuencia previa al fix:
- El rol claude_desktop no puede leer organismos_expediente.
- La consulta nombrada `organismos_consulta` (seed #395) queda inutilizable
  desde claude_desktop / MCP postgres.
- Auditorías vía claude_desktop dan falsos negativos sobre la existencia
  de la tabla.

Detectado en auditoría exhaustiva de migraciones, 22 mayo 2026.
"""
from alembic import op


revision = '449_grant_organismos_expediente'
down_revision = '405_catalogo_requerimientos'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("GRANT SELECT ON public.organismos_expediente TO claude_desktop")


def downgrade():
    op.execute("REVOKE SELECT ON public.organismos_expediente FROM claude_desktop")
