from app import db

class TipoFase(db.Model):
    """
    Catálogo maestro de fases procedimentales de tramitación administrativa.
    
    PROPÓSITO:
        Define las fases del procedimiento administrativo eléctrico que pueden
        atravesar los expedientes. Cada fase representa una etapa administrativa
        con sus propios plazos, requisitos y organismos implicados.
    
    FILOSOFÍA:
        - Fases basadas en estructura normativa del procedimiento administrativo
        - CODIGO es inmutable y se usa como clave en lógica de reglas de negocio
        - NOMBRE es modificable para mejorar claridad en interfaz de usuario
        - Tabla maestra estable con fases predefinidas
    
    CAMPO CODIGO:
        - Identificador único funcional (ej: ADMISIBILIDAD, CONSULTAS)
        - INMUTABLE: No debe cambiar porque se referencia en código del motor de reglas
        - Snake_case en mayúsculas sin espacios
        - Usado en lógica de validaciones y flujos
    
    CAMPO NOMBRE:
        - Denominación legible para usuarios
        - MODIFICABLE: Puede ajustarse para mejorar claridad
        - Usado en interfaz de usuario
    
    RELACIONES:
        - fases ← FASES.tipo_fase_id (instancias de fases en expedientes)
        - Referenciada por motor de reglas para determinar flujos y validaciones
    
    REGLAS DE NEGOCIO:
        El TIPO_FASE_ID determina:
        - Tareas y trámites obligatorios de la fase
        - Plazos de resolución
        - Organismos que intervienen
        - Documentación requerida
        - Secuencia de fases permitida
    
    DATOS MAESTROS:
        Ver datos_maestros.sql para valores iniciales.
    
    NOTAS DE VERSIÓN:
        v3.0: Sin cambios estructurales. Tabla maestra estable.
    """
    __tablename__ = 'tipos_fases'
    
    
    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='Identificador único autogenerado del tipo de fase'
    )
    
    codigo = db.Column(
        db.String(50), 
        nullable=False, 
        unique=True,
        comment='Código único inmutable de la fase (usado en lógica de reglas)'
    )
    
    nombre = db.Column(
        db.String(200),
        nullable=False,
        comment='Denominación completa de la fase para interfaz de usuario'
    )

    abrev = db.Column(
        db.String(20),
        nullable=True,
        comment='Abreviatura para breadcrumb (máx 20 car.). Si nula, se usa nombre.'
    )

    nombre_en_plantilla = db.Column(
        db.Text,
        nullable=True,
        comment='Nombre legible usado en nombres de documentos generados'
    )

    @property
    def label_bc(self):
        """Etiqueta corta para breadcrumb: abreviatura si existe, nombre completo si no."""
        return self.abrev or self.nombre

    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<TipoFase {self.codigo}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return self.nombre
