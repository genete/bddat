from app import db

class TipoFase(db.Model):
    """
    Tabla maestra que define las fases procedimentales de tramitación administrativa.
    Basadas en estructura normativa del procedimiento administrativo eléctrico.
    El CODIGO es inmutable y se usa en lógica de reglas de negocio.
    """
    __tablename__ = 'tipos_fases'
    __table_args__ = {'schema': 'estructura'}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True,
                   comment='Identificador único del tipo de fase')
    codigo = db.Column(db.String(50), nullable=False, unique=True,
                       comment='Código único identificativo de la fase (sin espacios, inmutable)')
    nombre = db.Column(db.String(200), nullable=False,
                       comment='Denominación completa de la fase para interfaz de usuario')
    
    def __repr__(self):
        return f'<TipoFase {self.codigo}>'
