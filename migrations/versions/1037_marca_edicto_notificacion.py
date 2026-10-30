"""1037_marca_edicto_notificacion — qué notificaciones van por edicto y qué trámite las recoge

Revision ID: 1037_marca_edicto_notificacion
Revises: 1007_fuera_modelo_rutas
Create Date: 2026-10-29

Issue #1037, ADR-052 §A y §G (se enmiendan al cerrar el issue).

El conjunto de notificaciones que cubre un anuncio edictal lo decide el usuario antes
de que exista el anuncio (Carlos, 2026-10-23): las marca en el trámite de notificación,
y el trámite `NOTIFICACION_EDICTAL` las recoge al crearse. Dos estados, porque una fase
puede tener varios edictos y el segundo no debe tomar lo que ya tomó el primero.

- `notificaciones.va_por_edicto`: el usuario la ha marcado. NOT NULL, `false` por defecto.
- `notificaciones.tramite_edictal_id` (FK `tramites`, SET NULL): el trámite edictal que la
  recogió. Una marcada sin recoger espera al siguiente edicto de la fase; si el trámite
  edictal se borra, la notificación vuelve a «marcada» y no se pierde la decisión.
- `ck_notificaciones_edicto_recogida`: una notificación recogida está marcada.

Lo que la BD no valida, a propósito: que la fuente sea de persona física (la lista es la
constante `FUENTES_QUE_ADMITEN_EDICTO` del modelo, que puede cambiar sin migrar), que la
tarea no esté cerrada, y que `tramite_edictal_id` sea un `NOTIFICACION_EDICTAL` de la misma
fase: un CHECK no mira otra tabla. Lo comprueban `editar_tramite` y `crear_tramite`.

Sin migración de datos: ninguna notificación existente va por edicto. El downgrade pierde
las marcas que haya.
"""
from alembic import op


revision = '1037_marca_edicto_notificacion'
down_revision = '1007_fuera_modelo_rutas'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE public.notificaciones
        ADD COLUMN va_por_edicto BOOLEAN NOT NULL DEFAULT false,
        ADD COLUMN tramite_edictal_id INTEGER
            CONSTRAINT fk_notificaciones_tramite_edictal
            REFERENCES public.tramites(id) ON DELETE SET NULL
    """)
    op.execute("""
        ALTER TABLE public.notificaciones
        ADD CONSTRAINT ck_notificaciones_edicto_recogida
        CHECK (tramite_edictal_id IS NULL OR va_por_edicto)
    """)
    op.execute("""
        CREATE INDEX idx_notificaciones_tramite_edictal
        ON public.notificaciones (tramite_edictal_id)
        WHERE tramite_edictal_id IS NOT NULL
    """)
    op.execute("""
        COMMENT ON COLUMN public.notificaciones.va_por_edicto IS
        'Marcada por el usuario para ir por edicto (#1037). Solo la admiten las fuentes de FUENTES_QUE_ADMITEN_EDICTO; lo valida el servicio'
    """)
    op.execute("""
        COMMENT ON COLUMN public.notificaciones.tramite_edictal_id IS
        'Trámite NOTIFICACION_EDICTAL que la recogió al crearse. NULL = no recogida (marcada que espera al siguiente edicto de la fase, o no marcada)'
    """)


def downgrade():
    op.execute('DROP INDEX IF EXISTS public.idx_notificaciones_tramite_edictal')
    op.execute('ALTER TABLE public.notificaciones DROP CONSTRAINT IF EXISTS ck_notificaciones_edicto_recogida')
    op.execute("""
        ALTER TABLE public.notificaciones
        DROP COLUMN IF EXISTS tramite_edictal_id,
        DROP COLUMN IF EXISTS va_por_edicto
    """)
