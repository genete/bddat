"""Alta de expediente: proyecto + expediente + documento de solicitud + solicitud (#428).

Una transacción y un solo punto de entrada, compartido por el formulario de alta y
por los scripts de expediente-tipo. Antes de esto el alta vivía en el paso 3 del
wizard y el script la replicaba a mano, con el resultado previsible: la copia se
quedó atrás y ninguna de las dos escribía el ancla documental de la solicitud.

EL INVARIANTE
=============

**No hay alta sin documento de solicitud.** No es una regla de motor ni admite
escape por justificación: de la `fecha_administrativa` de ese documento cuelga la
fecha de inicio del plazo para resolver y notificar, y sin ella el art. 128 RD
1955/2000 no computa —el motor devuelve `SIN_PLAZO`— y las suspensiones del art.
22 LPACAP se restan contra nada. Un expediente sin ese documento no es un
expediente con un dato pendiente: es uno cuyo plazo principal no ha empezado a
correr y nadie lo sabe.

`heredado` no exime. Marca que el expediente viene del sistema anterior con datos
incompletos, pero hoy ese flag solo se pinta —ningún servicio lo lee— y aceptarlo
como excusa reabriría por la puerta de atrás justo el agujero que este servicio
cierra.

EL ORDEN, QUE ES FORZOSO
========================

    proyecto → municipios → numero_at → expediente (flush)
        → documento al pool → solicitud con ancla → acreditativo del TITULAR → commit

`Documento.expediente_id` es NOT NULL y su ruta física es `AT-N/pool/…`, con el
`numero_at` saliendo del contador atómico dentro de la transacción: el documento no
puede existir antes que el expediente. De ahí se sigue que el signal `after_insert`
de `Expediente` **no puede** rellenar el acreditativo del interesado TITULAR —corre
en el flush del expediente, cuando el documento todavía no existe—. El signal deja
la fila puesta y aquí se completa, unas líneas después y en la misma transacción.

LA LIMPIEZA
===========

El sistema de ficheros no es transaccional. Si el commit falla, el rollback
devuelve el `numero_at` al contador y el siguiente expediente reutiliza ese número,
heredando una carpeta con el documento del intento fallido. Por eso el manejador
borra lo que escribió — ver `_limpiar_alta_fallida` para por qué ahí es seguro y en
ningún otro sitio lo sería.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from flask import current_app

from app import db
from app.models.documentos import Documento
from app.models.expedientes import Expediente
from app.models.municipios_proyecto import MunicipioProyecto
from app.models.proyectos import Proyecto
from app.models.solicitudes import Solicitud
from app.models.tipos_documentos import TipoDocumento
from app.models.tipos_solicitudes import TipoSolicitud
from app.services.ingesta_pool import ingestar_en_pool

log = logging.getLogger(__name__)

# Tipo documental del escrito que abre el procedimiento. Por código y nunca por id:
# es 146 en desarrollo y 56 en una instalación limpia (#849).
CODIGO_DOC_SOLICITUD = 'MODELO_SOLICITUD'

# El mismo texto para la ruta, el script y el test: si el alta se rechaza, que los
# tres digan por qué con las mismas palabras.
MENSAJE_SIN_ANCLA = (
    'Debe adjuntar el escrito de solicitud y su fecha de registro de entrada: '
    'de esa fecha cuelga el inicio del plazo para resolver, y sin ella el '
    'expediente nace sin plazo que computar.'
)


@dataclass(frozen=True)
class DocumentoSolicitud:
    """El escrito que abre el procedimiento, tal y como llega antes de existir.

    `fecha_registro` es la fecha de registro de entrada, y acaba siendo la
    `fecha_administrativa` del documento. El modelo la valida: futura, no se admite
    (#824).
    """
    contenido: bytes
    nombre_original: str
    fecha_registro: date


@dataclass(frozen=True)
class DatosAlta:
    """Todo lo que hace falta para dar de alta un expediente, de una pieza."""
    # --- Expediente ---
    tipo_expediente_id: int
    responsable_id: Optional[int]
    heredado: bool

    # --- Proyecto ---
    titulo: str
    descripcion: str
    finalidad: str
    emplazamiento: str
    fecha_proyecto: date
    ia_id: Optional[int]
    municipios_ids: list[int]

    # --- Solicitud ---
    titular_id: int
    tipo_solicitud_id: int
    # Puede diferir del titular cuando actúa un autorizado. Quien llama ya ha
    # comprobado la autorización (AutorizadoTitular.puede_actuar_como).
    solicitante_id: int
    observaciones: Optional[str] = None

    # --- Ancla documental (obligatoria, ver EL INVARIANTE) ---
    documento: Optional[DocumentoSolicitud] = None

    # Campos extra del proyecto que el formulario no pide pero los
    # expedientes-tipo sí fijan (es_modificacion, sin_linea_aerea…).
    proyecto_extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ResultadoAlta:
    expediente: Expediente
    solicitud: Solicitud
    documento: Documento
    numero_at: int


def alta_expediente(datos: DatosAlta) -> ResultadoAlta:
    """Da de alta el expediente completo, o no deja rastro de haberlo intentado.

    Raises:
        ValueError: si falta el documento de solicitud (`MENSAJE_SIN_ANCLA`), o si
            el catálogo no tiene el tipo documental o el tipo de solicitud pedidos.
            El llamador decide cómo contarlo: la ruta repinta el formulario, el
            script aborta.
        Cualquier otra: se propaga tras deshacer la transacción y borrar los
            ficheros escritos.

    La dependencia de catálogo no se degrada, al contrario que en el resto de
    servicios (#347): sin el tipo documental no hay documento, sin documento no hay
    ancla y sin ancla no debe haber expediente. Devolver algo degradado aquí es
    exactamente lo que este servicio existe para impedir.
    """
    if datos.documento is None or not datos.documento.contenido:
        raise ValueError(MENSAJE_SIN_ANCLA)

    tipo_doc = TipoDocumento.query.filter_by(codigo=CODIGO_DOC_SOLICITUD).first()
    if tipo_doc is None:
        raise ValueError(
            f'El catálogo no tiene el tipo de documento {CODIGO_DOC_SOLICITUD!r}, '
            'necesario para clasificar el escrito de solicitud.'
        )

    tipo_solicitud = TipoSolicitud.query.get(datos.tipo_solicitud_id)
    if tipo_solicitud is None:
        raise ValueError('El tipo de solicitud seleccionado no existe.')

    ingestado = None
    numero_at = None
    try:
        # 1) Proyecto y sus municipios
        proyecto = Proyecto(
            titulo=datos.titulo,
            descripcion=datos.descripcion,
            finalidad=datos.finalidad,
            emplazamiento=datos.emplazamiento,
            fecha=datos.fecha_proyecto,
            ia_id=datos.ia_id,
            **datos.proyecto_extra,
        )
        db.session.add(proyecto)
        db.session.flush()          # → proyecto.id

        for municipio_id in datos.municipios_ids:
            db.session.add(MunicipioProyecto(
                municipio_id=municipio_id, proyecto_id=proyecto.id))

        # 2) numero_at — contador gapless (UPDATE atómico; el rollback lo devuelve
        #    y no deja hueco en la numeración). Ver docs/fuentesIA/numero_at_gapless.md
        numero_at = db.session.execute(
            db.text('UPDATE public.contador_numero_at SET valor = valor + 1 RETURNING valor')
        ).scalar()

        # 3) Expediente. El signal after_insert crea el histórico INICIAL de titular
        #    y la fila TITULAR de interesados_expediente, esta última sin acreditativo
        #    porque el documento aún no existe (se completa en el punto 6).
        expediente = Expediente(
            numero_at=numero_at,
            responsable_id=datos.responsable_id,
            tipo_expediente_id=datos.tipo_expediente_id,
            heredado=datos.heredado,
            proyecto_id=proyecto.id,
            titular_id=datos.titular_id,
        )
        db.session.add(expediente)
        db.session.flush()          # → expediente.id, y dispara el signal

        # 4) El escrito de solicitud entra al pool como cualquier otro documento
        ingestado = ingestar_en_pool(
            expediente,
            datos.documento.contenido,
            datos.documento.nombre_original,
            tipo_doc_id=tipo_doc.id,
            fecha_administrativa=datos.documento.fecha_registro,
            asunto=f'Solicitud de {tipo_solicitud.siglas}',
        )
        db.session.flush()          # → documento.id

        # 5) Solicitud, ya anclada
        solicitud = Solicitud(
            expediente_id=expediente.id,
            entidad_id=datos.solicitante_id,
            tipo_solicitud_id=datos.tipo_solicitud_id,
            documento_solicitud_id=ingestado.documento.id,
            observaciones=datos.observaciones,
        )
        db.session.add(solicitud)

        # 6) El acreditativo del TITULAR es ese mismo documento: la solicitud es lo
        #    que lo acredita como interesado (#374). SQL y no ORM porque la fila la
        #    insertó el signal a nivel Core y no está en la identity map de la sesión.
        db.session.execute(
            db.text('UPDATE public.interesados_expediente '
                    'SET documento_acreditativo_id = :doc '
                    'WHERE expediente_id = :exp AND tipo_origen = :tipo'),
            {'doc': ingestado.documento.id, 'exp': expediente.id, 'tipo': 'TITULAR'},
        )

        db.session.commit()

    except Exception:
        db.session.rollback()
        _limpiar_alta_fallida(ingestado, numero_at)
        raise

    return ResultadoAlta(
        expediente=expediente,
        solicitud=solicitud,
        documento=ingestado.documento,
        numero_at=numero_at,
    )


def _limpiar_alta_fallida(ingestado, numero_at) -> None:
    """Retira del disco lo que escribió un alta que no llegó a cuajar.

    Aquí es seguro borrar y en ningún otro sitio lo sería: este `AT-N/` acaba de
    nacer en esta misma transacción —el `numero_at` sale del contador unas líneas
    antes— así que no había nada dentro que no hayamos puesto nosotros.

    Aun así se borra por lo fino, nunca con `rmtree`: primero el fichero que consta
    escrito (`fichero_escrito`, que un duplicado exacto pone a False — ahí el
    fichero es de otro documento que sí lo usa), y después las carpetas con
    `os.rmdir`, que se niega a borrar una que no esté vacía. Si el contador llegara
    a repetir un número cuya carpeta tuviera contenido ajeno, esto no lo tocaría.

    Los fallos de borrado se loguean y no se propagan: la excepción que importa es
    la que trajo hasta aquí, y taparla con un error de permisos de fichero dejaría
    al usuario sin saber por qué no se creó su expediente.
    """
    if ingestado is not None and ingestado.fichero_escrito:
        try:
            os.remove(ingestado.ruta_absoluta)
        except OSError as exc:
            log.warning('alta fallida: no se pudo borrar %s — %s',
                        ingestado.ruta_absoluta, exc)

    if numero_at is None:
        return

    base = current_app.config.get('FILESYSTEM_BASE', '')
    if not base:
        return

    raiz = os.path.join(base, f'AT-{numero_at}')
    for carpeta in (os.path.join(raiz, 'pool'), raiz):
        try:
            os.rmdir(carpeta)
        except OSError:
            # No está vacía o no existe: en ambos casos no es nuestra para borrarla.
            break
