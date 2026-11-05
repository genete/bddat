"""1009_plantillas_activa_fichero — una plantilla activa tiene fichero; fuera `ruta_plantilla`

Revision ID: 1009_plantillas_activa_fichero
Revises: 1009_fragmentos
Create Date: 2026-11-05

Issue #1009 (ADR-050, fase 4), cierre de «`ruta_plantilla` → `fichero_ref`». ADR-050 §J, con la
enmienda del 2026-11-03: `activo` es la pausa que escribe el supervisor, y **no se puede activar
una plantilla sin fichero**.

La primera migración (`1009_plantillas_fichero_ref`) solo añadió `fichero_ref` y dejó
`ruta_plantilla` a propósito: el motor y el alta seguían leyéndola. Con este commit el motor
trabaja con bytes del almacén y el alta sube el fichero desde el navegador, así que ningún
consumidor lee ya `ruta_plantilla`, y esta migración la quita y pone la restricción.

1. **Desactiva las plantillas activas sin fichero**, para que la restricción no falle. En una
   base que viene de la primera migración no hay ninguna (las desactivó todas), pero entre una
   migración y otra la gestión antigua pudo dar de alta o activar alguna: sin fichero en el
   almacén no se puede generar con ella, y activa mentía.
2. **`CHECK (NOT activo OR fichero_ref IS NOT NULL)`** (`ck_plantillas_activa_con_fichero`): la
   garantía de «no se activa sin fichero» que la gestión ya aplica con su mensaje, puesta
   también en la BD, donde no la salta ninguna ruta nueva.
3. **Quita `ruta_plantilla`.** Era la ruta relativa bajo `PLANTILLAS_BASE/plantillas/`, y esa
   raíz desaparece de la configuración. Los registros no pierden nada que funcionara: ninguna
   plantilla tiene fichero en el almacén todavía (se desactivaron en la primera migración),
   así que su ruta solo servía para saber qué fichero había que volver a subir, y las
   migraciones que las sembraron (402, 403, 404, 776, 849) conservan esos nombres.
4. Actualiza el comentario de `activo`: ya no es «oculta en la tarea ELABORAR», es la pausa del
   supervisor, y que se pueda usar se calcula.

Downgrade: quita la restricción y devuelve `ruta_plantilla` anulable y vacía (no se sabe qué
ruta tenía cada plantilla, y el almacén no guarda nombres). No reactiva ninguna plantilla.
"""
from alembic import op
import sqlalchemy as sa


revision = '1009_plantillas_activa_fichero'
down_revision = '1009_fragmentos'
branch_labels = None
depends_on = None


def _comentar(objeto: str, texto: str) -> None:
    # COMMENT ON no admite parámetros en el servidor: literal con las comillas escapadas.
    op.execute(f"COMMENT ON {objeto} IS '{texto.replace(chr(39), chr(39) * 2)}'")


def upgrade():
    desactivadas = op.get_bind().execute(
        sa.text('UPDATE public.plantillas SET activo = false WHERE activo AND fichero_ref IS NULL')
    ).rowcount
    print(f'[1009_plantillas_activa_fichero] plantillas activas sin fichero desactivadas: {desactivadas}')

    op.execute("""
        ALTER TABLE public.plantillas
        ADD CONSTRAINT ck_plantillas_activa_con_fichero
        CHECK (NOT activo OR fichero_ref IS NOT NULL)
    """)
    op.execute('ALTER TABLE public.plantillas DROP COLUMN ruta_plantilla')
    _comentar(
        'COLUMN public.plantillas.activo',
        'Pausa del supervisor (ADR-050 §J): FALSE = no se usa para generar, aunque se conserve. '
        'Solo la escribe el supervisor y sin fichero no puede estar activa (CHECK). Que se pueda '
        'usar se calcula: activa, con fichero y su contenido en buen estado',
    )


def downgrade():
    op.execute('ALTER TABLE public.plantillas ADD COLUMN ruta_plantilla TEXT')
    op.execute('ALTER TABLE public.plantillas DROP CONSTRAINT IF EXISTS ck_plantillas_activa_con_fichero')
    _comentar(
        'COLUMN public.plantillas.ruta_plantilla',
        'Ruta relativa a PLANTILLAS_BASE/plantillas/',
    )
    _comentar(
        'COLUMN public.plantillas.activo',
        'FALSE = oculta en tarea ELABORAR pero conservada para histórico',
    )
