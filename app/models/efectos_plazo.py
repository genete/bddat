"""Modelo EfectoPlazo — catálogo de efectos del vencimiento de plazos.

Referencia: DISEÑO_FECHAS_PLAZOS.md §2.4
"""
from app import db


class EfectoPlazo(db.Model):
    """Catálogo de efectos que produce el vencimiento de un plazo administrativo.

    PROPÓSITO: tabla maestra que evita hardcodear efectos como ENUM en Python.
    Los valores se administran por el Supervisor sin tocar código.

    CAMPO codigo: identificador único de negocio ('SILENCIO_ESTIMATORIO', etc.)
    CAMPO nombre: descripción legible en castellano.
    """
    __tablename__ = 'efectos_plazo'
    __table_args__ = (
        db.UniqueConstraint('codigo', name='uq_efectos_plazo_codigo'),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo = db.Column(
        db.String(60), nullable=False,
        comment='Código único de negocio: NINGUNO | SILENCIO_ESTIMATORIO | ...',
    )
    nombre = db.Column(
        db.String(200), nullable=False,
        comment='Descripción legible del efecto',
    )

    plazos = db.relationship('CatalogoPlazo', back_populates='efecto_plazo')

    def __repr__(self):
        return f'<EfectoPlazo {self.codigo}>'
