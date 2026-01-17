from app import db

class Proyecto(db.Model):
    __tablename__ = 'proyectos'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Campos adicionales se añadirán posteriormente
    
    def __repr__(self):
        return f'<Proyecto {self.id}>'