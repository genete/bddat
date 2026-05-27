from app import db


class CatalogoRequerimiento(db.Model):
    """
    Catálogo de defectos tipo reutilizables en la tarea ANALIZAR.

    Cada fila representa un defecto habitual en expedientes AT (falta de
    documento, deficiencia técnica, tasas incorrectas, etc.) que el técnico
    puede seleccionar en lugar de redactarlo desde cero. Garantiza imagen
    homogénea de la administración.

    Texto puede incluir huecos {placeholder} para completar en cada uso.
    Los defectos archivados (activo=False) no aparecen en el selector pero
    se conservan para no romper registros históricos en requerimientos_tarea.

    CATEGORÍAS (categoria):
        documental    — documentos faltantes o incompletos
        tecnica       — deficiencias de contenido del proyecto
        administrativa — requisitos formales del procedimiento
        tasas          — defectos relacionados con la tasa

    RELACIONES:
        usos ← REQUERIMIENTOS_TAREA (todas las veces que se ha seleccionado)
    """
    __tablename__ = 'catalogo_requerimientos'
    __table_args__ = (
        db.CheckConstraint(
            "categoria IN ('documental', 'tecnica', 'administrativa', 'tasas')",
            name='ck_catalogo_requerimientos_categoria'
        ),
        db.Index('idx_catalogo_requerimientos_categoria', 'categoria'),
        {'schema': 'public'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    texto = db.Column(
        db.Text,
        nullable=False,
        comment='Texto del defecto. Puede contener huecos {placeholder} para completar'
    )

    categoria = db.Column(
        db.String(20),
        nullable=False,
        comment='Categoría: documental | tecnica | administrativa | tasas'
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        comment='False = archivado; no aparece en el selector pero conserva historial'
    )

    # Relaciones
    usos = db.relationship(
        'RequerimientoTarea',
        back_populates='catalogo_requerimiento',
        lazy='dynamic',
    )

    def __repr__(self):
        return f'<CatalogoRequerimiento id={self.id} categoria={self.categoria}>'

    def __str__(self):
        return self.texto[:60] + ('…' if len(self.texto) > 60 else '')
