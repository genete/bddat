"""Modelo CatalogoPlazo — catálogo de plazos legales por tipo de elemento ESFTT.

Referencia: DISEÑO_FECHAS_PLAZOS.md §3.2
"""
from sqlalchemy.dialects.postgresql import JSONB

from app import db


class CatalogoPlazo(db.Model):
    """Plazo legal asociado a un tipo de elemento ESFTT.

    PROPÓSITO: tabla maestra administrable por el Supervisor que vincula un
    tipo de Solicitud/Fase/Trámite/Tarea con su plazo legal y el efecto del
    vencimiento. Permite histórico de cambios normativos sin alterar el
    catálogo de tipos ESFTT.

    CAMPO tipo_elemento: nivel ESFTT ('SOLICITUD' | 'FASE' | 'TRAMITE' | 'TAREA').
        Redundante con la longitud de `camino`, pero se conserva como prefiltro
        SQL barato — filtrar por número de segmentos de un string no es viable.
    CAMPO camino: patrón calificado ESFTT con comodín posicional 'ANY' (#785).
        Mismo formato y mismo matcher (motor_reglas._sujeto_casa) que
        ReglaMotor.sujeto, con un nivel más de profundidad. La longitud codifica
        el nivel, y el último segmento NUNCA es 'ANY' (es el tipo del elemento
        evaluado, siempre conocido):
            SOLICITUD  2 segmentos   <expediente>/<siglas>
            FASE       3             <expediente>/<siglas>/<fase>
            TRAMITE    4             …/<tramite>
            TAREA      5             …/<tramite>/<tarea>
        Sustituye a tipo_elemento_codigo, que no distinguía dos puntos distintos
        del árbol con el mismo literal (ESPERAR_PLAZO, RESOLUCION). Antes de #785
        esa distinción la hacían condiciones_plazo sobre variables que reexponían
        posición en el árbol — FK disfrazada, retirada en la misma migración.
    CAMPO campo_fecha: JSONB que indica qué Documento.fecha_administrativa
        es el inicio del cómputo. Formato:
            {'fk': 'documento_solicitud_id'}           -- caso directo (FK del elemento)
            {'via_tarea_tipo': 'ESPERAR_PLAZO',
             'rol': 'CONSUMIDO'}                       -- vía tarea hija (rol en documentos_tarea)
    CAMPO plazo_unidad: 'DIAS_HABILES' | 'DIAS_NATURALES' | 'MESES' | 'ANOS'
    CAMPO efecto_vencimiento_id: FK a efectos_plazo.
    CAMPO vigencia_desde / vigencia_hasta: rango de vigencia. NULL = sin límite.
    CAMPO activo: TRUE para la entrada vigente; permite desactivar sin borrar.
    """
    __tablename__ = 'catalogo_plazos'
    __table_args__ = (
        db.Index('idx_catalogo_plazos_tipo_orden', 'tipo_elemento', 'orden'),
        db.Index('idx_catalogo_plazos_camino',     'camino'),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo_elemento = db.Column(
        db.String(20), nullable=False,
        comment='Nivel ESFTT: SOLICITUD | FASE | TRAMITE | TAREA',
    )
    camino = db.Column(
        db.String(250), nullable=False,
        comment='Patrón calificado ESFTT con comodín ANY: '
                'ANY/ANY/ANY/REQUERIMIENTO_SUBSANACION/ESPERAR_PLAZO. '
                'La hoja (último segmento) nunca es ANY.',
    )
    campo_fecha = db.Column(
        JSONB, nullable=True,
        comment='Referencia al Documento.fecha_administrativa de inicio: {"fk":"..."} (FK del elemento) o {"via_tarea_tipo":"...","rol":"CONSUMIDO|PRODUCIDO"} (vía tarea hija)',
    )
    plazo_valor = db.Column(
        db.Integer, nullable=False,
        comment='Valor numérico del plazo (días, meses o años)',
    )
    plazo_unidad = db.Column(
        db.String(20), nullable=False,
        comment='Unidad: DIAS_HABILES | DIAS_NATURALES | MESES | ANOS',
    )
    efecto_vencimiento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.efectos_plazo.id', ondelete='RESTRICT'),
        nullable=False,
        comment='FK a efectos_plazo — efecto del vencimiento',
    )
    norma_origen = db.Column(
        db.Text, nullable=True,
        comment='Cita de la norma que fija el plazo (art. 21.3 LPACAP, art. 128 RD 1955/2000, etc.)',
    )
    vigencia_desde = db.Column(
        db.Date, nullable=True,
        comment='Inicio de vigencia de este plazo. NULL = desde siempre',
    )
    vigencia_hasta = db.Column(
        db.Date, nullable=True,
        comment='Fin de vigencia de este plazo. NULL = indefinido',
    )
    activo = db.Column(
        db.Boolean, nullable=False, default=True, server_default='TRUE',
        comment='FALSE para entradas desactivadas sin borrar',
    )
    orden = db.Column(
        db.Integer, nullable=False, default=100, server_default='100',
        comment='Prioridad de selección: menor → se evalúa primero. '
                'Fallback sin condiciones: orden alto (100). No unique.',
    )

    efecto_plazo = db.relationship(
        'EfectoPlazo',
        foreign_keys=[efecto_vencimiento_id],
        back_populates='plazos',
    )
    condiciones = db.relationship(
        'CondicionPlazo',
        backref='catalogo_plazo',
        cascade='all, delete-orphan',
        order_by='CondicionPlazo.orden',
    )

    @property
    def hoja(self) -> str:
        """Último segmento del camino — el tipo del elemento evaluado.

        Solo para presentación (plantillas, JSON del listado). No es filtrable en
        SQL: para eso está `camino`. Deliberadamente NO se llama
        `tipo_elemento_codigo`: ese nombre invitaba a usarlo en queries como si
        siguiera siendo columna, y falla en runtime al no serlo.
        """
        return (self.camino or '').rsplit('/', 1)[-1]

    def __repr__(self):
        return f'<CatalogoPlazo {self.camino} {self.plazo_valor}{self.plazo_unidad}>'
