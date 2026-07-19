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

from app.models.direccion_notificacion import DireccionNotificacion


class ContextoBaseExpediente:
    """
    Capa 1 del sistema de generación de escritos.

    Extrae del expediente un dict plano con los campos más habituales en
    plantillas administrativas. Todos los valores son strings, dicts o None
    para facilitar la inserción directa en Jinja2 sin conversiones adicionales.

    CAMPOS DISPONIBLES EN EL CONTEXTO:
        Expediente:
            numero_at           — Número administrativo (AT-XXXX)
            expediente_id       — ID técnico interno

        Titular:
            titular_nombre      — Nombre / Razón Social del titular
            titular_nif         — NIF del titular
            titular_dir         — Dict {calle, cp, municipio, provincia, nif, email} o None
                                  Acceso en plantilla: {{titular_dir.calle}}, {{titular_dir.email}} etc.
                                  Prioridad: DireccionNotificacion(rol=TITULAR) > dirección principal de Entidad

        Proyecto:
            proyecto_titulo     — Título del proyecto técnico
            proyecto_finalidad  — Finalidad de la instalación
            proyecto_emplazamiento — Emplazamiento descriptivo
            instrumento_ambiental  — Siglas del instrumento (AAI, AAU, EXENTO...)

        Responsable:
            responsable_nombre  — Nombre completo del tramitador asignado
            responsable_siglas_escritos — Siglas del redactor para firma (Usuario.siglas_escritos, #407)

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
            'titular_dir':          self._direccion_titular(),

            # Proyecto
            'proyecto_titulo':         proyecto.titulo        if proyecto else None,
            'proyecto_finalidad':      proyecto.finalidad     if proyecto else None,
            'proyecto_emplazamiento':  proyecto.emplazamiento if proyecto else None,
            'instrumento_ambiental':   proyecto.ia.siglas     if proyecto and proyecto.ia else None,

            # Responsable (Usuario no tiene nombre_completo, se construye aquí)
            'responsable_nombre': (
                self._nombre_responsable()
            ),
            'responsable_siglas_escritos': (
                exp.responsable.siglas_escritos if exp.responsable else None
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

    def _direccion_titular(self) -> dict | None:
        """Devuelve {calle, cp, municipio, provincia} de la dirección de notificación del titular.

        Prioridad: DireccionNotificacion con rol TITULAR > dirección principal de Entidad.
        """
        if not self._exp.titular:
            return None
        src = DireccionNotificacion.obtener_direccion_notificacion(
            self._exp.titular.id, es_titular=True
        ) or self._exp.titular
        return self._dir_a_dict(src)

    @staticmethod
    def _dir_a_dict(src) -> dict:
        """Convierte un objeto con campos dirección/nif/email a dict granular para plantillas."""
        mun = getattr(src, 'municipio', None)
        if src.direccion_fallback:
            postal = {'calle': src.direccion_fallback, 'cp': '', 'municipio': '', 'provincia': ''}
        else:
            postal = {
                'calle':     src.direccion or '',
                'cp':        src.codigo_postal or '',
                'municipio': mun.nombre    if mun else '',
                'provincia': mun.provincia if mun else '',
            }
        postal['nif']   = src.nif   or ''
        postal['email'] = src.email or ''
        return postal

    def _nombre_responsable(self) -> str | None:
        """Construye nombre completo del responsable (Usuario no tiene nombre_completo)."""
        r = self._exp.responsable
        if not r:
            return None
        partes = [r.nombre, r.apellido1]
        if r.apellido2:
            partes.append(r.apellido2)
        return ' '.join(p for p in partes if p)

    def _municipios(self) -> list[str]:
        """Devuelve los nombres de municipios afectados por el proyecto."""
        proyecto = self._exp.proyecto
        if not proyecto:
            return []
        return [mp.municipio.nombre for mp in proyecto.municipios_afectados]
