"""Módulo de modelos SQLAlchemy para BDDAT.

Estructura de importaciones:
- Modelos operacionales (public schema)
- Modelos maestros (estructura schema)
- Modelos auxiliares y relaciones
"""

# Modelos operacionales (public)
from app.models.expedientes import Expediente
from app.models.proyectos import Proyecto
from app.models.solicitudes import Solicitud
from app.models.solicitudes_tipos import SolicitudTipo
from app.models.documentos import Documento
from app.models.documentos_proyecto import DocumentoProyecto
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea
from app.models.municipios_proyecto import MunicipioProyecto

# Modelos maestros (estructura)
from app.models.municipios import Municipio
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_fases import TipoFase
from app.models.tipos_ia import TipoIA
from app.models.tipos_resultados_fases import TipoResultadoFase
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.tipos_tareas import TipoTarea
from app.models.tipos_tramites import TipoTramite
from app.models.usuarios import Usuario, Rol

__all__ = [
    # Operacionales
    'Expediente',
    'Proyecto',
    'Solicitud',
    'SolicitudTipo',
    'Documento',
    'DocumentoProyecto',
    'Fase',
    'Tramite',
    'Tarea',
    'MunicipioProyecto',
    # Maestros
    'Municipio',
    'TipoExpediente',
    'TipoFase',
    'TipoIA',
    'TipoResultadoFase',
    'TipoSolicitud',
    'TipoTarea',
    'TipoTramite',
    'Usuario',
    'Rol',
]
