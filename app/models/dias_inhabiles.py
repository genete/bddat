"""Modelo DiaInhabil — calendario de días inhábiles por ámbito.

Referencia: DISEÑO_FECHAS_PLAZOS.md §3.4
"""
from app import db


class DiaInhabil(db.Model):
    """Registro de un día inhábil en el calendario administrativo.

    PROPÓSITO: fuente de verdad del calendario de festivos para el cómputo
    de plazos en días hábiles (art. 30 LPACAP). La misma fecha puede
    aparecer en múltiples ámbitos (nacional, autonómico, provincial).

    CAMPO fecha: la fecha inhábil.
    CAMPO ambito_id: FK al ámbito territorial que declara la inhabilidad.
    La PK es (fecha, ambito_id) para permitir la misma fecha en distintos ámbitos.
    """
    __tablename__ = 'dias_inhabiles'
    __table_args__ = (
        db.PrimaryKeyConstraint('fecha', 'ambito_id', name='pk_dias_inhabiles'),
        db.Index('idx_dias_inhabiles_fecha', 'fecha'),
        {'schema': 'public'},
    )

    fecha = db.Column(
        db.Date, nullable=False,
        comment='Fecha inhábil',
    )
    descripcion = db.Column(
        db.String(200), nullable=True,
        comment='Denominación del festivo (Día de Andalucía, Viernes Santo, etc.)',
    )
    ambito_id = db.Column(
        db.Integer,
        db.ForeignKey('public.ambitos_inhabilidad.id', ondelete='RESTRICT'),
        nullable=False,
        comment='FK al ámbito territorial que declara la inhabilidad',
    )

    ambito = db.relationship('AmbitoInhabilidad', back_populates='dias_inhabiles')

    def __repr__(self):
        return f'<DiaInhabil {self.fecha} [{self.ambito_id}]>'
