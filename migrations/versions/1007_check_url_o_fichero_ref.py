"""1007_check_url_o_fichero_ref — un documento tiene contenido propio o una url, nunca las dos cosas ni ninguna

Revision ID: 1007_check_url_o_fichero_ref
Revises: 1007_almacen_ficheros
Create Date: 2026-10-07

Issue #1007 (ADR-050 §C), PR 4. Cierra el modelo de documento del almacén:

    CHECK ((url IS NULL) <> (fichero_ref IS NULL))

Un documento con contenido propio tiene `fichero_ref` y no tiene `url`; uno sin contenido propio
(un enlace `http(s)://` o un registro `bddat://`) tiene `url` y no tiene `fichero_ref`. Ni las dos
cosas, ni ninguna.

Solo el esquema: no toca ni comprueba los documentos que ya hay. Los de ruta local de las bases de
desarrollo se pasan al almacén con un script aparte, porque son datos operacionales y no
estructurales (ADR-050 §L). Un documento de ruta local sin pasar cumple la restricción (tiene
`url`), así que esta migración no depende de que ese script se haya ejecutado. PostgreSQL rechaza
añadirla solo si hubiera filas con `url` y `fichero_ref` a la vez, o con ninguna.

Downgrade: quita la restricción.
"""
from alembic import op


revision = '1007_check_url_o_fichero_ref'
down_revision = '1007_almacen_ficheros'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE public.documentos
        ADD CONSTRAINT ck_documentos_url_o_fichero_ref
        CHECK ((url IS NULL) <> (fichero_ref IS NULL))
    """)


def downgrade():
    op.execute('ALTER TABLE public.documentos DROP CONSTRAINT ck_documentos_url_o_fichero_ref')
