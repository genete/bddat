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


MENSAJE_FECHA_OBLIGATORIA = (
    'Un documento de proyecto necesita fecha administrativa: es la que ordena las '
    'versiones del proyecto y decide a cuál pertenece cada documento.'
)


def exigir_fecha_administrativa(tipo_doc_id, fecha) -> None:
    """Comprobación temprana de la fecha obligatoria, antes de tocar el disco.

    El listener de `Documento` es la red final —cubre las cuatro puertas, los
    scripts y el shell—, pero salta en el flush, y en la ingesta multipart el flush
    llega **después** de escribir el fichero en el pool: el rollback devuelve la
    fila y deja el fichero (es el problema que documenta `ResultadoIngesta`). Por eso
    la puerta que escribe pregunta antes, con el mismo mensaje.
    """
    if fecha is not None or tipo_doc_id is None:
        return
    from app.models.tipos_documentos import TipoDocumento
    try:
        tipo = TipoDocumento.query.get(tipo_doc_id)
    except (OperationalError, ProgrammingError):
        log.warning('reformados: catálogo de tipos no disponible — sin comprobar la fecha')
        return
    if tipo is not None and tipo.codigo == CODIGO_DOC_PROYECTO:
        raise ValueError(MENSAJE_FECHA_OBLIGATORIA)


def declarar_desde_metadatos(documento, metadatos: dict, *, usuario_id: int):
    """Aplica a un documento recién ingestado la respuesta del paso de metadatos.

    Punto único de las tres puertas de alta del pool —multipart, rutas del servidor
    y URL externa—, y donde vive la bifurcación de §C: **la rama la decide el estado
    del ancla, no el cliente**. Así, en un lote de varios DOC_PROYECTO el primero
    puede anclar el proyecto y el siguiente ya se encuentra la otra pregunta, sin que
    quepan dos principales.

    La marca solo cuenta si el documento es de verdad un `DOC_PROYECTO`: el control
    de la interfaz solo existe mientras ese es el tipo elegido, así que una marca
    sobre otro tipo no es la declaración de nadie.
    """
    if not es_doc_proyecto(documento):
        return None

    if rama_de_la_ingesta(documento.expediente) == RAMA_PRINCIPAL:
        if metadatos.get('es_principal'):
            return anclar_principal(documento, usuario_id=usuario_id)
        return None

    if not metadatos.get('abre_reformado'):
        return None
    origen = (metadatos.get('origen_reformado') or '').strip().upper() or ORIGENES_REFORMADO[0]
    return declarar_reformado(documento, origen, usuario_id=usuario_id)


def revertir_reformado(documento, *, usuario_id: int) -> None:
    """Retira el corte que abre `documento`, si es el último (sin commit).

    La reversión no es un CRUD: el corte nace de una respuesta consciente en la
    ingesta y muere por el mismo control, desmarcándolo. Solo alcanza al último
    porque quitar uno intermedio fundiría dos tramos y dejaría a las fases de la
    versión desaparecida apuntando a nada (ADR-044 §C).
    """
    reformado = documento.reformado_proyecto
    if reformado is None:
        raise ValueError('Este documento no abre ningún reformado de proyecto.')

    ultimo = ultimo_reformado(documento.expediente_id)
    if ultimo is not None and ultimo.id != reformado.id:
        raise ValueError(
            'Solo se puede deshacer el último reformado del expediente. Este tiene '
            'versiones posteriores: deshágalas primero, en orden inverso.'
        )

    # Antes del delete: después no hay id que anotar.
    bitacora_svc.registrar(
        usuario_id, 'BORRAR', 'reformados_proyecto', reformado.id,
        detalle={
            'documento_id': documento.id,
            'expediente_id': documento.expediente_id,
            'origen': reformado.origen,
        },
    )
    db.session.delete(reformado)
    db.session.flush()

    log.info('Reformado revertido: doc=%s expediente=%s',
             documento.id, documento.expediente_id)


def sincronizar_reformado(documento, *, abre_reformado: bool, origen: Optional[str],
                          usuario_id: int) -> None:
    """Deja el corte del documento como dice la respuesta del usuario (sin commit).

    Es la traducción del control de la interfaz: una casilla que solo existe
    mientras el tipo elegido es `DOC_PROYECTO`, con el origen pegado a ella. De ahí
    salen los cuatro casos:

    - marcada y sin corte     → se declara
    - marcada y con corte     → solo puede cambiar el origen
    - desmarcada y con corte  → se revierte (si es el último)
    - desmarcada y sin corte  → nada que hacer

    **Si el documento no es un DOC_PROYECTO se ignora la marca y, si arrastraba un
    corte, se retira**: cambiar el tipo es desmarcar por la puerta de atrás, y el
    corte de un documento que ya no es proyecto no significa nada. El control estaba
    oculto, así que lo que llegue en el payload no es una declaración de nadie.
    """
    corte = documento.reformado_proyecto

    if not es_doc_proyecto(documento):
        if corte is not None:
            revertir_reformado(documento, usuario_id=usuario_id)
        return

    if not abre_reformado:
        if corte is not None:
            revertir_reformado(documento, usuario_id=usuario_id)
        return

    if corte is None:
        declarar_reformado(documento, origen or ORIGENES_REFORMADO[0], usuario_id=usuario_id)
        return

    nuevo_origen = origen or corte.origen
    if nuevo_origen != corte.origen:
        if nuevo_origen not in ORIGENES_REFORMADO:
            raise ValueError(f'Origen de reformado desconocido: {nuevo_origen!r}')
        anterior, corte.origen = corte.origen, nuevo_origen
        db.session.flush()
        bitacora_svc.registrar(
            usuario_id, 'ALTERAR', 'reformados_proyecto', corte.id,
            columna='origen', detalle={'de': anterior, 'a': nuevo_origen},
        )


