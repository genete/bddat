"""1040_comentario_documento_principal — el comentario de proyectos.documento_principal_id deja de decir que llega al pool

Revision ID: 1040_comentario_documento_principal
Revises: 1009_plantillas_activa_fichero
Create Date: 2026-11-06

Issue #1040 (ADR-044 §D, enmienda del 2026-11-06). Solo cambia el comentario de la columna:
no toca datos ni estructura.

El comentario decía que `documento_principal_id` es «NULL hasta que llega al pool: en el alta el
único documento que entra es el escrito de solicitud». Desde #1040 el alta sube también el
proyecto técnico y lo ancla en la misma transacción, así que eso ya no es verdad: la columna solo
es NULL en un expediente heredado sin proyecto, y el principal no se reclasifica ni se suelta (solo
se sustituye su fichero).

Downgrade: devuelve el comentario anterior.
"""
from alembic import op


revision = '1040_comentario_documento_principal'
down_revision = '1009_plantillas_activa_fichero'
branch_labels = None
depends_on = None


COLUMNA = 'COLUMN public.proyectos.documento_principal_id'

COMENTARIO_NUEVO = (
    'FK a DOCUMENTOS. El DOC_PROYECTO que materializa el proyecto (ADR-044 §D). Lo sube el alta '
    'de expediente y queda anclado (#1040); no se reclasifica ni se suelta, solo se sustituye su '
    'fichero. NULL solo en un expediente heredado sin proyecto. Sin él, el sistema no sabe si un '
    'DOC_PROYECTO posterior abre reformado y el motor bloquea seguir la solicitud'
)

# El que dejó la migración 887 en la BD. El del modelo era más largo («…en el alta el único
# documento que entra es el escrito de solicitud…») y la BD nunca llegó a tenerlo.
COMENTARIO_ANTERIOR = (
    'FK a DOCUMENTOS. El DOC_PROYECTO que materializa el proyecto (ADR-044 §D). '
    'NULL hasta que llega al pool'
)


def _comentar(texto: str) -> None:
    # COMMENT ON no admite parámetros en el servidor: literal con las comillas escapadas.
    op.execute(f"COMMENT ON {COLUMNA} IS '{texto.replace(chr(39), chr(39) * 2)}'")


def upgrade():
    _comentar(COMENTARIO_NUEVO)


def downgrade():
    _comentar(COMENTARIO_ANTERIOR)
