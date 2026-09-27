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


# Fuentes de una notificación (ADR-051 §C): por qué se le notifica al
# destinatario. Lista cerrada en código, protegida por
# `ck_notificaciones_fuente` (967). La fija quien crea la `NOTIFICAR` y no
# cambia nunca.
FUENTES = (
    'SOLICITANTE',
    'ORGANISMO_DEL_TRAMITE',
    'ORGANISMOS_CONSULTADOS',
    'ORGANO_AMBIENTAL',
    'PROPIETARIOS_DUP',
    'INTERESADOS_RECONOCIDOS',
    'BOLETIN',
    'AYUNTAMIENTO',
    'MINISTERIO',
    'ORGANO_SUPERIOR',
)


class Notificacion(db.Model):
    """Ficha de la tarea NOTIFICAR: a quién se notifica y cómo acabó (ADR-034,
    enmendado por ADR-049 y ADR-051; #657/#658/#928/#967).

    Corrige ADR-008: no es un documento vitaminado 1:1 (ADR-005) — `resultado`,
    `numero_intento` y `sede_justificacion` son mutables a lo largo de la vida
    del acto de notificar. `tarea_id` es el ancla real de la fila.

    **Sin fechas** (ADR-049 §G, #928): la del cumplimiento y la de efectos salen
    de `Documento.fecha_administrativa` de los justificantes vinculados a la
    tarea — `app/services/notificaciones.py` es su única fuente.

    **Invariante (ADR-051 §B, #967; sustituye al de ADR-034/#928): toda
    `NOTIFICAR` tiene su fila y su fuente desde que se crea, y sin destinatario
    no avanza.** La fila nace en `mutaciones_arbol.crear_tarea` con `fuente` y
    se borra con la tarea (CASCADE). El destinatario (`entidad_id`,
    `en_nombre_de_entidad_id` y la copia `dest_*`) lo rellena
    `services.notificaciones.fijar_destinatario`: se puede cambiar mientras la
    tarea no tenga ningún justificante, y desde el primero queda fijo. Sin él
    la tarea no admite vínculos, salvo escape justificado; tras el escape ya no
    admite rellenarlo.

    El hook de `editar_tarea` (`mutaciones_arbol._hook_notificar`) fija `canal`
    —vacío hasta el primer justificante, #712— y `documento_id`, y coteja;
    nunca crea ni borra la fila ni escribe `resultado`: lo fija el usuario
    (PATCH .../notificar), el parser solo lo propone. «Hay una notificación
    registrada» (justificante con canal o resultado) es `registrada`, no la
    mera existencia de la fila, que desde #967 existe siempre.
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
        nullable=True,
        comment='NOTIFICA | BANDEJA | SIR | POSTAL. NULL hasta el primer justificante (#712, #967)',
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

    # --- Destinatario (ADR-051 §B, #967) ---

    fuente = db.Column(
        db.String(30),
        nullable=False,
        comment='Por qué se notifica (ADR-051 §C). Se fija al crear la tarea y no cambia',
    )
    entidad_id = db.Column(
        db.Integer,
        db.ForeignKey('public.entidades.id'),
        nullable=True,
        index=True,
        comment='A quién se envía (el representante, si lo hay). NULL = sin destinatario',
    )
    en_nombre_de_entidad_id = db.Column(
        db.Integer,
        db.ForeignKey('public.entidades.id'),
        nullable=True,
        comment='Representado, cuando se notifica a un representante',
    )
    direccion_origen_id = db.Column(
        db.Integer,
        db.ForeignKey('public.direcciones_notificacion.id', ondelete='SET NULL'),
        nullable=True,
        comment='Dirección de la que se copió el destinatario — solo referencia; lo válido es la copia',
    )
    dest_nombre = db.Column(db.Text, nullable=True)
    dest_nif = db.Column(db.String(20), nullable=True)
    dest_direccion = db.Column(db.Text, nullable=True)
    dest_codigo_postal = db.Column(db.String(10), nullable=True)
    dest_municipio = db.Column(db.Text, nullable=True)
    dest_provincia = db.Column(db.Text, nullable=True)
    dest_email = db.Column(db.Text, nullable=True)
    dest_dir3 = db.Column(db.String(20), nullable=True)
    dest_sir = db.Column(db.String(50), nullable=True)
    destinatario_fijado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
        comment='Cuándo se copió el destinatario. Fijo desde el primer justificante',
    )

    tarea = db.relationship(
        'Tarea',
        backref=db.backref('notificacion', uselist=False),
    )
    documento = db.relationship(
        'Documento',
        backref=db.backref('notificacion', uselist=False),
    )
    entidad = db.relationship('Entidad', foreign_keys=[entidad_id])
    en_nombre_de = db.relationship('Entidad', foreign_keys=[en_nombre_de_entidad_id])

    @property
    def tiene_destinatario(self) -> bool:
        return self.entidad_id is not None

    @property
    def registrada(self) -> bool:
        """Hay constancia de un acto de notificar: un justificante con canal
        vinculado (el hook fijó el canal) o un resultado. Es lo que hasta #967
        significaba «existe la fila»."""
        return self.canal is not None or self.resultado is not None
