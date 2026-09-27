"""967_destinatario_notificacion — destinatario en la fila de notificaciones

Revision ID: 967_destinatario_notificacion
Revises: 956_cert_cierre_fase
Create Date: 2026-09-27

Issue #967 (N5a-1), ADR-051 §B y §K.

- `solicitudes.representante_entidad_id` (FK `entidades`, opcional): quien
  representa al solicitante en esa solicitud (§K).
- `notificaciones` gana el destinatario: `fuente` (NOT NULL, lista cerrada en
  código, `app.models.notificaciones.FUENTES`), `entidad_id`,
  `en_nombre_de_entidad_id`, `direccion_origen_id` (SET NULL), los datos
  copiados (`dest_*`) y `destinatario_fijado_en`.
- `canal` admite NULL: la fila nace con la tarea (ADR-051 §B) y el canal se
  fija con el primer justificante (#712).

Sin migración de datos (issue #967 §5): los datos de desarrollo se desechan y
los expedientes tipo se recrean con los scripts. Las filas que ya existan
reciben `fuente = 'SOLICITANTE'` solo para poder poner el NOT NULL; las
`NOTIFICAR` sin fila siguen sin ella hasta que se recreen.
"""
from alembic import op


revision = '967_destinatario_notificacion'
down_revision = '956_cert_cierre_fase'
branch_labels = None
depends_on = None

# Copia de `app.models.notificaciones.FUENTES` en el momento de la migración:
# una migración no importa código de la aplicación.
_FUENTES = (
    'SOLICITANTE', 'ORGANISMO_DEL_TRAMITE', 'ORGANISMOS_CONSULTADOS',
    'ORGANO_AMBIENTAL', 'PROPIETARIOS_DUP', 'INTERESADOS_RECONOCIDOS',
    'BOLETIN', 'AYUNTAMIENTO', 'MINISTERIO', 'ORGANO_SUPERIOR',
)


def upgrade():
    op.execute("""
        ALTER TABLE public.solicitudes
        ADD COLUMN representante_entidad_id INTEGER
            REFERENCES public.entidades(id)
    """)
    op.execute("""
        COMMENT ON COLUMN public.solicitudes.representante_entidad_id IS
        'Quien representa al solicitante en esta solicitud (ADR-051 §K). Con él, se notifica al representante'
    """)

    op.execute('ALTER TABLE public.notificaciones ALTER COLUMN canal DROP NOT NULL')
    op.execute("""
        COMMENT ON COLUMN public.notificaciones.canal IS
        'NOTIFICA | BANDEJA | SIR | POSTAL. NULL hasta el primer justificante (#712, #967)'
    """)

    op.execute('ALTER TABLE public.notificaciones ADD COLUMN fuente VARCHAR(30)')
    op.execute("UPDATE public.notificaciones SET fuente = 'SOLICITANTE'")
    op.execute('ALTER TABLE public.notificaciones ALTER COLUMN fuente SET NOT NULL')
    lista = ', '.join(f"'{f}'" for f in _FUENTES)
    op.execute(f"""
        ALTER TABLE public.notificaciones
        ADD CONSTRAINT ck_notificaciones_fuente CHECK (fuente IN ({lista}))
    """)
    op.execute("""
        COMMENT ON COLUMN public.notificaciones.fuente IS
        'Por qué se notifica (ADR-051 §C). Se fija al crear la tarea y no cambia'
    """)

    op.execute("""
        ALTER TABLE public.notificaciones
        ADD COLUMN entidad_id INTEGER REFERENCES public.entidades(id),
        ADD COLUMN en_nombre_de_entidad_id INTEGER REFERENCES public.entidades(id),
        ADD COLUMN direccion_origen_id INTEGER
            REFERENCES public.direcciones_notificacion(id) ON DELETE SET NULL,
        ADD COLUMN dest_nombre TEXT,
        ADD COLUMN dest_nif VARCHAR(20),
        ADD COLUMN dest_direccion TEXT,
        ADD COLUMN dest_codigo_postal VARCHAR(10),
        ADD COLUMN dest_municipio TEXT,
        ADD COLUMN dest_provincia TEXT,
        ADD COLUMN dest_email TEXT,
        ADD COLUMN dest_dir3 VARCHAR(20),
        ADD COLUMN dest_sir VARCHAR(50),
        ADD COLUMN destinatario_fijado_en TIMESTAMP WITH TIME ZONE
    """)
    op.execute("""
        COMMENT ON COLUMN public.notificaciones.entidad_id IS
        'A quién se envía (el representante, si lo hay). NULL = sin destinatario'
    """)
    op.execute("""
        COMMENT ON COLUMN public.notificaciones.en_nombre_de_entidad_id IS
        'Representado, cuando se notifica a un representante'
    """)
    op.execute("""
        COMMENT ON COLUMN public.notificaciones.direccion_origen_id IS
        'Dirección de la que se copió el destinatario — solo referencia; lo válido es la copia'
    """)
    op.execute("""
        COMMENT ON COLUMN public.notificaciones.destinatario_fijado_en IS
        'Cuándo se copió el destinatario. Fijo desde el primer justificante'
    """)
    op.execute('CREATE INDEX idx_notificaciones_entidad ON public.notificaciones (entidad_id)')


def downgrade():
    op.execute('DROP INDEX IF EXISTS public.idx_notificaciones_entidad')
    op.execute("""
        ALTER TABLE public.notificaciones
        DROP COLUMN destinatario_fijado_en,
        DROP COLUMN dest_sir,
        DROP COLUMN dest_dir3,
        DROP COLUMN dest_email,
        DROP COLUMN dest_provincia,
        DROP COLUMN dest_municipio,
        DROP COLUMN dest_codigo_postal,
        DROP COLUMN dest_direccion,
        DROP COLUMN dest_nif,
        DROP COLUMN dest_nombre,
        DROP COLUMN direccion_origen_id,
        DROP COLUMN en_nombre_de_entidad_id,
        DROP COLUMN entidad_id
    """)
    op.execute('ALTER TABLE public.notificaciones DROP CONSTRAINT ck_notificaciones_fuente')
    op.execute('ALTER TABLE public.notificaciones DROP COLUMN fuente')
    # Filas sin justificante (nacidas con la tarea): el esquema anterior no las
    # admite (ADR-034/#928: fila ⇒ justificante).
    op.execute('DELETE FROM public.notificaciones WHERE canal IS NULL')
    op.execute('ALTER TABLE public.notificaciones ALTER COLUMN canal SET NOT NULL')
    op.execute('COMMENT ON COLUMN public.notificaciones.canal IS NULL')
    op.execute('ALTER TABLE public.solicitudes DROP COLUMN representante_entidad_id')
