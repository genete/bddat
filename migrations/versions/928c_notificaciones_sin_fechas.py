"""928c_notificaciones_sin_fechas — notificaciones sin fechas; RECHAZADA; sede

Revision ID: 928c_notificaciones_sin_fechas
Revises: 928b_ttd_multiples_entradas
Create Date: 2026-09-23

Issue #928 (N1 §3), ADR-049 §B/§C/§D. Las fechas de una notificación dejan de
guardarse en la fila: salen de `documentos.fecha_administrativa` de sus
justificantes (`app/services/notificaciones.py`).

- Quita `fecha_puesta_disposicion` y `fecha_resultado`.
- `resultado` admite `RECHAZADA` (art. 41.5: da la notificación por
  efectuada). Recrea `ck_notificaciones_resultado`; cabe en `String(12)`.
- Añade `sede_justificacion TEXT NULL`: por qué no se puso a disposición en
  sede una notificación en papel (art. 42.1) — el tercer estado de la sede.
- `numero_intento` solo tiene sentido en POSTAL (D14): normaliza a 1 las filas
  no postales y añade `ck_notificaciones_intento_postal`. En desarrollo hay 29
  filas, todas NOTIFICA/SIR con intento 1: no choca.

No se tocan `UNIQUE(tarea_id)` ni el destinatario (N5), ni `documento_id`.

El `NOT NULL` de `fecha_puesta_disposicion` garantizaba sin decirlo el
invariante «fila ⇒ hay al menos un justificante con canal vinculado» (H5); a
partir de aquí lo garantiza el hook de NOTIFICAR (`mutaciones_arbol`).

Downgrade simétrico: las filas RECHAZADA pasan a INCORRECTA antes de restaurar
el CHECK; las dos fechas se recrean con backfill desde la `fecha_administrativa`
del documento de la fila (o `CURRENT_DATE` si no hay documento o fecha).
"""
from alembic import op


revision = '928c_notificaciones_sin_fechas'
down_revision = '928b_ttd_multiples_entradas'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('ALTER TABLE public.notificaciones DROP COLUMN fecha_puesta_disposicion')
    op.execute('ALTER TABLE public.notificaciones DROP COLUMN fecha_resultado')

    op.execute('ALTER TABLE public.notificaciones DROP CONSTRAINT ck_notificaciones_resultado')
    op.execute("""
        ALTER TABLE public.notificaciones
        ADD CONSTRAINT ck_notificaciones_resultado
        CHECK (resultado IS NULL OR resultado IN ('CORRECTA', 'RECHAZADA', 'INCORRECTA'))
    """)
    op.execute("""
        COMMENT ON COLUMN public.notificaciones.resultado IS
        'CORRECTA | RECHAZADA | INCORRECTA | NULL (sin fijar). CORRECTA y RECHAZADA dan la notificación por efectuada (art. 41.5/41.7)'
    """)

    op.execute('ALTER TABLE public.notificaciones ADD COLUMN sede_justificacion TEXT')
    op.execute("""
        COMMENT ON COLUMN public.notificaciones.sede_justificacion IS
        'Solo POSTAL: por qué no hay JUSTIFICANTE_SEDE (art. 42.1). Con texto, la sede cuenta como JUSTIFICADA'
    """)

    op.execute("UPDATE public.notificaciones SET numero_intento = 1 WHERE canal <> 'POSTAL'")
    op.execute("""
        ALTER TABLE public.notificaciones
        ADD CONSTRAINT ck_notificaciones_intento_postal
        CHECK (canal = 'POSTAL' OR numero_intento = 1)
    """)


def downgrade():
    op.execute('ALTER TABLE public.notificaciones DROP CONSTRAINT ck_notificaciones_intento_postal')
    op.execute('ALTER TABLE public.notificaciones DROP COLUMN sede_justificacion')

    op.execute("UPDATE public.notificaciones SET resultado = 'INCORRECTA' WHERE resultado = 'RECHAZADA'")
    op.execute('ALTER TABLE public.notificaciones DROP CONSTRAINT ck_notificaciones_resultado')
    op.execute("""
        ALTER TABLE public.notificaciones
        ADD CONSTRAINT ck_notificaciones_resultado
        CHECK (resultado IS NULL OR resultado IN ('CORRECTA', 'INCORRECTA'))
    """)
    op.execute("""
        COMMENT ON COLUMN public.notificaciones.resultado IS
        'CORRECTA | INCORRECTA | NULL (pendiente del justificante definitivo)'
    """)

    op.execute('ALTER TABLE public.notificaciones ADD COLUMN fecha_puesta_disposicion DATE')
    op.execute('ALTER TABLE public.notificaciones ADD COLUMN fecha_resultado DATE')
    op.execute("""
        COMMENT ON COLUMN public.notificaciones.fecha_resultado IS
        'Fecha del acto resuelto (lectura/caducidad/rechazo) — NULL mientras no hay resultado'
    """)
    op.execute("""
        UPDATE public.notificaciones n
        SET fecha_puesta_disposicion = COALESCE(d.fecha_administrativa, CURRENT_DATE),
            fecha_resultado = CASE WHEN n.resultado IS NOT NULL THEN d.fecha_administrativa END
        FROM public.documentos d
        WHERE d.id = n.documento_id
    """)
    op.execute("""
        UPDATE public.notificaciones
        SET fecha_puesta_disposicion = CURRENT_DATE
        WHERE fecha_puesta_disposicion IS NULL
    """)
    op.execute('ALTER TABLE public.notificaciones ALTER COLUMN fecha_puesta_disposicion SET NOT NULL')
