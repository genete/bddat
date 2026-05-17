from app import db


class Notificacion(db.Model):
    """Documento vitaminado para los justificantes de la tarea NOTIFICAR (ADR-008, #418).

    Relación 1:1 con Documento: un justificante = una notificación.
    Sin fila → la tarea está ejecutada pero el resultado no ha sido registrado aún.
    """
    __tablename__ = 'notificaciones'
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )

    resultado = db.Column(
        db.String(12),
        nullable=False,
        comment='CORRECTA | INCORRECTA',
    )

    canal = db.Column(
        db.String(10),
        nullable=False,
        comment='NOTIFICA | BANDEJA | SIR | POSTAL',
    )

    fecha_notificacion = db.Column(db.Date, nullable=False)

    numero_intento = db.Column(
        db.SmallInteger,
        nullable=False,
        default=1,
        comment='1 o 2 — habilita regla LPACAP de dos intentos',
    )

    observaciones = db.Column(db.Text, nullable=True)

    documento = db.relationship(
        'Documento',
        backref=db.backref('notificacion', uselist=False),
    )
