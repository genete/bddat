"""
Parser del justificante de notificación de Notific@ PNT (issue #655).

Extrae de un PDF `Informe.pdf` (descarga de Notifica-PNT) los datos que hoy
hay que copiar a mano a la tabla `notificaciones` (#418 / ADR-008): estado,
fecha de puesta a disposición, fecha de lectura y algunos campos bonus
(remesa, destinatario, código de expediente si el PDF lo trae).

Sin ninguna integración en interfaz todavía — es una librería de bajo nivel
pensada para que la use el punto de subida al pool y/o el punto de
asociación a la tarea NOTIFICAR cuando esa interfaz exista (ver #655 para el
mapa de puntos de enganche pendientes de decidir).

Solo cubre el canal NOTIFICA (Notific@ PNT). BandeJA y SIR quedan fuera:
no hay muestras reales de su formato de justificante.

Validado contra 2 justificantes reales, ambos con estado "Leída". El resto
de valores de `MAPA_RESULTADO` viene del catálogo `Estado` de
`notifica-poc/notifica.py` (scraping DOM) — sin confirmar si el nombre de
campo de fecha ("Fecha de lectura") es el mismo en un PDF real de esos
estados.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader

CANAL = 'NOTIFICA'

# Traduce el texto libre de "Estado:" al binario CORRECTA/INCORRECTA que
# exige el CHECK de `notificaciones.resultado` (ADR-008).
MAPA_RESULTADO = {
    'Leída': 'CORRECTA',
    'Caducada': 'INCORRECTA',
    'Rechazada': 'INCORRECTA',
    'Rechazada por plazo': 'INCORRECTA',
    'Anulada': 'INCORRECTA',
    'No entregada': 'INCORRECTA',
}


@dataclass
class JustificanteNotificaPNT:
    id_remesa: str | None
    id_notificacion: str | None
    destinatario: str | None
    identificador_destinatario: str | None
    procedimiento: str | None
    codigo_expediente: str | None
    estado_texto: str | None
    resultado: str | None
    fecha_puesta_disposicion: datetime | None
    fecha_lectura: datetime | None
    fecha_generacion_informe: datetime | None
    verificacion: str | None
    canal: str = CANAL

    @property
    def reconocido(self) -> bool:
        """False cuando el PDF no encaja con el formato de justificante Notifica-PNT."""
        return self.id_remesa is not None and self.estado_texto is not None

    def to_dict(self) -> dict:
        """Representación JSON-serializable: fechas como ISO 8601."""
        datos = asdict(self)
        for campo in ('fecha_puesta_disposicion', 'fecha_lectura', 'fecha_generacion_informe'):
            if datos[campo] is not None:
                datos[campo] = datos[campo].isoformat()
        datos['reconocido'] = self.reconocido
        return datos


_VACIO = JustificanteNotificaPNT(
    id_remesa=None, id_notificacion=None, destinatario=None,
    identificador_destinatario=None, procedimiento=None, codigo_expediente=None,
    estado_texto=None, resultado=None, fecha_puesta_disposicion=None,
    fecha_lectura=None, fecha_generacion_informe=None, verificacion=None,
)


def _buscar(patron: str, texto: str) -> str | None:
    """Busca en una sola línea (MULTILINE, sin cruzar saltos de línea con '.')."""
    m = re.search(patron, texto, re.MULTILINE)
    if not m:
        return None
    valor = m.group(1).strip()
    return valor or None


def _parsear_fecha_hora(valor: str | None) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%d/%m/%y %H:%M")
    except ValueError:
        return None


def _parsear_texto(texto: str) -> JustificanteNotificaPNT:
    """Parseo puro sobre texto ya extraído — sin I/O, para tests sin PDF real."""
    estado_texto = _buscar(r"Estado:\s*(.+)", texto)

    return JustificanteNotificaPNT(
        id_remesa=_buscar(r"ID remesa:\s*(\S+)", texto),
        id_notificacion=_buscar(r"ID notificaci[oó]n:\s*(\S+)", texto),
        destinatario=_buscar(r"Destinatario:\s*(.+?)\s+Identificador:", texto),
        identificador_destinatario=_buscar(r"Destinatario:.+?Identificador:\s*(\S+)", texto),
        procedimiento=_buscar(r"^Procedimiento:[ \t]*(.+)$", texto),
        # Anclado a fin de línea: distingue "Código de Expediente:" de
        # "Código de Expediente Normalizado:" (línea distinta). Vacío -> None.
        codigo_expediente=_buscar(r"^C[oó]digo de Expediente:[ \t]*(\S*)[ \t]*$", texto),
        estado_texto=estado_texto,
        resultado=MAPA_RESULTADO.get(estado_texto) if estado_texto else None,
        fecha_puesta_disposicion=_parsear_fecha_hora(
            _buscar(r"Puesta a disposici[oó]n:\s*(\d{2}/\d{2}/\d{2} \d{2}:\d{2})", texto)
        ),
        fecha_lectura=_parsear_fecha_hora(
            _buscar(r"Fecha de lectura:\s*(\d{2}/\d{2}/\d{2} \d{2}:\d{2})", texto)
        ),
        fecha_generacion_informe=_parsear_fecha_hora(
            _buscar(r"Fecha y hora de generaci[oó]n:\s*(\d{2}/\d{2}/\d{2} \d{2}:\d{2})", texto)
        ),
        # Anclado a inicio de línea: "VERIFICACIÓN" también aparece suelto en
        # el párrafo de instrucciones ("...indicando el código de
        # VERIFICACIÓN"), sin código detrás en esa línea — solo la línea
        # final del PDF lo lleva.
        verificacion=_buscar(r"^VERIFICACI[OÓ]N[ \t]+(\S+)", texto),
    )


def parsear_justificante_notifica(fuente: str | Path | BinaryIO) -> JustificanteNotificaPNT:
    """
    Punto de entrada público. `fuente`: ruta a fichero o stream binario
    (p.ej. el `.stream` de un `FileStorage` de Flask al subir el documento).

    Nunca lanza excepción por un PDF que no sea un justificante Notifica-PNT
    (formato distinto, corrupto, escaneado sin texto...) — se espera llamarlo
    especulativamente sobre cualquier PDF que suba el usuario. Comprobar
    `.reconocido` en el resultado antes de usar los demás campos.
    """
    try:
        lector = PdfReader(fuente)
        texto = "\n".join(pagina.extract_text() or "" for pagina in lector.pages)
    except Exception:
        return _VACIO

    return _parsear_texto(texto)
