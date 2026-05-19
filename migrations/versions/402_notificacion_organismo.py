"""402_notificacion_organismo — CB ContextoNotificacionOrganismo

Revision ID: 402_notificacion_organismo
Revises: 374_interesados_expediente
Create Date: 2026-05-19

Issue #402 — Registra el tipo de escrito NOTIF_ORGANISMO en la tabla plantillas.
Asociado al trámite CONSULTA_TRASLADO_ORGANISMO (id=10) y al tipo de documento
OFICIO_TRASLADO_REPAROS (id=30).
"""
from alembic import op

revision = '402_notificacion_organismo'
down_revision = '374_interesados_expediente'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO public.plantillas
            (codigo, nombre, descripcion, ruta_plantilla, tipo_documento_id,
             contexto_clase, filtros_adicionales, tipo_tramite_id, activo)
        VALUES (
            'NOTIF_ORGANISMO',
            'Notificación a organismo consultado',
            'Traslado de reparos del titular al organismo sectorial',
            'escritos/notificacion_organismo.docx',
            30,
            'ContextoNotificacionOrganismo',
            '{}',
            10,
            TRUE
        )
    """)


def downgrade():
    op.execute("DELETE FROM public.plantillas WHERE codigo = 'NOTIF_ORGANISMO'")
