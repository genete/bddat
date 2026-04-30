"""Módulo de modelos SQLAlchemy para BDDAT.

Estructura de importaciones:
- Modelos operacionales (public schema)
- Modelos maestros (public schema)
- Modelos auxiliares y relaciones

ORDEN IMPORTANTE:
- Primero modelos SIN foreign keys a otros modelos operacionales
- Luego modelos CON foreign keys (respetando dependencias)
"""

# Modelos maestros primero (no tienen FKs entre ellos)
from app.models.efectos_plazo import EfectoPlazo
from app.models.ambitos_inhabilidad import AmbitoInhabilidad
from app.models.usuarios import Usuario, Rol
from app.models.municipios import Municipio
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_fases import TipoFase
from app.models.tipos_ia import TipoIA
from app.models.tipos_resultados_fases import TipoResultadoFase
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.tipos_tareas import TipoTarea
from app.models.tipos_tramites import TipoTramite
from app.models.tipos_documentos import TipoDocumento
from app.models.tipos_resultado_documentos import TipoResultadoDocumento
from app.models.consultas_nombradas import ConsultaNombrada
from app.models.plantillas import Plantilla

# Modelo de metadata del sistema (issue #85)
from app.models.tabla_metadata import TablaMetadata

# Arquitectura Entidades Simplificada (refactorizada en issue #103)
# Elimina jerarquía polimórfica, usa roles booleanos
from app.models.entidad import Entidad
from app.models.direccion_notificacion import DireccionNotificacion

# Relaciones N:N Entidades (issue #63)
from app.models.autorizados_titular import AutorizadoTitular

# Modelos operacionales sin dependencias operacionales
from app.models.proyectos import Proyecto

# Modelos operacionales con dependencias simples
from app.models.expedientes import Expediente  # Depende de Proyecto, Usuario, TipoExpediente
from app.models.documentos import Documento  # Depende de Expediente
from app.models.solicitudes import Solicitud  # Depende de Expediente

# Histórico de titulares (issue #64)
from app.models.historico_titular_expediente import HistoricoTitularExpediente  # Depende de Expediente, Entidad, Solicitud

# Tablas whitelist ESFTT (#167 Fase 1)
from app.models.expedientes_solicitudes import ExpedienteSolicitud
from app.models.solicitudes_fases import SolicitudFase
from app.models.fases_tramites import FaseTramite
from app.models.tipos_documentos_resultados_validos import TipoDocumentoResultadoValido

# Modelos operacionales con dependencias múltiples
from app.models.documentos_proyecto import DocumentoProyecto  # Depende de Documento, Proyecto
from app.models.fases import Fase  # Depende de Solicitud, TipoFase, TipoResultadoFase, Documento
from app.models.municipios_proyecto import MunicipioProyecto  # Depende de Municipio, Proyecto

# Modelos operacionales con dependencias complejas (al final)
from app.models.tramites import Tramite  # Depende de Fase, TipoTramite
from app.models.tareas import Tarea  # Depende de Tramite, TipoTarea, Documento
from app.models.documentos_tarea import DocumentoTarea  # Depende de Tarea, Documento
from app.models.resultados_documentos import ResultadoDocumento  # Depende de Documento, TipoResultadoDocumento

# Plazos — maestros sin dependencias operacionales (efectos_plazo, ambitos ya importados arriba)
from app.models.dias_inhabiles import DiaInhabil        # depende de AmbitoInhabilidad
from app.models.catalogo_plazos import CatalogoPlazo    # depende de EfectoPlazo
from app.models.condiciones_plazo import CondicionPlazo # depende de CatalogoPlazo y CatalogoVariable

# Motor de reglas (depende de TipoSolicitud; tipo_id sin FK por diseño polimórfico)
from app.models.motor_reglas import ReglaMotor, CondicionRegla

__all__ = [
    # Maestros
    'EfectoPlazo',
    'AmbitoInhabilidad',
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
    'TipoDocumento',
    'TipoResultadoDocumento',
    'ConsultaNombrada',
    'Plantilla',
    # Metadata del sistema
    'TablaMetadata',
    # Arquitectura Entidades (simplificada en issue #103)
    'Entidad',
    'DireccionNotificacion',
    # Relaciones N:N Entidades
    'AutorizadoTitular',
    # Operacionales
    'Proyecto',
    'Expediente',
    'Documento',
    'Solicitud',
    # Histórico
    'HistoricoTitularExpediente',
    # Whitelists ESFTT
    'ExpedienteSolicitud',
    'SolicitudFase',
    'FaseTramite',
    'TipoDocumentoResultadoValido',
    # Operacionales (continuación)
    'DocumentoProyecto',
    'Fase',
    'MunicipioProyecto',
    'Tramite',
    'Tarea',
    'DocumentoTarea',
    'ResultadoDocumento',
    # Plazos
    'DiaInhabil',
    'CatalogoPlazo',
    'CondicionPlazo',
    # Motor de reglas
    'ReglaMotor',
    'CondicionRegla',
]
