"""1007_almacen_ficheros — tabla ficheros y columnas del almacén en documentos

Revision ID: 1007_almacen_ficheros
Revises: 996_cert_cierre_solicitud
Create Date: 2026-10-03

Issue #1007 (ADR-050, fase 1), PR 1. ADR-050 §B y §C.

- `ficheros`: una fila por cada contenido distinto guardado en el almacén.
  Operacional (la escribe la subida, no el catálogo): está en
  `TABLAS_OPERACIONALES` de `scripts/comparar_catalogo.py`.
- `documentos` gana `nombre_fichero`, `fichero_ref` (FK a `ficheros.ref`) y
  `fecha_modificacion_fichero`, y `url` admite NULL: desde el corte (PR 4), un
  documento con contenido propio no tiene url.
- `nombre_fichero` se rellena solo en los documentos de ruta local (§C: los
  `bddat://` y `http(s)://` toman el nombre del tipo o de la URL): el último tramo de la url,
  sin el prefijo del pool `<md5[:n]>_`. La regla es la de
  `rutas_esftt._nombre_original_pool`, copiada aquí porque una migración no
  importa código de la aplicación, y esa función se retira en el PR 5.

Nadie tiene `fichero_ref` todavía: los documentos pasan al almacén con el script
del PR 4 (§L).

Downgrade: devuelve `url` a NOT NULL, y por eso falla si ya hay documentos sin
url. Los habrá tras el PR 4, cuya migración es de ida (§L).
"""
from alembic import op
import sqlalchemy as sa


revision = '1007_almacen_ficheros'
down_revision = '996_cert_cierre_solicitud'
branch_labels = None
depends_on = None

# rutas_esftt._LONGITUD_PREFIJO_HASH en el momento de la migración.
_LONGITUD_PREFIJO_MIN = 8

_COMENTARIO_URL = (
    'http(s):// o bddat://<recurso>/<id> (ADR-006); ruta local hasta el corte de '
    'ADR-050 (#1007). NULL si tiene contenido propio (fichero_ref)'
)
_COMENTARIO_URL_ANTERIOR = 'Ruta o URL del archivo físico en sistema de archivos o repositorio'


def _comentar(objeto: str, texto: str) -> None:
    # COMMENT ON no admite parámetros en el servidor: literal con las comillas escapadas.
    op.execute(f"COMMENT ON {objeto} IS '{texto.replace(chr(39), chr(39) * 2)}'")


def _nombre_desde_url(url: str, hash_md5) -> str:
    """Último tramo de la url, sin el prefijo `<md5[:n]>_` del pool si lo lleva."""
    nombre = url.replace('\\', '/').rsplit('/', 1)[-1]
    if hash_md5:
        for n in range(_LONGITUD_PREFIJO_MIN, len(hash_md5) + 1):
            prefijo = hash_md5[:n] + '_'
            if nombre.startswith(prefijo):
                return nombre[len(prefijo):] or nombre
    return nombre


def upgrade():
    op.execute("""
        CREATE TABLE public.ficheros (
            ref                   TEXT PRIMARY KEY,
            contenido_sha256      CHAR(64) NOT NULL,
            tamano                BIGINT NOT NULL,
            formato               TEXT NOT NULL,
            fecha_creacion        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            fecha_verificacion    TIMESTAMP WITH TIME ZONE,
            estado                VARCHAR(10) NOT NULL DEFAULT 'OK',
            fecha_sin_referencias TIMESTAMP WITH TIME ZONE,
            CONSTRAINT uq_ficheros_contenido_sha256 UNIQUE (contenido_sha256),
            CONSTRAINT ck_ficheros_sha256 CHECK (contenido_sha256 ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_ficheros_tamano CHECK (tamano >= 0),
            CONSTRAINT ck_ficheros_estado CHECK (estado IN ('OK', 'CORRUPTO', 'AUSENTE'))
        )
    """)
    for columna, comentario in (
        (None, 'Contenidos guardados en el almacén, uno por contenido distinto (ADR-050 §B, §C). '
               'Solo la usa el subsistema de almacenamiento'),
        ('ref', 'Lo que devuelve el almacén para volver a encontrar el contenido. '
                'Opaca para el resto de BDDAT'),
        ('contenido_sha256', 'SHA-256 del contenido, calculado por BDDAT. '
                             'Deduplicación, aviso de duplicado e integridad'),
        ('tamano', 'Tamaño en bytes'),
        ('formato', 'MIME detectado por el contenido, no por la extensión (ADR-050 §E)'),
        ('fecha_creacion', 'Cuándo se guardó por primera vez'),
        ('fecha_verificacion', 'Última comprobación de integridad (fase 7)'),
        ('estado', 'OK | CORRUPTO | AUSENTE. Un contenido que no está OK no se usa '
                   'ni se vincula (ADR-050 §G)'),
        ('fecha_sin_referencias', 'Desde cuándo no lo referencia nada: el reloj de la '
                                  'limpieza (fase 7)'),
    ):
        _comentar('TABLE public.ficheros' if columna is None
                  else f'COLUMN public.ficheros.{columna}', comentario)
    op.execute('GRANT SELECT ON public.ficheros TO claude_desktop')

    op.execute("""
        ALTER TABLE public.documentos
        ADD COLUMN nombre_fichero TEXT,
        ADD COLUMN fichero_ref TEXT
            CONSTRAINT fk_documentos_fichero_ref REFERENCES public.ficheros(ref),
        ADD COLUMN fecha_modificacion_fichero TIMESTAMP WITH TIME ZONE
    """)
    op.execute('CREATE INDEX idx_documentos_fichero_ref ON public.documentos (fichero_ref)')
    op.execute('ALTER TABLE public.documentos ALTER COLUMN url DROP NOT NULL')
    for columna, comentario in (
        ('url', _COMENTARIO_URL),
        ('nombre_fichero', 'Nombre visible y de descarga del fichero (ADR-050 §C). NULL en '
                           'los que tienen url: lo toman del tipo o de la URL'),
        ('fichero_ref', 'Contenido actual en el almacén (ADR-050 §B). Solo lo usa el '
                        'subsistema de almacenamiento'),
        ('fecha_modificacion_fichero', 'Cuándo cambió por última vez el fichero del documento '
                                       '(getlastmodified del WebDAV, ADR-050 §D)'),
    ):
        _comentar(f'COLUMN public.documentos.{columna}', comentario)

    conexion = op.get_bind()
    locales = conexion.execute(sa.text(
        "SELECT id, url, hash_md5 FROM public.documentos "
        "WHERE url IS NOT NULL AND position('://' in url) = 0"
    )).fetchall()
    if locales:
        conexion.execute(
            sa.text('UPDATE public.documentos SET nombre_fichero = :nombre WHERE id = :id'),
            [{'id': d.id, 'nombre': _nombre_desde_url(d.url, d.hash_md5)} for d in locales],
        )


def downgrade():
    op.execute('ALTER TABLE public.documentos ALTER COLUMN url SET NOT NULL')
    _comentar('COLUMN public.documentos.url', _COMENTARIO_URL_ANTERIOR)
    op.execute('DROP INDEX IF EXISTS public.idx_documentos_fichero_ref')
    op.execute("""
        ALTER TABLE public.documentos
        DROP COLUMN fecha_modificacion_fichero,
        DROP COLUMN fichero_ref,
        DROP COLUMN nombre_fichero
    """)
    op.execute('DROP TABLE public.ficheros')
