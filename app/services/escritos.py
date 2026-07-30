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

    Capa 3 — Consultas nombradas: SQL de catálogo que entra al contexto con
        su nombre como clave (listas de dicts para bucles de tabla).

El contexto resultante es un diccionario y NO conoce el formato de la
plantilla (ADR-035 §6): lo consumen igual el motor .docx y el .odt.

USO:
    from app.services.escritos import ContextoBaseExpediente, construir_contexto

    ctx = ContextoBaseExpediente(expediente).get_contexto()   # solo capa 1
    ctx = construir_contexto(plantilla, expediente, db.session, tarea)  # las tres
"""

import importlib
import logging
import re
from datetime import date

from app.models.direccion_notificacion import DireccionNotificacion

logger = logging.getLogger(__name__)


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


# ======================================================================
# Contexto completo — agnóstico del formato de plantilla (ADR-035 §6)
# ======================================================================

def construir_contexto(plantilla, expediente, db_session, tarea=None) -> dict:
    """
    Compone el contexto completo de una plantilla: capa 1 + capa 2 + consultas.

    Lo usan los dos motores de render (.docx y .odt) sin modificarlo: aquí no
    entra nada que dependa del formato del fichero (imágenes, subdocumentos).

    Args:
        plantilla:   Instancia de Plantilla (define contexto_clase y consultas).
        expediente:  Instancia de Expediente con relaciones cargadas.
        db_session:  Sesión SQLAlchemy activa (para las consultas nombradas).
        tarea:       Tarea opcional. Si tiene documentos consumidos, el primero
                     entra al contexto como 'doc_entrada' (ADR-010).

    Returns:
        dict — Contexto listo para Jinja2.

    Raises:
        RuntimeError — Si el Context Builder especificado no se puede cargar.
    """
    ctx = ContextoBaseExpediente(expediente).get_contexto()

    # Documento de entrada: el primer documento consumido por la tarea (ADR-010)
    if tarea:
        _consumidos = tarea.documentos_consumidos
        if _consumidos:
            ctx['doc_entrada'] = _consumidos[0]

    # Capa 2: Context Builder opcional
    if plantilla.contexto_clase:
        builder = cargar_context_builder(plantilla.contexto_clase)
        ctx.update(builder(expediente, db_session, tarea=tarea).get_contexto())

    # Consultas nombradas: se añaden al contexto con su nombre como clave
    ctx.update(ejecutar_consultas(expediente, db_session))

    return ctx


def cargar_context_builder(nombre_clase: str):
    """
    Importa y devuelve la clase Context Builder por nombre.

    Convenio de módulo: app.services.context_builders.<nombre_clase_en_snake>
    Ejemplo: 'RequerimientoSubsanacion' → app.services.context_builders.requerimiento_subsanacion
    """
    snake = re.sub(r'(?<!^)(?=[A-Z])', '_', nombre_clase).lower()
    modulo_path = f'app.services.context_builders.{snake}'
    try:
        modulo = importlib.import_module(modulo_path)
        return getattr(modulo, nombre_clase)
    except (ModuleNotFoundError, AttributeError) as e:
        raise RuntimeError(
            f'No se pudo cargar el Context Builder "{nombre_clase}" '
            f'desde {modulo_path}: {e}'
        )


def ejecutar_consultas(expediente, db_session) -> dict:
    """
    Ejecuta TODAS las ConsultaNombrada activas con :expediente_id y las pasa
    al contexto. Las no referenciadas en la plantilla se ignoran por Jinja2.

    Estrategia simple: ejecutar todas es más barato que parsear la plantilla
    buscando etiquetas {%tr for row in X %}. Si una consulta falla, se
    registra un warning y se pasa como lista vacía (no rompe la generación).
    """
    from sqlalchemy import text

    from app.models.consultas_nombradas import ConsultaNombrada

    resultado = {}

    for cn in ConsultaNombrada.query.filter_by(activo=True).all():
        try:
            rows = db_session.execute(
                text(cn.sql),
                {'expediente_id': expediente.id}
            ).mappings().all()
            resultado[cn.nombre] = [dict(r) for r in rows]
        except Exception as e:
            logger.warning(
                'Consulta nombrada "%s" (id=%s) falló para expediente %s: %s',
                cn.nombre, cn.id, expediente.id, e
            )
            resultado[cn.nombre] = []

    return resultado
