from app import db


class Resolucion(db.Model):
    """
    Contenido redaccional de la resolución de una fase RESOLUCION.

    Un registro por fase. Almacena los cuatro bloques textuales que el técnico
    redacta (con apoyo de las despensas #435 y #436) antes de generar el escrito.
    Todos los campos son nullable: el registro puede existir vacío mientras se
    redacta.

    RELACIÓN CON FASE:
        FK única a fases.id. Una fase RESOLUCION tiene como mucho una Resolucion.
        Accesible desde Fase como fase.resolucion (uselist=False).

    CAMPOS:
        antecedentes  — Narración de hechos previos al acto. Puede construirse
                        programáticamente vía consultas nombradas, pero este campo
                        permite texto libre adicional o sustitutivo.
        fundamentos   — Fundamentos jurídicos del acto. Compilable desde la
                        despensa de fundamentos (#435).
        resuelve      — Expresión verbal del sentido del acto. Margen de redacción
                        para el técnico; no sistematizable automáticamente.
        condicionado  — Condiciones impuestas. Compilable desde la despensa de
                        condicionados (#436).
    """
    __tablename__ = 'resoluciones'
    __table_args__ = (
        db.UniqueConstraint('fase_id', name='uq_resoluciones_fase'),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    fase_id = db.Column(
        db.Integer,
        db.ForeignKey('public.fases.id', name='fk_resoluciones_fase'),
        nullable=False,
        unique=True,
        comment='FK fases. Una resolución por fase RESOLUCION.',
    )

    antecedentes = db.Column(
        db.Text,
        nullable=True,
        comment='Narración de antecedentes del expediente',
    )

    fundamentos = db.Column(
        db.Text,
        nullable=True,
        comment='Fundamentos jurídicos del acto (#435)',
    )

    resuelve = db.Column(
        db.Text,
        nullable=True,
        comment='Expresión verbal del sentido del acto',
    )

    condicionado = db.Column(
        db.Text,
        nullable=True,
        comment='Condicionado técnico de la autorización (#436)',
    )

    fase = db.relationship(
        'Fase',
        foreign_keys=[fase_id],
        backref=db.backref('resolucion', uselist=False),
    )

    def __repr__(self):
        return f'<Resolucion fase_id={self.fase_id}>'

    def as_contexto_cb(self) -> dict:
        """Fragmento de contexto para la plantilla de resolución."""
        return {
            'resolucion_antecedentes': self.antecedentes,
            'resolucion_fundamentos':  self.fundamentos,
            'resolucion_resuelve':     self.resuelve,
            'resolucion_condicionado': self.condicionado,
        }
