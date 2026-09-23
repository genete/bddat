from app import db


# Valores de `resultado` (ck_notificaciones_resultado, 928c). RECHAZADA da la
# notificación por efectuada igual que CORRECTA (art. 41.5: «se tendrá por
# efectuado el trámite»; art. 41.7). Una INCORRECTA no llegó a practicarse.
RESULTADOS = ('CORRECTA', 'RECHAZADA', 'INCORRECTA')
RESULTADOS_EFECTUADA = ('CORRECTA', 'RECHAZADA')

# Justificantes previos (#928, ADR-049 §B/§C): se vinculan como CONSUMIDO de la
# NOTIFICAR, presupuesto del justificante final — nunca el documento que se
# notifica. JUSTIFICANTE_SEDE no es una notificación en sí (obligación paralela
# del art. 42.1) pero comparte el trato de "previo".
TIPOS_JUSTIFICANTE_PREVIO = (
    'JUSTIFICANTE_NOTIFICA_DISPOSICION',
    'JUSTIFICANTE_POSTAL_1ER',
    'JUSTIFICANTE_SEDE',
)


class Notificacion(db.Model):
    """Tabla de seguimiento del acto de notificar de la tarea NOTIFICAR (ADR-034,
    enmendado por ADR-049; #657/#658/#928).

    Corrige ADR-008: no es un documento vitaminado 1:1 (ADR-005) — `resultado`,
    `numero_intento` y `sede_justificacion` son mutables a lo largo de la vida
    del acto de notificar. `tarea_id` es el ancla real de la fila.

    **Sin fechas** (ADR-049 §G, #928): la del cumplimiento y la de efectos salen
    de `Documento.fecha_administrativa` de los justificantes vinculados a la
    tarea — `app/services/notificaciones.py` es su única fuente.

    Un solo camino de escritura: el hook de `editar_tarea`
    (`mutaciones_arbol._hook_notificar`) crea la fila al vincular el primer
    justificante con canal (previo o final) y la borra si se desvincula el
    último sin haber fijado `resultado`. Invariante (antes lo garantizaba el
    NOT NULL de la fecha de puesta a disposición, H5): **una fila existe solo
    si su tarea tiene, o tuvo al fijarse el resultado, un justificante de
    notificación vinculado**. El hook nunca escribe `resultado`: lo fija el
    usuario (PATCH .../notificar), el parser solo lo propone.
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
        comment='CORRECTA | RECHAZADA | INCORRECTA | NULL (sin fijar). CORRECTA y '
                'RECHAZADA dan la notificación por efectuada (art. 41.5/41.7)',
    )

    canal = db.Column(
        db.String(10),
        nullable=False,
        comment='NOTIFICA | BANDEJA | SIR | POSTAL',
    )

    numero_intento = db.Column(
        db.SmallInteger,
        nullable=False,
        default=1,
        comment='1 o 2 — habilita regla LPACAP de dos intentos',
    )  # solo POSTAL admite 2: ck_notificaciones_intento_postal (928c, D14)

    sede_justificacion = db.Column(
        db.Text,
        nullable=True,
        comment='Solo POSTAL: por qué no hay JUSTIFICANTE_SEDE (art. 42.1). '
                'Con texto, la sede cuenta como JUSTIFICADA',
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
