from app import db


class DocumentoTarea(db.Model):
    """
    Tabla puente N:N entre tareas INCORPORAR y sus documentos vinculados.

    Desde v5.5, la tarea INCORPORAR no usa documento_producido_id.
    En su lugar, este modelo registra los N documentos incorporados en un acto
    de recepción. Completitud: ≥1 registro con el tarea_id de la tarea INCORPORAR.

    REGLAS:
        - tarea_id → TAREAS (CASCADE delete)
        - documento_id → DOCUMENTOS (CASCADE delete)
        - (tarea_id, documento_id) UNIQUE: un documento solo se vincula una vez por acto
    """
    __tablename__ = 'documentos_tarea'
    __table_args__ = (
        db.UniqueConstraint('tarea_id', 'documento_id', name='uq_documentos_tarea'),
        db.Index('idx_documentos_tarea_tarea', 'tarea_id'),
        {'schema': 'public'}
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    tarea_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tareas.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a TAREAS. Acto de incorporación al que pertenece el vínculo'
    )

    documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a DOCUMENTOS. Documento incorporado en este acto'
    )

    tarea = db.relationship('Tarea', backref='documentos_tarea')
    documento = db.relationship('Documento', backref='documentos_tarea')

    def __repr__(self):
        return f'<DocumentoTarea tarea={self.tarea_id} doc={self.documento_id}>'
