from app import db

class TipoExpediente(db.Model):
    """
    Catálogo de tipos de expedientes según clasificación normativa.
    
    PROPÓSITO:
        Define la clasificación de expedientes combinando tipo de titular
        (particular, empresa distribuidora, productor) y tipo de instalación.
        Determina procedimientos aplicables según legislación sectorial eléctrica.
    
    FILOSOFÍA:
        - Combina tipo de titular + tipo de instalación en un único concepto
        - La semántica procedimental vive aquí, no en campos de EXPEDIENTES
        - Tabla maestra estable que define reglas de negocio procedimentales
        - Cada tipo determina flujos administrativos específicos
    
    CARACTERÍSTICAS:
        - Tabla maestra de configuración
        - Valores predefinidos por normativa sectorial
        - Raramente se añaden nuevos tipos
        - Define la lógica procedimental aplicable
    
    EJEMPLOS DE TIPOS:
        - "Expediente de particular - Línea Aérea"
        - "Expediente de distribuidora - Subestación Transformación"
        - "Expediente de productor - Parque Eólico"
        - "Expediente de transporte - Línea Alta Tensión"
    
    RELACIONES:
        - expedientes ← EXPEDIENTES.tipo_expediente_id (clasificación)
        - Usado por motor de reglas para determinar flujos procedimentales
    
    REGLAS DE NEGOCIO DERIVADAS:
        El TIPO_EXPEDIENTE_ID determina:
        
        1. Solicitudes aplicables:
           - Expedientes de transporte: pueden requerir DUP
           - Expedientes de distribución: AAP+AAC habitual
           - Expedientes de producción: AAP+AAC+DUP según potencia
        
        2. Fases obligatorias:
           - Expedientes de transporte: consulta a Ministerio obligatoria
           - Expedientes de distribución: consultas a ayuntamientos
           - Expedientes de producción: información pública ampliada
        
        3. Organismos a consultar:
           - Según tipo de titular e instalación
           - Carreteras, Hidráulica, Medio Ambiente, etc.
        
        4. Requisitos de información pública:
           - Duración del trámite según tipo
           - Alcance de la publicación
        
        5. Instrumentos ambientales aplicables:
           - AAI (Autorización Ambiental Integrada)
           - AAU (Autorización Ambiental Unificada)
           - AAUS (AAU Simplificada)
           - CA (Comunicación Ambiental)
           - EXENTO
    
    USO EN MOTOR DE REGLAS:
        Esta tabla es fundamental para el motor de reglas que determina:
        - Flujos procedimentales automáticos
        - Validaciones de solicitudes
        - Generación de tareas y trámites
        - Avisos de plazos
    
    NOTAS DE VERSIÓN:
        v3.0: Sin cambios estructurales. Tabla maestra estable.
    """
    __tablename__ = 'tipos_expedientes'
    __table_args__ = {'schema': 'estructura'}
    
    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='Identificador único autogenerado del tipo de expediente'
    )
    
    tipo = db.Column(
        db.String(100),
        comment='Denominación del tipo según clasificación normativa (titular + instalación)'
    )
    
    descripcion = db.Column(
        db.String(200),
        comment='Descripción detallada de características y particularidades procedimentales'
    )
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<TipoExpediente {self.id}: {self.tipo}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return self.tipo or f'TipoExpediente #{self.id}'
