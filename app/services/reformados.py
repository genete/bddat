"""El corte que parte el proyecto en versiones (ADR-044 §C).

Un reformado no es una entidad abstracta: **es** el documento que lo introduce.
Por eso aquí no hay CRUD de reformados —no hay pantalla que los administre— sino
una sola operación de alta, que se dispara desde la ingesta en el pool cuando
entra un `DOC_PROYECTO` y el técnico responde que sí produce corte.

La versión del proyecto es el **tramo entre cortes**, así que el orden importa y
sale de `documentos.fecha_administrativa` con el `id` de desempate. Esa es la razón
de que la fecha administrativa sea obligatoria para este tipo de documento: sin
cronología no hay tramos.

**No hace commit, a propósito**, igual que `ingesta_pool`: el alta del reformado
ocurre dentro de la misma transacción que crea el documento, y si el documento se
va, el corte se va con él.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.exc import OperationalError, ProgrammingError

from app import db
from app.models.documentos import Documento
from app.models.reformados_proyecto import ORIGENES_REFORMADO, ReformadoProyecto
from app.services import bitacora as bitacora_svc

log = logging.getLogger(__name__)

# El tipo de documento del que cuelga todo esto. Registrado en
# `app/checks/catalogo_requerido.py`: sin esta fila de catálogo el sistema no
# distingue un proyecto de cualquier otro papel del pool.
CODIGO_DOC_PROYECTO = 'DOC_PROYECTO'


def es_doc_proyecto(documento) -> bool:
    """True si el documento está clasificado como proyecto técnico.

    Degrada a False si el catálogo no responde (#347): el valor seguro es «no es
    proyecto», que a lo sumo deja de preguntar — nunca crea un corte a ciegas.
    """
    try:
        tipo = documento.tipo_doc
    except (OperationalError, ProgrammingError):
        log.warning('reformados: catálogo de tipos no disponible — documento tratado como no-proyecto')
        return False
    if tipo is None:
        return False
    return tipo.codigo == CODIGO_DOC_PROYECTO


def declarar_reformado(documento, origen: str, *, usuario_id: int) -> ReformadoProyecto:
    """Da de alta el corte que abre una versión nueva del proyecto (sin commit).

    Lanza `ValueError` con el motivo si el documento no puede abrir corte. Las
    cuatro puertas del pool lo llaman igual y traducen el error a su manera —la
    ruta a un 500 con el mensaje, el formulario a un aviso junto al campo—, mismo
    criterio que el validador de fecha futura de `Documento` (#824).
    """
    if not es_doc_proyecto(documento):
        raise ValueError('Solo un documento clasificado como proyecto puede abrir un reformado.')

    if documento.fecha_administrativa is None:
        raise ValueError(
            'El documento necesita fecha administrativa para abrir un reformado: '
            'es la que ordena las versiones del proyecto.'
        )

    if origen not in ORIGENES_REFORMADO:
        raise ValueError(f'Origen de reformado desconocido: {origen!r}')

    if documento.reformado_proyecto is not None:
        raise ValueError('Este documento ya abre un reformado de proyecto.')

    # Por la relación, no por `documento_id`: así el backref escalar
    # `documento.reformado_proyecto` queda poblado en la misma sesión, que es lo
    # que consulta la guarda del pool antes de que nadie recargue nada.
    reformado = ReformadoProyecto(documento=documento, origen=origen)
    db.session.add(reformado)
    db.session.flush()   # necesitamos el id para la bitácora

    # Declarar un reformado obliga a rehacer fases preceptivas: es un acto con
    # consecuencias, y por eso el ADR manda a bitácora quién lo declaró y cuándo
    # en vez de guardarlo como columna de la tabla.
    bitacora_svc.registrar(
        usuario_id, 'CREAR', 'reformados_proyecto', reformado.id,
        detalle={
            'documento_id': documento.id,
            'expediente_id': documento.expediente_id,
            'origen': origen,
            'fecha_administrativa': documento.fecha_administrativa.isoformat(),
        },
    )

    log.info('Reformado declarado: doc=%s expediente=%s origen=%s',
             documento.id, documento.expediente_id, origen)
    return reformado


def reformados_de(expediente_id: int) -> list:
    """Los cortes del expediente en el orden que define las versiones.

    `fecha_administrativa` primero, `id` de desempate: dos documentos pueden
    compartir fecha, y entonces manda el orden de entrada.
    """
    return (
        ReformadoProyecto.query
        .join(Documento, ReformadoProyecto.documento_id == Documento.id)
        .filter(Documento.expediente_id == expediente_id)
        .order_by(Documento.fecha_administrativa, Documento.id)
        .all()
    )


def ultimo_reformado(expediente_id: int) -> Optional[ReformadoProyecto]:
    """El corte más reciente, que es el único reversible.

    Se calcula en el momento y no se guarda: editar la fecha administrativa de un
    documento puede cambiar quién es el último.
    """
    cortes = reformados_de(expediente_id)
    return cortes[-1] if cortes else None
