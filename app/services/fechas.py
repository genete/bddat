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
