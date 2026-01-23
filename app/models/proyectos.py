from app import db
from datetime import date

class Proyecto(db.Model):
    """
    Proyecto técnico único asociado a cada expediente.
    
    PROPÓSITO:
        Representa la entidad técnica del proyecto de instalación eléctrica.
        Cada expediente tiene exactamente UN proyecto (relación 1:1 desde expediente).
        Contiene los metadatos técnicos fundamentales de la instalación.
    
    FILOSOFÍA:
        - Proyecto = entidad técnica PURA y ÚNICA por expediente
        - NO tiene múltiples versiones en esta tabla
        - Las versiones documentales (inicial, modificado, refundido) se gestionan
          mediante documentos vinculados en DOCUMENTOS_PROYECTO
        - Esta tabla solo almacena los metadatos técnicos actuales
    
    CARACTERÍSTICAS:
        - Relación 1:1 inversa con EXPEDIENTE (expediente apunta a proyecto)
        - Contiene datos técnicos esenciales (título, finalidad, emplazamiento)
        - Define instrumento ambiental aplicable (ia_id)
        - Fecha = fecha técnica (firma/visado), NO administrativa
    
    CAMPOS ESPECIALES:
        FECHA:
            - Es la fecha técnica del documento de proyecto (firma/visado)
            - NO es la fecha de presentación administrativa
            - Ayuda a identificar y ordenar versiones cronológicamente
            - Los documentos en DOCUMENTOS_PROYECTO tienen sus propias fechas
        
        IA_ID:
            - Define instrumento ambiental aplicable según normativa vigente
            - Valores posibles: AAI, AAU, AAUS, CA, EXENTO
            - Determina trámites ambientales necesarios
            - Puede ser NULL si aún no se ha determinado
        
        DEFAULTS CON EMOJI ⚠️:
            - Facilitan detección visual de datos incompletos
            - Permiten crear proyecto rápidamente para luego completar
            - No deben permanecer en producción (validación recomendada)
    
    RELACIONES:
        - expediente ← EXPEDIENTES (1:1 inversa, backref desde expediente)
        - ia → TIPOS_IA (instrumento ambiental aplicable)
        - documentos_proyecto → DOCUMENTOS_PROYECTO (N documentos versionados)
        - municipios → MUNICIPIOS_PROYECTO → MUNICIPIOS (N:M, afecciones territoriales)
    
    GESTIÓN DE VERSIONES:
        NO se crean múltiples registros de proyecto. La evolución se gestiona así:
        
        1. Proyecto Inicial:
           - Registro en PROYECTOS con metadatos base
           - Documento PDF en DOCUMENTOS_PROYECTO con TIPO='PRINCIPAL'
        
        2. Proyecto Modificado:
           - Se actualiza PROYECTOS (metadatos) si cambió algo esencial
           - Nuevo documento en DOCUMENTOS_PROYECTO con TIPO='MODIFICADO'
           - El PRINCIPAL sigue existiendo (historial)
        
        3. Proyecto Refundido:
           - Se actualiza PROYECTOS con datos consolidados
           - Nuevo documento en DOCUMENTOS_PROYECTO con TIPO='REFUNDIDO'
           - El REFUNDIDO anula PRINCIPAL y MODIFICADOS previos
    
    REGLAS DE NEGOCIO:
        1. Un proyecto debe tener al menos un documento PRINCIPAL en DOCUMENTOS_PROYECTO
        2. FECHA ayuda a ordenar cronológicamente versiones documentales
        3. IA_ID determina trámites ambientales obligatorios
        4. Los defaults con ⚠️ no deben permanecer en producción
    
    NOTAS DE VERSIÓN:
        v3.0: ELIMINADO EXPEDIENTE_ID (relación inversa desde expediente)
        v3.0: ELIMINADO TIPO_PROYECTO_ID (tipos viven en DOCUMENTOS_PROYECTO.TIPO)
        v3.0: ACLARADO FECHA (fecha técnica, no administrativa)
    """
    __tablename__ = 'proyectos'
    
    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='Identificador técnico único autogenerado'
    )
    
    titulo = db.Column(
        db.String(500), 
        nullable=False, 
        default='⚠️ Falta el título del proyecto',
        comment='Título descriptivo del proyecto técnico'
    )
    
    descripcion = db.Column(
        db.String(10000), 
        nullable=False, 
        default='⚠️ Falta la descripción del proyecto',
        comment='Descripción técnica detallada del proyecto (texto libre extenso)'
    )
    
    fecha = db.Column(
        db.Date, 
        nullable=False, 
        default=date.today,
        comment='Fecha técnica del proyecto (firma/visado), NO fecha administrativa de presentación'
    )
    
    finalidad = db.Column(
        db.String(500), 
        nullable=False, 
        default='⚠️ Falta la finalidad del proyecto',
        comment='Finalidad o uso previsto de la instalación eléctrica'
    )
    
    emplazamiento = db.Column(
        db.String(200), 
        nullable=False, 
        default='⚠️ Falta el emplazamiento',
        comment='Ubicación geográfica de la instalación (descripción textual)'
    )
    
    ia_id = db.Column(
        db.Integer, 
        db.ForeignKey('estructura.tipos_ia.id'), 
        nullable=True,
        comment='FK a TIPOS_IA. Instrumento ambiental aplicable (AAI, AAU, AAUS, CA, EXENTO)'
    )
    
    # Relación con TipoIA
    ia = db.relationship(
        'TipoIA', 
        foreign_keys=[ia_id], 
        backref='proyectos'
    )
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Proyecto {self.id}: {self.titulo[:50]}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return self.titulo
