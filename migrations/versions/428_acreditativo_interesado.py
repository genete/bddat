"""428_acreditativo_interesado

Revision ID: 428_acreditativo_interesado
Revises: 849_seed_catalogo_pendiente
Create Date: 2026-09-05

Issue #428 — `interesados_expediente.fuente_doc_id` pasa a llamarse
`documento_acreditativo_id`.

El nombre viejo dice que hay un documento detrás, pero no de qué. Y lo que hay
detrás es siempre lo mismo para los cinco `tipo_origen` de la tabla: el documento
que ACREDITA la condición de interesado, y del que sale la fecha administrativa de
esa condición. La solicitud acredita al TITULAR, el oficio de consulta al
ORGANISMO_CONSULTADO, el escrito de personación al INTERESADO_RECONOCIDO. Con el
nombre nuevo, la columna se explica sola en los cinco casos.

Se renombra también la constraint, que PostgreSQL no arrastra: un
`ALTER TABLE ... RENAME COLUMN` deja el nombre autogenerado
`interesados_expediente_fuente_doc_id_fkey` colgando de una columna que ya no se
llama así, y el siguiente que lea el esquema buscará una columna inexistente.

Solo estructura: la columna sigue siendo nullable. El NOT NULL del acreditativo se
descartó para este issue —los otros cuatro `tipo_origen` no están implementados,
así que la constraint no tendría a quién aplicarse más que al TITULAR—.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '428_acreditativo_interesado'
down_revision = '849_seed_catalogo_pendiente'
branch_labels = None
depends_on = None

_FK_VIEJA = 'interesados_expediente_fuente_doc_id_fkey'
_FK_NUEVA = 'interesados_expediente_documento_acreditativo_id_fkey'


def upgrade():
    op.alter_column(
        'interesados_expediente', 'fuente_doc_id',
        new_column_name='documento_acreditativo_id',
        schema='public',
    )
    op.execute(
        f'ALTER TABLE public.interesados_expediente '
        f'RENAME CONSTRAINT {_FK_VIEJA} TO {_FK_NUEVA}'
    )


def downgrade():
    op.execute(
        f'ALTER TABLE public.interesados_expediente '
        f'RENAME CONSTRAINT {_FK_NUEVA} TO {_FK_VIEJA}'
    )
    op.alter_column(
        'interesados_expediente', 'documento_acreditativo_id',
        new_column_name='fuente_doc_id',
        schema='public',
    )
