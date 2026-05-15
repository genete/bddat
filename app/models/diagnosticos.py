from sqlalchemy.dialects.postgresql import JSONB
from app import db


class Diagnostico(db.Model):
    """
    Diagnóstico documental resultante de una tarea ANALIZAR.

    Un registro por documento de tipo DIAGNOSTICO. Almacena el resultado
    (favorable/condicionado/desfavorable) y la lista de defectos detectados.
    Cualifica cualquier Documento producido por cualquier tarea ANALIZAR
    de cualquier trámite.

    CAMPO DEFECTOS:
        JSONB. Lista de dicts. Items pueden incluir un 'catalogo_id' opcional
        cuando exista la tabla de catálogo de defectos (diseño futuro).
    """
    __tablename__ = 'diagnosticos'
    __table_args__ = (
        db.UniqueConstraint('documento_id', name='uq_diagnostico_documento'),
        db.CheckConstraint(
            "resultado IN ('favorable', 'condicionado', 'desfavorable')",
            name='ck_diagnostico_resultado',
        ),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id'),
        nullable=False,
        unique=True,
        comment='FK documentos. Documento de tipo DIAGNOSTICO producido por ANALIZAR',
    )

    resultado = db.Column(
        db.String(20),
        nullable=False,
        comment='Resultado: favorable, condicionado o desfavorable',
    )

    defectos = db.Column(
        JSONB,
        nullable=False,
        default=list,
        server_default='[]',
        comment='Lista de defectos detectados',
    )

    documento = db.relationship(
        'Documento',
        foreign_keys=[documento_id],
        backref=db.backref('diagnostico', uselist=False),
    )

    def __repr__(self):
        return f'<Diagnostico doc={self.documento_id} resultado={self.resultado}>'

    def as_contexto_cb(self) -> dict:
        """Fragmento de contexto para plantillas de ANALISIS_DOCUMENTAL."""
        defectos = self.defectos or []
        return {
            'diagnostico_resultado': self.resultado,
            'diagnostico_defectos': defectos,
            'diagnostico_tiene_defectos': len(defectos) > 0,
        }
