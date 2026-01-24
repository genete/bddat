from app import db

class TipoTramite(db.Model):
    """
    Catálogo maestro de tipos de trámites administrativos.
    
    PROPÓSITO:
        Define los tipos de trámites administrativos que se realizan durante
        la tramitación de expedientes. Cada trámite representa una actuación
        administrativa concreta con un patrón de tareas asociado.
    
    FILOSOFÍA:
        - CODIGO es inmutable y se usa en lógica de reglas de negocio
        - NOMBRE es modificable para mejorar claridad en interfaz
        - Tabla maestra estable con trámites predefinidos
    
    CAMPO CODIGO:
        - Identificador único funcional (ej: SOLICITUD_INFORME, ANUNCIO_BOP)
        - INMUTABLE: No debe cambiar porque se referencia en código del motor de reglas
        - Snake_case en mayúsculas sin espacios
        - Usado en lógica de validaciones y flujos
    
    CAMPO NOMBRE:
        - Denominación legible para usuarios
        - MODIFICABLE: Puede ajustarse para mejorar claridad
        - Usado en interfaz de usuario
    
    RELACIONES:
        - tramites ← TRAMITES.tipo_tramite_id (instancias de trámites)
        - Referenciado por motor de reglas para determinar patrón de tareas
    
    REGLAS DE NEGOCIO:
        El TIPO_TRAMITE_ID determina:
        - Patrón de tareas del trámite (definido en motor de reglas)
        - Plazos aplicables
        - Organismos implicados
        - Documentación asociada
    
    DATOS MAESTROS:
        Ver datos_maestros.sql para valores iniciales.
    
    NOTAS DE VERSIÓN:
        v3.0: Sin cambios estructurales. Tabla maestra estable.
    """
    __tablename__ = 'tipos_tramites'
    __table_args__ = {'schema': 'estructura'}
    
    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='Identificador único autogenerado del tipo de trámite'
    )
    
    codigo = db.Column(
        db.String(50), 
        nullable=False, 
        unique=True,
        comment='Código único inmutable del trámite (usado en lógica de reglas)'
    )
    
    nombre = db.Column(
        db.String(200), 
        nullable=False,
        comment='Denominación completa del trámite para interfaz de usuario'
    )
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<TipoTramite {self.codigo}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return self.nombre
