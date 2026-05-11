"""370_actualizar_tipos_tareas — ELABORAR in; REDACTAR/FIRMAR/INCORPORAR/PUBLICAR out

Revision ID: 370_actualizar_tipos_tareas
Revises: 345_seed_tramites_tareas
Create Date: 2026-05-11

Issue #370 (ADR-003/004/005, #371) — Actualización estructural de tipos_tareas:
- ELABORAR reemplaza a REDACTAR+FIRMAR (acto único, ADR-003)
- INCORPORAR eliminado (recepción externa pasa a ESPERAR_PLAZO.documento_producido, ADR-004)
- PUBLICAR eliminado (pasa a patrón C = ELABORAR+NOTIFICAR+EP, #371)
- ANALIZAR: habilita_tareas ahora apunta a ELABORAR (ADR-005)
"""
from alembic import op
import sqlalchemy as sa


revision = '370_actualizar_tipos_tareas'
down_revision = '345_seed_tramites_tareas'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. Eliminar catálogo de secuencias (FK tramites_tareas → tipos_tareas)
    conn.execute(sa.text("DELETE FROM public.tramites_tareas"))

    # 2. Eliminar instancias de tareas con tipos obsoletos.
    #    En BD de desarrollo son datos de seed_listado.py (expedientes AT 2001-2010).
    #    En producción con datos reales: migrar a ELABORAR antes de borrar.
    conn.execute(sa.text("""
        DELETE FROM public.tareas
        WHERE tipo_tarea_id IN (
            SELECT id FROM public.tipos_tareas
            WHERE codigo IN ('REDACTAR', 'FIRMAR', 'INCORPORAR', 'PUBLICAR')
        )
    """))

    # 3. Eliminar tipos obsoletos
    conn.execute(sa.text("""
        DELETE FROM public.tipos_tareas
        WHERE codigo IN ('REDACTAR', 'FIRMAR', 'INCORPORAR', 'PUBLICAR')
    """))

    # 4. Insertar ELABORAR
    conn.execute(sa.text("""
        INSERT INTO public.tipos_tareas (codigo, nombre)
        VALUES ('ELABORAR', 'Elaborar documento administrativo (redacción y firma en acto único)')
        ON CONFLICT (codigo) DO NOTHING
    """))


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("DELETE FROM public.tramites_tareas"))
    conn.execute(sa.text(
        "DELETE FROM public.tipos_tareas WHERE codigo = 'ELABORAR'"
    ))
    conn.execute(sa.text("""
        INSERT INTO public.tipos_tareas (codigo, nombre) VALUES
          ('REDACTAR',   'Creación de documento administrativo (borrador)'),
          ('FIRMAR',     'Firma autorizada del documento'),
          ('PUBLICAR',   'Publicación en medios oficiales'),
          ('INCORPORAR', 'Incorporación de documentación externa al sistema')
        ON CONFLICT (codigo) DO NOTHING
    """))
