"""Modelo CondicionPlazo — condición de aplicabilidad de una entrada del catálogo de plazos.

Referencia: IMPLEMENTACION_341.md decisión B.
"""
from app import db


class CondicionPlazo(db.Model):
    """
    Condición individual que debe cumplirse para que una entrada de CatalogoPlazo
    sea la aplicable en un contexto dado.

    Todas las condiciones de la misma entrada se evalúan con AND implícito.
    Para expresar OR: crear entradas separadas en catalogo_plazos.

    La semántica de operadores y valor es idéntica a CondicionRegla.
    """
    __tablename__ = 'condiciones_plazo'
    __table_args__ = (
        db.CheckConstraint(
            "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL',"
            "'GT','GTE','LT','LTE','BETWEEN','NOT_BETWEEN')",
            name='ck_condiciones_plazo_operador',
        ),
        db.Index('idx_condiciones_plazo_catalogo', 'catalogo_plazo_id'),
        db.Index('idx_condiciones_plazo_variable', 'variable_id'),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    catalogo_plazo_id = db.Column(
        db.Integer,
        db.ForeignKey('public.catalogo_plazos.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a catalogo_plazos — entrada condicionada',
    )
    variable_id = db.Column(
        db.Integer,
        db.ForeignKey('public.catalogo_variables.id'),
        nullable=False,
        comment='FK a catalogo_variables — variable evaluada',
    )
    operador = db.Column(
        db.String(20), nullable=False,
        comment='Operador de comparación (ver catálogo en docstring)',
    )
    valor = db.Column(
        db.JSON, nullable=True,
        comment='Valor de referencia. Lista para IN/BETWEEN, None para IS_NULL/NOT_NULL',
    )
    orden = db.Column(
        db.Integer, nullable=False, default=1,
        comment='Orden de evaluación dentro de la entrada (informativo)',
    )

    variable = db.relationship('CatalogoVariable')

    def __repr__(self):
        nombre = self.variable.nombre if self.variable else f'var_id={self.variable_id}'
        return (
            f'<CondicionPlazo id={self.id} '
            f'plazo={self.catalogo_plazo_id} {nombre} {self.operador} {self.valor!r}>'
        )
