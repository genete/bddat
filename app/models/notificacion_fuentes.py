from app import db
from app.models.notificaciones import FUENTES


class NotificacionFuente(db.Model):
    """Qué se notifica en cada trámite (ADR-051 §C, #968): las fuentes (roles)
    que puebla cada (tipo de fase, tipo de trámite), con la norma que lo exige.

    La clave incluye la fase porque el mismo trámite (`NOTIFICACION`) está en
    varias. No va en `fases_tramites`, que es taxonomía y nunca cita norma
    (ADR-037). Solo guarda roles, nunca entidades: el destinatario concreto lo
    fija siempre el usuario en la tabla que le corresponde (§H).

    `fuente` es una lista cerrada en código (`FUENTES`,
    `ck_notificacion_fuentes_fuente`): el catálogo elige y el código
    (`services/destinatarios_notificacion.py`) sabe calcular cada una.

    Sembrada por la migración `968_fuentes_destinatarios`.
    """
    __tablename__ = 'notificacion_fuentes'
    __table_args__ = (
        db.UniqueConstraint('tipo_fase_id', 'tipo_tramite_id', 'fuente',
                            name='uq_notificacion_fuentes'),
        db.CheckConstraint(
            'fuente IN (' + ', '.join(f"'{f}'" for f in FUENTES) + ')',
            name='ck_notificacion_fuentes_fuente',
        ),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Sin prefijo de esquema, como `fases_tramites`: los modelos de tipos se
    # declaran sin `schema` y el ORM no casaría la FK con prefijo.
    tipo_fase_id = db.Column(db.Integer, db.ForeignKey('tipos_fases.id'), nullable=False)
    tipo_tramite_id = db.Column(db.Integer, db.ForeignKey('tipos_tramites.id'), nullable=False)
    fuente = db.Column(db.String(30), nullable=False,
                       comment='Rol a notificar: lista cerrada en código')
    norma = db.Column(db.Text, nullable=True,
                      comment='Artículo que exige notificar a esa fuente. NULL = pendiente de citar')
    orden = db.Column(db.SmallInteger, nullable=False, comment='Orden de presentación')

    tipo_fase = db.relationship('TipoFase')
    tipo_tramite = db.relationship('TipoTramite')

    def __repr__(self):
        return (f'<NotificacionFuente fase={self.tipo_fase_id} '
                f'tramite={self.tipo_tramite_id} {self.fuente}>')
