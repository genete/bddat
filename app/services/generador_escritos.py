"""
Servicio de generación de escritos administrativos.

RESPONSABILIDAD:
    Orquesta las capas de contexto y despacha al motor de render que
    corresponda para producir un escrito relleno a partir de una Plantilla
    registrada. Aquí no se renderiza nada: solo vive lo común a los dos
    formatos (nombre, MIME y validación).

DOS MOTORES HERMANOS (ADR-035 §2):
    .odt  → renderizador propio, en generador_escritos_odt   (formato de referencia)
    .docx → python-docx-template, en generador_escritos_docx (se mantiene, ADR-050 §J)

    La elección se hace por el formato de la fila de `ficheros` de la plantilla
    (ADR-050 §E), no por ninguna extensión. No hay abstracción común entre ambos
    — los modelos de docxtpl y de ODF no se parecen (ADR-035, alternativa B); lo
    que comparten es la firma y este despachador.

FLUJO:
    1. Comprueba que la plantilla se pueda usar (`contenido.motivo_no_usable`)
    2. Lee su contenido del almacén (`contenido.leer_plantilla`)
    3. Construye el contexto (escritos.construir_contexto) — agnóstico del formato
    4. Renderiza con el motor que toque, dándole los fragmentos por nombre
    5. Devuelve los bytes del documento resultante

    Los motores no tocan el disco: reciben bytes. Un fragmento que falte detiene la
    generación (`FragmentoAusente`).

FUNCIONES PÚBLICAS ADICIONALES (Fase 5 #167):
    componer_nombre_documento  — Nombre sistematizado para el documento generado
    advertencias_plantilla     — Avisos de canonicidad (#727); solo .odt, no bloquean

    El escrito no se guarda aquí: lo sube `regeneracion_escritos.regenerar_escrito`
    al almacén (ADR-050), con el nombre que compone `componer_nombre_documento`.

USO:
    from app.services.generador_escritos import generar_escrito, componer_nombre_documento

    doc_bytes = generar_escrito(plantilla, expediente, db_session)
    nombre = componer_nombre_documento(tarea, plantilla,
                                       contenido.extension_de_plantilla(plantilla))
    # regeneracion_escritos.regenerar_escrito(...) lo sube y lo vincula

DEPENDENCIA:
    El módulo de contenido del almacén (para la plantilla y los fragmentos). La
    rama .docx arrastra python-docx-template, pero se importa dentro de su módulo.
"""

import logging
import re

from app.services.almacenamiento import contenido
from app.services.almacenamiento.formatos import MIME_DOCX, MIME_ODT
from app.services.escritos import construir_contexto
from app.services.nombres_documentos import texto_tramite

logger = logging.getLogger(__name__)

# Extensiones de plantilla que tienen motor, con su MIME: las que admiten
# `validar_plantilla` y el alta de plantillas (`admin_plantillas`).
TIPOS_CONTENIDO = {
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.odt':  'application/vnd.oasis.opendocument.text',
}


def generar_escrito(plantilla, expediente, db_session, tarea=None,
                    codigo_seguimiento=None) -> bytes:
    """
    Genera el escrito relleno para la plantilla y expediente dados.

    Despacha al motor .docx o al .odt según el formato de la plantilla en el almacén.

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
        bytes — Contenido del documento generado, listo para subir al almacén.

    Raises:
        PlantillaNoUsable — Si no tiene fichero, su contenido no está disponible o el
                            supervisor la ha desactivado. El mensaje dice cuál.
        FragmentoAusente  — Si la plantilla cita un fragmento que no hay (o está
                            retirado): detiene la generación.
        ContenidoNoUtilizable / AlmacenNoDisponible — El contenido está ausente o
                            dañado / el almacén no contesta.
        RuntimeError      — Si el Context Builder especificado no se puede cargar.
        ValueError        — Si el formato de la plantilla no tiene motor.
    """
    motivo = contenido.motivo_no_usable(plantilla)
    if motivo is not None:
        raise contenido.PlantillaNoUsable(motivo)
    leida = contenido.leer_plantilla(plantilla)

    ctx = construir_contexto(plantilla, expediente, db_session, tarea=tarea)

    def fragmento(nombre):
        return contenido.leer_fragmento(nombre, leida.formato)

    if leida.formato == MIME_ODT:
        from app.services.generador_escritos_odt import generar_escrito_odt
        return generar_escrito_odt(leida.datos, ctx, codigo_seguimiento=codigo_seguimiento,
                                   fragmento=fragmento)

    if leida.formato == MIME_DOCX:
        if codigo_seguimiento:
            logger.warning(
                'Código de seguimiento ignorado: la plantilla «%s» es .docx y el '
                'motor OOXML no lo soporta (ADR-035)', plantilla.nombre
            )
        from app.services.generador_escritos_docx import generar_escrito_docx
        return generar_escrito_docx(leida.datos, ctx, fragmento=fragmento)

    raise ValueError(
        f'No hay motor de generación para el formato {leida.formato} '
        f'(plantilla: {plantilla.nombre}). Formatos soportados: '
        f'{", ".join(sorted(TIPOS_CONTENIDO))}.'
    )


