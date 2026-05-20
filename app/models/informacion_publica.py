from app import db


class InformacionPublica(db.Model):
    """
    Contenido redaccional del anuncio de información pública (fase INFORMACION_PUBLICA).

    Un registro por fase. Almacena los tres bloques textuales que el técnico
    redacta antes de generar el documento ANUNCIO_IP. Todos los campos son
    nullable: el registro puede existir vacío mientras se redacta.

    RELACIÓN CON FASE:
        FK única a fases.id. Una fase INFORMACION_PUBLICA tiene como mucho
        una InformacionPublica. Accesible desde Fase como fase.informacion_publica.

    CAMPOS:
        antecedentes      — Narración de la necesidad del anuncio. Compilable
                            programáticamente pero admite texto libre adicional.
        fundamentos       — Base legal que exige el trámite de IP. Compilable
                            desde la despensa de fundamentos (#435, ampliada para
                            compartirse con ContextoResolucion).
        exposicion_publica — Bloque que recoge las frases sobre el período de
                            exposición pública (plazo, sede, lugar de consulta).
                            Tiene una parte fija generada y espacio para texto libre.
    """
    __tablename__ = 'informaciones_publicas'
    __table_args__ = (
        db.UniqueConstraint('fase_id', name='uq_informaciones_publicas_fase'),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    fase_id = db.Column(
        db.Integer,
        db.ForeignKey('public.fases.id', name='fk_informaciones_publicas_fase'),
        nullable=False,
        unique=True,
        comment='FK fases. Un registro por fase INFORMACION_PUBLICA.',
    )

    antecedentes = db.Column(
        db.Text,
        nullable=True,
        comment='Narración de la necesidad del anuncio de información pública',
    )

    fundamentos = db.Column(
        db.Text,
        nullable=True,
        comment='Fundamento normativo que exige el trámite de IP (#435)',
    )

    exposicion_publica = db.Column(
        db.Text,
        nullable=True,
        comment='Período de exposición, plazo, sede y lugar de consulta',
    )

    fase = db.relationship(
        'Fase',
        foreign_keys=[fase_id],
        backref=db.backref('informacion_publica', uselist=False),
    )

    def __repr__(self):
        return f'<InformacionPublica fase_id={self.fase_id}>'

    def as_contexto_cb(self) -> dict:
        """Fragmento de contexto para la plantilla del anuncio de IP."""
        return {
            'ip_antecedentes':       self.antecedentes,
            'ip_fundamentos':        self.fundamentos,
            'ip_exposicion_publica': self.exposicion_publica,
        }
