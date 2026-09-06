"""428b_ancla_solicitud_obligatoria

Revision ID: 428b_ancla_solicitud
Revises: 428_acreditativo_interesado
Create Date: 2026-09-06

Issue #428 — `solicitudes.documento_solicitud_id` pasa a NOT NULL.

Es la clave de bóveda del issue: mientras la columna admitiera NULL, una solicitud
podía nacer sin el escrito que la abre, y con ella un procedimiento cuyo plazo del
art. 128 RD 1955/2000 nunca empieza a contar. Antes de esta migración eso no era
hipotético — ninguna de las 12 solicitudes de desarrollo tenía ancla, porque
ninguna vía de la aplicación la escribía.

Va al final del issue a propósito: solo es segura cuando las dos vías de alta
escriben el dato (`alta_expediente` y `mutaciones_arbol.crear_solicitud`) y los
datos existentes están saneados.

LA REGLA DE BORRADO, QUE HABÍA QUE CAMBIAR CON ELLA
===================================================

La FK nació en `b7f95d61a7a9` como `ON DELETE SET NULL`, a diferencia de sus dos
hermanas —`documento_cierre_id` y `documento_fin_instruccion_id`—, que son NO
ACTION. Esa combinación es incoherente con NOT NULL: al borrar el documento,
PostgreSQL intentaría escribir NULL en una columna que no lo admite, y el error
saldría en tiempo de borrado, lejos de aquí y sin explicar nada.

Así que la FK se recrea como NO ACTION, igualándola a las otras dos anclas. No
deja el borrado desprotegido: el pool ya se niega a borrar un documento anclado y
además dice cuál es la solicitud que lo usa (`_motivo_ancla`, #838), y
`limpiar_reciclables.py` borra las solicitudes antes que los documentos.

Sin `server_default` ni relleno de huérfanas a propósito: si quedara alguna, el
`ALTER` debe fallar aquí y no inventarse un ancla que nadie ha elegido.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '428b_ancla_solicitud'
down_revision = '428_acreditativo_interesado'
branch_labels = None
depends_on = None

_FK = 'fk_solicitudes_documento_solicitud'


def upgrade():
    # La FK vieja no tiene nombre propio: la creó un ALTER TABLE ... REFERENCES
    # sin CONSTRAINT, así que PostgreSQL la nombró él. Se localiza por columna en
    # vez de adivinar el nombre, que difiere entre instalaciones.
    op.execute("""
        DO $$
        DECLARE nombre text;
        BEGIN
            SELECT c.conname INTO nombre
            FROM pg_constraint c
            JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
            WHERE c.contype = 'f'
              AND c.conrelid = 'public.solicitudes'::regclass
              AND a.attname = 'documento_solicitud_id';
            IF nombre IS NOT NULL THEN
                EXECUTE format('ALTER TABLE public.solicitudes DROP CONSTRAINT %I', nombre);
            END IF;
        END $$;
    """)

    op.create_foreign_key(
        _FK, 'solicitudes', 'documentos',
        ['documento_solicitud_id'], ['id'],
        source_schema='public', referent_schema='public',
    )

    op.alter_column(
        'solicitudes', 'documento_solicitud_id',
        existing_type=sa.Integer(), nullable=False,
        schema='public',
    )


def downgrade():
    op.alter_column(
        'solicitudes', 'documento_solicitud_id',
        existing_type=sa.Integer(), nullable=True,
        schema='public',
    )
    op.drop_constraint(_FK, 'solicitudes', schema='public', type_='foreignkey')
    op.execute("""
        ALTER TABLE public.solicitudes
            ADD CONSTRAINT solicitudes_documento_solicitud_id_fkey
            FOREIGN KEY (documento_solicitud_id)
            REFERENCES public.documentos(id) ON DELETE SET NULL
    """)