# ------------------------------------------------------------------
# Funciones públicas — nombre y validación (Fase 5 #167)
# ------------------------------------------------------------------

# Caracteres no válidos en nombres de fichero Windows
_CARACTERES_INVALIDOS = re.compile(r'[\\/:*?"<>|]')


def componer_nombre_documento(tarea, plantilla, extension: str) -> str:
    """
    Genera un nombre sistematizado para el documento a partir de la cadena ESFTT.

    Cadena: {texto del trámite} {siglas de la solicitud} AT-{numero_at}
    [V {variante}].{extensión}

    El texto del trámite lo calcula nombres_documentos.texto_tramite() —
    lógica condicional por trámite (numeración de vueltas repetidas, ramas
    por tipo de expediente), no un dato de catálogo estático (#698). No hay
    token de tarea (siempre ELABORAR, único punto de entrada a la
    generación de escritos — no aporta nada) ni de tipo de expediente (dato
    inmutable ya implícito en AT-N).

    Si plantilla.variante existe, se añade " V {variante}" al final.
    La extensión es la de la plantilla (.docx o .odt), no una fija: el escrito
    generado conserva el formato de su plantilla (ADR-035 §2). La da quien llama
    (`contenido.extension_de_plantilla`): aquí no se lee nada.
    Caracteres inválidos para fichero → '_'.
    """
    tramite = tarea.tramite
    fase = tramite.fase if tramite else None
    solicitud = fase.solicitud if fase else None
    expediente = solicitud.expediente if solicitud else None

    partes = []

    if tramite:
        partes.append(texto_tramite(tramite))

    if solicitud and solicitud.tipo_solicitud:
        ts = solicitud.tipo_solicitud
        partes.append(ts.nombre_en_plantilla or ts.siglas)

    if expediente and expediente.numero_at:
        partes.append(f'AT-{expediente.numero_at}')

    nombre = ' '.join(partes)

    if plantilla.variante:
        nombre += f' V {plantilla.variante}'

    nombre += extension

    # Sanitizar caracteres inválidos para nombre de fichero
    nombre = _CARACTERES_INVALIDOS.sub('_', nombre)

    return nombre


def validar_plantilla(datos: bytes, formato: str) -> str | None:
    """
    Comprueba que el contenido sea una plantilla utilizable por su motor.

    `formato` es el MIME del contenido (el que detecta el módulo de contenido al
    subirlo, ADR-050 §E), no una extensión: es lo que elige el motor.

    Dos cosas distintas, y ambas importan en el alta: que el fichero esté bien
    formado para su formato, y que su sintaxis Jinja2 compile — un `{% for %}`
    sin cerrar no se ve hasta que alguien genera el escrito.

    Returns:
        str  — Mensaje de error, listo para enseñar al supervisor.
        None — La plantilla es válida.
    """
    if formato == MIME_ODT:
        from app.services.generador_escritos_odt import validar_plantilla_odt
        return validar_plantilla_odt(datos)

    if formato == MIME_DOCX:
        from app.services.generador_escritos_docx import validar_plantilla_docx
        return validar_plantilla_docx(datos)

    return (f'Formato de plantilla no soportado: "{formato}". '
            f'Se admiten {", ".join(sorted(TIPOS_CONTENIDO))}.')


def advertencias_plantilla(datos: bytes, formato: str) -> list[str]:
    """
    Avisos de canonicidad (ADR-035 §5, #727). Solo el motor .odt los tiene: el
    concepto de plantilla base no existe para .docx.

    No decide si la plantilla entra —eso es `validar_plantilla`—: son avisos,
    no errores. El criterio del proyecto es admitir con justificación, y una
    plantilla que se aparta de la base no es un acto administrativo inválido,
    solo una hoja de estilos distinta de la común.

    Returns:
        list[str] — avisos listos para enseñar al supervisor. Vacía si no hay
        nada que decir (no implica que la plantilla sea válida).
    """
    if formato != MIME_ODT:
        return []
    from app.services.plantilla_canonica_odt import comprobar_canonicidad
    return comprobar_canonicidad(datos)
