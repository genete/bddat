from app import db


class RequerimientoTarea(db.Model):
    """
    Defectos detectados en una tarea ANALIZAR, para el escrito de subsanación.

    Cada fila representa un requerimiento concreto que el técnico añade a la
    tarea ANALIZAR de ANÁLISIS_DOCUMENTAL o REQUERIMIENTO_SUBSANACIÓN. La
    lista ordenada alimenta el context builder de ContextoSubsanacion, que la
    inyecta en la plantilla del escrito.

    ORIGEN DEL TEXTO (exactamente uno de los dos campos tiene valor):
        catalogo_requerimientos_id — defecto del catálogo reutilizable (#405)
        texto_libre                — redacción manual del técnico

    El campo `texto` (property) abstrae el origen y devuelve siempre el texto
    efectivo, listo para renderizar en la plantilla ({{ r.texto }}).

    CAMPO ORDEN:
        Posición 1-based en el listado final. El técnico puede reordenar los
        ítems en el selector shuttle; el backend persiste el orden resultante.

    RELACIONES:
        tarea               → TAREAS.id (FK CASCADE, tarea ANALIZAR contenedora)
        catalogo_requerimiento → CATALOGO_REQUERIMIENTOS.id (FK, nullable)

    REGLAS DE NEGOCIO:
        - Exactamente uno de catalogo_requerimientos_id o texto_libre ≠ NULL
          (garantizado por CHECK constraint en la BD).
        - Solo tareas de tipo ANALIZAR deberían tener filas asociadas
          (responsabilidad de la capa de servicio, no de FK).
    """
    __tablename__ = 'requerimientos_tarea'
    __table_args__ = (
        db.CheckConstraint(
            "(catalogo_requerimientos_id IS NOT NULL AND texto_libre IS NULL) OR "
            "(catalogo_requerimientos_id IS NULL AND texto_libre IS NOT NULL)",
            name='ck_requerimientos_tarea_exactamente_uno'
        ),
        db.Index('idx_requerimientos_tarea_tarea', 'tarea_id'),
        db.Index('idx_requerimientos_tarea_catalogo', 'catalogo_requerimientos_id'),
        {'schema': 'public'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    tarea_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tareas.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a TAREAS. Tarea ANALIZAR a la que pertenece este requerimiento'
    )

    catalogo_requerimientos_id = db.Column(
        db.Integer,
        db.ForeignKey('public.catalogo_requerimientos.id'),
        nullable=True,
        comment='FK a CATALOGO_REQUERIMIENTOS. NULL si el origen es texto libre'
    )

    texto_libre = db.Column(
        db.Text,
        nullable=True,
        comment='Texto redactado manualmente. NULL si el origen es el catálogo'
    )

    orden = db.Column(
        db.Integer,
        nullable=False,
        comment='Posición 1-based en el listado del escrito'
    )

    # Relaciones
    tarea = db.relationship(
        'Tarea',
        backref=db.backref(
            'requerimientos',
            order_by='RequerimientoTarea.orden',
            cascade='all, delete-orphan',
        ),
    )
    catalogo_requerimiento = db.relationship(
        'CatalogoRequerimiento',
        back_populates='usos',
    )

    # --- Accesores ---

    @property
    def texto(self):
        """Texto efectivo: del catálogo o texto libre, listo para la plantilla."""
        if self.catalogo_requerimiento is not None:
            return self.catalogo_requerimiento.texto
        return self.texto_libre

    @property
    def desde_catalogo(self):
        """True si el origen es el catálogo; False si es texto libre."""
        return self.catalogo_requerimientos_id is not None

    def __repr__(self):
        origen = f'cat={self.catalogo_requerimientos_id}' if self.desde_catalogo else 'libre'
        return f'<RequerimientoTarea id={self.id} tarea={self.tarea_id} orden={self.orden} [{origen}]>'
