"""928a_justificantes_notificacion — tres tipos de documento nuevos de N1

Revision ID: 928a_justificantes_notificacion
Revises: 892_plazo_fases_finalizadoras
Create Date: 2026-09-22

Issue #928 (N1), ADR-049 §B/§C/§G. Tres tipos de documento nuevos que sostienen
el cumplimiento del deber de notificar y la obligación paralela de sede
electrónica, y actualiza la descripción de los cuatro tipos ya existentes que
hoy confunden la fecha de puesta a disposición con la de efectos (origen del
defecto que documenta ADR-049 §G).

Convención `JUSTIFICANTE_<CANAL>_<HITO>`: el código se compara por igualdad en
`mutaciones_arbol.py` y `pool_documentos.html`, y solo el prefijo
`JUSTIFICANTE_` se usa para el aviso de críticos/huérfanos (#738) — los tres
entran solos en ese aviso, ningún otro consumidor se confunde.
"""
from alembic import op
import sqlalchemy as sa


revision = '928a_justificantes_notificacion'
down_revision = '892_plazo_fases_finalizadoras'
branch_labels = None
depends_on = None

# (codigo, nombre, descripcion, origen)
_DOCUMENTOS_NUEVOS = [
    ('JUSTIFICANTE_NOTIFICA_DISPOSICION', 'Justificante de puesta a disposición (Notifica-PNT)',
     'Acredita que la Administración puso la notificación a disposición del '
     'destinatario en la plataforma Notifica-PNT. Fecha administrativa: fecha '
     'de puesta a disposición (art. 43.3 LPACAP). Da cumplimiento del deber '
     'de notificar; nunca produce efectos frente al interesado.',
     'EXTERNO'),
    ('JUSTIFICANTE_POSTAL_1ER', 'Acuse del primer intento de notificación postal',
     'Acredita el primer intento de entrega postal, solo cuando ese intento '
     'fracasa. Fecha administrativa: fecha del intento (arts. 40.4 y 42.2 '
     'LPACAP). Da cumplimiento del deber de notificar; no produce efectos.',
     'EXTERNO'),
    ('JUSTIFICANTE_SEDE', 'Justificante de puesta a disposición en sede electrónica',
     'Acredita la puesta a disposición en la sede electrónica, obligación '
     'paralela de toda notificación practicada en papel (art. 42.1 LPACAP). '
     'Fecha administrativa: fecha de esa puesta a disposición. No es una '
     'notificación: no da cumplimiento ni produce efectos por sí sola.',
     'EXTERNO'),
]

# (codigo, descripcion_anterior, descripcion_nueva)
_DESCRIPCIONES_ACTUALIZADAS = [
    ('JUSTIFICANTE_NOTIFICA',
     'Acuse de entrega electrónica emitido por la plataforma Notifica-PNT. '
     'Fecha administrativa: fecha de entrega al interesado, deducida '
     'automáticamente del documento; el usuario debe cotejar el valor '
     'deducido con el real.',
     'Acuse de entrega electrónica emitido por la plataforma Notifica-PNT. '
     'Fecha administrativa: fecha de efectos — acceso/lectura (art. 43.2 '
     'párr. 1º), rechazo expreso (art. 41.5) o el registro de fecha que da '
     'la plataforma en «Rechazada por transcurso de plazo» o «Caducada» '
     '(art. 43.2 párr. 2º). No la puesta a disposición, que consta en '
     'JUSTIFICANTE_NOTIFICA_DISPOSICION.'),
    ('JUSTIFICANTE_POSTAL',
     'Acuse de recibo de notificación practicada por correo postal. Fecha '
     'administrativa: fecha de entrega acreditada en el acuse de recibo; se '
     'introduce manualmente.',
     'Acuse de recibo de notificación practicada por correo postal. Fecha '
     'administrativa: fecha de efectos — entrega o rechazo acreditados en '
     'el acuse (arts. 42.2 y 41.5 LPACAP); si el primer intento fue '
     'correcto, esta misma fecha sirve también de cumplimiento. Se '
     'introduce manualmente.'),
    ('JUSTIFICANTE_BANDEJA',
     'Justificante de transmisión electrónica generado por BandeJA. Fecha '
     'administrativa: fecha de transmisión, deducida automáticamente; el '
     'usuario debe cotejar el valor deducido con el real.',
     'Justificante de transmisión electrónica generado por BandeJA. Fecha '
     'administrativa: fecha de recepción, única y de efectos; el usuario '
     'debe cotejar el valor deducido con el real.'),
    ('JUSTIFICANTE_SIR',
     'Justificante de notificación cursada por registro SIR/ARIES. Fecha '
     'administrativa: fecha de práctica de la notificación tal como consta '
     'en el justificante; se introduce manualmente.',
     'Justificante de notificación cursada por registro SIR/ARIES. Fecha '
     'administrativa: fecha de recepción, única y de efectos; se introduce '
     'manualmente.'),
]


def upgrade():
    conn = op.get_bind()
    for codigo, nombre, descripcion, origen in _DOCUMENTOS_NUEVOS:
        conn.execute(sa.text("""
            INSERT INTO public.tipos_documentos (codigo, nombre, descripcion, origen)
            VALUES (:codigo, :nombre, :descripcion, :origen)
            ON CONFLICT DO NOTHING
        """), {'codigo': codigo, 'nombre': nombre, 'descripcion': descripcion,
               'origen': origen})

    for codigo, anterior, nueva in _DESCRIPCIONES_ACTUALIZADAS:
        conn.execute(sa.text("""
            UPDATE public.tipos_documentos SET descripcion = :nueva
            WHERE codigo = :codigo AND descripcion = :anterior
        """), {'codigo': codigo, 'anterior': anterior, 'nueva': nueva})


def downgrade():
    conn = op.get_bind()
    for codigo, anterior, nueva in _DESCRIPCIONES_ACTUALIZADAS:
        conn.execute(sa.text("""
            UPDATE public.tipos_documentos SET descripcion = :anterior
            WHERE codigo = :codigo AND descripcion = :nueva
        """), {'codigo': codigo, 'anterior': anterior, 'nueva': nueva})

    for codigo, _nombre, _descripcion, _origen in _DOCUMENTOS_NUEVOS:
        conn.execute(sa.text(
            "DELETE FROM public.tipos_documentos WHERE codigo = :codigo"
        ), {'codigo': codigo})
