"""776_rename_comunicacion_inicio_admision

Revision ID: 776_rename_comunicacion_inicio_admision
Revises: 779_tener_por_desistido
Create Date: 2026-08-22

Issue #776 — el trámite COMUNICACION_INICIO cumple dos propósitos legales
distintos con el mismo escrito: informar del plazo máximo y el silencio
(art. 21.4 LPACAP, universal) y, para instalaciones renovables sujetas al
RD-ley 23/2020, acreditar el Hito 1 (admisión a trámite de la AAP). El nombre
original solo reflejaba el primero. Se renombra a COMUNICACION_INICIO_ADMISION
(trámite) y OFICIO_INICIO_ADMISION (tipo de documento) para que el nombre
recoja ambos propósitos, decidido por Carlos en la sesión de análisis.

Solo cambia el código y los textos legibles — ningún dato de expedientes en
curso depende de estos códigos todavía (el trámite estaba hueco, #776 lo
implementa por primera vez).
"""
from alembic import op
import sqlalchemy as sa


revision = '776_rename_comunicacion_inicio_admision'
down_revision = '779_tener_por_desistido'
branch_labels = None
depends_on = None


_CODIGO_TRAMITE_VIEJO = 'COMUNICACION_INICIO'
_CODIGO_TRAMITE_NUEVO = 'COMUNICACION_INICIO_ADMISION'
_NOMBRE_TRAMITE_VIEJO = 'Comunicación de Inicio'
_NOMBRE_TRAMITE_NUEVO = 'Comunicación de Inicio y Admisión a Trámite'
_ABREV_TRAMITE_VIEJO = 'COM. INICIO'
_ABREV_TRAMITE_NUEVO = 'COM. INICIO/ADM.'

_CODIGO_DOC_VIEJO = 'OFICIO_INICIO'
_CODIGO_DOC_NUEVO = 'OFICIO_INICIO_ADMISION'
_NOMBRE_DOC_VIEJO = 'Oficio de comunicación de inicio de expediente'
_NOMBRE_DOC_NUEVO = 'Oficio de comunicación de inicio y admisión a trámite'
_DESC_DOC_VIEJO = (
    'Escrito que comunica al titular el inicio formal de la tramitación del '
    'expediente. Fecha administrativa: fecha de firma.'
)
_DESC_DOC_NUEVO = (
    'Escrito que comunica al titular el inicio formal de la tramitación del '
    'expediente y, cuando aplica (renovables RD-ley 23/2020), acredita la '
    'admisión a trámite. Fecha administrativa: fecha de firma.'
)

_SUJETO_REGLA_VIEJO = 'ANY/ANY/ANALISIS_SOLICITUD/COMUNICACION_INICIO'
_SUJETO_REGLA_NUEVO = 'ANY/ANY/ANALISIS_SOLICITUD/COMUNICACION_INICIO_ADMISION'


def upgrade():
    conn = op.get_bind()

    conn.execute(
        sa.text("""
            UPDATE public.tipos_tramites
            SET codigo = :codigo_nuevo, nombre = :nombre_nuevo, abrev = :abrev_nuevo
            WHERE codigo = :codigo_viejo
        """),
        {
            'codigo_nuevo': _CODIGO_TRAMITE_NUEVO,
            'nombre_nuevo': _NOMBRE_TRAMITE_NUEVO,
            'abrev_nuevo': _ABREV_TRAMITE_NUEVO,
            'codigo_viejo': _CODIGO_TRAMITE_VIEJO,
        },
    )

    conn.execute(
        sa.text("""
            UPDATE public.tipos_documentos
            SET codigo = :codigo_nuevo, nombre = :nombre_nuevo, descripcion = :desc_nuevo
            WHERE codigo = :codigo_viejo
        """),
        {
            'codigo_nuevo': _CODIGO_DOC_NUEVO,
            'nombre_nuevo': _NOMBRE_DOC_NUEVO,
            'desc_nuevo': _DESC_DOC_NUEVO,
            'codigo_viejo': _CODIGO_DOC_VIEJO,
        },
    )

    conn.execute(
        sa.text("""
            UPDATE public.reglas_motor
            SET sujeto = :sujeto_nuevo
            WHERE sujeto = :sujeto_viejo
        """),
        {'sujeto_nuevo': _SUJETO_REGLA_NUEVO, 'sujeto_viejo': _SUJETO_REGLA_VIEJO},
    )


def downgrade():
    conn = op.get_bind()

    conn.execute(
        sa.text("""
            UPDATE public.reglas_motor
            SET sujeto = :sujeto_viejo
            WHERE sujeto = :sujeto_nuevo
        """),
        {'sujeto_viejo': _SUJETO_REGLA_VIEJO, 'sujeto_nuevo': _SUJETO_REGLA_NUEVO},
    )

    conn.execute(
        sa.text("""
            UPDATE public.tipos_documentos
            SET codigo = :codigo_viejo, nombre = :nombre_viejo, descripcion = :desc_viejo
            WHERE codigo = :codigo_nuevo
        """),
        {
            'codigo_viejo': _CODIGO_DOC_VIEJO,
            'nombre_viejo': _NOMBRE_DOC_VIEJO,
            'desc_viejo': _DESC_DOC_VIEJO,
            'codigo_nuevo': _CODIGO_DOC_NUEVO,
        },
    )

    conn.execute(
        sa.text("""
            UPDATE public.tipos_tramites
            SET codigo = :codigo_viejo, nombre = :nombre_viejo, abrev = :abrev_viejo
            WHERE codigo = :codigo_nuevo
        """),
        {
            'codigo_viejo': _CODIGO_TRAMITE_VIEJO,
            'nombre_viejo': _NOMBRE_TRAMITE_VIEJO,
            'abrev_viejo': _ABREV_TRAMITE_VIEJO,
            'codigo_nuevo': _CODIGO_TRAMITE_NUEVO,
        },
    )
