"""
Servicio de generación de escritos administrativos.

RESPONSABILIDAD:
    Orquesta las capas de contexto y despacha al motor de render que
    corresponda para producir un escrito relleno a partir de una Plantilla
    registrada. Aquí no se renderiza nada: solo vive lo común a los dos
    formatos (nombre, ruta, guardado, MIME y validación).

DOS MOTORES HERMANOS (ADR-035 §2):
    .odt  → renderizador propio, en generador_escritos_odt   (formato de referencia)
    .docx → python-docx-template, en generador_escritos_docx (heredado, en retirada)

    La elección se hace por la extensión de plantilla.ruta_plantilla: sin
    columna nueva ni migración. No hay abstracción común entre ambos — los
    modelos de docxtpl y de ODF no se parecen (ADR-035, alternativa B); lo que
    comparten es la firma y este despachador. Cuando el .docx se retire, se
    borra su módulo y su rama de los dos `if` de aquí.

FLUJO:
    1. Resuelve la ruta de la plantilla en PLANTILLAS_BASE
    2. Construye el contexto (escritos.construir_contexto) — agnóstico del formato
    3. Renderiza con el motor que toque
    4. Devuelve los bytes del documento resultante

FUNCIONES PÚBLICAS ADICIONALES (Fase 5 #167):
    componer_nombre_documento  — Nombre sistematizado para el documento generado
    ruta_destino_documento     — Ruta en FILESYSTEM_BASE/AT-XXXX/
    guardar_documento          — Escribe bytes a disco (sobrescribe si existe)
    tipo_contenido_documento   — MIME del documento según su extensión

USO:
    from app.services.generador_escritos import (
        generar_escrito, componer_nombre_documento,
        ruta_destino_documento, guardar_documento,
    )

    doc_bytes = generar_escrito(plantilla, expediente, db_session)
    nombre = componer_nombre_documento(tarea, plantilla)
    ruta = ruta_destino_documento(expediente, nombre)
    guardar_documento(doc_bytes, ruta)

DEPENDENCIA:
    Ninguna propia. La rama .docx arrastra python-docx-template, pero se
    importa dentro de su módulo.
"""

import logging
import os
import re

from app.services.escritos import construir_contexto

logger = logging.getLogger(__name__)

# MIME por extensión de plantilla. Lo consume la API al registrar el documento
# generado en el pool.
TIPOS_CONTENIDO = {
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.odt':  'application/vnd.oasis.opendocument.text',
}


def generar_escrito(plantilla, expediente, db_session, tarea=None,
                    codigo_seguimiento=None) -> bytes:
    """
    Genera el escrito relleno para la plantilla y expediente dados.

    Despacha al motor .docx o al .odt según la extensión de la plantilla.

    Args:
        plantilla:   Instancia de Plantilla (plantilla + contexto registrado).
        expediente:  Instancia de Expediente con relaciones cargadas.
        db_session:  Sesión SQLAlchemy activa (para ejecutar consultas nombradas).
        tarea:       Instancia de Tarea opcional. Si se proporciona y tiene
                     documentos consumidos, el primero se añade al contexto
                     como 'doc_entrada'.
        codigo_seguimiento: Código de trazabilidad a embeber en el documento
                     (#182). Solo lo soporta el motor .odt; en .docx se ignora
                     con un warning, porque ningún canal de metadatos OOXML
                     sobrevive al pipeline (ADR-035, contexto).

    Returns:
        bytes — Contenido del documento generado, listo para guardar en disco.

    Raises:
        FileNotFoundError — Si la plantilla no existe en PLANTILLAS_BASE.
        RuntimeError      — Si el Context Builder especificado no se puede cargar.
        ValueError        — Si la extensión de la plantilla no tiene motor.
    """
    plantilla_path = _ruta_plantilla(plantilla.ruta_plantilla)
    extension = os.path.splitext(plantilla_path)[1].lower()

    ctx = construir_contexto(plantilla, expediente, db_session, tarea=tarea)

    if extension == '.odt':
        from app.services.generador_escritos_odt import generar_escrito_odt
        return generar_escrito_odt(plantilla_path, ctx,
                                   codigo_seguimiento=codigo_seguimiento)

    if extension == '.docx':
        if codigo_seguimiento:
            logger.warning(
                'Código de seguimiento ignorado: la plantilla %s es .docx y el '
                'motor OOXML no lo soporta (ADR-035)', plantilla.ruta_plantilla
            )
        from app.services.generador_escritos_docx import generar_escrito_docx
        return generar_escrito_docx(plantilla_path, ctx)

    raise ValueError(
        f'No hay motor de generación para la extensión "{extension}" '
        f'(plantilla: {plantilla.ruta_plantilla}). Formatos soportados: '
        f'{", ".join(sorted(TIPOS_CONTENIDO))}.'
    )


# ------------------------------------------------------------------
# Funciones públicas — nombre, ruta y guardado (Fase 5 #167)
# ------------------------------------------------------------------

# Caracteres no válidos en nombres de fichero Windows
_CARACTERES_INVALIDOS = re.compile(r'[\\/:*?"<>|]')


