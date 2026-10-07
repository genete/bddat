"""
Servicio de regeneración de escritos de tarea ELABORAR (#730).

RESPONSABILIDAD:
    Decide qué debe pasar cuando se (re)genera el escrito de una tarea y lo
    ejecuta. El borrador de una tarea es único (rol CONSUMIDO + tipo_doc_id de la
    plantilla): en cuanto existe, SIEMPRE se reutiliza esa misma fila
    `Documento` — nunca se crea una segunda. Es la intención original de B6
    (#167), rota desde que #665 (ADR-032 §3) empezó a reescribir `Documento.url`
    al vincular, dejando inservible la búsqueda por comparación de rutas.

DOS CASOS (ADR-050, #1007; antes, una matriz de 8 casos con colisiones de nombre
y apartado de ficheros en el árbol):
    1. Sin borrador: el escrito se sube al almacén y se vincula como CONSUMIDO de
       la tarea. El nombre lo pone el sistema (`componer_nombre_documento`).
    2. Con borrador: si el contenido es el mismo no se hace nada; si es distinto
       se sustituye sin preguntar —hasta la fase 5, que traerá la confirmación
       cuando el borrador se haya retocado— con `cambiar_contenido`: el documento
       se conserva (mismo id, mismo nombre, mismos vínculos) y la bitácora anota
       el hash anterior y el nuevo. El contenido anterior no se toca: lo recoge la
       limpieza del almacén (fase 7).

    «El mismo contenido» es el mismo SHA-256. Lo cumple el .odt, el formato de
    referencia (ADR-035), porque su generación es determinista. El .docx, un
    motor en retirada, no lo es (python-docx sella la hora en las entradas del ZIP):
    regenerarlo cuenta siempre como contenido distinto y deja su entrada en la
    bitácora aunque el texto no cambie. Es conocido y se acepta (ADR-035 §2).

    Si el contenido es el mismo pero el almacén ya no lo tiene (borrador ausente o
    dañado), no se dice «sin cambios»: se avisa, con `ContenidoNoUtilizable`.

FUERA DE ALCANCE:
    El rol PRODUCIDO (reasignar el documento firmado) no pasa por aquí — es un
    problema propio, ligado a automatizar firma+asignación sin intervención del
    usuario (nota de Carlos en #730), con su propio issue futuro.
"""
from dataclasses import dataclass
from io import BytesIO

from app import db
from app.models.documentos import Documento
from app.models.documentos_tarea import DocumentoTarea
from app.services.almacenamiento.contenido import (
    VIA_REGENERACION, EntradaSubida, cambiar_contenido, comprobar_para_vincular, subir,
)

GENERADO = 'GENERADO'        # no había borrador: se ha subido y vinculado
SIN_CAMBIOS = 'SIN_CAMBIOS'  # había borrador y el contenido es el mismo
SUSTITUIDO = 'SUSTITUIDO'    # había borrador y se ha cambiado su contenido


@dataclass
class ResultadoRegeneracion:
    resultado: str          # GENERADO · SIN_CAMBIOS · SUSTITUIDO
    documento: Documento


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


def regenerar_escrito(*, tarea, expediente, plantilla, doc_bytes: bytes,
                      nombre_fichero: str, asunto: str, usuario_id: int,
                      rol: str = 'CONSUMIDO') -> ResultadoRegeneracion:
    """Sube el escrito o sustituye el del borrador, según haya o no borrador.

    No hace commit: el documento, el vínculo y la entrada de bitácora van en la
    sesión de quien llama. Los documentos no se añaden a la sesión por `subir`;
    aquí se añade el de un escrito nuevo.

    Lanza `ValueError` si la tarea no es ELABORAR: aquí se vincula el escrito
    directamente, sin pasar por `editar_tarea`, y en una NOTIFICAR eso se saltaría
    el bloqueo sin destinatario y el hook (#967, ADR-051 §B). La guarda va dentro
    para que ningún llamador pueda saltársela; el endpoint conserva la suya delante
    para salir antes de generar el documento.

    Lanza `FormatoNoAdmitido` (el contenido no es lo que dice la extensión del
    nombre: p. ej. un borrador `.docx` cuya plantilla ahora genera `.odt`) y
    `ValueError` (el «borrador» no tiene contenido propio: un enlace del mismo tipo),
    con mensajes para el usuario; `AlmacenNoDisponible` si el almacén no contesta;
    y `ContenidoNoUtilizable` si el borrador ya estaba ausente o dañado y el
    escrito nuevo es idéntico (no hay nada que sustituir, pero tampoco está).
    """
    if not tarea.tipo_tarea or tarea.tipo_tarea.codigo != 'ELABORAR':
        raise ValueError('Los escritos se generan en la tarea ELABORAR')

    documento = localizar_draft_vinculado(tarea, rol, plantilla.tipo_documento_id)

    if documento is None:
        [documento] = subir([EntradaSubida(BytesIO(doc_bytes), nombre_fichero, {
            'expediente_id': expediente.id,
            'tipo_doc_id': plantilla.tipo_documento_id,
            'asunto': asunto,
        })])
        db.session.add(documento)
        db.session.flush()
        tarea.vinculos_documento.append(DocumentoTarea(documento_id=documento.id, rol=rol))
        return ResultadoRegeneracion(GENERADO, documento)

    if cambiar_contenido(documento, BytesIO(doc_bytes), via=VIA_REGENERACION, usuario_id=usuario_id):
        return ResultadoRegeneracion(SUSTITUIDO, documento)

    comprobar_para_vincular(documento)   # «sin cambios» solo si el contenido está de verdad
    return ResultadoRegeneracion(SIN_CAMBIOS, documento)
