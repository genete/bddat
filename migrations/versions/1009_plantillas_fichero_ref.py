"""1009_plantillas_fichero_ref — las plantillas ganan su contenido en el almacén y se desactivan

Revision ID: 1009_plantillas_fichero_ref
Revises: 1037_marca_edicto_notificacion
Create Date: 2026-11-02

Issue #1009 (ADR-050, fase 4), primer punto. ADR-050 §C y §J, con la enmienda del
2026-11-02.

- `plantillas.fichero_ref` (FK a `ficheros.ref`, anulable): el contenido de la plantilla en
  el almacén. Lo escribe el módulo de contenido; nadie más ve la `ref` (§B).
- Las plantillas existentes pasan a `activo = false`. Las sembraron las migraciones 402,
  403, 404, 776 y 849 con una `ruta_plantilla`, pero ninguna llegó a crear el fichero: entran
  activas y sin contenido, y generar con ellas da error. Desactivarlas no pierde nada que
  funcione, y su contexto (trámite, tipo de documento, clase de contexto) se conserva para
  que el supervisor solo tenga que subirles el fichero. No se localiza ninguna por `id`.

Primera mitad de «`ruta_plantilla` → `fichero_ref`», a propósito. Esta migración solo
**añade**: `ruta_plantilla` se queda (el motor y el alta de plantillas siguen leyéndola) y
no hay restricción nueva que impida a la gestión actual dar de alta una plantilla activa.
La segunda mitad —el `CHECK (activo = false OR fichero_ref IS NOT NULL)` y la baja de
`ruta_plantilla`— va en la migración que acompaña al corte de los consumidores (motor con
bytes y alta por subida), para que ningún commit deje un botón roto.

Downgrade: quita la columna. No devuelve `activo` a lo que era: no se sabe qué plantillas
estaban activas antes.
"""
from alembic import op
import sqlalchemy as sa


revision = '1009_plantillas_fichero_ref'
down_revision = '1037_marca_edicto_notificacion'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE public.plantillas
        ADD COLUMN fichero_ref TEXT
            CONSTRAINT fk_plantillas_fichero_ref REFERENCES public.ficheros(ref)
    """)
    op.execute("""
        COMMENT ON COLUMN public.plantillas.fichero_ref IS
        'Contenido de la plantilla en el almacén (ADR-050 §J). Solo lo usa el subsistema de almacenamiento'
    """)

    desactivadas = op.get_bind().execute(
        sa.text('UPDATE public.plantillas SET activo = false WHERE activo')
    ).rowcount
    print(f'[1009_plantillas_fichero_ref] plantillas desactivadas: {desactivadas}')


def downgrade():
    op.execute('ALTER TABLE public.plantillas DROP COLUMN IF EXISTS fichero_ref')
