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
from app.models.consultas_nombradas import ConsultaNombrada
from app.models.plantillas import Plantilla

# Catálogo de requerimientos de subsanación (#405 — sin FK operacionales)
from app.models.catalogo_requerimientos import CatalogoRequerimiento

# Composición de Consejerías de la Delegación Territorial propia (#728 — sin FK, ADR-039 §1)
from app.models.organo_propio import ConsejeriaDelegacionTerritorial

# Unidad territorial propia por provincia (#728 — FK a ConsejeriaDelegacionTerritorial, ADR-039 §1)
from app.models.organo_propio import UnidadOrganoPropio

# Catálogo de firmantes de escritos (#728 — FK a UnidadOrganoPropio y Usuario, ADR-039 §2)
from app.models.organo_propio import FirmantePortafirmas

# Activos de red — corte mínimo de integración con bddat-instalaciones
# (#591 — activo_red autorreferenciada, sin FK operacionales de BDDAT)
from app.models.activo_red import ActivoRed, Envolvente

# Modelo de metadata del sistema (issue #85)
from app.models.tabla_metadata import TablaMetadata

# Configuración global del sistema (#323 — sin FKs)
from app.models.configuracion_sistema import ConfiguracionSistema

# Cuaderno de bitácora agnóstico (#1 — FK a usuarios)
from app.models.bitacora import Bitacora

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

from app.models.tramites_tareas import TramiteTarea

# Modelos operacionales con dependencias múltiples
from app.models.documentos_proyecto import DocumentoProyecto  # Depende de Documento, Proyecto
from app.models.fases import Fase  # Depende de Solicitud, TipoFase, TipoResultadoFase, Documento
from app.models.municipios_proyecto import MunicipioProyecto  # Depende de Municipio, Proyecto

# Modelos operacionales con dependencias complejas (al final)
from app.models.tramites import Tramite  # Depende de Fase, TipoTramite
from app.models.tareas import Tarea  # Depende de Tramite, TipoTarea, Documento
from app.models.documentos_tarea import DocumentoTarea  # Depende de Tarea, Documento
from app.models.notificaciones import Notificacion  # Depende de Documento (#418)

# Plazos — maestros sin dependencias operacionales (efectos_plazo, ambitos ya importados arriba)
from app.models.dias_inhabiles import DiaInhabil        # depende de AmbitoInhabilidad
from app.models.catalogo_plazos import CatalogoPlazo    # depende de EfectoPlazo
from app.models.condiciones_plazo import CondicionPlazo # depende de CatalogoPlazo y CatalogoVariable

# Motor de reglas (depende de TipoSolicitud; tipo_id sin FK por diseño polimórfico)
from app.models.motor_reglas import ReglaMotor, CondicionRegla

# Certificados de fase (#373 — depende de Expediente, Fase)
from app.models.certificados_fase import CertificadoFase

# Diagnóstico documental de tareas ANALIZAR (#392 — depende de Documento)
from app.models.diagnosticos import Diagnostico

# Certificados internos del motor vinculados al pool (#425 — depende de Documento)
from app.models.certificados import Certificado

# Alegante en trámites RECEPCION_ALEGACION (#393 — depende de Tramite, Entidad)
from app.models.alegantes import Alegante

# Organismos consultados por expediente (#391 — depende de Expediente, Entidad, Documento, Tramite)
from app.models.organismos_expediente import OrganismoExpediente
# Vínculo trámites↔organismos (#456 — depende de Tramite, OrganismoExpediente)
from app.models.tramites_organismos import TramiteOrganismo

# Interesados del expediente (#374 — depende de Expediente, Entidad, Documento)
from app.models.interesados_expediente import InteresadoExpediente

# Resolución de fase RESOLUCION (#403 — depende de Fase)
from app.models.resolucion import Resolucion

# Anuncio de información pública (#404 — depende de Fase)
from app.models.informacion_publica import InformacionPublica

# Requerimientos de tarea ANALIZAR (#405 — depende de Tarea y CatalogoRequerimiento)
from app.models.requerimientos_tarea import RequerimientoTarea

# Requisitos documentales por solicitud (#192 — depende de Solicitud, Documento, TipoDocumento)
from app.models.requisitos_documentales import (
    RequisitoDocumental,
    CondicionRequisito,
    DocumentoRequisito,
)

# Ítems técnicos del proyecto — apartados de contenido exigidos por RD 223/2008 /
# RD 337/2014 (#594 — depende de Solicitud, Norma, CatalogoVariable)
from app.models.items_tecnicos import (
    ItemTecnico,
    CondicionItemTecnico,
    CoberturaItemTecnico,
)

# Mapa semántico de documentos por tarea (#346 — sin FK operacional propia)
from app.models.tramites_tareas_documentos import TramiteTareaDocumento

# Tabla puente activo_red × expediente (#591 — depende de ActivoRed y Expediente)
from app.models.activos_expediente import ActivoExpediente

# Bandeja de peticiones al Supervisor (#28 — depende de Usuario, ADR-040)
from app.models.mensajes_internos import MensajeInterno

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
    'ConsultaNombrada',
    'Plantilla',
    # Catálogo de requerimientos
    'CatalogoRequerimiento',
    # Composición de Consejerías de la Delegación Territorial propia (#728)
    'ConsejeriaDelegacionTerritorial',
    # Unidad territorial propia por provincia (#728)
    'UnidadOrganoPropio',
    # Catálogo de firmantes de escritos (#728)
    'FirmantePortafirmas',
    # Activos de red (integración bddat-instalaciones)
    'ActivoRed',
    'Envolvente',
    # Metadata del sistema
    'TablaMetadata',
    # Configuración global del sistema
    'ConfiguracionSistema',
    # Cuaderno de bitácora
    'Bitacora',
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
    'TramiteTarea',
    # Operacionales (continuación)
    'DocumentoProyecto',
    'Fase',
    'MunicipioProyecto',
    'Tramite',
    'Tarea',
    'DocumentoTarea',
    'Notificacion',
    # Plazos
    'DiaInhabil',
    'CatalogoPlazo',
    'CondicionPlazo',
    # Motor de reglas
    'ReglaMotor',
    'CondicionRegla',
    # Certificados de fase
    'CertificadoFase',
    # Mapa semántico de documentos por tarea
    'TramiteTareaDocumento',
    # Tabla puente activo_red × expediente
    'ActivoExpediente',
    # Diagnóstico documental
    'Diagnostico',
    # Certificados internos del motor
    'Certificado',
    # Organismos consultados por expediente
    'OrganismoExpediente',
    # Vínculo trámites↔organismos
    'TramiteOrganismo',
    # Alegante en trámites RECEPCION_ALEGACION
    'Alegante',
    # Interesados del expediente
    'InteresadoExpediente',
    # Resolución de fase RESOLUCION
    'Resolucion',
    # Anuncio de información pública
    'InformacionPublica',
    # Requerimientos de tarea ANALIZAR
    'RequerimientoTarea',
    # Requisitos documentales por solicitud
    'RequisitoDocumental',
    'CondicionRequisito',
    'DocumentoRequisito',
    # Ítems técnicos del proyecto
    'ItemTecnico',
    'CondicionItemTecnico',
    'CoberturaItemTecnico',
    # Bandeja de peticiones al Supervisor (#28)
    'MensajeInterno',
]
