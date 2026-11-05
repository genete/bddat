"""Alta de expediente: proyecto + expediente + documentos de solicitud y de proyecto + solicitud (#428, #1040).

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

`heredado` no exime del documento de solicitud. Marca que el expediente viene del
sistema anterior con datos incompletos, pero aceptarlo como excusa reabriría por la
puerta de atrás justo el agujero que este servicio cierra.

EL PROYECTO PRINCIPAL (#1040, ADR-044 §D)
=========================================

**Tampoco hay alta sin documento de proyecto, salvo en un expediente heredado.** El
proyecto nace con su ancla (`proyectos.documento_principal_id`) puesta: el documento
que se sube con el alta es el proyecto principal, y los modificados o reformados
entran después por el pool. Un expediente sin ancla no se puede tramitar más allá del
análisis (regla de motor de #887, RD 1955/2000 arts. 123.1 y 130.1), y un alta que lo
fabricara dejaría la falta sin que nadie la viera hasta el certificado de fin de
instrucción. La fecha administrativa del documento es la `fecha_proyecto` del alta.

El expediente heredado queda exento: llega del sistema anterior sin ese documento y su
tratamiento está por decidir. La regla de motor lo exime por su cuenta
(`expediente_heredado`). Si trae el fichero, se ancla igual.

El alta no escribe en la bitácora —el proyecto y el expediente nacen sin entrada—, y
el ancla inicial tampoco: forma parte de crear el proyecto, no del gesto de
anclar un documento sobre otro ya existente.

EL ORDEN, QUE ES FORZOSO
========================

    proyecto → municipios → numero_at → expediente (flush)
        → documentos al pool → ancla del proyecto → solicitud con ancla
        → acreditativo del TITULAR → commit

`Documento.expediente_id` es NOT NULL: el documento no puede existir antes que el
expediente. De ahí se sigue que el signal `after_insert` de `Expediente` **no puede**
rellenar el acreditativo del interesado TITULAR —corre en el flush del expediente,
cuando el documento todavía no existe—. El signal deja la fila puesta y aquí se
completa, unas líneas después y en la misma transacción.

EL CONTENIDO DE UN ALTA FALLIDA
===============================

El almacén no es transaccional. Si el commit falla, el rollback deshace el
expediente y el documento, pero no el contenido que el almacén ya recibió: queda sin
referencias y lo recoge la limpieza (ADR-050 §G, fase 7). El `numero_at` vuelve al
contador y el siguiente expediente lo reutiliza sin heredar nada, porque el contenido
no depende del número.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from app import db
from app.models.documentos import Documento
from app.models.expedientes import Expediente
from app.models.municipios_proyecto import MunicipioProyecto
from app.models.proyectos import Proyecto
from app.models.solicitudes import Solicitud
from app.models.tipos_documentos import TipoDocumento
from app.models.tipos_solicitudes import TipoSolicitud
from app.services.ingesta_pool import FicheroAIngestar, ingestar_en_pool

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

# Tipo documental del proyecto técnico que se ancla en el alta (#1040).
CODIGO_DOC_PROYECTO = 'DOC_PROYECTO'

MENSAJE_SIN_PROYECTO = (
    'Debe adjuntar el proyecto técnico: es el documento que queda anclado como '
    'proyecto principal del expediente, y sin él no se puede tramitar más allá del '
    'análisis de la solicitud (RD 1955/2000, arts. 123.1 y 130.1).'
)


@dataclass(frozen=True)
class DocumentoProyecto:
    """El proyecto técnico que se sube con el alta y queda anclado como principal.

    Sin fecha propia: su `fecha_administrativa` es la `fecha_proyecto` de `DatosAlta`
    (la de firma o visado), que además es lo que ordena las versiones del proyecto
    (ADR-044 §C).
    """
    contenido: bytes
    nombre_original: str


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
    # El titular es el solicitante: la solicitud se contesta a él (#989).
    titular_id: int
    tipo_solicitud_id: int
    observaciones: Optional[str] = None
    # Quien actúa por el titular y recibe las notificaciones (ADR-051 §K):
    # un autorizado suyo, opcional.
    representante_entidad_id: Optional[int] = None
    # La sede del titular que figura en la solicitud: la dirección del oficio
    # y, sin representante, el correo de aviso. Opcional: sin ella, la ficha.
    direccion_notificacion_id: Optional[int] = None

    # --- Ancla documental (obligatoria, ver EL INVARIANTE) ---
    documento: Optional[DocumentoSolicitud] = None

    # --- Ancla del proyecto (obligatoria salvo en un expediente heredado) ---
    documento_proyecto: Optional[DocumentoProyecto] = None

    # Campos extra del proyecto que el formulario no pide pero los
    # expedientes-tipo sí fijan (es_modificacion, sin_linea_aerea…).
    proyecto_extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ResultadoAlta:
    expediente: Expediente
    solicitud: Solicitud
    documento: Documento
    numero_at: int
    # El proyecto principal anclado; None solo en un expediente heredado sin fichero.
    documento_proyecto: Optional[Documento] = None


def alta_expediente(datos: DatosAlta) -> ResultadoAlta:
    """Da de alta el expediente completo, o no deja rastro de haberlo intentado.

    Raises:
        ValueError: si falta el documento de solicitud (`MENSAJE_SIN_ANCLA`), si
            falta el del proyecto en un expediente que no es heredado
            (`MENSAJE_SIN_PROYECTO`, #1040), si
            el catálogo no tiene el tipo documental o el tipo de solicitud pedidos,
            o si el representante o la sede no valen (`mutaciones_arbol.
            validar_representante` y `validar_sede`, las mismas reglas que al
            crear o editar una solicitud), o si el escrito de solicitud no es de un
            formato admitido (`FormatoNoAdmitido`, con mensaje para el usuario). El
            llamador decide cómo contarlo: la ruta repinta el formulario, el script
            aborta.
        `AlmacenNoDisponible`: el almacén no contesta; reintentar en unos minutos.
        Cualquier otra: se propaga tras deshacer la transacción.

    La dependencia de catálogo no se degrada, al contrario que en el resto de
    servicios (#347): sin el tipo documental no hay documento, sin documento no hay
    ancla y sin ancla no debe haber expediente. Devolver algo degradado aquí es
    exactamente lo que este servicio existe para impedir.
    """
    if datos.documento is None or not datos.documento.contenido:
        raise ValueError(MENSAJE_SIN_ANCLA)

    # Un fichero vacío cuenta como ausente: en un heredado se ignora; en el resto, rechaza.
    proyecto_adjunto = (datos.documento_proyecto
                        if datos.documento_proyecto is not None
                        and datos.documento_proyecto.contenido else None)
    if proyecto_adjunto is None and not datos.heredado:
        raise ValueError(MENSAJE_SIN_PROYECTO)

    tipo_doc = TipoDocumento.query.filter_by(codigo=CODIGO_DOC_SOLICITUD).first()
    if tipo_doc is None:
        raise ValueError(
            f'El catálogo no tiene el tipo de documento {CODIGO_DOC_SOLICITUD!r}, '
            'necesario para clasificar el escrito de solicitud.'
        )

    tipo_doc_proyecto = None
    if proyecto_adjunto is not None:
        tipo_doc_proyecto = TipoDocumento.query.filter_by(codigo=CODIGO_DOC_PROYECTO).first()
        if tipo_doc_proyecto is None:
            raise ValueError(
                f'El catálogo no tiene el tipo de documento {CODIGO_DOC_PROYECTO!r}, '
                'necesario para clasificar el proyecto técnico.'
            )

    tipo_solicitud = TipoSolicitud.query.get(datos.tipo_solicitud_id)
    if tipo_solicitud is None:
        raise ValueError('El tipo de solicitud seleccionado no existe.')

    # Representante y sede (#989, ADR-051 §K): error si no valen.
    from app.services.mutaciones_arbol import validar_representante, validar_sede
    error = (validar_representante(datos.titular_id, datos.representante_entidad_id)
             or validar_sede(datos.titular_id, datos.direccion_notificacion_id))
    if error:
        raise ValueError(error)

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

        # 4) El escrito de solicitud y, si lo hay, el proyecto entran al pool como
        #    cualquier otro documento, en una sola llamada: ingestar valida los
        #    ficheros de todos antes de enviar el primero al almacén.
        ficheros = [FicheroAIngestar(
            io.BytesIO(datos.documento.contenido),
            datos.documento.nombre_original,
            tipo_doc_id=tipo_doc.id,
            fecha_administrativa=datos.documento.fecha_registro,
            asunto=f'Solicitud de {tipo_solicitud.siglas}',
        )]
        if proyecto_adjunto is not None:
            ficheros.append(FicheroAIngestar(
                io.BytesIO(proyecto_adjunto.contenido),
                proyecto_adjunto.nombre_original,
                tipo_doc_id=tipo_doc_proyecto.id,
                fecha_administrativa=datos.fecha_proyecto,
                asunto=f'Proyecto técnico: {datos.titulo}'[:200],
            ))
        documentos = ingestar_en_pool(expediente, ficheros)
        documento = documentos[0]
        documento_proyecto = documentos[1] if proyecto_adjunto is not None else None
        db.session.add_all(documentos)
        db.session.flush()          # → ids

        # 4 bis) El proyecto principal queda anclado. Por la relación y no por el id,
        #        como `anclar_principal`, para que el backref del documento quede
        #        poblado en la misma sesión. Sin bitácora: ver el docstring del módulo.
        if documento_proyecto is not None:
            proyecto.documento_principal = documento_proyecto
            db.session.flush()

        # 5) Solicitud, ya anclada
        solicitud = Solicitud(
            expediente_id=expediente.id,
            entidad_id=datos.titular_id,
            representante_entidad_id=datos.representante_entidad_id,
            direccion_notificacion_id=datos.direccion_notificacion_id,
            tipo_solicitud_id=datos.tipo_solicitud_id,
            documento_solicitud_id=documento.id,
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
            {'doc': documento.id, 'exp': expediente.id, 'tipo': 'TITULAR'},
        )

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return ResultadoAlta(
        expediente=expediente,
        solicitud=solicitud,
        documento=documento,
        numero_at=numero_at,
        documento_proyecto=documento_proyecto,
    )
