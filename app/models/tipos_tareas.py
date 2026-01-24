from app import db

class TipoTarea(db.Model):
    """
    Catálogo maestro de tipos atómicos de tareas administrativas.
    
    PROPÓSITO:
        Define los 7 tipos atómicos de tareas que componen cualquier trámite
        administrativo. Cada tipo representa una operación administrativa básica
        que no puede descomponerse en operaciones más simples.
    
    FILOSOFÍA:
        - CODIGO es inmutable y se usa en lógica de reglas de negocio
        - NOMBRE es modificable para mejorar claridad en interfaz
        - Solo 7 tipos atómicos predefinidos (catálogo cerrado)
        - Tabla maestra estable, raramente cambia
    
    CAMPO CODIGO:
        - Identificador único funcional
        - INMUTABLE: No debe cambiar porque se referencia en código del motor de reglas
        - Snake_case en mayúsculas sin espacios
        - Usado en lógica de validaciones y flujos
    
    CAMPO NOMBRE:
        - Denominación legible para usuarios
        - MODIFICABLE: Puede ajustarse para mejorar claridad
        - Usado en interfaz de usuario
    
    RELACIONES:
        - tareas ← TAREAS.tipo_tarea_id (instancias de tareas en trámites)
    
    REGLAS DE NEGOCIO:
        Cada tipo de tarea tiene características específicas:
        - Requiere o genera documentos
        - Puede generar justificantes
        - Tiene plazos asociados
        - Define transiciones de estado de documentos
    
    DATOS MAESTROS:
        Ver datos_maestros.sql para los 7 tipos atómicos.
    
    NOTAS DE VERSIÓN:
        v3.0: Solo 7 tipos atómicos. Catálogo cerrado y estable.
    """
    __tablename__ = 'tipos_tareas'
    __table_args__ = {'schema': 'estructura'}
    
    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='Identificador único autogenerado del tipo de tarea'
    )
    
    codigo = db.Column(
        db.String(50), 
        nullable=False, 
        unique=True,
        comment='Código único inmutable de la tarea (usado en lógica de reglas)'
    )
    
    nombre = db.Column(
        db.String(200), 
        nullable=False,
        comment='Denominación completa de la tarea para interfaz de usuario'
    )
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<TipoTarea {self.codigo}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return self.nombre
