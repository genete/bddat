from app import db


class TramiteTarea(db.Model):
    """Secuencia ordenada de tareas atómicas por tipo de trámite.

    PK (tipo_tramite_id, orden) permite que un mismo tipo de tarea
    aparezca en posiciones distintas del mismo trámite (p.ej. doble
    ESPERAR_PLAZO en ANUNCIO_BOE: espera publicación + plazo alegaciones).

    Seed desde ESTRUCTURA_FTT.json via migración 345_seed_tramites_tareas.
    """
    __tablename__ = 'tramites_tareas'
    __table_args__ = {'schema': 'public'}

    tipo_tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_tramites.id', name='fk_tram_tareas_tipo_tramite'),
        primary_key=True,
        nullable=False
    )
    orden = db.Column(db.SmallInteger, primary_key=True, nullable=False)
    tipo_tarea_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_tareas.id', name='fk_tram_tareas_tipo_tarea'),
        nullable=False
    )

    tipo_tramite = db.relationship('TipoTramite')
    tipo_tarea = db.relationship('TipoTarea')

    def __repr__(self):
        return f'<TramiteTarea tramite={self.tipo_tramite_id} orden={self.orden} tarea={self.tipo_tarea_id}>'
