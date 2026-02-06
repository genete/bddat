from app import db

class DocumentoProyecto(db.Model):
    """
    Vinculación entre documentos y proyectos con metadatos de tipo y evolución.
    
    PROPÓSITO:
        Externaliza la relación DOCUMENTO → PROYECTO añadiendo metadatos (TIPO)
        sin contaminar la tabla DOCUMENTOS. Permite clasificar documentos según
        su rol en la evolución del proyecto (PRINCIPAL, MODIFICADO, REFUNDIDO, ANEXO).
    
    FILOSOFÍA:
        - NO es relación N:M, es N:1 con metadatos externalizados
        - Un documento solo puede estar en UN proyecto (UNIQUE documento_id)
        - FK externalizada: permite documentos sin proyecto
        - Mantiene DOCUMENTOS puro (solo expediente_id)
    
    CAMPO TIPO:
        Define la naturaleza del documento en la secuencia temporal:
        - PRINCIPAL: Proyecto inicial presentado
        - MODIFICADO: Proyecto con cambios (acumulativo)
        - REFUNDIDO: Consolida PRINCIPAL + MODIFICADOS (anula anteriores)
        - ANEXO: Documentación complementaria (siempre vigente)
    
    DEDUCCIÓN DE VIGENCIA (sin campo VIGENTE):
        Regla automática por consulta:
        1. REFUNDIDO más reciente anula todos los anteriores
        2. Sin REFUNDIDO: PRINCIPAL + todos MODIFICADOS + ANEXOS son vigentes
        3. ANEXOS siempre vigentes (complementarios)
        
        Ordenación por DOCUMENTOS.fecha_administrativa
    
    CAMPO DOCUMENTO_ID:
        - UNIQUE: Un documento solo puede vincularse a un proyecto
        - Garantiza relación N:1 a nivel de base de datos
    
    RELACIONES:
        - proyecto → PROYECTOS.id (FK, proyecto contenedor)
        - documento → DOCUMENTOS.id (FK UNIQUE, archivo físico)
    
    REGLAS DE NEGOCIO:
        - Un documento pertenece a UN proyecto (UNIQUE constraint)
        - Un proyecto siempre tiene al menos un PRINCIPAL
        - REFUNDIDO debe ser posterior a PRINCIPAL (validar en interfaz)
        - Ordenación por DOCUMENTOS.fecha_administrativa (no duplicar fecha aquí)
    
    NOTAS DE VERSIÓN:
        v3.0: NUEVA TABLA. Externaliza DOCUMENTO.proyecto_id con metadatos.
              Relación N:1, no N:M.
              ELIMINADOS: fecha_vinculacion, vigente (se deduce por consulta).
    """
    __tablename__ = 'documentos_proyecto'
    __table_args__ = (
        db.Index('idx_documentos_proyecto_proyecto', 'proyecto_id'),
        db.Index('idx_documentos_proyecto_tipo', 'proyecto_id', 'tipo'),
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado del registro'
    )
    
    proyecto_id = db.Column(
        db.Integer,
        db.ForeignKey('public.proyectos.id', referent_schema='public', ondelete='CASCADE', use_alter=True, name='fk_documentos_proyecto_proyecto'),
        nullable=False,
        comment='FK a PROYECTOS. Proyecto al que pertenece el documento'
    )
    
    documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id', referent_schema='public', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        comment='FK UNIQUE a DOCUMENTOS. Un documento solo puede estar en un proyecto'
    )
    
    tipo = db.Column(
        db.String(20),
        nullable=False,
        comment='Tipo de documento: PRINCIPAL, MODIFICADO, REFUNDIDO, ANEXO'
    )
    
    observaciones = db.Column(
        db.String(500),
        nullable=True,
        comment='Notas del técnico sobre la incorporación del documento'
    )
    
    # Relaciones
    proyecto = db.relationship('Proyecto', backref='documentos_proyecto')
    documento = db.relationship('Documento', backref=db.backref('proyecto_vinculado', uselist=False))
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<DocumentoProyecto proyecto={self.proyecto_id} doc={self.documento_id} tipo={self.tipo}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'{self.tipo}: Documento {self.documento_id}'
