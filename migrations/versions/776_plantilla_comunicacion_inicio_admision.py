"""776_plantilla_comunicacion_inicio_admision

Revision ID: 776_plantilla_comunicacion_inicio_admision
Revises: 776_rename_comunicacion_inicio_admision
Create Date: 2026-08-22

Issue #776 — el trámite COMUNICACION_INICIO_ADMISION existía en el catálogo
ESFTT (regla 35 lo gobierna desde #455) pero no tenía plantilla: ELABORAR no
tenía nada que ofrecer. Alta de la plantilla con su Context Builder
(ContextoComunicacionInicioAdmision) y el tipo de documento OFICIO_INICIO_ADMISION
(renombrado en la migración anterior).

La redacción administrativa definitiva queda fuera de alcance (#444): esta
plantilla es un esqueleto con los tokens del CB (plazo_maximo_resolucion,
unidad_plazo, norma_plazo, efecto_silencio, fecha_recepcion_solicitud). El
párrafo condicionado del RD-ley 23/2020 para renovables queda diferido a
#780 (variable es_renovable_rdl23, aún sin dato de fecha_permiso_acceso).
"""
from alembic import op
import sqlalchemy as sa


revision = '776_plantilla_comunicacion_inicio_admision'
down_revision = '776_rename_comunicacion_inicio_admision'
branch_labels = None
depends_on = None


_CODIGO = 'COMUNICACION_INICIO_ADMISION'


def upgrade():
    conn = op.get_bind()

    conn.execute(
        sa.text("""
            INSERT INTO public.plantillas
                (codigo, nombre, descripcion, ruta_plantilla, contexto_clase,
                 tipo_documento_id, tipo_tramite_id, activo)
            VALUES (
                :codigo,
                'Comunicación de inicio y admisión a trámite',
                'Informa del plazo máximo para resolver y notificar y del '
                'efecto del silencio administrativo (art. 21.4 LPACAP). Para '
                'renovables sujetas al RD-ley 23/2020 acredita además el '
                'Hito 1 (admisión a trámite de la AAP) — párrafo condicionado '
                'pendiente de #780.',
                'escritos/comunicacion_inicio_admision.docx',
                'ContextoComunicacionInicioAdmision',
                (SELECT id FROM public.tipos_documentos WHERE codigo = 'OFICIO_INICIO_ADMISION'),
                (SELECT id FROM public.tipos_tramites WHERE codigo = :codigo),
                TRUE
            )
        """),
        {'codigo': _CODIGO},
    )


def downgrade():
    conn = op.get_bind()

    conn.execute(
        sa.text("DELETE FROM public.plantillas WHERE codigo = :codigo"),
        {'codigo': _CODIGO},
    )
