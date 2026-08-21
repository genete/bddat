from app import db

class Tramite(db.Model):
    """
    Contenedor organizativo de tareas dentro de una fase.

    PROPÓSITO:
        Representa actuaciones administrativas concretas (solicitud de informe,
        anuncio BOP, recepción de alegación, etc.) realizadas durante una fase.
        Agrupa tareas atómicas bajo un patrón procedimental.

    FILOSOFÍA:
        - Contenedor organizativo de tareas
        - Estructura mínima: Solo tipo y observaciones
        - Semántica en TIPO: Patrones de tareas viven en TIPOS_TRAMITES
        - Sin documentos ni fechas propios: ambos viven en las tareas hijas
        - Sin campos de fecha propios: ver §2.bis DISEÑO_FECHAS_PLAZOS.md

    CAMPO FASE_ID:
        - NOT NULL: Todo trámite pertenece a una fase
        - FK a FASES (public schema)

    CAMPO TIPO_TRAMITE_ID:
        - NOT NULL: Define qué tipo de trámite es
        - FK a TIPOS_TRAMITES (public schema)
        - Determina patrón de tareas obligatorias

    ESTADOS DEDUCIBLES (properties, no columna):
        - PLANIFICADO: len(tareas) == 0
        - EN_CURSO: tareas presentes, no todas finalizadas
        - FINALIZADO: todas las tareas con tipos documentales tienen documento producido
                      (ANALIZAR, ELABORAR, NOTIFICAR y ESPERAR_PLAZO incluidos)

    RELACIONES:
        - fase → FASES.id (FK CASCADE, fase contenedora)
        - tipo_tramite → TIPOS_TRAMITES.id (FK, definición del trámite)
        - tareas ← TAREAS.tramite_id (tareas realizadas en este trámite)

    REGLAS DE NEGOCIO:
        - No puede finalizarse si hay tareas sin finalizar
        - Secuencias determinadas por motor de reglas
        - Trámites pueden ejecutarse en paralelo dentro de una fase
    """
    __tablename__ = 'tramites'
    __table_args__ = (
        db.Index('idx_tramites_fase', 'fase_id'),
        db.Index('idx_tramites_tipo', 'tipo_tramite_id'),
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado del trámite'
    )
    
    fase_id = db.Column(
        db.Integer,
        db.ForeignKey('public.fases.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a FASES. Fase a la que pertenece el trámite'
    )
    
    tipo_tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_tramites.id'),
        nullable=False,
        comment='FK a TIPOS_TRAMITES. Tipo de trámite'
    )
    
    observaciones = db.Column(
        db.String(2000),
        nullable=True,
        comment='Notas o comentarios adicionales del técnico'
    )
    
    # Relaciones
    fase = db.relationship('Fase', backref='tramites')
    tipo_tramite = db.relationship('TipoTramite', backref='tramites_instanciados')
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Tramite id={self.id} tipo={self.tipo_tramite_id} fase={self.fase_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'Trámite {self.id} - {self.tipo_tramite.nombre if self.tipo_tramite else "Sin tipo"}'

    # --- Estados deducibles ---
    # La completitud se deduce de documentos en las tareas hijas, no de campos de fecha.

    @property
    def finalizado(self):
        """True si todas las tareas con tipos documentales tienen documento producido
        y toda tarea NOTIFICAR tiene resultado CORRECTA registrado en notificaciones.

        ESPERAR_PLAZO produce CERT_PLAZO_CUMPLIDO (Caso B) o un doc externo (Caso A).
        NOTIFICAR ejecutada sin resultado registrado (None, ADR-034) → no finalizado (#418).
        Deuda #357 eliminada: ESPERAR_PLAZO ya participa en finalizado (#362).

        Un trámite sin ninguna tarea nunca se considera finalizado (#723): antes
        devolvía True por vacuidad del bucle de abajo — "vacío" no es lo mismo
        que "hecho", y ese hueco dejaba cerrar fases con trámites fantasma sin
        ningún aviso (ver también estado_dominio.estado_tramite, que ya evitaba
        el mismo vacío por otra vía).
        """
        if not self.tareas:
            return False
        _requieren = {'ANALIZAR', 'ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO'}
        for t in self.tareas:
            if not t.tipo_tarea:
                continue
            codigo = t.tipo_tarea.codigo
            if codigo in _requieren and not t.ejecutada:
                return False
            if codigo == 'NOTIFICAR' and t.ejecutada and t.resultado != 'CORRECTA':
                return False
        return True

    @property
    def planificado(self):
        """True si el trámite no tiene ninguna tarea aún."""
        return len(self.tareas) == 0

    # --- Navegación ---

    @property
    def tarea_espera(self):
        """Primera tarea ESPERAR_PLAZO del trámite, o None.

        Lo que un consumidor llama «el plazo del trámite» —los 15 días del
        traslado al titular, los 30 de la separata— es el de esta tarea: es ahí
        donde está el documento que fija la fecha de inicio, y desde #788 es ahí
        donde está también la fila del catálogo.

        Vive aquí y no en plazos.py (#778, ADR-041 §G): bajar de un trámite a su
        espera es navegación del árbol ESFTT, no una entrada del servicio de
        plazos — una función llamada «plazo de un trámite» reintroduciría por la
        puerta de atrás el nivel que #788 eliminó.

        «Primera» por orden de la relación, igual que el resto de accesores del
        modelo. Los ANUNCIO_* tienen dos esperas —la de la publicación y la de
        los 30 días de exposición—; ningún consumidor de esta property es un
        anuncio, y quien necesite la segunda debe pedirla por su tipo de
        documento, no por posición.
        """
        for t in self.tareas:
            if t.tipo_tarea and t.tipo_tarea.codigo == 'ESPERAR_PLAZO':
                return t
        return None

    @property
    def en_curso(self):
        """True si el trámite tiene tareas pero no está finalizado."""
        return not self.planificado and not self.finalizado

    @property
    def estado(self):
        """Estado del trámite: PLANIFICADO | EN_CURSO | FINALIZADO."""
        if self.planificado:
            return 'PLANIFICADO'
        if self.finalizado:
            return 'FINALIZADO'
        return 'EN_CURSO'