# ---------------------------------------------------------------------------
# El ancla del proyecto principal (ADR-044 §D)
# ---------------------------------------------------------------------------
# Vive en este módulo y no en uno propio porque la puerta es la misma: al entrar un
# DOC_PROYECTO el sistema pregunta una cosa u otra según si el proyecto ya tiene
# principal (§C). Son las dos ramas de una bifurcación, no dos funcionalidades.

RAMA_PRINCIPAL = 'PRINCIPAL'    # «¿Es este el proyecto?»
RAMA_REFORMADO = 'REFORMADO'    # «¿Produce un reformado de proyecto?»


def rama_de_la_ingesta(expediente) -> str:
    """Qué se le pregunta a un DOC_PROYECTO que entra en este expediente.

    El discriminante es el **estado del ancla**, no la cronología: mientras el
    proyecto no tenga principal, cualquier DOC_PROYECTO es candidato a serlo; en
    cuanto lo tiene, la pregunta pasa a ser si abre una versión nueva.
    """
    proyecto = getattr(expediente, 'proyecto', None)
    if proyecto is None or proyecto.documento_principal_id is None:
        return RAMA_PRINCIPAL
    return RAMA_REFORMADO


def anclar_principal(documento, *, usuario_id: int):
    """Ancla `documento` como el proyecto del expediente (sin commit).

    Si ya había otro anclado, **mueve el ancla** y lo deja anotado: es el gesto que
    resuelve la divergencia detectada en el checklist (§D) y el que corrige un
    anclaje equivocado. El documento que suelta el ancla no se toca — sigue en el
    pool, y desde ese momento vuelve a ser borrable.
    """
    if not es_doc_proyecto(documento):
        raise ValueError('Solo un documento clasificado como proyecto puede ser el proyecto principal.')

    proyecto = documento.expediente.proyecto if documento.expediente else None
    if proyecto is None:
        raise ValueError('El expediente de este documento no tiene proyecto.')

    anterior = proyecto.documento_principal_id
    if anterior == documento.id:
        return proyecto

    # Por la relación, no por el id: así el backref
    # `documento.anclado_como_proyecto_principal` queda poblado en la misma sesión,
    # que es lo que consulta la guarda del pool (mismo motivo que en el corte, #885).
    proyecto.documento_principal = documento
    db.session.flush()

    bitacora_svc.registrar(
        usuario_id, 'ALTERAR' if anterior else 'CREAR', 'proyectos', proyecto.id,
        columna='documento_principal_id',
        detalle={'de': anterior, 'a': documento.id,
                 'expediente_id': documento.expediente_id},
    )
    log.info('Proyecto principal anclado: doc=%s proyecto=%s expediente=%s (antes %s)',
             documento.id, proyecto.id, documento.expediente_id, anterior)
    return proyecto


def desanclar_principal(proyecto, *, usuario_id: int) -> None:
    """Retira el ancla del proyecto principal (sin commit).

    No hay condición de «solo el último», como en los reformados: aquí no se corta
    una línea temporal, se deja de decir cuál es el proyecto. Lo que impide que el
    expediente siga así es la regla de motor de §D, no esta función.
    """
    anterior = proyecto.documento_principal_id
    if anterior is None:
        raise ValueError('Este proyecto no tiene documento principal anclado.')

    proyecto.documento_principal = None   # por la relación, para que el backref caiga
    db.session.flush()

    bitacora_svc.registrar(
        usuario_id, 'BORRAR', 'proyectos', proyecto.id,
        columna='documento_principal_id',
        detalle={'de': anterior, 'a': None},
    )
    log.info('Proyecto principal desanclado: proyecto=%s (era doc=%s)', proyecto.id, anterior)


def sincronizar_principal(documento, *, es_principal: bool, usuario_id: int) -> None:
    """Deja el ancla como dice la respuesta del usuario (sin commit).

    Mismo criterio que `sincronizar_reformado`: si el documento ha dejado de ser un
    DOC_PROYECTO, la marca no se interpreta y el ancla se retira — un proyecto no
    puede materializarse en un documento que ya no es el proyecto.
    """
    proyecto = documento.expediente.proyecto if documento.expediente else None
    era_principal = proyecto is not None and proyecto.documento_principal_id == documento.id

    if not es_doc_proyecto(documento):
        if era_principal:
            desanclar_principal(proyecto, usuario_id=usuario_id)
        return

    if es_principal and not era_principal:
        anclar_principal(documento, usuario_id=usuario_id)
    elif not es_principal and era_principal:
        desanclar_principal(proyecto, usuario_id=usuario_id)


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
