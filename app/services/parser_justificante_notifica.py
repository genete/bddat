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

## ZIP y coherencia con el XML (`coherente_con_xml`)

Notifica-PNT entrega el justificante como ZIP con `Informe.pdf` +
`InformeENI.xml` (formato ENI, con un bloque de firma CAdES/PKCS#7 real en
`enids:firma`). El PDF **no** lleva firma embebida — su "VERIFICACIÓN
QFQG..." es un CSV que exige consulta externa, no una prueba autocontenida.

`enidocmeta:FechaCaptura` del XML coincide al minuto con "Fecha y hora de
generación" del PDF en las 2 muestras reales — es el único dato en texto
plano compartido por ambos ficheros (comprobado: ni el código de
verificación, ni la huella SHA256 impresa, ni el ID de remesa aparecen en el
XML). `coherente_con_xml` certifica que el PDF y el XML se generaron juntos,
en el mismo evento — descarta emparejar un XML firmado legítimo de otra
notificación con un PDF distinto. **No** valida la firma CAdES en sí (eso
exigiría parsear el ASN.1 del `FirmaBase64` — fuera de alcance de momento).
"""
from __future__ import annotations

import io
import re
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from lxml import etree
from pypdf import PdfReader

CANAL = 'NOTIFICA'

_NS_ENIDOCMETA = 'http://administracionelectronica.gob.es/ENI/XSD/v1.0/documento-e/metadatos'

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
    # None = no se aportó XML para comparar (p.ej. parseo de PDF suelto).
    # True/False = PDF y XML se generaron en el mismo evento (ver docstring
    # del módulo) — no es validación de la firma CAdES en sí.
    coherente_con_xml: bool | None = None

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


def _extraer_fecha_captura_xml(xml_bytes: bytes) -> datetime | None:
    """Lee `enidocmeta:FechaCaptura` del InformeENI.xml. None si no se
    encuentra o el XML no es parseable (nunca lanza)."""
    try:
        raiz = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError:
        return None
    nodo = raiz.find(f'.//{{{_NS_ENIDOCMETA}}}FechaCaptura')
    if nodo is None or not nodo.text:
        return None
    try:
        return datetime.fromisoformat(nodo.text).replace(tzinfo=None)
    except ValueError:
        return None


def parsear_justificante_notifica_zip(fuente: str | Path | BinaryIO) -> JustificanteNotificaPNT:
    """
    Punto de entrada para el ZIP tal como lo entrega Notifica-PNT
    (`Informe.pdf` + `InformeENI.xml`). Extrae el PDF y lo pasa a
    `parsear_justificante_notifica`; si además encuentra el XML, calcula
    `coherente_con_xml` comparando `FechaCaptura` (XML) con "Fecha y hora de
    generación" (PDF) al minuto — el PDF no imprime segundos.

    Mismo contrato que `parsear_justificante_notifica`: nunca lanza
    excepción por un ZIP inesperado, devuelve `.reconocido == False`.
    """
    try:
        with zipfile.ZipFile(fuente) as zf:
            nombre_pdf = next((n for n in zf.namelist() if n.lower().endswith('.pdf')), None)
            if nombre_pdf is None:
                return _VACIO
            # PdfReader exige un stream con .read(), no bytes pelados.
            resultado = parsear_justificante_notifica(io.BytesIO(zf.read(nombre_pdf)))

            nombre_xml = next((n for n in zf.namelist() if n.lower().endswith('.xml')), None)
            if nombre_xml is not None and resultado.fecha_generacion_informe is not None:
                fecha_captura = _extraer_fecha_captura_xml(zf.read(nombre_xml))
                if fecha_captura is not None:
                    resultado.coherente_con_xml = (
                        fecha_captura.replace(second=0, microsecond=0)
                        == resultado.fecha_generacion_informe.replace(second=0, microsecond=0)
                    )
    except (zipfile.BadZipFile, KeyError):
        return _VACIO

    return resultado