def componer_nombre_documento(tarea, plantilla) -> str:
    """
    Genera un nombre sistematizado para el documento a partir de la cadena ESFTT.

    Recorre tarea → tipo_tarea → tramite → tipo_tramite → fase → tipo_fase
    → solicitud → tipo_solicitud → expediente, tomando nombre_en_plantilla
    de cada nivel. NULL al final se omite; NULL en medio se reemplaza por "ANY".

    Si plantilla.variante existe, se añade " V {variante}" al final.
    La extensión es la de la plantilla (.docx o .odt), no una fija: el escrito
    generado conserva el formato de su plantilla (ADR-035 §2).
    Caracteres inválidos para fichero → '_'.
    """
    tramite = tarea.tramite
    fase = tramite.fase if tramite else None
    solicitud = fase.solicitud if fase else None
    expediente = solicitud.expediente if solicitud else None

    # Recoger nombre_en_plantilla de cada nivel (de más genérico a más específico)
    partes_raw = [
        getattr(tarea.tipo_tarea, 'nombre_en_plantilla', None) if tarea.tipo_tarea else None,
        getattr(tramite.tipo_tramite, 'nombre_en_plantilla', None) if tramite and tramite.tipo_tramite else None,
        getattr(fase.tipo_fase, 'nombre_en_plantilla', None) if fase and fase.tipo_fase else None,
        getattr(solicitud.tipo_solicitud, 'nombre_en_plantilla', None) if solicitud and solicitud.tipo_solicitud else None,
        f'AT-{expediente.numero_at}' if expediente and expediente.numero_at else None,
    ]

    # Recortar NULLs del final; reemplazar NULLs internos por "ANY"
    while partes_raw and partes_raw[-1] is None:
        partes_raw.pop()

    partes = [p if p is not None else 'ANY' for p in partes_raw]

    nombre = ' '.join(partes)

    if plantilla.variante:
        nombre += f' V {plantilla.variante}'

    nombre += os.path.splitext(plantilla.ruta_plantilla or '')[1].lower() or '.docx'

    # Sanitizar caracteres inválidos para nombre de fichero
    nombre = _CARACTERES_INVALIDOS.sub('_', nombre)

    return nombre


def ruta_destino_documento(expediente, nombre_fichero) -> str:
    """
    Calcula la ruta absoluta donde guardar el documento generado.

    Estructura: FILESYSTEM_BASE / AT-{numero_at} / {nombre_fichero}
    Crea el subdirectorio si no existe.

    NOTA: Ruta hardcoded provisional. Se reemplazará por rutas configurables
    en tablas maestras cuando se implemente esa decisión de arquitectura
    (Bloque 2/8 del roadmap).
    """
    from flask import current_app
    base = current_app.config.get('FILESYSTEM_BASE', '')
    if not base:
        raise RuntimeError('FILESYSTEM_BASE no está configurado')

    carpeta_exp = f'AT-{expediente.numero_at}'
    directorio = os.path.join(base, carpeta_exp)
    os.makedirs(directorio, exist_ok=True)

    return os.path.join(directorio, nombre_fichero)


def guardar_documento(doc_bytes, ruta_destino) -> str:
    """
    Escribe los bytes del documento a disco. Sobrescribe si existe (regeneración B6).

    Returns:
        str — Ruta absoluta del fichero escrito.
    """
    with open(ruta_destino, 'wb') as f:
        f.write(doc_bytes)
    return ruta_destino


def validar_plantilla(ruta_abs: str) -> str | None:
    """
    Comprueba que el fichero sea una plantilla utilizable por su motor.

    Dos cosas distintas, y ambas importan en el alta: que el fichero esté bien
    formado para su formato, y que su sintaxis Jinja2 compile — un `{% for %}`
    sin cerrar no se ve hasta que alguien genera el escrito.

    Returns:
        str  — Mensaje de error, listo para enseñar al supervisor.
        None — La plantilla es válida.
    """
    extension = os.path.splitext(ruta_abs or '')[1].lower()

    if extension == '.odt':
        from app.services.generador_escritos_odt import validar_plantilla_odt
        return validar_plantilla_odt(ruta_abs)

    if extension == '.docx':
        from app.services.generador_escritos_docx import validar_plantilla_docx
        return validar_plantilla_docx(ruta_abs)

    return (f'Formato de plantilla no soportado: "{extension}". '
            f'Se admiten {", ".join(sorted(TIPOS_CONTENIDO))}.')


def tipo_contenido_documento(nombre_o_ruta: str) -> str:
    """
    MIME del documento generado, deducido de su extensión.

    Desconocida → 'application/octet-stream', que es lo honesto: mejor que el
    navegador no sepa abrirlo a que lo abra con el programa equivocado.
    """
    extension = os.path.splitext(nombre_o_ruta or '')[1].lower()
    return TIPOS_CONTENIDO.get(extension, 'application/octet-stream')


# ------------------------------------------------------------------
# Helpers privados
# ------------------------------------------------------------------

def _ruta_plantilla(ruta_relativa: str) -> str:
    """Resuelve la ruta absoluta de la plantilla dentro de PLANTILLAS_BASE."""
    from flask import current_app
    base = current_app.config['PLANTILLAS_BASE']
    ruta = os.path.join(base, 'plantillas', ruta_relativa)
    if not os.path.isfile(ruta):
        raise FileNotFoundError(
            f'Plantilla no encontrada: {ruta}. '
            f'Comprueba PLANTILLAS_BASE y la ruta registrada en la plantilla.'
        )
    return ruta
