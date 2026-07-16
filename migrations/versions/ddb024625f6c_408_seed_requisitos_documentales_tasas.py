"""408 seed requisitos documentales tasas

Revision ID: ddb024625f6c
Revises: 0bd1626c0f09
Create Date: 2026-07-16 11:03:50.974325

Issue #408 — Primer bloque de requisitos_documentales: los documentos base
de toda solicitud (identidad/representación + proyecto) y la justificación
de la tasa (art. 45.1 Ley 10/2021), que desbloquea la regla de motor #582
(hoy inerte por catálogo vacío — ver tasa_impagada en
app/services/variables/calculado.py).

Catálogo PARCIAL, para desarrollo — no es el catálogo definitivo de
producción. Queda pendiente el estudio andaluz completo de documentación
requerida (resto del alcance de #408); issue se cierra con Refs, no Closes,
hasta entonces.

tipos_documentos nuevos (origen EXTERNO — aportados por el titular):
    MODELO_SOLICITUD, ESCRITURAS_SOCIEDAD, CIF_NIF, PODER_REPRESENTACION,
    MODELO_046, MODELO_909, JUSTIFICANTE_PAGO_TASA
Reutiliza DOC_PROYECTO (#337) para el proyecto técnico — no crea tipo nuevo.

Modelo 046 y 909 son obligatorios sin condición. El justificante de pago
se modela también como requisito universal, sin condiciones_requisito:
tasa_impagada (calculado.py, #582) no evalúa condiciones — cuenta como
obligatorio cualquier RequisitoDocumental activo de este tipo, aplique o
no la condición. Cuando el 909 se presente ya mecanizado, el técnico
vincula ese mismo documento también al requisito JUSTIFICANTE_PAGO_TASA
(documentos_requisito no impone unicidad por documento_id, solo por
(requisito_id, solicitud_id) — ver #583/UI de #495).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ddb024625f6c'
down_revision = '0bd1626c0f09'
branch_labels = None
depends_on = None

# (codigo, nombre, origen) — nuevos tipos_documentos que aporta el titular
_TIPOS_NUEVOS = [
    ('MODELO_SOLICITUD',       'Modelo de solicitud de autorización de instalación', 'EXTERNO'),
    ('ESCRITURAS_SOCIEDAD',    'Escrituras de constitución de la sociedad',           'EXTERNO'),
    ('CIF_NIF',                'CIF/NIF del solicitante',                            'EXTERNO'),
    ('PODER_REPRESENTACION',   'Poder de representación',                            'EXTERNO'),
    ('MODELO_046',             'Modelo 046 de autoliquidación de tasa',              'EXTERNO'),
    ('MODELO_909',             'Modelo 909 de declaración de instalación',           'EXTERNO'),
    ('JUSTIFICANTE_PAGO_TASA', 'Justificante de pago de la tasa',                    'EXTERNO'),
]

# (codigo_tipo_documento, descripcion_legal, orden, cita_norma)
# cita_norma=True → norma_id apunta a LEY_10_2021_TASAS (ya sembrada en #582)
_REQUISITOS = [
    ('MODELO_SOLICITUD',
     'Modelo de solicitud de autorización de instalación, cumplimentado y firmado '
     'por el titular o su representante.',
     1, False),
    ('ESCRITURAS_SOCIEDAD',
     'Escritura de constitución de la sociedad, cuando el solicitante sea persona '
     'jurídica.',
     2, False),
    ('CIF_NIF',
     'CIF/NIF del solicitante.',
     3, False),
    ('PODER_REPRESENTACION',
     'Documento acreditativo del poder de representación, cuando la solicitud se '
     'presente mediante representante.',
     4, False),
    ('MODELO_046',
     'Modelo 046 de autoliquidación de tasa, cumplimentado. Obligatorio en toda '
     'solicitud.',
     5, True),
    ('MODELO_909',
     'Modelo 909 de declaración de instalación, cumplimentado. Obligatorio en toda '
     'solicitud.',
     6, True),
    ('JUSTIFICANTE_PAGO_TASA',
     'Justificante de pago de la tasa. Si el modelo 909 se presenta ya mecanizado '
     '(validado por la entidad bancaria), el mismo documento cubre este requisito; '
     'si no, debe aportarse el justificante por separado.',
     7, True),
    ('DOC_PROYECTO',
     'Proyecto técnico de la instalación, suscrito por técnico competente.',
     8, False),
]


def upgrade():
    conn = op.get_bind()

    for codigo, nombre, origen in _TIPOS_NUEVOS:
        conn.execute(sa.text("""
            INSERT INTO public.tipos_documentos (codigo, nombre, origen)
            VALUES (:codigo, :nombre, :origen)
            ON CONFLICT (codigo) DO NOTHING
        """), {'codigo': codigo, 'nombre': nombre, 'origen': origen})

    for codigo_tipo, descripcion, orden, cita_norma in _REQUISITOS:
        if cita_norma:
            conn.execute(sa.text("""
                INSERT INTO public.requisitos_documentales
                    (tipo_documento_id, descripcion_legal, norma_id, orden)
                SELECT td.id, :descripcion, n.id, :orden
                FROM public.tipos_documentos td
                CROSS JOIN public.normas n
                WHERE td.codigo = :codigo_tipo
                  AND n.codigo = 'LEY_10_2021_TASAS'
                  AND NOT EXISTS (
                      SELECT 1 FROM public.requisitos_documentales rd
                      WHERE rd.tipo_documento_id = td.id
                  )
            """), {'codigo_tipo': codigo_tipo, 'descripcion': descripcion, 'orden': orden})
        else:
            conn.execute(sa.text("""
                INSERT INTO public.requisitos_documentales
                    (tipo_documento_id, descripcion_legal, orden)
                SELECT td.id, :descripcion, :orden
                FROM public.tipos_documentos td
                WHERE td.codigo = :codigo_tipo
                  AND NOT EXISTS (
                      SELECT 1 FROM public.requisitos_documentales rd
                      WHERE rd.tipo_documento_id = td.id
                  )
            """), {'codigo_tipo': codigo_tipo, 'descripcion': descripcion, 'orden': orden})


def downgrade():
    conn = op.get_bind()

    codigos_requisito = [r[0] for r in _REQUISITOS]
    conn.execute(sa.text("""
        DELETE FROM public.requisitos_documentales
        WHERE tipo_documento_id IN (
            SELECT id FROM public.tipos_documentos WHERE codigo = ANY(:codigos)
        )
    """), {'codigos': codigos_requisito})

    codigos_nuevos = [t[0] for t in _TIPOS_NUEVOS]
    conn.execute(
        sa.text("DELETE FROM public.tipos_documentos WHERE codigo = ANY(:codigos)"),
        {'codigos': codigos_nuevos}
    )
