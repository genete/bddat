from app import db

class TipoResultadoFase(db.Model):
    """
    Catálogo maestro de resultados posibles de fases procedimentales.
    
    PROPÓSITO:
        Define los resultados que puede tener una fase tras su finalización.
        El técnico evalúa manualmente el resultado tras analizar documentos
        y determina si la fase tuvo éxito procedimental.
    
    FILOSOFÍA:
        - CODIGO es inmutable y se usa en lógica de reglas de negocio
        - NOMBRE es modificable para mejorar claridad en interfaz
        - Tabla maestra estable con resultados predefinidos
        - Condiciona fases siguientes según reglas de negocio
    
    CAMPO CODIGO:
        - Identificador único funcional (ej: FAVORABLE, DESFAVORABLE, CONDICIONADO)
        - INMUTABLE: No debe cambiar porque se referencia en código del motor de reglas
        - Snake_case en mayúsculas sin espacios
        - Usado en lógica de validaciones y flujos
    
    CAMPO NOMBRE:
        - Denominación legible para usuarios
        - MODIFICABLE: Puede ajustarse para mejorar claridad
        - Usado en interfaz de usuario
    
    RELACIONES:
        - fases ← FASES.resultado_fase_id (resultado de la fase)
    
    REGLAS DE NEGOCIO:
        El resultado de la fase determina:
        - Continuidad del procedimiento (avanza, paraliza, archiva)
        - Fases siguientes obligatorias
        - Condiciones o requisitos adicionales
        - Estado final del expediente
    
    DATOS MAESTROS:
        Ver datos_maestros.sql para valores iniciales.
    
    NOTAS DE VERSIÓN:
        v3.0: Sin cambios estructurales. Tabla maestra estable.
    """
    __tablename__ = 'tipos_resultados_fases'
    __table_args__ = {'schema': 'estructura'}
    
    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='Identificador único autogenerado del tipo de resultado'
    )
    
    codigo = db.Column(
        db.String(50), 
        nullable=False, 
        unique=True,
        comment='Código único inmutable del resultado (usado en lógica de reglas)'
    )
    
    nombre = db.Column(
        db.String(200), 
        nullable=False,
        comment='Denominación completa del resultado para interfaz de usuario'
    )
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<TipoResultadoFase {self.codigo}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return self.nombre
