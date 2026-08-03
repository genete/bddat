from app import db


class FaseTramite(db.Model):
    """Vocabulario de trámites por fase (ADR-037): qué tipos de trámite pertenecen
    conceptualmente a qué tipos de fase, y cuántas veces puede repetirse cada uno.

    No gatea permiso — eso lo decide reglas_motor (capa normativa condicional) o,
    para pertenencia/cardinalidad en sí, la categoría de bloqueo estructural
    escapable (ADR-037 §C). Esta tabla es taxonomía ESFTT: nunca citable a una
    norma, se mantiene por decisión propia de organización del procedimiento.

    Seed desde ESTRUCTURA_FTT.json vía migración 725_seed_fases_tramites.
    """
    __tablename__ = 'fases_tramites'
    __table_args__ = {'schema': 'public'}

    tipo_fase_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_fases.id', name='fk_fases_tramites_tipo_fase'),
        primary_key=True,
        nullable=False
    )
    tipo_tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_tramites.id', name='fk_fases_tramites_tipo_tramite'),
        primary_key=True,
        nullable=False
    )
    cardinalidad_maxima = db.Column(
        db.SmallInteger,
        nullable=True,
        comment='NULL = ilimitada. Ver ESTRUCTURA_FTT.json para la justificación por trámite.'
    )

    tipo_fase = db.relationship('TipoFase')
    tipo_tramite = db.relationship('TipoTramite')

    def __repr__(self):
        return f'<FaseTramite fase={self.tipo_fase_id} tramite={self.tipo_tramite_id}>'
