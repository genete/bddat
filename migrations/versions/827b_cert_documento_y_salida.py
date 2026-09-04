"""827b_cert_documento_y_salida

Revision ID: 827b_cert_documento
Revises: 827_cert_fin_instruccion
Create Date: 2026-09-04

Issue #827 — ADR-043 §E reescrita: el gesto pasa de puerta a revisión que se
consolida. Dos piezas de esquema/catálogo que ese giro necesita.

1. `certificados_fase.documento_id`
===================================

La columna que le faltaba a `CertificadoFase` y que su hermano `Certificado`
(#392) sí tiene desde el principio. Sin ella el vínculo solo existe en un
sentido —el `Documento` apunta al PDF, nadie apunta al `Documento`— y eso forzaba
un rodeo en el emisor: crear el `Documento` con una url provisional
(`bddat://certificados/pendiente-…`) para poder anclarlo a la solicitud ANTES de
auditar, y dejar que el generador lo completase después.

Con §E ter ese rodeo desaparece porque el orden se invierte: **se evalúa primero,
sin crear nada, y se consolida después**. El certificado solo existe cuando el
informe sale sin pendientes, así que ya no hay nada que anclar por adelantado y el
`Documento` puede crearse con su url definitiva. La columna es además la vuelta
certificado→documento que #838 necesitará para deshacer el sello.

NULLABLE, al contrario que en `certificados`: el PDF se llama
`{tipo_cert}_{cert.id}.pdf`, así que el `CertificadoFase` tiene que existir antes
que el `Documento` que lo referencia, y entre un `flush()` y el otro la columna
está vacía. Poner NOT NULL exigiría invertir esa dependencia o rellenar a mano las
filas ya emitidas, que no tienen forma fiable de saber cuál es su documento.

2. Las dos reglas del art. 82.1 pasan a señalar la salida
=========================================================

Hasta ahora prohibían a secas («No se puede abrir la fase de resolución mientras
no conste emitido el certificado…»). Con el gesto convertido en revisión, el
técnico ya no necesita adivinar qué le falta: puede preguntarlo desde el inspector
de la solicitud cuando quiera. La descripción —que es lo que `evaluar()` devuelve
como `motivo` y lo que el usuario lee en el toast del bloqueo— lo dice ahora.

Es lo que ADR-043 §F pide para el sello de la instrucción y vale igual aquí: un
check que nombra la vía es ayuda, y uno que solo prohíbe es obstáculo.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '827b_cert_documento'
down_revision = '827_cert_fin_instruccion'
branch_labels = None
depends_on = None


# (sujeto, descripción antigua, descripción nueva) — las dos filas de ADR-043 §C.
_REGLAS = [
    (
        'ANY/ANY/RESOLUCION',
        'No se puede abrir la fase de resolución mientras no conste emitido el '
        'certificado de fin de instrucción de la solicitud',
        'No se puede abrir la fase de resolución mientras no conste emitido el '
        'certificado de fin de instrucción de la solicitud. Pida el certificado '
        'desde la solicitud: si algo falta, el informe dirá qué y por qué.',
    ),
    (
        'ANY/INTERESADO/RECONOCIMIENTO_INTERESADO',
        'No se puede abrir la fase de reconocimiento de interesado mientras no conste '
        'emitido el certificado de fin de instrucción de la solicitud',
        'No se puede abrir la fase de reconocimiento de interesado mientras no conste '
        'emitido el certificado de fin de instrucción de la solicitud. Pida el '
        'certificado desde la solicitud: si algo falta, el informe dirá qué y por qué.',
    ),
]


def upgrade():
    conn = op.get_bind()

    # --- 1. La vuelta certificado → documento -------------------------------
    op.add_column(
        'certificados_fase',
        sa.Column(
            'documento_id', sa.Integer(), nullable=True,
            comment='FK a DOCUMENTOS. Documento del pool que materializa este '
                    'certificado (su PDF). NULL entre la creación del certificado y '
                    'la del documento, y en los emitidos antes de #827',
        ),
        schema='public',
    )
    op.create_foreign_key(
        'fk_cert_fase_documento',
        'certificados_fase', 'documentos',
        ['documento_id'], ['id'],
        source_schema='public', referent_schema='public',
    )
    op.create_index(
        'idx_cert_fase_documento', 'certificados_fase',
        ['documento_id'], schema='public',
    )

    # --- 2. El bloqueo del motor nombra la vía ------------------------------
    for sujeto, vieja, nueva in _REGLAS:
        conn.execute(sa.text("""
            UPDATE public.reglas_motor SET descripcion = :nueva
            WHERE accion = 'CREAR' AND sujeto = :sujeto AND descripcion = :vieja
        """), {'sujeto': sujeto, 'vieja': vieja, 'nueva': nueva})


def downgrade():
    conn = op.get_bind()

    for sujeto, vieja, nueva in _REGLAS:
        conn.execute(sa.text("""
            UPDATE public.reglas_motor SET descripcion = :vieja
            WHERE accion = 'CREAR' AND sujeto = :sujeto AND descripcion = :nueva
        """), {'sujeto': sujeto, 'vieja': vieja, 'nueva': nueva})

    op.drop_index('idx_cert_fase_documento',
                  table_name='certificados_fase', schema='public')
    op.drop_constraint('fk_cert_fase_documento', 'certificados_fase',
                       type_='foreignkey', schema='public')
    op.drop_column('certificados_fase', 'documento_id', schema='public')
