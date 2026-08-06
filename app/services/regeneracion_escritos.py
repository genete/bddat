"""
Servicio de regeneración de escritos de tarea ELABORAR (#730).

RESPONSABILIDAD:
    Decide qué debe pasar cuando se (re)genera el escrito de una tarea y lo
    ejecuta. El draft de una tarea es único (rol CONSUMIDO + tipo_doc_id de la
    plantilla): en cuanto existe, SIEMPRE se reutiliza esa misma fila
    `Documento` — nunca se crea una segunda. Es la intención original de B6
    (#167), rota desde que #665 (ADR-032 §3) empezó a reescribir `Documento.url`
    al vincular, dejando inservible la búsqueda por comparación de rutas.

MATRIZ DE CASOS (issue #730, tabla completa en el cuerpo del issue):
    1 - Sin draft previo, sin colisión                              -> alta directa
    2 - Sin draft previo, colisión externa                          -> requiere decisión
    3 - Draft previo, hash igual, nombre igual                      -> no-op
    4 - Draft previo, hash igual, nombre distinto, sin colisión     -> renombrado puro
    5 - Draft previo, hash igual, nombre distinto, con colisión     -> requiere decisión
    6 - Draft previo, hash distinto, nombre igual                   -> requiere decisión (sustitución)
    7 - Draft previo, hash distinto, nombre distinto, sin colisión  -> requiere decisión (sustitución)
    8 - Draft previo, hash distinto, nombre distinto, con colisión  -> requiere decisión (combinada)

El fichero físico del draft anterior, cuando el contenido cambia (casos 6/7/8),
se aparta en el mismo sitio con el timestamp del propio fichero como sufijo:
queda ajeno a bddat (ninguna fila lo referencia) pero recuperable por su código
de seguimiento embebido en el pie de página (#182/#717). Nunca pasa por pool/:
el escrito es un auxiliar de trabajo (#608), nunca perteneció al expediente.

FUERA DE ALCANCE:
    El rol PRODUCIDO (reasignar el documento firmado) no pasa por aquí — es un
    problema propio, ligado a automatizar firma+asignación sin intervención del
    usuario (nota de Carlos en #730), con su propio issue futuro.
"""
import hashlib
import os
from dataclasses import dataclass
from datetime import datetime

from app import db
from app.models.documentos import Documento
from app.models.documentos_tarea import DocumentoTarea
from app.services.generador_escritos import guardar_documento, tipo_contenido_documento

CASOS_CON_CONFIRMACION = {2, 5, 6, 7, 8}


@dataclass
class Evaluacion:
    caso: int
    documento_existente: Documento | None
    hash_coincide: bool | None
    nombre_coincide: bool | None
    colision_nombre: str | None  # nombre del fichero ajeno que ocupa el destino, o None
    requiere_confirmacion: bool


def localizar_draft_vinculado(tarea, rol: str, tipo_doc_id: int) -> Documento | None:
    """El draft de una tarea (rol + tipo_doc_id de la plantilla) es la identidad
    estable que sustituye a la comparación de `Documento.url` (#730): no depende
    de dónde viva físicamente el fichero."""
    vinculo = next(
        (v for v in tarea.vinculos_documento
         if v.rol == rol and v.documento.tipo_doc_id == tipo_doc_id),
        None,
    )
    return vinculo.documento if vinculo else None


def _hay_colision_externa(ruta_destino_abs: str, documento_existente: Documento | None) -> bool:
    """Ocupado por un fichero que no es el propio draft a sustituir ni el origen."""
    if not os.path.exists(ruta_destino_abs):
        return False
    if documento_existente is not None:
        try:
            origen_abs = documento_existente.ruta_absoluta()
        except (RuntimeError, ValueError):
            origen_abs = None
        if origen_abs and os.path.normpath(origen_abs) == os.path.normpath(ruta_destino_abs):
            return False
    return True


def evaluar_regeneracion(*, tarea, rol: str, tipo_doc_id: int, doc_bytes: bytes,
                         nombre_fichero: str, ruta_destino_abs: str) -> Evaluacion:
    """Decide qué caso de la matriz aplica. No escribe nada — solo lectura."""
    documento_existente = localizar_draft_vinculado(tarea, rol, tipo_doc_id)
    hash_nuevo = hashlib.md5(doc_bytes).hexdigest()

    if documento_existente is None:
        hay_colision = _hay_colision_externa(ruta_destino_abs, None)
        colision = os.path.basename(ruta_destino_abs) if hay_colision else None
        caso = 2 if hay_colision else 1
        return Evaluacion(caso, None, None, None, colision, caso in CASOS_CON_CONFIRMACION)

    hash_coincide = bool(documento_existente.hash_md5) and documento_existente.hash_md5 == hash_nuevo
    nombre_actual = os.path.basename(documento_existente.url)
    nombre_coincide = nombre_actual == nombre_fichero

    if hash_coincide and nombre_coincide:
        return Evaluacion(3, documento_existente, True, True, None, False)

    if hash_coincide:  # nombre distinto — renombrado puro
        hay_colision = _hay_colision_externa(ruta_destino_abs, documento_existente)
        colision = os.path.basename(ruta_destino_abs) if hay_colision else None
        caso = 5 if hay_colision else 4
        return Evaluacion(caso, documento_existente, True, False, colision, caso in CASOS_CON_CONFIRMACION)

    if nombre_coincide:
        # El ocupante del destino es el propio draft a sustituir: nunca colisión externa.
        return Evaluacion(6, documento_existente, False, True, None, True)

    hay_colision = _hay_colision_externa(ruta_destino_abs, documento_existente)
    colision = os.path.basename(ruta_destino_abs) if hay_colision else None
    caso = 8 if hay_colision else 7
    return Evaluacion(caso, documento_existente, False, False, colision, True)


