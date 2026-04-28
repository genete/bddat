"""Modelo AmbitoInhabilidad — catálogo de ámbitos del calendario de inhábiles.

Referencia: DISEÑO_FECHAS_PLAZOS.md §3.4
"""
from app import db


class AmbitoInhabilidad(db.Model):
    """Ámbito territorial de aplicación de una fecha inhábil.

    PROPÓSITO: distinguir festivos nacionales, autonómicos andaluces y
    provinciales para filtrar el calendario aplicable al órgano tramitador.

    CAMPO codigo: 'NACIONAL' | 'AUTONOMICO_AND' | 'PROVINCIAL_CAD' | ...
    """
    __tablename__ = 'ambitos_inhabilidad'
    __table_args__ = (
        db.UniqueConstraint('codigo', name='uq_ambitos_inhabilidad_codigo'),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo = db.Column(
        db.String(40), nullable=False,
        comment='Código: NACIONAL | AUTONOMICO_AND | PROVINCIAL_CAD | ...',
    )
    nombre = db.Column(
        db.String(200), nullable=False,
        comment='Nombre legible del ámbito territorial',
    )

    dias_inhabiles = db.relationship('DiaInhabil', back_populates='ambito')

    def __repr__(self):
        return f'<AmbitoInhabilidad {self.codigo}>'
