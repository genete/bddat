"""777_variables_representacion_dup_y_descripciones_tipos_documentos

Revision ID: 5eb35f788ab2
Revises: 91a701524476
Create Date: 2026-08-23 09:35:00.000000

Issue #777 — condiciones_requisito vacía: prepara el terreno para poblar
(vía CRUD de #583, fuera de esta migración) las condiciones de
ESCRITURAS_SOCIEDAD, PODER_REPRESENTACION y DR_NO_DUP.

1. Tres variables nuevas en catalogo_variables (función en
   app/services/variables/calculado.py):
   - solicitud_incluye_dup
   - solicitante_es_persona_juridica (sobre el TITULAR, no el solicitante)
   - solicitud_por_representante (titular actual, sin histórico — ver
     docstring de la función)

2. Rename tipos_documentos.codigo 'CIF_NIF' -> 'NIF_TITULAR': "CIF" quedó
   obsoleto desde la Orden EHA/451/2008, todo es NIF; y el documento se
   refiere al NIF del titular, no de quien meramente tramita la solicitud.
   Único uso de 'CIF_NIF' en el código era esta misma migración semilla
   (ddb024625f6c_408), sin más referencias.

3. Pobla tipos_documentos.descripcion, hasta ahora NULL en 9 filas: las 7
   sembradas en #408 (MODELO_SOLICITUD, ESCRITURAS_SOCIEDAD, NIF_TITULAR,
   PODER_REPRESENTACION, MODELO_046, MODELO_909, JUSTIFICANTE_PAGO_TASA) más
   CERT_PLAZO_TABLON y CONDICIONADO_OFICIO (ajenas a #408, aprovechando que
   se toca la tabla).
"""
from alembic import op
import sqlalchemy as sa


revision = '5eb35f788ab2'
down_revision = '91a701524476'
branch_labels = None
depends_on = None

_VARIABLES = [
    ('solicitud_incluye_dup',
     'Solicitud incluye tipo DUP', 'boolean'),
    ('solicitante_es_persona_juridica',
     'Titular es persona jurídica (según NIF)', 'boolean'),
    ('solicitud_por_representante',
     'Titular actúa por persona con poder de representación', 'boolean'),
]

_RENAME_CODIGO_ANTERIOR = 'CIF_NIF'
_RENAME_CODIGO_NUEVO = 'NIF_TITULAR'
_RENAME_NOMBRE_NUEVO = 'NIF del titular'
_RENAME_NOMBRE_ANTERIOR = 'CIF/NIF del solicitante'

# (codigo, descripcion)
_DESCRIPCIONES = [
    ('MODELO_SOLICITUD',
     'Modelo oficial de solicitud de autorización de instalación, cumplimentado '
     'y firmado por el titular o su representante. Documento de apertura del '
     'expediente. Fecha administrativa: fecha de registro de entrada.'),
    ('ESCRITURAS_SOCIEDAD',
     'Escritura de constitución de la sociedad titular, cuando ésta sea persona '
     'jurídica. Acredita su existencia y capacidad de obrar. Fecha '
     'administrativa: fecha de registro de entrada.'),
    (_RENAME_CODIGO_NUEVO,
     'Documento acreditativo del NIF del titular: DNI/NIE si es persona '
     'física, NIF de persona jurídica si es persona jurídica — el concepto de '
     'CIF quedó unificado bajo la denominación NIF (Orden EHA/451/2008). Fecha '
     'administrativa: fecha de registro de entrada.'),
    ('PODER_REPRESENTACION',
     'Documento acreditativo del poder de representación, cuando la solicitud '
     'se presente mediante representante distinto del titular. Fecha '
     'administrativa: fecha de registro de entrada.'),
    ('MODELO_046',
     'Modelo 046 de autoliquidación de tasa, cumplimentado por el solicitante. '
     'Obligatorio en toda solicitud (art. 45.1 Ley 10/2021). Fecha '
     'administrativa: fecha de registro de entrada.'),
    ('MODELO_909',
     'Modelo 909, carta de pago de la tasa, cumplimentado. Obligatorio en toda '
     'solicitud (art. 45.1 Ley 10/2021). Cuando se presenta ya mecanizado '
     '(validado por la entidad bancaria), el mismo documento cubre también '
     'JUSTIFICANTE_PAGO_TASA. Fecha administrativa: fecha de registro de '
     'entrada.'),
    ('JUSTIFICANTE_PAGO_TASA',
     'Justificante de pago de la tasa. Si el modelo 909 se presenta ya '
     'mecanizado, el mismo documento cubre este requisito; si no, debe '
     'aportarse por separado. Fecha administrativa: fecha de registro de '
     'entrada.'),
    ('CERT_PLAZO_TABLON',
     'Certificado del ayuntamiento que acredita la exposición del anuncio en '
     'su tablón de edictos, comunicado cuando el período ya ha concluido (30 '
     'días naturales, art. 125 RD 1955/2000). Caso retroactivo: es el '
     'documento PRODUCIDO del trámite, no un consumido de entrada — el '
     'ESPERAR_PLAZO queda completado retroactivamente al incorporarlo. Fecha '
     'administrativa: fecha de inicio de la exposición, no de recepción del '
     'certificado.'),
    ('CONDICIONADO_OFICIO',
     'Documento de trabajo interno producido por el tramitador cuando el '
     'organismo consultado respondió "condicionado" y el titular no respondió '
     'al traslado en un expediente AAC. Recoge los condicionados pasados a '
     'limpio.'),
]


def upgrade():
    conn = op.get_bind()

    for nombre, etiqueta, tipo_dato in _VARIABLES:
        conn.execute(sa.text("""
            INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
            VALUES (:nombre, :etiqueta, :tipo_dato, NULL, TRUE)
            ON CONFLICT (nombre) DO NOTHING
        """), {'nombre': nombre, 'etiqueta': etiqueta, 'tipo_dato': tipo_dato})

    conn.execute(sa.text("""
        UPDATE public.tipos_documentos
        SET codigo = :codigo_nuevo, nombre = :nombre_nuevo
        WHERE codigo = :codigo_anterior
    """), {
        'codigo_nuevo': _RENAME_CODIGO_NUEVO,
        'nombre_nuevo': _RENAME_NOMBRE_NUEVO,
        'codigo_anterior': _RENAME_CODIGO_ANTERIOR,
    })

    for codigo, descripcion in _DESCRIPCIONES:
        conn.execute(sa.text("""
            UPDATE public.tipos_documentos
            SET descripcion = :descripcion
            WHERE codigo = :codigo
        """), {'codigo': codigo, 'descripcion': descripcion})


def downgrade():
    conn = op.get_bind()

    for codigo, _descripcion in _DESCRIPCIONES:
        conn.execute(sa.text("""
            UPDATE public.tipos_documentos
            SET descripcion = NULL
            WHERE codigo = :codigo
        """), {'codigo': codigo})

    conn.execute(sa.text("""
        UPDATE public.tipos_documentos
        SET codigo = :codigo_anterior, nombre = :nombre_anterior
        WHERE codigo = :codigo_nuevo
    """), {
        'codigo_anterior': _RENAME_CODIGO_ANTERIOR,
        'nombre_anterior': _RENAME_NOMBRE_ANTERIOR,
        'codigo_nuevo': _RENAME_CODIGO_NUEVO,
    })

    for nombre, _etiqueta, _tipo_dato in _VARIABLES:
        conn.execute(sa.text("""
            DELETE FROM public.catalogo_variables WHERE nombre = :nombre
        """), {'nombre': nombre})
