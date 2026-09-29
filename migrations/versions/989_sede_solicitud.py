"""989_sede_solicitud — sede del solicitante en la solicitud

Revision ID: 989_sede_solicitud
Revises: 969_una_notificacion_dup
Create Date: 2026-09-29

Issue #989, ADR-051 §K (enmienda del 2026-09-29).

- `solicitudes.direccion_notificacion_id` (FK `direcciones_notificacion`,
  opcional, SET NULL): la sede del solicitante que figura en la solicitud. Es
  la dirección que sale en el oficio y, si no hay representante, la del correo
  de aviso de la notificación. Sin ella, los datos de la ficha de la entidad.
  Que sea del solicitante, activa, de rol titular y sin otro NIF lo valida el
  servicio: un CHECK no puede mirar otra tabla.

Sin migración de datos: las solicitudes existentes quedan sin sede, que es el
criterio de la ficha.
"""
from alembic import op


revision = '989_sede_solicitud'
down_revision = '969_una_notificacion_dup'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE public.solicitudes
        ADD COLUMN direccion_notificacion_id INTEGER
            CONSTRAINT fk_solicitudes_direccion_notif
            REFERENCES public.direcciones_notificacion(id) ON DELETE SET NULL
    """)
    op.execute("""
        CREATE INDEX idx_solicitudes_direccion_notif
        ON public.solicitudes (direccion_notificacion_id)
    """)
    op.execute("""
        COMMENT ON COLUMN public.solicitudes.direccion_notificacion_id IS
        'Sede del solicitante en esta solicitud (ADR-051 §K): la dirección del oficio y, sin representante, el correo de aviso. NULL = datos de la ficha de la entidad'
    """)


def downgrade():
    op.execute('DROP INDEX IF EXISTS public.idx_solicitudes_direccion_notif')
    op.execute('ALTER TABLE public.solicitudes DROP COLUMN IF EXISTS direccion_notificacion_id')
