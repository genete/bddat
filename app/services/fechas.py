"""Validación de fechas administrativas (#824).

Servicio deliberadamente diminuto: la regla es una comparación, pero necesita un
sitio con nombre porque la aplican dos capas distintas —el invariante del modelo
`Documento` y la interfaz, vía el componente `EntradaFecha`— y ninguna de las dos
debe reescribirla por su cuenta.
"""
from __future__ import annotations

from datetime import date
from typing import Optional


def fecha_administrativa_valida(fecha: Optional[date], hoy: Optional[date] = None) -> bool:
    """¿Es admisible esta fecha administrativa?

    Una fecha administrativa acredita un hecho consumado —se registró, se firmó,
    se publicó, se notificó, se certificó— y un hecho consumado no ocurre mañana:
    cualquier fecha posterior a hoy es inválida, sea cual sea el tipo de
    documento. La eficacia diferida de un acto (art. 39 LPACAP) no es una
    excepción a esto: esa fecha la porta *otro* documento —el justificante de
    notificación—, y por eso no hace falta ninguna columna de fecha de efectos.
    El razonamiento completo, con el descarte de los tres candidatos a caso
    legítimo, está en #824.

    Sí existen fechas futuras válidas en el sistema; ninguna es administrativa:
    los vencimientos que calcula el motor de plazos son fechas derivadas, no
    fechas de un documento.

    `None` es válido — el documento cargado al pool pendiente de revisión y el
    que no tiene valor jurídico propio (informe de ANALIZAR) son los dos casos
    legítimos que documenta `Documento`.

    `hoy` es el del sistema salvo que se diga otra cosa, reloj de desarrollo
    incluido (#820). El valor por defecto no es un detalle: si cada llamador
    tuviera que traer el suyo, tarde o temprano alguno usaría `date.today()` y la
    validación dejaría de ser comprobable en desarrollo, que es justo donde se
    prueba.
    """
    if fecha is None:
        return True
    if hoy is None:
        from app.services.reloj_simulado import hoy as hoy_del_sistema
        hoy = hoy_del_sistema()
    return fecha <= hoy


# Tipos de documento cuya fecha_administrativa es obligatoria (#928, N1 §4;
# precedente #885, antes solo DOC_PROYECTO). Sin fecha no aportan ninguna y el
# fallo sería silencioso (P1: «si el hecho no tiene documento, no hay
# fecha»). Invariante de completitud del dato, hardcode deliberado — no vive
# en `tipos_documentos` (ni regla de motor ni dato de catálogo) porque no
# admite excepción por expediente ni por usuario, a diferencia de una regla
# del motor o un dato de catálogo (ver [[feedback_invariante_vs_regla_motor]]
# en la memoria del proyecto).
TIPOS_FECHA_OBLIGATORIA = frozenset({
    'DOC_PROYECTO',
    'JUSTIFICANTE_NOTIFICA_DISPOSICION',
    'JUSTIFICANTE_NOTIFICA',
    'JUSTIFICANTE_POSTAL_1ER',
    'JUSTIFICANTE_POSTAL',
    'JUSTIFICANTE_BANDEJA',
    'JUSTIFICANTE_SIR',
    'JUSTIFICANTE_SEDE',
})

_MENSAJES_FECHA_OBLIGATORIA = {
    'DOC_PROYECTO': (
        'Un documento de proyecto necesita fecha administrativa: es la que '
        'ordena las versiones del proyecto y decide a cuál pertenece cada '
        'documento.'
    ),
    'JUSTIFICANTE_NOTIFICA_DISPOSICION': (
        'Un justificante de puesta a disposición (Notifica-PNT) necesita '
        'fecha administrativa: es la fecha de cumplimiento del deber de '
        'notificar.'
    ),
    'JUSTIFICANTE_NOTIFICA': (
        'Un justificante de Notifica-PNT necesita fecha administrativa: es '
        'la fecha de efectos frente al interesado.'
    ),
    'JUSTIFICANTE_POSTAL_1ER': (
        'Un acuse del primer intento de notificación postal necesita fecha '
        'administrativa: es la fecha de ese intento.'
    ),
    'JUSTIFICANTE_POSTAL': (
        'Un justificante de notificación postal necesita fecha '
        'administrativa: es la fecha de efectos frente al interesado.'
    ),
    'JUSTIFICANTE_BANDEJA': (
        'Un justificante de BandeJA necesita fecha administrativa: es la '
        'fecha de recepción, única y de efectos.'
    ),
    'JUSTIFICANTE_SIR': (
        'Un justificante de SIR/ARIES necesita fecha administrativa: es la '
        'fecha de recepción, única y de efectos.'
    ),
    'JUSTIFICANTE_SEDE': (
        'Un justificante de puesta a disposición en sede electrónica '
        'necesita fecha administrativa: es la fecha de esa puesta a '
        'disposición.'
    ),
}


def mensaje_fecha_obligatoria(codigo: str) -> str:
    """Mensaje de error para un `codigo` de `TIPOS_FECHA_OBLIGATORIA` — un
    mensaje por tipo, no uno genérico, porque cada uno dice qué fecha exacta
    hace falta y por qué (#928, N1 §4)."""
    return _MENSAJES_FECHA_OBLIGATORIA[codigo]
