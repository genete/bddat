"""
Servicio de contexto para generación de escritos administrativos.

ARQUITECTURA DE CAPAS:
    Capa 1 — ContextoBaseExpediente (este fichero):
        Construye un dict plano con los datos directos del expediente.
        Suficiente para la mayoría de escritos simples.

    Capa 2 — Context Builders (app/services/context_builders/):
        Clases Python que enriquecen el contexto base con datos calculados
        o cruzados. Se crean cuando el primer tipo de escrito complejo los
        requiera.

USO:
    from app.services.escritos import ContextoBaseExpediente

    ctx = ContextoBaseExpediente(expediente).get_contexto()
    # ctx es un dict plano listo para python-docx-template
"""

from datetime import date


class ContextoBaseExpediente:
    """
    Capa 1 del sistema de generación de escritos.

    Extrae del expediente un dict plano con los campos más habituales en
    plantillas administrativas. Todos los valores son strings o None para
    facilitar la inserción directa en Jinja2 sin conversiones adicionales.

    CAMPOS DISPONIBLES EN EL CONTEXTO:
        Expediente:
            numero_at           — Número administrativo (AT-XXXX)
            expediente_id       — ID técnico interno

        Titular:
            titular_nombre      — Nombre / Razón Social del titular
            titular_nif         — NIF del titular
            titular_direccion   — Dirección de notificación (si existe)

        Proyecto:
            proyecto_titulo     — Título del proyecto técnico
            proyecto_finalidad  — Finalidad de la instalación
            proyecto_emplazamiento — Emplazamiento descriptivo
            instrumento_ambiental  — Siglas del instrumento (AAI, AAU, EXENTO...)

        Responsable:
            responsable_nombre  — Nombre completo del tramitador asignado

        Municipios:
            municipios          — Lista de nombres de municipios afectados (list[str])

        Fecha:
            fecha_hoy           — Fecha actual en formato DD/MM/YYYY
    """

    def __init__(self, expediente):
        self._exp = expediente

    def get_contexto(self) -> dict:
        exp = self._exp
        proyecto = exp.proyecto

        ctx = {
            # Expediente
            'expediente_id':        exp.id,
            'numero_at':            f'AT-{exp.numero_at}' if exp.numero_at else None,

            # Titular
            'titular_nombre':       exp.titular.nombre_completo if exp.titular else None,
            'titular_nif':          exp.titular.nif            if exp.titular else None,
            'titular_direccion':    self._direccion_titular(),

            # Proyecto
            'proyecto_titulo':         proyecto.titulo        if proyecto else None,
            'proyecto_finalidad':      proyecto.finalidad     if proyecto else None,
            'proyecto_emplazamiento':  proyecto.emplazamiento if proyecto else None,
            'instrumento_ambiental':   proyecto.ia.siglas     if proyecto and proyecto.ia else None,

            # Responsable
            'responsable_nombre': (
                exp.responsable.nombre_completo if exp.responsable else None
            ),

            # Municipios (lista de nombres para uso en plantilla simple)
            'municipios': self._municipios(),

            # Fecha
            'fecha_hoy': date.today().strftime('%d/%m/%Y'),
        }
        return ctx

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _direccion_titular(self) -> str | None:
        """Devuelve la dirección de notificación preferente del titular."""
        if not self._exp.titular:
            return None
        direcciones = getattr(self._exp.titular, 'direcciones_notificacion', [])
        preferente = next((d for d in direcciones if d.preferente), None)
        if preferente:
            return str(preferente)
        return None

    def _municipios(self) -> list[str]:
        """Devuelve los nombres de municipios afectados por el proyecto."""
        proyecto = self._exp.proyecto
        if not proyecto:
            return []
        return [mp.municipio.nombre for mp in proyecto.municipios_afectados]
