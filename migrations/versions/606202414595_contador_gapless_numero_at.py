"""Contador gapless numero_at

Revision ID: 606202414595
Revises: 3f7071afb12d
Create Date: 2026-02-21 19:45:06.110103

PROPÓSITO:
    Sustituye el mecanismo MAX(numero_at)+1 del wizard por una tabla contador
    que garantiza números consecutivos sin huecos y sin race condition.

    Ver: docs/fuentesIA/numero_at_gapless.md
    Issue: #120
"""
from alembic import op
import sqlalchemy as sa


revision = '606202414595'
down_revision = '3f7071afb12d'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla contador con una única fila
    op.execute("""
        CREATE TABLE public.contador_numero_at (
            valor INTEGER NOT NULL
        )
    """)

    # Inicializar con MAX(numero_at) actual para continuar la secuencia
    # sin saltos respecto a los expedientes ya existentes.
    # En go-live, ejecutar manualmente:
    #   UPDATE public.contador_numero_at
    #   SET valor = <techo_legacy>;
    # donde <techo_legacy> es el número AT más alto de los expedientes
    # migrados desde Access, de modo que los nuevos expedientes BDDAT
    # empiecen claramente por encima del rango legacy.
    op.execute("""
        INSERT INTO public.contador_numero_at (valor)
        SELECT COALESCE(MAX(numero_at), 0)
        FROM public.expedientes
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS public.contador_numero_at")
