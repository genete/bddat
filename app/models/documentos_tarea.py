from app import db


class DocumentoTarea(db.Model):
    """
    Vínculo operacional N:M entre una tarea y un documento, con rol.

    Sustituye a las FK `documento_usado_id` / `documento_producido_id` de la
    tabla `tareas` (ADR-010, #420). Una tarea puede consumir N documentos y
    produce a lo sumo uno.

    ROLES:
        - CONSUMIDO: documento de entrada de la tarea (0..N por tarea).
        - PRODUCIDO: documento de salida de la tarea (0..1 por tarea).

    REGLAS:
        - tarea_id → TAREAS (CASCADE delete)
        - documento_id → DOCUMENTOS (CASCADE delete)
        - (tarea_id, documento_id, rol) UNIQUE — no se duplica un vínculo
        - Un documento tiene un único productor: índice parcial único sobre
          documento_id cuando rol = 'PRODUCIDO'
        - Una tarea produce a lo sumo un documento: índice parcial único sobre
          tarea_id cuando rol = 'PRODUCIDO'

    No confundir con `tramites_tareas_documentos` (#346), que es un mapa
    semántico de catálogo (qué tipo de documento corresponde a cada posición
    de cada tipo de trámite). Esta tabla es operacional: instancias concretas.
    """
    __tablename__ = 'documentos_tarea'
    __table_args__ = (
        db.UniqueConstraint('tarea_id', 'documento_id', 'rol',
                            name='uq_documentos_tarea_rol'),
        db.CheckConstraint("rol IN ('CONSUMIDO', 'PRODUCIDO')",
                           name='ck_documentos_tarea_rol'),
        db.Index('idx_documentos_tarea_tarea', 'tarea_id'),
        db.Index('uq_documento_un_productor', 'documento_id', unique=True,
                 postgresql_where=db.text("rol = 'PRODUCIDO'")),
        db.Index('uq_tarea_un_producido', 'tarea_id', unique=True,
                 postgresql_where=db.text("rol = 'PRODUCIDO'")),
        {'schema': 'public'}
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    tarea_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tareas.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a TAREAS. Tarea a la que pertenece el vínculo'
    )

    documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a DOCUMENTOS. Documento vinculado a la tarea'
    )

    rol = db.Column(
        db.String(12),
        nullable=False,
        comment='Rol del vínculo: CONSUMIDO (entrada) | PRODUCIDO (salida)'
    )

    tarea = db.relationship('Tarea', back_populates='vinculos_documento')
    documento = db.relationship('Documento', backref='vinculos_tarea')

    def __repr__(self):
        return (f'<DocumentoTarea tarea={self.tarea_id} '
                f'doc={self.documento_id} rol={self.rol}>')
