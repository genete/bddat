"""Módulo de modelos SQLAlchemy para BDDAT.

Estructura de importaciones:
- Modelos operacionales (public schema)
- Modelos maestros (estructura schema)
- Modelos auxiliares y relaciones

ORDEN IMPORTANTE:
- Primero modelos SIN foreign keys a otros modelos operacionales
- Luego modelos CON foreign keys (respetando dependencias)
"""

# Modelos maestros primero (no tienen FKs entre ellos)
from app.models.usuarios import Usuario, Rol
from app.models.municipios import Municipio
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_fases import TipoFase
from app.models.tipos_ia import TipoIA
from app.models.tipos_resultados_fases import TipoResultadoFase
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.tipos_tareas import TipoTarea
from app.models.tipos_tramites import TipoTramite

# Arquitectura Entidades Polimórfica (nuevos modelos issue #62)
# Orden: TipoEntidad primero, luego Entidad, luego metadatos
from app.models.tipo_entidad import TipoEntidad
from app.models.entidad import Entidad
from app.models.entidad_administrado import EntidadAdministrado
from app.models.entidad_empresa_servicio_publico import EntidadEmpresaServicioPublico
from app.models.entidad_organismo_publico import EntidadOrganismoPublico
from app.models.entidad_ayuntamiento import EntidadAyuntamiento
from app.models.entidad_diputacion import EntidadDiputacion

# Relaciones N:N Entidades (issue #63)
from app.models.autorizado_titular import AutorizadoTitular

# Modelos operacionales sin dependencias operacionales
from app.models.proyectos import Proyecto

# Modelos operacionales con dependencias simples
from app.models.expedientes import Expediente  # Depende de Proyecto, Usuario, TipoExpediente
from app.models.documentos import Documento  # Depende de Expediente
from app.models.solicitudes import Solicitud  # Depende de Expediente

# Modelos operacionales con dependencias múltiples
from app.models.solicitudes_tipos import SolicitudTipo  # Depende de Solicitud, TipoSolicitud
from app.models.documentos_proyecto import DocumentoProyecto  # Depende de Documento, Proyecto
from app.models.fases import Fase  # Depende de Solicitud, TipoFase, TipoResultadoFase, Documento
from app.models.municipios_proyecto import MunicipioProyecto  # Depende de Municipio, Proyecto

# Modelos operacionales con dependencias complejas (al final)
from app.models.tramites import Tramite  # Depende de Fase, TipoTramite
from app.models.tareas import Tarea  # Depende de Tramite, TipoTarea, Documento

__all__ = [
    # Maestros
    'Usuario',
    'Rol',
    'Municipio',
    'TipoExpediente',
    'TipoFase',
    'TipoIA',
    'TipoResultadoFase',
    'TipoSolicitud',
    'TipoTarea',
    'TipoTramite',
    # Arquitectura Entidades
    'TipoEntidad',
    'Entidad',
    'EntidadAdministrado',
    'EntidadEmpresaServicioPublico',
    'EntidadOrganismoPublico',
    'EntidadAyuntamiento',
    'EntidadDiputacion',
    # Relaciones N:N Entidades
    'AutorizadoTitular',
    # Operacionales
    'Proyecto',
    'Expediente',
    'Documento',
    'Solicitud',
    'SolicitudTipo',
    'DocumentoProyecto',
    'Fase',
    'MunicipioProyecto',
    'Tramite',
    'Tarea',
]
