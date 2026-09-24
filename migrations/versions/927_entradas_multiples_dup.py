"""927_entradas_multiples_dup — entradas múltiples de los pasos de DATOS_CATASTRALES

Revision ID: 927_entradas_multiples_dup
Revises: 928c_notificaciones_sin_fechas
Create Date: 2026-09-24

Issue #927. `914_tramites_tareas_docs` no pudo declarar estas entradas porque
la PK (tipo_tramite_id, orden_tarea, rol) solo admitía un tipo de documento de
entrada por paso. `928b_ttd_multiples_entradas` la sustituyó por `id` + índice
único funcional, así que ya caben. Fuente: `nota` de cada trámite en
ESTRUCTURA_FTT.json (y DISEÑO_RESOLUCION_DUP.md §2):

  - SOLICITUD_CATASTRALES.ANALIZAR consume XML_PARA_CATASTRO + DR_DATOS_CATASTRALES
    (este solo «si se aportó en origen»: obligatorio=false). El SOLICITUD
    genérico que cita la fuente no tiene tipo de documento identificable y no
    se declara.
  - REQUERIMIENTO_CATASTRALES.ELABORAR consume el DIAGNOSTICO de la ronda previa.
  - REMISION_ACUERDO_DATOS.ELABORAR consume XML_DE_CATASTRO + DR_DATOS_CATASTRALES
    + el DIAGNOSTICO favorable que habilita el trámite.
  - ANALISIS_RBDA.ANALIZAR consume RBDA + RBDA_DIRECCIONES.

Fuera de alcance, con issue propio: #936 (ELABORACION de RESOLUCION_DUP consume
RBDA_DEFINITIVA, pero el trámite se comparte con RESOLUCION y esta tabla no
distingue por fase). Sin definir en la fuente: la ENTRADA de
REQUERIMIENTO_CATASTRALES.ANALIZAR (orden 4).

Coste conocido (#935): `sugerencia_subida` junta los tipos exactos de ENTRADA y
SALIDA del paso y, si no es uno solo, no sugiere. Estos cuatro pasos dejan de
recibir sugerencia de tipo (antes: ACUERDO_CESION_CATASTRALES en
REMISION.ELABORAR; DIAGNOSTICO en los otros tres).

Las filas se resuelven por código de trámite y de documento, nunca por id.
"""
from alembic import op
import sqlalchemy as sa


revision = '927_entradas_multiples_dup'
down_revision = '928c_notificaciones_sin_fechas'
branch_labels = None
depends_on = None

# (tipo_tramite.codigo, orden_tarea, tipo_documento.codigo, obligatorio)
_ENTRADAS = [
    ('SOLICITUD_CATASTRALES', 1, 'XML_PARA_CATASTRO', True),
    ('SOLICITUD_CATASTRALES', 1, 'DR_DATOS_CATASTRALES', False),
    ('REQUERIMIENTO_CATASTRALES', 1, 'DIAGNOSTICO', True),
    ('REMISION_ACUERDO_DATOS', 1, 'XML_DE_CATASTRO', True),
    ('REMISION_ACUERDO_DATOS', 1, 'DR_DATOS_CATASTRALES', True),
    ('REMISION_ACUERDO_DATOS', 1, 'DIAGNOSTICO', True),
    ('ANALISIS_RBDA', 1, 'RBDA', True),
    ('ANALISIS_RBDA', 1, 'RBDA_DIRECCIONES', True),
]


def upgrade():
    conn = op.get_bind()
    for tramite_codigo, orden_tarea, doc_codigo, obligatorio in _ENTRADAS:
        # INSERT ... SELECT: si un código no existe insertaría 0 filas sin
        # avisar, así que se comprueba el rowcount y se aborta.
        res = conn.execute(sa.text("""
            INSERT INTO public.tramites_tareas_documentos
                (tipo_tramite_id, orden_tarea, rol, tipo_documento_id, obligatorio)
            SELECT tt.id, :orden_tarea, 'ENTRADA', td.id, :obligatorio
            FROM public.tipos_tramites tt, public.tipos_documentos td
            WHERE tt.codigo = :tramite_codigo AND td.codigo = :doc_codigo
            ON CONFLICT DO NOTHING
        """), {'tramite_codigo': tramite_codigo, 'orden_tarea': orden_tarea,
               'doc_codigo': doc_codigo, 'obligatorio': obligatorio})
        if res.rowcount != 1:
            raise ValueError(
                f"No se pudo declarar ENTRADA {doc_codigo} en "
                f"{tramite_codigo}#{orden_tarea} (ausente o ya existente) — migración abortada"
            )


def downgrade():
    conn = op.get_bind()
    for tramite_codigo, orden_tarea, doc_codigo, _obligatorio in _ENTRADAS:
        conn.execute(sa.text("""
            DELETE FROM public.tramites_tareas_documentos ttd
            USING public.tipos_tramites tt, public.tipos_documentos td
            WHERE ttd.tipo_tramite_id = tt.id
              AND ttd.tipo_documento_id = td.id
              AND tt.codigo = :tramite_codigo
              AND ttd.orden_tarea = :orden_tarea
              AND ttd.rol = 'ENTRADA'
              AND td.codigo = :doc_codigo
        """), {'tramite_codigo': tramite_codigo, 'orden_tarea': orden_tarea,
               'doc_codigo': doc_codigo})