def _apartar_fichero_anterior(documento: Documento) -> None:
    """Aparta el fichero físico del draft anterior en el mismo sitio, con el
    timestamp del propio fichero como sufijo. Queda ajeno a bddat (ninguna fila
    lo referencia ya) pero recuperable por su código de seguimiento embebido."""
    try:
        origen_abs = documento.ruta_absoluta()
    except (RuntimeError, ValueError):
        return
    if not os.path.exists(origen_abs):
        return
    _renombrar_con_sufijo(origen_abs, sufijo='')


def _renombrar_ajeno_aparte(ruta_ocupada_abs: str) -> None:
    """Aparta un fichero ajeno a bddat que ocupa el destino (decisión del
    usuario en el popup de colisión, #730). No se toca su contenido."""
    _renombrar_con_sufijo(ruta_ocupada_abs, sufijo='_ajeno')


def _renombrar_con_sufijo(ruta_abs: str, *, sufijo: str) -> str:
    timestamp = datetime.fromtimestamp(os.path.getmtime(ruta_abs)).strftime('%Y%m%d_%H%M%S')
    base, ext = os.path.splitext(ruta_abs)
    destino = f'{base}{sufijo}_{timestamp}{ext}'
    n = 1
    while os.path.exists(destino):
        destino = f'{base}{sufijo}_{timestamp}_{n}{ext}'
        n += 1
    os.rename(ruta_abs, destino)
    return destino


def _ruta_alternativa(ruta_destino_abs: str) -> str:
    """Nombre libre para el fichero nuevo cuando el usuario elige no desplazar
    al ajeno (decisión 'renombrar_nuevo' del popup de colisión)."""
    base, ext = os.path.splitext(ruta_destino_abs)
    n = 2
    candidato = f'{base}_{n}{ext}'
    while os.path.exists(candidato):
        n += 1
        candidato = f'{base}_{n}{ext}'
    return candidato


def _renombrar_en_sitio(documento: Documento, ruta_destino_abs: str, fs_base: str) -> None:
    """Renombrado puro (casos 4/5): mismo contenido, solo cambia el nombre."""
    origen_abs = documento.ruta_absoluta()
    if os.path.normpath(origen_abs) != os.path.normpath(ruta_destino_abs):
        os.rename(origen_abs, ruta_destino_abs)
        documento.url = os.path.relpath(ruta_destino_abs, fs_base).replace(os.sep, '/')


def ejecutar_regeneracion(*, tarea, expediente, plantilla, doc_bytes: bytes,
                          nombre_fichero: str, ruta_destino_abs: str, fs_base: str,
                          rol: str, asunto: str, evaluacion: Evaluacion,
                          decision_colision: str | None = None) -> Documento:
    """Ejecuta el caso ya decidido por `evaluar_regeneracion()`. No vuelve a
    decidir nada: `evaluacion` (y `decision_colision`, si el caso lo pedía) ya
    fijaron qué hacer.

    decision_colision: 'renombrar_nuevo' | 'renombrar_existente', obligatorio
    cuando `evaluacion.colision_nombre` no es None.
    """
    documento = evaluacion.documento_existente
    ruta_destino_final_abs = ruta_destino_abs
    nombre_final = nombre_fichero

    if evaluacion.colision_nombre:
        if decision_colision == 'renombrar_existente':
            _renombrar_ajeno_aparte(ruta_destino_abs)
        elif decision_colision == 'renombrar_nuevo':
            ruta_destino_final_abs = _ruta_alternativa(ruta_destino_abs)
            nombre_final = os.path.basename(ruta_destino_final_abs)
        else:
            raise ValueError(f'decisión de colisión no reconocida: {decision_colision!r}')

    if evaluacion.caso == 3:
        return documento

    if evaluacion.caso in (4, 5):
        _renombrar_en_sitio(documento, ruta_destino_final_abs, fs_base)
        return documento

    if documento is not None:
        _apartar_fichero_anterior(documento)

    guardar_documento(doc_bytes, ruta_destino_final_abs)
    ruta_relativa = os.path.relpath(ruta_destino_final_abs, fs_base).replace(os.sep, '/')
    hash_nuevo = hashlib.md5(doc_bytes).hexdigest()

    if documento is None:
        documento = Documento(
            expediente_id=expediente.id,
            url=ruta_relativa,
            tipo_doc_id=plantilla.tipo_documento_id,
            tipo_contenido=tipo_contenido_documento(nombre_final),
            asunto=asunto,
            hash_md5=hash_nuevo,
        )
        db.session.add(documento)
        db.session.flush()
        tarea.vinculos_documento.append(DocumentoTarea(documento_id=documento.id, rol=rol))
    else:
        documento.url = ruta_relativa
        documento.hash_md5 = hash_nuevo

    return documento
