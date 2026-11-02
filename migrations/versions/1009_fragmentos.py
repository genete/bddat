"""1009_fragmentos — tabla de fragmentos de escritos, con su contenido en el almacén

Revision ID: 1009_fragmentos
Revises: 1009_plantillas_fichero_ref
Create Date: 2026-11-02

Issue #1009 (ADR-050, fase 4), segundo punto. ADR-050 §C y §J, con la enmienda del
2026-11-02.

Un fragmento es un trozo de texto que comparten varias plantillas (el pie de recurso, los
fundamentos de derecho) y se cita en ellas con `{{r Nombre }}`. Hasta ahora eran ficheros
`PLANTILLAS_BASE/fragmentos/<Nombre>.odt|.docx`, sin tabla.

- `nombre`: la clave de `{{r Nombre }}`.
- `formato`: el MIME del fichero, el mismo que `ficheros.formato`. Con `nombre` forma la clave:
  un fragmento `.docx` y otro `.odt` pueden llamarse igual, porque cada motor busca el suyo.
  Lo copia el módulo de contenido del fichero ya guardado; no viene nunca de un formulario.
- `descripcion`: para quien gestiona los fragmentos.
- `activo`: `false` = fragmento retirado, que no se inserta al generar y para la generación
  equivale a ausente (ADR-050 §J: un fragmento ausente detiene la generación).
- `fichero_ref`: FK a `ficheros.ref`, obligatorio. No hay filas heredadas que desactivar,
  como en `plantillas`: la tabla nace vacía y una fila se crea al subir su fichero.

Lo que la BD no valida, a propósito: que `nombre` se pueda citar con `{{r Nombre }}`. Los dos
motores lo reconocen con `\\w+`, y el `\\w` de Postgres depende del locale; lo comprueba el
módulo de contenido al subir, con la misma expresión que los motores.

`scripts/comparar_catalogo.py` no hace falta tocarlo todavía: la tabla nace vacía en las dos
bases, y con filas solo en desarrollo el script la lista como «con filas en desarrollo y
vacías en la base migrada», sin contarla como divergencia. Cuando la semilla de tests
registre fragmentos de demostración (#1009, bloque 3) habrá que decidir cómo declararla.

Sin índice por `fichero_ref`: la tabla es pequeña (decenas de filas) y la limpieza del almacén
(#1012) la recorre entera.
"""
from alembic import op


revision = '1009_fragmentos'
down_revision = '1009_plantillas_fichero_ref'
branch_labels = None
depends_on = None


def _comentar(objeto: str, texto: str) -> None:
    # COMMENT ON no admite parámetros en el servidor: literal con las comillas escapadas.
    op.execute(f"COMMENT ON {objeto} IS '{texto.replace(chr(39), chr(39) * 2)}'")


def upgrade():
    op.execute("""
        CREATE TABLE public.fragmentos (
            id          SERIAL PRIMARY KEY,
            nombre      TEXT NOT NULL,
            formato     TEXT NOT NULL,
            descripcion TEXT,
            activo      BOOLEAN NOT NULL DEFAULT true,
            fichero_ref TEXT NOT NULL
                CONSTRAINT fk_fragmentos_fichero_ref REFERENCES public.ficheros(ref),
            CONSTRAINT uq_fragmentos_nombre_formato UNIQUE (nombre, formato)
        )
    """)
    for columna, comentario in (
        (None, 'Fragmentos de escritos: trozos de texto que comparten varias plantillas y se '
               'citan con {{r Nombre }} (ADR-050 §J)'),
        ('id', 'Identificador único autogenerado'),
        ('nombre', 'La clave de {{r Nombre }} en las plantillas. Con formato forma la clave única'),
        ('formato', 'MIME del fichero, el de ficheros.formato. Lo copia el módulo de contenido '
                    'del fichero guardado; un fragmento .docx y otro .odt pueden llamarse igual'),
        ('descripcion', 'Para quien gestiona los fragmentos'),
        ('activo', 'FALSE = fragmento retirado: no se inserta al generar (equivale a ausente)'),
        ('fichero_ref', 'Contenido del fragmento en el almacén (ADR-050 §J). Solo lo usa el '
                        'subsistema de almacenamiento'),
    ):
        _comentar('TABLE public.fragmentos' if columna is None
                  else f'COLUMN public.fragmentos.{columna}', comentario)
    op.execute('GRANT SELECT ON public.fragmentos TO claude_desktop')


def downgrade():
    op.execute('DROP TABLE public.fragmentos')
