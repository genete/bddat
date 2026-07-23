from app import db


class Notificacion(db.Model):
    """Tabla de seguimiento del acto de notificar de la tarea NOTIFICAR (ADR-034, #657/#658).

    Corrige ADR-008: no es un documento vitaminado 1:1 (ADR-005) — `resultado`
    y `numero_intento` son mutables a lo largo de la vida del acto de
    notificar, y el documento es, como mucho, una evidencia que puede no
    estar presente en cada momento. `tarea_id` es el ancla real de la fila.

    Dos caminos de escritura, un solo punto de verdad (`tarea_id`):
      - Camino A (opcional, "Registrar envío"): fila creada con
        documento_id=None al conocerse el envío (parseo transitorio del
        justificante de puesta a disposición, o manual para SIR).
      - Camino B (justificante definitivo): hook de `editar_tarea` al fijar/
        cambiar `documento_producido_id` en la tarea — upsert por `tarea_id`,
        nunca por `identificador_envio` (ese campo queda solo para cotejo).
    """
    __tablename__ = 'notificaciones'
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    tarea_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tareas.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )

    documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id', ondelete='CASCADE'),
        nullable=True,
        unique=True,
    )

    identificador_envio = db.Column(
        db.String(30),
        nullable=True,
        comment='Remesa/ID de envío — campo único genérico para los 4 canales, usado para cotejo (#658)',
    )

    resultado = db.Column(
        db.String(12),
        nullable=True,
        comment='CORRECTA | INCORRECTA | NULL (pendiente del justificante definitivo)',
    )

    canal = db.Column(
        db.String(10),
        nullable=False,
        comment='NOTIFICA | BANDEJA | SIR | POSTAL',
    )

    fecha_puesta_disposicion = db.Column(db.Date, nullable=False)

    fecha_resultado = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha del acto resuelto (lectura/caducidad/rechazo) — NULL mientras no hay resultado',
    )

    numero_intento = db.Column(
        db.SmallInteger,
        nullable=False,
        default=1,
        comment='1 o 2 — habilita regla LPACAP de dos intentos',
    )

    observaciones = db.Column(db.Text, nullable=True)

    tarea = db.relationship(
        'Tarea',
        backref=db.backref('notificacion', uselist=False),
    )
    documento = db.relationship(
        'Documento',
        backref=db.backref('notificacion', uselist=False),
    )
