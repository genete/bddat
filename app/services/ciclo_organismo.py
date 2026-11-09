"""
ciclo_organismo.py — Qué ha respondido un organismo y qué se ha analizado de su consulta (#652).

El ciclo de un organismo (ADR-011, ADR-042, DISEÑO_CONSULTAS_ORGANISMOS.md §4) es una
cadena de trámites vinculados por `tramites_organismos`: la separata, y después los
traslados al titular y al organismo que haga falta. Cada uno termina en una `ANALIZAR`
que produce un diagnóstico (favorable, condicionado o desfavorable); ese diagnóstico es
lo que dice cómo sigue el ciclo.

Este módulo solo lee: hace falta tanto para las reglas del motor que gobiernan la
creación de los traslados (variables `organismo_respuesta_analizada` y
`traslado_organismo_procede`) como para el aviso de la `ANALIZAR`. Las dos consultas
comparten estas definiciones para no discrepar:

- **Respuesta real**: el `ESPERAR_PLAZO` del trámite produjo un documento de tipo
  `RESPUESTA_ORGANISMO` (o `RESPUESTA_TITULAR`). Contar el tipo y no «cualquier
  documento» deja fuera el certificado de plazo cumplido: un organismo que calla no ha
  respondido, y no hay nada que trasladar (arts. 127.2, 131.1 y 146.1 RD 1955/2000).
- **Analizada**: la `ANALIZAR` del trámite ya produjo su diagnóstico.

Solo importa modelos: no importa servicios, para poder usarse desde las variables del
motor sin ciclos.
"""
from typing import Optional

from app import db
from app.models.tipos_tramites import TipoTramite
from app.models.tramites import Tramite
from app.models.tramites_organismos import TramiteOrganismo

# Trámites en los que el organismo da su respuesta.
CODIGOS_RESPUESTA_ORGANISMO = ('CONSULTA_SEPARATA', 'CONSULTA_TRASLADO_ORGANISMO')
CODIGO_TRASLADO_TITULAR = 'CONSULTA_TRASLADO_TITULAR'

DOC_RESPUESTA_ORGANISMO = 'RESPUESTA_ORGANISMO'
DOC_RESPUESTA_TITULAR = 'RESPUESTA_TITULAR'


def tramites_del_organismo(oe, codigos) -> list:
    """Trámites de `oe` de los tipos `codigos`, del más antiguo al más reciente."""
    return (
        db.session.query(Tramite)
        .join(TramiteOrganismo, TramiteOrganismo.tramite_id == Tramite.id)
        .join(TipoTramite, Tramite.tipo_tramite_id == TipoTramite.id)
        .filter(TramiteOrganismo.organismo_expediente_id == oe.id,
                TipoTramite.codigo.in_(tuple(codigos)))
        .order_by(Tramite.id)
        .all()
    )


def _tarea_de(tramite, codigo):
    for tarea in tramite.tareas:
        if tarea.tipo_tarea and tarea.tipo_tarea.codigo == codigo:
            return tarea
    return None


def diagnostico_de_respuesta(tramite, codigo_documento: str):
    """Diagnóstico de la `ANALIZAR` de `tramite`, si el trámite tuvo una respuesta real
    (documento de tipo `codigo_documento` producido por su `ESPERAR_PLAZO`) y ya está
    analizada. `None` en cualquier otro caso: sin respuesta, respuesta sin analizar o
    un trámite que no es de consulta."""
    espera = _tarea_de(tramite, 'ESPERAR_PLAZO')
    documento = espera.documento_producido if espera is not None else None
    if documento is None or documento.tipo_doc is None:
        return None
    if documento.tipo_doc.codigo != codigo_documento:
        return None
    analisis = _tarea_de(tramite, 'ANALIZAR')
    producido = analisis.documento_producido if analisis is not None else None
    return producido.diagnostico if producido is not None else None


def ultima_respuesta_del_organismo(oe) -> Optional[Tramite]:
    """El trámite más reciente en el que el organismo responde (separata o traslado al
    organismo), o None si aún no hay ninguno."""
    tramites = tramites_del_organismo(oe, CODIGOS_RESPUESTA_ORGANISMO)
    return tramites[-1] if tramites else None


def ultimo_traslado_al_titular(oe, despues_de: Tramite) -> Optional[Tramite]:
    """El traslado al titular más reciente de `oe` creado después de `despues_de`, o None."""
    posteriores = [t for t in tramites_del_organismo(oe, (CODIGO_TRASLADO_TITULAR,))
                   if t.id > despues_de.id]
    return posteriores[-1] if posteriores else None
