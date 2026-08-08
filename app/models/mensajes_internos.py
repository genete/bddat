from app import db
from sqlalchemy.dialects.postgresql import JSONB


class MensajeInterno(db.Model):
    """
    Petición interna de un usuario al Supervisor, y su respuesta (ADR-040).

    VOCABULARIO (ADR-040 §1) — tres palabras para tres cosas distintas:
        Notificación — acto jurídico de notificar al interesado, con efectos
                       de plazo. Vive en `notificaciones` (ADR-034).
        Aviso        — toast de UI capturado durante la sesión, efímero.
                       Vive en el tab "Avisos" del dock (ADR-020).
        Mensaje      — esto. Persistente y accionable.

    LA TABLA ES LA BANDEJA (ADR-040 §2):
        No hay `destinatario_usuario_id` ni `destinatario_rol_id`. Toda fila
        va dirigida al rol SUPERVISOR/ADMIN por construcción; lo que se
        persiste es el REMITENTE.

        El motivo no es de gusto: los roles son N:M y los permisos se evalúan
        contra el rol ACTIVO de sesión, así que un usuario TRAMITADOR+SUPERVISOR
        recibiría peticiones de supervisor mientras opera como tramitador, y al
        leerlas en un rol quedarían leídas para siempre. Un fan-out (una fila
        por destinatario) además congelaría la lista: un supervisor de alta
        posterior no vería las peticiones anteriores.

    UNA FILA, TRES ESTADOS (ADR-040 §3):

        pendiente  ->  hecho (+ resultado + notas)  ->  acusado por el remitente

        El Supervisor NO genera fila nueva al responder: cierra la misma. El
        usuario ve en un solo objeto qué pidió y qué le contestaron, y los dos
        badges del sobre son dos filtros del mismo registro.

        Para el Supervisor, marcar `hecho` *es* el acuse: no hay un "leído"
        aparte — una petición dirigida al rol la atiende uno y queda atendida
        para todos. El acuse del remitente sí es explícito.

    HECHO vs HECHO_AT:
        `hecho` es redundante con `hecho_at IS NOT NULL`. Se mantiene explícito
        porque es el campo del modelo mental de la interfaz (la casilla que el
        Supervisor marca); `hecho_at`/`hecho_por_id` son la traza de quién y
        cuándo. El CHECK `ck_mi_hecho` impide que diverjan.

    RESULTADO vs NOTAS:
        `resultado` existe además de `notas` a propósito: sin él el veredicto
        viviría solo en prosa libre — no contable, no filtrable, no legible sin
        interpretar texto. Para "solicitar cambio de rol", si se concedió o se
        denegó *es* el dato.

    TIPO + DATOS:
        `tipo` gobierna la forma de `datos` (JSONB). Ni el productor ni el
        inspector conocen esa forma de primera mano: ambos pasan por el registro
        de `app/services/mensajes_internos.py`, que declara para cada tipo su
        codificador, su validación y su render. Nunca se codifica el formato en
        dos sitios. Añadir un tipo nuevo (N055/N056/N070) es una entrada en ese
        registro, sin tocar este modelo ni el schema.

    RELACIONES:
        remitente (N:1) -> USUARIOS — quien pide
        hecho_por (N:1) -> USUARIOS — quien resolvió
    """
    __tablename__ = 'mensajes_internos'
    __table_args__ = (
        db.CheckConstraint(
            "resultado IS NULL OR resultado IN ('ATENDIDA', 'DENEGADA')",
            name='ck_mi_resultado'
        ),
        db.CheckConstraint(
            'hecho = FALSE OR (resultado IS NOT NULL AND hecho_at IS NOT NULL)',
            name='ck_mi_hecho'
        ),
        db.CheckConstraint(
            'acusado_at IS NULL OR hecho = TRUE',
            name='ck_mi_acuse'
        ),
        db.Index('idx_mi_remitente', 'remitente_usuario_id', 'acusado_at'),
        {'schema': 'public'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    remitente_usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('public.usuarios.id'),
        nullable=False,
        comment='FK usuarios. Quien pide. NOT NULL: el alta de usuario nuevo no entra por aquí (ADR-040 §9)'
    )

    tipo = db.Column(
        db.String(40),
        nullable=False,
        comment='Tipo de petición. Gobierna la forma de DATOS y su render (registro del servicio)'
    )

    datos = db.Column(
        JSONB,
        nullable=False,
        comment='Payload de la petición, con la forma que declare su TIPO en el registro del servicio'
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        comment='Momento del envío de la petición'
    )

    # --- Resolución por el Supervisor ---

    hecho = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default='false',
        comment='TRUE cuando el Supervisor la ha resuelto. Es la casilla que marca en la interfaz'
    )

    resultado = db.Column(
        db.String(10),
        nullable=True,
        comment='Veredicto: ATENDIDA | DENEGADA. NULL mientras HECHO=False'
    )

    notas = db.Column(
        db.Text,
        nullable=True,
        comment='Explicación libre del Supervisor al resolver. El veredicto contable va en RESULTADO'
    )

    hecho_por_id = db.Column(
        db.Integer,
        db.ForeignKey('public.usuarios.id'),
        nullable=True,
        comment='FK usuarios. Quién resolvió (traza: la petición va al rol, la atiende una persona)'
    )

    hecho_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
        comment='Cuándo se resolvió'
    )

    # --- Acuse del remitente ---

    acusado_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
        comment='Cuándo el remitente acusó la respuesta. Explícito, nunca implícito por abrir el listado'
    )

    # Relaciones
    remitente = db.relationship(
        'Usuario',
        foreign_keys=[remitente_usuario_id],
        backref=db.backref('mensajes_internos_enviados', lazy='dynamic'),
    )

    hecho_por = db.relationship(
        'Usuario',
        foreign_keys=[hecho_por_id],
    )

    @property
    def estado(self):
        """Estado del ciclo de vida: 'pendiente' | 'resuelto' | 'acusado'.

        Derivado, no columna: los tres estados son combinaciones de `hecho` y
        `acusado_at`, y los CHECK garantizan que no hay combinaciones fuera de
        esta escalera.
        """
        if not self.hecho:
            return 'pendiente'
        if self.acusado_at is None:
            return 'resuelto'
        return 'acusado'

    def __repr__(self):
        return f'<MensajeInterno id={self.id} tipo={self.tipo} estado={self.estado}>'

    def __str__(self):
        return f'{self.tipo} de {self.remitente} ({self.estado})'
